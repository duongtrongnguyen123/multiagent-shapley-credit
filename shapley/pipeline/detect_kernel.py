# H25 — KIEM LOI CO TACH ROI KHOI GIAI KHONG? Xem docs/PREREGISTRATION.md #24 (commit TRUOC khi chay).
# Phan tang bai theo NANG LUC GIAI cua chinh model (k=8 mau), roi do DO CHINH XAC PHAT HIEN
# loi so hoc DUOC TIEM SAN vao chuoi vang. CA HAI nhanh deu la chuoi vang -> khong lo nhan qua van phong.
import os, re, csv, json, glob, random, statistics, torch

N=__N__; BS=__BS__; QUANT=__QUANT__; K=8
if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])
from transformers import AutoModelForCausalLM, AutoTokenizer
_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True) or \
   glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
CSV=sorted(glob.glob("/kaggle/input/**/main_test.csv",recursive=True),key=len)[0]
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
    model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="auto").eval()
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
random.seed(0)
def corrupt(chain):
    ms=list(STEP.finditer(chain))
    if not ms: return None,None
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
print(f"cap hop le: {len(pairs)//2} bai",flush=True)

DET=("You are checking a solution for computational errors. "
     "Answer with exactly one word: YES if the solution contains a computational error, NO if it is correct.")
usrs=[f"Problem: {qs[i]}\n\nSolution:\n{t}\n\nDoes this solution contain a computational error?"
      for (i,v,t) in pairs]
print("== phat hien loi ==",flush=True)
ans=gen(DET,usrs,16,0.0)
def says_err(t):
    t=(t or "").strip().lower()
    if t.startswith("yes"): return True
    if t.startswith("no"):  return False
    return ("yes" in t[:20]) and ("no" not in t[:20])

res={b:{"CLEAN":[], "CORRUPT":[]} for b in ["HIGH","MID","ZERO"]}
for (i,v,t),a in zip(pairs,ans):
    res[buck[i]][v].append(says_err(a))

out={"n":len(rows),"quant":QUANT,"k":K,
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
        "balanced_acc":round((tnr+(1-fpr))/2,4)}
    print(f"[{b}] {json.dumps(out['tiers'][b])}",flush=True)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
tr=[{"i":i,"bucket":buck[i],"variant":v,"solve_rate":solve_rate[i],
     "chain":t[:900],"model_says":ans[n][:60]} for n,(i,v,t) in enumerate(pairs)][:400]
json.dump(tr,open("/kaggle/working/traces.json","w"),indent=1)
print("traces:",len(tr),flush=True)
