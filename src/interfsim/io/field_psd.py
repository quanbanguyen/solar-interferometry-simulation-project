"""Reader for the Vietnamese amateur 610 MHz field recordings (GNU Radio ``*_PSD.csv`` files).

The instrument (``Sun_Observering_Interferometry``: two Yagi-Uda antennas, an
RTL-SDR at 1 MS/s, GNU Radio flowgraph ``Interferometer.py``) writes one file
per integration, named ``YYYY_MM_DD_HH_MM_SS_d_PSD.csv`` (``d`` = tenths of a
second), with 512 rows ``frequency_MHz, power_dB``.

Things to know about these files (see docs/FIELD_DATA.md):

* The file clock is the recording computer's **local time**. For the Hoa Lac
  610 MHz runs it is Vietnam time (UTC+7): the daily maximum falls near 11:50
  on the file clock, i.e. close to solar transit at 05:03 UT.
* The 610 MHz flowgraph has no FFT: it takes |x|^2 of 512-sample vectors, so the
  512 "frequency" rows are 512 time positions of the same total-power
  measurement, not a spectrum. The rows are therefore combined into one value.
* Power is converted to dB *before* the averaging blocks, so the stored value is
  a mean of logarithms; it underestimates short, strong bursts. Treat it as a
  relative (uncalibrated) power level.
* Rows equal to exactly 0 dB are band-edge padding and are dropped.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_NAME = re.compile(r"(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d)_PSD\.csv$")


@dataclass
class FieldDay:
    """Total-power light curve of one recording session."""

    ut: np.ndarray              # (T,) datetime64[ms], converted to UT
    power_db: np.ndarray        # (T,) relative power [dB], one value per file
    spread_db: np.ndarray       # (T,) std of the rows inside each file (noise indicator)
    freq_center_mhz: float
    utc_offset_h: float
    source: str = ""

    @property
    def power_linear(self) -> np.ndarray:
        return 10.0 ** (self.power_db / 10.0)

    def excess_db(self, floor_db: float | None = None, floor_quantile: float = 0.05) -> np.ndarray:
        """Power above the noise floor [dB]. Default floor: a low quantile of the day,
        i.e. the receiver with the Sun outside the main beam."""
        floor = np.quantile(self.power_db, floor_quantile) if floor_db is None else floor_db
        return self.power_db - floor

    def hours_ut(self) -> np.ndarray:
        day = self.ut[0].astype("datetime64[D]")
        return (self.ut - day).astype("timedelta64[ms]").astype(float) / 3.6e6

    def to_csv(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write(f"# source: {self.source}\n# centre frequency {self.freq_center_mhz:.4f} MHz; "
                    f"file clock converted from UTC{self.utc_offset_h:+g} to UT\n")
            w = csv.writer(f)
            w.writerow(["ut", "power_db", "spread_db"])
            for t, p, s in zip(self.ut, self.power_db, self.spread_db, strict=True):
                w.writerow([str(t), f"{p:.5f}", f"{s:.5f}"])
        return path


def parse_timestamp(name: str) -> np.datetime64:
    """File-clock time encoded in a ``*_PSD.csv`` file name."""
    m = _NAME.search(name)
    if not m:
        raise ValueError(f"not a PSD file name: {name}")
    y, mo, d, h, mi, s, ds = m.groups()
    return np.datetime64(f"{y}-{mo}-{d}T{h}:{mi}:{s}") + np.timedelta64(int(ds) * 100, "ms")


def read_psd_file(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """(frequency_MHz, power_dB) columns of one file."""
    a = np.loadtxt(path, delimiter=",", ndmin=2)
    return a[:, 0], a[:, 1]


def read_psd_day(folder: str | Path, utc_offset_h: float = 7.0, statistic: str = "median") -> FieldDay:
    """Read every ``*_PSD.csv`` in a folder into a time-ordered light curve.

    utc_offset_h : offset of the recording clock from UT (Vietnam: +7).
    statistic    : how the 512 rows of a file are combined ("median" or "mean").
    """
    folder = Path(folder)
    files = sorted(p for p in folder.iterdir() if _NAME.search(p.name))
    if not files:
        raise FileNotFoundError(f"no *_PSD.csv files in {folder}")
    comb = {"median": np.median, "mean": np.mean}[statistic]
    t, p, s, fc = [], [], [], []
    for f in files:
        freq, db = read_psd_file(f)
        keep = db != 0.0
        if not keep.any():
            continue
        t.append(parse_timestamp(f.name))
        p.append(comb(db[keep]))
        s.append(np.std(db[keep]))
        fc.append(np.mean(freq[keep]))
    shift = np.timedelta64(int(round(utc_offset_h * 3600e3)), "ms")
    ut = np.array(t, dtype="datetime64[ms]") - shift
    order = np.argsort(ut)
    return FieldDay(ut[order], np.array(p)[order], np.array(s)[order], float(np.median(fc)),
                    utc_offset_h, str(folder))


def read_field_csv(path: str | Path) -> FieldDay:
    """Read a light curve written by :meth:`FieldDay.to_csv`."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    head = [ln for ln in lines if ln.startswith("#")]
    fc = float(re.search(r"centre frequency ([\d.]+)", " ".join(head)).group(1))
    off = float(re.search(r"UTC([+-][\d.]+)", " ".join(head)).group(1))
    rows = list(csv.DictReader(ln for ln in lines if not ln.startswith("#")))
    return FieldDay(np.array([r["ut"] for r in rows], dtype="datetime64[ms]"),
                    np.array([float(r["power_db"]) for r in rows]),
                    np.array([float(r["spread_db"]) for r in rows]), fc, off, str(path))


def align_to(field: FieldDay, ut: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Interpolate another instrument's series (e.g. RSTN flux) onto the field times.
    NaNs in `values` are skipped; times outside its span give NaN."""
    t_ref = ut.astype("datetime64[ms]").astype(float)
    ok = ~np.isnan(values)
    t = field.ut.astype("datetime64[ms]").astype(float)
    out = np.interp(t, t_ref[ok], values[ok], left=np.nan, right=np.nan)
    return out
