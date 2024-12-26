import math
import numpy as np

from scipy.special import ellipe, ellipk, lambertw

__all__ = ["ellipk", "ellipkinv"]


def ellipkinv(K, iter=4):
    """Inverse of `K = ellipk(m)` computed using a NFNI method.

    Never Failing Newton Initialization (NFNI) from

    J. P. Boyd (2015), CPC 196, 13-18:
    https://doi.org/10.1016/j.cpc.2015.05.006

    Examples
    --------
    >>> Ks = 10**np.linspace(-10, 1.0, 1000)
    >>> ms = list(map(ellipkinv, Ks))
    >>> print(abs((ellipk(ms)/Ks - 1)).max() < 1e-10)
    True
    >>> ellipkinv(np.pi/2.0)
    0.0
    """
    lam = K - np.pi / 2.0
    if lam == 0:
        return 0.0
    elif lam < 0:
        # Not in paper: from asymptotic expansion
        m = (-((lambertw(-K / 4, -1) / K) ** 2)).real
    else:
        m = 1 - np.exp(
            -lam
            * ((8 / np.pi + lam * 2.9619147279597561) / (1 + lam * 1.480957363979878))
        )
    for i in range(iter):
        # Only 4 iterations are needed
        K_m, E_m = ellipk(m), ellipe(m)
        f = K_m - K
        df = (E_m - (1 - m) * K_m) / (2 * m * (1 - m))
        m -= f / df
    return m


def step(t, t1, alpha=3.0, d=0):
    r"""Smooth step function that goes from 0 at time ``t=0`` to 1 at time
    ``t=t1``.  This step function is $C_\infty$:

    Arguments
    ---------
    t : float
        Independent variable.
    t1 : float
        Parameter defining length of step (from 0 to t1).
    alpha : float
        Shape parameter.  Larger values are steeper.
    d : [0, 1]:
        Return the d'th derivative.
    """
    if t < 0.0:
        return 0.0
    elif t < t1:
        if d == 0:
            return (1 + math.tanh(alpha * math.tan(math.pi * (2 * t / t1 - 1) / 2))) / 2
        elif d == 1:
            # This has overflow issues...
            theta = math.pi * t / t1
            try:
                return (math.pi * alpha) / (
                    (2 * t1)
                    * (math.sin(theta) * math.cosh(alpha / math.tan(theta))) ** 2
                )
            except OverflowError:
                return 0.0
        else:
            raise NotImplementedError(f"Only d=0 or d=1 supported (got {d=})")
    else:
        if d == 0:
            return 1.0
        else:
            return 0.0


def mstep(t, t1, alpha=3.0, d=0):
    r"""Smooth step function that goes from 0 at time ``t=0`` to 1 at time
    ``t=t1``. This step function is $C_\infty$:

    This is a vectorized version of `step()` using np.piecewise.

    Arguments
    ---------
    t : array-like
        Independent variable.
    t1 : float
        Parameter defining length of step (from 0 to t1).
    alpha : float
        Shape parameter.  Larger values are steeper.
    d : [0, 1]:
        Return the d'th derivative.
    """
    t = np.asarray(t)
    theta = np.pi * t / t1
    if d == 0:
        return np.piecewise(
            theta,
            [theta <= 0.0, np.logical_and(0 < theta, theta < np.pi)],
            [
                0.0,
                lambda theta: (1 - np.tanh(alpha / np.tan(theta))) / 2,
                1.0,
            ],
        )
    elif d == 1:
        with np.errstate(over="ignore"):
            # The cosh overflows here for small t, but this is not an issue since
            # the result is zero.
            return np.piecewise(
                theta,
                [theta < 0.0, np.logical_and(0 <= theta, theta < np.pi)],
                [
                    0.0,
                    lambda theta: (
                        (np.pi * alpha)
                        / (
                            (2 * t1)
                            * (np.sin(theta) * np.cosh(alpha / np.tan(theta))) ** 2
                        )
                    ),
                    0.0,
                ],
            )
    else:
        raise NotImplementedError(f"Only d=0 or d=1 supported (got {d=})")
