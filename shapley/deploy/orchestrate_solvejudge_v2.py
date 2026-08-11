#!/usr/bin/env python3
"""Push kernel pipeline solve-judge v2 (Judge nâng cấp) lên Kaggle T4.

  TASK=math   JUDGE_MODE=fewshot ACCOUNT=TrgDinKai python deploy/orchestrate_solvejudge_v2.py
  TASK=math   JUDGE_MODE=vote    ACCOUNT=tbmdemi   python deploy/orchestrate_solvejudge_v2.py
  TASK=gsm8k  JUDGE_MODE=fewshot ACCOUNT=TrgDinKai python deploy/orchestrate_solvejudge_v2.py
  TASK=gsm8k  JUDGE_MODE=vote    ACCOUNT=tbmdemi   python deploy/orchestrate_solvejudge_v2.py
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
SRC = ROOT / "pipeline" / "solvejudge_v2_kernel.py"
N = int(os.environ.get("N", "150"))
NF = int(os.environ.get("NF", "5"))
BS = int(os.environ.get("BS", "8"))
TASK = os.environ.get("TASK", "math")
JUDGE_MODE = os.environ.get("JUDGE_MODE", "single")
ACCOUNT = os.environ.get("ACCOUNT", "")
KDIR = ROOT / "kernels_solvejudge_v2"
DS_MODEL = "xatri007/qwen2-5-1-5b-instruct"
DATASETS = {"math":  [DS_MODEL, "open-benchmarks/math-500-measuring-mathematical-problem-solving"],
            "gsm8k": [DS_MODEL, "thedevastator/grade-school-math-8k-q-a"]}[TASK]

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
              .replace("__N__", str(N)).replace("__NF__", str(NF))
              .replace("__BS__", str(BS)).replace("__TASK__", TASK)
              .replace("__JUDGE_MODE__", JUDGE_MODE))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")
    slug = f"sj2-{TASK}-{JUDGE_MODE}"
    d = KDIR
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
    print(f"[{slug}] {TASK}/{JUDGE_MODE} -> {user} {'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)

if __name__ == "__main__":
    main()