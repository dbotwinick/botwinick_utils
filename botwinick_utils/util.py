# author: Drew Botwinick, Botwinick Innovations
# license: 3-clause BSD

import logging
import re
from logging.handlers import TimedRotatingFileHandler

LOGGING_FORMAT = '%(asctime)s %(levelname)s %(threadName)s %(name)s %(funcName)s() > %(message)s'
LOGGING_DATE_FORMAT = '%Y/%m/%d %H:%M:%S'


def safe_float(string):
    """ Utility function to convert python objects to floating point values without throwing an exception """
    try:
        return float(string)
    except ValueError:
        return None


def safe_int(string):
    """ Utility function to convert python objects to integer values without throwing an exception """
    try:
        return int(string)
    except ValueError:
        return None


def squelch(prop_call, default=None, exceptions=(ValueError,)):
    """ Utility function that wraps a call (likely a lambda function?) to return a default on specified exceptions """
    if not exceptions:
        return prop_call()
    try:
        return prop_call()
    except exceptions:
        return default


def clean_dns_name(name: str, length_limit: int = 253) -> str:
    """
    Converts a given string to a DNS-compliant name.

    Parameters:
        name (str): The input string to be converted.
        length_limit (int): maximum length limit

    Returns:
        str: A DNS-compliant name.
    """
    # Convert to lowercase
    name = name.lower()

    # Replace any character that is not a letter, digit, or hyphen with a hyphen
    name = re.sub(r'[^a-z0-9-]', '-', name)

    # Remove leading or trailing hyphens (a DNS label cannot start or end with a hyphen)
    name = name.strip('-')

    # collapse repeated hyphens to single hyphens
    name = re.sub(r'-+', '-', name)

    # Truncate the  resulting name if longer than the length_limit
    if len(name) > length_limit:
        name = name[:length_limit]

    return name


def init_logging(log_level_name, file_name=None, days_to_keep=7, basic=False, uncompressed_days_to_keep=2):
    # Logging Configuration
    log_level = logging.getLevelName(log_level_name.upper())
    fs = LOGGING_FORMAT
    dfs = LOGGING_DATE_FORMAT
    if file_name and not basic:
        formatter = logging.Formatter(fs, dfs)

        # TODO: add a max log file size option for uncompressed log files?

        # backupCount set to uncompressed_days_to_keep (default, 2) because there was an issue with log files never being deleted
        if uncompressed_days_to_keep > 0:
            today_handler = TimedRotatingFileHandler(file_name, when='D', backupCount=uncompressed_days_to_keep, utc=True)
            today_handler.setFormatter(formatter)
            logging.root.addHandler(today_handler)
        if days_to_keep > 0:
            archive_handler = TimedRotatingFileHandler('%s.gz' % file_name, when='D', backupCount=days_to_keep, utc=True, encoding='zlib')
            archive_handler.setFormatter(formatter)
            logging.root.addHandler(archive_handler)

        logging.root.setLevel(log_level)
    else:
        logging.basicConfig(format=fs, datefmt=dfs, level=log_level, filename=file_name)
