"""Various tools for displaying information with color."""
import numpy as np

import matplotlib.cm
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize

from .cmaps import cmaps

__all__ = ["MidpointNormalize", "cm", "color_angle", "color_complex"]


class MidpointNormalize(Normalize):
    """Colormap normalization that ensures a balanced distribution about the
    specified midpoint.

    Use this with a diverging colormap to ensure that the midpoint lies in the
    middle of the colormap.

    Examples
    --------
    >>> norm = MidpointNormalize(midpoint=1.0)
    >>> norm(np.arange(4))
    masked_array(data=[0.25, 0.5 , 0.75, 1. ],
                 mask=False,
           fill_value=1e+20)

    >>> norm = MidpointNormalize(midpoint=1.0, vmin=-3)
    >>> norm(np.arange(4))
    masked_array(data=[0.375, 0.5 , 0.625, 0.75 ],
                 mask=False,
           fill_value=1e+20)
    """

    def __init__(self, vmin=None, vmax=None, clip=False, midpoint=0):
        self.midpoint = midpoint
        Normalize.__init__(self, vmin=vmin, vmax=vmax, clip=clip)

    def autoscale_None(self, A):
        """Sets vmin and vmax if they are None."""
        if np.size(A) > 0:
            # Work with midpoint removed
            vmax = np.ma.max(A) - self.midpoint
            vmin = np.ma.min(A) - self.midpoint
            if self.vmin is None:
                if self.vmax is not None:
                    vmin = -(self.vmax - self.midpoint)
                else:
                    vmin = min(vmin, -vmax)
                self.vmin = vmin + self.midpoint

            if self.vmax is None:
                if self.vmin is not None:
                    vmax = -(self.vmin - self.midpoint)
                else:
                    vmax = max(vmax, -vmin)
                self.vmax = vmax + self.midpoint

            # These assertions are written this way to allow them to work with
            # fully masked arrays.  See issue 16.
            assert not self.vmin > self.vmax
            assert np.ma.allclose(self.midpoint - self.vmin, self.vmax - self.midpoint)


def color_angle(theta, map="huslp", gamma=1, saturation=100.0, lightness=75.6):
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
    if map in ("husl", "huslp"):
        import husl

        @np.vectorize
        def to_rgb(*v, **kw):
            """Turn output into a tuple so vectorize works."""
            return tuple(getattr(husl, map + "_to_rgb")(*v, **kw))

        rgb = np.asarray(to_rgb(theta / np.pi * 180 % 360, saturation, lightness))

        # Put the rgb axis last so we can pass this to imshow
        rgb = np.rollaxis(rgb, 0, rgb.ndim)
    else:
        r = ((1 + np.cos(theta)) / 2.0) ** gamma
        g = ((1 + np.cos(theta - 2 * np.pi / 3.0)) / 2.0) ** gamma
        b = ((1 + np.cos(theta - 4 * np.pi / 3.0)) / 2.0) ** gamma
        rgb = np.rollaxis(np.array([r, g, b]), 0, 3)

    # Scale to range 0-1 (in case of round-off errors)
    rgb = np.minimum(np.maximum(0.0, rgb), 1.0)
    return rgb

    # Need to fix broadcasting here.  Should make cmap.
    r = np.array([1.0, 0, 0])
    g = np.array([0, 1.0, 0])
    b = np.array([0, 0, 1.0])

    rgb = (
        r * ((1 + np.cos(theta)) / 2.0) ** gamma
        + g * ((1 + np.cos(theta - 2 * np.pi / 3.0)) / 2.0) ** gamma
        + b * ((1 + np.cos(theta - 4 * np.pi / 3.0)) / 2.0) ** gamma
    )


def color_complex(psi, vmin=None, vmax=None, reversed=False, **kw):
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

    lightness = 100.0 * np.ma.divide(mag - vmin, vmax - vmin).filled(0.75)
    if reversed:
        lightness = 100.0 - lightness
    return color_angle(theta, lightness=lightness, **kw)


def make_angle_colormap(map="huslp", gamma=1, saturation=100.0, lightness=75.6):
    import husl
    from matplotlib.colors import LinearSegmentedColormap

    N = 100
    rs = []
    gs = []
    bs = []
    for theta in np.linspace(0, 360, N):
        r, g, b = getattr(husl, map + "_to_rgb")(theta, saturation, lightness)
        rs.append((theta / 360.0, r, r))
        gs.append((theta / 360.0, g, g))
        bs.append((theta / 360.0, b, b))
    cdict = dict(red=tuple(rs), green=tuple(gs), blue=tuple(bs))
    return LinearSegmentedColormap("huslp", cdict)


class Colormaps(object):
    """New colormaps objects"""

    husl = make_angle_colormap(map="husl")
    huslp = make_angle_colormap(map="huslp")

    # Constructed with seaborn
    # import seaborn as sns
    # sns.diverging_palette(0, 255, n=4, s=63, l=73, sep=1, center='dark')
    diverging = LinearSegmentedColormap.from_list(
        "diverging",
        np.array(
            [
                [0.62950738, 0.70001025, 0.89382127, 1.0],
                # [0.13300000, 0.13300000, 0.13300000, 1.],
                [0.00000000, 0.00000000, 0.00000000, 1.0],
                [0.90488582, 0.62784940, 0.68104318, 1.0],
            ]
        ),
    )

    def __init__(self, **kw):
        self.__dict__.update(kw)
        self._add_to_matplotlib()

    def __iter__(self):
        for _cm in dir(self):
            if not _cm.startswith("_"):
                yield _cm

    def _add_to_matplotlib(self):
        # Monkeypatch matplotlib to add the new color maps
        for cm in self:
            if not hasattr(matplotlib.cm, cm):
                cmap = getattr(self, cm)
                setattr(matplotlib.cm, cm, cmap)
                matplotlib.cm.register_cmap(name=cm, cmap=cmap)


cm = Colormaps(**cmaps)
