# EVAL P(minlen-GRPO)+S vs S solo trên GSM8K TEST.
#
# So sánh 3 nhánh trên cùng 200 câu eval (tách rời train):
#   solo : S giải một mình (không plan)               -> baseline S solo
#   pbase: P BASE sinh plan (greedy) -> S              -> P (chưa train) + S
#   ptrl : P TRAINED (adapter pminlen) sinh plan -> S  -> P (sau GRPO) + S
#
# Ngoài acc còn ghi: độ dài plan base vs trained, % câu plan khác nhau,
# % câu solver output khác nhau, ma trận đúng/sai từng cặp nhánh.
import os, sys, re, csv, json, glob, subprocess

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

N  = __N__
BS = __BS__

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13,<0.15"], check=False)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
_a = sorted(glob.glob("/kaggle/input/**/adapter_config.json", recursive=True), key=len)
if not _a:
    raise FileNotFoundError("khong thay adapter_config.json :: "
                            + str(glob.glob("/kaggle/input/**", recursive=True)[:30]))
ADAPTER = os.path.dirname(_a[0])
print(f"MODEL={MODEL}\nADAPTER={ADAPTER}", flush=True)

CSV = sorted(glob.glob("/kaggle/input/**/main_test.csv", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
qs = [r["question"] for r in rows]

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
base = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                            device_map={"": 0}).eval()
model = PeftModel.from_pretrained(base, ADAPTER, adapter_name="P").eval()

import contextlib

@contextlib.contextmanager
def _null():
    yield

def gen(sysm, usrs, mx, trained):
    """trained=False -> chạy base (adapter tắt); True -> adapter P (minlen)."""
    ctx = _null() if trained else model.disable_adapter()
    outs = []
    with ctx:
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

gs = [gold_answer(r["answer"]) for r in rows]

# ---- rollout 3 nhánh ----
print("== rollout ==", flush=True)
sol_solo = gen(SOLVE_SYS, qs, 512, False)                          # S solo
plan_pb  = gen(PLAN_SYS, qs, 256, False)                           # P base
sol_pb   = gen(SOLVE_SYS, [q + "\n\nSuggested plan:\n" + p
                           for q, p in zip(qs, plan_pb)], 512, False)
plan_pt  = gen(PLAN_SYS, qs, 256, True)                            # P trained
sol_pt   = gen(SOLVE_SYS, [q + "\n\nSuggested plan:\n" + p
                           for q, p in zip(qs, plan_pt)], 512, False)

ok = lambda text, g: num_eq(pred_answer(text), g)
acc = lambda sols: sum(ok(s, g) for s, g in zip(sols, gs)) / len(gs)

acc_solo = acc(sol_solo)
acc_pb   = acc(sol_pb)
acc_pt   = acc(sol_pt)

# ---- so sánh chi tiết ----
plan_diff = sum(1 for a, b in zip(plan_pb, plan_pt) if a.strip() != b.strip())
sol_diff_pb = sum(1 for a, b in zip(sol_solo, sol_pb) if a.strip() != b.strip())
sol_diff_pt = sum(1 for a, b in zip(sol_solo, sol_pt) if a.strip() != b.strip())
len_pb = sum(len(p) for p in plan_pb) / len(plan_pb)
len_pt = sum(len(p) for p in plan_pt) / len(plan_pt)
empty_pt = sum(1 for p in plan_pt if not p.strip())

# ma trận đúng/sai 3 nhánh
def corr(sols):
    return [ok(s, g) for s, g in zip(sols, gs)]

c_solo, c_pb, c_pt = corr(sol_solo), corr(sol_pb), corr(sol_pt)

# trường hợp P trained cứu/sửa được câu mà S solo sai
fix_pt = sum(1 for a, b in zip(c_pt, c_solo) if b and not a)
break_pt = sum(1 for a, b in zip(c_pt, c_solo) if a and not b)
fix_pb = sum(1 for a, b in zip(c_pb, c_solo) if b and not a)
break_pb = sum(1 for a, b in zip(c_pb, c_solo) if a and not b)

# mối quan hệ: câu nào P trained thay đổi sol mà lại sai?
change_ok_pt = sum(1 for i in range(len(qs))
                   if sol_pt[i].strip() != sol_solo[i].strip() and c_pt[i])
change_bad_pt = sum(1 for i in range(len(qs))
                    if sol_pt[i].strip() != sol_solo[i].strip() and not c_pt[i])

print(f"N={N}", flush=True)
print(f"acc  solo={acc_solo:.4f}  P(base)+S={acc_pb:.4f}  P(trl)+S={acc_pt:.4f}", flush=True)
print(f"delta: pbase-solo={acc_pb-acc_solo:+.4f}  ptrl-solo={acc_pt-acc_solo:+.4f}  "
      f"ptrl-pbase={acc_pt-acc_pb:+.4f}", flush=True)
print(f"plan: len_base={len_pb:.0f} len_trl={len_pt:.0f} empty_trl={empty_pt} "
      f"plan_diff%={100*plan_diff/len(qs):.0f}", flush=True)
print(f"sol_diff: pbase {100*sol_diff_pb/len(qs):.0f}%  ptrl {100*sol_diff_pt/len(qs):.0f}%", flush=True)
print(f"P(base) vs solo: fix={fix_pb} break={break_pb}", flush=True)
print(f"P(trl)  vs solo: fix={fix_pt} break={break_pt}   "
      f"(trong đó sol đổi & đúng={change_ok_pt}, sol đổi & sai={change_bad_pt})", flush=True)

out = {"N": N, "acc": {"solo": acc_solo, "pbase_plus_s": acc_pb, "ptrl_plus_s": acc_pt},
       "delta": {"pbase_vs_solo": acc_pb - acc_solo, "ptrl_vs_solo": acc_pt - acc_solo,
                 "ptrl_vs_pbase": acc_pt - acc_pb},
       "plan": {"len_base": len_pb, "len_trl": len_pt, "empty_trl": empty_pt,
                "pct_diff": plan_diff / len(qs)},
       "sol_diff_pct": {"pbase": sol_diff_pb / len(qs), "ptrl": sol_diff_pt / len(qs)},
       "intervention": {"pbase_fix": fix_pb, "pbase_break": break_pb,
                        "ptrl_fix": fix_pt, "ptrl_break": break_pt,
                        "ptrl_change_ok": change_ok_pt, "ptrl_change_bad": change_bad_pt}}
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
print("SUMMARY", json.dumps(out, indent=1), flush=True)
print("done", flush=True)
