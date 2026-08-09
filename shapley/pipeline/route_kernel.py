# H38 (pre-reg #44) — DINH TUYEN THEO DONG THUAN vs TIEU DEU. Bao chi phi THUC TE.
import os, re, csv, json, glob, statistics as st, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
TASK="__TASK__"; N=__N__; BS=__BS__; QUANT=__QUANT__; NF=5; KMAX=8
if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"],check=False)
_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True) or \
   glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
FN="main_test.csv" if TASK=="gsm8k" else "math_500_test.csv"
CSV=sorted(glob.glob(f"/kaggle/input/**/{FN}",recursive=True),key=len)[0]
rows=list(csv.DictReader(open(CSV)))[:N]
tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
if QUANT:
    from transformers import BitsAndBytesConfig
    _b=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    model=AutoModelForCausalLM.from_pretrained(MODEL,quantization_config=_b,device_map="auto").eval()
else:
    model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="auto").eval()
NUM=re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def _bx(t):
    i=(t or "").rfind("\\boxed")
    if i<0: return None
    i=t.find("{",i); d=0; s0=i
    for j in range(i,len(t)):
        if t[j]=="{": d+=1
        elif t[j]=="}":
            d-=1
            if d==0: return t[s0+1:j]
    return None
if TASK=="gsm8k":
    qs=[r["question"] for r in rows]
    gs=[NUM.findall(r["answer"].split("####")[-1])[0].replace(",","") for r in rows]
    TAIL="End with 'The answer is <number>'."
    def pred(t):
        m=re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)",t or "",re.I) or NUM.findall(t or "")
        return m[-1].replace(",","") if m else None
    def ok(x,g):
        try: return x is not None and abs(float(x)-float(g))<1e-4
        except: return x==g
else:
    qs=[r["Question"] for r in rows]
    gs=[_bx(r["Answer"]) or (NUM.findall(r["Answer"]) or [""])[-1] for r in rows]
    TAIL="Put the final answer in \\boxed{}."
    def pred(t):
        b=_bx(t)
        if b is not None: return b.strip()
        m=re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)",t or "",re.I); return m[-1].strip() if m else None
    def _nm(a):
        if a is None: return None
        a=str(a).strip()
        for z in ["\\left","\\right","\\!","\\,","$"," ",","]: a=a.replace(z,"")
        a=re.sub(r"\\text\s*\{([^}]*)\}",r"\1",a).replace("\\dfrac","\\frac").replace("\\tfrac","\\frac")
        return a.rstrip(".").strip("{}").lower()
    def ok(x,g):
        x,g=_nm(x),_nm(g)
        if not x or not g: return False
        if x==g: return True
        try: return abs(float(x)-float(g))<1e-6
        except: return False
TOK={}
def gen(sysm,us,mx,temp,who):
    outs=[];nt=0
    for i in range(0,len(us),BS):
        ch=us[i:i+BS]
        ps=[tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
            tokenize=False,add_generation_prompt=True) for u in ch]
        e=tok(ps,return_tensors="pt",padding=True).to(model.device)
        with torch.no_grad():
            o=model.generate(**e,max_new_tokens=mx,do_sample=(temp>0),temperature=max(temp,1e-5),
                             top_p=0.95,pad_token_id=tok.pad_token_id)
        L=e["input_ids"].shape[1]
        for j in range(len(ch)):
            g=o[j,L:]; nt+=int((g!=tok.pad_token_id).sum())
            outs.append(tok.decode(g,skip_special_tokens=True).strip())
        del e,o; torch.cuda.empty_cache()
    TOK[who]=TOK.get(who,0)+nt
    return outs
SOLVE=f"Solve step by step. {TAIL}"
VERIFY=f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
ANCH=f"Solve step by step. A previous attempt answered: @@A@@. {TAIL}"
def vote(cols,i,k):
    c={}
    for r in range(k):
        p=pred(cols[r][i])
        if p is not None: c[p]=c.get(p,0)+1
    if not c: return None,0
    best=max(c,key=c.get); return best,c[best]

folds=[]; FOLD=len(qs)//NF
for fi in range(NF):
    lo,hi=fi*FOLD,(fi+1)*FOLD
    Q=qs[lo:hi]; G=gs[lo:hi]; n=len(Q)
    acc=lambda a: round(sum(ok(x,g) for x,g in zip(a,G))/n,4)
    print(f"== fold {fi} ==",flush=True)
    S=[gen(SOLVE,Q,512,0.8,f"pool{r}") for r in range(KMAX)]     # 8 mau dung chung moi nhanh
    r={"fold":fi,"n":n}
    for k in [3,4,6,8]:
        a=[vote(S,i,k)[0] for i in range(n)]
        r[f"maj{k}"]=acc(a); r[f"gens_maj{k}"]=float(k)
    # --- DINH TUYEN: 3 mau; dong thuan (>=2) -> nhan; khong -> them ---
    first=[vote(S,i,3) for i in range(n)]
    noconsensus=[i for i in range(n) if first[i][1] < 2]
    r["pct_no_consensus"]=round(len(noconsensus)/n,4)
    # route_3_6: them 3 mau nua (dung mau 3,4,5 co san)
    a_r36=[]
    for i in range(n):
        a_r36.append(first[i][0] if first[i][1]>=2 else vote(S,i,6)[0])
    r["route_3_6"]=acc(a_r36); r["gens_route_3_6"]=round(3+3*len(noconsensus)/n,3)
    # route_3_seq: bai phan tan -> tuan tu co mo neo (2 luot) + 1 verify
    if noconsensus:
        Qn=[Q[i] for i in noconsensus]; An=[first[i][0] for i in noconsensus]
        r1=gen(SOLVE,[ANCH.replace("@@A@@",str(a))+f"\n\n{q}" for q,a in zip(Qn,An)],512,0.0,"route_seq")
        b1=[pred(x) for x in r1]
        r2=gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(Qn,r1)],512,0.0,"route_seq")
        b2=[pred(x) if pred(x) is not None else b1[k] for k,x in enumerate(r2)]
        fix={noconsensus[k]:b2[k] for k in range(len(noconsensus))}
    else: fix={}
    a_rseq=[fix.get(i, first[i][0]) for i in range(n)]
    r["route_3_seq"]=acc(a_rseq); r["gens_route_3_seq"]=round(3+2*len(noconsensus)/n,3)
    folds.append(r); print(f"[fold {fi}] {json.dumps(r)}",flush=True)
def sp(k):
    v=[f[k] for f in folds]
    return {"mean":round(st.mean(v),4),"min":round(min(v),4),"max":round(max(v),4)}
out={"task":TASK,"n":len(qs),"quant":QUANT,"folds":folds,"tokens":TOK}
for k in folds[0]:
    if k not in ("fold","n"): out[k]=sp(k)
# noi suy duong cong tieu deu tai chi phi thuc te cua tung nhanh dinh tuyen
import bisect
ks=[3,4,6,8]; ys=[out[f"maj{k}"]["mean"] for k in ks]
def interp(x):
    if x<=ks[0]: return ys[0]
    if x>=ks[-1]: return ys[-1]
    j=bisect.bisect_left(ks,x)
    x0,x1,y0,y1=ks[j-1],ks[j],ys[j-1],ys[j]
    return y0+(y1-y0)*(x-x0)/(x1-x0)
for nm in ["route_3_6","route_3_seq"]:
    c=out[f"gens_{nm}"]["mean"]; base=interp(c)
    out[f"{nm}_vs_uniform"]={"cost_gens":round(c,3),"uniform_at_cost":round(base,4),
                             "route":out[nm]["mean"],"delta":round(out[nm]["mean"]-base,4)}
    print(nm,json.dumps(out[f"{nm}_vs_uniform"]),flush=True)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
