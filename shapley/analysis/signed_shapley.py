#!/usr/bin/env python3
"""JANUS — Đóng góp 1: Shapley có dấu. Tách marginal của mỗi vai trò thành luồng
SỬA ĐƯỢC (0->1) và PHÁ HỎNG (1->0) ở mức từng câu, rồi cộng theo trọng số Shapley.
  phi_i = phi_i^+ - phi_i^-   (khớp Shapley cổ điển)
  eta_i = phi_i / (phi_i^+ + phi_i^-)  in [-1,1]  (độ "sạch tay")
Chạy từ preds.json đã có — không cần Kaggle."""
import os, json, math
from itertools import combinations
from pathlib import Path

ROUND = os.environ.get("ROUND", "m1")
RES = Path(__file__).resolve().parents[1] / (f"results_{ROUND}" if ROUND != "r1" else "results")
ROLES = ["P", "S", "V", "A"]
NAMES = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}

# ma trận đúng/sai theo từng câu cho 16 tổ hợp
C = {}
for d in RES.iterdir():
    pj, sj = d / "preds.json", d / "summary.json"
    if pj.exists() and sj.exists():
        mask = json.loads(sj.read_text())["mask"]
        key = frozenset(r for r in ROLES if mask[r])
        C[key] = [1 if r["correct"] else 0 for r in json.loads(pj.read_text())]
M = len(next(iter(C.values())))
n = len(ROLES)

def signed(role):
    others = [x for x in ROLES if x != role]
    fix = brk = 0.0
    for k in range(n):
        w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
        for S in combinations(others, k):
            base, plus = frozenset(S), frozenset(S) | {role}
            if base not in C or plus not in C:
                continue
            f = sum(1 for m in range(M) if C[base][m] == 0 and C[plus][m] == 1)
            b = sum(1 for m in range(M) if C[base][m] == 1 and C[plus][m] == 0)
            fix += w * f / M
            brk += w * b / M
    return fix, brk

print(f"ROUND={ROUND}  M={M} câu\n")
print(f"{'vai trò':11s} {'phi+':>8s} {'phi-':>8s} {'phi':>8s} {'eta':>7s}  diễn giải")
for r in ROLES:
    fp, fm = signed(r)
    phi = fp - fm
    eta = phi / (fp + fm) if (fp + fm) > 0 else 0.0
    tag = ("agent HỖN LOẠN (vừa sửa vừa phá)" if fp > 0.02 and fm > 0.02 and abs(eta) < 0.5
           else "chủ yếu SỬA" if eta > 0.5 else "chủ yếu PHÁ" if eta < -0.5 else "trung tính")
    print(f"{NAMES[r]:11s} {fp:+8.4f} {fm:+8.4f} {phi:+8.4f} {eta:+7.2f}  {tag}")
print("\nGhi chú: phi khớp Shapley cổ điển, nhưng (phi+,phi-) tiết lộ thứ phi che giấu.")
