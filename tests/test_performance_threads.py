from mmfutils.performance import threads

import numpy as np
import pytest
import timeit

try:
    import numexpr
except ImportError:
    numexpr = None

try:
    import mkl
except ImportError:
    mkl = None


try:
    from mmfutils.performance import fft
except ImportError:
    fft = None


class TestThreads(object):
    def test_hooks_numexpr(self):
        if numexpr:
            assert numexpr.set_num_threads in threads.SET_THREAD_HOOKS
            assert numexpr.set_vml_num_threads in threads.SET_THREAD_HOOKS

    def test_hooks_fft(self):
        if fft:
            assert fft.set_num_threads in threads.SET_THREAD_HOOKS

    def test_hook_mkl(self):
        if mkl:
            assert mkl.set_num_threads in threads.SET_THREAD_HOOKS

    def test_set_threads_mkl(self):
        if mkl:
            for nthreads in [1, 2]:
                threads.set_num_threads(nthreads)
                assert mkl.get_max_threads() == nthreads

    def test_set_threads_numexpr(self):
        for nthreads in [1, 2]:
            threads.set_num_threads(nthreads)
            assert numexpr.set_num_threads(nthreads) == nthreads

    def test_set_threads_fft(self):
        for nthreads in [1, 2]:
            threads.set_num_threads(nthreads)
            assert fft._THREADS == nthreads


@pytest.mark.bench
class TestThreadsBenchmarks(object):
    bench = True

    @classmethod
    def setup_class(cls):
        np.random.seed(1)

    def test_numexpr(self):
        x = np.random.random((1000, 1000))
        ts = []
        for nthreads in [1, 2]:
            threads.set_num_threads(nthreads)
            t = timeit.repeat(lambda: numexpr.evaluate("sin(x)", {"x": x}), number=10)
            ts.append(min(t))
        assert ts[1] < ts[0] / 1.3

    def test_fft(self):
        x = np.random.random((1000, 1000))
        ts = []
        for nthreads in [1, 2]:
            threads.set_num_threads(nthreads)
            t = timeit.repeat(lambda: fft.fftn(x), number=10)
            ts.append(min(t))
        assert ts[1] < ts[0] / 1.3
