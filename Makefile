# All commands are provided through python setup.py so that they are
# platform independent.  These are included here simply as a
# convenience.

PANDOC_FLAGS = --toc --standalone
test:
	nox

README.rst: doc/README.ipynb
	jupyter nbconvert --to=rst --output=README.rst doc/README.ipynb

%.html: %.rst
	rst2html5.py $< > $@

%.html: %.md
	pandoc $(PANDOC_FLAGS) $< -o $@  && open -g -a Safari $@
	fswatch -e ".*\.html" -o . | while read num ; do pandoc $(PANDOC_FLAGS) $< -o $@ && open -g -a Safari $@; done


clean:
	$(RM) -r .nox .conda fil-result
	find . -type d -name "htmlcov"  -exec $(RM) -r {} +
	find . -type d -name "__pycache__" -exec $(RM) -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	$(RM) -r build
	$(RM) -r src/mmfutils.egg-info
	$(RM) -r doc/README_files/
	$(RM) *.html

.PHONY: test clean auto
