# H92 (dang ky truoc #102) — LIEU-DAP UNG cua viec NHIN THAY.
# #142 phat bieu lai M1: hai den tu viec M NHIN THAY artifact, khong phai tu viec M duoc phep GHI DE.
# Kiem bang cach cho M xem NGAY CANG NHIEU, va BO HAN lenh "review" o moi nhanh:
#   E0 = I     : khong cho xem gi                    <- moc that
#   E1         : chi noi "co model nho hon da thu"   (KHONG noi dung)
#   E2         : chi chu ky ham + so dong cua S      (cau truc, khong logic)
#   E3 = V     : toan bo code cua S                  (phoi nhiem toi da)
# Moi nhanh dung CUNG mot lenh SOLVE. Khac biet duy nhat: phan ngu canh them vao.
import os
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
import re, json, glob, time, gc, math, tempfile, subprocess, sys, torch
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN, LO, HI = "@@RUN@@", int("@@LO@@"), int("@@HI@@")

def _unclosed(t):
    """#154: CAT CUT = mo rao ``` ma khong dong (so rao LE).
    KHONG dem "khong co rao nao" la cat cut — do la lua chon dinh dang (#138)."""
    return (t or "").count("```") % 2 != 0

def trunc_report(named):
    """named = {ten_nhanh: list[str]}. In ti le cat cut moi nhanh + chenh lech.
    Cong bat NGUYEN NHAN: cong extract_spread chi bat HAU QUA va da de lot H91c (#153)."""
    r = {k: round(sum(_unclosed(t) for t in v)/max(len(v),1), 4) for k, v in named.items()}
    sp = round(max(r.values()) - min(r.values()), 4) if r else 0.0
    print(f"  [cat cut] {r} | chenh={sp} | {'DAT' if max(r.values(), default=0) < .05 else 'TRUOT (<.05)'}", flush=True)
    return r, sp

MAXNEW, TIMEOUT = 768, 60
BSZ = {"cheap": 24, "dear": 16}

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")
M = {"cheap": find_model("1-5b", "1_5b", "1.5b"), "dear": find_model("2-5-7b", "qwen2-5-7b")}
# #143: uu tien dataset da stage; chi goi HF khi that su co mang
_hits = sorted(glob.glob("/kaggle/input/**/mbpp_full.json", recursive=True), key=len)
if _hits:
    print(f"MBPP nap tu dataset da stage: {_hits[0]}", flush=True)
    _DS = json.load(open(_hits[0]))
else:
    print("khong mount duoc mbpp_full.json -> thu HuggingFace (can internet)", flush=True)
    from datasets import load_dataset
    _D = load_dataset("mbpp", "full", split="test+train+validation")
    _DS = [{k: r[k] for k in ["task_id", "text", "code", "test_list"]} for r in _D]

NGPU = torch.cuda.device_count()
print(f"SO GPU = {NGPU} | tong VRAM = "
      f"{sum(torch.cuda.get_device_properties(d).total_memory for d in range(NGPU))/2**30:.1f} GB\n"
      f"DAI BAI: {LO}-{HI}", flush=True)
VRAM = torch.cuda.get_device_properties(0).total_memory/2**30
BIG_CARD = VRAM >= 40
if not BIG_CARD:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
    from transformers import BitsAndBytesConfig
    _BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)

RAWALL = [r for r in _DS if LO <= r["task_id"] <= HI and len(r["test_list"]) >= 3]

SOLVE = ("Write the complete self-contained Python function. "
         "Return ONLY code inside a ```python block. No explanation.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def compiles(c):
    try: compile(c, "<s>", "exec"); return True
    except Exception: return False
def signature_only(code):
    """E2: chi giu dong `def ...` (chu ky) + so dong than ham. KHONG lo logic nao."""
    lines = [l for l in (code or "").splitlines() if l.strip()]
    defs = [l.strip() for l in lines if l.strip().startswith("def ")]
    if not defs: return None
    return f"{defs[0]}\n    # ... {max(0, len(lines)-len(defs))} dong than ham (khong hien)"

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

def load(tag):
    p = M[tag]
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    def _build(dmap):
        if BIG_CARD:
            return AutoModelForCausalLM.from_pretrained(p, dtype=torch.bfloat16, device_map=dmap).eval()
        if tag == "cheap":
            return AutoModelForCausalLM.from_pretrained(p, torch_dtype=torch.float16, device_map=dmap).eval()
        return AutoModelForCausalLM.from_pretrained(p, quantization_config=_BNB, device_map=dmap).eval()
    dmap = {"": 0}
    try:
        mo = _build(dmap)
    except torch.OutOfMemoryError:                       # #134-e: lac quan co duong lui
        if NGPU == 1: raise
        print(f"  {tag}: OOM mot card -> lui ve TRAI DEU", flush=True)
        mo = None; gc.collect()
        for d in range(NGPU):
            with torch.cuda.device(d): torch.cuda.empty_cache()
        dmap = "auto"; mo = _build(dmap)
    print(f"  nap {tag} (device_map={dmap}): " + " | ".join(
        f"gpu{d} cap phat {torch.cuda.memory_allocated(d)/2**30:.2f} giu cho {torch.cuda.memory_reserved(d)/2**30:.2f}"
        for d in range(NGPU)), flush=True)
    return mo, tk
def free():
    gc.collect()
    for d in range(NGPU):
        with torch.cuda.device(d): torch.cuda.empty_cache()
def _indev(mo):
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
_ok = par(lambda r: official(r, r["code"]), [(r,) for r in RAWALL], 8)
ALL = [r for r, o in zip(RAWALL, _ok) if o]
N = len(ALL)
print(f"loc chuan: {N}/{len(RAWALL)} bai ({time.time()-t_f:.0f}s)", flush=True)
PR = [f"{r['text']}\n\nYour code must satisfy this test:\n{r['test_list'][0]}" for r in ALL]
t0 = time.time()
def save_partial(**kw):
    json.dump({"partial": True, "run": RUN, "n": N, **kw},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))

mo, tk = load("cheap")
S_raw = gen(mo, tk, SOLVE, PR, BSZ["cheap"])
mo = None; tk = None; free()
S = [extract(t) for t in S_raw]
print(f"S xong ({time.time()-t0:.0f}s)", flush=True)
save_partial(S_raw=S_raw)

# --- bon muc phoi nhiem, CUNG lenh SOLVE, chi khac phan ngu canh them vao ---
SIG = [signature_only(S[i]) for i in range(N)]
E_PROMPT = {
    "E0": [PR[i] for i in range(N)],
    "E1": [f"{PR[i]}\n\nNote: a smaller model has already attempted this task." for i in range(N)],
    "E2": [f"{PR[i]}\n\nA smaller model's attempt had this structure:\n```python\n{SIG[i]}\n```"
           if SIG[i] else PR[i] for i in range(N)],
    "E3": [f"{PR[i]}\n\nA smaller model's attempt:\n```python\n{S[i]}\n```" for i in range(N)],
}
n_nosig = sum(1 for x in SIG if x is None)

mo, tk = load("dear")
OUT = {}
for k in ("E0", "E1", "E2", "E3"):
    OUT[k] = gen(mo, tk, SOLVE, E_PROMPT[k], BSZ["dear"])
    print(f"{k} xong ({time.time()-t0:.0f}s)", flush=True)
    save_partial(S_raw=S_raw, **{f"{kk}_raw": v for kk, v in OUT.items()})
mo = None; tk = None; free()

P = {k: par(official, [(ALL[i], extract(v[i])) for i in range(N)]) for k, v in OUT.items()}
PS = par(official, [(ALL[i], S[i]) for i in range(N)])
A = lambda p: round(sum(p)/N, 4)
ext = {k: round(sum(compiles(extract(t)) for t in v)/N, 4) for k, v in OUT.items()}
ext["S"] = round(sum(compiles(c) for c in S)/N, 4)
emin, espread = min(ext.values()), round(max(ext.values())-min(ext.values()), 4)
d_IS = round(A(P["E0"]) - A(PS), 4)
mc_IS = mcnemar(PS, P["E0"])
gates = {"extract_min>=.80": emin >= .80, "extract_spread<.05": espread < .05,
         "n>=480": N >= 480, "I-S>=.05 va p<.05": d_IS >= .05 and mc_IS[2] < .05}
VOID = [k for k, v in gates.items() if not v]

res = {"tag": RUN, "range": [LO, HI], "n": N, "acc_S": A(PS),
       "acc": {k: A(v) for k, v in P.items()},
       "vs_E0": {k: round(A(P[k]) - A(P["E0"]), 4) for k in ("E1", "E2", "E3")},
       "mcnemar_vs_E0": {k: dict(zip(("b01", "b10", "p"), mcnemar(P["E0"], P[k]))) for k in ("E1", "E2", "E3")},
       "I_minus_S": d_IS, "mcnemar_IS": dict(zip(("b01", "b10", "p"), mc_IS)),
       "extract_rate": ext, "no_signature": n_nosig, "gates": gates, "VOID": VOID}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "S": S[i][:800], "sig": SIG[i],
            **{f"p{k}": P[k][i] for k in P}, "pS": PS[i]} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print(f"\n==== H92 {RUN} ({LO}-{HI}) ====")
print(f"  n={N} | trich {ext} (min {emin}, chenh {espread}) | khong lay duoc chu ky: {n_nosig}")
print(f"  acc(S) = {A(PS):.4f} | I - S = {d_IS:+.4f} (p={mc_IS[2]})")
for k in ("E0", "E1", "E2", "E3"):
    d = res["vs_E0"].get(k); p = res["mcnemar_vs_E0"].get(k, {}).get("p")
    print(f"  {k}: acc={A(P[k]):.4f}" + (f"   vs E0 = {d:+.4f} (p={p})" if k != "E0" else "   <- moc"))
print("\n-- BANG KHOA #102 --")
a = {k: A(P[k]) for k in P}
p_ = {k: res["mcnemar_vs_E0"][k]["p"] for k in ("E1", "E2", "E3")}
mono = a["E0"] > a["E1"] > a["E2"] > a["E3"]
if VOID:
    print(f"  -> HANG 0: VOID {VOID}")
elif mono and (a["E0"]-a["E3"]) >= .05 and p_["E3"] < .05 and (a["E0"]-a["E2"]) >= .02 and p_["E2"] < .05:
    print("  -> HANG 1: LIEU-DAP UNG CO THAT. Cang nhin nhieu cang hai. M1 (#142) dung vung.")
elif (a["E0"]-a["E3"]) >= .02 and p_["E3"] < .05 and all(abs(a["E0"]-a[k]) < .02 for k in ("E1","E2")):
    print("  -> HANG 2: NGUONG, khong phai lieu. Chi LOGIC DAY DU moi hai; ton tai/cau truc vo hai.")
elif (a["E0"]-a["E1"]) >= .02 and p_["E1"] < .05:
    print("  -> HANG 3: KINH NGAC — chi BIET co nguoi thu da hai. Hieu ung KHUNG, khong phai nhiem noi dung.")
else:
    print("  -> HANG 4: GIET phat bieu lai cua #142. Bo lenh 'review' thi thiet hai KHONG tai lap")
    print("     => thu pham la LENH GHI DE, khong phai viec NHIN THAY. M1 quay ve ban goc.")
print("XONG", flush=True)
