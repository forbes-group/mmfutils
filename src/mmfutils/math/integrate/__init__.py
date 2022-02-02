"""Integration Utilities.
"""
import itertools
import logging
import warnings

import numpy as np

sp = None
numba = None
try:
    import scipy.integrate

    sp = scipy
    import numba
except ImportError:  # pragma: no cover
    pass

try:
    from ._ssum import ssum as _ssum_cython
except ImportError:
    _ssum_cython = None

__all__ = ["quad", "mquad", "Richardson", "rsum"]

_ABS_TOL = 1e-12
_REL_TOL = 1e-8
_EPS = np.finfo(float).eps


def quad(f, a, b, epsabs=_ABS_TOL, epsrel=_REL_TOL, limit=1000, points=None, **kwargs):
    r"""
    An improved version of integrate.quad that does some argument
    checking and deals with points properly.

    Return (ans, err).

    Examples
    --------
    >>> def f(x): return 1./x**2
    >>> (ans, err) = quad(f, 1, np.inf, points=[])
    >>> abs(ans - 1.0) < err
    True
    >>> (ans, err) = quad(f, 1, np.inf, points=[3.0, 2.0])
    >>> abs(ans - 1.0) < err
    True

    """
    if points is not None:
        points = [p for p in points if p < b]
        points = [p for p in points if a < p]
        if 0 == len(points):
            points = None

    if (points is None) or (b < np.inf):
        (y, err) = sp.integrate.quad(
            func=f,
            a=a,
            b=b,
            args=(),
            full_output=0,
            epsabs=epsabs,
            epsrel=epsrel,
            limit=limit,
            points=points,
            **kwargs
        )
    else:
        midp = max(points)
        (y0, err0) = sp.integrate.quad(
            func=f,
            a=a,
            b=midp,
            args=(),
            full_output=0,
            epsabs=epsabs,
            epsrel=epsrel,
            limit=limit,
            points=points,
            **kwargs
        )

        (y1, err1) = sp.integrate.quad(
            func=f,
            a=midp,
            b=b,
            args=(),
            full_output=0,
            epsabs=epsabs,
            epsrel=epsrel,
            limit=limit,
            points=None,
            **kwargs
        )
        y = y0 + y1
        err = err0 + err1
    return (y, err)


def mquad(
    f,
    a,
    b,
    abs_tol=_ABS_TOL,
    verbosity=0,
    fa=None,
    fb=None,
    save_fx=False,
    res_dict=None,
    max_fcnt=10000,
    min_step_size=None,
    norm=lambda x: abs(np.array(x)).max(),
    points=None,
):
    r"""Return (res, err) where res is the numerically evaluated
    integral using adaptive Simpson quadrature.

    mquad tries to approximate the integral of function
    f from a to b to within an error of abs_tol using recursive
    adaptive Simpson quadrature.  mquad allows the
    function y = f(x) to be array-valued.  In the matrix valued case,
    the infinity norm of the matrix is used as it's "absolute value".

    Parameters
    ----------
    f : function
        Possibly array valued function to integrate.  If this
        emits a NaN, then an AssertionError is raised to allow the
        user to optimize this check away (as it exists in the core
        of the loops)
    a, b : float
        Integration range (a, b)
    fa, fb : float
        f(a) and f(b) respectively (if already computed)
    abs_tol : float
        Approximate absolute tolerance on integral
    verbosity : int
        Display info if greater than zero. Shows the values of
        [fcnt a b-a Q] during the iteration.
    save_fx : bool
        If True, then save the abscissa and function values in
        res_dict.
    res_dict : dict
        Details are stored here. Pass a dictionary to access these.
        The dictionary will be modified.

        fcnt : Number of function evaluations.
        xy : List of pairs (x, f(x)) if save_fx is defined.
    max_fcnt : int
        Maximum number of function evaluations.
    min_step_size : float
        Minimum step size to limit recursion.
    norm : function
        Norm to use to determine convergence.  The absolute error is
        determined as `norm(f(x) - F)`.
    points : [float]
        List of special points to be included in abscissa.

    Notes
    -----
    Based on "adaptsim" by Walter Gander.
    Ref: W. Gander and W. Gautschi, "Adaptive Quadrature Revisited", 1998.
    http://www.inf.ethz.ch/personal/gander

    Examples
    --------

    Orthogonality of planewaves on [0, 2pi]

    >>> def f(x):
    ...     v = np.exp(1j*np.array([[1.0, 2.0, 3.0]])*x)
    ...     return v.T.conj()*v/2.0/np.pi
    >>> ans = mquad(f, 0, 2*np.pi)
    >>> abs(ans - np.eye(ans.shape[0])).max() < _ABS_TOL
    True

    >>> res_dict = {}
    >>> def f(x): return x**2
    >>> ans = mquad(f, -2, 1, res_dict=res_dict, save_fx=True)
    >>> abs(ans - 3.0) < _ABS_TOL
    True
    >>> x = np.array([xy[0] for xy in res_dict['xy']])
    >>> y = np.array([xy[1] for xy in res_dict['xy']])
    >>> abs(y - f(x)).max()
    0.0

    # This works, but triggers a warning because of the singular
    # endpoints.
    >>> logger = logging.getLogger()
    >>> logger.disabled = True
    >>> def f(x): return 1.0/np.sqrt(x) + 1.0/np.sqrt(1.0-x)
    >>> abs(mquad(f, 0, 1, abs_tol=1e-8) - 4.0) < 1e-8
    True
    >>> logger.disabled = False

    >>> def f(x):
    ...     if x < 0:
    ...         return 0.0
    ...     else:
    ...         return 1.0
    >>> abs(mquad(f, -2.0, 1.0) - 1.0) < 1e-10
    True

    >>> def f(x): return 1./x
    >>> mquad(f, 1, np.inf)
    Traceback (most recent call last):
        ...
    ValueError: Infinite endpoints not supported.
    """
    points = [] if points is None else points
    res_dict = {} if res_dict is None else res_dict

    assert isinstance(res_dict, dict), "res_dict must be a dictionary"
    if not (np.isfinite(a) and np.isfinite(b)):
        raise ValueError("Infinite endpoints not supported.")

    res_dict["fcnt"] = 0

    if min_step_size is None:
        min_step_size = _EPS / 1024.0 * abs(b - a)

    # We augment and decorate the function to pass various related
    # arguments to the helpers.
    if save_fx:
        res_dict["xy"] = []

        def f(x, f=f):
            y = f(x)
            res_dict["xy"].append((x, y))
            res_dict["fcnt"] += 1
            assert not np.any(np.isnan(y)), "Nan encountered: " "f({}) = {}".format(
                x, y
            )
            return y

    else:

        def f(x, f=f):
            res_dict["fcnt"] += 1
            y = f(x)
            assert not np.any(np.isnan(y)), "Nan encountered: " "f({}) = {}".format(
                x, y
            )
            return y

    f.__dict__["res_dict"] = res_dict
    f.__dict__["max_fcnt"] = max_fcnt
    f.__dict__["norm"] = norm

    fa = f(a) if fa is None else fa
    fb = f(b) if fb is None else fb

    xs = list(set(p for p in points if a < p and p < b))
    xs.sort()
    ys = list(map(f, xs))
    xs.insert(0, a)
    ys.insert(0, fa)
    xs.append(b)
    ys.append(fb)

    xs_ = []
    ys_ = []
    for i, a_ in enumerate(xs[:-1]):
        b_ = xs[i + 1]
        fa_ = ys[i]

        # Subdivide each interval into three unequal segments.
        h = 0.13579 * (b_ - a_)
        x1 = a_ + 2.0 * h
        x2 = b_ - 2.0 * h
        fx1 = f(x1)
        fx2 = f(x2)

        xs_.extend([a_, x1, x2])
        ys_.extend([fa_, fx1, fx2])

    xs_.append(b)
    ys_.append(fb)

    # Increase the tolerance so that roundoff errors from each
    # interval will not accumulate too much.
    abs_tol2 = abs_tol ** 2 / float(len(xs_) - 1)

    res = 0.0
    err2 = 0.0

    for i, a_ in enumerate(xs_[:-1]):
        # Call the recursive core integrator on each region.
        b_ = xs_[i + 1]
        fa_ = ys_[i]
        fb_ = ys_[i + 1]

        # Fudge endpoints to avoid infinities.
        if f.norm(fa_) == np.inf:
            fa_ = f(a_ + _EPS * (b_ - a_))

        if f.norm(fb_) == np.inf:
            fb_ = f(b_ - _EPS * (b_ - a_))

        r, e2 = _mquadstep(f, a_, b_, fa_, fb_, abs_tol2, min_step_size, verbosity)
        res += r
        err2 += e2

    res_dict["err"] = np.maximum(np.sqrt(err2), abs(_EPS * res))
    return res


def _mquadstep(f, a, b, fa, fb, abs_tol2, min_step_size, verbosity, fmid=None):
    r"""Recursive core routine for function mquad.

    Parameters
    ----------
        f : function
        a, b : float
            Endpoints and midpoint of interval `a` < `b`
        fa, fb, fmid: float, complex, or arrays
            `f(a)`, `f(b)`, `f(mid)` where `mid=(a+b)/2`.  Only provide
            `fmid` if it has been computed.
        abs_tol2 : float
            `abs_tol**2`
    """

    # Evaluate integrand twice in interior of subinterval [a, b].
    h = b - a
    c = (a + b) / 2.0
    if fmid is None:
        fc = f(c)
    else:
        fc = fmid

    # Three point Simpson's rule.
    Q0 = (h / 6.0) * (fa + 4.0 * fc + fb)
    err = f.norm(Q0 - (fa + fb) * h / 2.0)

    ac = (a + c) / 2.0
    cb = (c + b) / 2.0

    if abs(h) < min_step_size or ac <= a or b <= cb:
        # Minimum step size reached; singularity possible.
        logging.warning(
            " ".join(
                [
                    "mquad:MinStepSize:",
                    "Minimum step size reached.",
                    "({} < {})".format(abs(h), min_step_size),
                    "Singularity possible (err = {}).".format(err),
                ]
            )
        )

        return Q0, err * err

    if f.res_dict["fcnt"] > f.max_fcnt:  # pragma: no cover
        logging.warning(
            " ".join(
                [
                    "mquad:MaxFcnCount:",
                    "Maximum function count {} exceeded.".format(f.max_fcnt),
                    "Singularity likely.",
                ]
            )
        )
        return Q0, err * err

    fac = f((a + c) / 2.0)
    fcb = f((c + b) / 2.0)

    # Five point double Simpson's rule.
    Q1 = (h / 12.0) * (fa + 4.0 * fac + 2.0 * fc + 4.0 * fcb + fb)

    # One step of Romberg extrapolation.
    Q = Q1 + (Q1 - Q0) / 15.0

    # Check accuracy of integral over this subinterval.
    err2 = f.norm(Q1 - Q) ** 2

    if not np.isfinite(f.norm(Q)):  # pragma: no cover
        # Infinite or Not-a-Number function value encountered.
        logging.warning(
            " ".join(
                ["mquad:ImproperFcnValue:", "Inf or NaN function value encountered."]
            )
        )
        return Q, err2

    if 1 < verbosity:  # pragma: no cover
        print(a, h, f.norm(Q))

    if err2 <= abs_tol2:
        # We are done.
        pass
    else:
        # Subdivide region.
        Qac, err_ac2 = _mquadstep(
            f, a, c, fa, fc, abs_tol2 / 2.0, min_step_size, verbosity, fmid=fac
        )
        Qcb, err_cb2 = _mquadstep(
            f, c, b, fc, fb, abs_tol2 / 2.0, min_step_size, verbosity, fmid=fcb
        )
        Q = Qac + Qcb
        err2 = err_ac2 + err_cb2

    return Q, np.maximum(err2, (_EPS * Q) ** 2)


def Richardson(f, ps=None, l=2, n0=1):
    r"""Compute the Richardson extrapolation of $f$ given the function

    .. math::
       f(N) = f + \sum_{n=0}^{\infty} \frac{\alpha_n}{N^{p_n}}

    The extrapolants are stored in the array `S`[n, s] where
    `S[n, 0] = f(n0*l**n)` and `S[n, s]` is the s'th extrapolant.

    .. note:: It is crucial for performance that the powers $p_n$ be properly
       characterized.  If you do not know the form of the errors, then consider
       using a non-linear acceleration technique such as :func:`levin_sum`.

    Parameters
    ----------
    ps : iterable
       Iterable returning the powers $p_n$.  To generate the sequence $p_0 + m
      d_p$  for example, use :func:`itertools.count``(p0, dp)`.

    Examples
    --------
    Here we consider

    .. math::
       f(N) = \sum_{n=1}^{N} \frac{1}{n^2} = \frac{\pi^2}{6} +
              \order(N^{-1})

    >>> def f(N): return sum(np.arange(1, N+1, dtype=float)**(-2))
    >>> r = Richardson(f, l=3, n0=2)
    >>> for n in range(9):
    ...     x = next(r)
    >>> err = abs(x - np.pi**2/6.0)
    >>> assert err < 1e-14, 'err'

    Now some other examples with different `p` values:

    .. math::
       f(N) = \sum_{n=1}^{N} \frac{1}{n^4} = \frac{\pi^4}{90} +
              \order(N^{-3})

    >>> def f(N): return sum(np.arange(1, N+1, dtype=float)**(-4))
    >>> r = Richardson(f, ps=itertools.count(3,1))
    >>> for n in range(8):
    ...     x = next(r)
    >>> err = abs(x - np.pi**4/90.0)
    >>> assert err < 1e-14, 'err'

    .. math::
       f(N) = \sum_{n=1}^{N} \frac{1}{n^6} = \frac{\pi^6}{945} +
              \order(N^{-5})

    >>> def f(N): return sum(np.arange(1, N+1, dtype=float)**(-6))
    >>> r = Richardson(f, ps=itertools.count(5))
    >>> for n in range(7):
    ...     x = next(r)
    >>> err = abs(x - np.pi**6/945.0)
    >>> assert err < 1e-14, 'err'

    Richardson works with array valued functions:

    >>> def f(N): return np.array([sum(np.arange(1, N+1, dtype=float)**(-2)),
    ...                            sum(np.arange(1, N+1, dtype=float)**(-4))])
    >>> r = Richardson(f, l=3, n0=2)
    >>> for n in range(7):
    ...     x = next(r)
    >>> err = abs(x - np.array([np.pi**2/6.0, np.pi**4/90.0])).max()
    >>> assert err < 1e-13, 'err'

    It also works for complex valued functions:

    >>> def f(N): return (sum(np.arange(1, N+1, dtype=float)**(-2)) +
    ...                       1j*sum(np.arange(1, N+1, dtype=float)**(-4)))
    >>> r = Richardson(f, l=3, n0=2)
    >>> for n in range(7):
    ...     x = next(r)
    >>> err = abs(x - (np.pi**2/6.0 + 1j*np.pi**4/90.0))
    >>> assert err < 1e-13, 'err'
    """
    if ps is None:
        ps = itertools.count(1, 1)

    n = 0
    f0 = f(n0)
    if hasattr(f0, "shape"):
        # Allows us to deal with array valued functions
        S = np.zeros((n + 1, n + 1) + f0.shape, dtype=f0.dtype)
    else:
        S = np.zeros((n + 1, n + 1), dtype=type(f0))

    p = []
    while True:
        if S.shape[0] <= n:
            new_shape = np.array(S.shape)
            new_shape[:2] *= 2
            Snew = np.empty(new_shape, dtype=S.dtype)
            Snew[0 : S.shape[0], 0 : S.shape[1]] = S[:, :]
            S = Snew
        if 0 == l:  # pragma: no cover (What is this?)
            S[n, 0] = f0
        else:
            S[n, 0] = f(n0 * l ** n)
        p.append(next(ps))
        for m in range(1, n + 1):
            lpm1 = float(l ** p[m - 1])
            S[n, m] = (lpm1 * S[n, m - 1] - S[n - 1, m - 1]) / (lpm1 - 1.0)
        n = n + 1
        yield S[n - 1, n - 1]


def exact_add(a, b):
    """Exact addition.  Return (x, err) so that using exact addition
    x + err == a + b but using floating point x + err == x

    This is based on the fact that, with IEEE floating point
    if abs(b) <= abs(a):
        x = a + b               # Floating point sum
        err = (a - x) + b       # Exact error

    >>> exact_add(1e18, 1)
    (1e+18, 1.0)

    """
    if abs(a) < abs(b):
        x = b + a
        err = (b - x) + a
    else:
        x = a + b
        err = (a - x) + b
    return (x, err)


def exact_sum(xs, maxiter=5):
    """Compute the sum of all values in xs exactly.

    Return (ans, err) where err is an array whose sum is the exact
    err, and ans is the sum.

    Arguments
    ---------
    xs : list
       Numbers to be summed
    maxiter : int
       Maximum number of iterations.  The function tries to make
       return a result such that `ans + sum(err) == ans` but gives up
       if more than this many iterations are required.

    Examples
    --------

    >>> (x, err) = exact_sum([2e100, 2e51, 2, 2e-50, -2])
    >>> x
    2e+100
    >>> err
    [2e+51, 2e-50]
    >>> exact_sum([1e100]*100 + [2e100, 2e51, 2, 2e-50, -2])
    (1.02e+102, [2.7197364491160207e+85, 2e+51, 2e-50])
    """
    ans = 0.0
    err = []
    for b in xs:
        (ans, err0) = exact_add(ans, b)
        for n in range(len(err)):
            (err[n], err0) = exact_add(err[n], err0)
        if err0 != 0:
            err.append(err0)

    err = [e for e in err if e != 0]
    max_iter = 5
    while (sum(list(reversed(err))) + ans) != ans:
        max_iter -= 1
        if max_iter < 0:  # pragma: no cover (never get here?)
            # Prevent infinite looping.
            break
        ans, err = exact_sum(err + [ans])
    return (ans, err)


def ssum_python(xs):
    r"""Return (sum(xs), err) computed stably using Kahan's summation
    method for floating point numbers.  (Python version.)

    >>> N = 10000
    >>> l = [(10.0*n)**3.0 for n in reversed(range(N+1))]
    >>> ans = 250.0*((N + 1.0)*N)**2
    >>> (ssum_python(l)[0] - ans, sum(l) - ans)
    (0.0, -5632.0)
    """
    sum = 0.0
    carry = 0.0
    for x in xs:
        y = x - carry
        tmp = sum + y
        carry = (tmp - sum) - y
        sum = tmp

    eps = np.finfo(np.double).eps
    err = max(abs(2.0 * sum * eps), len(xs) * eps * eps)

    return (sum, err)


if numba:

    @numba.jit(nopython=True)
    def ssum_numba(xs, _eps=_EPS):
        r"""Return (sum(xs), err) computed stably using Kahan's summation
        method for floating point numbers.  (Numba version.)

        >>> N = 10000
        >>> l = np.array([(10.0*n)**3.0 for n in reversed(range(N+1))])
        >>> ans = 250.0*((N + 1.0)*N)**2
        >>> (ssum_numba(l)[0] - ans, sum(l) - ans)
        (0.0, -5632.0)

        Should run less than 8 times slower than a regular sum.
        >>> import time
        >>> n = 1./np.arange(1, 2**10)
        >>> t = time.time();tmp = n.sum();t0 = time.time() - t;
        >>> np.allclose(n.sum(), ssum_numba(n)[0])
        True
        >>> t = time.time();tmp = ssum_numba(n);t1 = time.time() - t;
        >>> t1 < 8.0*t0
        True
        """
        sum = 0.0
        carry = 0.0
        for x in xs:
            y = x - carry
            tmp = sum + y
            carry = (tmp - sum) - y
            sum = tmp

        err = max(abs(2.0 * sum * _eps), len(xs) * _eps * _eps)
        return (sum, err)


def ssum_cython(xs, _eps=_EPS):
    xs = np.asarray(xs)
    if _ssum_cython is None:
        warnings.warn("ImportError: Could not _ssum_cython: using slow version")
        return ssum_python(xs)

    sum = _ssum_cython(xs)
    ##if isinstance(xs.dtype, np.inexact):
    #    eps = np.finfo(xs.dtype).eps
    # else:
    #    eps = 0.0
    err = max(abs(2.0 * sum * _eps), len(xs) * _eps * _eps)
    return (sum, err)


def ssum(xs):
    r"""Return (sum(xs), err) computed stably using Kahan's summation
    method for floating point numbers.  (C++ version using weave).

    >>> N = 10000
    >>> l = [(10.0*n)**3.0 for n in reversed(range(N+1))]
    >>> ans = 250.0*((N + 1.0)*N)**2
    >>> (ssum(l)[0] - ans, sum(l) - ans)
    (0.0, -5632.0)

    Here is an example of the Harmonic series.  Series such as these
    should be summed in reverse, but ssum should do it well.
    >>> sn = 1./np.arange(1, 10**4)
    >>> Hn, Hn_err = exact_sum(sn)
    >>> ans, err = ssum(sn)
    >>> abs(ans - Hn) < err
    True
    >>> abs(sum(sn) - Hn) < err # Normal sum not good!
    False
    >>> abs(sum(list(reversed(sn))) - Hn) < err # Unless elements sorted
    True

    Here is an example where the truncation errors are tested.
    >>> try: long = long
    ... except: long = int
    >>> N = 10000
    >>> np.random.seed(3)
    >>> r = np.random.randint(-2**30, 2**30, 4*N)
    >>> A = np.array([long(a)*2**90 + long(b)*2**60 + long(c)*2**30 + long(d)
    ...      for (a, b, c, d) in zip(r[:N], r[N:2*N], r[2*N:3*N], r[3*N:4*N])])
    >>> B = A.astype(float)/3987.0 # Introduce truncation errors
    >>> exact_ans = A.sum()
    >>> ans, err = ssum(B)
    >>> ans *= 3987.0
    >>> err *= 3987.0
    >>> exact_err = abs(float(long(ans) - exact_ans))
    >>> exact_err < err
    True
    >>> exact_err < err/1000.0
    False
    """
    return ssum_cython(xs)


def rsum(f, N0=0, ps=None, l=2, abs_tol=_ABS_TOL, rel_tol=_REL_TOL, verbosity=0):
    """Sum f using Richardson extrapolation.

    Examples
    --------
    >>> def f(n):
    ...     return 1./(n+1)**2
    >>> res, err = rsum(f)
    >>> res
    1.6449340668...
    >>> abs(res - np.pi**2/6.0) < err
    True
    """

    def F(N, f=f, fs=[0.0, 0]):
        r"""Return sum of f(n) up to f(N)."""
        fs[0] += ssum([f(n + N0) for n in range(fs[1], N + 1)])[0]
        fs[1] = N + 1
        return fs[0]

    r = Richardson(F, ps=ps, l=l)
    r1 = next(r)
    while True:
        r0 = r1
        r1 = next(r)
        abs_err = abs(r1 - r0)
        rel_err = abs_err / (abs(r1) + abs_tol)
        if abs_err <= abs_tol or rel_err <= rel_tol:
            break
        if verbosity > 0:  # pragma: no cover
            logging.info("{} +- {}".format(r1, abs_err))
    return r1, abs_err
