# FEW-SHOT — chuyên biệt hoá vai trò bằng VÍ DỤ thay vì bằng chỉ thị.
# Bối cảnh: docs/PLANNER_COPYCAT.md cho thấy chỉ thị "Do NOT compute the final answer"
# KHÔNG chặn được Planner giải hộ (GSM8K 3/8, MATH 4/8 kế hoạch chứa sẵn đáp án), và lời
# nhắc thêm cho Solver (nhánh WPE) KHÔNG đổi được gì — output giống hệt từng ký tự.
# Giả thuyết: few-shot CHO THẤY dạng output mong muốn, mạnh hơn chỉ thị phủ định.
#
# Lưới 2x2 trên CÙNG bộ bài (cộng NP làm mốc), để tách tác động từng vai:
#   NP        : không plan                       (mốc: Solver tự làm hết)
#   bP_bS     : plan gốc      -> solver gốc      (baseline hiện tại của dự án)
#   fP_bS     : plan FEW-SHOT -> solver gốc      (plan sạch có cứu được Solver?)
#   bP_fS     : plan gốc      -> solver FEW-SHOT (Solver có kháng được plan rò đáp án?)
#   fP_fS     : plan FEW-SHOT -> solver FEW-SHOT (cả hai)
#
# ĐO HAI CHIỀU (bắt buộc): few-shot có làm plan SẠCH số không, VÀ accuracy có TỤT không.
# Plan sạch mà vô dụng thì cũng là thất bại.
import os, re, csv, json, glob, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "__TASK__"
N    = __N__
BS   = __BS__

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "main_test.csv" if TASK == "gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} n={len(rows)}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="auto").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx, shots=()):
    """shots = tuple các cặp (user, assistant) chèn trước câu hỏi thật."""
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = []
        for u in ch:
            msgs = [{"role": "system", "content": sysm}]
            for su, sa in shots:
                msgs += [{"role": "user", "content": su},
                         {"role": "assistant", "content": sa}]
            msgs.append({"role": "user", "content": u})
            ps.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False,
                               pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        print(f"   ...{min(i+BS,len(usrs))}/{len(usrs)}", flush=True)
    return outs

# ---- chấm điểm (giống template gốc) ----------------------------------------
def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0: return None
    i = s.find("{", i); d = 0; st = i
    for j in range(i, len(s)):
        if s[j] == "{": d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0: return s[st + 1:j]
    return None
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def norm(a):
    if a is None: return None
    a = str(a).strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " ", ","]: a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()
def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g: return False
    if p == g: return True
    try: return abs(float(p) - float(g)) < 1e-6
    except: return False

# ---- prompt gốc (bê nguyên từ template.py / template_math.py) ---------------
if TASK == "gsm8k":
    PLAN_SYS  = ("You are a math planning assistant. Read the problem and give a concise "
                 "numbered plan of the steps needed. Do NOT compute the final answer.")
    SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                 "End with a line: 'The answer is <number>'.")
    PLAN_MX, SOLVE_MX = 256, 512
    q_of = lambda r: r["question"]
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    def pred(t):
        m = (re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
             or NUM.findall(t or ""))
        return m[-1].replace(",", "") if m else None

    # few-shot Planner: kế hoạch CHỈ BẰNG LỜI, không con số, không dấu '='
    PLAN_SHOTS = (
        ("Natalia sold clips to 48 of her friends in April, and then she sold half as many "
         "clips in May. How many clips did Natalia sell altogether in April and May?",
         "1. Note the number of clips sold in April, given directly in the problem.\n"
         "2. Express May's sales as the stated fraction of April's sales.\n"
         "3. Add the two monthly amounts to obtain the total."),
        ("Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of "
         "babysitting. How much did she earn?",
         "1. Identify the hourly rate stated in the problem.\n"
         "2. Convert the babysitting duration from minutes into a fraction of an hour.\n"
         "3. Multiply the rate by that fraction to obtain the earnings."),
    )
    # few-shot Solver: plan mẫu CỐ TÌNH rò đáp án, lời giải mẫu VẪN trình bày đầy đủ
    SOLVE_SHOTS = (
        ("Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of "
         "babysitting. How much did she earn?\n\nSuggested plan:\n"
         "1. Rate is $12 per hour.\n2. 50 minutes = 50/60 hour.\n3. 12 * 50/60 = 10. "
         "The answer is 10.",
         "I will not rely on the plan's arithmetic; I recompute every step.\n\n"
         "Step 1. The rate is $12 per hour.\n"
         "Step 2. 50 minutes as a fraction of an hour: 50 / 60 = 5/6 hour.\n"
         "Step 3. Earnings: 12 * 5/6 = 60/6 = 10.\n"
         "Check: 12 per hour means 1 per 5 minutes, and 50 minutes is ten 5-minute blocks, "
         "so 10 * 1 = 10. Consistent.\n\n"
         "The answer is 10."),
    )
else:
    PLAN_SYS  = ("You are a math planning assistant. Read the competition problem and give a "
                 "concise numbered plan of the solution steps. Do NOT compute the final answer.")
    SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the final "
                 "answer in \\boxed{}.")
    PLAN_MX, SOLVE_MX = 512, 1024
    q_of = lambda r: r["Question"]
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None

    PLAN_SHOTS = (
        ("What is the value of $\\sqrt{36+64}-\\sqrt{25-16}$?",
         "1. Simplify the sum inside the first radical, then take its square root.\n"
         "2. Simplify the difference inside the second radical, then take its square root.\n"
         "3. Subtract the second root from the first."),
        ("If $x = 2$ and $y = 5$, then what is the value of $\\frac{x^4+2y^2}{6}$?",
         "1. Substitute the given values for the two variables into the numerator.\n"
         "2. Evaluate the fourth-power term and the doubled square term separately.\n"
         "3. Add those terms, then divide by the denominator and reduce the fraction."),
    )
    SOLVE_SHOTS = (
        ("What is the value of $\\sqrt{36+64}-\\sqrt{25-16}$?\n\nSuggested plan:\n"
         "1. sqrt(36+64) = sqrt(100) = 10.\n2. sqrt(25-16) = sqrt(9) = 3.\n"
         "3. 10 - 3 = 7. So the answer is $\\boxed{7}$.",
         "I will not rely on the plan's arithmetic; I recompute every step.\n\n"
         "Step 1. Inside the first radical: $36 + 64 = 100$, and $\\sqrt{100} = 10$.\n"
         "Step 2. Inside the second radical: $25 - 16 = 9$, and $\\sqrt{9} = 3$.\n"
         "Step 3. Subtract: $10 - 3 = 7$.\n"
         "Check: $10^2 = 100$ and $3^2 = 9$, so both roots are exact.\n\n"
         "$\\boxed{7}$"),
    )

SOLVE_FS_SYS = SOLVE_SYS + (" A suggested plan may be provided. Treat it only as a hint about "
                            "which steps to take: recompute every value yourself and show the "
                            "arithmetic. Never restate the plan's answer without redoing the work.")
PLAN_FS_SYS  = PLAN_SYS + (" Describe each step in words only. Write no arithmetic expression, "
                           "no equals sign, and no numeric result.")

qs = [q_of(r) for r in rows]
gs = [gold_of(r) for r in rows]

print("== PLANNER base ==", flush=True)
plan_b = gen(PLAN_SYS, qs, PLAN_MX)
print("== PLANNER few-shot ==", flush=True)
plan_f = gen(PLAN_FS_SYS, qs, PLAN_MX, shots=PLAN_SHOTS)

def with_plan(ps):
    return [f"{q}\n\nSuggested plan:\n{p}" for q, p in zip(qs, ps)]

arms = {
    "NP_no_plan":    (SOLVE_SYS,    list(qs),          (),           None),
    "bP_bS_baseline":(SOLVE_SYS,    with_plan(plan_b), (),           plan_b),
    "fP_bS_fewshot_planner": (SOLVE_SYS,    with_plan(plan_f), (),           plan_f),
    "bP_fS_fewshot_solver":  (SOLVE_FS_SYS, with_plan(plan_b), SOLVE_SHOTS,  plan_b),
    "fP_fS_both":    (SOLVE_FS_SYS, with_plan(plan_f), SOLVE_SHOTS,  plan_f),
}
sols, used_plan = {}, {}
for tag, (sysm, usrs, shots, pl) in arms.items():
    print(f"== SOLVER {tag} ==", flush=True)
    sols[tag] = gen(sysm, usrs, SOLVE_MX, shots=shots)
    used_plan[tag] = pl

# ---- chỉ số ----------------------------------------------------------------
def plan_answer(p):
    """đáp án mà kế hoạch để lộ: ưu tiên \\boxed, không có thì lấy số cuối."""
    b = boxed(p)
    if b is not None: return b
    m = NUM.findall(p or "")
    return m[-1].replace(",", "") if m else None

def plan_stats(ps, name):
    leak = sum(1 for p, g in zip(ps, gs) if g is not None and eq(plan_answer(p), g))
    d = {"median_len": int(statistics.median(len(p) for p in ps)),
         "leaks_correct_answer": round(leak / len(ps), 4),
         "has_boxed": round(sum(1 for p in ps if "\\boxed" in p) / len(ps), 4),
         "has_equals_sign": round(sum(1 for p in ps if "=" in p) / len(ps), 4),
         "median_digit_count": int(statistics.median(sum(c.isdigit() for c in p) for p in ps))}
    print(f"[PLAN {name}] {json.dumps(d)}", flush=True)
    return d

out = {"task": TASK, "n": len(rows),
       "plan": {"base": plan_stats(plan_b, "base"), "fewshot": plan_stats(plan_f, "fewshot")},
       "arms": {}}

for tag, ss in sols.items():
    a = [pred(s) for s in ss]
    acc = sum(eq(x, g) for x, g in zip(a, gs)) / len(gs)
    pl = used_plan[tag]
    copy = (0 if pl is None else
            sum(1 for s, p in zip(ss, pl)
                if pred(s) is not None and plan_answer(p) is not None
                and eq(pred(s), plan_answer(p))))
    out["arms"][tag] = {
        "solver_acc": round(acc, 4),
        "median_sol_len": int(statistics.median(len(s or "") for s in ss)),
        "pct_sol_under_200_chars": round(sum(1 for s in ss if len(s or "") < 200) / len(ss), 4),
        "copycat_rate": round(copy / len(ss), 4),
    }
    print(f"[{tag}] {json.dumps(out['arms'][tag])}", flush=True)

# ---- bảng ACCURACY so trực tiếp (chỉ số quyết định) ------------------------
base_acc = out["arms"]["bP_bS_baseline"]["solver_acc"]
print("\n" + "=" * 60, flush=True)
print(f"{'nhanh':<26} {'acc':>7} {'vs baseline':>12} {'copycat':>8}", flush=True)
print("=" * 60, flush=True)
for tag, r in out["arms"].items():
    d = r["solver_acc"] - base_acc
    print(f"{tag:<26} {r['solver_acc']:>7.4f} {d:>+12.4f} {r['copycat_rate']:>8.3f}", flush=True)
out["accuracy_table"] = {t: {"acc": r["solver_acc"],
                             "delta_vs_baseline": round(r["solver_acc"] - base_acc, 4)}
                         for t, r in out["arms"].items()}
print(f"\nCANH BAO: n={len(rows)} qua nho de ket luan hieu ung "
      f"(1 cau = {1/len(rows):.3f} acc). Xem san nhieu H13.", flush=True)

# ---- dump nguyên văn để đọc bằng mắt ---------------------------------------
K = min(5, len(rows))
print("\n" + "=" * 78, flush=True)
print(f"NGUYEN VAN {K} VI DU — {TASK.upper()}", flush=True)
print("=" * 78, flush=True)
for i in range(K):
    print(f"\n{'#'*78}\n### CAU {i+1}  |  GOLD = {gs[i]}\n{'#'*78}", flush=True)
    print(f"\n--- DE ---\n{qs[i]}", flush=True)
    print(f"\n--- PLAN base (len={len(plan_b[i])}) ---\n{plan_b[i]}", flush=True)
    print(f"\n--- PLAN few-shot (len={len(plan_f[i])}) ---\n{plan_f[i]}", flush=True)
    for tag in arms:
        s = sols[tag][i]
        print(f"\n--- SOLVER [{tag}] (len={len(s)}, pred={pred(s)}) ---\n{s[:700]}", flush=True)

print("\nSUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump([{"q": qs[i], "gold": gs[i], "plan_base": plan_b[i], "plan_fewshot": plan_f[i],
            **{f"sol_{t}": sols[t][i] for t in arms}} for i in range(len(rows))],
          open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)
