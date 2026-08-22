#!/usr/bin/env python3
"""Gộp `pairs.jsonl` từ các shard genpref, khử trùng, và kiểm chất lượng cặp.

Sau khi tải kết quả các shard về `results_genpref/s<k>/`, chạy:
    python analysis/merge_pairs.py
-> ghi `results_genpref/pairs_all.jsonl` và in thống kê để đối chiếu với ước tính yield 44%.

Kiểm luôn hai thứ dễ sai mà chỉ đọc số tổng thì không thấy:
  1. `chosen` có thật sự đúng và `rejected` có thật sự sai không (chấm lại độc lập).
  2. Bao nhiêu cặp có `rejected` đúng là ứng viên Aggregator đã chọn — đó mới là cặp dạy
     trực tiếp vào lỗi đã đo, phần còn lại chỉ là cặp đúng/sai chung chung.
"""
import json, re, sys, io
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results_genpref"

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

def pred(t):
    b = boxed(t)
    if b is not None:
        return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I)
    return m[-1].strip() if m else None

def main():
    if not RES.exists():
        print(f"chưa có {RES} — tải kết quả shard về trước")
        return
    pairs, seen, n_traces = [], set(), 0
    for f in sorted(RES.glob("*/pairs.jsonl")):
        cnt = 0
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            p = json.loads(line)
            key = (p.get("shard"), p.get("idx"))
            if key in seen:
                continue
            seen.add(key)
            pairs.append(p)
            cnt += 1
        print(f"  {f.parent.name}: {cnt} cặp")
    for f in sorted(RES.glob("*/traces.jsonl")):
        n_traces += sum(1 for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip())

    if not pairs:
        print("không có cặp nào")
        return

    print(f"\nTỔNG: {len(pairs)} cặp / {n_traces} câu đã chạy "
          f"(yield {100*len(pairs)/n_traces if n_traces else 0:.0f}%, ước tính 44%)")

    # kiểm chất lượng: chấm lại độc lập
    bad_chosen = sum(1 for p in pairs if not eq(pred(p["chosen"]), p["gold"]))
    bad_rej = sum(1 for p in pairs if eq(pred(p["rejected"]), p["gold"]))
    print(f"\nKIỂM CHẤT LƯỢNG (chấm lại độc lập):")
    print(f"  chosen KHÔNG đúng : {bad_chosen}  (phải là 0)")
    print(f"  rejected LẠI đúng : {bad_rej}  (phải là 0)")

    direct = sum(1 for p in pairs if p.get("rejected_is_agg_choice"))
    aggwrong = sum(1 for p in pairs if p.get("agg_was_wrong"))
    print(f"\n  cặp mà rejected ĐÚNG LÀ ứng viên Aggregator đã chọn: {direct} "
          f"({100*direct/len(pairs):.0f}%)  <- dạy trực tiếp vào lỗi đã đo")
    print(f"  cặp từ câu mà Aggregator vốn đã chọn SAI: {aggwrong} "
          f"({100*aggwrong/len(pairs):.0f}%)")

    lv = Counter(p.get("level", "?") for p in pairs)
    ty = Counter(p.get("type", "?") for p in pairs)
    print(f"\n  theo độ khó: {dict(sorted(lv.items()))}")
    print(f"  theo chủ đề: {dict(sorted(ty.items(), key=lambda x: -x[1])[:6])}")

    out = RES / "pairs_all.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for p in pairs:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"\n-> đã ghi {out} ({len(pairs)} cặp)")
    print("\nBƯỚC TIẾP: đọc tay vài cặp trước khi train —")
    print("  python -c \"import json;d=[json.loads(l) for l in open(r'%s',encoding='utf-8')];"
          "p=d[0];print(p['gold']);print('--CHOSEN--');print(p['chosen'][-400:]);"
          "print('--REJECTED--');print(p['rejected'][-400:])\"" % out)

if __name__ == "__main__":
    main()
