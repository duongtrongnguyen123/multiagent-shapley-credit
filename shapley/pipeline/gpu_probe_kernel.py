# Kiem tra moi truong chay cho ARC-AGI-3: xac nhan accelerator DUNG la RTX 6000 Pro.
import subprocess, json, os, glob
print("=== nvidia-smi ===", flush=True)
print(subprocess.run(["nvidia-smi","--query-gpu=name,memory.total,compute_cap,driver_version",
                      "--format=csv,noheader"],capture_output=True,text=True).stdout, flush=True)
import torch
name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO_CUDA"
cap  = torch.cuda.get_device_capability(0) if torch.cuda.is_available() else None
tot  = torch.cuda.get_device_properties(0).total_memory/1e9 if torch.cuda.is_available() else 0
print(f"torch={torch.__version__} gpu={name} sm={cap} vram={tot:.1f}GB", flush=True)
print("competition data:", sorted(glob.glob("/kaggle/input/*"))[:5], flush=True)
out={"gpu":name,"sm":list(cap) if cap else None,"vram_gb":round(tot,1),
     "torch":torch.__version__,
     "IS_RTX6000PRO": bool(cap and cap[0]>=12),          # Blackwell sm_120
     "IS_P100_FALLBACK": bool(cap and cap==(6,0))}       # canh bao tut ve P100
print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json","w"), indent=2)
