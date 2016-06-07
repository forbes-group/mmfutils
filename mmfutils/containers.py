"""Provides convenience containers that support pickling and archiving.

Archiving is supported through the interface defined by the ``persist``
package (though use of that package is optional and it is not a dependency).
"""
import collections

__all__ = ['Object', 'Container', 'ContainerList', 'ContainerDict']


######################################################################
# General utilities
class Object(object):
    r"""General base class with a few convenience methods.

    Constructors: The `__init__` method should simply be used to set variables,
    all initialization that computes attributes etc. should be done in `init()`
    which will be called at the end of `__init__`.

    This aids pickling which will save only those variables defined when the
    base `__init__` is finished, and will call `init()` upon unpickling,
    thereby allowing unpicklable objects to be used (in particular function
    instances).

    .. note:: Do not use any of the following variables:

          * `_empty_state`: reserved for objects without any state
          * `_independent_attributes`, `_dependent_attributes`,
            `initialized`: Used to flag if attributes have been
            changed but without `init()` being called.  (See below.)

    By default setting any attribute in `picklable_attributes` will
    set the `initialized` flag to `False`.  This will be set to `True`
    when `init()` is called. Objects can then include an `assert
    self.initialized` in the appropriate places.

    To allow for some variables to be set without invalidating the
    object we also check the set of names `_independent_attributes`.

    .. note:: This redefines __setattr__ to provide the behaviour.

    Examples
    --------
    >>> class A(Object):
    ...     def __init__(self, x=0):
    ...         self.x = x
    ...         Object.__init__(self)
    ...     def init(self):
    ...         self.x1 = self.x + 1   # A dependent variable
    ...         Object.init(self)
    ...     def check(self):
    ...         if not self.initialized:
    ...             raise AssertionError("Please call init()!")
    ...         return self.x1 == self.x + 1
    >>> a = A(x=0)
    >>> a.check()
    True
    >>> a.x = 2.0
    >>> a.check()
    Traceback (most recent call last):
    ...
    AssertionError: Please call init()!
    >>> a.init()
    >>> a.check()
    True
    """
    # Assure that this is always defined.
    initialized = False
    picklable_attributes = ()  # Tuple so it is immutable
    _independent_attributes = ()
    _dependent_attributes = ()

    def __init__(self):
        if 'picklable_attributes' not in self.__dict__:
            self.picklable_attributes = sorted(_k for _k in self.__dict__)
        self.init()

    def init(self):
        r"""Define any computed attributes here.

        Don't forget to call `Object.init()`
        """
        self.initialized = True

    def __getstate__(self):
        state = collections.OrderedDict((_k, getattr(self, _k))
                                        for _k in self.picklable_attributes)

        # From the docs:
        # "For new-style classes, if __getstate__() returns a false value,
        #  the __setstate__() method will not be called."
        # Don't return an empty state!
        if not state:
            state = dict(_empty_state=True)
        return state

    def __setstate__(self, state):
        if '_empty_state' in state:
            state.pop('_empty_state')

        if 'picklable_attributes' not in state:
            state['picklable_attributes'] = sorted(state)

        self.__dict__.update(state)

        self.init()

        # init() may reset an evolver state, for example, so we once again set
        # the variables from the pickle.
        self.__dict__.update(state)

    def get_persistent_rep(self, env):
        """Return `(rep, args, imports)`.

        Define a persistent representation `rep` of the instance self where
        the instance can be reconstructed from the string rep evaluated in the
        context of dict args with the specified imports = list of `(module,
        iname, uiname)` where one has either `import module as uiname`, `from
        module import iname` or `from module import iname as uiname`.

        This satisfies the ``IArchivable`` interface for the ``persist``
        package.
        """
        # Implementation taken from
        # persist.objects.Archivable.get_persistent_rep()
        args = self.__getstate__()
        module = self.__class__.__module__
        name = self.__class__.__name__
        imports = [(module, name, name)]

        keyvals = ["=".join((k, k)) for k in args]
        rep = "{0}({1})".format(name, ", ".join(keyvals))
        return (rep, args, imports)

    def __repr__(self):
        state = self.__getstate__()
        args = ", ".join("=".join((_k, repr(state[_k]))) for _k in state)
        return "{0}({1})".format(self.__class__.__name__, args)

    def _is_dependent_attribute(self, key):
        return (key not in self._independent_attributes
                and (key in self._dependent_attributes
                     or key in self.picklable_attributes))

    def __setattr__(self, key, value):
        """Sets the `initialized` flag to `False` if any picklable
        attribute is changed.
        """
        if self._is_dependent_attribute(key):
            self.__dict__['initialized'] = False
        object.__setattr__(self, key, value)


class Container(Object, collections.Sized, collections.Iterable,
                collections.Container):
    """Simple container object.

    Attributes can be specified in the constructor.  These will form the
    representation of the object as well as picking.  Additional attributes can
    be assigned, but will not be pickled.

    Examples
    --------
    >>> c = Container(b='Hi', a=1)
    >>> c                       # Note: items sorted for consistent repr
    Container(a=1, b='Hi')
    >>> c.a
    1
    >>> c.a = 2
    >>> c.a
    2
    >>> tuple(c)                # Order is lexicographic
    (2, 'Hi')
    >>> c.x = 6                 # Will not be pickled: only for temp usage
    >>> c.x
    6
    >>> 'a' in c
    True
    >>> 'x' in c
    False
    >>> import pickle
    >>> c1 = pickle.loads(pickle.dumps(c))
    >>> c1
    Container(a=2, b='Hi')
    >>> c1.x
    Traceback (most recent call last):
    ...
    AttributeError: 'Container' object has no attribute 'x'
    """
    def __init__(self, *argv, **kw):
        if 1 == len(argv):
            # Copy construct
            obj = argv[0]
            if isinstance(obj, Container):
                self.__setstate__(obj.__getstate__())
            else:
                # assume dict-like
                self.__dict__.update(obj)
                if isinstance(obj, collections.Sequence):
                    self.picklable_attributes = list(zip(*obj)[0])
                    self.picklable_attributes.extend(
                        _k for _k in kw if _k not in self.__dict__)

        self.__dict__.update(kw)
        Object.__init__(self)

    # Methods required by collections.Container
    def __contains__(self, key):
        return key in self.picklable_attributes

    # Methods required by collections.Sized
    def __len__(self):
        return len(self.picklable_attributes)

    # Methods required by collections.Iterable
    def __iter__(self):
        for _k in self.picklable_attributes:
            yield getattr(self, _k)

    def __delattr__(self, key):
        object.__delattr__(self, key)
        self.picklable_attributes.remove(key)


class ContainerList(Container, collections.Sequence):
    """Simple container object that behaves like a list.

    Examples
    --------
    >>> c = ContainerList(b='Hi', a=1)
    >>> c                       # Note: items sorted for consistent repr
    ContainerList(a=1, b='Hi')
    >>> c[0]
    1
    >>> c[0] = 2
    >>> c.a
    2
    >>> tuple(c)                # Order is lexicographic
    (2, 'Hi')
    """
    # Methods required by collections.Sequence
    def __getitem__(self, i):
        key = self.picklable_attributes[i]
        return getattr(self, key)

    # Methods required by collections.MutableSequence
    # We only provide a few
    def __setitem__(self, i, value):
        key = self.picklable_attributes[i]
        setattr(self, key, value)

    def __delitem__(self, i):
        key = self.picklable_attributes[i]
        self.__delattr__(key)


class ContainerDict(Container, collections.MutableMapping):
    """Simple container object that behaves like a dict.

    Attributes can be specified in the constructor.  These will form the
    representation of the object as well as picking.  Additional attributes can
    be assigned, but will not be pickled.

    Examples
    --------
    >>> c = ContainerDict(b='Hi', a=1)
    >>> c                       # Note: items sorted for consistent repr
    ContainerDict(a=1, b='Hi')
    >>> c['a']
    1
    >>> c['a'] = 2
    >>> c.a
    2
    >>> dict(c)
    {'a': 2, 'b': 'Hi'}
    """
    # Methods required by collections.Iterable
    def __iter__(self):
        return self.picklable_attributes.__iter__()

    # Methods required by collections.Mapping
    def __getitem__(self, key):
        return getattr(self, key)

    # Methods required by collections.MutableMapping
    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        self.__delattr__(key)
