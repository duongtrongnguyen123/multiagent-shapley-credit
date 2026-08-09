# Shapley credit assignment on MATH-500 (harder, still verifiable). Same 16-coalition
# Planner/Solver/Verifier/Aggregator design as GSM8K, but answers are LaTeX \boxed{}
# with a normalized-string + numeric grader. Homogeneous Qwen2.5-1.5B unless patched.
import os, re, csv, json, time, glob
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

CONFIG_ID = "__CONFIG_ID__"
MASK      = (__P__, __S__, __V__, __A__)
N_EVAL    = __N_EVAL__
BATCH     = 16          # MATH solutions are longer than GSM8K

def find_one(p, w):
    h = glob.glob(p, recursive=True)
    if not h:
        raise FileNotFoundError(f"{w}: {p} :: {glob.glob('/kaggle/input/**', recursive=True)[:40]}")
    return sorted(h, key=len)[0]

MODEL_DIR = os.path.dirname(find_one("/kaggle/input/**/model.safetensors", "1.5B model"))
MATH_CSV  = find_one("/kaggle/input/**/math_500_test.csv", "MATH-500 csv")
OUT_DIR   = "/kaggle/working"
P, S, V, A = MASK
print(f"CONFIG {CONFIG_ID} MASK P={P} S={S} V={V} A={A} N={N_EVAL}", flush=True)
print("torch", torch.__version__, "gpu",
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU", flush=True)

rows = []
with open(MATH_CSV, newline="") as f:
    for r in csv.DictReader(f):
        rows.append((r["Question"], r["Answer"]))
rows = rows[:N_EVAL]
questions = [q for q, _ in rows]
n = len(rows)
print(f"loaded {n} MATH problems", flush=True)

# ---- LaTeX \boxed{} extraction + grading ----------------------------------
def last_boxed(s):
    if not s:
        return None
    idx = s.rfind("\\boxed")
    if idx < 0:
        idx = s.rfind("\\fbox")
        if idx < 0:
            return None
    i = s.find("{", idx)
    if i < 0:
        return None
    depth, start = 0, i
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[start + 1:j]
    return None

def norm(a):
    if a is None:
        return None
    a = a.strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "\\ ", "\\quad", "\\qquad"]:
        a = a.replace(x, "")
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    a = re.sub(r"\\text\s*\{[^}]*\}", "", a)
    a = re.sub(r"\\mbox\s*\{[^}]*\}", "", a)
    a = a.replace("\\$", "").replace("$", "").replace(" ", "")
    a = a.replace("\\%", "").replace("%", "").replace("^{\\circ}", "").replace("^\\circ", "")
    a = a.replace("dollars", "").replace("\\cdot", "*")
    a = a.strip().rstrip(".").strip("{}")
    return a

def math_eq(p, g):
    p, g = norm(p), norm(g)
    if p is None or g is None:
        return False
    if p == g:
        return True
    try:
        return abs(float(p) - float(g)) < 1e-6
    except (ValueError, TypeError):
        return False

def pred_answer(text):
    b = last_boxed(text)
    if b is not None:
        return b
    m = re.findall(r"(?:final answer is|answer is|answer:)\s*\$?([^\n.$]+)", text or "", re.I)
    return m[-1].strip() if m else None

# ---- model ----------------------------------------------------------------
tok = AutoTokenizer.from_pretrained(MODEL_DIR)
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR, torch_dtype=torch.float16, device_map="auto").eval()

PLAN_SYS   = ("You are a math planning assistant. Read the competition problem and give a "
              "concise numbered plan of the solution steps. Do NOT compute the final answer.")
SOLVE_SYS  = ("You are an expert mathematician. Solve the problem step by step. Put the final "
              "answer in \\boxed{}.")
VERIFY_SYS = ("You are a math verifier. Given a problem and a proposed solution, check each "
              "step; if wrong, correct it. Put the final answer in \\boxed{}.")
AGG_SYS    = ("You are given a problem and one or more candidate solutions. Decide the correct "
              "final answer by re-checking. Put the final answer in \\boxed{}.")

def chat(system, user):
    return tok.apply_chat_template(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        tokenize=False, add_generation_prompt=True)

def gen(prompts, max_new):
    outs = []
    for i in range(0, len(prompts), BATCH):
        chunk = prompts[i:i + BATCH]
        enc = tok(chunk, return_tensors="pt", padding=True).to("cuda")
        with torch.no_grad():
            o = model.generate(**enc, max_new_tokens=max_new, do_sample=False,
                               pad_token_id=tok.pad_token_id)
        outs += tok.batch_decode(o[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        print(f"  batch {min(i+BATCH,len(prompts))}/{len(prompts)}", flush=True)
    return outs

t0 = time.time()
plans = [None] * n
produced = [[] for _ in range(n)]
def solve_user(i):
    u = questions[i]
    if P and plans[i]:
        u += "\n\nSuggested plan:\n" + plans[i]
    return u

if P:
    plans = gen([chat(PLAN_SYS, q) for q in questions], 512)
if S:
    sol = gen([chat(SOLVE_SYS, solve_user(i)) for i in range(n)], 1024)
    for i, t in enumerate(sol):
        produced[i].append(t)
if V:
    prompts = [chat(VERIFY_SYS, questions[i] + "\n\nProposed solution:\n" + produced[i][-1])
               if produced[i] else chat(SOLVE_SYS, solve_user(i)) for i in range(n)]
    ver = gen(prompts, 1024)
    for i, t in enumerate(ver):
        produced[i].append(t)
if A:
    prompts = []
    for i in range(n):
        if produced[i]:
            body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(produced[i]))
            prompts.append(chat(AGG_SYS, questions[i] + "\n\n" + body))
        else:
            prompts.append(chat(SOLVE_SYS, solve_user(i)))
    agg = gen(prompts, 1024)
    for i, t in enumerate(agg):
        produced[i].append(t)

correct, preds = 0, []
for i in range(n):
    final = produced[i][-1] if produced[i] else None
    p, g = pred_answer(final), last_boxed(rows[i][1])
    ok = math_eq(p, g); correct += ok
    preds.append({"gold": g, "pred": p, "correct": bool(ok)})
acc = correct / n if n else 0.0
summary = {"config_id": CONFIG_ID, "mask": {"P": P, "S": S, "V": V, "A": A},
           "dataset": "MATH-500", "n": n, "correct": correct, "accuracy": acc,
           "seconds": round(time.time() - t0, 1)}
print("SUMMARY", json.dumps(summary), flush=True)
os.makedirs(OUT_DIR, exist_ok=True)
json.dump(summary, open(os.path.join(OUT_DIR, "summary.json"), "w"), indent=2)
json.dump(preds, open(os.path.join(OUT_DIR, "preds.json"), "w"))
print("done", flush=True)
