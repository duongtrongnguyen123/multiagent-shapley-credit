#!/usr/bin/env python3
"""Deploy the full-pipeline rescue kernel (P->S->V->A, graded after every stage).

  TASK=gsm8k N=150 NF=5 ACCOUNT=TrgDinKai python deploy/orchestrate_rescue.py
  TASK=math  N=150 NF=5 ACCOUNT=zhongzhing python deploy/orchestrate_rescue.py
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
TEMPLATE = (ROOT / "pipeline" / "fullpipe_rescue_kernel.py").read_text(encoding="utf-8")
TASK = os.environ.get("TASK", "gsm8k")
N = int(os.environ.get("N", "150"))
NF = int(os.environ.get("NF", "5"))
BS = int(os.environ.get("BS", "8"))
ACCOUNT = os.environ.get("ACCOUNT", "")
BIG = os.environ.get("BIG", "0") not in ("0", "", "false", "False")
KDIR = ROOT / "kernels_rescue"
DS_MODEL = "xatri007/qwen2-5-1-5b-instruct"
DS_BIG = "ragnar123/qwen2-5-7b-instruct"
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
    src = (TEMPLATE.replace("__TASK__", TASK).replace("__N__", str(N))
                   .replace("__NF__", str(NF)).replace("__BS__", str(BS))
                   .replace("__BIG__", "True" if BIG else "False"))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")      # catch syntax errors before pushing
    slug = f"rescue-fullpipe-{TASK}" + ("-7b" if BIG else "")
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / TASK
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{slug}"
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": slug, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         "enable_internet": False, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": (DS[TASK] + [DS_BIG]) if BIG else DS[TASK],
         "competition_sources": [], "kernel_sources": []}, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] TASK={TASK} N={N} NF={NF} -> {user} {'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    man = ROOT / "manifest_rescue.json"
    cur = json.loads(man.read_text()) if man.exists() else []
    cur = [m for m in cur if m.get("task") != TASK] + [
        {"task": TASK, "user": user, "token": token, "slug": slug, "ref": ref, "pushed": ok}]
    man.write_text(json.dumps(cur, indent=2))

if __name__ == "__main__":
    main()
