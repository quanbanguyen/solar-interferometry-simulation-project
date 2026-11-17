import numpy as np
import pytest

import interfsim as ix
from interfsim import ephem
from interfsim.geometry import altaz_deg, source_dir_xyz, uv_basis_xyz


def test_uvw_east_west_baseline_at_transit():
    obs = ix.Observation(lat_deg=-22.22, dec_deg=0.0, fc_hz=610e6, H_deg=[0.0])
    u, v, w = ix.compute_uvw(np.array([[10.0, 0.0, 0.0]]), obs)
    assert u[0, 0] == pytest.approx(10.0 / obs.lam)
    assert v[0, 0] == pytest.approx(0.0, abs=1e-12)
    assert w[0, 0] == pytest.approx(0.0, abs=1e-12)


def test_uvw_preserves_baseline_length():
    rng = np.random.default_rng(0)
    b = rng.normal(size=(5, 3)) * 20
    obs = ix.Observation(35.0, 12.0, 610e6, np.linspace(-80, 80, 7))
    u, v, w = ix.compute_uvw(b, obs)
    assert np.allclose(np.sqrt(u**2 + v**2 + w**2), np.linalg.norm(b, axis=1) / obs.lam)


def test_uvw_frame_is_orthonormal():
    H = np.radians(np.linspace(-90, 90, 5))
    s = source_dir_xyz(H, 0.3)
    eu, ev = uv_basis_xyz(H, 0.3)
    for a, c in ((s, eu), (s, ev), (eu, ev)):
        assert np.allclose(np.sum(a * c, axis=1), 0)
    assert np.allclose(np.linalg.norm(eu, axis=1), 1)


def test_altaz_transit_and_zenith():
    obs = ix.Observation(lat_deg=-22.22, dec_deg=-22.22, H_deg=[0.0, 30.0])
    az, el = altaz_deg(obs)
    assert el[0] == pytest.approx(90.0)
    assert 180 < az[1] < 360          # west of the meridian after transit


def test_ephemeris_equinox_and_noon():
    ut = np.array(["2025-03-20T09:01:00"], dtype="datetime64[s]")   # March equinox
    dec, _ = ephem.solar_position(ut)
    assert abs(dec[0]) < 0.05
    # local solar noon at Learmonth on that day is ~04:31 UT
    ut = np.arange(np.datetime64("2025-03-20T04:00"), np.datetime64("2025-03-20T05:00"),
                   np.timedelta64(1, "m"))
    H, _ = ephem.sun_hour_angle_dec(ut, ephem.LEARMONTH.lon_deg)
    noon = ut[np.argmin(np.abs(H))]
    assert np.datetime64("2025-03-20T04:28") <= noon <= np.datetime64("2025-03-20T04:35")


def test_array_builders():
    a = ix.preset_compact()
    assert a.n_ant == 4 and a.n_baselines == 6
    assert np.allclose(sorted(a.baseline_lengths), [8, 8, 8, 16, 16, 24])
    assert a.unique_baseline_directions() == 1
    assert ix.preset_dlite(8).unique_baseline_directions() == 6
    assert ix.preset_cross4(8).unique_baseline_directions() < 6
    assert ix.make_array({"type": "linear", "n": 3, "spacing": 5}).n_ant == 3
    with pytest.raises(ValueError):
        ix.from_enu([[0, 0]])
