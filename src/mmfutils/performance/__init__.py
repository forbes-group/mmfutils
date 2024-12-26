"""Tools for high-performance computing.

This module may rely on many other packages that are not easy to install such
as pyfftw and the corresponding fftw implementation.
"""

import timeit
import numpy as np

__all__ = ["auto_timeit"]


def auto_timeit(
    stmt="pass",
    setup="pass",
    time=1.0,
    max_time=30,
    repeat=5,
    globals=None,
    display=True,
    format="{min_t: 8.4f} {unit} per loop (best of {repeat}, {number} loops)",
):
    """Custom wrapper for the :mod:`timeit` module.

    Arguments
    ---------
    time : float
        Desired execution time (s).  Will be used to determine the number of times to
        run the code.
    max_time : float
        If running the code takes more than this amount of time, then only a single run
        will be used.
    display : bool
        If `True`, then print the results.
    format : str
        Format string for printing.

    Returns
    -------
    (ts, number, factor, unit) if not display, else None.

    Examples
    --------

    >>> import time
    >>> def f(t):
    ...     time.sleep(t)
    >>> auto_timeit('f(t)', globals=dict(t=0.2, f=f))
    20...ms per loop (best of 5, 1 loops)

    You can increase the time if you don't mind waiting, and get better accuracy.

    >>> auto_timeit('f(t)', time=0.6, repeat=2, globals=dict(t=0.1, f=f))
    1...ms per loop (best of 2, 2 loops)

    If the test would exceed the maximum time, it simply uses a single loop:

    >>> auto_timeit('f(t)', max_time=0.1, globals=dict(t=0.05, f=f))
    5...ms per loop (best of 1, 1 loops)

    You can also get the results programmatically to do your own analysis:

    >>> ts, number, factor, unit = auto_timeit(
    ...     'f(t)', display=False, globals=dict(t=0.05, f=f))
    >>> len(ts), float(min(ts)), float(np.median(ts)), factor, unit
    (5, 0.05..., 0.05..., 1000, 'ms')
    """
    timer = timeit.Timer(stmt, setup, globals=globals)
    t = timer.timeit(number=1)
    number = min(max(1, int(time / t / repeat)), 100000000)
    if t * number * repeat < max_time:
        ts = np.divide(timer.repeat(repeat, number), number)
    else:
        ts = np.array([t])
        number = 1

    t0 = min(ts)
    prefix = int(np.floor(np.log(t0) / np.log(1000)))
    prefix = min(0, max(prefix, -3))
    unit = {0: "s", -1: "ms", -2: "μs", -3: "ns"}[prefix]
    factor = 1000 ** (-prefix)
    if display:
        print(
            format.format(
                number=number, repeat=len(ts), min_t=min(ts) * factor, unit=unit
            )
        )
    else:
        return ts, number, factor, unit
