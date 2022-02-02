"""Optimization tools."""


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
    while f0 * f1 >= 0:
        x0, x1 = x1, x0 - factor * (x1 - x0)
        f0, f1 = f1, f(x1)
    return (x0, x1)


def usolve(f, a, *v, **kw):
    """Return the root of `f(x) = 0` with uncertainties propagated.

    Arguments
    ---------
    f : function
       Function to find root of `f(x) = 0`.  Note: this must work with only a
       single argument even if the solver supports `args` etc.  Thus, use
       `lambda x: f(x, ...)` or `functools.partial` if needed.
    solver : function
       Solver function (default is scipy.optimize.brentq).
    v, kw :
       Remaining arguments will be passed as `solver(f, a, *v, **kw)`.
    """
    from uncertainties.core import nominal_value, ufloat, AffineScalarFunc
    import scipy.optimize

    solver = kw.pop("solver", scipy.optimize.brentq)

    if not isinstance(f(a), AffineScalarFunc):
        # Just solve normally which is faster
        return solver(f, a, *v, **kw)

    x = solver(lambda _x: nominal_value(f(_x)), a, *v, **kw)
    _x = ufloat(x, 0)
    zero = f(_x)
    params = [_k for _k in zero.derivatives if _k is not _x]
    return x - sum(
        (_p - nominal_value(_p)) * zero.derivatives[_p] / zero.derivatives[_x]
        for _p in params
    )


def ubrentq(f, a, b, *v, **kw):
    """Version of `scipy.optimize.brentq` with uncertainty processing using the
    uncertainties package.
    """
    from uncertainties import nominal_value

    return usolve(f, nominal_value(a), nominal_value(b), *v, **kw)
