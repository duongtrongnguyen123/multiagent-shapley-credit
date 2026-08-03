#!/usr/bin/env python3
"""Render 16 role-coalition kernels and deploy one per Kaggle account."""
import os, re, json, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt"))
TEMPLATE = (ROOT / "pipeline" / "template_math.py").read_text()
ROUND = os.environ.get("ROUND", "m1")
KDIR = ROOT / f"kernels_{ROUND}"
N_EVAL = int(os.environ.get("N_EVAL", "500"))
DATASETS = ["xatri007/qwen2-5-1-5b-instruct",
            "open-benchmarks/math-500-measuring-mathematical-problem-solving"]

def accounts():
    out = []
    for line in ACCOUNTS.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        m = re.search(r"KGAT_[0-9a-f]+", parts[1]) if len(parts) > 1 else None
        if m:
            out.append((parts[0], m.group(0)))
    return out

def render(mask):
    p, s, v, a = mask
    bits = f"{p}{s}{v}{a}"
    src = (TEMPLATE
           .replace("__CONFIG_ID__", bits)
           .replace("__P__", str(p)).replace("__S__", str(s))
           .replace("__V__", str(v)).replace("__A__", str(a))
           .replace("__N_EVAL__", str(N_EVAL)))
    return bits, src

def main():
    accs = accounts()
    masks = [(p, s, v, a) for p in (0, 1) for s in (0, 1)
             for v in (0, 1) for a in (0, 1)]          # 16 coalitions
    assert accs, "cần ít nhất 1 tài khoản trong accounts.txt (1 key cũng chạy được, tuần tự)"
    shutil.rmtree(KDIR, ignore_errors=True)
    KDIR.mkdir(parents=True)
    manifest = []
    for i, mask in enumerate(masks):
        user, token = accs[i % len(accs)]
        bits, src = render(mask)
        slug = f"shapley-math-{ROUND}-{bits}"
        d = KDIR / bits
        d.mkdir()
        (d / "kernel.py").write_text(src)
        meta = {"id": f"{user}/{slug}", "title": slug, "code_file": "kernel.py",
                "language": "python", "kernel_type": "script", "is_private": True,
                "enable_gpu": True, "enable_internet": False,
                "machine_shape": "NvidiaTeslaT4",
                "dataset_sources": DATASETS, "competition_sources": [],
                "kernel_sources": []}
        (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
        rec = {"config_id": bits, "mask": list(mask), "user": user,
               "token": token, "slug": slug, "ref": f"{user}/{slug}"}
        env = dict(os.environ, KAGGLE_API_TOKEN=token)
        r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                           env=env, capture_output=True, text=True)
        ok = "successfully pushed" in (r.stdout or "")
        rec["pushed"] = ok
        print(f"[{i:2d}] {bits} -> {user:22s} {'OK' if ok else 'FAIL'} "
              f"{(r.stdout or r.stderr).strip().splitlines()[-1][:80]}", flush=True)
        manifest.append(rec)
        time.sleep(2)
    (ROOT / f"manifest_{ROUND}.json").write_text(json.dumps(manifest, indent=2))
    npush = sum(m["pushed"] for m in manifest)
    print(f"\n=== deployed {npush}/16 coalitions; manifest.json written ===")

if __name__ == "__main__":
    main()
