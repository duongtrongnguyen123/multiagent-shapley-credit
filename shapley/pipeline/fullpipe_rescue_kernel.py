# PIPELINE ĐẦY ĐỦ P->S->V->A: Verifier có CỨU được lỗi của Solver không?
#
# Hạn chế của các vòng inspect/fewshot trước: chúng CHỈ chạy Planner->Solver, nên mọi câu
# tính là "sai" có thể đã được Verifier sửa trong pipeline thật. Kernel này chạy đủ 4 vai và
# chấm điểm SAU TỪNG TẦNG trên cùng một câu, nên theo dõi được số phận từng câu qua pipeline.
#
# Với mỗi câu ghi lại bộ 4 đúng/sai: (S, V, A) và phân loại chuyển tiếp:
#   S sai -> V đúng : VERIFIER CỨU ĐƯỢC
#   S đúng -> V sai : VERIFIER PHÁ
#   S sai -> V sai  : Verifier bỏ lỡ
#   V sai -> A đúng : AGGREGATOR CỨU
#   V đúng -> A sai : AGGREGATOR PHÁ
# Đồng thời tách theo NGUỒN GỐC lỗi (dùng nhánh NP - Solver làm một mình - làm phản chứng):
#   lỗi do PLAN gây ra (một mình đúng, có plan sai) -> Verifier có gỡ được loại lỗi này không?
#   lỗi do SOLVER tự gây (một mình cũng sai)        -> Verifier có gỡ được không?
# Câu hỏi cốt lõi: Verifier cứu được lỗi NÀO — lỗi tại plan hay lỗi tại solver?
#
# 5 fold rời nhau để có thanh sai số (chuẩn H13/H14).
#
# LƯU TRACE ĐẦY ĐỦ: traces.json chứa MỌI câu x MỌI fold, với output nguyên văn của cả 5 lượt
# sinh (plan, solver-một-mình, solver, verifier, aggregator), đáp án trích ra từng lượt, độ dài
# từng lượt, và nhãn phân loại sẵn (error_origin, V_transition, A_transition, plan_leaked_wrong,
# solver_copied_plan). Aggregate chỉ đáng tin khi còn kiểm lại được text phía sau nó.
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
                                             device_map="cuda").eval()
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

# ---- prompt: bê nguyên từ template.py / template_math.py --------------------
if TASK == "gsm8k":
    PLAN_SYS   = ("You are a math planning assistant. Read the problem and give a concise "
                  "numbered plan of the steps needed. Do NOT compute the final answer.")
    SOLVE_SYS  = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                  "End with a line: 'The answer is <number>'.")
    VERIFY_SYS = ("You are a math verifier. You are given a problem and a proposed solution. "
                  "Check each step; if wrong, correct it. End with 'The answer is <number>'.")
    AGG_SYS    = ("You are given a math problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking and majority. End with 'The answer is "
                  "<number>'.")
    PLAN_MX, SOLVE_MX = 256, 512
    q_of = lambda r: r["question"]
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
    def pred(t):
        m = (re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
             or NUM.findall(t or ""))
        return m[-1].replace(",", "") if m else None
else:
    PLAN_SYS   = ("You are a math planning assistant. Read the competition problem and give a "
                  "concise numbered plan of the solution steps. Do NOT compute the final answer.")
    SOLVE_SYS  = ("You are an expert mathematician. Solve the problem step by step. Put the "
                  "final answer in \\boxed{}.")
    VERIFY_SYS = ("You are a math verifier. Given a problem and a proposed solution, check each "
                  "step; if wrong, correct it. Put the final answer in \\boxed{}.")
    AGG_SYS    = ("You are given a problem and one or more candidate solutions. Decide the "
                  "correct final answer by re-checking. Put the final answer in \\boxed{}.")
    PLAN_MX, SOLVE_MX = 512, 1024
    q_of = lambda r: r["Question"]
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None

def plan_answer(p):
    b = boxed(p)
    if b is not None: return b
    m = NUM.findall(p or "")
    return m[-1].replace(",", "") if m else None

fold_stats, sample = [], []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n} bai) =====", flush=True)

    plans = gen(PLAN_SYS, qs, PLAN_MX)
    # nhánh phản chứng: Solver làm MỘT MÌNH (không plan) -> tách nguồn gốc lỗi
    alone = gen(SOLVE_SYS, list(qs), SOLVE_MX)
    # pipeline thật: P -> S -> V -> A
    sol = gen(SOLVE_SYS, [f"{q}\n\nSuggested plan:\n{p}" for q, p in zip(qs, plans)], SOLVE_MX)
    ver = gen(VERIFY_SYS, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, sol)], SOLVE_MX)
    agg = gen(AGG_SYS, [f"{q}\n\nCandidate 1:\n{s}\n\nCandidate 2:\n{v}"
                        for q, s, v in zip(qs, sol, ver)], SOLVE_MX)

    ok_alone = [eq(pred(t), g) for t, g in zip(alone, gs)]
    ok_s = [eq(pred(t), g) for t, g in zip(sol, gs)]
    ok_v = [eq(pred(t), g) for t, g in zip(ver, gs)]
    ok_a = [eq(pred(t), g) for t, g in zip(agg, gs)]

    d = {"acc_alone": sum(ok_alone) / n, "acc_S": sum(ok_s) / n,
         "acc_V": sum(ok_v) / n, "acc_A": sum(ok_a) / n}
    # chuyển tiếp S -> V
    d["V_rescued"] = sum(1 for i in range(n) if not ok_s[i] and ok_v[i])
    d["V_broke"]   = sum(1 for i in range(n) if ok_s[i] and not ok_v[i])
    d["V_missed"]  = sum(1 for i in range(n) if not ok_s[i] and not ok_v[i])
    # chuyển tiếp V -> A
    d["A_rescued"] = sum(1 for i in range(n) if not ok_v[i] and ok_a[i])
    d["A_broke"]   = sum(1 for i in range(n) if ok_v[i] and not ok_a[i])
    # Verifier cứu được loại lỗi NÀO? (dùng nhánh alone tách nguồn gốc)
    plan_caused = [i for i in range(n) if ok_alone[i] and not ok_s[i]]   # plan phá
    solver_own  = [i for i in range(n) if not ok_alone[i] and not ok_s[i]]  # solver tự sai
    d["n_plan_caused"] = len(plan_caused)
    d["n_solver_own"]  = len(solver_own)
    d["V_rescued_plan_caused"]  = sum(1 for i in plan_caused if ok_v[i])
    d["V_rescued_solver_own"]   = sum(1 for i in solver_own if ok_v[i])
    # trong các ca plan để lộ đáp án SAI, Verifier có gỡ được không?
    leak_wrong = [i for i in range(n)
                  if plan_answer(plans[i]) is not None and not eq(plan_answer(plans[i]), gs[i])]
    d["n_plan_leak_wrong"] = len(leak_wrong)
    d["V_rescued_leak_wrong"] = sum(1 for i in leak_wrong if ok_v[i])
    d["S_copied_leak_wrong"] = sum(1 for i in leak_wrong
                                   if pred(sol[i]) is not None
                                   and eq(pred(sol[i]), plan_answer(plans[i])))
    fold_stats.append(d)
    print(f"  acc: alone {d['acc_alone']:.3f} | S {d['acc_S']:.3f} | V {d['acc_V']:.3f} "
          f"| A {d['acc_A']:.3f}", flush=True)
    print(f"  V: cuu {d['V_rescued']} / pha {d['V_broke']} / bo lo {d['V_missed']}  "
          f"|  A: cuu {d['A_rescued']} / pha {d['A_broke']}", flush=True)
    print(f"  V cuu duoc: {d['V_rescued_plan_caused']}/{d['n_plan_caused']} ca loi-do-PLAN, "
          f"{d['V_rescued_solver_own']}/{d['n_solver_own']} ca loi-do-SOLVER", flush=True)

    # LƯU MỌI CÂU, MỌI FOLD: output nguyên văn của từng vai + đáp án trích ra + nhãn
    # phân loại sẵn, để phân tích ngoại tuyến không phải chạy lại và không phải tính lại.
    for i in range(n):
        pa = plan_answer(plans[i])
        sample.append({
            "fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
            "plan": plans[i], "sol_alone": alone[i], "sol": sol[i],
            "ver": ver[i], "agg": agg[i],
            "pred": {"alone": pred(alone[i]), "S": pred(sol[i]),
                     "V": pred(ver[i]), "A": pred(agg[i]), "plan_leak": pa},
            "ok": {"alone": ok_alone[i], "S": ok_s[i], "V": ok_v[i], "A": ok_a[i]},
            "len": {"plan": len(plans[i]), "alone": len(alone[i]), "S": len(sol[i]),
                    "V": len(ver[i]), "A": len(agg[i])},
            "label": {
                "error_origin": ("plan_caused" if ok_alone[i] and not ok_s[i] else
                                 "solver_own" if not ok_alone[i] and not ok_s[i] else
                                 "none" if ok_s[i] else "unknown"),
                "V_transition": ("rescued" if not ok_s[i] and ok_v[i] else
                                 "broke" if ok_s[i] and not ok_v[i] else
                                 "missed" if not ok_s[i] and not ok_v[i] else "kept_ok"),
                "A_transition": ("rescued" if not ok_v[i] and ok_a[i] else
                                 "broke" if ok_v[i] and not ok_a[i] else
                                 "missed" if not ok_v[i] and not ok_a[i] else "kept_ok"),
                "plan_leaked_wrong": pa is not None and not eq(pa, gs[i]),
                "solver_copied_plan": (pa is not None and pred(sol[i]) is not None
                                       and eq(pred(sol[i]), pa)),
            }})

def st(key):
    xs = [d[key] for d in fold_stats]
    return {"mean": round(statistics.mean(xs), 4), "min": min(xs), "max": max(xs),
            "by_fold": xs}

out = {"task": TASK, "n_folds": NF, "fold_size": FOLD,
       "metrics": {k: st(k) for k in fold_stats[0]}}

print("\n" + "=" * 72)
print("ACCURACY THEO TUNG TANG (mean qua 5 fold)")
print("=" * 72)
for k, lab in [("acc_alone", "Solver mot minh"), ("acc_S", "P->S"),
               ("acc_V", "P->S->V"), ("acc_A", "P->S->V->A")]:
    m = out["metrics"][k]
    print(f"  {lab:<18} {m['mean']:.4f}   theo fold {[round(x,3) for x in m['by_fold']]}")

vg = [d["acc_V"] - d["acc_S"] for d in fold_stats]
ag = [d["acc_A"] - d["acc_V"] for d in fold_stats]
out["V_gain"] = {"mean": round(statistics.mean(vg), 4), "min": round(min(vg), 4),
                 "max": round(max(vg), 4), "by_fold": [round(x, 4) for x in vg],
                 "folds_positive": f"{sum(1 for x in vg if x > 0)}/{NF}"}
out["A_gain"] = {"mean": round(statistics.mean(ag), 4), "min": round(min(ag), 4),
                 "max": round(max(ag), 4), "by_fold": [round(x, 4) for x in ag],
                 "folds_positive": f"{sum(1 for x in ag if x > 0)}/{NF}"}
print(f"\n  V_gain (V - S): mean {out['V_gain']['mean']:+.4f}  "
      f"[{out['V_gain']['min']:+.3f}, {out['V_gain']['max']:+.3f}]  "
      f"fold duong {out['V_gain']['folds_positive']}")
print(f"  A_gain (A - V): mean {out['A_gain']['mean']:+.4f}  "
      f"[{out['A_gain']['min']:+.3f}, {out['A_gain']['max']:+.3f}]  "
      f"fold duong {out['A_gain']['folds_positive']}")

print("\n" + "=" * 72)
print("VERIFIER CUU DUOC LOI NAO? (tong qua 5 fold)")
print("=" * 72)
tot = lambda k: sum(d[k] for d in fold_stats)
print(f"  tong so ca loi do PLAN gay ra   : {tot('n_plan_caused'):>4}  "
      f"-> Verifier cuu duoc {tot('V_rescued_plan_caused')}")
print(f"  tong so ca loi do SOLVER tu gay : {tot('n_solver_own'):>4}  "
      f"-> Verifier cuu duoc {tot('V_rescued_solver_own')}")
print(f"  ca plan lo dap an SAI           : {tot('n_plan_leak_wrong'):>4}  "
      f"-> Solver chep {tot('S_copied_leak_wrong')}, Verifier cuu {tot('V_rescued_leak_wrong')}")
print(f"\n  V tong: cuu {tot('V_rescued')} / pha {tot('V_broke')} / bo lo {tot('V_missed')}")
print(f"  A tong: cuu {tot('A_rescued')} / pha {tot('A_broke')}")
print(f"\nDOC KET QUA: hieu ung chi tinh la bang chung khi TOAN BO {NF} fold cung dau.")

print("\nSUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json", "w"), indent=2)
# traces.json: MỌI câu x MỌI fold, output nguyên văn của cả 5 lượt sinh (plan, solver-một-mình,
# solver, verifier, aggregator) + đáp án trích ra + nhãn phân loại. Đây là dữ liệu để phân tích
# ngoại tuyến; summary chỉ là tổng hợp của nó.
json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
print(f"traces.json: {len(sample)} cau x 5 luot sinh moi cau", flush=True)
print("done", flush=True)
