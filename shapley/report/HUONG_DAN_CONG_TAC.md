# HƯỚNG DẪN CHO NGƯỜI CÙNG LÀM BÁO CÁO

> **Ba tệp, ba việc:** `BAO_CAO_CAU_TRUC.md` = *viết cái gì* · tệp này = *được phép viết số nào* ·
> `QUY_TRINH_VIET_BAO_CAO.md` = *làm theo thứ tự nào*. Bắt đầu ở **§0 `BAO_CAO_CAU_TRUC.md`**.
>
> Đọc hết mục **1** và **2** trước khi viết bất cứ dòng nào. Hai mục đó quyết định con số nào
> được phép xuất hiện trong báo cáo. Phần còn lại tra khi cần.

---

## 1. Ba tầng bằng chứng — **quy tắc bất di bất dịch**

Mỗi con số trong dự án thuộc **đúng một** tầng. Tầng quyết định nó được viết như thế nào.

| tầng | nghĩa | được viết ở đâu | cách diễn đạt |
|---|---|---|---|
| **A — XÁC NHẬN** | có đăng ký trước, bảng khoá commit **trước** khi chạy, **mọi cổng đạt** | thân báo cáo, có thể in đậm | *"chúng tôi đo được X"* |
| **B — THĂM DÒ** | phân tích hậu nghiệm, hoặc không có đăng ký trước | thân báo cáo **có nhãn**, hoặc phụ lục | *"quan sát mô tả, chưa xác nhận"* |
| **C — VOID** | có ít nhất một cổng chất lượng **trượt** | **chỉ** ở phụ lục C, dạng danh sách | *"không đọc số"* — **tuyệt đối không trích giá trị** |

### Vì sao nghiêm đến vậy
Dự án **đã từng vi phạm** ở các vòng #114 / #121 / #123: đọc số từ lần chạy VOID, và một lần
tạo ra **kết quả tái lập giả**. Kiểm định #125 bắt được. Toàn bộ kỷ luật này sinh ra từ đó.
**Nếu bạn thấy một con số hay ho nhưng không rõ tầng nào — hỏi trước khi viết.**

### Cái bẫy phải biết (nếu không sẽ mắc)
Hai lần chạy **H88e** và **H92b** có `res_*.json` ghi `VOID: ["n>=480"]` **nhưng vẫn HỢP LỆ**.
Lý do: dải giữ lại của MBPP (`task_id` 511–974) **chỉ có 464 bài**, nên cổng `n ≥ 480` là
**bất khả thi về mặt vật lý**. Đăng ký trước đã được sửa thành **`n ≥ 460`** cho dải đó, và
sửa đổi ấy **commit TRƯỚC khi đọc số** (xem `#97-d` và `#102-b`, kiểm bằng `git log`).
Kernel vẫn cứng `n ≥ 480` nên trường `VOID` trong file bị **lỗi thời**.
⇒ **Cả hai thuộc tầng A.** Đừng loại chúng, và cũng đừng loại *chỉ vì* file ghi VOID —
**hãy đọc đăng ký trước tương ứng**.

---

## 2. Bảng số CHỐT — được phép trích thẳng

Mọi con số dưới đây là **tầng A** trừ khi ghi khác. Copy chính xác, đừng làm tròn lại.

### 2.1 `D` — thiệt hại do phơi nhiễm  *(kết quả mạnh nhất)*
| | MBPP 11–510 | MBPP 511–974 | MATH-500 |
|---|---|---|---|
| artifact **SAI** | −.1900 | −.1927 | **−.2720** (p ≈ 0) |
| artifact **ĐÚNG** | +.0636 | +.0245 | **+.0377** (p .012) |

MATH: `n` = 500 (239 đúng / 261 sai); model mạnh **46.4% → 19.2%** ở tầng SAI.
Gộp trọng số = `V − I` = **−.1240** (khớp chính xác).
*Nguồn: `results_H94d/res_H94d.json` → khoá `strat`. Cột MBPP: `results_H92`, `H92b`.*

### 2.2 `H` — dư địa theo chênh năng lực
`A = β₀ + β₁·chênh + β₂·khác_họ`, 15 cặp, cùng 499 bài:
- **β₁ = −.1922** (se .0260, p ≈ 0)
- **β₂ = +.00446** (se .0044, p = .33), **KTC 95% [−.0051, +.0140]**
- `R²` chỉ chênh = **.8237**; thêm biến họ = .8377
*Nguồn: `results_H96/res_H96.json` → `ols`, `pairs`.*

### 2.3 Luật `Δ_ceil`
`Δ_ceil = +.02184 − .23922·chênh`, `R²` = **.5998**, p(δ₁) = **1e-05**, **`g*` = .0913**
- **0/15** cặp dương có ý nghĩa · **3/15** âm có ý nghĩa
- **Chỉ được phát biểu chiều phủ định:** *chênh > .09 thì đừng sửa*
*Nguồn: `results_H97/res_H97.json` → `ols_ceil`, `pairs`.*

**Luật này CHUYỂN sang MATH** *(H99b, #112, mọi cổng đạt, 3/3 cặp)*: **2/3** dự báo nằm trong KTC 95%
— 7B→14B đo −.0140, KTC [−.046, +.018], dự báo **+.0108**; 1.5B→14B đo −.0680, KTC [−.102, −.034],
dự báo **−.0471**. Cặp lệch: 1.5B→7B đo **−.1660** so với dự báo −.0361 (`B` = .208).
⚠️ **Viết là "không bác được luật"; ĐỪNG viết "đã xác nhận luật"** — KTC rộng .064–.084.
*Nguồn: `results_H99b/res_H99b.json` → `pairs`.*

### 2.4 Đẳng thức phân rã
`Δ_ceil = A − B + C`, khớp **tuyệt đối 4/4** cặp có trace và **15/15** cặp trong H97.

### 2.5 Trần định tuyến  *(tầng B — dẫn xuất mô tả từ dữ liệu tầng A)*
`I` = .6980 · `V` = .5740 (−.1240) · **cổng ORACLE = .7160 (+.0180)**
Bộ phân loại cần **~89%** mới hoà vốn (.90 ⇒ +.0020; .85 ⇒ −.0060).

### 2.6 `M2` — đa dạng ứng viên
3 mẫu cùng model ⇒ **1.91/3** ứng viên phân biệt, **36.2%** bài chỉ có một.
Pool khác model ⇒ **2.70/3**, **6.5%**.
⚠️ **Viết là "khác MODEL"**, không phải "khác họ" — đối chứng khác-model-**cùng**-họ chưa chạy.

### 2.7 Số về phương pháp
- **31** lần chạy đã niêm phong, **16 VOID** (**52%**)
- Sổ tiên nghiệm: **21/42**
- Tất định: **499/499** giống hệt từng bài, hai tài khoản, hai ngày, cùng T4/nf4

---

## 3. Những điều **KHÔNG** được viết

| đừng viết | viết thế này |
|---|---|
| *"khác họ model cho nhiều dư địa hơn"* | *"chênh năng lực nhỏ cho nhiều dư địa hơn"* — nhãn họ đã bị **rút** ở #182 |
| *"chênh nhỏ thì sửa THẮNG"* | *"chênh > .09 thì đừng sửa"* — chiều khẳng định **chưa xác lập** |
| *"cổng định tuyến là lời giải"* | *"trần của định tuyến chỉ +.018; mặc định là đừng cho xem"* |
| *"chúng tôi tái lập bằng cách chạy lại"* | greedy **tất định** ⇒ chạy lại **không** phải bằng chứng độc lập |
| bất kỳ số nào từ **H98, H99, H95b, H94c, H91b/c/d, H88/H88b, H89b/d/e/f/h** | **VOID** — chỉ được nhắc trong phụ lục C |
| *"pool khác họ"* ở phần M2 | *"pool khác MODEL"* |

---

## 4. Phân công đề xuất

| phần | ai | vì sao |
|---|---|---|
| **§2 Công trình liên quan** | **Đức** (đã có sẵn phần lớn) | ⚠️ **SỬA:** phần này **KHÔNG** trống. Đức đã viết `../docs/RELATED_BASELINES.md` (102 dòng, có số công bố của debate/self-consistency trên GSM8K+MATH) và `../docs/RELATED_PIPELINE.md` (77 dòng, định vị so với MAS_RPSV / SHARP). **Việc còn lại:** bổ sung dòng *sinh-rồi-sửa* (Self-Refine / Reflexion / CRITIC) và **ghi rõ mỗi bài dùng mốc so sánh nào** — đó là chỗ luận điểm của báo cáo đứng hoặc đổ. |
| **§4 Thiết lập** | bạn của Nguyên | Cơ học: model, benchmark, đại lượng, kiểm định. Nguồn có sẵn hết trong `pipeline/*.py`. |
| **Hình 3, 5** | bạn của Nguyên | Hai hình quan trọng nhất. Dữ liệu có sẵn trong `results_H97` và `results_H94d`. |
| **§1, §3, §5, §6** | Nguyên | Cần biết lịch sử từng kết quả và lý do từng nhãn. |
| **§7 Phương pháp luận, §8 Hạn chế** | Nguyên | Cần nhớ tại sao từng luật ra đời. |
| **Phụ lục A–E** | trích tự động từ `../docs/` | Gần như copy. |

---

## 4b. Kết quả của các thành viên khác — ĐỌC TRƯỚC KHI GỘP

Dự án có **hai khối công việc** trên hai nhánh khác nhau, **hai chuẩn bằng chứng khác nhau**:

| khối | nhánh | nội dung | chuẩn bằng chứng |
|---|---|---|---|
| **Credit/Shapley + repair-vs-select** (Nguyên) | `nguyen` | vòng #97–#201 | **có đăng ký trước + cổng + niêm phong + VOID** |
| **Vai trò, debate, credit-RL, router** (Đức, Tùng Dương) | `duc`, `nguoi3-router`, `main` | ~30 tài liệu kết quả | **KHÔNG** dùng đăng ký trước/cổng/VOID |

⚠️ **Đây không phải chê ai.** Kỷ luật đăng-ký-trước chỉ ra đời từ vòng **#97** trên nhánh `nguyen`;
phần lớn công việc kia làm song song hoặc trước đó.

**Hệ quả bắt buộc cho báo cáo:** kết quả của hai khối **không được đặt cùng một tầng bằng chứng**
mà không kiểm lại. Ba lựa chọn, chọn một và **nói rõ trong báo cáo**:
1. Ghi rõ hai chuẩn khác nhau, để kết quả khối kia ở **tầng B (thăm dò)**;
2. Kiểm lại hậu kỳ: dựng cổng chất lượng tương đương rồi báo cáo cái nào qua;
3. Tách thành hai phần riêng, mỗi phần nêu chuẩn của mình.

**Khuyến nghị: lựa chọn 1** — rẻ, trung thực, và không đòi chạy lại.

### Hai kết quả của thành viên khác nên đưa vào báo cáo
- **`EFFICIENCY.md` **(chỉ có trên nhánh `nguoi3-router`)**** (Tùng Dương, 210 dòng, tự viết toàn bộ): Consensus Router đạt
  **.7200 acc / 2.32 cost** trên GSM8K so với full pipeline **.7233 / 3** — tức **gần bằng độ chính
  xác với 77% chi phí**; nhưng **vô dụng trên MATH** (router .4133 = đúng bằng Solver một mình).
  Kèm phân tích cơ chế: khi `S`,`V` bất đồng thì `A` cứu được **45.4%** ở GSM8K nhưng chỉ **25.0%**
  ở MATH. → **Đây là bằng chứng độc lập cho M3** ("định tuyến tiết kiệm ở chỗ ít cần nhất") và
  nên vào **§5** hoặc thành mục riêng.
- **`../docs/RELATED_BASELINES.md`** (Đức): literature cho thấy **debate thua self-consistency ở 3/4 ô**,
  và **sụp 16 điểm** với Llama3.1-8B trên GSM8K. → **Trùng hướng với kết luận "CHỌN thắng SỬA"**,
  đến từ nguồn hoàn toàn độc lập. Rất mạnh cho **§2** và **§6**.

## 5. Nguồn ở đâu

```
shapley/
├─ report/                     ← BA TEP HUONG DAN VIET BAO CAO (thu muc nay)
│  ├─ README.md                ← bat dau tu day
│  ├─ BAO_CAO_CAU_TRUC.md      ← viet CAI GI
│  ├─ HUONG_DAN_CONG_TAC.md    ← duoc phep viet CON SO NAO (tep nay)
│  ├─ QUY_TRINH_VIET_BAO_CAO.md← lam THEO THU TU NAO
│  └─ BAO_CAO.md               ← BAN THAO (chua co — Buoc 1 tao)
├─ docs/                       ← TAI LIEU KET QUA (38 tep) — KHONG phai huong dan viet
│  ├─ INDEX.md                 ← muc luc cua docs/
│  ├─ TONG_HOP.md              ← KHUNG ly thuyet. Doc truoc tien.
│  ├─ RESULTS.md               ← bang ket qua mang nhom (co thanh sai so 5 fold)
│  ├─ PREREGISTRATION.md       ← moi bang khoa
│  ├─ IDEAS.md                 ← nhat ky 201 vong
│  ├─ QUY_TRINH_VONG_LAP.md    ← 37 luat quy trinh
│  ├─ RESULT_SEALS.md          ← hash niem phong
│  └─ (29 tep ket qua cua Duc: CREDIT_RL, ORPO, SOLVEJUDGE, RELATED_*, ...)
├─ results_*/                  ← artifact tho (KHONG nam trong git)
└─ pipeline/ deploy/ analysis/ ← code
```

**Ba vòng nên đọc trước:** **#197** (`D` là hình phạt của nội dung sai) · **#185** (luật chênh) ·
**#182** (rút nhãn "khác họ"). Ba vòng đó là xương sống của §5.

---

## 6. Còn đang chạy — sẽ nối vào sau

| lần chạy | câu hỏi | nối vào đâu |
|---|---|---|
| **H100e** | `Δ_honest` — giao thức **độc lập-trước** có thắng việc gọi thẳng `I` không? | §5 mục mới, và §8 nếu âm |
| **H99b** | luật chênh có chuyển sang **toán** không? | §5.4; nếu không chuyển thì **phải thu hẹp luật thành "trên code"** ở §5.4 **và** §6 |

**Cả hai đều có bảng khoá đã commit.** Khi có kết quả: đọc bảng khoá **trước**, rồi mới đọc số.
**Đừng viết trước phần này** — nếu H99b rơi vào hàng 1 thì §5.4 và §6 phải sửa câu chữ.

---

## 7. Quy tắc làm việc chung

1. **Mỗi con số phải kèm nguồn** — `results_X/res_X.json`, khoá nào. Người chấm hỏi được.
2. **Đừng làm tròn lại.** Nếu nguồn ghi `−.2720` thì đừng viết `−.27` ở bảng (trong câu văn thì được).
3. **Đừng "làm mượt" kết luận.** Chỗ mạnh nhất của báo cáo là chỗ nói *"chúng tôi đo trần của
   chính đề xuất của mình và nó chỉ +.018"*. Giữ nguyên những chỗ như vậy.
4. **Kết quả âm và VOID là nội dung, không phải điều đáng xấu hổ.** Tỉ lệ VOID 52% là **bằng chứng
   cổng đang làm việc**. Đặt nó vào §7 một cách tự tin.
5. Có gì không chắc thuộc tầng nào ⇒ **hỏi Nguyên**, đừng đoán.
