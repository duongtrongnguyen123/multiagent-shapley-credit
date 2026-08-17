# TỔNG HỢP — Khi nào một agent thứ hai có giá trị?

> Tài liệu này gom **chỉ những kết quả sống sót sau kiểm định độc lập (vòng #125)**.
> Số nào bị rút, bị đình chỉ, hoặc không phân biệt được với nhiễu ở n=500 thì **không có mặt ở đây**
>(danh sách rút lại: xem cuối tài liệu).
> **Về kiểm định (sửa ở #160):** các con số ở **M1 mục `V−I`**, **#142**, **#145**, **#149** đều có
> McNemar ghép cặp. **KHÔNG có** kiểm định cho: bảng giao thức của M1 (−.1080 / +.0220 / chênh +.1300),
> bảng bộ chọn của M2 (−.0840 / −.0640), và mọi số từ #158 (đã rút ở #160).
> Câu cũ *"mọi con số đều có kiểm định McNemar"* là **SAI** và đã bị thay.

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

#### M1 có một ĐƠN THUỐC, và đơn thuốc đó ĐÃ CHẾT (#142, tái lập 2/2)
Nếu `D > 0` vì `M` ghi đè lên bản **vốn đã đúng**, thì **chặn ghi đè bằng cổng độc lập** phải khử
được `D`. Kiểm bằng H88d/H88e, hai dải **tách rời**:

| đại lượng | 11–510 | 511–974 |
|---|---|---|
| `Δ_gate` = cổng có cứu được "sửa" không | **+.0040** (p .69) | **+.0000** (p 1.00) |
| **`Δ_ceil` = cổng ORACLE so với `I`** | **−.0641** (p .0016) | **−.0583** (p .0067) |
| `Δ_cont` = leo thang bằng GIẢI LẠI vs bằng SỬA | **+.0902** (p 1e−6) | **+.0994** (p 1e−6) |

1. **Cổng không làm gì cả** (`Δ_gate` null hai lần). Phá hoại **không nằm** ở tập cổng-đạt:
   `V` phá 12 bài `S` đúng, chỉ **4** bài trong tập cổng-đạt.
2. **Ngay cả cổng ORACLE cũng THUA `I`.** Không có hệ thống nào vượt được chặn trên này ⇒
   **không có gì để khai thác** từ artifact của model yếu qua đường SỬA. Cải thiện tín hiệu là vô ích.
3. **Thiệt hại nằm ở NHÁNH LEO THANG:** khi đã quyết định can thiệp, **giải lại từ đầu hơn sửa
   ~+.09**. Cùng ngân sách, khác **duy nhất** ở chỗ `M` có **nhìn thấy** artifact hay không.

> **Phát biểu lại M1 cho mạnh hơn: vấn đề không phải `M` ĐƯỢC PHÉP ghi đè, mà là `M` NHÌN THẤY.
> Việc nhìn thấy làm hỏng model mạnh ĐÚNG Ở những bài mà model yếu đã sai — tức đúng chỗ
> ta cần model mạnh nhất.** Cổng không cứu được, vì cổng chỉ điều khiển *ghi đè*, không điều
> khiển *nhìn thấy*.

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
| **`G_V` sửa CÓ CỔNG** (#142) | >0 | 0 | **VẪN lớn** — cổng không chạm tới | **−.0842 / −.0929** ❌ |
| **`G*_V` cổng ORACLE** (#142) | >0 | 0 | **vẫn lớn** ⇒ **CHẶN TRÊN của cả dòng sửa** | **−.0641 / −.0583** ❌ |
| `SEL` test tự sinh | >0 | **~.5–.9** | **0** | **+.015 … +.022** ✓ |
| `SEL` + nhiều ứng viên | **lớn hơn** | ~.7 | 0 | **+.0496** (dải giữ lại) ✓ |
| test **chạy được** | >0 | **cao** (oracle thật) | 0 | **+.0401 / +.0388** ✓ |
| **`SEL` pool KHÁC HỌ** (#145) | **lớn nhất đo được** (+.069 trần) | **~.63** | 0 | **+.0452** ✓ **tái lập 2/2** |

**Mọi kết quả ÂM là `D > 0` hoặc `κ ≈ 0`. Mọi kết quả DƯƠNG là `D = 0` và `κ > 0`.**

### Sửa công thức sau #142: `D` phụ thuộc PHƠI NHIỄM, không phụ thuộc QUYỀN GHI ĐÈ

Bản đầu viết `D(giao thức)` và ngầm hiểu *"giao thức nào cho ghi đè thì `D > 0`"*. **Sai.**
#142 dựng cổng chặn ghi đè, kể cả **cổng ORACLE**, và `D` **không giảm** (`Δ_gate` = +.004 / +.000,
null hai lần). Phá hoại **không nằm** ở tập cổng-đạt: `V` phá 12 bài `S` đúng, chỉ **4** trong tập đó.

```
D = D(phoi nhiem)     KHONG phai   D(quyen ghi de)
```
Bằng chứng trực tiếp: `Δ_cont` = **+.0902 / +.0994** (p 1e−6) — cùng ngân sách, cùng bài, chỉ khác
việc `M` **có nhìn thấy** artifact hay không. Nhìn thấy tốn ~**.09**.

**Kiểm độc lập lần hai (#149, H92/H92b), bỏ HẲN lệnh "review":** mọi nhánh dùng **cùng một lệnh
`SOLVE`**, chỉ khác phần ngữ cảnh thêm vào. Cho `M` xem **toàn bộ code** của model yếu:

| | MBPP 11–510 | MBPP 511–974 |
|---|---|---|
| `E3` (thấy code) − `E0` (không thấy gì) | **−.0782** (p 1.5e−04) | **−.0778** (p 8.7e−05) |

Hai dải tách rời, lệch nhau **.0004**. ⇒ **thiệt hại KHÔNG cần lệnh ghi đè; chỉ cần NHÌN THẤY.**
Đây là hàng được viết sẵn để **giết** phát biểu này, và nó **không nổ ở cả hai lần**.

> **CHƯA biết là LIỀU hay NGƯỠNG.** Mức phơi nhiễm trung gian (chỉ chữ ký hàm) cho −.0140 (p .48)
> và −.0324 (p .072) — **không có ý nghĩa ở cả hai dải và đổi biên độ giữa chúng**. Phân định
> được thì cần `n` ≈ 2000–4000. **Không trích rằng "càng thấy nhiều càng hại"** — chưa đo được.

**Hệ quả cho thiết kế hệ thống:** muốn `D = 0` thì **không được cho model mạnh nhìn** sản phẩm của
model yếu **trong lượt sinh**. Chỉ được nhìn **ở lượt CHỌN**, sau khi nó đã có bản của chính mình.
Đó đúng là hình dạng của `SEL` — và đó là lý do `SEL` là **thứ duy nhất** cho kết quả dương.

### Nghịch lý phục tùng/chủ động — **đã sửa sau #142**

> ⚠️ **Bản trước viết: *"Muốn `D = 0` thì `M` phải không sửa"*. #142 BÁC BỎ câu đó.**
> Cổng chặn ghi đè — kể cả **cổng ORACLE** — **không** làm `D` giảm (`Δ_gate` null hai lần).
> **Không sửa là KHÔNG ĐỦ**, vì `M` **vẫn đã nhìn thấy**.

Ba cực, không phải hai:

| cực | `M` có **nhìn thấy** trước khi sinh? | `D` | trần |
|---|---|---|---|
| quá **chủ động** (`V_std`) | có | **lớn** — phá bản đúng | — |
| quá **phục tùng** (`V_cons`, GRPO) | có | **vẫn > 0**, cộng thêm **thừa hưởng `acc(S)`** | **chặn ở `acc(S)`** |
| **sửa CÓ CỔNG** (`G_V`, `G*_V` — #142) | có | **KHÔNG đổi** (`Δ_gate` = +.004 / +.000) | **vẫn dưới `acc(I)`** |
| **CHỌN** (`SEL`) | **KHÔNG** — `M` tự giải xong rồi mới so | **0** | `H(pool)` |

Đo được cho cực phục tùng: `V_cons` giữ nguyên 75% ⇒ tụt về **.4840** (nguồn `acc` = .428).

> **Không có điểm ngọt ở tầng prompt** — và giờ ta biết **vì sao**: cả ba cực đầu đều để `M`
> **nhìn thấy artifact TRƯỚC KHI nó sinh ra bản của mình**. Prompt điều khiển được *`M` làm gì
> với thứ nó thấy*, nhưng không xoá được *việc nó đã thấy*.
> **Lối thoát duy nhất là CHỌN**: `M` sinh bản của chính nó **trong trạng thái mù**, rồi mới
> được xem để so. Phơi nhiễm xảy ra **sau khi `M` đã cam kết câu trả lời của mình** ⇒ `D = 0`.
> Và khi ấy `κ` cần một `z` độc lập.

---

## 3. Dự đoán KIỂM ĐƯỢC (chưa kiểm)

1. ~~**`κ` phải tăng khi `z` độc lập hơn.** Test do **model KHÁC** viết phải chọn tốt hơn test tự viết.~~
   > **ĐÃ KIỂM (#157, H81e) — KHÔNG XÁC NHẬN.** Cùng ứng viên, cùng bài, chỉ đổi **người viết test**:
   > `SEL(DeepSeek viết test) − SEL(Qwen viết test)` = **−.0040**, CI95 **[−.0100, +.0000]**, p = .50.
   > Hàng 1 của #90 đòi ≥ +.02; **cận trên CI = +.000 ⇒ loại trừ**.
   > **Giới hạn phải nêu kèm:** pool là **hai mẫu cùng một model**, chỉ **8.6%** số bài có
   > bất đồng (50.4% hai ứng viên **trùng nguyên văn**), nên bộ chọn chỉ có **43 bài** để tạo
   > khác biệt và toàn bộ dư địa là **+.0320**.
   > ⇒ Phát biểu đúng: **trên pool TƯƠNG QUAN CAO, đổi họ của tín hiệu không giúp.**
   > Chưa kiểm được trên pool **đa dạng** — cần thí nghiệm riêng.
2. **`D` phải bằng 0 cho mọi giao thức chỉ-chọn**, kể cả với >2 ứng viên và nguồn hỗn hợp — đã đúng ở k≤8.
   > **ĐÃ KIỂM và ĐÃ BÁC (#142):** dự đoán ngầm rằng *"chặn ghi đè bằng cổng ⇒ `D` → 0"* là **SAI**.
   > `Δ_gate` = +.0040 (p .69) và +.0000 (p 1.00). `D` **không** nằm ở chỗ cổng với tới được.
3. ~~**`H` với ứng viên từ HỌ MODEL KHÁC phải cao hơn** … chưa đo.~~
   > **ĐÃ KIỂM và ĐÃ XÁC NHẬN, tái lập 2/2 (#131 H80, #145 H86c).**
   >
   > | | H80 (11–510) | H86c (511–974, **tách rời**) |
   > |---|---|---|
   > | `H(B) − H(A)` | +.0500 (p 6.2e-4) | **+.0690** (p **9.4e-07**) |
   > | `SEL(B) − SEL(A)` | +.0320 (p 7.0e-3) | **+.0453** (p **4.9e-05**) |
   > | bài hỗn hợp A→B | 57 → 167 | 47 → **176** |
   >
   > **Cơ chế đo được ở TẦNG CHUỖI (#99/#145):** 3 mẫu từ **cùng** model chỉ cho **1.91/3** ứng viên
   > phân biệt, **36.2%** số bài chỉ có **MỘT** ứng viên duy nhất — ở đó mọi giao thức chỉ-CHỌN
   > **bất lực về cấu trúc**. Pool **khác họ**: **2.70/3** ứng viên, chỉ **6.5%** số bài đơn-ứng-viên.
   > ⇒ phần lớn "lỗi tương quan" của mẫu cùng model là dạng mạnh nhất: **trùng nguyên văn**.
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
