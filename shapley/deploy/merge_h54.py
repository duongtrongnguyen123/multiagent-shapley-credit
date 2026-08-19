#!/usr/bin/env python3
"""Gop cac shard H40 va chay PHAN RA THEO TANG DO KHO (dang ky truoc #46).

Do do kho lay tu HF MATH-500 khop bang MA BAM DE BAI, khong tin cot 'level' cua CSV Kaggle.
Logic tong hop giong het strat_local.py tren 5090 -> hai ben so sanh duoc truc tiep.
"""
import sys, json, glob, re, hashlib
from pathlib import Path

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h54"
NEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20

# ---- do kho tu HF (nguon su that) ----
from datasets import load_dataset
hf = load_dataset("HuggingFaceH4/MATH-500", split="test")
def _qh(t): return hashlib.md5(" ".join(str(t).split()).encode("utf-8")).hexdigest()[:12]
LVL = {_qh(r["problem"]): int(r["level"]) for r in hf}
# Dap an chuan LAY TU HF, khong tin cot 'Answer' cua CSV Kaggle (khong ro la dap an cuoi
# hay ca loi giai). qhash la cau noi duy nhat can tin.
GOLD = {_qh(r["problem"]): r["answer"] for r in hf}
print(f"HF MATH-500: {len(LVL)} bai co do kho + dap an chuan")

# ---- gop shard ----
items, shards, quants, nsh = [], set(), set(), set()
for f in sorted(glob.glob(f"{RES}/res_H40s*.json")):
    d = json.load(open(f))
    shards.add(d["shard"]); quants.add(d.get("quant_big", "?")); nsh.add(d.get("nshard"))
    items += d["items"]
if len(nsh) > 1:
    print(f"DUNG: tron shard tu cac lan chia KHAC NHAU {sorted(nsh)} -> khong gop duoc.")
    raise SystemExit(1)
if len(quants) > 1:
    print(f"DUNG: shard chay o do chinh xac khac nhau {sorted(quants)}.")
    raise SystemExit(1)
print(f"gop {len(shards)}/{NEED} shard, {len(items)} bai, luong tu hoa: {quants}")
missing = sorted(set(range(NEED)) - shards)
if missing:
    print(f"THIEU shard: {missing} — KHONG doc ket qua cho den khi du (tranh lech tang do kho)")

nogold = 0
for it in items:
    it["lv"] = LVL.get(it["qhash"], 0)
    g = GOLD.get(it["qhash"])
    if g is not None: it["gold"] = g          # HF la nguon su that
    else: nogold += 1
if nogold: print(f"CANH BAO: {nogold} bai khong khop HF -> dung dap an cua shard")
nolv = sum(1 for it in items if it["lv"] == 0)
if nolv: print(f"CANH BAO: {nolv} bai khong khop duoc do kho")

# ---- cham diem: giong strat_local.py ----
def _nm(a):
    if a is None: return None
    a = str(a).strip()
    for z in ["\\left", "\\right", "\\!", "\\,", "$", " ", ","]: a = a.replace(z, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a).replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    return a.rstrip(".").strip("{}").lower()
def ok(x, g):
    x, g = _nm(x), _nm(g)
    if not x or not g: return False
    if x == g: return True
    try: return abs(float(x) - float(g)) < 1e-6
    except: return False
def vote(ps, k):
    c = {}
    for p in ps[:k]:
        if p is not None: c[p] = c.get(p, 0) + 1
    if not c: return None, 0
    b = max(c, key=lambda z: c[z]); return b, c[b]

RATIO = 14.7 / 1.5      # 1 luot 14B = 9.80 luot 1.5B
STRATA = [("DE", [1, 2]), ("GIUA", [3]), ("KHO", [4, 5]), ("TATCA", [1, 2, 3, 4, 5])]

def A(sub, f):
    return round(sum(ok(f(it), it["gold"]) for it in sub) / len(sub), 4) if sub else None

sm3  = lambda it: vote(it["small_pred"], 3)[0]
big3 = lambda it: vote(it["big_pred"], 3)[0]
big8 = lambda it: vote(it["big_pred"], 8)[0]
def eseq(it):
    return it["seq_pred"] if it["escalated"] else vote(it["small_pred"], 3)[0]

out = {"n": len(items), "quant_big": sorted(quants), "shards": sorted(shards), "strata": {}}
print(f"\n{'tang':7s}{'n':>5s}{'esc%':>7s}{'big3':>8s}{'esc_seq':>9s}{'gain':>8s}{'opp_cost':>10s}{'gain_esc':>10s}{'ID':>9s}")
for name, lvs in STRATA:
    sub  = [it for it in items if it["lv"] in lvs]
    if len(sub) < 40:
        out["strata"][name] = {"n": len(sub), "SKIP": "n<40"}; continue
    kept = [it for it in sub if not it["escalated"]]
    esc  = [it for it in sub if it["escalated"]]
    pk, pe = len(kept)/len(sub), len(esc)/len(sub)
    s = {"n": len(sub), "n_kept": len(kept), "n_esc": len(esc), "pct_escalated": round(pe, 4),
         "DEGENERATE": not (0.15 <= pe <= 0.85),
         "small_maj3": A(sub, sm3), "big_maj3": A(sub, big3), "big_maj8": A(sub, big8),
         "escalate_seq": A(sub, eseq),
         "cost_big_maj3": round(3*RATIO, 3), "cost_escalate_seq": round(3 + 2*RATIO*pe, 3),
         "acc_small_on_kept": A(kept, sm3), "acc_big3_on_kept": A(kept, big3),
         "acc_seq_on_esc": A(esc, eseq),    "acc_big3_on_esc": A(esc, big3)}
    if kept and esc:
        s["opp_cost"]    = round(s["acc_big3_on_kept"] - s["acc_small_on_kept"], 4)
        s["gain_on_esc"] = round(s["acc_seq_on_esc"] - s["acc_big3_on_esc"], 4)
        s["gain"]        = round(s["escalate_seq"] - s["big_maj3"], 4)
        p = pk*(-s["opp_cost"]) + pe*s["gain_on_esc"]
        s["identity_pred"] = round(p, 4)
        s["identity_err"]  = round(abs(p - s["gain"]), 4)
        s["IDENTITY_OK"]   = s["identity_err"] <= 0.01
        flag = "OK" if s["IDENTITY_OK"] else "BUG"
        if s["DEGENERATE"]: flag = "SUYBIEN"
        print(f"{name:7s}{s['n']:5d}{s['pct_escalated']:7.3f}{s['big_maj3']:8.4f}{s['escalate_seq']:9.4f}"
              f"{s['gain']:+8.4f}{s['opp_cost']:+10.4f}{s['gain_on_esc']:+10.4f}{flag:>9s}")
    out["strata"][name] = s

json.dump(out, open(f"{RES}/H54_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H40_merged.json")
if missing: print("NHAC LAI: con thieu shard — ket qua tren CHUA du de ket luan")
