#!/usr/bin/env python3
"""Gop H51 (dang ky truoc #57): 7B lap ke hoach, 1.5B thuc thi.
Cong kiem tra can thiep tu ap dung. Chi phi quy ve FLOP 1.5B (1 luot 7B = 5.07)."""
import sys, json, glob, re

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h51"
FENCE = "`" * 3
RATIO = 7.6 / 1.5
items = []
for f in sorted(glob.glob(f"{RES}/**/res_H51s*.json", recursive=True)):
    items += json.load(open(f))["items"]
n = len(items)
print(f"gop {len(glob.glob(f'{RES}/**/res_H51s*.json', recursive=True))} shard, {n} bai")
if n < 250:
    print(f"n = {n} < 250 -> CHUA du de doc bang khoa #57")

def is_code(p):
    p = p or ""
    return (FENCE in p) or (re.search(r"\bdef\s+\w+\s*\(", p) is not None)
pic = sum(is_code(x.get("plan_text")) for x in items) / max(n, 1)
runs = sum(1 for x in items if x["small_greedy"]["runs"]) / max(n, 1)
print(f"kiem tra can thiep: 'ke hoach' chua code {pic:.1%} -> {'DAT' if pic <= .20 else 'TRUOT'}")
print(f"ti le chay duoc: {runs:.3f}")

A = {k: round(sum(x[k]["pass"] for x in items) / n, 4)
     for k in ("small_greedy", "small_seq", "bigplan_smallsolve", "big_greedy")}
COST = {"small_greedy": 1.00, "small_seq": 3.00,
        "bigplan_smallsolve": round(RATIO + 2, 2), "big_greedy": round(RATIO, 2)}
print(f"\n{'nhanh':22s}{'acc':>9s}{'chi phi':>10s}")
for k in ("small_greedy", "small_seq", "big_greedy", "bigplan_smallsolve"):
    print(f"{k:22s}{A[k]:9.4f}{COST[k]:10.2f}")

bp, ss, bg = A["bigplan_smallsolve"], A["small_seq"], A["big_greedy"]
print(f"\n  bigplan_smallsolve - small_seq  = {bp-ss:+.4f}")
print(f"  bigplan_smallsolve - big_greedy = {bp-bg:+.4f}   (dat hon {COST['bigplan_smallsolve']-COST['big_greedy']:+.2f} don vi chi phi)")

print("\n-- bang khoa #57 --")
if pic > .20 or n < 250 or runs < .50:
    print("  -> KHONG DOC DUOC (can thiep that bai hoac duoi nguong hieu luc).")
elif bp > ss and bp > bg:
    print("  -> HANG 1: PHAN RA VAI BAT DOI XUNG CO GIA TRI. Ke hoach tu model manh nang model yeu")
    print("     vuot ca viec chay thang model manh. Ket qua LON — phai tai lap truoc khi cong bo.")
elif bp > ss:
    print("  -> HANG 2: ke hoach manh CO giup model nho, nhung BI AP DAO: chay thang 7B vua re hon")
    print("     vua tot hon. Y het hinh mau dinh tuyen o #81.")
else:
    print("  -> HANG 3: ke hoach tu model MANH HON cung khong giup noi model yeu.")
    print("     Day la dang phu dinh MANH NHAT ve lap ke hoach.")

json.dump({"n": n, "plan_is_code_rate": round(pic, 4), "runnable": round(runs, 3),
           "acc": A, "cost": COST,
           "bp_minus_small_seq": round(bp-ss, 4), "bp_minus_big_greedy": round(bp-bg, 4)},
          open(f"{RES}/H51_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H51_merged.json")
