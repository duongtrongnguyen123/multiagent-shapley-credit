# 5 hướng cải tiến trên MATH-500 (chấm \boxed{}). MODE bake sẵn. Model dir + device + N + dataset
# đặt lúc deploy (1.5B vs 7B). Đo accuracy để so cải tiến vs base trên bài KHÓ (chưa bão hoà).
import os, re, csv, json, glob, io, contextlib, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODE = "__MODE__"
N = __N__
QUANT = __QUANT__   # True -> load 4-bit nf4 (7B vừa 1xT4, hết offload)
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True) or glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = None
if QUANT:
    try:
        import subprocess, sys
        subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"], check=True)
        from transformers import BitsAndBytesConfig
        _bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                  bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
        model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=_bnb, device_map="auto").eval()
        print("LOADED 4bit (fast)", flush=True)
    except Exception as e:
        print("4bit FAILED -> fallback fp16 offload:", repr(e)[:200], flush=True); model = None
if model is None:
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto").eval()
    print("LOADED fp16 (auto/offload, slow but works)", flush=True)

def gen(sys, usr, mx=1024):
    p = tok.apply_chat_template([{"role":"system","content":sys},{"role":"user","content":usr}],
                                tokenize=False, add_generation_prompt=True)
    e = tok(p, return_tensors="pt").to(model.device)
    o = model.generate(**e, max_new_tokens=mx, do_sample=False, pad_token_id=tok.pad_token_id)
    return tok.decode(o[0, e["input_ids"].shape[1]:], skip_special_tokens=True).strip()

def boxed(s):
    i=s.rfind("\\boxed") if s else -1
    if i<0: return None
    i=s.find("{",i); d=0; st=i
    for j in range(i,len(s)):
        if s[j]=="{": d+=1
        elif s[j]=="}":
            d-=1
            if d==0: return s[st+1:j]
    return None
def norm(a):
    if a is None: return None
    a=a.strip()
    for x in ["\\left","\\right","\\!","\\,","\\;","$"," "]: a=a.replace(x,"")
    a=re.sub(r"\\text\s*\{([^}]*)\}",r"\1",a); a=a.replace("\\dfrac","\\frac").replace("\\tfrac","\\frac")
    return a.rstrip(".").strip("{}").lower()
def eq(p,g):
    p,g=norm(p),norm(g)
    if not p or not g: return False
    if p==g: return True
    try: return abs(float(p)-float(g))<1e-6
    except: return False
def pred(t):
    b=boxed(t)
    if b is not None: return b
    m=re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)",t or "",re.I); return m[-1].strip() if m else None

SOLVE="Solve the problem step by step. Put the final answer in \\boxed{}."
SOLVE_FULL="Solve step by step, showing EVERY operation explicitly (do not skip work). Put the final answer in \\boxed{}."
PLAN="Give a concise numbered plan. Do NOT compute the final answer."
VERIFY="Check the proposed solution step by step; if wrong, correct it. Put the final answer in \\boxed{}."
AGG="Given candidate solutions, decide the correct final answer. Put it in \\boxed{}."
S_ST="Solve by numbering each step 'Step k: <calc>'. Put final answer in \\boxed{}."
V_ST="For EACH numbered step, output 'Step k: OK' or 'Step k: WRONG, correct is <v>'. Do NOT resolve from scratch. Put final answer in \\boxed{}."
POT="Write ONLY a short Python program (use sympy if needed) that computes the answer and prints it. No explanation."

def run_pot(code):
    code=re.sub(r"^```(python)?|```$","",code.strip(),flags=re.M)
    buf=io.StringIO()
    try:
        with contextlib.redirect_stdout(buf): exec(code,{})
        o=buf.getvalue().strip().splitlines(); return o[-1].strip() if o else None
    except Exception: return None

cor=0
for r in rows:
    q=r["Question"]; g=boxed(r["Answer"])
    if MODE=="tool":
        a=run_pot(gen(POT,q,500)) or pred(gen(SOLVE,q))
    elif MODE=="loop":
        plan=gen(PLAN,q,384); sol=gen(SOLVE,q+"\n\nPlan:\n"+plan); ver=gen(VERIFY,q+"\n\nProposed solution:\n"+sol)
        a=pred(gen(SOLVE,q+"\n\nA reviewer flagged an error:\n"+ver+"\n\nRedo carefully.")) if pred(ver)!=pred(sol) else pred(sol)
    elif MODE=="struct":
        sol=gen(S_ST,q); ver=gen(V_ST,q+"\n\nProposed solution:\n"+sol); a=pred(ver)
    else:
        plan=gen(PLAN,q,384); sol=gen(SOLVE_FULL if MODE=="showwork" else SOLVE, q+"\n\nPlan:\n"+plan)
        ver=gen(VERIFY,q+"\n\nProposed solution:\n"+sol)
        a=pred(gen(AGG,q+f"\n\nCandidate 1:\n{sol}\n\nCandidate 2:\n{ver}",512))
    cor+=eq(a,g)
acc=cor/len(rows)
print("SUMMARY",json.dumps({"mode":MODE,"n":len(rows),"acc":acc}),flush=True)
json.dump({"mode":MODE,"n":len(rows),"acc":acc},open("/kaggle/working/summary.json","w"))
