# H65 (dang ky truoc #70) — DAU DOC CO TAN BIEN THEO NANG LUC KHONG?
# Solver CO DINH = 1.5B. Verifier chay o BA muc: 1.5B(fp16) / 7B(nf4) / 14B(nf4), 2x T4,
# MOI GPU mot ban sao (data parallel). RTX 6000 Pro het hieu luc — xem #70-b.
# poisoning(M) = acc(V_M) - acc(I_M): M xem loi giai cua S so voi M tu giai.
# MATH-500 (GSM8K da bao hoa o 7B: .908-.934). Gold lay tu \boxed trong cot Answer (da kiem 500/500).
import os, re, csv, json, glob, time, threading, subprocess, sys, gc, torch
if os.environ.get("NEED_BNB", "1") == "1":
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

RUN = "@@RUN@@"
MAXNEW = 1280   # #119: 640 cat nhanh I nhieu hon nhanh V (39.8% vs 25.4%) -> confound
BSZ_SMALL = {"1.5B": 32, "7B": 16, "14B": 8}    # T4 16 GB
BSZ_BIG   = {"1.5B": 96, "7B": 64, "14B": 32}   # RTX 6000 Pro 102 GB — tinh lai theo VRAM, khong chep

def find_model(*needles):
    """tim thu muc model theo TEN THU MUC, khong theo pattern file — vi ca ba model
    deu co model.safetensors(.index.json) nen glob theo file se lan lon."""
    cands = []
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        low = p.lower()
        if any(n in low for n in needles) and (
            os.path.exists(os.path.join(p, "config.json"))):
            cands.append(p.rstrip("/"))
    if not cands: raise RuntimeError(f"khong thay model cho {needles}: "
                                    f"co {sorted(os.listdir('/kaggle/input'))}")
    return sorted(cands, key=len)[0]

M = {"1.5B": find_model("1-5b", "1_5b", "1.5b"),
     "7B":   find_model("7b"),
     "14B":  find_model("14b")}
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
print(f"MODELS={json.dumps(M, indent=1)}\nCSV={CSV}", flush=True)
print(f"GPU={torch.cuda.get_device_name(0)} | "
      f"{torch.cuda.get_device_properties(0).total_memory/2**30:.1f} GB | "
      f"sm_{torch.cuda.get_device_capability(0)[0]}{torch.cuda.get_device_capability(0)[1]}", flush=True)

# newline="" BAT BUOC: de bai MATH co xuong dong trong o
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
    # \text{even} -> even (BOC RUOT, khong xoa: xoa ca cum se bien "even" thanh rong)
    s = re.sub(r"\\(?:text|mbox|textbf|mathrm)\s*\{([^{}]*)\}", r"\1", s)
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = s.replace("^{\\circ}", "").replace("^\\circ", "")
    s = re.sub(r"\\%|%", "", s)
    for p in _RM: s = re.sub(p, "", s)
    s = s.rstrip(".")
    s = re.sub(r"^\{(.*)\}$", r"\1", s)
    if re.fullmatch(r"-?\d+\.?\d*", s):
        try:
            f = float(s)
            s = str(int(f)) if f == int(f) else str(f)
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
print(f"MATH-500: {N}/{len(RAW)} bai co de + gold \\boxed", flush=True)
assert N >= 450, f"CSV hong: chi {N} bai"

TAIL   = "Put the final answer in \\boxed{}."
SOLVE  = f"Solve step by step. {TAIL}"
VERIFY = f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"

QUANT = {}
NG = torch.cuda.device_count()
DEVS = [f"cuda:{i}" for i in range(NG)]
CC = torch.cuda.get_device_capability(0)
VRAM = torch.cuda.get_device_properties(0).total_memory / 2**30
if CC[0] < 7:
    raise SystemExit(f"HUY: sm_{CC[0]}{CC[1]} (P100) — torch khong co kernel image. Cong GPU hong.")
# TU CHON do chinh xac theo phan cung (khuyen cao trong ghi chu Kaggle cua chinh minh):
#   card lon (>=40 GB, sm_80+) -> bf16 het, KHONG luong tu hoa -> khong con caveat #70-b
#   card nho (T4 16 GB)        -> nf4 cho 7B/14B, moi GPU mot ban sao
BIG = (VRAM >= 40 and CC[0] >= 8)
DT = torch.bfloat16 if CC[0] >= 8 else torch.float16
print(f"CHE DO: {'CARD LON -> bf16 khong luong tu hoa' if BIG else 'CARD NHO -> nf4 cho 7B/14B'}"
      f" | {NG} GPU | sm_{CC[0]}{CC[1]} | {VRAM:.1f} GB", flush=True)
BNB = None if BIG else BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
def load(tag):
    """MOT ban sao moi GPU -> data parallel that su (KHONG device_map='auto' = pipeline)."""
    p = M[tag]
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    if BIG or tag == "1.5B":
        mos = [AutoModelForCausalLM.from_pretrained(p, dtype=DT).to(d).eval() for d in DEVS]
        q = "bf16" if DT is torch.bfloat16 else "fp16"
    elif tag == "14B":
        # 14B nf4 KHONG vua MOT the T4 14.6 GB: 7.4 GB trong so 4-bit + embed/lm_head fp16
        # (152k x 5120 x 2 byte x 2 = ~3.1 GB) + dem nap -> cham tran. Trai MOT ban tren CA HAI the.
        mos = [AutoModelForCausalLM.from_pretrained(p, quantization_config=BNB,
                                                    device_map="auto").eval()]
        q = "nf4-auto"
    else:
        mos = [AutoModelForCausalLM.from_pretrained(p, quantization_config=BNB,
                                                    device_map={"": d}).eval() for d in DEVS]
        q = "nf4"
    QUANT[tag] = q
    print(f"nap {tag}: {len(mos)} ban sao {q} | VRAM {torch.cuda.memory_allocated()/2**30:.1f} GB", flush=True)
    return mos, tk

@torch.no_grad()
def _gen1(mo, tk, sysm, usrs, bs):
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
            bs = max(1, bs // 2); print(f"  OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs

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

def gen(mos, tk, sysm, usrs, bs):
    """chia deu cho cac ban sao, chay song song, ghep lai dung thu tu"""
    if len(mos) == 1: return _gen1(mos[0], tk, sysm, usrs, bs)
    parts = [list(range(j, len(usrs), len(mos))) for j in range(len(mos))]
    store, errs, lock = {}, [], threading.Lock()
    def work(mo, idxs):
        try:
            r = _gen1(mo, tk, sysm, [usrs[i] for i in idxs], bs)
            with lock: store.update(dict(zip(idxs, r)))
        except Exception as e:
            import traceback; traceback.print_exc()
            with lock: errs.append(e)
    ths = [threading.Thread(target=work, args=(mos[j], parts[j])) for j in range(len(mos)) if parts[j]]
    for t in ths: t.start()
    for t in ths: t.join()
    if errs: raise RuntimeError(f"luong sinh that bai: {errs[0]!r}")
    if len(store) != len(usrs): raise RuntimeError(f"thieu {len(usrs)-len(store)} dau ra")
    return [store[i] for i in range(len(usrs))]

BSZ = BSZ_BIG if BIG else BSZ_SMALL
t0 = time.time()
# ---- S = 1.5B tu giai. DONG THOI la I cho muc 1.5B (cung model, cung prompt, cung greedy) ----
m15, tk15 = load("1.5B")
SOLS = gen(m15, tk15, SOLVE, Q, BSZ["1.5B"])
VP   = [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(Q, SOLS)]
V15  = gen(m15, tk15, VERIFY, VP, BSZ["1.5B"])
_free_models(m15); m15 = None; gc.collect()
for _d in range(NG):
    with torch.cuda.device(_d): torch.cuda.empty_cache()
print(f"1.5B xong ({time.time()-t0:.0f}s)", flush=True)

OUT = {"S": SOLS, "I_1.5B": SOLS, "V_1.5B": V15}
for tag in ["7B", "14B"]:
    mo, tk = load(tag)
    OUT[f"I_{tag}"] = gen(mo, tk, SOLVE, Q, BSZ[tag])
    print(f"I_{tag} xong ({time.time()-t0:.0f}s)", flush=True)
    OUT[f"V_{tag}"] = gen(mo, tk, VERIFY, VP, BSZ[tag])
    print(f"V_{tag} xong ({time.time()-t0:.0f}s)", flush=True)
    # LUU TUNG PHAN: H65T sap o buoc 14B sau 2.7h va mat sach ket qua 1.5B/7B
    json.dump({"partial": True, "done": sorted(OUT.keys()), "quant": QUANT,
               "raw": {k: v for k, v in OUT.items()}},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))
    print(f"  da luu partial_{RUN}.json ({len(OUT)} nhanh)", flush=True)
    _free_models(mo); mo = None; gc.collect()
    # empty_cache()/memory_allocated() CHI tac dung len thiet bi HIEN TAI -> phai lap qua TUNG GPU.
    # Khong lam vay thi ban sao tren GPU 1 van chiem cho va 14B se OOM (loi cua H65T2).
    for _d in range(NG):
        with torch.cuda.device(_d): torch.cuda.empty_cache()
    free = " | ".join(f"gpu{_d} {torch.cuda.memory_allocated(_d)/2**30:.2f} GB" for _d in range(NG))
    print(f'  VRAM sau khi giai phong {tag}: {free}', flush=True)

A = {k: [_bx(t) or (re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I) or [None])[-1]
         for t in v] for k, v in OUT.items()}
def acc(k, lo=0, hi=None):
    hi = N if hi is None else hi
    return round(sum(eq(A[k][i], GOLD[i]) for i in range(lo, hi)) / (hi - lo), 4)

FOLD = N // 5
res = {"tag": RUN, "n": N, "quant": QUANT, "n_gpu": NG, "acc": {k: acc(k) for k in A}, "caps": {}}
for tag in ["1.5B", "7B", "14B"]:
    I, V = A[f"I_{tag}"], A[f"V_{tag}"]
    pois = [i for i in range(N) if eq(I[i], GOLD[i]) and not eq(V[i], GOLD[i])]
    resc = [i for i in range(N) if not eq(I[i], GOLD[i]) and eq(V[i], GOLD[i])]
    echo = [i for i in pois if V[i] is not None and eq(V[i], A["S"][i])]
    res["caps"][tag] = {
        "I": acc(f"I_{tag}"), "V": acc(f"V_{tag}"),
        "poisoning": round(acc(f"V_{tag}") - acc(f"I_{tag}"), 4),
        "poisoned": len(pois), "rescued": len(resc),
        "poisoned_echo": len(echo), "poisoned_third": len(pois) - len(echo),
        "folds": [round(acc(f"V_{tag}", f*FOLD, (f+1)*FOLD) - acc(f"I_{tag}", f*FOLD, (f+1)*FOLD), 4)
                  for f in range(5)]}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"q": Q[i][:600], "gold": GOLD[i], **{k: (OUT[k][i] or "")[:1500] for k in OUT},
            **{k+"_ans": A[k][i] for k in A}} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

BOXR = {k: round(sum(1 for t in OUT[k] if "\\boxed" in (t or "")) / N, 4) for k in OUT}
res["boxed_rate"] = BOXR
bmin = min(BOXR.values()); bspread = max(BOXR.values()) - bmin
print("\n==== H65 TONG KET ====")
print(f"  ti le co \\boxed: {BOXR}")
print(f"  CONG CAT NGAN: min {bmin:.4f} (>= .80) | chenh {bspread:.4f} (< .05) -> "
      f"{'DAT' if bmin >= .80 and bspread < .05 else 'HUY — KHONG DOC'}")
print(f"  n = {N} | S (1.5B giai) = {res['acc']['S']:.4f} | quant {QUANT} | {NG} GPU")
print(f"  {'nang luc':9s} {'I (tu giai)':>12s} {'V (xem S)':>11s} {'poisoning':>11s}  {'doc/cuu':>9s}  {'nhai/thu ba':>12s}")
for tag in ["1.5B", "7B", "14B"]:
    c = res["caps"][tag]
    print(f"  {tag:9s} {c['I']:12.4f} {c['V']:11.4f} {c['poisoning']:+11.4f}  "
          f"{c['poisoned']:4d}/{c['rescued']:<4d} {c['poisoned_echo']:5d}/{c['poisoned_third']:<6d}")
for tag in ["1.5B", "7B", "14B"]:
    print(f"    fold {tag}: {res['caps'][tag]['folds']}")
p15, p7, p14 = (res["caps"][t]["poisoning"] for t in ["1.5B", "7B", "14B"])
mono = abs(p14) < abs(p7) < abs(p15)
g1 = res["caps"]["14B"]["I"] - res["caps"]["7B"]["I"]
g2 = res["caps"]["7B"]["I"] - res["acc"]["S"]
print(f"\n  giam deu |poisoning| 1.5B->7B->14B? {'CO' if mono else 'KHONG'}"
      f"  ({abs(p15):.4f} -> {abs(p7):.4f} -> {abs(p14):.4f})")
print(f"  cong: acc(S) = {res['acc']['S']:.4f} ({'DAT' if .10 <= res['acc']['S'] <= .55 else 'HUY'})")
print(f"  cong: I_14B - I_7B = {g1:+.4f} ({'DAT' if g1 >= .05 else 'HUY — 14B khong manh hon that su'})")
print(f"  cong: I_7B - S     = {g2:+.4f} ({'DAT' if g2 >= .05 else 'HUY'})")
print("\n-- bang khoa #85 --")
if bmin < .80 or bspread >= .05:
    print("  -> HUY: cong cat ngan truot, khong doc so nao")
    print("XONG", flush=True); raise SystemExit(0)
if g1 < .05: print("  -> HUY: 14B khong manh hon 7B du .05 tren benchmark nay")
elif not (.10 <= res["acc"]["S"] <= .55): print("  -> HUY: acc(S) ngoai [.10,.55]")
elif p14 > .02:   print("  -> HANG 4: DAO DAU — o 14B doc loi giai yeu CO ICH.")
elif p14 >= -.02 and mono: print("  -> HANG 1: DAU DOC TAN THEO NANG LUC. La hien tuong cua model YEU.")
elif -.05 <= p14 < -.02 and mono: print("  -> HANG 2: co lai theo nang luc nhung CHUA het.")
else: print("  -> HANG 3: DAU DOC LA NOI TAI, khong rua duoc bang nang luc.")
print("XONG", flush=True)
