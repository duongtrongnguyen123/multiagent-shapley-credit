# PIPELINE v2: Planner -> iterate(Solve + Judge) với Judge nâng cấp (few-shot / vote).
#
# Bản v1 (solvejudge_kernel.py) đã đo: MATH loop .5133 > PSVA .4733 (5/5 fold), GSM8K thua.
# Khảo sát JUDGE_QUALITY.md: vote/few-shot chỉ nâng prec Judge <=.025 (null) NHƯNG khảo sát đó chỉ
# đo Judge trên S1, không chạy pipeline thật. Kernel này chạy pipeline ĐẦY ĐỦ với Judge nâng cấp:
#   JUDGE_MODE=single   : Judge greedy (mốc = bản v1)
#   JUDGE_MODE=fewshot  : Judge greedy + 1 đúng + 1 sai example
#   JUDGE_MODE=vote     : K=3 Judge độc lập, verdict = >=2/3 đồng thuận "đúng"
#
# Re-solve đổi temperature (1.0->0.7->0.4), budget 3 vòng, dừng sớm khi Judge bảo đúng.
# Baseline: S-alone, PSVA (cùng bài, cùng seed). Per-question trace đầy đủ.
import os, re, json, csv, glob, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N     = __N__
NF    = __NF__
BS    = __BS__
TASK  = "__TASK__"
JUDGE_MODE = "__JUDGE_MODE__"   # single | fewshot | vote
KVOTE = 3                        # số Judge độc lập khi vote
VOTE_THR = 2                     # >= 2/3 đồng thuận "đúng" -> dừng
MAXV  = 3
TEMP  = [1.0, 0.7, 0.4]

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "math_500_test.csv" if TASK == "math" else "main_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV, encoding="utf-8")))[:N]
print(f"TASK={TASK} MODE={JUDGE_MODE} N={N} NF={NF} fold={N//NF}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="auto").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx, shots=(), temp=1.0, seed=None):
    if seed is not None:
        torch.manual_seed(seed)
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
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=(temp < 1.0),
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
    PLAN_SYS   = ("You are a math planning assistant. Read the competition problem and give a "
                  "concise numbered plan of the solution steps. Do NOT compute the final answer.")
    SOLVE_SYS  = ("You are an expert mathematician. Solve the problem step by step. Put the "
                  "final answer in \\boxed{}.")
    JUDGE_SYS  = ("You are a strict math judge. You are given a problem and a proposed solution. "
                  "Reply with a single digit: 1 if the solution is correct, 0 if it is wrong.")
    VER_SYS    = ("You are a math verifier. Given a problem and a proposed solution, check each "
                  "step; if wrong, correct it. Put the final answer in \\boxed{}.")
    AGG_SYS    = ("You are given a problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking. Put the final answer in \\boxed{}.")
    q_of = lambda r: r["Question"].strip()
    def gold_of(r): return boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None
    PLAN_MX, SOLVE_MX, J_MX = 512, 1024, 8
    JUDGE_SHOTS = (
        ("Problem: What is $2+3\\times 4$?\n\nProposed solution:\nBy order of operations, "
         "$3\\times 4=12$, then $2+12=14$. The answer is $\\boxed{14}$.",
         "1"),
        ("Problem: What is $2+3\\times 4$?\n\nProposed solution:\n$2+3=5$, then "
         "$5\\times 4=20$. The answer is $\\boxed{20}$.",
         "0"),
    )
else:
    PLAN_SYS   = ("You are a math planning assistant. Read the problem and give a concise "
                  "numbered plan of the steps needed. Do NOT compute the final answer.")
    SOLVE_SYS  = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                  "End with a line: 'The answer is <number>'.")
    JUDGE_SYS  = ("You are a strict math judge. You are given a problem and a proposed solution. "
                  "Reply with a single digit: 1 if the solution is correct, 0 if it is wrong.")
    VER_SYS    = ("You are a math verifier. You are given a problem and a proposed solution. "
                  "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
    AGG_SYS    = ("You are given a math problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking and majority. End with 'The answer is "
                  "<number>'.")
    q_of = lambda r: r["question"].strip()
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    def pred(t):
        m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
        cands = m if m else NUM_RE.findall(t or "")
        return cands[-1].replace(",", "") if cands else None
    PLAN_MX, SOLVE_MX, J_MX = 256, 512, 8
    JUDGE_SHOTS = (
        ("Problem: Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes "
         "of babysitting. How much did she earn?\n\nProposed solution:\n50 minutes is 5/6 of "
         "an hour. 12 * 5/6 = 10. The answer is 10.",
         "1"),
        ("Problem: Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes "
         "of babysitting. How much did she earn?\n\nProposed solution:\n50 minutes is 1/2 of "
         "an hour. 12 * 1/2 = 6. The answer is 6.",
         "0"),
    )

def judge_verdicts(usrs):
    """Trả list verdict (0/1) cho từng câu theo JUDGE_MODE."""
    if JUDGE_MODE == "single":
        j = gen(JUDGE_SYS, usrs, J_MX, temp=1.0)
        return [read_digit(t) for t in j]
    if JUDGE_MODE == "fewshot":
        j = gen(JUDGE_SYS, usrs, J_MX, shots=JUDGE_SHOTS, temp=1.0)
        return [read_digit(t) for t in j]
    if JUDGE_MODE == "vote":
        votes = []
        for k in range(KVOTE):
            j = gen(JUDGE_SYS, usrs, J_MX, temp=(1.0 if k == 0 else TEMP[k]),
                    seed=2000 + k)
            votes.append([read_digit(t) for t in j])
        nq = len(usrs)
        out = []
        for i in range(nq):
            yes = sum(1 for k in range(KVOTE) if votes[k][i] == 1)
            out.append(1 if yes >= VOTE_THR else 0)
        return out

FOLD = N // NF
fold_stats, sample = [], []
for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n}) =====", flush=True)

    sol_alone = gen(SOLVE_SYS, list(qs), SOLVE_MX, temp=1.0)
    plans = gen(PLAN_SYS, list(qs), PLAN_MX, temp=1.0)
    ps_sol = gen(SOLVE_SYS, [f"{q}\n\nSuggested plan:\n{pl}" for q, pl in zip(qs, plans)], SOLVE_MX, temp=1.0)
    ps_ver = gen(VER_SYS, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, ps_sol)], SOLVE_MX, temp=1.0)
    ps_agg = gen(AGG_SYS, [f"{q}\n\nCandidate 1:\n{s}\n\nCandidate 2:\n{v}"
                  for q, s, v in zip(qs, ps_sol, ps_ver)], SOLVE_MX, temp=1.0)

    cur_s = ps_sol[:]
    stop_at = [None] * n
    sols, judges_all = [], []
    for v in range(MAXV):
        s_here = cur_s
        jv = judge_verdicts([f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, s_here)])
        sols.append(s_here)
        judges_all.append(jv)
        for i in range(n):
            if stop_at[i] is None and jv[i] == 1:
                stop_at[i] = v + 1
        if v < MAXV - 1:
            todo = [i for i in range(n) if stop_at[i] is None]
            if todo:
                nxt = gen(SOLVE_SYS,
                          [f"{q}\n\nSuggested plan:\n{pl}\nPlease solve again, more carefully."
                           for q, pl in zip([qs[i] for i in todo], [plans[i] for i in todo])],
                          SOLVE_MX, temp=TEMP[v+1], seed=1000 + v)
                cur_s = cur_s[:]
                for k, i in enumerate(todo):
                    cur_s[i] = nxt[k]
        else:
            for i in range(n):
                if stop_at[i] is None:
                    stop_at[i] = MAXV

    final_sol = [None] * n
    for i in range(n):
        final_sol[i] = sols[stop_at[i] - 1][i]

    ok_alone = [eq(pred(t), g) for t, g in zip(sol_alone, gs)]
    ok_psva  = [eq(pred(t), g) for t, g in zip(ps_agg, gs)]
    ok_loop  = [eq(pred(t), g) for t, g in zip(final_sol, gs)]
    d = {"acc_alone": sum(ok_alone)/n, "acc_psva": sum(ok_psva)/n,
         "acc_loop": sum(ok_loop)/n}
    d["stop_dist"] = {str(k): sum(1 for x in stop_at if x == k) for k in (1, 2, 3)}
    d["calls_avg"] = 1 + sum(2 * st for st in stop_at) / n
    j1 = judges_all[0]
    d["judge_prec"] = (sum(1 for i in range(n) if j1[i] == 1 and ok_alone[i])
                       / max(1, sum(1 for i in range(n) if j1[i] == 1)))
    d["judge_rec"]  = (sum(1 for i in range(n) if j1[i] == 1 and ok_alone[i])
                       / max(1, sum(1 for i in range(n) if ok_alone[i])))
    fold_stats.append(d)
    print("  " + " | ".join(f"{k} {d[k]:.3f}" for k in ("acc_alone", "acc_psva", "acc_loop"))
          + f" | stop {d['stop_dist']} | calls {d['calls_avg']:.2f}", flush=True)
    print(f"  judge prec {d['judge_prec']:.2f} rec {d['judge_rec']:.2f}", flush=True)

    for i in range(n):
        sample.append({"fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
                       "plan": plans[i], "sols": [sols[v][i] for v in range(len(sols))],
                       "judges": [judges_all[v][i] for v in range(len(judges_all))],
                       "stop_at": stop_at[i], "final_sol": final_sol[i],
                       "ok": {"alone": ok_alone[i], "psva": ok_psva[i], "loop": ok_loop[i]}})

    json.dump({"task": TASK, "judge_mode": JUDGE_MODE, "folds_done": f + 1, "n_folds": NF,
               "complete": f + 1 == NF, "per_fold": fold_stats},
              open("/kaggle/working/summary.json", "w"), indent=2)
    json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
    print(f"  [checkpoint] {f+1}/{NF}", flush=True)

def stats(xs):
    return {"mean": round(statistics.mean(xs), 4), "min": round(min(xs), 4),
            "max": round(max(xs), 4), "by_fold": [round(x, 4) for x in xs]}

out = {"task": TASK, "judge_mode": JUDGE_MODE, "n_folds": NF, "fold_size": N // NF,
       "complete": True, "arms": {}}
print("\n" + "=" * 70)
for a in ("acc_alone", "acc_psva", "acc_loop"):
    accs = [d[a] for d in fold_stats]
    out["arms"][a] = stats(accs)
    print(f"{a:<12} mean {statistics.mean(accs):.4f} min {min(accs):.4f} max {max(accs):.4f}")
for k in ("calls_avg", "judge_prec", "judge_rec"):
    out[k] = stats([d[k] for d in fold_stats])
    print(f"{k:<12} mean {statistics.mean([d[k] for d in fold_stats]):.4f}")
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
print("done", flush=True)