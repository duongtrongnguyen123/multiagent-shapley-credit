#!/usr/bin/env python3
"""Gop H58 (dang ky truoc #62): dung test tu sinh de CHON trong 8 mau.
Bao ca TI LE KHOANG TRONG THU DUOC = (select - maj8) / (oracle8 - maj8)."""
import sys, json, glob

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h58"
NEED = int(sys.argv[2]) if len(sys.argv) > 2 else 12
items, quants, nsh, nfile = [], set(), set(), 0
for f in sorted(glob.glob(f"{RES}/**/res_H*s*.json", recursive=True)):
    try: d = json.load(open(f))
    except Exception: continue
    if not str(d.get("tag","")).startswith("H58"): continue
    nfile += 1; items += d["items"]; quants.add(d.get("quant")); nsh.add(d.get("nshard"))
if len(quants) > 1 or len(nsh) > 1:
    print(f"DUNG: tron shard khac nhau (quant={sorted(quants)}, nshard={sorted(nsh)})"); raise SystemExit(1)
n = len(items)
print(f"gop {nfile}/{NEED} shard, {n} bai, quant={sorted(quants)}")
if nfile < NEED: print(f"THIEU shard -> CHUA du de doc bang khoa #62")

wt = [x for x in items if x["n_gen_tests"] > 0]
sound = sum(x["sound_all"] for x in wt) / max(len(wt), 1)
avg_t = sum(x["n_gen_tests"] for x in items) / max(n, 1)
print(f"\nso assert TB: {avg_t:.2f} | test_soundness: {sound:.4f} "
      f"({'DAT' if sound >= .50 else 'TRUOT'} nguong .50)")

def vb(pr, k):
    c = {}
    for i, d in enumerate(pr[:k]):
        o = d.get("out")
        if isinstance(o, str) and o.startswith("ERR:"): continue
        c.setdefault(o, []).append(i)
    return pr[max(c.values(), key=len)[0]]["held"] if c else False
def sel(x):
    """chon mau dat NHIEU test tu sinh nhat; hoa -> bo phieu hanh vi trong nhom hoa"""
    sc = x.get("test_score") or []
    if not sc or max(sc) == 0: return vb(x["samp"], 8)
    best = max(sc); tied = [i for i, v in enumerate(sc) if v == best]
    if len(tied) == 1: return x["samp"][tied[0]]["held"]
    sub = [x["samp"][i] for i in tied]
    return vb(sub, len(sub))

maj3 = round(sum(vb(x["samp"], 3) for x in items) / n, 4)
maj8 = round(sum(vb(x["samp"], 8) for x in items) / n, 4)
orc8 = round(sum(any(s["held"] for s in x["samp"]) for x in items) / n, 4)
selt = round(sum(sel(x) for x in items) / n, 4)
gap = orc8 - maj8
cap = (selt - maj8) / gap if gap > 0 else 0.0
print(f"\n{'nhanh':14s}{'acc':>9s}")
for k, v in (("maj3", maj3), ("maj8", maj8), ("select_tests", selt), ("oracle8 (tran)", orc8)):
    print(f"{k:14s}{v:9.4f}")
print(f"\n  select_tests - maj8 = {selt-maj8:+.4f}")
print(f"  khoang trong       = {gap:+.4f}   -> thu duoc {cap:.1%}")

print("\n-- bang khoa #62 --")
if sound < .50 or nfile < NEED:
    print("  -> KHONG DOC DUOC (soundness thap hoac thieu shard).")
elif selt - maj8 >= .02:
    print(f"  -> HANG 1: CHON BANG ORACLE TU SINH CO TAC DUNG (+{selt-maj8:.4f}).")
    print(f"     Thu duoc {cap:.1%} khoang trong. Phai TAI LAP tren 511-974 truoc khi cong bo.")
    if cap < .25: print("  -> nhung THU DUOC < 25%: phan lon 7.8 diem VAN bo khong.")
elif abs(selt - maj8) < .02:
    print("  -> HANG 2: khong hon bo phieu. Cung voi #94 -> oracle tu sinh vo dung cho CA sua lan chon.")
else:
    print("  -> HANG 3: test tu sinh LAM HONG viec chon.")

json.dump({"n": n, "avg_tests": round(avg_t,2), "test_soundness": round(sound,4),
           "maj3": maj3, "maj8": maj8, "select_tests": selt, "oracle8": orc8,
           "select_minus_maj8": round(selt-maj8,4), "gap": round(gap,4),
           "gap_captured": round(cap,4)}, open(f"{RES}/H58_merged.json","w"), indent=2)
print(f"\nda ghi {RES}/H58_merged.json")
