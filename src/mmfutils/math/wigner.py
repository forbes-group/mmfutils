"""Wigner Ville distribution.

This module contains some FFT-based routines for computing the
Wigner-Ville distribution.
"""
import numpy as np

from mmfutils.performance.fft import fft, ifft


def wigner_ville(psi, dt=1, make_analytic=False, skip=1, pad=True):
    """Return `(ws, P)` where `P` is the Wigner Ville quasi-distribution for psi.

    Assumes that psi is periodic.  Note: the frequencies at which `P`
    is valid are half the frequencies normally associated with the
    wavefunction.  Thus we also return the associated frequencies to
    avoid possible confusion.

    Arguments
    ---------
    psi : array-like
       The input signal.
    dt : float
       Step size for the input abscissa.
    make_analytic : bool
       If True, then negative frequency components are set to zero.
    skip : int
       Downsample the time-domain by skipping this many points.
    pad : bool
       If True, then pad the input array to remove aliasing artifacts.
    """

    N = len(psi)
    ws = np.pi * np.fft.fftfreq(N, dt)  # Note missing factor of 2
    if make_analytic:
        # Make signal analytic
        # See https://en.wikipedia.org/wiki/Analytic_signal
        psi = ifft((np.sign(ws) + 1) * fft(psi))

    if pad:
        psi = np.hstack([psi, np.zeros_like(psi)])
        Npad = N * 2
    else:
        Npad = N

    i = np.arange(0, N, skip)[:, None]
    j = np.arange(N)[None, :]
    i_ = (i + j) % Npad
    j_ = (i - j) % Npad
    Psi = psi[i_] * psi[j_].conj()
    P = 2 * fft(Psi, axis=-1).real[:N, :] * dt
    P = np.fft.fftshift(P, axes=-1)
    ws = np.fft.fftshift(ws)
    return ws, P * dt
