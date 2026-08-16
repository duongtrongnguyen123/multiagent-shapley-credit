# H70 (dang ky truoc #75) — TACH CHE DO / NGUON tren TOAN (MATH-500).
# Solver CO DINH = 1.5B. Verifier chay o BA muc: 1.5B(fp16) / 7B(nf4) / 14B(nf4), 2x T4,
# MOI GPU mot ban sao (data parallel). RTX 6000 Pro het hieu luc — xem #70-b.
# poisoning(M) = acc(V_M) - acc(I_M): M xem loi giai cua S so voi M tu giai.
# MATH-500 (GSM8K da bao hoa o 7B: .908-.934). Gold lay tu \boxed trong cot Answer (da kiem 500/500).
import os, re, csv, json, glob, time, threading, subprocess, sys, gc, torch
if os.environ.get("NEED_BNB", "1") == "1":
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

RUN = "@@RUN@@"

def save_partial(stage=""):
    """#128/#134: luu DU LIEU THO sau moi chang. Khong can biet ten bien cua tung kernel —
    chup MOI bien toan cuc la list[str] du dai. Tieu chuan: neu kernel chet o dong ngay sau,
    file nay phai CHAM DIEM duoc."""
    try:
        snap = {k: v for k, v in list(globals().items())
                if isinstance(v, list) and len(v) >= 10
                and isinstance(v[0], (str, list, bool, int, float))}
        json.dump({"partial": True, "run": RUN, "stage": stage,
                   "keys": sorted(snap), "raw": snap},
                  open(f"/kaggle/working/partial_{RUN}.json", "w"))
        print(f"    [partial] {stage}: {sorted(snap)}", flush=True)
    except Exception as _e:
        print(f"    [partial] LOI: {_e}", flush=True)

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
     "7B":   find_model("7b")}
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
BSZ = BSZ_BIG if BIG else BSZ_SMALL
t0 = time.time()

m15, tk15 = load("1.5B")
SOLS = gen(m15, tk15, SOLVE, Q, BSZ["1.5B"])
_free_models(m15); m15 = None; gc.collect()
for _d in range(torch.cuda.device_count()):
    with torch.cuda.device(_d): torch.cuda.empty_cache()
print(f"S (1.5B) xong ({time.time()-t0:.0f}s)", flush=True)

save_partial("S (1.5B)")
m7, tk7 = load("7B")
IND = gen(m7, tk7, SOLVE, Q, BSZ["7B"])
print(f"I xong ({time.time()-t0:.0f}s)", flush=True)
save_partial("I")
VW = gen(m7, tk7, VERIFY, [f"{Q[i]}\n\nProposed solution:\n{SOLS[i]}" for i in range(N)], BSZ["7B"])
print(f"V_weak xong ({time.time()-t0:.0f}s)", flush=True)
save_partial("V_weak")
VS = gen(m7, tk7, VERIFY, [f"{Q[i]}\n\nProposed solution:\n{IND[i]}" for i in range(N)], BSZ["7B"])
print(f"V_self xong ({time.time()-t0:.0f}s)", flush=True)

save_partial("V_self")
OUT = {"S": SOLS, "I": IND, "V_weak": VW, "V_self": VS}
A = {k: [_bx(t) or (re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I) or [None])[-1]
         for t in v] for k, v in OUT.items()}
def acc(k, lo=0, hi=None):
    hi = N if hi is None else hi
    return round(sum(eq(A[k][i], GOLD[i]) for i in range(lo, hi)) / (hi - lo), 4)
FOLD = N // 5
accS, accI = acc("S"), acc("I")
res = {"tag": RUN, "n": N, "quant": QUANT, "S": accS, "I": accI, "I_minus_S": round(accI-accS, 4), "arms": {}}
for k in ["V_self", "V_weak"]:
    v = A[k]
    pois = [i for i in range(N) if eq(A["I"][i], GOLD[i]) and not eq(v[i], GOLD[i])]
    resc = [i for i in range(N) if not eq(A["I"][i], GOLD[i]) and eq(v[i], GOLD[i])]
    ref = A["I"] if k == "V_self" else A["S"]
    same = [i for i in pois if v[i] is not None and eq(v[i], ref[i])]
    res["arms"][k] = {"acc": acc(k), "minus_I": round(acc(k)-accI, 4),
        "poisoned": len(pois), "rescued": len(resc),
        "kept_same": len(same), "third": len(pois)-len(same),
        "unchanged_rate": round(sum(1 for i in range(N) if v[i] is not None and eq(v[i], ref[i]))/N, 4),
        "folds": [round(acc(k, f*FOLD, (f+1)*FOLD) - acc("I", f*FOLD, (f+1)*FOLD), 4) for f in range(5)]}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"q": Q[i][:500], "gold": GOLD[i], **{k: (OUT[k][i] or "")[:1200] for k in OUT},
            **{k+"_ans": A[k][i] for k in A}} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

ds = res["arms"]["V_self"]["minus_I"]; dw = res["arms"]["V_weak"]["minus_I"]
BOXR = {k: round(sum(1 for t in OUT[k] if "\\boxed" in (t or "")) / N, 4) for k in OUT}
res["boxed_rate"] = BOXR
bmin = min(BOXR.values()); bspread = max(BOXR.values()) - bmin
print("\n==== H70 TONG KET ====")
print(f"  ti le co \\boxed: {BOXR}")
print(f"  cong cat ngan: min {bmin:.4f} (can >= .80) | chenh {bspread:.4f} (can < .05) -> "
      f"{'DAT' if bmin >= .80 and bspread < .05 else 'HUY — KHONG DOC'}")
print(f"  n={N} | quant={QUANT} | S={accS:.4f} | I={accI:.4f}")
for k in ["V_self", "V_weak"]:
    r = res["arms"][k]
    print(f"  {k:7s} acc={r['acc']:.4f}  -I={r['minus_I']:+.4f}  doc/cuu={r['poisoned']}/{r['rescued']}  "
          f"giu/thu-ba={r['kept_same']}/{r['third']}  unchanged={r['unchanged_rate']:.4f}")
    print(f"          fold: {r['folds']}")
print(f"  V_self - V_weak = {round(res['arms']['V_self']['acc']-res['arms']['V_weak']['acc'],4):+.4f}")
if ds < 0 and dw < 0 and abs(ds+ (dw-ds)) > 1e-9:
    tot = dw
    print(f"  phan CHE DO = {ds:+.4f} ({abs(ds/tot)*100:.0f}%) | phan THEM cua NGUON = {dw-ds:+.4f} ({abs((dw-ds)/tot)*100:.0f}%)   [code: 38%/62%]")
print(f"\n  cong I-S = {accI-accS:+.4f} ({'DAT' if accI-accS>=.05 else 'HUY'})")
print(f"  cong acc(S) = {accS:.4f} ({'DAT' if .10 <= accS <= .55 else 'HUY'})")
print("\n-- bang khoa #84 --")
if bmin < .80 or bspread >= .05:
    print("  -> HUY: cong cat ngan truot, khong doc so nao")
    print("XONG", flush=True); raise SystemExit(0)
if accI-accS < .05 or not (.10 <= accS <= .55): print("  -> HUY: cong khong dat")
elif ds <= -.02 and (res["arms"]["V_self"]["acc"] - res["arms"]["V_weak"]["acc"]) >= .02:
    print("  -> HANG 1: PHEP TACH LAP LAI tren toan. Cau truc chung, khong dac thu code.")
elif abs(ds) < .02 and dw <= -.02:
    print("  -> HANG 2: tren toan che do sua chua KHONG ton gi; toan bo thiet hai do NGUON.")
    print("     => phep tach 38/62 la DAC THU CODE, phai noi ro pham vi o #105.")
elif abs(ds) < .02 and abs(dw) < .02:
    print("  -> HANG 3: khong co thiet hai nao tren toan o cap nay -> mau thuan H61, phai kiem GSM8K vs MATH.")
elif (res["arms"]["V_weak"]["acc"] - res["arms"]["V_self"]["acc"]) >= .02:
    print("  -> HANG 4: sua loi giai CUA CHINH MINH hai HON — bat ngo, phai tai lap.")
else: print("  -> giua cac hang: ghi ro so, khong ep.")
print("XONG", flush=True)
