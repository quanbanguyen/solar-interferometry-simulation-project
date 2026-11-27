# Contributing

Thanks for your interest! Bug reports, data, and pull requests are welcome.

## Development setup

```bash
pip install -e ".[dev,notebooks]"
pytest                 # must pass
ruff check src tests   # must be clean
```

## Guidelines

- Physics goes into `src/interfsim`, never only into a notebook. Notebooks call the package.
- Every new physical model comes with a test against an analytic result or an independent code
  (see `tests/test_engines.py` for examples).
- SI units internally; state units in docstrings. Angles are degrees at the API unless named `_rad`.
- New runs are described by a TOML file in `configs/`; do not hard-code paths.
- New data go under `data/` with a line in `data/README.md` (origin, format, licence).
- Keep notebooks committed **without outputs** (`jupyter nbconvert --clear-output --inplace <nb>`).
- Commit messages: imperative mood, one topic per commit; reference issues (`Fixes #12`).

## Reporting issues

Please include the config file, the `summary.json` of the run, and the package version
(`python -c "import interfsim; print(interfsim.__version__)"`).
