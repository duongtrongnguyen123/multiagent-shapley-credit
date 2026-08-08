#!/usr/bin/env python3
"""Phong notebook len tai khoan zhongzhing, gan competition ARC-AGI-3, GPU = RTX 6000 Pro.

BA TRUONG BAT BUOC (thieu 1 -> Kaggle IM LANG tut ve P100):
    "enable_gpu": true
    "machine_shape": "NvidiaRtxPro6000"
    "competition_sources": ["arc-prize-2026-arc-agi-3"]
Tai khoan PHAI da bam Join/accept rules cua competition, neu khong kernel bi tu choi.
CAM INTERNET: enable_internet=true -> API tra ve 400 Bad Request. Phai de false.
Dung: python deploy/launch_arc.py <duong_dan_kernel.py> <ten-notebook> [ten_dataset ...]
"""
import os, re, sys, json, subprocess
from pathlib import Path

ACCOUNT = "zhongzhing"
COMP    = "arc-prize-2026-arc-agi-3"
SHAPE   = "NvidiaRtxPro6000"
ACCOUNTS_FILE = Path(os.environ.get("ACCOUNTS_FILE",
                    "/Users/hduong/dev/recurrent-research/accounts.txt"))

def token(user):
    for ln in ACCOUNTS_FILE.read_text().splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        p = s.split()
        if p[0] == user:
            m = re.search(r"KGAT_[0-9a-f]+", " ".join(p[1:]))
            if m:
                return m.group(0)
    raise SystemExit(f"khong tim thay token cho {user}")

def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    src, title = Path(sys.argv[1]), sys.argv[2]
    datasets = sys.argv[3:]
    import ast; ast.parse(src.read_text())          # LUAT: parse truoc khi day

    kd = Path(f"kernels_{title.replace('-','_')}"); kd.mkdir(exist_ok=True)
    (kd / "kernel.py").write_text(src.read_text())
    ref = f"{ACCOUNT}/{title}"
    meta = {
        "id": ref, "title": title, "code_file": "kernel.py", "language": "python",
        "kernel_type": "script",
        "is_private": True,                        # RIENG TU theo yeu cau
        "enable_gpu": True,                        # (1/3)
        "machine_shape": SHAPE,                    # (2/3)
        "enable_internet": False,   # BAT BUOC: competition ARC cam internet -> bat len se bi 400
        "dataset_sources": datasets,
        "competition_sources": [COMP],             # (3/3)
        "kernel_sources": [],
    }
    (kd / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    tok = token(ACCOUNT)
    (kd / "meta.json").write_text(json.dumps({"label": title, "token": tok, "ref": ref}))

    r = subprocess.run(["/opt/miniconda3/bin/kaggle", "kernels", "push", "-p", str(kd)],
                       capture_output=True, text=True,
                       env=dict(os.environ, KAGGLE_API_TOKEN=tok))
    out = (r.stdout + r.stderr).strip()
    print(out.splitlines()[-1][:100])
    if "successfully pushed" not in out:
        raise SystemExit("PUSH THAT BAI")
    print(f"OK -> https://www.kaggle.com/code/{ref}")

if __name__ == "__main__":
    main()
