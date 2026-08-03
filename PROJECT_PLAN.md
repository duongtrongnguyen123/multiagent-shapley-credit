# Kế hoạch đồ án & Phân công (bản chốt)

> Đồ án môn NLP. Nguồn phân công **duy nhất**. Đọc hết file này trước khi bắt tay.

## Hướng đồ án

**Audit thực nghiệm đóng góp vai trò trong hệ multi-agent LLM giải toán.** Dùng giá trị
Shapley chính xác (+ phân rã có dấu) để đo mỗi vai trò (Planner/Solver/Verifier/Aggregator)
đóng góp bao nhiêu, và đóng góp đó đổi thế nào theo **độ khó** (GSM8K ↔ MATH) và **năng lực
model** (1.5B ↔ 7B).

Tiêu đề tạm: *"Who Actually Helps? Auditing Role Contributions in Multi-Agent LLM Reasoning."*

**Câu hỏi nghiên cứu:** RQ1 — mỗi vai trò đóng góp bao nhiêu (Shapley)? · RQ2 — thứ hạng có
đảo theo độ khó và năng lực không? · RQ3 — φ (net) che giấu gì (signed → agent "hỗn loạn")? ·
RQ4 — tận dụng biến thiên theo câu để chạy rẻ hơn được không (oracle/router)?

Định vị (viết trung thực): đây là **empirical audit + công cụ tái lập**, *áp dụng* các lăng
kính đã có (Shapley, signed decomposition), **không** phải solution concept mới.

## Đã hoàn thành (≈70% hạ tầng, khỏi làm lại)

✅ Shapley GSM8K (4 vòng) · ✅ MATH baseline `m1` (chấm bằng grader sympy) ·
✅ signed Shapley (`analysis/signed_shapley.py`) · ✅ grader sympy + bootstrap CI ·
✅ oracle +19 điểm · ✅ repo tái lập, đường dẫn portable. Còn lại: **chạy nốt capacity MATH +
phân tích + hình + viết.**

---

## 🚩 BẮT ĐẦU TỪ ĐÂU (mọi người đọc)

1. `git clone` repo, mở `shapley/START_HERE.md` — hiểu luồng 3 bước `pipeline → deploy → analysis`.
2. **Dữ liệu của bạn nằm sẵn trong `shapley/results_*/`** (đã tải về, không cần chạy lại gì).
   Mỗi `results_<vòng>/<mã tổ hợp>/preds.json` = danh sách `{gold, pred, correct}` theo từng
   câu; mã tổ hợp là 4 bit `PSVA` (vd `1011` = Planner+Verifier+Aggregator).
3. **Chỉ Người 1 (Nguyên) đụng tới Kaggle.** Người 2/3/4 làm hoàn toàn trên data đã tải —
   **không cần tài khoản Kaggle, không cần chạy gì trên cloud.**
4. Tìm tên mình trong bảng phân công → làm theo timeline hôm-nay/ngày-mai bên dưới.
5. Cài môi trường: `pip install sympy matplotlib pandas`.

## Phân công 4 người

| Người | Mảng | Việc cụ thể | Mục báo cáo |
|---|---|---|---|
| **1 · Nguyên** | Thí nghiệm + Tổng hợp | Chạy nốt **mA/mV/mP** (7B cho từng vai trò) trên MATH → hoàn tất lưới *vai trò × độ khó × năng lực*; ghép **bảng master**; viết Intro + RQ2 | Intro, Results |
| **2** | Chẩn đoán (Analysis) | **signed Shapley** (chaotic agent, RQ3) + đo negative transfer; hình φ⁺/φ⁻ | Analysis |
| **3** | Hiệu quả (Applied) | Build **`analysis/router.py`** + đường **Pareto accuracy–compute** (RQ4, dùng oracle +19) | Efficiency |
| **4** | Method + Related Work | Viết Method (Shapley/grader/CI) + **Related Work** trung thực; baseline **self-consistency** | Method, Related Work |

---

## ⏱️ TIMELINE CHI TIẾT — HÔM NAY & NGÀY MAI

### Người 1 · Nguyên — Thí nghiệm + Tổng hợp
**Hôm nay**
- [ ] Chuẩn bị môi trường Kaggle + `accounts.txt` (chỉ mình bạn cần cái này).
- [ ] Khởi động vòng **mA** (7B Aggregator — quan trọng nhất vì Aggregator dẫn đầu MATH):
      `BIG=A ROUND=mA N_EVAL=300 python deploy/orchestrate_math_role7b.py`.
- [ ] Trong lúc chờ (~1–2 tiếng/lượt), dựng **khung bảng master**: gom φ của GSM8K (4 vòng đã
      có) + MATH `m1` vào một bảng *vai trò × {GSM8K,MATH} × {1.5B,7B}*.
- [ ] Poll kết quả: `ROUND=mA python deploy/sync_once.py` (gọi lại vài lần, đừng dùng vòng nền).

**Ngày mai**
- [ ] Thu xong mA → `BIG=A ROUND=mA python analysis/shapley_role7b.py`, điền vào bảng master.
- [ ] Khởi động tiếp **mV** rồi **mP** (lần lượt hoặc song song nếu đủ tài khoản).
- [ ] Viết nháp **Intro** (bối cảnh + 4 RQ) và khung mục **Results (RQ2)** — để sẵn bảng/hình trống.

### Người 2 · Chẩn đoán (signed Shapley + negative transfer)
**Hôm nay**
- [ ] Chạy `ROUND=m1 python analysis/signed_shapley.py` và `ROUND=r1 …` (GSM8K) → chép lại
      bảng φ⁺/φ⁻/η. Điểm nhấn: **Planner φ≈0 nhưng sửa ~10%, phá ~9% (churn ~19%)**.
- [ ] Viết script nhỏ `analysis/flip_analysis.py`: từ `results_m1/*/preds.json`, đếm cho từng
      cặp (tổ hợp S, tổ hợp S∪{i}) số câu **đúng→sai** và **sai→đúng** → xác định vai trò/vị
      trí nào gây "phá" nhiều nhất (định lượng cái 10.6%).
- [ ] Nháp đoạn *"credit ≠ reliability: Shapley cổ điển không phân biệt agent vô dụng với agent hỗn loạn."*

**Ngày mai**
- [ ] Làm **hình cột chồng φ⁺ / φ⁻** cho 4 vai trò (matplotlib), cả GSM8K và MATH cạnh nhau.
- [ ] Bảng flip-rate theo vai trò (ai phá nhiều nhất). Viết hoàn chỉnh mục **Analysis**.
- [ ] (Nếu cần ví dụ định tính) báo Người 1 bật lưu completion cho 1 vòng nhỏ để trích 3–5 ví dụ sycophancy.

### Người 3 · Hiệu quả (router + Pareto)
**Hôm nay**
- [ ] Viết `analysis/router.py`: nạp vector đúng/sai của 16 tổ hợp `results_m1/`; tính (a) trần
      **oracle** (mỗi câu chọn tổ hợp tốt nhất), (b) một **router heuristic** dựa độ đồng thuận
      giữa các vai trò. In: accuracy router vs pipeline tĩnh vs oracle, kèm số lần gọi model.
- [ ] Tính bảng **accuracy vs #lần-gọi-model** cho cả 16 tổ hợp (để vẽ Pareto).

**Ngày mai**
- [ ] Vẽ **đường Pareto accuracy–compute**: chấm 16 tổ hợp + điểm router + trần oracle.
- [ ] Thêm 2 mốc so sánh: "luôn chạy full" và "chỉ Solver". Viết mục **Efficiency** (thông điệp:
      *coordination có đáng compute không, và router lấy lại được bao nhiêu của +19 điểm*).

### Người 4 · Method + Related Work
**Hôm nay**
- [ ] Đọc `shapley/docs/FINDINGS.md` + file này. Viết mục **Method**: công thức Shapley, thiết
      kế 16 tổ hợp, grader sympy (`analysis/grade_math.py`), bootstrap CI, cấu hình model/decode.
- [ ] Bắt đầu **Related Work**: đọc abstract 4 bài — Shapley-Coop, SHARP, "When & Why Does MAD
      Fail", DyLAN — ghi 1–2 câu mỗi bài + mình khác chỗ nào (empirical audit, không phải method).

**Ngày mai**
- [ ] Hoàn tất bản nháp **Related Work** (nửa trang, trung thực).
- [ ] Thiết kế baseline **self-consistency** (lấy 4 mẫu Solver, majority vote) — viết script hoặc
      phối hợp Người 1 chạy 1 vòng nhẹ; để so "coordination vs self-consistency" ở cùng ngân sách.
- [ ] Soạn **phụ lục tái lập** (lệnh chạy, seed, phiên bản).

---

## "Money figures" cần có (chỗ đang thiếu, ăn điểm nhìn)
1. Bar chart Shapley từng benchmark. 2. Heatmap *vai trò × độ khó × năng lực*.
3. Cột chồng φ⁺/φ⁻ (chaotic Planner). 4. Bảng accuracy 16 tổ hợp. 5. Pareto oracle/router.

## Lộ trình 3 tuần (tổng quan)
- **Tuần 1** — P1 chạy mA/mV/mP; P2 & P3 làm phân tích + hình từ data sẵn; P4 dựng Related Work.
- **Tuần 2** — ghép kết quả, viết các mục; P3 xong router; P4 xong baseline.
- **Tuần 3** — hình cuối + viết + đọc soát.

## Quy tắc chạy Kaggle (chỉ Người 1)
- Xem [`shapley/START_HERE.md`](shapley/START_HERE.md). Dùng `N_EVAL=300` (MATH ~7× chậm hơn
  GSM8K). Gọi `deploy/sync_once.py` đồng bộ, **không** dùng vòng lặp nền (bị kill khi đổi lượt).
