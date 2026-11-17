# interfsim: end-to-end simulator for small solar radio interferometers

[![CI](https://github.com/quanbanguyen/solar-interferometry-simulation-project/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue)
![license](https://img.shields.io/badge/license-MIT-green)

`interfsim` simulates a few-element radio interferometer from the sky to the image. It takes
**measured solar flux** (RSTN, 245 MHz–15.4 GHz) and a **simulated antenna pattern** (NEC-2/4NEC2,
HFSS or CST export), and produces per-antenna voltages, correlator output, (u,v,w) coverage,
dirty images and PSFs, FPGA test vectors, and a comparison against field measurements.

It grew out of the HUST graduation thesis *"End-to-end simulation of a four-element UHF radio
interferometer for solar observation at 610 MHz"* (Nguyễn Bá Quân, 2026).
*Đồ án tốt nghiệp: mô phỏng đầu-cuối giao thoa kế vô tuyến 4 phần tử quan sát Mặt Trời ở 610 MHz.*

```
 RSTN flux S(t) ──► solar ephemeris (H, δ) ──► primary beam (NEC/HFSS, mounted on the sky)
        │                                              │
        ▼                                              ▼
 radiometry (½ S A_e Δν, kT_sysΔν) ──► Engine A: per-antenna voltages (point or extended Sun)
                                              │                      └──► FPGA hex stimulus
                                              ▼
                           correlator ──► (u,v,w) ──► dirty image / PSF / metrics
                                              ▲
                     Engine B: van Cittert–Zernike forward model (cross-check, layout sweeps)
```

## Quick start

```bash
git clone https://github.com/quanbanguyen/solar-interferometry-simulation-project
cd solar-interferometry-simulation-project
pip install -e ".[dev,notebooks]"

pytest                                             # 18 tests, incl. physics cross-checks
interfsim run configs/thesis_case1_20250320.toml   # thesis Case 1 with the corrected physics
```

Outputs go to `results/<run>/`: `summary.json`, `config_used.json`, `products.npz`,
`figures/*.png` and optionally `iq_array_stimulus.txt` (16-bit I/Q per antenna).

From Python:

```python
import numpy as np
import interfsim as ix

arr = ix.preset_dlite(side=8)                                   # triangle + centre
obs = ix.Observation(lat_deg=21.0, dec_deg=-10.0, fc_hz=610e6, H_deg=np.linspace(-60, 60, 300))
u, v, w, V = ix.forward_visibilities(arr, obs, {"type": "disk", "diameter_rad": np.radians(0.533)})
img, l, m = ix.make_dirty_image(u, v, w, V, fov_deg=3, grid=128, do_fringe_stop=False)
```

The tutorial notebook [`notebooks/01_end_to_end_pipeline.ipynb`](notebooks/01_end_to_end_pipeline.ipynb)
walks through the thesis cases, a layout comparison, and the van Cittert–Zernike validation.

## Features

| Area | What is there |
|---|---|
| Arrays | linear, cross, T, DLITE triangle+centre, random, file/ENU input; thesis presets |
| Geometry | ENU → XYZ → (u,v,w) (TMS Eq. 4.1), alt-az, NOAA solar ephemeris for any site |
| Beams | NEC `.out` parser (incl. 4NEC2 negative-θ scans), `.npz`, HFSS/CST CSV; 2-D lookup with antenna mounting |
| Signal | ½ S A_e Δν radiometry, Johnson–Nyquist noise, voltage synthesis for point **or extended** sources |
| Correlator | cross/auto-correlation, dump integration, fringe-smearing diagnostic |
| Imaging | direct-DFT dirty image (block-wise, low memory), PSF, optional flux-scaled output |
| Metrics | main-lobe FWHM, side-lobe level, off-source dynamic range, u-v filling, baseline redundancy |
| I/O | RSTN daily files (UT-aware), CSV export, fixed-point hex stimulus + metadata |
| Validation | Engine A ≡ Engine B; extended Sun reproduces the analytic jinc; offset point sources land on the right pixel |

How it compares with Ansys HFSS/AEDT/PyAEDT and with radio-astronomy simulators (OSKAR, CASA,
pyuvsim): [`docs/ANSYS_COMPARISON.md`](docs/ANSYS_COMPARISON.md).

## Repository layout

```
src/interfsim/      the Python package (all physics lives here)
tests/              pytest suite
configs/            TOML run configurations (thesis cases, v1 reproduction, DLITE)
notebooks/          tutorial notebook; legacy/ holds the original thesis notebook
data/               RSTN flux, antenna models/beams, field measurements (see data/README.md)
docs/               audit, Ansys comparison, roadmap, layout guide
thesis/             LaTeX report, slides, notes, field-project material
legacy/             thesis v1 scripts kept for traceability (not imported by the package)
tools/web/          standalone HTML beam visualiser
```

Details: [`docs/REPOSITORY_LAYOUT.md`](docs/REPOSITORY_LAYOUT.md).

## Status and known limitations

This is **v0.2**, a refactor of the thesis code. The audit [`docs/AUDIT.md`](docs/AUDIT.md) lists
what changed and how it moves the thesis numbers: SNR metadata, polarisation factor, UT time base,
2-D beam lookup and the extended-Sun model. Not yet available: deconvolution, calibration, FFT
gridding, MeasurementSet export, mutual coupling in the pipeline. See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Citing

See [`CITATION.cff`](CITATION.cff). Solar flux data: Radio Solar Telescope Network (RSTN),
Learmonth Solar Observatory, distributed by NOAA NCEI.

## License

Code: MIT ([`LICENSE`](LICENSE)). Thesis text, figures and photos in `thesis/` remain © the author;
third-party data keep their own terms (see `data/README.md`).
