---
jupytext:
  cell_metadata_json: true
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
kernelspec:
  display_name: Python [conda env:.conda-_mmfutils]
  language: python
  name: conda-env-.conda-_mmfutils-py
---

Here we discuss some tools for making publication quality plots with Matplotib.

```{code-cell} ipython3
:init_cell: true

%pylab inline --no-import-all
inline_rc = plt.rcParams.copy()   # Store a copy for later
deprecated_keys = ['examples.directory', 'text.latex.unicode', 
                   'savefig.frameon', 'verbose.fileo', 'verbose.level']
for key in deprecated_keys:
    inline_rc.pop(key)

# Work in a temporary directory
import os, tempfile; DIR = tempfile.TemporaryDirectory(); os.chdir(DIR.name)
DIR.name
```

```{code-cell} ipython3
plt.rcParams.update(inline_rc)
```

# Styles

+++

Much of the look of plots can be controlled by [Styles](https://matplotlib.org/tutorials/introductory/customizing.html).  There are three ways of customizing:

* **[Stylesheets](https://matplotlib.org/tutorials/introductory/customizing.html#using-style-sheets):** This is the new way of controlling the look.  See [the docs](https://matplotlib.org/tutorials/introductory/customizing.html#using-style-sheets) for possible locations.  Here we will specify the file explicitly.
* **[rcParams](https://matplotlib.org/tutorials/introductory/customizing.html#matplotlib-rcparams):** Dynamically set parameters with code like `mpl.rcParam['lines.linewidth'] = 2`.  The nice thing about this is you can do it programmatically as needed, but the downside is that the customizations get squirreled away in your code. 
* **[matplotlibrc](https://matplotlib.org/tutorials/introductory/customizing.html#the-matplotlibrc-file):**  Finally, if you want all of your plots customized to a particular style, you can update the settings in one of the `matplotlibrc` files.  See [the docs](https://matplotlib.org/tutorials/introductory/customizing.html#the-matplotlibrc-file) for possible locations of this file.

The full list of options can be seen in the [sample `matplotlibrc` file](https://matplotlib.org/tutorials/introductory/customizing.html#a-sample-matplotlibrc-file).

```{code-cell} ipython3
%%file mmfstyle.mplstyle
axes.linewidth : 1.0
axes.edgecolor : grey
axes.grid : True
axes.axisbelow : True

figure.frameon : False
    
grid.linestyle : -
grid.linewidth : 0.8
grid.color : WhiteSmoke

lines.linewidth : 1


xtick.direction : out
xtick.major.size : 2
xtick.minor.size : 1
xtick.color : k
    
ytick.direction : out
ytick.major.size : 2
ytick.minor.size : 1
ytick.color : k
    
font.family         : serif
font.size           : 10.0
#font.sans-serif     : DejaVu Sans, Bitstream Vera Sans, Computer Modern Sans Serif,
#                      Lucida Grande, Verdana, Geneva, Lucid, Arial, Helvetica,
#                      Avant Garde, sans-serif
#font.cursive        : Apple Chancery, Textile, Zapf Chancery, Sand, Script MT, Felipa, cursive
#font.fantasy        : Comic Sans MS, Chicago, Charcoal, ImpactWestern, Humor Sans, xkcd, fantasy
#font.monospace      : DejaVu Sans Mono, Bitstream Vera Sans Mono, Computer Modern Typewriter,
#                      Andale Mono, Nimbus Mono L, Courier New, Courier, Fixed, Terminal, monospace

#### LaTeX customizations. See http://wiki.scipy.org/Cookbook/Matplotlib/UsingTex
#text.usetex         : False  ## use latex for all text handling. The following fonts
                              ## are supported through the usual rc parameter settings:
                              ## new century schoolbook, bookman, times, palatino,
                              ## zapf chancery, charter, serif, sans-serif, helvetica,
                              ## avant garde, courier, monospace, computer modern roman,
                              ## computer modern sans serif, computer modern typewriter
                              ## If another font is desired which can loaded using the
                              ## LaTeX \usepackage command, please inquire at the
                              ## matplotlib mailing list
#text.latex.preamble :      ## IMPROPER USE OF THIS FEATURE WILL LEAD TO LATEX FAILURES
                            ## AND IS THEREFORE UNSUPPORTED. PLEASE DO NOT ASK FOR HELP
                            ## IF THIS FEATURE DOES NOT DO WHAT YOU EXPECT IT TO.
                            ## preamble is a comma separated list of LaTeX statements
                            ## that are included in the LaTeX document preamble.
                            ## An example:
                            ## text.latex.preamble : \usepackage{bm},\usepackage{euler}
                            ## The following packages are always loaded with usetex, so
                            ## beware of package collisions: color, geometry, graphicx,
                            ## type1cm, textcomp. Adobe Postscript (PSSNFS) font packages
                            ## may also be loaded, depending on your font settings
#text.latex.preview : False

text.hinting : auto   ## May be one of the following:
                      ##   none: Perform no hinting
                      ##   auto: Use FreeType's autohinter
                      ##   native: Use the hinting information in the
                      #              font file, if available, and if your
                      #              FreeType library supports it
                      ##   either: Use the native hinting information,
                      #              or the autohinter if none is available.
                      ## For backward compatibility, this value may also be
                      ## True === 'auto' or False === 'none'.
text.hinting_factor : 8 ## Specifies the amount of softness for hinting in the
                        ## horizontal direction.  A value of 1 will hint to full
                        ## pixels.  A value of 2 will hint to half pixels etc.
text.antialiased : True ## If True (default), the text will be antialiased.
                        ## This only affects the Agg backend.

## The following settings allow you to select the fonts in math mode.
## They map from a TeX font name to a fontconfig font pattern.
## These settings are only used if mathtext.fontset is 'custom'.
## Note that this "custom" mode is unsupported and may go away in the
## future.
#mathtext.cal : cursive
#mathtext.rm  : sans
#mathtext.tt  : monospace
#mathtext.it  : sans:italic
#mathtext.bf  : sans:bold
#mathtext.sf  : sans
#mathtext.fontset : dejavusans ## Should be 'dejavusans' (default),
                               ## 'dejavuserif', 'cm' (Computer Modern), 'stix',
                               ## 'stixsans' or 'custom'
#mathtext.fallback_to_cm : True  ## When True, use symbols from the Computer Modern
                                 ## fonts when a symbol can not be found in one of
                                 ## the custom math fonts.
#mathtext.default : it ## The default font to use for math.
                       ## Can be any of the LaTeX font names, including
                       ## the special name "regular" for the same font
                       ## used in regular text.
```

```{code-cell} ipython3
def eg():
    plt.clf()
    fig = plt.gcf()
    ax = plt.gca()
    x = np.linspace(0,1,100)
    for n in range(1, 5):
        ax.plot(x, x**n, label=f'$n={n}$')
    plt.legend()
    ax.set(xlabel='$x$\nThe abscissa.',
           ylabel='$y=x^n$',
           title="Figure with $\\mathtt{a\_title}$")
    return fig

plt.rcParams.update(inline_rc)
display(eg())
plt.style.use('mmfstyle.mplstyle')
display(eg())
plt.close('all')
```

# Figure Size

+++

Ideally, you should not scale your figures when inserting them into your document: produce the figures at the correct size so that the font size etc. will match the document.  Below we determine the `columnwidth` and the `textwidth` so we can specify the exact size of the figures.  These would be used in your LaTeX document as follows (using the [REVTeX](https://journals.aps.org/revtex) document classes):

```latex
\documentclass[10pt,aps,prl,twocolumn]{revtex4-1}
\usepackage{graphicx}
\begin{document}
\begin{figure}[htbp]
  \includegraphics[width=\columnwidth]{fig1}
  \caption{\label{fig:column}
    This is a single-column figure.}
\end{figure}


\begin{figure*}[htbp]
  % This figure will be located on the next page.
  \includegraphics[width=\textwidth]{fig2}
  \caption{\label{fig:page}
    This is a full width figure.}
\end{figure*}
\end{document}
```

+++

To do this, you can extract the appropriate size from your document by running `LaTeX`:

```{code-cell} ipython3
%%file test.tex
\documentclass[10pt,aps,prl,twocolumn]{revtex4-2}
\begin{document}
\showthe\textwidth
\showthe\textheight
\showthe\columnwidth
\showthe\baselineskip
\end{document}
```

```{code-cell} ipython3
!pdflatex --interaction=nonstopmode test.tex
```

We thus find the following values for APS papers based on ReVTeX-4.1.  To convert these to inches use the conversion factor below.

```{code-cell} ipython3
textwidth_pt = 510.0            # From LaTeX \showthe\textwidth
textheight_pt = 672.0           # From LaTeX \showthe\textheight
columnwidth_pt = 246.0          # From LaTeX \showthe\columnwidth
baselineskip_pt = 12.0          # From LaTeX \showthe\baselineskip
inches_per_pt = 1.0/72.27
golden_mean = (np.sqrt(5) - 1)/2

textwidth = textwidth_pt * inches_per_pt
textheight = textheight_pt * inches_per_pt
columnwidth = columnwidth_pt * inches_per_pt
baselineskip = baselineskip_pt * inches_per_pt
```

Now you can create proper-sized figures for single column and full-width plots:

```{code-cell} ipython3
plt.figure(figsize=(columnwidth, golden_mean*columnwidth))
display(eg())
plt.savefig("fig1.pdf")
plt.savefig("fig1.png")

plt.figure(figsize=(textwidth, golden_mean*textwidth))
display(eg())
plt.savefig("fig2.pdf")
plt.close('all')
```

```{code-cell} ipython3
%%file figtest.tex
\documentclass[10pt,aps,prl,twocolumn,floatfix]{revtex4-2}
\usepackage{graphicx}
\begin{document}
This document has two figures: One is a single column 
while the other spans a full page. 
\begin{figure}[tbp]
  \includegraphics[width=\columnwidth]{fig1}
  \caption{\label{fig:1}%
    This is a single-column figure.}
\end{figure}

\begin{figure*}[tbp]
  % This figure will be located on the next page.
  \includegraphics[width=\textwidth]{fig2}
  \caption{\label{fig:2}%
    This is a full width figure.}
\end{figure*}
\end{document}
```

```{code-cell} ipython3
!pdflatex --interaction=batchmode figtest.tex
!open figtest.pdf
```

# Tight-layout or Constrained-layout

+++

If you look at the previous figures, you will see that the smaller figure has it's labels clipped:

```{code-cell} ipython3
from IPython.display import Image
Image(filename=os.path.join(DIR.name, "fig1.png")) 
```

This can be fixed by using [tight layouts](https://matplotlib.org/users/tight_layout_guide.html) or [constrained layouts](https://matplotlib.org/tutorials/intermediate/constrainedlayout_guide.html).  Of these, simply calling `plt.tight_layout(pad=0)` often works quite well.  This leaves no padding around the figure, but as there will be whitespace in the document, this is usually fine.

```{code-cell} ipython3
plt.figure(figsize=(columnwidth, golden_mean*columnwidth))
eg()
plt.tight_layout(pad=0)
plt.savefig("fig1_tight_layout.png")
plt.close('all')
Image(filename=os.path.join(DIR.name, "fig1_tight_layout.png")) 
```

To use the constrained-layout approach, you must start with a figure or subplot with this parameter:

```{code-cell} ipython3
plt.figure(figsize=(columnwidth, golden_mean*columnwidth), constrained_layout=True)
eg()
plt.savefig("fig1_tight_layout.png")
plt.close('all')
Image(filename=os.path.join(DIR.name, "fig1_tight_layout.png")) 
```

## Advanced Usage

+++

When you have nested plot elements, these "magic" layout adjustments can shift things in unexpected ways.  To deal with this, you might need to specify that subplots have `constrained_layout=False`, or adjust further parameters.  We will discuss this again later.

+++

# Fonts

+++

Now that our figure has the correct size, we need to make sure the fonts have the correct size and match the document.  You can use fonts available on your system: just make sure that Matplotlib can find them as [described here](https://stackoverflow.com/a/27564040/1088938):

```{code-cell} ipython3
import matplotlib.font_manager
names = []
for fname in matplotlib.font_manager.get_fontconfig_fonts():
    try:
        names.append(matplotlib.font_manager.FontProperties(fname=fname).get_name())
    except:
        print(f"{fname} Failed!")
#[n for n in names if 'STIX' in n]
[n for n in names if 'TeX' in n]
```

## Neo Euler

+++

[I like to use](https://tex.stackexchange.com/a/97128/6903) the [Euler](https://en.wikipedia.org/wiki/AMS_Euler) math fonts with Palatino for text.  Most systems have Palatino, and you can get a fairly good approximation of [Neo Euler](https://github.com/khaledhosny/euler-otf) for free.  The idea here is to get as close as possible without having to invoke LaTeX which slows things down tremendously:

```{code-cell} ipython3
%%file figtest.tex
\documentclass[10pt,aps,prl,twocolumn,floatfix,amsmath]{revtex4-2}
\usepackage{graphicx}
\usepackage{lipsum}
\usepackage[T1]{fontenc}
\usepackage[tracking]{microtype}
\usepackage[sc,osf]{mathpazo}   % With old-style figures and real smallcaps.
\linespread{1.025}              % Palatino leads a little more leading

% Euler for math and numbers
\usepackage[euler-digits,small]{eulervm}
\AtBeginDocument{\renewcommand{\hbar}{\hslash}}

\begin{document}
This document has two figures: One is a single column 
while the other spans a full page. \lipsum[1-2]

\begin{figure}[htbp]
  \includegraphics[width=\columnwidth]{fig1}
  \caption{\label{fig:1}%
    This is a single-column figure.}
\end{figure}

\begin{gather}
  y=x^n, \qquad n \in \{1, 2, 3, 4\}.
\end{gather}

\begin{figure*}[tbp]
  % This figure will be located on the next page.
  \includegraphics[width=\textwidth]{fig2}
  \caption{\label{fig:2}%
    This is a full width figure.}
\end{figure*}
\lipsum[3-20]


\end{document}
```

```{code-cell} ipython3
plt.rcParams.update(inline_rc)
plt.rcParams['text.usetex'] = False
plt.rcParams['font.size'] = 10.0
plt.rcParams['font.serif'] = ['Palatino Linotype']
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.rm'] = 'Neo Euler'
plt.rcParams['mathtext.it'] = 'Neo Euler'

plt.figure(figsize=(columnwidth, golden_mean*columnwidth), constrained_layout=True)
display(eg())
plt.savefig("fig1.pdf")

plt.figure(figsize=(textwidth, golden_mean*textwidth), constrained_layout=True)
display(eg())
plt.savefig("fig2.pdf")

plt.close('all')
!pdflatex --interaction=batchmode figtest.tex 
!open figtest.pdf
```

## Times

+++

The default APS fonts are based on Times.  Here we can use the [STIX](https://www.stixfonts.org) fonts to match these:

```{code-cell} ipython3
%%file figtest.tex
\documentclass[10pt,aps,prl,twocolumn,floatfix,amsmath]{revtex4-2}
\usepackage{graphicx}
\usepackage{lipsum}
\usepackage{newtxtext}
\usepackage[varg]{newtxmath}
\begin{document}
This document has two figures: One is a single column 
while the other spans a full page. \lipsum[1-2]

\begin{figure}[htbp]
  \includegraphics[width=\columnwidth]{fig1}
  \caption{\label{fig:1}%
    This is a single-column figure.}
\end{figure}

\begin{gather}
  y=x^n, \qquad n \in \{1, 2, 3, 4\}.
\end{gather}

\lipsum[3-20]
\begin{figure*}[tbp]
  % This figure will be located on the next page.
  \includegraphics[width=\textwidth]{fig2}
  \caption{\label{fig:2}%
    This is a full width figure.}
\end{figure*}
\end{document}
```

```{code-cell} ipython3
[n for n in plt.rcParams if 'font' in n]
```

```{code-cell} ipython3
plt.rcParams.update(inline_rc)
#plt.rcParams['text.usetex'] = False
#plt.rcParams['font.size'] = 10.0
#plt.rcParams['font.serif'] = ['STIXGeneral']
#plt.rcParams['font.sans-serif'] = ['TeX Gyre Heros']
#plt.rcParams['font.monospace'] = ['Ariel']
plt.rcParams['mathtext.fontset'] = 'stix'
#plt.rcParams['mathtext.tt'] = 'TeX Gyre Bonum'

plt.figure(figsize=(columnwidth, golden_mean*columnwidth), constrained_layout=True)
display(eg())
plt.savefig("fig1.pdf")
plt.close('all')
!pdflatex --interaction=batchmode figtest.tex 
!open figtest.pdf
```

## LaTeX

+++

When you are ready for publication quality images, you should switch to LaTeX to generate the labels.  This is much slower, but will use exactly the same fonts as in your document, with all proper typesetting.

```{code-cell} ipython3
%%file figtest.tex
\documentclass[10pt,aps,prl,twocolumn,floatfix,amsmath]{revtex4-2}
\usepackage{graphicx}
\usepackage{lipsum}
\usepackage[osf]{newtxtext}
\usepackage[varg]{newtxmath}
%\usepackage[scaled]{berasans}
%\usepackage[scaled]{beramono}
\usepackage[scaled]{helvet}

\begin{document}
This document has two figures: One is a single column 
while the other spans a full page. \lipsum[1-2]

\begin{figure}[htbp]
  \includegraphics[width=\columnwidth]{fig1}
  \caption{\label{fig:1}%
    This is a single-column figure.}
\end{figure}

\begin{gather}
  y=x^n, \qquad n \in \{1, 2, 3, 4\}.
\end{gather}

We use these labels:
\begin{enumerate}
\item \texttt{a\_label}
\end{enumerate}

\lipsum[3-20]
\begin{figure*}[tbp]
  % This figure will be located on the next page.
  \includegraphics[width=\textwidth]{fig2}
  \caption{\label{fig:2}%
    This is a full width figure.}
\end{figure*}
\end{document}
```

```{code-cell} ipython3
plt.rcParams['text.usetex'] = False
#plt.rcParams['text.latex.preamble'] 
```

```{code-cell} ipython3
fig = plt.figure(figsize=(columnwidth, golden_mean*columnwidth), constrained_layout=True)
eg()
plt.title("Figure with $\\mathtt{a\_label}$")
plt.savefig("fig1.pdf")
plt.savefig("fig1.png")
plt.close('all')
Image(filename=os.path.join(DIR.name, "fig1.png")) 
```

```{code-cell} ipython3
!pdflatex --interaction=batchmode figtest.tex
!open figtest.pdf
```

# Sparklines

+++

Sparklines (see [Sparkline theory and practice](https://www.edwardtufte.com/bboard/q-and-a-fetch-msg?msg_id=0001OR) for examples) are small pictures to be treated as words inline.  Here is some code for generating them with LaTeX.  This is useful for getting the correct height (the same as capital letters) but this can be done separately by looking at the output of the following code:

```latex
\newlength\capheight
\settoheight\capheight{ABCDEFGHIJKLMNOPQRSTUVWXYZ}
\showthe\capheight
```


```latex
\usepackage{xparse}
\usepackage{tikz}
\usetikzlibrary{fpu}

\newlength\capheight
\settoheight\capheight{ABCDEFGHIJKLMNOPQRSTUVWXYZ}

\makeatletter
% Arguments (should be replaced by pgfkeys)
% [#1] width
% [#2] height
% (#3) domain (default "(0,1)")
% (#4) range (default "(0,1)"
% #5 function
\DeclareDocumentCommand{\sparkline}
{
  O{3em}
  O{0.5ex+0.5\capheight}
  > {\SplitArgument{1}{,}}D(){0,1}
  > {\SplitArgument{1}{,}}D(){0,1}
  m
}{\begin{tikzpicture}[]
    \def\xa{\@firstoftwo #3}
    \def\xb{\@secondoftwo #3}
    \def\ya{\@firstoftwo #4}
    \def\yb{\@secondoftwo #4}
    \draw[ultra thin,smooth,
          x=#1/(\xb - \xa),
          y=#2/(\yb - \ya),
          domain=\xa:\xb,
          /pgf/fpu,/pgf/fpu/output format=fixed,
          % http://tex.stackexchange.com/a/33116/6903
    ] plot (\x, {#5});
  \end{tikzpicture}}
\makeatother

%\documentclass{article}
%\begin{document}
%Hi \sparkline(0.01,0.99)(0,1){(1 + tanh(3.0*tan((2*pi*\x - pi)/2 r)))/2} there.
%\end{document}
```

```{code-cell} ipython3
inches_per_pt = 1/72.27
capheight = 6.83331*inches_per_pt
height = capheight
width = 3*capheight
_EPS = np.finfo(float).eps

############
from scipy.integrate import quad

sigma = 1.0

def f(x):
    return np.where(abs(x) < sigma, np.exp(-x**2/2/sigma**2), 0)

N = quad(f, -1, 1)[0]

x = np.unique(np.concatenate([
    np.linspace(-2.5, 2.5, 5),
    np.linspace(-1, 1, 20),    
    [-1 - _EPS, -1 + _EPS, 1 - _EPS, 1+_EPS]]))
y = f(x)/N
##############


fig = plt.figure(figsize=(width,height))
ax = fig.add_axes([0, 0, 1, 1])
l, = ax.plot(x, y, 'k-', lw=1.0)

# Small offset to include line-width.  Can we do this automatically?
pt_in_data = 0.1
dy = 0.5*l.get_lw() * pt_in_data
ax.set(xlim=[x.min(), x.max()], ylim=[y.min()-dy, y.max()+dy])
ax.axhline([0], lw=0.1, ls='--', c='k')
#ax.set(ylim=(-0.1, y.max()+0.1))
# remove all the axes
for k,v in ax.spines.items():
    v.set_visible(False)
ax.set_xticks([])
ax.set_yticks([])
plt.savefig("sparkline.pdf")
!open sparkline.pdf
```

```{code-cell} ipython3
fig.add_axes?
```

# Gotchas

+++

## Notebooks

There are a couple of gotchas when using Jupyter Notebooks.

+++

### "Inline" Style

The IPython `%pylab inline` or `%matplotlib inline` magic has it's [own style built in](https://stackoverflow.com/a/26413529/1088938) which is a little different than the default.  Here we can see these differences:

```{code-cell} ipython3
def param_diff(p1, p2):
    p1, p2 = p1.copy(), p2.copy()
    diffs = {}
    for p in p1:
        if p in p2 and p1[p] == p2[p]:
            continue
        diffs[p] = (p1[p], p2.get(p, NotImplemented))
    for p in set(p2).difference(p1):
        diffs[p] = (NotImplemented, p2[p])
    return diffs

param_diff(inline_rc, plt.rcParamsDefault)
```

```{code-cell} ipython3
plt.style.use('default')
param_diff(inline_rc, plt.rcParams)
```

The differences are basically the figure size, dpi, and a slight change in the bottom of the subplot.

+++

### Displaying Plots

+++

If you open a plot with the `inline` backend, it will be displayed, even if it is not explicitly displayed (by being the last output for example).  Conversely, if the output of your cell contains the figure, you will likely get two copies (for example, if your function returns the figure):

```{code-cell} ipython3
plt.plot([1,2], [1,2])
plt.gcf()
```

To suppress this, you can suppress the final output with a semicolon `;`, or you can close the figures and explicitly display the one you want.  This latter option can be helpful if you generate many figures, e.g. during an animation.  In the latter case, you are probably best reusing a single figure (faster) but another option is to explicitly close all figures:

```{code-cell} ipython3
plt.plot([0, 1])
fig = plt.gcf()
plt.close('all')
fig
```

```{code-cell} ipython3
plt.style.available
```

## Fonts

+++

### Cache

+++

If you change fonts on your system, you might sometimes need to [rebuild the cache:](https://bastibe.de/2016-05-30-matplotlib-font-cache.html)

```{code-cell} ipython3
matplotlib.font_manager.findfont('Calluna Sans')
```

```{code-cell} ipython3
matplotlib.font_manager._rebuild()
```

### LaTeX vs Mathtext

+++

It is desirable to be able to switch the `text.usetex` flag off (for speed) and on (for quality).  This requires a little care in what type of text you use.  In particular, you cannot freely use all LaTeX commands - especially font switching.  Ideally, you should restrict yourself to commands available with [mathtext](https://matplotlib.org/tutorials/text/mathtext.html).  Thus, instead of the AMS `\text{}` command, you should use `\mathrm{}` or leave the text outside of `$$`; instead of `\texttt{}` use `\mathtt{}` etc.

Here are some examples.

+++

https://matplotlib.org/tutorials/text/mathtext.html
