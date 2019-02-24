# All commands are provided through python setup.py so that they are platform independent.
# These are included here simply as a convenience.

test: envs test2 test3

test2:
	conda run -n _test2 py.test

test3: 
	conda run -n _test3 py.test

envs:
	conda env update -f environment._test2.yml
	conda env update -f environment._test3.yml



.PHONY: test test2 test3 envs
