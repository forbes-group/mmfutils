"""Tools for working with Numexp.
"""
from __future__ import absolute_import

__all__ = ['numexpr']

numexpr = False
try:
    import numexpr

    # These convolutions are needed to deal with a common failure mode: If the
    # MKL libraries cannot be found, then the whole python process crashes with
    # a library error.  We test this in a separate process and if it fails, we
    # disable the MKL.
    import multiprocessing

    def check(q):               # pragma: nocover
        import numexpr
        q.put(numexpr.get_vml_version())

    q = multiprocessing.Queue()
    _p = multiprocessing.Process(target=check, args=[q])
    _p.start()
    _p.join()
    if q.empty():               # pragma: nocover
        # Fail
        numexpr.use_vml = False

except ImportError:             # pragma: nocover
    pass
