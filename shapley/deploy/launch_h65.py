#!/usr/bin/env python3
"""H65 (dang ky truoc #70): MOT kernel tren Kaggle RTX 6000 Pro (102 GB).

CONG BA TRUONG (neu thieu bat ky cai nao -> Kaggle AM THAM tut ve P100 sm_60):
  machine_shape "NvidiaRtxPro6000" + enable_gpu true + competition_sources [nemotron]

KHONG can internet: model va MATH-500 deu mount tu dataset, ba model chay bf16 nen
khong phai cai bitsandbytes. Tranh luon chuoi loi goi da giet H54.

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
COMP = ["nvidia-nemotron-model-reasoning-challenge"]

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
            "enable_gpu": True, "enable_internet": False,
            "machine_shape": "NvidiaRtxPro6000",
            "dataset_sources": DATASETS, "competition_sources": COMP, "kernel_sources": []}
    (KDIR / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))

    for k in ("machine_shape", "enable_gpu", "competition_sources"):
        assert meta.get(k), f"CONG BA TRUONG: thieu {k} -> se tut ve P100"

    env = dict(os.environ, KAGGLE_API_TOKEN=tok)
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(KDIR)],
                       env=env, capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    print(out.strip())
    if "successfully pushed" not in out:
        sys.exit("PUSH THAT BAI — khong doc ket qua")
    print(f"\nda day: {USER}/{slug}")
    print(f"KIEM TRA NGAY khi chay: log phai in 'RTX PRO 6000' va 'sm_120'.")
    print(f"Neu in Tesla P100 -> cong ba truong hong, HUY va sua metadata.")

if __name__ == "__main__":
    main()
