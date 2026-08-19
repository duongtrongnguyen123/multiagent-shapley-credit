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
      ↓ có, +5,6đ — nhưng phần lớn cải thiện biến mất dưới sàn nhiễu
[2] Vai nào thực sự đóng góp?
      ↓ verifier; và hiệu ứng phụ thuộc CỠ verifier, không phụ thuộc việc có thêm vai
[3] Phối hợp có xứng chi phí không?
      ↓ có trên GSM8K, không trên MATH — vì sao khác nhau?
[4] Đang so với baseline nào?
      ↓ đổi mốc từ model yếu sang model mạnh → DẤU ĐẢO NGƯỢC
[5] Giá trị mất đi ở đâu?
      ↓ đẳng thức Δ_ceil = A − B + C tách được ba nguồn
[6] Số hạng A do đâu quyết định?      → chênh lệch năng lực, không phải họ model
[7] Số hạng B do đâu mà có?           → tiếp xúc với nội dung SAI
[8] Quy luật có tổng quát không?      → chuyển được sang miền toán
[9] Có chặn được B không?             → trần chỉ +0,018
      ↓
[10] Nghịch lý giữa [2] và [8] được giải bằng [5]
```

---

## [1] Điểm xuất phát: pipeline đa tác tử có giúp không?

**Câu hỏi.** Ghép nhiều vai LLM (planner, solver, verifier, aggregator) có tốt hơn một model đơn lẻ không?

**Kết quả.** Có: pipeline đầy đủ so với solver đơn lẻ đạt **+5,6 điểm** trên GSM8K, nhất quán 5/5 fold.

**Nhưng một phép đo khác làm thay đổi cách đọc toàn bộ.** Chạy cùng một cấu hình trên 5 fold rời
nhau cho `V_gain` dao động từ **+1,0 đến +8,0 điểm**. Sàn nhiễu 2σ tương đương **5 điểm**. Hệ quả:
mọi hiệu ứng nhỏ hơn 5 điểm, đo một lần, không được tính là bằng chứng. Nhiều kết luận trước đó bị
hạ cấp, trong đó có `A_gain` = +1,2 điểm với khoảng tin cậy chứa số 0.

**Câu hỏi để lại:** trong bốn vai, vai nào thực sự đóng góp?

---

## [2] Phân rã theo vai: hoá ra biến quyết định không phải vai

**Câu hỏi.** Dùng giá trị Shapley để tính đóng góp biên của từng vai.

**Kết quả bất ngờ.** Điều quyết định không phải *có thêm vai hay không*, mà là *vai đó mạnh đến đâu*:

| Cấu hình | Hiệu ứng trên MATH | Nhất quán |
|---|---|---|
| Solver 1.5B + Verifier **7B** | **+14,0 điểm**, khoảng [+8,3; +20,0] | 5/5 fold |
| Solver 1.5B + Verifier **1.5B** (cùng cỡ) | +3,0 điểm, khoảng **chạm 0** | không xác lập |
| Riêng phần do verifier mạnh hơn | **+11,0 điểm**, khoảng [+3,3; +16,7] | 5/5 fold |

Verifier 7B sửa đúng **43 bài** và làm hỏng **1 bài** trên 300 bài.

**Đây là lần đầu khái niệm bất đối xứng năng lực xuất hiện trong dự án**, và nó đến từ phía phân
tích vai, hoàn toàn độc lập với nhánh nghiên cứu sau này.

**Câu hỏi để lại:** nếu phối hợp có giá trị, giá trị đó có bù được chi phí tính toán không?

---

## [3] Chi phí: phối hợp chỉ trả tiền ở nơi ít cần nó nhất

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

## [4] Bước ngoặt: đang so với baseline nào?

**Quan sát.** Toàn bộ các phép đo ở [1]–[3] đều so với **model yếu** hoặc với solver đơn lẻ. Nhưng
nếu pipeline đã chứa một model mạnh, thì lựa chọn thực tế của người triển khai là: chạy pipeline,
hay **gọi thẳng model mạnh**?

**Đại lượng đúng là `V − I`, không phải `V − S`.**

**Kết quả.** Khi đổi mốc so sánh, **dấu của hiệu ứng đảo ngược**. Một giao thức "cải thiện" so với
model yếu lại **kém hơn** việc gọi trực tiếp model mạnh.

Đây là phát hiện phương pháp trung tâm của báo cáo, và là lý do tồn tại của toàn bộ nhánh nghiên
cứu tiếp theo.

**Câu hỏi để lại:** giá trị bị mất đi ở đâu?

---

## [5] Công cụ: đẳng thức phân rã

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

## [6] Số hạng A: một tương quan giả bị phát hiện

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

## [7] Số hạng B: thiệt hại đến từ nội dung sai, không từ việc nhìn thấy

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

## [8] Quy luật và tính chuyển miền

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

## [9] Có chặn được B không: giới hạn trên của cơ chế định tuyến

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

## [10] Khép mạch: nghịch lý giữa [2] và [8]

**Nghịch lý.** [2] nói chênh lệch năng lực lớn mang lại +14,0 điểm. [8] nói chênh lệch năng lực lớn
làm `Δ_ceil` âm. Cùng một biến, hai dấu ngược nhau.

**Cách giải, dùng công cụ ở [5].** Hai kết quả dùng hai giao thức khác nhau:

- Verifier ở [2] là giao thức **tuyển chọn**: 43 sửa đúng, 1 làm hỏng ⇒ `B ≈ 0`.
- `V` ở [8] là giao thức **sửa chữa**: phải trả `B` theo cấu trúc, và `B` tăng theo chênh lệch.

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
