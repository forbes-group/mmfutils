import pytest

from mmfutils.debugging import debug


class TestCoverage(object):
    """Some coverage tests."""

    def test_coverage_1(self):
        @debug()
        def f():
            x = 1
            return x

        f()
        assert f.locals["x"] == 1

    def test_coverage_2(self):
        @debug
        def f():
            x = 1
            return x

        f()
        assert f.env["x"] == 1

    def test_coverage_3(self):
        def f():
            x = 1
            return x

        env = {}
        debug(f, env)()
        assert env["x"] == 1

    def test_coverage_exception(self):
        def f():
            x = 1
            return x

        env = {}
        with pytest.raises(ValueError):
            debug(f, env, 3)()

    def test_generator(self):
        """Test generator expressions: see issue #41."""
        env = {}

        @debug(env)
        def gen(x):
            y = x**2
            yield y

        list(gen(2))
        assert env["x"] == 2
        assert env["y"] == 4
