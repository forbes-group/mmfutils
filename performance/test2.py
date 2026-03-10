import pyfftw
import numpy as np

_WISDOM_FILE = "tst1_wisdom.dat"


def get_fft_object(x, flags, axis=-1):
    n_fft = x.shape[axis]
    shape = (n_fft // 2 + 1, x.shape[1]) if axis == 0 else (len(x), n_fft // 2 + 1)

    a = pyfftw.empty_aligned(x.shape, dtype=x.dtype)
    b = pyfftw.empty_aligned(shape, dtype=(x[0] + 0j).dtype)
    return pyfftw.FFTW(
        a, b, axes=(axis,), flags=flags, planning_timelimit=120, threads=8
    )


# x = np.random.randn(400, 200000).astype("float32")
x = np.random.randn(400, 200).astype("float64")


get_fft_object(x, ["FFTW_PATIENT"])()
wisdom = pyfftw.export_wisdom()
get_fft_object(x, ["FFTW_PATIENT", "FFTW_WISDOM_ONLY"])()
pyfftw.forget_wisdom()
try:
    get_fft_object(x, ["FFTW_PATIENT", "FFTW_WISDOM_ONLY"])()
except RuntimeError as e:
    assert str(e) == "No FFTW wisdom is known for this plan."
pyfftw.import_wisdom(wisdom)
get_fft_object(x, ["FFTW_PATIENT", "FFTW_WISDOM_ONLY"])()
