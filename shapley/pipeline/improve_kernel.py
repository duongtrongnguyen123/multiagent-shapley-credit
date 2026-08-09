# Thử 4 hướng CẢI TIẾN (cùng Qwen2.5-1.5B, không thay/finetune model) trên GSM8K.
# MODE bake sẵn: base | showwork | loop | tool. Đo accuracy để so cải tiến.
import os, re, csv, json, glob, io, contextlib, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODE = "__MODE__"
N = 150
find = lambda p: sorted(glob.glob(p, recursive=True), key=len)[0]
MODEL = os.path.dirname(find("/kaggle/input/**/model.safetensors"))
rows = list(csv.DictReader(open(find("/kaggle/input/**/main_test.csv"))))[:N]
tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto").eval()

def gen(sys, usr, mx=512):
    p = tok.apply_chat_template([{"role":"system","content":sys},{"role":"user","content":usr}],
                                tokenize=False, add_generation_prompt=True)
    e = tok(p, return_tensors="pt").to("cuda")
    o = model.generate(**e, max_new_tokens=mx, do_sample=False, pad_token_id=tok.pad_token_id)
    return tok.decode(o[0, e["input_ids"].shape[1]:], skip_special_tokens=True).strip()

def gold(a): m=re.search(r"####\s*([-\d,\.]+)",a); return m.group(1).replace(",","").strip() if m else None
NUM=re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def ans(t):
    m=re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)",t or "",re.I) or NUM.findall(t or "")
    return m[-1].replace(",","") if m else None
def ok(x,g):
    try: return x is not None and g is not None and abs(float(x)-float(g))<1e-4
    except: return x==g

PLAN="Give a concise numbered plan. Do NOT compute the final answer."
SOLVE="Solve step by step. End with 'The answer is <number>'."
SOLVE_FULL="Solve step by step, showing EVERY arithmetic operation explicitly (do not skip work). End with 'The answer is <number>'."
VERIFY="Check the proposed solution step by step; if wrong, correct it. End with 'The answer is <number>'."
AGG="Given candidate solutions, decide the correct final answer. End with 'The answer is <number>'."
POT="Write ONLY a short Python program that computes the answer and prints it as the last line. No explanation."

def run_pot(code):
    code=re.sub(r"^```(python)?|```$","",code.strip(),flags=re.M)
    buf=io.StringIO()
    try:
        with contextlib.redirect_stdout(buf): exec(code,{})
        out=buf.getvalue().strip().splitlines()
        return ans(out[-1]) if out else None
    except Exception: return None

cor=0
for r in rows:
    q=r["question"]; g=gold(r["answer"])
    if MODE=="tool":                                  # PoT: model viết python, mình chạy
        code=gen(POT,q,400); a=run_pot(code)
        if a is None: a=ans(gen(SOLVE,q))             # fallback text
    elif MODE=="loop":                                # Solver làm lại sau khi Verifier chê
        plan=gen(PLAN,q,256); sol=gen(SOLVE,q+"\n\nPlan:\n"+plan)
        ver=gen(VERIFY,q+"\n\nProposed solution:\n"+sol)
        if ans(ver)!=ans(sol):
            sol2=gen(SOLVE,q+"\n\nA reviewer flagged an error:\n"+ver+"\n\nRedo carefully.")
            a=ans(sol2)
        else: a=ans(sol)
    elif MODE=="struct":                              # ép FORMAT: Solver đánh số step, Verifier duyệt TỪNG step
        S_ST="Solve by numbering each step exactly as 'Step k: <calculation> = <result>'. End with 'The answer is <number>'."
        V_ST=("For EACH numbered step in the proposed solution, output a line 'Step k: OK' or "
              "'Step k: WRONG, correct value is <v>'. Do NOT resolve from scratch. Then 'The answer is <number>'.")
        sol=gen(S_ST,q)
        ver=gen(V_ST,q+"\n\nProposed solution:\n"+sol)
        a=ans(ver)
    else:                                             # base / showwork: P->S->V->A
        plan=gen(PLAN,q,256)
        sol=gen(SOLVE_FULL if MODE=="showwork" else SOLVE, q+"\n\nPlan:\n"+plan)
        ver=gen(VERIFY,q+"\n\nProposed solution:\n"+sol)
        agg=gen(AGG,q+f"\n\nCandidate 1:\n{sol}\n\nCandidate 2:\n{ver}",256)
        a=ans(agg)
    cor+=ok(a,g)
acc=cor/len(rows)
print("SUMMARY",json.dumps({"mode":MODE,"n":len(rows),"acc":acc}),flush=True)
json.dump({"mode":MODE,"n":len(rows),"acc":acc},open("/kaggle/working/summary.json","w"))
