# Experiment Results — 2026-08-18

5/5 Kaggle kernels complete. All validity checks passed.

## Summary Table

| Kernel | Task | AUC | Adapter Leak | Maj@8 | Rerank@8 | WVote-Sum | Oracle@8 |
|--------|------|-----|-------------|-------|----------|-----------|----------|
| rc-m7-math | math | — | — | — | — | — | — |
| h24-cell4-math | math | — | — | — | — | — | — |
| disc-leakfix-gsm8k | gsm8k | 0.841 ✅ | -0.033 ✅ | 0.723 | 0.700 | 0.730 | 0.880 |
| disc-leakfix-math | math | 0.933 ✅ | -0.050 ✅ | 0.296 | 0.304 | 0.312 | 0.376 |
| injected-classifier-math | math | 0.833 ✅ | +0.050 ✅ | 0.400 | 0.404 | 0.432 | 0.532 |

> rc-m7-math and h24-cell4-math measure different metrics (context ablation, verifier variants) — see details below.

---

## 1. rc-m7-math (ziangtran) — Context Ablation

**Question:** Does full reasoning chain context improve solver accuracy vs trimmed context?

| Metric | Mean | Range |
|--------|------|-------|
| Solver (solo) | 0.660 | 0.50–0.77 |
| Full context | 0.727 | 0.57–0.80 |
| Trimmed context | 0.513 | 0.37–0.67 |

- **Full context +6.7pts** over solo — providing complete reasoning chain helps.
- **Trimmed context −21.3pts** — removing chain detail severely hurts performance.
- Conclusion: full reasoning chains carry signal that trimmed versions lose.

---

## 2. h24-cell4-math (nguyenminhoang) — Verifier Variants

**Question:** Does a verifier improve over solo solving? Does blind verification help?

| Metric | Mean |
|--------|------|
| Solo | 0.660 |
| Plan-conditioned | 0.653 |
| Verifier-infinite (full info) | 0.700 |
| Verifier-blind (no solution) | 0.667 |

- **Verifier-infinite +4.0pts** over solo — verifier with full information helps.
- **Verifier-blind +0.7pts** — barely helps, verifier needs to see the solution.
- **Plan-conditioned −0.7pts** — conditioning on plan alone doesn't help.

---

## 3. disc-leakfix-gsm8k (giangle) — Discriminative Verifier on GSM8K

**Design:** Train LoRA verifier on model-generated errors (K=8 samples). Test if it discriminates correct vs incorrect solutions. Adapter leak check: probe same 60 problems before/after training.

| Metric | Value |
|--------|-------|
| AUC | 0.841 ✅ (>0.55) |
| Adapter leak | -0.033 ✅ (≤0.05) |
| Probe pre-acc | 0.533 |
| Probe post-acc | 0.567 |
| Train pos rate | 0.620 (1514/2400 correct) |

**Reranking performance:**
| Method | Mean | Min | Max |
|--------|------|-----|-----|
| Greedy@1 | 0.577 | 0.483 | 0.683 |
| Maj@8 | 0.723 | 0.667 | 0.800 |
| Rerank@8 | 0.700 | 0.583 | 0.767 |
| WVote-Sum | 0.730 | 0.667 | 0.783 |
| Oracle@8 | 0.880 | 0.867 | 0.900 |

- AUC 0.841 — verifier discriminates well on GSM8K.
- **WVote-Sum +0.7pts over Maj@8** — weighted voting slightly helps.
- **Rerank@8 −2.3pts vs Maj@8** — reranking hurts on GSM8K (picks wrong sample).
- WVote-Mean (−13.0pts) — normalizing by vote count fails badly.

---

## 4. disc-leakfix-math (tran) — Discriminative Verifier on MATH

Same design as #3 but on MATH-500. Higher AUC but lower absolute accuracy (MATH is harder).

| Metric | Value |
|--------|-------|
| AUC | 0.933 ✅ (>0.55) |
| Adapter leak | -0.050 ✅ (≤0.05) |
| Probe pre-acc | 0.217 |
| Probe post-acc | 0.267 |
| Train pos rate | 0.223 (445/2000 correct) |

**Reranking performance:**
| Method | Mean | Min | Max |
|--------|------|-----|-----|
| Greedy@1 | 0.208 | 0.140 | 0.260 |
| Maj@8 | 0.296 | 0.220 | 0.340 |
| Rerank@8 | 0.304 | 0.220 | 0.360 |
| WVote-Sum | 0.312 | 0.220 | 0.360 |
| Oracle@8 | 0.376 | 0.340 | 0.420 |

- **AUC 0.933** — highest of all experiments. Verifier is very good at distinguishing correct vs incorrect on MATH.
- Low train pos rate (22.3%) — Qwen2.5-1.5B struggles with MATH, most samples are wrong.
- **WVote-Sum +1.6pts over Maj@8** — weighted voting helps consistently (5/5 folds positive).
- **Rerank@8 +0.8pts** — reranking helps slightly on MATH (unlike GSM8K).

---

## 5. injected-classifier-math (jlose) — Injected Error Training

**Design:** Train LoRA verifier on **injected errors** (corrupt one number in gold chain). Test if it transfers to **real errors** (model-generated mistakes). This tests whether synthetic error training generalizes.

| Metric | Value |
|--------|-------|
| AUC (real errors) | 0.833 ✅ (>0.55) |
| Adapter leak | +0.050 ✅ (≤0.05) |
| Probe pre-acc | 0.367 |
| Probe post-acc | 0.317 |
| Train pos rate | 0.515 (206/400) |
| Discrimination (injected) | 0.0 — cannot distinguish clean vs corrupt in-distribution |
| Degenerate rate | 0.694 ✅ (≤0.90) |

**Reranking performance:**
| Method | Mean | Min | Max |
|--------|------|-----|-----|
| Greedy@1 | 0.300 | 0.200 | 0.380 |
| Maj@8 | 0.400 | 0.260 | 0.520 |
| Rerank@8 | 0.404 | 0.320 | 0.500 |
| WVote-Sum | 0.432 | 0.340 | 0.540 |
| Oracle@8 | 0.532 | 0.440 | 0.580 |

- **AUC 0.833 on real errors** — injected error training transfers well to real errors.
- **Discrimination_injected = 0.0** — model says "Yes" to everything (clean and corrupt), so it can't detect injected errors. Yet it still discriminates real errors via logit magnitude.
- **WVote-Sum +3.2pts over Maj@8** — best improvement across all experiments.
- **Rerank@8 +0.4pts** — marginal help.

---

## Cross-Experiment Insights

1. **WVote-Sum consistently beats Maj@8** (+0.7 to +3.2pts across all 3 verifier experiments). Weighted voting by verifier logit is robust.
2. **Rerank@8 is unreliable** — helps on MATH (+0.8pts), hurts on GSM8K (−2.3pts). Picking single best sample is high variance.
3. **AUC ranking:** disc-leakfix-math (0.933) > disc-leakfix-gsm8k (0.841) > injected-classifier-math (0.833). Training on real errors gives better discrimination than injected errors, but injected transfers surprisingly well.
4. **Adapter leak** all ≤0.05 — LoRA training doesn't corrupt the base model's solving ability.
5. **Context matters:** full reasoning chain +6.7pts, trimmed −21.3pts (rc-m7). Verifier needs full info (+4pts), blind doesn't help (h24-cell4).

## Bugs Fixed This Run

- **torchao incompatibility:** Kaggle ships torchao 0.10, peft requires >0.16. Fix: `pip uninstall -y torchao` before import.
- **Missing `ok()` function:** injected_classifier_kernel.py used `ok()` but only defined `eq()`. Fix: added `ok = lambda x, g: eq(x, g)`.
