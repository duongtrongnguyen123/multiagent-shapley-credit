# Bảng kết quả tổng hợp

Tất cả số liệu dưới đây đo trên Qwen2.5-Instruct (1.5B fp16 / 7B nf4), giải mã greedy,
chạy trên GPU Kaggle T4. Mỗi giả thuyết đều được **đăng ký trước** trong
[`PREREGISTRATION.md`](PREREGISTRATION.md) và commit **trước khi** kernel chạy — lịch sử git
chứng minh thứ tự đó, nên không kết quả nào bị diễn giải lại sau khi đã nhìn thấy số.

---

## 1. Những gì CÓ TÁC DỤNG (đo được, dấu dương)

| Phương pháp | Thiết lập | Kết quả |
|---|---|---|
| **Solver 1.5B + Verifier 7B** (post-hoc, 1 lần) | MATH, n=50 | **.46 → .64** (+18đ), 9 sửa / **0 phá** |
| **loop** — Solver giải lại sau khi Verifier chê | MATH 1.5B, n=100 | **.40 → .60** (+20đ) |
| **Pipeline đầy đủ** so với Solver đơn độc | GSM8K 1.5B, n=250 | **.632 → .744** (+11.2đ) |
| **Self-consistency** maj@8 | MATH 1.5B, n=100 | **.50 → .60** (+10đ) |
| **Sửa lỗi bằng chạy test** (3 vòng) | HumanEval, n=164 | .531→.567 (1.5B); .787→**.835** (7B); **0 phá** cả 3 vòng |
| **Planner → Solver** | GSM8K / MATH 1.5B | .632→.684 / .405→.425 |
| **Verifier đọc lời giải** | MATH 7B, n=200 | **+6.5đ** (17 sửa / 4 phá) |

## 2. Phát hiện trung tâm: HIỆU ỨNG KHÔNG BỀN, ĐỔI DẤU THEO Ô

Cùng một lựa chọn kiến trúc, cùng mã nguồn, **đổi dấu** khi đổi task hoặc đổi cỡ model:

| Can thiệp | Ô A | Ô B | Biên độ đảo |
|---|---|---|---|
| **Truyền trace cho V và A** (H10, đã khử nhiễu) | GSM8K 1.5B: **+7.6đ** | MATH 1.5B: **−9.0đ** | 16.6đ |
| Che giá trị trung gian (H6) | GSM8K 1.5B: **+8.4đ** | MATH 1.5B: **−2.0đ** | 10.4đ |
| Verifier bịt mắt vs đọc lời giải (H1) | GSM8K 1.5B: **+2.0đ** | MATH 7B: **−6.0đ** | 8.0đ |
| Context KHÔNG liên quan (X_cross) | GSM8K/MATH 1.5B: **−3.6 / −3.5đ** | MATH 7B: **+5.5đ** | 9.1đ |
| Aggregator LLM vs bỏ phiếu (H2) | MATH 1.5B: **−6.7đ** | MATH 7B: **+1.7đ** | 8.4đ |

**Kết luận:** không được suy rộng một ô ra toàn cục. Một bài báo chỉ báo cáo một ô trong bảng
trên sẽ trông rất thuyết phục — và sai.

## 3. Phân bổ đóng góp đo ở mức ĐẦU-CUỐI (H11, GSM8K 1.5B, n=250)

| Cấu hình | acc | Chênh so với P→S |
|---|---|---|
| P→S | .684 | — |
| **P→S→V** (chỉ Verifier) | **.732** | **+4.8** |
| P→S→V→A (đủ) | .744 | +6.0 |
| **P→S→A** (chỉ Aggregator) | **.428** | **−25.6** |

**Verifier mang gần như toàn bộ giá trị**; Aggregator thêm được +1.2 khi đứng sau Verifier.
*Lưu ý trung thực:* nhánh P→S→A là **cấu hình thoái hoá** — một bộ tổng hợp chỉ nhận **một**
ứng viên thì không có gì để tổng hợp, nên nó đi giải lại và hỏng. Con số −25.6 phản ánh điều đó,
không phải "Aggregator vô dụng".

## 4. Giá trị của V và A phụ thuộc hoàn toàn vào context (H10, GSM8K 1.5B)

| Pipeline | acc |
|---|---|
| P→S→V→A, **toàn văn** | **.744** |
| P→S (bỏ hẳn V và A) | .684 |
| P→S→V→A, **chỉ đáp án** | **.668** |

Hai vai V và A **bị bỏ đói context thì tệ hơn là không có chúng** (−1.6), nhưng có context thì
đáng **+6.0**. Giá trị của một vai **không tách rời** khỏi thứ mà nó được nhận.

## 5. Ràng buộc theo năng lực model

| Quan sát | Số liệu |
|---|---|
| Solver gần bão hoà → verify vô nghĩa | GSM8K 7B, solver .916: **mọi** nhánh verify = 0 hoặc âm |
| Lợi ích bỏ phiếu giảm theo năng lực | maj@8: **+10đ** (1.5B) → **+1đ** (7B); đồng thuận mẫu 4.6/8 → 6.4/8 |
| loop giúp model yếu, không giúp model mạnh | MATH: +20đ (1.5B) → 0đ (7B) |

## 6. Kỷ luật phương pháp — những gì đã tự bác bỏ / tự rút lại

| # | Nội dung | Kết cục |
|---|---|---|
| 1 | Interleaving giảm "phá" | BỊ BÁC — là cấu hình tệ nhất |
| 2 | Math vốn khó verify | BỊ BÁC — do pipeline, không do task |
| 3 | H3 cổng lọc bằng verifier thận trọng | BỊ BÁC — cổng kêu 0/250 lần |
| 4 | H4 Planner gây hại | BỊ BÁC — bóp nghẹt trình bày nhưng acc TĂNG |
| 5 | H5 truyền kế hoạch cứu Verifier | BỊ BÁC ở cả 3 ô |
| 6 | H6 phép tính là thành phần hoạt tính | BỊ BÁC — thứ tự ngược hẳn |
| 7 | Che giá trị là kết quả triển khai được | **TỰ RÚT LẠI** — đảo dấu trên MATH |
| 8 | H7 che giá trị cứu Aggregator | BỊ BÁC — không tổng quát |
| 9 | H2 "aggregator kém 19 điểm" | **TỰ SỬA** — phần lớn là nhiễu prompt của chính tôi |
| 10 | H8 verify bằng thực thi trên math | **VÔ HIỆU** — exec_success_rate .42 < ngưỡng .50 đã khoá trước |
| 11 | H9 pipeline tối giản | BỊ BÁC + **TỰ THÚ LỖI THIẾT KẾ** (nhánh MIN bỏ nhầm 2 biến) |

Ngưỡng hiệu lực của H8 được khoá **trước** khi chạy: nếu model không viết nổi code chạy được thì
đó là **giới hạn năng lực**, không phải bằng chứng bác bỏ. Nhờ vậy tránh được kết luận sai
"verify bằng thực thi thất bại trên math" — số liệu không hề ủng hộ kết luận đó.
