# Credit Assignment in Multi-Agent LLM Reasoning: From Measuring Role Value to Dynamic Composition

**Question:** In a Planner→Solver→Verifier→Aggregator pipeline, how much does each
role actually contribute — and is any role a free-rider (drawing team reward without
contributing, the LLM analog of the MARL lazy-agent problem)?

**Method:** Exact Shapley value over roles. Run all 2⁴=16 role coalitions on the same
GSM8K questions; v(S) = pipeline accuracy with only roles S active. A missing role is
skipped; the answer is read from the most-downstream active role.
φ_i = Σ_{S⊆N\{i}} |S|!(n−|S|−1)!/n! · (v(S∪i) − v(S)).
Homogeneous Qwen2.5-1.5B-Instruct in every role unless noted. Greedy decoding.
Deployed one coalition per Kaggle account (T4, fp16), 16 accounts in parallel.

## Round 1 (N=300) & Round 2 (N=1319) — homogeneous 1.5B

| Role | φ (N=1319) | 95% CI (bootstrap) | P(φ<0) |
|---|---|---|---|
| Solver | +0.2523 | [+0.2420, +0.2628] | 0.000 |
| Verifier | +0.2523 | [+0.2420, +0.2628] | 0.000 |
| Aggregator | +0.1903 | [+0.1819, +0.1990] | 0.000 |
| Planner | −0.0142 | [−0.0301, +0.0018] | 0.960 |

φ sums to v(full)=0.681 ✓ (Shapley efficiency axiom).

- **Verifier credit exactly ties Solver.** A re-checking agent is worth as much as the
  one that solves — the core argument for solver–verifier coordination.
- **Planner is net-negative** (~96% posterior). Smoking gun in the coalitions:
  `SA=0.682 → PSA=0.562` and `VA=0.682 → PVA=0.562` — adding the planner **subtracts 12
  points**. Negative transfer: a 1.5B model emits plans it cannot execute, and downstream
  roles anchor on them. Team accuracy alone (0.68) completely hides this.

## Round 3 (N=300) — heterogeneous: 7B planner

Only the 8 P=1 coalitions rerun with a Qwen2.5-7B-Instruct planner (others 1.5B, loaded
one-at-a-time per stage, fp16); P=0 coalitions reused from Round 1.

| Role | 1.5B planner | 7B planner | Δ |
|---|---|---|---|
| **Planner** | **−0.023** | **+0.055** | **+0.078** |
| Solver | +0.269 | +0.261 | −0.008 |
| Verifier | +0.269 | +0.261 | −0.008 |
| Aggregator | +0.196 | +0.209 | +0.014 |

Planner φ(7B): +0.055, CI [+0.021, +0.089], P(φ>0)=0.999. Flip Δ: +0.078, CI
[+0.049, +0.109], P(Δ>0)=1.000. Full-pipeline accuracy 0.71 → 0.787.

**Verdict: CAPACITY, not inherent.** The catastrophic coalitions recover most:
`APS: 0.56 → 0.787 (+0.227)`, `APV: 0.56 → 0.787 (+0.227)`. The planner's harm was a
weak-model artifact — a competent planner turns the plan from liability into asset.

## Round 4 (N=300) — heterogeneous: 7B verifier

Same design as Round 3 but the 8 V=1 coalitions rerun with a 7B verifier.

| Role | 1.5B | 7B verifier | Δ |
|---|---|---|---|
| **Verifier** | +0.269 | **+0.462** | **+0.193** |
| Solver | +0.269 | +0.237 | −0.032 |
| Aggregator | +0.196 | +0.187 | −0.009 |
| Planner | −0.023 | −0.013 | +0.011 |

Verifier φ(7B) +0.462, CI [+0.438, +0.486]; flip Δ +0.193, CI [+0.162, +0.225], P(Δ>0)=1.000.
Full pipeline 0.71 → 0.873. Coalition lifts: `V-only 0.663→0.923 (+26pt!)`, `AV 0.713→0.937`,
`PSV 0.683→0.877`, `APSV 0.710→0.873`.

- **The verifier is by far the most capacity-sensitive role**: a 7B verifier lifts accuracy up
  to **+26pt**, versus **+7pt** for a 7B planner. Its Shapley credit (+0.462) is ~2× the
  solver's — a single 7B verifier captures ~46% of total team accuracy.
- **Substitution effect**: the Solver's credit *drops* (+0.269 → +0.237) when the verifier is
  strong — a capable verifier partially does the solver's job, so their contributions overlap.
  Shapley captures this interaction; leave-one-out would not.
- **Practical rule**: if you can upgrade the model for exactly one role in a solver–verifier
  team, **make it the verifier**.

## Cross-substrate: MATH-500 (N=500, homogeneous 1.5B)

Same 16-coalition design on MATH-500 (LaTeX `\boxed{}` grading, re-graded offline).
Base rate 0.428 (vs GSM8K 0.66) — much more headroom, but the ranking **changes**:

| Role | MATH φ | 95% CI | GSM8K φ |
|---|---|---|---|
| **Aggregator** | **+0.148** | [+0.132, +0.164] | +0.190 (3rd) |
| Solver | +0.141 | [+0.126, +0.157] | +0.252 (1st) |
| Verifier | +0.141 | [+0.126, +0.157] | +0.252 (1st) |
| Planner | +0.017 | [−0.008, +0.043] | −0.014 |

Three substrate-dependent shifts:
1. **The verifier loses its lead.** On GSM8K it tied the solver at the top; on MATH it still
   ties the solver but both fall *below the aggregator*. A weak verifier can't fix a long,
   hard, wrong solution — so re-checking adds little beyond a fresh attempt.
2. **The aggregator becomes the top role.** On hard problems, selecting among diverse
   independent attempts (self-consistency-like) beats single-pass verification.
3. **The planner stops being harmful** (+0.017, P(φ<0)=0.09) — no longer net-negative;
   MATH's real need for decomposition offsets the negative-transfer seen on GSM8K.

**Negative coordination among producers:** the 2-role producer coalitions are *worse* than
single roles — `S=V=A=0.428` but `SV=SA=VA=0.384`. A weak model given a peer's solution
tends to "correct" a right answer into a wrong one. Coordination gain over the best single
role is only **+0.02** — with homogeneous weak agents on hard problems, coordination barely
helps; the signal will come from the capacity (heterogeneous) rounds.

**Headline:** "invest in the verifier" is a GSM8K artifact, **not a general principle** —
on harder math the aggregator matters more and verification saturates. Role value is
substrate- *and* capacity-dependent.

## Takeaways

1. Shapley over roles cleanly exposes credit that team accuracy hides — including
   **negative** contributions (structural free-rider / negative-transfer).
2. The lazy/harmful-agent pathology is **capacity-dependent**: role value is not intrinsic
   to the role, but to the role×model-strength pairing.
3. **Roles differ hugely in capacity-sensitivity**: upgrading the verifier buys ~4× the
   accuracy of upgrading the planner. Where to spend compute is itself a credit-assignment
   question, and Shapley answers it — put the big model on the verifier.
4. Shapley captures **interaction/substitution** (strong verifier lowers solver credit) that
   leave-one-out misses.
5. GSM8K's verifiable reward makes it a valid *credit-assignment testbed* for LLM agents
   (not a coordination benchmark itself) — leave-subset-out is a real counterfactual here.

## Reproduce
- `template.py` / `orchestrate.py` — homogeneous coalitions; `ROUND=r1|r2 N_EVAL=… python orchestrate.py`
- `template_het.py` / `orchestrate_het.py` — 7B-planner coalitions
- `sync_once.py` — pull results (foreground; background poll loops get killed on turn transitions)
- `shapley.py` / `bootstrap.py` — homogeneous Shapley + CIs (`ROUND=…`)
- `shapley_het.py` / `bootstrap_het.py` — heterogeneous Shapley + flip CI
- Data: model `xatri007/qwen2-5-1-5b-instruct`, `ragnar123/qwen2-5-7b-instruct`; GSM8K `thedevastator/grade-school-math-8k-q-a`
