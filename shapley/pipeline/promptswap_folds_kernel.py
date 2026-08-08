# HOÁN VỊ PROMPT — prompt hay VỊ TRÍ trong pipeline quyết định hành vi của một vai?
#
# `ROLE_SPECIALIZATION.md` đo được: ở 1.5B, phân công lao động sụp đổ (Planner giải hộ 34.7%,
# Solver chép 62%, Aggregator chép Verifier 73-100%). Nhưng đó mới là TƯƠNG QUAN. Ta chưa
# chứng minh PROMPT là nguyên nhân — có thể chính CẤU TRÚC pipeline (vị trí, thứ hạng đầu vào)
# mới quyết định hành vi, còn prompt chỉ là nhãn dán.
#
# Phản chứng: HOÁN VỊ prompt giữa các vị trí, giữ nguyên luồng dữ liệu.
#   normal : pos1=PLAN(đề) -> pos2=SOLVE(đề+out1) -> pos3=VERIFY(đề+out2)
#   swap   : pos1=VERIFY   -> pos2=PLAN           -> pos3=SOLVE      (luồng y hệt)
#   solo   : cả 3 vị trí đều dùng SOLVE_SYS  (đối chứng: chỉ còn cấu trúc, không còn vai)
#
# ĐỌC KẾT QUẢ:
#   Nếu hành vi bám theo PROMPT  -> vị trí nào mang prompt PLAN thì vị trí đó rò đáp án
#      => prompt CÓ tạo ra vai, và sụp đổ là do model quá yếu để tuân theo.
#   Nếu hành vi bám theo VỊ TRÍ  -> vị trí 1 luôn hành xử như planner bất kể prompt nào
#      => prompt KHÔNG tạo ra phân công; cấu trúc mới tạo. Đây là mệnh đề mạnh chưa ai chứng minh.
#   Nếu `solo` (không có vai) ngang `normal` -> nhãn vai không đóng góp gì cả.
#
# Chỉ số bám theo TỪNG VỊ TRÍ, không theo tên vai — đó là điểm mấu chốt của thiết kế.
import os, re, csv, json, glob, statistics
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

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
print(f"TASK={TASK} {NF} fold x {FOLD}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map={"": 0}).eval()
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
    PLAN_SYS  = ("You are a math planning assistant. Read the problem and give a concise "
                 "numbered plan of the steps needed. Do NOT compute the final answer.")
    SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                 "End with a line: 'The answer is <number>'.")
    VER_SYS   = ("You are a math verifier. You are given a problem and a proposed solution. "
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
    PLAN_SYS  = ("You are a math planning assistant. Read the competition problem and give a "
                 "concise numbered plan of the solution steps. Do NOT compute the final answer.")
    SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the "
                 "final answer in \\boxed{}.")
    VER_SYS   = ("You are a math verifier. Given a problem and a proposed solution, check each "
                 "step; if wrong, correct it. Put the final answer in \\boxed{}.")
    MX = 1024
    q_of = lambda r: r["Question"]
    gold_of = lambda r: boxed(r["Answer"])
    def pred(t):
        b = boxed(t)
        if b is not None: return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None

def nums(t):
    return {x.replace(",", "") for x in NUM.findall(t or "")}

# LUỒNG DỮ LIỆU GIỮ NGUYÊN Ở MỌI NHÁNH — chỉ đổi prompt gán cho từng vị trí.
# pos1 thấy đề; pos2 thấy đề + output pos1; pos3 thấy đề + output pos2.
ARRANGE = {
    "normal": [PLAN_SYS, SOLVE_SYS, VER_SYS],   # đúng thứ tự vai gốc
    "swap":   [VER_SYS, PLAN_SYS, SOLVE_SYS],   # xoay vòng: prompt đổi, cấu trúc giữ nguyên
    "solo":   [SOLVE_SYS, SOLVE_SYS, SOLVE_SYS],  # bỏ hẳn vai, chỉ còn 3 lượt sinh
}

fold_stats, sample = [], []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n} bai) =====", flush=True)
    d = {}
    outs_all = {}

    for arr, sysms in ARRANGE.items():
        o1 = gen(sysms[0], list(qs), MX)
        o2 = gen(sysms[1], [f"{qs[i]}\n\nPrevious response:\n{o1[i]}" for i in range(n)], MX)
        o3 = gen(sysms[2], [f"{qs[i]}\n\nPrevious response:\n{o2[i]}" for i in range(n)], MX)
        outs = [o1, o2, o3]
        outs_all[arr] = outs
        d[f"acc_{arr}"] = sum(eq(pred(o3[i]), gs[i]) for i in range(n)) / n

        # CHỈ SỐ THEO VỊ TRÍ (không theo tên vai) — đây là điểm mấu chốt
        for p in range(3):
            op = outs[p]
            d[f"{arr}_pos{p+1}_leak"] = sum(
                1 for i in range(n) if eq(pred(op[i]), gs[i])) / n
            d[f"{arr}_pos{p+1}_len"] = statistics.median(len(x or "") for x in op)
            if p > 0:   # có output trước đó để so
                prev = outs[p - 1]
                d[f"{arr}_pos{p+1}_nonew"] = sum(
                    1 for i in range(n) if not (nums(op[i]) - nums(prev[i]))) / n
                d[f"{arr}_pos{p+1}_same_ans"] = sum(
                    1 for i in range(n) if pred(op[i]) is not None
                    and eq(pred(op[i]), pred(prev[i]))) / n

    fold_stats.append(d)
    print("  acc: " + " | ".join(f"{a} {d[f'acc_{a}']:.3f}" for a in ARRANGE), flush=True)
    for arr in ARRANGE:
        print(f"  {arr:<7} leak/pos: "
              + " ".join(f"p{p+1} {d[f'{arr}_pos{p+1}_leak']:.2f}" for p in range(3))
              + "   len: " + " ".join(f"{d[f'{arr}_pos{p+1}_len']:.0f}" for p in range(3)),
              flush=True)

    for i in range(n):
        sample.append({"fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
                       **{f"{arr}_pos{p+1}": outs_all[arr][p][i]
                          for arr in ARRANGE for p in range(3)}})
        with open("/kaggle/working/traces.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(sample[-1], ensure_ascii=False) + "\n")

    json.dump({"task": TASK, "folds_done": f + 1, "n_folds": NF,
               "complete": f + 1 == NF, "per_fold": fold_stats},
              open("/kaggle/working/summary.json", "w"), indent=2)
    json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
    print(f"  [checkpoint] {f+1}/{NF}", flush=True)

def m(k):
    return statistics.mean(x[k] for x in fold_stats)

out = {"task": TASK, "n_folds": NF, "fold_size": FOLD, "complete": True,
       "metrics": {k: round(m(k), 4) for k in fold_stats[0]}}

print("\n" + "=" * 78)
print("ACC CUOI PIPELINE")
for arr in ARRANGE:
    print(f"  {arr:<8} {m(f'acc_{arr}'):.4f}")

print("\n" + "=" * 78)
print("HANH VI THEO VI TRI — prompt hay vi tri quyet dinh?")
print(f"  {'':<9}" + "".join(f"{'pos'+str(p+1):>22}" for p in range(3)))
for arr, sysms in ARRANGE.items():
    names = ["PLAN" if s is PLAN_SYS else "SOLVE" if s is SOLVE_SYS else "VERIFY"
             for s in sysms]
    print(f"  {arr:<9}" + "".join(f"{names[p]:>22}" for p in range(3)))
    print(f"  {'  leak':<9}" + "".join(f"{m(f'{arr}_pos{p+1}_leak'):>22.3f}" for p in range(3)))
    print(f"  {'  len':<9}" + "".join(f"{m(f'{arr}_pos{p+1}_len'):>22.0f}" for p in range(3)))
    print(f"  {'  nonew':<9}" + "".join(
        (f"{m(f'{arr}_pos{p+1}_nonew'):>22.3f}" if p > 0 else f"{'—':>22}")
        for p in range(3)))

print("\nDOC: nếu cột `leak` cao ở vị trí mang prompt PLAN (normal p1, swap p2) -> hành vi bám")
print("PROMPT. Nếu leak cao ở p1 bất kể prompt nào -> hành vi bám VỊ TRÍ, và prompt không tạo")
print("ra phân công lao động. So `solo` với `normal` để biết nhãn vai có đóng góp gì không.")
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)
