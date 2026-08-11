# Solve+Judge loop — MATH 1.5B (n=150, 5 fold × 30)

Pipeline: `Planner → iterate(Solve + Judge)` — Judge binary, re-solve đổi temperature
(1.0 → 0.7 → 0.4), budget 3 vòng, dừng sớm khi Judge bảo đúng, hết budget lấy S₃.
Chi tiết thiết kế & so sánh GSM8K ở [`SOLVEJUDGE.md`](SOLVEJUDGE.md).

## Kết quả

| nhánh | mean acc | min/max | calls/câu |
|---|---|---|---|
| S-alone (1 call) | .4067 | .267/.567 | 1 |
| PSVA (4 call) | .4733 | .367/.667 | 4 |
| **loop (S+J)** | **.5133** | .367/.700 | **4.20** |

- **loop − S-alone = +10.7 điểm** (thắng 5/5 fold)
- **loop − PSVA = +4.0 điểm**, chi phí gần tương đương (4.2 vs 4.0 call) → **rẻ hơn mà cao hơn**

## Phân bố dừng & acc theo vòng dừng

| vòng dừng | số câu | % | đáp án đúng | acc |
|---|---|---|---|---|
| stop@1 | 82 | 54.7% | 43 | **.524** |
| stop@2 | 46 | 30.7% | 28 | **.609** |
| stop@3 | 22 | 14.7% | 6 | **.273** |

## Ma trận Judge vs Solver (đúng/sai thực tế) theo từng vòng

### VÒNG 1 (n=150, toàn bộ)
| | J bảo ĐÚNG | J bảo SAI | Tổng |
|---|---|---|---|
| S đúng thật | 43 | 28 | 71 |
| S sai thật | 39 | 40 | 79 |
| Tổng | 82 | 68 | 150 |
Judge prec .524 · rec .606 · S-đúng-bị-chê **28** · S-sai-được-khen **39**

### VÒNG 2 (n=150 — Judge chấm tất cả, chỉ 46 câu thực sự còn lặp)
| | J bảo ĐÚNG | J bảo SAI | Tổng |
|---|---|---|---|
| S đúng thật | 71 | 3 | 74 |
| S sai thật | 57 | 19 | 76 |
| Tổng | 128 | 22 | 150 |
Judge prec .555 · rec **.959** · S-đúng-bị-chê 3 · S-sai-được-khen 57

### VÒNG 3 (n=150)
| | J bảo ĐÚNG | J bảo SAI | Tổng |
|---|---|---|---|
| S đúng thật | 75 | 2 | 77 |
| S sai thật | 61 | 12 | 73 |
| Tổng | 136 | 14 | 150 |
Judge prec .551 · rec **.974** · S-đúng-bị-chê 2 · S-sai-được-khen 61

## Insight (MATH)

1. **Judge precision chỉ .52** ở vòng 1 — gần nửa số câu Judge "chốt đúng" thật ra S sai
   (39 false-pos). Loop vẫn thắng vì net rescue +16 so S-alone (+6 so PSVA).
2. **Recall tăng theo vòng (.61→.96→.97)** nhưng đó là hệ quả chọn lọc: câu dễ dừng sớm ở vòng 1,
   vòng sau chỉ còn câu khó (S sai đa số) → Judge "đúng" khi nói sai chúng. Không phải Judge giỏi
   hơn.
3. **stop@2 (.609) > stop@1 (.524) > stop@3 (.273)** — re-solve 1 lần tạo cơ hội mới; lần 2 gần như
   vô ích. Điểm nghẽn là Judge, không phải số vòng.

## Giới hạn

- n=150, một lần chạy. Δ loop−PSVA +4.0 quanh sàn nhiễu ~5 điểm; 5/5 fold thắng cần tái lập ở n lớn.
- Judge chấm cả n câu mỗi vòng (kể cả đã dừng) — tối ưu chỉ judge `todo` sẽ cắt call không đổi acc.