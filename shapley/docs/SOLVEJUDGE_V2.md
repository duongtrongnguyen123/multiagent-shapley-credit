# Solve+Judge pipeline với Judge nâng cấp (few-shot / vote) — kết quả pipeline thật

Bản v1 (`SOLVEJUDGE_MATH.md`) dùng Judge single (greedy binary). Khảo sát `JUDGE_QUALITY.md` cho thấy
vote/few-shot chỉ nâng prec Judge ≤.025 khi đo trên S1. Nhưng khảo sát đó KHÔNG chạy pipeline thật.
Kernel này chạy **pipeline đầy đủ** P→lặp(S+J) với Judge nâng cấp, trên cả MATH & GSM8K, n=150
mỗi task, 5 fold.

- `JUDGE_MODE=fewshot`: Judge + 1 ví dụ đúng + 1 ví dụ sai.
- `JUDGE_MODE=vote`: K=3 Judge độc lập, dừng khi ≥2/3 đồng thuận "đúng".
- Re-solve đổi temperature (1.0→0.7→0.4), budget 3 vòng, dừng sớm.

## Kết quả loop acc

| | v1 single | v2 few-shot | v2 vote |
|---|---|---|---|
| **MATH** | .5133 | .5000 | .5133 |
| **GSM8K** | .6333 | **.6600** | .6467 |

Baseline (cùng bài): MATH alone .407, PSVA .473 · GSM8K alone .640, PSVA .700.

## Đọc kết quả

**1. Trên MATH: vote/few-shot KHÔNG giúp.** v2 fewshot .5000 (THẤP hơn v1 .5133), vote .5133
(ngang v1). Khớp với `JUDGE_QUALITY.md`: Judge 1.5B chạm trần năng lực, thêm call không đáng.

**2. Trên GSM8K: few-shot CÓ giúp nhẹ — và đây là phát hiện mới.** v2 fewshot .6600 > v1 single
.6333 (+2.7), > vote .6467 (+1.3). Điều này **trái với khảo sát Judge-only** (few-shot trên GSM8K
chỉ đổi false-type, prec giảm .02). Lý do: trong pipeline thật, few-shot làm Judge **dừng sớm hơn
đúng** — GSM8K fewshot judge_rec .479 vs vote .261 — nên giữ được câu đúng, re-solve ít hơn, acc
cao hơn. **Khảo sát Judge-only không dự đoán được hiệu quả pipeline.**

**3. Vote làm Judge QUÁ BI QUAN.** GSM8K vote judge_rec chỉ .261 (Judge vote "đúng" rất ít) →
đẩy hầu hết câu đi re-solve → tốn call (4.64) mà acc không hơn (GSM8K .6467). vote đòi 2/3 đồng
thuận "đúng" — nhưng Judge 1.5B vốn đã bi quan (GSM8K single rec .283 từ solvejudge v1), vote làm
tệ hơn.

## Bảng Judge prec/rec (vòng 1, pipeline thật)

| | prec | rec |
|---|---|---|
| MATH fewshot | .486 | .645 |
| MATH vote | .392 | .519 |
| GSM8K fewshot | .653 | .479 |
| GSM8K vote | .590 | .261 |

## Kết luận

- **Vote KHÔNG đáng** ở cả hai task: tốn thêm call, acc không hơn (MATH .5133, GSM8K .6467 — đều
  thua hoặc ngang fewshot).
- **Few-shot có giá trị ở GSM8K** (+2.7 so single): cải thiện recall dừng-sớm, giữ câu đúng.
  Nhưng trên MATH không giúp (.5000 thấp hơn single).
- **Judge 1.5B vẫn là nút thắt.** Không biện pháp nào vỗ béo nó đáng kể. Hướng thật sự là **7B**
  (RESULTS: +14.0 trên MATH) hoặc **exec** (H33–H35, vướng rào cản H8 ở 1.5B).

## Giới hạn

- n=150 mỗi task, một lần chạy. GSM8K fewshot +2.7 nằm **dưới sàn nhiễu ~5 điểm** — đọc là
  "chưa phân biệt được" nhưng hướng đi (few-shot giúp recall dừng-sớm) có cơ chế rõ.
- Vote K=3 Judge tốn 2 call thêm/vòng — chi phí thật cao hơn số acc thể hiện.
- Chưa thử few-shot nhiều mẫu hơn (4–6 shots) — có thể cải thiện thêm.