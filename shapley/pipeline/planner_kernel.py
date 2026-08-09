# H4 — PLANNER CÓ LÀM SOLVER NGỪNG TRÌNH BÀY KHÔNG? (thí nghiệm CÓ KIỂM SOÁT)
# Xem docs/PREREGISTRATION.md #3 phần (B).
# Quan sát CHÉO thí nghiệm (chưa kiểm soát): cùng prompt SOLVE,
#   CÓ Planner -> median 18 ký tự (sw_g15) | KHÔNG Planner -> 600 ký tự (bl_g15).
# Nhưng 2 lần chạy đó khác nhau nhiều thứ. Ở đây CHỈ bật/tắt Planner, giữ nguyên mọi thứ khác.
# 4 nhánh trên CÙNG bài:
#   NP  : không planner
#   WP  : có planner (plan nhét vào input Solver)
#   WPE : có planner NHƯNG kèm câu nhắc "vẫn phải trình bày đầy đủ"  -> cứu được không?
#   PO  : chỉ đưa plan, KHÔNG đưa đề bài lại  -> plan có tự nó đủ dùng không (kiểm tra phụ)
import os, re, csv, json, glob, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "__TASK__"
N    = __N__
BS   = __BS__

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "main_test.csv" if TASK=="gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} n={len(rows)}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx=768):
    outs=[]
    for i in range(0,len(usrs),BS):
        ch=usrs[i:i+BS]
        ps=[tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                                    tokenize=False, add_generation_prompt=True) for u in ch]
        e=tok(ps,return_tensors="pt",padding=True).to(model.device)
        with torch.no_grad():
            o=model.generate(**e,max_new_tokens=mx,do_sample=False,pad_token_id=tok.pad_token_id)
        L=e["input_ids"].shape[1]
        outs+=[tok.decode(o[j,L:],skip_special_tokens=True).strip() for j in range(len(ch))]
    print(f"   ...{len(usrs)}", flush=True)
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
SOLVE_E=(f"Solve step by step. Even if a plan is provided, you must still write out every "
         f"calculation yourself. {TAIL}")

plans=gen(PLAN,qs,320)
arms={
 "NP_no_planner":  (SOLVE,   [q for q in qs]),
 "WP_with_planner":(SOLVE,   [f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,plans)]),
 "WPE_plan_plus_reminder":(SOLVE_E,[f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,plans)]),
 "PO_plan_only":   (SOLVE,   [f"Plan:\n{p}\n\nFollow the plan and give the final answer." for p in plans]),
}
out={"task":TASK,"n":len(gs),"median_plan_len":int(statistics.median(len(p) for p in plans)),"arms":{}}
for tag,(sysm,usrs) in arms.items():
    print(f"== {tag} ==", flush=True)
    sols=gen(sysm,usrs,768)
    a=[pred(s) for s in sols]
    acc=sum(eq(x,g) for x,g in zip(a,gs))/len(gs)
    r={"solver_acc":round(acc,4),
       "median_sol_len":int(statistics.median(len(s or "") for s in sols)),   # <-- CHỈ SỐ CHÍNH
       "mean_sol_len":int(sum(len(s or "") for s in sols)/len(sols)),
       "pct_under_200":round(sum(1 for s in sols if len(s or "")<200)/len(sols),4)}
    out["arms"][tag]=r; print(f"[{tag}] {json.dumps(r)}", flush=True)

print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json","w"), indent=2)
