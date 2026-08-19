# Do TOC DO SINH thuc te: P100 vs T4, cung model 1.5B, cung tai.
import os, glob, json, time, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
info={"torch":torch.__version__,"n_gpu":torch.cuda.device_count(),
      "gpus":[{"name":torch.cuda.get_device_name(i),
               "sm":list(torch.cuda.get_device_capability(i)),
               "gb":round(torch.cuda.get_device_properties(i).total_memory/1e9,1)}
              for i in range(torch.cuda.device_count())]}
print(json.dumps(info),flush=True)
_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
res={"env":info}
for dt_name,dt in [("fp16",torch.float16)]:
    try:
        m=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=dt,device_map="cuda").eval()
        Q=["Solve step by step: what is 17*23+45?"]*16
        ps=[tok.apply_chat_template([{"role":"user","content":q}],tokenize=False,add_generation_prompt=True) for q in Q]
        e=tok(ps,return_tensors="pt",padding=True).to(m.device)
        with torch.no_grad(): m.generate(**e,max_new_tokens=8,do_sample=False,pad_token_id=tok.pad_token_id)
        torch.cuda.synchronize(); t0=time.time()
        with torch.no_grad():
            o=m.generate(**e,max_new_tokens=256,do_sample=False,pad_token_id=tok.pad_token_id)
        torch.cuda.synchronize(); dt_s=time.time()-t0
        ntok=int((o[:,e["input_ids"].shape[1]:]!=tok.pad_token_id).sum())
        res[dt_name]={"seconds":round(dt_s,2),"gen_tokens":ntok,
                      "tok_per_sec":round(ntok/dt_s,1),"ok":True}
        print(dt_name,json.dumps(res[dt_name]),flush=True)
        del m; torch.cuda.empty_cache()
    except Exception as ex:
        res[dt_name]={"ok":False,"err":f"{type(ex).__name__}: {str(ex)[:200]}"}
        print(dt_name,"LOI",res[dt_name]["err"],flush=True)
print("SUMMARY",json.dumps(res),flush=True)
json.dump(res,open("/kaggle/working/summary.json","w"),indent=2)
