"""Test FFTW Performance.

Usage:
  python testfftw.py
  python testfftw.py [single] [double] [--wisdom-only] [--threads 8] [--effort FFTW_PATIENT]


Options:
  -t --threads <threads>      Number of threads (default 8)
  --effort <planner_erffort>  FFTW_MEASURE (default), FFTW_PATIENT etc.
  -w --wisdom-only            Only use wisdom (fail if it does not exist.)
"""

import sys

import time, timeit, numpy as np, pyfftw.builders

from docopt import docopt
from utils import allclose, get_fftn, get_fftw_wisdom

rng = np.random.default_rng(seed=2)

_WISDOM_FILE = ".fftw_wisdom"


def run_test(
    Nxyz,
    dtype="complex128",
    threads=8,
    seed=2,
    planner_effort="FFTW_MEASURE",
    wisdom_only=False,
    check=True,
):
    rng = np.random.default_rng(seed=seed)
    dtype = np.dtype(dtype)

    print(f"{Nxyz=} ({dtype})")
    psi = rng.normal(size=Nxyz).astype(dtype)
    if np.iscomplexobj(psi):
        psi += (rng.normal(size=Nxyz) * 1j).astype(dtype)

    tic = time.time()
    psi_t = np.fft.fftn(psi)
    t = time.time() - tic
    T, repeat = 3, 5  # Desired time for tests in s and number of repeats
    number = max(1, int(T / t / repeat))

    def test(fftn, label=""):
        ts = timeit.repeat(
            "fftn(psi)",
            globals=dict(psi=psi, fftn=fftn),
            repeat=repeat,
            number=number,
        )
        print(f"{label:6}: {min(ts):.4f}s (median {np.median(ts):.4f}s) / {number}")
        return ts

    if check:
        test(np.fft.fft, "np")

    flags = []
    if wisdom_only:
        flags.append("FFTW_WISDOM_ONLY")

    if True:
        fftn = get_fftn(
            psi, threads=threads, flags=flags, planner_effort=planner_effort
        )
    else:
        fftn = pyfftw.builders.fftn(
            psi.copy(),
            # threads=os.cpu_count(),
            threads=threads,
            flags=flags,
            planner_effort=planner_effort,
        )

    if check:
        assert allclose(fftn(psi), psi_t)

    ts = test(fftn, "pyfftw")
    print()
    return ts


def run(
    dtype="complex128",
    seed=2,
    threads=8,
    effort="FFTW_MEASURE",
    wisdom_file=_WISDOM_FILE,
):
    with get_fftw_wisdom(wisdom_file=wisdom_file):
        for Nxyz in [
            (2**12,),
            (2, 64),
            (32, 64),
            (64, 64, 64),
            (1200,) * 2,
            (256,) * 3,
        ]:
            run_test(
                Nxyz=Nxyz,
                dtype=dtype,
                seed=seed,
                threads=threads,
                planner_effort=effort,
            )


if __name__ == "__main__":
    args = docopt(__doc__, sys.argv)

    dtypes = []
    if args["single"]:
        dtypes.extend(["float32", "complex64"])
    if args["double"]:
        dtypes.extend(["float64", "complex128"])
    if not dtypes:
        dtypes = ["complex128"]

    threads = args["--threads"]
    if not threads:
        threads = 8
    threads = int(threads)

    effort = args["--effort"]
    if not effort:
        effort = "FFTW_MEASURE"
    for dtype in dtypes:
        run(dtype=dtype, threads=threads, effort=effort)
