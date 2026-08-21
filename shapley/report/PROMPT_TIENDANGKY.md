# Đoạn hướng dẫn thay cách diễn đạt "tiền đăng ký" (đưa nguyên văn cho AI)

---

Trong `report/BAO_CAO.tex`, cụm **"tiền đăng ký"** xuất hiện 17 chỗ và nghe nặng nề. Hãy thay
bằng cách diễn đạt tự nhiên hơn, **giữ nguyên thông tin**.

## Thông tin cần giữ

Cụm này cho người đọc biết: thí nghiệm đó có **thiết kế và tiêu chí kết luận được chốt trước khi
chạy**, nên kết quả không phải thứ được chọn ra sau khi đã nhìn dữ liệu. Nó phân biệt với các
quan sát **thăm dò** — chạy trước rồi mới diễn giải. Người đọc cần biết thí nghiệm nào thuộc
loại nào, vì hai loại có độ tin cậy khác nhau.

## Từ thay thế

Dùng cặp chuẩn của nghiên cứu thực nghiệm: **khẳng định** (confirmatory) so với **thăm dò**
(exploratory). Bài đã dùng "thăm dò" sẵn ở một chỗ nên cặp này khớp liền. Có thể diễn đạt vòng
bằng "chốt thiết kế trước khi chạy", "tiêu chí đặt trước", tuỳ câu cho tự nhiên — không cần dùng
đúng một từ ở mọi chỗ.

## Nhóm 1 — nhãn gắn cho một thí nghiệm cụ thể

Các dòng 70, 115, 152, 586, 598, 755, 769, 820, 832, 981, 1085. Ví dụ:

- `Thí nghiệm tiếp xúc (tiền đăng ký, MATH-500)`
  → `Thí nghiệm tiếp xúc trên MATH-500 (thiết kế khẳng định)`
- `Đây là thí nghiệm chính của khảo sát (tiền đăng ký; chọn MATH-500 để đổi miền…)`
  → `Đây là thí nghiệm khẳng định chính của khảo sát; chọn MATH-500 để đổi miền…`
- `Thiết kế tách (tiền đăng ký): 6 model, 15 cặp có hướng…`
  → `Thiết kế tách, chốt trước khi chạy: 6 model, 15 cặp có hướng…`
- `Hai bằng chứng nhân quả… Một (tiền đăng ký): chỉ cần bỏ dòng cấm…`
  → `Hai bằng chứng nhân quả… Một (thí nghiệm khẳng định): chỉ cần bỏ dòng cấm…`
- `Hai cột MBPP là phân rã hậu nghiệm (mức B); cột MATH là thí nghiệm tiền đăng ký (mức A).`
  → `Hai cột MBPP là phân rã hậu nghiệm (mức B); cột MATH là thí nghiệm khẳng định (mức A).`

## Nhóm 2 — mô tả quy trình chung

Các dòng 84, 164, 998, 1145, 1214, 1222. Ở nhóm này hãy **rút gọn**, đừng liệt kê tên quy trình:

- `Toàn bộ số liệu đi kèm quy trình chống tự đánh lừa (tiền đăng ký, điều kiện hợp lệ, niêm
  phong kết quả) mô tả ở §4`
  → `Cách chúng tôi kiểm soát độ tin cậy của từng phép đo được mô tả ở §4`
- `mỗi phương pháp có tiền đăng ký hoặc cổng hiệu lực`
  → `mỗi phương pháp có tiêu chí đánh giá đặt trước`
- `Hai chuẩn kiểm chứng của hai khối (fold so với tiền đăng ký) chưa kiểm chéo.`
  → `Hai khối dùng hai chuẩn kiểm chứng khác nhau và chưa được kiểm chéo.`

## Ràng buộc

- **Không đổi con số nào**, không đổi ký hiệu toán, không đổi `\label` / `\ref` / `\cite` và các
  macro `\dceil`, `\dhonest`, `\CEIL`, `\acc`, `\mucB`.
- **Không đổi thí nghiệm nào mang nhãn nào** — chỉ đổi cách gọi, không chuyển một thí nghiệm
  từ khẳng định sang thăm dò hay ngược lại.
- Giữ nguyên nhãn **mức A / mức B**.
- Giữ giọng trung tính, không thêm tính từ đánh giá.

## Đầu ra

Ghi đè file, rồi liệt kê mỗi chỗ sửa một dòng: `dòng ~N: "cũ" → "mới"`.

---

## Kiểm sau khi AI trả kết quả

```bash
tectonic BAO_CAO.tex                       # 0 lỗi
grep -c "tiền đăng ký" BAO_CAO.tex         # kỳ vọng 0
grep -c "khẳng định\|thăm dò" BAO_CAO.tex  # kỳ vọng ~17
```

Rồi so số liệu bằng script trong `PROMPT_VANPHONG.md` bước 3.
