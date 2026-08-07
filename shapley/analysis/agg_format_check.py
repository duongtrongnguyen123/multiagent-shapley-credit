#!/usr/bin/env python3
"""Aggregator có mất điểm vì LỖI TRÍCH XUẤT không? (kiểm H20 trên dữ liệu của ta)

main/H20 (460c01f) phát hiện: `A_gain` trên MATH đi từ -6.4 [-9,-4] (5/5 fold âm) lên
+1.0 [0,+2] chỉ bằng một FALLBACK MIỄN PHÍ — khi Aggregator không xuất `\\boxed{}` thì lấy
luôn đáp án của ứng viên trước đó, không tốn thêm lời gọi model. Tức phần lớn "tác hại" của
Aggregator là artifact đo đạc, không phải phán đoán kém.

Script này kiểm cùng lỗi đó trên trace aggk của chúng ta, TRƯỚC khi bỏ compute vào ORPO.
Nếu khoảng cách agg5 (.460) vs vote5 (.507) phần lớn do format, thì train preference để sửa
"phán đoán" là nhắm sai chỗ.

Chạy: python analysis/agg_format_check.py
"""
import json, re, sys, io, statistics
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]

def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0:
        return None
    i = s.find("{", i)
    if i < 0:
        return None
    d, st = 0, i
    for j in range(i, len(s)):
        if s[j] == "{":
            d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0:
                return s[st + 1:j]
    return None

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

def norm(a):
    if a is None:
        return None
    a = str(a).strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " ", ","]:
        a = a.replace(x, "")
    for x in ["\\(", "\\)", "\\[", "\\]"]:
        a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()

def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g:
        return False
    if p == g:
        return True
    try:
        return abs(float(p) - float(g)) < 1e-6
    except (ValueError, TypeError):
        return False

def pred(t):
    """bộ trích xuất GỐC của kernel: boxed, không có thì bắt 'answer is' / '='."""
    b = boxed(t)
    if b is not None:
        return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
    return m[-1].strip() if m else None

def by_fold(rows, fn):
    return [fn([t for t in rows if t["fold"] == f]) for f in sorted({t["fold"] for t in rows})]

def rep(name, vals, base=None):
    m = statistics.mean(vals)
    s = f"{name:<38} {m:>7.4f}"
    if base is not None:
        d = [v - b for v, b in zip(vals, base)]
        md = statistics.mean(d)
        same = sum(1 for x in d if x > 0) if md >= 0 else sum(1 for x in d if x < 0)
        s += f" {md:>+9.4f}  [{min(d):+.3f}, {max(d):+.3f}]  {same}/{len(d)} fold"
    print(s)
    return vals

def main():
    f = ROOT / "results_folds/aggk/traces.json"
    if not f.exists():
        print(f"chưa có {f}")
        return
    T = json.loads(f.read_text(encoding="utf-8"))
    n = len(T)

    print("=" * 78)
    print(f"AGGREGATOR — kiểm lỗi trích xuất (MATH, n={n}, 1.5B)")
    print("=" * 78)

    for arm in ("agg3", "agg5"):
        nb = sum(1 for t in T if boxed(t[arm]) is None)
        npred = sum(1 for t in T if pred(t[arm]) is None)
        print(f"  {arm}: có \\boxed {n-nb}/{n} ({100*(n-nb)/n:.1f}%) · "
              f"không boxed {nb} ({100*nb/n:.1f}%) · "
              f"không trích được gì {npred} ({100*npred/n:.1f}%)")

    # so sánh: nhóm CÓ boxed vs KHÔNG boxed, tỉ lệ sai
    print()
    for arm in ("agg3", "agg5"):
        b = [t for t in T if boxed(t[arm]) is not None]
        nb = [t for t in T if boxed(t[arm]) is None]
        wb = sum(1 for t in b if not t["ok"][arm])
        wn = sum(1 for t in nb if not t["ok"][arm])
        print(f"  {arm}: CÓ boxed sai {wb}/{len(b)} ({100*wb/len(b) if b else 0:.0f}%) | "
              f"KHÔNG boxed sai {wn}/{len(nb)} ({100*wn/len(nb) if nb else 0:.0f}%)")

    # ---- áp fallback kiểu H20 và đo lại -------------------------------------
    # fallback: nếu Aggregator không xuất boxed -> lấy đáp án của ứng viên CUỐI
    # (miễn phí, không gọi thêm model). Bản thứ hai: fallback về đa số ứng viên.
    def acc_raw(g, arm):
        return sum(1 for t in g if t["ok"][arm]) / len(g)

    def acc_fb_last(g, arm):
        hit = 0
        for t in g:
            p = boxed(t[arm])
            if p is None:
                p = t["pred"]["candidates"][-1]
            hit += eq(p, t["gold"])
        return hit / len(g)

    def acc_fb_vote(g, arm):
        hit = 0
        for t in g:
            p = boxed(t[arm])
            if p is None:
                p = t["pred"]["vote5"]
            hit += eq(p, t["gold"])
        return hit / len(g)

    print()
    print(f"{'chính sách':<38} {'acc':>7} {'Δ vs S':>9}  {'khoảng':>17}  fold")
    print("-" * 78)
    base = by_fold(T, lambda g: sum(1 for t in g if t["ok"]["S"]) / len(g))
    print(f"{'Solver một mình':<38} {statistics.mean(base):>7.4f}")
    rep("vote5 (bỏ phiếu cơ học)",
        by_fold(T, lambda g: sum(1 for t in g if t["ok"]["vote5"]) / len(g)), base)
    for arm in ("agg3", "agg5"):
        rep(f"{arm} (như đã đo)", by_fold(T, lambda g: acc_raw(g, arm)), base)
        rep(f"{arm} + fallback ứng viên cuối",
            by_fold(T, lambda g: acc_fb_last(g, arm)), base)
        rep(f"{arm} + fallback bỏ phiếu",
            by_fold(T, lambda g: acc_fb_vote(g, arm)), base)

    print()
    print("ĐỌC KẾT QUẢ: nếu fallback nâng agg lên ngang/vượt vote5 thì khoảng cách trước đây")
    print("phần lớn là LỖI ĐỊNH DẠNG, và ORPO nên nhắm vào định dạng chứ không phải phán đoán.")
    print("Nếu fallback KHÔNG thay đổi mấy thì đó là lỗi CHỌN THẬT — ORPO nhắm đúng chỗ.")

if __name__ == "__main__":
    main()
