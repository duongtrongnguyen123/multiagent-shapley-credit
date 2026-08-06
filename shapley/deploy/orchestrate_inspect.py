#!/usr/bin/env python3
"""Deploy the planner-inspection kernel (dump raw Planner/Solver output).

  TASK=gsm8k N=8 python deploy/orchestrate_inspect.py
  TASK=math  N=8 python deploy/orchestrate_inspect.py
  TASK=both  N=8 python deploy/orchestrate_inspect.py   # push both, one kernel each

Small N on purpose: this is a qualitative read, not an effect measurement.
Auth: accounts.txt first line if present, else the OAuth identity.
"""
import os, re, json, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt"))
TEMPLATE = (ROOT / "pipeline" / "inspect_planner_kernel.py").read_text(encoding="utf-8")
TASK = os.environ.get("TASK", "both")
N = int(os.environ.get("N", "8"))
BS = int(os.environ.get("BS", "8"))
ACCOUNT = os.environ.get("ACCOUNT", "")   # chọn dòng trong accounts.txt theo username
KDIR = ROOT / "kernels_inspect"
DS_MODEL = "xatri007/qwen2-5-1-5b-instruct"
DS = {"gsm8k": [DS_MODEL, "thedevastator/grade-school-math-8k-q-a"],
      "math":  [DS_MODEL, "open-benchmarks/math-500-measuring-mathematical-problem-solving"]}

def accounts():
    out = []
    if not ACCOUNTS.exists():
        return out
    for line in ACCOUNTS.read_text().splitlines():
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
        d = json.loads((Path.home() / ".kaggle" / "credentials.json").read_text())
        return d.get("username", "")
    except Exception:
        return ""

def push(user, token, task):
    src = (TEMPLATE.replace("__TASK__", task)
                   .replace("__N__", str(N)).replace("__BS__", str(BS)))
    slug = f"inspect-planner-{task}"
    d = KDIR / task
    d.mkdir(parents=True, exist_ok=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{slug}" if user else slug
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": slug, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         "enable_internet": False, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": DS[task], "competition_sources": [], "kernel_sources": []}, indent=2))
    env = dict(os.environ, KAGGLE_API_TOKEN=token) if token else dict(os.environ)
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=env, capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] TASK={task} N={N} -> {user or 'oauth'} {'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    return {"task": task, "user": user, "token": token, "slug": slug, "ref": ref, "pushed": ok}

def main():
    accs = accounts()
    if ACCOUNT:
        hit = [(u, t) for u, t in accs if u.lower() == ACCOUNT.lower()]
        if not hit:
            raise SystemExit(f"ACCOUNT={ACCOUNT} không có trong {ACCOUNTS}")
        user, token = hit[0]
    else:
        user, token = (accs[0][0], accs[0][1]) if accs else (oauth_username(), "")
    tasks = ["gsm8k", "math"] if TASK == "both" else [TASK]
    shutil.rmtree(KDIR, ignore_errors=True)
    manifest = []
    for t in tasks:
        manifest.append(push(user, token, t))
        time.sleep(2)
    (ROOT / "manifest_inspect.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n=== deployed {sum(m['pushed'] for m in manifest)}/{len(manifest)} ===")

if __name__ == "__main__":
    main()
