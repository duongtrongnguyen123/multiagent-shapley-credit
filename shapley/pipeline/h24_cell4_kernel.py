# H24 — Ô THỨ 4 CỦA LƯỚI 2×2: MATH 7B, S_pln vs V_bli vs V_inf
# Xem docs/PREREGISTRATION.md #24. 3/4 ô đã đo: "khung kiểm không mang thông tin, mỏ neo mới mang".
# Ô cuối: MATH 7B — S có kế hoạch (S_pln) vs V bịt mắt (V_bli) vs V đầy đủ (V_inf).
#
# Thiết kế: 7B 4-bit, MATH-500, 5 fold x 30 = 150 bài.
#   S_alone : Solver một mình (mốc)
#   S_pln   : Solver nhận kế hoạch từ Planner (P->S)
#   V_inf   : P->S->V, Verifier thấy TOÀN VĂN lời giải
#   V_bli   : P->S->V, Verifier chỉ thấy ĐÁP ÁN (bịt mắt)
# Nếu V_bli >= V_inf -> "khung kiểm không mang thông tin" xác nhận ở ô thứ 4.
import os, re, csv, json, glob, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "math"
N = __N__
BS = __BS__

import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes>=0.46.1"])

_c = glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True) or \
     glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV, encoding="utf-8")))[:N]
NF = 5
FOLD = N // NF
print(f"TASK={TASK} N={N} NF={NF} FOLD={FOLD}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL)
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

from transformers import BitsAndBytesConfig
_b = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True)
model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=_b,
                                              device_map="auto").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx=768):
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
    print(f"   ...{len(usrs)}", flush=True)
    return outs

def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0:
        return None
    i = s.find("{", i)
    if i < 0:
        return None
    d, st = 0, i
    for j in range(i, len(s)):
        if s[j] == "{":
            d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0:
                return s[st + 1:j]
    return None

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

def norm(a):
    if a is None:
        return None
    a = str(a).strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " ", ","]:
        a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()

def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g:
        return False
    if p == g:
        return True
    try:
        return abs(float(p) - float(g)) < 1e-6
    except:
        return False

gold_of = lambda r: boxed(r["Answer"])
q_of = lambda r: r["Question"]
TAIL = "Put the final answer in \\boxed{}."
fmt = lambda a: f"The answer is \\boxed{{{a}}}."

def pred(t):
    b = boxed(t)
    if b is not None:
        return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
    return m[-1].strip() if m else None

PLAN = "Give a concise numbered plan. Do NOT compute the final answer."
SOLVE = f"Solve step by step. {TAIL}"
VERIFY = f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"

folds = []
for fi in range(NF):
    rows = ALL[fi * FOLD:(fi + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"== FOLD {fi} (n={n}) ==", flush=True)

    def acc(a):
        return round(sum(eq(x, g) for x, g in zip(a, gs)) / len(gs), 4)

    # --- S_alone: Solver một mình ---
    solo = [pred(s) for s in gen(SOLVE, qs, 768)]
    acc_solo = acc(solo)
    print(f"  [S_alone] acc={acc_solo}", flush=True)

    # --- Planner ---
    plans = gen(PLAN, qs, 320)

    # --- S_pln: Solver nhận kế hoạch ---
    s_pln = gen(SOLVE, [f"{q}\n\nPlan:\n{p}" for q, p in zip(qs, plans)], 768)
    sa_pln = [pred(x) for x in s_pln]
    acc_pln = acc(sa_pln)
    print(f"  [S_pln] acc={acc_pln}", flush=True)

    # --- V_inf: Verifier thấy TOÀN VĂN ---
    v_inf = gen(VERIFY, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, s_pln)], 768)
    va_inf = [pred(x) for x in v_inf]
    acc_vinf = acc(va_inf)
    print(f"  [V_inf] acc={acc_vinf}", flush=True)

    # --- V_bli: Verifier chỉ thấy ĐÁP ÁN ---
    v_bli = gen(VERIFY, [f"{q}\n\nProposed solution:\n{fmt(a)}" for q, a in zip(qs, sa_pln)], 768)
    va_bli = [pred(x) for x in v_bli]
    acc_vbli = acc(va_bli)
    print(f"  [V_bli] acc={acc_vbli}", flush=True)

    r = {"fold": fi, "n": n,
         "acc_solo": acc_solo,
         "acc_s_pln": acc_pln,
         "acc_v_inf": acc_vinf,
         "acc_v_bli": acc_vbli,
         "pln_gain": round(acc_pln - acc_solo, 4),
         "vinf_gain": round(acc_vinf - acc_pln, 4),
         "vbli_gain": round(acc_vbli - acc_pln, 4),
         "vbli_minus_vinf": round(acc_vbli - acc_vinf, 4)}
    folds.append(r)
    print(f"  [fold {fi}] {json.dumps(r)}", flush=True)

    json.dump({"task": TASK, "folds_done": fi + 1, "n_folds": NF,
               "complete": fi + 1 == NF, "folds": folds},
              open("/kaggle/working/summary.json", "w"), indent=2)

def spread(key):
    v = [f[key] for f in folds]
    return {"mean": round(statistics.mean(v), 4),
            "min": round(min(v), 4),
            "max": round(max(v), 4),
            "range": round(max(v) - min(v), 4),
            "std": round(statistics.pstdev(v), 4),
            "by_fold": [round(x, 4) for x in v]}

out = {"task": TASK, "n": N, "n_folds": NF, "fold_n": FOLD, "folds": folds,
       "acc_solo": spread("acc_solo"),
       "acc_s_pln": spread("acc_s_pln"),
       "acc_v_inf": spread("acc_v_inf"),
       "acc_v_bli": spread("acc_v_bli"),
       "pln_gain": spread("pln_gain"),
       "vinf_gain": spread("vinf_gain"),
       "vbli_gain": spread("vbli_gain"),
       "vbli_minus_vinf": spread("vbli_minus_vinf")}
print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
print("DONE", flush=True)
