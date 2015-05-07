import nose.tools as nt

from mmfutils.performance import threads

import numpy as np
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
            nt.ok_(numexpr.set_num_threads in threads.SET_THREAD_HOOKS)
            nt.ok_(numexpr.set_vml_num_threads in threads.SET_THREAD_HOOKS)

    def test_hooks_fft(self):
        if fft:
            nt.ok_(fft.set_num_threads in threads.SET_THREAD_HOOKS)

    def test_hook_mkl(self):
        if mkl:
            nt.ok_(mkl.set_num_threads in threads.SET_THREAD_HOOKS)

    def test_set_threads_mkl(self):
        if mkl:
            for nthreads in [1, 2]:
                threads.set_num_threads(nthreads)
                nt.eq_(mkl.get_max_threads(), nthreads)

    def test_set_threads_numexpr(self):
        for nthreads in [1, 2]:
            threads.set_num_threads(nthreads)
            nt.eq_(numexpr.set_num_threads(nthreads), nthreads)

    def test_set_threads_fft(self):
        for nthreads in [1, 2]:
            threads.set_num_threads(nthreads)
            nt.eq_(fft._THREADS, nthreads)


class TestThreadsBenchmarks(object):
    bench = True

    def setUp(self):
        np.random.seed(1)

    def test_numexpr(self):
        x = np.random.random((1000, 1000))
        ts = []
        for nthreads in [1, 2]:
            threads.set_num_threads(nthreads)
            t = timeit.repeat(lambda: numexpr.evaluate('sin(x)', {'x': x}),
                              number=10)
            ts.append(min(t))
        nt.assert_less(ts[1], ts[0]/1.3)

    def test_fft(self):
        x = np.random.random((1000, 1000))
        ts = []
        for nthreads in [1, 2]:
            threads.set_num_threads(nthreads)
            t = timeit.repeat(lambda: fft.fftn(x),
                              number=10)
            ts.append(min(t))
        nt.assert_less(ts[1], ts[0]/1.3)
