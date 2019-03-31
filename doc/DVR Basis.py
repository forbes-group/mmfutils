# -*- coding: utf-8 -*-
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

# + {"init_cell": true}
import mmf_setup;mmf_setup.nbinit()
# -

# Here are the properties of the basis, including abscissa, basis functions, integration weights, and some quantities that appear in the DVR literature.  The general idea of a DVR basis is to introduce a set of basis functions $F_n(x) = \braket{x|F_n}$ and an associated set of abscissa $x_n$ such that:
#
# \begin{gather}
#   F_{m}(x_n) \propto \delta_{mn}. \tag{locality}
# \end{gather}
#
# These bases are generalized version of the Dirac delta function $\delta(x-x_n) = \braket{x|x_n}$ restricted to a limited set of momenta with maximum momentum $k$:
#
# $$
#   \ket{F_n} \propto \ket{\Delta_n} = \op{P}_{k}\ket{x_n},
#   \qquad \op{P}_k = \int_{p<k}\ket{p}\bra{p}, 
#   \qquad \op{P}_k^2 = \op{P}_k.
# $$
#
# A challenge is to choose a consistent set of abscissa so that these functions are orthogonal:
#
# $$
#   \braket{\Delta_m|\Delta_n} = \braket{x_m|\Delta_n} = \Delta_n(x_m) 
#   = \frac{\delta_{mn}}{\lambda_n}.
# $$
#
# The actual basis functions differ in their normalization so that they are orthonormal:
#
# $$
#   \braket{F_m|F_n} = \delta_{mn} = \lambda_n\braket{\Delta_m|\Delta_n}, 
#   \qquad \ket{F_n} = \sqrt{\lambda_n}\ket{\Delta_n}, \qquad
#   \lambda_n = \frac{1}{\braket{\Delta_n|\Delta_n}}
#             = \frac{1}{\Delta_n(x_n)}
#             = \frac{1}{F_n^2(x_n)}.
# $$
#
# The normalization factors $\lambda_n$ act as a set of integration weights that are exact for all functions $g(x) = F_{i}^*(x) F_{j}(x)$ expressed as products of basis elements:
#
# $$
#   \int g(x) = \sum_n \lambda_n g(x_n), \qquad g(x) = F_{i}(x)^* F_{j}(x).
# $$
#
# These weights can thus be used to effectively compute quantities such as the total particle number by integrating $n(x) = \psi^*(x)\psi(x)$.
#
# This condition ensures that if the wavefunction $\psi(r)$ mostly lies in the subspace spanned by the basis, it can be expanded by simply evaluating it at the abscissa:
#
# $$
#   \braket{F_n|\psi} = \int F_{n}^*(r) \psi(r) 
#   \approx \sum_m \sqrt{\lambda_m}\psi(r_m) \int F_{n}^*(r)F_m(r)
#   = \sum_m \sqrt{\lambda_m}\psi(r_m) \underbrace{
#     \sum_j \lambda_j \overbrace{F_n^*(r_j)F_m(r_j)}
#                               ^{\delta_{nj}\delta_{mj}/\sqrt{\lambda_n^*\lambda_m}}
#     }_{\delta_{mn}}
#   = \sqrt{\lambda_n}\psi(r_n).
# $$
#
# The coefficients can thus be computed by simply evaluating the wavefunction at the abscissa:
#
# $$
#   \psi(r) = \sum_n f_n F_n(r), \qquad f_n = \sqrt{\lambda_n}\psi(r_n).
# $$
#
# The key utility of these bases is that one can obtain exponentially accurate representations if with a tabulated kinetic energy operator, while simply evaluating the potential at the abscissa:
#
# $$
#   K_{mn} = \Braket{F_m|\op{K}|F_n}, \qquad
#   V_{mn} = \braket{F_m|\op{V}|F_n} \approx \delta_{mn}V(r_n).
# $$
#
# In general, choosing a consistent set of basis functions and abscissa is a challenge, and most (all?) known examples are based on some form of orthogonal polynomial.

# ## Sinc-Function Basis

# Here we demonstrate these properties with the sinc-function basis with equally spaced abscissa $x_n$:
#
# \begin{gather}
#   \DeclareMathOperator{\sinc}{sinc}
#  \ket{\Delta_n} = \op{P}_k\ket{x_n}, \qquad \op{P}_k 
#  = \int_{p<k} \frac{\d{p}}{2\pi}\ket{p}\bra{p},
#  \\
#  \Delta_n(x) = \braket{x|\Delta_n} 
#   = \int_{-k}^{k} \frac{\d{p}}{2\pi}e^{\I p (x-x_n)}
#   = \frac{k}{\pi}\sinc \bigl(k(x-x_n)\bigr)
#   \\
#   x_n = x_0 + an, \qquad z_n = kx_n = k x_0 + \pi n, \qquad a = \frac{\pi}{k} 
#   \tag{abscissa}
#   \\
#   \lambda_n = \braket{\Delta_n|\Delta_n}^{-1} = \frac{1}{\Delta_n(x_n)} 
#                                               = \frac{1}{F_n^2(x_n)} = a
#   \tag{weights}
#   \\
#   F_n(x) = \sqrt{\lambda_n}\Delta_n(x) = \frac{\sinc \bigl(k(x-x_n)\bigr)}{\sqrt{a}}
#   \tag{basis functions}
#   \\
#   \op{T}_{mn} = \Bigl\langle F_m\Big|-\diff[2]{}{x}\Big|F_n\Bigr\rangle = \frac{1}{a^2}\begin{cases}
#     2(-1)^{m-n}/(m-n)^2 & m \neq n,\\
#     \pi^2/3 & m = n.
#   \end{cases}\tag{kinetic term}
# \end{gather}
#

# ## Cylindrical Basis

# To represent problems with cylindrical coordinates we use a periodic basis for $x$ and a bessel-function DVR basis for the radial coordinate. Here we describe the properties of the bessel-function basis.  These are expressed in terms of the [Bessel function](https://en.wikipedia.org/wiki/Bessel_function#Bessel's_integrals) (with $n \equiv \alpha \equiv \nu$:
#
# $$
#   J_\nu(x) = \frac{1}{\pi}\int_0^{\pi}\cos(\nu\tau - x\sin\tau)\d{\tau} 
#   - \frac{\sin \nu\pi}{\pi}\int_0^\infty e^{-x\sinh t - \nu t}\d{t} 
# $$

# +
import numpy as np
from scipy.integrate import quad
from mmfutils.math import bessel

alpha = 1.1
x = 1.5
J_0 = bessel.J(alpha, 0)
J_0(x)

def J(x, nu):
    """Integral definition of J_n(x)."""
    def integrand1(tau):
        return np.cos(nu*tau-x*np.sin(tau))/np.pi
    def integrand2(t):
        return np.sin(nu*np.pi)*np.exp(-x*np.sinh(t) - nu*t)/np.pi
    res1, err1 = quad(integrand1, 0, np.pi)
    res2, err2 = quad(integrand2, 0, np.inf)
    return res1 - res2, np.sqrt(err1**2 + err2**2)

assert np.allclose(J(x, alpha)[0], J_0(x))
# -

# %pylab inline --no-import-all
plt.figure(figsize=(12,3))
z = np.linspace(0, 10*np.pi, 100)
for nu in [0,1,2,3]:
    l, = plt.plot(z/np.pi, bessel.J(nu,d=0)(z), 
                  label=r"$\nu={}$".format(nu))
    for z0 in bessel.j_root(nu, 10):
        if z0 <= z.max():
            plt.axvline(z0/np.pi, c=l.get_c(), ls='-', alpha=0.5)
plt.grid(True)
plt.legend()
plt.xlabel(r'$z/\pi$');
plt.ylabel(r'$J_0(z)$');

# Recall that in $d$-dimensions, [the Laplacian is](https://en.wikipedia.org/wiki/Spherical_harmonics#Higher_dimensions):
#
# $$
#   \nabla^2 = \Delta^{\mathbb{R}^{d}} = r^{1-d}\pdiff{}{r}r^{d-1}\pdiff{}{r} 
#   + \frac{1}{r^2}\Delta_{S^{d-1}}
# $$
#
# where $\Delta_{S^{d-1}}$ is the Laplacian suitably restricted to the sphere $S^{d-1}$ (i.e. the [Laplace–Beltrami operator](https://en.wikipedia.org/wiki/Laplace–Beltrami_operator).  Expressing the wavefunction in terms of "spherical" harmonics $Y_l^m(\uvect{x})$, one has:
#
# $$
#   \Delta_{S^{d-1}}Y_l^m(\uvect{x}) = -l(l+d-2)Y_l^m(\uvect{x}).
# $$
#
# The wavefunction can thus be expressed in terms of the following basis:
#
# $$
#   \psi(\vect{x}) = \frac{1}{r^{(d-1)/2}}u(r)Y_l^m(\uvect{x}),
# $$
#
# such that the radial wavefunction $u(r)$ satisfies:
#
# $$
#   \nabla^2\psi(r, \Omega) 
#   = \frac{Y_l^m(\uvect{x})}{r^{(d-1)/2}}\left[
#     \diff[2]{}{r} - \frac{\nu_{d,l}^2 - 1/4}{r^2}
#   \right]u(r), \qquad
#   \nu_{d,l} = l + \frac{d}{2} - 1.
# $$
#
# The Bessel-function DVR basis is chosen to provide an exponentially accurate representation of the radial portion of the wavefunction, including the singular centrifugal piece.  The advantage of this is exponential accuracy for analytic potentials, but each $\nu_{d,l}$ has a different set of abscissa which is inconvenient.  We have found that fairly good accuracy can be achieved using only $l=0$ and $l=1$ bases, shifting the residual portion of the $r^{-2}$ term into the potential, but this needs to be carefully checked.  (For example, with $d=3$, the $l=0$ basis works well for even $l$ while the $l=1$ basis must be used for odd $l$.)

# The Bessel-function DVR basis thus provides an orthonormal basis for the radial wavefunctions under the metric:
#
# $$
#   \braket{f|g} = \int_0^{\infty} f^*(r)g(r)\d{r}.
# $$
#
# Here are the details of the basis:
#
# \begin{gather}
#   \nu = l+\frac{d}{2}-1,\\
#   J_\nu(k r_n) = 0, \qquad z_n = k r_n, \tag{abscissa}\\
#   F_n(r) = (-1)^{n+1}\frac{\sqrt{2k_r}H(k r)}{1+r/r_n}, \qquad
#   H_n(z) = \frac{\sqrt{z} J_\nu(z)}{z-z_n}, \tag{basis functions}
#   \\
#   \lambda_n = \frac{1}{F_n(r_n)^2} = \frac{2}{k z_n [J_\nu'(z_n)]^{2}} \tag{weights}\\
#   [\mat{T}]_{mn} = \Biggl\langle F_m\Bigg|-\diff[2]{}{r}+\frac{\nu^2-\tfrac{1}{4}}{r^2}
#                                 \Bigg|F_n\Biggr\rangle
#    = k^2\begin{cases}
#     (-1)^{m-n}\frac{8z_mz_n}{(z_m^2 - z_n^2)^2}  & n \neq m\\
#     \tfrac{1}{3}\left[1 + \frac{2(\nu^2 - 1)}{z_n^2}\right] & n = m
#     \end{cases},
#     \tag{kinetic term}
# \end{gather}

# For use with wavefunctions, we must include the transformation to and from

from itertools import product
list(product([1,2,3], ['a', 'b']))



from mmfutils.math.bases import CylindricalBasis
basis = CylindricalBasis(Nxr=(2, 10), Lxr=(1.0, 1.0))
x, r = basis.xyz
k_x, k_r = basis.k_max

# ## Integrals

# In the cylindrical basis, we tabulate functions over $x$ and $r$.  For visualization, it is often desired to express these in terms of line-of-sight integrals.  The formal definitions are:
#
# \begin{align}
#   \newcommand{\d}{\mathrm{d}}
#   \newcommand{\abs}[1]{{\lvert#1\rvert}}
#   \d{r} &= \frac{y\d{y} + z\d{z}}{r}\\
#   n_{2D}(x, y) &= \int_{-\infty}^\infty \d{z}\; n(x, r)
#                = \int_{-\infty}^\infty \d{z}\; n(x, \sqrt{y^2+z^2})
#                = 2\int_0^{\abs{y}} \d{r}\; \frac{rn(x, r)}{\sqrt{r^2-y^2}}\\
#   n_{1D}(x) &= \iint_{-\infty}^\infty \d{y}\d{z}\; n(x, r)
#             = \int_0^{\infty} \d{r}\; 2\pi r n(x, r)
# \end{align}

# For testing, consider a Gaussian:
#
# $$
#   n(x, r) = e^{-(x^2+r^2)/r_0^2}, \qquad
#   n_{2D}(x,y) = \sqrt{\pi}r_0e^{-(x^2+y^2)/r_0^2}, \qquad
#   n_{1D}(x) = \pi r_0^2e^{-x^2/r_0^2}.
# $$

from mmfutils.math.bases import CylindricalBasis
from mmfutils.math.bases.tests import test_bases
basis = CylindricalBasis(Nxr=(2, 10), Lxr=(1.0, 1.0))
x, r = basis.xyz
gaussian = test_bases.ExactGaussian(r=r, d=2)



