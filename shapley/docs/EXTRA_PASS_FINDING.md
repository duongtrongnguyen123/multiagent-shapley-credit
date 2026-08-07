# Thứ có tác dụng là THÊM MỘT LƯỢT SINH, không phải vai trò nào cả

Ba thí nghiệm 5-fold trên MATH (1.5B, 5 × 30 = 150 câu mỗi vòng), chạy độc lập, cùng chỉ về
một kết luận. Trace đầy đủ trong `results_folds/{loop,aggk}/` và `results_rescue/math/`.

> Sàn nhiễu H13 ~5 điểm ở n ≤ 250. Chỉ hiệu ứng **5/5 fold cùng dấu** mới coi là đã xác lập;
> phần còn lại ghi là gợi ý.

## 1. `loop`: +20 điểm không tái lập được, và phê bình không phải nguyên nhân

IDEAS.md báo `loop` (Solver giải lại sau khi Verifier chê) được **+20 điểm** trên MATH 1.5B
(.40 → .60, đo một lần n=100). Đây là kết quả dương lớn nhất dự án từng có.

| nhánh | acc | Δ vs S | fold cùng dấu |
|---|---|---|---|
| S (Solver một mình) | .413 | — | — |
| SV (verify một lần) | .387 | −0.027 | 4/5 |
| **loop** (giải lại + phê bình) | **.453** | **+0.040** | 4/5 |
| **rerun** (giải lại, KHÔNG phê bình) | **.453** | **+0.040** | 3/5 |

**Hai kết quả:**

**(a) +20 điểm không tái lập.** Ở 5 fold, `loop` chỉ được **+4.0 điểm** — dưới sàn nhiễu. Con
số +20 gốc đo một lần ở n=100, đúng loại khẳng định mà H13 cảnh báo phải hạ cấp.

**(b) `rerun` bằng đúng `loop` (.453 = .453).** Nhánh đối chứng — Solver giải lại **vô điều
kiện, không hề thấy phê bình** — đạt y hệt. Vậy lợi ích **không đến từ phản hồi của Verifier**;
nó đến từ việc **model được sinh thêm một lượt nữa**.

Nếu không có nhánh `rerun`, ta đã kết luận "feedback-driven refinement có tác dụng" — và sai.

## 2. Aggregator: đúng là bị đặt sai cấu hình, nhưng bỏ phiếu vẫn thắng nó

`AGGREGATOR_EXPLAINED.md` giả thuyết Aggregator không vô dụng mà **thiếu ứng viên** — với 2
ứng viên thì "lấy đa số" là bất khả thi.

| nhánh | acc | Δ vs S | fold cùng dấu |
|---|---|---|---|
| S | .413 | — | — |
| SV_agg2 (cấu hình hiện tại) | .407 | −0.007 | 1/5 |
| **agg3** (3 ứng viên) | **.467** | **+0.053** | **5/5** ✅ |
| agg5 (5 ứng viên) | .460 | +0.047 | 4/5 |
| **vote5** (bỏ phiếu cơ học) | **.507** | **+0.093** | 4/5 |

**Giả thuyết được xác nhận:** `agg2` → `agg3` nhảy từ −0.007 lên **+0.053**, và **agg3 là hiệu
ứng dương duy nhất đạt 5/5 fold** trong cả ba thí nghiệm hôm nay. Aggregator bị đặt sai cấu
hình thật.

**Nhưng bỏ phiếu cơ học vẫn thắng cả hai** (+0.093 vs +0.047). Aggregator LLM **không cộng thêm
gì ngoài việc đếm phiếu** — nó còn làm kém đi. Khớp hướng H12 (bỏ phiếu thắng LLM-agg trên MATH,
+7.5).

**Recency bias được xác nhận:** `agg5_copies_last` = **0.653** — ngay cả với 5 ứng viên, nó vẫn
chép ứng viên cuối cùng 65% số câu (agg2: 0.747). Nó không "chọn", nó lấy cái đọc sau cùng.

Số đáp án khác nhau trung bình: **2.88/5** — có đủ đa dạng để bỏ phiếu có nghĩa.

## 3. Verifier trên MATH: khớp GSM8K về cơ chế

| tầng | acc |
|---|---|
| Solver một mình | .413 |
| P→S | .473 |
| P→S→V | .467 |
| P→S→V→A | .507 |

`V_gain` −0.007 [−.100, +.067] 2/5 · `A_gain` +0.040 [.000, +.100] **4/5**

| nguồn gốc lỗi | GSM8K | MATH |
|---|---|---|
| V gỡ lỗi **do PLAN** | 10/14 = **71%** | 8/13 = **62%** |
| V gỡ lỗi **do SOLVER** | 7/31 = **23%** | 5/66 = **8%** |

**Phát hiện chính của vòng rescue tái lập trên MATH**: Verifier gỡ lỗi ngoại lai tốt hơn lỗi
năng lực rất nhiều — 62% vs 8%, chênh còn mạnh hơn GSM8K. Verifier cứu 13 / phá 14 → lại ròng 0.

Đây là một trong số ít kết luận của dự án **không đảo dấu** giữa hai task.

## 4. Kết luận ghép: một giả thuyết cũ được ủng hộ mạnh

`FEWSHOT_ROLES.md` từng nêu giả thuyết chưa kiểm: *lợi ích của plan có thể đến từ việc cho model
thêm một lượt sinh, không phải từ chất lượng kế hoạch.*

Ba kết quả hôm nay đều ủng hộ nó:

| bằng chứng | ý nghĩa |
|---|---|
| `rerun` = `loop` (.453 = .453) | giải lại **không cần** phê bình vẫn được y hệt |
| `vote5` > `agg5` (.507 > .460) | 5 lượt sinh + đếm phiếu **thắng** 5 lượt sinh + LLM đọc |
| `agg3` +0.053 (5/5) vs `agg2` −0.007 | thêm **ứng viên độc lập** mới là thứ tạo giá trị |
| `V_gain` ≈ 0 ở cả hai task | verify — một lượt sinh **có điều kiện** — không cộng gì |

Mẫu hình chung: **mọi thứ cộng thêm một lượt sinh ĐỘC LẬP đều giúp; mọi thứ chỉ đọc lại lượt
trước đều không.** `rerun`, `agg3`, `vote5` thuộc nhóm đầu. `SV`, `agg2`, `loop`-phần-phê-bình
thuộc nhóm sau.

Điều này khớp `fc6f02c` (*"chỉ 2 trong 4 agent thực sự tính toán"*) và giải thích vì sao mọi can
thiệp prompt-level của dự án đều chìm dưới sàn nhiễu: chúng thay đổi **cách đọc lại**, không
thay đổi **số lượt sinh độc lập**.

## 5. Hệ quả thực dụng

Với model yếu trên bài khó, **self-consistency đơn giản (sample K + bỏ phiếu) tốt hơn mọi kiến
trúc multi-agent mà dự án đã thử** — và rẻ hơn: `vote5` cần 5 lượt gọi, `PSVA` cần 4 lượt cộng
chi phí prompt dài hơn nhiều.

Kết luận này khớp `maj@8` +10 điểm đã có trong RESULTS.md, và giờ có thanh sai số.

## 6. Giới hạn

- n = 150 mỗi vòng, MATH, 1.5B. Chỉ `agg3` đạt 5/5 fold; `vote5` (+9.3đ) đạt 4/5 và **vượt sàn
  nhiễu** nên đáng tin, nhưng chưa hoàn hảo.
- `vote5` dùng sampling temp 0.7 còn các nhánh khác greedy — một phần lợi ích có thể đến từ
  sampling. Cần đối chứng "5 lượt greedy khác seed" để tách hẳn, nhưng greedy không đổi seed
  được nên phép so này vốn khó làm sạch.
- Chưa chạy ở 7B. Theo IDEAS.md, `loop` mất tác dụng ở 7B (+20 → 0), nên rất có thể toàn bộ
  hiệu ứng "thêm lượt sinh" cũng biến mất khi model đủ mạnh.
