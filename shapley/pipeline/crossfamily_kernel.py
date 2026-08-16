# H80 (dang ky truoc #89) — DA DANG HO MODEL vs DA DANG LAY MAU, cung chi phi.
# Pool A: Q1(greedy) + Q2(T=.8) + Q3(T=.8)      <- da dang LAY MAU (mot ho)
# Pool B: Q1(greedy) + L(greedy) + D(greedy)    <- da dang HO (ba ho)
# Bo chon GIU NGUYEN cho ca hai (test tu sinh do Q viet, mot lan) => khac biet duy nhat la POOL.
import os, re, ast, json, glob, time, gc, tempfile, subprocess, sys, torch
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = "@@RUN@@"
TIDLO, TIDHI = int("@@LO@@"), int("@@HI@@")
MAXNEW, TIMEOUT = 512, 20
BS = 24

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")
M = {"Q": find_model("2-5-7b", "qwen2-5-7b"),
     "L": find_model("llama-3-1-8b", "llama-3.1-8b", "llama3-1-8b"),
     "D": find_model("deepseek-coder-6-7b", "deepseek-coder-6.7b")}
CC = torch.cuda.get_device_capability(0); VRAM = torch.cuda.get_device_properties(0).total_memory/2**30
print(f"MODELS={json.dumps(M,indent=1)}\nGPU={torch.cuda.get_device_name(0)} | {VRAM:.1f} GB | sm_{CC[0]}{CC[1]}", flush=True)

# khong internet tren RTX 6000 -> MBPP nap tu dataset JSON da stage
# dataset private KHONG mount duoc sang tai khoan khac (push van thanh cong) -> fallback HF.
_hits = sorted(glob.glob("/kaggle/input/**/mbpp_full.json", recursive=True), key=len)
if _hits:
    DS = json.load(open(_hits[0]))
else:
    print("khong mount duoc mbpp_full.json -> nap tu HuggingFace", flush=True)
    from datasets import load_dataset
    _D = load_dataset("mbpp", "full", split="test+train+validation")
    DS = [{k: r[k] for k in ["task_id","text","code","test_list"]} for r in _D]
ALL = sorted([r for r in DS if TIDLO <= r["task_id"] <= TIDHI and len(r["test_list"]) >= 3],
             key=lambda r: r["task_id"])
N = len(ALL)
print(f"MBPP {TIDLO}-{TIDHI}: {N} bai", flush=True)
assert N >= 400

SOLVE = "Write the Python function. Return ONLY code inside a ```python block. No explanation."
WTEST = ("Write 5 Python assert statements that check the described function. "
         "Use EXACTLY the function name given. Return ONLY the assert lines inside a "
         "```python block, one per line, no function definition, no explanation.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def compiles(c):
    try: compile(c, "<s>", "exec"); return True
    except Exception: return False
def clean_asserts(t):
    out = []
    for ln in extract(t).splitlines():
        ln = ln.strip()
        if ln.startswith("assert") and compiles(ln): out.append(ln)
    return out[:5]
def _run(code, checks, mode):
    if not code or not compiles(code): return False if mode == "all" else 0
    if not checks: return False if mode == "all" else 0
    if mode == "all":
        prog = code + "\n\n" + "\n".join(checks) + "\nprint('ALLOK')\n"
    else:
        prog = code + "\n\n_n=0\n" + "".join(
            f"try:\n    {c}\n    _n+=1\nexcept Exception:\n    pass\n" for c in checks) + "print('CNT',_n)\n"
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        o = r.stdout or ""
        if mode == "all": return "ALLOK" in o
        m = re.search(r"CNT (\d+)", o)
        return int(m.group(1)) if m else 0
    except Exception: return False if mode == "all" else 0
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
def par(fn, args, w=8):
    with ThreadPoolExecutor(max_workers=w) as ex: return list(ex.map(lambda a: fn(*a), args))
def grade(codes): return par(_run, [(codes[i], ALL[i]["test_list"][1:3], "all") for i in range(N)])

def load(tag):
    p = M[tag]
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    mo = AutoModelForCausalLM.from_pretrained(p, dtype=torch.bfloat16, device_map={"": 0}).eval()
    print(f"  nap {tag}: VRAM {torch.cuda.memory_allocated(0)/2**30:.1f} GB", flush=True)
    return mo, tk
def free(mo):
    del mo; gc.collect()
    for d in range(torch.cuda.device_count()):
        with torch.cuda.device(d): torch.cuda.empty_cache()

@torch.no_grad()
def gen(mo, tk, sysm, usrs, bs, temp=0.0):
    outs, i = [], 0
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                  tokenize=False, add_generation_prompt=True) for u in ch]
            e = tk(ps, return_tensors="pt", padding=True).to(mo.device)
            o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=(temp > 0),
                            temperature=max(temp, 1e-5), top_p=0.95, pad_token_id=tk.pad_token_id)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs//2); print(f"    OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs

PR = [f"{r['text']}\n\nYour code must satisfy this test:\n{r['test_list'][0]}" for r in ALL]
t0 = time.time()
CODE, RAW = {}, {}

mo, tk = load("Q")
CODE["Q1"] = [extract(t) for t in gen(mo, tk, SOLVE, PR, BS)]
CODE["Q2"] = [extract(t) for t in gen(mo, tk, SOLVE, PR, BS, temp=0.8)]
CODE["Q3"] = [extract(t) for t in gen(mo, tk, SOLVE, PR, BS, temp=0.8)]
TESTS = [clean_asserts(t) for t in gen(mo, tk, WTEST, PR, BS)]   # bo chon: CHI do Q viet
free(mo)
print(f"Q xong ({time.time()-t0:.0f}s)", flush=True)
json.dump({"partial": True, "raw": {k: v for k, v in CODE.items()}, "TESTS": TESTS},
          open(f"/kaggle/working/partial_{RUN}.json", "w"))

for tag in ["L", "D"]:
    mo, tk = load(tag)
    CODE[tag] = [extract(t) for t in gen(mo, tk, SOLVE, PR, BS)]
    free(mo)
    print(f"{tag} xong ({time.time()-t0:.0f}s)", flush=True)
    json.dump({"partial": True, "raw": {k: v for k, v in CODE.items()}, "TESTS": TESTS},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))

PASS = {k: grade(v) for k, v in CODE.items()}
CNT = {k: par(_run, [(v[i], TESTS[i], "cnt") for i in range(N)]) for k, v in CODE.items()}
A = lambda p: round(sum(p)/N, 4)

def analyse(pool):
    union = sum(1 for i in range(N) if any(PASS[k][i] for k in pool)) / N
    sel, ties = [], 0
    for i in range(N):
        sc = [CNT[k][i] for k in pool] if TESTS[i] else [0]*len(pool)
        mx = max(sc)
        if sc.count(mx) == len(pool): ties += 1
        sel.append(PASS[pool[sc.index(mx)]][i])
    base = A(PASS[pool[0]])
    g = union - base
    from collections import Counter
    dist = Counter(sum(PASS[k][i] for k in pool) for i in range(N))
    return {"acc_each": {k: A(PASS[k]) for k in pool}, "base": base,
            "H": round(union, 4), "SEL": round(sum(sel)/N, 4),
            "H_minus_base": round(g, 4), "SEL_minus_base": round(sum(sel)/N - base, 4),
            "kappa": round((sum(sel)/N - base)/g*100, 1) if g > 1e-9 else None,
            "tie_rate": round(ties/N, 4),
            "dist_n_correct": {str(c): dist.get(c, 0) for c in range(len(pool)+1)},
            "all_wrong": dist.get(0, 0), "all_right": dist.get(len(pool), 0),
            "mixed": N - dist.get(0, 0) - dist.get(len(pool), 0)}

POOLS = {"A_sampling": ["Q1", "Q2", "Q3"], "B_family": ["Q1", "L", "D"]}
RES = {k: analyse(v) for k, v in POOLS.items()}

def nrm(s): return " ".join(s.split())
off = [set(nrm(x) for x in r["test_list"][1:3]) for r in ALL]
ngen = sum(len(t) for t in TESTS)
copy_rate = round(sum(1 for i in range(N) for a in TESTS[i] if nrm(a) in off[i])/max(ngen,1), 4)
sound = par(_run, [(ALL[i]["code"], TESTS[i], "all") for i in range(N)])
soundness = round(sum(1 for i in range(N) if TESTS[i] and sound[i])/max(sum(1 for t in TESTS if t),1), 4)
comp = round(sum(compiles(c) for v in CODE.values() for c in v)/(len(CODE)*N), 4)

res = {"tag": RUN, "n": N, "pools": RES, "test_copy_rate": copy_rate,
       "test_soundness": soundness, "compile_rate": comp,
       "H_diff": round(RES["B_family"]["H"] - RES["A_sampling"]["H"], 4),
       "SEL_diff": round(RES["B_family"]["SEL"] - RES["A_sampling"]["SEL"], 4)}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "tests": TESTS[i],
            **{k: CODE[k][i][:800] for k in CODE}, **{"p_"+k: PASS[k][i] for k in PASS},
            **{"c_"+k: CNT[k][i] for k in CNT}} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H80 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} | soundness {soundness:.4f} | copy_rate {copy_rate:.4f}")
print(f"  acc tung model: " + "  ".join(f"{k}={A(PASS[k]):.4f}" for k in CODE))
for name, r in RES.items():
    print(f"\n  --- pool {name} ---")
    print(f"    acc ung vien: {r['acc_each']}")
    print(f"    TRAN H = {r['H']:.4f} (+{r['H_minus_base']:.4f})  |  SEL = {r['SEL']:.4f} (+{r['SEL_minus_base']:.4f})  |  kappa = {r['kappa']}%")
    print(f"    phan bo so ung vien dung: {r['dist_n_correct']}  (cung sai {r['all_wrong']} / cung dung {r['all_right']} / hon hop {r['mixed']})")
    print(f"    tie_rate = {r['tie_rate']:.4f}")
hd, sd = res["H_diff"], res["SEL_diff"]
print(f"\n  H(B) - H(A)   = {hd:+.4f}   <-- DAI LUONG CHINH (#89)")
print(f"  SEL(B) - SEL(A) = {sd:+.4f}")
mn = min(A(PASS[k]) for k in CODE)
print(f"  cong: acc thap nhat = {mn:.4f} ({'DAT' if mn >= .35 else 'HUY — mot model sup'})")
print("\n-- bang khoa #89 --")
if mn < .35: print("  -> HUY: co model duoi .35")
elif soundness < .50 or copy_rate > .20 or comp < .50: print("  -> HUY: cong test/bien dich truot")
elif hd >= .05 and sd >= .02: print("  -> HANG 1: M2 XAC NHAN MANH. Tron HO re hon nhieu so voi them mau.")
elif hd >= .05: print("  -> HANG 2: tran len nhung bo chon KHONG khai thac duoc (kappa tut). M2 dung ve H, sai ve kappa.")
elif abs(hd) < .05: print("  -> HANG 3: M2 SAI/YEU -> RUT LAI giai thich 'loi tuong quan'. Rang buoc nam o DO KHO cua BAI.")
else: print("  -> HANG 4: tron ho HAI tran. Kiem acc tung model truoc khi tin.")
if RES["B_family"]["SEL"] > RES["A_sampling"]["H"]:
    print("  -> them: SEL(B) vuot ca TRAN cua pool cung ho — ket qua rat manh.")
print("XONG", flush=True)
