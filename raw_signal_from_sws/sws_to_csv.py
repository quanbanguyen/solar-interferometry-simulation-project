r"""
sws_to_csv.py - Chuyen RSTN Learmonth (.txt) -> CSV, va lay khoi BAN NGAY cho mo phong.

File 1 ngay co ~52% "//////" = BAN DEM (Mat Troi duoi chan troi). Khong dung phan dem.
Module nay:
  - convert_file / convert_folder : .txt -> .csv (them cot gap_flag) de mo bang Excel.
  - load_day(date)                : chi can DOI NGAY, tu tim file cung thu muc, tra ve
                                    (time, flux) cua KHOI BAN NGAY (da bo dem) -> dua thang vao sim.
Khong can cai them thu vien ngoai numpy.
"""
import csv, os, glob
import numpy as np

FREQ_LABELS = ["Time_s", "F245", "F410", "F610", "F1415", "F2695", "F4995", "F8800", "F15400"]
N_COLS = len(FREQ_LABELS)

# Thu muc chua DU LIEU (mac dinh = thu muc chua chinh file .py nay).
# Vi ban de code + .txt cung mot folder nen khong can sua. Neu khac, dat:
#   import sws_to_csv as sws ; sws.BASE_DIR = r"E:\APSIN"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _parse_txt(path):
    """Doc .txt -> (data ndarray Nx9, flags ndarray N). Giu thoi gian, forward-fill flux."""
    rows, flags = [], []
    last = None
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if "//////" in line:
                if last is None:
                    continue
                try:
                    t = float(parts[0])
                except (ValueError, IndexError):
                    t = (rows[-1][0] + 1) if rows else 0.0
                rows.append([t] + list(last)); flags.append(1)
                continue
            try:
                vals = [float(p) for p in parts]
            except ValueError:
                continue
            if len(vals) < N_COLS:
                continue
            vals = vals[:N_COLS]
            rows.append(vals); flags.append(0); last = vals[1:]
    if not rows:
        raise ValueError(f"Khong doc duoc du lieu so nao tu: {path}")
    return np.array(rows), np.array(flags, dtype=int)


def _longest_gap_run(flags):
    """(start, end_inclusive, length) cua khoi GAP lien tuc dai nhat = ban dem."""
    best = (0, -1, 0); s = None
    for i, v in enumerate(list(flags) + [0]):
        if v == 1 and s is None:
            s = i
        elif v == 0 and s is not None:
            if i - s > best[2]:
                best = (s, i - 1, i - s)
            s = None
    return best


def _daytime_slice(flags):
    """Tra ve slice cua KHOI BAN NGAY: ben (truoc/sau dem) co nhieu mau that hon,
    sau khi cat bo dem va cat rim gap o hai dau."""
    ns, ne, nl = _longest_gap_run(flags)
    before = (0, ns)                      # truoc dem
    after = (ne + 1, len(flags))          # sau dem
    pick = before if (flags[before[0]:before[1]] == 0).sum() >= \
                     (flags[after[0]:after[1]] == 0).sum() else after
    lo, hi = pick
    real = np.where(flags[lo:hi] == 0)[0]
    if len(real):                         # cat bo gap thua o dau/cuoi khoi
        lo, hi = lo + real[0], lo + real[-1] + 1
    return slice(lo, hi)


def convert_file(input_file, output_file=None, verbose=True):
    """.txt -> .csv (them cot gap_flag). Tra ve duong dan CSV."""
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".csv"
    data, flags = _parse_txt(input_file)
    with open(output_file, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(FREQ_LABELS + ["gap_flag"])
        for r, g in zip(data, flags):
            w.writerow(list(r) + [int(g)])
    if verbose:
        sl = _daytime_slice(flags)
        L = sl.stop - sl.start
        print(f"[OK] {os.path.basename(input_file)} -> {os.path.basename(output_file)} | "
              f"{len(data)} dong, gap {100*flags.mean():.0f}% | "
              f"ban ngay: dong {sl.start}-{sl.stop} (~{L/3600:.1f} h)")
    return output_file


def convert_folder(folder=None, pattern="*.txt"):
    folder = folder or BASE_DIR
    files = sorted(glob.glob(os.path.join(folder, pattern)))
    out = [convert_file(fp) for fp in files]
    print(f"\nDa chuyen {len(out)} file trong {folder}.")
    return out


def load_day(date, freq="F610", save_csv=True, out_dir=None):
    """CHI CAN DOI NGAY. Tu tim '{date}.txt' trong BASE_DIR, tra ve (time_s, flux) cua
    KHOI BAN NGAY (da bo dem) o tan so 'freq'. Vd: t, flux = load_day('20-3-2025').
    freq thuoc: F245 F410 F610 F1415 F2695 F4995 F8800 F15400."""
    txt = os.path.join(BASE_DIR, f"{date}.txt")
    if not os.path.exists(txt):
        raise FileNotFoundError(f"Khong thay {txt}. Dat sws.BASE_DIR cho dung thu muc du lieu.")
    data, flags = _parse_txt(txt)
    if save_csv:
        od = out_dir or BASE_DIR
        os.makedirs(od, exist_ok=True)
        convert_file(txt, os.path.join(od, f"{date}.csv"), verbose=False)
    sl = _daytime_slice(flags)
    seg = data[sl]
    t = seg[:, 0]
    flux = np.clip(seg[:, FREQ_LABELS.index(freq)], 0.0, None)  # bo gia tri am
    print(f"[{date}] {freq}: khoi ban ngay {sl.start}-{sl.stop} "
          f"(~{(sl.stop-sl.start)/3600:.1f} h, {len(flux)} mau) | flux tb {flux.mean():.1f}")
    return t, flux


if __name__ == "__main__":
    # Dat code + cac file .txt cung mot folder. Chi can doi ngay:
    t, flux = load_day("20-3-2025", freq="F610")
    # convert_folder()   # chuyen het .txt trong folder sang CSV (nhieu ngay = nhieu case)
