# H3 — VERIFY CÓ CỔNG LỌC: tách "KHI NÀO can thiệp" khỏi "can thiệp THẾ NÀO".
# Xem docs/PREREGISTRATION.md #3 (commit TRƯỚC khi chạy).
# Đo được ở bl_g15: B(blind) 42 sửa/23 phá — sản lượng cao rủi ro cao;
#                   P(giấu đáp án) 15 sửa/1 phá — rủi ro cực thấp.
# => Dùng P làm CỔNG (chỉ hỏi có lỗi không, KHÔNG cho thấy đáp án), chỉ khi cổng kêu YES
#    mới cho B giải lại. Kỳ vọng: sửa gần B, phá gần P.
# Nhánh: N (không verify) | I (informed) | B (blind) | G (có cổng)
import os, re, csv, json, glob, statistics, torch

TASK  = "__TASK__"
N     = __N__
BS    = __BS__

from transformers import AutoModelForCausalLM, AutoTokenizer
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "main_test.csv" if TASK == "gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} MODEL={MODEL} n={len(rows)}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="cuda").eval()
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
    fmt_ans=lambda a:f"The answer is {a}."
else:
    gold_of=lambda r: boxed(r["Answer"])
    def pred(t):
        b=boxed(t)
        if b is not None: return b
        m=re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)",t or "",re.I); return m[-1].strip() if m else None
    q_of=lambda r:r["Question"]; TAIL="Put the final answer in \\boxed{}."
    fmt_ans=lambda a:f"The answer is \\boxed{{{a}}}."

qs=[q_of(r) for r in rows]; gs=[gold_of(r) for r in rows]
SOLVE=f"Solve step by step. {TAIL}"
VERIFY=f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
# CỔNG: chỉ phán CÓ LỖI hay KHÔNG, và KHÔNG được thấy đáp án cuối
GATE=("You are shown a partial worked solution with its final answer removed. "
      "Decide only whether the REASONING contains a mistake. Reply exactly one word: YES or NO. "
      "YES means there is a mistake.")

def strip_answer(s):
    if not s: return "(no reasoning)"
    t=re.split(r"(?i)the answer is",s)[0]
    t=re.sub(r"\\boxed\s*\{[^}]*\}","(redacted)",t)
    return t.strip() or "(no reasoning)"

sols=gen(SOLVE,qs,768)
sa=[pred(s) for s in sols]; s_ok=[eq(a,g) for a,g in zip(sa,gs)]
n_cor=sum(s_ok); base=n_cor/len(gs)
print(f"[N no-verify] acc={base:.4f}", flush=True)
out={"task":TASK,"n":len(gs),"solver_acc":round(base,4),"solver_correct":n_cor,
     "median_sol_len":int(statistics.median(len(s or "") for s in sols)),"arms":{}}

def score(va,tag,extra=None):
    v_ok=[eq(a,g) for a,g in zip(va,gs)]
    brk=sum(1 for i in range(len(gs)) if s_ok[i] and not v_ok[i])
    fix=sum(1 for i in range(len(gs)) if not s_ok[i] and v_ok[i])
    r={"verifier_acc":round(sum(v_ok)/len(gs),4),
       "value_added":round(sum(v_ok)/len(gs)-base,4),
       "fixes":fix,"breaks":brk,
       "changed_answer":sum(1 for i in range(len(gs)) if norm(va[i])!=norm(sa[i]))}
    if extra: r.update(extra)
    out["arms"][tag]=r; print(f"[{tag}] {json.dumps(r)}", flush=True)

# I informed
score([pred(v) for v in gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)],768)],"I_informed")
# B blind
vb=[pred(v) for v in gen(VERIFY,[f"{q}\n\nProposed solution:\n{fmt_ans(a)}" for q,a in zip(qs,sa)],768)]
score(vb,"B_blind")
# G gated: cổng P quyết định, chỉ ca bị kêu YES mới lấy đáp án của B
gate_out=gen(GATE,[f"{q}\n\nPartial solution (final answer removed):\n{strip_answer(s)}"
                   for q,s in zip(qs,sols)],8)
flag=[t.strip().upper().startswith("YES") for t in gate_out]
vg=[vb[i] if flag[i] else sa[i] for i in range(len(gs))]
n_flag=sum(flag)
gate_prec=sum(1 for i in range(len(gs)) if flag[i] and not s_ok[i])/max(n_flag,1)
gate_rec=sum(1 for i in range(len(gs)) if flag[i] and not s_ok[i])/max(len(gs)-n_cor,1)
score(vg,"G_gated",{"gate_flag_rate":round(n_flag/len(gs),4),
                    "gate_precision":round(gate_prec,4),   # bị kêu -> THỰC SỰ sai bao nhiêu %
                    "gate_recall":round(gate_rec,4),
                    "n_flagged":n_flag})

print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json","w"), indent=2)
