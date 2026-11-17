"""Low-precision solar ephemeris (NOAA algorithm, ~0.01 deg over 1950-2050).

Kept dependency-free on purpose: for the Sun's hour angle and declination at
the arc-minute level this is more than enough for array simulation, and
astropy can be swapped in when sub-arcsecond positions are needed.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Site:
    name: str
    lat_deg: float
    lon_deg: float           # east positive
    height_m: float = 0.0


LEARMONTH = Site("Learmonth (RSTN)", -22.22, 114.10, 5.0)
HOA_LAC = Site("Hoa Lac, Hanoi", 21.01, 105.52, 20.0)


def _julian_day(ut: np.ndarray) -> np.ndarray:
    ut = np.asarray(ut, dtype="datetime64[ns]")
    return ut.astype("int64") / 86400e9 + 2440587.5


def solar_position(ut) -> tuple[np.ndarray, np.ndarray]:
    """Return (declination_deg, equation_of_time_min) for UT datetime64 values."""
    jc = (_julian_day(ut) - 2451545.0) / 36525.0
    L0 = np.radians((280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360.0)
    M = np.radians(357.52911 + jc * (35999.05029 - 0.0001537 * jc))
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    C = np.radians(np.sin(M) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
                   + np.sin(2 * M) * (0.019993 - 0.000101 * jc)
                   + np.sin(3 * M) * 0.000289)
    omega = np.radians(125.04 - 1934.136 * jc)
    lam = L0 + C - np.radians(0.00569 + 0.00478 * np.sin(omega))
    eps0 = 23.0 + (26.0 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60.0) / 60.0
    eps = np.radians(eps0 + 0.00256 * np.cos(omega))
    dec = np.degrees(np.arcsin(np.sin(eps) * np.sin(lam)))
    y = np.tan(eps / 2) ** 2
    eot = 4.0 * np.degrees(y * np.sin(2 * L0) - 2 * e * np.sin(M)
                           + 4 * e * y * np.sin(M) * np.cos(2 * L0)
                           - 0.5 * y * y * np.sin(4 * L0) - 1.25 * e * e * np.sin(2 * M))
    return dec, eot


def sun_hour_angle_dec(ut, lon_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Local hour angle [deg, -180..180, 0 = transit] and declination [deg] of the Sun."""
    ut = np.asarray(ut, dtype="datetime64[ns]")
    dec, eot = solar_position(ut)
    day = ut.astype("datetime64[D]")
    minutes = (ut - day).astype("int64") / 60e9
    tst = minutes + eot + 4.0 * lon_deg              # true solar time [min]
    H = (tst / 4.0 - 180.0 + 180.0) % 360.0 - 180.0
    return H, dec


def sun_elevation_deg(ut, site: Site) -> np.ndarray:
    H, dec = sun_hour_angle_dec(ut, site.lon_deg)
    lat, dec, H = np.radians(site.lat_deg), np.radians(dec), np.radians(H)
    return np.degrees(np.arcsin(np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(H)))
