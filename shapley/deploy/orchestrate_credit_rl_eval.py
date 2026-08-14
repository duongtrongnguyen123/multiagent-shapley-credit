#!/usr/bin/env python3
"""Deploy credit-rl EVAL kernel (trained adapter vs base, GSM8K test, 5-fold).

  ROLE=V  N=200 NF=5 ACCOUNT=Viettran12 python deploy/orchestrate_credit_rl_eval.py
  ROLE=FULL ACCOUNT=Viettran12 python deploy/orchestrate_credit_rl_eval.py

ROLE="P"|"S"|"V"|"A"  -> kernel mount đúng 1 adapter của role đó.
ROLE="FULL"           -> kernel mount CẢ 4 adapter (đánh giá pipeline sau khi train 4 vai).
"""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
SRC = ROOT / "pipeline" / "credit_rl_eval_kernel.py"
ROLE = os.environ.get("ROLE", "V").upper()
N = int(os.environ.get("N", "200"))
NF = int(os.environ.get("NF", "5"))
BS = int(os.environ.get("BS", "4"))
ACCOUNT = os.environ.get("ACCOUNT", "")
KDIR = ROOT / "kernels_credit_rl_eval"
MODEL_DS = "xatri007/qwen2-5-1-5b-instruct"
GSM_DS = "thedevastator/grade-school-math-8k-q-a"

# adapter dataset của từng vai (đã upload bằng upload_credit_rl_adapters.py)
ROLE_DATASETS = {
    "P": "tbmdemi/credit-rl-p-adapter",
    "S": "truongdinhduc06/credit-rl-s-adapter",
    "V": "Viettran12/credit-rl-v-adapter",
    "A": "TrgDinKai/credit-rl-a-adapter",
}
FULL_DATASETS = list(ROLE_DATASETS.values())

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
    if ROLE not in (*ROLE_DATASETS, "FULL"):
        raise SystemExit(f"ROLE={ROLE} invalid (P|S|V|A|FULL)")
    datasets = [MODEL_DS, GSM_DS] + (FULL_DATASETS if ROLE == "FULL"
                                     else [ROLE_DATASETS[ROLE]])
    src = (SRC.read_text(encoding="utf-8")
              .replace("__ROLE__", repr(ROLE)).replace("__N__", str(N))
              .replace("__NF__", str(NF)).replace("__BS__", str(BS)))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")
    slug = f"credit-rl-eval-{ROLE.lower()}-gsm8k"
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / "eval"
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{slug}"
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": slug, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         # peft phải cài lúc chạy để nạp adapter
         "enable_internet": True, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": datasets, "competition_sources": [], "kernel_sources": []}, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] ROLE={ROLE} N={N} NF={NF} adapters={datasets[2:]} -> {user} "
          f"{'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)
    (ROOT / "manifest_credit_rl_eval.json").write_text(json.dumps(
        [{"user": user, "token": token, "slug": slug, "ref": ref, "role": ROLE,
          "pushed": ok}], indent=2))

if __name__ == "__main__":
    main()
