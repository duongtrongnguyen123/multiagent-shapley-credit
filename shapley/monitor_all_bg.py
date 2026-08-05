#!/usr/bin/env python3
"""Monitor MỌI kernel đang chạy (tự dò từ kernels_*/meta.json). Poll 5', thoát khi hết RUNNING."""
import json, os, subprocess, time, sys, glob
ROOT=os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT)
WATCH=sys.argv[1].split(",") if len(sys.argv)>1 else []
LOG=open("monitor_all.log","a")
def say(m): LOG.write(m+"\n"); LOG.flush(); print(m,flush=True)
def check(j):
    d=f"kernels_{j}"
    meta=json.load(open(f"{d}/meta.json")); env=dict(os.environ,KAGGLE_API_TOKEN=meta["token"])
    o=subprocess.run(["kaggle","kernels","status",meta["ref"]],env=env,capture_output=True,text=True)
    s=(o.stdout or "")+(o.stderr or "")
    if "COMPLETE" in s:
        subprocess.run(["kaggle","kernels","output",meta["ref"],"-p",f"res_{j}"],env=env,capture_output=True,text=True)
        try: return ("DONE",json.load(open(f"res_{j}/summary.json")))
        except Exception: return ("DONE",None)
    return ("ERR",None) if "ERROR" in s else ("RUN",None)
res={}
for it in range(60):
    res={}; nf=0
    for j in WATCH:
        try: res[j]=check(j)
        except Exception: res[j]=("RUN",None)
        if res[j][0] in ("DONE","ERR"): nf+=1
    say(f"[{it}|{nf}/{len(WATCH)}] "+" ".join(f"{j}:{res[j][0]}" for j in WATCH))
    if nf==len(WATCH):
        json.dump({j:{"status":res[j][0],"summary":res[j][1]} for j in WATCH},
                  open("monitor_all_result.json","w"),indent=2)
        say("ALL DONE"); sys.exit(0)
    time.sleep(300)
json.dump({j:{"status":res[j][0],"summary":res[j][1]} for j in WATCH},open("monitor_all_result.json","w"),indent=2)
say("TIMEOUT"); sys.exit(1)
