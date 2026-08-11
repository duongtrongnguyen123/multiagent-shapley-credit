# Planner → iterate(Solve + Judge): đồng thuận có kiểm soát, budget giới hạn

Thay pipeline tuyến tính `P→S→V→A` bằng **Planner rồi lặp (Solve + Judge)** cho tới khi Judge
xác nhận đúng, hoặc hết budget. Giữ đúng spec: Judge **binary** (đúng/sai), re-solve **đổi
temperature** (không sampling nhiều), budget **tối đa 3 vòng**.

## Thiết kế

```
P         1 call   plan
loop i = 1..3:
  S_i     solve    v1 greedy (temp 1.0) · v2 temp 0.7 · v3 temp 0.4  (+ "solve again, carefully")
  J_i     judge    binary: 1 đúng / 0 sai
  if J_i == 1:  DỪNG, lấy pred(S_i) làm đáp án   (dừng sớm)
if 3 vòng đều sai:  lấy pred(S_3) làm đáp án
```

Baseline cùng bài (cùng seed): **S-alone** (1 call), **PSVA** (4 call).
MATH 1.5B & GSM8K 1.5B, n=150 mỗi task, 5 fold × 30.

---

## Kết quả chung

| nhánh | MATH acc | MATH calls | GSM8K acc | GSM8K calls |
|---|---|---|---|---|
| S-alone | .4067 | 1 | .6400 | 1 |
| PSVA | .4733 | 4 | .7000 | 4 |
| **loop** | **.5133** | **4.20** | **.6333** | **4.60** |

- **MATH: loop thắng cả hai baseline** — +10.7 so S-alone, +4.0 so PSVA với chi phí gần bằng (4.2 vs 4.0), thắng 5/5 fold.
- **GSM8K: loop THUA** — −0.7 so S-alone, **−6.7 so PSVA** (0/5 fold thắng), với nhiều call hơn (4.6).
- Hai task cho hai kết quả ngược chiều — **lần đảo dấu thứ tám của dự án.**

---

## Phân bố dừng & acc theo vòng dừng

### MATH
| vòng dừng | số câu | % | đáp án đúng | acc |
|---|---|---|---|---|
| stop@1 | 82 | 54.7% | 43 | **.524** |
| stop@2 | 46 | 30.7% | 28 | **.609** |
| stop@3 | 22 | 14.7% | 6 | **.273** |

### GSM8K
| vòng dừng | số câu | % | đáp án đúng | acc |
|---|---|---|---|---|
| stop@1 | 43 | 28.7% | 26 | **.605** |
| stop@2 | 94 | 62.7% | 66 | **.702** |
| stop@3 | 13 | 8.7% | 3 | **.231** |

Cả hai task: **stop@2 tốt nhất, stop@3 tệ nhất.** Re-solve một lần sau khi Judge bảo sai có ích
(.609/.702); nhưng re-solve 2 lần liên tiếp (stop@3) gần như vô ích (.273/.231) — model nhỏ không
tự sửa được sau 2 lần thất bại.

---

## Ma trận Judge vs Solver (đúng/sai thực tế) theo từng vòng

### MATH — VÒNG 1 (n=150)
| | J bảo ĐÚNG | J bảo SAI | Tổng |
|---|---|---|---|
| S đúng thật | 43 | 28 | 71 |
| S sai thật | 39 | 40 | 79 |
| Tổng | 82 | 68 | 150 |
Judge prec .524 · rec .606 · S-đúng-bị-chê 28 · S-sai-được-khen 39

### MATH — VÒNG 2 (n=150)
| | J bảo ĐÚNG | J bảo SAI | Tổng |
|---|---|---|---|
| S đúng thật | 71 | 3 | 74 |
| S sai thật | 57 | 19 | 76 |
| Tổng | 128 | 22 | 150 |
Judge prec .555 · rec .959 · S-đúng-bị-chê 3 · S-sai-được-khen 57

### MATH — VÒNG 3 (n=150)
| | J bảo ĐÚNG | J bảo SAI | Tổng |
|---|---|---|---|
| S đúng thật | 75 | 2 | 77 |
| S sai thật | 61 | 12 | 73 |
| Tổng | 136 | 14 | 150 |
Judge prec .551 · rec .974 · S-đúng-bị-chê 2 · S-sai-được-khen 61

### GSM8K — VÒNG 1 (n=150)
| | J bảo ĐÚNG | J bảo SAI | Tổng |
|---|---|---|---|
| S đúng thật | 14 | 70 | 84 |
| S sai thật | 29 | 37 | 66 |
| Tổng | 43 | 107 | 150 |
Judge prec .326 · rec .167 · S-đúng-bị-chê **70** · S-sai-được-khen 29

### GSM8K — VÒNG 2 (n=150)
| | J bảo ĐÚNG | J bảo SAI | Tổng |
|---|---|---|---|
| S đúng thật | 52 | 2 | 54 |
| S sai thật | 85 | 11 | 96 |
| Tổng | 137 | 13 | 150 |
Judge prec .380 · rec .963 · S-đúng-bị-chê 2 · S-sai-được-khen **85**

### GSM8K — VÒNG 3 (n=150)
| | J bảo ĐÚNG | J bảo SAI | Tổng |
|---|---|---|---|
| S đúng thật | 53 | 0 | 53 |
| S sai thật | 92 | 5 | 97 |
| Tổng | 145 | 5 | 150 |
Judge prec .366 · rec 1.000 · S-đúng-bị-chê 0 · S-sai-được-khen **92**

---

## Insight

**1. Judge không "chốt" được — nó là một bộ lọc rò rỉ.**
Precision ở vòng 1 chỉ .52 (MATH) / .33 (GSM8K): **cứ 2–3 câu Judge bảo đúng thì 1–2 câu thật ra
sai**. Nó phát hiện đúng hầu hết câu đúng thật (recall cao ở vòng 2+), nhưng **false positive
lớn dần theo vòng** (39→57→61 MATH; 29→85→92 GSM8K). Vòng sau càng ít câu dừng sớm (câu dễ đã
dừng ở vòng 1), phần còn lại chủ yếu sai → Judge "đúng" khi nói sai chúng.

**2. Vì sao MATH thắng còn GSM8K thua — câu trả lời nằm ở vòng 1.**
- MATH vòng 1: Judge bảo đúng 82 câu, **43 đúng (acc .524)** — ít lỗi false-pos hơn, và dừng sớm
  giữ được câu đúng.
- GSM8K vòng 1: **Judge bảo sai 70 câu S-thật-đúng** (false negative). Nó đẩy 70 câu đúng đi
  re-solve → đa số vẫn đúng nhưng **tốn thêm call**, và vòng 2 Judge lại khen sai 85 câu (false
  pos cao). Ròng: loop −1 so S-alone, −10 so PSVA.

**3. Điểm nghẽn của toàn hệ là Judge, không phải Solver.**
Solver greedy đúng nhiều (GSM8K 84/150, MATH 71/150). Judge không nhận ra → MATH sai nửa số câu
đúng (28/71), GSM8K gần như toàn bộ (70/84). **Tăng chất lượng Judge (chứ không phải thêm vòng
solve) mới là đòn bẩy.** Một Judge tốt hơn (vd nhiều sample Judge vote, hay Judge có exec) sẽ
vừa tăng recall vòng 1 vừa giảm false-pos.

**4. Re-solve đổi temperature có tác dụng thật ở lần 1, hết tác dụng ở lần 2.**
stop@2 (.609/.702) > stop@1 (.524/.605) — re-solve một lần tạo cơ hội mới. stop@3 (.273/.231) cho
thấy lần re-solve thứ hai gần như vô dụng trên model nhỏ (khớp H41: thêm độ sâu không theo độ khó).

**5. Liên hệ H41 (giả thuyết trần bị bác).**
H41 nói thêm model/lượt không giúp theo độ khó. Loop MATH thắng **không phải vì độ khó** mà vì
**Judge là tín hiệu dừng có thông tin** (prec ~.52) — điều H41 không đo. Nhưng GSM8K cho thấy
tín hiệu đó không đáng tin khi model đã tự tin đúng: Judge GSM8K quá bi quan (prec .33), tự phá
các câu đúng. **Kết luận: loop giúp khi Judge đủ chuẩn (MATH), hại khi Judge lệch (GSM8K).**

---

## Giới hạn

- n=150 mỗi task, một lần chạy. Δ MATH loop−PSVA +4.0 nằm **quanh sàn nhiễu ~5 điểm**; 5/5 fold
  thắng là tín hiệu nhưng cần tái lập. GSM8K −6.7 so PSVA rõ hơn.
- Judge chạy **toàn bộ n câu mỗi vòng** (kể cả câu đã dừng) — vòng 2/3 tốn call thừa. Tối ưu hoá
  chỉ judge `todo` sẽ giảm calls mà không đổi acc.
- Chưa chạy 7B; chưa tăng chất lượng Judge (một trong các hướng tiếp theo).

## Hướng tiếp theo (ưu tiên)
1. **Nâng chất lượng Judge** (sample Judge vote, hay Judge có exec) — vì phân tích chỉ ra Judge là
   điểm nghẽn, không phải Solver hay số vòng.
2. **Judge chỉ `todo`** ở vòng 2/3 để cắt call.
3. Tái lập MATH ở n lớn hơn trước khi khẳng định loop thắng PSVA.