"""Generate Figure 4.1 — pipeline block diagram, B&W for thesis."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(16, 13))
ax.set_xlim(0, 16)
ax.set_ylim(0, 13)
ax.axis("off")
fig.patch.set_facecolor("white")

EAX = 4.0   # Engine A x-centre
EBX = 12.0  # Engine B x-centre
CX  = 8.0   # shared centre column

BW  = 4.2   # regular box width
BH  = 1.00  # regular box height
HW  = 4.4   # header box width
HH  = 0.72  # header box height

GRAY = "#d0d0d0"

# ── Y positions (top → bottom) ────────────────────────────────────────────────
TITLE_Y = 12.60
SWS_Y   = 11.75   # BOT = 11.25
FORK_Y  = 10.95
EHY     = 10.28   # engine header   TOP=10.64  BOT=9.92
A1Y = B1Y = 9.05  # TOP=9.55        BOT=8.55
A2Y = B2Y = 7.70  # TOP=8.20        BOT=7.20
A3Y = B3Y = 6.35  # TOP=6.85        BOT=5.85
A4Y       = 5.00  # TOP=5.50        BOT=4.50
A5Y       = 3.65  # TOP=4.15        BOT=3.15
MERGE_Y   = 2.95  # horizontal merge line (above VIS_TOP=2.65)
VIS_Y     = 2.15  # TOP=2.65        BOT=1.65
IMG_Y     = 0.75  # TOP=1.25        BOT=0.25

VIS_W = 5.5
IMG_W = 7.2


def box(x, y, w, h, main, sub=None, bg="white", fs=11, lw=2.0, z=3):
    ax.add_patch(FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.10", linewidth=lw,
        edgecolor="black", facecolor=bg, zorder=z,
    ))
    if sub:
        ax.text(x, y + 0.22, main, ha="center", va="center",
                fontsize=fs, fontweight="bold", color="black", zorder=z+1)
        ax.text(x, y - 0.27, sub, ha="center", va="center",
                fontsize=fs - 1.5, color="#222222", fontstyle="italic", zorder=z+1)
    else:
        ax.text(x, y, main, ha="center", va="center",
                fontsize=fs, fontweight="bold", color="black", zorder=z+1)


def arr(x0, y0, x1, y1, lw=1.8):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color="black",
                                lw=lw, mutation_scale=16), zorder=2)


def seg(x0, y0, x1, y1, dashed=False, lw=1.8):
    ax.plot([x0, x1], [y0, y1], color="black", lw=lw,
            linestyle="--" if dashed else "-", zorder=2)


# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(CX, TITLE_Y,
        "Hình 4.1  —  Sơ đồ khối quy trình mô phỏng đầu cuối",
        ha="center", va="center", fontsize=13, fontweight="bold", color="black")

# ── SWS Input ─────────────────────────────────────────────────────────────────
box(CX, SWS_Y, BW, BH,
    "Dữ liệu Thông lượng SWS",
    sub="Learmonth 610 MHz  ·  hàm load_day()")

# ── Fork ──────────────────────────────────────────────────────────────────────
arr(CX, SWS_Y - BH/2, CX, FORK_Y)
seg(EAX, FORK_Y, EBX, FORK_Y)
arr(EAX, FORK_Y, EAX, EHY + HH/2)
arr(EBX, FORK_Y, EBX, EHY + HH/2)

# ── Engine headers ────────────────────────────────────────────────────────────
box(EAX, EHY, HW, HH, "NHÁNH A  —  Tổng hợp Điện áp", bg=GRAY, fs=10.5)
box(EBX, EHY, HW, HH, "NHÁNH B  —  Mô hình Giải tích", bg=GRAY, fs=10.5)

# ── Engine A steps ────────────────────────────────────────────────────────────
arr(EAX, EHY - HH/2, EAX, A1Y + BH/2)
box(EAX, A1Y, BW, BH,
    "Vật lý Hệ thống + Bức xạ Anten",
    sub="Friis  ·  NEC 4nec2 pattern  ·  T_sys  ·  BW")

arr(EAX, A1Y - BH/2, EAX, A2Y + BH/2)
box(EAX, A2Y, BW, BH,
    "Cấu hình Mảng Anten",
    sub="Bố cục ENU  →  vector baseline")

arr(EAX, A2Y - BH/2, EAX, A3Y + BH/2)
box(EAX, A3Y, BW, BH,
    "Tổng hợp Điện áp từng Anten",
    sub="simulate_voltages()  ·  V_matrix [N×M]")

arr(EAX, A3Y - BH/2, EAX, A4Y + BH/2)
box(EAX, A4Y, BW, BH,
    "Biến đổi (u, v, w) Hình học",
    sub="ENU  →  XYZ  →  uvw  (TMS Eq. 4.1)")

arr(EAX, A4Y - BH/2, EAX, A5Y + BH/2)
box(EAX, A5Y, BW, BH,
    "Bộ Tương quan + Tích lũy",
    sub="correlate()  ·  dump = INTEGRATION_BINS")

# A5 → VIS: short vertical, horizontal, diagonal arrow
arr(EAX, A5Y - BH/2, EAX, MERGE_Y)
seg(EAX, MERGE_Y, CX - VIS_W/2, MERGE_Y)
ax.annotate("", xy=(CX, VIS_Y + BH/2), xytext=(CX - VIS_W/2, MERGE_Y),
            arrowprops=dict(arrowstyle="-|>", color="black",
                            lw=1.8, mutation_scale=14), zorder=2)

# ── Engine B steps ────────────────────────────────────────────────────────────
arr(EBX, EHY - HH/2, EBX, B1Y + BH/2)
box(EBX, B1Y, BW, BH,
    "Mô hình Độ sáng Nguồn",
    sub="Đĩa Mặt Trời  ·  đường kính θ☉ = 0.53°")

arr(EBX, B1Y - BH/2, EBX, B2Y + BH/2)
box(EBX, B2Y, BW, BH,
    "Định lý van Cittert–Zernike",
    sub="V(u,v) = ∫∫ I(l,m) e^{−2πi(ul+vm)} dl dm")

arr(EBX, B2Y - BH/2, EBX, B3Y + BH/2)
box(EBX, B3Y, BW, BH,
    "Hiệu chỉnh Pha Fringe-Stop",
    sub="e^{+2πiw(√(1−l²−m²)−1)}")

# B3 → VIS: dashed vertical + horizontal, solid diagonal arrow
seg(EBX, B3Y - BH/2, EBX, MERGE_Y, dashed=True)
seg(EBX, MERGE_Y, CX + VIS_W/2, MERGE_Y, dashed=True)
ax.annotate("", xy=(CX, VIS_Y + BH/2), xytext=(CX + VIS_W/2, MERGE_Y),
            arrowprops=dict(arrowstyle="-|>", color="black",
                            lw=1.8, mutation_scale=14), zorder=2)

# ── Visibilities ──────────────────────────────────────────────────────────────
box(CX, VIS_Y, VIS_W, BH,
    "Tầm nhìn  V(u, v, w)",
    sub="shape: (N_dumps × N_baselines)  ·  complex64")

# ── Common imaging ────────────────────────────────────────────────────────────
arr(CX, VIS_Y - BH/2, CX, IMG_Y + BH/2)
box(CX, IMG_Y, IMG_W, BH,
    "Giai đoạn Tạo ảnh Chung  —  make_dirty_image()",
    sub="Gridding  →  FFT 2D  →  Dirty Image + PSF  ·  FOV = 3°  ·  Grid 256×256",
    fs=10.5)

# ── Lane labels (right margin) ────────────────────────────────────────────────
ax.text(15.6, (EHY + A5Y)/2, "NHÁNH A",
        fontsize=9, color="black", fontweight="bold",
        rotation=90, ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=GRAY,
                  edgecolor="black", linewidth=1.2))
ax.text(0.4, (EHY + B3Y)/2, "NHÁNH B",
        fontsize=9, color="black", fontweight="bold",
        rotation=90, ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=GRAY,
                  edgecolor="black", linewidth=1.2))

plt.savefig(r"E:\1A DATN REAL\figure_4_1_pipeline.png",
            dpi=200, bbox_inches="tight", facecolor="white")
print("Saved: E:\\1A DATN REAL\\figure_4_1_pipeline.png")
