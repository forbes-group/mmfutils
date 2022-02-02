"""Tools for preparing publication quality figures.

This includes the following features:

* Common customization of figure style for all figures in a paper.
* Proper scaling of figure and font for direct inclusion in paper without
  additional scaling.
* Proper generation of LaTeX labels etc. in fonts matching manudcript.
* Automation of figure generation and saving for use in manuscript.

"""
import inspect
import logging
import os.path

import numpy as np
import scipy.stats
import scipy.interpolate
import matplotlib.collections
import matplotlib.artist
import matplotlib.colors
import matplotlib.pyplot as plt

from mmfutils.containers import Object

# import mmf.utils.mac

del scipy

__all__ = ["Paper", "Figure"]

_FINFO = np.finfo(float)
_EPS = _FINFO.eps


class Paper(object):
    """Subclass this to generate a set of figures for a paper.

    Each figure should have a corresponding `fig_*` method that returns an
    appropriate :py:class:`Figure` object.  This method will generate a file
    `<figdir>/*.pdf` with the same name as the method.

    Parameters
    ----------
    style : ['aps', 'arXiv']
       Font style etc.  By default, figures will also be saved to
       `<fig_dir>/<style>` so that different copies associated with each style
       can be used.
    final : bool
       If `True`, then make plots better typographically, but less useful
       interactively (slow).
    save : bool
       If `True`, then save the figures.  This can take some time, so while
       fiddling you might like this to be `False`
    figdir : str
       Figures will be saved here organized by `style`.  The default location
       is `./_build/figures/<style>`

    Example
    -------
    >>> import os.path, tempfile, shutil
    >>> import matplotlib; matplotlib.use('pdf')
    >>> class MyPaper(Paper):
    ...     figdir = tempfile.mkdtemp()
    ...
    ...     def fig_sine(self):
    ...         fig = self.figure(
    ...             width='columnwidth',  # For two-column documents, vs. 'textwidth'
    ...         )
    ...         x = np.linspace(-1, 1, 100)
    ...         y = np.sin(4*np.pi*x)
    ...         plt.plot(x, y, '-')
    ...         plt.xlabel("$x$")
    ...         plt.ylabel("$y$")
    ...         return fig
    >>> paper = MyPaper()
    >>> paper.draw_all()
    Drawing figure: fig_sine()
    Saving plot as '.../sine.pdf'...
    Saving plot as '.../sine.pdf'. Done.
    >>> os.path.exists(os.path.join(paper.figdir, 'sine.pdf'))
    True
    >>> shutil.rmtree(paper.figdir)
    """

    figdir = "./_build/figures/{style:s}"
    style = "arXiv"
    final = True
    save = True

    def _fig_template(self):
        r"""Sample figure.  Use this template as a model."""
        fig = self.figure(
            num=1,  # If you want to redraw in the same window
            width="columnwidth",  # For two-column documents, vs. 'textwidth'
        )
        x = np.linspace(-1, 1, 100)
        y = np.sin(4 * np.pi * x)
        plt.plot(x, y, "-")
        plt.xlabel("$x$")
        plt.ylabel("$y$")
        return fig

    def __init__(self, **kw):
        """Initialize plotting to use correct fonts and figure size.

        Additional kw arguments are passed to :py:class:`LaTeXPlotProperties`.
        """
        for _attr in ["final", "save", "style", "figdir"]:
            setattr(self, _attr, kw.pop(_attr, getattr(self, _attr)))
        self.plot_properties = LaTeXPlotProperties(style=self.style, **kw)

    def savefig(self, fig, _meth_name=None, dpi=None, **kw):
        """Save the specified figure to disk."""
        dir = self.figdir % self.__dict__
        if self.save:
            if not os.path.exists(dir):
                os.makedirs(dir)

            filename = fig.filename
            if filename is None:
                if _meth_name.startswith("fig_"):
                    _meth_name = _meth_name[4:]
                filename = _meth_name + (("_%idpi" % (dpi,)) if dpi else "") + ".pdf"
            filename = os.path.join(dir, filename)
            fig.savefig(filename, dpi=dpi, **kw)

    def draw(self, meth, dpi=None, *v, **kw):
        """Draw and save the specified figure.

        The figure is drawn by calling the method, then the layout is adjusted
        if needed (see `Figure.tight_layout`).
        """
        if isinstance(meth, str):
            name = meth
            meth = getattr(self, name)
        elif inspect.ismethod(meth):
            name = meth.__name__
        print("Drawing figure: %s()" % (name,))
        fig = meth(*v, **kw)
        if fig.tight_layout:
            plt.tight_layout(pad=0.0)
        self.savefig(fig=fig, _meth_name=name, dpi=dpi)

    def draw_all(self):
        r"""Draw (and save) all figures."""
        # Close all plots so that the figures can be opened at the appropriate
        # size.
        plt.close("all")
        for meth in [
            _meth
            for _name, _meth in inspect.getmembers(self)
            if _name.startswith("fig_") and inspect.ismethod(_meth)
        ]:
            self.draw(meth)

    def figure(self, num=None, **kw):
        r"""Call this to get a new :py:class:`Figure` object."""
        fig = Figure(num=num, plot_properties=self.plot_properties, **kw)
        return fig


class Defaults(object):
    r"""Default values.

    Change the values here to affect all plots.  (Defaults are set when
    :py:class:`Figure` instances are created.)
    """

    rc = {
        "axes": dict(linewidth=0.5, edgecolor="grey", grid=True, axisbelow=True),
        "grid": dict(ls="-", lw=1.0, c="WhiteSmoke"),
        "ytick": dict(direction="out"),
        "xtick": dict(direction="out"),
        "xtick.major": dict(size=2),
        "xtick.minor": dict(size=1),
        "ytick.major": dict(size=2),
        "ytick.minor": dict(size=1),
        # 'xtick': dict(color='k'),
        # 'ytick': dict(color='k'),
    }

    @classmethod
    def set_rc(cls, **kw):
        rc = dict(cls.rc)
        rc.update(kw)
        for _name in rc:
            plt.rc(_name, **rc[_name])


class LaTeXPlotProperties(Object):
    r"""Instances of this class provide a description of properties of
    a plot based on numbers extracted from a LaTeX file.  Insert the
    following code into the section where the plot is to appear in
    order to extract the appropriate parameters and then use the
    reported values to initialize this class::

       \showthe\textwidth
       \showthe\textheight
       \showthe\columnwidth
       \showthe\baselinskip

    .. note:: We assume that the document is typeset using the
       Computer Modern fonts.
    """
    textwidth_pt = 332.89723  # From LaTeX \showthe\textwidth
    textheight_pt = 332.89723  # From LaTeX \showthe\textheight
    columnwidth_pt = 332.89723  # From LaTeX \showthe\columnwidth
    baselineskip_pt = 12.0  # From LaTeX \showthe\baselineskip
    tick_fontsize = "footnotesize"  # Ticks etc. will be typeset in this font

    usetex = True
    # If `True`, then LaTeX will be used to typeset labels
    # etc.  Otherwise, labels etc. will be left as plain text
    # that can be replaced with the ``\psfrag{}{}`` command in
    # the LaTeX file.
    #
    # As of matplotlib version 1.0.1, psfrag replacements do not
    # work, so the default is now to use LaTeX.

    style = None  # Pick a style.  One of 'aps', or 'arXiv'
    grid = True  # Draw gridlines.  Turn this off for PRC

    # The following are "constants" that you should typically not
    # have to adjust unless you use a different font package.
    font_info = {
        "times": ("ptm", r"\usepackage{mathptm}"),
        "euler": (
            "zeur",
            r"\usepackage[sc, osf]{mathpazo}"
            + r"\usepackage[euler-digits, small]{eulervm}",
        ),
    }
    font = {
        "family": "serif",
        "serif": ["computer modern roman"],
        "sans-serif": ["computer modern sans serif"],
        "monospace": ["computer modern typewriter"],
    }
    font = {
        "family": "serif",
        "serif": ["euler"],
        "sans-serif": ["bera sans serif"],
        "monospace": ["computer modern typewriter"],
    }

    latex_preamble = r"\usepackage{mmfmath}\usepackage{amsmath}"
    latex_preamble = r"\usepackage{amsmath}"
    # List of strings to add to LaTeX preamble.  Add any
    # ``\usepackage{}`` commands here.
    #
    # .. note:: Don't forget to use raw strings to prevent
    #           escaping of characters.  Thus use something like the
    #           default value: `[r"\usepackage{amsmath}"]`"""),

    golden_mean = (np.sqrt(5) - 1) / 2
    font_size_pt = 10
    font_factors = {  # Font size reduction factors for latex fonts.
        "small": 9 / 10,
        "footnotesize": 8 / 10,
    }

    # Some units.  These can appear in expressions.
    inches_per_pt = 1.0 / 72.27
    inches = 1.0
    pt = inches_per_pt

    def __init__(self, **kw):
        self.__dict__.update(**kw)
        Object.__init__(self)

    def init(self):
        self.textwidth = self.textwidth_pt * self.inches_per_pt
        self.textheight = self.textheight_pt * self.inches_per_pt
        self.columnwidth = self.columnwidth_pt * self.inches_per_pt
        self.baselineskip = self.baselineskip_pt * self.inches_per_pt
        self.tick_font = self.font_size_pt * self.font_factors[self.tick_fontsize]

    def initialize_matplotlib(self):
        r""":class:`Figure` calls this."""
        if "aps" == self.style:
            # For APS journals: use times and no smallcaps!
            self.font = {
                "family": "serif",
                "serif": ["times"],
                "sans-serif": ["computer modern sans serif"],
                "monospace": ["computer modern typewriter"],
            }
            self.latex_preamble = (
                self.latex_preamble
                + r"\usepackage{amsmath}"
                + r"\usepackage{siunitx}"
                + r"\let\textsc\MakeUppercase"
            )
            self.textwidth_pt = 510.0
            self.textheight_pt = 672.0
            self.columnwidth_pt = 246.0
            self.font_size_pt = 10.0
            self.baselineskip_pt = 12.0

        elif "arXiv" == self.style:
            # My style for the arXiv.  Use Palatino and Euler.
            self.font = {
                "family": "serif",
                "serif": ["euler"],
                "sans-serif": ["computer modern sans serif"],
                "monospace": ["computer modern typewriter"],
            }
            self.latex_preamble = (
                self.latex_preamble
                + r"\usepackage{amsmath}"
                + r"\usepackage{siunitx}"
                + r"\usepackage[sc,osf]{mathpazo}"
                + r"\usepackage[euler-digits,small]{eulervm}"
                + r"\sisetup{mode=math, math-rm=\usefont{U}{zeur}{m}{n}{}"
                + r"\selectfont}"
            )
            self.textwidth_pt = 510.0
            self.textheight_pt = 672.0
            self.columnwidth_pt = 246.0
            self.font_size_pt = 10.0
            self.baselineskip_pt = 12.0

        matplotlib.rc("text", usetex=self.usetex)
        matplotlib.rc("font", **self.font)
        matplotlib.rc(
            "text.latex",
            preamble=self.latex_preamble,
        )
        matplotlib.rc("font", size=self.font_size_pt)
        # Use TT fonts
        matplotlib.rc("ps", fonttype=42)

        if not self.grid:
            # Disable grid-lines.  This only disables major gridlines: the minor
            # gridlines must be controlled separately... see Figure.__init__()
            matplotlib.rc("axes", grid=False)


# Default global instance.
_PLOT_PROPERTIES = LaTeXPlotProperties()


class Figure(Object):
    r"""This class represents a single figure.

    It allows customization of properties, as well as providing
    plotting facilities.

    .. note:: Units are either pts (for fonts) or inches (for linear
       measurements).

    Examples
    --------
    Here is an example of a figure suitable for a half of a page in a
    normal LaTeX book.  First we run the following file through
    LaTeX::

       \documentclass{book}
       \begin{document}
       \showthe\textwidth
       \showthe\columnwidth
       \showthe\baselineskip
       \end{document}

    This gives::

       > 345.0pt.
       l.3 \showthe\textwidth

       ?
       > 345.0pt.
       l.4 \showthe\columnwidth

       ?
       > 12.0pt.
       l.5 \showthe\baselineskip

    .. plot::
       :include-source:

       from mmfutils.plot.publish import LaTeXPlotProperties, Figure
       x = np.linspace(0, 1.01, 100)
       y = np.sin(x)
       plot_prop = LaTeXPlotProperties(textwidth_pt=345.0,
                                       columnwidth_pt=345.0,
                                       baselineskip_pt=12.0)
       fig = Figure(filename='tst_book.eps',
                    width='0.5*textwidth',
                    plot_properties=plot_prop)
       plt.plot(x, y, label="r'\sin(x)'")
       plt.axis([-0.02, 1.02, -0.02, 1.02])
       plt.ylabel(
           r'$\int_{0}^{x}\left(\frac{\cos(\tilde{x})}{1}\right)d{\tilde{x}}$')
       #fig.savefig()

    Here is another example using a two-column article::

       \documentclass[twocolumn]{article}
       \begin{document}
       \showthe\textwidth
       \showthe\columnwidth
       \showthe\baselineskip
       \end{document}

    This gives::
       > 469.0pt.
       l.3 \showthe\textwidth

       ?
       > 229.5pt.
       l.4 \showthe\columnwidth

       ?
       > 12.0pt.
       l.5 \showthe\baselineskip

    .. plot::
       :include-source:

       from mmfutils.plot.publish import LaTeXPlotProperties, Figure
       x = np.linspace(0, 1.01, 100)
       y = np.sin(x)
       plot_prop = LaTeXPlotProperties(textwidth_pt=489.0,
                                       columnwidth_pt=229.5,
                                       baselineskip_pt=12.0)
       fig = Figure(filename='tst_article.eps',
                    plot_properties=plot_prop)
       plt.plot(x, y, label="r'\sin(x)'")
       plt.axis([-0.02, 1.02, -0.02, 1.02])
       plt.ylabel(
           r'$\int_{0}^{x}\left(\frac{\cos(\tilde{x})}{1}\right)d{\tilde{x}}$')
       #fig.savefig()

    """
    num = None  # Figure number
    filename = None  # Filename for figure.
    width = "columnwidth"  # Expression involving 'columnwidth' and/or 'textwidth'
    height = 1.0  # Fraction of `golden_mean*width`
    plot_properties = None
    axes_dict = dict(labelsize="medium")
    tick_dict = dict(labelsize="small")
    legend_dict = dict(
        fontsize="medium",
        handlelength=4.0,
        frameon=True,
        # lw=0.5, c='k'
    )
    tight_layout = False

    # I cannot figure out how to set the size of the axes and allow
    # tight_layout() to work.  If you want tight_layout() to work, then you
    # should set this to be `True` and do not provide `margin_factors`.
    margin_factors = dict(  # These allocate extra space for labels etc.
        top=0.5, left=2.8, bot=3, right=0.5
    )

    autoadjust = False
    # Attempt to autoadjust for labels, otherwise you can do this manually by
    # calling :meth:`adjust`.

    figures = {}  # Dictonary of computed figures.
    on_draw_id = None  # Id associated with 'on_draw' event
    dpi = 600  # Resolution for saved figure (affects images)

    def __init__(self, **kw):
        self._kw = kw
        for _key in kw:
            if not hasattr(self, _key):
                raise AttributeError("Figure has no attribute '{}'".format(_key))
        if "margin_factors" in kw:
            margin_factors = dict(self.margin_factors)
            margin_factors.update(kw["margin_factors"])
            kw["margin_factors"] = margin_factors
        self.__dict__.update(**kw)
        Object.__init__(self)

    def init(self):
        if self.plot_properties is None:
            self.plot_properties = _PLOT_PROPERTIES
        pp = self.plot_properties
        pp.initialize_matplotlib()
        self._inset_axes = set()
        for _size in pp.font_factors:
            self._size = pp.font_size_pt * pp.font_factors[_size]

        if "num" in self._kw or "filename" in self._kw:
            width = eval(self.width, pp.__dict__)
            if isinstance(self.height, str):
                height = eval(self.height, pp.__dict__)
            else:
                height = self.height * width * pp.golden_mean

            fig_width = width
            fig_height = height

            size = pp.font_size_pt * pp.inches_per_pt

            # top space = 1/2 font
            space_top = self.margin_factors["top"] * size
            space_left = self.margin_factors["left"] * size
            space_bottom = self.margin_factors["bot"] * size
            space_right = self.margin_factors["right"] * size

            # Compute axes size:
            axes_left = space_left / fig_width
            axes_bottom = space_bottom / fig_height
            axes_width = 1.0 - (space_left + space_right) / fig_width
            axes_height = 1.0 - (space_bottom + space_top) / fig_height

            axes_size = [axes_left, axes_bottom, axes_width, axes_height]

            Defaults.set_rc(
                **{
                    "font": dict(size=pp.font_size_pt),
                    "axes": self.axes_dict,
                    "xtick": self.tick_dict,
                    "ytick": self.tick_dict,
                    "legend": self.legend_dict,
                }
            )

            plt.figure(num=self.num, figsize=(fig_width, fig_height))

            self.figure_manager = plt.get_current_fig_manager()

            """
            if mmf.utils.mac.has_appkit:
                # Check for screen info and position the window.
                screens = mmf.utils.mac.get_screen_info()
                if 1 < len(screens):
                    # More than one screen.  Put this on the second screen.
                    screen = screens[-1]
                    self.figure_manager.window.geometry(
                        "+%i+%i" % (screen.x, screen.y))
            """
            self.num = self.figure_manager.num
            self.figures[self.num] = self.figure_manager

            plt.clf()
            if self.tight_layout:
                # This creates a subplot so that tight_layout works
                ax = plt.axes()
            else:
                # This apparently does not create an axes subplot the
                # tight_layout() can work with.  No idea why.
                ax = plt.axes(axes_size)

            if pp.grid:
                ax.grid(True, which="both")
                ax.set_axisbelow(True)
                ax.xaxis.grid(True, "minor", lw=0.2)
                ax.yaxis.grid(True, "minor", lw=0.2)

        if self.autoadjust and False:
            # This makes the axis full frame.  Use adjust to shrink.
            a.set_position([0, 0, 1, 1])
            self.start_adjusting()
        elif False:
            self.stop_adjusting

    def activate(self):
        return plt.figure(self.num)

    def start_adjusting(self):
        if self.on_draw_id:
            self.figure_manager.canvas.mpl_disconnect(self.on_draw_id)
        self.on_draw_id = self.figure_manager.canvas.mpl_connect(
            "draw_event", self.on_draw
        )

    def stop_adjusting(self):
        if self.on_draw_id:
            self.figure_manager.canvas.mpl_disconnect(self.on_draw_id)
        self.on_draw_id = 0

    def new_inset_axes(self, rect):
        r"""Return a new axes set inside the main axis.

        Parameters
        ----------
        rect : [left, bottom, width or right, height or top]
           This is the rectangle for the new axes (the labels etc. will be
           outside).  Coordinates may be either floating point numbers which
           specify the location of the inset in terms of a fraction between 0
           and 1 of the current axis.

           One may also specify the coordinates in the data units of the actual
           corners by specifying the data as an imaginary number.  This will be
           transformed into relative axis coordinates using the current axis
           limits (the subplot will not subsequently move).  (Not implemented
           yet.)
        """
        ax = plt.axes(rect)
        self._inset_axes.add(ax)
        return ax

    def axis(self, *v, **kw):
        r"""Wrapper for :func:`pyplot.axis` function that applies the
        transformation to each axis (useful if :func:`pyplot.twinx` or
        :func:`pyplot.twiny` has been used)."""
        fig = self.figure_manager.canvas.figure
        for _a in fig.axes:
            _a.axis(*v, **kw)

    def adjust(self, full=True, padding=0.05):
        r"""Adjust the axes so that all text lies withing the figure.
        Optionally, add some padding."""
        plt.ioff()
        plt.figure(self.num)
        if full:
            # Reset axis to full size.
            fig = self.figure_manager.canvas.figure
            for _a in fig.axes:
                _a.set_position([0, 0, 1, 1])
        on_draw_id = self.figure_manager.canvas.mpl_connect("draw_event", self.on_draw)
        try:
            plt.ion()
            plt.draw()
        except:
            raise
        finally:
            pass
        self.figure_manager.canvas.mpl_disconnect(on_draw_id)

        adjustable_axes = [_a for _a in fig.axes if _a not in self._inset_axes]

        if 0 < padding:
            for _a in adjustable_axes:
                bb_a = _a.get_position()
                dx = bb_a.width * padding / 2
                dy = bb_a.height * padding / 2
                bb_a.x0 += dx
                bb_a.x1 -= dx
                bb_a.y0 += dy
                bb_a.y1 -= dy
                bb_a = _a.set_position(bb_a)

    @staticmethod
    def _shrink_bb(bb, factor=_EPS):
        r"""Shrink the bounding box bb by factor in order to prevent unneeded
        work due to rounding."""
        p = bb.get_points()
        p += factor * (np.diff(p) * np.array([1, -1])).T
        bb.set_points(p)
        return bb

    def _adjust(self, logger=logging.getLogger("mmf.utils.mmf_plot.Figure._adjust")):
        r"""Adjust the axes to make sure all text is inside the box."""
        fig = self.figure_manager.canvas.figure
        bb_f = fig.get_window_extent().inverse_transformed(fig.transFigure)
        logger.debug("Fig  bb %s" % (" ".join(str(bb_f).split()),))

        texts = []
        adjustable_axes = [_a for _a in fig.axes if _a not in self._inset_axes]
        for _a in adjustable_axes:
            texts.extend(_a.texts)
            texts.append(_a.title)
            texts.extend(_a.get_xticklabels())
            texts.extend(_a.get_yticklabels())
            texts.append(_a.xaxis.get_label())
            texts.append(_a.yaxis.get_label())

        bboxes = []
        for t in texts:
            if not t.get_text():
                # Ignore empty text!
                continue
            bbox = t.get_window_extent()
            # the figure transform goes from relative
            # coords->pixels and we want the inverse of that
            bboxi = bbox.inverse_transformed(fig.transFigure)
            bboxes.append(bboxi)

        # this is the bbox that bounds all the bboxes, again in
        # relative figure coords
        bbox = self._shrink_bb(matplotlib.transforms.Bbox.union(bboxes))
        adjusted = False
        if not np.all([bb_f.contains(*c) for c in bbox.corners()]):
            # Adjust axes position
            for _a in adjustable_axes:
                bb_a = _a.get_position()
                logger.debug("Text bb   %s" % (" ".join(str(bbox).split()),))
                logger.debug("Axis bb   %s" % (" ".join(str(bb_a).split()),))
                bb_a.x0 += max(0, bb_f.xmin - bbox.xmin)
                bb_a.x1 += min(0, bb_f.xmax - bbox.xmax)
                bb_a.y0 += max(0, bb_f.ymin - bbox.ymin)
                bb_a.y1 += min(0, bb_f.ymax - bbox.ymax)
                logger.debug("New  bb   %s" % (" ".join(str(bb_a).split()),))
                _a.set_position(bb_a)
            adjusted = True
        return adjusted

    def on_draw(self, event, _adjusting=[False]):
        """We register this to perform processing after the figure is
        drawn, like adjusting the margins so that the labels fit."""
        fig = self.figure_manager.canvas.figure

        logger = logging.getLogger("mmf.utils.mmf_plot.Figure.on_draw")
        if _adjusting[0]:
            # Don't recurse!
            return

        if event is None:
            # If called interactively...
            import pdb

            pdb.set_trace()
        _adjusting[0] = True

        try:
            _max_adjust = 10
            adjusted = False
            for _n in range(_max_adjust):
                adjusted = self._adjust(logger=logger)
                if adjusted:
                    fig.canvas.draw()
                else:
                    break
            if adjusted:
                # Even after _max_adjust steps we still needed adjusting:
                logger.warn("Still need adjustment after %i steps" % (_max_adjust,))
        finally:
            _adjusting[0] = False

    def adjust_axis(
        self,
        extents=None,
        xl=None,
        xh=None,
        yl=None,
        yh=None,
        extend_x=0.0,
        extend_y=0.0,
    ):
        if extents is not None:
            plt.axis(extents)
        xl_, xh_, yl_, yh_ = plt.axis()
        if xl is not None:
            xl_ = xl
        if xh is not None:
            xh_ = xh
        if yl is not None:
            yl_ = yl
        if yh is not None:
            yh_ = yh
        plt.axis([xl_, xh_, yl_, yh_])
        dx = extend_x * (xh_ - xl_)
        dy = extend_y * (yh_ - yl_)
        return plt.axis([xl_ - dx, xh_ + dx, yl_ - dy, yh_ + dy])

    def savefig(self, filename=None, dpi=None):
        if not filename:
            filename = self.filename
        print("Saving plot as %r..." % (filename,))
        plt.figure(self.num)
        plt.ion()  # Do this to ensure autoadjustments
        plt.draw()  # are made!
        if dpi is None:
            dpi = self.dpi
        plt.savefig(filename, dpi=dpi)
        print("Saving plot as %r. Done." % (filename,))

    def __del__(self):
        """Destructor: make sure we unregister the autoadjustor."""
        self.autoadjust = False
