# Phân công sửa báo cáo — làm việc trên nhánh riêng

Mỗi người sửa một phần của `BAO_CAO.tex` trên nhánh riêng của mình, rồi gộp về `main`.

| Người | Nhánh | Phần phụ trách trong `BAO_CAO.tex` |
|---|---|---|
| **Nguyên** | `nguyen-report` | **§3 Phương pháp đo lường**, **§4 Thiết lập thí nghiệm và quy trình** |
| Đức | `duc` | §2 Công trình liên quan (giải quyết các marker `\todoD`) |
| Tùng Dương | (chưa đặt) | §4 rà lại `\todoTD`; định nghĩa cột Bảng `tab:exec` và `tab:clf` |
| Quân | `quan` | §5.3 Shapley, §5.11 Huấn luyện; hai hình trong `figs/` |

## Quy tắc để tránh xung đột

1. **Chỉ sửa phần mình phụ trách.** Thấy lỗi ở phần người khác thì ghi vào
   `CAU_HOI_THAO_LUAN.md` chứ đừng sửa trực tiếp.
2. **Không chạm vào preamble** (dòng 1–60: `\documentclass`, các `\usepackage`, `\newcommand`).
   Cần macro mới thì báo trong nhóm — đây là chỗ dễ xung đột nhất.
3. **Không sửa `BAO_CAO.pdf`.** File PDF là kết quả biên dịch, sửa cùng lúc là chắc chắn xung
   đột. Ai gộp về `main` thì biên dịch lại một lần ở đó.
4. **Kéo `main` về trước khi bắt đầu một phiên làm việc:**
   `git fetch origin && git merge origin/main`
5. **Biên dịch thử trước khi đẩy:** `tectonic BAO_CAO.tex` phải ra 0 lỗi.

## Ký hiệu và giọng văn đã thống nhất (đừng đổi một mình)

- Ba khái niệm khung: **Tiềm năng cải thiện ($H$) — Khả năng khai thác ($\kappa$) — Thiệt hại ($D$)**.
- Bộ ký hiệu thí nghiệm tiếp xúc: `W` / `I` / `E`; ba số hạng: `G` / `L` / `R`.
- Vai pipeline: `P` / `S` / `V` / `A` — **không** dùng chữ này cho nghĩa khác.
- Mọi ký hiệu phải có trong **Bảng 1 (tra nhanh)** và phụ lục thuật ngữ.
- Nguyên tắc trình bày: lời thường → ví dụ cụ thể → hình → rồi mới hình thức hoá.
- Đơn vị: accuracy thang 0–1; hiệu ứng viết bằng "điểm" (= điểm phần trăm); tỷ số chi phí kèm dấu `×`.

## Còn treo

- `\todoD` ×3 (§2: xác nhận trích dẫn, nguồn số tranh biện, MAS_RPSV/SHARP chưa có mục thư mục).
- `\todoTD` ×2 (§4 rà tổng thể; đơn vị cột "phá" ở Bảng `tab:exec`; định nghĩa hai cột Bảng `tab:clf`).
- Mục **Đóng góp thành viên** đã tạm bỏ, thêm lại khi hoàn chỉnh.
- Bài đang 19 trang; nếu cần ép về 12–15 thì ứng viên cắt là bảng hiệu chỉnh FLOP (gộp vào lời)
  và phần định tuyến ở §5.10.
