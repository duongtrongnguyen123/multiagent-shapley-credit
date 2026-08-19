#!/usr/bin/env python3
"""Gop H50 (dang ky truoc #56): lap ke hoach CUONG CHE. 

HAI CONG BAT BUOC, script tu ap dung (khong de nguoi doc tu nho):
 1. KIEM TRA CAN THIEP: plan_is_code_rate > .20 -> KHONG in ket luan ve lap ke hoach.
 2. `maj3` cua H49 bi HUY (chon bang ket qua test = ro ri, va >=2/3 la dieu kien hoi).
    O day KHONG dung maj3 lam moc. Cau hoi lap ke hoach tra loi bang PSV vs seq (deu 3 luot).
"""
import sys, json, glob, re
from collections import defaultdict

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h50"
FENCE = "`" * 3
cells = defaultdict(list)
for f in sorted(glob.glob(f"{RES}/**/res_H50s*.json", recursive=True)):
    d = json.load(open(f))
    cells[f"bcb-{d['size']}"] += d["items"]
if len(cells) < 2:
    print(f"CANH BAO: chi thay {len(cells)} o (can 2) -> CHUA du de doc bang khoa #56")

def is_code(p):
    p = p or ""
    return (FENCE in p) or (re.search(r"\bdef\s+\w+\s*\(", p) is not None)

print(f"{'o':9s}{'n':>5s}{'plan co code':>14s}{'greedy':>9s}{'seq':>8s}{'PSV':>8s}{'PSV-seq':>10s}{'seq-greedy':>12s}")
rows = []
for key in sorted(cells):
    its = cells[key]; n = len(its)
    pic = sum(is_code(x.get("plan_text")) for x in its) / n
    g  = round(sum(x["greedy"]["pass"] for x in its) / n, 4)
    sq = round(sum(x["seq"]["pass"] for x in its) / n, 4)
    pv = round(sum(x["psv"]["pass"] for x in its) / n, 4)
    print(f"{key:9s}{n:5d}{pic:14.1%}{g:9.4f}{sq:8.4f}{pv:8.4f}{pv-sq:+10.4f}{sq-g:+12.4f}")
    rows.append({"cell": key, "n": n, "plan_is_code_rate": round(pic, 4), "greedy": g,
                 "seq": sq, "psv": pv, "psv_minus_seq": round(pv-sq, 4),
                 "seq_minus_greedy": round(sq-g, 4), "can_read": pic <= .20 and n >= 250})

print("\n-- bang khoa #56 --")
for r in rows:
    if not r["can_read"]:
        print(f"  {r['cell']}: plan_is_code = {r['plan_is_code_rate']:.1%} > 20% (hoac n<250)")
        print(f"     -> CAN THIEP THAT BAI. KHONG ket luan gi ve lap ke hoach o o nay.")
        continue
    d = r["psv_minus_seq"]
    print(f"  {r['cell']}: plan_is_code = {r['plan_is_code_rate']:.1%} (DAT) | PSV-seq = {d:+.4f}")
    if d >= .02:
        print("     -> LAP KE HOACH CO GIA TRI tren bai dai: hon tuan tu o CUNG 3 luot.")
    elif abs(d) < .02:
        print("     -> LUOT THEM quan trong, NOI DUNG luot do thi KHONG (khop #87 ve mo neo).")
    else:
        print("     -> LAP KE HOACH KHONG dang mot luot, va lan nay can thiep CO dien ra.")
        print("        Ket luan am THAT (khac H49, noi can thiep khong xay ra).")

H49 = {"bcb-15": 0.1433, "bcb-7": 0.2967}
print("\n-- doi chieu voi H49 (PSV khi 'ke hoach' con la code nhap) --")
for r in rows:
    if r["cell"] in H49:
        d = r["psv"] - H49[r["cell"]]
        print(f"  {r['cell']}: PSV {H49[r['cell']]:.4f} -> {r['psv']:.4f}  ({d:+.4f})")
        if d <= -.03 and r["can_read"]:
            print("     -> Cuong che LAY MAT phan dang gia: cai giup la BAN NHAP CODE, khong phai KE HOACH.")

json.dump(rows, open(f"{RES}/H50_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H50_merged.json")
