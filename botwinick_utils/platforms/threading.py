import logging
from threading import Thread
from time import sleep, time

from queue import PriorityQueue


class ThreadedEventLoop(object):
    def __init__(self, name='TEL', iteration_frequency=10, catch_exceptions=True):
        """

        :param name: name of loop / loop thread
        :param iteration_frequency: iterations per second
        """
        self._thread_name = name
        self._update_period = 1.0 / iteration_frequency
        self._logger = logging.getLogger(self.__class__.__name__)
        self._thread = None
        self._enabled = False  # basically means that we are allowed to run
        self._finalized = True  # basically means we're not running
        self._soft_stop = False  # means we're pending a soft stop
        self._catch_exceptions = catch_exceptions

    @property
    def running(self):
        return not self._finalized

    @property
    def _ready_to_exit(self):
        """
        Property meant to be overridden by implementations to make use of the 'soft stop' mechanism. This should return True
        if it's safe to exit (e.g. queue is empty, etc.).

        The default implementation just returns True--meaning there is no difference between a soft and hard stop. For implementations
        that are exhausting a queue or performing a series of calculations, this property should return True when that is completed.

        :return: boolean whether the thread loop method/function is ready for exit.
        :rtype: bool
        """
        return True

    @property
    def period(self):
        """
        Property that returns the update period. This is called on every loop invocation so:
        1) it can be variable if the property is overridden depending on changing conditions
        2) it should return a value quickly (i.e. not take a long time to calculate); we're already adding a lot of calls for every loop...

        :return: period between invocations / sleep time between invocations
        :rtype: float
        """
        return self._update_period

    def start(self, daemon_mode=True):
        self._logger.debug('Start Requested')
        self._enabled = True
        target = self.__run_w_catch if self._catch_exceptions else self.__run_wo_catch
        self._thread = Thread(target=target, name=self._thread_name)
        self._thread.daemon = daemon_mode
        self._thread.start()
        return self

    def stop(self, soft=True):
        self._logger.debug('Stop Requested')
        self._enabled = False
        self._soft_stop = soft

    def __run_wo_catch(self):
        self._logger.info('Starting')
        self._finalized = False
        try:
            while self._enabled or (self._soft_stop and not self._ready_to_exit):
                self._thread_loop()
                sleep(self.period)
        finally:
            self._finalized = True  # mark as done
            self._logger.info('Stopped')
            self._on_stop()

    def __run_w_catch(self):
        self._logger.info('Starting')
        self._finalized = False
        while self._enabled or (self._soft_stop and not self._ready_to_exit):
            try:
                self._thread_loop()
                sleep(self.period)
            except Exception as _e:
                self._logger.warning('Exception during loop iteration: "%s"', _e)
        self._finalized = True  # mark as done
        self._logger.info('Stopped')
        self._on_stop()

    def _on_stop(self):
        """
        Method to run when stopping (after thread loop execution). Can be useful for cleanup tasks.
        """
        pass

    def join(self, timeout=None):
        return self._thread.join(timeout)

    def _thread_loop(self):
        raise NotImplementedError()

    pass


# noinspection PyTestUnpassedFixture
class _QueueObject(object):
    """
    Quick Priority Queue Object Wrapper. Quickly added to ensure consistent
    behavior between old code and newer code using py3. Py3.7+ has dataclasses
    which could provide the same functionality, but this approach is compatible
    with py2.7+
    """

    def __init__(self, priority, item):
        self.priority = priority
        self.item = item
        self.time = time()  # capture instantiation time to break priority ties

    def __lt__(self, other):
        # TODO: error checking here?
        return self.priority < other.priority or self.time < other.time

    def __le__(self, other):
        # TODO: error checking here?
        return self.priority <= other.priority or self.time <= other.time

    def __gt__(self, other):
        # TODO: error checking here?
        return self.priority > other.priority or self.time > other.time

    def __ge__(self, other):
        # TODO: error checking here?
        return self.priority >= other.priority or self.time >= other.time

    def __eq__(self, o):
        if not isinstance(o, _QueueObject):
            return False
        if self.priority != o.priority:
            return False
        if self.time != o.time:
            return False
        return self.item == o.item

    def __repr__(self):
        return str((self.priority, self.item))

    @property
    def tuple(self):
        return self.priority, self.item


class CallQueue(object):
    _queue = None
    HIGH_PRIORITY = 25
    DEFAULT_PRIORITY = 50
    LOW_PRIORITY = 100

    def __init__(self):
        self._queue = PriorityQueue()

    @property
    def empty(self):
        return self._queue.empty()

    @property
    def size(self):
        return self._queue.qsize()

    def push(self, target, *args, **kwargs):
        queue_item = (target, args, kwargs)
        self._queue.put(_QueueObject(CallQueue.DEFAULT_PRIORITY, queue_item))

    def push_lo(self, target, *args, **kwargs):
        queue_item = (target, args, kwargs)
        self._queue.put(_QueueObject(CallQueue.LOW_PRIORITY, queue_item))

    def push_hi(self, target, *args, **kwargs):
        queue_item = (target, args, kwargs)
        self._queue.put(_QueueObject(CallQueue.HIGH_PRIORITY, queue_item))

    def pop(self, do_call=True):
        if not self._queue.empty():
            priority, (target, args, kwargs) = self._queue.get().tuple
            if do_call:
                return target(*args, **kwargs)
            return target, args, kwargs
        return None, None, None


class CallQueueThread(ThreadedEventLoop):

    def __init__(self, call_queue, name='CallQueueThread', iteration_frequency=10, catch_exceptions=True):
        super(CallQueueThread, self).__init__(name, iteration_frequency, catch_exceptions)
        self._call_queue = call_queue

    @property
    def queue(self):
        return self._call_queue

    @property
    def _ready_to_exit(self):
        # we're ready to exit if the queue is empty
        return self._call_queue.empty

    def _thread_loop(self):
        self._call_queue.pop()
