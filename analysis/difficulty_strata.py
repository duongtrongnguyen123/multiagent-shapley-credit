#!/usr/bin/env python3
"""Verifier chỉ hữu ích ở GIỮA dải độ khó? — phân tầng theo độ khó TỪNG CÂU.

Bốn ô của lưới (`ROLE_SPECIALIZATION.md`) xếp theo accuracy của Solver cho một mẫu hình rõ:
  MATH 1.5B .402 (quá tải) · GSM8K 1.5B .632 · MATH 7B .720 · GSM8K 7B .910 (bão hoà)
và V_gain chỉ dương ở khoảng giữa. Main độc lập kết luận tương tự ("verification pays only in
the middle of the difficulty band").

Nhưng đó là so sánh GIỮA CÁC Ô — mỗi ô một điểm dữ liệu, tổng cộng 4 điểm. Nếu cơ chế là thật
thì nó phải xuất hiện cả **BÊN TRONG một ô**: các câu khó/dễ khác nhau trong cùng một lần chạy
cũng phải cho V_gain khác nhau theo cùng hình dạng.

Đây là phép thử mạnh hơn nhiều, và chạy được trên trace ĐÃ CÓ, không tốn GPU.

ĐO ĐỘ KHÓ THẾ NÀO: MATH-500 trên Kaggle không có cột Level, nên dùng thước đo tốt hơn cho mục
đích này — **số lời giải đúng trong K mẫu độc lập của Solver**. Nó đo độ khó ĐỐI VỚI CHÍNH MODEL
NÀY, chứ không phải nhãn độ khó do người gán. 0/K = quá sức, K/K = quá dễ.

Nguồn: results_folds/aggk (K=5, MATH 1.5B) và results_orpo/eval_* (K=3) — các vòng có nhiều
mẫu độc lập trên cùng câu.

Chạy: python analysis/difficulty_strata.py
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

def load(path):
    f = ROOT / path
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

# ---- (1) V_gain theo tầng độ khó, dùng trace rescue (co ca S lan V) ---------
def verifier_by_strata(path, label):
    """rescue trace: mỗi câu có sol (S) và ver (V). Độ khó = S đúng hay sai + độ dài."""
    T = load(path)
    if not T:
        print(f"(bỏ qua {path})")
        return
    print("\n" + "=" * 78)
    print(f"{label}  n={len(T)}   — VERIFIER theo tầng")
    print("=" * 78)
    # tầng theo: Solver-một-mình đúng/sai (proxy độ khó nội tại của câu với model này)
    for lab, sel in (("Solver-một-mình ĐÚNG (câu dễ)", lambda t: t["ok"]["alone"]),
                     ("Solver-một-mình SAI  (câu khó)", lambda t: not t["ok"]["alone"])):
        g = [t for t in T if sel(t)]
        if not g:
            continue
        accS = sum(t["ok"]["S"] for t in g) / len(g)
        accV = sum(t["ok"]["V"] for t in g) / len(g)
        resc = sum(1 for t in g if not t["ok"]["S"] and t["ok"]["V"])
        brk = sum(1 for t in g if t["ok"]["S"] and not t["ok"]["V"])
        print(f"  {lab:<32} n={len(g):>3}  S {accS:.3f} -> V {accV:.3f}  "
              f"({accV-accS:+.3f})   cứu {resc} / phá {brk}")

# ---- (2) V_gain theo SỐ MẪU ĐÚNG trong K (thước đo độ khó liên tục) --------
def strata_by_k(path, label, arm_pre, arm_post, kcands="candidates"):
    """aggk/orpo trace: độ khó = số ứng viên đúng trong K. Đo hiệu ứng của arm_post vs arm_pre."""
    T = load(path)
    if not T:
        print(f"(bỏ qua {path})")
        return
    K = len(T[0]["pred"][kcands])
    print("\n" + "=" * 78)
    print(f"{label}  n={len(T)}  K={K}   — {arm_post} vs {arm_pre} theo tầng độ khó")
    print("=" * 78)
    print(f"  {'số mẫu ĐÚNG / K':<20} {'n':>4} {'pre':>7} {'post':>7} {'Δ':>8}   ý nghĩa")
    print("  " + "-" * 74)
    for k in range(K + 1):
        g = [t for t in T
             if sum(1 for p in t["pred"][kcands] if eq(p, t["gold"])) == k]
        if not g:
            continue
        pre = sum(t["ok"][arm_pre] for t in g) / len(g)
        post = sum(t["ok"][arm_post] for t in g) / len(g)
        tag = ("quá sức — không mẫu nào đúng" if k == 0 else
               "quá dễ — mọi mẫu đều đúng" if k == K else
               "GIỮA DẢI — có cái đúng cái sai")
        print(f"  {k}/{K}{'':<17} {len(g):>4} {pre:>7.3f} {post:>7.3f} {post-pre:>+8.3f}   {tag}")
    # tổng hợp: chỉ tầng giữa mới có gì để chọn
    mid = [t for t in T
           if 0 < sum(1 for p in t["pred"][kcands] if eq(p, t["gold"])) < K]
    if mid:
        pre = sum(t["ok"][arm_pre] for t in mid) / len(mid)
        post = sum(t["ok"][arm_post] for t in mid) / len(mid)
        print(f"\n  GỘP tầng giữa (1..{K-1}/{K}): n={len(mid)} ({100*len(mid)/len(T):.0f}%)  "
              f"{pre:.3f} -> {post:.3f} ({post-pre:+.3f})")
        print(f"  Ở hai tầng biên (0/{K} và {K}/{K}) thì KHÔNG THỂ có hiệu ứng: không có lựa "
              f"chọn đúng, hoặc mọi lựa chọn đều đúng.")

def main():
    verifier_by_strata("results_rescue/gsm8k/traces.json", "GSM8K 1.5B")
    verifier_by_strata("results_rescue/math/traces.json", "MATH 1.5B")
    verifier_by_strata("results_rescue/gsm8k_7b/traces.json", "GSM8K 7B")
    verifier_by_strata("results_rescue/math_7b/traces.json", "MATH 7B")

    strata_by_k("results_folds/aggk/traces.json", "MATH 1.5B (aggk)", "S", "vote5")
    strata_by_k("results_folds/aggk/traces.json", "MATH 1.5B (aggk)", "S", "agg5")

    print("\n" + "=" * 78)
    print("CÁCH ĐỌC: nếu cơ chế 'chỉ giúp ở giữa dải' là thật thì nó phải xuất hiện BÊN TRONG")
    print("một lần chạy, không chỉ khi so giữa 4 ô. Tầng 0/K và K/K là ràng buộc toán học —")
    print("không có gì để cứu, hoặc không có gì để phá. Câu hỏi thật là tầng GIỮA có dương không.")

if __name__ == "__main__":
    main()
