# All commands are provided through python setup.py so that they are
# platform independent.  These are included here simply as a
# convenience.

test: envs
	conda run -n _mmfutils pytest

envs:
	conda env update -f environment.yml

README.rst: doc/README.ipynb
	jupyter nbconvert --to=rst --output=README.rst doc/README.ipynb

clean:
	-find . -name "*.pyc" -delete
	-find . -name "*.pyo" -delete
	-find . -name "htmlcov" -type d -exec rm -r "{}" \;
	-find . -name "__pycache__" -exec rm -r "{}" \;
	-rm -r build
	-rm -r mmfutils.egg-info

.PHONY: test envs clean


