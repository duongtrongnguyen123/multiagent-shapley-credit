# STEP-INTERLEAVED + BẤT ĐỐI XỨNG NĂNG LỰC trên MATH-500.
# Solver viết TỪNG BƯỚC; Verifier duyệt NGAY bước đó rồi mới cho viết tiếp
# (khác hẳn post-hoc: verify sau khi đã xong cả bài).
# 4 nhánh CÙNG bài để so từng câu -> đếm chính xác fix/break:
#   A: 1.5B solve, KHÔNG verify              (mốc)
#   B: 1.5B solve + 1.5B verify từng bước    (interleaved, đồng nhất)
#   C: 1.5B solve + 7B  verify từng bước     (interleaved, BẤT ĐỐI XỨNG)  <-- giả thuyết chính
#   D: 1.5B solve + 7B  verify post-hoc      (đối chứng: nhờ interleave hay chỉ nhờ 7B?)
# Cả 2 model nằm đồng thời trên GPU: 1.5B fp16 (~3GB) + 7B nf4 (~5GB) = ~8GB < 16GB T4.
import os, re, csv, json, glob, torch

N = __N__
BS = __BS__
MAX_STEPS = 6

import subprocess, sys
subprocess.run([sys.executable,"-m","pip","install","-q","-U","bitsandbytes>=0.46.1"])
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# 1.5B = có model.safetensors nguyên khối; 7B = sharded nên chỉ có index.json
M15 = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors", recursive=True), key=len)[0])
M7  = os.path.dirname(sorted(glob.glob("/kaggle/input/**/model.safetensors.index.json", recursive=True), key=len)[0])
CSV = sorted(glob.glob("/kaggle/input/**/math_500_test.csv", recursive=True), key=len)[0]
print("M15:", M15, "\nM7 :", M7, flush=True)

rows = list(csv.DictReader(open(CSV)))[:N]

tok15 = AutoTokenizer.from_pretrained(M15); tok15.padding_side = "left"
if tok15.pad_token is None: tok15.pad_token = tok15.eos_token
tok7 = AutoTokenizer.from_pretrained(M7); tok7.padding_side = "left"
if tok7.pad_token is None: tok7.pad_token = tok7.eos_token

small = AutoModelForCausalLM.from_pretrained(M15, torch_dtype=torch.float16, device_map="cuda").eval()
print("1.5B loaded", flush=True)
_bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                          bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
big = AutoModelForCausalLM.from_pretrained(M7, quantization_config=_bnb, device_map="auto").eval()
print("7B loaded (4bit) | VRAM MiB:", round(torch.cuda.memory_allocated()/1048576), flush=True)

def gen(model, tk, sysm, usrs, mx):
    """Sinh theo batch cho 1 danh sách prompt."""
    outs = []
    for i in range(0, len(usrs), BS):
        ch = usrs[i:i+BS]
        ps = [tk.apply_chat_template([{"role":"system","content":sysm},{"role":"user","content":u}],
                                     tokenize=False, add_generation_prompt=True) for u in ch]
        e = tk(ps, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            o = model.generate(**e, max_new_tokens=mx, do_sample=False, pad_token_id=tk.pad_token_id)
        L = e["input_ids"].shape[1]
        outs += [tk.decode(o[j, L:], skip_special_tokens=True).strip() for j in range(len(ch))]
    return outs

def boxed(s):
    i = s.rfind("\\boxed") if s else -1
    if i < 0: return None
    i = s.find("{", i); d = 0; st = i
    for j in range(i, len(s)):
        if s[j] == "{": d += 1
        elif s[j] == "}":
            d -= 1
            if d == 0: return s[st+1:j]
    return None
def norm(a):
    if a is None: return None
    a = str(a).strip()
    for x in ["\\left","\\right","\\!","\\,","\\;","$"," "]: a = a.replace(x, "")
    a = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", a); a = a.replace("\\dfrac","\\frac").replace("\\tfrac","\\frac")
    return a.rstrip(".").strip("{}").lower()
def eq(p, g):
    p, g = norm(p), norm(g)
    if not p or not g: return False
    if p == g: return True
    try: return abs(float(p)-float(g)) < 1e-6
    except: return False
def pred(t):
    b = boxed(t)
    if b is not None: return b
    m = re.findall(r"(?:answer is|=)\s*\$?([^\n.$]+)", t or "", re.I); return m[-1].strip() if m else None

qs = [r["Question"] for r in rows]; gs = [boxed(r["Answer"]) for r in rows]

SOLVE = "Solve the problem step by step. Put the final answer in \\boxed{}."
VERIFY_POST = "Check the proposed solution step by step; if wrong, correct it. Put the final answer in \\boxed{}."
STEP_SYS = ("Continue the solution. Write ONLY the NEXT single step, one short line. "
            "If the solution is finished, instead write the final answer as \\boxed{...}.")
# Verifier CHỈ phán 1 bước cuối -> nhiệm vụ nhỏ, KHÔNG được viết lại đáp án cuối
STEPV_SYS = ("You check ONE step of a math solution. Look ONLY at the LAST step shown. "
             "Reply with exactly 'OK' if that step is correct, otherwise 'WRONG: <corrected step>'. "
             "Do NOT solve the whole problem. Do NOT give the final answer.")

# ---------- A: 1.5B solve, không verify ----------
solA = gen(small, tok15, SOLVE, qs, 1024)
ansA = [pred(s) for s in solA]
okA = [eq(a,g) for a,g in zip(ansA,gs)]
print(f"[A] no-verify acc = {sum(okA)/len(gs):.3f}", flush=True)

# ---------- B/C: step-interleaved (batch theo từng BƯỚC) ----------
def interleaved(vmodel, vtok, tag):
    body = [""]*len(qs)          # phần lời giải đã dựng
    done = [False]*len(qs)
    ans  = [None]*len(qs)
    n_int = 0                     # số lần Verifier can thiệp (= số bước 1.5B làm SAI)
    n_steps = 0                   # tổng số bước 1.5B đã viết (để tính tỉ lệ sai/bước)
    for k in range(1, MAX_STEPS+1):
        act = [i for i in range(len(qs)) if not done[i]]
        if not act: break
        # 1) Solver viết bước tiếp theo
        prompts = [f"{qs[i]}\n\nSolution so far:\n{body[i] or '(nothing yet)'}" for i in act]
        steps = gen(small, tok15, STEP_SYS, prompts, 160)
        need_v = []
        for pos, i in enumerate(act):
            st = steps[pos].strip().split("\n")[0].strip()
            b = boxed(steps[pos])
            if b is not None:                       # Solver đã chốt đáp án -> dừng
                ans[i] = b; done[i] = True; continue
            if not st:
                done[i] = True; continue
            body[i] = (body[i] + f"\nStep {k}: {st}").strip()
            n_steps += 1
            need_v.append(i)
        if not need_v: continue
        # 2) Verifier duyệt NGAY bước vừa viết (nhiệm vụ nhỏ, ngắn)
        vp = [f"{qs[i]}\n\nSteps so far:\n{body[i]}\n\nCheck ONLY the last step." for i in need_v]
        verdicts = gen(vmodel, vtok, STEPV_SYS, vp, 96)
        for pos, i in enumerate(need_v):
            v = verdicts[pos].strip()
            if v.upper().startswith("WRONG"):
                n_int += 1
                fix = v.split(":", 1)[1].strip() if ":" in v else v
                body[i] += f"\n[Reviewer: previous step is wrong. Corrected: {fix}]"
    # bài nào chưa chốt -> ép trả lời cuối từ phần đã dựng
    rest = [i for i in range(len(qs)) if ans[i] is None]
    if rest:
        fin = gen(small, tok15, "Given the work so far, state the final answer in \\boxed{}.",
                  [f"{qs[i]}\n\nWork:\n{body[i]}" for i in rest], 256)
        for pos, i in enumerate(rest): ans[i] = pred(fin[pos])
    ok = [eq(a,g) for a,g in zip(ans,gs)]
    fix = sum(1 for i in range(len(gs)) if ok[i] and not okA[i])
    brk = sum(1 for i in range(len(gs)) if okA[i] and not ok[i])
    r = {"acc": round(sum(ok)/len(gs),4), "interventions": n_int, "steps": n_steps,
         "step_err_rate": round(n_int/max(n_steps,1),3),   # 1.5B sai bao nhiêu % mỗi BƯỚC
         "fix_vs_A": fix, "break_vs_A": brk}
    print(f"[{tag}] {r}", flush=True)
    return r, ok

resB, okB = interleaved(small, tok15, "B interleaved 1.5B-verifier")
resC, okC = interleaved(big,   tok7,  "C interleaved 7B-verifier")

# ---------- D: post-hoc 7B verify (đối chứng) ----------
verD = gen(big, tok7, VERIFY_POST, [f"{q}\n\nProposed solution:\n{s}" for q,s in zip(qs,solA)], 1024)
ansD = [pred(v) for v in verD]
okD = [eq(a,g) for a,g in zip(ansD,gs)]
resD = {"acc": round(sum(okD)/len(gs),4),
        "fix_vs_A": sum(1 for i in range(len(gs)) if okD[i] and not okA[i]),
        "break_vs_A": sum(1 for i in range(len(gs)) if okA[i] and not okD[i])}
print(f"[D posthoc 7B] {resD}", flush=True)

# ---------- E: 7B CHIA VIỆC VỪA SỨC 1.5B, 1.5B thực thi từng bước ----------
# 7B được nói rõ người thi hành là model NHỎ -> phải cắt thành thao tác nguyên tử.
PLAN_SYS = ("You are planning for a WEAK small model that cannot do multi-step reasoning. "
            "Break the problem into the SMALLEST possible steps. Each step must be ONE elementary "
            "operation (a single arithmetic calculation or one substitution) that can be done with no reasoning. "
            "Output ONLY numbered lines '1. ...', '2. ...'. Do NOT compute the final answer.")
EXEC_SYS = ("Do ONLY the one instruction given, using the results so far. "
            "Reply with one short line: the result of that instruction. Nothing else.")
plansE = gen(big, tok7, PLAN_SYS, qs, 420)
stepsE = []
for p in plansE:
    ls = [l.strip() for l in p.split("\n") if re.match(r"^\s*\d+[\.\)]", l.strip())]
    stepsE.append([re.sub(r"^\s*\d+[\.\)]\s*", "", l) for l in ls][:MAX_STEPS])
workE = [""]*len(qs)
n_exec = 0
for k in range(MAX_STEPS):
    act = [i for i in range(len(qs)) if k < len(stepsE[i])]
    if not act: break
    res = gen(small, tok15, EXEC_SYS,
              [f"{qs[i]}\n\nResults so far:\n{workE[i] or '(none)'}\n\nInstruction: {stepsE[i][k]}" for i in act], 128)
    for pos, i in enumerate(act):
        workE[i] = (workE[i] + f"\n{k+1}. {stepsE[i][k]} -> {res[pos].strip().splitlines()[0][:200]}").strip()
        n_exec += 1
finE = gen(small, tok15, "Given the work, state the final answer in \\boxed{}.",
           [f"{qs[i]}\n\nWork:\n{workE[i]}" for i in range(len(qs))], 256)
ansE = [pred(t) for t in finE]
okE = [eq(a,g) for a,g in zip(ansE,gs)]
resE = {"acc": round(sum(okE)/len(gs),4),
        "avg_plan_steps": round(sum(len(s) for s in stepsE)/len(gs),2),
        "exec_calls": n_exec,
        "fix_vs_A": sum(1 for i in range(len(gs)) if okE[i] and not okA[i]),
        "break_vs_A": sum(1 for i in range(len(gs)) if okA[i] and not okE[i])}
print(f"[E 7B-plans-atomic + 1.5B-executes] {resE}", flush=True)

out = {"n": len(gs),
       "A_noverify": {"acc": round(sum(okA)/len(gs),4)},
       "B_interleaved_1p5B": resB,
       "C_interleaved_7B": resC,
       "D_posthoc_7B": resD,
       "E_7Bplan_atomic_1p5Bexec": resE}
print("SUMMARY", json.dumps(out), flush=True)
json.dump(out, open("/kaggle/working/summary.json","w"), indent=2)
