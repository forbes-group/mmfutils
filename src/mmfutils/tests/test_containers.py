import pickle

from mmfutils.containers import Object, Container, ContainerList, ContainerDict

import pytest


class TestContainer(object):
    def test_container_persist(self):
        """Test persistent representation of object class"""

        o = Container(c=[1, 2, 3], a=1, b="b")
        o.dont_store_this = "BAD"

        o1 = pickle.loads(pickle.dumps(o))
        assert repr(o) == repr(o1)
        assert hasattr(o, "dont_store_this")
        assert not hasattr(o1, "dont_store_this")

    def test_container_delattr(self):
        # Not encouraged but provided
        c = Container(c=[1, 2, 3], a=1, b="b")
        del c.b
        assert "a" in c
        assert "b" not in c
        assert "c" in c

    def test_preserve_order_of_picklable_attributes(self):
        """Check that the order of attributes defined by
        picklable_attributes is preserved"""
        c = Container(a=1, b=2, c=3, picklable_attributes=["b", "a"])
        assert repr(c) == "Container(b=2, a=1)"
        c.picklable_attributes = ["a", "b"]
        assert repr(c) == "Container(a=1, b=2)"


class TestContainerList(object):
    def test_container_delitem(self):
        # Not encouraged but provided
        c = ContainerList(c=[1, 2, 3], a=1, b="b")
        del c[1]
        assert "a" in c
        assert "b" not in c
        assert "c" in c


class TestContainerDict(object):
    def test_container_del(self):
        # Not encouraged but provided
        c = ContainerDict(c=[1, 2, 3], a=1, b="b")
        del c["b"]
        assert "a" in c
        assert "b" not in c
        assert "c" in c

    def test_container_setitem(self):
        # Not encouraged but provided
        c = ContainerDict(c=[1, 2, 3], a=1, b="b")
        c["a"] = 3
        assert c.a == 3


class TestContainerConversion(object):
    @classmethod
    def setup_class(cls):
        cls.c = Container(a=1, c=[1, 2, 3], b="b")
        cls.cl = ContainerList(a=1, c=[1, 2, 3], b="b")
        cls.cd = ContainerDict(a=1, c=[1, 2, 3], b="b")
        cls.d = dict(a=1, c=[1, 2, 3], b="b")
        cls.l = [("a", 1), ("b", "b"), ("c", [1, 2, 3])]

    def check(self, c):
        assert self.c.__getstate__() == c.__getstate__()

    def test_conversions(self):
        self.check(Container(self.c))
        self.check(Container(self.cl))
        self.check(Container(self.cd))
        self.check(Container(self.l))
        self.check(Container(self.d))

        self.check(ContainerDict(self.c))
        self.check(ContainerDict(self.cl))
        self.check(ContainerDict(self.cd))
        self.check(ContainerDict(self.l))
        self.check(ContainerDict(self.d))

        self.check(ContainerList(self.c))
        self.check(ContainerList(self.cl))
        self.check(ContainerList(self.cd))
        self.check(ContainerList(self.l))
        self.check(ContainerList(self.d))


class MyObject(Object):
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
        super().__init__()


class MyEmptyObject(Object):
    """Has no attributes, but should have init() called"""

    def init(self):
        self.x = 5


class MyDefaultObject(Object):
    """Has default attributes."""

    x = 5

    def d(self):
        return 5


class MyStrictObject(MyObject):
    _strict = True


class TestObject(object):
    def test_object_persist(self):
        """Test persistent representation of object class"""

        o = MyObject(c=[1, 2, 3], a=1, b="b")
        o.dont_store_this = "BAD"

        o1 = pickle.loads(pickle.dumps(o))
        assert repr(o) == repr(o1)
        assert hasattr(o, "dont_store_this")
        assert not hasattr(o1, "dont_store_this")

    def test_empty_object(self):
        o = MyEmptyObject()
        assert o.x == 5
        o1 = pickle.loads(pickle.dumps(o))
        assert o1.x == 5
        assert not o1.picklable_attributes

    def test_strict(self):
        o = MyStrictObject(c=[1, 2, 3], a=1, b="b")
        with pytest.raises(AttributeError):
            o.dont_store_this = "BAD"

    def test_defaults(self):
        o = MyDefaultObject()
        assert o.x == 5
        o1 = pickle.loads(pickle.dumps(o))
        assert o1.x == 5
        assert not o1.picklable_attributes

        # This is not picklable so does not get stored
        o.x = 6
        assert o.x == 6
        o2 = pickle.loads(pickle.dumps(o))
        assert o2.x == 5
        assert not o1.picklable_attributes

        # Strict guards against this
        o = MyDefaultObject(_strict=True)
        with pytest.raises(AttributeError):
            o.x = 6

        # and you can set it in the constructor
        o = MyDefaultObject(x=6)
        assert o.x == 6
        o1 = pickle.loads(pickle.dumps(o))
        assert o1.x == 6


class TestPersist(object):
    def test_archive(self):
        o = MyObject(c=[1, 2, 3], a=1, b="b")
        o.dont_store_this = "BAD"

        import persist.archive  # May not be installed

        a = persist.archive.Archive()
        a.insert(o=o)

        d = {}
        exec(str(a), d)
        o1 = d["o"]

        assert repr(o) == repr(o1)
        assert hasattr(o, "dont_store_this")
        assert not hasattr(o1, "dont_store_this")


class Issue4(ContainerDict):
    """Class where ``a = 2*b`` is enforced (unless independently set).

    Examples
    --------
    >>> i = Issue4(a=6)
    >>> i.a, i.b
    (6, 3.0)
    >>> i
    Issue4(a=6, b=None)

    >>> i = Issue4(a=None, b=4)
    >>> i.a, i.b
    (8, 4)
    >>> i
    Issue4(a=None, b=4)

    >>> i.a = 10
    >>> i.a, i.b
    (10, 4)
    >>> i
    Issue4(a=10, b=4)
    """

    def __init__(self, **kw):
        self.a = 1.0
        self.b = None  # By default, compute b.
        super().__init__()
        self.update(kw)

    def _getstate(self):
        # Return the real state as in __dict__.
        state = super()._getstate()
        for key in state:
            state[key] = self.__dict__[key]
        return state

    def __getattribute__(self, key):
        if key not in set(["a", "b"]):
            return super().__getattribute__(key)

        # Specialized access for these to enforce computation
        res = {}
        a = res["a"] = super().__getattribute__("a")
        b = res["b"] = super().__getattribute__("b")
        if a is None:
            res["a"] = 2 * b
        if b is None:
            res["b"] = a / 2
        return res[key]
