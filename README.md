# Do the roles in a multi-agent LLM pipeline actually exist?

Course project — Natural Language Processing (INT3406), VNU University of Engineering and
Technology. Group 13: Dương Trọng Nguyên, Trương Đình Đức, Trần Tùng Dương, Lê Hoàng Quân.

**[Read the report (29 pages, PDF)](report/REPORT_GROUP13.pdf)** · [Slides](report/SLIDE_BAO_CAO.pdf) · [Full experiment archive](../../tree/archive)

---

## The one-paragraph version

We asked a 1.5B model to write an implementation plan and told it explicitly not to write code.
It wrote code anyway in **53.7%** of HumanEval problems. Told to write it, 100%. And adding that
planner to the pipeline made the pipeline *worse* — 0.5375 accuracy with no planner against
0.4312 with one, in five folds out of five.

That is the report's subject. When one model is split into planner, solver, verifier and
aggregator, the model does not respect the boundaries the prompts describe. What looks like a
gain from coordination is mostly the gain from sampling the same model more than once.

## What the evidence looks like

Everything below is measured at a **single model size**, so no capability-gap confound is doing
the work. Five folds unless noted.

| Question | Answer | Where |
|---|---|---|
| Given a solver, what do the other three roles add? | **4.9 points** on GSM8K; nothing distinguishable from zero on MATH-500 | §5.3 |
| Does the planner respect its instruction? | No. Writes code in 53.7% of HumanEval plans under an explicit prohibition; net harmful, 5/5 folds | §5.4 |
| Does the verifier's critique carry information? | No. Re-solving *without* reading it scores the same as reading it: **0.453 = 0.453** | §5.2 |
| Do the role labels matter at all? | In 3 of 4 cells, no — three plain solver calls tie the named pipeline (0.728 = 0.728). In the 4th, the pipeline is ahead 11 points | §5.2 |
| Is the same-size verifier verifying? | Intervention accuracy 56–59%, near chance; blind to injected digit errors | §5.5 |
| Is the aggregator aggregating? | 3 new-and-correct answers in 2000 turns | §5.6 |
| Can it be trained away? | Seven methods, seven different shortcuts. None learned the role | §5.11 |
| So use a stronger checker? | It helps — and costs **−27.2 points** on the stratum where the weak model's solution is wrong | §5.9 |

## Why the measurement is the hard part

Three controls, and they do not point the same way — which is why all three have to be applied
at once:

| Control | If you skip it | Effect on the measured benefit |
|---|---|---|
| Compute budget | Comparing a multi-call system against one generation | **Inflates** |
| Choice of baseline | Measuring against the weak model instead of a strong model alone | **Inflates** |
| Denominator | Averaging over problems no mechanism could ever change | **Deflates** |

Effect sizes are read against a measured noise floor: the same configuration across five folds
has a standard deviation of 2.65 points, so the effective threshold is about **3.3 points**.
Anything below that is reported as below threshold rather than as a result.

## What we would not claim

The maths leakage rates (33.3% on GSM8K) are detected by checking whether the last number in the
plan equals the gold answer, so they are upper bounds, not counts of deliberate computation. The
code measurement — does the plan contain a code fence or a `def` — is the one the argument rests
on. HumanEval folds are 32 problems each, smaller than the 60–100 used to calibrate the noise
floor. The one cell where the named pipeline clearly beats an unlabelled one (MATH at 7B, 11
points, 5/5 folds) is reported as prominently as the ties.

## Repository map

```
report/     the report, the slides, and the figures
analysis/   Shapley, bootstrap, grading, strata, trace behaviour, routing
pipeline/   experiment kernels, one per experiment, written to run on Kaggle
deploy/     orchestration: launching jobs, collecting results, account rotation
tests/      test suite for the router
```

| To reproduce | Run |
|---|---|
| Role credit with the solver held fixed (§5.3) | `analysis/shapley.py`, `shapley_role7b.py`, `signed_shapley.py`, `interaction.py`, driven by `pipeline/roleablate_kernel.py` |
| Planner leakage, maths and code (§5.4) | `pipeline/patch_kernel.py`, `pipeline/planner_code_kernel.py` |
| Role behaviour from traces (§5.4–§5.6) | `analysis/role_specialization.py`, `trace_novelty.py`, `pipeline/promptswap_folds_kernel.py` |
| Budget controls and the anchored-solver control (§5.2) | `pipeline/budget_kernel.py`, `budget4_kernel.py` |
| Noise floor (§5.1) | `pipeline/noisefloor_kernel.py` |
| Strata and reach (§5.7) | `analysis/difficulty_strata.py` |
| Strong-model baseline and cost (§5.8) | `pipeline/baseline_kernel.py` |
| Artifact exposure (§5.9) | `pipeline/exposure_math_kernel.py`, `exposure_dose_kernel.py`, `capacity_poison_kernel.py` |
| Verification signal and routing (§5.10) | `pipeline/execverify_kernel.py`, `gate_kernel.py`, `injected_classifier_kernel.py`, `analysis/router.py` |
| Role training (§5.11) | `pipeline/credit_rl_kernel.py`, `orpo_kernel.py`, `maporl_kernel.py` |
| Capability gap and transfer (Appendix A) | `analysis/merge_pairs.py`, `pipeline/crossfamily_kernel.py` |

```bash
export ACCOUNTS_FILE=/path/to/accounts.txt    # one line per account: <username> <token>
export KAGGLE_RTX_ACCOUNT=<username>          # only needed for the large-GPU runs
python deploy/launch_any.py <kernel_name>

pytest tests/ -q
cd report && tectonic -X compile REPORT_GROUP13.tex --outdir .
```

No tokens or account names are committed. Raw trace dumps are not committed either — they
regenerate from `pipeline/`; only the summary files are kept.

## Setup

Four benchmarks: GSM8K, MATH, MBPP, HumanEval. Models from 0.5B to 32B parameters. Deterministic
decoding for the information-flow experiments, so fold-to-fold variation there comes from
different problems rather than from sampling. Designs and evaluation criteria were fixed in
advance; 16 of 32 runs were invalidated by their own preconditions and discarded before the
results were read.

The [`archive` branch](../../tree/archive) holds the complete record: 151 kernels, 89
orchestration scripts, 40 analysis documents, and the per-run result files, plus the project log
in `shapley/docs/NHAT_KY_DU_AN.md`.
