"""Sky brightness models and their visibilities (van Cittert-Zernike theorem).

Sign convention: V(u, v) = sum_k I_k exp(-2*pi*i (u l_k + v m_k)), consistent
with :func:`interfsim.geometry.antenna_phase` and :func:`interfsim.imaging.make_dirty_image`.
"""
from __future__ import annotations

import numpy as np
from scipy.special import j1


def vis_point_sources(u, v, sources) -> np.ndarray:
    """sources: iterable of (flux, l_rad, m_rad)."""
    V = np.zeros(np.shape(u), dtype=np.complex128)
    for flux, l0, m0 in sources:
        V += flux * np.exp(-2j * np.pi * (u * l0 + v * m0))
    return V


def vis_uniform_disk(u, v, flux, diameter_rad, l0=0.0, m0=0.0) -> np.ndarray:
    """Uniform disk of angular diameter theta_d: V = flux * 2 J1(x)/x, x = pi theta_d q."""
    q = np.hypot(u, v)
    x = np.pi * diameter_rad * q
    safe = np.where(x < 1e-9, 1.0, x)
    jinc = np.where(x < 1e-9, 1.0, 2.0 * j1(safe) / safe)
    return flux * jinc * np.exp(-2j * np.pi * (u * l0 + v * m0))


def vis_gaussian(u, v, flux, fwhm_rad, l0=0.0, m0=0.0) -> np.ndarray:
    """Circular Gaussian of given FWHM."""
    q2 = u ** 2 + v ** 2
    return flux * np.exp(-(np.pi * fwhm_rad) ** 2 * q2 / (4 * np.log(2))) \
        * np.exp(-2j * np.pi * (u * l0 + v * m0))


def disk_components(diameter_rad: float, n_across: int = 15,
                    l0: float = 0.0, m0: float = 0.0) -> np.ndarray:
    """Discretise a uniform disk into equal-flux point components on a square grid.

    Returns an array (K, 3) of (flux_fraction, l, m) summing to 1. Used by the
    voltage-level engine, which needs explicit, mutually incoherent emitters.
    The grid step must stay well below 1/q_max for the jinc to be reproduced.
    """
    r = diameter_rad / 2.0
    g = (np.arange(n_across) - (n_across - 1) / 2) * (diameter_rad / n_across)
    L, M = np.meshgrid(g, g)
    keep = L ** 2 + M ** 2 <= r ** 2
    L, M = L[keep], M[keep]
    frac = np.full(L.size, 1.0 / L.size)
    return np.column_stack([frac, L + l0, M + m0])


def sky_visibilities(sky: dict, u, v) -> np.ndarray:
    """Visibilities for a sky dict:
    {"type": "point", "sources": [(flux, l, m), ...]}
    {"type": "disk", "flux": 1, "diameter_rad": ..., "l0": 0, "m0": 0}
    {"type": "gaussian", "flux": 1, "fwhm_rad": ..., "l0": 0, "m0": 0}"""
    kind = sky["type"]
    if kind == "point":
        return vis_point_sources(u, v, sky["sources"])
    if kind == "disk":
        return vis_uniform_disk(u, v, sky.get("flux", 1.0), sky["diameter_rad"],
                                sky.get("l0", 0.0), sky.get("m0", 0.0))
    if kind == "gaussian":
        return vis_gaussian(u, v, sky.get("flux", 1.0), sky["fwhm_rad"],
                            sky.get("l0", 0.0), sky.get("m0", 0.0))
    raise ValueError(f"unknown sky type: {kind!r}")
