# EVAL credit-rl adapter(s) trên GSM8K TEST — 5 fold.
#
# ROLE = "P"|"S"|"V"|"A"|"FULL"
#   - per-role (P/S/V/A): kernel mount ĐÚNG 1 adapter của role đó, so pipeline CHỨA
#     role đó chạy BASE (adapter tắt) vs TRAINED (adapter bật). Các vai khác luôn base.
#   - FULL: mount CẢ 4 adapter (P,S,V,A), so pipeline P->S->V->A BASE vs TRAINED.
#
# Chỉ số chính (per-role): gain = acc(pipeline chứa role R, trained) − acc(cùng pipeline, base).
#   P:  P->S   (plan base vs trained; solver base)
#   S:  P->S   (plan base; solver base vs trained)
#   V:  P->S->V (V base vs trained) + intervention/fix/break/copy — mốc V_base +4.4đ [+1..+8]
#   A:  P->S->V->A (A base vs trained; P,S,V base)
#   FULL: P->S->V->A base vs trained + per-stage acc.
# Tiêu chí "kết quả dương thật": gain_train > 0 và 5/5 fold cùng dấu.
import os, sys, re, csv, json, glob, statistics, subprocess

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

ROLE = __ROLE__  # "P"|"S"|"V"|"A"|"FULL"
N  = __N__       # số bài eval (multiple of NF)
NF = __NF__      # số fold
BS = __BS__

assert ROLE in ("P", "S", "V", "A", "FULL"), f"ROLE={ROLE}"

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13,<0.15"], check=False)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

FOLD = N // NF
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])

ROLE_PAT = re.compile(r"credit-rl-([psva])-adapter", re.I)
# dataset của thí nghiệm chống collapse/conditional: tên chứa pminlen/vcond/asel
VARIANT_PAT = re.compile(r"credit-rl-(pminlen|vcond|asel)-adapter", re.I)
def role_of(path):
    m = VARIANT_PAT.search(path)
    if m:
        return {"pminlen": "P", "vcond": "V", "asel": "A"}[m.group(1).lower()]
    m = ROLE_PAT.search(path)
    return m.group(1).upper() if m else None

_a = sorted(glob.glob("/kaggle/input/**/adapter_config.json", recursive=True), key=len)
if not _a:
    raise FileNotFoundError("khong thay adapter_config.json :: "
                            + str(glob.glob("/kaggle/input/**", recursive=True)[:30]))
ADAPTERS = {}
for p in _a:
    r = role_of(p)
    if r:
        ADAPTERS.setdefault(r, os.path.dirname(p))
print(f"MODEL={MODEL}\nROLE={ROLE}\nadapters: {ADAPTERS}", flush=True)

if ROLE == "FULL":
    need = {"P", "S", "V", "A"}
    missing = need - set(ADAPTERS)
    if missing:
        raise FileNotFoundError(f"FULL can day du adapter, thieu {missing} :: {list(ADAPTERS)}")
else:
    if ROLE not in ADAPTERS:
        raise FileNotFoundError(f"ROLE={ROLE} khong co adapter matching :: {list(ADAPTERS)}")
    # chỉ giữ adapter của role đang eval (mỗi kernel đánh giá đúng 1 vai)
    ADAPTERS = {ROLE: ADAPTERS[ROLE]}

CSV = sorted(glob.glob("/kaggle/input/**/main_test.csv", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV)))[:N]
print(f"{NF} fold x {FOLD}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
base = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                            device_map={"": 0}).eval()
model = PeftModel.from_pretrained(base, ADAPTERS[list(ADAPTERS)[0]],
                                  adapter_name=list(ADAPTERS)[0])
for r, p in ADAPTERS.items():
    if r != list(ADAPTERS)[0]:
        model.load_adapter(p, adapter_name=r)
model.set_adapter(list(ADAPTERS)[0])
model.eval()
print("adapters loaded", flush=True)

import contextlib

@contextlib.contextmanager
def _null():
    yield

def gen(sysm, usrs, mx, role=None):
    """role=None -> base (tất cả adapter tắt); role="P"|"S"|"V"|"A" -> bật adapter đó."""
    outs = []
    if role is None:
        with model.disable_adapter():
            outs = _gen(sysm, usrs, mx)
    else:
        model.set_adapter(role)
        outs = _gen(sysm, usrs, mx)
        model.set_adapter(list(ADAPTERS)[0])
    return outs

def _gen(sysm, usrs, mx):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = [tok.apply_chat_template([{"role": "system", "content": sysm},
                                       {"role": "user", "content": u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False,
                               temperature=1.0, pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip()
                 for j in range(len(ch))]
    return outs

PLAN_SYS  = ("You are a math planning assistant. Read the problem and give a concise "
             "numbered plan of the steps needed. Do NOT compute the final answer.")
SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
             "End with a line: 'The answer is <number>'.")
VERIFY_SYS = ("You are a math verifier. You are given a problem and a proposed solution. "
              "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
AGG_SYS   = ("You are given a math problem and one or more candidate solutions. Decide the "
             "correct final answer by re-checking and majority. End with 'The answer is "
             "<number>'.")
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def pred(t):
    m = (re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
         or NUM.findall(t or ""))
    return m[-1].replace(",", "") if m else None
def eq(a, b):
    if a is None or b is None: return False
    try: return abs(float(a) - float(b)) < 1e-6
    except ValueError: return a == b
def gold_of(r):
    m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
    return m.group(1).replace(",", "").strip() if m else None

def with_plan(q, p): return q + "\n\nSuggested plan:\n" + p
def verify_user(q, s): return q + "\n\nProposed solution:\n" + s
def agg_user(q, cands):
    body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(cands))
    return f"{q}\n\n{body}"

MX_P, MX_S, MX_V, MX_A = 256, 512, 512, 256

# ==============================================================================
# Eval: 5-fold, mỗi fold chạy pipeline đúng theo ROLE
# ==============================================================================
fold_stats, sample = [], []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [r["question"] for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n} bai) ROLE={ROLE} =====", flush=True)

    plans = gen(PLAN_SYS, qs, MX_P, role=None)                     # P luôn base

    if ROLE in ("P", "FULL"):
        plans_t = gen(PLAN_SYS, qs, MX_P, role="P")                 # P trained
        sols_base = gen(SOLVE_SYS, [with_plan(q, p) for q, p in zip(qs, plans)], MX_S, None)
        sols_t    = gen(SOLVE_SYS, [with_plan(q, p) for q, p in zip(qs, plans_t)], MX_S, None)
        sols_ref = sols_base
    elif ROLE == "S":
        sols_base = gen(SOLVE_SYS, [with_plan(q, p) for q, p in zip(qs, plans)], MX_S, None)
        sols_t    = gen(SOLVE_SYS, [with_plan(q, p) for q, p in zip(qs, plans)], MX_S, "S")
        sols_ref = sols_base
    else:  # V | A
        sols_base = gen(SOLVE_SYS, [with_plan(q, p) for q, p in zip(qs, plans)], MX_S, None)
        sols_t = sols_base

    if ROLE in ("V", "FULL", "A"):
        if ROLE == "V":
            v_ref  = gen(VERIFY_SYS, [verify_user(q, s) for q, s in zip(qs, sols_base)], MX_V, None)
            v_full = gen(VERIFY_SYS, [verify_user(q, s) for q, s in zip(qs, sols_base)], MX_V, "V")
        else:  # FULL | A: V base
            v_ref = gen(VERIFY_SYS, [verify_user(q, s) for q, s in zip(qs, sols_base)], MX_V, None)
            if ROLE == "FULL":
                v_full = gen(VERIFY_SYS, [verify_user(q, s) for q, s in zip(qs, sols_base)], MX_V, "V")
            else:
                v_full = v_ref

    if ROLE in ("A", "FULL"):
        a_ref = gen(AGG_SYS, [agg_user(q, [s, v]) for q, s, v in zip(qs, sols_base, v_ref)], MX_A, None)
        if ROLE == "FULL":
            a_full = gen(AGG_SYS, [agg_user(q, [s, v]) for q, s, v in zip(qs, sols_t, v_full)], MX_A, "A")
        else:
            a_full = gen(AGG_SYS, [agg_user(q, [s, v]) for q, s, v in zip(qs, sols_base, v_ref)], MX_A, "A")

    # ---- kết quả theo ROLE ----
    if ROLE == "P":
        ref_out, full_out = sols_ref, sols_t
    elif ROLE == "S":
        ref_out, full_out = sols_ref, sols_t
    elif ROLE == "V":
        ref_out, full_out = v_ref, v_full
    else:  # A | FULL
        ref_out, full_out = a_ref, a_full

    ok_ref  = [eq(pred(t), g) for t, g in zip(ref_out, gs)]
    ok_full = [eq(pred(t), g) for t, g in zip(full_out, gs)]
    d = {"acc_ref": sum(ok_ref) / n, "acc_full": sum(ok_full) / n,
         "gain": sum(ok_full) / n - sum(ok_ref) / n}
    d["oracle"] = sum(1 for s, g in zip(sols_base, gs) if eq(pred(s), g)) / n

    if ROLE == "V":
        def metrics(vs):
            return {
                "intervention": sum(1 for t, s in zip(vs, sols_base)
                                    if not eq(pred(t), pred(s))) / n,
                "fix": sum(1 for t, s, g in zip(vs, sols_base, gs)
                           if eq(pred(t), g) and not eq(pred(s), g)) / n,
                "break": sum(1 for t, s, g in zip(vs, sols_base, gs)
                             if not eq(pred(t), g) and eq(pred(s), g)) / n,
                "copy": sum(1 for t, s in zip(vs, sols_base)
                            if eq(pred(t), pred(s))) / n,
            }
        d["V_ref"] = metrics(v_ref)
        d["V_full"] = metrics(v_full)
    if ROLE == "FULL":
        d["stage"] = {
            "PS_base": sum(eq(pred(s), g) for s, g in zip(sols_base, gs)) / n,
            "PS_full": sum(eq(pred(s), g) for s, g in zip(sols_t, gs)) / n,
            "PSV_base": sum(eq(pred(t), g) for t, g in zip(v_ref, gs)) / n,
            "PSV_full": sum(eq(pred(t), g) for t, g in zip(v_full, gs)) / n,
        }

    fold_stats.append(d)
    print(f"  ref {d['acc_ref']:.3f} -> full {d['acc_full']:.3f} "
          f"gain {d['gain']:+.3f} | oracle PS {d['oracle']:.3f}", flush=True)
    if ROLE == "V":
        print(f"  inter {d['V_ref']['intervention']:.2f}->{d['V_full']['intervention']:.2f} | "
              f"fix {d['V_ref']['fix']:.3f}->{d['V_full']['fix']:.3f} | "
              f"break {d['V_ref']['break']:.3f}->{d['V_full']['break']:.3f} | "
              f"copy {d['V_ref']['copy']:.3f}->{d['V_full']['copy']:.3f}", flush=True)
    if ROLE == "FULL":
        print(f"  PS {d['stage']['PS_base']:.3f}->{d['stage']['PS_full']:.3f} | "
              f"PSV {d['stage']['PSV_base']:.3f}->{d['stage']['PSV_full']:.3f}", flush=True)

    for i in range(n):
        rec = {"fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
               "plan": plans[i], "sol": sols_base[i],
               "ref": ref_out[i], "full": full_out[i],
               "pred": {"ref": pred(ref_out[i]), "full": pred(full_out[i])},
               "ok": {"ref": ok_ref[i], "full": ok_full[i]}}
        sample.append(rec)
        with open("/kaggle/working/traces.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    json.dump({"role": ROLE, "folds_done": f + 1, "n_folds": NF, "fold_size": FOLD,
               "complete": f + 1 == NF, "per_fold": fold_stats},
              open("/kaggle/working/summary.json", "w"), indent=2)
    print(f"  [checkpoint] {f+1}/{NF} fold", flush=True)

# ---- tổng hợp ----
def stats(xs):
    return {"mean": round(statistics.mean(xs), 4), "min": round(min(xs), 4),
            "max": round(max(xs), 4), "by_fold": [round(x, 4) for x in xs]}

gains = [d["gain"] for d in fold_stats]
same = (sum(1 for g in gains if g > 0) if statistics.mean(gains) >= 0
        else sum(1 for g in gains if g < 0))
out = {"role": ROLE, "n_folds": NF, "fold_size": FOLD, "complete": True,
       "arms": {"ref": stats([d["acc_ref"] for d in fold_stats]),
                "full": stats([d["acc_full"] for d in fold_stats]),
                "gain": stats(gains), "folds_same_sign": f"{same}/{NF}"},
       "oracle_PS": stats([d["oracle"] for d in fold_stats])}
print("\n" + "=" * 80)
print(f"ROLE={ROLE}: ref {statistics.mean(d['acc_ref'] for d in fold_stats):.3f} "
      f"-> full {statistics.mean(d['acc_full'] for d in fold_stats):.3f} | "
      f"gain {statistics.mean(gains):+.4f} [{min(gains):+.3f}..{max(gains):+.3f}] "
      f"{same}/{NF} fold cung dau")
print("=" * 80)
if ROLE == "V":
    for k in ("intervention", "fix", "break", "copy"):
        out[f"V_ref_{k}"] = stats([d["V_ref"][k] for d in fold_stats])
        out[f"V_full_{k}"] = stats([d["V_full"][k] for d in fold_stats])
        print(f"  {k:<12} ref {out[f'V_ref_{k}']['mean']:.3f} -> full "
              f"{out[f'V_full_{k}']['mean']:.3f}")
    print("MOC (GSM8K 1.5B, FINDINGS): V_base gain +4.4d [+1..+8], 5/5 fold duong.")
print("TIEU CHI: gain>0 VA 5/5 fold cung dau -> duong that.")
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)
