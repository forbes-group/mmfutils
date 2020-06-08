__version__ = '0.5.3'


def unique_list(l, preserve_order=True):
    """Make list contain only unique elements but preserve order.

    >>> l = [1,2,4,3,2,3,1,0]
    >>> unique_list(l)
    [1, 2, 4, 3, 0]
    >>> l
    [1, 2, 4, 3, 2, 3, 1, 0]
    >>> unique_list(l, preserve_order=False)
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
            return [x for x in l if x not in s and not s.add(x)]
        else:
            return list(set(l))
    except TypeError:  # Special case for non-hashable types
        res = []
        for x in l:
            if x not in res:
                res.append(x)
        return res
