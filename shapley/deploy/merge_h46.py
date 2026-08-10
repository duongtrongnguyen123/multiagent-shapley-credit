#!/usr/bin/env python3
"""Gop H46 (dang ky truoc #52): tach rieng tac dung cua MO NEO tren luoi tac vu x co model.
`greedy` cua moi o CHINH LA thuoc do bao hoa cua o do. In thang ra hang nao cua #51 khop."""
import sys, json, glob, re
from collections import defaultdict

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h46"

cells = defaultdict(list)
quant = defaultdict(set)
for f in sorted(glob.glob(f"{RES}/res_H46s*.json")):
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

print(f"{'o':12s}{'n':>5s}{'greedy':>9s}{'maj3':>8s}{'A_neo':>8s}{'B_khong':>9s}{'A-B':>9s}{'A-maj3':>9s}{'B-maj3':>9s}")
rows = []
for key in sorted(cells):
    its = cells[key]
    ok = ok_gsm if key.startswith("gsm8k") else ok_math
    n = len(its)
    parsed = sum(1 for x in its if x["greedy_pred"] is not None) / max(n, 1)
    g  = round(sum(ok(x["greedy_pred"], x["gold"]) for x in its) / n, 4)
    m3 = round(sum(ok(vote(x["samp_pred"]), x["gold"]) for x in its) / n, 4)
    A  = round(sum(ok(x["seq_pred"], x["gold"]) for x in its) / n, 4)
    B  = round(sum(ok(x.get("seq_noanchor_pred"), x["gold"]) for x in its) / n, 4)
    flag = "" if parsed >= .80 else "  SUYBIEN"
    print(f"{key:12s}{n:5d}{g:9.4f}{m3:8.4f}{A:8.4f}{B:9.4f}{A-B:+9.4f}{A-m3:+9.4f}{B-m3:+9.4f}{flag}")
    rows.append({"cell": key, "n": n, "parsed": round(parsed, 3), "greedy": g, "maj3": m3,
                 "A_anchor": A, "B_noanchor": B, "A_minus_B": round(A-B, 4),
                 "A_minus_maj3": round(A-m3, 4), "B_minus_maj3": round(B-m3, 4),
                 "valid": parsed >= .80})

good = [r for r in rows if r["valid"]]
if len(good) < 4:
    print(f"\nCHI CO {len(good)}/4 o hop le -> chua du de doc bang khoa #52")
else:
    math_cells = [r for r in good if r["cell"].startswith("math")]
    gsm_cells  = [r for r in good if r["cell"].startswith("gsm8k")]
    print("\n-- bang khoa #52 (H44 tren code da do A-B = -.0981) --")
    for r in good:
        print(f"  {r['cell']:12s} A-B = {r['A_minus_B']:+.4f}   (greedy={r['greedy']:.3f})")
    mb = [r["A_minus_B"] for r in math_cells + gsm_cells]
    if mb and all(abs(x) < .02 for x in mb):
        print("  -> HANG 2: MO NEO KHONG LAM GI tren toan. Phat bieu 'co che la mo neo' (vong #73) SAI.")
        print("     SS_anc ngang PSV vi ly do KHAC. PHAI RUT LAI.")
    elif mb and all(x < 0 for x in mb):
        print("  -> HANG 3: MO NEO HAI O MOI MIEN. Moi thang loi cua tuan tu den tu LUOT THEM,")
        print("     khong tu mo neo. PHAI RUT LAI vong #73.")
    elif mb and all(x > 0 for x in mb):
        print("  -> HANG 1: mo neo GIUP tren toan, HAI tren code -> co che CO DIEU KIEN theo mien.")
        print("     Phai viet lai phat bieu vong #73 kem dieu kien mien.")
    else:
        print("  -> HON HOP: dau cua A-B khong dong nhat giua cac o. Doc tung o mot, khong khai quat.")
    for r in good:
        if r["B_minus_maj3"] > 0 and r["A_minus_maj3"] < 0:
            print(f"  -> HANG 4 khop o {r['cell']}: B hon maj3 nhung A thua -> ban co mo neo tu lam hong minh.")

json.dump(rows, open(f"{RES}/H46_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H45_merged.json")
