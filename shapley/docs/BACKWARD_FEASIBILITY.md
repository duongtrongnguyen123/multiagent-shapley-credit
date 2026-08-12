# Khảo sát: backward reasoning có khả thi trên GSM8K/MATH không?

Trước khi thiết kế backward-chaining Planner, khảo sát cấu trúc câu hỏi thật trên n=150 mỗi task
(từ traces solvejudge — cùng bộ câu dùng trong pipeline).

## GSM8K (n=150) — RẤT thuận lợi cho backward

| chỉ số | giá trị |
|---|---|
| có hình/diagram | 0 (0%) |
| có dấu `?` (mục tiêu rõ) | 143 (95%) |
| avg số câu | 3.4 |
| avg số liệu | 3.6 |
| phân bố số câu | 2 câu: 28, 3 câu: 61, 4 câu: 41 |

**Kết luận:** GSM8K gần như lý tưởng cho backward — câu hỏi luôn kết thúc bằng câu hỏi rõ ràng
("How much...?", "How many...?"), nhiều dữ kiện số, multi-step có thứ tự tính toán tự nhiên.
Backward: "để tính [đáp án] → cần [giá trị A, B] → A từ [dữ kiện X], B từ [dữ kiện Y]".

## MATH (n=150) — KHÓ hơn nhiều, 39% không backward-able rõ ràng

| chỉ số | giá trị |
|---|---|
| có hình/diagram (Asymptote/code) | 11 (7%) — không text-only |
| có dấu `?` | 76 (51%) |
| avg số câu | 1.8 (ngắn, mật độ cao) |
| avg số liệu | 7.3 |

**Phân loại câu hỏi MATH:**

| loại | n | % | backward khả thi? |
|---|---|---|---|
| khác (đại số trừu tượng, hàm, tổng vô hạn...) | 58 | 39% | ❌ khó — mục tiêu là biểu thức/biến, không phải "số" |
| tính số (convert/find number/value) | 43 | 29% | ✅ tốt |
| giá trị biểu thức (express/in terms of) | 15 | 10% | ⚠️ trung bình |
| hình học đo độ | 15 | 10% | ✅ tốt (có số) |
| số học (divisors/prime/integer) | 13 | 9% | ✅ tốt |
| tìm x đại số | 5 | 3% | ⚠️ |
| chứng minh/tồn tại | 1 | 1% | ❌ |

**Kết luận MATH:** chỉ ~48% (tính số + hình học + số học) có mục tiêu "số" rõ để backward. **39%
thuộc loại đại số trừu tượng** (định nghĩa hàm, tổng vô hạn, đa thức) — "backward từ cái gì?" không
xác định được đơn giản, vì đáp án là biểu thức chứ không phải số. 7% có hình (không text-only).

## Ý nghĩa cho thiết kế backward Planner

**GSM8K — đáng làm.** Backward chaining tự nhiên, mọi câu đều có target số rõ. Kỳ vọng plan
backward sẽ liệt kê đúng thứ tự tính toán → giảm lỗi Solver.

**MATH — cần prompt backward linh hoạt.** Không thể ép mọi câu theo "cần biết cái gì → số".
Với câu đại số trừu tượng, backward nên là "cần xác định biểu thức trung gian nào". Có thể:

- **Option A**: backward plan chỉ áp dụng cho câu có target số; câu khác giữ forward.
- **Option B**: backward prompt dùng ngôn ngữ tổng quát ("what intermediate quantity must be
  determined") — áp dụng được cho cả biểu thức.

**Đề xuất:** vì 39% MATH khó backward, **backward prompt nên được thiết kế chung cho cả hai**
nhưng kỳ vọng lợi ích rõ nhất ở GSM8K (95% target rõ). Trên MATH, backward có thể không cải thiện
nhiều — đó là kết quả hợp lệ cần đo, không phải lý do bỏ cuộc.

## Giới hạn

- Khảo sát trên 150 câu/task (subset n=150 của pipeline), không phải toàn bộ 500.
- Phân loại MATH heuristic (regex) — có thể lệch vài %, đủ để định hướng.
- Không đo "độ khó backward" chính xác — chỉ cấu trúc bề mặt.