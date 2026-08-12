# KHẢO SÁT: Planner 1.5B có decompose bài thành sub-question JSON được không?
#
# Ý tưởng pipeline mới: Planner decompose bài -> Solver trả lời từng sub-question (kế thừa kết
# quả bước trước) -> final = answer sub-question cuối. Không cần Verifier/Aggregator.
#
# Trước khi xây pipeline đắt, khảo sát điều quyết định: Planner 1.5B có sinh JSON sub-question
# parse được không, và decompose có hợp lý không. Cùng họ fail backward v1 (mô tả không đủ model
# làm đúng) — nên đo parse rate trước.
#
# 30 câu mỗi task (nhanh, chỉ 1 planner call/câu). Đo:
#   - parse_rate: bao nhiêu % output Java parse được thành JSON list
#   - n_sub: số sub-question trung bình
#   - ví dụ decompose thật để đánh giá chất lượng
import os, re, json, glob, csv, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

TASK = "__TASK__"     # math | gsm8k
BS   = __BS__
N    = 30

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
FNAME = "math_500_test.csv" if TASK == "math" else "main_test.csv"
CSV = sorted(glob.glob(f"/kaggle/input/**/{FNAME}", recursive=True), key=len)[0]
ALL = list(csv.DictReader(open(CSV, encoding="utf-8")))[:N]
print(f"TASK={TASK} N={N}", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="auto").eval()
print("model loaded", flush=True)

DECOMPOSE_SYS = ("You are a math decomposition assistant. Given a math word problem, break it "
                 "into a sequence of sub-questions that lead step by step to the answer. Each "
                 "sub-question should ask for ONE computation. Return ONLY a JSON array of "
                 "strings, e.g. [\"Sub-question 1 text\", \"Sub-question 2 text\"]. No extra "
                 "text.")

def gen(usrs, mx=256):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = [tok.apply_chat_template([{"role": "system", "content": DECOMPOSE_SYS},
                                       {"role": "user", "content": u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False,
                               pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    return outs

if TASK == "math":
    q_of = lambda r: r["Question"].strip()
elif TASK == "gsm8k":
    q_of = lambda r: r["question"].strip()

qs = [q_of(r) for r in ALL]
outs = gen(list(qs))

def parse_json(s):
    """Trích JSON array từ output model (có thể bọc thêm text)."""
    if not s:
        return None
    m = re.search(r'\[.*\]', s, re.S)
    if not m:
        return None
    try:
        arr = json.loads(m.group(0))
        if isinstance(arr, list) and all(isinstance(x, str) for x in arr):
            return arr
    except Exception:
        pass
    return None

parsed = 0
ok_sub = []
fail_examples = []
success_examples = []
for i, (q, out) in enumerate(zip(qs, outs)):
    arr = parse_json(out)
    if arr is not None and len(arr) >= 1:
        parsed += 1
        try:
            nsub = len(arr)
            ok_sub.append(nsub)
            if len(success_examples) < 3:
                success_examples.append({"idx": i, "q": q[:80], "subs": arr[:4]})
        except Exception:
            pass
    else:
        if len(fail_examples) < 3:
            fail_examples.append({"idx": i, "q": q[:60], "out": out[:120]})

n = len(qs)
print(f"\nparse_rate: {parsed}/{n} ({parsed/n*100:.0f}%)")
if ok_sub:
    import statistics
    print(f"n_sub trung binh (trong cau parse duoc): {statistics.mean(ok_sub):.1f}")
print(f"\n=== {len(success_examples)} vi du decompose thanh cong ===")
for ex in success_examples:
    print(f"--- #{ex['idx']} — {ex['q']} ---")
    for s in ex["subs"]:
        print(f"  - {s}")
    print()
print(f"=== {len(fail_examples)} vi du fail parse ===")
for ex in fail_examples:
    print(f"--- #{ex['idx']}: {ex['out']}")
    print()

json.dump({"task": TASK, "n": n, "parse_rate": parsed / n,
           "n_sub_mean": statistics.mean(ok_sub) if ok_sub else 0,
           "success": success_examples, "fail": fail_examples},
          open("/kaggle/working/decompose_survey.json", "w"), indent=2, ensure_ascii=False)
print("done", flush=True)