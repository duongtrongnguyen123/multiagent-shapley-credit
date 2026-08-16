#!/usr/bin/env python3
"""Deploy A-SEL vs majority-vote comparison kernel.

  ACCOUNT=Viettran12 TASK=gsm8k python deploy/orchestrate_asel_vs_vote.py
  ACCOUNT=tbmdemi   TASK=math  python deploy/orchestrate_asel_vs_vote.py

Measures 6 arms (S, vote2, vote3, vote5, A_base, A_sel) on the SAME folds
with the SAME candidates, on GSM8K test or MATH-500 test.
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
SRC = ROOT / "pipeline" / "asel_vs_vote_kernel.py"
TASK = os.environ.get("TASK", "gsm8k")
N = int(os.environ.get("N", "200"))
NF = int(os.environ.get("NF", "5"))
BS = int(os.environ.get("BS", "4"))
ADAPTER_DS = os.environ.get("ADAPTER_DS", "TrgDinKai/credit-rl-asel-adapter")
SLUG = os.environ.get("SLUG", "")
ACCOUNT = os.environ.get("ACCOUNT", "")
KDIR = ROOT / "kernels_asel_vs_vote"
MODEL_DS = "xatri007/qwen2-5-1-5b-instruct"
GSM_DS = "thedevastator/grade-school-math-8k-q-a"
MATH_DS = "open-benchmarks/math-500-measuring-mathematical-problem-solving"


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
    if TASK not in ("gsm8k", "math"):
        raise SystemExit(f"TASK={TASK} invalid (gsm8k|math)")
    datasets = [MODEL_DS, GSM_DS, ADAPTER_DS] if TASK == "gsm8k" else [MODEL_DS, MATH_DS, ADAPTER_DS]
    src = (SRC.read_text(encoding="utf-8")
              .replace("__TASK__", repr(TASK))
              .replace("__N__", str(N))
              .replace("__NF__", str(NF)).replace("__BS__", str(BS)))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")
    slug = SLUG or f"asel-vs-vote-{TASK}"
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / "cmp"
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{slug}"
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": slug, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         "enable_internet": True, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": datasets, "competition_sources": [], "kernel_sources": []},
        indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] TASK={TASK} N={N} NF={NF} adapter={ADAPTER_DS} -> {user} "
          f"{'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    (ROOT / "manifest_asel_vs_vote.json").write_text(json.dumps(
        [{"user": user, "token": token, "slug": slug, "ref": ref, "task": TASK,
          "pushed": ok}], indent=2))


if __name__ == "__main__":
    main()