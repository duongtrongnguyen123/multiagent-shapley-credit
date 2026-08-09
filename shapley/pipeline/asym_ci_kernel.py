# H15 — KẾT QUẢ DƯƠNG MẠNH NHẤT CỦA DỰ ÁN CÓ SỐNG SÓT KHI CÓ THANH SAI SỐ KHÔNG?
# Xem docs/PREREGISTRATION.md #14 (commit TRƯỚC khi chạy).
# Khẳng định cần kiểm: "Solver 1.5B + Verifier 7B post-hoc = +18 điểm, 9 sửa / 0 phá" — đo MỘT LẦN, n=50.
# Sàn nhiễu (H13) cho thấy ở n=100 V_gain trải 7 điểm; ở n=50 còn rộng hơn.
# Ở đây: 5 fold rời nhau x 60 bài MATH. Cả 2 model đồng thời trên GPU (1.5B fp16 + 7B nf4 < 16GB).
import os, re, csv, json, glob, statistics as st, torch

N=__N__; BS=__BS__; NF=5
import subprocess, sys
subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

M15=os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors",recursive=True),key=len)[0])
M7 =os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True),key=len)[0])
CSV=sorted(glob.glob("/kaggle/input/**/math_500_test.csv",recursive=True),key=len)[0]
ALL=list(csv.DictReader(open(CSV))); FOLD=N//NF
print(f"M15={M15}\nM7={M7}\n{NF} fold x {FOLD} bai",flush=True)

t15=AutoTokenizer.from_pretrained(M15); t15.padding_side="left"
if t15.pad_token is None: t15.pad_token=t15.eos_token
t7=AutoTokenizer.from_pretrained(M7); t7.padding_side="left"
if t7.pad_token is None: t7.pad_token=t7.eos_token
small=AutoModelForCausalLM.from_pretrained(M15,torch_dtype=torch.float16,device_map="auto").eval()
print("1.5B loaded",flush=True)
_b=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
                      bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
big=AutoModelForCausalLM.from_pretrained(M7,quantization_config=_b,device_map="auto").eval()
print("7B loaded | VRAM MiB:",round(torch.cuda.memory_allocated()/1048576),flush=True)

def gen(model,tk,sysm,usrs,mx=768):
    outs=[]
    for i in range(0,len(usrs),BS):
        ch=usrs[i:i+BS]
        ps=[tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                                   tokenize=False,add_generation_prompt=True) for u in ch]
        e=tk(ps,return_tensors="pt",padding=True).to(model.device)
        with torch.no_grad():
            o=model.generate(**e,max_new_tokens=mx,do_sample=False,pad_token_id=tk.pad_token_id)
        L=e["input_ids"].shape[1]
        outs+=[tk.decode(o[j,L:],skip_special_tokens=True).strip() for j in range(len(ch))]
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
def norm(a):
    if a is None: return None
    a=str(a).strip()
    for x in ["\\left","\\right","\\!","\\,","\\;","$"," "]: a=a.replace(x,"")
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

SOLVE="Solve step by step. Put the final answer in \\boxed{}."
VERIFY="Check the proposed solution step by step; if wrong, correct it. Put the final answer in \\boxed{}."

folds=[]
for fi in range(NF):
    rows=ALL[fi*FOLD:(fi+1)*FOLD]
    qs=[r["Question"] for r in rows]; gs=[boxed(r["Answer"]) for r in rows]
    acc=lambda a: round(sum(eq(x,g) for x,g in zip(a,gs))/len(gs),4)
    print(f"== FOLD {fi} (n={len(qs)}) ==",flush=True)
    sols=gen(small,t15,SOLVE,qs,768); sa=[pred(s) for s in sols]
    s_ok=[eq(a,g) for a,g in zip(sa,gs)]
    up=[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)]
    a15=[pred(v) for v in gen(small,t15,VERIFY,up,768)]
    a7 =[pred(v) for v in gen(big,  t7, VERIFY,up,768)]
    def fb(av):
        v_ok=[eq(x,g) for x,g in zip(av,gs)]
        return (sum(1 for i in range(len(gs)) if not s_ok[i] and v_ok[i]),
                sum(1 for i in range(len(gs)) if s_ok[i] and not v_ok[i]))
    f15,b15=fb(a15); f7,b7=fb(a7)
    r={"fold":fi,"n":len(qs),"solo":acc(sa),"V15":acc(a15),"V7":acc(a7),
       "V15_gain":round(acc(a15)-acc(sa),4),"V7_gain":round(acc(a7)-acc(sa),4),
       "V7_minus_V15":round(acc(a7)-acc(a15),4),
       "fix15":f15,"break15":b15,"fix7":f7,"break7":b7}
    folds.append(r); print(f"[fold {fi}] {json.dumps(r)}",flush=True)

def spread(k):
    v=[f[k] for f in folds]
    return {"mean":round(st.mean(v),4),"min":round(min(v),4),"max":round(max(v),4),
            "range":round(max(v)-min(v),4),"std":round(st.pstdev(v),4)}
out={"task":"math","n_folds":NF,"fold_n":FOLD,"folds":folds,
     "solo":spread("solo"),"V15":spread("V15"),"V7":spread("V7"),
     "V15_gain":spread("V15_gain"),"V7_gain":spread("V7_gain"),
     "V7_minus_V15":spread("V7_minus_V15"),
     "total_fix7":sum(f["fix7"] for f in folds),"total_break7":sum(f["break7"] for f in folds),
     "total_fix15":sum(f["fix15"] for f in folds),"total_break15":sum(f["break15"] for f in folds)}
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
