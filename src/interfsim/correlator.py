"""FX-style cross-correlation with integration ("correlator")."""
from __future__ import annotations

import numpy as np

from .array import ArrayConfig


def correlate(V: np.ndarray, config: ArrayConfig, integration_bins: int):
    """Cross-multiply every antenna pair and average over `integration_bins` samples.

    Returns (vis, centers): vis has shape (NI, B) ordered as config.pairs, and
    centers are the sample indices at the middle of each dump. Trailing samples
    that do not fill a whole dump are dropped.
    """
    T = V.shape[0]
    NI = T // integration_bins
    if NI == 0:
        raise ValueError("integration_bins is larger than the number of samples")
    nval = NI * integration_bins
    i, j = np.array(config.pairs).T
    cc = V[:nval, i] * np.conj(V[:nval, j])
    vis = cc.reshape(NI, integration_bins, -1).mean(axis=1)
    centers = np.arange(NI) * integration_bins + integration_bins // 2
    return vis, centers


def fringe_rotation_per_dump(w_at_centers: np.ndarray) -> np.ndarray:
    """Fringe phase rotation [rad] across one dump, per baseline, estimated from w
    at consecutive dump centres. Values approaching ~1 rad mean the dump time is
    too long: amplitude is lost to time-average smearing, ~sinc(rotation / 2 pi)."""
    if w_at_centers.shape[0] < 2:
        return np.zeros(w_at_centers.shape[1:])
    return 2 * np.pi * np.abs(np.diff(w_at_centers, axis=0)).max(axis=0)


def autocorrelate(V: np.ndarray, integration_bins: int) -> np.ndarray:
    """Total power per antenna, shape (NI, N)."""
    NI = V.shape[0] // integration_bins
    p = np.abs(V[:NI * integration_bins]) ** 2
    return p.reshape(NI, integration_bins, -1).mean(axis=1)
