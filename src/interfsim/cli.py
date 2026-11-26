"""Command line interface: ``interfsim run|beam|rstn|field ...``."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _cmd_run(a) -> None:
    from .pipeline import PipelineConfig, run_pipeline
    cfg = PipelineConfig.from_toml(a.config)
    if a.out:
        cfg.output.dir = str(Path(a.out).resolve())
    if a.n_samples:
        cfg.observation.n_samples = a.n_samples
    if a.no_figures:
        cfg.output.figures = False
    res = run_pipeline(cfg)
    print(json.dumps(res.summary, indent=2))


def _cmd_beam(a) -> None:
    from .beam import load_beam
    b = load_beam(a.file)
    print(f"{a.file}\n  grid {b.theta.size} theta x {b.phi.size - 1} phi | "
          f"peak {b.gain_max_dBi:.2f} dBi at (theta, phi) = {b.peak_theta_phi} | "
          f"freq {b.freq_MHz} MHz")
    if a.npz:
        b.to_npz(a.npz)
        print(f"  written {a.npz}")


def _cmd_rstn(a) -> None:
    from .io.rstn import read_rstn_day
    d = read_rstn_day(a.file)
    print(f"{a.file}: {d.ut.size} rows, {d.valid.mean() * 100:.0f}% valid, {d.ut[0]} .. {d.ut[-1]}")
    if a.csv:
        print(f"  written {d.to_csv(a.csv)}")


def _cmd_field(a) -> None:
    from .io.field_psd import read_psd_day
    d = read_psd_day(a.folder, utc_offset_h=a.utc_offset)
    ex = d.excess_db()
    print(f"{a.folder}: {d.ut.size} files, {d.ut[0]} .. {d.ut[-1]} UT, centre {d.freq_center_mhz:.2f} MHz, "
          f"peak excess {ex.max():.4f} dB")
    if a.csv:
        print(f"  written {d.to_csv(a.csv)}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="interfsim", description="Radio interferometer simulator")
    sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run", help="run the end-to-end pipeline from a TOML config")
    r.add_argument("config")
    r.add_argument("--out", help="output directory (overrides output.dir)")
    r.add_argument("--n-samples", type=int)
    r.add_argument("--no-figures", action="store_true")
    r.set_defaults(func=_cmd_run)
    b = sp.add_parser("beam", help="inspect / convert a beam file (.npz, .csv, NEC .out)")
    b.add_argument("file")
    b.add_argument("--npz", help="write a normalised .npz copy")
    b.set_defaults(func=_cmd_beam)
    s = sp.add_parser("rstn", help="inspect / convert an RSTN daily text file")
    s.add_argument("file")
    s.add_argument("--csv")
    s.set_defaults(func=_cmd_rstn)
    f = sp.add_parser("field", help="convert a folder of GNU Radio *_PSD.csv files to a UT light curve")
    f.add_argument("folder")
    f.add_argument("--csv")
    f.add_argument("--utc-offset", type=float, default=7.0, help="recording clock minus UT [h] (Vietnam: 7)")
    f.set_defaults(func=_cmd_field)
    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
