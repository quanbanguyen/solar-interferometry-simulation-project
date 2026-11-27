# Code audit of the thesis pipeline (v1 → v0.2)

Scope: `notebooks/legacy/the_newest_heart_of_project.ipynb` (21 cells) and the helper
modules it imports (`legacy/v1/interfsim.py`, `sws_to_csv.py`, `primary_beam.py`,
`parse_nec_out.py`). Every finding below was checked by re-running the original v1
cells on the same input data (`data/rstn/learmonth/20-3-2025.txt`) and comparing with the
refactored package `src/interfsim` (v0.2).

Severity: **Critical** = a reported number is wrong · **High** = a physical assumption
changes results noticeably · **Medium** = a diagnostic or model limitation that can mislead ·
**Low** = engineering/reproducibility.

## 1. Findings

| # | Severity | Finding | Where (v1) | Fix in v0.2 |
|---|---|---|---|---|
| A1 | Critical | **Peak SNR is overstated by 18.75 dB.** The code computes `10 log10(max(P_signal) * R_load / P_noise)`, multiplying a power ratio by 75 Ω. The re-run prints *"Peak SNR transit: 18.4 dB \| V_sig_peak=0.38 µV, V_noise=0.39 µV"*, i.e. the signal is *below* the noise. Correct value: −0.4 dB. The wrong value was written to `iq_array_stimulus_meta.txt` (`snr_peak_db = 18.3556`). The thesis equation (ch4, Eq. snr-peak) is correct; only the code is wrong. | Cell A | `signal.snr_db(p_sig, p_noise)` (no resistance); test `test_radiometry_values` |
| A2 | High | **The single-polarisation factor ½ is missing.** The thesis states P_sig = ½ A_e S Δν (ch4 l.403), but the code uses S·A_e·Δν: +3 dB of signal. | Cell A | `source_power(..., pol_factor=0.5)`; configurable |
| A3 | High | **The RSTN time base is misread.** Column 1 is the UT time `HHMMSS`, not a sample index. The daylight block 00:00–10:40 UT (08:00–18:40 local) is stretched linearly over H = −90…+90°. Real solar transit at Learmonth is ≈04:31 UT, which v1 maps to H ≈ −14°. The real track is H = −68…+90° (the Sun had already risen when the UT day starts). Flux features (bursts) therefore get the wrong beam weighting and fringe phase. | `sws_to_csv.load_day`, Cell A | `io.rstn.read_rstn_day` parses UT; `ephem.sun_hour_angle_dec` (NOAA algorithm) gives H and δ per sample. `time_mapping = "stretch"` kept to reproduce v1 |
| A4 | High | **Thesis Table 5.7 cannot be reproduced from the final notebook.** The table gives simulated excess 0.586 dB (P/Pn = 14.3 %), ratio 23.8× and T_sys,eff ≈ 3600 K. Running Cell 20 of the final notebook on the same data gives **1.02 dB** (P/Pn = 26.5 %, ratio 44×). The table was produced by an earlier code state that is not in the repository. | Cell 20 vs `thesis/report/chapters/ch5_results.tex` | Results are now written to `results/<run>/summary.json` together with `config_used.json`, so every number has provenance |
| A5 | Medium | **The primary beam is read along a single cut.** `response_voltage_offset(zenith_angle)` always walks the NEC H-plane, whatever the Sun's azimuth. At transit the Sun is 22° *north* of zenith, where (elements N–S) the E-plane applies: response 0.505, not 0.603 (−0.8 dB). | Cell 2.5 | `beam.TabulatedBeam` + `Mount`: full 2-D lookup in the antenna frame (handles the NEC negative-θ scan); identical to v1 along E–W (verified) |
| A6 | Medium | **Engine A models the Sun as a point source.** All antennas see one common noise process, so visibility amplitude cannot fall with baseline. The Cell E check "longer baseline → smaller \|V\| (van Cittert–Zernike)" therefore reports only noise. | `interfsim.simulate_voltages`, Cell E | `simulate_voltages(..., components=disk_components(...))`: independent emitters across the disk. Matches the analytic jinc to < 5 % (test `test_extended_disk_decorrelates_like_jinc`, notebook §3) |
| A7 | Medium | **FWHM includes sidelobes.** `axis[profile >= max/2]` spans the first and last samples above half power, so grating lobes and the flat N–S profile of an E–W array give a meaningless width. | Cells G, G2, G3 | `metrics.fwhm_main_lobe`: walks from the peak to the first half-power crossing; returns NaN for an unresolved axis |
| A8 | Medium | **Time-average smearing is never checked.** A 50-sample dump lasts 37.9 s. On the 24 m baseline the fringe rotates by 0.84 rad (UT mapping) to 0.96 rad (v1) per dump, which costs ≈3–4 % amplitude and adds a phase bias with a stochastic source. Reducing `N_SAMPLES` without reducing `INTEGRATION_BINS` makes this much worse (2.1 rad at 20 000 samples). | Cells C, E | `summary["max_fringe_rotation_per_dump_rad"]`; `correlator.fringe_rotation_per_dump` |
| A9 | Low | Dynamic range = max/std over the whole image, source included: not a noise measure. | Cells G, I | `metrics.dynamic_range` uses the off-source RMS |
| A10 | Low | Images are always normalised to peak = 1, so the flux scale is lost. | `make_dirty_image` | `normalize=False` returns flux per synthesised beam (natural weighting, weight-normalised) |
| A11 | Low | Night gaps (`//////`) are forward-filled with the last valid row, so flat segments look like real data; CubicSpline resampling can overshoot. | `sws_to_csv._parse_txt`, Cell A | Gaps become NaN; daylight comes from solar elevation; linear interpolation across short gaps |
| A12 | Low | Reproducibility: absolute paths (`E:\1A DATN REAL`, `E:\APSIN`, `d:\datn`); cell-order dependence (Cell X must run between H and I because I overwrites `u, v, w, img, psf`); three diverging copies of `interfsim.py` and two of `primary_beam.py`; `parse_nec_out.py` outputs a θ = 0–90° grid while the beam file in use is 181×361 with θ = −180…0°, so the script that made it is not in the repo; `transfer-data.py` opens a directory as a file; `datetime.utcnow` is deprecated. | whole repo | One package, TOML configs, relative paths, tests, CI, `interfsim beam FILE` to regenerate beams from any NEC `.out` |
| A13 | Info | The field comparison uses Learmonth flux (correct: one Sun) but Learmonth geometry, while the hardware was at Hoa Lac (21° N, transit ≈ 05:03 UT). The \|H\| ≤ 30° window and the beam weighting should use the Hoa Lac site. | Cell 20 | `observation.site = "hoa_lac"` is available; see ROADMAP item P1 |

## 2. Effect on the headline numbers (20 March 2025, Case 1)

| Quantity | Thesis text | v1 code re-run | v0.2 with v1 assumptions¹ | **v0.2 corrected** |
|---|---|---|---|---|
| Peak SNR per sample | — (metadata: 18.36 dB) | prints 18.4 dB (true −0.4 dB²) | −5.3 dB | **−7.4 dB** |
| Hour-angle track | ±90° | ±90° | ±90° | **−67.8° … +90.0°** |
| Simulated solar excess, \|H\| ≤ 30° | 0.586 dB | 1.022 dB | 0.884 dB | **0.463 dB** |
| Sim/measured ratio (linear) | 23.8× | 44× | 37.6× | **18.7×** |
| Implied T_sys,eff (150 K × ratio) | ≈3600 K | ≈6600 K | ≈5600 K | **≈2800 K** |
| PSF FWHM E–W | — | — | 60.0′ | **55.4′** |
| Engine A vs Engine B image RMS difference | — | — | 0.011 | **0.009** |

¹ `configs/thesis_v1_reproduction.toml`: stretched time axis, δ = 0, pol_factor = 1, but with the
corrected 2-D beam lookup, which explains most of the gap to the v1 re-run.
² Peak flux before beam weighting, as v1 computes it. v0.2 reports the peak of the
beam-weighted signal, which is lower because the 110 SFU burst happens away from transit.

The qualitative conclusions of the thesis survive: the measured excess is one to two orders
of magnitude below the ideal receiver, consistent with an elevated effective system
temperature (no LNA). An E–W array has no N–S resolution at δ ≈ 0. Adding N–S baselines or a
DLITE-style triangle restores 2-D imaging. **The quantitative values (Table 5.7, the 3600 K
estimate, the SNR in the stimulus metadata) should be quoted from v0.2 in any publication.**

## 3. How to reproduce this audit

```bash
pip install -e ".[dev]"
pytest                                           # 18 tests, incl. the physics cross-checks
interfsim run configs/thesis_case1_20250320.toml  # corrected
interfsim run configs/thesis_v1_reproduction.toml # v1 assumptions
```
