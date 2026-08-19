# H45 (dang ky truoc #51) — delta_seq = seq - maj3, do tren luoi tac vu x co model.
# KHONG escalate, KHONG hai model. Co lap DUNG mot bien: do bao hoa cua chinh model dang chay.
# `greedy` cua moi o CHINH LA thuoc do bao hoa cua o do.
import os, re, csv, json, glob, threading, hashlib, torch, subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes>=0.46.1"], check=False)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

SHARD, NSHARD = @@SHARD@@, @@NSHARD@@
TASK, SIZE = "@@TASK@@", "@@SIZE@@"          # gsm8k|math , 15|7
N, K, MAXNEW = 300, 3, 512
BS = 32 if SIZE == "15" else 8

pat = "model.safetensors" if SIZE == "15" else "model.safetensors.index.json"
MODEL = os.path.dirname(sorted(glob.glob(f"/kaggle/input/**/{pat}", recursive=True), key=len)[0])
FN = "main_test.csv" if TASK == "gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FN}", recursive=True), key=len)[0]
RAW = list(csv.DictReader(open(CSV, newline="", encoding="utf-8")))
print(f"MODEL={MODEL}\nCSV={CSV} cot={list(RAW[0].keys())} n_tho={len(RAW)}", flush=True)

def _col(r, *names):
    low = {str(k).strip().lower(): v for k, v in r.items()}
    for n in names:
        v = low.get(n)
        if isinstance(v, str) and v.strip(): return v
    return None
def _qh(t): return hashlib.md5(" ".join(str(t).split()).encode("utf-8")).hexdigest()[:12]

def _bx(t):
    i = (t or "").rfind("\\boxed")
    if i < 0: return None
    i = t.find("{", i); d = 0; s0 = i
    for j in range(i, len(t)):
        if t[j] == "{": d += 1
        elif t[j] == "}":
            d -= 1
            if d == 0: return t[s0+1:j]
    return None
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
if TASK == "gsm8k":
    TAIL = "End with 'The answer is <number>'."
    def gold(r): return (_col(r, "answer") or "").split("####")[-1].replace(",", "").strip()
    def pred(t):
        m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I) or NUM.findall(t or "")
        return m[-1].replace(",", "") if m else None
    def ok(x, g):
        try: return x is not None and abs(float(x) - float(g)) < 1e-4
        except Exception: return x == g
else:
    TAIL = "Put the final answer in \\boxed{}."
    def gold(r): return _bx(_col(r, "answer") or "") or (NUM.findall(_col(r, "answer") or "") or [""])[-1]
    def pred(t):
        b = _bx(t)
        if b is not None: return b.strip()
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None
    def _nm(a):
        if a is None: return None
        a = str(a).strip()
        for z in ["\\left", "\\right", "\\!", "\\,", "$", " ", ","]: a = a.replace(z, "")
        a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a).replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
        return a.rstrip(".").strip("{}").lower()
    def ok(x, g):
        x, g = _nm(x), _nm(g)
        if not x or not g: return False
        if x == g: return True
        try: return abs(float(x) - float(g)) < 1e-6
        except Exception: return False

ALL = [r for r in RAW if isinstance(_col(r, "question", "problem"), str) and gold(r)][:N]
print(f"sau khi loc: {len(ALL)} bai", flush=True)
assert len(ALL) >= 300, f"chi con {len(ALL)} bai"
MINE = [i for i in range(len(ALL)) if i % NSHARD == SHARD]
Q = {i: _col(ALL[i], "question", "problem") for i in MINE}
G = {i: gold(ALL[i]) for i in MINE}
print(f"shard {SHARD}/{NSHARD}: {len(MINE)} bai | TASK={TASK} SIZE={SIZE}", flush=True)

SOLVE  = f"Solve step by step. {TAIL}"
VERIFY = f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
ANCH   = f"Solve step by step. A previous attempt answered: @@A@@. {TAIL}"

NG = torch.cuda.device_count(); DEVS = [f"cuda:{i}" for i in range(NG)]
def mktok(p):
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    return tk
TK = mktok(MODEL)
def _chunk(m, sysm, ch, temp):
    ps = [TK.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
          tokenize=False, add_generation_prompt=True) for u in ch]
    e = TK(ps, return_tensors="pt", padding=True).to(m.device)
    with torch.no_grad():
        o = m.generate(**e, max_new_tokens=MAXNEW, do_sample=(temp > 0),
                       temperature=max(temp, 1e-5), top_p=0.95, pad_token_id=TK.pad_token_id)
    L = e["input_ids"].shape[1]
    r = [TK.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    del e, o
    return r
def gen(m, sysm, usrs, temp):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i+BS]; cur = len(ch)
        while True:
            try:
                for j in range(0, len(ch), cur): outs += _chunk(m, sysm, ch[j:j+cur], temp)
                break
            except torch.OutOfMemoryError:
                torch.cuda.empty_cache()
                if cur == 1: raise
                cur = max(1, cur // 2); outs = outs[:i]
                print(f"  OOM -> lo {cur}", flush=True)
    return outs
def pgen(models, sysm, by_idx, temp, rounds):
    keys = list(by_idx.keys()); parts = [keys[j::len(models)] for j in range(len(models))]
    store, lock, errs = {}, threading.Lock(), []
    def work(m, sub):
        try:
            loc = {i: [] for i in sub}
            for _ in range(rounds):
                for i, o in zip(sub, gen(m, sysm, [by_idx[i] for i in sub], temp)): loc[i].append(o)
            with lock: store.update(loc)
        except Exception as e:
            import traceback; traceback.print_exc()
            with lock: errs.append(e)
    ths = [threading.Thread(target=work, args=(models[j], parts[j])) for j in range(len(models)) if parts[j]]
    for t in ths: t.start()
    for t in ths: t.join()
    if errs: raise RuntimeError(f"luong sinh that bai: {errs[0]!r}")
    miss = [i for i in by_idx if i not in store]
    if miss: raise RuntimeError(f"thieu {len(miss)} bai")
    return store

if SIZE == "7":
    BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    try:
        MS = [AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=BNB, device_map={"": d}).eval() for d in DEVS]
        QUANT = "nf4"
    except Exception as e:
        print(f"nf4 that bai ({e}) -> fp16 auto", flush=True)
        MS = [AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto").eval()]
        QUANT = "fp16-fallback"
else:
    MS = [AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16).to(d).eval() for d in DEVS]
    QUANT = "fp16"
print(f"{len(MS)} ban sao | {QUANT}", flush=True)

# greedy (thuoc do bao hoa)
GRE = pgen(MS, SOLVE, Q, 0.0, 1)
# maj3
SMP = pgen(MS, SOLVE, Q, 0.8, K)
# seq: giai -> giai lai CO MO NEO -> tu kiem   (3 luot, ngang ngan sach maj3)
s1 = pgen(MS, SOLVE, Q, 0.0, 1)
a1 = {i: ANCH.replace("@@A@@", str(pred(s1[i][0]))) + f"\n\n{Q[i]}" for i in MINE}
s2 = pgen(MS, SOLVE, a1, 0.0, 1)
v = {i: f"{Q[i]}\n\nProposed solution:\n{s2[i][0]}" for i in MINE}
s3 = pgen(MS, VERIFY, v, 0.0, 1)
print("xong sinh", flush=True)

CAP = 3000
out = {"tag": f"H45s{SHARD}", "shard": SHARD, "nshard": NSHARD, "task": TASK, "size": SIZE,
       "quant": QUANT, "n": len(MINE), "n_gpu": NG, "items": []}
for i in MINE:
    out["items"].append({
        "qi": i, "qhash": _qh(Q[i]), "gold": G[i],
        "greedy_pred": pred(GRE[i][0]),
        "samp_pred": [pred(t) for t in SMP[i]],
        "seq_pred": (pred(s3[i][0]) if pred(s3[i][0]) is not None else pred(s2[i][0])),
        "seq_texts": {"s1": s1[i][0][:CAP], "s2": s2[i][0][:CAP], "s3": s3[i][0][:CAP]},
    })
json.dump(out, open(f"/kaggle/working/res_H45s{SHARD}.json", "w"))
print(f"DA LUU {len(out['items'])} bai -> res_H45s{SHARD}.json", flush=True)
print("XONG", flush=True)
