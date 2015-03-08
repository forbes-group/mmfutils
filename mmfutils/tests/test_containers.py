import pickle
import nose.tools as nt

import zope.interface.document
import zope.interface.exceptions

from mmfutils.interface import (implements, verifyObject, verifyClass,
                                Interface, Attribute)
from mmfutils.containers import Object, Container


class TestContainer(object):
    def test_container_persist(self):
        """Test persistent representation of object class"""

        o = Container(c=[1, 2, 3], a=1, b="b")
        o.dont_store_this = "BAD"

        o1 = pickle.loads(pickle.dumps(o))
        nt.eq_(repr(o), repr(o1))
        nt.ok_(hasattr(o, 'dont_store_this'))
        nt.ok_(not hasattr(o1, 'dont_store_this'))


class MyObject(Object):
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
        Object.__init__(self)


class TestObject(object):
    def test_object_persist(self):
        """Test persistent representation of object class"""

        o = MyObject(c=[1, 2, 3], a=1, b="b")
        o.dont_store_this = "BAD"

        o1 = pickle.loads(pickle.dumps(o))
        nt.eq_(repr(o), repr(o1))
        nt.ok_(hasattr(o, 'dont_store_this'))
        nt.ok_(not hasattr(o1, 'dont_store_this'))


class TestPersist(object):
    def test_archive(self):
        o = MyObject(c=[1, 2, 3], a=1, b="b")
        o.dont_store_this = "BAD"

        import persist.archive  # May not be installed
        a = persist.archive.Archive()
        a.insert(o=o)

        d = {}
        exec str(a) in d
        o1 = d['o']

        nt.eq_(repr(o), repr(o1))
        nt.ok_(hasattr(o, 'dont_store_this'))
        nt.ok_(not hasattr(o1, 'dont_store_this'))


class IInterfaceTest(Interface):
    """Dummy interface for testing"""
    p = Attribute('p', "Power")

    def required_method(a, b):
        """Return a+b computed appropriately"""


class BrokenInterfaceTest(object):
    implements(IInterfaceTest)

    def required_method(self, a):
        # Wrong number of arguments
        return a


class InterfaceTest(object):
    implements(IInterfaceTest)

    def __init__(self, p=1.0):
        self.p = p

    def required_method(self, a, b):
        return (a + b)**self.p


class TestInterfaces(object):
    def test_verifyClass(self):
        verifyClass(IInterfaceTest, InterfaceTest)

    def test_verifyObject(self):
        o = InterfaceTest()
        verifyObject(IInterfaceTest, o)

    @nt.raises(zope.interface.exceptions.BrokenMethodImplementation)
    def test_verifyBrokenClass(self):
        verifyClass(IInterfaceTest, BrokenInterfaceTest)

    @nt.raises(zope.interface.exceptions.BrokenImplementation)
    def test_verifyBrokenObject(self):
        o = BrokenInterfaceTest()
        verifyObject(IInterfaceTest, o)


class Doctests(object):
    """
    >>> from zope.interface.document import asStructuredText
    >>> from mmfutils.interface import Interface, Attribute
    >>> class IInterface1(Interface):
    ...     offset = Attribute('offset', "Offset")
    >>> class IInterface2(IInterface1):
    ...     p = Attribute('p', "Power")
    ...     def required_method(a, b):
    ...         "Return (a+b)**p + offset"
    >>> print(asStructuredText(IInterface1))
    ``IInterface1``
    <BLANKLINE>
     Attributes:
    <BLANKLINE>
      ``offset`` -- Offset
    <BLANKLINE>
    <BLANKLINE>
    >>> print(asStructuredText(IInterface2))
    ``IInterface2``
    <BLANKLINE>
     This interface extends:
    <BLANKLINE>
      o ``IInterface1``
    <BLANKLINE>
     Attributes:
    <BLANKLINE>
      ``p`` -- Power
    <BLANKLINE>
     Methods:
    <BLANKLINE>
      ``required_method(a, b)`` -- Return (a+b)**p + offset
    <BLANKLINE>
    <BLANKLINE>
    """
