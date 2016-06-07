"""Some plotting utilities for matplotlib.
"""
from __future__ import absolute_import, division, print_function

from matplotlib import pyplot as plt

import numpy as np

import scipy.interpolate
import scipy as sp

import matplotlib.cm

from matplotlib.colors import LinearSegmentedColormap

from .viridis import test_cm as viridis

del scipy

# Monkeypatch matplotlib to add the new viridis color map
matplotlib.cm.viridis = viridis
matplotlib.cm.cmap_d.update(viridis=viridis)

# Constructed with seaborn
# import seaborn as sns
# sns.diverging_palette(0, 255, n=4, s=63, l=73, sep=1, center='dark')
diverging_colormap = LinearSegmentedColormap.from_list(
    'diverging',
    np.array([[0.62950738, 0.70001025, 0.89382127, 1.],
              # [0.13300000, 0.13300000, 0.13300000, 1.],
              [0.00000000, 0.00000000, 0.00000000, 1.],
              [0.90488582, 0.62784940, 0.68104318, 1.]]))


def _fix_args(x, y, z):
    """Fix the arguments to allow for more flexible processing."""
    x, y, z = map(np.asarray, (x, y, z))

    x = x[:, 0] if x.shape == z.shape else x.ravel()
    y = y[0, :] if y.shape == z.shape else y.ravel()
    assert z.shape[:2] == (len(x), len(y))
    return x, y, z


def imcontourf(x, y, z, interpolate=True, diverging=False,
               *v, **kw):
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
            np.allclose(np.diff(np.diff(x)), 0) and
            np.allclose(np.diff(np.diff(y)), 0)):
        spl = sp.interpolate.RectBivariateSpline(x, y, z, kx=1, ky=1, s=0)
        Nx = int(min(5*len(x), (x.max()-x.min()) / np.diff(sorted(x)).min()))
        Ny = int(min(5*len(y), (y.max()-y.min()) / np.diff(sorted(y)).min()))
        x = np.linspace(x.min(), x.max(), Nx)
        y = np.linspace(y.min(), y.max(), Ny)
        z = spl(x[:, None], y[None, :])

    assert np.allclose(np.diff(np.diff(x)), 0)
    assert np.allclose(np.diff(np.diff(y)), 0)
    kwargs = dict(**kw)
    kwargs.setdefault('aspect', 'auto')
    if diverging:
        z_max = abs(z).max()
        kwargs.setdefault('vmin', -z_max)
        kwargs.setdefault('vmax', z_max)
        kwargs.setdefault('cmap', diverging_colormap)
    else:
        kwargs.setdefault('cmap', viridis)

    img = plt.imshow(
        np.rollaxis(z, 0, 2), origin='lower',
        extent=(x[0], x[-1], y[0], y[-1]), *v, **kwargs)

    # Provide a method for updating the data properly for quick plotting.
    def set_data(z, img=img, sd=img.set_data):
        sd(np.rollaxis(z, 0, 2))

    img.set_data = set_data
    return img


def phase_contour(x, y, z, N=10, colors='k', linewidths=0.5, **kw):
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
    levels = 0.5*np.pi*(0.5 + (np.arange(N) + 0.5)/N)
    _z = np.rollaxis(z, 0, 2)
    c1 = plt.contour(x, y, abs(np.angle(_z)),
                     levels=levels, **args)
    c2 = plt.contour(x, y, abs(np.angle(_z*np.exp(0.5j*np.pi))),
                     levels=levels, **args)
    c2.levels = (c2.levels + 0.5*np.pi)
    c2.levels = np.where(c2.levels <= np.pi,
                         c2.levels,
                         c2.levels - 2.0*np.pi)
    return c1, c2


def color_angle(theta, map='huslp', gamma=1,
                saturation=100.0, lightness=75.6):
    """Return an RGB tuple of colors for each angle theta.

    The colors cycle smoothly through all hues in the order of the
    rainbow.  The default map is luminosity corrected:

    http://www.husl-colors.org

    Arguments
    ---------
    theta : array
       Array of angles as returned, for example, by `np.angle`.
    map : 'husl' or 'hue'
       Colour map to use.

       'huslp' :
          a luminosity corrected coloring.  All angles here
          have the same perceptual brightness, however only pastel
          colors are used.
       'husl' :
          a luminosity corrected coloring similar to huslp but
          allowing for full saturation. Highly saturated colors do not
          appear to change uniformly though.
       other :
         a custom but poor cycling through hue.
    """
    # Convert to same form used by color map which linear maps the
    # range -pi/2, pi/2 to 0, 360
    theta = theta + np.pi
    if map in ('husl', 'huslp'):
        import husl

        @np.vectorize
        def to_rgb(*v, **kw):
            """Turn output into a tuple so vectorize works."""
            return tuple(getattr(husl, map + '_to_rgb')(*v, **kw))

        rgb = np.asarray(to_rgb(theta/np.pi*180 % 360, saturation, lightness))

        # Put the rgb axis last so we can pass this to imshow
        return np.rollaxis(rgb, 0, rgb.ndim)

    r = ((1 + np.cos(theta)) / 2.0) ** gamma
    g = ((1 + np.cos(theta - 2*np.pi/3.0)) / 2.0) ** gamma
    b = ((1 + np.cos(theta - 4*np.pi/3.0)) / 2.0) ** gamma
    rgb = np.rollaxis(np.array([r, g, b]), 0, 3)
    return rgb

    # Need to fix broadcasting here.  Should make cmap.
    r = np.array([1.0, 0, 0])
    g = np.array([0, 1.0, 0])
    b = np.array([0, 0, 1.0])

    rgb = (r*((1 + np.cos(theta)) / 2.0) ** gamma +
           g*((1 + np.cos(theta - 2*np.pi/3.0)) / 2.0) ** gamma +
           b*((1 + np.cos(theta - 4*np.pi/3.0)) / 2.0) ** gamma)


def color_complex(psi, vmin=None, vmax=None, reversed=False,
                  **kw):
    """Return RGB tuple of colors for each complex value.

    Uses `color_angle` but varies the lightness to match the magnitude
    of `psi`.

    Arguments
    ---------
    vmin, vmax : float
       Minimum and maximum of magnitude range.  Uses min and max of
       abs(phi) if not provided.
    reversed : bool
       If True, then the minimum magnitude is white.
    """

    theta = np.angle(psi)
    mag = abs(psi)
    if vmin is None:
        vmin = mag.min()
    if vmax is None:
        vmax = mag.max()

    lightness = 100.0*np.ma.divide(mag - vmin,
                                   vmax - vmin).filled(0.75)
    if reversed:
        lightness = 100.0 - lightness
    return color_angle(theta, lightness=lightness, **kw)


def make_angle_colormap(map='huslp', gamma=1,
                        saturation=100.0, lightness=75.6):
    import husl
    from matplotlib.colors import LinearSegmentedColormap
    N = 100
    rs = []
    gs = []
    bs = []
    for theta in np.linspace(0, 360, N):
        r, g, b = getattr(husl, map + '_to_rgb')(theta, saturation, lightness)
        rs.append((theta/360.0, r, r))
        gs.append((theta/360.0, g, g))
        bs.append((theta/360.0, b, b))
    cdict = dict(red=tuple(rs),
                 green=tuple(gs),
                 blue=tuple(bs))
    return LinearSegmentedColormap('huslp', cdict)


cm_husl = make_angle_colormap(map='husl')
cm_huslp = make_angle_colormap(map='huslp')

plt.register_cmap(name='husl', cmap=cm_husl)
plt.register_cmap(name='huslp', cmap=cm_huslp)
