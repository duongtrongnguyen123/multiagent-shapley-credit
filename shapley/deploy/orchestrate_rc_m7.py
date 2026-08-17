#!/usr/bin/env python3
"""Deploy rc_m7 kernel (H17: MATH 7B FULL vs TRIM 5-fold).

  python deploy/orchestrate_rc_m7.py [ACCOUNT]

Account optional; defaults to first in accounts.txt.
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt"))
KERNEL = "rc_m7"
SRC = ROOT / "pipeline" / f"{KERNEL}_kernel.py"
KDIR = ROOT / f"kernels_{KERNEL}"

# 7B model on Kaggle T4 (4-bit quant)
DS_MODEL_7B = "ragnar123/qwen2-5-7b-instruct"
DS_MATH = "open-benchmarks/math-500-measuring-mathematical-problem-solving"
DATASETS = [DS_MODEL_7B, DS_MATH]

N = int(os.environ.get("N", "150"))
BS = int(os.environ.get("BS", "2"))

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
    src = src.replace("__N__", str(N)).replace("__BS__", str(BS))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")

    slug = f"{KERNEL}-math"
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / "math"
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": f"{user}/{slug}", "title": slug, "code_file": "kernel.py",
         "language": "python", "kernel_type": "script", "is_private": True,
         "enable_gpu": True, "enable_internet": False, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": DATASETS, "competition_sources": [], "kernel_sources": []}, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] N={N} BS={BS} -> {user} {'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)

    man = ROOT / f"manifest_{KERNEL}.json"
    cur = json.loads(man.read_text()) if man.exists() else []
    cur = [m for m in cur if m.get("slug") != slug] + [
        {"kernel": KERNEL, "task": "math", "user": user, "token": token,
         "slug": slug, "ref": f"{user}/{slug}", "pushed": ok}]
    man.write_text(json.dumps(cur, indent=2))

if __name__ == "__main__":
    main()
