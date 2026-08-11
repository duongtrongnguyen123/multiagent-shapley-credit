# PIPELINE: Planner -> iterate(Solve + Judge) — đồng thuận có kiểm soát, budget giới hạn.
#
# Ý tưởng: thay vì pipeline tuyến tính P->S->V->A (4 call, không có vòng phản hồi), dùng
# Planner rồi LẶP (Solve + Judge) cho tới khi Judge xác nhận đúng, hoặc hết budget.
#
# Vòng lặp theo spec:
#   P  1 call   plan
#   loop i = 1..3:
#     S_i  solve (vòng i)
#     J_i  judge binary: 1 = lời giải đúng, 0 = sai
#     if J_i == 1:  DỪNG, lấy pred(S_i) làm đáp án cuối   (dừng sớm)
#     else:         re-solve vòng sau với temperature khác (tránh greedy lặp cái sai)
#   nếu 3 vòng đều Judge bảo sai:  lấy pred(S_3) làm đáp án cuối
#
# Điểm mấu chốt:
#  - Judge là BINARY (đúng/sai) chứ không sinh đáp án — theo anh chọn, ít call hơn, sạch hơn.
#  - Re-solve đổi temperature: v1 greedy (temp 1.0), v2 temp 0.7, v3 temp 0.4 — model greedy
#    sẽ tái tạo y hệt lời giải cũ nếu nhiệt độ như nhau; thay đổi T là cách ép đa dạng mà không
#    phải sampling nhiều (spec: không sampling nhiều lần).
#  - Budget 3 vòng (S+J) mỗi vòng 2 call -> tối đa P + 3*2 = 7 call/câu; trung bình thấp hơn
#    nếu dừng sớm.
#
# Đo song song (cùng câu, cùng seed):
#   S_alone  : Solver greedy một mình (baseline, 1 call) — mốc cost 1
#   PSVA     : pipeline 4 vai đầy đủ (baseline, 4 call) — mốc cost 4
# 2 baseline này để so "loop có rẻ/giúp hơn không" trên cùng bài.
#
# Per-question ghi: S_i text, J_i verdict, dừng ở vòng nào, acc từng vòng, total calls.
import os, re, json, csv, glob, statistics, random, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N    = __N__
NF   = __NF__
BS   = __BS__
MAXV = 3               # budget: tối đa 3 vòng (S+J)
TEMP = [1.0, 0.7, 0.4] # nhiệt độ mỗi vòng — v1 greedy, sau đó hạ dần để ép đa dạng

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV, encoding="utf-8")))[:N]
print(f"N={N} NF={NF} fold={N//NF} MAXV={MAXV} TEMP={TEMP}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="auto").eval()
print("model loaded", flush=True)

def gen(sysm, usrs, mx, temp=1.0, seed=None):
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
            o = model.generate(**e, max_new_tokens=mx,
                               do_sample=(temp < 1.0), temperature=temp,
                               pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    return outs

def read_digit(t):
    m = re.search(r"[01]", t or "")
    return int(m.group(0)) if m else None

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
def pred(t):
    b = boxed(t)
    if b is not None: return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
    return m[-1].strip() if m else None

PLAN_SYS   = ("You are a math planning assistant. Read the competition problem and give a "
              "concise numbered plan of the solution steps. Do NOT compute the final answer.")
SOLVE_SYS  = ("You are an expert mathematician. Solve the problem step by step. Put the final "
              "answer in \\boxed{}.")
JUDGE_SYS  = ("You are a strict math judge. You are given a problem and a proposed solution. "
              "Reply with a single digit: 1 if the solution is correct, 0 if it is wrong.")
VER_SYS    = ("You are a math verifier. Given a problem and a proposed solution, check each "
              "step; if wrong, correct it. Put the final answer in \\boxed{}.")
AGG_SYS    = ("You are given a problem and one or more candidate solutions. Decide the "
              "correct final answer by re-checking. Put the final answer in \\boxed{}.")

# baselines cùng model
def solve_alone(usrs):
    return gen(SOLVE_SYS, usrs, 1024, temp=1.0)

PLAN_MX, SOLVE_MX = 512, 1024
FOLD = N // NF
fold_stats, sample = [], []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [r["Question"].strip() for r in rows]
    gs = [boxed(r["Answer"]) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n}) =====", flush=True)

    # ---- baselines: S-alone + PSVA (cùng bài, cùng seed) ----
    sol_alone = solve_alone(qs)                          # S-alone baseline
    plans = gen(PLAN_SYS, qs, PLAN_MX, temp=1.0)         # P
    ps_sol = gen(SOLVE_SYS, [f"{q}\n\nSuggested plan:\n{pl}" for q, pl in zip(qs, plans)], SOLVE_MX, temp=1.0)
    ps_ver = gen(VER_SYS, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, ps_sol)], SOLVE_MX, temp=1.0)
    ps_agg = gen(AGG_SYS, [f"{q}\n\nCandidate 1:\n{s}\n\nCandidate 2:\n{v}"
                  for q, s, v in zip(qs, ps_sol, ps_ver)], SOLVE_MX, temp=1.0)

    # ---- loop: Planner -> iterate(Solve + Judge) ----
    cur_s = ps_sol[:]        # vòng 1: Solver nhận plan (tái dùng ps_sol để so cùng nhánh P)
    stop_at = [None] * n     # vòng dừng (1..3); None = hết 3 vòng
    sols = []                # S_i của từng vòng
    judges = []              # J_i verdict
    for v in range(MAXV):
        # solve vòng v (v=0 greedy, sau đó re-solve nhiệt độ khác)
        s_here = cur_s
        # judge binary
        j = gen(JUDGE_SYS, [f"{q}\n\nProposed solution:\n{s}" for q, s in zip(qs, s_here)], 8, temp=1.0)
        jv = [read_digit(t) for t in j]
        sols.append(s_here)
        judges.append(jv)
        # dừng sớm: judge bảo đúng
        for i in range(n):
            if stop_at[i] is None and jv[i] == 1:
                stop_at[i] = v + 1
        # nếu chưa hết budget và còn câu chưa dừng -> re-solve cho vòng sau (đổi temp)
        if v < MAXV - 1:
            todo = [i for i in range(n) if stop_at[i] is None]
            if todo:
                nxt = gen(SOLVE_SYS,
                          [f"{q}\n\nSuggested plan:\n{pl}\nPlease solve again, more carefully."
                           for q, pl in zip([qs[i] for i in todo], [plans[i] for i in todo])],
                          SOLVE_MX, temp=TEMP[v+1], seed=1000 + v)
                # chèn vào đúng vị trí
                cur_s = cur_s[:]   # giữ không đổi, chỉ đổi phần chưa dừng
                for k, i in enumerate(todo):
                    cur_s[i] = nxt[k]
        else:
            # hết vòng, mọi câu chưa dừng coi như lấy S_3
            for i in range(n):
                if stop_at[i] is None:
                    stop_at[i] = MAXV

    # đáp án cuối: pred(S_{stop_at}); các vòng sau không dùng
    final_sol = [None] * n
    for i in range(n):
        st = stop_at[i] - 1
        final_sol[i] = sols[st][i]

    ok_alone = [eq(pred(t), g) for t, g in zip(sol_alone, gs)]
    ok_psva  = [eq(pred(t), g) for t, g in zip(ps_agg, gs)]
    ok_loop  = [eq(pred(t), g) for t, g in zip(final_sol, gs)]
    d = {"acc_alone": sum(ok_alone)/n, "acc_psva": sum(ok_psva)/n,
         "acc_loop": sum(ok_loop)/n}

    # phân bố dừng
    d["stop_dist"] = {str(k): sum(1 for x in stop_at if x == k) for k in (1, 2, 3)}
    d["calls_avg"] = 1 + sum(2 * st for st in stop_at) / n     # P + 2*stop (S+J mỗi vòng)
    d["stop_at1_ok"] = sum(1 for i in range(n) if stop_at[i] == 1 and ok_loop[i])
    d["stop_at1_n"]  = sum(1 for i in range(n) if stop_at[i] == 1)
    # judge precision/recall trên vòng 1 (label là stop hay không)
    j1 = judges[0]
    d["judge_prec"] = (sum(1 for i in range(n) if j1[i] == 1 and ok_alone[i])
                       / max(1, sum(1 for i in range(n) if j1[i] == 1)))
    d["judge_rec"]  = (sum(1 for i in range(n) if j1[i] == 1 and ok_alone[i])
                       / max(1, sum(1 for i in range(n) if ok_alone[i])))

    fold_stats.append(d)
    print("  " + " | ".join(f"{k} {d[k]:.3f}" for k in ("acc_alone", "acc_psva", "acc_loop"))
          + f" | stop {d['stop_dist']} | calls {d['calls_avg']:.2f}", flush=True)
    print(f"  judge prec {d['judge_prec']:.2f} rec {d['judge_rec']:.2f}", flush=True)

    for i in range(n):
        sample.append({"fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
                       "plan": plans[i], "sols": [sols[v][i] for v in range(len(sols))],
                       "judges": [judges[v][i] for v in range(len(judges))],
                       "stop_at": stop_at[i], "final_sol": final_sol[i],
                       "ok": {"alone": ok_alone[i], "psva": ok_psva[i], "loop": ok_loop[i]}})

    json.dump({"task": "math", "folds_done": f + 1, "n_folds": NF, "complete": f + 1 == NF,
               "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
    json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
    print(f"  [checkpoint] {f+1}/{NF}", flush=True)

def stats(xs):
    return {"mean": round(statistics.mean(xs), 4), "min": round(min(xs), 4),
            "max": round(max(xs), 4), "by_fold": [round(x, 4) for x in xs]}

out = {"task": "math", "n_folds": NF, "fold_size": N // NF, "complete": True, "arms": {}}
print("\n" + "=" * 70)
for a in ("acc_alone", "acc_psva", "acc_loop"):
    accs = [d[a] for d in fold_stats]
    out["arms"][a] = stats(accs)
    print(f"{a:<12} mean {statistics.mean(accs):.4f} min {min(accs):.4f} max {max(accs):.4f}")
for k in ("calls_avg", "judge_prec", "judge_rec"):
    out[k] = stats([d[k] for d in fold_stats])
    print(f"{k:<12} mean {statistics.mean([d[k] for d in fold_stats]):.4f}")
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
print("done", flush=True)