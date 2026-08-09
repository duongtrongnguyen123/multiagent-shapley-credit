# H35 (pre-reg #40) — BO KIEM DUNG DAN (chay test) vs LLM-KIEM, CUNG NGAN SACH 4 LUOT.
import os, re, csv, json, glob, subprocess, tempfile, statistics as st, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N=__N__; BS=__BS__; QUANT=__QUANT__; NF=5; TIMEOUT=8
if QUANT:
    import sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"],check=False)
_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True) or \
   glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
CSV=sorted(glob.glob("/kaggle/input/**/test.csv",recursive=True),key=len)[0]
rows=list(csv.DictReader(open(CSV)))[:N]
print(f"HumanEval n={len(rows)} MODEL={MODEL}",flush=True)
tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
if QUANT:
    from transformers import BitsAndBytesConfig
    _b=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    model=AutoModelForCausalLM.from_pretrained(MODEL,quantization_config=_b,device_map="auto").eval()
else:
    model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="auto").eval()

TOK={}
def gen(sysm,us,mx,temp,who):
    outs=[];ntok=0
    for i in range(0,len(us),BS):
        ch=us[i:i+BS]
        ps=[tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
            tokenize=False,add_generation_prompt=True) for u in ch]
        e=tok(ps,return_tensors="pt",padding=True).to("cuda")
        with torch.no_grad():
            o=model.generate(**e,max_new_tokens=mx,do_sample=(temp>0),temperature=max(temp,1e-5),
                             top_p=0.95,pad_token_id=tok.pad_token_id)
        L=e["input_ids"].shape[1]
        for j in range(len(ch)):
            g=o[j,L:]; ntok+=int((g!=tok.pad_token_id).sum())
            outs.append(tok.decode(g,skip_special_tokens=True).strip())
        del e,o; torch.cuda.empty_cache()
    TOK[who]=TOK.get(who,0)+ntok
    return outs

def extract(t):
    m=re.findall(r"```(?:python)?\s*\n(.*?)```",t or "",re.S)
    return (m[0] if m else (t or "")).strip()
def run_tests(code,test,entry):
    prog=f"{code}\n\n{test}\n\ncheck({entry})\n"
    with tempfile.NamedTemporaryFile("w",suffix=".py",delete=False) as f:
        f.write(prog); path=f.name
    try:
        r=subprocess.run(["python",path],capture_output=True,text=True,timeout=TIMEOUT)
        return r.returncode==0, (r.stderr or "")[-400:]
    except Exception as ex: return False, f"{type(ex).__name__}: {str(ex)[:200]}"
    finally:
        try: os.unlink(path)
        except Exception: pass
def runnable(code):
    """cu phap chay duoc? (nguong hieu luc .50 nhu H8)"""
    try:
        compile(code,"<s>","exec"); return True
    except Exception: return False

SOLVE=("Complete the Python function. Return the COMPLETE function including the signature, "
       "inside a ```python code block. No explanation.")
FIXE =("The code below FAILED its tests. Here is the error. Fix the code. "
       "Return the COMPLETE corrected function inside a ```python code block.")
FIXL =("Review the code below for correctness. If it is wrong, fix it. "
       "Return the COMPLETE function inside a ```python code block.")

folds=[]; FOLD=len(rows)//NF
for fi in range(NF):
    R=rows[fi*FOLD:(fi+1)*FOLD]
    P=[r["prompt"] for r in R]; T=[r["test"] for r in R]; E=[r["entry_point"] for r in R]
    score=lambda C: round(sum(run_tests(C[i],T[i],E[i])[0] for i in range(len(R)))/len(R),4)
    print(f"== fold {fi} ==",flush=True)
    base=[extract(x) for x in gen(SOLVE,P,512,0.0,"greedy1")]
    a_g=score(base)
    # maj@4: bo phieu theo code chuan hoa
    C4=[[extract(x) for x in gen(SOLVE,P,512,0.8,"maj4")] for _ in range(4)]
    a_mj=[]
    for i in range(len(R)):
        c={}
        for r_ in range(4):
            k=re.sub(r"\s+","",C4[r_][i])
            c[k]=c.get(k,(0,None)); c[k]=(c[k][0]+1,C4[r_][i])
        a_mj.append(max(c.values(),key=lambda x:x[0])[1])
    # exec3: 3 vong sua dua tren KET QUA CHAY TEST
    cur=list(base)
    for rd in range(3):
        need=[]; 
        for i in range(len(R)):
            okk,err=run_tests(cur[i],T[i],E[i])
            if not okk: need.append((i,err))
        if not need: break
        fx=gen(FIXE,[f"{P[i]}\n\nCode:\n```python\n{cur[i]}\n```\n\nError:\n{err}" for i,err in need],512,0.0,"exec3")
        for k,(i,_) in enumerate(need): cur[i]=extract(fx[k])
    exec3=list(cur)
    # llm3: 3 vong sua dua tren NHAN XET LLM (khong chay test)
    cur=list(base)
    for rd in range(3):
        fx=gen(FIXL,[f"{P[i]}\n\nCode:\n```python\n{cur[i]}\n```" for i in range(len(R))],512,0.0,"llm3")
        cur=[extract(x) for x in fx]
    llm3=list(cur)
    def breaks(new):
        return sum(1 for i in range(len(R))
                   if run_tests(base[i],T[i],E[i])[0] and not run_tests(new[i],T[i],E[i])[0])
    r={"fold":fi,"n":len(R),"greedy1":a_g,"maj4":score(a_mj),"exec3":score(exec3),"llm3":score(llm3),
       "exec3_minus_llm3":round(score(exec3)-score(llm3),4),
       "exec3_minus_maj4":round(score(exec3)-score(a_mj),4),
       "breaks_exec3":breaks(exec3),"breaks_llm3":breaks(llm3),
       "exec_success_rate":round(sum(runnable(c) for c in base)/len(R),4)}
    folds.append(r); print(f"[fold {fi}] {json.dumps(r)}",flush=True)

def sp(k):
    v=[f[k] for f in folds]
    return {"mean":round(st.mean(v),4),"min":round(min(v),4),"max":round(max(v),4),
            "pos":sum(1 for x in v if x>0)}
out={"task":"humaneval","n":len(rows),"quant":QUANT,"folds":folds,"tokens":TOK}
for k in ["greedy1","maj4","exec3","llm3","exec3_minus_llm3","exec3_minus_maj4",
          "breaks_exec3","breaks_llm3","exec_success_rate"]: out[k]=sp(k)
out["VALID_exec"]=bool(out["exec_success_rate"]["mean"]>=0.50)   # nguong H8 da khoa
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
