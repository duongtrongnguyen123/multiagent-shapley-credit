#!/usr/bin/env python3
"""Deploy the preference-data generation kernel, optionally sharded across accounts.

  # smoke test on one slot first
  N=50 SHARD=0 N_SHARDS=1 ACCOUNT=TrgDinKai python deploy/orchestrate_genpref.py

  # then fan out 3 shards over 2 accounts (leaves one slot free)
  N=500 SHARD=0 N_SHARDS=3 ACCOUNT=TrgDinKai python deploy/orchestrate_genpref.py
  N=500 SHARD=1 N_SHARDS=3 ACCOUNT=TrgDinKai python deploy/orchestrate_genpref.py
  N=500 SHARD=2 N_SHARDS=3 ACCOUNT=tbmdemi   python deploy/orchestrate_genpref.py

N is per-shard. Each shard takes ALL[SHARD::N_SHARDS] after a fixed shuffle, so shards get
comparable topic/difficulty mixes rather than contiguous blocks of one MATH subject.
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
SRC = ROOT / "pipeline" / "genpref_kernel.py"
N = int(os.environ.get("N", "500"))
SHARD = int(os.environ.get("SHARD", "0"))
N_SHARDS = int(os.environ.get("N_SHARDS", "3"))
BS = int(os.environ.get("BS", "4"))
ACCOUNT = os.environ.get("ACCOUNT", "")
KDIR = ROOT / "kernels_genpref"
# MATH train split (Hendrycks) - verified to contain MATH/train/ and MATH/test/
DATASETS = ["xatri007/qwen2-5-1-5b-instruct", "angelirodriguez/hendrycks-math-dataset"]

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
              .replace("__N__", str(N)).replace("__SHARD__", str(SHARD))
              .replace("__N_SHARDS__", str(N_SHARDS)).replace("__BS__", str(BS)))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")      # catch syntax errors before pushing
    slug = f"genpref-math-s{SHARD}"
    d = KDIR / f"s{SHARD}"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{slug}"
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": slug, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         "enable_internet": False, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": DATASETS, "competition_sources": [], "kernel_sources": []}, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] N={N} shard {SHARD}/{N_SHARDS} -> {user} {'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    man = ROOT / "manifest_genpref.json"
    cur = json.loads(man.read_text()) if man.exists() else []
    cur = [m for m in cur if m.get("slug") != slug] + [
        {"shard": SHARD, "n_shards": N_SHARDS, "n": N, "user": user, "token": token,
         "slug": slug, "ref": ref, "pushed": ok}]
    man.write_text(json.dumps(cur, indent=2))

if __name__ == "__main__":
    main()
