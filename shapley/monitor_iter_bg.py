#!/usr/bin/env python3
# Monitor NỀN cho 4 kernel iterative (K=2,3 x {1.5B,7B}). Poll 5', exit khi cả 4 final.
import json, os, subprocess, time, sys
ROOT=os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT)
JOBS=["iter_m15_r2","iter_m15_r3","iter_m7_r2","iter_m7_r3"]
LOG=open("monitor_iter.log","a")
def say(m): LOG.write(m+"\n"); LOG.flush(); print(m,flush=True)
def check(j):
    d=f"kernels_{j}"; meta=json.load(open(f"{d}/meta.json")); env=dict(os.environ,KAGGLE_API_TOKEN=meta["token"])
    o=subprocess.run(["kaggle","kernels","status",meta["ref"]],env=env,capture_output=True,text=True)
    s=(o.stdout or "")+(o.stderr or "")
    if "COMPLETE" in s:
        subprocess.run(["kaggle","kernels","output",meta["ref"],"-p",f"res_{j}"],env=env,capture_output=True,text=True)
        try: return ("DONE",json.load(open(f"res_{j}/summary.json")))
        except Exception: return ("DONE",None)
    return ("ERR",None) if "ERROR" in s else ("RUN",None)
for it in range(48):
    res={}; nf=0
    for j in JOBS:
        try: res[j]=check(j)
        except Exception: res[j]=("RUN",None)
        if res[j][0] in ("DONE","ERR"): nf+=1
    say(f"[iter {it} | {nf}/4] "+" ".join(f"{j}:{res[j][0]}"+(f"={res[j][1]['acc']}" if res[j][1] else "") for j in JOBS))
    if nf==4:
        json.dump({j:{"status":res[j][0],"summary":res[j][1]} for j in JOBS},open("monitor_iter_result.json","w"),indent=2)
        say("ALL 4 FINAL -> exit"); sys.exit(0)
    time.sleep(300)
json.dump({j:{"status":res[j][0],"summary":res[j][1]} for j in JOBS},open("monitor_iter_result.json","w"),indent=2)
say("TIMEOUT -> exit"); sys.exit(1)
