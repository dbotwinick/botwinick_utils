import logging
import os
import threading
from typing import Callable, Any
from concurrent.futures import ThreadPoolExecutor

_logger = None  # type: logging.Logger|None
_job_executor = None  # type: JobExecutorEngine|None

DEFAULT_BG_THREADS = os.getenv('ENGINE_BACKGROUND_THREADS', 4)
DEFAULT_SHUTDOWN_WAIT = False
DEFAULT_SHUTDOWN_CANCEL = True


def _get_logger():
    global _logger
    if _logger is None:
        _logger = logging.getLogger(__name__)
    return _logger


def _get_exec():
    global _job_executor
    if _job_executor is None:
        _job_executor = JobExecutorEngine()
    return _job_executor


class JobExecutorEngine(object):
    def __init__(self, max_workers: int = DEFAULT_BG_THREADS, name='engine background', thread_name_prefix='bg-engine-thread'):
        _get_logger().info('initializing %s thread pool executor with %s workers', name, max_workers)
        self._name = name
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=thread_name_prefix)
        # TODO: also consider using daemon threads if we don't care about interrupting the jobs on exit...
        self._lock = threading.Lock()
        self._job_ids = set()

    # TODO: add progress reporting capabilities from rostra to jobs to enable holistic progress reporting

    def submit_unique_job_pre(self, job_id, fn, *args, **kwargs):
        """
        Run a given task (fn, *args, **kwargs) via this thread pool executor. This is
        the "pre" style function (meaning that the "reservation" on the unique job_id is
        cleared immediately as the job is starting [rather than being cleared upon completion]).

        If unique job_id / collision / queue explosion prevention is not required, use `bg_run`.

        :param job_id: unique job_id to assigned to job to prevent collisions (otherwise use `bg_run`)
        :param fn: the function to execute
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :return: boolean True if queued
        """
        return self._submit_job(job_id, self._run_pre_job, fn, *args, **kwargs)

    def submit_unique_job_post(self, job_id, fn, *args, **kwargs):
        """
        Run a given task (fn, *args, **kwargs) via this thread pool executor. This is
        the default/"post" style function (meaning that the "reservation" on the unique job_id is
        cleared after the job finishes running).

        If unique job_id / collision / queue explosion prevention is not required, use `bg_run`.

        :param job_id: unique job_id to assigned to job to prevent collisions (otherwise use `bg_run`)
        :param fn: the function to execute
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :return: boolean True if queued
        """
        return self._submit_job(job_id, self._run_post_job, fn, *args, **kwargs)

    submit_unique_job = submit_unique_job_post

    def submit_job(self, fn, *args, **kwargs):
        """
        Run a given task (fn, *args, **kwargs) via this thread pool executor.

        :param fn: the function to execute
        :param args: arguments for the function
        :param kwargs: keyword arguments for the function
        :return: boolean True if queued
        """
        return bool(self._executor.submit(fn, *args, **kwargs))

    @property
    def queue_length(self):
        # noinspection PyProtectedMember
        return self._executor._work_queue.qsize()

    def contains_job(self, job_id: str):
        return job_id in self._job_ids

    def get_jobs(self):
        return list(self._job_ids)

    def _submit_job(self, job_id: str, run_fn, fn: Callable[..., Any], *args, **kwargs):
        with self._lock:
            # check for conflicting job
            if job_id in self._job_ids:
                # TODO: decide on proper level for this message and/or make it configurable because it could be context-dependent
                _get_logger().info("Job with ID %s is already in the queue. Ignoring duplicate.", job_id)
                return False

            # submit job
            self._job_ids.add(job_id)
            self._executor.submit(run_fn, job_id, fn, *args, **kwargs)
            return True

    def _run_pre_job(self, job_id: str, fn: Callable[..., Any], *args, **kwargs):
        with self._lock:
            self._job_ids.remove(job_id)  # Clean up job_id before starting for (pre) style job

        fn(*args, **kwargs)  # Run the actual job
        return

    def _run_post_job(self, job_id: str, fn: Callable[..., Any], *args, **kwargs):
        try:
            fn(*args, **kwargs)  # Run the actual job
        finally:
            with self._lock:
                self._job_ids.remove(job_id)  # Clean up job_id when done for (post) style job
        return

    def shutdown(self, wait: bool = DEFAULT_SHUTDOWN_WAIT, cancel_pending: bool = DEFAULT_SHUTDOWN_CANCEL):
        """
        Shuts down the executor.

        :param wait: whether to join/wait for shutdown completion
        :param cancel_pending: whether to cancel pending activities
        """
        _get_logger().info('Shutting down %s thread pool executor', self._name)
        return self._executor.shutdown(wait=wait, cancel_futures=cancel_pending)


def bg_run(fn, *args, **kwargs):
    return _get_exec().submit_job(fn, *args, **kwargs)


# noinspection PyShadowingBuiltins
def bg_run_unique_post(id, fn, *args, **kwargs):
    """
    Run a given task (fn, *args, **kwargs) via default background thread pool executor. This is
    the default/"post" style function (meaning that the "reservation" on the unique job_id is
    cleared after the job finishes running).

    If unique job_id / collision / queue explosion prevention is not required, use `bg_run`.

    :param id: unique job_id to assigned to job to prevent collisions (otherwise use `bg_run`)
    :param fn: the function to execute
    :param args: arguments for the function
    :param kwargs: keyword arguments for the function
    :return: boolean True if queued
    """
    return _get_exec().submit_unique_job_post(id, fn, *args, **kwargs)


# noinspection PyShadowingBuiltins
def bg_run_unique_pre(id, fn, *args, **kwargs):
    """
    Run a given task (fn, *args, **kwargs) via default background thread pool executor. This is
    the "pre" style function (meaning that the "reservation" on the unique job_id is
    cleared immediately as the job is starting [rather than being cleared upon completion]).

    If unique job_id / collision / queue explosion prevention is not required, use `bg_run`.

    :param id: unique job_id to assigned to job to prevent collisions (otherwise use `bg_run`)
    :param fn: the function to execute
    :param args: arguments for the function
    :param kwargs: keyword arguments for the function
    :return: boolean True if queued
    """
    return _get_exec().submit_unique_job_pre(id, fn, *args, **kwargs)


bg_run_unique = bg_run_unique_post


def bg_exec_shutdown(wait: bool = DEFAULT_SHUTDOWN_WAIT, cancel_pending: bool = DEFAULT_SHUTDOWN_CANCEL):
    """
    Call to trigger shutdown of the background thread pool executor if it has been initialized. It is
    safe to call this function on termination even if the background thread pool executor was never
    started.

    :param wait: whether to join/wait for shutdown completion
    :param cancel_pending: whether to cancel pending activities
    :return:
    """
    global _job_executor
    if _job_executor is None:  # nothing to do if job executor was never initialized
        return
    return _job_executor.shutdown(wait=wait, cancel_pending=cancel_pending)
