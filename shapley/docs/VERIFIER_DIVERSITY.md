# Ba Verifier hay ba Solver? — hòa nhau, và dự đoán của tôi sai

MATH 1.5B, 5 fold × 30, `pipeline/vdiv_folds_kernel.py`.

## Dự đoán ghi trước khi chạy — BỊ BÁC

Tôi dự đoán `PSVVV_vote` **thua** `PSSS_vote`, lập luận: ba Verifier đều đọc **cùng một** lời
giải của Solver, đã đo tái sử dụng 42–70% số liệu của nó, nên sẽ **sai giống nhau** và bỏ phiếu
giữa các lỗi tương quan không cứu được gì.

**Kết quả: hòa chính xác.**

| nhánh | lượt gọi | acc |
|---|---|---|
| S | 1 | .4133 |
| PS | 2 | .4800 |
| PSV | 3 | .4867 |
| PSVA | 4 | .5067 |
| **PSVVV_vote** | **5** | **.5333** |
| **PSSS_vote** | **4** | **.5333** |
| SSS_vote | 3 | .4533 |

`PSVVV − PSSS` = **+0.0000**, PSVVV thắng 1/5 fold.

## Vì sao dự đoán sai — cơ chế đo được

| chỉ số | nhóm Verifier | nhóm Solver |
|---|---|---|
| tỉ lệ câu có ≥2 đáp án khác nhau | **.420** | .280 |
| số đáp án phân biệt (trung bình) | **1.580** | 1.367 |
| oracle (có ứng viên đúng) | **.593** | .580 |

**Ba Verifier ĐA DẠNG HƠN ba Solver**, không kém hơn — ngược hẳn giả định của tôi. Tỉ lệ câu có
bất đồng cao hơn 50% (.420 vs .280), và trần oracle cũng nhỉnh hơn.

Điều này xảy ra **dù** `V_reuse_of_S` = **.778** — Verifier tái sử dụng 78% số liệu trong lời
giải Solver. Tôi đã suy sai từ con số này: **tái sử dụng nhiều số không có nghĩa là cho ra cùng
đáp án.** Ba Verifier đọc cùng một lời giải nhưng vẫn bất đồng về việc bước nào sai, nên đáp án
cuối phân tán hơn cả ba Solver sample.

Ngược lại, ba Solver sample **cùng nhận một plan** (để so công bằng) nên bị plan neo lại — đó mới
là nguồn đồng thuận giả.

## Điều thật sự học được

**Ngân sách quan trọng hơn nguồn đa dạng.** Xếp theo số lượt gọi:

| lượt gọi | acc tốt nhất |
|---|---|
| 1 | .4133 |
| 2 | .4800 |
| 3 | .4867 (PSV) · .4533 (SSS_vote) |
| **4** | **.5333** (PSSS_vote) · .5067 (PSVA) |
| **5** | **.5333** (PSVVV_vote) |

Ở **cùng 4 lượt gọi**, `PSSS_vote` (.5333) thắng `PSVA` (.5067) **2.7 điểm**. Và `PSVVV_vote`
tốn thêm 1 lượt mà không được gì.

⇒ **Kết luận thực dụng: ở ngân sách 4 lượt, `P→S` rồi 2 Solver sample nữa + bỏ phiếu là cấu hình
tốt nhất đo được.** Tốt hơn pipeline PSVA hiện tại, rẻ hơn PSVVV.

## Trả lời câu hỏi "có nên bỏ Aggregator không"

| | acc | lượt gọi |
|---|---|---|
| PSV | .4867 | 3 |
| PSVA | .5067 | 4 |

Aggregator được **+2.0 điểm** cho 1 lượt gọi thêm. **Không nên bỏ** — nhưng cũng không đáng giữ
nếu có 4 lượt, vì `PSSS_vote` cùng ngân sách được .5333.

## Một quan sát về plan

`SSS_vote` (3 Solver, **không** plan) chỉ đạt **.4533**, trong khi `PSSS_vote` (3 Solver, **có**
plan) đạt **.5333** — chênh **8 điểm**. Plan vẫn có giá trị ngay cả khi đã bỏ phiếu, và giá trị
đó không bị bỏ phiếu thay thế.

Nhưng lưu ý: ba Solver trong `PSSS_vote` dùng **cùng một plan**, nên chúng ít đa dạng hơn
(.280 vs .420). Plan vừa nâng chất lượng vừa giảm đa dạng — hai tác động ngược chiều mà kết quả
ròng vẫn dương.

## Giới hạn

- n=150, MATH 1.5B, một lần chạy. Khoảng cách `PSSS_vote` vs `PSVA` là 2.7 điểm — **dưới sàn
  nhiễu ~5 điểm**, nên đọc là *"chưa phân biệt được"*, không phải *"chắc chắn tốt hơn"*.
- Con số đáng tin hơn là **đa dạng** (.420 vs .280) và **oracle** (.593 vs .580) — đếm trực tiếp,
  không phải hiệu của hai ước lượng.
- `PSVVV − PSSS` = 0.0000 chính xác là trùng hợp của n nhỏ, không nên đọc là "bằng nhau tuyệt
  đối".
- Chưa chạy GSM8K.
