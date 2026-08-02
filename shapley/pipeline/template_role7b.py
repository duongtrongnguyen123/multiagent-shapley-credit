# Heterogeneous-role Shapley: PLANNER uses Qwen2.5-7B-Instruct, Solver/Verifier/
# Aggregator use 1.5B. Tests whether the planner's round-2 net-negative credit is
# inherent or just weak-1.5B capacity. Models are loaded ONE-AT-A-TIME per stage
# (fp16, device_map=auto; no bitsandbytes offline) so GPU memory never overflows.
# Only P=1 coalitions run here; P=0 coalitions are reused from round 1 (all-1.5B).
import os, re, csv, json, time, glob
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

CONFIG_ID = "__CONFIG_ID__"
MASK      = (__P__, __S__, __V__, __A__)
N_EVAL    = __N_EVAL__
BIG_ROLE  = "__BIG__"   # role that uses the 7B model

def find_one(p, w):
    h = glob.glob(p, recursive=True)
    if not h:
        raise FileNotFoundError(f"{w}: {p} :: {glob.glob('/kaggle/input/**', recursive=True)[:40]}")
    return sorted(h, key=len)[0]

SMALL_DIR   = os.path.dirname(find_one("/kaggle/input/**/model.safetensors", "1.5B (single-file)"))
PLANNER_DIR = os.path.dirname(find_one("/kaggle/input/**/model.safetensors.index.json", "7B (sharded)"))
GSM8K_CSV   = find_one("/kaggle/input/**/main_test.csv", "gsm8k")
OUT_DIR = "/kaggle/working"
P, S, V, A = MASK
def md(role):   # 7B for the upgraded role, else 1.5B
    return PLANNER_DIR if role == BIG_ROLE else SMALL_DIR
def bs(role):
    return 8 if role == BIG_ROLE else 32
print(f"CONFIG {CONFIG_ID} MASK P={P} S={S} V={V} A={A} BIG={BIG_ROLE} N={N_EVAL}", flush=True)
print("SMALL", SMALL_DIR, "\nPLANNER(7B)", PLANNER_DIR, flush=True)

rows = []
with open(GSM8K_CSV, newline="") as f:
    for r in csv.DictReader(f):
        rows.append((r["question"], r["answer"]))
rows = rows[:N_EVAL]
questions = [q for q, _ in rows]
n = len(rows)

def gold_answer(a):
    m = re.search(r"####\s*([-\d,\.]+)", a)
    return m.group(1).replace(",", "").strip().rstrip(".") if m else None
NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def pred_answer(t):
    if not t:
        return None
    m = re.findall(r"(?:answer is|answer:|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t, re.I)
    c = m if m else NUM_RE.findall(t)
    return c[-1].replace(",", "").strip().rstrip(".") if c else None
def num_eq(a, b):
    try:
        return a is not None and b is not None and abs(float(a) - float(b)) < 1e-4
    except ValueError:
        return a == b

# ---- one-model-at-a-time manager -----------------------------------------
_cur = {"dir": None, "model": None, "tok": None}
def use(mdir):
    if _cur["dir"] != mdir:
        if _cur["model"] is not None:
            del _cur["model"]; _cur["model"] = None
            torch.cuda.empty_cache()
        tok = AutoTokenizer.from_pretrained(mdir)
        tok.padding_side = "left"
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        t0 = time.time()
        m = AutoModelForCausalLM.from_pretrained(mdir, torch_dtype=torch.float16,
                                                 device_map="auto").eval()
        _cur.update(dir=mdir, model=m, tok=tok)
        print(f"  loaded {os.path.basename(mdir)} in {time.time()-t0:.0f}s "
              f"mem={torch.cuda.memory_allocated()/1e9:.1f}GB", flush=True)
    return _cur["model"], _cur["tok"]

def gen(prompts, max_new, mdir, batch):
    model, tok = use(mdir)
    outs = []
    for i in range(0, len(prompts), batch):
        chunk = prompts[i:i + batch]
        enc = tok(chunk, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**enc, max_new_tokens=max_new, do_sample=False,
                               pad_token_id=tok.pad_token_id)
        outs += tok.batch_decode(o[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
    return outs

def chat(mdir, system, user):
    _, tok = use(mdir)
    return tok.apply_chat_template(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        tokenize=False, add_generation_prompt=True)

PLAN_SYS   = ("You are a math planning assistant. Read the problem and give a concise "
              "numbered plan of the steps needed. Do NOT compute the final answer.")
SOLVE_SYS  = ("You are a careful math solver. Solve step by step, showing arithmetic. "
              "End with a line: 'The answer is <number>'.")
VERIFY_SYS = ("You are a math verifier. You are given a problem and a proposed solution. "
              "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
AGG_SYS    = ("You are given a math problem and one or more candidate solutions. Decide the "
              "correct final answer by re-checking and majority. End with 'The answer is <number>'.")

t0 = time.time()
plans = [None] * n
produced = [[] for _ in range(n)]
def solve_user(i):
    u = questions[i]
    if P and plans[i]:
        u += "\n\nSuggested plan:\n" + plans[i]
    return u

# Planner stage on the 7B (batch 8), everything else on the 1.5B (batch 32).
if P:
    plans = gen([chat(md("P"), PLAN_SYS, q) for q in questions], 256, md("P"), bs("P"))
if S:
    sol = gen([chat(md("S"), SOLVE_SYS, solve_user(i)) for i in range(n)], 512, md("S"), bs("S"))
    for i, t in enumerate(sol):
        produced[i].append(t)
if V:
    prompts = [chat(md("V"), VERIFY_SYS, questions[i] + "\n\nProposed solution:\n" + produced[i][-1])
               if produced[i] else chat(md("V"), SOLVE_SYS, solve_user(i)) for i in range(n)]
    ver = gen(prompts, 512, md("V"), bs("V"))
    for i, t in enumerate(ver):
        produced[i].append(t)
if A:
    prompts = []
    for i in range(n):
        if produced[i]:
            body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(produced[i]))
            prompts.append(chat(md("A"), AGG_SYS, questions[i] + "\n\n" + body))
        else:
            prompts.append(chat(md("A"), SOLVE_SYS, solve_user(i)))
    agg = gen(prompts, 256, md("A"), bs("A"))
    for i, t in enumerate(agg):
        produced[i].append(t)

correct, preds = 0, []
for i in range(n):
    final = produced[i][-1] if produced[i] else None
    p, g = pred_answer(final), gold_answer(rows[i][1])
    ok = num_eq(p, g); correct += ok
    preds.append({"gold": g, "pred": p, "correct": bool(ok)})
acc = correct / n if n else 0.0
summary = {"config_id": CONFIG_ID, "mask": {"P": P, "S": S, "V": V, "A": A},
           "big_role": BIG_ROLE, "n": n, "correct": correct, "accuracy": acc,
           "seconds": round(time.time() - t0, 1)}
print("SUMMARY", json.dumps(summary), flush=True)
os.makedirs(OUT_DIR, exist_ok=True)
json.dump(summary, open(os.path.join(OUT_DIR, "summary.json"), "w"), indent=2)
json.dump(preds, open(os.path.join(OUT_DIR, "preds.json"), "w"))
print("done", flush=True)
