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

from setuptools import setup, find_packages, Extension

import mmfutils
VERSION = mmfutils.__version__

USE_CYTHON = False
CYTHON_EXT = '.pyx' if USE_CYTHON else '.c'

setup_requires = [
    'setuptools>=18.0',      # automatically handles Cython extensions
    'cython>=0.28.4' if USE_CYTHON else ''
]

install_requires = [
    'zope.interface>=3.8.0',
    'husl',
    'pathlib',
    'backports.tempfile',
]

test_requires = [
    'pytest',
    'pytest-cov',
    'pytest-flake8',
    'pytest-xdist',
    'coverage',
    'flake8',
    "ipython>=4.0",
    "ipyparallel",
    "persist",
    "numpy",
    "numexpr",
    "uncertainties",
    "pyfftw",
]

extras_require = dict(
    doc=['sphinxcontrib.zopeext',
         'numpy',
         'matplotlib'],
)

extensions = [
    Extension(
        'mmfutils.math.integrate._ssum',
        ['mmfutils/math/integrate/_ssum_cython' + CYTHON_EXT]
    )]

# Remove mmfutils so that it gets properly covered in tests. See
# http://stackoverflow.com/questions/11279096
for mod in list(sys.modules.keys()):
    if mod.startswith('mmfutils'):
        del sys.modules[mod]
del mod


if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)


setup(name='mmfutils',
      # Python 3.8 does not work yet with ipyparallel
      # https://github.com/ipython/ipyparallel/issues/396
      python_requires='>2,<3.8',
      version=VERSION,
      packages=find_packages(exclude=['tests']),

      ext_modules=extensions,
      setup_requires=setup_requires,
      install_requires=install_requires,
      extras_require=extras_require,
      tests_require=test_requires,

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
          'Programming Language :: Python :: 3.7',
      ],
      )
