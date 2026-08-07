# STRUCTURED-COMMUNICATION trên MATH-500: agent reason tự do rồi kết bằng 1 JSON ở cuối;
# agent sau ĐỌC FIELD (plan/steps/answer/checks) thay vì nuốt cả đoạn text.
# Đo: accuracy + tỉ lệ JSON hợp lệ mỗi agent (1.5B có tuân format nổi không?) + fix/break của Verifier.
import os, re, csv, json, glob, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N = __N__
QUANT = __QUANT__
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True) or glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token

model = None
if QUANT:
    try:
        import subprocess, sys
        subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"], check=True)
        from transformers import BitsAndBytesConfig
        _bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                  bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
        model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=_bnb, device_map="auto").eval()
        print("LOADED 4bit", flush=True)
    except Exception as e:
        print("4bit FAILED -> fp16 offload:", repr(e)[:200], flush=True); model = None
if model is None:
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto").eval()
    print("LOADED fp16", flush=True)

def gen(sys, usr, mx=1024):
    p = tok.apply_chat_template([{"role":"system","content":sys},{"role":"user","content":usr}],
                                tokenize=False, add_generation_prompt=True)
    e = tok(p, return_tensors="pt").to(model.device)
    o = model.generate(**e, max_new_tokens=mx, do_sample=False, pad_token_id=tok.pad_token_id)
    return tok.decode(o[0, e["input_ids"].shape[1]:], skip_special_tokens=True).strip()

# --- bóc JSON cuối cùng hợp lệ trong text (reason tự do + JSON ở cuối) ---
def last_json(t):
    if not t: return None
    end = t.rfind("}")
    while end != -1:
        d = 0
        for k in range(end, -1, -1):
            if t[k] == "}": d += 1
            elif t[k] == "{":
                d -= 1
                if d == 0:
                    try: return json.loads(t[k:end+1])
                    except Exception: break
        end = t.rfind("}", 0, end)
    return None

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
    for x in ["\\left","\\right","\\!","\\,","\\;","$"," "]: a=a.replace(x,"")
    a=re.sub(r"\\text\s*\{([^}]*)\}",r"\1",a); a=a.replace("\\dfrac","\\frac").replace("\\tfrac","\\frac")
    return a.rstrip(".").strip("{}").lower()
def eq(p,g):
    p,g=norm(p),norm(g)
    if not p or not g: return False
    if p==g: return True
    try: return abs(float(p)-float(g))<1e-6
    except: return False
def raw_ans(t):  # fallback khi JSON hỏng
    b=boxed(t)
    if b is not None: return b
    m=re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)",t or "",re.I); return m[-1].strip() if m else None
def field_ans(j, raw):
    if isinstance(j,dict) and str(j.get("answer","")).strip() not in ("","None"):
        return str(j["answer"]).strip()
    return raw_ans(raw)

PLAN_SYS=('Reason briefly, then on the FINAL line output ONLY a JSON object: '
          '{"plan": ["short step description", ...]}. Do NOT compute the final answer.')
SOLVE_SYS=('Solve the problem, reasoning step by step. Then on the FINAL line output ONLY a JSON object: '
           '{"steps": [{"n": 1, "work": "what you did", "result": "value"}, ...], "answer": "FINAL answer only (number or expression, as it would go in \\boxed{})"}.')
VERIFY_SYS=('You are a verifier. You are given the problem and the solver\'s numbered steps. '
            'Check EACH step by its number. Then on the FINAL line output ONLY a JSON object: '
            '{"checks": [{"n": <step number>, "ok": true or false, "fix": "corrected value or empty"}, ...], '
            '"answer": "final corrected answer only"}. Do NOT re-solve from scratch; point to the specific wrong step.')
AGG_SYS=('You are given candidate answers with the verifier\'s per-step checks. '
         'Decide the single correct final answer. On the FINAL line output ONLY a JSON object: {"answer": "final answer only"}.')

def fmt_plan(j):
    if isinstance(j,dict) and isinstance(j.get("plan"),list):
        return "\n".join(f"- {s}" for s in j["plan"][:12])
    return ""
def fmt_steps(j):
    if isinstance(j,dict) and isinstance(j.get("steps"),list):
        return "\n".join(f"Step {s.get('n','?')}: {s.get('work','')} = {s.get('result','')}" for s in j["steps"][:20])
    return "(no structured steps)"
def fmt_checks(j):
    if isinstance(j,dict) and isinstance(j.get("checks"),list):
        return "\n".join(f"Step {c.get('n','?')}: {'OK' if c.get('ok') else 'WRONG -> '+str(c.get('fix',''))}" for c in j["checks"][:20])
    return ""

vj={"plan":0,"solve":0,"verify":0,"agg":0}   # đếm JSON hợp lệ
cor=0; vfix=0; vbreak=0
for r in rows:
    q=r["Question"]; g=boxed(r["Answer"])
    # Planner
    pt=gen(PLAN_SYS,q,384); pj=last_json(pt); vj["plan"]+=isinstance(pj,dict)
    # Solver
    st=gen(SOLVE_SYS,q+"\n\nPlan:\n"+fmt_plan(pj)); sj=last_json(st); vj["solve"]+=isinstance(sj,dict)
    sa=field_ans(sj,st)
    # Verifier ĐỌC steps của Solver
    vt=gen(VERIFY_SYS,q+"\n\nSolver steps:\n"+fmt_steps(sj)+f"\n\nSolver answer: {sa}")
    vjson=last_json(vt); vj["verify"]+=isinstance(vjson,dict); va=field_ans(vjson,vt)
    if not eq(sa,g) and eq(va,g): vfix+=1
    if eq(sa,g) and not eq(va,g): vbreak+=1
    # Aggregator ĐỌC checks + 2 đáp án
    at=gen(AGG_SYS,q+f"\n\nCandidate A (solver): {sa}\nCandidate B (verifier): {va}\n\nVerifier checks:\n"+fmt_checks(vjson),384)
    ajson=last_json(at); vj["agg"]+=isinstance(ajson,dict); aa=field_ans(ajson,at)
    cor+=eq(aa,g)
    print(f"gold={g} S={sa} V={va} A={aa} ok={eq(aa,g)}", flush=True)

n=len(rows)
res={"n":n,"acc":round(cor/n,4),
     "valid_json_rate":{k:round(v/n,3) for k,v in vj.items()},
     "verifier_fix":vfix,"verifier_break":vbreak}
print("SUMMARY",json.dumps(res),flush=True)
json.dump(res,open("/kaggle/working/summary.json","w"))
