# Aggregator: lỗi định dạng có phải nguyên nhân không? — KHÔNG, đây là lỗi chọn thật

Kiểm H20 (main `460c01f`) trên trace `aggk` của chúng ta, **trước khi** bỏ compute vào ORPO.
Tính offline bằng `analysis/agg_format_check.py`, không tốn GPU.

## Vì sao phải kiểm

main/H20 phát hiện `A_gain` trên MATH đi từ **−6.4** [−9,−4] (5/5 fold âm) lên **+1.0** [0,+2]
chỉ bằng một fallback miễn phí — khi Aggregator không xuất `\boxed{}` thì lấy đáp án của ứng
viên trước đó. Tức phần lớn "tác hại" của Aggregator là **artifact đo đạc**.

Nếu khoảng cách `agg5` (.460) vs `vote5` (.507) của ta cũng chủ yếu do format, thì train
preference để sửa **phán đoán** là nhắm sai chỗ — phải sửa **định dạng** mới đúng.

## Tỉ lệ định dạng

| | có `\boxed` | không boxed | không trích được gì |
|---|---|---|---|
| agg3 | 137/150 (**91.3%**) | 13 (8.7%) | 7 (4.7%) |
| agg5 | 139/150 (**92.7%**) | 11 (7.3%) | 7 (4.7%) |

Tỉ lệ xuất `\boxed` **cao hơn nhiều** so với con số .768 mà H20 gặp. Cấu hình của ta (nhiều ứng
viên độc lập, không có Verifier phía trước) ít bị lỗi format hơn.

Nhưng khi lỗi thì lỗi trọn vẹn: **100% số ca không có boxed đều bị chấm sai** (13/13 và 11/11).
Đó đúng là artifact — nhưng chỉ chiếm 7-9% số câu.

## Áp fallback và đo lại

| chính sách | acc | Δ vs S | fold |
|---|---|---|---|
| Solver một mình | .4133 | — | — |
| **vote5** (bỏ phiếu cơ học) | **.5067** | +0.093 | 4/5 |
| agg3 (như đã đo) | .4667 | +0.053 | **5/5** |
| agg3 + fallback ứng viên cuối | .4800 | +0.067 | **5/5** |
| **agg3 + fallback bỏ phiếu** | **.4933** | +0.080 | **5/5** |
| agg5 (như đã đo) | .4600 | +0.047 | 4/5 |
| agg5 + fallback ứng viên cuối | .4667 | +0.053 | 4/5 |
| agg5 + fallback bỏ phiếu | .4667 | +0.053 | 4/5 |

## Kết luận

**Fallback giúp, nhưng không đủ để đảo kết luận.** Bản tốt nhất — `agg3` + fallback bỏ phiếu —
đạt **.4933**, vẫn **thua `vote5` .5067**. Fallback thu hẹp khoảng cách từ 4.0 điểm xuống
1.3 điểm, nhưng không lật được thứ hạng.

**Khác với H20 vì lý do đo được:** ở cấu hình của ta tỉ lệ xuất `\boxed` là 91-93%, còn H20 gặp
76.8%. Ít lỗi format hơn ⇒ ít dư địa cho fallback hơn.

**Bằng chứng quyết định — lỗi nằm ở đâu:**

| agg5 | tỉ lệ sai |
|---|---|
| các ca **CÓ** `\boxed` | **70/139 = 50%** |
| các ca **KHÔNG** boxed | 11/11 = 100% |

Trong 81 ca sai, chỉ 11 ca do format. **70 ca còn lại (86%) là Aggregator xuất đáp án đúng định
dạng nhưng CHỌN SAI ứng viên.** Đây là lỗi phán đoán thật.

## Hệ quả cho kế hoạch ORPO

1. **ORPO vẫn nhắm đúng chỗ** — 86% lỗi là chọn sai, không phải format. Kết quả này *ủng hộ*
   hướng preference optimization thay vì bác bỏ nó.
2. **Nhưng phải thêm fallback vào mọi kernel sau này** — nó miễn phí và đáng +1.3 điểm. Không có
   lý do gì bỏ qua.
3. **Mốc so sánh không đổi**: `vote5` = .5067. Sau khi đã cho Aggregator lợi thế fallback tốt
   nhất mà nó vẫn thua, thì ORPO phải vượt .5067 mới có ý nghĩa. Trần oracle vẫn là **.673**.
4. `agg3` **tốt hơn** `agg5` một cách nhất quán (5/5 fold vs 4/5, và cao hơn ở mọi biến thể
   fallback). Nếu chạy ORPO nên dùng **K=3**, không phải K=5 — rẻ hơn mà tốt hơn.

## Giới hạn

- n = 150, MATH, 1.5B. Sàn nhiễu ~5 điểm: khoảng cách agg3-fallback (.4933) vs vote5 (.5067) là
  **1.3 điểm** — nằm sâu trong nhiễu, nên phát biểu chặt là *"không đo được khác biệt giữa hai
  cái"*, chứ không phải "vote5 chắc chắn hơn".
- Tỉ lệ 86% lỗi-chọn thì đáng tin hơn, vì nó là đếm ca trực tiếp chứ không phải hiệu của hai
  phép đo.
