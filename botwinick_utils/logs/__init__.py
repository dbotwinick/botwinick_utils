import pathlib
from typing import Generator


def file_log_lines_generator(log_path_obj: pathlib.Path, last_pos: int = 0, **kwargs) -> Generator[str, None, None]:
    """
    Create a generator that yields new lines from a given log file (as a Path object)

    :param log_path_obj: log path object
    :param last_pos: last logging position
    :param kwargs: (not used yet) but added to ensure flexible usage
    :return: generator that yields line_string, file_position
    """
    try:
        log_size = log_path_obj.stat().st_size

        # if last_pos is negative, then wrap to mean last n bytes
        if last_pos < 0:
            last_pos = max(0, log_size + last_pos)

        # if log file shrank, then we assume logs change and reset last_pos to zero!
        if log_size < last_pos:
            last_pos = 0
        # if log file has not grown, then return empty list
        elif log_size == last_pos:
            return

        # otherwise, seek to last position and yield iterate from there
        with log_path_obj.open(mode='r') as f:
            f.seek(last_pos)
            while line := f.readline():
                yield line, f.tell()

    except FileNotFoundError:
        # we use 1 for pos and check for last_pos of zero to
        # avoid repeatedly clearing and sending new data of 'No Log Data'...
        if last_pos == 0:
            yield 'No Log Data\n', 1

    return
