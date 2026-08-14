# INSPECT: so sanh truc tiep output Planner BASE vs TRAINED (adapter pminlen).
# Gen plan greedy cho N cau test, dem % cau khac nhau, in 6 vi du.
# Dong thoi tinh KL(logits trained || base) tren 1 batch de biet adapter co doi phan bo khong.
import os, sys, re, csv, json, glob, subprocess

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
N = __N__; BS = __BS__

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13,<0.15"], check=False)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
_a = sorted(glob.glob("/kaggle/input/**/adapter_config.json", recursive=True), key=len)
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

PLAN_SYS = ("You are a math planning assistant. Read the problem and give a concise "
            "numbered plan of the steps needed. Do NOT compute the final answer.")

def chat(u):
    return tok.apply_chat_template([{"role": "system", "content": PLAN_SYS},
                                    {"role": "user", "content": u}],
                                   tokenize=False, add_generation_prompt=True)

ps = [chat(q) for q in qs]
e = tok(ps, return_tensors="pt", padding=True).to(model.device)

def gen_with(trained):
    with (model.disable_adapter() if not trained else __import__("contextlib").nullcontext()):
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=256, do_sample=False,
                               temperature=1.0, pad_token_id=tok.pad_token_id)
    L = e["input_ids"].shape[1]
    return [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ps))]

plan_base = gen_with(False)
plan_trl  = gen_with(True)

diff = sum(1 for a, b in zip(plan_base, plan_trl) if a.strip() != b.strip())
print(f"\nN={N}  plan_diff (base vs trained) = {diff}/{N} = {100*diff/N:.1f}%", flush=True)
print(f"plan len: base={sum(len(p) for p in plan_base)/N:.1f}  trl={sum(len(p) for p in plan_trl)/N:.1f}",
      flush=True)

for i in range(min(6, N)):
    same = "SAME" if plan_base[i].strip() == plan_trl[i].strip() else "DIFF"
    print(f"\n--- cau {i} [{same}] ---", flush=True)
    print(f"Q  : {qs[i][:160]}", flush=True)
    print(f"BASE: {plan_base[i][:300]}", flush=True)
    if same != "SAME":
        print(f"TRL : {plan_trl[i][:300]}", flush=True)

# KL(trained || base) tren 1 cau dau: phan bo logits co doi khong?
print("\n== KL(logits trained||base), greedy top-1 ===", flush=True)
with torch.no_grad():
    b1 = base(**e)
    a1 = model(**e)
lgt = torch.nn.functional.log_softmax(a1.logits, -1)
lgb = torch.nn.functional.log_softmax(b1.logits, -1)
kl = torch.exp(lgb) * (lgb - lgt)
kl = kl.sum(-1).mean().item()
topb = b1.logits[0, -1].argmax().item()
topt = a1.logits[0, -1].argmax().item()
print(f"KL(p_tr||p_ba) mean over seq = {kl:.5f}", flush=True)
print(f"last token: base={tok.decode([topb])!r} trained={tok.decode([topt])!r}", flush=True)

out = {"N": N, "plan_diff": diff, "plan_diff_pct": diff / N,
       "plan_len": {"base": sum(len(p) for p in plan_base) / N,
                    "trl": sum(len(p) for p in plan_trl) / N},
       "KL_tr_ba": kl,
       "examples": [{"q": qs[i][:160], "same": plan_base[i].strip() == plan_trl[i].strip(),
                     "base": plan_base[i], "trl": plan_trl[i]}
                    for i in range(min(6, N))]}
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
print("SUMMARY", json.dumps(out, indent=1), flush=True)
print("done", flush=True)