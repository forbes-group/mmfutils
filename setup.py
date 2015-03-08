"""Small set of utilities that I commonly use.

This package provides some utilities that I tend to rely on during development.
Since I use these in many different projects, I turned this into a repository
so that I can easily sync and keep track of updates.  Once the intreface and
contents become stable, it will probably make sense to include these directly
along with the original project so that an additional dependency is not
introduced.

**Documentation:**
  http://mmfutils.readthedocs.org
**Source:**
  https://bitbucket.org/mforbes/mmfutils
**Issues:**
  https://bitbucket.org/mforbes/mmfutils/issues
"""

# Author: Michael McNeil Forbes <mforbes@physics.ubc.ca>

dependencies = []

if __name__ == "__main__":
    from setuptools import setup, find_packages

import mmfutils

setup(name='mmfutils',
      version=mmfutils.__version__,
      packages=find_packages(exclude=['tests']),

      # install_requires=["zope.interface>=3.8.0"],
      extras_require={
          'testing': [
              "zope.interface>=3.8.0",
              "persist>=1.0",
          ],
      },

      setup_requires=[
          'nose>=1.3',
          'coverage',
          'flake8'],

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
          'Programming Language :: Python :: 2.7',
      ],
      )
