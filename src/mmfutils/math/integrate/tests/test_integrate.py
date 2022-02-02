import itertools

import numpy as np

import pytest

from mmfutils.math import integrate


class TestRichardson(object):
    def test_scaling(self):
        """Test the Richardson extrapolation for the correct scaling behaviour.

        We use a centered difference scheme here, so only even powers of `h`
        should play a role.  Each successive iteration should show an
        improvement."""
        x = 1.0
        f = np.exp
        df = np.exp(x)

        def D(h):
            return (f(x + h) - f(x - h)) / 2 / h

        def F(N):
            h = 1.0 / N
            return D(h)

        def err(h, n=1):
            n0 = 1.0 / h
            r = integrate.Richardson(F, n0=n0, l=2.0, ps=itertools.count(2, 2))
            for _n in range(n):
                next(r)
            return abs(next(r) - df)

        # Draw the following to identify where these points should be for
        # calculating the slope:
        # hs = 10**linspace(-5,1,100)
        # for n in range(7):
        #     plt.plot(np.log10(hs), np.log10(err(hs, n=n)))
        lh = [-4, -2.3, -1.2, -0.5, 0.0, 0.36, 0.72]
        rh = [0, 0, 0, 0.3, 0.5, 0.6, 0.8]

        def slope(n):
            return (
                np.log10(err(10 ** rh[n], n=n)) - np.log10(err(10 ** lh[n], n=n))
            ) / (rh[n] - lh[n])

        ns = np.arange(6)
        slopes = 2 * (ns + 1)
        assert np.allclose(list(map(slope, ns)), slopes, rtol=0.05)


@pytest.fixture(params=[integrate.ssum, integrate.ssum_python])
def ssum(request):
    yield request.param


@pytest.fixture(params=[integrate.ssum_numba, integrate.ssum_cython])
def ssum_fast(request):
    yield request.param


@pytest.fixture(
    params=[np.int32, np.int64, np.float32, np.float64, np.complex64, np.complex128]
)
def dtype(request):
    yield request.param


class TestSSum(object):
    def test_1(self, ssum):
        N = 10000
        l = np.array([(10.0 * n) ** 3.0 for n in reversed(range(N + 1))])
        ans = 250.0 * ((N + 1.0) * N) ** 2
        assert np.allclose(ssum(l)[0] - ans, 0)
        assert not np.allclose(sum(l) - ans, 0)

    def test_harmonic(self, ssum):
        """Harmonic series.

        Series such as these  should be summed in reverse, but ssum
        should do it well."""
        sn = 1.0 / np.arange(1, 10 ** 4)
        Hn, Hn_err = integrate.exact_sum(sn)
        ans, err = ssum(sn)
        assert abs(ans - Hn) < err
        assert not abs(sum(sn) - Hn) < err  # Normal sum not good...
        assert abs(sum(reversed(sn)) - Hn) < err  # unless elements sorted

    def test_truncation(self, ssum):
        N = 10000
        np.random.seed(3)
        r = np.random.randint(-(2 ** 30), 2 ** 30, 4 * N)
        A = np.array(
            [
                int(a) * 2 ** 90 + int(b) * 2 ** 60 + int(c) * 2 ** 30 + int(d)
                for (a, b, c, d) in zip(
                    r[:N], r[N : 2 * N], r[2 * N : 3 * N], r[3 * N : 4 * N]
                )
            ]
        )
        B = A.astype(float) / 3987.0  # Introduce truncation errors
        exact_ans = A.sum()
        ans, err = ssum(B)
        ans *= 3987.0
        err *= 3987.0
        exact_err = abs(float(int(ans) - exact_ans))
        assert exact_err < err
        assert not exact_err < err / 1000.0

    def test_types(self, ssum, dtype):
        N = 10
        l = np.array([(10 * n) ** 3 for n in reversed(range(N + 1))])
        exact_ans = sum(l)
        x = np.asarray(l, dtype=dtype)
        res = ssum(x)
        assert np.allclose(res[0], exact_ans)

    def test_broken_import(self):
        """Test that broken import of _ssum_cython does not cause error."""
        _ssum_cython, integrate._ssum_cython = integrate._ssum_cython, None
        self.test_harmonic(ssum=integrate.ssum_cython)
        integrate._ssum_cython = _ssum_cython
