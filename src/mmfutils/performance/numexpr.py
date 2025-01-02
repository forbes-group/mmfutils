"""Tools for working with Numexp.

At present all this module provides is a safe way of importing
``numexpr``.  This prevents a hard crash (i.e. segfault) when the MKL
is enabled but cannot be found.  Just go:

>>> from mmfutils.performance.numexpr import numexpr

"""

__all__ = ["numexpr"]

numexpr = False
try:
    import numexpr

    # These convolutions are needed to deal with a common failure mode: If the
    # MKL libraries cannot be found, then the whole python process crashes with
    # a library error.  We test this in a separate process and if it fails, we
    # disable the MKL.  The target function must be in a separate module, otherwise we
    # will get
    # RuntimeError:
    #   An attempt has been made to start a new process before the
    #   current process has finished its bootstrapping phase.
    #   ...
    #   To fix this issue, refer to the "Safe importing of main module"
    #   section in https://docs.python.org/3/library/multiprocessing.html
    import multiprocessing
    from . import _numexpr_import_check

    q = multiprocessing.Queue()
    _p = multiprocessing.Process(target=_numexpr_import_check.check, args=[q])
    _p.start()
    _p.join()
    if q.empty():  # pragma: nocover
        # Fail
        numexpr.use_vml = False

except ImportError:  # pragma: nocover
    pass
