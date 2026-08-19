# Cấu trúc báo cáo

Tài liệu này xác định **nội dung** của báo cáo: luận điểm, khung lý thuyết, bố cục chương mục và
danh sách hình. Quy tắc trích dẫn số liệu nằm ở `HUONG_DAN_CONG_TAC.md`; trình tự thực hiện nằm ở
`QUY_TRINH_VIET_BAO_CAO.md`.

Dung lượng dự kiến: 20–28 trang kể cả phụ lục. Ngôn ngữ: tiếng Việt.

*Quy ước số: phần thân và bảng biểu dùng dấu phẩy thập phân theo chuẩn tiếng Việt (ví dụ 0,2720);
các công thức trong khối mã giữ nguyên ký hiệu gốc.*

---

## §0. Luận điểm chính

Ba khối công việc của nhóm được thực hiện độc lập với ba thiết kế khác nhau, và cùng dẫn đến một
kết luận:

> **Chênh lệch năng lực giữa hai model tạo ra cơ hội cải thiện; giao thức phối hợp quyết định
> cơ hội đó được khai thác hay bị phá huỷ.**

Luận điểm này chỉ đứng được sau **hai phép kiểm soát** mà phần lớn công trình trong lĩnh vực
không thực hiện:

**Kiểm soát 1 — cùng ngân sách token.** Pipeline nhiều vai tốn gấp ba lần solver đơn lẻ. Khi cố định
số lượt sinh và chỉ thay đổi cách tổng hợp, bỏ phiếu cơ học **thắng** aggregator LLM: trên MATH với
8 lượt sinh, `maj@8` đạt 0,60 (1.5B) và 0,73 (7B), trong khi `llm_agg@8` chỉ đạt 0,41 và 0,47.
Aggregator LLM phá vỡ đa số đúng **26 lần** và sửa được đa số sai **0 lần** (7B).

**Kiểm soát 2 — đúng mốc so sánh.** Kết quả +14,0 điểm của cấu hình bất đối xứng được đo so với
model **yếu**. So với model **mạnh chạy một mình** ở ngân sách token thấp hơn, cấu hình đó kém 10
điểm trên GSM8K và hoà trên MATH.

Sau hai kiểm soát này, phần giá trị còn lại rất nhỏ, và câu hỏi trở thành: **giá trị mất đi đâu?**

| Khi chênh lệch năng lực tăng | Kết quả | Nguồn |
|---|---|---|
| Giao thức **tuyển chọn** | Giá trị tăng: verifier lớn hơn cho **+14,0 điểm** so với model yếu, 5/5 fold, 43 sửa trên 1 phá | Khối nhóm |
| Giao thức **sửa chữa** | Giá trị giảm: `Δ_ceil = +0,0218 − 0,2392 × chênh lệch`, p = 1e-05, đổi dấu tại `g*` = **0,091** | Khối Nguyên (H97) |

Cùng một biến độc lập, hai dấu ngược nhau, khác biệt duy nhất nằm ở giao thức. Nguyên nhân được xác
định qua đẳng thức phân rã:

```
Δ_ceil = A − B + C        với  B = P(¬S ∧ I đúng ∧ V sai)
```

`B` là phần thiệt hại do giao thức gây ra. Giao thức tuyển chọn có `B` gần bằng 0; giao thức sửa chữa
luôn phải trả `B`. Nguồn gốc của `B` đã được đo và xác nhận qua tiền đăng ký trên hai miền: đó là
thiệt hại do model mạnh **tiếp xúc với nội dung sai** (trên MATH: −0,2720; độ chính xác giảm từ
46,4% xuống 19,2%). Con số "26 phá trên 0 sửa" ở Kiểm soát 1 chính là `B` quan sát trực tiếp.

Toàn bộ chương §5 là các mảnh chứng minh cho luận điểm trên.

---

## §1. Mở đầu (khoảng 2 trang)

**Vấn đề.** Việc bổ sung thêm một tác tử LLM vào hệ thống có mang lại giá trị hay không, và nếu có
thì giá trị đến từ đâu — từ việc thêm vai trò, hay từ yếu tố khác?

**Ba cách tiếp cận của nhóm**, đồng thời là bố cục của báo cáo:

1. **Theo vai trò** — vai nào trong pipeline `P→S→V→A` thực sự đóng góp giá trị (phân tích Shapley, Đức).
2. **Theo chi phí** — việc phối hợp có xứng đáng với chi phí tính toán không, và trong điều kiện nào
   (router, Tùng Dương).
3. **Theo luồng thông tin** — điều gì xảy ra khi một tác tử nhìn thấy sản phẩm của tác tử khác (Nguyên).

**Vấn đề về baseline.** Phần lớn công trình trong lĩnh vực đo cải thiện theo `V − S`, tức so với model
yếu. Nhưng lựa chọn thực tế của người triển khai là giữa việc chạy pipeline và việc gọi trực tiếp
model mạnh, tức đại lượng `V − I`. Khi đo theo `V − I`, dấu của hiệu ứng đảo ngược.

**Đóng góp của báo cáo:**

1. Khung phân rã giá trị `value = H(pool) × κ(z) − D(protocol)`, thống nhất được cả ba cách tiếp cận.
2. Bằng chứng cho thấy **bất đối xứng năng lực** là biến quyết định, không phải số lượng vai trò
   (nhất quán trên 5/5 fold).
3. Một **đẳng thức chính xác** tách phần cơ hội khỏi phần thiệt hại.
4. Bằng chứng có tiền đăng ký, tái lập trên hai miền: thiệt hại đến từ việc tiếp xúc với **nội dung sai**.
5. Giải thích được nghịch lý biểu kiến giữa hai nhóm kết quả.

---

## §2. Công trình liên quan (khoảng 2 trang)

Nguồn có sẵn: `../docs/RELATED_BASELINES.md` (102 dòng) và `../docs/RELATED_PIPELINE.md` (77 dòng).

- Số liệu công bố cho thấy debate kém hơn self-consistency ở 3 trên 4 ô so sánh, và giảm 16 điểm với
  Llama-3.1-8B trên GSM8K. Kết quả này trùng hướng với kết luận của nhóm nhưng đến từ nguồn độc lập.
- Định vị so với MAS_RPSV (bốn vai nối tiếp, cùng cỡ model, cùng benchmark) và SHARP (cùng sử dụng
  Shapley credit).
- **Phần còn thiếu:** nhóm phương pháp sinh rồi sửa (Self-Refine, Reflexion, CRITIC), và với mỗi
  công trình cần ghi rõ nó đo so với baseline nào. Đây là cơ sở trực tiếp cho luận điểm ở §1.

---

## §3. Khung lý thuyết (khoảng 2,5 trang)

### 3.1 Phân rã giá trị

```
value = H(pool) × κ(z) − D(protocol)
```

- `H` — **dư địa**: pool ứng viên có chứa lời giải mà model mạnh đơn lẻ không tạo ra được không?
- `κ` — **chất lượng bộ chọn**: một tín hiệu khả thi (không phải oracle) có lấy được lời giải đó không?
- `D` — **thiệt hại**: bản thân giao thức phá huỷ bao nhiêu?

### 3.2 Ba khối công việc tương ứng ba thành phần

| Khối | Đo thành phần | Công cụ |
|---|---|---|
| Phân tích Shapley theo vai (Đức) | `H` — đóng góp biên của từng vai | Giá trị Shapley trên `P`, `S`, `V`, `A` |
| Router hiệu quả (Tùng Dương) | `κ` — tín hiệu khả thi có rẻ không | Consensus router, so sánh độ chính xác với chi phí |
| Sửa chữa so với tuyển chọn (Nguyên) | `D` — mức thiệt hại do tiếp xúc | Phân rã `A`/`B`/`C`, phân tầng theo nội dung artifact |

Đây là điểm hợp nhất của báo cáo: ba khối không phải ba chủ đề rời, mà là ba thành phần của cùng
một biểu thức.

### 3.3 Đẳng thức phân rã

Với `S` là model yếu, `I` là model mạnh, `V` là kết quả khi `I` sửa artifact của `S`, và trần lý
tưởng `CEIL = S ∨ (¬S ∧ V)`:

```
Δ_ceil = acc(CEIL) − acc(I) = A − B + C

A = P(S đúng ∧ I sai)          cơ hội
B = P(¬S ∧ I đúng ∧ V sai)     giao thức sửa chữa làm hỏng bài mà I vốn giải đúng
C = P(¬S ∧ ¬I ∧ V đúng)        giao thức sửa chữa cứu được bài cả hai đều sai
```

Đây là **đẳng thức đại số**, không phải mô hình xấp xỉ: khớp tuyệt đối trên 4/4 cặp có lưu vết và
15/15 cặp trong thí nghiệm H97. `A` là tính chất của cặp model; `B` là tính chất của giao thức.
Đẳng thức này là công cụ giải nghịch lý ở §6.

### 3.4 Ba mệnh đề

- **M1** — Việc để model mạnh tiếp xúc với artifact làm mất giá trị. Phát biểu hoàn chỉnh ở §5.4.
- **M2** — Tín hiệu **độc lập** hiệu quả hơn tín hiệu **tương quan**, không phải tín hiệu mạnh hơn.
- **M3** — Cơ chế định tuyến tiết kiệm chi phí ở đúng nơi ít cần tiết kiệm nhất.

---

## §4. Thiết lập thí nghiệm (khoảng 2 trang)

Model sử dụng: Qwen2.5 (1.5B, 7B, 14B, 32B), Llama-3.1-8B, DeepSeek-Coder-6.7B.
Benchmark: GSM8K, MATH-500, MBPP (phần 11–510 và phần giữ lại 511–974), HumanEval.
Vai trò: `P` (planner), `S` (solver), `V` (verifier), `A` (aggregator).
Đại lượng đo: `Δ_ceil`, `Δ_honest`, `V_gain`, `A_gain`, chi phí trên mỗi câu hỏi.
Kiểm định: McNemar chính xác theo cặp, bootstrap theo chỉ số bài, thanh sai số qua 5 fold.

Hai chuẩn kiểm chứng của nhóm được trình bày ở §7.

---

## §5. Kết quả (khoảng 8 trang)

> **Khi viết phần này, dùng `MACH_DAN_DAT.md`.** Bố cục dưới đây chia theo thành phần khung
> (`H`, `κ`, `D`), tiện cho việc **tra cứu**. Nhưng phần thân báo cáo nên viết theo **mạch dẫn dắt**:
> mỗi thí nghiệm mở đầu bằng câu hỏi kế thừa từ thí nghiệm trước và kết thúc bằng câu hỏi để lại cho
> thí nghiệm sau. Hai tài liệu chứa **cùng một tập số liệu**, chỉ khác cách sắp xếp.

### 5.1 Dư địa: bất đối xứng năng lực, không phải số lượng vai (khối nhóm)

- Solver 1.5B kết hợp Verifier 7B: **+14,0 điểm** trên MATH, khoảng [+8,3; +20,0], nhất quán
  **5/5 fold**, sửa đúng 43 bài và làm hỏng 1 bài.
- Verifier **cùng cỡ**: chỉ +3,0 điểm, khoảng tin cậy chạm 0, tức chưa xác lập được hiệu ứng.
- Phần đóng góp riêng của việc verifier mạnh hơn (V7 trừ V15): **+11,0 điểm**, khoảng [+3,3; +16,7],
  nhất quán 5/5 fold.

Kết luận: giá trị nằm ở chênh lệch năng lực, không ở việc bổ sung thêm một vai trò.

### 5.2 Dư địa: cùng kết luận từ một thiết kế khác (khối Nguyên)

- 15 cặp có hướng, cùng 499 bài, một lần chạy. Hồi quy
  `A = β₀ + β₁ × chênh lệch + β₂ × khác họ model`.
- **β₁ = −0,1922** (p ≈ 0). **β₂ = +0,00446**, khoảng tin cậy 95% **[−0,0051; +0,0140]**.
- `R²` khi chỉ dùng biến chênh lệch: **0,824**.

Khoảng tin cậy của `β₂` nằm trọn dưới ngưỡng +0,02 đã khoá trong tiền đăng ký, nên đây là kết quả
null **có thông tin**, không phải trường hợp thiếu lực kiểm định.

Hai khối công việc, hai thiết kế độc lập, cùng một kết luận: biến quyết định là chênh lệch năng lực;
kiến trúc và họ model không phải biến quyết định.

### 5.3 Chất lượng bộ chọn: phối hợp có xứng đáng chi phí không (khối Tùng Dương)

| Chiến lược | GSM8K, độ chính xác | Chi phí | MATH, độ chính xác | Chi phí |
|---|---|---|---|---|
| Solver đơn lẻ | 0,6733 | 1 | 0,4133 | 1 |
| Pipeline đầy đủ | 0,7233 | 3 | 0,3733 | 3 |
| **Consensus Router** | **0,7200** | **2,32** | 0,4133 | 2,40 |

- Trên GSM8K: đạt gần bằng độ chính xác của pipeline đầy đủ với 77% chi phí.
- Trên MATH: router đạt đúng bằng solver đơn lẻ, tức không mang lại lợi ích.
- Cơ chế: khi solver và verifier bất đồng, aggregator sửa đúng được 45,4% trường hợp trên GSM8K
  nhưng chỉ 25,0% trên MATH.

Kết quả này xác nhận mệnh đề M3: định tuyến chỉ mang lại lợi ích ở nơi đã sẵn có đồng thuận, tức
nơi ít cần đến nó nhất.

### 5.4 Thiệt hại: hình phạt của việc tiếp xúc với nội dung sai (kết quả chính, có tiền đăng ký)

| | MBPP 11–510 | MBPP 511–974 | MATH-500 |
|---|---|---|---|
| Artifact **sai** | −0,1900 | −0,1927 | **−0,2720** (p ≈ 0) |
| Artifact **đúng** | +0,0636 | +0,0245 | **+0,0377** (p = 0,012) |

Trên MATH, độ chính xác của model mạnh giảm từ **46,4%** xuống **19,2%** ở tầng artifact sai. Tổng
hợp hai tầng theo trọng số cho `V − I` = **−0,1240**, khớp chính xác với giá trị đo trực tiếp.

Kết luận: `D` không phải hình phạt của việc **nhìn thấy**, mà là hình phạt của việc nhìn thấy
**nội dung sai**. Khi artifact đúng, model mạnh cải thiện — nhất quán trên cả ba phép đo, hai miền.

### 5.5 Quy luật `Δ_ceil` theo chênh lệch năng lực, và tính chuyển miền

Trên MBPP, 15 cặp, một lần chạy: `Δ_ceil = +0,0218 − 0,2392 × chênh lệch`; `R²` = 0,60;
p = **1e-05**; điểm đổi dấu `g*` = **0,0913**.

Cần lưu ý: **0 trên 15** cặp có `Δ_ceil` dương với ý nghĩa thống kê, trong khi **3 trên 15** cặp có
giá trị âm với ý nghĩa thống kê. Do đó chỉ phát biểu được theo **chiều phủ định**: khi chênh lệch
năng lực vượt 0,09 thì không nên áp dụng giao thức sửa chữa. Phân tích lực kiểm định cho thấy việc
xác lập vùng dương đòi hỏi lượng dữ liệu gấp khoảng 8 lần toàn bộ MBPP, tức không khả thi trên
benchmark này.

**Kiểm tra tính chuyển miền** (thí nghiệm H99b, tiền đăng ký #112, toàn bộ điều kiện hợp lệ đều đạt):
dùng đường hồi quy khớp trên MBPP để dự báo `Δ_ceil` trên MATH.

| Cặp | Chênh lệch | `Δ_ceil` đo được | Khoảng tin cậy 95% | MBPP dự báo | |
|---|---|---|---|---|---|
| 7B → 14B | 0,044 | −0,0140 | [−0,046; +0,018] | **+0,0108** | trong khoảng |
| 1.5B → 7B | 0,244 | **−0,1660** | [−0,208; −0,124] | −0,0361 | ngoài khoảng |
| 1.5B → 14B | 0,288 | −0,0680 | [−0,102; −0,034] | **−0,0471** | trong khoảng |

Hai trên ba dự báo nằm trong khoảng tin cậy, nên quy luật được xem là chuyển được sang miền toán.
Điều này cho thấy đây là quy luật về **giao thức**, không phải quy luật riêng của miền lập trình.

Hai lưu ý bắt buộc kèm theo kết quả này:

1. Các khoảng tin cậy rộng từ 0,064 đến 0,084, trong khi hiệu ứng có độ lớn từ 0,01 đến 0,17. Phép
   kiểm "dự báo nằm trong khoảng tin cậy" do đó có độ phân giải thấp. Kết quả nên được phát biểu là
   **không bác bỏ được quy luật**, không phải **đã xác nhận quy luật**.
2. Cặp 1.5B → 7B lệch một cách **hệ thống**: `B` = 0,208, gấp mười lần `A` = 0,020. Kết quả này tái
   lập một phép đo trước đó trên cùng cặp (−0,1380). Quy luật mô tả xu hướng chung và có ngoại lệ ở
   những trường hợp model yếu quá yếu so với độ khó của bài.

### 5.6 Giới hạn trên của cơ chế định tuyến theo mức tiếp xúc

Model mạnh đơn lẻ: 0,6980. Luôn cho xem artifact: 0,5740 (chênh −0,1240).
Cổng lý tưởng, tức chỉ cho xem khi artifact đúng: **0,7160 (chênh +0,0180)**.

Một bộ phân loại thực tế cần đạt độ chính xác khoảng **89%** mới hoà vốn. Do đó kết luận thực tiễn
không phải là "cần xây dựng cơ chế định tuyến tốt hơn", mà là **mặc định không nên cho model mạnh
xem artifact**.

### 5.7 Đa dạng ứng viên

Lấy ba mẫu từ cùng một model cho trung bình 1,91 trên 3 ứng viên phân biệt, và 36,2% số bài chỉ có
duy nhất một ứng viên. Với pool gồm các model khác nhau, con số tương ứng là 2,70 trên 3 và 6,5%.

Cần ghi là "khác model", không ghi là "khác họ model": đối chứng dùng các model khác nhau trong cùng
một họ chưa được thực hiện.

---

## §6. Tổng hợp: giải nghịch lý biểu kiến (khoảng 2 trang)

**Nghịch lý.** Mục §5.1 cho thấy chênh lệch năng lực lớn mang lại +14,0 điểm. Mục §5.5 cho thấy
chênh lệch năng lực lớn làm `Δ_ceil` âm.

**Cách giải.** Hai kết quả sử dụng hai giao thức khác nhau, và đẳng thức ở §3.3 tách được chúng:

- Verifier ở §5.1 là giao thức **tuyển chọn**: sửa đúng 43 bài, làm hỏng 1 bài, tức `B ≈ 0`.
- `V` ở §5.5 là giao thức **sửa chữa**: phải trả `B` theo cấu trúc, và `B` tăng theo chênh lệch năng lực.

Chênh lệch năng lực làm tăng **cả** `A` **lẫn** `B`. Kết quả cuối cùng phụ thuộc vào giao thức:

```
Tuyển chọn:  value ≈ A × κ − 0     → chênh lệch tăng thì giá trị tăng
Sửa chữa:    value ≈ A − B + C     → B tăng nhanh hơn nên giá trị giảm
```

Sáu mảnh bằng chứng độc lập cùng dẫn đến kết luận này:

1. **Đại số** — giao thức tuyển chọn có `B = 0` theo cấu trúc.
2. **Độ lớn** — trên MATH, `A` = 0,016 trong khi `B` = 0,176, tức gấp mười một lần.
3. **Xu hướng** — ngưỡng mà `V` phải vượt tăng theo chênh lệch nhanh gấp đôi khả năng bảo toàn thực
   tế của nó (hệ số góc 2,177 so với 1,101; p = 0,0066).
4. **Giới hạn trên** — cổng lý tưởng chỉ thu hồi được +0,018 trên nền thiệt hại −0,124.
5. **Bằng chứng ngoại vi** — số liệu công bố cho thấy debate kém hơn self-consistency ở 3 trên 4 ô,
   và giảm 16 điểm với model nhỏ.
6. **Tính chuyển miền** — quy luật khớp trên MBPP vẫn dự báo được trên MATH ở 2 trên 3 cặp, cho thấy
   cơ chế không riêng của miền lập trình (kèm lưu ý về lực kiểm định ở §5.5).

**Khuyến nghị thực tiễn**, nên đưa vào phần tóm tắt và phần kết luận:

> Dùng model nhỏ để giải và model lớn để soát; không cho model lớn xem bài làm của model nhỏ với
> mục đích sửa chữa. Chênh lệch năng lực là yếu tố tạo ra giá trị; giao thức tuyển chọn khai thác
> được giá trị đó, còn giao thức sửa chữa phá huỷ nó.

---

## §7. Phương pháp luận (khoảng 2 trang)

Nhóm sử dụng **hai chuẩn kiểm chứng bổ sung cho nhau**. Báo cáo cần trình bày cả hai.

| Chuẩn | Áp dụng cho | Cơ chế chống tự đánh lừa |
|---|---|---|
| Thanh sai số qua fold | Khối nhóm | 5 fold rời nhau; sàn nhiễu 2σ tương đương 5 điểm; hiệu ứng nhỏ hơn 5 điểm đo một lần không được tính là bằng chứng |
| Tiền đăng ký, điều kiện hợp lệ, niêm phong hash | Khối Nguyên | Bảng diễn giải commit trước khi chạy, có dòng bác bỏ giả thuyết; niêm phong hash artifact trước khi đọc số; trạng thái VOID thì không đọc số liệu |

Các số liệu về phương pháp nên nêu:

- Sàn nhiễu: cùng một cấu hình chạy trên 5 fold cho `V_gain` dao động từ +1,0 đến +8,0 điểm, dẫn
  đến ngưỡng tin cậy 5 điểm.
- **16 trên 31** lần chạy đã niêm phong có trạng thái VOID (tỷ lệ 52%). Đây là chỉ dấu cho thấy hệ
  thống điều kiện hợp lệ đang hoạt động đúng chức năng.
- Sổ theo dõi dự đoán trước, công khai: **21 đúng trên 43** lần.
- Tính tất định của greedy decoding: hai tài khoản khác nhau, hai ngày khác nhau, cùng cấu hình
  phần cứng cho kết quả giống nhau trên toàn bộ 499 bài. Hệ quả: chạy lại cùng một cấu hình không
  tạo ra bằng chứng độc lập.
- Điều kiện để so sánh chéo giữa các lần chạy: phải trùng cả cấu hình phần cứng và độ chính xác số,
  **và** trùng tập dữ liệu.

Nhận định chung từ cả hai chuẩn: phần lớn các "cải thiện" ghi nhận ban đầu không tồn tại sau kiểm
chứng. Đây là một kết quả, không phải một thất bại.

---

## §8. Hạn chế (khoảng 1 trang)

1. Hai khối công việc dùng hai chuẩn kiểm chứng khác nhau và chưa được kiểm chéo lẫn nhau.
2. Kết luận về tính chuyển miền của quy luật chênh lệch chỉ dựa trên 3 cặp, với khoảng tin cậy rộng,
   và có 1 trên 3 cặp lệch hệ thống.
3. Khối Nguyên chỉ dùng greedy decoding nên không có phương sai lấy mẫu; khối nhóm có thanh sai số
   qua fold.
4. Tập model bị giới hạn bởi dung lượng GPU tầng miễn phí: Llama-8B và Qwen-14B không lượng tử hoá
   được trên cấu hình 14,6 GB.
5. Vùng dương của quy luật chênh lệch chưa được xác lập và không thể xác lập trên MBPP do thiếu lực
   kiểm định.
6. Thành phần `κ` chưa được giải quyết: chưa tìm được tín hiệu khả thi nào trong khối Nguyên.
7. Đại lượng `Δ_honest` cho giao thức sinh độc lập trước chưa có kết luận sau năm lần chạy, do giới
   hạn bộ nhớ GPU.

---

## §9. Kết luận (khoảng 0,5 trang)

---

## Phụ lục

- **A.** Trích các bản tiền đăng ký
- **B.** Bảng niêm phong hash
- **C.** Danh sách 16 lần chạy VOID và lý do
- **D.** Sổ theo dõi dự đoán trước (21/43)
- **E.** 37 quy tắc quy trình
- **F.** Bảng kết quả đầy đủ của khối nhóm
- **G.** Phân tích Shapley theo vai (29 tài liệu)

---

## Danh sách hình

| Hình | Nội dung | Nguồn dữ liệu | Người thực hiện |
|---|---|---|---|
| 1 | Sơ đồ khung `H × κ − D`, kèm ánh xạ ba khối công việc | Vẽ mới | Nguyên |
| 2 | Nghịch lý: chênh lệch tăng thì verifier thắng còn sửa chữa thua (hai đường ngược chiều) | `../docs/RESULTS.md`, `../results_H97/` | Nguyên |
| 3 | `Δ_ceil` theo chênh lệch, 15 điểm kèm đường hồi quy và `g*` | `../results_H97/` | Tùng Dương |
| 4 | Phân tầng mức tiếp xúc, bảng 2×2 | `../results_H94d/` | Tùng Dương |
| 5 | Độ chính xác so với chi phí, có điểm router | `EFFICIENCY.md` (nhánh `nguoi3-router`) | Tùng Dương |
| 6 | Bất đối xứng năng lực: verifier cùng cỡ so với lớn hơn, có thanh sai số | `../docs/RESULTS.md` §1a | Đức |
| 7 | Giới hạn trên của định tuyến: độ chính xác bộ phân loại so với lợi ích ròng | `../results_H94d/` | Tùng Dương |

Hình 2 là hình quan trọng nhất vì nó thể hiện trực tiếp luận điểm chính. Nếu thời gian hạn chế, ưu
tiên Hình 2, 4 và 6.
