"""Linear Algebra Routines"""
__all__ = ["block_diag"]

import numpy as np


def block_diag(arrays):
    """Create a new diagonal matrix from the provided arrays.

    Parameters
    ----------
    a, b, c, ... : ndarray
        Input arrays.

    Returns
    -------
    D : ndarray
        Array with a, b, c, ... on the diagonal.

    Examples
    --------
    """
    arrays = list(map(np.asarray, arrays))
    shapes = np.array([a.shape for a in arrays])
    out = np.zeros(np.sum(shapes, axis=0))

    r, c = 0, 0
    for i, (rr, cc) in enumerate(shapes):
        out[r : r + rr, c : c + cc] = arrays[i]
        r += rr
        c += cc
    return out
