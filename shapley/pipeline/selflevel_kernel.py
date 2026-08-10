# KHẢO SÁT: 1.5B TỰ ĐÁNH GIÁ LEVEL ĐỘ KHÓ — có dùng được để route pipeline không?
#
# Câu hỏi: thay vì label level do con người gán (kém khớp model nhỏ), CHÍNH con Qwen2.5-1.5B
# đọc đề và tự chấm độ khó 1-5. Độ khó này có tương quan với "S-alone có giải được không" không?
#
# Nếu có tương quan -> level tự chấm là tín hiệu routing khả thi (câu dễ -> S-only, khó -> full).
# Nếu không -> phải dùng tín hiệu khác (vd đồng thuận K-mẫu, như difficulty_strata.md dự đoán).
#
# Thiết kế:
#   - 150 câu MATH test (math_500_test.csv), idx 0-149 -- KHỚP trace results_rescue/math
#   - Qwen 1.5B: prompt "Rate difficulty of problem 1-5". Đọc số level -> self_level
#   - Song song, lấy level GỐC Hendrycks (từ MATH/train, join theo exact problem text) -> true_level
#   - Xuất: {idx, q, self_level, true_level} thành level_assigned.json
#   - Phân tích tương quan offline (trace rescue có alone_correct cho từng idx)
#
# Lưu ý prompt: yêu cầu TRẢ VỀ ĐÚNG 1 SỐ 1-5, dùng few-shot để model không trả lời lan man.
import os, re, json, glob, random, csv
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

N    = __N__
BS   = __BS__
TEMP = 0.0

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
print("MODEL", MODEL, flush=True)
# dataset hendrycks chứa MATH/train/**/*.json (có level gốc) + test csv
FILES = glob.glob("/kaggle/input/**/MATH/train/**/*.json", recursive=True)
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)
print(f"MATH train json: {len(FILES)}; test csv found: {len(CSV)}", flush=True)
if not CSV:
    raise FileNotFoundError("khong thay math_500_test.csv :: "
                            + str(glob.glob('/kaggle/input/**', recursive=True)[:30]))

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map="auto").eval()
print("model loaded", flush=True)

def gen(usrs, mx=16):
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i + BS]
        ps = [tok.apply_chat_template([{"role": "system", "content": SYS},
                                       {"role": "user", "content": u}],
                                      tokenize=False, add_generation_prompt=True) for u in ch]
        e = tok(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False,
                               pad_token_id=tok.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tok.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    return outs

SYS = ("You are a math difficulty rater. Given a competition math problem, classify its "
       "difficulty as a single integer 1, 2, 3, 4, or 5 (1 = easiest, 5 = hardest). "
       "Reply with ONLY the number, no explanation.")

def read_level(text):
    m = re.findall(r"[1-5]", text or "")
    return m[0] if m else None

# ---- load MATH test csv (math_500_test) ----
rows = list(csv.DictReader(open(CSV[0], encoding="utf-8")))[:N]
qs = [r["Question"].strip().replace("\n", " ") for r in rows]
# đảm bảo thứ tự khớp math_500 (Kernel khác đã dùng csv này với idx 0-149)
print(f"test rows: {len(rows)}", flush=True)

# ---- load MATH/train để lấy level gốc (join theo problem text) ----
true_level = {}
for p in FILES:
    try:
        d = json.load(open(p, encoding="utf-8"))
        if d.get("problem"):
            true_level[d["problem"].strip().replace("\n", " ")] = d.get("level", None)
    except Exception:
        continue
print(f"train problems indexed: {len(true_level)}", flush=True)

# ---- generate self level ----
self_levels = gen([f"Problem: {q}\nDifficulty (1-5):" for q in qs])
levels = [read_level(s) for s in self_levels]

out = []
for i, q in enumerate(qs):
    out.append({"idx": i, "q": q, "self_level": levels[i],
                "true_level": true_level.get(q)})

json.dump(out, open("/kaggle/working/level_assigned.json", "w"), indent=1, ensure_ascii=False)
nl = sum(1 for o in out if o["self_level"] is not None)
nt = sum(1 for o in out if o["true_level"] is not None)
print(f"\nparsed self_level: {nl}/{len(out)} | true_level matched: {nt}/{len(out)}", flush=True)
print("SUMMARY", json.dumps({"n": len(out), "n_self": nl, "n_true": nt}), flush=True)
print("done", flush=True)