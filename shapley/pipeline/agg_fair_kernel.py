# KHỬ NHIỄU cho H2: bộ tổng hợp LLM vs BỎ PHIẾU, ĐỐI XỬ CÔNG BẰNG.
# Lần trước aggregator bị thiệt: KHÔNG có chỉ dẫn CoT + chỉ 384 token (solver có CoT + 1024).
# Lần này aggregator ĐƯỢC: cùng chỉ dẫn "step by step", CÙNG 1024 token, và thêm 2 biến thể.
# Mọi nhánh dùng CHUNG một bể k=8 mẫu -> so sánh tuyệt đối công bằng.
#   maj@k            : bỏ phiếu thuần thống kê
#   agg_fair         : LLM tổng hợp, CoT + 1024 token (khử nhiễu prompt)
#   agg_with_counts  : LLM tổng hợp NHƯNG được cho biết SỐ PHIẾU mỗi đáp án
#                      -> nếu vẫn đè lên đa số dù BIẾT phiếu, đó là bằng chứng rất mạnh
#   agg_full_sol     : LLM tổng hợp khi thấy TOÀN VĂN 3 lời giải (không chỉ đáp án)
import os, re, csv, json, glob, torch
from collections import Counter

N = __N__
BS = __BS__
K = 8
QUANT = __QUANT__

if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])
from transformers import AutoModelForCausalLM, AutoTokenizer

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True) or \
     glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
print(f"MODEL={MODEL} n={len(rows)}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
if QUANT:
    from transformers import BitsAndBytesConfig
    _b = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=_b, device_map="auto").eval()
else:
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto").eval()
print("model loaded", flush=True)

def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0: return None
    i = s.find("{", i); d = 0; st = i
    for j in range(i, len(s)):
        if s[j] == "{": d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0: return s[st+1:j]
    return None
def norm(a):
    if a is None: return None
    a = str(a).strip()
    for x in ["\\left","\\right","\\!","\\,","\\;","$"," "]: a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a); a = a.replace("\\dfrac","\\frac").replace("\\tfrac","\\frac")
    return a.rstrip(".").strip("{}").lower()
def eq(p,g):
    p,g = norm(p),norm(g)
    if not p or not g: return False
    if p==g: return True
    try: return abs(float(p)-float(g))<1e-6
    except: return False
def pred(t):
    b = boxed(t)
    if b is not None: return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I); return m[-1].strip() if m else None

qs = [r["Question"] for r in rows]; gs = [boxed(r["Answer"]) for r in rows]
SOLVE = "Solve the problem step by step. Put the final answer in \\boxed{}."
def chat(s,u): return tok.apply_chat_template([{"role":"system","content":s},{"role":"user","content":u}],
                                              tokenize=False, add_generation_prompt=True)
def gen(sysm, usrs, mx):
    outs=[]
    for i in range(0,len(usrs),BS):
        ch=usrs[i:i+BS]
        e=tok([chat(sysm,u) for u in ch],return_tensors="pt",padding=True).to(model.device)
        with torch.no_grad():
            o=model.generate(**e,max_new_tokens=mx,do_sample=False,pad_token_id=tok.pad_token_id)
        L=e["input_ids"].shape[1]
        outs+= [tok.decode(o[j,L:],skip_special_tokens=True).strip() for j in range(len(ch))]
    print(f"   ...{len(usrs)} xong", flush=True)
    return outs

# ---------- bể K=8 mẫu, dùng chung mọi nhánh ----------
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
    print(f"  sampled {i+len(ch)}/{len(qs)}", flush=True)
ans = [[pred(s) for s in sl] for sl in sols]

def majority(c):
    ks=[norm(x) for x in c if norm(x)]
    if not ks: return None,0
    k,cnt=Counter(ks).most_common(1)[0]
    for x in c:
        if norm(x)==k: return x,cnt
    return None,0
maj8=[majority(a)[0] for a in ans]
out={"n":len(gs),"K":K,
     "greedy_proxy":round(sum(eq(a[0],g) for a,g in zip(ans,gs))/len(gs),4),
     "maj@8":round(sum(eq(m,g) for m,g in zip(maj8,gs))/len(gs),4),
     "oracle@8":round(sum(any(eq(c,g) for c in a) for a,g in zip(ans,gs))/len(gs),4),
     "arms":{}}
print("maj@8 =", out["maj@8"], "| oracle@8 =", out["oracle@8"], flush=True)

# CÙNG chỉ dẫn CoT + CÙNG 1024 token như solver -> công bằng
AGG_FAIR = ("You are given candidate answers to a math problem. Reason step by step about which "
            "is correct, then put the final answer in \\boxed{}.")
def cand_list(i): return "\n".join(f"{r+1}. {ans[i][r]}" for r in range(K))
def cand_counts(i):
    c=Counter(norm(x) for x in ans[i] if norm(x))
    disp=[]
    for k,v in c.most_common():
        orig=next((x for x in ans[i] if norm(x)==k), k)
        disp.append(f"{orig}  ({v}/{K} samples agree)")
    return "\n".join(disp)
def cand_full(i): return "\n\n".join(f"--- Candidate {r+1} ---\n{sols[i][r][:900]}" for r in range(3))

arms = {
 "agg_fair":        (AGG_FAIR, [f"{qs[i]}\n\nCandidate answers:\n{cand_list(i)}" for i in range(len(qs))], 1024),
 "agg_with_counts": (AGG_FAIR, [f"{qs[i]}\n\nCandidate answers with vote counts:\n{cand_counts(i)}" for i in range(len(qs))], 1024),
 "agg_full_sol":    (AGG_FAIR, [f"{qs[i]}\n\n{cand_full(i)}" for i in range(len(qs))], 1024),
}
for tag,(sysm,usrs,mx) in arms.items():
    print(f"== {tag} ==", flush=True)
    o=gen(sysm,usrs,mx); a=[pred(t) for t in o]
    acc=sum(eq(x,g) for x,g in zip(a,gs))/len(gs)
    brk=sum(1 for i in range(len(gs)) if eq(maj8[i],gs[i]) and not eq(a[i],gs[i]))
    fx =sum(1 for i in range(len(gs)) if not eq(maj8[i],gs[i]) and eq(a[i],gs[i]))
    agree=sum(1 for i in range(len(gs)) if norm(a[i])==norm(maj8[i]))
    r={"acc":round(acc,4),"vs_maj":round(acc-out["maj@8"],4),
       "breaks_majority":brk,"fixes_majority":fx,
       "agrees_with_majority":agree,
       "agree_rate":round(agree/len(gs),4)}
    out["arms"][tag]=r
    print(f"[{tag}] {json.dumps(r)}", flush=True)

print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json","w"), indent=2)
