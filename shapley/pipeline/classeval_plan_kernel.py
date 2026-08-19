# H64 (dang ky truoc #69) — LAP KE HOACH CO DANG KHONG KHI SAN PHAM DU DAI?
# ClassEval: 100 lop, 4.1 method/lop, loi giai TB 1334 ky tu (3.2x BigCodeBench).
# Ba nhanh: solve1(1 luot) | seq3(giai->sua->sua, KHONG vai) | PSV(ke hoach->giai->tu kiem, CO vai)
# Dai luong CHINH = PSV - seq3 (cung 3 luot, khac dung mot dieu: luot dau LAP KE HOACH hay GIAI)
# Phep thu QUYET DINH = dap ung theo lieu qua 3 nhom do dai.
import os, re, ast, json, glob, threading, tempfile, subprocess, sys, time, torch
from concurrent.futures import ThreadPoolExecutor
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes>=0.46.1"], check=False)
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

SIZE, RUN = "@@SIZE@@", "@@RUN@@"
N, MAXNEW = 100, 1024
BS = 12 if SIZE == "15" else 4
TIMEOUT = 30

pat = "model.safetensors" if SIZE == "15" else "model.safetensors.index.json"
MODEL = os.path.dirname(sorted(glob.glob(f"/kaggle/input/**/{pat}", recursive=True), key=len)[0])
DS = load_dataset("FudanSELab/ClassEval", split="test")
ALL = [DS[i] for i in range(min(N, len(DS)))]
IDX = list(range(len(ALL)))
NMETH = sum(len(r["methods_info"]) for r in ALL)
print(f"MODEL={MODEL} | ClassEval {len(ALL)} lop, {NMETH} method", flush=True)

NG = torch.cuda.device_count(); DEVS = [f"cuda:{i}" for i in range(NG)]

SOLVE = ("Implement every method of the Python class below. Keep the class name, method names and "
         "signatures exactly as given. Return ONLY the complete class inside a ```python block. "
         "No explanation.")
REVISE = ("Review the class implementation below against the specification. Fix anything wrong, "
          "missing or incomplete. Return ONLY the complete corrected class inside a ```python block.")
PLAN = ("Reply with a numbered plan for implementing this class. For EACH method say in ONE sentence "
        "of plain prose what it must do, and note which methods call which. "
        "Absolutely NO code, no def statements, no code blocks.")
FROMPLAN = ("Following the plan below, implement every method of the class. Keep the class name, "
            "method names and signatures exactly as given. "
            "Return ONLY the complete class inside a ```python block.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def parses(code):
    try: ast.parse(code); return True
    except Exception: return False
def is_code(t):
    t = t or ""
    return ("```" in t) or (re.search(r"^\s*def\s+\w+\s*\(", t, re.M) is not None)

def run_one(rec, code, mi):
    """chay test cua MOT method. Tra True/False."""
    if not code or not code.strip() or not parses(code): return False
    prog = ("\n".join(rec["import_statement"]) + "\nimport unittest\n\n" + code + "\n\n"
            + mi["test_code"] + "\n\n"
            + f"_r = unittest.TextTestRunner(verbosity=0).run("
              f"unittest.TestLoader().loadTestsFromTestCase({mi['test_class']}))\n"
              f"print('RESULT_OK' if _r.wasSuccessful() else 'RESULT_FAIL')\n")
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        res = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        return "RESULT_OK" in (res.stdout or "")
    except Exception: return False
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass

def grade(codes, meths):
    """codes: {i -> code}; meths: {i -> [methods_info da loc]}. Tra {i: [bool moi method]}"""
    jobs, key = [], []
    for i in IDX:
        for mi in meths[i]:
            jobs.append((ALL[i], codes[i], mi)); key.append(i)
    with ThreadPoolExecutor(max_workers=8) as ex:
        out = list(ex.map(lambda a: run_one(*a), jobs))
    per = {i: [] for i in IDX}
    for i, o in zip(key, out): per[i].append(o)
    return per

# ---- LOC #69-b: chi giu method ma LOI GIAI CHUAN dat, ngay trong kernel ----
t_f = time.time()
_gold = grade({i: ALL[i]["solution_code"] for i in IDX}, {i: ALL[i]["methods_info"] for i in IDX})
METH = {i: [mi for mi, o in zip(ALL[i]["methods_info"], _gold[i]) if o] for i in IDX}
IDX = [i for i in IDX if METH[i]]
NM = sum(len(METH[i]) for i in IDX)
print(f"loc chuan: {len(IDX)} lop / {NM} method giu lai (tu {len(ALL)}/{NMETH}) ({time.time()-t_f:.0f}s)", flush=True)
if NM < 350 or len(IDX) < 80:
    print(f"HUY: n_method={NM} < 350 hoac n_class={len(IDX)} < 80 (cong khoa #69-b)", flush=True)
    json.dump({"halt": "n_too_small", "n_method": NM, "n_class": len(IDX)},
              open(f"/kaggle/working/res_{RUN}.json", "w"))
    print("XONG", flush=True); raise SystemExit(0)

def mktok(p):
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    return tk
TK = mktok(MODEL)

def _chunk(m, sysm, ch):
    ps = [TK.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
          tokenize=False, add_generation_prompt=True) for u in ch]
    e = TK(ps, return_tensors="pt", padding=True).to(m.device)
    with torch.no_grad():
        o = m.generate(**e, max_new_tokens=MAXNEW, do_sample=False, pad_token_id=TK.pad_token_id)
    L = e["input_ids"].shape[1]
    r = [TK.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    del e, o
    return r
def gen(m, sysm, usrs):
    outs, i, bs = [], 0, BS
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            outs += _chunk(m, sysm, ch)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs // 2); print(f"  OOM -> lo {bs}", flush=True); continue
        i += bs
    return outs
def pgen(models, sysm, by_idx):
    keys = list(by_idx.keys()); parts = [keys[j::len(models)] for j in range(len(models))]
    store, lock, errs = {}, threading.Lock(), []
    def work(m, sub):
        try:
            res = gen(m, sysm, [by_idx[i] for i in sub])
            with lock: store.update(dict(zip(sub, res)))
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
    MS = [AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=BNB, device_map={"": d}).eval() for d in DEVS]
    QUANT = "nf4"
else:
    MS = [AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16).to(d).eval() for d in DEVS]
    QUANT = "fp16"
print(f"{len(MS)} ban sao | {QUANT}", flush=True)

SPEC = {i: ALL[i]["skeleton"] for i in IDX}
t0 = time.time()

# --- nhanh 1: solve1 (1 luot) ---
a1 = pgen(MS, SOLVE, SPEC)
C1 = {i: extract(a1[i]) for i in IDX}
print(f"solve1 xong ({time.time()-t0:.0f}s)", flush=True)

# --- nhanh 2: seq3 = giai -> sua -> sua (KHONG ngon ngu vai) ---
s2i = {i: f"{SPEC[i]}\n\nCurrent implementation:\n```python\n{C1[i]}\n```" for i in IDX}
a2 = pgen(MS, REVISE, s2i)
C2 = {i: (extract(a2[i]) or C1[i]) for i in IDX}
s3i = {i: f"{SPEC[i]}\n\nCurrent implementation:\n```python\n{C2[i]}\n```" for i in IDX}
a3 = pgen(MS, REVISE, s3i)
CSEQ = {i: (extract(a3[i]) or C2[i]) for i in IDX}
print(f"seq3 xong ({time.time()-t0:.0f}s)", flush=True)

# --- nhanh 3: PSV = lap ke hoach -> giai theo ke hoach -> tu kiem (CO ngon ngu vai) ---
p1 = pgen(MS, PLAN, SPEC)
p2i = {i: f"{SPEC[i]}\n\nPlan:\n{p1[i][:2500]}" for i in IDX}
p2 = pgen(MS, FROMPLAN, p2i)
CP2 = {i: extract(p2[i]) for i in IDX}
p3i = {i: f"{SPEC[i]}\n\nCurrent implementation:\n```python\n{CP2[i]}\n```" for i in IDX}
p3 = pgen(MS, REVISE, p3i)
CPSV = {i: (extract(p3[i]) or CP2[i]) for i in IDX}
print(f"PSV xong ({time.time()-t0:.0f}s)", flush=True)

# --- cham ---
G = {"solve1": grade(C1, METH), "seq3": grade(CSEQ, METH), "PSV": grade(CPSV, METH)}
print(f"cham xong ({time.time()-t0:.0f}s)", flush=True)

LEN = {i: len(ALL[i]["solution_code"]) for i in IDX}
srt = sorted(IDX, key=lambda i: LEN[i])
TERT = {0: srt[:len(srt)//3], 1: srt[len(srt)//3:2*len(srt)//3], 2: srt[2*len(srt)//3:]}

def stats(per, codes, sub=None):
    sub = IDX if sub is None else sub
    flat = [b for i in sub for b in per[i]]
    return {"method_pass": round(sum(flat)/max(len(flat),1), 4),
            "class_pass": round(sum(1 for i in sub if per[i] and all(per[i]))/max(len(sub),1), 4),
            "n_class": len(sub), "n_method": len(flat),
            "ast_rate": round(sum(1 for i in sub if parses(codes[i]))/max(len(sub),1), 4)}

CODES = {"solve1": C1, "seq3": CSEQ, "PSV": CPSV}
res = {"tag": RUN, "task": "classeval", "size": SIZE, "quant": QUANT,
       "n_class": len(IDX), "n_method": NM, "n_class_raw": len(ALL), "n_method_raw": NMETH, "n_gpu": NG,
       "overall": {k: stats(G[k], CODES[k]) for k in G},
       "tertile": {str(t): {k: stats(G[k], CODES[k], TERT[t]) for k in G} for t in TERT},
       "tertile_len_range": {str(t): [LEN[TERT[t][0]], LEN[TERT[t][-1]]] for t in TERT},
       "plan_is_code_rate": round(sum(1 for i in IDX if is_code(p1[i]))/len(IDX), 4),
       "plan_len_med": sorted(len(p1[i]) for i in IDX)[len(IDX)//2]}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump({str(i): {"class_name": ALL[i]["class_name"], "sol_len": LEN[i], "plan": p1[i][:2500],
                    "solve1": C1[i][:3000], "seq3": CSEQ[i][:3000], "PSV": CPSV[i][:3000],
                    "m_solve1": G["solve1"][i], "m_seq3": G["seq3"][i], "m_PSV": G["PSV"][i]}
           for i in IDX}, open(f"/kaggle/working/traces_{RUN}.json", "w"))

O = res["overall"]
print("\n==== H64 TONG KET ====")
print(f"  {'nhanh':8s} {'method_pass':>12s} {'class_pass':>11s} {'AST':>6s}")
for k in ["solve1", "seq3", "PSV"]:
    print(f"  {k:8s} {O[k]['method_pass']:12.4f} {O[k]['class_pass']:11.4f} {O[k]['ast_rate']:6.3f}")
d = O["PSV"]["method_pass"] - O["seq3"]["method_pass"]
print(f"\n  PSV - seq3 (method) = {d:+.4f}   <-- DAI LUONG CHINH (bang khoa #69)")
print(f"  PSV - seq3 (class)  = {O['PSV']['class_pass']-O['seq3']['class_pass']:+.4f}")
print("\n  DAP UNG THEO LIEU (nhom ba theo do dai loi giai chuan):")
dt = []
for t in [0, 1, 2]:
    T = res["tertile"][str(t)]; lo, hi = res["tertile_len_range"][str(t)]
    dd = T["PSV"]["method_pass"] - T["seq3"]["method_pass"]; dt.append(dd)
    print(f"    nhom {t} ({lo}-{hi} ky tu, {T['seq3']['n_class']} lop): "
          f"seq3 {T['seq3']['method_pass']:.4f} | PSV {T['PSV']['method_pass']:.4f} | chenh {dd:+.4f}")
mono = dt[2] > dt[1] > dt[0]
print(f"    tang deu theo do dai? {'CO' if mono else 'KHONG'}  (chenh nhom2 - nhom0 = {dt[2]-dt[0]:+.4f})")
print(f"\n  cong: class_pass(solve1) = {O['solve1']['class_pass']:.4f} "
      f"({'DAT' if .10 <= O['solve1']['class_pass'] <= .60 else 'HUY — san/bao hoa'})")
print(f"  cong: plan_is_code_rate = {res['plan_is_code_rate']:.4f} "
      f"({'DAT' if res['plan_is_code_rate'] <= .20 else 'HUY nhanh PSV'}) | ke hoach dai TB {res['plan_len_med']} ky tu")
print(f"  cong: AST min = {min(O[k]['ast_rate'] for k in O):.3f} "
      f"({'DAT' if min(O[k]['ast_rate'] for k in O) >= .80 else 'HUY'})")
print("\n-- bang khoa #69 --")
if not (.10 <= O["solve1"]["class_pass"] <= .60): print("  -> HUY: san hoac bao hoa")
elif res["plan_is_code_rate"] > .20: print("  -> HUY nhanh PSV: 'ke hoach' thuc chat la code")
elif d >= .05 and mono: print("  -> HANG 1: LAP KE HOACH DANG GIA KHI SAN PHAM DU DAI. Gia thuyet cua Nguyen DUNG.")
elif d >= .05:          print("  -> HANG 2: lap ke hoach giup nhung PHANG theo do dai -> KHONG phai vi do dai.")
elif abs(d) < .05:      print("  -> HANG 3: LAP KE HOACH VAN KHONG THEM GI, ke ca o 3.2x do dai. Thu co tac dung la SO LUOT.")
else:                   print("  -> HANG 4: lap ke hoach CO HAI tren bai dai.")
print("XONG", flush=True)
