# Qwen2.5-1.5B-Instruct  x  GSM8K  (zero-shot CoT, greedy)  on Kaggle GPU.
# Everything is mounted from Kaggle datasets; no internet required.
import os, re, csv, json, time, glob
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def find_one(pattern, what):
    hits = glob.glob(pattern, recursive=True)
    if not hits:
        raise FileNotFoundError(f"{what}: no match for {pattern}\n"
                                f"tree: {glob.glob('/kaggle/input/**', recursive=True)[:50]}")
    return sorted(hits, key=len)[0]

# resolve mounts by content, not by guessed folder names
MODEL_DIR = os.path.dirname(find_one("/kaggle/input/**/config.json", "model config.json"))
GSM8K_CSV = find_one("/kaggle/input/**/main_test.csv", "GSM8K main_test.csv")
OUT_DIR   = "/kaggle/working"
print("MODEL_DIR", MODEL_DIR, "\nGSM8K_CSV", GSM8K_CSV, flush=True)
N_EVAL    = int(os.environ.get("N_EVAL", "500"))   # subset of the 1319-row test split
BATCH     = int(os.environ.get("BATCH", "32"))
MAX_NEW   = int(os.environ.get("MAX_NEW", "512"))

print("torch", torch.__version__, "cuda", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU", flush=True)

# ---- load data ------------------------------------------------------------
rows = []
with open(GSM8K_CSV, newline="") as f:
    for r in csv.DictReader(f):
        rows.append((r["question"], r["answer"]))
rows = rows[:N_EVAL]
print(f"loaded {len(rows)} GSM8K test questions", flush=True)

def gold_answer(ans):
    # gold is the number after the '####' marker
    m = re.search(r"####\s*([-\d,\.]+)", ans)
    return m.group(1).replace(",", "").strip().rstrip(".") if m else None

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def pred_answer(text):
    # prefer an explicit "answer is X"; else the last number in the completion
    m = re.findall(r"(?:answer is|answer:|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", text, re.I)
    cands = m if m else NUM_RE.findall(text)
    if not cands:
        return None
    return cands[-1].replace(",", "").strip().rstrip(".")

def num_eq(a, b):
    try:
        return a is not None and b is not None and abs(float(a) - float(b)) < 1e-4
    except ValueError:
        return a == b

# ---- load model -----------------------------------------------------------
tok = AutoTokenizer.from_pretrained(MODEL_DIR)
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR, torch_dtype=torch.float16, device_map="cuda")
model.eval()

SYS = ("You are a careful math assistant. Solve the problem step by step, "
       "then give the final answer on a new line as 'The answer is <number>'.")

def build_prompt(q):
    msgs = [{"role": "system", "content": SYS},
            {"role": "user", "content": q}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

# ---- run ------------------------------------------------------------------
correct, results = 0, []
t0 = time.time()
for i in range(0, len(rows), BATCH):
    batch = rows[i:i + BATCH]
    prompts = [build_prompt(q) for q, _ in batch]
    enc = tok(prompts, return_tensors="pt", padding=True).to("cuda")
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=MAX_NEW, do_sample=False,
                             pad_token_id=tok.pad_token_id)
    gen = out[:, enc["input_ids"].shape[1]:]
    texts = tok.batch_decode(gen, skip_special_tokens=True)
    for (q, gold), comp in zip(batch, texts):
        g, p = gold_answer(gold), pred_answer(comp)
        ok = num_eq(p, g)
        correct += ok
        results.append({"question": q, "gold": g, "pred": p, "correct": bool(ok),
                        "completion": comp})
    done = min(i + BATCH, len(rows))
    print(f"[{done}/{len(rows)}] running acc = {correct/done:.4f} "
          f"({time.time()-t0:.0f}s)", flush=True)

acc = correct / len(rows)
summary = {"model": "Qwen2.5-1.5B-Instruct", "dataset": "GSM8K main_test",
           "n": len(rows), "correct": correct, "accuracy": acc,
           "batch": BATCH, "max_new_tokens": MAX_NEW,
           "seconds": round(time.time() - t0, 1)}
print("SUMMARY", json.dumps(summary), flush=True)
os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
with open(os.path.join(OUT_DIR, "predictions.jsonl"), "w") as f:
    for r in results:
        f.write(json.dumps(r) + "\n")
print("wrote summary.json + predictions.jsonl", flush=True)
