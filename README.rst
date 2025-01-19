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

**Source:**

-  https://alum.mit.edu/www/mforbes/hg/forbes-group/mmfutils: Permalink
   (will forward).
-  https://hg.iscimath.org/forbes-group/mmfutils: Current, in case the
   permalink fails.
-  https://github.com/forbes-group/mmfutils: Public read-only mirror.

**Issues:**
https://alum.mit.edu/www/mforbes/hg/forbes-group/mmfutils/issues

**Build Status**

|Documentation Status| |Build Status| |Python 3.9 test results| |Python
3.10 test results| |Python 3.11 test results| |Python 3.12 test results|
|Python 3.13 test results|

.. |Documentation Status| image:: https://readthedocs.org/projects/mmfutils/badge/?version=latest
   :target: https://mmfutils.readthedocs.io/en/latest/?badge=latest
.. |Build Status| image:: https://cloud.drone.io/api/badges/forbes-group/mmfutils/status.svg
   :target: https://cloud.drone.io/forbes-group/mmfutils
.. |Python 3.9 test results| image:: https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.9.yaml?label=3.9&logo=GitHub
   :target: https://github.com/forbes-group/mmfutils/actions/workflows/python_3.9.yaml
.. |Python 3.10 test results| image:: https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.10.yaml?label=3.10&logo=GitHub
   :target: https://github.com/forbes-group/mmfutils/actions/workflows/python_3.10.yaml
.. |Python 3.11 test results| image:: https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.11.yaml?label=3.11&logo=GitHub
   :target: https://github.com/forbes-group/mmfutils/actions/workflows/python_3.11.yaml
.. |Python 3.12 test results| image:: https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.12.yaml?label=3.12&logo=GitHub
   :target: https://github.com/forbes-group/mmfutils/actions/workflows/python_3.12.yaml
.. |Python 3.13 test results| image:: https://img.shields.io/github/actions/workflow/status/forbes-group/mmfutils/python_3.13.yaml?label=3.13&logo=GitHub
   :target: https://github.com/forbes-group/mmfutils/actions/workflows/python_3.13.yaml

Installing
----------

This package can be installed from
`PyPI <https://pypi.org/project/mmfutils/>`__:

.. code:: bash

   python3 -m pip install mmfutils
   python3 -m pip install mmfutils[fftw]   # If you have the FFTW libraries installed

or, if you need to install from source, you can get it from one of the
repositories:

.. code:: bash

   python3 -m pip install hg+https://alum.mit.edu/www/mforbes/hg/forbes-group/mmfutils
   python3 -m pip install git+https://github.com/forbes-group/mmfutils

Usage
=====

Containers
----------

ObjectBase and Object
~~~~~~~~~~~~~~~~~~~~~

The ``ObjectBase`` and ``Object`` classes provide some useful features
described below. Consider a problem where a class is defined through a
few parameters, but requires extensive initialization before it can be
properly used. An example is a numerical simulation where one passes the
number of grid points :math:`N` and a length :math:`L`, but the
initialization must generate large grids for efficient use later on.
These grids should be generated before computations begin, but should
not be re-generated every time needed. They also should not be pickled
when saved to disk.

**Deferred initialization via the ``init()`` method:** The idea here
changes the semantics of ``__init__()`` slightly by deferring any
expensive initialization to ``init()``. Under this scheme,
``__init__()`` should only set and check what we call picklable
attributes: these are parameters that define the object (they will be
pickled in ``Object`` below) and will be stored in a list
``self.picklable_attributes`` which is computed at the end of
``ObjectBase.__init__()`` as the list of all keys in ``__dict__``. Then,
``ObjectBase.__init__()`` will call ``init()`` where all remaining
attributes should be calculated.

This allows users to change various attributes, then reinitialize the
object once with an explicit call to ``init()`` before performing
expensive computations. This is an alternative to providing complete
properties (getters and setters) for objects that need to trigger
computation. The use of setters is safer, but requires more work on the
side of the developer and can lead to complex code when different
properties depend on each other. The approach here puts all computations
in a single place. Of course, the user must remember to call ``init()``
before working with the object.

To facilitate this, we provide a mild check in the form of an
``initialized`` flag that is set to ``True`` at the end of the base
``init()`` chain, and set to ``False`` if any variables are in
``pickleable_attributes`` are set.

**Serialization and Deferred Initialization:** The base class
``ObjectBase`` does not provide any pickling services but does provide a
nice representation. Additional functionality is provided by ``Object``
which uses the features of ``ObjectBase`` to define ``__getstate__()``
and ``__setstate__()`` methods for pickling which pickle only the
``picklable_attributes``. Note: unpickling an object will **not** call
``__init__()`` but will call ``init()`` giving objects a chance to
restore the computed attributes from pickles.

-  **Note:** *Before using, consider if these features are really needed
   – with all such added functionality comes additional potential
   failure modes from side-interactions. The ``ObjectBase`` class is
   quite simple, and therefore quite safe, while ``Object`` adds
   additional functionality with potential side-effects. For example, a
   side-effect of support for pickles is that ``copy.copy()`` will also
   invoke ``init()`` when copying might instead be much faster. Thus, we
   recommend only using ``ObjectBase`` for efficient code.*

Object Example
^^^^^^^^^^^^^^

.. code:: ipython3

    ROOTDIR = !hg root
    ROOTDIR = ROOTDIR[0]
    import sys
    
    sys.path.insert(0, ROOTDIR)
    
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
            self.x = np.arange(self.N, dtype=float) * dx - self.L / 2.0
            self.k = 2 * np.pi * np.fft.fftfreq(self.N, dx)
    
            # Set highest momentum to zero if N is even to
            # avoid rapid oscillations
            if self.N % 2 == 0:
                self.k[self.N // 2] = 0.0
    
            # Calls base class which sets self.initialized
            super().init()
    
        def compute_derivative(self, f):
            """Return the derivative of f."""
            return np.fft.ifft(self.k * 1j * np.fft.fft(f)).real
    
    
    s = State(256)
    print(s)  # No default value for L


.. parsed-literal::

    init() called
    __init__() called
    State(L=1.0, N=256)


.. code:: ipython3

    s.L = 2.0
    print(s)


.. parsed-literal::

    State(L=2.0, N=256)


One feature is that a nice ``repr()`` of the object is produced. Now
let’s do a calculation:

.. code:: ipython3

    f = np.exp(3 * np.cos(2 * np.pi * s.x / s.L)) / 15
    df = (
        -2.0
        * np.pi
        / 5.0
        * np.exp(3 * np.cos(2 * np.pi * s.x / s.L))
        * np.sin(2 * np.pi * s.x / s.L)
        / s.L
    )
    np.allclose(s.compute_derivative(f), df)




.. parsed-literal::

    False



Oops! We forgot to reinitialize the object… (The formula is correct, but
the lattice is no longer commensurate so the FFT derivative has huge
errors).

.. code:: ipython3

    print(s.initialized)
    s.init()
    assert s.initialized
    f = np.exp(3 * np.cos(2 * np.pi * s.x / s.L)) / 15
    df = (
        -2.0
        * np.pi
        / 5.0
        * np.exp(3 * np.cos(2 * np.pi * s.x / s.L))
        * np.sin(2 * np.pi * s.x / s.L)
        / s.L
    )
    np.allclose(s.compute_derivative(f), df)


.. parsed-literal::

    False
    init() called




.. parsed-literal::

    True



Here we demonstrate pickling. Note that using ``Object`` makes the
pickles very small, and when unpickled, ``init()`` is called to
re-establish ``s.x`` and ``s.k``. Generally one would inherit from
``Object``, but since we already have a class, we can provide pickling
functionality with ``ObjectMixin``:

.. code:: ipython3

    class State1(ObjectMixin, State):
        pass
    
    
    s = State(N=256, _quiet=True)
    s1 = State1(N=256, _quiet=True)

.. code:: ipython3

    import pickle, copy

.. code:: ipython3

    s_repr = pickle.dumps(s)
    s1_repr = pickle.dumps(s1)
    print(f"ObjectBase pickle:  {len(s_repr)} bytes")
    print(f"ObjectMixin pickle: {len(s1_repr)} bytes")


.. parsed-literal::

    ObjectBase pickle:  4397 bytes
    ObjectMixin pickle: 103 bytes


Note, however, that the speed of copying is significantly impacted:

.. code:: ipython3

    %timeit copy.copy(s)
    %timeit copy.copy(s1)


.. parsed-literal::

    1.12 μs ± 33.2 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)
    8.98 μs ± 168 ns per loop (mean ± std. dev. of 7 runs, 100,000 loops each)


Another use case applies when ``init()`` is expensive. If :math:`x` and
:math:`k` were computed in ``__init__()``, then using properties to
change both :math:`N` and :math:`L` would trigger two updates. Here we
do the updates, then call ``init()``. Good practice is to call
``init()`` automatically before any serious calculation to ensure that
the object is brought up to date before the computation.

.. code:: ipython3

    s.N = 64
    s.L = 2.0
    s.init()

Finally, we demonstrate that ``Object`` instances can be archived using
the ``persist`` package:

.. code:: ipython3

    import persist.archive
    
    a = persist.archive.Archive(check_on_insert=True)
    a.insert(s=s)
    
    d = {}
    exec(str(a), d)
    
    d["s"]




.. parsed-literal::

    State(L=2.0, N=64, _quiet=True)



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

.. code:: ipython3

    from mmfutils.containers import Container
    
    c = Container(a=1, c=2, b="Hi there")
    print(c)
    print(tuple(c))


.. parsed-literal::

    Container(a=1, b='Hi there', c=2)
    (1, 'Hi there', 2)


.. code:: ipython3

    # Attributes are mutable
    c.b = "Ho there"
    print(c)


.. parsed-literal::

    Container(a=1, b='Ho there', c=2)


.. code:: ipython3

    # Other attributes can be used for temporary storage but will not be pickled.
    import numpy as np
    
    c.large_temporary_array = np.ones((256, 256))
    print(c)
    print(c.large_temporary_array)


.. parsed-literal::

    Container(a=1, b='Ho there', c=2)
    [[1. 1. 1. ... 1. 1. 1.]
     [1. 1. 1. ... 1. 1. 1.]
     [1. 1. 1. ... 1. 1. 1.]
     ...
     [1. 1. 1. ... 1. 1. 1.]
     [1. 1. 1. ... 1. 1. 1.]
     [1. 1. 1. ... 1. 1. 1.]]


.. code:: ipython3

    import pickle

.. code:: ipython3

    c1 = pickle.loads(pickle.dumps(c))
    print(c1)
    c1.large_temporary_array


.. parsed-literal::

    Container(a=1, b='Ho there', c=2)


::


    ---------------------------------------------------------------------------

    AttributeError                            Traceback (most recent call last)

    Cell In[15], line 3
          1 c1 = pickle.loads(pickle.dumps(c))
          2 print(c1)
    ----> 3 c1.large_temporary_array


    AttributeError: 'Container' object has no attribute 'large_temporary_array'


Contexts
--------

The ``mmfutils.contexts`` module provides two useful contexts:

``NoInterrupt``: This can be used to susspend ``KeyboardInterrupt``
exceptions until they can be dealt with at a point that is convenient. A
typical use is when performing a series of calculations in a loop. By
placing the loop in a ``NoInterrupt`` context, one can avoid an
interrupt from ruining a calculation:

.. code:: ipython3

    from mmfutils.contexts import NoInterrupt
    
    complete = False
    n = 0
    with NoInterrupt() as interrupted:
        while not complete and not interrupted:
            n += 1
            if n > 10:
                complete = True

Note: One can nest ``NoInterrupt`` contexts so that outer loops are also
interrupted. Another use-case is mapping. See
`doc/Animation.ipynb <Animation.ipynb>`__ for more examples.

.. code:: ipython3

    res = NoInterrupt().map(abs, range(-100, 100))
    np.sign(res)




.. parsed-literal::

    array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
           1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
           1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
           1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
           1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
           1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
           1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
           1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
           1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
           1, 1])



Interfaces
----------

The interfaces module collects some useful
`zope.interface <http://docs.zope.org/zope.interface/>`__ tools for
checking interface requirements. Interfaces provide a convenient way of
communicating to a programmer what needs to be done to used your code.
This can then be checked in tests.

.. code:: ipython3

    from mmfutils.interface import (
        Interface,
        Attribute,
        verifyClass,
        verifyObject,
        implementer,
    )
    
    
    class IAdder(Interface):
        """Interface for objects that support addition."""
    
        value = Attribute("value", "Current value of object")
    
        # No self here since this is the "user" interface
        def add(other):
            """Return self + other."""

Here is a broken implementation. We muck up the arguments to ``add``:

.. code:: ipython3

    @implementer(IAdder)
    class AdderBroken(object):
        def add(self, one, another):
            # There should only be one argument!
            return one + another
    
    
    try:
        verifyClass(IAdder, AdderBroken)
    except Exception as e:
        print("{0.__class__.__name__}: {0}".format(e))


.. parsed-literal::

    BrokenMethodImplementation: The object <class '__main__.AdderBroken'> has failed to implement interface __main__.IAdder: The contract of __main__.IAdder.add(other) is violated because 'AdderBroken.add(self, one, another)' requires too many arguments.


Now we get ``add`` right, but forget to define ``value``. This is only
caught when we have an object since the attribute is supposed to be
defined in ``__init__()``:

.. code:: ipython3

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


.. parsed-literal::

    BrokenImplementation: The object <__main__.AdderBroken object at 0x115ac5a90> has failed to implement interface __main__.IAdder: The __main__.IAdder.value attribute was not provided.


Finally, a working instance:

.. code:: ipython3

    @implementer(IAdder)
    class Adder(object):
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

.. code:: ipython3

    from mmfutils.interface import describe_interface

.. code:: ipython3

    describe_interface(IAdder)




.. raw:: html

    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="generator" content="Docutils 0.21.2: https://docutils.sourceforge.io/" />
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

.. code:: ipython3

    import logging

.. code:: ipython3

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    import numpy as np
    from mmfutils import parallel

.. code:: ipython3

    cluster = parallel.Cluster(profile="default", n=3, sleep_time=1.0)
    cluster.start()
    cluster.wait()  # Instance of IPython.parallel.Client
    view = cluster.load_balanced_view
    x = np.linspace(-6, 6, 100)
    y = view.map(lambda x: x**2, x)
    print(np.allclose(y, x**2))
    cluster.stop()


.. parsed-literal::

    Waiting for connection file: ~/.ipython/profile_default/security/ipcontroller-client.json


.. parsed-literal::

    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=default --n=3
    2024-12-31 16:40:49.374 [IPController] Hub listening on tcp://127.0.0.1:65099 for registration.
    2024-12-31 16:40:49.374 [IPController] Hub using DB backend: DictDB
    2024-12-31 16:40:49.626 [IPController] hub::created hub
    2024-12-31 16:40:49.627 [IPController] writing connection info to /Users/mforbes/.ipython/profile_default/security/ipcontroller-client.json
    2024-12-31 16:40:49.627 [IPController] writing connection info to /Users/mforbes/.ipython/profile_default/security/ipcontroller-engine.json
    2024-12-31 16:40:49.628 [IPController] task::using Python leastload Task scheduler
    2024-12-31 16:40:49.993 [IPController] Heartmonitor beating every 3000ms
    2024-12-31 16:40:50.296 [broadcast-00] BroadcastScheduler 00 started
    2024-12-31 16:40:50.297 [broadcast-0] BroadcastScheduler 0 started
    2024-12-31 16:40:50.298 [broadcast-01] BroadcastScheduler 01 started
    Leaving cluster running: /Users/mforbes/.ipython/profile_default/security/cluster-.json
    INFO:root:waiting for 3 engines
    INFO:root:0 of 3 running
    INFO:root:3 of 3 running
    INFO:root:Stopping cluster: ipcluster stop --profile=default


.. parsed-literal::

    True


.. parsed-literal::

    2024-12-31 16:40:56.878 [IPClusterStop] Stopping cluster 
    2024-12-31 16:40:56.878 [IPClusterStop] Stopping controller
    2024-12-31 16:40:56.964 [IPClusterStop] Stopping engine(s): 1735688450


.. parsed-literal::

    Waiting for connection file: ~/.ipython/profile_default/security/ipcontroller-client.json


If you only need a cluster for a single task, it can be managed with a
context. Be sure to wait for the result to be computed before exiting
the context and shutting down the cluster!

.. code:: ipython3

    with parallel.Cluster(profile="default", n=3, sleep_time=1.0) as client:
        view = client.load_balanced_view
        x = np.linspace(-6, 6, 100)
        y = view.map(lambda x: x**2, x, block=True)  # Make sure to wait for the result!
    print(np.allclose(y, x**2))


.. parsed-literal::

    Waiting for connection file: ~/.ipython/profile_default/security/ipcontroller-client.json


.. parsed-literal::

    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=default --n=3
    2024-12-31 16:41:18.017 [IPController] Hub listening on tcp://127.0.0.1:65265 for registration.
    2024-12-31 16:41:18.018 [IPController] Hub using DB backend: DictDB
    2024-12-31 16:41:18.273 [IPController] hub::created hub
    2024-12-31 16:41:18.273 [IPController] writing connection info to /Users/mforbes/.ipython/profile_default/security/ipcontroller-client.json
    2024-12-31 16:41:18.275 [IPController] writing connection info to /Users/mforbes/.ipython/profile_default/security/ipcontroller-engine.json
    2024-12-31 16:41:18.275 [IPController] task::using Python leastload Task scheduler
    2024-12-31 16:41:18.307 [IPController] Heartmonitor beating every 3000ms
    2024-12-31 16:41:18.597 [broadcast-01] BroadcastScheduler 01 started
    2024-12-31 16:41:18.598 [broadcast-00] BroadcastScheduler 00 started
    2024-12-31 16:41:18.598 [broadcast-0] BroadcastScheduler 0 started
    2024-12-31 16:41:18.625 [task] Task scheduler started [leastload]
    2024-12-31 16:41:18.625 [IPController] client::client b'\x00\x80\x00A\xaa' requested 'connection_request'
    2024-12-31 16:41:18.625 [IPController] client::client [b'\x00\x80\x00A\xaa'] connected
    2024-12-31 16:41:18.628 [IPController] heartbeat::waiting for subscription
    2024-12-31 16:41:18.629 [IPController] heartbeat::subscription started
    Leaving cluster running: /Users/mforbes/.ipython/profile_default/security/cluster-.json
    INFO:root:waiting for 3 engines
    INFO:root:0 of 3 running
    INFO:root:3 of 3 running
    INFO:root:Stopping cluster: ipcluster stop --profile=default
    2024-12-31 16:41:25.512 [IPClusterStop] Stopping cluster 
    2024-12-31 16:41:25.512 [IPClusterStop] Stopping controller
    2024-12-31 16:41:25.599 [IPClusterStop] Stopping engine(s): 1735688478


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
libraries (i.e. the `FFTW <http://www.fftw.org>`__). However, the
various components will not be imported by default.

Here is a brief description of the components:

-  ``mmfutils.performance.blas``: Provides an interface to a few of the
   scipy BLAS wrappers. Very incomplete (only things I currently need).
-  ``mmfutils.performance.fft``: Provides an interface to the
   `FFTW <http://www.fftw.org>`__ using ``pyfftw`` if it is available.
   Also enables the planning cache and setting threads so you can better
   control your performance.
-  ``mmfutils.performance.numexpr``: Robustly imports numexpr and
   disabling the VML. (If you don’t do this carefully, it will crash
   your program so fast you won’t even get a traceback.)
-  ``mmfutils.performance.threads``: Provides some hooks for setting the
   maximum number of threads in a bunch of places including the MKL,
   numexpr, and fftw.

Plotting
--------

Several tools are provided in ``mmfutils.plot``:

Fast Filled Contour Plots
~~~~~~~~~~~~~~~~~~~~~~~~~

``mmfutils.plot.imcontourf`` is similar to matplotlib’s ``plt.contourf``
function, but uses ``plt.imshow`` which is much faster. This is useful
for animations and interactive work. It also supports my idea of saner
array-shape processing (i.e. if ``x`` and ``y`` have different shapes,
then it will match these to the shape of ``z``). Matplotlib now provides
``plt.pcolourmesh`` which is similar, but has the same interface issues.

.. code:: ipython3

    %matplotlib inline
    from matplotlib import pyplot as plt
    import time
    import numpy as np
    from mmfutils import plot as mmfplt

.. code:: ipython3

    x = np.linspace(-1, 1, 100)[:, None] ** 3
    y = np.linspace(-0.1, 0.1, 200)[None, :] ** 3
    z = np.sin(10 * x) * y**2
    plt.figure(figsize=(12, 3))
    plt.subplot(141)
    %time mmfplt.imcontourf(x, y, z, cmap='gist_heat')
    plt.subplot(142)
    %time plt.contourf(x.ravel(), y.ravel(), z.T, 50, cmap='gist_heat')
    plt.subplot(143)
    %time plt.pcolor(x.ravel(), y.ravel(), z.T, cmap='gist_heat', shading='auto')
    plt.subplot(144)
    %time plt.pcolormesh(x.ravel(), y.ravel(), z.T, cmap='gist_heat', shading='gouraud')


.. parsed-literal::

    CPU times: user 6.26 ms, sys: 1.87 ms, total: 8.13 ms
    Wall time: 8.85 ms
    CPU times: user 31.3 ms, sys: 3.68 ms, total: 35 ms
    Wall time: 200 ms
    CPU times: user 47.7 ms, sys: 2.04 ms, total: 49.8 ms
    Wall time: 49.6 ms
    CPU times: user 1.3 ms, sys: 43 μs, total: 1.34 ms
    Wall time: 1.35 ms




.. parsed-literal::

    <matplotlib.collections.QuadMesh at 0x122f6cb00>




.. image:: ../README_files/../README_66_2.png


Angular Variables
-----------------

A couple of tools are provided to visualize angular fields, such as the
phase of a complex wavefunction.

.. code:: ipython3

    %matplotlib inline
    from matplotlib import pyplot as plt
    import time
    import numpy as np
    from mmfutils import plot as mmfplt
    
    x = np.linspace(-1, 1, 100)[:, None]
    y = np.linspace(-1, 1, 200)[None, :]
    z = x + 1j * y
    
    plt.figure(figsize=(9, 2))
    ax = plt.subplot(131)
    mmfplt.phase_contour(x, y, z, colors="k", linewidths=0.5)
    ax.set_aspect(1)
    
    # This is a little slow but allows you to vary the luminosity.
    ax = plt.subplot(132)
    mmfplt.imcontourf(x, y, mmfplt.colors.color_complex(z))
    mmfplt.phase_contour(x, y, z, linewidths=0.5)
    ax.set_aspect(1)
    
    # This is faster if you just want to show the phase and allows
    # for a colorbar via a registered colormap
    ax = plt.subplot(133)
    mmfplt.imcontourf(x, y, np.angle(z), cmap="huslp")
    ax.set_aspect(1)
    plt.colorbar()
    mmfplt.phase_contour(x, y, z, linewidths=0.5)




.. parsed-literal::

    (<matplotlib.contour.QuadContourSet at 0x12362f590>,
     <matplotlib.contour.QuadContourSet at 0x1255c57c0>)




.. image:: ../README_files/../README_69_1.png


Debugging
---------

A couple of debugging tools are provided. The most useful is the
``debug`` decorator which will store the local variables of a function
in a dictionary or in your global scope.

.. code:: ipython3

    from mmfutils.debugging import debug
    
    
    @debug(locals())
    def f(x):
        y = x**1.5
        z = 2 / x
        return z
    
    
    print(f(2.0), x, y, z)


.. parsed-literal::

    1.0 2.0 2.8284271247461903 1.0


Mathematics
-----------

We include a few mathematical tools here too. In particular, numerical
integration and differentiation. Check the API documentation for
details.

Developer Instructions
======================

For Developer Notes, please see `Notes.md <../Notes.md>`__.

Complete code coverage information is provided in
``build/_coverage/index.html``.

.. code:: ipython3

    from IPython.display import HTML

.. code:: ipython3

    with open(os.path.join(ROOTDIR, "build/_coverage/index.html")) as f:
        coverage = f.read()
    HTML(coverage)




.. raw:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>Coverage report</title>
        <link rel="icon" sizes="32x32" href="favicon_32_cb_58284776.png">
        <link rel="stylesheet" href="style_cb_8e611ae1.css" type="text/css">
        <script src="coverage_html_cb_6fb7b396.js" defer></script>
    </head>
    <body class="indexfile">
    <header>
        <div class="content">
            <h1>Coverage report:
                <span class="pc_cov">86%</span>
            </h1>
            <aside id="help_panel_wrapper">
                <input id="help_panel_state" type="checkbox">
                <label for="help_panel_state">
                    <img id="keyboard_icon" src="keybd_closed_cb_ce680311.png" alt="Show/hide keyboard shortcuts">
                </label>
                <div id="help_panel">
                    <p class="legend">Shortcuts on this page</p>
                    <div class="keyhelp">
                        <p>
                            <kbd>f</kbd>
                            <kbd>s</kbd>
                            <kbd>m</kbd>
                            <kbd>x</kbd>
                            <kbd>c</kbd>
                            &nbsp; change column sorting
                        </p>
                        <p>
                            <kbd>[</kbd>
                            <kbd>]</kbd>
                            &nbsp; prev/next file
                        </p>
                        <p>
                            <kbd>?</kbd> &nbsp; show/hide this help
                        </p>
                    </div>
                </div>
            </aside>
            <form id="filter_container">
                <input id="filter" type="text" value="" placeholder="filter...">
                <div>
                    <input id="hide100" type="checkbox" >
                    <label for="hide100">hide covered</label>
                </div>
            </form>
            <h2>
                    <a class="button current">Files</a>
                    <a class="button" href="function_index.html">Functions</a>
                    <a class="button" href="class_index.html">Classes</a>
            </h2>
            <p class="text">
                <a class="nav" href="https://coverage.readthedocs.io/en/7.6.10">coverage.py v7.6.10</a>,
                created at 2024-12-29 01:07 -0800
            </p>
        </div>
    </header>
    <main id="index">
        <table class="index" data-sortable>
            <thead>
                <tr class="tablehead" title="Click to sort">
                    <th id="file" class="name left" aria-sort="none" data-shortcut="f">File<span class="arrows"></span></th>
                    <th id="statements" aria-sort="none" data-default-sort-order="descending" data-shortcut="s">statements<span class="arrows"></span></th>
                    <th id="missing" aria-sort="none" data-default-sort-order="descending" data-shortcut="m">missing<span class="arrows"></span></th>
                    <th id="excluded" aria-sort="none" data-default-sort-order="descending" data-shortcut="x">excluded<span class="arrows"></span></th>
                    <th id="coverage" class="right" aria-sort="none" data-shortcut="c">coverage<span class="arrows"></span></th>
                </tr>
            </thead>
            <tbody>
                <tr class="region">
                    <td class="name left"><a href="z_d79ac605fce24c24___init___py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/__init__.py</a></td>
                    <td>18</td>
                    <td>2</td>
                    <td>2</td>
                    <td class="right" data-ratio="16 18">89%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d79ac605fce24c24_containers_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/containers.py</a></td>
                    <td>113</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="113 113">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d79ac605fce24c24_contexts_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/contexts.py</a></td>
                    <td>313</td>
                    <td>28</td>
                    <td>2</td>
                    <td class="right" data-ratio="285 313">91%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d79ac605fce24c24_debugging_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/debugging.py</a></td>
                    <td>49</td>
                    <td>0</td>
                    <td>3</td>
                    <td class="right" data-ratio="49 49">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d79ac605fce24c24_interface_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/interface.py</a></td>
                    <td>77</td>
                    <td>0</td>
                    <td>16</td>
                    <td class="right" data-ratio="77 77">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_a3d06838b9c8763c___init___py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/__init__.py</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="0 0">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d5c69074a1ed3391___init___py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/bases/__init__.py</a></td>
                    <td>2</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="2 2">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d5c69074a1ed3391_bases_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/bases/bases.py</a></td>
                    <td>463</td>
                    <td>59</td>
                    <td>0</td>
                    <td class="right" data-ratio="404 463">87%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d5c69074a1ed3391_interfaces_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/bases/interfaces.py</a></td>
                    <td>41</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="41 41">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d5c69074a1ed3391_utils_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/bases/utils.py</a></td>
                    <td>28</td>
                    <td>0</td>
                    <td>14</td>
                    <td class="right" data-ratio="28 28">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_a3d06838b9c8763c_bessel_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/bessel.py</a></td>
                    <td>132</td>
                    <td>0</td>
                    <td>14</td>
                    <td class="right" data-ratio="132 132">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_a3d06838b9c8763c_differentiate_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/differentiate.py</a></td>
                    <td>61</td>
                    <td>2</td>
                    <td>0</td>
                    <td class="right" data-ratio="59 61">97%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_f46b66d8c9e48fc7___init___py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/integrate/__init__.py</a></td>
                    <td>215</td>
                    <td>12</td>
                    <td>16</td>
                    <td class="right" data-ratio="203 215">94%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_a3d06838b9c8763c_linalg_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/linalg.py</a></td>
                    <td>12</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="12 12">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_a3d06838b9c8763c_special_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/special.py</a></td>
                    <td>42</td>
                    <td>12</td>
                    <td>0</td>
                    <td class="right" data-ratio="30 42">71%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_a3d06838b9c8763c_wigner_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/math/wigner.py</a></td>
                    <td>20</td>
                    <td>2</td>
                    <td>0</td>
                    <td class="right" data-ratio="18 20">90%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d79ac605fce24c24_optimize_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/optimize.py</a></td>
                    <td>26</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="26 26">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d79ac605fce24c24_parallel_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/parallel.py</a></td>
                    <td>129</td>
                    <td>5</td>
                    <td>8</td>
                    <td class="right" data-ratio="124 129">96%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_29592a65330e2fe5___init___py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/performance/__init__.py</a></td>
                    <td>19</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="19 19">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_29592a65330e2fe5_blas_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/performance/blas.py</a></td>
                    <td>58</td>
                    <td>0</td>
                    <td>6</td>
                    <td class="right" data-ratio="58 58">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_29592a65330e2fe5_fft_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/performance/fft.py</a></td>
                    <td>168</td>
                    <td>5</td>
                    <td>7</td>
                    <td class="right" data-ratio="163 168">97%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_29592a65330e2fe5_numexpr_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/performance/numexpr.py</a></td>
                    <td>9</td>
                    <td>0</td>
                    <td>8</td>
                    <td class="right" data-ratio="9 9">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_29592a65330e2fe5_threads_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/performance/threads.py</a></td>
                    <td>9</td>
                    <td>0</td>
                    <td>8</td>
                    <td class="right" data-ratio="9 9">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_406f9e27329eddcd___init___py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/plot/__init__.py</a></td>
                    <td>5</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="5 5">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_406f9e27329eddcd_animation_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/plot/animation.py</a></td>
                    <td>81</td>
                    <td>18</td>
                    <td>0</td>
                    <td class="right" data-ratio="63 81">78%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_406f9e27329eddcd_cmaps_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/plot/cmaps.py</a></td>
                    <td>10</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="10 10">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_406f9e27329eddcd_colors_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/plot/colors.py</a></td>
                    <td>84</td>
                    <td>7</td>
                    <td>0</td>
                    <td class="right" data-ratio="77 84">92%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_406f9e27329eddcd_contour_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/plot/contour.py</a></td>
                    <td>63</td>
                    <td>24</td>
                    <td>0</td>
                    <td class="right" data-ratio="39 63">62%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_406f9e27329eddcd_errors_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/plot/errors.py</a></td>
                    <td>79</td>
                    <td>27</td>
                    <td>0</td>
                    <td class="right" data-ratio="52 79">66%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_406f9e27329eddcd_publish_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/plot/publish.py</a></td>
                    <td>326</td>
                    <td>137</td>
                    <td>0</td>
                    <td class="right" data-ratio="189 326">58%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_406f9e27329eddcd_rasterize_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/plot/rasterize.py</a></td>
                    <td>23</td>
                    <td>6</td>
                    <td>0</td>
                    <td class="right" data-ratio="17 23">74%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3172abb41a3a9bc6___init___py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/solve/__init__.py</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="0 0">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3172abb41a3a9bc6_broyden_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/solve/broyden.py</a></td>
                    <td>325</td>
                    <td>66</td>
                    <td>0</td>
                    <td class="right" data-ratio="259 325">80%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_d79ac605fce24c24_testing_py.html">.nox/test-3-10/lib/python3.10/site-packages/mmfutils/testing.py</a></td>
                    <td>18</td>
                    <td>2</td>
                    <td>2</td>
                    <td class="right" data-ratio="16 18">89%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_37318ec43babbc61___init___py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/__init__.py</a></td>
                    <td>18</td>
                    <td>2</td>
                    <td>2</td>
                    <td class="right" data-ratio="16 18">89%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_37318ec43babbc61_containers_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/containers.py</a></td>
                    <td>113</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="113 113">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_37318ec43babbc61_contexts_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/contexts.py</a></td>
                    <td>313</td>
                    <td>28</td>
                    <td>2</td>
                    <td class="right" data-ratio="285 313">91%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_37318ec43babbc61_debugging_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/debugging.py</a></td>
                    <td>49</td>
                    <td>0</td>
                    <td>3</td>
                    <td class="right" data-ratio="49 49">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_37318ec43babbc61_interface_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/interface.py</a></td>
                    <td>77</td>
                    <td>0</td>
                    <td>16</td>
                    <td class="right" data-ratio="77 77">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_2ab4bfb8124a6a45___init___py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/__init__.py</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="0 0">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_4accd1b72b07cbde___init___py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/bases/__init__.py</a></td>
                    <td>2</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="2 2">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_4accd1b72b07cbde_bases_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/bases/bases.py</a></td>
                    <td>463</td>
                    <td>59</td>
                    <td>0</td>
                    <td class="right" data-ratio="404 463">87%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_4accd1b72b07cbde_interfaces_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/bases/interfaces.py</a></td>
                    <td>41</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="41 41">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_4accd1b72b07cbde_utils_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/bases/utils.py</a></td>
                    <td>28</td>
                    <td>0</td>
                    <td>14</td>
                    <td class="right" data-ratio="28 28">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_2ab4bfb8124a6a45_bessel_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/bessel.py</a></td>
                    <td>132</td>
                    <td>0</td>
                    <td>14</td>
                    <td class="right" data-ratio="132 132">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_2ab4bfb8124a6a45_differentiate_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/differentiate.py</a></td>
                    <td>61</td>
                    <td>2</td>
                    <td>0</td>
                    <td class="right" data-ratio="59 61">97%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_1082079def8de7e7___init___py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/integrate/__init__.py</a></td>
                    <td>215</td>
                    <td>12</td>
                    <td>16</td>
                    <td class="right" data-ratio="203 215">94%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_2ab4bfb8124a6a45_linalg_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/linalg.py</a></td>
                    <td>12</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="12 12">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_2ab4bfb8124a6a45_special_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/special.py</a></td>
                    <td>42</td>
                    <td>12</td>
                    <td>0</td>
                    <td class="right" data-ratio="30 42">71%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_2ab4bfb8124a6a45_wigner_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/math/wigner.py</a></td>
                    <td>20</td>
                    <td>2</td>
                    <td>0</td>
                    <td class="right" data-ratio="18 20">90%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_37318ec43babbc61_optimize_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/optimize.py</a></td>
                    <td>26</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="26 26">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_37318ec43babbc61_parallel_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/parallel.py</a></td>
                    <td>129</td>
                    <td>5</td>
                    <td>8</td>
                    <td class="right" data-ratio="124 129">96%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_20a77a2883a54c23___init___py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/performance/__init__.py</a></td>
                    <td>19</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="19 19">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_20a77a2883a54c23_blas_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/performance/blas.py</a></td>
                    <td>58</td>
                    <td>0</td>
                    <td>6</td>
                    <td class="right" data-ratio="58 58">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_20a77a2883a54c23_fft_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/performance/fft.py</a></td>
                    <td>168</td>
                    <td>5</td>
                    <td>7</td>
                    <td class="right" data-ratio="163 168">97%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_20a77a2883a54c23_numexpr_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/performance/numexpr.py</a></td>
                    <td>9</td>
                    <td>0</td>
                    <td>8</td>
                    <td class="right" data-ratio="9 9">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_20a77a2883a54c23_threads_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/performance/threads.py</a></td>
                    <td>9</td>
                    <td>0</td>
                    <td>8</td>
                    <td class="right" data-ratio="9 9">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_7348379a055a9ba7___init___py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/plot/__init__.py</a></td>
                    <td>5</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="5 5">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_7348379a055a9ba7_animation_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/plot/animation.py</a></td>
                    <td>81</td>
                    <td>16</td>
                    <td>0</td>
                    <td class="right" data-ratio="65 81">80%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_7348379a055a9ba7_cmaps_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/plot/cmaps.py</a></td>
                    <td>10</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="10 10">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_7348379a055a9ba7_colors_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/plot/colors.py</a></td>
                    <td>84</td>
                    <td>7</td>
                    <td>0</td>
                    <td class="right" data-ratio="77 84">92%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_7348379a055a9ba7_contour_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/plot/contour.py</a></td>
                    <td>63</td>
                    <td>24</td>
                    <td>0</td>
                    <td class="right" data-ratio="39 63">62%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_7348379a055a9ba7_errors_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/plot/errors.py</a></td>
                    <td>79</td>
                    <td>27</td>
                    <td>0</td>
                    <td class="right" data-ratio="52 79">66%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_7348379a055a9ba7_publish_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/plot/publish.py</a></td>
                    <td>326</td>
                    <td>137</td>
                    <td>0</td>
                    <td class="right" data-ratio="189 326">58%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_7348379a055a9ba7_rasterize_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/plot/rasterize.py</a></td>
                    <td>23</td>
                    <td>6</td>
                    <td>0</td>
                    <td class="right" data-ratio="17 23">74%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_e8e3792c39eb018a___init___py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/solve/__init__.py</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="0 0">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_e8e3792c39eb018a_broyden_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/solve/broyden.py</a></td>
                    <td>325</td>
                    <td>66</td>
                    <td>0</td>
                    <td class="right" data-ratio="259 325">80%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_37318ec43babbc61_testing_py.html">.nox/test-3-11/lib/python3.11/site-packages/mmfutils/testing.py</a></td>
                    <td>18</td>
                    <td>2</td>
                    <td>2</td>
                    <td class="right" data-ratio="16 18">89%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_430eb520d66b91e6___init___py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/__init__.py</a></td>
                    <td>18</td>
                    <td>2</td>
                    <td>2</td>
                    <td class="right" data-ratio="16 18">89%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_430eb520d66b91e6_containers_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/containers.py</a></td>
                    <td>113</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="113 113">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_430eb520d66b91e6_contexts_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/contexts.py</a></td>
                    <td>312</td>
                    <td>27</td>
                    <td>2</td>
                    <td class="right" data-ratio="285 312">91%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_430eb520d66b91e6_debugging_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/debugging.py</a></td>
                    <td>49</td>
                    <td>0</td>
                    <td>3</td>
                    <td class="right" data-ratio="49 49">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_430eb520d66b91e6_interface_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/interface.py</a></td>
                    <td>77</td>
                    <td>0</td>
                    <td>16</td>
                    <td class="right" data-ratio="77 77">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_1f41b71b360dc242___init___py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/__init__.py</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="0 0">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_c3712e7c3a436e01___init___py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/bases/__init__.py</a></td>
                    <td>2</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="2 2">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_c3712e7c3a436e01_bases_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/bases/bases.py</a></td>
                    <td>463</td>
                    <td>59</td>
                    <td>0</td>
                    <td class="right" data-ratio="404 463">87%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_c3712e7c3a436e01_interfaces_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/bases/interfaces.py</a></td>
                    <td>41</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="41 41">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_c3712e7c3a436e01_utils_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/bases/utils.py</a></td>
                    <td>28</td>
                    <td>0</td>
                    <td>14</td>
                    <td class="right" data-ratio="28 28">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_1f41b71b360dc242_bessel_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/bessel.py</a></td>
                    <td>132</td>
                    <td>0</td>
                    <td>14</td>
                    <td class="right" data-ratio="132 132">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_1f41b71b360dc242_differentiate_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/differentiate.py</a></td>
                    <td>61</td>
                    <td>2</td>
                    <td>0</td>
                    <td class="right" data-ratio="59 61">97%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_bf5d796325f94311___init___py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/integrate/__init__.py</a></td>
                    <td>215</td>
                    <td>12</td>
                    <td>16</td>
                    <td class="right" data-ratio="203 215">94%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_1f41b71b360dc242_linalg_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/linalg.py</a></td>
                    <td>12</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="12 12">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_1f41b71b360dc242_special_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/special.py</a></td>
                    <td>42</td>
                    <td>12</td>
                    <td>0</td>
                    <td class="right" data-ratio="30 42">71%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_1f41b71b360dc242_wigner_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/math/wigner.py</a></td>
                    <td>20</td>
                    <td>2</td>
                    <td>0</td>
                    <td class="right" data-ratio="18 20">90%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_430eb520d66b91e6_optimize_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/optimize.py</a></td>
                    <td>26</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="26 26">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_430eb520d66b91e6_parallel_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/parallel.py</a></td>
                    <td>129</td>
                    <td>5</td>
                    <td>8</td>
                    <td class="right" data-ratio="124 129">96%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_292b785e7e29d698___init___py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/performance/__init__.py</a></td>
                    <td>19</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="19 19">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_292b785e7e29d698_blas_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/performance/blas.py</a></td>
                    <td>58</td>
                    <td>0</td>
                    <td>6</td>
                    <td class="right" data-ratio="58 58">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_292b785e7e29d698_fft_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/performance/fft.py</a></td>
                    <td>168</td>
                    <td>5</td>
                    <td>7</td>
                    <td class="right" data-ratio="163 168">97%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_292b785e7e29d698_numexpr_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/performance/numexpr.py</a></td>
                    <td>9</td>
                    <td>0</td>
                    <td>8</td>
                    <td class="right" data-ratio="9 9">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_292b785e7e29d698_threads_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/performance/threads.py</a></td>
                    <td>9</td>
                    <td>0</td>
                    <td>8</td>
                    <td class="right" data-ratio="9 9">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_97c7e4624ef219ca___init___py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/plot/__init__.py</a></td>
                    <td>5</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="5 5">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_97c7e4624ef219ca_animation_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/plot/animation.py</a></td>
                    <td>81</td>
                    <td>18</td>
                    <td>0</td>
                    <td class="right" data-ratio="63 81">78%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_97c7e4624ef219ca_cmaps_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/plot/cmaps.py</a></td>
                    <td>10</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="10 10">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_97c7e4624ef219ca_colors_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/plot/colors.py</a></td>
                    <td>84</td>
                    <td>7</td>
                    <td>0</td>
                    <td class="right" data-ratio="77 84">92%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_97c7e4624ef219ca_contour_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/plot/contour.py</a></td>
                    <td>63</td>
                    <td>24</td>
                    <td>0</td>
                    <td class="right" data-ratio="39 63">62%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_97c7e4624ef219ca_errors_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/plot/errors.py</a></td>
                    <td>79</td>
                    <td>27</td>
                    <td>0</td>
                    <td class="right" data-ratio="52 79">66%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_97c7e4624ef219ca_publish_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/plot/publish.py</a></td>
                    <td>326</td>
                    <td>137</td>
                    <td>0</td>
                    <td class="right" data-ratio="189 326">58%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_97c7e4624ef219ca_rasterize_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/plot/rasterize.py</a></td>
                    <td>23</td>
                    <td>6</td>
                    <td>0</td>
                    <td class="right" data-ratio="17 23">74%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_f3231d1114133c0b___init___py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/solve/__init__.py</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="0 0">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_f3231d1114133c0b_broyden_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/solve/broyden.py</a></td>
                    <td>325</td>
                    <td>66</td>
                    <td>0</td>
                    <td class="right" data-ratio="259 325">80%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_430eb520d66b91e6_testing_py.html">.nox/test-3-12/lib/python3.12/site-packages/mmfutils/testing.py</a></td>
                    <td>18</td>
                    <td>2</td>
                    <td>2</td>
                    <td class="right" data-ratio="16 18">89%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_24cb80c982ce9cd7___init___py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/__init__.py</a></td>
                    <td>18</td>
                    <td>2</td>
                    <td>2</td>
                    <td class="right" data-ratio="16 18">89%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_24cb80c982ce9cd7_containers_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/containers.py</a></td>
                    <td>113</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="113 113">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_24cb80c982ce9cd7_contexts_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/contexts.py</a></td>
                    <td>312</td>
                    <td>27</td>
                    <td>2</td>
                    <td class="right" data-ratio="285 312">91%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_24cb80c982ce9cd7_debugging_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/debugging.py</a></td>
                    <td>49</td>
                    <td>0</td>
                    <td>3</td>
                    <td class="right" data-ratio="49 49">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_24cb80c982ce9cd7_interface_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/interface.py</a></td>
                    <td>77</td>
                    <td>0</td>
                    <td>16</td>
                    <td class="right" data-ratio="77 77">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_82e13d4a02664b00___init___py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/__init__.py</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="0 0">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_e4da03c3f7bf123e___init___py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/bases/__init__.py</a></td>
                    <td>2</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="2 2">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_e4da03c3f7bf123e_bases_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/bases/bases.py</a></td>
                    <td>463</td>
                    <td>59</td>
                    <td>0</td>
                    <td class="right" data-ratio="404 463">87%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_e4da03c3f7bf123e_interfaces_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/bases/interfaces.py</a></td>
                    <td>41</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="41 41">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_e4da03c3f7bf123e_utils_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/bases/utils.py</a></td>
                    <td>28</td>
                    <td>0</td>
                    <td>14</td>
                    <td class="right" data-ratio="28 28">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_82e13d4a02664b00_bessel_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/bessel.py</a></td>
                    <td>131</td>
                    <td>0</td>
                    <td>14</td>
                    <td class="right" data-ratio="131 131">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_82e13d4a02664b00_differentiate_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/differentiate.py</a></td>
                    <td>61</td>
                    <td>2</td>
                    <td>0</td>
                    <td class="right" data-ratio="59 61">97%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_434a14a59d2b7650___init___py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/integrate/__init__.py</a></td>
                    <td>213</td>
                    <td>12</td>
                    <td>16</td>
                    <td class="right" data-ratio="201 213">94%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_82e13d4a02664b00_linalg_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/linalg.py</a></td>
                    <td>12</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="12 12">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_82e13d4a02664b00_special_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/special.py</a></td>
                    <td>42</td>
                    <td>12</td>
                    <td>0</td>
                    <td class="right" data-ratio="30 42">71%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_82e13d4a02664b00_wigner_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/math/wigner.py</a></td>
                    <td>20</td>
                    <td>2</td>
                    <td>0</td>
                    <td class="right" data-ratio="18 20">90%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_24cb80c982ce9cd7_optimize_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/optimize.py</a></td>
                    <td>26</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="26 26">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_24cb80c982ce9cd7_parallel_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/parallel.py</a></td>
                    <td>128</td>
                    <td>5</td>
                    <td>8</td>
                    <td class="right" data-ratio="123 128">96%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_fceb832163e82c1b___init___py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/performance/__init__.py</a></td>
                    <td>19</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="19 19">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_fceb832163e82c1b_blas_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/performance/blas.py</a></td>
                    <td>58</td>
                    <td>0</td>
                    <td>6</td>
                    <td class="right" data-ratio="58 58">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_fceb832163e82c1b_fft_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/performance/fft.py</a></td>
                    <td>168</td>
                    <td>5</td>
                    <td>7</td>
                    <td class="right" data-ratio="163 168">97%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_fceb832163e82c1b_numexpr_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/performance/numexpr.py</a></td>
                    <td>9</td>
                    <td>0</td>
                    <td>8</td>
                    <td class="right" data-ratio="9 9">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_fceb832163e82c1b_threads_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/performance/threads.py</a></td>
                    <td>9</td>
                    <td>0</td>
                    <td>8</td>
                    <td class="right" data-ratio="9 9">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3622dda1e2759c5f___init___py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/plot/__init__.py</a></td>
                    <td>5</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="5 5">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3622dda1e2759c5f_animation_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/plot/animation.py</a></td>
                    <td>81</td>
                    <td>18</td>
                    <td>0</td>
                    <td class="right" data-ratio="63 81">78%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3622dda1e2759c5f_cmaps_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/plot/cmaps.py</a></td>
                    <td>10</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="10 10">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3622dda1e2759c5f_colors_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/plot/colors.py</a></td>
                    <td>85</td>
                    <td>8</td>
                    <td>0</td>
                    <td class="right" data-ratio="77 85">91%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3622dda1e2759c5f_contour_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/plot/contour.py</a></td>
                    <td>63</td>
                    <td>24</td>
                    <td>0</td>
                    <td class="right" data-ratio="39 63">62%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3622dda1e2759c5f_errors_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/plot/errors.py</a></td>
                    <td>78</td>
                    <td>26</td>
                    <td>0</td>
                    <td class="right" data-ratio="52 78">67%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3622dda1e2759c5f_publish_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/plot/publish.py</a></td>
                    <td>327</td>
                    <td>139</td>
                    <td>0</td>
                    <td class="right" data-ratio="188 327">57%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_3622dda1e2759c5f_rasterize_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/plot/rasterize.py</a></td>
                    <td>23</td>
                    <td>6</td>
                    <td>0</td>
                    <td class="right" data-ratio="17 23">74%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_46d366db1deca0d6___init___py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/solve/__init__.py</a></td>
                    <td>0</td>
                    <td>0</td>
                    <td>0</td>
                    <td class="right" data-ratio="0 0">100%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_46d366db1deca0d6_broyden_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/solve/broyden.py</a></td>
                    <td>325</td>
                    <td>66</td>
                    <td>0</td>
                    <td class="right" data-ratio="259 325">80%</td>
                </tr>
                <tr class="region">
                    <td class="name left"><a href="z_24cb80c982ce9cd7_testing_py.html">.nox/test-3-9/lib/python3.9/site-packages/mmfutils/testing.py</a></td>
                    <td>18</td>
                    <td>2</td>
                    <td>2</td>
                    <td class="right" data-ratio="16 18">89%</td>
                </tr>
            </tbody>
            <tfoot>
                <tr class="total">
                    <td class="name left">Total</td>
                    <td>12068</td>
                    <td>1656</td>
                    <td>424</td>
                    <td class="right" data-ratio="10412 12068">86%</td>
                </tr>
            </tfoot>
        </table>
        <p id="no_rows">
            No items found using the specified filter.
        </p>
    </main>
    <footer>
        <div class="content">
            <p>
                <a class="nav" href="https://coverage.readthedocs.io/en/7.6.10">coverage.py v7.6.10</a>,
                created at 2024-12-29 01:07 -0800
            </p>
        </div>
        <aside class="hidden">
            <a id="prevFileLink" class="nav" href="z_24cb80c982ce9cd7_testing_py.html"></a>
            <a id="nextFileLink" class="nav" href="z_d79ac605fce24c24___init___py.html"></a>
            <button type="button" class="button_prev_file" data-shortcut="["></button>
            <button type="button" class="button_next_file" data-shortcut="]"></button>
            <button type="button" class="button_show_hide_help" data-shortcut="?"></button>
        </aside>
    </footer>
    </body>
    </html>




Change Log
==========

REL: 0.6.7
----------

-  Add derivative ``d=1`` support for step and mstep. Remove floating
   point warning.
-  Improved FPS context: better sleeping timing and default timeout
   behavior.
-  Drop support for python 3.9 and below. (Could work, but dependencies
   need careful thought and version pinning.)
-  Added IBasisCutoff to allow working with the Galerkin projected GPE.
-  Updated some tests to work with new Numpy formatting (See `NEP
   51 <https://numpy.org/neps/nep-0051-scalar-representation.html>`__.)
-  Fixed broken rasterization in contourf but should be unnecessary in
   the future (see
   https://github.com/matplotlib/matplotlib/issues/27669).
-  Improved ``performance.auto_timeit``.
-  Revert to installing pyfftw from default repo now that `issue
   303 <https://github.com/pyFFTW/pyFFTW/issues/303>`__ is fixed.

REL: 0.6.6
----------

-  Fix issue #31: FFT falbacks should work even if pyfftw is not
   installed. (Monkeypatch this case in ``test_performance_fft.py``)
-  Fix issue #32: Make copy of arrays before calling pyfftw builders for
   the convenience functions to ensure that everything works, even if
   they are not ``WRITEABLE``.

REL: 0.6.5
----------

-  Fix issue #30: measure fft performance and fallback to numpy (with a
   warning) if it is faster than pyfftw.

REL: 0.6.4
----------

-  Support python 3.7.13 through 3.11.
-  Fix some tests.
-  Add ``contexts.FPS`` which is generally preferred to ``NoInterrupt``.
-  Add a ``timeout=`` argument to contexts.
-  Unbind versions.
-  Fix a couple of bugs in ``math.bases.bases.py``:

   -  Actually use ``memoization_GB``.
   -  ``PeriodicBasis.kx`` is now a property.

REL: 0.6.3
----------

-  Fix some dependencies.

REL: 0.6.2
----------

-  Fix some issues with GPU and PeriodicBases.
-  Add warning to FFT plans about data ownership.
-  Include some Sparkline demonstrations.
-  Drop support for Python 3.6. (Still no support for 3.10).

REL: 0.6.0
----------

-  Use Poetry for dependency management.
-  Update to ``src/mmfutils`` layout.
-  Better testing and coverage, including GitHub CI.
-  Odd-numbered lattices are now centered at 0.
-  Added ``fftw`` extra.

REL: 0.5.4
----------

-  Drop support for Python 3.5.
-  Use `Nox <https://nox.thea.codes>`__ for testing (see
   `Notes.md <../Notes.md>`__)

REL: 0.5.3
----------

Allow Python 3.8. Previous version required ``python <= 3.7`` due to an
`issue with
ipyparallel <https://github.com/ipython/ipyparallel/issues/396>`__. This
has been resolved with revision 6.2.5 which is available with ``conda``.

REL: 0.5.1
----------

API changes:

-  Split ``mmfutils.containers.Object`` into ``ObjectBase`` which is
   simple and ``ObjectMixin`` which provides the picking support.
   Demonstrate in docs how the pickling can be useful, but slows
   copying.

REL: 0.5.0
----------

API changes:

-  Python 3 support only.
-  ``mmfutils.math.bases.interface`` renamed to
   ``mmfutils.math.bases.interfaces``.
-  Added default class-variable attribute support to
   e\ ``mmfutils.containers.Object``.
-  Minor enhancements to ``mmfutils.math.bases.PeriodicBasis`` to
   enhance GPU support.
-  Added ``mmfutils.math.bases.interfaces.IBasisLz`` and support in
   ``mmfutils.math.bases.bases.PeriodicBasis`` for rotating frames.
-  Cleanup of build environment and tests.

   -  Single environment ``_mmfutils`` now used for testing and
      documentation.

REL: 0.4.13
-----------

API changes:

-  Use ``@implementer()`` class decorator rather than
   ``classImplements`` or ``implements`` in all interfaces.
-  Improve ``NoInterrupt`` context. Added ``NoInterrupt.unregister()``:
   this allows ``NoInterrupt`` to work in a notebook cell even when the
   signal handlers are reset. (But only works in that one cell.)
-  Added Abel transform ``integrate2`` to Cylindrical bases.

Issues:

-  Resolved issue #22: Masked arrays work with ``imcontourf`` etc.
-  Resolved issue #23: ``NoInterrupt`` works well except in notebooks
   due to `ipykernel issue
   #328 <https://github.com/ipython/ipykernel/issues/328>`__.
-  Resolved issue #24: Python 3 is now fully supported and tested.

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
