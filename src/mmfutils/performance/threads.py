"""Thread Control

This module provides control of the number of threads used by the MKL and
numexpr.  It uses the global set SET_THREAD_HOOKS which should contain
functions that take a single argument and set the number of threads for that
particular part of the system.

Use `set_num_threads(nthreads)` to call all of these hooks.
"""
SET_THREAD_HOOKS = set()


def set_num_threads(nthreads):
    """Set the maximum number of threads to use.

    Calls all the hooks in `mmfutils.performance.threads.SET_THREAD_HOOKS`
    """
    global SET_THREAD_HOOKS
    for set_num_threads in SET_THREAD_HOOKS:
        set_num_threads(nthreads)


try:  # pragma: nocover  Can't do this on public CI servers
    import mkl

    MKL_NUM_THREADS = mkl.get_max_threads()
    SET_THREAD_HOOKS.add(mkl.set_num_threads)
except ImportError:  # pragma: nocover
    pass

try:
    import numexpr

    if numexpr:
        SET_THREAD_HOOKS.add(numexpr.set_num_threads)
        SET_THREAD_HOOKS.add(numexpr.set_vml_num_threads)
except ImportError:  # pragma: nocover
    pass
