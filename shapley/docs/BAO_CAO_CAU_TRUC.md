# CẤU TRÚC BÁO CÁO — "Sửa hay Chọn?"

> **Trạng thái:** khung + phân công. Số liệu đã chốt; phần viết còn trống.
> **Đích:** báo cáo cuối kỳ môn NLP. Ước ~18–25 trang kể cả phụ lục.
> **Ngôn ngữ:** tiếng Việt (mọi tài liệu nguồn đều tiếng Việt). Nếu cần nộp tiếng Anh thì dịch
> **sau khi** chốt nội dung — đừng dịch song song, sẽ lệch số.

---

## 0. Tên và một câu chốt

**Tên đề xuất:** *Sửa hay Chọn? Đo lại lợi ích của kiến trúc đa tác tử LLM bằng đúng mốc so sánh*

**Một câu:** Các hệ đa tác tử LLM thường báo cáo cải thiện so với **model yếu**; khi đo lại so với
**model mạnh chạy một mình** — mốc mà người triển khai thực sự đối mặt — dấu của hiệu ứng **đảo ngược**,
và chúng tôi truy được nguyên nhân về một đại lượng đo được: **thiệt hại do nhìn thấy nội dung sai**.

---

## 1. Mở đầu / Động cơ  *(~2 trang)*

**Vấn đề đặt ra.** Self-Refine, Reflexion, debate, LLM-as-judge, agentic pipelines: tất cả đều
dựng một model **sửa** hoặc **đánh giá** sản phẩm của một model khác. Gần như mọi báo cáo đo
cải thiện theo `V − S` (so với model **yếu** một mình).

**Nhưng người triển khai không đứng trước lựa chọn đó.** Nếu pipeline đã có model mạnh `I` bên trong,
thì lựa chọn thật là: *chạy pipeline*, hay *gọi thẳng `I`*? Đại lượng đúng là **`V − I`**.

**Phát hiện trung tâm về phương pháp:** `V − I` **đổi dấu** so với `V − S`.
→ Đây là "hook" của báo cáo. Đặt ngay trang 1, kèm một hình.

**Đóng góp** (liệt kê 4 gạch đầu dòng):
1. Một khung phân rã giá trị: `value = H(pool) × κ(z) − D(protocol)`.
2. Một **đẳng thức chính xác** phân rã trần lợi ích thành ba số hạng đo được (`A − B + C`).
3. Bằng chứng **đăng ký trước** rằng `D` là hình phạt của việc thấy nội dung **SAI**, không phải của
   việc **thấy** — tái lập trên hai miền (code, toán).
4. Một **luật quyết định** dùng được, và giới hạn trung thực của nó.

---

## 2. Nền tảng & công trình liên quan  *(~2 trang)*

- **Sinh–rồi–sửa**: Self-Refine, Reflexion, CRITIC. Nêu rõ mốc so sánh mà mỗi bài dùng.
- **Sinh–rồi–chọn**: self-consistency, best-of-n, reranking bằng test.
- **Đa tác tử**: debate, hội đồng, phân rã vai.
- **Vấn đề mốc so sánh**: đây là chỗ đặt luận điểm — *rất ít công trình báo cáo `V − I`*.
- **Benchmark**: MBPP (`task_id` 11–510 chính, 511–974 tách rời), MATH-500.

> ⚠️ Phần này **chưa có ai viết**. Cần đọc và trích thật, **không** bịa số của bài khác.

---

## 3. Khung  *(~2 trang — LÕI LÝ THUYẾT)*

### 3.1 Phân rã giá trị
```
value  =  H(pool) × κ(z)  −  D(protocol)
```
- **`H`** — **dư địa**: pool ứng viên có chứa lời giải đúng mà `I` một mình không có không?
- **`κ`** — **chất lượng bộ chọn**: một tín hiệu **khả thi** (không phải oracle) có lấy được nó không?
- **`D`** — **thiệt hại**: bản thân giao thức phá đi bao nhiêu?

### 3.2 Ba mệnh đề
- **M1** — Giao thức cho `M` **nhìn thấy** artifact thì mất giá trị. *(bản cuối ở §5.3)*
- **M2** — Tín hiệu **độc lập** thắng tín hiệu **tương quan**, không phải "tín hiệu mạnh hơn".
- **M3** — Định tuyến tiết kiệm ở đúng chỗ **ít cần tiết kiệm nhất**.

### 3.3 Đẳng thức phân rã  ← **viên gạch nối toàn bộ phần kết quả**
Với `S` yếu, `I` mạnh, `V` = `I` sửa artifact của `S`, và trần oracle
`CEIL = S ∨ (¬S ∧ V)`:

```
Δ_ceil  =  acc(CEIL) − acc(I)  =  A − B + C

A = P(S đúng ∧ I sai)          dư địa
B = P(¬S ∧ I đúng ∧ V sai)     V PHÁ bài I vốn làm đúng
C = P(¬S ∧ ¬I ∧ V đúng)        V CỨU bài cả hai đều sai
```
**Đây là đẳng thức đại số, không phải mô hình** — kiểm số trên **4/4** cặp có trace, khớp tuyệt đối.
`A` là tính chất của **cặp model**; `B` là tính chất của **giao thức**. Mọi kết quả sau đều là câu
trả lời cho *"số hạng nào đang giết chúng ta?"*

---

## 4. Thiết lập thực nghiệm  *(~2 trang)*

Model · benchmark · giao thức (`S`, `I`, `V`, `CEIL`, `G_V`, các biến thể lời nhắc R0/R1/R2) ·
đại lượng (`Δ_ceil`, `Δ_honest`, `Δ_gate`, `Δ_cont`) · kiểm định (McNemar chính xác ghép cặp,
bootstrap ghép cặp theo chỉ số bài) · **cổng chất lượng** và vì sao chúng tồn tại.

> Bảng model + dung lượng VRAM đo được: lấy từ `deploy/preflight.py` (`DO_DUOC_GB`).

---

## 5. Kết quả  *(~7 trang — PHẦN CHÍNH)*

### 5.1 Dấu đảo ngược — đặt vấn đề bằng số
`V − S` dương ⟷ `V − I` âm. Nêu ngay, rồi dùng đẳng thức §3.3 để hỏi "tại sao".

### 5.2 `H`: dư địa do **chênh năng lực** quyết định, **không** phải "khác họ"
- 6 model · 15 cặp có hướng · **cùng 499 bài** · một lần chạy *(H96)*
- `A ~ β₀ + β₁·chênh + β₂·khác_họ` ⇒ **β₁ = −.192 (p ≈ 0)**, **β₂ = +.0045, KTC 95% [−.005, +.014]**
- `R²` chỉ với chênh = **.824**; thêm biến họ được **+.014**
- **Null CÓ THÔNG TIN**: KTC nằm trọn dưới ngưỡng +.02 đã đăng ký trước
- Thô thì khác họ *trông* cao hơn (.0597 vs .0481) **nhưng** cặp khác họ có chênh nhỏ hơn
  (.130 vs .167), tương quan (chênh, `A`) = **−.908** ⇒ **tương quan giả**

### 5.3 `D`: hình phạt của việc thấy thứ **SAI**  ← **KẾT QUẢ MẠNH NHẤT**
Phân rã phơi nhiễm theo **nội dung** artifact, **đăng ký trước**, xác nhận trên **miền mới** *(H94d)*:

| | MBPP 11–510 | MBPP 511–974 | **MATH-500 (đăng ký trước)** |
|---|---|---|---|
| artifact **SAI** | −.1900 | −.1927 | **−.2720** (p ≈ 0) |
| artifact **ĐÚNG** | +.0636 | +.0245 | **+.0377** (p .012) |

Trên toán: model mạnh rơi **46.4% → 19.2%** trên đúng những bài nó vốn làm được gần một nửa.
Gộp hai tầng theo trọng số tái tạo **chính xác** `V − I` = −.1240.

### 5.4 `Δ_ceil` theo chênh năng lực — và **giới hạn trung thực**
- 15 cặp, một lần chạy *(H97)*: `Δ_ceil ≈ +.0218 − .2392·chênh`, `R²` = .60, p = 1e-05, **`g*` = .0913**
- ⚠️ **0/15 cặp dương có ý nghĩa**; **3/15 âm có ý nghĩa** (đều ở chênh ≥ .218)
- ⇒ chỉ phát biểu chiều **PHỦ ĐỊNH**: **chênh > .09 thì đừng sửa**
- Tính lực: xác lập vùng dương cần **~8× toàn bộ MBPP** ⇒ **không thể** trên benchmark này

### 5.5 `κ`: nút thắt, và **trần** của định tuyến
- Hai lần thử tín hiệu cổng khả thi đều **bị chặn** (pool suy biến; độ phủ tín hiệu .699)
- **Trần của cổng phơi nhiễm ORACLE = +.0180** so với `I`; bộ phân loại cần **~89%** mới hoà vốn
- ⇒ kết luận **không** phải "làm cổng tốt hơn" mà **"mặc định đừng cho xem"**

### 5.6 `M2`: pool **khác model** cho nhiều ứng viên phân biệt hơn
3 mẫu cùng model ⇒ **1.91/3** ứng viên phân biệt, **36.2%** số bài chỉ có **một**;
pool khác model ⇒ **2.70/3**, chỉ **6.5%**.
> ⚠️ Ghi **"khác MODEL"**, không phải "khác họ" — đối chứng khác-model-cùng-họ **chưa chạy**.

---

## 6. Tổng hợp: vì sao **CHỌN** thắng **SỬA**  *(~1.5 trang — CHỖ ĐỂ LẠI ẤN TƯỢNG)*

Bốn mảnh độc lập chỉ về **cùng một** kết luận:

1. **Đại số** — `Δ_ceil = A − B + C`. Giao thức **SỬA** trả `B` **theo cấu trúc**;
   giao thức **CHỈ-CHỌN** đặt `B = 0` **theo cấu trúc**.
2. **Cỡ** — `B` lớn hơn `A` rất nhiều ở chênh lớn (MATH: `A` = .016 vs `B` = .176, **gấp 11 lần**).
3. **Xu hướng** — ngưỡng `V` phải vượt (`r*_C`) tăng theo chênh **nhanh gấp đôi** khả năng bảo toàn
   thực tế của nó (`ρ`): độ dốc **2.177 vs 1.101**, chênh lệch p = .0066.
4. **Trần** — kể cả cổng phơi nhiễm **hoàn hảo** cũng chỉ cứu về **+.018** trên nền thiệt hại **−.124**.

> **Câu chốt của báo cáo:** *"Đừng cho model mạnh xem bài làm của model yếu. Hãy sinh độc lập rồi chọn."*

---

## 7. Phương pháp luận  *(~2 trang — ĐÓNG GÓP RIÊNG, ĐỪNG BỎ)*

Với một môn NLP, phần này **có giá trị ngang phần kết quả**:

- **Đăng ký trước có bảng khoá diễn giải**, gồm **một hàng giết giả thuyết**, commit **trước** khi chạy
- **Niêm phong hash** artifact **trước** khi đọc số (git chứng minh sửa đổi có trước lúc *viết*,
  **không** chứng minh có trước lúc *đọc* — hash thì có)
- **16/31 lần chạy đã niêm phong là VOID (52%)** — và đó là **tính năng**, không phải lỗi
- **Greedy tất định** ⇒ hai tài khoản, hai ngày, cùng phần cứng ⇒ **499/499 giống hệt từng bài**
  ⇒ **"chạy lại y nguyên" KHÔNG phải xác nhận độc lập**
- **Sổ tiên nghiệm công khai: 21/42** — mỗi đăng ký trước ghi xác suất cho từng hàng **trước** khi chạy
- **So chéo lần chạy hợp lệ ⇔ trùng (máy + độ chính xác) VÀ trùng bộ bài** — hai confound riêng biệt

---

## 8. Hạn chế  *(~1 trang — VIẾT THẬT, ĐỪNG LÀM ĐẸP)*

1. Chủ yếu **MBPP**; MATH mới có phân rã phơi nhiễm, phần `Δ_ceil` trên MATH **chưa xong**
2. **Chỉ greedy** ⇒ không có phương sai lấy mẫu ⇒ mỗi cấu hình là **một điểm**
3. Pool model bị **VRAM tầng miễn phí** giới hạn (Llama-8B, Qwen-14B không lượng tử hoá được)
4. Vùng **dương** của luật chênh **chưa xác lập** và **không thể** xác lập trên MBPP (thiếu lực)
5. **`κ` chưa giải được** — chưa tìm được tín hiệu khả thi nào
6. `Δ_honest` cho giao thức **độc lập-trước** vẫn **đang chạy** *(H100e)*

---

## 9. Kết luận  *(~0.5 trang)*

---

## Phụ lục
- **A.** Toàn văn các đăng ký trước được trích *(từ `PREREGISTRATION.md`)*
- **B.** Bảng niêm phong hash *(`RESULT_SEALS.md`)*
- **C.** Danh sách VOID và lý do — bảng 16 dòng
- **D.** Sổ tiên nghiệm 21/42
- **E.** Nhật ký quy trình: 37 luật rút ra từ thất bại *(`QUY_TRINH_VONG_LAP.md`)*

---

## Hình cần vẽ

| # | Hình | Nguồn dữ liệu |
|---|---|---|
| 1 | Sơ đồ khung `H × κ − D` | vẽ tay |
| 2 | **Dấu đảo ngược**: `V−S` so với `V−I` | `results_H88d`, `results_H88f` |
| 3 | `Δ_ceil` theo chênh, 15 điểm + đường khớp + `g*` | `results_H97/res_H97.json` |
| 4 | Phân rã `A`/`B`/`C` xếp chồng theo cặp | `results_H97` |
| 5 | **Phơi nhiễm 2×2** (đúng/sai × thấy/không) | `results_H94d/res_H94d.json` |
| 6 | `ρ` và `r*_C` — hai đường cắt nhau | `results_H97` |
| 7 | Trần định tuyến: độ chính xác bộ phân loại → lợi ích ròng | `results_H94d` |

**Hình 5 và Hình 3 là hai hình quan trọng nhất.** Nếu chỉ kịp vẽ hai hình thì vẽ hai hình đó.
