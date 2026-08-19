# H78 (dang ky truoc #87) — 32B: DAU DOC CO TAN THEO NANG LUC KHONG?
# THIET KE DA SUA (kiem dinh #125-A2): BO hang 1.5B (do la TU-xem-lai, khong phai cross-model).
# Solver CO DINH = 1.5B. Chi doi nang luc VERIFIER: 7B / 14B / 32B, deu xem CUNG mot bo loi giai.
# bf16 toan bo, nap TUAN TU (15+29+68 = 112 GB > 95 GB), LUU TUNG PHAN sau moi model.
import os, re, csv, json, glob, time, gc, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = "@@RUN@@"
MAXNEW = 1280
BSZ = {"7B": 48, "14B": 24, "32B": 12}   # 32B: KV ~0.25 MB/token x 2100 token = 525 MB/chuoi

def find_model(*needles):
    cands = []
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            cands.append(p.rstrip("/"))
    if not cands: raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")
    return sorted(cands, key=len)[0]

M = {"1.5B": find_model("1-5b", "1_5b", "1.5b"),
     "7B":   find_model("2-5-7b", "qwen2-5-7b"),
     "14B":  find_model("14b"),
     "32B":  find_model("32b")}
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
CC = torch.cuda.get_device_capability(0)
VRAM = torch.cuda.get_device_properties(0).total_memory / 2**30
print(f"MODELS={json.dumps(M, indent=1)}\nGPU={torch.cuda.get_device_name(0)} | {VRAM:.1f} GB | sm_{CC[0]}{CC[1]}", flush=True)
if VRAM < 80: raise SystemExit(f"HUY: can >= 80 GB cho 32B bf16, chi co {VRAM:.1f} GB")
if CC[0] < 8: raise SystemExit(f"HUY: sm_{CC[0]}{CC[1]} khong ho tro bf16")

RAW = list(csv.DictReader(open(CSV, newline="", encoding="utf-8")))
def _col(r, *names):
    low = {str(k).strip().lower(): v for k, v in r.items()}
    for n in names:
        v = low.get(n)
        if isinstance(v, str) and v.strip(): return v
    return None
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

Q = [_col(r, "question", "problem") for r in RAW]
GOLD = [_bx(_col(r, "answer", "solution") or "") for r in RAW]
keep = [i for i in range(len(RAW)) if Q[i] and GOLD[i]]
Q = [Q[i] for i in keep]; GOLD = [GOLD[i].strip() for i in keep]
N = len(Q)
print(f"MATH-500: {N} bai", flush=True)
assert N >= 450

TAIL   = "Put the final answer in \\boxed{}."
SOLVE  = f"Solve step by step. {TAIL}"
VERIFY = f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"

def load(tag):
    p = M[tag]
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    mo = AutoModelForCausalLM.from_pretrained(p, dtype=torch.bfloat16, device_map={"": 0}).eval()
    print(f"  nap {tag}: VRAM {torch.cuda.memory_allocated(0)/2**30:.1f} GB", flush=True)
    return mo, tk
def free(mo=None):
    """LUU Y: 'del mo' TRONG ham chi xoa TEN CUC BO — model van song o bien cua caller.
    Vi the caller PHAI gan mo=None TRUOC khi goi. Ham nay chi lam gc + empty_cache."""
    gc.collect()
    for d in range(torch.cuda.device_count()):
        with torch.cuda.device(d): torch.cuda.empty_cache()
    print(f"  VRAM sau giai phong: " +
          " | ".join(f"gpu{d} {torch.cuda.memory_allocated(d)/2**30:.2f}" for d in range(torch.cuda.device_count())), flush=True)

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

t0 = time.time()
OUT = {}
mo, tk = load("1.5B")
OUT["S"] = gen(mo, tk, SOLVE, Q, 64)
mo = None; tk = None   # #159: 'tk = tk' la no-op, khong ha refcount
free()
print(f"S (1.5B) xong ({time.time()-t0:.0f}s)", flush=True)
VP = [f"{Q[i]}\n\nProposed solution:\n{OUT['S'][i]}" for i in range(N)]

for tag in ["7B", "14B", "32B"]:
    mo, tk = load(tag)
    OUT[f"I_{tag}"] = gen(mo, tk, SOLVE, Q, BSZ[tag])
    print(f"I_{tag} xong ({time.time()-t0:.0f}s)", flush=True)
    OUT[f"V_{tag}"] = gen(mo, tk, VERIFY, VP, BSZ[tag])
    print(f"V_{tag} xong ({time.time()-t0:.0f}s)", flush=True)
    mo = None; tk = None   # #159: 'tk = tk' la no-op, khong ha refcount
    free()
    json.dump({"partial": True, "done": sorted(OUT.keys()), "raw": OUT},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))
    print(f"  da luu partial_{RUN}.json ({len(OUT)} nhanh)", flush=True)

A = {k: [_bx(t) or (re.findall(r"(?:answer is|=)\s*\$?([^\n$]+)", t or "", re.I) or [None])[-1]
         for t in v] for k, v in OUT.items()}
def acc(k, lo=0, hi=None):
    hi = N if hi is None else hi
    return round(sum(eq(A[k][i], GOLD[i]) for i in range(lo, hi)) / (hi - lo), 4)
FOLD = N // 5
BOXR = {k: round(sum(1 for t in v if _bx(t) is not None) / N, 4) for k, v in OUT.items()}
bmin = min(BOXR.values()); bspread = max(BOXR.values()) - min(BOXR.values())

res = {"tag": RUN, "n": N, "S": acc("S"), "boxed_rate": BOXR,
       "boxed_min": bmin, "boxed_spread": round(bspread, 4), "caps": {}}
for tag in ["7B", "14B", "32B"]:
    I, V = A[f"I_{tag}"], A[f"V_{tag}"]
    pois = [i for i in range(N) if eq(I[i], GOLD[i]) and not eq(V[i], GOLD[i])]
    resc = [i for i in range(N) if not eq(I[i], GOLD[i]) and eq(V[i], GOLD[i])]
    echo = [i for i in pois if V[i] is not None and eq(V[i], A["S"][i])]
    res["caps"][tag] = {"I": acc(f"I_{tag}"), "V": acc(f"V_{tag}"),
        "poisoning": round(acc(f"V_{tag}") - acc(f"I_{tag}"), 4),
        "poisoned": len(pois), "rescued": len(resc),
        "echo": len(echo), "third": len(pois) - len(echo),
        "unchanged_rate": round(sum(1 for i in range(N) if V[i] is not None and eq(V[i], A["S"][i]))/N, 4),
        "folds": [round(acc(f"V_{tag}", f*FOLD, (f+1)*FOLD) - acc(f"I_{tag}", f*FOLD, (f+1)*FOLD), 4) for f in range(5)]}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"q": Q[i][:500], "gold": GOLD[i], **{k: (OUT[k][i] or "")[:1500] for k in OUT},
            **{k+"_ans": A[k][i] for k in A}} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H78 TONG KET ====")
print(f"  n={N} | S (1.5B) = {res['S']:.4f}")
print(f"  ti le co \\boxed: {BOXR}")
print(f"  CONG CAT NGAN: min {bmin:.4f} (>= .80) | chenh {bspread:.4f} (< .05) -> "
      f"{'DAT' if bmin >= .80 and bspread < .05 else 'HUY'}")
print(f"  {'nang luc':9s} {'I':>8s} {'V':>8s} {'poisoning':>11s} {'doc/cuu':>9s} {'nhai/thu ba':>12s} {'unchanged':>10s}")
for tag in ["7B", "14B", "32B"]:
    c = res["caps"][tag]
    print(f"  {tag:9s} {c['I']:8.4f} {c['V']:8.4f} {c['poisoning']:+11.4f} {c['poisoned']:4d}/{c['rescued']:<4d} "
          f"{c['echo']:5d}/{c['third']:<6d} {c['unchanged_rate']:10.4f}")
    print(f"      fold: {c['folds']}")
p7, p14, p32 = (res["caps"][t]["poisoning"] for t in ["7B", "14B", "32B"])
mono = abs(p32) < abs(p14) < abs(p7)
gapcap = round(res["caps"]["32B"]["I"] - res["caps"]["7B"]["I"], 4)
print(f"\n  giam deu |poisoning| 7B->14B->32B? {'CO' if mono else 'KHONG'}  ({abs(p7):.4f} -> {abs(p14):.4f} -> {abs(p32):.4f})")
print(f"  CONG NANG LUC: I_32B - I_7B = {gapcap:+.4f} ({'DAT' if gapcap >= .05 else 'HUY — 32B khong manh hon du .05'})")
print("\n-- bang khoa #87 --")
if bmin < .80 or bspread >= .05: print("  -> HUY: cong cat ngan truot, khong doc so nao")
elif gapcap < .05: print("  -> HUY: cong nang luc truot. MATH-500 greedy khong phan giai duoc nang luc trong dai nay.")
elif p32 > .02: print("  -> HANG 4: DAO DAU o 32B — xem lai loi giai yeu lai CO ICH. Kiem unchanged_rate truoc khi tin.")
elif p32 >= -.02 and mono: print("  -> HANG 1: DAU DOC TAN THEO NANG LUC. Phan bien 'model qua nho' DUNG.")
elif -.05 <= p32 < -.02 and mono: print("  -> HANG 2: co lai theo nang luc nhung CHUA het o 32B.")
else: print("  -> HANG 3: DAU DOC KHONG RUA DUOC BANG NANG LUC trong dai 7B-32B (hon 4.5x tham so).")
print("XONG", flush=True)
