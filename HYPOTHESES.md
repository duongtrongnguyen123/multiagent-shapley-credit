# Các hướng nghiên cứu & phân công (4 hypothesis)

Tài liệu này gom bốn hướng nghiên cứu để cả nhóm 4 người chia nhau chạy, cùng một
khung chung: **phân bổ đóng góp (credit assignment) trong hệ multi-agent LLM**. Tất cả
dùng chung hạ tầng đã có (fan-out 16 liên minh trên Kaggle + tính Shapley), xem
[`README.md`](README.md) và [`shapley/FINDINGS.md`](shapley/FINDINGS.md).

---

## Framing thống nhất

Xem hệ multi-agent như một **graph có thể tối ưu hoá**: mỗi agent là một node, mỗi
message là một cạnh. Dùng phân bổ đóng góp (Shapley + chỉ số tương tác) làm *tín hiệu*
để **định tuyến động** (chọn liên minh theo từng câu) và **tỉa topology** (bỏ cạnh thừa),
thay cho pipeline tĩnh chạy cả 4 vai trò cho mọi câu.

**Liên hệ với Mixture-of-Experts (MoE).** Multi-agent về bản chất là "MoE nâng lên mức
ngữ nghĩa": expert là agent *diễn giải được* (Planner/Solver/Verifier/Aggregator) thay
vì sub-network ẩn, định tuyến ở mức *vai trò* thay vì *token*. Điểm khác mấu chốt: MoE có
một **gate được huấn luyện**, còn multi-agent hiện chạy gate = **prompt tĩnh**. Nhiều
hướng dưới đây chính là nỗ lực "học lại cái gate" đó cho hệ agent.

| | MoE | Multi-agent LLM |
|---|---|---|
| Expert | sub-network trong 1 model | nhiều LLM đầy đủ, mỗi cái một vai trò |
| Định tuyến | mức token, gate học sẵn | mức vai trò, prompt tĩnh |
| Chuyên biệt hoá | ẩn | tường minh |
| Giao tiếp | không | có (message) |
| Huấn luyện | joint | thường không train |

---

## Bằng chứng nền (từ dữ liệu `m1`, MATH-500, N=500)

Đo trực tiếp trên kết quả 16 liên minh đã có:

- Pipeline tĩnh đầy đủ (1111): **0.448**
- **Oracle** (router hoàn hảo chọn liên minh theo từng câu): **0.638 (+19 điểm)**
- Oracle chỉ dùng liên minh ≤2 vai trò (rẻ hơn full): **0.584**
- Full SAI nhưng có liên minh rẻ ĐÚNG: **16.8%** số câu
- Solver ĐÚNG nhưng full làm HỎNG (negative transfer cấp câu hỏi): **10.6%** số câu

Hai con số cuối là động lực chính cho H1 và H2.

---

## H1 — Router động: học "gate MoE" trên các liên minh agent
**Người phụ trách: Người 1 · Nguyên**

- **Giả thuyết:** giá trị vai trò biến thiên *theo từng câu hỏi*, nên pipeline tĩnh là
  dưới tối ưu. Một router nhẹ chọn liên minh phù hợp cho mỗi câu sẽ đạt accuracy cao hơn
  với compute thấp hơn.
- **Phương pháp:** xây router từ tín hiệu rẻ (độ đồng thuận giữa các vai trò, độ tự tin
  của model, độ dài/độ khó câu hỏi). So với: (a) baseline pipeline tĩnh, (b) trần oracle.
- **Đo:** phần trăm của +19 điểm oracle mà router lấy lại được, kèm chi phí (số lần gọi
  model). Báo cáo trung thực nếu headroom khó khai thác.
- **Sản phẩm:** `router.py` + bảng accuracy↑/compute↓; mục *Dynamic Composition*.

## H2 — Cơ chế negative transfer & confidence-gating
**Người phụ trách: Người 2**

- **Giả thuyết:** agent yếu *phá* lời giải đúng của peer (10.6% số câu) do sycophancy/
  anchoring — bị lời giải trước dẫn dắt và ghi đè đáp án đúng thành sai.
- **Phương pháp:** đặc tả "correct→wrong flip rate" theo từng vai trò và từng vị trí trong
  chuỗi; kiểm tra giả thuyết sycophancy (agent có xu hướng đồng ý/đổi theo input). Đề xuất
  một **cổng tự tin (confidence-gate)**: chỉ cho Verifier/Aggregator ghi đè khi đủ chắc.
- **Đo:** flip-rate trước/sau khi gating; accuracy toàn pipeline có cải thiện không.
- **Sản phẩm:** phân tích cơ chế + patch gating; mục *Negative Transfer*.

## H3 — Topology agent như một graph tối ưu hoá được
**Người phụ trách: Người 3 (thế mạnh knowledge graph / LAWGIC)**

- **Giả thuyết:** cấu trúc giao tiếp giữa các agent (chain / star / tree / complete) ảnh
  hưởng lớn tới kết quả; có một topology tốt hơn hẳn pipeline tuyến tính mặc định.
- **Phương pháp:** mô hình hoá hệ như graph (node = agent, edge = luồng message), chạy
  vài topology, dùng Shapley + **chỉ số tương tác từng cặp** để phát hiện cạnh cộng hưởng
  vs cạnh triệt tiêu (đã có manh mối: Verifier–Solver là *thay thế* nhau, không cộng
  hưởng). Tỉa cạnh thừa để ra topology gọn hơn mà không giảm accuracy.
- **Đo:** accuracy theo topology; ma trận tương tác 4×4; topology sau khi tỉa.
- **Sản phẩm:** `interaction.py` (chỉ số tương tác) + so sánh topology; mục *Agent Graph*.
- Liên hệ: hướng nóng gần đây (GPTSwarm, DyLAN, "Agents as optimizable graphs").

## H4 — Grounding: verifier có công cụ so với verifier "chay"
**Người phụ trách: Người 4**

- **Giả thuyết:** verifier vô-căn-cứ (chỉ suy luận lại bằng chính trọng số) sụp đổ trên
  bài khó; verifier *có căn cứ* (chạy Python/sympy, hoặc unit test với code) khôi phục giá
  trị vì có tín hiệu độc lập, đúng.
- **Phương pháp:** thêm một verifier chạy tool (sympy cho MATH, hoặc chuyển sang nhánh
  code + MBPP+ với unit test). Đo lại Shapley của Verifier: chay vs có-tool.
- **Đo:** φ của Verifier tăng bao nhiêu khi được grounding; so với việc chỉ nâng size model.
- **Sản phẩm:** kernel verifier có tool; mục *Grounded Verification*.

---

## Bảng phân công tổng hợp

| Người | Hypothesis | Sản phẩm | Mục báo cáo |
|---|---|---|---|
| **Người 1 · Nguyên** | H1 — Router động (gate MoE trên agent) | `router.py` | Dynamic Composition |
| **Người 2** | H2 — Negative transfer + confidence-gate | phân tích + patch | Negative Transfer |
| **Người 3** | H3 — Topology agent như graph | `interaction.py` + so sánh topology | Agent Graph |
| **Người 4** | H4 — Grounded verification (tool) | kernel verifier + tool | Grounded Verification |

**Quy tắc chung:** dùng `N_EVAL=300` (MATH ~7× chậm hơn GSM8K); bỏ tài khoản
`truongdv006` (đã khoá), dự phòng `khunht`/`dnglethnh`/`tbmdemi`; báo nhau trước khi chạy
để không trùng tài khoản (tối đa 2 vòng song song trên 19 tài khoản). Mỗi người nộp
`*_results.json` + một mục báo cáo; Người 1 tổng hợp thành bức tranh chung: *"phối hợp
multi-agent nên động và có căn cứ, không nên tĩnh và chay."*

Xem thêm trình tự chạy trong [`shapley/WORK_SPLIT.md`](shapley/WORK_SPLIT.md).
