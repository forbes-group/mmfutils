"""Optimization tools.
"""
from __future__ import division, absolute_import


def bracket_monotonic(f, x0=0.0, x1=1.0, factor=2.0):
    """Return `(x0, x1)` where `f(x0)*f(x1) < 0`.

    Assumes that `f` is monotonic and that the root exists.

    Proceeds by increasing the size of the interval by `factor` in the
    direction of the root until the root is found.

    Examples
    --------

    >>> import math
    >>> bracket_monotonic(lambda x:10 - math.exp(x))
    (0.0, 3.0)
    >>> bracket_monotonic(lambda x:10 - math.exp(-x), factor=1.5)
    (4.75, -10.875)
    """
    assert abs(x1 - x0) > 0
    assert factor > 1.0
    f0 = f(x0)
    f1 = f(x1)
    if f1 < f0:
        x0, x1 = x1, x0
        f0, f1 = f1, f0
    while f0*f1 >= 0:
        x0, x1 = x1, x0 - factor*(x1-x0)
        f0, f1 = f1, f(x1)
    return (x0, x1)
