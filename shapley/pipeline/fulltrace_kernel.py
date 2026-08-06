# SINH TRACE ĐẦY ĐỦ 4 VAI để KIỂM TRA HỒI TỐ được mọi khẳng định.
# Lý do tồn tại: 23/26 kernel trước đây VỨT BỎ văn bản mô hình sinh ra, chỉ giữ số tổng hợp
# -> không thể kiểm lại. Đọc trace lần đầu đã lộ ngay một lỗi trích xuất (plan_tail dính "\)").
# Kernel này lưu TOÀN BỘ output của Planner/Solver/Verifier/Aggregator + mọi cờ chấm điểm.
import os, re, csv, json, glob, statistics as st, torch
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
    i=s.find("{",i); d=0; stt=i
    for j in range(i,len(s)):
        if s[j]=="{": d+=1
        elif s[j]=="}":
            d-=1
            if d==0: return s[stt+1:j]
    return None
NUM=re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def norm(a):
    """ĐÃ SỬA: bỏ cả \\( \\) \\[ \\] — lỗi này từng làm đếm hụt hơn 2 lần ở pt_m7."""
    if a is None: return None
    a=str(a).strip()
    a=re.sub(r"\\[\[\]()]","",a)
    a=re.sub(r"\\(?:mbox|textbf|mathrm|text)\s*\{([^}]*)\}",r"\1",a)
    for x in ["\\left","\\right","\\!","\\,","\\;","$"," ",",","~"]: a=a.replace(x,"")
    a=a.replace("\\dfrac","\\frac").replace("\\tfrac","\\frac")
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
PLAN="Give a concise numbered plan. Do NOT compute the final answer."
SOLVE=f"Solve step by step. {TAIL}"
VERIFY=f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
AGG=f"Given candidate solutions, decide the correct final answer. {TAIL}"

plans=gen(PLAN,qs,384)
sols =gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,plans)],768)
vers =gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)],768)
aggs =gen(AGG,[f"{q}\n\nCandidate 1:\n{s}\n\nCandidate 2:\n{v}" for q,s,v in zip(qs,sols,vers)],512)
sa=[pred(x) for x in sols]; va=[pred(x) for x in vers]; aa=[pred(x) for x in aggs]

# "đáp án ngầm" của kế hoạch — nhiều cách trích, LƯU CẢ BA để kiểm lại được
def tail_eq(p):
    m=re.findall(r"=\s*([^\n=]+?)\s*(?:$|\n)",p or ""); return m[-1].strip() if m else None
def tail_num(p):
    m=NUM.findall(p or ""); return m[-1].replace(",","") if m else None

T=[]
for i in range(len(qs)):
    T.append({"i":i,"q":qs[i],"gold":gs[i],
              "plan":plans[i],"sol":sols[i],"ver":vers[i],"agg":aggs[i],
              "sa":sa[i],"va":va[i],"aa":aa[i],
              "plan_boxed":boxed(plans[i]),"plan_tail_eq":tail_eq(plans[i]),"plan_tail_num":tail_num(plans[i]),
              "s_ok":eq(sa[i],gs[i]),"v_ok":eq(va[i],gs[i]),"a_ok":eq(aa[i],gs[i]),
              "len_plan":len(plans[i]),"len_sol":len(sols[i]),"len_ver":len(vers[i]),"len_agg":len(aggs[i])})

n=len(T)
out={"task":TASK,"n":n,
     "acc_S":round(sum(t["s_ok"] for t in T)/n,4),
     "acc_V":round(sum(t["v_ok"] for t in T)/n,4),
     "acc_A":round(sum(t["a_ok"] for t in T)/n,4),
     "median_len":{k:int(st.median(t[f"len_{k}"] for t in T)) for k in ["plan","sol","ver","agg"]},
     "V_fix":sum(1 for t in T if not t["s_ok"] and t["v_ok"]),
     "V_break":sum(1 for t in T if t["s_ok"] and not t["v_ok"]),
     "plan_boxed_rate":round(sum(1 for t in T if t["plan_boxed"] is not None)/n,4),
     "plan_has_ans_boxed":round(sum(1 for t in T if eq(t["plan_boxed"],t["gold"]))/n,4),
     "plan_has_ans_tail":round(sum(1 for t in T if eq(t["plan_tail_eq"],t["gold"]))/n,4)}
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
json.dump(T,open("/kaggle/working/traces_full.json","w"),indent=1)   # <-- BẮT BUỘC LƯU
print(f"-> traces_full.json: {n} trace ĐẦY ĐỦ 4 vai",flush=True)
