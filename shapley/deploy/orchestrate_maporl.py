#!/usr/bin/env python3
"""Deploy the MAPoRL co-train (S/V/A) kernel.

  ACCOUNT=viettran12 python deploy/orchestrate_maporl.py

Co-trains S, V, A simultaneously via 3 LoRA adapters on 1 base model (P stays
base). Reward is influence-aware (correctness + influence on downstream agents),
grouped per question (GRPO advantage). Internet is enabled (peft installed at
runtime).

NOTE: KDIR = kernels_maporl (khac kernels_credit_rl) de tranh xung dot push.
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
SRC = ROOT / "pipeline" / "maporl_kernel.py"
TASK = os.environ.get("TASK", "gsm8k")
N_TRAIN = os.environ.get("N_TRAIN", "256")
K = os.environ.get("K", "32")
OUTER = os.environ.get("OUTER", "16")
E = os.environ.get("E", "3")
LR = os.environ.get("LR", "5e-5")
EPS = os.environ.get("EPS", "0.2")
BETA = os.environ.get("BETA", "0.04")
TEMP = os.environ.get("V_TEMP", "0.7")
SEED = os.environ.get("SEED", "42")
BS = os.environ.get("BS", "8")
MB = os.environ.get("MB", "4")
BETA_S = os.environ.get("BETA_S", "1.0")
BETA_V = os.environ.get("BETA_V", "1.0")
ACCOUNT = os.environ.get("ACCOUNT", "")
SLUG = os.environ.get("SLUG", "")               # override kernel slug
KDIR = ROOT / "kernels_maporl"
GSM_DS = "thedevastator/grade-school-math-8k-q-a"
MATH_DS = "angelirodriguez/hendrycks-math-dataset"
MATH_500_DS = "open-benchmarks/math-500-measuring-mathematical-problem-solving"

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
              .replace("__TASK__", repr(TASK))
              .replace("__N_TRAIN__", N_TRAIN).replace("__K__", K)
              .replace("__OUTER__", OUTER).replace("__E__", E)
              .replace("__LR__", LR)   # literal: 5e-5
              .replace("__EPS__", EPS)
              .replace("__BETA__", BETA)
              .replace("__TEMP__", TEMP)
              .replace("__SEED__", SEED).replace("__BS__", BS)
              .replace("__MB__", MB)
              .replace("__BETA_S__", BETA_S)
              .replace("__BETA_V__", BETA_V))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")
    datasets = (["xatri007/qwen2-5-1-5b-instruct", MATH_DS, MATH_500_DS]
                if TASK == "math" else
                ["xatri007/qwen2-5-1-5b-instruct", GSM_DS])
    suffix = "math" if TASK == "math" else "gsm8k"
    slug = os.environ.get("SLUG", f"maporl-cotrain-sva-{suffix}")
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / "train"
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{slug}"
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": slug, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         "enable_internet": True, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": datasets, "competition_sources": [], "kernel_sources": []}, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] task={TASK} n={N_TRAIN} k={K} outer={OUTER} e={E} lr={LR} eps={EPS} "
          f"beta={BETA} temp={TEMP} beta_s={BETA_S} beta_v={BETA_V} -> {user} "
          f"{'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    man = ROOT / "manifest_maporl.json"
    man.write_text(json.dumps([{"user": user, "token": token, "slug": slug,
                                "ref": ref, "task": TASK, "pushed": ok}], indent=2))

if __name__ == "__main__":
    main()