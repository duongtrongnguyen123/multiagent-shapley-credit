#!/usr/bin/env python3
"""Deploy credit-rl EVAL MATH kernel (MATH-500 test, 5-fold).

  ACCOUNT=Viettran12 ROLE=V    python deploy/orchestrate_credit_rl_eval_math.py
  ACCOUNT=Viettran12 ROLE=PSVA python deploy/orchestrate_credit_rl_eval_math.py

ROLE="V"   -> mount 1 adapter V (base vs trained V-COND), pipeline P->S->V.
ROLE="PSVA"-> mount 3 adapter S,V,A (P base), pipeline P->S->V->A với S,V,A trained.
Prompts MATH-native (boxed).
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
SRC = ROOT / "pipeline" / "credit_rl_eval_math_kernel.py"
ROLE = os.environ.get("ROLE", "V").upper()
N = int(os.environ.get("N", "200"))
NF = int(os.environ.get("NF", "5"))
BS = int(os.environ.get("BS", "4"))
ADAPTER_DS = os.environ.get("ADAPTER_DS", "Viettran12/credit-rl-vcond-adapter")
ADAPTER_S = os.environ.get("ADAPTER_S", "")     # override S adapter trong PSVA
ADAPTER_V = os.environ.get("ADAPTER_V", "")     # override V adapter trong PSVA
ADAPTER_A = os.environ.get("ADAPTER_A", "")     # override A adapter trong PSVA (vd: asel)
SLUG = os.environ.get("SLUG", "")
ACCOUNT = os.environ.get("ACCOUNT", "")
KDIR = ROOT / "kernels_credit_rl_eval_math"
MODEL_DS = "xatri007/qwen2-5-1-5b-instruct"
MATH_DS = "open-benchmarks/math-500-measuring-mathematical-problem-solving"
ROLE_DATASETS = {
    "S": "truongdinhduc06/credit-rl-s-adapter",
    "V": "Viettran12/credit-rl-v-adapter",
    "A": "TrgDinKai/credit-rl-a-adapter",
}


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
    if ROLE not in ("V", "PSVA"):
        raise SystemExit(f"ROLE={ROLE} invalid (V|PSVA)")
    if ROLE == "PSVA":
        ds = [ROLE_DATASETS["S"], ROLE_DATASETS["V"], ROLE_DATASETS["A"]]
        if ADAPTER_S: ds[0] = ADAPTER_S
        if ADAPTER_V: ds[1] = ADAPTER_V
        if ADAPTER_A: ds[2] = ADAPTER_A
        datasets = [MODEL_DS, MATH_DS] + ds
    else:
        datasets = [MODEL_DS, MATH_DS, ADAPTER_DS]
    src = (SRC.read_text(encoding="utf-8")
              .replace("__ROLE__", repr(ROLE))
              .replace("__N__", str(N))
              .replace("__NF__", str(NF)).replace("__BS__", str(BS)))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")
    slug = SLUG or (f"credit-rl-eval-psva-math" if ROLE == "PSVA"
                    else "credit-rl-eval-vcond-math")
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / "eval"
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
    print(f"[{slug}] ROLE={ROLE} N={N} NF={NF} adapters={datasets[2:]} -> {user} "
          f"{'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    (ROOT / "manifest_credit_rl_eval_math.json").write_text(json.dumps(
        [{"user": user, "token": token, "slug": slug, "ref": ref, "role": ROLE,
          "adapters": datasets[2:], "pushed": ok}], indent=2))


if __name__ == "__main__":
    main()