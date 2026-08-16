# A-SEL vs BỎ PHIẾU CƠ HỌC — cùng bộ bài, cùng ứng viên.
#
# Câu hỏi: "Aggregator trained (A-SEL) có thực sự tốt hơn majority vote không?"
# Các thí nghiệm vote3/vote5 cũ (AGG_FORMAT_CHECK) chạy MATH n=150 còn A-SEL eval chạy
# GSM8K/MATH n=200 — KHÔNG cùng setup nên không so trực tiếp được. Kernel này đo cả 6 nhánh
# trên CÙNG fold, CÙNG ứng viên:
#   S        : 1 Solver greedy                       (mốc)
#   vote2    : majority 2  [sol, verifier]           (cùng 2 ứng viên như A-SEL)
#   vote3    : majority 3  [sol, s1, s2]             (bỏ phiếu cơ học K=3)
#   vote5    : majority 5  [sol, s1..s4]             (bỏ phiếu cơ học K=5, đối chứng then chốt)
#   A_base   : LLM base chọn [sol, verifier]         (AGG_SYS_SEL, adapter tắt)
#   A_sel    : LLM A-SEL chọn [sol, verifier]        (adapter asel bật)
#
# So sánh công bằng: vote2 vs A_base vs A_sel (cùng 2 ứng viên). Nếu A_sel > vote2 -> selection
# LLM trained có giá trị hơn bỏ phiếu cơ học trên cùng đầu vào; vote3/vote5 cho biết bỏ phiếu
# với NHIỀU ứng viên hơn có qua mặt A-SEL không.
import os, sys, re, csv, json, glob, statistics, subprocess
from collections import Counter

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

TASK = __TASK__  # "gsm8k"|"math"
N  = __N__
NF = __NF__
BS = __BS__
TEMP = 0.7

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13,<0.15"], check=False)
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

FOLD = N // NF
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
_a = sorted(glob.glob("/kaggle/input/**/adapter_config.json", recursive=True), key=len)
if not _a:
    raise FileNotFoundError("khong thay adapter (asel) :: " + str(glob.glob("/kaggle/input/**", recursive=True)[:30]))
ADAPTER = os.path.dirname(_a[0])

FNAME = "main_test.csv" if TASK == "gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} {NF} fold x {FOLD} | adapter={ADAPTER}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
base = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                            device_map={"": 0}).eval()
model = PeftModel.from_pretrained(base, ADAPTER, adapter_name="A")
model.eval()

import contextlib

@contextlib.contextmanager
def _null():
    yield

def gen(sysm, usrs, mx, do_sample=False, seed=None, role=None):
    if seed is not None:
        torch.manual_seed(seed)
    outs = []
    ctx = (model.disable_adapter() if role is None else _null())
    with ctx:
        for i in range(0, len(usrs), BS):
            ch = usrs[i:i + BS]
            ps = [tok.apply_chat_template([{"role": "system", "content": sysm},
                                           {"role": "user", "content": u}],
                                          tokenize=False, add_generation_prompt=True) for u in ch]
            e = tok(ps, return_tensors="pt", padding=True).to(model.device)
            with torch.no_grad():
                o = model.generate(**e, max_new_tokens=mx, do_sample=do_sample,
                                   temperature=TEMP if do_sample else 1.0,
                                   pad_token_id=tok.pad_token_id)
            L = e["input_ids"].shape[1]
            outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip()
                     for j in range(len(ch))]
    return outs

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
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
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
    except (ValueError, TypeError): return False

if TASK == "gsm8k":
    SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                 "End with a line: 'The answer is <number>'.")
    VERIFY_SYS = ("You are a math verifier. You are given a problem and a proposed solution. "
                  "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
    MX = 512
    q_of = lambda r: r["question"]
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    def pred(t):
        m = (re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
             or NUM.findall(t or ""))
        return m[-1].replace(",", "") if m else None
else:
    SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the "
                 "final answer in \\boxed{}.")
    VERIFY_SYS = ("You are a math verifier. Given a problem and a proposed solution, check each "
                  "step; if wrong, correct it. Put the final answer in \\boxed{}.")
    MX = 1024
    q_of = lambda r: r["Question"]
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None

AGG_SEL = ("You are given a math problem and two candidate solutions. Determine which "
           "candidate gives the correct final answer. Output ONLY the number of the "
           "correct candidate: '1' or '2'. No explanation.")
SEL_RE = re.compile(r"\b([12])\b")
def select_idx(text):
    if not text: return None
    m = SEL_RE.search(text)
    return int(m.group(1)) if m else None

def agg_user(q, cands):
    body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(cands))
    return f"{q}\n\n{body}"

def majority(answers):
    keys = [norm(a) for a in answers if norm(a)]
    if not keys:
        return None
    top = Counter(keys).most_common(1)[0][0]
    for a in answers:
        if norm(a) == top:
            return a
    return None

ARMS = ["S", "vote2", "vote3", "vote5", "A_base", "A_sel"]
fold_stats, sample = [], []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n} bai) =====", flush=True)

    sol = gen(SOLVE_SYS, list(qs), MX)
    ver = gen(VERIFY_SYS, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, sol)], MX)
    samp = [gen(SOLVE_SYS, list(qs), MX, do_sample=True, seed=2000 + k) for k in range(4)]
    cands5 = [[sol[i]] + [samp[k][i] for k in range(4)] for i in range(n)]

    vote2 = [majority([sol[i], ver[i]]) for i in range(n)]
    vote3 = [majority(cands5[i][:3]) for i in range(n)]
    vote5 = [majority(cands5[i]) for i in range(n)]

    sel_base = gen(AGG_SEL, [agg_user(qs[i], [sol[i], ver[i]]) for i in range(n)], 32, role=None)
    sel_sel  = gen(AGG_SEL, [agg_user(qs[i], [sol[i], ver[i]]) for i in range(n)], 32, role="A")
    a_base = [sol[i] if select_idx(sel_base[i]) == 1 else ver[i] for i in range(n)]
    a_sel  = [sol[i] if select_idx(sel_sel[i]) == 1 else ver[i] for i in range(n)]

    ok = {
        "S":      [eq(pred(t), g) for t, g in zip(sol, gs)],
        "vote2":  [eq(v, g) for v, g in zip(vote2, gs)],
        "vote3":  [eq(v, g) for v, g in zip(vote3, gs)],
        "vote5":  [eq(v, g) for v, g in zip(vote5, gs)],
        "A_base": [eq(pred(t), g) for t, g in zip(a_base, gs)],
        "A_sel":  [eq(pred(t), g) for t, g in zip(a_sel, gs)],
    }
    d = {f"acc_{a}": sum(ok[a]) / n for a in ARMS}
    d["sel_idx_valid"] = sum(1 for i in range(n) if select_idx(sel_sel[i]) is not None) / n
    d["sel_matches_vote2"] = sum(1 for i in range(n)
                                 if vote2[i] is not None
                                 and eq(pred(a_sel[i]), vote2[i])) / n
    d["mean_distinct_answers"] = statistics.mean(
        len({norm(pred(c)) for c in cands5[i] if norm(pred(c))}) for i in range(n))
    fold_stats.append(d)
    print("  " + " | ".join(f"{a} {d[f'acc_{a}']:.3f}" for a in ARMS), flush=True)
    print(f"  sel_idx_valid {d['sel_idx_valid']:.2f} | "
          f"A_sel trung vote2 {d['sel_matches_vote2']:.2f} | "
          f"so dap an khac nhau tb {d['mean_distinct_answers']:.2f}/5", flush=True)

    for i in range(n):
        sample.append({
            "fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
            "sol": sol[i], "ver": ver[i],
            "samps": cands5[i][1:], "vote2": vote2[i], "vote3": vote3[i],
            "vote5": vote5[i], "a_base": a_base[i], "a_sel": a_sel[i],
            "sel_base": sel_base[i], "sel_sel": sel_sel[i],
            "ok": {a: ok[a][i] for a in ARMS}})

print("\n===== TONG KET =====", flush=True)
agg = {f"acc_{a}": statistics.mean(d[f"acc_{a}"] for d in fold_stats) for a in ARMS}
print("  " + " | ".join(f"{a} {agg[f'acc_{a}']:.3f}" for a in ARMS), flush=True)
for a in ARMS:
    signs = [1 if d[f"acc_{a}"] >= d["acc_S"] else -1 for d in fold_stats]
    print(f"  {a} vs S: fold+ {sum(1 for s in signs if s > 0)}/{NF}", flush=True)
gain_sel_v2 = agg["acc_A_sel"] - agg["acc_vote2"]
gain_sel_v5 = agg["acc_A_sel"] - agg["acc_vote5"]
gain_sel_base = agg["acc_A_sel"] - agg["acc_A_base"]
print(f"  A_sel - vote2 = {gain_sel_v2:+.3f} | A_sel - vote5 = {gain_sel_v5:+.3f} | "
      f"A_sel - A_base = {gain_sel_base:+.3f}", flush=True)

json.dump({"task": TASK, "n": N, "nf": NF, "arms": ARMS, "agg": agg,
           "fold_stats": fold_stats, "gains": {"A_sel_minus_vote2": gain_sel_v2,
                                               "A_sel_minus_vote5": gain_sel_v5,
                                               "A_sel_minus_A_base": gain_sel_base},
           "sample": sample}, open("asel_vs_vote.json", "w"))
print("saved asel_vs_vote.json", flush=True)