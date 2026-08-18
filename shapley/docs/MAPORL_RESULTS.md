# MAPoRL co-training (S/V/A) — kết quả thí nghiệm

Giai đoạn 3 (sau credit-sharing RL): áp dụng **MAPoRL2** (Park et al., ACL 2025,
`maporl.pdf`/`maporl.txt` trong `Temp\opencode\`) vào pipeline P→S→V→A. Khác
credit-RL (train từng vai, 3 vai kia fixed base), MAPoRL **co-train S/V/A đồng thời**
bằng 3 LoRA adapter trên cùng 1 base model, reward **influence-aware**: mỗi agent
được thưởng theo correctness của chính nó **+ ảnh hưởng lên agent downstream**.

Mốc so sánh (GSM8K 1.5B): base pipeline P→S→V→A greedy đạt **.744** (RESULTS.md:104,
n=250); credit-RL (Giai đoạn 1–2) chưa bao giờ thắng base pipeline.

---

## 1. Phương pháp (từ paper, rút gọn cho T4 16GB)

| thành phần | paper (MAPoRL2) | thí nghiệm này |
|---|---|---|
| agents | A agents × T turn debate (Du et al. 2024) | 3 agent S/V/A, 1 turn pipeline (P base = "bắt đầu co-train từ turn 2") |
| reward | verifier score `p(correct|q,s1:x)` ∈[0,1] (ORM, acc 0.91) + influence term | correctness 0/1 (soft penalty) + influence term |
| training | multi-agent PPO, mỗi agent 1 QLoRA adapter + value head riêng | multi-agent PPO, 3 LoRA adapter (r=16 α=32), 1 optimizer chung, **không value head** |
| data | 7.4k GSM8K (verifier) + 12.8k TinyGSM (RL), 8×A100 | 256 GSM8K train, 1×T4 |
| incentive | λ₁ own-revision (W→R khi majority đúng), β₀ influence (answer sai nhưng hữu ích) | β_S, β_V = trong số influence (cả 2 = 1.0) |

### Reward influence-aware (kernel)
```
r_S = soft(sol) + βs·(soft(v) + soft(a))/2     # S thưởng thêm nếu giúp V, A đúng
r_V = soft(v) + βv·soft(a)                     # V thưởng thêm nếu giúp A đúng
r_A = soft(a)                                  # A = kết quả cuối cùng
soft(t) = ok(t, gold) − 0.5·(short/empty <20 token) − 0.5·(post-\boxed{} junk, MATH)
```
Group advantage per câu (GRPO): normalize {r_S, r_V, r_A} theo (mean,std) — chống
3 agent cùng collapse về đáp án sai trùng nhau. Inner loop multi-epoch PPO
(clip ε=0.2, KL vs base β=0.04).

---

## 2. Cấu hình thí nghiệm

| tham số | giá trị |
|---|---|
| model | Qwen2.5-1.5B-Instruct (`xatri007/qwen2-5-1-5b-instruct`) |
| LoRA | 3 adapter (s/v/a), r=16, alpha=32, dropout 0.05, target q/k/v/o |
| data train | GSM8K `main_train.csv`, pool N_TRAIN=256 |
| outer loop | OUTER=16, mỗi vòng K=32 câu (rollout lại policy hiện tại) |
| inner loop | PPO E=3, clip 0.2, KL vs base 0.04 |
| rollout | S/V/A sampling TEMP=0.7; P luôn base |
| reward | influence-aware, β_S=1.0, β_V=1.0 |
| eval | N=100 test, greedy; base vs co-train vs từng adapter solo |
| phần cứng | Kaggle T4 fp16, 1 kernel (`viettran12/maporl-cotrain-sva-gsm8k`) |

---

## 3. Kết quả

### 3.1 Smoke test (`maporl-cotrain-sva-gsm8k-smoke`, N=64, K=8, OUTER=2)
- Chạy sạch, không crash/OOM; lưu đủ 3 adapter `s/` `v/` `a/`.
- quick_eval (200 câu): base 0.700 → co-train 0.705 (**+0.005**); solo S 0.705, V 0.700, A 0.700.
- **Phát hiện thời gian**: eval cuối 5 pipeline × 200 câu ≈ 80 phút → giảm còn 100 câu
  + precompute plan 1 lần dùng chung (bản full).

### 3.2 Full run (`maporl-cotrain-sva-gsm8k`, N=256, K=32, OUTER=16, ~1.9h)

Hist outer loop (mean reward / acc từng vai):

| outer | rS | rV | rA | acc_sol | acc_v | acc_a |
|---|---|---|---|---|---|---|
| 1 | 0.95 | 1.08 | 0.41 | 0.41 | 0.67 | 0.41 |
| 6 | 1.07 | 1.14 | 0.39 | 0.50 | 0.75 | 0.39 |
| 11 | 1.10 | 1.11 | 0.38 | 0.55 | 0.73 | 0.38 |
| 16 | 0.88 | 0.86 | 0.34 | 0.45 | 0.52 | 0.34 |

quick_eval (100 câu test):

| pipeline | acc | gain |
|---|---|---|
| base (P→S→V→A, P base) | **0.690** | — |
| co-train (S/V/A adapters) | **0.690** | **+0.000** |
| solo S | 0.690 | 0.000 |
| solo V | 0.690 | 0.000 |
| solo A | 0.690 | 0.000 |

Adapter lưu tại `Temp\opencode\maporl_full\adapter\` (s/ v/ a/).

### 3.3 V2: co-train S/V/A có siết A (N=512, K=32, OUTER=32, ~9h)

Sau v1 phát hiện v1 thực ra **chỉ train được adapter S** (PEFT chỉ set
`requires_grad=True` cho adapter active "s"; V/A bị freeze vô tình) — đây là lý do
v1 không gain. V2 sửa để co-train thật cả S/V/A: `requires_grad=True` cho mọi
lora params, **siết A** qua A-cond reward (+1.0 đúng / −2.0 sai khi có candidate
đúng, LR_A=1e-4 gấp đôi), tăng compute N=512/OUTER=32.
Kernel `tbmdemi/maporl-cotrain-sva-gsm8k-v2` (v1–v4 ERROR: assert adapter params →
NaN trong PPO → TypeError shadowing biến `n`; v5 chạy trọn).

quick_eval (100 câu test):

| pipeline | acc | gain |
|---|---|---|
| base (P→S→V→A, P base) | **0.690** | — |
| co-train (S/V/A adapters) | **0.000** | **−0.690** |
| solo S | 0.720 | +0.030 |
| solo V | 0.210 | −0.480 |
| solo A | 0.000 | −0.690 |

Hist: outer 1 acc_v=0.766/acc_a=0.781 (adapter mới init = base) nhưng từ outer 2
trở đi **acc_v ≈ 0.0 và acc_a = 0.0 suốt 31 outer** — V và A **collapse hoàn toàn**
sau đúng 1 PPO update (S vẫn ổn, acc_sol 0.4–0.6).

### 3.4 V3: co-train S/V, A frozen=base (N=512, K=32, OUTER=32, ~3.7h)

Nguyên nhân nghi vấn ban đầu là penalty −2.0 trong rV (A sai kéo V xuống) → thử
bỏ hẳn adapter A (A luôn base, sa=soft 0/1 không penalty), chỉ co-train S/V.
Kernel `viettran12/maporl-cotrain-sv-gsm8k` (COMPLETE).

quick_eval (100 câu test):

| pipeline | acc | gain |
|---|---|---|
| base (P→S→V→A, P base) | **0.690** | — |
| co-train (S/V adapters, A base) | **0.480** | **−0.210** |
| solo S | 0.710 | +0.020 |
| solo V | 0.450 | −0.240 |

Hist: outer 1 acc_v=0.766 (V base) → outer 2 **acc_v=0.094** rồi ~0.000 suốt 30
outer còn lại. **V collapse vẫn xảy ra dù A không còn penalty** → root cause không
phải reward A. Log ghi `NaN/Inf adapter params repaired: 49 tensors` lặp **mỗi
step** suốt run (1453 lần), lần đầu ngay outer 1 (`224 tensors` = toàn bộ S+V).

Output: `Temp\opencode\maporl_sv_log1\` (summary.json, hist.json, adapter\{s,v}\).

---

## 4. Phân tích

1. **Co-train không thắng base (0.690 = 0.690).** Gain = 0.000, các adapter solo cũng
   không đổi gì so với base trên eval. Không phải âm như credit-RL, nhưng cũng không
   tiến triển.
2. **V có học được** (acc_v tăng tới 0.75 ở vài outer, reward rV cao ~1.0), **nhưng A
   là bottleneck**: rA thấp (~0.34), acc_a chỉ 0.28–0.45 suốt 16 outer. Aggregator không
   tận dụng được lời giải đúng của S/V → kéo toàn pipeline về baseline.
3. **Khác biệt với paper quá lớn để hy vọng tái lập trên T4**: paper dùng verifier RL
   (reward mượt acc 0.91, không hack được) + 12.8k câu + 8×A100 + value head/GAE
   cho từng agent. Thí nghiệm này dùng correctness 0/1 proxy + 256 câu + 1 T4 —
   tín hiệu yếu và vẫn dễ hack như Giai đoạn 1–2.
4. **Eval 100 câu** = slice đầu test (không random) — acc_ref 0.690 thấp hơn baseline
   .744 (n=250, subset khác) nên chỉ dùng làm so sánh trong cùng subset.

---

## 5. Kết luận

- **Bác bỏ giả thuyết** rằng co-train 3 agent bằng multi-agent PPO với reward
  correctness + influence term (phiên bản T4, không verifier RL) cải thiện được
  pipeline 1.5B trên GSM8K.
- **v2/v3 xác nhận V/A collapse không phải do reward A**: dù bỏ penalty A và để A
  frozen=base, adapter V vẫn bị NaN mỗi step (`repaired: 49 tensors` ~ mỗi 2.3s,
  1453 lần) và collapse tới acc_v ≈ 0 từ outer 2. Chỉ S học được nhẹ (solo +0.02).
  Nghi vấn kỹ thuật: `clip_grad_norm_` toàn cục có thể lan NaN từ 1 grad sang toàn
  bộ params (total_norm=NaN) — chưa được chẩn đoán sâu (đã dừng theo quyết định).
- Hướng còn lại nếu muốn tiếp tục: (a) sửa clip_grad theo từng param group + chẩn
  đoán nguồn NaN V; (b) tăng data/compute; (c) **dừng và ghi nhận như kết quả âm**
  (đã chọn — MAPoRL co-train kết thúc ở đây).

## 6. Trạng thái

- Kernel: `shapley/pipeline/maporl_kernel.py` (co-train S/V, A frozen=base — bản
  cuối).
- Deploy: `shapley/deploy/orchestrate_maporl.py` (KDIR `kernels_maporl` — riêng, tránh
  xung đột KDIR như asel-vs-vote).
- Kernel đã chạy: `viettran12/maporl-cotrain-sva-gsm8k-smoke` (COMPLETE),
  `viettran12/maporl-cotrain-sva-gsm8k` (COMPLETE), `tbmdemi/maporl-cotrain-sva-gsm8k-v2`
  (COMPLETE), `viettran12/maporl-cotrain-sv-gsm8k` (COMPLETE). Output:
  `Temp\opencode\maporl_full\`, `maporl_v2_log5b\`, `maporl_sv_log1\`.
- Adapter (chưa upload dataset): trong output kernel `adapter\{s,v,a}\`.
- Paper đọc: `Temp\opencode\maporl.pdf` + `maporl.txt` (đầy đủ method/verifier/training).