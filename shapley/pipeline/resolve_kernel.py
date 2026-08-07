# H24 — "SUA LOI" CUA VERIFIER CHI LA GIAI LAI? Xem docs/PREREGISTRATION.md #23 (commit TRUOC khi chay).
# 4 nhanh, CUNG bo loi giai, moi nhanh DUNG 1 lan sinh them (chi phi bang nhau):
#   V_inf: khung KIEM + toan bo loi giai | V_bli: khung KIEM + chi dap an
#   S_anc: khung GIAI + mo neo dap an     | S_pln: khung GIAI, khong neo (temp .7)
#
# Sinh MỘT bộ lời giải duy nhất, rồi cho Verifier xem 4 KIỂU KHÁC NHAU của CÙNG lời giải đó
# -> mọi khác biệt CHỈ do "verifier được nhìn thấy cái gì":
#   I (informed): thấy TOÀN BỘ lời giải + đáp án      <- baseline "truyền cả trace" như framework thường làm
#   B (blind)   : CHỈ thấy đáp án                      <- giả thuyết: bắt lỗi tốt hơn nhiều
#   P (partial) : thấy phần suy luận, XOÁ đáp án cuối  <- tách: thủ phạm là ĐÁP ÁN hay là SUY LUẬN?
#   X (cross)   : thấy lời giải của BÀI KHÁC + đáp án  <- giả dược: có phải chỉ vì context dài hơn?
import os, re, csv, json, glob, statistics, torch

TASK  = "__TASK__"
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

def gen(sysm, usrs, mx=768, temp=0.0):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i+BS]
        ps = [tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=(temp>0), temperature=max(temp,1e-5),
                               top_p=0.95, pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    print(f"   ...{len(usrs)} xong", flush=True)
    return outs

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
    q_of = lambda r: r["question"]; TAIL = "End with 'The answer is <number>'."
    fmt_ans = lambda a: f"The answer is {a}."
else:
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I); return m[-1].strip() if m else None
    q_of = lambda r: r["Question"]; TAIL = "Put the final answer in \\boxed{}."
    fmt_ans = lambda a: f"The answer is \\boxed{{{a}}}."

qs = [q_of(r) for r in rows]; gs = [gold_of(r) for r in rows]
SOLVE  = f"Solve step by step. {TAIL}"
VERIFY = f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"

# ---------- MỘT bộ lời giải duy nhất, dùng chung cho cả 4 nhánh ----------
print("== Solver (1 lần, dùng chung) ==", flush=True)
sols = gen(SOLVE, qs, 768)
sa   = [pred(s) for s in sols]
s_ok = [eq(a,g) for a,g in zip(sa,gs)]
n_cor = sum(s_ok)
print(f"solver acc = {n_cor/len(gs):.4f}", flush=True)

def strip_answer(s, a):
    """Xoá câu chốt đáp án ở cuối, giữ phần suy luận."""
    if not s: return ""
    t = re.split(r"(?i)the answer is", s)[0]
    t = re.sub(r"\\boxed\s*\{[^}]*\}", "(redacted)", t)
    return t.strip() or "(no reasoning)"

ARMS = {
  # (system_prompt, user_builder, temperature)
  "V_inf": (VERIFY, [f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)], 0.0),
  "V_bli": (VERIFY, [f"{q}\n\nProposed solution:\n{fmt_ans(a)}" for q,a in zip(qs,sa)], 0.0),
  "S_anc": (SOLVE,  [f"{q}\n\nA previous attempt answered: {a}" for q,a in zip(qs,sa)], 0.0),
  "S_pln": (SOLVE,  list(qs), 0.7),
}

out = {"task": TASK, "n": len(gs), "quant": QUANT,
       "solver_acc": round(n_cor/len(gs),4), "solver_correct": n_cor,
       "median_sol_len": int(statistics.median(len(s or "") for s in sols)), "arms": {}}
traces = []

for tag, (sysm, usrs, temp) in ARMS.items():
    print(f"== {tag} ==", flush=True)
    vers = gen(sysm, usrs, 768, temp)
    va   = [pred(v) for v in vers]
    v_ok = [eq(a,g) for a,g in zip(va,gs)]
    brk  = sum(1 for i in range(len(gs)) if s_ok[i] and not v_ok[i])
    fix  = sum(1 for i in range(len(gs)) if not s_ok[i] and v_ok[i])
    changed = sum(1 for i in range(len(gs)) if norm(va[i]) != norm(sa[i]))
    # HIEU LUC MO NEO: nhanh co nhac lai con so cua Solver khong?
    def _nums(t): return set(x.replace(",","") for x in re.findall(r"-?\d[\d,]*(?:\.\d+)?", t or ""))
    echo = [len(_nums(vers[i]) & (_nums(sols[i]) - _nums(qs[i]))) /
            max(len(_nums(sols[i]) - _nums(qs[i])), 1) for i in range(len(gs))]
    r = {"acc": round(sum(v_ok)/len(gs),4),
         "value_added": round(sum(v_ok)/len(gs) - n_cor/len(gs), 4),
         "fixes": fix, "breaks": brk,
         "fix_rate_on_wrong": round(fix/max(len(gs)-n_cor,1), 4),
         "break_rate_on_right": round(brk/max(n_cor,1), 4),
         "changed_answer": changed,
         "reuse_solver_nums": round(statistics.median(echo), 4),
         "median_out_chars": int(statistics.median(len(v or "") for v in vers))}
    out["arms"][tag] = r
    print(f"[{tag}] {json.dumps(r)}", flush=True)
    for i in range(min(60, len(gs))):
        traces.append({"arm":tag,"i":i,"q":qs[i][:400],"gold":gs[i],
                       "solver_ans":sa[i],"solver_ok":bool(s_ok[i]),
                       "arm_ans":va[i],"arm_ok":bool(v_ok[i]),"arm_out":(vers[i] or "")[:1200]})

print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json","w"), indent=2)
json.dump(traces, open("/kaggle/working/traces.json","w"), indent=1)   # BAT BUOC: >=50 trace/nhanh
print("traces saved:", len(traces), flush=True)
