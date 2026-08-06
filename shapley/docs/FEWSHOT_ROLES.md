# Few-shot chuyên biệt hoá vai trò: đổi được hành vi, không đổi được accuracy

5 fold × 30 câu mỗi task, Qwen2.5-1.5B greedy. Kernel `pipeline/fewshot_folds_kernel.py`.
Trace đầy đủ: `results_fsfold/{gsm8k,math}/traces.json` (150 câu × 5 nhánh mỗi task).

## Vì sao thử few-shot

`docs/PLANNER_COPYCAT.md` cho thấy hai cách sửa bằng lời đều **thất bại**:

- Chỉ thị phủ định `"Do NOT compute the final answer"` — Planner vẫn giải trọn bài, còn viết cả
  `\boxed{}`.
- Nhắc thêm Solver `"you must write out every calculation yourself"` — output **giống hệt từng
  ký tự** với nhánh không nhắc, ở 4/8 ca GSM8K.

Few-shot khác về bản chất: nó **cho model xem** dạng output mong muốn thay vì mô tả bằng lời.

Năm nhánh trên cùng bộ bài: `NP` (không plan) · `bP_bS` (baseline) · `fP_bS` (few-shot planner) ·
`bP_fS` (few-shot solver) · `fP_fS` (cả hai).

## 1. Hình thức plan: few-shot có tác dụng, ở CẢ HAI task

| chỉ số plan | GSM8K base | GSM8K few-shot | MATH base | MATH few-shot |
|---|---|---|---|---|
| chứa sẵn đáp án đúng | .420 | **.193** | .360 | **.160** |
| có `\boxed` | .033 | .000 | .453 | **.047** |
| có dấu `=` | .907 | **.393** | .960 | **.440** |
| số chữ số (median) | 28.4 | **7.6** | 56.4 | **8.0** |
| độ dài | 618 | 259 | 1153 | 320 |

Nhất quán ở cả hai task: rò rỉ đáp án **giảm hơn một nửa**, số chữ số giảm **4–7 lần**,
`\boxed` trên MATH gần như biến mất (.453 → .047).

Đây là thay đổi hành vi lớn và ổn định — thứ mà chỉ thị bằng lời không làm nổi.

## 2. Accuracy: không nhánh nào cải thiện

**GSM8K** (Δ so với baseline .700):

| nhánh | mean | khoảng | fold cùng dấu |
|---|---|---|---|
| NP (bỏ plan) | **−0.060** | [−.133, −.033] | **5/5** ✅ |
| few-shot planner | −0.013 | [−.133, +.133] | 3/5 |
| few-shot solver | −0.007 | [−.033, +.067] | 3/5 |
| cả hai | −0.060 | [−.200, .000] | 3/5 |

**MATH** (Δ so với baseline .473):

| nhánh | mean | khoảng | fold cùng dấu |
|---|---|---|---|
| NP (bỏ plan) | −0.060 | [−.200, +.033] | 3/5 |
| few-shot planner | −0.013 | [−.100, +.100] | 2/5 |
| **few-shot solver** | **+0.027** | [−.133, +.100] | 4/5 |
| cả hai | −0.013 | [−.100, +.067] | 2/5 |

**Chỉ một hiệu ứng đạt chuẩn 5/5 fold cùng dấu: bỏ plan đi thì tệ hơn −6 điểm trên GSM8K.**

Nhánh triển vọng nhất là few-shot solver trên MATH (+2.7đ, 4/5 fold) nhưng khoảng vẫn chứa 0 và
độ lớn dưới ngưỡng ~5 điểm của sàn nhiễu H13 → **chưa phải bằng chứng**.

## 3. Đọc kết quả

Few-shot **làm đúng việc nó hứa** — plan hết chứa đáp án, và Solver quay lại tự trình bày (trên
MATH n=30 trước đó: `<200 ký tự` .433 → .033, median độ dài 370 → 1379). Nhưng **accuracy không
nhúc nhích**.

Kết hợp với `docs/VERIFIER_RESCUE.md`, bức tranh hợp lý nhất là:

> Việc Planner giải hộ **không phải nguyên nhân chính của lỗi**. Plan chứa sẵn đáp án vẫn giúp
> pipeline +6 điểm so với không có plan (GSM8K, 5/5 fold). Và khi plan có dắt Solver đi sai thì
> Verifier gỡ lại được 71% số ca đó.

Nói cách khác: hiện tượng copycat khiến vai "Planner" **không đúng như tên gọi** — nhưng nó
không phải chỗ để tìm accuracy. Lợi ích của plan có vẻ đến từ việc **cho model thêm một lượt
sinh trước khi chốt đáp án**, chứ không phải từ chất lượng "kế hoạch" theo nghĩa thông thường.

Đây là một giả thuyết khớp dữ liệu hiện có, **chưa được kiểm trực tiếp**. Phép thử sạch sẽ là:
thay plan bằng một lượt sinh trung tính cùng độ dài (không phải kế hoạch) và xem +6 điểm còn
không.

## 4. Giới hạn

- n = 150 mỗi task (5 × 30). Sàn nhiễu H13 ở n ≤ 250 là **~5 điểm**; mọi Δ ở đây đều nhỏ hơn thế
  trừ nhánh NP. Kết luận trung thực: **"không đo được cải thiện"**, không phải "chắc chắn vô ích".
- Chỉ số hình thức plan thì đáng tin hơn nhiều — chúng là thay đổi 3–7 lần, không phải vài điểm.
- Chỉ chạy 1.5B. Chưa biết few-shot có hành xử khác ở 7B không.
