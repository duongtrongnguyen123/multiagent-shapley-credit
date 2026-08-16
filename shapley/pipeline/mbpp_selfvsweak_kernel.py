# H68 (dang ky truoc #73) — DOC VI NGUON YEU, HAY DOC VI CHE DO SUA CHUA?
# I = 7B tu viet (sang tac) | V_self = 7B sua code CUA CHINH NO | V_weak = 7B sua code cua 1.5B
# V_self vs V_weak: CUNG che do sua chua, khac DUNG mot dieu — code do la cua ai.
import os, re, json, glob, time, tempfile, subprocess, sys, gc, torch
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
print(f"M15={M15}\nM7={M7}\nGPU={torch.cuda.get_device_name(0)} "
      f"sm_{torch.cuda.get_device_capability(0)[0]}{torch.cuda.get_device_capability(0)[1]} "
      f"x{torch.cuda.device_count()}", flush=True)

DS = load_dataset("mbpp", "full", split="test+train+validation")
ALL = [r for r in DS if TIDLO <= r["task_id"] <= TIDHI]
ALL = sorted(ALL, key=lambda r: r["task_id"])
N = len(ALL)
print(f"MBPP {TIDLO}-{TIDHI}: {N} bai", flush=True)
assert N >= 400, f"chi {N} bai"

SOLVE  = ("Write the Python function. Return ONLY code inside a ```python block. No explanation.")
REVIEW = ("Review the code below against the task. If it is wrong or incomplete, fix it. "
          "Return ONLY the complete corrected code inside a ```python block.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def compiles(c):
    try: compile(c, "<s>", "exec"); return True
    except Exception: return False
def run_asserts(rec, code):
    if not code or not code.strip() or not compiles(code): return False
    prog = code + "\n\n" + "\n".join(rec["test_list"]) + "\nprint('ALLOK')\n"
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        return "ALLOK" in (r.stdout or "")
    except Exception: return False
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
def grade(codes):
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(lambda a: run_asserts(*a), [(ALL[i], codes[i]) for i in range(N)]))

BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
NG = torch.cuda.device_count(); DEVS = [f"cuda:{i}" for i in range(NG)]
def load(p, big):
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    if big:
        mos = [AutoModelForCausalLM.from_pretrained(p, quantization_config=BNB, device_map={"": d}).eval() for d in DEVS]
    else:
        mos = [AutoModelForCausalLM.from_pretrained(p, torch_dtype=torch.float16).to(d).eval() for d in DEVS]
    print(f"nap {'7B nf4' if big else '1.5B fp16'}: {len(mos)} ban sao | "
          f"VRAM {torch.cuda.memory_allocated()/2**30:.1f} GB", flush=True)
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
    import threading
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
    if len(store) != len(usrs): raise RuntimeError("thieu dau ra")
    return [store[i] for i in range(len(usrs))]

def _free_models(mos):
    """#134: 'for _m in mos: del _m' chi xoa BIEN VONG LAP — khong ha refcount cua model.
    Gan tung phan tu = None thi cat duoc lien ket du ai dang giu cai list."""
    if mos:
        try:
            for _i in range(len(mos)): mos[_i] = None
        except TypeError: pass
    gc.collect()
    for _d in range(torch.cuda.device_count()):
        with torch.cuda.device(_d): torch.cuda.empty_cache()

def task(r): return f"{r['text']}\n\nYour code must satisfy:\n" + "\n".join(r["test_list"])
PR = [task(r) for r in ALL]
t0 = time.time()

m15, tk15 = load(M15, False)
S_RAW = gen(m15, tk15, SOLVE, PR, 24)
S = [extract(t) for t in S_RAW]
_free_models(m15); m15 = None; gc.collect()
for _d in range(torch.cuda.device_count()):
    with torch.cuda.device(_d): torch.cuda.empty_cache()
print(f"S (1.5B) xong ({time.time()-t0:.0f}s)", flush=True)

m7, tk7 = load(M7, True)
I_RAW = gen(m7, tk7, SOLVE, PR, 8)
I = [extract(t) for t in I_RAW]
print(f"I (7B tu viet) xong ({time.time()-t0:.0f}s)", flush=True)
VP_weak = [f"{PR[i]}\n\nProposed code:\n```python\n{S[i]}\n```" for i in range(N)]
VP_self = [f"{PR[i]}\n\nProposed code:\n```python\n{I[i]}\n```" for i in range(N)]
V_weak = [extract(t) for t in gen(m7, tk7, REVIEW, VP_weak, 8)]
print(f"V_weak xong ({time.time()-t0:.0f}s)", flush=True)
V_self = [extract(t) for t in gen(m7, tk7, REVIEW, VP_self, 8)]
print(f"V_self xong ({time.time()-t0:.0f}s)", flush=True)

PS, PI = grade(S), grade(I)
PW, PSF = grade(V_weak), grade(V_self)
allc = S + I + V_weak + V_self
comp = sum(compiles(c) for c in allc) / len(allc)
accS, accI = round(sum(PS)/N, 4), round(sum(PI)/N, 4)
accW, accSF = round(sum(PW)/N, 4), round(sum(PSF)/N, 4)
FOLD = N // 5
def a(p, lo, hi): return sum(p[lo:hi]) / (hi - lo)
def blk(pv, code, ref):
    pois = [i for i in range(N) if PI[i] and not pv[i]]
    kept = [i for i in pois if code[i].strip() == ref[i].strip()]
    return {"acc": round(sum(pv)/N, 4), "minus_I": round(sum(pv)/N - accI, 4),
            "poisoned": len(pois), "rescued": sum(1 for i in range(N) if not PI[i] and pv[i]),
            "poisoned_kept": len(kept), "poisoned_third": len(pois)-len(kept),
            "unchanged_rate": round(sum(1 for i in range(N) if code[i].strip() == ref[i].strip())/N, 4),
            "folds": [round(a(pv, f*FOLD, (f+1)*FOLD) - a(PI, f*FOLD, (f+1)*FOLD), 4) for f in range(5)]}
res = {"tag": RUN, "n": N, "S": accS, "I": accI, "I_minus_S": round(accI-accS, 4),
       "compile_rate": round(comp, 4),
       "V_weak": blk(PW, V_weak, S), "V_self": blk(PSF, V_self, I)}
res["self_minus_weak"] = round(accSF - accW, 4)
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "text": ALL[i]["text"][:400],
            "S": S[i][:1000], "I": I[i][:1000], "V_weak": V_weak[i][:1000], "V_self": V_self[i][:1000],
            "pS": PS[i], "pI": PI[i], "pW": PW[i], "pSF": PSF[i]} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H68 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} ({'DAT' if comp>=.50 else 'HUY'})")
print(f"  S  (1.5B viet)            = {accS:.4f}")
print(f"  I  (7B TU viet, sang tac) = {accI:.4f}")
print(f"  V_self (7B sua code CUA NO)  = {accSF:.4f}  ({res['V_self']['minus_I']:+.4f} vs I)  "
      f"unchanged {res['V_self']['unchanged_rate']:.4f}")
print(f"  V_weak (7B sua code 1.5B)    = {accW:.4f}  ({res['V_weak']['minus_I']:+.4f} vs I)  "
      f"unchanged {res['V_weak']['unchanged_rate']:.4f}")
print(f"  fold V_self: {res['V_self']['folds']}")
print(f"  fold V_weak: {res['V_weak']['folds']}")
print(f"  V_self - V_weak = {res['self_minus_weak']:+.4f}   <-- TACH NGUON khoi CHE DO")
g = res["V_weak"]["minus_I"]
print(f"\n  cong tai lap H66: V_weak - I = {g:+.4f} ({'DAT' if -.12 <= g <= -.03 else 'HUY'})")
print(f"  cong I-S = {accI-accS:+.4f} ({'DAT' if accI-accS>=.05 else 'HUY'})")
print("\n-- bang khoa #73 --")
ds, dw, diff = res["V_self"]["minus_I"], g, abs(accSF-accW)
if not (-.12 <= g <= -.03): print("  -> HUY: khong tai lap duoc H66")
elif ds <= -.03 and diff < .03:
    print("  -> HANG 1: THU PHAM LA CHE DO SUA CHUA, KHONG PHAI NGUON.")
    print("     PHAI RUT LAI cach dien giai 'dau doc' o #99-#103 (so giu nguyen).")
elif abs(ds) < .02 and dw <= -.03:
    print("  -> HANG 2: NGUON moi la thu pham. Cau chuyen dau doc DUNG VUNG, nay co doi chung chat.")
elif ds < 0 and dw < 0 and (accSF - accW) >= .03:
    print("  -> HANG 3: CA HAI deu gop. Che do sua chua hai mot phan, nguon ngoai lai hai them.")
    print(f"     phan cua CHE DO = {ds:+.4f} | phan THEM cua NGUON = {accW-accSF:+.4f}")
elif ds >= .02: print("  -> HANG 4: tu review CO ICH tren code — bat ngo, phai tai lap truoc khi tin.")
else: print("  -> giua cac hang: ghi ro so, khong ep.")
print("XONG", flush=True)
