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
#     display_name: Python [conda env:_test3]
#     language: python
#     name: conda-env-_test3-py
# ---

import mmf_setup;mmf_setup.nbinit()

# # Table of Contents
# * [1. Numerical Optimization](#1.-Numerical-Optimization)
# 	* [1.1 Quadratic Test Problem](#1.1-Quadratic-Test-Problem)
# * [2. Termination Criteria](#2.-Termination-Criteria)
# * [3. Other Algorithms](#3.-Other-Algorithms)
#

# # 1. Numerical Optimization

# The basic goal here is to minimize some function $f(\vect{x})$ which has a computable Jacobian $\vect{J}(\vect{x}) = \vect{\nabla}f(\vect{x})$ and possibly a Hessian.  Where possible, we use a (quasi-)Newton's method to quickly find the root $\vect{J}(\vect{x}) = 0$ but fallback to the steepest descent if this fails to reduce the objectives.
#
# Give the following quadratic model:
#
# $$
#   f(\ket{x} + \ket{\delta}) \approx f + \braket{\delta|J} + \frac{\braket{\delta|\mat{H}|\delta}}{2} + \order(\delta^3),
# $$
#
# the descent step and Newton's steps, along with the expected reduction in $f$ are:
#
# $$
#   \ket{\text{descent}} = -\frac{\ket{J}\braket{J|J}}{\braket{J|\mat{H}|J}}, \qquad
#   \delta f = \frac{-\braket{J|J}^2}{2\braket{J|\mat{H}|J}}\\
#   \ket{\text{Newton}} = -\braket{\mat{H}^{-1}|J}, \qquad
#   \delta f = \frac{\braket{J|\mat{H}^{-1}|J}}{2}\\  
# $$
#
#

# ## 1.1 Quadratic Test Problem

# For testing the formula, we use the following quadratic test problem.  Since much of our problem domain involves complex wavefunctions, we keep everything complex:
#
# $$
#   f(\ket{x}) = \frac{1}{2}\braket{x - x_0|\mat{H}|x-x_0} + 1
# $$
#
# where $\mat{H}$ is a positive definite matrix.

# Test above formulae numerically
# %pylab inline --no-import-all
from importlib import reload
import optimization_notes;reload(optimization_notes)
from optimization_notes import crand, braket, QuadraticProblem
np.random.seed(1)
N = 3
p = QuadraticProblem(N=N)
f = p.f
df = p.df
ddf = p.ddf
f_min = f(p.x0)

# +
x = crand(N)  # Starting point
J = df(x)
H = ddf(x)
dx_downhill = -J*braket(J, J) / braket(J, H.dot(J))
dx_newton = -np.linalg.solve(ddf(x), J)
df_downhill = -(braket(J,J)**2/braket(J,H.dot(J))/2.0).real
df_newton = -(braket(J,np.linalg.solve(H, J))/2.0).real

# Check formulae
alphas = np.linspace(-2, 2, 21)
compare = np.array([
    (df_downhill, f(x + dx_downhill) - f(x)),
    (df_newton, f(x + dx_newton) - f(x)),
    ])
assert np.allclose(*residuals.T)

fs = [f(x + _a*dx_downhill) for _a in alphas]
assert np.all(f_min <= np.array(fs))

fs = [f(x + _a*dx_newton) for _a in alphas]
assert np.all(f_min <= np.array(fs))
# -

# # 2. Termination Criteria

# There are two objectives for these problems

# # 3. Other Algorithms

# In principle, the [L-BGFS](https://en.wikipedia.org/wiki/Limited-memory_BFGS) algorithm solves the problem we are interested in, but unfortunately, there seems to be no way to get a refined solution where the gradient is guaranteed to be small.  The problem is that two stopping criteria are used:
#
# $$
#   \DeclareMathOperator{\proj}{proj}
#   \frac{f_k - f_{k+1}}{\max(\abs{f_k}, \abs{f_{k+1}}, 1)} \leq \mathtt{factr}\cdot\varepsilon, \qquad
#   \norm{\proj J}_{\infty}  = \mathtt{pgtol}.
# $$
#
# The problem is that, even if `factr = 0`, noise in the function $f(x)$ may cause the algorithm to converge prematurely.  Here we demonstrate the issue:

# +
import numpy as np
from scipy.optimize.lbfgsb import fmin_l_bfgs_b

def f(x):
    return 1e12 + np.exp((x-1.0)**2)

def df(x):
    return np.array([2.0*(x-1.0)*np.exp((x-1.0)**2)])

fmin_l_bfgs_b(f, x0=[0.0001], fprime=df, factr=0)
# -

# The function to be optimized has roundoff errors due to the large offset, so we would like to use the jacobian for convergence, but even setting `tol=0` does not permit the criterion from being satisfied. (note that `factr = tol / macheps` with SciPy's interface).  My version removes this restriction.

from mmf_lbfgsb.lbfgsb import fmin_l_bfgs_b
fmin_l_bfgs_b(f, x0=[0.0001], fprime=df, factr=0)


