"""Small set of utilities: containers and interfaces.

This package provides some utilities that I tend to rely on during
development. Presently in includes some convenience containers and some stubs
for working with `zope.interface <http://docs.zope.org/zope.interface/>`__
without having to introduce an additional dependence.

**Documentation:**
  http://mmfutils.readthedocs.org
**Source:**
  https://bitbucket.org/mforbes/mmfutils
**Issues:**
  https://bitbucket.org/mforbes/mmfutils/issues

"""
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as original_test

import mmfutils.monkeypatches
VERSION = mmfutils.__version__

# Remove mmfutils so that it gets properly covered in tests. See
# http://stackoverflow.com/questions/11279096
for mod in sys.modules.keys():
    if mod.startswith('mmfutils'):
        del sys.modules[mod]
del mod


class test(original_test):
    description = "Run all tests and checks (customized for this project)"

    def finalize_options(self):
        # Don't actually run any "test" tests (we will use nosetest)
        self.test_suit = None

    def run(self):
        # Call this to do complicated distribute stuff.
        original_test.run(self)

        for cmd in ['nosetests', 'flake8', 'check']:
            try:
                self.run_command(cmd)
            except SystemExit, e:
                if e.code:
                    raise

setup(name='mmfutils',
      version=VERSION,
      packages=find_packages(exclude=['tests']),
      cmdclass=dict(test=test),

      install_requires=[
          "zope.interface>=3.8.0",
          "persist>=0.8b1",
      ],

      extras_require={},

      tests_require=[
          'nose>=1.3',
          'coverage',
          'flake8'],

      dependency_links=[
          'hg+https://bitbucket.org/mforbes/persist@0.9#egg=persist-0.9'
      ],

      # Metadata
      author='Michael McNeil Forbes',
      author_email='michael.forbes+bitbucket@gmail.com',
      url='https://bitbucket.org/mforbes/mmfutils',
      description="Useful Utilities",
      long_description=__doc__,
      license='BSD',

      classifiers=[
          # How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 4 - Beta',

          # Indicate who your project is intended for
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Utilities',

          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: BSD License',

          # Specify the Python versions you support here. In particular, ensure
          # that you indicate whether you support Python 2, Python 3 or both.
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
      ],
      )