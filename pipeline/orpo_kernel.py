# ORPO LoRA cho Aggregator — giai đoạn 2 của vòng preference optimization.
#
# Bối cảnh (docs/ORPO_AGGREGATOR.md): agg3 .467 | vote5 .507 | oracle .673 trên MATH 1.5B.
# 86% lỗi của Aggregator là CHỌN SAI thật (không phải lỗi format), và nó chép ứng viên cuối
# 65% số câu ngay cả ở K=5 — recency bias định lượng được. 428 cặp preference đã sinh từ
# MATH train, mỗi cặp là (cùng một prompt, chosen = ứng viên đúng, rejected = ứng viên
# Aggregator đã chọn nhưng sai).
#
# ORPO chứ không DPO: không cần reference model -> vừa T4 16GB, và gộp SFT + preference một
# bước. Với 428 cặp thì DPO 2-model là lãng phí bộ nhớ không cần thiết.
#
# Rủi ro đã ghi trước: 428 cặp là ÍT so với literature. Null result là khả năng thật, và vẫn
# có giá trị — nếu copies_last (65%) không giảm thì recency bias là giới hạn năng lực của
# 1.5B chứ không phải vấn đề thiếu dữ liệu.
import os, sys, json, glob, subprocess

# PHẢI đặt TRƯỚC khi import torch, nếu không allocator đã khởi tạo và biến này vô tác dụng.
# Lần chạy v4 đặt sau import nên không có hiệu lực -> vẫn OOM vì phân mảnh.
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# CHỈ dùng 1 GPU. Kaggle T4 cấp 2 GPU, HF Trainer thấy vậy thì tự bật DataParallel, rồi
# `scatter_gather` gom logits của cả hai về GPU 0 — với vocab 152k x seq 1536 x 2 (chosen+
# rejected) thì riêng phép gather đó đòi 13.91 GiB và giết kernel ở cuối epoch 1. Traceback
# v5 chỉ thẳng vào torch/nn/parallel/comm.py:255. Một GPU chậm hơn nhưng chạy được.
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

EPOCHS = __EPOCHS__
LR     = __LR__
BETA   = __BETA__      # hệ số odds-ratio của ORPO
MAXLEN = __MAXLEN__

# GHIM phiên bản trl: bản mới (>=0.20) đã BỎ ORPOTrainer/ORPOConfig — lần chạy đầu chết ở
# `ImportError: cannot import name 'ORPOConfig' from 'trl'` vì pip -U kéo về bản mới nhất.
# 0.11-0.19 vẫn còn ORPO. Cũng ghim transformers cho khớp API của trl cũ.
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "trl==0.13.0", "peft>=0.13,<0.15", "accelerate>=0.34", "datasets<4",
                "bitsandbytes>=0.46.1"], check=False)

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import Dataset
from peft import LoraConfig
import trl
print("trl", getattr(trl, "__version__", "?"), flush=True)
from trl import ORPOConfig, ORPOTrainer

_c = glob.glob("/kaggle/input/**/model.safetensors", recursive=True)
if not _c:
    raise FileNotFoundError("khong thay 1.5B weights :: "
                            + str(glob.glob("/kaggle/input/**", recursive=True)[:30]))
MODEL = os.path.dirname(sorted(_c, key=len)[0])

# ưu tiên bản K=2 (prompt ngắn hơn ~1/3 -> ít bị cắt hơn nhiều); fallback bản K=3
_p = (glob.glob("/kaggle/input/**/pairs_k2.jsonl", recursive=True)
      or glob.glob("/kaggle/input/**/pairs_all.jsonl", recursive=True))
if not _p:
    raise FileNotFoundError("khong thay pairs_*.jsonl :: "
                            + str(glob.glob("/kaggle/input/**", recursive=True)[:30]))
PAIRS = sorted(_p, key=len)[0]
print(f"MODEL={MODEL}\nPAIRS={PAIRS}", flush=True)

AGG_SYS = ("You are given a problem and one or more candidate solutions. Decide the correct "
           "final answer by re-checking. Put the final answer in \\boxed{}.")

tok = AutoTokenizer.from_pretrained(MODEL)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

# ---- dựng dataset: prompt phải khớp ĐÚNG format lúc inference -----------------
rows = []
for line in open(PAIRS, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    # apply_chat_template để prompt lúc train giống hệt lúc gen() ở kernel eval
    prompt = tok.apply_chat_template(
        [{"role": "system", "content": AGG_SYS},
         {"role": "user", "content": d["prompt"]}],
        tokenize=False, add_generation_prompt=True)
    rows.append({"prompt": prompt, "chosen": d["chosen"], "rejected": d["rejected"]})
print(f"{len(rows)} cap preference", flush=True)

# giữ lại một phần nhỏ để xem loss trên dữ liệu chưa thấy — 428 cặp thì 5% là đủ để phát
# hiện overfit thô, nhiều hơn thì phí dữ liệu train vốn đã ít
split = max(16, len(rows) // 20)
ds_train = Dataset.from_list(rows[split:])
ds_eval = Dataset.from_list(rows[:split])
print(f"train {len(ds_train)} | eval {len(ds_eval)}", flush=True)

# fp16 chứ không 4-bit: bản 4-bit chết vì `CUDA error: an illegal memory access` trong
# bitsandbytes dequant khi chạy cùng gradient checkpointing của ORPO. Thay vào đó cắt bộ nhớ
# ở chỗ thật sự tốn: ORPO gọi logits.log_softmax trên vocab 152k và concatenated_forward
# ghép chosen+rejected, nên chi phí ~ 2 x seq_len x 152k. Giảm seq_len là đòn bẩy chính.
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16,
                                             device_map={"": 0})
model.config.use_cache = False

peft_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                      task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])

_cfg_kw = dict(
    output_dir="/kaggle/working/orpo_out",
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,      # eval là chỗ OOM ở v5 (cuối epoch 1)
    gradient_accumulation_steps=8,
    learning_rate=LR,
    beta=BETA,
    max_length=MAXLEN,
    max_prompt_length=MAXLEN - 512,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    logging_steps=10,
    save_strategy="no",
    bf16=False, fp16=True,
    gradient_checkpointing=True,
    report_to=[],
    remove_unused_columns=False,
)
# `evaluation_strategy` bị đổi tên thành `eval_strategy` ở transformers 4.46 -> thử cả hai
try:
    cfg = ORPOConfig(eval_strategy="epoch", **_cfg_kw)
except TypeError:
    cfg = ORPOConfig(evaluation_strategy="epoch", **_cfg_kw)

# trl 0.13 dùng `processing_class`, các bản cũ hơn dùng `tokenizer` -> thử cả hai
try:
    trainer = ORPOTrainer(model=model, args=cfg, processing_class=tok,
                          train_dataset=ds_train, eval_dataset=ds_eval,
                          peft_config=peft_cfg)
except TypeError:
    trainer = ORPOTrainer(model=model, args=cfg, tokenizer=tok,
                          train_dataset=ds_train, eval_dataset=ds_eval,
                          peft_config=peft_cfg)
print("== bat dau train ==", flush=True)
trainer.train()

ADAPTER = "/kaggle/working/adapter"
trainer.model.save_pretrained(ADAPTER)
tok.save_pretrained(ADAPTER)
print(f"adapter -> {ADAPTER}", flush=True)

hist = [h for h in trainer.state.log_history if "loss" in h or "eval_loss" in h]
json.dump({"n_pairs": len(rows), "n_train": len(ds_train), "n_eval": len(ds_eval),
           "epochs": EPOCHS, "lr": LR, "beta": BETA, "max_length": MAXLEN,
           "log_history": hist},
          open("/kaggle/working/summary.json", "w"), indent=2)
print("SUMMARY", json.dumps({"n_pairs": len(rows), "epochs": EPOCHS,
                             "final": hist[-1] if hist else None}), flush=True)
print("done", flush=True)
