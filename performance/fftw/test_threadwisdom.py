"""Test if wisdom can deduce the best number of threads.

Usage:
  python test_threadwisdom.py [options]

Options:
  -s --single
  -d --double
  -t --threads=<t>   Maximum number of threads.
  --shape=<s>        Shape of array [default: (16,)]
  --strict           Only plan for max threads.  (Fails with wisdom_only)
"""

import os
import sys

from docopt import docopt

from testfftw import run_test


def run(dtype="complex128", seed=2, max_threads=8, Nxyz=(16,), strict=False):
    kw = dict(
        Nxyz=Nxyz,
        dtype=dtype,
        seed=seed,
        planner_effort="FFTW_PATIENT",
    )

    run_test(threads=max_threads, **kw)
    print("The following should all be slower or comparable")
    for threads in range(1, max_threads):
        print(f"{threads=}")
        if strict:
            # This typically fails
            run_test(threads=threads, wisdom_only=True, **kw)
        else:
            run_test(threads=threads, **kw)

    print("Now we can run all with wisdom only.")
    for threads in range(1, max_threads):
        print(f"{threads=}")
        run_test(threads=threads, wisdom_only=True, check=False, **kw)


if __name__ == "__main__":
    args = docopt(__doc__, sys.argv)

    dtypes = []
    if args["--single"]:
        dtypes.extend(["float32", "complex64"])
    if args["--double"]:
        dtypes.extend(["float64", "complex128"])
    if not dtypes:
        dtypes = ["complex128"]

    Nxyz = eval(args["--shape"])
    strict = args["--strict"]

    max_threads = args["--threads"]
    if not max_threads:
        max_threads = os.cpu_count()
    max_threads = int(max_threads)

    for dtype in dtypes:
        run(dtype=dtype, max_threads=max_threads, Nxyz=Nxyz, strict=strict)
