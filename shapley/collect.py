#!/usr/bin/env python3
"""Poll all 16 coalition kernels (each with its own account token), download
summary.json on completion. Exits when every kernel is terminal."""
import os, json, subprocess, sys, time
from pathlib import Path

ROOT = Path("/Users/hduong/dev/qwen-gsm8k-kaggle/shapley")
ROUND = os.environ.get("ROUND", "r1")
RES = ROOT / (f"results_{ROUND}" if ROUND != "r1" else "results")
RES.mkdir(exist_ok=True)
manifest = json.loads((ROOT / f"manifest_{ROUND}.json").read_text())

def status(ref, token):
    r = subprocess.run(["kaggle", "kernels", "status", ref],
                       env=dict(os.environ, KAGGLE_API_TOKEN=token),
                       capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    for key in ("COMPLETE", "ERROR", "CANCEL", "RUNNING", "QUEUE"):
        if key in out:
            return key
    return "UNKNOWN"

def pull(ref, token, cid):
    d = RES / cid
    d.mkdir(exist_ok=True)
    subprocess.run(["kaggle", "kernels", "output", ref, "-p", str(d)],
                   env=dict(os.environ, KAGGLE_API_TOKEN=token),
                   capture_output=True, text=True)

done, INTERVAL = {}, 60
while len(done) < len(manifest):
    for m in manifest:
        cid = m["config_id"]
        if cid in done:
            continue
        st = status(m["ref"], m["token"])
        if st in ("COMPLETE", "ERROR", "CANCEL"):
            pull(m["ref"], m["token"], cid)
            sm = RES / cid / "summary.json"
            acc = json.loads(sm.read_text())["accuracy"] if sm.exists() else None
            done[cid] = (st, acc)
            print(f"{time.strftime('%H:%M:%S')} {cid} {st} acc={acc}", flush=True)
    remaining = [m["config_id"] for m in manifest if m["config_id"] not in done]
    print(f"{time.strftime('%H:%M:%S')} done={len(done)}/16 remaining={remaining}", flush=True)
    if len(done) < len(manifest):
        time.sleep(INTERVAL)

(ROOT / f"collect_done_{ROUND}.json").write_text(json.dumps(done, indent=2))
print("ALL TERMINAL", json.dumps(done), flush=True)
