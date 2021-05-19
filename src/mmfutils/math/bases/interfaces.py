"""Interfaces for Basis Objects

The interface here provides a way to represent functions in a variety
of spaces, such as in periodic boxes, or in cylindrical or spherical
symmetry.
"""
import functools

import numpy as np

from mmfutils.interface import implementer, Interface, Attribute

__all__ = [
    "implementer",
    "IBasis",
    "IBasisKx",
    "IBasisLz",
    "IBasisWithConvolution",
    "BasisMixin",
]


class IBasisMinimal(Interface):
    """General interface for a basis.

    The basis provides a set of abscissa at which functions should be
    represented and methods for computing the laplacian etc.
    """

    xyz = Attribute("The abscissa")
    metric = Attribute("The metric")
    k_max = Attribute("Maximum momentum (used for determining cutoffs)")

    def laplacian(y, factor=1.0, exp=False):
        """Return the laplacian of `y` times `factor` or the exponential of this.

        Parameters
        ----------
        factor : float
           Additional factor (mostly used with `exp=True`).  The
           implementation must be careful to allow the factor to
           broadcast across the components.
        exp : bool
           If `True`, then compute the exponential of the laplacian.
           This is used for split evolvers.
        """


class IBasis(IBasisMinimal):
    def grad_dot_grad(a, b):
        """Return the grad(y1).dot(grad(y2)).

        I.e. laplacian(y) = grad_dot_grad(y, y)
        """

    is_metric_scalar = Attribute(
        """True if the metric is a scalar (number) that commutes with
        everything.  (Allows some algorithms to improve performance.
        """
    )

    shape = Attribute(
        """Array shape the basis.  This is the shape of the array that would be
        formed by evaluating a function of all coordinates xyz.
        """
    )


class IBasisWithConvolution(IBasis):
    def convolve_coulomb(y, form_factors):
        """Convolve y with the form factors without any images"""

    def convolve(y, Ck):
        """Convolve y with Ck"""


class IBasisExtended(IBasis):
    """Extended basis with quantum numbers etc.  Used with fermionic
    functionals where you need a complete set of states."""

    def get_quantum_numbers():
        """Return a set of iterators over the quantum numbers for the
        basis."""

    def get_laplacian(qns):
        """Return the matrix representation of the laplacian for the
        specified quantum numbers.

        This should be a 2-dimensional array (matrix) whose indices can
        be reshaped if needed.
        """


class IBasisKx(IBasis):
    """This ensures that the basis is periodic in the x direction, and allows
    the user to access the quasi-momenta `kx` in this direction and to
    manipulate the form of the laplacian.  The allows one to implement, for
    example, modified dispersion relations in the x direction such as might
    arise with artificial gauge fields (Spin-Orbit Coupled BEC's for
    example).
    """

    kx = Attribute("Momenta in x direction")
    Lx = Attribute("Length of box in x direction")
    Nx = Attribute("Number of abscissa in x direction")

    def laplacian(y, factor=1.0, exp=False, kx2=None, twist_phase_x=None):
        """Return the laplacian of `y` times `factor` or the exponential of this.

        Parameters
        ----------
        factor : float
           Additional factor (mostly used with `exp=True`).  The
           implementation must be careful to allow the factor to
           broadcast across the components.
        exp : bool
           If `True`, then compute the exponential of the laplacian.
           This is used for split evolvers.
        k2x : None, array
           Replacement for the default `kx2=kx**2` used when computing the
           "laplacian".
        twist_phase_x : array, optional
           To implement twisted boundary conditions, one needs to remove an
           overall phase from the wavefunction rendering it periodic for use
           the the FFT.  This the the phase that should be removed.  Note: to
           compensate, the momenta should be shifted as well::

              -factor * twist_phase_x*ifft((k+k_twist)**2*fft(y/twist_phase_x)
        """


class IBasisLz(IBasis):
    """Extension of IBasis that allows the angular momentum along the
    z-axis to be applied.  Useful for implementing rotating frames.
    """

    def apply_Lz_hbar(y):
        """Apply `Lz/hbar` to `y`."""

    def laplacian(y, factor=1.0, exp=False, kwz2=0):
        """Return the laplacian of `y` times `factor` or the exponential of this.

        Parameters
        ----------
        factor : float
           Additional factor (mostly used with `exp=True`).  The
           implementation must be careful to allow the factor to
           broadcast across the components.
        exp : bool
           If `True`, then compute the exponential of the laplacian.
           This is used for split evolvers.  Only allowed to be `True`
           if `kwz2 == 0`.
        kwz2 : None, float
           Angular velocity of the frame expressed as `kwz2 = m*omega_z/hbar`.
        """


class BasisMixin(object):
    """Provides the methods of IBasis for a class implementing
    IBasisMinimal
    """

    def grad_dot_grad(self, a, b):
        """Return the grad(a).dot(grad(b))."""
        laplacian = self.laplacian
        return (laplacian(a * b) - laplacian(a) * b - a * laplacian(b)) / 2.0

    @property
    def is_metric_scalar(self):
        """Return `True` if the metric is a scalar (number) that commutes with
        everything.  (Allows some algorithms to improve performance.
        """
        return np.prod(np.asarray(self.metric).shape) == 1

    @property
    def shape(self):
        """Return the shape of the basis."""
        return functools.reduce(np.maximum, [_x.shape for _x in self.xyz])
