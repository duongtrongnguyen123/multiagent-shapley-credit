# Kế hoạch đồ án & Phân công (bản chốt)

> Đồ án môn NLP. Nguồn phân công **duy nhất** — thay cho các bản kế hoạch cũ.

## Hướng đồ án

**Audit thực nghiệm đóng góp vai trò trong hệ multi-agent LLM giải toán.** Dùng giá trị
Shapley chính xác (+ phân rã có dấu) để đo mỗi vai trò (Planner/Solver/Verifier/Aggregator)
đóng góp bao nhiêu, và đóng góp đó đổi thế nào theo **độ khó** (GSM8K ↔ MATH) và **năng lực
model** (1.5B ↔ 7B).

Tiêu đề tạm: *"Who Actually Helps? Auditing Role Contributions in Multi-Agent LLM Reasoning."*

**Câu hỏi nghiên cứu**
- **RQ1** — mỗi vai trò đóng góp bao nhiêu? (Shapley)
- **RQ2** — thứ hạng có đảo theo độ khó và năng lực không?
- **RQ3** — φ (net) che giấu gì? (signed Shapley → agent "hỗn loạn")
- **RQ4** — có tận dụng biến thiên theo câu để chạy rẻ hơn không? (oracle / router)

Định vị (Related Work, viết trung thực): đây là một **empirical audit + công cụ tái lập**,
*áp dụng* các lăng kính đã có (Shapley, signed decomposition), **không** phải solution
concept mới. Đối chiếu: Shapley-Coop, SHARP, "When & Why Does MAD Fail", DyLAN.

## Đã hoàn thành (≈70% hạ tầng)

✅ Shapley GSM8K (4 vòng: đồng nhất + 3 vòng 7B) · ✅ MATH baseline `m1` (chấm sympy) ·
✅ signed Shapley (`analysis/signed_shapley.py`) · ✅ grader sympy + bootstrap CI ·
✅ oracle +19 điểm · ✅ repo tái lập. **Còn lại: chạy nốt capacity MATH + phân tích + hình + viết.**

## Phân công 4 người

| Người | Mảng | Việc cụ thể | Mục báo cáo |
|---|---|---|---|
| **1 · Nguyên** | Thí nghiệm + Tổng hợp | Chạy nốt **mA / mV / mP** trên MATH → hoàn tất lưới *vai trò × độ khó × năng lực*; ghép **bảng master**; viết Intro + mục RQ2 (ranking reversal); chủ trì ghép báo cáo | Intro, RQ2 Results |
| **2** | Chẩn đoán (Analysis) | **signed Shapley** (chaotic agent, RQ3) + đo negative transfer + **đọc completion thật** lấy ví dụ sycophancy | Analysis / Diagnostics |
| **3** | Hiệu quả (Applied) | Build **`analysis/router.py`** + đường **Pareto accuracy–compute** (RQ4, dùng oracle +19) | Efficiency / Application |
| **4** | Method + Related Work | Viết Method (Shapley, grader, CI, thiết kế pipeline) + **Related Work** trung thực; chạy 1 baseline **self-consistency** để so; phụ lục tái lập | Method, Related Work |

Cân bằng: P1 & P3 nặng *chạy/xây*; P2 & P4 nặng *phân tích/viết*. Mỗi người ≈ 1 thí
nghiệm-hoặc-build + 1 mục báo cáo + hình của phần mình.

## "Money figures" cần có (chỗ đang thiếu, ăn điểm nhìn)
1. Bar chart Shapley từng benchmark. 2. Heatmap *vai trò × độ khó × năng lực*.
3. Cột chồng φ⁺/φ⁻ (chaotic Planner). 4. Bảng accuracy 16 tổ hợp. 5. Pareto oracle/router.

## Lộ trình 3 tuần
- **Tuần 1** — P1 chạy mA/mV/mP; P2 & P3 làm phân tích + hình từ data sẵn có; P4 dựng Related Work.
- **Tuần 2** — ghép kết quả, viết các mục; P3 xong router; P4 xong baseline self-consistency.
- **Tuần 3** — hình cuối + viết + đọc soát.

## Quy tắc vận hành (Kaggle)
- Bắt đầu ở `shapley/` — đọc [`shapley/START_HERE.md`](shapley/START_HERE.md).
- Lệnh: `BIG=<P|S|V|A> ROUND=m<X> N_EVAL=300 python deploy/orchestrate_math_role7b.py` →
  `ROUND=m<X> python deploy/sync_once.py` → `BIG=<X> ROUND=m<X> python analysis/shapley_role7b.py`.
- **Dùng `N_EVAL=300`** (MATH ~7× chậm hơn GSM8K). **Bỏ tài khoản `truongdv006`** (đã khoá),
  dự phòng `khunht`/`dnglethnh`/`tbmdemi`. Báo nhau trước khi chạy — tối đa 2 vòng song song
  trên 19 tài khoản. Không dùng vòng lặp nền để poll (bị kill); gọi `sync_once.py` đồng bộ.
