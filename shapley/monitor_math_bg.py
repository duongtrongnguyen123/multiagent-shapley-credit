#!/usr/bin/env python3
# Monitor NỀN: poll 10 kernel MATH mỗi 5 phút, THOÁT khi tất cả xong (COMPLETE/ERROR).
# Chạy: run_in_background -> khi process exit, harness tự báo. Ghi log + kết quả ra file.
import json, os, subprocess, time, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
SIZES = ["m15", "m7"]
MODES = ["base", "showwork", "loop", "tool", "struct"]
LOG = open("monitor_math.log", "a")

def say(m):
    LOG.write(m + "\n"); LOG.flush(); print(m, flush=True)

def check(size, mode):
    d = f"kernels_impM_{size}_{mode}"
    meta = json.load(open(f"{d}/meta.json"))
    env = dict(os.environ, KAGGLE_API_TOKEN=meta["token"])
    st = subprocess.run(["kaggle","kernels","status",meta["ref"]],
                        env=env, capture_output=True, text=True)
    o = (st.stdout or "") + (st.stderr or "")
    if "COMPLETE" in o:
        subprocess.run(["kaggle","kernels","output",meta["ref"],"-p",f"resM_{size}_{mode}"],
                       env=env, capture_output=True, text=True)
        try:
            acc = round(json.load(open(f"resM_{size}_{mode}/summary.json"))["acc"], 3)
            return ("DONE", acc)
        except Exception:
            return ("DONE", "?")
    if "ERROR" in o:
        return ("ERR", None)
    return ("RUN", None)

MAX_ITERS = 48   # 48 * 5min = 4h trần an toàn
for it in range(MAX_ITERS):
    res = {}
    n_final = 0
    for size in SIZES:
        for mode in MODES:
            k = f"{size}_{mode}"
            try:
                res[k] = check(size, mode)
            except Exception as e:
                res[k] = ("RUN", None)   # meta chưa có -> coi như đang chạy
            if res[k][0] in ("DONE","ERR"):
                n_final += 1
    line = " ".join(f"{k}:{v[0]}{('='+str(v[1])) if v[1] is not None else ''}" for k,v in res.items())
    say(f"[iter {it} | {n_final}/10 final] {line}")
    if n_final == 10:
        json.dump({k:{"status":v[0],"acc":v[1]} for k,v in res.items()},
                  open("monitor_math_result.json","w"), indent=2)
        say("ALL 10 FINAL -> exit, notify parent")
        sys.exit(0)
    time.sleep(300)

# Hết trần thời gian
json.dump({k:{"status":v[0],"acc":v[1]} for k,v in res.items()},
          open("monitor_math_result.json","w"), indent=2)
say(f"TIMEOUT after {MAX_ITERS} iters, {n_final}/10 final -> exit")
sys.exit(1)
