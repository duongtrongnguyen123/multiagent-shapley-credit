#!/usr/bin/env python3
"""Upload credit-rl adapters (P/S/V/A) thành Kaggle datasets.

  python deploy/upload_credit_rl_adapters.py

Mỗi adapter được upload dưới đúng account đã train vai đó:
  V -> Viettran12/credit-rl-v-adapter
  S -> truongdinhduc06/credit-rl-s-adapter
  A -> TrgDinKai/credit-rl-a-adapter
  P -> tbmdemi/credit-rl-p-adapter

Lấy adapter đã tải về (crl_final/<account>_credit-rl-<role>-gsm8k/adapter).
Có thể override LOCAL_ROOT, hoặc ACCOUNT/ROLE để upload 1 vai.
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
LOCAL_ROOT = Path(os.environ.get("LOCAL_ROOT",
                 r"C:\Users\hp\AppData\Local\Temp\opencode\crl_final"))
ONLY = os.environ.get("ONLY", "")   # "P"|"S"|"V"|"A"|"" (upload tất cả)
WORK = Path(os.environ.get("WORK", ROOT / "kernels_credit_rl" / "adapter_upload"))

# vai -> (account, slug)
ROLES = {
    "P": ("tbmdemi", "credit-rl-p-adapter"),
    "S": ("truongdinhduc06", "credit-rl-s-adapter"),
    "V": ("Viettran12", "credit-rl-v-adapter"),
    "A": ("TrgDinKai", "credit-rl-a-adapter"),
}

def accounts():
    out = {}
    for line in ACCOUNTS.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        m = re.search(r"KGAT_[0-9a-f]+", parts[1]) if len(parts) > 1 else None
        if m:
            out[parts[0].lower()] = (parts[0], m.group(0))
    return out

def find_adapter_dir(role):
    if not LOCAL_ROOT.is_dir():
        raise SystemExit(f"LOCAL_ROOT khong ton tai: {LOCAL_ROOT}")
    hits = []
    for p in LOCAL_ROOT.iterdir():
        if not p.is_dir():
            continue
        ad = p / "adapter"
        if re.search(rf"_credit-rl-{role.lower()}-gsm8k$", p.name, re.I) and ad.is_dir():
            hits.append(ad)
    if not hits:
        raise SystemExit(f"khong thay adapter dir cho {role} trong {LOCAL_ROOT} "
                         f"(co: {[p.name for p in LOCAL_ROOT.iterdir()]})")
    return hits[0]

def main():
    accs = accounts()
    targets = [ONLY.upper()] if ONLY else list(ROLES)
    shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True)
    done = []
    for role in targets:
        user, slug = ROLES[role]
        tok = accs.get(user.lower())
        if not tok:
            raise SystemExit(f"account {user} khong co trong {ACCOUNTS}")
        adir = find_adapter_dir(role)
        d = WORK / role
        d.mkdir(parents=True)
        for f in adir.iterdir():
            shutil.copy2(f, d / f.name)
        ref = f"{user}/{slug}"
        (d / "dataset-metadata.json").write_text(json.dumps(
            {"id": ref, "title": slug, "licenses": [{"name": "CC0-1.0"}],
             "isPrivate": True}, indent=2))
        r = subprocess.run(["kaggle", "datasets", "create", "-p", str(d)],
                           env=dict(os.environ, KAGGLE_API_TOKEN=tok[1]),
                           capture_output=True, text=True)
        ok = "success" in (r.stdout or "").lower() or "is available at" in (r.stdout or "")
        done.append({"role": role, "user": user, "token": tok[1], "ref": ref,
                     "local": str(adir), "pushed": ok,
                     "msg": (r.stdout or r.stderr).strip().splitlines()[-1][:120]})
        print(f"[{role}] adapter {len(list(d.iterdir()))} files -> {ref} "
              f"{'OK' if ok else 'FAIL'}: {done[-1]['msg']}", flush=True)
    (ROOT / "manifest_credit_rl_adapters.json").write_text(
        json.dumps(done, indent=2))

if __name__ == "__main__":
    main()
