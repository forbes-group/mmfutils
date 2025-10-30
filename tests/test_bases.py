r"""

As a test function, we compute the Laplacian of a Gaussian which has
the following form:

.. math::

            y(r) &= e^{-(r/r_0)^2/2}\\
   \nabla^2 y(r) &= \sum_{i}\frac{(f_i^2 (x_i^2 - r_0^2)}{r_0^4} y(r)\\
   e^{a\nabla^2} y(r) &= \frac{r_0^d}{\sqrt{r_0^2+2a}^d}
   e^{-r^2/(r_0^2+2a)/2}
"""

import contextlib
import functools
import gc
import os
import psutil
import re

import numpy as np
import scipy.special
import scipy as sp

import pytest

import mmfutils.performance.threads
from mmfutils.interface import verifyObject, verifyClass
from mmfutils.math.bases import bases
from mmfutils.math.bases.interfaces import (
    IBasis,
    IBasisWithConvolution,
    IBasisKx,
    IBasisLz,
)

del scipy

# def rand_complex(shape):
#     """Return a random complex array"""
#     return (np.random.random(shape) + np.random.random(shape) * 1j
#             - 0.5 - 0.5j)


@pytest.fixture
def get_mem_MB():
    """Current memory usage in MB."""
    process = psutil.Process(os.getpid())
    mem0 = [process.memory_info().rss / 1024**2]

    def _get_mem(reset=False):
        if reset:
            mem0[0] = process.memory_info().rss / 1024**2
        return process.memory_info().rss / 1024**2 - mem0[0]

    yield _get_mem


@pytest.fixture(params=[0, 0.5])
def memoization_GB(request):
    yield request.param


class ExactGaussian:
    """Exact gaussian with different standard deviations Rs and factors."""

    # Degeneracy factors.  What are the dimensions of each component?
    ds = (1, 1, 1)

    def __init__(
        self, xyz, A=1.1, factor=1.0, factors=(1.0, 1.0, 1.0), Rs=(1.0, 1.0, 1.0)
    ):
        self.xyz = xyz
        self.A = A
        self.factor = factor
        self.factors = factors
        self.Rs = Rs

    def get_y(self, Rs=None):
        if Rs is None:
            Rs = self.Rs
        return self.A * np.exp(-sum(((x / R) ** 2) / 2.0 for x, R in zip(self.xyz, Rs)))

    @property
    def y(self):
        return self.get_y()

    @property
    def n(self):
        """Exact density"""
        return abs(self.y) ** 2

    @property
    def N_3D(self):
        """Exact total particle number in 3D."""
        return np.prod(np.pow(np.sqrt(np.pi) * self.Rs, self.ds)) * self.A**2

    @property
    def d2y(self):
        """Exact Laplacian with factors"""
        return (
            self.factor
            * self.y
            * sum(
                f**2 * (x**2 - d * R**2) / R**4
                for x, R, f, d in zip(self.xyz, self.Rs, self.factors, self.ds)
            )
        )

    @property
    def grad_dot_grad(self):
        """Exact grad_dot_grad with factors."""
        return (
            sum((f * x) ** 2 / R**4 for x, R, f in zip(self.xyz, self.Rs, self.factors))
            * self.y**2
        )

    def get_grad(self):
        """Return the gradient with factors."""
        y = self.y
        return [-f * x / R**2 * y for x, R, f in zip(self.xyz, self.Rs, self.factors)]

    @property
    def exp_d2y(self):
        """Exact exponential of laplacian with factors applied to y"""
        Rs = [
            np.sqrt(R**2 + 2 * self.factor * f**2)
            for R, f in zip(self.Rs, self.factors)
        ]
        return np.prod(np.divide(self.Rs, Rs) ** self.ds[: len(Rs)]) * self.get_y(Rs=Rs)

    @property
    def convolution(self):
        """Exact convolution of the Gaussian with itself."""
        raise NotImplementedError
        return (
            self.A**2
            * self.r_0**3
            * np.pi ** (3.0 / 2.0)
            * np.exp(-((self.r / self.r_0) ** 2) / 4.0)
        )


class ExactGaussianCyl(ExactGaussian):
    """Cylindrically symmetric gaussian."""

    ds = (1, 2)

    def __init__(self, xr, A=1.1, factor=1.0, factors=(1.0, 1.0), Rs=(1.0, 1.0)):
        self.xr = xr
        self.A = A
        self.factor = factor
        self.factors = factors
        self.Rs = Rs

    @property
    def xyz(self):
        """Used for some common methods... don't rely on."""
        return self.xr


class ExactGaussianR:
    """Spherically symmetric gaussian."""

    def __init__(self, r, A=1.1, factor=1.0, factors=None, r_0=1.0, d=1):
        self.r = r
        self.A = A
        self.factor = factor
        self.r_0 = r_0
        self.d = d

    def get_y(self, r_0=None):
        if r_0 is None:
            r_0 = self.r_0
        return self.A * np.exp(-((self.r / r_0) ** 2) / 2.0)

    @property
    def y(self):
        return self.get_y()

    @property
    def n(self):
        """Exact density"""
        return abs(self.y) ** 2

    @property
    def N_3D(self):
        """Exact total particle number in 3D."""
        return self.r_0**3 * np.pi ** (3.0 / 2.0) * self.A**2

    @property
    def d2y(self):
        """Exact Laplacian with factor"""
        return self.factor * self.y * (self.r**2 - self.d * self.r_0**2) / self.r_0**4

    @property
    def grad_dot_grad(self):
        """Exact grad_dot_grad."""
        return self.r**2 / self.r_0**4 * self.y**2

    def get_dy(self, x):
        """Exact gradient along x direction"""
        return -self.y * x / self.r_0**2

    @property
    def exp_d2y(self):
        """Exact exponential of laplacian with factor applied to y"""
        r_0 = np.sqrt(self.r_0**2 + 2 * self.factor)
        return (self.r_0 / r_0) ** self.d * self.get_y(r_0=r_0)

    @property
    def convolution(self):
        """Exact convolution of the Gaussian with itself."""
        return (
            self.A**2
            * self.r_0**3
            * np.pi ** (3.0 / 2.0)
            * np.exp(-((self.r / self.r_0) ** 2) / 4.0)
        )


class ExactGaussianQuart(ExactGaussianR):
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
            self.factor
            * self.y
            * (
                -(r**4)
                + 2 * r**2 * (d + 2) * r0**2
                + (r**2 - d**2 - 2 * d) * r0**4
                - d * r0**6
            )
            / r0**8
        )

    @property
    def exp_d2y(self):
        """Exact exponential of laplacian with factor applied to y"""
        r_0 = np.sqrt(self.r_0**2 + 2 * self.factor)
        return (self.r_0 / r_0) ** self.d * self.get_y(r_0=r_0)


class ExactGaussianQuartCyl(ExactGaussianR):
    """In order to test the k2 and kx2 option of the laplacian for Cylindrical
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
        return self.A * np.exp(-((r / r_0) ** 2) / 2.0)

    @property
    def d2y(self):
        """Exact Laplacian with factor"""
        r = self.r
        x = self.x
        r0 = self.r_0
        d = 1
        d2y_x = (
            -(x**4)
            + 2 * x**2 * (d + 2) * r0**2
            + (x**2 - d**2 - 2 * d) * r0**4
            - d * r0**6
        ) / r0**8
        d = 2
        d2y_r = (r**2 - d * r0**2) / r0**4
        return self.factor * self.y * (d2y_x + d2y_r)

    @property
    def exp_d2y(self):
        """Exact exponential of laplacian with factor applied to y"""
        r_0 = np.sqrt(self.r_0**2 + 2 * self.factor)
        return (self.r_0 / r_0) ** self.d * self.get_y(r_0=r_0)


class LaplacianTests:
    """Base with some tests for the laplacian functionality.

    Requires the following fixtures:

    Basis
    basis
    exact
    """

    def get_r(self, basis):
        return np.sqrt(sum(_x**2 for _x in basis.xyz))

    # @property
    # def y(self):
    #    return self.exact.y

    def test_interface(self, basis):
        assert verifyClass(IBasis, self.Basis)
        assert verifyObject(IBasis, basis)

    def test_laplacian(self, basis, exact_r, threads):
        """Test the laplacian with a Gaussian."""
        # Real and Complex
        exact = exact_r
        laplacian = basis.laplacian
        for exact.factor in [(0.5 + 0.5j), exact.factor]:
            for exact.A in [(0.2 - 0.2j), exact.A]:
                ddy = laplacian(exact.y, factor=exact.factor)
                assert np.allclose(ddy, exact.d2y)
                if getattr(basis, "memoization_GB", 1) == 0:
                    with pytest.raises(NotImplementedError):
                        exp_ddy = laplacian(exact.y, factor=exact.factor, exp=True)
                        assert np.allclose(exp_ddy, exact.exp_d2y)
                else:
                    exp_ddy = laplacian(exact.y, factor=exact.factor, exp=True)
                    assert np.allclose(exp_ddy, exact.exp_d2y)

    def test_grad_dot_grad(self, basis, exact_r):
        """Test grad_dot_grad function."""
        exact = exact_r
        grad_dot_grad = basis.grad_dot_grad
        dydy = grad_dot_grad(exact.y, exact.y)
        # Lower atol since y^2 lies outside of the basis.
        assert np.allclose(dydy, exact.grad_dot_grad, atol=1e-5)

    def test_apply_K(self, basis, exact_r):
        """Test the application of K."""
        exact = exact_r
        Ky = basis.laplacian(exact.y, factor=-0.5)
        Ky_exact = -0.5 * exact.d2y
        assert np.allclose(Ky, Ky_exact)

    @pytest.fixture
    def exact_r(self, basis):
        return ExactGaussianR(
            r=self.get_r(basis),
            d=3,
            r_0=np.sqrt(2),
            A=self.Q / 8.0 / np.pi ** (3.0 / 2.0),
        )


class ConvolutionTests(LaplacianTests):
    """Adds tests for convolution."""

    def test_interface(self, basis):
        LaplacianTests.test_interface(self, basis)
        assert verifyClass(IBasisWithConvolution, self.Basis)
        assert verifyObject(IBasisWithConvolution, basis)

    def test_coulomb(self, basis, exact_r):
        """Test computation of the coulomb potential."""
        exact = exact_r
        y = [exact.y] * 2  # Test that broadcasting works
        V = basis.convolve_coulomb(y)
        r = self.get_r(basis)
        V_exact = self.Q * sp.special.erf(r / 2) / r
        assert np.allclose(V[0], V_exact)
        assert np.allclose(V[1], V_exact)

    def test_coulomb_form_factors_stub(self, basis, exact_r):
        """Test computation of the coulomb potential with form-factors.
        This is just a stub - it does not do a non-trivial test, but checks
        to see that broadcasting works properly.
        """
        exact = exact_r

        def F1(k):
            return [1.0 + k**2, 2.0 + k**2]

        def F2(k):
            return [1.0 / (1.0 + k**2), 1.0 / (2.0 + k**2)]

        y = [exact.y] * 2
        V = basis.convolve_coulomb(y, form_factors=[F1, F2])
        r = self.get_r(basis)
        V_exact = self.Q * sp.special.erf(r / 2) / r
        assert np.allclose(V[0], V_exact)
        assert np.allclose(V[1], V_exact)

    @pytest.fixture
    def exact_quart(self, basis):
        return ExactGaussianQuart(
            r=self.get_r(basis),
            d=self.dim,
            r_0=np.sqrt(2),
            A=self.Q / 8.0 / np.pi ** (3.0 / 2.0),
        )


class TestSphericalBasis(ConvolutionTests):
    Basis = bases.SphericalBasis
    Q = 8.0

    @pytest.fixture
    def basis(self):
        yield self.Basis(N=32 * 2, R=15.0)

    def test_convolution(self, basis, exact_r):
        """Test the convolution."""
        exact = exact_r
        y = exact.y
        convolution = basis.convolve(y, y)
        assert np.allclose(convolution, exact.convolution)


class TestPeriodicBasis1:
    Basis = bases.PeriodicBasis
    Q = 8.0

    @pytest.fixture(params=[1, 2, 3])
    def dim(self, request):
        yield request.param

    # These values are carefully chosen to be close to the tolerance threshold
    @pytest.fixture(params=[32, 35])
    def basis(self, request, memoization_GB, dim):
        yield self.Basis(
            Nxyz=(request.param,) * dim,
            Lxyz=(18.5,) * dim,
            memoization_GB=memoization_GB,
        )

    @pytest.fixture
    def exact(self, basis, dim):
        return ExactGaussian(
            xyz=basis.xyz,
            Rs=np.linspace(1.02, 1.1, dim),
            A=self.Q / 8.0 / np.pi ** (3.0 / 2.0),
        )

    def test_interface(self, basis):
        assert verifyClass(IBasis, self.Basis)
        assert verifyObject(IBasis, basis)

    def test_laplacian(self, basis, exact, dim, threads):
        """Test the laplacian with a Gaussian."""
        factors_ = [None, np.linspace(0.8, 0.9, dim)]
        factor_ = [None, 1.0, (0.5 + 0.5j)]
        for exact.A in [(0.2 - 0.2j), exact.A]:
            for factor in factor_:
                for factors in factors_:
                    exact.factor = factor if factor is not None else 1.0
                    exact.factors = factors if factors is not None else [1] * dim
                    laplacian = functools.partial(
                        basis.laplacian, factor=factor, factors=factors
                    )
                    ddy = laplacian(exact.y)
                    assert np.allclose(ddy, exact.d2y, atol=2e-7)
                    if getattr(basis, "memoization_GB", 1) == 0:
                        with pytest.raises(NotImplementedError):
                            exp_ddy = laplacian(exact.y, exp=True)
                            assert np.allclose(exp_ddy, exact.exp_d2y, atol=2e-7)
                    else:
                        exp_ddy = laplacian(exact.y, exp=True)
                        assert np.allclose(exp_ddy, exact.exp_d2y, atol=2e-7)

    def test_laplacian_kx2(self, basis, exact, dim, threads):
        """Test the laplacian with a Gaussian using custom kx."""
        exact_factors = np.linspace(0.8, 0.9, dim)
        factors = np.linspace(0.8, 0.9, dim)
        kx2 = (factors[0] * basis.kx) ** 2
        factors[0] = 1.0
        factor_ = [None, 1.0, (0.5 + 0.5j)]
        for exact.A in [(0.2 - 0.2j), exact.A]:
            for factor in factor_:
                exact.factor = factor if factor is not None else 1.0
                exact.factors = exact_factors
                laplacian = functools.partial(
                    basis.laplacian, factor=factor, factors=factors, kx2=kx2
                )
                ddy = laplacian(exact.y)
                assert np.allclose(ddy, exact.d2y, atol=2e-7)
                try:
                    exp_ddy = laplacian(exact.y, exp=True)
                    assert np.allclose(exp_ddy, exact.exp_d2y, atol=2e-7)
                except NotImplementedError:
                    # Known error
                    assert basis.__class__ is bases.PeriodicBasis

    def test_gradient(self, basis, exact, dim):
        """Test the gradient"""
        factors = np.linspace(0.8, 0.9, dim)
        # Here we also test partial gradients selected by incomplete factors
        factors_ = [None] + [factors[: 1 + n] for n in range(len(factors))]
        for exact.A in [(0.2 + 0.2j), exact.A]:
            for factors in factors_:
                exact.factors = factors if factors is not None else [1] * dim
                get_gradient = functools.partial(basis.get_gradient, factors=factors)

                dy = get_gradient(exact.y)
                if any([dy is NotImplemented for dy in dy]):
                    pytest.skip("Gradient not implemented yet. (radial?)")

                dy_exact = exact.get_grad()

                assert np.allclose(dy, dy_exact, atol=1e-7)

                if factors is None or np.allclose(factors, 1):
                    dy = get_gradient(exact.y, kx=1.234 * basis._pxyz_derivative[0])
                    dy[0] /= 1.234
                    assert np.allclose(dy, dy_exact, atol=1e-7)
                else:
                    with pytest.raises(
                        ValueError,
                        match=r"Cannot set factors=.* with kw={'kx': (?s:.)*}. "
                        + r"You must include the factors yourself.",
                    ):
                        dy = get_gradient(exact.y, kx=1.234 * basis._pxyz_derivative[0])

    def test_grad_dot_grad(self, basis, exact, dim):
        """Test grad_dot_grad function."""
        factors_ = [None, np.linspace(0.8, 0.9, dim)]
        for factors in factors_:
            grad_dot_grad = functools.partial(basis.grad_dot_grad, factors=factors)
            exact.factors = factors if factors is not None else [1] * dim
            dydy = grad_dot_grad(exact.y, exact.y)
            # Lower atol since y^2 lies outside of the basis.
            assert np.allclose(dydy, exact.grad_dot_grad, atol=2e-5)


class TestCylindricalBasis2(TestPeriodicBasis1):
    Basis = bases.CylindricalBasis
    Q = 8.0

    @pytest.fixture
    def dim(self, request):
        yield 2

    # These values are carefully chosen to be close to the tolerance threshold
    @pytest.fixture(params=[32, 35])
    def basis(self, request):
        yield self.Basis(Nxr=(request.param, 32), Lxr=(18.5, 13.0))

    @pytest.fixture
    def exact(self, basis, dim):
        return ExactGaussianCyl(
            xr=basis.xr,
            # Rs=np.linspace(1.02, 1.1, dim),
            Rs=np.linspace(1.02, 1.1, dim),
            A=self.Q / 8.0 / np.pi ** (3.0 / 2.0),
        )


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

    Basis = bases.PeriodicBasis
    dim = 3
    Q = 8.0
    Mi = -1.747564594633182190636212

    @pytest.fixture
    def basis(self, memoization_GB):
        yield self.Basis(
            Nxyz=(32,) * self.dim,
            Lxyz=(25.0,) * self.dim,
            memoization_GB=memoization_GB,
        )

    @pytest.fixture
    def exact_r(self, basis):
        return ExactGaussianR(
            r=self.get_r(basis),
            d=self.dim,
            r_0=np.sqrt(2),
            A=self.Q / 8.0 / np.pi ** (3.0 / 2.0),
        )

    def test_interface(self, basis):
        super().test_interface(basis)
        assert verifyClass(IBasisKx, self.Basis)
        assert verifyObject(IBasisLz, basis)

    def test_coulomb(self, basis, exact_r):
        """Test computation of the coulomb potential.

        This is a stub: it just makes sure the code
        runs... unfortunately, computing the exact result to check is
        a bit tricky!
        """
        exact = exact_r
        y = [exact.y] * 2
        V = basis.convolve_coulomb(y)
        r = self.get_r(basis)
        V_exact = np.ma.divide(self.Q * sp.special.erf(r / 2), r).filled(
            self.Q / np.sqrt(np.pi)
        )
        if False:
            assert np.allclose(V[0], V_exact)
            assert np.allclose(V[1], V_exact)

    def test_coulomb_form_factors_stub(self, basis, exact_r):
        """Test computation of the coulomb potential with form-factors.
        This is just a stub - it does not do a non-trivial test, but checks
        to see that broadcasting works properly.
        """
        exact = exact_r

        def F1(k):
            return [1.0 + k**2, 2.0 + k**2]

        def F2(k):
            return [1.0 / (1.0 + k**2), 1.0 / (2.0 + k**2)]

        y = [exact.y] * 2
        V = basis.convolve_coulomb(y, form_factors=[F1, F2])
        V_no_ff = basis.convolve_coulomb(exact.y)
        assert np.allclose(V[0], V_no_ff)
        assert np.allclose(V[1], V_no_ff)

    def test_laplacian_quart(self, basis, exact_quart):
        """Test the laplacian with a Gaussian and modified dispersion."""
        # Real and Complex
        laplacian = basis.laplacian
        k2 = sum(_k**2 for _k in basis._pxyz)
        k4 = k2**2
        _k2 = k2 + k4
        exact = exact_quart
        for exact.factor in [(0.5 + 0.5j), exact.factor]:
            for exact.A in [(0.2 + 0.2j), exact.A]:
                ddy = laplacian(exact.y, factor=exact.factor, k2=_k2)
                assert np.allclose(ddy, exact.d2y, atol=1e-6)

                # exp_ddy = laplacian(exact.y, factor=exact.factor, exp=True)
                # assert np.allclose(exp_ddy, exact.exp_d2y)

    def test_gradient(self, basis, exact_r):
        """Test the gradient"""
        exact = exact_r
        get_gradient = basis.get_gradient
        xyz = basis.xyz
        for exact.A in [(0.2 + 0.2j), exact.A]:
            dy = get_gradient(exact.y)
            dy_exact = list(map(exact.get_dy, xyz))
            assert np.allclose(dy, dy_exact, atol=1e-7)

            dy = get_gradient(exact.y, kx=1.2 * basis.kx)
            dy[0] /= 1.2
            assert np.allclose(dy, dy_exact, atol=1e-7)

    def test_Lz(self, memoization_GB):
        """Test Lz"""
        N = 64
        L = 14.0
        b = bases.PeriodicBasis(Nxyz=(N, N), Lxyz=(L, L), memoization_GB=memoization_GB)
        x, y = b.xyz[:2]
        kx, ky = b._pxyz

        # Exact solutions for a Gaussian with phase
        f = (x + 1j * y) * np.exp(-(x**2) - y**2)
        nabla_f = (4 * (x**2 + y**2) - 8) * f
        Lz_f = f

        assert np.allclose(nabla_f, b.laplacian(f))
        assert np.allclose(Lz_f, b.apply_Lz_hbar(f))
        m = 1.1
        hbar = 2.2
        wz = 3.3
        kwz2 = m * wz / hbar
        factor = -(hbar**2) / 2 / m
        assert np.allclose(
            factor * nabla_f - wz * hbar * Lz_f,
            b.laplacian(f, factor=factor, kwz2=kwz2),
        )


class TestCartesianBasis(ConvolutionTests):
    dim = 3
    Q = 8.0
    Basis = bases.CartesianBasis

    @pytest.fixture
    def basis(self, memoization_GB):
        yield self.Basis(
            Nxyz=(32,) * self.dim,
            Lxyz=(25.0,) * self.dim,
            memoization_GB=memoization_GB,
        )

    def test_coulomb_exact(self, basis, exact_r):
        """Test computation of the coulomb potential."""
        exact = exact_r
        y = [exact.y] * 2  # Test that broadcasting works
        basis.fast_coulomb = False
        r = self.get_r(basis)
        V_exact = np.ma.divide(self.Q * sp.special.erf(r / 2), r).filled(
            self.Q / np.sqrt(np.pi)
        )
        for method in ["sum", "pad"]:
            V = basis.convolve_coulomb(y, method=method)
            assert np.allclose(V[0], V_exact)
            assert np.allclose(V[1], V_exact)

    test_coulomb = test_coulomb_exact

    def test_coulomb_fast(self, basis, exact_r):
        """Test fast computation of the coulomb potential."""
        exact = exact_r
        y = [exact.y] * 2  # Test that broadcasting works
        basis.fast_coulomb = True
        V_exact = np.ma.divide(self.Q * sp.special.erf(exact.r / 2), exact.r).filled(
            self.Q / np.sqrt(np.pi)
        )
        V = basis.convolve_coulomb(y)
        assert np.allclose(V[0], V_exact, rtol=0.052)
        assert np.allclose(V[1], V_exact, rtol=0.052)
        V = basis.convolve_coulomb_fast(y, correct=True)
        assert np.allclose(V[0], V_exact, rtol=0.052)
        assert np.allclose(V[1], V_exact, rtol=0.052)

    def test_coulomb_form_factors_stub(self, basis, exact_r):
        """Test computation of the coulomb potential with form-factors.
        This is just a stub - it does not do a non-trivial test, but checks
        to see that broadcasting works properly.
        """
        exact = exact_r
        basis.fast_coulomb = False

        def F1(k):
            return [1.0 + k**2, 2.0 + k**2]

        def F2(k):
            return [1.0 / (1.0 + k**2), 1.0 / (2.0 + k**2)]

        y = [exact.y] * 2
        V = basis.convolve_coulomb(y, form_factors=[F1, F2])
        V_exact = np.ma.divide(self.Q * sp.special.erf(exact.r / 2), exact.r).filled(
            self.Q / np.sqrt(np.pi)
        )
        assert np.allclose(V[0], V_exact)
        assert np.allclose(V[1], V_exact)

    def test_coulomb_fast_form_factors_stub(self, basis, exact_r):
        """Test computation of the coulomb potential with form-factors.
        This is just a stub - it does not do a non-trivial test, but checks
        to see that broadcasting works properly.
        """
        exact = exact_r
        basis.fast_coulomb = True

        def F1(k):
            return [1.0 + k**2, 2.0 + k**2]

        def F2(k):
            return [1.0 / (1.0 + k**2), 1.0 / (2.0 + k**2)]

        y = [exact.y] * 2
        V = basis.convolve_coulomb_fast(y, form_factors=[F1, F2])
        V_exact = np.ma.divide(self.Q * sp.special.erf(exact.r / 2), exact.r).filled(
            self.Q / np.sqrt(np.pi)
        )
        assert np.allclose(V[0], V_exact, rtol=0.052)
        assert np.allclose(V[1], V_exact, rtol=0.052)

    def test_laplacian_quart(self, basis, exact_quart):
        """Test the laplacian with a Gaussian and modified dispersion."""
        # Real and Complex
        laplacian = basis.laplacian
        k2 = sum(_k**2 for _k in basis._pxyz)
        k4 = k2**2
        _k2 = k2 + k4
        exact = exact_quart
        for exact.factor in [(0.5 + 0.5j), exact.factor]:
            for exact.A in [(0.2 - 0.2j), exact.A]:
                ddy = laplacian(exact.y, factor=exact.factor, k2=_k2)
                assert np.allclose(ddy, exact.d2y, atol=1e-6)

                # exp_ddy = laplacian(exact.y, factor=exact.factor, exp=True)
                # assert np.allclose(exp_ddy, exact.exp_d2y)

    def test_gradient(self, basis, exact_r):
        """Test the gradient"""
        exact = exact_r
        get_gradient = basis.get_gradient
        xyz = basis.xyz
        for exact.A in [(0.2 - 0.2j), exact.A]:
            dy = get_gradient(exact.y)
            dy_exact = list(map(exact.get_dy, xyz))
            assert np.allclose(dy, dy_exact, atol=1e-7)

            dy = get_gradient(exact.y, kx=1.2 * basis.kx)
            dy[0] /= 1.2
            assert np.allclose(dy, dy_exact, atol=1e-7)

    def test_memory(self, get_mem_MB):
        """Regression for issue #29: excessive memory usage."""
        # 4.0MB/complex state,
        Nxyz = (2**20,)  # 8.0MB per real array
        Nxyz = (2**9,) * 3  # 1GB for full state, but each array is small
        Nxyz = (2**10,) * 3  # 8GB for full state, but each array is small
        # Nxyz = (2 ** 11,) * 3  # 64GB for full state, but each array is small
        MB_per_array = np.prod(Nxyz) * 8 / 1024**2
        MB_per_slices = sum(_N * 8 for _N in Nxyz) / 1024**2
        get_mem_MB(reset=True)
        assert get_mem_MB() == 0
        basis = bases.CartesianBasis(Nxyz=Nxyz, Lxyz=(1.0,) * 3, memoization_GB=0)
        assert get_mem_MB() < MB_per_array

        # 3 slices for xyz, 3 slices for pxyz
        assert get_mem_MB() < 6 * MB_per_slices
        del basis
        assert get_mem_MB() < 1.0


class TestCylindricalBasis(LaplacianTests):
    Basis = bases.CylindricalBasis
    Q = 8.0
    Lxr = (25.0, 13.0)
    Nm = 5  # Number of functions to test
    Nn = 5  # Used when functions are compared

    # Enough points for trapezoid to give answers to 4 digits.
    R = np.linspace(0.0, Lxr[1] * 3.0, 10000)

    @pytest.fixture
    def basis(self):
        yield self.Basis(Nxr=(64, 32), Lxr=self.Lxr)

    @pytest.fixture
    def basis1(self):
        """Slightly different basis for interpolation."""
        yield self.Basis(Nxr=(64, 37), Lxr=self.Lxr)

    @pytest.fixture
    def exact_quart(self, basis):
        x, r = basis.xyz
        return ExactGaussianQuartCyl(
            x=x, r=r, r_0=np.sqrt(2), A=self.Q / 8.0 / np.pi ** (3.0 / 2.0)
        )

    @pytest.fixture
    def exact_r1(self, basis1):
        x, r = basis1.xyz
        return ExactGaussianR(
            r=self.get_r(basis1),
            d=3,
            r_0=np.sqrt(2),
            A=self.Q / 8.0 / np.pi ** (3.0 / 2.0),
        )

    def test_basis(self, basis):
        """Test orthonormality of basis functions."""
        b = basis
        x, r = b.xyz
        R = self.R
        for _m in range(self.Nm):
            Fm = b._F(_m, R)
            assert np.allclose(np.trapezoid(abs(Fm) ** 2, R), 1.0, rtol=1e-3)
            for _n in range(_m + 1, self.Nn):
                Fn = b._F(_n, R)
                assert np.allclose(np.trapezoid(Fm.conj() * Fn, R), 0.0, atol=1e-3)

    def test_derivatives(self, basis):
        """Test the derivatives of the basis functions."""
        b = basis
        x, r = b.xyz
        R = self.R + 0.1  # Derivatives are singular at origin
        for _m in range(self.Nm):
            F = b._F(_m, R)
            dF = b._F(_m, R, d=1)

            # Compute the derivative using FD half-way between the lattice
            # points.
            dF_fd = (F[1:] - F[:-1]) / np.diff(R)

            # Interpolate dFm to the same lattice midpoints
            dF = (dF[1:] + dF[:-1]) / 2.0

            assert np.allclose(dF, dF_fd, atol=1e-2)

    def test_laplacian_quart(self, basis, exact_quart):
        """Test the laplacian with a Gaussian and modified dispersion."""
        # Real and Complex
        laplacian = basis.laplacian
        kx2 = basis._kx2
        kx4 = kx2**2
        _kx2 = kx2 + kx4
        exact = exact_quart
        for exact.factor in [(0.5 + 0.5j), exact.factor]:
            for exact.A in [(0.2 - 0.2j), exact.A]:
                ddy = laplacian(exact.y, factor=exact.factor, kx2=_kx2)
                assert np.allclose(ddy, exact.d2y)

                # exp_ddy = laplacian(exact.y, factor=exact.factor, exp=True)
                # assert np.allclose(exp_ddy, exact.exp_d2y)

    def test_gradient(self, basis, exact_r):
        """Test the gradient"""
        exact = exact_r
        get_gradient = basis.get_gradient
        x, r = basis.xyz
        for exact.A in [(0.2 - 0.2j), exact.A]:
            dy = get_gradient(exact.y)[0]
            dy_exact = exact.get_dy(x)
            assert np.allclose(dy, dy_exact, atol=1e-7)

            dy = get_gradient(exact.y, kx=1.2 * basis.kx)[0]
            dy /= 1.2
            assert np.allclose(dy, dy_exact, atol=1e-7)

    def test_integrate1(self, basis, exact_r):
        exact = exact_r
        x, r = basis.xyz
        n = abs(exact.y) ** 2
        assert np.allclose((basis.metric * n).sum(), exact.N_3D)
        n_1D = basis.integrate1(n).ravel()
        r0 = exact.r_0
        n_1D_exact = exact.A**2 * (np.pi * r0**2 * np.exp(-(x**2) / r0**2)).ravel()
        assert np.allclose(n_1D, n_1D_exact)

    def test_integrate2(self, basis, exact_r):
        exact = exact_r
        x, r = basis.xyz
        n = abs(exact.y) ** 2
        assert np.allclose((basis.metric * n).sum(), exact.N_3D)
        y = np.linspace(1e-8, r.max(), 50)[None, :]
        n_2D = basis.integrate2(n, y=y)
        r0 = exact.r_0
        n_2D_exact = exact.A**2 * (np.sqrt(np.pi) * r0 * np.exp(-(x**2 + y**2) / r0**2))
        assert np.allclose(n_2D, n_2D_exact)

    def test_interpolation(self, basis, basis1, exact_r, exact_r1):
        """Test interpolation to a new basis.  Regression for issue #38."""
        exact, exact1 = exact_r, exact_r1
        x, r = basis.xyz
        x1, r1 = basis1.xyz

        n = abs(exact.y) ** 2
        n1 = abs(exact1.y) ** 2
        n1_interp = basis.Psi(np.sqrt(n), (x1, r1)) ** 2
        assert np.allclose(n1, n1_interp)


class TestCoverage:
    """Walk down some error branches for coverage."""

    # These values are carefully chosen to be close to the tolerance threshold
    @pytest.fixture
    def basis_p(self):
        yield bases.PeriodicBasis(Nxyz=(16,), Lxyz=(18.5,))

    @pytest.fixture
    def basis_c(self):
        yield

    def test_convolve_coulomb_exact(self, memoization_GB):
        dim = 1
        basis = bases.CartesianBasis(
            Nxyz=(32,) * dim,
            Lxyz=(25.0,) * dim,
            memoization_GB=memoization_GB,
        )
        exact = ExactGaussianR(r=abs(basis.xyz[0]), d=dim)
        with pytest.raises(NotImplementedError):
            basis.convolve_coulomb_exact(exact.y, method="unknown")

    def test_raise_twist_err(self, basis_p, basis_c):
        for Basis, kw in [
            (bases.PeriodicBasis, dict(Nxyz=(16,), Lxyz=(18.5,))),
            (bases.CylindricalBasis, dict(Nxr=(16, 8), Lxr=(18.5, 13.0))),
        ]:
            basis = Basis(**kw)
            for Error, arg, match in [
                (
                    NotImplementedError,
                    dict(twist=1),
                    "twist was removed in mmfutils==0.7.2: pass kx2 and kx instead",
                ),
                (
                    NotImplementedError,
                    dict(boost_px=1),
                    "boost_px* was removed in mmfutils==0.7.2: pass kx2 and kx instead",
                ),
                (
                    NotImplementedError,
                    dict(boost_pxyz=1),
                    "boost_px* was removed in mmfutils==0.7.2: pass kx2 and kx instead",
                ),
                (
                    TypeError,
                    dict(unknown=1),
                    "{}.{{name}}() got unexpected keyword argument(s) ['unknown']".format(
                        Basis.__name__
                    ),
                ),
            ]:
                with pytest.raises(
                    Error, match=re.escape(match.format(name="__init__"))
                ):
                    Basis(**arg, **kw)

                with pytest.raises(
                    Error, match=re.escape(match.format(name="laplacian"))
                ):
                    basis.laplacian(y=None, **arg)

                with pytest.raises(
                    Error, match=re.escape(match.format(name="get_gradient"))
                ):
                    basis.get_gradient(y=None, **arg)

                if hasattr(basis, "apply_exp_K"):
                    with pytest.raises(
                        Error, match=re.escape(match.format(name="apply_exp_K"))
                    ):
                        basis.apply_exp_K(y=None, factor=1, **arg)

                if hasattr(basis, "apply_K"):
                    with pytest.raises(
                        Error, match=re.escape(match.format(name="apply_K"))
                    ):
                        basis.apply_K(y=None, **arg)
