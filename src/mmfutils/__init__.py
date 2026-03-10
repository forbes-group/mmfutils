try:
    import importlib.metadata as _metadata
except ImportError:
    import importlib_metadata as _metadata

try:
    __version__ = _metadata.version(__name__)
except _metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "<unknown source distribution>"

import numpy as np

__all__ = ["unique_list", "allclose"]


def unique_list(lst, preserve_order=True):
    """Make list contain only unique elements but preserve order.

    >>> lst = [1,2,4,3,2,3,1,0]
    >>> unique_list(lst)
    [1, 2, 4, 3, 0]
    >>> lst
    [1, 2, 4, 3, 2, 3, 1, 0]
    >>> unique_list(lst, preserve_order=False)
    [0, 1, 2, 3, 4]
    >>> unique_list([[1],[2],[2],[1],[3]])
    [[1], [2], [3]]

    See Also
    --------
    http://www.peterbe.com/plog/uniqifiers-benchmark
    """
    try:
        if preserve_order:
            s = set()
            return [x for x in lst if x not in s and not s.add(x)]
        else:
            return list(set(lst))
    except TypeError:  # Special case for non-hashable types
        res = []
        for x in lst:
            if x not in res:
                res.append(x)
        return res


def allclose(a, b, atol=None, rtol=None, tol_eps_N=8, min_tol=0.01):
    """Fix some issues with np.allclose.  See:
    https://github.com/numpy/numpy/issues/10161
    """
    a, b = map(np.asarray, (a, b))
    eps = max([np.finfo(x.dtype).eps for x in (a, b)])

    # Larger arrays will have more roundoff error.  Correct for this
    tol_eps = tol_eps_N * np.sqrt(np.prod(a.shape))

    if rtol is None:
        rtol = min(tol_eps * eps, min_tol)
    if atol is None:
        atol = min(tol_eps * eps, min_tol)

    res = np.all(abs(a - b) <= np.maximum(rtol * np.maximum(abs(a), abs(b)), atol))
    if not res:
        print(
            f"max abs err={abs(a - b).max()}, max rel err={abs(a / b - 1).max()} "
            + f"({atol=}, {rtol=})"
        )
    return res
