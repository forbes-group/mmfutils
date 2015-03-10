import pickle
import nose.tools as nt

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


class MyEmptyObject(Object):
    """Has no attributes, but should have init() called"""
    def init(self):
        self.x = 5


class TestObject(object):
    def test_object_persist(self):
        """Test persistent representation of object class"""

        o = MyObject(c=[1, 2, 3], a=1, b="b")
        o.dont_store_this = "BAD"

        o1 = pickle.loads(pickle.dumps(o))
        nt.eq_(repr(o), repr(o1))
        nt.ok_(hasattr(o, 'dont_store_this'))
        nt.ok_(not hasattr(o1, 'dont_store_this'))

    def test_empty_object(self):
        o = MyEmptyObject()
        nt.eq_(o.x, 5)
        o1 = pickle.loads(pickle.dumps(o))
        nt.eq_(o1.x, 5)
        nt.ok_(not o1.picklable_attributes)


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
