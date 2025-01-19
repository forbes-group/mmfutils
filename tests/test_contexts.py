import itertools
import os
import signal
import time

from uncertainties import ufloat

import numpy as np

import pytest

from mmfutils import contexts


@pytest.fixture
def NoInterrupt():
    yield contexts.NoInterrupt
    # Restore original handlers
    contexts.NoInterrupt.unregister()


@pytest.fixture(params=[False, True])
def unregister(request):
    yield request.param


class TestNoInterrupt(object):
    @staticmethod
    def simulate_interrupt(force=False, signum=signal.SIGINT):
        """Simulates an interrupt or forced interupt."""
        # Simulate user interrupt
        os.kill(os.getpid(), signum)
        if force:
            # Simulated a forced interrupt with multiple signals
            os.kill(os.getpid(), signum)
            os.kill(os.getpid(), signum)
        contexts.sleep(0.1)

    def test_typical_use(self, NoInterrupt):
        """Typical usage"""
        with NoInterrupt() as interrupted:
            done = False
            n = 0
            while not done and not interrupted:
                n += 1
                if n == 10:
                    done = True

        assert n == 10

    def test_restoration_of_handlers(self, NoInterrupt):
        original_hs = {_sig: signal.getsignal(_sig) for _sig in NoInterrupt._signals}

        with NoInterrupt():
            with NoInterrupt():
                for _sig in original_hs:
                    assert original_hs[_sig] is not signal.getsignal(_sig)
            for _sig in original_hs:
                assert original_hs[_sig] is not signal.getsignal(_sig)

        for _sig in original_hs:
            assert original_hs[_sig] is not signal.getsignal(_sig)

        NoInterrupt.unregister()

        for _sig in original_hs:
            assert original_hs[_sig] is signal.getsignal(_sig)

    def test_signal(self, NoInterrupt):
        with pytest.raises(KeyboardInterrupt):
            with NoInterrupt(ignore=False) as interrupted:
                m = -1
                for n in range(10):
                    if n == 5:
                        self.simulate_interrupt()
                    if interrupted:
                        m = n
        assert n == 9
        assert m >= 5

        # Make sure the signals can still be raised.
        with pytest.raises(KeyboardInterrupt):
            self.simulate_interrupt()
            contexts.sleep(1)

        # And that the interrupts are reset
        try:
            with NoInterrupt() as interrupted:
                n = 0
                while n < 10 and not interrupted:
                    n += 1
        except KeyboardInterrupt:
            raise Exception("KeyboardInterrupt raised when it should not be!")

        assert n == 10

    def test_set_signal(self, NoInterrupt):
        signals = set(NoInterrupt._signals)
        try:
            NoInterrupt.set_signals((signal.SIGHUP,))
            with pytest.raises(KeyboardInterrupt):
                with NoInterrupt(ignore=False) as interrupted:
                    while not interrupted:
                        self.simulate_interrupt()
        finally:
            # Reset signals
            NoInterrupt.set_signals(signals)

    def interrupted_loop(self, interrupted=False, force=False):
        """Simulates an interrupt or forced interupt in the middle of a
        loop.  Two counters are incremented from 0 in `self.n`.  The interrupt
        is signaled self.n[0] == 5, and the loop naturally exist when self.n[0]
        >= 10.  The first counter is incremented before the interrupt is
        simulated, while the second counter is incremented after."""
        self.n = [0, 0]
        done = False
        while not done and not interrupted:
            self.n[0] += 1
            if self.n[0] == 5:
                self.simulate_interrupt(force=force)
            self.n[1] += 1
            done = self.n[0] >= 10

    def test_issue_14(self, NoInterrupt):
        """Regression test for issue 14 and bug discovered there."""
        with pytest.raises(KeyboardInterrupt):
            with NoInterrupt() as interrupted:
                self.interrupted_loop(interrupted=interrupted, force=True)
        assert np.allclose(self.n, [5, 4])

        try:
            # We need to wrap this in a try block otherwise py.test will think
            # that the user aborted the test.

            # All interrupts should be cleared and this should run to
            # completion.
            with NoInterrupt() as interrupted:
                self.interrupted_loop(force=False)
        except KeyboardInterrupt:
            pass

        # This used to fail since the interrupts were not cleared.
        assert np.allclose(self.n, [10, 10])

    def test_nested_handlers(self, NoInterrupt):
        completed = []
        for a in range(3):
            with NoInterrupt(ignore=True) as i2:
                for b in range(3):
                    if i2:
                        break
                    if a == 1 and b == 1:
                        self.simulate_interrupt()
                    completed.append((a, b))

        assert completed == [
            (0, 0),
            (0, 1),
            (0, 2),
            (1, 0),
            (1, 1),
            (2, 0),
            (2, 1),
            (2, 2),
        ]

        completed = []
        with NoInterrupt(ignore=True) as i1:
            for a in range(3):
                if i1:
                    break
                with NoInterrupt(ignore=True) as i2:
                    for b in range(3):
                        if i2:
                            break
                        if a == 1 and b == 1:
                            self.simulate_interrupt()
                        completed.append((a, b))

        assert completed == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]

        completed = []
        with NoInterrupt(ignore=True) as i1:
            for a in range(3):
                if i1:
                    break
                with NoInterrupt(ignore=True) as i2:
                    for b in [0, 1, 2]:
                        if i2:
                            break
                        if a == 1 and b == 1:
                            self.simulate_interrupt()
                        completed.append((a, b))

                with NoInterrupt(ignore=True) as i3:
                    for b in [3]:
                        if i3:
                            break
                        completed.append((a, b))

        assert completed == [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3)]

    def test_unused_context(self, NoInterrupt):
        """Test issue 28: bare instance hides signals.

        Signals should only be caught in contexts.
        """
        NoInterrupt()

        # Signals should no longer be caught
        with pytest.raises(KeyboardInterrupt):
            self.simulate_interrupt()
            contexts.sleep(1)

    def test_reused_context(self, NoInterrupt):
        """Test that NoInterrupt() instances can be reused."""
        ni = NoInterrupt()
        with pytest.raises(KeyboardInterrupt):
            with ni as interrupted:
                self.interrupted_loop(interrupted=interrupted, force=True)
        assert np.allclose(self.n, [5, 4])

        with ni as interrupted:
            self.interrupted_loop(interrupted=interrupted, force=False)
        assert np.allclose(self.n, [5, 5])

    def test_map(self, NoInterrupt):
        def f(x, values_computed):
            if x == 2:
                self.simulate_interrupt()
            values_computed.append(x)
            return x**2

        values_computed = []
        res = NoInterrupt().map(f, [1, 2, 3], values_computed=values_computed)
        assert res == [1, 4]

        with pytest.raises(KeyboardInterrupt):
            # Signals still work.
            self.simulate_interrupt()

        # Here the interrupt should not be ignored, but f() should be
        # allowed to complete.
        values_computed = []
        res = []
        with pytest.raises(KeyboardInterrupt):
            res = NoInterrupt(ignore=False).map(
                f, [1, 2, 3], values_computed=values_computed
            )
        assert res == []
        assert values_computed == [1, 2]

        # As opposed to a normal map:
        values_computed = []
        res = []
        with pytest.raises(KeyboardInterrupt):
            res = list(map(lambda x: f(x, values_computed), [1, 2, 3]))
        assert res == []
        assert values_computed == [1]

    def test_no_context(self, NoInterrupt):
        """Test catching signals without a context."""
        NoInterrupt._signal_count = {}  # Don't do this... just for testing
        NoInterrupt.register()
        interrupted = NoInterrupt()
        assert interrupted._signal_count == {}
        with pytest.raises(KeyboardInterrupt):
            self.simulate_interrupt(signum=signal.SIGINT)
            # Won't get executed because we have not suspended signals
            self.simulate_interrupt(signum=signal.SIGINT)
        assert interrupted._signal_count == {signal.SIGINT: 1}

        NoInterrupt.reset()  # Prevent triggering a forced interrupt

        interrupted1 = NoInterrupt()
        assert interrupted  # Old interrupted still registers the interrupt
        assert not interrupted1  # New interrupted does not.

        # reset() does not reset counts.
        assert interrupted._signal_count == {signal.SIGINT: 1}
        assert interrupted1._signal_count == {signal.SIGINT: 1}

        NoInterrupt.suspend()
        self.simulate_interrupt(signum=signal.SIGTERM)
        self.simulate_interrupt(signum=signal.SIGTERM)
        assert interrupted1._signal_count == {signal.SIGINT: 1, signal.SIGTERM: 2}
        NoInterrupt.resume()
        with pytest.raises(KeyboardInterrupt):
            self.simulate_interrupt(signum=signal.SIGINT)

    def test_unregister_context(self, NoInterrupt):
        NoInterrupt.unregister()
        with NoInterrupt(ignore=True) as interrupted:
            self.simulate_interrupt(signum=signal.SIGINT)

    def test_nested_exceptions(self, NoInterrupt):
        with pytest.raises(ValueError):
            with NoInterrupt():
                with NoInterrupt():
                    raise ValueError("My Value Error")

    def test_issue33(self, NoInterrupt):
        """Regression test for issue #33 about ipython and nested contexts."""
        import IPython

        # IPython.start_ipython()
        with pytest.raises(ValueError):
            with NoInterrupt():
                with NoInterrupt():
                    raise ValueError("My Value Error")


@pytest.fixture(params=[None, 60])
def max_fps(request):
    yield request.param


class TestFPS:
    def test_timeout(self):
        timeout = 0.1
        sleep_time = 0.01
        with contexts.FPS(frames=100, timeout=timeout) as fps:
            tic = time.time()
            for frame in fps:
                contexts.sleep(sleep_time)
            _fps = fps.fps
        assert fps.fps == _fps
        t = time.time() - tic
        assert t < 1.1 * (timeout + sleep_time)
        assert str(fps) == f"{fps.fps:.2f}"
        assert np.allclose(float(fps), fps.fps)

    def test_frames(self, max_fps):
        sleep_time = 0.01
        frames = 13
        with contexts.FPS(frames=frames, max_fps=max_fps) as fps:
            contexts.sleep(sleep_time)
            for frame in fps:
                contexts.sleep(sleep_time)
        assert frame == frames - 1
        _fps = fps.fps
        contexts.sleep(sleep_time)  # should not change fps
        assert _fps == fps.fps
        self._check_fps(fps, sleep_time=sleep_time)

    @pytest.mark.flaky(reruns=5)
    def test_ts(self, max_fps):
        sleep_time = 0.01
        ts = np.linspace(0, 1, 13)
        with contexts.FPS(frames=ts, max_fps=max_fps) as fps:
            for n, t in enumerate(fps):
                assert t == ts[n]
                contexts.sleep(sleep_time)

        assert t == ts[-1]
        self._check_fps(fps, sleep_time=sleep_time)

    def test_infinite(self, max_fps):
        sleep_time = 0.01
        timeout = 0.1
        tic = time.time()
        with contexts.FPS(
            frames=itertools.count(start=0, step=1),
            timeout=timeout,
            unregister=unregister,
            max_fps=max_fps,
        ) as fps:
            for frame in fps:
                contexts.sleep(sleep_time)

        t = time.time() - tic
        assert t < 1.1 * (timeout + sleep_time)
        self._check_fps(fps, sleep_time)
        # leftover = 1.0 / fps.fps - sleep_time
        # assert np.allclose(fps.fps, leftover)

    @pytest.mark.flaky(reruns=5)
    def test_default_timeout(self):
        _default_timeout = contexts.FPS._default_timeout
        try:
            dT = 0.03
            contexts.FPS._default_timeout = 0.1
            N = 10

            def gen():
                """Indeterminate generator... no len."""
                for n in range(N):
                    time.sleep(dT)
                    yield n

            tic = time.time()
            for frame in contexts.FPS(gen()):
                # Loop would normally take N*dT, but default timeout should kick in
                # since we can get the length of the loop.
                pass
            T = time.time() - tic

            # Should take less than the full time but close to default.
            assert frame < N - 1
            assert T < (N - 2) * dT
            assert np.allclose(T, contexts.FPS._default_timeout, atol=2 * dT)

            tic = time.time()
            for frame in contexts.FPS(range(N)):
                # Now we can count, so this should take the full
                time.sleep(dT)
            T = time.time() - tic

            # Should take full time, more than timeout.
            assert frame == N - 1
            assert T > contexts.FPS._default_timeout + dT
            assert np.allclose(T, N * dT, atol=2 * dT)
        finally:
            contexts.FPS._default_timeout = _default_timeout

    def _check_fps(self, fps, sleep_time, rtol=0.05):
        if fps.max_fps:
            sleep_time = max(sleep_time, 1 / fps.max_fps)
        _fps = 1.0 / sleep_time
        dts = np.diff(fps.tics)
        dt = ufloat(dts.mean(), dts.std())
        assert np.allclose(1 / dt.n, fps.fps)
        assert np.allclose(fps.fps, _fps, rtol=rtol, atol=(1 / dt).s)

    def test_coverage(self, unregister):
        """Test some edge cases."""
        with contexts.FPS(frames=[], unregister=unregister) as fps:
            assert np.isnan(fps.fps)
            assert len(fps.tics) == 1

    def test_len(self):
        """Test that FPS() provides a length (issue 35).

        This makes it work nicely with tqdm.
        """
        assert len(contexts.FPS(10)) == 10
        with pytest.raises(TypeError) as e:
            len(contexts.FPS(itertools.count()))
        assert e.value.args[0] == "object of type 'FPS' has no len()"
