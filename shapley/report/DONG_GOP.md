# Danh mục đóng góp của cả nhóm

Liệt kê đầu việc, **chưa gán tên** — để trưởng nhóm tự phân bổ. Mỗi mục có kèm bằng chứng
(thư mục kết quả / tài liệu / mã nguồn) để đối chiếu khi phân công.

Quy mô tổng: 789 commit · 273 thư mục kết quả (111 đã commit, 162 chạy cục bộ) ·
39 tài liệu phân tích · 151 kernel · 89 script điều phối · 24 script phân tích ·
báo cáo 21 trang (7 mục, 16 bảng, 4 hình, 24 trích dẫn) · slide 18 trang.

---

## A. Khối thí nghiệm

| # | Đầu việc | Sản phẩm | Bằng chứng |
|---|---|---|---|
| A1 | **Giá trị Shapley theo vai trò** — chạy đủ $2^4=16$ tổ hợp bật/tắt bốn vai trên GSM8K và MATH; tính khoảng tin cậy bootstrap; nâng riêng từng vai lên 7B để đo độ nhạy theo năng lực | Bảng 4; kết luận planner âm ở 1.5B lật dương ở 7B | `results_mP/mS/mV/mA`, `results_gS/gA`, `analysis/shapley.py`, `shapley_role7b.py` |
| A2 | **Chỉ số tương tác Shapley** — đo mức thay thế lẫn nhau giữa các vai | Kết luận $S/V/A$ thay thế nhau, không bổ sung | `analysis/interaction.py`, `signed_shapley.py`, `shapley_het.py` |
| A3 | **Shapley phân tầng theo độ trung thực thực thi** | Tách công của *nhãn vai trò* khỏi *chức năng thật* | `analysis/fidelity.py`, `extract_fidelity.py` |
| A4 | **Chuyên biệt hoá vai trò** — dựng lưới hành vi 2×2 (task × năng lực) đọc từ trace; đo tỷ lệ planner rò đáp án, solver không sinh số mới, aggregator tạo đáp án mới | Bảng 5; kết luận các vai không làm đúng chức năng được giao | `docs/ROLE_SPECIALIZATION.md`, `PLANNER_COPYCAT.md`, `PLANNER_ROUND_RESULTS.md`, `analysis/role_specialization.py`, `trace_novelty.py` |
| A5 | **Hoán vị prompt vai trò** — kiểm xem hành vi đến từ prompt hay từ vị trí trong pipeline | `docs/PROMPT_SWAP.md` | `res_sw_*` (4 cấu hình) |
| A6 | **Verifier có thật sự kiểm không** — Fix/Break, Intervention Accuracy, tiêm lỗi chữ số, quét lưới `V_gain` theo task × năng lực | Bảng 6, Bảng 7; IA chỉ 56–59% ở 1.5B | `docs/VERIFIER_DIVERSITY.md`, `VERIFIER_RESCUE.md`, `JUDGE_QUALITY.md`, `res_wv_*`, `res_vt_*` |
| A7 | **Hiệu chuẩn mức dao động nền** — chạy cùng một cấu hình trên 5 fold để biết ngưỡng hiệu dụng | Ngưỡng ~3,3 điểm, dùng xuyên suốt phần Kết quả | `res_nf_*` (4 ô), `results_fsfold`, `results_psfold` |
| A8 | **Kiểm soát ngân sách sinh** — giữ nguyên 8 lần sinh, chỉ đổi bộ tổng hợp; đối chứng `rerun` vs `loop` | Kết luận giá trị nằm ở số lần sinh, không ở nội dung phản hồi | `res_bs_*`, `res_sc8_*`, `res_rc_*`, `docs/EXTRA_PASS_FINDING.md` |
| A9 | **Aggregator và lỗi định dạng `boxed`** — phát hiện tỷ lệ trích được đáp án chỉ 73–81%, dựng cơ chế dự phòng | Sửa `A_gain` từ $-6{,}4$ thành $+0{,}8$ | `docs/AGGREGATOR_EXPLAINED.md`, `AGG_FORMAT_CHECK.md`, `res_af_m`, `res_agf_*` |
| A10 | **Kiểm soát mốc so sánh + đơn giá token** — so pipeline với model mạnh đơn lẻ, quy chi phí về FLOP thay vì đếm lượt gọi | Bảng 8; "rẻ hơn 12%" biến mất khi quy FLOP | `res_bl_*` (4 cấu hình), `res_cp_*` |
| A11 | **Kiểm soát mẫu số** — phân tầng câu hỏi theo số lần đúng trong 5 lần sinh, tách phần bất động theo cấu trúc | Bảng 11; 57% số câu không thể đổi kết quả | `docs/DIFFICULTY_STRATA.md`, `analysis/difficulty_strata.py` |
| A12 | **Số hạng $G$ và quy luật chênh lệch năng lực** — 6 model, 15 cặp có hướng trên MBPP; hồi quy | Bảng 12–13; hệ số âm, ngưỡng chênh $g^\ast$ | `res_pp_*`, `res_pa_*`, `analysis/merge_pairs.py`, `rebuild_pairs_k2.py` |
| A13 | **Kiểm chuyển miền** — dùng đường khớp MBPP dự báo MATH trên 3 cặp | Bảng 14; 2/3 trong khoảng, 1 cặp lệch hệ thống | `res_tr_*` (4 cấu hình) |
| A14 | **Thí nghiệm tác động artifact** ⭐ — thiết kế chốt trước, hai nhánh cùng lệnh giải, phân tầng theo nội dung artifact, bảng $2\times2$ | Hình 1, Bảng 15; $-27{,}2$ điểm trên tầng artifact sai | `res_ex_*` (4 cấu hình), `res_h59`, `res_h60` |
| A15 | **Khả năng khai thác $\kappa$** — `exec3` vs `llm3` trên HumanEval; hai cổng oracle; trần `oracle@k − maj@k` | Bảng 16; tín hiệu chắc chắn lấy gần trọn trần, tín hiệu học được thì không | `res_ev_he15`, `res_ev_he7`, `res_gate_*`, `res_pc_he` |
| A16 | **Bộ phân loại lỗi tiêm + định tuyến** — huấn luyện bộ phân loại, đo AUC, kiểm xem AUC cao có đổi thành điểm không | AUC 0,893 chỉ đổi $+2{,}4$ điểm | `results_injected_classifier`, `results_disc_leakfix_gsm8k/math`, `docs/LENGTH_ROUTER.md`, `analysis/length_router.py` |
| A17 | **GRPO trên verifier (3 biến thể)** — thưởng theo can thiệp, theo đáp án cuối, và cấu hình bất đối xứng thông tin | Ba lối tắt khác nhau; biến thể 3 đo đồng thời $+17{,}0$ và $-10{,}4$ | `res_h60`, `res_h61`–`res_h63` |
| A18 | **ORPO trên aggregator** | Chéo miền âm; khuếch đại tật chép ứng viên cuối | `docs/ORPO_AGGREGATOR.md`, `ORPO_RESULTS.md`, `ORPO_VS_H23.md` |
| A19 | **Credit-RL hai giai đoạn** — thưởng bằng phần đóng góp Shapley biên, rồi thiết kế chống lối tắt | 0/4 vai cải thiện; biến thể V-COND dương nhưng không chuyển miền | `docs/CREDIT_RL_RESULTS.md`, `analysis/credit_critic.py` |
| A20 | **MAPoRL đồng huấn luyện ba vai** | $+0{,}000$; aggregator nghẽn suốt quá trình | `res_h77`, `res_h79`, `res_h79b` |
| A21 | **Nhóm thí nghiệm suy luận ngược** (backward reasoning / backward solver) | 3 tài liệu; hướng không mang lại cải thiện | `results_backward`, `docs/BACKWARD_*.md` (3 file) |
| A22 | **Nhóm giải-rồi-chấm** (solve-then-judge, 3 vòng) | Biến thể vòng lặp thắng pipeline đủ vai trên MATH | `results_solvejudge`, `_v2`, `results_judge`, `docs/SOLVEJUDGE*.md` |
| A23 | **Phân rã bài toán và tự đánh giá mức độ** | Hai hướng âm, được ghi lại làm đối chứng | `results_decompose`, `results_selflevel`, `docs/SELFLEVEL_FAIL.md` |
| A24 | **Few-shot cho vai trò + phân tích quy trách lỗi** | `docs/FEWSHOT_ROLES.md`, `BLAME_ANALYSIS.md` | `analysis/blame_analysis.py` |
| A25 | **Phân tích trace bằng NLI** — đo mức trùng lặp ngữ nghĩa giữa các vai | `docs/nlp_trace_analysis.md` | `analysis/trace_nli.py`, `results_trace`, `results_trace2` |

⭐ = thí nghiệm chính của cả khảo sát.

**Còn dở:** $\Delta_{real}$ thiếu **một nhánh** (`R:R2`); 8/9 nhánh đã có kết quả, kernel đã vá OOM.

---

## B. Hạ tầng và vận hành

| # | Đầu việc | Quy mô |
|---|---|---|
| B1 | **Viết kernel thí nghiệm** — mỗi thí nghiệm một kernel chạy được trên Kaggle | 151 file trong `pipeline/` |
| B2 | **Hệ điều phối và thu kết quả** — phóng job, gộp shard, quản lý nhiều tài khoản | 89 file trong `deploy/` |
| B3 | **Xử lý hạ tầng Kaggle** — cổng ba trường metadata cho GPU, phiên bản CLI, đường mount dataset, giới hạn quota | Ghi trong `docs/QUY_TRINH_VONG_LAP.md` |
| B4 | **Công cụ chấm điểm** — chấm MATH, chấm lại, kiểm định dạng `boxed` | `analysis/grade_math.py`, `regrade_math.py`, `agg_format_check.py` |
| B5 | **Công cụ thống kê** — bootstrap, bootstrap phân tầng, bảng tổng hợp | `analysis/bootstrap.py`, `bootstrap_het.py`, `bootstrap_hetV.py`, `master_table.py` |
| B6 | **Đo chuẩn phần cứng** — so P100/T4/H100, đếm GPU, đo VRAM theo model | `res_bench_p100`, `res_bench_t4`, `res_gpucount`, `res_devmap`, `res_q7bench` |

---

## C. Phân tích và tài liệu

| # | Đầu việc | Quy mô |
|---|---|---|
| C1 | **Viết tài liệu kết quả cho từng thí nghiệm** | 39 file trong `docs/` |
| C2 | **Tài liệu tổng hợp toàn khảo sát** — `FINDINGS`, `RESULTS`, `TONG_HOP`, `INDEX` | 4 file, cập nhật liên tục |
| C3 | **Quy trình chốt trước và niêm phong kết quả** | `docs/PREREGISTRATION.md`, `RESULT_SEALS.md` |
| C4 | **Quy trình vòng lặp nghiên cứu** — cách sinh giả thuyết, chạy, ghi nhận | `docs/QUY_TRINH_VONG_LAP.md`, `IDEAS.md` |
| C5 | **Rà soát công trình liên quan** | `docs/RELATED_BASELINES.md`, `RELATED_PIPELINE.md` |
| C6 | **Truy vết mâu thuẫn số liệu giữa các lần chạy** | `docs/REUSE_DISCREPANCY.md` |

---

## D. Báo cáo

| # | Đầu việc | Trạng thái |
|---|---|---|
| D1 | Trang bìa — logo trường, 4 thành viên, mã lớp học phần | Xong |
| D2 | Lời cảm ơn | Xong |
| D3 | Tóm tắt (219 từ, không ký hiệu) | Xong |
| D4 | §1 Mở đầu — ví dụ dẫn nhập, ba vấn đề đo lường, bốn đóng góp | Xong |
| D5 | §2 Công trình liên quan — ba dòng nghiên cứu và vị trí của khảo sát | Xong |
| D6 | §3 Phương pháp đo lường — ba câu hỏi khung, đẳng thức phân rã, hai lớp giao thức | Xong |
| D7 | §4 Thiết lập — model, benchmark, vai trò, mốc so sánh, thống kê, nhãn tin cậy | **Chưa ai rà lại** |
| D8 | §5 Kết quả — 11 tiểu mục, 16 bảng | Xong |
| D9 | §6 Tổng hợp — hai mốc so sánh, cây quyết định | Xong |
| D10 | §7 Kết luận và Hạn chế — 6 mục | Xong |
| D11 | Thư mục tham khảo — 24 trích dẫn | Xong |
| D12 | Hình 1 — sơ đồ thí nghiệm tác động artifact | Xong |
| D13 | Hình 2 — sơ đồ pipeline bốn vai và 16 tổ hợp Shapley | Xong |
| D14 | Hình 3 — ví dụ lối tắt của GRPO | Xong |
| D15 | Hình 4 — hai mốc so sánh (vẽ bằng TikZ) | Xong |
| D16 | Chuẩn hoá thuật ngữ và ký hiệu toàn bài | Xong |
| D17 | Xử lý font tiếng Việt cho hai bộ biên dịch (pdflatex và XeTeX) | Xong |
| D18 | Gộp bốn nhánh và khôi phục số liệu mất khi gộp | Xong |
| D19 | Mục Đóng góp thành viên | **Chưa làm** |

---

## E. Slide thuyết trình

| # | Đầu việc | Trạng thái |
|---|---|---|
| E1 | Bộ slide beamer 16:9, 18 trang | Xong |
| E2 | Trang bìa slide, logo, tách hình Shapley và hình reward hacking | Xong |
| E3 | Soát lại slide sau mỗi lần chốt số liệu trong báo cáo | **Chưa làm** |

---

## F. Việc còn lại cần phân công

| # | Việc | Ước lượng |
|---|---|---|
| F1 | Đối chiếu lại `L ≈ 11G` (§5.8) — số 0,208 trùng biên khoảng tin cậy ở bảng, tỷ số 11 trùng tỷ số đếm bài ở mục sau; lặp ở 3 chỗ | 30 phút |
| F2 | $\varphi_V$ trong Bảng 4 là giá trị áp đặt bằng đối xứng, không phải đo — mà kết luận về verifier lại dựa vào nó | 45 phút |
| F3 | Văn xuôi §5.3 lệch Bảng 4 (−0,023 vs −0,014; +0,269 vs +0,252) | 15 phút |
| F4 | Lỗi số học: "71% (48/68)" phải là 65% (48/74) — tầng 2/5 có 6 bài `maj@5` sai bị bỏ sót | 10 phút |
| F5 | Ba số chưa dẫn được từ bảng nào: khoảng cách trần trên code $+21{,}3$; hai số `maj` $-11{,}3$/$-13{,}1$; "21/43 giả thuyết" | 30 phút |
| F6 | Xung đột ký hiệu: $I$ vừa là chỉ số tương tác Shapley vừa là model mạnh độc lập | 10 phút |
| F7 | Bảng 15 có hai hàng trùng nhãn, caption nói "hai hệ phần cứng" nhưng không phân biệt được | 15 phút |
| F8 | Độ chính xác solver xuất hiện nhiều giá trị chưa giải thích (GSM8K 7B: 0,916/0,910/0,884) | 30 phút |
| F9 | Định nghĩa hai cột của bảng phân loại — là đại lượng gì, đơn vị nào | 15 phút |
| F10 | Rà §4 (D7) | 1 giờ |
| F11 | Viết mục Đóng góp thành viên (D19) | 20 phút |
| F12 | Gom biến thể thuật ngữ còn sót: "tiền đăng ký" (6), "phơi nhiễm" (5), "tác nhân", "Hồi II" | 20 phút |
| F13 | Soát cuối trước nộp: biên dịch, chính tả, xoá khối comment lịch sử sửa bài | 30 phút |
| F14 | *(tuỳ chọn)* Chạy nốt nhánh `R:R2` để khép $\Delta_{real}$ | ~40 phút GPU |
| F15 | *(tuỳ chọn)* Đối chứng thêm lượt 7B không kèm artifact | ~30 phút GPU |
| F16 | *(tuỳ chọn)* Đối chứng khác-model-cùng-họ | ~30 phút GPU |
