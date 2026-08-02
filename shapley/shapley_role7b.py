#!/usr/bin/env python3
"""Round 3 analysis: Shapley with a 7B planner. P=0 coalitions reused from round 1
(results/, all-1.5B, N=300); P=1 coalitions from results_r3/ (7B planner, N=300).
Compares Planner credit vs the all-1.5B round-1 baseline to separate inherent harm
from weak-model capacity."""
import json, math
from itertools import combinations
from pathlib import Path

ROOT = Path("/Users/hduong/dev/qwen-gsm8k-kaggle/shapley")
import os
BIG=os.environ["BIG"]; ROUND=os.environ.get("ROUND","r4")
R1, R3 = ROOT/"results", ROOT/f"results_{ROUND}"
ROLES = ["P", "S", "V", "A"]
NAMES = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}

def acc(d, cid):
    f = d / cid / "summary.json"
    return json.loads(f.read_text())["accuracy"] if f.exists() else None

def load(planner_source):
    """planner_source=R3 -> heterogeneous (7B planner); =R1 -> all-1.5B baseline."""
    v, missing = {}, []
    for p in (0, 1):
        for s in (0, 1):
            for vv in (0, 1):
                for a in (0, 1):
                    cid = f"{p}{s}{vv}{a}"
                    big_on = dict(zip(ROLES,(p,s,vv,a)))[BIG]
                    src = (planner_source if big_on else R1)
                    val = acc(src, cid)
                    if val is None:
                        missing.append(cid)
                    else:
                        v[frozenset(r for r, b in zip(ROLES, (p, s, vv, a)) if b)] = val
    return v, missing

def shapley(v):
    n = len(ROLES); phi = {r: 0.0 for r in ROLES}
    for r in ROLES:
        others = [x for x in ROLES if x != r]
        for k in range(n):
            w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
            for S in combinations(others, k):
                fs, fsr = frozenset(S), frozenset(S) | {r}
                if fs in v and fsr in v:
                    phi[r] += w * (v[fsr] - v[fs])
    return phi

het, missing = load(R3)
base, _ = load(R1)
if missing:
    print(f"waiting on {len(missing)} r3 coalitions: {missing}")
    import sys; sys.exit(0)

print(f"{BIG}=1 coalition accuracies  (1.5B -> 7B {BIG}):")
for key in [k for k in het if BIG in k]:
    b1 = base.get(key); h = het.get(key)
    print(f"  {''.join(sorted(key)):5s}  {b1:.4f} -> {h:.4f}  ({h-b1:+.4f})")

phi_h, phi_b = shapley(het), shapley(base)
print(f"\n=== {BIG} CREDIT: 1.5B vs 7B for role {BIG} ===")
print(f"{'role':11s} {'1.5B-planner':>13s} {'7B-planner':>12s} {'Δ':>9s}")
for r in ROLES:
    print(f"{NAMES[r]:11s} {phi_b[r]:>+13.4f} {phi_h[r]:>+12.4f} {phi_h[r]-phi_b[r]:>+9.4f}")
print(f"\nv(full) all-1.5B = {base[frozenset(ROLES)]:.4f}   "
      f"7B-planner = {het[frozenset(ROLES)]:.4f}")
verdict = f"{BIG}: phi {phi_b[BIG]:+.4f} (1.5B) -> {phi_h[BIG]:+.4f} (7B), delta {phi_h[BIG]-phi_b[BIG]:+.4f}"
print("VERDICT:", verdict)
json.dump({"phi_1p5b_planner": phi_b, "phi_7b_planner": phi_h,
           "verdict": verdict}, open(ROOT / f"shapley_{ROUND}_results.json", "w"), indent=2)
print("wrote shapley_het_results.json")
