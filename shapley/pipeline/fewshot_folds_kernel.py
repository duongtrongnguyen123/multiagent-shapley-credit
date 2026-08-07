# FEW-SHOT x 5 FOLD — đặt thanh sai số lên kết quả few-shot.
# Bối cảnh: H13 (docs/RESULTS.md mục 0) đo được sàn nhiễu GSM8K std 2.65, ngưỡng 2-sigma ~5 điểm
# ở n<=250. MATH còn nhiễu hơn (PS dao động .34-.48 giữa các fold). Vòng fewshot n=30 trước đó
# cho acc 0.30-0.40 — CHÊNH LỆCH ĐÓ NẰM TRONG NHIỄU, không kết luận được.
#
# Kernel này chạy CÙNG lưới 5 nhánh trên 5 FOLD RỜI NHAU và báo cáo mean / min / max / std,
# cùng số fold cùng dấu — đúng chuẩn H13/H14 của dự án.
#
# HAI NHÓM CHỈ SỐ, ĐỘ TIN CẬY KHÁC NHAU:
#   (a) HÌNH THỨC PLAN (has_boxed, has_equals, digit_count, leaks_answer) — thay đổi hành vi
#       lớn và ổn định, đọc được ngay cả ở n nhỏ.
#   (b) ACCURACY — chỉ đọc được KHI có thanh sai số qua 5 fold. Đây là lý do kernel này tồn tại.
# Lưu trace thô theo quy tắc mới của dự án (mọi kernel phải giữ mẫu output để kiểm lại được).
import os, re, csv, json, glob, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK   = "__TASK__"
N      = __N__          # tổng số bài, chia đều cho NF fold
NF     = __NF__
BS     = __BS__

FOLD = N // NF
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "main_test.csv" if TASK == "gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} {NF} fold x {FOLD} bai = {len(ALL)}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="cuda").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx, shots=()):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = []
        for u in ch:
            msgs = [{"role": "system", "content": sysm}]
            for su, sa in shots:
                msgs += [{"role": "user", "content": su}, {"role": "assistant", "content": sa}]
            msgs.append({"role": "user", "content": u})
            ps.append(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False,
                               pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    return outs

# ---- chấm điểm; normalizer ĐÃ VÁ dấu LaTeX bao ngoài (lỗi fc2f429 của dự án) --
def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0: return None
    i = s.find("{", i); d = 0; st = i
    for j in range(i, len(s)):
        if s[j] == "{": d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0: return s[st + 1:j]
    return None
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def norm(a):
    if a is None: return None
    a = str(a).strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " ", ","]: a = a.replace(x, "")
    for x in ["\\(", "\\)", "\\[", "\\]"]: a = a.replace(x, "")   # <-- vá lỗi normalizer
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()
def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g: return False
    if p == g: return True
    try: return abs(float(p) - float(g)) < 1e-6
    except: return False

if TASK == "gsm8k":
    PLAN_SYS  = ("You are a math planning assistant. Read the problem and give a concise "
                 "numbered plan of the steps needed. Do NOT compute the final answer.")
    SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                 "End with a line: 'The answer is <number>'.")
    PLAN_MX, SOLVE_MX = 256, 512
    q_of = lambda r: r["question"]
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    def pred(t):
        m = (re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
             or NUM.findall(t or ""))
        return m[-1].replace(",", "") if m else None
    PLAN_SHOTS = (
        ("Natalia sold clips to 48 of her friends in April, and then she sold half as many "
         "clips in May. How many clips did Natalia sell altogether in April and May?",
         "1. Note the number of clips sold in April, given directly in the problem.\n"
         "2. Express May's sales as the stated fraction of April's sales.\n"
         "3. Add the two monthly amounts to obtain the total."),
        ("Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of "
         "babysitting. How much did she earn?",
         "1. Identify the hourly rate stated in the problem.\n"
         "2. Convert the babysitting duration from minutes into a fraction of an hour.\n"
         "3. Multiply the rate by that fraction to obtain the earnings."),
    )
    SOLVE_SHOTS = (
        ("Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of "
         "babysitting. How much did she earn?\n\nSuggested plan:\n"
         "1. Rate is $12 per hour.\n2. 50 minutes = 50/60 hour.\n3. 12 * 50/60 = 10. "
         "The answer is 10.",
         "I will not rely on the plan's arithmetic; I recompute every step.\n\n"
         "Step 1. The rate is $12 per hour.\n"
         "Step 2. 50 minutes as a fraction of an hour: 50 / 60 = 5/6 hour.\n"
         "Step 3. Earnings: 12 * 5/6 = 60/6 = 10.\n"
         "Check: 12 per hour means 1 per 5 minutes, and 50 minutes is ten 5-minute blocks, "
         "so 10 * 1 = 10. Consistent.\n\n"
         "The answer is 10."),
    )
else:
    PLAN_SYS  = ("You are a math planning assistant. Read the competition problem and give a "
                 "concise numbered plan of the solution steps. Do NOT compute the final answer.")
    SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the final "
                 "answer in \\boxed{}.")
    PLAN_MX, SOLVE_MX = 512, 1024
    q_of = lambda r: r["Question"]
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None
    PLAN_SHOTS = (
        ("What is the value of $\\sqrt{36+64}-\\sqrt{25-16}$?",
         "1. Simplify the sum inside the first radical, then take its square root.\n"
         "2. Simplify the difference inside the second radical, then take its square root.\n"
         "3. Subtract the second root from the first."),
        ("If $x = 2$ and $y = 5$, then what is the value of $\\frac{x^4+2y^2}{6}$?",
         "1. Substitute the given values for the two variables into the numerator.\n"
         "2. Evaluate the fourth-power term and the doubled square term separately.\n"
         "3. Add those terms, then divide by the denominator and reduce the fraction."),
    )
    SOLVE_SHOTS = (
        ("What is the value of $\\sqrt{36+64}-\\sqrt{25-16}$?\n\nSuggested plan:\n"
         "1. sqrt(36+64) = sqrt(100) = 10.\n2. sqrt(25-16) = sqrt(9) = 3.\n"
         "3. 10 - 3 = 7. So the answer is $\\boxed{7}$.",
         "I will not rely on the plan's arithmetic; I recompute every step.\n\n"
         "Step 1. Inside the first radical: $36 + 64 = 100$, and $\\sqrt{100} = 10$.\n"
         "Step 2. Inside the second radical: $25 - 16 = 9$, and $\\sqrt{9} = 3$.\n"
         "Step 3. Subtract: $10 - 3 = 7$.\n"
         "Check: $10^2 = 100$ and $3^2 = 9$, so both roots are exact.\n\n"
         "$\\boxed{7}$"),
    )

PLAN_FS_SYS  = PLAN_SYS + (" Describe each step in words only. Write no arithmetic expression, "
                           "no equals sign, and no numeric result.")
SOLVE_FS_SYS = SOLVE_SYS + (" A suggested plan may be provided. Treat it only as a hint about "
                            "which steps to take: recompute every value yourself and show the "
                            "arithmetic. Never restate the plan's answer without redoing the work.")

def plan_answer(p):
    b = boxed(p)
    if b is not None: return b
    m = NUM.findall(p or "")
    return m[-1].replace(",", "") if m else None

ARMS = ["NP_no_plan", "bP_bS_baseline", "fP_bS_fewshot_planner",
        "bP_fS_fewshot_solver", "fP_fS_both"]

per_fold = {a: [] for a in ARMS}
plan_fold = {"base": [], "fewshot": []}
sample_traces = []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    print(f"\n===== FOLD {f+1}/{NF} ({len(rows)} bai) =====", flush=True)

    plan_b = gen(PLAN_SYS, qs, PLAN_MX)
    plan_f = gen(PLAN_FS_SYS, qs, PLAN_MX, shots=PLAN_SHOTS)
    wp_b = [f"{q}\n\nSuggested plan:\n{p}" for q, p in zip(qs, plan_b)]
    wp_f = [f"{q}\n\nSuggested plan:\n{p}" for q, p in zip(qs, plan_f)]

    cfg = {
        "NP_no_plan":            (SOLVE_SYS,    list(qs), (),          None),
        "bP_bS_baseline":        (SOLVE_SYS,    wp_b,     (),          plan_b),
        "fP_bS_fewshot_planner": (SOLVE_SYS,    wp_f,     (),          plan_f),
        "bP_fS_fewshot_solver":  (SOLVE_FS_SYS, wp_b,     SOLVE_SHOTS, plan_b),
        "fP_fS_both":            (SOLVE_FS_SYS, wp_f,     SOLVE_SHOTS, plan_f),
    }
    sols = {}
    for tag, (sysm, usrs, shots, pl) in cfg.items():
        ss = gen(sysm, usrs, SOLVE_MX, shots=shots)
        sols[tag] = ss
        a = [pred(s) for s in ss]
        acc = sum(eq(x, g) for x, g in zip(a, gs)) / len(gs)
        copy = (0.0 if pl is None else
                sum(1 for s, p in zip(ss, pl)
                    if pred(s) is not None and plan_answer(p) is not None
                    and eq(pred(s), plan_answer(p))) / len(ss))
        per_fold[tag].append({"acc": round(acc, 4), "copycat": round(copy, 4),
                              "median_len": int(statistics.median(len(s or "") for s in ss))})
        print(f"  [fold{f+1}] {tag:<24} acc={acc:.4f} copycat={copy:.3f}", flush=True)

    for nm, ps in (("base", plan_b), ("fewshot", plan_f)):
        leak = sum(1 for p, g in zip(ps, gs) if g is not None and eq(plan_answer(p), g)) / len(ps)
        plan_fold[nm].append({
            "leaks_correct_answer": round(leak, 4),
            "has_boxed": round(sum(1 for p in ps if "\\boxed" in p) / len(ps), 4),
            "has_equals_sign": round(sum(1 for p in ps if "=" in p) / len(ps), 4),
            "median_digit_count": int(statistics.median(sum(c.isdigit() for c in p) for p in ps)),
            "median_len": int(statistics.median(len(p) for p in ps))})
    print(f"  [fold{f+1}] plan base leak={plan_fold['base'][-1]['leaks_correct_answer']:.3f} "
          f"| fewshot leak={plan_fold['fewshot'][-1]['leaks_correct_answer']:.3f}", flush=True)

    # LƯU MỌI CÂU, MỌI FOLD: output nguyên văn của từng vai + đáp án trích ra + đúng/sai,
    # để phân tích ngoại tuyến không phải chạy lại.
    for i in range(len(rows)):
        sample_traces.append({
            "fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
            "plan_base": plan_b[i], "plan_fewshot": plan_f[i],
            "plan_leak": {"base": plan_answer(plan_b[i]), "fewshot": plan_answer(plan_f[i])},
            **{f"sol_{t}": sols[t][i] for t in ARMS},
            "pred": {t: pred(sols[t][i]) for t in ARMS},
            "ok": {t: eq(pred(sols[t][i]), gs[i]) for t in ARMS},
            "len": {"plan_base": len(plan_b[i]), "plan_fewshot": len(plan_f[i]),
                    **{t: len(sols[t][i] or "") for t in ARMS}},
        })
        # ghi ngay sau MỖI câu: dòng JSONL nối thêm, không mất gì kể cả khi bị cắt giữa fold
        with open("/kaggle/working/traces.jsonl", "a") as fh:
            fh.write(json.dumps(sample_traces[-1]) + "\n")

    # CHECKPOINT sau MỖI fold (bài học từ vòng debate: ghi ở dòng cuối = mất trắng khi bị cắt)
    json.dump({"task": TASK, "folds_done": f + 1, "n_folds": NF, "fold_size": FOLD,
               "complete": f + 1 == NF, "per_fold": per_fold, "plan_per_fold": plan_fold},
              open("/kaggle/working/summary.json", "w"), indent=2)
    json.dump(sample_traces, open("/kaggle/working/traces.json", "w"), indent=1)
    print(f"  [checkpoint] da ghi {f+1}/{NF} fold, {len(sample_traces)} cau", flush=True)

# ---- tổng hợp qua fold -----------------------------------------------------
def stats(xs):
    return {"mean": round(statistics.mean(xs), 4), "min": round(min(xs), 4),
            "max": round(max(xs), 4), "range": round(max(xs) - min(xs), 4),
            "std": round(statistics.pstdev(xs), 4) if len(xs) > 1 else 0.0}

out = {"task": TASK, "n_total": len(ALL), "n_folds": NF, "fold_size": FOLD,
       "arms": {}, "plan": {}, "per_fold": per_fold}
for tag in ARMS:
    accs = [d["acc"] for d in per_fold[tag]]
    out["arms"][tag] = {"acc": stats(accs), "acc_by_fold": accs,
                        "copycat_mean": round(statistics.mean(d["copycat"]
                                                              for d in per_fold[tag]), 4)}
for nm in ("base", "fewshot"):
    out["plan"][nm] = {k: stats([d[k] for d in plan_fold[nm]])
                       for k in ("leaks_correct_answer", "has_boxed", "has_equals_sign",
                                 "median_digit_count", "median_len")}

# hiệu so với baseline, TỪNG FOLD — chỉ số quyết định
base_by_fold = [d["acc"] for d in per_fold["bP_bS_baseline"]]
print("\n" + "=" * 74, flush=True)
print(f"{'nhanh':<24} {'mean':>7} {'min':>7} {'max':>7} {'range':>7} {'fold cung dau':>14}",
      flush=True)
print("=" * 74, flush=True)
for tag in ARMS:
    diffs = [a - b for a, b in zip([d["acc"] for d in per_fold[tag]], base_by_fold)]
    same = sum(1 for d in diffs if d > 0) if statistics.mean(diffs) > 0 else \
           sum(1 for d in diffs if d < 0)
    s = stats(diffs)
    out["arms"][tag]["delta_vs_baseline"] = {**s, "by_fold": [round(d, 4) for d in diffs],
                                             "folds_same_sign": f"{same}/{NF}"}
    print(f"{tag:<24} {s['mean']:>+7.3f} {s['min']:>+7.3f} {s['max']:>+7.3f} "
          f"{s['range']:>7.3f} {same:>10}/{NF}", flush=True)

print("\n--- PLAN: hinh thuc (mean qua 5 fold) ---", flush=True)
for nm in ("base", "fewshot"):
    p = out["plan"][nm]
    print(f"  {nm:<8} leak={p['leaks_correct_answer']['mean']:.3f} "
          f"boxed={p['has_boxed']['mean']:.3f} equals={p['has_equals_sign']['mean']:.3f} "
          f"digits={p['median_digit_count']['mean']:.1f} len={p['median_len']['mean']:.0f}",
          flush=True)

print(f"\nDOC KET QUA: hieu ung chi tinh la bang chung khi TOAN BO {NF} fold cung dau "
      f"(chuan H13/H14). Hieu ung <5 diem do MOT LAN khong phai bang chung.", flush=True)
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump(sample_traces, open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)
