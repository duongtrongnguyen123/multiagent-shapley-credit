#!/usr/bin/env python3
"""Deploy the credit-sharing RL (Shapley marginal / GRPO) training kernel.

  ACCOUNT=tbmdemi python deploy/orchestrate_credit_rl.py

Trains the VERIFIER role (V) with LoRA on the GSM8K train split. Reward per V
trace = Shapley marginal m = v(S|V) - v(S) over the 8 coalitions containing V,
grouped per question (GRPO advantage). P/S/A stay base model.
Internet is enabled (peft installed at runtime).
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
SRC = ROOT / "pipeline" / "credit_rl_kernel.py"
ROLE = os.environ.get("ROLE", "V")
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
MAXLEN = os.environ.get("MAXLEN", "2048")
ONLY_VERIFY = os.environ.get("ONLY_VERIFY", "0")
ACCOUNT = os.environ.get("ACCOUNT", "")
KDIR = ROOT / "kernels_credit_rl"
DATASETS = ["xatri007/qwen2-5-1-5b-instruct", "thedevastator/grade-school-math-8k-q-a"]

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
              .replace("__ROLE__", repr(ROLE))
              .replace("__N_TRAIN__", N_TRAIN).replace("__K__", K)
              .replace("__OUTER__", OUTER).replace("__E__", E)
              .replace("__LR__", LR)   # literal thô: 5e-5 (không phải repr -> string)
              .replace("__EPS__", EPS)
              .replace("__BETA__", BETA)
              .replace("__TEMP__", TEMP)  # literal thô: 0.7
              .replace("__SEED__", SEED).replace("__BS__", BS)
              .replace("__MB__", MB).replace("__MAXLEN__", MAXLEN)
              .replace("__ONLY_VERIFY__", ONLY_VERIFY))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")
    slug = f"credit-rl-{ROLE.lower()}-gsm8k"
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / "train"
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{slug}"
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": slug, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         # peft cài lúc chạy -> cần internet
         "enable_internet": True, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": DATASETS, "competition_sources": [], "kernel_sources": []}, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] n={N_TRAIN} k={K} outer={OUTER} e={E} lr={LR} eps={EPS} "
          f"beta={BETA} temp={TEMP} only_verify={ONLY_VERIFY} -> {user} "
          f"{'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    man = ROOT / "manifest_credit_rl.json"
    man.write_text(json.dumps([{"user": user, "token": token, "slug": slug,
                                "ref": ref, "pushed": ok}], indent=2))

if __name__ == "__main__":
    main()
