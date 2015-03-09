"""A few extra tests to run all the code"""
import os.path
import mmfutils.monkeypatches
import flake8.main
import nose.commands
import nose.tools as nt

PROJECT_DIR = os.path.join(os.path.dirname(mmfutils.__file__), '..')


class TestCoverage(object):
    @staticmethod
    def run_noerr(self):
        raise SystemExit(0)

    @staticmethod
    def run_err(self):
        raise SystemExit(1)

    def setUp(self):
        reload(mmfutils.monkeypatches)

        class Flake8Command(flake8.main.Flake8Command):
            def __init__(self):
                pass

        class nosetests(nose.commands.nosetests):
            def __init__(self):
                pass

        self.nose_self = nosetests()
        self.flake8_self = Flake8Command()

    def test_cover_monkeypatchs(self):
        # Both these patched commands store the old run method in _run so we
        # can sub it out to ensure coverage testing.
        self.nose_self.run(_run=self.run_noerr)
        self.flake8_self.run(_run=self.run_noerr)

    @nt.raises(SystemExit)
    def test_nose_patch_err(self):
        self.nose_self.run(_run=self.run_err)

    @nt.raises(SystemExit)
    def test_flake8_patch_err(self):
        self.flake8_self.run(_run=self.run_err)
