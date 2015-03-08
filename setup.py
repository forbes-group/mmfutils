"""Small set of utilities that I commonly use.

This package provides some utilities that I tend to rely on during development.
Since I use these in many different projects, I turned this into a repository
so that I can easily sync and keep track of updates.  Once the intreface and
contents become stable, it will probably make sense to include these directly
along with the original project so that an additional dependency is not
introduced.
"""

# Author: Michael McNeil Forbes <mforbes@physics.ubc.ca>

dependencies = []

if __name__ == "__main__":
    from setuptools import setup, find_packages

setup(name='mmfutils',
      version='0.1',
      packages=find_packages(),

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
      url='http://alum.mit.edu/www/mforbes',
      description="Useful Utilities",
      long_description=__doc__,
      )
