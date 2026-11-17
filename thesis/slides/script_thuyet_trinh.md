# Script thuyết trình bảo vệ đồ án tốt nghiệp

**Đề tài:** End-to-End Simulation of a Four-Element UHF Radio Interferometer for Solar Radio Observation at 610 MHz
**Thời lượng phần chính:** ~12 phút (14 slide nội dung + title + outline)
**Thời lượng phần backup:** không tính giờ, chỉ dùng khi được hỏi

> Cách dùng: mỗi mục dưới đây ứng với đúng một slide trong `slides.pdf`, đánh số theo góc trên-trái của slide (ví dụ "1.1", "2.2"...). Số giây ghi trong ngoặc là ước lượng thời gian nói cho slide đó — tổng phần chính ~730 giây (~12 phút 10 giây), có chút đệm cho việc chuyển slide và hít thở. Chữ *in nghiêng* là hướng dẫn cho bạn (không đọc), phần còn lại là lời nói nguyên văn, đọc tự nhiên chứ không học thuộc cứng.

---

## Mở đầu (trước khi bật slide 1, ~15s)

Kính thưa các thầy, các cô trong hội đồng, em xin phép được trình bày đồ án tốt nghiệp với đề tài **"Mô phỏng đầu-cuối hệ giao thoa kế vô tuyến UHF bốn phần tử phục vụ quan trắc bức xạ vô tuyến Mặt Trời tại tần số 610 MHz"**. Em là Nguyễn Bá Quân, mã số sinh viên 20224350, thực hiện dưới sự hướng dẫn của thầy Phó Giáo sư, Tiến sĩ Hà Duyên Trung. Sau đây em xin trình bày nội dung đồ án.

## Slide "Outline" (~10s)

Bài trình bày của em gồm bảy phần: động lực nghiên cứu, phương pháp mô phỏng, phần cứng anten và thiết lập đầu vào, kiểm chứng mô phỏng, kết quả tối ưu bố trí anten, chẩn đoán nguyên nhân thất bại thực địa, và cuối cùng là kết luận, hướng phát triển.

---

## 1.1 — Motivation: Why Monitor Solar Radio Bursts (~50s)

Trước hết là động lực nghiên cứu. Các vụ bùng phát Mặt Trời (solar flare) và phun trào vành nhật hoa tạo ra các đợt bùng phát bức xạ vô tuyến — gọi là solar radio burst. Các đợt bùng phát này làm thay đổi mật độ electron của tầng điện ly, từ đó gây nhiễu loạn cho các thiết bị điện tử phụ thuộc vào tín hiệu vệ tinh. Một ví dụ cụ thể: năm 2022, một cơn bão địa từ đã khiến SpaceX mất 38 trên tổng số 49 vệ tinh Starlink vừa phóng. Vì vậy, quan trắc vô tuyến từ mặt đất có thể cho chúng ta khoảng một đến ba ngày cảnh báo sớm trước khi các hiệu ứng này ảnh hưởng đến tầng điện ly. Cũng cần nói thêm, các đợt bùng phát loại II và loại III có thể làm flux tăng tới mười mũ bốn đến mười mũ năm lần so với nền Mặt Trời tĩnh — em có bảng phân loại chi tiết các loại burst trong phần backup nếu thầy cô quan tâm.

## 1.2 — Big Dish vs. Aperture Synthesis (~55s)

Vậy quan trắc bằng cách nào? Có hai hướng tiếp cận. Bên trái là kính thiên văn chảo đơn, ví dụ FAST của Trung Quốc, đường kính 500 mét — độ phân giải tỉ lệ thuận với đường kính chảo, nhưng đây gần như là giới hạn vật lý, không thể xây to hơn, và chi phí lên tới hàng trăm triệu đô. Bên phải là hướng tiếp cận giao thoa kế tổng hợp khẩu độ, như trạm DLITE ở Mỹ — độ phân giải lúc này không phụ thuộc kích thước từng anten, mà phụ thuộc **baseline** dài nhất, tức khoảng cách lớn nhất giữa hai anten bất kỳ. Chi phí chỉ khoảng vài nghìn đô mỗi anten, và có thể mở rộng bằng cách di chuyển hoặc thêm anten. Nhưng đổi lại — như bảng bên dưới thể hiện — cái giá phải trả là toàn bộ độ phức tạp chuyển từ kết cấu cơ khí sang xử lý tín hiệu: phải kết hợp tín hiệu từ nhiều anten một cách đồng pha. Đây chính xác là bài toán mà đồ án của em mô phỏng và kiểm chứng.

## 1.3 — Objectives (~50s)

Trước khi đi vào phương pháp, em xin nêu bối cảnh trực tiếp dẫn đến đồ án này. Trong một đợt triển khai thực địa trước đây tại Xuân Mai, với 2 anten Yagi-Uda cách nhau 8 mét, kết quả thu được chỉ là một xu hướng ngày–đêm mơ hồ, không quan sát được vân giao thoa rõ ràng, và không thể chẩn đoán được lỗi nằm ở đâu trong hệ thống phần cứng chỉ bằng cách quan sát trực tiếp. Đồ án này xây dựng và kiểm chứng một mô phỏng đầu-cuối, sau đó dùng chính mô phỏng đó để **chẩn đoán chính xác nguyên nhân** của thất bại đó — có số liệu định lượng và hướng khắc phục phần cứng cụ thể, em sẽ trình bày ở phần kết quả. Từ bối cảnh đó, đồ án đặt ra hai mục tiêu: một là xây dựng một mô phỏng vật lý đáng tin cậy, đi từ tín hiệu qua bộ tương quan đến ảnh, được kiểm chứng bằng lý thuyết cổ điển và phần cứng thực; hai là dùng mô phỏng đó để tối ưu cách bố trí anten trong không gian, tìm cách sắp xếp cho độ phân giải hai chiều tốt nhất mà không cần mua thêm phần cứng.

---

## 2.1 — Simulation Pipeline: From Flux to Image (~55s)

Đây là toàn bộ pipeline mô phỏng, gồm ba khối. Khối một, sinh tín hiệu: flux Mặt Trời thực đo tại 610 MHz kết hợp với mẫu bức xạ anten mô phỏng bằng 4NEC2, qua công thức Friis, cộng thêm nhiễu nhiệt Johnson–Nyquist, cho ra điện áp ở từng anten. Khối hai, tương quan: nhân chéo và lấy trung bình theo thời gian giữa từng cặp anten, cho ra visibility. Khối ba, tạo ảnh: dùng hình học tọa độ (u,v,w) và biến đổi Fourier ngược để tạo ảnh dirty image cùng hàm PSF. Toàn bộ chuỗi ba khối này được chạy lại cho mọi cấu hình anten khác nhau — việc so sánh kết quả đầu ra giữa các cấu hình chính là nửa sau của đồ án.

## 2.2 — What Is a Visibility? (~70s)

Slide này giải thích visibility là gì — khái niệm cốt lõi của giao thoa kế. Giả sử có hai anten cách nhau một khoảng baseline b. Sóng phẳng từ nguồn tới với góc θ so với thiên đỉnh sẽ tới anten 2 sớm hơn anten 1 một khoảng thời gian trễ hình học τ, bằng b nhân sin θ chia cho vận tốc ánh sáng. Bộ tương quan nhân hai điện áp V1, V2 rồi lấy trung bình theo thời gian, cho ra **một số phức duy nhất** — đó chính là visibility, tương ứng với một vân giao thoa trên bầu trời. Khi Trái Đất quay, góc θ thay đổi theo thời gian trong ngày, khiến đầu ra bộ tương quan dao động — đó là **fringe**, vân giao thoa có thể đo được. Và về mặt toán học, mỗi baseline tương ứng với một tần số không gian; nhiều baseline khác nhau cho nhiều thành phần Fourier khác nhau, kết hợp lại tái tạo được ảnh bầu trời — đây chính là định lý van Cittert–Zernike.

---

## 3.1 — Antenna: A Validated Model (~50s)

Chuyển sang phần cứng. Anten sử dụng là Yagi-Uda thương mại HKD G11KD-T2, được mô hình hóa từng đoạn dây trong 4NEC2. Bảng bên trái là các thông số mô phỏng chính: trở kháng vào, gain, độ rộng búp sóng nửa công suất, và SWR. Bảng bên phải là điểm quan trọng: em đối chiếu kết quả mô phỏng 4NEC2 với **đo đạc thực tế bằng NanoVNA** — SWR đo được 1.59 so với mô phỏng 1.55, độ lệch rất nhỏ. Điều này chứng minh mẫu anten mô phỏng đủ tin cậy để dẫn dắt toàn bộ pipeline tạo ảnh phía sau. Ngoài ra, em cũng khảo sát mutual coupling giữa các anten — coupling giảm xuống dưới −78 dB ở khoảng cách 5 mét, −87 dB ở 10 mét, nghĩa là ở mọi baseline vận hành trong đồ án này (từ 8 mét trở lên), các anten hoạt động **độc lập** với nhau, đúng như giả định nền tảng của lý thuyết tổng hợp khẩu độ.

## 3.2 — Real Input Data (~35s)

Dữ liệu đầu vào cho toàn bộ mô phỏng là flux 610 MHz thực, đã hiệu chuẩn, lấy từ đài quan trắc SWS Learmonth ở Úc, ngày 20 tháng 3 năm 2025 — đây không phải dữ liệu tự sinh, mà là dữ liệu đo thật. Các tham số chính: tần số 610 MHz, băng thông 1 MHz, nhiệt độ hệ thống lý tưởng 150 K, vị trí trạm tại vĩ độ −22.2 độ, và baseline được quét từ 8 mét đến 130 mét, sử dụng cùng một bộ 4 anten.

---

## 4.1 — Visibility Validation: Fringe & Jinc Curve (~55s)

Đây là phần kiểm chứng — rất quan trọng để chứng minh mô phỏng đáng tin cậy. Bên trái: trên baseline 8 mét, tức cặp anten liền kề của Case 1, đầu ra bộ tương quan dao động với chu kỳ khoảng 14 phút, khớp chính xác với dự đoán giải tích cho baseline và thời điểm đó. Bên phải: biên độ visibility giảm dần theo chiều dài baseline, rơi đúng lên đường cong jinc giải tích cho một đĩa Mặt Trời đồng nhất, với điểm null đầu tiên tại khoảng 130 lần bước sóng. Hai kiểm chứng độc lập này, cùng thỏa mãn trên dữ liệu Mặt Trời thực, chứng minh bộ tương quan đã cài đặt đúng định lý van Cittert–Zernike.

## 4.2 — Imaging Validation: Dirty Image = Sky * PSF (~45s)

Kiểm chứng thứ ba, ở miền tạo ảnh: (a) là ảnh bầu trời thật — một đĩa tròn mô phỏng Mặt Trời; nhân chập với (b) là PSF, hàm trải điểm tổng hợp; kết quả phải bằng (c), là dirty image tính trực tiếp từ dữ liệu qua gridding và FFT. Hai cách tính độc lập này — (b) nhân chập và (c) tính trực tiếp — khớp nhau đến **độ chính xác máy tính**. Điều này khẳng định bộ tương quan, việc lấy mẫu (u,v), và biến đổi Fourier ngược đều tự nhất quán với nhau, đúng cho bất kỳ cấu hình anten hai chiều nào.

---

## 5.1 — Why Array Layout Matters (~45s)

Sau khi mô phỏng đã được kiểm chứng, em dùng nó để trả lời câu hỏi thứ hai: bố trí anten thế nào là tốt nhất. So sánh hai cấu hình: cấu hình compact theo hướng Đông–Tây chỉ cho vùng phủ (u,v) một chiều, khiến PSF bị kéo dài thành một dải — ảnh bị nhòe theo hướng Bắc–Nam. Ngược lại, cấu hình graded cross trải theo cả hai hướng lấp đầy mặt phẳng (u,v) hai chiều, khiến sidelobe của PSF giảm khoảng 20 dB so với cấu hình compact. Điểm mấu chốt: chính việc phủ (u,v) hai chiều mới là thứ loại bỏ sidelobe — và nghiên cứu bố trí ở slide sau sẽ cô lập đúng hiệu ứng này, giữ cố định ngân sách 4 anten.

## 5.2 — Array Geometry Comparison (~60s)

Đây là bảng kết quả quan trọng nhất của đồ án. Em giữ nguyên 4 anten, chỉ thay đổi cách bố trí. Case 1, xếp thành đường thẳng Đông–Tây 24 mét: độ phân giải theo hướng Bắc–Nam chỉ đạt 180 phút góc — gần như không phân giải được gì theo hướng đó. Case 1.5, thêm một nhánh Bắc–Nam tạo hình chữ thập: cải thiện xuống 62.1 phút góc, tốt hơn 2.9 lần. Case 1.75, bố trí hình tam giác cộng tâm lấy cảm hứng từ DLITE, sao cho cả 6 baseline chỉ ra 6 hướng khác nhau: độ phân giải đạt 19.8 phút góc — tốt hơn **9.1 lần** so với case 1. Điểm mấu chốt em muốn nhấn mạnh: trong suốt cả ba trường hợp, phần cứng không đổi — chỉ thay đổi cách sắp xếp đã cải thiện độ phân giải hơn 9 lần.

*(Ghi chú: nếu hội đồng hỏi về mảng mở rộng 130 mét từng nhắc tới — đó là một thiết kế 17 anten riêng biệt, khác hẳn phần cứng 4 anten ở trên, xem slide backup 8.9.)*

## 5.3 — Sensitivity and Burst Detectability (~35s)

Về độ nhạy: flux tối thiểu có thể phát hiện được dao động khoảng 0.026 đến 0.183 đơn vị flux Mặt Trời, tùy số lượng mẫu tích lũy được lấy trung bình. Tỷ số tín hiệu trên nhiễu khi quan trắc Mặt Trời tĩnh luôn lớn hơn 500 trên 1 ở mọi cấu hình. Và quan trọng nhất cho mục tiêu khoa học: các đợt bùng phát loại II, loại III vượt ngưỡng nhiễu nền tới mười mũ bốn đến mười mũ năm lần — nghĩa là hệ thống hoàn toàn đủ khả năng phát hiện các sự kiện bùng phát thực tế.

---

## 6.1 — Closing the Loop: Diagnosing the Field Trial (~55s)

Bây giờ quay lại câu hỏi mở đầu: vì sao thực nghiệm tại Xuân Mai thất bại? Bằng cách so sánh mô phỏng với dữ liệu đo thực tế bằng 2 anten cùng ngày 20 tháng 3 năm 2025, em xác định được **hai nguyên nhân cụ thể, đo lường được**. Thứ nhất, chuỗi thu chưa được hiệu chuẩn: excess tín hiệu Mặt Trời đo được thấp hơn 23.8 lần so với dự đoán mô phỏng, tương ứng với nhiệt độ hệ thống hiệu dụng khoảng 3600 K, thay vì 150 K lý tưởng — nghĩa là chuỗi LNA chưa từng được hiệu chuẩn ngoài thực địa. Thứ hai, đồng hồ không đồng pha: một tinh thể thạch anh RTL-SDR thông thường trôi khoảng 1 phần triệu, dẫn đến thời gian kết hợp pha chỉ khoảng 1.6 mili giây ở tần số 610 MHz — ngắn hơn thời gian tích lũy 43.2 giây tới bốn bậc độ lớn — khiến biên độ vân giao thoa suy giảm về 0 bất kể tỷ số tín hiệu trên nhiễu tốt đến đâu. Kết luận quan trọng: thất bại thực địa **không phải do sai concept**, mà quy về hai yêu cầu phần cứng cụ thể và hoàn toàn khắc phục được — hiệu chuẩn nhiệt độ hệ thống, và bổ sung đồng hồ tham chiếu GPS hoặc dùng chung nguồn 10 MHz.

## 7.1 — Conclusion & Future Work (~45s)

Tổng kết lại, hai mục tiêu ban đầu đã đạt được. Một, mô phỏng vật lý đáng tin cậy: mô hình anten được đối chiếu trực tiếp với đo đạc NanoVNA, mutual coupling xác nhận các anten hoạt động độc lập, và visibility, fringe, ảnh tạo ra đều khớp lý thuyết giải tích trên dữ liệu Mặt Trời thực. Hai, tối ưu bố trí anten: với cùng 4 anten, việc sắp xếp lại từ đường thẳng sang hình tam giác kiểu DLITE cho độ phân giải Bắc–Nam tốt hơn 9.1 lần. Hướng phát triển tiếp theo: xây bộ tương quan phần cứng trên FPGA và kiểm chứng vân giao thoa hardware-in-the-loop; nâng cấp thực địa tại Xuân Mai theo cấu hình tam giác cộng tâm, kèm chuỗi LNA đã hiệu chuẩn và đồng hồ GPS; và thu dữ liệu bùng phát loại II, III thực tế, kết hợp giải chập CLEAN, tiến tới vận hành thời gian thực.

**Em xin cảm ơn quý thầy cô đã lắng nghe. Em xin sẵn sàng trả lời các câu hỏi của hội đồng.**

---
---

# PHẦN BACKUP — chỉ trình bày khi được hỏi

*Các slide dưới đây không tính vào 12 phút. Khi thầy cô hỏi, hãy bật đúng slide backup tương ứng rồi dùng đoạn script ngắn bên dưới làm khung trả lời — nói tự nhiên theo câu hỏi cụ thể, không cần đọc nguyên văn.*

## 8.1 — Backup: Key Contributions

*Dùng khi được hỏi "đóng góp chính của đồ án là gì".*

Đồ án có năm đóng góp chính. Một, mô hình anten được kiểm chứng bằng đo đạc NanoVNA trực tiếp, cùng nghiên cứu mutual coupling chứng minh các phần tử hoạt động độc lập ở mọi baseline vận hành. Hai, một engine mô phỏng giao thoa kế tổng quát, dùng chung một công thức (u,v,w) nhất quán cho pha từng anten, hình chiếu baseline, và fringe stopping — áp dụng được cho bất kỳ cấu hình mảng hai chiều nào. Ba, kiểm chứng bằng dữ liệu thực: pipeline chạy trên flux Learmonth thật, tái tạo đồng thời ba chữ ký kinh điển của tổng hợp khẩu độ. Bốn, so sánh có cấu trúc với công cụ giáo dục APSYNSIM, với bốn điểm vượt trội: dữ liệu thực, búp sóng anten thực, nhiễu dựa trên vật lý, và đường hướng tới phần cứng FPGA. Năm, một quy trình làm việc tái lập được trong một notebook duy nhất, từ file flux thô tới ảnh đã hiệu chuẩn trong dưới hai phút tính toán.

## 8.2 — Backup: Solar Radio Bursts, Types I–V

*Dùng khi được hỏi phân biệt các loại burst.*

Bùng phát vô tuyến Mặt Trời được phân thành 5 loại theo đặc tính phổ động. Loại I là các cơn bão nhiễu băng hẹp, kéo dài. Loại II trôi tần chậm, đánh dấu mặt sốc của CME lan truyền qua vành nhật hoa. Loại III trôi tần rất nhanh, do chùm electron trên đường sức từ mở, chiếm ưu thế ở bước sóng decimet — đây là dải tần liên quan trực tiếp đến đồ án của em. Loại IV là continuum băng rộng theo sau flare. Loại V là continuum ngắn đôi khi theo sau loại III, đánh dấu dòng electron bị giữ lại. Trong bảng tham số mô phỏng, em đã đưa vào cả loại II, III, IV và trường hợp Mặt Trời tĩnh.

## 8.3 — Backup: The Idea of Interferometry, Step by Step

*Dùng khi cần giải thích trực quan cơ chế giao thoa kế cho người ngoài chuyên ngành.*

Đây là minh họa từng bước ý tưởng giao thoa kế. Với hai anten và nguồn ở ngay chính giữa, không có độ trễ thời gian. Khi nguồn lệch sang một bên, xuất hiện một độ trễ nhỏ giữa hai anten. Một nguồn thực không phải một điểm, nên cần nhiều anten hơn. Với chỉ ba anten, ảnh tái tạo chỉ là các vân thô. Với 30 anten, hình dạng nguồn mới hiện rõ. Ý chính: mỗi cặp anten đo được một độ trễ thời gian, tương ứng một mảnh thông tin của bức tranh — càng nhiều anten, càng nhiều cặp, ảnh càng sắc nét.

## 8.4 — Backup: 3-D Radiation Pattern & E-plane

*Dùng khi được hỏi sâu về búp sóng bức xạ của anten.*

Đây là mẫu bức xạ mô phỏng đầy đủ từ 4NEC2. Bên trái là mặt cắt E-plane theo phương thẳng đứng, bên phải là mẫu bức xạ 3 chiều đầy đủ tại 610 MHz. Anten có gain hướng mạnh về phía chân trời, phù hợp với việc Mặt Trời di chuyển ở góc ngẩng thấp tại vĩ độ của trạm Learmonth trong phần lớn thời gian quan trắc.

## 8.5 — Backup: Full Input & Voltage Synthesis

*Dùng khi được hỏi chi tiết bước biến đổi từ flux sang điện áp.*

Đây là toàn bộ chuỗi biến đổi tín hiệu đầu vào. Đồ thị trên là flux 610 MHz thực, đã hiệu chuẩn, lấy trực tiếp từ SWS Learmonth — đầu vào thô, không bị mô phỏng lại. Đồ thị dưới là chính tín hiệu đó sau khi qua công thức Friis, nhân với búp sóng chính của anten mô phỏng bằng 4NEC2, và cộng thêm nhiễu — cho ra điện áp phức băng gốc ở từng anten, sẵn sàng đưa vào bộ tương quan.

## 8.6 — Backup: Array Geometry, Site & Observing Setup

*Dùng khi được hỏi về hình học vị trí trạm quan trắc.*

Trạm quan trắc Learmonth có vĩ độ −22.2 độ; Mặt Trời đi qua trong khoảng góc giờ từ −90 đến +90 độ, tương ứng cửa sổ quan trắc 12 giờ. Vị trí từng anten theo hệ tọa độ Đông–Bắc–Thiên đỉnh được xoay lần lượt theo vĩ độ trạm, rồi theo góc giờ và độ xích vĩ hiện tại của Mặt Trời, để cho ra tọa độ (u,v,w) tính bằng bước sóng ở mọi thời điểm.

## 8.7 — Backup: Mutual Coupling Curve

*Dùng khi được hỏi sâu về ảnh hưởng coupling giữa các anten.*

Bên trái là coupling |S21| đo và mô phỏng theo khoảng cách baseline: các điểm tròn là mô phỏng trong dải đo được từ 0.5 đến 3 mét, các điểm chữ thập đỏ là mô phỏng trực tiếp tại 5, 10, 15 mét. Coupling giảm xuống dưới −78 dB ở 5 mét, −87 dB ở 10 mét. Bên phải là hệ quả thực tế: mức méo trở kháng mà coupling gây ra trên mỗi phần tử đang hoạt động — đã nhỏ hơn 0.02% ngay từ khoảng cách 5 mét. Cả hai góc nhìn đều thống nhất: ở các baseline vận hành của đồ án, từ 8 mét trở lên, các anten hoạt động độc lập, không cần hiệu chỉnh ma trận Jones cho xuyên nhiễu.

## 8.8 — Backup: Position Matrix — Computing (u,v,w)

*Dùng khi được hỏi cụ thể "tọa độ (u,v,w) tính như thế nào", đây là câu hỏi toán nhiều khả năng gặp nhất.*

Việc tính (u,v,w) gồm hai bước xoay hệ tọa độ liên tiếp. Bước một, từ hệ tọa độ cục bộ Đông–Bắc–Thiên đỉnh sang hệ xích đạo X, Y, Z, bằng cách xoay theo vĩ độ trạm φ — ma trận này cố định, không đổi theo thời gian. Bước hai, từ hệ xích đạo sang hệ baseline u, v, w, bằng cách xoay theo góc giờ H và độ xích vĩ δ của nguồn — ma trận này thay đổi theo thời gian vì Mặt Trời di chuyển trên bầu trời. Hai ma trận này được dùng lại ở khắp nơi trong mô phỏng: cho pha từng anten ở khối sinh tín hiệu, và cho tọa độ baseline của mọi cặp anten ở khối tạo ảnh. Khi góc giờ H thay đổi trong ngày, mỗi baseline vạch nên một cung trên mặt phẳng (u,v) — đây chính là cơ chế tổng hợp nhờ chuyển động quay của Trái Đất, hay Earth-rotation synthesis.

## 8.9 — Backup: Beyond 4 Antennas (Case 2)

*Dùng khi được hỏi về mảng 130 mét/Case 2, hoặc nếu hội đồng thắc mắc "Case 2 có phải cùng 4 anten không" — câu trả lời trung thực là KHÔNG.*

Khác với Case 1/1.5/1.75, đây không phải cùng phần cứng 4 anten — đây là một thiết kế riêng, mảng chữ thập 2 chiều 17 phần tử: 1 anten tâm cộng 4 nhánh, mỗi nhánh 4 anten ở bán kính 5, 15, 35, 65 mét. Case này dùng mô hình thuận lý tưởng hóa — đĩa Mặt Trời đều, không nhiễu — chứ không dùng dữ liệu sfu thật. Với baseline dài tới 130 mét, tương đương khoảng 264 lần bước sóng ở 610 MHz — vượt qua điểm null visibility khoảng 132 lần bước sóng đã nói ở phần kiểm chứng — độ phân giải Đông–Tây đạt khoảng 11 phút góc, bắt đầu phân giải được đĩa 32 phút góc. Đây là một câu hỏi thiết kế riêng biệt: nếu sau này có thêm anten, một mảng 2 chiều graded như thế này là hướng để bắt đầu phân giải được hình dạng đĩa Mặt Trời, chứ không chỉ phát hiện nó.

## 8.10 — Backup: Full Array Sweep (5 Layouts)

*Dùng khi được hỏi về việc khảo sát nhiều cấu hình mảng hơn 3 case chính.*

Đây là khảo sát đầy đủ 5 cấu hình mảng: compact Đông–Tây, tuyến tính, hình chữ T, graded cross mở rộng hai chiều, và ngẫu nhiên. Hàng trên là dirty image, hàng giữa là PSF, hàng dưới là vùng phủ (u,v). Có thể thấy rõ: cấu hình càng phủ (u,v) đều theo mọi hướng, PSF càng gọn và sidelobe càng thấp. Lưu ý: các cấu hình linear/tee/extended/random trong hình quét này có số anten khác nhau, không phải cùng 4 anten của bảng kết quả chính.

## 8.11 — Backup: Sensitivity Detail

*Dùng khi được hỏi sâu về ngân sách nhiễu và khả năng xuất dữ liệu sang phần cứng FPGA.*

Vài chi tiết thêm về độ nhạy. SNR khi quan trắc Mặt Trời tĩnh lớn hơn 500 trên 1 ở mọi cấu hình, có thể lên tới khoảng 1700 trên 1 khi lấy trung bình 50 lần tích lũy. Xét trên từng mẫu đơn lẻ, SNR chỉ khoảng −3.8 dB — tín hiệu thực sự chìm trong nhiễu ở từng mẫu — nhưng sau khi lấy trung bình trong một lần tích lũy, SNR phục hồi lên khoảng 13 trên 1, đúng như hành vi kỳ vọng của một kính thiên văn vô tuyến thực. Về phần cứng: mức nhiễu nền chiếm hơn 20 bit LSB trên một mẫu 16-bit, nghĩa là tín hiệu đã sẵn sàng để xuất sang một bộ tương quan phần cứng trên FPGA mà không lo tràn hay thiếu độ phân giải.
