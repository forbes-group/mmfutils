import sys

import numpy as np
import scipy.optimize.nonlin
import scipy as sp

import pytest

from mmfutils.solve import broyden


@pytest.fixture(params=[-0.5, 0.5, 1.0])
def alpha(request):
    yield request.param


@pytest.fixture(params=["good", "bad"])
def method(request):
    yield request.param


@pytest.fixture
def dyadic_sum(alpha):
    np.random.seed(1)
    a = np.random.random((3, 4)) - 0.5
    b = np.random.random((3, 4)) - 0.5
    B = broyden.DyadicSum(alpha=alpha, n_max=np.inf)
    B.add_dyad(a.T, b)
    B_ = alpha * np.eye(4) + a.T.dot(b)
    yield (B, B_)


@pytest.fixture
def jacobian(alpha):
    np.random.seed(1)
    a = np.random.random((3, 4)) - 0.5
    b = np.random.random((3, 4)) - 0.5
    B = broyden.Jacobian(alpha=alpha, n_max=np.inf)
    B.add_dyad(a.T, b)
    B_ = alpha * np.eye(4) + a.T.dot(b)
    assert np.allclose(B_, B.todense())
    B_ = sp.optimize.nonlin.asjacobian(B_)
    x = np.random.random(4) - 0.5
    yield (B, B_, x)


class TestDyadicSum(object):
    def test_add_dyad(self, dyadic_sum):
        B, B_ = dyadic_sum
        assert np.allclose(B.todense(), B_)

    def test_dot(self, dyadic_sum):
        B, B_ = dyadic_sum
        np.random.seed(2)
        A = np.random.random(B_.shape) - 0.5

        assert np.allclose(B_, B.todense())
        assert np.allclose(B_.dot(A), B.dot(A))

        if sys.version_info >= (3, 5):
            # assert np.allclose(B_ @ A, B @ A)
            # assert np.allclose(A @ B_, A @ B)
            assert np.allclose(B_.dot(A), eval("B @ A"))
            assert np.allclose(A.dot(B_), eval("A @ B"))

    def test_errors(self):
        """Test error messages"""
        with pytest.raises(ValueError) as e:
            broyden.DyadicSum(n_max=2, use_svd=False)
        assert e.value.args[0] == "Finite `n_max=2` requires `svd=True`."

        s = broyden.DyadicSum()
        with pytest.raises(ValueError) as e:
            s["x"]
        assert (
            e.value.args[0]
            == "DyadicSum only supports two-dimensional indexing.  Got 'x'"
        )

        a = np.random.random((4, 6))
        b = np.random.random((5, 6))
        s = broyden.DyadicSum(n_max=np.inf)
        with pytest.raises(ValueError) as e:
            s.add_dyad(a.T, b)
        assert (
            e.value.args[0]
            == "If sigma==None, a and b must have same length. Got 4 and 5."
        )

    def test_rectangular(self):
        """Test rectangular matrices"""
        a = np.random.random((6, 4))
        b = np.random.random((6, 5))
        s = broyden.DyadicSum()
        s.add_dyad(a.T, b)

    def test_update_broyden(self, dyadic_sum, method):
        B, B_ = dyadic_sum
        np.random.seed(1)

        dx = np.random.random(4)
        df = np.random.random(4)

        B.update_broyden(dx=dx, df=df, method=method)

        assert np.allclose(B.dot(df), dx)

    def test_inv(self, dyadic_sum):
        B, B_ = dyadic_sum
        assert np.allclose(B.inv().todense(), np.linalg.inv(B_))


class TestJacobianBFGS(object):
    """Test the JacobianBFGS object."""

    def test_1(self):
        J = broyden.JacobianBFGS()
        np.random.seed(1)
        k = 3
        N = 4
        dxs = np.random.random((k, N)) - 0.5
        dfs = np.random.random((k, N)) - 0.5
        x = np.random.random(N) - 0.5
        f = np.random.random(N) - 0.5
        v = np.random.random(N) - 0.5
        J.update(x, f)
        for dx, df in zip(dxs, dfs):
            x, f = x + dx, f + df
            J.update(x, f)
            H = J.dense_H()
            assert np.allclose(H.dot(df), dx)
            assert np.allclose(J.solve(df), dx)

        H = J.dense_H()
        assert np.allclose(J.solve(v), H.dot(v))
        assert np.allclose(np.eye(*J.shape), J.solve(J.dense_J()))


class TestDyadicSumJacobian(object):
    """Test the `scipy.optimize.nonlin.Jacobian` interface."""

    def test_1(self, jacobian):
        B, B_, x = jacobian
        assert B.dtype == B_.dtype
        assert B.shape == B_.shape
        assert np.allclose(B.solve(v=x), B_.solve(v=x))
        assert np.allclose(B.rsolve(v=x), B_.rsolve(v=x))
        assert np.allclose(B.matvec(v=x), B_.matvec(v=x))
        assert np.allclose(B.rmatvec(v=x), B_.rmatvec(v=x))


class TestDyadicSumDoctestPython3(object):
    """Doctests of Python 3 features.

    We can't include these as regular tests because they will fail
    with a SyntaxError.

    >>> np.random.seed(3)
    >>> N, n, m = 20, 5, 3
    >>> At = np.random.random((N, n+m))
    >>> B = np.random.random((n+m, N))
    >>> at = At[:, :n]
    >>> b = B[:n, :]
    >>> sigma = np.eye(n)
    >>> s = broyden.DyadicSum(at=at, b=b, sigma=sigma, n_max=n)
    >>> np.allclose(s._at*s._sigma @ s._b, at @ b)
    True

    Now we add the remaining terms.  The dyadic sum should be the
    best rank n approximation of `At @ B`:

    >>> s.add_dyad(at=At[:, n:], b=B[n:, :], sigma=np.eye(m))
    >>> U, d, Vt = np.linalg.svd(At @ B)
    >>> d[n:] = 0                   # Make rank deficient approx
    >>> np.allclose(s._at*s._sigma @ s._b, U*d @ Vt)
    True

    Note that the approximation is not exact:

    >>> np.allclose(s._at*s._sigma @ s._b, At @ B)
    False

    >>> np.allclose(s._at*s._sigma @ s._b, At @ B)
    False

    >>> J = broyden.DyadicSum()
    >>> x = np.array([[1.0],
    ...               [2.0]])
    >>> J @ x - x
    array([[0.],
           [0.]])
    >>> b = np.array([[1.0, 0.0]])
    >>> a = np.array([[0.0],
    ...               [2.0]])

    >>> J.add_dyad(a, b)
    >>> J @ x
    array([[1.],
           [4.]])
    >>> x.T @ J
    array([[5., 2.]])
    >>> J.__rmatmul__(x.T)
    array([[5., 2.]])
    """


if sys.version_info < (3, 5):
    # Delete this class and don't test if @ is not defined.
    del TestDyadicSumDoctestPython3
