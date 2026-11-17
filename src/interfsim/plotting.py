"""Static (matplotlib) figures for pipeline results."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .metrics import center_cuts


def _plt():
    import matplotlib
    if matplotlib.get_backend().lower() not in ("agg", "module://matplotlib_inline.backend_inline"):
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def sliding_rms(x: np.ndarray, w: int) -> np.ndarray:
    """Centred-ish running RMS of |x| with window w (O(N))."""
    cs = np.concatenate([[0.0], np.cumsum(np.abs(x) ** 2)])
    r = np.sqrt((cs[w:] - cs[:-w]) / w)
    return np.concatenate([np.full(w - 1, r[0]), r])


def _hours(res):
    return (res.ut - res.ut[0]).astype("timedelta64[ms]").astype(float) / 3.6e6


def plot_track(res, ax_flux=None, ax_env=None, window: int = 500):
    plt = _plt()
    if ax_flux is None:
        fig, (ax_flux, ax_env) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    t = _hours(res)
    ax_flux.plot(t, res.flux_sfu, color="tab:orange", lw=0.8)
    ax_flux.set_ylabel("Flux density (SFU)")
    ax_flux.set_title(f"RSTN {res.cfg.observation.freq_mhz:g} MHz, from {str(res.ut[0])[:16]} UT")
    env = sliding_rms(res.V[:, 0], min(window, res.V.shape[0])) * 1e6
    ax_env.plot(t, env, color="tab:blue", lw=0.8, label="antenna 0, sliding RMS")
    ax_env.axhline(res.summary["v_noise_rms_v"] * 1e6, color="tab:red", ls="--", label="noise floor")
    ax_env.plot(t, np.sqrt(res.p_signal_w * res.cfg.receiver.r_load_ohm) * 1e6,
                color="k", lw=0.8, alpha=0.6, label="source only (beam-weighted)")
    ax_env.set_xlabel("Hours since start of track")
    ax_env.set_ylabel("RMS voltage (uV)")
    ax_env.legend(fontsize=8)
    return ax_flux.figure


def plot_visibilities(res):
    plt = _plt()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    H = res.obs.H_deg[res.centers]
    for b, lab in enumerate(res.array.baseline_labels()):
        a1.plot(H, np.abs(res.vis[:, b]), lw=0.7, label=lab)
        a2.plot(H, np.angle(res.vis[:, b], deg=True), ".", ms=1)
    a1.set_ylabel("|V| (V^2)")
    a1.legend(fontsize=7, ncol=2)
    a2.set_ylabel("phase (deg)")
    a2.set_xlabel("Hour angle (deg)")
    a1.set_title(f"Raw correlator output - {res.array.name}")
    return fig


def plot_uv(res, ax=None):
    plt = _plt()
    if ax is None:
        fig, ax = plt.subplots(figsize=(5.5, 5.5))
    for b, lab in enumerate(res.array.baseline_labels()):
        line, = ax.plot(res.u[:, b], res.v[:, b], ".", ms=1.5, label=lab)
        ax.plot(-res.u[:, b], -res.v[:, b], ".", ms=1.5, color=line.get_color())
    ax.set_aspect("equal")
    ax.set_xlabel("u (wavelengths)")
    ax.set_ylabel("v (wavelengths)")
    ax.set_title("u-v coverage")
    ax.legend(fontsize=7, markerscale=5)
    return ax.figure


def plot_image_psf(res):
    plt = _plt()
    l, m = res.l_deg * 60, res.m_deg * 60
    ext = [l[0], l[-1], m[0], m[-1]]
    fig, ax = plt.subplots(2, 2, figsize=(10, 9))
    th = np.linspace(0, 2 * np.pi, 200)
    r = res.cfg.source.diameter_deg * 30
    im0 = ax[0, 0].imshow(res.image, extent=ext, origin="lower", cmap="hot", vmin=0, vmax=1)
    ax[0, 0].plot(r * np.cos(th), r * np.sin(th), "c--", lw=1)
    ax[0, 0].set_title("Dirty image (Engine A)")
    im1 = ax[0, 1].imshow(res.psf, extent=ext, origin="lower", cmap="RdBu_r", vmin=-1, vmax=1)
    s = res.summary
    ax[0, 1].set_title(f"PSF  FWHM E-W {s['psf_fwhm_ew_arcmin']:.1f}', N-S {s['psf_fwhm_ns_arcmin']:.1f}'")
    for a, im in ((ax[0, 0], im0), (ax[0, 1], im1)):
        a.set_xlabel("E-W offset (arcmin)")
        a.set_ylabel("N-S offset (arcmin)")
        fig.colorbar(im, ax=a, shrink=0.8)
    ew_i, ns_i = center_cuts(res.image, l, m)
    ew_p, ns_p = center_cuts(res.psf, l, m)
    for a, x, img, psf, name in ((ax[1, 0], l, ew_i, ew_p, "E-W"), (ax[1, 1], m, ns_i, ns_p, "N-S")):
        a.plot(x, img, label="image")
        a.plot(x, psf, "--", label="PSF")
        a.axhline(0.5, color="gray", lw=0.6, ls=":")
        a.set_xlabel(f"{name} offset (arcmin)")
        a.legend(fontsize=8)
    fig.suptitle(res.array.summary())
    fig.tight_layout()
    return fig


def save_standard_figures(res, out_dir: str | Path) -> list[Path]:
    plt = _plt()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved = []
    for name, fn in (("track", plot_track), ("visibilities", plot_visibilities),
                     ("uv_coverage", plot_uv), ("image_psf", plot_image_psf)):
        fig = fn(res)
        p = out / f"{name}.png"
        fig.savefig(p, dpi=130, bbox_inches="tight")
        plt.close(fig)
        saved.append(p)
    return saved
