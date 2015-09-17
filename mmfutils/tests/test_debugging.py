import nose.tools as nt

from mmfutils.debugging import debug


class TestCoverage(object):
    """Some coverage tests."""
    def test_coverage_1(self):
        @debug()
        def f():
            x = 1
            return x

        f()
        nt.eq_(f.locals['x'], 1)

    def test_coverage_2(self):
        @debug
        def f():
            x = 1
            return x

        f()
        nt.eq_(f.env['x'], 1)

    def test_coverage_3(self):
        def f():
            x = 1
            return x

        env = {}
        debug(f, env)()
        nt.eq_(env['x'], 1)

    @nt.raises(ValueError)
    def test_coverage_exception(self):
        def f():
            x = 1
            return x

        env = {}
        debug(f, env, 3)()
        nt.eq_(env['x'], 1)
