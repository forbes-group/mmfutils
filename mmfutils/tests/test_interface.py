import nose.tools as nt

import zope.interface.document
import zope.interface.exceptions

from mmfutils.interface import (implements, verifyObject, verifyClass,
                                Interface, Attribute)


class IInterfaceTest(Interface):
    """Dummy interface for testing"""
    p = Attribute('p', "Power")

    def required_method(a, b):
        """Return a+b computed appropriately"""


class BrokenInterfaceTest1(object):
    implements(IInterfaceTest)

    # Note, don't break both attribute and method interfaces at the same time
    # because the verifyObject() test relies on dictionary ordering and might
    # raise BrokenMethodImplementation or BrokenImplementation quasi-randomly
    p = 1.0

    def required_method(self, a):
        # Wrong number of arguments
        return a


class BrokenInterfaceTest2(object):
    implements(IInterfaceTest)

    # Missing p
    def required_method(self, a, b):
        return a + b


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
        verifyClass(IInterfaceTest, BrokenInterfaceTest1)

    @nt.raises(zope.interface.exceptions.BrokenMethodImplementation)
    def test_verifyBrokenObject1(self):
        o = BrokenInterfaceTest1()
        verifyObject(IInterfaceTest, o)

    @nt.raises(zope.interface.exceptions.BrokenImplementation)
    def test_verifyBrokenObject2(self):
        o = BrokenInterfaceTest2()
        verifyObject(IInterfaceTest, o)


class Doctests(object):
    """
    >>> from zope.interface.document import asStructuredText
    >>> from mmfutils.interface import Interface, Attribute
    >>> class IInterface1(Interface):
    ...     "IInterface1"
    ...     offset = Attribute('offset', "Offset")
    >>> class IInterface2(IInterface1):
    ...     p = Attribute('p', "Power")
    ...     def required_method(a, b):
    ...         "Return (a+b)**p + offset"
    >>> print(asStructuredText(IInterface1))
    ``IInterface1``
    <BLANKLINE>
    IInterface1
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
