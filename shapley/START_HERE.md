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

Thư mục khác: `docs/` (báo cáo `FINDINGS.md` + phân công `WORK_SPLIT.md`),
`results_summary/` (các file JSON kết quả nhỏ), `probe7b/` (kernel thử tải model 7B).

## Cài đặt một lần

```bash
pip install "kaggle>=2.0" sympy    # sympy để chấm đáp án MATH (tương đương đại số)
# tạo file accounts.txt trong thư mục shapley/ (mỗi dòng: USERNAME TOKEN), đã .gitignore
#   hoặc trỏ tới file khác: export ACCOUNTS_FILE=/duong/dan/accounts.txt
```
Đường dẫn trong code là **tương đối** (theo vị trí file), nên clone về máy nào cũng chạy.

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

Mỗi người phụ trách một hypothesis (chi tiết trong [`../HYPOTHESES.md`](../HYPOTHESES.md)).
Cả 4 đều có thể lấy kết quả tuần-1 **ngay từ dữ liệu đã có** trong `results_*/` (không cần
chạy Kaggle lại):

| Người | Hypothesis | File để đọc/bắt đầu | Tuần 1 làm gì |
|---|---|---|---|
| **1 · Nguyên** | H1 Router động | tạo `analysis/router.py` | đọc vector đúng/sai 16 tổ hợp trong `results_m1/*/preds.json`, dựng router heuristic |
| **2** | H2 Negative transfer | tạo `analysis/flip_analysis.py` | đo tỉ lệ tổ hợp làm answer đúng→sai từ `results_m1/*/preds.json` |
| **3** | H3 Topology graph | tạo `analysis/interaction.py` | tính ma trận tương tác 4×4 từ 16 accuracy đã có |
| **4** | H4 Grounded verifier | sửa `pipeline/template_math.py` | thêm verifier chạy sympy, rồi deploy như mục "Chạy thử" |

> Mẹo đọc dữ liệu: mỗi `results_<round>/<mã tổ hợp>/preds.json` là danh sách
> `{gold, pred, correct}` theo từng câu; `<mã tổ hợp>` là 4 bit `PSVA` (vd `1011` =
> Planner+Verifier+Aggregator). `results_m1/` là baseline MATH đồng nhất 1.5B.

Có gì chưa rõ, xem [`../README.md`](../README.md) (tổng quan + kết quả) hoặc
[`docs/FINDINGS.md`](docs/FINDINGS.md) (báo cáo chi tiết).
