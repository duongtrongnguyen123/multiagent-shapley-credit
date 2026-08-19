# H54 (dang ky truoc #60) — nhu H40 nhung model LON = 14B (thay 7B).
# 14B tai tu HF va luong tu hoa nf4 TAI CHO bang bitsandbytes.
# (Da thu AWQ: transformers doi `gptqmodel`, goi do keo numpy khac ABI, roi thieu `pcre` -> bo.)
# (dan xuat tu H40 / #46) — SHARD @@SHARD@@/@@NSHARD@@ tren MATH-500.
# Kernel chi SINH va LUU du lieu tho. Moi tong hop (bo phieu, tang do kho, phan ra) lam O LOCAL
# tren toan bo 500 bai sau khi gop -> khong shard nao tu ket luan gi.
#
# DUNG CA HAI T4 THAT SU (data parallel, KHONG phai pipeline):
#   1.5B fp16  = 3.1 GB  -> moi GPU mot ban sao
#   14B  nf4   = ~9  GB  -> moi GPU mot ban sao   (fp16 29.5 GB KHONG vua 2 the T4)
# device_map="auto" chi chia lop (pipeline) = suc chua, KHONG phai toc do. O day ta muon toc do.
import os, re, csv, json, glob, threading, hashlib, torch, subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes>=0.46.1"], check=False)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

SHARD, NSHARD = @@SHARD@@, @@NSHARD@@
K, MAXNEW = 8, 512
BSS, BSB = 48, 8           # 14B nf4 ~9 GB + KV 192 KB/token (48 lop x 8 kv-head) -> BSB 8
TEMP = 0.8

M15 = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors", recursive=True), key=len)[0])
M7  = "Qwen/Qwen2.5-14B-Instruct"   # tai tu HF, luong tu hoa nf4 tai cho bang bitsandbytes
os.environ.setdefault("HF_HOME", "/kaggle/temp/hf")   # tranh gioi han 20GB cua /kaggle/working
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
# newline="" BAT BUOC: de bai MATH co xuong dong ben trong o -> thieu no thi DictReader
# cat nham dong va tra ve None cho cac cot cuoi (da lam chet shard 01/02/04/05).
RAW = list(csv.DictReader(open(CSV, newline="", encoding="utf-8")))
print(f"M15={M15}\nM7={M7}\nCSV={CSV} cot={list(RAW[0].keys())} dong_tho={len(RAW)}", flush=True)

NG = torch.cuda.device_count()
DEVS = [f"cuda:{i}" for i in range(NG)]
print(f"so GPU={NG} -> {DEVS}", flush=True)
assert NG >= 1

# Ten cot KHONG on dinh giua cac ban dataset: ban Kaggle dung 'Question'/'Answer' (viet hoa),
# ban HF dung 'problem'/'answer'. Tra cuu KHONG PHAN BIET HOA THUONG -> da lam chet ca 20 shard.
def _col(r, *names):
    low = {str(k).strip().lower(): v for k, v in r.items()}
    for n in names:
        v = low.get(n)
        if isinstance(v, str) and v.strip(): return v
    return None
def _lv(r):
    m = re.search(r"\d", str(_col(r, "level") or ""))
    return int(m.group()) if m else 0
def _q(r):  return _col(r, "problem", "question")
def _g(r):  return _col(r, "answer", "solution")
def _qh(t): return hashlib.md5(" ".join(str(t).split()).encode("utf-8")).hexdigest()[:12]

# Loc dong hong TRUOC khi chia shard. Moi shard loc y het nhau tren cung file
# -> chi so sau khi loc la nhat quan giua cac shard.
ALL = [r for r in RAW if isinstance(_q(r), str) and _q(r).strip()
                     and isinstance(_g(r), str) and _g(r).strip()]
print(f"sau khi loc: {len(ALL)}/{len(RAW)} dong dung (bo {len(RAW)-len(ALL)})", flush=True)
assert len(ALL) >= 400, f"CSV hong nang: chi con {len(ALL)} dong"

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
    errs = []
    def work(m, sub):
        try:
            loc = {i: [] for i in sub}
            for _ in range(rounds):
                outs = gen(m, tk, sysm, [prompts_by_idx[i] for i in sub], bs, temp)
                for i, o in zip(sub, outs): loc[i].append(o)
            with lock: store.update(loc)
        except Exception as e:
            import traceback; traceback.print_exc()
            with lock: errs.append(e)
    ths = [threading.Thread(target=work, args=(models[j], parts[j])) for j in range(len(models)) if parts[j]]
    for t in ths: t.start()
    for t in ths: t.join()
    # Luong chet TRONG IM LANG tung tra ve dict thieu khoa -> KeyError kho hieu o tan sau.
    # Nay bao loi ngay tai cho.
    if errs: raise RuntimeError(f"{len(errs)} luong sinh that bai: {errs[0]!r}")
    miss = [i for i in prompts_by_idx if i not in store]
    if miss: raise RuntimeError(f"thieu {len(miss)} bai sau khi sinh, vd {miss[:5]}")
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

# ---------- PHA 2+3: 14B nf4 (bitsandbytes), TRAI TREN CA HAI THE ----------
BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
import gc
# Giai phong TRIET DE pha 1 truoc khi nap 14B: xoa ca pool sinh lan cache.
for _v in ("ms","m","smalls"):
    if _v in dir(): pass
gc.collect(); torch.cuda.empty_cache(); torch.cuda.synchronize()
gc.collect(); torch.cuda.empty_cache()
print("VRAM TRUOC khi nap 14B (MiB/gpu):",
      [round(torch.cuda.memory_allocated(i)/1048576) for i in range(NG)],
      "| da giu cho:", [round(torch.cuda.memory_reserved(i)/1048576) for i in range(NG)], flush=True)
# 14B: TRAI TREN CA HAI THE (device_map="auto").
# Da thu 1-ban-sao-moi-GPU: dinh 9 GB trong so + mot shard fp16 dang chuyen doi > 14.56 GB -> OOM.
# Doi song song du lieu lay do TIN CAY; model lon la nut co chai nhung phai CHAY duoc da.
MAXMEM = {i: "9GiB" for i in range(NG)}
MAXMEM["cpu"] = "24GiB"        # cho phep tran ra CPU thay vi chet
bigs = [AutoModelForCausalLM.from_pretrained(M7, quantization_config=BNB,
                                             device_map="auto", max_memory=MAXMEM,
                                             low_cpu_mem_usage=True).eval()]
print("14B nf4 trai 2 the | VRAM MiB/gpu:",
      [round(torch.cuda.memory_allocated(i)/1048576) for i in range(NG)], flush=True)
QUANT = "nf4-split"

B_TXT = parallel_gen(bigs, T7, SOLVE, Q, BSB, TEMP, K)
print("xong pha 2", flush=True)

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
out = {"tag": f"H54s{SHARD}", "shard": SHARD, "nshard": NSHARD, "n": len(MINE),
       "quant_big": QUANT, "dtype_small": "fp16", "n_gpu": NG, "items": []}
for i in MINE:
    out["items"].append({
        "qi": i, "level": LV[i], "gold": G[i],
        "qhash": _qh(Q[i]),
        "small_pred": S_PRED[i],
        "big_pred": [pred(t) for t in B_TXT[i]],
        "seq_pred": SEQ.get(i),
        "escalated": i in ESC,
        "small_text": [t[:CAP] for t in S_TXT[i]],
        "big_text":   [t[:CAP] for t in B_TXT[i]],
        "seq_text":   {k: v[:CAP] for k, v in SEQ_TXT.get(i, {}).items()},
    })
json.dump(out, open(f"/kaggle/working/res_H54s{SHARD}.json", "w"))
print(f"DA LUU {len(out['items'])} bai -> res_H54s{SHARD}.json", flush=True)
print("XONG", flush=True)

# Ghi chu VRAM (tinh, khong chep):
#   1.5B fp16: 3.1 GB trong so; KV = 28 lop x 2 kv-head x 128 x 2(K,V) x 2 byte = 28 KB/token
#              -> 1024 token x 48 seq = 1.4 GB. Vua thoai mai tren 15.6 GB.
#   7B nf4:    ~5 GB trong so;  KV = 28 lop x 4 kv-head x 128 x 2 x 2 byte = 56 KB/token
#              -> 1024 token x 32 seq = 1.8 GB. Con thua nhieu.
