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

---

## Nhóm E — Đề xuất sửa chuẩn thống kê: sàn nhiễu 5 điểm đang quá thận trọng

### E1. Ngưỡng 5 điểm được suy ra cho **một phép đo đơn lẻ**, nhưng đang áp cho kết quả **5 fold**

**Cách ngưỡng hiện tại ra đời** (`../docs/RESULTS.md` §0): chạy cùng cấu hình trên 5 fold ×100 bài
cho `V_gain` dao động +1,0 đến +8,0, độ lệch chuẩn **2,65 điểm**. Rồi:

```
std giữa các fold (fold_n=100)         = 2,65 điểm
quy đổi sang MỘT phép đo n=250         = 2,65 × √(100/250) = 1,68
hiệu của HAI phép đo độc lập n=250     = 1,68 × √2         = 2,37
2σ của hiệu đó                          = 4,74  →  làm tròn thành NGƯỠNG 5 ĐIỂM
```

**Ngưỡng này đúng cho tình huống: một phép đo n=250, so với một phép đo n=250 khác.**
Nhưng phần lớn kết quả của dự án được đo trên **5 fold**, và khi đó thông tin nhiều hơn hẳn.

### Với 5 fold thì ngưỡng đúng là bao nhiêu

Khi có 5 fold, đại lượng cần dùng là **sai số chuẩn của trung bình**, không phải độ lệch chuẩn của
một phép đo:

```
SE của trung bình 5 fold  = 2,65 / √5  = 1,19 điểm
t(0,975; dof = 4)                      = 2,776
ngưỡng ý nghĩa 95%        = 2,776 × 1,19 = 3,29 điểm
```

⇒ **Ngưỡng đúng là ~3,3 điểm, không phải 5.** Ngưỡng hiện tại **thận trọng gấp 1,5 lần** mức cần thiết.

### Và "5/5 fold cùng dấu" là thông tin **độc lập** với độ lớn

| Số fold cùng dấu | p (một phía, phép thử dấu) |
|---|---|
| **5/5** | **0,031** — đã đủ ý nghĩa ở mức 0,05 |
| 4/5 | 0,188 |
| 3/5 | 0,500 |

Nghĩa là **"5/5 fold cùng dấu" tự nó đã là bằng chứng ở p = 0,031**, bất kể hiệu ứng lớn hay nhỏ.
Quy tắc hiện tại yêu cầu **đồng thời** 5/5 fold **và** hiệu ứng > 5 điểm — tức đòi hai điều kiện
trong khi mỗi điều kiện đã đủ riêng.

### Kiểm lại bằng t-test trên chính dữ liệu fold

| Đại lượng | Trung bình | SE | t | p | Kết luận |
|---|---|---|---|---|---|
| MATH: thêm `V` vào S7B | **+7,67** | 1,53 | +5,00 | **0,0075** | có ý nghĩa |
| MATH: `A_gain` (nf_m15) | **−6,40** | 0,72 | −8,83 | **0,0009** | có ý nghĩa |
| MATH: `V_gain` (nf_m15) | +1,40 | 1,00 | +1,40 | 0,235 | không |

t-test cho **cùng kết luận** với quy tắc 5 điểm ở các trường hợp rõ ràng, nhưng xử lý được vùng
biên mà quy tắc thô bỏ sót.

### Kết quả đang bị chôn oan

| Kết quả | Hiệu ứng | Quy tắc 5 điểm | Ngưỡng 3,3 + phép thử dấu |
|---|---|---|---|
| `SOLVEJUDGE`: `loop − PSVA` trên MATH, **cùng chi phí** (4,2 so với 4,0 lượt) | **+4,0**; 4 fold thắng, 1 hoà, 0 thua | dưới sàn ⇒ **không tính** | **có ý nghĩa** (t = 3,21; p = 0,033) |

Đây là một trong rất ít kết quả **dương, cùng ngân sách, 5/5 fold** của toàn dự án — và quy tắc
hiện tại loại nó.

### Lý lẽ NGƯỢC LẠI, cần cân nhắc trước khi đổi

Dự án chạy khoảng **200 vòng**. Với α = 0,05 và 200 phép thử, kỳ vọng có **~10 dương tính giả**.
Ngưỡng thận trọng bù đắp phần nào cho vấn đề **so sánh bội**.

Nhưng cách bù đó **thô và sai chỗ**: nó phạt đều mọi kết quả thay vì phạt theo số phép thử thực sự
đã làm trên cùng một câu hỏi. Cách đúng hơn: **báo cáo khoảng tin cậy thay vì chỉ báo "đạt/không
đạt"**, và nêu rõ số phép thử đã chạy trên cùng một giả thuyết.

### Đề xuất

1. **Bỏ ngưỡng cứng 5 điểm** cho kết quả đo trên nhiều fold.
2. **Thay bằng: t-test trên các fold, báo cáo khoảng tin cậy 95%.** Ngưỡng ~3,3 điểm là hệ quả, không
   phải quy tắc riêng.
3. **Giữ phép thử dấu 5/5 như một tiêu chí bổ sung**, không phải điều kiện bắt buộc kèm theo.
4. **Giữ ngưỡng 5 điểm cho các phép đo ĐƠN LẺ** (không có fold) — với chúng thì con số đó vẫn đúng.
5. Với các giả thuyết đã thử nhiều lần, **nêu rõ số lần thử** thay vì nâng ngưỡng.

⚠️ **Đây là chuẩn của khối nhóm, không phải của riêng ai.** `RESULTS.md` do Tùng Dương biên soạn và
nhiều kết luận hiện tại đang dựa trên ngưỡng 5 điểm. **Cần cả nhóm đồng ý trước khi đổi**, và nếu
đổi thì phải rà lại toàn bộ các kết quả đã bị hạ cấp để xem cái nào đổi trạng thái.

*Ảnh hưởng: §7 Phương pháp luận, và có thể một số mục trong §5. Nên bàn ở Bước 0.*


### E2. Kết quả rà lại toàn bộ dưới chuẩn đề xuất *(chưa áp dụng — mọi thay đổi chờ nhóm quyết ở Bước 0)*

Hai đợt kiểm độc lập: (a) t-test trên **131 đại lượng hiệu ứng** có cấu trúc fold trong toàn bộ
artifact thô; (b) rà 19 tài liệu tìm các kết luận từng bị hạ cấp. Mọi giá trị t dưới đây dùng
**sample std** (ddof = 1, thận trọng hơn số std lưu trong tệp khoảng 1,12 lần) và được tính lại
trực tiếp từ mảng giá trị fold, không lấy từ số tổng hợp.

#### Bốn kết quả chủ lực của `RESULTS.md` §1a: TẤT CẢ ĐỨNG VỮNG

| Kết quả | t | p | KTC 95% | P(hiệu ứng > 0) |
|---|---|---|---|---|
| S1.5B + V7B, MATH, +14,0 | **5,85** | 0,0043 | [+7,4; +20,6] | 99,8% |
| Riêng phần verifier mạnh hơn (V7 − V15), +11,0 | **4,30** | 0,0127 | [+3,9; +18,1] | 99,4% |
| Pipeline đầy đủ so với PS, GSM8K, +5,6 * | **6,89** | 0,0023 | [+3,3; +7,9] | 99,9% |
| Verifier GSM8K, +4,4 | **3,32** | 0,0295 | [+0,7; +8,1] | 98,5% |

*Cột `P(hiệu ứng > 0)` là xác suất một phía suy từ phân phối t (tương đương cách đọc Bayes với
prior phẳng). Chuẩn "có ý nghĩa hai phía 95%" tương ứng P(>0) ≥ 97,5%. Cách trình bày này giữ được
thông tin ở các ca không đạt chuẩn thay vì chỉ ghi đạt/trượt.*

\* Ghi chú truy nguồn: con số +5,6 tính từ `PSVA − PS` theo fold trong `res_nf_g15` — mốc là
**planner + solver**, không phải solver đơn độc thuần tuý. Câu chữ trong báo cáo cần phản ánh đúng.

Đáng chú ý: con số +4,4 vốn **đã nằm dưới ngưỡng 5 điểm cũ** mà vẫn được coi là xác lập — tức quy
tắc cũ trong thực tế được áp không nhất quán, tiêu chí thao tác thật là "5/5 fold". Chuẩn mới thay
bằng p-value thật.

#### Được phục hồi (sau khi ĐỐI CHIẾU CỜ HỢP LỆ — bước mà thống kê thuần tuý bỏ qua)

Quét thô cho 9 ứng viên qua t-test, nhưng **thống kê không phục hồi được kết quả từ lần chạy vô
hiệu**. Sau đối chiếu:

**Bị loại dù t-test qua:**
- `wsum_minus_maj` và `rerank_minus_maj` từ `res_wf_g15` — lần chạy này có `adapter_leak` = 0,0606
  \> ngưỡng 0,05, `VALID_no_leak` = false, **đã bị tuyên vô hiệu từ trước**; bản chạy sạch là
  `results_disc_leakfix_*`.
- `wsum_minus_maj` từ `results_injected_classifier` — lần chạy phụ đã bị thay thế bởi bản
  "H37 HOÀN TẤT".

**Giữ lại (5 + 1 từ tài liệu):**

| Đại lượng | Nguồn | Hiệu ứng | KTC 95% | t | p | Fold |
|---|---|---|---|---|---|---|
| `loop − PSVA` (MATH, cùng chi phí) | `results_solvejudge/math` | **+4,0** | [+0,5; +7,5] | 3,21 | 0,033 | 4 thắng, 1 hoà — P(>0) = 98,4% |
| **`V_gain` trên MATH 7B** | `res_nf_m7` | **+4,4** | [+1,5; +7,3] | 4,27 | 0,013 | 5/5 — P(>0) = 99,4% |
| `V_gain` trên GSM8K 1.5B | `res_nf_g15` | +4,4 | [+0,7; +8,1] | 3,32 | 0,030 | 5/5 — P(>0) = 98,5% |
| `gain_forced` (ép vai fallback) | `res_af_m` | **−2,4** | [−4,1; −0,7] | −4,00 | 0,016 | 0/5 — P(<0) = 99,2% |
| `patch_minus_std` | `res_pa2_m15` | −3,5 | [−6,0; −1,0] | −3,81 | 0,019 | 0/5 |
| `arm_minus_ctl` (3S1V, MATH 1.5B) | `res_a_3s1vs_m` | −3,5 | [−6,3; −0,7] | −3,50 | 0,025 | — |

Khoảng tin cậy làm rõ vì sao các hiệu ứng 2–4 điểm này hợp lệ: **cận dưới của chúng đều nằm cùng
phía với 0**. Một hiệu ứng nhỏ với các fold đồng đều đáng tin hơn một hiệu ứng lớn với các fold
đánh nhau — đó chính là điều t-test đo mà quy tắc "ngưỡng độ lớn" không đo được.

**Phục hồi đáng chú ý nhất: `V_gain` = +4,4 trên MATH ở 7B.** `RESULTS.md` §1d ghi *"Verifier trên
MATH chưa xác lập"* — nhưng số đó đo ở **1.5B** (+1,4; p = 0,235, đúng là không). Ở **7B** hiệu ứng
có ý nghĩa rõ. Điều này **củng cố thêm luận điểm bất đối xứng năng lực** (§5.1): giá trị của verifier
xuất hiện cùng với năng lực.

#### MẤT ý nghĩa (1)

| Đại lượng | Nguồn | Hiệu ứng | Vấn đề |
|---|---|---|---|
| `trim_minus_full` (MATH 7B) | `res_rc_m7b` | −13,9 điểm | chỉ **k = 3 fold** ⇒ t_crit = 4,303; t = −3,57; **p = 0,070** |

Từng được coi là xác lập vì \>5 điểm và 3/3 cùng dấu. Chuẩn mới cho thấy 3 fold là quá ít để xác
nhận — **chuẩn mới không chỉ phục hồi mà còn siết**, đây là bằng chứng nó không phải "hạ ngưỡng
cho dễ đậu".

#### Nhóm thứ tư: bị chôn vì đòi 5/5 cùng dấu, không phải vì ngưỡng độ lớn

5 đại lượng có |hiệu ứng| ≥ 5 điểm nhưng chỉ 4/5 fold cùng dấu nên quy tắc cũ loại; t-test qua
nhưng phần lớn ở vùng biên: `SVV_minus_maj3` (`res_bg_m15`, +6,5; p = 0,019) là ca rõ nhất; ba ca
`maj3_minus_PSV` và một ca `pct_gap_closed` đều biên — chỉ ghi nhận, không phục hồi.

#### So sánh bội — bắt buộc ghi kèm mọi trích dẫn từ E2

131 phép thử ở α = 0,05 ⇒ kỳ vọng **~6,6 dương tính giả** do ngẫu nhiên. Danh sách phục hồi ở trên
là **danh sách ứng viên đã xếp lại hạng**, không phải chân lý mới; nếu đưa vào báo cáo cần hiệu
chỉnh Benjamini–Hochberg hoặc ghi rõ số phép thử. Các ca p trong khoảng 0,02–0,05 (tức phần lớn
bảng phục hồi) là những ca dễ là dương tính giả nhất.

#### Phạm vi không bị ảnh hưởng

Khối tiền đăng ký (`Δ_ceil`, `A/B/C`, `g*`, H94d/H96/H97/H99b) dùng McNemar/bootstrap ghép cặp,
không dùng sàn nhiễu fold — **không con số nào của khối đó thay đổi**.


### E3. Trả lời hai câu hỏi phát sinh: các ca +3,3/+2,7 và khả năng chạy lại

#### ORPO +3,3 (3/5 fold): KHÔNG BAO GIỜ qua được — chứng minh bằng chặn, không cần dữ liệu

Ngưỡng ~3,3 điểm **không phải cổng độ lớn** — phép thử thật là `t = trung bình / (std/√5) > 2,776`,
và **dấu fold lẫn lộn làm std phình**. Với trung bình +3,3 mà **2 trên 5 fold không dương**, trường
hợp *thuận lợi nhất có thể tồn tại* là hai fold đúng bằng 0 và ba fold còn lại bằng nhau (+5,5):

```
folds tốt nhất = [0; 0; +5,5; +5,5; +5,5]   →   t tối đa = 2,449  <  2,776
```

Mọi cấu hình thực tế (fold âm thật sự, ba fold dương lệch nhau) chỉ cho t **thấp hơn nữa**.
⇒ **ORPO +3,3 bị loại vĩnh viễn, không cần tìm dữ liệu fold, không cần chạy lại.**

#### Few-shot +2,7 (4/5 fold): ĐÃ PHÁN — không đạt, dứt khoát

Dữ liệu fold gốc **vẫn còn trên Kaggle** (`<tài khoản RTX>/fewshot-folds-math`, Đức chạy ngày 06-08) và
đã được tải về `results_fsfold/math_folds/`, **không cần chạy lại**:

```
by_fold (điểm) = [+10,0; +6,7; +6,7; +3,3; −13,3]
t = 0,64   p = 0,56   KTC 95% [−8,8; +14,2]   P(>0) = 72%
```

Phép chặn trước đó (t tối đa 4,0) giả định fold âm nằm sát 0; thực tế nó là **−13,3** — một fold
sập nặng che giấu sau nhãn "4/5". Khoảng tin cậy rộng gần 23 điểm. **Loại dứt khoát.**
Đây cũng là minh hoạ tốt cho vì sao "x/5 fold cùng dấu" không thay được t-test: nhãn 4/5 không nói
fold trái dấu *tệ đến mức nào*.

#### `PROMPT_SWAP` MATH +5,3: ĐÃ PHÁN — không đạt

Output gốc còn trên Kaggle (`tbmdemi/promptswap-folds-math`), tải về `results_psfold/math/`:

```
swap − normal, by_fold (điểm) = [−3,3; +3,3; +13,3; +3,3; +10,0]
t = 1,84   p = 0,14   KTC 95% [−2,7; +13,4]   P(>0) = 93%
```

4/5 fold dương nhưng độ phân tán quá lớn. P(>0) = 93% — *gợi ý* nhưng dưới chuẩn 97,5%.
Lưu ý điều này **không làm yếu** kết luận chính của `PROMPT_SWAP.md` (danh tính vai không quan
trọng): việc `swap` không khác `normal` có ý nghĩa lại càng **thuận** với kết luận đó.

#### Bài học vận hành: KHÔNG cần chạy lại — output vẫn nằm trên Kaggle

Cả hai ca "chưa phán được" đều được giải quyết bằng cách **tải output cũ về** (kernel của Đức trên
tài khoản `<tài khoản RTX>`, kernel promptswap trên `tbmdemi`), không tốn giây GPU nào. Quy tắc rút ra:
**trước khi tính chuyện chạy lại, quét output còn trên Kaggle của mọi tài khoản fleet** — các
kernel folds đều đã lưu `by_fold` trong `summary.json`, chỉ là chưa ai kéo về.

**Tổng kết đợt vớt vát:** hai ca treo đều ra phán quyết **không đạt** (few-shot t = 0,64;
promptswap t = 1,84). Không thêm được kết quả dương nào ngoài sáu ca đã phục hồi ở E2 — nhưng
"treo" đã thành "dứt khoát", và đó cũng là giá trị.

---

### A6. "Khi model mạnh sai thì sửa có tốt hơn không?" — phân tích tầng I-sai *(mức B, hậu nghiệm từ trace đã niêm phong)*

Câu hỏi tự nhiên (và người phản biện chắc chắn sẽ hỏi): *có trường hợp nào `V` tốt hơn `I` không,
nhất là ở những bài `I` sai?*

**Cái bẫy điều kiện hoá cần nói trước:** trên tầng "`I` sai", `I` đạt 0% *theo định nghĩa* — nên
`V` luôn "thắng" ở đó một cách tầm thường. Câu hỏi chỉ có nghĩa vận hành nếu **biết trước** khi
nào `I` sai; đó chính là bài toán `κ`.

**Bảng 2×2×2 trên MATH (H94d, chấm lại từ raw, n = 500):**

| Tầng | n | `V` đúng |
|---|---|---|
| `S` đúng, `I` đúng | 228 | 99,6% |
| **`S` đúng, `I` sai** | **11** | **90,9%** |
| `S` sai, `I` đúng *(vùng rủi ro)* | **121** | 36,4% → tức **`V` phá 63,6%** |
| Cả hai sai | 140 | **4,3%** |

Trên MBPP (15 cặp, H97): `P(V đúng | I sai, S đúng)` = 43–87%; `P(V đúng | cả hai sai)` = 3–18%;
`P(V phá | I đúng, S sai)` = 30–72%. **Không cặp nào có `V − I` dương** (tốt nhất −0,030).

**Ba điều bảng này nói:**

1. **Giao thức sửa là ống dẫn, không phải bộ sửa lỗi.** Khi `S` đã đúng mà `I` sai, `V` khôi phục
   ~91% — artifact đúng *chuyển giao* đáp án gần như trọn vẹn. Khi **cả hai** sai, `V` chỉ cứu 4,3%
   — nó gần như không bao giờ *sáng tạo* ra lời giải mà không model nào có.
2. **Số học tầng:** tầng khai thác được (`S` đúng, `I` sai) chỉ **11 bài (2,2%)**; tầng rủi ro
   (`I` đúng, `S` sai) là **121 bài (24%)** với tỷ lệ phá 63,6%. Đó là dạng thô nhất của lập luận
   ngân sách `A` so với `B`.
3. **Trần của router "biết-khi-`I`-sai":** nếu có oracle phát hiện đúng lúc `I` sai và chỉ khi đó
   mới dùng `V`: lợi = `P(V∧¬I)` = 16/500 = **+3,2 điểm** trên MATH (MBPP: ~+4 đến +7,5 tuỳ cặp).
   Cao hơn trần cổng-theo-artifact (+1,8) nhưng đòi một tín hiệu phát hiện **lỗi của chính model
   mạnh** — đúng loại tín hiệu mà thí nghiệm H37 cho thấy "đo được (AUC 0,893) nhưng không dùng
   được (+2,4 điểm, 2/5 fold)".

*Nguồn: `results_H97/traces_H97.json` (boolean từng bài), `results_H94d/traces_H94d.json` (chấm
lại bằng đúng `_bx`/`eq`; khớp acc đã ghi .478/.698/.574). Phân tích hậu nghiệm — mức B.*

#### A6b. "S đúng thì giữ nguyên S, cần gì V sửa?" — đúng, và đó chính là `CEIL`

Nhận xét chính xác — nhưng có ba tầng cần tách:

**1. "Giữ S khi S đúng" đòi biết S đúng — tức một oracle.** Chiến lược *"S đúng thì giữ S, ngược
lại lấy V"* chính là **định nghĩa của `CEIL`**. Nó không chạy được trong thực tế vì không ai biết
trước S đúng hay sai; nó là chặn trên.

**2. Pipeline thật KHÔNG giữ S.** Trong giao thức sửa được triển khai, đầu ra cuối là **V** — đáp
án của S bị vứt, bài làm của S chỉ là ngữ cảnh đưa cho model mạnh. Vì vậy con số 90,9% ở A6 đo
đúng cái pipeline thật làm: *tỷ lệ V giữ lại được đáp án đúng của S*. Nó là hiệu suất truyền của
ống dẫn, không phải một lựa chọn "sửa hay giữ".

**3. Giữ-S-hoàn-hảo đáng giá bao nhiêu?** Tính trực tiếp `CEIL − V` = P(S đúng ∧ V làm mất):

| | V luôn | CEIL (giữ-S oracle) | Chênh | `I` một mình |
|---|---|---|---|---|
| MATH | 0,574 | 0,578 | **+0,004 (đúng 2 bài/500)** | **0,698** |
| MBPP (15 cặp) | — | — | +0,018 đến +0,080 | — |

Trên MATH, oracle giữ-S gần như **vô giá trị** — vì V vốn đã giữ được 99,6%/90,9%. Trên code đáng
giá hơn (retention thấp hơn) nhưng vẫn là con số nhỏ.

**Điểm chốt:** kể cả khi tặng không pipeline cái oracle giữ-S (tức dùng `CEIL`), ở chênh lệch năng
lực lớn nó **vẫn thua gọi thẳng `I`**: MATH 0,578 so với 0,698. Vấn đề không nằm ở chỗ "quên giữ
S" — mà ở chỗ **V phá tầng (S sai, I đúng)**, và giữ S không cứu được tầng đó (S ở đó vốn sai).
Cách duy nhất bảo vệ tầng đó là **đừng đưa bài của S cho model mạnh xem** — tức gọi thẳng `I`.

Đây cũng chính là lý do `Δ_ceil = CEIL − I` là đại lượng trung tâm của cả phân tích: nó **đã tặng
sẵn** cho pipeline cái oracle mà nhận xét này đề xuất, rồi mới hỏi *"kể cả vậy, có thắng nổi `I`
không?"* — và câu trả lời ở chênh lệch nhỏ là "đôi khi, không đáng kể" (tối đa +0,030, không ca
nào có ý nghĩa), ở chênh lệch lớn là "không".

### A7. Chi phí token giữa hai cỡ model không cùng đơn vị — hiệu chỉnh làm đổi một kết luận

Nhận xét từ người đọc: *một token của 7B khác một token của 1.5B*. Đúng, và khi kiểm thì lộ ra
**hai lỗi chồng nhau** trong so sánh chi phí của cấu hình bất đối xứng (`S1.5B + V7B` so với `S7B`):

1. **Thiếu token:** trường đo gốc (`tok7_*` trong `res_bs_g`, `res_bs_m`) chỉ đếm token **do model
   7B sinh** — token của solver 1.5B trong cấu hình bất đối xứng không được cộng vào đâu cả.
2. **Sai đơn vị:** chi phí suy luận mỗi token tỷ lệ với số tham số — token 7B đắt gấp ~4,67 lần
   (danh nghĩa 7/1,5) hay ~4,95 lần (tham số thực 7,62B/1,54B) token 1.5B.

**Hiệu chỉnh** — chi phí = Σ(tham số × token); token 1.5B ước từ độ dài ký tự median
(600 ký tự GSM8K, 1319 MATH; độ nhạy chars/token quét 3,0–4,0; cả hai bộ tham số):

| | Token thô 7B (như tài liệu gốc) | **Trọng số FLOP** |
|---|---|---|
| GSM8K: asym / S7B | 0,88 — "rẻ hơn 12%" | **1,00–1,05** — tiết kiệm biến mất |
| MATH: asym / S7B | 0,78 — "rẻ hơn 22%" | **0,92–0,96** — còn rẻ hơn 3–8% |

**Kết luận đổi:** trên GSM8K, cấu hình bất đối xứng **bị chi phối hoàn toàn** (kém 10 điểm và
không hề rẻ hơn); trên MATH nó chỉ là phương án tiết kiệm **biên** (~3–8%, độ chính xác hoà).
Câu *"lựa chọn chi phí hợp lệ ở giữa dải độ khó"* trong `EFFICIENCY.md` §4 cần hạ xuống tương ứng.

**Ghi chú thiên vị còn lại:** hiệu chỉnh chưa tính **prefill** — model 7B trong cấu hình bất đối
xứng còn phải *đọc* toàn bộ bài làm của 1.5B (FLOP tỷ lệ với token vào), nên chi phí thật của nó
còn cao hơn số ở bảng. Các so sánh chi phí **trong cùng một cỡ model** (2,9×/6,63× ký tự ở §5.1;
router theo lượt gọi ở §5.6; exec3/llm3) **không bị ảnh hưởng** vì token cùng giá.

*Đã sửa tại: `BAO_CAO.md` §5.5, `MACH_DAN_DAT.md` [7], `THUAT_NGU.md` §2. Mức: hiệu chỉnh số học
trên dữ liệu mức A, phần ước lượng token 1.5B là xấp xỉ có nêu độ nhạy.*

---

## Nhóm F — từ vòng phản biện độc lập về giọng văn (v1.1, 2026-08-20)

Một agent đóng vai reviewer đã rà toàn bộ `BAO_CAO_NHOM13.tex`; ~50 chỗ giọng văn thiếu trung tính
(cách ngôn kịch tính, mệnh lệnh, in đậm cảm xúc, khẳng định vượt bằng chứng) **đã được sửa
trực tiếp** trong v1.1. Các mục dưới đây reviewer nêu nhưng cần nhóm quyết:

- **F1.** Bảng bộ phân loại học được (§5.10): hai cột "Lỗi tiêm"/"Lỗi thật" là đại lượng gì
  chính xác (hiệu số điểm phân loại? mức phát hiện?) — cần người chạy H37 ghi rõ định nghĩa
  cột vào caption. Con số solver 0,916 (GSM8K 7B, §5.10) cũng chưa dẫn từ bảng nào.
- **F2.** §5.1: bảng chênh $+0{,}112$ (toàn tập, pipeline−solver) và kiểm định $+5{,}6$
  (5 fold, PSVA−PS) là hai đại lượng khác nhau — v1.1 đã thêm một câu nối, nhóm xem đã đủ rõ chưa.
- **F3.** Trước khi nộp: xoá phần "Hình dự kiến" kèm phân công tên người và chú thích tác giả
  "quyết ở Bước 0" (nội dung quản lý nội bộ); giải quyết hết 5 marker \todoD/\todoTD.
  Đặc biệt: hai khẳng định phê phán dòng sửa chữa ở §2 chỉ được giữ nếu Đức xác nhận nguồn (=B1).
- **F4.** Reviewer đề xuất quy ước in đậm: chỉ đậm thuật ngữ định nghĩa lần đầu; nhấn mạnh dùng
  nghiêng, tối đa một lần mỗi đoạn; không đậm nguyên câu kết luận. v1.1 đã áp dụng phần lớn;
  ai viết thêm nội dung mới thì theo quy ước này.
