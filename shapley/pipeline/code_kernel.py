# CODE (HumanEval) — kiểm định ĐỊNH LUẬT BÁO ĐỘNG GIẢ bằng một verifier CHÍNH XÁC TUYỆT ĐỐI.
# Ở MATH, verifier là LLM -> báo động giả 42-72% -> can thiệp càng nhiều càng hại.
# Ở CODE, verifier có thể là BỘ CHẠY TEST -> báo động giả = 0 theo định nghĩa.
# Câu hỏi quyết định: khi false-alarm = 0 thì lặp NHIỀU VÒNG có còn hại nữa không?
#   Nếu KHÔNG hại (tăng đều) -> chứng minh cơ chế là BÁO ĐỘNG GIẢ, không phải "lặp nhiều là xấu".
# 4 nhánh, cùng bài, so từng câu:
#   A: sinh code, không verify                      (mốc, pass@1)
#   B: LLM (1.5B) tự soát post-hoc                  (verifier PHÁN ĐOÁN)
#   C: chạy test + sửa 1 vòng                       (verifier CHÍNH XÁC, 1 can thiệp)
#   D: chạy test + sửa 3 vòng                       (verifier CHÍNH XÁC, NHIỀU can thiệp)
# Đo THÊM (chỉ code mới làm được): precision/recall THẬT của verifier LLM, vì có test làm chân lý.
import os, re, csv, json, glob, subprocess, tempfile, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N = __N__
BS = __BS__
ROUNDS = 3
TIMEOUT = 8

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True) or \
     glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
CSV = sorted(glob.glob("/kaggle/input/**/test.csv", recursive=True), key=len)[0]
rows = list(csv.DictReader(open(CSV)))[:N]
print("MODEL:", MODEL, "| n =", len(rows), flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
if __QUANT__:                      # 7B: nf4 để vừa 1xT4 (fp16 15GB không vừa 16GB)
    import sys
    subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])
    from transformers import BitsAndBytesConfig
    _b = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL, quantization_config=_b, device_map="auto").eval()
else:
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16, device_map="cuda").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx=512):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i+BS]
        ps = [tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False, pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    return outs

def extract(t):
    """Lấy code từ khối ```python ... ``` nếu có."""
    m = re.findall(r"```(?:python)?\s*\n(.*?)```", t or "", re.S)
    return (m[0] if m else (t or "")).strip()

def run_tests(code, test, entry):
    """Chạy thật: trả (pass?, thông báo lỗi rút gọn). Đây là VERIFIER CHÍNH XÁC."""
    prog = f"{code}\n\n{test}\n\ncheck({entry})\n"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(prog); path = f.name
    try:
        r = subprocess.run(["python", path], capture_output=True, text=True, timeout=TIMEOUT)
        if r.returncode == 0: return True, ""
        err = (r.stderr or "").strip().splitlines()
        return False, "\n".join(err[-4:])[:400]
    except subprocess.TimeoutExpired:
        return False, "TimeoutError: code did not finish (possible infinite loop)"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"[:300]
    finally:
        try: os.unlink(path)
        except Exception: pass

prompts = [r["prompt"] for r in rows]
tests   = [r["test"] for r in rows]
entries = [r["entry_point"] for r in rows]

SOLVE = ("Complete the Python function. Return the COMPLETE function including the signature, "
         "inside a ```python code block. No explanation.")
LLMV  = ("You are reviewing Python code against its specification. If the code is correct, reply exactly 'OK'. "
         "If it is wrong, reply 'WRONG' followed by the corrected COMPLETE function in a ```python block.")
REPAIR = ("The code failed its tests. Fix it. Return the COMPLETE corrected function "
          "inside a ```python block. No explanation.")

# ---------- A: sinh code, không verify ----------
codeA = [extract(t) for t in gen(SOLVE, prompts, 512)]
okA = [run_tests(codeA[i], tests[i], entries[i])[0] for i in range(len(rows))]
print(f"[A no-verify] pass@1 = {sum(okA)/len(rows):.3f}", flush=True)

# ---------- B: LLM tự soát (verifier PHÁN ĐOÁN) ----------
vout = gen(LLMV, [f"Specification:\n{prompts[i]}\n\nCode:\n```python\n{codeA[i]}\n```"
                  for i in range(len(rows))], 512)
codeB = list(codeA); flagged = 0; false_alarm = 0; missed = 0; caught = 0
for i, v in enumerate(vout):
    says_wrong = v.strip().upper().startswith("WRONG")
    if says_wrong:
        flagged += 1
        if okA[i]: false_alarm += 1      # code VỐN ĐÚNG mà bị kêu sai  <- BÁO ĐỘNG GIẢ (đo chính xác)
        else:      caught += 1           # bắt đúng bài lỗi
        c = extract(v.split("WRONG", 1)[-1])
        if c and "def " in c: codeB[i] = c
    else:
        if not okA[i]: missed += 1       # code SAI mà bảo OK
okB = [run_tests(codeB[i], tests[i], entries[i])[0] for i in range(len(rows))]
n_bad = sum(1 for x in okA if not x)
resB = {"acc": round(sum(okB)/len(rows),4),
        "flagged": flagged,
        "false_alarm": false_alarm,
        "false_alarm_rate": round(false_alarm/max(sum(okA),1),3),   # trong số code ĐÚNG, bao nhiêu bị kêu sai
        "caught": caught, "missed": missed,
        "recall_on_bugs": round(caught/max(n_bad,1),3),
        "fix_vs_A": sum(1 for i in range(len(rows)) if okB[i] and not okA[i]),
        "break_vs_A": sum(1 for i in range(len(rows)) if okA[i] and not okB[i])}
print(f"[B llm-verify] {resB}", flush=True)

# ---------- C/D: verifier CHÍNH XÁC (chạy test) + sửa, theo vòng ----------
codeR = list(codeA)
okR = list(okA)
acc_by_round = [round(sum(okA)/len(rows), 4)]
fix_r, brk_r = [], []
for rd in range(1, ROUNDS+1):
    bad = [i for i in range(len(rows)) if not okR[i]]     # CHỈ đụng bài đang FAIL -> báo động giả = 0
    if not bad:
        acc_by_round.append(acc_by_round[-1]); fix_r.append(0); brk_r.append(0); continue
    errs = [run_tests(codeR[i], tests[i], entries[i])[1] for i in bad]
    fixes = gen(REPAIR, [f"Specification:\n{prompts[i]}\n\nCode:\n```python\n{codeR[i]}\n```"
                         f"\n\nTest failure:\n{e}" for i, e in zip(bad, errs)], 512)
    f_, b_ = 0, 0
    for pos, i in enumerate(bad):
        c = extract(fixes[pos])
        if not c or "def " not in c: continue
        p, _ = run_tests(c, tests[i], entries[i])
        if p and not okR[i]: f_ += 1
        if not p and okR[i]: b_ += 1
        codeR[i] = c; okR[i] = p
    acc_by_round.append(round(sum(okR)/len(rows), 4)); fix_r.append(f_); brk_r.append(b_)
    print(f"  [exec-repair round {rd}] acc = {acc_by_round[-1]} (+{f_} fixed)", flush=True)

resC = {"acc": acc_by_round[1] if len(acc_by_round) > 1 else acc_by_round[0]}
resD = {"acc": acc_by_round[-1], "acc_by_round": acc_by_round,
        "fix_by_round": fix_r, "break_by_round": brk_r,
        "break_total": sum(brk_r),
        "fix_vs_A": sum(1 for i in range(len(rows)) if okR[i] and not okA[i]),
        "break_vs_A": sum(1 for i in range(len(rows)) if okA[i] and not okR[i])}
print(f"[C exec-repair 1 round] {resC}", flush=True)
print(f"[D exec-repair 3 rounds] {resD}", flush=True)

out = {"n": len(rows),
       "A_noverify": {"acc": round(sum(okA)/len(rows),4)},
       "B_llm_verify": resB,
       "C_exec_repair_1": resC,
       "D_exec_repair_3": resD}
print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json","w"), indent=2)
