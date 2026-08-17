# H96 (dang ky truoc #106) — BAN DO DU DIA: tach HO khoi CHENH NANG LUC.
# Sau model, MOT luot greedy moi model, CUNG bo bai MBPP 11-510. KHONG co nhanh V.
# Dai luong: A = P(S dung & I sai) cho MOI cap co huong (I manh hon S) -> 15 cap.
# Bang khoa #106: hoi quy A ~ b0 + b1*(I-S) + b2*khac_ho; b2 tra loi cau hoi.
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

# thu tu nap: nho -> lon, de neu het gio thi van co cac model nho
SPEC = [("qwen1.5b", ("1-5b", "1_5b", "1.5b"), "qwen"),
        ("qwen7b",   ("2-5-7b", "qwen2-5-7b"), "qwen"),
        ("qwen14b",  ("14b",),                 "qwen"),
        ("qwen32b",  ("32b",),                 "qwen"),
        ("llama8b",  ("llama-3-1-8b", "llama-3.1-8b"), "llama"),
        ("dscoder",  ("deepseek-coder-6-7b", "deepseek-coder-6.7b"), "deepseek")]
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
def gen(mo, tk, usrs, bs):
    outs, i = [], 0
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            ps = [tk.apply_chat_template([{"role":"system","content":SOLVE},{"role":"user","content":u}],
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
        if i == 0:   # #155 + #173: kiem tinh tinh va cat cut ngay lo dau
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

t0 = time.time()
RAW, PASS = {}, {}
for tag, (path, fam) in M.items():
    print(f"\n=== {tag} ({fam}) ===", flush=True)
    mo, tk = load(path)
    RAW[tag] = gen(mo, tk, PR, 16)
    mo = None; tk = None; free()
    PASS[tag] = par(official, [(ALL[i], extract(RAW[tag][i])) for i in range(N)])
    print(f"  {tag}: acc={sum(PASS[tag])/N:.4f} ({time.time()-t0:.0f}s)", flush=True)
    json.dump({"partial": True, "run": RUN, "n": N, "done": sorted(RAW),
               "raw": RAW, "pass": {k: v for k, v in PASS.items()}},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))

A_ = lambda p: round(sum(p)/N, 4)
ext = {t: round(sum(compiles(extract(x)) for x in v)/N, 4) for t, v in RAW.items()}
trunc = {t: round(sum(_unclosed(x) for x in v)/N, 4) for t, v in RAW.items()}
acc = {t: A_(PASS[t]) for t in PASS}
gates = {"extract_min>=.80": min(ext.values()) >= .80,
         "extract_spread<.05": (max(ext.values()) - min(ext.values())) < .05,
         "truncation<.05": max(trunc.values()) < .05,
         "n>=480": N >= 480,
         "moi acc trong [.30,.90]": all(.30 <= a <= .90 for a in acc.values())}
VOID = [k for k, v in gates.items() if not v]

pairs = []
for s in M:
    for i in M:
        if s == i or acc[i] <= acc[s]: continue
        A = sum(1 for k in range(N) if PASS[s][k] and not PASS[i][k])/N
        b01, b10, p = mcnemar(PASS[s], PASS[i])
        pairs.append({"S": s, "I": i, "acc_S": acc[s], "acc_I": acc[i],
                      "gap": round(acc[i]-acc[s], 4), "A": round(A, 4),
                      "khac_ho": M[s][1] != M[i][1], "p_gap": p})

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
    dof = n_-k
    s2 = sum(e*e for e in resid)/dof if dof > 0 else float("nan")
    inv = [[1.0 if a == b else 0.0 for b in range(k)] for a in range(k)]
    Aug2 = [XtX[r][:] + inv[r] for r in range(k)]
    for c in range(k):
        piv = max(range(c, k), key=lambda r: abs(Aug2[r][c]))
        Aug2[c], Aug2[piv] = Aug2[piv], Aug2[c]
        d = Aug2[c][c]
        for cc in range(2*k): Aug2[c][cc] /= d
        for r in range(k):
            if r == c: continue
            f = Aug2[r][c]
            for cc in range(2*k): Aug2[r][cc] -= f*Aug2[c][cc]
    se = [ (s2*Aug2[a][k+a])**.5 for a in range(k) ]
    return beta, se, dof

res = {"tag": RUN, "n": N, "acc": acc, "extract_rate": ext, "truncation_rate": trunc,
       "gates": gates, "VOID": VOID, "pairs": pairs}
if len(pairs) >= 4:
    y = [q["A"] for q in pairs]
    X = [[1.0, q["gap"], 1.0 if q["khac_ho"] else 0.0] for q in pairs]
    out = ols(y, X)
    if out:
        beta, se, dof = out
        # p hai phia xap xi bang phan phoi chuan (dof nho -> chi la uoc luong)
        def p2(b, s):
            if s <= 0: return 1.0
            z = abs(b/s)
            return round(math.erfc(z/(2**.5)), 6)
        res["ols"] = {"b0": round(beta[0], 5), "b1_gap": round(beta[1], 5), "b2_khacho": round(beta[2], 5),
                      "se": [round(x, 5) for x in se], "dof": dof,
                      "p_b1": p2(beta[1], se[1]), "p_b2": p2(beta[2], se[2])}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump({"pass": PASS, "acc": acc, "n": N,
           "task_id": [r["task_id"] for r in ALL]},
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print(f"\n==== H96 {RUN} ====")
print(f"  n={N} | trich {ext} | cat cut {trunc}")
print(f"  acc: {acc}")
print(f"\n  {'S':10s}{'I':10s}{'acc_S':>8s}{'acc_I':>8s}{'gap':>8s}{'A':>8s}  khac ho")
for q in sorted(pairs, key=lambda z: -z["gap"]):
    print(f"  {q['S']:10s}{q['I']:10s}{q['acc_S']:8.4f}{q['acc_I']:8.4f}{q['gap']:+8.4f}{q['A']:8.4f}  {q['khac_ho']}")
print("\n-- BANG KHOA #106 --")
if VOID:
    print(f"  -> HANG 0: VOID {VOID}")
elif "ols" not in res:
    print("  -> khong du cap de hoi quy")
else:
    o = res["ols"]
    print(f"  A ~ {o['b0']:+.5f} + {o['b1_gap']:+.5f}*(I-S) + {o['b2_khacho']:+.5f}*khac_ho   (dof={o['dof']})")
    print(f"     p(b1_gap)={o['p_b1']:.4g}  p(b2_khacho)={o['p_b2']:.4g}")
    if o["b2_khacho"] >= .02 and o["p_b2"] < .05:
        print("  -> HANG 1: HO co tac dung RIENG, khong chi la chenh nang luc.")
    elif (abs(o["b2_khacho"]) < .02 or o["p_b2"] >= .05) and o["p_b1"] < .05:
        print("  -> HANG 2: CHI CHENH NANG LUC quan trong. 'Khac ho' o #179 la GIA TUONG QUAN")
        print("     => PHAI sua dien giai cua #145/#169 trong TONG_HOP.")
    elif o["p_b1"] >= .05 and o["p_b2"] >= .05:
        print("  -> HANG 3: 15 cap khong du luc; khong ket luan.")
    else:
        print("  -> HANG 4: khac ho co A THAP hon khi da kiem soat chenh — dieu tra lai.")
print("XONG", flush=True)
