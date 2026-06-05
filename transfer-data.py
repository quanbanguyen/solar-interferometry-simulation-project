import csv

# ==========================================
# CHUYỂN ĐỔI NOTEPAD TXT SANG EXCEL (CSV)
# KHÔNG CẦN CÀI ĐẶT THÊM THƯ VIỆN
# ==========================================

input_file = r'E:\APSIN\solar_signal.txt.txt'  # File gốc của bạn
output_file = r'E:\APSIN\xlsx\solar_signal_cleaned.csv' # File xuất ra (Mở bằng Excel)

data_rows = []
error_count = 0

print(f"Đang đọc dữ liệu từ file: {input_file}...")

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Bỏ qua dòng trống
            if not line:
                continue
                
            # Xử lý dòng chứa nhiễu ////// (Vá lỗi tự động)
            if '//////' in line:
                error_count += 1
                if len(data_rows) > 0:
                    data_rows.append(data_rows[-1])
                continue
            
            # Cắt dòng thành các phần tử
            parts = line.split()
            
            try:
                # Ép kiểu thành số thực
                numeric_row = [float(p) for p in parts]
                data_rows.append(numeric_row)
            except ValueError:
                pass

    if len(data_rows) == 0:
        print("\n[LỖI]: Không tìm thấy bất kỳ dữ liệu số nào!")
    else:
        # Ghi dữ liệu ra file CSV
        print("Đang xuất dữ liệu ra file CSV...")
        with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out)
            
            # Tạo hàng tiêu đề (Headers)
            num_cols = len(data_rows[0])
            headers = [f"Cột_{i}" for i in range(num_cols)]
            
            # Đặt tên chuẩn nếu có đủ số lượng cột
            if num_cols > 3:
                headers[0] = "Time_Index"
                headers[1] = "Freq_245"
                headers[2] = "Freq_410"
                headers[3] = "Freq_610" 
                headers[4] = "Freq_1415"
                headers[5] = "Freq_2695"
                headers[6] = "Freq_4995" 
                headers[7] = "Freq_8800"
                headers[8] = "Freq_15400"
              
            writer.writerow(headers) # Ghi tiêu đề
            writer.writerows(data_rows) # Ghi toàn bộ dữ liệu
        
        print(f"\n[THÀNH CÔNG] Đã lưu {len(data_rows)} dòng dữ liệu vào file: {output_file}")
        print(f"Số dòng chứa '//////' đã được tự động vá lỗi: {error_count}")
        print("-> BẠN HÃY NHẤP ĐÚP CHUỘT VÀO FILE .CSV TRONG THƯ MỤC ĐỂ MỞ BẰNG EXCEL NHÉ!")

except FileNotFoundError:
    print(f"\n[LỖI]: Không tìm thấy file '{input_file}'.")