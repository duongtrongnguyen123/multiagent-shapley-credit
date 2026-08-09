# LOOP x 5 FOLD — đặt thanh sai số lên kết quả dương lớn nhất của dự án.
#
# IDEAS.md: `loop` (Solver giải LẠI sau khi Verifier chê) cho +20 điểm trên MATH 1.5B
# (.40 -> .60, n=100, ĐO MỘT LẦN) và 0 điểm ở 7B. Đây là hiệu ứng dương lớn nhất dự án từng
# đo được nhưng CHƯA CÓ thanh sai số — RESULTS.md xếp nó vào mục "LỚN nhưng mới đo MỘT LẦN".
# Sàn nhiễu H13 ~5 điểm ở n<=250, nên +20 rất có thể là thật, nhưng phải kiểm.
#
# 4 nhánh trên CÙNG bộ bài, mỗi nhánh cộng thêm đúng MỘT thành phần, để tách được lợi ích
# thực sự đến từ đâu:
#   S      : Solver một mình                                   (mốc)
#   SV     : Solver -> Verifier, lấy đáp án Verifier            (verify một lần)
#   loop   : S -> V, nếu V BẤT ĐỒNG thì Solver giải lại có phê bình  (nghi phạm chính)
#   rerun  : S -> Solver giải lại LẦN 2 vô điều kiện, KHÔNG phê bình (ĐỐI CHỨNG then chốt)
#
# `rerun` là đối chứng quan trọng nhất: nếu nó cũng được +20 thì lợi ích không đến từ PHÊ BÌNH
# mà chỉ từ việc được GIẢI THÊM MỘT LẦN. Không có nhánh này thì mọi kết luận về "feedback" đều
# có thể sai. Cùng logic với việc dùng `sampling` làm đối chứng cho `debate`.
#
# Checkpoint sau mỗi câu (JSONL) và mỗi fold; lưu output nguyên văn mọi vai trên mọi câu.
import os, re, csv, json, glob, statistics, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "__TASK__"
N    = __N__
NF   = __NF__
BS   = __BS__

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
                                             device_map="auto").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = [tok.apply_chat_template([{"role": "system", "content": sysm},
                                       {"role": "user", "content": u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False,
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
    MX = 1024
    q_of = lambda r: r["Question"]
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None

fold_stats, sample = [], []
ARMS = ["S", "SV", "loop", "rerun"]

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n} bai) =====", flush=True)

    sol = gen(SOLVE_SYS, list(qs), MX)
    ver = gen(VERIFY_SYS, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, sol)], MX)
    # rerun: giải lại vô điều kiện, KHÔNG có phê bình -> tách "thêm lượt sinh" khỏi "feedback"
    rer = gen(SOLVE_SYS, [f"{q}\n\nSolve it again, carefully." for q in qs], MX)

    # loop: chỉ giải lại KHI Verifier bất đồng, và có kèm phê bình
    disagree = [i for i in range(n) if pred(ver[i]) != pred(sol[i])]
    redo_map = {}
    if disagree:
        redo = gen(SOLVE_SYS, [f"{qs[i]}\n\nA reviewer flagged an error:\n{ver[i]}\n\n"
                               f"Redo the problem carefully." for i in disagree], MX)
        redo_map = dict(zip(disagree, redo))
    loop_out = [redo_map.get(i, sol[i]) for i in range(n)]

    outs = {"S": sol, "SV": ver, "loop": loop_out, "rerun": rer}
    ok = {a: [eq(pred(t), g) for t, g in zip(outs[a], gs)] for a in ARMS}
    d = {f"acc_{a}": sum(ok[a]) / n for a in ARMS}
    d["n_disagree"] = len(disagree)
    # trong các ca Verifier bất đồng, giải lại có cứu được không?
    d["loop_rescued"] = sum(1 for i in disagree if not ok["S"][i] and ok["loop"][i])
    d["loop_broke"]   = sum(1 for i in disagree if ok["S"][i] and not ok["loop"][i])
    fold_stats.append(d)
    print("  " + " | ".join(f"{a} {d[f'acc_{a}']:.3f}" for a in ARMS), flush=True)
    print(f"  V bat dong {len(disagree)}/{n} ca -> loop cuu {d['loop_rescued']}, "
          f"pha {d['loop_broke']}", flush=True)

    for i in range(n):
        sample.append({
            "fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
            "sol": sol[i], "ver": ver[i], "loop": loop_out[i], "rerun": rer[i],
            "verifier_disagreed": i in disagree,
            "pred": {a: pred(outs[a][i]) for a in ARMS},
            "ok": {a: ok[a][i] for a in ARMS},
            "len": {a: len(outs[a][i] or "") for a in ARMS}})
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
print("\n" + "=" * 72)
print(f"{'nhanh':<8} {'mean':>7} {'min':>7} {'max':>7} | {'vs S: mean':>11} {'fold cung dau':>14}")
print("=" * 72)
for a in ARMS:
    accs = [d[f"acc_{a}"] for d in fold_stats]
    diffs = [x - b for x, b in zip(accs, base)]
    same = (sum(1 for x in diffs if x > 0) if statistics.mean(diffs) >= 0
            else sum(1 for x in diffs if x < 0))
    out["arms"][a] = {"acc": stats(accs), "delta_vs_S": stats(diffs),
                      "folds_same_sign": f"{same}/{NF}"}
    print(f"{a:<8} {statistics.mean(accs):>7.3f} {min(accs):>7.3f} {max(accs):>7.3f} | "
          f"{statistics.mean(diffs):>+11.3f} {same:>10}/{NF}")

tot = lambda k: sum(d[k] for d in fold_stats)
print(f"\n  Verifier bat dong: {tot('n_disagree')}/{len(ALL)} ca "
      f"-> giai lai cuu {tot('loop_rescued')}, pha {tot('loop_broke')}")
print(f"\nDOC KET QUA: chi tinh la bang chung khi TOAN BO {NF} fold cung dau VA hieu ung > ~5 diem.")
print("  So `loop` voi `rerun`: neu rerun cung tang bang loop thi loi ich den tu THEM MOT LUOT")
print("  SINH, khong phai tu PHE BINH cua Verifier.")
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)
