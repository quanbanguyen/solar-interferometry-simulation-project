# Đồ án tốt nghiệp — Mô phỏng giao thoa kế vô tuyến Mặt Trời 610 MHz

Tác giả: **Nguyễn Bá Quân** — MSSV **20224350** — quan.nb224350@sis.hust.edu.vn

## Cách biên dịch

Phải dùng **XeLaTeX** (vì có tiếng Việt + font Times New Roman qua `fontspec`).

**Cách 1 — latexmk (khuyên dùng):**
```
latexmk -xelatex main.tex
```

**Cách 2 — thủ công:**
```
xelatex main.tex
bibtex main          # (hoặc biber nếu bạn đổi sang biblatex)
xelatex main.tex
xelatex main.tex
```

**Trên Overleaf:** Menu → Compiler → chọn **XeLaTeX**. Upload cả thư mục.

> Mẹo: nếu máy bạn có sẵn `IEEEtran.bst`, đổi dòng `\bibliographystyle{unsrt}`
> trong `main.tex` thành `\bibliographystyle{IEEEtran}` để có định dạng IEEE chuẩn.

## Cấu trúc thư mục

```
main.tex                 ← file gốc: preamble, trang bìa, các \input
refs.bib                 ← tài liệu tham khảo
chapters/
  eval_forms.tex         ← 3 mẫu đánh giá ĐATN (HUST)
  abbreviations.tex      ← danh mục viết tắt
  intro.tex              ← MỞ ĐẦU (0.1–0.5)
  ch2_theory.tex         ← Chương 1: Cơ sở lý thuyết
  ch3_antenna.tex        ← Chương 2: Mô phỏng anten + mutual coupling
  ch4_pipeline.tex       ← Chương 3: Thiết kế pipeline mô phỏng
  ch5_results.tex        ← Chương 4: Kết quả & kiểm chứng
  conclusion.tex         ← KẾT LUẬN & HƯỚNG PHÁT TRIỂN
figures/                 ← 17 ảnh PLACEHOLDER (.png) — thay bằng ảnh thật của bạn
```

## Thay ảnh

Trong `figures/` đang là 17 ảnh placeholder. **Chỉ cần ghi đè bằng ảnh thật
CÙNG TÊN** (giữ đuôi `.png`, hoặc đổi sang `.pdf`/`.jpg` rồi sửa lại tên trong lệnh
`\includegraphics`). Danh sách:

| Tên file | Nội dung cần thay |
|---|---|
| `fig_solar_dynamic_spectrum` | Phổ động Mặt Trời (Type I–V) |
| `fig_antenna_geometry` | Hình học anten Yagi U-frame |
| `fig_pattern_eplane`, `fig_pattern_3d` | Giản đồ bức xạ E-plane / 3D |
| `fig_coupling_vs_distance` | Mutual coupling theo khoảng cách |
| `fig_pipeline_block` | Sơ đồ khối pipeline |
| `fig_sws_flux_day` | Flux SWS 610 MHz 28/04/2024 |
| `fig_uv_coverage` | uv-coverage |
| `fig_dirty_beam`, `fig_dirty_image` | Dirty beam / dirty image |
| `fig_fringe_pattern` | Vân giao thoa (baseline 15 m) |
| `fig_visibility_jinc` | Visibility theo baseline (jinc) |
| `fig_dirty_from_dft`, `fig_sky_conv_psf` | Kiểm chứng dirty = sky*PSF |
| `fig_layout_sweep` | Quét hình học mảng |
| `fig_before_clean`, `fig_after_clean` | Trước/sau CLEAN |

## Cần sửa trước khi nộp

Mở `main.tex`, phần "EDITABLE FIELDS":
- `\supervisor` / `\supervisorVN` → **điền tên GVHD**
- `\programme`, `\department`, `\school` → kiểm tra đúng ngành/bộ môn của bạn
- `\submitplacedate` → tháng/năm nộp
- Phần ACKNOWLEDGMENT trong `main.tex` → viết lại lời cảm ơn theo ý bạn

Các con số kỹ thuật (Zin = 108−j22 Ω, gain 9.48 dBi, SWR 1.55, coupling < −34 dB,
chu kỳ vân ~8 phút, δ = +14.4°, H = ±84.2°…) đã lấy theo đúng kết quả đồ án của bạn —
rà lại lần cuối cho khớp số liệu mới nhất.
