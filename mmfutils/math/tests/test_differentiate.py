from mmfutils.math.differentiate import differentiate

import math

import nose.tools as nt


class TestDifferentiate(object):
    def test_left_1(self):
        """Test directional first derivatives"""
        x0 = math.pi / 4.0
        y0 = 1./math.sqrt(2)
        kw = dict(h0=0.8, d=1, x=x0)

        def f(x):
            return abs(math.sin(x)-y0)

        exact = -math.cos(x0)
        res = differentiate(f, dir=-1, **kw)
        nt.assert_almost_equal(res, exact, places=12)

        exact = math.cos(x0)
        res = differentiate(f, dir=+1, **kw)
        nt.assert_almost_equal(res, exact, places=12)

    def test_left_2(self):
        """Test directional second derivatives"""
        x0 = math.pi / 4.0
        y0 = 1./math.sqrt(2)
        kw = dict(h0=0.4, d=2, x=x0)

        def f(x):
            return abs(math.sin(x)-y0)

        exact = math.sin(x0)
        res = differentiate(f, dir=-1, **kw)
        nt.assert_almost_equal(res, exact, places=9)

        exact = -math.sin(x0)
        res = differentiate(f, dir=+1, **kw)
        nt.assert_almost_equal(res, exact, places=9)
