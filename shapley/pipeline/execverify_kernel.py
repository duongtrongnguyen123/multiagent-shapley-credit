# H8 — VERIFY BẰNG THỰC THI CÓ TỔNG QUÁT TỪ CODE SANG MATH KHÔNG?
# Xem docs/PREREGISTRATION.md #7 (commit TRƯỚC khi chạy).
# 7 giả thuyết dựa trên PHÁN ĐOÁN LLM đã chết. Verify bằng THỰC THI (trên code) chưa từng hỏng:
#   0 phá qua 3 vòng, cả 2 cỡ model. Ở đây thử đúng cơ chế đó trên MATH/GSM8K.
# Verifier CƠ HỌC: model VIẾT PYTHON tính lại, ta CHẠY THẬT, so với đáp án Solver.
#   N = không verify | L = verify bằng LLM | E_take = lấy đáp án Python | E_flag = Python làm CỔNG
import os, re, csv, json, glob, io, contextlib, signal, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK="__TASK__"; N=__N__; BS=__BS__

_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
FNAME="main_test.csv" if TASK=="gsm8k" else "math_500_test.csv"
CSV=sorted(glob.glob(f"/kaggle/input/**/{FNAME}",recursive=True),key=len)[0]
rows=list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} n={len(rows)}",flush=True)

tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="cuda").eval()
print("model loaded",flush=True)

def gen(sysm,usrs,mx=768):
    outs=[]
    for i in range(0,len(usrs),BS):
        ch=usrs[i:i+BS]
        ps=[tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                                    tokenize=False,add_generation_prompt=True) for u in ch]
        e=tok(ps,return_tensors="pt",padding=True).to(model.device)
        with torch.no_grad():
            o=model.generate(**e,max_new_tokens=mx,do_sample=False,pad_token_id=tok.pad_token_id)
        L=e["input_ids"].shape[1]
        outs+=[tok.decode(o[j,L:],skip_special_tokens=True).strip() for j in range(len(ch))]
    print(f"   ...{len(usrs)}",flush=True)
    return outs

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
NUM=re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def norm(a):
    if a is None: return None
    a=str(a).strip()
    for x in ["\\left","\\right","\\!","\\,","\\;","$"," ",","]: a=a.replace(x,"")
    a=re.sub(r"\\text\s*\{([^}]*)\}",r"\1",a); a=a.replace("\\dfrac","\\frac").replace("\\tfrac","\\frac")
    return a.rstrip(".").strip("{}").lower()
def eq(p,g):
    p,g=norm(p),norm(g)
    if not p or not g: return False
    if p==g: return True
    try: return abs(float(p)-float(g))<1e-6
    except: return False
if TASK=="gsm8k":
    def gold_of(r):
        m=re.search(r"####\s*([-\d,\.]+)",r["answer"]); return m.group(1).replace(",","").strip() if m else None
    def pred(t):
        m=re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)",t or "",re.I) or NUM.findall(t or "")
        return m[-1].replace(",","") if m else None
    q_of=lambda r:r["question"]; TAIL="End with 'The answer is <number>'."
else:
    gold_of=lambda r:boxed(r["Answer"])
    def pred(t):
        b=boxed(t)
        if b is not None: return b
        m=re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)",t or "",re.I); return m[-1].strip() if m else None
    q_of=lambda r:r["Question"]; TAIL="Put the final answer in \\boxed{}."

qs=[q_of(r) for r in rows]; gs=[gold_of(r) for r in rows]
SOLVE=f"Solve step by step. {TAIL}"
VERIFY=f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
PYV=("Write ONLY a short Python program that recomputes the answer to this problem from scratch "
     "and prints it as the last line. Use sympy if algebra is needed. No explanation, no comments.")
REDO=f"A recomputation disagreed with this solution. Solve again very carefully. {TAIL}"

class TO(Exception): pass
def _h(s,f): raise TO()
def run_py(code):
    """CHẠY THẬT. Trả (ok, giá trị in ra cuối)."""
    code=re.sub(r"^```(python)?|```$","",(code or "").strip(),flags=re.M)
    buf=io.StringIO()
    signal.signal(signal.SIGALRM,_h); signal.alarm(6)
    try:
        with contextlib.redirect_stdout(buf): exec(code,{"__name__":"__main__"})
        signal.alarm(0)
        o=buf.getvalue().strip().splitlines()
        return (True,o[-1].strip()) if o else (False,None)
    except Exception:
        signal.alarm(0); return (False,None)

sols=gen(SOLVE,qs,768)
sa=[pred(s) for s in sols]; s_ok=[eq(a,g) for a,g in zip(sa,gs)]
n_cor=sum(s_ok); base=n_cor/len(gs)
print(f"[N no-verify] acc={base:.4f}",flush=True)
out={"task":TASK,"n":len(gs),"solver_acc":round(base,4),"solver_correct":n_cor,"arms":{}}

def score(va,tag,extra=None):
    v_ok=[eq(a,g) for a,g in zip(va,gs)]
    r={"verifier_acc":round(sum(v_ok)/len(gs),4),
       "value_added":round(sum(v_ok)/len(gs)-base,4),
       "fixes":sum(1 for i in range(len(gs)) if not s_ok[i] and v_ok[i]),
       "breaks":sum(1 for i in range(len(gs)) if s_ok[i] and not v_ok[i])}
    if extra: r.update(extra)
    out["arms"][tag]=r; print(f"[{tag}] {json.dumps(r)}",flush=True)

# L: verify bằng LLM
score([pred(v) for v in gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)],768)],"L_llm")

# E: model viết Python -> CHẠY THẬT
codes=gen(PYV,qs,420)
ok_run=[]; pyans=[]
for c in codes:
    ok,v=run_py(c); ok_run.append(ok); pyans.append(v)
n_ok=sum(ok_run)
exec_acc=sum(1 for i in range(len(gs)) if ok_run[i] and eq(pyans[i],gs[i]))/max(n_ok,1)
disagree=[i for i in range(len(gs)) if ok_run[i] and not eq(pyans[i],sa[i])]
diag={"exec_success_rate":round(n_ok/len(gs),4),      # KIỂM TRA HIỆU LỰC
      "exec_acc":round(exec_acc,4),
      "disagree_rate":round(len(disagree)/len(gs),4)}
print(f"[exec diagnostics] {json.dumps(diag)}",flush=True)

# E_take: bất đồng -> lấy luôn đáp án Python
score([pyans[i] if i in set(disagree) else sa[i] for i in range(len(gs))],"E_take",diag)

# E_flag: bất đồng -> cho LLM giải lại (Python chỉ làm CỔNG)
va=list(sa)
if disagree:
    redo=gen(REDO,[f"{qs[i]}\n\nYour previous solution:\n{sols[i]}\n\n"
                   f"An independent recomputation gave: {pyans[i]}" for i in disagree],768)
    for k,i in enumerate(disagree): va[i]=pred(redo[k])
score(va,"E_flag",diag)

print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
