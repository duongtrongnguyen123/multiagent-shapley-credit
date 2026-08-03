#!/usr/bin/env python3
"""Lớp NLP #1 — NOVELTY bằng embedding. Encode từng message trong trace, đo mỗi turn
'mới' bao nhiêu so với các turn trước (1 - cosine). Verifier chỉ paraphrase -> novelty
thấp; thêm bước mới -> novelty cao. Chạy LOCAL/CPU (all-MiniLM). Đọc results_trace/traces.json.

KẾT QUẢ PILOT (40 trace GSM8K, 1.5B): novelty thô BỊ CONFOUND bởi độ dài —
Verifier LUÔN giải lại nên luôn 'novel'; corr(novelty, đổi-đáp-án) = -0.16 (SAI hướng).
=> embedding thô là tín hiệu yếu; dùng NLI (trace_nli.py) hoặc mức-câu + kiểm soát độ dài."""
import json, numpy as np, statistics as st
from pathlib import Path
from sentence_transformers import SentenceTransformer

T = json.loads((Path(__file__).resolve().parents[1] / "results_trace/traces.json").read_text())
m = SentenceTransformer("all-MiniLM-L6-v2")
emb = lambda x: m.encode(x or " ", normalize_embeddings=True)
cos = lambda a, b: float(np.dot(a, b))

def category(t):
    ch = t["sa"] != t["va"]
    return ("PHÁ" if t["s_ok"] and not t["v_ok"] and ch else
            "SỬA" if not t["s_ok"] and t["v_ok"] and ch else
            "đổi-khác" if ch else "GIỮ")

rows = []
for t in T:
    es, ev = emb(t["sol"]), emb(t["ver"])
    rows.append((category(t), 1 - cos(ev, es)))       # novelty của Verifier vs Solver

print(f"{'nhóm':10s} {'n':>3s} {'novelty_V TB':>13s}")
for c in ["GIỮ", "SỬA", "PHÁ", "đổi-khác"]:
    v = [r[1] for r in rows if r[0] == c]
    if v:
        print(f"{c:10s} {len(v):>3d} {st.mean(v):>13.3f}")
y = [0 if r[0] == "GIỮ" else 1 for r in rows]
x = [r[1] for r in rows]
print(f"\ncorr(novelty_V, đổi-đáp-án) = {np.corrcoef(x, y)[0, 1]:+.3f}  (âm = tín hiệu confound)")
