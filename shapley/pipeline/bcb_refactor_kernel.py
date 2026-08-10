# H52 (dang ky truoc #58) — REFACTOR: giu nguyen hanh vi co can ORACLE that khong?
# (dan xuat tu H50 / #56) — nhu H49 nhung CUONG CHE lap ke hoach o TANG SINH.
# (dan xuat tu H49 / #55) — LAP KE HOACH CO DANG MOT LUOT KHONG, KHI BAI DU DAI?
# BigCodeBench: prompt trung vi 607 ky tu, loi giai chuan 414 (MBPP: mot cau / ~3 dong).
# Bon nhanh, CUNG NGAN SACH 3 LUOT: greedy(1) | maj3(3) | seq(3) | PSV(3)
#   PSV vs seq khac DUNG mot dieu: luot dau dung de LAP KE HOACH hay de GIAI.
import os, re, ast, json, glob, threading, tempfile, subprocess, sys, time, torch
from concurrent.futures import ThreadPoolExecutor
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes>=0.46.1"], check=False)
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

SHARD, NSHARD = @@SHARD@@, @@NSHARD@@
SIZE, RUN = "@@SIZE@@", "@@RUN@@"
N, MAXNEW, TEMP = 300, 768, 0.8
BS = 16 if SIZE == "15" else 6
TIMEOUT = 60

pat = "model.safetensors" if SIZE == "15" else "model.safetensors.index.json"
MODEL = os.path.dirname(sorted(glob.glob(f"/kaggle/input/**/{pat}", recursive=True), key=len)[0])
DS = load_dataset("bigcode/bigcodebench", split="v0.1.4")
ALL = [DS[i] for i in range(min(N, len(DS)))]
MINE = [i for i in range(len(ALL)) if i % NSHARD == SHARD]
print(f"MODEL={MODEL} | BigCodeBench {len(ALL)} bai | shard {SHARD}/{NSHARD}: {len(MINE)}", flush=True)

NG = torch.cuda.device_count(); DEVS = [f"cuda:{i}" for i in range(NG)]

SOLVE = ("Write the complete self-contained Python function. "
         "Return ONLY code inside a ```python block. No explanation.")
PLAN  = ("Reply with 3 to 6 numbered steps. Each step MUST be ONE sentence of plain prose "
         "describing what to do. Name libraries in prose if needed. Absolutely no code, "
         "no function definitions, no code blocks.")
FROMPLAN = ("Following the plan below, write the complete self-contained Python function. "
            "Return ONLY code inside a ```python block.")

REFAC = ("Refactor the code below to be simpler and more readable. "
         "The behaviour MUST NOT change: same inputs give the same outputs. "
         "Return ONLY the complete refactored code inside a ```python block.")
FIXERR = ("The refactored code below FAILED its tests. Here is the error. Fix it so the "
          "original behaviour is restored. Return ONLY complete code inside a ```python block.")
REVIEW = ("Review the code below against the task. If it is wrong or incomplete, fix it. "
          "Return ONLY the complete corrected code inside a ```python block.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def task_text(r): return r["instruct_prompt"]

def run_tests(r, code):
    """chay unittest di kem. Tra (dat, chay_duoc)."""
    if not code or not code.strip(): return False, False
    try: compile(code, "<s>", "exec"); ok_syntax = True
    except Exception: return False, False
    prog = code + "\n\n" + r["test"] + "\n\nimport unittest\nunittest.main(argv=['x'],exit=False,verbosity=0)\n"
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        res = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        out = (res.stdout or "") + (res.stderr or "")
        passed = (re.search(r"^OK", out, re.M) is not None) or ("FAILED" not in out and res.returncode == 0)
        return bool(passed), ok_syntax
    except subprocess.TimeoutExpired: return False, ok_syntax
    except Exception: return False, ok_syntax
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
def run_many(pairs):
    with ThreadPoolExecutor(max_workers=6) as ex:
        return list(ex.map(lambda a: run_tests(*a), pairs))


def nodes_of(code):
    try: return sum(1 for _ in ast.walk(ast.parse(code)))
    except Exception: return None
def run_tests_err(r, code):
    """nhu run_tests nhung tra ve ca stderr de sua theo oracle"""
    ok, _ = run_tests(r, code)
    if ok: return True, ""
    if not code or not code.strip(): return False, "empty"
    prog = code + "\n\n" + r["test"] + "\n\nimport unittest\nunittest.main(argv=['x'],exit=False,verbosity=0)\n"
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        res = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        return False, ((res.stdout or "") + (res.stderr or ""))[-500:]
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:200]}"
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass

def mktok(p):
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    return tk
TK = mktok(MODEL)
FENCE = "`" * 3
def _ban_ids():
    """id cua cac token chua dau rao code -> cam sinh trong luot lap ke hoach"""
    ids = set()
    for t in (FENCE, "\n" + FENCE, FENCE + "python", "``", "`"):
        e = TK(t, add_special_tokens=False)["input_ids"]
        if len(e) == 1: ids.add(e[0])
    return [[i] for i in ids]
BAN = None
def strip_code(p):
    """cat an toan: bo moi khoi rao va moi dong dinh nghia ham"""
    p = re.sub(r"```.*?```", " ", p or "", flags=re.S)
    p = re.sub(r"```", " ", p)
    p = "\n".join(l for l in p.splitlines() if not re.search(r"\bdef\s+\w+\s*\(", l))
    return p.strip()
def _chunk(m, sysm, ch, temp, ban=None):
    ps = [TK.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
          tokenize=False, add_generation_prompt=True) for u in ch]
    e = TK(ps, return_tensors="pt", padding=True).to(m.device)
    with torch.no_grad():
        kw = dict(max_new_tokens=MAXNEW, do_sample=(temp > 0), temperature=max(temp, 1e-5),
                  top_p=0.95, pad_token_id=TK.pad_token_id)
        if ban: kw["bad_words_ids"] = ban
        o = m.generate(**e, **kw)
    L = e["input_ids"].shape[1]
    r = [TK.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    del e, o
    return r
def gen(m, sysm, usrs, temp, ban=None):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i+BS]; cur = len(ch)
        while True:
            try:
                for j in range(0, len(ch), cur): outs += _chunk(m, sysm, ch[j:j+cur], temp, ban)
                break
            except torch.OutOfMemoryError:
                torch.cuda.empty_cache()
                if cur == 1: raise
                cur = max(1, cur // 2); outs = outs[:i]
                print(f"  OOM -> lo {cur}", flush=True)
    return outs
def pgen(models, sysm, by_idx, temp, rounds, ban=None):
    keys = list(by_idx.keys()); parts = [keys[j::len(models)] for j in range(len(models))]
    store, lock, errs = {}, threading.Lock(), []
    def work(m, sub):
        try:
            loc = {i: [] for i in sub}
            for _ in range(rounds):
                for i, o in zip(sub, gen(m, sysm, [by_idx[i] for i in sub], temp, ban)): loc[i].append(o)
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

BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
try:
    MS = [AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=BNB, device_map={"": d}).eval() for d in DEVS]
    QUANT = "nf4"
except Exception as e:
    print(f"nf4 that bai ({e}) -> fp16 auto", flush=True)
    MS = [AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto").eval()]
    QUANT = "fp16-fallback"
print(f"{len(MS)} ban sao | {QUANT}", flush=True)
t0 = time.time()

ORIG = {i: ALL[i]["complete_prompt"] + ALL[i]["canonical_solution"] for i in MINE}
base = run_many([(ALL[i], ORIG[i]) for i in MINE])
KEEP = [i for k, i in enumerate(MINE) if base[k][0]]
print(f"loi giai chuan dat test: {len(KEEP)}/{len(MINE)} -> chi refactor nhung bai nay", flush=True)

REQ = {i: "Task: " + task_text(ALL[i])[:900] + "\n\nCode:\n```python\n" + ORIG[i] + "\n```" for i in KEEP}
R1 = pgen(MS, REFAC, REQ, 0.0, 1)
c1 = {i: extract(R1[i][0]) for i in KEEP}
sv = {i: "Task: " + task_text(ALL[i])[:900] + "\n\nRefactored code:\n```python\n" + c1[i] + "\n```" for i in KEEP}
R2 = pgen(MS, REVIEW, sv, 0.0, 1)
c_seq = {i: (extract(R2[i][0]) or c1[i]) for i in KEEP}
chk = {i: run_tests_err(ALL[i], c1[i]) for i in KEEP}
BAD = [i for i in KEEP if not chk[i][0]]
print(f"ref1 lam HONG {len(BAD)}/{len(KEEP)} -> sua theo oracle", flush=True)
c_exec = dict(c1)
if BAD:
    fx = {i: "Task: " + task_text(ALL[i])[:600] + "\n\nCode:\n```python\n" + c1[i] + "\n```\n\nError:\n" + chk[i][1][:600] for i in BAD}
    R3 = pgen(MS, FIXERR, fx, 0.0, 1)
    for i in BAD: c_exec[i] = extract(R3[i][0]) or c1[i]
print(f"xong sinh ({time.time()-t0:.0f}s)", flush=True)

P1 = run_many([(ALL[i], c1[i]) for i in KEEP])
PS = run_many([(ALL[i], c_seq[i]) for i in KEEP])
PE = run_many([(ALL[i], c_exec[i]) for i in KEEP])
print(f"xong chay test ({time.time()-t0:.0f}s)", flush=True)

CAP = 3000
out = {"tag": f"{RUN}s{SHARD}", "shard": SHARD, "nshard": NSHARD, "task": "refactor-bcb",
       "size": SIZE, "quant": QUANT, "n": len(KEEP), "n_gpu": NG, "items": []}
for k_, i in enumerate(KEEP):
    out["items"].append({
        "qi": i, "task_id": ALL[i]["task_id"],
        "nodes_orig": nodes_of(ORIG[i]),
        "ref1":     {"pass": P1[k_][0], "nodes": nodes_of(c1[i])},
        "ref_seq":  {"pass": PS[k_][0], "nodes": nodes_of(c_seq[i])},
        "ref_exec": {"pass": PE[k_][0], "nodes": nodes_of(c_exec[i])},
        "ref1_broke": not chk[i][0],
        "code_ref1": c1[i][:CAP],
    })
json.dump(out, open(f"/kaggle/working/res_{RUN}s{SHARD}.json", "w"))
print(f"DA LUU {len(out['items'])} bai -> res_{RUN}s{SHARD}.json", flush=True)
print("XONG", flush=True)
