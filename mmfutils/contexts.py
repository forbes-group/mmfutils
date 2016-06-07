"""Various useful contexts.
"""
import signal
import time

from threading import RLock


class NoInterrupt(object):
    """Suspend the various signals during the execution block.

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

    >>> def f(n, interrupted=False):
    ...     done = False
    ...     while not done and not interrupted:
    ...         n[0] += 1
    ...         if n[0] == 5:
    ...             # Simulate user interrupt
    ...             os.kill(os.getpid(), signal.SIGINT)
    ...             time.sleep(0.1)
    ...         n[1] += 1
    ...         done = n[0] >= 10

    >>> n = [0, 0]
    >>> try:
    ...     f(n)
    ... except KeyboardInterrupt:
    ...     print("Caught KeyboardInterrupt")
    Caught KeyboardInterrupt
    >>> n
    [5, 4]

    Now we protect the loop from interrupts.
    >>> n = [0, 0]
    >>> try:
    ...     with NoInterrupt() as interrupted:
    ...         f(n)
    ... except KeyboardInterrupt:
    ...     print("Caught KeyboardInterrupt")
    Caught KeyboardInterrupt
    >>> n
    [10, 10]

    If `f()` is slow, we might want to interrupt it at safe times.  This is
    what the `interrupted` flag is for:

    >>> n = [0, 0]
    >>> try:
    ...     with NoInterrupt() as interrupted:
    ...         f(n, interrupted)
    ... except KeyboardInterrupt:
    ...     print("Caught KeyboardInterrupt")
    Caught KeyboardInterrupt
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

    def __init__(self):
        NoInterrupt._instances.add(self)
        self.catch_signals()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with self._lock:
            self._instances.remove(self)
            if not self._instances:
                self._reset_handlers()
                if exc_type is None and self:
                    # Only raise an exception if all the interrupts have been
                    # cleared, otherwise we might still be in a protected
                    # context somewhere.
                    while self._signals_raised:
                        # Clear previous signals
                        self._signals_raised.pop()
                    raise KeyboardInterrupt()

    @classmethod
    def __nonzero__(cls):
        with cls._lock:
            return bool(cls._signals_raised)
