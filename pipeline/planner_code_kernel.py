# H22 — BỎ CHỈ DẪN CẤM CỦA PLANNER: có chuyển sang MIỀN CODE không?
# Xem docs/PREREGISTRATION.md #21. Chấm bằng CHẠY TEST THẬT (chân lý chính xác, không phải grader xấp xỉ).
# ĐO ĐƯỢC ở toán (H21b): bỏ "Do NOT compute" -> Solver tốt hơn +3.75 (MATH 5/5) / +3.25 (GSM8K 4/5).
import os, re, csv, json, glob, subprocess, tempfile, signal, statistics as st, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N=__N__; BS=__BS__; NF=5; TIMEOUT=8
_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
CSV=sorted(glob.glob("/kaggle/input/**/test.csv",recursive=True),key=len)[0]
ALL=list(csv.DictReader(open(CSV)))[:N]; FOLD=len(ALL)//NF
print(f"HumanEval n={len(ALL)} | {NF} fold x {FOLD}",flush=True)

tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="auto").eval()
print("model loaded",flush=True)

def gen(sysm,usrs,mx=512):
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
    return outs

def extract(t):
    m=re.findall(r"```(?:python)?\s*\n(.*?)```",t or "",re.S)
    return (m[0] if m else (t or "")).strip()
class TO(Exception): pass
def _h(s,f): raise TO()
def run_tests(code,test,entry):
    prog=f"{code}\n\n{test}\n\ncheck({entry})\n"
    with tempfile.NamedTemporaryFile("w",suffix=".py",delete=False) as f:
        f.write(prog); path=f.name
    try:
        r=subprocess.run(["python",path],capture_output=True,text=True,timeout=TIMEOUT)
        return r.returncode==0
    except Exception: return False
    finally:
        try: os.unlink(path)
        except Exception: pass

# 3 kiểu Planner: CẤM viết code / KHÔNG cấm / YÊU CẦU viết luôn
P_HIDE="Give a concise numbered plan for implementing this function. Do NOT write the code."
P_FREE="Give a concise numbered plan for implementing this function."
P_ASK ="Give a concise numbered plan, then write the implementation."
SOLVE=("Complete the Python function. Return the COMPLETE function including the signature, "
       "inside a ```python code block. No explanation.")

folds=[]
for fi in range(NF):
    rows=ALL[fi*FOLD:(fi+1)*FOLD]
    prompts=[r["prompt"] for r in rows]; tests=[r["test"] for r in rows]; ents=[r["entry_point"] for r in rows]
    def score(codes): return round(sum(run_tests(codes[i],tests[i],ents[i]) for i in range(len(rows)))/len(rows),4)
    print(f"== FOLD {fi} (n={len(rows)}) ==",flush=True)
    # NoP: không planner
    nop=[extract(t) for t in gen(SOLVE,prompts,512)]
    r={"fold":fi,"n":len(rows),"NoP":score(nop)}
    for tag,psys in [("P_hide",P_HIDE),("P_free",P_FREE),("P_ask",P_ASK)]:
        plans=gen(psys,prompts,384)
        codes=[extract(t) for t in gen(SOLVE,[f"{p}\n\nPlan:\n{pl}" for p,pl in zip(prompts,plans)],512)]
        r[tag]=score(codes)
        r[f"len_{tag}"]=int(st.median(len(x) for x in plans))
        r[f"planCode_{tag}"]=round(sum(1 for x in plans if "```" in x or "def " in x)/len(plans),3)
    r["free_minus_hide"]=round(r["P_free"]-r["P_hide"],4)
    r["ask_minus_hide"]=round(r["P_ask"]-r["P_hide"],4)
    folds.append(r); print(f"[fold {fi}] {json.dumps(r)}",flush=True)

def spread(k):
    v=[f[k] for f in folds]
    return {"mean":round(st.mean(v),4),"min":round(min(v),4),"max":round(max(v),4),
            "pos_folds":sum(1 for x in v if x>0)}
out={"task":"humaneval","folds":folds}
for k in ["NoP","P_hide","P_free","P_ask","free_minus_hide","ask_minus_hide",
          "planCode_P_hide","planCode_P_free","planCode_P_ask"]:
    out[k]=spread(k)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
