# Introduction (bản nháp cho báo cáo)

> Khung mở đầu theo hướng NLP: bắt đầu bằng *ngôn ngữ & giao tiếp giữa agent*, coi Shapley
> chỉ là công cụ đo. Dùng bản tiếng Anh này cho paper; đoạn tóm tắt tiếng Việt ở cuối.

---

Large language models increasingly solve hard reasoning problems in **teams** rather than
alone. A now-common design assigns each model a role and lets them coordinate entirely
through **natural-language messages**: a *Planner* sketches an approach, a *Solver* works it
out, a *Verifier* checks the reasoning, and an *Aggregator* reconciles candidate answers into
a final one. This multi-agent pattern underlies popular methods such as debate,
self-refinement, and planner–solver–verifier pipelines.

But coordinating through language is double-edged. The very message that corrects a peer's
arithmetic slip can just as easily mislead a peer who was **already right** — a failure mode
tied to *sycophancy*, where a model abandons a correct answer to agree with a
confident-sounding peer. Whether a given role helps or hurts is therefore far from obvious,
and it is obscured by the metric the field reports: **end-to-end team accuracy**. A single
number cannot say which agent's message improved the answer, which merely rode along, and
which quietly corrupted it.

We ask a deliberately simple question — **who actually helps?** — and answer it by treating
the pipeline as a cooperative game and computing the exact **Shapley value** of each role:
its average marginal contribution to team accuracy over all subsets of active roles. On
**GSM8K** and **MATH-500**, with Qwen2.5 at two capacities (1.5B and 7B), we find:

- **Role importance reverses with task difficulty.** The Verifier ties the Solver as the most
  valuable role on easy problems (GSM8K), but is overtaken by the Aggregator on hard ones
  (MATH) — a weak verifier cannot repair a long, wrong solution, so *selecting* among diverse
  attempts beats *re-checking* them.
- **Net credit hides an agent's behavior.** The Planner's Shapley value reads as near-zero,
  yet a signed decomposition shows it is highly *chaotic* — fixing ~10% of answers while
  corrupting ~9% — a distinction standard credit assignment cannot make.
- These findings are **robust** to model capacity and to grader choice.

Our contribution is an **empirical audit**, not a new algorithm: we apply exact Shapley (with
a signed *fix/break* decomposition) to a controlled, role-based reasoning pipeline, and
release a fully reproducible framework for measuring agent-role contributions in multi-agent
LLM systems.

---

**Tóm tắt tiếng Việt (nếu báo cáo bằng tiếng Việt):** Các mô hình ngôn ngữ ngày càng giải toán
theo *đội*, phối hợp **qua các thông điệp ngôn ngữ tự nhiên**: Planner phác hướng, Solver giải,
Verifier kiểm tra, Aggregator chốt đáp án. Nhưng giao tiếp là con dao hai lưỡi — một thông điệp
có thể sửa lỗi cho bạn cùng đội, hoặc làm hỏng đáp án vốn đã đúng (*sycophancy*). *Vai trò nào
thực sự đóng góp?* — câu hỏi bị che bởi độ chính xác toàn đội. Chúng tôi trả lời bằng cách coi
pipeline như một trò chơi hợp tác và đo **giá trị Shapley** của từng vai trò, phát hiện: thứ
hạng vai trò **đảo theo độ khó** (Verifier dẫn ở GSM8K, Aggregator dẫn ở MATH); và φ net **che
giấu** hành vi (Planner ≈0 nhưng thực ra "hỗn loạn": sửa ~10%, phá ~9%). Đóng góp là một
**nghiên cứu thực nghiệm + công cụ tái lập**, không phải thuật toán mới.
