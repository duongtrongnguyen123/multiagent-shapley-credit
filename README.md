# Role Specialisation in Multi-Agent LLM Pipelines: An Empirical Study

This repository contains the code, experiment records and report for a study of whether the
roles in a planner/solver/verifier/aggregator pipeline perform the functions they are named for.
Report: [`report/REPORT_GROUP13.pdf`](report/REPORT_GROUP13.pdf) (29 pages).

Course project, Natural Language Processing (INT3406), VNU University of Engineering and
Technology. Group 13: Dương Trọng Nguyên, Trương Đình Đức, Trần Tùng Dương, Lê Hoàng Quân.

## Requirements

```bash
pip install torch transformers datasets accelerate peft trl \
            numpy scipy scikit-learn sympy matplotlib pytest
pip install "kaggle>=2.0"     # from git, not PyPI: the PyPI CLI drops machine_shape
```

Experiments run as Kaggle kernels on 2×T4. Credentials are read from a file outside the
repository; nothing is committed.

```bash
export ACCOUNTS_FILE=/path/to/accounts.txt    # one line per account: <username> <token>
export KAGGLE_RTX_ACCOUNT=<username>          # only for the runs needing a larger GPU
```

## Repository structure

```
analysis/    Shapley values, bootstrap CIs, grading, strata, trace behaviour, routing
pipeline/    experiment kernels — one file per experiment, each self-contained
deploy/      job launch, result collection, account rotation
tests/       test suite for the router
report/      LaTeX source, compiled PDF, slides, figures
```

The [`archive` branch](../../tree/archive) holds the complete record: 151 kernels, 89
orchestration scripts, 40 analysis documents, and every per-run result file.

## Running experiments

Each kernel is one experiment. Launch one, then collect its results:

```bash
python deploy/launch_any.py <kernel_name>     # e.g. roleablate_kernel
python deploy/collect.py <kernel_name>
```

Analysis scripts read the collected result files and print the tables used in the report:

```bash
python analysis/shapley.py
python analysis/role_specialization.py
python analysis/difficulty_strata.py
```

## Results

All figures below are five-fold means at a single model size unless stated. Effect sizes are read
against a measured noise floor of 2.65 points standard deviation between folds, giving an
effective threshold of about 3.3 points.

### Role credit, with the solver held fixed (§5.3)

Shapley values over the eight coalitions containing the solver. Scale 0–1, 95% bootstrap CI.

| Role | GSM8K (N=1319) | MATH-500 (N=500) |
|---|---|---|
| Planner | −0.0188 [−0.0399; +0.0021] | +0.0210 [−0.0137; +0.0540] |
| Verifier | **+0.0555** [+0.0430; +0.0675] | −0.0050 [−0.0257; +0.0150] |
| Aggregator | **+0.0126** [+0.0052; +0.0202] | +0.0040 [−0.0100; +0.0187] |

Given a solver, the other three roles add 4.9 points on GSM8K and nothing distinguishable from
zero on MATH-500.

```bash
python deploy/launch_any.py roleablate_kernel && python analysis/shapley.py
```

### The planner does not respect its instruction (§5.4)

HumanEval, 5 folds × 32 problems.

| Planner prompt | Accuracy | Plan contains code |
|---|---|---|
| no planner | **0.5375** | — |
| "Do NOT write the code" | 0.4312 | 53.7% |
| no prohibition | 0.3812 | 73.8% |
| "then write the implementation" | 0.4437 | 100.0% |

Adding a planner costs 10.6 points, with the no-planner condition at or above the planner
condition in 5 of 5 folds.

```bash
python deploy/launch_any.py planner_code_kernel    # code
python deploy/launch_any.py patch_kernel           # maths, HIDE/FREE/ASK
```

### Role labels versus three plain solver calls (§5.2)

`SS_anc` calls the solver three times, each pass told only "a previous attempt answered X".

| Cell | one generation | `PSV` | `SS_anc` | difference | tokens `PSV` / `SS_anc` |
|---|---|---|---|---|---|
| GSM8K 1.5B | 0.632 | 0.728 | **0.728** | 0.0 (2/5) | 116k / 169k |
| MATH 1.5B | 0.330 | 0.380 | 0.360 | −2.0 (3/5) | 197k / 248k |
| GSM8K 7B | 0.912 | 0.904 | 0.924 | +2.0 (2/5) | 115k / 179k |
| MATH 7B | 0.500 | 0.590 | 0.480 | **−11.0 (0/5)** | 199k / 255k |

```bash
python deploy/launch_any.py budget_kernel
python deploy/launch_any.py budget4_kernel
```

### Other measurements

| Result | Value | Reproduce |
|---|---|---|
| Re-solving without the critique equals re-solving with it | 0.453 = 0.453 | `budget_kernel` |
| LLM aggregation vs majority voting at equal budget | −19 to −26 points | `budget_kernel` |
| Same-size verifier intervention accuracy | 56–59% (98% when larger) | `wvfix_kernel`, `vdiv_folds_kernel` |
| Aggregator producing a new and correct answer | 3 in 2000 turns | `analysis/trace_novelty.py` |
| Problems no selection mechanism can reach | 57% | `analysis/difficulty_strata.py` |
| Strong model shown a wrong weak-model solution | −27.2 points | `exposure_math_kernel` |
| Execution-based selection destroying solutions | 0 of 20 folds | `execverify_kernel` |
| Learned error classifier, AUC → accuracy | 0.893 → +2.4 points | `injected_classifier_kernel` |
| Role training methods that avoided a shortcut | 0 of 7 | `credit_rl_kernel`, `orpo_kernel`, `maporl_kernel` |

## Notes on measurement

Three controls are applied together throughout, because they bias in opposite directions:
compute budget and choice of baseline inflate the measured benefit, while the denominator
deflates it.

The maths leakage rates are detected by comparing the last number in a plan against the gold
answer, so they are upper bounds rather than counts of deliberate computation. The code
measurement — whether the plan contains a code fence or a `def` — does not have this weakness and
is the one the argument rests on. HumanEval folds are 32 problems, smaller than the 60–100 used
to calibrate the noise floor. The one cell where the named pipeline clearly beats an unlabelled
one (MATH at 7B) is reported alongside the ties.

Designs and evaluation criteria were fixed before running; 16 of 32 runs failed a precondition
and were discarded before results were read.

## Tests

```bash
pytest tests/ -q
```

## Report

```bash
cd report && tectonic -X compile REPORT_GROUP13.tex --outdir .
```
