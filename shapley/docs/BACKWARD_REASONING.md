# Backward reasoning Planner — có giúp pipeline không?

Thay đổi cách Planner lập plan: thay vì forward (liệt kê bước từ đề), dùng **backward chaining**
(reason từ target cần tính, lần ngược đến các dữ kiện cho sẵn). Chạy forward & backward **song
song trên 2 T4** (mỗi GPU 1 model 1.5B, cùng bài, cùng seed) — mock test xác nhận khả thi
(2 GPU, 3.1GB/model).

## Khảo sát khả thi (`BACKWARD_FEASIBILITY.md`)

- **GSM8K**: 95% câu có `?` target rõ, 0% hình → backward tự nhiên.
- **MATH**: chỉ 51% có `?`, 39% đại số trừu tượng (target là biểu thức không phải số) → backward
  khó hơn, cần prompt linh hoạt.

## Hai prompt backward

- **v1**: chỉ mô tả ý tưởng ("reason BACKWARD... expanding until leaf given") + câu tự phản bội
  "output in forward computation order". → Model KHÔNG lần ngược, plan ≈ forward.
- **v2**: bỏ câu tự phản bội, thêm few-shot backward chain thật, ép cấu trúc target→subgoal→given.
  → Model sinh backward plan THẬT (xác nhận qua trace: gọn, đúng thứ tự tính).

## Kết quả

### Bảng v1 (prompt mô tả, plan ≈ forward)

| kernel | forward | backward | Δ |
|---|---|---|---|
| GSM8K × PSVA | .7000 | .6933 | **−.007** |
| GSM8K × solve-judge | .6267 | .6533 | **+.027** |
| MATH × PSVA | .4733 | .4600 | **−.013** |
| MATH × solve-judge | .4867 | .4800 | **−.007** |

### Bảng v2 (prompt backward thật)

| kernel | forward | backward | Δ |
|---|---|---|---|
| GSM8K × PSVA | .7000 | .6533 | **−.047** |
| GSM8K × solve-judge | .6600 | .6400 | **−.020** |
| MATH × PSVA | .4733 | .4800 | **+.007** |
| MATH × solve-judge | .5333 | .4600 | **−.073** |

## Vì sao backward tệ (phân tích trace MATH solve-judge v2)

4 nhóm trace (n=150): both-đúng 55, **broke 25**, rescued 14, neither 56.

1. **Backward plan ngắn hơn forward ở mọi nhóm** (689–1026 vs 989–1275) — prompt v2 ép gọn, bỏ
   context chi tiết Solver 1.5B cần.
2. **Lời giải backward DÀI hơn forward rõ rệt** ở nhóm broke (1175 vs 969), rescued (1134 vs 859),
   neither (1378 vs 1252). Solver nhận plan gọn → tự khai triển thêm, viết dài hơn, loay hoay hơn
   → dễ sai hơn.
3. **broke 25 > rescued 14** → net −11 câu = nguồn của −7.3 điểm.
4. Backward marker chỉ ~một nửa plan backward (5/14 → 23/56) — prompt v2 chưa ép 100% backward,
   nhưng dù có backward, kết quả vẫn tệ.

## Kết luận

**Backward reasoning KHÔNG giúp pipeline nhỏ 1.5B.** Plan backward "đẹp" (gọn, đúng thứ tự tính)
nhưng Solver 1.5B không hưởng lợi: nó cần plan forward chi tiết để bám, plan gọn khiến nó tự
khai triển → lời giải dài, loay hoay, dễ sai. Chỉ ô MATH × PSVA v2 cho backward +.007 (hòa, trong
nhiễu).

Đây là kết quả null đáng ghi nhận: **backward chaining về lý thuyết đúng hướng nhưng không phù
hợp năng lực của Solver nhỏ** — thêm một lần nữa khẳng định mẫu hình của dự án: thay đổi cấu trúc
plan/prompt không chuyển thành accuracy (cùng họ với prompt-swap, role order).

## Giới hạn

- n=150 mỗi ô, một lần chạy. Δ đều dưới/trong sàn nhiễu ~5 điểm (trừ MATH solve-judge v2 −7.3
  vượt nhiễu).
- **Đang chạy bổ sung: backward trên 7B** (cả pipeline 7B 4-bit, prompt v2, 4 ô) — để kiểm tra
  liệu Solver mạnh hơn có dùng được plan backward gọn không. Kết quả sẽ cập nhật sau.