# H17 — MATH 7B: FULL vs TRIM, 5 fold. Xem docs/PREREGISTRATION.md #17.
# Mắt xích cuối của phát biểu hợp nhất: ở MATH, truyền trace có hại không khi model LỚN?
# Đã đo 1 lần (trim_minus_full = -17.5). Nay chạy 5 fold để có thanh sai số.
#
#   FULL : P->S->V->A, mỗi agent nhận TOÀN VĂN output trước đó (chuẩn hiện hành)
#   TRIM : P->S (giữ trace), V và A chỉ nhận ĐÁP ÁN (cat trace ở V và A)
#   S    : chỉ Solver (mốc)
#
# 7B fp16 on T4 16GB (no quantization, same as template_role7b).
# No bitsandbytes needed — internet is off on Kaggle.
import os, re, csv, json, glob, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "math"
N = __N__
BS = __BS__

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

model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                              device_map="auto").eval()
print("model loaded", flush=True)

CHARS = {"FULL": 0, "TRIM": 0}

def gen(sysm, usrs, mx=768, bucket=None):
    if bucket:
        CHARS[bucket] += sum(len(u) for u in usrs)
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
AGG = f"Given candidate answers, decide the correct final answer. {TAIL}"

folds = []
for fi in range(NF):
    rows = ALL[fi * FOLD:(fi + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"== FOLD {fi} (n={n}) ==", flush=True)

    def acc(a):
        return round(sum(eq(x, g) for x, g in zip(a, gs)) / len(gs), 4)

    # --- MỐC: chỉ Solver ---
    solo = [pred(s) for s in gen(SOLVE, qs, 768)]
    print(f"  [S_only] acc={acc(solo)}", flush=True)

    # --- FULL: truyền TOÀN VĂN ---
    plans = gen(PLAN, qs, 320, "FULL")
    sF = gen(SOLVE, [f"{q}\n\nPlan:\n{p}" for q, p in zip(qs, plans)], 768, "FULL")
    saF = [pred(x) for x in sF]
    vF = gen(VERIFY, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, sF)], 768, "FULL")
    vaF = [pred(x) for x in vF]
    aF = gen(AGG, [f"{q}\n\nCandidate 1:\n{s}\n\nCandidate 2:\n{v}" for q, s, v in zip(qs, sF, vF)], 512, "FULL")
    accF = acc([pred(x) for x in aF])
    print(f"  [FULL] acc={accF} chars={CHARS['FULL']}", flush=True)

    # --- TRIM: giữ P->S, cắt trace ở V và A (chỉ truyền đáp án) ---
    sT = sF  # dùng lại cùng lời giải
    saT = [pred(x) for x in sT]
    vT = gen(VERIFY, [f"{q}\n\nProposed solution:\n{fmt(a)}" for q, a in zip(qs, saT)], 768, "TRIM")
    vaT = [pred(x) for x in vT]
    aT = gen(AGG, [f"{q}\n\nCandidate 1: {a1}\nCandidate 2: {a2}" for q, a1, a2 in zip(qs, saT, vaT)], 512, "TRIM")
    accT = acc([pred(x) for x in aT])
    print(f"  [TRIM] acc={accT} chars={CHARS['TRIM']}", flush=True)

    r = {"fold": fi, "n": n,
         "acc_solver": acc(solo),
         "acc_full": accF,
         "acc_trim": accT,
         "trim_minus_full": round(accT - accF, 4),
         "full_minus_solo": round(accF - acc(solo), 4),
         "trim_minus_solo": round(accT - acc(solo), 4),
         "chars_full": CHARS["FULL"],
         "chars_trim": CHARS["TRIM"]}
    folds.append(r)
    print(f"  [fold {fi}] {json.dumps(r)}", flush=True)

    # checkpoint
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
       "acc_solver": spread("acc_solver"),
       "acc_full": spread("acc_full"),
       "acc_trim": spread("acc_trim"),
       "trim_minus_full": spread("trim_minus_full"),
       "full_minus_solo": spread("full_minus_solo"),
       "trim_minus_solo": spread("trim_minus_solo")}
print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
print("DONE", flush=True)
