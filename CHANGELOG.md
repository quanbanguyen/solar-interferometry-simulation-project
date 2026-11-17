# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

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
