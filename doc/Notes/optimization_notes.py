from __future__ import division, print_function
import numpy as np


np.random.seed(1)
N = 3


def crand(shape):
    """Return a random complex matrix."""
    return 2*(np.random.random(shape) + 1j*np.random.random(shape)
              - 0.5 - 0.5j)


def braket(a, b):
    return a.conj().T.dot(b)


class QuadraticProblem(object):
    def __init__(self, N=3, x0=None, H=None):
        if x0 is None:
            x0 = crand(N)  # Solution

        if H is None:
            lam = np.random.random(N) + 0.1  # positive eigenvalues of Hessian
            U = np.linalg.qr(crand((N, N)))[0]
            H = U.T.conj().dot(lam[None, :]*U)

        self.x0 = x0
        self.H = H

    def f(self, x):
        x = x - self.x0
        return 1 + braket(x, self.H.dot(x)).real/2.0

    def df(self, x):
        x = x - self.x0
        return (self.H + self.H.conj().T).dot(x)/2.0

    def ddf(self, x):
        return self.H
