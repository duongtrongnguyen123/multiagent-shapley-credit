# Verifier có sửa được lỗi của Solver không?

Pipeline đầy đủ `P→S→V→A`, chấm điểm **sau từng tầng**, GSM8K 1.5B, 5 fold × 30 = 150 câu.
Kernel `pipeline/fullpipe_rescue_kernel.py`; trace đầy đủ ở `results_rescue/gsm8k/traces.json`
(150 câu × 5 lượt sinh).

Vòng này sinh ra vì các vòng inspect/fewshot trước **chỉ chạy Planner→Solver**, nên mọi câu bị
tính là sai ở đó có thể đã được Verifier sửa trong pipeline thật.

## 1. Accuracy theo từng tầng

| tầng | acc | theo fold |
|---|---|---|
| Solver một mình | .640 | .567 .633 .600 .733 .667 |
| P→S | **.700** | .633 .767 .633 .767 .700 |
| P→S→V | .693 | .667 .633 .700 .700 .767 |
| P→S→V→A | .700 | .633 .633 .733 .700 .800 |

| | mean | khoảng | fold dương |
|---|---|---|---|
| `V_gain` (V − S) | **−0.007** | [−.133, +.067] | 3/5 |
| `A_gain` (A − V) | **+0.007** | [−.033, +.033] | 2/5 |

**Cả hai đều không phân biệt được với 0.** Khoảng chứa 0, fold không cùng dấu, độ lớn dưới
ngưỡng 5 điểm của sàn nhiễu H13.

Nói cách khác: **cộng thêm Verifier và Aggregator vào P→S không thay đổi accuracy** trong
thiết lập này. Thứ duy nhất có tác dụng là bản thân cái plan (.640 → .700).

## 2. Nhưng bên trong thì rất động

Accuracy đứng yên **không có nghĩa là không có gì xảy ra**. Đếm chuyển tiếp từng câu:

| | số câu |
|---|---|
| Verifier **cứu** (S sai → V đúng) | **17** |
| Verifier **phá** (S đúng → V sai) | **18** |
| Verifier bỏ lỡ (S sai → V sai) | 28 |
| Aggregator cứu | 4 |
| Aggregator phá | 3 |

**17 cứu và 18 phá gần như triệt tiêu nhau.** Đây chính là "agent hỗn loạn" mà signed Shapley
của dự án chỉ ra: φ ≈ 0 che giấu churn lớn. Verifier động vào 35/150 câu (23%) nhưng ròng
bằng 0.

Nếu chỉ báo cáo accuracy, ta sẽ kết luận "Verifier vô dụng". Đọc chuyển tiếp thì thấy nó
**vừa hữu ích vừa nguy hiểm**, và hai mặt gần bằng nhau.

## 3. Verifier cứu được loại lỗi NÀO?

Dùng nhánh Solver-một-mình làm phản chứng để tách nguồn gốc lỗi:

| nguồn gốc lỗi | số ca | Verifier cứu được |
|---|---|---|
| **lỗi do PLAN gây ra** (một mình đúng, có plan sai) | 14 | **10 (71%)** |
| **lỗi do SOLVER tự gây** (một mình cũng sai) | 31 | **7 (23%)** |

**Đây là kết quả đáng chú ý nhất.** Verifier gỡ được **71%** lỗi do plan gây ra, nhưng chỉ
**23%** lỗi do Solver tự gây.

Giải thích hợp lý: lỗi do plan là lỗi **ngoại lai** — Solver vốn đủ sức làm đúng bài đó, chỉ bị
plan dắt đi sai. Verifier đọc lại đề và lời giải thì phát hiện được. Còn lỗi Solver tự gây là
lỗi **năng lực** — bài vượt quá khả năng của model 1.5B, nên một model 1.5B khác đọc lại cũng
không gỡ nổi.

Hệ quả trực tiếp cho câu hỏi mở đầu: **các "lỗi do Planner" mà vòng trước đếm được phần lớn
KHÔNG sống sót qua pipeline thật** — Verifier gỡ 10/14. Mọi kết luận về tác hại của Planner đo
ở tầng P→S đều bị phóng đại.

## 4. Giả thuyết "Solver chép nên Verifier không có gì để kiểm" — BỊ BÁC

Trước khi chạy, tôi dự đoán: khi Solver chép plan, lời giải chỉ dài 16–68 ký tự nên Verifier
gần như không có gì để kiểm tra, khiến copycat nguy hiểm hơn vẻ ngoài.

**Dữ liệu nói ngược lại:**

| | n | median độ dài lời giải Solver | S sai → V cứu |
|---|---|---|---|
| Solver **chép** plan | 82 | **17 ký tự** | 8/19 = **42%** |
| Solver **không chép** | 68 | 365 ký tự | 9/26 = **35%** |

| trong các ca Solver sai | n | V cứu |
|---|---|---|
| lời giải **ngắn** (<200 ký tự) | 24 | **12 = 50%** |
| lời giải **dài** (≥200 ký tự) | 21 | 5 = **24%** |

Lời giải **càng ngắn thì Verifier càng dễ cứu**, không phải càng khó. Giả thuyết sai.

Giải thích: Verifier nhận đề bài **và** lời giải. Khi lời giải chỉ là `"The answer is 3."`,
không có gì để bị dẫn dắt — Verifier buộc phải tự giải lại từ đề, và một lượt giải mới thì có
cơ hội đúng. Khi lời giải dài và sai, Verifier bị chính lập luận đó neo vào (anchoring) nên khó
thoát ra hơn.

Điều này khớp với phát hiện `d23ef44` của dự án (*"giving the verifier the plan destroys its
checking"*) và với hiệu ứng **blind verifier** (`e25cd0b`: verify không nhìn lời giải cộng 7–11
điểm, verify có nhìn cộng ~0). Cùng một cơ chế: **càng ít context sai, verifier càng tốt.**

Đáng lưu ý: 87/150 câu (58%) có plan để lộ đáp án **sai**, Solver chép 19, Verifier cứu 54.

## 5. Kết luận

1. **Verifier và Aggregator không cộng thêm accuracy** trong thiết lập này (V_gain −0.007,
   A_gain +0.007, cả hai chứa 0 trong khoảng).
2. **Nhưng chúng không đứng yên**: 17 cứu / 18 phá — churn 23% số câu, ròng bằng 0. Đây là
   agent hỗn loạn theo đúng nghĩa signed Shapley.
3. **Verifier gỡ lỗi ngoại lai tốt hơn lỗi năng lực nhiều**: 71% lỗi do plan gây ra, chỉ 23%
   lỗi Solver tự gây. ⇒ tác hại của Planner đo ở tầng P→S là **phóng đại**, vì pipeline thật
   gỡ được phần lớn.
4. **Lời giải ngắn dễ cứu hơn lời giải dài** (50% vs 24%) — bác bỏ giả thuyết "chép làm
   Verifier mù", và củng cố cơ chế blind-verifier: context sai gây hại nhiều hơn thiếu context.

## 6. Giới hạn

- n = 150 (5 × 30). Sàn nhiễu H13 ở n ≤ 250 là ~5 điểm; V_gain và A_gain đều nhỏ hơn thế nhiều
  nên **chỉ kết luận được là "không đo được hiệu ứng"**, không phải "chắc chắn bằng 0".
- Các tỉ lệ ở mục 3 và 4 dựa trên 14–87 ca, chưa có thanh sai số theo fold. Chúng là **đếm ca
  để đọc cơ chế**, cần lặp lại ở n lớn hơn trước khi coi là số công bố.
- Mới chạy GSM8K. Bản MATH chưa chạy — mà theo bảng đảo dấu của dự án, MATH rất hay cho kết quả
  ngược.
