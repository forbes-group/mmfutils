"""FFTW wrappers for high-performance computing.

This module requires you to have installed the fftw libraries and
:mod:`pyfftw`.  Note that you must build the fftw with all precisions
using something like::

    PREFIX=/data/apps/fftw
    VER=3.3.4
    for opt in " " "--enable-sse2 --enable-single" \\
               "--enable-long-double" "--enable-quad-precision"; do
      ./configure --prefix="${PREFIX}/${VER}"\\
                  --enable-threads\\
                  --enable-shared\\
                  $opt
      make -j8 install
    done

Note: The FFTW library does not work with negative indices for axis.
Indices should first be normalized by ``inds % len(shape)``.
"""
import functools
import itertools
import warnings

import numpy.fft
import numpy as np

from .threads import SET_THREAD_HOOKS

del numpy

__all__ = ["fft", "ifft", "fftn", "ifftn", "fftfreq", "resample"]


# Numpy versions with a default axis specified
def fft_numpy(Phi, axis=-1):
    return np.fft.fft(Phi, axis=axis)


def ifft_numpy(Phit, axis=-1):
    return np.fft.ifft(Phit, axis=axis)


def fftn_numpy(Phi, axes=None):
    return np.fft.fftn(Phi, axes=axes)


def ifftn_numpy(Phit, axes=None):
    return np.fft.ifftn(Phit, axes=axes)


fftfreq = np.fft.fftfreq
fftshift = np.fft.fftshift


_THREADS = 8
_PLANNER_EFFORT = "FFTW_MEASURE"


def set_num_threads(nthreads):
    global _THREADS
    _THREADS = nthreads


SET_THREAD_HOOKS.add(set_num_threads)


try:  # NOQA  This is too complex, but that is okay
    import pyfftw
    from pyfftw.interfaces.numpy_fft import (
        fft as _fft,
        ifft as _ifft,
        fftn as _fftn,
        ifftn as _ifftn,
    )

    # Hack to get the version from pyfftw to resolve issue #25
    from pkg_resources import parse_version

    pyfftw_version = getattr(pyfftw, "version", "0")
    while hasattr(pyfftw_version, "version"):
        pyfftw_version = pyfftw_version.version

    # By default, pyfftw does not cache the plans.  Here we enable the cache
    # and set the keepalive time to an hour.
    if parse_version(pyfftw_version) >= parse_version("0.9.2"):
        pyfftw.interfaces.cache.enable()
        pyfftw.interfaces.cache.set_keepalive_time(60 * 60)

    # Also, the number of threads is set by default to 1.  Here we set the
    # default value to 8 and use FFT_MEASURE to actually check.
    @functools.wraps(_fft)
    def fft_pyfftw(*v, **kw):
        global _THREADS, _PLANNER_EFFORT
        kw.update(threads=_THREADS, planner_effort=_PLANNER_EFFORT)
        if "axis" in kw:
            # Support negative arguments for the axis keyword
            dim = len(np.shape(v[0]))
            kw["axis"] = (kw["axis"] + dim) % dim
        return _fft(*v, **kw)

    @functools.wraps(_ifft)
    def ifft_pyfftw(*v, **kw):
        global _THREADS, _PLANNER_EFFORT
        kw.update(threads=_THREADS, planner_effort=_PLANNER_EFFORT)
        if "axis" in kw:
            # Support negative arguments for the axis keyword
            dim = len(np.shape(v[0]))
            kw["axis"] = (kw["axis"] + dim) % dim
        return _ifft(*v, **kw)

    @functools.wraps(_fftn)
    def fftn_pyfftw(*v, **kw):
        global _THREADS, _PLANNER_EFFORT
        kw.update(threads=_THREADS, planner_effort=_PLANNER_EFFORT)
        if "axes" in kw:
            # Support negative arguments for the axis keyword
            dim = len(np.shape(v[0]))
            kw["axes"] = (np.asarray(kw["axes"]) + dim) % dim
        return _fftn(*v, **kw)

    @functools.wraps(_ifftn)
    def ifftn_pyfftw(*v, **kw):
        global _THREADS, _PLANNER_EFFORT
        kw.update(threads=_THREADS, planner_effort=_PLANNER_EFFORT)
        if "axes" in kw:
            # Support negative arguments for the axis keyword
            dim = len(np.shape(v[0]))
            kw["axes"] = (np.asarray(kw["axes"]) + dim) % dim
        return _ifftn(*v, **kw)

    def get_fft_pyfftw(
        a,
        n=None,
        axis=-1,
        overwrite_input=False,
        auto_align_input=True,
        auto_contiguous=True,
        avoid_copy=False,
    ):
        """Return a function to compute the fft.

        WARNING: The returned array may not own its data (check `res.flags['OWNDATA']`).
                 If it does not, subsequent calls to the function might change the data.
                 Make a copy if needed.
        """
        global _THREADS, _PLANNER_EFFORT
        # Support negative arguments for the axis keyword
        dim = len(np.shape(a))
        axis = (axis + dim) % dim
        return pyfftw.builders.fft(
            a=a,
            n=n,
            axis=axis,
            threads=_THREADS,
            planner_effort=_PLANNER_EFFORT,
            overwrite_input=overwrite_input,
            auto_align_input=auto_align_input,
            auto_contiguous=auto_contiguous,
            avoid_copy=avoid_copy,
        )

    def get_ifft_pyfftw(
        a,
        n=None,
        axis=-1,
        overwrite_input=False,
        auto_align_input=True,
        auto_contiguous=True,
        avoid_copy=False,
    ):
        """Return a function to compute the ifft.

        WARNING: The returned array may not own its data (check `res.flags['OWNDATA']`).
                 If it does not, subsequent calls to the function might change the data.
                 Make a copy if needed.
        """
        global _THREADS, _PLANNER_EFFORT
        dim = len(np.shape(a))
        axis = (axis + dim) % dim
        return pyfftw.builders.ifft(
            a=a,
            n=n,
            axis=axis,
            threads=_THREADS,
            planner_effort=_PLANNER_EFFORT,
            overwrite_input=overwrite_input,
            auto_align_input=auto_align_input,
            auto_contiguous=auto_contiguous,
            avoid_copy=avoid_copy,
        )

    def get_fftn_pyfftw(
        a,
        s=None,
        axes=None,
        overwrite_input=False,
        auto_align_input=True,
        auto_contiguous=True,
        avoid_copy=False,
    ):
        """Return a function to compute the fftn.

        WARNING: The returned array may not own its data (check `res.flags['OWNDATA']`).
                 If it does not, subsequent calls to the function might change the data.
                 Make a copy if needed.
        """
        global _THREADS, _PLANNER_EFFORT
        if axes is not None:
            dim = len(np.shape(a))
            axes = (np.asarray(axes) + dim) % dim
        return pyfftw.builders.fftn(
            a=a,
            s=s,
            axes=axes,
            threads=_THREADS,
            planner_effort=_PLANNER_EFFORT,
            overwrite_input=overwrite_input,
            auto_align_input=auto_align_input,
            auto_contiguous=auto_contiguous,
            avoid_copy=avoid_copy,
        )

    def get_ifftn_pyfftw(
        a,
        s=None,
        axes=None,
        overwrite_input=False,
        auto_align_input=True,
        auto_contiguous=True,
        avoid_copy=False,
    ):
        """Return a function to compute the ifftn.

        WARNING: The returned array may not own its data (check `res.flags['OWNDATA']`).
                 If it does not, subsequent calls to the function might change the data.
                 Make a copy if needed.
        """
        global _THREADS, _PLANNER_EFFORT
        if axes is not None:
            dim = len(np.shape(a))
            axes = (np.asarray(axes) + dim) % dim
        return pyfftw.builders.ifftn(
            a=a,
            s=s,
            axes=axes,
            threads=_THREADS,
            planner_effort=_PLANNER_EFFORT,
            overwrite_input=overwrite_input,
            auto_align_input=auto_align_input,
            auto_contiguous=auto_contiguous,
            avoid_copy=avoid_copy,
        )

    fft = fft_pyfftw
    ifft = ifft_pyfftw
    fftn = fftn_pyfftw
    ifftn = ifftn_pyfftw
except ImportError:  # pragma: nocover
    warnings.warn("Could not import pyfftw... falling back to numpy")
    fft = fft_numpy
    ifft = ifft_numpy
    fftn = fftn_numpy
    ifftn = ifftn_numpy


def resample(f, N):
    """Resample f to a new grid of size N.

    This uses the FFT to resample the function `f` on a new grid with `N`
    points.  Note: this assumes that the function `f` is periodic.  Resampling
    non-periodic functions to finer lattices may introduce aliasing artifacts.

    Arguments
    ---------
    f : array
       The function to be resampled.  May be n-dimensional
    N : int or array
       The number of lattice points in the new array.  If this is an integer,
       then all dimensions of the output array will have this length.

    Examples
    --------
    >>> def f(x, y):
    ...     "Function with only low frequencies"
    ...     return (np.sin(2*np.pi*x)-np.cos(4*np.pi*y))
    >>> L = 1.0
    >>> Nx, Ny = 16, 13   # Small grid
    >>> NX, NY = 31, 24   # Large grid
    >>> dx, dy = L/Nx, L/Ny
    >>> dX, dY = L/NX, L/NY
    >>> x = (np.arange(Nx)*dx - L/2)[:, None]
    >>> y = (np.arange(Ny)*dy - L/2)[None, :]
    >>> X = (np.arange(NX)*dX - L/2)[:, None]
    >>> Y = (np.arange(NY)*dY - L/2)[None, :]
    >>> f_XY = resample(f(x,y), (NX, NY))
    >>> np.allclose(f_XY, f(X,Y))                      # To larger grid
    True
    >>> np.allclose(resample(f_XY, (Nx, Ny)), f(x,y))  # Back down
    True
    """
    newshape = np.array(f.shape)
    newshape[...] = N
    axes = np.where(np.not_equal(f.shape, newshape))[0]
    fk = fftn(f, axes=axes)
    fk1 = np.zeros(newshape, dtype=complex)
    for _s in itertools.product(
        *(
            (slice(0, (_N + 1) // 2), slice(-(_N - 1) // 2, None))
            for _N in np.minimum(f.shape, newshape)
        )
    ):
        fk1[_s] = fk[_s]

    return ifftn(fk1, axes=axes) * np.prod(newshape.astype(float) / f.shape)
