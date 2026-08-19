# Câu hỏi thảo luận

Danh sách câu hỏi cần thống nhất trước hoặc trong quá trình viết. Mỗi câu ghi rõ **vì sao cần trả
lời**, **có thể trả lời bằng cách nào**, và **ảnh hưởng tới phần nào của báo cáo**.

Ba nhóm:
- **Nhóm A** — trả lời được bằng dữ liệu đã có, không cần chạy thêm GPU.
- **Nhóm B** — cần đọc tài liệu hoặc thảo luận, không cần dữ liệu.
- **Nhóm C** — chưa trả lời được; cần quyết định cách trình bày phần chưa biết.

---

## Nhóm A — Trả lời được bằng dữ liệu đã có

### A1. Verifier ở [2] có thật sự đạt `B ≈ 0` không, hay chỉ là `B` nhỏ?

Toàn bộ lập luận khép mạch ở [10] dựa trên khẳng định: giao thức tuyển chọn có `B = 0` **theo cấu
trúc**, còn giao thức sửa chữa phải trả `B`. Bằng chứng hiện có là "43 sửa đúng, 1 làm hỏng", tức
tỷ lệ hỏng khoảng 0,003.

Nhưng con số đó **không được đo bằng cùng định nghĩa** với `B = P(¬S ∧ I đúng ∧ V sai)` của chúng ta.

- Có thể tính `B` theo đúng định nghĩa từ lưu vết của thí nghiệm verifier không?
- Nếu `B` của verifier thực sự bằng 0 theo cấu trúc, hãy phát biểu **vì sao** — do verifier chỉ được
  chọn giữa hai phương án có sẵn, nên không thể tạo ra lời giải sai mới?
- Nếu `B` chỉ nhỏ chứ không bằng 0, luận điểm ở [10] cần sửa từ *"bằng 0 theo cấu trúc"* thành
  *"nhỏ hơn nhiều bậc"*. Đây là sửa đổi đáng kể về mức độ mạnh của khẳng định.

*Ảnh hưởng: §6, mảnh bằng chứng số 1. Đây là câu hỏi quan trọng nhất trong danh sách.*

### A1b. Kết quả +14,0 nên trình bày như thế nào sau khi có đối chứng token?

Số liệu token cho thấy `S1.5B + V7B` **kém hơn `S7B` một mình 10 điểm** trên GSM8K và **hoà** trên
MATH, dù rẻ hơn 12–22% token. Nghĩa là +14,0 là kết quả so với model **yếu**, không phải một cải
thiện độ chính xác so với phương án hiển nhiên nhất.

- Có nên giữ con số +14,0 ở vị trí nổi bật không, hay đưa nó xuống cùng bảng token?
- Phát biểu nào chính xác hơn: *"bất đối xứng năng lực tạo giá trị"*, hay *"bất đối xứng năng lực là
  phương án tiết kiệm chi phí ở giữa dải độ khó"*?
- Đây là **cùng một vấn đề baseline** mà nhánh Nguyên phát hiện qua `V − I`. Có nên trình bày nó như
  một phát hiện **xuyên suốt cả ba khối** ngay từ §1, thay vì như một phát hiện riêng của một nhánh?

Cách trình bày thứ hai làm báo cáo mạch lạc hơn nhiều, nhưng đòi hỏi viết lại §1 và §5.1.

*Ảnh hưởng: §0, §1, §5.1, §6. Đây là câu hỏi có ảnh hưởng rộng nhất trong danh sách.*

### A2. Aggregator hỏng trên MATH có cùng cơ chế với "tiếp xúc nội dung sai" không?

Mục [7] đưa ra một điểm nối ngược: aggregator hỏng trên MATH vì model yếu sai nhiều hơn nên
aggregator tiếp xúc với nhiều artifact sai hơn. Hiện tại đây mới là **lập luận**, chưa phải phép đo.

Số liệu có sẵn: aggregator sửa đúng 45,4% khi bất đồng trên GSM8K, so với 25,0% trên MATH. Và độ
chính xác solver: 0,6733 trên GSM8K so với 0,4133 trên MATH.

- Tỷ lệ artifact sai mà aggregator gặp trên hai miền là bao nhiêu? Có tính được từ dữ liệu router không?
- Chênh lệch 45,4% so với 25,0% có giải thích được **chỉ bằng** chênh lệch tỷ lệ artifact sai không,
  hay còn yếu tố khác?
- Nếu kiểm được, điểm nối ngược này trở thành bằng chứng thật và làm §6 mạnh hơn hẳn.

*Ảnh hưởng: [7], §5.3, §6.*

### A3. Hai phát hiện về bất đối xứng năng lực có nhất quán về mặt định lượng không?

[2] cho biết verifier 7B với solver 1.5B đạt +14,0 điểm; verifier cùng cỡ chỉ +3,0.
[6] cho biết `A` giảm theo chênh lệch với hệ số −0,192.

Hai kết luận cùng hướng, nhưng đo trên hai đại lượng khác nhau và hai benchmark khác nhau.

- Có quy đổi được về cùng một thang để so sánh không?
- Nếu không quy đổi được, cần nói rõ trong báo cáo rằng đây là **hai bằng chứng cùng hướng**, không
  phải hai phép đo của cùng một đại lượng. Cách phát biểu này an toàn hơn và vẫn đủ mạnh.

*Ảnh hưởng: §5.2, §6.*

### A4. Con số `g*` = 0,091 có ý nghĩa thực chất, hay là đặc thù của tập model đã dùng?

Điểm đổi dấu `g*` = 0,091 được suy ra từ 15 cặp tạo bởi 6 model cụ thể.

- Nếu thay tập model khác, `g*` có giữ nguyên không? Dữ liệu hiện có đủ để bàn về câu này không?
- Nên trình bày `g*` như một **hằng số** hay như một **đại lượng phụ thuộc bối cảnh**?
- Khuyến nghị cân nhắc: phát biểu ngưỡng theo dạng khoảng (khoảng 0,09) thay vì con số chính xác,
  vì khoảng tin cậy của hệ số chặn khá rộng.

*Ảnh hưởng: §5.5, và khuyến nghị thực tiễn ở §6.*

### A5. Nên xử lý tỷ lệ VOID 50% như thế nào trong báo cáo?

16 trên 32 lần chạy có tệp kết quả mang trạng thái VOID.

- Trình bày như một **chỉ dấu tích cực về phương pháp** (điều kiện hợp lệ đang hoạt động), hay như
  một **hạn chế về hiệu suất thí nghiệm**? Hay cả hai?
- Có nên phân loại 16 lần VOID theo nguyên nhân (lỗi đo, lỗi hạ tầng, mô hình không phù hợp) để
  người đọc thấy chúng không cùng một loại?
- Phần lớn nguyên nhân đến từ giới hạn GPU 14,6 GB của tầng miễn phí. Điều này nên nằm ở §7
  (phương pháp) hay §8 (hạn chế)?

*Ảnh hưởng: §7, §8, Phụ lục C.*

---

## Nhóm B — Cần đọc tài liệu hoặc thảo luận

### B1. Có công trình nào báo cáo `V − I` không?

Đây là câu hỏi **quan trọng nhất của toàn bộ báo cáo**, vì luận điểm ở §1 dựa hẳn vào nó.

Với mỗi công trình trong Self-Refine, Reflexion, CRITIC, Multi-Agent Debate, self-consistency, cần
xác định: **model sửa chữa và model bị sửa có cùng cỡ không**, và **bài báo so với baseline nào**.

- Nếu **không công trình nào** báo cáo `V − I`, đó là một khoảng trống rõ ràng và luận điểm rất mạnh.
- Nếu **có** một số công trình báo cáo, cần trích dẫn trung thực và điều chỉnh luận điểm thành
  *"phần lớn công trình không báo cáo"*, đồng thời nêu công trình nào có.
- Trường hợp thứ hai **không làm yếu báo cáo**, chỉ làm phát biểu chính xác hơn.

*Ảnh hưởng: §1, §2. Không viết §1 trước khi trả lời xong câu này.*

### B2. Kết quả của nhóm có mâu thuẫn với công trình nào không?

`RELATED_BASELINES.md` cho thấy debate kém hơn self-consistency ở 3/4 ô, trùng hướng với kết luận
của nhóm.

- Có công trình nào cho kết quả **ngược lại**, tức sửa chữa thắng tuyển chọn?
- Nếu có, điều kiện của họ khác gì (cỡ model, benchmark, cách đo)? Khung `H × κ − D` có giải thích
  được sự khác biệt không?
- Một công trình mâu thuẫn được giải thích bằng khung của mình là bằng chứng **mạnh hơn** so với
  việc chỉ liệt kê các công trình đồng thuận.

*Ảnh hưởng: §2, §6.*

### B3. Đặt tên cho hai giao thức như thế nào?

Hiện dùng "tuyển chọn" và "sửa chữa". Cần kiểm tra hai tên này có trùng với thuật ngữ đã dùng phổ
biến trong tài liệu không, và có gây hiểu nhầm không.

- "Tuyển chọn" có bao gồm cả reranking và best-of-n không?
- "Sửa chữa" có phân biệt được với "refinement" và "revision" trong các bài đã đọc không?
- Có nên định nghĩa hai giao thức bằng **`B`** thay vì bằng tên gọi: giao thức nào không cho phép
  tạo lời giải mới thì `B = 0`?

Định nghĩa theo `B` có ưu điểm là chính xác và gắn trực tiếp với khung lý thuyết.

*Ảnh hưởng: §3, và tính nhất quán thuật ngữ toàn bài.*

### B4. Phạm vi khẳng định của báo cáo nên đến đâu?

Dữ liệu hiện có: hai benchmark chính (MBPP, MATH), thêm GSM8K và HumanEval ở khối nhóm; model từ
1.5B đến 32B; chỉ greedy decoding.

- Phát biểu kết luận cho **các model cỡ nhỏ đến trung bình trên bài toán suy luận**, hay phát biểu
  tổng quát hơn?
- Kết luận có được kỳ vọng giữ nguyên với model rất lớn không? Có lý do nào để nghi ngờ không?
- Cần một câu giới hạn phạm vi ngay trong phần tóm tắt, hay để ở §8 là đủ?

*Ảnh hưởng: Tóm tắt, §8, §9.*

---

## Nhóm C — Chưa trả lời được, cần quyết định cách trình bày

### C1. Trình bày `Δ_honest` chưa có kết luận như thế nào?

Đại lượng `Δ_honest` (giao thức sinh độc lập trước có thắng model mạnh đơn lẻ không) đã qua **năm
lần chạy** mà chưa có kết luận, đều do giới hạn bộ nhớ GPU.

- Nêu như một hướng còn mở, hay lược bỏ khỏi báo cáo?
- Nếu nêu, có nên trình bày cả năm nguyên nhân thất bại? Điều này minh hoạ chi phí thực của việc
  nghiên cứu trên GPU tầng miễn phí, nhưng cũng chiếm dung lượng.
- Thí nghiệm còn thiếu 2 trên 6 ô; hoàn tất cần khoảng 40 phút GPU. Có đáng chạy nốt không?

*Ảnh hưởng: §5.8 (nếu có), §8.*

### C2. Thành phần `κ` chưa giải quyết được — trình bày ra sao?

Ba lần thử tìm tín hiệu cổng khả thi đều không thành công. Đồng thời đã tính được giới hạn trên của
cơ chế này chỉ là +0,018.

- Nên trình bày `κ` như một **hướng nghiên cứu thất bại**, hay như một **kết quả phủ định có giá trị**
  (đã chứng minh trần thấp nên không đáng theo đuổi)?
- Cách thứ hai đúng hơn về mặt logic, nhưng cần lập luận cẩn thận để không giống biện minh.

*Ảnh hưởng: §5.6, §8.*

### C3. Hai chuẩn kiểm chứng — hợp nhất hay tách riêng?

Khối nhóm dùng thanh sai số qua 5 fold; khối Nguyên dùng tiền đăng ký và điều kiện hợp lệ.

Ba phương án đã nêu trong `HUONG_DAN_CONG_TAC.md` mục 5. Phương án 1 (ghi rõ hai chuẩn, xếp kết quả
khối kia vào mức B) được khuyến nghị, nhưng cần cả nhóm đồng ý.

- Việc xếp kết quả của một thành viên vào "mức B" có gây hiểu nhầm rằng kết quả đó kém tin cậy hơn không?
- Có cách diễn đạt nào phản ánh đúng rằng đây là **hai chuẩn khác nhau**, chứ không phải **một chuẩn
  cao và một chuẩn thấp**?

Đây vừa là vấn đề học thuật vừa là vấn đề trình bày công bằng giữa các thành viên. Nên thống nhất ở
Bước 0.

*Ảnh hưởng: §7, và cách phân bố nội dung giữa phần thân với phụ lục.*

---

## Thứ tự đề nghị

| Thời điểm | Câu hỏi |
|---|---|
| Bước 0, cả nhóm cùng bàn | **C3** (hai chuẩn), **B3** (đặt tên giao thức), **B4** (phạm vi) |
| Trước khi viết §1 | **B1** (có ai báo cáo `V − I` không) |
| Trong lúc viết §5–§6 | **A1** (verifier có `B ≈ 0` không), **A1b** (trình bày +14,0), **A2** (điểm nối ngược) |
| Khi rà soát cuối | **A4** (`g*`), **A5** (VOID), **C1**, **C2** |

**A1, A1b và B1 là ba câu quan trọng nhất.** A1 quyết định độ mạnh của luận điểm khép mạch ở §6; B1
quyết định luận điểm mở đầu ở §1 có đứng được hay không.

---

## Nhóm D — Phát sinh từ đợt kiểm định độc lập (sáu agent, đọc toàn bộ kết quả)

### D1. Mâu thuẫn chưa giải: aggregator trên MATH, hai lần chạy 5-fold cho **dấu ngược nhau**

| Lần chạy | Thiết lập | `PSVA − PSV` | Fold |
|---|---|---|---|
| `res_nf_m15` | MATH 1.5B, 5 fold × 100 | **−0,064** | 5/5 âm |
| `res_b4_m15` | MATH 1.5B, 5 fold × 40 | **+0,080** | 5/5 dương |

Cùng task, cùng model, cùng đại lượng, **ngược dấu**, và mỗi lần chạy đều "nhất quán 5/5" trong nội
bộ nó. Chưa tài liệu nào của dự án nêu mâu thuẫn này.

- Khác biệt đã biết: cỡ fold (100 so với 40) và độ chính xác nền `PSV` (0,416 so với 0,380).
- Con số −6,4 là một trong những số được trích nhiều nhất của dự án. **Nếu mâu thuẫn này không giải
  được thì phải nêu nó trong báo cáo**, không được chỉ trích một phía.
- Đề xuất: kiểm xem hai lần chạy có dùng cùng định nghĩa `PSVA` không (đặc biệt là có fallback
  `\boxed` hay không — xem mục [4] của `MACH_DAN_DAT.md`).

*Ảnh hưởng: [4], [8], §5.3. Cần giải trước khi nộp.*

### D2. Một nhánh thí nghiệm chưa từng được viết ra, và nó **không hợp lệ**

`res_arc_agi3_stepcheck_scaling_a/b` (trùng với `res_scaling_a/b`): nghiên cứu bộ kiểm theo bước
trên ARC-AGI-3, ba cỡ model 7B/14B/32B. Khả năng phân biệt tăng đơn điệu theo cỡ
(0,337 → 0,472 → 0,529). **Nhưng `VALID_parse` = false ở cả ba cỡ** (tỷ lệ hỏng phân tích
0,232/0,219/0,224, vượt ngưỡng 0,20 của chính dự án), và ô 14B có `degenerate_rate` 0,9125 vượt
ngưỡng 0,90.

⇒ **Không được trích bất kỳ số nào từ nhánh này.** Nêu ở Phụ lục C nếu muốn cho đầy đủ.

### D3. Một giới hạn của kết quả `exec3` cần nêu

`res_ex_g7`: trên GSM8K 7B, bộ kiểm bằng thực thi đạt độ chính xác **0,8369** — cao nhất trong toàn
bộ nhóm thí nghiệm — nhưng vẫn **lỗ ròng** (26 lần phá so với 6 lần sửa, giá trị ròng −0,08).

Lý do: solver 7B trên GSM8K đã gần bão hoà (0,916), nên gần như không còn gì để sửa mà lại còn nhiều
thứ để phá. **Kết quả `exec3` ở §5.8 không được phát biểu như một quy luật phổ quát** — nó đúng khi
còn dư địa, và sai khi model nền đã bão hoà. Điều này khớp với mục [5] (mẫu số) và với phát biểu hợp
nhất "giá trị bộ kiểm = khoảng cách `oracle@k − maj@k`".

*Ảnh hưởng: §5.8. Nên thêm một câu giới hạn.*

### D4. Kết quả sửa lỗi rò rỉ đã chạy xong nhưng chưa ai viết

`results_disc_leakfix_gsm8k` và `results_disc_leakfix_math` là bản chạy lại sạch của hai lần chạy
từng bị tuyên vô hiệu vì rò rỉ adapter (`res_wf_g15`, `res_wf_m15`, rò rỉ 0,06 > ngưỡng 0,05).
Bản sửa cho `adapter_leak` = −0,0334 và −0,0500, **cả hai `VALID_leak` = true**, AUC 0,8412 và 0,9330.

Đây là lời giải cho một vấn đề mở đã được ghi trong tài liệu, nhưng kết quả **chưa được trích ở đâu**.
Cần quyết định có đưa vào báo cáo không.
