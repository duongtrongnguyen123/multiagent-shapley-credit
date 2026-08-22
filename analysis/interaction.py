#!/usr/bin/env python3
r"""Chỉ số tương tác Shapley (Grabisch–Roubens) từng CẶP vai trò, từ 16 accuracy tổ hợp.
I_ij > 0 = SYNERGY (bổ trợ, cùng nhau hơn tổng riêng); I_ij < 0 = SUBSTITUTION (thay thế/thừa).
  I_ij = Σ_{S⊆N\{i,j}} w(|S|) [v(S∪ij) − v(S∪i) − v(S∪j) + v(S)],  n=4.
Chạy: `python analysis/interaction.py` (mặc định GSM8K=results_r2 + MATH=results_m1)."""
import os, json, math
from itertools import combinations
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROLES = ["P", "S", "V", "A"]
NM = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}

def load_v(d):
    d = BASE / d
    v = {}
    for sub in d.iterdir() if d.exists() else []:
        sj = sub / "summary.json"
        if sj.exists():
            s = json.loads(sj.read_text())
            v[frozenset(r for r in ROLES if s["mask"][r])] = s["accuracy"]
    return v if len(v) == 16 else None

def interaction(v):
    n = 4
    out = {}
    for i, j in combinations(ROLES, 2):
        rest = [x for x in ROLES if x not in (i, j)]
        I = 0.0
        for k in range(len(rest) + 1):
            w = math.factorial(k) * math.factorial(n - k - 2) / math.factorial(n - 1)
            for S in combinations(rest, k):
                s = frozenset(S)
                I += w * (v[s | {i, j}] - v[s | {i}] - v[s | {j}] + v[s])
        out[(i, j)] = I
    return out

for name, d in [("GSM8K", "results_r2"), ("MATH", "results_m1")]:
    v = load_v(d)
    if not v:
        print(f"{name}: thiếu data ({d})"); continue
    I = interaction(v)
    print(f"\n=== {name} — interaction index từng cặp ===")
    for (i, j), val in sorted(I.items(), key=lambda x: x[1]):
        tag = "SYNERGY (bổ trợ)" if val > 0.01 else "SUBSTITUTE (thay thế)" if val < -0.01 else "~độc lập"
        print(f"  {NM[i]:10s} × {NM[j]:10s} : {val:+.3f}  {tag}")
    json.dump({f"{i}-{j}": val for (i, j), val in I.items()},
              open(BASE / "results_summary" / f"interaction_{name.lower()}.json", "w"), indent=2)
