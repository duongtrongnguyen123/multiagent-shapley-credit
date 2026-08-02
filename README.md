# Đánh giá đóng góp của từng vai trò trong hệ suy luận multi-agent LLM bằng giá trị Shapley: mức đóng góp thay đổi theo độ khó bài toán và năng lực model
<sub>Shapley Credit Assignment for Multi-Agent LLM Reasoning: Role Value Across Task Difficulty and Model Capacity</sub>

Dự án này đo lường mức đóng góp thực sự của từng vai trò (agent) trong một pipeline
multi-agent gồm bốn tác nhân **Planner → Solver → Verifier → Aggregator** khi cùng giải
toán. Chúng tôi dùng **giá trị Shapley** tính chính xác trên toàn bộ 16 tổ hợp (liên minh)
vai trò để tách bạch phần công của mỗi tác nhân. Toàn bộ quá trình suy luận được chạy song
song trên GPU của Kaggle (T4), mỗi liên minh tương ứng với một tài khoản.

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

Để đo đóng góp của từng vai trò, chúng tôi chạy cả 2⁴ = 16 liên minh trên cùng một tập câu
hỏi, trong đó `v(S)` là độ chính xác của pipeline khi chỉ bật các vai trò thuộc tập `S`.
Giá trị Shapley của vai trò $i$ được tính bằng công thức:

$$\varphi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!\,(n-|S|-1)!}{n!}\,\bigl(v(S \cup \{i\}) - v(S)\bigr)$$

Về cấu hình, mọi vai trò đều dùng Qwen2.5-1.5B-Instruct (riêng các vòng thí nghiệm "năng
lực" sẽ nâng một vai trò lên bản 7B), giải mã theo kiểu greedy. Cả model lẫn dữ liệu đều
được mount sẵn từ Kaggle nên kernel không cần Internet. Mỗi liên minh được đẩy thành một
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
  orchestrate*.py             # sinh 16 (hoặc 8) liên minh và deploy mỗi liên minh một tài khoản
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
# 1) Deploy 16 liên minh, mỗi liên minh một tài khoản
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

- MATH chậm hơn GSM8K khoảng 7 lần (mỗi liên minh hai tầng mất chừng 60-70 phút ở N=500),
  vì vậy nên dùng N=300 cho các vòng năng lực.
- Không nên dùng vòng lặp nền để poll trạng thái, vì chúng bị kill mỗi khi đổi lượt; hãy
  luôn gọi `sync_once.py` một cách đồng bộ.
- Với kernel Kaggle: slug được suy ra từ `title` chứ không phải `id`; đường dẫn mount của
  dataset không trùng với ref nên cần dùng `glob` trên `/kaggle/input/**`; và cần ép GPU T4
  bằng `machine_shape="NvidiaTeslaT4"` để tránh rơi về P100.

---

## 5. Phân công công việc (đội 4 người)

Vòng nền `m1` (MATH đồng nhất 1.5B) đã hoàn tất, và đây là điều kiện tiên quyết cho mọi vòng
năng lực về sau. Vì Aggregator vươn lên vị trí số 1 trên MATH, vòng nâng Aggregator lên 7B
hiện là thí nghiệm đáng ưu tiên nhất.

| Người | Nhiệm vụ | Lệnh chính | Lý do |
|---|---|---|---|
| **Người 1 · Nguyên** | Vòng 7B-Aggregator (`mA`) và tổng hợp cuối cùng | `BIG=A ROUND=mA N_EVAL=300 python orchestrate_math_role7b.py` | Kiểm chứng dự đoán: Aggregator có thống trị trên MATH giống như Verifier từng thống trị trên GSM8K hay không |
| **Người 2** | Vòng 7B-Verifier (`mV`) và 7B-Solver (`mS`) | `BIG=V ROUND=mV N_EVAL=300 python orchestrate_math_role7b.py` | Xem việc nâng năng lực có cứu được Verifier trên bài khó hay nó vẫn bão hòa |
| **Người 3** | Vòng 7B-Planner (`mP`) | `BIG=P ROUND=mP N_EVAL=300 python orchestrate_math_role7b.py` | Planner đã hết đóng góp âm trên MATH, thử xem bản 7B có biến việc lập dàn ý thành lợi thế thật sự không |
| **Người 4** | Nhánh Coding (độc lập) | tự dựng kernel Coder cùng bộ MBPP+ có chạy unit test | Verifier lúc này có căn cứ (chạy test thật) và phần thưởng được phân mức — hướng cho kết quả mới mẻ nhất |

Vì cả đội chỉ có 19 tài khoản nên tại một thời điểm chỉ nên chạy tối đa hai vòng song song.
Đợt A (làm ngay) gồm Người 1 chạy `mA` với 8 tài khoản và Người 2 chạy `mV` với 8 tài khoản.
Đợt B là Người 3 chạy `mP` và Người 2 chạy `mS` khi các tài khoản đã rảnh. Nhánh coding của
Người 4 chạy độc lập, không tranh chấp tài khoản với các vòng trên.

Một số quy tắc chung: nên dùng `N_EVAL=300`; bỏ qua tài khoản `truongdv006` vì đã bị khoá, và
dùng các tài khoản dự phòng `khunht`, `dnglethnh`, `tbmdemi`; các thành viên nên báo nhau
trước khi chạy để tránh trùng tài khoản. Sản phẩm bàn giao của mỗi người là file
`shapley_<round>_results.json` cùng một dòng trong bảng role×capacity chung do Người 1 tổng
hợp. Chi tiết đầy đủ nằm trong [`shapley/WORK_SPLIT.md`](shapley/WORK_SPLIT.md).

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
