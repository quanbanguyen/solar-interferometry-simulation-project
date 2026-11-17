"""Antenna primary beams.

A tabulated beam is stored in the frame of the file it came from (NEC, HFSS,
CST ...): theta measured from +z, phi from +x. A mount description maps that
antenna frame onto the local ENU sky, so the beam is evaluated in the real
direction of the source instead of along a single pattern cut.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from .geometry import altaz_to_enu

_AXES = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0),
         "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}


@dataclass
class Mount:
    """How the antenna is installed.

    boresight_axis / element_axis : axes of the *pattern file* frame that point
        along the main beam and along the driven element (e.g. "+y", "+x" for
        the 4NEC2 Yagi model in this repo).
    pointing_az_deg, pointing_el_deg : sky direction of the boresight.
    element_az_deg : horizontal azimuth of the element axis when pointing at
        zenith (0 = elements along N-S, 90 = elements along E-W). For other
        pointings it is the azimuth of the element axis projected on the ground.
    """

    boresight_axis: str = "+y"
    element_axis: str = "+x"
    pointing_az_deg: float = 0.0
    pointing_el_deg: float = 90.0
    element_az_deg: float = 0.0

    def rotation(self) -> np.ndarray:
        """3x3 matrix R with R @ v_file = v_enu."""
        b = np.array(_AXES[self.boresight_axis], float)
        e = np.array(_AXES[self.element_axis], float)
        if abs(b @ e) > 1e-9:
            raise ValueError("boresight_axis and element_axis must be orthogonal")
        p = altaz_to_enu(self.pointing_az_deg, self.pointing_el_deg)
        ea = np.radians(self.element_az_deg)
        e_enu = np.array([np.sin(ea), np.cos(ea), 0.0])
        e_enu = e_enu - (e_enu @ p) * p                  # make orthogonal to pointing
        if np.linalg.norm(e_enu) < 1e-9:
            raise ValueError("element axis cannot be parallel to the pointing direction")
        e_enu /= np.linalg.norm(e_enu)
        F = np.column_stack([b, e, np.cross(b, e)])
        S = np.column_stack([p, e_enu, np.cross(p, e_enu)])
        return S @ F.T


class Beam:
    """Interface: normalised power response (1 at boresight) towards ENU directions."""

    def power_enu(self, dirs_enu: np.ndarray) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError

    def power_altaz(self, az_deg, el_deg) -> np.ndarray:
        return self.power_enu(altaz_to_enu(az_deg, el_deg))

    def voltage_altaz(self, az_deg, el_deg) -> np.ndarray:
        return np.sqrt(self.power_altaz(az_deg, el_deg))


class IsotropicBeam(Beam):
    def __init__(self, gain_dBi: float = 0.0):
        self.gain_max_dBi = gain_dBi

    def power_enu(self, dirs_enu):
        return np.ones(np.shape(dirs_enu)[:-1])


class GaussianBeam(Beam):
    """Circular Gaussian beam of given half-power width around a pointing direction."""

    def __init__(self, fwhm_deg: float, gain_dBi: float, pointing_az_deg: float = 0.0,
                 pointing_el_deg: float = 90.0):
        self.fwhm_deg = fwhm_deg
        self.gain_max_dBi = gain_dBi
        self._p = altaz_to_enu(pointing_az_deg, pointing_el_deg)

    def power_enu(self, dirs_enu):
        ang = np.degrees(np.arccos(np.clip(np.asarray(dirs_enu) @ self._p, -1, 1)))
        return np.exp(-4 * np.log(2) * (ang / self.fwhm_deg) ** 2)


class TabulatedBeam(Beam):
    """Gain table G(theta, phi) [dBi] on a regular grid in the pattern-file frame."""

    def __init__(self, theta_deg, phi_deg, gain_dBi, freq_MHz: float | None = None,
                 mount: Mount | None = None, source: str = ""):
        theta = np.asarray(theta_deg, float)
        phi = np.asarray(phi_deg, float)
        gain = np.asarray(gain_dBi, float)
        if gain.shape != (theta.size, phi.size):
            raise ValueError("gain_dBi must have shape (len(theta), len(phi))")
        if theta.max() <= 0 and theta.min() < 0:
            # NEC "negative theta" scan (e.g. RP theta -180..0): direction (theta, phi)
            # equals (-theta, phi + 180) in the usual 0..180 convention.
            theta, phi, gain = _canonicalise_negative_theta(theta, phi, gain)
        order = np.argsort(theta)
        theta, gain = theta[order], gain[order]
        phi, gain = _wrap_phi(phi, gain)
        self.theta, self.phi, self.gain_dBi = theta, phi, gain
        self.freq_MHz = freq_MHz
        self.source = source
        k = np.unravel_index(np.nanargmax(gain), gain.shape)
        self.gain_max_dBi = float(gain[k])
        self.peak_theta_phi = (float(theta[k[0]]), float(phi[k[1]]))
        self.mount = mount or Mount()
        self._R = self.mount.rotation()
        p_lin = 10.0 ** ((np.nan_to_num(gain, nan=-100.0) - self.gain_max_dBi) / 10.0)
        self._interp = RegularGridInterpolator((theta, phi), p_lin,
                                               bounds_error=False, fill_value=0.0)

    def with_mount(self, mount: Mount) -> TabulatedBeam:
        return TabulatedBeam(self.theta, self.phi, self.gain_dBi, self.freq_MHz, mount, self.source)

    def power_file_frame(self, theta_deg, phi_deg) -> np.ndarray:
        pts = np.stack(np.broadcast_arrays(np.asarray(theta_deg, float),
                                           np.asarray(phi_deg, float) % 360.0), axis=-1)
        return self._interp(pts)

    def power_enu(self, dirs_enu):
        d = np.asarray(dirs_enu, float) @ self._R          # = R^T d, file frame
        theta = np.degrees(np.arccos(np.clip(d[..., 2], -1.0, 1.0)))
        phi = np.degrees(np.arctan2(d[..., 1], d[..., 0])) % 360.0
        return self.power_file_frame(theta, phi)

    def boresight_power(self) -> float:
        return float(np.ravel(self.power_altaz(self.mount.pointing_az_deg,
                                               self.mount.pointing_el_deg))[0])

    # ── loaders ──────────────────────────────────────────────────────────────
    @classmethod
    def from_npz(cls, path, mount: Mount | None = None) -> TabulatedBeam:
        """Load an .npz with theta_deg, phi_deg, gain_dBi [, freq_MHz]."""
        d = np.load(path)
        freq = float(d["freq_MHz"]) if "freq_MHz" in d.files else None
        return cls(d["theta_deg"], d["phi_deg"], d["gain_dBi"], freq, mount, str(path))

    @classmethod
    def from_csv(cls, path, mount: Mount | None = None, freq_MHz: float | None = None,
                 theta_col: str | None = None, phi_col: str | None = None,
                 gain_col: str | None = None) -> TabulatedBeam:
        """Load a long-format far-field table (one row per direction).

        Column names are auto-detected (case-insensitive substrings 'theta',
        'phi' and 'gain'/'db'), which covers 4NEC2 exports and HFSS/CST
        far-field reports such as ``Phi [deg], Theta [deg], dB(GainTotal) []``.
        """
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        header = [h.strip() for h in rows[0]]
        low = [h.lower() for h in header]

        def pick(explicit, *keys):
            if explicit:
                return header.index(explicit)
            for key in keys:
                for i, h in enumerate(low):
                    if key in h:
                        return i
            raise ValueError(f"cannot find a column matching {keys} in {header}")

        it, ip = pick(theta_col, "theta"), pick(phi_col, "phi")
        ig = pick(gain_col, "gain", "db", "directivity")
        data = np.array([[float(r[it]), float(r[ip]), float(r[ig])] for r in rows[1:] if r], float)
        theta = np.unique(data[:, 0])
        phi = np.unique(data[:, 1])
        grid = np.full((theta.size, phi.size), np.nan)
        grid[np.searchsorted(theta, data[:, 0]), np.searchsorted(phi, data[:, 1])] = data[:, 2]
        return cls(theta, phi, grid, freq_MHz, mount, str(path))

    @classmethod
    def from_nec_out(cls, path, mount: Mount | None = None) -> TabulatedBeam:
        from .nec import read_nec_pattern
        pat = read_nec_pattern(path)
        return cls(pat.theta_deg, pat.phi_deg, pat.gain_total_dBi, pat.freq_MHz, mount, str(path))

    def to_npz(self, path) -> None:
        np.savez_compressed(path, theta_deg=self.theta, phi_deg=self.phi, gain_dBi=self.gain_dBi,
                            gain_max_dBi=self.gain_max_dBi, freq_MHz=self.freq_MHz or np.nan)


def load_beam(path, mount: Mount | None = None) -> TabulatedBeam:
    """Load a beam from .npz, .csv or a NEC .out/.out.txt file."""
    name = str(path).lower()
    if name.endswith(".npz"):
        return TabulatedBeam.from_npz(path, mount)
    if name.endswith(".csv"):
        return TabulatedBeam.from_csv(path, mount)
    if name.endswith(".out") or name.endswith(".out.txt"):
        return TabulatedBeam.from_nec_out(path, mount)
    raise ValueError(f"unsupported beam file: {path}")


def _canonicalise_negative_theta(theta, phi, gain):
    theta_c = -theta
    phi_c = (phi + 180.0) % 360.0
    order = np.argsort(phi_c, kind="stable")
    phi_c, gain = phi_c[order], gain[:, order]
    phi_c, idx = np.unique(phi_c, return_index=True)
    return theta_c, phi_c, gain[:, idx]


def _wrap_phi(phi, gain):
    """Sort phi, drop a duplicate 360, and append phi+360 so interpolation wraps."""
    phi = phi % 360.0
    order = np.argsort(phi, kind="stable")
    phi, gain = phi[order], gain[:, order]
    phi, idx = np.unique(phi, return_index=True)
    gain = gain[:, idx]
    phi = np.append(phi, phi[0] + 360.0)
    gain = np.hstack([gain, gain[:, :1]])
    return phi, gain


def default_beam_path() -> Path:
    """Path of the 610 MHz U-frame Yagi beam shipped in data/antenna/beams (repo checkout)."""
    beams = Path(__file__).resolve().parents[2] / "data" / "antenna" / "beams"
    return beams / "UFRAME_primary_beam_610MHz.npz"
