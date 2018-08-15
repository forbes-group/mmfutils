"""Various useful contexts.
"""
import functools
import signal
import time

from threading import RLock


class NoInterrupt(object):
    """Suspend the various signals during the execution block.

    Arguments
    ---------
    ignore : bool
       If True, then do not raise a KeyboardInterrupt if a soft interrupt is
       caught.

    Note: This is not yet threadsafe.  Semaphores should be used so that the
      ultimate KeyboardInterrupt is raised only by the outer-most context (in
      the main thread?)  The present code works for a single thread because the
      outermost context will return last.

      See:

      * http://stackoverflow.com/questions/323972/
        is-there-any-way-to-kill-a-thread-in-python

    >>> import os, signal, time

    This loop will get interrupted in the middle so that m and n will not be
    the same.

    >>> def f(n, interrupted=False, force=False):
    ...     done = False
    ...     while not done and not interrupted:
    ...         n[0] += 1
    ...         if n[0] == 5:
    ...             # Simulate user interrupt
    ...             os.kill(os.getpid(), signal.SIGINT)
    ...             if force:
    ...                 # Simulated a forced interrupt with multiple signals
    ...                 os.kill(os.getpid(), signal.SIGINT)
    ...                 os.kill(os.getpid(), signal.SIGINT)
    ...             time.sleep(0.1)
    ...         n[1] += 1
    ...         done = n[0] >= 10

    >>> n = [0, 0]
    >>> try:  # All doctests need to be wrapped in try blocks to not kill py.test!
    ...     f(n)
    ... except KeyboardInterrupt as err:
    ...     print("KeyboardInterrupt: {}".format(err))
    KeyboardInterrupt:
    >>> n
    [5, 4]

    Now we protect the loop from interrupts.
    >>> n = [0, 0]
    >>> try:
    ...     with NoInterrupt(ignore=False) as interrupted:
    ...         f(n)
    ... except KeyboardInterrupt as err:
    ...     print("KeyboardInterrupt: {}".format(err))
    KeyboardInterrupt:
    >>> n
    [10, 10]

    One can ignore the exception if desired (this is the default as of 0.4.11):
    >>> n = [0, 0]
    >>> with NoInterrupt() as interrupted:
    ...     f(n)
    >>> n
    [10, 10]

    Three rapid exceptions will still force an interrupt when it occurs.  This
    might occur at random places in your code, so don't do this unless you
    really need to stop the process.
    >>> n = [0, 0]
    >>> try:
    ...     with NoInterrupt(ignore=False) as interrupted:
    ...         f(n, force=True)
    ... except KeyboardInterrupt as err:
    ...     print("KeyboardInterrupt: {}".format(err))
    KeyboardInterrupt: Interrupt forced
    >>> n
    [5, 4]


    If `f()` is slow, we might want to interrupt it at safe times.  This is
    what the `interrupted` flag is for:

    >>> n = [0, 0]
    >>> try:
    ...     with NoInterrupt(ignore=False) as interrupted:
    ...         f(n, interrupted)
    ... except KeyboardInterrupt as err:
    ...     print("KeyboardInterrupt: {}".format(err))
    KeyboardInterrupt:
    >>> n
    [5, 5]

    Again: the exception can be ignored
    >>> n = [0, 0]
    >>> with NoInterrupt() as interrupted:
    ...     f(n, interrupted)
    >>> n
    [5, 5]
    """
    _instances = set()  # Instances of NoInterrupt suspending signals
    _signals = set((signal.SIGINT, signal.SIGTERM))
    _signal_handlers = {}  # Dictionary of original handlers
    _signals_raised = []
    _force_n = 3

    # Time, in seconds, for which 3 successive interrupts will raise a
    # KeyboardInterrupt
    _force_timeout = 1

    # Lock should be re-entrant (I think) since a signal might be sent during
    # operation of one of the functions.
    _lock = RLock()

    @classmethod
    def catch_signals(cls, signals=None):
        """Set signals and register the signal handler if there are any
        interrupt instances."""
        with cls._lock:
            if signals:
                cls._signals = set(signals)
                cls._reset_handlers()

            if cls._instances:
                # Only set the handlers if there are interrupt instances
                cls._set_handlers()

    @classmethod
    def _set_handlers(cls):
        with cls._lock:
            cls._reset_handlers()
            for _sig in cls._signals:
                cls._signal_handlers[_sig] = signal.signal(
                    _sig, cls.handle_signal)
        
    @classmethod
    def _reset_handlers(cls):
        with cls._lock:
            for _sig in list(cls._signal_handlers):
                signal.signal(_sig, cls._signal_handlers.pop(_sig))

    @classmethod
    def handle_signal(cls, signum, frame):
        with cls._lock:
            cls._signals_raised.append((signum, frame, time.time()))
            if cls._forced_interrupt():
                raise KeyboardInterrupt("Interrupt forced")

    @classmethod
    def _forced_interrupt(cls):
        """Return True if `_force_n` interrupts have been recieved in the past
        `_force_timeout` seconds"""
        with cls._lock:
            return (cls._force_n <= len(cls._signals_raised)
                    and
                    cls._force_timeout > (cls._signals_raised[-1][-1] -
                                          cls._signals_raised[-3][-1]))

    def __init__(self, ignore=True):
        self.ignore = ignore
        NoInterrupt._instances.add(self)
        self.catch_signals()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with self._lock:
            self._instances.remove(self)
            if not self._instances:
                # Only raise an exception if all the instances have been
                # cleared, otherwise we might still be in a protected
                # context somewhere.
                self._reset_handlers()
                if self:
                    # An interrupt was raised.
                    while self._signals_raised:
                        # Clear previous signals
                        self._signals_raised.pop()
                    if exc_type is None and not self.ignore:
                        raise KeyboardInterrupt()

    @classmethod
    def __bool__(cls):
        with cls._lock:
            return bool(cls._signals_raised)

    __nonzero__ = __bool__      # For python 2.


class CoroutineWrapper(object):
    """Wrapper for coroutine contexts that allows them to function as a context
    but also as a function.  Similar to open() which may be used both in a
    function or as a file object.  Note: be sure to call close() if you do not
    use this as a context.
    """
    def __init__(self, coroutine):
        self.coroutine = coroutine
        self.started = False

    def __enter__(self, *v, **kw):
        self.res = next(self.coroutine)   # Prime the coroutine
        self.started = True
        return self.send

    def __exit__(self, type, value, tb):
        self.close()
        return

    def send(self, *v):
        self.res = self.coroutine.send(*v)
        return self.res

    def __call__(self, *v):
        if not self.started:
            self.__enter__()
        return self.send(*v)

    def close(self):
        self.coroutine.close()


def coroutine(coroutine):
    """Decorator for a context that yeilds an function from a coroutine.

    This allows you to write functions that maintain state between calls.  The
    use as a context here ensures that the coroutine is closed.

    Examples
    --------
    Here is an example based on that suggested by Thomas Kluyver:
    http://takluyver.github.io/posts/readable-python-coroutines.html

    >>> @coroutine
    ... def get_have_seen(case_sensitive=False):
    ...     seen = set()    # Set of words already seen.  This is the "state"
    ...     word = (yield)
    ...     while True:
    ...         if not case_sensitive:
    ...             word = word.lower()
    ...         result = word in seen
    ...         seen.add(word)
    ...         word = (yield result)
    >>> with get_have_seen(case_sensitive=False) as have_seen:
    ...     print(have_seen("hello"))
    ...     print(have_seen("hello"))
    ...     print(have_seen("Hello"))
    ...     print(have_seen("hi"))
    ...     print(have_seen("hi"))
    False
    True
    True
    False
    True
    >>> have_seen("hi")
    Traceback (most recent call last):
       ...
    StopIteration

    You can also use this as a function (like open()) but don't forget to close
    it.
    >>> have_seen = get_have_seen(case_sensitive=True)
    >>> have_seen("hello")
    False
    >>> have_seen("hello")
    True
    >>> have_seen("Hello")
    False
    >>> have_seen("hi")
    False
    >>> have_seen("hi")
    True
    >>> have_seen.close()
    >>> have_seen("hi")
    Traceback (most recent call last):
       ...
    StopIteration

    """
    # @contextlib.contextmanager
    @functools.wraps(coroutine)
    def wrapper(*v, **kw):
        return CoroutineWrapper(coroutine(*v, **kw))
        # primed_coroutine = coroutine(*v, **kw)
        # next(primed_coroutine)
        # yield primed_coroutine.send
        # primed_coroutine.close()
    return wrapper
