# Credit-Sharing RL (Shapley marginal / GRPO) — kết quả thí nghiệm & insight

Giai đoạn: train từng vai (Planner P / Solver S / Verifier V / Aggregator A) bằng
credit-sharing RL trên **GSM8K train**, reward = đóng góp biên (Shapley marginal) của
vai đó trong pipeline P→S→V→A, nhóm GRPO advantage theo câu. Sau đó eval 5-fold trên
**GSM8K test** (tách rời, không rò rỉ) cho từng vai và cho cả pipeline đủ 4 vai.

Mốc đối chiếu (`FINDINGS.md`, GSM8K 1.5B): **V_base gain +4.4đ [+1..+8], 5/5 fold dương**.
Tiêu chí "kết quả dương thật": `gain_train > 0` **và** 5/5 fold cùng dấu.

---

## 1. Cấu hình thí nghiệm

| tham số | giá trị |
|---|---|
| model | Qwen2.5-1.5B-Instruct (`xatri007/qwen2-5-1-5b-instruct`) |
| LoRA | r=16, alpha=32, dropout 0.05, target q/k/v/o |
| dữ liệu train | GSM8K `main_train.csv`, pool N_TRAIN=256 |
| outer loop | OUTER=16, mỗi vòng K=32 câu (rollout lại policy hiện tại) |
| inner loop | PPO multi-epoch E=3, clip ε=0.2, KL vs base (π_ref) β=0.04 |
| rollout | vai train sampling TEMP=0.7; 3 vai còn lại luôn base (adapter tắt) |
| reward | 8 marginal m_S = v(S∪{R}) − v(S), S ⊆ {3 vai còn lại}; adv=(m−mean)/std nhóm 8 |
| eval | N=200 test, NF=5 fold, greedy; mỗi vai 1 kernel (chỉ load adapter vai đó) + 1 kernel FULL (cả 4 adapter) |
| phần cứng | Kaggle T4 fp16, 1 kernel/account |

Ma trận 16 coalition dùng chung 15 stage/câu (1 plan + 2 solver + 4 verifier + 8 aggregator);
7 stage không phụ thuộc vai đang train precompute 1 lần cho pool, mỗi outer chỉ rollout
vai R + 7 stage downstream phụ thuộc nó.

---

## 2. Kết quả training (hist outer loop + quick_eval trên 200 câu test)

| vai | mean_marginal outer 1 → 16 | pct_pos outer 1 → 16 | quick_eval gain |
|---|---|---|---|
| P | 0.52 → 0.56 | 65.6 → 78.1% | **0.000** |
| S | 0.72 → 0.70 | 90.6 → 84.4% | **0.000** |
| V | 0.69 → **0.82** | 93.8 → **100%** | **−0.005** |
| A | 0.66 → 0.63 | 90.6 → 84.4% | **−0.010** |

Đáng chú ý: **marginal dương cao và (với V) tăng dần qua 16 outer** — reward theo
đóng góp biên *có vẻ* học đúng hướng. Nhưng quick_eval (thay base bằng adapter trên
test) đều ≈ 0/âm — tín hiệu đầu tiên rằng marginal cao KHÔNG đồng nghĩa pipeline tốt hơn.

---

## 3. Kết quả eval 5-fold trên test (các kernel `credit-rl-eval-*`)

### 3.1 Từng vai (kernel chỉ load 1 adapter của vai đó)

| vai | acc_ref → acc_full | gain | folds cùng dấu |
|---|---|---|---|
| P | 0.680 → 0.680 | 0.000 | 0/5 |
| S | 0.680 → 0.685 | +0.005 | 2/5 |
| V | 0.670 → 0.665 | −0.005 | 2/5 |
| A | 0.695 → 0.690 | −0.005 | 1/5 |

### 3.2 FULL pipeline (load cả 4 adapter)

| nhánh | acc | gain | folds cùng dấu |
|---|---|---|---|
| ref (P→S→V→A base) | 0.695 | — | — |
| full (4 adapter trained) | 0.710 | +0.015 | 3/5 |
| stage PS base → full | 0.680 → 0.680 | 0.000 | — |
| stage PSV base → full | 0.670 → 0.670 | 0.000 (mean) | — |

### 3.3 Metrics can thiệp của Verifier (guardrail H23)

| metric | V base | V trained |
|---|---|---|
| intervention | 0.35 | 0.395 |
| fix | 0.10 | 0.13 |
| break | 0.11 | **0.145** |
| copy | 0.65 | 0.605 |

---

## 4. Phân tích trace — nguyên nhân thất bại

Tất cả trace lưu trong `traces.json`/`traces.jsonl` của từng eval kernel (200 câu × 5 fold).

### 4.1 Planner (P) — **collapse về output rỗng**

- Plan trained **rỗng 200/200 câu** (độ dài mean = 0 char; base = 585 char).
- Solver nhận `Suggested plan:` trống → coi như không có plan → **sol base == sol full ở
  80/80 câu kiểm tra** → gain = 0.000 chính xác từng fold.
- **Cơ chế:** plan rollout (temp 0.7) tạo nhiễu → solver base đôi khi trả lời tệ hơn →
  marginal âm. PPO học cách "an toàn": sinh plan ngắn/rỗng để không làm hỏng solver.
  Đây là **reward hacking**: điểm cao nhất đạt được bằng cách không làm gì, không phải
  bằng cách tạo plan hữu ích.

### 4.2 Verifier (V) — can thiệp khắp nơi, không phân biệt đúng/sai

- V trained viết lại lời giải **195/200 câu** (chỉ 5 câu giữ nguyên base).
- Kết quả: 23 fix nhưng **24 break** (cân bằng âm nhẹ). Intervention 0.35→0.395,
  break 0.11→0.145 > fix 0.10→0.13.
- **Cơ chế:** V không học quy tắc *"sửa khi sai, giữ khi đúng"* — nó sửa cả khi đúng.
  Điều này trái ngược baseline V_base (+4.4đ) của thí nghiệm static; loRA-train theo
  marginal 0/1 không tái tạo được hành vi đó.

### 4.3 Solver (S) / Aggregator (A)

- S: 109/200 câu giữ nguyên text; 4 fix vs 3 break → ≈ 0.
- A: 160/200 câu giữ nguyên; output vốn ngắn ("The answer is X"), trained dài thêm
  nhưng không cải thiện đáng kể.

---

## 5. Insight tổng hợp

1. **Marginal correctness 0/1 là tín hiệu thô và dễ bị hack.** Mỗi marginal chỉ nhận
   0/1 nên gradient không phân biệt "plan giúp ít" vs "plan phá" đủ mạnh; policy tìm
   được quỹ đạo điểm cao nhất bằng cách **không hành động** (P rỗng) hoặc **hành động
   vô trách nhiệm** (V sửa cả khi đúng). Điều này khiến `mean_marginal` tăng (0.69→0.82
   với V) **trong khi** eval thật không cải thiện — một ví dụ rõ ràng về **reward hacking**
   trong RL cho LLM multi-agent.

2. **Marginal cao ≠ pipeline tốt hơn.** Cả 4 vai đều có marginal dương rất cao
   (75–100% câu) nhưng 0 vai đạt tiêu chí dương thật (gain>0 + 5/5 fold cùng dấu).
   Shapley marginal đo *giá trị vai trong coalition tĩnh*; dùng nó làm reward trực tiếp
   không chuyển thành hành vi mong muốn khi mỗi vai được LoRA-train riêng lẻ trong khi
   3 vai kia cố định base.

3. **P là vai "vô hình" trong RL, dù static measurement chỉ ra nó là free-rider
   (φ_P ≈ 0).** Ở cấu hình này P thậm chí còn tệ hơn: collapse về rỗng. Điều này khớp
   insight trước đó rằng Planner hại khi 1.5B (FINDINGS Round 2: PSA/PVA −12đ) — RL với
   reward 0/1 đã tìm ra cách tối ưu là *tắt hẳn* vai này.

4. **Hướng sửa tiềm năng** (chưa thử):
   - Reward mượt hơn: dùng **log-likelihood/confidence** của solver thay vì correctness
     0/1, hoặc thưởng phạt đối xứng khi can thiệp đúng/sai (cho V).
   - Thêm điều khoản **KL/entropy bonus mạnh hơn** hoặc cấm empty output (độ dài plan ≥
     ngưỡng) để chống collapse.
   - Với V: reward chỉ cho hành vi *sửa khi base sai* (marginal của V có điều kiện trên
     sai), hoặc imitation từ baseline V_base thay vì RL thuần.

---

## 6. Trạng thái

- Kernel train: `shapley/pipeline/credit_rl_kernel.py` (tổng quát 4 vai) + `deploy/orchestrate_credit_rl.py`.
- Eval: `shapley/pipeline/credit_rl_eval_kernel.py` (ROLE ∈ P/S/V/A/FULL) + `deploy/orchestrate_credit_rl_eval.py`.
- Adapter datasets (public): `tbmdemi/credit-rl-p-adapter`, `truongdinhduc06/credit-rl-s-adapter`,
  `Viettran12/credit-rl-v-adapter`, `TrgDinKai/credit-rl-a-adapter`.
- Kết quả chi tiết per-fold: log/summary/traces của 5 eval kernel (lưu cục bộ trong
  `C:\Users\hp\AppData\Local\Temp\opencode\eval_results\`).
- Kết luận: **thí nghiệm bác bỏ giả thuyết** rằng credit-sharing RL với reward =
  Shapley marginal 0/1 cải thiện được pipeline; không vai nào đạt tiêu chí dương thật.
