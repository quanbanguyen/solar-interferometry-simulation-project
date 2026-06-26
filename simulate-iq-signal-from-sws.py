# %% CELL 1: KHỞI TẠO VÀ IMPORT THƯ VIỆN
import csv
import os
import numpy as np
import matplotlib.pyplot as plt

print("Cell 1: Đã nạp thư viện thành công!")

# %% CELL 2: ĐỌC DỮ LIỆU TỪ FILE CSV VÀ LÀM SẠCH LẦN CUỐI
# (Chạy cell này 1 lần duy nhất để load dữ liệu vào RAM)
input_file = r'E:\APSIN\xlsx\solar_signal_cleaned.csv'
sfu_raw_list = []

print(f"Đang đọc dữ liệu từ: {input_file}...")
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader) # Bỏ qua dòng tiêu đề (Time_Index, Freq_245...)
    
    for row in reader:
        if len(row) > 3:
            try:
                # Cột Freq_610 nằm ở vị trí thứ 4 (index 3)
                sfu_raw_list.append(float(row[3]))
            except ValueError:
                pass

# Ép kiểu an toàn bằng numpy và diệt mọi NaN/Inf rác nếu có
sfu_raw = np.array(sfu_raw_list, dtype=np.float64)
sfu_raw = np.nan_to_num(sfu_raw, nan=0.0, posinf=0.0, neginf=0.0)

print(f"Cell 2 Xong! Đã nạp {len(sfu_raw)} mẫu dữ liệu 610MHz vào bộ nhớ.")

# %% CELL 3: XỬ LÝ TÍN HIỆU SỐ (DSP) & TẠO I/Q BASEBAND
# (Bạn có thể thoải mái sửa thông số nhiễu, tần số ở cell này và chạy lại độc lập)
N_SAMPLES = 2000  # Số mẫu xuất ra cho FPGA

t_raw = np.linspace(0, 1, len(sfu_raw))
t_fpga = np.linspace(0, 1, N_SAMPLES)

# Nội suy giãn dữ liệu
sfu_data = np.interp(t_fpga, t_raw, sfu_raw)
sfu_data = np.clip(sfu_data, a_min=0.0, a_max=None)
amplitude_envelope = np.sqrt(sfu_data)

# Thông số vật lý của trạm giao thoa
fc = 610e6              
baseline = 24.0
theta_deg = 30.0        
c = 299792458.0

# Tính độ lệch pha
tau = (baseline * np.sin(np.radians(theta_deg))) / c
phase_shift = -2 * np.pi * fc * tau 

# Nguồn nhiễu vô tuyến (Mặt trời + LNA)
cwgn_source = (np.random.randn(N_SAMPLES) + 1j * np.random.randn(N_SAMPLES)) / np.sqrt(2)
signal_core = amplitude_envelope * cwgn_source

noise_floor = 1.5 
n1 = np.sqrt(noise_floor/2) * (np.random.randn(N_SAMPLES) + 1j * np.random.randn(N_SAMPLES))
n2 = np.sqrt(noise_floor/2) * (np.random.randn(N_SAMPLES) + 1j * np.random.randn(N_SAMPLES))

# Tín hiệu chui vào cổng ADC
v1 = signal_core + n1
v2 = signal_core * np.exp(1j * phase_shift) + n2

print("Cell 3 Xong! Đã tạo xong tín hiệu băng gốc I/Q phức.")

# %% CELL 4: LƯỢNG TỬ HÓA VÀ XUẤT FILE HEX CHO VERILOG
output_dir = r"E:\APSIN\signal-for-fpga"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

filename = os.path.join(output_dir, "iq_stimulus.txt")

# Tìm đỉnh tín hiệu để lượng tử hóa không bị tràn bit
max_val = np.nanmax([np.nanmax(np.abs(v1.real)), np.nanmax(np.abs(v1.imag)), 
                     np.nanmax(np.abs(v2.real)), np.nanmax(np.abs(v2.imag))])

if max_val == 0 or np.isnan(max_val) or np.isinf(max_val):
    scale_factor = 1.0
else:
    scale_factor = 32767.0 / max_val

# Lượng tử hóa về 16-bit
i1_16b = np.round(v1.real * scale_factor).astype(np.int16)
q1_16b = np.round(v1.imag * scale_factor).astype(np.int16)
i2_16b = np.round(v2.real * scale_factor).astype(np.int16)
q2_16b = np.round(v2.imag * scale_factor).astype(np.int16)

# Ghi file
with open(filename, "w") as f:
    for n in range(N_SAMPLES):
        # Format Hex an toàn, chống tràn số
        h_i1 = format(int(i1_16b[n]) & 0xFFFF, '04x')
        h_q1 = format(int(q1_16b[n]) & 0xFFFF, '04x')
        h_i2 = format(int(i2_16b[n]) & 0xFFFF, '04x')
        h_q2 = format(int(q2_16b[n]) & 0xFFFF, '04x')
        f.write(f"{h_i1} {h_q1} {h_i2} {h_q2}\n")

print(f"Cell 4 Xong! Đã xuất file Hex an toàn tại: {filename}")

# %% CELL 5: KIỂM TRA TRỰC QUAN BẰNG ĐỒ THỊ (Tuỳ chọn)
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(sfu_raw, color='darkorange')
plt.title("Tín hiệu 610MHz gốc (từ file CSV)")
plt.xlabel("Mẫu")

plt.subplot(1, 2, 2)
plt.plot(np.abs(v1), color='blue', alpha=0.7, label='|V1| mô phỏng')
plt.title("Biên độ tín hiệu sau khi ghép nhiễu vô tuyến")
plt.xlabel("Mẫu")
plt.legend()

plt.tight_layout()
plt.show()
print("Cell 5 Xong! Hoàn tất toàn bộ quy trình.")