# H55 (dang ky truoc #61) — VERIFIER TU VIET TEST, solver cai dat, chay test tu sinh.
# (dan xuat tu H42 / #48) — DINH TUYEN TREN CODE (MBPP), shard @@SHARD@@/@@NSHARD@@.
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
RUN = "@@RUN@@"
TID_LO, TID_HI = @@TIDLO@@, @@TIDHI@@
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
    if not (TID_LO <= tid <= TID_HI): continue    # dai task_id do nguoi goi chon
    t = r.get("test_list") or []
    if len(t) < 3: continue
    call = split_assert(t[0])
    if call is None: continue                     # 2/500 bai khong tach duoc -> bo, ghi ro
    ALL.append({"tid": tid, "text": r["text"], "setup": r.get("test_setup_code") or "",
                "a0": t[0], "a1": t[1], "a2": t[2], "call": call,
                "gold_code": r.get("code") or ""})
ALL.sort(key=lambda x: x["tid"])
print(f"sau khi loc: {len(ALL)} bai dung (task_id {TID_LO}-{TID_HI})", flush=True)
assert len(ALL) >= 400, f"du lieu hong: chi con {len(ALL)}"

MINE = [i for i in range(len(ALL)) if i % NSHARD == SHARD]
print(f"shard {SHARD}/{NSHARD}: {len(MINE)} bai", flush=True)

NG = torch.cuda.device_count(); DEVS = [f"cuda:{i}" for i in range(NG)]
print(f"so GPU={NG}", flush=True)

SOLVE = ("Complete the Python function. Return the COMPLETE function including the signature, "
         "inside a ```python code block. No explanation.")

WRITE_TESTS = ("Write 3 to 5 Python assert statements that check the described function. "
               "Use the exact function name from the given example test. "
               "Return ONLY the assert lines, one per line, no code block, no explanation.")
IMPL = ("Write the complete Python function. Return ONLY code inside a ```python block.")
FIXT = ("The code below FAILED one of these tests. Fix the code so all tests pass. "
        "Return ONLY the complete corrected function inside a ```python block.")
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

def clean_asserts(t):
    """chi giu cac dong assert hop le ve cu phap"""
    out = []
    for ln in (t or "").splitlines():
        ln = ln.strip().strip("`")
        if not ln.startswith("assert"): continue
        try: ast.parse(ln)
        except Exception: continue
        out.append(ln)
    return out[:5]
def run_asserts(x, code, asserts):
    """chay code + cac assert TU SINH. Tra (dat_het, so_dat, stderr)"""
    if not code or not asserts: return False, 0, "empty"
    body = code + "\n\n" + (x["setup"] or "") + "\n"
    n_ok = 0; err = ""
    prog = body + "\n".join(f"try:\n    {a}\n    print('@@OK@@')\nexcept Exception as _e:\n    print('@@NG@@', type(_e).__name__, _e)" for a in asserts)
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        out = (r.stdout or "")
        n_ok = out.count("@@OK@@")
        err = "\n".join(l for l in out.splitlines() if "@@NG@@" in l)[:400]
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)[:150]}"
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
    return (n_ok == len(asserts) and n_ok > 0), n_ok, err

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
BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
try:
    MS = [AutoModelForCausalLM.from_pretrained(M7, quantization_config=BNB, device_map={"": d}).eval() for d in DEVS]
    QUANT = "nf4"
except Exception as e:
    print(f"nf4 that bai ({e}) -> fp16 auto", flush=True)
    MS = [AutoModelForCausalLM.from_pretrained(M7, torch_dtype=torch.float16, device_map="auto").eval()]
    QUANT = "fp16-fallback"
print(f"{len(MS)} ban sao | {QUANT}", flush=True)

# --- VAI VERIFIER: tu viet test (KHONG duoc thay assert[1..2]) ---
TQ = {i: f"{ALL[i]['text']}\n\nExample test (for the function name):\n{ALL[i]['a0']}" for i in MINE}
TG = parallel_gen(MS, T7, WRITE_TESTS, TQ, BSB, 0.0, 1)
GEN = {i: clean_asserts(TG[i][0]) for i in MINE}
print("so assert tu sinh TB:", round(sum(len(v) for v in GEN.values())/max(len(MINE),1), 2), flush=True)

# --- CONG HIEU LUC: test tu sinh co dung khong? (loi giai chuan phai DAT) ---
SOUND = {i: run_asserts(ALL[i], ALL[i].get("gold_code",""), GEN[i]) for i in MINE} if False else {}
# MBPP co truong 'code' = loi giai chuan
SOUND = {i: run_asserts(ALL[i], ALL[i]["gold_code"], GEN[i]) for i in MINE}

# --- solve1 / maj3 (mocs, giong #88) ---
S1 = parallel_gen(MS, T7, SOLVE, PR, BSB, 0.0, 1)
MJ = parallel_gen(MS, T7, SOLVE, PR, BSB, TEMP, 3)

# --- TDD: cai dat -> chay test TU SINH -> sua ---
IQ = {i: f"{PR[i]}\n\nYour code must also satisfy these tests:\n" + "\n".join(GEN[i]) for i in MINE}
D1 = parallel_gen(MS, T7, IMPL, IQ, BSB, 0.0, 1)
d1c = {i: extract(D1[i][0]) for i in MINE}
chk = {i: run_asserts(ALL[i], d1c[i], GEN[i]) for i in MINE}
BADT = [i for i in MINE if GEN[i] and not chk[i][0]]
print(f"TDD: {len(BADT)}/{len(MINE)} truot test tu sinh -> sua", flush=True)
tdd = dict(d1c)
if BADT:
    FQ = {i: f"{PR[i]}\n\nTests:\n" + "\n".join(GEN[i]) + f"\n\nCode:\n```python\n{d1c[i]}\n```\n\nFailures:\n{chk[i][2][:400]}" for i in BADT}
    D2 = parallel_gen(MS, T7, FIXT, FQ, BSB, 0.0, 1)
    for i in BADT: tdd[i] = extract(D2[i][0]) or d1c[i]

# --- TDD_noexec: thay test nhung KHONG chay -> tu nhan xet ---
NQ = {i: f"{PR[i]}\n\nCode:\n```python\n{d1c[i]}\n```" for i in MINE}
D3 = parallel_gen(MS, T7, REVIEW, NQ, BSB, 0.0, 1)
tdd_ne = {i: (extract(D3[i][0]) or d1c[i]) for i in MINE}
print("xong sinh", flush=True)

P_S1 = probe_many([(ALL[i], extract(S1[i][0])) for i in MINE])
P_MJ = [probe_many([(ALL[i], extract(MJ[i][k])) for i in MINE]) for k in range(3)]
P_TD = probe_many([(ALL[i], tdd[i]) for i in MINE])
P_NE = probe_many([(ALL[i], tdd_ne[i]) for i in MINE])
P_D1 = probe_many([(ALL[i], d1c[i]) for i in MINE])
print("xong chay thu", flush=True)

CAP = 4000
out = {"tag": f"{RUN}s{SHARD}", "shard": SHARD, "nshard": NSHARD, "task": "mbpp-tdd",
       "quant": QUANT, "n": len(MINE), "n_gpu": NG, "items": []}
K4 = ("out", "a0", "held", "compiles")
for k_, i in enumerate(MINE):
    out["items"].append({
        "qi": i, "tid": ALL[i]["tid"],
        "n_gen_tests": len(GEN[i]),
        "gen_tests": GEN[i],
        "sound_all": SOUND[i][0], "sound_n": SOUND[i][1],
        "solve1":    {k2: P_S1[k_][k2] for k2 in K4},
        "samp":      [{k2: P_MJ[k][k_][k2] for k2 in K4} for k in range(3)],
        "tdd_impl":  {k2: P_D1[k_][k2] for k2 in K4},
        "tdd":       {k2: P_TD[k_][k2] for k2 in K4},
        "tdd_noexec":{k2: P_NE[k_][k2] for k2 in K4},
        "gen_pass_impl": chk[i][0],
    })
json.dump(out, open(f"/kaggle/working/res_H43s{SHARD}.json", "w"))
print(f"DA LUU {len(out['items'])} bai -> res_H43s{SHARD}.json", flush=True)
print("XONG", flush=True)
