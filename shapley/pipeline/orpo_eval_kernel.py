# EVAL adapter ORPO trên MATH-500 TEST — cùng thiết lập 5 fold với aggk_folds_kernel.py.
#
# Thay đổi DUY NHẤT so với aggk: lượt Aggregator chạy qua LoRA adapter đã train. Solver vẫn là
# model gốc, cùng seed sample, nên chênh lệch accuracy quy được về đúng một biến.
#
# SỐ ỨNG VIÊN PHẢI KHỚP LÚC TRAIN. Adapter train trên `pairs_k2.jsonl` — prompt có ĐÚNG 2
# Candidate. Vòng eval đầu tiên đưa cho nó 3 ứng viên (train/eval mismatch), nên con số .500
# ở vòng đó KHÔNG phải hiệu năng thật, và rất có thể chính mismatch gây ra `novel`=.307
# (model rơi ngoài phân bố -> thoái hoá về "giải lại từ đầu" thay vì chọn).
# Nhánh `agg3_orpo_ood` giữ lại đúng cấu hình sai đó làm ĐỐI CHỨNG: chênh lệch giữa agg2_orpo
# và agg3_orpo_ood đo trực tiếp cái giá của mismatch.
#
# Mốc đã có (MATH 1.5B, docs/ORPO_AGGREGATOR.md + AGG_FORMAT_CHECK.md):
#   S .413 | agg3 .467 | agg3+fallback .493 | vote5 .507 | oracle .673
# `vote2` là so CÙNG NGÂN SÁCH với agg2 (2 mẫu); `vote3`/`vote5` là so THỰC DỤNG (rẻ nhất mà
# tốt nhất hiện có). Báo cáo tất cả.
#
# Cũng đo lại `copies_last`: nếu accuracy không đổi mà chỉ số này giảm mạnh thì ORPO CÓ tác động
# lên hành vi, chỉ là recency bias không phải nguyên nhân chính của lỗi — vẫn là thông tin.
import os, sys, re, csv, json, glob, statistics, subprocess
from collections import Counter

os.environ["CUDA_VISIBLE_DEVICES"] = "0"   # tránh DataParallel gather (xem orpo_kernel.py)

TASK = "__TASK__"   # math = in-domain (adapter train tren MATH) | gsm8k = cross-task
N    = __N__
NF   = __NF__
BS   = __BS__
TEMP = 0.7

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft>=0.13,<0.15"], check=False)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

FOLD = N // NF
_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
_a = glob.glob("/kaggle/input/**/adapter_config.json", recursive=True)
if not _a:
    raise FileNotFoundError("khong thay adapter_config.json :: "
                            + str(glob.glob("/kaggle/input/**", recursive=True)[:30]))
ADAPTER = os.path.dirname(sorted(_a, key=len)[0])
FNAME = "main_test.csv" if TASK == "gsm8k" else "math_500_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV)))[:N]
print(f"MODEL={MODEL}\nADAPTER={ADAPTER}\n{NF} fold x {FOLD}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
base = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                            device_map={"": 0}).eval()
# một bản model duy nhất: bật/tắt adapter thay vì nạp hai lần -> vừa bộ nhớ, và đảm bảo
# Solver dùng đúng trọng số gốc
model = PeftModel.from_pretrained(base, ADAPTER, adapter_name="orpo").eval()
print("adapter loaded", flush=True)

import contextlib

@contextlib.contextmanager
def _null():
    yield

def gen(sysm, usrs, mx, do_sample=False, seed=None, use_adapter=False):
    """use_adapter=False -> tắt LoRA, chạy đúng model gốc (dùng cho Solver và agg3_base)."""
    if seed is not None:
        torch.manual_seed(seed)
    outs = []
    ctx = _null() if use_adapter else model.disable_adapter()
    with ctx:
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
            outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip()
                     for j in range(len(ch))]
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
def pred(t):
    if TASK == "gsm8k":     # đáp án là SỐ, không có \boxed -> bắt số như template.py
        m = (re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)", t or "", re.I)
             or NUM.findall(t or ""))
        return m[-1].replace(",", "") if m else None
    b = boxed(t)
    if b is not None: return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
    return m[-1].strip() if m else None

if TASK == "gsm8k":
    SOLVE_SYS = ("You are a careful math solver. Solve step by step, showing arithmetic. "
                 "End with a line: 'The answer is <number>'.")
    AGG_SYS   = ("You are given a math problem and one or more candidate solutions. Decide the "
                 "correct final answer by re-checking and majority. End with 'The answer is "
                 "<number>'.")
    q_of = lambda r: r["question"]
    def gold_of(r):
        m = re.search(r"####\s*([-\d,\.]+)", r["answer"])
        return m.group(1).replace(",", "").strip() if m else None
else:
    SOLVE_SYS = ("You are an expert mathematician. Solve the problem step by step. Put the final "
                 "answer in \\boxed{}.")
    AGG_SYS   = ("You are given a problem and one or more candidate solutions. Decide the correct "
                 "final answer by re-checking. Put the final answer in \\boxed{}.")
    q_of = lambda r: r["Question"]
    gold_of = lambda r: boxed(r["Answer"])

def agg_user(q, cands):
    body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(cands))
    return f"{q}\n\n{body}"

def majority(answers):
    keys = [norm(a) for a in answers if norm(a)]
    if not keys: return None
    top = Counter(keys).most_common(1)[0][0]
    return next((a for a in answers if norm(a) == top), None)

ARMS = ["S", "agg2_base", "agg2_orpo", "agg2_orpo_fb", "vote2",
        "agg3_orpo_ood", "vote3"]   # agg2_* khop train; agg3_* la doi chung OOD
fold_stats, sample = [], []

for f in range(NF):
    rows = ALL[f * FOLD:(f + 1) * FOLD]
    qs = [q_of(r) for r in rows]
    gs = [gold_of(r) for r in rows]
    n = len(rows)
    print(f"\n===== FOLD {f+1}/{NF} ({n} bai) =====", flush=True)

    # 3 ứng viên từ model GỐC (adapter tắt) — cùng seed với aggk để so được
    c0 = gen(SOLVE_SYS, list(qs), 1024)
    c1 = gen(SOLVE_SYS, list(qs), 1024, do_sample=True, seed=2000)
    c2 = gen(SOLVE_SYS, list(qs), 1024, do_sample=True, seed=2001)
    cands3 = [[c0[i], c1[i], c2[i]] for i in range(n)]
    # K=2 là cấu hình KHỚP LÚC TRAIN (pairs_k2.jsonl có đúng 2 Candidate). Vòng eval trước
    # dùng K=3 cho adapter train trên K=2 -> train/eval mismatch, và rất có thể chính nó gây
    # ra `novel`=.307 (model rơi ngoài phân bố nên thoái hoá về "giải lại từ đầu").
    cands2 = [[c0[i], c1[i]] for i in range(n)]
    au2 = [agg_user(qs[i], cands2[i]) for i in range(n)]
    au3 = [agg_user(qs[i], cands3[i]) for i in range(n)]

    agg2_b = gen(AGG_SYS, au2, 1024, use_adapter=False)   # base, K=2 (khớp train)
    agg2_o = gen(AGG_SYS, au2, 1024, use_adapter=True)    # ORPO, K=2 (khớp train)
    agg3_o = gen(AGG_SYS, au3, 1024, use_adapter=True)    # ORPO, K=3 (đối chứng OOD)
    vote2 = [majority([pred(c) for c in cands2[i]]) for i in range(n)]
    vote3 = [majority([pred(c) for c in cands3[i]]) for i in range(n)]

    # fallback miễn phí: không trích được đáp án -> lấy đáp án bỏ phiếu (AGG_FORMAT_CHECK.md)
    def fb(i):
        # GSM8K không dùng \boxed -> fallback khi không trích được đáp án nào
        p = boxed(agg2_o[i]) if TASK != "gsm8k" else pred(agg2_o[i])
        return p if p is not None else vote2[i]

    agg_b, agg_o, cands = agg2_b, agg2_o, cands2   # dùng cho phần lưu trace bên dưới
    ok = {
        "S":            [eq(pred(t), g) for t, g in zip(c0, gs)],
        "agg2_base":    [eq(pred(t), g) for t, g in zip(agg2_b, gs)],
        "agg2_orpo":    [eq(pred(t), g) for t, g in zip(agg2_o, gs)],
        "agg2_orpo_fb": [eq(fb(i), gs[i]) for i in range(n)],
        "vote2":        [eq(v, g) for v, g in zip(vote2, gs)],
        "agg3_orpo_ood": [eq(pred(t), g) for t, g in zip(agg3_o, gs)],
        "vote3":        [eq(v, g) for v, g in zip(vote3, gs)],
    }
    d = {f"acc_{a}": sum(ok[a]) / n for a in ARMS}
    # recency bias: có còn chép ứng viên cuối không?
    d["base_copies_last"] = sum(1 for i in range(n) if pred(agg_b[i]) is not None
                                and eq(pred(agg_b[i]), pred(cands[i][-1]))) / n
    d["orpo_copies_last"] = sum(1 for i in range(n) if pred(agg_o[i]) is not None
                                and eq(pred(agg_o[i]), pred(cands[i][-1]))) / n
    d["orpo_novel"] = sum(1 for i in range(n) if pred(agg_o[i]) is not None
                          and not any(eq(pred(agg_o[i]), pred(c)) for c in cands[i])) / n
    d["ood_novel"] = sum(1 for i in range(n) if pred(agg3_o[i]) is not None
                         and not any(eq(pred(agg3_o[i]), pred(c)) for c in cands3[i])) / n
    d["oracle"] = sum(1 for i in range(n)
                      if any(eq(pred(c), gs[i]) for c in cands[i])) / n
    d["oracle3"] = sum(1 for i in range(n)
                       if any(eq(pred(c), gs[i]) for c in cands3[i])) / n
    fold_stats.append(d)
    print("  " + " | ".join(f"{a} {d[f'acc_{a}']:.3f}" for a in ARMS), flush=True)
    print(f"  copies_last base {d['base_copies_last']:.2f} -> orpo {d['orpo_copies_last']:.2f}"
          f" | novel K2 {d['orpo_novel']:.2f} / K3-OOD {d['ood_novel']:.2f}"
          f" | oracle {d['oracle']:.3f}", flush=True)

    for i in range(n):
        sample.append({"fold": f + 1, "idx": f * FOLD + i, "q": qs[i], "gold": gs[i],
                       "candidates": cands[i], "agg_base": agg_b[i], "agg_orpo": agg_o[i],
                       "agg3_orpo_ood": agg3_o[i],
                       "pred": {"S": pred(c0[i]), "agg_base": pred(agg_b[i]),
                                "agg_orpo": pred(agg_o[i]), "vote3": vote3[i],
                                "candidates": [pred(c) for c in cands[i]]},
                       "ok": {a: ok[a][i] for a in ARMS}})
        with open("/kaggle/working/traces.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(sample[-1], ensure_ascii=False) + "\n")

    json.dump({"folds_done": f + 1, "n_folds": NF, "fold_size": FOLD,
               "complete": f + 1 == NF, "per_fold": fold_stats},
              open("/kaggle/working/summary.json", "w"), indent=2)
    json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
    print(f"  [checkpoint] {f+1}/{NF} fold", flush=True)

def stats(xs):
    return {"mean": round(statistics.mean(xs), 4), "min": round(min(xs), 4),
            "max": round(max(xs), 4), "by_fold": [round(x, 4) for x in xs]}

out = {"n_folds": NF, "fold_size": FOLD, "complete": True, "arms": {}}
base = [d["acc_agg2_base"] for d in fold_stats]
print("\n" + "=" * 76)
print(f"{'nhanh':<16} {'mean':>7} {'min':>7} {'max':>7} | {'vs agg3_base':>13} {'fold':>6}")
print("=" * 76)
for a in ARMS:
    accs = [d[f"acc_{a}"] for d in fold_stats]
    diffs = [x - b for x, b in zip(accs, base)]
    same = (sum(1 for x in diffs if x > 0) if statistics.mean(diffs) >= 0
            else sum(1 for x in diffs if x < 0))
    out["arms"][a] = {"acc": stats(accs), "delta_vs_base": stats(diffs),
                      "folds_same_sign": f"{same}/{NF}"}
    print(f"{a:<16} {statistics.mean(accs):>7.3f} {min(accs):>7.3f} {max(accs):>7.3f} | "
          f"{statistics.mean(diffs):>+13.3f} {same:>4}/{NF}")

for k in ("base_copies_last", "orpo_copies_last", "orpo_novel", "ood_novel",
          "oracle", "oracle3"):
    out[k] = stats([d[k] for d in fold_stats])
    print(f"  {k:<20} {out[k]['mean']:.3f}")

print("\nMOC SO SANH (MATH 1.5B da do): S .413 | agg3 .467 | +fallback .493 | "
      "vote5 .507 | oracle .673")
print("TIEU CHI: agg3_orpo > .507 VA 5/5 fold cung dau -> ket qua duong that.")
print("\nSUMMARY", json.dumps(out), flush=True)
json.dump({**out, "per_fold": fold_stats}, open("/kaggle/working/summary.json", "w"), indent=2)
json.dump(sample, open("/kaggle/working/traces.json", "w"), indent=1)
print("done", flush=True)
