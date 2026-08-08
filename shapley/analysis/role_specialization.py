#!/usr/bin/env python3
"""Bốn vai trò có THẬT SỰ khác nhau không, hay chỉ khác trên danh nghĩa?

Dự án bắt đầu bằng câu hỏi đo lường ("vai nào đóng góp bao nhiêu"), vốn giả định các vai làm
đúng việc mà tên gọi của chúng nói. Script này kiểm chính giả định đó, bằng các chỉ số HÀNH VI
đọc trực tiếp từ trace — không phải accuracy.

Với mỗi vai, đo xem nó có làm đúng việc được giao không:
  Planner   — được bảo ĐỪNG tính đáp án. Có bao nhiêu % kế hoạch chứa sẵn đáp án đúng?
  Solver    — được bảo giải từng bước. Bao nhiêu % lượt không sinh ra CON SỐ MỚI nào
              (tức chỉ chép lại của Planner)?
  Verifier  — được bảo KIỂM TỪNG BƯỚC. Nó có tái sử dụng lời giải của Solver không, hay
              giải lại từ đầu? (đo bằng độ chồng lấn số giữa lời giải S và V)
  Aggregator— được bảo đối chiếu rồi chọn. Nó có tự tính ra đáp án nào không, hay chỉ chép
              lại một ứng viên?

Chỉ số then chốt là NOVEL: tỉ lệ lượt sinh ra một đáp án không có trong đầu vào của nó. Một vai
"làm việc" thì thỉnh thoảng phải sinh ra thứ mới; một trạm trung chuyển thì không bao giờ.

Chạy: python analysis/role_specialization.py
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

def nums(t):
    """tập số xuất hiện trong một lượt sinh — dùng để đo 'có tính gì mới không'."""
    return {x.replace(",", "") for x in NUM.findall(t or "")}

def pct(a, b):
    return f"{100*a/b:.1f}%" if b else "—"

def analyse(path, label):
    f = ROOT / path
    if not f.exists():
        print(f"(bỏ qua {path} — chưa có)")
        return None
    T = json.loads(f.read_text(encoding="utf-8"))
    n = len(T)
    r = {"label": label, "n": n}

    # --- PLANNER: được bảo ĐỪNG tính đáp án ---------------------------------
    leak = sum(1 for t in T if eq(boxed(t["plan"]) or (list(nums(t["plan"]))[-1:] or [None])[0],
                                  t["gold"]))
    r["plan_leaks_answer"] = leak / n
    r["plan_has_boxed"] = sum(1 for t in T if "\\boxed" in (t["plan"] or "")) / n

    # --- SOLVER: có sinh ra số MỚI so với plan không? ------------------------
    no_new = sum(1 for t in T if not (nums(t["sol"]) - nums(t["plan"])))
    r["solver_no_new_number"] = no_new / n
    r["solver_median_len"] = statistics.median(t["len"]["S"] for t in T)
    r["solver_alone_median_len"] = statistics.median(t["len"]["alone"] for t in T)

    # --- VERIFIER: kiểm lại hay giải lại? -----------------------------------
    # tái sử dụng = tỉ lệ số trong lời giải S còn xuất hiện trong lời giải V
    reuse = []
    for t in T:
        s, v = nums(t["sol"]), nums(t["ver"])
        if s:
            reuse.append(len(s & v) / len(s))
    r["verifier_reuse_of_solver"] = statistics.mean(reuse) if reuse else 0.0
    # khi V ĐỔI đáp án (can thiệp thật) thì nó tái sử dụng bao nhiêu?
    reuse_int = []
    for t in T:
        if t["pred"]["V"] is not None and not eq(t["pred"]["V"], t["pred"]["S"]):
            s, v = nums(t["sol"]), nums(t["ver"])
            if s:
                reuse_int.append(len(s & v) / len(s))
    r["verifier_reuse_when_intervening"] = statistics.mean(reuse_int) if reuse_int else 0.0
    r["verifier_intervened"] = len(reuse_int) / n

    # --- AGGREGATOR: chép hay tính? -----------------------------------------
    echo_v = sum(1 for t in T if t["pred"]["A"] is not None
                 and eq(t["pred"]["A"], t["pred"]["V"])) / n
    novel = novel_ok = 0
    for t in T:
        ap = t["pred"]["A"]
        if ap is None:
            continue
        srcs = [t["pred"]["S"], t["pred"]["V"]]
        if not any(eq(ap, s) for s in srcs if s):
            novel += 1
            if eq(ap, t["gold"]):
                novel_ok += 1
    r["agg_echoes_verifier"] = echo_v
    r["agg_novel_answer"] = novel / n
    r["agg_novel_and_correct"] = novel_ok
    r["agg_median_len"] = statistics.median(t["len"]["A"] for t in T)
    return r

def show(rows):
    rows = [r for r in rows if r]
    if not rows:
        return
    w = max(len(r["label"]) for r in rows) + 2
    def line(name, key, fmt="pct"):
        cells = []
        for r in rows:
            v = r.get(key)
            cells.append(f"{100*v:>8.1f}%" if fmt == "pct" and isinstance(v, float)
                         else f"{v:>9.0f}" if fmt == "num" else f"{v:>9}")
        print(f"  {name:<44}" + "".join(cells))

    print("\n" + "=" * (46 + 9 * len(rows)))
    print(f"  {'chỉ số hành vi':<44}" + "".join(f"{r['label']:>9}" for r in rows))
    print("=" * (46 + 9 * len(rows)))
    print(f"  {'n':<44}" + "".join(f"{r['n']:>9}" for r in rows))

    print("\n  PLANNER — được bảo 'Do NOT compute the final answer'")
    line("kế hoạch chứa sẵn đáp án ĐÚNG", "plan_leaks_answer")
    line("kế hoạch có \\boxed{}", "plan_has_boxed")

    print("\n  SOLVER — được bảo 'solve step by step'")
    line("lượt KHÔNG sinh số mới nào (chép plan)", "solver_no_new_number")
    line("độ dài lời giải (median, ký tự)", "solver_median_len", "num")
    line("  ... khi KHÔNG có plan", "solver_alone_median_len", "num")

    print("\n  VERIFIER — được bảo 'check each step'")
    line("tái sử dụng số của Solver (trung bình)", "verifier_reuse_of_solver")
    line("  ... khi thật sự ĐỔI đáp án", "verifier_reuse_when_intervening")
    line("tỉ lệ lượt có can thiệp", "verifier_intervened")

    print("\n  AGGREGATOR — được bảo 'decide by re-checking'")
    line("lặp lại đáp án của Verifier", "agg_echoes_verifier")
    line("đáp án KHÔNG có trong đầu vào", "agg_novel_answer")
    line("  ... trong đó đúng (số ca)", "agg_novel_and_correct", "raw")
    line("độ dài (median, ký tự)", "agg_median_len", "num")

def main():
    rows = [analyse("results_rescue/gsm8k/traces.json", "GSM8K"),
            analyse("results_rescue/math/traces.json", "MATH"),
            analyse("results_rescue/gsm8k_7b/traces.json", "GSM8K7B"),
            analyse("results_rescue/math_7b/traces.json", "MATH7B")]
    show(rows)
    print("\n" + "=" * 78)
    print("ĐỌC BẢNG: 'đáp án KHÔNG có trong đầu vào' là chỉ số quyết định — một vai LÀM VIỆC thì")
    print("thỉnh thoảng phải sinh ra thứ mới; một trạm trung chuyển thì không bao giờ. Nếu cột 7B")
    print("khác hẳn cột 1.5B thì chuyên biệt hoá XUẤT HIỆN CÙNG NĂNG LỰC, và kết luận phải nói rõ")
    print("là đặc thù model yếu chứ không phải tính chất của kiến trúc multi-agent.")

if __name__ == "__main__":
    main()
