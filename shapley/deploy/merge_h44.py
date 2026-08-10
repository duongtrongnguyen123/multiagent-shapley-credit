#!/usr/bin/env python3
"""Gop H44 (dang ky truoc #50): tren CUNG nhom escalate, so ba HANH DONG
  A) tuan tu CO mo neo   (2 luot 7B)
  B) tuan tu KHONG mo neo (2 luot 7B)  <- chi khac A o cho co dua code cu vao hay khong
  C) lay mau maj@3        (3 luot 7B)
Cham CHI bang assert[1..2]. In thang ra hang nao cua bang khoa #50 khop.
"""
import sys, json, glob

RES  = sys.argv[1] if len(sys.argv) > 1 else "res_h44"
NEED = int(sys.argv[2]) if len(sys.argv) > 2 else 12

items, shards, quants = [], set(), set()
for f in sorted(glob.glob(f"{RES}/res_H44s*.json")):
    d = json.load(open(f))
    shards.add(d["shard"]); quants.add(d.get("quant_big", "?"))
    items += d["items"]
print(f"gop {len(shards)}/{NEED} shard, {len(items)} bai, 7B: {sorted(quants)}")
missing = sorted(set(range(NEED)) - shards)
if missing: print(f"THIEU shard: {missing} — KHONG doc ket qua cho den khi du")

allp = [p for it in items for p in it["small"] + it["big"]]
comp = sum(1 for p in allp if p.get("compiles")) / max(len(allp), 1)
print(f"ti le bien dich duoc: {comp:.3f} ({'DAT' if comp>=.50 else 'KHONG DAT -> HUY'})")

def vb(pr, k):
    c = {}
    for i, d in enumerate(pr[:k]):
        o = d.get("out")
        if isinstance(o, str) and o.startswith("ERR:"): continue
        c.setdefault(o, []).append(i)
    return pr[max(c.values(), key=len)[0]]["held"] if c else False

esc = [it for it in items if it["esc_oracle"]]
pe = len(esc) / len(items)
print(f"\nnhom escalate (bo dinh tuyen oracle): {len(esc)}/{len(items)} = {pe:.3f} "
      f"({'HOP LE' if .15 <= pe <= .85 else 'SUY BIEN -> khong doc'})")
if len(esc) < 100:
    print(f"n_escalate = {len(esc)} < 100 -> DUOI NGUONG da khoa, khong ket luan")

def r(sub, f): return round(sum(bool(f(x)) for x in sub) / len(sub), 4) if sub else None
A = r(esc, lambda x: x["seq"]["held"] if x.get("seq") else False)
B = r(esc, lambda x: x["noanchor"]["held"] if x.get("noanchor") else False)
C = r(esc, lambda x: vb(x["big"], 3))

print(f"\nTREN NHOM ESCALATE (n={len(esc)}):")
print(f"  A) tuan tu CO mo neo    = {A:.4f}   (2 luot 7B)")
print(f"  B) tuan tu KHONG mo neo = {B:.4f}   (2 luot 7B)")
print(f"  C) lay mau maj@3        = {C:.4f}   (3 luot 7B)")
print(f"\n  B - A = {B-A:+.4f}   <- tac dung RIENG cua MO NEO")
print(f"  C - B = {C-B:+.4f}   <- lay mau vs tuan tu khi DA BO mo neo")
print(f"  C - A = {C-A:+.4f}   <- so voi #81/#82 (+.1159 / +.1164)")

print("\n-- bang khoa #50 --")
if B - A >= .05:
    print("  -> HANG 1: MO NEO LA THU PHAM. Dua code sai vao khien model VA thay vi viet lai.")
elif A - B >= .05:
    print("  -> HANG 3: mo neo GIUP -> phai RUT LAI phat bieu co che o vong #82.")
else:
    print("  -> HANG 2: mo neo KHONG phai nguyen nhan; chinh LUOT TU KIEM tren code gay hai (khop H35).")
if C - B >= .05:
    print("  -> HANG 4 cung khop: bo mo neo roi lay mau VAN hon -> ket luan la LAY MAU vs TUAN TU.")

json.dump({"n": len(items), "n_esc": len(esc), "pct_esc": round(pe, 4), "compile_rate": round(comp, 4),
           "A_anchor": A, "B_noanchor": B, "C_maj3": C,
           "B_minus_A": round(B-A, 4), "C_minus_B": round(C-B, 4), "C_minus_A": round(C-A, 4),
           "shards": sorted(shards)}, open(f"{RES}/H44_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H44_merged.json")
if missing: print("NHAC LAI: con thieu shard — CHUA du de ket luan")
