# Đánh giá đóng góp trong hệ suy luận multi-agent LLM: từ đo lường giá trị vai trò đến phối hợp động
<sub>Credit Assignment in Multi-Agent LLM Reasoning: From Measuring Role Value to Dynamic Composition</sub>

Dự án này đo lường mức đóng góp thực sự của từng vai trò (agent) trong một pipeline
multi-agent gồm bốn tác nhân **Planner → Solver → Verifier → Aggregator** khi cùng giải
toán. Chúng tôi dùng **giá trị Shapley** tính chính xác trên toàn bộ 16 tổ hợp
vai trò để tách bạch phần công của mỗi tác nhân. Toàn bộ quá trình suy luận được chạy song
song trên GPU của Kaggle (T4), mỗi tổ hợp tương ứng với một tài khoản.

Câu hỏi cốt lõi của nghiên cứu là: trong một đội agent, ai thực sự đóng góp vào kết quả,
ai chỉ "ăn theo" (free-rider), và mức đóng góp đó thay đổi ra sao khi độ khó của bài toán
cũng như năng lực của model thay đổi.

---

## 1. Phương pháp

Bốn vai trò trong pipeline được định nghĩa như sau:

- **Planner** — đọc đề rồi lập dàn ý các bước, không tính ra đáp số cuối cùng.
- **Solver** — giải từng bước và đưa ra đáp án đầu tiên (dạng `\boxed{}` hoặc "The answer is X").
- **Verifier** — nhận lời giải của Solver, kiểm tra từng bước và sửa lại nếu phát hiện sai.
- **Aggregator** — nhận các lời giải ứng viên, đối chiếu rồi chọn ra đáp án cuối cùng.

Để đo đóng góp của từng vai trò, chúng tôi chạy cả 2⁴ = 16 tổ hợp trên cùng một tập câu
hỏi, trong đó `v(S)` là độ chính xác của pipeline khi chỉ bật các vai trò thuộc tập `S`.
Giá trị Shapley của vai trò $i$ được tính bằng công thức:

$$\varphi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!\,(n-|S|-1)!}{n!}\,\bigl(v(S \cup \{i\}) - v(S)\bigr)$$

Về cấu hình, mọi vai trò đều dùng Qwen2.5-1.5B-Instruct (riêng các vòng thí nghiệm "năng
lực" sẽ nâng một vai trò lên bản 7B), giải mã theo kiểu greedy. Cả model lẫn dữ liệu đều
được mount sẵn từ Kaggle nên kernel không cần Internet. Mỗi tổ hợp được đẩy thành một
kernel Kaggle riêng, xác thực bằng `KAGGLE_API_TOKEN` của từng tài khoản, và kết quả được
thu về bằng `sync_once.py`.

---

## 2. Kết quả chính

Trên GSM8K (bài toán dễ) với cấu hình đồng nhất 1.5B (N=1319), thứ hạng đóng góp như sau:

| Vai trò | Shapley φ | Nhận xét |
|---|---|---|
| Solver | +0.252 | trụ cột của pipeline |
| Verifier | +0.252 | ngang bằng Solver — việc kiểm tra đáng giá như việc giải |
| Aggregator | +0.190 | có ích rõ rệt |
| Planner | −0.014 | đóng góp âm, đóng vai free-rider và gây "negative transfer" khoảng −12 điểm |

Ở các thí nghiệm nâng năng lực (chỉ nâng một vai trò lên 7B), chúng tôi thấy rằng khi nâng
Planner lên 7B thì giá trị Shapley của nó chuyển từ −0.023 thành +0.055, cho thấy tác hại
của Planner đến từ việc model quá yếu chứ không phải do bản chất vai trò. Còn khi nâng
Verifier lên 7B, giá trị Shapley của nó tăng từ +0.269 lên +0.462 và độ chính xác toàn
pipeline tăng từ 0.71 lên 0.87 — đây là vai trò nhạy cảm với năng lực model nhất, cải thiện
tới +26 điểm so với chỉ +7 điểm khi nâng Planner.

Điều thú vị là khi chuyển sang MATH-500 (bài toán khó) với cấu hình đồng nhất 1.5B (N=500),
thứ hạng gần như đảo ngược:

| Vai trò | MATH φ | So với GSM8K |
|---|---|---|
| **Aggregator** | **+0.148** | từ hạng 3 (+0.190) vươn lên số 1 |
| Solver | +0.141 | +0.252 |
| Verifier | +0.141 | +0.252 — không còn dẫn đầu |
| Planner | +0.017 | từ −0.014 chuyển sang không còn âm |

Kết quả này cho thấy nguyên tắc "nên đầu tư vào Verifier" chỉ đúng với GSM8K chứ không mang
tính tổng quát. Khi bài toán khó hơn, một verifier yếu không đủ sức sửa những lời giải dài
và sai nên vai trò kiểm tra dần bão hòa; lúc này Aggregator — vốn có nhiệm vụ chọn lọc giữa
nhiều lời giải khác nhau — mới trở thành vai trò quan trọng nhất. Nói cách khác, giá trị của
mỗi vai trò phụ thuộc vào cả độ khó của bài toán lẫn năng lực của model, chứ không phải là
một hằng số cố định.

Báo cáo đầy đủ nằm trong [`shapley/FINDINGS.md`](shapley/FINDINGS.md).

---

## 3. Cấu trúc repo

```
kernel/                       # kernel GSM8K inference ban đầu (Qwen 1.5B)
shapley/
  template.py                 # pipeline GSM8K, tham số hoá theo mặt nạ vai trò (P,S,V,A)
  template_math.py            # pipeline MATH-500 (chấm đáp án \boxed{} LaTeX)
  template_role7b.py          # phiên bản nâng một vai trò lên 7B (GSM8K)
  template_math_role7b.py     # phiên bản nâng một vai trò lên 7B (MATH)
  orchestrate*.py             # sinh 16 (hoặc 8) tổ hợp và deploy mỗi tổ hợp một tài khoản
  sync_once.py                # thu kết quả một lượt (đồng bộ, không dùng vòng lặp nền)
  shapley.py / shapley_role7b.py   # tính giá trị Shapley
  bootstrap.py / bootstrap_het.py  # tính khoảng tin cậy bằng bootstrap
  regrade_math.py             # chấm lại MATH offline từ preds.json
  FINDINGS.md                 # báo cáo kết quả (tiếng Anh)
  WORK_SPLIT.md               # phân công chi tiết kèm trình tự dùng tài khoản
```

Về bảo mật, các file `accounts.txt`, `manifest*.json` và `monitor.sh` có chứa token Kaggle
nên đã được đưa vào `.gitignore` và tuyệt đối không commit lên repo. Các thư mục `results_*/`
và `kernels_*/` là dữ liệu có thể tái sinh nên cũng được bỏ qua.

---

## 4. Hướng dẫn chạy

Yêu cầu: Kaggle CLI phiên bản 2.x trở lên, và một file `accounts.txt` với mỗi dòng theo
định dạng `USERNAME TOKEN`.

```bash
# 1) Deploy 16 tổ hợp, mỗi tổ hợp một tài khoản
ROUND=m1 N_EVAL=300 python orchestrate_math.py

# 2) Thu kết quả (chạy tiền cảnh, lặp lại tới khi REMAINING về 0)
ROUND=m1 python sync_once.py     # gọi lại vài lần, cách nhau khoảng 10-15 phút

# 3) Chấm lại (chỉ với MATH) rồi tính Shapley và khoảng tin cậy
ROUND=m1 python regrade_math.py
ROUND=m1 python shapley.py
ROUND=m1 python bootstrap.py

# Vòng thí nghiệm năng lực (nâng một vai trò lên 7B), với BIG thuộc {P,S,V,A}
BIG=A ROUND=mA N_EVAL=300 python orchestrate_math_role7b.py
ROUND=mA python sync_once.py
BIG=A ROUND=mA python shapley_role7b.py
```

Một vài điểm cần lưu ý khi chạy:

- MATH chậm hơn GSM8K khoảng 7 lần (mỗi tổ hợp hai tầng mất chừng 60-70 phút ở N=500),
  vì vậy nên dùng N=300 cho các vòng năng lực.
- Không nên dùng vòng lặp nền để poll trạng thái, vì chúng bị kill mỗi khi đổi lượt; hãy
  luôn gọi `sync_once.py` một cách đồng bộ.
- Với kernel Kaggle: slug được suy ra từ `title` chứ không phải `id`; đường dẫn mount của
  dataset không trùng với ref nên cần dùng `glob` trên `/kaggle/input/**`; và cần ép GPU T4
  bằng `machine_shape="NvidiaTeslaT4"` để tránh rơi về P100.

---

## 5. Phân công công việc (đội 4 người)

Vòng nền `m1` (MATH đồng nhất 1.5B) đã hoàn tất và là dữ liệu chung cho cả bốn hướng. Mỗi
người phụ trách một hypothesis; bốn hypothesis không rời rạc mà là bốn bước của một lập luận
nhân–quả: **H2 chẩn đoán bệnh → H1 kê thuốc → H3 đổi cấu trúc → H4 thay cơ chế.**

| Người | Hypothesis | Vai trò trong lập luận | Sản phẩm | Mục báo cáo |
|---|---|---|---|---|
| **Người 1 · Nguyên** | **H1 — Router động** (gate MoE trên tổ hợp agent) | *Kê thuốc:* né tổ hợp xấu, chọn tổ hợp theo từng câu | `router.py` | Dynamic Composition |
| **Người 2** | **H2 — Negative transfer** + confidence-gate | *Chẩn đoán:* vì sao agent yếu phá answer đúng (10.6%) | phân tích + patch | Negative Transfer |
| **Người 3** | **H3 — Topology agent như graph** tối ưu hoá được | *Đổi cấu trúc:* tỉa cạnh gây hại, tìm topology tốt hơn | `interaction.py` + so sánh topology | Agent Graph |
| **Người 4** | **H4 — Grounded verification** (verifier chạy tool) | *Thay cơ chế:* verifier có căn cứ thay vì suy luận chay | kernel verifier + tool | Grounded Verification |

Mô tả chi tiết từng hypothesis (giả thuyết, phương pháp, cách đo) nằm trong
[`HYPOTHESES.md`](HYPOTHESES.md), kèm framing MoE/graph và bằng chứng nền (oracle +19 điểm,
negative transfer 10.6%). Người 1 tổng hợp bốn mảnh thành luận điểm chung: *phối hợp
multi-agent nên **động** và **có căn cứ**, không nên **tĩnh** và **chay**.*

Các vòng thí nghiệm capacity (`BIG=<P|S|V|A> ROUND=m<X> N_EVAL=300 python
orchestrate_math_role7b.py`) là **hạ tầng dùng chung** nuôi cho nhiều hypothesis, không phải
phân công riêng của ai. Một số quy tắc: dùng `N_EVAL=300` (MATH ~7× chậm hơn GSM8K); bỏ tài
khoản `truongdv006` (đã khoá), dự phòng `khunht`/`dnglethnh`/`tbmdemi`; báo nhau trước khi
chạy để không trùng tài khoản (tối đa 2 vòng song song trên 19 tài khoản). Trình tự chạy chi
tiết trong [`shapley/WORK_SPLIT.md`](shapley/WORK_SPLIT.md).

---

## 6. Ghi chú kỹ thuật

Việc chấm điểm MATH được thực hiện bằng cách trích phần trong `\boxed{}` rồi chuẩn hoá chuỗi
và số trước khi so sánh. Bản chấm đầu tiên xoá hẳn `\text{...}` khiến các đáp án dạng chữ bị
khớp nhầm với nhau, và `regrade_math.py` sửa lỗi này ngay trên máy (giữ lại nội dung bên
trong `\text{}`) mà không cần chạy lại trên Kaggle.

Cuối cùng, khi cả bốn agent đều yếu như nhau (cùng dùng 1.5B), việc phối hợp gần như không
mang lại lợi ích trên bài khó — cả đội chỉ nhỉnh hơn một Solver đơn lẻ khoảng 0.02 điểm, và
hai vai trò "sản xuất" thậm chí còn gây nhiễu cho nhau. Điều này cho thấy tín hiệu thật sự
nằm ở các vòng thí nghiệm năng lực (khi các agent có năng lực khác nhau), chứ không phải ở
cấu hình đồng nhất.
