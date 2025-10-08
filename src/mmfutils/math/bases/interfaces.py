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
    "IBasisCutoff",
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

    def laplacian(y, factor=1.0, factors=None, exp=False):
        """Return the laplacian of `y` times `factor` or the exponential of this.

        Parameters
        ----------
        factor : float | None
            Additional factor (mostly used with `exp=True`).  The
            implementation must be careful to allow the factor to
            broadcast across the components.
        factors : [float] | None
            Tuple of scale factors for each dimension.  Allows for independent scaling
            of each direction (used in expanding reference frames).
        exp : bool
            If `True`, then compute the exponential of the laplacian.
            This is used for split evolvers.
        """


class IBasis(IBasisMinimal):
    def grad_dot_grad(a, b, factors=None):
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
    def convolve_coulomb(y, form_factors, factors=None):
        """Convolve y with the form factors without any images"""

    def convolve(y, Ck, factors=None):
        """Convolve y with Ck"""


class IBasisExtended(IBasis):
    """Extended basis with quantum numbers etc.  Used with fermionic
    functionals where you need a complete set of states."""

    def get_quantum_numbers():
        """Return a set of iterators over the quantum numbers for the
        basis."""

    def get_laplacian(qns, factors=None):
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

    Two versions of the momenta are provided: :attr:`kx` is used for the laplacian,
    while `kx_derivative` is used for gradients.  Most ks are paired - one positive and
    one negative, but when the basis contains an even number of abscissa, the highest
    momentum point is unpaired.  This is set to zero in `kx_derivative` to ensure that,
    e.g., the derivative of a real function is real.

    To implement twisted boundary conditions, one should pass `kx` and `kx2` as needed
    modified with `kx + twist/Lx` where `twist` is the angle of the twist.
    """

    kx = Attribute("Momenta in x direction")
    kx_derivative = Attribute("Momenta in x direction suitable for differentiation")
    Lx = Attribute("Length of box in x direction")
    Nx = Attribute("Number of abscissa in x direction")

    def laplacian(y, factor=1.0, factors=None, exp=False, kx2=None):
        """Return the laplacian of `y` times `factor` or the exponential of this.

        Parameters
        ----------
        factor : float, Li
            Additional factor(s) (mostly used with `exp=True`).  The
            implementation must be careful to allow the factor to
            broadcast across multiple components.
        factors : [float], None
            Tuple of scale factors for each dimension.  Allows for independent scaling
            of each direction (used in expanding reference frames).
        exp : bool
            If `True`, then compute the exponential of the laplacian.
            This is used for split evolvers.
        kx2 : None, array
            Replacement for the default `kx2=kx**2` used when computing the
            "laplacian".
        """

    def get_gradient(y, kx=None, factors=None):
        """Return the gradient of `y`.

        Parameters
        ----------
        kx : None, array
            Replacement for the default `kx` including twists etc.
        """


class IBasisCutoff(IBasis):
    """Extended basis classes that provide a momentum cutoff.

    These classes are used by the PGPE to project to lower frequency.
    """

    k_max = Attribute("Maximum momenta representable in the basis.")
    smoothing_cutoff = Attribute("Fraction of k_max to smooth.")

    def smooth(f):
        """Return `f` projected onto momenta < kc, maintaining reality."""


class IBasisLz(IBasis):
    """Extension of IBasis that allows the angular momentum along the
    z-axis to be applied.  Useful for implementing rotating frames.
    """

    def apply_Lz_hbar(y):
        """Apply `Lz/hbar` to `y`."""

    def laplacian(y, factor=1.0, factors=None, exp=False, kwz2=0):
        """Return the laplacian of `y` times `factor` or the exponential of this.

        Parameters
        ----------
        factor : float
            Additional factor (mostly used with `exp=True`).  The
            implementation must be careful to allow the factor to
            broadcast across the components.
        factors : [float], None
            Tuple of scale factors for each dimension.  Allows for independent scaling
            of each direction (used in expanding reference frames).
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

    def grad_dot_grad(self, a, b, factors=None):
        """Return the grad(a).dot(grad(b))."""
        laplacian = functools.partial(self.laplacian, factors=factors)
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
