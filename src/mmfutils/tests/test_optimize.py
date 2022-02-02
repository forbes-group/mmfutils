from mmfutils import optimize

import numpy as np

from uncertainties import ufloat


class Test(object):
    def test_usolve(self):
        n = ufloat(2.0, 0.1, "n")
        c = ufloat(1.0, 0.1, "c")
        a = ufloat(3.0, 0.1, "a")

        def f(x):
            return x ** n - a * c

        ans = optimize.ubrentq(f, 0, max(1, a))
        exact = (a * c) ** (1.0 / n)
        res = ans - exact
        assert np.allclose(0, [res.nominal_value, res.std_dev])

    def test_usolve_1(self):
        """Should also work with regular numbers (which is faster)."""
        n = 2.0
        c = 1.0
        a = 3.0

        def f(x):
            return x ** n - a * c

        ans = optimize.ubrentq(f, 0, max(1, a))
        exact = (a * c) ** (1.0 / n)
        assert np.allclose(ans, exact)
