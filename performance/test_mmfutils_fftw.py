"""Test the performance of mmfutils.performance.fft.fftn.

Run this twice: the first time should take a while as FFTW_PATIENT is used to determine
the optimal performance.  The second time should be fast as the wisdom file is used::

  $ rm -f .fftw_wisdom
  $ time python test_mmfutils_fftw.py
  $ time python test_mmfutils_fftw.py

In both cases, the performance should be better than numpy.

Usage:
  python test_mmfutils_fftw.py [--Nxyz=(256,)] [--dtype=float]

Options:
  --Nxyz=<Nxyz>   Size of array [default: (1024,)]
  --dtype=<type>  Data type [default: float64]
"""

import os
import sys

import numpy as np

from mmfutils.performance import fft

from docopt import docopt
from utils import allclose, tester


def run(Nxyz, dtype=np.float64, seed=2):
    rng = np.random.default_rng(seed=seed)
    with fft.fftw_wisdom(threads=os.cpu_count()):
        X = rng.normal(size=Nxyz).astype(dtype)

        with tester(np_fftn=np.fft.fftn, X=X) as (get_ts, X_t):
            ts_np = get_ts(np.fft.fftn, label="np")
            assert allclose(fft.fftn(X), X_t)
            ts_fftw = get_ts(fft.fftn, label="fft.fftn")
        speedup = min(ts_fftw) / min(ts_np) * 100

        print(f"{speedup = :.2f}%")


if __name__ == "__main__":
    args = docopt(__doc__, sys.argv)
    Nxyz = eval(args["--Nxyz"])
    dtype = np.dtype(args["--dtype"])
    run(Nxyz=Nxyz, dtype=dtype)
