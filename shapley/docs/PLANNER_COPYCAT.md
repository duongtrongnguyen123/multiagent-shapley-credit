# Vì sao Planner giải luôn đáp án còn Solver chỉ chép lại?

Quan sát trực tiếp trên GSM8K, Qwen2.5-1.5B, greedy, n=8, dùng **đúng prompt của
`pipeline/template.py`** đang chạy trong dự án. Kernel: `pipeline/inspect_planner_kernel.py`.
Dữ liệu thô: `results_inspect/gsm8k/traces.json`.

> Cỡ mẫu n=8 chỉ đủ để **quan sát định tính** (đọc nguyên văn). Mọi con số tỷ lệ dưới đây
> KHÔNG dùng để kết luận hiệu ứng — xem cảnh báo sàn nhiễu ở H13 (`PREREGISTRATION.md` #12).

## 1. Prompt đang dùng

```python
PLAN_SYS  = ("You are a math planning assistant. Read the problem and give a concise "
             "numbered plan of the steps needed. Do NOT compute the final answer.")
SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
             "End with a line: 'The answer is <number>'.")
```
Solver nhận: `<đề bài>` + `"\n\nSuggested plan:\n"` + `<plan>`.

## 2. Bằng chứng nguyên văn

**Câu 2** — *"A robe takes 2 bolts of blue fiber and half that much white fiber. How many
bolts in total?"* (đáp án 3)

Planner — dù bị bảo *"Do NOT compute the final answer"*:
```
1. Determine the amount of blue fiber required: 2 bolts.
2. Calculate the amount of white fiber required: \( \frac{1}{2} \times 2 = 1 \) bolt.
3. Add the amounts together to find the total number of bolts: \( 2 + 1 = 3 \) bolts.
```
→ Bước 3 **là đáp số cuối cùng**. Kế hoạch đã giải xong bài toán.

Solver khi **có** plan (16 ký tự — toàn bộ output):
```
The answer is 3.
```
Solver khi **không** có plan (451 ký tự):
```
To find the total number of bolts needed for the robe, we start by determining how much
white fiber is required.
...
\[ \text{Total bolts} = 2 (\text{blue}) + 1 (\text{white}) = 3 \text{ bolts} \]
```
→ Cùng một model, cùng prompt SOLVE. Chỉ khác: **có plan trong input hay không**.

## 3. Độ dài lời giải Solver (ký tự), n=8

| câu | gold | plan | NP (không plan) | WP (có plan) | WPE (có plan + nhắc) |
|---|---|---|---|---|---|
| 1 | 18 | 516 | 661 | 1066 | 633 |
| 2 | 3 | 228 | 451 | **16** | **16** |
| 3 | 70000 | 658 | 854 | **22** | **22** |
| 4 | 540 | 351 | 849 | **18** | **18** |
| 5 | 20 | 878 | 1058 | **17** | **17** |
| 6 | 64 | 454 | 911 | 469 | 636 |
| 7 | 260 | 581 | 633 | 695 | 715 |
| 8 | 160 | 319 | 1098 | 1223 | 1686 |

- Solver viết dưới 60 ký tự: **0/8 khi không có plan** → **4/8 khi có plan**.
- Median: 851 (NP) → 245 (WP). Plan có mặt thì Solver ngừng trình bày.
- `plan_contains_correct_answer` = **0.375** (3/8 kế hoạch chứa sẵn đáp án đúng).

## 4. Ba nguyên nhân

**(a) "Do NOT compute" là chỉ thị phủ định, và với số học nó tự mâu thuẫn.**
Muốn nêu bước cho bài GSM8K, model phải viết ra chính phép tính đó (`2 + 1 = 3`). Ranh giới
giữa "nêu bước" và "làm bước" không tồn tại ở loại bài này. Model 1.5B không tuân thủ nổi.

**(b) Prompt không có ràng buộc định dạng nào cấm plan chứa số.**
`"concise numbered plan"` không cấm viết biểu thức, dấu `=`, hay kết quả. Muốn plan thật sự
trống đáp án thì phải ràng buộc kiểu *"describe each step in words only; write no arithmetic
expression and no numeric result"*.

**(c) Nhãn `"Suggested plan:"` biến Solver thành người chép.**
Solver bị bảo "solve step by step" nhưng nhận sẵn văn bản đã chứa đáp án. Đường ngắn nhất
thỏa mãn cả hai ràng buộc là chép kết luận rồi in `The answer is X`. Không có gì trong prompt
phạt hành vi đó.

## 5. Nhắc bằng prompt KHÔNG cứu được

Nhánh WPE thêm câu *"Even if a plan is provided, you must still write out every calculation
yourself; do not just restate the plan's answer."*

Kết quả: 4 câu bị chép (2,3,4,5) có output **giống hệt từng ký tự** với WP — 16, 22, 18, 17 ký
tự. Câu nào Solver đã chép thì lời nhắc không đổi được gì; nó chỉ làm dài thêm những câu vốn
đã tự giải (câu 1: 1066→633, câu 8: 1223→1686 — đổi cả hai chiều, tức là nhiễu).

→ **Đây là vấn đề kiến trúc, không phải vấn đề diễn đạt prompt.**

## 6. MATH cũng bị — và ở dạng nặng hơn về nội dung

Chạy cùng kernel với `TASK=math`, n=8 (`results_inspect/math/`):

| | GSM8K | MATH |
|---|---|---|
| plan chứa sẵn đáp án đúng | 3/8 (0.375) | **4/8 (0.50)** |
| Solver < 200 ký tự — không plan | 0/8 | 0/8 |
| Solver < 200 ký tự — có plan | 4/8 | **3/8** |
| median lời giải Solver: không plan → có plan | 851 → 245 | **1244 → 517** |
| median độ dài plan | 485 | **1117** |

Trên MATH, Planner **viết hẳn `\boxed{}`** — tức là nó không chỉ tính ra đáp số mà còn trình
bày theo đúng định dạng nộp bài của Solver. Ví dụ câu 3, đề *"If f(x)=(3x-2)/(x-2), what is
f(-2)+f(-1)+f(0)?"*:

Planner (phần cuối của 991 ký tự):
```
So, f(-2) + f(-1) + f(0) = 6/3 + 5/3 + 3/3 = 14/3
Thus, the value of f(-2) + f(-1) + f(0) is:
\[ \boxed{\frac{14}{3}} \]
```
Solver có plan — **toàn bộ** output, 68 ký tự:
```
The value of \( f(-2) + f(-1) + f(0) \) is \(\boxed{\frac{14}{3}}\).
```
Solver không plan: 1191 ký tự, tự đánh giá hàm tại từng điểm rồi cộng.

**Khác biệt so với GSM8K là về mức độ, không phải về bản chất.** Trên MATH kế hoạch dài hơn
(1117 vs 485 ký tự) nên tỷ lệ câu bị rút gọn thấp hơn chút, nhưng **tỷ lệ plan chứa đáp án
lại CAO hơn** (0.50 vs 0.375). Bài nào Planner giải trọn được thì Solver chép trọn.

Điều này **không mâu thuẫn** với `pt_m15` (IDEAS.md, n=200: copycat GSM8K 61% vs MATH 6.5%) —
chỉ số ở đó là "đáp án Solver == số cuối cùng của plan", một phép so khớp theo *số*. Trên MATH
đáp án thường là biểu thức (`14/3`, `p-q`, `90^\circ`) nên phép so theo số bỏ sót phần lớn ca
chép. Đọc nguyên văn thì thấy việc chép vẫn diễn ra.

Nguyên nhân gốc chung: GSM8K chỉ cần 2-3 phép tính nên **kế hoạch chính là lời giải**; MATH
thì kế hoạch dài hơn nhưng model vẫn giải trọn bài ngay trong lúc "lập kế hoạch". Cả hai ô,
vai Planner đều không có không gian tồn tại độc lập.

## 7. Hệ quả

1. **Trên GSM8K, "Planner→Solver" thực chất là "Planner giải, Solver ký tên".** Mọi φ Shapley
   đo trên cấu hình có P=1 ở GSM8K đều đang đo một pipeline khác với pipeline được mô tả.
2. Điều này giải thích tại sao Planner GSM8K có φ ≈ 0 hoặc âm: nó không "lười", nó **chiếm
   việc** của Solver — và làm kém hơn vì bị bảo đừng tính nên tính vội (xem câu 1: plan nhầm
   "3 quả/ngày × 7 ngày" thành 21 quả/tuần rồi kéo Solver đi sai theo).
3. **MATH cũng bị** (mục 6): 50% kế hoạch chứa sẵn đáp án đúng, Planner viết cả `\boxed{}`.
   Nên thí nghiệm debate-planner (nhánh `duc`) thực chất đang so *chất lượng lời giải của
   Planner*, không phải *chất lượng kế hoạch* — cần nói rõ điều này khi diễn giải kết quả.

## 8. Cách chạy lại

```bash
cd shapley
TASK=gsm8k N=8 python deploy/orchestrate_inspect.py   # hoặc TASK=math / TASK=both
KAGGLE_API_TOKEN=... kaggle kernels output <user>/inspect-planner-gsm8k -p results_inspect/gsm8k
```
