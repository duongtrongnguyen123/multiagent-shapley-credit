# H69 (dang ky truoc #74) — CUNG HAI BAN CODE: CHON thay vi REVIEW.
# I = 7B tu viet | V_review = 7B review code cua 1.5B | SEL = 7B TU VIET TEST roi CHON giua hai ban
# CHONG RO RI: luot viet test CHI nhan mo ta, KHONG nhan test_list (test_list la BO CHAM).
import os, re, json, glob, time, tempfile, subprocess, sys, gc, threading, torch
from concurrent.futures import ThreadPoolExecutor
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

RUN = "@@RUN@@"
TIDLO, TIDHI = int("@@LO@@"), int("@@HI@@")
MAXNEW, TIMEOUT = 512, 20

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}")
M15, M7 = find_model("1-5b", "1_5b", "1.5b"), find_model("7b")
print(f"GPU={torch.cuda.get_device_name(0)} x{torch.cuda.device_count()}", flush=True)

DS = load_dataset("mbpp", "full", split="test+train+validation")
ALL = sorted([r for r in DS if TIDLO <= r["task_id"] <= TIDHI and len(r["test_list"]) >= 3],
             key=lambda r: r["task_id"])   # #74-c: can >=3 assert (1 lam vi du, 2 de cham)
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
# #74-c: CHAM CHI bang assert[1..2] — assert[0] da vao prompt lam vi du (giao thuc H56)
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
def _g1(mo, tk, sysm, usrs, bs):
    outs, i = [], 0
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                  tokenize=False, add_generation_prompt=True) for u in ch]
            e = tk(ps, return_tensors="pt", padding=True).to(mo.device)
            o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=False, pad_token_id=tk.pad_token_id)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs//2); print(f"  OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs
def gen(mos, tk, sysm, usrs, bs):
    if len(mos) == 1: return _g1(mos[0], tk, sysm, usrs, bs)
    parts = [list(range(j, len(usrs), len(mos))) for j in range(len(mos))]
    store, errs, lock = {}, [], threading.Lock()
    def work(mo, idxs):
        try:
            r = _g1(mo, tk, sysm, [usrs[i] for i in idxs], bs)
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
# #74-c: dua assert[0] lam VI DU NGU NGHIA (H56 dat soundness .8712 nho dieu nay).
# Chi assert[0]; assert[1..2] la phan GIU LAI de cham.
PRNT = [f"{ALL[i]['text']}\n\nExample test (shows the function name and expected behaviour):\n"
        f"{ALL[i]['test_list'][0]}" for i in range(N)]
t0 = time.time()

m15, tk15 = load(M15, False)
S = [extract(t) for t in gen(m15, tk15, SOLVE, PR, 24)]
for _m in m15: del _m
del m15; gc.collect(); torch.cuda.empty_cache()
print(f"S xong ({time.time()-t0:.0f}s)", flush=True)

m7, tk7 = load(M7, True)
I = [extract(t) for t in gen(m7, tk7, SOLVE, PR, 8)]
print(f"I xong ({time.time()-t0:.0f}s)", flush=True)
VREV = [extract(t) for t in gen(m7, tk7, REVIEW,
        [f"{PR[i]}\n\nProposed code:\n```python\n{S[i]}\n```" for i in range(N)], 8)]
print(f"V_review xong ({time.time()-t0:.0f}s)", flush=True)
TESTS = [clean_asserts(t) for t in gen(m7, tk7, WTEST, PRNT, 8)]
print(f"test tu sinh xong ({time.time()-t0:.0f}s)", flush=True)

def nrm(s): return " ".join(s.split())
off = [set(nrm(x) for x in r["test_list"][1:3]) for r in ALL]   # ro ri = chep trung PHAN CHAM
ngen = sum(len(t) for t in TESTS)
ncopy = sum(1 for i in range(N) for a in TESTS[i] if nrm(a) in off[i])
copy_rate = round(ncopy / max(ngen, 1), 4)
# MBPP dung truong 'code', KHONG phai 'solution' (da kiem tra schema truoc khi chay)
sound = par(_run, [(ALL[i]["code"], TESTS[i], "all") for i in range(N)])
soundness = round(sum(1 for i in range(N) if TESTS[i] and sound[i]) / max(sum(1 for t in TESTS if t), 1), 4)

cI = par(_run, [(I[i], TESTS[i], "count") for i in range(N)])
cS = par(_run, [(S[i], TESTS[i], "count") for i in range(N)])
SEL = [S[i] if (TESTS[i] and cS[i] > cI[i]) else I[i] for i in range(N)]
n_pick_S = sum(1 for i in range(N) if SEL[i] is S[i])

PS, PI, PV, PSEL = grade(S), grade(I), grade(VREV), grade(SEL)
comp = sum(compiles(c) for c in S+I+VREV+SEL) / (4*N)
A = lambda p: round(sum(p)/N, 4)
union = round(sum(1 for i in range(N) if PI[i] or PS[i]) / N, 4)
FOLD = N//5
f_ = lambda p, lo, hi: sum(p[lo:hi])/(hi-lo)
res = {"tag": RUN, "n": N, "S": A(PS), "I": A(PI), "V_review": A(PV), "SEL": A(PSEL),
       "ORACLE2_union": union,
       "SEL_minus_I": round(A(PSEL)-A(PI), 4), "SEL_minus_Vreview": round(A(PSEL)-A(PV), 4),
       "Vreview_minus_I": round(A(PV)-A(PI), 4),
       "test_copy_rate": copy_rate, "test_soundness": soundness,
       "n_tests_gen": ngen, "n_picked_S": n_pick_S, "n_no_fname": n_noname,
       "wrongly_dropped": sum(1 for i in range(N) if PS[i] and not PI[i] and SEL[i] is I[i]),
       "wrongly_taken": sum(1 for i in range(N) if PI[i] and not PS[i] and SEL[i] is S[i]),
       "compile_rate": round(comp, 4),
       "folds_SEL_minus_I": [round(f_(PSEL, k*FOLD, (k+1)*FOLD) - f_(PI, k*FOLD, (k+1)*FOLD), 4) for k in range(5)]}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "text": ALL[i]["text"][:300], "tests": TESTS[i],
            "S": S[i][:900], "I": I[i][:900], "V": VREV[i][:900],
            "cS": cS[i], "cI": cI[i], "picked": "S" if SEL[i] is S[i] else "I",
            "pS": PS[i], "pI": PI[i], "pV": PV[i], "pSEL": PSEL[i]} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H69 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} | test sinh {ngen} | chon ban cua S: {n_pick_S}")
print(f"  S={A(PS):.4f}  I={A(PI):.4f}  V_review={A(PV):.4f}  SEL={A(PSEL):.4f}  | TRAN(hop)={union:.4f}")
print(f"  SEL - I        = {res['SEL_minus_I']:+.4f}   <-- DAI LUONG CHINH (bang khoa #74)")
print(f"  SEL - V_review = {res['SEL_minus_Vreview']:+.4f}")
print(f"  V_review - I   = {res['Vreview_minus_I']:+.4f}   (cong tai lap H66)")
print(f"  fold SEL-I: {res['folds_SEL_minus_I']}")
print(f"  loai oan (S dung, I sai, van chon I): {res['wrongly_dropped']} | "
      f"lay nham (I dung, S sai, lai chon S): {res['wrongly_taken']}")
print(f"\n  CONG RO RI test_copy_rate = {copy_rate:.4f} ({'DAT' if copy_rate<=.20 else 'HUY nhanh SEL — RO RI'})")
print(f"  test_soundness = {soundness:.4f} ({'DAT' if soundness>=.50 else 'HUY'})")
g = res["Vreview_minus_I"]
print(f"  cong tai lap H66: {g:+.4f} ({'DAT' if -.12<=g<=-.03 else 'HUY'})")
print("\n-- bang khoa #74 --")
d, dv = res["SEL_minus_I"], res["SEL_minus_Vreview"]
if copy_rate > .20:        print("  -> HUY nhanh SEL: RO RI (test tu sinh chep tu bo cham)")
elif soundness < .50:      print("  -> HUY: test_soundness < .50")
elif not (-.12 <= g <= -.03): print("  -> HUY: khong tai lap duoc H66")
elif d >= .02:             print("  -> HANG 1: CHON THU DUOC gia tri ma REVIEW pha. Giao thuc thay the dung duoc ngay.")
elif dv >= .05:            print("  -> HANG 2: chon HON HAN review nhung KHONG hon goi thang model manh.")
elif abs(dv) < .05:        print("  -> HANG 3: chon khong hon review -> nut that la CHAT LUONG PHAN BIET cua test tu sinh.")
else:                      print("  -> HANG 4: chon CO HAI (test sai loai oan ban dung).")
print("XONG", flush=True)
