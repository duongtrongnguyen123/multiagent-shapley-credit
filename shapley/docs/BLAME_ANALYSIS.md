# Câu sai là lỗi của ai — Planner hay Solver?

Phân tích bằng `analysis/blame_analysis.py` trên trace thô đã tải
(`results_fewshot/math`, `results_inspect/{math,gsm8k}`).

## Cách quy trách nhiệm

Dùng nhánh **NP** (Solver làm một mình, không thấy plan) làm phản chứng cho từng câu:

| Solver một mình | Có plan | Kết luận |
|---|---|---|
| ĐÚNG | SAI | **LỖI PLANNER** — plan phá lời giải vốn đúng |
| SAI | ĐÚNG | **PLAN CỨU ĐƯỢC** |
| SAI | SAI | cả hai cùng thua (bài khó / Solver yếu) |
| ĐÚNG | ĐÚNG | không sao |

> n = 8–30 câu. Đây là **đếm ca cụ thể để đọc nguyên nhân**, không phải ước lượng tỉ lệ.
> Sàn nhiễu H13 ≈ 5 điểm ở n ≤ 250 — mọi tỉ lệ dưới đây không dùng để so hiệu ứng.

## Kết quả (MATH, n=30)

| nhóm | số câu |
|---|---|
| LỖI PLANNER | **3** |
| PLAN CỨU ĐƯỢC | 2 |
| cả hai cùng thua | **18** |
| cả hai đúng | 7 |

**Cân bằng ròng của Planner: −1 câu** (cứu 2, phá 3).

Phần lớn câu sai (**18/30**) là **cả hai cùng thua** — tức Solver tự làm cũng sai. Trong 18
câu đó, chỉ 4 câu do Solver chép đáp án sai của plan; 14 câu còn lại Solver tự tính và vẫn sai.

**⇒ Nguyên nhân sai chủ yếu KHÔNG phải Planner, mà là năng lực Solver trên bài khó.**

Nhưng Planner **không vô can**: khi kế hoạch để lộ đáp án sai (21/30 câu), Solver **chép theo
24%** số ca và chỉ bắt được lỗi 2 lần.

## Ba ca LỖI PLANNER — nguyên văn

### Ca 1 (câu 30, gold 225) — Planner kết luận sai, Solver chép mù

Đề: chọn 4 lính thượng lưu từ 5, và 8 lính hạ lưu từ 10.

Plan kết luận:
```
Since there are only 5 upper class soldiers available, it is impossible to form
a battalion with exactly 4 upper class soldiers.
Conclusion: The number of different battalions is \( \boxed{0} \).
```
Sai logic sơ đẳng: chọn 4 từ 5 hoàn toàn được (`C(5,4)=5`).

Solver **có plan** (450 ký tự): lặp lại nguyên si "không đủ lính, không lập được tiểu đoàn" → **0**.
Solver **một mình** (2020 ký tự): `C(5,4) × C(10,8) = 5 × 45 = 225` → **đúng**.

### Ca 2 (câu 19, gold 28) — Planner tính lỗi giữa chừng, Solver nối tiếp cái sai

Plan tính ra `248° + ∠ABC = 180°` (đã sai từ trước), rồi bị cắt ngang vì hết token.

Solver **có plan** (162 ký tự) — nối thẳng vào chỗ plan dừng:
```
∠ABC = 180° − 248° = −68°     →  \boxed{-68}
```
Không hề thắc mắc góc âm là vô lý. Solver **một mình** (1237 ký tự): `x = 56/2 = 28` → **đúng**.

### Ca 3 (câu 14, gold 5) — plan đúng, nhưng Solver ngừng làm việc

Plan giải trọn ra `\boxed{5}` (đúng). Solver có plan viết **35 ký tự**:
`"The height of the cylinder is 5 cm."` — không có `\boxed{}` nên **bộ chấm không bắt được
đáp án** → tính là sai dù nội dung đúng.

Đây là dạng lỗi thứ ba: plan đúng nhưng **làm Solver mất luôn định dạng nộp bài**.

## Ba cơ chế hỏng khác nhau

| # | Cơ chế | Ví dụ | Solver một mình |
|---|---|---|---|
| 1 | Planner **kết luận sai**, Solver chép mù | câu 30: `0` thay vì `225` | đúng (2020 ký tự) |
| 2 | Planner **tính lỗi giữa chừng**, Solver nối tiếp | câu 19: `−68°` | đúng (1237 ký tự) |
| 3 | Planner **đúng** nhưng Solver rút gọn mất định dạng | câu 14 | đúng (645 ký tự) |

Điểm chung cả ba: **Solver một mình đều làm đúng**, và lời giải một mình **dài hơn 4–58 lần**.
Plan không làm Solver sai vì lập luận kém — nó làm Solver **ngừng lập luận**.

## So sánh hai benchmark

| | MATH n=30 | MATH n=8 | GSM8K n=8 |
|---|---|---|---|
| lỗi Planner | 3 | 0 | 1 |
| plan cứu được | 2 | 2 | 2 |
| ròng | **−1** | +2 | +1 |
| Solver chép plan sai | 24% | 0% | 0% |

Ở n=8 Planner có vẻ có lợi (+2, +1), ở n=30 thì thành âm (−1). **Chính là hiện tượng sàn nhiễu
H13**: cùng một đại lượng, đổi bộ bài thì đổi dấu. Không được kết luận dấu của cân bằng ròng
từ những n này.

## Few-shot có sửa được không?

Few-shot planner so với plan gốc (MATH n=30): **sửa được 4 câu, làm hỏng 3 câu → ròng +1**.

Nằm trong nhiễu, chưa kết luận được về accuracy. Nhưng cơ chế thì rõ: few-shot làm plan không
còn chứa đáp án (`has_boxed` .467 → .067), nên **cơ chế hỏng số 1 và 3 không còn đất diễn** —
Solver không có gì để chép, buộc phải tự giải (median 370 → 1379 ký tự).

Kernel `fewshot-folds-{math,gsm8k}` (5 fold) đang chạy để có thanh sai số cho phần accuracy.

## Kết luận

1. **Câu sai chủ yếu do Solver yếu**, không do Planner: 18/30 ca cả hai cùng thua, trong đó
   14 ca Solver tự tính vẫn sai.
2. **Nhưng Planner gây hại theo một cách riêng**: nó không làm Solver lập luận sai, nó làm
   Solver **ngừng lập luận** rồi chép. 3/3 ca lỗi planner đều có Solver-một-mình làm đúng.
3. **Rủi ro tập trung ở ca plan để lộ đáp án sai** — Solver chép theo 24%, chỉ bắt lỗi 2 lần.
   Đây chính là điểm mà few-shot planner (plan không chứa số) tấn công trực tiếp.
