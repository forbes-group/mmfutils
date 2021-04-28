# All commands are provided through python setup.py so that they are
# platform independent.  These are included here simply as a
# convenience.

test:
	nox

README.rst: doc/README.ipynb
	jupyter nbconvert --to=rst --output=README.rst doc/README.ipynb

%.html: %.rst
	rst2html5.py $< > $@

%.html: %.md
	pandoc -o $@ $< 

clean:
	-find . -name "*.pyc" -delete
	-find . -name "*.pyo" -delete
	-find . -name "htmlcov" -type d -exec rm -r "{}" \;
	-find . -name "__pycache__" -exec rm -r "{}" \;
	-rm -r build
	-rm -r mmfutils.egg-info
	-rm -r .nox
	-rm -r doc/README_files/
	-rm *.html

.PHONY: test clean
