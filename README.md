# 🌞 Mô phỏng Giao thoa kế Vô tuyến Mặt Trời (610 MHz)
**Phát triển bởi:** Nguyễn Bá Quân 
Dự án này cung cấp một pipeline phần mềm hoàn chỉnh để mô phỏng và xử lý tín hiệu giao thoa vô tuyến Mặt Trời tại dải tần **610 MHz**. Hệ thống sử dụng dữ liệu quan trắc thực tế được trích xuất trực tiếp từ đài khí tượng vô tuyến **Learmonth (RSTN)** của cơ quan thời tiết vũ trụ Úc (SWS). 

> **💡 Điểm đáng lưu ý:** Đài Learmonth nằm ở múi giờ **UTC+8**, chỉ lệch +1 tiếng so với giờ Việt Nam (**UTC+7**). Điều này tạo điều kiện cực kỳ thuận lợi để đồng bộ, so sánh và đối chiếu kết quả mô phỏng với các hệ thống ăng-ten thực tế đang triển khai tại địa phương.

---

## 📂 Cấu trúc Thư mục (Repository Structure)

Để hệ thống hoạt động trơn tru, dự án được tổ chức theo cấu trúc sau:

* **`the_newest_heart_of_project.ipynb`**: File Jupyter Notebook trung tâm. Đây là "trái tim" của dự án, chứa toàn bộ luồng chạy chính từ tiền xử lý, tính toán vật lý đến xuất dữ liệu cho FPGA.
* **`interfsim.py`**: Thư viện lõi chứa engine toán học của hệ thống giao thoa. Bắt buộc phải đặt cùng thư mục với file Notebook trên.
* **`raw_signal_from_sws/`**: Nơi lưu trữ dữ liệu tín hiệu Mặt Trời thô tải về từ trang SWS (định dạng `.txt`).
* **`Cell_I_Data/`**: Thư mục chứa các ảnh kết quả đầu ra của **Cell I**. Do Cell I thực hiện các tính toán mô phỏng phần cứng rất nặng, nó sẽ không in ảnh tương tác trực tiếp lên Notebook để tránh treo máy, mà xuất thẳng file ảnh vào thư mục này.
* **`4nec2-out/`**: Chứa các file kết quả mô phỏng giản đồ bức xạ (Radiation Pattern) trích xuất từ phần mềm 4NEC2 để đưa vào hệ thống.
* **`tong hop file note và bao cao/`**: Thư mục tài liệu cực kỳ quan trọng dành cho người mới. Chứa báo cáo nghiên cứu, kết luận hệ thống và các sơ đồ luồng (Flowchart) giải thích chi tiết cơ chế hoạt động của từng bài toán.

---

## 🚀 Hướng dẫn Sử dụng (Quick Start Guide)

Dự án được thiết kế để dễ dàng triển khai. Hãy làm theo các bước sau để chạy mô phỏng:

### Bước 1: Chuẩn bị môi trường
1. Clone repository này về máy tính cá nhân.
2. Đảm bảo bạn đã cài đặt Python và các thư viện cần thiết (Numpy, Scipy, Plotly, Jupyter Notebook).
3. **Lưu ý tối quan trọng:** Đảm bảo file `interfsim.py` nằm chung thư mục gốc với file `the_newest_heart_of_project.ipynb`. Nếu thiếu file này, các mô hình toán học (Van Cittert-Zernike, tính trễ pha) sẽ không hoạt động.

### Bước 2: Chuẩn bị dữ liệu
1. Tải dữ liệu `.txt` của đài Learmonth từ SWS và đặt vào thư mục `raw_signal_from_sws/`.

### Bước 3: Cấu hình và Chạy Code
1. Mở file `the_newest_heart_of_project.ipynb` bằng Jupyter Notebook hoặc VS Code.
2. Chuyển đến **Cell 0 (Cấu hình dự án)**.
3. Thay đổi các đường dẫn gốc (root paths) và khai báo thư mục lưu trữ cho khớp với máy tính của bạn.
4. Chạy tuần tự từng Cell từ trên xuống dưới.
5. Khi chạy đến **Cell I**, vui lòng mở thư mục `Cell_I_Data/` để kiểm tra hình ảnh kết quả mô phỏng phần cứng thay vì đợi hiển thị trên màn hình Notebook.

---

## 📚 Tài liệu tham khảo & Đọc hiểu (Documentation)

Nếu bạn là người mới tiếp cận hệ thống, vui lòng **KHÔNG BỎ QUA** thư mục `tong hop file note và bao cao/`. 

Trình tự đọc khuyến nghị để hiểu sâu dự án:
1. Đọc file **"TỔNG QUAN VỀ TOÀN BỘ HỆ THỐNG"** để nắm bắt lý thuyết Giao thoa kế vô tuyến và thiết kế hệ thống.
2. Tham khảo các file **Sơ đồ luồng (Flowchart)** để hiểu cách dữ liệu di chuyển qua từng Cell (Từ Analog -> Lượng tử hóa 16-bit số -> Correlator -> Tạo ảnh Dirty Image).
3. Đọc các báo cáo và kết luận đi kèm để nắm được các thông số kiểm chuẩn (Validation) và cấu hình tối ưu.

---
*Dự án hướng tới việc cung cấp dữ liệu testbench 16-bit fixed-point có độ chính xác cao phục vụ cho các khối xử lý tín hiệu DSP/FFT trên nền tảng FPGA.*
## 🔬 Đánh giá Cấu hình Mảng Ăng-ten (Forward Modeling & Topology Sweep)

Bên cạnh việc xử lý tín hiệu thực tế để cấp luồng dữ liệu 16-bit cho FPGA, dự án tích hợp một khối Đánh giá Cấu hình Mảng (Cell H & Cell I) dựa trên định lý Van Cittert-Zernike. Khối này không sử dụng dữ liệu quan trắc SWS mà giả lập một nguồn phát đĩa Mặt Trời lý tưởng (đường kính góc ~32 arcmin) nhằm mục đích kiểm chuẩn khả năng phân giải của hệ thống.

**Mục tiêu học thuật:**
1. **Kiểm định khả năng phân giải (Cell H):** Chứng minh hệ thống giao thoa với baseline mở rộng (lên tới 130m tại 610MHz) có đủ độ phân giải không gian để quan sát cấu trúc mở rộng của đĩa Mặt Trời thay vì chỉ nhìn thấy một điểm sáng (point source).
2. **Tối ưu hóa hình học ăng-ten (Cell I):** Tự động hóa quá trình quét (sweep) qua 5 cấu hình mảng khác nhau (Linear Đông-Tây, Cross, Tee, Random 2D). Hệ thống sử dụng backend `Agg` của matplotlib để render ngầm và xuất trực tiếp ra ổ cứng các dữ liệu đối chiếu:
   * **u-v coverage:** Đánh giá độ lấp đầy mặt phẳng tần số không gian do sự tự quay của Trái Đất (Earth Rotation Synthesis).
   * **Synthesized Beam (PSF):** Đánh giá mức độ thất thoát năng lượng vào các sidelobe của từng cấu hình.
   * **Dirty Image & Dynamic Range:** So sánh chất lượng ảnh tái tạo (Tỷ số Peak/RMS) để làm cơ sở luận chứng cho việc lựa chọn cấu hình ăng-ten triển khai thực tế ngoài trời.

> Toàn bộ kết quả đối chiếu không gian (Montage) và file dữ liệu `npz` siêu nhẹ được hệ thống tự động dọn dẹp RAM (`gc.collect()`) và tập hợp tại thư mục `Cell_I_Data/sweep_layouts` để phục vụ công tác báo cáo.
