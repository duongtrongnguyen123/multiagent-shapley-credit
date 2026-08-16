# H87 (dang ky truoc #96) — model YEU-KHAC-HO ben canh model MANH (32B) — DA DANG HO MODEL vs DA DANG LAY MAU, cung chi phi.
# Pool A: Q1(greedy) + Q2(T=.8) + Q3(T=.8)      <- da dang LAY MAU (mot ho)
# Pool B: Q1(greedy) + L(greedy) + D(greedy)    <- da dang HO (ba ho)
# Bo chon GIU NGUYEN cho ca hai (test tu sinh do Q viet, mot lan) => khac biet duy nhat la POOL.
import os
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")  # TRUOC import torch
import re, ast, json, glob, time, gc, tempfile, subprocess, sys, torch
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer

RUN = "@@RUN@@"
TIDLO, TIDHI = int("@@LO@@"), int("@@HI@@")
MAXNEW, TIMEOUT = 512, 20
BS = 8   # 32B bf16 tren card 95 GB

def find_model(*needles):
    for p in glob.glob("/kaggle/input/*/**/", recursive=True):
        if any(n in p.lower() for n in needles) and os.path.exists(os.path.join(p, "config.json")):
            return p.rstrip("/")
    raise RuntimeError(f"khong thay {needles}: co {sorted(os.listdir('/kaggle/input'))}")
M = {"Q": find_model("32b"),   # "Q" = model MANH (32B)
     "L": find_model("llama-3-1-8b", "llama-3.1-8b", "llama3-1-8b"),
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
    out = []
    for ln in extract(t).splitlines():
        ln = ln.strip()
        if ln.startswith("assert") and compiles(ln): out.append(ln)
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
    # #134-e: LAC QUAN CO DUONG LUI. Llama-3.1-8B KHONG luong tu hoa tren ban transformers nay —
    # quan sat DOC LAP 3 lan (H84c, H89, H86b): deu roi ve fp16 ~14 GB roi OOM tren mot card T4.
    # Khong the biet truoc; chi lan nap THAT moi tra loi. Thu MOT card (nhanh nhat), OOM thi
    # giai phong SACH roi lui ve TRAI DEU hai card (31.2 GB tong -> fp16 15 GB vua thoai mai).
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
    if hasattr(mo, "hf_device_map"):
        print(f"    trai tren: {sorted(set(str(v) for v in mo.hf_device_map.values()))}", flush=True)
    return mo, tk

def _indev(mo):
    """Model trai nhieu card thi mo.device khong dang tin — dua dau vao ve card cua lop nhung."""
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
def canary():
    """#134-g: nap THU tung model roi giai phong NGAY, TRUOC khi sinh bat cu gi.

    H86b tieu 54 phut sinh voi model 1 roi moi chet luc nap model 2. Canary tra loi cau hoi
    "ke hoach nay co chay duoc tren phan cung nay khong" trong ~5 phut thay vi ~2 gio.
    No cung IN ra footprint that cua tung model, nen phat hien duoc truong hop
    "xin nf4 nhung nhan fp16" ngay lap tuc thay vi suy dien tu mot dong OOM."""
    print("=== CANARY: thu nap tung model truoc khi sinh ===", flush=True)
    for _tag in list(M):
        _mo, _tk = load(_tag)
        _mo = None; _tk = None
        free()
    print("=== CANARY xong: MOI model deu nap duoc ===", flush=True)

canary()
t0 = time.time()
CODE, RAW = {}, {}

mo, tk = load("Q")
CODE["Q1"] = [extract(t) for t in gen(mo, tk, SOLVE, PR, BS)]
CODE["Q2"] = [extract(t) for t in gen(mo, tk, SOLVE, PR, BS, temp=0.8)]
TESTS = [clean_asserts(t) for t in gen(mo, tk, WTEST, PR, BS)]   # bo chon: CHI do Q viet
mo = None; tk = tk   # thao tham chieu cua CALLER truoc khi gc
free()
print(f"Q xong ({time.time()-t0:.0f}s)", flush=True)
json.dump({"partial": True, "raw": {k: v for k, v in CODE.items()}, "TESTS": TESTS},
          open(f"/kaggle/working/partial_{RUN}.json", "w"))

for tag in ["L", "D"]:
    mo, tk = load(tag)
    CODE[tag] = [extract(t) for t in gen(mo, tk, SOLVE, PR, BS)]
    mo = None; tk = tk   # thao tham chieu cua CALLER truoc khi gc
    free()
    print(f"{tag} xong ({time.time()-t0:.0f}s)", flush=True)
    json.dump({"partial": True, "raw": {k: v for k, v in CODE.items()}, "TESTS": TESTS},
              open(f"/kaggle/working/partial_{RUN}.json", "w"))

PASS = {k: grade(v) for k, v in CODE.items()}
CNT = {k: par(_run, [(v[i], TESTS[i], "cnt") for i in range(N)]) for k, v in CODE.items()}
A = lambda p: round(sum(p)/N, 4)

def analyse(pool):
    union = sum(1 for i in range(N) if any(PASS[k][i] for k in pool)) / N
    sel, ties = [], 0
    for i in range(N):
        sc = [CNT[k][i] for k in pool] if TESTS[i] else [0]*len(pool)
        mx = max(sc)
        if sc.count(mx) == len(pool): ties += 1
        sel.append(PASS[pool[sc.index(mx)]][i])
    base = A(PASS[pool[0]])
    g = union - base
    from collections import Counter
    dist = Counter(sum(PASS[k][i] for k in pool) for i in range(N))
    return {"acc_each": {k: A(PASS[k]) for k in pool}, "base": base,
            "H": round(union, 4), "SEL": round(sum(sel)/N, 4),
            "_H_raw": union, "_SEL_raw": sum(sel)/N,   # #152: tru TRUOC roi moi lam tron
            "H_minus_base": round(g, 4), "SEL_minus_base": round(sum(sel)/N - base, 4),
            "kappa": round((sum(sel)/N - base)/g*100, 1) if g > 1e-9 else None,
            "tie_rate": round(ties/N, 4),
            "dist_n_correct": {str(c): dist.get(c, 0) for c in range(len(pool)+1)},
            "all_wrong": dist.get(0, 0), "all_right": dist.get(len(pool), 0),
            "mixed": N - dist.get(0, 0) - dist.get(len(pool), 0)}

POOLS = {"A_one": ["Q1"], "B_sampling": ["Q1", "Q2"], "C_family": ["Q1", "L", "D"]}
RES = {k: analyse(v) for k, v in POOLS.items()}

def nrm(s): return " ".join(s.split())
off = [set(nrm(x) for x in r["test_list"][1:3]) for r in ALL]
ngen = sum(len(t) for t in TESTS)
copy_rate = round(sum(1 for i in range(N) for a in TESTS[i] if nrm(a) in off[i])/max(ngen,1), 4)
sound = par(_run, [(ALL[i]["code"], TESTS[i], "all") for i in range(N)])
soundness = round(sum(1 for i in range(N) if TESTS[i] and sound[i])/max(sum(1 for t in TESTS if t),1), 4)
comp = round(sum(compiles(c) for v in CODE.values() for c in v)/(len(CODE)*N), 4)

res = {"tag": RUN, "n": N, "pools": RES, "test_copy_rate": copy_rate,
       "test_soundness": soundness, "compile_rate": comp,
       "SEL_C_minus_A": round(RES["C_family"]["_SEL_raw"] - RES["A_one"]["_SEL_raw"], 4),
       "SEL_C_minus_B": round(RES["C_family"]["_SEL_raw"] - RES["B_sampling"]["_SEL_raw"], 4),
       "H_C_minus_B": round(RES["C_family"]["_H_raw"] - RES["B_sampling"]["_H_raw"], 4)}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump([{"task_id": ALL[i]["task_id"], "tests": TESTS[i],
            **{k: CODE[k][i][:800] for k in CODE}, **{"p_"+k: PASS[k][i] for k in PASS},
            **{"c_"+k: CNT[k][i] for k in CNT}} for i in range(N)],
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H80 TONG KET ====")
print(f"  n={N} | bien dich {comp:.4f} | soundness {soundness:.4f} | copy_rate {copy_rate:.4f}")
print(f"  acc tung model: " + "  ".join(f"{k}={A(PASS[k]):.4f}" for k in CODE))
for name, r in RES.items():
    print(f"\n  --- pool {name} ---")
    print(f"    acc ung vien: {r['acc_each']}")
    print(f"    TRAN H = {r['H']:.4f} (+{r['H_minus_base']:.4f})  |  SEL = {r['SEL']:.4f} (+{r['SEL_minus_base']:.4f})  |  kappa = {r['kappa']}%")
    print(f"    phan bo so ung vien dung: {r['dist_n_correct']}  (cung sai {r['all_wrong']} / cung dung {r['all_right']} / hon hop {r['mixed']})")
    print(f"    tie_rate = {r['tie_rate']:.4f}")
ca, cb = res["SEL_C_minus_A"], res["SEL_C_minus_B"]
q = A(PASS["Q1"]); mn = min(A(PASS[k]) for k in ["L", "D"])
print(f"\n  SEL(C) - SEL(A) = {ca:+.4f}   <-- DAI LUONG CHINH (#96)")
print(f"  SEL(C) - SEL(B) = {cb:+.4f}  | H(C) - H(B) = {res['H_C_minus_B']:+.4f}")
print(f"  cong: acc(32B) = {q:.4f} ({'DAT' if .60 <= q <= .90 else 'HUY'}) | acc(L,D) min = {mn:.4f} ({'DAT' if mn >= .35 else 'HUY'})")
print("\n-- bang khoa #96 --")
if not (.60 <= q <= .90) or mn < .35: print("  -> HUY: cong nang luc truot")
elif soundness < .50 or copy_rate > .20: print("  -> HUY: cong test truot")
elif ca >= .02 and cb >= -.01: print("  -> HANG 1: M2 DANG MANH DUNG. Model yeu-khac-ho van dong gop, RE HON them mau.")
elif ca >= .02: print("  -> HANG 2: co dong gop nhung thua them mau -> da dang ho chi thang giua model NGANG CO.")
elif abs(ca) < .02: print("  -> HANG 3: chenh nang luc NUOT phan da dang. Thu hep M2.")
else: print("  -> HANG 4: them model yeu HAI khi da co model manh.")
if res["H_C_minus_B"] > .02 and cb < -.01: print("  -> them: tran cao hon ma khong khai thac duoc -> kappa tut khi pool lech nang luc.")
print("XONG", flush=True)
