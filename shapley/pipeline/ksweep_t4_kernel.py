# H30 (pre-reg #33) — k = 2..64 tren CUNG bo mau. Kiem tra khoang trong maj->oracle co that khong.
# oracle_solid@k = chi tinh dung khi >=2 trong k mau cung ra dap an dung (loai "dung do may").
import os, re, csv, json, glob, statistics as st, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK="__TASK__"; MODELV="__MODELV__"; N=__N__; BS=__BS__; KMAX=__KMAX__; NF=5
KS=__KS__
cap=torch.cuda.get_device_capability(0); gpu=torch.cuda.get_device_name(0)
print(f"GPU={gpu} sm={cap} vram={torch.cuda.get_device_properties(0).total_memory/1e9:.0f}GB",flush=True)
assert cap[0]>=7, f"GPU qua cu (sm={cap})"   # ban T4: chi can sm_75

c=[os.path.dirname(p) for p in glob.glob("/kaggle/input/**/config.json",recursive=True)]
MP=sorted(c,key=len)[0]; print("MODEL",MP,flush=True)
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
if TASK=="math":
    CSV=sorted(glob.glob("/kaggle/input/**/math_500_test.csv",recursive=True),key=len)[0]
    rows=list(csv.DictReader(open(CSV)))[:N]
    qs=[r["Question"] for r in rows]
    gs=[_bx(r["Answer"]) or (NUM.findall(r["Answer"]) or [""])[-1] for r in rows]
    S_SYS="Solve step by step. Put the final answer in \\boxed{}."
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
else:
    CSV=sorted(glob.glob("/kaggle/input/**/main_test.csv",recursive=True),key=len)[0]
    rows=list(csv.DictReader(open(CSV)))[:N]
    qs=[r["question"] for r in rows]
    gs=[NUM.findall(r["answer"].split("####")[-1])[0].replace(",","") for r in rows]
    S_SYS="Solve step by step. End with 'The answer is <number>'."
    def pred(t):
        m=re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)",t or "",re.I) or NUM.findall(t or "")
        return m[-1].replace(",","") if m else None
    def ok(x,g):
        try: return x is not None and abs(float(x)-float(g))<1e-4
        except: return x==g

tok=AutoTokenizer.from_pretrained(MP); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
if __QUANT__:
    import subprocess,sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"],check=False)
    from transformers import BitsAndBytesConfig
    _b=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    model=AutoModelForCausalLM.from_pretrained(MP,quantization_config=_b,device_map="auto").eval()
else:
    model=AutoModelForCausalLM.from_pretrained(MP,dtype=torch.float16,device_map="auto").eval()
@torch.no_grad()
def gen(us,mx=512,temp=0.8,k=1):
    out=[]
    for i in range(0,len(us),BS):
        ch=us[i:i+BS]
        ps=[tok.apply_chat_template([{"role":"system","content":S_SYS},{"role":"user","content":u}],
            tokenize=False,add_generation_prompt=True) for u in ch]
        e=tok(ps,return_tensors="pt",padding=True).to("cuda")
        o=model.generate(**e,max_new_tokens=mx,do_sample=(temp>0),temperature=max(temp,1e-5),
                         top_p=0.95,num_return_sequences=k,pad_token_id=tok.pad_token_id)
        L=e["input_ids"].shape[1]
        out+=[tok.decode(o[j,L:],skip_special_tokens=True).strip() for j in range(o.shape[0])]
        del e,o; torch.cuda.empty_cache()
        if i%(BS*10)==0: print(f"   ...{min(i+BS,len(us))}/{len(us)}",flush=True)
    return out

print(f"== sinh {KMAX} mau/bai ==",flush=True)
samp=gen(qs,512,0.8,KMAX)
G=[[pred(samp[i*KMAX+j]) for j in range(KMAX)] for i in range(len(qs))]
FOLD=len(qs)//NF; folds=[]
for fi in range(NF):
    lo,hi=fi*FOLD,(fi+1)*FOLD
    r={"fold":fi,"n":hi-lo}
    r["greedy1"]=round(sum(ok(G[i][0],gs[i]) for i in range(lo,hi))/(hi-lo),4)
    for k in KS:
        mj=[];orc=[];sol=[]
        for i in range(lo,hi):
            C=G[i][:k]; cnt={}
            for p in C:
                if p is not None: cnt[p]=cnt.get(p,0)+1
            mj.append(max(cnt,key=cnt.get) if cnt else None)
            nc=sum(1 for p in C if ok(p,gs[i]))
            orc.append(nc>=1); sol.append(nc>=2)          # oracle vs oracle_solid
        r[f"maj@{k}"]=round(sum(ok(a,g) for a,g in zip(mj,gs[lo:hi]))/(hi-lo),4)
        r[f"oracle@{k}"]=round(sum(orc)/(hi-lo),4)
        r[f"oracle_solid@{k}"]=round(sum(sol)/(hi-lo),4)
        r[f"gap@{k}"]=round(r[f"oracle@{k}"]-r[f"maj@{k}"],4)
        r[f"gap_solid@{k}"]=round(r[f"oracle_solid@{k}"]-r[f"maj@{k}"],4)
    folds.append(r); print(f"[fold {fi}] maj@8={r['maj@8']} orc@8={r['oracle@8']} solid@8={r['oracle_solid@8']}",flush=True)
def sp(key):
    v=[f[key] for f in folds]
    return {"mean":round(st.mean(v),4),"min":round(min(v),4),"max":round(max(v),4)}
out={"task":TASK,"model":MODELV,"gpu":gpu,"n":len(qs),"kmax":KMAX,"folds":folds,"by_k":{}}
out["greedy1"]=sp("greedy1")
for k in KS:
    out["by_k"][str(k)]={m:sp(f"{m}@{k}") for m in ["maj","oracle","oracle_solid","gap","gap_solid"]}
    b=out["by_k"][str(k)]
    print(f"k={k:2d}  maj={b['maj']['mean']:.4f}  oracle={b['oracle']['mean']:.4f}  "
          f"solid={b['oracle_solid']['mean']:.4f}  gap={b['gap']['mean']:+.4f}  gap_solid={b['gap_solid']['mean']:+.4f}",flush=True)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
json.dump([{"i":i,"gold":gs[i],"preds":G[i][:16]} for i in range(min(60,len(qs)))],
          open("/kaggle/working/traces.json","w"),indent=1)
print("DONE",flush=True)
