import numpy as np

from mmfutils.math import special


def test_step():
    """Test the step function."""
    t1 = 2.0
    for alpha in [1.0, 3.0, 7.0]:
        for t in [-0.1, 0.0]:
            assert special.step(t, t1, alpha) == 0
        for t in [t1 // 2]:
            assert special.step(t, t1, alpha) == 0.5
        for t in [t1, t1 + 1.0]:
            assert special.step(t, t1, alpha) == 1


def test_mstep():
    """Test the mstep function."""
    t1 = 2.0
    t = [-0.1, 0.0, t1 // 2, t1 + 1.0]

    for alpha in [1.0, 3.0, 7.0]:
        assert np.allclose(
            special.mstep(t, t1, alpha), np.vectorize(special.step)(t, t1, alpha)
        )
