# MỤC LỤC TÀI LIỆU

> `docs/` có **41 tệp**. File này là **cửa vào duy nhất** — đừng đọc mò.
> Muốn hiểu **code** thì đọc `../START_HERE.md`. Muốn hiểu **kết quả** thì đọc file này.

---

## Đọc theo mục đích

| bạn muốn… | đọc theo thứ tự này |
|---|---|
| **hiểu nhanh dự án làm gì** | `INTRO.md` → `../../README.md` → `TONG_HOP.md` |
| **viết báo cáo cuối kỳ** | `BAO_CAO_CAU_TRUC.md` → `HUONG_DAN_CONG_TAC.md` |
| **tra một con số có được trích không** | `HUONG_DAN_CONG_TAC.md` §1–§2 → `PREREGISTRATION.md` |
| **hiểu vai nào trong pipeline có giá trị** | `RESULTS.md` → nhóm *Vai trò & Credit* bên dưới |
| **hiểu vì sao SỬA thua CHỌN** | `TONG_HOP.md` → `IDEAS.md` vòng #182, #185, #197 |
| **lặp lại một thí nghiệm** | `PREREGISTRATION.md` (tìm mã H…) → `../pipeline/` → `../deploy/` |

---

## 1. Khung & tổng hợp *(đọc trước)*

| tệp | nội dung |
|---|---|
| **`TONG_HOP.md`** | **Khung `value = H × κ − D`** + ba mệnh đề M1/M2/M3. Lõi lý thuyết. |
| `INTRO.md` | Giới thiệu ngắn |
| `FINDINGS.md` | Tổng hợp phát hiện (bản sớm) |
| **`RESULTS.md`** | **Bảng kết quả chính của mảng nhóm** — có sàn nhiễu và thanh sai số 5 fold. **Đọc mục 0 trước mọi con số.** |

## 2. Báo cáo cuối kỳ *(đang làm)*

| tệp | nội dung |
|---|---|
| **`BAO_CAO_CAU_TRUC.md`** | Cấu trúc báo cáo bản 2 — luận điểm hợp nhất, 9 mục, 7 hình, phân công |
| **`HUONG_DAN_CONG_TAC.md`** | Bàn giao: **ba tầng bằng chứng**, bảng số chốt, "đừng viết X hãy viết Y" |

## 3. Phương pháp & kỷ luật *(mảng Nguyên)*

| tệp | nội dung |
|---|---|
| **`PREREGISTRATION.md`** | Mọi **bảng khoá diễn giải**, commit **trước** khi chạy. Tra ở đây để biết một kết quả thuộc tầng nào. |
| `IDEAS.md` | Nhật ký **201 vòng**. Tra theo số vòng. |
| `QUY_TRINH_VONG_LAP.md` | **37 luật quy trình**, mỗi luật rút từ một thất bại thật |
| `RESULT_SEALS.md` | Hash artifact ghi **trước** khi đọc số |

## 4. Vai trò & Credit assignment *(mảng Đức)*

| nhóm | tệp |
|---|---|
| **Credit / RL** | `CREDIT_RL_RESULTS.md` · `ORPO_RESULTS.md` · `ORPO_AGGREGATOR.md` · `ORPO_VS_H23.md` |
| **Phân tích vai** | `ROLE_SPECIALIZATION.md` · `BLAME_ANALYSIS.md` · `AGGREGATOR_EXPLAINED.md` · `AGG_FORMAT_CHECK.md` |
| **Planner** | `PLANNER_ROUND_RESULTS.md` · `PLANNER_COPYCAT.md` · `DEBATE_PLANNER.md` |
| **Verifier / Judge** | `VERIFIER_RESCUE.md` · `VERIFIER_DIVERSITY.md` · `JUDGE_QUALITY.md` · `SOLVEJUDGE.md` · `SOLVEJUDGE_V2.md` · `SOLVEJUDGE_MATH.md` |
| **Suy luận ngược** | `BACKWARD_SOLVER.md` · `BACKWARD_REASONING.md` · `BACKWARD_FEASIBILITY.md` |
| **Khác** | `DIFFICULTY_STRATA.md` · `LENGTH_ROUTER.md` · `FEWSHOT_ROLES.md` · `PROMPT_SWAP.md` · `EXTRA_PASS_FINDING.md` · `REUSE_DISCREPANCY.md` · `SELFLEVEL_FAIL.md` |
| **Công trình liên quan** | **`RELATED_BASELINES.md`** · **`RELATED_PIPELINE.md`** ← dùng cho §2 báo cáo |

## 5. Phân tích khác

| tệp | nội dung |
|---|---|
| `nlp_trace_analysis.md` | Phân tích trace |

---

## ⚠️ Ba điều phải biết trước khi trích bất kỳ con số nào

1. **Nhóm dùng HAI chuẩn kiểm chứng.** Mảng nhóm (`RESULTS.md`, docs của Đức) dùng **thanh sai số
   5 fold** với **ngưỡng nhiễu 5 điểm**. Mảng Nguyên (`PREREGISTRATION.md`) dùng **đăng ký trước +
   cổng + niêm phong**. Cả hai đều hợp lệ, **nhưng không được đặt cùng một tầng mà không nói rõ**.
   Xem `HUONG_DAN_CONG_TAC.md` §4b.
2. **`res_*.json` có thể ghi `VOID` mà kết quả vẫn HỢP LỆ** — nếu đăng ký trước đã sửa cổng
   *trước khi đọc*. Trường hợp đã biết: **H88e**, **H92b** (cổng `n ≥ 480` bất khả thi trên dải
   464 bài; sửa thành `n ≥ 460` ở `#97-d`/`#102-b`).
3. **Thư mục `results_*/` và `res_*/` KHÔNG nằm trong git** (bị `.gitignore` chặn, cố ý — chúng
   nặng hàng trăm MB). Artifact thô chỉ có **trên máy local**. Hash của chúng thì có trong
   `RESULT_SEALS.md`, nên vẫn kiểm được tính toàn vẹn.

---

## Không nằm trên `main`

| thứ | ở đâu | vì sao quan trọng |
|---|---|---|
| `EFFICIENCY.md` (210 dòng, Tùng Dương) | nhánh **`nguoi3-router`** | Bảng accuracy-vs-cost + Consensus Router. **Cần cho §5.3 của báo cáo.** |
| `analysis/router.py` | nhánh **`nguoi3-router`** | Code sinh ra bảng trên |

⇒ **Cần quyết định:** gộp `nguoi3-router` vào `main`, hay để nguyên. Đây là nhánh của Tùng Dương
nên **để chủ nhánh quyết**.
