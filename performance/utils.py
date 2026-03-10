from contextlib import contextmanager
import os
import pickle
import time
import timeit

import numpy as np
import pyfftw.builders

_WISDOM_FILE = ".fftw_wisdom"


def allclose(a, b, atol=None, rtol=None, tol_eps_N=8, min_tol=0.01):
    """Fix some issues with np.allclose.  See:
    https://github.com/numpy/numpy/issues/10161
    """
    a, b = map(np.asarray, (a, b))
    eps = max([np.finfo(x.dtype).eps for x in (a, b)])

    # Larger arrays will have more roundoff error.  Correct for this
    tol_eps = tol_eps_N * np.sqrt(np.prod(a.shape))

    if rtol is None:
        rtol = min(tol_eps * eps, min_tol)
    if atol is None:
        atol = min(tol_eps * eps, min_tol)

    res = np.all(abs(a - b) <= np.maximum(rtol * np.maximum(abs(a), abs(b)), atol))
    if not res:
        print(
            f"max abs err={abs(a - b).max()}, max rel err={abs(a / b - 1).max()} "
            + f"({atol=}, {rtol=})"
        )
    return res


def get_fftn(
    x,
    axes=None,
    threads=1,
    flags=None,
    planner_effort="FFTW_MEASURE",
    planning_timelimit=None,
    overwrite_input=False,
):
    """Replacement for pyfftw.builders.fftn allowing `FFTW_WISDOM_ONLY`."""
    a = pyfftw.empty_aligned(x.shape, dtype=x.dtype)
    b = pyfftw.empty_aligned(x.shape, dtype=(x[:1] + 0j).dtype)
    if axes is None:
        axes = list(range(-len(x.shape), 0))

    if flags is None:
        flags = []

    flags = list(flags)

    flags.append(planner_effort)

    if overwrite_input:
        flags.append("FFTW_DESTROY_INPUT")

    return pyfftw.FFTW(
        a,
        b,
        direction="FFTW_FORWARD",
        flags=flags,
        axes=axes,
        threads=threads,
        planning_timelimit=planning_timelimit,
    )


@contextmanager
def fftw_wisdom(wisdom_file=_WISDOM_FILE):
    """Context in which to load and save wisdom."""
    wisdom = None
    if os.path.exists(wisdom_file):
        print("Loading wisdom")
        with open(wisdom_file, "rb") as f:
            try:
                wisdom = pickle.load(f)
                pyfftw.import_wisdom(wisdom)
            except pickle.UnpicklingError:
                print("Invalid wisdom pickle... ignoring")
                wisdom = None
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


@contextmanager
def tester(np_fftn, X, T=3, repeat=5):
    tic = time.time()
    X_t = np_fftn(X)
    t = time.time() - tic
    number = max(1, int(T / t / repeat))

    def get_ts(fftn, label="", quiet=False):
        ts = timeit.repeat(
            "fftn(X)",
            globals=dict(X=X, fftn=fftn),
            repeat=repeat,
            number=number,
        )
        if not quiet:
            print(f"{label:6}: {min(ts):.4f}s (median {np.median(ts):.4f}s) / {number}")
        return ts

    yield get_ts, X_t
