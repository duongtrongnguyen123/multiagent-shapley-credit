# H67 (dang ky truoc #72) — TREN CODE THUOC PHAI KHAC: V_std | V_first | V_cons | I
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
FIRST  = ("First write your OWN complete solution to the task and commit to it. ONLY AFTER that, "
          "read the proposed code below and decide which is right. "
          "Return ONLY the final code inside a ```python block.")
CONS   = ("Mentally run the proposed code against the given tests. If it is CORRECT, return it "
          "VERBATIM, unchanged, character for character. Only modify parts you can prove are wrong. "
          "Do NOT rewrite working code, do not restyle it, do not rename anything. "
          "Return ONLY the final code inside a ```python block.")

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
ARMS = {}
for name, sysm in [("V_std", REVIEW), ("V_first", FIRST), ("V_cons", CONS)]:
    ARMS[name] = [extract(t) for t in gen(m7, tk7, sysm, VP, 8)]
    print(f"{name} xong ({time.time()-t0:.0f}s)", flush=True)

PS, PI = grade(S), grade(I)
P = {k: grade(v) for k, v in ARMS.items()}
allc = S + I + [c for v in ARMS.values() for c in v]
comp = sum(compiles(c) for c in allc) / len(allc)
accS, accI = round(sum(PS)/N, 4), round(sum(PI)/N, 4)
FOLD = N // 5
def a(p, lo, hi): return sum(p[lo:hi]) / (hi - lo)
res = {"tag": RUN, "n": N, "S": accS, "I": accI, "I_minus_S": round(accI-accS, 4),
       "compile_rate": round(comp, 4), "arms": {}}
for k, code in ARMS.items():
    pv = P[k]; acc = round(sum(pv)/N, 4)
    pois = [i for i in range(N) if PI[i] and not pv[i]]
    kept = [i for i in pois if code[i].strip() == S[i].strip()]
    res["arms"][k] = {"acc": acc, "minus_I": round(acc-accI, 4),
        "minus_Vstd": round(acc - round(sum(P["V_std"])/N, 4), 4),
        "poisoned": len(pois), "rescued": sum(1 for i in range(N) if not PI[i] and pv[i]),
        "poisoned_kept_S": len(kept), "poisoned_third": len(pois)-len(kept),
        "unchanged_rate": round(sum(1 for i in range(N) if code[i].strip() == S[i].strip())/N, 4),
        "folds": [round(a(pv, f*FOLD, (f+1)*FOLD) - a(PI, f*FOLD, (f+1)*FOLD), 4) for f in range(5)]}
V = ARMS["V_std"]; accV = res["arms"]["V_std"]["acc"]
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "text": ALL[i]["text"][:400],
            "S": S[i][:1200], "I": I[i][:1200],
            **{k: ARMS[k][i][:1200] for k in ARMS},
            "pS": PS[i], "pI": PI[i], **{"p_"+k: P[k][i] for k in P}} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H67 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} ({'DAT' if comp>=.50 else 'HUY'}) | S={accS:.4f} | I={accI:.4f}")
print(f"  {'nhanh':8s} {'acc':>7s} {'-I':>8s} {'-V_std':>8s} {'doc/cuu':>9s} {'giu S/thu ba':>13s} {'unchanged':>10s}")
for k in ["V_std", "V_first", "V_cons"]:
    r = res["arms"][k]
    print(f"  {k:8s} {r['acc']:7.4f} {r['minus_I']:+8.4f} {r['minus_Vstd']:+8.4f} "
          f"{r['poisoned']:4d}/{r['rescued']:<4d} {r['poisoned_kept_S']:5d}/{r['poisoned_third']:<7d} {r['unchanged_rate']:10.4f}")
for k in ["V_std", "V_first", "V_cons"]:
    print(f"    fold {k}: {res['arms'][k]['folds']}")
g = res["arms"]["V_std"]["minus_I"]
dc = res["arms"]["V_cons"]["minus_Vstd"]; df = res["arms"]["V_first"]["minus_Vstd"]
ur = res["arms"]["V_cons"]["unchanged_rate"]
print(f"\n  cong tai lap H66: V_std - I = {g:+.4f} ({'DAT' if -.12 <= g <= -.03 else 'HUY'})")
print(f"  cong can thiep  : unchanged_rate(V_cons) = {ur:.4f} ({'DAT' if ur >= .20 else 'HUY nhanh V_cons — model KHONG nghe loi'})")
print(f"  V_cons - V_std = {dc:+.4f} | V_first - V_std = {df:+.4f} | V_cons - V_first = {dc-df:+.4f}")
print("\n-- bang khoa #72 --")
if not (-.12 <= g <= -.03): print("  -> HUY: khong tai lap duoc H66")
elif ur < .20: print("  -> HUY nhanh V_cons: can thiep khong xay ra")
elif dc >= .04 and (dc - df) >= .02:
    print("  -> HANG 1: CO CHE XAC NHAN — benh khac thi thuoc khac. Toan: cam ket truoc. Code: DUNG VIET LAI.")
elif dc >= .04 and df >= .04 and abs(dc-df) < .02:
    print("  -> HANG 2: hai can thiep khong phan biet duoc; lap luan co che cua toi SAI du ket qua duong.")
elif dc < .02:
    print("  -> HANG 3: trinh bay KHONG cuu duoc dau doc tren CODE (trai voi toan go 40-49%).")
else:
    print("  -> giua cac hang: ghi ro so, khong ep vao hang nao.")
if res["arms"]["V_cons"]["minus_I"] >= -.02:
    print("  -> them: V_cons ~ I. Chua gan het, NHUNG khi do V chi BANG I ma van DAT hon -> van nen goi thang I.")
print("XONG", flush=True)
