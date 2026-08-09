# H7 — CHE GIÁ TRỊ TRUNG GIAN CÓ CỨU ĐƯỢC VAI AGGREGATOR KHÔNG? (tổng quát hoá sang vai thứ 2)
# Xem docs/PREREGISTRATION.md #6 (commit TRƯỚC khi chạy).
# ĐO ĐƯỢC ở vai VERIFIER (cp_g15): che hết số -> TỐT NHẤT (+8.4), hơn chỉ-đáp-án (+7.6),
#   hơn chỉ-phép-tính (+6.4), hơn nguyên văn (+5.6). Đơn điệu theo lượng số nhìn thấy.
# ĐO ĐƯỢC ở vai AGGREGATOR (agf_15): cho xem TOÀN VĂN là nhánh TỆ NHẤT (-17.5 so với bỏ phiếu).
# Nếu cơ chế "giá trị trung gian neo model lại" là đúng và TỔNG QUÁT, che số phải cứu được aggregator.
import os, re, csv, json, glob, torch
from collections import Counter
from transformers import AutoModelForCausalLM, AutoTokenizer

N=__N__; BS=__BS__; K=8; QUANT=__QUANT__
if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])

_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True) or \
   glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True)
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

qs=[r["Question"] for r in rows]; gs=[boxed(r["Answer"]) for r in rows]
SOLVE="Solve the problem step by step. Put the final answer in \\boxed{}."
def chat(s,u): return tok.apply_chat_template([{"role":"system","content":s},{"role":"user","content":u}],
                                              tokenize=False,add_generation_prompt=True)
def gen(sysm,usrs,mx):
    outs=[]
    for i in range(0,len(usrs),BS):
        ch=usrs[i:i+BS]
        e=tok([chat(sysm,u) for u in ch],return_tensors="pt",padding=True).to(model.device)
        with torch.no_grad():
            o=model.generate(**e,max_new_tokens=mx,do_sample=False,pad_token_id=tok.pad_token_id)
        L=e["input_ids"].shape[1]
        outs+=[tok.decode(o[j,L:],skip_special_tokens=True).strip() for j in range(len(ch))]
    print(f"   ...{len(usrs)}",flush=True)
    return outs

def mask_values(s):
    """CHE mọi giá trị trung gian, giữ cấu trúc suy luận (giống W_prose của cp_g15)."""
    out=[]
    for ln in (s or "").split("\n"):
        t=re.sub(r"\\boxed\s*\{[^}]*\}","<value>",ln)
        t=NUM.sub("<num>",t)
        t=re.sub(r"\s+"," ",t).strip()
        if len(t)>8: out.append(t)
    return "\n".join(out) or "(no reasoning)"

# ---- bể K=8 mẫu dùng chung ----
sols=[[] for _ in qs]
for i in range(0,len(qs),BS):
    ch=qs[i:i+BS]
    e=tok([chat(SOLVE,q) for q in ch],return_tensors="pt",padding=True).to(model.device)
    with torch.no_grad():
        o=model.generate(**e,max_new_tokens=1024,do_sample=True,temperature=0.8,top_p=0.95,
                         num_return_sequences=K,pad_token_id=tok.pad_token_id)
    L=e["input_ids"].shape[1]
    for j in range(len(ch)):
        for r in range(K): sols[i+j].append(tok.decode(o[j*K+r,L:],skip_special_tokens=True).strip())
    print(f"  sampled {i+len(ch)}/{len(qs)}",flush=True)
ans=[[pred(s) for s in sl] for sl in sols]

def majority(c):
    ks=[norm(x) for x in c if norm(x)]
    if not ks: return None,0
    k,_=Counter(ks).most_common(1)[0]
    for x in c:
        if norm(x)==k: return x,0
    return None,0
maj8=[majority(a)[0] for a in ans]
out={"n":len(gs),"K":K,
     "maj@8":round(sum(eq(m,g) for m,g in zip(maj8,gs))/len(gs),4),
     "oracle@8":round(sum(any(eq(c,g) for c in a) for a,g in zip(ans,gs))/len(gs),4),"arms":{}}
print("maj@8 =",out["maj@8"],"oracle@8 =",out["oracle@8"],flush=True)

AGG=("You are given candidate answers to a math problem. Reason step by step about which "
     "is correct, then put the final answer in \\boxed{}.")
NSHOW=3   # số ứng viên hiển thị toàn văn (giữ context vừa phải)
views={
 "A_answers":[f"{qs[i]}\n\nCandidate answers:\n" + "\n".join(f"{r+1}. {ans[i][r]}" for r in range(K))
              for i in range(len(qs))],
 "A_full":   [f"{qs[i]}\n\n" + "\n\n".join(f"--- Candidate {r+1} ---\n{sols[i][r][:900]}"
              for r in range(NSHOW)) for i in range(len(qs))],
 "A_masked": [f"{qs[i]}\n\n" + "\n\n".join(f"--- Candidate {r+1} (values hidden) ---\n"
              f"{mask_values(sols[i][r][:900])}\nFinal answer: {ans[i][r]}" for r in range(NSHOW))
              for i in range(len(qs))],
}
for tag,usrs in views.items():
    print(f"== {tag} ==",flush=True)
    a=[pred(t) for t in gen(AGG,usrs,1024)]
    acc=sum(eq(x,g) for x,g in zip(a,gs))/len(gs)
    r={"acc":round(acc,4),"vs_maj":round(acc-out["maj@8"],4),
       "breaks_majority":sum(1 for i in range(len(gs)) if eq(maj8[i],gs[i]) and not eq(a[i],gs[i])),
       "fixes_majority":sum(1 for i in range(len(gs)) if not eq(maj8[i],gs[i]) and eq(a[i],gs[i])),
       "agree_rate":round(sum(1 for i in range(len(gs)) if norm(a[i])==norm(maj8[i]))/len(gs),4),
       "median_ctx_chars":int(sorted(len(u) for u in usrs)[len(usrs)//2])}
    out["arms"][tag]=r; print(f"[{tag}] {json.dumps(r)}",flush=True)

print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
