# ITERATIVE giữa các agent trên MATH-500: lặp Solver<->Verifier tối đa ROUNDS vòng,
# dừng sớm khi đồng thuận. Log accuracy SAU MỖI vòng + đếm fix(sai->đúng)/break(đúng->sai)
# mỗi vòng để thấy động lực (kiểm định giả thuyết Verifier yếu phá đáp án đúng).
import os, re, csv, json, glob, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROUNDS = __ROUNDS__
N = __N__
QUANT = __QUANT__
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
        print("LOADED 4bit", flush=True)
    except Exception as e:
        print("4bit FAILED -> fp16 offload:", repr(e)[:200], flush=True); model = None
if model is None:
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto").eval()
    print("LOADED fp16", flush=True)

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

PLAN="Give a concise numbered plan. Do NOT compute the final answer."
SOLVE="Solve the problem step by step. Put the final answer in \\boxed{}."
REDO="Solve again carefully, using the reviewer feedback to fix mistakes. Put the final answer in \\boxed{}."
VERIFY="Check the proposed solution step by step; if wrong, correct it. Put the final answer in \\boxed{}."

# acc_at[k] = đúng sau khi kết thúc vòng k (k=0 là solve lần đầu, chưa verify)
acc_at=[0]*(ROUNDS+1); fix=[0]*(ROUNDS+1); brk=[0]*(ROUNDS+1); conv=[0]*(ROUNDS+1)
for r in rows:
    q=r["Question"]; g=boxed(r["Answer"])
    plan=gen(PLAN,q,384)
    sol=gen(SOLVE,q+"\n\nPlan:\n"+plan)
    cur=pred(sol); prev_ok=eq(cur,g); acc_at[0]+=prev_ok
    for k in range(1,ROUNDS+1):
        ver=gen(VERIFY,q+"\n\nProposed solution:\n"+sol)
        if pred(ver)==pred(sol):                 # đồng thuận -> dừng sớm, giữ nguyên cho các vòng sau
            conv[k]+=1
            for kk in range(k,ROUNDS+1): acc_at[kk]+=eq(pred(sol),g)
            break
        sol=gen(REDO,q+"\n\nReviewer feedback:\n"+ver+"\n\nOriginal attempt:\n"+sol)
        cur=pred(sol); now_ok=eq(cur,g)
        if now_ok and not prev_ok: fix[k]+=1
        if prev_ok and not now_ok: brk[k]+=1
        prev_ok=now_ok; acc_at[k]+=now_ok
    else:
        pass
    print(f"gold={g} final={pred(sol)} ok={eq(pred(sol),g)}", flush=True)

n=len(rows)
res={"rounds":ROUNDS,"n":n,
     "acc_by_round":[round(a/n,4) for a in acc_at],   # [sau solve, sau vòng1, sau vòng2, ...]
     "fix_by_round":fix,"break_by_round":brk,"converged_by_round":conv,
     "acc":round(acc_at[ROUNDS]/n,4)}
print("SUMMARY",json.dumps(res),flush=True)
json.dump(res,open("/kaggle/working/summary.json","w"))
