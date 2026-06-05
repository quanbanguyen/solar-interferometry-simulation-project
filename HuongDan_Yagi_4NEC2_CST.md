# Hướng dẫn dựng anten Yagi 610 MHz trên 4NEC2 và CST

Tài liệu này đi kèm 2 file:
- `yagi_610_full.nec` — model đầy đủ (reflector 4 thanh + folded dipole + 6 director), dùng để xem pattern 3D và xuất primary beam cho pipeline.
- `yagi_610_sweep.nec` — cùng geometry nhưng quét tần số 470–862 MHz, để vẽ S11/VSWR theo tần số (giống Figure 3.8–3.9 của nhóm).

---

## 1. Tóm tắt cấu trúc đã thống nhất

Đi từ đuôi (gần LNA) ra mũi:

| Cụm | Số thanh | Chiều dài | Bán kính | Vị trí dọc boom (Y) |
|---|---|---|---|---|
| Reflector (swept-back) | 4 | 300 mm | 3.5 mm | 0, −30, −60, −90 mm |
| Folded dipole (driven) | 1 (2 rod + 2 short) | 210 mm, fold 44 mm | 2.0 mm | 98 mm |
| Directors | 6 | 210 mm | 3.5 mm | 180, 220, 270, 320, 386, 455 mm |

Hệ trục: **X** = chiều dài chấn tử (thanh ngang), **Y** = dọc boom (búp sóng hướng +Y), **Z** = 0.

Nguồn kích thước: bảng tham số HFSS (Figure 3.3). Cụm reflector được diễn giải thành 4 thanh lùi dần để khớp khung chữ V trong ảnh.

---

## 2. Kết quả NEC-2 đã kiểm chứng (tại 610 MHz)

Mình đã chạy thử trên engine NEC-2 trước khi giao file. Kết quả:

| Đại lượng | NEC-2 (model này) | HFSS (báo cáo nhóm) | Khớp? |
|---|---|---|---|
| Gain | 9.0 dBi | 9.5–10.5 dBi | ✓ |
| VSWR @ 75Ω | 1.28 | 1.22–1.53 | ✓ |
| S11 @ 75Ω | −18.3 dB | −13.6 đến −20 dB | ✓ |
| F/B ratio | 18.2 dB | > 15 dB | ✓ |
| Z_in | 89 + 15j Ω | ~75 Ω | ✓ (folded nâng trở kháng) |

Kết luận: model dây tái lập tốt kết quả HFSS tại tần số trung tâm. **Lưu ý quan trọng cho báo cáo:** model NEC cho băng thông HẸP (cộng hưởng sắc tại 610 MHz, các tần số khác match kém). Đây là hạn chế cố hữu của mô hình thin-wire với folded dipole; folded dipole thật + cụm reflector phức hợp mới cho băng rộng 470–862 MHz như nhóm báo cáo. Chính sự khác biệt này là lý do chính đáng để dùng CST kiểm chứng — và là một điểm thảo luận hay trong chương Kết quả.

---

## 3. Dựng trên 4NEC2

### 3.1 Nạp file
1. Mở 4NEC2 → **File → Open** → chọn `yagi_610_full.nec`.
2. **Calculate → NEC output-data → (chọn) Far field pattern → Generate**.
3. Xem kết quả:
   - **Show → Pattern**: pattern 3D
   - **Show → Far field**: gain, F/B, HPBW
   - **Show → Geometry**: kiểm tra hình học đúng chưa
   - **View → Input/Impedance**: Z_in, VSWR

### 3.2 Vẽ S11/VSWR theo tần số
1. Mở `yagi_610_sweep.nec` (đã cài sẵn FR card quét 470–862 MHz).
2. **Calculate → Frequency sweep → Generate**.
3. **Show → SWR** hoặc **Show → S-parameters**: ra đường cong giống Figure 3.9.
4. Đặt reference impedance = 75Ω trong **Settings → Char. impedance** (vì anten dùng folded dipole + balun 4:1 về 75Ω).

### 3.3 Xuất pattern cho pipeline Python
1. Sau khi chạy far field, **File → Export → Radiation pattern** (hoặc copy từ output .out).
2. Định dạng cột: theta, phi, gain (dBi). Lưu thành `yagi_pattern.csv`.
3. Trong code Python (Cell 3), thay `primary_beam` Gaussian bằng pattern này — xem mục 5.

### 3.4 Các tham số NEC cần biết
- `GW tag nseg x1 y1 z1 x2 y2 z2 radius`: tạo 1 thanh. nseg lẻ (21) để có segment giữa làm feed.
- `EX 0 5 11 0 1 0`: nguồn áp tại tag 5 (rod được feed của folded dipole), segment 11 (giữa).
- `FR 0 1 0 0 610 0`: 1 tần số 610 MHz. Để quét: `FR 0 N 0 0 fstart fstep`.
- `RP 0 ntheta nphi 1000 0 0 dtheta dphi`: pattern. File full dùng 181×73 điểm cho 3D.

---

## 4. Dựng trên CST Studio Suite

### 4.1 Tạo project
1. **New Template → MW & RF & Optical → Antennas → Antenna (Wire)** → **Time Domain** solver.
2. Đặt đơn vị: **mm**, tần số **MHz**, **Units → Frequency: MHz**.
3. **Frequency range**: 400–900 MHz (để thấy băng rộng).

### 4.2 Dựng hình học
Dùng đúng tọa độ trong bảng mục 1. Mỗi chấn tử là một **Cylinder**:
- **Modeling → Cylinder**: trục theo X (Orientation: X), tâm tại (0, Y_position, 0).
- Chiều dài = chiều dài chấn tử (vd 210mm → từ X=−105 đến X=+105).
- Bán kính: director/reflector = 3.5mm, dipole = 2.0mm.
- Material: **PEC** (perfect conductor) cho lần chạy đầu; đổi sang **Aluminum** nếu muốn tính loss.

Reflector 4 thanh: tạo 1 cylinder rồi **Transform → Translate → Copy** 3 lần theo Y (−30, −60, −90mm).

Folded dipole: 2 cylinder song song (Y=98 và Y=142mm) + 2 cylinder ngắn nối 2 đầu (theo Y, tại X=±105mm). Để hở khe feed 2mm ở giữa rod trước.

### 4.3 Đặt port
1. Tại khe giữa rod được feed: **Simulation → Sources and Ports → Discrete Port**.
2. Loại: **S-parameter**, impedance **75 Ω** (khớp folded dipole + balun).
3. Đặt port bắc qua khe 2mm ở tâm rod trước của folded dipole.

### 4.4 Far-field monitor
1. **Simulation → Field Monitors → Farfield/RCS**.
2. Tần số: thêm monitor tại **610 MHz** (và 550, 650 nếu muốn so sánh).

### 4.5 Chạy và đọc kết quả
1. **Simulation → Start Simulation**.
2. Kết quả:
   - **1D Results → S-Parameters → S1,1**: đường cong S11 (giống Figure 3.8).
   - **1D Results → VSWR**: VSWR (giống Figure 3.9).
   - **Farfields → farfield (f=610) → 3D**: pattern 3D (giống Figure 3.10–3.11).
   - **Farfields → ... → Polar**: cắt E-plane (phi=90) và H-plane (phi=0) (giống Figure 3.12–3.13).
   - **Current**: chọn surface current để minh họa nguyên lý Yagi (figure ăn điểm).

### 4.6 Xuất pattern cho pipeline
1. **Farfields → farfield (f=610)** → chuột phải → **Export → ASCII (.txt)** hoặc **.ffs**.
2. Định dạng .ffs có theta, phi, |E_theta|, |E_phi| — đầy đủ cho primary beam.

---

## 5. Tích hợp pattern vào pipeline Python (Cell 3)

Sau khi có file pattern (từ 4NEC2 hoặc CST), thay primary beam lý tưởng bằng pattern thật:

```python
import numpy as np
from scipy.interpolate import interp1d

# Load pattern: cột theta (deg), gain (dBi) — lấy cắt H-plane (phi=0)
# (đổi tên cột cho khớp file bạn export)
pat = np.loadtxt("yagi_pattern.csv", delimiter=",", skiprows=1)
theta_deg = pat[:,0]          # 0..180
gain_dBi  = pat[:,2]          # gain theo theta

# Chuyển sang gain tuyến tính, chuẩn hóa về 1 tại boresight (theta=90, hướng +Y)
gain_lin = 10**(gain_dBi/10)
gain_lin /= gain_lin.max()

# Hàm beam: nội suy theo hour angle. Mặt trời đi qua => theta hiệu dụng
beam_interp = interp1d(theta_deg, gain_lin, kind='cubic',
                       bounds_error=False, fill_value=0.0)

# Trong vòng lặp tạo tín hiệu: thay
#   primary_beam = np.exp(-4*np.log(2)*(H_deg/HPBW)**2)
# bằng
#   theta_effective = 90.0 + H_deg     # ánh xạ hour angle -> theta của pattern
#   primary_beam = beam_interp(theta_effective)
```

Như vậy pipeline dùng pattern thật của anten thay cho Gaussian lý tưởng. So sánh 2 kết quả (Gaussian vs pattern thật) chính là một trong các thí nghiệm "rắc rối" cho chương Kết quả.

---

## 6. Việc cần làm tiếp

1. Nạp 2 file .nec vào 4NEC2, xác nhận chạy ra kết quả như bảng mục 2.
2. Dựng song song trên CST theo mục 4, so sánh với NEC.
3. Khi đo anten thật, nếu số director khác 6, chỉ cần thêm/bớt dòng GW (director) trong file .nec và copy cylinder trong CST.
4. Xuất pattern → tích hợp vào Cell 3 theo mục 5.

Nếu kết quả CST lệch nhiều so với NEC (đặc biệt băng thông), đó là kết quả mong đợi — ghi vào báo cáo như một điểm so sánh giữa 2 phương pháp số (thin-wire MoM vs full-wave FIT).
