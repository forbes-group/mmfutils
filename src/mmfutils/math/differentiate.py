"""Differentiation."""
import itertools

import numpy as np

from mmfutils.math.integrate import Richardson

__all__ = ["differentiate", "hessian"]


def differentiate(f, x=0.0, d=1, h0=1.0, l=1.4, nmax=10, dir=0, p0=1, err=[0]):
    r"""Evaluate the numerical dth derivative of f(x) using a Richardson
    extrapolation of the finite difference formula.

    Parameters
    ----------
    f : function
       The function to compute the derivative of.
    x : {float, array}
       The derivative is computed at this point (or at these points if
       the function is vectorized.
    d : int, optional
       Order of derivative to compute.  `d=0` is the function `f(x)`,
      `d=1` is the first derivative etc.
    h0 : float, optional
       Initial stepsize.  Should be on about a factor of 10 smaller
       than the typical scale over which `f(x)` varies significantly.
    l : float, optional
       Richardson extrapolation factor.  Stepsizes used are `h0/l**n`
    nmax : int, optional
       Maximum number of extrapolation steps to take.
    dir : int, optional
        If `dir < 0`, then the function is only evaluated to the
        left, if positive, then only to the right, and if zero, then
        centered form is used.

    Returns
    -------
    df : {float, array}
       Order `d` derivative of `f` at `x`.

    Other Parameters
    ----------------
    p0 : int, optional
       This is the first non-zero term in the taylor expansion of either the
       difference formula.  If you know that the first term is zero (because of
       the coefficient), then you should set `p0=2` to skip that term.

       .. note:: This is not the power of the term, but the order.
          For centered difference formulae, `p0=1` is the `h**2` term,
          which would vanish if third derivative vanished at `x` while
          for the forward difference formulae this is the `h` term
          which is absent if the second derivative vanishes.

    err[0] : float
       This is mutated to provide an error estimate.

    Notes
    -----
    This implementation uses the Richardson extrapolation to
    extrapolate the answer.  This is based on the following Taylor
    series error formulae:

    .. math::
       f'(x) &= \frac{f(x+h) - f(x)}{h} - h \frac{f'')}{2} + \cdots\\
             &= \frac{f(x+h) - f(x-h)}{2h} - h^2 \frac{f''}{3!} + \cdots\\
       f''(x) &= \frac{f(x+2h) - 2f(x+h) + f(x)}{h^2} - hf^{(3)} + \cdots\\
              &= \frac{f(x+h) -2f(x) + f(x-h)}{h^2}
                 - 2h^2 \frac{f^{(4)}}{4!} + \cdots\\

    If we let $h = 1/N$ then these formula match the expected error
    model for the Richardson extrapolation

    .. math::
       S(h) = S(0) + ah^{p} + \order(h^{p+1})

    with $p=1$ for the one-sided formulae and $p=2$ for the centered
    difference formula respectively.

    See :class:`mmf.math.integrate.Richardson`

    See Also
    --------
    :func:`mmfutils.math.integrate.Richardson` : Richardson extrapolation


    Examples
    --------
    >>> from math import sin, cos
    >>> x = 100.0
    >>> assert(abs(differentiate(sin, x, d=0)-sin(x))<1e-15)
    >>> assert(abs(differentiate(sin, x, d=1)-cos(x))<1e-14)
    >>> assert(abs(differentiate(sin, x, d=2)+sin(x))<1e-13)
    >>> assert(abs(differentiate(sin, x, d=3)+cos(x))<1e-11)
    >>> assert(abs(differentiate(sin, x, d=4)-sin(x))<1e-9)
    >>> differentiate(abs, 0.0, d=1, dir=1)
    1.0
    >>> differentiate(abs, 0.0, d=1, dir=-1)
    -1.0
    >>> differentiate(abs, 0.0, d=1, dir=0)
    0.0

    Note that the Richardson extrapolation assumes that `h0` is small
    enough that the truncation errors are controlled by the taylor
    series and that the taylor series properly describes the behaviour
    of the error.  For example, the following will not converge well,
    even though the derivative is well defined:

    >>> def f(x):
    ...     return np.sign(x)*abs(x)**(1.5)
    >>> df = differentiate(f, 0.0)
    >>> abs(df) < 0.1
    True
    >>> abs(df) < 0.01
    False
    >>> abs(differentiate(f, 0.0, nmax=100)) < 3e-8
    True

    Sometimes, one may compensate by increasing nmax.  (One could in
    principle change the Richardson parameter p, but this is optimized
    for analytic functions.)

    The :func:`differentiate` also works over arrays if the function
    `f` is vectorized:

    >>> x = np.linspace(0, 100, 10)
    >>> assert(max(abs(differentiate(np.sin, x, d=1) - np.cos(x))) < 3e-15)
    """
    if 0 == d:
        return f(x)

    if 2 < d:

        def df(x):
            return differentiate(f=f, x=x, d=d - 2, h0=h0, dir=dir, l=l, nmax=nmax)

        return differentiate(df, x=x, d=2, h0=h0, dir=dir, l=l, nmax=nmax, err=err)

    def df(N, x=x, d=d, dir=dir, h0=h0):
        h = float(h0) / N
        h = (x + h) - x
        if 1 == d:
            if dir < 0:
                return (f(x) - f(x - h)) / h
            elif dir > 0:
                return (f(x + h) - f(x)) / h
            else:
                return (f(x + h) - f(x - h)) / (2 * h)
        elif 2 == d:
            if dir < 0:
                return (f(x - 2 * h) - 2 * f(x - h) + f(x)) / (h * h)
            elif dir > 0:
                return (f(x + 2 * h) - 2 * f(x + h) + f(x)) / (h * h)
            else:
                return (f(x + h) - 2 * f(x) + f(x - h)) / (h * h)

    p = 2 if dir == 0 else 1

    r = Richardson(df, ps=itertools.count(p * p0, p), l=l)
    next(r)
    d1 = next(r)
    d0 = next(r)
    err_old = abs(d1 - d0)
    n = 2
    for _d in r:
        n += 1
        err[0] = abs(_d - d0)
        d0 = _d
        if np.any(err[0] > err_old) or (n > nmax):
            break
        err_old = err[0]
    return next(r)


def hessian(f, x, **kw):
    r"""Return the gradient Hessian matrix of `f(x)` at `x` using
    :func:`differentiate`.  This is not efficient.

    Parameters
    ----------
    f : function
       Scalar function of an array.
    x : array-like
       Derivatives evaluated at this point.
    kw : dict
       See :func:`differentiate` for options.

    Examples
    --------
    >>> def f(x): return np.arctan2(*x)
    >>> def df(x): return np.array([x[1], -x[0]])/np.sum(x**2)
    >>> def ddf(x):
    ...     return np.array([[-2.*x[0]*x[1], -np.diff(x**2)[0]],
    ...                      [-np.diff(x**2)[0], 2.*x[0]*x[1]]])/np.sum(x**2)**2
    >>> x = [0.1, 0.2]
    >>> D, H = hessian(f, x, h0=0.1)
    >>> x= np.asarray(x)
    >>> D, df(x)
    (array([ 4., -2.]), array([ 4., -2.]))
    >>> H, ddf(x)
    (array([[-16., -12.],
            [-12.,  16.]]),
     array([[-16., -12.],
            [-12.,  16.]]))
    """
    x = np.asarray(x)
    N = len(x)

    def _f(_x, x0=x):
        r"""Shift arguments to be about zero."""
        return f(_x + x)

    f0 = f(0 * x)
    D = np.empty(N, dtype=np.dtype(f0))
    H = np.empty((N,) * 2, dtype=np.dtype(f0))

    def _f_m_n(_xm, m, _xn=None, n=None):
        r"""Return `f(x)` where `x[m,n]` are offset by `_x[m,n]`."""
        x = np.zeros(N, dtype=float)
        x[m] = _xm
        if n is not None:
            x[n] = _xn
        return _f(x)

    for m in range(len(x)):
        D[m] = differentiate(lambda _x: _f_m_n(_x, m=m), d=1, **kw)
        H[m, m] = differentiate(lambda _x: _f_m_n(_x, m=m), d=2, **kw)
        for n in range(m + 1, len(x)):
            H[m, n] = H[n, m] = differentiate(
                lambda _xn: differentiate(lambda _xm: _f_m_n(_xm, m, _xn, n), **kw),
                **kw
            )
    return D, H
