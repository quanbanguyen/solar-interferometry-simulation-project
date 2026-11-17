"""Observation geometry: ENU -> equatorial XYZ -> (u, v, w), alt-az, phases.

Conventions follow Thompson, Moran & Swenson, *Interferometry and Synthesis in
Radio Astronomy* (3rd ed.), Sect. 4.1: X towards (H=0, dec=0), Y towards
(H=-6h, dec=0) i.e. East, Z towards the celestial pole.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .constants import C_LIGHT


@dataclass
class Observation:
    """Station latitude, source declination, observing frequency and hour-angle track."""

    lat_deg: float
    dec_deg: float
    fc_hz: float = 610e6
    H_deg: np.ndarray = field(default_factory=lambda: np.linspace(-90.0, 90.0, 600))

    def __post_init__(self) -> None:
        self.H_deg = np.atleast_1d(np.asarray(self.H_deg, dtype=float))

    @property
    def lam(self) -> float:
        return C_LIGHT / self.fc_hz

    @property
    def H_rad(self) -> np.ndarray:
        return np.radians(self.H_deg)

    @property
    def dec_rad(self) -> float:
        return float(np.radians(self.dec_deg))

    @property
    def lat_rad(self) -> float:
        return float(np.radians(self.lat_deg))

    def subset(self, idx) -> Observation:
        """Same observation restricted to the hour angles H_deg[idx]."""
        return Observation(self.lat_deg, self.dec_deg, self.fc_hz, self.H_deg[idx])


def enu_to_xyz(enu: np.ndarray, lat_rad: float) -> np.ndarray:
    """Rotate local ENU vectors to the equatorial XYZ frame."""
    E, N, U = enu[..., 0], enu[..., 1], enu[..., 2]
    X = -N * np.sin(lat_rad) + U * np.cos(lat_rad)
    Y = E
    Z = N * np.cos(lat_rad) + U * np.sin(lat_rad)
    return np.stack([X, Y, Z], axis=-1)


def source_dir_xyz(H_rad: np.ndarray, dec_rad: float) -> np.ndarray:
    """Unit vector towards the phase centre in XYZ, shape (T, 3)."""
    cd = np.cos(dec_rad)
    return np.stack([cd * np.cos(H_rad), -cd * np.sin(H_rad),
                     np.full_like(H_rad, np.sin(dec_rad))], axis=-1)


def uv_basis_xyz(H_rad: np.ndarray, dec_rad: float) -> tuple[np.ndarray, np.ndarray]:
    """Unit vectors along the u (east) and v (north) sky axes in XYZ, each (T, 3)."""
    sH, cH = np.sin(H_rad), np.cos(H_rad)
    sd, cd = np.sin(dec_rad), np.cos(dec_rad)
    eu = np.stack([sH, cH, np.zeros_like(H_rad)], axis=-1)
    ev = np.stack([-sd * cH, sd * sH, np.full_like(H_rad, cd)], axis=-1)
    return eu, ev


def compute_uvw(baseline_vecs_enu: np.ndarray, obs: Observation):
    """(u, v, w) in wavelengths for every (time, baseline); each has shape (T, B).

    TMS Eq. 4.1. w is the baseline projected on the source direction, so the
    geometric delay of baseline b is tau = w * lambda / c.
    """
    b = enu_to_xyz(np.asarray(baseline_vecs_enu, float), obs.lat_rad) / obs.lam
    s = source_dir_xyz(obs.H_rad, obs.dec_rad)
    eu, ev = uv_basis_xyz(obs.H_rad, obs.dec_rad)
    return eu @ b.T, ev @ b.T, s @ b.T


def antenna_phase(positions_enu: np.ndarray, obs: Observation,
                  l: float = 0.0, m: float = 0.0) -> np.ndarray:
    """Geometric phase of each antenna, shape (T, N), for a source at offset (l, m)
    [direction cosines] from the phase centre: phi_k = -2*pi/lambda * r_k . s_hat."""
    ant = enu_to_xyz(np.asarray(positions_enu, float), obs.lat_rad)
    s = source_dir_xyz(obs.H_rad, obs.dec_rad)
    if l or m:
        eu, ev = uv_basis_xyz(obs.H_rad, obs.dec_rad)
        s = s + l * eu + m * ev
    return -2.0 * np.pi / obs.lam * (s @ ant.T)


def altaz_deg(obs: Observation) -> tuple[np.ndarray, np.ndarray]:
    """Azimuth (0=N, 90=E) and elevation of the phase centre along the track [deg]."""
    lat, dec, H = obs.lat_rad, obs.dec_rad, obs.H_rad
    sin_el = np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(H)
    el = np.arcsin(np.clip(sin_el, -1.0, 1.0))
    az = np.arctan2(-np.cos(dec) * np.sin(H),
                    np.sin(dec) * np.cos(lat) - np.cos(dec) * np.cos(H) * np.sin(lat))
    return np.degrees(az) % 360.0, np.degrees(el)


def zenith_angle_deg(obs: Observation) -> np.ndarray:
    return 90.0 - altaz_deg(obs)[1]


def altaz_to_enu(az_deg, el_deg) -> np.ndarray:
    """Unit direction vectors in ENU, shape (..., 3)."""
    az, el = np.radians(az_deg), np.radians(el_deg)
    return np.stack([np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)], axis=-1)
