# author: Drew Botwinick, Botwinick Innovations
# title: miscellaneous regex-based utilities for python 2/3
# license: 3-clause BSD

import re as _re


def split(delimiters, string, max_split=0, collapse_spaces_to_tabs=True):
    """
    Alternative to str.split that supports multiple delimiters simultaneously (uses regular expressions under the hood)

    :param delimiters: iterable of delimiters (a string containing 1 or more delimiters should work since it is iterable)
    :param string: the string to split
    :param max_split:  the maximum number of parts
    :param collapse_spaces_to_tabs: whether spaces in the input string should be consolidated into 1 TAB for any number of contiguous spaces
    :return:
    """
    if collapse_spaces_to_tabs:
        string = _re.sub(r'\s+', '\t', string)
    return _re.split('|'.join(map(_re.escape, delimiters)), string, max_split)


def number_unit(string):
    """
    Take an input string that contains a unit and convert it to a tuple of (number, unit) using regex

    :param string: number with unit string (e.g. "72 degF")
    :return: tuple of number, unit
    """
    return _re.findall(r'\s*([-]*[0-9.]*)[\s-]*(.*)', string)[0]


def parse_numeric_ranges(input_string, sep_delims=(',', ';', '\t'), range_delims=(':', '-'), r_type=int):
    """
    convert string of numbers and numeric ranges to a list suitable for processing and storage. This is the
    opposite operation of `convert_list_to_numeric_ranges_str`.

    :param input_string: string to parse
    :param sep_delims: delimiters separating separate inputs
    :param range_delims: delimiters separate begin:end of ranges
    :param r_type: type of value to return (basically int or float)
    :return:
    """
    # normalize input_string
    normalized_input = _re.sub(r'\s+', '\t', input_string)
    for rd in range_delims:
        normalized_input = _re.sub(''.join(map(_re.escape, ('\t', rd, '\t'))), rd, normalized_input)
    normalized_input = _re.split('|'.join(map(_re.escape, sep_delims)), normalized_input)

    # tokenize / extract
    tokens = [p for p in normalized_input if p] if isinstance(input_string, str) else []
    result = []
    i = 0
    while i < len(tokens):
        if any(d in tokens[i] for d in range_delims):  # range delimiter as embedded token
            range_start, range_end = (r_type(p) for p in split(range_delims, tokens[i], collapse_spaces_to_tabs=False))
            result.extend(range(range_start, range_end + 1))
        else:  # no range delimiter
            result.append(r_type(tokens[i]))
        i += 1
    return result


def convert_list_to_numeric_ranges_str(source_list, range_sep=':', sep=', '):
    """
    Consolidate a list of values into a user-friendly string list that consolidates contiguous (generally int) ranges
    separated by 1 into a user-readable format of ranges. This is the opposite operation of `parse_numeric_ranges`.

    :param source_list: list of values e.g. [1,2,3,4,5,6,10,11,12,13]
    :param range_sep: the string to place separating a range
    :param sep: the string to place between ranges
    :return: a user-readable range str, e.g. "1:6, 10:13"
    """
    if not source_list:
        return ''
    data = sorted(set(source_list))

    result = []
    range_start = -1
    for i in range(len(data)):
        if 0 <= i < len(data) - 1 and range_start == -1 and data[i + 1] - data[i] == 1:  # range start
            range_start = i
        if range_start != -1 and ((i == len(data) - 1 and data[i] - data[i - 1] == 1) or
                                  (i < len(data) - 1 and data[i + 1] - data[i] != 1)):  # range end
            result.append('%s%s%s' % (data[range_start], range_sep, data[i]))
            range_start = -1
        elif range_start == -1:  # not a range
            result.append('%s' % data[i])

    return sep.join(result)
