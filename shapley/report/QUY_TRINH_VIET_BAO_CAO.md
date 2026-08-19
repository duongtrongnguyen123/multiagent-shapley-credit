# Quy trình viết báo cáo

Ba tài liệu, ba chức năng: `BAO_CAO_CAU_TRUC.md` xác định **viết nội dung gì**;
`HUONG_DAN_CONG_TAC.md` xác định **được phép trích số liệu nào**; tài liệu này xác định
**trình tự thực hiện**.

Nếu chỉ đọc được một mục trước khi bắt đầu, nên đọc **§0 của `BAO_CAO_CAU_TRUC.md`**.

---

## Bước 0 — Thống nhất trước khi viết (cả nhóm, khoảng 30 phút)

- [ ] Cả ba thành viên đọc **§0 của `BAO_CAO_CAU_TRUC.md`** (luận điểm chính, khoảng một trang).
- [ ] Cả ba thành viên đọc **mục 1, 2, 3 của `HUONG_DAN_CONG_TAC.md`** (mức tin cậy, bảng số liệu
      đã chốt, các phát biểu cần tránh).
- [ ] Thống nhất **một câu luận điểm** và ghi vào đầu bản thảo. Mọi chương sau đó phải phục vụ câu này.
- [ ] Xác nhận ngôn ngữ nộp bài là tiếng Việt. Nếu yêu cầu nộp bằng tiếng Anh, việc dịch nên thực
      hiện **sau khi** nội dung đã hoàn chỉnh, không dịch song song với quá trình viết.

Bước này quan trọng vì ba khối công việc sử dụng hệ thuật ngữ khác nhau (`verifier gain`, `Δ_ceil`,
`cost per query`). Nếu không thống nhất trước, báo cáo sẽ đọc như ba tài liệu rời ghép lại.

---

## Bước 1 — Dựng khung rỗng (Nguyên, khoảng 1 giờ)

- [ ] Tạo `report/BAO_CAO.md` với đầy đủ 9 tiêu đề chương và phần phụ lục; mỗi mục ghi `TODO` kèm
      số trang dự kiến.
- [ ] Đưa luận điểm chính (§0) vào ngay dưới tiêu đề, dạng khối trích dẫn.
- [ ] Đưa bảng số liệu đã chốt (mục 2 của `HUONG_DAN_CONG_TAC.md`) vào phụ lục trước, để trong quá
      trình viết chỉ cần tham chiếu.

Hoàn thành khi mở tệp là thấy được toàn bộ bố cục báo cáo, dù nội dung chưa viết.

---

## Bước 2 — Viết song song (cả nhóm, khoảng 3–4 ngày)

Ba thành viên viết đồng thời, mỗi người phụ trách phần không phụ thuộc vào phần của người khác:

| Người | Chương phụ trách | Điều kiện bắt đầu |
|---|---|---|
| Đức | §2 Công trình liên quan | Không phụ thuộc; có thể bắt đầu ngay |
| Tùng Dương | §4 Thiết lập thí nghiệm và Hình 5 | Không phụ thuộc; có thể bắt đầu ngay |
| Nguyên | §3 Khung lý thuyết, sau đó §5.4–5.6, cuối cùng §6 | Theo đúng thứ tự này |

Thứ tự trong phần của Nguyên là bắt buộc: §3 (khung) trước, §5 (kết quả) tiếp theo, §6 (tổng hợp)
sau cùng. Viết §6 trước khi có §5 sẽ tạo ra phần lập luận không có số liệu chống đỡ.

### Cấu trúc mỗi mục kết quả

Mỗi mục trong §5 nên trình bày theo bốn phần:

1. **Câu hỏi** — mục này trả lời điều gì (một câu).
2. **Thiết kế** — cách đo và các điều kiện hợp lệ (hai đến ba câu).
3. **Số liệu** — bảng, kèm giá trị p hoặc khoảng tin cậy.
4. **Diễn giải** — ý nghĩa của kết quả, **và giới hạn của nó**.

Phần thứ tư là điểm phân biệt báo cáo này với một bản trình bày kết quả thông thường, không nên rút gọn.

---

## Bước 3 — Vẽ hình (thực hiện song song với Bước 2)

Danh sách hình ở cuối `BAO_CAO_CAU_TRUC.md`. Nếu thời gian hạn chế, ưu tiên Hình 2, 4, 6.

- [ ] Tất cả hình dùng chung một bảng màu và một cỡ chữ.
- [ ] Trục toạ độ ghi rõ đơn vị; mọi hiệu ứng đều kèm thanh sai số hoặc khoảng tin cậy.
- [ ] Chú thích hình phải đủ để hiểu độc lập, không cần đọc phần thân.

Hình 2 (hai đường ngược chiều thể hiện nghịch lý) là hình quan trọng nhất của báo cáo.

---

## Bước 4 — Kiểm tra số liệu (bắt buộc, trước khi ghép)

- [ ] Mỗi số liệu trong bản thảo truy được về `results_X/res_X.json` kèm tên khoá.
- [ ] Chạy lại script đối chiếu số liệu; toàn bộ phải khớp tuyệt đối.
- [ ] Rà soát bảng các phát biểu cần tránh (mục 3 của `HUONG_DAN_CONG_TAC.md`). Có thể tìm nhanh
      bằng các từ khoá: `khác họ`, `thắng`, `tái lập`, `xác nhận`, `định tuyến`.
- [ ] Xác nhận không có số liệu nào lấy từ 16 lần chạy VOID.

Hoàn thành khi một người ngoài nhóm chọn ngẫu nhiên năm số liệu bất kỳ và cả năm đều truy ngược được
về tệp nguồn.

---

## Bước 5 — Ghép và thống nhất văn phong (Nguyên, khoảng nửa ngày)

- [ ] Ghép ba phần vào `BAO_CAO.md`.
- [ ] Thống nhất thuật ngữ theo bảng quy ước trong `README.md`. Mỗi khái niệm dùng đúng một tên
      xuyên suốt báo cáo.
- [ ] Thống nhất ký hiệu: `S`, `I`, `V`, `A`, `B`, `C`, `H`, `κ`, `D` được định nghĩa một lần ở §3
      và dùng lại về sau.
- [ ] Đọc lại §1 và §6. Nếu §6 không trả lời được câu hỏi đặt ra ở §1 thì một trong hai chương cần sửa.

---

## Bước 6 — Bổ sung kết quả thí nghiệm còn lại

Thí nghiệm **H100e** chưa hoàn tất. Khi có kết quả, thực hiện đúng trình tự sau, không bỏ bước:

1. Tải kết quả, **niêm phong bằng hash ngay** (`python deploy/seal_results.py results_X`), rồi commit.
2. **Đọc bảng diễn giải đã khoá trước** (`../docs/PREREGISTRATION.md`, mục #111).
3. **Kiểm tra điều kiện hợp lệ trước.** Nếu không đạt thì kết quả là VOID: chỉ ghi ở Phụ lục C,
   không đọc số liệu.
4. Nếu đạt, đọc số liệu và đối chiếu với đúng dòng tương ứng trong bảng diễn giải.
5. Chỉ sau bước 4 mới sửa bản thảo.

### Ảnh hưởng tới bản thảo

| Kết quả | Nội dung cần sửa |
|---|---|
| `Δ_honest` dương ở ít nhất 2 trên 3 cặp | Đây là kết quả dương đầu tiên có thể triển khai của dự án. Bổ sung mục §5.8 và cập nhật §6 |
| `Δ_honest` không dương | Ghi vào §8: giao thức sinh độc lập trước không vượt được model mạnh đơn lẻ |
| Thí nghiệm không hoàn tất | Ghi vào §8 là chưa xác lập, kèm lý do kỹ thuật (giới hạn 14,6 GB của GPU miễn phí) |

Thí nghiệm **H99b** đã hoàn tất và cho kết quả **dòng 2** (quy luật chuyển được sang miền toán).
Nội dung đã được cập nhật vào §5.5, §6 và §8.

---

## Bước 7 — Rà soát cuối (cả nhóm, khoảng 1 giờ)

- [ ] Phần tóm tắt nêu được khuyến nghị thực tiễn: dùng model nhỏ để giải, model lớn để soát, và
      không cho model lớn xem bài làm của model nhỏ với mục đích sửa chữa.
- [ ] §8 Hạn chế giữ đầy đủ các mục đã liệt kê trong `BAO_CAO_CAU_TRUC.md`.
- [ ] Đóng góp của cả ba thành viên đều xuất hiện trong phần thân, không dồn hết xuống phụ lục.
- [ ] §7 nêu cả hai chuẩn kiểm chứng (5 fold và tiền đăng ký).
- [ ] Tỷ lệ VOID 52% và sổ dự đoán trước 21/43 có mặt trong báo cáo, kèm giải thích vì sao đây là
      chỉ dấu tích cực về phương pháp.

---

## Các lỗi thường gặp

| Lỗi | Hậu quả | Cách phòng tránh |
|---|---|---|
| Ba khối viết như ba tài liệu rời | Mất luận điểm chung, mất phần có giá trị nhất | Bước 0 thống nhất một câu; §6 liên kết ba khối |
| Trích số liệu từ lần chạy VOID | Đã từng xảy ra ở các vòng #114, #121, #123 | Bước 4 và mục 1 của `HUONG_DAN_CONG_TAC.md` |
| Viết "chênh lệch nhỏ thì sửa chữa thắng" | Chiều khẳng định chưa được xác lập | Chỉ phát biểu theo chiều phủ định |
| Viết "đã xác nhận quy luật trên miền toán" | Khoảng tin cậy rộng, phép kiểm độ phân giải thấp | Viết "không bác bỏ được" |
| Gộp số liệu hai khối vào một bảng | Hai chuẩn kiểm chứng khác nhau | Ghi rõ chuẩn ở mỗi bảng, hoặc tách bảng |
| §8 Hạn chế viết sơ sài | Làm giảm độ tin cậy của toàn bộ báo cáo | Giữ đầy đủ các mục đã liệt kê |
| Chờ H100e xong mới bắt đầu viết | Không đủ thời gian | §1–§4, §5.1–§5.5 và §7 không phụ thuộc H100e, có thể viết ngay |

---

## Đường găng

Nếu quỹ thời gian hạn chế, thứ tự ưu tiên như sau:

```
Bước 0 → §3 Khung → §5.1–§5.5 → §6 Tổng hợp → §1 Mở đầu → các phần còn lại
```

§1 nên viết sau §6: chỉ khi đã xác định rõ kết luận thì phần mở đầu mới viết được cô đọng.
