"""Interfaces for Basis Objects

The interface here provides a way to represent functions in a variety
of spaces, such as in periodic boxes, or in cylindrical or spherical
symmetry.
"""
from __future__ import absolute_import, division, print_function

import numpy as np

from mmfutils.interface import (implements, Interface, Attribute)

__all__ = ['implements', 'IBasis', 'BasisMixin']


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

        Arguments
        ---------
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
        """)


class IBasisWithConvolution(IBasis):
    def convolve_coulomb(y, form_factors):
        """Convolve y with the form factors without any images
        """

    def convolve(y, Ck):
        """Convolve y with Ck"""


class BasisMixin(object):
    """Provides the methods of IBasis for a class implementing
    IBasisMinimal
    """
    def grad_dot_grad(self, a, b):
        """Return the grad(a).dot(grad(b)).

        I.e. laplacian(y) = grad_dot_grad(y, y)
        """
        laplacian = self.laplacian
        return (laplacian(a*b) - laplacian(a)*b - a*laplacian(b))/2.0

    @property
    def is_metric_scalar(self):
        """Return `True` if the metric is a scalar (number) that commutes with
        everything.  (Allows some algorithms to improve performance.
        """
        return np.prod(np.asarray(self.metric).shape) == 1
