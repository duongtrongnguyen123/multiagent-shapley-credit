# Do DATA PARALLEL tren 2xT4: 2 tien trinh, moi tien trinh mot card, chia doi so bai.
import os, sys, glob, json, time, subprocess, tempfile, torch
NG = torch.cuda.device_count()
WORKER = os.environ.get("DP_WORKER")

WORK = r'''
import os, sys, glob, json, time, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
w=int(os.environ["DP_WORKER"]); n=int(os.environ["DP_N"])
_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
m=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="cuda").eval()
Q=["Solve step by step: what is 17*23+45?"]*(16//n)
ps=[tok.apply_chat_template([{"role":"user","content":q}],tokenize=False,add_generation_prompt=True) for q in Q]
e=tok(ps,return_tensors="pt",padding=True).to(m.device)
with torch.no_grad(): m.generate(**e,max_new_tokens=8,do_sample=False,pad_token_id=tok.pad_token_id)
torch.cuda.synchronize(); t0=time.time()
with torch.no_grad(): o=m.generate(**e,max_new_tokens=256,do_sample=False,pad_token_id=tok.pad_token_id)
torch.cuda.synchronize(); dt=time.time()-t0
nt=int((o[:,e["input_ids"].shape[1]:]!=tok.pad_token_id).sum())
json.dump({"worker":w,"seconds":dt,"tokens":nt,"dev":torch.cuda.get_device_name(0)},
          open(f"/kaggle/working/dp_{w}.json","w"))
'''
if WORKER is None:
    with open("/tmp/w.py","w") as f: f.write(WORK)
    res={}
    for n in [1,2]:
        t0=time.time(); procs=[]
        for w in range(n):
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(w), DP_WORKER=str(w), DP_N=str(n))
            procs.append(subprocess.Popen([sys.executable,"/tmp/w.py"],env=env))
        for p in procs: p.wait()
        wall=time.time()-t0
        tot=0
        for w in range(n):
            f=f"/kaggle/working/dp_{w}.json"
            if os.path.exists(f): tot+=json.load(open(f))["tokens"]
        res[f"{n}_gpu"]={"wall_seconds":round(wall,2),"total_tokens":tot,
                         "tok_per_sec":round(tot/wall,1)}
        print(n,"gpu:",json.dumps(res[f"{n}_gpu"]),flush=True)
    if "1_gpu" in res and "2_gpu" in res:
        res["speedup_2gpu"]=round(res["2_gpu"]["tok_per_sec"]/max(res["1_gpu"]["tok_per_sec"],1e-9),3)
    print("SUMMARY",json.dumps(res),flush=True)
    json.dump(res,open("/kaggle/working/summary.json","w"),indent=2)
