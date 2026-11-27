# interfsim vs Ansys (HFSS / AEDT / STK / PyAnsys): feature comparison

**Bottom line.** Ansys and interfsim solve different halves of the same problem. Ansys
(HFSS, AEDT Circuit, EMIT, STK) models *electromagnetics and RF hardware*: how an antenna
radiates, how antennas couple, and how a receiver chain adds gain and noise. It has no
model of *interferometry*: no correlator, no (u,v,w), no aperture synthesis, no imaging,
no astronomical sources. interfsim covers that second half and uses an EM solver only as an
input, through the far-field pattern. The two are complementary, and the strongest position
for this project is a **bridge** between them, not a competitor to HFSS.

"Ansys open source" here means **PyAnsys**: MIT-licensed Python libraries such as
[PyAEDT](https://github.com/ansys/pyaedt) and [PyEDB](https://github.com/ansys/pyedb). They are
scripting layers, and running them still needs a licensed AEDT installation. The solvers
themselves remain commercial (Ansys has been part of Synopsys since 2025; the current
release is 2026 R1).

## 1. Feature matrix

Legend: ✅ supported · 🟡 partial or indirect · ❌ not available · → planned (see ROADMAP.md)

| Capability | interfsim v0.2 | Ansys HFSS / AEDT (+PyAEDT) | Notes |
|---|---|---|---|
| **Antenna EM modelling** | | | |
| Full-wave solution of an antenna (FEM/MoM) | ❌ (imports NEC-2 / 4NEC2, CSV) | ✅ HFSS FEM, IE, hybrid; SBR+ for large platforms | interfsim never solves Maxwell's equations; it consumes patterns |
| Far-field gain pattern G(θ,φ) | 🟡 import: NEC `.out`, `.npz`, CSV (HFSS/CST reports) | ✅ native | `TabulatedBeam.from_csv` auto-detects HFSS column names |
| Mounting/orientation of the pattern on the sky | ✅ `Mount` (boresight, element axis, pointing) | 🟡 coordinate systems inside the model; no sky frame | |
| Mutual coupling / embedded element patterns | 🟡 4NEC2 two-antenna runs in `data/antenna/nec_out` (not yet used in the pipeline) → | ✅ finite-array DDM, unit-cell, embedded patterns | Strong Ansys advantage; planned import of per-element patterns |
| Input impedance, S-parameters, VSWR | ❌ | ✅ | Measured with NanoVNA in the thesis |
| Ground, mast and installation effects | ❌ | ✅ (SBR+, installed performance) | |
| **RF chain** | | | |
| System temperature, noise power kTB | ✅ analytic | ✅ circuit/system simulation (Nexxim, noise figure, cascades) | Ansys gives T_sys from component data; interfsim takes T_sys as a parameter |
| LNA, filters, mixers, non-linearity | ❌ → | ✅ | |
| ADC quantisation, fixed-point I/Q | ✅ `io.fpga` (any bit width, hex testbench files) | ❌ | |
| RF interference / coexistence | ❌ → | ✅ EMIT; STK for satellite RFI | 608–614 MHz is a radio-astronomy band; RFI modelling is a natural next step |
| **Observation geometry** | | | |
| Site, Sun ephemeris, hour angle, declination | ✅ (NOAA solar algorithm, any site) | 🟡 STK (orbits/ephemerides), not in HFSS | |
| ENU → XYZ → (u,v,w), Earth-rotation synthesis | ✅ (TMS Eq. 4.1) | ❌ | |
| **Interferometry** | | | |
| Per-antenna voltage synthesis from a real flux time series | ✅ Engine A (point or extended Sun) | ❌ | Unique feature: drives FPGA/correlator testbenches |
| Van Cittert–Zernike forward model (point, disk, Gaussian) | ✅ Engine B | ❌ | |
| Correlator (cross-multiply + integrate), smearing diagnostic | ✅ | ❌ | |
| Dirty image, PSF, FWHM, side lobes, u-v fill | ✅ direct DFT | ❌ | |
| Deconvolution (CLEAN), calibration, self-cal | ❌ → | ❌ | |
| Array-layout sweeps | ✅ `sweep_layouts` | 🟡 Optimetrics can sweep EM geometry, not synthesis performance | |
| **Data & validation** | | | |
| Real solar data ingestion (RSTN 245 MHz – 15.4 GHz) | ✅ | ❌ | |
| Comparison with field measurements | ✅ gain-independent solar excess | ❌ | |
| Automated physics tests | ✅ 18 pytest tests incl. jinc and Engine A = B checks | n/a (vendor-verified solvers) | |
| **Engineering** | | | |
| Licence / cost | MIT, free | Commercial; PyAEDT is MIT but needs a licensed AEDT | Ansys Student is free but size-limited |
| Scripting | Python API, TOML configs, CLI | PyAEDT, IronPython | |
| Platforms | any with Python ≥ 3.10 | Windows/Linux, high-end workstations | |
| Compute scale | seconds to minutes on a laptop | minutes to hours per EM solve; HPC licences | |

## 2. What each tool is better at

**Use Ansys for:** element design and matching (U-frame Yagi, folded dipole, balun),
coupling in dense layouts (< 1 λ), installed performance (mast, ground, nearby structures),
receiver-chain noise budgets, and RFI coexistence. Its accuracy here is far beyond NEC-2 for
complex 3-D metal/dielectric geometry.

**Use interfsim for:** everything from "the Sun emits S(t) SFU" to "this is the image the array
makes": hour-angle tracks, fringe rates, correlator dumps and smearing, u-v coverage, PSF,
layout trade studies, real-data replay, and FPGA test vectors. No Ansys product does this.

## 3. The bridge: HFSS/PyAEDT → interfsim

The import path works today, without code changes:

1. In HFSS create a far-field report: `GainTotal` (dB) versus Theta and Phi, full sphere, at 610 MHz.
2. Export it to CSV, either from the GUI (*Report → Export → .csv*) or from PyAEDT. Below is a sketch;
   check method names against your PyAEDT version:

   ```python
   from ansys.aedt.core import Hfss          # PyAEDT >= 0.9 namespace
   hfss = Hfss(project="yagi_610.aedt", design="UFrame")
   report = hfss.post.reports_by_category.far_field("dB(GainTotal)", hfss.nominal_adaptive, "3D")
   report.variations = {"Freq": ["610MHz"], "Theta": ["All"], "Phi": ["All"]}
   report.create("gain3d")
   hfss.post.export_report_to_csv("exports", "gain3d")
   ```
3. Load it in interfsim, declaring which model axes are boresight and element:

   ```python
   import interfsim as ix
   beam = ix.TabulatedBeam.from_csv("exports/gain3d.csv",
                                    mount=ix.Mount(boresight_axis="+y", element_axis="+x",
                                                   pointing_el_deg=90, element_az_deg=0))
   ```
   or set `antenna.beam_file = "exports/gain3d.csv"` in a TOML config.

**Cross-validation exercise (recommended for the paper):** model the U-frame Yagi in both
4NEC2 and HFSS, load both patterns, and report the difference in PSF, solar excess and
image fidelity. That turns "we used NEC-2" into a quantified model-uncertainty statement.

## 4. The comparison reviewers will actually make

For a radio-astronomy paper the reference tools are other *interferometer* simulators, not
Ansys. Position interfsim against them explicitly:

| Tool | Scope | How interfsim differs |
|---|---|---|
| CASA `simobserve` / `simalma` | Visibility simulation + imaging for large observatories | interfsim adds per-antenna *voltages* from real flux time series, plus FPGA I/O; it is small-array and solar focused |
| OSKAR (SKA) | GPU beam + visibility simulation, large arrays | interfsim is laptop-scale, imports measured/NEC element patterns, and simulates the signal chain below the correlator |
| pyuvsim / hera_sim | Precise visibility simulation, UVH5 output | interfsim targets low-cost instruments and hardware co-design |
| RASCIL / Karabo | SKA pipeline prototyping | as above |
| APSYNSIM (in `_archive/third_party`) | Teaching tool for aperture synthesis | interfsim is physical (flux units, noise, beam, real data), not purely geometric |

Interoperability with these tools (UVFITS/MeasurementSet export, ROADMAP item E1) is what will
make results checkable by others.
