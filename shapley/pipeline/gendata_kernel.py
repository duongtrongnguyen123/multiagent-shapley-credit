# GIAI ĐOẠN 1 — AGENT TỰ SINH + TỰ GÁN NHÃN trên MATH, tạo corpus để huấn luyện (RFT/verifier/GRPO).
# Sinh trên MATH/train (7500 bài của Hendrycks). Đánh giá sau này trên MATH-500 (thuộc MATH/test)
# -> train/test TÁCH BẠCH, không nhiễm chéo.
#
# HAI QUYẾT ĐỊNH THIẾT KẾ RÚT TỪ CHÍNH SỐ LIỆU CỦA MÌNH:
#  (1) ÉP TRÌNH BÀY khi sinh. Đo được: Solver mặc định chỉ ghi "The answer is X" (median 20 KÝ TỰ).
#      RFT trên dữ liệu đó = DẠY MODEL BỎ QUA SUY LUẬN -> phản tác dụng. Bắt buộc phải ép.
#  (2) NHÃN LẤY TỪ GRADER (chân lý), KHÔNG từ verifier LLM. Đo được: verifier LLM chỉ bắt 15-17%
#      lỗi thật trên code, và báo động thừa trên math -> dùng làm nhãn thì hỏng corpus.
# NHƯNG vẫn cho agent TỰ GÁN NHÃN song song rồi ĐO agent-label vs gold-label
#      -> ra con số "agent làm labeler đáng tin tới đâu" (quyết định có tự gán nhãn được ở miền
#         KHÔNG có đáp án chuẩn hay không — chính là câu hỏi cho RLAIF).
import os, re, json, glob, statistics, torch

N = __N__          # số bài train
K = __K__          # số mẫu mỗi bài
BS = __BS__
QUANT = __QUANT__

if QUANT:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])
from transformers import AutoModelForCausalLM, AutoTokenizer

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True) or \
     glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])

files = sorted(glob.glob("/kaggle/input/**/MATH/train/**/*.json", recursive=True))
print(f"MATH train files = {len(files)}", flush=True)
probs = []
for f in files:
    try:
        d = json.load(open(f))
        if d.get("problem") and d.get("solution"): probs.append(d)
    except Exception: pass
# trộn xen kẽ theo thứ tự file để phủ đều các chủ đề, rồi lấy N bài
probs = probs[::max(1, len(probs)//max(N,1))][:N] if len(probs) > N else probs
print(f"MODEL={MODEL} | train n={len(probs)} | K={K}", flush=True)

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

qs  = [p["problem"] for p in probs]
gs  = [boxed(p["solution"]) for p in probs]
lvl = [p.get("level","?") for p in probs]
typ = [p.get("type","?") for p in probs]

# (1) ÉP TRÌNH BÀY — nếu không, corpus toàn đáp án trơ và RFT sẽ dạy model bỏ suy luận
SOLVE = ("Show your complete derivation. Write EVERY intermediate calculation on its own line "
         "as 'Step k: <expression> = <result>'. Never state the answer without showing the work "
         "that produced it. Put the final answer in \\boxed{}.")
JUDGE = ("You are given a math problem and a proposed solution. Decide if the FINAL ANSWER is correct. "
         "Reply with exactly one word: YES or NO.")

def chat(sysm,u):
    return tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                                   tokenize=False, add_generation_prompt=True)

# ---------- SINH K MẪU/BÀI ----------
samples = [[] for _ in qs]
for i in range(0, len(qs), BS):
    ch = qs[i:i+BS]
    e = tok([chat(SOLVE,q) for q in ch], return_tensors="pt", padding=True).to(model.device)
    with torch.no_grad():
        o = model.generate(**e, max_new_tokens=640, do_sample=True, temperature=0.9, top_p=0.95,
                           num_return_sequences=K, pad_token_id=tok.pad_token_id)
    L = e["input_ids"].shape[1]
    for j in range(len(ch)):
        for r in range(K):
            samples[i+j].append(tok.decode(o[j*K+r, L:], skip_special_tokens=True).strip())
    print(f"  gen {i+len(ch)}/{len(qs)}", flush=True)

# ---------- NHÃN TỪ GRADER (chân lý) ----------
flat = []
for qi, sl in enumerate(samples):
    for s in sl:
        flat.append({"qi": qi, "sol": s, "ans": pred(s), "gold_ok": eq(pred(s), gs[qi]), "len": len(s)})
print(f"tổng mẫu = {len(flat)}", flush=True)

# ---------- AGENT TỰ GÁN NHÃN (đo độ tin cậy của agent-as-labeler) ----------
jud = []
for i in range(0, len(flat), BS*2):
    ch = flat[i:i+BS*2]
    us = [f"Problem:\n{qs[f['qi']]}\n\nProposed solution:\n{f['sol'][:1200]}" for f in ch]
    e = tok([chat(JUDGE,u) for u in us], return_tensors="pt", padding=True).to(model.device)
    with torch.no_grad():
        o = model.generate(**e, max_new_tokens=8, do_sample=False, pad_token_id=tok.pad_token_id)
    L = e["input_ids"].shape[1]
    for j in range(len(ch)):
        jud.append(tok.decode(o[j, L:], skip_special_tokens=True).strip().upper().startswith("YES"))
    print(f"  judge {min(i+len(ch),len(flat))}/{len(flat)}", flush=True)
for f, j in zip(flat, jud): f["agent_ok"] = j

# ---------- CORPUS RFT: giữ mẫu ĐÚNG + CÓ TRÌNH BÀY, khử trùng ----------
rft, seen = [], set()
for f in flat:
    if not f["gold_ok"] or f["len"] < 150: continue      # loại lời giải trơ (bài học median-20-ký-tự)
    key = (f["qi"], re.sub(r"\s+"," ",f["sol"])[:200])
    if key in seen: continue
    seen.add(key)
    rft.append({"problem": qs[f["qi"]], "solution": f["sol"], "answer": gs[f["qi"]],
                "level": lvl[f["qi"]], "type": typ[f["qi"]]})

# ---------- THỐNG KÊ ----------
tp = sum(1 for f in flat if f["agent_ok"] and f["gold_ok"])
fp = sum(1 for f in flat if f["agent_ok"] and not f["gold_ok"])
fn = sum(1 for f in flat if not f["agent_ok"] and f["gold_ok"])
tn = sum(1 for f in flat if not f["agent_ok"] and not f["gold_ok"])
solved = [qi for qi in range(len(qs)) if any(eq(pred(s), gs[qi]) for s in samples[qi])]
by_level = {}
for qi in range(len(qs)):
    L_ = lvl[qi]; d = by_level.setdefault(L_, {"n":0,"solved":0})
    d["n"] += 1; d["solved"] += (qi in set(solved))
stats = {
  "n_problems": len(qs), "K": K, "n_samples": len(flat),
  "sample_acc": round(sum(f["gold_ok"] for f in flat)/max(len(flat),1), 4),
  "coverage_any_correct": round(len(solved)/max(len(qs),1), 4),      # pass@K = TRẦN của RFT
  "rft_examples": len(rft),
  "median_sol_len": int(statistics.median(f["len"] for f in flat)),
  "pct_under_150_chars": round(sum(1 for f in flat if f["len"]<150)/max(len(flat),1), 4),
  "coverage_by_level": {k: round(v["solved"]/max(v["n"],1),3) for k,v in sorted(by_level.items())},
  "agent_labeler": {                                                 # <-- ĐỘ TIN CẬY LABELER
      "tp": tp, "fp": fp, "fn": fn, "tn": tn,
      "precision": round(tp/max(tp+fp,1), 4),
      "recall": round(tp/max(tp+fn,1), 4),
      "accuracy": round((tp+tn)/max(len(flat),1), 4),
      "says_yes_rate": round((tp+fp)/max(len(flat),1), 4)}
}
print("SUMMARY", json.dumps(stats), flush=True)
json.dump(stats, open("/kaggle/working/summary.json","w"), indent=2)
json.dump(rft, open("/kaggle/working/rft_data.json","w"))
json.dump([{k:v for k,v in f.items() if k!="sol"} | {"sol": f["sol"][:2000]} for f in flat],
          open("/kaggle/working/labeled_samples.json","w"))
print(f"-> rft_data.json: {len(rft)} ví dụ | labeled_samples.json: {len(flat)} mẫu có nhãn", flush=True)
