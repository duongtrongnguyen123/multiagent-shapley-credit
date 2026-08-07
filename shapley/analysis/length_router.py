#!/usr/bin/env python3
"""Route verify theo ĐỘ DÀI lời giải — tính offline trên trace đã có, không tốn GPU.

VERIFIER_RESCUE.md: trong các ca Solver sai, lời giải NGẮN được Verifier cứu 50%, lời giải DÀI
chỉ 24%. Và Verifier ròng bằng 0 (cứu 17 / phá 18). Nếu chỉ verify khi lời giải ngắn, ta có thể
giữ phần cứu và bỏ phần phá.

Điểm mấu chốt khiến hướng này khác các routing đã thất bại (H3 gated verification, fidelity
routing): **độ dài quan sát được TRƯỚC khi verify**. Không cần biết trước câu nào sai.

Vì mọi câu trong trace đều đã có cả nhánh S lẫn nhánh V, chính sách "verify nếu len(S) < T"
tính được CHÍNH XÁC bằng cách chọn nhánh tương ứng cho từng câu — không cần chạy lại, và không
thêm nhiễu. Đây là phép đo counterfactual sạch, không phải mô phỏng.

Chạy: python analysis/length_router.py
"""
import json, sys, io, statistics
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    f = ROOT / path
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))

def policy_acc(rows, threshold):
    """acc nếu verify CHỈ KHI len(lời giải Solver) < threshold; ngược lại giữ đáp án Solver."""
    hit = 0
    for t in rows:
        use_v = t["len"]["S"] < threshold
        hit += t["ok"]["V"] if use_v else t["ok"]["S"]
    return hit / len(rows)

def by_fold(rows, fn):
    folds = sorted({t["fold"] for t in rows})
    return [fn([t for t in rows if t["fold"] == f]) for f in folds]

def summarize(name, vals, base_vals):
    diffs = [v - b for v, b in zip(vals, base_vals)]
    m = statistics.mean(diffs)
    same = sum(1 for d in diffs if d > 0) if m >= 0 else sum(1 for d in diffs if d < 0)
    return {"mean_acc": statistics.mean(vals), "delta": m,
            "min": min(diffs), "max": max(diffs),
            "folds_same_sign": f"{same}/{len(diffs)}", "name": name}

def run(path, label):
    rows = load(path)
    if not rows:
        print(f"(bỏ qua {path} — chưa tải về)")
        return
    n = len(rows)
    print("\n" + "=" * 78)
    print(f"{label}  (n={n}, {len({t['fold'] for t in rows})} fold)")
    print("=" * 78)

    always_s = by_fold(rows, lambda g: sum(t["ok"]["S"] for t in g) / len(g))
    always_v = by_fold(rows, lambda g: sum(t["ok"]["V"] for t in g) / len(g))

    print(f"{'chính sách':<34} {'acc':>7} {'Δ vs luôn-S':>12} {'khoảng':>17} {'fold cùng dấu':>14}")
    print("-" * 78)
    print(f"{'không bao giờ verify (chỉ S)':<34} {statistics.mean(always_s):>7.4f} "
          f"{0.0:>+12.4f} {'':>17} {'—':>14}")
    r = summarize("luôn verify", always_v, always_s)
    print(f"{'luôn verify (S->V, hiện tại)':<34} {r['mean_acc']:>7.4f} {r['delta']:>+12.4f} "
          f"{'[%+.3f, %+.3f]'%(r['min'],r['max']):>17} {r['folds_same_sign']:>14}")

    best = None
    for T in (100, 150, 200, 300, 400, 600):
        vals = by_fold(rows, lambda g: policy_acc(g, T))
        r = summarize(f"T={T}", vals, always_s)
        frac = sum(1 for t in rows if t["len"]["S"] < T) / n
        print(f"{'verify nếu len(S) < %d' % T:<34} {r['mean_acc']:>7.4f} {r['delta']:>+12.4f} "
              f"{'[%+.3f, %+.3f]'%(r['min'],r['max']):>17} {r['folds_same_sign']:>14}"
              f"   (verify {frac:.0%} số câu)")
        if best is None or r["delta"] > best[1]["delta"]:
            best = (T, r, frac)

    # trần oracle: verify đúng những câu mà verify có lợi (không khả thi, chỉ để so)
    orc = by_fold(rows, lambda g: sum(max(t["ok"]["S"], t["ok"]["V"]) for t in g) / len(g))
    r = summarize("oracle", orc, always_s)
    print(f"{'[trần oracle, không khả thi]':<34} {r['mean_acc']:>7.4f} {r['delta']:>+12.4f}")

    # tiết kiệm compute
    T, rb, frac = best
    print(f"\n  Ngưỡng tốt nhất T={T}: Δ {rb['delta']:+.4f} so với chỉ-S, "
          f"{rb['folds_same_sign']} fold cùng dấu")
    print(f"  So với 'luôn verify': Δ {rb['mean_acc'] - statistics.mean(always_v):+.4f} accuracy, "
          f"và chỉ tốn {frac:.0%} số lần gọi Verifier (tiết kiệm {1-frac:.0%})")

    # cơ chế: tỷ lệ cứu/phá theo nhóm độ dài
    print(f"\n  {'nhóm':<22} {'n':>4} {'S sai':>6} {'V cứu':>7} {'S đúng':>7} {'V phá':>7}")
    for lo, hi, nm in [(0, 200, "ngắn (<200)"), (200, 10**9, "dài (>=200)")]:
        g = [t for t in rows if lo <= t["len"]["S"] < hi]
        sw = [t for t in g if not t["ok"]["S"]]
        so = [t for t in g if t["ok"]["S"]]
        resc = sum(1 for t in sw if t["ok"]["V"])
        brk = sum(1 for t in so if not t["ok"]["V"])
        print(f"  {nm:<22} {len(g):>4} {len(sw):>6} {resc:>4} ({100*resc/len(sw) if sw else 0:.0f}%)"
              f" {len(so):>6} {brk:>4} ({100*brk/len(so) if so else 0:.0f}%)")

def main():
    run("results_rescue/gsm8k/traces.json", "GSM8K — route verify theo độ dài")
    run("results_rescue/math/traces.json", "MATH — route verify theo độ dài")
    print("\n" + "=" * 78)
    print("CÁCH ĐỌC: mọi câu trong trace đều đã có CẢ nhánh S lẫn nhánh V, nên chính sách route")
    print("được tính CHÍNH XÁC (counterfactual thật), không phải mô phỏng. Nhưng ngưỡng T được")
    print("chọn TRÊN CHÍNH dữ liệu này -> có overfit. Muốn kết luận phải chốt T rồi kiểm trên")
    print("tập khác. Sàn nhiễu H13 ~5 điểm ở n<=250 vẫn áp dụng.")

if __name__ == "__main__":
    main()
