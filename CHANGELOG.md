# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Moving solar burst model (`interfsim.burst`): rise/decay light curve, radial plane-of-sky motion
  (speed in km/s, position angle), optional Gaussian extent; Engine A voltages and Engine B visibilities.
- Burst-centroid tracking per correlator dump (point-source maximum likelihood, 1-D fit for collinear
  arrays) and the Cramer-Rao bound, both at the simulated sample count and at the real B·tau.
- `[burst]` config section, `configs/dlite_moving_burst.toml`, `burst_track.png` figure, `burst_*`
  entries in `summary.json` and `products.npz`.
- `geometry.antenna_phase` accepts per-sample (l, m) offsets.
- Field data: reader for the GNU Radio `*_PSD.csv` recordings of the Vietnamese 610 MHz instrument
  (`interfsim.io.field_psd`, CLI `interfsim field`), with UTC+7 -> UT conversion; seven 610 MHz days
  converted to `data/field/hoa_lac_610MHz_psd/`.
- `interfsim.validation.fit_effective_tsys` and `[comparison] field_csv`: effective system temperature
  and 3-sigma detectable flux from the field light curve (roadmap P1); `configs/hoalac_field_20250320.toml`.
- docs/FIELD_DATA.md: what the field recordings are, their known problems, first T_sys,eff results.

## [0.2.0] - 2026-11-03

First packaged release; refactors the thesis notebook into the `interfsim` library.

### Added
- Installable package `src/interfsim` with CLI `interfsim run|beam|rstn`, TOML configs, pytest suite and CI.
- NOAA solar ephemeris and UT-aware RSTN reader: each sample gets its real hour angle and declination.
- `TabulatedBeam` + `Mount`: 2-D beam lookup in the antenna frame; loaders for NEC `.out`, `.npz` and HFSS/CST CSV.
- Extended-source voltage synthesis (`components=disk_components(...)`), validated against the analytic jinc.
- Metrics: main-lobe FWHM, off-source dynamic range, side-lobe level, u-v filling, fringe rotation per dump.
- Flux-scaled imaging (`normalize=False`), optional visibility weights.
- Docs: audit, Ansys/PyAEDT comparison, roadmap, repository layout, data provenance.

### Fixed
- Peak SNR no longer multiplied by the load resistance (+18.75 dB error in v1; AUDIT A1).
- Single-polarisation factor ½ in the received power (AUDIT A2).
- RSTN first column read as UT `HHMMSS` instead of a sample index (AUDIT A3).
- Missing samples are NaN rather than forward-filled (AUDIT A11).

### Changed
- Repository reorganised (see docs/REPOSITORY_LAYOUT.md); third-party and copyrighted material moved to the ignored `_archive/`.

## [0.1.0] - 2026-08 (thesis v1)
- Jupyter notebook `the_newest_heart_of_project.ipynb` with `interfsim.py`, `primary_beam.py`, `sws_to_csv.py`.
