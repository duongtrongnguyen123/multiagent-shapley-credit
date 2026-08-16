# Do THUC TE: device_map="auto" dat layer o dau, va co nhanh hon khong.
import os, glob, json, time, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
Q=["What is 17*23? Solve step by step."]*32
res={}
for mode in ["cuda","auto"]:
    m=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map=mode).eval()
    dm=getattr(m,"hf_device_map",None)
    devs={}
    if dm:
        for k,v in dm.items(): devs[str(v)]=devs.get(str(v),0)+1
    ps=[tok.apply_chat_template([{"role":"user","content":q}],tokenize=False,add_generation_prompt=True) for q in Q]
    e=tok(ps,return_tensors="pt",padding=True).to(m.device)
    with torch.no_grad(): m.generate(**e,max_new_tokens=16,do_sample=False,pad_token_id=tok.pad_token_id)  # warmup
    torch.cuda.synchronize(); t0=time.time()
    with torch.no_grad():
        o=m.generate(**e,max_new_tokens=256,do_sample=False,pad_token_id=tok.pad_token_id)
    torch.cuda.synchronize(); dt=time.time()-t0
    per=[round(torch.cuda.memory_allocated(i)/1e9,2) for i in range(torch.cuda.device_count())]
    res[mode]={"seconds":round(dt,2),"module_per_device":devs,
               "vram_per_gpu_GB":per,"n_devices_used":len([x for x in per if x>0.05])}
    print(mode,json.dumps(res[mode]),flush=True)
    del m; torch.cuda.empty_cache()
res["speedup_auto_vs_cuda"]=round(res["cuda"]["seconds"]/max(res["auto"]["seconds"],1e-9),3)
print("SUMMARY",json.dumps(res),flush=True)
json.dump(res,open("/kaggle/working/summary.json","w"),indent=2)
