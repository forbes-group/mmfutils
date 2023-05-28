import pytest

import pyfftw
import mmfutils.performance.threads


@pytest.fixture(params=[1, 2])
def threads(request):
    threads = request.param
    if threads > 1 and not pyfftw._threading_type:
        pytest.skip(
            "Skipping threads>1: fftw not compiled with multithreaded support")
    mmfutils.performance.threads.set_num_threads(threads)
    yield threads
