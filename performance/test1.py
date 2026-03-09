from contextlib import contextmanager
import os
import pickle
import pyfftw
import numpy as np

_WISDOM_FILE = "tst1_wisdom.dat"


@contextmanager
def get_wisdom(wisdom_file=_WISDOM_FILE):
    """Context in which to load and save wisdom."""
    wisdom = None
    if os.path.exists(wisdom_file):
        print("Loading wisdom")
        with open(wisdom_file, "rb") as f:
            wisdom = pickle.load(f)
            pyfftw.import_wisdom(wisdom)
    try:
        yield wisdom
    finally:
        print("Saving wisdom")
        with open(wisdom_file, "wb") as f:
            wisdom = pyfftw.export_wisdom()
            pickle.dump(wisdom, f)

        with open(wisdom_file, "rb") as f1:
            wisdom1 = pickle.load(f1)

        assert wisdom == wisdom1


def get_fft_object(x, flags, axis=-1):
    n_fft = x.shape[axis]
    shape = (n_fft // 2 + 1, x.shape[1]) if axis == 0 else (len(x), n_fft // 2 + 1)

    a = pyfftw.empty_aligned(x.shape, dtype=x.dtype)
    b = pyfftw.empty_aligned(shape, dtype=(x[0] + 0j).dtype)
    return pyfftw.FFTW(
        a, b, axes=(axis,), flags=flags, planning_timelimit=None, threads=8
    )


# x = np.random.randn(400, 200000).astype("float32")
x = np.random.randn(400, 200).astype("float32")

with get_wisdom() as wisdom:
    print(wisdom)
    get_fft_object(x, ["FFTW_PATIENT"])()
    get_fft_object(x, ["FFTW_PATIENT", "FFTW_WISDOM_ONLY"])()
    print(pyfftw.export_wisdom())
