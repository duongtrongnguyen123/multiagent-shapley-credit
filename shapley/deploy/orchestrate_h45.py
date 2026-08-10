#!/usr/bin/env python3
"""H45 (dang ky truoc #51): luoi 4 o (tac vu x co model) x 5 shard = 20 kernel.
Moi kernel chi mount DUNG model va dataset can dung -> glob khong nhap nhang."""
import os, sys, json, shutil, subprocess, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from accounts import t4_pool

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "pipeline" / "seq_grid_kernel.py").read_text()
NSHARD = int(os.environ.get("NSHARD", "5"))
ROUND = os.environ.get("ROUND", "h45")
KDIR = ROOT / f"kernels_{ROUND}"
MAX_PER_ACCOUNT = 2

M15 = "xatri007/qwen2-5-1-5b-instruct"
M7  = "ragnar123/qwen2-5-7b-instruct"
DS  = {"gsm8k": "thedevastator/grade-school-math-8k-q-a",
       "math":  "open-benchmarks/math-500-measuring-mathematical-problem-solving"}
CELLS = [(t, s) for t in ("gsm8k", "math") for s in ("15", "7")]

def main():
    accs = t4_pool()
    jobs = [(t, s, sh) for (t, s) in CELLS for sh in range(NSHARD)]
    if len(jobs) > len(accs) * MAX_PER_ACCOUNT:
        sys.exit(f"{len(jobs)} kernel vuot {len(accs)}x{MAX_PER_ACCOUNT}")
    print(f"{len(jobs)} kernel = {len(CELLS)} o x {NSHARD} shard", flush=True)
    shutil.rmtree(KDIR, ignore_errors=True); KDIR.mkdir(parents=True)
    manifest, used = [], {}
    for n, (task, size, sh) in enumerate(jobs):
        user, token = accs[n % len(accs)]
        used[user] = used.get(user, 0) + 1
        if used[user] > MAX_PER_ACCOUNT: sys.exit(f"{user} vuot han muc")
        src = (TEMPLATE.replace("@@SHARD@@", str(sh)).replace("@@NSHARD@@", str(NSHARD))
                       .replace("@@TASK@@", task).replace("@@SIZE@@", size))
        slug = f"reasoning-depth-{task}-{size}b-{sh}"
        d = KDIR / f"{task}{size}s{sh}"; d.mkdir()
        (d / "kernel.py").write_text(src)
        meta = {"id": f"{user}/{slug}", "title": slug, "code_file": "kernel.py",
                "language": "python", "kernel_type": "script", "is_private": True,
                "enable_gpu": True, "enable_internet": True,
                "machine_shape": "NvidiaTeslaT4",
                "dataset_sources": [M15 if size == "15" else M7, DS[task]],
                "competition_sources": [], "kernel_sources": []}
        (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
        env = dict(os.environ, KAGGLE_API_TOKEN=token)
        r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                           env=env, capture_output=True, text=True)
        ok = "successfully pushed" in (r.stdout or "")
        last = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        print(f"[{n:2d}] {task:5s} {size:2s}B s{sh} {user:20s} {'OK  ' if ok else 'FAIL'} "
              f"{last[-1][:70] if last else ''}", flush=True)
        manifest.append({"shard": n, "cell": f"{task}-{size}", "task": task, "size": size,
                         "sub": sh, "user": user, "token": token, "slug": slug,
                         "ref": f"{user}/{slug}", "pushed": ok})
        time.sleep(2)
    (ROOT / f"manifest_{ROUND}.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nday thanh cong {sum(1 for m in manifest if m['pushed'])}/{len(jobs)}")

if __name__ == "__main__":
    main()
