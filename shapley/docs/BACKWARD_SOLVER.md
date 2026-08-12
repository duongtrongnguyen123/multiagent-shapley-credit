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

## Phân tích trace MATH solve-judge (n=150) — vì sao tệ nhất

So v2 (Solver cũ) với bwsolver (Solver backward-aware):

| | v2 | bwsolver |
|---|---|---|
| fwd_ok | 80 | 77 |
| bwd_ok | 69 | **60** |
| both đúng | 55 | 49 |
| broke (fwd đúng, bwd sai) | 25 | **28** |
| rescued (fwd sai, bwd đúng) | 14 | **11** |
| net | −11 | **−17** |

BWSolver hại theo hai cách: **bwd_ok giảm 69 → 60** (Solver mới giải sai nhiều hơn), và
**rescued giảm 14 → 11** (cứu được ít hơn). fwd_ok cũng giảm 80 → 77 (nhiễu — forward dùng Solver
cũ không đổi).

**Cơ chế (độ dài lời giải theo nhóm):**

| nhóm | plan fwd/bwd | sol fwd/bwd |
|---|---|---|
| both (n=49) | 942/673 | 823/**625** |
| broke (n=28) | 1156/848 | 975/**1030** |
| neither (n=62) | 1253/1003 | 1262/**1192** |

- Backward plan **ngắn hơn** forward (673–1003 vs 942–1253) — Planner backward gọn.
- Solver backward-aware viết lời giải **NGẮN hơn** forward ở nhóm both (625 vs 823): prompt
  "leaf→target" khiến nó **bỏ bớt bước** (tắt theo chain).
- Nhưng ở **broke**, Solver bwd viết **DÀI hơn** (1030 vs 975): leaf→target ép nó loay hoay trên
  bài không có leaf rõ.

**Root cause:** prompt "start from the leaf (givens) → sub-goal → target" **giả định có leaf số
cụ thể** — đúng GSM8K, **sai MATH đại số trừu tượng** (target là biểu thức/biến, không có leaf).
Solver 1.5B ép theo hướng dẫn đó → lời giải không tự nhiên, bỏ/nhầm bước → giải sai nhiều hơn.
Đây là phát hiện cốt lõi: **Solver backward-aware không cứu được vì MATH vốn không hợp backward
structure**, không phải vì prompt Solver kém.

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