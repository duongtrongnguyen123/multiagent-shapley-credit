#!/usr/bin/env python3
"""Chấm lại MATH offline từ preds.json bằng grader sympy (grade_math.math_equal:
tương đương đại số, xử lý phân số/biểu thức/khoảng/chữ) và SO SÁNH với grader naive
(chuỗi + số) để thấy độ lệch. Ghi correct vào preds.json/summary.json cho shapley.py
dùng. Không cần chạy Kaggle lại.  Cần: pip install sympy."""
import os, re, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from grade_math import math_equal

ROUND = os.environ.get("ROUND", "m1")
RES = Path(__file__).resolve().parents[1] / (f"results_{ROUND}" if ROUND != "r1" else "results")

def naive_eq(p, g):
    def norm(a):
        a = str(a).strip()
        for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " "]:
            a = a.replace(x, "")
        a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
        return a.rstrip(".").strip("{}").lower()
    if p is None or g is None:
        return False
    p, g = norm(p), norm(g)
    if not p or not g:
        return False
    if p == g:
        return True
    try:
        return abs(float(p) - float(g)) < 1e-6
    except (ValueError, TypeError):
        return False

rows = []
for d in sorted(RES.iterdir()):
    pj, sj = d / "preds.json", d / "summary.json"
    if not (pj.exists() and sj.exists()):
        continue
    preds = json.loads(pj.read_text())
    old = sum(naive_eq(r["pred"], r["gold"]) for r in preds)
    new = changed = 0
    for r in preds:
        ok = math_equal(r["pred"], r["gold"])
        if ok != naive_eq(r["pred"], r["gold"]):
            changed += 1
        r["correct"] = ok
        new += ok
    sm = json.loads(sj.read_text())
    sm["correct"], sm["accuracy"] = new, new / len(preds)
    json.dump(sm, open(sj, "w"), indent=2)
    json.dump(preds, open(pj, "w"))
    rows.append((d.name, old / len(preds), new / len(preds), changed))

print(f"{'tổ hợp':8s} {'naive':>7s} {'sympy':>7s} {'Δ':>7s}  #đổi")
tot_o = tot_n = 0
for cid, o, n, ch in sorted(rows):
    tot_o += o
    tot_n += n
    print(f"{cid:8s} {o:7.4f} {n:7.4f} {n-o:+7.4f}  {ch}")
k = len(rows)
print(f"\nTB accuracy: naive {tot_o/k:.4f} -> sympy {tot_n/k:.4f}  (Δ {(tot_n-tot_o)/k:+.4f})")
print(f"Đã ghi lại {k} tổ hợp trong {RES.name}/ — chạy shapley.py để xem Shapley mới.")
