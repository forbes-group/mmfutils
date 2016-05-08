
1. MMF Utils
============

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

Table of Contents
=================

-  `1. MMF Utils <#1.-MMF-Utils>`__

   -  `1.1 Installing <#1.1-Installing>`__

-  `2. Usage <#2.-Usage>`__

   -  `2.1 Containers <#2.1-Containers>`__

      -  `2.1.1 Object <#2.1.1-Object>`__

         -  `2.1.1.1 Object Example <#2.1.1.1-Object-Example>`__

      -  `2.1.2 Container <#2.1.2-Container>`__

         -  `2.1.2.1 Container Examples <#2.1.2.1-Container-Examples>`__

   -  `2.2 Interfaces <#2.2-Interfaces>`__

      -  `2.2.1 Interface
         Documentation <#2.2.1-Interface-Documentation>`__

   -  `2.3 Parallel <#2.3-Parallel>`__
   -  `2.4 Performance <#2.4-Performance>`__
   -  `2.5 Plotting <#2.5-Plotting>`__

      -  `2.5.1 Fast Filled Contour
         Plots <#2.5.1-Fast-Filled-Contour-Plots>`__
      -  `2.5.2 Angular Variables <#2.5.2-Angular-Variables>`__

   -  `2.6 Debugging <#2.6-Debugging>`__
   -  `2.7 Mathematics <#2.7-Mathematics>`__

-  `3. Developer Instructions <#3.-Developer-Instructions>`__

   -  `3.1 Releases <#3.1-Releases>`__

-  `4. Change Log <#4.-Change-Log>`__

   -  `4.1 REL: 0.4.7 <#4.1-REL:-0.4.7>`__

1.1 Installing
--------------

This package can be installed from `from the bitbucket
project <https://bitbucket.org/mforbes/mmfutils>`__:

.. code:: bash

    pip install hg+https://bitbucket.org/mforbes/mmfutils

2. Usage
========

2.1 Containers
--------------

2.1.1 Object
~~~~~~~~~~~~

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

2.1.1.1 Object Example
^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

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

.. code:: python

    f = np.exp(3*np.cos(2*np.pi*s.x/s.L)) / 15
    df = -2.*np.pi/5.*np.exp(3*np.cos(2*np.pi*s.x/s.L))*np.sin(2*np.pi*s.x/s.L)/s.L
    np.allclose(s.compute_derivative(f), df)




.. parsed-literal::

    True



Here we demonstrate pickling. Note that the pickle is very small, and
when unpickled, ``init()`` is called to re-establish ``s.x`` and
``s.k``.

.. code:: python

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

.. code:: python

    s.N = 64
    s.L = 2.0
    s.init()


.. parsed-literal::

    init() called


Finally, we demonstrate that ``Object`` instances can be archived using
the ``persist`` package:

.. code:: python

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



2.1.2 Container
~~~~~~~~~~~~~~~

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

2.1.2.1 Container Examples
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    from mmfutils.containers import Container
    
    c = Container(a=1, c=2, b='Hi there')
    print c
    print tuple(c)


.. parsed-literal::

    Container(a=1, b='Hi there', c=2)
    (1, 'Hi there', 2)


.. code:: python

    # Attributes are mutable
    c.b = 'Ho there'
    print c


.. parsed-literal::

    Container(a=1, b='Ho there', c=2)


.. code:: python

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


.. code:: python

    import pickle
    c1 = pickle.loads(pickle.dumps(c))
    print c1
    c1.large_temporary_array


.. parsed-literal::

    Container(a=1, b='Ho there', c=2)


::


    ---------------------------------------------------------------------------

    AttributeError                            Traceback (most recent call last)

    <ipython-input-9-cbfd03ed340e> in <module>()
          2 c1 = pickle.loads(pickle.dumps(c))
          3 print c1
    ----> 4 c1.large_temporary_array
    

    AttributeError: 'Container' object has no attribute 'large_temporary_array'


2.2 Interfaces
--------------

The interfaces module collects some useful
`zope.interface <http://docs.zope.org/zope.interface/>`__ tools for
checking interface requirements. Interfaces provide a convenient way of
communicating to a programmer what needs to be done to used your code.
This can then be checked in tests.

.. code:: python

    from mmfutils.interface import Interface, Attribute, verifyClass, verifyObject, implements
    
    class IAdder(Interface):
        """Interface for objects that support addition."""
    
        value = Attribute('value', "Current value of object")
    
        # No self here since this is the "user" interface
        def add(other):
            """Return self + other."""

Here is a broken implementation. We muck up the arguments to ``add``:

.. code:: python

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

.. code:: python

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

.. code:: python

    class Adder(object):
        implements(IAdder)
        def __init__(self, value=0):
            self.value = value
        def add(self, other):
            return one + other
        
    verifyClass(IAdder, Adder) and verifyObject(IAdder, Adder())




.. parsed-literal::

    True



2.2.1 Interface Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We also monkeypatch ``zope.interface.documentation.asStructuredText()``
to provide a mechanism for documentating interfaces in a notebook.

.. code:: python

    from mmfutils.interface import describe_interface
    describe_interface(IAdder)




.. raw:: html

    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="generator" content="Docutils 0.12: http://docutils.sourceforge.net/" />
    <title></title>
    
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




2.3 Parallel
------------

The ``mmfutils.parallel`` module provides some tools for launching and
connecting to IPython clusters. The ``parallel.Cluster`` class
represents and controls a cluster. The cluster is specified by the
profile name, and can be started or stopped from this class:

.. code:: python

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

    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=default --n=3
    WARNING:root:No ipcontroller-client.json, waiting...
    INFO:root:waiting for 3 engines
    INFO:root:0 of 3 running
    INFO:root:3 of 3 running
    INFO:root:Stopping cluster: ipcluster stop --profile=default


.. parsed-literal::

    True


If you only need a cluster for a single task, it can be managed with a
context. Be sure to wait for the result to be computed before exiting
the context and shutting down the cluster!

.. code:: python

    with parallel.Cluster(profile='default', n=3, sleep_time=1.0) as client:
        view = client.load_balanced_view
        x = np.linspace(-6,6, 100)
        y = view.map(lambda x:x**2, x, block=True)  # Make sure to wait for the result!
    print np.allclose(y, x**2)


.. parsed-literal::

    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=default --n=3
    WARNING:root:No ipcontroller-client.json, waiting...
    INFO:root:waiting for 3 engines
    INFO:root:0 of 3 running
    INFO:root:3 of 3 running
    INFO:root:Stopping cluster: ipcluster stop --profile=default


.. parsed-literal::

    True


If you just need to connect to a running cluster, you can use
``parallel.get_client()``.

2.4 Performance
---------------

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

2.5 Plotting
------------

Several tools are provided in ``mmfutils.plot``:

2.5.1 Fast Filled Contour Plots
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``mmfutils.plot.imcontourf`` is similar to matplotlib's ``plt.contourf``
function, but uses ``plt.imshow`` which is much faster. This has
limitations – the data must be equally spaced for example, and it
effectively has as many contours as colours – but is useful for
animations and interactive work. It also supports my idea of saner
array-shape processing (i.e. if ``x`` and ``y`` have different shapes,
then it will match these to the shape of ``z``).

.. code:: python

    %matplotlib inline
    from matplotlib import pyplot as plt
    import time
    import numpy as np
    from mmfutils import plot as mmfplt
    x = np.linspace(-1, 1, 100)[:, None]
    y = np.linspace(-0.1, 0.1, 200)[None, :]
    z = np.sin(10*x)*y**2
    plt.subplot(121)
    %time mmfplt.imcontourf(x, y, z)
    plt.subplot(122)
    %time plt.contourf(x.ravel(), y.ravel(), z.T, 50, cmap='gist_heat')


.. parsed-literal::

    CPU times: user 1.05 ms, sys: 54 µs, total: 1.11 ms
    Wall time: 1.11 ms
    CPU times: user 38.2 ms, sys: 1.25 ms, total: 39.4 ms
    Wall time: 39.4 ms




.. parsed-literal::

    <matplotlib.contour.QuadContourSet instance at 0x115216c20>



.. parsed-literal::

    /data/apps/anaconda/envs/work/lib/python2.7/site-packages/matplotlib/collections.py:590: FutureWarning: elementwise comparison failed; returning scalar instead, but in the future will perform elementwise comparison
      if self._edgecolors == str('face'):



.. image:: README_files/README_50_3.png


2.5.2 Angular Variables
~~~~~~~~~~~~~~~~~~~~~~~

A couple of tools are provided to visualize angular fields, such as the
phase of a complex wavefunction.

.. code:: python

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
    mmfplt.imcontourf(x, y, mmfplt.color_complex(z), aspect=1)
    mmfplt.phase_contour(x, y, z, aspect=1, linewidths=0.5)
    
    # This is faster if you just want to show the phase and allows
    # for a colorbar via a registered colormap
    plt.subplot(133).set_aspect(1)
    mmfplt.imcontourf(x, y, np.angle(z), cmap='huslp', aspect=1)
    plt.colorbar()
    mmfplt.phase_contour(x, y, z, aspect=1, linewidths=0.5)


.. parsed-literal::

    /data/apps/anaconda/envs/work/lib/python2.7/site-packages/matplotlib/collections.py:650: FutureWarning: elementwise comparison failed; returning scalar instead, but in the future will perform elementwise comparison
      if self._edgecolors_original != str('face'):




.. parsed-literal::

    (<matplotlib.contour.QuadContourSet instance at 0x115f66d88>,
     <matplotlib.contour.QuadContourSet instance at 0x115f8d950>)




.. image:: README_files/README_53_2.png


2.6 Debugging
-------------

A couple of debugging tools are provided. The most useful is the
``debug`` decorator which will store the local variables of a function
in a dictionary or in your global scope.

.. code:: python

    from mmfutils.debugging import debug
    
    @debug(locals())
    def f(x):
        y = x**1.5
        z = 2/x
        return z
    
    print(f(2.0), x, y, z)


.. parsed-literal::

    (1.0, 2.0, 2.8284271247461903, 1.0)


2.7 Mathematics
---------------

We include a few mathematical tools here too. In particular, numerical
integration and differentiation. Check the API documentation for
details.

3. Developer Instructions
=========================

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

.. code:: python

    !cd $ROOTDIR; ipython nbconvert --to=rst --output=README.rst doc/README.ipynb


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

.. code:: python

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

.. code:: python

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




3.1 Releases
------------

We try to keep the repository clean with the following properties:

1. The default branch is stable: i.e. if someone runs ``hg clone``, this
   will pull the latest stable release.
2. Each release has its own named branch so that e.g. ``hg up 0.4.6``
   will get the right thing. Note: this should update to the development
   branch, *not* the default branch so that any work committed will not
   pollute the development branch (which would violate the previous
   point).

To do this, we advocate the following proceedure.

1. **``hg up <version>``**: Make sure this is the correct development
   branch, not the default branch. (Check by ``hg up default`` which
   should take you to the default branch.)
2. **Work**: Do your work, committing as required with messages as shown
   in the repository with the following keys:

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

3. **``python setup.py test``**: Make sure the tests pass. (``hg com``
   will do this automatically if you have linked the ``.hgrc`` file as
   discussed above.
4. **Update Docs**: Update the documentation if needed. To generate new
   documentation run:

   cd doc sphinx-apidoc -eTE ../mmfutils -o source rm
   source/mmfutis.tests.\*

Edit any new files created (titles often need to be added) and check
that this looks good with

::

     make html
     open build/html/index.html
     

Look especially for errors of the type
``WARNING: document isn't included in any toctree``. This indicates that
you probably need to add the module to an upper level ``.. toctree::``.
Also look for
``WARNING: toctree contains reference to document u'...' that doesn't have a title: no link will be generated``.
This indicates you need to add a title to a new file. For example, when
I added the ``mmf.math.optimize`` module, I needed to update the
following:

\`\`\`rst .. doc/source/mmfutils.rst mmfutils ========

.. toctree:: ... mmfutils.optimize ... ````\ rst ..
doc/source/mmfutils.optimize.rst mmfutils.optimize =================

.. automodule:: mmfutils.optimize :members: :undoc-members:
:show-inheritance: \`\`\`

5. **``hg histedit``**: (or ``hg rebase``, or ``hg strip`` as needed)
   Clean up the repo before you push. Branches should generally be
   linear unless there is an exceptional reason to split development.
6. **Release**: First edit ``mmfutils/__init__.py`` and update the
   version number by removing the ``dev`` part of the version number.
   Commit only this change and then push only the branch you are working
   on:

   hg com -m "REL: " hg push -b .
7. Create a pull request on the development fork from your branch to
   ``default`` on the release project bitbucket. Review it, fix
   anything, then accept the PR and close the branch.
8. **Start new branch**: On the same development branch (not
   ``default``), increase the version number in ``mmfutils/__init__.py``
   and add ``dev``: i.e.:

   **version** = '0.4.7dev'

Then create this branch and commit this:

::

       hg branch "0.4.7"
       hg com -m "BRN: Started branch 0.4.7"

9.  Update `MyPI <https://bitbucket.org/mforbes/mypi>`__ index.
10. Optional: Update any ``setup.py`` files that depend on your new
    features/fixes etc.

4. Change Log
=============

4.1 REL: 0.4.7
--------------

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
