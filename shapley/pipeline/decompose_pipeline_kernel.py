# PIPELINE: Planner decompose bài -> chuỗi sub-question -> Solver trả lời từng sub (kế thừa bước
# trước) -> final = answer sub-question cuối. Không dùng Verifier/Aggregator.
#
# Khảo sát (decompose_survey): Planner 1.5B parse_rate GSM8K 1.00, MATH 0.70. MATH fail do regex
# bắt được mảng lồng nhau '["p"],["q"]'. Kernel này dùng parser JSON robust: thử json.loads cả
# output, fallback từng mảng con, chọn mảng chuỗi dài nhất.
#
# Vòng lặp Solver theo từng sub-question:
#   sub[0]: "giải sub-question (kèm context bài gốc)"
#   sub[i]: "dựa trên kết quả sub-question trước là <answer_{i-1}>, giải sub-question i"
#   final  = answer của sub-question cuối
# Risky: lỗi dồn tích (sub i sai -> sub i+1 nhận sai).
import os, re, json, csv, glob, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "__TASK__"     # math | gsm8k
N    = __N__
NF   = __NF__
BS   = __BS__

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "math_500_test.csv" if TASK == "math" else "main_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV, encoding="utf-8")))[:N]
print(f"TASK={TASK} N={N} NF={NF}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="auto").eval()
print("model loaded", flush=True)

DECOMPOSE_SYS = (
    "You are a mathematical problem decomposition planner.\n\n"
    "Your task is to decompose the given original problem into a sequence of small, logically "
    "ordered sub-questions.\n\n"
    "The sub-questions must form a STRICT SEQUENTIAL CHAIN.\n\n"
    "For each sub-question i > 1:\n"
    "- It must be solvable using the original problem, the sub-question itself, and the answer "
    "produced for sub-question i-1.\n"
    "- It must make meaningful use of the previous answer.\n"
    "- Do not require answers from earlier steps other than the immediately previous answer.\n"
    "- Do not solve any sub-question yourself.\n"
    "- Do not compute the final answer.\n"
    "- Do not include explanations, solutions, calculations, or answers.\n"
    "- Do not introduce information that is not present or logically implied by the original "
    "problem.\n\n"
    "The final sub-question must directly determine the final answer to the original problem.\n\n"
    "A good decomposition should:\n"
    "1. Break a complex problem into simple atomic questions.\n"
    "2. Preserve the logical dependency between consecutive steps.\n"
    "3. Ensure that each step produces information needed by the next step.\n"
    "4. Avoid redundant or unnecessary steps.\n"
    "5. End with a sub-question whose answer is the final answer.\n\n"
    "Return ONLY valid JSON using exactly this format:\n\n"
    "{\n"
    "  \"sub_questions\": [\n"
    "    {\"id\": 1, \"question\": \"...\"},\n"
    "    {\"id\": 2, \"question\": \"...\"}\n"
    "  ]\n"
    "}\n\n"
    "Do not output Markdown.\nDo not output code fences.\n"
    "Do not output any text outside the JSON object.")
SOLVER_SYS = (
    "You are a step-by-step mathematical sub-question solver.\n\n"
    "You are one solver in a sequential reasoning pipeline.\n\n"
    "At each step, you receive:\n"
    "1. The original problem.\n"
    "2. The current sub-question.\n"
    "3. The answer produced by the previous step.\n\n"
    "Your task is to answer ONLY the current sub-question.\n\n"
    "IMPORTANT RULES:\n"
    "1. Do not solve the entire original problem.\n"
    "2. Do not skip the current sub-question.\n"
    "3. Use the previous answer as an input when it is relevant.\n"
    "4. Check whether the previous answer provides the information needed for the current "
    "sub-question.\n"
    "5. Perform any calculations necessary to answer the current sub-question.\n"
    "6. Your answer must be self-contained enough to be used as the previous answer for the "
    "next step.\n"
    "7. Do not assume that previous answers are necessarily correct. If the previous answer "
    "contains an error, correct it when necessary before continuing.\n"
    "8. Do not invent information that is not supported by the original problem or previous "
    "answer.\n"
    "9. Focus only on the current sub-question.\n"
    "10. The final step's answer should directly provide the answer to the original problem.\n\n"
    "Return the reasoning needed to solve the current sub-question followed by a clearly "
    "identifiable final answer.\n\n"
    "Format:\n\n"
    "Reasoning:\n<reasoning for the current sub-question>\n\n"
    "Answer:\n<answer to the current sub-question>")
SOLVE_SYS_ALONE = (
    ("You are an expert mathematician. Solve the problem step by step. Put the final answer "
     "in \\boxed{}.") if TASK == "math" else
    ("You are a careful math solver. Solve step by step, showing arithmetic. End with a line: "
     "'The answer is <number>'."))

def gen(usrs, mx, sysm=SOLVER_SYS, temp=1.0):
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
NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
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

if TASK == "math":
    q_of = lambda r: r["Question"].strip()
    def gold_of(r): return boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None
else:
    q_of = lambda r: r["question"].strip()
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    def pred(t):
        m = re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
        cands = m if m else NUM_RE.findall(t or "")
        return cands[-1].replace(",", "") if cands else None
DECOMPOSE_USER = (
    "Original problem:\n{}\n\n"
    "Decompose this problem into a strict sequential chain of atomic sub-questions.\n\n"
    "Remember:\n"
    "- Do not solve the problem.\n"
    "- Do not provide answers.\n"
    "- Each sub-question after the first must meaningfully depend on the answer to the "
    "immediately preceding sub-question.\n"
    "- The answer to the final sub-question must be the final answer to the original problem.\n\n"
    "Return only the required JSON.")

def parse_subquestions(s):
    """Parse format {'sub_questions': [{'id':1,'question':'...'}, ...]} mới.
     Trả list câu hỏi (strings), hoặc None nếu không parse được."""
    if not s:
        return None
    # 1) thử toàn output là dict
    try:
        d = json.loads(s)
        if isinstance(d, dict) and isinstance(d.get("sub_questions"), list):
            subs = d["sub_questions"]
            if subs and all(isinstance(x, dict) and isinstance(x.get("question"), str)
                            for x in subs):
                return [x["question"] for x in subs]
            # fallback nếu list string thuần
            if subs and all(isinstance(x, str) for x in subs):
                return subs
    except Exception:
        pass
    # 2) thử list string thuần (format cũ)
    try:
        arr = json.loads(s)
        if isinstance(arr, list) and arr and all(isinstance(x, str) for x in arr):
            return arr
    except Exception:
        pass
    # 3) fallback regex - tìm dict sub_questions
    m = re.search(r'\{\s*"sub_questions"\s*:\s*\[.*?\]\s*\}', s, re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            if isinstance(d, dict) and isinstance(d.get("sub_questions"), list):
                subs = [x["question"] for x in d["sub_questions"]
                        if isinstance(x, dict) and isinstance(x.get("question"), str)]
                if subs:
                    return subs
        except Exception:
            pass
    # 4) regex tìm mảng chuỗi bất kỳ
    for m in re.finditer(r'\[.*?\]', s, re.S):
        try:
            arr = json.loads(m.group(0))
            if isinstance(arr, list) and arr and all(isinstance(x, str) for x in arr):
                return arr
        except Exception:
            continue
    return None

FOLD = N // NF
fold_stats, sample = [], []
for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n}) =====", flush=True)

    # Baseline: Solver-alone (cùng bài, cùng seed, dùng SOLVE gốc)
    sol_alone = gen([f"{q}" for q in qs], 1024, sysm=SOLVE_SYS_ALONE)

    # Planner decompose
    dec = gen([DECOMPOSE_USER.format(q) for q in qs], 256, sysm=DECOMPOSE_SYS)
    subs_list = []
    parse_ok = 0
    for i, s in enumerate(dec):
        subs = parse_subquestions(s)
        subs_list.append(subs)
        if subs is not None:
            parse_ok += 1

    # Solver trả lời từng sub-question, kế thừa kết quả trước
    finals = []
    fa = None  # final answer (pred của sub cuối)
    all_answers = []  # answer từng sub (text)
    for i in range(n):
        subs = subs_list[i]
        if not subs:
            finals.append(None); all_answers.append(None); continue
        answers_txt = []
        for si, sub in enumerate(subs):
            if si == 0:
                u = (f"Original problem:\n{qs[i]}\n\nCurrent sub-question:\n{sub}\n\n"
                     f"Previous step answer:\n(none - this is the first step)")
            else:
                u = (f"Original problem:\n{qs[i]}\n\nCurrent sub-question:\n{sub}\n\n"
                     f"Previous step answer:\n{answers_txt[si-1]}")
            ans = gen([u], 256)[0]
            answers_txt.append(ans)
            prev = ans
        finals.append(answers_txt[-1] if answers_txt else None)
        all_answers.append(answers_txt)

    ok = [eq(pred(t), g) for t, g in zip(finals, gs)]
    ok_alone = [eq(pred(t), g) for t, g in zip(sol_alone, gs)]
    d = {"acc": sum(ok) / n, "acc_alone": sum(ok_alone) / n,
         "parse_rate": parse_ok / n,
         "n_sub_mean": sum(len(s) for s in subs_list if s) / max(1, sum(1 for s in subs_list if s))}
    fold_stats.append(d)
    print(f"  acc {d['acc']:.4f} | alone {d['acc_alone']:.4f} | parse {d['parse_rate']:.2f} | "
          f"n_sub {d['n_sub_mean']:.1f}", flush=True)

    for i in range(n):
        sample.append({"fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
                       "subs": subs_list[i], "answers": all_answers[i],
                       "final": finals[i], "ok": ok[i], "ok_alone": ok_alone[i]})
    json.dump({"task": TASK, "folds_done": f + 1, "n_folds": NF, "complete": f + 1 == NF,
               "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
    json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
    print(f"  [checkpoint] {f+1}/{NF}", flush=True)

def stats(xs):
    return {"mean": round(sum(xs)/len(xs), 4), "by_fold": [round(x, 4) for x in xs]}
out = {"task": TASK, "n_folds": NF, "fold_size": N // NF, "complete": True}
out["acc"] = stats([d["acc"] for d in fold_stats])
out["acc_alone"] = stats([d["acc_alone"] for d in fold_stats])
out["parse_rate"] = stats([d["parse_rate"] for d in fold_stats])
print("\nSUMMARY", json.dumps(out), flush=True)
print(f"acc mean {out['acc']['mean']:.4f} | alone {out['acc_alone']['mean']:.4f} | "
      f"parse_rate {out['parse_rate']['mean']:.2f}")
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
print("done", flush=True)