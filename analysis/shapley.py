#!/usr/bin/env python3
"""Compute exact Shapley credit for each role from the 16 coalition accuracies.
phi_i = sum_{S subset N\{i}} |S|!(n-|S|-1)!/n! * (v(S+i) - v(S)), n=4 roles."""
import os, json, math
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUND = os.environ.get("ROUND", "r1")
RES = ROOT / "data" / (f"results_{ROUND}" if ROUND != "r1" else "results")
ROLES = ["P", "S", "V", "A"]
NAMES = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}

def load_v():
    v = {}
    for cid_dir in RES.iterdir():
        sm = cid_dir / "summary.json"
        if sm.exists():
            d = json.loads(sm.read_text())
            v[frozenset(r for r in ROLES if d["mask"][r])] = d["accuracy"]
    return v

def shapley(v):
    n = len(ROLES)
    phi = {r: 0.0 for r in ROLES}
    others = lambda r: [x for x in ROLES if x != r]
    for r in ROLES:
        for k in range(n):                       # size of coalition S (without r)
            w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
            for S in combinations(others(r), k):
                fs, fsr = frozenset(S), frozenset(S) | {r}
                if fs in v and fsr in v:
                    phi[r] += w * (v[fsr] - v[fs])
    return phi

def main():
    v = load_v()
    print(f"loaded {len(v)}/16 coalitions")
    full = v.get(frozenset(ROLES))
    empty = v.get(frozenset())
    print(f"v(full PSVA) = {full}   v(empty) = {empty}\n")
    # single-role accuracies + full leave-one-out for context
    print("Coalition accuracies:")
    for size in range(5):
        for S in combinations(ROLES, size):
            fs = frozenset(S)
            if fs in v:
                label = "".join(S) or "-"
                print(f"  {label:<9} = {v[fs]:.4f}")
    if len(v) < 16:
        print(f"\nWARNING: only {len(v)}/16 coalitions present; Shapley is partial.")
        return
    phi = shapley(v)
    tot = sum(phi.values())
    print("\n=== SHAPLEY CREDIT (share of team accuracy attributable to each role) ===")
    for r in sorted(ROLES, key=lambda x: -phi[x]):
        loo = v[frozenset(ROLES)] - v[frozenset(set(ROLES) - {r})]
        lazy = " <-- LAZY (~0)" if abs(phi[r]) < 0.01 else ""
        print(f"  {NAMES[r]:11s} phi={phi[r]:+.4f}   leave-one-out Δ={loo:+.4f}{lazy}")
    print(f"\n  sum(phi)={tot:+.4f}  (should equal v(full)-v(empty)={full-empty:+.4f})")
    out = {"shapley": phi, "coalitions": {",".join(sorted(k)) or "empty": val
                                          for k, val in v.items()},
           "v_full": full, "v_empty": empty}
    (ROOT / "results_summary" / "shapley_results.json").write_text(json.dumps(out, indent=2))
    print("\nwrote shapley_results.json")

if __name__ == "__main__":
    main()
