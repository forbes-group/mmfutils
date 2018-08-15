import itertools

import numpy as np

from mmfutils.math.integrate import Richardson


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
            return (f(x + h) - f(x - h))/2/h

        def F(N):
            h = 1./N
            return D(h)

        def err(h, n=1):
            n0 = 1./h
            r = Richardson(F, n0=n0, l=2.0, ps=itertools.count(2, 2))
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
            return (np.log10(err(10**rh[n], n=n))
                    - np.log10(err(10**lh[n], n=n)))/(rh[n]-lh[n])

        ns = np.arange(6)
        slopes = 2*(ns + 1)
        assert np.allclose(list(map(slope, ns)), slopes, rtol=0.05)
