import numpy as np

from uncertainties import ufloat

import pytest

from mmfutils import testing


class TestTesting(object):
    def test_allclose(self):
        allclose = testing.allclose

        # Floats
        a, b = 1.0, 1.01
        assert allclose(a, b, atol=0.01)
        assert not allclose(a, b)

        # Arrays
        a, b = np.array(1.0), np.array(1.01)
        assert allclose(a, b, rtol=0.01)

        # Ufloats
        a, b = ufloat(1.0, 0.01), ufloat(1.01, 0.01)
        assert allclose(a, b, atol=0.01)
        assert allclose(a, b, use_covariance=True)
        assert not allclose(a, b)

        # Ufloats and floats
        a, b = ufloat(1.0, 0.02), 1.01
        assert allclose(a, b, atol=0.01)
        assert allclose(a, b, use_covariance=True)
        assert not allclose(a, b)

        b, a = ufloat(1.0, 0.02), 1.01
        assert allclose(a, b, atol=0.01)
        assert allclose(a, b, use_covariance=True)
        assert not allclose(a, b, use_covariance=0.1)
        assert not allclose(a, b)

        b, a = ufloat(1.0, 0.01), 1.02
        assert not allclose(a, b, use_covariance=True)
        assert allclose(a, b, use_covariance=2.1)

        # Equality testing
        assert allclose("123", "123")

    def test_coverage(self):
        unumpy, testing.unumpy = testing.unumpy, None
        try:
            allclose = testing.allclose
            a, b = ufloat(1.0, 0.1), 1.01
            with pytest.raises(ValueError):
                assert allclose(a, b, use_covariance=True)

        finally:
            testing.unumpy = unumpy
