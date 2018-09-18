from __future__ import division, with_statement, print_function, absolute_import

import numpy as np

from scipy.special import ellipe, ellipk, lambertw

__all__ = ['ellipk', 'ellipkinv']


def ellipkinv(K, iter=4):
    """Inverse of `K = ellipk(m) computed using a NFNI method.
    
    Never Failing Newton Initialization (NFNI) from
    
    J. P. Boyd (2015), CPC 196, 13-18:
    https://doi.org/10.1016/j.cpc.2015.05.006
    
    Examples
    --------
    >>> Ks = 10**np.linspace(-10, 1.0, 1000)
    >>> ms = list(map(ellipkinv, Ks))
    >>> abs((ellipk(ms)/Ks - 1)).max() < 1e-10
    True
    >>> ellipkinv(np.pi/2.0)
    0.0
    """
    lam = K - np.pi/2.
    if lam == 0:
        return 0.0
    elif lam < 0:
        # Not in paper: from asymptotic expansion
        m = (-(lambertw(-K/4, -1)/K)**2).real
    else:
        m = 1 - np.exp(-lam*((8/np.pi + lam*2.9619147279597561)/
                             (1+lam*1.480957363979878)))
    for i in range(iter):
        # Only 4 iterations are needed
        K_m, E_m = ellipk(m), ellipe(m)
        f = K_m - K
        df = (E_m - (1-m)*K_m) / (2*m*(1-m))
        m -= f/df
    return m
