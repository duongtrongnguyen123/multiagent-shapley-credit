# H9 — PIPELINE TỐI GIẢN vs PIPELINE TRUYỀN TOÀN BỘ TRACE (thí nghiệm HỢP NHẤT, đầu-cuối)
# Xem docs/PREREGISTRATION.md #8 (commit TRƯỚC khi chạy).
# ĐO ĐƯỢC nhiều lần: ở TỪNG vai, truyền thêm trace đều vô ích hoặc có hại
#   (Verifier: chỉ-đáp-án tốt nhất 3/3; Aggregator: .533 -> .300 khi thêm toàn văn).
# Mọi framework đa tác tử hiện nay đều truyền TOÀN BỘ trace. Ở đây đo ĐẦU-CUỐI xem điều đó
# có đáng không, kèm CHI PHÍ context.
#   S_only : chỉ Solver (mốc, không đa tác tử)
#   FULL   : P->S->V->A, mỗi agent nhận TOÀN VĂN output trước đó   (chuẩn hiện hành)
#   MIN    : P->S->V->A, mỗi agent chỉ nhận ĐÁP ÁN của agent trước (không trace)
import os, re, csv, json, glob, statistics, torch
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

CHARS={"FULL":0,"MIN":0}      # đếm chi phí context
def gen(sysm,usrs,mx=768,bucket=None):
    if bucket: CHARS[bucket]+=sum(len(u) for u in usrs)
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
    fmt=lambda a:f"The answer is {a}."
else:
    gold_of=lambda r:boxed(r["Answer"])
    def pred(t):
        b=boxed(t)
        if b is not None: return b
        m=re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)",t or "",re.I); return m[-1].strip() if m else None
    q_of=lambda r:r["Question"]; TAIL="Put the final answer in \\boxed{}."
    fmt=lambda a:f"The answer is \\boxed{{{a}}}."

qs=[q_of(r) for r in rows]; gs=[gold_of(r) for r in rows]
PLAN=f"Give a concise numbered plan. Do NOT compute the final answer."
SOLVE=f"Solve step by step. {TAIL}"
VERIFY=f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
AGG=f"Given candidate answers, decide the correct final answer. {TAIL}"
def acc(a): return round(sum(eq(x,g) for x,g in zip(a,gs))/len(gs),4)

# ---------- MỐC: chỉ Solver ----------
solo=[pred(s) for s in gen(SOLVE,qs,768)]
print(f"[S_only] acc={acc(solo)}",flush=True)

# ---------- FULL: truyền TOÀN VĂN ----------
plans=gen(PLAN,qs,320,"FULL")
sF=gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,plans)],768,"FULL")
vF=gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sF)],768,"FULL")
aF=gen(AGG,[f"{q}\n\nCandidate 1:\n{s}\n\nCandidate 2:\n{v}" for q,s,v in zip(qs,sF,vF)],512,"FULL")
accF=acc([pred(x) for x in aF])
print(f"[FULL] acc={accF} chars={CHARS['FULL']}",flush=True)

# ---------- MIN: chỉ truyền ĐÁP ÁN ----------
# Planner vẫn chạy (nó là agent đầu, không có gì phía trước để rút gọn) nhưng KHÔNG chuyển tiếp.
sM=gen(SOLVE,qs,768,"MIN")                                   # Solver KHÔNG nhận kế hoạch
saM=[pred(x) for x in sM]
vM=gen(VERIFY,[f"{q}\n\nProposed solution:\n{fmt(a)}" for q,a in zip(qs,saM)],768,"MIN")
vaM=[pred(x) for x in vM]
aM=gen(AGG,[f"{q}\n\nCandidate 1: {a1}\nCandidate 2: {a2}" for q,a1,a2 in zip(qs,saM,vaM)],512,"MIN")
accM=acc([pred(x) for x in aM])
print(f"[MIN] acc={accM} chars={CHARS['MIN']}",flush=True)

out={"task":TASK,"n":len(gs),
     "acc_solver_only":acc(solo),
     "acc_full":accF,"acc_min":accM,
     "chars_full":CHARS["FULL"],"chars_min":CHARS["MIN"],
     "chars_ratio":round(CHARS["FULL"]/max(CHARS["MIN"],1),2),
     "min_minus_full":round(accM-accF,4),
     "full_minus_solo":round(accF-acc(solo),4),
     "min_minus_solo":round(accM-acc(solo),4)}
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
