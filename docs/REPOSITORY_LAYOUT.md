# Repository layout and where the old files went

## Current tree

| Path | Content | Tracked |
|---|---|---|
| `src/interfsim/` | package: `array`, `geometry`, `ephem`, `beam`, `nec`, `sky`, `signal`, `correlator`, `imaging`, `metrics`, `pipeline`, `plotting`, `cli`, `io/{rstn,fpga}` | yes |
| `tests/` | pytest suite | yes |
| `configs/` | TOML run configurations | yes |
| `notebooks/01_end_to_end_pipeline.ipynb` | tutorial (committed without outputs) | yes |
| `notebooks/legacy/` | original thesis notebook, unchanged | yes |
| `data/rstn/learmonth/` | raw RSTN daily files (`D-M-YYYY.txt`) | yes |
| `data/rstn/csv/` | CSV conversions from thesis v1 (regenerate with `interfsim rstn FILE --csv`) | yes |
| `data/antenna/nec/` | NEC-2 input decks (single U-frame Yagi, two-antenna coupling runs) | yes |
| `data/antenna/nec_out/` | 4NEC2 output for the two-antenna runs (5 m, 10 m, 15 m, 50 cm) | yes |
| `data/antenna/beams/` | beam tables used by the pipeline | yes |
| `data/field/hoa_lac_610MHz_daily_power/` | daily power plots from the Hoa Lac instrument | yes |
| `docs/` | audit, Ansys comparison, roadmap, guides | yes |
| `thesis/report/` | LaTeX thesis (build with `latexmk -xelatex main.tex`) | sources + `main.pdf` |
| `thesis/slides/` | defence slides (LaTeX beamer) and talk scripts | sources + `slides.pdf` |
| `thesis/notes/` | working notes, flowcharts, survey, drafts | yes |
| `thesis/antenna_report_4nec2/` | 4NEC2 antenna report (docx, data-flow diagram) | yes |
| `thesis/field_project/` | field-campaign reports and photos | yes |
| `thesis/figures_extra/` | figures not used directly by the LaTeX source | yes |
| `legacy/v1/` | thesis-era scripts, superseded by the package | yes |
| `legacy/gnuradio/` | GNU Radio flowgraphs (DLITE-derived) | yes |
| `tools/web/` | `radio_simulation.html` beam visualiser | yes |
| `results/` | pipeline outputs | **ignored** |
| `_archive/` | local-only: third-party code, copyrighted papers, duplicates, scratch, old outputs | **ignored** |

## Old path → new path

| Old | New |
|---|---|
| `the_newest_heart_of_project.ipynb` | `notebooks/legacy/the_newest_heart_of_project.ipynb` (superseded by `notebooks/01_end_to_end_pipeline.ipynb`) |
| `interfsim.py`, `primary_beam.py`, `sws_to_csv.py` | `src/interfsim/*` (rewritten); originals in `legacy/v1/` |
| `export_thesis_figures.py`, `make_figure_4_1.py`, `simulate-iq-signal-from-sws.py`, `transfer-data.py`, `import numpy as np, json.py` | `legacy/v1/` (`beam_to_json.py` for the last one) |
| `raw_signal_from_sws/*.txt`, `solar_signal.txt.txt` | `data/rstn/learmonth/` (`undated_solar_signal.txt`) |
| `file_excel_du_lieu/` | `data/rstn/csv/` |
| `4nec2-out/` | `data/antenna/nec_out/` |
| `yagi_610_Uframe (1).nec`, `file_trichxuat_primary beam_cua_anten/*.nec` | `data/antenna/nec/` |
| `…/UFRAME_primary_beam_610MHz.npz`, `yagi_pattern_610MHz.csv` | `data/antenna/beams/` |
| `avg_power_thu_từ project_a_long/` | `data/field/hoa_lac_610MHz_daily_power/` |
| `baocaodatn/datn/` | `thesis/report/` |
| `datn/` (identical copy) | `_archive/duplicates/` |
| `slides datn/` | `thesis/slides/` |
| `tong hop file note và bao cao/` | `thesis/notes/working_notes/` |
| `baocaomophonganten4nec2/` | `thesis/antenna_report_4nec2/` (scripts → `legacy/v1/`) |
| `project ngoai doi/` | `thesis/field_project/` (third-party report → `_archive/`) |
| `HuongDan_Yagi_4NEC2_CST.md` | `docs/guides/yagi_4nec2_cst_vi.md` |
| `radio_simulation.html` | `tools/web/` |
| loose figures (`compare.png`, `newplot.png`, …) | `thesis/figures_extra/` |
| `DATN-REFERENCE/` | GNU Radio files → `legacy/gnuradio/`; own notes → `thesis/notes/`; papers, SunRISE docs, LWA front end → `_archive/` |
| `toolmophong_APSYNSIM_trengithub/` | removed from the index and ignored; move it to `_archive/third_party/` when no program has it open |
| `cell_*.txt`, `nb_*.txt` | `_archive/scratch/` (text dumps of notebook cells) |
| `IQ_data_for signal_processing/`, `Cell_I_Data/` | `_archive/legacy_outputs/` (regenerate with `output.fpga_hex = true` / the notebook) |

## Conventions

- Python package code: English identifiers and docstrings, SI units, angles in degrees at the API
  boundary unless the name says `_rad`.
- Every simulation run is fully described by a TOML file in `configs/`; results never live in the source tree.
- Large binaries: keep new raw data under `data/` with a line in `data/README.md` giving origin and licence.
