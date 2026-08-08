# SINH DỮ LIỆU PREFERENCE cho Aggregator — chạy trên MATH *train* (không đụng test).
#
# Bối cảnh (docs/EXTRA_PASS_FINDING.md, docs/AGG_FORMAT_CHECK.md):
#   Solver .413 | agg3 .467 | vote5 .507 | ORACLE .673
#   -> còn 17 điểm headroom giữa bỏ phiếu và oracle. Trong các ca vote5 sai, 35% VẪN CÓ ứng
#   viên đúng nằm sẵn, chỉ bị chọn nhầm. Và 86% lỗi của Aggregator là CHỌN SAI thật (chỉ
#   11/81 ca do thiếu \boxed). Đây là bài toán selection -> hợp với preference optimization.
#
# Cấu hình khớp đúng nhánh `agg3` đã đo: K=3 ứng viên ĐỀU LÀ SOLVER, KHÔNG có Verifier.
# (aggk_folds_kernel.py:157 — agg3 = 1 Solver greedy + 2 Solver sample. Nhánh có Verifier là
#  agg2 và nó tệ nhất: .407 / 1-5 fold, so với agg3 .467 / 5-5 fold.)
#
# Cặp preference phải nằm TRONG CÙNG một prompt (đây là điểm dễ nhầm với binary classification):
#   prompt   = đề bài + K ứng viên   (đúng format Aggregator nhận lúc inference)
#   chosen   = ứng viên có đáp án ĐÚNG
#   rejected = ứng viên Aggregator đã chọn nhưng SAI (không xác định được thì lấy ứng viên sai)
#
# Sharding: mỗi kernel xử lý ALL[SHARD::N_SHARDS] — bước nhảy chứ không phải khối liên tiếp,
# để các shard có phân bố chủ đề/độ khó tương đương (MATH xếp theo thư mục algebra, geometry...).
#
# Checkpoint sau MỖI câu (JSONL append) — bài học vòng debate: mất 11h vì chỉ ghi ở dòng cuối.
import os, re, json, glob, random
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N        = __N__          # số câu shard này xử lý (đã chia sẵn)
SHARD    = __SHARD__
N_SHARDS = __N_SHARDS__
BS       = __BS__
K        = 3              # số ứng viên; agg3 thắng agg5 ở mọi biến thể
TEMP     = 0.7            # phải sample, greedy K lần cho ra K bản y hệt

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])

# ---- nạp MATH train (Hendrycks: JSON per-file, thư mục theo chủ đề) --------
files = sorted(glob.glob("/kaggle/input/**/MATH/train/**/*.json", recursive=True))
if not files:
    raise FileNotFoundError("khong thay MATH/train/**/*.json :: "
                            + str(glob.glob("/kaggle/input/**", recursive=True)[:30]))
rows = []
for p in files:
    try:
        d = json.load(open(p, encoding="utf-8"))
        if d.get("problem") and d.get("solution"):
            rows.append({"problem": d["problem"], "solution": d["solution"],
                         "level": d.get("level", ""), "type": d.get("type", "")})
    except Exception:
        continue
random.Random(0).shuffle(rows)          # trộn cố định để shard không lệch chủ đề
rows = rows[SHARD::N_SHARDS][:N]
print(f"SHARD {SHARD}/{N_SHARDS}: {len(rows)} bai (tu {len(files)} file train)", flush=True)

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

# ---- chấm điểm: bê nguyên từ aggk_folds_kernel.py (đã vá normalizer fc2f429) ----
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

SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the final "
             "answer in \\boxed{}.")
AGG_SYS   = ("You are given a problem and one or more candidate solutions. Decide the correct "
             "final answer by re-checking. Put the final answer in \\boxed{}.")

def agg_user(q, cands):
    body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(cands))
    return f"{q}\n\n{body}"

qs = [r["problem"] for r in rows]
gs = [boxed(r["solution"]) for r in rows]
n = len(rows)

# ---- sinh K ứng viên: 1 greedy + (K-1) sample ------------------------------
print("== sinh ung vien ==", flush=True)
cands = [gen(SOLVE_SYS, list(qs), 1024)]
for k in range(K - 1):
    cands.append(gen(SOLVE_SYS, list(qs), 1024, do_sample=True, seed=3000 + k))
cands = [[cands[k][i] for k in range(K)] for i in range(n)]

print("== chay aggregator ==", flush=True)
agg = gen(AGG_SYS, [agg_user(qs[i], cands[i]) for i in range(n)], 1024)

# ---- lọc cặp ---------------------------------------------------------------
npair = nagg_ok = nall_wrong = nall_right = 0
for i in range(n):
    g = gs[i]
    cp = [pred(c) for c in cands[i]]
    ok = [eq(p, g) for p in cp]
    ap = pred(agg[i])
    agg_ok = eq(ap, g)
    nagg_ok += agg_ok

    rec = {"idx": i, "shard": SHARD, "problem": qs[i], "gold": g,
           "level": rows[i]["level"], "type": rows[i]["type"],
           "candidates": cands[i], "cand_pred": cp, "cand_ok": ok,
           "agg": agg[i], "agg_pred": ap, "agg_ok": bool(agg_ok)}
    with open("/kaggle/working/traces.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if not any(ok):
        nall_wrong += 1            # cả K ứng viên đều sai -> khong co gi de chon dung hon
        continue
    if all(ok):
        nall_right += 1            # khong co ung vien sai -> khong tao duoc rejected
        continue

    good = [j for j in range(K) if ok[j]]
    bad = [j for j in range(K) if not ok[j]]
    # rejected: ưu tiên đúng ứng viên mà Aggregator đã chọn (nếu nó chọn sai) -> dạy đúng lỗi
    rej = next((j for j in bad if ap is not None and eq(cp[j], ap)), bad[0])
    pair = {"idx": i, "shard": SHARD,
            "prompt": agg_user(qs[i], cands[i]),
            "chosen": cands[i][good[0]],
            "rejected": cands[i][rej],
            "gold": g, "agg_was_wrong": not bool(agg_ok),
            "rejected_is_agg_choice": bool(ap is not None and eq(cp[rej], ap)),
            "level": rows[i]["level"], "type": rows[i]["type"]}
    with open("/kaggle/working/pairs.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(pair, ensure_ascii=False) + "\n")
    npair += 1

    if npair % 25 == 0:
        print(f"  [{i+1}/{n}] {npair} cap", flush=True)

summary = {"shard": SHARD, "n_shards": N_SHARDS, "n": n, "K": K,
           "pairs": npair, "pair_yield": round(npair / n, 4) if n else 0,
           "agg_acc": round(nagg_ok / n, 4) if n else 0,
           "all_candidates_wrong": nall_wrong, "all_candidates_right": nall_right}
print("SUMMARY", json.dumps(summary), flush=True)
json.dump(summary, open("/kaggle/working/summary.json", "w"), indent=2)
print(f"\n{npair} cap tu {n} cau (yield {100*npair/n if n else 0:.0f}%, uoc tinh 44%)", flush=True)
print(f"  ca K ung vien deu sai : {nall_wrong} ({100*nall_wrong/n if n else 0:.0f}%)", flush=True)
print(f"  ca K ung vien deu dung: {nall_right} ({100*nall_right/n if n else 0:.0f}%)", flush=True)
print("done", flush=True)
