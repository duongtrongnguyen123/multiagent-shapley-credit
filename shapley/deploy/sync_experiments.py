#!/usr/bin/env python3
"""Sync pending experiment kernels. Checks status and pulls output if terminal.
Usage: python3 deploy/sync_experiments.py
"""
import os, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

KERNELS = [
    {"slug": "rc-m7-math", "user": "ziangtran123", "token": os.environ.get("KGAT_ZIANG", ""),
     "dest": ROOT / "results_rc_m7"},
    {"slug": "h24-cell4-math", "user": "nguyenminhoang", "token": os.environ.get("KGAT_NGUYEN", ""),
     "dest": ROOT / "results_h24_cell4"},
    {"slug": "disc-leakfix-gsm8k", "user": "giangleeeeeeeeeee", "token": os.environ.get("KGAT_GIANGLE", ""),
     "dest": ROOT / "results_disc_leakfix_gsm8k"},
    {"slug": "disc-leakfix-math", "user": "tranmihkhuyn", "token": os.environ.get("KGAT_TRAN", ""),
     "dest": ROOT / "results_disc_leakfix_math"},
    {"slug": "injected-classifier-math", "user": "jlosewilliam", "token": os.environ.get("KGAT_JLOSE", ""),
     "dest": ROOT / "results_injected_classifier"},
]

def st(ref, token):
    r = subprocess.run(["kaggle", "kernels", "status", ref],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    o = (r.stdout or "") + (r.stderr or "")
    for k in ("COMPLETE", "ERROR", "CANCEL", "RUNNING", "QUEUE"):
        if k in o:
            return k
    return "UNK"

remaining, errored, done = [], [], 0
for k in KERNELS:
    ref = f"{k['user']}/{k['slug']}"
    dest = k["dest"]
    dest.mkdir(exist_ok=True)
    if (dest / "summary.json").exists():
        done += 1
        print(f"  [{k['slug']}] ALREADY DOWNLOADED")
        continue
    s = st(ref, k["token"])
    if s in ("COMPLETE", "ERROR", "CANCEL"):
        subprocess.run(["kaggle", "kernels", "output", ref, "-p", str(dest)],
                       env=dict(os.environ, KAGGLE_API_TOKEN=k["token"]),
                       capture_output=True, text=True)
        got = (dest / "summary.json").exists()
        print(f"  [{k['slug']}] {s} downloaded={got}")
        if not got or s != "COMPLETE":
            errored.append(k["slug"])
        else:
            done += 1
    else:
        remaining.append(k["slug"])
        print(f"  [{k['slug']}] {s}")

print(f"\nDONE {done}/{len(KERNELS)}  REMAINING {len(remaining)} {remaining}  ERRORED {errored}")
