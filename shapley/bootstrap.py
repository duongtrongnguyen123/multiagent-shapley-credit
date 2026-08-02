#!/usr/bin/env python3
"""Bootstrap CIs on per-role Shapley credit using the aligned per-question
correctness vectors (same 300 questions across all 16 coalitions).
No Kaggle rerun needed — resample questions, recompute v(S) and Shapley."""
import os, json, math, random
from itertools import combinations
from pathlib import Path

ROUND = os.environ.get("ROUND", "r1")
_base = Path("/Users/hduong/dev/qwen-gsm8k-kaggle/shapley")
RES = _base / (f"results_{ROUND}" if ROUND != "r1" else "results")
ROLES = ["P", "S", "V", "A"]
NAMES = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}
random.seed(0)

# correctness matrix: coalition frozenset -> list[0/1] over the 300 questions
C = {}
for d in RES.iterdir():
    pj, sj = d / "preds.json", d / "summary.json"
    if pj.exists() and sj.exists():
        mask = json.loads(sj.read_text())["mask"]
        key = frozenset(r for r in ROLES if mask[r])
        C[key] = [1 if p["correct"] else 0 for p in json.loads(pj.read_text())]
N = len(next(iter(C.values())))
assert len(C) == 16

def shapley_from_acc(v):
    n = len(ROLES)
    phi = {r: 0.0 for r in ROLES}
    for r in ROLES:
        others = [x for x in ROLES if x != r]
        for k in range(n):
            w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
            for S in combinations(others, k):
                phi[r] += w * (v[frozenset(S) | {r}] - v[frozenset(S)])
    return phi

def acc_on(idx):
    return {key: sum(vec[i] for i in idx) / len(idx) for key, vec in C.items()}

point = shapley_from_acc(acc_on(range(N)))

B = 5000
dist = {r: [] for r in ROLES}
for _ in range(B):
    idx = [random.randrange(N) for _ in range(N)]
    phi = shapley_from_acc(acc_on(idx))
    for r in ROLES:
        dist[r].append(phi[r])

def ci(xs):
    xs = sorted(xs)
    return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs))]

print(f"Bootstrap Shapley CIs  (N={N} questions, B={B} resamples)\n")
print(f"{'role':11s} {'phi':>8s}  {'95% CI':>18s}   P(phi<0)")
rows = []
for r in sorted(ROLES, key=lambda x: -point[x]):
    lo, hi = ci(dist[r])
    p_neg = sum(x < 0 for x in dist[r]) / B
    flag = "  <-- LAZY/negative" if hi < 0.02 else ""
    print(f"{NAMES[r]:11s} {point[r]:+.4f}  [{lo:+.4f}, {hi:+.4f}]   {p_neg:.3f}{flag}")
    rows.append({"role": NAMES[r], "phi": point[r], "ci_low": lo, "ci_high": hi,
                 "p_negative": p_neg})
json.dump({"n": N, "B": B, "roles": rows},
          open(RES.parent / "bootstrap_results.json", "w"), indent=2)
print("\nwrote bootstrap_results.json")
