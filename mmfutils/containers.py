r"""Utilities"""
"""Provides convenience containers that support pickling and archiving.

Archiving is supported through the interface defined by the ``persist``
package (though use of that package is optional and it is not a dependency).
"""

__all__ = ['Object']


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

    .. note:: Do not use a variable named `_empty_state`... this is reserved
       for objects without any state.

    """
    def __init__(self):
        if 'picklable_attributes' not in self.__dict__:
            self.picklable_attributes = sorted(_k for _k in self.__dict__)
        self.init()

    def init(self):
        r"""Define any computed attributes here."""

    def __getstate__(self):
        state = dict((_k, getattr(self, _k))
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
        args = ", ".join(
            "=".join((_k, repr(getattr(self, _k))))
            for _k in self.picklable_attributes)
        return "{0}({1})".format(self.__class__.__name__, args)


class Container(Object):
    """Simple container object.

    Attributes can be specified in the constructor.  These will form the
    representation of the object as well as picking.  Additional attributes can
    be assigned, but will not be pickled.

    Examples
    --------
    >>> c = Container(b='Hi', a=1)
    >>> c                       # Note: items sorted for consistent reprs
    Container(a=1, b='Hi')
    >>> c.a
    1
    >>> c.a = 2
    >>> c.a
    2
    >>> tuple(c)                # Order is lexicographic
    (2, 'Hi')
    >>> c.x = 6                 # Will not be pickled
    >>> c.x
    6
    >>> import pickle
    >>> c1 = pickle.loads(pickle.dumps(c))
    >>> c1
    Container(a=2, b='Hi')
    >>> c1.x
    Traceback (most recent call last):
    ...
    AttributeError: 'Container' object has no attribute 'x'
    """
    def __init__(self, **kw):
        self.__dict__.update(kw)
        Object.__init__(self)

    def __iter__(self):
        for _k in self.picklable_attributes:
            yield getattr(self, _k)
