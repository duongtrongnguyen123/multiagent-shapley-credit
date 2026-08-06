# Bảng kết quả tổng hợp

Tất cả số liệu dưới đây đo trên Qwen2.5-Instruct (1.5B fp16 / 7B nf4), giải mã greedy,
chạy trên GPU Kaggle T4. Mỗi giả thuyết đều được **đăng ký trước** trong
[`PREREGISTRATION.md`](PREREGISTRATION.md) và commit **trước khi** kernel chạy — lịch sử git
chứng minh thứ tự đó, nên không kết quả nào bị diễn giải lại sau khi đã nhìn thấy số.


---

## 0. SÀN NHIỄU — ĐỌC MỤC NÀY TRƯỚC MỌI CON SỐ BÊN DƯỚI

Cùng MỘT cấu hình, chạy trên **5 fold rời nhau** (GSM8K 1.5B, mỗi fold 100 bài):

| Đại lượng | mean | min | max | range | std |
|---|---|---|---|---|---|
| `V_gain` (Verifier) | +4.4 | **+1.0** | **+8.0** | **7.0** | 2.65 |
| `A_gain` (Aggregator) | +1.2 | **−1.0** | **+3.0** | **4.0** | 1.33 |

**Cùng một thí nghiệm chạy 5 lần cho giá trị Verifier từ +1.0 đến +8.0.**
Quy đổi sang n=250: std ≈ 1.7đ; hiệu của HAI phép đo có std ≈ 2.4đ → **ngưỡng 2σ ≈ 5 ĐIỂM**.

> ### QUY TẮC ĐỌC BẢNG
> **Mọi hiệu ứng < 5 điểm, đo MỘT LẦN ở n ≤ 250, KHÔNG phải bằng chứng.**
> Cụ thể: khoảng của `A_gain` chứa số 0 và có phần âm → khẳng định "Aggregator +1.2 trên GSM8K"
> **ĐÃ BỊ HẠ CẤP**. Các hiệu ứng nhỏ khác trong tài liệu này cần được đọc với cùng thái độ.
>
> **Các lần ĐẢO DẤU đều vượt ngưỡng** và vẫn đứng: truyền trace 16.6 · bỏ phiếu 13.1 ·
> che giá trị 10.4 · X_cross 9.1 · verifier bịt mắt 8.0 · vai Aggregator 7.2.

*Phép đo này lẽ ra phải chạy ĐẦU TIÊN. Chạy muộn nên nhiều vòng trước đã diễn giải các chênh
lệch 1–3 điểm vốn không có ý nghĩa thống kê.*

---

## 1. CÓ CẢI THIỆN THẬT KHÔNG? — PHÂN LOẠI THEO ĐỘ TIN CẬY

### 1a. ĐÃ XÁC NHẬN có thanh sai số (5 fold, TOÀN BỘ fold cùng dấu)

| Cải thiện | Thiết lập | Hiệu ứng | Khoảng | Fold cùng dấu |
|---|---|---|---|---|
| **Solver 1.5B + Verifier 7B** | **MATH**, n=300 | **+14.0đ** | **[+8.3, +20.0]** | **5/5** ✅ |
| ↳ *riêng phần do verifier MẠNH HƠN* (V7 − V15) | MATH, n=300 | **+11.0đ** | **[+3.3, +16.7]** | **5/5** ✅ |
| **Pipeline đa tác tử vs Solver đơn độc** | GSM8K 1.5B | +5.6đ | [+4, +8] | **5/5** ✅ |
| **Verifier** (P→S→V vs P→S) | GSM8K 1.5B | +4.4đ | [+1, +8] | **5/5** ✅ |

> ### KẾT QUẢ MẠNH NHẤT: BẤT ĐỐI XỨNG NĂNG LỰC
> **Solver nhỏ + Verifier LỚN HƠN = +14.0đ trên MATH, 43 SỬA / 1 PHÁ trên 300 bài.**
> Điều then chốt: verifier **cùng cỡ** chỉ cho +3.0đ với khoảng **chạm 0** (vô giá trị).
> Giá trị nằm ở **CHÊNH LỆCH NĂNG LỰC**, không ở việc có thêm một vai.
>
> Điều này giải câu đố MATH: mọi thí nghiệm verifier ĐỒNG CỠ trên MATH đều ra ~0
> (nf_m15: +1.4, khoảng [−1,+4]). Đổi sang verifier 7B: **+14.0**.
> Và nó hoạt động ĐÚNG Ở TASK mà truyền trace, che giá trị, Aggregator đều thất bại.
>
> **Khuyến nghị thực dụng:** đừng nhân bản cùng một model thành nhiều vai. Dùng model nhỏ để
> GIẢI, model lớn để SOÁT — rẻ hơn dùng model lớn cho mọi vai, và đây là cấu hình duy nhất
> trong dự án vượt qua kiểm chứng thanh sai số trên bài khó.

### 1b. LỚN nhưng mới đo MỘT LẦN (vượt ngưỡng 5đ, chưa có thanh sai số)

| Cải thiện | Thiết lập | Hiệu ứng | Ghi chú |
|---|---|---|---|
| `loop` — Solver giải lại sau khi bị chê | MATH 1.5B, n=100 | +20đ | 1 lần đo |
| `maj@8` self-consistency | MATH 1.5B, n=100 | +10đ | 1 lần đo |
| Solver 1.5B + Verifier 7B | MATH, **n=50** | +18đ | **đang kiểm lại (H15)** — n nhỏ nhất, khẳng định mạnh nhất |

### 1c. NHỎ HƠN NGƯỠNG NHIỄU — KHÔNG tính là bằng chứng

| "Cải thiện" | Hiệu ứng | Vì sao không tính |
|---|---|---|
| Sửa lỗi bằng chạy test (HumanEval) | +3.6 / +4.8đ | dưới ngưỡng 5đ, đo 1 lần |
| Planner → Solver | +5.2 / +2.0đ | sát ngưỡng, đo 1 lần |
| Aggregator trên GSM8K | +1.2đ | khoảng [−1, +3] **chứa 0** |

*Ngoại lệ đáng giữ:* sửa-lỗi-bằng-chạy-test có **0 phá qua 3 vòng ở CẢ HAI cỡ model** —
bản thân mẫu hình "không bao giờ phá" là tín hiệu đáng tin, dù mức tăng nhỏ.

### 1d. KHÔNG cải thiện / GÂY HẠI (đã xác nhận)

| Can thiệp | Kết quả |
|---|---|
| **Aggregator trên MATH** | **−6.4đ**, khoảng [−9, −4], **5/5 fold âm** |
| Verifier trên MATH | +1.4đ, khoảng [−1, +4] **chứa 0** → CHƯA XÁC LẬP |
| interleaving, cổng lọc, truyền kế hoạch, che giá trị, verify bằng thực thi trên math | đều bị bác |

> ### TRẢ LỜI NGẮN GỌN CHO "CÓ CẢI THIỆN KHÔNG?"
> **CÓ, nhưng ít hơn nhiều so với vẻ ngoài ban đầu.** Thứ đáng tin nhất lại là thứ ĐƠN GIẢN NHẤT:
> **dùng pipeline đa tác tử thay vì một model đơn độc** (+5.6đ trên GSM8K, 5/5 fold),
> và **phần lớn giá trị đó đến từ Verifier** (+4.4đ, 5/5 fold).
> Hầu hết các "mẹo" tinh vi hơn — interleaving, cổng lọc, che giá trị, truyền kế hoạch,
> tổng hợp bằng LLM — KHÔNG cải thiện gì, hoặc gây hại.
> Và **trên MATH thì ngay cả điều đó cũng không đúng**: Verifier chưa xác lập được,
> Aggregator gây hại rõ rệt.

---

## 2. Những gì CÓ TÁC DỤNG (số liệu thô, chưa lọc theo nhiễu)

| Phương pháp | Thiết lập | Kết quả |
|---|---|---|
| **Solver 1.5B + Verifier 7B** (post-hoc, 1 lần) | MATH, n=50 | **.46 → .64** (+18đ), 9 sửa / **0 phá** |
| **loop** — Solver giải lại sau khi Verifier chê | MATH 1.5B, n=100 | **.40 → .60** (+20đ) |
| **Pipeline đầy đủ** so với Solver đơn độc | GSM8K 1.5B, n=250 | **.632 → .744** (+11.2đ) |
| **Self-consistency** maj@8 | MATH 1.5B, n=100 | **.50 → .60** (+10đ) |
| **Sửa lỗi bằng chạy test** (3 vòng) | HumanEval, n=164 | .531→.567 (1.5B); .787→**.835** (7B); **0 phá** cả 3 vòng |
| **Planner → Solver** | GSM8K / MATH 1.5B | .632→.684 / .405→.425 |
| **Verifier đọc lời giải** | MATH 7B, n=200 | **+6.5đ** (17 sửa / 4 phá) |

## 2. BẢNG "ĐẢO DẤU" — ĐÃ HẠ CẤP TOÀN BỘ VÌ THIẾU KIỂM CHỨNG

Các bản trước trình bày bảng dưới đây như PHÁT HIỆN CHỦ ĐẠO. Sau khi đo sàn nhiễu (mục 0),
**chỉ MỘT dòng từng được kiểm bằng 5 fold — và nó KHÔNG SỐNG SÓT.** Bốn dòng còn lại
vẫn chỉ là **đo một lần mỗi ô**, chưa từng có thanh sai số.

| Can thiệp | Ô A | Ô B | Biên độ | Đã kiểm 5 fold? | Kết cục |
|---|---|---|---|---|---|
| **Truyền trace cho V và A** (H10/H14) | GSM8K: −7.0 **[−10,−2]** | MATH: **+0.4 [−6,+4]** | — | ✅ **CÓ** | ❌ **BỊ HẠ CẤP** — hai khoảng CHỒNG LẤN, MATH chứa 0 |
| Che giá trị trung gian (H6) | GSM8K +8.4đ | MATH −2.0đ | 10.4 | ❌ chưa | ⚠️ CHƯA KIỂM CHỨNG |
| Verifier bịt mắt vs đọc (H1) | GSM8K +2.0đ | MATH 7B −6.0đ | 8.0 | ❌ chưa | ⚠️ CHƯA KIỂM CHỨNG |
| Context không liên quan (X_cross) | 1.5B −3.6/−3.5đ | MATH 7B +5.5đ | 9.1 | ❌ chưa | ⚠️ CHƯA KIỂM CHỨNG |
| Aggregator LLM vs bỏ phiếu (H2/H12) | MATH 1.5B −6.7đ | MATH 7B +1.7đ | 8.4 | ❌ chưa | ⚠️ CHƯA KIỂM CHỨNG |

> ### BÀI HỌC QUAN TRỌNG NHẤT CỦA DỰ ÁN
> Chúng tôi xây cả một câu chuyện trên bảng này. Khi đem **đúng một dòng** đi kiểm bằng 5 fold,
> nó **tan biến**: con số +9.0 trên MATH hoá ra là nhiễu, chạy lại cho +0.4.
> **Không có lý do gì để tin bốn dòng còn lại vững hơn dòng đã sụp.**
> Mọi dòng ⚠️ phải được đọc như GIẢ THUYẾT CHƯA KIỂM CHỨNG, không phải kết quả.
>
> Phát biểu duy nhất còn đứng: **truyền trace có ích trên GSM8K** (−7.0đ khi cắt, 5/5 fold);
> **trên MATH không đo được tác dụng**. Đó là PHỤ THUỘC ĐỘ LỚN theo task, KHÔNG phải đảo dấu.

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
