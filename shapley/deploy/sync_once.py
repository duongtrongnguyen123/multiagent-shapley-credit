#!/usr/bin/env python3
"""One synchronous pass: for each coalition not yet downloaded, check status and
pull output if terminal. Prints REMAINING <n> <list>. Safe to call from a wakeup
(runs to completion within the turn, unlike a background poll loop)."""
import os, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUND = os.environ.get("ROUND", "r2")
RES = ROOT / (f"results_{ROUND}" if ROUND != "r1" else "results")
RES.mkdir(exist_ok=True)
man = json.loads((ROOT / f"manifest_{ROUND}.json").read_text())

def st(ref, token):
    r = subprocess.run(["kaggle", "kernels", "status", ref],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    o = (r.stdout or "") + (r.stderr or "")
    return next((k for k in ("COMPLETE", "ERROR", "CANCEL", "RUNNING", "QUEUE") if k in o), "UNK")

remaining, errored = [], []
for m in man:
    cid = m["config_id"]
    if (RES / cid / "summary.json").exists():
        continue
    s = st(m["ref"], m["token"])
    if s in ("COMPLETE", "ERROR", "CANCEL"):
        (RES / cid).mkdir(exist_ok=True)
        subprocess.run(["kaggle", "kernels", "output", m["ref"], "-p", str(RES / cid)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=m["token"]),
                       capture_output=True, text=True)
        got = (RES / cid / "summary.json").exists()
        print(f"  {cid} {s} downloaded={got}")
        if not got or s != "COMPLETE":
            errored.append(cid)
    else:
        remaining.append(cid)

done = sum((RES / m["config_id"] / "summary.json").exists() for m in man)
print(f"DONE {done}/16  REMAINING {len(remaining)} {remaining}  ERRORED {errored}")
