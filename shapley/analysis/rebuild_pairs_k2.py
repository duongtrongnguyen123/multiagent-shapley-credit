#!/usr/bin/env python3
"""Dựng lại cặp preference với K=2 từ trace đã có — không cần chạy lại Solver.

VÌ SAO: bản K=3 có prompt dài ~1305 token (median) vì chứa 3 lời giải đầy đủ. Với
max_prompt_length=1024 thì **75% prompt bị cắt**, mất trung bình 37% nội dung, và chỉ 25% cặp
còn nguyên vẹn hoàn toàn. Đó là hỏng đúng thứ đang dạy: model phải CHỌN giữa các ứng viên,
mà ta lại che mất chính các ứng viên đó.

K=2 giảm prompt còn ~2/3, vừa maxlen mà không phải cắt. Bài toán vẫn đúng loại lỗi cần sửa —
recency bias ở K=2 còn nặng hơn (Aggregator chép ứng viên cuối 75% ở K=2 so với 65% ở K=5).

CÁCH CHỌN 2 ỨNG VIÊN: lấy 1 đúng + 1 sai, ưu tiên cặp NGẮN NHẤT để prompt vừa ngân sách.
Ưu tiên giữ ứng viên mà Aggregator đã chọn (nếu nó chọn sai) làm `rejected`, vì đó là cặp dạy
trực tiếp vào lỗi đã đo.

THỨ TỰ ỨNG VIÊN: đặt `chosen` ở vị trí 1 và `rejected` ở vị trí 2 trong một nửa số cặp, đảo lại
ở nửa kia. Nếu để nguyên thứ tự thì model học được "chọn Candidate 1" thay vì học chọn đúng —
và với recency bias đã đo thì đây là rủi ro thật, không phải lo xa.

Chạy: python analysis/rebuild_pairs_k2.py
"""
import json, re, sys, io
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results_genpref"
OUT = RES / "pairs_k2.jsonl"
CH = 3.5          # ký tự/token ước tính cho LaTeX
MAX_PROMPT = 1024  # phải khớp max_prompt_length trong orpo_kernel

def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0:
        return None
    i = s.find("{", i)
    if i < 0:
        return None
    d, st = 0, i
    for j in range(i, len(s)):
        if s[j] == "{":
            d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0:
                return s[st + 1:j]
    return None

def norm(a):
    if a is None:
        return None
    a = str(a).strip()
    for x in ["\\left", "\\right", "\\!", "\\,", "\\;", "$", " ", ","]:
        a = a.replace(x, "")
    for x in ["\\(", "\\)", "\\[", "\\]"]:
        a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a)
    a = a.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()

def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g:
        return False
    if p == g:
        return True
    try:
        return abs(float(p) - float(g)) < 1e-6
    except (ValueError, TypeError):
        return False

def agg_user(q, cands):
    body = "\n\n".join(f"Candidate {j+1}:\n{c}" for j, c in enumerate(cands))
    return f"{q}\n\n{body}"

def main():
    files = sorted(RES.glob("*/traces.jsonl"))
    if not files:
        print(f"chưa có trace trong {RES}")
        return
    pairs, n_seen, n_mixed = [], 0, 0
    flip = 0
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            t = json.loads(line)
            n_seen += 1
            ok, cp, cands = t["cand_ok"], t["cand_pred"], t["candidates"]
            good = [j for j in range(len(cands)) if ok[j]]
            bad = [j for j in range(len(cands)) if not ok[j]]
            if not good or not bad:
                continue                       # cả đúng hoặc cả sai -> không tạo cặp được
            n_mixed += 1
            ap = t["agg_pred"]
            # rejected: ưu tiên ứng viên Aggregator đã chọn (nếu sai) -> dạy trúng lỗi
            rej_pref = [j for j in bad if ap is not None and eq(cp[j], ap)]
            rej = min(rej_pref or bad, key=lambda j: len(cands[j]))
            cho = min(good, key=lambda j: len(cands[j]))   # ngắn nhất -> prompt vừa ngân sách

            # đảo vị trí luân phiên: chống việc model học "luôn chọn Candidate 1"
            if flip % 2 == 0:
                two, chosen_pos = [cands[cho], cands[rej]], 1
            else:
                two, chosen_pos = [cands[rej], cands[cho]], 2
            flip += 1

            pairs.append({
                "idx": t["idx"], "shard": t["shard"],
                "prompt": agg_user(t["problem"], two),
                "chosen": cands[cho], "rejected": cands[rej],
                "chosen_position": chosen_pos,
                "gold": t["gold"], "level": t["level"], "type": t["type"],
                "rejected_is_agg_choice": bool(rej_pref),
                "agg_was_wrong": not t["agg_ok"],
            })

    if not pairs:
        print("không dựng được cặp nào")
        return

    # ---- kiểm chất lượng + độ dài -----------------------------------------
    def pred(t):
        b = boxed(t)
        if b is not None:
            return b
        m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
        return m[-1].strip() if m else None

    bad_c = sum(1 for p in pairs if not eq(pred(p["chosen"]), p["gold"]))
    bad_r = sum(1 for p in pairs if eq(pred(p["rejected"]), p["gold"]))
    pl = sorted(len(p["prompt"]) / CH for p in pairs)
    med = pl[len(pl) // 2]
    over = sum(1 for x in pl if x > MAX_PROMPT)
    direct = sum(1 for p in pairs if p["rejected_is_agg_choice"])
    pos1 = sum(1 for p in pairs if p["chosen_position"] == 1)

    print(f"{len(pairs)} cặp từ {n_seen} câu ({n_mixed} câu hỗn hợp)")
    print(f"\nKIỂM CHẤT LƯỢNG (chấm lại độc lập):")
    print(f"  chosen KHÔNG đúng : {bad_c}  (phải là 0)")
    print(f"  rejected LẠI đúng : {bad_r}  (phải là 0)")
    print(f"\nĐỘ DÀI PROMPT (ước tính token):")
    print(f"  median {med:.0f} · p90 {pl[int(.9*len(pl))]:.0f} · max {pl[-1]:.0f}")
    print(f"  vượt giới hạn {MAX_PROMPT}: {over}/{len(pairs)} ({100*over/len(pairs):.0f}%)"
          f"   <- K=3 trước đây là 75%")
    print(f"\n  rejected đúng là ứng viên Aggregator đã chọn: {direct} "
          f"({100*direct/len(pairs):.0f}%)")
    print(f"  chosen ở vị trí 1: {pos1}/{len(pairs)} ({100*pos1/len(pairs):.0f}%)  "
          f"<- cân bằng để không học 'luôn chọn Candidate 1'")

    with open(OUT, "w", encoding="utf-8") as fh:
        for p in pairs:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"\n-> đã ghi {OUT}")

if __name__ == "__main__":
    main()
