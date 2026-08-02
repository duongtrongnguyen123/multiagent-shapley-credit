#!/usr/bin/env python3
"""Re-grade MATH coalitions offline from stored preds.json with an improved grader
(keeps \\text{} content instead of deleting it, so distinct text answers no longer
spuriously match). Rewrites accuracy/correct in each summary.json. No Kaggle rerun."""
import os, re, json
from pathlib import Path

ROUND = os.environ.get("ROUND", "m1")
RES = Path(__file__).resolve().parents[1] / f"results_{ROUND}"

def norm(a):
    if a is None:
        return None
    a = a.strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "\\ ", "\\quad", "\\qquad"]:
        a = a.replace(x, "")
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)    # KEEP content
    a = re.sub(r"\\mbox\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("\\$", "").replace("$", "").replace(" ", "")
    a = a.replace("\\%", "").replace("%", "").replace("^{\\circ}", "").replace("^\\circ", "")
    a = a.replace("\\cdot", "*").replace("dollars", "")
    return a.strip().rstrip(".").strip("{}").lower()

def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g:            # empty pred/gold never counts as a match
        return False
    if p == g:
        return True
    try:
        return abs(float(p) - float(g)) < 1e-6
    except (ValueError, TypeError):
        return False

changed = []
for d in sorted(RES.iterdir()):
    pj, sj = d / "preds.json", d / "summary.json"
    if not (pj.exists() and sj.exists()):
        continue
    preds = json.loads(pj.read_text())
    corr = 0
    for r in preds:
        ok = eq(r["pred"], r["gold"])
        r["correct"] = ok
        corr += ok
    sm = json.loads(sj.read_text())
    old = sm.get("accuracy")
    sm["correct"], sm["accuracy"] = corr, corr / len(preds)
    json.dump(sm, open(sj, "w"), indent=2)
    json.dump(preds, open(pj, "w"))
    changed.append((d.name, old, sm["accuracy"]))

for cid, old, new in changed:
    print(f"  {cid}: {old:.4f} -> {new:.4f}" if old is not None else f"  {cid}: -> {new:.4f}")
print(f"re-graded {len(changed)} coalitions in results_{ROUND}/")
