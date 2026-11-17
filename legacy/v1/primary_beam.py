"""
primary_beam.py
---------------
Nạp giản đồ bức xạ (radiation pattern) đã trích từ 4nec2 và áp dụng làm
primary beam (giản đồ tia chính) cho pipeline giao thoa kế.

Dữ liệu nguồn: yagi_pattern_610MHz.npz
    theta_deg : (181,)      góc cực, đo từ trục +z (0..180)
    phi_deg   : (73,)       góc phương vị (0..360)
    gain_dBi  : (181,73)    gain toàn phần theo dBi
    freq_MHz, gain_max_dBi

Quy ước trục (khớp file .nec của bạn):
    X = hướng baseline (Đông-Tây)
    Y = trục boom Yagi  -> main beam hướng +Y  (theta=90, phi=90)
    Z = phương thẳng đứng
"""
import numpy as np
from scipy.interpolate import RegularGridInterpolator


class PrimaryBeam:
    def __init__(self, npz_path):
        d = np.load(npz_path)
        self.theta = d["theta_deg"]          # (Ntheta,)
        self.phi = d["phi_deg"]              # (Nphi,)
        self.gain_dBi = d["gain_dBi"]        # (Ntheta, Nphi)
        self.gain_max_dBi = float(d["gain_max_dBi"])
        self.freq_MHz = float(d["freq_MHz"])

        # Gain TUYẾN TÍNH đã chuẩn hóa về boresight = 1.0
        # Đây là biên độ trường-điện áp nhân vào voltage stream.
        g_lin = 10.0 ** (self.gain_dBi / 10.0)
        self.A_power = g_lin / g_lin.max()           # đáp ứng theo CÔNG SUẤT (0..1)
        self.A_voltage = np.sqrt(self.A_power)       # đáp ứng theo BIÊN ĐỘ điện áp

        # Bộ nội suy (theo công suất, an toàn vì luôn >= 0)
        self._interp = RegularGridInterpolator(
            (self.theta, self.phi), self.A_power,
            bounds_error=False, fill_value=0.0,
        )

    def response_power(self, theta_deg, phi_deg):
        """Đáp ứng beam theo công suất tại (theta, phi). Boresight = 1.0."""
        theta_deg = np.atleast_1d(theta_deg)
        phi_deg = np.atleast_1d(phi_deg) % 360.0
        pts = np.stack([theta_deg, phi_deg], axis=-1)
        return self._interp(pts)

    def response_voltage(self, theta_deg, phi_deg):
        """Đáp ứng beam theo biên độ điện áp (= căn của công suất)."""
        return np.sqrt(self.response_power(theta_deg, phi_deg))


# ----------------------------------------------------------------------
# CÁCH DÙNG TRONG PIPELINE
# ----------------------------------------------------------------------
if __name__ == "__main__":
    beam = PrimaryBeam("yagi_pattern_610MHz.npz")
    print(f"Tần số      : {beam.freq_MHz:.0f} MHz")
    print(f"Gain đỉnh   : {beam.gain_max_dBi:.2f} dBi")

    # --- Ví dụ 1: lấy đáp ứng tại boresight và lệch 20 độ ---
    print("Boresight (theta=90, phi=90) :", beam.response_power(90, 90))
    print("Lệch 20 deg (theta=90, phi=70):", beam.response_power(90, 70))

    # --- Ví dụ 2: áp primary beam lên dòng điện áp thu được ---
    # Giả sử Mặt Trời transit, mỗi mẫu thời gian có toạ độ (theta_t, phi_t)
    # và điện áp "trần" V_sky (chưa tính beam):
    #
    #   theta_t, phi_t = pointing_of_sun(times)          # từ hour-angle
    #   A = beam.response_voltage(theta_t, phi_t)        # (Ntime,)
    #   V_received = A * V_sky                           # áp beam vào voltage stream
    #
    # Sau đó V_received của mỗi anten đi vào correlator để tính visibility.
    #
    # Muốn đổi sang CST sau này: chỉ cần xuất pattern CST ra cùng định dạng
    # (theta, phi, gain_dBi) và trỏ PrimaryBeam vào file .npz mới — phần
    # còn lại của pipeline KHÔNG phải sửa gì.
    print("\nModule sẵn sàng cắm vào pipeline.")
