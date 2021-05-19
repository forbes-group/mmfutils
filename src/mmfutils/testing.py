"""Testing utilities."""
import numpy as np

try:
    from uncertainties import unumpy
except ImportError:  # pragma: nocover
    unumpy = None


def allclose(a, b, use_covariance=False, **kw):
    """Return `True` if a and be are close.

    Like np.allclose, but first tries a strict equality test, and also
    works for quantities with uncertainties.

    Arguments
    ---------
    use_covariance : bool, float
       If True and parameters have uncertainties, then use their
       covariance information.  Two parameters are considered equal in
       this case if their difference is zero to within the factor
       use_covariance times the std_dev of the difference.  (If
       use_covariance is True, this is 1 standard deviation, but
       floats can be used.)
    """
    try:
        if a == b:
            return True
    except ValueError:
        pass

    if use_covariance:
        if unumpy is None:
            raise ValueError("use_covariance requires the uncertainties package.")
        zero = abs(a - b)
        return np.all(
            unumpy.nominal_values(zero) <= use_covariance * unumpy.std_devs(zero)
        )
    try:
        return np.allclose(a, b, **kw)
    except TypeError:
        return np.allclose(unumpy.nominal_values(a), unumpy.nominal_values(b), **kw)
