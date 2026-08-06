# Vòng Planner: tổng hợp kết quả và kết luận

Tất cả đo trên Qwen2.5-1.5B-Instruct, greedy, GPU Kaggle T4. Mỗi kernel lưu **toàn bộ output
nguyên văn của mọi vai trên mọi câu** (`results_*/traces.json`), theo quy tắc mà `fc2f429` đặt
ra cho dự án.

> **Đọc con số ở đây với sàn nhiễu H13 trong đầu:** ở n ≤ 250, mọi hiệu ứng **< 5 điểm** đo một
> lần **không phải bằng chứng**. Các vòng dưới đây dùng 5 fold rời nhau và báo cáo số fold cùng
> dấu; chỉ hiệu ứng **5/5 fold cùng dấu** mới được coi là đã xác lập.

## Câu hỏi mở đầu

`de51589` phát hiện *"the Planner is doing the solving and the Solver is transcribing"* trên
GSM8K. Vòng này hỏi tiếp: hiện tượng đó có trên MATH không, nó có phải nguyên nhân gây lỗi
không, và sửa được không.

---

## Thí nghiệm 1 — Quan sát trực tiếp (`inspect_planner_kernel.py`)

3 nhánh Solver trên cùng plan: không plan (NP) · có plan (WP) · có plan + nhắc phải tự trình bày
(WPE). n = 8 mỗi task, đọc nguyên văn.

| | GSM8K | MATH |
|---|---|---|
| plan chứa sẵn đáp án đúng | 3/8 | **4/8** |
| Solver < 200 ký tự (có plan) | 4/8 | 3/8 |
| median lời giải: không plan → có plan | 851 → 245 | 1244 → 517 |

**Kết quả 1a — MATH cũng bị.** Planner trên MATH còn viết cả `\boxed{}`, tức trình bày đúng
định dạng nộp bài của Solver. Ví dụ (`f(-2)+f(-1)+f(0)`, gold `14/3`): plan kết bằng
`\[ \boxed{\frac{14}{3}} \]`; Solver có plan viết **68 ký tự**; Solver một mình viết 1191 ký tự.

**Kết quả 1b — chỉ số cũ bỏ sót.** `pt_m15` báo copycat MATH chỉ 6.5% và kết luận "trên MATH
Solver thực sự làm việc". Chỉ số đó so khớp theo **số cuối cùng**, trong khi đáp án MATH là
**biểu thức** (`14/3`, `p−q`, `90^\circ`). Đây là cùng loại lỗi mà `fc2f429` tìm ra độc lập.

**Kết quả 1c — nhắc bằng prompt vô tác dụng.** Nhánh WPE cho output **giống hệt từng ký tự** với
WP ở 4/8 ca GSM8K (16, 22, 18, 17 ký tự). Vấn đề nằm ở kiến trúc, không ở diễn đạt.

---

## Thí nghiệm 2 — Quy trách nhiệm câu sai (`analysis/blame_analysis.py`)

Dùng nhánh Solver-một-mình làm phản chứng cho từng câu. MATH n=30:

| nhóm | số câu |
|---|---|
| lỗi Planner (một mình đúng → có plan sai) | 3 |
| plan cứu được | 2 |
| **cả hai cùng thua** | **18** |
| cả hai đúng | 7 |

**Kết quả 2a — lỗi chủ yếu do Solver.** 18/30 ca cả hai cùng thua, trong đó 14 ca Solver tự tính
vẫn sai. Cân bằng ròng của Planner chỉ −1 câu.

**Kết quả 2b — plan hại theo cách riêng.** Ba ca lỗi Planner có ba cơ chế, và **cả ba đều có
Solver-một-mình làm đúng**:

| cơ chế | ví dụ |
|---|---|
| Planner kết luận sai, Solver chép mù | gold 225: plan bảo *"chỉ có 5 lính, không chọn nổi 4"* → `\boxed{0}`; một mình tính `C(5,4)·C(10,8)=225` ✅ |
| Planner tính lỗi rồi hết token, Solver nối tiếp | gold 28: `180−248 = −68°`, không thắc mắc góc âm; một mình ra 28 ✅ |
| Plan **đúng** nhưng Solver rút gọn mất `\boxed{}` | gold 5: `"The height of the cylinder is 5 cm."` (35 ký tự) |

Lời giải một mình dài hơn **4–58 lần**. ⇒ **plan không làm Solver lập luận sai, nó làm Solver
ngừng lập luận.**

---

## Thí nghiệm 3 — Few-shot chuyên biệt hoá vai (`fewshot_folds_kernel.py`, 5 fold × 30)

Chi tiết: [`FEWSHOT_ROLES.md`](FEWSHOT_ROLES.md).

**Kết quả 3a — few-shot đổi được hành vi, ở cả hai task:**

| chỉ số plan | GSM8K base→fs | MATH base→fs |
|---|---|---|
| chứa sẵn đáp án đúng | .420 → **.193** | .360 → **.160** |
| có `\boxed` | .033 → .000 | .453 → **.047** |
| số chữ số (median) | 28.4 → **7.6** | 56.4 → **8.0** |

Đây là thay đổi 3–7 lần, không phải vài điểm — đáng tin dù n nhỏ. Và Solver quay lại làm việc
(MATH n=30: `<200 ký tự` .433 → .033).

**Kết quả 3b — nhưng accuracy không nhúc nhích.** Không nhánh few-shot nào vượt sàn nhiễu; ứng
viên tốt nhất là few-shot solver trên MATH (+2.7đ, 4/5 fold) vẫn chứa 0 trong khoảng.

**Kết quả 3c — điều duy nhất đạt chuẩn 5/5 fold: bỏ plan đi thì tệ hơn −6 điểm (GSM8K).**
Plan **có ích thật**, dù nó chứa sẵn đáp án 42% số lần.

---

## Thí nghiệm 4 — Pipeline đầy đủ P→S→V→A (`fullpipe_rescue_kernel.py`, 5 fold × 30)

Chi tiết: [`VERIFIER_RESCUE.md`](VERIFIER_RESCUE.md). Ba thí nghiệm trên **chỉ chạy P→S**, nên
mọi câu bị tính sai ở đó có thể đã được sửa ở tầng sau. Vòng này chấm sau **từng tầng**.

| tầng | acc (GSM8K) |
|---|---|
| Solver một mình | .640 |
| P→S | **.700** |
| P→S→V | .693 |
| P→S→V→A | .700 |

`V_gain` −0.007 [−.133, +.067] 3/5 fold · `A_gain` +0.007 [−.033, +.033] 2/5 fold.

**Kết quả 4a — V và A không cộng thêm accuracy.** Cả hai chứa 0, dưới sàn nhiễu.

**Kết quả 4b — nhưng bên trong rất động:** Verifier **cứu 17 / phá 18** — động vào 23% số câu,
ròng bằng 0. Đúng "agent hỗn loạn" mà signed Shapley dự đoán. Chỉ nhìn accuracy sẽ kết luận sai
là "Verifier vô dụng".

**Kết quả 4c (quan trọng nhất) — Verifier gỡ lỗi ngoại lai tốt hơn lỗi năng lực nhiều:**

| nguồn gốc lỗi | số ca | V cứu được |
|---|---|---|
| **do PLAN gây ra** | 14 | **10 (71%)** |
| **do SOLVER tự gây** | 31 | **7 (23%)** |

Lỗi do plan là lỗi *ngoại lai* — Solver vốn làm được, chỉ bị dắt sai. Lỗi Solver tự gây là *giới
hạn năng lực* — một model 1.5B khác đọc lại cũng chịu.

⇒ **Tác hại của Planner đo ở tầng P→S là phóng đại**, vì pipeline thật gỡ được phần lớn.

**Kết quả 4d — một giả thuyết của tôi bị bác bỏ.** Tôi dự đoán: Solver chép → lời giải 17 ký tự
→ Verifier không có gì để kiểm. Dữ liệu ngược lại:

| trong các ca Solver sai | V cứu |
|---|---|
| lời giải **ngắn** (<200 ký tự) | **50%** |
| lời giải **dài** (≥200) | 24% |

Lời giải càng ngắn Verifier càng **dễ** cứu — vì không có lập luận sai nào để bị neo vào, buộc
phải tự giải lại. Khớp với `d23ef44` (*"cho verifier xem plan phá hỏng khả năng kiểm tra"*) và
hiệu ứng blind-verifier `e25cd0b`. **Cùng một cơ chế: context sai gây hại hơn thiếu context.**

---

## Kết luận chung

1. **Hiện tượng Planner giải hộ có ở cả GSM8K lẫn MATH** — trên MATH còn kèm `\boxed{}`. Chỉ số
   copycat cũ bỏ sót vì so khớp theo số trên tập có đáp án là biểu thức.
2. **Nhưng nó KHÔNG phải nguyên nhân chính của lỗi.** Plan chứa sẵn đáp án vẫn giúp +6 điểm so
   với không plan (5/5 fold), và khi nó dắt sai thì Verifier gỡ 71%.
3. **Sửa được hành vi, không mua được accuracy.** Few-shot làm plan hết chứa đáp án (giảm 3–7
   lần) và Solver trình bày trở lại — accuracy vẫn đứng yên trong nhiễu.
4. **Verifier là agent hỗn loạn thật**: 17 cứu / 18 phá. Ròng bằng 0 nhưng cơ chế bên trong rõ
   ràng — nó gỡ lỗi ngoại lai (71%) tốt hơn lỗi năng lực (23%) gấp ba.
5. **Càng ít context sai, verifier càng tốt** — lời giải ngắn được cứu 50% vs dài 24%. Kết quả
   thứ ba trong dự án chỉ về cùng hướng này.
6. **Ba lần chỉ thị bằng lời thất bại** (chỉ thị phủ định, lời nhắc, và một phần few-shot),
   trong khi thay đổi *cấu trúc* (bỏ plan, đổi context của verifier) thì luôn ra hiệu ứng đo
   được. Đây là điểm nhất quán nhất của vòng này.

## Giả thuyết chưa kiểm

Lợi ích +6 điểm của plan có thể đến từ việc **cho model thêm một lượt sinh trước khi chốt đáp
án**, chứ không phải từ chất lượng "kế hoạch". Phép thử sạch: thay plan bằng một lượt sinh
trung tính cùng độ dài (không phải kế hoạch) rồi xem +6 còn không.

## Giới hạn

- n = 150 mỗi vòng 5-fold; n = 8–30 cho phần quan sát. Sàn nhiễu ~5 điểm ở n ≤ 250.
- Các tỉ lệ cơ chế (71% / 23%, 50% / 24%) dựa trên 14–87 ca, **chưa có thanh sai số theo fold**.
  Chúng là đếm ca để đọc cơ chế, cần lặp ở n lớn hơn trước khi coi là số công bố.
- Thí nghiệm 4 mới chạy GSM8K. Theo bảng đảo dấu của dự án, MATH rất hay cho kết quả ngược.
- Toàn bộ ở 1.5B.

## Tái lập

```bash
cd shapley
TASK=gsm8k N=8   ACCOUNT=<acc> python deploy/orchestrate_inspect.py        # thí nghiệm 1
python analysis/blame_analysis.py                                          # thí nghiệm 2
TASK=math  N=150 NF=5 ACCOUNT=<acc> python deploy/orchestrate_fewshot_folds.py   # thí nghiệm 3
TASK=gsm8k N=150 NF=5 ACCOUNT=<acc> python deploy/orchestrate_rescue.py         # thí nghiệm 4
```
