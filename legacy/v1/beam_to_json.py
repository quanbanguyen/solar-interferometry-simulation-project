import numpy as np, json

npz_path = "UFRAME_primary_beam_610MHz.npz"   # đổi đường dẫn nếu cần
out_path  = "beam.json"

d     = np.load(npz_path)
# Keys thực tế: theta_deg (181,), phi_deg (361,), gain_dBi (181,361)
# Convention: theta = -elevation_above_horizon  (theta=-90 → el=90°=zenith, theta=0 → el=0°=horizon)
# phi = azimuth (0=N, 90=E, 180=S, 270=W theo hệ NEC2 ở đây)
theta    = d["theta_deg"]   # -180 … 0
gain_2d  = d["gain_dBi"]    # shape (181, 361)

# Chỉ lấy bán cầu trên (el 0..90° = theta -90..0)
mask         = (theta >= -90) & (theta <= 0)
theta_upper  = theta[mask]            # 91 điểm: -90 … 0
gain_upper   = gain_2d[mask, :]       # (91, 361)

# Envelope: lấy max gain theo phi tại mỗi góc ngưỡng → 1D elevation cut
gain_dBi_1d = gain_upper.max(axis=1)  # (91,)
el_deg       = (-theta_upper).tolist() # [90, 89, ..., 0]  (trên trước)

# Quy đổi sang tuyến tính chuẩn hóa 0..1
gain_max = gain_dBi_1d.max()
gain_lin = (10 ** ((gain_dBi_1d - gain_max) / 10)).tolist()

out = {
    "theta_deg":     el_deg,        # elevation above horizon, 90→0
    "gain":          gain_lin,      # linear normalized, 1.0 tại đỉnh
    "gain_dBi":      gain_dBi_1d.tolist(),
    "freq_MHz":      float(d["freq_MHz"]),
    "note":          "1D elevation envelope (max over phi), el=90 down to el=0"
}

with open(out_path, "w") as f:
    json.dump(out, f, indent=2)

print(f"Saved {out_path}  ({len(el_deg)} points, "
      f"peak={gain_max:.2f} dBi at el=90°)")
