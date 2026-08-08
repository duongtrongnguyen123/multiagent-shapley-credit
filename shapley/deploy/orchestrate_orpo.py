#!/usr/bin/env python3
"""Deploy the ORPO LoRA training kernel for the aggregator.

  ACCOUNT=tbmdemi python deploy/orchestrate_orpo.py

Needs the preference pairs uploaded as a Kaggle dataset first (see PAIRS_DS below).
Internet is enabled because trl/peft must be installed at runtime.
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
SRC = ROOT / "pipeline" / "orpo_kernel.py"
EPOCHS = os.environ.get("EPOCHS", "2")
LR = os.environ.get("LR", "5e-5")
BETA = os.environ.get("BETA", "0.1")
MAXLEN = os.environ.get("MAXLEN", "2048")
ACCOUNT = os.environ.get("ACCOUNT", "")
KDIR = ROOT / "kernels_orpo"
PAIRS_DS = os.environ.get("PAIRS_DS", "tbmdemi/aggpref-math-1p5b")
DATASETS = ["xatri007/qwen2-5-1-5b-instruct", PAIRS_DS]

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

def pick():
    accs = accounts()
    if ACCOUNT:
        hit = [(u, t) for u, t in accs if u.lower() == ACCOUNT.lower()]
        if not hit:
            raise SystemExit(f"ACCOUNT={ACCOUNT} not in {ACCOUNTS}")
        return hit[0]
    if not accs:
        raise SystemExit(f"no accounts in {ACCOUNTS}")
    return accs[0]

def main():
    user, token = pick()
    src = (SRC.read_text(encoding="utf-8")
              .replace("__EPOCHS__", EPOCHS).replace("__LR__", LR)
              .replace("__BETA__", BETA).replace("__MAXLEN__", MAXLEN))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")
    slug = "orpo-agg-math"
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / "train"
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{slug}"
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": slug, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         # trl/peft phải cài lúc chạy -> cần internet, khác mọi kernel inference trước
         "enable_internet": True, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": DATASETS, "competition_sources": [], "kernel_sources": []}, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] epochs={EPOCHS} lr={LR} beta={BETA} -> {user} {'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    man = ROOT / "manifest_orpo.json"
    man.write_text(json.dumps([{"user": user, "token": token, "slug": slug,
                                "ref": ref, "pushed": ok}], indent=2))

if __name__ == "__main__":
    main()
