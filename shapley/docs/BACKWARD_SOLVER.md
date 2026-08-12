# Backward-aware Solver: dạy Solver giải backward plan (leaf → target)

`BACKWARD_REASONING.md` kết luận backward plan không giúp (1.5B & 7B) — nhưng ở đó **Solver vẫn
dùng prompt cũ** ("solve step by step"), chỉ Planner đổi. Giả thuyết vòng này: **Solver không biết
dùng backward plan** vì prompt của nó không hướng dẫn. Sửa: Solver backward-aware (prompt "start
from leaf → sub-goal → target" + 1 few-shot ví dụ) chỉ áp cho nhánh backward; nhánh forward giữ
Solver cũ (để so công bằng). 2 GPU song song, n=150 mỗi ô.

## Kết quả (1.5B) — so với v2 (chỉ đổi Planner)

| kernel | Δ v2 | Δ bwsolver | thay đổi |
|---|---|---|---|
| GSM8K × PSVA | −.047 | **−.033** | +1.4 |
| GSM8K × solve-judge | −.020 | **+.007** | **+2.7 (đảo dấu)** |
| MATH × PSVA | +.007 | **−.080** | −8.7 |
| MATH × solve-judge | −.073 | **−.113** | −4.0 |

Tham chiếu: forward (Solver gốc) là baseline cố định.

## Đọc kết quả — pattern NGƯỢC nhau theo độ khó

**Trên GSM8K (bài dễ): backward-aware Solver GIÚP.**
- solve-judge: −.020 → **+.007** (đảo dấu — lần đầu backward thắng forward trên 1.5B)
- psva: −.047 → −.033 (cải thiện +1.4)
⇒ 1.5B học được cách giải backward plan khi bài đơn giản đủ.

**Trên MATH (bài khó): backward-aware Solver HẠI — tệ hơn cả v2.**
- psva: +.007 → **−.080** (mất 8.7 điểm — ô v2 vốn là backward thắng duy nhất giờ thành thua)
- solve-judge: −.073 → **−.113** (tệ nhất toàn dự án)
⇒ Prompt "start from leaf" khiến Solver 1.5B mất hướng trên bài khó: MATH không có "leaf số"
rõ ràng (đại số trừu tượng), ép leaf→target làm lời giải loạn.

## Kết luận

**Backward-aware Solver không cứu được backward reasoning.** Nó giúp chút trên GSM8K (Solver
tận dụng được chain đơn giản) nhưng HẠI nặng trên MATH — nơi vốn là mục tiêu chính. Pattern:
**hiệu quả của Solver backward-aware chia theo độ khó câu** — ngược chiều với mong muốn (cần nhất
ở chỗ khó thì hại nhất).

Cùng họ với các null khác: thay prompt ở bất kỳ tầng nào (Planner hay Solver) không chuyển thành
accuracy. Backward reasoning đóng lại: **không có cấu hình nào (prompt Planner, prompt Solver,
1.5B/7B) làm backward thắng forward đáng kể.**

## Giới hạn

- n=150 mỗi ô, một lần chạy.
- MATH bwsolver tệ (−.080, −.113) vượt sàn nhiễu — tín hiệu rõ.
- GSM8K bwsolver cải thiện nhỏ (+1.4, +2.7) trong sàn nhiễu, nhưng cùng hướng (backward hết kém).