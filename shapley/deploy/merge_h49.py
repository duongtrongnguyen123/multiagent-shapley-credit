#!/usr/bin/env python3
"""Gop H49 (dang ky truoc #55): lap ke hoach co dang mot luot khong, khi bai du dai?
BigCodeBench. Bon nhanh cung 3 luot. In thang ra hang nao cua #55 khop."""
import sys, json, glob
from collections import defaultdict

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h49"
cells, quant = defaultdict(list), defaultdict(set)
for f in sorted(glob.glob(f"{RES}/**/res_H49s*.json", recursive=True)):
    d = json.load(open(f))
    k = f"bcb-{d['size']}"
    cells[k] += d["items"]; quant[k].add(d.get("quant", "?"))
if len(cells) < 2:
    print(f"CANH BAO: chi thay {len(cells)} o (can 2) -> CHUA du de doc bang khoa #55")

def maj3(x):
    """bo phieu tren 3 mau: code khac nhau nen bo phieu theo KET QUA TEST (dat/khong).
    Lay the da so; hoa thi lay mau dau."""
    p = [s["pass"] for s in x["samp"]]
    return sum(p) >= 2

print(f"{'o':9s}{'n':>5s}{'chay duoc':>11s}{'greedy':>9s}{'maj3':>8s}{'seq':>8s}{'PSV':>8s}"
      f"{'PSV-maj3':>10s}{'PSV-seq':>9s}{'seq-maj3':>10s}")
rows = []
for key in sorted(cells):
    its = cells[key]; n = len(its)
    runs = sum(1 for x in its if x["greedy"]["runs"]) / max(n, 1)
    g  = round(sum(x["greedy"]["pass"] for x in its) / n, 4)
    m3 = round(sum(maj3(x) for x in its) / n, 4)
    sq = round(sum(x["seq"]["pass"] for x in its) / n, 4)
    pv = round(sum(x["psv"]["pass"] for x in its) / n, 4)
    print(f"{key:9s}{n:5d}{runs:11.3f}{g:9.4f}{m3:8.4f}{sq:8.4f}{pv:8.4f}"
          f"{pv-m3:+10.4f}{pv-sq:+9.4f}{sq-m3:+10.4f}")
    rows.append({"cell": key, "n": n, "runnable": round(runs, 3), "greedy": g, "maj3": m3,
                 "seq": sq, "psv": pv, "psv_minus_maj3": round(pv-m3, 4),
                 "psv_minus_seq": round(pv-sq, 4), "seq_minus_maj3": round(sq-m3, 4),
                 "valid": (.05 <= m3 <= .95) and n >= 250 and runs >= .50})

good = [r for r in rows if r["valid"]]
print("\n-- bang khoa #55 --")
for r in rows:
    if not r["valid"]:
        print(f"  {r['cell']}: SUY BIEN (maj3={r['maj3']}, n={r['n']}, chay duoc={r['runnable']}) -> khong doc")
for r in good:
    a, b, c = r["psv_minus_maj3"], r["psv_minus_seq"], r["seq_minus_maj3"]
    print(f"  {r['cell']:9s} PSV-maj3={a:+.4f}  PSV-seq={b:+.4f}  seq-maj3={c:+.4f}")
    if a >= .02 and b >= .02:
        print("     -> HANG 1: LAP KE HOACH CO GIA TRI khi bai du dai. Ket qua null truoc day la do BO DU LIEU ngan.")
    elif abs(b) < .02 and a > 0 and c > 0:
        print("     -> HANG 2: LUOT THEM moi quan trong, KHONG phai noi dung luot do (khop #87).")
    elif a <= 0 and c > 0:
        print("     -> HANG 4: tuan tu giup nhung RIENG lap ke hoach gay hai (tieu mot luot khong sinh code).")
    elif a <= 0:
        print("     -> HANG 3: lap ke hoach KHONG dang mot luot KE CA tren bai dai nhieu buoc.")
    else:
        print("     -> khong khop hang nao ro rang; doc tung so mot.")
json.dump(rows, open(f"{RES}/H49_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H49_merged.json")
