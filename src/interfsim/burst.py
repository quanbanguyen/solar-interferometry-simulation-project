"""Moving solar radio bursts and burst-centroid tracking.

A few-element array at 610 MHz has a fringe spacing comparable to or larger
than the solar disk, so it cannot image a burst the way LOFAR or MWA do. It
can still measure the brightness centroid of a bright compact source from the
visibility phases, to a small fraction of the fringe spacing. This module

* describes a burst that rises, decays and moves radially across the sky
  (moving type IV / type II-like sources; plane-of-sky motion),
* synthesises its per-antenna voltages for Engine A (time-varying position,
  optional Gaussian extent made of independent emitters),
* gives its analytic visibilities for Engine B,
* estimates the source position per correlator dump (point-source maximum
  likelihood = peak of the per-dump dirty map), and
* gives the Cramer-Rao lower bound on that position, the reference against
  which a layout or a receiver can be judged.

Coordinates: l towards east, m towards north (direction cosines, radians),
relative to the centre of the solar disk. Position angle (PA) is measured
from north through east. The solar P-angle (tilt of the solar rotation axis
against celestial north) is ignored, so "north" here is celestial north.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from .array import ArrayConfig
from .constants import SUN_DIAMETER_DEG
from .geometry import Observation, antenna_phase
from .signal import complex_noise

R_SUN_KM = 695_700.0                                  # IAU nominal solar radius
R_SUN_RAD = np.radians(SUN_DIAMETER_DEG / 2)          # apparent radius used for km -> angle
ARCMIN = np.pi / (180 * 60)


@dataclass
class MovingBurst:
    """A compact burst source with a rise/decay light curve and radial plane-of-sky motion.

    Times are seconds on the same axis as the observation track (``t_s``).
    peak_flux_sfu : flux density at the peak, added on top of the quiet Sun.
    rise_s        : Gaussian rise time constant (sigma) before the peak.
    decay_s       : exponential decay time after the peak.
    start_r_rsun  : heliocentric distance of the source at onset [solar radii].
    pa_deg        : position angle of the radial path (0 = N, 90 = E).
    speed_km_s    : plane-of-sky speed (moving type IV: typically 10^2-10^3 km/s).
    fwhm_arcmin   : source size (circular Gaussian); 0 = point source.
    Onset is defined as t_peak_s - 3 rise_s; the source sits at start_r_rsun
    before onset and moves outward after it.
    """

    t_peak_s: float
    peak_flux_sfu: float = 1000.0
    rise_s: float = 120.0
    decay_s: float = 600.0
    start_r_rsun: float = 1.1
    pa_deg: float = 90.0
    speed_km_s: float = 500.0
    fwhm_arcmin: float = 0.0

    @property
    def t_onset_s(self) -> float:
        return self.t_peak_s - 3.0 * self.rise_s

    def flux(self, t_s) -> np.ndarray:
        """Burst flux density [SFU] at times t_s."""
        dt = np.asarray(t_s, float) - self.t_peak_s
        rise = np.exp(-0.5 * (dt / self.rise_s) ** 2)
        decay = np.exp(-np.clip(dt, 0.0, None) / self.decay_s)
        return self.peak_flux_sfu * np.where(dt < 0, rise, decay)

    def radius_rsun(self, t_s) -> np.ndarray:
        travelled = np.clip(np.asarray(t_s, float) - self.t_onset_s, 0.0, None) * self.speed_km_s
        return self.start_r_rsun + travelled / R_SUN_KM

    def position(self, t_s) -> tuple[np.ndarray, np.ndarray]:
        """(l, m) of the burst [rad] relative to the disk centre."""
        r = self.radius_rsun(t_s) * R_SUN_RAD
        pa = np.radians(self.pa_deg)
        return r * np.sin(pa), r * np.cos(pa)

    @property
    def angular_speed_arcmin_per_min(self) -> float:
        return self.speed_km_s * 60.0 / R_SUN_KM * R_SUN_RAD / ARCMIN


def gaussian_components(fwhm_rad: float, n_across: int = 7) -> np.ndarray:
    """Discretise a circular Gaussian into (weight, dl, dm) offsets that sum to 1.

    The grid spans +-1.5 FWHM; with fwhm_rad = 0 a single point is returned."""
    if fwhm_rad <= 0 or n_across <= 1:
        return np.array([[1.0, 0.0, 0.0]])
    g = np.linspace(-1.5, 1.5, n_across) * fwhm_rad
    L, M = np.meshgrid(g, g)
    sig = fwhm_rad / (2 * np.sqrt(2 * np.log(2)))
    wgt = np.exp(-(L ** 2 + M ** 2) / (2 * sig ** 2)).ravel()
    return np.column_stack([wgt / wgt.sum(), L.ravel(), M.ravel()])


def burst_voltages(config: ArrayConfig, obs: Observation, amplitude: np.ndarray,
                   l_t: np.ndarray, m_t: np.ndarray, fwhm_rad: float = 0.0,
                   n_across: int = 7, seed: int | None = None) -> np.ndarray:
    """Engine A voltages (T, N) of a moving source, without receiver noise.

    amplitude : (T,) RMS voltage of the burst at the antenna (flux, beam and
        receiver already applied, as for ``simulate_voltages``).
    l_t, m_t  : (T,) source position along the track [rad].
    Each component of an extended source radiates its own Gaussian process,
    so the source decorrelates on long baselines (van Cittert-Zernike)."""
    rng = np.random.default_rng(seed)
    T = obs.H_deg.size
    amp = np.broadcast_to(np.asarray(amplitude, float), (T,))
    out = np.zeros((T, config.n_ant), dtype=np.complex128)
    active = amp > 0
    if not active.any():
        return out
    idx = np.flatnonzero(active)
    sub = obs.subset(idx)
    for wgt, dl, dm in gaussian_components(fwhm_rad, n_across):
        proc = complex_noise(rng, idx.size, np.sqrt(wgt / 2))
        ph = antenna_phase(config.positions_enu, sub, l_t[idx] + dl, m_t[idx] + dm)
        out[idx] += (amp[idx] * proc)[:, None] * np.exp(1j * ph)
    return out


def vis_moving_gaussian(u, v, flux_t, l_t, m_t, fwhm_rad: float = 0.0) -> np.ndarray:
    """Engine B visibilities (T, B) of a source with time-varying flux and position."""
    q2 = u ** 2 + v ** 2
    shape = np.exp(-(np.pi * fwhm_rad) ** 2 * q2 / (4 * np.log(2))) if fwhm_rad > 0 else 1.0
    return (np.asarray(flux_t)[:, None] * shape
            * np.exp(-2j * np.pi * (u * np.asarray(l_t)[:, None] + v * np.asarray(m_t)[:, None])))


# ── centroid estimation ─────────────────────────────────────────────────────
@dataclass
class CentroidTrack:
    """Per-dump position estimates.

    l, m        : estimated position [rad]. For a dump whose baselines are all
                  parallel only the component along ``axis`` is measured; the
                  perpendicular component stays at the search prior (see ``is_2d``).
    along       : position projected on ``axis`` [rad] (always defined).
    axis        : (NI, 2) unit vector of the dominant baseline direction in (l, m).
    is_2d       : True where the dump's baselines span two dimensions.
    """

    l: np.ndarray
    m: np.ndarray
    along: np.ndarray
    axis: np.ndarray
    is_2d: np.ndarray

    def error(self, l_true, m_true) -> np.ndarray:
        """Position error per dump [rad]: 2-D distance, or the along-axis error
        for one-dimensional dumps."""
        dl, dm = self.l - l_true, self.m - m_true
        e2d = np.hypot(dl, dm)
        e1d = np.abs(self.along - (self.axis[:, 0] * l_true + self.axis[:, 1] * m_true))
        return np.where(self.is_2d, e2d, e1d)


def _uv_axes(u, v, tol: float = 0.05):
    """Dominant direction of a set of (u, v) points and whether they span 2-D."""
    P = np.column_stack([np.ravel(u), np.ravel(v)])
    _, s, vt = np.linalg.svd(P, full_matrices=False)
    is_2d = s.size > 1 and s[1] > tol * s[0]
    return vt[0], is_2d


def fit_point_source(u, v, vis, search_radius_rad: float, l0=0.0, m0=0.0,
                     n_grid: int = 41) -> tuple[float, float, np.ndarray, bool]:
    """Maximum-likelihood position of a single point source from phased visibilities.

    Maximises Re sum_b V_b exp(+2 pi i (u_b l + v_b m)) (the dirty map) over a
    box of +-search_radius around (l0, m0): grid search, then a Nelder-Mead
    refinement. For collinear baselines the fit is one-dimensional along the
    baseline direction. Returns (l, m, axis, is_2d)."""
    u, v, vis = np.ravel(u), np.ravel(v), np.ravel(vis)
    axis, is_2d = _uv_axes(u, v)

    def dirty(p):
        return float(np.real(np.sum(vis * np.exp(2j * np.pi * (u * p[0] + v * p[1])))))

    g = np.linspace(-search_radius_rad, search_radius_rad, n_grid)
    if is_2d:
        L, M = np.meshgrid(g + l0, g + m0)
        vals = np.real(np.exp(2j * np.pi * (np.outer(L.ravel(), u) + np.outer(M.ravel(), v))) @ vis)
        k = int(np.argmax(vals))
        start = np.array([L.ravel()[k], M.ravel()[k]])
        res = minimize(lambda p: -dirty(p), start, method="Nelder-Mead",
                       options={"xatol": search_radius_rad * 1e-4, "fatol": 1e-12})
        return float(res.x[0]), float(res.x[1]), axis, True
    base = np.array([l0, m0])
    t0 = float(axis @ base)
    pts = base[None, :] + np.outer(g, axis)
    vals = np.real(np.exp(2j * np.pi * (np.outer(pts[:, 0], u) + np.outer(pts[:, 1], v))) @ vis)
    k = int(np.argmax(vals))
    res = minimize(lambda t: -dirty(base + (t[0] - t0) * axis), [t0 + g[k]], method="Nelder-Mead",
                   options={"xatol": search_radius_rad * 1e-4, "fatol": 1e-12})
    p = base + (res.x[0] - t0) * axis
    return float(p[0]), float(p[1]), axis, False


def track_centroid(u, v, vis_phased, search_radius_rad: float,
                   prior_l=None, prior_m=None) -> CentroidTrack:
    """Fit a point source in every dump. vis_phased: (NI, B), already fringe-stopped
    and with any model of the quiet Sun subtracted. prior_l/m (NI,) centre the
    search box (default: disk centre)."""
    NI = vis_phased.shape[0]
    pl = np.zeros(NI) if prior_l is None else np.asarray(prior_l, float)
    pm = np.zeros(NI) if prior_m is None else np.asarray(prior_m, float)
    l, m, along = np.empty(NI), np.empty(NI), np.empty(NI)
    axes, is2 = np.empty((NI, 2)), np.empty(NI, bool)
    for k in range(NI):
        lk, mk, ax, d2 = fit_point_source(u[k], v[k], vis_phased[k], search_radius_rad, pl[k], pm[k])
        if ax[0] < 0 or (ax[0] == 0 and ax[1] < 0):      # fixed orientation for "along"
            ax = -ax
        l[k], m[k], axes[k], is2[k] = lk, mk, ax, d2
        along[k] = ax[0] * lk + ax[1] * mk
    return CentroidTrack(l, m, along, axes, is2)


def centroid_crb(u, v, snr_vis) -> np.ndarray:
    """Cramer-Rao bound on the position of a point source from one dump [rad].

    snr_vis : amplitude SNR of each visibility, |V| / sigma (sigma per
        quadrature), scalar or (B,).
    The Fisher matrix is F = sum_b (2 pi snr_b)^2 [u_b, v_b]^T [u_b, v_b].
    Returns the rms 2-D position error sqrt(trace F^-1); for collinear
    baselines (singular F) the bound along the baseline direction."""
    u, v = np.ravel(u), np.ravel(v)
    s = np.broadcast_to(np.asarray(snr_vis, float), u.shape)
    A = np.column_stack([u, v]) * (2 * np.pi * s)[:, None]
    F = A.T @ A
    axis, is_2d = _uv_axes(u, v)
    if is_2d:
        return float(np.sqrt(np.trace(np.linalg.inv(F))))
    return float(1.0 / np.sqrt(axis @ F @ axis))


def visibility_snr(p_burst, p_total, n_avg: int) -> np.ndarray:
    """Amplitude SNR of a cross-correlation of n_avg complex samples:
    |V| / sigma_quadrature = P_burst / P_total * sqrt(2 n_avg), where P_total is
    the total power per antenna (burst + quiet Sun + receiver noise)."""
    return np.asarray(p_burst, float) / np.asarray(p_total, float) * np.sqrt(2.0 * n_avg)
