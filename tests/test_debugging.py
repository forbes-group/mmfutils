import pytest

from mmfutils.debugging import debug, persistent_locals


class TestDebugging:
    def test_persistent_locals_generator(self):
        @persistent_locals
        def f(x):
            for p in [1, 2, 3]:
                y = x**p
                yield y

        gen = f(2)
        assert next(gen) == 2
        assert f.locals == dict(x=2, y=2, p=1)
        assert next(gen) == 4
        assert f.locals == dict(x=2, y=4, p=2)
        assert next(gen) == 8
        assert f.locals == dict(x=2, y=8, p=3)
        f.clear_locals()
        assert f.locals == {}

    def test_debug_generator(self):
        env = {}

        @debug(env)
        def f(x):
            for p in [1, 2, 3]:
                y = x**p
                yield y

        gen = f(2)
        assert next(gen) == 2
        assert env == dict(x=2, y=2, p=1)
        assert next(gen) == 4
        assert env == dict(x=2, y=4, p=2)
        assert next(gen) == 8
        assert env == dict(x=2, y=8, p=3)

    def test_debug_return(self):
        @debug
        def f(x):
            return x**2

        assert f(2) == 4

    def test_debug(self):
        @debug
        def f(x):
            y = x**2
            assert False

        try:
            f(2)
        except AssertionError:
            pass

        assert (f.locals | dict(x=2, y=4)) == f.locals

    def test_debug_env(self):
        env = {}

        @debug(env)
        def f(x):
            y = x**2
            assert False
            return y

        try:
            f(2)
        except AssertionError:
            pass

        assert (env | dict(x=2, y=4)) == env


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
