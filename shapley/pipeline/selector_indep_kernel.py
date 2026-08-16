# H81 (dang ky truoc #90) — BO CHON co can DOC LAP VE HO khong? — DA DANG HO MODEL vs DA DANG LAY MAU, cung chi phi.
# Pool A: Q1(greedy) + Q2(T=.8) + Q3(T=.8)      <- da dang LAY MAU (mot ho)
# Pool B: Q1(greedy) + L(greedy) + D(greedy)    <- da dang HO (ba ho)
# Bo chon GIU NGUYEN cho ca hai (test tu sinh do Q viet, mot lan) => khac biet duy nhat la POOL.
import os, re, ast, json, glob, time, gc, tempfile, subprocess, sys, torch
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = "@@RUN@@"
TIDLO, TIDHI = int("@@LO@@"), int("@@HI@@")
MAXNEW, TIMEOUT = 512, 20
BS = 24

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")
M = {"Q": find_model("2-5-7b", "qwen2-5-7b"),
     "D": find_model("deepseek-coder-6-7b", "deepseek-coder-6.7b")}
CC = torch.cuda.get_device_capability(0); VRAM = torch.cuda.get_device_properties(0).total_memory/2**30
print(f"MODELS={json.dumps(M,indent=1)}\nGPU={torch.cuda.get_device_name(0)} | {VRAM:.1f} GB | sm_{CC[0]}{CC[1]}", flush=True)

# khong internet tren RTX 6000 -> MBPP nap tu dataset JSON da stage
# dataset private KHONG mount duoc sang tai khoan khac (push van thanh cong) -> fallback HF.
_hits = sorted(glob.glob("/kaggle/input/**/mbpp_full.json", recursive=True), key=len)
if _hits:
    DS = json.load(open(_hits[0]))
else:
    print("khong mount duoc mbpp_full.json -> nap tu HuggingFace", flush=True)
    from datasets import load_dataset
    _D = load_dataset("mbpp", "full", split="test+train+validation")
    DS = [{k: r[k] for k in ["task_id","text","code","test_list"]} for r in _D]
ALL = sorted([r for r in DS if TIDLO <= r["task_id"] <= TIDHI and len(r["test_list"]) >= 3],
             key=lambda r: r["task_id"])
N = len(ALL)
print(f"MBPP {TIDLO}-{TIDHI}: {N} bai", flush=True)
assert N >= 400

SOLVE = "Write the Python function. Return ONLY code inside a ```python block. No explanation."
WTEST = ("Write 5 Python assert statements that check the described function. "
         "Use EXACTLY the function name given. Return ONLY the assert lines inside a "
         "```python block, one per line, no function definition, no explanation.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def compiles(c):
    try: compile(c, "<s>", "exec"); return True
    except Exception: return False
def clean_asserts(t):
    """#90-b: quet TOAN VAN, khong chi trong block markdown. H81d cho thay bo loc cu ep ca hai
    model ve ~1/5 assert, va DeepSeek trot nhieu hon -> do phu 41% vs 99.6%, lam hong phep so.
    Ap DOI XUNG cho ca hai nhanh."""
    out, seen = [], set()
    for src in (extract(t), t or ""):
        for ln in src.splitlines():
            ln = ln.strip()
            if ln.startswith("assert") and compiles(ln) and ln not in seen:
                seen.add(ln); out.append(ln)
    return out[:5]
def _run(code, checks, mode):
    if not code or not compiles(code): return False if mode == "all" else 0
    if not checks: return False if mode == "all" else 0
    if mode == "all":
        prog = code + "\n\n" + "\n".join(checks) + "\nprint('ALLOK')\n"
    else:
        prog = code + "\n\n_n=0\n" + "".join(
            f"try:\n    {c}\n    _n+=1\nexcept Exception:\n    pass\n" for c in checks) + "print('CNT',_n)\n"
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        o = r.stdout or ""
        if mode == "all": return "ALLOK" in o
        m = re.search(r"CNT (\d+)", o)
        return int(m.group(1)) if m else 0
    except Exception: return False if mode == "all" else 0
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
def par(fn, args, w=8):
    with ThreadPoolExecutor(max_workers=w) as ex: return list(ex.map(lambda a: fn(*a), args))
def grade(codes): return par(_run, [(codes[i], ALL[i]["test_list"][1:3], "all") for i in range(N)])

BIG_CARD = (torch.cuda.get_device_properties(0).total_memory/2**30 >= 40)
if not BIG_CARD:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "bitsandbytes>=0.46.1"], check=False)
    from transformers import BitsAndBytesConfig
    _BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                              bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
print(f"CHE DO: {'card lon -> bf16' if BIG_CARD else 'card nho -> nf4 (7-8B bf16 = 15+ GB > 14.56 GB cua T4)'}", flush=True)

def load(tag):
    p = M[tag]
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    # #134-h: tren ban transformers nay, model NGOAI HO QWEN khong duoc luong tu hoa —
    # quan sat doc lap: Llama-3.1-8B (H84c/H89/H86b) va DeepSeek-Coder-6.7B (H81c, 13.85 GB
    # = dung bang fp16 cua no). Thu MOT card truoc, OOM thi lui ve TRAI DEU hai card.
    NG = torch.cuda.device_count()
    def _build(dmap):
        if BIG_CARD:
            return AutoModelForCausalLM.from_pretrained(p, dtype=torch.bfloat16, device_map=dmap).eval()
        return AutoModelForCausalLM.from_pretrained(p, quantization_config=_BNB, device_map=dmap).eval()
    dmap = {"": 0}
    try:
        mo = _build(dmap)
    except torch.OutOfMemoryError:
        if NG == 1: raise
        print(f"  {tag}: OOM tren MOT card -> giai phong -> lui ve TRAI DEU", flush=True)
        mo = None; gc.collect()
        for _d in range(NG):
            with torch.cuda.device(_d): torch.cuda.empty_cache()
        dmap = "auto"
        mo = _build(dmap)
    print(f"  nap {tag} (device_map={dmap}): " + " | ".join(
        f"gpu{d} cap phat {torch.cuda.memory_allocated(d)/2**30:.2f} giu cho {torch.cuda.memory_reserved(d)/2**30:.2f}"
        for d in range(NG)), flush=True)
    return mo, tk

def _indev(mo):
    dm = getattr(mo, "hf_device_map", None)
    if dm:
        for k in ("model.embed_tokens", "transformer.wte", ""):
            if k in dm: return dm[k]
        return sorted(dm.values(), key=str)[0]
    return mo.device
def free(mo=None):
    """LUU Y: 'del mo' TRONG ham chi xoa TEN CUC BO — model van song o bien cua caller.
    Vi the caller PHAI gan mo=None TRUOC khi goi. Ham nay chi lam gc + empty_cache."""
    gc.collect()
    for d in range(torch.cuda.device_count()):
        with torch.cuda.device(d): torch.cuda.empty_cache()

@torch.no_grad()
def gen(mo, tk, sysm, usrs, bs, temp=0.0):
    outs, i = [], 0
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                  tokenize=False, add_generation_prompt=True) for u in ch]
            e = tk(ps, return_tensors="pt", padding=True).to(_indev(mo))
            o = mo.generate(**e, max_new_tokens=MAXNEW, do_sample=(temp > 0),
                            temperature=max(temp, 1e-5), top_p=0.95, pad_token_id=tk.pad_token_id)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs//2); print(f"    OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs

PR = [f"{r['text']}\n\nYour code must satisfy this test:\n{r['test_list'][0]}" for r in ALL]
t0 = time.time()
CODE, RAW = {}, {}

mo, tk = load("Q")
CODE["Q1"] = [extract(t) for t in gen(mo, tk, SOLVE, PR, BS)]
CODE["Q2"] = [extract(t) for t in gen(mo, tk, SOLVE, PR, BS, temp=0.8)]
T_self_raw = gen(mo, tk, WTEST, PR, BS)                              # test do CHINH Qwen viet
T_self = [clean_asserts(t) for t in T_self_raw]
mo = None; tk = tk   # thao tham chieu cua CALLER truoc khi gc
free()
print(f"Q xong ({time.time()-t0:.0f}s)", flush=True)
json.dump({"partial": True, "raw": CODE, "T_self": T_self, "T_self_raw": T_self_raw},
          open(f"/kaggle/working/partial_{RUN}.json", "w"))

mo, tk = load("D")
T_other_raw = gen(mo, tk, WTEST, PR, BS)                             # test do HO KHAC viet
T_other = [clean_asserts(t) for t in T_other_raw]
mo = None; tk = tk   # thao tham chieu cua CALLER truoc khi gc
free()
print(f"T_other (DeepSeek) xong ({time.time()-t0:.0f}s)", flush=True)
json.dump({"partial": True, "raw": CODE, "T_self": T_self, "T_self_raw": T_self_raw,
           "T_other": T_other, "T_other_raw": T_other_raw},
          open(f"/kaggle/working/partial_{RUN}.json", "w"))

PASS = {k: grade(v) for k, v in CODE.items()}
POOL = ["Q1", "Q2"]
A = lambda p: round(sum(p)/N, 4)

def run_sel(TESTS, lab):
    CNT = {k: par(_run, [(CODE[k][i], TESTS[i], "cnt") for i in range(N)]) for k in POOL}
    sel = []
    for i in range(N):
        sc = [CNT[k][i] for k in POOL] if TESTS[i] else [0]*len(POOL)
        sel.append(PASS[POOL[sc.index(max(sc))]][i])
    def nrm(x): return " ".join(x.split())
    off = [set(nrm(x) for x in ALL[i]["test_list"][1:3]) for i in range(N)]
    ng = sum(len(t) for t in TESTS)
    cr = round(sum(1 for i in range(N) for a in TESTS[i] if nrm(a) in off[i])/max(ng,1), 4)
    sd = par(_run, [(ALL[i]["code"], TESTS[i], "all") for i in range(N)])
    snd = round(sum(1 for i in range(N) if TESTS[i] and sd[i])/max(sum(1 for t in TESTS if t),1), 4)
    base = A(PASS["Q1"])
    union = sum(1 for i in range(N) if any(PASS[k][i] for k in POOL))/N
    cov = round(sum(1 for t in TESTS if t)/N, 4)
    return {"lab": lab, "SEL": round(sum(sel)/N, 4), "_SEL_raw": sum(sel)/N, "SEL_minus_base": round(sum(sel)/N-base, 4),
            "soundness": snd, "copy_rate": cr, "n_tests": ng, "coverage": cov, "sel_vec": sel,
            "H": round(union, 4), "kappa": round((sum(sel)/N-base)/(union-base)*100, 1) if union > base else None}

RS, RO = run_sel(T_self, "T_self(Qwen)"), run_sel(T_other, "T_other(DeepSeek)")
comp = round(sum(compiles(c) for v in CODE.values() for c in v)/(len(CODE)*N), 4)
# #90-b: cong DO PHU — phep so vo nghia neu mot tin hieu im lang o nhieu bai
BOTH = [i for i in range(N) if T_self[i] and T_other[i]]
sel_i = {"T_self": RS.pop("sel_vec"), "T_other": RO.pop("sel_vec")}
inter = {k: round(sum(sel_i[k][i] for i in BOTH)/max(len(BOTH),1), 4) for k in sel_i}
gates = {"coverage>=.90 ca hai": min(RS["coverage"], RO["coverage"]) >= .90,
         "chenh do phu <.10": abs(RS["coverage"] - RO["coverage"]) < .10,
         "soundness>=.50 ca hai": min(RS["soundness"], RO["soundness"]) >= .50,
         "copy_rate<=.20": max(RS["copy_rate"], RO["copy_rate"]) <= .20}
VOID = [k for k, v in gates.items() if not v]
res = {"tag": RUN, "n": N, "acc_each": {k: A(PASS[k]) for k in CODE}, "base": A(PASS["Q1"]),
       "T_self": RS, "T_other": RO, "compile_rate": comp,
       "diff": round(RO["_SEL_raw"] - RS["_SEL_raw"], 4),
       "n_giao": len(BOTH), "SEL_tren_tap_giao": inter,
       "diff_tap_giao": round(inter["T_other"] - inter["T_self"], 4),
       "gates": gates, "VOID": VOID}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "T_self": T_self[i], "T_other": T_other[i],
            **{k: CODE[k][i][:800] for k in CODE}, **{"p_"+k: PASS[k][i] for k in PASS}} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H81 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} | acc: {res['acc_each']}")
for r in (RS, RO):
    print(f"  {r['lab']:20s} SEL={r['SEL']:.4f} (+{r['SEL_minus_base']:.4f})  kappa={r['kappa']}%  "
          f"soundness={r['soundness']:.4f}  copy={r['copy_rate']:.4f}  n_test={r['n_tests']}")
d = res["diff"]
print(f"\n  SEL(T_other) - SEL(T_self) = {d:+.4f}   <-- DAI LUONG CHINH (#90)")
print("\n-- bang khoa #90 --")
print(f"  do phu: T_self={RS['coverage']} T_other={RO['coverage']} | n_giao={len(BOTH)}"
      f" | SEL tren tap giao: {inter} (chenh {res['diff_tap_giao']:+.4f})")
if VOID: print(f"  -> HANG 0: VOID {VOID}")
elif RO["soundness"] < .50: print("  -> HUY nhanh T_other: soundness < .50")
elif RS["soundness"] < .50 or max(RS["copy_rate"], RO["copy_rate"]) > .20: print("  -> HUY: cong truot")
elif d >= .02: print("  -> HANG 1: M2 XAC NHAN o phia BO CHON. Tin hieu phai doc lap ve HO.")
elif abs(d) < .02: print("  -> HANG 2: doc lap ve ho KHONG cai thien kappa. Thu hep M2 ve pool.")
else: print("  -> HANG 3: test cua ho khac TE HON -> kappa phu thuoc KHOP PHONG CACH, nguoc M2.")
print("XONG", flush=True)
