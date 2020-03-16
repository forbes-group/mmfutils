# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_json: true
#     formats: ipynb,py
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.0
#   kernelspec:
#     display_name: Python [conda env:_mmfutils]
#     language: python
#     name: conda-env-_mmfutils-py
# ---

# # MMF Utils

# Small set of utilities: containers and interfaces.
#
# This package provides some utilities that I tend to rely on during development.  Presently it includes some convenience containers, plotting tools, and a patch for including [zope.interface](http://docs.zope.org/zope.interface/) documentation in a notebook.
#
# (Note: If this file does not render properly, try viewing it through [nbviewer.org](http://nbviewer.ipython.org/urls/bitbucket.org/mforbes/mmfutils-fork/raw/tip/doc/README.ipynb))
#
# **Documentation:**
#    http://mmfutils.readthedocs.org
#
# **Source:**
#    https://bitbucket.org/mforbes/mmfutils
#    
# **Issues:**
#   https://bitbucket.org/mforbes/mmfutils/issues
#   
# **Build Status:**
#
# <table>
#   <tr>
#     <td>[Main](https://bitbucket.org/mforbes/mmfutils)</td>
#     <td>[Fork](https://bitbucket.org/mforbes/mmfutils-fork)</td>
#   </tr><tr>
#     <td>[![mmfutils Build Status]](https://drone.io/bitbucket.org/mforbes/mmfutils/latest)</td>
#     <td>[![mmfutils-fork Build Status]](https://drone.io/bitbucket.org/mforbes/mmfutils-fork/latest)</td>
#   </tr>
# </table>
#
# [mmfutils Build Status]: https://drone.io/bitbucket.org/mforbes/mmfutils/status.png
# [mmfutils-fork Build Status]: https://drone.io/bitbucket.org/mforbes/mmfutils-fork/status.png

# + [markdown] {"toc": "true"}
# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><span><a href="#MMF-Utils" data-toc-modified-id="MMF-Utils-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>MMF Utils</a></span><ul class="toc-item"><li><span><a href="#Installing" data-toc-modified-id="Installing-1.1"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>Installing</a></span></li></ul></li><li><span><a href="#Usage" data-toc-modified-id="Usage-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Usage</a></span><ul class="toc-item"><li><span><a href="#Containers" data-toc-modified-id="Containers-2.1"><span class="toc-item-num">2.1&nbsp;&nbsp;</span>Containers</a></span><ul class="toc-item"><li><span><a href="#ObjectBase-and-Object" data-toc-modified-id="ObjectBase-and-Object-2.1.1"><span class="toc-item-num">2.1.1&nbsp;&nbsp;</span>ObjectBase and Object</a></span><ul class="toc-item"><li><span><a href="#Object-Example" data-toc-modified-id="Object-Example-2.1.1.1"><span class="toc-item-num">2.1.1.1&nbsp;&nbsp;</span>Object Example</a></span></li></ul></li><li><span><a href="#Container" data-toc-modified-id="Container-2.1.2"><span class="toc-item-num">2.1.2&nbsp;&nbsp;</span>Container</a></span><ul class="toc-item"><li><span><a href="#Container-Examples" data-toc-modified-id="Container-Examples-2.1.2.1"><span class="toc-item-num">2.1.2.1&nbsp;&nbsp;</span>Container Examples</a></span></li></ul></li></ul></li><li><span><a href="#Contexts" data-toc-modified-id="Contexts-2.2"><span class="toc-item-num">2.2&nbsp;&nbsp;</span>Contexts</a></span></li><li><span><a href="#Interfaces" data-toc-modified-id="Interfaces-2.3"><span class="toc-item-num">2.3&nbsp;&nbsp;</span>Interfaces</a></span><ul class="toc-item"><li><span><a href="#Interface-Documentation" data-toc-modified-id="Interface-Documentation-2.3.1"><span class="toc-item-num">2.3.1&nbsp;&nbsp;</span>Interface Documentation</a></span></li></ul></li><li><span><a href="#Parallel" data-toc-modified-id="Parallel-2.4"><span class="toc-item-num">2.4&nbsp;&nbsp;</span>Parallel</a></span></li><li><span><a href="#Performance" data-toc-modified-id="Performance-2.5"><span class="toc-item-num">2.5&nbsp;&nbsp;</span>Performance</a></span></li><li><span><a href="#Plotting" data-toc-modified-id="Plotting-2.6"><span class="toc-item-num">2.6&nbsp;&nbsp;</span>Plotting</a></span><ul class="toc-item"><li><span><a href="#Fast-Filled-Contour-Plots" data-toc-modified-id="Fast-Filled-Contour-Plots-2.6.1"><span class="toc-item-num">2.6.1&nbsp;&nbsp;</span>Fast Filled Contour Plots</a></span></li></ul></li><li><span><a href="#Angular-Variables" data-toc-modified-id="Angular-Variables-2.7"><span class="toc-item-num">2.7&nbsp;&nbsp;</span>Angular Variables</a></span></li><li><span><a href="#Debugging" data-toc-modified-id="Debugging-2.8"><span class="toc-item-num">2.8&nbsp;&nbsp;</span>Debugging</a></span></li><li><span><a href="#Mathematics" data-toc-modified-id="Mathematics-2.9"><span class="toc-item-num">2.9&nbsp;&nbsp;</span>Mathematics</a></span></li></ul></li><li><span><a href="#Developer-Instructions" data-toc-modified-id="Developer-Instructions-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Developer Instructions</a></span><ul class="toc-item"><li><span><a href="#Releases" data-toc-modified-id="Releases-3.1"><span class="toc-item-num">3.1&nbsp;&nbsp;</span>Releases</a></span></li></ul></li><li><span><a href="#Change-Log" data-toc-modified-id="Change-Log-4"><span class="toc-item-num">4&nbsp;&nbsp;</span>Change Log</a></span><ul class="toc-item"><li><span><a href="#REL:-0.5.1" data-toc-modified-id="REL:-0.5.1-4.1"><span class="toc-item-num">4.1&nbsp;&nbsp;</span>REL: 0.5.1</a></span></li><li><span><a href="#REL:-0.5.0" data-toc-modified-id="REL:-0.5.0-4.2"><span class="toc-item-num">4.2&nbsp;&nbsp;</span>REL: 0.5.0</a></span></li><li><span><a href="#REL:-0.4.13" data-toc-modified-id="REL:-0.4.13-4.3"><span class="toc-item-num">4.3&nbsp;&nbsp;</span>REL: 0.4.13</a></span></li><li><span><a href="#REL:-0.4.10" data-toc-modified-id="REL:-0.4.10-4.4"><span class="toc-item-num">4.4&nbsp;&nbsp;</span>REL: 0.4.10</a></span></li><li><span><a href="#REL:-0.4.9" data-toc-modified-id="REL:-0.4.9-4.5"><span class="toc-item-num">4.5&nbsp;&nbsp;</span>REL: 0.4.9</a></span></li><li><span><a href="#REL:-0.4.7" data-toc-modified-id="REL:-0.4.7-4.6"><span class="toc-item-num">4.6&nbsp;&nbsp;</span>REL: 0.4.7</a></span></li></ul></li></ul></div>
# -

# ## Installing

# This package can be installed from [from the bitbucket project](https://bitbucket.org/mforbes/mmfutils):
#
# ```bash
# pip install hg+https://bitbucket.org/mforbes/mmfutils
# ```

# # Usage

# ## Containers

# ### ObjectBase and Object

# The `ObjectBase` and `Object` classes provide some useful features described below. Consider a problem where a class is defined through a few parameters, but requires extensive initialization before it can be properly used.  An example is a numerical simulation where one passes the number of grid points $N$ and a length $L$, but the initialization must generate large grids for efficient use later on.  These grids should be generated before computations begin, but should not be re-generated every time needed.  They also should not be pickled when saved to disk.
#
# **Deferred initialization via the `init()` method:** The idea here changes the semantics of `__init__()` slightly by deferring any expensive initialization to `init()`.  Under this scheme, `__init__()` should only set and check what we call picklable attributes: these are parameters that define the object (they will be pickled in `Object` below) and will be stored in a list `self.picklable_attributes` which is computed at the end of `ObjectBase.__init__()` as the list of all keys in `__dict__`.  Then, `ObjectBase.__init__()` will call `init()` where all remaining attributes should be calculated.  
#
# This allows users to change various attributes, then reinitialize the object once with an explicit call to `init()` before performing expensive computations.  This is an alternative to providing complete properties (getters and setters) for objects that need to trigger computation.  The use of setters is safer, but requires more work on the side of the developer and can lead to complex code when different properties depend on each other.  The approach here puts all computations in a single place.  Of course, the user must remember to call `init()` before working with the object.
#
# To facilitate this, we provide a mild check in the form of an `initialized` flag that is set to `True` at the end of the base `init()` chain, and set to `False` if any variables are in `pickleable_attributes` are set.
#
# **Serialization and Deferred Initialization:** 
# The base class `ObjectBase` does not provide any pickling services but does provide a nice representation.  Additional functionality is provided by `Object` which uses the features of `ObjectBase` to define `__getstate__()` and `__setstate__()` methods for pickling which pickle only the `picklable_attributes`.  Note: unpickling an object will **not** call `__init__()` but will call `init()` giving objects a chance to restore the computed attributes from pickles.
#
# * **Note:** *Before using, consider if these features are really needed – with all such added functionality comes additional potential failure modes from side-interactions. The `ObjectBase` class is quite simple, and therefore quite safe, while `Object` adds additional functionality with potential side-effects.  For example, a side-effect of support for pickles is that `copy.copy()` will also invoke `init()` when copying might instead be much faster.  Thus, we recommend only using `ObjectBase` for efficient code.*

# #### Object Example

# +
ROOTDIR = !hg root
ROOTDIR = ROOTDIR[0]
import sys;sys.path.insert(0, ROOTDIR)

import numpy as np

from mmfutils.containers import ObjectBase, ObjectMixin

class State(ObjectBase):  
    _quiet = False
    def __init__(self, N, L=1.0, **kw):
        """Set all of the picklable parameters, in this case, N and L."""
        self.N = N
        self.L = L
        
        # Now register these and call init()
        super().__init__(**kw)
        if not self._quiet:
            print("__init__() called")
        
    def init(self):
        """All additional initializations"""
        if not self._quiet:
            print("init() called")
        dx = self.L / self.N
        self.x = np.arange(self.N, dtype=float) * dx - self.L/2.0
        self.k = 2*np.pi * np.fft.fftfreq(self.N, dx)

        # Set highest momentum to zero if N is even to
        # avoid rapid oscillations
        if self.N % 2 == 0:
            self.k[self.N//2] = 0.0

        # Calls base class which sets self.initialized
        super().init()
            
    def compute_derivative(self, f):
        """Return the derivative of f."""        
        return np.fft.ifft(self.k*1j*np.fft.fft(f)).real

s = State(256)
print(s)  # No default value for L
# -

s.L = 2.0
print(s)

# One feature is that a nice ``repr()`` of the object is produced.  Now let's do a calculation:

f = np.exp(3*np.cos(2*np.pi*s.x/s.L)) / 15
df = -2.*np.pi/5.*np.exp(3*np.cos(2*np.pi*s.x/s.L))*np.sin(2*np.pi*s.x/s.L)/s.L
np.allclose(s.compute_derivative(f), df)

# Oops!  We forgot to reinitialize the object... (The formula is correct, but the lattice is no longer commensurate so the FFT derivative has huge errors).

print(s.initialized)
s.init()
assert s.initialized
f = np.exp(3*np.cos(2*np.pi*s.x/s.L)) / 15
df = -2.*np.pi/5.*np.exp(3*np.cos(2*np.pi*s.x/s.L))*np.sin(2*np.pi*s.x/s.L)/s.L
np.allclose(s.compute_derivative(f), df)


# Here we demonstrate pickling.  Note that using `Object` makes the pickles very small, and when unpickled, ``init()`` is called to re-establish ``s.x`` and ``s.k``.  Generally one would inherit from `Object`, but since we already have a class, we can provide pickling functionality with `ObjectMixin`:

# +
class State1(ObjectMixin, State):
    pass

s = State(N=256, _quiet=True)
s1 = State1(N=256, _quiet=True)
# -

import pickle, copy
s_repr = pickle.dumps(s)
s1_repr = pickle.dumps(s1)
print(f"ObjectBase pickle:  {len(s_repr)} bytes")
print(f"ObjectMixin pickle: {len(s1_repr)} bytes")

# Note, however, that the speed of copying is significantly impacted:

# %timeit copy.copy(s)
# %timeit copy.copy(s1)

# Another use case applies when ``init()`` is expensive.  If $x$ and $k$ were computed in ``__init__()``, then using properties to change both $N$ and $L$ would trigger two updates.  Here we do the updates, then call ``init()``.  Good practice is to call ``init()`` automatically before any serious calculation to ensure that the object is brought up to date before the computation.

s.N = 64
s.L = 2.0
s.init()

# Finally, we demonstrate that ``Object`` instances can be archived using the ``persist`` package:

# +
import persist.archive
a = persist.archive.Archive(check_on_insert=True)
a.insert(s=s)

d = {}
exec(str(a), d)

d['s']
# -

# ### Container

# The ``Container`` object is a slight extension of ``Object`` that provides a simple container for storing data with attribute and iterative access. These implement some of the [Collections Abstract Base Classes from the python standard library](https://docs.python.org/2/library/collections.html#collections-abstract-base-classes). The following containers are provided:
#
# - ``Container``: Bare-bones container extending the ``Sized``, ``Iterable``, and ``Container`` abstract ase classes (ABCs) from the standard ``containers`` library.
# - ``ContainerList``: Extension that acts like a tuple/list satisfying the ``Sequence`` ABC from the ``containers`` library (but not the ``MutableSequence`` ABC.  Although we allow setting and deleting items, we do not provide a way for insertion, which breaks this interface.)
# - ``ContainerDict``: Extension that acts like a dict satisfying the ``MutableMapping`` ABC from the ``containers`` library.
#
# These were designed with the following use cases in mind:
#
# - Returning data from a function associating names with each data.  The resulting ``ContainerList`` will act like a tuple, but will support attribute access.  Note that the order will be lexicographic.  One could use a dictionary, but attribute access with tab completion is much nicer in an interactive session.  The ``containers.nametuple`` generator could also be used, but this is somewhat more complicated (though might be faster).  Also, named tuples are immutable - here we provide a mutable object that is picklable etc.  The choice between ``ContainerList`` and ``ContainerDict`` will depend on subsequent usage.  Containers can be converted from one type to another.

# #### Container Examples

# +
from mmfutils.containers import Container

c = Container(a=1, c=2, b='Hi there')
print(c)
print(tuple(c))
# -

# Attributes are mutable
c.b = 'Ho there'
print(c)

# +
# Other attributes can be used for temporary storage but will not be pickled.
import numpy as np

c.large_temporary_array = np.ones((256,256))
print(c)
print(c.large_temporary_array)
# -

import pickle
c1 = pickle.loads(pickle.dumps(c))
print(c1)
c1.large_temporary_array

# ## Contexts

# The ``mmfutils.contexts`` module provides two useful contexts:
#
# ``NoInterrupt``: This can be used to susspend ``KeyboardInterrupt`` exceptions until they can be dealt with at a point that is convenient.  A typical use is when performing a series of calculations in a loop.  By placing the loop in a ``NoInterrupt`` context, one can avoid an interrupt from ruining a calculation:

# +
from mmfutils.contexts import NoInterrupt

complete = False
n = 0
with NoInterrupt() as interrupted:
    while not complete and not interrupted:
        n += 1
        if n > 10:
            complete = True
# -

# Note: One can nest ``NoInterrupt`` contexts so that outer loops are also interrupted.  Another use-case is mapping.  See [doc/Animation.ipynb](Animation.ipynb) for more examples.

res = NoInterrupt().map(abs, range(-100, 100))
np.sign(res)

# ## Interfaces

# The interfaces module collects some useful [zope.interface](http://docs.zope.org/zope.interface/) tools for checking interface requirements.  Interfaces provide a convenient way of communicating to a programmer what needs to be done to used your code.  This can then be checked in tests.

# +
from mmfutils.interface import Interface, Attribute, verifyClass, verifyObject, implementer

class IAdder(Interface):
    """Interface for objects that support addition."""

    value = Attribute('value', "Current value of object")

    # No self here since this is the "user" interface
    def add(other):
        """Return self + other."""


# -

# Here is a broken implementation. We muck up the arguments to ``add``:

# +
@implementer(IAdder)
class AdderBroken(object):
    def add(self, one, another):
        # There should only be one argument!
        return one + another

try:
    verifyClass(IAdder, AdderBroken)
except Exception as e:
    print("{0.__class__.__name__}: {0}".format(e))
    
# -

# Now we get ``add`` right, but forget to define ``value``.  This is only caught when we have an object since the attribute is supposed to be defined in ``__init__()``:

# +
@implementer(IAdder)
class AdderBroken(object):
    def add(self, other):
        return one + other

# The class validates...
verifyClass(IAdder, AdderBroken)

# ... but objects are missing the value Attribute
try:
    verifyObject(IAdder, AdderBroken())
except Exception as e:
    print("{0.__class__.__name__}: {0}".format(e))    


# -

# Finally, a working instance:

# +
@implementer(IAdder)
class Adder(object):
    def __init__(self, value=0):
        self.value = value
    def add(self, other):
        return one + other
    
verifyClass(IAdder, Adder) and verifyObject(IAdder, Adder())
# -

# ### Interface Documentation

# We also monkeypatch ``zope.interface.documentation.asStructuredText()`` to provide a mechanism for documentating interfaces in a notebook.

from mmfutils.interface import describe_interface
describe_interface(IAdder)

# ## Parallel

# The ``mmfutils.parallel`` module provides some tools for launching and connecting to IPython clusters.  The ``parallel.Cluster`` class represents and controls a cluster.  The cluster is specified by the profile name, and can be started or stopped from this class:

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
import numpy as np
from mmfutils import parallel
cluster = parallel.Cluster(profile='default', n=3, sleep_time=1.0)
cluster.start()
cluster.wait()  # Instance of IPython.parallel.Client
view = cluster.load_balanced_view
x = np.linspace(-6, 6, 100)
y = view.map(lambda x:x**2, x)
print(np.allclose(y, x**2))
cluster.stop()

# If you only need a cluster for a single task, it can be managed with a context.  Be sure to wait for the result to be computed before exiting the context and shutting down the cluster!

with parallel.Cluster(profile='default', n=3, sleep_time=1.0) as client:
    view = client.load_balanced_view
    x = np.linspace(-6, 6, 100)
    y = view.map(lambda x:x**2, x, block=True)  # Make sure to wait for the result!
print(np.allclose(y, x**2))

# If you just need to connect to a running cluster, you can use ``parallel.get_client()``.

# ## Performance

# The ``mmfutils.performance`` module provides some tools for high performance computing.  Note: this module requires some additional packages including [numexp](https://github.com/pydata/numexpr/wiki/Numexpr-Users-Guide), [pyfftw](http://hgomersall.github.io/pyFFTW/), and the ``mkl`` package installed by anaconda.  Some of these require building system libraries (i.e. the [FFTW](http://www.fftw.org)).  However, the various components will not be imported by default.
#
# Here is a brief description of the components:
#
# * ``mmfutils.performance.blas``: Provides an interface to a few of the scipy BLAS wrappers.  Very incomplete (only things I currently need).
# * ``mmfutils.performance.fft``: Provides an interface to the [FFTW](http://www.fftw.org) using ``pyfftw`` if it is available.  Also enables the planning cache and setting threads so you can better control your performance.
# * ``mmfutils.performance.numexpr``: Robustly imports numexpr and disabling the VML.  (If you don't do this carefully, it will crash your program so fast you won't even get a traceback.)
# * ``mmfutils.performance.threads``: Provides some hooks for setting the maximum number of threads in a bunch of places including the MKL, numexpr, and fftw.

# ## Plotting

# Several tools are provided in `mmfutils.plot`:

# ### Fast Filled Contour Plots

# `mmfutils.plot.imcontourf` is similar to matplotlib's `plt.contourf` function, but uses `plt.imshow` which is much faster.  This is useful for animations and interactive work.  It also supports my idea of saner array-shape processing (i.e. if `x` and `y` have different shapes, then it will match these to the shape of `z`).  Matplotlib now provies `plt.pcolourmesh` which is similar, but has the same interface issues.

# %matplotlib inline
from matplotlib import pyplot as plt
import time
import numpy as np
from mmfutils import plot as mmfplt
x = np.linspace(-1, 1, 100)[:, None]**3
y = np.linspace(-0.1, 0.1, 200)[None, :]**3
z = np.sin(10*x)*y**2
plt.figure(figsize=(12,3))
plt.subplot(141)
# %time mmfplt.imcontourf(x, y, z, cmap='gist_heat')
plt.subplot(142)
# %time plt.contourf(x.ravel(), y.ravel(), z.T, 50, cmap='gist_heat')
plt.subplot(143)
# %time plt.pcolor(x.ravel(), y.ravel(), z.T, cmap='gist_heat')
plt.subplot(144)
# %time plt.pcolormesh(x.ravel(), y.ravel(), z.T, cmap='gist_heat')

# ## Angular Variables

# A couple of tools are provided to visualize angular fields, such as the phase of a complex wavefunction.

# +
# %matplotlib inline
from matplotlib import pyplot as plt
import time
import numpy as np
from mmfutils import plot as mmfplt
x = np.linspace(-1, 1, 100)[:, None]
y = np.linspace(-1, 1, 200)[None, :]
z = x + 1j*y

plt.figure(figsize=(9,2))
ax = plt.subplot(131)
mmfplt.phase_contour(x, y, z, colors='k', linewidths=0.5)
ax.set_aspect(1)

# This is a little slow but allows you to vary the luminosity.
ax = plt.subplot(132)
mmfplt.imcontourf(x, y, mmfplt.colors.color_complex(z))
mmfplt.phase_contour(x, y, z, linewidths=0.5)
ax.set_aspect(1)

# This is faster if you just want to show the phase and allows
# for a colorbar via a registered colormap
ax = plt.subplot(133)
mmfplt.imcontourf(x, y, np.angle(z), cmap='huslp')
ax.set_aspect(1)
plt.colorbar()
mmfplt.phase_contour(x, y, z, linewidths=0.5)
# -

# ## Debugging

# A couple of debugging tools are provided.  The most useful is the `debug` decorator which will store the local variables of a function in a dictionary or in your global scope.

# +
from mmfutils.debugging import debug

@debug(locals())
def f(x):
    y = x**1.5
    z = 2/x
    return z

print(f(2.0), x, y, z)
# -

# ## Mathematics

# We include a few mathematical tools here too.  In particular, numerical integration and differentiation.  Check the API documentation for details.

# # Developer Instructions

# If you are a developer of this package, there are a few things to be aware of.
#
# 1. If you modify the notebooks in ``docs/notebooks`` then you may need to regenerate some of the ``.rst`` files and commit them so they appear on bitbucket.  This is done automatically by the ``pre-commit`` hook in ``.hgrc`` if you include this in your ``.hg/hgrc`` file with a line like:
#
#     ```
#     %include ../.hgrc
#     ```
#
# **Security Warning:** if you do this, be sure to inspect the ``.hgrc`` file carefully to make sure that no one inserts malicious code.
#
# This runs the following code:

# !cd $ROOTDIR; jupyter nbconvert --to=rst --output=README.rst doc/README.ipynb

# We also run a comprehensive set of tests, and the pre-commit hook will fail if any of these do not pass, or if we don't have complete code coverage.  We run these tests in a conda environment that can be made using the makefile:
#
# ```bash
# make envs
# make test   # conda run -n _mmfutils pytest
# ```
#
# To run these manually you could do:
#
# ```bash
# cond activate _mmfutils
# pytest
# ```

# Here is an example:

# !cd $ROOTDIR; conda activate _mmfutils; pytest -n4

# Complete code coverage information is provided in ``build/_coverage/index.html``.

from IPython.display import HTML
with open(os.path.join(ROOTDIR, 'build/_coverage/index.html')) as f:
    coverage = f.read()
HTML(coverage)

# ## Releases

# We try to keep the repository clean with the following properties:
#
# 1. The default branch is stable: i.e. if someone runs `hg clone`, this will pull the latest stable release.
# 2. Each release has its own named branch so that e.g. `hg up 0.5.0` will get the right thing.  Note: this should update to the development branch, *not* the default branch so that any work committed will not pollute the development branch (which would violate the previous point).
#
# To do this, we advocate the following proceedure.
#
# 1. **Update to Correct Branch**: Make sure this is the correct development branch, not the default branch by explicitly updating:
#
#    ```bash
#    hg up <version>
#    ```
#    
#    (Compare with `hg up default` which should take you to the default branch instead.)
# 2. **Work**: Do your work, committing as required with messages as shown in the repository with the following keys:
#
#    * `DOC`: Documentation changes.
#    * `API`: Changes to the exising API.  This could break old code.
#    * `EHN`: Enhancement or new functionality. Without an `API` tag, these should not break existing codes.
#    * `BLD`: Build system changes (`setup.py`, `requirements.txt` etc.)
#    * `TST`: Update tests, code coverage, etc.
#    * `BUG`: Address an issue as filed on the issue tracker.
#    * `BRN`: Start a new branch (see below).
#    * `REL`: Release (see below).
#    * `WIP`: Work in progress.  Do not depend on these!  They will be stripped.  This is useful when testing things like the rendering of documentation on bitbucket etc. where you need to push an incomplete set of files.  Please collapse and strip these eventually when you get things working.
#    * `CHK`: Checkpoints.  These should not be pushed to bitbucket!
# 3. **Tests**: Make sure the tests pass.
#    
#    ```bash
#    conda env update --file environment.yml
#    conda activate _mmfutils; pytest
#    ```
#
#    (`hg com` will automatically run tests after pip-installing everything in `setup.py` if you have linked the `.hgrc` file as discussed above, but the use of independent environments is preferred now.)
# 4. **Update Docs**: Update the documentation if needed.  To generate new documentation run:
#
#    ```bash
#    cd doc
#    sphinx-apidoc -eTE ../mmfutils -o source
#    rm source/mmfutils.*tests*
#    ```
#    
#    * Include any changes at the bottom of this file (`doc/README.ipynb`).
#    * You may need to copy new figures to `README_files/` if the figure numbers have changed, and then `hg add` these while `hg rm` the old ones.
#    
#    Edit any new files created (titles often need to be added) and check that this looks good with
#   
#      ```bash
#      make html
#      open build/html/index.html
#      ```
#      
#    Look especially for errors of the type "WARNING: document isn't included in any toctree".  This indicates that you probably need to add the module to an upper level `.. toctree::`.  Also look for "WARNING: toctree contains reference to document u'...' that doesn't have a title: no link will be generated".  This indicates you need to add a title to a new file.  For example, when I added the `mmf.math.optimize` module, I needed to update the following:
#   
# [comment]: # (The rst generate is mucked up by this indented code block...)
# ```rst
#    .. doc/source/mmfutils.rst
#    mmfutils
#    ========
#    
#    .. toctree::
#        ...
#        mmfutils.optimize
#        ...
# ```   
# ```rst
#    .. doc/source/mmfutils.optimize.rst
#    mmfutils.optimize
#    =================
#        
#    .. automodule:: mmfutils.optimize
#        :members:
#        :undoc-members:
#        :show-inheritance:
# ```
#   
# 5. **Clean up History**: Run `hg histedit`, `hg rebase`, or `hg strip` as needed to clean up the repo before you push.  Branches should generally be linear unless there is an exceptional reason to split development.
# 6. **Release**: First edit `mmfutils/__init__.py` to update the version number by removing the `dev` part of the version number.  Commit only this change and then push only the branch you are working on:
#
#    ```bash
#    hg com -m "REL: <version>"
#    hg push -b .
#    ```
# 7. **Pull Request**: Create a pull request on the development fork from your branch to `default` on the release project bitbucket. Review it, fix anything, then accept the PR and close the branch.
# 8. **Publish on PyPI**: Publish the released version on [PyPI](https://pypi.org/project/mmfutils/) using [twine](https://pypi.org/project/twine/)
#
#    ```bash
#    # Build the package.
#    python setup.py sdist bdist_wheel
#    
#    # Test that everything looks right:
#    twine upload --repository-url https://test.pypi.org/legacy/ dist/*
#    
#    # Upload to PyPI
#    twine upload dist/*
#    ```
#
# 9. **Build Conda Package**: This will run all the tests in a fresh environment as specified by `meta.yaml`.  Make sure that the dependencies in `meta.yaml`, `environment.yml`, and `setup.py` are consistent.  Note that the list of versions to be built is specified in `conda_build_config.yaml`.
#
#    ```bash
#    conda build .
#    conda build . --output   # Use this below
#    anaconda login
#    anaconda upload --all /data/apps/conda/conda-bld/noarch/mmfutils-0.5.0-py_0.tar.bz2
#    ```
#    
# 10. **Start new branch**: On the same development branch (not `default`), increase the version number in `mmfutils/__init__.py` and add `dev`: i.e.:
#
#        __version__ = '0.5.1dev'
#        
#   Then create this branch and commit this:
#   
#        hg branch "0.5.1"
#        hg com -m "BRN: Started branch 0.5.1"
# 11. Update [MyPI](https://bitbucket.org/mforbes/mypi) index.
#
# 12. Optional: Update any `setup.py` files that depend on your new features/fixes etc.

# # Change Log

# ## REL: 0.5.1

# API changes:
# * Split `mmfutils.containers.Object` into `ObjectBase` which is simple and `ObjectMixin` which provides the picking support.  Demonstrate in docs how the pickling can be useful, but slows copying.

# ## REL: 0.5.0

# API changes:
# * Python 3 support only.
# * `mmfutils.math.bases.interface` renamed to `mmfutils.math.bases.interfaces`.
# * Added default class-variable attribute support to e`mmfutils.containers.Object`.
# * Minor enhancements to `mmfutils.math.bases.PeriodicBasis` to enhance GPU support.
# * Added `mmfutils.math.bases.interfaces.IBasisLz` and support in `mmfutils.math.bases.bases.PeriodicBasis` for rotating frames.
# * Cleanup of build environment and tests.
#   * Single environment `_mmfutils` now used for testing and documentation.

# ## REL: 0.4.13

# API changes:
#
# * Use `@implementer()` class decorator rather than `classImplements` or `implements` in all interfaces.
# * Improve `NoInterrupt` context.  Added `NoInterrupt.unregister()`: this allows `NoInterrupt` to work in a notebook cell even when the signal handlers are reset.  (But only works in that one cell.)
# * Added Abel transform `integrate2` to Cylindrical bases.
#
# Issues:
# * Resolved issue #22: Masked arrays work with `imcontourf` etc.
# * Resolved issue #23: `NoInterrupt` works well except in notebooks due to [ipykernel issue #328](https://github.com/ipython/ipykernel/issues/328).
# * Resolved issue #24: Python 3 is now fully supported and tested.

# ## REL: 0.4.10

# API changes:
#
# * Added `contourf`, `error_line`, and `ListCollections` to `mmfutils.plot`.
# * Added Python 3 support (still a couple of issues such as `mmfutils.math.integrate.ssum_inline`.)
# * Added `mmf.math.bases.IBasisKx` and update `lagrangian` in bases to accept `k2` and `kx2` for modified dispersion control (along x).
# * Added `math.special.ellipkinv`.
# * Added some new `mmfutils.math.linalg` tools.
#
# Issues:
#
# * Resolved issue #20: `DyadicSum` and `scipy.optimize.nonlin.Jacobian`
# * Resolved issue #22: imcontourf now respects masked arrays.
# * Resolved issue #24: Support Python 3.
#

# ## REL: 0.4.9

# *< incomplete >*

# ## REL: 0.4.7

# API changes:
#
# * Added `mmfutils.interface.describe_interface()` for inserting interfaces into documentation.
# * Added some DVR basis code to `mmfutils.math.bases`.
# * Added a diverging colormap and some support in `mmfutils.plot`.
# * Added a Wigner Ville distribution computation in `mmfutils.math.wigner`
# * Added `mmfutils.optimize.usolve` and `ubrentq` for finding roots with [`uncertanties`](https://pythonhosted.org/uncertainties/) support.
#
# Issues:
#
# * Resolve issue #8: Use [`ipyparallel`](https://github.com/ipython/ipyparallel) now.
# * Resolve issue #9: Use [pytest](https://pytest.org) rather than `nose` (which is no longer supported).
# * Resolve issue #10: PYFFTW wrappers now support negative `axis` and `axes` arguments.
# * Address issue #11: Preliminary version of some DVR basis classes.
# * Resolve issue #12: Added solvers with [`uncertanties`](https://pythonhosted.org/uncertainties/) support.
