import numpy as np

from mmfutils import plot as mmfplt


class TestMidpointNormalize(object):
    def test_mask(self):
        A = np.ma.MaskedArray([1, 2, 3], mask=[0, 0, 1])
        assert np.allclose(
            [0.75, 1.0, np.nan],
            mmfplt.MidpointNormalize()(A))

        A = np.ma.MaskedArray([1, 2, 3], mask=[1, 1, 1])
        assert np.allclose(
            A.mask,
            mmfplt.MidpointNormalize()(A).mask)
