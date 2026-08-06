#!/usr/bin/env python3
"""Câu sai là LỖI CỦA AI — Planner hướng dẫn sai, hay Solver tự làm sai?

Đọc trace thô đã tải về (results_inspect/*, results_fewshot/*) và quy trách nhiệm từng câu
bằng một PHẢN CHỨNG có sẵn: nhánh NP (Solver làm MỘT MÌNH, không thấy plan).

  Solver một mình ĐÚNG  + có plan SAI   -> LỖI PLANNER (negative transfer: plan phá)
  Solver một mình SAI   + có plan ĐÚNG  -> PLAN CỨU ĐƯỢC
  Solver một mình SAI   + có plan SAI   -> CẢ HAI CÙNG THUA (bài khó)
  Solver một mình ĐÚNG  + có plan ĐÚNG  -> không sao

Trong nhóm LỖI PLANNER còn tách tiếp:
  plan để lộ đáp án SAI và Solver CHÉP y nguyên -> Planner dắt Solver đi sai (chép mù)
  plan không lộ đáp án                          -> plan dẫn hướng sai nhưng Solver tự tính

Chạy:  python analysis/blame_analysis.py
"""
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]

# ---- chấm điểm; normalizer đã vá dấu LaTeX bao ngoài (lỗi fc2f429) ----------
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
    for x in ["\\(", "\\)", "\\[", "\\]"]:        # vá normalizer
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

def pred_math(t):
    b = boxed(t)
    if b is not None:
        return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
    return m[-1].strip() if m else None

def pred_gsm(t):
    m = (re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
         or NUM.findall(t or ""))
    return m[-1].replace(",", "") if m else None

def plan_answer(p, task):
    """đáp án mà kế hoạch để lộ (nếu có)."""
    b = boxed(p)
    if b is not None:
        return b
    m = NUM.findall(p or "")
    return m[-1].replace(",", "") if m else None

# ---- nạp trace, chuẩn hoá về một schema chung ------------------------------
def load(path, task):
    """-> list các dict {q, gold, plan, alone, withplan, fs_plan, fs_withplan}"""
    f = ROOT / path
    if not f.exists():
        return None
    T = json.loads(f.read_text(encoding="utf-8"))
    out = []
    for t in T:
        r = {"q": t["q"], "gold": t["gold"], "task": task}
        r["plan"] = t.get("plan_base", t.get("plan"))
        r["alone"] = t.get("sol_NP_no_plan")
        r["withplan"] = t.get("sol_bP_bS_baseline", t.get("sol_WP_with_plan"))
        r["fs_plan"] = t.get("plan_fewshot")
        r["fs_withplan"] = t.get("sol_fP_bS_fewshot_planner")
        out.append(r)
    return out

def analyse(rows, label, task):
    P = pred_gsm if task == "gsm8k" else pred_math
    cats = {"planner_fault": [], "plan_rescued": [], "both_fail": [], "both_ok": []}
    plan_leak_wrong_copied = 0
    plan_leak_wrong_caught = 0
    plan_leak_wrong_total = 0

    for i, r in enumerate(rows):
        g = r["gold"]
        a_ok = eq(P(r["alone"]), g)
        w_ok = eq(P(r["withplan"]), g)
        pa = plan_answer(r["plan"], task)
        pa_ok = eq(pa, g) if pa is not None else None
        copied = (pa is not None and P(r["withplan"]) is not None
                  and eq(P(r["withplan"]), pa))

        key = ("both_ok" if a_ok and w_ok else
               "planner_fault" if a_ok and not w_ok else
               "plan_rescued" if (not a_ok) and w_ok else "both_fail")
        cats[key].append({"i": i + 1, "gold": g, "plan_ans": pa, "plan_ans_ok": pa_ok,
                          "copied": copied, "sol_len": len(r["withplan"] or ""),
                          "alone_len": len(r["alone"] or "")})

        # trong các ca kế hoạch để lộ đáp án SAI: Solver chép hay bắt được lỗi?
        if pa is not None and pa_ok is False:
            plan_leak_wrong_total += 1
            if copied:
                plan_leak_wrong_copied += 1
            elif w_ok:
                plan_leak_wrong_caught += 1

    n = len(rows)
    print("\n" + "=" * 76)
    print(f"{label}  (n={n})")
    print("=" * 76)
    print(f"{'nhóm':<34} {'số câu':>7}   ý nghĩa")
    print("-" * 76)
    print(f"{'LỖI PLANNER (một mình đúng->sai)':<34} {len(cats['planner_fault']):>7}"
          f"   plan PHÁ lời giải vốn đúng")
    print(f"{'PLAN CỨU (một mình sai->đúng)':<34} {len(cats['plan_rescued']):>7}"
          f"   plan giúp thật")
    print(f"{'CẢ HAI CÙNG THUA':<34} {len(cats['both_fail']):>7}   bài khó / Solver yếu")
    print(f"{'CẢ HAI ĐÚNG':<34} {len(cats['both_ok']):>7}   không sao")

    net = len(cats["plan_rescued"]) - len(cats["planner_fault"])
    print(f"\n  cân bằng ròng của Planner: {net:+d} câu  "
          f"(cứu {len(cats['plan_rescued'])} − phá {len(cats['planner_fault'])})")

    # tách nguyên nhân trong nhóm CẢ HAI CÙNG THUA
    bf = cats["both_fail"]
    bf_copied = sum(1 for c in bf if c["copied"])
    print(f"\n  Trong {len(bf)} câu CẢ HAI CÙNG THUA:")
    print(f"    - {bf_copied} câu Solver CHÉP đáp án sai của plan (không tự tính lại)")
    print(f"    - {len(bf)-bf_copied} câu Solver tự tính nhưng vẫn sai")

    print(f"\n  Khi kế hoạch để lộ đáp án SAI ({plan_leak_wrong_total} câu):")
    print(f"    - {plan_leak_wrong_copied} câu Solver CHÉP y nguyên -> sai theo")
    print(f"    - {plan_leak_wrong_caught} câu Solver BẮT ĐƯỢC lỗi và tự sửa đúng")
    if plan_leak_wrong_total:
        print(f"    -> tỉ lệ Solver chép theo plan sai: "
              f"{plan_leak_wrong_copied/plan_leak_wrong_total:.0%}")

    if cats["planner_fault"]:
        print(f"\n  Chi tiết các câu LỖI PLANNER:")
        for c in cats["planner_fault"]:
            tag = "CHÉP đáp án sai của plan" if c["copied"] else "plan dẫn hướng sai"
            print(f"    câu {c['i']:>2}  gold={str(c['gold'])[:16]:<16} "
                  f"plan_ans={str(c['plan_ans'])[:14]:<14} {tag}"
                  f"  (một mình {c['alone_len']} ký tự -> có plan {c['sol_len']} ký tự)")
    return cats

def fewshot_effect(rows, task):
    """Few-shot planner có sửa được các ca lỗi planner không?"""
    if not rows or rows[0].get("fs_withplan") is None:
        return
    P = pred_gsm if task == "gsm8k" else pred_math
    fixed = broke = 0
    for r in rows:
        g = r["gold"]
        base_ok = eq(P(r["withplan"]), g)
        fs_ok = eq(P(r["fs_withplan"]), g)
        if not base_ok and fs_ok:
            fixed += 1
        elif base_ok and not fs_ok:
            broke += 1
    print(f"\n  Few-shot planner so với plan gốc: sửa được {fixed} câu, làm hỏng {broke} câu"
          f"  (ròng {fixed-broke:+d})")

def main():
    jobs = [("results_fewshot/math/traces.json", "MATH — few-shot n=30", "math"),
            ("results_inspect/math/traces.json", "MATH — inspect n=8", "math"),
            ("results_inspect/gsm8k/traces.json", "GSM8K — inspect n=8", "gsm8k")]
    any_found = False
    for path, label, task in jobs:
        rows = load(path, task)
        if rows is None:
            print(f"(bỏ qua {path} — chưa tải về)")
            continue
        any_found = True
        analyse(rows, label, task)
        fewshot_effect(rows, task)
    if any_found:
        print("\n" + "=" * 76)
        print("CẢNH BÁO: n ở đây rất nhỏ (8-30 câu). Các con số là ĐẾM CA CỤ THỂ để đọc")
        print("nguyên nhân, KHÔNG phải ước lượng tỉ lệ. Sàn nhiễu H13 ~5 điểm ở n<=250.")

if __name__ == "__main__":
    main()
