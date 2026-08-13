# H63 (dang ky truoc #68) — REFACTOR bang CHON LOC, khong phai SUA CHUA.
# ref1 | ref_exec3 (tai lap H53) | ref_sel8 (loc bang test, xep hang bang nut AST) | ref_sel8_first
import re, ast, json, time, tempfile, subprocess, sys, os, glob
from concurrent.futures import ThreadPoolExecutor
import torch
subprocess.run([sys.executable,"-m","pip","install","-q","bitsandbytes>=0.46.1"],check=False)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from datasets import load_dataset

RUN = "@@RUN@@"
M7 = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True), key=len)[0])
N, MAXNEW, TEMP, K = 300, 768, 0.8, 8
TIMEOUT = 60
BS = 8           # 7B nf4 ~5 GB tren T4 16 GB
torch.manual_seed(0)

REFAC = ("Refactor the code below to be simpler and more readable. "
         "The behaviour MUST NOT change: same inputs give the same outputs. "
         "Return ONLY the complete refactored code inside a ```python block.")
FIXERR = ("The refactored code below FAILED its tests. Here is the error. Fix it so the "
          "behaviour matches the original exactly. Return ONLY the complete corrected code "
          "inside a ```python block.")

def extract(t):
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()
def nodes(code):
    try: return sum(1 for _ in ast.walk(ast.parse(code)))
    except Exception: return None

DS = load_dataset("bigcode/bigcodebench", split="v0.1.4")
ALL = [DS[i] for i in range(min(N, len(DS)))]
print(f"BigCodeBench {len(ALL)} bai", flush=True)

def run_tests(r, code):
    if not code or not code.strip(): return False
    try: compile(code, "<s>", "exec")
    except Exception: return False
    prog = code + "\n\n" + r["test"] + "\n\nimport unittest\nunittest.main(argv=['x'],exit=False,verbosity=0)\n"
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        res = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        out = (res.stdout or "") + (res.stderr or "")
        return (re.search(r"^OK", out, re.M) is not None) or ("FAILED" not in out and res.returncode == 0)
    except Exception: return False
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
def run_err(r, code):
    """tra (dat, stderr rut gon) — dung cho nhanh sua chua"""
    if not code or not code.strip(): return False, "empty output"
    try: compile(code, "<s>", "exec")
    except Exception as e: return False, f"SyntaxError: {e}"
    prog = code + "\n\n" + r["test"] + "\n\nimport unittest\nunittest.main(argv=['x'],exit=False,verbosity=0)\n"
    p = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(prog); p = f.name
        res = subprocess.run([sys.executable, p], capture_output=True, text=True, timeout=TIMEOUT)
        out = (res.stdout or "") + (res.stderr or "")
        ok_ = (re.search(r"^OK", out, re.M) is not None) or ("FAILED" not in out and res.returncode == 0)
        return ok_, out[-1200:]
    except subprocess.TimeoutExpired: return False, "TimeoutExpired"
    except Exception as e: return False, str(e)[:300]
    finally:
        if p:
            try: os.unlink(p)
            except Exception: pass
def many(fn, pairs, w=12):
    with ThreadPoolExecutor(max_workers=w) as ex:
        return list(ex.map(lambda a: fn(*a), pairs))

# ---- LOC: chi giu bai ma LOI GIAI CHUAN dat test (dung nhu H52) ----
t0 = time.time()
base_ok = many(run_tests, [(r, r["complete_prompt"] + r["canonical_solution"]) for r in ALL], 16)
KEEP = [i for i in range(len(ALL)) if base_ok[i]]
print(f"loc: {len(KEEP)}/{len(ALL)} bai co loi giai chuan DAT test ({time.time()-t0:.0f}s)", flush=True)
if len(KEEP) < 250:
    print(f"HUY: n={len(KEEP)} < 250 (cong khoa #68)", flush=True)
    json.dump({"halt": "n_too_small", "n": len(KEEP)}, open(f"/kaggle/working/res_{RUN}.json", "w")); print("XONG", flush=True); raise SystemExit(0)
SRC = {i: ALL[i]["complete_prompt"] + ALL[i]["canonical_solution"] for i in KEEP}
N0  = {i: nodes(SRC[i]) for i in KEEP}

tk = AutoTokenizer.from_pretrained(M7); tk.padding_side = "left"
if tk.pad_token is None: tk.pad_token = tk.eos_token
BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
m = AutoModelForCausalLM.from_pretrained(M7, quantization_config=BNB, device_map={"": 0}).eval()
print(f"GPU={torch.cuda.get_device_name(0)} sm_{torch.cuda.get_device_capability(0)[0]}{torch.cuda.get_device_capability(0)[1]}\nnap 7B: VRAM {torch.cuda.memory_allocated()/2**30:.2f} GB", flush=True)

@torch.no_grad()
def gen(sysm, usrs, temp, bs=BS):
    outs, i = [], 0
    while i < len(usrs):
        ch = usrs[i:i+bs]
        try:
            ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                  tokenize=False, add_generation_prompt=True) for u in ch]
            e = tk(ps, return_tensors="pt", padding=True).to(m.device)
            o = m.generate(**e, max_new_tokens=MAXNEW, do_sample=(temp > 0),
                           temperature=max(temp, 1e-5), top_p=0.95, pad_token_id=tk.pad_token_id)
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs == 1: raise
            bs = max(1, bs//2); print(f"  OOM -> lo {bs}", flush=True); continue
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o; torch.cuda.empty_cache(); i += bs
    return outs

# ---- nhanh 1: ref1 (greedy) ----
r1 = {i: extract(c) for i, c in zip(KEEP, gen(REFAC, [SRC[i] for i in KEEP], 0.0))}
p1 = dict(zip(KEEP, many(run_tests, [(ALL[i], r1[i]) for i in KEEP])))
print(f"ref1 xong ({time.time()-t0:.0f}s) preserve={sum(p1.values())/len(KEEP):.4f}", flush=True)

# ---- nhanh 2: ref_exec3 — sua toi da 3 vong theo stderr ----
cur = dict(r1); okm = dict(p1); rounds = {i: 0 for i in KEEP}
for rd in range(3):
    bad = [i for i in KEEP if not okm[i]]
    if not bad: break
    errs = dict(zip(bad, [e for _, e in many(run_err, [(ALL[i], cur[i]) for i in bad])]))
    us = [f"Original code:\n```python\n{SRC[i]}\n```\n\nRefactored code that FAILED:\n"
          f"```python\n{cur[i]}\n```\n\nError:\n{errs[i]}" for i in bad]
    fixed = gen(FIXERR, us, 0.0)
    newok = many(run_tests, [(ALL[i], extract(c)) for i, c in zip(bad, fixed)])
    for i, c, o in zip(bad, fixed, newok):
        cur[i] = extract(c); okm[i] = o; rounds[i] = rd + 1
    print(f"  exec vong {rd+1}: sua {len(bad)}, con hong {sum(1 for i in KEEP if not okm[i])}", flush=True)
e3, pe3 = cur, okm
print(f"ref_exec3 xong ({time.time()-t0:.0f}s) preserve={sum(pe3.values())/len(KEEP):.4f}", flush=True)

# ---- nhanh 3/4: 8 mau -> chay test ca 8 -> chon ----
flat = gen(REFAC, [SRC[i] for i in KEEP] * K, TEMP)
CAND = {i: [extract(flat[k*len(KEEP)+j]) for k in range(K)] for j, i in enumerate(KEEP)}
pairs, idxmap = [], []
for i in KEEP:
    for k in range(K):
        pairs.append((ALL[i], CAND[i][k])); idxmap.append((i, k))
res_all = many(run_tests, pairs, 16)
PASS = {i: [] for i in KEEP}
for (i, k), o in zip(idxmap, res_all):
    if o: PASS[i].append(k)
print(f"8 mau + chay test xong ({time.time()-t0:.0f}s)", flush=True)

sel, selfirst = {}, {}
for i in KEEP:
    ok_k = PASS[i]
    if not ok_k: sel[i], selfirst[i] = None, None; continue
    selfirst[i] = CAND[i][ok_k[0]]
    scored = [(nodes(CAND[i][k]), k) for k in ok_k]
    scored = [(n, k) for n, k in scored if n is not None]
    sel[i] = CAND[i][min(scored)[1]] if scored else CAND[i][ok_k[0]]

# ---- cham ----
def score(name, code, okmap):
    pres = [i for i in KEEP if okmap[i]]
    simp = [i for i in pres if nodes(code[i]) is not None and N0[i] is not None and nodes(code[i]) < N0[i]]
    parsed = sum(1 for i in KEEP if code[i] is not None and nodes(code[i]) is not None)
    nd = [nodes(code[i]) for i in pres if nodes(code[i]) is not None]
    return {"arm": name, "preserve": round(len(pres)/len(KEEP), 4),
            "simpler_of_preserve": round(len(simp)/max(len(pres), 1), 4),
            "good_refactor": round(len(simp)/len(KEEP), 4),
            "ast_parse_rate": round(parsed/len(KEEP), 4),
            "mean_nodes": round(sum(nd)/max(len(nd), 1), 1)}

okmap_sel  = {i: sel[i] is not None for i in KEEP}
rows = [score("ref1", r1, p1), score("ref_exec3", e3, pe3),
        score("ref_sel8", {i: (sel[i] or "") for i in KEEP}, okmap_sel),
        score("ref_sel8_first", {i: (selfirst[i] or "") for i in KEEP}, okmap_sel)]
orig_nodes = round(sum(N0[i] for i in KEEP if N0[i]) / len(KEEP), 1)
npass = [len(PASS[i]) for i in KEEP]
res = {"n": len(KEEP), "orig_mean_nodes": orig_nodes, "K": K, "rows": rows,
       "npass_hist": {str(v): npass.count(v) for v in range(K+1)},
       "mean_npass": round(sum(npass)/len(npass), 2),
       "zero_pass": sum(1 for v in npass if v == 0),
       "exec3_mean_rounds": round(sum(rounds.values())/max(sum(1 for i in KEEP if not p1[i]), 1), 2)}
json.dump(res, open(f"/kaggle/working/res_{RUN}.json", "w"), indent=2)
json.dump({str(i): {"src": SRC[i][:2500], "ref1": r1[i][:2500], "exec3": e3[i][:2500],
                    "sel8": (sel[i] or "")[:2500], "npass": len(PASS[i])} for i in KEEP},
          open(f"/kaggle/working/traces_{RUN}.json", "w"))

print("\n==== H63 TONG KET ====")
print(f"  n = {len(KEEP)} | goc TB {orig_nodes} nut | K = {K}")
print(f"  {'nhanh':16s} {'preserve':>9s} {'simpler|p':>10s} {'GOOD':>8s} {'AST%':>6s} {'nut TB':>7s}")
for r in rows:
    print(f"  {r['arm']:16s} {r['preserve']:9.4f} {r['simpler_of_preserve']:10.4f} "
          f"{r['good_refactor']:8.4f} {r['ast_parse_rate']:6.3f} {r['mean_nodes']:7.1f}")
G = {r["arm"]: r["good_refactor"] for r in rows}
P = {r["arm"]: r["preserve"] for r in rows}
d = G["ref_sel8"] - G["ref_exec3"]
dfirst = G["ref_sel8"] - G["ref_sel8_first"]
print(f"\n  so mau DAT / bai: TB {res['mean_npass']}/{K} | {res['zero_pass']} bai KHONG mau nao dat")
print(f"  good(sel8) - good(exec3)      = {d:+.4f}   <-- DAI LUONG CHINH (bang khoa #68)")
print(f"  good(sel8) - good(sel8_first) = {dfirst:+.4f}   <-- LOC hay XEP HANG?")
print(f"\n  cong tai lap: preserve(ref1) = {P['ref1']:.4f} "
      f"({'DAT' if .70 <= P['ref1'] <= .79 else 'HUY — ngoai [.70,.79]'})")
print(f"  cong AST: {min(r['ast_parse_rate'] for r in rows):.3f} ({'DAT' if min(r['ast_parse_rate'] for r in rows) >= .80 else 'HUY'})")
print("\n-- bang khoa #68 --")
if not (.70 <= P["ref1"] <= .79): print("  -> HUY: khong tai lap duoc ref1")
elif d >= .08:      print("  -> HANG 1: CHON LOC THANG SUA CHUA tren refactor. Quy tac 'loc, dung sua' TONG QUAT sang bien doi code.")
elif d >= .02:      print("  -> HANG 2: chon loc hon sua chua nhung KHIEM TON (chi phi 8 luot vs <=4).")
elif abs(d) < .02:  print("  -> HANG 3: CHON LOC KHONG tong quat sang refactor. Nut that la NANG LUC GIU NGU NGHIA.")
else:               print("  -> HANG 4: chon loc TE HON sua chua. Rut huong nay.")
if dfirst < .02: print("  -> them: loi ich den tu LOC (co ban song sot), KHONG tu XEP HANG theo do don gian.")
if P["ref_sel8"] < .90: print(f"  -> them: preserve(sel8) = {P['ref_sel8']:.4f} < .90 -> GIOI HAN NANG LUC, khong phai gioi han tim kiem.")
print("XONG", flush=True)
