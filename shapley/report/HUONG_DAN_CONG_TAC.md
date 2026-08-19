# Hướng dẫn cộng tác — Quy tắc trích dẫn số liệu

Ba tài liệu, ba chức năng: `BAO_CAO_CAU_TRUC.md` xác định **viết nội dung gì**; tài liệu này xác định
**được phép trích dẫn số liệu nào**; `QUY_TRINH_VIET_BAO_CAO.md` xác định **trình tự thực hiện**.
Điểm khởi đầu: mục §0 của `BAO_CAO_CAU_TRUC.md`.

Cần đọc hết mục 1 và mục 2 của tài liệu này trước khi viết bất kỳ con số nào.

---

## 1. Ba mức độ tin cậy

Mỗi số liệu trong dự án thuộc **đúng một** mức. Mức độ quyết định cách phát biểu số liệu đó.

| Mức | Định nghĩa | Vị trí trong báo cáo | Cách diễn đạt |
|---|---|---|---|
| **A — Đã xác nhận** | Có tiền đăng ký, bảng diễn giải được khoá **trước** khi chạy, và **toàn bộ điều kiện hợp lệ đều đạt** | Phần thân báo cáo | *"Kết quả đo được là X"* |
| **B — Thăm dò** | Phân tích hậu nghiệm, hoặc không có tiền đăng ký | Phần thân, có ghi chú rõ; hoặc phụ lục | *"Quan sát mô tả, chưa được xác nhận"* |
| **C — VOID** | Có ít nhất một điều kiện hợp lệ không đạt | Chỉ liệt kê ở Phụ lục C | Không trích dẫn giá trị số |

### Lý do áp dụng quy tắc này

Trong quá trình thực hiện, dự án đã từng đọc số liệu từ những lần chạy VOID (các vòng #114, #121,
#123), một lần trong số đó tạo ra kết quả tái lập không có thật. Sai sót được phát hiện ở vòng kiểm
định #125. Toàn bộ quy tắc phân mức hiện tại hình thành từ sự cố đó.

Khi gặp một số liệu chưa rõ thuộc mức nào, cần xác định mức trước khi đưa vào báo cáo.

### Một trường hợp ngoại lệ cần lưu ý

Hai lần chạy **H88e** và **H92b** có tệp `res_*.json` ghi trạng thái `VOID: ["n>=480"]` nhưng
**vẫn hợp lệ**. Nguyên nhân: phần giữ lại của MBPP (`task_id` từ 511 đến 974) chỉ có 464 bài, nên
điều kiện `n ≥ 480` không thể đạt được về mặt vật lý. Bản tiền đăng ký đã được sửa thành `n ≥ 460`
cho phần dữ liệu này, và bản sửa được commit **trước khi đọc số liệu** (xem mục `#97-d` và `#102-b`;
có thể kiểm chứng bằng `git log`). Mã kernel vẫn giữ ngưỡng `n ≥ 480` nên trường `VOID` trong tệp
kết quả không còn phản ánh đúng trạng thái.

Kết luận: cả hai lần chạy thuộc **mức A**. Không loại bỏ chúng chỉ vì tệp kết quả ghi VOID; cần đối
chiếu với bản tiền đăng ký tương ứng.

---

## 2. Bảng số liệu đã chốt

Toàn bộ số liệu dưới đây thuộc **mức A**, trừ khi có ghi chú khác. Cần sao chép chính xác, không
làm tròn lại.

### 2.1 Thiệt hại do mức tiếp xúc với artifact

| | MBPP 11–510 | MBPP 511–974 | MATH-500 |
|---|---|---|---|
| Artifact **sai** | −0,1900 | −0,1927 | **−0,2720** (p ≈ 0) |
| Artifact **đúng** | +0,0636 | +0,0245 | **+0,0377** (p = 0,012) |

Trên MATH: `n` = 500, gồm 239 bài có artifact đúng và 261 bài có artifact sai. Ở tầng artifact sai,
độ chính xác của model mạnh giảm từ **46,4%** xuống **19,2%**. Tổng hợp hai tầng theo trọng số cho
`V − I` = **−0,1240**, khớp chính xác với giá trị đo trực tiếp.

Nguồn: `../results_H94d/res_H94d.json`, khoá `strat`. Cột MBPP: `../results_H92`, `../results_H92b`.

### 2.2 Dư địa theo chênh lệch năng lực

Hồi quy `A = β₀ + β₁ × (chênh lệch năng lực) + β₂ × (khác họ model)` trên 15 cặp, cùng 499 bài:

- **β₁ = −0,1922** (sai số chuẩn 0,0260; p ≈ 0)
- **β₂ = +0,00446** (sai số chuẩn 0,0044; p = 0,33), khoảng tin cậy 95%: **[−0,0051; +0,0140]**
- `R²` khi chỉ dùng biến chênh lệch năng lực: **0,8237**; thêm biến họ model: 0,8377

Khoảng tin cậy của `β₂` nằm trọn dưới ngưỡng +0,02 đã được khoá trong tiền đăng ký. Đây là kết quả
**null có thông tin**, không phải trường hợp thiếu lực kiểm định.

Nguồn: `../results_H96/res_H96.json`, khoá `ols` và `pairs`.

### 2.3 Quy luật `Δ_ceil` theo chênh lệch năng lực

`Δ_ceil = +0,0218 − 0,2392 × (chênh lệch năng lực)`; `R²` = **0,5998**; p(δ₁) = **1e-05**;
điểm đổi dấu `g*` = **0,0913**.

- **0 trên 15** cặp có `Δ_ceil` dương với ý nghĩa thống kê
- **3 trên 15** cặp có `Δ_ceil` âm với ý nghĩa thống kê
- Do đó **chỉ phát biểu theo chiều phủ định**: khi chênh lệch năng lực vượt 0,09 thì không nên áp
  dụng giao thức sửa chữa

Nguồn: `../results_H97/res_H97.json`, khoá `ols_ceil` và `pairs`.

**Quy luật này chuyển được sang miền toán** (thí nghiệm H99b, tiền đăng ký #112, toàn bộ điều kiện
hợp lệ đều đạt, 3 trên 3 cặp): **2 trên 3** giá trị dự báo nằm trong khoảng tin cậy 95%.

| Cặp | Chênh lệch | `Δ_ceil` đo được | Khoảng tin cậy 95% | Giá trị MBPP dự báo |
|---|---|---|---|---|
| 7B → 14B | 0,044 | −0,0140 | [−0,046; +0,018] | **+0,0108** (trong khoảng) |
| 1.5B → 7B | 0,244 | **−0,1660** | [−0,208; −0,124] | −0,0361 (ngoài khoảng) |
| 1.5B → 14B | 0,288 | −0,0680 | [−0,102; −0,034] | **−0,0471** (trong khoảng) |

Cần phát biểu là **"không bác bỏ được quy luật"**, không phát biểu là **"đã xác nhận quy luật"**:
các khoảng tin cậy rộng từ 0,064 đến 0,084 nên phép kiểm này có độ phân giải thấp.

Nguồn: `../results_H99b/res_H99b.json`, khoá `pairs`.

### 2.4 Đẳng thức phân rã

`Δ_ceil = A − B + C`. Đẳng thức khớp tuyệt đối trên **4 trên 4** cặp có lưu vết trung gian và
**15 trên 15** cặp trong thí nghiệm H97.

### 2.5 Giới hạn trên của cơ chế định tuyến (mức B — suy ra từ dữ liệu mức A)

Model mạnh đơn lẻ: 0,6980. Luôn cho xem artifact: 0,5740 (chênh −0,1240).
**Cổng lý tưởng: 0,7160 (chênh +0,0180).**

Một bộ phân loại thực tế cần đạt độ chính xác khoảng **89%** mới hoà vốn: ở mức 0,90 chênh lệch là
+0,0020; ở mức 0,85 chênh lệch là −0,0060.

### 2.6 Đa dạng ứng viên

Lấy ba mẫu từ cùng một model cho trung bình **1,91 trên 3** ứng viên phân biệt, và **36,2%** số bài
chỉ có duy nhất một ứng viên. Dùng pool gồm các model khác nhau cho **2,70 trên 3** ứng viên phân
biệt và **6,5%** số bài có một ứng viên.

Cần ghi là **"khác model"**, không ghi là "khác họ model": đối chứng dùng các model khác nhau trong
cùng một họ chưa được thực hiện.

### 2.7 Tín hiệu kiểm: đúng đắn so với học được

**Tín hiệu đúng đắn (chạy test), HumanEval, cùng 4 lượt sinh:**

| Ô | greedy | **exec3** | llm3 | exec3 − llm3 | `exec3` phá | `llm3` phá |
|---|---|---|---|---|---|---|
| HE 1.5B (Kaggle) | 0,5375 | **0,6000** | 0,4812 | +0,119 (5/5) | **0,0** | 2,8 |
| HE 1.5B (5090) | 0,5625 | **0,6438** | 0,4375 | +0,206 (5/5) | **0,0** | 4,6 |
| HE 7B (5090) | 0,8000 | **0,8812** | 0,7812 | +0,100 (4/5) | **0,0** | 2,6 |
| HE 7B (Kaggle) | 0,7938 | **0,9000** | 0,7438 | +0,156 (5/5) | **0,0** | 3,2 |

`exec3` đạt **đúng bằng `oracle@4`**; phá 0 bài trong **20 trên 20 fold**.
⚠️ Mốc trung thực là `greedy` chứ không phải `maj@4` (bỏ phiếu **có hại** trên code: −0,113 và
−0,131). Theo mốc đúng: `exec3 − greedy` = **+0,063 đến +0,106**.

**Tín hiệu học được (bộ phân loại huấn luyện trên lỗi tiêm):**
lỗi tiêm (đổi một chữ số) khả năng phân biệt **+0,032**; lỗi thật +0,219 (AUC 0,563); và cả hai
**không chuyển thành độ chính xác** (bỏ phiếu có trọng số ≈ bỏ phiếu thường).

*Nguồn: `../docs/RESULTS.md` §8.1 và §8.2; `../results_injected_classifier/summary.json`;
`../docs/IDEAS.md` vòng #72.*

### 2.8 Mẫu số: 57% số câu bất động

| Số mẫu đúng trên 5 | n | Solver | vote5 | Δ |
|---|---|---|---|---|
| 0/5 | 48 (32%) | 0,000 | 0,000 | 0,000 |
| 1/5 | 20 | 0,000 | 0,000 | 0,000 |
| 2/5 | 15 | 0,333 | 0,600 | +0,267 |
| 3/5 | 12 | 0,583 | 1,000 | +0,417 |
| 4/5 | 18 | 0,722 | 1,000 | +0,278 |
| 5/5 | 37 (25%) | 1,000 | 1,000 | 0,000 |

Tầng 2–4/5 (30% số câu): **+31,1 điểm**. Toàn bộ 150 câu: **+9,3 điểm**. Pha loãng **3,3 lần**.
*Nguồn: `../docs/DIFFICULTY_STRATA.md`.*

### 2.9 Số liệu về phương pháp

- **31** lần chạy đã niêm phong bằng hash, trong đó **16 lần VOID** (tỷ lệ **52%**)
- Sổ theo dõi dự đoán trước: **21 đúng trên 43** lần
- Tính tất định của greedy decoding: hai tài khoản khác nhau, hai ngày khác nhau, cùng cấu hình
  phần cứng cho kết quả **giống nhau trên toàn bộ 499 bài**

---

## 3. Các phát biểu cần tránh

| Không viết | Viết thay bằng |
|---|---|
| "Khác họ model cho dư địa lớn hơn" | "Chênh lệch năng lực nhỏ cho dư địa lớn hơn". Nhãn "khác họ" đã bị rút ở vòng #182 |
| "Chênh lệch nhỏ thì giao thức sửa chữa thắng" | "Khi chênh lệch vượt 0,09 thì không nên sửa chữa". Chiều khẳng định chưa được xác lập |
| "Đã xác nhận quy luật chuyển được sang toán" | "Không bác bỏ được quy luật trên miền toán". Khoảng tin cậy rộng |
| "Cơ chế định tuyến là lời giải" | "Giới hạn trên của định tuyến chỉ là +0,018; mặc định nên không cho xem artifact" |
| "Kết quả được tái lập bằng cách chạy lại" | Greedy decoding có tính tất định, nên chạy lại cùng cấu hình không tạo bằng chứng độc lập |
| Bất kỳ số liệu nào từ H98, H99, H95b, H94c, H91b/c/d, H88, H88b, H89b/d/e/f/h | Các lần chạy VOID; chỉ được nhắc tên ở Phụ lục C |
| "Pool khác họ model" ở mục đa dạng ứng viên | "Pool khác model" |

---

## 4. Phân công

| Phần | Người thực hiện | Ghi chú |
|---|---|---|
| §2 Công trình liên quan | Đức | Phần lớn đã có sẵn: `../docs/RELATED_BASELINES.md` (102 dòng, số liệu công bố về debate và self-consistency trên GSM8K và MATH) và `../docs/RELATED_PIPELINE.md` (77 dòng, định vị so với MAS_RPSV và SHARP). Phần còn thiếu: nhóm phương pháp sinh rồi sửa (Self-Refine, Reflexion, CRITIC), và với mỗi công trình cần ghi rõ nó đo so với baseline nào. Đây là cơ sở cho luận điểm ở §1 |
| §4 Thiết lập thí nghiệm | Tùng Dương | Nội dung mang tính mô tả: model, benchmark, đại lượng đo, kiểm định. Nguồn có sẵn trong `../pipeline/` |
| Hình 3, Hình 4 | Tùng Dương | Dữ liệu có sẵn trong `../results_H97/` và `../results_H94d/` |
| §1, §3, §5, §6 | Nguyên | Cần nắm lịch sử từng kết quả và lý do đặt từng nhãn |
| §7 Phương pháp luận, §8 Hạn chế | Nguyên | Cần nắm bối cảnh hình thành từng quy tắc |
| Phụ lục A–G | Trích từ `../docs/` | Chủ yếu là sao chép |

---

## 5. Kết quả của các thành viên khác

Dự án gồm **hai khối công việc** trên các nhánh khác nhau, sử dụng **hai chuẩn kiểm chứng khác nhau**:

| Khối | Nhánh | Nội dung | Chuẩn kiểm chứng |
|---|---|---|---|
| Credit assignment, Shapley, sửa chữa so với tuyển chọn (Nguyên) | `nguyen` | Các vòng #97–#203 | Tiền đăng ký, điều kiện hợp lệ, niêm phong hash, trạng thái VOID |
| Phân tích vai trò, debate, credit-RL, router (Đức, Tùng Dương) | `duc`, `nguoi3-router`, `main` | Khoảng 30 tài liệu kết quả | Thanh sai số qua 5 fold, sàn nhiễu 5 điểm |

Đây là hai chuẩn **bổ sung cho nhau**, không phải một chuẩn tốt hơn chuẩn kia. Quy trình tiền đăng ký
chỉ hình thành từ vòng #97 trên nhánh `nguyen`; phần lớn công việc của khối còn lại được thực hiện
song song hoặc trước thời điểm đó.

**Yêu cầu đối với báo cáo:** không đặt kết quả của hai khối vào cùng một mức tin cậy nếu chưa kiểm
tra lại. Có ba phương án, cần chọn một và nêu rõ trong báo cáo:

1. Ghi rõ hai chuẩn khác nhau và xếp kết quả khối còn lại vào mức B.
2. Kiểm tra lại hậu kỳ: xây dựng điều kiện hợp lệ tương đương rồi báo cáo kết quả nào đạt.
3. Tách thành hai phần riêng, mỗi phần nêu chuẩn kiểm chứng của mình.

Phương án 1 được khuyến nghị: chi phí thấp, trung thực, và không đòi hỏi chạy lại thí nghiệm.

### Hai kết quả nên đưa vào phần thân báo cáo

- **`EFFICIENCY.md`** (Tùng Dương, 210 dòng, tác giả duy nhất; hiện chỉ có trên nhánh
  `nguoi3-router`): Consensus Router đạt độ chính xác 0,7200 với chi phí 2,32 lần, so với pipeline
  đầy đủ đạt 0,7233 với chi phí 3 lần — tức gần bằng độ chính xác với 77% chi phí. Trên MATH, router
  đạt 0,4133, đúng bằng solver đơn lẻ, tức không mang lại lợi ích. Phân tích cơ chế cho thấy khi
  solver và verifier bất đồng, aggregator sửa đúng được 45,4% trường hợp trên GSM8K nhưng chỉ 25,0%
  trên MATH. Đây là bằng chứng độc lập cho mệnh đề M3, nên đưa vào §5.3.

- **`../docs/RELATED_BASELINES.md`** (Đức): tổng hợp số liệu công bố cho thấy debate kém hơn
  self-consistency ở 3 trên 4 ô so sánh, và giảm 16 điểm với Llama-3.1-8B trên GSM8K. Kết quả này
  trùng hướng với kết luận của dự án về ưu thế của giao thức tuyển chọn, nhưng đến từ nguồn hoàn toàn
  độc lập. Phù hợp cho §2 và §6.

---

## 6. Vị trí các nguồn

```
shapley/
├─ report/                        Hướng dẫn viết báo cáo (thư mục này)
│  ├─ README.md                   Điểm vào
│  ├─ BAO_CAO_CAU_TRUC.md         Viết nội dung gì
│  ├─ HUONG_DAN_CONG_TAC.md       Được trích số liệu nào (tài liệu này)
│  ├─ QUY_TRINH_VIET_BAO_CAO.md   Trình tự thực hiện
│  └─ BAO_CAO.md                  Bản thảo (chưa có; Bước 1 tạo)
├─ docs/                          Tài liệu kết quả (39 tệp)
│  ├─ INDEX.md                    Mục lục của docs/
│  ├─ TONG_HOP.md                 Khung lý thuyết. Nên đọc trước tiên
│  ├─ RESULTS.md                  Bảng kết quả khối nhóm, có thanh sai số 5 fold
│  ├─ PREREGISTRATION.md          Toàn bộ bảng diễn giải đã khoá
│  ├─ IDEAS.md                    Nhật ký nghiên cứu, 203 vòng
│  ├─ QUY_TRINH_VONG_LAP.md       37 quy tắc quy trình
│  ├─ RESULT_SEALS.md             Niêm phong hash
│  └─ (29 tệp kết quả của Đức: CREDIT_RL, ORPO, SOLVEJUDGE, RELATED_*, ...)
├─ results_*/                     Dữ liệu thô (không nằm trong git)
└─ pipeline/ deploy/ analysis/    Mã nguồn
```

Ba vòng nên đọc trước trong `../docs/IDEAS.md`: **#197** (thiệt hại do tiếp xúc với nội dung sai),
**#185** (quy luật theo chênh lệch năng lực), **#182** (rút nhãn "khác họ model"). Ba vòng này là
cơ sở của §5.

---

## 7. Nguyên tắc chung

1. Mỗi số liệu phải truy được về tệp nguồn cụ thể: `results_X/res_X.json` và tên khoá.
2. Không làm tròn lại số liệu. Nếu nguồn ghi −0,2720 thì bảng biểu giữ nguyên bốn chữ số.
3. Giữ nguyên các phát biểu tự giới hạn. Ví dụ, việc báo cáo giới hạn trên của chính đề xuất của
   nhóm chỉ là +0,018 là một điểm mạnh về phương pháp, không nên lược bỏ.
4. Kết quả âm và các lần chạy VOID là nội dung khoa học. Tỷ lệ VOID 52% cho thấy hệ thống điều kiện
   hợp lệ đang hoạt động đúng chức năng, nên trình bày ở §7 với đầy đủ ngữ cảnh.
5. Khi chưa xác định được một số liệu thuộc mức tin cậy nào, cần làm rõ trước khi đưa vào báo cáo.
