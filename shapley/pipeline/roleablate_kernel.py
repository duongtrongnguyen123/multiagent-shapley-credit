# H11 — VAI NÀO PHÍA SAU MANG GIÁ TRỊ: VERIFIER hay AGGREGATOR?
# Xem docs/PREREGISTRATION.md #10 (commit TRƯỚC khi chạy).
# ĐO ĐƯỢC (tr_g15): P->S .684 | P->S->V->A toàn văn .744 (+6.0) | chỉ-đáp-án .668 (ÂM).
# Chưa biết +6.0 đó do Verifier hay Aggregator. Đây là câu hỏi PHÂN BỔ ĐÓNG GÓP gốc của dự án,
# nhưng đo ở mức ĐẦU-CUỐI thay vì từng vai riêng lẻ (bài học từ vòng #10).
#   PS | PSV (chỉ Verifier) | PSA (chỉ Aggregator) | PSVA (đầy đủ)
import os, re, csv, json, glob, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK="__TASK__"; N=__N__; BS=__BS__; QUANT=__QUANT__
if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])

_c=(glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True) if QUANT
    else glob.glob("/kaggle/input/**/model.safetensors",recursive=True))
MODEL=os.path.dirname(sorted(_c,key=len)[0])
FNAME="main_test.csv" if TASK=="gsm8k" else "math_500_test.csv"
CSV=sorted(glob.glob(f"/kaggle/input/**/{FNAME}",recursive=True),key=len)[0]
rows=list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} n={len(rows)}",flush=True)

tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
if QUANT:
    from transformers import BitsAndBytesConfig
    _b=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
                          bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    model=AutoModelForCausalLM.from_pretrained(MODEL,quantization_config=_b,device_map="auto").eval()
else:
    model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="auto").eval()
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
PLAN=f"Give a concise numbered plan. Do NOT compute the final answer."
SOLVE=f"Solve step by step. {TAIL}"
VERIFY=f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
AGG=f"Given candidate solutions, decide the correct final answer. {TAIL}"
def acc(a): return round(sum(eq(x,g) for x,g in zip(a,gs))/len(gs),4)
def changed(a,b): return sum(1 for i in range(len(gs)) if norm(a[i])!=norm(b[i]))

# CÙNG (plan, solution) cho MỌI nhánh -> chỉ đổi vai nào có mặt
plans=gen(PLAN,qs,320)
sols=gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,plans)],768)
sa=[pred(s) for s in sols]
out={"task":TASK,"n":len(gs),"quant":QUANT,"acc_PS":acc(sa),"arms":{}}
print(f"[PS] acc={out['acc_PS']}",flush=True)

# PSV: chỉ Verifier
vers=gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)],768)
va=[pred(v) for v in vers]
out["arms"]["PSV"]={"acc":acc(va),"changed_by_V":changed(va,sa)}
print(f"[PSV] {json.dumps(out['arms']['PSV'])}",flush=True)

# PSA: chỉ Aggregator (nhận lời giải của S, KHÔNG có V)
aggA=gen(AGG,[f"{q}\n\nCandidate solution:\n{s}" for q,s in zip(qs,sols)],512)
aa=[pred(x) for x in aggA]
out["arms"]["PSA"]={"acc":acc(aa),"changed_by_A":changed(aa,sa)}
print(f"[PSA] {json.dumps(out['arms']['PSA'])}",flush=True)

# PSVA: đầy đủ
aggF=gen(AGG,[f"{q}\n\nCandidate 1:\n{s}\n\nCandidate 2:\n{v}" for q,s,v in zip(qs,sols,vers)],512)
fa=[pred(x) for x in aggF]
out["arms"]["PSVA"]={"acc":acc(fa),"changed_vs_S":changed(fa,sa),"changed_vs_V":changed(fa,va)}
print(f"[PSVA] {json.dumps(out['arms']['PSVA'])}",flush=True)

out["V_alone_gain"]=round(out["arms"]["PSV"]["acc"]-out["acc_PS"],4)
out["A_alone_gain"]=round(out["arms"]["PSA"]["acc"]-out["acc_PS"],4)
out["both_gain"]   =round(out["arms"]["PSVA"]["acc"]-out["acc_PS"],4)
out["synergy"]     =round(out["both_gain"]-out["V_alone_gain"]-out["A_alone_gain"],4)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
