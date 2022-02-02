"""BLAS and LAPACK access.

These functions provide access to BLAS routines from scipy which can improve
performance.  This modules is woefully incomplete - it only contains functions
that I routinely used.  It should give you an idea about how to add your own.
"""
import numpy.linalg
import numpy as np
from scipy.linalg import get_blas_funcs

del numpy

__all__ = ["daxpy", "zaxpy"]

_BLAS = True


def _norm_no_blas(x):
    r"""Return `norm(x)` using numpy."""
    return np.linalg.norm(x.ravel(order="K"))


def _zdotc_no_blas(a, b):
    r"""Non-BLAS version of zdotc for use when BLAS breaks."""
    return np.dot(a.conj().ravel(), b.ravel())


def _zaxpy_no_blas(y, x, a=1.0):
    r"""Non-BLAS version of zaxpy for use when BLAS breaks."""
    y += a * x
    return y


def _ddot_no_blas(a, b):
    r"""Non-BLAS version for use when BLAS breaks."""
    return np.dot(a.ravel(), b.ravel())


def _znorm(x, _znrm2=get_blas_funcs(["nrm2"], [np.zeros(2, dtype=complex)])[0]):
    r"""Return `norm(x)` using BLAS for complex arrays.

    Warning: This can be substantially slower than `np.linalg.norm` on account
    of it doing scaling to ensure accuracy.
    """
    assert x.flags.c_contiguous
    assert _znrm2 is get_blas_funcs(["nrm2"], [x.ravel()])[0]
    return _znrm2(x.ravel(order="K"))


def _dnorm(x, _dnrm2=get_blas_funcs(["nrm2"], [np.zeros(2, dtype=float)])[0]):
    r"""Return `norm(x)` using BLAS for real arrays.

    Warning: This can be substantially slower than `np.linalg.norm` on account
    of it doing scaling to ensure accuracy.
    """
    assert x.flags.c_contiguous
    assert _dnrm2 is get_blas_funcs(["nrm2"], [x.ravel()])[0]
    return _dnrm2(x.ravel(order="K"))


def _zdotc(
    a,
    b,
    _zdotc=get_blas_funcs(
        ["dotc"],
        [
            np.zeros(2, dtype=complex),
        ]
        * 2,
    )[0],
):
    a = a.ravel()
    b = b.ravel()
    assert a.flags.f_contiguous
    assert a.flags.c_contiguous
    assert _zdotc is get_blas_funcs(["dotc"], [a, b])[0]
    return _zdotc(a, b)


def _ddot(
    a,
    b,
    _ddot=get_blas_funcs(
        ["dot"],
        [
            np.zeros(2, dtype=float),
        ]
        * 2,
    )[0],
):
    a = a.ravel()
    b = b.ravel()
    assert a.flags.f_contiguous
    assert a.flags.c_contiguous
    assert _ddot is get_blas_funcs(["dot"], [a, b])[0]
    return _ddot(a, b)


def _zaxpy(
    y,
    x,
    a=1.0,
    _axpy=get_blas_funcs(
        ["axpy"],
        [
            np.zeros(2, dtype=complex),
        ]
        * 2,
    )[0],
):
    r"""Performs ``y += a*x`` inplace using the BLAS axpy command.  This is
    significantly faster than using generic expressions that make temporary
    copies etc.

    .. note:: There is a bug in some versions of numpy that lead to segfaults
       when arrays are deallocated.  This is fixed in current versions of
       numpy, but you might need to upgrade manually.  See:

       * http://projects.scipy.org/numpy/ticket/2148
    """
    shape = y.shape
    x = x.ravel()
    y = y.ravel()
    assert y.flags.c_contiguous
    assert _axpy is get_blas_funcs(["axpy"], [x, y])[0]
    return _axpy(x=x, y=y, n=x.size, a=a).reshape(shape)


def _daxpy(
    y,
    x,
    a=1.0,
    _axpy=get_blas_funcs(
        ["axpy"],
        [
            np.zeros(2, dtype=float),
        ]
        * 2,
    )[0],
):
    r"""Performs ``y += a*x`` inplace using the BLAS axpy command.  This is
    significantly faster than using generic expressions that make temporary
    copies etc.

    .. note:: There is a bug in some versions of numpy that lead to segfaults
       when arrays are deallocated.  This is fixed in current versions of
       numpy, but you might need to upgrade manually.  See:

       * http://projects.scipy.org/numpy/ticket/2148
    """
    shape = y.shape
    x = x.ravel()
    y = y.ravel()
    assert y.flags.c_contiguous
    assert _axpy is get_blas_funcs(["axpy"], [x, y])[0]
    return _axpy(x=x, y=y, n=x.size, a=a).reshape(shape)


if _BLAS:
    znorm = _znorm
    dnorm = _dnorm
    zdotc = _zdotc
    ddot = _ddot
    zaxpy = _zaxpy
    daxpy = _daxpy
else:  # pragma: nocover
    znorm = dnorm = _norm_no_blas
    ddot = _ddot_no_blas
    zdotc = _zdotc_no_blas
    zaxpy = _zaxpy_no_blas
    daxpy = _zaxpy_no_blas
