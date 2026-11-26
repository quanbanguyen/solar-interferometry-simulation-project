"""Moving burst model, centroid estimator and Cramer-Rao bound."""
from pathlib import Path

import numpy as np
import pytest

import interfsim as ix
from interfsim import burst as bu
from interfsim.imaging import fringe_stop

AM = bu.ARCMIN
ROOT = Path(__file__).resolve().parents[1]


def test_burst_kinematics_and_light_curve():
    b = bu.MovingBurst(t_peak_s=1000.0, peak_flux_sfu=500.0, rise_s=60.0, decay_s=300.0,
                       start_r_rsun=1.0, pa_deg=90.0, speed_km_s=bu.R_SUN_KM / 600.0)
    assert b.flux(1000.0) == pytest.approx(500.0)
    assert b.flux(1300.0) == pytest.approx(500.0 / np.e)
    # one solar radius in 600 s after onset, due east (PA 90)
    l, m = b.position(np.array([b.t_onset_s, b.t_onset_s + 600.0]))
    assert l[1] - l[0] == pytest.approx(bu.R_SUN_RAD, rel=1e-9)
    assert np.allclose(m, 0.0, atol=1e-12)
    assert b.angular_speed_arcmin_per_min == pytest.approx(bu.R_SUN_RAD / AM / 10.0)


def test_antenna_phase_accepts_time_varying_offsets():
    arr = ix.preset_dlite(8)
    obs = ix.Observation(21.0, -10.0, 610e6, np.linspace(-30, 30, 50))
    fixed = ix.antenna_phase(arr.positions_enu, obs, 0.003, -0.002)
    varying = ix.antenna_phase(arr.positions_enu, obs, np.full(50, 0.003), np.full(50, -0.002))
    assert np.allclose(fixed, varying)


LAYOUTS = [(lambda: ix.preset_dlite(8), True),
           (lambda: ix.make_array({"preset": "compact", "spacing": 8.0}), False)]


@pytest.mark.parametrize("layout, is_2d", LAYOUTS)
def test_centroid_error_reaches_cramer_rao_bound(layout, is_2d):
    """Engine B + white noise: the per-dump fit is unbiased and its rms error matches the CRB."""
    arr = layout()
    T, snr = 300, 20.0
    obs = ix.Observation(21.0, -10.0, 610e6, np.linspace(-30, 30, T))
    u, v, _ = ix.compute_uvw(arr.baseline_vectors_enu, obs)
    l0, m0 = 10 * AM, -6 * AM
    rng = np.random.default_rng(0)
    V = bu.vis_moving_gaussian(u, v, np.ones(T), np.full(T, l0), np.full(T, m0))
    V = V + (rng.standard_normal(V.shape) + 1j * rng.standard_normal(V.shape)) / snr
    tr = bu.track_centroid(u, v, V, 30 * AM)
    assert tr.is_2d.all() == is_2d
    err = tr.error(l0, m0)
    crb = np.array([bu.centroid_crb(u[k], v[k], snr) for k in range(T)])
    ratio = np.sqrt(np.mean(err ** 2) / np.mean(crb ** 2))
    assert 0.75 < ratio < 1.3


def test_engine_a_tracks_a_moving_burst():
    """Noise-free voltages of a moving point burst: every dump recovers the true position."""
    arr = ix.preset_dlite(8)
    T = 20000
    obs = ix.Observation(21.0, -10.0, 610e6, np.linspace(-10, 10, T))
    t = np.linspace(0.0, 20 / 15 * 3600, T)
    b = bu.MovingBurst(t_peak_s=1500.0, speed_km_s=1500.0, pa_deg=45.0)
    lt, mt = b.position(t)
    V = bu.burst_voltages(arr, obs, np.ones(T), lt, mt, seed=1)
    vis, cen = ix.correlate(V, arr, 50)
    u, v, w = ix.compute_uvw(arr.baseline_vectors_enu, obs.subset(cen))
    tr = bu.track_centroid(u, v, fringe_stop(vis, w), 40 * AM)
    assert np.max(tr.error(lt[cen], mt[cen])) < 0.5 * AM


def test_extended_burst_decorrelates():
    """A Gaussian burst much larger than the fringe spacing loses visibility amplitude."""
    arr = ix.from_enu([[0, 0], [60, 0]])
    obs = ix.Observation(21.0, 0.0, 610e6, np.zeros(40000))
    T = obs.H_deg.size
    V_pt = bu.burst_voltages(arr, obs, np.ones(T), np.zeros(T), np.zeros(T), 0.0, seed=2)
    V_ext = bu.burst_voltages(arr, obs, np.ones(T), np.zeros(T), np.zeros(T), np.radians(0.4), 9, seed=2)
    amp = [abs(np.mean(V[:, 0] * np.conj(V[:, 1]))) for V in (V_pt, V_ext)]
    q = 60 / obs.lam
    expected = np.exp(-(np.pi * np.radians(0.4)) ** 2 * q ** 2 / (4 * np.log(2)))
    assert amp[0] == pytest.approx(1.0, abs=0.03)
    assert amp[1] == pytest.approx(expected, abs=0.05)


@pytest.mark.skipif(not (ROOT / "data/rstn/learmonth/20-3-2025.txt").exists(), reason="RSTN data missing")
def test_pipeline_with_burst(tmp_path):
    from interfsim.pipeline import PipelineConfig, run_pipeline
    cfg = PipelineConfig.from_toml(ROOT / "configs" / "dlite_moving_burst.toml")
    cfg.observation.n_samples = 6000
    cfg.integration_bins = 5
    cfg.imaging.grid = 48
    cfg.output.dir = str(tmp_path)
    cfg.output.figures = False
    res = run_pipeline(cfg, verbose=False)
    s = res.summary
    assert s["burst_n_dumps_tracked"] >= 5
    assert s["burst_fraction_2d"] == 1.0
    assert np.isfinite(s["burst_centroid_rms_error_arcmin"])
    assert s["burst_centroid_crb_physical_rms_arcmin"] < s["burst_centroid_crb_rms_arcmin"]
    assert s["engineA_vs_engineB_image_rms_diff"] < 0.05
    assert "burst_l_true" in np.load(tmp_path / "products.npz").files
