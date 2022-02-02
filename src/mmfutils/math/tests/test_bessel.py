from mmfutils.math import bessel

import numpy as np


class TestBessel(object):
    """ """

    nus = [0.5, 1.0, 1.5]

    def test_j_root(self):
        for nu in self.nus:
            for Nroots in [5, 2000]:
                # Ensure coverage
                j_ = bessel.j_root(nu, Nroots)
                J = bessel.J(nu)(j_)
                assert np.allclose(0, J / j_)

    def test_J_sqrt_pole(self):
        for nu in self.nus:
            Nroots = 5
            z = np.linspace(0.01, 1.1, 10)
            h = 1e-6
            for zn in bessel.j_root(nu, Nroots):
                f = bessel.J_sqrt_pole(nu, zn, d=0)
                df = bessel.J_sqrt_pole(nu, zn, d=1)
                assert np.allclose(np.divide(f(z + h) - f(z - h), 2 * h), df(z))


class TestBesselDoctests(object):
    """Doctests for exceptions and coverage.

    >>> bessel.sinc(1.0, d=2)
    Traceback (most recent call last):
       ...
    NotImplementedError: Only d=0 or 1 supported (got d=2).

    >>> bessel.j_root(-1, 10)
    Traceback (most recent call last):
       ...
    ValueError: nu must be non-negative

    >>> bessel.J_sqrt_pole(-1, 1.0, d=2)
    Traceback (most recent call last):
       ...
    NotImplementedError: Only d=0 or 1 supported (got d=2).
    """
