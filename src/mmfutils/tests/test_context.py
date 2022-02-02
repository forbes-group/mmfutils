import os
import signal
import time

import numpy as np

import pytest

from mmfutils import contexts


@pytest.yield_fixture
def NoInterrupt():
    yield contexts.NoInterrupt
    # Restore original handlers
    contexts.NoInterrupt.unregister()


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
        time.sleep(0.1)

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
            time.sleep(1)

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
            time.sleep(1)

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
            return x ** 2

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
