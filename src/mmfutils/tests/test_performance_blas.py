from mmfutils.performance import blas
import numpy as np
import timeit

import pytest


class Test_BLAS(object):
    @classmethod
    def setup_class(cls):
        np.random.seed(10)

    def rand(self, shape, complex=True):
        X = np.random.random(shape) - 0.5
        if complex:
            X = X + 1j * (np.random.random(shape) - 0.5)
        return X

    def test_zdotc(self):
        shape = (100, 10)
        x = self.rand(shape)
        y = self.rand(shape)

        exact = (x.conj() * y).sum()
        assert np.allclose(blas._zdotc(x, y), exact)
        assert np.allclose(blas._zdotc_no_blas(x, y), exact)

    @pytest.mark.bench
    def test_zdotc_bench(self):
        shape = (50, 50)
        x = self.rand(shape)
        y = self.rand(shape)

        t1 = timeit.repeat(lambda: blas._zdotc(x, y), number=100)
        t2 = timeit.repeat(lambda: np.dot(x.conj().ravel(), y.ravel()), number=100)
        assert min(t1) < min(t2) / 2

    def test_ddot(self):
        shape = (100, 10)
        x = self.rand(shape, complex=False)
        y = self.rand(shape, complex=False)

        exact = (x * y).sum()
        assert np.allclose(blas._ddot(x, y), exact)
        assert np.allclose(blas._ddot_no_blas(x, y), exact)

    @pytest.mark.bench
    def test_ddot_bench(self):
        shape = (50, 50)
        x = self.rand(shape, complex=False)
        y = self.rand(shape, complex=False)

        t1 = timeit.repeat(lambda: blas._ddot(x, y), number=100)
        t2 = timeit.repeat(lambda: blas._zdotc(x, y), number=100)
        assert min(t1) < min(t2) / 2

    def test_zaxpy(self):
        shape = (10, 10, 10)
        x = self.rand(shape)
        y1 = self.rand(shape)
        y2 = y1.copy()
        a = self.rand(1)

        exact = y1 + a * x
        r1 = blas._zaxpy(y1, x, a)
        r2 = blas._zaxpy_no_blas(y2, x, a)
        assert np.allclose(r1, exact)
        assert np.allclose(r2, exact)
        assert np.allclose(y1, exact)
        assert np.allclose(y2, exact)

    @pytest.mark.bench
    def test_zaxpy_bench(self):
        shape = (50, 50, 50)
        x = self.rand(shape)
        y1 = self.rand(shape)
        y2 = y1.copy()
        a = self.rand(1)

        t1 = timeit.repeat(lambda: blas._zaxpy(y1, x, a), number=100)
        t2 = timeit.repeat(lambda: blas._zaxpy_no_blas(y2, x, a), number=100)
        assert min(t1) < min(t2) / 2

    def test_daxpy(self):
        shape = (10, 10, 10)
        x = self.rand(shape, complex=False)
        y1 = self.rand(shape, complex=False)
        a = self.rand(1, complex=False)

        exact = y1 + a * x
        r1 = blas._daxpy(y1, x, a)
        assert np.allclose(r1, exact)
        assert np.allclose(y1, exact)

    @pytest.mark.bench
    def test_daxpy_bench(self):
        shape = (100, 50, 50)
        x1 = self.rand(shape, complex=False)
        y1 = self.rand(shape, complex=False)
        a1 = self.rand(1, complex=False)
        x2 = 0j + x1
        y2 = 0j + y1
        a2 = 0j + a1

        t1 = timeit.repeat(lambda: blas._daxpy(y1, x1, a1), number=100)
        t2 = timeit.repeat(lambda: blas._zaxpy(y2, x2, a2), number=100)
        assert min(t1) < min(t2) / 2

    def test_znorm(self):
        shape = (100, 10)
        x = self.rand(shape)

        exact = np.sqrt((abs(x.ravel()) ** 2).sum())
        assert np.allclose(blas._znorm(x), exact)
        assert np.allclose(blas._norm_no_blas(x), exact)

    def test_dnorm(self):
        shape = (100, 10)
        x = self.rand(shape, complex=False)

        exact = np.sqrt((abs(x.ravel()) ** 2).sum())
        assert np.allclose(blas._dnorm(x), exact)
        assert np.allclose(blas._norm_no_blas(x), exact)

    # http://lists.mcs.anl.gov/pipermail/petsc-dev/2012-January/006934.html
    @pytest.mark.bench
    @pytest.mark.skipif(True, reason="BLAS is more accurate, not faster!")
    def test_znorm_bench(self):
        shape = (500, 500)
        x = self.rand(shape)

        t1 = timeit.repeat(lambda: blas._znorm(x), number=100)
        t2 = timeit.repeat(lambda: np.linalg.norm(x.ravel()), number=100)
        assert min(t1) < min(t2)

    @pytest.mark.bench
    def test_dnorm_bench(self):
        shape = (1000, 1000)
        x = self.rand(shape, complex=False)
        y = x + 0j

        t1 = timeit.repeat(lambda: blas._dnorm(x), number=100)
        t2 = timeit.repeat(lambda: blas._znorm(y), number=100)
        assert min(t1) < min(t2)
