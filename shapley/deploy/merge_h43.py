#!/usr/bin/env python3
"""Gop cac shard H43 (MBPP 511-974, phan CHUA TUNG DUNG) — dang ky truoc #49.

Cham diem CHI bang assert[1..2] (truong 'held'). assert[0] chi dung de dinh tuyen.
Chi phi quy ve FLOP 1.5B: 1 luot 7B = 5.07.
"""
import sys, json, glob, statistics as st

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h43"
NEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20
RATIO, KS, K = 7.6/1.5, 3, 8

items, shards, quants = [], set(), set()
for f in sorted(glob.glob(f"{RES}/res_H43s*.json")):
    d = json.load(open(f))
    shards.add(d["shard"]); quants.add(d.get("quant_big", "?"))
    items += d["items"]
print(f"gop {len(shards)}/{NEED} shard, {len(items)} bai, luong tu hoa 7B: {sorted(quants)}")
missing = sorted(set(range(NEED)) - shards)
if missing:
    print(f"THIEU shard: {missing} — KHONG doc ket qua cho den khi du")

# ---- ngưỡng hiệu lực: tỉ lệ biên dịch được ----
allp = [p for it in items for p in it["small"] + it["big"]]
comp = sum(1 for p in allp if p.get("compiles")) / max(len(allp), 1)
print(f"ti le bien dich duoc: {comp:.3f}  ({'DAT' if comp >= .50 else 'KHONG DAT -> HUY'} nguong .50)")

def vote_behavior(probes, k):
    """bo phieu theo HANH VI: nhom theo dau ra tren loi goi assert[0]; bo cac ban loi."""
    c = {}
    for idx, d in enumerate(probes[:k]):
        o = d.get("out")
        if isinstance(o, str) and o.startswith("ERR:"): continue
        c.setdefault(o, []).append(idx)
    if not c: return 0
    best = max(c.values(), key=len)
    return probes[best[0]]["held"]

def acc(f):  return round(sum(bool(f(it)) for it in items) / len(items), 4)

# ---- cac nhanh ----
small_maj3 = acc(lambda it: vote_behavior(it["small"], KS))
big_maj3   = acc(lambda it: vote_behavior(it["big"], 3))
big_maj8   = acc(lambda it: vote_behavior(it["big"], K))
big_greedy = acc(lambda it: it["big"][0]["held"])
small_1    = acc(lambda it: it["small"][0]["held"])

def routed(it, esc_key, keep):
    if it[esc_key]:
        return it["seq"]["held"] if it.get("seq") else False
    return keep(it)
route_cons = acc(lambda it: routed(it, "esc_consensus", lambda x: vote_behavior(x["small"], KS)))
route_orac = acc(lambda it: routed(it, "esc_oracle",    lambda x: x["small"][0]["held"]))
# NHANH CAN KIEM (#49): tin hieu oracle, nhung escalate bang LAY MAU 7B maj@3
route_orac_maj3 = acc(lambda it: vote_behavior(it["big"], 3) if it["esc_oracle"] else it["small"][0]["held"])

pe_c = round(sum(1 for it in items if it["esc_consensus"]) / len(items), 4)
pe_o = round(sum(1 for it in items if it["esc_oracle"]) / len(items), 4)
cost_c = round(KS + 2*RATIO*pe_c, 2)
cost_o = round(1 + 2*RATIO*pe_o, 2)

print(f"\n{'nhanh':22s}{'acc(held)':>11s}{'chi phi':>10s}{'esc%':>8s}")
for nm, a, c, p in [("small_1 (1 ban 1.5B)", small_1, 1.0, None),
                    ("small_maj3", small_maj3, float(KS), None),
                    ("big_greedy", big_greedy, RATIO, None),
                    ("big_maj3", big_maj3, 3*RATIO, None),
                    ("big_maj8", big_maj8, K*RATIO, None),
                    ("route_consensus", route_cons, cost_c, pe_c),
                    ("route_oracle_seq", route_orac, cost_o, pe_o),
                    ("route_oracle_maj3 *", route_orac_maj3, round(1+3*RATIO*pe_o,2), pe_o)]:
    print(f"{nm:22s}{a:11.4f}{c:10.2f}" + (f"{p:8.3f}" if p is not None else f"{'-':>8s}"))

cost_om = round(1+3*RATIO*pe_o, 2)
print(f"\n-- doi chieu voi bang khoa #49 (* = nhanh can kiem) --")
print(f"  route_oracle_maj3 - big_maj3   = {route_orac_maj3-big_maj3:+.4f}   (re hon {3*RATIO/cost_om:.2f}x)")
print(f"  route_oracle_seq  - big_maj3   = {route_orac-big_maj3:+.4f}")
print(f"  maj3 vs tuan tu khi escalate   = {route_orac_maj3-route_orac:+.4f}")
# HANG 2 xet TRUOC: hai hang chong nhau trong bang khoa #48/#49, va cach doc
# BAO THU (|chenh| < .01 = ngang nhau) moi la cach doc trung thuc.
if abs(route_orac_maj3-big_maj3) < .01: print("  -> HANG 2: NGANG do chinh xac, chi RE HON (chenh trong nguong nhieu .01)")
elif route_orac_maj3 > big_maj3: print("  -> HANG 1: XAC NHAN (dinh tuyen that + escalate bang LAY MAU)")
else: print("  -> HANG 3: KHONG TAI LAP -> dinh tuyen tren code CHET hoan toan")
for nm, p in (("consensus", pe_c), ("oracle", pe_o)):
    if not (0.15 <= p <= 0.85): print(f"  !! pct_escalated({nm}) = {p} NGOAI .15-.85 -> SUY BIEN, khong doc nhanh nay")

out = {"n": len(items), "shards": sorted(shards), "quant_big": sorted(quants), "compile_rate": round(comp, 4),
       "small_1": small_1, "small_maj3": small_maj3, "big_greedy": big_greedy,
       "big_maj3": big_maj3, "big_maj8": big_maj8,
       "route_consensus": route_cons, "route_oracle_seq": route_orac, "route_oracle_maj3": route_orac_maj3,
       "pct_esc_consensus": pe_c, "pct_esc_oracle": pe_o,
       "cost_consensus": cost_c, "cost_oracle": cost_o, "cost_big_maj3": round(3*RATIO, 2)}
json.dump(out, open(f"{RES}/H43_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H42_merged.json")
if missing: print("NHAC LAI: con thieu shard — CHUA du de ket luan")
