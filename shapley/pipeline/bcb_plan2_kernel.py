# H50 (dang ky truoc #56) — nhu H49 nhung CUONG CHE lap ke hoach o TANG SINH.
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

PR = {i: task_text(ALL[i]) for i in MINE}
t0 = time.time()
GRE = pgen(MS, SOLVE, PR, 0.0, 1)                    # 1 luot — thuoc do bao hoa
SMP = pgen(MS, SOLVE, PR, TEMP, 3)                   # maj3
# seq: giai -> giai lai -> tu kiem
s1 = pgen(MS, SOLVE, PR, 0.0, 1)
s2i = {i: f"{PR[i]}\n\nA previous attempt:\n```python\n{extract(s1[i][0])}\n```\nWrite the correct complete code." for i in MINE}
s2 = pgen(MS, SOLVE, s2i, 0.0, 1)
s3i = {i: f"{PR[i]}\n\nCode:\n```python\n{extract(s2[i][0])}\n```" for i in MINE}
s3 = pgen(MS, REVIEW, s3i, 0.0, 1)
# PSV: lap ke hoach (KHONG code) -> giai theo ke hoach -> tu kiem
BAN = _ban_ids()
print(f"cam {len(BAN)} token rao code khi lap ke hoach", flush=True)
p1 = pgen(MS, PLAN, PR, 0.0, 1, ban=BAN)
p2i = {i: f"{PR[i]}\n\nPlan:\n{strip_code(p1[i][0])[:2000]}" for i in MINE}
p2 = pgen(MS, FROMPLAN, p2i, 0.0, 1)
p3i = {i: f"{PR[i]}\n\nCode:\n```python\n{extract(p2[i][0])}\n```" for i in MINE}
p3 = pgen(MS, REVIEW, p3i, 0.0, 1)
print(f"xong sinh ({time.time()-t0:.0f}s)", flush=True)

RG = run_many([(ALL[i], extract(GRE[i][0])) for i in MINE])
RS = [run_many([(ALL[i], extract(SMP[i][k])) for i in MINE]) for k in range(3)]
RQ = run_many([(ALL[i], extract(s3[i][0]) or extract(s2[i][0])) for i in MINE])
RP = run_many([(ALL[i], extract(p3[i][0]) or extract(p2[i][0])) for i in MINE])
print(f"xong chay test ({time.time()-t0:.0f}s)", flush=True)

CAP = 3000
out = {"tag": f"{RUN}s{SHARD}", "shard": SHARD, "nshard": NSHARD, "task": "bigcodebench",
       "size": SIZE, "quant": QUANT, "n": len(MINE), "n_gpu": NG, "items": []}
for k_, i in enumerate(MINE):
    out["items"].append({
        "qi": i, "task_id": ALL[i]["task_id"],
        "greedy": {"pass": RG[k_][0], "runs": RG[k_][1]},
        "samp":   [{"pass": RS[j][k_][0], "runs": RS[j][k_][1]} for j in range(3)],
        "seq":    {"pass": RQ[k_][0], "runs": RQ[k_][1]},
        "psv":    {"pass": RP[k_][0], "runs": RP[k_][1]},
        "plan_text": p1[i][0][:CAP],
        "seq_code": (extract(s3[i][0]) or extract(s2[i][0]))[:CAP],
        "psv_code": (extract(p3[i][0]) or extract(p2[i][0]))[:CAP],
    })
json.dump(out, open(f"/kaggle/working/res_{RUN}s{SHARD}.json", "w"))
print(f"DA LUU {len(out['items'])} bai -> res_{RUN}s{SHARD}.json", flush=True)
print("XONG", flush=True)
