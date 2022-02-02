try:
    import importlib.metadata as _metadata
except ImportError:
    import importlib_metadata as _metadata

try:
    __version__ = _metadata.version(__name__)
except _metadata.PackageNotFoundError:
    __version__ = "<unknown source distribution>"


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
