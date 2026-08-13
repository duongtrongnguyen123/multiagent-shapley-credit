# H76 (dang ky truoc #83) — DONG THUAN co hoat dong khi DA SO DUNG khong? (pool 8x7B)
# I = 7B tu viet | V_review = 7B review code cua 1.5B | SEL = 7B TU VIET TEST roi CHON giua hai ban
# CHONG RO RI: luot viet test CHI nhan mo ta, KHONG nhan test_list (test_list la BO CHAM).
import os, re, ast, json, glob, time, tempfile, subprocess, sys, gc, threading, torch
from concurrent.futures import ThreadPoolExecutor
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

RUN = "@@RUN@@"
TIDLO, TIDHI = 11, 510
MAXNEW, TIMEOUT = 512, 20

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}")
M7 = find_model("7b")
print(f"GPU={torch.cuda.get_device_name(0)} x{torch.cuda.device_count()}", flush=True)

DS = load_dataset("mbpp", "full", split="test+train+validation")
ALL = sorted([r for r in DS if TIDLO <= r["task_id"] <= TIDHI and len(r["test_list"]) >= 3],
             key=lambda r: r["task_id"])
N = len(ALL)
print(f"MBPP {TIDLO}-{TIDHI}: {N} bai", flush=True)
assert N >= 400

SOLVE  = "Write the Python function. Return ONLY code inside a ```python block. No explanation."
REVIEW = ("Review the code below against the task. If it is wrong or incomplete, fix it. "
          "Return ONLY the complete corrected code inside a ```python block.")
WTEST  = ("Write 5 Python assert statements that test the function described. "
          "Use EXACTLY the function name given. Return ONLY the assert lines inside a "
          "```python block, one per line, no function definition, no explanation.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def compiles(c):
    try: compile(c, "<s>", "exec"); return True
    except Exception: return False
def split_assert(a):
    """tach 'assert LOI_GOI == KY_VONG' bang AST -> tra LOI_GOI (bo ve ky vong)"""
    a = (a or "").strip()
    if not a.startswith("assert"): return None
    try: node = ast.parse(a[len("assert"):].strip(), mode="eval").body
    except Exception: return None
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
        return ast.unparse(node.left)
    return None

def run_outputs(code, calls):
    """chay code tren cac LOI GOI, tra chuoi dai dien dau ra (khong can biet dap an dung)"""
    if not code or not compiles(code) or not calls: return None
    prog = code + "\n\n_o=[]\n" + "".join(
        f"try:\n    _o.append(repr({c}))\nexcept Exception as _e:\n    _o.append('ERR:'+type(_e).__name__)\n"
        for c in calls) + "print('OUT<<'+chr(31).join(_o)+'>>')\n"
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        m = re.search(r"OUT<<(.*)>>", r.stdout or "", re.S)
        return m.group(1) if m else None
    except Exception: return None
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass

def clean_asserts(t):
    out = []
    for ln in extract(t).splitlines():
        ln = ln.strip()
        if ln.startswith("assert") and compiles(ln): out.append(ln)
    return out[:5]
def _run(code, checks, all_or_count):
    """all_or_count='all' -> True/False qua het; 'count' -> so check qua"""
    if not code or not compiles(code): return False if all_or_count == "all" else 0
    if all_or_count == "all":
        prog = code + "\n\n" + "\n".join(checks) + "\nprint('ALLOK')\n"
    else:
        prog = code + "\n\n_n=0\n" + "".join(
            f"try:\n    {c}\n    _n+=1\nexcept Exception:\n    pass\n" for c in checks
        ) + "print('CNT',_n)\n"
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        o = r.stdout or ""
        if all_or_count == "all": return "ALLOK" in o
        m = re.search(r"CNT (\d+)", o)
        return int(m.group(1)) if m else 0
    except Exception: return False if all_or_count == "all" else 0
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
def par(fn, args, w=8):
    with ThreadPoolExecutor(max_workers=w) as ex: return list(ex.map(lambda a: fn(*a), args))
# #74-c: CHAM CHI bang assert[1..2]; assert[0] da vao prompt lam vi du
def grade(codes): return par(_run, [(codes[i], ALL[i]["test_list"][1:3], "all") for i in range(N)])

BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
NG = torch.cuda.device_count(); DEVS = [f"cuda:{i}" for i in range(NG)]
def load(p, big):
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    mos = ([AutoModelForCausalLM.from_pretrained(p, quantization_config=BNB, device_map={"": d}).eval() for d in DEVS]
           if big else [AutoModelForCausalLM.from_pretrained(p, torch_dtype=torch.float16).to(d).eval() for d in DEVS])
    print(f"nap {'7B nf4' if big else '1.5B fp16'}: {len(mos)} ban sao", flush=True)
    return mos, tk
@torch.no_grad()
def _g1(mo, tk, sysm, usrs, bs, temp=0.0):
    outs, i = [], 0
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                  tokenize=False, add_generation_prompt=True) for u in ch]
            e = tk(ps, return_tensors="pt", padding=True).to(mo.device)
            o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=(temp>0), temperature=max(temp,1e-5),
                            top_p=0.95, pad_token_id=tk.pad_token_id)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs//2); print(f"  OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs
def gen(mos, tk, sysm, usrs, bs, temp=0.0):
    if len(mos) == 1: return _g1(mos[0], tk, sysm, usrs, bs, temp)
    parts = [list(range(j, len(usrs), len(mos))) for j in range(len(mos))]
    store, errs, lock = {}, [], threading.Lock()
    def work(mo, idxs):
        try:
            r = _g1(mo, tk, sysm, [usrs[i] for i in idxs], bs, temp)
            with lock: store.update(dict(zip(idxs, r)))
        except Exception as e:
            import traceback; traceback.print_exc()
            with lock: errs.append(e)
    ths = [threading.Thread(target=work, args=(mos[j], parts[j])) for j in range(len(mos)) if parts[j]]
    for t in ths: t.start()
    for t in ths: t.join()
    if errs: raise RuntimeError(errs[0])
    return [store[i] for i in range(len(usrs))]

PR   = [f"{r['text']}\n\nYour code must satisfy this test:\n{r['test_list'][0]}" for r in ALL]
# #106: bo test_list lam MAT TEN HAM -> model bia ten -> soundness .0523 -> HUY.
# Nay dua TEN HAM (trich tu test_list) nhung KHONG dua gia tri ky vong (do moi la bo cham).
def fname(r):
    for a in r["test_list"]:
        m = re.search(r"assert\s+\(?\s*([A-Za-z_]\w*)\s*\(", a)
        if m: return m.group(1)
    return None
FN = [fname(r) for r in ALL]
n_noname = sum(1 for f in FN if not f)
print(f"trich ten ham: {N-n_noname}/{N} bai (thieu {n_noname})", flush=True)
# #74-c: assert[0] lam VI DU NGU NGHIA (chi ten ham thi soundness chi .2580)
PRNT = [f"{ALL[i]['text']}\n\nExample test (shows the function name and expected behaviour):\n"
        f"{ALL[i]['test_list'][0]}" for i in range(N)]
t0 = time.time()

m7, tk7 = load(M7, True)
CANDS = [[extract(t) for t in gen(m7, tk7, SOLVE, PR, 8)]]      # cand 0 = greedy
print(f"cand 0 (greedy) xong ({time.time()-t0:.0f}s)", flush=True)
for kk in range(1, 8):
    CANDS.append([extract(t) for t in gen(m7, tk7, SOLVE, PR, 8, temp=0.8)])
    print(f"cand {kk} (T=0.8) xong ({time.time()-t0:.0f}s)", flush=True)
    json.dump({"partial": True, "n_cand": len(CANDS)}, open(f"/kaggle/working/partial_{RUN}.json", "w"))
I, I2 = CANDS[0], CANDS[1]
VREV = I
TESTS = [clean_asserts(t) for t in gen(m7, tk7, WTEST, PRNT, 8)]
print(f"test tu sinh xong ({time.time()-t0:.0f}s)", flush=True)

def nrm(s): return " ".join(s.split())
off = [set(nrm(x) for x in r["test_list"][1:3]) for r in ALL]
ngen = sum(len(t) for t in TESTS)
ncopy = sum(1 for i in range(N) for a in TESTS[i] if nrm(a) in off[i])
copy_rate = round(ncopy / max(ngen, 1), 4)
# MBPP dung truong 'code', KHONG phai 'solution' (da kiem tra schema truoc khi chay)
sound = par(_run, [(ALL[i]["code"], TESTS[i], "all") for i in range(N)])
soundness = round(sum(1 for i in range(N) if TESTS[i] and sound[i]) / max(sum(1 for t in TESTS if t), 1), 4)

CNT = [par(_run, [(c[i], TESTS[i], "count") for i in range(N)]) for c in CANDS]
PASS = [grade(c) for c in CANDS]

K = len(CANDS)
CALLS = [[c for c in (split_assert(a) for a in TESTS[i]) if c] for i in range(N)]
n_split = sum(len(c) for c in CALLS); n_ass = sum(len(t) for t in TESTS)
split_rate = round(n_split/max(n_ass,1), 4)
print(f"tach duoc loi goi: {n_split}/{n_ass} = {split_rate}", flush=True)
OUTS = [par(run_outputs, [(c[i], CALLS[i]) for i in range(N)]) for c in CANDS]

def sel(mode):
    out, picks = [], []
    for i in range(N):
        if mode == "test":
            sc = [CNT[j][i] for j in range(K)] if TESTS[i] else [0]*K
            b = sc.index(max(sc))
        else:
            groups = {}
            for j in range(K):
                o = OUTS[j][i]
                if o is None: continue
                groups.setdefault(o, []).append(j)
            if not groups: b = 0
            else:
                mx = max(len(v) for v in groups.values())
                cand = [j for v in groups.values() if len(v) == mx for j in v]
                if mode == "hyb" and len(cand) > 1:
                    b = max(cand, key=lambda j: (CNT[j][i] if TESTS[i] else -1, -j))
                else:
                    b = min(cand)
        out.append(CANDS[b][i]); picks.append(b)
    return out, picks

MODES = ["test", "cons", "hyb"]
RES = {}
a1 = round(sum(PASS[0])/N, 4)
union = round(sum(1 for i in range(N) if any(PASS[j][i] for j in range(K)))/N, 4)
for mo in MODES:
    code, picks = sel(mo)
    p = grade(code)
    g = union - a1
    acc = round(sum(p)/N, 4)
    RES[mo] = {"acc": acc, "ceiling": union, "minus_k1": round(acc-a1, 4),
               "captured_pct": round((acc-a1)/g*100, 1) if g > 1e-9 else None,
               "picks": {str(j): picks.count(j) for j in range(K)}, "cost": round(5.07*(K+1), 2)}

def nrm(s): return " ".join(s.split())
off = [set(nrm(x) for x in r["test_list"][1:3]) for r in ALL]
ngen = sum(len(t) for t in TESTS)
ncopy = sum(1 for i in range(N) for a in TESTS[i] if nrm(a) in off[i])
copy_rate = round(ncopy/max(ngen,1), 4)
sound = par(_run, [(ALL[i]["code"], TESTS[i], "all") for i in range(N)])
soundness = round(sum(1 for i in range(N) if TESTS[i] and sound[i])/max(sum(1 for t in TESTS if t),1), 4)
comp = sum(compiles(c) for cc in CANDS for c in cc)/(len(CANDS)*N)
res = {"tag": RUN, "n": N, "by_mode": RES, "split_rate": split_rate,
       "acc_each_cand": [round(sum(p)/N, 4) for p in PASS],
       "test_copy_rate": copy_rate, "test_soundness": soundness,
       "n_tests_gen": ngen, "compile_rate": round(comp, 4)}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "tests": TESTS[i],
            "cands": [c[i][:600] for c in CANDS], "pass": [p[i] for p in PASS],
            "cnt": [c[i] for c in CNT]} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H76 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} | soundness {soundness:.4f} | tach loi goi {split_rate:.4f}")
print(f"  acc tung ung vien: {res['acc_each_cand']}")
print(f"  {'bo chon':10s} {'acc':>7s} {'-cand0':>8s} {'tran':>7s} {'thu':>7s}")
for mo in MODES:
    r = RES[mo]
    cp = f"{r['captured_pct']:.0f}%" if r["captured_pct"] is not None else "   -"
    print(f"  SEL_{mo:6s} {r['acc']:7.4f} {r['minus_k1']:+8.4f} {r['ceiling']:7.4f} {cp:>7s}")
    print(f"      chon: {r['picks']}")
d = round(RES["cons"]["acc"] - RES["test"]["acc"], 4)
dh = round(RES["hyb"]["acc"] - max(RES["cons"]["acc"], RES["test"]["acc"]), 4)
print(f"\n  SEL_cons - SEL_test = {d:+.4f}   <-- DAI LUONG CHINH (#83)")
print(f"  SEL_hyb - max = {dh:+.4f}")
print("\n-- bang khoa #83 --")
if split_rate < .80 or soundness < .50 or copy_rate > .20: print("  -> HUY: cong truot")
elif not (.69 <= RES["test"]["acc"] <= .75): print(f"  -> HUY: SEL_test {RES['test']['acc']:.4f} ngoai [.69,.75], khong tai lap #117")
elif d >= .02: print("  -> HANG 1: CHAN DOAN #118 XAC NHAN. Dong thuan tot khi da so DUNG.")
elif abs(d) < .02: print("  -> HANG 2: dong thuan KHONG hon ke ca khi da so dung -> loi TUONG QUAN noi chung, chan doan #118 chua du.")
else: print("  -> HANG 3: dong thuan hai KE CA khi da so dung -> RUT LAI chan doan #118.")
if dh > .005: print("  -> them: SEL_hyb hon ca hai, hai tin hieu BO SUNG.")
if RES["cons"]["acc"] >= union - .01: print("  -> them: dong thuan gan het tran -> nut that chuyen han ve SINH.")
print("XONG", flush=True)
