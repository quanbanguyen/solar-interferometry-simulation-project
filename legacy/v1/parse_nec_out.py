"""
parse_nec_out.py
----------------
Đọc giản đồ bức xạ từ file .out (4nec2), THỰC HIỆN XOAY TRỤC BỨC XẠ (Y -> Z),
nội suy lưới và chuyển sang định dạng .npz cho primary_beam.py.

Chạy:
    python parse_nec_out.py input.out output.npz
"""
import numpy as np
from scipy.interpolate import griddata

def parse_and_rotate_nec_out(path):
    theta_list, phi_list, gain_list = [], [], []
    with open(path, "r", errors="ignore") as f:
        lines = f.readlines()

    in_block = False
    for ln in lines:
        if "RADIATION PATTERNS" in ln:
            in_block = True
            continue
        if not in_block:
            continue
        # Dừng nếu gặp khối khác
        if in_block and ln.strip().startswith("- - -") and "RADIATION" not in ln:
            break
        
        parts = ln.split()
        if len(parts) >= 5:
            try:
                # 4NEC2 xuất theta(0) là trục Z.
                th = float(parts[0])
                ph = float(parts[1])
                tot = float(parts[4])
            except ValueError:
                continue
            theta_list.append(th)
            phi_list.append(ph)
            gain_list.append(tot)

    if not gain_list:
        raise RuntimeError("Không tìm thấy bảng RADIATION PATTERNS trong file .out")

    # 1. Chuyển đổi mảng sang Radian
    theta_rad = np.radians(theta_list)
    phi_rad = np.radians(phi_list)
    gain_raw = np.array(gain_list)

    # 2. Chuyển sang tọa độ Đề-các (Cartesian)
    x_old = np.sin(theta_rad) * np.cos(phi_rad)
    y_old = np.sin(theta_rad) * np.sin(phi_rad)
    z_old = np.cos(theta_rad)

    # 3. Phép Xoay Trục 3D (Đưa búp sóng từ trục Y vươn lên thành trục Z)
    x_new = x_old
    y_new = -z_old
    z_new = y_old

    # Kẹp giá trị z_new để tránh lỗi float gây ra NaN trong hàm arccos
    z_new = np.clip(z_new, -1.0, 1.0)

    # 4. Chuyển về lại tọa độ Cầu của Bầu trời thực tế
    theta_sky = np.arccos(z_new)
    phi_sky = np.arctan2(y_new, x_new)
    phi_sky = np.mod(phi_sky, 2 * np.pi)

    # 5. Thiết lập Lưới Đều (Regular Grid) cho primary_beam.py
    # Giả định phân giải lưới là 1 độ. Nếu chạy mô phỏng 4nec2 bước 5 độ, 
    # thì phân giải 1 độ ở đây giúp đồ thị mượt hơn.
    grid_theta_deg = np.arange(0, 91, 1.0)   # Góc Thiên đỉnh -> Chân trời (0 -> 90)
    grid_phi_deg = np.arange(0, 360, 1.0)    # Phương vị (0 -> 359)
    
    # Tạo ma trận lưới (mesh) bằng numpy
    th_mesh, ph_mesh = np.meshgrid(np.radians(grid_theta_deg), np.radians(grid_phi_deg), indexing='ij')

    # 6. Nội Suy (Interpolation)
    # Ánh xạ các điểm bị phân tán sau khi xoay vào một ma trận (len(theta) x len(phi)) vuông vức
    points = np.column_stack((theta_sky, phi_sky))
    
    # Những tọa độ nằm ngoài dữ liệu xoay (ví dụ đâm xuống đất) được gán là -50 dBi (Noise floor)
    gain_grid = griddata(points, gain_raw, (th_mesh, ph_mesh), method='cubic', fill_value=-50.0)

    return grid_theta_deg, grid_phi_deg, gain_grid


if __name__ == "__main__":
    import os

    src = r"E:\1A DATN REAL\4nec2-out\YAGI_610_UFRAME.out.txt"
    out_dir = r"E:\1A DATN REAL\primary beam folder"
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "YAGI_610_UFRAME.npz")

    print(f"Input : {src}")
    print(f"Output: {dst}")
    print("Đang đọc, xoay trục 3D và nội suy dữ liệu...")
    theta_deg, phi_deg, gain_dBi = parse_and_rotate_nec_out(src)

    gmax = float(np.nanmax(gain_dBi))
    imax = np.unravel_index(np.nanargmax(gain_dBi), gain_dBi.shape)

    # Xuất ra file chuẩn cho primary_beam.py
    np.savez(dst,
             theta_deg=theta_deg,
             phi_deg=phi_deg,
             gain_dBi=gain_dBi,
             gain_max_dBi=gmax,
             freq_MHz=610.0)

    print(f"Hoàn tất: Tạo lưới {gain_dBi.shape[0]} theta x {gain_dBi.shape[1]} phi")
    print(f"Gain đỉnh = {gmax:.2f} dBi hướng thẳng lên tại theta={theta_deg[imax[0]]:.0f}°, phi={phi_deg[imax[1]]:.0f}°")
    print(f"Đã lưu file chuẩn -> {dst}")