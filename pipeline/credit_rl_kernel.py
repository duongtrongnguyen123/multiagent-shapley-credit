# Credit-sharing RL — kernel TỔNG QUÁT cho cả 4 vai P / S / V / A trên GSM8K train.
# reward của 1 trace = ĐÓNG GÓP BIÊN (Shapley marginal) của vai đó trong coalition,
# nhóm 8 marginal normalize theo câu -> GRPO group advantage.
#
# Ma trận 16 coalition của pipeline P->S->V->A được rollout DÙNG CHUNG stage (15 forward
# call / câu): 1 plan + 2 solver + 4 verifier + 8 aggregator. Với mỗi vai R, reward của
# trace = v(S∪{R}) − v(S) cho S ⊆ {3 vai còn lại}; trace được LoRA-train, 3 vai kia chạy
# base (adapter tắt). Shapley: Σ marginal = v(full) − v(∅), v(∅)=v({P})=0.
#
# Tối ưu: 7 stage KHÔNG phụ thuộc vai đang train được precompute 1 lần cho toàn pool
# (base model); mỗi outer loop chỉ rollout lại vai R (LoRA sampling) + 7 stage downstream
# phụ thuộc nó (base) = 8 gen call / outer / câu.
#
# Inner loop: multi-epoch PPO (ratio clip + importance sampling + KL vs base = π_ref).
# Outer loop rollout lại bằng policy hiện tại -> reward bám theo năng lực (non-stationarity).
# Guardrail H23: eval nhẹ cuối kernel ghi acc/intervention/fix/break/copy.
# Dữ liệu: GSM8K main_train.csv (train pool), eval CHỈ main_test.csv (không rò rỉ).
import os, re, csv, json, glob, math, random, contextlib, subprocess, sys, time

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# ---- config (patched by orchestrate_credit_rl.py) ----------------------------
ROLE       = __ROLE__          # "P" | "S" | "V" | "A" — vai được LoRA train
TASK       = __TASK__          # "gsm8k" | "math" — tập train/eval
N_TRAIN    = __N_TRAIN__       # số câu train làm pool
K          = __K__             # câu/outer loop
OUTER      = __OUTER__         # số vòng ngoài (rollout + credit recompute)
E          = __E__             # số epoch inner (multi-epoch PPO)
LR         = __LR__
EPS        = __EPS__           # PPO ratio clip
BETA       = __BETA__          # hệ số KL vs π_ref
TEMP       = __TEMP__          # nhiệt độ sampling khi rollout vai train (exploration)
SEED       = __SEED__
BS         = __BS__            # batch sinh
MB         = __MB__            # mini-batch PPO (số sample/step)
MAXLEN     = __MAXLEN__
ONLY_VERIFY = __ONLY_VERIFY__  # (chỉ áp dụng cho V) 1: chỉ train context KIỂM (S có mặt)
COND        = __COND__         # (chỉ áp dụng cho V) 1: reward có điều kiện (fix/keep/break) thay vì marginal
PLAN_MINLEN = __PLAN_MINLEN__  # (chỉ áp dụng cho P) plan tối thiểu (char), 0 = tắt penalty
PLAN_LAMBDA = __PLAN_LAMBDA__  # (chỉ áp dụng cho P) phạt mỗi char thiếu hụt so với MINLEN
A_SELECT    = __A_SELECT__     # (chỉ áp dụng cho A) 1: selection constraint (trả chỉ số) + reward conditional

assert ROLE in ("P", "S", "V", "A"), f"ROLE={ROLE} khong hop le"
assert TASK in ("gsm8k", "math"), f"TASK={TASK}"
if COND:
    assert ROLE == "V", "COND chi ap dung cho V"
if PLAN_MINLEN:
    assert ROLE == "P", "PLAN_MINLEN chi ap dung cho P"
if A_SELECT:
    assert ROLE == "A", "A_SELECT chi ap dung cho A"

# ---- debug: in cây /kaggle/input sớm nhất có thể (log rỗng = crash ở đây) ----
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

# model định vị bằng model.safetensors — giống mọi kernel đã chạy được
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
model = AutoModelForCausalLM.from_pretrained(MODEL_DIR, torch_dtype=torch.float16,
                                             device_map={"": 0})
model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                         bias="none", task_type="CAUSAL_LM",
                                         target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]))
model.config.use_cache = True
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
print(f"LoRA on {ROLE}; trainable tensors: "
      f"{sum(1 for n,p in model.named_parameters() if p.requires_grad)}", flush=True)

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
# Selection constraint: A chỉ được trả về CHỈ SỐ của ứng viên đúng, không viết tự do
AGG_SYS_SEL = ("You are given a math problem and two candidate solutions. Determine which "
               "candidate gives the correct final answer. Output ONLY the number of the "
               "correct candidate: '1' or '2'. No explanation.")

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

def agg_sel_user(q, c1, c2):
    return agg_user(q, [c1, c2])

SEL_RE = re.compile(r"\b([12])\b")
def select_idx(text):
    """Trích chỉ số ứng viên A chọn từ output selection constraint."""
    if not text:
        return None
    m = SEL_RE.search(text)
    return int(m.group(1)) if m else None

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

@contextlib.contextmanager
def _null():
    yield

def gen(prompts, mx, use_lora, do_sample=False, temp=1.0):
    """Sinh văn bản; use_lora=False -> chạy base (adapter tắt) cho vai không train.
    Trả (outs, pids, rids): pids/rids để tính logp khi training."""
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

def logp(pid, rid, use_lora, grad=False):
    """Per-token log-prob của trace (rid) sau prompt (pid), có/không adapter.
    Chunk theo sequence để tránh peak fp32 (logits fp16 [T,V] -> float() cả khối gây OOM
    trên T4 16GB; T lên tới ~1500 token x vocab 152k)."""
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
        chunk = lg[s:e].float() - lse                               # [CH,V] fp32 (nhỏ)
        idx = full[0, s + 1:e + 1].unsqueeze(1)
        lp.append(chunk.gather(1, idx).squeeze(1))
    lp = torch.cat(lp)                                   # [T-1]
    return lp[pl - 1: pl - 1 + len(rid)]                 # [len(rid)]

# ---- dữ liệu: pool train (gsm8k main_train.csv | math MATH/train/**/*.json) -----
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
print(f"pool train {n} cau | ROLE={ROLE} TASK={TASK}", flush=True)

# ==============================================================================
# Stage helper: trả đúng prompt cho từng stage của pipeline chia sẻ
# ==============================================================================
def p_plan(q):  return chat(PLAN_SYS, q)
def s_np(q):    return chat(SOLVE_SYS, q)
def s_wp(q, pl): return chat(SOLVE_SYS, with_plan(q, pl))
def v_fnp(q):   return chat(SOLVE_SYS, q)                                   # V tự giải, no plan
def v_fwp(q, pl): return chat(SOLVE_SYS, with_plan(q, pl))                  # V tự giải, có plan
def v_vnp(q, sol): return chat(VERIFY_SYS, verify_user(q, sol))             # V verify sol_np
def v_vwp(q, sol): return chat(VERIFY_SYS, verify_user(q, sol))             # V verify sol_wp
def a_f(q):     return chat(SOLVE_SYS, q)                                   # A tự giải
def a_fp(q, pl): return chat(SOLVE_SYS, with_plan(q, pl))                   # A tự giải, có plan
def a_snp(q, sol): return chat(AGG_SYS, agg_user(q, [sol]))
def a_swp(q, sol): return chat(AGG_SYS, agg_user(q, [sol]))
def a_vfnp(q, v):  return chat(AGG_SYS, agg_user(q, [v]))
def a_vfwp(q, v):  return chat(AGG_SYS, agg_user(q, [v]))
def a_svnp(q, sol, v): return chat(AGG_SYS_SEL if A_SELECT else AGG_SYS, agg_sel_user(q, sol, v))
def a_svwp(q, sol, v): return chat(AGG_SYS_SEL if A_SELECT else AGG_SYS, agg_sel_user(q, sol, v))

MX_P, MX_S, MX_V, MX_A = 256, 512, 512, 256

# ==============================================================================
# Precompute 7 stage KHÔNG phụ thuộc vai đang train (base model, 1 lần cho pool)
# ==============================================================================
print(f"[{ROLE}] precompute base stages (7 khong phu thuoc {ROLE})...", flush=True)
PRE = {}
if ROLE == "P":
    # P không train: plan cần rollout mỗi loop. Precompute các stage không cần plan.
    PRE["sol_np"] = text_only(gen([s_np(q) for q in qs], MX_S, False))
    PRE["v_fnp"]  = text_only(gen([v_fnp(q) for q in qs], MX_V, False))
    PRE["v_vnp"]  = text_only(gen([v_vnp(q, s) for q, s in zip(qs, PRE["sol_np"])], MX_V, False))
    PRE["a_f"]    = text_only(gen([a_f(q) for q in qs], MX_A, False))
    PRE["a_snp"]  = text_only(gen([a_snp(q, s) for q, s in zip(qs, PRE["sol_np"])], MX_A, False))
    PRE["a_vfnp"] = text_only(gen([a_vfnp(q, v) for q, v in zip(qs, PRE["v_fnp"])], MX_A, False))
    PRE["a_svnp"] = text_only(gen([a_svnp(q, s, v) for q, s, v in
                                   zip(qs, PRE["sol_np"], PRE["v_vnp"])], MX_A, False))
elif ROLE == "S":
    PRE["plan"]   = text_only(gen([p_plan(q) for q in qs], MX_P, False))
    PRE["v_fnp"]  = text_only(gen([v_fnp(q) for q in qs], MX_V, False))
    PRE["v_fwp"]  = text_only(gen([v_fwp(q, p) for q, p in zip(qs, PRE["plan"])], MX_V, False))
    PRE["a_f"]    = text_only(gen([a_f(q) for q in qs], MX_A, False))
    PRE["a_fp"]   = text_only(gen([a_fp(q, p) for q, p in zip(qs, PRE["plan"])], MX_A, False))
    PRE["a_vfnp"] = text_only(gen([a_vfnp(q, v) for q, v in zip(qs, PRE["v_fnp"])], MX_A, False))
    PRE["a_vfwp"] = text_only(gen([a_vfwp(q, v) for q, v in zip(qs, PRE["v_fwp"])], MX_A, False))
elif ROLE == "V":
    PRE["plan"]   = text_only(gen([p_plan(q) for q in qs], MX_P, False))
    PRE["sol_np"] = text_only(gen([s_np(q) for q in qs], MX_S, False))
    PRE["sol_wp"] = text_only(gen([s_wp(q, p) for q, p in zip(qs, PRE["plan"])], MX_S, False))
    PRE["a_f"]    = text_only(gen([a_f(q) for q in qs], MX_A, False))
    PRE["a_fp"]   = text_only(gen([a_fp(q, p) for q, p in zip(qs, PRE["plan"])], MX_A, False))
    PRE["a_snp"]  = text_only(gen([a_snp(q, s) for q, s in zip(qs, PRE["sol_np"])], MX_A, False))
    PRE["a_swp"]  = text_only(gen([a_swp(q, s) for q, s in zip(qs, PRE["sol_wp"])], MX_A, False))
elif ROLE == "A":
    PRE["plan"]   = text_only(gen([p_plan(q) for q in qs], MX_P, False))
    PRE["sol_np"] = text_only(gen([s_np(q) for q in qs], MX_S, False))
    PRE["sol_wp"] = text_only(gen([s_wp(q, p) for q, p in zip(qs, PRE["plan"])], MX_S, False))
    PRE["v_fnp"]  = text_only(gen([v_fnp(q) for q in qs], MX_V, False))
    PRE["v_fwp"]  = text_only(gen([v_fwp(q, p) for q, p in zip(qs, PRE["plan"])], MX_V, False))
    PRE["v_vnp"]  = text_only(gen([v_vnp(q, s) for q, s in zip(qs, PRE["sol_np"])], MX_V, False))
    PRE["v_vwp"]  = text_only(gen([v_vwp(q, s) for q, s in zip(qs, PRE["sol_wp"])], MX_V, False))
print(f"[{ROLE}] precompute xong", flush=True)
torch.cuda.empty_cache()

# ==============================================================================
# Vòng ngoài: rollout vai R (LoRA sampling) + downstream (base), 8 marginal/outer
# ==============================================================================
t0 = time.time()
hist = []
for outer in range(OUTER):
    model.eval()
    idxs = random.sample(range(n), min(K, n))
    S_ = lambda i: PRE.get("sol_np", [None] * len(idxs))[i]   # sol không-plan (base cố định)
    W_ = lambda i: PRE.get("sol_wp", [None] * len(idxs))[i]   # sol có-plan (base cố định)

    # stage text cho outer này: bắt đầu từ PRE (base cố định), ghi đè trace train + downstream
    ST = {k: v for k, v in PRE.items()}

    # ---- rollout vai đang train (LoRA, sampling) ----
    TR = {}   # pid/rid của trace vai train (để tính logp + PPO)
    if ROLE == "P":
        pl_t, TR["pid"], TR["rid"] = gen([p_plan(qs[i]) for i in idxs], MX_P, True,
                                         do_sample=TEMP > 0, temp=TEMP)
        ST["plan"] = pl_t
        # downstream phụ thuộc plan
        ST["sol_wp"] = text_only(gen([s_wp(qs[i], pl_t[j]) for j, i in enumerate(idxs)],
                                     MX_S, False))
        ST["v_fwp"]  = text_only(gen([v_fwp(qs[i], pl_t[j]) for j, i in enumerate(idxs)],
                                     MX_V, False))
        ST["a_fp"]   = text_only(gen([a_fp(qs[i], pl_t[j]) for j, i in enumerate(idxs)],
                                     MX_A, False))
        ST["v_vwp"]  = text_only(gen([v_vwp(qs[i], ST["sol_wp"][j]) for j, i in enumerate(idxs)],
                                     MX_V, False))
        ST["a_swp"]  = text_only(gen([a_swp(qs[i], ST["sol_wp"][j]) for j, i in enumerate(idxs)],
                                     MX_A, False))
        ST["a_vfwp"] = text_only(gen([a_vfwp(qs[i], ST["v_fwp"][j]) for j, i in enumerate(idxs)],
                                     MX_A, False))
        ST["a_svwp"] = text_only(gen([a_svwp(qs[i], ST["sol_wp"][j], ST["v_vwp"][j])
                                      for j, i in enumerate(idxs)], MX_A, False))
    elif ROLE == "S":
        s0, s0p, s0r = gen([s_np(qs[i]) for i in idxs], MX_S, True, do_sample=TEMP > 0, temp=TEMP)
        s1, s1p, s1r = gen([s_wp(qs[i], PRE["plan"][i]) for i in idxs], MX_S, True,
                           do_sample=TEMP > 0, temp=TEMP)
        ST["sol_np"], TR["pid0"], TR["rid0"] = s0, s0p, s0r
        ST["sol_wp"], TR["pid1"], TR["rid1"] = s1, s1p, s1r
        # downstream phụ thuộc sol
        ST["v_vnp"] = text_only(gen([v_vnp(qs[i], s0[j]) for j, i in enumerate(idxs)], MX_V, False))
        ST["v_vwp"] = text_only(gen([v_vwp(qs[i], s1[j]) for j, i in enumerate(idxs)], MX_V, False))
        ST["a_snp"] = text_only(gen([a_snp(qs[i], s0[j]) for j, i in enumerate(idxs)], MX_A, False))
        ST["a_swp"] = text_only(gen([a_swp(qs[i], s1[j]) for j, i in enumerate(idxs)], MX_A, False))
        ST["a_svnp"] = text_only(gen([a_svnp(qs[i], s0[j], ST["v_vnp"][j])
                                      for j, i in enumerate(idxs)], MX_A, False))
        ST["a_svwp"] = text_only(gen([a_svwp(qs[i], s1[j], ST["v_vwp"][j])
                                      for j, i in enumerate(idxs)], MX_A, False))
    elif ROLE == "V":
        v0, v0p, v0r = gen([v_fnp(qs[i]) for i in idxs], MX_V, True, do_sample=TEMP > 0, temp=TEMP)
        v1, v1p, v1r = gen([v_fwp(qs[i], PRE["plan"][i]) for i in idxs], MX_V, True,
                           do_sample=TEMP > 0, temp=TEMP)
        v2, v2p, v2r = gen([v_vnp(qs[i], S_(i)) for i in idxs], MX_V, True,
                           do_sample=TEMP > 0, temp=TEMP)
        v3, v3p, v3r = gen([v_vwp(qs[i], W_(i)) for i in idxs], MX_V, True,
                           do_sample=TEMP > 0, temp=TEMP)
        ST["v_fnp"], TR["pid0"], TR["rid0"] = v0, v0p, v0r
        ST["v_fwp"], TR["pid1"], TR["rid1"] = v1, v1p, v1r
        ST["v_vnp"], TR["pid2"], TR["rid2"] = v2, v2p, v2r
        ST["v_vwp"], TR["pid3"], TR["rid3"] = v3, v3p, v3r
        # downstream phụ thuộc V (chỉ cần khi reward là marginal)
        if not COND:
            ST["a_vfnp"] = text_only(gen([a_vfnp(qs[i], v0[j]) for j, i in enumerate(idxs)],
                                         MX_A, False))
            ST["a_vfwp"] = text_only(gen([a_vfwp(qs[i], v1[j]) for j, i in enumerate(idxs)],
                                         MX_A, False))
            ST["a_svnp"] = text_only(gen([a_svnp(qs[i], S_(i), v2[j]) for j, i in enumerate(idxs)],
                                         MX_A, False))
            ST["a_svwp"] = text_only(gen([a_svwp(qs[i], W_(i), v3[j]) for j, i in enumerate(idxs)],
                                         MX_A, False))
    elif ROLE == "A":
        if A_SELECT:
            # A_SELECT: chỉ train 2 trace selection thật sự (2 candidate: sol + verifier).
            # a_f/a_fp/a_snp/a_swp/a_vfnp/a_vfwp chỉ có 1 candidate -> selection vô nghĩa.
            a6, a6p, a6r = gen([a_svnp(qs[i], S_(i), PRE["v_vnp"][i]) for i in idxs], MX_A, True,
                               do_sample=TEMP > 0, temp=TEMP)
            a7, a7p, a7r = gen([a_svwp(qs[i], W_(i), PRE["v_vwp"][i]) for i in idxs], MX_A, True,
                               do_sample=TEMP > 0, temp=TEMP)
            ST["a_svnp"], TR["pid6"], TR["rid6"] = a6, a6p, a6r
            ST["a_svwp"], TR["pid7"], TR["rid7"] = a7, a7p, a7r
        else:
            # 8 trace A (LoRA) — A là vai cuối nên không có downstream
            a0, a0p, a0r = gen([a_f(qs[i]) for i in idxs], MX_A, True, do_sample=TEMP > 0, temp=TEMP)
            a1, a1p, a1r = gen([a_fp(qs[i], PRE["plan"][i]) for i in idxs], MX_A, True,
                               do_sample=TEMP > 0, temp=TEMP)
            a2, a2p, a2r = gen([a_snp(qs[i], S_(i)) for i in idxs], MX_A, True, do_sample=TEMP > 0, temp=TEMP)
            a3, a3p, a3r = gen([a_swp(qs[i], W_(i)) for i in idxs], MX_A, True, do_sample=TEMP > 0, temp=TEMP)
            a4, a4p, a4r = gen([a_vfnp(qs[i], PRE["v_fnp"][i]) for i in idxs], MX_A, True,
                               do_sample=TEMP > 0, temp=TEMP)
            a5, a5p, a5r = gen([a_vfwp(qs[i], PRE["v_fwp"][i]) for i in idxs], MX_A, True,
                               do_sample=TEMP > 0, temp=TEMP)
            a6, a6p, a6r = gen([a_svnp(qs[i], S_(i), PRE["v_vnp"][i]) for i in idxs], MX_A, True,
                               do_sample=TEMP > 0, temp=TEMP)
            a7, a7p, a7r = gen([a_svwp(qs[i], W_(i), PRE["v_vwp"][i]) for i in idxs], MX_A, True,
                               do_sample=TEMP > 0, temp=TEMP)
            for j, (t, pid, rid) in enumerate(
                    [(a0, a0p, a0r), (a1, a1p, a1r), (a2, a2p, a2r), (a3, a3p, a3r),
                     (a4, a4p, a4r), (a5, a5p, a5r), (a6, a6p, a6r), (a7, a7p, a7r)]):
                ST[f"a{j}"] = t
                TR[f"pid{j}"], TR[f"rid{j}"] = pid, rid
            ST["a_f"], ST["a_fp"] = a0, a1
            ST["a_snp"], ST["a_swp"] = a2, a3
            ST["a_vfnp"], ST["a_vfwp"] = a4, a5
            ST["a_svnp"], ST["a_svwp"] = a6, a7

    G = lambda name, i: ST[name][i]

    # ---- reward: COND (có điều kiện) nếu bật, ngược lại Shapley marginal ----
    if ROLE == "V" and COND:
        # reward có điều kiện cho V (mã hóa "sửa khi sai, giữ khi đúng"):
        #   fix : base sai & V đúng  -> +1.0
        #   noop: base sai & V sai   ->  0.0
        #   copy: base đúng & V đúng -> +0.1  (không can thiệp thừa)
        #   break: base đúng & V sai -> −2.0  (phạt nặng)
        def cond_r(base_ok, v_ok):
            if not base_ok and v_ok:   return 1.0
            if not base_ok and not v_ok: return 0.0
            if base_ok and v_ok:        return 0.1
            return -2.0
        REW = {
            # v_fnp / v_fwp: base = ∅ / {P} (không ra đáp án) -> luôn base sai
            "pid0": [cond_r(False, ok(G("v_fnp", j), gs[i])) for j, i in enumerate(idxs)],
            "pid1": [cond_r(False, ok(G("v_fwp", j), gs[i])) for j, i in enumerate(idxs)],
            # v_vnp / v_vwp: base = sol_np / sol_wp
            "pid2": [cond_r(ok(G("sol_np", j), gs[i]), ok(G("v_vnp", j), gs[i])) for j, i in enumerate(idxs)],
            "pid3": [cond_r(ok(G("sol_wp", j), gs[i]), ok(G("v_vwp", j), gs[i])) for j, i in enumerate(idxs)],
        }
        samples = []
        for t in range(len(idxs)):
            keys = ["pid0", "pid1", "pid2", "pid3"] if not ONLY_VERIFY else ["pid2", "pid3"]
            grp = [REW[k][t] for k in keys]
            mean = sum(grp) / len(grp)
            std = (sum((x - mean) ** 2 for x in grp) / len(grp)) ** 0.5
            sd = max(std, 1e-4)
            for k in keys:
                samples.append({"pid": TR[k][t], "rid": TR[k.replace("pid", "rid")][t],
                                "advs": [(REW[k][t] - mean) / sd]})
        # stats cho log: mean reward + phân loại fix/copy/noop/break của 2 trace verify
        _r2, _r3 = REW["pid2"], REW["pid3"]
        _n_fix = sum(1 for x, y in zip(_r2, _r3) if x == 1.0 or y == 1.0)
        _n_break = sum(1 for x, y in zip(_r2, _r3) if x == -2.0 or y == -2.0)
        _n_copy = sum(1 for x, y in zip(_r2, _r3) if x == 0.1 or y == 0.1)
        _n_noop = sum(1 for x, y in zip(_r2, _r3) if x == 0.0 and y == 0.0)
    elif ROLE == "A" and A_SELECT:
        # reward selection constraint cho A: trả CHỈ SỐ ứng viên đúng (1 hoặc 2).
        #   có ứng viên đúng trong 2?  A chọn đúng?    reward
        #   yes                        yes             +1.0
        #   yes                        no              −1.0
        #   no                         (bất kỳ)         0.0
        # Ứng viên: a_svnp = (sol_np, v_vnp); a_svwp = (sol_wp, v_vwp).
        def sel_reward(c1, c2, sel_text, g):
            has = ok(c1, g) or ok(c2, g)
            if not has:
                return 0.0
            idx = select_idx(sel_text)
            if idx is None:
                return -1.0
            return 1.0 if (idx == 1 and ok(c1, g)) or (idx == 2 and ok(c2, g)) else -1.0
        REW = {
            "pid6": [sel_reward(G("sol_np", j), G("v_vnp", j), G("a_svnp", j), gs[i])
                     for j, i in enumerate(idxs)],
            "pid7": [sel_reward(G("sol_wp", j), G("v_vwp", j), G("a_svwp", j), gs[i])
                     for j, i in enumerate(idxs)],
        }
        samples = []
        for t in range(len(idxs)):
            keys = ["pid6", "pid7"]
            grp = [REW[k][t] for k in keys]
            mean = sum(grp) / len(grp)
            std = (sum((x - mean) ** 2 for x in grp) / len(grp)) ** 0.5
            sd = max(std, 1e-4)
            for k in keys:
                samples.append({"pid": TR[k][t], "rid": TR[k.replace("pid", "rid")][t],
                                "advs": [(REW[k][t] - mean) / sd]})
        _r6, _r7 = REW["pid6"], REW["pid7"]
        _n_sel_ok = sum(1 for x in _r6 + _r7 if x == 1.0)
        _n_sel_bad = sum(1 for x in _r6 + _r7 if x == -1.0)
        _n_sel_none = sum(1 for x in _r6 + _r7 if x == 0.0)
        _n_sel_parse = sum(1 for x, c1, c2, g in
                           ((G("a_svnp", j), G("sol_np", j), G("v_vnp", j), gs[i])
                            for j, i in enumerate(idxs)) if select_idx(x) is not None) + \
                       sum(1 for x, c1, c2, g in
                           ((G("a_svwp", j), G("sol_wp", j), G("v_vwp", j), gs[i])
                            for j, i in enumerate(idxs)) if select_idx(x) is not None)
    else:
        # ---- 16 giá trị v(S) cho mỗi câu (0/1) ----
        vP   = [0.0] * len(idxs)                      # v({P}) = 0 (plan không ra đáp án)
        vS   = [ok(G("sol_np", j), gs[i]) for j, i in enumerate(idxs)]
        vV   = [ok(G("v_fnp", j), gs[i]) for j, i in enumerate(idxs)]
        vA   = [ok(G("a_f", j), gs[i]) for j, i in enumerate(idxs)]
        vPS  = [ok(G("sol_wp", j), gs[i]) for j, i in enumerate(idxs)]
        vPV  = [ok(G("v_fwp", j), gs[i]) for j, i in enumerate(idxs)]
        vPA  = [ok(G("a_fp", j), gs[i]) for j, i in enumerate(idxs)]
        vSV  = [ok(G("v_vnp", j), gs[i]) for j, i in enumerate(idxs)]
        vSA  = [ok(G("a_snp", j), gs[i]) for j, i in enumerate(idxs)]
        vVA  = [ok(G("a_vfnp", j), gs[i]) for j, i in enumerate(idxs)]
        vPSV = [ok(G("v_vwp", j), gs[i]) for j, i in enumerate(idxs)]
        vPSA = [ok(G("a_swp", j), gs[i]) for j, i in enumerate(idxs)]
        vPVA = [ok(G("a_vfwp", j), gs[i]) for j, i in enumerate(idxs)]
        vSVA = [ok(G("a_svnp", j), gs[i]) for j, i in enumerate(idxs)]
        vPSVA = [ok(G("a_svwp", j), gs[i]) for j, i in enumerate(idxs)]

        # ---- 8 marginal của vai R (theo từng coalition) ----
        # m_k = v(C_k ∪ {R}) − v(C_k), C_k là 8 subset của 3 vai còn lại
        if ROLE == "P":
            # C: {∅},{S},{V},{S,V},{A},{S,A},{V,A},{S,V,A}
            M = [
                [vP[j] - 0.0 for j in range(len(idxs))],
                [vPS[j] - vS[j] for j in range(len(idxs))],
                [vPV[j] - vV[j] for j in range(len(idxs))],
                [vPSV[j] - vSV[j] for j in range(len(idxs))],
                [vPA[j] - vA[j] for j in range(len(idxs))],
                [vPSA[j] - vSA[j] for j in range(len(idxs))],
                [vPVA[j] - vVA[j] for j in range(len(idxs))],
                [vPSVA[j] - vSVA[j] for j in range(len(idxs))],
            ]
        elif ROLE == "S":
            # C: {∅},{P},{V},{P,V},{A},{P,A},{V,A},{P,V,A}
            M = [
                [vS[j] - 0.0 for j in range(len(idxs))],
                [vPS[j] - vP[j] for j in range(len(idxs))],
                [vSV[j] - vV[j] for j in range(len(idxs))],
                [vPSV[j] - vPV[j] for j in range(len(idxs))],
                [vSA[j] - vA[j] for j in range(len(idxs))],
                [vPSA[j] - vPA[j] for j in range(len(idxs))],
                [vSVA[j] - vVA[j] for j in range(len(idxs))],
                [vPSVA[j] - vPVA[j] for j in range(len(idxs))],
            ]
        elif ROLE == "V":
            # C: {∅},{P},{S},{P,S},{A},{P,A},{S,A},{P,S,A}
            M = [
                [vV[j] - 0.0 for j in range(len(idxs))],
                [vPV[j] - vP[j] for j in range(len(idxs))],
                [vSV[j] - vS[j] for j in range(len(idxs))],
                [vPSV[j] - vPS[j] for j in range(len(idxs))],
                [vVA[j] - vA[j] for j in range(len(idxs))],
                [vPVA[j] - vPA[j] for j in range(len(idxs))],
                [vSVA[j] - vSA[j] for j in range(len(idxs))],
                [vPSVA[j] - vPSA[j] for j in range(len(idxs))],
            ]
        elif ROLE == "A":
            # C: {∅},{P},{S},{P,S},{V},{P,V},{S,V},{P,S,V}
            M = [
                [vA[j] - 0.0 for j in range(len(idxs))],
                [vPA[j] - vP[j] for j in range(len(idxs))],
                [vSA[j] - vS[j] for j in range(len(idxs))],
                [vPSA[j] - vPS[j] for j in range(len(idxs))],
                [vVA[j] - vV[j] for j in range(len(idxs))],
                [vPVA[j] - vPV[j] for j in range(len(idxs))],
                [vSVA[j] - vSV[j] for j in range(len(idxs))],
                [vPSVA[j] - vPSV[j] for j in range(len(idxs))],
            ]

        # ---- P: phạt plan quá ngắn/rỗng (chống reward hacking: policy "an toàn" = plan rỗng)
        #      trừ penalty vào mọi marginal của câu có plan thiếu độ dài MINLEN ----
        if ROLE == "P" and PLAN_MINLEN:
            for t in range(len(idxs)):
                pen = PLAN_LAMBDA * max(0, PLAN_MINLEN - len(ST["plan"][t]))
                for k in range(8):
                    M[k][t] = M[k][t] - pen

        # ---- group advantage per câu (GRPO); trace vai R gán theo coalition ----
        samples = []
        for t in range(len(idxs)):
            grp = [M[k][t] for k in range(8)] if not (ROLE == "V" and ONLY_VERIFY) \
                  else [M[2][t], M[3][t], M[6][t], M[7][t]]
            mean = sum(grp) / len(grp)
            std = (sum((x - mean) ** 2 for x in grp) / len(grp)) ** 0.5
            sd = max(std, 1e-4)
            adv = lambda x: (x - mean) / sd
            a = [adv(M[k][t]) for k in range(8)]
            if ROLE == "P":
                samples.append({"pid": TR["pid"][t], "rid": TR["rid"][t], "advs": a})
            elif ROLE == "S":
                samples.append({"pid": TR["pid0"][t], "rid": TR["rid0"][t], "advs": [a[0], a[2], a[4], a[6]]})
                samples.append({"pid": TR["pid1"][t], "rid": TR["rid1"][t], "advs": [a[1], a[3], a[5], a[7]]})
            elif ROLE == "V":
                if ONLY_VERIFY:
                    samples.append({"pid": TR["pid2"][t], "rid": TR["rid2"][t], "advs": [a[2], a[6]]})
                    samples.append({"pid": TR["pid3"][t], "rid": TR["rid3"][t], "advs": [a[3], a[7]]})
                else:
                    samples.append({"pid": TR["pid0"][t], "rid": TR["rid0"][t], "advs": [a[0], a[4]]})
                    samples.append({"pid": TR["pid1"][t], "rid": TR["rid1"][t], "advs": [a[1], a[5]]})
                    samples.append({"pid": TR["pid2"][t], "rid": TR["rid2"][t], "advs": [a[2], a[6]]})
                    samples.append({"pid": TR["pid3"][t], "rid": TR["rid3"][t], "advs": [a[3], a[7]]})
            elif ROLE == "A":
                for k in range(8):
                    samples.append({"pid": TR[f"pid{k}"][t], "rid": TR[f"rid{k}"][t], "advs": [a[k]]})

    # ---- logp_old (policy rollout) & logp_ref (base) — cache trước update ----
    torch.cuda.empty_cache()
    for s in samples:
        s["lp_old"] = logp(s["pid"], s["rid"], use_lora=True, grad=False).detach()
        s["lp_ref"] = logp(s["pid"], s["rid"], use_lora=False, grad=False).detach()
    torch.cuda.empty_cache()

    # ---- inner loop: multi-epoch PPO (clip + IS + KL); backward từng sample
    #      để chỉ 1 autograd graph sống (tránh OOM: logits [T,V] fp16 ~ 456MB/graph) ----
    model.train()
    for ep in range(E):
        random.shuffle(samples)
        for b in range(0, len(samples), MB):
            batch = samples[b:b + MB]
            opt.zero_grad()
            for s in batch:
                lp = logp(s["pid"], s["rid"], use_lora=True, grad=True)
                ratio = torch.exp(lp - s["lp_old"])
                rc = torch.clamp(ratio, 1 - EPS, 1 + EPS)
                surr = torch.zeros_like(ratio)
                for advv in s["advs"]:
                    surr = surr + torch.min(ratio * advv, rc * advv)
                surr = surr / len(s["advs"])
                kl = torch.exp(s["lp_ref"] - lp) - (s["lp_ref"] - lp) - 1.0
                loss_s = (-surr.mean() + BETA * kl.mean()) / len(batch)
                loss_s.backward()
                del lp
                torch.cuda.empty_cache()
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad], 1.0)
            opt.step()
    model.eval()

    # ---- log ----
    el = time.time() - t0
    if ROLE == "V" and COND:
        hist.append({"outer": outer + 1, "mean_reward": round(
            (sum(REW["pid0"]) + sum(REW["pid1"]) + sum(REW["pid2"]) + sum(REW["pid3"]))
            / (4 * len(idxs)), 4),
            "n_fix": _n_fix, "n_break": _n_break, "n_copy": _n_copy, "n_noop": _n_noop,
            "samples": len(samples), "seconds": round(el, 1)})
        print(f"[{ROLE} outer {outer+1}/{OUTER}] mean_reward={hist[-1]['mean_reward']:+.4f} "
              f"fix={_n_fix} break={_n_break} copy={_n_copy} noop={_n_noop} "
              f"samples={len(samples)} elapsed={el/60:.1f}m", flush=True)
    elif ROLE == "A" and A_SELECT:
        mean_rew = (sum(REW["pid6"]) + sum(REW["pid7"])) / (2 * len(idxs))
        hist.append({"outer": outer + 1, "mean_reward": round(mean_rew, 4),
                     "n_sel_ok": _n_sel_ok, "n_sel_bad": _n_sel_bad, "n_sel_none": _n_sel_none,
                     "n_sel_parse": _n_sel_parse, "samples": len(samples),
                     "seconds": round(el, 1)})
        print(f"[{ROLE} outer {outer+1}/{OUTER}] mean_reward={mean_rew:+.4f} "
              f"sel_ok={_n_sel_ok} sel_bad={_n_sel_bad} none={_n_sel_none} parse={_n_sel_parse} "
              f"samples={len(samples)} elapsed={el/60:.1f}m", flush=True)
    else:
        mm = [sum(M[k][t] for k in range(8)) / 8.0 for t in range(len(idxs))]
        mean_marg = sum(mm) / len(mm)
        n_pos = sum(1 for x in mm if x > 0.05)
        extra = {}
        if ROLE == "P":
            plens = [len(ST["plan"][t]) for t in range(len(idxs))]
            extra = {"mean_plan_len": round(sum(plens) / len(plens), 1),
                     "pct_empty_plan": round(100 * sum(1 for p in plens if p == 0) / len(plens), 1)}
        hist.append({"outer": outer + 1, "mean_marginal": round(mean_marg, 4),
                     "pct_pos_marginal": round(100 * n_pos / len(mm), 1),
                     "samples": len(samples), "seconds": round(el, 1), **extra})
        print(f"[{ROLE} outer {outer+1}/{OUTER}] mean_marginal={mean_marg:+.4f} "
              f"pos%={100*n_pos/len(mm):.0f} samples={len(samples)}"
              + (f" plan_len={extra['mean_plan_len']} empty%={extra['pct_empty_plan']}" if ROLE == "P" else "")
              + f" elapsed={el/60:.1f}m", flush=True)
    if (outer + 1) % 5 == 0 or outer == OUTER - 1:
        with open("/kaggle/working/hist.json", "w") as f:
            json.dump(hist, f)

# ==============================================================================
# Eval nhẹ cuối kernel: pipeline chứa vai R, so base vs train trên main_test.csv
# ==============================================================================
print(f"\n== quick eval [{ROLE}] tren test (tach rong train) ==", flush=True)
if TASK == "math":
    trows = list(csv.DictReader(open(TEST_CSV, encoding="utf-8")))[:200]
    tq = [r["Question"].strip() for r in trows]
    tg = [gold_answer(r["Answer"]) for r in trows]
else:
    trows = list(csv.DictReader(open(TEST_CSV, newline="")))[:200]
    tq = [r["question"] for r in trows]
    tg = [gold_answer(r["answer"]) for r in trows]

# pipeline theo vai: so SỐ pipeline chứa vai R chạy base vs chạy vai R đã train
def run_pipe():
    tp  = text_only(gen([p_plan(q) for q in tq], MX_P, False))
    ts1 = text_only(gen([s_wp(q, p) for q, p in zip(tq, tp)], MX_S, False))
    if ROLE == "P":
        tplan_t = text_only(gen([p_plan(q) for q in tq], MX_P, True))
        ts1_t = text_only(gen([s_wp(q, p) for q, p in zip(tq, tplan_t)], MX_S, False))
        return ts1, ts1_t
    if ROLE == "S":
        ts1_t = text_only(gen([s_wp(q, p) for q, p in zip(tq, tp)], MX_S, True))
        return ts1, ts1_t
    if ROLE == "V":
        tv = text_only(gen([v_vwp(q, s) for q, s in zip(tq, ts1)], MX_V, False))
        tv_t = text_only(gen([v_vwp(q, s) for q, s in zip(tq, ts1)], MX_V, True))
        return tv, tv_t
    if ROLE == "A":
        tv = text_only(gen([v_vwp(q, s) for q, s in zip(tq, ts1)], MX_V, False))
        if A_SELECT:
            ta = text_only(gen([a_svwp(q, s, v) for q, s, v in zip(tq, ts1, tv)], MX_A, False))
            ta_t = text_only(gen([a_svwp(q, s, v) for q, s, v in zip(tq, ts1, tv)], MX_A, True))
            return ta, ta_t, ts1, tv
        ta = text_only(gen([a_svwp(q, s, v) for q, s, v in zip(tq, ts1, tv)], MX_A, False))
        ta_t = text_only(gen([a_svwp(q, s, v) for q, s, v in zip(tq, ts1, tv)], MX_A, True))
        return ta, ta_t

if ROLE == "A" and A_SELECT:
    _r = run_pipe()
    t_ref, t_full, t_s1, t_v = _r
    # selection accuracy: tỷ lệ câu A chọn đúng ứng viên (khi có ≥1 ứng viên đúng)
    def sel_acc(sel_list, c1s, c2s, gs_):
        hit = tot = 0
        for sel, c1, c2, g in zip(sel_list, c1s, c2s, gs_):
            if not (ok(c1, g) or ok(c2, g)):
                continue
            tot += 1
            idx = select_idx(sel)
            if idx == 1 and ok(c1, g):
                hit += 1
            elif idx == 2 and ok(c2, g):
                hit += 1
        return hit / tot if tot else 0.0
    acc_ref = sel_acc(t_ref, t_s1, t_v, tg)
    acc_full = sel_acc(t_full, t_s1, t_v, tg)
else:
    t_ref, t_full = run_pipe()
    acc_ref = sum(ok(t, g) for t, g in zip(t_ref, tg)) / len(tg)
    acc_full = sum(ok(t, g) for t, g in zip(t_full, tg)) / len(tg)
print(f"  pipeline base acc={acc_ref:.4f} | train({ROLE}) acc={acc_full:.4f} "
      f"gain={acc_full-acc_ref:+.4f}", flush=True)

ADAPTER = "/kaggle/working/adapter"
model.save_pretrained(ADAPTER)
tok.save_pretrained(ADAPTER)
out = {"role": ROLE, "n_train": n, "K": K, "OUTER": OUTER, "E": E,
       "lr": LR, "eps": EPS, "beta": BETA, "temp": TEMP, "only_verify": ONLY_VERIFY,
       "cond": COND, "plan_minlen": PLAN_MINLEN, "plan_lambda": PLAN_LAMBDA,
       "a_select": A_SELECT,
       "seed": SEED, "hist": hist,
       "quick_eval": {"acc_ref": acc_ref, "acc_train": acc_full,
                      "gain": acc_full - acc_ref},
       "seconds": round(time.time() - t0, 1)}
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
print("SUMMARY", json.dumps({"quick_eval": out["quick_eval"],
                             "hist_tail": hist[-5:] if hist else []}), flush=True)
print(f"adapter -> {ADAPTER}", flush=True)
print("done", flush=True)
