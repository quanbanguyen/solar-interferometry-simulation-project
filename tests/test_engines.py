"""Physics consistency: voltage engine (A) vs forward model (B) vs analytic results."""
import numpy as np
import pytest
from scipy.special import j1

import interfsim as ix
from interfsim.correlator import fringe_rotation_per_dump
from interfsim.imaging import fringe_stop
from interfsim.metrics import fwhm_main_lobe, peak_position


def _obs(T=4000):
    return ix.Observation(lat_deg=-22.22, dec_deg=0.0, fc_hz=610e6, H_deg=np.linspace(-60, 60, T))


def test_point_source_engine_a_matches_engine_b():
    """Noise-free Engine A, after fringe stopping, equals the forward model (V = |s|^2).

    The residual phase is time-average smearing: the fringe keeps rotating
    during each 50-sample dump while the stochastic source weights the samples
    unevenly. It must stay small for these short baselines.
    """
    arr, obs = ix.preset_dlite(8), _obs(T=40000)     # ~0.25 rad fringe rotation per dump
    V = ix.simulate_voltages(arr, obs, amplitude_envelope=1.0, noise_sigma=0.0, seed=1)
    vis, cen = ix.correlate(V, arr, 50)
    u, v, w = ix.compute_uvw(arr.baseline_vectors_enu, obs.subset(cen))
    assert fringe_rotation_per_dump(w).max() < 0.3
    stopped = fringe_stop(vis, w)
    assert np.abs(np.angle(stopped)).max() < 0.1
    assert np.abs(np.angle(stopped)).mean() < 0.02
    # a constant-modulus source removes the random weighting; only smearing remains
    V1 = ix.simulate_voltages(arr, obs, 1.0, 0.0, source_process=np.ones(obs.H_deg.size))
    vis1, _ = ix.correlate(V1, arr, 1)
    _, _, w1 = ix.compute_uvw(arr.baseline_vectors_enu, obs)
    assert np.allclose(fringe_stop(vis1, w1), 1.0, atol=1e-9)


def test_extended_disk_decorrelates_like_jinc():
    """Engine A with an extended disk reproduces van Cittert-Zernike: |V|/V0 = jinc(q)."""
    diam = np.radians(0.53)
    arr = ix.from_enu([[0, 0], [20, 0], [45, 0], [70, 0]])
    obs = ix.Observation(-22.22, 0.0, 610e6, np.zeros(60000))     # fixed H: stationary statistics
    comps = ix.disk_components(diam, n_across=21)
    V = ix.simulate_voltages(arr, obs, 1.0, 0.0, seed=3, components=comps)
    vis = (V[:, [i for i, _ in arr.pairs]] * np.conj(V[:, [j for _, j in arr.pairs]])).mean(0)
    q = arr.baseline_lengths / obs.lam
    x = np.pi * diam * q
    jinc = np.abs(2 * j1(x) / x)
    # discretised disk + finite samples: agree to a few percent of the zero-spacing power
    assert np.allclose(np.abs(vis), jinc, atol=0.05)


def test_dirty_image_recovers_offset_point_source():
    arr = ix.preset_extended()
    obs = ix.Observation(-22.22, 0.0, 610e6, np.linspace(-60, 60, 120))
    l0, m0 = np.radians(0.4), np.radians(-0.25)
    u, v, w, V = ix.forward_visibilities(arr, obs, {"type": "point", "sources": [(1.0, l0, m0)]})
    img, l, m = ix.make_dirty_image(u, v, w, V, fov_deg=2.0, grid=161, do_fringe_stop=False)
    pl, pm = peak_position(img, l, m)
    assert pl == pytest.approx(0.4, abs=0.02)
    assert pm == pytest.approx(-0.25, abs=0.02)


def test_unnormalised_image_has_flux_units():
    arr = ix.preset_extended()
    obs = ix.Observation(-22.22, 0.0, 610e6, np.linspace(-30, 30, 40))
    u, v, w, V = ix.forward_visibilities(arr, obs, {"type": "point", "sources": [(3.0, 0, 0)]})
    img, _, _ = ix.make_dirty_image(u, v, w, V, fov_deg=1.0, grid=65, do_fringe_stop=False,
                                    normalize=False)
    assert img.max() == pytest.approx(3.0, rel=1e-3)


def test_fwhm_main_lobe_ignores_sidelobes():
    x = np.linspace(-10, 10, 2001)
    sigma = 1.0
    p = np.exp(-x**2 / (2 * sigma**2)) + 0.8 * np.exp(-(x - 6) ** 2 / 0.5)   # strong sidelobe
    assert fwhm_main_lobe(p, x) == pytest.approx(2.3548 * sigma, rel=1e-3)
    assert np.isnan(fwhm_main_lobe(np.ones_like(x), x))


def test_correlator_shapes():
    V = np.ones((1003, 3), complex)
    vis, cen = ix.correlate(V, ix.from_enu([[0, 0], [1, 0], [0, 1]]), 100)
    assert vis.shape == (10, 3) and cen[0] == 50
