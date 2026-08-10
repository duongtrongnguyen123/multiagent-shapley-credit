# H51 (dang ky truoc #57) — 7B LAP KE HOACH, 1.5B THUC THI. Nap model TUAN TU.
# (dan xuat tu H50 / #56) — nhu H49 nhung CUONG CHE lap ke hoach o TANG SINH.
# (dan xuat tu H49 / #55) — LAP KE HOACH CO DANG MOT LUOT KHONG, KHI BAI DU DAI?
# BigCodeBench: prompt trung vi 607 ky tu, loi giai chuan 414 (MBPP: mot cau / ~3 dong).
# Bon nhanh, CUNG NGAN SACH 3 LUOT: greedy(1) | maj3(3) | seq(3) | PSV(3)
#   PSV vs seq khac DUNG mot dieu: luot dau dung de LAP KE HOACH hay de GIAI.
import os, re, json, glob, threading, tempfile, subprocess, sys, time, torch
from concurrent.futures import ThreadPoolExecutor
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes>=0.46.1"], check=False)
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

SHARD, NSHARD = @@SHARD@@, @@NSHARD@@
SIZE, RUN = "@@SIZE@@", "@@RUN@@"
N, MAXNEW, TEMP = 300, 768, 0.8
BS = 16 if SIZE == "15" else 6
TIMEOUT = 60

M15 = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors", recursive=True), key=len)[0])
M7  = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True), key=len)[0])
DS = load_dataset("bigcode/bigcodebench", split="v0.1.4")
ALL = [DS[i] for i in range(min(N, len(DS)))]
MINE = [i for i in range(len(ALL)) if i % NSHARD == SHARD]
print(f"M15={M15} M7={M7} | BigCodeBench {len(ALL)} bai | shard {SHARD}/{NSHARD}: {len(MINE)}", flush=True)

NG = torch.cuda.device_count(); DEVS = [f"cuda:{i}" for i in range(NG)]

SOLVE = ("Write the complete self-contained Python function. "
         "Return ONLY code inside a ```python block. No explanation.")
PLAN  = ("Reply with 3 to 6 numbered steps. Each step MUST be ONE sentence of plain prose "
         "describing what to do. Name libraries in prose if needed. Absolutely no code, "
         "no function definitions, no code blocks.")
FROMPLAN = ("Following the plan below, write the complete self-contained Python function. "
            "Return ONLY code inside a ```python block.")
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

def mktok(p):
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    return tk
TK = mktok(M15)          # tokenizer 1.5B (Qwen2.5 dung chung bo tu vung)
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

import gc
BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
PR = {i: task_text(ALL[i]) for i in MINE}
t0 = time.time()

# ---------- PHA 1: 7B LAP KE HOACH (cuong che), roi GIAI PHONG ----------
TK7 = mktok(M7)
_TK_SAVE = TK
TK = TK7
BAN = _ban_ids()
try:
    B7 = [AutoModelForCausalLM.from_pretrained(M7, quantization_config=BNB, device_map={"": d}).eval() for d in DEVS]
    QUANT7 = "nf4"
except Exception as e:
    print(f"nf4 that bai ({e}) -> fp16 auto", flush=True)
    B7 = [AutoModelForCausalLM.from_pretrained(M7, torch_dtype=torch.float16, device_map="auto").eval()]
    QUANT7 = "fp16-fallback"
print(f"7B: {len(B7)} ban sao | {QUANT7} | cam {len(BAN)} token rao code", flush=True)
BIGPLAN = pgen(B7, PLAN, PR, 0.0, 1, ban=BAN)
BG = pgen(B7, SOLVE, PR, 0.0, 1)                  # big_greedy — moc quan trong nhat
for m in B7: del m
del B7; gc.collect(); torch.cuda.empty_cache()
TK = _TK_SAVE
print(f"xong pha 1 ({time.time()-t0:.0f}s)", flush=True)

# ---------- PHA 2: 1.5B THUC THI ----------
S15 = [AutoModelForCausalLM.from_pretrained(M15, torch_dtype=torch.float16).to(d).eval() for d in DEVS]
print(f"1.5B: {len(S15)} ban sao", flush=True)
SG = pgen(S15, SOLVE, PR, 0.0, 1)                 # small_greedy
s1 = pgen(S15, SOLVE, PR, 0.0, 1)
s2i = {i: f"{PR[i]}\n\nA previous attempt:\n```python\n{extract(s1[i][0])}\n```\nWrite the correct complete code." for i in MINE}
s2 = pgen(S15, SOLVE, s2i, 0.0, 1)
s3i = {i: f"{PR[i]}\n\nCode:\n```python\n{extract(s2[i][0])}\n```" for i in MINE}
s3 = pgen(S15, REVIEW, s3i, 0.0, 1)               # small_seq
q2i = {i: f"{PR[i]}\n\nPlan:\n{strip_code(BIGPLAN[i][0])[:2000]}" for i in MINE}
q2 = pgen(S15, FROMPLAN, q2i, 0.0, 1)
q3i = {i: f"{PR[i]}\n\nCode:\n```python\n{extract(q2[i][0])}\n```" for i in MINE}
q3 = pgen(S15, REVIEW, q3i, 0.0, 1)               # bigplan_smallsolve
print(f"xong pha 2 ({time.time()-t0:.0f}s)", flush=True)

R_BG = run_many([(ALL[i], extract(BG[i][0])) for i in MINE])
R_SG = run_many([(ALL[i], extract(SG[i][0])) for i in MINE])
R_SS = run_many([(ALL[i], extract(s3[i][0]) or extract(s2[i][0])) for i in MINE])
R_BP = run_many([(ALL[i], extract(q3[i][0]) or extract(q2[i][0])) for i in MINE])
print(f"xong chay test ({time.time()-t0:.0f}s)", flush=True)

CAP = 3000
out = {"tag": f"{RUN}s{SHARD}", "shard": SHARD, "nshard": NSHARD, "task": "bigcodebench",
       "size": "mix", "quant": QUANT7, "n": len(MINE), "n_gpu": NG, "items": []}
for k_, i in enumerate(MINE):
    out["items"].append({
        "qi": i, "task_id": ALL[i]["task_id"],
        "big_greedy":         {"pass": R_BG[k_][0], "runs": R_BG[k_][1]},
        "small_greedy":       {"pass": R_SG[k_][0], "runs": R_SG[k_][1]},
        "small_seq":          {"pass": R_SS[k_][0], "runs": R_SS[k_][1]},
        "bigplan_smallsolve": {"pass": R_BP[k_][0], "runs": R_BP[k_][1]},
        "plan_text": BIGPLAN[i][0][:CAP],
        "bp_code": (extract(q3[i][0]) or extract(q2[i][0]))[:CAP],
    })
json.dump(out, open(f"/kaggle/working/res_{RUN}s{SHARD}.json", "w"))
print(f"DA LUU {len(out['items'])} bai -> res_{RUN}s{SHARD}.json", flush=True)
print("XONG", flush=True)
