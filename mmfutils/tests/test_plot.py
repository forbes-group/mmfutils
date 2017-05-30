import os
import tempfile

import numpy as np
from matplotlib import pyplot as plt

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


class TestRasterize(object):
    def test_contourf(self):
        with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
            x, y = np.meshgrid(*(np.linspace(-1, 1, 500),)*2)
            z = np.sin(20*x**2)*np.cos(30*y)
            plt.contourf(x, y, z, 30)

            plt.savefig(f.name)
            size_unrasterized = os.stat(f.name).st_size

            plt.clf()
            mmfplt.contourf(x, y, z, 30, rasterized=True)

            plt.savefig(f.name)
            size_rasterized = os.stat(f.name).st_size

        assert size_rasterized < size_unrasterized/25
