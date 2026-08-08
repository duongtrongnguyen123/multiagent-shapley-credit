# Related work: multi-agent pipeline TUYẾN TÍNH (không debate)

Bổ sung cho `RELATED_BASELINES.md` (vốn chỉ tra debate/self-consistency). Ở đây tìm các hệ có
**vai trò nối tiếp** như P→S→V→A của ta — tức cùng họ kiến trúc, không phải debate.

## Các hệ cùng họ

| hệ | kiến trúc | model | benchmark |
|---|---|---|---|
| **MAS_RPSV** (trong MASPRM) | Reader → Planner → Solver → Verifier | 1.5B, 7B | GSM8K, MATH |
| **SHARP** | Planner → Workers (tuần tự, có tool) | Qwen3 0.6B–8B | MuSiQue, GAIA, DocMath — **không có GSM8K/MATH** |
| Mathematical Analyst → Inspector → Math Solver → Decision Maker | chuỗi tuần tự 4 vai | — | toán |
| Planner / Actor / Corrector / Verifier | chia vai qua nhiều model | — | ra quyết định tuần tự |

**MAS_RPSV là hệ gần ta nhất**: 4 vai nối tiếp, có Planner/Solver/Verifier, chạy trên **cùng cỡ
model (1.5B và 7B)** và **cùng benchmark (GSM8K, MATH)**. Khác biệt: nó có *Reader* thay cho
*Aggregator* của ta.

## SHARP — gần nhất về phương pháp, và xác nhận phát hiện chính của ta

SHARP dùng **Shapley credit** cho multi-agent LLM, đúng công cụ của dự án này.

**Điểm khác về phương pháp:** SHARP dùng **xấp xỉ counterfactual** (`credit = R(τ) − R(τ\m)`,
tức leave-one-out một bước), còn ta tính **Shapley chính xác trên toàn bộ 2⁴ = 16 tổ hợp**.
Leave-one-out bỏ sót tương tác giữa các vai — chính thứ mà `interaction.py` của ta đo được là
mạnh (S/V/A thay thế nhau, I ≈ −0.21..−0.27).

**Và họ báo cùng phát hiện với ta:**

> *"useful subagents remain a minority of total calls in the tested systems"*
> — chỉ **12.96%** lời gọi subagent có ích, **4.40%** gây hại.

So với đo đạc của ta:

| | SHARP | ta (`ROLE_SPECIALIZATION.md`) |
|---|---|---|
| tỉ lệ vai có đóng góp | 12.96% lời gọi có ích | 2/4 vai thực sự tính toán |
| vai gây hại | 4.40% | Verifier cứu 17 / phá 18 (ròng 0) |
| kết luận | *"role specialization failure"* | *"phân công lao động sụp đổ ở model yếu"* |

Hai nghiên cứu độc lập, hai benchmark khác nhau (MuSiQue/GAIA vs GSM8K/MATH), cùng kết luận.

## Ta có gì mà các hệ này không có

**(a) Shapley chính xác thay vì leave-one-out.** SHARP xấp xỉ bằng ablation một bước. Ta chạy
đủ 16 tổ hợp, nên đo được **tương tác** — và phát hiện S/V/A là *substitute* mạnh chứ không
cộng dồn. LOO không thấy được điều này.

**(b) Chỉ số hành vi, không chỉ credit.** SHARP đếm *"lời gọi có ích"* bằng accuracy. Ta đo
**vai đó thực sự làm gì**: Planner có giải hộ không (34.7% kế hoạch chứa đáp án), Solver có chép
không (62% lượt không sinh số mới), Aggregator có tính không (3 đáp án mới-đúng trên 500 câu).
Hai câu hỏi khác nhau — *"vai này có giúp không"* vs *"vai này có làm đúng việc của nó không"*.

**(c) Phân tầng mẫu số.** `DIFFICULTY_STRATA.md`: 57% số câu không thể có hiệu ứng. Chưa thấy
hệ nào trong nhóm này báo cáo điều tương tự, mà nó ảnh hưởng trực tiếp tới cách đọc mọi con số
credit — bao gồm cả 12.96% của SHARP.

**(d) MAS_RPSV không có phân tích đóng góp từng vai.** Nó dùng đúng kiến trúc gần ta nhất, trên
đúng model và benchmark, nhưng (theo abstract) **không** ablation từng vai. Đây chính là khoảng
trống dự án này lấp.

## Điều cần cẩn thận

Số của MASPRM (1.5B: +2.0–3.0 điểm; 7B: +4.1–14.5) là gain của **process reward model**, không
phải của pipeline RPSV trần. Không so trực tiếp được với con số của ta.

Và như `RELATED_BASELINES.md` đã ghi: các số này lấy từ abstract, **chưa kiểm chứng bằng cách
chạy lại**.

## Nguồn

- [MASPRM: Multi-Agent System Process Reward Model](https://arxiv.org/abs/2510.24803) — chứa MAS_RPSV
- [SHARP: Shapley Credit-based Optimization for Multi-Agent System](https://arxiv.org/html/2602.08335v2)
- [Shapley-Coop: Credit Assignment for Emergent Cooperation](https://openreview.net/pdf?id=HnJ1UkuJXS)
- [Who Gets the Reward & Who Gets the Blame? Evaluation-Aligned Training Signals for Multi-LLM Agents](https://arxiv.org/html/2511.10687v3)
- [Unifying Temporal and Structural Credit Assignment in LLM-Based Multi-Agent Prompt Optimization](https://arxiv.org/pdf/2605.30227)
- [Unlocking the Power of Multi-Agent LLM for Reasoning](https://arxiv.org/pdf/2511.02303)
