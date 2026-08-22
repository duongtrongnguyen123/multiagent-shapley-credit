# Đánh giá đóng góp của từng vai trò trong hệ suy luận đa tác tử

Báo cáo bài tập lớn — Xử lý ngôn ngữ tự nhiên (INT3406), Trường Đại học Công nghệ, ĐHQGHN.
Nhóm 13: Dương Trọng Nguyên, Trương Đình Đức, Trần Tùng Dương, Lê Hoàng Quân.

| | |
|---|---|
| **Báo cáo** | [`report/BAO_CAO_NHOM13.pdf`](report/BAO_CAO_NHOM13.pdf) — 22 trang |
| **Slide** | [`report/SLIDE_BAO_CAO.pdf`](report/SLIDE_BAO_CAO.pdf) |
| **Mã nguồn chính** | `analysis/`, `pipeline/`, `deploy/`, `tests/` — xem bảng dưới |
| **Toàn bộ thực nghiệm** (151 kernel, 40 tài liệu, kết quả từng lần chạy) | nhánh [`archive`](../../tree/archive) |

---

## Khảo sát này hỏi gì

Các hệ LLM đa tác tử chia việc cho nhiều vai trò — lập kế hoạch, giải, kiểm tra, tổng hợp — với
kỳ vọng tốt hơn một model đơn lẻ. Câu hỏi của chúng tôi là: **lợi ích đo được đến từ cơ chế
phối hợp, hay chỉ từ việc gọi model nhiều lần hơn?**

Để trả lời, mọi phép đo được đặt dưới ba phép kiểm soát mà các nghiên cứu thường bỏ qua:

| Kiểm soát | Nếu thiếu | Hệ quả |
|---|---|---|
| Chi phí tính toán | So hệ nhiều lượt gọi với model chạy một lượt | Đánh giá **cao** |
| Mốc so sánh | Chỉ so với model yếu bị sửa, không so với model mạnh đơn lẻ | Đánh giá **cao** |
| Mẫu số | Tính trung bình cả trên bài không cơ chế nào đổi được | Đánh giá **thấp** |

Ba sai lệch không cùng chiều, nên phải áp đồng thời.

## Kết quả chính

- **Lợi ích không phổ quát.** Pipeline bốn vai hơn 11,2 điểm trên GSM8K nhưng kém 6,0 điểm
  trên MATH, trong khi tốn thêm 2,9× đến 6,63× token.
- **Giá trị nằm ở số lần sinh, không ở cơ chế phối hợp.** Cho model giải lại mà không đọc phê
  bình của verifier cho kết quả bằng đúng khi có đọc (0,453 so với 0,453).
- **Đổi mốc so sánh làm đảo dấu kết luận.** So với model yếu, hiệu ứng tăng theo chênh lệch
  năng lực; so với model mạnh chạy độc lập, hiệu ứng giảm và xuống dưới 0.
- **Nội dung artifact quyết định dấu của hiệu ứng.** Cho model mạnh xem bài làm của model yếu:
  artifact đúng cho +3,8 điểm, artifact sai cho −27,2 điểm. Giao thức sinh-rồi-sửa hoạt động
  như một ống dẫn đáp án, không phải bộ sửa lỗi.
- **Bước kiểm chỉ có giá trị khi người kiểm mạnh hơn.** Verifier cùng cỡ với solver đạt độ
  chính xác can thiệp 56–59%; verifier lớn hơn đạt 98%.
- **Bảy phương pháp huấn luyện vai trò đều tìm ra lối tắt của hàm mục tiêu**, không cái nào cải
  thiện thật.

Mỗi cấu hình được đo trên 500 bài chia năm fold; ngưỡng hiệu dụng khoảng 3,3 điểm.
Benchmark: GSM8K, MATH, MBPP, HumanEval. Model từ 0,5B đến 32B tham số.

## Mã nguồn

Nhánh này giữ các file sinh ra số liệu được trích trong báo cáo.

| File | Dùng cho |
|---|---|
| `analysis/shapley.py`, `shapley_role7b.py`, `signed_shapley.py`, `interaction.py` | Giá trị Shapley của bốn vai và chỉ số tương tác (§5.3) |
| `analysis/role_specialization.py`, `trace_novelty.py` | Lưới hành vi vai trò đọc từ trace (§5.4) |
| `analysis/difficulty_strata.py` | Phân tầng theo số lần đúng (§5.6) |
| `analysis/merge_pairs.py` | Hồi quy theo chênh lệch năng lực (§5.7–§5.8) |
| `analysis/router.py` + `tests/` | Định tuyến và phân tích Pareto (§5.10) |
| `analysis/bootstrap.py`, `bootstrap_het.py`, `grade_math.py`, `master_table.py` | Thống kê, chấm điểm, bảng tổng hợp |
| `pipeline/baseline_kernel.py`, `noisefloor_kernel.py`, `budget_kernel.py` | Mốc so sánh, mức dao động nền, kiểm soát ngân sách (§5.1–§5.2, §5.5) |
| `pipeline/roleablate_kernel.py`, `promptswap_folds_kernel.py` | 16 tổ hợp bật/tắt vai, hoán vị prompt (§5.3–§5.4) |
| `pipeline/exposure_math_kernel.py`, `exposure_dose_kernel.py`, `capacity_poison_kernel.py` | Thí nghiệm tác động artifact (§5.9) |
| `pipeline/execverify_kernel.py`, `gate_kernel.py`, `injected_classifier_kernel.py` | Tín hiệu kiểm chứng và hai cổng oracle (§5.10) |
| `pipeline/credit_rl_kernel.py`, `orpo_kernel.py`, `maporl_kernel.py` | Huấn luyện vai trò (§5.11) |
| `pipeline/crossfamily_kernel.py` | Đối chứng khác họ model (§5.7) |
| `pipeline/template.py`, `deploy/` | Khung kernel dùng chung, điều phối và thu kết quả |

```bash
pytest tests/ -q                    # test cho bộ định tuyến
python analysis/shapley.py --help
```

## Biên dịch lại báo cáo

```bash
cd report && tectonic -X compile BAO_CAO_NHOM13.tex --outdir .
```

## Nhánh `archive`

Nhánh `archive` giữ nguyên trạng toàn bộ phần thực nghiệm: 151 kernel chạy trên Kaggle
(`shapley/pipeline/`), 89 script điều phối (`shapley/deploy/`), 24 script phân tích
(`shapley/analysis/`), 40 tài liệu kết quả (`shapley/docs/`) và các file kết quả tóm tắt
(`shapley/res_*/`). Repo không chứa token hay tên tài khoản Kaggle; các bản dump trace thô
cũng không được commit vì tái sinh được từ `pipeline/`.
