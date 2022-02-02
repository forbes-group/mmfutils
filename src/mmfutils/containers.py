"""Provides convenience containers that support pickling and archiving.

Archiving is supported through the interface defined by the ``persist``
package (though use of that package is optional and it is not a dependency).
"""

import collections
from collections import abc
import pickle

__all__ = ["ObjectBase", "Object", "Container", "ContainerList", "ContainerDict"]


######################################################################
# General utilities
class ObjectBase(object):
    """General base class with a few convenience methods.

    Summary:

    * `__init__()` sets parameters and calls `init()`
    * `init()` calculates all other parameters.

    Motivation:

    The motivation is objects intended to be used in computationally
    demanding settings.  The idea is that the `init()` method will be
    called before starting a computation, ensuring that the object is
    up-to-date, and performing any expensive calculations.  Then the
    object can be used in a computationally demanding setting.

    I have been using this approach for some time and am generally
    happy with how it works.  Some care is needed nesting calls to
    `init()` in derived classes, but I have found these cases easy to
    deal with.  Other approaches such as using properties can carry a
    performance hit.  Writing setters can work well, but demands a lot
    from the developer and become very complicated when properties
    depend on each other.

    Details:

    * The constructor `__init__()` should only be used to set
      variables in `self`.  The reason is that the code here uses the
      variables set in the constructor to determine which attributes
      need to be pickled.  Initialization of computed attributes
      should instead be done in the `init()` method .

    * The constructor `__init__()` takes `kwargs` and will set these.
      This allows using `super().__init__()`.  See e.g.:

          https://rhettinger.wordpress.com/2011/05/26/super-considered-super/

    * The constructor will store all assigned variables (in
      `__dict__()`) to a list `picklable_attributes` which can then be
      used by the `Object` to provide pickling services.  Here
      we simply use this to set an `initialized` flag to note the user
      that the object might be invalid and need `init()` called again.

    * The `init()` method should make sure that the object ends in a
      consistent state so that further computations (without users
      setting attributes) can be computed efficiently.  If the user
      sets attributes, `init()` should be called again.

    .. note:: Do not use any of the following variables:

          * `picklable_attributes`:
             Reserved for the list of attributes that will be
             pickled.  If this has been stored in `self.__dict__` then
             the constructor chain has finished processing.
          * `initialized`:
             Used to flag if attributes have been changed but without
             `init()` being called.

    By default setting any attribute in `picklable_attributes` will
    set the `initialized` flag to `False`.  This will be set to `True`
    when `init()` is called. Objects can then include an `assert
    self.initialized` in the appropriate places.

    .. note:: This redefines __setattr__ to provide the behaviour.

    Examples
    --------
    >>> class A(ObjectBase):
    ...     def __init__(self, x=0):
    ...         super().__init__(x=x)
    ...     def init(self):
    ...         self.x1 = self.x + 1   # A dependent variable
    ...         super().init()
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

    initialized = False  # Assure that this is always defined.
    picklable_attributes = ()  # Tuple so it is immutable

    def __init__(self, **kw):
        for _k in kw:
            setattr(self, _k, kw[_k])
        if "picklable_attributes" not in self.__dict__:
            self.picklable_attributes = sorted(_k for _k in self.__dict__)
        self.init()

    def init(self):
        """Initialize Object."""
        # Define any computed attributes here.
        # Don't forget to call `super().init()` in your code!
        self.initialized = True

    def _check_attribute(self, key, value=None):
        """Return True if attribute is pickable.

        Can be overloaded to perform more comprehensive checks.
        """
        return key in self.picklable_attributes

    def _getstate(self):
        """Return and OrderedDict of picklable attributes."""
        return collections.OrderedDict(
            (_k, getattr(self, _k)) for _k in self.picklable_attributes
        )

    def get_persistent_rep(self, env):
        """Return `(rep, args, imports)`.

        Define a persistent representation `rep` of the instance self where
        the instance can be reconstructed from the string rep evaluated in the
        context of dict args with the specified imports = list of `(module,
        iname, uiname)` where one has either `import module as uiname`, `from
        module import iname` or `from module import iname as uiname`.

        This satisfies the `IArchivable` interface for the `persist`
        package.
        """
        # Implementation taken from
        # persist.objects.Archivable.get_persistent_rep()
        args = self._getstate()
        module = self.__class__.__module__
        name = self.__class__.__name__
        imports = [(module, name, name)]

        keyvals = ["=".join((k, k)) for k in args]
        rep = "{0}({1})".format(name, ", ".join(keyvals))
        return (rep, args, imports)

    def __repr__(self):
        state = self._getstate()
        args = ", ".join("=".join((_k, repr(state[_k]))) for _k in state)
        return "{0}({1})".format(self.__class__.__name__, args)

    def __setattr__(self, key, value):
        """Sets the `initialized` flag to `False` if any picklable
        attribute is changed.
        """
        if self._check_attribute(key, value):
            self.__dict__["initialized"] = False
        super().__setattr__(key, value)


class ObjectMixin(object):
    """Mixin for ObjectBase that provides pickling support.

    Pickling will save only those variables defined in
    `picklable_attributes` which is usually defined when the base
    `__init__` is finished.  The `init()` method will be called upon
    unpickling, thereby allowing unpicklable objects to be used (in
    particular function instances).

    .. note:: Do not use any of the following variables:

          * `_empty_state`:
             Reserved for objects without any state
          * `_independent_attributes`:
          * `_dependent_attributes`:
          * `_strict`:
             If `True`, then only picklable attributes will be
             settable through `__setattr__()`.
          * `_check`:
             If `True`, check that objects are actually picklable when
             they are set.
          * `_reserved_attributes`:
             List of special attributes that should be excluded from
             processing.

    To allow for some variables to be set without invalidating the
    object we also check the set of names `_independent_attributes`.

    Examples
    --------
    >>> class A(ObjectMixin, ObjectBase):
    ...     def __init__(self, x=0):
    ...         self.x = x
    ...         super().__init__()
    ...     def init(self):
    ...         self.x1 = self.x + 1   # A dependent variable
    ...         super().init()
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

    _check = True
    _strict = False
    _independent_attributes = ()
    _dependent_attributes = ()
    _reserved_attributes = (
        "initialized",
        "picklable_attributes",
        "_independent_attributes",
        "_dependent_attributes",
        "_strict",
        "_check",
        "_reserved_attributes",
    )

    ######################################################################
    # Python pickle and copy interface
    # https://docs.python.org/3/library/copy.html
    # https://docs.python.org/3/library/pickle.html
    def __getstate__(self):
        state = self._getstate()

        # From the docs:
        # "For new-style classes, if __getstate__() returns a false value,
        #  the __setstate__() method will not be called."
        # Don't return an empty state!
        if not state:
            state = dict(_empty_state=True)
        return state

    def __setstate__(self, state):
        if "_empty_state" in state:
            state.pop("_empty_state")

        if "picklable_attributes" not in state:
            state["picklable_attributes"] = sorted(state)

        self.__dict__.update(state)

        self.init()

        # init() may reset an evolver state, for example, so we once again set
        # the variables from the pickle.
        self.__dict__.update(state)

    ######################################################################
    # More comprehensive checks
    def _check_picklable(self, key, value):
        """Raise ValueError if obj is not picklable."""
        try:
            pickle.dumps(value)
        except pickle.PicklingError:
            raise ValueError(f"Attribute {key}={value} not picklable.")

    def _check_attribute(self, key, value=None):
        """Expended version that looks at exclusion lists and checks
        if value is picklable.  Raises AttributeError if _strict and
        attribute is not picklable.
        """
        if key not in self._independent_attributes and (
            key in self._dependent_attributes or key in self.picklable_attributes
        ):
            if self._check:
                self._check_picklable(key=key, value=value)
            return True
        elif (
            self._strict
            and "picklable_attributes" in self.__dict__
            and key not in self.picklable_attributes
            and key not in self._independent_attributes
            and key not in self._reserved_attributes
            and key not in self._dependent_attributes
        ):
            raise AttributeError(f"Cannot set attribute `{key}` in `_strict` object.")
        return False


class Object(ObjectMixin, ObjectBase):
    """Extension of Object with pickling support.

    Pickling will save only those variables defined in
    `picklable_attributes` which is usually defined when the base
    `__init__` is finished.  The `init()` method will be called upon
    unpickling, thereby allowing unpicklable objects to be used (in
    particular function instances).

    .. note:: Do not use any of the following variables:

          * `_empty_state`:
             Reserved for objects without any state
          * `_independent_attributes`:
          * `_dependent_attributes`:
          * `_strict`:
             If `True`, then only picklable attributes will be
             settable through `__setattr__()`.
          * `_check`:
             If `True`, check that objects are actually picklable when
             they are set.
          * `_reserved_attributes`:
             List of special attributes that should be excluded from
             processing.

    To allow for some variables to be set without invalidating the
    object we also check the set of names `_independent_attributes`.

    Examples
    --------
    >>> class A(Object):
    ...     def __init__(self, x=0):
    ...         self.x = x
    ...         super().__init__()
    ...     def init(self):
    ...         self.x1 = self.x + 1   # A dependent variable
    ...         super().init()
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

    def __init__(self, **kw):
        super().__init__(**kw)

        # Check for bad attributes
        if self._check:
            for key in self.picklable_attributes:
                self._check_picklable(key, getattr(self, key))


class Container(Object, abc.Sized, abc.Iterable, abc.Container):
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
                if isinstance(obj, abc.Sequence):
                    self.picklable_attributes = list(list(zip(*obj))[0])
                    self.picklable_attributes.extend(
                        _k for _k in kw if _k not in self.__dict__
                    )

        super().__init__(**kw)

    # Methods required by abc.Container
    def __contains__(self, key):
        return key in self.picklable_attributes

    # Methods required by abc.Sized
    def __len__(self):
        return len(self.picklable_attributes)

    # Methods required by abc.Iterable
    def __iter__(self):
        for _k in self.picklable_attributes:
            yield getattr(self, _k)

    def __delattr__(self, key):
        object.__delattr__(self, key)
        self.picklable_attributes.remove(key)


class ContainerList(Container, abc.Sequence):
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

    # Methods required by abc.Sequence
    def __getitem__(self, i):
        key = self.picklable_attributes[i]
        return getattr(self, key)

    # Methods required by abc.MutableSequence
    # We only provide a few
    def __setitem__(self, i, value):
        key = self.picklable_attributes[i]
        setattr(self, key, value)

    def __delitem__(self, i):
        key = self.picklable_attributes[i]
        self.__delattr__(key)


class ContainerDict(Container, abc.MutableMapping):
    """Simple container object that behaves like a dict.

    Attributes can be specified in the constructor.  These will form the
    representation of the object as well as picking.  Additional attributes can
    be assigned, but will not be pickled.

    Examples
    --------
    >>> from collections import OrderedDict
    >>> c = ContainerDict(b='Hi', a=1)
    >>> c                       # Note: items sorted for consistent repr
    ContainerDict(a=1, b='Hi')
    >>> c['a']
    1
    >>> c['a'] = 2
    >>> c.a
    2
    >>> OrderedDict(c)
    OrderedDict([('a', 2), ('b', 'Hi')])
    """

    # Methods required by abc.Iterable
    def __iter__(self):
        return self.picklable_attributes.__iter__()

    # Methods required by abc.Mapping
    def __getitem__(self, key):
        return getattr(self, key)

    # Methods required by abc.MutableMapping
    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        self.__delattr__(key)
