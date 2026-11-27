# Thesis material

- `report/`: LaTeX source of the graduation thesis (XeLaTeX; see `report/README.md`). `main.pdf` is the submitted version.
- `slides/`: defence slides (`slides.tex`, figures in `figs/`) and talk scripts (VI/EN).
- `notes/`: working notes, notebook-cell flowcharts, chapter drafts, survey of imaging algorithms.
- `antenna_report_4nec2/`: 4NEC2 antenna simulation report.
- `field_project/`: field-campaign reports and photos.
- `figures_extra/`: figures produced during the work but not referenced by the LaTeX source.

The numbers in the thesis come from thesis v1 code (`legacy/`, `notebooks/legacy/`). For
corrections that affect quoted values, see `docs/AUDIT.md`.

Build products (`*.aux`, `*.log`, …) are git-ignored; rebuild with `latexmk -xelatex main.tex`.
