"""Some debugging tools.

Most of these are implemented as decorators.
"""

import functools
import inspect
import sys

from six import reraise as raise_

__all__ = ["persistent_locals", "debug"]

# Default location
_LOCALS = {}


def persistent_locals(func, env=None):
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
    >>> assert f.locals == dict(x=1, y=1, z=2)
    >>> f.clear_locals()
    >>> f.locals
    {}

    >>> @persistent_locals
    ... def f(x):
    ...     for p in [1, 2, 3]:
    ...         y = x**p
    ...         yield y
    >>> gen = f(2)
    >>> next(gen)
    2
    >>> assert f.locals == dict(x=2, y=2, p=1)
    >>> next(gen)
    4
    >>> assert f.locals == dict(x=2, y=4, p=2)
    >>> next(gen)
    8
    >>> assert f.locals == dict(x=2, y=8, p=3)
    >>> f.clear_locals()
    >>> f.locals
    {}
    """

    locals_ = {}

    def trace(frame, event, arg):
        if frame.f_code is func.__code__:
            if event == "call":
                return trace  # Only trace into the function call
            if event == "return":
                locals_.update(frame.f_locals)
                if env is not None:
                    env.update(frame.f_locals)

    if inspect.isgeneratorfunction(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            gen = func(*args, **kwargs)

            def traced_gen():
                old_trace = sys.gettrace()
                sys.settrace(trace)
                try:
                    yield from gen
                except Exception as e:
                    # Remove one level of the traceback so we don't see the decorator
                    # junk.
                    raise_(e.__class__, e, sys.exc_info()[2].tb_next)
                finally:
                    sys.settrace(old_trace)

            return traced_gen()

    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            old_trace = sys.gettrace()
            sys.settrace(trace)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Remove one level of the traceback so we don't see the decorator junk.
                raise_(e.__class__, e, sys.exc_info()[2].tb_next)
            finally:
                sys.settrace(old_trace)

    wrapper.locals = locals_
    wrapper.env = env
    wrapper.clear_locals = wrapper.locals.clear
    return wrapper


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

    def decorator(func):
        return persistent_locals(func, env=env)

    if func is None:
        return decorator
    else:
        return decorator(func)
