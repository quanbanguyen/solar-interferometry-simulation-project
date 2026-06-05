import numpy as np
import matplotlib.pyplot as plt

# 1. KHỞI TẠO CÁC THÔNG SỐ (Tương tự dự án thực tế)
grid_size = 256        # Lưới Fourier tổng (Main Grid)
subgrid_size = 32      # Lưới phụ miền ảnh (Subgrid)
main_grid = np.zeros((grid_size, grid_size), dtype=complex)
subgrid = np.zeros((subgrid_size, subgrid_size), dtype=complex)

# 2. TẠO DỮ LIỆU THÔ GIẢ LẬP (Visibilities từ 2 ăng-ten)
# Mỗi data gồm: Giá trị đo được (V) và Tọa độ (u, v, w)
visibilities = [1.5 + 0.2j, 1.2 - 0.1j, 0.9 + 0.5j] 
uvw_coords = [(10, 15, 2), (11, 16, 2.1), (12, 17, 2.2)]

# 3. BƯỚC 1: GRIDDER KERNEL (Gom dữ liệu vào Subgrid miền ảnh)
for V, (u, v, w) in zip(visibilities, uvw_coords):
    for y in range(subgrid_size):
        for x in range(subgrid_size):
            # Tính góc lệch pha alpha (Mô phỏng W-term đơn giản)
            # Trong thực tế, hàm này phức tạp hơn phụ thuộc vào l, m
            alpha = 0.05 * (x*u + y*v + w) 
            
            # Chuyển đổi Euler: Phi = cos(alpha) + i*sin(alpha)
            Phi = np.cos(alpha) + 1j * np.sin(alpha)
            
            # Nhân chập và Cộng dồn vào Subgrid (Tính chất phân phối)
            subgrid[y, x] += Phi * V

# 4. BƯỚC 2: SUBGRID FFT (Chuyển Subgrid sang miền Fourier)
# Dùng hàm FFT 2D của Numpy (Tương đương khối FFT 128/256 điểm trên mạch phần cứng)
subgrid_fft = np.fft.fft2(subgrid)

# 5. BƯỚC 3: ADDER KERNEL (Cộng Subgrid vào Lưới tổng)
# Xác định vị trí trung tâm để cộng vào lưới chính (Giả sử ném vào giữa lưới)
cx, cy = grid_size // 2, grid_size // 2
half = subgrid_size // 2

# Cộng dồn mảng Fourier nhỏ vào mảng Fourier lớn
main_grid[cy-half : cy+half, cx-half : cx+half] += np.fft.fftshift(subgrid_fft)

# 6. BƯỚC TẠO ẢNH: iFFT Lưới tổng để xem bức ảnh thô (Residual Image)
dirty_image = np.fft.ifftshift(np.fft.ifft2(main_grid)).real

# 7. HIỂN THỊ KẾT QUẢ
plt.imshow(dirty_image, cmap='hot')
plt.title("Bức ảnh thô (Residual Image) từ IDG")
plt.colorbar()
plt.show()