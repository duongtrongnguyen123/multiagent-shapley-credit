#!/usr/bin/env python3
"""Deploy the 8 coalitions containing BIG_ROLE, upgrading that role to 7B.
Coalitions without BIG_ROLE are reused from round 1 (all-1.5B). Env: BIG (P/S/V/A),
ROUND, N_EVAL."""
import os, re, json, shutil, subprocess, time
from pathlib import Path

ROOT = Path("/Users/hduong/dev/qwen-gsm8k-kaggle/shapley")
ACCOUNTS = Path("/Users/hduong/dev/recurrent-research/accounts.txt")
TEMPLATE = (ROOT / "template_math_role7b.py").read_text()
ROLES = ["P", "S", "V", "A"]
BIG = os.environ["BIG"]
ROUND = os.environ.get("ROUND", "mV")
N_EVAL = int(os.environ.get("N_EVAL", "500"))
KDIR = ROOT / f"kernels_{ROUND}"
DATASETS = ["xatri007/qwen2-5-1-5b-instruct", "ragnar123/qwen2-5-7b-instruct",
            "open-benchmarks/math-500-measuring-mathematical-problem-solving"]

def accounts():
    out = []
    for line in ACCOUNTS.read_text().splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            parts = s.split()
            m = re.search(r"KGAT_[0-9a-f]+", parts[1]) if len(parts) > 1 else None
            if m:
                out.append((parts[0], m.group(0)))
    return out

def render(mask):
    bits = "".join(map(str, mask))
    src = TEMPLATE
    for ph, val in zip(("__P__", "__S__", "__V__", "__A__"), mask):
        src = src.replace(ph, str(val))
    return bits, (src.replace("__CONFIG_ID__", bits)
                  .replace("__N_EVAL__", str(N_EVAL)).replace("__BIG__", BIG))

def main():
    accs = accounts()
    bi = ROLES.index(BIG)
    masks = [m for m in [(p, s, v, a) for p in (0, 1) for s in (0, 1)
             for v in (0, 1) for a in (0, 1)] if m[bi] == 1]     # 8 with BIG active
    shutil.rmtree(KDIR, ignore_errors=True); KDIR.mkdir(parents=True)
    manifest = []
    for i, mask in enumerate(masks):
        user, token = accs[i]
        bits, src = render(mask)
        slug = f"shapley-math-{ROUND}-{bits}"
        d = KDIR / bits; d.mkdir()
        (d / "kernel.py").write_text(src)
        (d / "kernel-metadata.json").write_text(json.dumps(
            {"id": f"{user}/{slug}", "title": slug, "code_file": "kernel.py",
             "language": "python", "kernel_type": "script", "is_private": True,
             "enable_gpu": True, "enable_internet": False, "machine_shape": "NvidiaTeslaT4",
             "dataset_sources": DATASETS, "competition_sources": [], "kernel_sources": []}, indent=2))
        r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                           env=dict(os.environ, KAGGLE_API_TOKEN=token),
                           capture_output=True, text=True)
        ok = "successfully pushed" in (r.stdout or "")
        manifest.append({"config_id": bits, "mask": list(mask), "user": user,
                         "token": token, "slug": slug, "ref": f"{user}/{slug}", "pushed": ok})
        print(f"[{i}] {bits} BIG={BIG} -> {user:22s} {'OK' if ok else 'FAIL'}", flush=True)
        time.sleep(2)
    (ROOT / f"manifest_{ROUND}.json").write_text(json.dumps(manifest, indent=2))
    print(f"deployed {sum(m['pushed'] for m in manifest)}/8 (BIG={BIG}, {ROUND})")

if __name__ == "__main__":
    main()
