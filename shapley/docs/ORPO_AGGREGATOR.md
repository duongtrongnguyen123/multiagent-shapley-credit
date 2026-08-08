# ORPO cho Aggregator — giai đoạn 1: dữ liệu preference

Ghi nhật ký vòng ORPO. Mục này viết **trước khi train**, để tiêu chí thành công được chốt trước
khi nhìn thấy kết quả.

## Vì sao làm

Khoảng trống đo được từ `EXTRA_PASS_FINDING.md` và `AGG_FORMAT_CHECK.md` (MATH, 1.5B):

| | acc |
|---|---|
| Solver một mình | .413 |
| agg3 (LLM chọn, K=3) | .467 (5/5 fold) |
| **vote5** (bỏ phiếu cơ học) | **.507** |
| **ORACLE** (luôn chọn ứng viên đúng) | **.673** |

Còn **17 điểm** giữa bỏ phiếu và oracle. Trong các ca `vote5` sai, **35% vẫn có ứng viên đúng**
nằm sẵn. Và **86% lỗi của Aggregator là chọn sai thật** (chỉ 11/81 ca do thiếu `\boxed`) — đã
kiểm chéo với H20 của main. Đây là bài toán selection.

## Giai đoạn 1 — kết quả (đã xong)

3 shard song song trên MATH **train**, K=3 ứng viên đều từ Solver (không Verifier), 1500 câu:

| shard | n | cặp | yield | agg_acc |
|---|---|---|---|---|
| s0 (TrgDinKai) | 500 | 134 | 27% | .504 |
| s1 (TrgDinKai) | 500 | 150 | 30% | .520 |
| s2 (tbmdemi) | 500 | 144 | 29% | .518 |
| **tổng** | **1500** | **428** | **29%** | **.514** |

Thời gian thực: ~7h song song thay vì ~22h tuần tự.

### Yield 29%, không phải 44% như ước tính

Smoke test N=50 đã cảnh báo trước (24%), và con số đầy đủ xác nhận. Nguyên nhân:

| | tỉ lệ |
|---|---|
| cả K ứng viên đều **SAI** → không có `chosen` | **37%** |
| cả K ứng viên đều **ĐÚNG** → không có `rejected` | **35%** |
| hỗn hợp → tạo được cặp | **29%** |

Ước tính 44% của tôi lấy từ trace MATH-500 **test**, không tính đến việc **MATH train dễ hơn**:
Solver đạt .514 trên train so với .413 trên test, nên tỉ lệ "cả 3 đều đúng" cao hơn nhiều.

### Chất lượng dữ liệu

Chấm lại độc lập bằng `analysis/merge_pairs.py` (không tin nhãn của kernel):

| kiểm tra | kết quả |
|---|---|
| `chosen` không đúng | **0** ✅ |
| `rejected` lại đúng | **0** ✅ |
| `rejected` **đúng là ứng viên Aggregator đã chọn** | 131 (31%) |
| cặp từ câu Aggregator vốn chọn sai | 172 (40%) |

Phân bố cân đối — Level 1-5 (25/83/106/107/107) và 6 chủ đề (Algebra 104, Prealgebra 67,
Number Theory 63, Intermediate Algebra 63, Counting & Probability 54, Precalculus 41).

**Một cặp điển hình** (gold `63π`, Level 5, Algebra) — hai lời giải gần như giống hệt, khác đúng
một bước tính bán kính, và Aggregator chọn nhầm cái sai:

```
chosen  : ... radius √63 ... A = π(√63)² = 63π   ->  \boxed{63\pi}
rejected: ... radius √67 ... A = π(√67)² = 67π   ->  \boxed{67\pi}
```

Đây đúng loại lỗi cần dạy: không phải "lời giải hay vs dở" mà là **chọn nhầm giữa hai lời giải
gần giống nhau**.

## Tiêu chí thành công — CHỐT TRƯỚC KHI TRAIN

| kết quả | kết luận bắt buộc |
|---|---|
| agg3-ORPO **> vote5 (.507)** và **5/5 fold** cùng dấu | thắng mốc thực dụng — kết quả dương thật |
| > `vote3` nhưng ≤ .507 | thắng **cùng ngân sách**, thua bỏ phiếu 5 mẫu → kết quả một phần |
| .467 < x ≤ `vote3` | cải thiện so với chính nó nhưng **thua bỏ phiếu miễn phí** → thất bại thực dụng |
| ≤ .467 | ORPO không dịch chuyển được hành vi |

Chỉ số phụ **bắt buộc** báo cáo: `copies_last` (hiện **65%** ở K=5, **75%** ở K=2). Nếu accuracy
đứng yên mà `copies_last` giảm mạnh → ORPO có tác dụng lên hành vi nhưng recency bias không phải
nguyên nhân chính của lỗi. Thông tin này có giá trị kể cả khi accuracy không đổi.

## Rủi ro ghi trước

428 cặp là **ít** so với literature DPO/ORPO (thường hàng nghìn tới hàng chục nghìn). LoRA trên
1.5B với ngần này dữ liệu có khả năng thật là không dịch chuyển được gì.

Nhưng kết quả âm vẫn có giá trị: nếu train mà `copies_last` 65% không giảm, đó là bằng chứng
recency bias là **giới hạn năng lực** của 1.5B chứ không phải vấn đề thiếu dữ liệu.

## Giai đoạn 2 — chưa chạy

`orpo_kernel.py` (ORPO LoRA r=16, `trl`+`peft`) và `orpo_eval_kernel.py` (5 fold trên MATH-500
**test**, cùng bộ câu để so trực tiếp). Cần upload `pairs_all.jsonl` (3.6 MB) thành Kaggle
dataset trước.
