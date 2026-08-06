#!/usr/bin/env python3
"""One synchronous pull pass for the pdeb round. Reads manifest_pdeb.json, checks each
kernel status and pulls terminal output into results_pdeb/. Safe to call repeatedly from
a wakeup (foreground; repo rule: never background poll loops)."""
import os, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUND = os.environ.get("ROUND", "pdeb")
RES = ROOT / f"results_{ROUND}"
RES.mkdir(exist_ok=True)
man = json.loads((ROOT / f"manifest_{ROUND}.json").read_text())

def st(ref, token):
    env = dict(os.environ, KAGGLE_API_TOKEN=token) if token else dict(os.environ)
    r = subprocess.run(["kaggle", "kernels", "status", ref],
                       env=env, capture_output=True, text=True)
    o = (r.stdout or "") + (r.stderr or "")
    return next((k for k in ("COMPLETE", "ERROR", "CANCEL", "RUNNING", "QUEUE") if k in o), "UNK")

def dst_dir(m):
    # Round 2 P=1 coalition: config_id = 4-bit mask, plan_mode=debate -> results_pdeb/1ssa_debate
    # Round 1 full pipeline (1111): plan_mode=single/sampling/debate -> results_pdeb/full_<mode>
    mode = m.get("plan_mode", "")
    cid = m["config_id"]
    if cid == "1111":
        return RES / f"full_{mode}"
    return RES / f"{cid}_{mode}"

remaining, errored = [], []
for m in man:
    ref = m["ref"]
    if not ref or not m.get("pushed"):
        errored.append(f"{m['slug']}:not-pushed")
        continue
    d = dst_dir(m)
    if (d / "summary.json").exists():
        continue
    s = st(ref, m.get("token") or "")
    if s in ("COMPLETE", "ERROR", "CANCEL"):
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run(["kaggle", "kernels", "output", ref, "-p", str(d)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=(m.get("token") or "")),
                       capture_output=True, text=True)
        got = (d / "summary.json").exists()
        print(f"  {m['slug']} {s} downloaded={got}")
        if not got or s != "COMPLETE":
            errored.append(m["slug"])
    else:
        remaining.append(m["slug"])

done = sum((dst_dir(m) / "summary.json").exists() for m in man if m.get("pushed"))
print(f"DONE {done}/{len([m for m in man if m.get('pushed')])}  "
      f"REMAINING {len(remaining)} {remaining}  ERRORED {errored}")
