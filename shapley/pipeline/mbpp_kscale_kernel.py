# H73 (dang ky truoc #79) — LOI ICH CUA CHON CO TANG THEO SO UNG VIEN k KHONG?
# I = 7B tu viet | V_review = 7B review code cua 1.5B | SEL = 7B TU VIET TEST roi CHON giua hai ban
# CHONG RO RI: luot viet test CHI nhan mo ta, KHONG nhan test_list (test_list la BO CHAM).
import os, re, json, glob, time, tempfile, subprocess, sys, gc, threading, torch
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

def sel_at(k):
    """chon trong k ung vien dau; hoa -> giu cand 0 (greedy)"""
    out, ties = [], 0
    for i in range(N):
        scores = [CNT[j][i] for j in range(k)] if TESTS[i] else [0]*k
        best = max(scores)
        if scores.count(best) == k: ties += 1
        out.append(CANDS[scores.index(best)][i])
    return out, ties

KS = [1, 2, 4, 8]
RES = {}
for k in KS:
    code, ties = sel_at(k)
    p = grade(code)
    union = sum(1 for i in range(N) if any(PASS[j][i] for j in range(k))) / N
    RES[k] = {"acc": round(sum(p)/N, 4), "ceiling": round(union, 4),
              "tie_rate": round(ties/N, 4), "cost": round(5.07*(k+1), 2)}
a1 = RES[1]["acc"]
for k in KS:
    g = RES[k]["ceiling"] - a1
    RES[k]["minus_k1"] = round(RES[k]["acc"] - a1, 4)
    RES[k]["captured_pct"] = round(RES[k]["minus_k1"]/g*100, 1) if g > 1e-9 else None

def nrm(s): return " ".join(s.split())
off = [set(nrm(x) for x in r["test_list"][1:3]) for r in ALL]
ngen = sum(len(t) for t in TESTS)
ncopy = sum(1 for i in range(N) for a in TESTS[i] if nrm(a) in off[i])
copy_rate = round(ncopy/max(ngen,1), 4)
sound = par(_run, [(ALL[i]["code"], TESTS[i], "all") for i in range(N)])
soundness = round(sum(1 for i in range(N) if TESTS[i] and sound[i])/max(sum(1 for t in TESTS if t),1), 4)
comp = sum(compiles(c) for cc in CANDS for c in cc)/(len(CANDS)*N)
res = {"tag": RUN, "n": N, "by_k": {str(k): RES[k] for k in KS},
       "acc_each_cand": [round(sum(p)/N, 4) for p in PASS],
       "test_copy_rate": copy_rate, "test_soundness": soundness,
       "n_tests_gen": ngen, "compile_rate": round(comp, 4)}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "tests": TESTS[i],
            "cands": [c[i][:600] for c in CANDS], "pass": [p[i] for p in PASS],
            "cnt": [c[i] for c in CNT]} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H73 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} | soundness {soundness:.4f} | copy_rate {copy_rate:.4f}")
print(f"  acc tung ung vien: {res['acc_each_cand']}")
print(f"  {'k':>3s} {'SEL@k':>8s} {'-k=1':>8s} {'tran':>8s} {'thu':>7s} {'tie_rate':>9s} {'chi phi':>8s}")
for k in KS:
    r = RES[k]
    cp = f"{r['captured_pct']:.0f}%" if r["captured_pct"] is not None else "   -"
    print(f"  {k:3d} {r['acc']:8.4f} {r['minus_k1']:+8.4f} {r['ceiling']:8.4f} {cp:>7s} {r['tie_rate']:9.4f} {r['cost']:8.2f}")
d82 = round(RES[8]["acc"] - RES[2]["acc"], 4)
c82 = round(RES[8]["ceiling"] - RES[2]["ceiling"], 4)
mono = RES[8]["acc"] >= RES[4]["acc"] >= RES[2]["acc"]
print(f"\n  SEL@8 - SEL@2 = {d82:+.4f}   <-- DAI LUONG CHINH (#79)")
print(f"  tran@8 - tran@2 = {c82:+.4f} | tang deu theo k? {'CO' if mono else 'KHONG'}")
print(f"  tie_rate: k=2 {RES[2]['tie_rate']:.4f} -> k=8 {RES[8]['tie_rate']:.4f}")
print("\n-- bang khoa #79 --")
if soundness < .50 or copy_rate > .20: print("  -> HUY: cong test truot")
elif not (.60 <= RES[1]["acc"] <= .68): print("  -> HUY: acc(SEL@1) ngoai [.60,.68]")
elif d82 >= .02 and mono: print("  -> HANG 1: k LA DON BAY. #111-b duoc xac nhan, nut that la tran pool.")
elif abs(d82) < .02 and c82 >= .04: print("  -> HANG 3: DAO LAI #111-b — o k lon BO CHON moi la nut that. Phai rut lai #111-b.")
elif abs(d82) < .02: print("  -> HANG 2: k KHONG phai don bay. Nut that nam o ban than viec SINH.")
else: print("  -> giua cac hang: ghi ro so, khong ep.")
if RES[8]["tie_rate"] >= RES[2]["tie_rate"] - .05:
    print("  -> them: tie_rate KHONG giam ro -> co che neu o #111-b SAI.")
print("XONG", flush=True)
