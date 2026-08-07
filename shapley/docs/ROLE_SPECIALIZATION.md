# Bốn vai trò có thật sự khác nhau không? — hai vai phân hóa cùng năng lực, hai vai thì không

Dự án bắt đầu bằng câu hỏi đo lường (*"vai nào đóng góp bao nhiêu"*), vốn **giả định** các vai
làm đúng việc mà tên gọi nói. Vòng này kiểm chính giả định đó bằng chỉ số **hành vi** đọc từ
trace, không phải accuracy.

Chỉ số quyết định: **tỉ lệ lượt sinh ra đáp án không có trong đầu vào của nó**. Một vai *làm
việc* thì thỉnh thoảng phải sinh ra thứ mới; một *trạm trung chuyển* thì không bao giờ.

## Bảng

| chỉ số hành vi | GSM8K 1.5B | MATH 1.5B | **MATH 7B** |
|---|---|---|---|
| n | 150 | 150 | 100 |
| **PLANNER** — *"Do NOT compute the final answer"* | | | |
| kế hoạch chứa sẵn đáp án đúng | 6.7% | **33.3%** | **1.0%** |
| kế hoạch có `\boxed{}` | 3.3% | **45.3%** | **0.0%** |
| **SOLVER** — *"solve step by step"* | | | |
| lượt không sinh số mới nào | **60.7%** | **62.0%** | **11.0%** |
| độ dài lời giải (median) | **19** | 344 | **1247** |
| … khi không có plan | 664 | 1384 | 1264 |
| **VERIFIER** — *"check each step"* | | | |
| tái sử dụng số của Solver | 67.7% | 77.2% | 87.0% |
| … khi thật sự đổi đáp án | 42.5% | 70.1% | 69.2% |
| tỉ lệ lượt có can thiệp | 32.7% | 38.0% | **14.0%** |
| **AGGREGATOR** — *"decide by re-checking"* | | | |
| lặp lại đáp án Verifier | 93.3% | 73.3% | **97.0%** |
| **đáp án không có trong đầu vào** | 1.3% | 12.0% | 3.0% |
| … trong đó **đúng** | **1 ca** | **1 ca** | **1 ca** |

## Kết luận: chuyên biệt hóa là **có điều kiện**, không phải hoàn toàn danh nghĩa

Câu hỏi đặt ra là *"nâng năng lực thì các vai có phân hóa không"*. Trả lời: **hai vai phân hóa
rõ rệt, hai vai thì không.**

### Phân hóa cùng năng lực — Planner và Solver

**Planner ngừng giải hộ.** Tỉ lệ kế hoạch chứa sẵn đáp án đúng sụp từ **33.3% xuống 1.0%**, và
`\boxed{}` từ 45.3% xuống **0%**. Ở 7B nó thật sự *lập kế hoạch* thay vì giải rồi giấu đáp án.

**Solver ngừng chép.** Lượt không sinh số mới nào giảm từ **62% xuống 11%**, độ dài lời giải
tăng từ 344 lên **1247 ký tự**. Và quan trọng hơn: ở 7B, lời giải **có plan** (1247) gần bằng
**không có plan** (1264) — tức plan không còn bóp nghẹt phần trình bày. Ở 1.5B khoảng cách này
là 19 vs 664 trên GSM8K, tức gấp **35 lần**.

⇒ Hai hiện tượng "Planner giải hộ" và "Solver chép lại" là **đặc thù model yếu**, không phải
tính chất của kiến trúc multi-agent. Tuyên bố *"specialization is nominal"* **không đúng ở 7B**
cho hai vai này.

### KHÔNG phân hóa — Aggregator

Đây là phần bất ngờ. Nâng lên 7B khiến Aggregator **tệ hơn về mặt tự chủ**:

| | 1.5B | 7B |
|---|---|---|
| lặp lại đáp án Verifier | 73.3% | **97.0%** |
| đáp án không có trong đầu vào | 12.0% | 3.0% |

**Nó chép nhiều hơn, không ít hơn.** Và trên tổng **400 câu ở cả ba cấu hình**, nó sinh ra đáp
án mới-và-đúng đúng **3 lần** — mỗi cấu hình 1 ca.

Diễn giải hợp lý: ở 7B, ứng viên đầu vào đã tốt hơn nên "đồng ý" là hành vi hợp lý. Nhưng dù lý
do là gì, kết quả vẫn là **Aggregator không tính toán ở bất kỳ mức năng lực nào đã đo**. Đây là
kết luận **bền qua cả ba ô** — hiếm trong dự án này, nơi phần lớn hiệu ứng đảo dấu.

### Verifier — phân hóa theo hướng khác

Ở 7B nó **can thiệp ít hơn hẳn** (38% → 14%) nhưng tái sử dụng lời giải Solver **nhiều hơn**
(77% → 87%). Tức nó chuyển từ *"giải lại"* sang *"đọc rồi phần lớn đồng ý"*. Kèm theo là
`V_gain` sụp về +0.010 [−.05, +.05], chỉ 2/5 fold dương.

## Một kết quả phụ đáng chú ý: ở 7B, pipeline LÀM HẠI

| tầng | acc |
|---|---|
| **Solver một mình** | **.720** |
| P→S | .670 |
| P→S→V | .680 |
| P→S→V→A | .690 |

**Solver 7B làm một mình tốt hơn cả pipeline đầy đủ 3 điểm.** Thêm Planner làm mất 5 điểm; V và
A gỡ lại được 2. Khớp với kết luận của main rằng mọi cải thiện đều thua việc dùng model to hơn —
ở đây còn mạnh hơn: **thua chính model đó chạy một mình.**

Verifier 7B gỡ được **0/10** lỗi do plan gây ra và 2/23 lỗi Solver tự gây, ngược hẳn với 1.5B
(62% và 8% trên MATH).

## Phát biểu đúng

Không phải *"chuyên biệt hóa chỉ tồn tại trên danh nghĩa"* mà là:

> **Với model yếu, phân công lao động sụp đổ: Planner giải hộ, Solver chép lại. Nâng lên 7B thì
> hai vai này hồi phục đúng vai trò — nhưng lúc đó pipeline lại thua chính Solver chạy một
> mình. Aggregator thì không tính toán ở bất kỳ mức năng lực nào.**

Nói cách khác: multi-agent có phân công thật ở nơi nó **không cần thiết**, và mất phân công ở
nơi nó **được kỳ vọng giúp**.

## Giới hạn

- 7B chỉ n=100 (5 fold × 20), chạy 4-bit nf4. Các Δ accuracy đều dưới sàn nhiễu ~5 điểm nên
  phần accuracy chỉ đọc được theo hướng, không theo độ lớn.
- Chỉ số hành vi thì đáng tin hơn nhiều — chúng là thay đổi 3–45 lần (33.3%→1.0%,
  62%→11%, 19→1247 ký tự), vượt xa mọi nhiễu đo đạc.
- Chưa có GSM8K 7B để hoàn tất lưới 2×2. Script tự chạy khi có trace.
- Chỉ 1 họ model (Qwen2.5). Phân hóa có thể khác ở họ khác.
