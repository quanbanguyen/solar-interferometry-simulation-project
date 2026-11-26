# Field data: the Vietnamese 610 MHz solar instrument

Source repository: `E:\Sun_Observering_Interferometry` (GNU Radio flowgraphs, processing notebooks
and the raw `*_PSD.csv` recordings; about 538 000 files). This page records what those files are, how
`interfsim` reads them, and what has to be fixed before they are quoted in a paper.

## 1. What is in the source folder

| Folder | Frequency | Content | Used here |
|---|---|---|---|
| `Signal_Processing/2024_08_28` | 622 MHz centre | 2 500 files, 5-s cadence, 03:50–07:03 UT | yes |
| `Signal_Processing/2024_10_11` | 610 MHz | 523 files, 03:35–05:02 UT | yes |
| `Signal_Processing/2025_03_20 … 2025_03_24` | 610 MHz | 1 433 files/day, 10-s cadence, 03:00–07:00 UT | yes |
| `Signal_Processing/2025_04_18` | **31–35 MHz** | DLITE-style low-band run | no (not 610 MHz) |
| `radio1/extracted`, `radio2/extracted` | **31–35 MHz** | 34 and 38 days, 2025-04-24 … 2025-06-30 | no |
| `hus/Data Zip Files` | 31–35 MHz | the same files as `radio2` (byte-identical sample) | no |
| `solar app/` | – | e-CALLISTO installer and tools | – |
| `Interferometer.py/.grc` | 610 MHz | RTL-SDR (osmosdr), 1 MS/s, 512-sample vectors | flowgraph of the data above |
| `dlite.py/.grc` | 35 MHz | SDRplay RSPdx, 8 MS/s, FFT spectrometer | low-band runs |

The 610 MHz light curves are converted with `interfsim field <day folder> --csv …` and stored in
`data/field/hoa_lac_610MHz_psd/YYYY-MM-DD.csv` (UT, power in dB, spread in dB): 452 kB for 7 days.

## 2. How the 610 MHz recording works and what that means

`Interferometer.py`: RTL-SDR → `stream_to_vector(512)` → `|x|²` → `moving_average(100)` → `10 log10`
→ `integration(512)` → `integration(38)` → one CSV every ≈ 10 s (512 × 512 × 38 ≈ 10⁷ samples at 1 MS/s).

* **No FFT.** The 512 rows of a file are 512 time positions of the same total-power measurement, not a
  spectrum, even though the CSV labels them with frequencies. `interfsim` combines them (median).
* **Local clock.** Files are named with `datetime.now()` on the recording computer. For the 610 MHz runs
  this is Vietnam time (UTC+7): files run 10:00–14:00 on the file clock and the daily maximum falls at
  ≈ 11:50, near solar transit at Hoa Lac (05:03 UT = 12:03 local). The reader converts to UT
  (`utc_offset_h = 7`); a test checks the maximum falls between 04 and 06 UT.
* **Logarithm before averaging.** The stored value is a mean of dB values. For thermal noise this is
  a constant offset, but a short strong burst is compressed. Fix in the flowgraph (move `nlog10` to the
  end) before using the instrument for burst flux measurements.
* **Uncalibrated.** No noise diode or hot/cold load, so only relative power is available. The fit in
  §3 avoids the need for an absolute gain.

Other issues in the source code, for whoever maintains the instrument:
`dlite.py` calls `set_sample_rate(samp_rate)` but defines `sample_rate` (NameError at start-up);
the custom `integration` block outputs one value per call regardless of how many inputs it received;
`radio2` and `hus` duplicate each other; a 111 MB `Unconfirmed 20850.crdownload` is committed.

## 3. Effective system temperature from the field data (roadmap P1)

`interfsim.validation.fit_effective_tsys` fits the field power with
P(t) = A + C · x(t), where x(t) = P_sun/(k T_sys B) is the simulated Sun-to-noise ratio for the Hoa Lac
site (Learmonth RSTN 610 MHz flux × 2-D primary beam). Then T_eff = T_sys · A / C. The beam weighting
that changes along the track is the lever arm, so no "Sun off" level is needed.

| Day (2025) | T_sys,eff (K), formal 1σ | correlation r | 3σ detectable flux per 10 s |
|---|---|---|---|
| 03-20 | 5 590 ± 240 | 0.53 | 26 SFU |
| 03-21 | 4 870 ± 180 | 0.59 | 21 SFU |
| 03-22 | 7 360 ± 330 | 0.51 | 32 SFU |

(`configs/hoalac_field_20250320.toml`, compact E–W array, disk Sun, 150 K model receiver.)

Reading the table:
* The day-to-day spread (≈ 5 900 ± 1 300 K) is much larger than the formal errors: the residuals are
  correlated in time, so the regression error is too small. Quote the spread over days (roadmap P3).
* r ≈ 0.5 means the beam model explains only a quarter to a third of the variance. Candidates: the
  fringe pattern of the two-antenna adding interferometer (not yet in the model), gain drift of the
  RTL-SDR (no temperature control), and pointing/mounting uncertainty of the Yagis.
* The older 2 800 K estimate in docs/AUDIT.md used Learmonth geometry and two dB values read off a
  plot; this fit replaces it.
* The detection limit is the useful number for space-weather work: a burst brighter than about
  20–30 SFU above the quiet Sun is seen at 3σ in a single 10-s point. Typical 610 MHz bursts during
  flares are tens to thousands of SFU.

## 4. Next steps with this data

1. Run the fit for all 610 MHz days (2024-08-28 at 622 MHz needs its own beam frequency) and quote the
   mean and spread of T_sys,eff.
2. Add the adding-interferometer fringe term (two antennas into one receiver) to the model.
3. Fix the flowgraph (FFT or no FFT, log at the end, UTC timestamps, a noise-diode calibration) before
   the next campaign.
4. Cross-match with other stations (see the cross-country plan in the README/roadmap).
