# H83 (dang ky truoc #92) — diem thu BA cho cong thuc dinh tuyen: 1.5B->7B tren MBPP — DINH TUYEN HOP LY tren BigCodeBench, cheap=7B, strong=32B, bf16.
# S | I | V (32B xem code 7B) | ROUTE (7B tu viet test -> dat thi NHAN, truot thi leo thang 32B) | SEL
# Khong internet: BCB nap tu dataset JSON da stage san.
import os, re, json, glob, time, gc, tempfile, subprocess, sys, torch
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = "@@RUN@@"
N_TASK, MAXNEW, TIMEOUT = 340, 768, 60   # #88: loc giu ~.89 (267/300) -> 340 raw ~ 303 sau loc, du cong n>=280
BSZ = {"7B": 24, "32B": 16}
COST = {"7B": 1.0, "32B": 5.07}   # nguong hoa von = 1 - 1/5.07 = .803

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")
M = {"7B": find_model("1-5b", "1_5b", "1.5b"), "32B": find_model("2-5-7b", "qwen2-5-7b")}  # "7B"=tang re(1.5B), "32B"=tang dat(7B)
# T4 CO internet -> nap thang tu HF, khong can dataset private (loi H83 lan 1)
from datasets import load_dataset
_DS = load_dataset("mbpp", "full", split="test+train+validation")
CC = torch.cuda.get_device_capability(0); VRAM = torch.cuda.get_device_properties(0).total_memory/2**30
print(f"MODELS={json.dumps(M,indent=1)}\nGPU={torch.cuda.get_device_name(0)} | {VRAM:.1f} GB | sm_{CC[0]}{CC[1]}", flush=True)


RAWALL = [r for r in _DS if 11 <= r["task_id"] <= 510 and len(r["test_list"]) >= 3]
def canon(r): return r["code"]   # MBPP: truong "code" la loi giai day du

SOLVE = ("Write the complete self-contained Python function. "
         "Return ONLY code inside a ```python block. No explanation.")
REVIEW = ("Review the code below against the task. If it is wrong or incomplete, fix it. "
          "Return ONLY the complete corrected code inside a ```python block.")
WTEST = ("Write 4 Python assert statements that check the described function. "
         "Use the exact function name from the task. Return ONLY the assert lines inside a "
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
    return out[:4]

def _run(prog):
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        return (r.stdout or "") + (r.stderr or ""), r.returncode
    except Exception: return "", 1
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
def official_raw(rec, code):
    """chay unittest di kem cua BCB tren code DA HOAN CHINH"""
    if not code or not compiles(code): return False
    out, rc = _run(code + "\n\n" + "\n".join(rec["test_list"][1:3]) + "\nprint('ALLOK')\n")
    return "ALLOK" in out

def official(rec, code):
    """CHAM CHINH THUC cho code do model sinh (da tu chua import)"""
    if not code or not compiles(code): return False
    out, rc = _run(code + "\n\n" + "\n".join(rec["test_list"][1:3]) + "\nprint('ALLOK')\n")
    return "ALLOK" in out
def own_tests(code, asserts):
    """DAT test TU SINH cua 7B (khong phai bo cham)"""
    if not code or not compiles(code) or not asserts: return False
    out, rc = _run(code + "\n\n" + "\n".join(asserts) + "\nprint('ALLOK')\n")
    return "ALLOK" in out
def par(fn, args, w=8):
    with ThreadPoolExecutor(max_workers=w) as ex: return list(ex.map(lambda a: fn(*a), args))

BIG_CARD = (torch.cuda.get_device_properties(0).total_memory/2**30 >= 40)
if not BIG_CARD:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
    from transformers import BitsAndBytesConfig
    _BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
print(f"CHE DO: {'card lon -> bf16' if BIG_CARD else 'card nho -> nf4 cho model >=7B'}", flush=True)

def load(tag):
    p = M[tag]
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    if BIG_CARD:
        mo = AutoModelForCausalLM.from_pretrained(p, dtype=torch.bfloat16, device_map={"": 0}).eval()
    elif tag == "7B":   # tang re = 1.5B, vua fp16
        mo = AutoModelForCausalLM.from_pretrained(p, torch_dtype=torch.float16, device_map={"": 0}).eval()
    else:               # tang dat = 7B, PHAI nf4 tren T4 (bf16 = 15.2 GB > 14.56 GB)
        mo = AutoModelForCausalLM.from_pretrained(p, quantization_config=_BNB, device_map={"": 0}).eval()
    print(f"  nap {tag}: VRAM {torch.cuda.memory_allocated(0)/2**30:.1f} GB", flush=True)
    return mo, tk
def free(mo=None):
    """LUU Y: 'del mo' TRONG ham chi xoa TEN CUC BO — model van song o bien cua caller.
    Vi the caller PHAI gan mo=None TRUOC khi goi. Ham nay chi lam gc + empty_cache."""
    gc.collect()
    for d in range(torch.cuda.device_count()):
        with torch.cuda.device(d): torch.cuda.empty_cache()

@torch.no_grad()
def gen(mo, tk, sysm, usrs, bs):
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
            bs = max(1, bs//2); print(f"    OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs

# LOC nhu H52: chi giu bai ma LOI GIAI CHUAN dat test chinh thuc (8/40 truot vi moi truong)
t_f = time.time()
_ok = par(lambda r: official_raw(r, canon(r)), [(r,) for r in RAWALL], 8)
ALL = [r for r, o in zip(RAWALL, _ok) if o]
N = len(ALL)
print(f"loc chuan: {N}/{len(RAWALL)} bai co loi giai chuan DAT test ({time.time()-t_f:.0f}s)", flush=True)
if N < 280:
    print(f"HUY: n={N} < 280 (cong khoa #88)", flush=True)
    json.dump({"halt": "n_too_small", "n": N}, open(f"/kaggle/working/res_{RUN}.json", "w"))
    print("XONG", flush=True); raise SystemExit(0)

PR = [f"{r['text']}\n\nYour code must satisfy this test:\n{r['test_list'][0]}" for r in ALL]
def _snap(**kw):
    """#156: luu SAU MOI chang. Mot diem luu dat o CUOI = dung tuong 12h giua chung thi mat sach."""
    try:
        json.dump({"partial": True, "run": RUN, **kw},
                  open(f"/kaggle/working/partial_{RUN}.json", "w"))
        print(f"    [luu] {sorted(kw)}", flush=True)
    except Exception as _e:
        print(f"    [luu] LOI: {_e}", flush=True)

t0 = time.time()

mo, tk = load("7B")
S = [extract(t) for t in gen(mo, tk, SOLVE, PR, BSZ["7B"])]
print(f"S (7B) xong ({time.time()-t0:.0f}s)", flush=True)
_snap(**{k: v for k, v in list(globals().items()) if isinstance(v, list) and len(v) >= 10 and isinstance(v[0], (str, list, bool, int, float))})
TESTS = [clean_asserts(t) for t in gen(mo, tk, WTEST, PR, BSZ["7B"])]
print(f"test tu sinh xong ({time.time()-t0:.0f}s)", flush=True)
_snap(**{k: v for k, v in list(globals().items()) if isinstance(v, list) and len(v) >= 10 and isinstance(v[0], (str, list, bool, int, float))})
mo = None; tk = tk   # thao tham chieu cua CALLER truoc khi gc
free()
json.dump({"partial": 1, "S": S, "TESTS": TESTS}, open(f"/kaggle/working/partial_{RUN}.json", "w"))

# quyet dinh dinh tuyen: code cua 7B DAT test cua chinh no?
ACCEPT = par(own_tests, [(S[i], TESTS[i]) for i in range(N)])
p_esc = round(1 - sum(ACCEPT)/N, 4)
ESC = [i for i in range(N) if not ACCEPT[i]]
print(f"NHAN {sum(ACCEPT)}/{N} | leo thang {len(ESC)} (p_esc={p_esc})", flush=True)

mo, tk = load("32B")
I = [extract(t) for t in gen(mo, tk, SOLVE, PR, BSZ["32B"])]
print(f"I (32B) xong ({time.time()-t0:.0f}s)", flush=True)
_snap(**{k: v for k, v in list(globals().items()) if isinstance(v, list) and len(v) >= 10 and isinstance(v[0], (str, list, bool, int, float))})
V = [extract(t) for t in gen(mo, tk, REVIEW,
     [f"{PR[i]}\n\nProposed code:\n```python\n{S[i]}\n```" for i in range(N)], BSZ["32B"])]
print(f"V (32B xem code 7B) xong ({time.time()-t0:.0f}s)", flush=True)
_snap(**{k: v for k, v in list(globals().items()) if isinstance(v, list) and len(v) >= 10 and isinstance(v[0], (str, list, bool, int, float))})
mo = None; tk = tk   # thao tham chieu cua CALLER truoc khi gc
free()

ROUTE = [S[i] if ACCEPT[i] else I[i] for i in range(N)]
cI = par(own_tests, [(I[i], TESTS[i]) for i in range(N)])
SEL = [S[i] if (TESTS[i] and ACCEPT[i] and not cI[i]) else I[i] for i in range(N)]

PS, PI, PV, PR_, PSEL = (par(official, [(ALL[i], c[i]) for i in range(N)]) for c in (S, I, V, ROUTE, SEL))
sound = par(official_raw, [(ALL[i], canon(ALL[i])) for i in range(N)])   # phai la 1.0 sau khi loc
sound_own = par(own_tests, [(canon(ALL[i]), TESTS[i]) for i in range(N)])
A = lambda p: round(sum(p)/N, 4)
comp = round(sum(compiles(c) for c in S+I+V)/(3*N), 4)
cost_route = round(COST["7B"]*2 + p_esc*COST["32B"], 2)

res = {"tag": RUN, "n": N, "S": A(PS), "I": A(PI), "V": A(PV), "ROUTE": A(PR_), "SEL": A(PSEL),
       "V_minus_I": round(A(PV)-A(PI), 4), "ROUTE_minus_I": round(A(PR_)-A(PI), 4),
       "SEL_minus_I": round(A(PSEL)-A(PI), 4), "I_minus_S": round(A(PI)-A(PS), 4),
       "p_esc": p_esc, "cost": {"S": COST["7B"], "I": COST["32B"], "V": round(COST["7B"]+COST["32B"],2),
                                "ROUTE": cost_route, "SEL": round(COST["7B"]*2+COST["32B"],2)},
       "cost_ratio_ROUTE_over_I": round(cost_route/COST["32B"], 3),
       "accept_but_wrong": sum(1 for i in range(N) if ACCEPT[i] and not PS[i]),
       "test_soundness": round(sum(1 for i in range(N) if TESTS[i] and sound_own[i])/max(sum(1 for t in TESTS if t),1), 4),
       "official_on_canonical": A(sound), "compile_rate": comp,
       "agree_V_I": round(sum(1 for i in range(N) if V[i].strip()==I[i].strip())/N, 4),
       "agree_V_S": round(sum(1 for i in range(N) if V[i].strip()==S[i].strip())/N, 4)}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "tests": TESTS[i], "accept": ACCEPT[i],
            "S": S[i][:1200], "I": I[i][:1200], "V": V[i][:1200],
            "pS": PS[i], "pI": PI[i], "pV": PV[i], "pROUTE": PR_[i], "pSEL": PSEL[i]} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H79 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} | soundness {res['test_soundness']:.4f} | chuan chay duoc {res['official_on_canonical']:.4f}")
print(f"  {'nhanh':7s} {'acc':>7s} {'vs I':>8s} {'chi phi':>8s} {'/I':>6s}")
for k in ["S", "I", "V", "ROUTE", "SEL"]:
    print(f"  {k:7s} {res[k]:7.4f} {res[k]-res['I']:+8.4f} {res['cost'][k]:8.2f} {res['cost'][k]/COST['32B']:6.2f}")
print(f"\n  p_esc = {p_esc} | chi phi ROUTE / I = {res['cost_ratio_ROUTE_over_I']:.3f}")
print(f"  NHAN nham (7B dat test cua no nhung SAI that): {res['accept_but_wrong']}")
print(f"  agree(V,I) = {res['agree_V_I']:.4f} | agree(V,S) = {res['agree_V_S']:.4f}   [#87-b]")
print(f"  cong nang luc: I - S = {res['I_minus_S']:+.4f} ({'DAT' if res['I_minus_S']>=.05 else 'HUY'})")
print("\n-- bang khoa #88 --")
if res["I_minus_S"] < .05: print("  -> HUY: 32B khong hon 7B du .05 tren BCB")
elif res["test_soundness"] < .50 or comp < .50: print("  -> HUY: cong test/bien dich truot")
elif res["ROUTE_minus_I"] >= -.02 and res["cost_ratio_ROUTE_over_I"] < .80:
    print("  -> HANG 1: DINH TUYEN CO DIEU KIEN HOAT DONG tren code kho. H39 tong quat len 32B.")
elif res["ROUTE_minus_I"] >= -.02:
    print(f"  -> HANG 2: SUY BIEN — gan nhu luon leo thang (p_esc={p_esc}), khong tiet kiem.")
else:
    print(f"  -> HANG 3: dinh tuyen MAT chinh xac; nhan nham {res['accept_but_wrong']} bai.")
if res["V_minus_I"] <= -.02: print("  -> them: dau doc VAN am o 32B tren code kho — ban manh nhat cua ket qua chinh.")
else: print("  -> them: dau doc KHONG am o 32B -> doi chieu agree(V,I) vs agree(V,S) theo #87-b.")
print("XONG", flush=True)
