# KHẢO SÁT: few-shot Judge có nâng chất lượng Judge không?
#
# Bối cảnh (docs/SOLVEJUDGE.md): Judge 1.5B binary là điểm nghẽn — MATH prec .52 (39 false-pos),
# GSM8K prec .33 (chê sai 70/84 câu đúng). Câu hỏi: thêm few-shot ví dụ (problem + solution + đúng
# verdict) vào prompt Judge có cải thiện precision/recall không?
#
# Thiết kế khớp judgevote_kernel.py — tái tạo S1 greedy (khớp solvejudge v1), rồi chạy Judge:
#   judge0   : Judge greedy KHÔNG few-shot (mốc, = baseline solvejudge)
#   judge_fs : Judge greedy CÓ few-shot examples
# Cả hai trên cùng lời giải S1, cùng seed. Đo prec/rec theo S1-correct thực tế.
#
# Few-shot examples (đúng/sai xen kẽ):
#   - 1 ví dụ lời giải ĐÚNG -> verdict 1
#   - 1 ví dụ lời giải SAI  -> verdict 0
# Dạy Judge phân biệt lời giải đúng vs sai, không chỉ theo format.
import os, re, json, glob, csv, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "__TASK__"     # "math" | "gsm8k"
BS   = __BS__

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
print(f"TASK={TASK}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="auto").eval()
print("model loaded", flush=True)

JUDGE_SYS = ("You are a strict math judge. You are given a problem and a proposed solution. "
             "Reply with a single digit: 1 if the solution is correct, 0 if it is wrong.")

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

FNAME = "math_500_test.csv" if TASK == "math" else "main_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV, encoding="utf-8")))[:150]

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
    q_of = lambda r: r["Question"].strip()
    gold_of = lambda r: boxed(r["Answer"])
    SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the "
                 "final answer in \\boxed{}.")
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None
    JUDGE_SHOTS = (
        # ví dụ ĐÚNG -> verdict 1
        ("Problem: What is $2+3\\times 4$?\n\nProposed solution:\nBy order of operations, "
         "$3\\times 4=12$, then $2+12=14$. The answer is $\\boxed{14}$.",
         "1"),
        # ví dụ SAI -> verdict 0
        ("Problem: What is $2+3\\times 4$?\n\nProposed solution:\n$2+3=5$, then "
         "$5\\times 4=20$. The answer is $\\boxed{20}$.",
         "0"),
    )
else:
    q_of = lambda r: r["question"].strip()
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                 "End with a line: 'The answer is <number>'.")
    def pred(t):
        m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
        cands = m if m else NUM_RE.findall(t or "")
        return cands[-1].replace(",", "") if cands else None
    JUDGE_SHOTS = (
        # ví dụ ĐÚNG -> verdict 1
        ("Problem: Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes "
         "of babysitting. How much did she earn?\n\nProposed solution:\n50 minutes is 5/6 of "
         "an hour. 12 * 5/6 = 10. The answer is 10.",
         "1"),
        # ví dụ SAI -> verdict 0
        ("Problem: Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes "
         "of babysitting. How much did she earn?\n\nProposed solution:\n50 minutes is 1/2 of "
         "an hour. 12 * 1/2 = 6. The answer is 6.",
         "0"),
    )

qs = [q_of(r) for r in ALL]
gs = [gold_of(r) for r in ALL]
n = len(ALL)

# S1 greedy (khớp solvejudge v1)
S1 = gen(SOLVE_SYS, list(qs), 1024, temp=1.0)
s1_ok = [eq(pred(t), g) for t, g in zip(S1, gs)]
print(f"S1 acc: {sum(s1_ok)/n:.3f}", flush=True)

# Judge greedy KHÔNG few-shot (mốc)
j0 = gen(JUDGE_SYS, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, S1)], 8, temp=1.0)
j0v = [read_digit(t) for t in j0]
# Judge greedy CÓ few-shot
j1 = gen(JUDGE_SYS, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, S1)], 8,
         shots=JUDGE_SHOTS, temp=1.0)
j1v = [read_digit(t) for t in j1]
print(f"parsed: judge0 {sum(1 for x in j0v if x is not None)}/{n}, "
      f"judge_fs {sum(1 for x in j1v if x is not None)}/{n}", flush=True)

def prec_rec(v):
    tp = sum(1 for i in range(n) if v[i] == 1 and s1_ok[i])
    fp = sum(1 for i in range(n) if v[i] == 1 and not s1_ok[i])
    fn = sum(1 for i in range(n) if v[i] == 0 and s1_ok[i])
    return {"prec": tp/max(1, tp+fp), "rec": tp/max(1, tp+fn),
            "tp": tp, "fp": fp, "fn": fn, "n_yes": sum(1 for x in v if x == 1)}

r0 = prec_rec(j0v)
r1 = prec_rec(j1v)
print("\n=== MATH/GSM8K few-shot Judge ===")
print(f"  judge0 (baseline): prec {r0['prec']:.3f} rec {r0['rec']:.3f} | tp {r0['tp']} "
      f"fp {r0['fp']} fn {r0['fn']} | yes {r0['n_yes']}/{n}")
print(f"  judge_fs          : prec {r1['prec']:.3f} rec {r1['rec']:.3f} | tp {r1['tp']} "
      f"fp {r1['fp']} fn {r1['fn']} | yes {r1['n_yes']}/{n}")
print(f"  Δ prec {r1['prec']-r0['prec']:+.3f} | Δ rec {r1['rec']-r0['rec']:+.3f}")

json.dump({"task": TASK, "n": n, "s1_acc": sum(s1_ok)/n,
           "baseline": r0, "fewshot": r1}, open("/kaggle/working/judgefewshot.json", "w"),
          indent=2, ensure_ascii=False)
print("done", flush=True)