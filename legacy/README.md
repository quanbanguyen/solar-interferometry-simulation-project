# Legacy code (thesis v1)

Kept unchanged so that the thesis (`thesis/report/`) and its appendix can be traced back to the
code that produced it. **Not maintained and not imported by the `interfsim` package.** Use
`src/interfsim` instead; `docs/AUDIT.md` lists the known issues in these files.

- `v1/interfsim.py`, `v1/primary_beam.py`, `v1/sws_to_csv.py`: modules imported by
  `notebooks/legacy/the_newest_heart_of_project.ipynb`. To re-run that notebook, add `legacy/v1`
  to `PYTHONPATH` and edit the paths in its Cell 0.
- `v1/export_thesis_figures.py`: Cell X of the notebook as a script (needs the notebook globals).
- `v1/make_figure_4_1.py`: pipeline block diagram (Fig. 4.1).
- `v1/parse_nec_out.py`: NEC parser used for the 4NEC2 report; it rotates the pattern and regrids
  to θ = 0–90°, which differs from the beam file actually used (see AUDIT A12).
- `v1/simulate-iq-signal-from-sws.py`, `v1/transfer-data.py`: earliest prototypes (hard-coded paths).
- `gnuradio/`: GNU Radio Companion flowgraphs and embedded Python blocks derived from the DLITE project.
