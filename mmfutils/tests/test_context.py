import os
import signal
import time

import numpy as np

import pytest

from mmfutils.contexts import NoInterrupt


class TestNoInterrupt(object):
    def test_typical_use(self):
        """Typical usage"""
        with NoInterrupt() as interrupted:
            done = False
            n = 0
            while not done and not interrupted:
                n += 1
                if n == 10:
                    done = True

        assert n == 10
        
    def test_restoration_of_handlers(self):
        original_hs = {_sig: signal.getsignal(_sig)
                       for _sig in NoInterrupt._signals}
        with NoInterrupt():
            with NoInterrupt():
                for _sig in original_hs:
                    assert original_hs[_sig] is not signal.getsignal(_sig)
            for _sig in original_hs:
                assert original_hs[_sig] is not signal.getsignal(_sig)
        for _sig in original_hs:
            assert original_hs[_sig] is signal.getsignal(_sig)

    def test_signal(self):
        with pytest.raises(KeyboardInterrupt):
            with NoInterrupt(ignore=False) as interrupted:
                m = -1
                for n in range(10):
                    if n == 5:
                        os.kill(os.getpid(), signal.SIGINT)
                    if interrupted:
                        m = n
        assert n == 9
        assert m >= 5

        # Make sure the signals can still be raised.
        with pytest.raises(KeyboardInterrupt):
            os.kill(os.getpid(), signal.SIGINT)
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

    def test_set_signal(self):
        signals = set(NoInterrupt._signals)
        try:
            NoInterrupt.catch_signals((signal.SIGHUP,))
            with pytest.raises(KeyboardInterrupt):
                with NoInterrupt(ignore=False) as interrupted:
                    while not interrupted:
                        os.kill(os.getpid(), signal.SIGHUP)
        finally:
            # Reset signals
            NoInterrupt.catch_signals(signals)

    def simulate_interrupt(self, force=False):
        """Simulates an interrupt or forced interupt."""
        # Simulate user interrupt
        os.kill(os.getpid(), signal.SIGINT)
        if force:
            # Simulated a forced interrupt with multiple signals
            os.kill(os.getpid(), signal.SIGINT)
            os.kill(os.getpid(), signal.SIGINT)

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
                time.sleep(0.1)
            self.n[1] += 1
            done = self.n[0] >= 10

    def test_issue_14(self):
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

    def test_nested_handlers(self):
        completed = []
        for a in range(3):
            with NoInterrupt(ignore=True) as i2:
                for b in range(3):
                    if i2:
                        break
                    if a == 1 and b == 1:
                        self.simulate_interrupt()
                        time.sleep(0.1)
                    completed.append((a, b))
                    
        assert completed == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1),
                             (2, 0), (2, 1), (2, 2)]

        completed = []
        with NoInterrupt(ignore=True) as i1:
            for a in range(3):
                if i1:
                    break
                with NoInterrupt(ignore=True) as i2:
                    for b in range(3):
                        if i2:
                            break
                        if a ==1 and b == 1:
                            self.simulate_interrupt()
                            time.sleep(0.1)
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
                        if a ==1 and b == 1:
                            self.simulate_interrupt()
                            time.sleep(0.1)
                        completed.append((a, b))

                with NoInterrupt(ignore=True) as i3:
                    for b in [3]:
                        if i3:
                            break
                        completed.append((a, b))

        assert completed == [(0, 0), (0, 1), (0, 2), (0, 3),
                             (1, 0), (1, 1)]

        # Perhaps this should be the result.
        # assert completed == [(0, 0), (0, 1), (0, 2), (0, 3),
        #                      (1, 0), (1, 1), (1, 3)]
