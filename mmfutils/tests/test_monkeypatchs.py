"""A few extra tests to run all the code"""
import os.path
import mmfutils.monkeypatches
import flake8.main
import pytest

PROJECT_DIR = os.path.join(os.path.dirname(mmfutils.__file__), '..')


class TestCoverage(object):
    @staticmethod
    def run_noerr(self):
        raise SystemExit(0)

    @staticmethod
    def run_err(self):
        raise SystemExit(1)

    @classmethod
    def setup_class(cls):
        reload(mmfutils.monkeypatches)

        class Flake8Command(flake8.main.Flake8Command):
            def __init__(self):
                pass

        cls.flake8_self = Flake8Command()

    def test_cover_monkeypatchs(self):
        # Both these patched commands store the old run method in _run so we
        # can sub it out to ensure coverage testing.
        self.flake8_self.run(_run=self.run_noerr)

    def test_flake8_patch_err(self):
        with pytest.raises(SystemExit):
            self.flake8_self.run(_run=self.run_err)
