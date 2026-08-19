#!/usr/bin/env python3
"""Gop H55 (dang ky truoc #61): verifier tu viet test.
Cong TU AP DUNG: test_soundness < .50 -> KHONG doc duoc cho cau hoi TDD."""
import sys, json, glob

RES = sys.argv[1] if len(sys.argv) > 1 else "res_h55"
NEED = int(sys.argv[2]) if len(sys.argv) > 2 else 12
items, quants, nsh = [], set(), set()
# ten file co the sai do ke thua tu kernel to tien -> XAC THUC BANG NOI DUNG (`tag`)
nfile = 0
for f in sorted(glob.glob(f"{RES}/**/res_H*s*.json", recursive=True)):
    try: d = json.load(open(f))
    except Exception: continue
    if not str(d.get("tag","")).startswith("H55"): continue
    nfile += 1
    items += d["items"]; quants.add(d.get("quant")); nsh.add(d.get("nshard"))
if len(quants) > 1 or len(nsh) > 1:
    print(f"DUNG: tron shard khac nhau (quant={sorted(quants)}, nshard={sorted(nsh)})"); raise SystemExit(1)
n = len(items)
print(f"gop {nfile}/{NEED} shard, {n} bai, quant={sorted(quants)}")

with_tests = [x for x in items if x["n_gen_tests"] > 0]
gen_rate = len(with_tests) / max(n, 1)
sound = sum(x["sound_all"] for x in with_tests) / max(len(with_tests), 1)
avg_n = sum(x["n_gen_tests"] for x in items) / max(n, 1)
print(f"\nsinh duoc test: {gen_rate:.3f} | so assert TB: {avg_n:.2f}")
print(f"test_soundness (loi giai chuan DAT het test tu sinh): {sound:.4f}  "
      f"({'DAT' if sound >= .50 else 'TRUOT'} nguong .50)")

# test_power: trong so bai ma ban cai dat DAU TIEN sai (truot assert[1..2] that),
# bao nhieu bai bi test TU SINH bat duoc?
wrong = [x for x in with_tests if not x["tdd_impl"]["held"]]
caught = [x for x in wrong if not x["gen_pass_impl"]]
power = len(caught) / max(len(wrong), 1)
print(f"test_power (bat duoc ban cai dat SAI): {power:.4f}  ({len(caught)}/{len(wrong)})")

def acc(k): return round(sum(x[k]["held"] for x in items) / n, 4)
def vb(x):
    c = {}
    for i, d in enumerate(x["samp"]):
        o = d.get("out")
        if isinstance(o, str) and o.startswith("ERR:"): continue
        c.setdefault(o, []).append(i)
    return x["samp"][max(c.values(), key=len)[0]]["held"] if c else False
maj3 = round(sum(vb(x) for x in items) / n, 4)
A = {"solve1": acc("solve1"), "maj3": maj3, "tdd_impl": acc("tdd_impl"),
     "tdd": acc("tdd"), "tdd_noexec": acc("tdd_noexec")}
print(f"\n{'nhanh':14s}{'acc (assert giu lai)':>22s}")
for k in ("solve1", "maj3", "tdd_impl", "tdd_noexec", "tdd"):
    print(f"{k:14s}{A[k]:22.4f}")
d_maj = A["tdd"] - A["maj3"]; d_ne = A["tdd"] - A["tdd_noexec"]
print(f"\n  tdd - maj3       = {d_maj:+.4f}")
print(f"  tdd - tdd_noexec = {d_ne:+.4f}   <- tach 'CHAY test' khoi 'prompt giau hon'")

print("\n-- bang khoa #61 --")
if sound < .50:
    print("  -> SUY BIEN: test tu sinh sai nhieu hon dung. Vai verifier THAT BAI o khau tao oracle.")
    print("     KHONG ket luan 'phan ra vai vo dung'.")
elif d_maj >= .02 and sound >= .70:
    print("  -> HANG 1: PHAN RA VAI CO GIA TRI khi cac vai sinh ARTIFACT KHAC NHAU.")
    print("     Phai tai lap tren tach 511-974 truoc khi cong bo.")
elif abs(d_maj) < .02:
    print("  -> HANG 2: oracle tu sinh KHONG them gi so voi lay mau.")
else:
    print("  -> HANG 3: test tu sinh DANH LAC HUONG solver (dac ta sai).")
if abs(d_ne) < .02:
    print("  -> HANG 4 khop: loi ich (neu co) den tu PROMPT GIAU HON, khong phai tu CHAY test.")
if sound >= .70 and power < .20:
    print("  -> HANG 5 khop: test DUNG nhung RONG (khong bat duoc loi nao).")

json.dump({"n": n, "gen_rate": round(gen_rate,4), "avg_tests": round(avg_n,2),
           "test_soundness": round(sound,4), "test_power": round(power,4), "acc": A,
           "tdd_minus_maj3": round(d_maj,4), "tdd_minus_noexec": round(d_ne,4)},
          open(f"{RES}/H55_merged.json","w"), indent=2)
print(f"\nda ghi {RES}/H55_merged.json")
