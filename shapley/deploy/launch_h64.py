#!/usr/bin/env python3
"""H64 (dang ky truoc #69 + #69-b): MOT kernel duy nhat tren tai khoan mac dinh (~/.kaggle/kaggle.json).

Khong can fleet: ClassEval chi 100 lop, ~700 luot sinh -> vua mot phien 12h tren 2x T4.
enable_internet BAT BUOC: kernel tai ClassEval tu HuggingFace VA cai bitsandbytes cho nf4.
"""
import os, sys, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("RUN", "H64")
SIZE = os.environ.get("SIZE", "7")
TEMPLATE = (ROOT / "pipeline" / "classeval_plan_kernel.py").read_text()
KDIR = ROOT / f"kernels_{RUN.lower()}"

DATASETS = ["xatri007/qwen2-5-1-5b-instruct", "ragnar123/qwen2-5-7b-instruct"]

def main():
    user = json.loads((Path.home() / ".kaggle" / "kaggle.json").read_text())["username"]
    src = TEMPLATE.replace("@@SIZE@@", SIZE).replace("@@RUN@@", RUN)
    for tok in ["@@SIZE@@", "@@RUN@@"]:
        if tok in src: sys.exit(f"con placeholder chua thay: {tok}")

    slug = f"classeval-plan-vs-seq-{RUN.lower()}"
    shutil.rmtree(KDIR, ignore_errors=True); KDIR.mkdir(parents=True)
    (KDIR / "kernel.py").write_text(src)
    meta = {"id": f"{user}/{slug}", "title": slug, "code_file": "kernel.py",
            "language": "python", "kernel_type": "script", "is_private": True,
            "enable_gpu": True, "enable_internet": True,
            "machine_shape": "NvidiaTeslaT4",
            "dataset_sources": DATASETS, "competition_sources": [], "kernel_sources": []}
    (KDIR / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))

    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(KDIR)], capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    print(out.strip())
    if "successfully pushed" not in out:
        sys.exit("PUSH THAT BAI — khong doc ket qua")
    print(f"\nda day: {user}/{slug}")
    print(f"theo doi : kaggle kernels status {user}/{slug}")
    print(f"tai ve   : kaggle kernels output {user}/{slug} -p {ROOT}/res_{RUN.lower()}")

if __name__ == "__main__":
    main()
