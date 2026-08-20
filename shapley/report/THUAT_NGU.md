# Thuật ngữ và ký hiệu

Tài liệu tra cứu cho người đọc báo cáo. Mỗi mục nêu **định nghĩa chính xác** (đúng như cách tính
trong mã nguồn), kèm ví dụ khi cần.

---

## 1. Ba cách dùng nhiều lượt sinh

Đây là nhóm thuật ngữ hay bị lẫn nhất. Giả sử với **một câu hỏi**, model sinh `k` lời giải độc lập
(gọi là `k` **mẫu**), mỗi mẫu cho một đáp án.

### `greedy` — một lượt sinh, không lấy mẫu ngẫu nhiên

Model sinh **đúng một** lời giải, luôn chọn token có xác suất cao nhất. Kết quả **tất định**: chạy
lại cùng cấu hình cho kết quả giống hệt. Đây là mốc rẻ nhất, chi phí 1 lượt.

### `maj@k` — bỏ phiếu đa số trên `k` mẫu

Lấy `k` mẫu, **chuẩn hoá** đáp án của từng mẫu (bỏ khoảng trắng, `\left`, `\dfrac` → `\frac`…),
rồi chọn đáp án **xuất hiện nhiều lần nhất**.

```
k = 5 mẫu, đáp án lần lượt:   42 · 42 · 17 · 42 · 8
                               ↓
đếm phiếu:  42 → 3 phiếu · 17 → 1 phiếu · 8 → 1 phiếu
maj@5 = 42
```

Đây là **self-consistency**. Chi phí `k` lượt. Nó **không dùng thêm model nào** — chỉ đếm.

### `oracle@k` — **trần lý tưởng**, không phải một phương pháp

Câu được tính là **đúng** nếu **có ít nhất một** trong `k` mẫu đúng, bất kể mẫu đó là mẫu thứ mấy.

```
k = 5 mẫu, đáp án:   42 · 42 · 17 · 42 · 8      (đáp án chuẩn = 17)
maj@5     = 42  → SAI
oracle@5  = ĐÚNG, vì mẫu thứ 3 đúng
```

> **`oracle@k` không phải một chiến lược chạy được.** Nó đòi phải **biết trước** đáp án nào đúng.
> Nó tồn tại để trả lời câu hỏi: *"nếu có một bộ chọn hoàn hảo thì tối đa đạt được bao nhiêu?"*

**Vì sao ba con số này quan trọng khi đọc chung:**

```
greedy  ≤  maj@k  ≤  oracle@k
   |         |          |
   |         |          └─ trần: pool có chứa đáp án đúng ở bao nhiêu câu
   |         └─ bỏ phiếu lấy được bao nhiêu
   └─ một lượt lấy được bao nhiêu
```

**Khoảng cách `oracle@k − maj@k` là "phần còn để lại trên bàn"** — phần mà một bộ chọn tốt hơn bỏ
phiếu có thể lấy thêm. Đây là đại lượng trung tâm của báo cáo: giá trị của mọi bộ kiểm bị **chặn
trên** bởi khoảng cách này.

| Miền | `oracle@k − maj@k` | Bộ kiểm lấy được |
|---|---|---|
| Code (HumanEval) | **+21,3 điểm** | bộ test lấy **toàn bộ** |
| Toán (MATH) | nhỏ | bộ phân loại AUC 0,893 chỉ lấy **+2,4 điểm** |

---

## 2. Vai trò trong pipeline

Pipeline gốc của dự án là chuỗi bốn vai: **`P → S → V → A`**

| Ký hiệu | Vai | Nhiệm vụ theo thiết kế |
|---|---|---|
| `P` | **Planner** | Vạch kế hoạch giải, **không** được tính ra đáp án |
| `S` | **Solver** | Giải bài theo kế hoạch |
| `V` | **Verifier** | Kiểm từng bước, sửa nếu sai |
| `A` | **Aggregator** | Tổng hợp các đáp án thành một đáp án cuối |

Các tổ hợp hay gặp: `PS` (chỉ planner + solver) · `PSV` (thêm verifier) · `PSVA` (đủ bốn vai) ·
`SVV` (một solver, hai verifier) · `S-alone` (solver chạy một mình).

**Chi phí** thường ghi theo **số lượt gọi model trên mỗi câu**: `PS` = 2, `PSV` = 3, `PSVA` = 4.

⚠️ **Số lượt gọi không bằng số token.** Mỗi vai tốn lượng token rất khác nhau — verifier tốn gấp
khoảng 5 lần aggregator. Báo cáo dùng **cả hai** thước đo và nêu rõ đang dùng thước nào.

`V_gain` = `acc(PSV) − acc(PS)` — phần verifier đóng góp.
`A_gain` = `acc(PSVA) − acc(PSV)` — phần aggregator đóng góp.

---

## 3. Ký hiệu trong phần "sửa chữa so với tuyển chọn"

Phần này dùng hệ ký hiệu riêng, **không trùng** với vai trò ở mục 2.

| Ký hiệu | Nghĩa |
|---|---|
| `S` | Model **yếu** (small) — sinh ra artifact |
| `I` | Model **mạnh** (identical task, chạy một mình) — đây là **mốc so sánh đúng** |
| `V` | Kết quả khi model mạnh **sửa** artifact của model yếu |
| `CEIL` | Trần lý tưởng: giữ đáp án của `S` khi `S` đúng, ngược lại lấy `V` |

**Bốn đại lượng delta:**

| Đại lượng | Công thức | Trả lời câu hỏi |
|---|---|---|
| `Δ_ceil` | `acc(CEIL) − acc(I)` | Có **dư địa** nào để khai thác không (dùng oracle)? |
| `Δ_honest` | `acc(V) − acc(I)` | Giao thức **thực tế** có hơn gọi thẳng model mạnh không? |
| `Δ_gate` | `acc(có cổng) − acc(V)` | Thêm cổng lọc có cứu được không? |
| `V − S` | `acc(V) − acc(S)` | So với model **yếu** — mốc mà phần lớn công trình dùng |

> **Điểm mấu chốt của báo cáo: `V − S` và `V − I` thường **ngược dấu**.**
> `V − S` dương (có vẻ cải thiện), `V − I` âm (thực ra thua việc chỉ gọi model mạnh).

---

## 4. Phân rã `A − B + C`

Với cùng bộ ký hiệu ở mục 3, mỗi câu rơi vào đúng một ô tuỳ theo `S`, `I`, `V` đúng hay sai:

```
Δ_ceil  =  A  −  B  +  C

A = P(S đúng ∧ I sai)          "cơ hội"    — model yếu làm được bài mà model mạnh trượt
B = P(S sai ∧ I đúng ∧ V sai)  "thiệt hại" — việc sửa làm hỏng bài mà model mạnh vốn làm đúng
C = P(S sai ∧ I sai ∧ V đúng)  "cứu vớt"   — việc sửa cứu được bài cả hai đều trượt
```

Đây là **đẳng thức đại số**, không phải mô hình xấp xỉ — nó luôn đúng tuyệt đối.

Ý nghĩa của việc tách ba số hạng: **`A` là tính chất của cặp model** (không đổi được nếu không đổi
model), còn **`B` là tính chất của giao thức** (đổi cách phối hợp thì `B` đổi). Giao thức **chỉ
chọn** có `B` gần bằng 0 vì nó không thể tạo ra lời giải sai mới; giao thức **sửa** luôn phải trả `B`.

---

## 5. Khung `H × κ − D`

```
giá trị  =  H(pool) × κ(z)  −  D(giao thức)
```

| Ký hiệu | Đọc là | Nghĩa |
|---|---|---|
| `H` | *dư địa* | Pool ứng viên có chứa lời giải mà model mạnh đơn lẻ không tạo ra được không? Đo bằng `oracle@k` |
| `κ` | *kappa* — chất lượng bộ chọn | Một tín hiệu **khả thi** (không phải oracle) có lấy được lời giải đó ra không? |
| `D` | *thiệt hại* | Bản thân giao thức phá hỏng bao nhiêu? Chính là số hạng `B` |

---

## 6. Nguồn tín hiệu kiểm

| Ký hiệu | Nghĩa |
|---|---|
| `exec3` | Kiểm bằng **chạy test thật** (execution), 3 vòng. Tín hiệu **đúng đắn** |
| `llm3` | Kiểm bằng **để LLM tự đọc và phán**, 3 vòng. Tín hiệu **học được** |
| `llm_agg@k` | Đưa cả `k` ứng viên cho một LLM đọc rồi tổng hợp |
| `wvote` | Bỏ phiếu **có trọng số** theo điểm của một bộ phân loại đã huấn luyện |
| `PAL` | Giải bằng cách sinh code rồi chạy, thay vì suy luận bằng văn bản |

**`breaks_majority` / `fixes_majority`** — đếm số câu mà thành phần LLM **phá** một đáp án đa số vốn
đúng, so với số câu nó **sửa** được một đáp án đa số vốn sai. Tỷ lệ 26 phá : 0 sửa nghĩa là nó chỉ
làm hỏng, không cứu được gì.

---

## 7. Thuật ngữ về độ tin cậy

| Thuật ngữ | Nghĩa |
|---|---|
| **fold** | Một phần dữ liệu rời nhau. "5 fold × 60" = chia 300 câu thành 5 phần 60 câu, đo riêng từng phần |
| **5/5 fold** | Hiệu ứng **cùng dấu ở cả năm phần** — tiêu chuẩn mạnh nhất của khối nhóm |
| **sàn nhiễu** | Mức dao động khi chạy **cùng một cấu hình** trên các fold khác nhau. Ở dự án này là **≈ 5 điểm**; hiệu ứng nhỏ hơn thế, đo một lần, **không tính là bằng chứng** |
| **tiền đăng ký** | Ghi trước giả thuyết và **bảng diễn giải** rồi commit **trước khi chạy** |
| **bảng diễn giải đã khoá** | Bảng liệt kê trước mọi kết cục có thể và kết luận tương ứng, **gồm cả một dòng bác bỏ giả thuyết** |
| **điều kiện hợp lệ** | Các ngưỡng chất lượng đo lường (tỷ lệ trích xuất được đáp án, tỷ lệ cắt cụt, cỡ mẫu…) |
| **VOID** | Có ít nhất một điều kiện hợp lệ không đạt ⇒ **không đọc số liệu của lần chạy đó** |
| **AUC** | Diện tích dưới đường ROC. 0,5 = đoán ngẫu nhiên; 1,0 = phân biệt hoàn hảo |
| **McNemar** | Kiểm định cho dữ liệu **ghép cặp** — dùng khi hai phương pháp chạy trên **cùng** bộ câu hỏi |
| **bootstrap** | Lấy mẫu lại có hoàn lại để ước lượng khoảng tin cậy khi không có công thức sẵn |

---

## 8. Benchmark

| Tên | Nội dung | Cách chấm |
|---|---|---|
| **GSM8K** | Toán tiểu học bằng lời, nhiều bước | So đáp án số cuối cùng |
| **MATH-500** | Toán thi, khó hơn nhiều | So biểu thức trong `\boxed{}`, có chuẩn hoá |
| **MBPP** | Sinh hàm Python ngắn | **Chạy test thật**. Dải chính 11–510; dải giữ lại 511–974 (chỉ 464 bài) |
| **HumanEval** | Sinh hàm Python, 164 bài | **Chạy test thật** |

⚠️ **MBPP và HumanEval có bộ kiểm đúng đắn** (chạy được test), MATH và GSM8K thì **không**. Đây là
lý do kết luận của báo cáo khác nhau giữa hai nhóm miền — xem §5.8.

---

## 9. Model

| Tên gọi tắt | Model | Ghi chú |
|---|---|---|
| `1.5B`, `m15`, `S15` | Qwen2.5-1.5B-Instruct | Model yếu chuẩn của dự án |
| `7B`, `m7`, `S7` | Qwen2.5-7B-Instruct | Model mạnh chuẩn |
| `14B`, `32B` | Qwen2.5-14B / 32B-Instruct | Dùng ở các thí nghiệm mở rộng |
| `llama8b` | Llama-3.1-8B-Instruct | Dùng cho đối chứng khác họ model |
| `dscoder` | DeepSeek-Coder-6.7B-Instruct | Model **code**; đạt 1,2% trên MATH nên không dùng cho toán |

Hậu tố trong tên thư mục kết quả: `_g` = GSM8K · `_m` = MATH · `he` = HumanEval.
