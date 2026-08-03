# BẮT ĐẦU TỪ ĐÂY 👋

Chào mừng vào phần code. Đọc file này trước, đừng lo folder nhiều — quy trình chỉ có
**3 bước** và mỗi thư mục ứng với đúng một bước.

## Luồng chạy (3 bước)

```
pipeline/  →  deploy/  →  analysis/
(định nghĩa    (đẩy lên      (tính Shapley,
 pipeline       Kaggle,        bootstrap,
 4 agent)       thu kết quả)   chấm điểm)
```

1. **`pipeline/`** — định nghĩa hệ 4 agent (Planner/Solver/Verifier/Aggregator). Mỗi
   `template_*.py` là một biến thể (GSM8K, MATH, hoặc bản nâng 1 vai trò lên 7B). **Bạn
   sửa prompt/logic agent ở đây.**
2. **`deploy/`** — sinh 16 (hoặc 8) tổ hợp vai trò, đẩy mỗi tổ hợp thành 1 kernel Kaggle
   (`orchestrate_*.py`), rồi thu kết quả về (`sync_once.py`). **Bạn chạy thí nghiệm ở đây.**
3. **`analysis/`** — từ kết quả đã thu, tính giá trị Shapley (`shapley*.py`), khoảng tin
   cậy (`bootstrap*.py`), chấm lại điểm MATH (`regrade_math.py`). **Bạn phân tích ở đây.**

Thư mục khác: `docs/` (báo cáo `FINDINGS.md`), phân công ở `../PROJECT_PLAN.md`,
`results_summary/` (các file JSON kết quả nhỏ), `probe7b/` (kernel thử tải model 7B).

## Cài đặt một lần

```bash
pip install "kaggle>=2.0" sympy matplotlib pandas   # sympy để chấm MATH; matplotlib/pandas để vẽ
# Chỉ ai chạy Kaggle mới cần accounts.txt. Người phân tích (P2/P3/P4) BỎ QUA bước này —
# dữ liệu đã có sẵn trong results_*/.
```
Đường dẫn trong code là **tương đối** (theo vị trí file), nên clone về máy nào cũng chạy.

## Chạy Kaggle với **1 API key** (nếu tự tái lập)

Không cần nhiều tài khoản — 1 key vẫn chạy được, chỉ là **tuần tự** (chậm hơn).

1. Lấy key: kaggle.com → Settings → API → *Create New Token* → tải về `kaggle.json`
   (`{"username": "...", "key": "..."}`).
2. Tạo `shapley/accounts.txt` **một dòng**: `<username> <key>`.
3. Chạy như bình thường — orchestrator tự **round-robin**, đẩy cả 16 tổ hợp lên chính key đó
   (mỗi tổ hợp một slug riêng). Kaggle xếp hàng, chạy ~1–2 kernel cùng lúc; `sync_once.py`
   thu dần khi từng cái xong.
4. **MATH chậm** (~1 tiếng/tổ hợp) → 1 key nên dùng **`N_EVAL=100`–`150`** cho vừa giới hạn
   12h/kernel và ~30 GPU-giờ/tuần. GSM8K nhanh, để `N_EVAL=300` thoải mái.

Có bao nhiêu key thì bỏ bấy nhiêu dòng vào `accounts.txt` — 1 dòng chạy tuần tự, 16 dòng chạy
song song. Không có dòng nào ⇒ chỉ làm được phần phân tích trên data đã tải.

## Chạy thử một vòng đầy đủ (ví dụ MATH baseline)

```bash
cd shapley
ROUND=m1 N_EVAL=300 python deploy/orchestrate_math.py   # đẩy 16 tổ hợp lên Kaggle
ROUND=m1 python deploy/sync_once.py                     # lặp lại tới khi REMAINING 0
ROUND=m1 python analysis/regrade_math.py                # chấm lại (chỉ MATH)
ROUND=m1 python analysis/shapley.py                     # tính Shapley
ROUND=m1 python analysis/bootstrap.py                   # khoảng tin cậy
```

## 4 người bắt đầu từ đâu

Phân công đầy đủ (mảng, sản phẩm, mục báo cáo, lộ trình) trong
[`../PROJECT_PLAN.md`](../PROJECT_PLAN.md). Cả 4 đều có thể bắt đầu tuần-1 **ngay từ dữ liệu
đã có** trong `results_*/` (không cần chạy Kaggle lại):

| Người | Mảng | File để bắt đầu | Tuần 1 làm gì |
|---|---|---|---|
| **1 · Nguyên** | Thí nghiệm + tổng hợp | `deploy/orchestrate_math_role7b.py` | chạy `mA/mV/mP`, ghép bảng master vai×khó×năng-lực |
| **2** | Chẩn đoán | `analysis/signed_shapley.py` (đã có) | đọc φ⁺/φ⁻ + đọc `results_m1/*/preds.json` tìm ví dụ answer đúng→sai |
| **3** | Hiệu quả | tạo `analysis/router.py` | dựng router heuristic + Pareto acc–compute từ 16 tổ hợp có sẵn |
| **4** | Method + Related Work | `analysis/shapley.py`, `grade_math.py` | viết Method + Related Work; chạy 1 baseline self-consistency |

> Mẹo đọc dữ liệu: mỗi `results_<round>/<mã tổ hợp>/preds.json` là danh sách
> `{gold, pred, correct}` theo từng câu; `<mã tổ hợp>` là 4 bit `PSVA` (vd `1011` =
> Planner+Verifier+Aggregator). `results_m1/` là baseline MATH đồng nhất 1.5B.

Có gì chưa rõ, xem [`../README.md`](../README.md) (tổng quan + kết quả) hoặc
[`docs/FINDINGS.md`](docs/FINDINGS.md) (báo cáo chi tiết).
