"""Antenna array layouts in the local East-North-Up (ENU) frame."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import numpy as np


@dataclass
class ArrayConfig:
    """Antenna positions in local ENU coordinates [m], shape (N, 3).

    A (N, 2) input is accepted and gets Up = 0. Positions are re-centred on the
    array centroid; baselines are unaffected by this.
    """

    name: str
    positions_enu: np.ndarray

    def __post_init__(self) -> None:
        p = np.atleast_2d(np.asarray(self.positions_enu, dtype=float))
        if p.shape[1] == 2:
            p = np.hstack([p, np.zeros((p.shape[0], 1))])
        if p.shape[1] != 3:
            raise ValueError("positions_enu must have shape (N, 2) or (N, 3)")
        if p.shape[0] < 2:
            raise ValueError("an interferometer needs at least two antennas")
        self.positions_enu = p - p.mean(axis=0)

    @property
    def n_ant(self) -> int:
        return self.positions_enu.shape[0]

    @property
    def pairs(self) -> list[tuple[int, int]]:
        return list(combinations(range(self.n_ant), 2))

    @property
    def n_baselines(self) -> int:
        return self.n_ant * (self.n_ant - 1) // 2

    @property
    def baseline_vectors_enu(self) -> np.ndarray:
        """(B, 3) baseline vectors b_ij = r_i - r_j, ordered as :attr:`pairs`."""
        p = self.positions_enu
        i, j = np.array(self.pairs).T
        return p[i] - p[j]

    @property
    def baseline_lengths(self) -> np.ndarray:
        return np.linalg.norm(self.baseline_vectors_enu, axis=1)

    def baseline_labels(self, fmt: str = "{i}-{j} ({length:.0f} m)") -> list[str]:
        return [fmt.format(i=i, j=j, length=L)
                for (i, j), L in zip(self.pairs, self.baseline_lengths, strict=True)]

    def unique_baseline_directions(self, decimals: int = 1) -> int:
        """Number of distinct baseline orientations (mod 180 deg).

        Parallel baselines trace overlapping u-v tracks, so this is a simple
        redundancy measure for small arrays.
        """
        b = self.baseline_vectors_enu[:, :2]
        ang = np.round(np.degrees(np.arctan2(b[:, 1], b[:, 0])) % 180.0, decimals)
        return int(np.unique(ang % 180.0).size)

    def summary(self) -> str:
        bl = self.baseline_lengths
        return (f"{self.name}: N={self.n_ant} antennas, {self.n_baselines} baselines, "
                f"min/max baseline = {bl.min():.1f}/{bl.max():.1f} m")

    def to_file(self, path: str | Path) -> None:
        header = f"{self.name}\nE_m N_m U_m"
        np.savetxt(path, self.positions_enu, fmt="%.4f", header=header)


# ── builders ────────────────────────────────────────────────────────────────
def from_enu(positions_enu, name: str = "custom") -> ArrayConfig:
    """Arbitrary layout from an (N, 2) or (N, 3) array in metres."""
    return ArrayConfig(name, np.asarray(positions_enu, dtype=float))


def from_file(path: str | Path, name: str | None = None) -> ArrayConfig:
    """Read a whitespace/comma separated table of E N [U] in metres ('#' comments)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8").replace(",", " ")
    rows = [ln.split() for ln in text.splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")]
    return ArrayConfig(name or path.stem, np.array(rows, dtype=float))


def linear(n: int, spacing: float, az_deg: float = 90.0, name: str | None = None) -> ArrayConfig:
    """n antennas on a line with step `spacing` m along compass azimuth az (0=N, 90=E)."""
    az = np.radians(az_deg)
    r = np.arange(n) * spacing
    return ArrayConfig(name or f"linear_n{n}_d{spacing:g}_az{az_deg:g}",
                       np.column_stack([r * np.sin(az), r * np.cos(az)]))


def cross(n_arm: int, spacing: float, name: str | None = None) -> ArrayConfig:
    """Plus-shaped array: centre antenna plus n_arm antennas on each of the E, W, N, S arms."""
    pts = [(0.0, 0.0)]
    for d in np.arange(1, n_arm + 1) * spacing:
        pts += [(d, 0.0), (-d, 0.0), (0.0, d), (0.0, -d)]
    return ArrayConfig(name or f"cross_arm{n_arm}_d{spacing:g}", np.array(pts))


def tee(n_ew: int, n_ns: int, spacing: float, name: str | None = None) -> ArrayConfig:
    """T-shaped array: an E-W arm of n_ew antennas and a northward arm of n_ns antennas."""
    pts = [(i * spacing, 0.0) for i in range(n_ew)]
    pts += [(0.0, j * spacing) for j in range(1, n_ns + 1)]
    return ArrayConfig(name or f"tee_{n_ew}x{n_ns}_d{spacing:g}", np.array(pts))


def triangle_center(side: float, az0_deg: float = 0.0, name: str | None = None) -> ArrayConfig:
    """Equilateral triangle of side `side` m plus a centre antenna (DLITE-style).

    No two of the six baselines are parallel, so every baseline traces a
    distinct u-v ellipse (Helmboldt et al. 2021, Radio Sci. 56, e2021RS007298).
    Antenna 0 is the centre; antenna 1 points to azimuth az0_deg.
    """
    R = side / np.sqrt(3.0)
    az = np.radians(az0_deg + np.array([0.0, 120.0, 240.0]))
    pts = np.vstack([[0.0, 0.0], np.column_stack([R * np.sin(az), R * np.cos(az)])])
    return ArrayConfig(name or f"triangle_center_side{side:g}", pts)


def random_2d(n: int, extent: float, seed: int = 0, name: str | None = None) -> ArrayConfig:
    """n antennas uniformly distributed in a square of side `extent` m."""
    rng = np.random.default_rng(seed)
    return ArrayConfig(name or f"random_n{n}_ext{extent:g}_s{seed}",
                       (rng.random((n, 2)) - 0.5) * extent)


# ── presets used in the thesis ──────────────────────────────────────────────
def preset_compact(spacing: float = 8.0) -> ArrayConfig:
    """Case 1: four antennas on an E-W line, [0, 8, 16, 24] m (field setup)."""
    return linear(4, spacing, az_deg=90.0, name="compact_outdoor_EW")


def preset_cross4(spacing: float = 8.0) -> ArrayConfig:
    """Case 1.5: four antennas on a cross, two E-W and two N-S at +/- spacing."""
    s = spacing
    return from_enu([[-s, 0], [s, 0], [0, -s], [0, s]], name=f"cross_4ant_{s:g}m")


def preset_dlite(side: float = 8.0) -> ArrayConfig:
    """Case 1.75: DLITE-style triangle + centre with the first vertex to the north."""
    return triangle_center(side, az0_deg=0.0, name=f"dlite_triangle_center_{side:g}m")


def preset_extended() -> ArrayConfig:
    """Case 2: graded 2-D cross, baselines 5-130 m (resolves the solar disk at 610 MHz)."""
    pts = [(0.0, 0.0)]
    for d in (5.0, 15.0, 35.0, 65.0):
        pts += [(d, 0.0), (-d, 0.0), (0.0, d), (0.0, -d)]
    return ArrayConfig("extended_graded_cross_2D", np.array(pts))


PRESETS = {
    "compact": preset_compact,
    "cross4": preset_cross4,
    "dlite": preset_dlite,
    "extended": preset_extended,
}


def make_array(spec: dict) -> ArrayConfig:
    """Build a layout from a config dict, e.g. {"preset": "dlite", "side": 8}
    or {"type": "linear", "n": 8, "spacing": 15, "az_deg": 0}
    or {"positions": [[0, 0], [10, 0]]} or {"file": "layout.txt"}."""
    spec = dict(spec)
    if "preset" in spec:
        return PRESETS[spec.pop("preset")](**spec)
    if "positions" in spec:
        return from_enu(spec["positions"], name=spec.get("name", "custom"))
    if "file" in spec:
        return from_file(spec["file"], name=spec.get("name"))
    builders = {"linear": linear, "cross": cross, "tee": tee,
                "triangle_center": triangle_center, "random_2d": random_2d}
    return builders[spec.pop("type")](**spec)
