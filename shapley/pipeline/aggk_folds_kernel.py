# AGGREGATOR VỚI K ỨNG VIÊN — nó có bị đặt sai cấu hình không?
#
# docs/AGGREGATOR_EXPLAINED.md: với đúng 2 ứng viên, Aggregator chép Candidate 2 trong 94% số
# câu, và khi hai ứng viên bất đồng thì theo Verifier 43/50 lần. Prompt bảo nó "lấy đa số"
# nhưng 2 phiếu thì không bao giờ có đa số — đây là khiếm khuyết cấu hình, không hẳn là vai trò
# vô dụng. Bằng chứng ủng hộ: maj@8 được +10 điểm trên MATH 1.5B, và trong bảng Shapley gốc
# (nơi Aggregator nhận nhiều ứng viên hơn) nó đứng #1 trên MATH với +0.148.
#
# Giả thuyết: cho Aggregator đủ ứng viên ĐỘC LẬP thì cơ chế chọn lọc mới có đất.
#
# 5 nhánh trên CÙNG bộ bài:
#   S        : 1 Solver greedy                                  (mốc)
#   SV_agg2  : S -> V -> Aggregator 2 ứng viên                  (cấu hình HIỆN TẠI của dự án)
#   agg3     : 3 Solver sample -> Aggregator LLM                (K=3)
#   agg5     : 5 Solver sample -> Aggregator LLM                (K=5)
#   vote5    : 5 Solver sample -> BỎ PHIẾU theo đa số           (ĐỐI CHỨNG then chốt)
#
# `vote5` tách được hai thứ dễ lẫn: lợi ích đến từ việc CÓ NHIỀU ỨNG VIÊN (bỏ phiếu cơ học làm
# được), hay từ việc Aggregator LLM THỰC SỰ ĐỌC và chọn? Nếu agg5 <= vote5 thì Aggregator LLM
# không cộng thêm gì ngoài phần bỏ phiếu — khớp hướng của H12 (bỏ phiếu thắng LLM-agg trên MATH).
#
# Checkpoint sau mỗi câu (JSONL) và mỗi fold; lưu output nguyên văn mọi vai trên mọi câu.
import os, re, csv, json, glob, statistics
from collections import Counter
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "__TASK__"
N    = __N__
NF   = __NF__
BS   = __BS__
TEMP = 0.7          # sample để các ứng viên khác nhau; greedy 5 lần sẽ ra 5 bản y hệt

FOLD = N // NF
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "main_test.csv" if TASK == "gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} {NF} fold x {FOLD} bai", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="cuda").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx, do_sample=False, seed=None):
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
            o = model.generate(**e, max_new_tokens=mx, do_sample=do_sample,
                               temperature=TEMP if do_sample else 1.0,
                               pad_token_id=tok.pad_token_id)
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
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
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
    except (ValueError, TypeError): return False

if TASK == "gsm8k":
    SOLVE_SYS  = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                  "End with a line: 'The answer is <number>'.")
    VERIFY_SYS = ("You are a math verifier. You are given a problem and a proposed solution. "
                  "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
    AGG_SYS    = ("You are given a math problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking and majority. End with 'The answer is "
                  "<number>'.")
    MX = 512
    q_of = lambda r: r["question"]
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    def pred(t):
        m = (re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
             or NUM.findall(t or ""))
        return m[-1].replace(",", "") if m else None
else:
    SOLVE_SYS  = ("You are an expert mathematician. Solve the problem step by step. Put the "
                  "final answer in \\boxed{}.")
    VERIFY_SYS = ("You are a math verifier. Given a problem and a proposed solution, check each "
                  "step; if wrong, correct it. Put the final answer in \\boxed{}.")
    AGG_SYS    = ("You are given a problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking. Put the final answer in \\boxed{}.")
    MX = 1024
    q_of = lambda r: r["Question"]
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None

def agg_user(q, cands):
    body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(cands))
    return f"{q}\n\n{body}"

def majority(answers):
    """bỏ phiếu cơ học trên đáp án đã chuẩn hoá; hoà thì lấy ứng viên đầu tiên trong nhóm."""
    keys = [norm(a) for a in answers if norm(a)]
    if not keys:
        return None
    top = Counter(keys).most_common(1)[0][0]
    for a in answers:
        if norm(a) == top:
            return a
    return None

ARMS = ["S", "SV_agg2", "agg3", "agg5", "vote5"]
fold_stats, sample = [], []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n} bai) =====", flush=True)

    sol = gen(SOLVE_SYS, list(qs), MX)                       # ứng viên greedy (cũng là mốc S)
    ver = gen(VERIFY_SYS, [f"{q}\n\nProposed solution:\n{s}"
                           for q, s in zip(qs, sol)], MX)
    # 4 ứng viên sample thêm -> cùng với `sol` thành 5 ứng viên độc lập
    samp = [gen(SOLVE_SYS, list(qs), MX, do_sample=True, seed=2000 + k) for k in range(4)]
    cands5 = [[sol[i]] + [samp[k][i] for k in range(4)] for i in range(n)]

    agg2 = gen(AGG_SYS, [agg_user(qs[i], [sol[i], ver[i]]) for i in range(n)], MX)
    agg3 = gen(AGG_SYS, [agg_user(qs[i], cands5[i][:3]) for i in range(n)], MX)
    agg5 = gen(AGG_SYS, [agg_user(qs[i], cands5[i]) for i in range(n)], MX)
    vote5 = [majority([pred(c) for c in cands5[i]]) for i in range(n)]   # đáp án, không phải text

    ok = {
        "S":       [eq(pred(t), g) for t, g in zip(sol, gs)],
        "SV_agg2": [eq(pred(t), g) for t, g in zip(agg2, gs)],
        "agg3":    [eq(pred(t), g) for t, g in zip(agg3, gs)],
        "agg5":    [eq(pred(t), g) for t, g in zip(agg5, gs)],
        "vote5":   [eq(v, g) for v, g in zip(vote5, gs)],
    }
    d = {f"acc_{a}": sum(ok[a]) / n for a in ARMS}
    # Aggregator có chép ứng viên cuối không? (kiểm lại recency bias ở K lớn)
    d["agg2_copies_last"] = sum(1 for i in range(n)
                                if pred(agg2[i]) is not None
                                and eq(pred(agg2[i]), pred(ver[i]))) / n
    d["agg5_copies_last"] = sum(1 for i in range(n)
                                if pred(agg5[i]) is not None
                                and eq(pred(agg5[i]), pred(cands5[i][-1]))) / n
    d["agg5_matches_vote"] = sum(1 for i in range(n)
                                 if pred(agg5[i]) is not None and vote5[i] is not None
                                 and eq(pred(agg5[i]), vote5[i])) / n
    d["mean_distinct_answers"] = statistics.mean(
        len({norm(pred(c)) for c in cands5[i] if norm(pred(c))}) for i in range(n))
    fold_stats.append(d)
    print("  " + " | ".join(f"{a} {d[f'acc_{a}']:.3f}" for a in ARMS), flush=True)
    print(f"  agg2 chep ung vien cuoi {d['agg2_copies_last']:.2f} | "
          f"agg5 chep cuoi {d['agg5_copies_last']:.2f} | "
          f"agg5 trung bo phieu {d['agg5_matches_vote']:.2f} | "
          f"so dap an khac nhau tb {d['mean_distinct_answers']:.2f}/5", flush=True)

    for i in range(n):
        sample.append({
            "fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
            "sol": sol[i], "ver": ver[i],
            "candidates": cands5[i], "agg2": agg2[i], "agg3": agg3[i], "agg5": agg5[i],
            "pred": {"S": pred(sol[i]), "V": pred(ver[i]), "SV_agg2": pred(agg2[i]),
                     "agg3": pred(agg3[i]), "agg5": pred(agg5[i]), "vote5": vote5[i],
                     "candidates": [pred(c) for c in cands5[i]]},
            "ok": {a: ok[a][i] for a in ARMS}})
        with open("/kaggle/working/traces.jsonl", "a") as fh:
            fh.write(json.dumps(sample[-1]) + "\n")

    json.dump({"task": TASK, "folds_done": f + 1, "n_folds": NF, "fold_size": FOLD,
               "complete": f + 1 == NF, "per_fold": fold_stats},
              open("/kaggle/working/summary.json", "w"), indent=2)
    json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
    print(f"  [checkpoint] {f+1}/{NF} fold, {len(sample)} cau", flush=True)

def stats(xs):
    return {"mean": round(statistics.mean(xs), 4), "min": round(min(xs), 4),
            "max": round(max(xs), 4), "by_fold": [round(x, 4) for x in xs]}

out = {"task": TASK, "n_folds": NF, "fold_size": FOLD, "complete": True, "arms": {}}
base = [d["acc_S"] for d in fold_stats]
print("\n" + "=" * 74)
print(f"{'nhanh':<10} {'mean':>7} {'min':>7} {'max':>7} | {'vs S':>9} {'fold cung dau':>14}")
print("=" * 74)
for a in ARMS:
    accs = [d[f"acc_{a}"] for d in fold_stats]
    diffs = [x - b for x, b in zip(accs, base)]
    same = (sum(1 for x in diffs if x > 0) if statistics.mean(diffs) >= 0
            else sum(1 for x in diffs if x < 0))
    out["arms"][a] = {"acc": stats(accs), "delta_vs_S": stats(diffs),
                      "folds_same_sign": f"{same}/{NF}"}
    print(f"{a:<10} {statistics.mean(accs):>7.3f} {min(accs):>7.3f} {max(accs):>7.3f} | "
          f"{statistics.mean(diffs):>+9.3f} {same:>10}/{NF}")

for k in ("agg2_copies_last", "agg5_copies_last", "agg5_matches_vote", "mean_distinct_answers"):
    out[k] = stats([d[k] for d in fold_stats])
    print(f"  {k:<24} {out[k]['mean']:.3f}")

print(f"\nDOC KET QUA: chi tinh la bang chung khi TOAN BO {NF} fold cung dau VA hieu ung > ~5 diem.")
print("  agg5 vs vote5: neu agg5 <= vote5 thi Aggregator LLM khong cong them gi ngoai bo phieu.")
print("  agg5_copies_last: neu van cao o K=5 thi day la recency bias, khong phai 'chon verifier'.")
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)
