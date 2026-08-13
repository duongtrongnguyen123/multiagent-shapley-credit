#!/usr/bin/env python3
"""H65 (dang ky truoc #70 + #70-b): MOT kernel tren Kaggle 2x T4.

RTX 6000 Pro KHONG con: competition nemotron dong han 2026-06-15 nen suat tinh toan het
hieu luc; Kaggle van nhan competition_sources roi AM THAM cap P100 sm_60 (torch khong chay).

Can internet CHI de cai bitsandbytes (nf4). Model va MATH-500 mount tu dataset.

Token KHONG BAO GIO ghi vao file. Truyen qua bien moi truong:
  KAGGLE_API_TOKEN=$(awk '/^zhongzhing /{print $2}' <duong-dan>/accounts.txt) python deploy/launch_h65.py
"""
import os, sys, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("RUN", "H65")
TEMPLATE = (ROOT / "pipeline" / "capacity_poison_kernel.py").read_text()
KDIR = ROOT / f"kernels_{RUN.lower()}"
USER = os.environ.get("KUSER", "zhongzhing")

DATASETS = ["xatri007/qwen2-5-1-5b-instruct",
            "ragnar123/qwen2-5-7b-instruct",
            "syzong/qwen2-5-14b-instruct",
            "open-benchmarks/math-500-measuring-mathematical-problem-solving"]
COMP = []   # #70-b: competition nemotron da dong han 2026-06-15 -> lien ket VO HIEU, Kaggle cap P100

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
            "enable_gpu": True, "enable_internet": True,   # can internet cho bitsandbytes (nf4)
            "machine_shape": "NvidiaTeslaT4",
            "dataset_sources": DATASETS, "competition_sources": COMP, "kernel_sources": []}
    (KDIR / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))

    assert meta["machine_shape"] == "NvidiaTeslaT4", "machine_shape phai la ten enum hop le"
    assert meta["enable_gpu"] is True and meta["enable_internet"] is True

    env = dict(os.environ, KAGGLE_API_TOKEN=tok)
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(KDIR)],
                       env=env, capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    print(out.strip())
    if "successfully pushed" not in out:
        sys.exit("PUSH THAT BAI — khong doc ket qua")
    print(f"\nda day: {USER}/{slug}")
    print("KIEM TRA NGAY khi chay: log phai in 'Tesla T4' va 'sm_75', va 2 GPU.")
    print("Neu in Tesla P100 (sm_60) -> torch khong chay duoc, HUY.")

if __name__ == "__main__":
    main()
