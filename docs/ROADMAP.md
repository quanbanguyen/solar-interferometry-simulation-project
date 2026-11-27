# Roadmap: from thesis code to a research tool and a paper

Items are ordered by value for a first publication. Each item says what to build, why it
matters scientifically, and what "done" looks like (a test or a figure).

## Phase P: make the existing results publishable (≈1–2 months)

| ID | Item | Why | Done when |
|---|---|---|---|
| P1 | *(started: `interfsim field`, `validation.fit_effective_tsys`, docs/FIELD_DATA.md)* **Run the field comparison at the Hoa Lac site** (`site = "hoa_lac"`) and replace the hand-read dB values with the raw receiver recording | Today the comparison mixes Learmonth geometry with Hoa Lac hardware and two numbers read off a PNG (AUDIT A4, A13) | `configs/hoalac_20250320.toml`; the measured excess is computed from data, with an error bar |
| P2 | **Uncertainty budget** for the solar excess: T_sys, beam model (NEC vs HFSS), pointing, cable loss, flux calibration (RSTN ±10–20 %) | Turns the 18.7× gap into "T_sys,eff = X ± Y K", a defensible measurement of the receiver | Monte Carlo over the config parameters; table in the paper |
| P3 | **Multi-day statistics**: run all days in `data/rstn` against the `data/field` daily curves | One day is an anecdote; 40+ days are a result | Scatter plot of simulated vs measured excess across days |
| P4 | **Cross-code validation** against pyuvsim or CASA `simobserve` for the same layout and point/disk source | Reviewers trust a simulator that agrees with established codes | Visibility difference < 1 % in a test |

## Phase E: features that make it a tool other people use (≈2–4 months)

| ID | Item | Notes |
|---|---|---|
| E1 | **UVFITS / MeasurementSet export** (via `pyuvdata`) | Opens the output to CASA, WSClean, AIPS: interoperability is the main adoption criterion |
| E2 | **Gridding + FFT imager** with natural/uniform/Briggs weighting; keep the DFT as a reference | The DFT is O(N_vis · N_pix²); the FFT is needed for >16 antennas or long tracks |
| E3 | **Högbom / Clark CLEAN** and restored images | Dirty images alone are not accepted as science products |
| E4 | **Calibration module**: per-antenna complex gains, delays (clock offsets: the Xuan Mai "fringe washing"), bandpass; solve with StEFCal using the Sun or a strong source | Directly models the hardware failure modes seen in the field campaign |
| E5 | **Embedded element patterns / mutual coupling**: one beam per antenna, read from the 4NEC2 two-antenna runs (`data/antenna/nec_out/yagi_two_ant_d*.out.txt`) or HFSS finite-array exports | Quantifies coupling-induced imaging error versus spacing, a publishable small-array study |
| E6 | **Multi-frequency / dynamic spectrum**: use all 8 RSTN channels, bandwidth smearing, multi-frequency synthesis | Solar radio bursts are spectral phenomena (type II/III drift) |
| E7 | **Solar sky models**: limb-brightened disk, active regions. *Moving burst sources with position vs time: done (`interfsim.burst`, centroid tracking + Cramer-Rao bound)* | Enables "can this array locate a type III burst?" studies |
| E8 | **Performance**: `numba` or GPU (CuPy) kernels for voltage synthesis and DFT; chunked streaming for 10⁸-sample voltage files | Real ADC rates (MS/s) instead of one sample per 0.76 s |
| E9 | **RFI injection**: FM, TV, GNSS and satellite signals (and flagging tests) | 608–614 MHz is a protected radio-astronomy band; RFI is the dominant real-world issue |
| E10 | **Ionospheric phase screens** (Kolmogorov, TID waves) | Relevant at 610 MHz on longer baselines; matches the DLITE science case |
| E11 | **HDL co-simulation**: bit-exact golden model of the FPGA correlator, Van Vleck correction for low-bit quantisation, automatic comparison with the HDL testbench output | Makes `io.fpga` a verification tool, not only a stimulus generator |
| E12 | **PyAEDT bridge**: a script that sweeps the Yagi geometry in HFSS and scores each design on *interferometric* metrics (PSF, excess, sidelobes), not just gain | Antenna-array co-design: something neither Ansys nor radio-astronomy simulators do alone |

## Phase D: documentation and community

- Sphinx or MkDocs site generated from the docstrings, plus the notebook as a tutorial; publish it on Read the Docs.
- Tagged releases on GitHub; Zenodo DOI per release (the `CITATION.cff` is already in place).
- Example gallery: E–W vs cross vs DLITE vs random layouts; burst localisation; RFI.

## Paper strategy

1. **Software paper → Journal of Open Source Software (JOSS).** Short paper, review of code
   quality and documentation. Needs: a public repo, licence, tests and CI (in place), docs (D),
   and a statement of need. Realistic once E1–E3 exist.
2. **Instrument/method paper**, e.g. *Radio Science*, *Journal of Astronomical Telescopes,
   Instruments, and Systems*, *Astronomy and Computing*, or *Publications of the Astronomical
   Society of Australia*, or a URSI AT-RASC / GASS conference paper as a first step.
   Working title: *"End-to-end simulation and field validation of a low-cost 610 MHz solar
   radio interferometer"*. Core figures already produced by this repo:
   - Engine A (voltages, extended Sun) vs the analytic van Cittert–Zernike jinc (notebook §3).
   - Engine A = Engine B image agreement (RMS < 0.02).
   - Layout comparison (E–W, cross, DLITE, extended): PSF, u-v fill, unique baseline directions.
   - Simulated vs measured solar excess → T_sys,eff with uncertainty (needs P1–P3).
   - Fringe-smearing and clock-offset effects (needs E4).
3. **Follow-up science paper** once E5–E7 exist: burst localisation accuracy of few-element
   arrays versus layout and coupling, a question small solar arrays (and their builders)
   actually face.

### Before making the repository public

- Git history still contains copyrighted PDFs and third-party material that has now been moved
  to `_archive/`. Rewrite history (`git filter-repo`) or start a fresh public repo from the
  current tree. Either way, decide with your supervisor.
- Confirm the RSTN data licence and attribution (NOAA NCEI / US Air Force), and get permission
  for the field photos and reports in `thesis/`.
