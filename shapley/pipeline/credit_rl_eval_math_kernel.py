# EVAL credit-rl adapter(s) trên MATH-500 TEST (open-benchmarks) — 5 fold.
#
# ROLE = "V" | "PSVA"   (prompts MATH-native: solver/verifier trả \boxed{})
#   - V:   mount 1 adapter V (base vs trained V-COND), pipeline P->S->V.
#   - PSVA: mount 3 adapter S,V,A (P base), pipeline P(base)->S->V->A với
#          S,V,A trained vs toàn bộ base. P luôn base (plan-inspect KL=0).
import os, sys, re, csv, json, glob, statistics, subprocess

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

ROLE = __ROLE__  # "V" | "PSVA"
N  = __N__
NF = __NF__
BS = __BS__
FOLD = N // NF

assert ROLE in ("V", "PSVA"), f"ROLE={ROLE}"

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13,<0.15"], check=False)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])

ROLE_PAT = re.compile(r"credit-rl-([psva])-adapter", re.I)
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

if ROLE == "PSVA":
    need = {"S", "V", "A"}
    missing = need - set(ADAPTERS)
    if missing:
        raise FileNotFoundError(f"PSVA can S,V,A, thieu {missing} :: {list(ADAPTERS)}")
else:
    if ROLE not in ADAPTERS:
        raise FileNotFoundError(f"ROLE={ROLE} khong co adapter matching :: {list(ADAPTERS)}")
    ADAPTERS = {ROLE: ADAPTERS[ROLE]}

CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV, encoding="utf-8")))[:N]
print(f"{NF} fold x {FOLD} MATH", flush=True)

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
    """role=None -> base (tất cả adapter tắt); role="S"|"V"|"A" -> bật adapter đó."""
    if role is None:
        with model.disable_adapter():
            return _gen(sysm, usrs, mx)
    model.set_adapter(role)
    try:
        return _gen(sysm, usrs, mx)
    finally:
        model.set_adapter(list(ADAPTERS)[0])

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

PLAN_SYS  = ("You are a math planning assistant. Read the competition problem and give a "
             "concise numbered plan of the solution steps. Do NOT compute the final answer.")
SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the "
             "final answer in \\boxed{}.")
VERIFY_SYS = ("You are a math verifier. Given a problem and a proposed solution, check each "
              "step; if wrong, correct it. Put the final answer in \\boxed{}.")
AGG_SYS   = ("You are given a math problem and one or more candidate solutions. Decide the "
             "correct final answer by re-checking and majority. Put the final answer in "
             "\\boxed{}.")

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
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " ", ","]: a = a.replace(x, "")
    for x in ["\\(", "\\)", "\\[", "\\]"]: a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()

def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g: return False
    if p == g: return True
    try: return abs(float(p) - float(g)) < 1e-6
    except: return False

def with_plan(q, p): return q + "\n\nSuggested plan:\n" + p
def verify_user(q, s): return q + "\n\nProposed solution:\n" + s
def agg_user(q, cands):
    body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(cands))
    return f"{q}\n\n{body}"

MX_P, MX_S, MX_V, MX_A = 256, 512, 512, 256

fold_stats, sample = [], []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [r["Question"].strip() for r in rows]
    gs = [boxed(r["Answer"]) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n} bai MATH) ROLE={ROLE} =====", flush=True)

    plans = gen(PLAN_SYS, qs, MX_P, None)                                # P luôn base

    if ROLE == "PSVA":
        sols_base = gen(SOLVE_SYS, [with_plan(q, p) for q, p in zip(qs, plans)], MX_S, None)
        sols_t    = gen(SOLVE_SYS, [with_plan(q, p) for q, p in zip(qs, plans)], MX_S, "S")
        v_ref  = gen(VERIFY_SYS, [verify_user(q, s) for q, s in zip(qs, sols_base)], MX_V, None)
        v_full = gen(VERIFY_SYS, [verify_user(q, s) for q, s in zip(qs, sols_t)], MX_V, "V")
        a_ref  = gen(AGG_SYS, [agg_user(q, [s, v]) for q, s, v in zip(qs, sols_base, v_ref)], MX_A, None)
        a_full = gen(AGG_SYS, [agg_user(q, [s, v]) for q, s, v in zip(qs, sols_t, v_full)], MX_A, "A")
        ref_out, full_out = a_ref, a_full
        sols = sols_base
    else:  # V
        sols = gen(SOLVE_SYS, [with_plan(q, p) for q, p in zip(qs, plans)], MX_S, None)
        v_ref  = gen(VERIFY_SYS, [verify_user(q, s) for q, s in zip(qs, sols)], MX_V, None)
        v_full = gen(VERIFY_SYS, [verify_user(q, s) for q, s in zip(qs, sols)], MX_V, "V")
        ref_out, full_out = v_ref, v_full

    ok_ref  = [eq(boxed(t), g) for t, g in zip(ref_out, gs)]
    ok_full = [eq(boxed(t), g) for t, g in zip(full_out, gs)]
    d = {"acc_ref": sum(ok_ref) / n, "acc_full": sum(ok_full) / n,
         "gain": sum(ok_full) / n - sum(ok_ref) / n,
         "oracle": sum(1 for s, g in zip(sols, gs) if eq(boxed(s), g)) / n}
    def metrics(vs):
        return {
            "intervention": sum(1 for t, s in zip(vs, sols)
                                if not eq(boxed(t), boxed(s))) / n,
            "fix": sum(1 for t, s, g in zip(vs, sols, gs)
                       if eq(boxed(t), g) and not eq(boxed(s), g)) / n,
            "break": sum(1 for t, s, g in zip(vs, sols, gs)
                         if not eq(boxed(t), g) and eq(boxed(s), g)) / n,
            "copy": sum(1 for t, s in zip(vs, sols)
                        if eq(boxed(t), boxed(s))) / n,
        }
    d["V_ref"] = metrics(v_ref)
    d["V_full"] = metrics(v_full)
    if ROLE == "PSVA":
        d["stage"] = {
            "PS_base": sum(eq(boxed(s), g) for s, g in zip(sols_base, gs)) / n,
            "PS_full": sum(eq(boxed(s), g) for s, g in zip(sols_t, gs)) / n,
            "PSV_base": sum(eq(boxed(t), g) for t, g in zip(v_ref, gs)) / n,
            "PSV_full": sum(eq(boxed(t), g) for t, g in zip(v_full, gs)) / n,
        }
    fold_stats.append(d)
    print(f"  ref {d['acc_ref']:.3f} -> full {d['acc_full']:.3f} gain {d['gain']:+.3f} "
          f"| oracle PS {d['oracle']:.3f}", flush=True)
    print(f"  inter {d['V_ref']['intervention']:.2f}->{d['V_full']['intervention']:.2f} | "
          f"fix {d['V_ref']['fix']:.3f}->{d['V_full']['fix']:.3f} | "
          f"break {d['V_ref']['break']:.3f}->{d['V_full']['break']:.3f} | "
          f"copy {d['V_ref']['copy']:.3f}->{d['V_full']['copy']:.3f}", flush=True)
    if ROLE == "PSVA":
        print(f"  PS {d['stage']['PS_base']:.3f}->{d['stage']['PS_full']:.3f} | "
              f"PSV {d['stage']['PSV_base']:.3f}->{d['stage']['PSV_full']:.3f}", flush=True)

    for i in range(n):
        rec = {"fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
               "plan": plans[i], "sol": sols[i],
               "ref": ref_out[i], "full": full_out[i],
               "pred": {"ref": boxed(ref_out[i]), "full": boxed(full_out[i])},
               "ok": {"ref": ok_ref[i], "full": ok_full[i]}}
        sample.append(rec)
        with open("/kaggle/working/traces.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    json.dump({"role": ROLE, "task": "math", "folds_done": f + 1, "n_folds": NF,
               "fold_size": FOLD, "complete": f + 1 == NF, "per_fold": fold_stats},
              open("/kaggle/working/summary.json", "w"), indent=2)
    print(f"  [checkpoint] {f+1}/{NF} fold", flush=True)

def stats(xs):
    return {"mean": round(statistics.mean(xs), 4), "min": round(min(xs), 4),
            "max": round(max(xs), 4), "by_fold": [round(x, 4) for x in xs]}

gains = [d["gain"] for d in fold_stats]
same = (sum(1 for g in gains if g > 0) if statistics.mean(gains) >= 0
        else sum(1 for g in gains if g < 0))
out = {"role": ROLE, "task": "math", "n_folds": NF, "fold_size": FOLD, "complete": True,
       "arms": {"ref": stats([d["acc_ref"] for d in fold_stats]),
                "full": stats([d["acc_full"] for d in fold_stats]),
                "gain": stats(gains), "folds_same_sign": f"{same}/{NF}"},
       "oracle_PS": stats([d["oracle"] for d in fold_stats])}
print("\n" + "=" * 80)
print(f"MATH ROLE={ROLE}: ref {statistics.mean(d['acc_ref'] for d in fold_stats):.3f} "
      f"-> full {statistics.mean(d['acc_full'] for d in fold_stats):.3f} | "
      f"gain {statistics.mean(gains):+.4f} [{min(gains):+.3f}..{max(gains):+.3f}] "
      f"{same}/{NF} fold cung dau")
for k in ("intervention", "fix", "break", "copy"):
    out[f"V_ref_{k}"] = stats([d["V_ref"][k] for d in fold_stats])
    out[f"V_full_{k}"] = stats([d["V_full"][k] for d in fold_stats])
    print(f"  {k:<12} ref {out[f'V_ref_{k}']['mean']:.3f} -> full "
          f"{out[f'V_full_{k}']['mean']:.3f}")
if ROLE == "PSVA":
    for k in ("PS_base", "PS_full", "PSV_base", "PSV_full"):
        out[f"stage_{k}"] = stats([d["stage"][k] for d in fold_stats])
        print(f"  {k:<9} {out[f'stage_{k}']['mean']:.3f}")
print("TIEU CHI: gain>0 VA 5/5 fold cung dau -> duong that.")
print("=" * 80)
print("SUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)