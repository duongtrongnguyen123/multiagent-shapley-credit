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
