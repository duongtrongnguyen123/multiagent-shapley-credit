# Phân bổ tín nhiệm (Shapley Credit Assignment) cho hệ thống multi-agent LLM

Nghiên cứu đo **mức đóng góp thực sự của từng vai trò (agent)** trong một pipeline
multi-agent **Planner → Solver → Verifier → Aggregator** giải toán, bằng **giá trị
Shapley chính xác** trên toàn bộ 16 liên minh (coalition) vai trò. Toàn bộ suy luận
chạy song song trên **Kaggle GPU (T4)**, mỗi liên minh một tài khoản.

> Câu hỏi cốt lõi: trong một đội agent, ai thực sự đóng góp, ai "ăn theo" (free-rider),
> và giá trị của mỗi vai trò thay đổi thế nào theo **độ khó bài toán** và **năng lực
> model**?

---

## 1. Tổng quan phương pháp

- **4 vai trò (agent):**
  - **Planner** — đọc đề, lập dàn ý các bước, *không* tính đáp số.
  - **Solver** — giải từng bước, xuất đáp án cuối (`\boxed{}` hoặc "The answer is X").
  - **Verifier** — nhận lời giải của Solver, kiểm tra từng bước, sửa nếu sai.
  - **Aggregator** — nhận các lời giải ứng viên, đối chiếu và chọn đáp án cuối.
- **Giá trị Shapley:** chạy cả 2⁴ = 16 liên minh vai trò trên *cùng* tập câu hỏi;
  `v(S)` = độ chính xác của pipeline khi chỉ bật các vai trò trong tập `S`.

  `φ_i = Σ_{S ⊆ N\{i}} |S|!·(n−|S|−1)!/n! · (v(S∪{i}) − v(S))`

- **Model:** Qwen2.5-1.5B-Instruct cho mọi vai trò (các vòng "capacity" nâng một vai
  trò lên 7B). Giải mã greedy. Dữ liệu và model đều mount từ Kaggle (không cần Internet).
- **Hạ tầng:** mỗi liên minh đẩy thành 1 kernel Kaggle riêng, xác thực bằng
  `KAGGLE_API_TOKEN` của từng tài khoản; thu kết quả bằng `sync_once.py`.

---

## 2. Kết quả chính

**GSM8K (dễ) — đồng nhất 1.5B (N=1319):**

| Vai trò | Shapley φ | Nhận xét |
|---|---|---|
| Solver | +0.252 | trụ cột |
| Verifier | +0.252 | **ngang Solver** — kiểm tra đáng giá như giải |
| Aggregator | +0.190 | hữu ích |
| Planner | −0.014 | **âm** — free-rider, gây "negative transfer" −12 điểm |

**Thí nghiệm năng lực (nâng 1 vai trò lên 7B):**
- **Planner 7B:** φ lật từ −0.023 → **+0.055** ⇒ hại của planner là do *năng lực yếu*,
  không phải bản chất.
- **Verifier 7B:** φ +0.269 → **+0.462**, độ chính xác 0.71 → 0.87 ⇒ verifier là vai
  trò **nhạy năng lực nhất** (+26 điểm so với +7 của planner).

**MATH-500 (khó) — đồng nhất 1.5B (N=500): THỨ HẠNG ĐẢO NGƯỢC**

| Vai trò | MATH φ | (GSM8K) |
|---|---|---|
| **Aggregator** | **+0.148** | +0.190 (hạng 3) → **lên #1** |
| Solver | +0.141 | +0.252 |
| Verifier | +0.141 | +0.252 → **mất ngôi đầu** |
| Planner | +0.017 | −0.014 → **hết âm** |

**Bài học:** "đầu tư vào Verifier" chỉ đúng với GSM8K, **không** tổng quát. Với bài
khó, verifier yếu không sửa nổi lời giải dài/sai ⇒ bão hòa; **Aggregator** (chọn giữa
nhiều lời giải đa dạng) mới quan trọng nhất. Giá trị vai trò phụ thuộc **cả độ khó bài
toán lẫn năng lực model**.

Chi tiết đầy đủ: [`shapley/FINDINGS.md`](shapley/FINDINGS.md).

---

## 3. Cấu trúc repo

```
kernel/                       # kernel GSM8K inference ban đầu (Qwen 1.5B)
shapley/
  template.py                 # pipeline GSM8K, tham số hoá theo mặt nạ vai trò (P,S,V,A)
  template_math.py            # pipeline MATH-500 (chấm đáp án \boxed{} LaTeX)
  template_role7b.py          # phiên bản nâng 1 vai trò lên 7B (GSM8K)
  template_math_role7b.py     # phiên bản nâng 1 vai trò lên 7B (MATH)
  orchestrate*.py             # sinh 16 (hoặc 8) liên minh và deploy mỗi cái 1 tài khoản
  sync_once.py                # thu kết quả 1 lượt (đồng bộ, KHÔNG dùng vòng lặp nền)
  shapley.py / shapley_role7b.py   # tính Shapley
  bootstrap.py / bootstrap_het.py  # khoảng tin cậy bằng bootstrap
  regrade_math.py             # chấm lại MATH offline từ preds.json
  FINDINGS.md                 # báo cáo kết quả (tiếng Anh)
  WORK_SPLIT.md               # phân công chi tiết + trình tự tài khoản
```

> **Bảo mật:** `accounts.txt`, `manifest*.json`, `monitor.sh` chứa token Kaggle nên đã
> bị `.gitignore` — **không bao giờ commit token**. Các thư mục `results_*/`,
> `kernels_*/` là dữ liệu tái sinh, cũng được bỏ qua.

---

## 4. Hướng dẫn chạy

Cần: Kaggle CLI ≥ 2.x, file `accounts.txt` (mỗi dòng `USERNAME TOKEN`).

```bash
# 1) Vòng nền: deploy 16 liên minh, mỗi liên minh 1 tài khoản
ROUND=m1 N_EVAL=300 python orchestrate_math.py

# 2) Thu kết quả (chạy tiền cảnh, lặp lại tới khi REMAINING 0)
ROUND=m1 python sync_once.py     # gọi lại vài lần mỗi ~10-15 phút

# 3) Chấm lại (chỉ MATH) rồi tính Shapley + khoảng tin cậy
ROUND=m1 python regrade_math.py
ROUND=m1 python shapley.py
ROUND=m1 python bootstrap.py

# Vòng capacity (nâng 1 vai trò lên 7B): BIG ∈ {P,S,V,A}
BIG=A ROUND=mA N_EVAL=300 python orchestrate_math_role7b.py
ROUND=mA python sync_once.py
BIG=A ROUND=mA python shapley_role7b.py
```

**Lưu ý quan trọng:**
- **MATH chậm hơn GSM8K ~7 lần** (mỗi liên minh 2 tầng mất ~60-70 phút ở N=500) ⇒ dùng
  **N=300** cho các vòng capacity.
- **KHÔNG dùng vòng lặp nền** để poll — chúng bị kill khi đổi lượt; luôn gọi
  `sync_once.py` đồng bộ.
- Kernel Kaggle: slug lấy từ `title` (không phải `id`); đường dẫn mount dataset ≠ ref
  (nên dùng `glob` `/kaggle/input/**`); ép GPU T4 bằng `machine_shape="NvidiaTeslaT4"`.

---

## 5. Phân công công việc (đội 4 người)

Vòng nền `m1` (MATH đồng nhất 1.5B) **đã xong** — đây là điều kiện cho mọi vòng
capacity. Vì Aggregator lên #1 trên MATH, **vòng 7B-Aggregator là ưu tiên cao nhất**.

| Người | Nhiệm vụ | Lệnh chính | Vì sao |
|---|---|---|---|
| **Người 1 · Nguyên** | Vòng **7B-Aggregator** (`mA`) + tổng hợp cuối | `BIG=A ROUND=mA N_EVAL=300 python orchestrate_math_role7b.py` | Kiểm chứng dự đoán: Aggregator có thống trị MATH như Verifier thống trị GSM8K? |
| **Người 2** | Vòng **7B-Verifier** (`mV`) + **7B-Solver** (`mS`) | `BIG=V ROUND=mV N_EVAL=300 python orchestrate_math_role7b.py` | Nâng năng lực có cứu được Verifier trên bài khó, hay vẫn bão hòa? |
| **Người 3** | Vòng **7B-Planner** (`mP`) + **7B-Aggregator dự phòng** | `BIG=P ROUND=mP N_EVAL=300 python orchestrate_math_role7b.py` | Planner hết âm trên MATH — 7B có biến "lập dàn ý" thành lợi thế thật? |
| **Người 4** | Nhánh **Coding** (độc lập) | tự dựng kernel Coder + MBPP+ (có chạy unit test) | Verifier *có căn cứ* (chạy test) + phần thưởng *phân mức* — kết quả mới nhất |

**Trình tự (chỉ có 19 tài khoản, chạy tối đa 2 vòng cùng lúc):**
1. **Đợt A (ngay):** Người 1 `mA` (8 tk) + Người 2 `mV` (8 tk).
2. **Đợt B:** Người 3 `mP` + Người 2 `mS` khi tài khoản rảnh.
3. **Người 4** chạy nhánh coding độc lập.

**Quy tắc chung:** dùng `N_EVAL=300`; **bỏ tài khoản `truongdv006`** (đã bị khoá),
dự phòng `khunht`/`dnglethnh`/`tbmdemi`; báo nhau trước khi chạy để không trùng tài
khoản. Kết quả mỗi người: `shapley_<round>_results.json` + 1 dòng trong bảng
role×capacity chung (Người 1 tổng hợp). Chi tiết: [`shapley/WORK_SPLIT.md`](shapley/WORK_SPLIT.md).

---

## 6. Ghi chú kỹ thuật

- Chấm điểm MATH: trích `\boxed{}` + chuẩn hoá chuỗi/số. Bản đầu strip `\text{...}` gây
  khớp nhầm đáp án chữ; `regrade_math.py` sửa offline (giữ nội dung `\text{}`).
- Với 4 agent *cùng yếu (1.5B)*, phối hợp gần như không lợi trên bài khó (đội chỉ hơn
  1 solver đơn ~0.02), và 2 vai trò "sản xuất" còn *nhiễu* nhau ⇒ tín hiệu thật nằm ở
  các vòng **capacity** (dị thể).
