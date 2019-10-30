# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.2.4
#   kernelspec:
#     display_name: Python 2
#     language: python
#     name: python2
# ---

# + {"hide_input": true, "hide_output": true, "init_cell": true, "run_control": {"marked": true}}
import mmf_setup;mmf_setup.nbinit()
# -

# # 1. Uncertainties

# When dealing with quantities that have errors, it can be very useful to track the propagation of the errors through automatic differentiation.  The [uncertainties] package does this quite nicely, but there are a few cases not covered which we address here.
#
# [uncertainties]: https://pythonhosted.org/uncertainties/

# ## 1.1 Implicit Relationships

# Often one needs to find the root of a function $f(x, a) = 0$ where $f$ may depend on some parameters $a$ with uncertainties.  This defines the function $x(a)$ implicitly but must be implemeted numerically.

# +
import uncertainties
from uncertainties import ufloat
from scipy.optimize import brentq

a = ufloat(4.0, 0.1, 'a')

def f(x, a, n):
    return x**n - a

def _root(a, n=2):
    """Return `a**(1/n)` using a root-finding algorithm"""
    return brentq(lambda x: f(x, a, n), 0, max(a, 1))

root = uncertainties.wrap(_root)
root(a)
# -

# To start, one can wrap the function using `uncertainties.wrap`.  This uses finite-differences to compute the derivatives which should be okay in general since the results are only valid if the function is approximately linear over the parameter region, however, the algorithm uses a relative step-size of about $10^{-8}$ which is generally the appropriate solution, but might fail in some circumstances (for example, if a function is only linear on a much smaller interval and the uncertaintaies are small).

# %timeit _root(4.0)
# %timeit root(4.0)
# %timeit root(a)

n = ufloat(2, 0.1, 'n')
print root(a, n=2)
print root(a, n=n)


# This approach has two main problems:
#
# * It can be slow.
# * The results may suffer from inaccuracies (finite-difference techniques are very poorly conditioned due the conflict between roundoff and truncation errors).
# * All of the parameters with uncertainties must be passed as arguments.  Thus, for example, the following fails:

# +
class Root(object):
    def __init__(self, n=2.0):
        self.n = n
        
    def _f(self, x, a):
        return x**self.n - a
    
    @uncertainties.wrap
    def __call__(self, a):
        return brentq(lambda x: self._f(x, a), 0, max(a, 1))

print Root(n=2)(a)
#print Root(n=n)(a)  # Fails
# -

# One solution to this problem is to explicitly compute the derivatives 

# $$
#   f(x, \vec{a}) = 0, \qquad
#   \pdiff{f}{x}\d{x} + \pdiff{f}{a_i}\d{a_i} = 0, \\
#   \pdiff{x}{a_i} =  -\pdiff{f}{a_i}\left(\pdiff{f}{x}\right)^{-1},\\
#   x = x_0 + \pdiff{x}{a_i}(a_i - a_i)
# $$

# +
def solve(f, a, b):
    """Return the root of f with uncertainties."""
    x = brentq(lambda _x: uncertainties.nominal_value(f(_x)), a, b)
    _x = ufloat(x, 0, tag='x')
    zero = f(_x)
    params = [_k for _k in zero.derivatives if _k is not _x]
    return x - sum((_p - uncertainties.nominal_value(_p))
                    *zero.derivatives[_p]/zero.derivatives[_x]
                    for _p in params)

root = Root(n=n)
x = solve(lambda x: root._f(x, a), 0, 3.0)
exact = a**(1./n)

n.std_dev = 0.2  # Change the uncertainty to make sure it tracks through
print x
print exact
print x-exact
# -

# Note that there is no uncertainty in the final answer indicating that we have correctly linked the derivatives to the original variables.
