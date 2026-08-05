# Đăng ký trước (pre-registration) — thí nghiệm CAN THIỆP "ép trình bày lời giải"

**Viết TRƯỚC khi có kết quả.** Mục đích: khoá sẵn cách diễn giải, để kết quả nào cũng
không thể "uốn" theo ý muốn sau khi đã nhìn thấy số.

## Giả thuyết
Verifier phá đáp án đúng VÌ Solver không trình bày lời giải (chỉ ghi "The answer is X",
median 20 ký tự) -> Verifier không có gì để kiểm -> buộc phải tự giải lại -> lỗi riêng
của nó thành đáp án cuối.

Bằng chứng quan sát (chưa phải nhân quả): 11/103 phá khi không trình bày; 0/28 khi có.

## Ba nhánh
- **A**: Solver trả lời trơ (prompt gốc) — Verifier thấy đáp án trơ
- **B**: Solver bị ép trình bày — Verifier thấy TOÀN BỘ lời giải
- **C**: CÙNG lời giải của B — nhưng Verifier chỉ được thấy đáp án (đã xoá phần trình bày)

B vs C là đối chứng cặp: lời giải Y HỆT, chỉ khác Verifier có được nhìn hay không.

## Cam kết diễn giải (khoá trước)

| Kết quả | Kết luận BẮT BUỘC phải rút |
|---|---|
| break(B) thấp, break(C) cao | TÍNH NHÌN THẤY ĐƯỢC là nguyên nhân. Khẳng định nhân quả. |
| break(B) ≈ break(C), cả hai < A | KHÔNG phải do nhìn thấy; ép trình bày làm LỜI GIẢI tốt hơn. Cơ chế khác. |
| break(B) ≈ break(C) ≈ break(A) | **GIẢ THUYẾT SAI.** Tương quan quan sát được là do nhiễu (model trình bày ở đúng những bài nó vốn làm tốt). Chuyển hướng: biến thật là ĐỘ KHÓ BÀI, không phải tính nhìn thấy. |
| median_sol_len(B) ≈ median_sol_len(A) | **THÍ NGHIỆM VÔ HIỆU** — can thiệp không tác động được lên hành vi. Không được coi là phát hiện. Phải làm lại với can thiệp mạnh hơn. |

## Chỉ số chính
`break_rate = breaks / solver_correct` (không phải accuracy).
Kiểm tra can thiệp có hiệu lực: `median_sol_len`, `pct_under_200_chars`.

## Điều KHÔNG phụ thuộc kết quả này
Các quan sát sau đã đo xong, thí nghiệm này không thể bác bỏ:
Verifier phá đáp án đúng (4 thiết lập độc lập); verify bằng chạy test không phá lần nào
(0/0/0 qua 3 vòng); 1.5B+7B post-hoc thắng (+.18, 9 sửa/0 phá); verifier LLM chỉ bắt
15-17% lỗi thật trên code; feedback bão hoà sau 1 vòng.

---

# Đăng ký trước #2 — XÁC NHẬN "VERIFIER BỊ BỊT MẮT" + KHỬ NHIỄU BỘ TỔNG HỢP
**Viết TRƯỚC khi chạy.** Hai phát hiện hậu nghiệm cần kiểm chứng có đăng ký trước.

## Giả thuyết H1 — tính nhìn thấy lời giải BÓP NGHẸT khả năng bắt lỗi
Verifier ĐỌC ĐƯỢC lời giải của Solver sẽ bắt được ÍT lỗi hơn hẳn so với khi chỉ thấy đáp án.
Cơ chế đề xuất: anchoring/sycophancy — thấy suy luận trôi chảy thì bị thuyết phục, thôi phản đối.
Số hậu nghiệm (CÙNG mẻ, chưa đăng ký): giá trị gia tăng của verify
  THẤY lời giải: -0.8 / +0.4 / +1.3 điểm | BỊT MẮT: +10.8 / +8.0 / +6.7 điểm
  fixes: 10->40, 9->26, 6->20

### Cam kết diễn giải (khoá trước khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| fixes(blind) > fixes(informed), cả 2 task, p<.05 | H1 XÁC NHẬN. Được phát biểu như KHẲNG ĐỊNH. |
| fixes(blind) ~ fixes(informed) | H1 BỊ BÁC. Hiệu ứng cũ là ngẫu nhiên của một mẻ. Phải ghi rõ đã bác. |
| ngược hướng (informed > blind) | H1 BỊ BÁC MẠNH. Rút lại toàn bộ diễn giải "anchoring". |
| chỉ 1 task có, 1 task không | KHÔNG kết luận chung. Ghi là "phụ thuộc task", cần thêm dữ liệu. |

### Nhánh MỚI để tách cơ chế (chưa từng chạy)
- **P (partial)**: Verifier thấy lời giải nhưng ĐÃ XOÁ đáp án cuối -> có suy luận, không có kết luận.
  Nếu P bắt lỗi tốt như blind => thủ phạm là ĐÁP ÁN (anchor số), không phải phần suy luận.
  Nếu P kém như informed => thủ phạm là PHẦN SUY LUẬN (bị thuyết phục bởi lập luận trôi chảy).
- **X (cross-check)**: Verifier thấy lời giải của MỘT BÀI KHÁC (đối chứng giả dược).
  Kiểm tra hiệu ứng có phải chỉ do "context dài hơn" hay không.

## Giả thuyết H2 — bộ tổng hợp LLM kém hơn bỏ phiếu KHI ĐƯỢC ĐỐI XỬ CÔNG BẰNG
Lần trước aggregator bị thiệt: KHÔNG có chỉ dẫn CoT, chỉ 384 token (so với 1024 của solver).
Lần này: CÙNG chỉ dẫn "step by step", CÙNG 1024 token.
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| vẫn đè lên đa số đúng >> cứu, p<.05 | H2 XÁC NHẬN kể cả khi công bằng. Được phát biểu mạnh. |
| khoảng cách thu hẹp rõ | Kết quả cũ PHẦN LỚN do NHIỄU PROMPT. Phải sửa lại phát biểu. |
| aggregator >= bỏ phiếu | H2 BỊ BÁC. Rút lại "sai loại bộ tổng hợp". |

## Chỉ số chính
H1: `fixes` và `verifier_acc - solver_acc` theo từng nhánh (CÙNG bộ lời giải).
H2: `llm_breaks_majority` vs `llm_fixes_majority`, và `llm_agg_acc` vs `maj@8`.
Kiểm tra hiệu lực: độ dài context mỗi nhánh phải khác nhau như thiết kế.

---

# Đăng ký trước #3 — (A) VERIFY CÓ CỔNG LỌC  (B) PLANNER CÓ BÓP NGHẸT SOLVER KHÔNG
**Viết TRƯỚC khi chạy.** Rút thẳng từ số đo của bl_g15.

## Xuất phát (ĐO ĐƯỢC ở bl_g15, GSM8K 1.5B, n=250, 158 bài đúng)
  I informed : 20 sửa /  6 phá  (+5.6 điểm)
  B blind    : 42 sửa / 23 phá  (+7.6 điểm)   <- sản lượng CAO, rủi ro CAO
  P giấu đáp : 15 sửa /  1 phá  (+5.6 điểm)   <- rủi ro CỰC THẤP, sản lượng thấp
Nhận xét: B và P bù trừ nhau. B biết CÁCH SỬA, P biết KHI NÀO nên động vào.

## (A) GIẢ THUYẾT H3 — TÁCH "KHI NÀO CAN THIỆP" KHỎI "CAN THIỆP THẾ NÀO"
Dùng P làm CỔNG (chỉ hỏi "phần suy luận này có lỗi không? YES/NO", KHÔNG cho thấy đáp án),
chỉ khi cổng báo YES mới cho B giải lại từ đầu.
Kỳ vọng: số SỬA gần B, số PHÁ gần P -> vượt cả hai.
Nhánh: N (không verify) | I (informed) | B (blind) | **G (có cổng)**

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| G có value_added > cả I và B | H3 XÁC NHẬN. Đây là ĐÓNG GÓP PHƯƠNG PHÁP, không chỉ phân tích. |
| G ~ B (phá nhiều như B) | Cổng KHÔNG lọc được. P an toàn chỉ vì nó LƯỜI, không vì nó chính xác. |
| G ~ P (sửa ít như P) | Cổng quá chặt, chặn luôn cả ca đáng sửa. Phải nới ngưỡng. |
| G kém cả hai | H3 BỊ BÁC. Ghi rõ đã bác, không diễn giải lại. |
Chỉ số phụ BẮT BUỘC báo: `gate_flag_rate` (cổng kêu YES bao nhiêu %),
`gate_precision` (trong số bị kêu, bao nhiêu THỰC SỰ sai) -> cho biết cổng lọc được thật hay không.

## (B) GIẢ THUYẾT H4 — PLANNER LÀM SOLVER NGỪNG TRÌNH BÀY
Quan sát CHÉO thí nghiệm (chưa kiểm soát): cùng prompt SOLVE,
  CÓ Planner -> median 18 ký tự (sw_g15) | KHÔNG Planner -> 600 ký tự (bl_g15).
Nếu đúng, đây là TƯƠNG TÁC ÂM giữa hai vai, và giải thích được vì sao Planner có Shapley thấp/âm.
Thí nghiệm CÓ KIỂM SOÁT: cùng model, cùng bài, cùng prompt SOLVE, chỉ bật/tắt Planner.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| median_len(có plan) << median_len(không plan), và acc giảm | H4 XÁC NHẬN. Planner gây hại qua việc bóp nghẹt trình bày. |
| median_len khác nhưng acc KHÔNG đổi | Planner đổi ĐỘ DÀI chứ không đổi CHẤT LƯỢNG. Không được nói "gây hại". |
| median_len ~ nhau | H4 BỊ BÁC. Chênh lệch 18 vs 600 là do yếu tố khác giữa 2 thí nghiệm, không phải Planner. |

## Chỉ số chính
H3: `value_added` từng nhánh + fixes/breaks + gate_flag_rate + gate_precision.
H4: `median_sol_len` và `solver_acc`, có/không Planner, trên CÙNG bài.
