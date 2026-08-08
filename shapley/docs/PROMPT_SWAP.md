# Prompt tạo ra vai, nhưng vai không tạo ra giá trị — phản chứng hoán vị

`ROLE_SPECIALIZATION.md` đo được rằng phân công lao động sụp đổ ở 1.5B. Nhưng đó mới là **tương
quan**: chưa rõ prompt có phải nguyên nhân, hay chính **cấu trúc** pipeline (vị trí, đầu vào của
từng tầng) mới quyết định hành vi còn prompt chỉ là nhãn dán.

Phản chứng: **hoán vị prompt giữa các vị trí, giữ nguyên luồng dữ liệu.** Mọi chỉ số đo theo
**vị trí**, không theo tên vai — đó là điểm mấu chốt của thiết kế.

| sắp xếp | pos1 | pos2 | pos3 |
|---|---|---|---|
| `normal` | PLAN | SOLVE | VERIFY |
| `swap` | VERIFY | PLAN | SOLVE |
| `solo` | SOLVE | SOLVE | SOLVE |

## Kết quả (GSM8K 1.5B, 5 fold × 30)

### Hành vi bám theo PROMPT, không theo vị trí

| | pos1 | pos2 | pos3 |
|---|---|---|---|
| **normal** | PLAN | SOLVE | VERIFY |
| độ dài (median) | 626 | **18** | 524 |
| **swap** | VERIFY | **PLAN** | SOLVE |
| độ dài (median) | 684 | **278** | 507 |
| **solo** | SOLVE | SOLVE | SOLVE |
| độ dài (median) | 678 | **18** | 745 |

Nhìn cột **pos2**: khi nó mang prompt SOLVE thì output **18 ký tự**; khi mang prompt PLAN thì
**278 ký tự**. Cùng một vị trí, cùng đầu vào, khác 15 lần — **chỉ vì đổi prompt**.

Và ở `solo` (pos2 lại là SOLVE) độ dài **quay về 18** ký tự chính xác.

⇒ **Prompt CÓ tạo ra hành vi khác nhau.** Giả thuyết "prompt chỉ là nhãn dán, cấu trúc mới
quyết định" **bị bác bỏ**.

### Nhưng "vai" không mua được accuracy

| sắp xếp | acc cuối pipeline |
|---|---|
| `normal` (đúng thứ tự vai) | **.6600** |
| `swap` (vai xáo trộn) | **.6600** |
| **`solo`** (KHÔNG có vai) | **.6733** |

**Ba nhánh bằng nhau trong nhiễu, và nhánh KHÔNG có vai nhỉnh nhất.**

`normal` và `swap` giống nhau **đến từng chữ số** (.6600) dù thứ tự vai hoàn toàn khác. Còn bỏ
hẳn vai — ba lượt SOLVE nối tiếp — cho .6733.

## Hai kết luận, và chúng không mâu thuẫn

**(1) Prompt điều khiển hành vi.** Đổi prompt thì độ dài output đổi 15 lần, tỉ lệ chứa đáp án
đổi từ .200 lên .700. Model *có* nghe prompt.

**(2) Hành vi khác nhau đó không chuyển thành accuracy.** Sắp xếp vai đúng, sai, hay bỏ hẳn —
kết quả như nhau.

Ghép lại: **sự chuyên biệt hoá là có thật ở mức hành vi, nhưng vô nghĩa ở mức kết quả.** Pipeline
được lợi từ việc *có ba lượt sinh*, không phải từ việc ba lượt đó *đóng ba vai khác nhau*.

Đây là phiên bản mạnh hơn của kết luận `EXTRA_PASS_FINDING.md` (*"thứ có tác dụng là thêm một
lượt sinh độc lập"*) — giờ có phản chứng trực tiếp thay vì chỉ suy từ tương quan.

## Một chi tiết đáng chú ý: pos2 luôn ngắn nhất

| sắp xếp | pos1 | pos2 | pos3 |
|---|---|---|---|
| normal | 626 | **18** | 524 |
| swap | 684 | **278** | 507 |
| solo | 678 | **18** | 745 |

Ở **cả ba** sắp xếp, pos2 ngắn hơn pos1 và pos3 rõ rệt. Đây là hiệu ứng **vị trí**, chồng lên
hiệu ứng prompt: tầng thứ hai — tầng đầu tiên nhận output của tầng trước — bị ức chế mạnh nhất.

Khớp với `PLANNER_COPYCAT.md`: khi Solver nhận sẵn một lời giải, nó rút gọn còn 18 ký tự. Nhưng
giờ ta biết điều đó **không riêng gì Solver** — nó xảy ra với bất kỳ prompt nào đặt ở vị trí 2,
chỉ khác mức độ (PLAN ở pos2 vẫn viết 278 ký tự, ít bị ức chế hơn SOLVE).

⇒ **Cả prompt lẫn vị trí đều tác động, và chúng cộng dồn.** Vị trí quyết định *bị ức chế bao
nhiêu*; prompt quyết định *viết cái gì*.

## MATH — cùng hướng ở hành vi, nhưng accuracy KHÔNG khớp GSM8K

| | pos1 | pos2 | pos3 | acc |
|---|---|---|---|---|
| `normal` | PLAN 1265 | SOLVE **196** | VERIFY 1139 | **.4600** |
| `swap` | VERIFY 1282 | **PLAN 298** | SOLVE 1077 | **.5133** |
| `solo` | SOLVE 1332 | SOLVE **256** | SOLVE 1104 | **.4400** |

**Hiệu ứng vị trí tái lập**: pos2 ngắn nhất ở cả ba sắp xếp (196 / 298 / 256 so với 1077–1332).
Xác nhận đây không phải đặc thù GSM8K.

**Nhưng hiệu ứng prompt yếu hơn nhiều.** Trên GSM8K, pos2 đổi 18 → 278 ký tự (15 lần) khi đổi
prompt. Trên MATH chỉ 196 → 298 (1.5 lần). Bài khó buộc mọi vai phải viết dài, nên prompt ít
chỗ để ức chế.

**Và accuracy đảo thứ tự:**

| | GSM8K | MATH |
|---|---|---|
| `normal` | .6600 | .4600 |
| `swap` | .6600 | **.5133** |
| `solo` | **.6733** | .4400 |

Trên MATH, `swap` (vai xáo trộn) **cao nhất** (+5.3đ so với `normal`); trên GSM8K thì `solo`
(không vai) cao nhất. **Hai task cho hai thứ hạng khác nhau** — đây là lần đảo dấu thứ bảy của
dự án.

Cách đọc thận trọng: cả hai chênh lệch đều **quanh hoặc dưới sàn nhiễu** (1.3đ trên GSM8K, 5.3đ
trên MATH sát ngưỡng). Kết luận chung cho cả hai task vẫn là **thứ tự vai không quyết định
accuracy** — nếu nó quyết định thì `normal` phải thắng ở cả hai, mà nó không thắng ở đâu cả.

Riêng việc `swap` thắng trên MATH đáng ghi nhận nhưng chưa đủ để kết luận: nó chỉ vượt sàn nhiễu
sát nút, một lần đo, n=150.

## Giới hạn

- GSM8K và MATH, n=150 mỗi task.
- Δ accuracy giữa ba nhánh (≤1.3 điểm) **dưới sàn nhiễu ~5 điểm** — kết luận đúng là *"không đo
  được khác biệt"*, không phải *"solo chắc chắn tốt hơn"*. Điều đó vẫn đủ để bác bỏ *"sắp xếp
  vai đúng thì tốt hơn"*.
- Chỉ số hành vi (18 vs 278 ký tự, leak .200 vs .700) thì **rất xa nhiễu** và là phần đáng tin
  nhất của vòng này.
- `swap` chỉ xoay vòng một cách; các hoán vị khác chưa thử.
