# H84 (dang ky truoc #93) — nguon CUNG CO khac ho (Llama-3.1-8B) vs nguon YEU (1.5B) — DAU DOC CO XAY RA TREN CODE KHONG?
# Y het H61, doi task: MBPP thay GSM8K. S=1.5B viet code | I=7B tu viet | V=7B xem code cua S.
# Dai luong CHINH = V - I (KHONG phai V - S). I re hon V -> I >= V la AP DAO HOAN TOAN.
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
M15 = find_model("1-5b", "1_5b", "1.5b")
MPEER = find_model("llama-3-1-8b", "llama-3.1-8b")
M7 = find_model("2-5-7b", "qwen2-5-7b")
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

def task(r): return f"{r['text']}\n\nYour code must satisfy:\n" + "\n".join(r["test_list"])
PR = [task(r) for r in ALL]
t0 = time.time()

m15, tk15 = load(M15, False)
S_RAW = gen(m15, tk15, SOLVE, PR, 24)
S = [extract(t) for t in S_RAW]
for _m in m15: del _m
del m15; gc.collect(); torch.cuda.empty_cache()
print(f"S (1.5B) xong ({time.time()-t0:.0f}s)", flush=True)

m7, tk7 = load(M7, True)
I_RAW = gen(m7, tk7, SOLVE, PR, 8)
I = [extract(t) for t in I_RAW]
print(f"I (7B tu viet) xong ({time.time()-t0:.0f}s)", flush=True)
VP = [f"{PR[i]}\n\nProposed code:\n```python\n{S[i]}\n```" for i in range(N)]
V = [extract(t) for t in gen(m7, tk7, REVIEW, VP, 8)]
print(f"V_weak xong ({time.time()-t0:.0f}s)", flush=True)
for _m in m7: del _m
del m7; gc.collect(); torch.cuda.empty_cache()
mp, tkp = load(MPEER, True)
PEER = [extract(t) for t in gen(mp, tkp, SOLVE, PR, 8)]
for _m in mp: del _m
del mp; gc.collect(); torch.cuda.empty_cache()
print(f"S_peer (Llama-8B) xong ({time.time()-t0:.0f}s)", flush=True)
m7, tk7 = load(M7, True)
VPP = [f"{PR[i]}\n\nProposed code:\n```python\n{PEER[i]}\n```" for i in range(N)]
VPEER = [extract(t) for t in gen(m7, tk7, REVIEW, VPP, 8)]
print(f"V_peer xong ({time.time()-t0:.0f}s)", flush=True)

PS, PI, PV = grade(S), grade(I), grade(V)
PPEER, PVPEER = grade(PEER), grade(VPEER)
comp = sum(compiles(c) for c in S + I + V) / (3*N)
accS, accI, accV = (round(sum(x)/N, 4) for x in (PS, PI, PV))
pois = [i for i in range(N) if PI[i] and not PV[i]]
resc = [i for i in range(N) if not PI[i] and PV[i]]
kept = [i for i in pois if V[i].strip() == S[i].strip()]
FOLD = N // 5
def a(p, lo, hi): return sum(p[lo:hi]) / (hi - lo)
res = {"tag": RUN, "n": N, "S": accS, "I": accI, "V": accV,
       "V_minus_I": round(accV-accI, 4), "V_minus_S": round(accV-accS, 4), "I_minus_S": round(accI-accS, 4),
       "poisoned": len(pois), "rescued": len(resc),
       "poisoned_kept_S_code": len(kept), "poisoned_third": len(pois)-len(kept),
       "compile_rate": round(comp, 4),
       "S_peer": round(sum(PPEER)/N,4), "V_peer": round(sum(PVPEER)/N,4),
       "Vpeer_minus_I": round(sum(PVPEER)/N - accI, 4),
       "folds_V_minus_I": [round(a(PV, f*FOLD, (f+1)*FOLD) - a(PI, f*FOLD, (f+1)*FOLD), 4) for f in range(5)]}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "text": ALL[i]["text"][:400],
            "S": S[i][:1200], "I": I[i][:1200], "V": V[i][:1200],
            "pS": PS[i], "pI": PI[i], "pV": PV[i]} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H66 TONG KET ====")
print(f"  n={N} | ti le bien dich {comp:.4f} ({'DAT' if comp>=.50 else 'HUY'})")
print(f"  S (1.5B viet)     = {accS:.4f}")
print(f"  I (7B tu viet)    = {accI:.4f}   <- NHANH DOI CHUNG, RE HON V")
print(f"  V (7B xem code S) = {accV:.4f}")
print(f"  V - S = {accV-accS:+.4f}   (con so ai cung bao cao)")
print(f"  V - I = {accV-accI:+.4f}   <-- DAI LUONG CHINH (bang khoa #71)")
print(f"  fold V-I: {res['folds_V_minus_I']}")
print(f"  bi dau doc {len(pois)} vs duoc cuu {len(resc)} | giu nguyen code sai cua S {len(kept)}, ban thu ba {len(pois)-len(kept)}")
print(f"  cong I-S = {accI-accS:+.4f} ({'DAT' if accI-accS>=.05 else 'HUY'})")
print(f"  S_peer (Llama-8B)  = {res['S_peer']:.4f}")
print(f"  V_peer (7B xem Llama) = {res['V_peer']:.4f}  -> V_peer - I = {res['Vpeer_minus_I']:+.4f}")
print("\n-- bang khoa #93 --")
vp = res["Vpeer_minus_I"]
if vp <= -.02: print("  -> HANG 1: DAU DOC KHONG CAN CHENH NANG LUC — van ban ngoai lai tu no gay hai.")
elif accV-accI <= -.05: print("  -> HANG 2: dau doc CAN nguon yeu; thu hep ve 'nguon KEM' chu khong phai 'NGOAI LAI'.")
else: print("  -> HANG 3: khong tai lap duoc dau doc -> HUY, kiem lai thiet lap.")
print("\n-- bang khoa #71 (doi chieu) --")
d = accV - accI
if accI-accS < .05: print("  -> HUY: bat doi xung khong thanh")
elif comp < .50:    print("  -> HUY: ti le bien dich duoi .50")
elif d <= -.02:     print("  -> HANG 1: DAU DOC TONG QUAT SANG CODE. Khong phai hien tuong cua toan.")
elif abs(d) < .02:  print("  -> HANG 2: dau doc KHONG tong quat sang code. Phai thu hep #99-#101 ve 'tren toan'.")
else:               print("  -> HANG 3: tren code doc code yeu CO ICH — nguoc dau voi toan.")
print("XONG", flush=True)
