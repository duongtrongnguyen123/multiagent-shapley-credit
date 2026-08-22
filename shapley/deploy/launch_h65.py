#!/usr/bin/env python3
"""H65 (dang ky truoc #70 + #70-b): MOT kernel tren Kaggle 2x T4.

RTX 6000 Pro KHONG con: competition nemotron dong han 2026-06-15 nen suat tinh toan het
hieu luc; Kaggle van nhan competition_sources roi AM THAM cap P100 sm_60 (torch khong chay).

Can internet CHI de cai bitsandbytes (nf4). Model va MATH-500 mount tu dataset.

Token KHONG BAO GIO ghi vao file. Truyen qua bien moi truong:
  KAGGLE_API_TOKEN=$(awk '/^tai khoan RTX /{print $2}' <duong-dan>/accounts.txt) python deploy/launch_h65.py
"""
import os, sys, json, shutil, subprocess
from pathlib import Path

RTX_ONLY = os.environ.get("KAGGLE_RTX_ACCOUNT", "")  # tai khoan RTX, dat qua bien moi truong

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("RUN", "H65")
TEMPLATE = (ROOT / "pipeline" / "capacity_poison_kernel.py").read_text()
KDIR = ROOT / f"kernels_{RUN.lower()}"
USER = os.environ.get("KUSER", RTX_ONLY)

DATASETS = ["xatri007/qwen2-5-1-5b-instruct",
            "ragnar123/qwen2-5-7b-instruct",
            "syzong/qwen2-5-14b-instruct",
            "open-benchmarks/math-500-measuring-mathematical-problem-solving"]
# CHON PHAN CUNG qua bien moi truong:
#   MACHINE=NvidiaRtxPro6000 COMP=arc-prize-2026-arc-agi-3   -> 102 GB, bf16, KHONG internet
#   MACHINE=NvidiaTeslaT4                                    -> 2x16 GB, nf4, CAN internet
# LUU Y: nemotron da dong han 2026-06-15 -> lien ket VO HIEU (Kaggle am tham cap P100).
#        arc-prize-2026-arc-agi-3 con mo den 2026-11-02 va VAN cap RTX 6000 Pro.
MACHINE = os.environ.get("MACHINE", "NvidiaTeslaT4")
COMP = [c for c in os.environ.get("COMP", "").split(",") if c]
INTERNET = MACHINE == "NvidiaTeslaT4"   # competition ARC/Nemotron CAM internet (push tra HTTP 400)

def main():
    tok = os.environ.get("KAGGLE_API_TOKEN")
    if not tok:
        sys.exit("thieu KAGGLE_API_TOKEN — xem docstring")
    src = TEMPLATE.replace("@@RUN@@", RUN)
    if "@@" in src: sys.exit("con placeholder chua thay")

    slug = f"capacity-poisoning-sweep-{RUN.lower()}"
    shutil.rmtree(KDIR, ignore_errors=True); KDIR.mkdir(parents=True)
    (KDIR / "kernel.py").write_text(src)
    meta = {"id": f"{USER}/{slug}", "title": slug, "code_file": "kernel.py",
            "language": "python", "kernel_type": "script", "is_private": True,
            "enable_gpu": True, "enable_internet": INTERNET,
            "machine_shape": MACHINE,
            "dataset_sources": DATASETS, "competition_sources": COMP, "kernel_sources": []}
    (KDIR / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))

    assert meta["machine_shape"] in ("NvidiaTeslaT4", "NvidiaRtxPro6000"), "ten enum khong hop le"
    assert meta["enable_gpu"] is True
    if MACHINE == "NvidiaRtxPro6000":
        assert COMP, "RTX 6000 Pro CAN competition_sources con hieu luc, neu khong se tut ve P100"
        assert not INTERNET, "competition cam internet -> push se tra HTTP 400"

    env = dict(os.environ, KAGGLE_API_TOKEN=tok)
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(KDIR)],
                       env=env, capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    print(out.strip())
    if "successfully pushed" not in out:
        sys.exit("PUSH THAT BAI — khong doc ket qua")
    print(f"\nda day: {USER}/{slug}")
    print(f"machine={MACHINE} comp={COMP} internet={INTERNET}")
    print("Kernel TU HUY neu nhan sm_60 (P100) — xem dong 'CHE DO:' dau log.")

if __name__ == "__main__":
    main()
