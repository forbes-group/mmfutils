"""Some debugging tools.

Most of these are implemented as decorators.
"""
import sys

from six import reraise as raise_

__all__ = ["persistent_locals", "debug"]

# Default location
_LOCALS = {}


class persistent_locals(object):
    """Decorator that stores the function's local variables.

    Examples
    --------
    >>> @persistent_locals
    ... def f(x):
    ...     y = x**2
    ...     z = 2*y
    ...     return z
    >>> f(1)
    2
    >>> sorted(f.locals.items())
    [('x', 1), ('y', 1), ('z', 2)]
    >>> f.clear_locals()
    >>> f.locals
    {}
    """

    def __init__(self, func):
        self._locals = {}
        self.func = func

    def __call__(self, *args, **kwargs):
        def tracer(frame, event, arg):  # pragma: nocover
            if event == "return":
                self._locals = frame.f_locals.copy()

        # tracer is activated on next call, return or exception
        sys.setprofile(tracer)
        try:
            # trace the function call
            res = self.func(*args, **kwargs)
        finally:
            # disable tracer and replace with old one
            sys.setprofile(None)
        return res

    def clear_locals(self):
        self._locals = {}

    @property
    def locals(self):
        return self._locals


def debug(*v, **kw):
    """Decorator to wrap a function and dump its local scope.

    Arguments
    ---------
    locals (or env): dict
       Function's local variables will be updated in this dict.
       Use locals() if desired.

    Examples
    --------
    >>> env = {}
    >>> @debug(env)
    ... def f(x):
    ...     y = x**2
    ...     z = 2*y
    ...     return z
    >>> f(1)
    2
    >>> sorted(env.items())
    [('x', 1), ('y', 1), ('z', 2)]

    This will put the local variables directly in the global scope:

    >>> @debug(locals())
    ... def f(x):
    ...     y = x**2
    ...     z = 2*y
    ...     return z
    >>> f(1)
    2
    >>> x, y, z
    (1, 1, 2)
    >>> f(2)
    8
    >>> x, y, z
    (2, 4, 8)

    If an exception is raised, you still have access to the results:

    >>> env = {}
    >>> @debug(env)
    ... def f(x):
    ...    y = 2*x
    ...    z = 2/y
    ...    return z
    >>> f(0)
    Traceback (most recent call last):
      ...
      File "<doctest mmfutils.debugging.debug[14]>", line 1, in <module>
        f(0)
      File "<doctest mmfutils.debugging.debug[13]>", line 4, in f
        z = 2/y
    ZeroDivisionError: division by zero
    >>> sorted(env.items())
    [('x', 0), ('y', 0)]
    """
    func = None
    env = kw.get("locals", kw.get("env", _LOCALS))

    if len(v) == 0:
        pass
    elif len(v) == 1:
        if isinstance(v[0], dict):
            env = v[0]
        else:
            func = v[0]
    elif len(v) == 2:
        func, env = v
    else:
        raise ValueError("Must pass in either function or locals or both")

    class Decorator(object):
        def __init__(self, f):
            self.func = persistent_locals(f)
            self.env = env

        def __call__(self, *v, **kw):
            try:
                res = self.func(*v, **kw)
            except Exception as e:
                # Remove two levels of the traceback so we don't see the
                # decorator junk.
                raise_(e.__class__, e, sys.exc_info()[2].tb_next.tb_next)
            finally:
                self.env.update(self.func.locals)
                self.func.clear_locals()

            return res

        @property
        def locals(self):
            return self.env

    if func is None:
        return Decorator
    else:
        return Decorator(func)
