"""Image and array quality metrics."""
from __future__ import annotations

import numpy as np


def fwhm_main_lobe(profile: np.ndarray, axis: np.ndarray) -> float:
    """Full width at half maximum of the lobe containing the peak.

    Walks outwards from the peak to the first half-power crossing on each side
    and interpolates linearly. Unlike "all samples above 0.5", sidelobes or
    grating lobes above half power do not inflate the width. Returns nan when
    the lobe does not drop to half power inside the axis (unresolved direction).
    """
    p = np.asarray(profile, float)
    k = int(np.argmax(p))
    half = p[k] / 2.0

    def crossing(step):
        i = k
        while 0 <= i + step < p.size:
            if p[i + step] < half:
                j = i + step
                return axis[i] + (half - p[i]) * (axis[j] - axis[i]) / (p[j] - p[i])
            i += step
        return np.nan

    return float(crossing(+1) - crossing(-1))


def center_cuts(image: np.ndarray, l_axis: np.ndarray, m_axis: np.ndarray):
    """E-W (row through m=0) and N-S (column through l=0) profiles."""
    ir = int(np.argmin(np.abs(m_axis)))
    ic = int(np.argmin(np.abs(l_axis)))
    return image[ir, :], image[:, ic]


def psf_fwhm(psf: np.ndarray, l_axis: np.ndarray, m_axis: np.ndarray) -> tuple[float, float]:
    """(FWHM_EW, FWHM_NS) of a PSF in the units of the axes."""
    ew, ns = center_cuts(psf, l_axis, m_axis)
    return fwhm_main_lobe(ew, l_axis), fwhm_main_lobe(ns, m_axis)


def peak_position(image: np.ndarray, l_axis: np.ndarray, m_axis: np.ndarray) -> tuple[float, float]:
    i, j = np.unravel_index(np.argmax(image), image.shape)
    return float(l_axis[j]), float(m_axis[i])


def peak_sidelobe_level(psf: np.ndarray, l_axis, m_axis, exclude_radius) -> float:
    """Largest |PSF| outside `exclude_radius` (same units as the axes) relative to the peak."""
    L, M = np.meshgrid(l_axis, m_axis)
    mask = np.hypot(L, M) > exclude_radius
    return float(np.max(np.abs(psf[mask])) / np.max(psf)) if mask.any() else np.nan


def dynamic_range(image: np.ndarray, l_axis, m_axis, source_radius) -> float:
    """Peak / RMS of the image outside `source_radius` (off-source residual level)."""
    L, M = np.meshgrid(l_axis, m_axis)
    off = image[np.hypot(L, M) > source_radius]
    return float(np.max(image) / np.sqrt(np.mean(off ** 2))) if off.size else np.nan


def uv_filling_factor(u, v, uv_max: float, cells: int = 64) -> float:
    """Fraction of a cells x cells grid (|u|,|v| <= uv_max) hit by at least one sample
    (Hermitian points included) - a simple coverage-completeness measure."""
    uu = np.concatenate([np.ravel(u), -np.ravel(u)])
    vv = np.concatenate([np.ravel(v), -np.ravel(v)])
    H, _, _ = np.histogram2d(uu, vv, bins=cells, range=[[-uv_max, uv_max], [-uv_max, uv_max]])
    return float(np.count_nonzero(H) / H.size)
