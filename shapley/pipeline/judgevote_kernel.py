# KHẢO SÁT: Judge-vote (K=3 Judge độc lập) có nâng chất lượng Judge không?
#
# Bối cảnh (docs/SOLVEJUDGE.md): Judge 1.5B binary là điểm nghẽn — MATH prec .52 (39 false-pos),
# GSM8K prec .33 (chê sai 70/84 câu đúng). Câu hỏi: chạy K Judge độc lập (nhiệt độ khác) rồi
# lấy đồng thuận (>=2/3 "đúng") có làm prec/rec so với Judge đơn không?
#
# Không chạy lại pipeline — dùng lời giải S1 (sols[0]) + gold từ traces solvejudge ĐÃ CÓ.
# Mỗi câu: K Judge độc lập đọc cùng (problem, S1). Xuất ma trận nhầm lẫn theo ngưỡng vote.
#
# Ngưỡng vote:
#   judge1   : chỉ Judge greedy (mốc, = baseline hiện tại)
#   vote2/3  : >=2/3 Judge đồng thuận "đúng" -> coi là ĐÚNG (dừng)
#   vote3/3  : cả 3 đều "đúng" -> coi là ĐÚNG
# Đo precision/recall của từng ngưỡng so với S1-correct thực tế.
import os, re, json, glob, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "__TASK__"     # "math" | "gsm8k"
BS   = __BS__
K    = 3
TEMPS = [1.0, 0.7, 0.4]

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
print(f"TASK={TASK} K={K} TEMPS={TEMPS}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="auto").eval()
print("model loaded", flush=True)

JUDGE_SYS = ("You are a strict math judge. You are given a problem and a proposed solution. "
             "Reply with a single digit: 1 if the solution is correct, 0 if it is wrong.")

def gen(sysm, usrs, mx=8, temp=1.0, seed=None):
    if seed is not None:
        torch.manual_seed(seed)
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = [tok.apply_chat_template([{"role": "system", "content": sysm},
                                       {"role": "user", "content": u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=(temp < 1.0),
                               temperature=temp, pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    return outs

def read_digit(t):
    m = re.search(r"[01]", t or "")
    return int(m.group(0)) if m else None

# ---- nạp traces solvejudge (chứa sols[0] + gold cho từng idx) ----
# kernel mount dataset chứa traces? Traces không nằm trong dataset public.
# Thay vào đó: kernel NHẬN trực tiếp (problem, solution, gold) qua placeholder? Không khả thi.
# Giải pháp: kernel đọc từ trace file đẩy lên dataset của account. Ở đây ta đẩy traces qua
# kernel_sources (kernel nối tiếp) — nhưng traces không public. Dùng file gắn vào dataset.

# Cách thực tế: tự build input. Kernel chạy trên MATH-500 test, lấy 150 câu đầu,
# và lời giải S1 = chính kernel tự sinh (greedy, giống hệt solvejudge v1).
# Vậy không cần traces — ta tái tạo S1 greedily rồi judge K lần.
FNAME = "math_500_test.csv" if TASK == "math" else "main_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
import csv
ALL = list(csv.DictReader(open(CSV, encoding="utf-8")))[:150]
if TASK == "math":
    q_of = lambda r: r["Question"].strip()
    def gold_of(r):
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
        return boxed(r["Answer"])
    SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the "
                 "final answer in \\boxed{}.")
else:
    q_of = lambda r: r["question"].strip()
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                 "End with a line: 'The answer is <number>'.")

# tái tạo S1 greedy (khớp solvejudge v1)
def pred_math(t):
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
    b = boxed(t)
    if b is not None: return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
    return m[-1].strip() if m else None
NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def pred_gsm(t):
    m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
    cands = m if m else NUM_RE.findall(t or "")
    return cands[-1].replace(",", "") if cands else None
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

qs = [q_of(r) for r in ALL]
gs = [gold_of(r) for r in ALL]
n = len(ALL)

# S1 greedy (dùng SOLVE_SYS, không phải JUDGE_SYS)
S1 = gen(SOLVE_SYS, [f"{q}" for q in qs], 1024, temp=1.0)
pred_fn = pred_math if TASK == "math" else pred_gsm
s1_ok = [eq(pred_fn(t), g) for t, g in zip(S1, gs)]
print(f"S1 acc: {sum(s1_ok)/n:.3f}", flush=True)

# K Judge độc lập (dùng JUDGE_SYS)
judges = []
for k in range(K):
    j = gen(JUDGE_SYS, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, S1)], 8,
            temp=TEMPS[k], seed=2000 + k)
    judges.append([read_digit(t) for t in j])
    print(f"  judge{k+1} parsed: {sum(1 for x in judges[k] if x is not None)}/{n}", flush=True)

# ngưỡng vote
def verdict(threshold):
    """threshold = số Judge 'đúng' tối thiểu để coi là ĐÚNG."""
    out = []
    for i in range(n):
        yes = sum(1 for k in range(K) if judges[k][i] == 1)
        out.append(1 if yes >= threshold else 0)
    return out

def prec_rec(pred_binary, truth_binary):
    tp = sum(1 for i in range(n) if pred_binary[i] == 1 and truth_binary[i])
    fp = sum(1 for i in range(n) if pred_binary[i] == 1 and not truth_binary[i])
    fn = sum(1 for i in range(n) if pred_binary[i] == 0 and truth_binary[i])
    p = tp / max(1, tp + fp)
    r = tp / max(1, tp + fn)
    return p, r, tp, fp, fn

results = {}
for label, thr in (("judge1", 1), ("vote2of3", 2), ("vote3of3", 3)):
    v = verdict(thr)
    p, r, tp, fp, fn = prec_rec(v, s1_ok)
    results[label] = {"prec": p, "rec": r, "tp": tp, "fp": fp, "fn": fn,
                      "n_judge_yes": sum(v)}
    print(f"{label}: prec {p:.3f} rec {r:.3f} | tp {tp} fp {fp} fn {fn} | "
          f"judge-yes {sum(v)}/{n}")

# dừng-sớm mô phỏng: nếu Judge nói đúng -> lấy S1 (loop stop@1). acc đáp án cuối
# cho từng ngưỡng = prec của verdict (vì lấy S1 khi verdict=1, sai khi verdict=0 thì phải re-solve
# — không khảo sát re-solve, chỉ đo chất lượng Judge).
json.dump({"task": TASK, "n": n, "s1_acc": sum(s1_ok)/n,
           "judge_agreement": sum(1 for i in range(n)
                                  if len({judges[k][i] for k in range(K)}) == 1) / n,
           "results": results},
          open("/kaggle/working/judgevote.json", "w"), indent=2, ensure_ascii=False)
print("\nS1 acc:", round(sum(s1_ok)/n, 3))
print("judge agreement (3/3 same):", round(sum(1 for i in range(n)
      if len({judges[k][i] for k in range(K)}) == 1) / n, 3))
print("done", flush=True)