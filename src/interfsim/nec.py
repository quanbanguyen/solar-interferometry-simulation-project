"""Read radiation patterns from NEC-2 / 4NEC2 output files."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class NecPattern:
    freq_MHz: float | None
    theta_deg: np.ndarray            # (Nt,)
    phi_deg: np.ndarray              # (Np,)
    gain_total_dBi: np.ndarray       # (Nt, Np)
    gain_vert_dBi: np.ndarray
    gain_hor_dBi: np.ndarray


_FREQ = re.compile(r"FREQUENCY\s*=\s*([0-9.Ee+-]+)\s*MHZ", re.I)


def read_nec_pattern(path: str | Path, block: int = 0) -> NecPattern:
    """Parse the `block`-th RADIATION PATTERNS table of a NEC output file.

    Rows are ``THETA PHI VERT HOR TOTAL ...`` in degrees / dB; any theta/phi
    scan order is accepted and returned on a sorted regular grid.
    """
    lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    freq = None
    starts = []
    for i, ln in enumerate(lines):
        m = _FREQ.search(ln)
        if m and freq is None:
            freq = float(m.group(1))
        if "RADIATION PATTERNS" in ln:
            starts.append(i)
    if len(starts) <= block:
        raise ValueError(f"no RADIATION PATTERNS block #{block} in {path}")

    rows = []
    started = False
    for ln in lines[starts[block] + 1:]:
        parts = ln.split()
        try:
            vals = [float(p) for p in parts[:5]]
        except ValueError:
            if started:
                break
            continue
        if len(vals) < 5:
            if started:
                break
            continue
        rows.append(vals)
        started = True
    a = np.array(rows)
    theta, phi = np.unique(a[:, 0]), np.unique(a[:, 1])
    grids = []
    for col in (4, 2, 3):
        g = np.full((theta.size, phi.size), np.nan)
        g[np.searchsorted(theta, a[:, 0]), np.searchsorted(phi, a[:, 1])] = a[:, col]
        g[g <= -999] = -100.0
        grids.append(g)
    return NecPattern(freq, theta, phi, *grids)
