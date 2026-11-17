"""
primary_beam.py  (bản cập nhật)
-------------------------------
Nạp giản đồ bức xạ từ .npz (do parse_nec_out.py tạo ra) và áp làm primary beam.
Bản này TỰ nhận diện hướng boresight = điểm gain cực đại, nên hoạt động với
MỌI quy ước góc:
  - quy ước chuẩn NEC : theta 0..180, phi 0..360
  - quy ước 4nec2 GUI : theta -180..0, phi 0..360
Không cần biết trước boresight nằm ở đâu.

Hai cách truy vấn:
  1) response_*(theta, phi)        -> theo toạ độ tuyệt đối trong file
  2) response_*_offset(delta_deg)  -> theo GÓC LỆCH so với boresight
     (tiện cho interferometer: chỉ cần góc lệch của nguồn so với tâm búp)
"""
import numpy as np
from scipy.interpolate import RegularGridInterpolator


class PrimaryBeam:
    def __init__(self, npz_path):
        d = np.load(npz_path)
        self.theta = np.asarray(d["theta_deg"], float)
        self.phi = np.asarray(d["phi_deg"], float)
        self.gain_dBi = np.asarray(d["gain_dBi"], float)
        self.freq_MHz = float(d["freq_MHz"]) if "freq_MHz" in d else None

        i, j = np.unravel_index(np.nanargmax(self.gain_dBi), self.gain_dBi.shape)
        self.boresight = (self.theta[i], self.phi[j])
        self.gain_max_dBi = float(self.gain_dBi[i, j])

        self.A_power = 10.0 ** ((self.gain_dBi - self.gain_max_dBi) / 10.0)
        self._interp = RegularGridInterpolator(
            (self.theta, self.phi), self.A_power,
            bounds_error=False, fill_value=0.0)

    def response_power(self, theta_deg, phi_deg):
        theta_deg = np.atleast_1d(np.asarray(theta_deg, float))
        phi_deg = np.atleast_1d(np.asarray(phi_deg, float))
        pts = np.stack([theta_deg, phi_deg], axis=-1)
        return self._interp(pts)

    def response_voltage(self, theta_deg, phi_deg):
        return np.sqrt(self.response_power(theta_deg, phi_deg))

    def response_power_offset(self, delta_deg):
        th0, ph0 = self.boresight
        delta_deg = np.atleast_1d(np.asarray(delta_deg, float))
        return self.response_power(th0 + delta_deg, np.full_like(delta_deg, ph0))

    def response_voltage_offset(self, delta_deg):
        return np.sqrt(self.response_power_offset(delta_deg))

    def hpbw_deg(self):
        d = np.linspace(-90, 90, 3601)
        p = 10 * np.log10(np.clip(self.response_power_offset(d), 1e-12, None))
        c = np.argmin(np.abs(d)); r = c; l = c
        while r < len(p) - 1 and p[r] > -3: r += 1
        while l > 0 and p[l] > -3: l -= 1
        return d[r] - d[l]


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "real_pattern.npz"
    b = PrimaryBeam(path)
    print(f"File           : {path}")
    print(f"Tần số         : {b.freq_MHz} MHz")
    print(f"Gain đỉnh      : {b.gain_max_dBi:.2f} dBi")
    print(f"Boresight      : theta={b.boresight[0]:.0f}, phi={b.boresight[1]:.0f}")
    print(f"HPBW (-3 dB)   : ~{b.hpbw_deg():.0f} deg")
    print(f"Đáp ứng boresight             : {b.response_power_offset(0)[0]:.3f}")
    print(f"Đáp ứng lệch 10 deg (cs)      : {b.response_power_offset(10)[0]:.3f}")
    print(f"Đáp ứng lệch 10 deg (đ.áp)    : {b.response_voltage_offset(10)[0]:.3f}")
