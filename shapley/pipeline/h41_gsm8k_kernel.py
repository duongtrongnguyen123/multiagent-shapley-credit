# H41 (dang ky truoc #47) — KIEM GIA THUYET "TRAN" NGAY TRONG GSM8K (mien escalate da THUA).
#
# Khac biet vs H40: GSM8K KHONG co truong 'level'. Dung SO BUOC TINH = so chu thich <<...>>
# trong loi giai chuan de xep do kho.
# Phan bo (N=500): DE (<=2 buoc) 188 · GIUA (3) 125 · KHO (>=4) 187 — deu >= 40.
#
# Giao thuc H39 y nguyen:
#   3 mau 1.5B -> dong thuan (>=2/3 giong nhau) -> nhan, dung.
#   Khong dong thuan -> 7B TUAN TU co mo neo (solve lai voi dap an cu + verify).
#
# Kernel chi SINH va LUU du lieu tho. Phan ra co che (gain, opp_cost, dang thuc tu kiem)
# lam O LOCAL sau khi co du lieu.
#
# DUNG CA HAI T4 THAT SU (data parallel, KHONG phai pipeline):
#   1.5B fp16  = 3.1 GB  -> moi GPU mot ban sao
#   7B   nf4   = ~5  GB  -> moi GPU mot ban sao   (fp16 15.2 GB KHONG vua 1 the T4)
import os, re, csv, json, glob, threading, torch, subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", "bitsandbytes>=0.46.1"])
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

K, MAXNEW = 8, 512
BSS, BSB = 48, 32          # batch size cho 1.5B / 7B, tinh tu VRAM
TEMP = 0.8                 # nhiet do lay mau cho 3 mau 1.5B va 8 mau 7B song song

# ---- tim model va data tren Kaggle ----
M15 = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors", recursive=True), key=len)[0])
M7  = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True), key=len)[0])
CSV = sorted(glob.glob("/kaggle/input/**/main_test.csv", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV)))
print(f"M15={M15}\nM7={M7}\nCSV={CSV} cot={list(ALL[0].keys())}", flush=True)

NG = torch.cuda.device_count()
DEVS = [f"cuda:{i}" for i in range(NG)]
print(f"so GPU={NG} -> {DEVS}", flush=True)
assert NG >= 1

# ---- GSM8K: cau hoi, dap an, SO BUOC TINH ----
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

def count_steps(answer_text):
    """Dem so buoc tinh = so chu thich <<...>> trong loi giai chuan GSM8K.
    Vi du: 'Bob has 5 apples. <<5+3=8>> He now has 8. <<8-2=6>> #### 6' -> 2 buoc."""
    return len(re.findall(r"<<[^>]+>>", answer_text or ""))

def difficulty(steps):
    """Phan loai do kho theo so buoc tinh (dang ky #47):
    DE  = <=2 buoc, GIUA = 3 buoc, KHO = >=4 buoc."""
    if steps <= 2: return 1   # DE
    if steps == 3: return 2   # GIUA
    return 3                  # KHO

QS = [r["question"] for r in ALL]
GS = [NUM.findall(r["answer"].split("####")[-1])[0].replace(",", "") for r in ALL]
STEPS = [count_steps(r["answer"]) for r in ALL]
DIFF  = [difficulty(s) for s in STEPS]

N = len(ALL)
Q  = {i: QS[i] for i in range(N)}
G  = {i: GS[i] for i in range(N)}
LV = {i: STEPS[i] for i in range(N)}   # so buoc tinh (nguyen thuy)
DF = {i: DIFF[i] for i in range(N)}    # tang do kho (1=DE, 2=GIUA, 3=KHO)

print(f"tong so: {N} bai", flush=True)
print(f"phan bo do kho: DE(<={2})={sum(1 for d in DIFF if d==1)} | "
      f"GIUA(3)={sum(1 for d in DIFF if d==2)} | "
      f"KHO(>={4})={sum(1 for d in DIFF if d==3)}", flush=True)

TAIL   = "End with 'The answer is <number>'."
SOLVE  = f"Solve step by step. {TAIL}"
VERIFY = f"Check the proposed solution step by step; if wrong, correct it. {TAIL}"
ANCH   = f"Solve step by step. A previous attempt answered: @@A@@. {TAIL}"

# ---- parser cho GSM8K (tra ve so) ----
def pred(t):
    m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I) or NUM.findall(t or "")
    return m[-1].replace(",", "") if m else None

def ok(x, g):
    try: return x is not None and abs(float(x) - float(g)) < 1e-4
    except: return x == g

# ---- tokenizers ----
def mktok(p):
    tk = AutoTokenizer.from_pretrained(p); tk.padding_side = "left"
    if tk.pad_token is None: tk.pad_token = tk.eos_token
    return tk
T15, T7 = mktok(M15), mktok(M7)

# ---- sinh batch ----
def gen(model, tk, sysm, usrs, bs, temp):
    outs = []
    for i in range(0, len(usrs), bs):
        ch = usrs[i:i+bs]
        ps = [tk.apply_chat_template([{"role": "system", "content": sysm},
                                      {"role": "user", "content": u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tk(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=MAXNEW, do_sample=(temp > 0),
                               temperature=max(temp, 1e-5), top_p=0.95, pad_token_id=tk.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
        del e, o
    return outs

def split(items, n):
    return [items[j::n] for j in range(n)]

def parallel_gen(models, tk, sysm, prompts_by_idx, bs, temp, rounds):
    """Moi GPU mot ban sao model, moi luong lo mot phan bai."""
    parts = split(list(prompts_by_idx.keys()), len(models))
    store, lock = {}, threading.Lock()
    def work(m, sub):
        loc = {i: [] for i in sub}
        for _ in range(rounds):
            outs = gen(m, tk, sysm, [prompts_by_idx[i] for i in sub], bs, temp)
            for i, o in zip(sub, outs): loc[i].append(o)
        with lock: store.update(loc)
    ths = [threading.Thread(target=work, args=(models[j], parts[j])) for j in range(len(models)) if parts[j]]
    for t in ths: t.start()
    for t in ths: t.join()
    return store

# ==========================================================
# PHA 1: 1.5B fp16, mot ban sao MOI GPU — 3 mau (K=8 nhung chi dung 3 dau)
# ==========================================================
smalls = []
for d in DEVS:
    m = AutoModelForCausalLM.from_pretrained(M15, torch_dtype=torch.float16).to(d).eval()
    smalls.append(m)
print(f"1.5B: {len(smalls)} ban sao", flush=True)

# Lay 3 mau (K=3 la du cho vote dong thuan), nhung sinh 8 mau de co du lieu maj@3, maj@8
S_TXT = parallel_gen(smalls, T15, SOLVE, Q, BSS, TEMP, K)
for m in smalls: del m
del smalls; torch.cuda.empty_cache()
print("xong pha 1 (1.5B)", flush=True)

S_PRED = {i: [pred(t) for t in S_TXT[i]] for i in range(N)}

# ---- vote dong thuan 3 mau dau ----
def vote3(ps):
    c = {}
    for p in ps[:3]:
        if p is not None: c[p] = c.get(p, 0) + 1
    if not c: return None, 0
    b = max(c, key=c.get); return b, c[b]

ESC = [i for i in range(N) if vote3(S_PRED[i])[1] < 2]
print(f"escalate {len(ESC)}/{N} ({len(ESC)/N:.1%})", flush=True)

# Thong ke escalate theo tang do kho
for d, name in [(1, "DE"), (2, "GIUA"), (3, "KHO")]:
    idx = [i for i in range(N) if DF[i] == d]
    esc_d = [i for i in idx if i in ESC]
    if idx:
        print(f"  tang {name} (n={len(idx)}): escalate {len(esc_d)}/{len(idx)} = {len(esc_d)/len(idx):.1%}", flush=True)

# ==========================================================
# PHA 2: 7B nf4, mot ban sao MOI GPU — 8 mau (big_maj@3, big_maj@8)
# ==========================================================
BNB = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
bigs = []
try:
    for d in DEVS:
        m = AutoModelForCausalLM.from_pretrained(M7, quantization_config=BNB, device_map={"": d}).eval()
        bigs.append(m)
    print(f"7B nf4: {len(bigs)} ban sao | VRAM MiB/gpu:",
          [round(torch.cuda.memory_allocated(i) / 1048576) for i in range(NG)], flush=True)
except Exception as e:
    print(f"nf4 THAT BAI ({type(e).__name__}: {e}) -> quay ve fp16 device_map=auto", flush=True)
    for m in bigs: del m
    bigs = []; torch.cuda.empty_cache()
    bigs = [AutoModelForCausalLM.from_pretrained(M7, torch_dtype=torch.float16, device_map="auto").eval()]
QUANT = "nf4" if len(bigs) == NG else "fp16-fallback"

B_TXT = parallel_gen(bigs, T7, SOLVE, Q, BSB, TEMP, K)
print("xong pha 2 (7B song song)", flush=True)

# ==========================================================
# PHA 3: 7B TUAN TU co MO NEO — chi cho bai can escalate
# ==========================================================
SEQ_TXT, SEQ = {}, {}
if ESC:
    anch = {i: ANCH.replace("@@A@@", str(vote3(S_PRED[i])[0])) + f"\n\n{Q[i]}" for i in ESC}
    s1 = parallel_gen(bigs, T7, SOLVE, anch, BSB, 0.0, 1)
    ver = {i: f"{Q[i]}\n\nProposed solution:\n{s1[i][0]}" for i in ESC}
    s2 = parallel_gen(bigs, T7, VERIFY, ver, BSB, 0.0, 1)
    for i in ESC:
        SEQ_TXT[i] = {"pass1": s1[i][0], "pass2": s2[i][0]}
        SEQ[i] = pred(s2[i][0]) if pred(s2[i][0]) is not None else pred(s1[i][0])
print(f"xong pha 3 (7B tuan tu, {len(ESC)} bai)", flush=True)

# ==========================================================
# LUU DU LIEU THO
# ==========================================================
CAP = 4000  # cat text de giam kich thuoc
out = {
    "tag": "H41_gsm8k",
    "experiment": "H41",
    "preregistration": "#47",
    "task": "gsm8k",
    "n": N,
    "k_samples": K,
    "quant_big": QUANT,
    "dtype_small": "fp16",
    "n_gpu": NG,
    "temp": TEMP,
    "difficulty_definition": "so buoc tinh = so chu thich <<...>> trong loi giai chuan",
    "difficulty_bins": {"DE": "<=2 buoc", "GIUA": "3 buoc", "KHO": ">=4 buoc"},
    "difficulty_counts": {
        "DE": sum(1 for d in DIFF if d == 1),
        "GIUA": sum(1 for d in DIFF if d == 2),
        "KHO": sum(1 for d in DIFF if d == 3),
    },
    "n_escalated": len(ESC),
    "pct_escalated": len(ESC) / N,
    "items": [],
}
for i in range(N):
    out["items"].append({
        "qi": i,
        "steps": LV[i],           # so buoc tinh (nguyen thuy)
        "difficulty": DF[i],      # 1=DE, 2=GIUA, 3=KHO
        "gold": G[i],
        "small_pred": S_PRED[i],  # 8 mau cua 1.5B
        "big_pred": [pred(t) for t in B_TXT[i]],  # 8 mau cua 7B
        "seq_pred": SEQ.get(i),   # dap an sau escalate tuan tu
        "escalated": i in ESC,
        "small_text": [t[:CAP] for t in S_TXT[i]],
        "big_text":   [t[:CAP] for t in B_TXT[i]],
        "seq_text":   {k: v[:CAP] for k, v in SEQ_TXT.get(i, {}).items()},
    })

FNAME = "/kaggle/working/res_H41_gsm8k.json"
json.dump(out, open(FNAME, "w"))
print(f"DA LUU {N} bai -> {FNAME}", flush=True)

# ==========================================================
# IN TOM TAT NGAY TREN KERNEL (cho doc nhanh, khong phai ket luan)
# ==========================================================
def acc(preds_list, golds):
    return sum(1 for ps, g in zip(preds_list, golds) if any(ok(p, g) for p in ps[:3])) / len(golds)

small_maj3 = sum(1 for i in range(N) if any(ok(p, G[i]) for p in S_PRED[i][:3])) / N
small_maj8 = sum(1 for i in range(N) if any(ok(p, G[i]) for p in S_PRED[i])) / N
big_maj3   = sum(1 for i in range(N) if any(ok(p, G[i]) for p in [pred(t) for t in B_TXT[i]][:3])) / N
big_maj8   = sum(1 for i in range(N) if any(ok(p, G[i]) for p in [pred(t) for t in B_TXT[i]])) / N

# escalate_seq: neu dong thuan -> small_pred[0]; neu escalate -> seq_pred
esc_seq_correct = 0
for i in range(N):
    v, c = vote3(S_PRED[i])
    if c >= 2:
        if ok(v, G[i]): esc_seq_correct += 1
    else:
        if SEQ.get(i) is not None and ok(SEQ[i], G[i]): esc_seq_correct += 1
escalate_seq = esc_seq_correct / N

print(f"\n{'='*60}", flush=True)
print(f"TOM TAT H41 — GSM8K, N={N}", flush=True)
print(f"{'='*60}", flush=True)
print(f"small_maj3  = {small_maj3:.4f}", flush=True)
print(f"small_maj8  = {small_maj8:.4f}", flush=True)
print(f"big_maj3    = {big_maj3:.4f}", flush=True)
print(f"big_maj8    = {big_maj8:.4f}", flush=True)
print(f"escalate_seq= {escalate_seq:.4f}", flush=True)
print(f"pct_escalate= {len(ESC)/N:.1%}", flush=True)

# Phan ra theo tang do kho
for d, name in [(1, "DE (<=2 buoc)"), (2, "GIUA (3 buoc)"), (3, "KHO (>=4 buoc)")]:
    idx = [i for i in range(N) if DF[i] == d]
    if not idx: continue
    s_maj3 = sum(1 for i in idx if any(ok(p, G[i]) for p in S_PRED[i][:3])) / len(idx)
    b_maj3 = sum(1 for i in idx if any(ok(p, G[i]) for p in [pred(t) for t in B_TXT[i]][:3])) / len(idx)
    esc_d = [i for i in idx if i in ESC]
    kept = [i for i in idx if i not in ESC]
    # gain_on_esc: cai thu duoc o nhom escalate
    if esc_d:
        small_on_esc = sum(1 for i in esc_d if any(ok(p, G[i]) for p in S_PRED[i][:3])) / len(esc_d)
        seq_on_esc   = sum(1 for i in esc_d if SEQ.get(i) and ok(SEQ[i], G[i])) / len(esc_d)
        gain_on_esc  = seq_on_esc - small_on_esc
    else:
        small_on_esc = seq_on_esc = gain_on_esc = 0.0
    # opp_cost: cai tu bo o nhom giu lai
    if kept:
        small_on_kept = sum(1 for i in kept if any(ok(p, G[i]) for p in S_PRED[i][:3])) / len(kept)
        big3_on_kept  = sum(1 for i in kept if any(ok(p, G[i]) for p in [pred(t) for t in B_TXT[i]][:3])) / len(kept)
        opp_cost = big3_on_kept - small_on_kept
    else:
        small_on_kept = big3_on_kept = opp_cost = 0.0
    
    p_kept = len(kept) / len(idx)
    p_esc  = len(esc_d) / len(idx)
    delta  = (sum(1 for i in idx if (vote3(S_PRED[i])[1] >= 2 and ok(vote3(S_PRED[i])[0], G[i])) or
                   (vote3(S_PRED[i])[1] < 2 and SEQ.get(i) and ok(SEQ[i], G[i]))) / len(idx)) - b_maj3
    
    print(f"\n  {name} (n={len(idx)}, escalate={len(esc_d)}/{len(idx)}={p_esc:.1%}):", flush=True)
    print(f"    small_maj3  = {s_maj3:.4f}", flush=True)
    print(f"    big_maj3    = {b_maj3:.4f}", flush=True)
    print(f"    gain_on_esc = {gain_on_esc:+.4f}", flush=True)
    print(f"    opp_cost    = {opp_cost:+.4f}", flush=True)
    print(f"    p_kept={p_kept:.3f} p_esc={p_esc:.3f}", flush=True)
    print(f"    dang thuc: delta={delta:+.4f} vs cong thuc={p_kept*(-opp_cost)+p_esc*gain_on_esc:+.4f}", flush=True)

print(f"\n{'='*60}", flush=True)
print("XONG — Du lieu tho da luu. Phan ra va ket luan lam o local.", flush=True)
