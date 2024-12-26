"""Tools for rasterizing plots.

Some plots - especially contour plots - can become extremely large when stored
as vector graphics files (i.e. PDF).  These tools allow parts of these figures
to be rasterized so that file sizes can be kept manageable.
"""

import matplotlib.collections
from matplotlib import pyplot as plt

__all__ = ["ListCollection", "contourf"]


class ListCollection(matplotlib.collections.Collection):
    r"""Provide a simple :class:`matplotlib.collections.Collection` of a list of
    artists.  Provided so that this collection of artists can be simultaneously
    rasterized.  Used by my custom :func:`contourf` function."""

    def __init__(self, collections, **kwargs):
        matplotlib.collections.Collection.__init__(self, **kwargs)
        self.set_collections(collections)

    def set_collections(self, collections):
        self._collections = collections

    def get_collections(self):
        return self._collections

    @matplotlib.artist.allow_rasterization
    def draw(self, renderer):
        for _c in self._collections:
            _c.draw(renderer)


def contourf(*v, **kw):
    r"""Replacement for :func:`matplotlib.pyplot.contourf` that supports the
    `rasterized` keyword.

    Can be removed once this issue is resolved:
    https://github.com/matplotlib/matplotlib/issues/27669
    """
    was_interactive = matplotlib.is_interactive()
    matplotlib.interactive(False)
    rasterized = kw.pop("rasterized", None)
    contour_set = plt.contourf(*v, **kw)
    contour_set.set_rasterized(rasterized)
    matplotlib.interactive(was_interactive)
    return contour_set
