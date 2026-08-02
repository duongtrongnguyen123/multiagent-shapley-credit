# PROBE: can Qwen2.5-7B-Instruct load + run offline on a single T4? Tests 4-bit
# (bitsandbytes) then fp16 fallback, runs 8 GSM8K questions. Cheap go/no-go before
# committing 16 accounts to a heterogeneous-role round.
import os, re, csv, json, time, glob, traceback
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def find_one(p, w):
    h = glob.glob(p, recursive=True)
    if not h:
        raise FileNotFoundError(f"{w}: {p} :: {glob.glob('/kaggle/input/**', recursive=True)[:40]}")
    return sorted(h, key=len)[0]

MODEL_DIR = os.path.dirname(find_one("/kaggle/input/**/model.safetensors.index.json", "7B model"))
GSM8K_CSV = find_one("/kaggle/input/**/main_test.csv", "gsm8k")
print("MODEL_DIR", MODEL_DIR, flush=True)
print("torch", torch.__version__, "gpu",
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU", flush=True)

try:
    import bitsandbytes as bnb
    print("bitsandbytes OK", bnb.__version__, flush=True)
    HAS_BNB = True
except Exception as e:
    print("bitsandbytes IMPORT FAILED:", e, flush=True)
    HAS_BNB = False

tok = AutoTokenizer.from_pretrained(MODEL_DIR)
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

result = {"has_bnb": HAS_BNB}
model, mode = None, None
if HAS_BNB:
    try:
        from transformers import BitsAndBytesConfig
        bnb_cfg = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                                     bnb_4bit_quant_type="nf4")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_DIR, quantization_config=bnb_cfg, device_map="cuda")
        mode = "4bit"
    except Exception:
        print("4bit load failed:\n", traceback.format_exc(), flush=True)
if model is None:
    try:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_DIR, torch_dtype=torch.float16, device_map="auto")
        mode = "fp16"
    except Exception:
        print("fp16 load failed:\n", traceback.format_exc(), flush=True)
        result["load"] = "FAILED"
        json.dump(result, open("/kaggle/working/probe.json", "w"), indent=2)
        raise
model.eval()
result["mode"] = mode
print("LOADED mode=", mode, "mem_GB=",
      round(torch.cuda.memory_allocated() / 1e9, 2), flush=True)

rows = []
with open(GSM8K_CSV, newline="") as f:
    for r in csv.DictReader(f):
        rows.append((r["question"], r["answer"]))
rows = rows[:8]

def gold(a):
    m = re.search(r"####\s*([-\d,\.]+)", a)
    return m.group(1).replace(",", "").strip().rstrip(".") if m else None
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def pred(t):
    m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t, re.I)
    c = m if m else NUM.findall(t)
    return c[-1].replace(",", "").strip().rstrip(".") if c else None

SYS = ("You are a careful math solver. Solve step by step. End with "
       "'The answer is <number>'.")
prompts = [tok.apply_chat_template(
    [{"role": "system", "content": SYS}, {"role": "user", "content": q}],
    tokenize=False, add_generation_prompt=True) for q, _ in rows]
t0 = time.time()
enc = tok(prompts, return_tensors="pt", padding=True).to("cuda")
with torch.no_grad():
    out = model.generate(**enc, max_new_tokens=512, do_sample=False, pad_token_id=tok.pad_token_id)
texts = tok.batch_decode(out[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
correct = sum(pred(t) == gold(a) or (pred(t) and gold(a) and abs(float(pred(t)) - float(gold(a))) < 1e-4)
              for t, (_, a) in zip(texts, rows))
result.update({"n": len(rows), "correct": int(correct), "seconds": round(time.time() - t0, 1),
               "peak_mem_GB": round(torch.cuda.max_memory_allocated() / 1e9, 2)})
print("PROBE_RESULT", json.dumps(result), flush=True)
json.dump(result, open("/kaggle/working/probe.json", "w"), indent=2)
