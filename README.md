# Đánh giá đóng góp trong hệ suy luận multi-agent LLM: đo lường vai trò và tính KHÔNG BỀN của hiệu ứng
<sub>Credit Assignment in Multi-Agent LLM Reasoning: Measuring Role Value and the Non-Transferability of Effects</sub>

Các mô hình ngôn ngữ ngày càng phối hợp thành nhóm để giải toán, thay vì làm một mình: một *Planner* phác
hướng, *Solver* giải, *Verifier* kiểm tra, *Aggregator* chốt đáp án — và chúng **phối hợp
hoàn toàn bằng ngôn ngữ** — mô hình sau đọc lời giải của mô hình trước rồi viết tiếp. Nhưng giao tiếp là con dao
hai lưỡi: lời của mô hình này có thể sửa lỗi cho mô hình kia, hoặc **làm hỏng một đáp án vốn đã
đúng** (hiện tượng *sycophancy* — mô hình đang đúng lại hùa theo bạn cùng nhóm rồi sửa thành sai).

Xuất phát điểm của dự án là câu hỏi **vai trò nào thực sự đóng góp?**, đo bằng **giá trị Shapley**
trên 2⁴ = 16 tổ hợp vai trò. Nhưng khi mở rộng sang lưới `task × cỡ model` và kiểm chứng bằng
**đăng ký trước (pre-registration)**, chúng tôi gặp một hiện tượng lặp đi lặp lại quan trọng hơn
chính bảng Shapley ban đầu:

> ### Hướng chính hiện tại
> **Hiệu ứng của các cơ chế phối hợp đa tác tử KHÔNG BỀN — chúng đổi dấu khi đổi task hoặc đổi cỡ model.**
>
> Cùng một lựa chọn kiến trúc, cùng mã nguồn, cùng bộ lời giải: truyền trace giữa các agent
> **+7.6 điểm** trên GSM8K 1.5B nhưng **−9.0 điểm** trên MATH 1.5B. Che giá trị trung gian
> **+8.4** rồi **−2.0**. Context không liên quan **−3.6** rồi **+5.5**. Bộ tổng hợp LLM **−6.7**
> rồi **+1.7**. Năm can thiệp, năm lần đảo dấu — chi tiết ở [`RESULTS.md`](shapley/docs/RESULTS.md).
>
> **Hệ quả:** một nghiên cứu chỉ báo cáo **một ô** của lưới sẽ trông rất thuyết phục và vẫn sai.
> Muốn kết luận bất cứ điều gì về phối hợp đa tác tử, phải đo trên **lưới**, không phải một điểm.

Phát hiện này được củng cố bởi chính **kỷ luật kiểm chứng**: 9 giả thuyết của nhóm đã bị bác bỏ,
1 kết quả phải tự rút lại, 1 thí nghiệm bị tuyên vô hiệu bởi ngưỡng hiệu lực khoá sẵn, và 1 lỗi
thiết kế được tự công bố. Mỗi giả thuyết đều có **bảng diễn giải khoá trước khi chạy**
([`PREREGISTRATION.md`](shapley/docs/PREREGISTRATION.md)) — lịch sử git chứng minh không kết quả nào
bị diễn giải lại sau khi đã nhìn thấy số.

**Đọc theo thứ tự:** [`RESULTS.md`](shapley/docs/RESULTS.md) (bảng tổng hợp) →
[`PREREGISTRATION.md`](shapley/docs/PREREGISTRATION.md) (đăng ký trước) →
[`IDEAS.md`](shapley/docs/IDEAS.md) (nhật ký từng vòng) → [`INTRO.md`](shapley/docs/INTRO.md) (nháp Intro).

---

## 0. Tóm tắt kết quả

**Những gì có tác dụng (đo được):**

| Phương pháp | Kết quả |
|---|---|
| Solver 1.5B + **Verifier 7B** (post-hoc) | **.46 → .64**, 9 sửa / **0 phá** |
| **loop** — Solver giải lại sau khi bị chê (MATH 1.5B) | **.40 → .60** |
| Pipeline đầy đủ vs Solver đơn độc (GSM8K 1.5B) | **.632 → .744** |
| **Self-consistency** maj@8 (MATH 1.5B) | **.50 → .60** |
| **Sửa lỗi bằng chạy test** (HumanEval, 3 vòng) | .787 → **.835** (7B), **0 phá** |

**Phân bổ đóng góp đo ở mức đầu-cuối** (GSM8K 1.5B, n=250): P→S `.684` →
**P→S→V `.732`** → P→S→V→A `.744`. **Verifier mang gần như toàn bộ giá trị.**
Nhưng nếu V và A chỉ nhận đáp án (không nhận trace) thì pipeline tụt còn `.668` —
**tệ hơn cả việc bỏ hẳn hai vai đó** (`.684`).

---

## 1. Phương pháp

Bốn vai trò trong pipeline được định nghĩa như sau:

- **Planner** — đọc đề rồi lập dàn ý các bước, không tính ra đáp số cuối cùng.
- **Solver** — giải từng bước và đưa ra đáp án đầu tiên (dạng `\boxed{}` hoặc "The answer is X").
- **Verifier** — nhận lời giải của Solver, kiểm tra từng bước và sửa lại nếu phát hiện sai.
- **Aggregator** — nhận các lời giải ứng viên, đối chiếu rồi chọn ra đáp án cuối cùng.

Các agent nối tiếp nhau, mỗi agent đọc kết quả của agent trước rồi viết tiếp (phối hợp bằng
ngôn ngữ):

```mermaid
flowchart LR
    Q([Đề bài]) --> P[Planner<br/>lập dàn ý]
    Q --> S[Solver<br/>giải + đáp số]
    Q --> V[Verifier<br/>soát & sửa]
    Q --> A[Aggregator<br/>chọn đáp cuối]
    P -- dàn ý --> S
    S -- lời giải --> V
    S -- ứng viên --> A
    V -- ứng viên --> A
    A --> ANS([Đáp án cuối])

    classDef pos fill:#d7f0d7,stroke:#2f8f2f;
    classDef neg fill:#f7d9d9,stroke:#c23b3b;
    class S,V,A pos;
    class P neg;
```

*Xanh = đóng góp dương; đỏ = Planner (đóng góp ≈0 / âm, hay "phá" đáp án đúng). Verifier &
Aggregator đọc lời giải của Solver — đó là nơi vừa sinh ra "sửa đúng" vừa sinh ra "phá hỏng".*

Để đo đóng góp của từng vai trò, chúng tôi chạy cả 2⁴ = 16 tổ hợp trên cùng một tập câu
hỏi, trong đó `v(S)` là độ chính xác của pipeline khi chỉ bật các vai trò thuộc tập `S`.
Giá trị Shapley của vai trò $i$ được tính bằng công thức:

$$
\varphi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!\,(n-|S|-1)!}{n!}\,\bigl(v(S \cup \{i\}) - v(S)\bigr)
$$

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

Báo cáo đầy đủ nằm trong [`shapley/docs/FINDINGS.md`](shapley/docs/FINDINGS.md).

---

## 3. Cấu trúc repo

```
kernel/                    # kernel GSM8K inference ban đầu (Qwen 1.5B)
shapley/
  START_HERE.md            # ĐỌC TRƯỚC — luồng 3 bước + 4 người bắt đầu từ đâu
  pipeline/                # định nghĩa hệ 4 agent (các template_*.py)
  deploy/                  # đẩy tổ hợp lên Kaggle + thu kết quả (orchestrate*, sync_once)
  analysis/                # tính Shapley, bootstrap, chấm lại điểm (shapley*, bootstrap*, regrade)
  docs/                    # FINDINGS.md (báo cáo kết quả)
  results_summary/         # các file JSON kết quả nhỏ (đã commit)
  probe7b/                 # kernel thử tải model 7B
```
Chi tiết vai trò từng thư mục và cách bắt đầu: [`shapley/START_HERE.md`](shapley/START_HERE.md).

Về bảo mật, các file `accounts.txt`, `manifest*.json` và `monitor.sh` có chứa token Kaggle
nên đã được đưa vào `.gitignore` và tuyệt đối không commit lên repo. Các thư mục `results_*/`
và `kernels_*/` là dữ liệu có thể tái sinh nên cũng được bỏ qua.

---

## 4. Hướng dẫn chạy

Yêu cầu: Kaggle CLI phiên bản 2.x trở lên, và một file `accounts.txt` với mỗi dòng theo
định dạng `USERNAME TOKEN`.

```bash
cd shapley

# 1) Deploy 16 tổ hợp, mỗi tổ hợp một tài khoản
ROUND=m1 N_EVAL=300 python deploy/orchestrate_math.py

# 2) Thu kết quả (chạy tiền cảnh, lặp lại tới khi REMAINING về 0)
ROUND=m1 python deploy/sync_once.py     # gọi lại vài lần, cách nhau khoảng 10-15 phút

# 3) Chấm lại (chỉ với MATH) rồi tính Shapley và khoảng tin cậy
ROUND=m1 python analysis/regrade_math.py
ROUND=m1 python analysis/shapley.py
ROUND=m1 python analysis/bootstrap.py

# Vòng thí nghiệm năng lực (nâng một vai trò lên 7B), với BIG thuộc {P,S,V,A}
BIG=A ROUND=mA N_EVAL=300 python deploy/orchestrate_math_role7b.py
ROUND=mA python deploy/sync_once.py
BIG=A ROUND=mA python analysis/shapley_role7b.py
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

Đồ án là một **audit thực nghiệm** đóng góp vai trò (không phải đề xuất method mới). Mỗi
người phụ trách một mảng = một thí-nghiệm/build + một mục báo cáo:

| Người | Mảng | Việc cụ thể | Mục báo cáo |
|---|---|---|---|
| **Người 1 · Nguyên** | Thí nghiệm + Tổng hợp | Chạy nốt **mA/mV/mP** trên MATH → hoàn tất lưới vai×khó×năng-lực; bảng master; viết Intro + RQ2 (ranking reversal); chủ trì ghép báo cáo | Intro, Results |
| **Người 2** | Chẩn đoán | **signed Shapley** (chaotic agent) + negative transfer + ví dụ sycophancy từ completion thật | Analysis |
| **Người 3** | Hiệu quả | Build **`analysis/router.py`** + đường Pareto accuracy–compute (dùng oracle +19) | Efficiency |
| **Người 4** | Method + Related Work | Viết Method (Shapley/grader/CI) + Related Work trung thực; baseline **self-consistency** | Method, Related Work |

Kế hoạch đầy đủ (câu hỏi nghiên cứu, đã-làm, money figures, **timeline hôm-nay/ngày-mai cho
từng người**, lộ trình 3 tuần) nằm trong **[`PROJECT_PLAN.md`](PROJECT_PLAN.md)**. Lưu ý:
chỉ Người 1 chạy Kaggle; Người 2/3/4 làm trên dữ liệu đã tải trong `shapley/results_*/`.

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
