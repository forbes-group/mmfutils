
1. MMF Utils
============

Small set of utilities: containers and interfaces.

This package provides some utilities that I tend to rely on during
development. Presently in includes some convenience containers and a
patch for including
`zope.interface <http://docs.zope.org/zope.interface/>`__ documentation
in a notebook.

**Documentation:** http://mmfutils.readthedocs.org

**Source:** https://bitbucket.org/mforbes/mmfutils

**Issues:** https://bitbucket.org/mforbes/mmfutils/issues

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
                self.k[self.N/2.0] = 0.0
                
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

    115
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

    <ipython-input-14-cbfd03ed340e> in <module>()
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


.. parsed-literal::

    INFO:root:Patching zope.interface.document.asStructuredText to format code


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
to provide a mechanism for documentating interfaces in a notebook. This
still requires a bit of work to convert the string to HTML for display
using ``docutils``:

.. code:: python

    # Chunk of code to display interfaces.
    # See: http://code.activestate.com/recipes/
    #            193890-using-rest-restructuredtext-to-create-html-snippet/
    import IPython.display
    
    from docutils import core
    from docutils.writers.html4css1 import Writer, HTMLTranslator
    
    import zope.interface.document
    
    
    class NoHeaderHTMLTranslator(HTMLTranslator):
        def __init__(self, document):
            HTMLTranslator.__init__(self, document)
            self.head_prefix = ['']*5
            self.body_prefix = []
            self.body_suffix = []
            self.stylesheet = []
    
    
    _w = Writer()
    _w.translator_class = NoHeaderHTMLTranslator
    
    
    def reSTify(string):
        return IPython.display.HTML(core.publish_string(string, writer=_w))
    
    
    def describe_interface(interface):
        rst = zope.interface.document.asStructuredText(interface)
        return IPython.display.display(reSTify(rst))

Now we can show the interface in our documentation:

.. code:: python

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
    client = cluster.wait()  # Instance of IPython.parallel.Client
    view = client.load_balanced_view()
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
        view = client.load_balanced_view()
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
    [NbConvertApp] Writing 17392 bytes to README.rst


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

    running test
    /Users/mforbes/.anaconda/lib/python2.7/site-packages/distribute-0.6.27-py2.7.egg/setuptools/dist.py:247: UserWarning: Module flake8 was already imported from /Users/mforbes/.anaconda/lib/python2.7/site-packages/flake8/__init__.pyc, but /Users/mforbes/work/mmfbb/pytimeode/flake8-2.4.0-py2.7.egg is being added to sys.path
    /Users/mforbes/.anaconda/lib/python2.7/site-packages/distribute-0.6.27-py2.7.egg/setuptools/dist.py:247: UserWarning: Module pep8 was already imported from /Users/mforbes/.anaconda/lib/python2.7/site-packages/pep8.pyc, but /Users/mforbes/work/mmfbb/pytimeode/pep8-1.5.7-py2.7.egg is being added to sys.path
    running nosetests
    running egg_info
    writing requirements to mmfutils.egg-info/requires.txt
    writing mmfutils.egg-info/PKG-INFO
    writing top-level names to mmfutils.egg-info/top_level.txt
    writing dependency_links to mmfutils.egg-info/dependency_links.txt
    writing requirements to mmfutils.egg-info/requires.txt
    writing mmfutils.egg-info/PKG-INFO
    writing top-level names to mmfutils.egg-info/top_level.txt
    writing dependency_links to mmfutils.egg-info/dependency_links.txt
    reading manifest file 'mmfutils.egg-info/SOURCES.txt'
    writing manifest file 'mmfutils.egg-info/SOURCES.txt'
    nose.config: INFO: Set working dir to /Users/mforbes/work/mmfbb/mmfutils
    nose.config: INFO: Ignoring files matching ['^\\.', '^_', '^setup\\.py$']
    nose.plugins.cover: INFO: Coverage report will include only packages: ['mmfutils']
    nose.plugins.cover: INFO: Coverage report will include only packages: ['mmfutils']
    INFO:root:Patching zope.interface.document.asStructuredText to format code
    INFO:root:Patching flake8 for issues 39 and 40
    Doctest: mmfutils.containers.Container ... ok
    Doctest: mmfutils.containers.ContainerDict ... ok
    Doctest: mmfutils.containers.ContainerList ... ok
    mmfutils.tests.test_containers.TestContainer.test_container_delattr ... ok
    Test persistent representation of object class ... ok
    mmfutils.tests.test_containers.TestContainerConversion.test_conversions ... ok
    mmfutils.tests.test_containers.TestContainerDict.test_container_del ... ok
    mmfutils.tests.test_containers.TestContainerDict.test_container_setitem ... ok
    mmfutils.tests.test_containers.TestContainerList.test_container_delitem ... ok
    mmfutils.tests.test_containers.TestObject.test_empty_object ... ok
    Test persistent representation of object class ... ok
    mmfutils.tests.test_containers.TestPersist.test_archive ... ok
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
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/ipython_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/ipython_kernel_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/ipython_console_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/ipython_qtconsole_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/ipython_notebook_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/ipython_nbconvert_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/ipcontroller_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/ipengine_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/ipcluster_config.py'
    [ProfileCreate] Generating default config file: u'/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml/profile_testing/iplogger_config.py'
    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=testing1 --n=7 --ipython-dir="/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml"
    INFO:root:Starting cluster: ipcluster start --daemonize --quiet --profile=testing2 --n=3 --ipython-dir="/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml"
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    WARNING:root:No ipcontroller-client.json, waiting...
    INFO:root:waiting for 3 engines
    INFO:root:0 of 3 running
    INFO:root:3 of 3 running
    INFO:root:waiting for 7 engines
    INFO:root:7 of 7 running
    Simple test connecting to a cluster. ... ok
    Test that starting a running cluster does nothing. ... ok
    Test that the PBS_NODEFILE is used if defined ... ok
    Test timeout (coverage) ... ok
    INFO:root:Stopping cluster: ipcluster stop --profile=testing2 --ipython-dir="/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml"
    2015-04-28 10:22:59.830 [IPClusterStop] Stopping cluster [pid=42033] with [signal=2]
    INFO:root:Stopping cluster: ipcluster stop --profile=testing1 --ipython-dir="/var/folders/m7/dnr91tjs4gn58_t3k8zp_g000000gn/T/tmpdrrGml"
    2015-04-28 10:23:00.136 [IPClusterStop] Stopping cluster [pid=42025] with [signal=2]
    
    Name                        Stmts   Miss  Cover   Missing
    ---------------------------------------------------------
    mmfutils.py                     1      0   100%   
    mmfutils/containers.py         73      0   100%   
    mmfutils/interface.py          47      0   100%   
    mmfutils/monkeypatches.py      12      0   100%   
    mmfutils/parallel.py           89      0   100%   
    ---------------------------------------------------------
    TOTAL                         222      0   100%   
    ----------------------------------------------------------------------
    Ran 24 tests in 10.458s
    
    OK
    running flake8
    running check


Complete code coverage information is provided in
``build/_coverage/index.html``.

.. code:: python

    from IPython.display import HTML
    with open(os.path.join(ROOTDIR, 'build/_coverage/index.html')) as f:
        coverage = f.read()
    HTML(coverage)




.. raw:: html

    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
        <title>Coverage report</title>
        <link rel='stylesheet' href='style.css' type='text/css'>
        
        <script type='text/javascript' src='jquery.min.js'></script>
        <script type='text/javascript' src='jquery.debounce.min.js'></script>
        <script type='text/javascript' src='jquery.tablesorter.min.js'></script>
        <script type='text/javascript' src='jquery.hotkeys.js'></script>
        <script type='text/javascript' src='coverage_html.js'></script>
        <script type='text/javascript'>
            jQuery(document).ready(coverage.index_ready);
        </script>
    </head>
    <body class='indexfile'>
    
    <div id='header'>
        <div class='content'>
            <h1>Coverage report:
                <span class='pc_cov'>100%</span>
            </h1>
    
            <img id='keyboard_icon' src='keybd_closed.png' alt='Show keyboard shortcuts' />
    
            <form id="filter_container">
                <input id="filter" type="text" value="" placeholder="filter..." />
            </form>
        </div>
    </div>
    
    <div class='help_panel'>
        <img id='panel_icon' src='keybd_open.png' alt='Hide keyboard shortcuts' />
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
                    <td>222</td>
                    <td>0</td>
                    <td>26</td>
                    
                    <td class='right' data-ratio='222 222'>100%</td>
                </tr>
            </tfoot>
            <tbody>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_py.html'>mmfutils.py</a></td>
                    <td>1</td>
                    <td>0</td>
                    <td>0</td>
                    
                    <td class='right' data-ratio='1 1'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_containers_py.html'>mmfutils/containers.py</a></td>
                    <td>73</td>
                    <td>0</td>
                    <td>0</td>
                    
                    <td class='right' data-ratio='73 73'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_interface_py.html'>mmfutils/interface.py</a></td>
                    <td>47</td>
                    <td>0</td>
                    <td>14</td>
                    
                    <td class='right' data-ratio='47 47'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_monkeypatches_py.html'>mmfutils/monkeypatches.py</a></td>
                    <td>12</td>
                    <td>0</td>
                    <td>4</td>
                    
                    <td class='right' data-ratio='12 12'>100%</td>
                </tr>
                
                <tr class='file'>
                    <td class='name left'><a href='mmfutils_parallel_py.html'>mmfutils/parallel.py</a></td>
                    <td>89</td>
                    <td>0</td>
                    <td>8</td>
                    
                    <td class='right' data-ratio='89 89'>100%</td>
                </tr>
                
            </tbody>
        </table>
    
        <p id="no_rows">
            No items found using the specified filter.
        </p>
    </div>
    
    <div id='footer'>
        <div class='content'>
            <p>
                <a class='nav' href='https://coverage.readthedocs.org/en/4.0a6'>coverage.py v4.0a6</a>
            </p>
        </div>
    </div>
    
    </body>
    </html>



