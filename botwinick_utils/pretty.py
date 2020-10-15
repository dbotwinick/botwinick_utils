# author: Drew Botwinick, Botwinick Innovations
# license: 3-clause BSD

from math import floor


def pretty_format_duration(time_seconds):
    # noinspection PyBroadException
    try:
        if time_seconds < 60:  # seconds
            return "%.0f s" % time_seconds
        elif time_seconds < 3600:  # minutes, seconds
            return "%.0f min %.0f s" % (floor(time_seconds / 60), time_seconds % 60)
        elif time_seconds < 86400:  # hours, minutes
            hours = floor(time_seconds / 3600)
            return "%.0f hrs %.0f min" % (hours, floor((time_seconds - 3600 * hours) / 60))
        else:  # days, hours
            days = floor(time_seconds / 86400)
            return "%.0f days %.1f hrs" % (days, (time_seconds - 86400 * days) / 3600)
    except Exception:
        return '...'


def pretty_format_sizeof(size, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(size) < 1024.0:
            return "%3.1f%s%s" % (size, unit, suffix)
        size /= 1024.0
    return "%.1f%s%s" % (size, 'Yi', suffix)


def right_truncate(s, length=32, prefix='...'):
    if not s:
        return s
    effective_len = length - len(prefix)
    if len(s) > length:
        return '%s%s' % (prefix, s[-effective_len:])
    return s


def left_truncate(s, length=32, suffix='...', leeway=0):
    if not s:
        return s
    if len(s) <= length + leeway:
        return s
    result = s[:length - len(suffix)].rsplit(' ', 1)[0]
    return result + suffix
