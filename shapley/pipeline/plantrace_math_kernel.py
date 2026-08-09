# PLANNER CÓ TỰ GIẢI LUÔN KHÔNG — ĐO TRÊN MATH (đối chứng với phát hiện trên GSM8K).
# ĐO ĐƯỢC ở GSM8K (n=200, 1.5B): kế hoạch đã chứa đáp án đúng 45.5%; đáp án Solver trùng số cuối
#   của kế hoạch 62.5%; lời giải Solver <60 ký tự 69%; "chép lại" 61%;
#   kế hoạch ĐÚNG -> Solver đúng 98.9%, kế hoạch SAI -> Solver đúng 37.6%.
# Câu hỏi: trên MATH (Solver vốn viết 899 ký tự) thì Planner có lấn sân như vậy không?
# Kernel tự tính luôn thống kê + lưu trace để đọc tay.
import os, re, csv, json, glob, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N=__N__; BS=__BS__; QUANT=__QUANT__
if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])

_c=(glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True) if QUANT
    else glob.glob("/kaggle/input/**/model.safetensors",recursive=True))
MODEL=os.path.dirname(sorted(_c,key=len)[0])
CSV=sorted(glob.glob("/kaggle/input/**/math_500_test.csv",recursive=True),key=len)[0]
rows=list(csv.DictReader(open(CSV)))[:N]
print(f"MODEL={MODEL} n={len(rows)}",flush=True)

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
        print(f"    {min(i+BS,len(usrs))}/{len(usrs)}",flush=True)
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
def pred(t):
    b=boxed(t)
    if b is not None: return b
    m=re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)",t or "",re.I); return m[-1].strip() if m else None
def plan_tail(p):
    """'Đáp án' ngầm của kế hoạch: ưu tiên \\boxed, nếu không thì lấy vế phải dấu '=' cuối cùng."""
    b=boxed(p)
    if b is not None: return b
    m=re.findall(r"=\s*([^\n=]+?)\s*(?:$|\n)", p or "")
    return m[-1].strip() if m else None

qs=[r["Question"] for r in rows]; gs=[boxed(r["Answer"]) for r in rows]
PLAN="Give a concise numbered plan. Do NOT compute the final answer."
SOLVE="Solve step by step. Put the final answer in \\boxed{}."

plans=gen(PLAN,qs,384)
sols =gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,plans)],768)
sa=[pred(s) for s in sols]
pt=[plan_tail(p) for p in plans]

n=len(qs)
plan_has_ans   = sum(1 for i in range(n) if eq(pt[i], gs[i]))
plan_has_boxed = sum(1 for p in plans if boxed(p) is not None)      # vi phạm rõ ràng nhất
solver_eq_plan = sum(1 for i in range(n) if eq(sa[i], pt[i]))
short_sol      = sum(1 for s in sols if len(s)<60)
copycat        = sum(1 for i in range(n) if len(sols[i])<60 and eq(sa[i], pt[i]))
gidx=[i for i in range(n) if eq(pt[i], gs[i])]; bidx=[i for i in range(n) if not eq(pt[i], gs[i])]
sok=lambda i: eq(sa[i], gs[i])
out={"task":"math","n":n,"quant":QUANT,
     "median_plan_len":int(statistics.median(len(p) for p in plans)),
     "median_sol_len":int(statistics.median(len(s) for s in sols)),
     "solver_acc":round(sum(sok(i) for i in range(n))/n,4),
     "plan_has_correct_answer":round(plan_has_ans/n,4),
     "plan_contains_boxed":round(plan_has_boxed/n,4),
     "solver_answer_equals_plan":round(solver_eq_plan/n,4),
     "solver_under_60_chars":round(short_sol/n,4),
     "copycat_rate":round(copycat/n,4),
     "solver_acc_when_plan_right":round(sum(sok(i) for i in gidx)/max(len(gidx),1),4),
     "solver_acc_when_plan_wrong":round(sum(sok(i) for i in bidx)/max(len(bidx),1),4),
     "n_plan_right":len(gidx),"n_plan_wrong":len(bidx)}
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
json.dump([{"q":qs[i],"gold":gs[i],"plan":plans[i],"sol":sols[i],"sa":sa[i],"plan_tail":pt[i]}
           for i in range(n)], open("/kaggle/working/traces_math.json","w"), indent=1)
