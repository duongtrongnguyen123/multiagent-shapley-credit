#!/usr/bin/env python3
"""H40 (dang ky truoc #46): chia MATH-500 thanh NSHARD kernel Kaggle chay song song.

Moi kernel: 2x T4, MOI GPU mot ban sao model (1.5B fp16, 7B nf4) -> data parallel that su.
Kernel chi SINH du lieu tho; tong hop lam o local bang merge_h40.py tren ca 500 bai.
Moi tai khoan chay toi da 2 notebook cung luc -> NSHARD <= 2 * so tai khoan.
"""
import os, sys, json, shutil, subprocess, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from accounts import t4_pool

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "pipeline" / "mbpp_select_kernel.py").read_text()
NSHARD = int(os.environ.get("NSHARD", "20"))
ROUND = os.environ.get("ROUND", "h56")
KDIR = ROOT / f"kernels_{ROUND}"
MAX_PER_ACCOUNT = 2

DATASETS = ["xatri007/qwen2-5-1-5b-instruct",
            "ragnar123/qwen2-5-7b-instruct",
            "mpwolke/mbppjsonl"]

def main():
    accs = t4_pool()
    cap = len(accs) * MAX_PER_ACCOUNT
    if NSHARD > cap:
        sys.exit(f"NSHARD={NSHARD} vuot suc chua: {len(accs)} tai khoan x {MAX_PER_ACCOUNT} = {cap}")
    print(f"{NSHARD} shard tren {len(accs)} tai khoan (toi da {MAX_PER_ACCOUNT}/tai khoan)", flush=True)

    shutil.rmtree(KDIR, ignore_errors=True)
    KDIR.mkdir(parents=True)
    manifest, used = [], {}
    for s in range(NSHARD):
        user, token = accs[s % len(accs)]
        used[user] = used.get(user, 0) + 1
        if used[user] > MAX_PER_ACCOUNT:
            sys.exit(f"loi phan bo: {user} vuot {MAX_PER_ACCOUNT}")
        src = (TEMPLATE.replace("@@SHARD@@", str(s)).replace("@@NSHARD@@", str(NSHARD))
                .replace("@@RUN@@", "H56").replace("@@TIDLO@@", "11").replace("@@TIDHI@@", "510"))
        slug = f"candidate-selection-shard-{s:02d}"
        d = KDIR / f"s{s:02d}"
        d.mkdir()
        (d / "kernel.py").write_text(src)
        meta = {"id": f"{user}/{slug}", "title": slug, "code_file": "kernel.py",
                "language": "python", "kernel_type": "script", "is_private": True,
                "enable_gpu": True, "enable_internet": True,
                "machine_shape": "NvidiaTeslaT4",
                "dataset_sources": DATASETS, "competition_sources": [], "kernel_sources": []}
        (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
        env = dict(os.environ, KAGGLE_API_TOKEN=token)
        r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                           env=env, capture_output=True, text=True)
        ok = "successfully pushed" in (r.stdout or "")
        if not ok and "internet" in ((r.stdout or "") + (r.stderr or "")).lower():
            meta["enable_internet"] = False        # lui ve: se chay fp16 thay vi nf4
            (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
            r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                               env=env, capture_output=True, text=True)
            ok = "successfully pushed" in (r.stdout or "")
            if ok: print(f"     (shard {s}: internet bi tu choi -> day lai voi internet TAT)", flush=True)
        last = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        print(f"[{s:2d}/{NSHARD}] {user:22s} {'OK  ' if ok else 'FAIL'} {last[-1][:90] if last else ''}", flush=True)
        manifest.append({"shard": s, "user": user, "token": token,
                         "slug": slug, "ref": f"{user}/{slug}", "pushed": ok})
        time.sleep(2)
    (ROOT / f"manifest_{ROUND}.json").write_text(json.dumps(manifest, indent=2))
    nok = sum(1 for m in manifest if m["pushed"])
    print(f"\nday thanh cong {nok}/{NSHARD}. manifest_{ROUND}.json (CHUA TOKEN — khong commit)")

if __name__ == "__main__":
    main()
