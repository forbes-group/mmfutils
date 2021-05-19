"""Module with some tools required by the parallel tests.

The strategy is to put all initialization and dependencies in this
module which will get imported by each engine.  By placing all
functions in this module, we can assure that each engine gets
initialized before the functions are called - even if they start late.

For example, without this, one had a problem running the tests if
nose.tools was not installed.  This would be installed by the
``python setup.py test`` command, but only made available to the main
python process since it is installed "locally".  The engines would
thus fail if they tried to compute with any functions defined in the
testing file which imported nose.tools.
"""


def exp2(p):
    """Return 2^p"""
    return 2 ** p
