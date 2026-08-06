#!/usr/bin/env python3
"""Deploy the debate-planner experiment on MATH-500 (round pdeb).

Round 1 (default): 3 kernels, full pipeline PSVA, N=N_EVAL, one per planner mode:
  single   - baseline (1 greedy plan)
  sampling - 3 sampled plans -> judge (no critique)   [control for sampling effect]
  debate   - 3 sampled plans -> cross-critique -> self-rewrite -> judge

Round 2 (--coalitions): 8 kernels P=1 with PLAN_MODE=debate, rest 1.5B greedy.
  Masks: 1ssa where the planner is the debate-3 ensemble. Saved under results_pdeb/.
Env: ROUND (default pdeb), N_EVAL (default 500), KDIR base, ACCOUNTS_FILE (optional).
Uses one Kaggle OAuth identity (credentials.json), round-robin over accounts.txt if present.
"""
import os, re, json, shutil, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTS = Path(os.environ.get("ACCOUNTS_FILE", ROOT / "accounts.txt"))
TEMPLATE = (ROOT / "pipeline" / "template_debate_math.py").read_text()
ROUND = os.environ.get("ROUND", "pdeb")
N_EVAL = int(os.environ.get("N_EVAL", "500"))
KDIR = ROOT / f"kernels_{ROUND}"
DATASETS = ["xatri007/qwen2-5-1-5b-instruct",
            "open-benchmarks/math-500-measuring-mathematical-problem-solving"]

MODES = ["single", "sampling", "debate"]
P1_MASKS = [(1, s, v, a) for s in (0, 1) for v in (0, 1) for a in (0, 1)]  # 8 coalition round 2

def accounts():
    out = []
    if not ACCOUNTS.exists():
        return out
    for line in ACCOUNTS.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        m = re.search(r"KGAT_[0-9a-f]+", parts[1]) if len(parts) > 1 else None
        if m:
            out.append((parts[0], m.group(0)))
    return out

def oauth_username():
    """Fall back to the OAuth identity in ~/.kaggle/credentials.json when no accounts.txt."""
    try:
        import json as _json
        d = _json.loads((Path.home() / ".kaggle" / "credentials.json").read_text())
        return d.get("username", "")
    except Exception:
        return ""

def render(mask, plan_mode):
    bits = f"{mask[0]}{mask[1]}{mask[2]}{mask[3]}"
    src = (TEMPLATE
           .replace("__CONFIG_ID__", bits)
           .replace("__P__", str(mask[0])).replace("__S__", str(mask[1]))
           .replace("__V__", str(mask[2])).replace("__A__", str(mask[3]))
           .replace("__N_EVAL__", str(N_EVAL))
           .replace("__PLAN_MODE__", plan_mode))
    return bits, src

def push(user, token, d, bits, plan_mode):
    slug = f"shapley-pdeb-{bits}-{plan_mode}" if plan_mode != "single" else f"shapley-pdeb-{bits}"
    ref = f"{user}/{slug}" if user else slug
    meta = {"id": ref, "title": slug, "code_file": "kernel.py",
            "language": "python", "kernel_type": "script", "is_private": True,
            "enable_gpu": True, "enable_internet": False,
            "machine_shape": "NvidiaTeslaT4",
            "dataset_sources": DATASETS, "competition_sources": [], "kernel_sources": []}
    (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    env = dict(os.environ, KAGGLE_API_TOKEN=token) if token else dict(os.environ)
    r = subprocess.run(["kaggle", "kernels", "push", "-p", str(d)],
                       env=env, capture_output=True, text=True)
    ok = "successfully pushed" in (r.stdout or "")
    print(f"[{slug}] PLAN_MODE={plan_mode} mask={bits} -> {user or 'oauth':20s} "
          f"{'OK' if ok else 'FAIL'} {(r.stdout or r.stderr).strip().splitlines()[-1][:70]}",
          flush=True)
    return {"config_id": bits, "plan_mode": plan_mode, "user": user, "token": token,
            "slug": slug, "ref": ref, "pushed": ok}

def main():
    import sys
    coalitions = "--coalitions" in sys.argv
    # --modes single,sampling  -> only push those modes (round 1); default all 3.
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--modes="):
            only = a.split("=", 1)[1].split(",")
    accs = accounts()
    # One identity: use accounts.txt first account if present, else the OAuth username.
    user, token = (accs[0][0], accs[0][1]) if accs else (oauth_username(), "")
    # Preserve previously pushed entries (e.g. 'single' from an earlier run).
    man_file = ROOT / f"manifest_{ROUND}.json"
    manifest = json.loads(man_file.read_text()) if man_file.exists() else []
    manifest = [m for m in manifest if m.get("plan_mode") != "debate" or m["config_id"] == "1111"]
    KDIR.mkdir(parents=True, exist_ok=True)
    if coalitions:
        for mask in P1_MASKS:
            bits, src = render(mask, "debate")
            d = KDIR / f"p1_{bits}"; d.mkdir(exist_ok=True)
            (d / "kernel.py").write_text(src)
            manifest.append(push(user, token, d, bits, "debate"))
            time.sleep(2)
    else:
        modes = only if only else MODES
        for mode in modes:
            bits, src = render((1, 1, 1, 1), mode)
            d = KDIR / mode; d.mkdir(exist_ok=True)
            (d / "kernel.py").write_text(src)
            manifest.append(push(user, token, d, bits, mode))
            time.sleep(2)
    man_file.write_text(json.dumps(manifest, indent=2))
    npush = sum(m["pushed"] for m in manifest)
    print(f"\n=== deployed {npush}/{len(manifest)} total ({ROUND}, round2={coalitions}); "
          f"manifest_{ROUND}.json written ===")

if __name__ == "__main__":
    main()
