#!/usr/bin/env python3
"""Bo phong chung: day MOT kernel len MOT tai khoan bat ky trong fleet.

  KERNEL=pipeline/x.py RUN=H66 KUSER=hduong DATASETS=a/b,c/d python deploy/launch_any.py

Quy tac tai nguyen (Nguyen, 2026-08-13):
  - `tai khoan RTX` CHI dung cho viec THAT SU can RTX 6000 Pro (>=40 GB).
    Muon dung: MACHINE=NvidiaRtxPro6000 COMP=arc-prize-2026-arc-agi-3 (comp phai CON MO).
  - Moi viec khac -> tai khoan khac, T4.
Token doc tu accounts.txt theo username, KHONG BAO GIO ghi vao file.
"""
import os, sys, json, shutil, subprocess
from pathlib import Path

RTX_ONLY = os.environ.get("KAGGLE_RTX_ACCOUNT", "")  # tai khoan RTX, dat qua bien moi truong

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
    LO      = os.environ.get("LO", "11")
    HI      = os.environ.get("HI", "510")
    DEAR    = os.environ.get("DEAR", "2-5-7b,qwen2-5-7b")
    CHEAP   = os.environ.get("CHEAP", "1-5b,1_5b,1.5b")   # #98: mac dinh = Qwen 7B (cung ho)
    INTERNET = os.environ.get("INTERNET", "1" if MACHINE == "NvidiaTeslaT4" else "0") == "1"

    if MACHINE == "NvidiaRtxPro6000":
        if USER != RTX_ONLY: sys.exit("RTX 6000 Pro chi cau hinh cho tai khoan RTX")
        if not COMP: sys.exit("RTX 6000 Pro CAN competition_sources con hieu luc")
        if INTERNET: sys.exit("competition cam internet -> push se tra HTTP 400")
    elif USER == RTX_ONLY:
        sys.exit("tai khoan RTX DE DANH cho viec can RTX 6000 Pro — dung tai khoan khac cho T4")

    raw = (ROOT / kernel).read_text()
    # #143: RTX 6000 chay trong competition -> KHONG internet. H91 goi load_dataset("mbpp") va
    # chet ngay dong do, truoc khi in duoc mot chu ("client has been closed"), phi ca khe RTX.
    # Kernel chay khong internet PHAI co duong nap tu dataset da stage.
    if not INTERNET and "load_dataset(" in raw and "/kaggle/input" not in raw.split("load_dataset(")[0][-800:]:
        if "mbpp_full.json" not in raw and "glob.glob(\"/kaggle/input" not in raw:
            sys.exit("KHONG internet nhung kernel goi load_dataset() ma khong co duong nap tu "
                     "dataset da stage -> se chet ngay dong do. Stage benchmark thanh dataset truoc.")
    # #121: launcher CHI kiem "con placeholder chua thay", KHONG kiem "placeholder co ton tai".
    # Vi the LO=511 HI=974 bi BO QUA IM LANG khi kernel hardcode dai -> tao ra mot ban
    # "tai lap" GIA chay tren dung du lieu cu. Kiem xuoi: da truyen thi PHAI co cho de thay.
    for var, ph in (("LO", "@@LO@@"), ("HI", "@@HI@@"), ("SIZE", "@@SIZE@@"), ("DEAR", "@@DEAR@@"), ("CHEAP", "@@CHEAP@@")):
        if os.environ.get(var) and ph not in raw:
            sys.exit(f"{var}={os.environ[var]} duoc truyen nhung kernel KHONG co {ph} "
                     f"-> se bi bo qua im lang. Tham so hoa kernel truoc.")
    src = (raw.replace("@@RUN@@", RUN).replace("@@SIZE@@", SIZE)
           .replace("@@LO@@", LO).replace("@@HI@@", HI).replace("@@DEAR@@", DEAR).replace("@@CHEAP@@", CHEAP))
    for ph in ["@@RUN@@", "@@SIZE@@", "@@LO@@", "@@HI@@", "@@DEAR@@", "@@CHEAP@@"]:
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
