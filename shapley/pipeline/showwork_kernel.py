# THÍ NGHIỆM CAN THIỆP: "Verifier phá đáp án đúng" có phải VÌ Solver không trình bày lời giải?
# Quan sát trước: 11/103 phá khi Solver chỉ ghi "The answer is X"; 0/28 khi có trình bày.
# Nhưng đó là QUAN SÁT -> phải CAN THIỆP mới kết luận nhân quả được.
#
# 3 nhánh; nhánh B và C dùng CHUNG một bộ lời giải -> đối chứng cặp hoàn hảo:
#   A: Solver trả lời trống (prompt gốc)      -> Verifier thấy đáp án trơ
#   B: Solver BỊ ÉP trình bày                 -> Verifier thấy TOÀN BỘ lời giải
#   C: Solver BỊ ÉP trình bày (CÙNG lời giải B) -> nhưng Verifier chỉ được thấy ĐÁP ÁN (đã xoá work)
#
# B vs C: lời giải Y HỆT NHAU, chỉ khác Verifier CÓ ĐƯỢC NHÌN phần trình bày hay không.
#   -> tách bạch "Solver suy luận tốt hơn" khỏi "Verifier có cái để kiểm".
#   Nếu C phá nhiều mà B phá ít => nguyên nhân là TÍNH NHÌN THẤY ĐƯỢC của lời giải. Nhân quả.
import os, re, csv, json, glob, statistics, torch

TASK  = "__TASK__"        # gsm8k | math
N     = __N__
BS    = __BS__
QUANT = __QUANT__

if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])
from transformers import AutoModelForCausalLM, AutoTokenizer

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True) or \
     glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "main_test.csv" if TASK == "gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} MODEL={MODEL} n={len(rows)}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
if QUANT:
    from transformers import BitsAndBytesConfig
    _b = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=_b, device_map="auto").eval()
else:
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="cuda").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx=768):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i+BS]
        ps = [tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False, pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        print(f"    {i+len(ch)}/{len(usrs)}", flush=True)
    return outs

# ---- chấm điểm theo task ----
def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0: return None
    i = s.find("{", i); d = 0; st = i
    for j in range(i, len(s)):
        if s[j] == "{": d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0: return s[st+1:j]
    return None
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def norm(a):
    if a is None: return None
    a = str(a).strip()
    for x in ["\\left","\\right","\\!","\\,","\\;","$"," ",","]: a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a); a = a.replace("\\dfrac","\\frac").replace("\\tfrac","\\frac")
    return a.rstrip(".").strip("{}").lower()
def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g: return False
    if p == g: return True
    try: return abs(float(p)-float(g)) < 1e-6
    except: return False
if TASK == "gsm8k":
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"]); return m.group(1).replace(",","").strip() if m else None
    def pred(t):
        m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I) or NUM.findall(t or "")
        return m[-1].replace(",","") if m else None
    q_of = lambda r: r["question"]
    TAIL = "End with 'The answer is <number>'."
else:
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I); return m[-1].strip() if m else None
    q_of = lambda r: r["Question"]
    TAIL = "Put the final answer in \\boxed{}."

qs = [q_of(r) for r in rows]; gs = [gold_of(r) for r in rows]

PLAN   = "Give a concise numbered plan. Do NOT compute the final answer."
SOLVE_BARE = f"Solve step by step. {TAIL}"
SOLVE_WORK = ("Show your complete derivation. Write EVERY intermediate calculation on its own line "
              "as 'Step k: <expression> = <result>'. Never state the answer without showing the work "
              f"that produced it. {TAIL}")
VERIFY = f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"

plans = gen(PLAN, qs, 320)

print("== Solver A (trống) ==", flush=True)
solA = gen(SOLVE_BARE, [f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,plans)], 768)
print("== Solver B (ép trình bày) ==", flush=True)
solB = gen(SOLVE_WORK, [f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,plans)], 768)

# C: CÙNG lời giải B nhưng XOÁ phần trình bày, chỉ chừa đáp án
solC = [f"The answer is {pred(s)}." if TASK=="gsm8k" else f"The answer is \\boxed{{{pred(s)}}}."
        for s in solB]

def verify_arm(sols, tag):
    vers = gen(VERIFY, [f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)], 768)
    sa = [pred(s) for s in sols]; va = [pred(v) for v in vers]
    s_ok = [eq(a,g) for a,g in zip(sa,gs)]; v_ok = [eq(a,g) for a,g in zip(va,gs)]
    brk = sum(1 for i in range(len(gs)) if s_ok[i] and not v_ok[i])
    fix = sum(1 for i in range(len(gs)) if not s_ok[i] and v_ok[i])
    ncor = sum(s_ok)
    r = {"solver_acc": round(ncor/len(gs),4), "verifier_acc": round(sum(v_ok)/len(gs),4),
         "solver_correct": ncor, "breaks": brk, "fixes": fix,
         "break_rate": round(brk/max(ncor,1),4),          # <-- CHỈ SỐ CHÍNH
         "median_sol_len": int(statistics.median(len(s or "") for s in sols)),
         "pct_under_200_chars": round(sum(1 for s in sols if len(s or "")<200)/len(sols),3)}
    print(f"[{tag}] {json.dumps(r)}", flush=True)
    return r

print("== Verify A ==", flush=True); rA = verify_arm(solA, "A bare-solver")
print("== Verify B ==", flush=True); rB = verify_arm(solB, "B work-shown")
print("== Verify C ==", flush=True); rC = verify_arm(solC, "C work-hidden (same solutions as B)")

out = {"task": TASK, "n": len(gs), "quant": QUANT,
       "A_bare": rA, "B_work_shown": rB, "C_work_hidden": rC,
       "note": "B vs C dùng CÙNG lời giải; chỉ khác Verifier có thấy phần trình bày hay không"}
print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json","w"), indent=2)
