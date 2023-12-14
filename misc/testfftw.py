import os, time, timeit, numpy as np, pyfftw.builders

rng = np.random.default_rng(seed=2)

for Nxyz in [(2, 64), (1200,) * 2, (256,) * 3][-1:]:
    print(f"{Nxyz=}")
    psi = rng.normal(size=Nxyz) + rng.normal(size=Nxyz) * 1j

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

    test(np.fft.fft, "np")

    fftn = pyfftw.builders.fftn(
        psi.copy(),
        # threads=os.cpu_count(),
        # planner_effort="FFTW_PATIENT",
        threads=8,
        planner_effort="FFTW_MEASURE",
    )

    assert np.allclose(fftn(psi), psi_t)

    test(fftn, "pyfftw")
    print()
