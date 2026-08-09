import torch, json, subprocess
n=torch.cuda.device_count()
info=[{"idx":i,"name":torch.cuda.get_device_name(i),
       "gb":round(torch.cuda.get_device_properties(i).total_memory/1e9,1),
       "sm":list(torch.cuda.get_device_capability(i))} for i in range(n)]
tot=sum(d["gb"] for d in info)
print("device_count =",n,flush=True)
for d in info: print("  ",d,flush=True)
print("TONG VRAM =",round(tot,1),"GB",flush=True)
print(subprocess.run(["nvidia-smi","--query-gpu=index,name,memory.total","--format=csv,noheader"],
                     capture_output=True,text=True).stdout,flush=True)
json.dump({"device_count":n,"devices":info,"total_gb":round(tot,1)},
          open("/kaggle/working/summary.json","w"),indent=2)
