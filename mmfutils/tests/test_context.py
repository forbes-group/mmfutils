import os
import signal
import time

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
            with NoInterrupt() as interrupted:
                m = -1
                for n in xrange(10):
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
                with NoInterrupt() as interrupted:
                    while not interrupted:
                        os.kill(os.getpid(), signal.SIGHUP)
        finally:
            # Reset signals
            NoInterrupt.catch_signals(signals)
