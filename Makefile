# All commands are provided through python setup.py so that they are platform independent.
# These are included here simply as a convenience.

test:
	python setup.py nosetests

.PHONY: test