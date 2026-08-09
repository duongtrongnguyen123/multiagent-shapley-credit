# H42 (dang ky truoc #48) — DINH TUYEN TREN CODE (MBPP), shard @@SHARD@@/@@NSHARD@@.
# Kernel chi SINH + CHAY THU va luu du lieu tho. Moi tong hop lam O LOCAL.
#
# KHONG RO RI: assert[0] vao prompt va dung dinh tuyen; assert[1..2] CHI de cham diem.
# Hai bo dinh tuyen khac nhau DUNG mot dieu: co nhin dap an ky vong hay khong.
#   route_consensus: 3 ban 1.5B -> chay tren LOI GOI cua assert[0], so dau ra VOI NHAU
#   route_oracle   : 1 ban 1.5B -> chay assert[0] DAY DU (co ky vong)
import os, re, ast, json, glob, threading, hashlib, tempfile, subprocess, sys, torch
from concurrent.futures import ThreadPoolExecutor
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes>=0.46.1"], check=False)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

SHARD, NSHARD = @@SHARD@@, @@NSHARD@@
K, MAXNEW, TEMP = 8, 512, 0.8
KS = 3                      # so ban cua model nho
BSS, BSB = 32, 8   # 7B nf4: 2 ban sao/the -> logits tien xu ly [B,T,151936] la thu bung VRAM
TIMEOUT = 8

M15 = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors", recursive=True), key=len)[0])
M7  = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True), key=len)[0])
JL  = sorted(glob.glob("/kaggle/input/**/*.jsonl", recursive=True), key=len)[0]
RAW = [json.loads(l) for l in open(JL, encoding="utf-8") if l.strip()]
print(f"M15={M15}\nM7={M7}\nJL={JL} n_tho={len(RAW)}", flush=True)

def split_assert(a):
    """tach 'assert LOI_GOI == KY_VONG' bang AST (da kiem: 498/500 tach duoc)"""
    a = (a or "").strip()
    if not a.startswith("assert"): return None
    try: node = ast.parse(a[len("assert"):].strip(), mode="eval").body
    except Exception: return None
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
        return ast.unparse(node.left)
    return None

ALL = []
for r in RAW:
    try: tid = int(r["task_id"])
    except Exception: continue
    if not (11 <= tid <= 510): continue          # tach chuan MBPP test
    t = r.get("test_list") or []
    if len(t) < 3: continue
    call = split_assert(t[0])
    if call is None: continue                     # 2/500 bai khong tach duoc -> bo, ghi ro
    ALL.append({"tid": tid, "text": r["text"], "setup": r.get("test_setup_code") or "",
                "a0": t[0], "a1": t[1], "a2": t[2], "call": call})
ALL.sort(key=lambda x: x["tid"])
print(f"sau khi loc: {len(ALL)} bai dung (tach chuan 11-510)", flush=True)
assert len(ALL) >= 400, f"du lieu hong: chi con {len(ALL)}"

MINE = [i for i in range(len(ALL)) if i % NSHARD == SHARD]
print(f"shard {SHARD}/{NSHARD}: {len(MINE)} bai", flush=True)

NG = torch.cuda.device_count(); DEVS = [f"cuda:{i}" for i in range(NG)]
print(f"so GPU={NG}", flush=True)

SOLVE = ("Complete the Python function. Return the COMPLETE function including the signature, "
         "inside a ```python code block. No explanation.")
REVIEW = ("Review the code below for correctness against the task. If it is wrong, fix it. "
          "Return the COMPLETE function inside a ```python code block.")
def task_prompt(x):
    return f"{x['text']}\n\nYour code must satisfy this test:\n{x['a0']}"
def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()

# ---------------- chay thu: MOI chuong trinh chay MOT LAN, do 3 thu ----------------
def probe_src(x, code):
    return (code + "\n\n" + f'''
import json as _J
_R = {{}}
try: exec({json.dumps(x["setup"])})
except Exception: pass
try:
    _v = eval({json.dumps(x["call"])})
    _R["out"] = repr(_v)[:200]
except Exception as _e:
    _R["out"] = "ERR:" + type(_e).__name__
for _k, _s in (("a0", {json.dumps(x["a0"])}), ("h1", {json.dumps(x["a1"])}), ("h2", {json.dumps(x["a2"])})):
    try:
        exec(_s); _R[_k] = True
    except Exception:
        _R[_k] = False
_R["held"] = bool(_R["h1"] and _R["h2"])
print("@@R@@" + _J.dumps(_R))
''')
def probe(args):
    x, code = args
    if not code or not code.strip():
        return {"out": "ERR:Empty", "a0": False, "held": False, "compiles": False}
    try: compile(code, "<s>", "exec"); comp = True
    except Exception: comp = False
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(probe_src(x, code)); p = f.name
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        m = re.search(r"@@R@@(\{.*\})", r.stdout or "")
        d = json.loads(m.group(1)) if m else {"out": "ERR:NoOutput", "a0": False, "held": False}
    except subprocess.TimeoutExpired:
        d = {"out": "ERR:Timeout", "a0": False, "held": False}
    except Exception as e:
        d = {"out": "ERR:" + type(e).__name__, "a0": False, "held": False}
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
    d["compiles"] = comp
    return d
def probe_many(pairs):
    # chay thu la viec CPU + I/O -> dung nhieu luong, khong de GPU cho khong
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(probe, pairs))

# ---------------- sinh: mot ban sao model MOI GPU ----------------
def mktok(p):
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    return tk
T15, T7 = mktok(M15), mktok(M7)
def _gen_chunk(model, tk, sysm, ch, temp):
    ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
          tokenize=False, add_generation_prompt=True) for u in ch]
    e = tk(ps, return_tensors="pt", padding=True).to(model.device)
    with torch.no_grad():
        o = model.generate(**e, max_new_tokens=MAXNEW, do_sample=(temp > 0),
                           temperature=max(temp, 1e-5), top_p=0.95, pad_token_id=tk.pad_token_id)
    L = e["input_ids"].shape[1]
    r = [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    del e, o
    return r
def gen(model, tk, sysm, usrs, bs, temp):
    """Gap OOM thi CHIA DOI lo va thu lai, xuong toi 1. Mot lo dai bat thuong khong
    duoc phep giet ca shard (da lam hong shard 00: logits tien xu ly doi 4.25 GiB)."""
    outs = []
    for i in range(0, len(usrs), bs):
        ch = usrs[i:i+bs]
        cur = len(ch)
        while True:
            try:
                for j in range(0, len(ch), cur):
                    outs += _gen_chunk(model, tk, sysm, ch[j:j+cur], temp)
                break
            except torch.OutOfMemoryError:
                torch.cuda.empty_cache()
                if cur == 1: raise
                cur = max(1, cur // 2)
                outs = outs[:i]     # bo phan da sinh cua lo nay, lam lai tu dau lo
                print(f"  OOM -> giam lo xuong {cur}", flush=True)
    return outs
def parallel_gen(models, tk, sysm, by_idx, bs, temp, rounds):
    keys = list(by_idx.keys())
    parts = [keys[j::len(models)] for j in range(len(models))]
    store, lock, errs = {}, threading.Lock(), []
    def work(m, sub):
        try:
            loc = {i: [] for i in sub}
            for _ in range(rounds):
                for i, o in zip(sub, gen(m, tk, sysm, [by_idx[i] for i in sub], bs, temp)):
                    loc[i].append(o)
            with lock: store.update(loc)
        except Exception as e:
            import traceback; traceback.print_exc()
            with lock: errs.append(e)
    ths = [threading.Thread(target=work, args=(models[j], parts[j])) for j in range(len(models)) if parts[j]]
    for t in ths: t.start()
    for t in ths: t.join()
    if errs: raise RuntimeError(f"{len(errs)} luong sinh that bai: {errs[0]!r}")
    miss = [i for i in by_idx if i not in store]
    if miss: raise RuntimeError(f"thieu {len(miss)} bai sau khi sinh")
    return store

PR = {i: task_prompt(ALL[i]) for i in MINE}

# ---- PHA 1: 1.5B, 3 ban ----
smalls = [AutoModelForCausalLM.from_pretrained(M15, torch_dtype=torch.float16).to(d).eval() for d in DEVS]
print(f"1.5B: {len(smalls)} ban sao", flush=True)
S_TXT = parallel_gen(smalls, T15, SOLVE, PR, BSS, TEMP, KS)
for m in smalls: del m
del smalls; torch.cuda.empty_cache()
S_CODE = {i: [extract(t) for t in S_TXT[i]] for i in MINE}
flat = [(ALL[i], S_CODE[i][k]) for i in MINE for k in range(KS)]
res = probe_many(flat)
S_PR = {i: res[n*KS:(n+1)*KS] for n, i in enumerate(MINE)}
print("xong pha 1 + chay thu", flush=True)

def consensus_ok(pr):
    c = {}
    for d in pr[:KS]:
        o = d["out"]
        if isinstance(o, str) and o.startswith("ERR:"): continue   # KHOA TRUOC: cung crash != dong thuan
        c[o] = c.get(o, 0) + 1
    if not c: return None
    b = max(c, key=lambda z: c[z])
    return b if c[b] >= 2 else None
ESC_C = [i for i in MINE if consensus_ok(S_PR[i]) is None]
ESC_O = [i for i in MINE if not S_PR[i][0]["a0"]]
ESC = sorted(set(ESC_C) | set(ESC_O))
print(f"escalate: dong thuan {len(ESC_C)}/{len(MINE)} | oracle {len(ESC_O)}/{len(MINE)} | hop {len(ESC)}", flush=True)

# ---- PHA 2+3: 7B ----
BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
bigs = []
try:
    for d in DEVS:
        bigs.append(AutoModelForCausalLM.from_pretrained(M7, quantization_config=BNB, device_map={"": d}).eval())
    print(f"7B nf4: {len(bigs)} ban sao", flush=True)
except Exception as e:
    print(f"nf4 THAT BAI ({type(e).__name__}: {e}) -> fp16 device_map=auto", flush=True)
    bigs = []; torch.cuda.empty_cache()
    bigs = [AutoModelForCausalLM.from_pretrained(M7, torch_dtype=torch.float16, device_map="auto").eval()]
QUANT = "nf4" if len(bigs) == NG else "fp16-fallback"

B_TXT = parallel_gen(bigs, T7, SOLVE, PR, BSB, TEMP, K)
B_CODE = {i: [extract(t) for t in B_TXT[i]] for i in MINE}
flatb = [(ALL[i], B_CODE[i][k]) for i in MINE for k in range(K)]
resb = probe_many(flatb)
B_PR = {i: resb[n*K:(n+1)*K] for n, i in enumerate(MINE)}
print("xong pha 2", flush=True)

SEQ_CODE, SEQ_PR, SEQ_TXT = {}, {}, {}
if ESC:
    anch = {i: (f"{PR[i]}\n\nA previous attempt produced this code:\n```python\n{S_CODE[i][0]}\n```\n"
                f"Write the correct complete function.") for i in ESC}
    s1 = parallel_gen(bigs, T7, SOLVE, anch, BSB, 0.0, 1)
    rev = {i: f"{PR[i]}\n\nCode:\n```python\n{extract(s1[i][0])}\n```" for i in ESC}
    s2 = parallel_gen(bigs, T7, REVIEW, rev, BSB, 0.0, 1)
    for i in ESC:
        SEQ_TXT[i] = {"pass1": s1[i][0][:4000], "pass2": s2[i][0][:4000]}
        SEQ_CODE[i] = extract(s2[i][0]) or extract(s1[i][0])
    rs = probe_many([(ALL[i], SEQ_CODE[i]) for i in ESC])
    SEQ_PR = {i: rs[n] for n, i in enumerate(ESC)}
print("xong pha 3", flush=True)

CAP = 4000
out = {"tag": f"H42s{SHARD}", "shard": SHARD, "nshard": NSHARD, "n": len(MINE),
       "quant_big": QUANT, "n_gpu": NG, "task": "mbpp", "items": []}
for i in MINE:
    x = ALL[i]
    out["items"].append({
        "qi": i, "tid": x["tid"], "text": x["text"][:500], "a0": x["a0"],
        "small": [{k: d[k] for k in ("out", "a0", "held", "compiles")} for d in S_PR[i]],
        "big":   [{k: d[k] for k in ("out", "a0", "held", "compiles")} for d in B_PR[i]],
        "seq":   ({k: SEQ_PR[i][k] for k in ("out", "a0", "held", "compiles")} if i in SEQ_PR else None),
        "esc_consensus": i in ESC_C, "esc_oracle": i in ESC_O,
        "small_code": [c[:CAP] for c in S_CODE[i]],
        "big_code":   [c[:CAP] for c in B_CODE[i]],
        "seq_code":   (SEQ_CODE.get(i) or "")[:CAP],
    })
json.dump(out, open(f"/kaggle/working/res_H42s{SHARD}.json", "w"))
print(f"DA LUU {len(out['items'])} bai -> res_H42s{SHARD}.json", flush=True)
print("XONG", flush=True)
