#!/usr/bin/env python3
"""Deploy the few-shot x 5-fold kernel (error bars, H13/H14 style).

  TASK=math  N=250 NF=5 ACCOUNT=tai khoan RTX python deploy/orchestrate_fewshot_folds.py
  TASK=gsm8k N=250 NF=5 ACCOUNT=TrgDinKai  python deploy/orchestrate_fewshot_folds.py

ACCOUNTS_FILE defaults to shapley/accounts.txt; ~/.kaggle/accounts.txt also works.
"""
import os, re, json, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
TEMPLATE = (ROOT / "pipeline" / "fewshot_folds_kernel.py").read_text(encoding="utf-8")
TASK = os.environ.get("TASK", "math")
N = int(os.environ.get("N", "250"))
NF = int(os.environ.get("NF", "5"))
BS = int(os.environ.get("BS", "4"))
ACCOUNT = os.environ.get("ACCOUNT", "")
KDIR = ROOT / "kernels_fsfold"
DS_MODEL = "xatri007/qwen2-5-1-5b-instruct"
DS = {"gsm8k": [DS_MODEL, "thedevastator/grade-school-math-8k-q-a"],
      "math":  [DS_MODEL, "open-benchmarks/math-500-measuring-mathematical-problem-solving"]}

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

def oauth_username():
    try:
        d = json.loads((Path.home() / ".kaggle" / "credentials.json").read_text(encoding="utf-8"))
        return d.get("username", "")
    except Exception:
        return ""

def pick():
    accs = accounts()
    if ACCOUNT:
        hit = [(u, t) for u, t in accs if u.lower() == ACCOUNT.lower()]
        if not hit:
            raise SystemExit(f"ACCOUNT={ACCOUNT} không có trong {ACCOUNTS}")
        return hit[0]
    return (accs[0][0], accs[0][1]) if accs else (oauth_username(), "")

def main():
    user, token = pick()
    src = (TEMPLATE.replace("__TASK__", TASK).replace("__N__", str(N))
                   .replace("__NF__", str(NF)).replace("__BS__", str(BS)))
    compile(src, "<kernel>", "exec")     # bắt lỗi cú pháp TRƯỚC khi push (bài học 76dbde6)
    slug = f"fewshot-folds-{TASK}"
    d = KDIR / TASK
    shutil.rmtree(KDIR, ignore_errors=True)
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{slug}" if user else slug
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": slug, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         "enable_internet": False, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": DS[TASK], "competition_sources": [], "kernel_sources": []}, indent=2))
    env = dict(os.environ, KAGGLE_API_TOKEN=token) if token else dict(os.environ)
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=env, capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] TASK={TASK} N={N} NF={NF} -> {user} {'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    man = ROOT / "manifest_fsfold.json"
    cur = json.loads(man.read_text()) if man.exists() else []
    cur = [m for m in cur if m.get("task") != TASK] + [
        {"task": TASK, "user": user, "token": token, "slug": slug, "ref": ref, "pushed": ok}]
    man.write_text(json.dumps(cur, indent=2))

if __name__ == "__main__":
    main()
