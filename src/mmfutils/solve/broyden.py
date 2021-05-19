"""Broyden Minimizers and Root Finders.

This module contains several different minimizers and root finders that
implement Broyden's method.
"""
import copy

import numpy as np

# We import these here in case we want to change in future to use more
# efficient implementations.
from numpy import matmul

import scipy.optimize.nonlin
import scipy as sp

from ..math.linalg import block_diag

__all__ = ["DyadicSum"]


_FINFO = np.finfo(float)
_EPS = _FINFO.eps
_TINY = _FINFO.tiny
_SINGULAR_TOL = 1e-6


class DyadicSum(object):
    r"""Represents a matrix as a sum of :math:`n` dyads of length :math:`N`:

    .. math::
       \newcommand{\mat}[1]{\mathbf{#1}}
       \newcommand{\ket}[1]{\left|#1\right\rangle}
       \newcommand{\bra}[1]{\left\langle#1\right|}
       \mat{M} = \alpha\mat{1} + \sum_{n}\ket{a_n}\sigma_n\bra{b_n}
               = \alpha\mat{1} + \ket{\mat{A}}\mat{\sigma}\bra{\mat{B}}.

    The two sets of bases are stored in :math:`N \times n` matrices
    :math:`\ket{\mat{A}}` and :math:`\ket{\mat{B}}` and the :math:`n\times n` matrix
    :math:`\mat{\sigma}`.

    If :attr:`use_svd` is `True`, then the singular value
    decomposition of :math:`\mat{\sigma}` is used to keep :math:`\mat{\sigma}`
    diagonal with positive entries and only these diagonals are stored.

    Notes
    -----
    * We assume everything is real here: no complex conjugation is performed
      with transposition.
    * We also do not explicitly support non-square matrices.  Some methods may
      work but this has not been properly tested.
    * Left and right multiplication rely on working with matrices, not arrays.
      In particular, things like `.dot()` do not work properly.

    .. todo:: Perform an analysis of the inverse jacobian, changing bases
       if needed to make the dyads linearly independent.
    .. todo:: Make `inplace` work properly.
    .. todo:: Use BLAS routines (more are now available).
    .. todo:: Support __array_ufunc__:
       https://docs.scipy.org/doc/numpy/neps/ufunc-overrides.html

    Examples
    --------
    >>> np.random.seed(3)
    >>> N, n, m = 20, 5, 3
    >>> At = np.random.random((N, n+m))
    >>> B = np.random.random((n+m, N))
    >>> at = At[:, :n]
    >>> b = B[:n, :]
    >>> sigma = np.eye(n)
    >>> s = DyadicSum(at=at, b=b, sigma=sigma, n_max=n)
    >>> np.allclose(s._at*s._sigma @ s._b, at @ b)        # doctest: +SKIP
    True

    Now we add the remaining terms.  The dyadic sum should be the
    best rank n approximation of `At @ B`:

    >>> s.add_dyad(at=At[:, n:], b=B[n:, :], sigma=np.eye(m))
    >>> U, d, Vt = np.linalg.svd(At @ B)                  # doctest: +SKIP
    >>> d[n:] = 0    # Make rank deficient approx         # doctest: +SKIP
    >>> np.allclose(s._at*s._sigma @ s._b, U*d @ Vt)      # doctest: +SKIP
    True

    Note that the approximation is not exact:

    >>> np.allclose(s._at*s._sigma @ s._b, At @ B)        # doctest: +SKIP
    False

    Examples
    --------
    >>> J = DyadicSum()
    >>> x = np.array([[1.0],
    ...               [2.0]])
    >>> J @ x - x                                         # doctest: +SKIP
    array([[0.],
           [0.]])
    >>> b = np.array([[1.0, 0.0]])
    >>> a = np.array([[0.0],
    ...               [2.0]])

    >>> J.add_dyad(a, b)
    >>> J @ x                                             # doctest: +SKIP
    array([[1.],
           [4.]])
    >>> x.T @ J                                           # doctest: +SKIP
    array([[5., 2.]])
    >>> J.__rmatmul__(x.T)
    array([[5., 2.]])

    Here is an example of limiting the size of the dyadic.

    >>> np.random.seed(3)
    >>> s1 = np.eye(10)
    >>> s2 = DyadicSum(n_max=10)
    >>> for n in range(100):
    ...    a = np.random.random(10)
    ...    b = np.random.random(10)
    ...    s1 += a[:, None]*b[None, :]
    ...    s2.add_dyad(a, b)

    This should still be exact because the space is only ten
    dimensional.

    >>> np.allclose(s1, s2.todense())
    True

    The dynamic_range parameter is a more mathematical way of keeping
    the basis fixed.  It ensures that the most significant singular
    values will be kept.

    >>> s1 = DyadicSum(dynamic_range=0.01)
    >>> s2 = DyadicSum()
    >>> for n in range(100):
    ...    a = np.random.random(20)
    ...    b = np.random.random(20)
    ...    s1.add_dyad(a, b)
    ...    s2.add_dyad(a, b)

    >>> d1 = np.linalg.svd(s1.todense(), compute_uv=False)
    >>> d2 = np.linalg.svd(s2.todense(), compute_uv=False)
    >>> (abs(d1 - d2)/max(d2)).max() < 0.02
    True

    Attributes
    ----------
    n_max : int
       Maximum number n of Dyads to store.  If this is finite, then the N x n
       matrices are pre-allocated, and when m new dyads are added, they replace
       the least significant m dyads, requiring no more allocations, otherwise
       the dyads are added as required.
    inplace : bool (False)
       If :attr:`n_max` is finite, then this signifies that the matrices
       :attr:`at` and :attr:`b` should be allocated only once and all
       operations should be done inplace on these.  In particular, when new
       dyads are added, the least significant components of the old matrix are
       dropped *first* then the dyads are added.

       If this is `False`, then the new dyads are added first and *then* the
       least-significant components are dropped.  This latter form requires
       more storage, but may be more  accurate.

       .. note:: Presently, the inplace operations cannot be performed because
              `scipy` does not expose the correct BLAS routines, so the only
              purpose of this flag is to somewhat limit memory usage, but this
              is probably quite ineffective at the moment.

    use_svd : bool (True)
       If `True`, then :meth:`orthogonalize` will be run whenever a new dyad is
       added.  (Generally a good idea, but can be slow if there are a lot of dyads).
    dynamic_range : float (_EPS)
       Each call to :meth:`orthogonalize` will only keep the singular values
       within this fraction of the highest.

    _at : (N, n) float array
       :math:`\ket{\mat{A}}`. We use the ket form here because that is
       most often used and more efficient (presently, :func:`numpy.dot` makes
       copies if the arrays are not both `C_CONTIGUOUS`
    _b : (n, N) float array
       :math:`\bra{\mat{B}}`
    _sigma : (n, n) float array
       :math:`\mat{\sigma}` or `(n, )` array :math:`\diag\mat{\sigma}`
       if :attr:`use_svd`.
    alpha : float
       Initial dyad is this factor times the identity.
    """
    # Ensure that this has higher priority than numpy or scipy arrays
    # so that A @ B will call B.__rmatmul__ if B is a DyadicSum.
    __array_priority__ = 100.0  # https://stackoverflow.com/questions/55879170

    def __init__(
        self,
        at=None,
        b=None,
        sigma=None,
        alpha=1.0,
        n_max=np.inf,
        use_svd=True,
        inplace=False,
        dynamic_range=_EPS,
    ):
        self._at = np.empty((0, 0)) if at is None else np.ascontiguousarray(at)
        self._b = np.empty((0, 0)) if b is None else np.ascontiguousarray(b)
        if sigma is None:
            k = len(self._b)
            if not len(self._at.T) == k:
                raise ValueError(
                    "If sigma==None, a and b must have same length. "
                    + "Got {} and {}.".format(len(self._at.T), k)
                )
            sigma = np.eye(k, k)
        self._sigma = np.asarray(sigma)

        self.alpha = alpha

        assert self._at.shape[0] == self._b.shape[1]
        assert (self._at.shape[1], self._b.shape[0]) == self._sigma.shape or (
            self._at.shape[1],
            self._b.shape[0],
        ) == self._sigma.shape * 2

        self.n_max = n_max
        self.use_svd = use_svd
        self.inplace = inplace
        self.dynamic_range = dynamic_range

        if not use_svd and n_max < np.inf:
            raise ValueError("Finite `n_max={}` requires `svd=True`.".format(n_max))

        self.orthogonalize()

    @property
    def dtype(self):
        return np.asarray(self._at).dtype

    @property
    def shape(self):
        return (self._at.shape[0], self._b.shape[1])

    def copy(self):
        """Return a (deep) copy of self."""
        return copy.deepcopy(self)

    def reset(self):
        """Reset the matrix.

        Examples
        --------
        >>> M = DyadicSum()
        >>> M.todense()
        array(1.)
        >>> M.add_dyad([1, 0], [1, 0])
        >>> M.add_dyad([0, 2], [1, 0])
        >>> M.add_dyad([3, 0], [0, 1])
        >>> M.add_dyad([0, 4], [0, 1])
        >>> M.todense()
        array([[2., 3.],
               [2., 5.]])
        >>> M.reset()
        >>> M.todense()
        array(1.)
        """
        self._at = np.empty((0, 0), dtype=float)
        self._b = np.empty((0, 0), dtype=float)
        self._sigma = np.empty(0, dtype=float)

    def add_dyad(self, at, b, sigma=None):
        r"""Add `|a>d<b|` to `J`.

        Parameters
        ----------
        at, b : array
           These should be either 1-d arrays  (for a single dyad) or
           2-d arrays (`(N, m)` for `at` and `(m, N)` for `b`)
           arrays representing the bra's `<a|` and `<b|`.
        sigma : array
           Matrix linking `at` and `b`.  Must be provided if `len(at.T)`
           and `len(b)` are different.

        Examples
        --------

        Here is a regression test for a bug: adding a set of dyads
        that would push the total number beyond `n_max`.

        >>> np.random.seed(0)
        >>> at = np.random.random((10, 3))
        >>> b = np.random.random((3, 10))
        >>> s = DyadicSum(n_max=2)
        >>> s.add_dyad(at=at, b=b)
        """
        # Checking
        at = np.asarray(at)
        b = np.asarray(b)
        if 1 == len(at.shape):
            at = at.reshape((len(at), 1))
        if 1 == len(b.shape):
            b = b.reshape((1, len(b)))

        a = at.T
        if sigma is None:
            if not len(a) == len(b):
                raise ValueError(
                    "If sigma==None, a and b must have same length. "
                    + "Got {} and {}.".format(len(a), len(b))
                )
            sigma = np.eye(len(a), len(b))
        else:
            sigma = np.asarray(sigma)
            if 1 == len(sigma.shape):
                sigma = np.diag(sigma)
            assert len(a) == sigma.shape[0]
            assert len(b) == sigma.shape[1]

        # assert a.shape[1] == b.shape[1]
        if 0 < len(self._b):
            assert self._at.shape[0] == at.shape[0]
            assert self._b.shape[1] == b.shape[1]

            if self.n_max == np.inf or not self.inplace:
                # Just add them
                at_ = np.hstack([self._at, at])
                b_ = np.vstack([self._b, b])
                self_sigma = self._sigma
                if 1 == len(self_sigma.shape):
                    self_sigma = np.diag(self_sigma)
                sigma_ = block_diag((self_sigma, sigma))
            else:
                assert len(a) <= self.n_max
                assert len(b) <= self.n_max
                at_ = self._at
                b_ = self._b
                sigma_ = np.diag(self._sigma)

                na, nb = sigma.shape
                sigma_[-na:, -nb:] = sigma
                at_[:, -na:] = at
                b_[-nb:, :] = b
        else:
            # Dyadic sum is empty: just add the new ones
            at_ = at
            b_ = b
            sigma_ = sigma

        self.orthogonalize(at=at_, b=b_, sigma=sigma_)

    def orthogonalize(self, at=None, b=None, sigma=None):
        r"""Perform a QR decomposition of the dyadic components to
        make them orthogonal.

        Notes
        -----
        Let :math:`\ket{\mat{A}} =` :attr:`at` and :math:`\bra{\mat{B}} =`
        :attr:`b` and :math:`\mat{\sigma} =` :attr:`sigma`:

        .. math::
           \ket{\mat{A}}\mat{\sigma}\bra{\mat{B}}
           = \ket{\uvect{Q}_a}\mat{r}_a\mat{\sigma}\mat{r}_b^T\bra{\uvect{Q}_b}
           = \ket{\uvect{Q}_a}\mat{u}\mat{d}\mat{v}^T\bra{\uvect{Q}_b}
           = \ket{\uvect{A}}\mat{d}\bra{\uvect{B}}

        In order to compute the QR factorization of :math:`\ket{\mat{A}}`
        without working with the large matrices, we could do a Cholesky
        decomposition on

        .. math::
          \braket{\mat{A}|\mat{A}} &= \mat{r}_a^T\mat{r}_{a}\\
          \ket{\uvect{Q}} &= \ket{\mat{A}}\mat{r}_{a}^{-1}

        .. note:: These should be nicely accelerated using the BLAS
           routines for performing the operations in place.  In
           principle, :func:`numpy.dot` should do this, but at present
           there are issues with contiguity that force copies to be
           made.  Also, SciPy does not yet expose all BLAS operations,
           in particular `_SYRK` is missing.

        We perform a QR decomposition of these

        .. math::
           \mat{A} &= \mat{Q}_{A}\mat{R}_{A}, \\
           \mat{B} &= \mat{Q}_{B}\mat{R}_{B}

        and then an SVD of the product of the R factors
        :math:`\mat{U}\mat{D}\mat{V}^{\dagger} = \mat{R}_{A}\mat{R}_{B}^T`
        to obtain the new basis:

        .. math::
           \mat{M} = \mat{A}\mat{B}^{T}
           = \mat{Q}_{A}\mat{R}_{A}\mat{R}_{B}^{T}\mat{Q}_{B}^T
           = \left(\mat{Q}_{A}\mat{U}\right)\mat{D}
             \left(\mat{V}^{\dagger}\mat{Q}_{B}^T\right)

        .. math::
           \mat{A}_{\text{new}} &= \mat{Q}_{A}\mat{U}\sqrt{\mat{D}}, \\
           \mat{B}_{\text{new}} &= \mat{Q}_{B}\mat{V}^{*}\sqrt{\mat{D}}.
        """
        if at is None:
            at = self._at
            if 0 == np.prod(at.shape):
                # Empty.  Do nothing.  This should only happen on
                # default initialization.
                return

        if b is None:
            b = self._b
        if sigma is None:
            sigma = self._sigma
            if 1 == len(sigma.shape):
                sigma = np.diag(sigma)

        cholesky = False
        if cholesky:
            # Cholesky version: avoids working with large arrays.
            # This could be optimized using BLAS and LAPACK here for
            # both inplace operations and to avoid making copies.
            # Right now there is no point in the added complication.
            aa = matmul(at, at.T)
            bb = matmul(b, b.T)

            la = np.linalg.cholesky(aa)
            lb = np.linalg.cholesky(bb)
            ra = la.T
            rb = lb.T
            at = sp.linalg.cho_solve(clow=(lb, True), b=at.T).T
            b = sp.linalg.cho_solve(clow=(lb, True), b=b)
        else:
            qa, ra = np.linalg.qr(at)  # at = qa*ra
            qb, rb = np.linalg.qr(b.T)  # b = rb.T*qb.T
            sigma = matmul(ra, matmul(sigma, rb.T))
            if self.use_svd:
                u, d_, vt = np.linalg.svd(sigma)
                max_inds = np.where(d_ / d_.max() >= self.dynamic_range)[0]
                if 0 < len(max_inds):
                    max_ind = min(max_inds[-1] + 1, self.n_max)
                else:
                    max_ind = self.n_max
                max_ind = min(max_ind, len(u))
                at = matmul(qa, u[:, :max_ind])
                b = matmul(vt[:max_ind, :], qb.T)
                sigma = d_[:max_ind]
            else:
                at = qa
                b = qb.T

        self._at = at
        self._b = b
        self._sigma = sigma

    def apply_transform(self, f, fr=None):
        """Apply the linear transform `f` to the vectors forming the
        dyads.  If `fr` is `None`, this is applied to the right
        (bra's), otherwise `f` is applied to both sides.
        This is equivalent to the transformation
        `J -> I  + F*(J - I)*Fr.T`.

        .. note::
           This should be modified to be done in place if possible.

        Examples
        --------
        """
        if fr is None:
            fr = f
        if 0 < len(self._at):
            self._at = f(self._at)
            self._b = fr(self._b.T).T
            self.orthogonalize()

    def todense(self):
        """Return the matrix.

        Examples
        --------
        >>> M = DyadicSum()
        >>> M.todense()
        array(1.)
        >>> M.add_dyad([1, 0], [1, 0])
        >>> M.add_dyad([0, 2], [1, 0])
        >>> M.add_dyad([3, 0], [0, 1])
        >>> M.add_dyad([0, 4], [0, 1])
        >>> M.todense()
        array([[2., 3.],
               [2., 5.]])
        """
        if len(self._b) == 0:
            return np.array(self.alpha)

        if 1 == len(self._sigma.shape):
            M = matmul(self._at * self._sigma, self._b)
        else:
            M = matmul(self._at, matmul(self._sigma, self._b))
        return M + self.alpha * np.eye(*M.shape)

    def diag(self, k=0):
        r"""Return the diagonal of the matrix.

        Examples
        --------
        >>> M = DyadicSum()
        >>> M.diag()
        array(1.)
        >>> M.add_dyad([1, 0], [1, 0])
        >>> M.add_dyad([0, 2], [1, 0])
        >>> M.add_dyad([3, 0], [0, 1])
        >>> M.add_dyad([0, 4], [0, 1])
        >>> M.diag()
        array([2., 5.])
        """
        if len(self._b) == 0:
            return np.array(1.0)

        b = self._b

        if 1 == len(self._sigma.shape):
            at = self._at * self._sigma
        else:
            at = matmul(self._at, self._sigma)
        na = at.shape[0]
        nb = b.shape[1]
        ka = max(0, -k)
        kb = max(0, k)
        n = min(na - ka, nb - kb)
        d = (at[ka : ka + n, :].T * b[:, kb : kb + n]).sum(axis=0)
        if 0 == k:
            d += self.alpha
        return d

    def __matmul__(self, x):
        r"""Matrix multiplication: Return self*x."""
        if 0 == len(self._b):
            res = self.alpha * x
        else:
            shape = x.shape
            if 1 == len(shape):
                x = x.reshape((len(x), 1))
            if 1 == len(self._sigma.shape):
                res = self.alpha * x + matmul(
                    self._at, np.multiply(self._sigma[:, None], matmul(self._b, x))
                )
            else:
                res = self.alpha * x + matmul(
                    self._at, matmul(self._sigma, matmul(self._b, x))
                )
            res = res.reshape(shape)
        return res

    def __rmatmul__(self, x):
        r"""Matrix multiplication: Return x*self."""
        if 0 == len(self._b):
            res = self.alpha * x
        else:
            shape = x.shape
            if 1 == len(shape):
                x = x.reshape((1, len(x)))
            if 1 == len(self._sigma.shape):
                res = self.alpha * x + matmul(
                    np.multiply(matmul(x, self._at), self._sigma[None, :]), self._b
                )
            else:
                res = self.alpha * x + matmul(
                    matmul(matmul(x, self._at), self._sigma), self._b
                )
            res = res.reshape(shape)
        return res

    def inv(self):
        """Return the inverse using the Sherman-Morrison formula."""
        args = dict(
            n_max=self.n_max,
            use_svd=self.use_svd,
            inplace=self.inplace,
            dynamic_range=self.dynamic_range,
        )
        U = self._at
        if 1 == len(self._sigma.shape):
            V = self._sigma[:, None] * self._b
        else:
            V = self._sigma.dot(self._b)

        k, N = V.shape
        b = np.linalg.solve(np.eye(k) + V.dot(U) / self.alpha, V / self.alpha)
        at = -U / self.alpha

        J = DyadicSum(alpha=1.0 / self.alpha, at=at, b=b, **args)
        return J

    def dot(self, x):
        """Return the matrix multiplication of self with x."""
        return self.__matmul__(x)

    def __getitem__(self, key):
        r"""Minimal support of two-dimensional indexing.

        Examples
        --------
        >>> np.random.seed(1)
        >>> d = DyadicSum()
        >>> for n in range(10):
        ...     d.add_dyad(np.random.rand(100), np.random.rand(100))

        >>> inds = np.s_[[1, 2, 3, 5, 4, -98], 20:-2]
        >>> np.allclose(d[inds],
        ...             d.todense()[inds])
        True
        >>> inds = np.array([1, 3, 4, 2])
        >>> np.allclose(d[inds[:, None], inds[None, :]],
        ...             d.todense()[inds[:, None], inds[None, :]])
        True

        .. warning:: Assumes that the indexing is for extracting
           sub-arrays.  This is different from numpy.

        >>> np.allclose(d[inds, inds],
        ...             d.todense()[inds, inds])
        False
        >>> np.allclose(d[inds, inds],
        ...             d.todense()[inds[:, None], inds[None, :]])
        True
        """
        if 2 == len(key):
            at = self._at[key[0], :]
            b = self._b[:, key[1]]
            if 2 < len(b.shape):
                b = np.rollaxis(b, 0, -1)
            if 1 == len(self._sigma.shape):
                res = matmul(at * self._sigma, b).squeeze()
            else:
                res = matmul(at, matmul(self._sigma, b)).sqeeze()

            if res.shape == ():
                res = res.reshape((1, 1))

            ka = np.arange(self._at.shape[0])[key[0]].ravel()
            kb = np.arange(self._b.shape[1])[key[1]].ravel()
            res[np.where(ka[:, None] == kb[None, :])] += self.alpha
        else:
            raise ValueError(
                "{} only supports two-dimensional indexing.  Got {}".format(
                    self.__class__.__name__, repr(key)
                )
            )
        return res

    def update_broyden(self, dx, df, method="good"):
        """Add a dyad according to the Broyden update to satisfy the secant
        condition `B*dx = df`.

        Arguments
        ---------
        dx, df : vectors
           Difference in step and function values in search.
        method : 'good' or 'bad'
           Use either Broyden's "good" method which minimizes the change in
           the Frobenius norm of the Jacobian (the inverse of this DyadicSum),
           or the "bad" method which minimizes the change in the Frobenius norm
           of this DyadicSum representing the inverse Jacobian.
        """
        Bdf = self.dot(df)

        if method == "good":
            dxB = self.__rmatmul__(np.asarray(dx))  # dx @ self
            self.add_dyad((dx - Bdf) / dx.dot(Bdf), dxB)
        else:
            self.add_dyad((dx - Bdf) / df.dot(df), df)


class JacobianBFGS(sp.optimize.nonlin.Jacobian):
    r"""Represent a symmetric matrix by a memory-limited L-BFGS approximation.

    This assumes that the Jacobian :math:`J_{ij} = \partial_i\partial_j f(x)` is
    symmetric, and stores a memory-limited representation of the Hessian :math:`H =
    J^{-1}`.  This should be used for optimization problems minimizing :math:`f(x)`.

    See Chapter 7 of [Nocedal:2006] (7.19) in particular.

    .. [Nocedal:2006]
       Jorge Nocedal and Stephen J. Wright, `"Numerical Optimization"
       <http://dx.doi.org/10.1007/978-0-387-40065-5>`_,  ,  (2006)

    Attributes
    ----------
    _dx, _df : list
       List of the previous `k` differences.

    """

    def __init__(self, alpha=1.0, n_max=20):
        self._dx = []
        self._df = []
        self._H0 = alpha
        self._last_x = self._last_f = None
        self.n_max = n_max
        sp.optimize.nonlin.Jacobian.__init__(self)

    @property
    def H0(self):
        """Return the factor for the initial inverse Jacobian approximation.

        This default version uses equation (7.20) of [Nocedal:2006]
        """
        s, y = self._dx, self._df

        if len(y) >= 1:
            return s[-1].dot(y[-1]) / (y[-1].dot(y[-1]))
        else:
            return self._H0

    @property
    def dtype(self):
        return np.asarray(self._last_f).dtype

    @property
    def shape(self):
        return (len(np.asarray(self._last_f)),) * 2

    @property
    def _eye(self):
        """Return an appropriately sized identity matrix."""
        if self._dx:
            return np.eye(*self.shape, dtype=self.dtype)
        else:
            return np.array(1.0, dtype=self.dtype)

    def solve(self, v):
        """Return `H.dot(v)` where `H` is the inverse Jacobian.

        Uses Algorithm (7.4) of [Nocedal:2006]
        """
        if not self._dx:  # Short circuit if no updates have been given
            return self._H0 * v
        s_, y_ = self._dx, self._df
        q = np.asarray(v).copy()
        q_shape = q.shape
        if 1 == len(q_shape):
            q = q[:, None]
        k = len(y_)
        alpha = np.empty((k, q.shape[1]), dtype=q.dtype)
        rho = np.empty(k, dtype=self.dtype)
        for i in reversed(range(k)):
            s, y = s_[i], y_[i]
            rho[i] = 1.0 / (y.dot(s))
            alpha[i, ...] = rho[i] * (s.dot(q))
            q -= alpha[i][None, :] * y[:, None]
        q *= self.H0
        r = q
        for i in range(k):
            s, y = s_[i], y_[i]
            beta = rho[i] * y.dot(r)
            r += (alpha[i] - beta)[None, :] * s[:, None]
        return r.reshape(q_shape)

    def dense_H(self):
        """Return a dense array with the inverse Jacobian H.

        Uses (7.16) and (7.17) of [Nocedal:2006]
        """
        # V = I - rho*y.s.T
        # H . V = H - rho*(H . y) . s.T
        # V.T . H . V = (I - rho*s . y.T) . (H - rho*(H . y) . s.T)
        #             = (H - rho*[(H.y) . s.T + transpose]
        #               + rho**2 * s . (y.T . H . y) . s.T)
        I = self._eye
        H = self.H0 * I
        for s, y in zip(self._dx, self._df):
            rho = 1.0 / (y.dot(s))
            V = I - rho * y[:, None] * s[None, :]
            H = V.T.dot(H).dot(V) + rho * s[:, None] * s[None, :]
        return np.asarray(H)

    def dense_J(self):
        """Return a dense array with the Jacobian J."""
        return np.linalg.inv(self.dense_H())

    todense = toarray = dense_J

    def update(self, x, f):
        if self._last_x is not None:
            dx = x - self._last_x
            df = f - self._last_f
            if np.allclose(0, df.dot(dx), atol=_EPS ** 2):
                raise np.linalg.LinAlgError("Current step makes Jacobian singular.")
            self._dx.append(dx)
            self._df.append(df)
            if len(self._dx) > self.n_max:
                self._dx = self._dx[-self.n_max :]
                self._df = self._df[-self.n_max :]
        self._last_x, self._last_f = x, f


class Jacobian(DyadicSum):
    """Provides the `scipy.optimize.nonlin.Jacobian` interface."""

    def __init__(self, method="good", *v, **kw):
        DyadicSum.__init__(self, *v, **kw)
        self.last_f = None
        self.last_x = None
        self.method = method

    def solve(self, v):
        return self.inv().dot(v)

    def rsolve(self, v):
        return self.inv().__rmatmul__(v)

    def update(self, x, f):
        if self.last_x is not None:
            dx = x - self.last_x
            df = f - self.last_f
            self.update_broyden(dx=dx, df=df, method=self.method)
        self.last_x = np.copy(x)
        self.last_f = np.copy(f)

    def matvec(self, v):
        return self.__matmul__(v)

    def rmatvec(self, v):
        return self.__rmatmul__(v)


class L_BFGS(object):
    """Simple implementation of the L_BFGS algorithm."""

    def __init__(self, f, df, x0, alpha=1.0, n_max=10):
        self.f = f
        self.df = df
        self.x0 = x0
        self.s_ = []  # Last m steps dx
        self.y_ = []  # Last m changes in df
        self.B = DyadicSum(alpha=alpha, n_max=n_max)

    def get_search_direction(self, df):
        """Return the search direction"""
        sy = s_.T.dot(y_)
        delta = sy[-1, -1]
        R = np.asarray(np.bmat([[delta * s_], [y_]]))
        L = np.tril(sy)
        D = np.diag(np.diag(sy))
        M = np.asarray(np.bmat([[delta * s_.T.dot(s_), L], [L.T, -D]]))

        search_direction = -delta * df - R.dot(np.linalg.solve(M, R_.T.dot(df)))
        return search_direction
