"""Compare a simulated observation with a field light curve.

The field receiver reports an uncalibrated power P(t) = G k B (T_eff + T_sys x(t)),
where x(t) = P_sun(t) / (k T_sys B) is the simulated Sun-to-noise ratio (measured
flux x primary beam, from the pipeline) and T_eff is the effective system
temperature of the real receiver. A straight-line fit P = A + C x over the
observing window gives T_eff = T_sys A / C without knowing the gain G and
without needing a "Sun-off" noise level: the change of beam weighting along the
track provides the lever arm.
"""
from __future__ import annotations

import numpy as np

from .io.field_psd import FieldDay, align_to


def fit_effective_tsys(field: FieldDay, ut_sim: np.ndarray, x_sim: np.ndarray,
                       t_sys_model_k: float, flux_sfu: np.ndarray | None = None) -> dict:
    """Fit P_field = A + C x_sim on the overlapping samples.

    Returns the effective system temperature with a 1-sigma error from the
    regression, the correlation coefficient, the noise of the field light
    curve and, if `flux_sfu` (simulated flux on the same time axis) is given,
    the smallest flux increase the field instrument detects at 3 sigma near
    transit."""
    x = align_to(field, ut_sim, np.asarray(x_sim, float))
    ok = np.isfinite(x)
    if ok.sum() < 10:
        return {"field_error": "fewer than 10 field samples overlap the simulated track"}
    p = field.power_linear[ok] / np.median(field.power_linear[ok])      # relative units
    xo = x[ok]
    X = np.column_stack([np.ones_like(xo), xo])
    coef, res, *_ = np.linalg.lstsq(X, p, rcond=None)
    A, C = coef
    resid = p - X @ coef
    dof = max(p.size - 2, 1)
    cov = np.linalg.inv(X.T @ X) * (resid @ resid) / dof
    t_eff = t_sys_model_k * A / C
    # error propagation for A / C
    dA, dC, cAC = np.sqrt(cov[0, 0]), np.sqrt(cov[1, 1]), cov[0, 1]
    rel = np.sqrt((dA / A) ** 2 + (dC / C) ** 2 - 2 * cAC / (A * C))
    noise_rel = float(np.std(np.diff(p)) / np.sqrt(2))                   # per-sample, relative
    out = {
        "field_source": field.source,
        "field_n_samples": int(p.size),
        "field_ut_span": [str(field.ut[ok][0]), str(field.ut[ok][-1])],
        "field_corr_coef": float(np.corrcoef(xo, p)[0, 1]),
        "field_excess_peak_db": float(10 * np.log10(p.max() / p.min())),
        "field_noise_per_sample_db": float(10 * np.log10(1 + noise_rel)),
        "field_t_sys_eff_k": float(t_eff),
        "field_t_sys_eff_err_k": float(abs(t_eff) * rel),
        "field_t_sys_eff_over_model": float(A / C),
    }
    if flux_sfu is not None:
        s = align_to(field, ut_sim, np.asarray(flux_sfu, float))[ok]
        # relative power per SFU at the samples nearest transit (largest x / S)
        k = int(np.nanargmax(xo))
        dp_per_sfu = C * xo[k] / s[k]
        out["field_min_detectable_sfu_3sigma"] = float(3 * noise_rel / dp_per_sfu)
    return out
