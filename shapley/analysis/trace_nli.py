#!/usr/bin/env python3
"""Lớp NLP #2 — NLI. Phân loại quan hệ giữa lời giải Solver và lời giải Verifier
(mâu thuẫn / kéo theo / trung tính) để bắt hành vi hội thoại: Verifier ĐỒNG Ý (kéo theo)
hay PHẢN BÁC (mâu thuẫn). Ghép với đúng/sai (gold) -> phân biệt SỬA vs PHÁ. LOCAL/CPU.

KẾT QUẢ PILOT (40 trace GSM8K): NLI > embedding ở việc bắt 'đồng ý' — GIỮ đáp án ->
kéo-theo 15/24; SỬA -> mâu-thuẫn 3/5. NHƯNG yếu ở 'PHÁ' (0/3) vì NLI off-the-shelf
không giỏi so hai lời giải toán DÀI nhiều bước => motivation để TRAIN credit critic."""
import json, numpy as np
from collections import Counter, defaultdict
from pathlib import Path
from sentence_transformers import CrossEncoder

BASE = Path(__file__).resolve().parents[1]
T = json.loads((BASE / "results_trace/traces.json").read_text())
ce = CrossEncoder("cross-encoder/nli-deberta-v3-small")   # [contradiction, entailment, neutral]
LAB = ["mâu thuẫn", "kéo theo", "trung tính"]

def category(t):
    ch = t["sa"] != t["va"]
    return ("PHÁ" if t["s_ok"] and not t["v_ok"] and ch else
            "SỬA" if not t["s_ok"] and t["v_ok"] and ch else
            "đổi-khác" if ch else "GIỮ")

labs = [int(np.argmax(s)) for s in
        ce.predict([(t["sol"][:1000], t["ver"][:1000]) for t in T], apply_softmax=True, batch_size=8)]
by = defaultdict(Counter)
for t, l in zip(T, labs):
    by[category(t)][LAB[l]] += 1

print(f"{'nhóm':10s} {'n':>3s}  {'mâu thuẫn':>10s} {'kéo theo':>9s} {'trung tính':>11s}")
for c in ["GIỮ", "SỬA", "PHÁ", "đổi-khác"]:
    cc = by[c]; n = sum(cc.values())
    if n:
        print(f"{c:10s} {n:>3d}  {cc['mâu thuẫn']:>10d} {cc['kéo theo']:>9d} {cc['trung tính']:>11d}")
json.dump([{"cat": category(t), "nli": LAB[l], "sa": t["sa"], "va": t["va"], "gold": t["gold"]}
           for t, l in zip(T, labs)],
          open(BASE / "results_trace/nli_out.json", "w"), ensure_ascii=False, indent=1)
