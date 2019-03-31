# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.3'
#       jupytext_version: 1.0.5
#   kernelspec:
#     display_name: Python [conda env:_test2]
#     language: python
#     name: conda-env-_test2-py
# ---

# # Performance

# Here we consider several ways of writing some high-performance code.  We use the example of a stable Kahan's summation method.

# ## Python

# + {"init_cell": true}
import numpy as np
from IPython.display import clear_output

def ssum_python(xs):
    r"""Return (sum(xs), err) computed stably using Kahan's summation
    method for floating point numbers.  (Python version.)
    """
    sum = 0.0
    carry = 0.0
    for x in xs:
        y = x - carry
        tmp = sum + y
        carry = (tmp - sum) - y
        sum = tmp

    eps = np.finfo(np.double).eps
    err = max(abs(2.0*sum*eps), len(xs)*eps*eps)

    return (sum, err)

N = 100000
l = np.array([(10.0*n)**3.0 for n in reversed(range(N+1))])
ans = 250.0*((N + 1.0)*N)**2
print("sum error: {}".format(sum(l) - ans))
print("ssum error: {}".format(ssum_python(l)[0] - ans))
ssum_python(l)
# -

# %timeit ssum_python(l)
# %timeit l.sum()

# ## `weave.inline`

# With python 2 you can use the [`weave.inline`](https://github.com/scipy/weave) package, but this does not work with python 3 and is no longer maintained.

# +
try:
    import weave
except ImportError:
    weave = None

code = '''
double volatile t, y;
double sum = 0.0;
double volatile c = 0.0;
int i;
Py_BEGIN_ALLOW_THREADS
for (i=0;i<Nxs[0];++i) {
    y = xs[i] - c;
    t = sum + y;
    c = (t - sum) - y;
    sum = t;
}
Py_END_ALLOW_THREADS
return_val = sum;
'''

def ssum_weave(xs):
    xs = np.asarray(xs).astype(np.double)
    sum = weave.inline(code, ['xs'])

    eps = np.finfo(np.double).eps
    err = max(abs(2.0*sum*eps), len(xs)*eps*eps)

    return (sum, err)


# -

ssum_weave(l), ssum_python(l)

if weave:
    #assert np.allclose(ssum_weave(l)[0], ans)
    #clear_output()
    %timeit ssum_weave(l)

# ## Cython

# Cython provides a good option. In the notebook there is a nice Cython extension that takes care of compilation, but this complicates distribution a bit.  We discuss distribution after the demonstration.

# %load_ext Cython

# +
# %%cython --annotate
#cython: boundscheck=False
#cython: wraparound=False
import numpy
cimport numpy as np
import cython

_EPS = numpy.finfo(numpy.double).eps

def ssum_cython1(xs, _EPS=_EPS):
    r"""Return (sum(xs), err) computed stably using Kahan's summation
    method for floating point numbers.  (Cython version.)
    """
    sum = 0.0
    carry = 0.0
    for x in xs:
        y = x - carry
        tmp = sum + y
        carry = (tmp - sum) - y
        sum = tmp

    eps = _EPS
    err = max(abs(2.0*sum*eps), len(xs)*eps*eps)

    return (sum, err)


def ssum_cython2(cython.numeric[::1] xs):
    r"""Return (sum(xs), err) computed stably using Kahan's summation
    method for floating point numbers.  (Cython version.)
    """
    cdef:
        cython.numeric x, y, sum=0, carry=0, tmp
        cython.double eps
        size_t k, Nx 
    Nx = xs.shape[0]
    for k in range(Nx):
        x = xs[k]
        y = x - carry
        tmp = sum + y
        carry = (tmp - sum) - y
        sum = tmp

    eps = 1e-16
    err = max(abs(2.0*sum*eps), Nx*eps)

    return (sum, err)


# -

sn = 1./np.arange(1, 10**4, dtype=np.float32)
sn = 1./np.arange(1, 10**4, dtype=np.float64)
ssum_cython2(sn)

# +
assert np.allclose(ssum_cython1(l)[0], ans)
assert np.allclose(ssum_cython2(l)[0], ans)

# %timeit ssum_cython1(l)
# %timeit ssum_cython2(np.asarray(l))
# -

# ### Distribution

# Distributing Cython functions is discussed [in the documentation](https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html#distributing-cython-modules).  The recommendation is to include the generated `.c` source files so that users can build without having cython.

# ## Numba



import numba
numba.__version__

# +
import numpy as np
from numba import jit, prange

_EPS = np.finfo(float).eps

@jit(nopython=True)
def ssum_numba1(xs, _EPS=_EPS):
    r"""Return (sum(xs), err) computed stably using Kahan's summation
    method for floating point numbers.  (Numba version.)
    """
    sum = 0.0
    carry = 0.0
    for x in xs:
        y = x - carry
        tmp = sum + y
        carry = (tmp - sum) - y
        sum = tmp

    eps = _EPS
    err = max(abs(2.0*sum*eps), len(xs)*eps*eps)

    return (sum, err)

assert np.allclose(ssum_numba1(l)[0], ans)
# -

# %timeit ssum_numba1(l)

# # Summary

# From a performance perspective, both numba and Cython are similar and about 3 times faster than weave (which I do not understand, this is not just due to boiler-plate as the difference remains even for larger arrays.)

N = 100000000
l = np.array([(10.0*n)**3.0 for n in reversed(range(N+1))])

if weave:
    print("weave:")
    %timeit ssum_weave(l)
print("sum:")
# %timeit l.sum()
print("cython:")
# %timeit ssum_cython2(l)
print("numba:")
# %timeit ssum_numba1(l)




















