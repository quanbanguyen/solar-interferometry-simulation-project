"""Fixed-point quantisation and hex stimulus files for FPGA/HDL testbenches."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import numpy as np


def quantize_iq(V: np.ndarray, bits: int = 16, full_scale: float | None = None):
    """Scale complex V so that `full_scale` (default max|V|) maps to 2^(bits-1)-1
    and round I and Q to signed integers. Returns (I, Q, scale) with V*scale ~ I + jQ."""
    if not 2 <= bits <= 32:
        raise ValueError("bits must be in 2..32")
    V = np.atleast_2d(V)
    fs = float(np.nanmax(np.abs(V))) if full_scale is None else float(full_scale)
    top = 2 ** (bits - 1) - 1
    scale = 1.0 if not np.isfinite(fs) or fs == 0 else top / fs
    dtype = np.int16 if bits <= 16 else np.int32
    I = np.clip(np.round(V.real * scale), -top - 1, top).astype(dtype)
    Q = np.clip(np.round(V.imag * scale), -top - 1, top).astype(dtype)
    return I, Q, scale


def write_hex(path: str | Path, I: np.ndarray, Q: np.ndarray, bits: int = 16) -> Path:
    """One line per sample: ``I0 Q0 I1 Q1 ...`` as two's-complement hex words."""
    path = Path(path)
    digits = (bits + 3) // 4
    mask = (1 << bits) - 1
    words = np.empty((I.shape[0], 2 * I.shape[1]), dtype=np.int64)
    words[:, 0::2] = I.astype(np.int64) & mask
    words[:, 1::2] = Q.astype(np.int64) & mask
    fmt = " ".join([f"%0{digits}x"] * words.shape[1])
    np.savetxt(path, words, fmt=fmt)
    return path


def read_hex(path: str | Path, bits: int = 16):
    """Inverse of :func:`write_hex`. Returns (I, Q) as signed integers."""
    with open(path) as f:
        words = np.array([[int(w, 16) for w in ln.split()] for ln in f if ln.strip()], np.int64)
    words = np.where(words >= 1 << (bits - 1), words - (1 << bits), words)
    return words[:, 0::2], words[:, 1::2]


def write_metadata(path: str | Path, meta: dict) -> Path:
    path = Path(path)
    stamp = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    lines = ["# IQ array stimulus - metadata", f"# generated_utc = {stamp}"]
    width = max(len(k) for k in meta)
    lines += [f"{k:<{width}} = {v}" for k, v in meta.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
