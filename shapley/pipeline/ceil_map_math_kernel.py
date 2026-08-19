# H99 (dang ky truoc #109) — BAN DO d_ceil tren MATH-500: H97 lap lai, doi DUY NHAT mien.
# Sau model, 15 cap co huong, cung 500 bai. Nhanh V: I SUA loi giai cua S.
# d_ceil = P(S | (~S & V)) - P(I), tu kiem lai bang A - B + C.
# Bang khoa #109: so g* cua MATH voi g* = .0913 cua MBPP (#185).
# MAXNEW=2048 (khong phai 1280 cua H88c) — #130: cap co dinh phat model manh nang nhat.
import os, re, csv, json, glob, time, gc, math, subprocess, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = "@@RUN@@"
MAXNEW = 2048

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")

# thu tu NAP nhanh V: RE -> DAT (#128: luu RAW moi buoc)
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

CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
RAWCSV = list(csv.DictReader(open(CSV, newline="", encoding="utf-8")))
def _col(r, *names):
    low = {str(k).strip().lower(): v for k, v in r.items()}
    for n in names:
        v = low.get(n)
        if isinstance(v, str) and v.strip(): return v
    return None
# --- CHAM: dung DUNG ba ham cua #174/#181, khong sua mot ky tu ---
def _bx(t):
    i = (t or "").rfind("\\boxed")
    if i < 0: return None
    i = t.find("{", i)
    if i < 0: return None
    d = 0
    for j in range(i, len(t)):
        if t[j] == "{": d += 1
        elif t[j] == "}":
            d -= 1
            if d == 0: return t[i+1:j]
    return None
_RM = [r"\\left", r"\\right", r"\\!", r"\\,", r"\\;", r"\\ ", r"\\\$", r"\$", r"^\\\\", r"\s"]
def norm(a):
    if a is None: return None
    s = str(a).strip()
    s = re.sub(r"\\(?:text|mbox|textbf|mathrm)\s*\{([^{}]*)\}", r"\1", s)
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = s.replace("^{\\circ}", "").replace("^\\circ", "")
    s = re.sub(r"\\%|%", "", s)
    for p in _RM: s = re.sub(p, "", s)
    s = s.rstrip(".")
    s = re.sub(r"^\{(.*)\}$", r"\1", s)
    if re.fullmatch(r"-?\d+\.?\d*", s):
        try:
            f = float(s); s = str(int(f)) if f == int(f) else str(f)
        except Exception: pass
    return s
def eq(a, b):
    na, nb = norm(a), norm(b)
    if na is None or nb is None: return False
    if na == nb: return True
    try: return abs(float(na) - float(nb)) < 1e-6
    except Exception: return False

Q = [_col(r, "question", "problem") for r in RAWCSV]
GOLD = [_bx(_col(r, "answer", "solution") or "") for r in RAWCSV]
keep = [i for i in range(len(RAWCSV)) if Q[i] and GOLD[i]]
Q = [Q[i] for i in keep]; GOLD = [GOLD[i].strip() for i in keep]
N = len(Q)
print(f"MATH-500: {N} bai", flush=True)

TAIL = "Put ONLY the final answer inside \\boxed{}."
SOLVE = f"Solve step by step. {TAIL}"
FIX = ("You are given a problem and a candidate solution that may be wrong. "
       f"Produce the correct complete solution. {TAIL}")

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
def gen(mo, tk, sysm, usrs, bs, lab):
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

RAW, PASS, RAWV, PASSV = {}, {}, {}, {}
def save_partial():   # #128: BAN LUU CHUA DU LIEU THO
    json.dump({"partial": True, "run": RUN, "n": N, "gold": GOLD,
               "raw": RAW, "pass": PASS, "raw_v": RAWV, "pass_v": PASSV},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))

t0 = time.time()
for tag, (path, fam) in M.items():
    print(f"\n=== NEN {tag} ({fam}) ===", flush=True)
    mo, tk = load(path)
    RAW[tag] = gen(mo, tk, SOLVE, Q, 16, tag)
    mo = None; tk = None; free()
    PASS[tag] = [eq(_bx(RAW[tag][k]), GOLD[k]) for k in range(N)]
    print(f"  {tag}: acc={sum(PASS[tag])/N:.4f} ({time.time()-t0:.0f}s)", flush=True)
    save_partial()

acc = {t: round(sum(PASS[t])/N, 4) for t in PASS}
DIRECTED = [(s, i) for i in M for s in M if s != i and acc[i] > acc[s]]
BY_I = {}
for s, i in DIRECTED: BY_I.setdefault(i, []).append(s)
print(f"\n{len(DIRECTED)} cap co huong; nap {len(BY_I)} model sua", flush=True)

WALL = 10.5*3600   # #178: dung sinh som de kip cham + ghi res_
for i in M:
    if i not in BY_I: continue
    if time.time()-t0 > WALL:
        print(f"  DUNG SINH o {time.time()-t0:.0f}s — bo qua {i} va sau do", flush=True); break
    print(f"\n=== SUA boi {i} ({len(BY_I[i])} cap) ===", flush=True)
    mo, tk = load(M[i][0])
    for s in BY_I[i]:
        if time.time()-t0 > WALL:
            print(f"  DUNG SINH giua chung — bo {s}->{i}", flush=True); break
        up = [f"{Q[k]}\n\nCandidate solution:\n{RAW[s][k]}" for k in range(N)]
        RAWV[f"{s}->{i}"] = gen(mo, tk, FIX, up, 16, f"{s}->{i}")
        print(f"  {s}->{i}: sinh xong ({time.time()-t0:.0f}s)", flush=True)
        save_partial()
    mo = None; tk = None; free()
    for s in BY_I[i]:
        key = f"{s}->{i}"
        if key not in RAWV: continue
        PASSV[key] = [eq(_bx(RAWV[key][k]), GOLD[k]) for k in range(N)]
        print(f"  {key}: acc_V={sum(PASSV[key])/N:.4f}", flush=True)
    save_partial()

box = {t: round(sum(_bx(x) is not None for x in v)/N, 4) for t, v in RAW.items()}
boxv = {k: round(sum(_bx(x) is not None for x in v)/N, 4) for k, v in RAWV.items()}
run_gates = {"n>=480": N >= 480,
             "moi acc nen trong [.10,.90]": all(.10 <= a <= .90 for a in acc.values())}

pairs, bo_cap = [], []
for s, i in DIRECTED:
    key = f"{s}->{i}"
    if key not in PASSV:
        bo_cap.append({"cap": key, "vi_sao": "chua chay xong (het gio)"}); continue
    g_box = boxv[key] >= .90
    g_sym = abs(boxv[key] - box[i]) < .05
    if not (g_box and g_sym):
        bo_cap.append({"cap": key, "boxed_V": boxv[key], "boxed_I_nen": box[i],
                       "vi_sao": [n for n, v in [("boxed_V>=.90", g_box),
                                                 ("|boxV-boxI|<.05", g_sym)] if not v]})
        continue
    S_, I_, V_ = PASS[s], PASS[i], PASSV[key]
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

def p2(b, s):
    if s <= 0: return 1.0
    return round(math.erfc(abs(b/s)/(2**.5)), 6)

res = {"tag": RUN, "mien": "MATH-500", "MAXNEW": MAXNEW, "n": N, "acc": acc,
       "acc_V": {k: round(sum(v)/N, 4) for k, v in PASSV.items()},
       "boxed_rate": box, "boxed_rate_V": boxv,
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
json.dump({"pass": PASS, "pass_v": PASSV, "acc": acc, "n": N, "gold": GOLD},
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

MBPP_GSTAR, MBPP_D1, MBPP_R2B = .0913, -.23922, .3451
print(f"\n==== H99 {RUN} (MATH-500) ====")
print(f"  n={N} | MAXNEW={MAXNEW} | acc nen: {acc}")
print(f"  boxed nen: {box}")
print(f"  cong lan chay: {run_gates}")
if bo_cap:
    print(f"  CAP BI LOAI ({len(bo_cap)}):")
    for z in bo_cap: print(f"     {z}")
print(f"\n  {'S':10s}{'I':10s}{'gap':>8s}{'A':>8s}{'B':>8s}{'C':>8s}{'d_ceil':>9s}{'p':>10s}  =ABC")
for q in sorted(pairs, key=lambda z: z["gap"]):
    print(f"  {q['S']:10s}{q['I']:10s}{q['gap']:+8.4f}{q['A']:8.4f}{q['B']:8.4f}{q['C']:8.4f}"
          f"{q['d_ceil']:+9.4f}{q['p_ceil']:10.4g}  {q['khop_dang_thuc']}")
if pairs and not all(q["khop_dang_thuc"] for q in pairs):
    print("  !! DANG THUC A-B+C KHONG KHOP — LOI CAI DAT, KHONG DUOC DOC SO")

print("\n-- BANG KHOA #109 --")
if VOID:
    print(f"  -> HANG 0: VOID {VOID}")
elif "ols_ceil" not in res:
    print("  -> khong du cap de hoi quy")
else:
    o = res["ols_ceil"]; gs = o["g_star"]
    print(f"  MATH : d_ceil ~ {o['d0']:+.5f} {o['d1_gap']:+.5f}*chenh  R2={o['R2']:.4f} "
          f"p={o['p_d1']:.4g}  g*={gs}")
    print(f"  MBPP : d_ceil ~ +0.02184 {MBPP_D1:+.5f}*chenh  R2=0.5998  p=1e-05  g*={MBPP_GSTAR}")
    if o["p_d1"] >= .05 or o["R2"] < .50:
        print("  -> HANG 4: chenh KHONG du bao d_ceil tren MATH => luat #185 la DAC THU CODE.")
        print("     => PHAI rut luat khoi README hoac gan nhan 'chi code'. Lam NGAY vong nay.")
    elif o["d1_gap"] >= 0:
        print("  -> do doc KHONG am du bao khong ap dung: ghi nhan, dieu tra. Khong ep vao hang nao.")
    elif gs is None:
        print("  -> g* khong tinh duoc; ghi nhan.")
    elif .061 <= gs <= .121:
        print("  -> HANG 1: LUAT CHUYEN DUOC. g* ~ .09 o ca hai mien => luat ve GIAO THUC.")
    elif gs < .061:
        print("  -> HANG 2: chuyen ve DANG, khong ve SO. MATH khac nghiet hon; g* PHU THUOC MIEN.")
        print("     => PHAI thu hep luat o README thanh 'tren code' + neu g* rieng tung mien.")
    else:
        print("  -> HANG 3: MATH DE hon MBPP — mau thuan H88f. Khong ket luan, phai dieu tra.")
    if "ols_B" in res:
        rb = res["ols_B"]
        print(f"\n  PHU: B ~ chenh  R2={rb['R2']:.4f} (MBPP {MBPP_R2B})  b1={rb['b1_gap']:+.5f} p={rb['p_b1']:.4g}")
        print("       -> " + ("ca hai mien deu noi B KHONG bi chenh dinh doat (cung co cho mo cho giao thuc)"
                              if rb["R2"] < .50 else "tren MATH thi B BI chenh dinh doat — khac MBPP"))
    for nm in ("ols_A", "ols_C"):
        if nm in res:
            r_ = res[nm]
            print(f"  mo ta: {nm[4:]} ~ {r_['b0']:+.5f} {r_['b1_gap']:+.5f}*chenh  R2={r_['R2']:.4f}")
print("XONG", flush=True)
