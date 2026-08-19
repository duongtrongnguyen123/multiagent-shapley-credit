# Debate-planner experiment on MATH-500. Same 16-coalition PSVA mask + \boxed{} grader as
# template_math.py, but the Planner stage has 3 modes (baked at deploy):
#   single   - 1 greedy plan (== original template behaviour)
#   sampling - 3 sampled plans -> judge merges (no critique) [control for sampling effect]
#   debate   - 3 sampled plans -> cross-critique -> each planner rewrites its own plan
#              -> judge produces the final plan [anti-anchoring, "debate"]
# Solver/Verifier/Aggregator unchanged. P=0 coalitions skip the planner entirely (reuse logic).
import os, re, csv, json, time, glob, gc
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

CONFIG_ID = "__CONFIG_ID__"
MASK      = (__P__, __S__, __V__, __A__)
N_EVAL    = __N_EVAL__
PLAN_MODE = "__PLAN_MODE__"
N_PLAN    = 3
SAMPLE_TEMP = 0.7
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
print(f"CONFIG {CONFIG_ID} MASK P={P} S={S} V={V} A={A} N={N_EVAL} PLAN_MODE={PLAN_MODE}", flush=True)
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
# ---- debate-specific prompts (Planner stage only) --------------------------
CRITIQUE_SYS = ("You are a critical math planner. Given a problem and a set of proposed plans, "
                "review the OTHER plans (not your own): point out calculation errors, missing "
                "steps, and risky assumptions. Do NOT propose a new plan.")
REWRITE_SYS  = ("You are a math planner. You have your own plan for a problem, plus critiques of "
                "it from two peers. Rewrite YOUR plan to fix the flaws they flagged and keep what "
                "is correct. Give a concise numbered plan. Do NOT compute the final answer.")
JUDGE_SYS    = ("You are a senior math planner. Given several proposed plans (and possibly their "
                "critiques), produce ONE concise merged plan that keeps the best steps and avoids "
                "the flagged flaws. Do NOT compute the final answer.")

def chat(system, user):
    return tok.apply_chat_template(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        tokenize=False, add_generation_prompt=True)

# Progress logging: [tag] k/n gives a live view of how many MATH questions a stage
# has finished (written to stderr-less stdout so it shows in the Kaggle kernel log).
_DONE = {"propose": 0, "critique": 0, "rewrite": 0, "judge": 0, "solve": 0,
         "verify": 0, "agg": 0}
def log_progress(tag, done, total):
    _DONE[tag] = done
    print(f"[{tag.upper()}] done {done}/{total}", flush=True)

def gen(prompts, max_new, do_sample=False, temp=1.0, tag=None, total=None):
    outs = []
    for i in range(0, len(prompts), BATCH):
        chunk = prompts[i:i + BATCH]
        enc = tok(chunk, return_tensors="pt", padding=True).to("cuda")
        with torch.no_grad():
            o = model.generate(**enc, max_new_tokens=max_new, do_sample=do_sample,
                               temperature=temp, pad_token_id=tok.pad_token_id)
        outs += tok.batch_decode(o[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        if tag:
            log_progress(tag, min(i + BATCH, len(prompts)), total or len(prompts))
    return outs

t0 = time.time()

# ---- Planner stage: single / sampling / debate ------------------------------
# Returns one merged plan (str) for every question.
def plan_for_question(q):
    if PLAN_MODE == "single":
        return gen([chat(PLAN_SYS, q)], 512, do_sample=False, tag="propose", total=1)[0]

    # sampling / debate: draw N_PLAN diverse plans via sampling with fixed seeds
    plans = []
    for j in range(N_PLAN):
        torch.manual_seed(1000 + j)
        plans.append(gen([chat(PLAN_SYS, q)], 512, do_sample=True, temp=SAMPLE_TEMP,
                         tag="propose", total=N_PLAN)[0])

    if PLAN_MODE == "sampling":
        # control: judge merges the sampled plans WITHOUT any critique
        body = "\n\n".join(f"Plan {k+1}:\n{p}" for k, p in enumerate(plans))
        return gen([chat(JUDGE_SYS, q + "\n\n" + body)], 512, do_sample=False,
                   tag="judge", total=1)[0]

    # debate: cross-critique, each planner rewrites its own plan, then judge merges
    critiques = []
    for j in range(N_PLAN):
        others = [p for k, p in enumerate(plans) if k != j]
        body = "\n\n".join(f"Plan {k+1}:\n{p}" for k, p in enumerate(others))
        critiques.append(gen([chat(CRITIQUE_SYS, q + "\n\n" + body)], 384, do_sample=False,
                             tag="critique", total=N_PLAN)[0])

    rewrites = []
    for j in range(N_PLAN):
        others_crit = [c for k, c in enumerate(critiques) if k != j]
        body = ("Your own plan:\n" + plans[j] + "\n\nPeer critiques:\n"
                + "\n\n".join(f"Critique {k+1}:\n{c}" for k, c in enumerate(others_crit)))
        rewrites.append(gen([chat(REWRITE_SYS, q + "\n\n" + body)], 512, do_sample=False,
                            tag="rewrite", total=N_PLAN)[0])

    # Judge merges the rewritten plans (+ the critiques that produced them) into one plan.
    merge_body = "\n\n".join(f"Revised plan {k+1}:\n{p}" for k, p in enumerate(rewrites))
    crit_body = "\n\n".join(f"Critique {k+1}:\n{c}" for k, c in enumerate(critiques))
    return gen([chat(JUDGE_SYS, q + "\n\n" + merge_body + "\n\n" + crit_body)], 512,
               do_sample=False)[0]

# ---- Checkpoint helpers --------------------------------------------------
CKPT_DIR = os.path.join(OUT_DIR, "ckpt")
os.makedirs(CKPT_DIR, exist_ok=True)

def ckpt_path(tag):
    return os.path.join(CKPT_DIR, f"{tag}.json")

def save_ckpt(tag, data):
    json.dump(data, open(ckpt_path(tag), "w"))
    print(f"[CKPT] saved {tag} ({len(data) if isinstance(data, (list, dict)) else 1} items)", flush=True)

def load_ckpt(tag):
    p = ckpt_path(tag)
    if os.path.exists(p):
        d = json.load(open(p))
        print(f"[CKPT] loaded {tag} ({len(d) if isinstance(d, (list, dict)) else 1} items)", flush=True)
        return d
    return None

plans = [None] * n
if P:
    cached = load_ckpt("plans")
    if cached is not None:
        plans = cached
    else:
        for qi, q in enumerate(questions):
            plans[qi] = plan_for_question(q)
            if (qi + 1) % 10 == 0:
                save_ckpt("plans", plans)
                print(f"[plan] {qi+1}/{n}", flush=True)
        save_ckpt("plans", plans)

produced = [None] * n  # None = chua xu ly; list = da co output

def solve_user(i):
    u = questions[i]
    if P and plans[i]:
        u += "\n\nSuggested plan:\n" + plans[i]
    return u

# Solve stage (with checkpoint)
cached = load_ckpt("solve")
if cached is not None:
    produced = [c if c else [] for c in cached]
if S:
    todo = [i for i in range(n) if not produced[i]]
    for bi in range(0, len(todo), BATCH):
        batch_idx = todo[bi:bi+BATCH]
        prompts = [chat(SOLVE_SYS, solve_user(i)) for i in batch_idx]
        sol = gen(prompts, 1024, tag="solve", total=len(todo))
        for i, t in zip(batch_idx, sol):
            produced[i] = [t]
        if (bi + BATCH) % (BATCH * 3) < BATCH:
            save_ckpt("solve", produced)
    save_ckpt("solve", produced)

# Verify stage (with checkpoint)
cached = load_ckpt("verify")
if cached is not None:
    for i, c in enumerate(cached):
        if c and len(c) > len(produced[i] or []):
            produced[i] = c
if V:
    todo = [i for i in range(n) if produced[i] and len(produced[i]) < 2]
    for bi in range(0, len(todo), BATCH):
        batch_idx = todo[bi:bi+BATCH]
        prompts = [chat(VERIFY_SYS, questions[i] + "\n\nProposed solution:\n" + produced[i][-1])
                   for i in batch_idx]
        ver = gen(prompts, 1024, tag="verify", total=len(todo))
        for i, t in zip(batch_idx, ver):
            produced[i].append(t)
        if (bi + BATCH) % (BATCH * 3) < BATCH:
            save_ckpt("verify", produced)
    save_ckpt("verify", produced)

# Aggregator stage (with checkpoint)
cached = load_ckpt("agg")
if cached is not None:
    for i, c in enumerate(cached):
        if c and len(c) > len(produced[i] or []):
            produced[i] = c
if A:
    todo = [i for i in range(n) if produced[i] and len(produced[i]) < 3]
    for bi in range(0, len(todo), BATCH):
        batch_idx = todo[bi:bi+BATCH]
        prompts = []
        for i in batch_idx:
            body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(produced[i]))
            prompts.append(chat(AGG_SYS, questions[i] + "\n\n" + body))
        agg = gen(prompts, 1024, tag="agg", total=len(todo))
        for i, t in zip(batch_idx, agg):
            produced[i].append(t)
        if (bi + BATCH) % (BATCH * 3) < BATCH:
            save_ckpt("agg", produced)
    save_ckpt("agg", produced)

# Ensure all produced entries are lists
produced = [p or [] for p in produced]

correct, preds = 0, []
for i in range(n):
    final = produced[i][-1] if produced[i] else None
    p, g = pred_answer(final), last_boxed(rows[i][1])
    ok = math_eq(p, g); correct += ok
    preds.append({"gold": g, "pred": p, "correct": bool(ok)})
acc = correct / n if n else 0.0
summary = {"config_id": CONFIG_ID, "mask": {"P": P, "S": S, "V": V, "A": A},
           "plan_mode": PLAN_MODE, "dataset": "MATH-500", "n": n, "correct": correct,
           "accuracy": acc, "seconds": round(time.time() - t0, 1)}
print("SUMMARY", json.dumps(summary), flush=True)
os.makedirs(OUT_DIR, exist_ok=True)
json.dump(summary, open(os.path.join(OUT_DIR, "summary.json"), "w"), indent=2)
json.dump(preds, open(os.path.join(OUT_DIR, "preds.json"), "w"))
print("done", flush=True)
