import cmath
import math

def calculate_visibility(antenna1_iq, antenna2_iq):
    # Kiểm tra xem dữ liệu 2 ăng-ten có khớp độ dài không
    if len(antenna1_iq) != len(antenna2_iq) or len(antenna1_iq) == 0:
        print("Lỗi: Luồng dữ liệu không đồng bộ hoặc trống!")
        return

    num_samples = len(antenna1_iq)
    
    # Khởi tạo biến tổng là một số phức (0 + 0j)
    visibility_sum = 0j 

    # BƯỚC 1: TƯƠNG QUAN CHÉO VÀ TÍCH LŨY (Multiply & Accumulate)
    # Thực hiện phép toán: V = S1 * conj(S2)
    for i in range(num_samples):
        # Nhân mẫu của Ant1 với số phức liên hợp (conjugate) của Ant2
        visibility_sum += antenna1_iq[i] * antenna2_iq[i].conjugate()

    # BƯỚC 2: TÍCH PHÂN (Integration / Averaging)
    # Lấy trung bình để triệt tiêu nhiễu trắng
    final_visibility = visibility_sum / num_samples

    # BƯỚC 3: TRÍCH XUẤT BIÊN ĐỘ VÀ PHA
    amplitude = abs(final_visibility) 
    phase_rad = cmath.phase(final_visibility) 
    phase_deg = math.degrees(phase_rad) # Đổi radian sang độ

    # In kết quả ra màn hình
    print("--- KẾT QUẢ TƯƠNG QUAN ---")
    print(f"Số mẫu tích lũy (Integration): {num_samples}")
    # Làm tròn 4 chữ số thập phân cho dễ nhìn
    print(f"Visibility (Số phức): {final_visibility.real:.4f} + {final_visibility.imag:.4f}j")
    print(f"-> BIÊN ĐỘ (Sức mạnh chớp bão): {amplitude:.4f}")
    print(f"-> PHA (Góc định vị): {phase_deg:.4f} độ")

if __name__ == "__main__":
    # TẠO DỮ LIỆU GIẢ LẬP TỪ 2 ĂNG-TEN SDRplay (Dạng I + Qj)
    # Trong Python, số ảo được ký hiệu là 'j' thay vì 'i'
    stream_ant1 = [1.0+0.5j, 0.8+0.6j, 1.2+0.3j, 0.9+0.7j]
    
    # Giả sử tín hiệu tới ăng-ten 2 bị trễ pha một chút so với ăng-ten 1
    stream_ant2 = [0.5+1.0j, 0.6+0.8j, 0.3+1.2j, 0.7+0.9j]

    # Chạy bộ Correlator
    calculate_visibility(stream_ant1, stream_ant2)