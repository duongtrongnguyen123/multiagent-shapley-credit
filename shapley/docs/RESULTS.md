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
| **Aggregator trên MATH** | **−6.4đ** [−9,−4] 5/5 âm — NHƯNG xem ghi chú ⬇️ |
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

**Verifier mang gần như toàn bộ giá trị** (+4.8 — đã kiểm 5 fold: +4.4, khoảng [+1,+8]).
⚠️ Con số "Aggregator thêm +1.2" **DƯỚI ngưỡng nhiễu 5 điểm** và khoảng của nó là [−1,+3]
(chứa 0) → **KHÔNG phải bằng chứng**.
*Lưu ý trung thực:* nhánh P→S→A là **cấu hình thoái hoá** — một bộ tổng hợp chỉ nhận **một**
ứng viên thì không có gì để tổng hợp, nên nó đi giải lại và hỏng. Con số −25.6 phản ánh điều đó,
không phải "Aggregator vô dụng".

## 4. Giá trị của V và A phụ thuộc hoàn toàn vào context (H10, GSM8K 1.5B)

| Pipeline | acc |
|---|---|
| P→S→V→A, **toàn văn** | **.744** |
| P→S (bỏ hẳn V và A) | .684 |
| P→S→V→A, **chỉ đáp án** | **.668** |

⚠️ Chênh lệch −1.6 (TRIM vs NOVA) **DƯỚI ngưỡng nhiễu** → không kết luận được.
Phần ĐỨNG VỮNG: FULL vs TRIM = **−7.0đ, khoảng [−10,−2], 5/5 fold** (rc_g15) — tức trên GSM8K,
truyền trace cho V và A thực sự đáng giá. Trên MATH 1.5B thì **không** ([−6,+4], rc_m15).

## 4b. PHÁT BIỂU HỢP NHẤT (đang chờ mắt xích cuối)

| Trên MATH | Solver+Verifier 1.5B | Verifier 7B |
|---|---|---|
| giá trị Verifier | +1.4 **[−1, +4]** ❌ | **+14.0 [+8.3, +20.0]** ✅ 5/5 fold |
| giá trị truyền trace | +0.4 **[−6, +4]** ❌ | **−17.5 khi cắt** ⚠️ *1 lần đo, đang kiểm (H17)* |
| Aggregator | **−6.4 [−9, −4]** hại | ~0 |

> **BỘ MÁY ĐA TÁC TỬ CHỈ HOẠT ĐỘNG KHI MODEL ĐI KIỂM ĐỦ MẠNH ĐỂ DÙNG ĐƯỢC THỨ NÓ ĐƯỢC ĐƯA.**
> Ở 1.5B, verifier không khai thác nổi phần trình bày → truyền trace vô ích, và mọi can thiệp
> đều thất bại. Ở 7B, cả verifier lẫn trace đều bắt đầu sinh lợi.
>
> ⚠️ **Nửa sau của phát biểu (phần về trace) đang dựa trên MỘT phép đo.** Kernel `rc_m7` đang
> kiểm bằng 5 fold. Nếu khoảng chứa 0, phát biểu phải THU HẸP còn: *"một verifier MẠNH HƠN
> có giá trị"* — và không được nói gì về trace.

> ### ⚠️ ĐÍNH CHÍNH: "AGGREGATOR GÂY HẠI" LÀ LỖI PARSING (H20, af_m)
> Đọc trace: **85%** ca "phá" của Aggregator KHÔNG phát ra `\boxed`, chỉ **5%** là chọn nhầm thật.
> Thêm một FALLBACK miễn phí (không có `\boxed` → lấy đáp án Verifier, **không gọi thêm model**):
>
> | | A_gain | khoảng | fold |
> |---|---|---|---|
> | base | **−6.4** | [−9,−4] | 5/5 âm |
> | **+ fallback** | **+1.0** | **[0,+2]** | **5/5 ≥ 0** |
>
> ⇒ Phép ĐO đúng, nhưng DIỄN GIẢI "LLM tổng hợp phán đoán kém" là SAI.
> Phát biểu đúng: **bộ tổng hợp LLM trung tính một khi đã xử lý định dạng đầu ra.**

---

## 4c. CƠ CHẾ — VÌ SAO CÁC VAI HÀNH XỬ NHƯ VẬY (từ 600 trace thô)

Toàn bộ mục này rút ra từ việc ĐỌC output thô, không phải từ số tổng hợp.
Năm lần đọc trace, năm lần lật lại một diễn giải.

### (1) AI THỰC SỰ TÍNH TOÁN? — chỉ 2/4 vai
| Agent | median ký tự | số MỚI/lượt | % lượt KHÔNG có số mới | đáp án = agent trước |
|---|---|---|---|---|
| **Planner** | 501 | **6** | **0.0%** | — |
| Solver | 20 | 0 | 69.0% | 62.5% |
| **Verifier** | 592 | **4** | 20.5% | 69.0% |
| Aggregator | 18 | 0 | **100.0%** | **96.0%** |

Pipeline "4 tác tử" thực chất là **2 tác tử tính toán + 2 trạm chuyển tiếp** (số liệu GSM8K 1.5B).

### (2) PLANNER KHÔNG LẬP KẾ HOẠCH — NÓ GIẢI, RỒI GIẤU ĐÁP ÁN
Nó sinh 6 số mới ở **100%** số lượt (0% lượt không tính) nhưng chỉ **3.3%** có `\boxed`;
đáp án ngầm vẫn trích được ở **32–45%** kế hoạch.
⇒ Chỉ dẫn *"Do NOT compute the final answer"* **không ngăn nó tính**, chỉ khiến nó **không nói ra**.
Hệ quả: khi kế hoạch ĐÚNG, Solver đúng **98.9%**; khi kế hoạch SAI, chỉ **37.6%**.

### (3) VERIFIER KHÔNG KIỂM TRA — NÓ GIẢI LẠI TỪ ĐẦU
Tỉ lệ Verifier **tái sử dụng số của Solver** (bỏ số vốn có trong đề):
| | toàn bộ | khi ĐỒNG Ý | khi SỬA | khi PHÁ |
|---|---|---|---|---|
| GSM8K | .17 | .20 | **0.00** | **0.00** |
| MATH | .83 | 1.00 | .33 | .29 |

Mỗi khi **can thiệp**, nó **vứt bỏ toàn bộ chuỗi của Solver**. Chỉ tái sử dụng khi đang **đồng ý**.
⇒ Vì thế độ chính xác can thiệp ≈ **độ chính xác TỰ GIẢI** của model, chứ không phải độ chính xác
của việc KIỂM (đáng lẽ dễ hơn nhiều):

| Verifier | sửa/phá | độ chính xác can thiệp |
|---|---|---|
| 1.5B | 18/14, 32/22 | **56–59%** ≈ chính nó tự giải (~.63) |
| **7B** | **43/1** | **98%** |

⇒ **Verifier không phải bộ kiểm tra tồi — nó là một SOLVER THỨ HAI đội lốt bộ kiểm tra.**
Mua verifier 7B tức là mua một **solver tốt hơn** cho lượt thứ hai.

### (4) AGGREGATOR HỎNG KHÁC HẲN: LỖI ĐỊNH DẠNG, KHÔNG PHẢI PHÁN ĐOÁN
Phân loại 20 ca PHÁ trên MATH: **85%** không phát ra `\boxed` · 50% tự giải lại ·
40% output thoái hoá · **chỉ 5% chọn nhầm ứng viên thật**.
⇒ Sửa bằng fallback **miễn phí**: −6.4 → **+1.0** (xem đính chính ở mục 4b).

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

---

## 7. CẬP NHẬT VÒNG #43–#49 — HAI RÚT LẠI VÀ MỘT PHÁT HIỆN DƯƠNG
*(mọi số dưới đây ĐO ĐƯỢC, có đăng ký trước; xem PREREGISTRATION.md #2, #23–#30)*

### 7.1 RÚT LẠI: "Aggregator LLM là SAI LOẠI, phải thay bằng thống kê"
Phát biểu cũ dựa trên so sánh KHÔNG CÔNG BẰNG (aggregator không có chỉ dẫn CoT, 384 token
so với 1024 của solver). Chạy lại CÔNG BẰNG (cùng CoT, cùng 1024 token):
| ô | maj@8 | agg_fair | vs maj | đè/cứu đa số |
|---|---|---|---|---|
| 1.5B | .533 | .467 | −.067 | 15 / 7 |
| **7B** | .717 | **.725** | **+.008** | **3 / 4** |
Số cũ ở 7B: đè **26** đa số đúng, cứu **0**. Số mới: đè **3**, cứu **4**.
=> **H2 BỊ BÁC ở 7B.** Phát biểu thay thế (HẸP): ở model yếu (1.5B) tổng hợp bằng LLM kém
   bỏ phiếu, đặc biệt khi phải đọc TOÀN BỘ lời giải (−.175); ở 7B **không còn khác biệt đo được**.

### 7.2 RÚT LẠI: "verifier bịt mắt bắt lỗi tốt hơn" (H1)
`fixes` blind vs informed: GSM8K 1.5B 42/20 · GSM8K 7B 6/4 · MATH 1.5B 19/13 · **MATH 7B 9/17 (NGƯỢC)**
=> HÀNG 4 của bảng khoá: **KHÔNG kết luận chung**. Ở GSM8K 1.5B bịt mắt sửa nhiều hơn thật
   (.457 vs .217, p<.001) NHƯNG cũng phá nhiều hơn đúng tỉ lệ (.146 vs .038, p<.001)
   -> giá trị RÒNG gần như không đổi. **Bịt mắt KHÔNG phải bữa trưa miễn phí.**
Nhánh P (xoá đáp án, giữ suy luận) GIỐNG informed ở cả 4 ô => thủ phạm là **PHẦN SUY LUẬN**,
không phải mỏ neo đáp án.

### 7.3 KHUNG "KIỂM TRA" KHÔNG MANG THÔNG TIN — MỎ NEO MỚI MANG (H24, 3/4 ô)
Cùng bộ lời giải, mỗi nhánh đúng 1 lần sinh thêm:
| ô | V_inf | V_bli | **S_anc** (không có chữ "kiểm") | **S_pln** (không mỏ neo) |
|---|---|---|---|---|
| GSM8K 1.5B | +.060 | +.076 | **+.080** | **−.012** |
| MATH 1.5B | +.050 | +.055 | +.035 | +.025 |
| GSM8K 7B | +.004 | +.004 | **+.008** | +.000 |
`S_pln` TỆ NHẤT ở cả 3 ô; `S_anc` ngang/hơn `V_bli` ở 2/3.
=> Thứ tạo ra giá trị là **cho model thấy đáp án trước đó**, không phải bảo nó "hãy kiểm tra".
   (CHƯA CHỐT — chờ ô thứ 4.)

### 7.4 PHÁT HIỆN DƯƠNG: 7B PHÁT HIỆN ĐƯỢC LỖI SỐ HỌC — 1.5B THÌ KHÔNG
Lỗi số học TIÊM SẴN vào chuỗi vàng (cả hai nhánh cùng văn phong -> không lộ nhãn):
| model | suy biến | phân biệt (HIGH) | HỢP LỆ |
|---|---|---|---|
| 1.5B | **.99** (luôn nói "NO") | — | **KHÔNG** |
| **7B** | .60 | **+.651** (n=166) | **CÓ** |
=> Ngưỡng NĂNG LỰC cho việc kiểm, đo ở nhiệm vụ kiểm THUẦN TUÝ (không lẫn với giải).
⚠️ Tầng "model KHÔNG giải nổi" ở GSM8K 7B chỉ có **9 cặp** -> câu hỏi "kiểm có tách rời khỏi
   giải không" **CHƯA trả lời được**. Đang chạy lại trên MATH (tầng đó đông hơn).

### ⚠️ 7.5 **TẠM ĐÌNH CHỈ** — số dưới đây đo trên bể mẫu BỊ HỎNG (xem vòng #59–#60)
Mẫu đánh giá sinh khi LoRA Yes/No còn BẬT -> Solver bị bộ chấm làm hỏng (`greedy1` tụt 13 điểm
giữa hai lần chạy chỉ khác lượng huấn luyện). H27/H28/H28b/H31 **không được trích dẫn** cho tới khi
bản sửa (đăng ký trước #36, ngưỡng `adapter_leak <= .05`) chạy xong.

### 7.5 NGHỊCH LÝ: bộ chấm AUC .883 VẪN KHÔNG thắng đếm phiếu
Verifier PHÂN BIỆT huấn luyện trên 3200 nhãn TỰ ĐỘNG (grader, không gán tay):
**AUC .883** | greedy .533 | **maj@8 .703** | **rerank@8 .687** | oracle@8 .843
=> rerank − maj = **−.017** (2/5 fold dương) -> HÀNG 2: **chấm điểm không thêm gì so với đếm phiếu**.
GIẢ THUYẾT: `argmax` chọn MỘT mẫu và vứt bỏ thông tin ĐỒNG THUẬN mà đếm phiếu đang dùng.
Đang kiểm bằng **bỏ phiếu có trọng số** (pre-reg #29).
**⚠️ ĐÍNH CHÍNH HAI CHIỀU (H30 #33, rồi H31 #35 sửa lại chính nó):** con số "+14.0 điểm" BỊ THỔI PHỒNG,
NHƯNG bản sửa đầu tiên lại QUÁ BI QUAN. `oracle@k` phóng đại (tính bài chỉ 1/k mẫu đúng);
`oracle_solid@k` hạ thấp (trên MATH nó .285, **thấp hơn cả maj@8 .295** -> không phải trần hợp lệ).
Trần thật nằm trong **[`oracle_solid`, `oracle`]**. Bằng chứng cứng: bỏ phiếu có trọng số đạt
maj@8 **+11.0 điểm (5/5 fold, GSM8K 1.5B)** nên trần thật ít nhất là mức đó. Chi tiết cũ:
`oracle@k` tính là thành công cả bài chỉ có **1/k** mẫu đúng (trên GSM8K, đáp án số nguyên -> phần lớn
là TRÙNG SỐ). Dùng `oracle_solid@8` (đòi >=2/k mẫu đúng): GSM8K khoảng trống thật **+.060** (34% của
+.175), MATH **+.005** (7% của +.075, 2/5 fold ÂM -> không khác 0).
Khoảng trống thật nhỏ hơn ~3× (GSM8K) và ~14× (MATH).

### 7.6 RL TRÊN VERIFIER: HỌC CÁCH IM LẶNG (H23)
GRPO thưởng theo độ chính xác can thiệp: precision .70–.90 -> **1.00 cả 5 fold** (22 sửa/**0 phá**)
NHƯNG V_gain +.068 -> **+.044** (0/5 fold tốt hơn) và số lần can thiệp **20.2 -> 8.4 /100**.
=> Đạt precision 1.00 bằng cách NÓI ÍT ĐI MỘT NỬA. Lỗi ở HÀM THƯỞNG (im lặng được 0 điểm,
   tức là MIỄN PHÍ), không ở thuật toán. Chỉ số "số lần can thiệp" đã khoá trước mới lộ ra điều này.

### 7.7 LUẬT PHƯƠNG PHÁP MỚI (rút từ 3 phép đo hỏng liên tiếp)
Mọi thí nghiệm phán đoán nhị phân PHẢI khoá TRƯỚC:
`degenerate_rate` <= .90 (tầng vi phạm -> VÔ HIỆU) · `parse_fail_rate` <= .20 (cả lần chạy VÔ HIỆU)
· cỡ mẫu tối thiểu cho tầng dùng để kết luận · và với thí nghiệm tiêm lỗi: `pct_corruptible` >= .50.
Ba lần ngưỡng này đã cứu khỏi đọc nhầm một phép đo hỏng (dt_g15, dt2_g15, dt3_m15).

---

## 8. VÒNG #59–#70 — BỐN PHÁT HIỆN ĐÃ TÁI LẬP, MỘT NHÁNH BỊ ĐÌNH CHỈ

### 8.1 BỘ KIỂM ĐÚNG ĐẮN vs LLM-ĐI-KIỂM (HumanEval) — kết quả bền nhất dự án
Cùng model, cùng 4 lượt sinh, chỉ khác NGUỒN TÍN HIỆU KIỂM.
| lần chạy | máy | greedy | maj@4 | **exec3** | llm3 | exec3−llm3 | phá exec3 | phá llm3 |
|---|---|---|---|---|---|---|---|---|
| HE 1.5B | Kaggle | .5375 | .4250 | **.6000** | .4812 | +.119 (5/5) | **0.0** | 2.8 |
| HE 1.5B | 5090 | .5625 | .4313 | **.6438** | .4375 | +.206 (5/5) | **0.0** | 4.6 |
| HE 7B | 5090 | .8000 | .7875 | **.8812** | .7812 | +.100 (4/5) | **0.0** | 2.6 |
| HE 7B | Kaggle | .7938 | .7375 | **.9000** | .7438 | +.156 (5/5) | **0.0** | 3.2 |
**0 lần phá trong 20/20 fold; llm3 phá trong 20/20 fold.**
CƠ CHẾ: `exec3` = `oracle@4` **CHÍNH XÁC** (.6438 và .8812). Bộ kiểm là **BỘ CHỌN hoàn hảo**,
không phải bộ sửa. Phân bố: 14% số bài ở 1.5B chỉ có ĐÚNG 1/4 mẫu đúng — bỏ phiếu gần như
không thể chọn ra, bộ kiểm tìm ra hết. Bỏ phiếu bỏ lỡ **21.3 điểm**.
LƯU Ý MỐC: `maj@4` trên code THẤP HƠN greedy (−.113, −.131) -> **bỏ phiếu CÓ HẠI trên code**
(lời giải là chuỗi dài, hiếm khi trùng nhau -> "đa số" là hoà -> chọn ngẫu nhiên).
Vì vậy mốc trung thực là **`exec3 − greedy` = +.063 đến +.106**, không phải `exec3 − maj@4`.

### 8.2 H8b — "CHẠY ĐƯỢC" ≠ "MÔ HÌNH HOÁ ĐÚNG"
| | exec_success | greedy | maj3 | pal1 | pal3 | exec3 | pal3−maj3 |
|---|---|---|---|---|---|---|---|
| MATH 7B | **.875** (.975 sau sửa) | .485 | **.540** | .430 | .475 | .475 | **−.065 (1/5)** |
| MATH 1.5B | **.760** (.895) | .325 | **.370** | .250 | .295 | .280 | **−.075 (0/5)** |
Rào cản của H8 (exec_success .42 < .50) ĐÃ HẾT ở 7B. Nhưng PAL vẫn THUA suy luận văn bản.
Sửa lỗi SẬP có tác dụng nhất quán (`exec3−pal1` = +.045 và +.030, **5/5 fold**) — và vẫn thua.
=> **Bộ kiểm chỉ có giá trị khi là ORACLE VỀ TÍNH ĐÚNG, không phải khi là MỘT CÁCH TÍNH KHÁC.**
=> Hệ quả: bộ kiểm Lean LÀ oracle -> chứng minh định lý thuộc nhóm CODE, không phải nhóm này.

### 8.3 TUẦN TỰ vs SONG SONG ở CÙNG NGÂN SÁCH (mỗi nhánh 3 lượt)
| ô | greedy | maj@3 | PSV | SVV | SS_anc | maj3−PSV |
|---|---|---|---|---|---|---|
| GSM8K 1.5B | .632 | .664 | **.728** | .692 | **.728** | −.084 (5/5) |
| MATH 1.5B | .325 | .385 | **.440** | .385 | — | −.055 (0/5) |
| MATH 7B | .480 | .515 | **.595** | .525 | .475 | −.080 (0/5) |
| GSM8K 7B | .924 | **.928** | .912 | .924 | .928 | +.016 (3/5) |
Token: `PSV` **2.29×** greedy vs `maj@3` **2.96×** -> tuần tự RẺ HƠN 22% mà vẫn hơn.
`SS_anc` (không có ngôn ngữ vai) = `PSV` chính xác -> **cơ chế là MỎ NEO, không phải VAI**.
ĐỐI CHỨNG `maj3_g` (bỏ phiếu có 1 mẫu greedy) ≈ `maj@3` ở **7 ô** -> loại trừ nhiễu loạn giải mã.

### 8.4 KIỂM LỖI = NĂNG LỰC × MIỀN (không chỉ năng lực)
| | 1.5B | 7B |
|---|---|---|
| GSM8K | suy biến .99 VÔ HIỆU | **+.651** |
| MATH | suy biến .99 VÔ HIỆU | **+.113** (ZERO n=224, HỢP LỆ + ĐỦ LỰC) |
Chênh **5.8 lần** chỉ vì miền. Ở MATH, ZERO (+.116) ≈ HIGH (+.113) -> yếu ĐỀU, không phải
"bị chặn bởi năng lực giải". Đây là lần thứ hai kết luận "năng lực" hoá ra là "năng lực × miền".

### 8.5 ĐỒNG THUẬN — tín hiệu miễn phí, mạnh hơn bộ chấm huấn luyện
k=8: đồng thuận 8/8 -> acc **1.000**; 1/8 -> **.143** (GSM8K) / **.000** (MATH).
k=3: **50–58% số bài KHÔNG có đa số** -> `maj@3` thoái hoá thành "lấy mẫu đầu".
Chỉ cần đếm. So với bộ chấm huấn luyện (AUC .88–.95) tốn dữ liệu + LoRA + đã gây lỗi rò rỉ adapter.

### 8.6 ĐANG ĐÌNH CHỈ
H27/H28/H28b/H31 (rerank, bỏ phiếu có trọng số, oracle_solid) — lỗi RÒ RỈ ADAPTER:
mẫu đánh giá sinh khi LoRA Yes/No còn bật. Không trích dẫn tới khi bản sửa (#36/#37) chạy xong.

### 8.2b H8b CHỐT — PAL thua ở 5/5 phép đo (bổ sung cho 8.2)
Phép thử GSM8K THẬT (trước bị lỗi tham số `task` che mất — kernel hardcode MATH):
| ô | exec_ok | greedy | maj@3 | pal3 | exec3 | pal3−maj3 | exec3−pal1 |
|---|---|---|---|---|---|---|---|
| GSM8K 7B | **.980** | .948 | .944 | .876 | — | **−.068 (0/5)** | — |
| GSM8K 1.5B | .872 | .492 | .480 | .436 | — | **−.044 (1/5)** | — |
| MATH 7B n200 | .875 | .485 | .540 | .475 | .475 | −.065 (1/5) | +.045 (5/5) |
| MATH 7B n250 | .852 | .480 | .508 | .452 | .452 | −.056 (2/5) | +.048 (5/5) |
| MATH 1.5B | .760 | .325 | .370 | .295 | .280 | −.075 (0/5) | +.030 (5/5) |
**exec_success .98 ở GSM8K 7B** -> chương trình chạy được gần như luôn luôn; vẫn thua văn bản.
Sửa lỗi SẬP giúp nhất quán (`exec3−pal1` dương **5/5 fold** ở cả ba ô MATH) mà vẫn không đủ.
=> Xác lập phân biệt: **ORACLE VỀ TÍNH ĐÚNG** (bộ test) vs **MỘT CÁCH TÍNH KHÁC** (chạy Python cho toán).
=> Lean là oracle -> chứng minh định lý thuộc nhóm CODE; kết quả âm này KHÔNG áp cho Lean.

## 9. H41 — GIẢ THUYẾT "TRẦN" BỊ BÁC TRONG GSM8K (pre-reg #47)

Kiểm tra khắt khe nhất: escalate đã **thua** trên GSM8K (−.064, 0/5 fold, vòng #79).
Nếu "trần" là nguyên nhân thật thì NGAY TRONG GSM8K, nhóm bài nhiều bước (7B xa trần hơn)
phải cho `gain` cao hơn nhóm ít bước.

**Thiết kế:** 1319 bài GSM8K, bf16 trên RTX 5090, k=8 mẫu. Độ khó = số bước tính `<<...>>`
trong lời giải chuẩn. Tách 3 tầng: DỄ (≤2 bước, n=440) · GIỮA (3 bước, n=364) · KHÓ (≥4 bước, n=515).
Giao thức H39: 3 mẫu 1.5B → đồng thuận thì nhận, không → 7B tuần tự có mỏ neo.

### Kết quả tổng quan

| Chiến lược | Accuracy |
|---|---|
| small_maj8 (1.5B ×8) | .711 |
| **big_maj3 (7B ×3)** | **.920** |
| big_maj8 (7B ×8) | .930 |
| escalate_seq | .811 (thua big_maj3 **−10.8đ**) |
| pct_escalated | 33.4% |

### Phân rã theo độ khó

| Tầng | n | pct_esc | big_maj3 | escalate | esc−big3 | opp_cost | gain_on_esc |
|---|---|---|---|---|---|---|---|
| **DỄ** (≤2 bước) | 440 | 20.9% | .952 | .882 | **−.071** | +.081 | **−.033** |
| **GIỮA** (3 bước) | 364 | 29.1% | .931 | .843 | **−.088** | +.097 | **−.066** |
| **KHÓ** (≥4 bước) | 515 | 47.2% | .884 | .728 | **−.155** | +.228 | **−.074** |

Đẳng thức tự kiểm (khoá trước): `escalate_seq − big_maj3 ≈ p_kept·(−opp_cost) + p_esc·gain`
→ **lệch 0.0000 ở cả 3 tầng** → mã đúng, số liệu tin được.

### Kết luận (khoá trước ở pre-reg #47)

`gain(KHÓ) − gain(DỄ)` = −0.074 − (−0.033) = **−0.041 < −0.03** → **NGƯỢC HẶN. Giả thuyết trần CHẾT.**

- `gain_on_esc` **âm ở mọi tầng** — tuần tự có mỏ neo tệ hơn big_maj3 ngay trên tập đã escalate.
- `opp_cost` đi **sai chiều dự đoán**: tăng từ +0.08 (dễ) lên +0.23 (khó), thay vì giảm.
  Tức bài khó càng phải trả đắt để giữ 1.5B, ngược logic "trần".
- Escalate thua **NHIỀU HƠN** ở bài khó (−.155) so với bài dễ (−.071) — ngược hoàn toàn dự đoán.

**Phát biểu thay thế:** khác biệt MATH↔GSM8K (escalate thắng ở MATH, thua ở GSM8K)
**không phải do độ khó trong nhiệm vụ**, mà ở cấp **tác vụ**. Giả thuyết "trần" không giải thích được.
Phải tìm biến khác (độ dài? kiểu suy luận? bộ chấm?) hoặc chấp nhận kết quả #78 trên MATH
có thể không tái lập.

---

## PENDING — THÍ NGHIỆM CHỜ CHẠY

Các kernel đã triển khai, chờ chạy trên Kaggle.

### H17 — rc_m7: MATH 7B FULL vs TRIM, 5 fold

**Kernel:** `pipeline/rc_m7_kernel.py` · **Deploy:** `deploy/orchestrate_rc_m7.py`
**Pre-reg:** #17

Mắt xích cuối của phát biểu hợp nhất. Đã đo 1 lần (trim_minus_full = −17.5). Nay 5 fold.
Nếu khoảng toàn âm → xác nhận phát biểu hợp nhất. Nếu chứa 0 → phải thu hẹp.

### H24 — Ô thứ 4 lưới 2×2: MATH 7B, S_pln vs V_bli vs V_inf

**Kernel:** `pipeline/h24_cell4_kernel.py` · **Deploy:** `deploy/orchestrate_h24_cell4.py`
**Pre-reg:** #24

3/4 ô đã đo: "khung kiểm không mang thông tin, mỏ neo mới mang". Ô cuối (MATH 7B) xác nhận hay bác.

### H27-FIX — Sửa lỗi rò rỉ adapter (#36/#37)

**Kernel:** `pipeline/disc_leakfix_kernel.py` · **Deploy:** `deploy/orchestrate_disc_leakfix.py`
**Pre-reg:** #36, #37

Mẫu đánh giá sinh khi LoRA vẫn bật → solver bị hỏng. Sửa: gen mặc định adapter TẮT.
Ngưỡng rò rỉ: `probe_pre − probe_post` trên 60 bài, |leak| ≤ .05.

### H37 — Huấn luyện bộ kiểm trên lỗi TIÊM, đánh giá chuyển giao lên lỗi THẬT

**Kernel:** `pipeline/injected_classifier_kernel.py` · **Deploy:** `deploy/orchestrate_injected_classifier.py`
**Pre-reg:** #43

Chỉ số chính: `discrimination_real` (chuyển giao). Nếu ≈ 0 → "nhãn rẻ không thay thế nhãn đúng loại".

### Decompose pipeline v2

**Kernel:** `pipeline/decompose_pipeline_kernel.py` (đã sửa: mỗi sub mang original problem + prior answers)
**Deploy:** `deploy/orchestrate_decompose_pipeline.py`
**Kết quả đã có:** GSM8K .08 / MATH .02 (thua Solver-alone ở cả hai).

Kernel đã v2 (mỗi sub-question nhận original problem + previous answer). Kết quả thấp là thật.
