#!/usr/bin/env python3
"""Round 3: deploy the 8 P=1 coalitions with a 7B planner (others 1.5B) at N=300.
P=0 coalitions are reused from round 1 (identical all-1.5B config)."""
import os, re, json, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt"))
TEMPLATE = (ROOT / "pipeline" / "template_het.py").read_text()
ROUND = "r3"
KDIR = ROOT / f"kernels_{ROUND}"
N_EVAL = int(os.environ.get("N_EVAL", "300"))
DATASETS = ["xatri007/qwen2-5-1-5b-instruct",       # 1.5B (single-file safetensors)
            "ragnar123/qwen2-5-7b-instruct",        # 7B (sharded) -> planner
            "thedevastator/grade-school-math-8k-q-a"]

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
    src = (TEMPLATE.replace("__CONFIG_ID__", bits)
           .replace("__P__", str(p)).replace("__S__", str(s))
           .replace("__V__", str(v)).replace("__A__", str(a))
           .replace("__N_EVAL__", str(N_EVAL)))
    return bits, src

def main():
    accs = accounts()
    masks = [(1, s, v, a) for s in (0, 1) for v in (0, 1) for a in (0, 1)]   # 8 P=1 coalitions
    shutil.rmtree(KDIR, ignore_errors=True)
    KDIR.mkdir(parents=True)
    manifest = []
    for i, mask in enumerate(masks):
        user, token = accs[i]
        bits, src = render(mask)
        slug = f"shapley-gsm8k-{ROUND}-{bits}"
        d = KDIR / bits
        d.mkdir()
        (d / "kernel.py").write_text(src)
        meta = {"id": f"{user}/{slug}", "title": slug, "code_file": "kernel.py",
                "language": "python", "kernel_type": "script", "is_private": True,
                "enable_gpu": True, "enable_internet": False,
                "machine_shape": "NvidiaTeslaT4", "dataset_sources": DATASETS,
                "competition_sources": [], "kernel_sources": []}
        (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
        env = dict(os.environ, KAGGLE_API_TOKEN=token)
        r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                           env=env, capture_output=True, text=True)
        ok = "successfully pushed" in (r.stdout or "")
        manifest.append({"config_id": bits, "mask": list(mask), "user": user,
                         "token": token, "slug": slug, "ref": f"{user}/{slug}", "pushed": ok})
        print(f"[{i}] {bits} -> {user:22s} {'OK' if ok else 'FAIL'}", flush=True)
        time.sleep(2)
    (ROOT / f"manifest_{ROUND}.json").write_text(json.dumps(manifest, indent=2))
    print(f"deployed {sum(m['pushed'] for m in manifest)}/8 P=1 coalitions")

if __name__ == "__main__":
    main()
