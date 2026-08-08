# Baseline multi-agent trên GSM8K/MATH — literature nói gì, và ta đứng ở đâu

Tra cứu để định vị kết quả của dự án. Điểm bất ngờ: **literature 2025-2026 đã hội tụ về đúng
kết luận mà ta đo được độc lập** — và bằng nhiều lối vào khác nhau.

## Số liệu công bố

| nguồn | model | task | CoT | Self-Consistency | Multi-Agent Debate |
|---|---|---|---|---|---|
| ICLR Blogpost 2025 | GPT-4o-mini | GSM8K | 93.60 | **95.67** | 94.93 |
| ICLR Blogpost 2025 | Llama3.1-8b | GSM8K | 80.13 | 79.53 | **63.87** |
| ICLR Blogpost 2025 | GPT-4o-mini | MATH | 72.87 | 73.96 | **75.40** |
| ICLR Blogpost 2025 | Llama3.1-8b | MATH | 40.13 | 30.04 | **40.20** |
| A-HMAD (2025) | — | GSM8K | 77.0 | — | 84.0 → **90.2** |

Hai điều đọc được ngay:

1. **Debate thua Self-Consistency ở 3/4 ô.** Chỉ thắng ở MATH GPT-4o-mini (+1.4đ).
2. **Debate sụp ở model nhỏ**: Llama3.1-8b GSM8K từ 80.13 (CoT) xuống **63.87** — mất 16 điểm.
   Khớp chính xác với những gì ta đo ở 1.5B.

## Ba kết luận của literature trùng với đo đạc của ta

### (1) "Bỏ phiếu chiếm phần lớn lợi ích được quy cho debate"

Đây gần như nguyên văn kết luận của ta ở `EXTRA_PASS_FINDING.md`:

| | ta đo (MATH 1.5B) |
|---|---|
| `agg3` (LLM chọn) | .467 |
| **`vote5`** (bỏ phiếu cơ học) | **.507** |
| `agg5` (LLM, 5 ứng viên) | .460 |

Literature: *"majority voting alone accounts for most of the performance gains attributed to
multi-agent debate"* và *"vanilla MAD often underperforms a simple majority vote despite
incurring substantially higher computational cost"*.

### (2) Ở cùng ngân sách compute thì debate thua

`DEBATE_PLANNER.md` của ta: `debate` cần **10 lượt gọi/câu** so với 4 của `sampling`, và nhánh
`sampling` không nhích được gì so với `single`.

Literature: *"multi-agent debate significantly underperforms simple self-consistency using
majority voting when given an equivalent number of responses"* và *"current MAD frameworks may
not effectively utilize larger inference budgets"* — tăng compute không tăng accuracy.

### (3) Team đồng nhất không có phân công thì không hưởng lợi

`ROLE_SPECIALIZATION.md` của ta cho thấy ở 1.5B, phân công lao động **sụp đổ**: Planner giải hộ
(34.7% kế hoạch chứa đáp án), Solver chép (62% lượt không sinh số mới), Aggregator chép Verifier
(73-100%).

Literature: *"homogeneous teams without structured roles do not benefit from unguided peer
exchange"* và *"under homogeneous agents and unweighted belief updates, debate preserves expected
correctness over time"* — tức về mặt toán học, debate giữa các agent giống nhau **không thể**
tốt hơn bỏ phiếu.

## Ta có gì mà literature chưa có

Ba điểm dự án này đi xa hơn:

**(a) Cơ chế ở mức từng câu, không chỉ accuracy tổng.** Literature báo *"debate thua voting"*.
Ta đo được **vì sao**: Aggregator chép ứng viên cuối 65-100% số câu và sinh đáp án mới-và-đúng
đúng 3 lần trên 500 câu (`AGGREGATOR_EXPLAINED.md`). Đó là chép, không phải đếm phiếu.

**(b) Mẫu số bị pha loãng.** `DIFFICULTY_STRATA.md`: **57% số câu không thể có hiệu ứng** — 32%
không mẫu nào đúng, 25% mọi mẫu đều đúng. Hiệu ứng thật +21.5 điểm trên tầng giữa hiện ra thành
+9.3 trên toàn tập. **Chưa thấy paper nào phân tầng kiểu này**, mà nó giải thích tại sao rất
nhiều kết quả trong literature nằm ở mức 1-3 điểm và khó tái lập.

**(c) Chuyên biệt hóa là có điều kiện, đo bằng hành vi.** Literature nói *"homogeneous teams
không hưởng lợi"* nhưng không đo **các vai có thật sự khác nhau không**. Ta đo trực tiếp và thấy
Planner/Solver **hồi phục ở 7B** (rò rỉ đáp án 34.7% → 4.0%) trong khi Aggregator thì **không**
(chép nhiều hơn: 73% → 97%).

## Điều literature xác nhận mà ta nên bớt tự tin

Kết quả `debate` của ta (kernel chết vì quota, không có dữ liệu) hóa ra **không mất mát nhiều**:
literature đã cho thấy debate thua voting ở cùng ngân sách, và sụp ở model nhỏ. Quyết định dừng
hướng đó là đúng, và giờ có thêm cơ sở ngoài dự án.

Ngược lại, một điều **cần cẩn thận**: có paper báo debate **thắng lớn** (A-HMAD 90.2 vs 77.0 CoT;
post-training MAD +27.6% GSM8K). Những kết quả này thường (i) dùng model lớn hơn nhiều, (ii) so
với baseline yếu (CoT một lần, không phải self-consistency cùng ngân sách). Đúng loại so sánh mà
main đã cảnh báo: *"multi-agent papers thường benchmark với single-call cùng model — dễ thắng —
và hiếm khi so với model lớn hơn ở compute tương đương"*.

## Nguồn

- [When and Why Does Multi-Agent Debate Fail and Does It Really Underperform?](https://arxiv.org/html/2510.20963v2)
- [Multi-LLM-Agents Debate — Performance, Efficiency, and Scaling Challenges (ICLR Blogposts 2025)](https://d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/)
- [Improving Factuality and Reasoning in Language Models through Multiagent Debate](https://openreview.net/pdf?id=zj7YuTE4t8)
- [The Cost of Consensus: Isolated Self-Correction Prevails Over Unguided Homogeneous Multi-Agent Debate](https://arxiv.org/html/2605.00914v1)
- [Stop Overvaluing Multi-Agent Debate — We Must Rethink Evaluation and Embrace Model Heterogeneity](https://www.alphaxiv.org/overview/2502.08788v3)
- [Voting or Consensus? Decision-Making in Multi-Agent Debate](https://arxiv.org/pdf/2502.19130)
- [Adaptive heterogeneous multi-agent debate (A-HMAD)](https://link.springer.com/article/10.1007/s44443-025-00353-3)

## Giới hạn của việc tra cứu này

Các con số trên lấy từ abstract/blogpost, **chưa kiểm chứng bằng cách chạy lại**. Dự án này đã ba
lần phát hiện số công bố không tái lập được (lỗi normalizer `fc2f429`, reuse 0% ở `RESULTS.md`,
và chính con số copycat MATH 6.5%) — nên nên coi đây là **định vị**, không phải bằng chứng.
