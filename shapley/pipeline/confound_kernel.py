# H32 (pre-reg #38) — PIPELINE VAI TRO vs BO PHIEU o CUNG NGAN SACH (3 luot sinh moi nhanh).
# Dem ca SO TOKEN sinh ra -> ngan sach cong bang tinh theo TOKEN, khong chi theo so luot.
import os, re, csv, json, glob, statistics as st, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK="__TASK__"; N=__N__; BS=__BS__; QUANT=__QUANT__; NF=5
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
print(f"TASK={TASK} n={len(rows)}",flush=True)

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

TOKENS={}   # dem token SINH RA moi nhanh
def gen(sysm,us,mx,temp,arm):
    outs=[]; ntok=0
    for i in range(0,len(us),BS):
        ch=us[i:i+BS]
        ps=[tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
            tokenize=False,add_generation_prompt=True) for u in ch]
        e=tok(ps,return_tensors="pt",padding=True).to("cuda")
        with torch.no_grad():
            o=model.generate(**e,max_new_tokens=mx,do_sample=(temp>0),temperature=max(temp,1e-5),
                             top_p=0.95,pad_token_id=tok.pad_token_id)
        L=e["input_ids"].shape[1]
        for j in range(len(ch)):
            g=o[j,L:]
            ntok+=int((g!=tok.pad_token_id).sum())
            outs.append(tok.decode(g,skip_special_tokens=True).strip())
        del e,o; torch.cuda.empty_cache()
    TOKENS[arm]=TOKENS.get(arm,0)+ntok
    return outs

SOLVE=f"Solve step by step. {TAIL}"
PLAN ="Give a concise numbered plan for solving this problem."
VERIFY=f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
ANCH =f"Solve step by step. A previous attempt answered: @@A@@. {TAIL}"

folds=[]
FOLD=len(qs)//NF
for fi in range(NF):
    lo,hi=fi*FOLD,(fi+1)*FOLD
    Q,G=qs[lo:hi],gs[lo:hi]
    acc=lambda a: round(sum(ok(x,g) for x,g in zip(a,G))/len(G),4)
    print(f"== fold {fi} ==",flush=True)
    # --- 1 luot: greedy ---
    g1_raw=gen(SOLVE,Q,512,0.0,"greedy1"); g1=[pred(x) for x in g1_raw]
    # --- 3 luot: maj@3 ---
    S=[gen(SOLVE,Q,512,0.8,"maj3") for _ in range(3)]
    a_mj=[]
    for i in range(len(Q)):
        c={}
        for r in range(3):
            p=pred(S[r][i])
            if p is not None: c[p]=c.get(p,0)+1
        a_mj.append(max(c,key=c.get) if c else None)
    # --- 3 luot: maj@3 CO MOT MAU GREEDY (doi chung tach nhieu loan #41) ---
    Sg=[g1_raw]+S[:2]
    a_mjg=[]
    for i in range(len(Q)):
        c={}
        for r_ in range(3):
            p=pred(Sg[r_][i]) if r_>0 else g1[i]
            if p is not None: c[p]=c.get(p,0)+1
        a_mjg.append(max(c,key=c.get) if c else None)
    # --- 3 luot: P -> S -> V ---
    pl=gen(PLAN,Q,384,0.0,"PSV")
    so=gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(Q,pl)],512,0.0,"PSV")
    ve=gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(Q,so)],512,0.0,"PSV")
    a_psv=[pred(x) for x in ve]
    # --- 3 luot: S -> V -> V ---
    s2=gen(SOLVE,Q,512,0.0,"SVV")
    v1=gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(Q,s2)],512,0.0,"SVV")
    v2=gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(Q,v1)],512,0.0,"SVV")
    a_svv=[pred(x) for x in v2]
    # --- 3 luot: S -> neo -> neo (KHONG co chu "kiem") ---
    s3=gen(SOLVE,Q,512,0.0,"SS_anc"); a3=[pred(x) for x in s3]
    r1=gen(SOLVE,[ANCH.replace("@@A@@",str(a))+f"\n\n{q}" for q,a in zip(Q,a3)],512,0.0,"SS_anc")
    b3=[pred(x) for x in r1]
    r2=gen(SOLVE,[ANCH.replace("@@A@@",str(a))+f"\n\n{q}" for q,a in zip(Q,b3)],512,0.0,"SS_anc")
    a_anc=[pred(x) for x in r2]
    r={"fold":fi,"n":len(Q),"greedy1":acc(g1),"maj3":acc(a_mj),"PSV":acc(a_psv),
       "SVV":acc(a_svv),"SS_anc":acc(a_anc),
       "maj3_g":acc(a_mjg),
       "maj3g_minus_maj3":round(acc(a_mjg)-acc(a_mj),4),
       "PSV_minus_maj3g":round(acc(a_psv)-acc(a_mjg),4),
       "maj3_minus_PSV":round(acc(a_mj)-acc(a_psv),4),
       "SVV_minus_maj3":round(acc(a_svv)-acc(a_mj),4),
       "SSanc_minus_PSV":round(acc(a_anc)-acc(a_psv),4)}
    folds.append(r); print(f"[fold {fi}] {json.dumps(r)}",flush=True)

def sp(k):
    v=[f[k] for f in folds]
    return {"mean":round(st.mean(v),4),"min":round(min(v),4),"max":round(max(v),4),
            "pos":sum(1 for x in v if x>0)}
out={"task":TASK,"n":len(qs),"quant":QUANT,"folds":folds,"tokens_per_arm":TOKENS}
for k in ["greedy1","maj3","maj3_g","PSV","SVV","SS_anc","maj3_minus_PSV",
          "maj3g_minus_maj3","PSV_minus_maj3g","SVV_minus_maj3","SSanc_minus_PSV"]:
    out[k]=sp(k)
print("TOKENS",json.dumps(TOKENS),flush=True)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
