from typing import Callable


class ProgressTracker(object):
    _percent = None  # type: dict[str, float]

    # TODO: add status text tracker from rostra

    def __init__(self):
        """
        Generic Progress Tracking Mechanism.

        Note: assigns equal weight to all sub-tasks
        """
        self._percent = {}

    # noinspection PyShadowingBuiltins
    def set_task_progress(self, id: str, value: float = 0.0):
        """
        Set progress value for a given task ID.

        :param id: task ID
        :param value: progress value [0.0, 1.0]
        """
        s = self._percent
        if 0.0 <= value < 1:
            s[id] = value
        elif id in s and value >= 1:  # remove tasks if value hits 1
            del s[id]
        return

    register_task = set_task_progress

    # noinspection PyShadowingBuiltins
    def create_task_callback(self, id: str, lambda_fn: Callable = None, init_task=True):
        """
        Create a callback function for a particular task ID to facilitate various workflows.

        :param id: task ID
        :param lambda_fn: an optional function that will be called after each use of the callback function (e.g. schedule UI update)
        :param init_task: whether to ensure that the task is initialized with value of 0.0 before returning callback function
        :return: a single-arg callback function that takes a float value between 0 and 1 (see `set_task_progress`)
        """
        stp = self.set_task_progress

        if lambda_fn is None:
            def callback(value):
                stp(id, value)
        else:
            def callback(value):
                stp(id, value)
                lambda_fn()  # consider if we should wrap lambda_fn in try-except or if it's better to let things bubble up undisturbed

        if init_task:
            callback(0.0)

        return callback

    # noinspection PyShadowingBuiltins
    def rollup(self, id: str, progress_tracker: "ProgressTracker"):
        """
        Set progress value for a given task ID.

        :param id: task ID
        :param progress_tracker: a progress tracker whose summary percent values should be integrated
        """
        cp = progress_tracker.current_progress
        if cp is None:
            return
        return self.set_task_progress(id, cp)

    # noinspection PyShadowingBuiltins
    def close_task(self, id):
        """
        Set progress finished for a given task ID.

        :param id: task ID
        """
        if 'id' in self._percent:
            del self._percent[id]
        return

    @property
    def detailed_percents(self):
        """
        Get dict snapshot of current progress in form of {job_id: progress_float, ...}

        :return: dict containing current progress as a float value in range [0.0, 1.0] for each job_id
        :rtype: dict[str, float]
        """
        return self._percent.copy()

    @property
    def task_count(self):
        return len(self._percent)

    @property
    def current_progress(self):
        """
        Get current overall progress of the default progress tracker

        :return: current progress as a float value in range [0.0, 1.0] or None if there are no tasks
        """
        s = self._percent
        if len(s) > 0:
            return sum(s.values())
        return None  # use None to differentiate between 0 and nothing to report


_progress_tracker = ProgressTracker()


# noinspection PyShadowingBuiltins
def progress_set(id: str, value: float = 0.0):
    """
    Set progress value for a given task ID.

    :param id: task ID
    :param value: progress value [0.0, 1.0]
    """
    return _progress_tracker.set_task_progress(id, value)


# noinspection PyShadowingBuiltins
def progress_rollup(id: str, value: ProgressTracker):
    """
    Set progress value for a given task ID.

    :param id: task ID
    :param value: a progress tracker whose summary percent values should be integrated
    """
    return _progress_tracker.rollup(id, value)


# noinspection PyShadowingBuiltins
def progress_close(id: str):
    """
    Set progress finished for a given task ID.

    :param id: task ID
    """
    return _progress_tracker.close_task(id)


def progress_percent():
    """
    Get current overall progress of the default progress tracker

    :return: current progress as a float value in range [0.0, 1.0] or None if there are no tasks
    """
    return _progress_tracker.current_progress


def progress_detail():
    """
    Get dict snapshot of current progress in form of {job_id: progress_float, ...}

    :return: dict containing current progress as a float value in range [0.0, 1.0] for each job_id
    :rtype: dict[str, float]
    """
    return _progress_tracker.detailed_percents


__all__ = ('ProgressTracker', 'progress_set', 'progress_detail', 'progress_percent', 'progress_rollup', 'progress_close',)
