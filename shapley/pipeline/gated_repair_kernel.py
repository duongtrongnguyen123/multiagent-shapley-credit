# H88 (dang ky truoc #97) — SUA CO CONG: D co bien mat khi cong bang tin hieu doc lap khong?
# Sinh MOT lan (S, I, V, TESTS) roi ghep nhanh OFFLINE -> moi nhanh dung CUNG artifact.
#   S     1.5B tu giai
#   I     7B tu giai, khong thay gi          <- MOC THAT
#   V     7B xem code cua S roi sua (vo dieu kien)
#   z     test do S tu viet, CHAY THAT tren code cua S
#   G_V   z dat -> giu S ; z truot -> V
#   G_I   z dat -> giu S ; z truot -> I      (khong cho thay artifact)
#   G*_V  cong ORACLE: S dung THAT -> giu S ; sai -> V   <- CHAN TREN, khong phai he thong
import os
# #134: phai dat TRUOC khi import torch. Giam phan manh — H89 con 2.88 GB "giu cho" sau khi
# da giai phong sach (cap phat 0.01), va chinh 2.88 GB do gop phan lam OOM khi nap model 8B.
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
import re, json, glob, time, gc, math, tempfile, subprocess, sys, torch
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN, LO, HI = "@@RUN@@", int("@@LO@@"), int("@@HI@@")
DEAR_NEEDLES = [s for s in "@@DEAR@@".split(",") if s]   # model DAT: doi ho de kiem #98
MAXNEW, TIMEOUT = 3072, 60   # #101-d: luoi an toan; chan chinh la stop_strings
BSZ = {"cheap": 24, "dear": 16}

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")
CHEAP_NEEDLES = [x for x in "@@CHEAP@@".split(",") if x]   # #142: tang RE cung tham so hoa
M = {"cheap": find_model(*CHEAP_NEEDLES), "dear": find_model(*DEAR_NEEDLES)}
SAME_FAMILY = any("qwen" in n for n in DEAR_NEEDLES)
# #143: RTX 6000 chay trong competition -> KHONG co internet. H91 chet ngay dong nay
# ("Cannot send a request, as the client has been closed") truoc khi in duoc gi.
# Uu tien dataset JSON da stage; chi goi HuggingFace khi that su co mang.
_hits = sorted(glob.glob("/kaggle/input/**/mbpp_full.json", recursive=True), key=len)
if _hits:
    print(f"MBPP nap tu dataset da stage: {_hits[0]}", flush=True)
    _DS = json.load(open(_hits[0]))
else:
    print("khong mount duoc mbpp_full.json -> thu HuggingFace (can internet)", flush=True)
    from datasets import load_dataset
    _D = load_dataset("mbpp", "full", split="test+train+validation")
    _DS = [{k: r[k] for k in ["task_id", "text", "code", "test_list"]} for r in _D]
CC = torch.cuda.get_device_capability(0); VRAM = torch.cuda.get_device_properties(0).total_memory/2**30
print(f"MODELS={json.dumps(M,indent=1)}\nGPU={torch.cuda.get_device_name(0)} | {VRAM:.1f} GB | sm_{CC[0]}{CC[1]}\n"
      f"DAI BAI: {LO}-{HI}", flush=True)

RAWALL = [r for r in _DS if LO <= r["task_id"] <= HI and len(r["test_list"]) >= 3]
def canon(r): return r["code"]

SOLVE  = ("Write the complete self-contained Python function. "
          "Return ONLY code inside a ```python block. No explanation.")
REVIEW = ("Review the code below against the task. If it is wrong or incomplete, fix it. "
          "Return ONLY the complete corrected code inside a ```python block.")
WTEST  = ("Write 4 Python assert statements that check the described function. "
          "Use the exact function name from the task. Return ONLY the assert lines inside a "
          "```python block, one per line, no function definition, no explanation.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def has_block(t):
    return bool(re.search(r"```(?:python)?\s*\n.*?```", t or "", re.S))
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
def official(rec, code):
    if not code or not compiles(code): return False
    out, _ = _run(code + "\n\n" + "\n".join(rec["test_list"][1:3]) + "\nprint('ALLOK')\n")
    return "ALLOK" in out
def own_tests(code, asserts):
    if not code or not compiles(code) or not asserts: return False
    out, _ = _run(code + "\n\n" + "\n".join(asserts) + "\nprint('ALLOK')\n")
    return "ALLOK" in out
def par(fn, args, w=8):
    with ThreadPoolExecutor(max_workers=w) as ex: return list(ex.map(lambda a: fn(*a), args))

def mcnemar(a, b):
    """McNemar CHINH XAC hai phia tren vector ket qua GHEP CAP. Tra (b01, b10, p)."""
    b01 = sum(1 for x, y in zip(a, b) if x and not y)
    b10 = sum(1 for x, y in zip(a, b) if y and not x)
    n = b01 + b10
    if n == 0: return b01, b10, 1.0
    k = min(b01, b10)
    p = min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k+1)) / (2.0 ** n))
    return b01, b10, round(p, 6)

BIG_CARD = (VRAM >= 40)
if not BIG_CARD:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
    from transformers import BitsAndBytesConfig
    _BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
print(f"CHE DO: {'card lon -> bf16' if BIG_CARD else 'card nho -> nf4 cho model dat'}", flush=True)

def ckpt_gb(p):
    """Kich thuoc checkpoint THAT (fp16) — doc tu index, KHONG dung GPU, mat vai mili giay."""
    idx = os.path.join(p, "model.safetensors.index.json")
    if os.path.exists(idx):
        t = json.load(open(idx)).get("metadata", {}).get("total_size", 0)
        if t: return t / 2**30
    tot = sum(os.path.getsize(f) for pat in ("*.safetensors", "*.bin")
              for f in glob.glob(os.path.join(p, pat)))
    return tot / 2**30

def plan_placement(p, tag):
    """#134-e: KHONG DAT CUOC VAO LUONG TU HOA.

    H84c xin nf4 cho Llama-3.1-8B va nhan ve fp16 (~15 GB) -> OOM sau 36 phut. Uoc tinh theo
    nf4 se bao 'vua 1 card' va van hong y het. Vi the tinh cho theo kich thuoc fp16 THAT:
    neu no khong vua mot card thi trai deu ngay, du ta co xin luong tu hoa hay khong.
    Gia phai tra neu luong tu hoa CO chay: dung nhieu card hon can. Chap nhan duoc.
    """
    fp16 = ckpt_gb(p)
    per = torch.cuda.get_device_properties(0).total_memory / 2**30
    n = torch.cuda.device_count()
    fits_one_fp16 = fp16 <= per * 0.90
    risky = not fits_one_fp16          # chi vua neu luong tu hoa THAT SU chay
    if risky and n == 1:
        print(f"  [preflight] CANH BAO {tag}: {fp16:.2f} GB fp16 tren 1 card {per:.2f} GB — "
              f"chi chay duoc neu luong tu hoa ap dung. Khong co card thu hai de lui ve.", flush=True)
    print(f"  [preflight] {tag}: checkpoint {fp16:.2f} GB fp16 | {n} card x {per:.2f} GB | "
          f"{'vua mot card ke ca fp16' if fits_one_fp16 else 'CAN luong tu hoa, neu truot thi TRAI DEU'}",
          flush=True)
    return risky

NGPU = torch.cuda.device_count()
print(f"SO GPU THAY DUOC = {NGPU} | tong VRAM = "
      f"{sum(torch.cuda.get_device_properties(d).total_memory for d in range(NGPU))/2**30:.1f} GB", flush=True)

def load(tag):
    p = M[tag]
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    # #134-e: LAC QUAN CO DUONG LUI. Thu mot card truoc (nhanh nhat: song song du lieu, va
    # Qwen-7B nf4 that su chi ton 5.2 GB nen ep trai deu la phi). Neu OOM -> giai phong sach
    # roi thu lai TRAI DEU. Ly do can duong lui: H84c XIN nf4 va NHAN fp16 (#134-d), nen khong
    # the biet truoc luong tu hoa co ap dung hay khong; chi co lan nap that moi tra loi duoc.
    risky = plan_placement(p, tag)
    def _build(dmap):
        if BIG_CARD:
            return AutoModelForCausalLM.from_pretrained(p, dtype=torch.bfloat16, device_map=dmap).eval()
        if tag == "cheap":
            return AutoModelForCausalLM.from_pretrained(p, torch_dtype=torch.float16, device_map=dmap).eval()
        return AutoModelForCausalLM.from_pretrained(p, quantization_config=_BNB, device_map=dmap).eval()
    dmap = {"": 0}
    try:
        mo = _build(dmap)
    except torch.OutOfMemoryError:
        if NGPU == 1: raise
        print(f"  [preflight] {tag} OOM tren MOT card (du bao rui ro={risky}) -> lui ve TRAI DEU", flush=True)
        mo = None; gc.collect()
        for _d in range(NGPU):
            with torch.cuda.device(_d): torch.cuda.empty_cache()
        dmap = "auto"
        mo = _build(dmap)
    print(f"  nap {tag} (device_map={dmap}): " + " | ".join(
        f"gpu{d} cap phat {torch.cuda.memory_allocated(d)/2**30:.2f} giu cho {torch.cuda.memory_reserved(d)/2**30:.2f}"
        for d in range(NGPU)), flush=True)
    if hasattr(mo, "hf_device_map"):
        print(f"    trai tren: {sorted(set(str(v) for v in mo.hf_device_map.values()))}", flush=True)
    return mo, tk
def free():
    """#132: 'del mo' TRONG ham chi xoa TEN CUC BO. Caller PHAI gan mo=None TRUOC khi goi.
    In ca memory_reserved — memory_allocated ve 0 ngay ca khi pool van bi chiem."""
    gc.collect()
    for d in range(torch.cuda.device_count()):
        with torch.cuda.device(d): torch.cuda.empty_cache()
    print("  sau giai phong: " + " | ".join(
        f"gpu{d} cap phat {torch.cuda.memory_allocated(d)/2**30:.2f} giu cho {torch.cuda.memory_reserved(d)/2**30:.2f}"
        for d in range(torch.cuda.device_count())), flush=True)

def _indev(mo):
    """Model trai tren nhieu card thi mo.device khong dang tin — dua dau vao ve card cua
    LOP NHUNG (embed), noi forward bat dau; accelerate lo phan chuyen tiep giua cac card."""
    dm = getattr(mo, "hf_device_map", None)
    if dm:
        for k in ("model.embed_tokens", "transformer.wte", ""):
            if k in dm: return dm[k]
        return sorted(dm.values(), key=str)[0]
    return mo.device

@torch.no_grad()
def gen(mo, tk, sysm, usrs, bs):
    outs, i = [], 0
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                  tokenize=False, add_generation_prompt=True) for u in ch]
            e = tk(ps, return_tensors="pt", padding=True).to(_indev(mo))
            # #101-d: dung ngay sau khi DONG block code. Ap DOI XUNG moi nhanh.
            # extract() chi lay block dau tien, nen phan bi cat la van xuoi THUA sau code.
            try:
                o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=False,
                                pad_token_id=tk.pad_token_id,
                                stop_strings=["```\n", "```"], tokenizer=tk)
            except TypeError:
                if not globals().get("_NOSTOP_WARNED"):
                    print("    [#101-d] transformers khong nhan stop_strings -> chi dung MAXNEW", flush=True)
                    globals()["_NOSTOP_WARNED"] = True
                o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=False, pad_token_id=tk.pad_token_id)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs//2); print(f"    OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs

t_f = time.time()
_ok = par(lambda r: official(r, canon(r)), [(r,) for r in RAWALL], 8)
ALL = [r for r, o in zip(RAWALL, _ok) if o]
N = len(ALL)
print(f"loc chuan: {N}/{len(RAWALL)} bai co loi giai chuan DAT test ({time.time()-t_f:.0f}s)", flush=True)

PR = [f"{r['text']}\n\nYour code must satisfy this test:\n{r['test_list'][0]}" for r in ALL]
t0 = time.time()
def save_partial(**kw):
    """#128: file phai CHAM DUOC neu kernel chet o dong ngay sau."""
    json.dump({"partial": True, "run": RUN, "n": N, **kw},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))

mo, tk = load("cheap")
S_raw = gen(mo, tk, SOLVE, PR, BSZ["cheap"])
print(f"S xong ({time.time()-t0:.0f}s)", flush=True)
T_raw = gen(mo, tk, WTEST, PR, BSZ["cheap"])
print(f"test tu sinh xong ({time.time()-t0:.0f}s)", flush=True)
mo = None; tk = None
free()
S = [extract(t) for t in S_raw]; TESTS = [clean_asserts(t) for t in T_raw]
save_partial(S=S, TESTS=TESTS, S_raw=S_raw, T_raw=T_raw)

mo, tk = load("dear")
I_raw = gen(mo, tk, SOLVE, PR, BSZ["dear"])
print(f"I xong ({time.time()-t0:.0f}s)", flush=True)
save_partial(S=S, TESTS=TESTS, S_raw=S_raw, T_raw=T_raw, I_raw=I_raw)
V_raw = gen(mo, tk, REVIEW,
            [f"{PR[i]}\n\nProposed code:\n```python\n{S[i]}\n```" for i in range(N)], BSZ["dear"])
print(f"V xong ({time.time()-t0:.0f}s)", flush=True)
mo = None; tk = None
free()
I = [extract(t) for t in I_raw]; V = [extract(t) for t in V_raw]
save_partial(S=S, TESTS=TESTS, S_raw=S_raw, T_raw=T_raw, I_raw=I_raw, V_raw=V_raw)

# ---- cham ----
PS = par(official, [(ALL[i], S[i]) for i in range(N)])
PI = par(official, [(ALL[i], I[i]) for i in range(N)])
PV = par(official, [(ALL[i], V[i]) for i in range(N)])
Z  = par(own_tests, [(S[i], TESTS[i]) for i in range(N)])          # cong doc lap
p_esc = round(1 - sum(Z)/N, 4)

# ---- ghep nhanh CO CONG (offline, cung artifact) ----
PG_V  = [PS[i] if Z[i]  else PV[i] for i in range(N)]
PG_I  = [PS[i] if Z[i]  else PI[i] for i in range(N)]
PGO_V = [PS[i] if PS[i] else PV[i] for i in range(N)]              # cong ORACLE = chan tren

A = lambda p: round(sum(p)/N, 4)
d_gate   = round(A(PG_V) - A(PV), 4)
d_honest = round(A(PG_V) - A(PI), 4)
d_cont   = round(A(PG_I) - A(PG_V), 4)
d_ceil   = round(A(PGO_V) - A(PI), 4)
d_VI     = round(A(PV) - A(PI), 4)      # #98: dau doc, so voi -.0740 cua cap NOI HO Qwen
d_IS     = round(A(PI) - A(PS), 4)      # cong nang luc
mc = {"gate": mcnemar(PV, PG_V), "honest": mcnemar(PI, PG_V),
      "cont": mcnemar(PG_V, PG_I), "ceil": mcnemar(PI, PGO_V),
      "VI": mcnemar(PI, PV), "IS": mcnemar(PS, PI)}

# ---- CONG CHAT LUONG (#97) ----
# #97-c: cong PHAI la "trich duoc code CHAY", khong phai "co hang rao markdown".
# H88/H88b VOID vi cai nham: S co has_block .1383 nhung compiles(extract) .9980 —
# model yeu khong rao code, the thoi. `has_block` van duoc BAO CAO nhung khong con la cong.
ext = {k: round(sum(compiles(extract(t)) for t in v)/N, 4) for k, v in
       (("S", S_raw), ("I", I_raw), ("V", V_raw))}
fenced = {k: round(sum(has_block(t) for t in v)/N, 4) for k, v in
          (("S", S_raw), ("I", I_raw), ("V", V_raw))}
ext_min, ext_spread = min(ext.values()), round(max(ext.values())-min(ext.values()), 4)
runnable = round(sum(1 for t in TESTS if t)/N, 4)
# #101-b: cong CAT CUT tuong minh — bat NGUYEN NHAN, som hon cong extract_spread (bat hau qua)
def _unclosed(t):
    """#154: CAT CUT = mo rao ma khong dong (so rao LE). KHONG dem "khong co rao nao"
    la cat cut — do la lua chon DINH DANG (bai hoc #138: model yeu khong rao code,
    nhung code van bien dich .998). Ve `count < 2` cu gan nhan sai cho ca mot nhanh."""
    return (t or "").count("```") % 2 != 0
trunc = {k: round(sum(_unclosed(t) for t in v)/N, 4) for k, v in
         (("S", S_raw), ("I", I_raw), ("V", V_raw))}
trunc_max = max(trunc.values())
gates = {"extract_min>=.80": ext_min >= .80, "extract_spread<.05": ext_spread < .05,
         "truncation<.05 moi nhanh": trunc_max < .05,
         "n>=480": N >= 480, ".15<=p_esc<=.90": .15 <= p_esc <= .90, "test_runnable>=.60": runnable >= .60,
         "I-S>=.05 (cong nang luc #98)": d_IS >= .05}
VOID = [k for k, v in gates.items() if not v]

res = {"tag": RUN, "range": [LO, HI], "n": N,
       "dear_model": M["dear"], "dear_needles": DEAR_NEEDLES, "same_family": SAME_FAMILY,
       "acc": {"S": A(PS), "I": A(PI), "V": A(PV), "G_V": A(PG_V), "G_I": A(PG_I), "Go_V": A(PGO_V)},
       "delta": {"gate": d_gate, "honest": d_honest, "cont": d_cont, "ceil": d_ceil,
                 "V_minus_I": d_VI, "I_minus_S": d_IS},
       "mcnemar": {k: {"b01": v[0], "b10": v[1], "p": v[2]} for k, v in mc.items()},
       "p_esc": p_esc, "extract_rate": ext, "extract_min": ext_min, "extract_spread": ext_spread,
       "test_runnable": runnable, "fenced_rate": fenced, "truncation_rate": trunc, "gates": gates, "VOID": VOID,
       "gate_accept_but_wrong": sum(1 for i in range(N) if Z[i] and not PS[i]),
       "gate_reject_but_right": sum(1 for i in range(N) if not Z[i] and PS[i]),
       "V_destroys": sum(1 for i in range(N) if PS[i] and not PV[i]),
       "V_destroys_inside_gate": sum(1 for i in range(N) if PS[i] and not PV[i] and Z[i])}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "z": Z[i], "tests": TESTS[i],
            "S": S[i][:1200], "I": I[i][:1200], "V": V[i][:1200],
            "pS": PS[i], "pI": PI[i], "pV": PV[i]} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print(f"\n==== H88 {RUN} ({LO}-{HI}) ====")
print(f"  n={N} | p_esc={p_esc} | trich duoc {ext} (min {ext_min}, chenh {ext_spread}) | test chay duoc {runnable}")
for k in ["S", "I", "V", "G_V", "G_I", "Go_V"]:
    print(f"  {k:6s} {res['acc'][k]:.4f}")
print(f"\n  d_gate   = {d_gate:+.4f}  (G_V vs V)   p={mc['gate'][2]}")
print(f"  d_honest = {d_honest:+.4f}  (G_V vs I)   p={mc['honest'][2]}")
print(f"  d_cont   = {d_cont:+.4f}  (G_I vs G_V) p={mc['cont'][2]}")
print(f"  d_ceil   = {d_ceil:+.4f}  (G*_V vs I)  p={mc['ceil'][2]}")
print(f"  V pha {res['V_destroys']} bai S lam dung, trong do {res['V_destroys_inside_gate']} nam TRONG tap cong-dat")
print(f"  cong nhan nham {res['gate_accept_but_wrong']} | tu choi oan {res['gate_reject_but_right']}")

print("\n-- BANG KHOA #97 --")
if VOID:
    print(f"  -> HANG 0: VOID, cong chat luong truot: {VOID}. KHONG doc so nao.")
elif d_ceil <= 0 or (mc["ceil"][2] >= .05 and abs(d_ceil) < .02):
    print("  -> HANG 1: GIET CA DONG SUA. Cong ORACLE cung khong vuot I => khong co gi de khai thac.")
elif d_gate >= .04 and mc["gate"][2] < .05 and d_honest >= .02 and mc["honest"][2] < .05:
    print("  -> HANG 2: M1 CHO DON THUOC DUNG DUOC. Sua an toan khi co cong doc lap.")
elif d_gate >= .04 and mc["gate"][2] < .05:
    print("  -> HANG 3: cong KHU duoc D nhung kappa=0 — van khong bang chi goi M mot luot.")
else:
    print("  -> HANG 4: M1 SAI NHU DANG PHAT BIEU. Co cho khai thac nhung chan ghi de KHONG cuu duoc.")
if d_cont < -.02 and mc["cont"][2] < .05:
    print("  -> HANG 5 (cong them): duoi cong, cho thay artifact VAN nhiem doc — cung co #119.")

# ---- BANG KHOA #98: dau doc co PHU THUOC HO cua model DAT khong? ----
QWEN_MBPP_VI = -.0740   # moc NOI HO da khoa (1.5B->7B Qwen, MBPP), TONG_HOP muc 1
print(f"\n-- BANG KHOA #98 (model dat = {M['dear'].split('/')[-1]}, cung ho = {SAME_FAMILY}) --")
print(f"  V - I = {d_VI:+.4f} (p={mc['VI'][2]})  |  moc noi ho Qwen tren MBPP = {QWEN_MBPP_VI:+.4f}")
print(f"  I - S = {d_IS:+.4f} (p={mc['IS'][2]})  cong nang luc {'DAT' if d_IS>=.05 else 'TRUOT'}")
if VOID:
    print(f"  -> HANG 0: VOID ({VOID}). Khong doc.")
elif d_VI <= QWEN_MBPP_VI - .03 and mc["VI"][2] < .05:
    print("  -> HANG A: nguon NGOAI HO PHA MANH HON nguon noi ho => co che 'nguon la' duoc cung co.")
elif abs(d_VI - QWEN_MBPP_VI) < .03 and d_VI < -.02:
    print("  -> HANG B: pha hoai KHONG phu thuoc ho => 'nguon la' khong phai ve HO MODEL, "
          "ma ve viec artifact la CUA NGUOI KHAC. Phat bieu lai co che.")
elif d_VI >= -.02:
    print("  -> HANG C: dau doc BIEN MAT khi doi ho => ket qua trung tam CHI DUNG TRONG HO Qwen. "
          "Gioi han pham vi cua ca du an.")
else:
    print(f"  -> HANG D: pha hoai YEU HON ro ret ({d_VI:+.4f} vs {QWEN_MBPP_VI:+.4f}) nhung van am.")
print("XONG", flush=True)
