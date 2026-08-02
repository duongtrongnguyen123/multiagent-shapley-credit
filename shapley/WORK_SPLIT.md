# MATH-500 Shapley Study — 4-Person Work Split

Goal: replicate the GSM8K credit-assignment result on a harder verifiable substrate
(MATH-500) and build the full role×capacity matrix. Each person owns a workstream end
to end (deploy → collect → analyze). Shared infra lives in `qwen-gsm8k-kaggle/shapley/`.

**Shared conventions**
- Auth per account: `export KAGGLE_API_TOKEN=<KGAT_… from accounts.txt>` (already wired
  into the orchestrators, which read `accounts.txt`).
- Collect (foreground, never a background poll loop — they die on turn transitions):
  `ROUND=<round> python sync_once.py` repeatedly until `REMAINING 0`.
- One 16-coalition round OR two 8-coalition rounds saturate the 19 accounts. **Coordinate
  in the team channel before launching so two rounds don't grab the same accounts.**
- `truongdv006` is rate-limited/flagged — skip it; use spares `khunht`, `dnglethnh`,
  `tbmdemi` (accounts 17–19) for redeploys.

---

## Person 1 — Nguyên · Baseline + analysis harness  *(IN PROGRESS)*
- **Round `m1`**: homogeneous 1.5B, all 16 coalitions, N=500. Deployed; collecting.
  `ROUND=m1 python sync_once.py` → `ROUND=m1 python shapley.py` + `ROUND=m1 python bootstrap.py`.
- Owns the cross-round synthesis: merge all rounds into the final role×capacity table,
  update `FINDINGS.md`. Baseline v(S) here is reused by every capacity round (S with the
  upgraded role absent = m1 value), so **m1 must finish first**.

## Person 2 — Core producers: 7B Solver & 7B Verifier
- **Round `mV`** (7B verifier, 8 V=1 coalitions):
  `BIG=V ROUND=mV N_EVAL=500 python orchestrate_math_role7b.py`
  then `ROUND=mV python sync_once.py`, `BIG=V ROUND=mV python shapley_role7b.py`.
- **Round `mS`** (7B solver): `BIG=S ROUND=mS N_EVAL=500 python orchestrate_math_role7b.py` …
- Question: on MATH, does the verifier still dominate, or does the **solver** take the top
  slot when problems are too hard for a weak verifier to check?

## Person 3 — Auxiliary roles: 7B Planner & 7B Aggregator
- **Round `mP`** (7B planner): `BIG=P ROUND=mP N_EVAL=500 python orchestrate_math_role7b.py` …
- **Round `mA`** (7B aggregator): `BIG=A ROUND=mA N_EVAL=500 python orchestrate_math_role7b.py` …
- Key test: GSM8K's planner was a net-negative free-rider. MATH needs real decomposition —
  **does the planner become essential here?** If φ_P flips strongly positive, planning value
  is task-dependent (the headline cross-substrate result).

## Person 4 — Coding substrate track  *(parallel, independent)*
- Port the same 16-coalition design to code, where the verifier is **grounded** (executes
  unit tests) and the reward is **graded** (fraction of tests passing).
- Tasks: (a) find Kaggle datasets — `kaggle models list -s "qwen2.5 coder"` (Coder-1.5B/7B),
  a tests-bearing set (MBPP+/HumanEval+); (b) write a code-execution kernel (subprocess +
  timeout sandbox, offline); (c) deploy homogeneous round `c1`. Reuse `sync_once.py`,
  `shapley.py`, `bootstrap.py` unchanged (ROUND=c1).
- Highest engineering, most novel result — the grounded-verifier comparison.

---

## Sequencing (account contention)
1. **Wave 1 (now):** P1 runs `m1` (16 accounts).
2. **Wave 2:** after m1 frees accounts, P2 `mV` (8) + P3 `mP` (8) run together (16).
3. **Wave 3:** P2 `mS` (8) + P3 `mA` (8) together.
4. P4's coding track runs whenever accounts are idle, or on the team's other accounts.

## Deliverable per workstream
`results_<round>/` + `shapley_<round>_results.json` + `bootstrap_<round>_results.json`,
and one row in the shared role×capacity table (P1 assembles). Analysis scripts
(`shapley.py`, `shapley_role7b.py`, `bootstrap*.py`) already generalize by `ROUND`/`BIG`.
