#!/usr/bin/env python3
"""Bo phong chung: day MOT kernel len MOT tai khoan bat ky trong fleet.

  KERNEL=pipeline/x.py RUN=H66 KUSER=hduong DATASETS=a/b,c/d python deploy/launch_any.py

Quy tac tai nguyen (Nguyen, 2026-08-13):
  - `zhongzhing` CHI dung cho viec THAT SU can RTX 6000 Pro (>=40 GB).
    Muon dung: MACHINE=NvidiaRtxPro6000 COMP=arc-prize-2026-arc-agi-3 (comp phai CON MO).
  - Moi viec khac -> tai khoan khac, T4.
Token doc tu accounts.txt theo username, KHONG BAO GIO ghi vao file.
"""
import os, sys, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACC = Path(os.environ.get("ACCOUNTS", "/Users/hduong/dev/recurrent-research/accounts.txt"))

def token_for(user):
    for line in ACC.read_text().splitlines():
        p = line.split()
        if len(p) >= 2 and p[0] == user: return p[1]
    sys.exit(f"khong thay tai khoan {user} trong {ACC}")

def main():
    kernel = os.environ.get("KERNEL") or sys.exit("thieu KERNEL")
    RUN    = os.environ.get("RUN")    or sys.exit("thieu RUN")
    USER   = os.environ.get("KUSER")  or sys.exit("thieu KUSER")
    SLUG   = os.environ.get("SLUG", RUN.lower())
    MACHINE = os.environ.get("MACHINE", "NvidiaTeslaT4")
    COMP    = [c for c in os.environ.get("COMP", "").split(",") if c]
    DATASETS = [d for d in os.environ.get("DATASETS", "").split(",") if d]
    SIZE    = os.environ.get("SIZE", "7")
    INTERNET = os.environ.get("INTERNET", "1" if MACHINE == "NvidiaTeslaT4" else "0") == "1"

    if MACHINE == "NvidiaRtxPro6000":
        if USER != "zhongzhing": sys.exit("RTX 6000 Pro chi cau hinh cho zhongzhing")
        if not COMP: sys.exit("RTX 6000 Pro CAN competition_sources con hieu luc")
        if INTERNET: sys.exit("competition cam internet -> push se tra HTTP 400")
    elif USER == "zhongzhing":
        sys.exit("zhongzhing DE DANH cho viec can RTX 6000 Pro — dung tai khoan khac cho T4")

    src = (ROOT / kernel).read_text().replace("@@RUN@@", RUN).replace("@@SIZE@@", SIZE)
    for ph in ["@@RUN@@", "@@SIZE@@"]:
        if ph in src: sys.exit(f"con placeholder: {ph}")
    if "@@" in src: sys.exit(f"con placeholder chua thay: {[l for l in src.splitlines() if '@@' in l][:2]}")

    KDIR = ROOT / f"kernels_{RUN.lower()}"
    shutil.rmtree(KDIR, ignore_errors=True); KDIR.mkdir(parents=True)
    (KDIR / "kernel.py").write_text(src)
    meta = {"id": f"{USER}/{SLUG}", "title": SLUG, "code_file": "kernel.py",
            "language": "python", "kernel_type": "script", "is_private": True,
            "enable_gpu": True, "enable_internet": INTERNET, "machine_shape": MACHINE,
            "dataset_sources": DATASETS, "competition_sources": COMP, "kernel_sources": []}
    (KDIR / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))

    env = dict(os.environ, KAGGLE_API_TOKEN=token_for(USER))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(KDIR)],
                       env=env, capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    if "successfully pushed" not in out:
        print(out.strip()); sys.exit(f"PUSH THAT BAI cho {USER}/{SLUG}")
    print(f"OK {USER}/{SLUG}  machine={MACHINE} internet={INTERNET} comp={COMP}")

if __name__ == "__main__":
    main()
