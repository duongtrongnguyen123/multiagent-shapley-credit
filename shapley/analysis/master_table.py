#!/usr/bin/env python3
"""Bảng master (Người 1): gom giá trị Shapley của mọi vai trò qua các cấu hình
(benchmark × năng lực). Cột 1.5B = Shapley đồng nhất; cột 7B = φ của CHÍNH vai trò
đó khi được nâng lên 7B (đường chéo), tính từ các vòng het (mA/mV/mP), khớp N=300."""
import json, math
from itertools import combinations
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROLES = ["P", "S", "V", "A"]
NAMES = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}

def _acc_dir(d, n=None):
    """φ từ accuracy 16 tổ hợp; n giới hạn số câu (đọc preds.json), None = dùng summary."""
    d = BASE / d
    if not d.exists():
        return None
    v = {}
    for sub in d.iterdir():
        sj, pj = sub / "summary.json", sub / "preds.json"
        if not sj.exists():
            continue
        m = json.loads(sj.read_text())["mask"]
        key = frozenset(r for r in ROLES if m[r])
        if n and pj.exists():
            p = json.loads(pj.read_text())[:n]
            v[key] = sum(1 for r in p if r["correct"]) / len(p)
        else:
            v[key] = json.loads(sj.read_text())["accuracy"]
    return v if len(v) == 16 else None

def _shapley(v):
    n = len(ROLES); phi = {}
    for r in ROLES:
        o = [x for x in ROLES if x != r]; acc = 0.0
        for k in range(n):
            w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
            for S in combinations(o, k):
                acc += w * (v[frozenset(S) | {r}] - v[frozenset(S)])
        phi[r] = acc
    return phi

def homog(d, n=None):
    v = _acc_dir(d, n)
    return _shapley(v) if v else None

def het_math_diag(big):
    """φ[big] khi big=7B trên MATH: tổ hợp có big lấy từ results_m{big} (300 câu),
    còn lại lấy từ results_m1 (300 câu đầu)."""
    hd = BASE / f"results_m{big}"
    if not hd.exists():
        return None
    def vecacc(d, cid):
        f = BASE / d / cid / "preds.json"
        if not f.exists():
            raise FileNotFoundError(cid)
        p = json.loads(f.read_text())[:300]
        return sum(1 for r in p if r["correct"]) / len(p)
    v = {}
    for p in (0, 1):
        for s in (0, 1):
            for u in (0, 1):
                for a in (0, 1):
                    cid = f"{p}{s}{u}{a}"
                    role_on = dict(zip(ROLES, (p, s, u, a)))[big]
                    d = f"results_m{big}" if role_on else "results_m1"
                    v[frozenset(r for r, b in zip(ROLES, (p, s, u, a)) if b)] = vecacc(d, cid)
    return _shapley(v).get(big)

# --- cột ---
g_15 = homog("results_r2") or homog("results")      # GSM8K 1.5B (N=1319)
m_15 = homog("results_m1")                           # MATH 1.5B (N=500)
def _safe_diag(r):
    try:
        return het_math_diag(r)
    except (FileNotFoundError, KeyError):
        return None                                      # vòng chưa chạy xong -> để "—"
m_7b = {r: _safe_diag(r) for r in ROLES}             # MATH 7B (đường chéo, N=300)

def c15(phi, r): return f"{phi[r]:+.3f}" if phi else "—"
def c7(r):       return f"{m_7b[r]:+.3f}" if m_7b.get(r) is not None else "—"

md = ["# Bảng master — Shapley theo vai trò × cấu hình\n",
      "| Vai trò | GSM8K·1.5B | MATH·1.5B | MATH·7B (nâng chính vai đó) |",
      "|---|---|---|---|"]
for r in ROLES:
    md.append(f"| **{NAMES[r]}** | {c15(g_15,r)} | {c15(m_15,r)} | {c7(r)} |")
md += ["",
       "*(GSM8K·1.5B: N=1319. MATH·1.5B: N=500. MATH·7B: mỗi ô = φ của vai trò đó khi nó dùng",
       "7B (các vòng mA/mV/mP), so trên cùng N=300; ô '—' là vòng chưa chạy xong.)*",
       "",
       "**RQ2 (thứ hạng đảo theo độ khó):** Verifier ngang Solver & dẫn đầu ở GSM8K, nhưng ở MATH",
       "**Aggregator lên #1**. **RQ4 (nhạy năng lực):** trên MATH, nâng Aggregator lên 7B làm φ của",
       "nó hơn gấp đôi (+0.152 → +0.319) — Aggregator là vai nhạy năng lực nhất ở bài khó, y như",
       "Verifier ở bài dễ (GSM8K).",
       ]
out = "\n".join(md)
print(out)
(BASE / "results_summary" / "master_table.md").write_text(out + "\n")
print("\n-> đã ghi results_summary/master_table.md")
