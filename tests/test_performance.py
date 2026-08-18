"""Tests of the top-level performance utils."""

import numpy as np
import pytest
import warnings
from mmfutils.performance import GPUPerformanceWarning, perf_warn_on_GPU


@pytest.mark.parametrize("gpu", [True, False], ids=["gpu", "cpu"])
@pytest.mark.parametrize(
    "initializing", [True, False], ids=["initializing", "not initializing"]
)
def test_perf_warn_on_GPU(gpu, initializing):
    cp = None  # Warning should be raised if xp is not np, so this should be fine

    class TestClass:
        if gpu:
            xp = cp

        else:
            xp = np

        @perf_warn_on_GPU
        def cpu_method(self, a=1):
            return a**2

    tc = TestClass()
    tc._initializing = initializing

    a = 10

    if gpu and not initializing:
        # Ensure we raise a warning
        with pytest.warns(GPUPerformanceWarning):
            out = tc.cpu_method(a=a)

    else:
        # Ensure we do not raise a warning
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                out = tc.cpu_method(a=a)

        except GPUPerformanceWarning:
            raise AssertionError("Decorated method warned when it shouldn't have")

    # Ensure the function output is correct
    assert out == a**2
