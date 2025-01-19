import numpy as np
from mmfutils.math import wigner


class TestWigner:
    def test_wigner(self):
        N = 128
        ts = np.linspace(-1, 1, N)
        xs = np.where(abs(ts) < 0.5, 1, 0)
        ws, P = wigner.wigner_ville(xs, dt=np.diff(ts).mean())
        t = ts[:, None]
        w = ws[None, :]
        f = w / 2 / np.pi
        P_ = np.where(
            abs(t) < 0.5,
            np.where(
                f == 0,
                2 * (1 - 2 * abs(t)),
                np.sin(2 * np.pi * f * (1 - 2 * abs(t))) / np.pi / f,
            ),
            0,
        )

        assert np.allclose(P / P.max(), P_ / P_.max(), atol=0.03)
