from pathlib import Path

import numpy as np
import pytest

from interfsim.pipeline import PipelineConfig, run_pipeline

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "configs" / "thesis_case1_20250320.toml"


@pytest.mark.skipif(not (ROOT / "data/rstn/learmonth/20-3-2025.txt").exists(), reason="RSTN data missing")
def test_pipeline_smoke(tmp_path):
    cfg = PipelineConfig.from_toml(CFG)
    cfg.observation.n_samples = 3000
    cfg.imaging.grid = 64
    cfg.output.dir = str(tmp_path)
    cfg.output.figures = False
    res = run_pipeline(cfg, verbose=False)
    s = res.summary
    assert res.V.shape == (3000, 4)
    assert s["time_mapping"] == "ut" and -70 < s["hour_angle_range_deg"][0] < -60
    assert abs(s["dec_deg"]) < 0.5
    assert np.isfinite(s["psf_fwhm_ew_arcmin"])
    assert np.isnan(s["psf_fwhm_ns_arcmin"])        # pure E-W array: no N-S resolution at dec 0
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "iq_array_stimulus.txt").exists()
