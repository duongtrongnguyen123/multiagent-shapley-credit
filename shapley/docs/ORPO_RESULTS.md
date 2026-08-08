# ORPO cho Aggregator — kết quả cuối, sau khi sửa lỗi train/eval mismatch

Giai đoạn 2 vòng ORPO. Tiêu chí khoá trước trong `ORPO_AGGREGATOR.md`.

Adapter LoRA (r=16) train trên **428 cặp preference từ MATH train**, prompt có **2 ứng viên**.
Eval 5 fold × 30 trên MATH-500 test (in-domain) và GSM8K test (cross-task).

> **Đính chính:** vòng eval đầu tiên đưa cho adapter **3 ứng viên** trong khi nó train trên 2 —
> train/eval mismatch. Tài liệu này thay thế toàn bộ số của vòng đó. Nhánh `agg3_orpo_ood` giữ
> lại đúng cấu hình sai làm đối chứng, và kết quả của nó **bác bỏ** giả thuyết ban đầu của tôi
> về nguyên nhân (xem mục 3).

## Kết quả

### MATH — in-domain (adapter train trên MATH)

| nhánh | acc | Δ vs base | fold |
|---|---|---|---|
| S (Solver một mình) | .4133 | −0.033 | 3/5 |
| **agg2_base** | **.4467** | — | — |
| **agg2_orpo** (khớp train) | **.4667** | **+0.020** | 3/5 |
| **agg2_orpo + fallback** | **.4800** | **+0.033** | 3/5 |
| vote2 | .4133 | −0.033 | 3/5 |
| *agg3_orpo_ood* (cấu hình sai) | *.4933* | *+0.047* | *4/5* |
| *vote3* | *.4733* | *+0.027* | *3/5* |
| *oracle (K=2)* | *.553* | | |

### GSM8K — cross-task (adapter chưa từng thấy GSM8K)

| nhánh | acc | Δ vs base | fold |
|---|---|---|---|
| S | .6533 | −0.047 | 4/5 |
| **agg2_base** | **.7000** | — | — |
| **agg2_orpo** | **.6733** | **−0.027** | 3/5 |
| agg2_orpo + fallback | .6733 | −0.027 | 3/5 |
| vote2 | .6533 | −0.047 | 4/5 |
| *agg3_orpo_ood* | *.7267* | *+0.027* | *3/5* |
| *oracle (K=2)* | *.753* | | |

## 1. Đọc theo tiêu chí đã khoá

**MATH: rơi hàng 2** — `agg2_orpo_fb` = .4800 vượt `agg2_base` (.4467) và vượt `vote2` (.4133),
nhưng **không đạt** mốc `vote5` = .507. Chỉ 3/5 fold, hiệu ứng +3.3 điểm **dưới sàn nhiễu**.

**GSM8K: rơi hàng 4** — `agg2_orpo` = .6733 **thấp hơn** base .7000. Adapter **làm hại** khi
chuyển sang task khác.

Phát biểu trung thực: **ORPO cải thiện nhẹ in-domain nhưng dưới ngưỡng đo được, và làm hại khi
đổi task.**

## 2. Chỉ số khoá trước: `copies_last`

| | base | ORPO |
|---|---|---|
| **MATH** | .560 | **.540** ↓ nhẹ |
| **GSM8K** | .713 | **.813** ↑ **ngược hướng** |

Trên GSM8K, adapter **tăng** recency bias — chép ứng viên cuối nhiều hơn base. Đây là bằng chứng
độc lập cho việc nó không chuyển được: nó không chỉ mất tác dụng mà còn khuếch đại đúng lỗi
đáng lẽ phải sửa.

## 3. Giả thuyết mismatch của tôi BỊ BÁC

Ở vòng trước tôi viết rằng `novel` = .307 (đáp án ngoài đầu vào) là do train/eval mismatch —
adapter rơi ngoài phân bố nên thoái hoá về "tự giải lại". Nhánh đối chứng bác bỏ điều đó:

| | `agg2_orpo` (khớp train) | `agg3_orpo_ood` (mismatch) |
|---|---|---|
| **MATH** `novel` | **.327** | .307 |
| **GSM8K** `novel` | **.087** | .033 |

**Cấu hình khớp train cho `novel` CAO HƠN, không thấp hơn.** Mismatch không phải nguyên nhân.

⇒ Diễn giải gốc **đúng**: adapter thật sự học **tự giải lại** thay vì **chọn**. Nhiệm vụ là chọn
giữa các ứng viên, nhưng cách dễ nhất để giảm loss là bỏ qua ứng viên và giải lại. Cùng loại
thất bại với H23 (học im lặng vì im lặng miễn phí) — lối tắt mà hàm mục tiêu cho phép.

Đáng chú ý hơn: `agg3_orpo_ood` **tốt hơn** `agg2_orpo` ở **cả hai** task (.4933 vs .4667;
.7267 vs .6733). Adapter chạy tốt hơn ở cấu hình nó **chưa từng** train. Điều này chỉ hợp lý nếu
thứ nó học được là **có hại**, và cấu hình lạ làm nó bớt áp dụng cái đã học.

## 4. Vì sao — trần vốn đã hẹp

Oracle với K=2 chỉ **.553** (MATH) và **.753** (GSM8K), so với K=3 là .620/.807. Ít ứng viên thì
ít cơ hội có cái đúng để chọn.

Kết hợp với `DIFFICULTY_STRATA.md`: với K=2, tỉ lệ câu "cả hai đều sai" hoặc "cả hai đều đúng"
còn cao hơn K=5, nên phần câu mà việc chọn có ý nghĩa còn nhỏ hơn nữa. **Giảm K để vừa bộ nhớ
đã thu hẹp chính bài toán cần giải.**

## 5. Kết luận

1. **ORPO không đạt mốc.** In-domain +3.3 điểm (dưới sàn nhiễu, 3/5 fold), cross-task **−2.7
   điểm**.
2. **Không chuyển sang task khác** — và còn khuếch đại recency bias (`copies_last` .713 → .813).
3. **Cơ chế không phải cái ta muốn dạy** — xác nhận bằng đối chứng, không phải suy đoán.
4. **Bỏ phiếu vẫn thắng**: `vote5` = .507 > mọi nhánh ORPO. Không cần train, không cần dữ liệu.

## 6. Giới hạn

- 428 cặp là ít, đã ghi rủi ro trước khi train. Nhưng thất bại **không phải** "không học được"
  — loss giảm .452 → .287, eval_loss .310 → .265, và hành vi đổi rõ rệt.
- n=150 mỗi task, sàn nhiễu ~5 điểm. Mọi Δ đều nhỏ hơn thế.
- K=2 làm trần oracle hẹp lại (.553 MATH). Một vòng công bằng hơn cần GPU lớn hơn để giữ K=3
  mà không cắt prompt.

## 7. Nếu quay lại hướng này

Ràng buộc `chosen` phải **là một trong các ứng viên** thay vì văn bản tự do — hiện tại hàm mục
tiêu vô tình cho phép model thoát khỏi bài toán selection. Đây là bản vá trực tiếp cho cơ chế đã
xác nhận ở mục 3.
