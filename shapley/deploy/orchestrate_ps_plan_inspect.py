#!/usr/bin/env python3
"""Deploy ps_plan_inspect_kernel (so sanh plan Planner base vs trained pminlen)."""
import os, re, json, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt")).expanduser()
SRC = ROOT / "pipeline" / "ps_plan_inspect_kernel.py"
N = os.environ.get("N", "20")
BS = os.environ.get("BS", "4")
ACCOUNT = os.environ.get("ACCOUNT", "tbmdemi")
SLUG = os.environ.get("SLUG", "credit-rl-plan-inspect-gsm8k")
KDIR = ROOT / "kernels_ps_plan_inspect"
MODEL_DS = "xatri007/qwen2-5-1-5b-instruct"
GSM_DS = "thedevastator/grade-school-math-8k-q-a"
ADAPTER_DS = os.environ.get("ADAPTER_DS", "tbmdemi/credit-rl-pminlen-adapter")

def accounts():
    out = []
    for line in ACCOUNTS.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        m = re.search(r"KGAT_[0-9a-f]+", parts[1]) if len(parts) > 1 else None
        if m:
            out.append((parts[0], m.group(0)))
    return out

def main():
    accs = accounts()
    hit = [(u, t) for u, t in accs if u.lower() == ACCOUNT.lower()]
    if not hit:
        raise SystemExit(f"ACCOUNT={ACCOUNT} not found")
    user, token = hit[0]
    src = (SRC.read_text(encoding="utf-8")
              .replace("__N__", str(N)).replace("__BS__", str(BS)))
    left = re.findall(r"__[A-Z_]+__", src)
    if left:
        raise SystemExit(f"unreplaced placeholders: {left}")
    compile(src, "<kernel>", "exec")
    shutil.rmtree(KDIR, ignore_errors=True)
    d = KDIR / "inspect"
    d.mkdir(parents=True)
    (d / "kernel.py").write_text(src, encoding="utf-8")
    ref = f"{user}/{SLUG}"
    (d / "kernel-metadata.json").write_text(json.dumps(
        {"id": ref, "title": SLUG, "code_file": "kernel.py", "language": "python",
         "kernel_type": "script", "is_private": True, "enable_gpu": True,
         "enable_internet": True, "machine_shape": "NvidiaTeslaT4",
         "dataset_sources": [MODEL_DS, GSM_DS, ADAPTER_DS],
         "competition_sources": [], "kernel_sources": []}, indent=2))
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{SLUG}] N={N} BS={BS} adapter={ADAPTER_DS} -> {user} "
          f"{'OK' if ok else 'FAIL'} "
          f"{(r.stdout or r.stderr).strip().splitlines()[-1][:70]}", flush=True)

if __name__ == "__main__":
    main()