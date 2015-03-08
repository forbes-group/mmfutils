"""Check for coding conformance"""
import os.path

import pep8
import flake8.main

import nose.tools as nt

import mmfutils

PROJECT_DIR = os.path.join(os.path.dirname(mmfutils.__file__), '..')


def find_py_files(root=PROJECT_DIR):
    files = []

    def gather(files, dirname, fnames):
        for fname in [os.path.join(dirname, _f) for _f in fnames]:
            if os.path.isfile(fname) and os.path.splitext(fname)[1] == '.py':
                files.append(fname)

    os.path.walk(root, gather, files)
    return files


class TestCodeFormat(object):
    # Skip this since it is covered by flake8
    def setUp(self):
        self.files = find_py_files()

    def _test_pep8_conformance(self):
        """Test that we conform to PEP8."""
        style_guide = pep8.StyleGuide(paths=self.files)
        result = style_guide.check_files()
        nt.eq_(result.total_errors, 0,
               "Found {0} code style errors (and warnings)."
               .format(result.total_errors))

    def test_flake8_conformance(self):
        # Pass in the files here so that config setup.cfg file gets found
        style_guide = flake8.main.get_style_guide(paths=self.files)
        result = style_guide.check_files()
        nt.eq_(result.total_errors, 0,
               "Found {0} code style errors (and warnings)."
               .format(result.total_errors))
