# H34 — MOT CAU HINH MOI NOTEBOOK (chay song song), moi kernel co DOI CHUNG CUNG NGAN SACH.
# Cau hinh: PSV | SVV | SS_anc | P3S | PSVA | 3S_1V | 2S_1V   (V nho = 0.5B, V thuong = 1.5B)
import os, re, csv, json, glob, statistics as st, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK="__TASK__"; ARM="__ARM__"; NGEN=__NGEN__; N=__N__; BS=__BS__; SMALL_V=__SMALL_V__; NF=5

def find_model(pat):
    c=[os.path.dirname(p) for p in glob.glob("/kaggle/input/**/config.json",recursive=True) if pat in p.lower()]
    if not c: raise SystemExit(f"khong tim thay model khop {pat!r}")
    return sorted(c,key=len)[0]
MAIN=find_model("1-5b") if glob.glob("/kaggle/input/**/*1-5b*/**",recursive=True) else find_model("1.5b")
print(f"TASK={TASK} ARM={ARM} NGEN={NGEN} MAIN={MAIN} SMALL_V={SMALL_V}",flush=True)

FN="main_test.csv" if TASK=="gsm8k" else "math_500_test.csv"
CSV=sorted(glob.glob(f"/kaggle/input/**/{FN}",recursive=True),key=len)[0]
rows=list(csv.DictReader(open(CSV)))[:N]
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

tokM=AutoTokenizer.from_pretrained(MAIN); tokM.padding_side="left"
if tokM.pad_token is None: tokM.pad_token=tokM.eos_token
mdlM=AutoModelForCausalLM.from_pretrained(MAIN,torch_dtype=torch.float16,device_map="cuda").eval()
mdlS,tokS=None,None
if SMALL_V:
    SM=find_model("0-5b") if glob.glob("/kaggle/input/**/*0-5b*/**",recursive=True) else find_model("0.5b")
    tokS=AutoTokenizer.from_pretrained(SM); tokS.padding_side="left"
    if tokS.pad_token is None: tokS.pad_token=tokS.eos_token
    mdlS=AutoModelForCausalLM.from_pretrained(SM,torch_dtype=torch.float16,device_map="cuda").eval()
    print("small V:",SM,flush=True)

TOK={}
def gen(sysm,us,mx,temp,who,small=False):
    m,t=(mdlS,tokS) if small else (mdlM,tokM)
    outs=[];ntok=0
    for i in range(0,len(us),BS):
        ch=us[i:i+BS]
        ps=[t.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
            tokenize=False,add_generation_prompt=True) for u in ch]
        e=t(ps,return_tensors="pt",padding=True).to("cuda")
        with torch.no_grad():
            o=m.generate(**e,max_new_tokens=mx,do_sample=(temp>0),temperature=max(temp,1e-5),
                         top_p=0.95,pad_token_id=t.pad_token_id)
        L=e["input_ids"].shape[1]
        for j in range(len(ch)):
            g=o[j,L:]; ntok+=int((g!=t.pad_token_id).sum())
            outs.append(t.decode(g,skip_special_tokens=True).strip())
        del e,o; torch.cuda.empty_cache()
    TOK[who]=TOK.get(who,0)+ntok
    return outs

SOLVE=f"Solve step by step. {TAIL}"
PLAN ="Give a concise numbered plan for solving this problem."
VERIFY=f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
PICK =f"You are given candidate solutions to the same problem. Check them and give the correct final answer. {TAIL}"
ANCH =f"Solve step by step. A previous attempt answered: @@A@@. {TAIL}"

def vote(cols,i,k):
    c={}
    for r in range(k):
        p=pred(cols[r][i])
        if p is not None: c[p]=c.get(p,0)+1
    return max(c,key=c.get) if c else None

folds=[]; FOLD=len(qs)//NF
for fi in range(NF):
    lo,hi=fi*FOLD,(fi+1)*FOLD
    Q,G=qs[lo:hi],gs[lo:hi]
    acc=lambda a: round(sum(ok(x,g) for x,g in zip(a,G))/len(G),4)
    print(f"== fold {fi} ==",flush=True)
    g1=[pred(x) for x in gen(SOLVE,Q,512,0.0,"greedy1")]
    # DOI CHUNG cung ngan sach: maj@NGEN
    Sc=[gen(SOLVE,Q,512,0.8,f"maj{NGEN}") for _ in range(NGEN)]
    a_ctl=[vote(Sc,i,NGEN) for i in range(len(Q))]
    # NHANH CAN KIEM
    if ARM=="PSV":
        pl=gen(PLAN,Q,384,0.0,ARM)
        so=gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(Q,pl)],512,0.0,ARM)
        a=[pred(x) for x in gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(Q,so)],512,0.0,ARM)]
    elif ARM=="SVV":
        s1=gen(SOLVE,Q,512,0.0,ARM)
        v1=gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(Q,s1)],512,0.0,ARM)
        a=[pred(x) for x in gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(Q,v1)],512,0.0,ARM)]
    elif ARM=="3S_1V":
        C=[gen(SOLVE,Q,512,0.8,ARM) for _ in range(3)]
        us=[f"{Q[i]}\n\nCandidate 1:\n{C[0][i]}\n\nCandidate 2:\n{C[1][i]}\n\nCandidate 3:\n{C[2][i]}"
            for i in range(len(Q))]
        vv=gen(PICK,us,512,0.0,ARM,small=SMALL_V)
        a=[pred(vv[i]) if pred(vv[i]) is not None else vote(C,i,3) for i in range(len(Q))]
    elif ARM=="2S_1V":
        C=[gen(SOLVE,Q,512,0.8,ARM) for _ in range(2)]
        us=[f"{Q[i]}\n\nCandidate 1:\n{C[0][i]}\n\nCandidate 2:\n{C[1][i]}" for i in range(len(Q))]
        vv=gen(PICK,us,512,0.0,ARM,small=SMALL_V)
        a=[pred(vv[i]) if pred(vv[i]) is not None else vote(C,i,2) for i in range(len(Q))]
    else:
        raise SystemExit(f"ARM la khong ro: {ARM}")
    r={"fold":fi,"n":len(Q),"greedy1":acc(g1),f"maj{NGEN}":acc(a_ctl),ARM:acc(a),
       "arm_minus_ctl":round(acc(a)-acc(a_ctl),4)}
    folds.append(r); print(f"[fold {fi}] {json.dumps(r)}",flush=True)

def sp(k):
    v=[f[k] for f in folds]
    return {"mean":round(st.mean(v),4),"min":round(min(v),4),"max":round(max(v),4),
            "pos":sum(1 for x in v if x>0)}
out={"task":TASK,"arm":ARM,"ngen":NGEN,"small_v":SMALL_V,"n":len(qs),
     "folds":folds,"tokens":TOK}
for k in ["greedy1",f"maj{NGEN}",ARM,"arm_minus_ctl"]: out[k]=sp(k)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
