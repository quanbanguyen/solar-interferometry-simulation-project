"""End-to-end simulation driven by a TOML configuration file.

    RSTN flux -> observation track -> primary beam -> radiometry ->
    per-antenna voltages (Engine A) -> correlator -> (u,v,w) -> dirty image/PSF
    (+ FPGA hex export, forward-model cross-check, hardware comparison)

Every parameter lives in the config (see configs/*.toml); nothing is read from
notebook globals or absolute paths.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from . import burst as burst_mod
from . import ephem
from .array import ArrayConfig, make_array
from .beam import Mount, TabulatedBeam, load_beam
from .constants import SUN_DIAMETER_DEG
from .correlator import correlate, fringe_rotation_per_dump
from .geometry import Observation, altaz_deg, compute_uvw
from .imaging import forward_visibilities, fringe_stop, make_dirty_image, synthesized_beam
from .io.fpga import quantize_iq, write_hex, write_metadata
from .io.rstn import RSTNDay, read_rstn_day
from .metrics import dynamic_range, peak_position, psf_fwhm
from .signal import effective_area, noise_power, power_to_vrms, simulate_voltages, snr_db, source_power
from .sky import disk_components, sky_visibilities

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

SITES = {"learmonth": ephem.LEARMONTH, "hoa_lac": ephem.HOA_LAC}


# ── configuration ───────────────────────────────────────────────────────────
@dataclass
class ObservationCfg:
    rstn_file: str = "data/rstn/learmonth/20-3-2025.txt"
    freq_mhz: float = 610.0
    site: str = "learmonth"
    lat_deg: float | None = None            # override the site
    lon_deg: float | None = None
    time_mapping: str = "ut"                # "ut" (ephemeris) or "stretch" (thesis v1)
    dec_deg: float | None = None            # only used with "stretch"; None = ephemeris
    min_elevation_deg: float = 0.0
    n_samples: int = 50_000


@dataclass
class ReceiverCfg:
    bw_hz: float = 1e6
    t_sys_k: float = 150.0
    r_load_ohm: float = 75.0
    pol_factor: float = 0.5


@dataclass
class AntennaCfg:
    beam_file: str = "data/antenna/beams/UFRAME_primary_beam_610MHz.npz"
    boresight_axis: str = "+y"
    element_axis: str = "+x"
    pointing_az_deg: float = 0.0
    pointing_el_deg: float = 90.0
    element_az_deg: float = 0.0


@dataclass
class SourceCfg:
    model: str = "point"                    # "point" or "disk"
    diameter_deg: float = SUN_DIAMETER_DEG
    disk_n_across: int = 15


@dataclass
class BurstCfg:
    """Synthetic moving burst injected on top of the measured (quiet + real) solar flux."""
    enabled: bool = False
    peak_ut: str = "05:00:00"               # HH:MM:SS on the RSTN day
    peak_flux_sfu: float = 1000.0
    rise_s: float = 120.0
    decay_s: float = 600.0
    start_r_rsun: float = 1.1
    pa_deg: float = 90.0                    # position angle of the radial path, N through E
    speed_km_s: float = 500.0               # plane-of-sky speed
    fwhm_arcmin: float = 0.0                # 0 = point source
    n_across: int = 5                       # components per axis for an extended burst
    search_radius_arcmin: float = 40.0      # centroid search box half-width (keep < fringe spacing)
    subtract_quiet_sun: bool = True         # remove the quiet-Sun model before fitting
    track_threshold: float = 0.2            # fit dumps where burst flux > threshold * peak


@dataclass
class ImagingCfg:
    fov_deg: float = 3.0
    grid: int = 256
    forward_model_check: bool = True


@dataclass
class ComparisonCfg:
    enabled: bool = False
    measured_noise_db: float = 0.0
    measured_peak_db: float = 0.0
    hour_angle_window_deg: float = 30.0
    field_csv: str = ""                     # field light curve (data/field/hoa_lac_610MHz_psd/*.csv)


@dataclass
class OutputCfg:
    dir: str = "results/run"
    fpga_hex: bool = False
    fpga_bits: int = 16
    figures: bool = True
    save_npz: bool = True


@dataclass
class PipelineConfig:
    name: str = "run"
    seed: int = 42
    integration_bins: int = 50
    array: dict = field(default_factory=lambda: {"preset": "compact"})
    observation: ObservationCfg = field(default_factory=ObservationCfg)
    receiver: ReceiverCfg = field(default_factory=ReceiverCfg)
    antenna: AntennaCfg = field(default_factory=AntennaCfg)
    source: SourceCfg = field(default_factory=SourceCfg)
    burst: BurstCfg = field(default_factory=BurstCfg)
    imaging: ImagingCfg = field(default_factory=ImagingCfg)
    comparison: ComparisonCfg = field(default_factory=ComparisonCfg)
    output: OutputCfg = field(default_factory=OutputCfg)
    base_dir: str = "."                     # relative paths are resolved against this

    @classmethod
    def from_dict(cls, d: dict, base_dir: str | Path = ".") -> PipelineConfig:
        sub = {"observation": ObservationCfg, "receiver": ReceiverCfg, "antenna": AntennaCfg,
               "source": SourceCfg, "burst": BurstCfg, "imaging": ImagingCfg, "comparison": ComparisonCfg,
               "output": OutputCfg}
        kw = {k: (sub[k](**v) if k in sub else v) for k, v in d.items()}
        return cls(base_dir=str(base_dir), **kw)

    @classmethod
    def from_toml(cls, path: str | Path, base_dir: str | Path | None = None) -> PipelineConfig:
        path = Path(path)
        with open(path, "rb") as f:
            d = tomllib.load(f)
        # configs/ lives one level below the repository root
        return cls.from_dict(d, base_dir or path.resolve().parent.parent)

    def path(self, p: str) -> Path:
        q = Path(p)
        return q if q.is_absolute() else Path(self.base_dir) / q


# ── results ─────────────────────────────────────────────────────────────────
@dataclass
class PipelineResult:
    cfg: PipelineConfig
    array: ArrayConfig
    beam: TabulatedBeam
    obs: Observation
    ut: np.ndarray
    flux_sfu: np.ndarray
    beam_power: np.ndarray
    p_signal_w: np.ndarray
    p_noise_w: float
    V: np.ndarray
    vis: np.ndarray
    centers: np.ndarray
    u: np.ndarray
    v: np.ndarray
    w: np.ndarray
    image: np.ndarray
    psf: np.ndarray
    l_deg: np.ndarray
    m_deg: np.ndarray
    summary: dict
    forward_image: np.ndarray | None = None
    burst: dict | None = None

    def save(self, out_dir: str | Path | None = None) -> Path:
        out = Path(out_dir) if out_dir else self.cfg.path(self.cfg.output.dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "summary.json").write_text(json.dumps(self.summary, indent=2), encoding="utf-8")
        (out / "config_used.json").write_text(json.dumps(asdict(self.cfg), indent=2), encoding="utf-8")
        if self.cfg.output.save_npz:
            np.savez_compressed(out / "products.npz", vis=self.vis, u=self.u, v=self.v, w=self.w,
                                image=self.image, psf=self.psf, l_deg=self.l_deg, m_deg=self.m_deg,
                                H_deg=self.obs.H_deg, flux_sfu=self.flux_sfu,
                                beam_power=self.beam_power, positions_enu=self.array.positions_enu,
                                **{f"burst_{k}": a for k, a in (self.burst or {}).items()})
        return out


# ── steps ───────────────────────────────────────────────────────────────────
def _site(cfg: ObservationCfg) -> ephem.Site:
    s = SITES[cfg.site.lower()]
    return ephem.Site(s.name, cfg.lat_deg if cfg.lat_deg is not None else s.lat_deg,
                      cfg.lon_deg if cfg.lon_deg is not None else s.lon_deg, s.height_m)


def _longest_run(mask: np.ndarray) -> slice:
    best, start = (0, 0), None
    for i, v in enumerate(np.append(mask, False)):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    return slice(*best)


def build_track(day: RSTNDay, cfg: ObservationCfg):
    """Resample the longest daylight segment onto n_samples points.

    Returns (ut, flux_sfu, Observation). With time_mapping="ut" the hour angle
    and declination come from the solar ephemeris at the real UT of each
    sample; "stretch" reproduces thesis v1, which spread the daylight block
    uniformly over H = -90..+90 deg.
    """
    site = _site(cfg)
    from .ephem import sun_elevation_deg
    up = sun_elevation_deg(day.ut, site) > cfg.min_elevation_deg
    seg = day.select(np.arange(day.ut.size)[_longest_run(up)])    # short gaps are interpolated
    t_s = (seg.ut - seg.ut[0]).astype("timedelta64[ms]").astype(float) / 1e3
    flux = seg.channel(cfg.freq_mhz)
    ok = ~np.isnan(flux)
    t_grid = np.linspace(t_s[0], t_s[-1], cfg.n_samples)
    flux_grid = np.clip(np.interp(t_grid, t_s[ok], flux[ok]), 0.0, None)
    ut = seg.ut[0] + (t_grid * 1e3).astype("timedelta64[ms]")
    fc = cfg.freq_mhz * 1e6
    if cfg.time_mapping == "ut":
        H, dec = ephem.sun_hour_angle_dec(ut, site.lon_deg)
        obs = Observation(site.lat_deg, float(np.median(dec)), fc, H)
    elif cfg.time_mapping == "stretch":
        dec = cfg.dec_deg
        if dec is None:
            dec = float(np.median(ephem.sun_hour_angle_dec(ut, site.lon_deg)[1]))
        obs = Observation(site.lat_deg, dec, fc, np.linspace(-90.0, 90.0, cfg.n_samples))
    else:
        raise ValueError(f"time_mapping must be 'ut' or 'stretch', got {cfg.time_mapping!r}")
    return ut, flux_grid, obs


def run_pipeline(cfg: PipelineConfig, verbose: bool = True) -> PipelineResult:
    log = print if verbose else (lambda *a, **k: None)
    oc, rc = cfg.observation, cfg.receiver

    day = read_rstn_day(cfg.path(oc.rstn_file))
    ut, flux, obs = build_track(day, oc)
    log(f"[track] {ut[0]} .. {ut[-1]} UT | H {obs.H_deg[0]:.1f}..{obs.H_deg[-1]:.1f} deg | "
        f"dec {obs.dec_deg:.2f} deg | mean flux {flux.mean():.1f} SFU")

    ac = cfg.antenna
    mount = Mount(ac.boresight_axis, ac.element_axis, ac.pointing_az_deg,
                  ac.pointing_el_deg, ac.element_az_deg)
    beam = load_beam(cfg.path(ac.beam_file), mount)
    az, el = altaz_deg(obs)
    beam_power = beam.power_altaz(az, el)
    a_eff = effective_area(beam.gain_max_dBi, obs.lam)

    p_sig = source_power(flux, a_eff, rc.bw_hz, rc.pol_factor) * beam_power
    p_n = noise_power(rc.t_sys_k, rc.bw_hz)
    env = power_to_vrms(p_sig, rc.r_load_ohm)
    v_noise = float(power_to_vrms(p_n, rc.r_load_ohm))
    log(f"[radiometry] G={beam.gain_max_dBi:.2f} dBi, Ae={a_eff:.4f} m^2, "
        f"peak SNR/sample={float(snr_db(p_sig.max(), p_n)):.2f} dB")

    array = make_array(cfg.array)
    comps = None
    if cfg.source.model == "disk":
        comps = disk_components(np.radians(cfg.source.diameter_deg), cfg.source.disk_n_across)
    elif cfg.source.model != "point":
        raise ValueError("source.model must be 'point' or 'disk'")
    V = simulate_voltages(array, obs, env, v_noise / np.sqrt(2), seed=cfg.seed, components=comps)

    t_s = (ut - ut[0]).astype("timedelta64[ms]").astype(float) / 1e3
    burst = p_burst = l_b = m_b = None
    if cfg.burst.enabled:
        burst, p_burst, l_b, m_b = inject_burst(cfg, ut, t_s, a_eff, beam_power)
        V = V + burst_mod.burst_voltages(array, obs, power_to_vrms(p_burst, rc.r_load_ohm), l_b, m_b,
                                         np.radians(cfg.burst.fwhm_arcmin / 60), cfg.burst.n_across,
                                         seed=cfg.seed + 1)
        log(f"[burst] peak {cfg.burst.peak_flux_sfu:.0f} SFU at {cfg.burst.peak_ut} UT, "
            f"{cfg.burst.speed_km_s:.0f} km/s ({burst.angular_speed_arcmin_per_min:.2f} arcmin/min) "
            f"towards PA {cfg.burst.pa_deg:.0f} deg")

    vis, centers = correlate(V, array, cfg.integration_bins)
    obs_c = obs.subset(centers)
    u, v, w = compute_uvw(array.baseline_vectors_enu, obs_c)
    ic = cfg.imaging
    image, l_deg, m_deg = make_dirty_image(u, v, w, vis, ic.fov_deg, ic.grid, do_fringe_stop=True)
    psf, _, _ = synthesized_beam(u, v, w, ic.fov_deg, ic.grid)
    l_am, m_am = l_deg * 60, m_deg * 60
    fwhm_ew, fwhm_ns = psf_fwhm(psf, l_am, m_am)
    pk = peak_position(image, l_am, m_am)
    r_sun_am = cfg.source.diameter_deg * 30

    dt = (ut[-1] - ut[0]).astype("timedelta64[ms]").astype(float) / 1e3 / (oc.n_samples - 1)
    summary = {
        "name": cfg.name,
        "array": array.summary(),
        "n_unique_baseline_directions": array.unique_baseline_directions(),
        "ut_start": str(ut[0]), "ut_end": str(ut[-1]),
        "hour_angle_range_deg": [float(obs.H_deg[0]), float(obs.H_deg[-1])],
        "dec_deg": obs.dec_deg, "lat_deg": obs.lat_deg, "time_mapping": oc.time_mapping,
        "sample_interval_s": dt, "dump_time_s": dt * cfg.integration_bins,
        "max_fringe_rotation_per_dump_rad": float(fringe_rotation_per_dump(w).max()),
        "flux_mean_sfu": float(flux.mean()), "flux_max_sfu": float(flux.max()),
        "beam_gain_dBi": beam.gain_max_dBi, "a_eff_m2": a_eff,
        "p_noise_w": p_n, "v_noise_rms_v": v_noise,
        "snr_peak_db_per_sample": float(snr_db(p_sig.max(), p_n)),
        "source_model": cfg.source.model, "pol_factor": rc.pol_factor,
        "psf_fwhm_ew_arcmin": fwhm_ew, "psf_fwhm_ns_arcmin": fwhm_ns,
        "image_peak_arcmin": pk,
        "image_dynamic_range": dynamic_range(image, l_am, m_am, max(r_sun_am, fwhm_ew)),
    }

    fwd_img = None
    if ic.forward_model_check:
        sky = {"type": "disk" if cfg.source.model == "disk" else "point",
               "diameter_rad": np.radians(cfg.source.diameter_deg), "sources": [(1.0, 0.0, 0.0)]}
        _, _, _, Vf = forward_visibilities(array, obs_c, sky, time_weight=p_sig[centers])
        if burst is not None:
            Vf = Vf + burst_mod.vis_moving_gaussian(u, v, p_burst[centers], l_b[centers], m_b[centers],
                                                    np.radians(cfg.burst.fwhm_arcmin / 60))
        fwd_img, _, _ = make_dirty_image(u, v, w, Vf, ic.fov_deg, ic.grid, do_fringe_stop=False)
        summary["engineA_vs_engineB_image_rms_diff"] = float(np.sqrt(np.mean((image - fwd_img) ** 2)))

    if cfg.comparison.enabled:
        summary.update(hardware_comparison(obs, p_sig, p_n, cfg.comparison))
    if cfg.comparison.field_csv:
        from .io.field_psd import read_field_csv
        from .validation import fit_effective_tsys
        field = read_field_csv(cfg.path(cfg.comparison.field_csv))
        summary.update(fit_effective_tsys(field, ut, p_sig / p_n, rc.t_sys_k, flux))
        log(f"[field] T_sys,eff = {summary.get('field_t_sys_eff_k', float('nan')):.0f} "
            f"+- {summary.get('field_t_sys_eff_err_k', float('nan')):.0f} K, "
            f"r = {summary.get('field_corr_coef', float('nan')):.2f}")

    burst_products = None
    if burst is not None:
        burst_summary, burst_products = track_burst(cfg, burst, t_s, centers, u, v, w, vis,
                                                    p_sig, p_burst, p_n, l_b, m_b)
        summary.update(burst_summary)
        log(f"[burst] {burst_summary['burst_n_dumps_tracked']} dumps tracked, centroid rms error "
            f"{burst_summary['burst_centroid_rms_error_arcmin']:.2f} arcmin "
            f"(Cramer-Rao {burst_summary['burst_centroid_crb_rms_arcmin']:.2f})")

    result = PipelineResult(cfg, array, beam, obs, ut, flux, beam_power, p_sig, p_n, V, vis,
                            centers, u, v, w, image, psf, l_deg, m_deg, summary, fwd_img,
                            burst_products)

    out = cfg.path(cfg.output.dir)
    if cfg.output.fpga_hex:
        export_fpga(result, out)
    if cfg.output.figures:
        from .plotting import save_standard_figures
        save_standard_figures(result, out / "figures")
    result.save(out)
    log(f"[done] outputs in {out}")
    return result


def inject_burst(cfg: PipelineConfig, ut, t_s, a_eff, beam_power):
    """Build the MovingBurst from the config; return it with its received power [W] and
    its track (l, m) [rad] per sample."""
    bc, rc = cfg.burst, cfg.receiver
    day = ut[0].astype("datetime64[D]")
    t_peak = (np.datetime64(f"{day}T{bc.peak_ut}") - ut[0]).astype("timedelta64[ms]").astype(float) / 1e3
    if not t_s[0] <= t_peak <= t_s[-1]:
        raise ValueError(f"burst.peak_ut {bc.peak_ut} is outside the track {ut[0]} .. {ut[-1]}")
    burst = burst_mod.MovingBurst(t_peak, bc.peak_flux_sfu, bc.rise_s, bc.decay_s, bc.start_r_rsun,
                                  bc.pa_deg, bc.speed_km_s, bc.fwhm_arcmin)
    p_burst = source_power(burst.flux(t_s), a_eff, rc.bw_hz, rc.pol_factor) * beam_power
    l_b, m_b = burst.position(t_s)
    return burst, p_burst, l_b, m_b


def track_burst(cfg: PipelineConfig, burst, t_s, centers, u, v, w, vis, p_sig, p_burst, p_n,
                l_b, m_b) -> tuple[dict, dict]:
    """Fit the burst position in every dump where it is bright; compare with the true
    track and with the Cramer-Rao bound. Returns (summary entries, per-dump products)."""
    bc, R = cfg.burst, cfg.receiver.r_load_ohm
    am = burst_mod.ARCMIN
    vis_ph = fringe_stop(vis, w)
    if bc.subtract_quiet_sun:
        # ideal subtraction (the model is known in a simulation); with real data use a
        # pre-burst average of the visibilities instead
        quiet = ({"type": "disk", "diameter_rad": np.radians(cfg.source.diameter_deg)}
                 if cfg.source.model == "disk" else {"type": "point", "sources": [(1.0, 0.0, 0.0)]})
        vis_ph = vis_ph - R * p_sig[centers][:, None] * sky_visibilities(quiet, u, v)
    sel = np.flatnonzero(burst.flux(t_s[centers]) >= bc.track_threshold * burst.peak_flux_sfu)
    if sel.size < 2:
        return {"burst_n_dumps_tracked": int(sel.size), "burst_centroid_rms_error_arcmin": np.nan,
                "burst_centroid_crb_rms_arcmin": np.nan}, {}
    c = centers[sel]
    lt, mt = l_b[c], m_b[c]
    tr = burst_mod.track_centroid(u[sel], v[sel], vis_ph[sel], np.radians(bc.search_radius_arcmin / 60))
    err = tr.error(lt, mt)
    snr = burst_mod.visibility_snr(p_burst[c], p_sig[c] + p_burst[c] + p_n, cfg.integration_bins)
    crb = np.array([burst_mod.centroid_crb(u[k], v[k], s) for k, s in zip(sel, snr, strict=True)])
    # The simulation averages only `integration_bins` samples per dump; a real receiver
    # averages B * tau_dump independent samples in the same time. Scale the bound to that.
    dump_s = (t_s[-1] - t_s[0]) / (t_s.size - 1) * cfg.integration_bins
    n_phys = cfg.receiver.bw_hz * dump_s
    crb_phys = crb * np.sqrt(cfg.integration_bins / n_phys)

    tt = t_s[c]
    km_per_rad = burst_mod.R_SUN_KM / burst_mod.R_SUN_RAD
    if tr.is_2d.all():
        speed_fit = np.hypot(np.polyfit(tt, tr.l, 1)[0], np.polyfit(tt, tr.m, 1)[0]) * km_per_rad
        speed_true = bc.speed_km_s
    else:     # 1-D array: only the projection on the baseline axis is measured
        ax = tr.axis.mean(axis=0)
        ax /= np.hypot(*ax)
        speed_fit = abs(np.polyfit(tt, tr.along, 1)[0]) * km_per_rad
        pa = np.radians(bc.pa_deg)
        speed_true = bc.speed_km_s * abs(ax[0] * np.sin(pa) + ax[1] * np.cos(pa))
    summary = {
        "burst_peak_flux_sfu": bc.peak_flux_sfu,
        "burst_peak_snr_db_per_sample": float(10 * np.log10(p_burst.max() / p_n)),
        "burst_n_dumps_tracked": int(sel.size),
        "burst_fraction_2d": float(tr.is_2d.mean()),
        "burst_centroid_rms_error_arcmin": float(np.sqrt(np.mean(err ** 2)) / am),
        "burst_centroid_median_error_arcmin": float(np.median(err) / am),
        "burst_centroid_crb_rms_arcmin": float(np.sqrt(np.mean(crb ** 2)) / am),
        "burst_centroid_crb_physical_rms_arcmin": float(np.sqrt(np.mean(crb_phys ** 2)) / am),
        "burst_physical_samples_per_dump": float(n_phys),
        "burst_true_motion_arcmin": float(np.hypot(lt[-1] - lt[0], mt[-1] - mt[0]) / am),
        "burst_speed_true_km_s": float(speed_true),
        "burst_speed_fit_km_s": float(speed_fit),
        "burst_speed_is_projected": bool(not tr.is_2d.all()),
    }
    products = {"t_s": tt, "l_true": lt, "m_true": mt, "l_fit": tr.l, "m_fit": tr.m,
                "along_fit": tr.along, "axis": tr.axis, "is_2d": tr.is_2d, "error_rad": err,
                "crb_rad": crb, "snr_vis": snr, "flux_sfu": burst.flux(tt)}
    return summary, products


def hardware_comparison(obs: Observation, p_sig: np.ndarray, p_noise: float,
                        cc: ComparisonCfg) -> dict:
    """Solar excess above the noise floor, 10 log10(1 + P_sig/P_n), simulation vs measurement.
    Independent of the (unknown) absolute receiver gain."""
    mask = np.abs(obs.H_deg) <= cc.hour_angle_window_deg
    if not mask.any():
        return {"comparison_error": "no samples inside the hour-angle window"}
    sim_peak = 10 * np.log10(1 + p_sig[mask].max() / p_noise)
    sim_avg = 10 * np.log10(1 + p_sig[mask].mean() / p_noise)
    meas = cc.measured_peak_db - cc.measured_noise_db
    return {"excess_sim_peak_db": float(sim_peak), "excess_sim_avg_db": float(sim_avg),
            "excess_measured_db": float(meas),
            "excess_ratio_linear": float((10 ** (sim_avg / 10) - 1) / max(10 ** (meas / 10) - 1, 1e-30))}


def export_fpga(result: PipelineResult, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    bits = result.cfg.output.fpga_bits
    I, Q, scale = quantize_iq(result.V, bits)
    path = write_hex(out_dir / "iq_array_stimulus.txt", I, Q, bits)
    s, rc = result.summary, result.cfg.receiver
    write_metadata(out_dir / "iq_array_stimulus_meta.txt", {
        "n_samples": I.shape[0], "num_antennas": I.shape[1], "array": result.array.name,
        "fc_hz": f"{result.obs.fc_hz:.6e}", "bw_hz": f"{rc.bw_hz:.6e}",
        "t_sys_k": rc.t_sys_k, "r_load_ohm": rc.r_load_ohm, "a_eff_m2": f"{s['a_eff_m2']:.6e}",
        "bits": bits, "scale_factor": f"{scale:.10e}",
        "v_noise_rms_v": f"{s['v_noise_rms_v']:.10e}",
        "noise_rms_lsb": f"{s['v_noise_rms_v'] * scale:.2f}",
        "snr_peak_db_per_sample": f"{s['snr_peak_db_per_sample']:.4f}",
        "sample_interval_s": f"{s['sample_interval_s']:.6f}",
        "format": f"(I Q) x {I.shape[1]} antennas, {bits}-bit two's complement hex",
    })
    return path
