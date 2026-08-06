# SELF-CONSISTENCY (maj@k) vs LLM-AGGREGATOR trên MATH-500 — cùng một bể k=8 mẫu.
# Câu hỏi: bộ tổng hợp THỐNG KÊ (bỏ phiếu) hay bộ tổng hợp LLM tốt hơn?
# Data trước của mình: Aggregator-LLM yếu, Verifier phá đáp án đúng. Bỏ phiếu KHÔNG thể
# phá vì nó không tự nghĩ ra đáp án mới -> giả thuyết: maj@k thắng cả greedy lẫn LLM-agg.
# Sinh 8 mẫu MỘT lần rồi tính mọi chỉ số từ cùng bể đó (công bằng tuyệt đối, không tốn thêm):
#   greedy(k=1) | maj@2 | maj@4 | maj@8 | LLM-agg trên đúng 8 ứng viên đó | oracle@8 (trần trên)
import os, re, csv, json, glob, torch
from collections import Counter

N = __N__
BS = __BS__          # số BÀI mỗi lượt (mỗi bài sinh K mẫu -> BS*K chuỗi cùng lúc)
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
print("MODEL:", MODEL, flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
if QUANT:
    from transformers import BitsAndBytesConfig
    _b = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=_b, device_map="auto").eval()
else:
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="cuda").eval()
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
def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g: return False
    if p == g: return True
    try: return abs(float(p)-float(g)) < 1e-6
    except: return False
def pred(t):
    b = boxed(t)
    if b is not None: return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I); return m[-1].strip() if m else None

qs = [r["Question"] for r in rows]; gs = [boxed(r["Answer"]) for r in rows]
SOLVE = "Solve the problem step by step. Put the final answer in \\boxed{}."

def chat(sysm, u):
    return tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                                   tokenize=False, add_generation_prompt=True)

# ---- 1) GREEDY (k=1, mốc so sánh) ----
greedy = []
for i in range(0, len(qs), BS*2):
    ch = qs[i:i+BS*2]
    e = tok([chat(SOLVE,q) for q in ch], return_tensors="pt", padding=True).to(model.device)
    with torch.no_grad():
        o = model.generate(**e, max_new_tokens=1024, do_sample=False, pad_token_id=tok.pad_token_id)
    L = e["input_ids"].shape[1]
    greedy += [pred(tok.decode(o[j, L:], skip_special_tokens=True)) for j in range(len(ch))]
    print(f"  greedy {len(greedy)}/{len(qs)}", flush=True)
acc_greedy = sum(eq(a,g) for a,g in zip(greedy,gs))/len(gs)
print(f"[greedy k=1] acc = {acc_greedy:.3f}", flush=True)

# ---- 2) SINH K=8 MẪU (temperature) — dùng chung cho MỌI chỉ số bên dưới ----
samples = [[] for _ in qs]
for i in range(0, len(qs), BS):
    ch = qs[i:i+BS]
    e = tok([chat(SOLVE,q) for q in ch], return_tensors="pt", padding=True).to(model.device)
    with torch.no_grad():
        o = model.generate(**e, max_new_tokens=1024, do_sample=True, temperature=0.8, top_p=0.95,
                           num_return_sequences=K, pad_token_id=tok.pad_token_id)
    L = e["input_ids"].shape[1]
    for j in range(len(ch)):
        for r in range(K):
            samples[i+j].append(pred(tok.decode(o[j*K+r, L:], skip_special_tokens=True)))
    print(f"  sampled {i+len(ch)}/{len(qs)}", flush=True)

def majority(cands):
    """Bỏ phiếu trên đáp án đã chuẩn hoá; trả về đáp án gốc của phe đông nhất."""
    keys = [norm(c) for c in cands if norm(c)]
    if not keys: return None, 0
    k, cnt = Counter(keys).most_common(1)[0]
    for c in cands:
        if norm(c) == k: return c, cnt
    return None, 0

out = {"n": len(gs), "K": K, "greedy": round(acc_greedy,4)}
votes8 = []
for k in (2, 4, 8):                      # đường cong scaling: cùng bể, lấy k mẫu đầu
    correct = 0
    for i in range(len(qs)):
        m, cnt = majority(samples[i][:k])
        if k == 8: votes8.append(cnt)
        correct += eq(m, gs[i])
    out[f"maj@{k}"] = round(correct/len(gs), 4)
    print(f"[maj@{k}] acc = {out[f'maj@{k}']:.3f}", flush=True)

# trần trên: có ÍT NHẤT 1 trong 8 mẫu đúng -> cho biết còn bao nhiêu dư địa cho khâu CHỌN
out["oracle@8"] = round(sum(any(eq(c,g) for c in s) for s,g in zip(samples,gs))/len(gs), 4)
print(f"[oracle@8] acc = {out['oracle@8']:.3f}", flush=True)

# ---- 3) LLM-AGGREGATOR trên ĐÚNG 8 ứng viên đó (đối đầu trực tiếp với bỏ phiếu) ----
AGG = ("You are given several candidate final answers to a math problem. "
       "Decide which one is correct. Put your chosen final answer in \\boxed{}.")
llm_agg = []
for i in range(0, len(qs), BS*2):
    ch = list(range(i, min(i+BS*2, len(qs))))
    us = [qs[j] + "\n\nCandidate answers:\n" + "\n".join(
            f"{r+1}. {samples[j][r]}" for r in range(K)) for j in ch]
    e = tok([chat(AGG,u) for u in us], return_tensors="pt", padding=True).to(model.device)
    with torch.no_grad():
        o = model.generate(**e, max_new_tokens=384, do_sample=False, pad_token_id=tok.pad_token_id)
    L = e["input_ids"].shape[1]
    llm_agg += [pred(tok.decode(o[t, L:], skip_special_tokens=True)) for t in range(len(ch))]
    print(f"  llm-agg {len(llm_agg)}/{len(qs)}", flush=True)
out["llm_agg@8"] = round(sum(eq(a,g) for a,g in zip(llm_agg,gs))/len(gs), 4)
print(f"[llm_agg@8] acc = {out['llm_agg@8']:.3f}", flush=True)

# LLM-agg có "phá" phe đa số không? (đếm khi bỏ phiếu đúng mà LLM chọn sai)
maj8 = [majority(s)[0] for s in samples]
out["llm_breaks_majority"] = sum(1 for i in range(len(gs)) if eq(maj8[i],gs[i]) and not eq(llm_agg[i],gs[i]))
out["llm_fixes_majority"]  = sum(1 for i in range(len(gs)) if not eq(maj8[i],gs[i]) and eq(llm_agg[i],gs[i]))
out["mean_top_votes"] = round(sum(votes8)/max(len(votes8),1), 2)

print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json","w"), indent=2)
