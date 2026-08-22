# MAPoRL co-train S+V+A kernel (Multi-Agent Post-Co-Training with RL, inspired by
# Park et al. ACL 2025 "MAPoRL2").
#
# Khac credit_rl_kernel (train tung vai, 3 vai kia base): kernel NAY co-train
# S / V / A DONG THOI bang 3 LoRA adapter tren cung 1 base model (P giu base,
# nhu paper bat dau co-train tu turn 2). Pipeline 1 duong: plan(P base)
# -> sol(S adapter) -> v(V adapter, verify sol) -> a(A adapter, aggregate).
# Reward influence-aware:
#   r_S = soft(sol) + BETA_S * (soft(v) + soft(a)) / 2   # S thuong them neu giup V,A dung
#   r_V = soft(v) + BETA_V * soft(a)                     # V thuong them neu giup A dung
#   r_A = soft(a)                                        # A = ket qua cuoi cung
# soft() = correctness 0/1 tru penalty anti-reward-hacking (short/empty, post-boxed junk).
# Group advantage per cau (GRPO) tren {r_S, r_V, r_A} -> chong 3 agent cung collapse
# ve dap an sai trung nhau. Inner loop: multi-epoch PPO (clip + IS + KL vs base).
import os, re, csv, json, glob, math, random, contextlib, subprocess, sys, time

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# ---- config (patched by orchestrate_maporl.py) ------------------------------
TASK    = __TASK__          # "gsm8k" | "math"
N_TRAIN = __N_TRAIN__       # so cau train lam pool
K       = __K__             # cau/outer loop
OUTER   = __OUTER__         # so vong ngoai (rollout + reward recompute)
E       = __E__             # so epoch inner (multi-epoch PPO)
LR      = __LR__
LR_A    = __LR_A__          # (khong dung: A frozen=base, chi train S/V)
EPS     = __EPS__           # PPO ratio clip
BETA    = __BETA__          # he so KL vs ref
TEMP    = __TEMP__          # nhiet do sampling khi rollout (exploration)
SEED    = __SEED__
BS      = __BS__            # batch sinh
MB      = __MB__            # mini-batch PPO (so sample/step)
BETA_S  = __BETA_S__        # trong so influence cua S len V,A
BETA_V  = __BETA_V__        # trong so influence cua V len A

assert TASK in ("gsm8k", "math"), f"TASK={TASK}"

# ---- debug: in cay /kaggle/input som nhat co the (log rong = crash day day) ----
print("DEBUG input tree:", flush=True)
for _d in sorted(glob.glob("/kaggle/input/*", recursive=False)):
    print("  ", _d, flush=True)
    for _f in sorted(glob.glob(f"{_d}/**/*", recursive=True))[:20]:
        print("     ", _f, flush=True)

def find_one(pattern, what):
    hits = glob.glob(pattern, recursive=True)
    if not hits:
        raise FileNotFoundError(f"{what}: no match {pattern} :: "
                                f"{glob.glob('/kaggle/input/**', recursive=True)[:40]}")
    return sorted(hits, key=len)[0]

# model dinh vi bang model.safetensors - giong moi kernel da chay duoc
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
if not _c:
    raise FileNotFoundError("khong thay model.safetensors :: "
                            + str(glob.glob("/kaggle/input/**", recursive=True)[:40]))
MODEL_DIR = os.path.dirname(sorted(_c, key=len)[0])
if TASK == "math":
    TRAIN_CSV = find_one("/kaggle/input/**/MATH/train/**/*.json", "math train json")
    TEST_CSV  = find_one("/kaggle/input/**/math_500_test.csv", "math-500 test csv")
else:
    TRAIN_CSV = find_one("/kaggle/input/**/main_train.csv", "gsm8k train csv")
    TEST_CSV  = find_one("/kaggle/input/**/main_test.csv", "gsm8k test csv")
print(f"MODEL={MODEL_DIR}\nTASK={TASK}\nTRAIN={TRAIN_CSV}\nTEST={TEST_CSV}", flush=True)

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13,<0.15"],
               check=False)

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

torch.manual_seed(SEED); random.seed(SEED)

tok = AutoTokenizer.from_pretrained(MODEL_DIR)
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
base = AutoModelForCausalLM.from_pretrained(MODEL_DIR, torch_dtype=torch.float16,
                                            device_map={"": 0})
def _lora_cfg():
    return LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                      bias="none", task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
model = get_peft_model(base, _lora_cfg(), adapter_name="s")
model.add_adapter("v", _lora_cfg())
model.set_adapter("s")
for pn, p in model.named_parameters():
    if ".lora_A." in pn or ".lora_B." in pn:
        p.requires_grad = True
model.config.use_cache = True
def _adapter_params(name):
    return [p for n, p in model.named_parameters()
            if p.requires_grad
            and (f".lora_A.{name}." in n or f".lora_B.{name}." in n)]
pS, pV = _adapter_params("s"), _adapter_params("v")
if not (pS and pV):
    names = [n for n, p in model.named_parameters() if p.requires_grad]
    print("TRAINABLE PARAM NAMES:", names[:40], flush=True)
    raise AssertionError(f"adapter params rong: s={len(pS)} v={len(pV)}")
opt = torch.optim.AdamW(
    [{"params": pS, "lr": LR}, {"params": pV, "lr": LR}])
print(f"LoRA co-train S/V (A frozen=base); params: S={len(pS)} V={len(pV)} "
      f"| lr={LR}", flush=True)

if TASK == "math":
    PLAN_SYS   = ("You are a math planning assistant. Read the competition problem and give a "
                  "concise numbered plan of the solution steps. Do NOT compute the final answer.")
    SOLVE_SYS  = ("You are an expert mathematician. Solve the problem step by step. Put the "
                  "final answer in \\boxed{}.")
    VERIFY_SYS = ("You are a math verifier. Given a problem and a proposed solution, check each "
                  "step; if wrong, correct it. Put the final answer in \\boxed{}.")
    AGG_SYS    = ("You are given a math problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking and majority. Put the final answer in "
                  "\\boxed{}.")
else:
    PLAN_SYS   = ("You are a math planning assistant. Read the problem and give a concise "
                  "numbered plan of the steps needed. Do NOT compute the final answer.")
    SOLVE_SYS  = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                  "End with a line: 'The answer is <number>'.")
    VERIFY_SYS = ("You are a math verifier. You are given a problem and a proposed solution. "
                  "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
    AGG_SYS    = ("You are given a math problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking and majority. End with 'The answer is "
                  "<number>'.")

def chat(system, user):
    return tok.apply_chat_template(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        tokenize=False, add_generation_prompt=True)

def with_plan(q, plan):
    return q + "\n\nSuggested plan:\n" + plan

def verify_user(q, sol):
    return q + "\n\nProposed solution:\n" + sol

def agg_user(q, cands):
    body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(cands))
    return f"{q}\n\n{body}"

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def pred_answer(text):
    if not text:
        return None
    m = re.findall(r"(?:answer is|answer:|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", text, re.I)
    cands = m if m else NUM_RE.findall(text)
    return cands[-1].replace(",", "").strip().rstrip(".") if cands else None

def gold_answer(ans):
    m = re.search(r"####\s*([-\d,\.]+)", ans)
    return m.group(1).replace(",", "").strip().rstrip(".") if m else None

def num_eq(a, b):
    try:
        return a is not None and b is not None and abs(float(a) - float(b)) < 1e-4
    except ValueError:
        return a == b

if TASK == "math":
    def boxed(s):
        i = s.rfind("\\boxed") if s else -1
        if i < 0: return None
        i = s.find("{", i)
        if i < 0: return None
        d, st = 0, i
        for j in range(i, len(s)):
            if s[j] == "{": d += 1
            elif s[j] == "}":
                d -= 1
                if d == 0: return s[st + 1:j]
        return None
    def norm(a):
        if a is None: return None
        a = str(a).strip()
        for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " ", ","]:
            a = a.replace(x, "")
        for x in ["\\(", "\\)", "\\[", "\\]"]: a = a.replace(x, "")
        a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
        a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
        return a.rstrip(".").strip("{}").lower()
    def eq_math(p, g):
        p, g = norm(p), norm(g)
        if not p or not g: return False
        if p == g: return True
        try: return abs(float(p) - float(g)) < 1e-6
        except: return False
    def extract(text):
        b = boxed(text) if text else None
        return b if b is not None else pred_answer(text)
    gold_answer = lambda sol: extract(sol)
    ok = lambda text, gold: eq_math(extract(text), gold)
else:
    ok = lambda text, gold: num_eq(pred_answer(text), gold)

def post_boxed_junk(text):
    i = text.rfind("\\boxed")
    if i < 0: return False
    j = text.find("}", i)
    if j < 0: return False
    return bool(text[j + 1:].strip())

def soft_ok(text, gold):
    """Correctness 0/1 tru penalty anti-reward-hacking -> reward graded/muot."""
    c = ok(text, gold)
    r = 1.0 if c else 0.0
    if not text or len(text.strip()) < 20:
        r -= 0.5
    if TASK == "math" and c and post_boxed_junk(text):
        r -= 0.5
    return r

@contextlib.contextmanager
def _null():
    yield

def gen(prompts, mx, use_lora, do_sample=False, temp=1.0, adapter=None):
    """Sinh van ban; use_lora=False -> chay base (adapter tat) cho P/ref.
    Tra ve (outs, pids, rids): pids/rids de tinh logp khi training."""
    if use_lora and adapter:
        model.set_adapter(adapter)
    outs, pids, rids = [], [], []
    ctx = _null() if use_lora else model.disable_adapter()
    with ctx:
        for i in range(0, len(prompts), BS):
            ch = prompts[i:i + BS]
            enc = tok(ch, return_tensors="pt", padding=True).to(model.device)
            with torch.no_grad():
                o = model.generate(**enc, max_new_tokens=mx,
                                   do_sample=do_sample,
                                   temperature=temp if do_sample else 1.0,
                                   pad_token_id=tok.pad_token_id)
            L = enc["input_ids"].shape[1]
            for j in range(len(ch)):
                rid = o[j, L:]
                rids.append(rid.tolist())
                outs.append(tok.decode(rid, skip_special_tokens=True).strip())
                pids.append(tok(ch[j], add_special_tokens=True).input_ids)
    return outs, pids, rids

def text_only(r):
    return r[0]

def logp(pid, rid, use_lora, grad=False, adapter=None):
    """Per-token log-prob cua trace (rid) sau prompt (pid), co/khong adapter.
    Chunk theo sequence de tranh peak fp32 (logits fp16 [T,V])."""
    if use_lora and adapter:
        model.set_adapter(adapter)
    pids = torch.tensor(pid, device=model.device, dtype=torch.long)
    rids = torch.tensor(rid, device=model.device, dtype=torch.long)
    full = torch.cat([pids, rids]).unsqueeze(0)
    ctx = _null() if use_lora else model.disable_adapter()
    with ctx:
        if grad:
            out = model(full)
        else:
            with torch.no_grad():
                out = model(full)
    lg = out.logits[0]                                   # fp16 [T, V]
    T = lg.shape[0]
    pl = len(pid)
    CH = 128
    lp = []
    for s in range(0, T - 1, CH):
        e = min(s + CH, T - 1)
        lse = torch.logsumexp(lg[s:e].float(), -1, keepdim=True)   # [CH,1] fp32
        chunk = lg[s:e].float() - lse                               # [CH,V] fp32 (nho)
        idx = full[0, s + 1:e + 1].unsqueeze(1)
        lp.append(chunk.gather(1, idx).squeeze(1))
    lp = torch.cat(lp)                                   # [T-1]
    return lp[pl - 1: pl - 1 + len(rid)]                 # [len(rid)]

# ---- du lieu: pool train (gsm8k main_train.csv | math MATH/train/**/*.json) -----
if TASK == "math":
    import glob as _g
    files = sorted(_g.glob("/kaggle/input/**/MATH/train/**/*.json", recursive=True))
    pool = []
    for fp in files[:N_TRAIN]:
        d = json.load(open(fp, encoding="utf-8"))
        pool.append({"problem": d.get("problem", "").strip(),
                     "solution": d.get("solution", "").strip()})
    rows = pool
    qs = [r["problem"] for r in rows]
    gs = [gold_answer(r["solution"]) for r in rows]
else:
    rows = list(csv.DictReader(open(TRAIN_CSV, newline="")))[:N_TRAIN]
    qs = [r["question"] for r in rows]
    gs = [gold_answer(r["answer"]) for r in rows]
n = len(rows)
print(f"pool train {n} cau | TASK={TASK}", flush=True)

# ==============================================================================
# Stage helper: tra ve prompt tung buoc cua pipeline 1 duong
# ==============================================================================
def p_plan(q):   return chat(PLAN_SYS, q)
def s_wp(q, pl): return chat(SOLVE_SYS, with_plan(q, pl))
def v_vwp(q, sol): return chat(VERIFY_SYS, verify_user(q, sol))
def a_svwp(q, sol, v): return chat(AGG_SYS, agg_user(q, [sol, v]))

MX_P, MX_S, MX_V, MX_A = 256, 512, 512, 256

# ==============================================================================
# Precompute plan (P base) 1 lan cho pool - khong phu thuoc S/V/A
# ==============================================================================
print("precompute plan (P base)...", flush=True)
PRE_PLAN = text_only(gen([p_plan(q) for q in qs], MX_P, False))
print("precompute xong", flush=True)
torch.cuda.empty_cache()

# ==============================================================================
# Vong ngoai: rollout 1 duong pipeline, co-train S/V/A (3 adapter, 1 base)
# ==============================================================================
t0 = time.time()
hist = []
for outer in range(OUTER):
    model.eval()
    idxs = random.sample(range(n), min(K, n))

    # ---- rollout (S/V = LoRA sampling, A = base frozen, P = base plan) ----
    plan_t = [PRE_PLAN[i] for i in idxs]
    sol, sol_p, sol_r = gen([s_wp(qs[i], plan_t[j]) for j, i in enumerate(idxs)],
                            MX_S, True, do_sample=TEMP > 0, temp=TEMP, adapter="s")
    v,   v_p,   v_r   = gen([v_vwp(qs[i], sol[j]) for j, i in enumerate(idxs)],
                            MX_V, True, do_sample=TEMP > 0, temp=TEMP, adapter="v")
    a,   a_p,   a_r   = gen([a_svwp(qs[i], sol[j], v[j]) for j, i in enumerate(idxs)],
                            MX_A, False)

    # ---- reward influence-aware (soft; A dung base, khong train) ----
    ss = [soft_ok(sol[j], gs[idxs[j]]) for j in range(len(idxs))]
    sv = [soft_ok(v[j], gs[idxs[j]]) for j in range(len(idxs))]
    sa = [soft_ok(a[j], gs[idxs[j]]) for j in range(len(idxs))]
    rS = [ss[j] + BETA_S * (sv[j] + sa[j]) / 2 for j in range(len(idxs))]
    rV = [sv[j] + BETA_V * sa[j] for j in range(len(idxs))]
    rA = list(sa)

    # ---- group advantage per cau (GRPO): normalize {r_S, r_V} ----
    samples = []
    for t in range(len(idxs)):
        grp = [rS[t], rV[t]]
        mean = sum(grp) / 2
        std = (sum((x - mean) ** 2 for x in grp) / 2) ** 0.5
        sd = max(std, 1e-4)
        adv = lambda x: max(-3.0, min(3.0, (x - mean) / sd))
        samples.append({"pid": sol_p[t], "rid": sol_r[t], "advs": [adv(rS[t])],
                        "adapter": "s"})
        samples.append({"pid": v_p[t], "rid": v_r[t], "advs": [adv(rV[t])],
                        "adapter": "v"})

    # ---- logp_old (policy rollout) & logp_ref (base) - cache truoc update ----
    torch.cuda.empty_cache()
    for s in samples:
        s["lp_old"] = logp(s["pid"], s["rid"], use_lora=True, grad=False,
                           adapter=s["adapter"]).detach()
        s["lp_ref"] = logp(s["pid"], s["rid"], use_lora=False, grad=False).detach()
    torch.cuda.empty_cache()

    # ---- inner loop: multi-epoch PPO (clip + IS + KL); backward tung sample
    #      de chi 1 autograd graph song (tranh OOM: logits [T,V] fp16) ----
    model.train()
    for ep in range(E):
        random.shuffle(samples)
        for b in range(0, len(samples), MB):
            batch = samples[b:b + MB]
            opt.zero_grad()
            for s in batch:
                lp = logp(s["pid"], s["rid"], use_lora=True, grad=True,
                          adapter=s["adapter"])
                d = torch.clamp(lp - s["lp_old"], -5.0, 5.0)
                ratio = torch.exp(d)
                rc = torch.clamp(ratio, 1 - EPS, 1 + EPS)
                surr = torch.zeros_like(ratio)
                for advv in s["advs"]:
                    surr = surr + torch.min(ratio * advv, rc * advv)
                surr = surr / len(s["advs"])
                kd = torch.clamp(s["lp_ref"] - lp, -5.0, 5.0)
                kl = torch.exp(kd) - kd - 1.0
                loss_s = (-surr.mean() + BETA * kl.mean()) / len(batch)
                if torch.isfinite(loss_s):
                    loss_s.backward()
                del lp
                torch.cuda.empty_cache()
            with torch.no_grad():
                for pn, p in model.named_parameters():
                    if p.grad is not None and not torch.isfinite(p.grad).all():
                        p.grad = torch.zeros_like(p.grad)
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad], 1.0)
            opt.step()
            with torch.no_grad():
                nbad = 0
                for pn, p in model.named_parameters():
                    if ".lora_A." in pn or ".lora_B." in pn:
                        if not torch.isfinite(p).all():
                            nbad += 1
                        p.data = torch.nan_to_num(
                            p.data, nan=0.0, posinf=0.05, neginf=-0.05)
                        p.data.clamp_(-1.0, 1.0)
                if nbad:
                    print(f"NaN/Inf adapter params repaired: {nbad} tensors", flush=True)
    model.eval()

    # ---- log ----
    el = time.time() - t0
    has_ok = sum(1 for j in range(len(idxs))
                 if ok(sol[j], gs[idxs[j]]) or ok(v[j], gs[idxs[j]])) / len(idxs)
    hist.append({
        "outer": outer + 1,
        "mean_rS": round(sum(rS) / len(rS), 4),
        "mean_rV": round(sum(rV) / len(rV), 4),
        "mean_rA": round(sum(rA) / len(rA), 4),
        "acc_sol": round(sum(ss) / len(ss), 4),
        "acc_v":   round(sum(sv) / len(sv), 4),
        "acc_a":   round(sum(sa) / len(sa), 4),
        "has_ok":  round(has_ok, 4),
        "samples": len(samples), "seconds": round(el, 1)})
    print(f"[SV outer {outer+1}/{OUTER}] rS={hist[-1]['mean_rS']:+.4f} "
          f"rV={hist[-1]['mean_rV']:+.4f} rA(base)={hist[-1]['mean_rA']:+.4f} "
          f"acc S/V/A={hist[-1]['acc_sol']:.3f}/{hist[-1]['acc_v']:.3f}/"
          f"{hist[-1]['acc_a']:.3f} has_ok={hist[-1]['has_ok']:.3f} "
          f"samples={len(samples)} elapsed={el/60:.1f}m", flush=True)
    if (outer + 1) % 5 == 0 or outer == OUTER - 1:
        with open("/kaggle/working/hist.json", "w") as f:
            json.dump(hist, f)

# ==============================================================================
# Eval cuoi kernel: pipeline base vs co-trained vs tung adapter solo (test)
# ==============================================================================
print(f"\n== quick eval co-train tren test (tach rong train) ==", flush=True)
N_EVAL = 100
if TASK == "math":
    trows = list(csv.DictReader(open(TEST_CSV, encoding="utf-8")))[:N_EVAL]
    tq = [r["Question"].strip() for r in trows]
    tg = [gold_answer(r["Answer"]) for r in trows]
else:
    trows = list(csv.DictReader(open(TEST_CSV, newline="")))[:N_EVAL]
    tq = [r["question"] for r in trows]
    tg = [gold_answer(r["answer"]) for r in trows]

# plan (P base) tinh 1 lan, dung chung cho moi pipeline eval
tp = text_only(gen([p_plan(q) for q in tq], MX_P, False))

def run_pipe(full):
    """full = {"S": bool, "V": bool}: vai nao dung adapter da train.
    A luon dung base (A frozen, khong co adapter)."""
    if full["S"]:
        ts1 = text_only(gen([s_wp(q, p) for q, p in zip(tq, tp)], MX_S, True,
                            adapter="s"))
    else:
        ts1 = text_only(gen([s_wp(q, p) for q, p in zip(tq, tp)], MX_S, False))
    if full["V"]:
        tv = text_only(gen([v_vwp(q, s) for q, s in zip(tq, ts1)], MX_V, True,
                           adapter="v"))
    else:
        tv = text_only(gen([v_vwp(q, s) for q, s in zip(tq, ts1)], MX_V, False))
    return text_only(gen([a_svwp(q, s, v) for q, s, v in zip(tq, ts1, tv)], MX_A,
                         False))

_REF = {"S": False, "V": False}
_FULL = {"S": True, "V": True}
t_ref = run_pipe(_REF)
t_full = run_pipe(_FULL)
t_s = run_pipe({"S": True, "V": False})
t_v = run_pipe({"S": False, "V": True})

acc_ref = sum(ok(t, g) for t, g in zip(t_ref, tg)) / len(tg)
acc_full = sum(ok(t, g) for t, g in zip(t_full, tg)) / len(tg)
acc_s = sum(ok(t, g) for t, g in zip(t_s, tg)) / len(tg)
acc_v = sum(ok(t, g) for t, g in zip(t_v, tg)) / len(tg)
print(f"  base acc={acc_ref:.4f} | co-train(SV) acc={acc_full:.4f} "
      f"gain={acc_full - acc_ref:+.4f}", flush=True)
print(f"  solo: S={acc_s:.4f} (gain {acc_s - acc_ref:+.4f}) | "
      f"V={acc_v:.4f} (gain {acc_v - acc_ref:+.4f}) | "
      f"A=base (frozen)={acc_ref:.4f}", flush=True)

ADAPTER = "/kaggle/working/adapter"
model.save_pretrained(ADAPTER)
tok.save_pretrained(ADAPTER)
out = {"n_train": n, "K": K, "OUTER": OUTER, "E": E,
       "lr": LR, "eps": EPS, "beta": BETA, "temp": TEMP,
       "beta_s": BETA_S, "beta_v": BETA_V, "seed": SEED, "hist": hist,
       "quick_eval": {"acc_ref": acc_ref, "acc_full": acc_full,
                      "gain": acc_full - acc_ref,
                      "solo": {"S": acc_s, "V": acc_v, "A": "base_frozen"}},
       "seconds": round(time.time() - t0, 1)}
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
print("SUMMARY", json.dumps({"quick_eval": out["quick_eval"],
                             "hist_tail": hist[-5:] if hist else []}), flush=True)
print(f"adapter -> {ADAPTER}", flush=True)
print("done", flush=True)