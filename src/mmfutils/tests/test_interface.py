import pytest
import zope.interface.document
import zope.interface.exceptions

from mmfutils.interface import (
    implementer,
    verifyObject,
    verifyClass,
    Interface,
    Attribute,
)


class IInterfaceTest(Interface):
    """Dummy interface for testing"""

    p = Attribute("p", "Power")

    def required_method(a, b):
        """Return a+b computed appropriately"""


@implementer(IInterfaceTest)
class BrokenInterfaceTest1(object):
    # Note, don't break both attribute and method interfaces at the same time
    # because the verifyObject() test relies on dictionary ordering and might
    # raise BrokenMethodImplementation or BrokenImplementation quasi-randomly
    p = 1.0

    def required_method(self, a):
        # Wrong number of arguments
        return a


@implementer(IInterfaceTest)
class BrokenInterfaceTest2(object):
    # Missing p
    def required_method(self, a, b):
        return a + b


@implementer(IInterfaceTest)
class InterfaceTest(object):
    def __init__(self, p=1.0):
        self.p = p

    def required_method(self, a, b):
        return (a + b) ** self.p


class TestInterfaces(object):
    def test_verifyClass(self):
        verifyClass(IInterfaceTest, InterfaceTest)
        with pytest.raises(zope.interface.exceptions.BrokenMethodImplementation):
            verifyClass(IInterfaceTest, BrokenInterfaceTest1)

    def test_verifyObject(self):
        o = InterfaceTest()
        verifyObject(IInterfaceTest, o)

        o = BrokenInterfaceTest1()
        with pytest.raises(zope.interface.exceptions.BrokenMethodImplementation):
            verifyObject(IInterfaceTest, o)

        o = BrokenInterfaceTest2()
        with pytest.raises(zope.interface.exceptions.BrokenImplementation):
            verifyObject(IInterfaceTest, o)


class Doctests(object):
    """
    >>> from zope.interface.document import asReStructuredText
    >>> from mmfutils.interface import Interface, Attribute
    >>> class IInterface1(Interface):
    ...     "IInterface1"
    ...     offset = Attribute('offset', "Offset")
    >>> class IInterface2(IInterface1):
    ...     p = Attribute('p', "Power")
    ...     def required_method(a, b):
    ...         "Return (a+b)**p + offset"
    >>> print(asReStructuredText(IInterface1))
    ``IInterface1``
    <BLANKLINE>
     IInterface1
    <BLANKLINE>
     Attributes:
    <BLANKLINE>
      ``offset`` -- Offset
    <BLANKLINE>
     Methods:
    <BLANKLINE>
    <BLANKLINE>
    >>> print(asReStructuredText(IInterface2))
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
