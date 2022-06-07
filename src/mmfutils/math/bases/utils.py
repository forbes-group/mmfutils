"""General utility functions"""
from distutils.version import StrictVersion
import functools
import operator

import numpy as np
from numpy.linalg import norm
import scipy as sp

from mmfutils.performance.fft import fft, ifft, fftn, ifftn, resample

__all__ = ("prod", "norm", "ndgrid", "dst", "idst", "get_xyz")


def prod(x):
    """Equivalent of sum but with multiplication."""
    # http://stackoverflow.com/a/595396/1088938
    return functools.reduce(operator.mul, x, 1)


def ndgrid(*v):
    """Sparse meshgrid with regular ordering.

    Examples
    --------
    >>> ndgrid([1,2])
    ([1, 2],)
    >>> ndgrid([1,2],[1,2,3])
    [array([[1],
           [2]]), array([[1, 2, 3]])]
    """
    if len(v) == 1:
        return v
    else:
        return np.meshgrid(*v, sparse=True, indexing="ij")


def get_xyz(Nxyz, Lxyz, symmetric_lattice=False):
    """Return `(x,y,z,...)` with broadcasting for a periodic lattice.

    Arguments
    ---------
    Nxyz : [int]
        Number of points in each dimension.
    Lxyz : [float]
        Size of periodic box in each dimension.
    symmetric_lattice : bool
        If `True`, then shift the grid so that the origin is in the middle
        but not on the lattice, otherwise the origin is part of the lattice,
        but the lattice will not be symmetric (if `Nxyz` is even as is
        typically the case for performance).

    Examples
    --------
    >>> get_xyz(Nxyz=(4, 5), Lxyz=(4, 5))
    [array([[-2.],
            [-1.],
            [ 0.],
            [ 1.]]), array([[-2.5, -1.5, -0.5,  0.5,  1.5]])]
    >>> get_xyz(Nxyz=(4, 5), Lxyz=(4, 5), symmetric_lattice=True)
    [array([[-1.5],
            [-0.5],
            [ 0.5],
            [ 1.5]]), array([[-2., -1., 0.,  1.,  2.]])]
    """
    # Special case for N = 1 should also always be centered
    _offsets = [0.5 if symmetric_lattice or _N == 1 else 0 for _N in Nxyz]
    xyz = ndgrid(
        *[
            _l / _n * (np.arange(-_n / 2, _n / 2) + _offset)
            for _n, _l, _offset in zip(Nxyz, Lxyz, _offsets)
        ]
    )
    return xyz


def get_kxyz(Nxyz, Lxyz):
    """Return list of ks in correct order for FFT.

    Arguments
    ---------
    Nxyz : [int]
       Number of points in each dimension.
    Lxyz : [float]
       Size of periodic box in each dimension.
    """
    # Note: Do not kill the single highest momenta... this leads to bad
    # scaling of high-frequency errors.
    kxyz = ndgrid(
        *[2.0 * np.pi * np.fft.fftfreq(_n, _l / _n) for _n, _l in zip(Nxyz, Lxyz)]
    )
    return kxyz


######################################################################
# 1D FFTs for real functions.
def dst(f, axis=-1):
    """Return the Discrete Sine Transform (DST III) of `f`"""
    args = dict(type=3, axis=axis)
    return sp.fftpack.dst(f, **args)


def idst(F, axis=-1):
    """Return the Inverse Discrete Sine Transform (DST II) of `f`"""
    N = F.shape[-1]
    args = dict(type=2, axis=axis)
    return sp.fftpack.dst(F, **args) / (2.0 * N)


if StrictVersion(sp.__version__) < StrictVersion("0.16.0"):
    # Scipy pre 0.16.0 cannot handle complex inputs.
    dst_real, idst_real = dst, idst

    def dst(f, axis=-1):
        """Return the Discrete Sine Transform (DST III) of `f`"""
        res = dst_real(f.real)
        if np.iscomplexobj(f):
            res = res + 1j * dst_real(f.imag)
        return res

    def idst(F, axis=-1):
        """Return the Inverse Discrete Sine Transform (DST II) of `f`"""
        res = idst_real(F.real)
        if np.iscomplexobj(F):
            res = res + 1j * idst_real(F.imag)
        return res
