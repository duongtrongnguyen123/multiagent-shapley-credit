# BACKWARD vs FORWARD Planner — 2 GPU song song, cùng pipeline.
#
# Khảo sát (docs/BACKWARD_FEASIBILITY.md): GSM8K 95% target rõ -> backward tự nhiên; MATH 39%
# đại số trừu tượng -> backward cần prompt linh hoạt.
#
# Thiết kế: 2 model 1.5B, mỗi GPU 1 bản (đã mock OK: 2xT4, 3.1GB/GPU).
#   GPU0 -> FORWARD planner (plan hiện tại)
#   GPU1 -> BACKWARD planner (reason ngược từ mục tiêu)
# Hai pipeline ĐỘC LẬP chạy song song (thread), cùng bài, cùng seed -> so plan nào tốt hơn.
#
# PIPELINE tham số:
#   psva      : P -> S -> V -> A (4 call)
#   solvejudge: P -> lặp(S+J) budget 3, re-solve temp
# Cùng một kernel chạy cả 2 pipeline style nhưng CHỈ theo PIPELINE đã chọn.
# Per-question ghi: plan_forward, plan_backward, sol_f, sol_b, final, ok cả 2 nhánh.
import os, re, json, csv, glob, statistics, torch, threading
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK    = "__TASK__"       # math | gsm8k
PIPE    = "__PIPE__"       # psva | solvejudge
N       = __N__
NF      = __NF__
BS      = __BS__
MAXV    = 3
TEMP    = [1.0, 0.7, 0.4]

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "math_500_test.csv" if TASK == "math" else "main_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV, encoding="utf-8")))[:N]
print(f"TASK={TASK} PIPE={PIPE} N={N} NF={NF} device_count={torch.cuda.device_count()}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token

models = {}
for gpu in (0, 1):
    models[gpu] = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                                       device_map={"": gpu}).eval()
print("2 models loaded (GPU0 forward, GPU1 backward)", flush=True)

def gen(gpu, sysm, usrs, mx, shots=(), temp=1.0, seed=None):
    if seed is not None:
        torch.manual_seed(seed)
    m = models[gpu]
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = []
        for u in ch:
            msgs = [{"role": "system", "content": sysm}]
            for su, sa in shots:
                msgs += [{"role": "user", "content": su}, {"role": "assistant", "content": sa}]
            msgs.append({"role": "user", "content": u})
            ps.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
        e = tok(ps, return_tensors="pt", padding=True).to(m.device)
        with torch.no_grad():
            o = m.generate(**e, max_new_tokens=mx, do_sample=(temp < 1.0),
                           temperature=temp, pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    return outs

def read_digit(t):
    m = re.search(r"[01]", t or "")
    return int(m.group(0)) if m else None

def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0: return None
    i = s.find("{", i)
    if i < 0: return None
    d, st = 0, i
    for j in range(i, len(s)):
        if s[j] == "{": d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0: return s[st + 1:j]
    return None
NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def norm(a):
    if a is None: return None
    a = str(a).strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " ", ","]: a = a.replace(x, "")
    for x in ["\\(", "\\)", "\\[", "\\]"]: a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()
def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g: return False
    if p == g: return True
    try: return abs(float(p) - float(g)) < 1e-6
    except: return False

if TASK == "math":
    SOLVE_SYS_FWD = ("You are an expert mathematician. Solve the problem step by step. Put the "
                     "final answer in \\boxed{}.")
    SOLVE_SYS_BWD = ("You are an expert mathematician. A backward plan is given below, listed "
                     "from the target down to the leaf values. Solve the problem by starting "
                     "from the leaf (values directly given), compute each sub-goal in order, and "
                     "finish at the target. Show each step's arithmetic. Put the final answer in "
                     "\\boxed{}.")
    JUDGE_SYS  = ("You are a strict math judge. You are given a problem and a proposed solution. "
                  "Reply with a single digit: 1 if the solution is correct, 0 if it is wrong.")
    VER_SYS    = ("You are a math verifier. Given a problem and a proposed solution, check each "
                  "step; if wrong, correct it. Put the final answer in \\boxed{}.")
    AGG_SYS    = ("You are given a problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking. Put the final answer in \\boxed{}.")
    PLAN_FWD   = ("You are a math planning assistant. Read the competition problem and give a "
                  "concise numbered plan of the solution steps. Do NOT compute the final answer.")
    PLAN_BWD   = ("You are a math planning assistant. Do BACKWARD CHAINING to build a plan.\n"
                  "1. State the target quantity the problem asks for.\n"
                  "2. Ask: to get the target, what sub-quantities must be known first?\n"
                  "3. For each sub-quantity, keep asking what must be known, until every leaf is "
                  "a value directly given in the problem.\n"
                  "4. Output ONLY the final plan as a numbered list, ordered from first "
                  "computation to last. Do NOT compute any arithmetic. Do NOT restate the "
                  "question.\n\n"
                  "Example:\n"
                  "Problem: A shop sells apples at $2 each. Jill buys 3 apples and a $4 basket. "
                  "How much does she pay?\n"
                  "Target: total cost = apples cost + basket cost.\n"
                  "  apples cost <- $2/apple x 3 apples (given)\n"
                  "  basket cost <- $4 (given)\n"
                  "Plan:\n"
                  "1. apples cost = 2 * 3\n"
                  "2. total = apples cost + 4")
    q_of = lambda r: r["Question"].strip()
    def gold_of(r): return boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None
    PLAN_MX, SOLVE_MX, J_MX = 512, 1024, 8
    SOLVE_SHOTS = SOLVE_SHOTS_MATH
else:
    SOLVE_SYS_FWD = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                     "End with a line: 'The answer is <number>'.")
    SOLVE_SYS_BWD = ("You are a careful math solver. A backward plan is given below, listed "
                     "from the target down to the leaf values. Solve the problem by starting "
                     "from the leaf (values directly given), compute each sub-goal in order, and "
                     "finish at the target. Show each step's arithmetic. End with a line: "
                     "'The answer is <number>'.")
    JUDGE_SYS  = ("You are a strict math judge. You are given a problem and a proposed solution. "
                  "Reply with a single digit: 1 if the solution is correct, 0 if it is wrong.")
    VER_SYS    = ("You are a math verifier. You are given a problem and a proposed solution. "
                  "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
    AGG_SYS    = ("You are given a math problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking and majority. End with 'The answer is "
                  "<number>'.")
    PLAN_FWD   = ("You are a math planning assistant. Read the problem and give a concise "
                  "numbered plan of the steps needed. Do NOT compute the final answer.")
    PLAN_BWD   = ("You are a math planning assistant. Do BACKWARD CHAINING to build a plan.\n"
                  "1. State the target quantity the problem asks for.\n"
                  "2. Ask: to get the target, what sub-quantities must be known first?\n"
                  "3. For each sub-quantity, keep asking what must be known, until every leaf is "
                  "a value directly given in the problem.\n"
                  "4. Output ONLY the final plan as a numbered list, ordered from first "
                  "computation to last. Do NOT compute any arithmetic. Do NOT restate the "
                  "question.\n\n"
                  "Example:\n"
                  "Problem: Janet sells eggs. She lays 16 per day, eats 3, bakes with 4, sells "
                  "rest at $2 each. How much does she make daily?\n"
                  "Target: daily income = eggs sold x $2.\n"
                  "  eggs sold <- 16 - 3 - 4 (all given)\n"
                  "Plan:\n"
                  "1. eggs sold = 16 - 3 - 4\n"
                  "2. income = eggs sold * 2")
    q_of = lambda r: r["question"].strip()
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    def pred(t):
        m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
        cands = m if m else NUM_RE.findall(t or "")
        return cands[-1].replace(",", "") if cands else None
    PLAN_MX, SOLVE_MX, J_MX = 256, 512, 8

def run_planner(gpu, plan_sys, qs, plan_mx):
    return gen(gpu, plan_sys, list(qs), plan_mx, temp=1.0)

# Few-shot: cách giải một backward plan (leaf -> target)
SOLVE_SHOTS_MATH = (
    ("Problem: If $f(x)=3x+2$, what is $f(4)$?\n\nBackward plan:\n"
     "target <- f(4)\nleaf <- 4, f(x)=3x+2 (given)",
     "Start from the leaf: $f(4) = 3(4)+2 = 14$. The value of $f(4)$ is $\\boxed{14}$."),
)
SOLVE_SHOTS_GSM = (
    ("Problem: A rectangle is 5cm wide and 3cm long. What is its area?\n\nBackward plan:\n"
     "target <- area\nleaf <- width=5, length=3 (given)",
     "Start from the leaf: area $= 5 \\times 3 = 15$. The answer is 15."),
)
SOLVE_SHOTS = SOLVE_SHOTS_MATH if TASK == "math" else SOLVE_SHOTS_GSM

# ---- một pipeline đầy đủ trên 1 GPU (forward hoặc backward) ----
def run_pipe(gpu, plan_sys, solve_sys, solve_shots, qs, gs):
    """Chạy pipeline (psva | solvejudge) với plan từ plan_sys + Solver tương ứng. Trả kết quả."""
    n = len(qs)
    plans = run_planner(gpu, plan_sys, qs, PLAN_MX)
    wp = [f"{qs[i]}\n\nSuggested plan:\n{plans[i]}" for i in range(n)]
    if PIPE == "psva":
        sol = gen(gpu, solve_sys, wp, SOLVE_MX, shots=solve_shots, temp=1.0)
        ver = gen(gpu, VER_SYS, [f"{qs[i]}\n\nProposed solution:\n{sol[i]}" for i in range(n)],
                  SOLVE_MX, temp=1.0)
        agg = gen(gpu, AGG_SYS, [f"{qs[i]}\n\nCandidate 1:\n{sol[i]}\n\nCandidate 2:\n{ver[i]}"
                                 for i in range(n)], SOLVE_MX, temp=1.0)
        final = agg
        stop_at = [1] * n
        calls = [4] * n
        sols_by_round = [sol]
        judges_by_round = []
        return final, plans, stop_at, calls, sols_by_round, judges_by_round
    else:  # solvejudge
        cur_s = gen(gpu, solve_sys, wp, SOLVE_MX, shots=solve_shots, temp=1.0)   # S1 greedy with plan
        stop_at = [None] * n
        sols, judges = [], []
        for v in range(MAXV):
            j = gen(gpu, JUDGE_SYS, [f"{qs[i]}\n\nProposed solution:\n{cur_s[i]}" for i in range(n)],
                    J_MX, temp=1.0)
            jv = [read_digit(t) for t in j]
            sols.append(cur_s[:])
            judges.append(jv)
            for i in range(n):
                if stop_at[i] is None and jv[i] == 1:
                    stop_at[i] = v + 1
            if v < MAXV - 1:
                todo = [i for i in range(n) if stop_at[i] is None]
                if todo:
                    nxt = gen(gpu, solve_sys,
                              [f"{qs[i]}\n\nSuggested plan:\n{plans[i]}\nPlease solve again, "
                               f"more carefully." for i in todo],
                              SOLVE_MX, shots=solve_shots, temp=TEMP[v+1], seed=1000 + v)
                    cur_s = cur_s[:]
                    for k, i in enumerate(todo):
                        cur_s[i] = nxt[k]
            else:
                for i in range(n):
                    if stop_at[i] is None:
                        stop_at[i] = MAXV
        final = [None] * n
        for i in range(n):
            final[i] = sols[stop_at[i] - 1][i]
        calls = [1 + 2 * st for st in stop_at]
        return final, plans, stop_at, calls, sols, judges

FOLD = N // NF
fold_stats, sample = [], []

def process_fold(f):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n}) =====", flush=True)

    results = {}
    threads = []
    lock = threading.Lock()
    def worker(gpu, plan_sys, solve_sys, solve_shots, tag):
        final, plans, stop_at, calls, sols, judges = run_pipe(gpu, plan_sys, solve_sys,
                                                              solve_shots, qs, gs)
        with lock:
            results[tag] = {"final": final, "plans": plans, "stop_at": stop_at,
                            "calls": calls, "sols": sols, "judges": judges}
    # forward GPU0: plan forward + Solver cũ (không few-shot backward) | backward GPU1: plan bwd + Solver bwd
    th1 = threading.Thread(target=worker, args=(0, PLAN_FWD, SOLVE_SYS_FWD, (), "fwd"))
    th2 = threading.Thread(target=worker, args=(1, PLAN_BWD, SOLVE_SYS_BWD, SOLVE_SHOTS, "bwd"))
    th1.start(); th2.start(); th1.join(); th2.join()

    ok_f = [eq(pred(t), g) for t, g in zip(results["fwd"]["final"], gs)]
    ok_b = [eq(pred(t), g) for t, g in zip(results["bwd"]["final"], gs)]
    d = {"acc_fwd": sum(ok_f)/n, "acc_bwd": sum(ok_b)/n,
         "calls_fwd": sum(results["fwd"]["calls"])/n, "calls_bwd": sum(results["bwd"]["calls"])/n}
    if PIPE == "solvejudge":
        d["stop_fwd"] = {str(k): sum(1 for x in results["fwd"]["stop_at"] if x == k) for k in (1,2,3)}
        d["stop_bwd"] = {str(k): sum(1 for x in results["bwd"]["stop_at"] if x == k) for k in (1,2,3)}
    # plan length (proxy chất lượng plan)
    d["plan_len_fwd"] = statistics.mean([len(p) for p in results["fwd"]["plans"]])
    d["plan_len_bwd"] = statistics.mean([len(p) for p in results["bwd"]["plans"]])
    fold_stats.append(d)
    print(f"  fwd {d['acc_fwd']:.4f} calls {d['calls_fwd']:.2f} | bwd {d['acc_bwd']:.4f} "
          f"calls {d['calls_bwd']:.2f} | plan_len {d['plan_len_fwd']:.0f}/{d['plan_len_bwd']:.0f}",
          flush=True)

    for i in range(n):
        sample.append({"fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
                       "plan_fwd": results["fwd"]["plans"][i],
                       "plan_bwd": results["bwd"]["plans"][i],
                       "final_fwd": results["fwd"]["final"][i],
                       "final_bwd": results["bwd"]["final"][i],
                       "ok": {"fwd": ok_f[i], "bwd": ok_b[i]}})

    json.dump({"task": TASK, "pipe": PIPE, "folds_done": f + 1, "n_folds": NF,
               "complete": f + 1 == NF, "per_fold": fold_stats},
              open("/kaggle/working/summary.json", "w"), indent=2)
    json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
    print(f"  [checkpoint] {f+1}/{NF}", flush=True)

for f in range(NF):
    process_fold(f)

def stats(xs):
    return {"mean": round(statistics.mean(xs), 4), "min": round(min(xs), 4),
            "max": round(max(xs), 4), "by_fold": [round(x, 4) for x in xs]}

out = {"task": TASK, "pipe": PIPE, "n_folds": NF, "fold_size": N // NF, "complete": True}
print("\n" + "=" * 70)
for k in ("acc_fwd", "acc_bwd", "calls_fwd", "calls_bwd"):
    out[k] = stats([d[k] for d in fold_stats])
    print(f"{k:<12} mean {statistics.mean([d[k] for d in fold_stats]):.4f}")
if PIPE == "solvejudge":
    out["plan_len"] = {"fwd": stats([d["plan_len_fwd"] for d in fold_stats]),
                       "bwd": stats([d["plan_len_bwd"] for d in fold_stats])}
    print(f"plan_len fwd {out['plan_len']['fwd']['mean']:.0f} bwd {out['plan_len']['bwd']['mean']:.0f}")
# chênh lệch
diffs = [d["acc_bwd"] - d["acc_fwd"] for d in fold_stats]
out["bwd_minus_fwd"] = stats(diffs)
win = sum(1 for x in diffs if x > 0)
print(f"bwd - fwd: {statistics.mean(diffs):+.4f} (bwd thang {win}/{NF} fold)")
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
print("done", flush=True)