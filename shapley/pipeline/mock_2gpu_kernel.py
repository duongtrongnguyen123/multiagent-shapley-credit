# MOCK TEST: 2 T4 có chạy 2 pipeline (backward/forward) song song trong 1 kernel không?
#
# Câu hỏi: Kaggle T4 cấp 2 GPU. Muốn chạy 2 pipeline độc lập SONG SONG — mỗi GPU 1 bản model
# 1.5B, mỗi bản chạy pipeline riêng (forward / backward). Đây là "model-parallel theo pipeline",
# khác data-parallel (cùng 1 model chia batch).
#
# Mock: load 2 bản model Qwen2.5-1.5B (cuda:0 và cuda:1), chạy mỗi cái 1 batch ~8 câu song song,
# đo VRAM từng GPU + thời gian. Nếu cả 2 chạy được và VRAM mỗi GPU < 15GB -> khả thi.
import os, json, time, glob, torch, threading
from transformers import AutoModelForCausalLM, AutoTokenizer

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
MODEL = os.path.dirname(sorted(_c, key=len)[0])
print("device_count =", torch.cuda.device_count(), flush=True)
for i in range(torch.cuda.device_count()):
    p = torch.cuda.get_device_properties(i)
    print(f"  GPU{i}: {torch.cuda.get_device_name(i)} {round(p.total_memory/1e9,1)}GB", flush=True)

tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token

# load 2 bản model trên 2 GPU riêng
t0 = time.time()
models = {}
for gpu in (0, 1):
    m = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map={"": gpu}).eval()
    models[gpu] = m
    print(f"model on GPU{gpu} loaded", flush=True)
print(f"both models loaded in {time.time()-t0:.1f}s", flush=True)

QS = [f"What is {i}+{i}? Return only the number." for i in range(8)]

def gen_on(gpu, prompts, tag):
    m = models[gpu]
    enc = tok(prompts, return_tensors="pt", padding=True).to(m.device)
    with torch.no_grad():
        o = m.generate(**enc, max_new_tokens=16, do_sample=False,
                       pad_token_id=tok.pad_token_id)
    L = enc["input_ids"].shape[1]
    out = tok.decode(o[0, L:], skip_special_tokens=True).strip()
    print(f"  [{tag}] GPU{gpu} gen done: '{out[:30]}'", flush=True)

# chạy SONG SONG trên 2 GPU bằng 2 thread
threads = []
for gpu, tag in ((0, "forward"), (1, "backward")):
    th = threading.Thread(target=gen_on, args=(gpu, QS, tag))
    th.start()
    threads.append(th)
for th in threads:
    th.join()
print("parallel gen done", flush=True)

# VRAM sau khi chạy
vr = {}
for gpu in (0, 1):
    vr[gpu] = {"allocated_gb": round(torch.cuda.memory_allocated(gpu)/1e9, 2),
               "reserved_gb": round(torch.cuda.memory_reserved(gpu)/1e9, 2)}
    print(f"GPU{gpu} VRAM allocated {vr[gpu]['allocated_gb']}GB reserved {vr[gpu]['reserved_gb']}GB", flush=True)

summary = {"device_count": torch.cuda.device_count(), "loaded_2_models": True,
           "parallel_gen": True, "vram_per_gpu": vr,
           "total_elapsed": round(time.time()-t0, 1)}
print("SUMMARY", json.dumps(summary), flush=True)
json.dump(summary, open("/kaggle/working/summary.json", "w"), indent=2)
print("done", flush=True)