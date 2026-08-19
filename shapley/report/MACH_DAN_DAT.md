# Mạch dẫn dắt giữa các thí nghiệm

Tài liệu này trình bày **thứ tự phát sinh** của các thí nghiệm: mỗi thí nghiệm ra đời từ một câu hỏi
mà thí nghiệm trước để lại. Đây là nội dung của chương §5 khi viết theo dạng survey.

Bố cục theo thành phần khung (`H`, `κ`, `D`) đã có trong `BAO_CAO_CAU_TRUC.md` và phù hợp để **tra
cứu**. Bố cục theo mạch dẫn dắt dưới đây phù hợp để **kể lại quá trình**, và nên dùng khi viết
phần thân báo cáo.

---

## Sơ đồ tổng quát

```
[1] Pipeline đa tác tử có giúp không?
      ↓ GSM8K +11,2đ (2,9× ký tự) nhưng MATH −6,0đ (6,63× ký tự). Chưa kiểm soát ngân sách.
[2] Cùng ngân sách token thì sao?
      ↓ thành phần tổng hợp LLM không ổn định: thắng ở GSM8K, thua đậm ở MATH
[3] Có phải nhờ phản hồi của verifier không?
      ↓ không: giải lại KHÔNG xem phê bình cho kết quả y hệt
[4] Vậy aggregator LLM thực sự làm gì?
      ↓ chép ứng viên cuối 65% số câu; phá đa số 26 lần, sửa đa số 0 lần
[5] Có phải đang đo sai MẪU SỐ?
      ↓ ĐÚNG: 57% số câu bất động. Hiệu ứng thật +31,1đ trên 30% câu, pha loãng 3,3× còn +9,3đ
[6] Các vai có thực sự chuyên biệt không?
      ↓ ở 1.5B thì KHÔNG: planner giải hộ, solver chép lại (lời giải dài 19 ký tự)
[7] Vai nào thực sự đóng góp?
      ↓ verifier, phụ thuộc CỠ (43:1 so với 2,5:1). Nhưng cùng token thì chỉ HOÀ với model mạnh
[8] Phối hợp có xứng chi phí không?
      ↓ có trên GSM8K, không trên MATH — vì sao khác nhau?
[9] Đang so với baseline nào?
      ↓ đổi mốc từ model yếu sang model mạnh → DẤU ĐẢO NGƯỢC
[10] Giá trị mất đi ở đâu?
      ↓ đẳng thức Δ_ceil = A − B + C tách được ba nguồn
[11] Số hạng A do đâu quyết định?     → chênh lệch năng lực, không phải họ model
[12] Số hạng B do đâu mà có?          → tiếp xúc với nội dung SAI
[13] Quy luật có tổng quát không?     → chuyển được sang miền toán
[14] Tín hiệu kiểm là ĐÚNG ĐẮN hay HỌC ĐƯỢC?
      ↓ đúng đắn (chạy test): bộ chọn HOÀN HẢO, phá 0 bài trong 20/20 fold
      ↓ học được (LLM/phân loại): không phát hiện nổi MỘT CHỮ SỐ bị đổi (+0,032)
[15] Có chặn được B không?            → trần chỉ +0,018
      ↓
[16] Nghịch lý giữa [7] và [13] được giải bằng [10]

BA KIỂM SOÁT phải đi cùng nhau:
   ngân sách token [2] · mẫu số [5] · mốc so sánh [9]
   thiếu [5] thì đánh giá THẤP; thiếu [2] và [9] thì đánh giá CAO
```

---

## [1] Điểm xuất phát: pipeline đa tác tử có giúp không?

**Câu hỏi.** Ghép nhiều vai LLM (planner, solver, verifier, aggregator) có tốt hơn một model đơn lẻ không?

**Kết quả ban đầu, và nó phụ thuộc task:**

| Task | Solver đơn lẻ | Pipeline đầy đủ | Chênh | Chi phí ký tự |
|---|---|---|---|---|
| GSM8K 1.5B | 0,632 | 0,744 | **+0,112** | 2,9× |
| MATH 1.5B | 0,405 | 0,345 | **−0,060** | **6,63×** |

Trên GSM8K pipeline có lợi; trên MATH nó **tốn 6,63 lần số ký tự để cho kết quả kém hơn 6 điểm**.
(Phép đo 5 fold trên GSM8K cho +5,6 điểm, thấp hơn con số đo một lần ở trên.)

**Hai lý do khiến kết quả này chưa đủ để kết luận.**

Thứ nhất, sàn nhiễu. Chạy cùng một cấu hình trên 5 fold rời nhau cho `V_gain` dao động từ **+1,0 đến
+8,0 điểm**; sàn nhiễu 2σ tương đương **5 điểm**. Mọi hiệu ứng nhỏ hơn 5 điểm đo một lần không được
tính là bằng chứng. Nhiều kết luận trước đó bị hạ cấp, trong đó có `A_gain` = +1,2 điểm với khoảng
tin cậy chứa số 0.

Thứ hai, và quan trọng hơn: **pipeline đầy đủ tốn gấp ba lần số token so với solver đơn lẻ.** So sánh
một hệ 3× với một hệ 1× rồi kết luận "phối hợp có giá trị" là so sánh không công bằng. Câu hỏi đúng
phải là: **với cùng ngân sách token, phối hợp nhiều vai có thắng việc sinh nhiều lượt độc lập rồi
bỏ phiếu không?**

**Câu hỏi để lại:** cùng ngân sách thì kết quả thế nào?

---

## [2] Đối chứng cùng ngân sách: thành phần tổng hợp LLM không ổn định

**Thiết kế.** Cố định số lượt sinh, chỉ thay đổi cách tổng hợp. Với `K` = 8 lượt sinh trên MATH:

| Cách tổng hợp | MATH 1.5B | MATH 7B |
|---|---|---|
| Greedy, 1 lượt sinh | 0,50 | 0,72 |
| **maj@8** — bỏ phiếu cơ học | **0,60** | **0,73** |
| **llm_agg@8** — aggregator LLM đọc cả 8 rồi tổng hợp | **0,41** | **0,47** |
| oracle@8 — trần lý tưởng | 0,73 | 0,85 |

**Cùng chính xác 8 lượt sinh, cùng chi phí, khác duy nhất ở bộ tổng hợp.** Aggregator LLM kém hơn
bỏ phiếu cơ học **0,19** trên 1.5B và **0,26** trên 7B. Trên 7B, aggregator LLM thậm chí còn **kém
hơn cả greedy một lượt** (0,47 so với 0,72).

**Nhưng kết quả này PHỤ THUỘC TASK — cần nêu rõ, không được khái quát hoá.** Đo trực tiếp
`vote5` so với `llm_agg` trên cùng ứng viên:

| Task | `vote5` − `llm_agg` |
|---|---|
| MATH 1.5B | **+0,075** (bỏ phiếu thắng) |
| GSM8K 1.5B | **−0,056** (aggregator LLM thắng) |

Trên **MATH**, bỏ phiếu cơ học thắng rõ rệt và nhất quán ở cả hai cỡ model. Trên **GSM8K**,
aggregator LLM lại nhỉnh hơn. Phát biểu đúng là: **thành phần LLM tổng hợp không mang lại giá trị
ổn định; ở miền khó nó gây hại đáng kể.**

Điều này cho thấy giá trị quan sát được ở [1] chủ yếu đến từ **việc sinh thêm lượt**, không từ việc
bổ sung vai trò tổng hợp.

**Câu hỏi để lại:** liệu lợi ích có đến từ phản hồi của verifier không, hay chỉ từ lượt sinh thêm?

---

## [3] Tách phản hồi khỏi lượt sinh thêm

**Thiết kế.** So sánh hai nhánh có **cùng số lượt sinh**:

- `loop` — solver giải lại **sau khi đọc phê bình** của verifier
- `rerun` — solver giải lại **vô điều kiện, không hề thấy phê bình**

| Nhánh | Độ chính xác | Δ so với solver | Fold cùng dấu |
|---|---|---|---|
| Solver một mình | 0,413 | — | — |
| `loop` (giải lại kèm phê bình) | **0,453** | +0,040 | 4/5 |
| `rerun` (giải lại, không phê bình) | **0,453** | +0,040 | 3/5 |

**Hai nhánh bằng nhau chính xác.** Lợi ích không đến từ nội dung phản hồi của verifier; nó đến từ
việc model được sinh thêm một lượt.

Ghi chú thêm: con số +20 điểm cho `loop` từng được báo cáo ở một phép đo đơn lẻ (n = 100) không tái
lập được — trên 5 fold chỉ còn +4,0 điểm, dưới sàn nhiễu.

**Nếu không có nhánh đối chứng `rerun`, kết luận sẽ là "refinement dựa trên phản hồi có tác dụng",
và kết luận đó sai.** Đây là ví dụ điển hình cho vai trò của nhánh đối chứng.

**Câu hỏi để lại:** vậy aggregator LLM thực sự làm gì với các ứng viên?

---

## [4] Cơ chế: aggregator không chọn, nó chép ứng viên cuối

**Số liệu.**

- `agg5_copies_last` = **0,653**: ngay cả khi có 5 ứng viên, aggregator chép nguyên ứng viên **cuối
  cùng** ở 65% số câu. Với 2 ứng viên, tỷ lệ này là 0,747.
- Số đáp án khác nhau trung bình: **2,88 trên 5** — tức có đủ đa dạng để việc bỏ phiếu là có nghĩa.
- Trong thí nghiệm 8 lượt sinh: aggregator **phá vỡ đa số đúng 21 lần** (1.5B) và **26 lần** (7B),
  trong khi **sửa được đa số sai chỉ 2 lần** và **0 lần**.

**Tỷ lệ 26 phá trên 0 sửa là dạng thuần khiết nhất của số hạng `B`** sẽ được định nghĩa hình thức ở
[8]. Ở đây `B` được quan sát trực tiếp, không cần suy diễn: thành phần LLM phá huỷ những câu trả lời
mà cơ chế bỏ phiếu đã chọn đúng.

Nguyên nhân là **thiên lệch vị trí**: aggregator không thực hiện việc chọn, nó lấy nội dung đọc sau
cùng.

**Một điều chỉnh cần ghi nhận.** Aggregator từng bị cấu hình sai: với 2 ứng viên thì khái niệm "đa số"
không tồn tại. Khi tăng lên 3 ứng viên, hiệu ứng chuyển từ −0,007 thành **+0,053**, đạt 5/5 fold —
hiệu ứng dương duy nhất đạt 5/5 trong nhóm thí nghiệm đó. Tuy nhiên bỏ phiếu cơ học vẫn thắng
(**+0,093** so với +0,047). Aggregator LLM sau khi sửa cấu hình vẫn không đóng góp gì ngoài việc
đếm phiếu, và vẫn làm kém đi.

**Câu hỏi để lại:** nếu aggregator không đóng góp, vai nào đóng góp?

---

## [5] Mẫu số: 57% số câu không thể có hiệu ứng

**Câu hỏi.** Suốt [1]–[4], mọi can thiệp đều cho hiệu ứng 0–5 điểm và phần lớn chìm dưới sàn nhiễu.
Có phải phối hợp thực sự vô dụng, hay phép đo đang dùng sai mẫu số?

**Thiết kế.** Phân tầng theo độ khó **đối với chính model**: đếm số lời giải đúng trong `K` = 5 mẫu
độc lập của solver. Tính offline trên trace đã có, không tốn GPU.

| Số mẫu đúng trên 5 | n | Solver | vote5 | Δ |
|---|---|---|---|---|
| **0/5** (quá sức) | 48 (32%) | 0,000 | 0,000 | **0,000** |
| 1/5 | 20 | 0,000 | 0,000 | 0,000 |
| 2/5 | 15 | 0,333 | 0,600 | +0,267 |
| 3/5 | 12 | 0,583 | 1,000 | +0,417 |
| 4/5 | 18 | 0,722 | 1,000 | +0,278 |
| **5/5** (quá dễ) | 37 (25%) | 1,000 | 1,000 | **0,000** |

**57% số câu không thể có hiệu ứng vì lý do toán học, không phải vì phương pháp kém:** 32% số câu
không mẫu nào đúng nên không có gì để chọn; 25% số câu mọi mẫu đều đúng nên không có gì để cải
thiện hay phá hỏng.

Trên **30% số câu** mà cơ chế chọn lọc có thể tác động (tầng 2–4/5), hiệu ứng là **+31,1 điểm** —
gấp hơn sáu lần sàn nhiễu. Nhưng khi lấy trung bình trên toàn bộ 150 câu, con số đó bị pha loãng
**3,3 lần** thành **+9,3 điểm**.

> **Đây không phải "phối hợp vô dụng" mà là "đo sai mẫu số".** Một can thiệp mạnh +31 điểm trên tập
> nó có thể tác động sẽ hiện ra thành +9 điểm trên tập đầy đủ; một can thiệp trung bình +10 điểm sẽ
> thành +3 điểm, chìm dưới sàn nhiễu, và bị kết luận là "không có tác dụng".

**Đây là kiểm soát thứ ba, bên cạnh ngân sách token ở [2] và mốc so sánh ở [9].** Ba kiểm soát này
phải đi cùng nhau: thiếu kiểm soát mẫu số thì mọi hiệu ứng bị đánh giá thấp; thiếu kiểm soát ngân
sách và mốc so sánh thì mọi hiệu ứng bị đánh giá cao.

**Câu hỏi để lại:** nếu chỉ 30% số câu là nơi phối hợp có ý nghĩa, thì trong số đó vai nào đóng góp?

---

## [6] Các vai có thực sự chuyên biệt không?

**Câu hỏi.** Toàn bộ phân tích theo vai giả định mỗi vai làm đúng việc mà tên gọi mô tả. Giả định
này chưa từng được kiểm.

**Thiết kế.** Đọc chỉ số **hành vi** từ trace, không dùng accuracy.

| Chỉ số | GSM8K 1.5B | MATH 1.5B | GSM8K 7B | MATH 7B |
|---|---|---|---|---|
| Planner (được yêu cầu *không* tính đáp án) chứa sẵn đáp án đúng | 14,0% | **34,7%** | 1,0% | 4,0% |
| Planner có `\boxed{}` | 3,3% | **45,3%** | 0,0% | 0,0% |
| Solver không sinh số mới nào | **60,7%** | **62,0%** | 1,0% | 11,0% |
| Độ dài lời giải của Solver (median, ký tự) | **19** | 344 | 821 | 1247 |
| …khi không có plan | 664 | 1384 | 754 | 1264 |

Ở 1.5B, solver sinh lời giải dài **19 ký tự** khi có plan, so với **664 ký tự** khi không có plan.
Nó không giải, nó chép.

> **Với model yếu, phân công lao động sụp đổ: planner giải hộ, solver chép lại. Ở 7B hai vai hồi
> phục đúng chức năng — nhưng ở mức năng lực đó pipeline lại thua chính solver chạy một mình.**
>
> Nói cách khác: multi-agent có phân công thật ở nơi **không cần**, và mất phân công ở nơi **được
> kỳ vọng giúp**.

**Một quan sát bổ sung, cùng hình dạng với [12].** Phân tầng theo nội dung của plan trên MATH 1.5B:
solver đúng **97,3%** khi plan chứa đáp án đúng (n = 37), nhưng chỉ **31,9%** khi plan sai (n = 163).
Ở 7B khoảng cách hẹp hơn: 92,9% so với 60,2%.

⚠️ Quan sát này **bị nhiễu bởi độ khó**: những câu mà planner làm đúng có thể vốn dễ hơn. Nó chưa
có nhánh đối chứng "không thấy plan" như thiết kế ở [12], nên chỉ là **gợi ý cùng hướng**, không
phải bằng chứng độc lập.

**Câu hỏi để lại:** trong số các vai, vai nào đóng góp giá trị?

---

## [7] Phân rã theo vai: hoá ra biến quyết định không phải vai

**Câu hỏi.** Dùng giá trị Shapley để tính đóng góp biên của từng vai.

**Kết quả bất ngờ.** Điều quyết định không phải *có thêm vai hay không*, mà là *vai đó mạnh đến đâu*:

| Cấu hình | Hiệu ứng trên MATH | Nhất quán |
|---|---|---|
| Solver 1.5B + Verifier **7B** | **+14,0 điểm**, khoảng [+8,3; +20,0] | 5/5 fold |
| Solver 1.5B + Verifier **1.5B** (cùng cỡ) | +3,0 điểm, khoảng **chạm 0** | không xác lập |
| Riêng phần do verifier mạnh hơn | **+11,0 điểm**, khoảng [+3,3; +16,7] | 5/5 fold |

Đối chiếu trực tiếp trên cùng 300 bài (5 fold × 60):

| Verifier | Sửa đúng | Làm hỏng | Tỷ lệ |
|---|---|---|---|
| **V7B** (lớn hơn) | **43** | **1** | 43 : 1 |
| V1.5B (cùng cỡ) | 15 | 6 | 2,5 : 1 |

Verifier lớn hơn không chỉ sửa nhiều hơn mà còn **phá ít hơn sáu lần**.

**Đây là lần đầu khái niệm bất đối xứng năng lực xuất hiện trong dự án**, và nó đến từ phía phân
tích vai, hoàn toàn độc lập với nhánh nghiên cứu sau này.

### Nhưng con số +14,0 được đo so với model YẾU

Cấu hình `S1.5B + V7B` đã dùng một model 7B. Vậy câu hỏi công bằng là: nó có hơn việc **chỉ dùng
7B** hay không? Số liệu token thật, đo trên 5 fold:

| Cấu hình | GSM8K | MATH | Token GSM8K | Token MATH |
|---|---|---|---|---|
| S1.5B + V7B | 0,810 | 0,563 | 105k | 119k |
| **S7B một mình** | **0,910** | **0,593** | 120k | 152k |
| S7B + V7B | 0,900 | 0,670 | 205k | 261k |

- Trên **GSM8K**: cấu hình bất đối xứng **kém hơn 10 điểm** so với chỉ dùng 7B, dù rẻ hơn 12% token.
- Trên **MATH**: kém hơn 3 điểm, ngang bằng về mặt thống kê, và rẻ hơn **22%** token.

**Phát biểu đúng: cấu hình bất đối xứng là một lựa chọn TIẾT KIỆM CHI PHÍ, không phải một cải thiện
độ chính xác.** Lợi ích +14,0 chỉ tồn tại khi so với model yếu; so với model mạnh chạy một mình ở
ngân sách token thấp hơn, nó hoà hoặc kém.

Một quan sát riêng: thêm verifier vào chính S7B trên MATH cho **+7,7 điểm** (0,593 → 0,670), nhưng
tốn **1,7 lần** token. Đây là cải thiện thật, kèm chi phí thật.

**Phân tích Pareto khẳng định lại điều này.** Trên cả hai task, **solver một mình nằm trên đường
Pareto** — không có tổ hợp nào vừa rẻ hơn vừa chính xác hơn. Trên MATH, **pipeline đầy đủ không nằm
trên đường Pareto**: nó bị chi phối bởi phương án chỉ dùng solver (chi phí 1, độ chính xác 0,436 so
với 0,373 của pipeline đầy đủ).

**Câu hỏi để lại:** nếu ngay cả cấu hình tốt nhất cũng chỉ hoà với model mạnh đơn lẻ, thì suốt thời
gian qua các phép đo đang so với baseline nào?

---

## [8] Chi phí: phối hợp chỉ trả tiền ở nơi ít cần nó nhất

**Câu hỏi.** Pipeline đầy đủ tốn gấp ba lần solver đơn lẻ. Có cách nào giữ phần lớn lợi ích với chi
phí thấp hơn không?

**Thiết kế.** Consensus router: chạy solver và verifier; chỉ khi hai bên bất đồng mới gọi aggregator.

| Chiến lược | GSM8K | Chi phí | MATH | Chi phí |
|---|---|---|---|---|
| Solver đơn lẻ | 0,6733 | 1 | 0,4133 | 1 |
| Pipeline đầy đủ | 0,7233 | 3 | 0,3733 | 3 |
| **Consensus Router** | **0,7200** | **2,32** | 0,4133 | 2,40 |

**Trên GSM8K router thành công**: gần bằng độ chính xác của pipeline đầy đủ với 77% chi phí.
**Trên MATH router vô dụng**: đúng bằng solver đơn lẻ.

**Cơ chế.** Khi solver và verifier bất đồng, aggregator sửa đúng được **45,4%** trường hợp trên
GSM8K nhưng chỉ **25,0%** trên MATH.

Đây là mệnh đề **M3**: định tuyến tiết kiệm được ở nơi đã sẵn có đồng thuận, tức nơi ít cần nó nhất.

**Câu hỏi để lại:** vì sao aggregator hỏng trên MATH? Câu hỏi này chưa được trả lời ở đây, và sẽ
được trả lời ở [7].

---

## [9] Bước ngoặt: đang so với baseline nào?

**Quan sát.** Toàn bộ các phép đo ở [1]–[6] đều so với **model yếu** hoặc với solver đơn lẻ. Nhưng
nếu pipeline đã chứa một model mạnh, thì lựa chọn thực tế của người triển khai là: chạy pipeline,
hay **gọi thẳng model mạnh**?

Bảng token ở [5] đã cho thấy vấn đề này một lần: cấu hình bất đối xứng thắng đậm khi so với model
yếu, nhưng hoà hoặc kém khi so với model mạnh đơn lẻ. **Đây không phải hiện tượng riêng của một
cấu hình — đó là hệ quả của việc chọn sai mốc so sánh, và nó lặp lại ở mọi nhánh nghiên cứu của
dự án.**

**Đại lượng đúng là `V − I`, không phải `V − S`.**

**Kết quả.** Khi đổi mốc so sánh, **dấu của hiệu ứng đảo ngược**. Một giao thức "cải thiện" so với
model yếu lại **kém hơn** việc gọi trực tiếp model mạnh.

Đây là phát hiện phương pháp trung tâm của báo cáo, và là lý do tồn tại của toàn bộ nhánh nghiên
cứu tiếp theo.

**Câu hỏi để lại:** giá trị bị mất đi ở đâu?

---

## [10] Công cụ: đẳng thức phân rã

Để trả lời "mất ở đâu", cần một cách tách giá trị thành các phần đo được. Với `S` là model yếu,
`I` là model mạnh, `V` là kết quả khi `I` sửa artifact của `S`, và trần lý tưởng
`CEIL = S ∨ (¬S ∧ V)`:

```
Δ_ceil = acc(CEIL) − acc(I) = A − B + C

A = P(S đúng ∧ I sai)          cơ hội có sẵn
B = P(¬S ∧ I đúng ∧ V sai)     giao thức làm hỏng bài mà I vốn giải đúng
C = P(¬S ∧ ¬I ∧ V đúng)        giao thức cứu được bài cả hai đều sai
```

Đây là **đẳng thức đại số**, không phải mô hình xấp xỉ. Kiểm chứng: khớp tuyệt đối trên 4/4 cặp có
lưu vết, sau đó 15/15 cặp trong thí nghiệm quy mô lớn.

Từ đây mọi câu hỏi đều có dạng: **số hạng nào đang gây ra kết quả?**

**Câu hỏi để lại:** `A` do đâu quyết định?

---

## [11] Số hạng A: một tương quan giả bị phát hiện

**Giả thuyết ban đầu.** Quan sát trên 7 cặp cho thấy cặp **khác họ model** có `A` cao gần gấp đôi
cặp cùng họ (0,0597 so với 0,0481). Giả thuyết: đa dạng họ model tạo ra dư địa.

**Vấn đề.** Các cặp khác họ trong mẫu đó **cũng có chênh lệch năng lực nhỏ hơn** (0,1296 so với
0,1666), và tương quan giữa chênh lệch và `A` là **−0,908**. Hai lời giải thích bị trộn hoàn toàn.

**Thiết kế tách biệt.** Sáu model, **15 cặp có hướng, cùng 499 bài, một lần chạy**, bổ sung đúng
những ô mà mẫu cũ thiếu: cùng họ nhưng chênh lệch nhỏ, và khác họ nhưng chênh lệch lớn.

**Kết quả.** Hồi quy `A = β₀ + β₁ × chênh lệch + β₂ × khác họ`:

- **β₁ = −0,1922** (p ≈ 0)
- **β₂ = +0,00446**, khoảng tin cậy 95% **[−0,0051; +0,0140]**
- `R²` khi chỉ dùng chênh lệch: **0,824**

Khoảng tin cậy của `β₂` nằm **trọn dưới** ngưỡng +0,02 đã khoá trong tiền đăng ký. Đây là kết quả
null **có thông tin**: không phải "chưa đủ dữ liệu để thấy", mà là "nếu có hiệu ứng thì nó nhỏ hơn
mức được coi là đáng kể".

**Điểm nối quan trọng với [2].** Hai khối công việc, hai thiết kế hoàn toàn khác nhau, cùng một kết
luận: **biến quyết định là chênh lệch năng lực, không phải cấu trúc hay họ model.**

**Câu hỏi để lại:** còn `B` thì do đâu?

---

## [12] Số hạng B: thiệt hại đến từ nội dung sai, không từ việc nhìn thấy

**Giả thuyết ban đầu (thăm dò).** Trên MBPP, tách theo nội dung artifact cho thấy hai tầng phản ứng
ngược nhau. Nhưng đây là phân rã hậu nghiệm, chưa đủ tin cậy.

**Thiết kế xác nhận.** Tiền đăng ký đầy đủ, **đổi miền** sang MATH-500 để không lặp lại cùng phép đo.
Hai nhánh dùng **cùng một lệnh giải**, khác biệt duy nhất là có kèm artifact của model yếu hay không.

| | MBPP 11–510 | MBPP 511–974 | **MATH-500 (có tiền đăng ký)** |
|---|---|---|---|
| Artifact **sai** | −0,1900 | −0,1927 | **−0,2720** (p ≈ 0) |
| Artifact **đúng** | +0,0636 | +0,0245 | **+0,0377** (p = 0,012) |

Trên MATH, độ chính xác của model mạnh giảm từ **46,4%** xuống **19,2%** ở tầng artifact sai — tức
giảm trên chính những bài mà nó vốn giải đúng gần một nửa. Tổng hợp hai tầng theo trọng số tái tạo
chính xác `V − I` = **−0,1240**.

**Kết luận.** `D` không phải hình phạt của việc **nhìn thấy**, mà là hình phạt của việc nhìn thấy
**nội dung sai**. Khi artifact đúng, model mạnh **cải thiện**.

**Điểm nối ngược về [3].** Đây là lời giải cho câu hỏi bỏ ngỏ ở [3]: aggregator hỏng trên MATH vì
trên MATH model yếu sai nhiều hơn, nên aggregator tiếp xúc với nhiều nội dung sai hơn. Hai phép đo
độc lập, cùng một cơ chế.

**Câu hỏi để lại:** quy luật này chỉ đúng cho lập trình hay tổng quát hơn?

---

## [13] Quy luật và tính chuyển miền

**Trên MBPP**, 15 cặp, một lần chạy:

```
Δ_ceil = +0,0218 − 0,2392 × (chênh lệch năng lực)
R² = 0,60      p = 1e-05      điểm đổi dấu g* = 0,0913
```

Cần lưu ý ngay: **0/15** cặp có `Δ_ceil` dương với ý nghĩa thống kê, trong khi **3/15** cặp âm có ý
nghĩa. Do đó chỉ phát biểu được theo **chiều phủ định**: chênh lệch vượt 0,09 thì không nên sửa chữa.
Phân tích lực kiểm định cho thấy xác lập vùng dương cần lượng dữ liệu gấp khoảng **8 lần** toàn bộ
MBPP — không khả thi trên benchmark này.

**Kiểm tra chuyển miền.** Dùng đường hồi quy khớp trên MBPP để **dự báo** `Δ_ceil` trên MATH:

| Cặp | Chênh lệch | Đo được | Khoảng tin cậy 95% | MBPP dự báo | |
|---|---|---|---|---|---|
| 7B → 14B | 0,044 | −0,0140 | [−0,046; +0,018] | **+0,0108** | trong khoảng |
| 1.5B → 7B | 0,244 | **−0,1660** | [−0,208; −0,124] | −0,0361 | ngoài khoảng |
| 1.5B → 14B | 0,288 | −0,0680 | [−0,102; −0,034] | **−0,0471** | trong khoảng |

Hai trên ba dự báo nằm trong khoảng tin cậy ⇒ quy luật chuyển được, tức là quy luật về **giao thức**
chứ không riêng miền lập trình.

Hai lưu ý bắt buộc: (a) khoảng tin cậy rộng 0,064–0,084 nên phép kiểm có độ phân giải thấp, phải
phát biểu là *không bác bỏ được* chứ không phải *đã xác nhận*; (b) cặp 1.5B → 7B lệch **hệ thống**
(`B` = 0,208, gấp mười lần `A` = 0,020) và tái lập một phép đo trước đó trên cùng cặp.

**Câu hỏi để lại:** nếu `B` là thủ phạm, có chặn được `B` không?

---

## [14] Bản chất tín hiệu kiểm: **đúng đắn** hay **học được**?

Các bước [11]–[13] cho thấy `B` là thủ phạm. Trước khi hỏi có chặn được `B` không, cần hỏi:
**tín hiệu dùng để chặn có chất lượng thế nào?**

### 14a. Khi tín hiệu là ĐÚNG ĐẮN: bộ chọn hoàn hảo, không phá gì

Trên HumanEval, cùng model, **cùng 4 lượt sinh**, khác **duy nhất** ở nguồn tín hiệu kiểm —
chạy test thật (`exec3`) so với để LLM tự kiểm (`llm3`):

| Ô | greedy | maj@4 | **exec3** | llm3 | exec3 − llm3 | Số bài `exec3` phá | Số bài `llm3` phá |
|---|---|---|---|---|---|---|---|
| HE 1.5B (Kaggle) | 0,5375 | 0,4250 | **0,6000** | 0,4812 | +0,119 (5/5) | **0,0** | 2,8 |
| HE 1.5B (5090) | 0,5625 | 0,4313 | **0,6438** | 0,4375 | +0,206 (5/5) | **0,0** | 4,6 |
| HE 7B (5090) | 0,8000 | 0,7875 | **0,8812** | 0,7812 | +0,100 (4/5) | **0,0** | 2,6 |
| HE 7B (Kaggle) | 0,7938 | 0,7375 | **0,9000** | 0,7438 | +0,156 (5/5) | **0,0** | 3,2 |

**`exec3` phá 0 bài trong 20 trên 20 fold; `llm3` phá bài trong 20 trên 20 fold.**

Cơ chế: **`exec3` đạt đúng bằng `oracle@4`** (0,6438 và 0,8812). Tín hiệu đúng đắn là một **bộ chọn
hoàn hảo** — nó không sửa gì, chỉ chọn, và chọn không sai lần nào.

⚠️ **Mốc so sánh trung thực ở đây là `greedy`, không phải `maj@4`.** Trên code, bỏ phiếu **có hại**
(−0,113 và −0,131 so với greedy) vì lời giải là chuỗi dài hiếm khi trùng nhau nên "đa số" thành ra
chọn ngẫu nhiên. Theo mốc đúng, `exec3 − greedy` = **+0,063 đến +0,106**.

Đây là **kết quả được tái lập nhiều nhất của dự án**: 4 cấu hình, 2 model, 2 hệ phần cứng.

Một kết quả bổ sung làm rõ giới hạn: bộ kiểm chỉ có giá trị khi nó là **oracle về tính đúng**, không
phải khi nó là **một cách tính khác**. Trên MATH, dùng thực thi code (PAL) làm cách giải thay thế
vẫn **thua** suy luận bằng văn bản.

### 14b. Khi tín hiệu là HỌC ĐƯỢC: không phát hiện nổi một chữ số bị đổi

Thí nghiệm huấn luyện bộ phân loại đúng/sai trên lỗi **tiêm vào** (đổi một chữ số trong lời giải
vàng), rồi đánh giá khả năng chuyển giao sang lỗi **thật**.

Tiền đăng ký dự đoán: khả năng phân biệt lỗi **tiêm** sẽ **cao** (> 0,6), lỗi **thật** sẽ **thấp**
(< 0,2) — tức bộ phân loại học được hiện vật bề mặt rồi không chuyển giao được.

**Kết quả ngược hẳn dự đoán:**

| | Khả năng phân biệt |
|---|---|
| Lỗi **tiêm vào** (đổi một chữ số) | **+0,032** — gần bằng ngẫu nhiên |
| Lỗi **thật** | +0,219 (AUC 0,563) |

> **Phát hiện một chữ số bị đổi trong một lời giải vốn hoàn hảo còn khó hơn phân biệt lời giải
> đúng với lời giải sai thật.**

Và ngay cả khả năng phân biệt lỗi thật cũng **không chuyển thành độ chính xác**: bỏ phiếu có trọng
số theo điểm của bộ phân loại không hơn bỏ phiếu thường (chênh trung bình ≈ 0 qua các fold).
AUC 0,563 chỉ nhỉnh hơn mức ngẫu nhiên 0,50.

**Kết luận: đo được ≠ dùng được.**

### 14c. Phát biểu lại M2

Hai kết quả trên gộp lại cho một phát biểu sắc hơn nhiều so với *"tín hiệu độc lập thắng tín hiệu
tương quan"*:

> **`κ` phụ thuộc vào việc tín hiệu là ĐÚNG ĐẮN hay HỌC ĐƯỢC, không phụ thuộc vào việc nó mạnh
> hay độc lập.**
>
> - Tín hiệu **đúng đắn** (chạy test): `κ` ≈ 1, `B` = 0, đạt đúng trần oracle.
> - Tín hiệu **học được hoặc do prompt** (LLM kiểm, bộ phân loại huấn luyện): `κ` ≈ 0 (AUC 0,563),
>   `B` > 0 ở mọi fold.

Điều này giải thích vì sao mọi nỗ lực tìm tín hiệu cổng ở nhánh [14] tiếp theo đều thất bại: chúng
đều là tín hiệu **học được**, mà loại tín hiệu đó đã được chứng minh là không đủ.

Nó cũng khoanh vùng phạm vi áp dụng: **miền nào có bộ kiểm đúng đắn (code chạy được, chứng minh
hình thức) thì phối hợp đa tác tử có giá trị thật; miền nào không có thì không.**

**Câu hỏi để lại:** nếu không có tín hiệu đúng đắn, cơ chế định tuyến tốt nhất có thể đạt tới đâu?

---

## [15] Có chặn được B không: giới hạn trên của cơ chế định tuyến

**Ý tưởng tự nhiên.** Chỉ cho model mạnh xem artifact khi artifact có vẻ đúng.

**Trước khi xây dựng, tính giới hạn trên của chính ý tưởng đó:**

| | Độ chính xác | So với model mạnh đơn lẻ |
|---|---|---|
| Model mạnh đơn lẻ | 0,6980 | — |
| Luôn cho xem artifact | 0,5740 | −0,1240 |
| **Cổng lý tưởng** (chỉ cho xem khi artifact đúng) | **0,7160** | **+0,0180** |

Bộ phân loại thực tế cần đạt độ chính xác khoảng **89%** mới hoà vốn (ở 90% chỉ được +0,0020; ở 85%
đã lỗ −0,0060).

Thêm vào đó, hai lần thử tìm tín hiệu cổng khả thi đều bị chặn vì lý do kỹ thuật: một lần do pool
ứng viên suy biến, một lần do độ phủ tín hiệu chỉ đạt 69,9%.

**Kết luận thực tiễn** không phải "cần cổng tốt hơn", mà là **mặc định không cho xem artifact**.

---

## [16] Khép mạch: nghịch lý giữa [7] và [13]

**Nghịch lý.** [7] nói chênh lệch năng lực lớn mang lại +14,0 điểm so với model yếu. [13] nói chênh
lệch năng lực lớn làm `Δ_ceil` âm. Cùng một biến, hai dấu ngược nhau.

**Cách giải, dùng công cụ ở [10].** Hai kết quả dùng hai giao thức khác nhau:

- Verifier ở [7] là giao thức **tuyển chọn**: 43 sửa đúng, 1 làm hỏng ⇒ `B ≈ 0`.
- `V` ở [13] là giao thức **sửa chữa**: phải trả `B` theo cấu trúc, và `B` tăng theo chênh lệch.

Chênh lệch năng lực làm tăng **cả** `A` **lẫn** `B`. Kết quả cuối cùng do giao thức quyết định:

```
Tuyển chọn:  value ≈ A × κ − 0     → chênh lệch tăng thì giá trị tăng
Sửa chữa:    value ≈ A − B + C     → B tăng nhanh hơn nên giá trị giảm
```

Một chi tiết củng cố: trong thí nghiệm 15 cặp, `A` được chênh lệch giải thích tới `R²` = **0,824**,
còn `B` chỉ **0,345**. Nghĩa là `A` gần như do cặp model quyết định, còn `B` còn phần lớn phương sai
đến từ nơi khác — phù hợp với việc `B` là đại lượng phụ thuộc giao thức.

**Luận điểm cuối cùng:**

> Chênh lệch năng lực tạo ra cơ hội; giao thức quyết định cơ hội đó được khai thác hay bị phá huỷ.

---

## Ghi chú khi viết theo mạch này

- Mỗi mục nên mở bằng **câu hỏi kế thừa từ mục trước**, kết bằng **câu hỏi để lại cho mục sau**.
  Đây là thứ khiến báo cáo đọc như một quá trình chứ không phải một danh sách.
- Hai chỗ **nối ngược** là điểm mạnh, cần nêu rõ: [6] nối về [2] (hai phương pháp, một kết luận);
  [7] nối về [3] (giải thích được câu hỏi bỏ ngỏ trước đó).
- Các bước [4] và [5] là bước **phương pháp**, không có số liệu mới, nhưng là bản lề của toàn bài.
  Không nên rút gọn.
