# Vòng ORPO của ta khác H23/H26 của main ở đâu — và bài học cần mượn trước khi đọc kết quả

Main đã chạy **H23 (GRPO cho Verifier)** và đang đăng ký trước **H26 (3 adapter riêng cho 3 vai)**.
Vòng ORPO Aggregator của ta chạy song song, độc lập. Tài liệu này đối chiếu để (a) không kể lại
kết quả đã có, (b) mượn đúng bài học trước khi nhìn số của mình.

## H23 đã dạy gì — hàm thưởng, không phải thuật toán

GRPO trên Verifier, GSM8K, 5 fold:

| | base | sau GRPO |
|---|---|---|
| độ chính xác can thiệp | .70–.90 | **1.00 (5/5 fold)** |
| **V_gain** | +.068 | **+.044** |
| số lần can thiệp /100 | 20.2 | **8.4** |
| sửa / phá | 45 / 11 | **22 / 0** |

Nó đạt precision 100% bằng cách **nói ít đi một nửa**. Reward là `+1 sửa / −1 phá / 0 nếu không
đổi`, nên chiến lược tối ưu tầm thường là **im lặng** — im lặng miễn phí.

> *"Model đã tối ưu ĐÚNG thứ tôi viết ra. Lỗi ở HÀM THƯỞNG, không ở thuật toán."*

Điều cứu kết luận này là **chỉ số `số lần can thiệp` đã được khoá trước khi chạy**. Không có nó,
báo cáo sẽ là *"độ chính xác can thiệp đạt 100%!"* — đúng số, sai câu chuyện.

## Vòng của ta khác ở ba điểm

| | H23 (main) | **ORPO Aggregator (ta)** |
|---|---|---|
| vai | Verifier | **Aggregator** |
| thuật toán | GRPO (online, cần rollout) | **ORPO** (offline, từ cặp có sẵn) |
| reward | +1/−1/0, **im lặng miễn phí** | **chosen/rejected trên cùng prompt** |
| task | GSM8K | **MATH** |

Điểm khác quan trọng nhất: **ORPO không có lối thoát "im lặng"**. Cặp preference luôn có một
`chosen` và một `rejected` cho cùng một prompt, nên model buộc phải xếp hạng — không tồn tại
hành động "không làm gì" để lẩn vào.

Nhưng ta có **lối thoát tầm thường riêng**, và tôi đã chặn trước: nếu luôn đặt `chosen` ở vị trí
1 thì model học *"chọn Candidate 1"* thay vì học chọn đúng. Vì vậy `rebuild_pairs_k2.py` đảo vị
trí luân phiên (50/50). Đây đúng là loại lỗi mà H23 dính.

## Bài học mượn: chỉ số phải khoá trước, và phải là chỉ số bắt được lối tắt

H23 sống sót nhờ khoá `số lần can thiệp`. Tương đương ở vòng ta là **`copies_last`** — đã khoá
trong `ORPO_AGGREGATOR.md` trước khi train, và kernel eval tính sẵn.

Ba kịch bản, diễn giải khoá trước:

| kết quả | kết luận |
|---|---|
| accuracy tăng **và** `copies_last` giảm | ORPO sửa được recency bias — kết quả dương thật |
| accuracy **đứng yên**, `copies_last` giảm mạnh | adapter đổi hành vi nhưng recency bias **không phải** nguyên nhân chính của lỗi |
| accuracy tăng, `copies_last` **không đổi** | cải thiện đến từ chỗ khác — phải tìm ra chỗ đó trước khi kể |
| cả hai không đổi | 428 cặp không đủ dịch chuyển hành vi |

## Một trần thấp hơn tôi từng nói

Trong 172 ca Aggregator chọn sai (trên dữ liệu train):

| | |
|---|---|
| chọn nhầm một **ứng viên có sẵn** | 131 (**76%**) — ORPO nhắm được |
| **tự bịa** đáp án không có trong ứng viên nào | 41 (**24%**) — ORPO **không** nhắm được |

Ví dụ thật: ứng viên sai là `3` và `3(√3+1)`, còn Aggregator xuất ra `3(√5+1)/4` — không phải
cái nào. Với 24% này, cặp vẫn tạo được nhưng nó dạy *"đừng chọn ứng viên sai"* chứ không dạy
*"đừng bịa"*.

Khớp với đo đạc độc lập ở `ROLE_SPECIALIZATION.md`: Aggregator sinh đáp án ngoài đầu vào ở 12%
số câu MATH và **0 ca nào trong đó đúng** — nhiễu thuần túy.

⇒ **Trần thực tế của ORPO là ~76% lỗi chọn**, không phải toàn bộ lỗi. Phải nói rõ khi diễn giải.

## H26 của main và vòng này bổ sung nhau

H26 train **3 adapter cho P/S/V** với reward = đóng góp biên, cộng **phạt im lặng −0.3** — bản
vá trực tiếp cho lỗi H23. Nó **không** đụng Aggregator.

Nên hai vòng ghép lại phủ được cả 4 vai, và dùng hai họ thuật toán khác nhau (online RL vs
offline preference). Nếu cả hai cùng thất bại theo hai cách khác nhau, đó là bằng chứng mạnh hơn
nhiều so với một lần thất bại.

Đáng chú ý: H26 tự khoá trước một kịch bản rất giống thứ ta đã đo — *"nếu A_plan hội tụ về nói
thẳng đáp án thì phải báo là BIẾN PLANNER THÀNH SOLVER, không được kể là chuyên biệt hoá vai"*.
`ROLE_SPECIALIZATION.md` cho thấy Planner 1.5B vốn **đã** làm vậy sẵn (33% kế hoạch chứa đáp án
trên MATH), nên đây là rủi ro thật chứ không phải giả định.
