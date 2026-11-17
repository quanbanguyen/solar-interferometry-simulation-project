"""
demo_primary_beam.py
====================
Chạy thử primary beam thật (trích từ 4nec2) trong đúng kịch bản transit
của notebook HUS.ipynb, và so sánh với mô hình Gaussian lý tưởng đang dùng.

Chạy:  python demo_primary_beam.py
Cần:   primary_beam.py  và  UFRAME_primary_beam_610MHz.npz  cùng thư mục.
"""
import numpy as np
from primary_beam import PrimaryBeam

# ── 1. Nạp beam thật ──────────────────────────────────────────────
beam = PrimaryBeam("UFRAME_primary_beam_610MHz.npz")
print(f"Đã nạp beam: {beam.freq_MHz:.0f} MHz, gain đỉnh {beam.gain_max_dBi:.2f} dBi, "
      f"HPBW ~{beam.hpbw_deg():.0f}°")

# ── 2. Vài giá trị lẻ để cảm nhận ─────────────────────────────────
print("\nĐáp ứng (điện áp) theo góc lệch boresight:")
for d in [0, 10, 26, 45, 60, 84]:
    print(f"  lệch {d:3d}° -> {beam.response_voltage_offset(d)[0]:.4f}")

# ── 3. Mô phỏng transit như Cell 3 của notebook ───────────────────
# Mặt Trời quét góc giờ -84.2° .. +84.2° trong 12 giờ ban ngày
N = 50000
H_deg = np.linspace(-84.2, 84.2, N)        # = theta_array_deg trong notebook

# (a) Beam THẬT từ NEC
beam_nec = beam.response_voltage_offset(H_deg)

# (b) Beam Gaussian cũ của notebook (HPBW = 60°)
HPBW_old = 60.0
beam_gauss = np.exp(-4 * np.log(2) * (H_deg / HPBW_old) ** 2)

print(f"\nTại đỉnh transit (H=0):  NEC={beam_nec[N//2]:.3f}  Gauss={beam_gauss[N//2]:.3f}")
print(f"Tại rìa (H=±84°):        NEC={beam_nec[0]:.3f}  Gauss={beam_gauss[0]:.3f}")

# ── 4. Vẽ so sánh ─────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(9, 4.5))
    plt.plot(H_deg, beam_nec, lw=2, label="Beam THẬT (NEC, UFRAME)")
    plt.plot(H_deg, beam_gauss, "--", lw=1.5, label=f"Gaussian cũ (HPBW {HPBW_old:.0f}°)")
    plt.axhline(1/np.sqrt(2), color="r", ls=":", lw=1, label="-3 dB (nửa công suất)")
    plt.xlabel("Góc giờ Mặt Trời H (độ) = góc lệch boresight")
    plt.ylabel("Đáp ứng beam (điện áp, chuẩn hóa)")
    plt.title("Primary beam: NEC thật vs Gaussian lý tưởng")
    plt.grid(alpha=0.3); plt.legend()
    plt.tight_layout(); plt.savefig("demo_beam_compare.png", dpi=130)
    print("\nĐã lưu hình so sánh -> demo_beam_compare.png")
except ImportError:
    print("\n(matplotlib chưa cài — bỏ qua phần vẽ)")

print("\nDemo xong. Đây chính là mảng beam_nec sẽ thay cho biến primary_beam trong Cell 3.")
