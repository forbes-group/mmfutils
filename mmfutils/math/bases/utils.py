"""General utility functions"""
from __future__ import absolute_import, division

import functools
import operator

import numpy as np
from numpy.linalg import norm
import scipy as sp

from mmfutils.performance.fft import fft, ifft, fftn, ifftn, resample

__all__ = ('prod', 'norm', 'ndgrid',
           'fft', 'ifft', 'fftn', 'ifftn', 'fftn', 'ifftn', 'resample',
           'dst', 'idst', 'get_xyz')


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
        return np.meshgrid(*v, sparse=True, indexing='ij')


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
    """
    xyz = []
    _offset = 0.5 if symmetric_lattice else 0
    xyz = ndgrid(*[_l/_n * (np.arange(-_n/2, _n/2) + _offset)
                   for _n, _l in zip(Nxyz, Lxyz)])
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
    kxyz = ndgrid(*[2.0 * np.pi * np.fft.fftfreq(_n, _l/_n)
                    for _n, _l in zip(Nxyz, Lxyz)])
    return kxyz


######################################################################
# 1D FFTs for real functions.
def dst(f, axis=-1):
    """Return the Discrete Sine Transform (DST III) of `f`"""
    args = dict(type=3, axis=axis)
    if np.iscomplexobj(f):
        # This is needed for scipy < 0.16.0
        return (sp.fftpack.dst(f.real, **args) + 1j*
                sp.fftpack.dst(f.imag, **args))
    else:
        return sp.fftpack.dst(f, **args)


def idst(F, axis=-1):
    """Return the Inverse Discrete Sine Transform (DST II) of `f`"""
    N = F.shape[-1]
    args = dict(type=2, axis=axis)
    if np.iscomplexobj(F):
        # This is needed for scipy < 0.16.0
        res = (sp.fftpack.dst(F.real, **args) + 1j*
               sp.fftpack.dst(F.imag, **args))
    else:
        res = sp.fftpack.dst(F, **args)
    return res/(2.0*N)
