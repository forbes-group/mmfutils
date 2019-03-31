
MMF Utils
=========

Small set of utilities: containers and interfaces.

This package provides some utilities that I tend to rely on during
development. Presently it includes some convenience containers, plotting
tools, and a patch for including
`zope.interface <http://docs.zope.org/zope.interface/>`__ documentation
in a notebook.

(Note: If this file does not render properly, try viewing it through
`nbviewer.org <http://nbviewer.ipython.org/urls/bitbucket.org/mforbes/mmfutils-fork/raw/tip/doc/README.ipynb>`__)

**Documentation:** http://mmfutils.readthedocs.org

**Source:** https://bitbucket.org/mforbes/mmfutils

**Issues:** https://bitbucket.org/mforbes/mmfutils/issues

**Build Status:**

.. raw:: html

   <table>

.. raw:: html

   <tr>

::

    <td>[Main](https://bitbucket.org/mforbes/mmfutils)</td>
    <td>[Fork](https://bitbucket.org/mforbes/mmfutils-fork)</td>

.. raw:: html

   </tr>

.. raw:: html

   <tr>

::

    <td>[![mmfutils Build Status]](https://drone.io/bitbucket.org/mforbes/mmfutils/latest)</td>
    <td>[![mmfutils-fork Build Status]](https://drone.io/bitbucket.org/mforbes/mmfutils-fork/latest)</td>

.. raw:: html

   </tr>

.. raw:: html

   </table>

.. raw:: html

   <h1>

Table of Contents

.. raw:: html

   </h1>

.. raw:: html

   <div class="toc">

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

1  MMF Utils

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

1.1  Installing

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </li>

.. raw:: html

   <li>

2  Usage

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

2.1  Containers

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

2.1.1  Object

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

2.1.1.1  Object Example

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </li>

.. raw:: html

   <li>

2.1.2  Container

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

2.1.2.1  Container Examples

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </li>

.. raw:: html

   <li>

2.2  Contexts

.. raw:: html

   </li>

.. raw:: html

   <li>

2.3  Interfaces

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

2.3.1  Interface Documentation

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </li>

.. raw:: html

   <li>

2.4  Parallel

.. raw:: html

   </li>

.. raw:: html

   <li>

2.5  Performance

.. raw:: html

   </li>

.. raw:: html

   <li>

2.6  Plotting

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

2.6.1  Fast Filled Contour Plots

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </li>

.. raw:: html

   <li>

2.7  Angular Variables

.. raw:: html

   </li>

.. raw:: html

   <li>

2.8  Debugging

.. raw:: html

   </li>

.. raw:: html

   <li>

2.9  Mathematics

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </li>

.. raw:: html

   <li>

3  Developer Instructions

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

3.1  Releases

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </li>

.. raw:: html

   <li>

4  Change Log

.. raw:: html

   <ul class="toc-item">

.. raw:: html

   <li>

4.1  REL: 0.4.10

.. raw:: html

   </li>

.. raw:: html

   <li>

4.2  REL: 0.4.9

.. raw:: html

   </li>

.. raw:: html

   <li>

4.3  REL: 0.4.7

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </li>

.. raw:: html

   </ul>

.. raw:: html

   </div>

Installing
----------

This package can be installed from `from the bitbucket
project <https://bitbucket.org/mforbes/mmfutils>`__:

.. code:: bash

    pip install hg+https://bitbucket.org/mforbes/mmfutils

Usage
=====

Containers
----------

Object
~~~~~~

The ``Object`` object provides a base class to satisfy the following
use-case.

**Serialization and Deferred Initialization:** Consider a problem where
a class is defined through a few parameters, but requires extensive
initialization before it can be properly used. An example is a numerical
simulation where one passes the number of grid points :math:`N` and a
length :math:`L`, but the initialization must generate large grids for
efficient use later on. These grids should not be pickled when the
object is serialized: instead, they should be generated at the end of
initialization. By default, everything in ``__dict__`` will be pickled,
leading to bloated pickles. The solution here is to split initialization
into two steps: ``__init__()`` should initialize everything that is
picklable, then ``init()`` should do any further initialization,
defining the grid points based on the values of the picklable
attributes. To do this, the semantics of the ``__init__()`` method are
changed slightly here. ``Object.__init__()`` registers all keys in
``__dict__`` as ``self.picklable_attributes``. These and only these
attributes will be pickled (through the provided ``__getstate__`` and
``__setstate__`` methods).

The intended use is for subclasses to set and defined all attributes
that should be pickled in the ``__init__()`` method, then call
``Object.__init__(self)``. Any additional initialization can be done
after this call, or in the ``init()`` method (see below) and attributes
defined after this point will be treated as temporary. Note, however,
that unpickling an object will not call ``__init__()`` so any additional
initialization required should be included in the ``init()`` method.

**Deferred initialization via the ``init()`` method:** The idea here is
to defer any expensive initialization – especially that which creates
large temporary data that should not be pickled – until later. This
method is automatically called at the end of ``Object.__init__()`` and
after restoring a pickle. A further use-case is to allow one to change
many parameters, then reinitialize the object once with an explicit call
to ``init()``.

Object Example
^^^^^^^^^^^^^^

.. code:: ipython2

    ROOTDIR = !hg root
    ROOTDIR = ROOTDIR[0]
    import sys;sys.path.insert(0, ROOTDIR)
    
    import numpy as np
    
    from mmfutils.containers import Object
    
    class State(Object):
        def __init__(self, N, L=1.0):
            """This method should set all of the picklable
            parameters, in this case, N and L."""
            print("__init__() called")
            self.N = N
            self.L = L
            
            # Now register these and call init()
            Object.__init__(self)
            
        def init(self):
            """All additional initializations"""
            print("init() called")
            dx = self.L / self.N
            self.x = np.arange(self.N, dtype=float) * dx - self.L/2.0
            self.k = 2*np.pi * np.fft.fftfreq(self.N, dx)
    
            # Set highest momentum to zero if N is even to
            # avoid rapid oscillations
            if self.N % 2 == 0:
                self.k[self.N//2] = 0.0
                
        def compute_derivative(self, f):
            """Return the derivative of f."""        
            return np.fft.ifft(self.k*1j*np.fft.fft(f)).real
    
    s = State(256)
    print s


.. parsed-literal::

    __init__() called
    init() called
    State(L=1.0, N=256)


One feature is that a nice ``repr()`` of the object is produced. Now
let's do a calculation:

.. code:: ipython2

    f = np.exp(3*np.cos(2*np.pi*s.x/s.L)) / 15
    df = -2.*np.pi/5.*np.exp(3*np.cos(2*np.pi*s.x/s.L))*np.sin(2*np.pi*s.x/s.L)/s.L
    np.allclose(s.compute_derivative(f), df)




.. parsed-literal::

    True



Here we demonstrate pickling. Note that the pickle is very small, and
when unpickled, ``init()`` is called to re-establish ``s.x`` and
``s.k``.

.. code:: ipython2

    import pickle
    s_repr = pickle.dumps(s)
    print(len(s_repr))
    s1 = pickle.loads(s_repr)


.. parsed-literal::

    169
    init() called


Another use case applies when ``init()`` is expensive. If :math:`x` and
:math:`k` were computed in ``__init__()``, then using properties to
change both :math:`N` and :math:`L` would trigger two updates. Here we
do the updates, then call ``init()``. Good practice is to call
``init()`` automatically before any serious calculation to ensure that
the object is brought up to date before the computation.

.. code:: ipython2

    s.N = 64
    s.L = 2.0
    s.init()


.. parsed-literal::

    init() called


Finally, we demonstrate that ``Object`` instances can be archived using
the ``persist`` package:

.. code:: ipython2

    import persist.archive;reload(persist.archive)
    a = persist.archive.Archive(check_on_insert=True)
    a.insert(s=s)
    
    d = {}
    exec str(a) in d
    
    d['s']


.. parsed-literal::

    __init__() called
    init() called




.. parsed-literal::

    State(L=2.0, N=64)



Container
~~~~~~~~~

The ``Container`` object is a slight extension of ``Object`` that
provides a simple container for storing data with attribute and
iterative access. These implement some of the `Collections Abstract Base
Classes from the python standard
library <https://docs.python.org/2/library/collections.html#collections-abstract-base-classes>`__.
The following containers are provided:

-  ``Container``: Bare-bones container extending the ``Sized``,
   ``Iterable``, and ``Container`` abstract ase classes (ABCs) from the
   standard ``containers`` library.
-  ``ContainerList``: Extension that acts like a tuple/list satisfying
   the ``Sequence`` ABC from the ``containers`` library (but not the
   ``MutableSequence`` ABC. Although we allow setting and deleting
   items, we do not provide a way for insertion, which breaks this
   interface.)
-  ``ContainerDict``: Extension that acts like a dict satisfying the
   ``MutableMapping`` ABC from the ``containers`` library.

These were designed with the following use cases in mind:

-  Returning data from a function associating names with each data. The
   resulting ``ContainerList`` will act like a tuple, but will support
   attribute access. Note that the order will be lexicographic. One
   could use a dictionary, but attribute access with tab completion is
   much nicer in an interactive session. The ``containers.nametuple``
   generator could also be used, but this is somewhat more complicated
   (though might be faster). Also, named tuples are immutable - here we
   provide a mutable object that is picklable etc. The choice between
   ``ContainerList`` and ``ContainerDict`` will depend on subsequent
   usage. Containers can be converted from one type to another.

Container Examples
^^^^^^^^^^^^^^^^^^

.. code:: ipython2

    from mmfutils.containers import Container
    
    c = Container(a=1, c=2, b='Hi there')
    print c
    print tuple(c)


.. parsed-literal::

    Container(a=1, b='Hi there', c=2)
    (1, 'Hi there', 2)


.. code:: ipython2

    # Attributes are mutable
    c.b = 'Ho there'
    print c


.. parsed-literal::

    Container(a=1, b='Ho there', c=2)


.. code:: ipython2

    # Other attributes can be used for temporary storage but will not be pickled.
    import numpy as np
    
    c.large_temporary_array = np.ones((256,256))
    print c
    print c.large_temporary_array


.. parsed-literal::

    Container(a=1, b='Ho there', c=2)
    [[ 1.  1.  1. ...,  1.  1.  1.]
     [ 1.  1.  1. ...,  1.  1.  1.]
     [ 1.  1.  1. ...,  1.  1.  1.]
     ..., 
     [ 1.  1.  1. ...,  1.  1.  1.]
     [ 1.  1.  1. ...,  1.  1.  1.]
     [ 1.  1.  1. ...,  1.  1.  1.]]


.. code:: ipython2

    import pickle
    c1 = pickle.loads(pickle.dumps(c))
    print c1
    c1.large_temporary_array


.. parsed-literal::

    Container(a=1, b='Ho there', c=2)


::


    ---------------------------------------------------------------------------

    AttributeError                            Traceback (most recent call last)

    <ipython-input-9-c6cad315ac19> in <module>()
          2 c1 = pickle.loads(pickle.dumps(c))
          3 print c1
    ----> 4 c1.large_temporary_array
    

    AttributeError: 'Container' object has no attribute 'large_temporary_array'


Contexts
--------

The ``mmfutils.contexts`` module provides two useful contexts:

``NoInterrupt``: This can be used to susspend ``KeyboardInterrupt``
exceptions until they can be dealt with at a point that is convenient. A
typical use is when performing a series of calculations in a loop. By
placing the loop in a ``NoInterrupt`` context, one can avoid an
interrupt from ruining a calculation:

.. code:: ipython2

    from mmfutils.contexts import NoInterrupt
    
    complete = False
    n = 0
    with NoInterrupt() as interrupted:
        while not complete and not interrupted:
            n += 1
            if n > 10:
                complete = True

Note: One can nest ``NoInterrupt`` contexts so that outer loops are also
interrupted.

Interfaces
----------

The interfaces module collects some useful
`zope.interface <http://docs.zope.org/zope.interface/>`__ tools for
checking interface requirements. Interfaces provide a convenient way of
communicating to a programmer what needs to be done to used your code.
This can then be checked in tests.

.. code:: ipython2

    from mmfutils.interface import Interface, Attribute, verifyClass, verifyObject, implements
    
    class IAdder(Interface):
        """Interface for objects that support addition."""
    
        value = Attribute('value', "Current value of object")
    
        # No self here since this is the "user" interface
        def add(other):
            """Return self + other."""

Here is a broken implementation. We muck up the arguments to ``add``:

.. code:: ipython2

    class AdderBroken(object):
        implements(IAdder)
        
        def add(self, one, another):
            # There should only be one argument!
            return one + another
    
    try:
        verifyClass(IAdder, AdderBroken)
    except Exception, e:
        print("{0.__class__.__name__}: {0}".format(e))
        


.. parsed-literal::

    BrokenMethodImplementation: The implementation of add violates its contract
            because implementation requires too many arguments.
            


Now we get ``add`` right, but forget to define ``value``. This is only
caught when we have an object since the attribute is supposed to be
defined in ``__init__()``:

.. code:: ipython2

    class AdderBroken(object):
        implements(IAdder)
        
        def add(self, other):
            return one + other
    
    # The class validates...
    verifyClass(IAdder, AdderBroken)
    
    # ... but objects are missing the value Attribute
    try:
        verifyObject(IAdder, AdderBroken())
    except Exception, e:
        print("{0.__class__.__name__}: {0}".format(e))    


.. parsed-literal::

    BrokenImplementation: An object has failed to implement interface <InterfaceClass __main__.IAdder>
    
            The value attribute was not provided.
            


Finally, a working instance:

.. code:: ipython2

    class Adder(object):
        implements(IAdder)
        def __init__(self, value=0):
            self.value = value
        def add(self, other):
            return one + other
        
    verifyClass(IAdder, Adder) and verifyObject(IAdder, Adder())




.. parsed-literal::

    True



Interface Documentation
~~~~~~~~~~~~~~~~~~~~~~~

We also monkeypatch ``zope.interface.documentation.asStructuredText()``
to provide a mechanism for documentating interfaces in a notebook.

.. code:: ipython2

    from mmfutils.interface import describe_interface
    describe_interface(IAdder)




.. raw:: html

    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="generator" content="Docutils 0.14: http://docutils.sourceforge.net/" />
    <title>&lt;string&gt;</title>
    
    <div class="document">
    
    
    <p><tt class="docutils literal">IAdder</tt></p>
    <blockquote>
    <p>Interface for objects that support addition.</p>
    <p>Attributes:</p>
    <blockquote>
    <tt class="docutils literal">value</tt> -- Current value of object</blockquote>
    <p>Methods:</p>
    <blockquote>
    <tt class="docutils literal">add(other)</tt> -- Return self + other.</blockquote>
    </blockquote>
    </div>




Parallel
--------

The ``mmfutils.parallel`` module provides some tools for launching and
connecting to IPython clusters. The ``parallel.Cluster`` class
represents and controls a cluster. The cluster is specified by the
profile name, and can be started or stopped from this class:

.. code:: ipython2

    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    import numpy as np
    from mmfutils import parallel
    cluster = parallel.Cluster(profile='default', n=3, sleep_time=1.0)
    cluster.start()
    cluster.wait()  # Instance of IPython.parallel.Client
    view = cluster.load_balanced_view
    x = np.linspace(-6,6, 100)
    y = view.map(lambda x:x**2, x)
    print np.allclose(y, x**2)
    cluster.stop()


.. parsed-literal::

    Waiting for connection file: ~/.ipython/profile_default/security/ipcontroller-client.json


.. parsed-literal::

    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=default --n=3


.. parsed-literal::

    Waiting for connection file: ~/.ipython/profile_default/security/ipcontroller-client.json


.. parsed-literal::

    INFO:root:waiting for 3 engines
    INFO:root:0 of 3 running
    INFO:root:3 of 3 running
    INFO:root:Stopping cluster: ipcluster stop --profile=default


.. parsed-literal::

    True
    Waiting for connection file: ~/.ipython/profile_default/security/ipcontroller-client.json


If you only need a cluster for a single task, it can be managed with a
context. Be sure to wait for the result to be computed before exiting
the context and shutting down the cluster!

.. code:: ipython2

    with parallel.Cluster(profile='default', n=3, sleep_time=1.0) as client:
        view = client.load_balanced_view
        x = np.linspace(-6,6, 100)
        y = view.map(lambda x:x**2, x, block=True)  # Make sure to wait for the result!
    print np.allclose(y, x**2)


.. parsed-literal::

    Waiting for connection file: ~/.ipython/profile_default/security/ipcontroller-client.json


.. parsed-literal::

    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=default --n=3


.. parsed-literal::

    Waiting for connection file: ~/.ipython/profile_default/security/ipcontroller-client.json


.. parsed-literal::

    INFO:root:waiting for 3 engines
    INFO:root:0 of 3 running
    INFO:root:3 of 3 running
    INFO:root:Stopping cluster: ipcluster stop --profile=default


.. parsed-literal::

    Waiting for connection file: ~/.ipython/profile_default/security/ipcontroller-client.json
    True


If you just need to connect to a running cluster, you can use
``parallel.get_client()``.

Performance
-----------

The ``mmfutils.performance`` module provides some tools for high
performance computing. Note: this module requires some additional
packages including
`numexp <https://github.com/pydata/numexpr/wiki/Numexpr-Users-Guide>`__,
`pyfftw <http://hgomersall.github.io/pyFFTW/>`__, and the ``mkl``
package installed by anaconda. Some of these require building system
libraries (i.e. the `FFTW <http://www.fftw.org>`__). However, the
various components will not be imported by default.

Here is a brief description of the components:

-  ``mmfutils.performance.blas``: Provides an interface to a few of the
   scipy BLAS wrappers. Very incomplete (only things I currently need).
-  ``mmfutils.performance.fft``: Provides an interface to the
   `FFTW <http://www.fftw.org>`__ using ``pyfftw`` if it is available.
   Also enables the planning cache and setting threads so you can better
   control your performance.
-  ``mmfutils.performance.numexpr``: Robustly imports numexpr and
   disabling the VML. (If you don't do this carefully, it will crash
   your program so fast you won't even get a traceback.)
-  ``mmfutils.performance.threads``: Provides some hooks for setting the
   maximum number of threads in a bunch of places including the MKL,
   numexpr, and fftw.

Plotting
--------

Several tools are provided in ``mmfutils.plot``:

Fast Filled Contour Plots
~~~~~~~~~~~~~~~~~~~~~~~~~

``mmfutils.plot.imcontourf`` is similar to matplotlib's ``plt.contourf``
function, but uses ``plt.imshow`` which is much faster. This is useful
for animations and interactive work. It also supports my idea of saner
array-shape processing (i.e. if ``x`` and ``y`` have different shapes,
then it will match these to the shape of ``z``). Matplotlib now provies
``plt.pcolourmesh`` which is similar, but has the same interface issues.

.. code:: ipython2

    %matplotlib inline
    from matplotlib import pyplot as plt
    import time
    import numpy as np
    from mmfutils import plot as mmfplt
    x = np.linspace(-1, 1, 100)[:, None]**3
    y = np.linspace(-0.1, 0.1, 200)[None, :]**3
    z = np.sin(10*x)*y**2
    plt.figure(figsize=(12,3))
    plt.subplot(141)
    %time mmfplt.imcontourf(x, y, z, cmap='gist_heat')
    plt.subplot(142)
    %time plt.contourf(x.ravel(), y.ravel(), z.T, 50, cmap='gist_heat')
    plt.subplot(143)
    %time plt.pcolor(x.ravel(), y.ravel(), z.T, cmap='gist_heat')
    plt.subplot(144)
    %time plt.pcolormesh(x.ravel(), y.ravel(), z.T, cmap='gist_heat')


.. parsed-literal::

    CPU times: user 9.77 ms, sys: 50 µs, total: 9.82 ms
    Wall time: 9.86 ms
    CPU times: user 43.5 ms, sys: 1.19 ms, total: 44.6 ms
    Wall time: 44.7 ms
    CPU times: user 426 ms, sys: 34.1 ms, total: 460 ms
    Wall time: 450 ms
    CPU times: user 2.39 ms, sys: 346 µs, total: 2.73 ms
    Wall time: 2.74 ms




.. parsed-literal::

    <matplotlib.collections.QuadMesh at 0x1209acd10>




.. image:: README_files/README_54_2.png


Angular Variables
-----------------

A couple of tools are provided to visualize angular fields, such as the
phase of a complex wavefunction.

.. code:: ipython2

    %matplotlib inline
    from matplotlib import pyplot as plt
    import time
    import numpy as np
    from mmfutils import plot as mmfplt;reload(mmfplt)
    x = np.linspace(-1, 1, 100)[:, None]
    y = np.linspace(-1, 1, 200)[None, :]
    z = x + 1j*y
    
    plt.figure(figsize=(9,2))
    plt.subplot(131).set_aspect(1)
    mmfplt.phase_contour(x, y, z, aspect=1, colors='k', linewidths=0.5)
    
    # This is a little slow but allows you to vary the luminosity.
    plt.subplot(132).set_aspect(1)
    mmfplt.imcontourf(x, y, mmfplt.colors.color_complex(z), aspect=1)
    mmfplt.phase_contour(x, y, z, aspect=1, linewidths=0.5)
    
    # This is faster if you just want to show the phase and allows
    # for a colorbar via a registered colormap
    plt.subplot(133).set_aspect(1)
    mmfplt.imcontourf(x, y, np.angle(z), cmap='huslp', aspect=1)
    plt.colorbar()
    mmfplt.phase_contour(x, y, z, aspect=1, linewidths=0.5)




.. parsed-literal::

    (<matplotlib.contour.QuadContourSet at 0x11558d8d0>,
     <matplotlib.contour.QuadContourSet at 0x115630b10>)




.. image:: README_files/README_57_1.png


Debugging
---------

A couple of debugging tools are provided. The most useful is the
``debug`` decorator which will store the local variables of a function
in a dictionary or in your global scope.

.. code:: ipython2

    from mmfutils.debugging import debug
    
    @debug(locals())
    def f(x):
        y = x**1.5
        z = 2/x
        return z
    
    print(f(2.0), x, y, z)


.. parsed-literal::

    (1.0, 2.0, 2.8284271247461903, 1.0)


Mathematics
-----------

We include a few mathematical tools here too. In particular, numerical
integration and differentiation. Check the API documentation for
details.

Developer Instructions
======================

If you are a developer of this package, there are a few things to be
aware of.

1. If you modify the notebooks in ``docs/notebooks`` then you may need
   to regenerate some of the ``.rst`` files and commit them so they
   appear on bitbucket. This is done automatically by the ``pre-commit``
   hook in ``.hgrc`` if you include this in your ``.hg/hgrc`` file with
   a line like:

   ::

       %include ../.hgrc

**Security Warning:** if you do this, be sure to inspect the ``.hgrc``
file carefully to make sure that no one inserts malicious code.

This runs the following code:

.. code:: ipython2

    !cd $ROOTDIR; jupyter nbconvert --to=rst --output=README.rst doc/README.ipynb


.. parsed-literal::

    [NbConvertApp] Converting notebook doc/README.ipynb to rst
    [NbConvertApp] Support files will be in README_files/
    [NbConvertApp] Making directory README_files
    [NbConvertApp] Making directory README_files
    [NbConvertApp] Writing 29492 bytes to README.rst


We also run a comprehensive set of tests, and the pre-commit hook will
fail if any of these do not pass, or if we don't have complete code
coverage. This uses
`nosetests <https://nose.readthedocs.org/en/latest/>`__ and
`flake8 <http://flake8.readthedocs.org>`__. To run individal tests do
one of:

.. code:: bash

    python setup.py nosetests
    python setup.py flake8
    python setup.py check
    python setup.py test   # This runs them all using a custom command defined in setup.py

Here is an example:

.. code:: ipython2

    !cd $ROOTDIR; python setup.py test


.. parsed-literal::

    /data/apps/anaconda/envs/work/lib/python2.7/site-packages/setuptools-19.1.1-py2.7.egg/setuptools/dist.py:284: UserWarning: Normalizing '0.4.7dev' to '0.4.7.dev0'
    running test
    running nosetests
    running egg_info
    writing requirements to mmfutils.egg-info/requires.txt
    writing mmfutils.egg-info/PKG-INFO
    writing top-level names to mmfutils.egg-info/top_level.txt
    writing dependency_links to mmfutils.egg-info/dependency_links.txt
    reading manifest file 'mmfutils.egg-info/SOURCES.txt'
    writing manifest file 'mmfutils.egg-info/SOURCES.txt'
    nose.config: INFO: Set working dir to /Users/mforbes/work/mmfbb/mmfutils
    nose.config: INFO: Ignoring files matching ['^\\.', '^_', '^setup\\.py$']
    nose.plugins.cover: INFO: Coverage report will include only packages: ['mmfutils']
    INFO:root:Patching zope.interface.document.asStructuredText to format code
    INFO:root:Patching flake8 for issues 39 and 40
    Doctest: mmfutils.containers.Container ... ok
    Doctest: mmfutils.containers.ContainerDict ... ok
    Doctest: mmfutils.containers.ContainerList ... ok
    Doctest: mmfutils.containers.Object ... ok
    Doctest: mmfutils.debugging.debug ... ok
    Doctest: mmfutils.debugging.persistent_locals ... ok
    Doctest: mmfutils.interface.describe_interface ... ok
    Doctest: mmfutils.math.differentiate.differentiate ... ok
    Doctest: mmfutils.math.differentiate.hessian ... ok
    Test the Richardson extrapolation for the correct scaling behaviour. ... ok
    Doctest: mmfutils.math.integrate.Richardson ... ok
    Doctest: mmfutils.math.integrate.exact_add ... ok
    Doctest: mmfutils.math.integrate.exact_sum ... ok
    Doctest: mmfutils.math.integrate.mquad ... /Users/mforbes/work/mmfbb/mmfutils/mmfutils/math/integrate/__init__.py:1: RuntimeWarning: divide by zero encountered in double_scalars
      """Integration Utilities.
    WARNING:root:mquad:MinStepSize: Minimum step size reached. (5.94368304574e-19 < 6.50521303491e-19) Singularity possible (err = 0.0).
    WARNING:root:mquad:MinStepSize: Minimum step size reached. (5.94368304574e-19 < 6.50521303491e-19) Singularity possible (err = 1.98122768191e-19).
    ok
    Doctest: mmfutils.math.integrate.quad ... ok
    Doctest: mmfutils.math.integrate.rsum ... ok
    Doctest: mmfutils.math.integrate.ssum_inline ... ok
    Doctest: mmfutils.math.integrate.ssum_python ... ok
    Test directional first derivatives ... ok
    Test directional second derivatives ... ok
    Doctest: mmfutils.optimize.bracket_monotonic ... ok
    Doctest: mmfutils.performance.fft.resample ... ok
    Doctest: mmfutils.performance.numexpr ... ok
    mmfutils.tests.test_containers.TestContainer.test_container_delattr ... ok
    Test persistent representation of object class ... ok
    Check that the order of attributes defined by ... ok
    mmfutils.tests.test_containers.TestContainerConversion.test_conversions ... ok
    mmfutils.tests.test_containers.TestContainerDict.test_container_del ... ok
    mmfutils.tests.test_containers.TestContainerDict.test_container_setitem ... ok
    mmfutils.tests.test_containers.TestContainerList.test_container_delitem ... ok
    mmfutils.tests.test_containers.TestObject.test_empty_object ... ok
    Test persistent representation of object class ... ok
    mmfutils.tests.test_containers.TestPersist.test_archive ... ok
    Doctest: mmfutils.tests.test_containers.Issue4 ... ok
    mmfutils.tests.test_debugging.TestCoverage.test_coverage_1 ... ok
    mmfutils.tests.test_debugging.TestCoverage.test_coverage_2 ... ok
    mmfutils.tests.test_debugging.TestCoverage.test_coverage_3 ... ok
    mmfutils.tests.test_debugging.TestCoverage.test_coverage_exception ... ok
    Test 3rd order differentiation ... ok
    mmfutils.tests.test_interface.TestInterfaces.test_verifyBrokenClass ... ok
    mmfutils.tests.test_interface.TestInterfaces.test_verifyBrokenObject1 ... ok
    mmfutils.tests.test_interface.TestInterfaces.test_verifyBrokenObject2 ... ok
    mmfutils.tests.test_interface.TestInterfaces.test_verifyClass ... ok
    mmfutils.tests.test_interface.TestInterfaces.test_verifyObject ... ok
    Doctest: mmfutils.tests.test_interface.Doctests ... ok
    mmfutils.tests.test_monkeypatchs.TestCoverage.test_cover_monkeypatchs ... INFO:root:Patching flake8 for issues 39 and 40
    ok
    mmfutils.tests.test_monkeypatchs.TestCoverage.test_flake8_patch_err ... INFO:root:Patching flake8 for issues 39 and 40
    ok
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmp9itx0A/profile_testing/ipython_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmp9itx0A/profile_testing/ipython_kernel_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmp9itx0A/profile_testing/ipcontroller_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmp9itx0A/profile_testing/ipengine_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmp9itx0A/profile_testing/ipcluster_config.py'
    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=testing1 --n=7 --ipython-dir="/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmp9itx0A"
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    INFO:root:waiting for 1 engines
    INFO:root:0 of 1 running
    INFO:root:7 of 1 running
    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=testing_pbs --n=3 --ipython-dir="/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmp9itx0A"
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    INFO:root:waiting for 1 engines
    INFO:root:0 of 1 running
    INFO:root:3 of 1 running
    Simple test connecting to a cluster. ... INFO:root:waiting for 1 engines
    INFO:root:7 of 1 running
    ok
    Test deleting of cluster objects ... ok
    Test that starting a running cluster does nothing. ... ok
    Test that the PBS_NODEFILE is used if defined ... INFO:root:waiting for 1 engines
    INFO:root:3 of 1 running
    INFO:root:waiting for 3 engines
    INFO:root:3 of 3 running
    INFO:root:Stopping cluster: ipcluster stop --profile=testing_pbs --ipython-dir="/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmp9itx0A"
    2016-01-05 12:16:55.566 [IPClusterStop] Stopping cluster [pid=17497] with [signal=2]
    ok
    Test timeout (coverage) ... ok
    mmfutils.tests.test_parallel.TestCluster.test_views ... DEBUG:root:Importing canning map
    ok
    INFO:root:Stopping cluster: ipcluster stop --profile=testing1 --ipython-dir="/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmp9itx0A"
    2016-01-05 12:16:56.330 [IPClusterStop] Stopping cluster [pid=17461] with [signal=2]
    mmfutils.tests.test_performance_blas.Test_BLAS.test_daxpy ... ok
    mmfutils.tests.test_performance_blas.Test_BLAS.test_ddot ... ok
    mmfutils.tests.test_performance_blas.Test_BLAS.test_dnorm ... ok
    mmfutils.tests.test_performance_blas.Test_BLAS.test_zaxpy ... ok
    mmfutils.tests.test_performance_blas.Test_BLAS.test_zdotc ... ok
    mmfutils.tests.test_performance_blas.Test_BLAS.test_znorm ... ok
    mmfutils.tests.test_performance_fft.Test_FFT.test_fft ... ok
    mmfutils.tests.test_performance_fft.Test_FFT.test_fftn ... ok
    mmfutils.tests.test_performance_fft.Test_FFT_pyfftw.test_fft ... ok
    mmfutils.tests.test_performance_fft.Test_FFT_pyfftw.test_fft_pyfftw ... ok
    mmfutils.tests.test_performance_fft.Test_FFT_pyfftw.test_fftn ... ok
    mmfutils.tests.test_performance_fft.Test_FFT_pyfftw.test_fftn_pyfftw ... ok
    mmfutils.tests.test_performance_fft.Test_FFT_pyfftw.test_get_fft_pyfftw ... ok
    mmfutils.tests.test_performance_fft.Test_FFT_pyfftw.test_get_fftn_pyfftw ... ok
    mmfutils.tests.test_performance_threads.TestThreads.test_hook_mkl ... ok
    mmfutils.tests.test_performance_threads.TestThreads.test_hooks_fft ... ok
    mmfutils.tests.test_performance_threads.TestThreads.test_hooks_numexpr ... ok
    mmfutils.tests.test_performance_threads.TestThreads.test_set_threads_fft ... ok
    mmfutils.tests.test_performance_threads.TestThreads.test_set_threads_mkl ... ok
    mmfutils.tests.test_performance_threads.TestThreads.test_set_threads_numexpr ... ok
    
    Name                           Stmts   Miss  Cover   Missing
    ------------------------------------------------------------
    mmfutils                           1      0   100%   
    mmfutils.containers               85      0   100%   
    mmfutils.debugging                47      0   100%   
    mmfutils.interface                70      0   100%   
    mmfutils.math                      0      0   100%   
    mmfutils.math.differentiate       61      0   100%   
    mmfutils.math.integrate          193      0   100%   
    mmfutils.monkeypatches            14      0   100%   
    mmfutils.optimize                 13      0   100%   
    mmfutils.parallel                124      2    98%   15-16
    mmfutils.performance               0      0   100%   
    mmfutils.performance.blas         58      0   100%   
    mmfutils.performance.fft          61      0   100%   
    mmfutils.performance.numexpr      10      0   100%   
    mmfutils.performance.threads      10      0   100%   
    ------------------------------------------------------------
    TOTAL                            747      2    99%   
    ----------------------------------------------------------------------
    Ran 73 tests in 19.302s
    
    OK


Complete code coverage information is provided in
``build/_coverage/index.html``.

.. code:: ipython2

    from IPython.display import HTML
    with open(os.path.join(ROOTDIR, 'build/_coverage/index.html')) as f:
        coverage = f.read()
    HTML(coverage)




.. raw:: html

    <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
    <html>
    <head>
        <meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
        <title>Coverage report</title>
        <link rel='stylesheet' href='style.css' type='text/css'>
        
        <script type='text/javascript' src='jquery.min.js'></script>
        <script type='text/javascript' src='jquery.tablesorter.min.js'></script>
        <script type='text/javascript' src='jquery.hotkeys.js'></script>
        <script type='text/javascript' src='coverage_html.js'></script>
        <script type='text/javascript' charset='utf-8'>
            jQuery(document).ready(coverage.index_ready);
        </script>
    </head>
    <body id='indexfile'>
    
    <div id='header'>
        <div class='content'>
            <h1>Coverage report:
                <span class='pc_cov'>99%</span>
            </h1>
            <img id='keyboard_icon' src='keybd_closed.png'>
        </div>
    </div>
    
    <div class='help_panel'>
        <img id='panel_icon' src='keybd_open.png'>
        <p class='legend'>Hot-keys on this page</p>
        <div>
        <p class='keyhelp'>
            <span class='key'>n</span>
            <span class='key'>s</span>
            <span class='key'>m</span>
            <span class='key'>x</span>
            
            <span class='key'>c</span> &nbsp; change column sorting
        </p>
        </div>
    </div>
    
    <div id='index'>
        <table class='index'>
            <thead>
                
                <tr class='tablehead' title='Click to sort'>
                    <th class='name left headerSortDown shortkey_n'>Module</th>
                    <th class='shortkey_s'>statements</th>
                    <th class='shortkey_m'>missing</th>
                    <th class='shortkey_x'>excluded</th>
                    
                    <th class='right shortkey_c'>coverage</th>
                </tr>
            </thead>
            
            <tfoot>
                <tr class='total'>
                    <td class='name left'>Total</td>
                    <td>747</td>
                    <td>2</td>
                    <td>71</td>
                    
                    <td class='right'>99%</td>
                </tr>
            </tfoot>
            <tbody>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils.html'>mmfutils</a></td>
                    <td>1</td>
                    <td>0</td>
                    <td>0</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_containers.html'>mmfutils.containers</a></td>
                    <td>85</td>
                    <td>0</td>
                    <td>0</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_debugging.html'>mmfutils.debugging</a></td>
                    <td>47</td>
                    <td>0</td>
                    <td>3</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_interface.html'>mmfutils.interface</a></td>
                    <td>70</td>
                    <td>0</td>
                    <td>14</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_math.html'>mmfutils.math</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_math_differentiate.html'>mmfutils.math.differentiate</a></td>
                    <td>61</td>
                    <td>0</td>
                    <td>0</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_math_integrate.html'>mmfutils.math.integrate</a></td>
                    <td>193</td>
                    <td>0</td>
                    <td>16</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_monkeypatches.html'>mmfutils.monkeypatches</a></td>
                    <td>14</td>
                    <td>0</td>
                    <td>4</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_optimize.html'>mmfutils.optimize</a></td>
                    <td>13</td>
                    <td>0</td>
                    <td>0</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_parallel.html'>mmfutils.parallel</a></td>
                    <td>124</td>
                    <td>2</td>
                    <td>8</td>
                    
                    <td class='right'>98%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_performance.html'>mmfutils.performance</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_performance_blas.html'>mmfutils.performance.blas</a></td>
                    <td>58</td>
                    <td>0</td>
                    <td>6</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_performance_fft.html'>mmfutils.performance.fft</a></td>
                    <td>61</td>
                    <td>0</td>
                    <td>5</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_performance_numexpr.html'>mmfutils.performance.numexpr</a></td>
                    <td>10</td>
                    <td>0</td>
                    <td>7</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_performance_threads.html'>mmfutils.performance.threads</a></td>
                    <td>10</td>
                    <td>0</td>
                    <td>8</td>
                    
                    <td class='right'>100%</td>
                </tr>
                
            </tbody>
        </table>
    </div>
    
    <div id='footer'>
        <div class='content'>
            <p>
                <a class='nav' href='http://nedbatchelder.com/code/coverage'>coverage.py v3.7.1</a>
            </p>
        </div>
    </div>
    
    </body>
    </html>




Releases
--------

We try to keep the repository clean with the following properties:

1. The default branch is stable: i.e. if someone runs ``hg clone``, this
   will pull the latest stable release.
2. Each release has its own named branch so that e.g. ``hg up 0.4.6``
   will get the right thing. Note: this should update to the development
   branch, *not* the default branch so that any work committed will not
   pollute the development branch (which would violate the previous
   point).

To do this, we advocate the following proceedure.

1. **Update to Correct Branch**: Make sure this is the correct
   development branch, not the default branch by explicitly updating:

``bash    hg up <version>``

(Compare with ``hg up default`` which should take you to the default
branch instead.) 2. **Work**: Do your work, committing as required with
messages as shown in the repository with the following keys:

-  ``DOC``: Documentation changes.
-  ``API``: Changes to the exising API. This could break old code.
-  ``EHN``: Enhancement or new functionality. Without an ``API`` tag,
   these should not break existing codes.
-  ``BLD``: Build system changes (``setup.py``, ``requirements.txt``
   etc.)
-  ``TST``: Update tests, code coverage, etc.
-  ``BUG``: Address an issue as filed on the issue tracker.
-  ``BRN``: Start a new branch (see below).
-  ``REL``: Release (see below).
-  ``WIP``: Work in progress. Do not depend on these! They will be
   stripped. This is useful when testing things like the rendering of
   documentation on bitbucket etc. where you need to push an incomplete
   set of files. Please collapse and strip these eventually when you get
   things working.
-  ``CHK``: Checkpoints. These should not be pushed to bitbucket!

3. **Tests**: Make sure the tests pass. Do do this you should run the
   tests in both the ``_test2`` and ``_test3`` environments:

``bash    conda env update --file environment._test2.yml  # If needed    conda env update --file environment._test3.yml  # If needed    conda activate _test2; py.test    conda activate _test3; py.test``

(``hg com`` will automatically run tests after pip-installing everything
in ``setup.py`` if you have linked the ``.hgrc`` file as discussed
above, but the use of independent environments is preferred now.) 4.
**Update Docs**: Update the documentation if needed. To generate new
documentation run:

``bash    cd doc    sphinx-apidoc -eTE ../mmfutils -o source    rm source/mmfutis.tests.*``

Include any changes at the bottom of this file (``doc/README.ipynb``).

Edit any new files created (titles often need to be added) and check
that this looks good with

::

     ```bash
     make html
     open build/html/index.html
     ```
     

Look especially for errors of the type "WARNING: document isn't included
in any toctree". This indicates that you probably need to add the module
to an upper level ``.. toctree::``. Also look for "WARNING: toctree
contains reference to document u'...' that doesn't have a title: no link
will be generated". This indicates you need to add a title to a new
file. For example, when I added the ``mmf.math.optimize`` module, I
needed to update the following:

.. code:: rst

       .. doc/source/mmfutils.rst
       mmfutils
       ========
       
       .. toctree::
           ...
           mmfutils.optimize
           ...

.. code:: rst

       .. doc/source/mmfutils.optimize.rst
       mmfutils.optimize
       =================
           
       .. automodule:: mmfutils.optimize
           :members:
           :undoc-members:
           :show-inheritance:

5. **Clean up History**: Run ``hg histedit``, ``hg rebase``, or
   ``hg strip`` as needed to clean up the repo before you push. Branches
   should generally be linear unless there is an exceptional reason to
   split development.
6. **Release**: First edit ``mmfutils/__init__.py`` and update the
   version number by removing the ``dev`` part of the version number.
   Commit only this change and then push only the branch you are working
   on:

``bash    hg com -m "REL: <version>"    hg push -b .`` 7. **Pull
Request**: Create a pull request on the development fork from your
branch to ``default`` on the release project bitbucket. Review it, fix
anything, then accept the PR and close the branch. 8. **Publish on
PyPI**: Publish the released version on
`PyPI <https://pypi.org/project/mmfutils/>`__ using
`twine <https://pypi.org/project/twine/>`__

\`\`\`bash # Build the package. python setup.py sdist bdist\_wheel

# Test that everything looks right: twine upload --repository-url
https://test.pypi.org/legacy/ dist/\*

# Upload to PyPI twine upload dist/\* \`\`\`

9. **Start new branch**: On the same development branch (not
   ``default``), increase the version number in ``mmfutils/__init__.py``
   and add ``dev``: i.e.:

   **version** = '0.4.7dev'

Then create this branch and commit this:

::

       hg branch "0.4.7"
       hg com -m "BRN: Started branch 0.4.7"

10. Update `MyPI <https://bitbucket.org/mforbes/mypi>`__ index.

11. Optional: Update any ``setup.py`` files that depend on your new
    features/fixes etc.

Change Log
==========

REL: 0.4.10
-----------

API changes:

-  Added ``contourf``, ``error_line``, and ``ListCollections`` to
   ``mmfutils.plot``.
-  Added Python 3 support (still a couple of issues such as
   ``mmfutils.math.integrate.ssum_inline``.)
-  Added ``mmf.math.bases.IBasisKx`` and update ``lagrangian`` in bases
   to accept ``k2`` and ``kx2`` for modified dispersion control (along
   x).
-  Added ``math.special.ellipkinv``.
-  Added some new ``mmfutils.math.linalg`` tools.

Issues:

-  Resolved issue #20: ``DyadicSum`` and
   ``scipy.optimize.nonlin.Jacobian``
-  Resolved issue #22: imcontourf now respects masked arrays.
-  Resolved issue #24: Support Python 3.

REL: 0.4.9
----------

*< incomplete >*

REL: 0.4.7
----------

API changes:

-  Added ``mmfutils.interface.describe_interface()`` for inserting
   interfaces into documentation.
-  Added some DVR basis code to ``mmfutils.math.bases``.
-  Added a diverging colormap and some support in ``mmfutils.plot``.
-  Added a Wigner Ville distribution computation in
   ``mmfutils.math.wigner``
-  Added ``mmfutils.optimize.usolve`` and ``ubrentq`` for finding roots
   with ```uncertanties`` <https://pythonhosted.org/uncertainties/>`__
   support.

Issues:

-  Resolve issue #8: Use
   ```ipyparallel`` <https://github.com/ipython/ipyparallel>`__ now.
-  Resolve issue #9: Use `pytest <https://pytest.org>`__ rather than
   ``nose`` (which is no longer supported).
-  Resolve issue #10: PYFFTW wrappers now support negative ``axis`` and
   ``axes`` arguments.
-  Address issue #11: Preliminary version of some DVR basis classes.
-  Resolve issue #12: Added solvers with
   ```uncertanties`` <https://pythonhosted.org/uncertainties/>`__
   support.

