"""Reader for RSTN (Radio Solar Telescope Network) 1-second fixed-frequency data.

Line format of the daily files used here (e.g. Learmonth ``20-3-2025.txt``)::

    HHMMSS  F245  F410  F610  F1415  F2695  F4995  F8800  F15400

Flux densities are in SFU; ``//////`` marks missing samples (night / outages).
The first column is the UT time of day, not a running sample index.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

FREQS_MHZ = (245, 410, 610, 1415, 2695, 4995, 8800, 15400)
FREQ_LABELS = tuple(f"F{f}" for f in FREQS_MHZ)


@dataclass
class RSTNDay:
    date: np.datetime64             # UT date of the file
    ut: np.ndarray                  # (T,) datetime64[s]
    flux_sfu: np.ndarray            # (T, 8) with NaN where missing
    source: str = ""

    def channel(self, freq) -> np.ndarray:
        """Flux column for 610, "610", "F610" ..."""
        f = int(str(freq).upper().lstrip("F"))
        return self.flux_sfu[:, FREQS_MHZ.index(f)]

    @property
    def valid(self) -> np.ndarray:
        return ~np.isnan(self.flux_sfu).all(axis=1)

    def select(self, mask: np.ndarray) -> RSTNDay:
        return RSTNDay(self.date, self.ut[mask], self.flux_sfu[mask], self.source)

    def daylight(self, site, min_elevation_deg: float = 0.0) -> RSTNDay:
        """Samples with the Sun above `min_elevation_deg` at `site` (an ephem.Site)."""
        from ..ephem import sun_elevation_deg
        return self.select(sun_elevation_deg(self.ut, site) > min_elevation_deg)

    def to_csv(self, path: str | Path) -> Path:
        path = Path(path)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ut", *FREQ_LABELS])
            for t, row in zip(self.ut, self.flux_sfu, strict=True):
                w.writerow([str(t), *("" if np.isnan(x) else f"{x:g}" for x in row)])
        return path


def parse_date_from_name(name: str) -> np.datetime64:
    """'20-3-2025' (D-M-YYYY, as used for the files in data/rstn) -> datetime64[D]."""
    m = re.search(r"(\d{1,2})-(\d{1,2})-(\d{4})", name)
    if not m:
        raise ValueError(f"cannot find a D-M-YYYY date in {name!r}")
    d, mo, y = (int(x) for x in m.groups())
    return np.datetime64(f"{y:04d}-{mo:02d}-{d:02d}")


def read_rstn_day(path: str | Path, date: str | np.datetime64 | None = None) -> RSTNDay:
    """Read one daily RSTN text file. `date` defaults to the date in the file name."""
    path = Path(path)
    day = np.datetime64(date, "D") if date is not None else parse_date_from_name(path.name)
    secs, rows = [], []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 9 or not parts[0].isdigit():
                continue
            hhmmss = int(parts[0])
            h, mnt, s = hhmmss // 10000, hhmmss // 100 % 100, hhmmss % 100
            if h > 23 or mnt > 59 or s > 59:
                continue
            vals = [float(p) if p.lstrip("-").isdigit() else np.nan for p in parts[1:9]]
            secs.append(h * 3600 + mnt * 60 + s)
            rows.append(vals)
    if not rows:
        raise ValueError(f"no data rows in {path}")
    ut = day.astype("datetime64[s]") + np.array(secs, dtype="timedelta64[s]")
    flux = np.array(rows, float)
    flux[flux < 0] = np.nan
    return RSTNDay(day, ut, flux, str(path))
