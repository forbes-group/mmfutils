import os
import tempfile

import numpy as np
from matplotlib import pyplot as plt

from mmfutils import plot as mmfplt

import pytest


class TestMidpointNormalize(object):
    def test_mask(self):
        A = np.ma.MaskedArray([1, 2, 3], mask=[0, 0, 1])
        assert np.allclose([0.75, 1.0, np.nan], mmfplt.MidpointNormalize()(A))

        A = np.ma.MaskedArray([1, 2, 3], mask=[1, 1, 1])
        assert np.allclose(A.mask, mmfplt.MidpointNormalize()(A).mask)


class TestRasterize(object):
    def test_contourf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            x, y = np.meshgrid(*(np.linspace(-1, 1, 500),) * 2)
            z = np.sin(20 * x**2) * np.cos(30 * y)
            plt.contourf(x, y, z, 30)

            plt.savefig(f.name)
            size_unrasterized = os.stat(f.name).st_size

            plt.clf()
            mmfplt.contourf(x, y, z, 30, rasterized=True)

            plt.savefig(f.name)
            size_rasterized = os.stat(f.name).st_size

        assert size_rasterized < size_unrasterized / 20


class TestContour(object):
    """Test bug with unequally spaced contours"""

    def test(self):
        x = np.array([0, 1, 3])[:, None]
        y = np.array([0, 2, 3])[None, :]
        z = x + 1j * y

        c = mmfplt.colors.color_complex(z)
        mmfplt.imcontourf(x, y, c)


class TestErrorBars:
    """Test errorbar plots.

    These mostly just check that the code executes.  (Testing plot generation is hard.)
    """

    def test_error_line(self):
        x = np.linspace(0, 5)
        y = x**2
        dy = 0.1 * np.sin(x)
        mmfplt.error_line(x, y, dy)

    def test_plot_err(self):
        x = np.linspace(0, 5)
        y = x**2
        dy = 0.1 * np.sin(x)
        dx = 0.1 * np.cos(x)
        with pytest.raises(ValueError) as e:
            mmfplt.plot_err(x, y, abs(dy), dx)
        assert e.value.args[0] == "'xerr' must not contain negative values"
        with pytest.raises(ValueError) as e:
            mmfplt.plot_err(x, y, dy, abs(dx))
        assert e.value.args[0] == "'yerr' must not contain negative values"
        mmfplt.plot_err(x, y, abs(dy), abs(dx))

    def test_plot_errorbars(self):
        x = np.linspace(0, 5)
        y = x**2
        dy = 0.1 * np.sin(x)
        dx = 0.1 * np.cos(x)
        mmfplt.plot_errorbars(x, y, dy, dx)
