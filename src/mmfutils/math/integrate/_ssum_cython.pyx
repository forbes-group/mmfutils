import numpy as np
import cython


def ssum(cython.numeric[::1] xs):
    """Return (sum(xs), err) computed stably using Kahan's summation
    method for floating point numbers.  (Cython version.)

    >>> N = 10000
    >>> l = [(10.0*n)**3.0 for n in reversed(range(N+1))]
    >>> ans = 250.0*((N + 1.0)*N)**2
    >>> (ssum_cython(l)[0] - ans, sum(l) - ans)
    (0.0, -5632.0)

    Should run less than 8 times slower than a regular sum.
    >>> import time
    >>> n = 1./np.arange(1, 2**10)
    >>> t = time.time();tmp = n.sum();t0 = time.time() - t;
    >>> t = time.time();tmp = ssum_cython(n);t1 = time.time() - t;
    >>> t1 < 8.0*t0
    True
    """
    cdef:
        cython.numeric x, y, sum=0, carry=0, tmp
        size_t k, Nx 
    Nx = xs.shape[0]
    for k in range(Nx):
        x = xs[k]
        y = x - carry
        tmp = sum + y
        carry = (tmp - sum) - y
        sum = tmp
       
    return sum
