class ProgressTracker(object):
    _percent = None  # type: dict[str, float]

    # TODO: add status text tracker from rostra

    def __init__(self):
        self._percent = {}

    # noinspection PyShadowingBuiltins
    def set_task_progress(self, id: str, value: float = 0.0):
        s = self._percent
        if 0.0 <= value < 1:
            s[id] = value
        elif id in s and value >= 1:  # remove tasks if value hits 1
            del s[id]
        return

    register_task = set_task_progress

    # noinspection PyShadowingBuiltins
    def rollup(self, id: str, progress_tracker: "ProgressTracker"):
        cp = progress_tracker.current_progress
        if cp is None:
            return
        return self.set_task_progress(id, cp)

    # noinspection PyShadowingBuiltins
    def close_task(self, id):
        if 'id' in self._percent:
            del self._percent[id]
        return

    @property
    def detailed_percents(self):
        return self._percent.copy()

    @property
    def task_count(self):
        return len(self._percent)

    @property
    def current_progress(self):
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
