# Kernel LOG từng bước: chạy full pipeline Planner->Solver->Verifier->Aggregator trên
# một ít câu GSM8K, lưu TOÀN BỘ văn bản mỗi agent nghĩ + đánh dấu chỗ đáp án bị ĐỔI
# (solver->verifier, verifier->aggregator) = bằng chứng negative transfer/sycophancy.
import os, re, csv, json, glob, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N = 200
find = lambda p: sorted(glob.glob(p, recursive=True), key=len)[0]
MODEL = os.path.dirname(find("/kaggle/input/**/model.safetensors"))
CSV = find("/kaggle/input/**/main_test.csv")
rows = list(csv.DictReader(open(CSV)))[:N]

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto").eval()

def gold(a):
    m = re.search(r"####\s*([-\d,\.]+)", a); return m.group(1).replace(",", "").strip() if m else None
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def ans(t):
    m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I) or NUM.findall(t or "")
    return m[-1].replace(",", "") if m else None
def gen(sys, usr, mx=512):
    p = tok.apply_chat_template([{"role":"system","content":sys},{"role":"user","content":usr}],
                                tokenize=False, add_generation_prompt=True)
    e = tok(p, return_tensors="pt").to("cuda")
    o = model.generate(**e, max_new_tokens=mx, do_sample=False, pad_token_id=tok.pad_token_id)
    return tok.decode(o[0, e["input_ids"].shape[1]:], skip_special_tokens=True).strip()

PLAN="You are a math planning assistant. Give a concise numbered plan of steps. Do NOT compute the final answer."
SOLVE="You are a careful math solver. Solve step by step. End with 'The answer is <number>'."
VERIFY="You are a math verifier. Given a problem and a proposed solution, check each step; if wrong, correct it. End with 'The answer is <number>'."
AGG="You are given a problem and candidate solutions. Decide the correct final answer. End with 'The answer is <number>'."

traces = []
for r in rows:
    q = r["question"]; g = gold(r["answer"])
    plan = gen(PLAN, q, 256)
    sol = gen(SOLVE, q + "\n\nSuggested plan:\n" + plan)
    ver = gen(VERIFY, q + "\n\nProposed solution:\n" + sol)
    agg = gen(AGG, q + f"\n\nCandidate 1:\n{sol}\n\nCandidate 2:\n{ver}", 256)
    sa, va, aa = ans(sol), ans(ver), ans(agg)
    ok = lambda x: x is not None and g is not None and abs(float(x)-float(g))<1e-4
    traces.append(dict(q=q, gold=g, plan=plan, sol=sol, ver=ver, agg=agg,
                       sa=sa, va=va, aa=aa, s_ok=ok(sa), v_ok=ok(va), a_ok=ok(aa),
                       flip_sv=(sa!=va), flip_va=(va!=aa)))
    tag = ("V PHÁ (đúng->sai)" if ok(sa) and not ok(va) else
           "V SỬA (sai->đúng)" if not ok(sa) and ok(va) else "")
    print(f"[{len(traces)}] gold={g} S={sa}({ok(sa)}) V={va}({ok(va)}) A={aa}({ok(aa)}) {tag}", flush=True)

json.dump(traces, open("/kaggle/working/traces.json","w"), indent=2)
nv_break = sum(t["s_ok"] and not t["v_ok"] for t in traces)
nv_fix   = sum(not t["s_ok"] and t["v_ok"] for t in traces)
print(f"\nTỔNG {len(traces)} câu: Verifier SỬA {nv_fix}, Verifier PHÁ {nv_break}", flush=True)
