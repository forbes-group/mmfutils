import pickle
import nose.tools as nt

from mmfutils.containers import Object, Container, ContainerList, ContainerDict


class TestContainer(object):
    def test_container_persist(self):
        """Test persistent representation of object class"""

        o = Container(c=[1, 2, 3], a=1, b="b")
        o.dont_store_this = "BAD"

        o1 = pickle.loads(pickle.dumps(o))
        nt.eq_(repr(o), repr(o1))
        nt.ok_(hasattr(o, 'dont_store_this'))
        nt.ok_(not hasattr(o1, 'dont_store_this'))

    def test_container_delattr(self):
        # Not encouraged but provided
        c = Container(c=[1, 2, 3], a=1, b="b")
        del c.b
        nt.ok_('a' in c)
        nt.ok_('b' not in c)
        nt.ok_('c' in c)


class TestContainerList(object):
    def test_container_delitem(self):
        # Not encouraged but provided
        c = ContainerList(c=[1, 2, 3], a=1, b="b")
        del c[1]
        nt.ok_('a' in c)
        nt.ok_('b' not in c)
        nt.ok_('c' in c)


class TestContainerDict(object):
    def test_container_del(self):
        # Not encouraged but provided
        c = ContainerDict(c=[1, 2, 3], a=1, b="b")
        del c['b']
        nt.ok_('a' in c)
        nt.ok_('b' not in c)
        nt.ok_('c' in c)

    def test_container_setitem(self):
        # Not encouraged but provided
        c = ContainerDict(c=[1, 2, 3], a=1, b="b")
        c['a'] = 3
        nt.eq_(c.a, 3)


class TestContainerConversion(object):
    def setUp(self):
        self.c = Container(a=1, c=[1, 2, 3], b="b")
        self.cl = ContainerList(a=1, c=[1, 2, 3], b="b")
        self.cd = ContainerDict(a=1, c=[1, 2, 3], b="b")
        self.d = dict(a=1, c=[1, 2, 3], b="b")
        self.l = [('a', 1), ('b', "b"), ('c', [1, 2, 3])]

    def check(self, c):
        nt.eq_(self.c.__getstate__(), c.__getstate__())

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
