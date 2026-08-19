#!/usr/bin/env python3
"""Gop H52 (dang ky truoc #58): refactor — bao toan hanh vi co can ORACLE that khong?
`simpler` CHI tinh tren cac bai `preserve` (xoa sach code cung "giam phuc tap")."""
import sys, json, glob

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h52"
items = []; quants = set()
for f in sorted(glob.glob(f"{RES}/**/res_H52s*.json", recursive=True)):
    d = json.load(open(f)); items += d["items"]; quants.add(d.get("quant", "?"))
if len(quants) > 1:
    print(f"DUNG: shard chay o CAC DO CHINH XAC KHAC NHAU {sorted(quants)} -> khong duoc gop chung.")
    raise SystemExit(1)
print(f"luong tu hoa (dong nhat): {sorted(quants)}")
n = len(items)
nf = len(glob.glob(f"{RES}/**/res_H52s*.json", recursive=True))
print(f"gop {nf} shard, {n} bai (loi giai chuan da dat test)")
if n < 250:
    print(f"n = {n} < 250 -> CHUA du de doc bang khoa #58")

parsed = sum(1 for x in items if x["ref1"]["nodes"] is not None) / max(n, 1)
print(f"ban refactor phan tich duoc AST: {parsed:.3f} ({'DAT' if parsed >= .80 else 'TRUOT'} nguong .80)")

ARMS = ("ref1", "ref_seq", "ref_exec")
print(f"\n{'nhanh':10s}{'preserve':>10s}{'simpler|pre':>13s}{'good':>8s}{'nut TB (pre)':>14s}")
R = {}
for a in ARMS:
    pres = [x for x in items if x[a]["pass"]]
    p = len(pres) / max(n, 1)
    simp = [x for x in pres if x[a]["nodes"] is not None and x["nodes_orig"] and x[a]["nodes"] < x["nodes_orig"]]
    s_giv = len(simp) / max(len(pres), 1)
    good = len(simp) / max(n, 1)
    avg = (sum(x[a]["nodes"] for x in pres if x[a]["nodes"]) / max(len([x for x in pres if x[a]["nodes"]]), 1))
    print(f"{a:10s}{p:10.4f}{s_giv:13.4f}{good:8.4f}{avg:14.1f}")
    R[a] = {"preserve": round(p, 4), "simpler_given_preserve": round(s_giv, 4), "good_refactor": round(good, 4)}
orig_avg = sum(x["nodes_orig"] for x in items if x["nodes_orig"]) / max(len([x for x in items if x["nodes_orig"]]), 1)
print(f"{'(goc)':10s}{'':10s}{'':13s}{'':8s}{orig_avg:14.1f}")

d = R["ref_exec"]["preserve"] - R["ref_seq"]["preserve"]
print(f"\n  preserve(exec) - preserve(seq) = {d:+.4f}")
print(f"  ref1 lam hong ngay tu dau: {sum(1 for x in items if x['ref1_broke'])}/{n}")

print("\n-- bang khoa #58 --")
if n < 250 or parsed < .80:
    print("  -> DUOI NGUONG HIEU LUC, khong ket luan.")
elif all(R[a]["preserve"] < .50 for a in ARMS):
    print("  -> HANG 3: MOI nhanh preserve < .50. Model khong refactor an toan duoc o quy mo nay.")
    print("     Gioi han NANG LUC, khong phai ve vai.")
elif d >= .10:
    print("  -> HANG 1: ORACLE LA THIET YEU. Xac nhan phan biet #42 o mien thu ba:")
    print("     LLM tu nhan xet KHONG phat hien duoc doi hanh vi; chay test thi phat hien.")
elif abs(d) < .05:
    print("  -> HANG 2: LLM tu nhan xet DU cho refactor -> LAM YEU phan biet #42. Ghi ro.")
else:
    print("  -> nam giua .05 va .10: huong ung ho oracle nhung chua dat nguong da khoa. Ghi ro.")
if R["ref1"]["good_refactor"] and abs(R["ref_seq"]["good_refactor"] - R["ref1"]["good_refactor"]) < .02:
    print("  -> ref1 ~ ref_seq o good_refactor: luot them KHONG mang lai gi khi thieu oracle (khop #90/#91).")

json.dump({"n": n, "parsed": round(parsed, 3), "arms": R,
           "exec_minus_seq_preserve": round(d, 4)},
          open(f"{RES}/H52_merged.json", "w"), indent=2)
print(f"\nda ghi {RES}/H52_merged.json")
