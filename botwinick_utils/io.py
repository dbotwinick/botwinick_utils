# author: Drew Botwinick, Botwinick Innovations
# license: 3-clause BSD

import errno
from time import sleep


class FileIOPositionCallbackWrapper(object):
    """
    Simple Wrapper over File-like object that reports read/write progress to a given callback function.

    It only reports position (in bytes) to the callback function, so it is meant to be a 'one time use' wrapper
    around EITHER reading or writing a file.

    callback signature should accept: callback_fn(position_in_bytes)
    """

    def __init__(self, file_interface_obj, callback, rate_control=None):
        self._f = file_interface_obj
        self._c = callback
        self._r = rate_control
        self._l = None

    def _report_progress(self, force=False):
        pos = self._f.tell()
        r = self._r
        if force or self._r is None or (self._l is None or abs(pos - self._l) >= r):
            self._c(pos)
            self._l = pos

    def read(self, *args, **kwargs):
        self._report_progress()
        return self._f.read(*args, **kwargs)

    def write(self, *args, **kwargs):
        self._report_progress()
        return self._f.write(*args, **kwargs)

    def seek(self, *args, **kwargs):
        result = self._f.seek(*args, **kwargs)
        self._report_progress()
        return result

    def __getattr__(self, item):
        # delegate all attributes to underlying file object
        return getattr(self._f, item)


def permissions_wait(io_fn, timeout=15.0, action_on_wait=None, transient_errors=(errno.EACCES,), period=0.5):
    """
    A wrapper for opening a file etc. that might be able to be resolved if we notify the user and give them a chance
    to do something...
    :param io_fn: function (lambda?) that we're trying to perform that might involve a temporary/resolvable I/O error
    :param timeout: the maximum wait time for the I/O error to be resolved.
    :param action_on_wait: the function (lambda?) that we'll call periodically while waiting for either resolution or timeout
    :param transient_errors: the errno(s) that we're willing to ignore / might be resolved; any other errors will be raised
    :param period: the delay between subsequent calls to the `action_on_wait` while waiting to hit the `timeout`
    :return:
    """
    wait_time = 0.0
    while wait_time < timeout:
        try:
            result = io_fn()
            return result
        except InterruptedError:  # fail fast on interruptions/breaks
            return None
        except (IOError, OSError) as e:
            if e.errno not in transient_errors:
                raise e
        if action_on_wait:
            action_on_wait()
        sleep(period)  # sleep/yield
        wait_time += period
