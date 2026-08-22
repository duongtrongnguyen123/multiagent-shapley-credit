# Đánh giá đóng góp của từng vai trò trong hệ suy luận đa tác tử

Báo cáo bài tập lớn — Xử lý ngôn ngữ tự nhiên (INT3406), Trường Đại học Công nghệ, ĐHQGHN.
Nhóm 13: Dương Trọng Nguyên, Trương Đình Đức, Trần Tùng Dương, Lê Hoàng Quân.

**Báo cáo đầy đủ:** [`shapley/report/BAO_CAO_NHOM13.pdf`](shapley/report/BAO_CAO_NHOM13.pdf)

---

## Khảo sát này hỏi gì

Các hệ LLM đa tác tử chia việc cho nhiều vai trò — lập kế hoạch, giải, kiểm tra, tổng hợp — với
kỳ vọng tốt hơn một model đơn lẻ. Câu hỏi của chúng tôi là: **lợi ích đo được đến từ cơ chế
phối hợp, hay chỉ từ việc gọi model nhiều lần hơn?**

Để trả lời, mọi phép đo được đặt dưới ba phép kiểm soát mà các nghiên cứu thường bỏ qua:

| Kiểm soát | Nếu thiếu | Hệ quả |
|---|---|---|
| Chi phí tính toán | So hệ nhiều lượt gọi với model chạy một lượt | Đánh giá **cao** |
| Mốc so sánh | Chỉ so với model yếu bị sửa, không so với model mạnh đơn lẻ | Đánh giá **cao** |
| Mẫu số | Tính trung bình cả trên bài không cơ chế nào đổi được | Đánh giá **thấp** |

Ba sai lệch không cùng chiều, nên phải áp đồng thời.

## Kết quả chính

- **Lợi ích không phổ quát.** Pipeline bốn vai hơn 11,2 điểm trên GSM8K nhưng kém 6,0 điểm
  trên MATH, trong khi tốn thêm 2,9× đến 6,63× token.
- **Giá trị nằm ở số lần sinh, không ở cơ chế phối hợp.** Cho model giải lại mà không đọc phê
  bình của verifier cho kết quả bằng đúng khi có đọc (0,453 so với 0,453).
- **Đổi mốc so sánh làm đảo dấu kết luận.** So với model yếu, hiệu ứng tăng theo chênh lệch
  năng lực; so với model mạnh chạy độc lập, hiệu ứng giảm và xuống dưới 0.
- **Nội dung artifact quyết định dấu của hiệu ứng.** Cho model mạnh xem bài làm của model yếu:
  artifact đúng cho +3,8 điểm, artifact sai cho −27,2 điểm. Giao thức sinh-rồi-sửa hoạt động
  như một ống dẫn đáp án, không phải bộ sửa lỗi.
- **Bước kiểm chỉ có giá trị khi người kiểm mạnh hơn.** Verifier cùng cỡ với solver đạt độ
  chính xác can thiệp 56–59%; verifier lớn hơn đạt 98%.
- **Bảy phương pháp huấn luyện vai trò đều tìm ra lối tắt của hàm mục tiêu**, không cái nào cải
  thiện thật.

Mọi hiệu ứng được đọc trên **mức dao động nền** đo được: chạy cùng một cấu hình trên 5 fold cho
độ lệch chuẩn 2,65 điểm, suy ra ngưỡng hiệu dụng khoảng 3,3 điểm.

## Cấu trúc thư mục

```
shapley/
  report/     báo cáo LaTeX, slide, và các tài liệu hỗ trợ viết bài
  docs/       tài liệu phân tích cho từng thí nghiệm (40 file)
  pipeline/   kernel thí nghiệm, chạy trên Kaggle
  deploy/     script điều phối, phóng job và thu kết quả
  analysis/   Shapley, bootstrap, chấm điểm, phân tầng, định tuyến
  tests/      test cho bộ định tuyến
  res_*/      kết quả tóm tắt của từng lần chạy
```

## Chạy lại

Cần một tài khoản Kaggle có bật GPU. Token đọc từ file ngoài repo:

```bash
export ACCOUNTS_FILE=/duong/dan/toi/accounts.txt   # mỗi dòng: <username> <token>
export KAGGLE_RTX_ACCOUNT=<username có quyền RTX>  # chỉ khi cần GPU lớn
python shapley/deploy/launch_any.py <ten_kernel>
```

Repo **không chứa** token hay tên tài khoản. Các bản dump trace thô cũng không được commit vì
tái sinh được từ `pipeline/`; chỉ file tóm tắt được giữ lại.

## Ghi chú về dữ liệu

Benchmark dùng trong khảo sát: GSM8K, MATH, MBPP, HumanEval. Model từ 0,5B đến 32B tham số.
Giải mã tất định (`sample = false`), nên chênh lệch giữa các fold hoàn toàn do khác bài chứ
không do ngẫu nhiên lấy mẫu.

Nhật ký quá trình nghiên cứu, gồm các hướng đã thử và loại bỏ, nằm ở
[`shapley/docs/NHAT_KY_DU_AN.md`](shapley/docs/NHAT_KY_DU_AN.md). Một số thuật ngữ trong nhật ký
là bản cũ, đã được thống nhất lại trong báo cáo.
