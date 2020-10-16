# author: Drew Botwinick, Botwinick Innovations
# license: 3-clause BSD

import logging
from logging.handlers import TimedRotatingFileHandler


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


def init_logging(log_level_name, file_name=None, days_to_keep=7, basic=False, uncompressed_days_to_keep=2):
    # Logging Configuration
    log_level = logging.getLevelName(log_level_name.upper())
    fs = '%(asctime)s %(levelname)s %(threadName)s %(name)s %(funcName)s() > %(message)s'
    dfs = '%Y/%m/%d %H:%M:%S'
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
