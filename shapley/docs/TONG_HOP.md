# TỔNG HỢP — Khi nào một agent thứ hai có giá trị?

> Tài liệu này gom **chỉ những kết quả sống sót sau kiểm định độc lập (vòng #125)**.
> Số nào bị rút, bị đình chỉ, hoặc không phân biệt được với nhiễu ở n=500 thì **không có mặt ở đây**
> (danh sách rút lại: xem cuối tài liệu). Mọi con số đều có kiểm định ghép cặp McNemar.

---

## 0. Ký hiệu

Một bài toán `x`. Model **yếu** `S` (rẻ), model **mạnh** `M` (đắt).

| ký hiệu | nghĩa | chi phí |
|---|---|---|
| `S` | `S` tự giải | 1 |
| `I` | `M` tự giải, **không thấy gì** | `c` |
| `V` | `M` **được xem** lời giải của `S` rồi kiểm/sửa | 1 + `c` |
| `SEL` | sinh nhiều ứng viên rồi **CHỌN một**, không sửa | tuỳ |

**Mốc so sánh đúng là `I`, không phải `S`.** `I` rẻ hơn `V` (một lượt thay vì hai).
Báo cáo `V − S` là so với **lựa chọn tệ nhất**, không phải lựa chọn thay thế thật.

---

## 1. Ba mệnh đề

### Mệnh đề 1 — GIAO THỨC SỬA ĐỔI thì PHÁ; GIAO THỨC CHỌN thì không

| miền | `V − S` (hay được báo) | **`V − I`** | p |
|---|---|---|---|
| GSM8K (1.5B→7B) | +.1620 | **−.0740** | 3e-4 |
| MBPP (1.5B→7B) | +.1380 | **−.0740** | 3e-4 |
| MATH-500 (1.5B→7B) | — | **−.1260** | 2.7e-10 |

Cùng **hai artifact y hệt**, cùng ngân sách, chỉ đổi **giao thức**:

| giao thức | MBPP 11–510 | MBPP 511–974 |
|---|---|---|
| `V_review` (sửa) | **−.1080** | **−.0690** |
| `SEL` (chọn) | **+.0220** | **+.0151** |
| **chênh** | **+.1300** | **+.0841** |

**Cơ chế, đọc từ trace:** được lệnh *"review"*, `M` **viết lại** — **78%** thiệt hại trên code là
một **bản thứ ba** (không phải chép bản sai). Trên MATH, `V_self` cho **+.0020** (vô hại) còn
`V_weak` cho **−.1260**: thiệt hại **100% đến từ NGUỒN NGOẠI LAI**, không từ việc thêm một lượt.
Trên code tỉ lệ là **38% chế độ / 62% nguồn**.

> **M1. Bất kỳ giao thức nào cho phép `M` GHI ĐÈ artifact đều mất giá trị.
> Giao thức chỉ cho phép `M` CHỌN thì không.**

### Mệnh đề 2 — Bộ chọn chỉ tốt bằng ĐỘ ĐỘC LẬP của tín hiệu, không phải độ mạnh

| pool | bộ chọn = đếm test tự sinh | bộ chọn = đồng thuận thực thi | chênh |
|---|---|---|---|
| 5/7 ứng viên yếu | .6900 | .6060 | **−.0840** |
| **8/8 ứng viên mạnh** | .7280 | .6640 | **−.0640** |

Đồng thuận **thua ở CẢ HAI**, kể cả khi đa số đúng. Lý do đo được trực tiếp:

8 mẫu từ **cùng một model**: **25.0% cùng SAI · 52.8% cùng ĐÚNG · chỉ 22.2% hỗn hợp**.
Trong nhóm hỗn hợp — nơi bỏ phiếu mới có việc làm — **đa số chỉ đúng 46.8%**.

> **Nghịch lý: model đúng 64% tổng thể, nhưng ở những bài CÓ BẤT ĐỒNG đa số chỉ đúng 46.8%.
> Bất đồng CHỌN LỌC ra đúng những bài mà câu trả lời phổ biến nhất là SAI.**

Test tự sinh chỉ đúng **.72** — yếu hơn đồng thuận về mọi mặt — nhưng lỗi của nó **độc lập với**
lỗi của ứng viên (nó do `M` viết từ đề bài). Lỗi đồng thuận **CHÍNH LÀ** lỗi ứng viên.

> **M2. Một tín hiệu YẾU nhưng ĐỘC LẬP thắng một tín hiệu MẠNH nhưng TƯƠNG QUAN.**
> Hệ quả: cộng thêm mẫu từ cùng một model **không thêm bằng chứng**, chỉ thêm **trọng số cho
> phân phối lỗi của model đó**.

### Mệnh đề 3 — Định tuyến có điều kiện tiết kiệm ở nơi ta ÍT CẦN nhất

Cấu hình hợp lý (`S` viết + `S` tự viết test → đạt thì NHẬN, trượt thì leo thang `M`):

| tác vụ | `S` tự tin ở | `p_esc` | chi phí `ROUTE` / chi phí `I` |
|---|---|---|---|
| MATH (H39, kết quả dương) | **37.5%** | .625 | **0.61×** ✓ |
| BigCodeBench (H79b) | **11.3%** | **.887** | **1.36×** ❌ |
| **MBPP (H83d, #137)** | **25.3%** | **.7475** | **1.14×** ❌ |

> **Cảnh báo #137:** ba dòng trên dùng **quy ước chi phí có thể KHÔNG nhất quán** (số lượt tầng rẻ
> tính vào giá). Bản thân **hướng** của M3 (tiết kiệm nơi ít cần nhất) vẫn được cả ba dòng ủng hộ:
> `p_esc` càng cao thì định tuyến càng thua. Cái bị **đình chỉ** là **NGƯỠNG ĐỊNH LƯỢNG**, không
> phải mệnh đề M3.

> **M3. Giá trị của định tuyến tỉ lệ với việc tầng rẻ THƯỜNG XUYÊN tự tin ĐÚNG —
> mà đó chính là điều KHÔNG xảy ra trên tác vụ đủ khó để cần tầng đắt.**
> Đây là **giới hạn cấu trúc**: cùng một tính chất làm bài khó (tầng rẻ hay sai) cũng là
> tính chất giữ cổng leo thang luôn mở.

---

## 2. Hợp nhất

Ba mệnh đề là **ba mặt của một điều kiện duy nhất**. Với artifact `a` (của `S`) và tín hiệu `z`:

```
giá trị của agent thứ hai  =  H(pool)  ×  κ(z)  −  D(giao thức)
```
- **`H(pool)` — TRẦN**: bao nhiêu bài có **ít nhất một** ứng viên đúng, trừ đi `acc(I)`.
  Đo được: tăng đều theo số ứng viên (`.6400 → .7500` khi k đi từ 1 lên 8).
- **`κ(z)` — TỈ LỆ KHAI THÁC**: bộ chọn lấy được bao nhiêu phần của trần. **Bị chặn bởi
  ĐỘ ĐỘC LẬP của `z` với lỗi ứng viên** (M2), không phải bởi độ mạnh của `z`.
- **`D` — PHÁ HOẠI**: giao thức cho phép ghi đè thì `D > 0` (M1); giao thức chỉ chọn thì `D = 0`.

Đọc lại toàn bộ dự án qua công thức này:

| giao thức | `H` | `κ` | `D` | kết quả |
|---|---|---|---|---|
| `V` review | >0 | **0** (không chọn gì) | **lớn** | **−.074 … −.126** ❌ |
| `V_cons` "đừng sửa" | >0 | 0 | 0 nhưng **thừa hưởng `acc(S)`** | **−.1560** ❌ |
| đồng thuận | >0 | **≈0** (tương quan) | 0 | **−.064 … −.084** ❌ |
| GRPO verifier | >0 | 0 | 0, **học nhại lại** ⇒ chặn trần ở `acc(S)` | +.018 (dưới ngưỡng) ❌ |
| `SEL` test tự sinh | >0 | **~.5–.9** | **0** | **+.015 … +.022** ✓ |
| `SEL` + nhiều ứng viên | **lớn hơn** | ~.7 | 0 | **+.0496** (dải giữ lại) ✓ |
| test **chạy được** | >0 | **cao** (oracle thật) | 0 | **+.0401 / +.0388** ✓ |

**Mọi kết quả ÂM là `D > 0` hoặc `κ ≈ 0`. Mọi kết quả DƯƠNG là `D = 0` và `κ > 0`.**

### Nghịch lý phục tùng/chủ động — hệ quả trực tiếp
Muốn `D = 0` thì `M` phải **không sửa**. Nhưng nếu `M` **không sửa gì cả** thì nó thừa hưởng
`acc(S)`. Đo được: `V_cons` giữ nguyên 75% ⇒ tụt về **.4840** (nguồn có `acc` = .428).

| cực | `D` | trần |
|---|---|---|
| quá **chủ động** (`V_std`) | **lớn** — phá bản đúng | — |
| quá **phục tùng** (`V_cons`, GRPO) | 0 | **chặn ở `acc(S)`** |

> **Không có điểm ngọt ở tầng prompt**, vì chọn giữa hai cực đòi hỏi biết đâu đúng đâu sai —
> **chính là bài toán cần giải**. Lối thoát duy nhất là **CHỌN** (D=0 mà không phục tùng),
> và nó cần một `z` độc lập.

---

## 3. Dự đoán KIỂM ĐƯỢC (chưa kiểm)

1. **`κ` phải tăng khi `z` độc lập hơn.** Test do **model KHÁC** viết phải chọn tốt hơn test tự viết.
2. **`D` phải bằng 0 cho mọi giao thức chỉ-chọn**, kể cả với >2 ứng viên và nguồn hỗn hợp — đã đúng ở k≤8.
3. **`H` với ứng viên từ HỌ MODEL KHÁC phải cao hơn** cùng số ứng viên từ một model
   (lỗi ít tương quan hơn) — hệ quả trực tiếp của M2, chưa đo.
4. ~~**M3 định lượng:** định tuyến hoà vốn khi `p_esc < 1 − (chi phí rẻ)/(chi phí đắt)` …
   **Công thức khớp cả hai trường hợp đã có.**~~
   > **ĐÌNH CHỈ từ #137 — ĐỪNG TRÍCH.** Điểm thứ ba (H83d, MBPP 1.5B→7B) rơi vào **hàng 4** của
   > đăng ký trước #92: công thức dự đoán **THẮNG** (`p_esc .7475 < ngưỡng .803`), thực tế
   > **THUA** (`ROUTE` đắt hơn `I` 1.142×).
   > **Nguyên nhân:** ngưỡng `.803` giả định tầng rẻ tốn **1 lượt**, còn thiết kế tốn **2**
   > (giải + viết test). Với `c_rẻ = 2` ⇒ ngưỡng `.606` < `.7475` ⇒ dự đoán thua, khớp thực tế.
   > **Nhưng MATH cũng dùng ngưỡng `.803`**, tức cùng giả định sai ⇒ **thành tích "2/2" ở trên
   > không đáng tin cho tới khi cả ba điểm được tính lại bằng MỘT quy ước chi phí duy nhất.**
   > Việc phải làm: (1) chốt quy ước, (2) tính lại 3 điểm, (3) đăng ký trước rồi mới đo điểm thứ tư.

## 4. KHÔNG được kết luận từ tài liệu này
- Không có điểm nào ở **32B trở lên** — hai lần HUỶ vì hạ tầng (#123, #130), chưa vì khoa học.
- `SEL − I` chỉ **+.0220** [+.008, +.038] (p .0074) và **+.0151** [+.002, +.028] (p .039),
  gộp Fisher p .0026 — **sát ngưỡng .02 mà mục 5 gọi là nhiễu**, và **lật 6 bài là xoá sạch**
  hiệu ứng ở H69c (kiểm định #125-D bắt buộc nêu kèm CI). Kết luận vững là **`SEL − V_review`**
  (+.1300 / +.0841), tức **tránh REVIEW**; giá trị thật của agent yếu thì **nhỏ và mong manh**.
- Mọi thứ ở **một họ model (Qwen2.5)**, hai benchmark, greedy.
- Phần lớn trùng hướng tài liệu đã có: **Huang et al. 2023** (self-correct thất bại),
  **Cobbe et al. 2021** (best-of-n có verifier), **Wang et al. 2022** (self-consistency).
  Đóng góp ở đây là **định lượng `V−S` vs `V−I`** và **hợp nhất ba thất bại bằng một điều kiện**.

## 5. Đã RÚT LẠI (đừng trích)
"k=2 là điểm ngọt" · "tự xem lại giúp trên toán +.108" · "agent yếu thua mẫu của chính model
mạnh (+.012)" · "tie_rate giảm theo k" · "5/5 fold" (hai chỗ thực ra 4/5) · mọi chênh lệch ≤ .02
ở n=500 · quét năng lực 1.5B/7B/14B (thiết kế trộn chế độ với nguồn).
