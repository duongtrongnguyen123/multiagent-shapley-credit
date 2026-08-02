#!/usr/bin/env python3
"""Bootstrap CI on the Planner's Shapley credit with a 7B planner, and on the
flip Δ vs the 1.5B baseline. Uses aligned per-question correctness (same 300
questions): P=0 from results/ (round1), P=1 from results_r3/ (7B planner)."""
import json, math, random
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R1, R3 = ROOT / "results", ROOT / "results_r3"
ROLES = ["P", "S", "V", "A"]
random.seed(0)

def vec(d, cid):
    return [1 if p["correct"] else 0 for p in json.loads((d / cid / "preds.json").read_text())]

# correctness matrices for baseline (1.5B planner) and het (7B planner)
base, het = {}, {}
for p in (0, 1):
    for s in (0, 1):
        for v in (0, 1):
            for a in (0, 1):
                cid = f"{p}{s}{v}{a}"
                key = frozenset(r for r, b in zip(ROLES, (p, s, v, a)) if b)
                base[key] = vec(R1, cid)
                het[key] = vec(R3, cid) if p == 1 else vec(R1, cid)
N = len(base[frozenset(ROLES)])

def shap(mat, idx, role):
    accs = {k: sum(v[i] for i in idx) / len(idx) for k, v in mat.items()}
    others = [x for x in ROLES if x != role]
    phi = 0.0
    for k in range(4):
        w = math.factorial(k) * math.factorial(3 - k) / math.factorial(4)
        for S in combinations(others, k):
            phi += w * (accs[frozenset(S) | {role}] - accs[frozenset(S)])
    return phi

full = list(range(N))
pt_b, pt_h = shap(base, full, "P"), shap(het, full, "P")
B = 5000
d_h, d_flip = [], []
for _ in range(B):
    idx = [random.randrange(N) for _ in range(N)]
    hb, hh = shap(base, idx, "P"), shap(het, idx, "P")
    d_h.append(hh)
    d_flip.append(hh - hb)

def ci(xs):
    xs = sorted(xs); return xs[int(.025 * len(xs))], xs[int(.975 * len(xs))]

lo_h, hi_h = ci(d_h)
lo_f, hi_f = ci(d_flip)
print(f"Planner phi  (7B planner):  {pt_h:+.4f}  95% CI [{lo_h:+.4f}, {hi_h:+.4f}]  "
      f"P(phi>0)={sum(x>0 for x in d_h)/B:.3f}")
print(f"Flip Δ (7B - 1.5B planner): {pt_h-pt_b:+.4f}  95% CI [{lo_f:+.4f}, {hi_f:+.4f}]  "
      f"P(Δ>0)={sum(x>0 for x in d_flip)/B:.3f}")
json.dump({"phi_7b": pt_h, "phi_7b_ci": [lo_h, hi_h],
           "flip": pt_h - pt_b, "flip_ci": [lo_f, hi_f]},
          open(ROOT / "results_summary" / "bootstrap_het_results.json", "w"), indent=2)
