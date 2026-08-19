# CẤU TRÚC BÁO CÁO — bản 2 (hợp nhất ba mảng công việc của nhóm)

> **Thay bản 1.** Bản 1 chỉ dựng quanh mảng của Nguyên. Sau khi rà nhánh `duc`, `nguoi3-router`,
> `main` thì thấy hai mảng còn lại **không phải phụ lục** — chúng là **hai chân còn lại của cùng
> một luận điểm**. Cấu trúc dưới đây dựng lại từ đầu theo luận điểm hợp nhất đó.
> **Đích:** báo cáo cuối kỳ NLP, ~20–28 trang kể cả phụ lục. **Ngôn ngữ:** tiếng Việt.

---

## 0. LUẬN ĐIỂM HỢP NHẤT — đọc mục này trước khi viết bất cứ gì

Ba mảng công việc chạy độc lập, thiết kế khác nhau, **và hội tụ về một câu**:

> ### **Chênh lệch năng lực TẠO RA cơ hội; GIAO THỨC quyết định ta thu hoạch hay phá huỷ nó.**

Bằng chứng hai chiều, **ngược dấu nhau và đó chính là điểm hay**:

| | chênh năng lực **tăng** thì… | nguồn |
|---|---|---|
| giao thức **SOÁT/CHỌN** (verifier) | **giá trị TĂNG mạnh**: Solver 1.5B + Verifier 7B = **+14.0đ** trên MATH, **5/5 fold**, 43 sửa / 1 phá. Verifier **cùng cỡ** chỉ +3.0đ, khoảng **chạm 0** | mảng nhóm (`RESULTS.md` §1a) |
| giao thức **SỬA** (repair) | **giá trị GIẢM**: `Δ_ceil = +.0218 − .2392·chênh`, p = **1e-05**; đổi dấu tại `g*` = **.091** | mảng Nguyên (H97) |

**Cùng một biến (chênh năng lực), hai dấu ngược nhau, khác nhau ở đúng một thứ: giao thức.**
Và ta **đo được** tại sao — bằng đẳng thức phân rã:

```
Δ_ceil = A − B + C        B = P(¬S ∧ I đúng ∧ V sai) = thiệt hại do SỬA
```
Giao thức **CHỌN** đặt `B = 0` **theo cấu trúc**. Giao thức **SỬA** trả `B` **theo cấu trúc**.
Và `B` đến từ đâu thì đã đo, đăng ký trước, tái lập hai miền: **nhìn thấy nội dung SAI**
(MATH: **−.2720**; model mạnh rơi **46.4% → 19.2%**).

**⇒ Đó là toàn bộ báo cáo.** Mọi mục §5 chỉ là chứng minh một mảnh của câu trên.

---

## 1. Mở đầu / Động cơ *(~2 trang)*

**Câu hỏi thực tế:** thêm một tác tử LLM nữa vào hệ có đáng không? Nếu có thì **giá trị đến từ đâu** —
từ việc **thêm vai**, hay từ **thứ khác**?

**Ba cách hỏi mà nhóm đã dùng** (giới thiệu ngay, đây là bố cục của báo cáo):
1. **Theo VAI** — vai nào trong pipeline `P→S→V→A` thực sự trả tiền? *(Shapley credit — Đức)*
2. **Theo CHI PHÍ** — phối hợp có đáng compute không, và khi nào? *(router — Tùng Dương)*
3. **Theo LUỒNG THÔNG TIN** — chuyện gì xảy ra khi một tác tử **nhìn thấy** sản phẩm của tác tử khác? *(Nguyên)*

**Phát hiện về mốc so sánh** (giữ nguyên từ bản 1, vẫn là hook mạnh): gần như mọi công trình đo
`V − S` (so với model **yếu**). Mốc mà người triển khai đối mặt là `V − I` (so với model **mạnh**
chạy một mình). **Dấu đảo ngược.**

**Đóng góp** — 5 gạch đầu dòng:
1. Khung `value = H(pool) × κ(z) − D(protocol)` gộp được cả ba cách hỏi.
2. **Bất đối xứng năng lực** là biến quyết định, **không** phải số lượng vai *(5/5 fold)*.
3. **Đẳng thức chính xác** `Δ_ceil = A − B + C` tách cơ hội khỏi thiệt hại.
4. Bằng chứng **đăng ký trước, hai miền**: `D` là hình phạt của việc thấy **nội dung SAI**.
5. Giải được **nghịch lý biểu kiến**: cùng biến chênh năng lực, SOÁT thắng lớn còn SỬA thua.

---

## 2. Công trình liên quan *(~2 trang)* — **PHẦN LỚN ĐÃ CÓ**

Nguồn sẵn: `docs/RELATED_BASELINES.md` (102 dòng, Đức) + `docs/RELATED_PIPELINE.md` (77 dòng, Đức).
- **Debate thua self-consistency ở 3/4 ô công bố**; sụp **16 điểm** với Llama3.1-8B trên GSM8K
  → **độc lập trùng hướng** với kết luận "CHỌN thắng SỬA" của ta.
- Định vị so với **MAS_RPSV** (gần nhất: 4 vai nối tiếp, cùng cỡ model, cùng benchmark) và **SHARP**
  (cùng dùng Shapley credit).
- **Việc còn thiếu:** dòng *sinh-rồi-sửa* — Self-Refine, Reflexion, CRITIC — và với **mỗi bài, ghi
  rõ nó đo so với mốc nào**. Đây là chỗ luận điểm §1 đứng hoặc đổ.

---

## 3. Khung *(~2.5 trang — LÕI)*

### 3.1 Phân rã giá trị
```
value = H(pool) × κ(z) − D(protocol)
```
`H` **dư địa** — pool có chứa cái `I` một mình không có? ·
`κ` **bộ chọn khả thi** — có lấy ra được không? · `D` **thiệt hại** — giao thức phá bao nhiêu?

### 3.2 Ba mảng = ba số hạng  ← **chỗ hợp nhất báo cáo**
| mảng | đo số hạng nào | công cụ |
|---|---|---|
| Shapley theo vai *(Đức)* | **`H`** — đóng góp biên của từng vai | giá trị Shapley trên `P/S/V/A` |
| Router hiệu quả *(Tùng Dương)* | **`κ`** — tín hiệu khả thi có rẻ không | consensus router, accuracy-vs-cost |
| Sửa vs Chọn *(Nguyên)* | **`D`** — phơi nhiễm phá bao nhiêu | phân rã `A/B/C`, phân tầng phơi nhiễm |

### 3.3 Đẳng thức phân rã
`CEIL = S ∨ (¬S ∧ V)`, và
```
Δ_ceil = acc(CEIL) − acc(I) = A − B + C
A = P(S đúng ∧ I sai)         cơ hội
B = P(¬S ∧ I đúng ∧ V sai)    SỬA phá bài I vốn làm đúng
C = P(¬S ∧ ¬I ∧ V đúng)       SỬA cứu bài cả hai đều sai
```
**Đẳng thức đại số, không phải mô hình** — khớp tuyệt đối **4/4** cặp có trace và **15/15** cặp ở H97.
`A` là tính chất **cặp model**; `B` là tính chất **giao thức**. → đây là công cụ giải nghịch lý §6.

### 3.4 Ba mệnh đề
**M1** phơi nhiễm phá giá trị *(bản cuối §5.4)* · **M2** tín hiệu **độc lập** thắng tín hiệu
**tương quan** · **M3** định tuyến tiết kiệm ở chỗ **ít cần nhất**.

---

## 4. Thiết lập chung *(~2 trang)*

Model (Qwen2.5 1.5B/7B/14B/32B, Llama-3.1-8B, DeepSeek-Coder-6.7B) · benchmark (GSM8K, MATH-500,
MBPP 11–510 và 511–974, HumanEval) · vai `P/S/V/A` · đại lượng (`Δ_ceil`, `Δ_honest`, `V_gain`,
`A_gain`, cost/Q) · **hai chuẩn kiểm chứng của nhóm** — xem §7.

---

## 5. Kết quả *(~8 trang)*

### 5.1 `H` — **bất đối xứng năng lực**, không phải số lượng vai  ⟵ *mảng nhóm*
- Solver 1.5B + Verifier 7B: **+14.0đ** MATH, khoảng **[+8.3, +20.0]**, **5/5 fold**, 43 sửa / 1 phá
- Verifier **cùng cỡ**: chỉ **+3.0đ**, khoảng **chạm 0** ⇒ **vô giá trị**
- Riêng phần do verifier mạnh hơn (V7 − V15): **+11.0đ [+3.3, +16.7]**, 5/5
> **Giá trị nằm ở CHÊNH LỆCH NĂNG LỰC, không ở việc có thêm một vai.**

### 5.2 `H` — cùng kết luận, đo bằng thiết kế hoàn toàn khác  ⟵ *mảng Nguyên*
- 15 cặp có hướng, **cùng 499 bài**, một lần chạy: `A ~ β₀ + β₁·chênh + β₂·khác_họ`
- **β₁ = −.1922** (p ≈ 0); **β₂ = +.0045**, KTC **[−.005, +.014]** ⇒ **null CÓ THÔNG TIN**
- `R²` chỉ với chênh = **.824**
> **Hai mảng, hai thiết kế, một kết luận: chênh năng lực là biến; kiến trúc/họ model thì không.**

### 5.3 `κ` — phối hợp có đáng compute không  ⟵ *mảng Tùng Dương*
| chiến lược | GSM8K acc | cost/Q | MATH acc | cost/Q |
|---|---|---|---|---|
| Solver một mình | .6733 | 1 | .4133 | 1 |
| Pipeline đầy đủ | .7233 | 3 | .3733 | 3 |
| **Consensus Router** | **.7200** | **2.32** | .4133 | 2.40 |
- GSM8K: **gần bằng độ chính xác với 77% chi phí**
- MATH: router = **đúng bằng Solver một mình** ⇒ **vô dụng**
- Cơ chế: khi `S`,`V` bất đồng, `A` cứu được **45.4%** (GSM8K) so với **25.0%** (MATH)
> **M3 được xác nhận:** định tuyến chỉ trả tiền ở nơi **đã** có đồng thuận — tức nơi **ít cần nhất**.

### 5.4 `D` — hình phạt của việc thấy thứ **SAI**  ⟵ *kết quả mạnh nhất, đăng ký trước*
| | MBPP 11–510 | MBPP 511–974 | **MATH-500** |
|---|---|---|---|
| artifact **SAI** | −.1900 | −.1927 | **−.2720** (p ≈ 0) |
| artifact **ĐÚNG** | +.0636 | +.0245 | **+.0377** (p .012) |

MATH: model mạnh **46.4% → 19.2%**; gộp trọng số tái tạo chính xác `V − I` = **−.1240**.

### 5.5 `D` trả lời `Δ_ceil` theo chênh năng lực
- `Δ_ceil = +.0218 − .2392·chênh`, `R²` = .60, p = **1e-05**, `g*` = **.0913**
- ⚠️ **0/15** dương có ý nghĩa · **3/15** âm có ý nghĩa ⇒ **chỉ phát biểu chiều PHỦ ĐỊNH**
- Lực: xác lập vùng dương cần **~8× toàn bộ MBPP** ⇒ **bất khả thi trên benchmark này**

### 5.6 Trần của định tuyến phơi nhiễm
`I` = .6980 · `V` = .5740 (−.1240) · **cổng ORACLE = .7160 (+.0180)**; bộ phân loại cần **~89%**
mới hoà vốn ⇒ **kết luận là "mặc định đừng cho xem"**, không phải "làm cổng tốt hơn".

### 5.7 `M2` — pool khác **MODEL** cho nhiều ứng viên phân biệt hơn
1.91/3 → **2.70/3** ứng viên; **36.2%** → **6.5%** số bài chỉ có một ứng viên.
⚠️ ghi **"khác MODEL"**, không phải "khác họ".

---

## 6. Tổng hợp: giải **nghịch lý biểu kiến** *(~2 trang — ĐIỂM CAO NHẤT CỦA BÁO CÁO)*

**Nghịch lý:** §5.1 nói chênh năng lực lớn ⇒ **+14.0đ**. §5.5 nói chênh năng lực lớn ⇒ `Δ_ceil` **âm**.

**Giải:** hai bên dùng **hai giao thức khác nhau**, và đẳng thức §3.3 tách được:
- Verifier ở §5.1 là giao thức **SOÁT/CHỌN** → **43 sửa / 1 phá** ⇒ `B ≈ 0`
- `V` ở §5.5 là giao thức **SỬA/GHI ĐÈ** → trả `B` theo cấu trúc, và `B` **tăng theo chênh**

**Chênh năng lực làm tăng `A` lẫn `B`.** Ai thắng là do giao thức:
```
CHỌN:  value ≈ A × κ − 0        → chênh tăng thì THẮNG
SỬA:   value ≈ A − B + C        → B tăng nhanh hơn ⇒ chênh tăng thì THUA
```
Bốn mảnh chứng cứ độc lập cho cùng kết luận:
1. **Đại số** — CHỌN đặt `B = 0` theo cấu trúc.
2. **Cỡ** — MATH: `A` = .016 vs `B` = .176 (**gấp 11 lần**).
3. **Xu hướng** — ngưỡng phải vượt (`r*_C`) tăng theo chênh **nhanh gấp đôi** khả năng bảo toàn (`ρ`):
   độ dốc **2.177 vs 1.101**, p = .0066.
4. **Trần** — cổng phơi nhiễm **hoàn hảo** cũng chỉ cứu **+.018** trên nền **−.124**.
5. **Ngoại chứng** — literature: debate thua self-consistency **3/4 ô**, sụp **16đ** ở model nhỏ.

> ### KHUYẾN NGHỊ THỰC DỤNG (đặt vào abstract và kết luận)
> **Dùng model nhỏ để GIẢI, model lớn để SOÁT — và đừng cho model lớn xem bài làm của model nhỏ
> khi mục đích là để nó SỬA.** Chênh năng lực là thứ tạo ra giá trị; giao thức CHỌN thu hoạch nó,
> giao thức SỬA phá nó.

---

## 7. Phương pháp luận *(~2 trang — ĐÓNG GÓP RIÊNG)*

**Nhóm dùng HAI chuẩn kiểm chứng bổ sung cho nhau — nói rõ cả hai, đừng giấu:**

| chuẩn | dùng ở | cách chống tự lừa |
|---|---|---|
| **Thanh sai số bằng fold** | mảng nhóm | 5 fold rời nhau; **ngưỡng nhiễu 2σ ≈ 5 điểm**; hiệu ứng < 5đ đo một lần **không** tính là bằng chứng |
| **Đăng ký trước + cổng + niêm phong** | mảng Nguyên | bảng khoá commit **trước** khi chạy, có **hàng giết giả thuyết**; hash artifact **trước** khi đọc; **VOID** thì không đọc số |

Con số nên nêu:
- Sàn nhiễu: cùng cấu hình, 5 fold ⇒ `V_gain` từ **+1.0** đến **+8.0** ⇒ ngưỡng **5 điểm**
- **16/31** lần chạy đã niêm phong là **VOID (52%)** — **tính năng, không phải lỗi**
- Sổ tiên nghiệm công khai: **21/42**
- **Greedy tất định**: hai tài khoản, hai ngày, cùng phần cứng ⇒ **499/499 giống hệt từng bài**
  ⇒ **"chạy lại y nguyên" KHÔNG phải xác nhận độc lập**
- So chéo lần chạy hợp lệ ⇔ trùng **(máy + độ chính xác)** VÀ trùng **bộ bài**

> **Bài học chung của cả hai chuẩn:** phần lớn "cải thiện" ban đầu **không sống sót** qua kiểm chứng.
> Đó là kết quả, không phải thất bại.

---

## 8. Hạn chế *(~1 trang — VIẾT THẬT)*

1. Hai mảng dùng hai chuẩn khác nhau; **chưa** kiểm chéo lẫn nhau
2. Chủ yếu **greedy** ⇒ không có phương sai lấy mẫu ở mảng Nguyên (mảng nhóm có fold)
3. Pool model bị **VRAM tầng miễn phí** giới hạn (Llama-8B, Qwen-14B không lượng tử hoá được)
4. Vùng **dương** của luật chênh **chưa xác lập** và **không thể** xác lập trên MBPP
5. **`κ` chưa giải được** — chưa tìm được tín hiệu khả thi nào ở mảng Nguyên
6. Đang chạy: **H100e** (`Δ_honest` cho giao thức độc-lập-trước), **H99b** (luật chênh trên toán)

---

## 9. Kết luận *(~0.5 trang)*

---

## Phụ lục
**A.** Đăng ký trước được trích · **B.** Niêm phong hash · **C.** 16 lần VOID và lý do ·
**D.** Sổ tiên nghiệm 21/42 · **E.** 37 luật quy trình · **F.** Bảng kết quả đầy đủ của mảng nhóm
(`RESULTS.md`) · **G.** Shapley theo vai (`docs/` của Đức, 30 tệp)

---

## Hình cần vẽ

| # | hình | nguồn | ai |
|---|---|---|---|
| 1 | Sơ đồ khung `H × κ − D` **+ ba mảng ứng với ba số hạng** | vẽ tay | Nguyên |
| 2 | **Nghịch lý**: chênh↑ ⇒ verifier thắng / sửa thua (hai đường ngược nhau) | `RESULTS.md` + `results_H97` | Nguyên |
| 3 | `Δ_ceil` theo chênh, 15 điểm + đường khớp + `g*` | `results_H97` | bạn |
| 4 | **Phơi nhiễm 2×2** (đúng/sai × thấy/không) | `results_H94d` | bạn |
| 5 | Accuracy-vs-cost, có điểm router | `EFFICIENCY.md` | Tùng Dương |
| 6 | Bất đối xứng năng lực: verifier cùng cỡ vs lớn hơn, có thanh sai số | `RESULTS.md` §1a | Đức |
| 7 | Trần định tuyến: độ chính xác bộ phân loại → lợi ích ròng | `results_H94d` | bạn |

**Hình 2 là hình quan trọng nhất của báo cáo** — nó *là* luận điểm. Nếu chỉ kịp ba hình:
**2, 4, 6**.
