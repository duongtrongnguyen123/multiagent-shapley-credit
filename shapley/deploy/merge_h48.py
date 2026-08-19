#!/usr/bin/env python3
"""Gop H48 (dang ky truoc #54): quy tac bao hoa (#51) co dung tren CODE khong?
Cham CHI bang assert[1..2] (truong 'held'). In thang ra hang nao cua #54 khop."""
import sys, json, glob
from collections import defaultdict

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h48"
cells, quant = defaultdict(list), defaultdict(set)
for f in sorted(glob.glob(f"{RES}/**/res_H48s*.json", recursive=True)):
    d = json.load(open(f))
    cells[f"mbpp-{d['size']}"] += d["items"]; quant[f"mbpp-{d['size']}"].add(d.get("quant", "?"))

if len(cells) < 2:
    print(f"CANH BAO: chi thay {len(cells)} o (can 2) -> CHUA du de doc bang khoa #54")

def vb(probes):
    """bo phieu theo HANH VI tren dau ra cua loi goi assert[0]; bo cac ban loi"""
    c = {}
    for i, d in enumerate(probes):
        o = d.get("out")
        if isinstance(o, str) and o.startswith("ERR:"): continue
        c.setdefault(o, []).append(i)
    return probes[max(c.values(), key=len)[0]]["held"] if c else False

print(f"{'o':10s}{'n':>5s}{'bien dich':>11s}{'greedy':>9s}{'maj3':>8s}{'A_neo':>8s}{'B_khong':>9s}"
      f"{'delta_seq(A)':>14s}{'A-B':>8s}")
rows = []
for key in sorted(cells):
    its = cells[key]; n = len(its)
    comp = sum(1 for x in its for p in [x["greedy"]] + x["samp"] if p.get("compiles")) / max(n*4, 1)
    g  = round(sum(x["greedy"]["held"] for x in its) / n, 4)
    m3 = round(sum(vb(x["samp"]) for x in its) / n, 4)
    A  = round(sum(x["A"]["held"] for x in its) / n, 4)
    B  = round(sum(x["B"]["held"] for x in its) / n, 4)
    print(f"{key:10s}{n:5d}{comp:11.3f}{g:9.4f}{m3:8.4f}{A:8.4f}{B:9.4f}{A-m3:+14.4f}{A-B:+8.4f}"
          + ("" if comp >= .50 else "  SUYBIEN"))
    rows.append({"cell": key, "n": n, "compile": round(comp, 3), "greedy": g, "maj3": m3,
                 "A_anchor": A, "B_noanchor": B, "delta_seq": round(A-m3, 4),
                 "A_minus_B": round(A-B, 4), "valid": comp >= .50 and n >= 400})

good = [r for r in rows if r["valid"]]
print("\n-- bang khoa #54 (luoi toan #51: >0 khi greedy<.60, <0 khi greedy>.85) --")
for r in good:
    print(f"  {r['cell']:10s} greedy={r['greedy']:.4f}  delta_seq={r['delta_seq']:+.4f}  A-B={r['A_minus_B']:+.4f}")
small = [r for r in good if r["greedy"] < .60]
if not good:
    print("  khong co o hop le -> khong ket luan")
elif small and all(r["delta_seq"] > 0 for r in small):
    print("  -> HANG 1: quy tac bao hoa DUNG CA TREN CODE. That bai o H44/H47 la do do tren")
    print("     NHOM ESCALATE (quan the da loc), khong phai do mien code.")
elif small and all(r["delta_seq"] < 0 for r in small):
    print("  -> HANG 2: quy tac bao hoa KHONG ap dung cho CODE. #85 chi dung cho TOAN.")
    print("     PHAI sua phat bieu da ghi o vong #87.")
elif all(abs(r["delta_seq"]) < .02 for r in good):
    print("  -> HANG 3: tuan tu TRUNG TINH tren code; thiet hai truoc day do loc theo nhom escalate.")
else:
    print("  -> HON HOP: doc tung o mot, khong khai quat.")
for r in good:
    if r["greedy"] > .60 and r["delta_seq"] > 0:
        print(f"  -> HANG 4 khop o {r['cell']}: diem doi dau .62-.71 uoc luong o #85 SAI, phai bo con so do.")
    if r["A_minus_B"] < -.05:
        print(f"  -> HANG 5 khop o {r['cell']}: mo neo hai tren code KE CA khi khong escalate.")

json.dump(rows, open(f"{RES}/H48_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H48_merged.json")
