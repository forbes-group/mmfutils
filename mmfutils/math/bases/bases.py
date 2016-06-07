from __future__ import absolute_import, division

import itertools
import math

import numpy as np
import scipy.fftpack

from mmfutils.containers import Object

from .interface import implements, IBasis, IBasisWithConvolution, BasisMixin
from .utils import (prod, dst, idst, fft, ifft, fftn, ifftn, resample,
                    get_xyz, get_kxyz)
from mmfutils.math import bessel

sp = scipy

_TINY = np.finfo(float).tiny

__all__ = ['SphericalBasis', 'PeriodicBasis', 'CartesianBasis']


class SphericalBasis(Object, BasisMixin):
    """1-dimensional basis for radial problems.

    We represent exactly `N` positive abscissa, excluding the origin and use
    the discrete sine transform.  We represent the square-root of the
    wavefunctions here so that a factor of `r` is required to convert these
    into the radial functions.  Unlike the DVR techniques, this approach allows
    us to compute the Coulomb interaction for example.
    """
    implements(IBasisWithConvolution)

    def __init__(self, N, R):
        self.N = N
        self.R = R
        Object.__init__(self)

    def init(self):
        dx = self.R/self.N
        r = np.arange(1, self.N+1) * dx
        k = np.pi * (0.5 + np.arange(self.N)) / self.R
        self.xyz = [r]
        self._pxyz = [k]
        self.metric = 4*np.pi * r**2 * dx
        self.k_max = k.max()

    def laplacian(self, y, factor=1.0, exp=False):
        """Return the laplacian of `y` times `factor` or the
        exponential of this.

        Arguments
        ---------
        factor : float
           Additional factor (mostly used with `exp=True`).  The
           implementation must be careful to allow the factor to
           broadcast across the components.
        exp : bool
           If `True`, then compute the exponential of the laplacian.
           This is used for split evolvers.
        """
        r = self.xyz[0]
        K = -factor * self._pxyz[0]**2
        if exp:
            K = np.exp(K)

        ys = [y.real, y.imag] if np.iscomplexobj(y) else [y]
        res = [idst(K * dst(r*_y))/r for _y in ys]

        if np.iscomplexobj(y):
            res = res[0] + 1j*res[1]
        else:
            res = res[0]

        return res

    def coulomb_kernel(self, k):
        """Form for the truncated Coulomb kernel."""
        D = 2*self.R
        return 4*np.pi * np.ma.divide(1.0 - np.cos(k*D), k**2).filled(D**2/2.0)

    def convolve_coulomb(self, y, form_factors=[]):
        """Modified Coulomb convolution to include form-factors (if provided).

        This version implemented a 3D spherically symmetric convolution.
        """
        y = np.asarray(y)
        r = self.xyz[0]
        N, R = self.N, self.R

        # Padded arrays with trailing _
        ry_ = np.concatenate([r*y, np.zeros(y.shape, dtype=y.dtype)], axis=-1)
        k_ = np.pi * (0.5 + np.arange(2*N)) / (2*R)
        K = prod([_K(k_) for _K in [self.coulomb_kernel] + form_factors])
        return idst(K * dst(ry_))[..., :N] / r

    def convolve(self, y, C=None, Ck=None):
        """Return the periodic convolution `int(C(x-r)*y(r),r)`.

        Note: this is the 3D convolution.
        """
        r = self.xyz[0]
        k = self._pxyz[0]
        if Ck is None:
            C0 = (self.metric * C).sum()
            Ck = np.ma.divide(2*np.pi * dst(r*C), k).filled(C0)
        else:
            Ck = Ck(k)
        return idst(Ck * dst(r*y)) / r


class PeriodicBasis(Object, BasisMixin):
    """dim-dimensional periodic bases.

    Parameters
    ----------
    Nxyz : (Nx, Ny, ...)
       Number of lattice points in basis.
    Lxyz : (Lx, Ly, ...)
       Size of each dimension (length of box and radius)
    symmetric_lattice: bool
       If True, then shift the lattice so that it is symmetric about
       the origin.  The default is to ensure that there is a lattice
       point at the origin which will make the lattice asymmetric for
       even Nxyz.
    axes : (int, int, ...)
       Axes in array y which correspond to the x, y, ... axes here.
       This is required for cases where y has additional dimensions.
       The default is the last dim axes (best for performance).
    boost_pxyz : float
       Momentum of moving frame.  Momenta are shifted by this, which
       corresponds to working in a boosted frame with velocity `vx = px/m`.
    """
    implements(IBasisWithConvolution)

    def __init__(self, Nxyz, Lxyz, symmetric_lattice=False,
                 axes=None, boost_pxyz=None):
        self.symmetric_lattice = symmetric_lattice
        self.Nxyz = np.asarray(Nxyz)
        self.Lxyz = np.asarray(Lxyz)
        if boost_pxyz is None:
            boost_pxyz = np.zeros_like(self.Lxyz)
        self.boost_pxyz = np.asarray(boost_pxyz)
        if axes is None:
            axes = np.arange(-self.dim, 0)
        self.axes = np.asarray(axes)
        Object.__init__(self)

    def init(self):
        self.xyz = get_xyz(Nxyz=self.Nxyz, Lxyz=self.Lxyz,
                           symmetric_lattice=self.symmetric_lattice)
        self._pxyz = get_kxyz(Nxyz=self.Nxyz, Lxyz=self.Lxyz)

        # Add boosts
        self._pxyz = [_p - _b
                      for (_p, _b) in zip(self._pxyz, self.boost_pxyz)]
        self.metric = np.prod(self.Lxyz/self.Nxyz)
        self.k_max = np.array([abs(_p).max() for _p in self._pxyz])

    def laplacian(self, y, factor=1.0, exp=False,
                  _k2=None):
        """Return the laplacian of `y` times `factor` or the exponential of this.

        Arguments
        ---------
        factor : float
           Additional factor (mostly used with `exp=True`).  The
           implementation must be careful to allow the factor to
           broadcast across the components.
        exp : bool
           If `True`, then compute the exponential of the laplacian.
           This is used for split evolvers.
        _k2 : array, optional
           If provided then this will be used in place of the sum of
           the squares of the wavevectors.  This would allow you, for
           example, to implement a modified dispersion relationship
           like ``1-cos(k)`` rather than ``k**2``.  It is not a
           standard part of the interface since it cannot be easily
           implement for arbitrary bases
        """
        if _k2 is None:
            _k2 = sum(_p**2 for _p in self._pxyz)
        K = -factor * _k2
        if exp:
            K = np.exp(K)
        return self.ifftn(K * self.fftn(y))

    # We need these wrappers because the state may have additional
    # indices for components etc. in front.
    def fft(self, x, axis):
        """Perform the fft along self.axes[axis]"""
        axis = self.axes[axis] % len(x.shape)
        return fft(x, axis=axis)

    def ifft(self, x, axis):
        """Perform the ifft along self.axes[axis]"""
        axis = self.axes[axis] % len(x.shape)
        return ifft(x, axis=axis)

    def fftn(self, x):
        """Perform the fft along spatial axes"""
        axes = self.axes % len(x.shape)
        return fftn(x, axes=axes)

    def ifftn(self, x):
        """Perform the ifft along spatial axes"""
        axes = self.axes % len(x.shape)
        return ifftn(x, axes=axes)

    def get_gradient(self, y):
        # TODO: Check this for the highest momentum issue.
        return [self.ifft(1j*_p*self.fft(y, axis=_i), axis=_i)
                for _i, _p in enumerate(self._pxyz)]

    @staticmethod
    def _bcast(n, N):
        """Use this to broadcast a 1D array along the n'th of N dimensions"""
        inds = [None]*N
        inds[n] = slice(None)
        return inds

    def coulomb_kernel(self, k):
        """Form for the Coulomb kernel.

        The normalization here is that the k=0 component is set to
        zero.  This means that the charge distribution has an overall
        constant background removed so that the net charge in the unit
        cell is zero.
        """
        return 4*np.pi * np.ma.divide(1.0, k**2).filled(0.0)

    def convolve_coulomb(self, y, form_factors=[]):
        """Periodic convolution with the Coulomb kernel."""
        y = np.asarray(y)

        # This broadcasts to the appropriate size if there are
        # multiple components.
        # dim = len(np.asarray(self.Lxyz))
        # N = np.asarray(y.shape)
        # b_cast = [None] * (dim - len(N)) + [slice(None)]*dim

        k = np.sqrt(sum(_k**2 for _k in self._pxyz))
        Ck = prod([_K(k) for _K in [self.coulomb_kernel] + form_factors])
        return self.ifftn(Ck * self.fftn(y))

    def convolve(self, y, C=None, Ck=None):
        """Return the periodic convolution `int(C(x-r)*y(r),r)`.

        Arguments
        ---------
        y : array
           Usually the density, but can be any array
        C : array
           Convolution kernel. The convolution will be performed using the FFT.
        Ck : function (optional)
           If provided, then this function will be used instead directly in
           momentum space.  Assumed to be spherically symmetric (will be passed
           only the magnitude `k`)
        """
        if Ck is None:
            Ck = self.fftn(C)
        else:
            k = np.sqrt(sum(_k**2 for _k in self._pxyz))
            Ck = Ck(k)
        return self.ifftn(Ck * self.fftn(y))

    @property
    def dim(self):
        return len(self.Nxyz)


class CartesianBasis(PeriodicBasis):
    """N-dimensional periodic bases but with Coulomb convolution that does not
    use periodic images.  Use this for nuclei in free space.

    Parameters
    ----------
    Nxyz : (Nx, Ny, ...)
       Number of lattice points in basis.
    Lxyz : (Lx, Ly, ...)
       Size of each dimension (length of box and radius)
    symmetric_lattice: bool
       If True, then shift the lattice so that it is symmetric about
       the origin.  The default is to ensure that there is a lattice
       point at the origin which will make the lattice asymmetric for
       even Nxyz.
    axes : (int, int, ...)
       Axes in array y which correspond to the x, y, ... axes here.
       This is required for cases where y has additional dimensions.
       The default is the last dim axes (best for performance).
    fast_coulomb : bool
       If `True`, use the fast Coulomb algorithm which is slightly less
       accurate but much faster.
    """
    implements(IBasisWithConvolution)

    def __init__(self, Nxyz, Lxyz, axes=None,
                 symmetric_lattice=False, fast_coulomb=True):
        self.fast_coulomb = fast_coulomb
        PeriodicBasis.__init__(self, Nxyz=Nxyz, Lxyz=Lxyz, axes=axes,
                               symmetric_lattice=symmetric_lattice)

    def convolve_coulomb_fast(self, y, form_factors=[], correct=False):
        """Return the approximate convolution `int(C(x-r)*y(r),r)` where

        .. math::
           C(r) = 1/r

        is the Coulomb potential (without charges etc.)

        Arguments
        ---------
        y : array
           Usually the density, but can be any array
        correct : bool
           If `True`, then include the high frequency components via the
           periodic convolution.

        Notes
        -----
        This version uses the Truncated Kernel Expansion method which uses the
        Truncated Kernel

        .. math::
           4\pi(1-\cos\sqrt{3}Lk)/k^2

        on a padded array to remove the images, approximating the linear
        convolution without the highest frequency modes.  By choosing the
        smaller lattice to be at least 3 times smaller we can guarantee that
        the padded array will fit into memory.  This can be augmented by the
        periodic convolution to fill in the higher modes.

        There are two sources of error here:

        * We presently use the same periodic ``resample`` method to interpolate
          the linear convolution to the larger grid.  This assumes that the
          function is periodic -- which it is not -- and can introduce some
          aliasing artifacts.  Some preliminary experimentation shows, however,
          that these are generally small.  Perhaps cubic spline interpolation
          could be used to improve the interpolation, but this is not clear
          yet.
        * The contribution from the higher modes are computed from the periodic
          convolution which could in principle be contaminated by images.
          However, for smooth functions, there should be little amplitude here,
          and it should consist only of higher multipoles, so the contamination
          should be small.
        """
        y = np.asarray(y)
        L = np.asarray(self.Lxyz)
        dim = len(L)
        N = np.asarray(y.shape)
        N0 = N.copy()
        N0[-dim:] = N[-dim:]//3

        y0 = resample(y, N0)
        V = resample(self.convolve_coulomb_exact(
            y0, form_factors=form_factors, method='pad'), N)
        if correct:
            k = np.sqrt(sum(_K**2 for _K in self._pxyz))
            C = 4*np.pi * np.ma.divide(1.0, k**2).filled(0.0)
            for F in form_factors:
                C = C * F(k)
            dV = self.ifftn(C * self.fftn(y - resample(y0, N)))
            if np.issubdtype(V.dtype, complex):
                V += dV
            else:
                assert np.allclose(0, V.imag)
                V += dV.real
        return V

    def convolve_coulomb_exact(self, y, form_factors=[], method='sum'):
        """Return the convolution `int(C(x-r)*y(r),r)` where

        .. math::
           C(r) = 1/r

        is the Coulomb potential (without charges etc.)

        Arguments
        ---------
        y : array
           Usually the density, but can be any array
        method : 'sum', 'pad'
           Either zero-pad the array (takes extra memory but can use multiple
           cores) or sum over the 27 small transforms (slow).

        This function is designed for computing the Coulomb potential of a
        charge distribution.  In this case, one would have the kernel:

        .. math::
           4\pi/k^2

        or in the case of non-periodic convolution to remove the images

        .. math::
           4\pi(1-\cos\sqrt{3}Lk)/k^2
        """
        y = np.asarray(y)
        L = np.asarray(self.Lxyz)
        dim = len(L)
        D = np.sqrt((L**2).sum())  # Diameter of cell

        def C(k):
            C = 4*np.pi * np.ma.divide(1 - np.cos(D*k), k**2).filled(D**2/2.)
            for F in form_factors:
                C = C * F(k)
            return C

        if method == 'sum':
            # Sum with a loop.  Minimizes the memory usage, but will not
            # use multiple cores.
            K = self._pxyz
            X = self.xyz
            V = np.zeros(y.shape, dtype=y.dtype)
            for l in itertools.product(np.arange(3), repeat=dim):
                delta = [2*np.pi * _l/3.0/_L for _l, _L in zip(l, L)]
                exp_delta = np.exp(1j*sum(_d*_x for _x, _d in zip(X, delta)))
                y_delta = (exp_delta.conj() * y)
                k = np.sqrt(sum((_k + _d)**2 for _k, _d in zip(K, delta)))
                dV = (exp_delta * self.ifftn(C(k) * self.fftn(y_delta)))
                if np.issubdtype(V.dtype, complex):
                    V += dV
                else:
                    assert np.allclose(0, V.imag)
                    V += dV.real
            return V/dim**3
        elif method == 'pad':
            N = np.asarray(y.shape[-dim:])
            N_padded = 3*N
            L_padded = 3*L
            shape = np.asarray(y.shape)
            shape_padded = shape.copy()
            shape_padded[-dim:] = N_padded
            y_padded = np.zeros(shape_padded, dtype=y.dtype)
            inds = [slice(0, _N) for _N in shape]
            y_padded[inds] = y
            k = np.sqrt(
                sum(_K**2 for _K in get_kxyz(N_padded, L_padded)))

            # This broadcasts to the appropriate size
            b_cast = [None] * (dim - len(N)) + [slice(None)]*dim
            return self.ifftn(C(k)[b_cast] * self.fftn(y_padded))[inds]
        else:
            raise NotImplementedError(
                "method=%s not implemented: use 'sum' or 'pad'" % (method,))

    def convolve_coulomb(self, y, form_factors=[], **kw):
        if self.fast_coulomb:
            return self.convolve_coulomb_fast(
                y, form_factors=form_factors, **kw)
        else:
            return self.convolve_coulomb_exact(
                y, form_factors=form_factors, **kw)


class CylindricalBasis(Object, BasisMixin):
    r"""2D basis for Cylindrical coordinates via a DVR basis.

    This represents 3-dimensional problems with axial symmetry, but only has
    two dimensions (x, r).

    Parameters
    ----------
    Nxr : (Nx, Nr)
       Number of lattice points in basis.
    Lxr : (L, R)
       Size of each dimension (length of box and radius)
    twist : float
       Twist (angle) in periodic dimension.  This adds a constant offset to the
       momenta allowing one to study Bloch waves.
    boost_px : float
       Momentum of moving frame (along the x axis).  Momenta are shifted by
       this, which corresponds to working in a boosted frame with velocity
       `vx = boost_px/m`.
    axes : (int, int)
       Axes in array y which correspond to the x and r axes here.
       This is required for cases where y has additional dimensions.
       The default is the last two axes (best for performance).
    """
    implements(IBasis)

    def __init__(self, Nxr, Lxr, twist=0, boost_px=0,
                 axes=(-2, -1), symmetric_x=True):
        self.twist = twist
        self.boost_px = np.asarray(boost_px)
        self.Nxr = np.asarray(Nxr)
        self.Lxr = np.asarray(Lxr)
        self.symmetric_x = symmetric_x
        self.axes = np.asarray(axes)
        Object.__init__(self)

    def init(self):
        Lx, R = self.Lxr
        x = get_xyz(Nxyz=self.Nxr, Lxyz=self.Lxr,
                    symmetric_lattice=self.symmetric_x)[0]
        kx0 = get_kxyz(Nxyz=self.Nxr, Lxyz=self.Lxr)[0]
        kx = (kx0 + float(self.twist) / Lx - self.boost_px)
        self._kx0 = kx0
        self._kx = kx
        self._kx2 = kx**2

        self.y_twist = np.exp(1j*self.twist*x/Lx)

        Nx, Nr = self.Nxr

        # For large n, the roots of the bessel function are approximately
        # z[n] = (n + 0.75)*pi, so R = r_max = z_max/k_max = (N-0.25)*pi/kmax
        # This self._kmax defines the DVR basis, not self.k_max
        self._kmax = (Nr - 0.25)*np.pi/R

        # This is just the maximum momentum for diagnostics,
        # determining cutoffs etc.
        self.k_max = np.array([abs(kx).max(), self._kmax])

        nr = np.arange(Nr)[None, :]
        r = self._r(Nr)[None, :]  # Do this after setting _kmax
        self.xyz = [x, r]

        _lambda = np.asarray(
            [1./(self._F(_nr, _r))**2
             for _nr, _r in zip(nr.ravel(), r.ravel())])[None, :]
        self.metric = 2*np.pi * r * _lambda * (Lx / Nx)
        self.metric.setflags(write=False)
        # Get the DVR kinetic piece for radial component
        K, r1, r2, w = self._get_K()

        # We did not apply the sqrt(r) factors so at this point, K is still
        # Hermitian and we can diagonalize for later exponentiation.
        d, V = sp.linalg.eigh(K)     # K = np.dot(V*d, V.T)

        # Here we convert from the wavefunction Psi(r) to the radial
        # function u(r) = sqrt(r)*Psi(r) and back with factors of sqrt(r).
        K *= r1
        K *= r2

        self.weights = w
        self._Kr = K
        self._Kr_diag = (r1, r2, V, d)   # For use when exponentiating

        # And factor for x.
        self._Kx = self._kx2

        # Cache for K_data from apply_exp_K.
        self._K_data = []

    def laplacian(self, y, factor=1.0, exp=False,
                  _kx2=None):
        r"""Return the laplacian of y.

        Arguments
        ---------
        factor : float
           Additional factor (mostly used with `exp=True`).  The
           implementation must be careful to allow the factor to
           broadcast across the components.
        exp : bool
           If `True`, then compute the exponential of the laplacian.
           This is used for split evolvers.
        _kx2 : array, optional
           If provided then this will be used in place of kx**2.  This
           would allow you, for example, to implement a modified
           dispersion relationship along the ``x`` direction
           like ``1-cos(kx)`` rather than ``kx**2``.  It is not a
           standard part of the interface since it cannot be easily
           implement for arbitrary bases
        """
        if not exp:
            return self.apply_K(y=y, _kx2=_kx2) * (-factor)
        else:
            return self.apply_exp_K(y=y, factor=-factor, _kx2=_kx2)

    def get_gradient(self, y):
        """Returns the gradient along the x axis."""
        kx = self._kx
        return [self.ifft(1j*kx*self.fft(y)), NotImplemented]

    def apply_Lz(self, y, hermitian=False):
        raise NotImplementedError

    def apply_Px(self, y, hermitian=False):
        r"""Apply the Pz operator to y without any px.

        Requires :attr:`_pxyz` to be defined.
        """
        return self.y_twist * self.ifft(self._kx0 * self.fft(y/self.y_twist))

    def apply_exp_K(self, y, factor, _kx2=None):
        r"""Return `exp(K*factor)*y` or return precomputed data if
        `K_data` is `None`.
        """
        if _kx2 is None:
            _kx2 = self._Kx
        _K_data_max_len = 3
        ind = None
        for _i, (_f, _d) in enumerate(self._K_data):
            if np.allclose(factor, _f):
                ind = _i
        if ind is None:
            _r1, _r2, V, d = self._Kr_diag
            exp_K_r = _r1 * np.dot(V*np.exp(factor * d), V.T) * _r2
            exp_K_x = np.exp(factor * _kx2)
            K_data = (exp_K_r, exp_K_x)
            self._K_data.append((factor, K_data))
            ind = -1
            while len(self._K_data) > _K_data_max_len:
                # Reduce storage
                self._K_data.pop(0)

        K_data = self._K_data[ind][1]
        exp_K_r, exp_K_x = K_data
        if self.twist == 0:
            tmp = self.ifft(exp_K_x * self.fft(y))
        else:
            tmp = self.y_twist*self.ifft(exp_K_x * self.fft(y/self.y_twist))
        return np.einsum('...ij,...yj->...yi', exp_K_r, tmp)

    def apply_K(self, y, _kx2=None):
        r"""Return `K*y` where `K = k**2/2`"""
        # Here is how the indices work:
        if _kx2 is None:
            _kx2 = self._Kx

        if self.twist == 0:
            yt = self.fft(y)
            yt *= _kx2
            yt = self.ifft(yt)
        else:
            yt = self.fft(y/self.y_twist)
            yt *= _kx2
            yt = self.ifft(yt)
            yt *= self.y_twist

        # C <- alpha*B*A + beta*C    A = A^T  zSYMM or zHYMM but not supported
        # maybe cvxopt.blas?  Actually, A is not symmetric... so be careful!
        yt += np.dot(y, self._Kr.T)
        return yt

    ######################################################################
    # FFT and DVR Helper functions.
    #
    # These are specific to the basis, defining the kinetic energy
    # matrix for example.

    # We need these wrappers because the state may have additional
    # indices for components etc. in front.
    def fft(self, x):
        """Perform the fft along the x axes"""
        # Makes sure that
        axis = (self.axes % len(x.shape))[0]
        return fft(x, axis=axis)

    def ifft(self, x):
        """Perform the fft along the x axes"""
        axis = (self.axes % len(x.shape))[0]
        return ifft(x, axis=axis)

    def _get_K(self):
        r"""Return `(K, r1, r2, w)`: the DVR kinetic term for the radial function
        and the appropriate factors for converting to the radial coordinates.

        This term effects the $-d^2/dr^2 - (\nu^2 - 1/4)/r^2$ term.

        Returns
        -------
        K : array
           Operates on radial wavefunctions
        r1, r2 : array
           K*r1*r2 operators on the full wavefunction (but is no longer
           Hermitian)
        w : array
           Quadrature integration weights.
        """
        nu = 0.0
        r = self.xyz[1].ravel()
        z = self._kmax * r
        n = np.arange(len(z))
        i1 = (slice(None), None)
        i2 = (None, slice(None))

        # Quadrature weights
        w = 2.0 / (self._kmax * z * bessel.J(nu=nu, d=1)(z)**2)

        # DVR kinetic term for radial function:
        K = np.ma.divide(
            (-1)**(n[i1] - n[i2]) * 8.0 * z[i1] * z[i2],
            (z[i1]**2 - z[i2]**2)**2).filled(0)
        K[n, n] = 1.0 / 3.0 * (1.0 + 2.0*(nu**2 - 1.0)/z**2)
        K *= self._kmax**2

        # Here we convert from the wavefunction Psi(r) to the radial
        # function u(r) = sqrt(r)*Psi(r) and back with factors of
        # sqrt(wr).  This includes the integration weights (since K is
        # defined acting on the basis functions).
        # Note: this makes the matrix non-hermitian, so don't do this if you
        # want to diagonalize.
        _tmp = np.sqrt(w*r)
        r2 = _tmp[i2]
        r1 = 1./_tmp[i1]

        return K, r1, r2, w

    def _r(self, N):
        r"""Return the abscissa."""
        nu = 0.0                # l=0 cylindrical: nu = l + d/2 - 1
        return bessel.j_root(nu=nu, N=N) / self._kmax

    def _F(self, n, r, d=0):
        r"""Return the dth derivative of the n'th basis function."""
        nu = 0.0                # l=0 cylindrical: nu = l + d/2 - 1
        rn = self.xyz[1].ravel()[n]
        zn = self._kmax*rn
        z = self._kmax*r
        H = bessel.J_sqrt_pole(nu=nu, zn=zn, d=0)
        coeff = math.sqrt(2.0*self._kmax)*(-1)**(n + 1)/(1.0 + r/rn)
        if 0 == d:
            return coeff * H(z)
        elif 1 == d:
            dH = bessel.J_sqrt_pole(nu=nu, zn=zn, d=1)
            return coeff * (dH(z) - H(z)/(z + zn)) * self._kmax
        else:
            raise NotImplementedError

    def get_F(self, r):
        """Return a function that can extrapolate a radial
        wavefunction to a new set of abscissa (x, r)."""
        x, r0 = self.xyz
        n = np.arange(r0.size)[:, None]

        # Here is the transform matrix
        _F = self._F(n, r) / self._F(n, r0.T)

        def F(u):
            return np.dot(u, _F)

        return F

    def F(self, u, xr):
        r"""Return u evaluated on the new abscissa (Assumes x does not
        change for now)"""
        x0, r0 = self.xyz
        x, r = xr
        assert np.allclose(x, x0)

        return self.get_F(r)(u)

    def get_Psi(self, r, return_matrix=False):
        """Return a function that can extrapolate a wavefunction to a
        new set of abscissa (x, r).

        This includes the factor of $\sqrt{r}$ that converts the
        wavefunction to the radial function, then uses the basis the
        extrapolate the radial function.

        Arguments
        ---------
        r : array
           The new abscissa in the radial direction (the $x$ values
           stay the same.)
        return_matrix : bool
           If True, then return the extrapolation matrix Fso that
           ``Psi = np.dot(psi, F)``
        """
        x, r0 = self.xyz
        n = np.arange(r0.size)[:, None]

        # Here is the transform matrix
        _F = (np.sqrt(r) * self._F(n, r)) / (np.sqrt(r0.T) * self._F(n, r0.T))

        if return_matrix:
            return _F

        def Psi(psi):
            return np.dot(psi, _F)

        return Psi

    def Psi(self, psi, xr):
        r"""Return psi evaluated on the new abscissa (Assumes x does not
        change for now)"""
        x0, r0 = self.xyz
        x, r = xr
        assert np.allclose(x, x0)

        return self.get_Psi(r)(psi)
