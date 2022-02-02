import numpy as np

from mmfutils.math.differentiate import differentiate


class TestCoverage(object):
    """Some edge cases to ensure coverage"""

    def test_differentiate(self):
        """Test 3rd order differentiation"""

        def f(x):
            return np.sin(2 * x)

        x = 1.0
        for d in range(5):
            exact = (2j ** d * np.exp(2j * x)).imag
            assert np.allclose(exact, differentiate(f, 1, d=d))
