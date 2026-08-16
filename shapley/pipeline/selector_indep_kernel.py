# H81 (dang ky truoc #90) — BO CHON co can DOC LAP VE HO khong? — DA DANG HO MODEL vs DA DANG LAY MAU, cung chi phi.
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
     "D": find_model("deepseek-coder-6-7b", "deepseek-coder-6.7b")}
CC = torch.cuda.get_device_capability(0); VRAM = torch.cuda.get_device_properties(0).total_memory/2**30
print(f"MODELS={json.dumps(M,indent=1)}\nGPU={torch.cuda.get_device_name(0)} | {VRAM:.1f} GB | sm_{CC[0]}{CC[1]}", flush=True)

# khong internet tren RTX 6000 -> MBPP nap tu dataset JSON da stage
MB = sorted(glob.glob("/kaggle/input/**/mbpp_full.json", recursive=True), key=len)[0]
DS = json.load(open(MB))
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
T_self = [clean_asserts(t) for t in gen(mo, tk, WTEST, PR, BS)]   # test do CHINH Qwen viet
free(mo)
print(f"Q xong ({time.time()-t0:.0f}s)", flush=True)
json.dump({"partial": True, "raw": CODE, "T_self": T_self},
          open(f"/kaggle/working/partial_{RUN}.json", "w"))

mo, tk = load("D")
T_other = [clean_asserts(t) for t in gen(mo, tk, WTEST, PR, BS)]   # test do HO KHAC viet
free(mo)
print(f"T_other (DeepSeek) xong ({time.time()-t0:.0f}s)", flush=True)
json.dump({"partial": True, "raw": CODE, "T_self": T_self, "T_other": T_other},
          open(f"/kaggle/working/partial_{RUN}.json", "w"))

PASS = {k: grade(v) for k, v in CODE.items()}
POOL = ["Q1", "Q2"]
A = lambda p: round(sum(p)/N, 4)

def run_sel(TESTS, lab):
    CNT = {k: par(_run, [(CODE[k][i], TESTS[i], "cnt") for i in range(N)]) for k in POOL}
    sel = []
    for i in range(N):
        sc = [CNT[k][i] for k in POOL] if TESTS[i] else [0]*len(POOL)
        sel.append(PASS[POOL[sc.index(max(sc))]][i])
    def nrm(x): return " ".join(x.split())
    off = [set(nrm(x) for x in ALL[i]["test_list"][1:3]) for i in range(N)]
    ng = sum(len(t) for t in TESTS)
    cr = round(sum(1 for i in range(N) for a in TESTS[i] if nrm(a) in off[i])/max(ng,1), 4)
    sd = par(_run, [(ALL[i]["code"], TESTS[i], "all") for i in range(N)])
    snd = round(sum(1 for i in range(N) if TESTS[i] and sd[i])/max(sum(1 for t in TESTS if t),1), 4)
    base = A(PASS["Q1"])
    union = sum(1 for i in range(N) if any(PASS[k][i] for k in POOL))/N
    return {"lab": lab, "SEL": round(sum(sel)/N, 4), "SEL_minus_base": round(sum(sel)/N-base, 4),
            "soundness": snd, "copy_rate": cr, "n_tests": ng,
            "H": round(union, 4), "kappa": round((sum(sel)/N-base)/(union-base)*100, 1) if union > base else None}

RS, RO = run_sel(T_self, "T_self(Qwen)"), run_sel(T_other, "T_other(DeepSeek)")
comp = round(sum(compiles(c) for v in CODE.values() for c in v)/(len(CODE)*N), 4)
res = {"tag": RUN, "n": N, "acc_each": {k: A(PASS[k]) for k in CODE}, "base": A(PASS["Q1"]),
       "T_self": RS, "T_other": RO, "compile_rate": comp,
       "diff": round(RO["SEL"] - RS["SEL"], 4)}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "T_self": T_self[i], "T_other": T_other[i],
            **{k: CODE[k][i][:800] for k in CODE}, **{"p_"+k: PASS[k][i] for k in PASS}} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H81 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} | acc: {res['acc_each']}")
for r in (RS, RO):
    print(f"  {r['lab']:20s} SEL={r['SEL']:.4f} (+{r['SEL_minus_base']:.4f})  kappa={r['kappa']}%  "
          f"soundness={r['soundness']:.4f}  copy={r['copy_rate']:.4f}  n_test={r['n_tests']}")
d = res["diff"]
print(f"\n  SEL(T_other) - SEL(T_self) = {d:+.4f}   <-- DAI LUONG CHINH (#90)")
print("\n-- bang khoa #90 --")
if RO["soundness"] < .50: print("  -> HUY nhanh T_other: soundness < .50")
elif RS["soundness"] < .50 or max(RS["copy_rate"], RO["copy_rate"]) > .20: print("  -> HUY: cong truot")
elif d >= .02: print("  -> HANG 1: M2 XAC NHAN o phia BO CHON. Tin hieu phai doc lap ve HO.")
elif abs(d) < .02: print("  -> HANG 2: doc lap ve ho KHONG cai thien kappa. Thu hep M2 ve pool.")
else: print("  -> HANG 3: test cua ho khac TE HON -> kappa phu thuoc KHOP PHONG CACH, nguoc M2.")
print("XONG", flush=True)
