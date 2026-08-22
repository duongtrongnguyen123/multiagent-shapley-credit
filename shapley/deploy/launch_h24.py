#!/usr/bin/env python3
"""H24 (pre-reg #23): render resolve_kernel cho 4 o va day len 4 tai khoan roi."""
import os, re, json, subprocess, sys
from pathlib import Path

RTX_ONLY = os.environ.get("KAGGLE_RTX_ACCOUNT", "")  # tai khoan RTX, dat qua bien moi truong
ROOT = Path(__file__).resolve().parents[1]
ACC  = Path(os.environ["ACCOUNTS_FILE"])
TPL  = (ROOT/"pipeline"/"resolve_kernel.py").read_text()
M15, M7 = "xatri007/qwen2-5-1-5b-instruct", "ragnar123/qwen2-5-7b-instruct"
DG = "thedevastator/grade-school-math-8k-q-a"
DM = "open-benchmarks/math-500-measuring-mathematical-problem-solving"
CELLS = [  # tag, task, n, bs, quant, model_ds, task_ds
 ("rs_g15","gsm8k",250,16,False,M15,DG), ("rs_g7","gsm8k",250, 8,True, M7,DG),
 ("rs_m15","math", 200,16,False,M15,DM), ("rs_m7","math", 200, 8,True, M7,DM)]

def accounts():
    out=[]
    for ln in ACC.read_text().splitlines():
        s=ln.strip()
        if not s or s.startswith("#"): continue
        p=s.split(); m=re.search(r"KGAT_[0-9a-f]+", p[1]) if len(p)>1 else None
        if m: out.append((p[0], m.group(0)))
    return out

want = sys.argv[1:] or [a for a in os.environ.get("KAGGLE_ACCOUNTS","").split(",") if a] \
       or [u for u, _ in accounts()]   # mac dinh: moi tai khoan co trong accounts.txt
avail = [a for a in accounts() if a[0] in want]
assert len(avail) >= len(CELLS), f"chi co {len(avail)} tai khoan cho {len(CELLS)} o"
for (tag,task,n,bs,quant,mds,tds),(user,tokn) in zip(CELLS, avail):
    kd = ROOT/f"kernels_{tag}"; kd.mkdir(exist_ok=True)
    src = (TPL.replace("__TASK__",task).replace("__N__",str(n))
              .replace("__BS__",str(bs)).replace("__QUANT__",str(quant)))
    import ast; ast.parse(src)                                  # LUAT: parse TRUOC khi day
    (kd/"kernel.py").write_text(src)
    ref=f"{user}/impm-{tag.replace('_','-')}"
    (kd/"kernel-metadata.json").write_text(json.dumps({
      "id":ref,"title":f"impm-{tag.replace('_','-')}","code_file":"kernel.py","language":"python",
      "kernel_type":"script","is_private":True,"enable_gpu":True,"enable_internet":bool(quant),
      "machine_shape":"NvidiaTeslaT4","dataset_sources":[mds,tds],
      "competition_sources":[],"kernel_sources":[]},indent=2))
    (kd/"meta.json").write_text(json.dumps({"label":tag,"token":tokn,"ref":ref}))
    env=dict(os.environ, KAGGLE_API_TOKEN=tokn)
    r=subprocess.run(["/opt/miniconda3/bin/kaggle","kernels","push","-p",str(kd)],
                     capture_output=True,text=True,env=env)
    print(f"{tag:7s} -> {ref:38s} {(r.stdout+r.stderr).strip().splitlines()[-1][:70]}")
