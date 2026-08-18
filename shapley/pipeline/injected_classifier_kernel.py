# H37 — HUẤN LUYỆN BỘ KIỂM LỖI TIÊM, ĐÁNH GIÁ CHUYỂN GIAO LÊN LỖI THẬT.
# Xem docs/PREREGISTRATION.md #43.
#
# RỦI RO CHÍNH: lỗi TIÊM = đổi 1 số trong chuỗi vàng; lỗi THẬT = sai cách tiếp cận.
# Thiết kế BẮT BUỘC: huấn luyện trên TIÊM, đánh giá trên THẬT.
#
#   Huấn luyện: LoRA phân loại nhị phân trên MATH train-half, nhãn tiêm sẵn (clean vs corrupt)
#   Đánh giá A (in-distribution): lỗi TIÊM trên test-half -> discrimination_injected
#   Đánh giá B (CHUYỂN GIAO — chỉ số CHÍNH): lời giải THẬT, nhãn grader -> discrimination_real
#   Đánh giá C (thực tiễn): wvote vs maj@8
#   Mốc: so với bộ chấm H27 (huấn luyện trên lời giải thật)
#
# NGƯỠNG: adapter_leak <= .05 · AUC > .55 · degenerate_rate <= .90
# Solver KHÔNG dính adapter (bài học rò rỉ #59).
import os, re, csv, json, glob, random, subprocess, sys, statistics as st

# torchao/bitsandbytes only needed for 4-bit quant; 1.5B fp16 doesn't need them.
# Kaggle offline mode can't pip install, so skip entirely.

import torch, torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

TASK = "math"  # chỉ MATH (GSM8K chuỗi vàng có <<...>> quá dễ tiêm)
NTR = __NTR__      # số bài train (mỗi bài sinh 1 clean + 1 corrupt = 2*NTR cặp)
NTE = __NTE__      # số bài test
BS = __BS__
MB = __MB__
K = 8
NF = 5
EPOCH = 1
LR = 1e-4
PROBE_N = 60

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True) or \
     glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])

_te = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)
_tr = sorted(glob.glob("/kaggle/input/**/math_500_train.csv", recursive=True), key=len)
if not _tr:
    # MATH-500 has no train split; split test into train-half / test-half
    _all = list(csv.DictReader(open(_te[0])))
    mid = len(_all) // 2
    TRROWS = _all[:mid][:NTR]
    TEROWS = _all[mid:][:NTE]
else:
    TRROWS = list(csv.DictReader(open(_tr[0])))[:NTR]
    TEROWS = list(csv.DictReader(open(_te[0])))[:NTE]

tok = AutoTokenizer.from_pretrained(MODEL)
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="auto")
print(f"MODEL={MODEL} train={len(TRROWS)} test={len(TEROWS)}", flush=True)

# ============ UTILITY ============
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
ANYNUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")

def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0:
        return None
    i = s.find("{", i)
    if i < 0:
        return None
    d, st = 0, i
    for j in range(i, len(s)):
        if s[j] == "{":
            d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0:
                return s[st + 1:j]
    return None

def pred(t):
    b = boxed(t)
    if b is not None:
        return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
    return m[-1].strip() if m else None

def norm(a):
    if a is None:
        return None
    a = str(a).strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " ", ","]:
        a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()

def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g:
        return False
    if p == g:
        return True
    try:
        return abs(float(p) - float(g)) < 1e-6
    except:
        return False

gold_of = lambda r: boxed(r["Answer"])
q_of = lambda r: r["Question"]
gold_chain = lambda r: r["Answer"].strip()

S_SYS = "Solve step by step. Put the final answer in \\boxed{}."
J_SYS = "You judge whether a proposed solution is correct. Answer with one word: Yes or No."

def jprompt(q, s):
    return tok.apply_chat_template(
        [{"role": "system", "content": J_SYS},
         {"role": "user", "content": f"Problem: {q}\n\nProposed solution:\n{s}\n\nIs this solution correct?"}],
        tokenize=False, add_generation_prompt=True)

# ---- Adapter toggle ----
_adapter_active = False

def disable_adapter():
    global _adapter_active
    if _adapter_active:
        try:
            model.disable_adapter_layers()
        except Exception:
            pass
        _adapter_active = False

def enable_adapter():
    global _adapter_active
    if not _adapter_active:
        try:
            model.enable_adapter_layers()
        except Exception:
            pass
        _adapter_active = True

@torch.no_grad()
def gen(sysm, usrs, mx=512, temp=0.0, k=1, use_adapter=False):
    if use_adapter:
        enable_adapter()
    else:
        disable_adapter()
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = [tok.apply_chat_template([{"role": "system", "content": sysm},
                                       {"role": "user", "content": u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to("cuda")
        o = model.generate(**e, max_new_tokens=mx, do_sample=(temp > 0),
                           temperature=max(temp, 1e-5), top_p=0.95,
                           num_return_sequences=k, pad_token_id=tok.pad_token_id)
        torch.cuda.empty_cache()
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(o.shape[0])]
        del e, o
    torch.cuda.empty_cache()
    disable_adapter()
    return outs

# ============ TIÊM LỖI ============
# Đổi MỘT số bất kỳ trong thân bài (trừ \boxed cuối) -> mâu thuẫn nội tại.
random.seed(42)

def corrupt_chain(chain):
    """Đổi 1 số trong thân chuỗi vàng (trước \boxed). Trả (corrupted, tag) hoặc (None, None)."""
    b = chain.rfind("\\boxed")
    body = chain[:b] if b > 0 else chain
    ms = [m for m in ANYNUM.finditer(body)]
    if not ms:
        return None, None
    m = random.choice(ms)
    try:
        val = float(m.group(1))
    except:
        return None, None
    d = random.choice([1, 2, 3, -1, -2]) if abs(val) > 3 else random.choice([1, 2, 3])
    new = val + d
    new = str(int(new)) if float(new).is_integer() else f"{new:g}"
    return chain[:m.start(1)] + new + chain[m.end(1):], f"{m.group(1)}->{new}"

# Tự kiểm regex
_t = r"We have $2 + 3 = 5$ then $5 \times 4 = 20$, so \boxed{20}."
assert len(ANYNUM.findall(_t)) >= 4, f"REGEX HỎNG: {ANYNUM.findall(_t)}"
print("tự kiểm regex: OK", ANYNUM.findall(_t)[:5], flush=True)

# ============ 1) PROBE PRE ============
print("== probe pre (60 bài, model gốc) ==", flush=True)
probe_idx = list(range(min(PROBE_N, len(TEROWS))))
probe_qs = [q_of(TEROWS[i]) for i in probe_idx]
probe_gs = [gold_of(TEROWS[i]) for i in probe_idx]
probe_pre = [pred(s) for s in gen(S_SYS, probe_qs, 512, 0.0)]
probe_pre_acc = round(sum(ok(x, g) for x, g in zip(probe_pre, probe_gs)) / len(probe_gs), 4)
print(f"  probe_pre_acc={probe_pre_acc}", flush=True)

# ============ 2) SINH DỮ LIỆU HUẤN LUYỆN (tiêm lỗi vào chuỗi vàng) ============
print("== sinh dữ liệu huấn luyện (tiêm lỗi) ==", flush=True)
train_data = []  # (question, solution_text, label_bool)
n_corruptible = 0
for r in TRROWS:
    q = q_of(r)
    chain = gold_chain(r)
    # clean
    train_data.append((q, chain, True))
    # corrupt
    cor, tag = corrupt_chain(chain)
    if cor is not None and cor != chain:
        train_data.append((q, cor, False))
        n_corruptible += 1
    else:
        # không tiêm được -> tạo 1 mẫu clean nữa (cân bằng)
        train_data.append((q, chain, True))

pos = sum(1 for d in train_data if d[2])
print(f"  cặp={len(train_data)} đúng={pos} ({pos / len(train_data):.3f}) "
      f"corruptible={n_corruptible}/{len(TRROWS)}", flush=True)

# ============ 3) HUẤN LUYỆN LoRA ============
model.gradient_checkpointing_enable()
model.enable_input_require_grads()
model = get_peft_model(model, LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM"))
model.print_trainable_parameters()

YES = tok.encode("Yes", add_special_tokens=False)[0]
NO = tok.encode("No", add_special_tokens=False)[0]
print(f"token Yes/No: {YES}/{NO}", flush=True)

opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
random.shuffle(train_data)
model.train()
for ep in range(EPOCH):
    tot = 0.0
    n = 0
    for i in range(0, len(train_data), MB):
        b = train_data[i:i + MB]
        e = tok([jprompt(q, s) for q, s, _ in b], return_tensors="pt",
                padding=True, truncation=True, max_length=768).to("cuda")
        out = model(**e)
        lg = out.logits[:, -1, :]
        tgt = torch.tensor([YES if y else NO for _, _, y in b], device="cuda")
        loss = F.cross_entropy(lg[:, [NO, YES]], (tgt == YES).long())
        loss.backward()
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
        opt.step()
        opt.zero_grad()
        tot += float(loss)
        n += 1
        if n % 50 == 0:
            print(f"  ep{ep} b{n}/{len(train_data) // MB} loss={tot / n:.4f} "
                  f"mem={torch.cuda.max_memory_allocated() / 1e9:.1f}GB", flush=True)
        del out, lg
    print(f"epoch {ep}: loss={tot / max(n, 1):.4f}", flush=True)

model.eval()
model.save_pretrained("/kaggle/working/injected_lora")
disable_adapter()

# ============ 4) PROBE POST ============
print("== probe post (60 bài, adapter TẮT) ==", flush=True)
probe_post = [pred(s) for s in gen(S_SYS, probe_qs, 512, 0.0)]
probe_post_acc = round(sum(ok(x, g) for x, g in zip(probe_post, probe_gs)) / len(probe_gs), 4)
adapter_leak = round(probe_pre_acc - probe_post_acc, 4)
VALID_LEAK = abs(adapter_leak) <= 0.05
print(f"  probe_post_acc={probe_post_acc} adapter_leak={adapter_leak} VALID={VALID_LEAK}", flush=True)

# ============ 5) CHẤM ĐIỂM ============
@torch.no_grad()
def score(qs, sols):
    enable_adapter()
    out = []
    for i in range(0, len(qs), BS):
        e = tok([jprompt(q, s) for q, s in zip(qs[i:i + BS], sols[i:i + BS])],
                return_tensors="pt", padding=True, truncation=True, max_length=768).to("cuda")
        lg = model(**e).logits[:, -1, :]
        out += F.log_softmax(lg[:, [NO, YES]], dim=-1)[:, 1].float().tolist()
        del e, lg
    torch.cuda.empty_cache()
    disable_adapter()
    return out

# ============ 6) ĐÁNH GIÁ A: IN-DISTRIBUTION (lỗi tiêm trên test) ============
print("== đánh giá A: in-distribution (lỗi tiêm trên test) ==", flush=True)
test_pairs = []  # (question, solution, label, variant)
for r in TEROWS:
    q = q_of(r)
    chain = gold_chain(r)
    test_pairs.append((q, chain, True, "CLEAN"))
    cor, tag = corrupt_chain(chain)
    if cor is not None and cor != chain:
        test_pairs.append((q, cor, False, "CORRUPT"))

pair_qs = [p[0] for p in test_pairs]
pair_ss = [p[1] for p in test_pairs]
pair_sc = score(pair_qs, pair_ss)

# Phân tách CLEAN vs CORRUPT
clean_scores = [pair_sc[i] for i in range(len(test_pairs)) if test_pairs[i][3] == "CLEAN"]
corrupt_scores = [pair_sc[i] for i in range(len(test_pairs)) if test_pairs[i][3] == "CORRUPT"]

if clean_scores and corrupt_scores:
    tnr = sum(1 for s in corrupt_scores if s > 0) / len(corrupt_scores)  # detects corrupt
    fpr = sum(1 for s in clean_scores if s > 0) / len(clean_scores)  # false alarm on clean
    disc_inj = round(tnr - fpr, 4)
    bal_acc_inj = round((tnr + (1 - fpr)) / 2, 4)
else:
    tnr = fpr = disc_inj = bal_acc_inj = None

print(f"  discrimination_injected={disc_inj} tnr={tnr} fpr={fpr} bal_acc={bal_acc_inj}", flush=True)

# ============ 7) ĐÁNH GIÁ B: CHUYỂN GIAO (lỗi thật) ============
print("== đánh giá B: chuyển giao (lỗi thật do model sinh) ==", flush=True)
TEQ = [q_of(r) for r in TEROWS]
TEG = [gold_of(r) for r in TEROWS]
FOLD = len(TEQ) // NF
folds = []

# Sinh k=8 mẫu bằng MODEL GỐC
all_s = []
all_y = []

for fi in range(NF):
    qs = TEQ[fi * FOLD:(fi + 1) * FOLD]
    gs = TEG[fi * FOLD:(fi + 1) * FOLD]
    print(f"== fold {fi} ==", flush=True)

    mj = gen(S_SYS, qs, 512, 0.8, K)  # model gốc
    grid = [[mj[i * K + j] for j in range(K)] for i in range(len(qs))]
    fq = [qs[i] for i in range(len(qs)) for j in range(K)]
    fs = [grid[i][j] for i in range(len(qs)) for j in range(K)]

    sc = score(fq, fs)  # adapter bật
    lab = [eq(pred(fs[n]), gs[n // K]) for n in range(len(fs))]
    all_s += sc
    all_y += lab

    # AUC trên lỗi thật
    pa = [s for s, y in zip(sc, lab) if y]
    na = [s for s, y in zip(sc, lab) if not y]
    fold_auc = round(sum(1 for p in pa for q in na if p > q) / max(len(pa) * len(na), 1), 4) if pa and na else None

    # discrimination_real = TPR - FPR trên lỗi thật
    if pa and na:
        tpr_real = sum(1 for s in pa if s > 0.5) / len(pa)  # rate of saying Yes on correct
        fpr_real = sum(1 for s in na if s > 0.5) / len(na)  # rate of saying Yes on wrong
        disc_real = round(tpr_real - fpr_real, 4)
    else:
        tpr_real = fpr_real = disc_real = None

    # wvote vs maj
    a_re, a_mj, a_or, a_gd, a_ws = [], [], [], [], []
    for i in range(len(qs)):
        S = sc[i * K:(i + 1) * K]
        C = grid[i]
        a_re.append(pred(C[max(range(K), key=lambda j: S[j])]))
        cnt, wsum = {}, {}
        for j in range(K):
            p = pred(C[j])
            if p is not None:
                cnt[p] = cnt.get(p, 0) + 1
                w = float(torch.tensor(S[j]).exp())
                wsum[p] = wsum.get(p, 0.0) + w
        a_mj.append(max(cnt, key=cnt.get) if cnt else None)
        a_ws.append(max(wsum, key=wsum.get) if wsum else None)
        a_or.append(gs[i] if any(eq(pred(C[j]), gs[i]) for j in range(K)) else pred(C[0]))
        a_gd.append(pred(C[0]))

    acc = lambda a: round(sum(eq(x, g) for x, g in zip(a, gs)) / len(gs), 4)
    r = {"fold": fi, "n": len(qs),
         "greedy1": acc(a_gd), "maj8": acc(a_mj), "rerank8": acc(a_re),
         "wvote_sum": acc(a_ws), "oracle8": acc(a_or),
         "wsum_minus_maj": round(acc(a_ws) - acc(a_mj), 4),
         "rerank_minus_maj": round(acc(a_re) - acc(a_mj), 4),
         "auc_real": fold_auc,
         "discrimination_real": disc_real,
         "tpr_real": tpr_real, "fpr_real": fpr_real}
    folds.append(r)
    print(f"  [fold {fi}] {json.dumps(r)}", flush=True)

# Tổng hợp AUC trên lỗi thật (toàn bộ)
pa_all = [s for s, y in zip(all_s, all_y) if y]
na_all = [s for s, y in zip(all_s, all_y) if not y]
auc_real = round(sum(1 for p in pa_all for q in na_all if p > q) / max(len(pa_all) * len(na_all), 1), 4) if pa_all and na_all else None
tpr_all = sum(1 for s in pa_all if s > 0.5) / len(pa_all) if pa_all else None
fpr_all = sum(1 for s in na_all if s > 0.5) / len(na_all) if na_all else None
disc_real_all = round(tpr_all - fpr_all, 4) if tpr_all is not None and fpr_all is not None else None

# Degenerate rate
total_labels = len(all_y)
deg_rate = max(sum(all_y), total_labels - sum(all_y)) / max(total_labels, 1)


def sp(k):
    v = [f[k] for f in folds if f.get(k) is not None]
    if not v:
        return None
    return {"mean": round(st.mean(v), 4), "min": round(min(v), 4),
            "max": round(max(v), 4), "pos": sum(1 for x in v if x > 0)}


out = {
    "tag": "injected_classifier", "task": TASK,
    "adapter_leak": adapter_leak, "VALID_leak": VALID_LEAK,
    "probe_n": PROBE_N, "probe_pre_acc": probe_pre_acc, "probe_post_acc": probe_post_acc,
    "n_train_pairs": len(train_data), "train_pos_rate": round(pos / len(train_data), 4),
    # Đánh giá A: in-distribution
    "discrimination_injected": disc_inj,
    "tnr_injected": round(tnr, 4) if tnr is not None else None,
    "fpr_injected": round(fpr, 4) if fpr is not None else None,
    "balanced_acc_injected": bal_acc_inj,
    # Đánh giá B: chuyển giao
    "auc_real": auc_real, "VALID_auc": bool(auc_real and auc_real > 0.55),
    "discrimination_real": disc_real_all,
    "tpr_real": round(tpr_all, 4) if tpr_all is not None else None,
    "fpr_real": round(fpr_all, 4) if fpr_all is not None else None,
    "degenerate_rate": round(deg_rate, 4),
    "VALID_degenerate": bool(deg_rate <= 0.90),
    # Đánh giá C: thực tiễn
    "folds": folds}
for k in ["greedy1", "maj8", "rerank8", "wvote_sum", "oracle8",
          "wsum_minus_maj", "rerank_minus_maj", "auc_real", "discrimination_real"]:
    out[k] = sp(k)

print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump([{"q": fq if isinstance(fq, str) else str(fq), "sol": str(fs)[:500],
            "score": all_s[i], "correct": all_y[i]}
           for i in range(min(200, len(all_s)))],
          open("/kaggle/working/traces.json", "w"), indent=1)
print("DONE", flush=True)
