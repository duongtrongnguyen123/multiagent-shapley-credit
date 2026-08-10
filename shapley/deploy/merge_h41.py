#!/usr/bin/env python3
"""Gop cac shard H41 (GSM8K) — PHAN RA THEO TANG DO KHO (dang ky truoc #47 + bo sung 2026-08-10).

Do do kho lay tu HF MATH-500 khop bang MA BAM DE BAI, khong tin cot 'level' cua CSV Kaggle.
Logic tong hop giong het strat_local.py tren 5090 -> hai ben so sanh duoc truc tiep.
"""
import sys, json, glob, re, hashlib
from pathlib import Path

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h41"
NEED = int(sys.argv[2]) if len(sys.argv) > 2 else 20

# ---- do kho tu HF (nguon su that) ----
from datasets import load_dataset
hf = load_dataset("openai/gsm8k", "main", split="test")
def _qh(t): return hashlib.md5(" ".join(str(t).split()).encode("utf-8")).hexdigest()[:12]
def _bucket(a):
    s = a.count("<<")
    return 1 if s <= 2 else (3 if s == 3 else 5)   # 1=DE(<=2 buoc) 3=GIUA(3) 5=KHO(>=4)
LVL = {_qh(r["question"]): _bucket(r["answer"]) for r in hf}
# Dap an chuan LAY TU HF, khong tin cot 'Answer' cua CSV Kaggle (khong ro la dap an cuoi
# hay ca loi giai). qhash la cau noi duy nhat can tin.
GOLD = {_qh(r["question"]): r["answer"].split("####")[-1].replace(",", "").strip() for r in hf}
print(f"HF GSM8K: {len(LVL)} bai, do kho = so buoc tinh <<>>")

# ---- gop shard ----
items, shards, quants = [], set(), set()
for f in sorted(glob.glob(f"{RES}/res_H41s*.json")):
    d = json.load(open(f))
    shards.add(d["shard"]); quants.add(d.get("quant_big", "?"))
    items += d["items"]
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
def ok(x, g):
    if x is None or g is None: return False
    try: return abs(float(str(x).replace(",", "")) - float(str(g).replace(",", ""))) < 1e-4
    except: return str(x).strip() == str(g).strip()
def vote(ps, k):
    c = {}
    for p in ps[:k]:
        if p is not None: c[p] = c.get(p, 0) + 1
    if not c: return None, 0
    b = max(c, key=lambda z: c[z]); return b, c[b]

RATIO = 7.6 / 1.5
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

de = out["strata"].get("DE", {})
if de.get("big_maj3") is not None and de["big_maj3"] < .90:
    print(f"\n!! BO SUNG #47: big_maj3(DE) = {de['big_maj3']:.4f} < .90 -> CHUA CHAM VUNG BAO HOA.")
    print("   Ket luan bat buoc: cau hoi bao hoa VAN CHUA duoc tra loi (y nhu H40). Khong doc theo huong ung ho/bac bo.")
json.dump(out, open(f"{RES}/H41_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H40_merged.json")
if missing: print("NHAC LAI: con thieu shard — ket qua tren CHUA du de ket luan")
