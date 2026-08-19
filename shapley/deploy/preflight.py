#!/usr/bin/env python3
"""KIEM TRUOC KHI PHONG: doi chieu kernel voi DANG KY TRUOC cua chinh no.

Vi sao ton tai (#192): trong 6 lan chay GPU gan nhat co 4 lan HONG (67%, so voi 17% ca doi du an).
Bon nguyen nhan:
  H95b  cong do phu bat kha thi voi model yeu   -> khong kiem KHA THI truoc
  H98   cong chep tu H96, bao ca nhanh khong so -> LECH dac ta/hien thuc
  H94c  kernel hien thuc 3/5 cong cua #104      -> LECH dac ta/hien thuc
  H100  OOM vi Llama fp16 16GB > T4 14.6GB      -> khong TINH ngan sach VRAM

`astcheck.py` bat loi cu phap. Kiem phu bang khoa bat loi logic. **Ca hai deu khong bat duoc
bon loi tren.** Cong cu nay bat dung bon loai do, va CHI bon loai do.

Dung:
    python deploy/preflight.py pipeline/x_kernel.py 104 --machine NvidiaTeslaT4 --copies 2

Tra ve ma loi != 0 neu co canh bao PHAI xem. Khong tu dong "duyet" — no BUOC phai nhin.
"""
import ast, re, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs" / "PREREGISTRATION.md"

VRAM = {"NvidiaTeslaT4": 14.6, "NvidiaRtxPro6000": 95.0, "NvidiaTeslaP100": 16.0}
# ty tham so uoc luong tu ten thu muc/needle
SIZE_HINTS = [("32b", 32), ("14b", 14), ("8b", 8), ("7b", 7), ("6-7b", 6.7), ("6.7b", 6.7),
              ("3b", 3), ("1-5b", 1.5), ("1_5b", 1.5), ("1.5b", 1.5), ("0-5b", 0.5)]
# #193: DUNG SO DO DUOC, dung doan theo ho.
# H100b in ra truc tiep: DeepSeek-Coder-6.7B nap het **3.61 GB** => CO luong tu hoa nf4.
# Nen phat bieu "khong-Qwen khong luong tu hoa" (#135) la QUA RONG — no dung cho Llama, sai cho
# DeepSeek. Bang duoi chi chua so DA DO; thieu thi moi quay ve doan theo ho, va NOI RO la doan.
DO_DUOC_GB = {          # GB thuc te tren T4, do bang torch.cuda.memory_allocated
    "dscoder": 3.61,    # H100b @220s  — CO luong tu hoa
    "qwen7b":  5.21,    # H100c @3819s — CO luong tu hoa
}
# #195: KHONG luong tu hoa (do gian tiep qua OOM khi nap tren the trong 14.56 GB).
# qwen14b nam o day du la ho Qwen — **quy tac theo ho lai sai them mot lan nua**.
KHONG_LUONG_TU_HOA = ("llama", "14b")
# Chia duoc tren 2 the T4 (da chay that): llama8b (H100c, acc .5050 tinh xong).
# KHONG chia duoc: qwen14b — 28 GB fp16 > 29.1 GB tong tru kich hoat (H100c).
CHIA_DUOC = ("llama",)
QUANTIZABLE = ("qwen",)

def gates_in_kernel(src):
    """lay cac khoa cua `gates = {...}` / `run_gates = {...}` bang AST (khong regex mo)"""
    tree = ast.parse(src)
    out = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign): continue
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in ("gates", "run_gates", "pair_gates"):
                if isinstance(node.value, ast.Dict):
                    ks = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
                    out.setdefault(t.id, []).extend(ks)
    return out

def prereg_gates(pid):
    if not PREREG.exists(): return None, "khong tim thay PREREGISTRATION.md"
    txt = PREREG.read_text(encoding="utf-8")
    m = re.search(rf"^## #{re.escape(pid)}\b.*?$(.*?)(?=^## #|\Z)", txt, re.M | re.S)
    if not m: return None, f"khong tim thay muc #{pid}"
    body = m.group(1)
    g = re.search(r"^###\s*C[ỔO]NG.*?$(.*?)(?=^###|\Z)", body, re.M | re.S)
    if not g: return None, f"muc #{pid} khong co phan CONG"
    block = g.group(1)
    items = re.findall(r"^\s*(?:\d+\.|[-*])\s+(.{6,140})", block, re.M)
    return [re.sub(r"\s+", " ", i).strip() for i in items], None

def models_in_kernel(src):
    """Tra ve [(tag, [needle,...])] tu SPEC — CHAP NHAN CA dict LAN list-of-tuple.

    #192: ban dau toi flatten moi chuoi ra roi doan ho theo tung needle. Sai hai lan:
      (a) regex bo sot han dang `SPEC = {...}` (dict) — cong cu KHONG bat duoc chinh loi H100;
      (b) needle "2-5-7b" khong chua "qwen" nen bi doan nham la fp16, con "14b" bi dem hai lan.
    Ho phai quyet dinh tu **tag + TAT CA needle cua no**, khong phai tung chuoi roi rac.
    """
    tree = ast.parse(src)
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in ("SPEC", "M", "MODELS") for t in node.targets)):
            continue
        v = node.value
        pairs = []
        if isinstance(v, ast.Dict):                      # SPEC = {"tag": ("n1","n2"), ...}
            pairs = list(zip(v.keys, v.values))
        elif isinstance(v, (ast.List, ast.Tuple)):       # SPEC = [("tag", ("n1",..), "fam"), ...]
            for el in v.elts:
                if isinstance(el, (ast.Tuple, ast.List)) and len(el.elts) >= 2:
                    pairs.append((el.elts[0], el.elts[1]))
        for kn, vn in pairs:
            tag = kn.value if isinstance(kn, ast.Constant) else "?"
            nds = [x.value for x in ast.walk(vn)
                   if isinstance(x, ast.Constant) and isinstance(x.value, str)]
            if isinstance(tag, str) and nds: out.append((tag, nds))
    return out

def est_gb(tag, needles, big_card=False):
    """Uoc luong GB. Ho quyet dinh tu tag VA moi needle (#192).

    Tren the lon (>=40 GB) moi kernel cua du an di nhanh BIG_CARD -> bf16, KHONG luong tu hoa.
    """
    hay = " ".join([tag] + list(needles)).lower()
    if not big_card:
        for k, gb in DO_DUOC_GB.items():
            if k in hay: return gb, "DO DUOC"
    b = next((v for k, v in SIZE_HINTS if k in hay), None)
    if b is None: return None, None
    if big_card: return b * 2.0, "bf16"
    if any(q in hay for q in KHONG_LUONG_TU_HOA): return b * 2.0, "fp16 (khong luong tu hoa)"
    if any(q in hay for q in QUANTIZABLE): return b * 0.6, "nf4 (doan)"
    return b * 2.0, "fp16? (doan THAN TRONG — chua do)"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kernel"); ap.add_argument("prereg_id")
    ap.add_argument("--machine", default="NvidiaTeslaT4")
    ap.add_argument("--copies", type=int, default=1)
    a = ap.parse_args()

    src = Path(a.kernel).read_text(encoding="utf-8")
    warn = []

    print(f"=== PREFLIGHT {a.kernel}  vs dang ky truoc #{a.prereg_id} ===\n")

    # (1) placeholder con sot
    left = re.findall(r"@@[A-Z_]+@@", src)
    print(f"[1] placeholder trong NGUON: {sorted(set(left)) or 'khong con'}")
    print("    (nho kiem lai trong ban DA DAY kernels_*/kernel.py — #121)")

    # (2) doi chieu CONG
    kg = gates_in_kernel(src)
    pg, err = prereg_gates(a.prereg_id)
    print(f"\n[2] CONG trong kernel:")
    for k, v in kg.items():
        for x in v: print(f"      {k}: {x}")
    if err:
        print(f"    dang ky truoc: {err}"); warn.append("khong doc duoc CONG cua dang ky truoc")
    elif pg is not None:
        print(f"    CONG trong dang ky truoc (#{a.prereg_id}), {len(pg)} muc:")
        for x in pg: print(f"      - {x[:110]}")
        nk = sum(len(v) for v in kg.values())
        if not kg:
            warn.append("kernel KHONG co dict `gates`/`run_gates` nao")
        # #192: dem cong KHONG duoc lam canh bao cung — dinh dang gach dau dong cua dang ky
        # truoc khong anh xa 1-1 sang khoa dict, nen no bao dong ca voi H97 (lan chay TOT).
        # Canh bao lien tuc = bi phot lo. Chi in de BUOC doi chieu bang mat.
        print(f"\n    -> {nk} cong trong kernel vs {len(pg)} muc trong dang ky truoc."
              f"  **DOI CHIEU TUNG DONG BANG MAT** — day KHONG phai phep kiem tu dong")
        print(f"       (#190: H94c hien thuc 3/5 cong cua #104. Chi mat nguoi moi bat duoc.)")

    # (3) ngan sach VRAM
    cap = VRAM.get(a.machine)
    print(f"\n[3] NGAN SACH VRAM — {a.machine} = {cap} GB/the, du dinh {a.copies} ban sao/the")
    mods = models_in_kernel(src)
    if not mods:
        warn.append("KHONG tim thay SPEC/M nao -> khong kiem duoc ngan sach VRAM")
    for tag, nds in mods:
        gb, q = est_gb(tag, nds, big_card=(cap or 0) >= 40)
        if gb is None:
            print(f"      {tag:12s} ? khong doan duoc so tham so tu {nds}"); continue
        tot = gb * a.copies
        bad = cap is not None and tot > cap * 0.85
        print(f"      {tag:12s} ~{gb:5.1f} GB [{q}]"
              f"  x{a.copies} ban sao = {tot:5.1f} GB" + ("   <-- KHONG LOT" if bad else ""))
        if bad:
            if any(k in (tag+" "+" ".join(nds)).lower() for k in CHIA_DUOC):
                print(f"        ^ da biet: CHIA duoc tren {len(VRAM)>0 and 2 or 2} the (H100c chay that). "
                      f"Kernel phai co duong `load_shard` + bat OOM lan nap DAU.")
            else:
                warn.append(f"{tag}: {tot:.1f} GB vuot 85% cua {cap} GB/the va CHUA biet chia duoc "
                            f"(qwen14b da that bai ca khi chia — #195)")

    # (4) kha thi cua tin hieu (chi nhac — khong tu dong duoc)
    print(f"\n[4] KHA THI (khong tu dong kiem duoc — TRA LOI TRUOC KHI PHONG):")
    print("      - Model yeu co sinh noi tin hieu ma cong doi khong? (#184: 1.5B viet test chay duoc 70%)")
    print("      - Da co lan chay nao cho biet nguong cong nay dat duoc chua?")
    print("      - MODEL CO HOP MIEN khong? (#198: DeepSeek-*Coder* tren MATH -> acc .012, boxed .098.")
    print("        Doan truoc duoc tu TEN MODEL. Dung bung danh sach model tu lan chay mien khac.)")
    print("      - Nhanh NEN co bi gac trich xuat khong, hay chi gac nhanh V? (#198: gac nua so nhanh")
    print("        roi quen nua kia -> acc cua hai model KHONG so duoc. Day la confound #138.)")
    print("      - NGAN SACH THOI GIAN: uoc bao nhieu gio? Co `stop_strings` khong? (#198: MATH khong")
    print("        co rao ``` nen moi luot chay toi tran token -> ~4x MBPP, cham chan 10.5h, mat 3 cap.)")

    print("\n" + "="*60)
    if warn:
        print("CANH BAO — PHAI XU LY TRUOC KHI PHONG:")
        for w in warn: print(f"  ! {w}")
        return 1
    print("khong co canh bao tu dong. Muc [2] va [4] van phai xem bang mat.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
