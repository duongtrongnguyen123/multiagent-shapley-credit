# H5 — PIPELINE CÓ ĐANG VỨT MẤT PHẦN SUY LUẬN TRƯỚC KHI VERIFIER NHÌN THẤY KHÔNG?
# Xem docs/PREREGISTRATION.md #4 (commit TRƯỚC khi chạy).
# ĐO ĐƯỢC (H4): có Planner -> Solver chỉ viết 18 ký tự nhưng acc TĂNG .632->.684; nhắc nhở
#   không cứu được. => suy luận nằm TRONG KẾ HOẠCH, nhưng pipeline chỉ chuyển LỜI GIẢI (đã trơ).
# Ở đây: Planner LUÔN BẬT, dùng CÙNG một bộ (plan, solution), chỉ đổi thứ Verifier ĐƯỢC THẤY.
import os, re, csv, json, glob, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK="__TASK__"; N=__N__; BS=__BS__; QUANT=__QUANT__
if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])

_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True) or \
   glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True)
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

# Planner LUÔN BẬT — tái tạo đúng điều kiện đã đo ở H4
plans=gen(PLAN,qs,320)
sols=gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,plans)],768)
sa=[pred(s) for s in sols]; s_ok=[eq(a,g) for a,g in zip(sa,gs)]
n_cor=sum(s_ok); base=n_cor/len(gs)
print(f"solver acc={base:.4f} | median plan={int(statistics.median(len(p) for p in plans))} "
      f"| median sol={int(statistics.median(len(s or '') for s in sols))}",flush=True)

out={"task":TASK,"n":len(gs),"quant":QUANT,"solver_acc":round(base,4),"solver_correct":n_cor,
     "median_plan_len":int(statistics.median(len(p) for p in plans)),
     "median_sol_len":int(statistics.median(len(s or "") for s in sols)),"arms":{}}

views={
 "V_sol":  [f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)],
 "V_plan": [f"{q}\n\nSolver's plan:\n{p}\n\nSolver's answer: {fmt(a)}" for q,p,a in zip(qs,plans,sa)],
 "V_both": [f"{q}\n\nSolver's plan:\n{p}\n\nProposed solution:\n{s}" for q,p,s in zip(qs,plans,sols)],
 "V_none": [f"{q}\n\nProposed solution:\n{fmt(a)}" for q,a in zip(qs,sa)],
}
for tag,usrs in views.items():
    print(f"== {tag} ==",flush=True)
    va=[pred(v) for v in gen(VERIFY,usrs,768)]
    v_ok=[eq(a,g) for a,g in zip(va,gs)]
    r={"verifier_acc":round(sum(v_ok)/len(gs),4),
       "value_added":round(sum(v_ok)/len(gs)-base,4),
       "fixes":sum(1 for i in range(len(gs)) if not s_ok[i] and v_ok[i]),
       "breaks":sum(1 for i in range(len(gs)) if s_ok[i] and not v_ok[i]),
       "changed_answer":sum(1 for i in range(len(gs)) if norm(va[i])!=norm(sa[i])),
       "median_ctx_chars":int(statistics.median(len(u) for u in usrs))}
    out["arms"][tag]=r; print(f"[{tag}] {json.dumps(r)}",flush=True)

print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
