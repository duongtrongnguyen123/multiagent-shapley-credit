# Bảng công việc — để phân công và ghi nhận đóng góp

Cập nhật 2026-08-21. Nguồn: lịch sử git (724 commit), `shapley/docs/` (39 tài liệu),
273 thư mục kết quả thí nghiệm, và `report/BAO_CAO.tex` (7 mục, 14 tiểu mục, 16 bảng, 4 hình,
24 trích dẫn).

---

## A. Khối nghiên cứu — ai chạy thí nghiệm gì

| # | Khối | Nội dung chính | Kết quả đáng kể | Người chạy | Ở đâu trong báo cáo |
|---|---|---|---|---|---|
| A1 | **Shapley theo vai trò** | Đủ $2^4=16$ tổ hợp bật/tắt 4 vai, GSM8K + MATH; nâng riêng từng vai lên 7B | $\varphi_P = -0{,}014$ (âm ở 1.5B) lật thành $+0{,}055$ ở 7B; $\varphi_V$ $+0{,}269 \to +0{,}462$; chỉ số tương tác cho thấy S/V/A thay thế nhau | Quân | §5.3 |
| A2 | **Chuyên biệt hoá vai trò** | Lưới hành vi 2×2 (task × năng lực) đọc từ trace; hoán vị prompt; bỏ lệnh cấm tính | Planner rò đáp án 34,7%; solver không sinh số mới 62%; aggregator chỉ 3/2000 lượt ra đáp án mới-và-đúng | Quân | §5.4 |
| A3 | **Verifier không thật sự kiểm** | Fix/Break, Intervention Accuracy, tiêm lỗi chữ số, lưới `V_gain` | IA chỉ 56–59% ở 1.5B (98% ở 7B); 1.5B mù với lỗi tiêm; dải có lợi 0,60–0,67 | Quân | §5.4 |
| A4 | **Mức dao động nền** | Chạy cùng cấu hình trên 5 fold để hiệu chuẩn | `V_gain` dao động $+1{,}0$…$+8{,}0$; std 2,65 → ngưỡng hiệu dụng ~3,3 điểm | Quân | §4, §5.1 |
| A5 | **Kiểm soát ngân sách** | Cùng 8 lần sinh, đổi bộ tổng hợp; đối chứng `rerun = loop` | `llm_agg` kém `maj@8` 19–26 điểm; `rerun = loop` (0,453 = 0,453) → giá trị ở lần sinh, không ở phản hồi | Nguyên | §5.2 |
| A6 | **Kiểm soát mốc + đơn giá token** | So với model mạnh đơn lẻ; quy chi phí về FLOP | Bất đối xứng kém S7B 10 điểm/GSM8K; "rẻ hơn 12%" biến mất khi quy FLOP; $+7{,}7$ ở chênh $=0$ | Nguyên | §5.5 |
| A7 | **Kiểm soát mẫu số** | Phân tầng theo số lần đúng trong 5 lần sinh | 57% số câu bất động theo cấu trúc (70% với bỏ phiếu); pha loãng 2,3–3,3 lần | Nguyên | §5.6 |
| A8 | **Số hạng $G$ + quy luật chênh** | 6 model, 15 cặp có hướng, MBPP; hồi quy $G$ và $\Delta_{ceil}$ | $\beta_1 = -0{,}19$ ($p\approx 0$); "khác họ" là tương quan giả; $g^\ast \approx 0{,}09$ | Nguyên | §5.7 |
| A9 | **Chuyển miền** | Dùng đường khớp MBPP dự báo MATH, 3 cặp | 2/3 trong khoảng; cặp 1.5B→7B lệch hệ thống ($L \approx 11G$) | Nguyên | §5.8 |
| A10 | **Tác động artifact** ⭐ | Thiết kế chốt trước, 2 nhánh cùng lệnh giải, phân tầng theo nội dung artifact | $-27{,}2$ điểm trên tầng artifact sai ($p\approx 0$); $+3{,}8$ trên artifact đúng; bảng $2\times2$ cho thấy giao thức sửa là **ống dẫn** | Nguyên | §5.9 |
| A11 | **$\kappa$ và định tuyến** | `exec3` vs `llm3` trên HumanEval; bộ phân loại lỗi tiêm; hai trần cổng | `exec3` phá 0 bài 20/20 fold; AUC 0,893 chỉ đổi $+2{,}4$ điểm; consensus router vô dụng trên MATH | Nguyên + Tùng Dương | §5.10 |
| A12 | **Huấn luyện vai trò** | GRPO ×3, ORPO, credit-RL 2 giai đoạn, MAPoRL | 7/7 thất bại, mỗi cái một lối tắt; **H60 đo đồng thời $+17{,}0$ và $-10{,}4$ trên cùng lần chạy** | Quân | §5.11 |

⭐ = thí nghiệm chính của khảo sát.

**Chưa xong:** $\Delta_{real}$ còn thiếu **một nhánh** (`R:R2`) — 8/9 nhánh đã sinh xong, kernel
đã vá OOM sẵn (`bs=4`), chạy được trên Kaggle 2×T4, tài khoản `tuetrandoanminh` còn quota.

---

## B. Báo cáo — hiện trạng từng mục

| Mục | Nội dung | Người chấp bút | Người đã rà | Tình trạng |
|---|---|---|---|---|
| Bìa | Logo UET, 4 thành viên + MSV, INT3406 | Nguyên | — | Xong |
| Lời cảm ơn | Gửi thầy Trần Hồng Việt | Tùng Dương | — | Xong |
| Tóm tắt | 219 từ, không ký hiệu | Nguyên | — | Xong |
| §1 Mở đầu | Ví dụ cụ thể → Hình 1 → 3 vấn đề đo lường → 4 đóng góp | Đức | Nguyên (chuẩn hoá thuật ngữ) | Xong |
| §2 Công trình liên quan | 3 dòng nghiên cứu + vị trí khảo sát | Đức | Nguyên | Xong — Đức đã tra đủ nguồn |
| §3 Phương pháp đo lường | 3 câu hỏi khung, đẳng thức $G-L+R$, 2 lớp giao thức | Nguyên | — | Xong |
| §4 Thiết lập | Model, benchmark, vai trò, mốc, thống kê, nhãn tin cậy | Nguyên | **Tùng Dương chưa rà** | Cần rà |
| §5 Kết quả (11 tiểu mục) | Xem bảng A | Quân + Nguyên | Nguyên (chuẩn hoá + khôi phục số liệu) | Xong |
| §6 Tổng hợp | Hai mốc so sánh, cây quyết định | Tùng Dương | Nguyên | Xong |
| §7 Kết luận + Hạn chế | 6 mục hạn chế | Tùng Dương | Nguyên | Xong |
| Thư mục | 24 trích dẫn | Đức | — | Xong |
| Phụ lục | Link repo công khai | Nguyên | — | Xong |

**Hình:** Hình 1 tác động artifact (Đức vẽ lại) · Hình 2 pipeline + Shapley (tái dụng từ khối
Quân) · Hình 3 ví dụ GRPO (tái dụng) · Hình 4 hai mốc so sánh (Tùng Dương vẽ lại bằng TikZ).

**Slide thuyết trình:** `SLIDE_BAO_CAO.tex` — beamer 16:9, 18 slide, Tùng Dương dựng.
Lưu ý: slide dựng từ bản báo cáo **trước** vòng sửa số liệu, nên mỗi lần chốt lại một con số ở
mục C phải soát lại slide. Đã kiểm: các số C1–C5 chưa lọt vào slide; đã gom "phơi nhiễm" →
"tiếp xúc" cho khớp báo cáo.

---

## C. Việc còn lại — để phân công

Nguồn: một lượt review độc lập toàn bài (agent đọc hết 1132 dòng) + kiểm chứng tay từng mục.
Đã lọc bỏ các báo động sai. Nhóm C-số là **phải làm trước khi nộp**, nhóm C-tuỳ là nâng chất.

### C-số — đối chiếu lại số liệu (cần người đã chạy thí nghiệm)

| # | Vấn đề | Đã kiểm chứng | Ai làm được | Ước lượng |
|---|---|---|---|---|
| C1 | **$L \approx 11G$ không khớp bảng.** §5.8 ghi $L = 0{,}208$ nhưng 0,208 là **biên khoảng tin cậy** ở Bảng 14, còn ước lượng điểm là $-0{,}166$. Tỷ số "11 lần" trùng đúng tỷ số **đếm bài** 11:121 ở §5.9 — nhiều khả năng chép nhầm. Từ Bảng 15: $L = 77/500$, $G = 11/500$ → tỷ số $\approx 7$. Số này lặp ở **3 chỗ** (§5.8, §6, §7) như kết luận chủ lực. | Xác nhận là không khớp | Nguyên (chạy A8/A9) | 30 phút |
| C2 | **$\varphi_V$ không phải giá trị đo.** Bảng 4 ghi Verifier $= +0{,}252$ "đối xứng cấu trúc với Solver". Vì áp đặt nên tổng $\varphi$ không thoả tiên đề hiệu quả (GSM8K: tổng $0{,}680$ vs `PSVA` $0{,}744$). Mà kết luận "verifier là vai trò nhạy cảm nhất với năng lực" lại dựa trên chính giá trị áp đặt này. | Xác nhận | Quân (chạy A1) | 45 phút |
| C3 | **Văn xuôi §5.3 lệch Bảng 4:** ghi $\varphi_P = -0{,}023$ và $\varphi_V = +0{,}269$, bảng ghi $-0{,}014$ và $+0{,}252$. | Xác nhận | Quân | 15 phút |
| C4 | **Độ chính xác solver xuất hiện nhiều giá trị:** GSM8K 7B là 0,916 / 0,910 / 0,884; MATH 1.5B là 0,50 / 0,405 / 0,402 / 0,413. Có thể đều đúng (khác bộ bài) nhưng bài không nói. | Cần xác minh | Quân | 30 phút |
| C5 | **Ba số mồ côi:** khoảng cách `oracle@k − maj@k` $= +21{,}3$ điểm trên code; hai số `maj` $-11{,}3$/$-13{,}1$; "21/43 giả thuyết" — không bảng nào chứa. | Cần xác minh | Nguyên | 30 phút |
| C6 | **Xung đột ký hiệu $I$:** §5.3 dùng $I$ cho *chỉ số tương tác Shapley*, đè lên $I$ = *model mạnh độc lập* ở Bảng 1 và §3.2. Đổi sang $\mathcal{I}$ hoặc $\varphi_{ij}$. | Xác nhận | Ai cũng được | 10 phút |
| C7 | **Bảng 15 có hai hàng "HE 1.5B" và hai hàng "HE 7B" trùng nhãn** — caption nói "hai hệ phần cứng" nhưng không phân biệt được hàng nào. | Xác nhận | Nguyên | 15 phút |
| C8 | **Định nghĩa 2 cột bảng phân loại** — "Tách biệt trên lỗi tiêm / lỗi thật" là đại lượng gì, đơn vị nào. | — | Người chạy H37 | 15 phút |
| C9 | **Rà §4** — mục duy nhất chưa ai đọc lại. | — | Tùng Dương | 1 giờ |
| C10 | **Mục Đóng góp thành viên** (bắt buộc với báo cáo nhóm). | — | Cả nhóm | 20 phút |
| C11 | Soát cuối: biên dịch, chính tả, xoá khối comment lịch sử sửa bài ở đầu file. | — | Nguyên | 30 phút |

### C-tuỳ — thí nghiệm bổ sung (bỏ qua được)

| # | Việc | Ước lượng | Vì sao đáng làm |
|---|---|---|---|
| C12 | Chạy nốt nhánh `R:R2` để khép $\Delta_{real}$ | ~40 phút GPU | Biến hạn chế #1 thành kết quả |
| C13 | Đối chứng thêm lượt 7B không kèm artifact (300 bài MATH) | ~30 phút GPU | Tách "lợi ích lượt sinh" khỏi "lợi ích kiểm" |
| C14 | Đối chứng khác-model-cùng-họ | ~30 phút GPU | §5.7 tự khai đang thiếu |

### Đã sửa xong trong vòng này (không cần phân công)

Lỗi số học 48/68 → **48/74** (65%, không phải 71% — tầng 2/5 có 6 bài `maj@5` sai bị bỏ sót);
lặp từ "tiềm năng cải thiện cải thiện"; câu hỏng "llm3 phá hủy thì ở"; gom 6 "tiền đăng ký" →
"chốt trước", 5 "phơi nhiễm" → "tiếp xúc", "tác nhân" → "tác tử", "Hồi II" → "Mạch thứ hai".

### Review nói quá — đã kiểm, **không** cần sửa

"Mức dao động nền và kết quả chủ lực là cùng một bộ số" — đúng là cùng dữ liệu, nhưng không mâu
thuẫn: độ lệch giữa fold cho **mức nhiễu**, còn trung bình 5 fold cho **hiệu ứng**
($t = 4{,}4/(2{,}65/\sqrt5) = 3{,}7 > 2{,}776$). Chỉ nên thêm một câu nói rõ, không phải sửa số.

---

## D. Quy ước đang áp dụng (đừng đổi một mình)

- **Từ vựng:** `model` (không "mô hình"), `trace`, `task`, `pool`, `lần sinh` (không "lượt sinh"),
  `mức dao động nền` (không "sàn nhiễu"), `tiềm năng cải thiện` ($H$), `khả năng khai thác`
  ($\kappa$), `chốt trước` (không "tiền đăng ký"), `vai trò` (không "vai"), `thí nghiệm tác động
  artifact` (không "thí nghiệm tiếp xúc").
- **Ký hiệu:** $W/I/E$ (nhân vật) · $G/L/R$ (số hạng) · $P/S/V/A$ (vai trò) ·
  $\Delta_{ceil}$ / $\Delta_{real}$ / CEIL — chỉ số tiếng Anh, giải thích tiếng Việt.
- **Đơn vị:** accuracy thang 0–1; hiệu ứng bằng "điểm" (= điểm phần trăm); tỷ số chi phí kèm `×`.
- **Giọng:** trung tính. Không "đáng kể", "vượt trội", "ấn tượng", không câu hỏi tu từ.
- **Hình:** dùng `[!ht]`, **đừng đổi về `[t]`** — hình sẽ trôi lên đè Tóm tắt (đã tái phát 3 lần).
- **PDF:** không commit trên nhánh cá nhân; chỉ biên dịch lại khi gộp về `main`.
