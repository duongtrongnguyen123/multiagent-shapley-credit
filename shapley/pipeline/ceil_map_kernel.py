# H97 (dang ky truoc #107) — BAN DO d_ceil: phan ra A/B/C tren 15 cap, CUNG bo bai MBPP.
# Nen: 6 model x 1 luot greedy. Nhanh V: voi moi cap co huong (S,I), I SUA artifact cua S.
# d_ceil = P(S | (~S & V)) - P(I), tu kiem lai bang A - B + C (phai khop tuyet doi).
# Bang khoa #107: hoi quy d_ceil ~ d0 + d1*chenh; g* = -d0/d1 la muc chenh doi dau.
# CONG THEO CAP (#177): mot nhanh V hong chi giet cap cua no, khong giet ca lan chay.
import os, re, json, glob, time, gc, math, tempfile, subprocess, sys, torch
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN, LO, HI = "@@RUN@@", int("@@LO@@"), int("@@HI@@")
MAXNEW, TIMEOUT = 2048, 60

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")

# thu tu NAP nhanh V: RE -> DAT, de het gio van con cap dung duoc (#128: luu RAW moi buoc)
SPEC = [("qwen1.5b", ("1-5b", "1_5b", "1.5b"), "qwen"),
        ("llama8b",  ("llama-3-1-8b", "llama-3.1-8b"), "llama"),
        ("dscoder",  ("deepseek-coder-6-7b", "deepseek-coder-6.7b"), "deepseek"),
        ("qwen7b",   ("2-5-7b", "qwen2-5-7b"), "qwen"),
        ("qwen14b",  ("14b",),                 "qwen"),
        ("qwen32b",  ("32b",),                 "qwen")]
M = {}
for tag, needles, fam in SPEC:
    try: M[tag] = (find_model(*needles), fam)
    except RuntimeError as e: print(f"  BO QUA {tag}: {e}", flush=True)
print(f"MODELS={json.dumps({k: v[0] for k, v in M.items()}, indent=1)}", flush=True)

NG = torch.cuda.device_count()
VRAM = torch.cuda.get_device_properties(0).total_memory/2**30
BIG_CARD = VRAM >= 40
print(f"SO GPU = {NG} | VRAM/card = {VRAM:.1f} GB | che do = {'bf16' if BIG_CARD else 'nf4'}", flush=True)
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
FIX = ("You are given a task and a candidate Python solution that may be wrong. "
       "Return the complete corrected self-contained function. "
       "Return ONLY code inside a ```python block. No explanation.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def compiles(c):
    try: compile(c, "<s>", "exec"); return True
    except Exception: return False
def _unclosed(t):  # #154: cat cut = so rao LE
    return (t or "").count("```") % 2 != 0
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

def load(path):
    tk = AutoTokenizer.from_pretrained(path); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    if BIG_CARD:
        mo = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16, device_map={"": 0}).eval()
    else:
        mo = AutoModelForCausalLM.from_pretrained(path, quantization_config=_BNB, device_map={"": 0}).eval()
    print(f"    nap: " + " | ".join(f"gpu{d} {torch.cuda.memory_allocated(d)/2**30:.2f} GB"
                                    for d in range(NG)), flush=True)
    return mo, tk
def free():
    gc.collect()
    for d in range(NG):
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
            try:
                o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=False,
                                pad_token_id=tk.pad_token_id, stop_strings=["\n```\n"], tokenizer=tk)
            except TypeError:
                o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=False, pad_token_id=tk.pad_token_id)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs//2); print(f"      OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        if i == 0:   # #155: kiem tinh tinh ngay lo dau (nguong 20 hieu chinh tren du lieu that)
            _avg = sum(len(x) for x in outs)/max(len(outs), 1)
            if _avg < 20:
                raise SystemExit(f"HUY SOM (#155): lo 1 dai TB {_avg:.1f} ky tu — sinh hong. {outs[0][:80]!r}")
            print(f"      [lo 1] dai TB {_avg:.0f} ky tu", flush=True)
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs

t_f = time.time()
_ok = par(lambda r: official(r, r["code"]), [(r,) for r in RAWALL], 8)
ALL = [r for r, o in zip(RAWALL, _ok) if o]
N = len(ALL)
print(f"loc chuan: {N}/{len(RAWALL)} bai ({time.time()-t_f:.0f}s)", flush=True)
PR = [f"{r['text']}\n\nYour code must satisfy this test:\n{r['test_list'][0]}" for r in ALL]

def save_partial():
    # #128: BAN LUU PHAI CHUA DU LIEU THO, khong phai bo dem tien do
    json.dump({"partial": True, "run": RUN, "n": N,
               "task_id": [r["task_id"] for r in ALL],
               "raw": RAW, "pass": PASS, "raw_v": RAWV, "pass_v": PASSV},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))

t0 = time.time()
RAW, PASS, RAWV, PASSV = {}, {}, {}, {}
for tag, (path, fam) in M.items():
    print(f"\n=== NEN {tag} ({fam}) ===", flush=True)
    mo, tk = load(path)
    RAW[tag] = gen(mo, tk, SOLVE, PR, 16)
    mo = None; tk = None; free()
    PASS[tag] = par(official, [(ALL[i], extract(RAW[tag][i])) for i in range(N)])
    print(f"  {tag}: acc={sum(PASS[tag])/N:.4f} ({time.time()-t0:.0f}s)", flush=True)
    save_partial()

acc = {t: round(sum(PASS[t])/N, 4) for t in PASS}
# cap co huong: I manh hon S. Gom theo I de nap model I DUNG MOT LAN.
DIRECTED = [(s, i) for i in M for s in M if s != i and acc[i] > acc[s]]
BY_I = {}
for s, i in DIRECTED: BY_I.setdefault(i, []).append(s)
print(f"\n{len(DIRECTED)} cap co huong; nap {len(BY_I)} model sua", flush=True)

WALL = 10.5*3600   # dung sinh o 10.5h; con lai de cham + phan tich kip ghi res_ (#178)
for i in M:                       # M da xep re -> dat, nen vong nay cung theo thu tu do
    if i not in BY_I: continue
    if time.time()-t0 > WALL:
        print(f"  DUNG SINH o {time.time()-t0:.0f}s (>{WALL:.0f}) — bo qua {i} va sau do", flush=True)
        break
    print(f"\n=== SUA boi {i} ({len(BY_I[i])} cap) ===", flush=True)
    mo, tk = load(M[i][0])
    for s in BY_I[i]:
        up = [f"{PR[k]}\n\nCandidate solution:\n```python\n{extract(RAW[s][k])}\n```"
              for k in range(N)]
        if time.time()-t0 > WALL:
            print(f"  DUNG SINH giua chung — bo {s}->{i}", flush=True); break
        RAWV[f"{s}->{i}"] = gen(mo, tk, FIX, up, 16)
        print(f"  {s}->{i}: sinh xong ({time.time()-t0:.0f}s)", flush=True)
        save_partial()
    mo = None; tk = None; free()
    for s in BY_I[i]:
        key = f"{s}->{i}"
        if key not in RAWV: continue
        PASSV[key] = par(official, [(ALL[k], extract(RAWV[key][k])) for k in range(N)])
        print(f"  {key}: acc_V={sum(PASSV[key])/N:.4f}", flush=True)
    save_partial()

ext = {t: round(sum(compiles(extract(x)) for x in v)/N, 4) for t, v in RAW.items()}
extv = {k: round(sum(compiles(extract(x)) for x in v)/N, 4) for k, v in RAWV.items()}
trunc = {t: round(sum(_unclosed(x) for x in v)/N, 4) for t, v in RAW.items()}
truncv = {k: round(sum(_unclosed(x) for x in v)/N, 4) for k, v in RAWV.items()}

run_gates = {"n>=480": N >= 480,
             "moi acc nen trong [.30,.90]": all(.30 <= a <= .90 for a in acc.values())}

pairs, bo_cap = [], []
for s, i in DIRECTED:
    key = f"{s}->{i}"
    if key not in PASSV:
        bo_cap.append({"cap": key, "vi_sao": "chua chay xong (het gio)"}); continue
    # --- CONG THEO CAP (#107) ---
    g_ext  = extv[key] >= .90
    g_sym  = abs(extv[key] - ext[i]) < .05
    g_trun = truncv[key] < .05
    if not (g_ext and g_sym and g_trun):
        bo_cap.append({"cap": key, "trich_V": extv[key], "trich_I_nen": ext[i],
                       "cat_cut_V": truncv[key],
                       "vi_sao": [n for n, v in [("trich_V>=.90", g_ext),
                                                 ("|trichV-trichI|<.05", g_sym),
                                                 ("cat_cut_V<.05", g_trun)] if not v]})
        continue
    S_, I_, V_ = PASS[s], PASS[i], PASSV[key]
    # S or (not S and V)  ==  S or V  (dai so Boole) — viet gon cho de doc, KET QUA Y HET
    CEIL = [S_[k] or V_[k] for k in range(N)]
    A = sum(1 for k in range(N) if S_[k] and not I_[k])/N
    B = sum(1 for k in range(N) if (not S_[k]) and I_[k] and not V_[k])/N
    C = sum(1 for k in range(N) if (not S_[k]) and (not I_[k]) and V_[k])/N
    d_ceil = sum(CEIL)/N - sum(I_)/N
    b01, b10, p = mcnemar(I_, CEIL)
    pairs.append({"S": s, "I": i, "acc_S": acc[s], "acc_I": acc[i], "acc_V": round(sum(V_)/N, 4),
                  "gap": round(acc[i]-acc[s], 4),
                  "A": round(A, 4), "B": round(B, 4), "C": round(C, 4),
                  "d_ceil": round(d_ceil, 4), "ABC": round(A-B+C, 4),
                  "khop_dang_thuc": abs((A-B+C) - d_ceil) < 1e-9,
                  "p_ceil": p, "khac_ho": M[s][1] != M[i][1]})
run_gates["con >=10 cap hop le"] = len(pairs) >= 10
VOID = [k for k, v in run_gates.items() if not v]

def ols(y, X):
    """hoi quy boi nho nhat, giai bang phuong trinh chuan (khong can numpy)"""
    n_, k = len(y), len(X[0])
    XtX = [[sum(X[r][a]*X[r][b] for r in range(n_)) for b in range(k)] for a in range(k)]
    Xty = [sum(X[r][a]*y[r] for r in range(n_)) for a in range(k)]
    Aug = [XtX[r][:] + [Xty[r]] for r in range(k)]
    for c in range(k):
        piv = max(range(c, k), key=lambda r: abs(Aug[r][c]))
        Aug[c], Aug[piv] = Aug[piv], Aug[c]
        if abs(Aug[c][c]) < 1e-12: return None
        for r in range(k):
            if r == c: continue
            f = Aug[r][c]/Aug[c][c]
            for cc in range(c, k+1): Aug[r][cc] -= f*Aug[c][cc]
    beta = [Aug[r][k]/Aug[r][r] for r in range(k)]
    yhat = [sum(beta[a]*X[r][a] for a in range(k)) for r in range(n_)]
    resid = [y[r]-yhat[r] for r in range(n_)]
    ybar = sum(y)/n_
    sst = sum((v-ybar)**2 for v in y)
    r2 = 1 - sum(e*e for e in resid)/sst if sst > 0 else float("nan")
    dof = n_-k
    s2 = sum(e*e for e in resid)/dof if dof > 0 else float("nan")
    Aug2 = [XtX[r][:] + [1.0 if a == r else 0.0 for a in range(k)] for r in range(k)]
    for c in range(k):
        piv = max(range(c, k), key=lambda r: abs(Aug2[r][c]))
        Aug2[c], Aug2[piv] = Aug2[piv], Aug2[c]
        d = Aug2[c][c]
        for cc in range(2*k): Aug2[c][cc] /= d
        for r in range(k):
            if r == c: continue
            f = Aug2[r][c]
            for cc in range(2*k): Aug2[r][cc] -= f*Aug2[c][cc]
    se = [(s2*Aug2[a][k+a])**.5 for a in range(k)]
    return beta, se, dof, r2

def p2(b, s):   # xap xi chuan; dof nho nen chi la uoc luong (doc ky khi sat .05)
    if s <= 0: return 1.0
    return round(math.erfc(abs(b/s)/(2**.5)), 6)

res = {"tag": RUN, "n": N, "acc": acc, "acc_V": {k: round(sum(v)/N, 4) for k, v in PASSV.items()},
       "extract_rate": ext, "extract_rate_V": extv,
       "truncation_rate": trunc, "truncation_rate_V": truncv,
       "run_gates": run_gates, "VOID": VOID, "bo_cap": bo_cap, "pairs": pairs}
if not VOID and len(pairs) >= 4:
    X = [[1.0, q["gap"]] for q in pairs]
    o1 = ols([q["d_ceil"] for q in pairs], X)
    if o1:
        b, se, dof, r2 = o1
        res["ols_ceil"] = {"d0": round(b[0], 5), "d1_gap": round(b[1], 5),
                           "se": [round(x, 5) for x in se], "dof": dof, "R2": round(r2, 4),
                           "p_d1": p2(b[1], se[1]),
                           "g_star": round(-b[0]/b[1], 4) if abs(b[1]) > 1e-9 else None}
    for nm, fld in (("ols_B", "B"), ("ols_A", "A"), ("ols_C", "C")):
        o2 = ols([q[fld] for q in pairs], X)
        if o2:
            b, se, dof, r2 = o2
            res[nm] = {"b0": round(b[0], 5), "b1_gap": round(b[1], 5), "R2": round(r2, 4),
                       "dof": dof, "p_b1": p2(b[1], se[1])}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump({"pass": PASS, "pass_v": PASSV, "acc": acc, "n": N,
           "task_id": [r["task_id"] for r in ALL]},
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print(f"\n==== H97 {RUN} ====")
print(f"  n={N} | acc nen: {acc}")
print(f"  cong lan chay: {run_gates}")
if bo_cap:
    print(f"  CAP BI LOAI ({len(bo_cap)}):")
    for z in bo_cap: print(f"     {z}")
print(f"\n  {'S':10s}{'I':10s}{'gap':>8s}{'A':>8s}{'B':>8s}{'C':>8s}{'d_ceil':>9s}{'p':>10s}  =ABC")
for q in sorted(pairs, key=lambda z: z["gap"]):
    print(f"  {q['S']:10s}{q['I']:10s}{q['gap']:+8.4f}{q['A']:8.4f}{q['B']:8.4f}{q['C']:8.4f}"
          f"{q['d_ceil']:+9.4f}{q['p_ceil']:10.4g}  {q['khop_dang_thuc']}")
if not all(q["khop_dang_thuc"] for q in pairs):
    print("  !! DANG THUC A-B+C KHONG KHOP — LOI CAI DAT, KHONG DUOC DOC SO")

print("\n-- BANG KHOA #107 --")
if VOID:
    print(f"  -> HANG 0: VOID {VOID}")
elif "ols_ceil" not in res:
    print("  -> khong du cap de hoi quy")
else:
    o = res["ols_ceil"]
    print(f"  d_ceil ~ {o['d0']:+.5f} {o['d1_gap']:+.5f}*chenh   R2={o['R2']:.4f} "
          f"p(d1)={o['p_d1']:.4g} dof={o['dof']}  g*={o['g_star']}")
    gs = o["g_star"]
    if o["d1_gap"] > 0 and o["p_d1"] < .05:
        print("  -> HANG 4: NGUOC — chenh lon cho du dia rong NHIEU hon. Mau thuan luat A cua #182.")
    elif o["p_d1"] >= .05 or o["R2"] < .50:
        print("  -> HANG 3: chenh KHONG du bao d_ceil => B hoac C mang phuong sai khac")
        print("     => don bay giao thuc CON KHA NANG. Bao cao bang mo ta.")
    elif gs is not None and .04 <= gs <= .32:
        print(f"  -> HANG 1: chenh DU BAO d_ceil. Luat quyet dinh: chi dang thu 'sua' khi chenh < {gs:.4f}")
    elif gs is not None and gs < .04:
        print("  -> HANG 2: GIET DONG 'SUA' — d_ceil < 0 tren TOAN DAI do duoc.")
        print("     => phai rut phan 'nut that la kappa chu khong phai H' cua #169 trong TONG_HOP.")
    else:
        print(f"  -> g*={gs} nam TREN dai do duoc (>.32): d_ceil > 0 khap dai. Khong co hang nao "
              f"phu — GHI NHAN va dieu tra, KHONG duoc ep vao hang 1.")
    if "ols_B" in res:
        rb = res["ols_B"]
        print(f"\n  PHU: B ~ {rb['b0']:+.5f} {rb['b1_gap']:+.5f}*chenh  R2={rb['R2']:.4f} p={rb['p_b1']:.4g}")
        print("       -> " + ("B phan lon do CAP MODEL quyet dinh; don bay giao thuc HEP"
                              if rb["R2"] >= .50 else
                              "B con phuong sai KHONG do chenh => co cho cho giao thuc tac dong"))
        print("       (mot giao thuc sua duy nhat: KHONG chung minh duoc nhan qua — xem canh bao #107)")
    for nm in ("ols_A", "ols_C"):
        if nm in res:
            r_ = res[nm]
            print(f"  mo ta: {nm[4:]} ~ {r_['b0']:+.5f} {r_['b1_gap']:+.5f}*chenh  R2={r_['R2']:.4f}")
print("XONG", flush=True)
