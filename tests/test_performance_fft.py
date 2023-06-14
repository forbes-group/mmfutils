import sys
import numpy as np

import mmfutils.performance.fft

import pytest

# import timeit


@pytest.fixture
def fft(threads):
    from mmfutils.performance import fft

    fft.set_num_threads(threads)
    yield fft


class Test_FFT(object):
    @classmethod
    def setup_class(cls):
        np.random.seed(1)

    def rand(self, shape, complex=True, writeable=False):
        X = np.random.random(shape) - 0.5
        if complex:
            X = X + 1j * (np.random.random(shape) - 0.5)

        # The default builders should respect this.  See issue #32.
        X.flags["WRITEABLE"] = writeable
        return X

    def test_fft(self, fft):
        shape = (256, 256)
        x = self.rand(shape)
        for axis in [None, 0, 1, -1, -2]:
            kw = {}
            if axis is not None:
                kw = dict(axis=axis)
            assert np.allclose(fft.fft_numpy(x, **kw), np.fft.fft(x, **kw))
            assert np.allclose(fft.ifft_numpy(x, **kw), np.fft.ifft(x, **kw))

    def test_fftn(self, fft):
        shape = (256, 256)
        x = self.rand(shape)
        for axes in [None, [0], [1], [-1], [-2], [1, 0]]:
            kw = {}
            if axes is not None:
                kw = dict(axes=axes)
            assert np.allclose(fft.fftn_numpy(x, **kw), np.fft.fftn(x, **kw))
            assert np.allclose(fft.ifftn_numpy(x, **kw), np.fft.ifftn(x, **kw))


@pytest.mark.skipif(
    not hasattr(mmfutils.performance.fft, "pyfftw"), reason="requires pyfftw"
)
class Test_FFT_pyfftw(Test_FFT):
    @classmethod
    def setup_class(cls):
        np.random.seed(1)

    def test_fft_pyfftw(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=False)
        for axis in [None, 0, 1, -1, -2]:
            kw = {}
            if axis is not None:
                kw = dict(axis=axis)
            assert np.allclose(fft.fft_pyfftw(x, **kw), np.fft.fft(x, **kw))
            assert np.allclose(fft.ifft_pyfftw(x, **kw), np.fft.ifft(x, **kw))

    def test_fftn_pyfftw(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=False)
        for axes in [None, [0], [1], [-1], [-2], [1, 0]]:
            kw = {}
            if axes is not None:
                kw = dict(axes=axes)
            assert np.allclose(fft.fftn_pyfftw(x, **kw), np.fft.fftn(x, **kw))
            assert np.allclose(fft.ifftn_pyfftw(x, **kw), np.fft.ifftn(x, **kw))

    def test_get_fft_pyfftw(self, threads):
        fft = mmfutils.performance.fft
        shape = (256, 256)
        x = self.rand(shape, writeable=True)

        fft.set_num_threads(threads)
        for axis in [None, 0, 1, -1, -2]:
            kw = {}
            if axis is not None:
                kw = dict(axis=axis)
            assert np.allclose(fft.get_fft_pyfftw(x, **kw)(x), np.fft.fft(x, **kw))
            assert np.allclose(fft.get_ifft_pyfftw(x, **kw)(x), np.fft.ifft(x, **kw))

    def test_get_fftn_pyfftw(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=True)
        for axes in [None, [0], [1], [-1], [-2], [1, 0]]:
            kw = {}
            if axes is not None:
                kw = dict(axes=axes)
            assert np.allclose(fft.get_fftn_pyfftw(x, **kw)(x), np.fft.fftn(x, **kw))
            assert np.allclose(fft.get_ifftn_pyfftw(x, **kw)(x), np.fft.ifftn(x, **kw))

    def test_get_fft(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=True)
        for axis in [None, 0, 1, -1, -2]:
            kw = {}
            if axis is not None:
                kw = dict(axis=axis)
            assert np.allclose(fft.get_fft(x, **kw)(x), np.fft.fft(x, **kw))
            assert np.allclose(fft.get_ifft(x, **kw)(x), np.fft.ifft(x, **kw))

    def test_get_fftn(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=True)
        for axes in [None, [0], [1], [-1], [-2], [1, 0]]:
            kw = {}
            if axes is not None:
                kw = dict(axes=axes)
            assert np.allclose(fft.get_fftn(x, **kw)(x), np.fft.fftn(x, **kw))
            assert np.allclose(fft.get_ifftn(x, **kw)(x), np.fft.ifftn(x, **kw))

    def test_fft(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=False)
        for axis in [None, 0, 1, -1, -2]:
            kw = {}
            if axis is not None:
                kw = dict(axis=axis)
            for n in range(2):
                assert np.allclose(fft.fft(x, **kw), np.fft.fft(x, **kw))
                assert np.allclose(fft.ifft(x, **kw), np.fft.ifft(x, **kw))

    def test_fftn(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=False)
        for axes in [None, [0], [1], [-1], [-2], [1, 0]]:
            kw = {}
            if axes is not None:
                kw = dict(axes=axes)
            for n in range(2):
                assert np.allclose(fft.fftn(x, **kw), np.fft.fftn(x, **kw))
                assert np.allclose(fft.ifftn(x, **kw), np.fft.ifftn(x, **kw))


@pytest.fixture
def no_pyfftw(monkeypatch):
    """Fixture to test what happens if there is no pyfftw."""
    import builtins

    import_orig = builtins.__import__

    def mocked_import(name, *v, **kw):
        if name == "pyfftw":
            raise ImportError()
        return import_orig(name, *v, **kw)

    monkeypatch.setattr(builtins, "__import__", mocked_import)

    for mod in list(sys.modules):
        if mod.startswith("pyfftw") or mod.startswith("mmfutils"):
            monkeypatch.delitem(sys.modules, mod, raising=False)

    with pytest.warns(
        Warning, match="Could not import pyfftw... falling back to numpy"
    ):
        import mmfutils.performance.fft


class Test_FFT_no_pyfftw(Test_FFT):
    """Regression test to ensure safe fallbacks if pyfftw is missing."""

    @pytest.mark.usefixtures("no_pyfftw")
    def test_get_fft(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=True)
        for axis in [None, 0, 1, -1, -2]:
            kw = {}
            if axis is not None:
                kw = dict(axis=axis)
            assert np.allclose(fft.get_fft(x, **kw)(x), np.fft.fft(x, **kw))
            assert np.allclose(fft.get_ifft(x, **kw)(x), np.fft.ifft(x, **kw))

    @pytest.mark.usefixtures("no_pyfftw")
    def test_get_fftn(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=True)
        for axes in [None, [0], [1], [-1], [-2], [1, 0]]:
            kw = {}
            if axes is not None:
                kw = dict(axes=axes)
            assert np.allclose(fft.get_fftn(x, **kw)(x), np.fft.fftn(x, **kw))
            assert np.allclose(fft.get_ifftn(x, **kw)(x), np.fft.ifftn(x, **kw))

    @pytest.mark.usefixtures("no_pyfftw")
    def test_fft(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=False)
        for axis in [None, 0, 1, -1, -2]:
            kw = {}
            if axis is not None:
                kw = dict(axis=axis)
            for n in range(2):
                assert np.allclose(fft.fft(x, **kw), np.fft.fft(x, **kw))
                assert np.allclose(fft.ifft(x, **kw), np.fft.ifft(x, **kw))

    @pytest.mark.usefixtures("no_pyfftw")
    def test_fftn(self, fft):
        shape = (256, 256)
        x = self.rand(shape, writeable=False)
        for axes in [None, [0], [1], [-1], [-2], [1, 0]]:
            kw = {}
            if axes is not None:
                kw = dict(axes=axes)
            for n in range(2):
                assert np.allclose(fft.fftn(x, **kw), np.fft.fftn(x, **kw))
                assert np.allclose(fft.ifftn(x, **kw), np.fft.ifftn(x, **kw))
