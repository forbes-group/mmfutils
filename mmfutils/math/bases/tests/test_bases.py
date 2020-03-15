r"""

As a test function, we compute the Laplacian of a Gaussian which has
the following form:

.. math::

            y(r) &= e^{-(r/r_0)^2/2}\\
   \nabla^2 y(r) &= \frac{r^2 - dr_0^2}{r_0^4} y(r)\\
   e^{a\nabla^2} y(r) &= \frac{r_0^d}{\sqrt{r_0^2+2a}^d}
   e^{-r^2/(r_0^2+2a)/2}
"""
import numpy as np
import scipy.special
import scipy as sp

import pytest

from mmfutils.interface import verifyObject, verifyClass
from mmfutils.math.bases import bases
from mmfutils.math.bases.interfaces import (
    IBasis, IBasisWithConvolution, IBasisKx, IBasisLz)

del scipy

# def rand_complex(shape):
#     """Return a random complex array"""
#     return (np.random.random(shape) + np.random.random(shape) * 1j
#             - 0.5 - 0.5j)


class ExactGaussian(object):
    def __init__(self, r, A=1.1, factor=1.0, r_0=1.0, d=1):
        self.r = r
        self.A = A
        self.factor = factor
        self.r_0 = r_0
        self.d = d

    def get_y(self, r_0=None):
        if r_0 is None:
            r_0 = self.r_0
        return self.A * np.exp(-(self.r/r_0)**2/2.0)

    @property
    def y(self):
        return self.get_y()

    @property
    def n(self):
        """Exact density"""
        return abs(self.y)**2

    @property
    def N_3D(self):
        """Exact total particle number in 3D."""
        return self.r_0**3 * np.pi**(3./2.) * self.A**2

    @property
    def d2y(self):
        """Exact Laplacian with factor"""
        return (self.factor * self.y
                * (self.r**2 - self.d*self.r_0**2)/self.r_0**4)

    @property
    def grad_dot_grad(self):
        """Exact grad_dot_grad."""
        return self.r**2/self.r_0**4 * self.y**2

    def get_dy(self, x):
        """Exact gradient along x direction"""
        return (-self.y * x/self.r_0**2)

    @property
    def exp_d2y(self):
        """Exact exponential of laplacian with factor applied to y"""
        r_0 = np.sqrt(self.r_0**2 + 2*self.factor)
        return (self.r_0/r_0)**self.d * self.get_y(r_0=r_0)

    @property
    def convolution(self):
        """Exact convolution of the Gaussian with itself."""
        return (self.A**2 * self.r_0**3 * np.pi**(3./2.)
                * np.exp(-(self.r/self.r_0)**2/4.0))


class ExactGaussianQuart(ExactGaussian):
    """In order to test the k2 and kx2 option of the laplacian for Periodic
    bases, we add a quartic term $k^2 + (k^2)^2$.
    """
    @property
    def d2y(self):
        """Exact Laplacian with factor"""
        r = self.r
        r0 = self.r_0
        d = self.d
        return (
            self.factor * self.y
            * (-r**4 + 2*r**2*(d+2)*r0**2 + (r**2 - d**2 - 2*d)*r0**4 - d*r0**6)
            / r0**8)

    @property
    def exp_d2y(self):
        """Exact exponential of laplacian with factor applied to y"""
        r_0 = np.sqrt(self.r_0**2 + 2*self.factor)
        return (self.r_0/r_0)**self.d * self.get_y(r_0=r_0)


class ExactGaussianQuartCyl(ExactGaussian):
    """In order to test the k2 and kx2 option of the laplacian for Periodic
    bases, we add a quartic term $k^2 + (k^2)^2$.
    """
    def __init__(self, x, r, A=1.0, factor=1.0, r_0=1.0):
        self.x = x
        self.r = r
        self.A = A
        self.factor = factor
        self.r_0 = r_0

    def get_y(self, r_0=None):
        if r_0 is None:
            r_0 = self.r_0
        r = np.sqrt(self.r**2 + self.x**2)
        return self.A * np.exp(-(r/r_0)**2/2.0)

    @property
    def d2y(self):
        """Exact Laplacian with factor"""
        r = self.r
        x = self.x
        r0 = self.r_0
        d = 1
        d2y_x = (
            (-x**4 + 2*x**2*(d+2)*r0**2 + (x**2 - d**2 - 2*d)*r0**4 - d*r0**6)
            /r0**8)
        d = 2
        d2y_r = (r**2 - d*r0**2)/r0**4
        return (self.factor * self.y * (d2y_x + d2y_r))

    @property
    def exp_d2y(self):
        """Exact exponential of laplacian with factor applied to y"""
        r_0 = np.sqrt(self.r_0**2 + 2*self.factor)
        return (self.r_0/r_0)**self.d * self.get_y(r_0=r_0)


class LaplacianTests(object):
    """Base with some tests for the laplacian functionality.

    Requires the following attributes:

    cls.Basis
    cls.basis
    cls.exact
    """
    @classmethod
    def get_r(cls):
        return np.sqrt(sum(_x**2 for _x in cls.basis.xyz))

    @property
    def r(self):
        return self.get_r()

    @property
    def y(self):
        return self.exact.y

    def test_interface(self):
        assert verifyClass(IBasis, self.Basis)
        assert verifyObject(IBasis, self.basis)

    def test_laplacian(self):
        """Test the laplacian with a Gaussian."""
        # Real and Complex
        laplacian = self.basis.laplacian
        exact = self.exact
        for exact.factor in [(0.5+0.5j), exact.factor]:
            for exact.A in [(0.5+0.5j), exact.A]:
                ddy = laplacian(exact.y, factor=exact.factor)
                assert np.allclose(ddy, exact.d2y)

                exp_ddy = laplacian(exact.y, factor=exact.factor, exp=True)
                assert np.allclose(exp_ddy, exact.exp_d2y)

    def test_grad_dot_grad(self):
        """Test grad_dot_grad function."""
        grad_dot_grad = self.basis.grad_dot_grad
        exact = self.exact
        dydy = grad_dot_grad(exact.y, exact.y)
        # Lower atol since y^2 lies outside of the basis.
        assert np.allclose(dydy, exact.grad_dot_grad, atol=1e-5)

    def test_apply_K(self):
        """Test the application of K."""
        exact = self.exact
        Ky = self.basis.laplacian(exact.y, factor=-0.5)
        Ky_exact = -0.5 * exact.d2y
        assert np.allclose(Ky, Ky_exact)


class ConvolutionTests(LaplacianTests):
    """Adds tests for convolution."""
    def test_interface(self):
        LaplacianTests.test_interface(self)
        assert verifyClass(IBasisWithConvolution, self.Basis)
        assert verifyObject(IBasisWithConvolution, self.basis)

    def test_coulomb(self):
        """Test computation of the coulomb potential."""
        y = [self.y, self.y]    # Test that broadcasting works
        V = self.basis.convolve_coulomb(y)
        V_exact = self.Q * sp.special.erf(self.r/2)/self.r
        assert np.allclose(V[0], V_exact)
        assert np.allclose(V[1], V_exact)

    def test_coulomb_form_factors_stub(self):
        """Test computation of the coulomb potential with form-factors.
        This is just a stub - it does not do a non-trivial test, but checks
        to see that broadcasting works properly.
        """
        def F1(k):
            return [1.0 + k**2, 2.0 + k**2]

        def F2(k):
            return [1./(1.0 + k**2), 1./(2.0 + k**2)]

        y = [self.y]*2
        V = self.basis.convolve_coulomb(y, form_factors=[F1, F2])
        V_exact = self.Q * sp.special.erf(self.r/2)/self.r
        assert np.allclose(V[0], V_exact)
        assert np.allclose(V[1], V_exact)


class TestSphericalBasis(ConvolutionTests):
    @classmethod
    def setup_class(cls):
        cls.Basis = bases.SphericalBasis
        cls.basis = bases.SphericalBasis(N=32*2, R=15.0)
        cls.Q = 8.0
        cls.exact = ExactGaussian(
            r=cls.get_r(), d=3, r_0=np.sqrt(2), A=cls.Q/8.0/np.pi**(3./2.))

    def test_convolution(self):
        """Test the convolution."""
        y = self.y
        convolution = self.basis.convolve(y, y)
        assert np.allclose(convolution, self.exact.convolution)


class TestPeriodicBasis(ConvolutionTests):
    r"""In this case, the exact Coulomb potential is difficult to
    calculate, but for a localized charge distribution, it can be
    computed at the origin in terms of a Madelung constant through the
    relationship

    $$
      V(0) = \frac{e}{4\pi\epsilon_0 r_0}M
    $$

    and $M = -1.7475645946331821906362120355443974034851614$.

    Unfortunately, this is not simply to apply because the
    normalization of the Coulomb potential includes a constant
    subtraction so that the total charge in the unit cell is zero.
    This net neutrality is the only thing that makes sense physically.

    """
    @classmethod
    def setup_class(cls):
        dim = 3
        cls.Basis = bases.PeriodicBasis
        cls.basis = bases.PeriodicBasis(Nxyz=(32,)*dim, Lxyz=(25.0,)*dim)
        cls.Q = 8.0
        cls.exact = ExactGaussian(
            r=cls.get_r(), d=dim, r_0=np.sqrt(2), A=cls.Q/8.0/np.pi**(3./2.))
        cls.exact_quart = ExactGaussianQuart(
            r=cls.get_r(), d=dim, r_0=np.sqrt(2), A=cls.Q/8.0/np.pi**(3./2.))
        cls.Mi = -1.747564594633182190636212

    def test_interface(self):
        super().test_interface()
        assert verifyClass(IBasisKx, self.Basis)
        assert verifyObject(IBasisLz, self.basis)

    def test_coulomb(self):
        """Test computation of the coulomb potential.

        This is a stub: it just makes sure the code
        runs... unfortunately, computing the exact result to check is
        a bit tricky!
        """
        y = [self.y] * 2
        V = self.basis.convolve_coulomb(y)
        V_exact = np.ma.divide(
            self.Q * sp.special.erf(self.r/2),
            self.r).filled(self.Q/np.sqrt(np.pi))
        if False:
            assert np.allclose(V[0], V_exact)
            assert np.allclose(V[1], V_exact)

    def test_coulomb_form_factors_stub(self):
        """Test computation of the coulomb potential with form-factors.
        This is just a stub - it does not do a non-trivial test, but checks
        to see that broadcasting works properly.
        """
        def F1(k):
            return [1.0 + k**2, 2.0 + k**2]

        def F2(k):
            return [1./(1.0 + k**2), 1./(2.0 + k**2)]

        y = [self.y]*2
        V = self.basis.convolve_coulomb(y, form_factors=[F1, F2])
        V_no_ff = self.basis.convolve_coulomb(self.y)
        assert np.allclose(V[0], V_no_ff)
        assert np.allclose(V[1], V_no_ff)

    def test_laplacian_quart(self):
        """Test the laplacian with a Gaussian and modified dispersion."""
        # Real and Complex
        laplacian = self.basis.laplacian
        k2 = sum(_k**2 for _k in self.basis._pxyz)
        k4 = k2**2
        _k2 = k2 + k4
        exact = self.exact_quart
        for exact.factor in [(0.5+0.5j), exact.factor]:
            for exact.A in [(0.5+0.5j), exact.A]:
                ddy = laplacian(exact.y, factor=exact.factor, k2=_k2)
                assert np.allclose(ddy, exact.d2y, atol=1e-6)

                # exp_ddy = laplacian(self.y, factor=exact.factor, exp=True)
                # assert np.allclose(exp_ddy, exact.exp_d2y)

    def test_gradient(self):
        """Test the gradient"""
        get_gradient = self.basis.get_gradient
        xyz = self.basis.xyz
        exact = self.exact
        for exact.A in [(0.5+0.5j), exact.A]:
            dy = get_gradient(exact.y)
            dy_exact = list(map(exact.get_dy, xyz))
            assert np.allclose(dy, dy_exact, atol=1e-7)

    def test_Lz(self):
        """Test Lz"""
        N = 64
        L = 14.0
        b = bases.PeriodicBasis(Nxyz=(N, N), Lxyz=(L, L))
        x, y = b.xyz[:2]
        kx, ky = b._pxyz

        # Exact solutions for a Gaussian with phase
        f = (x+1j*y)*np.exp(-x**2-y**2)
        nabla_f = (4*(x**2+y**2)-8)*f
        Lz_f = f
        
        assert np.allclose(nabla_f, b.laplacian(f))
        assert np.allclose(Lz_f, b.apply_Lz_hbar(f))
        m = 1.1
        hbar = 2.2
        wz = 3.3
        kwz2 = m*wz/hbar
        factor = -hbar**2/2/m
        assert np.allclose(factor*nabla_f - wz*hbar*Lz_f, 
                           b.laplacian(f, factor=factor, kwz2=kwz2))        


class TestCartesianBasis(ConvolutionTests):
    @classmethod
    def setup_class(cls):
        dim = 3
        cls.Basis = bases.CartesianBasis
        cls.basis = bases.CartesianBasis(Nxyz=(32,)*dim, Lxyz=(25.0,)*dim)
        cls.Q = 8.0
        cls.exact = ExactGaussian(
            r=cls.get_r(), d=dim, r_0=np.sqrt(2), A=cls.Q/8.0/np.pi**(3./2.))
        cls.exact_quart = ExactGaussianQuart(
            r=cls.get_r(), d=dim, r_0=np.sqrt(2), A=cls.Q/8.0/np.pi**(3./2.))

    def test_coulomb_exact(self):
        """Test computation of the coulomb potential."""
        y = [self.y]*2   # Test that broadcasting works
        self.basis.fast_coulomb = False
        V_exact = np.ma.divide(
            self.Q * sp.special.erf(self.r/2),
            self.r).filled(self.Q/np.sqrt(np.pi))
        for method in ['sum', 'pad']:
            V = self.basis.convolve_coulomb(y, method=method)
            assert np.allclose(V[0], V_exact)
            assert np.allclose(V[1], V_exact)

    test_coulomb = test_coulomb_exact

    def test_coulomb_fast(self):
        """Test fast computation of the coulomb potential."""
        y = [self.y]*2   # Test that broadcasting works
        self.basis.fast_coulomb = True
        V_exact = np.ma.divide(
            self.Q * sp.special.erf(self.r/2),
            self.r).filled(self.Q/np.sqrt(np.pi))
        V = self.basis.convolve_coulomb(y)
        assert np.allclose(V[0], V_exact, rtol=0.052)
        assert np.allclose(V[1], V_exact, rtol=0.052)
        V = self.basis.convolve_coulomb_fast(y, correct=True)
        assert np.allclose(V[0], V_exact, rtol=0.052)
        assert np.allclose(V[1], V_exact, rtol=0.052)

    def test_coulomb_form_factors_stub(self):
        """Test computation of the coulomb potential with form-factors.
        This is just a stub - it does not do a non-trivial test, but checks
        to see that broadcasting works properly.
        """
        self.basis.fast_coulomb = False

        def F1(k):
            return [1.0 + k**2, 2.0 + k**2]

        def F2(k):
            return [1./(1.0 + k**2), 1./(2.0 + k**2)]

        y = [self.y]*2
        V = self.basis.convolve_coulomb(y, form_factors=[F1, F2])
        V_exact = np.ma.divide(
            self.Q * sp.special.erf(self.r/2),
            self.r).filled(self.Q/np.sqrt(np.pi))
        assert np.allclose(V[0], V_exact)
        assert np.allclose(V[1], V_exact)

    def test_coulomb_fast_form_factors_stub(self):
        """Test computation of the coulomb potential with form-factors.
        This is just a stub - it does not do a non-trivial test, but checks
        to see that broadcasting works properly.
        """
        self.basis.fast_coulomb = True

        def F1(k):
            return [1.0 + k**2, 2.0 + k**2]

        def F2(k):
            return [1./(1.0 + k**2), 1./(2.0 + k**2)]

        y = [self.y]*2
        V = self.basis.convolve_coulomb_fast(y, form_factors=[F1, F2])
        V_exact = np.ma.divide(
            self.Q * sp.special.erf(self.r/2),
            self.r).filled(self.Q/np.sqrt(np.pi))
        assert np.allclose(V[0], V_exact, rtol=0.052)
        assert np.allclose(V[1], V_exact, rtol=0.052)

    def test_laplacian_quart(self):
        """Test the laplacian with a Gaussian and modified dispersion."""
        # Real and Complex
        laplacian = self.basis.laplacian
        k2 = sum(_k**2 for _k in self.basis._pxyz)
        k4 = k2**2
        _k2 = k2 + k4
        exact = self.exact_quart
        for exact.factor in [(0.5+0.5j), exact.factor]:
            for exact.A in [(0.5+0.5j), exact.A]:
                ddy = laplacian(exact.y, factor=exact.factor, k2=_k2)
                assert np.allclose(ddy, exact.d2y, atol=1e-6)

                # exp_ddy = laplacian(self.y, factor=exact.factor, exp=True)
                # assert np.allclose(exp_ddy, exact.exp_d2y)

    def test_gradient(self):
        """Test the gradient"""
        get_gradient = self.basis.get_gradient
        xyz = self.basis.xyz
        exact = self.exact
        for exact.A in [(0.5+0.5j), exact.A]:
            dy = get_gradient(exact.y)
            dy_exact = list(map(exact.get_dy, xyz))
            assert np.allclose(dy, dy_exact, atol=1e-7)


class TestCylindricalBasis(LaplacianTests):
    @classmethod
    def setup_class(cls):
        Lxr = (25.0, 13.0)
        cls.Basis = bases.CylindricalBasis
        cls.basis = bases.CylindricalBasis(Nxr=(64, 32), Lxr=Lxr)
        x, r = cls.basis.xyz
        cls.Q = 8.0
        cls.exact = ExactGaussian(
            r=cls.get_r(), d=3, r_0=np.sqrt(2), A=cls.Q/8.0/np.pi**(3./2.))
        cls.exact_quart = ExactGaussianQuartCyl(
            x=x, r=r, r_0=np.sqrt(2), A=cls.Q/8.0/np.pi**(3./2.))

        cls.Nm = 5             # Number of functions to test
        cls.Nn = 5             # Used when functions are compared
        # Enough points for trapz to give answers to 4 digits.
        cls.R = np.linspace(0.0, Lxr[1]*3.0, 10000)

    def test_basis(self):
        """Test orthonormality of basis functions."""
        b = self.basis
        x, r = b.xyz
        R = self.R
        for _m in range(self.Nm):
            Fm = b._F(_m, R)
            assert np.allclose(np.trapz(abs(Fm)**2, R), 1.0, rtol=1e-3)
            for _n in range(_m+1, self.Nn):
                Fn = b._F(_n, R)
                assert np.allclose(np.trapz(Fm.conj()*Fn, R), 0.0, atol=1e-3)

    def test_derivatives(self):
        """Test the derivatives of the basis functions."""
        b = self.basis
        x, r = b.xyz
        R = self.R + 0.1        # Derivatives are singular at origin
        for _m in range(self.Nm):
            F = b._F(_m, R)
            dF = b._F(_m, R, d=1)

            # Compute the derivative using FD half-way between the lattice
            # points.
            dF_fd = (F[1:] - F[:-1])/np.diff(R)

            # Interpolate dFm to the same lattice midpoints
            dF = (dF[1:] + dF[:-1])/2.0

            assert np.allclose(dF, dF_fd, atol=1e-2)

    def test_laplacian_quart(self):
        """Test the laplacian with a Gaussian and modified dispersion."""
        # Real and Complex
        laplacian = self.basis.laplacian
        kx2 = self.basis._kx2
        kx4 = kx2**2
        _kx2 = kx2 + kx4
        exact = self.exact_quart
        for exact.factor in [(0.5+0.5j), exact.factor]:
            for exact.A in [(0.5+0.5j), exact.A]:
                ddy = laplacian(exact.y, factor=exact.factor, kx2=_kx2)
                assert np.allclose(ddy, exact.d2y)

                # exp_ddy = laplacian(self.y, factor=exact.factor, exp=True)
                # assert np.allclose(exp_ddy, exact.exp_d2y)

    def test_gradient(self):
        """Test the gradient"""
        get_gradient = self.basis.get_gradient
        x, r = self.basis.xyz
        exact = self.exact
        for exact.A in [(0.5+0.5j), exact.A]:
            dy = get_gradient(exact.y)[0]
            dy_exact = exact.get_dy(x)
            assert np.allclose(dy, dy_exact, atol=1e-7)

    def test_integrate1(self):
        x, r = self.basis.xyz
        n = abs(self.exact.y)**2
        assert np.allclose((self.basis.metric*n).sum(), self.exact.N_3D)
        n_1D = self.basis.integrate1(n).ravel()
        r0 = self.exact.r_0
        n_1D_exact = self.exact.A**2*(np.pi*r0**2*np.exp(-x**2/r0**2)).ravel()
        assert np.allclose(n_1D, n_1D_exact)
        
    def test_integrate2(self):
        x, r = self.basis.xyz
        n = abs(self.exact.y)**2
        assert np.allclose((self.basis.metric*n).sum(), self.exact.N_3D)
        y = np.linspace(0, r.max(), 50)[None, :]
        n_2D = self.basis.integrate2(n, y=y)
        r0 = self.exact.r_0
        n_2D_exact = self.exact.A**2*(np.sqrt(np.pi)
                                      *r0*np.exp(-(x**2+y**2)/r0**2))
        assert np.allclose(n_2D, n_2D_exact, rtol=0.01, atol=0.01)


class TestCoverage(object):
    """Walk down some error branches for coverage."""
    def test_convolve_coulomb_exact(self):
        dim = 1
        basis = bases.CartesianBasis(Nxyz=(32,)*dim, Lxyz=(25.0,)*dim)
        exact = ExactGaussian(r=abs(basis.xyz[0]), d=dim)
        with pytest.raises(NotImplementedError):
            basis.convolve_coulomb_exact(exact.y, method='unknown')
