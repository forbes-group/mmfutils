"""Various types of contour plots."""
import numpy as np

import scipy.interpolate
import scipy as sp

from matplotlib import pyplot as plt
from .rasterize import contourf
from .colors import cm

del scipy

__all__ = ["contourf", "imcontourf", "phase_contour"]


def _fix_args(x, y, z):
    """Fix the arguments to allow for more flexible processing."""
    x, y, z = list(map(np.asanyarray, (x, y, z)))

    x = x[:, 0] if x.shape == z.shape else x.ravel()
    y = y[0, :] if y.shape == z.shape else y.ravel()
    assert z.shape[:2] == (len(x), len(y))
    return x, y, z


def imcontourf(x, y, z, interpolate=True, diverging=False, *v, **kw):
    r"""Like :func:`matplotlib.pyplot.contourf` but does not actually find
    contours.  Just displays `z` using
    :func:`matplotlib.pyplot.imshow` which is much faster and uses
    exactly the information available.

    Parameters
    ----------
    x, y, z : array-like
       Assumes that `z` is ordered as `z[x, y]`.  If `x` and `y` have the same
       shape as `z`, then `x = x[:, 0]` and `y = y[0, :]` are used.  Otherwise,
       `z.shape == (len(x), len(y))`.  `x` and `y` must be equally spaced.
    interpolate : bool
       If `True`, then interpolate the function onto an evenly spaced set of
       abscissa using cublic splines.
    diverging : bool
       If `True`, then the output is normalized so that diverging
       colormaps will have 0 in the middle.  This is done by setting
       `vmin` and `vmax` symmetrically.
    """
    x, y, z = _fix_args(x, y, z)

    if interpolate and not (
        np.allclose(np.diff(np.diff(x)), 0) and np.allclose(np.diff(np.diff(y)), 0)
    ):

        Nx = int(min(5 * len(x), (x.max() - x.min()) / np.diff(sorted(x)).min()))
        Ny = int(min(5 * len(y), (y.max() - y.min()) / np.diff(sorted(y)).min()))
        X = np.linspace(x.min(), x.max(), Nx)
        Y = np.linspace(y.min(), y.max(), Ny)

        # Vectorize this over last few indices of z.  This allows z to
        # be an RGB tuple for example.
        z_ = np.reshape(z, z.shape[:2] + (int(np.prod(z.shape[2:])),))
        Z = []
        for _n in range(z_.shape[-1]):
            spl = sp.interpolate.RectBivariateSpline(x, y, z_[..., _n], kx=1, ky=1, s=0)
            Z.append(spl(X[:, None], Y[None, :]).T)
        Z = np.transpose(Z)
        x, y, z = X, Y, np.reshape(Z, (Nx, Ny) + z.shape[2:])

    assert np.allclose(np.diff(np.diff(x)), 0)
    assert np.allclose(np.diff(np.diff(y)), 0)
    kwargs = dict(**kw)
    kwargs.setdefault("aspect", "auto")
    if diverging:
        z_max = abs(z).max()
        kwargs.setdefault("vmin", -z_max)
        kwargs.setdefault("vmax", z_max)
        kwargs.setdefault("cmap", cm.diverging)
    else:
        kwargs.setdefault("cmap", cm.viridis)

    img = plt.imshow(
        np.rollaxis(z, 0, 2),
        origin="lower",
        extent=(x[0], x[-1], y[0], y[-1]),
        *v,
        **kwargs
    )

    # Provide a method for updating the data properly for quick plotting.
    def set_data(z, x=None, y=None, img=img, sd=img.set_data):
        sd(np.rollaxis(z, 0, 2))
        if x is not None or y is not None:
            extent = list(img.get_extent())
            if x is not None:
                extent[:2] = [np.ravel(x)[0], np.ravel(x)[-1]]
            if y is not None:
                extent[:2] = [np.ravel(y)[0], np.ravel(y)[-1]]
            img.set_extent(extent)

    img.set_data = set_data
    return img


def phase_contour(x, y, z, N=10, colors="k", linewidths=0.5, ax=None, **kw):
    r"""Specialized contour plot for plotting the contours of constant
    phase for the complex variable z.  Plots `4*N` contours in total.
    Note: two sets of contours are returned, and, due to processing,
    these do not have the correct values.

    The problem this solves is that plotting the contours of
    `np.angle(z)` gives a whole swath of contours at the discontinuity
    between `-pi` and `pi`.  We get around this by doing two things:

    1) We plot the contours of `abs(angle(z))`.  This almost fixes the problem,
       but can give rise to spurious closed contours near zero and `pi`.  To
       deal with this:
    2) We plot only the contours between `pi/4` and `3*pi/4`.  We do
       this twice, multiplying `z` by `exp(0.5j*pi)`.
    3) We carefully choose the contours so that they have even spacing.
    """
    x, y, z = _fix_args(x, y, z)
    args = dict(colors=colors, linewidths=linewidths)
    args.update(kw)
    levels = 0.5 * np.pi * (0.5 + (np.arange(N) + 0.5) / N)
    _z = np.rollaxis(z, 0, 2)
    if ax is None:
        ax = plt.gca()
    c1 = ax.contour(x, y, abs(np.angle(_z)), levels=levels, **args)
    c2 = ax.contour(
        x, y, abs(np.angle(_z * np.exp(0.5j * np.pi))), levels=levels, **args
    )
    c2.levels = np.add(c2.levels, 0.5 * np.pi)
    c2.levels = np.where(c2.levels <= np.pi, c2.levels, c2.levels - 2.0 * np.pi)
    return c1, c2
