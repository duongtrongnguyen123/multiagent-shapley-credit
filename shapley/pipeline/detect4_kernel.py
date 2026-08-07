# H25 — KIEM LOI CO TACH ROI KHOI GIAI KHONG? Xem docs/PREREGISTRATION.md #24 (commit TRUOC khi chay).
# Phan tang bai theo NANG LUC GIAI cua chinh model (k=8 mau), roi do DO CHINH XAC PHAT HIEN
# loi so hoc DUOC TIEM SAN vao chuoi vang. CA HAI nhanh deu la chuoi vang -> khong lo nhan qua van phong.
import os, re, csv, json, glob, random, statistics, torch

TASK="__TASK__"; N=__N__; BS=__BS__; QUANT=__QUANT__; K=8
if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])
from transformers import AutoModelForCausalLM, AutoTokenizer
_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True) or \
   glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
FNAME="math_500_test.csv" if TASK=="math" else "main_test.csv"
CSV=sorted(glob.glob(f"/kaggle/input/**/{FNAME}",recursive=True),key=len)[0]
rows=list(csv.DictReader(open(CSV)))[:N]
print(f"MODEL={MODEL} n={len(rows)} k={K}",flush=True)
tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
if QUANT:
    from transformers import BitsAndBytesConfig
    _b=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    model=AutoModelForCausalLM.from_pretrained(MODEL,quantization_config=_b,device_map="auto").eval()
else:
    model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="cuda").eval()
print("loaded",flush=True)

def gen(sysm,usrs,mx=512,temp=0.0,k=1):
    outs=[]
    for i in range(0,len(usrs),BS):
        ch=usrs[i:i+BS]
        ps=[tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
            tokenize=False,add_generation_prompt=True) for u in ch]
        e=tok(ps,return_tensors="pt",padding=True).to(model.device)
        with torch.no_grad():
            o=model.generate(**e,max_new_tokens=mx,do_sample=(temp>0),temperature=max(temp,1e-5),
                             top_p=0.95,num_return_sequences=k,pad_token_id=tok.pad_token_id)
        L=e["input_ids"].shape[1]
        outs+=[tok.decode(o[j,L:],skip_special_tokens=True).strip() for j in range(o.shape[0])]
    print(f"   ...{len(usrs)}x{k} xong",flush=True)
    return outs

NUM=re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def pred(t):
    m=re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)",t or "",re.I) or NUM.findall(t or "")
    return m[-1].replace(",","") if m else None
def eq(a,g):
    try: return a is not None and abs(float(a)-float(g))<1e-4
    except: return a==g

def _boxed(t):
    i=(t or "").rfind("\\boxed")
    if i<0: return None
    i=t.find("{",i); d=0; st0=i
    for j in range(i,len(t)):
        if t[j]=="{": d+=1
        elif t[j]=="}":
            d-=1
            if d==0: return t[st0+1:j]
    return None
if TASK=="math":
    qs=[r["Question"] for r in rows]
    gs=[_boxed(r["Answer"]) or (NUM.findall(r["Answer"]) or [""])[-1] for r in rows]
    gold_chain=[r["Answer"].strip() for r in rows]
else:
    qs=[r["question"] for r in rows]
    gs=[NUM.findall(r["answer"].split("####")[-1])[0].replace(",","") for r in rows]
    gold_chain=[r["answer"].split("####")[0].strip() for r in rows]

# ---------- 1) NANG LUC GIAI: k=8 mau ----------
print("== do nang luc giai (k=8) ==",flush=True)
samp=gen("Solve step by step. End with 'The answer is <number>'.",qs,400,0.8,K)
solve_rate=[]
for i in range(len(qs)):
    c=sum(1 for j in range(K) if eq(pred(samp[i*K+j]),gs[i]))
    solve_rate.append(c)
def bucket(c): return "HIGH" if c>=6 else ("ZERO" if c==0 else "MID")
buck=[bucket(c) for c in solve_rate]
print("phan tang:",{b:buck.count(b) for b in ["HIGH","MID","ZERO"]},flush=True)

# ---------- 2) TIEM LOI SO HOC vao DUNG MOT buoc cua chuoi vang ----------
STEP=re.compile(r"<<([^=<>]+)=([^<>]+)>>")
PLAIN=re.compile(r"(\d+(?:\.\d+)?)\s*([-+*/])\s*(\d+(?:\.\d+)?)\s*=\s*(\d+(?:\.\d+)?)")
random.seed(0)
ANYNUM=re.compile(r"(?<![\\w.])(\\d+(?:\\.\\d+)?)(?![\\w.])")
def corrupt_any(chain):
    """MATH: doi MOT so bat ky trong THAN bai (tru \\boxed cuoi) -> mau thuan noi tai."""
    b=chain.rfind("\\boxed"); body=chain[:b] if b>0 else chain
    ms=[m for m in ANYNUM.finditer(body)]
    if not ms: return None,None
    m=random.choice(ms)
    try: val=float(m.group(1))
    except: return None,None
    d=random.choice([1,2,3,-1,-2]) if abs(val)>3 else random.choice([1,2,3])
    new=val+d; new=str(int(new)) if float(new).is_integer() else f"{new:g}"
    return chain[:m.start(1)]+new+chain[m.end(1):], f"{m.group(1)}->{new}"
def corrupt(chain):
    if TASK=="math": return corrupt_any(chain)
    ms=list(STEP.finditer(chain))
    if not ms:
        pm=list(PLAIN.finditer(chain))              # MATH: bieu thuc so hoc thuong
        if not pm: return None,None
        m=random.choice(pm)
        try: val=float(m.group(4))
        except: return None,None
        d=random.choice([1,2,3,-1,-2]) if abs(val)>3 else random.choice([1,2,3])
        new=val+d; new=str(int(new)) if float(new).is_integer() else f"{new:g}"
        s0,e0=m.span(4)
        return chain[:s0]+new+chain[e0:], f"{m.group(4)}->{new}"
    m=random.choice(ms)
    try: val=float(m.group(2))
    except: return None,None
    d=random.choice([1,2,3,-1,-2]) if abs(val)>3 else random.choice([1,2,3])
    new=val+d
    new=str(int(new)) if float(new).is_integer() else f"{new:g}"
    old_txt=m.group(0); old_res=m.group(2)
    # doi CA trong <<...>> VA con so lap lai ngay sau no
    seg=chain[m.start():m.end()+len(old_res)+2]
    new_seg=seg.replace(old_res,new)
    return chain[:m.start()]+new_seg+chain[m.start()+len(seg):], f"{old_res}->{new}"

pairs=[]   # (i, variant, text)
for i,ch in enumerate(gold_chain):
    cor,tagd=corrupt(ch)
    if cor is None or cor==ch: continue
    pairs.append((i,"CLEAN",ch)); pairs.append((i,"CORRUPT",cor))
pct_corr=round((len(pairs)//2)/max(len(rows),1),4)
print(f"cap hop le: {len(pairs)//2} bai | pct_problems_corruptible={pct_corr}",flush=True)

DET=("Check EACH computational step of the solution and verify the arithmetic. "
     "Work through it, then end your reply with a final line of exactly "
     "'VERDICT: YES' if any step contains a computational error, or 'VERDICT: NO' if all steps are correct.")
usrs=[f"Problem: {qs[i]}\n\nSolution:\n{t}\n\nDoes this solution contain a computational error?"
      for (i,v,t) in pairs]
print("== phat hien loi ==",flush=True)
ans=gen(DET,usrs,400,0.0)
def says_err(t):
    """Doc dong VERDICT cuoi. Tra None neu khong doc duoc -> tinh vao parse_fail."""
    m=re.findall(r"verdict\s*:\s*(yes|no)",(t or "").lower())
    if m: return m[-1]=="yes"
    m2=re.findall(r"\b(yes|no)\b",(t or "").lower())
    return (m2[-1]=="yes") if m2 else None

res={b:{"CLEAN":[], "CORRUPT":[]} for b in ["HIGH","MID","ZERO"]}
n_fail=0
for (i,v,t),a in zip(pairs,ans):
    d=says_err(a)
    if d is None: n_fail+=1; continue
    res[buck[i]][v].append(d)
parse_fail=round(n_fail/max(len(pairs),1),4)
print(f"parse_fail_rate={parse_fail}",flush=True)

out={"task":TASK,"n":len(rows),"quant":QUANT,"k":K,"parse_fail_rate":parse_fail,
     "pct_problems_corruptible":pct_corr,"VALID_corruptible":bool(pct_corr>=0.50),
     "buckets":{b:buck.count(b) for b in ["HIGH","MID","ZERO"]},
     "mean_solve_rate":round(statistics.mean(solve_rate)/K,4),"tiers":{}}
for b in ["HIGH","MID","ZERO"]:
    cl,co=res[b]["CLEAN"],res[b]["CORRUPT"]
    if not cl or not co: out["tiers"][b]=None; continue
    tnr=sum(co)/len(co)                 # phat hien dung loi da tiem
    fpr=sum(cl)/len(cl)                 # THIEN LECH: keu loi tren chuoi SACH
    out["tiers"][b]={"n_pairs":len(co),
        "detect_rate_on_CORRUPT":round(tnr,4),
        "false_alarm_on_CLEAN":round(fpr,4),
        "discrimination":round(tnr-fpr,4),          # <-- CHI SO CHINH, mien nhiem thien lech
        "balanced_acc":round((tnr+(1-fpr))/2,4),
        # NGUONG HIEU LUC da khoa o pre-reg #26: suy bien >.90 -> tang VO HIEU
        "degenerate_rate":round(max(sum(cl+co),len(cl+co)-sum(cl+co))/max(len(cl+co),1),4),
        "VALID":bool(max(sum(cl+co),len(cl+co)-sum(cl+co))/max(len(cl+co),1) <= 0.90),
        "ENOUGH_POWER":bool(len(co)>=40)}   # nguong n>=40 khoa o pre-reg #28
    print(f"[{b}] {json.dumps(out['tiers'][b])}",flush=True)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
tr=[{"i":i,"bucket":buck[i],"variant":v,"solve_rate":solve_rate[i],
     "chain":t[:900],"model_says":ans[n][:60]} for n,(i,v,t) in enumerate(pairs)][:400]
json.dump(tr,open("/kaggle/working/traces.json","w"),indent=1)
print("traces:",len(tr),flush=True)
