# Shapley credit assignment for a Planner/Solver/Verifier/Aggregator LLM-agent
# pipeline on GSM8K. One Kaggle kernel = one role-subset (coalition). All 16
# coalitions run the SAME first N questions so v(S) is comparable across accounts.
# Roles: bit order (P, S, V, A). A missing role is skipped; the answer is read
# from the most-downstream present role's output. Same Qwen2.5-1.5B for all roles.
import os, re, csv, json, time, glob
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# ---- config (patched per coalition by orchestrate.py) ---------------------
CONFIG_ID = "__CONFIG_ID__"
MASK      = (__P__, __S__, __V__, __A__)   # (Planner, Solver, Verifier, Aggregator)
N_EVAL    = __N_EVAL__
BATCH     = 32

def find_one(pattern, what):
    hits = glob.glob(pattern, recursive=True)
    if not hits:
        raise FileNotFoundError(f"{what}: no match {pattern} :: "
                                f"{glob.glob('/kaggle/input/**', recursive=True)[:40]}")
    return sorted(hits, key=len)[0]

MODEL_DIR = os.path.dirname(find_one("/kaggle/input/**/config.json", "model config"))
GSM8K_CSV = find_one("/kaggle/input/**/main_test.csv", "gsm8k csv")
OUT_DIR   = "/kaggle/working"
P, S, V, A = MASK
print(f"CONFIG {CONFIG_ID} MASK P={P} S={S} V={V} A={A} N={N_EVAL}", flush=True)
print("torch", torch.__version__, "gpu",
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU", flush=True)

# ---- data -----------------------------------------------------------------
rows = []
with open(GSM8K_CSV, newline="") as f:
    for r in csv.DictReader(f):
        rows.append((r["question"], r["answer"]))
rows = rows[:N_EVAL]
questions = [q for q, _ in rows]
n = len(rows)
print(f"loaded {n} questions", flush=True)

def gold_answer(ans):
    m = re.search(r"####\s*([-\d,\.]+)", ans)
    return m.group(1).replace(",", "").strip().rstrip(".") if m else None

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def pred_answer(text):
    if not text:
        return None
    m = re.findall(r"(?:answer is|answer:|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", text, re.I)
    cands = m if m else NUM_RE.findall(text)
    return cands[-1].replace(",", "").strip().rstrip(".") if cands else None

def num_eq(a, b):
    try:
        return a is not None and b is not None and abs(float(a) - float(b)) < 1e-4
    except ValueError:
        return a == b

# ---- model ----------------------------------------------------------------
tok = AutoTokenizer.from_pretrained(MODEL_DIR)
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR, torch_dtype=torch.float16, device_map="auto").eval()

PLAN_SYS   = ("You are a math planning assistant. Read the problem and give a concise "
              "numbered plan of the steps needed. Do NOT compute the final answer.")
SOLVE_SYS  = ("You are a careful math solver. Solve step by step, showing arithmetic. "
              "End with a line: 'The answer is <number>'.")
VERIFY_SYS = ("You are a math verifier. You are given a problem and a proposed solution. "
              "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
AGG_SYS    = ("You are given a math problem and one or more candidate solutions. Decide the "
              "correct final answer by re-checking and majority. End with 'The answer is <number>'.")

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
        g = o[:, enc["input_ids"].shape[1]:]
        outs += tok.batch_decode(g, skip_special_tokens=True)
        print(f"  stage batch {min(i+BATCH,len(prompts))}/{len(prompts)}", flush=True)
    return outs

# ---- pipeline (stage-by-stage, batched across all questions) --------------
t0 = time.time()
plans = [None] * n
produced = [[] for _ in range(n)]          # candidate solution texts per question

def solve_user(i):
    u = questions[i]
    if P and plans[i]:
        u += "\n\nSuggested plan:\n" + plans[i]
    return u

if P:
    plans = gen([chat(PLAN_SYS, q) for q in questions], 256)

if S:
    sol = gen([chat(SOLVE_SYS, solve_user(i)) for i in range(n)], 512)
    for i, t in enumerate(sol):
        produced[i].append(t)

if V:
    prompts = []
    for i in range(n):
        if produced[i]:
            prompts.append(chat(VERIFY_SYS, questions[i] +
                                "\n\nProposed solution:\n" + produced[i][-1]))
        else:
            prompts.append(chat(SOLVE_SYS, solve_user(i)))   # verify-solve fresh
    ver = gen(prompts, 512)
    for i, t in enumerate(ver):
        produced[i].append(t)

if A:
    prompts = []
    for i in range(n):
        if produced[i]:
            body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(produced[i]))
            prompts.append(chat(AGG_SYS, questions[i] + "\n\n" + body))
        else:
            prompts.append(chat(SOLVE_SYS, solve_user(i)))   # aggregate-solve fresh
    agg = gen(prompts, 256)
    for i, t in enumerate(agg):
        produced[i].append(t)

# ---- score ----------------------------------------------------------------
correct = 0
preds = []
for i in range(n):
    final = produced[i][-1] if produced[i] else None
    p = pred_answer(final)
    g = gold_answer(rows[i][1])
    ok = num_eq(p, g)
    correct += ok
    preds.append({"gold": g, "pred": p, "correct": bool(ok)})

acc = correct / n if n else 0.0
summary = {"config_id": CONFIG_ID, "mask": {"P": P, "S": S, "V": V, "A": A},
           "n": n, "correct": correct, "accuracy": acc,
           "seconds": round(time.time() - t0, 1)}
print("SUMMARY", json.dumps(summary), flush=True)
os.makedirs(OUT_DIR, exist_ok=True)
json.dump(summary, open(os.path.join(OUT_DIR, "summary.json"), "w"), indent=2)
json.dump(preds, open(os.path.join(OUT_DIR, "preds.json"), "w"))
print("done", flush=True)
