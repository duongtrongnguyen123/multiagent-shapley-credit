# H21 — (a) VERIFIER VÁ LỖI thay vì GIẢI LẠI  (b) PLANNER có đang GIẤU đáp án không?
# Xem docs/PREREGISTRATION.md #20 (commit TRƯỚC khi chạy).
# ĐO ĐƯỢC: mỗi khi Verifier CAN THIỆP, nó tái sử dụng 0% số của Solver (GSM8K) -> nó GIẢI LẠI.
#   Độ chính xác can thiệp ~56% ≈ độ chính xác TỰ GIẢI của model, không phải độ chính xác KIỂM.
# Ở đây: GIỮ TIỀN TỐ CỦA SOLVER BẰNG CODE (ghép chuỗi), không phụ thuộc model có nghe lời.
import os, re, csv, json, glob, statistics as st, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK="__TASK__"; N=__N__; BS=__BS__; NF=5

_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
FNAME="main_test.csv" if TASK=="gsm8k" else "math_500_test.csv"
CSV=sorted(glob.glob(f"/kaggle/input/**/{FNAME}",recursive=True),key=len)[0]
ALL=list(csv.DictReader(open(CSV))); FOLD=N//NF
print(f"TASK={TASK} {NF} fold x {FOLD}",flush=True)

tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
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
    if a is None: return None
    a=str(a).strip(); a=re.sub(r"\\[\[\]()]","",a)
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
    gold_of=lambda r:(NUM.findall(r["answer"].split("####")[-1]) or [None])[0]
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

PLAN_HIDE="Give a concise numbered plan. Do NOT compute the final answer."
PLAN_FREE="Give a concise numbered plan."
PLAN_ASK ="Give a concise numbered plan, and compute the final answer at the end."
SOLVE=f"Solve step by step. {TAIL}"
VERIFY=f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
# VÁ LỖI: chỉ viết TIẾP, không được nhắc lại phần đã đúng
PATCH=("The solution below may contain an error. Find the FIRST incorrect line. "
       "Do NOT rewrite the earlier correct lines. Write ONLY the continuation starting from that "
       f"line, using the earlier values as given. {TAIL}")
def nums(t): return set(x.replace(",","") for x in NUM.findall(t or ""))

folds=[]
for fi in range(NF):
    rows=ALL[fi*FOLD:(fi+1)*FOLD]
    qs=[q_of(r) for r in rows]; gs=[gold_of(r) for r in rows]
    acc=lambda a: round(sum(eq(x,g) for x,g in zip(a,gs))/len(gs),4)
    print(f"== FOLD {fi} ==",flush=True)
    # ---- H21b: 3 kiểu Planner ----
    ph=gen(PLAN_HIDE,qs,384); pf=gen(PLAN_FREE,qs,384); pa=gen(PLAN_ASK,qs,384)
    def implicit(p):
        b=boxed(p)
        if b is not None: return b
        m=re.findall(r"=\s*([^\n=]+?)\s*(?:$|\n)",p or "")
        if m: return m[-1].strip()
        m2=NUM.findall(p or ""); return m2[-1].replace(",","") if m2 else None
    acc_ph=acc([implicit(x) for x in ph]); acc_pf=acc([implicit(x) for x in pf]); acc_pa=acc([implicit(x) for x in pa])
    # Solver phía sau mỗi loại kế hoạch
    s_h=[pred(x) for x in gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,ph)],768)]
    s_f=[pred(x) for x in gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,pf)],768)]
    # ---- H21a: verifier chuẩn vs VÁ LỖI (dùng CHUNG lời giải từ P_hide) ----
    sols=gen(SOLVE,[f"{q}\n\nPlan:\n{p}" for q,p in zip(qs,ph)],768)
    sa=[pred(x) for x in sols]
    v_std=gen(VERIFY,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)],768)
    a_std=[pred(x) for x in v_std]
    # VÁ LỖI: model chỉ viết phần TIẾP; ta GHÉP tiền tố Solver vào bằng CODE
    v_pat=gen(PATCH,[f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,sols)],512)
    # SUA LOI: lay dap an TU CHUOI GHEP (tien to Solver + phan tiep cua Verifier),
    # dung y nghia "va loi": phan truoc GIU NGUYEN bang CODE.
    def splice(sol, pat):
        # cat tien to Solver toi dong dau tien ma Verifier nhac lai (neu co), roi noi phan va
        lines=[l for l in (sol or "").split("\n") if l.strip()]
        keep=lines[:len(lines)-1] if len(lines)>=3 else lines      # bo dong ket luan cu cua Solver
        return "\n".join(keep)+"\n"+(pat or "")
    merged=[splice(sols[i],v_pat[i]) for i in range(len(qs))]
    a_pat=[pred(merged[i]) if pred(merged[i]) is not None else sa[i] for i in range(len(qs))]
    def reuse(vtxt,stxt,qtxt):
        vv=nums(vtxt)-nums(qtxt)
        return len(vv & nums(stxt))/len(vv) if vv else None
    ru_std=[reuse(v_std[i],sols[i],qs[i]) for i in range(len(qs))]; ru_std=[x for x in ru_std if x is not None]
    ru_pat=[reuse(merged[i],sols[i],qs[i]) for i in range(len(qs))]; ru_pat=[x for x in ru_pat if x is not None]
    r={"fold":fi,"n":len(qs),
       "S":acc(sa),"V_std":acc(a_std),"V_patch":acc(a_pat),"V_none":acc(sa),
       "patch_minus_std":round(acc(a_pat)-acc(a_std),4),
       "reuse_std":round(st.median(ru_std),3) if ru_std else None,
       "reuse_patch":round(st.median(ru_pat),3) if ru_pat else None,
       "plan_acc_hide":acc_ph,"plan_acc_free":acc_pf,"plan_acc_ask":acc_pa,
       "solver_after_hide":acc(s_h),"solver_after_free":acc(s_f),
       "len_patch":int(st.median(len(x) for x in v_pat)),
       "len_std":int(st.median(len(x) for x in v_std))}
    folds.append(r); print(f"[fold {fi}] {json.dumps(r)}",flush=True)

def spread(k):
    v=[f[k] for f in folds if f[k] is not None]
    return {"mean":round(st.mean(v),4),"min":round(min(v),4),"max":round(max(v),4),
            "range":round(max(v)-min(v),4)} if v else None
out={"task":TASK,"folds":folds}
for k in ["S","V_std","V_patch","patch_minus_std","reuse_std","reuse_patch",
          "plan_acc_hide","plan_acc_free","plan_acc_ask","solver_after_hide","solver_after_free"]:
    out[k]=spread(k)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
