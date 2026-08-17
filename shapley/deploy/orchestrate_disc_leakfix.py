#!/usr/bin/env python3
"""Deploy disc_leakfix kernel (H27-fix: verifier phân biệt + rerank, sửa lỗi rò rỉ adapter #36/#37).

  KERNEL=disc_leakfix TASK=gsm8k NTR=300 NTE=300 BS=4 QUANT=0 MB=4 ACCOUNT=TrgDinKai python deploy/orchestrate_disc_leakfix.py
  KERNEL=disc_leakfix TASK=math  NTR=300 NTE=300 BS=4 QUANT=1 MB=4 ACCOUNT=TrgDinKai python deploy/orchestrate_disc_leakfix.py
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt"))
KERNEL = os.environ.get("KERNEL", "disc_leakfix")
SRC = ROOT / "pipeline" / f"{KERNEL}_kernel.py"

DS_MODEL_15B = "xatri007/qwen2-5-1-5b-instruct"
DS_GSM8K = "thedevastator/grade-school-math-8k-q-a"
DS_MATH = "open-benchmarks/math-500-measuring-mathematical-problem-solving"
DS = {"gsm8k": [DS_MODEL_15B, DS_GSM8K],
      "math":  [DS_MODEL_15B, DS_MATH]}

TASK = os.environ.get("TASK", "gsm8k")
KDIR = ROOT / f"kernels_{KERNEL}_{TASK}"
NTR = int(os.environ.get("NTR", "300"))
NTE = int(os.environ.get("NTE", "300"))
BS = int(os.environ.get("BS", "4"))
QUANT = int(os.environ.get("QUANT", "0"))
MB = int(os.environ.get("MB", "4"))

def accounts():
    out = []
    if not ACCOUNTS.exists():
        return out
    for line in ACCOUNTS.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        m = re.search(r"KGAT_[0-9a-f]+", parts[1]) if len(parts) > 1 else None
        if m:
            out.append((parts[0], m.group(0)))
    return out

def main():
    if not SRC.exists():
        raise SystemExit(f"no such kernel: {SRC}")
    accs = accounts()
    if not accs:
        raise SystemExit(f"no accounts in {ACCOUNTS}")
    account = os.environ.get("ACCOUNT", "")
    if account:
        hit = [(u, t) for u, t in accs if u.lower() == account.lower()]
        if not hit:
            raise SystemExit(f"ACCOUNT={account} not in {ACCOUNTS}")
        user, token = hit[0]
    else:
        user, token = accs[0]

    src = SRC.read_text(encoding="utf-8")
    src = (src.replace("__TASK__", TASK)
              .replace("__NTR__", str(NTR))
              .replace("__NTE__", str(NTE))
              .replace("__BS__", str(BS))
              .replace("__QUANT__", str(QUANT))
              .replace("__MB__", str(MB)))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")

    slug = f"{KERNEL}-{TASK}"
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / TASK
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": f"{user}/{slug}", "title": slug, "code_file": "kernel.py",
         "language": "python", "kernel_type": "script", "is_private": True,
         "enable_gpu": True, "enable_internet": False, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": DS[TASK], "competition_sources": [], "kernel_sources": []}, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] TASK={TASK} NTR={NTR} NTE={NTE} QUANT={QUANT} -> {user} "
          f"{'OK' if ok else 'FAIL'} {(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)

    man = ROOT / f"manifest_{KERNEL}.json"
    cur = json.loads(man.read_text()) if man.exists() else []
    cur = [m for m in cur if m.get("slug") != slug] + [
        {"kernel": KERNEL, "task": TASK, "user": user, "token": token,
         "slug": slug, "ref": f"{user}/{slug}", "pushed": ok}]
    man.write_text(json.dumps(cur, indent=2))

if __name__ == "__main__":
    main()
