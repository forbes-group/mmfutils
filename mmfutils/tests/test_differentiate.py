import numpy as np

import nose.tools as nt

from mmfutils.math.differentiate import differentiate


class TestCoverage(object):
    """Some edge cases to ensure coverage"""

    def test_differentiate(self):
        """Test 3rd order differentiation"""
        def f(x):
            return np.sin(2*x)

        x = 1.0
        for d in range(5):
            exact = (2j**d*np.exp(2j*x)).imag
            nt.assert_almost_equal(
                exact, differentiate(f, 1, d=d))
