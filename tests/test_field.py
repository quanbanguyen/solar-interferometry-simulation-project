"""Field (GNU Radio PSD) reader and the effective-Tsys fit."""
from pathlib import Path

import numpy as np
import pytest

from interfsim.io.field_psd import FieldDay, parse_timestamp, read_field_csv, read_psd_day
from interfsim.validation import fit_effective_tsys

ROOT = Path(__file__).resolve().parents[1]


def _write_psd(folder: Path, stamp: str, level_db: float):
    f = np.linspace(609.5, 610.5, 512)
    db = np.full(512, level_db)
    db[:3] = 0.0                                   # band-edge padding rows
    np.savetxt(folder / f"{stamp}_PSD.csv", np.column_stack([f, db]), delimiter=",")


def test_timestamp_and_utc_offset(tmp_path):
    assert parse_timestamp("2025_03_20_12_03_15_7_PSD.csv") == np.datetime64("2025-03-20T12:03:15.700")
    _write_psd(tmp_path, "2025_03_20_12_00_10_0", -32.0)
    _write_psd(tmp_path, "2025_03_20_12_00_00_0", -32.1)
    d = read_psd_day(tmp_path, utc_offset_h=7)
    assert d.ut[0] == np.datetime64("2025-03-20T05:00:00.000")          # sorted, UTC+7 -> UT
    assert np.allclose(d.power_db, [-32.1, -32.0])                       # zero rows ignored
    assert d.freq_center_mhz == pytest.approx(610.0, abs=0.01)
    back = read_field_csv(d.to_csv(tmp_path / "out.csv"))
    assert np.array_equal(back.ut, d.ut) and back.utc_offset_h == 7


def test_fit_recovers_effective_tsys():
    """P = G (T_eff + T_sys x) + noise: the fit returns T_eff without knowing G."""
    rng = np.random.default_rng(0)
    ut = np.datetime64("2025-03-20T03:00") + np.arange(1500) * np.timedelta64(10, "s")
    x = 0.4 * np.exp(-0.5 * ((np.arange(1500) - 750) / 400.0) ** 2)     # Sun-to-noise, model T_sys
    t_sys, t_eff, gain = 150.0, 4000.0, 3.7e-4
    p = gain * (t_eff + t_sys * x) * (1 + 2e-4 * rng.standard_normal(x.size))
    field = FieldDay(ut.astype("datetime64[ms]"), 10 * np.log10(p), np.zeros(x.size), 610.0, 7.0)
    out = fit_effective_tsys(field, ut, x, t_sys, flux_sfu=np.full(x.size, 70.0))
    assert out["field_t_sys_eff_k"] == pytest.approx(t_eff, rel=0.03)
    assert out["field_corr_coef"] > 0.9
    assert 0 < out["field_min_detectable_sfu_3sigma"] < 70


@pytest.mark.skipif(not (ROOT / "data/field/hoa_lac_610MHz_psd/2025-03-20.csv").exists(),
                    reason="field light curve missing")
def test_shipped_field_day_is_in_ut():
    d = read_field_csv(ROOT / "data/field/hoa_lac_610MHz_psd/2025-03-20.csv")
    h = d.hours_ut()
    assert 2.9 < h[0] < 3.1 and 6.9 < h[-1] < 7.1                      # 10:00-14:00 Vietnam time
    assert 4.0 < h[np.argmax(d.power_db)] < 6.0                         # maximum near transit (05:03 UT)
