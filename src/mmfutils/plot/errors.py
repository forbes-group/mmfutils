"""Tools for plotting error bands etc."""
import numpy as np

import scipy.stats
import scipy as sp

import matplotlib.collections
from matplotlib import pyplot as plt

from .rasterize import ListCollection

del scipy

__all__ = ["plot_errorbars", "plot_err", "error_line"]


def plot_errorbars(
    x,
    y,
    dx=None,
    dy=None,
    colour="",
    linestyle="",
    pointstyle=".",
    barwidth=0.5,
    **kwargs
):

    if pointstyle != "" or linestyle != "":
        plt.plot(x, y, pointstyle + linestyle + colour, **kwargs)
    elif dx is None and dy is None:
        # Plot points if both error bars are not drawn.
        plt.plot(x, y, "." + colour, **kwargs)

    if dx is not None:
        xmax = x + dx
        xmin = x - dx
    if dy is not None:
        ymax = y + dy
        ymin = y - dy

    for n in range(len(x)):
        if dx is not None:
            plt.plot([xmin[n], xmax[n]], [y[n], y[n]], "-|" + colour, lw=barwidth)
        if dy is not None:
            plt.plot([x[n], x[n]], [ymin[n], ymax[n]], "-_" + colour, lw=barwidth)


def plot_err(x, y, yerr=None, xerr=None, **kwarg):
    """Plot x vs. y with errorbars.

    Right now we support the following cases:
    x = 1D, y = 1D
    """
    if 1 == len(x.shape) and 1 == len(y.shape):
        plt.errorbar(x, y, yerr=yerr, xerr=xerr, **kwarg)
    elif 1 == len(x.shape) and 1 < len(y.shape):
        plot_axis = np.where(np.array(y.shape) == len(x))[0][0]
        y = y.swapaxes(0, plot_axis)
        Nx, Ny = y.shape
        for n in Ny:
            plt.errorbar(x, y[:, n], **kwarg)
    elif max(x.shape) == np.prod(x.shape):
        plot_axis = np.argmax(x.shape)
        x = x.ravel()
        y = y.swapaxes(0, plot_axis)
        if yerr is not None:
            yerr = yerr.swapaxes(0, plot_axis)
        Nx, Ny = y.shape
        for n in range(Ny):
            if yerr is None:
                plt.errorbar(x, y[:, n], xerr=xerr, **kwarg)
            else:
                plt.errorbar(x, y[:, n], xerr=xerr, yerr=yerr[:, n], **kwarg)
    else:
        plt.plot(x, y, **kwarg)


def error_line(x, y, dy, fgc="k", bgc="w", N=20, fill=True):
    """Plots a curve (x, y) with gaussian errors dy represented by
    shading out to 5 dy."""
    yp0 = y
    ym0 = y
    pdf = sp.stats.norm().pdf
    to_rgb = plt.matplotlib.colors.ColorConverter().to_rgb

    bg_colour = np.array(to_rgb(bgc))
    fg_colour = np.array(to_rgb(fgc))
    if fill:
        patches = []
    else:
        lines = []

    ax = plt.gca()
    for sigma in np.linspace(0, 5, N)[1:]:
        yp = y + dy * sigma
        ym = y - dy * sigma
        c = pdf(sigma) / pdf(0.0)
        # colour = fg_colour*c + (1.0-c)*bg_colour
        colour = fg_colour

        if fill:
            X = np.hstack((x, np.flipud(x)))
            Y = np.hstack((yp0, np.flipud(yp)))
            patches.extend(ax.fill(X, Y, fc=colour, ec=colour, lw=0, alpha=c))
            X = np.hstack((x, np.flipud(x)))
            Y = np.hstack((ym0, np.flipud(ym)))
            patches.extend(ax.fill(X, Y, fc=fg_colour, ec=fg_colour, lw=0, alpha=c))
        else:
            lines.extend(
                ax.plot(x, yp, color=colour, alpha=c)
                + ax.plot(x, ym, color=fg_colour * c + (1.0 - c) * bg_colour)
            )

        ym0 = ym
        yp0 = yp

    if fill:
        artists = [matplotlib.collections.PatchCollection(patches)]
    else:
        if False:
            # Can't add alphas to LineCollection unfortunately.
            args = dict(
                zip(
                    ["segments", "linewidths", "colors", "antialiaseds", "linestyles"],
                    zip(
                        *[
                            (
                                _l.get_xydata(),
                                _l.get_linewidth(),
                                _l.get_color(),
                                _l.get_antialiased(),
                                _l.get_linestyle(),
                            )
                            for _l in lines
                        ]
                    ),
                )
            )
            artists = [matplotlib.collections.LineCollection(**args)]
        else:
            artists = [ListCollection(lines)]

        # Remove individual lines from the axis...
        for _l in lines:
            _l.remove()

        # ... and add back as a collection.
        ax.add_collection(artists[0])

    return artists
