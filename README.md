# Role Specialisation in Multi-Agent LLM Pipelines: An Empirical Study

Code and results for a study of whether the roles in a planner/solver/verifier/aggregator
pipeline perform the functions they are named for.
Report: [`report/REPORT_GROUP13.pdf`](report/REPORT_GROUP13.pdf) (29 pages).

Course project, Natural Language Processing (INT3406), VNU University of Engineering and
Technology. Group 13: Dương Trọng Nguyên, Trương Đình Đức, Trần Tùng Dương, Lê Hoàng Quân.

```bash
pip install -r requirements.txt
```

Benchmarks: GSM8K, MATH, MBPP, HumanEval. Models from 0.5B to 32B parameters. All results below
are five-fold means at a single model size unless stated, read against a measured noise floor of
2.65 points standard deviation between folds — an effective threshold of about 3.3 points.

## Results

### Role credit, with the solver held fixed

Shapley values over the eight coalitions containing the solver. Scale 0–1, 95% bootstrap CI.

| Role | GSM8K (N=1319) | MATH-500 (N=500) |
|---|---|---|
| Planner | −0.0188 [−0.0399; +0.0021] | +0.0210 [−0.0137; +0.0540] |
| Verifier | **+0.0555** [+0.0430; +0.0675] | −0.0050 [−0.0257; +0.0150] |
| Aggregator | **+0.0126** [+0.0052; +0.0202] | +0.0040 [−0.0100; +0.0187] |

Given a solver, the other three roles add 4.9 points on GSM8K and nothing distinguishable from
zero on MATH-500.

```bash
ROUND=r2 python analysis/shapley.py     # GSM8K
ROUND=m1 python analysis/shapley.py     # MATH-500
```

### The planner does not respect its instruction

HumanEval, 5 folds × 32 problems.

| Planner prompt | Accuracy | Plan contains code |
|---|---|---|
| no planner | **0.5375** | — |
| "Do NOT write the code" | 0.4312 | 53.7% |
| no prohibition | 0.3812 | 73.8% |
| "then write the implementation" | 0.4437 | 100.0% |

Adding a planner costs 10.6 points, with the no-planner condition at or above the planner
condition in 5 of 5 folds. On maths the same prohibition is ignored in 33.3% of GSM8K problems.

Produced by `pipeline/planner_code_kernel.py` (code) and `pipeline/patch_kernel.py` (maths).

### Role labels versus three plain solver calls

`SS_anc` calls the solver three times, each pass told only "a previous attempt answered X" — the
same information flow as verification, without the verification framing.

| Cell | one generation | `PSV` | `SS_anc` | difference | tokens `PSV` / `SS_anc` |
|---|---|---|---|---|---|
| GSM8K 1.5B | 0.632 | 0.728 | **0.728** | 0.0 (2/5) | 116k / 169k |
| MATH 1.5B | 0.330 | 0.380 | 0.360 | −2.0 (3/5) | 197k / 248k |
| GSM8K 7B | 0.912 | 0.904 | 0.924 | +2.0 (2/5) | 115k / 179k |
| MATH 7B | 0.500 | 0.590 | 0.480 | **−11.0 (0/5)** | 199k / 255k |

In three of four cells the labels buy nothing measurable. The fourth does not follow, and is
reported alongside the ties.

Produced by `pipeline/budget_kernel.py` and `pipeline/budget4_kernel.py`.

### Everything else

| Result | Value | Produced by |
|---|---|---|
| Re-solving without the critique equals re-solving with it | 0.453 = 0.453 | `pipeline/budget_kernel.py` |
| LLM aggregation vs majority voting at equal budget | −19 to −26 points | `pipeline/budget_kernel.py` |
| Same-size verifier intervention accuracy | 56–59% (98% when larger) | `pipeline/wvfix_kernel.py`, `vdiv_folds_kernel.py` |
| Aggregator producing a new and correct answer | 3 in 2000 turns | `analysis/trace_novelty.py` |
| Problems no selection mechanism can reach | 57% | `analysis/difficulty_strata.py` |
| Strong model shown a wrong weak-model solution | −27.2 points | `pipeline/exposure_math_kernel.py` |
| Execution-based selection destroying solutions | 0 of 20 folds | `pipeline/execverify_kernel.py` |
| Learned error classifier, AUC → accuracy | 0.893 → +2.4 points | `pipeline/injected_classifier_kernel.py` |
| Role training methods that avoided a shortcut | 0 of 7 | `pipeline/credit_rl_kernel.py`, `orpo_kernel.py`, `maporl_kernel.py` |

## Code

```
analysis/    Shapley values, bootstrap CIs, grading, strata, trace behaviour, routing
pipeline/    experiment kernels, one file per experiment
deploy/      job launch and result collection
data/        the result files the tables above are computed from
tests/       test suite for the router
report/      LaTeX source, compiled PDF, slides, figures
```

| File | What it computes |
|---|---|
| `analysis/shapley.py`, `shapley_role7b.py`, `signed_shapley.py`, `interaction.py` | Shapley credit per role, capability variants, interaction indices |
| `analysis/role_specialization.py`, `trace_novelty.py` | Role behaviour read from execution traces |
| `analysis/difficulty_strata.py` | Stratification by how many generations are correct |
| `analysis/bootstrap.py`, `bootstrap_het.py` | Confidence intervals |
| `analysis/grade_math.py`, `regrade_math.py` | Answer grading and re-grading |
| `analysis/router.py`, `pareto_plot.py` | Routing policy and cost-accuracy frontier |
| `analysis/merge_pairs.py` | Capability-gap regression |
| `pipeline/template.py` | Shared kernel skeleton the coalition runs are built from |

The analysis scripts run against `data/` with no GPU. The kernels in `pipeline/` were written to
run on Kaggle — they read `/kaggle/input/`, write `/kaggle/working/`, and are templated at launch
by `deploy/`, so re-running one needs an account with GPU quota. See `deploy/launch_any.py`.

```bash
pytest tests/ -q
cd report && tectonic -X compile REPORT_GROUP13.tex --outdir .
```

## Notes on measurement

Three controls are applied together throughout, because they bias in opposite directions:
compute budget and choice of baseline inflate the measured benefit, while the denominator
deflates it.

The maths leakage rates are detected by comparing the last number in a plan against the gold
answer, so they are upper bounds rather than counts of deliberate computation. The code
measurement — whether the plan contains a code fence or a `def` — does not have this weakness and
is the one the argument rests on. HumanEval folds are 32 problems, smaller than the 60–100 used
to calibrate the noise floor.

Designs and evaluation criteria were fixed before running; 16 of 32 runs failed a precondition
and were discarded before results were read.

The [`archive` branch](../../tree/archive) holds the complete record: 151 kernels, 89
orchestration scripts, 40 analysis documents, and every per-run result file.
