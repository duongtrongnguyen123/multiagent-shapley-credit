# "Verifier tái sử dụng 0% khi can thiệp" không tái lập được — kể cả trên dữ liệu gốc

`RESULTS.md` mục 4c(3) khẳng định: *"Mỗi khi can thiệp, Verifier vứt bỏ toàn bộ chuỗi của
Solver"* — reuse **0.00** khi SỬA và khi PHÁ trên GSM8K. Đây là một trong bốn cơ chế trụ cột
của mục đó.

Đo lại cho kết quả khác, **trên cả hai tập dữ liệu**.

## Trên chính trace mà RESULTS.md dùng (`res_ft_g15/traces_full.json`, n=300)

Dùng đúng cách tính của main (loại số vốn có trong đề bài):

| GSM8K | toàn bộ | khi ĐỒNG Ý | khi SỬA | khi PHÁ |
|---|---|---|---|---|
| **RESULTS.md 4c(3)** | .17 | .20 | **0.00** | **0.00** |
| **đo lại trên cùng file** | **.712** | **.956** | **.198** (n=28) | **.230** (n=21) |

| MATH | toàn bộ | khi ĐỒNG Ý | khi SỬA | khi PHÁ |
|---|---|---|---|---|
| RESULTS.md 4c(3) | .83 | 1.00 | .33 | .29 |
| đo lại trên cùng file | .713 | .847 | .619 (n=16) | .470 (n=13) |

Đáng chú ý: cột "toàn bộ" và "khi ĐỒNG Ý" của GSM8K trong RESULTS.md (.17 / .20) **gần đúng
bằng** con số "khi ĐỔI đáp án" mà tôi tính (**.177**, n=89). Nhiều khả năng bảng gốc bị **lệch
cột** — các giá trị đúng nhưng gán sai nhãn.

## Trên trace độc lập của ta (`results_rescue/`, n=150/task)

| GSM8K | toàn bộ | khi ĐỒNG Ý | khi SỬA | khi PHÁ |
|---|---|---|---|---|
| giữ số trong đề | .68 | .81 | .37 (n=17) | .48 (n=18) |
| bỏ số trong đề | .66 | .80 | .34 (n=17) | .45 (n=17) |

Việc loại số trong đề **không** giải thích chênh lệch — nó chỉ đổi .37 → .34.

## Kết luận

**Con số 0.00 không tái lập được trên bất kỳ tập nào**, kể cả tập gốc. Verifier **có đọc** lời
giải của Solver khi can thiệp — nó tái sử dụng ~20% giá trị trên GSM8K và ~50–62% trên MATH.

**Điều vẫn đúng:** reuse khi can thiệp **thấp hơn hẳn** khi đồng ý — .198 vs .956 trên GSM8K
(chênh gần 5 lần). **Hướng của phát hiện đứng vững, chỉ độ lớn sai.**

Phát biểu đúng phải là *"Verifier tái sử dụng ít hơn nhiều khi can thiệp"*, không phải *"vứt bỏ
toàn bộ"*.

## Hệ quả cho kết luận phụ thuộc

RESULTS.md dùng reuse=0 để suy ra: *"intervention precision của Verifier bằng đúng độ chính xác
tự-giải, chứ không phải độ chính xác kiểm-tra vốn dễ hơn"*.

Suy luận đó dựa vào tiền đề "giải lại hoàn toàn từ đầu". Với reuse ~.20, Verifier ở đâu đó
**giữa** kiểm-tra và giải-lại, nên con số intervention precision cần **đo trực tiếp** chứ không
suy ra được từ tiền đề này. Bản thân con số precision có thể vẫn đúng — chỉ là lập luận dẫn tới
nó không còn chống đỡ được.

## Việc cần làm

Sửa bảng 4c(3) trong `RESULTS.md`. Nhưng đây là tài liệu của nhánh main và tác giả khác đang
chạy thí nghiệm dựa trên nó, nên nêu vấn đề trước khi tự ghi đè. Số liệu tái lập được nằm ở
`analysis/role_specialization.py` và script kiểm tra trong tài liệu này.

## Ghi chú phương pháp

Phát hiện này đến từ việc **đo lại một số đã công bố trên chính dữ liệu gốc của nó** — cùng loại
kiểm tra chéo đã tìm ra lỗi normalizer (`fc2f429`) và bác bỏ giả thuyết format của Aggregator
(`AGG_FORMAT_CHECK.md`). Ba lần, cùng một cách làm.
