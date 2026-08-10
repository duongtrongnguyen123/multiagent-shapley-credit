#!/usr/bin/env python3
"""Gop H45 (dang ky truoc #51): delta_seq = seq - maj3 tren luoi tac vu x co model.
`greedy` cua moi o CHINH LA thuoc do bao hoa cua o do. In thang ra hang nao cua #51 khop."""
import sys, json, glob, re
from collections import defaultdict

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h45"

cells = defaultdict(list)
quant = defaultdict(set)
for f in sorted(glob.glob(f"{RES}/res_H45s*.json")):
    d = json.load(open(f))
    key = f"{d['task']}-{d['size']}"
    cells[key] += d["items"]; quant[key].add(d.get("quant", "?"))

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def _nm(a):
    if a is None: return None
    a = str(a).strip()
    for z in ["\\left", "\\right", "\\!", "\\,", "$", " ", ","]: a = a.replace(z, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a).replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()
def ok_math(x, g):
    x, g = _nm(x), _nm(g)
    if not x or not g: return False
    if x == g: return True
    try: return abs(float(x) - float(g)) < 1e-6
    except Exception: return False
def ok_gsm(x, g):
    if x is None or g is None: return False
    try: return abs(float(str(x).replace(",", "")) - float(str(g).replace(",", ""))) < 1e-4
    except Exception: return str(x).strip() == str(g).strip()

def vote(ps):
    c = {}
    for p in ps:
        if p is not None: c[p] = c.get(p, 0) + 1
    return max(c, key=lambda z: c[z]) if c else None

print(f"{'o':12s}{'n':>5s}{'phan tich':>11s}{'greedy':>9s}{'maj3':>8s}{'seq':>8s}{'delta_seq':>11s}{'quant':>16s}")
rows = []
for key in sorted(cells):
    its = cells[key]
    ok = ok_gsm if key.startswith("gsm8k") else ok_math
    n = len(its)
    parsed = sum(1 for x in its if x["greedy_pred"] is not None) / max(n, 1)
    g  = round(sum(ok(x["greedy_pred"], x["gold"]) for x in its) / n, 4)
    m3 = round(sum(ok(vote(x["samp_pred"]), x["gold"]) for x in its) / n, 4)
    sq = round(sum(ok(x["seq_pred"], x["gold"]) for x in its) / n, 4)
    d  = round(sq - m3, 4)
    flag = "" if parsed >= .80 else "  SUYBIEN(parse<.80)"
    print(f"{key:12s}{n:5d}{parsed:11.3f}{g:9.4f}{m3:8.4f}{sq:8.4f}{d:+11.4f}{str(sorted(quant[key])):>16s}{flag}")
    rows.append({"cell": key, "n": n, "parsed": round(parsed, 3), "greedy": g,
                 "maj3": m3, "seq": sq, "delta_seq": d, "valid": parsed >= .80})

good = [r for r in rows if r["valid"]]
if len(good) < 4:
    print(f"\nCHI CO {len(good)}/4 o hop le -> chua du de doc bang khoa #51")
else:
    lo = [r for r in good if r["greedy"] < .60]
    hi = [r for r in good if r["greedy"] > .85]
    print("\n-- bang khoa #51 --")
    print(f"  o CHUA bao hoa (greedy<.60): {[(r['cell'], r['delta_seq']) for r in lo]}")
    print(f"  o DA  bao hoa (greedy>.85): {[(r['cell'], r['delta_seq']) for r in hi]}")
    allneg = all(r["delta_seq"] < 0 for r in good)
    allpos = all(r["delta_seq"] > 0 for r in good)
    if allneg:
        print("  -> HANG 3: delta_seq AM O CA BON O. Moi ket qua duong truoc day den tu ESCALATE,")
        print("     khong tu tuan tu. PHAI xem lai toan bo phat bieu 'tuan tu hon lay mau'.")
    elif allpos:
        print("  -> HANG 4: delta_seq DUONG o ca bon o -> cai hai o H41/H42 la do ESCALATE, khong do tuan tu.")
    elif lo and hi and all(r["delta_seq"] > 0 for r in lo) and all(r["delta_seq"] < 0 for r in hi):
        print("  -> HANG 1: XAC NHAN - dau di theo DO BAO HOA CUA MODEL.")
    else:
        print("  -> HANG 2: dau KHONG theo greedy -> bao hoa cung KHONG giai thich duoc.")
        print("     Khac biet nam o TAC VU. Ghi ro: CHUA GIAI THICH DUOC.")

json.dump(rows, open(f"{RES}/H45_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H45_merged.json")
