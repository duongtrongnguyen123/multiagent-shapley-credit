# 7B tren 2xT4: (A) fp16 pipeline 2 card, (B) 4-bit MOT card, (C) 4-bit DATA PARALLEL 2 card.
import os, sys, glob, json, time, subprocess, torch
subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"],check=False)
W = os.environ.get("QW")
CODE = r'''
import os, glob, json, time, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
mode=os.environ["QMODE"]; w=int(os.environ.get("QW","0")); n=int(os.environ.get("QN","1"))
_c=glob.glob("/kaggle/input/**/model.safetensors*",recursive=True)+glob.glob("/kaggle/input/**/*.index.json",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
if mode=="fp16_pipe":
    m=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="auto").eval()
else:
    b=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    m=AutoModelForCausalLM.from_pretrained(MODEL,quantization_config=b,device_map="cuda").eval()
Q=["Solve step by step: what is 17*23+45?"]*(16//n)
ps=[tok.apply_chat_template([{"role":"user","content":q}],tokenize=False,add_generation_prompt=True) for q in Q]
e=tok(ps,return_tensors="pt",padding=True).to(m.device)
with torch.no_grad(): m.generate(**e,max_new_tokens=8,do_sample=False,pad_token_id=tok.pad_token_id)
torch.cuda.synchronize(); t0=time.time()
with torch.no_grad(): o=m.generate(**e,max_new_tokens=256,min_new_tokens=256,do_sample=False,pad_token_id=tok.pad_token_id)
torch.cuda.synchronize(); dt=time.time()-t0
nt=int((o[:,e["input_ids"].shape[1]:]!=tok.pad_token_id).sum())
json.dump({"seconds":dt,"tokens":nt,"n_seq":len(Q)},open(f"/kaggle/working/q_{mode}_{w}.json","w"))
'''
open("/tmp/qw.py","w").write(CODE)
res={"n_gpu":torch.cuda.device_count()}
def run(mode,n):
    for w in range(4):
        f=f"/kaggle/working/q_{mode}_{w}.json"
        if os.path.exists(f): os.remove(f)
    t0=time.time(); ps=[]
    for w in range(n):
        env=dict(os.environ,QMODE=mode,QW=str(w),QN=str(n))
        if mode!="fp16_pipe": env["CUDA_VISIBLE_DEVICES"]=str(w)
        ps.append(subprocess.Popen([sys.executable,"/tmp/qw.py"],env=env))
    rcs=[p.wait() for p in ps]
    wall=time.time()-t0; tot=0; nseq=0; missing=[]
    for w in range(n):
        f=f"/kaggle/working/q_{mode}_{w}.json"
        if os.path.exists(f):
            j=json.load(open(f)); tot+=j["tokens"]; nseq+=j.get("n_seq",0)
        else: missing.append(w)
    return {"wall":round(wall,2),"tokens":tot,"n_seq":nseq,"rcs":rcs,
            "missing_workers":missing,"VALID":len(missing)==0,
            "tok_per_sec":round(tot/wall,1)}
for lbl,mode,n in [("A_fp16_pipeline_2card","fp16_pipe",1),
                   ("B_4bit_1card","q4",1),
                   ("C_4bit_dataparallel_2card","q4",2)]:
    try:
        res[lbl]=run(mode,n); print(lbl,json.dumps(res[lbl]),flush=True)
    except Exception as ex:
        res[lbl]={"err":str(ex)[:150]}; print(lbl,"LOI",res[lbl]["err"],flush=True)
try:
    a=res["A_fp16_pipeline_2card"]["tok_per_sec"]; c=res["C_4bit_dataparallel_2card"]["tok_per_sec"]
    b=res["B_4bit_1card"]["tok_per_sec"]
    res["C_vs_A"]=round(c/a,3); res["4bit_vs_fp16_per_card"]=round(b/a,3)
except Exception: pass
print("SUMMARY",json.dumps(res),flush=True)
json.dump(res,open("/kaggle/working/summary.json","w"),indent=2)
