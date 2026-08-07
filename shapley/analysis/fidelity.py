#!/usr/bin/env python3
"""Phân tầng Shapley theo Execution Fidelity (F).

Chia N câu thành F=1 (Solver trung thành với plan) và F=0 (lệch), rồi:
  1) Tính Shapley chính xác cho từng vai trò TRÊN TỪNG NHÓM (cùng công thức
     16 tổ hợp, giới hạn trên subset câu) — trả lời cho câu hỏi "Verifier đáng
     giá bao nhiêu khi Solver lệch vs khi Solver trung thành".
  2) Bootstrap 95% CI cho từng nhóm + CI cho chênh lệch phi_Verifier
     (F=0 trừ F=1) — nếu CI không chứa 0, khác biệt có ý nghĩa thống kê.
  3) Mô phỏng routing policy rẻ: F=1 -> tổ hợp PSA (bỏ Verifier), F=0 -> PSVA.

Cách dùng:
  ROUND=m1 python analysis/fidelity.py
  (ROUND, LABELS, B, SEED có thể đổi bằng env)

Đọc:
  results_<round>/*/preds.json + summary.json  (vector đúng/sai từng câu,
                                               đúng định dạng bootstrap.py đang dùng)
  results_summary/fidelity_<round>.json        (nhãn F — tạo bằng extract_fidelity.py)
Ghi:
  results_summary/fidelity_<round>_results.json
"""
import os, json, math, random
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUND = os.environ.get("ROUND", "m1")
RES = ROOT / (f"results_{ROUND}" if ROUND != "r1" else "results")
LABELS = Path(os.environ.get("LABELS", ROOT / "results_summary" / f"fidelity_{ROUND}.json"))
OUT = ROOT / "results_summary" / f"fidelity_{ROUND}_results.json"
B = int(os.environ.get("B", "2000"))
random.seed(int(os.environ.get("SEED", "0")))

ROLES = ["P", "S", "V", "A"]
NAMES = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}

C = {}  # tổ hợp (frozenset vai trò) -> list[0/1] đúng/sai theo câu


def load_correctness():
    global C
    for d in RES.iterdir():
        pj, sj = d / "preds.json", d / "summary.json"
        if pj.exists() and sj.exists():
            mask = json.loads(sj.read_text())["mask"]
            key = frozenset(r for r in ROLES if mask[r])
            C[key] = [1 if p["correct"] else 0 for p in json.loads(pj.read_text())]
    if len(C) != 16:
        have = set(C)
        miss = ["".join(sorted(S)) or "empty"
                for k in range(5) for S in combinations(ROLES, k)
                if frozenset(S) not in have]
        raise SystemExit(f"mới có {len(C)}/16 tổ hợp, thiếu {miss}.\n"
                         f"  -> Chạy ROUND={ROUND} python deploy/sync_once.py tới khi DONE 16/16.")
    n = len(next(iter(C.values())))
    if not all(len(v) == n for v in C.values()):
        raise SystemExit("số câu giữa các tổ hợp không khớp — kiểm tra results_<round>/")
    return n


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


def ci(xs):
    xs = sorted(xs)
    return xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs))]


def main():
    N = load_correctness()

    if not LABELS.exists():
        raise SystemExit(f"không tìm thấy {LABELS} — chạy analysis/extract_fidelity.py trước")
    raw = json.loads(LABELS.read_text())
    labels = raw["labels"] if isinstance(raw, dict) else raw
    if len(labels) != N:
        raise SystemExit(f"#nhãn F ({len(labels)}) != #câu trong results ({N}) — "
                         f"phải cùng N và cùng thứ tự câu")

    idx1 = [i for i in range(N) if labels[i] == 1]
    idx0 = [i for i in range(N) if labels[i] == 0]
    if not idx1 or not idx0:
        raise SystemExit(f"nhóm rỗng: F=1 có {len(idx1)} câu, F=0 có {len(idx0)} câu — "
                         f"cần cả hai nhóm mới phân tầng được")

    # bootstrap lồng nhau: mỗi lần rút lại (có hoàn lại) trong TỪNG nhóm
    dist = {"F=1": {r: [] for r in ROLES}, "F=0": {r: [] for r in ROLES}}
    dist_diff = []  # phi_V(F=0) - phi_V(F=1)
    for _ in range(B):
        bs1 = [random.choice(idx1) for _ in range(len(idx1))]
        bs0 = [random.choice(idx0) for _ in range(len(idx0))]
        ph1 = shapley_from_acc(acc_on(bs1))
        ph0 = shapley_from_acc(acc_on(bs0))
        for r in ROLES:
            dist["F=1"][r].append(ph1[r])
            dist["F=0"][r].append(ph0[r])
        dist_diff.append(ph0["V"] - ph1["V"])

    v1, v0 = acc_on(idx1), acc_on(idx0)
    phi1, phi0 = shapley_from_acc(v1), shapley_from_acc(v0)
    full, S = frozenset(ROLES), frozenset("S")

    print(f"=== Execution Fidelity — Shapley phân tầng (ROUND={ROUND}, B={B}, n={N}) ===")
    print(f"{'nhóm':16s} {'n':>5s} {'SolverAcc':>9s} {'FullAcc':>8s}")
    for tag, idx in (("F=1 (trung thành)", idx1), ("F=0 (lệch)", idx0)):
        sa = sum(C[S][i] for i in idx) / len(idx)
        fa = sum(C[full][i] for i in idx) / len(idx)
        print(f"{tag:16s} {len(idx):5d} {sa:9.4f} {fa:8.4f}")

    print(f"\n{'vai trò':11s} {'F=1 phi':>10s} {'F=1 95% CI':>18s}   "
          f"{'F=0 phi':>10s} {'F=0 95% CI':>18s}   Δ(F=0−F=1)")
    for r in ROLES:
        lo1, hi1 = ci(dist["F=1"][r])
        lo0, hi0 = ci(dist["F=0"][r])
        print(f"{NAMES[r]:11s} {phi1[r]:>+10.4f} [{lo1:+.4f},{hi1:+.4f}]   "
              f"{phi0[r]:>+10.4f} [{lo0:+.4f},{hi0:+.4f}]   {phi0[r] - phi1[r]:+.4f}")

    lo_d, hi_d = ci(dist_diff)
    p_gt0 = sum(x > 0 for x in dist_diff) / B
    print(f"\nVerifier Δ = phi(F=0) − phi(F=1) = {phi0['V'] - phi1['V']:+.4f}  "
          f"95% CI [{lo_d:+.4f}, {hi_d:+.4f}]  P(Δ>0) = {p_gt0:.3f}")

    # routing policy rẻ: F=1 -> PSA (bỏ Verifier), F=0 -> PSVA
    r_f1, r_f0 = frozenset("PSA"), frozenset("PSVA")
    routed = (sum(C[r_f1][i] for i in idx1) + sum(C[r_f0][i] for i in idx0)) / N
    full_acc = sum(C[full]) / N
    print(f"\nRouting rẻ (F=1 -> {''.join(sorted(r_f1))}, F=0 -> {''.join(sorted(r_f0))}):")
    print(f"  full 1111        = {full_acc:.4f}")
    print(f"  routed           = {routed:.4f}  (Δ {routed - full_acc:+.4f})")
    print(f"  bỏ Verifier ở {len(idx1) / N:.1%} câu (F=1)")

    out = {
        "round": ROUND, "n": N,
        "n_faithful": len(idx1), "n_deviant": len(idx0),
        "solver_acc": {"F=1": sum(C[S][i] for i in idx1) / len(idx1),
                       "F=0": sum(C[S][i] for i in idx0) / len(idx0)},
        "full_acc": {"F=1": sum(C[full][i] for i in idx1) / len(idx1),
                     "F=0": sum(C[full][i] for i in idx0) / len(idx0),
                     "all": full_acc},
        "shapley": {"F=1": phi1, "F=0": phi0},
        "bootstrap": {tag: {r: {"ci_low": ci(dist[tag][r])[0],
                                "ci_high": ci(dist[tag][r])[1],
                                "p_negative": sum(x < 0 for x in dist[tag][r]) / B}
                            for r in ROLES} for tag in ("F=1", "F=0")},
        "verifier_diff": {"delta": phi0["V"] - phi1["V"],
                          "ci_low": lo_d, "ci_high": hi_d,
                          "p_gt0": p_gt0},
        "routing": {"coalition_f1": "PSA", "coalition_f0": "PSVA",
                    "full_acc": full_acc, "routed_acc": routed,
                    "delta": routed - full_acc,
                    "skip_verifier_frac": len(idx1) / N},
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nđã ghi {OUT}")


if __name__ == "__main__":
    main()
