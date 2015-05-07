import nose.tools as nt
from nose.plugins.attrib import attr

from mmfutils.performance import blas
import numpy as np
import timeit


class Test_BLAS(object):
    def setUp(self):
        np.random.seed(1)

    def rand(self, shape, complex=True):
        X = np.random.random(shape) - 0.5
        if complex:
            X = X + 1j*(np.random.random(shape) - 0.5)
        return X

    def test_zdotc(self):
        shape = (100, 10)
        x = self.rand(shape)
        y = self.rand(shape)

        exact = (x.conj() * y).sum()
        nt.assert_almost_equal(blas._zdotc(x, y), exact)
        nt.assert_almost_equal(blas._zdotc_no_blas(x, y), exact)

    @attr('bench')
    def test_zdotc_bench(self):
        shape = (50, 50)
        x = self.rand(shape)
        y = self.rand(shape)

        t1 = timeit.repeat(lambda: blas._zdotc(x, y), number=100)
        t2 = timeit.repeat(lambda: np.dot(x.conj().ravel(), y.ravel()),
                           number=100)
        nt.assert_less(min(t1), min(t2)/2)

    def test_zaxpy(self):
        shape = (10, 10, 10)
        x = self.rand(shape)
        y1 = self.rand(shape)
        y2 = y1.copy()
        a = self.rand(1)

        exact = (y1 + a * x)
        r1 = blas._zaxpy(y1, x, a)
        r2 = blas._zaxpy_no_blas(y2, x, a)
        nt.ok_(np.allclose(r1, exact))
        nt.ok_(np.allclose(r2, exact))
        nt.ok_(np.allclose(y1, exact))
        nt.ok_(np.allclose(y2, exact))

    @attr('bench')
    def test_zaxpy_bench(self):
        shape = (50, 50, 50)
        x = self.rand(shape)
        y1 = self.rand(shape)
        y2 = y1.copy()
        a = self.rand(1)

        t1 = timeit.repeat(lambda: blas._zaxpy(y1, x, a), number=100)
        t2 = timeit.repeat(lambda: blas._zaxpy_no_blas(y2, x, a), number=100)
        nt.assert_less(min(t1), min(t2)/2)

    def test_daxpy(self):
        shape = (10, 10, 10)
        x = self.rand(shape, complex=False)
        y1 = self.rand(shape, complex=False)
        a = self.rand(1, complex=False)

        exact = (y1 + a * x)
        r1 = blas._daxpy(y1, x, a)
        nt.ok_(np.allclose(r1, exact))
        nt.ok_(np.allclose(y1, exact))

    @attr('bench')
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
        nt.assert_less(min(t1), min(t2)/2)
