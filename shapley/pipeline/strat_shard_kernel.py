# H40 (dang ky truoc #46) — SHARD @@SHARD@@/@@NSHARD@@ tren MATH-500.
# Kernel chi SINH va LUU du lieu tho. Moi tong hop (bo phieu, tang do kho, phan ra) lam O LOCAL
# tren toan bo 500 bai sau khi gop -> khong shard nao tu ket luan gi.
#
# DUNG CA HAI T4 THAT SU (data parallel, KHONG phai pipeline):
#   1.5B fp16  = 3.1 GB  -> moi GPU mot ban sao
#   7B   nf4   = ~5  GB  -> moi GPU mot ban sao   (fp16 15.2 GB KHONG vua 1 the T4)
# device_map="auto" chi chia lop (pipeline) = suc chua, KHONG phai toc do. O day ta muon toc do.
import os, re, csv, json, glob, threading, hashlib, torch, subprocess, sys
# Install bitsandbytes OFFLINE tu wheel trong dataset Kaggle (khong can Internet)
_wheels = glob.glob("/kaggle/input/**/bitsandbytes*.whl", recursive=True)
if _wheels:
    subprocess.run([sys.executable,"-m","pip","install","-q",_wheels[0]], check=True)
    print(f"installed bitsandbytes from {_wheels[0]}", flush=True)
else:
    print("WARNING: khong tim thay bitsandbytes wheel trong input — se fallback fp16", flush=True)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

SHARD, NSHARD = @@SHARD@@, @@NSHARD@@
K, MAXNEW = 8, 512
BSS, BSB = 48, 16          # tinh tu VRAM, khong chep lai: xem ghi chu cuoi file
                           # BSB=16 (tu 32): giam de tranh OOM o pha 3 (prompt dai)
TEMP = 0.8

M15 = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors", recursive=True), key=len)[0])
M7  = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True), key=len)[0])
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV)))
print(f"M15={M15}\nM7={M7}\nCSV={CSV} cot={list(ALL[0].keys())}", flush=True)

NG = torch.cuda.device_count()
DEVS = [f"cuda:{i}" for i in range(NG)]
print(f"so GPU={NG} -> {DEVS}", flush=True)
assert NG >= 1

def _ci(r, *keys):
    """Case-insensitive column lookup — CSV headers vary (Question/question)."""
    rl = {k.lower(): v for k, v in r.items()}
    for k in keys:
        v = rl.get(k.lower())
        if v is not None: return v
    return None
def _lv(r):
    m = re.search(r"\d", str(_ci(r, "level")))
    return int(m.group()) if m else 0
def _q(r):  return _ci(r, "problem", "question")
def _g(r):  return _ci(r, "answer")

# shard XEN KE -> moi shard co du cac muc do kho (cat lien tuc se lech tang)
MINE = [i for i in range(len(ALL)) if i % NSHARD == SHARD]
Q  = {i: _q(ALL[i]) for i in MINE}
G  = {i: _g(ALL[i]) for i in MINE}
LV = {i: _lv(ALL[i]) for i in MINE}
print(f"shard {SHARD}/{NSHARD}: {len(MINE)} bai, tang={sorted(set(LV.values()))}", flush=True)

TAIL   = "Put the final answer in \\boxed{}."
SOLVE  = f"Solve step by step. {TAIL}"
VERIFY = f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
ANCH   = f"Solve step by step. A previous attempt answered: @@A@@. {TAIL}"

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
def pred(t):
    b = _bx(t)
    if b is not None: return b.strip()
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
    return m[-1].strip() if m else None

def mktok(p):
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    return tk
T15, T7 = mktok(M15), mktok(M7)

def gen(model, tk, sysm, usrs, bs, temp):
    outs = []
    for i in range(0, len(usrs), bs):
        ch = usrs[i:i+bs]
        ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
              tokenize=False, add_generation_prompt=True) for u in ch]
        e = tk(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=MAXNEW, do_sample=(temp > 0),
                               temperature=max(temp, 1e-5), top_p=0.95, pad_token_id=tk.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o
    return outs

def split(items, n):
    return [items[j::n] for j in range(n)]

def parallel_gen(models, tk, sysm, prompts_by_idx, bs, temp, rounds):
    """Moi GPU mot ban sao model, moi luong lo mot phan bai. Threads that su chay chong lan
    vi generate() nha GIL trong luc goi CUDA."""
    parts = split(list(prompts_by_idx.keys()), len(models))
    store, lock = {}, threading.Lock()
    def work(m, sub):
        loc = {i: [] for i in sub}
        for _ in range(rounds):
            outs = gen(m, tk, sysm, [prompts_by_idx[i] for i in sub], bs, temp)
            for i, o in zip(sub, outs): loc[i].append(o)
        with lock: store.update(loc)
    ths = [threading.Thread(target=work, args=(models[j], parts[j])) for j in range(len(models)) if parts[j]]
    for t in ths: t.start()
    for t in ths: t.join()
    return store

# ---------- PHA 1: 1.5B fp16, mot ban sao MOI GPU ----------
smalls = []
for d in DEVS:
    m = AutoModelForCausalLM.from_pretrained(M15, torch_dtype=torch.float16).to(d).eval()
    smalls.append(m)
print(f"1.5B: {len(smalls)} ban sao", flush=True)
S_TXT = parallel_gen(smalls, T15, SOLVE, Q, BSS, TEMP, K)
for m in smalls: del m
del smalls; torch.cuda.empty_cache()
print("xong pha 1", flush=True)

S_PRED = {i: [pred(t) for t in S_TXT[i]] for i in MINE}

def vote3(ps):
    c = {}
    for p in ps[:3]:
        if p is not None: c[p] = c.get(p, 0) + 1
    if not c: return None, 0
    b = max(c, key=c.get); return b, c[b]
ESC = [i for i in MINE if vote3(S_PRED[i])[1] < 2]
print(f"escalate {len(ESC)}/{len(MINE)}", flush=True)

# ---------- PHA 2+3: 7B nf4, mot ban sao MOI GPU ----------
BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
bigs = []
try:
    for d in DEVS:
        m = AutoModelForCausalLM.from_pretrained(M7, quantization_config=BNB, device_map={"": d}).eval()
        bigs.append(m)
    print(f"7B nf4: {len(bigs)} ban sao | VRAM MiB/gpu:",
          [round(torch.cuda.memory_allocated(i)/1048576) for i in range(NG)], flush=True)
except Exception as e:
    # Du phong: neu 4-bit khong dung duoc (thieu bitsandbytes), quay ve fp16 trai tren ca 2 the.
    # Cham hon (pipeline, khong song song) nhung VAN RA KET QUA — 20 shard khong duoc chet ca loat.
    print(f"nf4 THAT BAI ({type(e).__name__}: {e}) -> quay ve fp16 device_map=auto", flush=True)
    for m in bigs: del m
    bigs = []; torch.cuda.empty_cache()
    bigs = [AutoModelForCausalLM.from_pretrained(M7, torch_dtype=torch.float16, device_map="auto").eval()]
    out_quant = "fp16-fallback"
QUANT = "nf4" if len(bigs) == NG else "fp16-fallback"

B_TXT = parallel_gen(bigs, T7, SOLVE, Q, BSB, TEMP, K)
print("xong pha 2", flush=True)
torch.cuda.empty_cache()   # giai phong KV cache giua pha 2 va 3

SEQ_TXT, SEQ = {}, {}
if ESC:
    anch = {i: ANCH.replace("@@A@@", str(vote3(S_PRED[i])[0])) + f"\n\n{Q[i]}" for i in ESC}
    s1 = parallel_gen(bigs, T7, SOLVE, anch, BSB, 0.0, 1)
    ver = {i: f"{Q[i]}\n\nProposed solution:\n{s1[i][0]}" for i in ESC}
    s2 = parallel_gen(bigs, T7, VERIFY, ver, BSB, 0.0, 1)
    for i in ESC:
        SEQ_TXT[i] = {"pass1": s1[i][0], "pass2": s2[i][0]}
        SEQ[i] = pred(s2[i][0]) if pred(s2[i][0]) is not None else pred(s1[i][0])
print("xong pha 3", flush=True)

CAP = 4000
out = {"tag": f"H40s{SHARD}", "shard": SHARD, "nshard": NSHARD, "n": len(MINE),
       "quant_big": QUANT, "dtype_small": "fp16", "n_gpu": NG, "items": []}
for i in MINE:
    out["items"].append({
        "qi": i, "level": LV[i], "gold": G[i],
        "qhash": hashlib.md5(Q[i].encode("utf-8")).hexdigest()[:12],
        "small_pred": S_PRED[i],
        "big_pred": [pred(t) for t in B_TXT[i]],
        "seq_pred": SEQ.get(i),
        "escalated": i in ESC,
        "small_text": [t[:CAP] for t in S_TXT[i]],
        "big_text":   [t[:CAP] for t in B_TXT[i]],
        "seq_text":   {k: v[:CAP] for k, v in SEQ_TXT.get(i, {}).items()},
    })
json.dump(out, open(f"/kaggle/working/res_H40s{SHARD}.json", "w"))
print(f"DA LUU {len(out['items'])} bai -> res_H40s{SHARD}.json", flush=True)
print("XONG", flush=True)

# Ghi chu VRAM (tinh, khong chep):
#   1.5B fp16: 3.1 GB trong so; KV = 28 lop x 2 kv-head x 128 x 2(K,V) x 2 byte = 28 KB/token
#              -> 1024 token x 48 seq = 1.4 GB. Vua thoai mai tren 15.6 GB.
#   7B nf4:    ~5 GB trong so;  KV = 28 lop x 4 kv-head x 128 x 2 x 2 byte = 56 KB/token
#              -> 1024 token x 32 seq = 1.8 GB. Con thua nhieu.
