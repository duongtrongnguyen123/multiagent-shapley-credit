# H27 — VERIFIER PHAN BIET (cham diem) + RERANK@8. Xem docs/PREREGISTRATION.md #27.
# Nhan TU DONG tu grader, KHONG gan tay. Chay tren Kaggle T4 (remote da mat).
import os, re, csv, json, glob, random, subprocess, sys, statistics as st
# SUA LOI MOI TRUONG: anh Kaggle co torchao 0.10.0 nhung peft doi >0.16.0
subprocess.run([sys.executable,"-m","pip","install","-q","-U","torchao>=0.16.0"],check=False)
if __QUANT__: subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"],check=False)
import torch, torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

NTR=__NTR__; NTE=__NTE__; BS=__BS__; QUANT=__QUANT__; MB=__MB__
K=8; NF=5; EPOCH=1; LR=1e-4
_c=glob.glob("/kaggle/input/**/model.safetensors",recursive=True) or \
   glob.glob("/kaggle/input/**/model.safetensors.index.json",recursive=True)
MODEL=os.path.dirname(sorted(_c,key=len)[0])
_tr=sorted(glob.glob("/kaggle/input/**/main_train.csv",recursive=True),key=len)
_te=sorted(glob.glob("/kaggle/input/**/main_test.csv",recursive=True),key=len)
TRROWS=list(csv.DictReader(open(_tr[0])))[:NTR]
TEROWS=list(csv.DictReader(open(_te[0])))[:NTE]
tok=AutoTokenizer.from_pretrained(MODEL); tok.padding_side="left"
if tok.pad_token is None: tok.pad_token=tok.eos_token
if QUANT:
    from transformers import BitsAndBytesConfig
    _b=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True)
    model=AutoModelForCausalLM.from_pretrained(MODEL,quantization_config=_b,device_map="auto")
else:
    model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=torch.float16,device_map="auto")
print(f"MODEL={MODEL} train={len(TRROWS)} test={len(TEROWS)}",flush=True)
NUM=re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def pred(t):
    m=re.findall(r"(?:answer is|=)\s*\$?(-?\d[\d,]*(?:\.\d+)?)",t or "",re.I) or NUM.findall(t or "")
    return m[-1].replace(",","") if m else None
def ok(x,g):
    try: return x is not None and abs(float(x)-float(g))<1e-4
    except: return x==g
gold=lambda r:(NUM.findall(r["answer"].split("####")[-1]) or [None])[0].replace(",","")
S_SYS="Solve step by step. End with 'The answer is <number>'."
J_SYS="You judge whether a proposed solution is correct. Answer with one word: Yes or No."
def jprompt(q,s): return tok.apply_chat_template(
    [{"role":"system","content":J_SYS},
     {"role":"user","content":f"Problem: {q}\n\nProposed solution:\n{s}\n\nIs this solution correct?"}],
    tokenize=False,add_generation_prompt=True)
@torch.no_grad()
def gen(sysm,usrs,mx=400,temp=0.0,k=1,adapter=False):
    # adapter=False -> DUNG MODEL GOC de GIAI (LoRA Yes/No pha nang luc giai)
    outs=[]
    for i in range(0,len(usrs),BS):
        ch=usrs[i:i+BS]
        ps=[tok.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
            tokenize=False,add_generation_prompt=True) for u in ch]
        e=tok(ps,return_tensors="pt",padding=True).to("cuda")
        _has=hasattr(model,"disable_adapter")
        if (not adapter) and _has:
            with model.disable_adapter():
                o=model.generate(**e,max_new_tokens=mx,do_sample=(temp>0),temperature=max(temp,1e-5),
                                 top_p=0.95,num_return_sequences=k,pad_token_id=tok.pad_token_id)
        else:
            o=model.generate(**e,max_new_tokens=mx,do_sample=(temp>0),temperature=max(temp,1e-5),
                             top_p=0.95,num_return_sequences=k,pad_token_id=tok.pad_token_id)
        torch.cuda.empty_cache()
        L=e["input_ids"].shape[1]
        outs+=[tok.decode(o[j,L:],skip_special_tokens=True).strip() for j in range(o.shape[0])]
        del e,o
    torch.cuda.empty_cache(); return outs

# 1) SINH + NHAN TU DONG
print("== sinh du lieu huan luyen ==",flush=True)
TQ=[r["question"] for r in TRROWS]; TG=[gold(r) for r in TRROWS]
samp=gen(S_SYS,TQ,400,0.8,K)
DATA=[(TQ[i],samp[i*K+j],ok(pred(samp[i*K+j]),TG[i])) for i in range(len(TQ)) for j in range(K)]
pos=sum(1 for d in DATA if d[2])
print(f"cap={len(DATA)} dung={pos} ({pos/len(DATA):.3f})",flush=True)
PRE_ACC=pos/len(DATA)   # do chinh xac mau TRUOC huan luyen (moc doi chieu)

if QUANT: model=prepare_model_for_kbit_training(model)
model.gradient_checkpointing_enable(); model.enable_input_require_grads()
model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,
      target_modules=["q_proj","k_proj","v_proj","o_proj"],task_type="CAUSAL_LM"))
model.print_trainable_parameters()
YES=tok.encode("Yes",add_special_tokens=False)[0]; NO=tok.encode("No",add_special_tokens=False)[0]
print("token Yes/No:",YES,NO,flush=True)
opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=LR)
random.shuffle(DATA); model.train()
tok.padding_side="left"
for ep in range(EPOCH):
    tot=0.0; n=0
    for i in range(0,len(DATA),MB):
        b=DATA[i:i+MB]
        e=tok([jprompt(q,s) for q,s,_ in b],return_tensors="pt",padding=True,truncation=True,max_length=768).to("cuda")
        out=model(**e)
        lg=out.logits[:,-1,:]                       # token ke tiep = phan quyet
        tgt=torch.tensor([YES if y else NO for _,_,y in b],device="cuda")
        loss=F.cross_entropy(lg[:,[NO,YES]], (tgt==YES).long())
        loss.backward()
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.0)
        opt.step(); opt.zero_grad()
        tot+=float(loss); n+=1
        if n%50==0: print(f"  ep{ep} b{n}/{len(DATA)//MB} loss={tot/n:.4f} mem={torch.cuda.max_memory_allocated()/1e9:.1f}GB",flush=True)
        del out,lg; 
    print(f"epoch {ep}: loss={tot/max(n,1):.4f}",flush=True)
model.eval(); model.save_pretrained("/kaggle/working/disc_lora")

# ---------- 3) CHAM DIEM + RERANK ----------
@torch.no_grad()
def score(qs,sols):
    out=[]
    for i in range(0,len(qs),BS):
        e=tok([jprompt(q,s) for q,s in zip(qs[i:i+BS],sols[i:i+BS])],
              return_tensors="pt",padding=True,truncation=True,max_length=768).to("cuda")
        lg=model(**e).logits[:,-1,:]
        out+=F.log_softmax(lg[:,[NO,YES]],dim=-1)[:,1].float().tolist()
        del e,lg
    torch.cuda.empty_cache(); return out

TEQ=[r["question"] for r in TEROWS]; TEG=[gold(r) for r in TEROWS]
FOLD=len(TEQ)//NF; folds=[]; all_s=[]; all_y=[]
for fi in range(NF):
    qs=TEQ[fi*FOLD:(fi+1)*FOLD]; gs=TEG[fi*FOLD:(fi+1)*FOLD]
    print(f"== fold {fi} ==",flush=True)
    mj=gen(S_SYS,qs,400,0.8,K)
    grid=[[mj[i*K+j] for j in range(K)] for i in range(len(qs))]
    fq=[qs[i] for i in range(len(qs)) for j in range(K)]
    fs=[grid[i][j] for i in range(len(qs)) for j in range(K)]
    sc=score(fq,fs); lab=[ok(pred(fs[n]),gs[n//K]) for n in range(len(fs))]
    all_s+=sc; all_y+=lab
    a_re,a_mj,a_or,a_gd,a_ws,a_wm,a_os=[],[],[],[],[],[],[]
    for i in range(len(qs)):
        S=sc[i*K:(i+1)*K]; C=grid[i]
        a_re.append(pred(C[max(range(K),key=lambda j:S[j])]))
        cnt={}; wsum={}; wcnt={}
        for j in range(K):
            p=pred(C[j])
            if p is not None:
                cnt[p]=cnt.get(p,0)+1
                w=float(torch.tensor(S[j]).exp())          # prob(Yes)
                wsum[p]=wsum.get(p,0.0)+w; wcnt[p]=wcnt.get(p,0)+1
        a_mj.append(max(cnt,key=cnt.get) if cnt else None)
        a_ws.append(max(wsum,key=wsum.get) if wsum else None)                       # TONG diem
        a_wm.append(max(wsum,key=lambda p: wsum[p]/wcnt[p]) if wsum else None)      # TRUNG BINH diem
        _nc=sum(1 for j in range(K) if ok(pred(C[j]),gs[i]))
        a_or.append(gs[i] if _nc>=1 else pred(C[0]))
        a_os.append(gs[i] if _nc>=2 else None)          # oracle_solid: doi >=2/K cung dung
        a_gd.append(pred(C[0]))
    acc=lambda a: round(sum(ok(x,g) for x,g in zip(a,gs))/len(gs),4)
    r={"fold":fi,"n":len(qs),"greedy1":acc(a_gd),"maj8":acc(a_mj),"rerank8":acc(a_re),
       "wvote_sum":acc(a_ws),"wvote_mean":acc(a_wm),"oracle8":acc(a_or),
       "rerank_minus_maj":round(acc(a_re)-acc(a_mj),4),
       "wsum_minus_maj":round(acc(a_ws)-acc(a_mj),4),
       "wmean_minus_maj":round(acc(a_wm)-acc(a_mj),4),
       "oracle_solid8":acc(a_os),
       "gap_solid":round(acc(a_os)-acc(a_mj),4),
       "wsum_pct_gap":round((acc(a_ws)-acc(a_mj))/max(acc(a_or)-acc(a_mj),1e-9),3),
       # NGUONG #35: khoang trong that <=0 -> KHONG tinh ti le
       "wsum_pct_gap_solid":(round((acc(a_ws)-acc(a_mj))/(acc(a_os)-acc(a_mj)),3)
                             if acc(a_os)-acc(a_mj)>1e-9 else None),
       "pct_gap_closed":round((acc(a_re)-acc(a_mj))/max(acc(a_or)-acc(a_mj),1e-9),3)}
    folds.append(r); print(f"[fold {fi}] {json.dumps(r)}",flush=True)
# HIEU LUC: neu sinh mau SAU huan luyen tut xa so voi TRUOC -> adapter da ro ri vao pha giai
POST_ACC=sum(1 for y in all_y if y)/max(len(all_y),1)
LEAK=round(PRE_ACC-POST_ACC,4)
print(f"PRE_ACC={PRE_ACC:.4f} POST_ACC={POST_ACC:.4f} LEAK={LEAK}",flush=True)
pa=[s for s,y in zip(all_s,all_y) if y]; na=[s for s,y in zip(all_s,all_y) if not y]
auc=round(sum(1 for p in pa for q in na if p>q)/max(len(pa)*len(na),1),4) if pa and na else None
def sp(k):
    v=[f[k] for f in folds]
    return {"mean":round(st.mean(v),4),"min":round(min(v),4),"max":round(max(v),4),"pos":sum(1 for x in v if x>0)}
out={"tag":"disc","auc":auc,"VALID_auc":bool(auc and auc>0.55),
     "pre_acc":round(PRE_ACC,4),"post_acc":round(POST_ACC,4),"adapter_leak":LEAK,
     "VALID_no_leak":bool(abs(LEAK)<=0.05),   # nguong moi: ro ri adapter <= 5 diem

     "n_train_pairs":len(DATA),"train_pos_rate":round(pos/len(DATA),4),"folds":folds}
for k in ["greedy1","maj8","rerank8","wvote_sum","wvote_mean","oracle8","oracle_solid8",
          "rerank_minus_maj","wsum_minus_maj","wmean_minus_maj","gap_solid","wsum_pct_gap"]: out[k]=sp(k)
print("SUMMARY",json.dumps(out),flush=True)
json.dump(out,open("/kaggle/working/summary.json","w"),indent=2)
json.dump([{"q":fq[i][:200],"sol":fs[i][:500],"score":all_s[i],"correct":all_y[i]}
           for i in range(min(200,len(all_s)))],open("/kaggle/working/traces.json","w"),indent=1)
print("DONE",flush=True)
