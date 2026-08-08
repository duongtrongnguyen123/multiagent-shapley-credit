# H29 (pre-reg #32) — DUONG CONG NANG LUC CUA VIEC KIEM LOI, bf16 toan bo, MATH-500.
# Chay tren RTX 6000 Pro (102 GB). Nhieu model TUAN TU trong mot kernel.
import os, re, csv, json, glob, gc, random, statistics as st, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODELS = __MODELS__          # vd: ["7b-instruct","14b-instruct"]
N      = __N__
BS     = __BS__
K      = 8

# --- BAT BUOC: xac nhan GPU that su la RTX 6000 Pro, khong tut ve P100 ---
cap = torch.cuda.get_device_capability(0)
gpu = torch.cuda.get_device_name(0)
vram = torch.cuda.get_device_properties(0).total_memory/1e9
print(f"GPU={gpu} sm={cap} vram={vram:.0f}GB torch={torch.__version__}", flush=True)
assert cap[0] >= 12, f"KHONG PHAI RTX 6000 Pro (sm={cap}) -> dung lai, tranh do so lieu ban"

CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
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
qs=[r["Question"] for r in rows]
gs=[_bx(r["Answer"]) or (NUM.findall(r["Answer"]) or [""])[-1] for r in rows]
chains=[r["Answer"].strip() for r in rows]
def _nm(a):
    if a is None: return None
    a=str(a).strip()
    for z in ["\\left","\\right","\\!","\\,","\;","$"," ",","]: a=a.replace(z,"")
    a=re.sub(r"\\text\s*\{([^}]*)\}",r"\1",a).replace("\\dfrac","\\frac").replace("\\tfrac","\\frac")
    return a.rstrip(".").strip("{}").lower()
def ok(x,g):
    x,g=_nm(x),_nm(g)
    if not x or not g: return False
    if x==g: return True
    try: return abs(float(x)-float(g))<1e-6
    except: return False
def pred(t):
    b=_bx(t)
    if b is not None: return b.strip()
    m=re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)",t or "",re.I)
    return m[-1].strip() if m else None

# --- tiem loi: doi MOT so bat ky trong THAN bai (tru \boxed cuoi) ---
ANY=re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")
random.seed(0)
def corrupt(ch):
    b=ch.rfind("\\boxed"); body=ch[:b] if b>0 else ch
    ms=list(ANY.finditer(body))
    if not ms: return None
    m=random.choice(ms)
    try: v=float(m.group(1))
    except: return None
    nv=v+(random.choice([1,2,3,-1,-2]) if abs(v)>3 else random.choice([1,2,3]))
    nv=str(int(nv)) if float(nv).is_integer() else f"{nv:g}"
    return ch[:m.start(1)]+nv+ch[m.end(1):]
pairs=[]
for i,ch in enumerate(chains):
    c=corrupt(ch)
    if c and c!=ch: pairs.append((i,"CLEAN",ch)); pairs.append((i,"CORRUPT",c))
pct_corr=round((len(pairs)//2)/max(len(rows),1),4)
print(f"cap tiem duoc: {len(pairs)//2}/{len(rows)}  pct={pct_corr}",flush=True)

S_SYS="Solve step by step. Put the final answer in \\boxed{}."
DET=("Check EACH computational step of the solution and verify the arithmetic. Work through it, "
     "then end your reply with a final line of exactly 'VERDICT: YES' if any step contains a "
     "computational error, or 'VERDICT: NO' if all steps are correct.")
def verdict(t):
    m=re.findall(r"verdict\s*:\s*(yes|no)",(t or "").lower())
    if m: return m[-1]=="yes"
    m2=re.findall(r"\b(yes|no)\b",(t or "").lower())
    return (m2[-1]=="yes") if m2 else None

ALL={}
for mv in MODELS:
    base=glob.glob(f"/kaggle/input/**/{mv}/**/config.json",recursive=True) or \
         glob.glob(f"/kaggle/input/**/{mv}/config.json",recursive=True)
    if not base:
        cands=[os.path.dirname(p) for p in glob.glob("/kaggle/input/**/config.json",recursive=True) if mv in p]
        base=[cands[0]+"/config.json"] if cands else []
    if not base: print(f"!! khong tim thay {mv}",flush=True); continue
    MP=os.path.dirname(base[0]); print(f"\n===== {mv} @ {MP} =====",flush=True)
    tok=AutoTokenizer.from_pretrained(MP); tok.padding_side="left"
    if tok.pad_token is None: tok.pad_token=tok.eos_token
    model=AutoModelForCausalLM.from_pretrained(MP,dtype=torch.bfloat16,device_map="cuda").eval()
    @torch.no_grad()
    def gen(sysm,us,mx=512,temp=0.0,k=1):
        out=[]
        for i in range(0,len(us),BS):
            ch=us[i:i+BS]
            ps=[tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                tokenize=False,add_generation_prompt=True) for u in ch]
            e=tok(ps,return_tensors="pt",padding=True).to("cuda")
            o=model.generate(**e,max_new_tokens=mx,do_sample=(temp>0),temperature=max(temp,1e-5),
                             top_p=0.95,num_return_sequences=k,pad_token_id=tok.pad_token_id)
            L=e["input_ids"].shape[1]
            out+=[tok.decode(o[j,L:],skip_special_tokens=True).strip() for j in range(o.shape[0])]
            del e,o; torch.cuda.empty_cache()
        return out
    samp=gen(S_SYS,qs,512,0.8,K)
    rate=[sum(1 for j in range(K) if ok(pred(samp[i*K+j]),gs[i])) for i in range(len(qs))]
    buck=["HIGH" if c>=6 else ("ZERO" if c==0 else "MID") for c in rate]
    print(f"  phan tang: {[(b,buck.count(b)) for b in ['HIGH','MID','ZERO']]}  solve={st.mean(rate)/K:.3f}",flush=True)
    ans=gen(DET,[f"Problem: {qs[i]}\n\nSolution:\n{t}\n\nDoes this solution contain a computational error?"
                 for (i,v,t) in pairs],512,0.0)
    res={b:{"CLEAN":[],"CORRUPT":[]} for b in ["HIGH","MID","ZERO"]}; nf=0
    for (i,v,t),a in zip(pairs,ans):
        d=verdict(a)
        if d is None: nf+=1; continue
        res[buck[i]][v].append(d)
    pf=round(nf/max(len(pairs),1),4)
    ent={"model":mv,"gpu":gpu,"sm":list(cap),"parse_fail_rate":pf,
         "pct_problems_corruptible":pct_corr,"VALID_corruptible":bool(pct_corr>=0.50),
         "VALID_parse":bool(pf<=0.20),"mean_solve_rate":round(st.mean(rate)/K,4),
         "buckets":{b:buck.count(b) for b in ["HIGH","MID","ZERO"]},"tiers":{}}
    for b in ["HIGH","MID","ZERO"]:
        cl,co=res[b]["CLEAN"],res[b]["CORRUPT"]
        if not cl or not co: ent["tiers"][b]=None; continue
        tnr=sum(co)/len(co); fpr=sum(cl)/len(cl); av=cl+co
        deg=max(sum(av),len(av)-sum(av))/max(len(av),1)
        ent["tiers"][b]={"n_pairs":len(co),"detect":round(tnr,4),"false_alarm":round(fpr,4),
            "discrimination":round(tnr-fpr,4),"balanced_acc":round((tnr+(1-fpr))/2,4),
            "degenerate_rate":round(deg,4),"VALID":bool(deg<=0.90),"ENOUGH_POWER":bool(len(co)>=40)}
        print(f"  [{b}] {json.dumps(ent['tiers'][b])}",flush=True)
    ALL[mv]=ent
    json.dump(ALL,open("/kaggle/working/summary.json","w"),indent=2)   # luu SAU MOI model
    json.dump([{"model":mv,"i":i,"bucket":buck[i],"variant":v,"says":ans[n][-260:]}
               for n,(i,v,t) in enumerate(pairs)][:300],
              open(f"/kaggle/working/traces_{mv}.json","w"),indent=1)
    del model,tok; gc.collect(); torch.cuda.empty_cache()
print("SUMMARY",json.dumps(ALL),flush=True)
print("DONE",flush=True)
