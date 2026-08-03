#!/usr/bin/env python3
"""Bảng master (Người 1): gom giá trị Shapley của mọi vai trò qua các cấu hình
(benchmark × năng lực) vào một bảng, xuất Markdown cho báo cáo. Đọc từ results_*/
đã có; ô nào chưa chạy (mA/mV/mP) để trống."""
import json, math
from itertools import combinations
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROLES = ["P", "S", "V", "A"]
NAMES = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}

def shapley_from_dir(d):
    """Tính φ từ accuracy 16 tổ hợp trong thư mục results."""
    d = BASE / d
    if not d.exists():
        return None
    v = {}
    for sub in d.iterdir():
        sj = sub / "summary.json"
        if sj.exists():
            s = json.loads(sj.read_text())
            m = s["mask"]
            v[frozenset(r for r in ROLES if m[r])] = s["accuracy"]
    if len(v) < 16:
        return None
    n = len(ROLES)
    phi = {}
    for r in ROLES:
        others = [x for x in ROLES if x != r]
        acc = 0.0
        for k in range(n):
            w = math.factorial(k) * math.factorial(n - k - 1) / math.factorial(n)
            for S in combinations(others, k):
                fs, fsr = frozenset(S), frozenset(S) | {r}
                if fs in v and fsr in v:
                    acc += w * (v[fsr] - v[fs])
        phi[r] = acc
    return phi

# Nguồn cho từng cấu hình đồng nhất 1.5B (ô nào thiếu -> None)
configs = {
    "GSM8K·1.5B": shapley_from_dir("results_r2") or shapley_from_dir("results"),
    "MATH·1.5B":  shapley_from_dir("results_m1"),
    # Các vòng 7B (capacity) sẽ điền khi chạy xong — placeholder:
    "MATH·7B*":   shapley_from_dir("results_mA_full") if False else None,
}

cols = [c for c in configs]
def cell(cfg, r):
    phi = configs[cfg]
    return f"{phi[r]:+.3f}" if phi else "—"

md = ["# Bảng master — Shapley theo vai trò × cấu hình\n",
      "| Vai trò | " + " | ".join(cols) + " |",
      "|---|" + "|".join("---" for _ in cols) + "|"]
for r in ROLES:
    md.append(f"| **{NAMES[r]}** | " + " | ".join(cell(c, r) for c in cols) + " |")
md += ["",
       "*(GSM8K·1.5B từ N=1319; MATH·1.5B từ N=500, chấm sympy. Cột 7B điền khi mA/mV/mP xong.)*",
       "",
       "**Đọc nhanh (RQ2 — thứ hạng đảo theo độ khó):** Verifier ngang Solver và dẫn đầu trên",
       "GSM8K, nhưng trên MATH thì **Aggregator vươn lên #1**, Verifier tụt ngang Solver; Planner",
       "từ đóng-góp-âm (GSM8K) sang ~trung tính (MATH).",
       ]
out = "\n".join(md)
print(out)
(BASE / "results_summary" / "master_table.md").write_text(out + "\n")
print("\n-> đã ghi results_summary/master_table.md")
