# H100 (dang ky truoc #111) — XAC NHAN R2 tren 3 cap MOI; dai luong CHINH = d_honest.
# d_honest = acc(R2) - acc(I): giao thuc KHA THI co thang viec goi thang I khong (khong can oracle).
# Cong thu ve DUNG nhanh dem so {R0,R2,I} (bai hoc #187: H98 VOID vi cong bao ca nhanh NEN).
# Mau chot: A KHONG phu thuoc giao thuc => d_ceil^P - d_ceil^0 = (C_P-B_P) - (C_0-B_0) chinh xac,
# nen so sanh giao thuc = McNemar GHEP CAP tren vector CEIL. Khong so chéo lan chay.
import os, re, json, glob, time, gc, math, tempfile, subprocess, sys, threading, torch
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN, LO, HI = "@@RUN@@", int("@@LO@@"), int("@@HI@@")
MAXNEW, TIMEOUT = 2048, 60

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")

SPEC = {"dscoder":  ("deepseek-coder-6-7b", "deepseek-coder-6.7b"),
        "llama8b":  ("llama-3-1-8b", "llama-3.1-8b"),
        "qwen7b":   ("2-5-7b", "qwen2-5-7b"),
        "qwen14b":  ("14b",)}
M = {k: find_model(*v) for k, v in SPEC.items()}
print(f"MODELS={json.dumps(M, indent=1)}", flush=True)
PAIRS = {"P": ("llama8b", "qwen7b"), "Q": ("qwen7b", "qwen14b"), "R": ("dscoder", "qwen14b")}

NG = torch.cuda.device_count()
VRAM = torch.cuda.get_device_properties(0).total_memory/2**30
BIG_CARD = VRAM >= 40
print(f"SO GPU = {NG} | VRAM/card = {VRAM:.1f} GB", flush=True)
if not BIG_CARD:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
    from transformers import BitsAndBytesConfig
    _BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)

_hits = sorted(glob.glob("/kaggle/input/**/mbpp_full.json", recursive=True), key=len)
if _hits:
    print(f"MBPP nap tu dataset da stage: {_hits[0]}", flush=True)
    _DS = json.load(open(_hits[0]))
else:
    print("khong mount duoc mbpp_full.json -> HuggingFace", flush=True)
    from datasets import load_dataset
    _D = load_dataset("mbpp", "full", split="test+train+validation")
    _DS = [{k: r[k] for k in ["task_id", "text", "code", "test_list"]} for r in _D]
RAWALL = [r for r in _DS if LO <= r["task_id"] <= HI and len(r["test_list"]) >= 3]

SOLVE = ("Write the complete self-contained Python function. "
         "Return ONLY code inside a ```python block. No explanation.")
# --- BA GIAO THUC: khac DUY NHAT o loi nhac, cung artifact, cung ngan sach ---
R0 = ("You are given a task and a candidate Python solution that may be wrong. "
      "Return the complete corrected self-contained function. "
      "Return ONLY code inside a ```python block. No explanation.")
R1 = ("You are given a task and a candidate Python solution. The candidate is wrong more often "
      "than it is right. Check every part of it against the task. If you have any doubt, DISCARD "
      "it entirely and write your own solution from scratch. "
      "Return the complete self-contained function. "
      "Return ONLY code inside a ```python block. No explanation.")
R2 = ("You are given a task, YOUR OWN solution, and another solution written independently by a "
      "different model. Decide which is correct, or combine them. "
      "Return the complete self-contained function. "
      "Return ONLY code inside a ```python block. No explanation.")
PROTO = {"R0": R0, "R2": R2}

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def compiles(c):
    try: compile(c, "<s>", "exec"); return True
    except Exception: return False
def _unclosed(t): return (t or "").count("```") % 2 != 0
def _run(prog):
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        return (r.stdout or "") + (r.stderr or "")
    except Exception: return ""
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
def official(rec, code):
    if not code or not compiles(code): return False
    return "ALLOK" in _run(code + "\n\n" + "\n".join(rec["test_list"][1:3]) + "\nprint('ALLOK')\n")
def par(fn, args, w=8):
    with ThreadPoolExecutor(max_workers=w) as ex: return list(ex.map(lambda a: fn(*a), args))
def mcnemar(a, b):
    b01 = sum(1 for x, y in zip(a, b) if x and not y)
    b10 = sum(1 for x, y in zip(a, b) if y and not x)
    n = b01 + b10
    if n == 0: return b01, b10, 1.0
    k = min(b01, b10)
    return b01, b10, round(min(1.0, 2.0*sum(math.comb(n, i) for i in range(k+1))/(2.0**n)), 6)

def load_on(path, dev):
    tk = AutoTokenizer.from_pretrained(path); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    kw = dict(dtype=torch.float16) if BIG_CARD else dict(quantization_config=_BNB)
    mo = AutoModelForCausalLM.from_pretrained(path, device_map={"": dev}, **kw).eval()
    return mo, tk

def load_shard(path):
    """#191: model KHONG-Qwen KHONG luong tu hoa duoc tren ban transformers nay (fp16 ~16 GB),
    khong lot mot the T4 14.6 GB. Nap MOT ban, CHIA tren ca hai the."""
    tk = AutoTokenizer.from_pretrained(path); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    kw = dict(dtype=torch.float16) if BIG_CARD else dict(quantization_config=_BNB)
    mo = AutoModelForCausalLM.from_pretrained(path, device_map="auto", **kw).eval()
    return mo, tk
def free():
    gc.collect()
    for d in range(NG):
        with torch.cuda.device(d): torch.cuda.empty_cache()

@torch.no_grad()
def _gen_one(mo, tk, sysm, usrs, bs, lab):
    outs, i = [], 0
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                  tokenize=False, add_generation_prompt=True) for u in ch]
            e = tk(ps, return_tensors="pt", padding=True).to(mo.device)
            try:
                o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=False,
                                pad_token_id=tk.pad_token_id, stop_strings=["\n```\n"], tokenizer=tk)
            except TypeError:
                o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=False, pad_token_id=tk.pad_token_id)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs//2); print(f"      [{lab}] OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        if i == 0:
            _avg = sum(len(x) for x in outs)/max(len(outs), 1)
            if _avg < 20:
                raise SystemExit(f"HUY SOM (#155) [{lab}]: lo 1 dai TB {_avg:.1f} ky tu. {outs[0][:80]!r}")
            print(f"      [{lab}] lo 1 dai TB {_avg:.0f} ky tu", flush=True)
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs

def gen_dp(path, sysm, usrs, bs=8):
    """song song DU LIEU tren tat ca GPU (khong phai pipeline) — #gpu_batch_sizing"""
    if NG <= 1:
        mo, tk = load_on(path, 0); out = _gen_one(mo, tk, sysm, usrs, bs, "gpu0")
        mo = None; tk = None; free(); return out
    # #191: H100 OOM khi nap model KE TIEP vi ban sao cua model TRUOC chua duoc giai phong.
    # Kiem TRUOC khi nap: neu VRAM chua sach thi bao ngay, dung de OOM giua chung.
    for d in range(NG):
        _used = torch.cuda.memory_allocated(d)/2**30
        if _used > 1.0:
            print(f"      CANH BAO: gpu{d} con {_used:.2f} GB truoc khi nap — thu giai phong lai", flush=True)
            free()
            _used = torch.cuda.memory_allocated(d)/2**30
            if _used > 1.0:
                raise SystemExit(f"KHONG GIAI PHONG DUOC gpu{d}: con {_used:.2f} GB. Dung lai (#191).")
    # #191: thu nap ban sao thu nhat; neu no chiem qua nua the thi KHONG the co ban sao thu hai
    # -> quay ve MOT ban chia tren ca hai the (mat song song, nhung chay duoc).
    _m0 = load_on(path, 0)
    _g0 = torch.cuda.memory_allocated(0)/2**30
    print(f"      ban sao 1: gpu0 {_g0:.2f} GB", flush=True)
    if _g0 > VRAM*0.5:
        print(f"      -> qua lon cho 2 ban sao; nap lai MOT ban CHIA tren {NG} the", flush=True)
        _m0 = None; free(); free()
        mo, tk = load_shard(path)
        out = _gen_one(mo, tk, sysm, usrs, max(1, bs//2), "shard")
        mo = None; tk = None; free(); free()
        print("      sau giai phong: " + " | ".join(
            f"gpu{d} {torch.cuda.memory_allocated(d)/2**30:.2f} GB" for d in range(NG)), flush=True)
        return out
    parts = [usrs[d::NG] for d in range(NG)]
    res, models = [None]*NG, [None]*NG
    models[0] = _m0; _m0 = None
    for d in range(1, NG): models[d] = load_on(path, d)
    def work(d):
        mo, tk = models[d]
        res[d] = _gen_one(mo, tk, sysm, parts[d], bs, f"gpu{d}")
    th = [threading.Thread(target=work, args=(d,)) for d in range(NG)]
    for t in th: t.start()
    for t in th: t.join()
    out = [None]*len(usrs)
    for d in range(NG):
        for j, v in enumerate(res[d]): out[d + j*NG] = v
    # giai phong TUONG MINH tung tham chieu (bai hoc #132: `del ten_cuc_bo` la vo tac dung)
    for d in range(NG): models[d] = None
    del th, work
    free(); free()
    print("      sau giai phong: " + " | ".join(
        f"gpu{d} {torch.cuda.memory_allocated(d)/2**30:.2f} GB" for d in range(NG)), flush=True)
    assert all(v is not None for v in out), "gep song song thieu phan tu"
    return out

t_f = time.time()
_ok = par(lambda r: official(r, r["code"]), [(r,) for r in RAWALL], 8)
ALL = [r for r, o in zip(RAWALL, _ok) if o]
N = len(ALL)
print(f"loc chuan: {N}/{len(RAWALL)} bai ({time.time()-t_f:.0f}s)", flush=True)
PR = [f"{r['text']}\n\nYour code must satisfy this test:\n{r['test_list'][0]}" for r in ALL]

RAW, PASS = {}, {}
def save_partial():   # #128: BAN LUU CHUA DU LIEU THO
    json.dump({"partial": True, "run": RUN, "n": N, "task_id": [r["task_id"] for r in ALL],
               "raw": RAW, "pass": PASS}, open(f"/kaggle/working/partial_{RUN}.json", "w"))

t0 = time.time()
for tag in ["dscoder", "llama8b", "qwen7b", "qwen14b"]:   # nen: re -> dat
    print(f"\n=== NEN {tag} ===", flush=True)
    RAW[tag] = gen_dp(M[tag], SOLVE, PR)
    PASS[tag] = par(official, [(ALL[i], extract(RAW[tag][i])) for i in range(N)])
    print(f"  {tag}: acc={sum(PASS[tag])/N:.4f} ({time.time()-t0:.0f}s)", flush=True)
    save_partial()

WALL = 10.5*3600
for pk, (s, i) in PAIRS.items():
    for rk, sysm in PROTO.items():
        key = f"{pk}:{rk}"
        if time.time()-t0 > WALL:
            print(f"  DUNG SINH o {time.time()-t0:.0f}s — bo {key}", flush=True); continue
        print(f"\n=== {key}  ({s} -> {i}, {rk}) ===", flush=True)
        if rk == "R2":   # tai dung loi giai cua chinh I: KHONG ton luot sinh
            up = [f"{PR[k]}\n\nYour own solution:\n```python\n{extract(RAW[i][k])}\n```"
                  f"\n\nSolution from a different model:\n```python\n{extract(RAW[s][k])}\n```"
                  for k in range(N)]
        else:
            up = [f"{PR[k]}\n\nCandidate solution:\n```python\n{extract(RAW[s][k])}\n```"
                  for k in range(N)]
        RAW[key] = gen_dp(M[i], sysm, up)
        PASS[key] = par(official, [(ALL[k], extract(RAW[key][k])) for k in range(N)])
        print(f"  {key}: acc_V={sum(PASS[key])/N:.4f} ({time.time()-t0:.0f}s)", flush=True)
        save_partial()

acc = {t: round(sum(v)/N, 4) for t, v in PASS.items()}
ext = {t: round(sum(compiles(extract(x)) for x in v)/N, 4) for t, v in RAW.items()}
trunc = {t: round(sum(_unclosed(x) for x in v)/N, 4) for t, v in RAW.items()}
run_gates = {"n>=480": N >= 480,
             "extract_min>=.80 moi nhanh": min(ext.values()) >= .80,
             "truncation<.05 moi nhanh": max(trunc.values()) < .05}
# #187: gian trich xuat chi tinh TRONG nhom nhanh DEM SO SANH cua tung cap = {R0, R2, I}.
# Nhanh S KHONG nam trong so sanh nao => khong vao cong gian.

cells, pair_gates = {}, {}
for pk, (s, i) in PAIRS.items():
    S_, I_ = PASS[s], PASS[i]
    A = sum(1 for k in range(N) if S_[k] and not I_[k])/N
    _, _, p_is = mcnemar(S_, I_)
    _cmp = [ext[i]] + [ext[f"{pk}:{rk}"] for rk in PROTO if f"{pk}:{rk}" in ext]
    pair_gates[pk] = {"I-S>=.02": acc[i]-acc[s] >= .02, "p(I-S)<.05": p_is < .05,
                      "gian trich xuat {R0,R2,I} <.05": (max(_cmp)-min(_cmp)) < .05,
                      "A": round(A, 4), "I-S": round(acc[i]-acc[s], 4), "p_IS": p_is,
                      "gian_cmp": round(max(_cmp)-min(_cmp), 4)}
    for rk in PROTO:
        key = f"{pk}:{rk}"
        if key not in PASS: continue
        V_ = PASS[key]
        CEIL = [S_[k] or V_[k] for k in range(N)]
        B = sum(1 for k in range(N) if (not S_[k]) and I_[k] and not V_[k])/N
        C = sum(1 for k in range(N) if (not S_[k]) and (not I_[k]) and V_[k])/N
        d_ceil = sum(CEIL)/N - sum(I_)/N
        cells[key] = {"pair": pk, "proto": rk, "acc_V": acc[key],
                      "A": round(A, 4), "B": round(B, 4), "C": round(C, 4),
                      "d_ceil": round(d_ceil, 4), "ABC": round(A-B+C, 4),
                      "khop_dang_thuc": abs((A-B+C)-d_ceil) < 1e-9, "_CEIL": CEIL}

# --- CHINH (#111): d_honest = acc(R2) - acc(I), McNemar GHEP CAP, khong can oracle ---
HON = {}
for pk, (s, i) in PAIRS.items():
    key = f"{pk}:R2"
    if key not in PASS: continue
    b01, b10, p = mcnemar(PASS[i], PASS[key])
    HON[pk] = {"d_honest": round(acc[key]-acc[i], 4), "p": p, "b01": b01, "b10": b10,
               "acc_R2": acc[key], "acc_I": acc[i]}

# --- PHU: D = acc(CEIL_R2) - acc(CEIL_R0), ghep cap (xac nhan #188) ---
D = {}
for pk in PAIRS:
    base = cells.get(f"{pk}:R0")
    if not base: continue
    for rk in ("R2",):
        c = cells.get(f"{pk}:{rk}")
        if not c: continue
        b01, b10, p = mcnemar(base["_CEIL"], c["_CEIL"])
        D[f"{pk}:{rk}-R0"] = {"D": round(c["d_ceil"]-base["d_ceil"], 4), "p": p,
                              "b01": b01, "b10": b10,
                              "dB": round(c["B"]-base["B"], 4), "dC": round(c["C"]-base["C"], 4)}
for c in cells.values(): c.pop("_CEIL")

VOID = [k for k, v in run_gates.items() if not v]
pair_ok = {pk: all(v for k, v in g.items() if isinstance(v, bool)) for pk, g in pair_gates.items()}
if not any(pair_ok.values()): VOID.append("ca ba cap truot cong rieng")

res = {"tag": RUN, "n": N, "acc": acc, "extract_rate": ext, "truncation_rate": trunc,
       "run_gates": run_gates, "pair_gates": pair_gates, "pair_ok": pair_ok,
       "VOID": VOID, "cells": cells, "d_honest": HON, "D": D}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump({"pass": PASS, "acc": acc, "n": N, "task_id": [r["task_id"] for r in ALL]},
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print(f"\n==== H98 {RUN} ====")
print(f"  n={N} | acc: {acc}")
print(f"  cong lan chay: {run_gates}")
for pk, g in pair_gates.items(): print(f"  cong cap {pk}: {g}  -> {'DAT' if pair_ok[pk] else 'TRUOT'}")
print(f"\n  {'o':10s}{'A':>8s}{'B':>8s}{'C':>8s}{'d_ceil':>9s}  =ABC")
for k, c in cells.items():
    print(f"  {k:10s}{c['A']:8.4f}{c['B']:8.4f}{c['C']:8.4f}{c['d_ceil']:+9.4f}  {c['khop_dang_thuc']}")
if cells and not all(c["khop_dang_thuc"] for c in cells.values()):
    print("  !! DANG THUC A-B+C KHONG KHOP — LOI CAI DAT, KHONG DUOC DOC SO")
print(f"\n  {'so sanh':14s}{'D':>9s}{'p':>10s}{'dB':>8s}{'dC':>8s}")
for k, v in D.items():
    print(f"  {k:14s}{v['D']:+9.4f}{v['p']:10.4g}{v['dB']:+8.4f}{v['dC']:+8.4f}")

print(f"\n  {'cap':6s}{'acc_I':>8s}{'acc_R2':>8s}{'d_honest':>10s}{'p':>10s}")
for pk, v in HON.items():
    print(f"  {pk:6s}{v['acc_I']:8.4f}{v['acc_R2']:8.4f}{v['d_honest']:+10.4f}{v['p']:10.4g}")

print("\n-- BANG KHOA #111 (CHINH: d_honest) --")
if VOID:
    print(f"  -> HANG 0: VOID {VOID}")
elif not HON:
    print("  -> khong co o nao tinh duoc")
else:
    ok = {pk: v for pk, v in HON.items() if pair_ok.get(pk)}
    pos = {pk: v for pk, v in ok.items() if v["d_honest"] >= .02 and v["p"] < .05}
    neg = {pk: v for pk, v in ok.items() if v["d_honest"] <= -.02 and v["p"] < .05}
    n_ok = len(ok)
    print(f"  cap hop le = {n_ok} | duong co y nghia = {sorted(pos)} | am co y nghia = {sorted(neg)}")
    if len(pos) >= 2:
        print("  -> HANG 1: GIAO THUC KHA THI DAU TIEN THANG I. Ket qua duong dung duoc dau tien.")
        print(f"     => vao README kem so cap ({len(pos)}/{n_ok}).")
    elif len(pos) == 1:
        print(f"  -> HANG 2: goi y, CHUA XAC LAP (chi {sorted(pos)} / {n_ok} cap).")
    elif neg:
        print(f"  -> HANG 4: R2 CHU DONG HAI so voi goi thang I: {sorted(neg)}. Canh bao trien khai.")
    else:
        print("  -> HANG 3: R2 KHONG thang I. Loi ich cua #188 chi ton tai o TRAN ORACLE.")
        print("     => PHAI rut moi ham y trien khai cua #188, ghi ngay vao #188.")
    print("\n-- PHU: xac nhan #188 (D = d_ceil^R2 - d_ceil^R0) --")
    dpos = [k for k, v in D.items() if v["D"] >= .02 and v["p"] < .05 and pair_ok.get(k.split(":")[0])]
    print(f"  cap tai lap = {sorted(dpos)} / {n_ok}")
    print("  -> " + ("#188 TAI LAP tren cap moi" if len(dpos) >= 2 else
                     "#188 KHONG tai lap — phai ghi ro vao IDEAS.md rang ket qua thu cap do KHONG dung"))
print("XONG", flush=True)
