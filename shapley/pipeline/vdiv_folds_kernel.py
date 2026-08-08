# NHIỀU VERIFIER hay NHIỀU SOLVER? — đa dạng có điều kiện vs đa dạng độc lập.
#
# `EXTRA_PASS_FINDING.md`: thứ có tác dụng là THÊM MỘT LƯỢT SINH ĐỘC LẬP; lượt chỉ ĐỌC LẠI lượt
# trước thì không. `ORPO_RESULTS.md`: vote3 (3 Solver sample) đạt 5/5 fold trên GSM8K.
#
# Câu hỏi: nếu bỏ phiếu là thứ hoạt động, thì bỏ phiếu giữa 3 VERIFIER có bằng bỏ phiếu giữa
# 3 SOLVER không? Cùng số lượt gọi, khác nguồn đa dạng.
#
# Dự đoán (ghi TRƯỚC khi chạy): PSVVV THUA PSSS. Ba Verifier đều đọc CÙNG một lời giải của
# Solver, và ta đã đo chúng tái sử dụng 42-70% số liệu của lời giải đó — tức bị neo vào cùng
# một chỗ, nên sẽ sai GIỐNG NHAU. Bỏ phiếu giữa các lỗi tương quan không cứu được gì. Ba Solver
# sample thì giải lại từ đầu nên sai theo cách khác nhau -> phiếu mới có thông tin.
#
# 6 nhánh, cùng bộ bài, ngân sách ghi rõ để so công bằng:
#   S            1 lượt   Solver greedy (mốc)
#   PS           2        Planner -> Solver
#   PSV          3        + Verifier, lấy đáp án V              (bỏ Aggregator)
#   PSVA         4        pipeline đầy đủ hiện tại
#   PSVVV_vote   5        P->S rồi BA Verifier độc lập -> vote  (ý tưởng cần kiểm)
#   PSSS_vote    4        P->S rồi HAI Solver sample nữa -> vote3  (đối chứng then chốt)
#   SSS_vote     3        ba Solver sample, KHÔNG pipeline
#
# PSSS_vote là đối chứng quan trọng nhất: nếu nó thắng PSVVV_vote thì nguồn giá trị là tính
# ĐỘC LẬP của lượt sinh, không phải việc "có nhiều verifier".
#
# Cũng đo TƯƠNG QUAN LỖI giữa các ứng viên trong mỗi nhóm — cơ chế phải nhìn thấy được, không
# chỉ suy từ accuracy.
import os, re, csv, json, glob, statistics
from collections import Counter
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

TASK = "__TASK__"
N    = __N__
NF   = __NF__
BS   = __BS__
TEMP = 0.7

FOLD = N // NF
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "main_test.csv" if TASK == "gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV)))[:N]
print(f"TASK={TASK} {NF} fold x {FOLD}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map={"": 0}).eval()
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
    PLAN_SYS  = ("You are a math planning assistant. Read the problem and give a concise "
                 "numbered plan of the steps needed. Do NOT compute the final answer.")
    SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                 "End with a line: 'The answer is <number>'.")
    VER_SYS   = ("You are a math verifier. You are given a problem and a proposed solution. "
                 "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
    AGG_SYS   = ("You are given a math problem and one or more candidate solutions. Decide the "
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
    PLAN_SYS  = ("You are a math planning assistant. Read the competition problem and give a "
                 "concise numbered plan of the solution steps. Do NOT compute the final answer.")
    SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the "
                 "final answer in \\boxed{}.")
    VER_SYS   = ("You are a math verifier. Given a problem and a proposed solution, check each "
                 "step; if wrong, correct it. Put the final answer in \\boxed{}.")
    AGG_SYS   = ("You are given a problem and one or more candidate solutions. Decide the "
                 "correct final answer by re-checking. Put the final answer in \\boxed{}.")
    MX = 1024
    q_of = lambda r: r["Question"]
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None

def majority(answers):
    keys = [norm(a) for a in answers if norm(a)]
    if not keys: return None
    top = Counter(keys).most_common(1)[0][0]
    return next((a for a in answers if norm(a) == top), None)

def nums(t):
    return {x.replace(",", "") for x in NUM.findall(t or "")}

ARMS = ["S", "PS", "PSV", "PSVA", "PSVVV_vote", "PSSS_vote", "SSS_vote"]
COST = {"S": 1, "PS": 2, "PSV": 3, "PSVA": 4, "PSVVV_vote": 5, "PSSS_vote": 4, "SSS_vote": 3}
fold_stats, sample = [], []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n} bai) =====", flush=True)

    plan = gen(PLAN_SYS, list(qs), MX)
    wp = [f"{qs[i]}\n\nSuggested plan:\n{plan[i]}" for i in range(n)]
    sol = gen(SOLVE_SYS, wp, MX)                       # PS
    vu = [f"{qs[i]}\n\nProposed solution:\n{sol[i]}" for i in range(n)]

    # BA Verifier độc lập trên CÙNG lời giải (nguồn đa dạng: sampling của verifier)
    v1 = gen(VER_SYS, vu, MX)                          # greedy
    v2 = gen(VER_SYS, vu, MX, do_sample=True, seed=4000)
    v3 = gen(VER_SYS, vu, MX, do_sample=True, seed=4001)
    # HAI Solver sample nữa (nguồn đa dạng: giải lại từ đầu) — cùng plan để công bằng
    s2 = gen(SOLVE_SYS, wp, MX, do_sample=True, seed=4000)
    s3 = gen(SOLVE_SYS, wp, MX, do_sample=True, seed=4001)
    # ba Solver KHÔNG pipeline
    n1 = gen(SOLVE_SYS, list(qs), MX)
    n2 = gen(SOLVE_SYS, list(qs), MX, do_sample=True, seed=4000)
    n3 = gen(SOLVE_SYS, list(qs), MX, do_sample=True, seed=4001)

    agg = gen(AGG_SYS, [f"{qs[i]}\n\nCandidate 1:\n{sol[i]}\n\nCandidate 2:\n{v1[i]}"
                        for i in range(n)], MX)

    vote_v = [majority([pred(v1[i]), pred(v2[i]), pred(v3[i])]) for i in range(n)]
    vote_s = [majority([pred(sol[i]), pred(s2[i]), pred(s3[i])]) for i in range(n)]
    vote_n = [majority([pred(n1[i]), pred(n2[i]), pred(n3[i])]) for i in range(n)]

    ok = {
        "S":          [eq(pred(t), g) for t, g in zip(n1, gs)],
        "PS":         [eq(pred(t), g) for t, g in zip(sol, gs)],
        "PSV":        [eq(pred(t), g) for t, g in zip(v1, gs)],
        "PSVA":       [eq(pred(t), g) for t, g in zip(agg, gs)],
        "PSVVV_vote": [eq(v, g) for v, g in zip(vote_v, gs)],
        "PSSS_vote":  [eq(v, g) for v, g in zip(vote_s, gs)],
        "SSS_vote":   [eq(v, g) for v, g in zip(vote_n, gs)],
    }
    d = {f"acc_{a}": sum(ok[a]) / n for a in ARMS}

    # CƠ CHẾ: các ứng viên trong mỗi nhóm có sai GIỐNG NHAU không?
    def diversity(group):
        """tỉ lệ câu có >=2 đáp án khác nhau; và số đáp án phân biệt trung bình."""
        distinct = [len({norm(pred(g[k][i])) for k in range(3)
                         if norm(pred(g[k][i]))}) for i in range(n)]
        return (sum(1 for x in distinct if x > 1) / n, statistics.mean(distinct))
    for nm, grp in (("V", [v1, v2, v3]), ("S", [sol, s2, s3]), ("N", [n1, n2, n3])):
        dis, mean_d = diversity(grp)
        d[f"div_{nm}_any"] = dis
        d[f"div_{nm}_mean"] = mean_d
    # neo vào lời giải Solver: Verifier tái sử dụng bao nhiêu số của nó?
    reuse = [len(nums(sol[i]) & nums(v1[i])) / len(nums(sol[i]))
             for i in range(n) if nums(sol[i])]
    d["V_reuse_of_S"] = statistics.mean(reuse) if reuse else 0.0
    # oracle từng nhóm
    d["oracle_V"] = sum(1 for i in range(n)
                        if any(eq(pred(x[i]), gs[i]) for x in (v1, v2, v3))) / n
    d["oracle_S"] = sum(1 for i in range(n)
                        if any(eq(pred(x[i]), gs[i]) for x in (sol, s2, s3))) / n

    fold_stats.append(d)
    print("  " + " | ".join(f"{a} {d[f'acc_{a}']:.3f}" for a in ARMS), flush=True)
    print(f"  đa dạng: V {d['div_V_any']:.2f} ({d['div_V_mean']:.2f}) | "
          f"S {d['div_S_any']:.2f} ({d['div_S_mean']:.2f}) | "
          f"V tái dùng số của S {d['V_reuse_of_S']:.2f} | "
          f"oracle V {d['oracle_V']:.3f} S {d['oracle_S']:.3f}", flush=True)

    for i in range(n):
        sample.append({"fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
                       "plan": plan[i], "sol": sol[i],
                       "v": [v1[i], v2[i], v3[i]], "s": [sol[i], s2[i], s3[i]],
                       "agg": agg[i],
                       "pred": {"v": [pred(v1[i]), pred(v2[i]), pred(v3[i])],
                                "s": [pred(sol[i]), pred(s2[i]), pred(s3[i])],
                                "vote_v": vote_v[i], "vote_s": vote_s[i]},
                       "ok": {a: ok[a][i] for a in ARMS}})
        with open("/kaggle/working/traces.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(sample[-1], ensure_ascii=False) + "\n")

    json.dump({"task": TASK, "folds_done": f + 1, "n_folds": NF,
               "complete": f + 1 == NF, "per_fold": fold_stats},
              open("/kaggle/working/summary.json", "w"), indent=2)
    json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
    print(f"  [checkpoint] {f+1}/{NF}", flush=True)

def stats(xs):
    return {"mean": round(statistics.mean(xs), 4), "min": round(min(xs), 4),
            "max": round(max(xs), 4), "by_fold": [round(x, 4) for x in xs]}

out = {"task": TASK, "n_folds": NF, "fold_size": FOLD, "complete": True, "arms": {}}
print("\n" + "=" * 76)
print(f"{'nhanh':<14} {'goi':>4} {'mean':>7} {'min':>7} {'max':>7}")
print("=" * 76)
for a in ARMS:
    accs = [d[f"acc_{a}"] for d in fold_stats]
    out["arms"][a] = {"acc": stats(accs), "calls": COST[a]}
    print(f"{a:<14} {COST[a]:>4} {statistics.mean(accs):>7.4f} "
          f"{min(accs):>7.4f} {max(accs):>7.4f}")

# so truc tiep hai nhanh cung cau hoi
vv = [d["acc_PSVVV_vote"] for d in fold_stats]
ss = [d["acc_PSSS_vote"] for d in fold_stats]
diff = [a - b for a, b in zip(vv, ss)]
win = sum(1 for x in diff if x > 0)
out["PSVVV_minus_PSSS"] = stats(diff)
out["PSVVV_wins_folds"] = f"{win}/{NF}"
print(f"\nPSVVV_vote (5 goi) − PSSS_vote (4 goi): {statistics.mean(diff):+.4f}  "
      f"PSVVV thang {win}/{NF} fold")
for k in ("div_V_any", "div_S_any", "div_V_mean", "div_S_mean",
          "V_reuse_of_S", "oracle_V", "oracle_S"):
    out[k] = stats([d[k] for d in fold_stats])
    print(f"  {k:<14} {out[k]['mean']:.3f}")

print("\nDU DOAN GHI TRUOC: PSVVV THUA PSSS, vi ba Verifier deu doc CUNG mot loi giai nen sai")
print("GIONG NHAU. Kiem bang div_V vs div_S (do da dang) va oracle_V vs oracle_S (tran).")
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)
