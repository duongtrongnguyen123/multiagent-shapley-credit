# H94 (dang ky truoc #104) — PHAN RA PHOI NHIEM tren TOAN: xac nhan #150.
# E0 = M khong thay gi | E3 = M thay TOAN BO loi giai cua S. CUNG mot lenh giai.
# Dai luong CHINH: Delta tren tang 'artifact SAI' va tang 'artifact DUNG'.
# (goc: H88c) — SUA CO CONG tren MATH-500.
# CHINH = d_ceil (cong ORACLE, khong phu thuoc chat luong z). Phu = cong tu-nhat-quan k=2 (DA BIET la tuong quan).
# MAXNEW=1280 + cong \boxed (bai hoc #119/#130: cat cut phat nhanh I nang hon nhanh V).
import os, re, csv, json, glob, time, gc, math, sys, subprocess, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = "@@RUN@@"
MAXNEW = 1536   # #101-b/#104
BSZ = {"cheap": 48, "dear": 24}
SEED = 1234

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")
M = {"cheap": find_model("1-5b", "1_5b", "1.5b"), "dear": find_model("2-5-7b", "qwen2-5-7b")}
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
VRAM = torch.cuda.get_device_properties(0).total_memory/2**30
CC = torch.cuda.get_device_capability(0)
print(f"MODELS={json.dumps(M,indent=1)}\nGPU={torch.cuda.get_device_name(0)} | {VRAM:.1f} GB | sm_{CC[0]}{CC[1]}", flush=True)

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

TAIL   = "Put the final answer in \\boxed{}."
SOLVE  = f"Solve step by step. {TAIL}"
REVIEW = f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"

def mcnemar(a, b):
    b01 = sum(1 for x, y in zip(a, b) if x and not y)
    b10 = sum(1 for x, y in zip(a, b) if y and not x)
    n = b01 + b10
    if n == 0: return b01, b10, 1.0
    k = min(b01, b10)
    return b01, b10, round(min(1.0, 2.0*sum(math.comb(n, i) for i in range(k+1))/(2.0**n)), 6)

BIG_CARD = (torch.cuda.get_device_properties(0).total_memory/2**30 >= 40)
if not BIG_CARD:
    # #162: hai kernel MATH KHONG he co duong luong tu hoa — Qwen-7B vao fp16 = 14.21 GB tren
    # card 14.56 GB, khong con cho cho KV cache => OOM ke ca o lo=1 (H88c chet dung the).
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
    from transformers import BitsAndBytesConfig
    _BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
print(f"CHE DO: {'card lon -> bf16' if BIG_CARD else 'card nho -> nf4 cho model dat'}", flush=True)

NG = torch.cuda.device_count(); DEVS = [f"cuda:{i}" for i in range(NG)]
def load(tag):
    p = M[tag]
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    # #178: dung CA HAI card (song song DU LIEU). H94b chet o tuong 12h vi chi dung 1 card:
    # E0 mat 5.7h, E3 chua kip chay. Hai ban sao -> ~2x nhanh.
    def _one(d):
        if BIG_CARD:
            return AutoModelForCausalLM.from_pretrained(p, dtype=torch.bfloat16, device_map={"": d}).eval()
        if tag == "cheap":
            return AutoModelForCausalLM.from_pretrained(p, torch_dtype=torch.float16).to(d).eval()
        return AutoModelForCausalLM.from_pretrained(p, quantization_config=_BNB, device_map={"": d}).eval()
    mo = [_one(d) for d in DEVS]
    _dtlab = "bf16" if BIG_CARD else ("fp16" if tag == "cheap" else "nf4")
    print(f"  nap {tag} ({_dtlab}) x{len(mo)} ban sao: " + " | ".join(
        f"gpu{d} cap phat {torch.cuda.memory_allocated(d)/2**30:.2f}" for d in range(NG)), flush=True)
    return mo, tk
def free():
    """#132: caller PHAI gan mo=None TRUOC khi goi — 'del mo' trong ham chi xoa ten cuc bo."""
    gc.collect()
    for d in range(torch.cuda.device_count()):
        with torch.cuda.device(d): torch.cuda.empty_cache()
    print("  sau giai phong: " + " | ".join(
        f"gpu{d} cap phat {torch.cuda.memory_allocated(d)/2**30:.2f} giu cho {torch.cuda.memory_reserved(d)/2**30:.2f}"
        for d in range(torch.cuda.device_count())), flush=True)

@torch.no_grad()
def _g1(mo, tk, sysm, usrs, bs, sample=False):
    outs, i = [], 0
    if sample: torch.manual_seed(SEED)
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                  tokenize=False, add_generation_prompt=True) for u in ch]
            e = tk(ps, return_tensors="pt", padding=True).to(mo.device)
            kw = dict(max_new_tokens=MAXNEW, pad_token_id=tk.pad_token_id)
            kw.update(dict(do_sample=True, temperature=0.8, top_p=0.95) if sample else dict(do_sample=False))
            o = mo.generate(**e, **kw)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs//2); print(f"    OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs

def gen(mos, tk, sysm, usrs, bs, sample=False):
    """#178: chia deu bai cho cac ban sao, chay song song."""
    if not isinstance(mos, list): mos = [mos]
    if len(mos) == 1: return _g1(mos[0], tk, sysm, usrs, bs, sample)
    import threading
    parts = [list(range(j, len(usrs), len(mos))) for j in range(len(mos))]
    store, errs, lock = {}, [], threading.Lock()
    def work(mo, idxs):
        try:
            r = _g1(mo, tk, sysm, [usrs[i] for i in idxs], bs, sample)
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

t0 = time.time()
def save_partial(**kw):
    json.dump({"partial": True, "run": RUN, "n": N, **kw},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))

mo, tk = load("cheap")
S_raw  = gen(mo, tk, SOLVE, Q, BSZ["cheap"])
print(f"S greedy xong ({time.time()-t0:.0f}s)", flush=True)
mo = None; tk = None
free()
save_partial(S_raw=S_raw)

mo, tk = load("dear")
E0_raw = gen(mo, tk, SOLVE, Q, BSZ["dear"])
print(f"E0 xong ({time.time()-t0:.0f}s)", flush=True)
save_partial(S_raw=S_raw, E0_raw=E0_raw)
# #104: CUNG lenh SOLVE, chi THEM ngu canh — tach NHIN THAY khoi DUOC LENH SUA
EP = [f"{Q[i]}\n\nA smaller model's attempt:\n{S_raw[i]}" for i in range(N)]
E3_raw = gen(mo, tk, SOLVE, EP, BSZ["dear"])
print(f"E3 xong ({time.time()-t0:.0f}s)", flush=True)
I_raw, V_raw = E0_raw, E3_raw
mo = None; tk = None
free()
save_partial(S_raw=S_raw, E0_raw=E0_raw, E3_raw=E3_raw)

ansS, ansI, ansV = (_bx(t) for t in S_raw), (_bx(t) for t in I_raw), (_bx(t) for t in V_raw)
AS, AI, AV = list(ansS), list(ansI), list(ansV)
AS2 = AS   # #178: bo nhanh S2 (khong dung cho #104); giu ten cho phan con lai
PS = [eq(AS[i],  GOLD[i]) for i in range(N)]
PI = [eq(AI[i],  GOLD[i]) for i in range(N)]
PV = [eq(AV[i],  GOLD[i]) for i in range(N)]
Z  = [AS[i] is not None and AS2[i] is not None and eq(AS[i], AS2[i]) for i in range(N)]  # tu nhat quan k=2
p_esc = round(1 - sum(Z)/N, 4)
# #190: cong 2 cua #104 (block/dap an CHUA DONG). Tren TOAN khong co rao ```, dau hieu tuong
# duong cua "chua dong" la sinh DUNG HET ngan sach token => bi cat giua chung.
# Dem lai bang tokenizer tren CPU sau khi da giai phong GPU (khong ton VRAM).
_tkc = AutoTokenizer.from_pretrained(M["dear"])
def _hit_cap(txt):
    return len(_tkc(txt, add_special_tokens=False)["input_ids"]) >= MAXNEW
NTOK = {"S": [_hit_cap(t) for t in S_raw],
        "I": [_hit_cap(t) for t in I_raw],
        "V": [_hit_cap(t) for t in V_raw]}
TRUNC = {k: round(sum(v)/N, 4) for k, v in NTOK.items()}
print(f"  cat cut (cham tran {MAXNEW} token): {TRUNC}", flush=True)

PG_V  = [PS[i] if Z[i]  else PV[i] for i in range(N)]
PG_I  = [PS[i] if Z[i]  else PI[i] for i in range(N)]
PGO_V = [PS[i] if PS[i] else PV[i] for i in range(N)]

A = lambda p: round(sum(p)/N, 4)
d_ceil   = round(A(PGO_V) - A(PI), 4)          # CHINH (#97-b)
d_gate   = round(A(PG_V) - A(PV), 4)           # phu, tham do
d_honest = round(A(PG_V) - A(PI), 4)           # phu, tham do
d_VI     = round(A(PV) - A(PI), 4)
d_IS     = round(A(PI) - A(PS), 4)
mc = {"ceil": mcnemar(PI, PGO_V), "gate": mcnemar(PV, PG_V), "honest": mcnemar(PI, PG_V),
      "VI": mcnemar(PI, PV), "IS": mcnemar(PS, PI)}

BOX = {k: round(sum(1 for t in v if _bx(t) is not None)/N, 4)
       for k, v in (("S", S_raw), ("I", I_raw), ("V", V_raw))}
bmin, bspread = min(BOX.values()), round(max(BOX.values())-min(BOX.values()), 4)
# #190: hien thuc DUNG NAM cong cua #104 — khong thieu, khong thua.
# Bo cong `.15<=p_esc<=.90`: no thuoc dong kernel DINH TUYEN, #104 khong he yeu cau no,
# va nhanh dinh tuyen KHONG phai dai luong cua #104.
gates = {"boxed_min>=.80": bmin >= .80, "boxed_spread<.05": bspread < .05,
         "cat cut <.05 moi nhanh": max(TRUNC.values()) < .05,
         "n>=450": N >= 450,
         "I-S>=.05": d_IS >= .05, "p(I-S)<.05": mc["IS"][2] < .05,
         "S sai>=30% va dung>=20%": (1-A(PS)) >= .30 and A(PS) >= .20}
VOID = [k for k, v in gates.items() if not v]

res = {"tag": RUN, "n": N, "MAXNEW": MAXNEW,
       "acc": {"S": A(PS), "I": A(PI), "V": A(PV), "G_V": A(PG_V), "G_I": A(PG_I), "Go_V": A(PGO_V)},
       "delta": {"ceil": d_ceil, "gate": d_gate, "honest": d_honest,
                 "V_minus_I": d_VI, "I_minus_S": d_IS},
       "mcnemar": {k: {"b01": v[0], "b10": v[1], "p": v[2]} for k, v in mc.items()},
       "p_esc": p_esc, "truncation_rate": TRUNC, "boxed_rate": BOX, "boxed_min": bmin, "boxed_spread": bspread,
       "gates": gates, "VOID": VOID,
       "S_right_I_wrong": sum(1 for i in range(N) if PS[i] and not PI[i]),
       "V_destroys": sum(1 for i in range(N) if PS[i] and not PV[i]),
       "gate_accept_but_wrong": sum(1 for i in range(N) if Z[i] and not PS[i])}
# ---- #104: PHAN RA theo artifact cua S DUNG hay SAI ----
RIGHT = [i for i in range(N) if PS[i]]
WRONG = [i for i in range(N) if not PS[i]]
def strat(idx):
    if not idx: return {"n": 0}
    a = sum(PI[i] for i in idx)/len(idx); b = sum(PV[i] for i in idx)/len(idx)
    return {"n": len(idx), "E0": round(a,4), "E3": round(b,4), "delta": round(b-a,4),
            "mcnemar": dict(zip(("b01","b10","p"), mcnemar([PI[i] for i in idx], [PV[i] for i in idx])))}
res["strat"] = {"artifact_DUNG": strat(RIGHT), "artifact_SAI": strat(WRONG)}
res["gates"]["S sai >=30% va dung >=20%"] = (len(WRONG)/N >= .30 and len(RIGHT)/N >= .20)
res["VOID"] = [k for k, v in res["gates"].items() if not v]
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump({"raw": {"S": S_raw, "I": I_raw, "V": V_raw}, "gold": GOLD},   # #178: bo S2
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print(f"\n==== H88c {RUN} (MATH-500) ====")
print(f"  n={N} | \\boxed {BOX} (min {bmin}, chenh {bspread}) | p_esc={p_esc}")
for k in ["S", "I", "V", "G_V", "G_I", "Go_V"]: print(f"  {k:6s} {res['acc'][k]:.4f}")
print(f"\n  CHINH  d_ceil   = {d_ceil:+.4f} (G*_V vs I)  p={mc['ceil'][2]}")
print(f"  phu    d_gate   = {d_gate:+.4f}  p={mc['gate'][2]}")
print(f"  phu    d_honest = {d_honest:+.4f}  p={mc['honest'][2]}")
print(f"         V - I    = {d_VI:+.4f}  p={mc['VI'][2]}   |  I - S = {d_IS:+.4f}")
print(f"  S dung ma I sai: {res['S_right_I_wrong']} bai  (= tran cua cong ORACLE)")
print(f"  V pha {res['V_destroys']} bai S lam dung | cong nhan nham {res['gate_accept_but_wrong']}")

print(f"\n  PHAN RA (#104): artifact DUNG {res['strat']['artifact_DUNG']}")
print(f"                  artifact SAI  {res['strat']['artifact_SAI']}")
_w = res["strat"]["artifact_SAI"]; _r = res["strat"]["artifact_DUNG"]
print("\n-- BANG KHOA #104 --")
if res["VOID"]: print(f"  -> HANG 0: VOID {res['VOID']}")
elif _w.get("delta", 0) <= -.10 and _w["mcnemar"]["p"] < .05 and _r.get("delta", -1) >= 0:
    print("  -> HANG 1: XAC NHAN #150 va tong quat sang TOAN. D la ham cua NOI DUNG SAI.")
elif _w.get("delta", 0) <= -.10 and _w["mcnemar"]["p"] < .05:
    print("  -> HANG 2: thay BAT KY artifact nao cung hai; 'sai' chi khuech dai. Thu hep #150.")
elif -.10 < _w.get("delta", 0) <= -.02 and _w["mcnemar"]["p"] < .05:
    print("  -> HANG 3: hai YEU HON tren toan => bien do phu thuoc MIEN.")
else:
    print("  -> HANG 4: KHONG tai lap tren toan. #150 chi dung cho code, giu nguyen la tham do.")
print("\n-- (tham khao) bang khoa #97 --")
if VOID:
    print(f"  -> HANG 0: VOID, cong chat luong truot: {VOID}. KHONG doc so nao.")
elif d_ceil <= 0 or (mc["ceil"][2] >= .05 and abs(d_ceil) < .02):
    print("  -> HANG 1: GIET CA DONG SUA TREN TOAN. Cong ORACLE cung khong vuot I")
    print("     => tren MATH khong co gi de khai thac tu artifact cua S, bat ke tin hieu tot den dau.")
else:
    print(f"  -> KHONG phai hang 1: con {d_ceil:+.4f} de khai thac tren toan (tran cua cong).")
    print("     Hang 2/3/4 KHONG ap dung — z tu-nhat-quan da biet truoc la TUONG QUAN (#97-b).")
    print(f"     Cong kha thi bat duoc {d_honest:+.4f} / {d_ceil:+.4f} cua tran"
          f" = kappa ~ {round(d_honest/d_ceil, 3) if d_ceil > 0 else 'n/a'}")
print("XONG", flush=True)
