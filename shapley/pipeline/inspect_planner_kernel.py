# INSPECT — vì sao Planner giải luôn đáp án còn Solver chỉ chép lại?
# Dump nguyên văn output của Planner và Solver trên vài câu, CẢ GSM8K lẫn MATH, để đọc bằng mắt.
# Không có can thiệp, không đo hiệu ứng — chỉ quan sát. Dùng ĐÚNG prompt của template gốc
# (template.py cho gsm8k, template_math.py cho math) để cái nhìn thấy đúng là cái đang chạy.
#
# 3 nhánh Solver trên CÙNG plan, để tách "Solver chép vì có plan" khỏi "Solver vốn lười":
#   NP  : Solver không thấy plan          (đối chứng)
#   WP  : Solver thấy plan (như template) (nghi phạm)
#   WPE : Solver thấy plan + bị nhắc phải tự trình bày (thử cứu)
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

def gen(sysm, usrs, mx):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = [tok.apply_chat_template([{"role": "system", "content": sysm},
                                       {"role": "user", "content": u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False,
                               pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        print(f"   ...{min(i+BS,len(usrs))}/{len(usrs)}", flush=True)
    return outs

# ---- grading helpers (giống template gốc) ----------------------------------
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

# ---- ĐÚNG prompt của template gốc ------------------------------------------
if TASK == "gsm8k":
    # template.py
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
else:
    # template_math.py
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

SOLVE_E = SOLVE_SYS + (" Even if a plan is provided, you must still write out every "
                       "calculation yourself; do not just restate the plan's answer.")

qs = [q_of(r) for r in rows]
gs = [gold_of(r) for r in rows]

print("== PLANNER ==", flush=True)
plans = gen(PLAN_SYS, qs, PLAN_MX)

arms = {
    "NP_no_plan":  (SOLVE_SYS, list(qs)),
    "WP_with_plan": (SOLVE_SYS, [f"{q}\n\nSuggested plan:\n{p}" for q, p in zip(qs, plans)]),
    "WPE_plan_reminder": (SOLVE_E, [f"{q}\n\nSuggested plan:\n{p}" for q, p in zip(qs, plans)]),
}
sols = {}
for tag, (sysm, usrs) in arms.items():
    print(f"== SOLVER {tag} ==", flush=True)
    sols[tag] = gen(sysm, usrs, SOLVE_MX)

# ---- các chỉ số "Planner giải hộ / Solver chép" -----------------------------
def last_num(t):
    m = NUM.findall(t or "")
    return m[-1].replace(",", "") if m else None

out = {"task": TASK, "n": len(rows), "arms": {}}
plan_has_gold = sum(1 for p, g in zip(plans, gs) if g is not None and eq(last_num(p), g)
                    or (g is not None and boxed(p) is not None and eq(boxed(p), g)))
out["plan_contains_correct_answer"] = round(plan_has_gold / len(rows), 4)
out["median_plan_len"] = int(statistics.median(len(p) for p in plans))

for tag, ss in sols.items():
    a = [pred(s) for s in ss]
    acc = sum(eq(x, g) for x, g in zip(a, gs)) / len(gs)
    # Solver "chép": đáp án Solver == số cuối cùng của plan
    copy = sum(1 for s, p in zip(ss, plans)
               if pred(s) is not None and last_num(p) is not None and eq(pred(s), last_num(p)))
    out["arms"][tag] = {
        "solver_acc": round(acc, 4),
        "median_sol_len": int(statistics.median(len(s or "") for s in ss)),
        "pct_sol_under_200_chars": round(sum(1 for s in ss if len(s or "") < 200) / len(ss), 4),
        "copycat_rate_ans_eq_plan_last_num": round(copy / len(ss), 4),
    }
    print(f"[{tag}] {json.dumps(out['arms'][tag])}", flush=True)

# ---- DUMP nguyên văn để ĐỌC BẰNG MẮT ---------------------------------------
K = min(8, len(rows))
print("\n" + "=" * 78, flush=True)
print(f"NGUYEN VAN {K} VI DU DAU TIEN — {TASK.upper()}", flush=True)
print("=" * 78, flush=True)
for i in range(K):
    print(f"\n{'#'*78}\n### CAU {i+1}  |  GOLD = {gs[i]}\n{'#'*78}", flush=True)
    print(f"\n--- DE BAI ---\n{qs[i]}", flush=True)
    print(f"\n--- PLANNER (duoc bao: 'Do NOT compute the final answer') ---\n{plans[i]}", flush=True)
    for tag in arms:
        s = sols[tag][i]
        print(f"\n--- SOLVER [{tag}]  (len={len(s)}, pred={pred(s)}) ---\n{s}", flush=True)

print("\nSUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump([{"q": qs[i], "gold": gs[i], "plan": plans[i],
            **{f"sol_{t}": sols[t][i] for t in arms}} for i in range(len(rows))],
          open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)
