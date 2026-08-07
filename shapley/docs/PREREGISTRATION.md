# Đăng ký trước (pre-registration) — thí nghiệm CAN THIỆP "ép trình bày lời giải"

**Viết TRƯỚC khi có kết quả.** Mục đích: khoá sẵn cách diễn giải, để kết quả nào cũng
không thể "uốn" theo ý muốn sau khi đã nhìn thấy số.

## Giả thuyết
Verifier phá đáp án đúng VÌ Solver không trình bày lời giải (chỉ ghi "The answer is X",
median 20 ký tự) -> Verifier không có gì để kiểm -> buộc phải tự giải lại -> lỗi riêng
của nó thành đáp án cuối.

Bằng chứng quan sát (chưa phải nhân quả): 11/103 phá khi không trình bày; 0/28 khi có.

## Ba nhánh
- **A**: Solver trả lời trơ (prompt gốc) — Verifier thấy đáp án trơ
- **B**: Solver bị ép trình bày — Verifier thấy TOÀN BỘ lời giải
- **C**: CÙNG lời giải của B — nhưng Verifier chỉ được thấy đáp án (đã xoá phần trình bày)

B vs C là đối chứng cặp: lời giải Y HỆT, chỉ khác Verifier có được nhìn hay không.

## Cam kết diễn giải (khoá trước)

| Kết quả | Kết luận BẮT BUỘC phải rút |
|---|---|
| break(B) thấp, break(C) cao | TÍNH NHÌN THẤY ĐƯỢC là nguyên nhân. Khẳng định nhân quả. |
| break(B) ≈ break(C), cả hai < A | KHÔNG phải do nhìn thấy; ép trình bày làm LỜI GIẢI tốt hơn. Cơ chế khác. |
| break(B) ≈ break(C) ≈ break(A) | **GIẢ THUYẾT SAI.** Tương quan quan sát được là do nhiễu (model trình bày ở đúng những bài nó vốn làm tốt). Chuyển hướng: biến thật là ĐỘ KHÓ BÀI, không phải tính nhìn thấy. |
| median_sol_len(B) ≈ median_sol_len(A) | **THÍ NGHIỆM VÔ HIỆU** — can thiệp không tác động được lên hành vi. Không được coi là phát hiện. Phải làm lại với can thiệp mạnh hơn. |

## Chỉ số chính
`break_rate = breaks / solver_correct` (không phải accuracy).
Kiểm tra can thiệp có hiệu lực: `median_sol_len`, `pct_under_200_chars`.

## Điều KHÔNG phụ thuộc kết quả này
Các quan sát sau đã đo xong, thí nghiệm này không thể bác bỏ:
Verifier phá đáp án đúng (4 thiết lập độc lập); verify bằng chạy test không phá lần nào
(0/0/0 qua 3 vòng); 1.5B+7B post-hoc thắng (+.18, 9 sửa/0 phá); verifier LLM chỉ bắt
15-17% lỗi thật trên code; feedback bão hoà sau 1 vòng.

---

# Đăng ký trước #2 — XÁC NHẬN "VERIFIER BỊ BỊT MẮT" + KHỬ NHIỄU BỘ TỔNG HỢP
**Viết TRƯỚC khi chạy.** Hai phát hiện hậu nghiệm cần kiểm chứng có đăng ký trước.

## Giả thuyết H1 — tính nhìn thấy lời giải BÓP NGHẸT khả năng bắt lỗi
Verifier ĐỌC ĐƯỢC lời giải của Solver sẽ bắt được ÍT lỗi hơn hẳn so với khi chỉ thấy đáp án.
Cơ chế đề xuất: anchoring/sycophancy — thấy suy luận trôi chảy thì bị thuyết phục, thôi phản đối.
Số hậu nghiệm (CÙNG mẻ, chưa đăng ký): giá trị gia tăng của verify
  THẤY lời giải: -0.8 / +0.4 / +1.3 điểm | BỊT MẮT: +10.8 / +8.0 / +6.7 điểm
  fixes: 10->40, 9->26, 6->20

### Cam kết diễn giải (khoá trước khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| fixes(blind) > fixes(informed), cả 2 task, p<.05 | H1 XÁC NHẬN. Được phát biểu như KHẲNG ĐỊNH. |
| fixes(blind) ~ fixes(informed) | H1 BỊ BÁC. Hiệu ứng cũ là ngẫu nhiên của một mẻ. Phải ghi rõ đã bác. |
| ngược hướng (informed > blind) | H1 BỊ BÁC MẠNH. Rút lại toàn bộ diễn giải "anchoring". |
| chỉ 1 task có, 1 task không | KHÔNG kết luận chung. Ghi là "phụ thuộc task", cần thêm dữ liệu. |

### Nhánh MỚI để tách cơ chế (chưa từng chạy)
- **P (partial)**: Verifier thấy lời giải nhưng ĐÃ XOÁ đáp án cuối -> có suy luận, không có kết luận.
  Nếu P bắt lỗi tốt như blind => thủ phạm là ĐÁP ÁN (anchor số), không phải phần suy luận.
  Nếu P kém như informed => thủ phạm là PHẦN SUY LUẬN (bị thuyết phục bởi lập luận trôi chảy).
- **X (cross-check)**: Verifier thấy lời giải của MỘT BÀI KHÁC (đối chứng giả dược).
  Kiểm tra hiệu ứng có phải chỉ do "context dài hơn" hay không.

## Giả thuyết H2 — bộ tổng hợp LLM kém hơn bỏ phiếu KHI ĐƯỢC ĐỐI XỬ CÔNG BẰNG
Lần trước aggregator bị thiệt: KHÔNG có chỉ dẫn CoT, chỉ 384 token (so với 1024 của solver).
Lần này: CÙNG chỉ dẫn "step by step", CÙNG 1024 token.
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| vẫn đè lên đa số đúng >> cứu, p<.05 | H2 XÁC NHẬN kể cả khi công bằng. Được phát biểu mạnh. |
| khoảng cách thu hẹp rõ | Kết quả cũ PHẦN LỚN do NHIỄU PROMPT. Phải sửa lại phát biểu. |
| aggregator >= bỏ phiếu | H2 BỊ BÁC. Rút lại "sai loại bộ tổng hợp". |

## Chỉ số chính
H1: `fixes` và `verifier_acc - solver_acc` theo từng nhánh (CÙNG bộ lời giải).
H2: `llm_breaks_majority` vs `llm_fixes_majority`, và `llm_agg_acc` vs `maj@8`.
Kiểm tra hiệu lực: độ dài context mỗi nhánh phải khác nhau như thiết kế.

---

# Đăng ký trước #3 — (A) VERIFY CÓ CỔNG LỌC  (B) PLANNER CÓ BÓP NGHẸT SOLVER KHÔNG
**Viết TRƯỚC khi chạy.** Rút thẳng từ số đo của bl_g15.

## Xuất phát (ĐO ĐƯỢC ở bl_g15, GSM8K 1.5B, n=250, 158 bài đúng)
  I informed : 20 sửa /  6 phá  (+5.6 điểm)
  B blind    : 42 sửa / 23 phá  (+7.6 điểm)   <- sản lượng CAO, rủi ro CAO
  P giấu đáp : 15 sửa /  1 phá  (+5.6 điểm)   <- rủi ro CỰC THẤP, sản lượng thấp
Nhận xét: B và P bù trừ nhau. B biết CÁCH SỬA, P biết KHI NÀO nên động vào.

## (A) GIẢ THUYẾT H3 — TÁCH "KHI NÀO CAN THIỆP" KHỎI "CAN THIỆP THẾ NÀO"
Dùng P làm CỔNG (chỉ hỏi "phần suy luận này có lỗi không? YES/NO", KHÔNG cho thấy đáp án),
chỉ khi cổng báo YES mới cho B giải lại từ đầu.
Kỳ vọng: số SỬA gần B, số PHÁ gần P -> vượt cả hai.
Nhánh: N (không verify) | I (informed) | B (blind) | **G (có cổng)**

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| G có value_added > cả I và B | H3 XÁC NHẬN. Đây là ĐÓNG GÓP PHƯƠNG PHÁP, không chỉ phân tích. |
| G ~ B (phá nhiều như B) | Cổng KHÔNG lọc được. P an toàn chỉ vì nó LƯỜI, không vì nó chính xác. |
| G ~ P (sửa ít như P) | Cổng quá chặt, chặn luôn cả ca đáng sửa. Phải nới ngưỡng. |
| G kém cả hai | H3 BỊ BÁC. Ghi rõ đã bác, không diễn giải lại. |
Chỉ số phụ BẮT BUỘC báo: `gate_flag_rate` (cổng kêu YES bao nhiêu %),
`gate_precision` (trong số bị kêu, bao nhiêu THỰC SỰ sai) -> cho biết cổng lọc được thật hay không.

## (B) GIẢ THUYẾT H4 — PLANNER LÀM SOLVER NGỪNG TRÌNH BÀY
Quan sát CHÉO thí nghiệm (chưa kiểm soát): cùng prompt SOLVE,
  CÓ Planner -> median 18 ký tự (sw_g15) | KHÔNG Planner -> 600 ký tự (bl_g15).
Nếu đúng, đây là TƯƠNG TÁC ÂM giữa hai vai, và giải thích được vì sao Planner có Shapley thấp/âm.
Thí nghiệm CÓ KIỂM SOÁT: cùng model, cùng bài, cùng prompt SOLVE, chỉ bật/tắt Planner.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| median_len(có plan) << median_len(không plan), và acc giảm | H4 XÁC NHẬN. Planner gây hại qua việc bóp nghẹt trình bày. |
| median_len khác nhưng acc KHÔNG đổi | Planner đổi ĐỘ DÀI chứ không đổi CHẤT LƯỢNG. Không được nói "gây hại". |
| median_len ~ nhau | H4 BỊ BÁC. Chênh lệch 18 vs 600 là do yếu tố khác giữa 2 thí nghiệm, không phải Planner. |

## Chỉ số chính
H3: `value_added` từng nhánh + fixes/breaks + gate_flag_rate + gate_precision.
H4: `median_sol_len` và `solver_acc`, có/không Planner, trên CÙNG bài.

---

# Đăng ký trước #4 — H5: PIPELINE VỨT MẤT PHẦN SUY LUẬN TRƯỚC KHI VERIFIER NHÌN THẤY
**Viết TRƯỚC khi chạy.** Rút thẳng từ H4 (plan_g15/plan_m15).

## Xuất phát (ĐO ĐƯỢC)
Có Planner: Solver chỉ viết 18 ký tự nhưng acc TĂNG (.632 -> .684).
Nhắc "vẫn phải trình bày" KHÔNG cứu được (vẫn 18 ký tự) -> bóp nghẹt là CẤU TRÚC, không phải prompt.
=> Suy luận không biến mất, nó NẰM TRONG BẢN KẾ HOẠCH. Nhưng pipeline chỉ chuyển LỜI GIẢI
   (đã trơ) cho Verifier, KHÔNG chuyển kế hoạch. Verifier vì thế không có gì để kiểm.

## H5
Đưa BẢN KẾ HOẠCH cho Verifier sẽ khôi phục khả năng kiểm tra của nó, vì đó mới là nơi chứa suy luận.
4 nhánh, CÙNG bộ (plan, solution), Planner LUÔN BẬT:
  V_sol  : Verifier thấy lời giải Solver (trơ)          <- chuẩn hiện hành của mọi framework
  V_plan : Verifier thấy KẾ HOẠCH + đáp án
  V_both : Verifier thấy KẾ HOẠCH + lời giải
  V_none : Verifier chỉ thấy đáp án (blind, đối chứng)

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| V_plan và/hoặc V_both > V_sol rõ rệt | H5 XÁC NHẬN. Lỗi nằm ở ĐƯỜNG TRUYỀN của pipeline, không ở năng lực Verifier. Khuyến nghị: chuyển KẾ HOẠCH, đừng chỉ chuyển lời giải. |
| V_plan ~ V_sol ~ V_none | H5 BỊ BÁC. Kế hoạch không giúp kiểm tra. Ghi rõ đã bác. |
| V_both < V_sol (thêm kế hoạch làm TỆ hơn) | Khớp với phát hiện "context nhiều hơn làm hỏng phán đoán". Kế hoạch chỉ là context gây nhiễu, KHÔNG phải suy luận hữu ích. |
| V_none tốt nhất | Củng cố: mọi context đều hại, chỉ đáp án là đủ. Rút lại luôn giả thuyết "cần cái gì đó để kiểm". |

## Chỉ số chính
`value_added` (verifier_acc - solver_acc), fixes, breaks cho từng nhánh, trên CÙNG bộ lời giải.
Phụ: `median_plan_len`, `median_sol_len` (xác nhận Planner vẫn đang bóp nghẹt như H4).

## Ghi chú trung thực
Ba giả thuyết gần nhất của tôi (interleaving, math-khó-verify, H3 cổng lọc, H4 gây hại) đều đã bị
bác. H5 cũng có thể bị bác. Bảng trên đã khoá sẵn cách diễn giải cho MỌI kết cục, kể cả kết cục đó.

---

# Đăng ký trước #5 — H6: THÀNH PHẦN HOẠT TÍNH LÀ "PHÉP TÍNH KIỂM CHỨNG ĐƯỢC"?
**Viết TRƯỚC khi chạy.** Rút từ H5 (pp_g15).

## Xuất phát (ĐO ĐƯỢC, 4 lần lặp)
Thêm context cho Verifier đều làm giảm giá trị: kế hoạch -2.8, kế hoạch+lời giải -2.0,
suy luận bài khác -3.6/-3.5, toàn văn cho aggregator -17.5; chỉ-đáp-án +4.0.
NHƯNG ở bl_g15 (Planner TẮT, lời giải là 600 ký tự CÓ PHÉP TÍNH THẬT), informed đạt +5.6 —
tức context ĐÓ không hại. Khác biệt khả dĩ: CÓ hay KHÔNG có phép tính kiểm chứng được.

## H6
Verifier chỉ dùng được context nào chứa PHÉP TÍNH (kết quả cụ thể), không dùng được context
chỉ nêu Ý ĐỊNH (kế hoạch, mô tả bằng lời).
Planner TẮT để Solver viết lời giải thật, rồi CẮT GỌT chính lời giải đó thành 4 dạng:
  W_full  : nguyên văn lời giải (có cả lời văn lẫn phép tính)
  W_calc  : CHỈ giữ các dòng có phép tính/số (bỏ hết lời văn)
  W_prose : CHỈ giữ lời văn, XOÁ mọi số và phép tính  (biến lời giải thành "kế hoạch")
  W_none  : chỉ đáp án (đối chứng)
Mọi nhánh dùng CÙNG bộ lời giải -> khác biệt CHỈ do nội dung context.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| W_calc ~ W_full > W_prose ~ W_none | H6 XÁC NHẬN. Phép tính là thành phần hoạt tính. Khuyến nghị: chỉ chuyển dòng TÍNH TOÁN cho Verifier. |
| W_prose ~ W_full (lời văn cũng tốt) | H6 BỊ BÁC. Không phải phép tính; là thứ khác. Ghi rõ đã bác. |
| W_none tốt nhất, mọi context đều kém hơn | KẾT LUẬN MẠNH & ĐƠN GIẢN: ĐỪNG đưa gì cho Verifier ngoài đáp án. Đây là khuyến nghị cuối cùng, khỏi cần tìm "context tốt". |
| W_calc < W_full | Phép tính KHÔNG đủ; cần cả ngữ cảnh lời văn. Rút lại giả thuyết. |

## Chỉ số chính
`value_added`, fixes, breaks từng nhánh; kèm `median_ctx_chars` để xác nhận việc cắt gọt có hiệu lực.
## Ghi chú trung thực
5 giả thuyết gần nhất của tôi đều đã bị bác. H6 cũng có thể. Hàng 3 ở trên là kết cục
"mọi context đều hại" — nếu rơi vào đó thì đó CHÍNH LÀ kết luận của dự án, không phải thất bại.

---

# Đăng ký trước #6 — H7: CHE GIÁ TRỊ TRUNG GIAN CÓ CỨU ĐƯỢC CẢ VAI AGGREGATOR KHÔNG?
**Viết TRƯỚC khi chạy.** Rút từ cp_g15 (H6 bị bác, thứ tự ngược dự đoán).

## Xuất phát (ĐO ĐƯỢC)
Với vai VERIFIER: che hết số trong lời giải cho kết quả TỐT NHẤT (+8.4), hơn cả chỉ-đáp-án (+7.6),
hơn chỉ-phép-tính (+6.4) và nguyên văn (+5.6). Đơn điệu theo lượng số liệu nhìn thấy.
Với vai AGGREGATOR (đo ở agf_15): cho xem TOÀN VĂN lời giải là nhánh TỆ NHẤT (-17.5 so với bỏ phiếu).

## H7
Nếu cơ chế đúng là "GIÁ TRỊ TRUNG GIAN neo model lại", thì che số cũng phải cứu được AGGREGATOR,
vì đó là cùng một bệnh ở một vai khác. Đây là phép thử TỔNG QUÁT HOÁ sang vai thứ hai.
Nhánh (cùng bể k=8 mẫu, cùng prompt CoT + 1024 token):
  A_answers : chỉ danh sách đáp án ứng viên            (đã đo trước: -6.7 so với bỏ phiếu)
  A_full    : toàn văn lời giải ứng viên               (đã đo trước: -17.5)
  A_masked  : toàn văn NHƯNG ĐÃ CHE HẾT GIÁ TRỊ        <- nhánh mới
  maj@8     : bỏ phiếu thuần (mốc)

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| A_masked > A_full RÕ RỆT, và tiến gần/vượt maj@8 | H7 XÁC NHẬN. Cơ chế "neo bởi giá trị" TỔNG QUÁT cho nhiều vai. Khuyến nghị chung: che giá trị trung gian khi truyền giữa các agent. |
| A_masked ~ A_full (vẫn tệ) | H7 BỊ BÁC. Hiệu ứng che số chỉ riêng cho vai Verifier, không tổng quát. Ghi rõ đã bác. |
| A_masked ~ A_answers | Che số chỉ đơn giản = bỏ bớt context, không có gì đặc biệt. Rút lại diễn giải "neo bởi giá trị". |
| mọi nhánh LLM < maj@8 | Củng cố kết luận cũ: với vai TỔNG HỢP, hãy dùng THỐNG KÊ, đừng dùng LLM — bất kể context. |

## Chỉ số chính
`acc` từng nhánh, `vs_maj`, `breaks_majority` vs `fixes_majority`.
## Ghi chú trung thực
6 giả thuyết gần nhất của tôi đã bị bác (interleaving, math-khó-verify, H3, H4-hại, H5, H6).
H7 cũng có thể. Mọi kết cục kể cả kết cục đó đã được khoá diễn giải ở bảng trên.

---

# Đăng ký trước #7 — H8: VERIFY BẰNG THỰC THI CÓ TỔNG QUÁT TỪ CODE SANG MATH KHÔNG?
**Viết TRƯỚC khi chạy.** Rút từ chuỗi 7 lần bác bỏ.

## Xuất phát (ĐO ĐƯỢC)
7 giả thuyết dựa trên PHÁN ĐOÁN LLM đều chết. Hai thứ CHƯA TỪNG hỏng:
  (1) verify bằng THỰC THI trên code: 0 phá qua 3 vòng, cả 2 cỡ model, tăng đơn điệu;
  (2) context KHÔNG liên quan luôn hại (âm 3/3).
=> Câu hỏi còn lại đáng giá nhất: cơ chế CƠ HỌC (thực thi) có dùng được ở miền KHÔNG phải code không?
Nếu CÓ, khuyến nghị của dự án trở nên mạnh và đơn giản: ở đâu kiểm được bằng máy thì đừng
dùng phán đoán LLM. Nếu KHÔNG, kết luận là "code đặc biệt", cũng là kết quả rõ ràng.

## H8
Bắt model VIẾT PYTHON tính lại đáp án, CHẠY THẬT, rồi so với đáp án của Solver.
Đây là verifier CƠ HỌC: nó không "phán đoán", nó TÍNH.
Nhánh (cùng bộ lời giải Solver):
  N       : không verify (mốc)
  L       : verify bằng LLM (chuẩn hiện hành)
  E_take  : Python bất đồng -> LẤY LUÔN đáp án của Python
  E_flag  : Python bất đồng -> báo động, cho LLM GIẢI LẠI (Python chỉ làm CỔNG)

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| E_take và/hoặc E_flag > L rõ rệt | H8 XÁC NHẬN. Cơ chế cơ học TỔNG QUÁT ngoài code. Khuyến nghị chính của dự án. |
| E_* ~ L | H8 BỊ BÁC. Thực thi không hơn phán đoán ở miền math. Ghi rõ đã bác. |
| E_* < L | Thực thi HẠI trên math (Python model viết ra sai nhiều hơn nó sửa). Kết luận: verify cơ học CHỈ dùng được khi bài toán VỐN LÀ code. |
| exec_success_rate thấp (<50%) | THÍ NGHIỆM VÔ HIỆU về mặt cơ chế: model không viết nổi Python chạy được. Phải báo là hạn chế năng lực, KHÔNG phải bác bỏ H8. |

## Chỉ số chính
`value_added`, fixes, breaks từng nhánh.
Kiểm tra hiệu lực BẮT BUỘC báo: `exec_success_rate` (Python chạy được không),
`disagree_rate` (Python khác Solver bao nhiêu %), `exec_acc` (đáp án Python đúng bao nhiêu %).

## Ghi chú trung thực
7 giả thuyết gần nhất của tôi đã bị bác, 1 kết quả đã phải rút lại. H8 cũng có thể chết.
Hàng 3 và 4 ở trên đã khoá sẵn cách diễn giải cho kết cục đó.

---

# Bổ sung cho #7 — CHẠY LẠI H8 VỚI MODEL 7B (không phải giả thuyết mới)
**Viết TRƯỚC khi chạy.** H8 vẫn là H8; lần trước THÍ NGHIỆM VÔ HIỆU vì model quá yếu.

## Lý do chạy lại
Kiểm tra hiệu lực đã khoá trước: exec_success_rate phải >= 50% thì kết quả mới có ý nghĩa.
Lần chạy 1.5B: .416 (GSM8K) và .435 (MATH) -> VÔ HIỆU. exec_acc chỉ .414/.391.
7B đạt .787 pass@1 trên HumanEval (so với .53 của 1.5B) -> nhiều khả năng vượt ngưỡng hiệu lực.
KHÔNG thay đổi giả thuyết, KHÔNG thay đổi bảng diễn giải. Chỉ thay model để có phép thử HỢP LỆ.

## Bảng diễn giải giữ NGUYÊN như #7
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| E_take và/hoặc E_flag > L rõ rệt | H8 XÁC NHẬN. Cơ chế cơ học TỔNG QUÁT ngoài code. |
| E_* ~ L | H8 BỊ BÁC. Thực thi không hơn phán đoán ở miền math. |
| E_* < L | Thực thi HẠI trên math. Verify cơ học CHỈ dùng được khi bài toán VỐN LÀ code. |
| exec_success_rate < 50% LẦN NỮA | VẪN VÔ HIỆU. Kết luận: cơ chế này ĐÒI HỎI năng lực viết code mà model ở cỡ này không có -> đó CHÍNH LÀ giới hạn thực tế đáng báo cáo. KHÔNG được diễn giải thành "H8 sai". |

## Ghi chú trung thực
Nếu lần này exec_success_rate vẫn dưới 50%, KHÔNG chạy lại lần ba. Kết luận cuối sẽ là:
"verify bằng thực thi cần model đủ mạnh để viết code đúng; ở cỡ model chúng tôi thử nghiệm được
thì điều kiện đó không thoả" — một giới hạn được ĐO ĐẠC, không phải một giả thuyết bị bác.

---

# Đăng ký trước #8 — H9: PIPELINE TỐI GIẢN CÓ BẰNG/HƠN PIPELINE TRUYỀN TOÀN BỘ TRACE KHÔNG?
**Viết TRƯỚC khi chạy.** Đây là thí nghiệm HỢP NHẤT: biến phát hiện lặp lại nhiều lần thành
MỘT phép so sánh đầu-cuối, đúng dạng có thể đưa vào tóm tắt báo cáo.

## Xuất phát (ĐO ĐƯỢC, nhiều lần, nhiều vai, nhiều task, nhiều cỡ model)
  Vai VERIFIER: chỉ-đáp-án tốt nhất hoặc gần nhất ở 3/3 thiết lập; thêm kế hoạch -> -2.8/-2.0;
                context KHÔNG liên quan -> -3.6/-3.5/-1.6 (âm 3/3)
  Vai AGGREGATOR: chỉ-danh-sách-đáp-án .533 vs toàn-văn .300 -> THÊM CONTEXT MẤT 23 ĐIỂM
=> Mọi framework đa tác tử hiện nay đều truyền TOÀN BỘ trace giữa các agent. Dữ liệu nói đó là SAI.

## H9
Pipeline 4 vai P->S->V->A, hai biến thể, CÙNG model, CÙNG bài:
  FULL : mỗi agent nhận TOÀN VĂN mọi output trước đó (chuẩn hiện hành)
  MIN  : mỗi agent chỉ nhận ĐÁP ÁN của agent trước (không có trace suy luận)
Đo: accuracy đầu-cuối VÀ chi phí (tổng ký tự context) -> tỉ số "điểm trên mỗi đơn vị context".

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| MIN >= FULL về accuracy VÀ rẻ hơn | H9 XÁC NHẬN. Khuyến nghị chính, có số đầu-cuối: ĐỪNG truyền trace, chỉ truyền đáp án. |
| MIN < FULL rõ rệt | H9 BỊ BÁC. Ở mức ĐẦU-CUỐI thì truyền trace vẫn có giá trị, dù ở từng vai đo được là hại. Ghi rõ đã bác — đây sẽ là mâu thuẫn quan trọng phải giải thích. |
| MIN ~ FULL (chênh trong nhiễu) | KẾT LUẬN THỰC DỤNG: trace KHÔNG đem lại gì nhưng tốn 3-4x context -> vẫn nên bỏ, vì lý do CHI PHÍ chứ không phải độ chính xác. |
| cả hai < solver đơn lẻ | Kết luận mạnh hơn: TOÀN BỘ pipeline đa tác tử không đáng, ở cỡ model này. |

## Chỉ số chính
`acc_full`, `acc_min`, `chars_full`, `chars_min`, và accuracy của Solver đơn lẻ làm mốc.
## Ghi chú trung thực
8 giả thuyết của tôi đã bị bác/rút lại. H9 cũng có thể. Hàng 2 ở trên là kết cục "bị bác" và
đã khoá sẵn rằng nó sẽ là MÂU THUẪN CẦN GIẢI THÍCH, không được lờ đi.

---

# Đăng ký trước #9 — H10: SỬA LỖI THIẾT KẾ CỦA H9, ĐO TRÊN LƯỚI ĐẦY ĐỦ
**Viết TRƯỚC khi chạy.** Sửa lỗi đã tự thú ở vòng #9.

## Lỗi cần sửa
Nhánh MIN của H9 bỏ ĐỒNG THỜI hai thứ: (a) trace -> Verifier/Aggregator, (b) Planner -> Solver.
Đã ĐO ĐƯỢC (b) LÀM TĂNG acc (.632 -> .684) => MIN bị chấp ~5 điểm. So sánh KHÔNG SẠCH.

## Thiết kế sửa lỗi — CHỈ đổi MỘT biến
Cả ba nhánh đều GIỮ NGUYÊN đường Planner -> Solver. Chỉ đổi thứ Verifier/Aggregator được thấy:
  FULL   : V và A nhận TOÀN VĂN lời giải (chuẩn hiện hành)
  TRIM   : V và A chỉ nhận ĐÁP ÁN (giữ nguyên Planner -> Solver)
  NOVA   : bỏ luôn V và A, chỉ P -> S (đo xem hai vai sau có đáng tồn tại không)
Chạy trên LƯỚI ĐẦY ĐỦ: {GSM8K, MATH} x {1.5B, 7B} — vì vòng #9 cho thấy hiệu ứng ĐỔI DẤU theo ô.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| TRIM >= FULL ở ĐA SỐ ô | Cắt trace là ĐÚNG. Khuyến nghị có điều kiện, ghi rõ ô nào áp dụng được. |
| FULL > TRIM ở ĐA SỐ ô | Truyền trace ĐÚNG là có giá trị. RÚT LẠI toàn bộ khuyến nghị "đừng truyền trace" của các vòng trước. Ghi rõ đã rút. |
| Kết quả ĐỔI DẤU giữa các ô | Kết luận cuối của dự án là chính META-PHÁT HIỆN: hiệu ứng KHÔNG BỀN, phải đo theo ô. Đây là kết quả HỢP LỆ, không phải thất bại. |
| NOVA >= FULL và >= TRIM | Hai vai V và A KHÔNG đáng tồn tại ở cấu hình này. Kết luận mạnh về kiến trúc. |

## Chỉ số chính
`acc_full`, `acc_trim`, `acc_nova`, `acc_solo`; kèm `chars_*` để tính chi phí.
Bắt buộc báo theo TỪNG Ô của lưới, KHÔNG được gộp trung bình che mất đảo dấu.

## Ghi chú trung thực
9 giả thuyết của tôi đã bị bác, 1 kết quả bị rút lại, 1 thí nghiệm vô hiệu, và vòng #9 vừa
lật ngược "phát hiện bền nhất". H10 nhiều khả năng cũng cho kết quả không đồng nhất —
hàng 3 đã khoá sẵn rằng ĐÓ CHÍNH LÀ kết luận, không phải thất bại.

---

# Đăng ký trước #10 — H11: VAI NÀO PHÍA SAU (VERIFIER hay AGGREGATOR) MANG GIÁ TRỊ?
**Viết TRƯỚC khi chạy.** Rút thẳng từ tr_g15, và quay lại đúng câu hỏi gốc của dự án.

## Xuất phát (ĐO ĐƯỢC ở tr_g15, GSM8K 1.5B)
  P->S            .684
  P->S->V->A toàn văn  .744  (+6.0 nhờ có V và A)
  P->S->V->A chỉ đáp án .668  (-1.6 so với không có V,A -> ÂM khi bị bỏ đói context)
Chưa biết: trong +6.0 đó, VERIFIER đóng góp bao nhiêu, AGGREGATOR bao nhiêu?
Đây CHÍNH LÀ câu hỏi phân bổ đóng góp mà dự án khởi đầu, nhưng đo ở mức ĐẦU-CUỐI thay vì từng vai.

## H11 — tách đóng góp của hai vai phía sau
4 nhánh, CÙNG bộ (plan, solution), toàn văn được truyền ở mọi nhánh có vai đó:
  PS    : P->S                      (mốc)
  PSV   : P->S->V     (chỉ Verifier, đáp án cuối lấy của V)
  PSA   : P->S->A     (chỉ Aggregator, nhận lời giải của S; KHÔNG có V)
  PSVA  : P->S->V->A  (đầy đủ)

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| PSV ~ PSVA > PSA | VERIFIER mang gần hết giá trị; Aggregator gần như thừa. |
| PSA ~ PSVA > PSV | AGGREGATOR mang gần hết giá trị; Verifier gần như thừa. |
| PSVA > cả PSV và PSA rõ rệt | HAI VAI BỔ TRỢ NHAU (synergy) — không vai nào một mình đủ. Khớp với chỉ số tương tác Shapley đo ở giai đoạn đầu dự án. |
| PSV ~ PSA ~ PSVA ~ PS | Không vai nào đóng góp gì; +6.0 ở tr_g15 là do yếu tố khác (vd chỉ cần thêm một lượt sinh). PHẢI ghi rõ và kiểm tra lại. |

## Chỉ số chính
`acc` từng nhánh trên CÙNG bài; kèm số lần đổi đáp án ở mỗi bước để thấy vai nào thực sự tác động.
## Ghi chú trung thực
9 giả thuyết đã bị bác, 1 rút lại, 1 vô hiệu, 1 lỗi thiết kế tự thú, và vòng #9 đã lật ngược
"phát hiện bền nhất". H11 nhiều khả năng cũng cho kết quả phụ thuộc ô — hàng 4 đã khoá sẵn
kết cục "không vai nào đóng góp".

---

# Đăng ký trước #11 — H12: THAY AGGREGATOR-LLM BẰNG BỎ PHIẾU TRONG PIPELINE
**Viết TRƯỚC khi chạy.** Rút từ H11 + kết quả self-consistency.

## Xuất phát (ĐO ĐƯỢC)
Aggregator là vai DUY NHẤT ĐẢO DẤU rõ rệt giữa hai task:
  thêm A sau V:  GSM8K **+1.2đ** (.732->.744)  |  MATH **-6.0đ** (.445->.385)
Trong khi Verifier DƯƠNG ở cả hai (+4.8 / +2.0), và truyền kế hoạch vô ích ở 4/4 ô.
Đồng thời đã đo: maj@8 THẮNG greedy +10đ ở 1.5B; và bỏ phiếu thắng aggregator-LLM ở 1.5B (-6.7đ).
=> Giả thuyết tự nhiên: vấn đề không phải "có vai tổng hợp", mà là "tổng hợp BẰNG LLM".

## H12
Trong pipeline P->S->V, thay bước tổng hợp LLM bằng BỎ PHIẾU trên các ứng viên đã có.
Nhánh (cùng bài, cùng P->S->V):
  PSV        : dừng ở Verifier (mốc tốt nhất hiện tại)
  PSVA       : Aggregator LLM (chuẩn hiện hành)
  PSV_vote   : bỏ phiếu giữa {đáp án Solver, đáp án Verifier} + 1 mẫu Solver thêm (3 phiếu)
  PSV_vote5  : bỏ phiếu giữa 5 ứng viên (3 mẫu Solver nhiệt độ + Verifier + Solver greedy)
Chạy trên CẢ HAI task với 1.5B.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| PSV_vote* >= PSVA ở CẢ HAI task | H12 XÁC NHẬN. Khuyến nghị: giữ vai tổng hợp nhưng thực hiện bằng THỐNG KÊ, không bằng LLM. |
| PSV_vote* ~ PSVA | Bỏ phiếu không hơn. Vấn đề nằm ở CHÍNH việc tổng hợp, không ở cách tổng hợp. |
| PSV_vote* < PSVA | H12 BỊ BÁC. Ghi rõ đã bác. |
| PSV vẫn tốt nhất ở cả hai task | KẾT LUẬN KIẾN TRÚC: bỏ hẳn vai tổng hợp. Dừng ở Verifier là cấu hình tốt nhất. |
| Kết quả ĐỔI DẤU giữa hai task | Lại thêm một bằng chứng cho meta-phát hiện; ghi vào bảng đảo dấu. |

## Chỉ số chính
`acc` từng nhánh trên CÙNG bài; kèm số lần bỏ phiếu khác với đáp án Verifier.
## Ghi chú trung thực
10 giả thuyết của tôi đã bị bác/rút lại/vô hiệu. H12 cũng có thể. Hàng 3 và 5 đã khoá sẵn.

---

# Đăng ký trước #12 — H13: SÀN NHIỄU. CÁC HIỆU ỨNG CHÚNG TÔI BÁO CÁO CÓ LỚN HƠN NHIỄU KHÔNG?
**Viết TRƯỚC khi chạy.** Đây là thí nghiệm QUAN TRỌNG NHẤT còn lại, và nó có thể HẠ GIÁ
phần lớn các kết luận trước đó của chính dự án này.

## Lý do bắt buộc phải chạy
agf_7 và am_7 (cùng 7B, cùng MATH, n=120, thiết lập gần như y hệt) cho KẾT LUẬN NGƯỢC NHAU:
  agf_7: aggregator THẮNG bỏ phiếu +1.7   |   am_7: aggregator THUA bỏ phiếu -11.7
Ngay cả mốc maj@8 cũng lệch (.7167 vs .7583). Nếu hai lần chạy gần giống nhau chênh tới ~13 điểm,
thì MỌI hiệu ứng 2-7 điểm mà chúng tôi đã báo cáo có thể chỉ là NHIỄU.

## H13 — đo trực tiếp phương sai giữa các lần chạy
Chia MATH-500 thành 5 FOLD RỜI NHAU, mỗi fold 100 bài. Chạy CÙNG cấu hình (PS / PSV / PSVA)
trên từng fold một cách độc lập. Báo cáo TRUNG BÌNH và ĐỘ TRẢI của từng hiệu ứng qua 5 fold.
Đây là ước lượng SÀN NHIỄU do lấy mẫu bài toán — chính là thứ chưa bao giờ được đo.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Độ trải giữa các fold NHỎ hơn nhiều so với hiệu ứng đã báo cáo (vd < 2đ) | Các kết luận trước ĐỨNG VỮNG. Mâu thuẫn agf_7/am_7 phải có nguyên nhân khác, cần truy tiếp. |
| Độ trải NGANG NGỬA hiệu ứng đã báo cáo (vd 4-8đ) | **PHẢI HẠ CẤP** mọi khẳng định dựa trên một lần chạy ở n<=250, kể cả các "đảo dấu". Bảng đảo dấu phải ghi rõ khoảng tin cậy. |
| Độ trải LỚN HƠN hiệu ứng đã báo cáo | Phần lớn kết quả của dự án là NHIỄU. Kết luận trung thực duy nhất còn lại là meta-phát hiện, và phải phát biểu như "không đo được hiệu ứng ổn định", KHÔNG phải "hiệu ứng đảo dấu". |

## Chỉ số chính
Với từng fold: acc_PS, acc_PSV, acc_PSVA. Sau đó tính qua 5 fold:
`mean` và `min-max range` và `std` của (PSV - PS) và (PSVA - PSV).
So sánh trực tiếp độ trải đó với các hiệu ứng đã công bố (+4.8, +1.2, -6.0, +7.5, -5.6...).

## Ghi chú trung thực
Kết cục HÀNG 3 sẽ HẠ GIÁ phần lớn công sức của dự án. Nó vẫn phải được báo cáo y nguyên nếu xảy ra.
Đây chính là phép thử mà lẽ ra tôi phải chạy TỪ ĐẦU, trước khi diễn giải bất kỳ hiệu ứng nào.

---

# Đăng ký trước #13 — H14: ĐẢO DẤU LỚN NHẤT CÓ SỐNG SÓT KHI CÓ THANH SAI SỐ KHÔNG?
**Viết TRƯỚC khi chạy.** Sau khi đã đo sàn nhiễu (H13), phải kiểm lại chính phát hiện chủ đạo.

## Xuất phát (ĐO ĐƯỢC)
H13: cùng cấu hình chạy 5 fold -> V_gain trải từ +1.0 đến +8.0 (range 7.0). Ngưỡng 2σ ≈ 5đ.
Phát hiện CHỦ ĐẠO của dự án là ĐẢO DẤU của "truyền trace" (H10): +7.6 (GSM8K) vs -9.0 (MATH),
biên độ 16.6đ. Đo MỘT LẦN mỗi ô. Chưa từng có thanh sai số.

## H14
Chạy lại đúng so sánh FULL vs TRIM trên **5 fold rời nhau** cho **cả hai task**, 1.5B.
Báo cáo `trim_minus_full` theo từng fold, kèm mean/range/std.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Khoảng của GSM8K (âm) và MATH (dương) KHÔNG chồng lấn | ĐẢO DẤU LÀ THẬT. Phát hiện chủ đạo được xác nhận có thanh sai số. |
| Hai khoảng CHỒNG LẤN | **PHÁT HIỆN CHỦ ĐẠO BỊ HẠ CẤP** — không kết luận được là đảo dấu. Phải sửa README và RESULTS.md, hạ xuống mức "không đo được hiệu ứng ổn định". |
| Cả hai khoảng đều chứa 0 | Truyền trace KHÔNG có tác dụng đo được ở cả hai task. Toàn bộ nhánh H9/H10 phải viết lại. |
| Dấu ĐẢO NGƯỢC so với lần đo đầu | Lần đo đầu là nhiễu. Ghi rõ và rút lại. |

## Chỉ số chính
`trim_minus_full` từng fold; mean, min, max, range, std cho mỗi task.
Kiểm tra chồng lấn: [min_GSM8K, max_GSM8K] ∩ [min_MATH, max_MATH] có rỗng không.

## Ghi chú trung thực
Nếu rơi vào hàng 2 hoặc 3, phần lớn nội dung README hiện tại phải viết lại. Điều đó vẫn phải làm.

---

# Đăng ký trước #14 — H15: KẾT QUẢ DƯƠNG MẠNH NHẤT CỦA DỰ ÁN CÓ SỐNG SÓT KHÔNG?
**Viết TRƯỚC khi chạy.** Đây là phép kiểm mà kết quả tốt nhất của dự án đang thiếu.

## Vấn đề
Kết quả DƯƠNG mạnh nhất toàn dự án: "Solver 1.5B + Verifier 7B (post-hoc) = .46 -> .64,
+18 điểm, 9 sửa / 0 phá". Nhưng nó được đo **MỘT LẦN, ở n=50**.
Sàn nhiễu đã đo (H13): ở n=100, V_gain trải 7 điểm; ở n=50 độ trải còn LỚN HƠN (~1.4 lần).
=> Khẳng định MẠNH NHẤT của dự án đang dựa trên phép đo YẾU NHẤT. Không thể để nguyên.

## H15
Đo lại bất đối xứng năng lực trên **5 fold rời nhau**, mỗi fold 60 bài MATH (tổng 300).
Cả hai model nằm đồng thời trên GPU: 1.5B fp16 (~3GB) + 7B nf4 (~5GB) < 16GB T4.
Nhánh (mỗi fold): `solo` (1.5B không verify) | `V15` (verifier 1.5B) | `V7` (verifier 7B)

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Khoảng của `V7_gain` TOÀN DƯƠNG và không chứa 0 | XÁC NHẬN. Bất đối xứng năng lực là kết quả dương THẬT, có thanh sai số. Đây là khuyến nghị chính đáng tin nhất của dự án. |
| Khoảng `V7_gain` CHỨA 0 | **HẠ CẤP** khẳng định "+18 điểm". Phải sửa RESULTS.md và README: kết quả dương mạnh nhất KHÔNG xác lập được. |
| `V7_gain` ~ `V15_gain` | Lợi ích đến từ VIỆC CÓ verifier, KHÔNG phải từ việc verifier MẠNH HƠN. Rút lại toàn bộ diễn giải "bất đối xứng năng lực". |
| `V7_gain` ÂM | Kết quả n=50 ban đầu là nhiễu thuần tuý. Rút lại hoàn toàn. |

## Chỉ số chính
Mỗi fold: `solo`, `V15`, `V7`; số sửa/phá của từng verifier.
Tổng hợp: mean/min/max/range/std của `V7_gain = V7 - solo` và `V15_gain = V15 - solo`,
và của hiệu `V7 - V15` (đây mới là "bất đối xứng năng lực" đúng nghĩa).

## Ghi chú trung thực
Nếu rơi hàng 2/3/4 thì kết quả TỐT NHẤT của dự án bị mất. Vẫn phải báo cáo y nguyên.
Kết quả "9 sửa / 0 phá" ở n=50 đặc biệt đáng ngờ: 0 phá trên 23 bài đúng là hoàn toàn có thể
xảy ra do may mắn.

---

# Đăng ký trước #15 — H16: HOÀN TẤT LƯỚI VỚI THANH SAI SỐ (hai ô 7B còn thiếu)
**Viết TRƯỚC khi chạy.** Đây là bảng cuối cùng của dự án; cần đủ 4 ô cùng một chuẩn đo.

## Vấn đề
Hiện chỉ có thanh sai số (5 fold) cho hai ô 1.5B. Hai ô 7B mới đo MỘT LẦN:
  GSM8K 7B: V_gain ~0 (solver .916, bão hoà) | MATH 7B: V_gain +3.5 (dưới ngưỡng)
Không thể kết luận "chỉ 1/4 ô xác lập" một cách chắc chắn khi hai ô kia chưa có cùng chuẩn đo.

## H16
Chạy đúng phân tích 5-fold (PS / PSV / PSVA) cho **GSM8K 7B** và **MATH 7B**, 4-bit, mỗi fold 100 bài.
Sau đó dựng bảng 4 ô, tất cả cùng chuẩn: mean + khoảng + số fold cùng dấu.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Cả hai ô 7B đều CHỨA 0 | XÁC NHẬN "chỉ 1/4 ô xác lập". Đây là phát biểu cuối cùng của dự án. |
| MATH 7B TOÀN DƯƠNG (không chứa 0) | Thành 2/4 ô. Phải sửa phát biểu: đa tác tử có ích ở model yếu/bài dễ VÀ ở model mạnh/bài khó, nhưng KHÔNG ở hai ô còn lại. |
| GSM8K 7B TOÀN DƯƠNG | Bất ngờ (solver đã .916). Phải kiểm lại xem có lỗi đo không trước khi tin. |
| Ô nào đó TOÀN ÂM | Đa tác tử GÂY HẠI ở ô đó — phải ghi rõ, đây là cảnh báo triển khai. |

## Chỉ số chính
Mỗi ô: mean/min/max/range/std của `V_gain` và `A_gain`; số fold cùng dấu.
Bảng cuối 4 ô x {V_gain, A_gain} với khoảng, đưa thẳng vào RESULTS.md và README.

## Ghi chú trung thực
Đây là thí nghiệm KHÉP LẠI, không phải mở hướng mới. Sau H16 (cộng rc_m15 và as_m đang chạy),
dự án có đủ dữ liệu để viết báo cáo cuối; nên DỪNG mở giả thuyết mới và chuyển sang hợp nhất.

---

# Đăng ký trước #16 — H17: KIỂM CHỨNG PHÁT BIỂU HỢP NHẤT BẰNG THANH SAI SỐ
**Viết TRƯỚC khi chạy.** Đây là phép kiểm cuối cùng của dự án.

## Phát biểu cần kiểm (rút ra ở vòng #21)
"Bộ máy đa tác tử chỉ hoạt động khi MODEL ĐI KIỂM đủ mạnh để dùng được thứ nó được đưa."
Bằng chứng hiện có trên MATH:
  verifier 7B  : +14.0 [+8.3, +20.0]  5/5 fold  (ĐÃ KIỂM — H15)
  truyền trace 7B: -17.5 khi cắt      **1 LẦN ĐO** (tr_m7) — CHƯA KIỂM
  cả hai ở 1.5B : khoảng chứa 0                  (ĐÃ KIỂM — nf_m15, rc_m15)
Mắt xích YẾU NHẤT là con số -17.5: nó đang gánh nửa phát biểu mà chưa có thanh sai số.

## H17
Chạy lại FULL vs TRIM trên **5 fold rời nhau** ở **MATH 7B** (4-bit), mỗi fold 100 bài.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `trim_minus_full` TOÀN ÂM, không chứa 0 | XÁC NHẬN. Phát biểu hợp nhất đứng vững: trace chỉ có giá trị khi model kiểm đủ mạnh. |
| Khoảng CHỨA 0 | Con số -17.5 là nhiễu. Phát biểu hợp nhất chỉ còn dựa trên H15, phải phát biểu HẸP hơn: "verifier MẠNH có giá trị", KHÔNG được nói gì về trace. |
| TOÀN DƯƠNG | Đảo dấu so với lần đo đầu -> lần đầu sai hoàn toàn. Rút lại tr_m7. |
| Khoảng chồng lấn với MATH 1.5B [-6,+4] | KHÔNG kết luận được là phụ thuộc năng lực. Phải hạ cấp phát biểu hợp nhất. |

## Chỉ số chính
`trim_minus_full` từng fold; mean/min/max/range/std. So chồng lấn với MATH 1.5B [-6, +4].

## Ghi chú trung thực
Sau H17, dự án DỪNG mở thí nghiệm mới. Đây là mắt xích cuối cùng chưa có thanh sai số trong
phát biểu chính. Nếu nó sụp, phát biểu phải thu hẹp lại chỉ còn kết quả H15 — và điều đó vẫn
là kết quả tốt nhất của dự án.

---

# Đăng ký trước #17 — H18: KẾT QUẢ "MẠNH NHẤT" CÓ THẮNG NỔI MỐC TẦM THƯỜNG KHÔNG?
**Viết TRƯỚC khi chạy.** Đây là phép so sánh lẽ ra phải làm NGAY khi H15 được xác nhận.

## Vấn đề mới phát hiện
H15 xác nhận: 1.5B giải + 7B soát = **+14.0đ** so với 1.5B giải một mình (.423 -> .563).
NHƯNG đối chiếu với các kernel khác: **7B GIẢI MỘT MÌNH trên MATH = .625–.640** (4 phép đo độc lập).
=> Cấu hình "mạnh nhất" của dự án đang THẤP HƠN ~6 điểm so với việc CHỈ DÙNG 7B.
Và nó cũng KHÔNG rẻ hơn: phải trả thêm một lượt 1.5B, còn lượt 7B soát sinh gần bằng số token
mà 7B giải sẽ sinh.
CẢNH BÁO SO SÁNH: as_m dùng n=300 (5 fold x 60); các số 7B-solo từ kernel n=200 trên tập KHÁC.
Khoảng của V7 là [.517, .633] có CHẠM .625. Cần so ĐẦU-ĐỐI-ĐẦU trên CÙNG bài.

## H18
Trên CÙNG 5 fold (mỗi fold 60 bài MATH), đo 4 nhánh:
  S15      : 1.5B giải một mình
  S15+V7   : 1.5B giải + 7B soát   (cấu hình "mạnh nhất")
  S7       : 7B giải một mình      (MỐC TẦM THƯỜNG)
  S7+V7    : 7B giải + 7B soát
Đồng thời đếm SỐ TOKEN SINH RA BỞI 7B ở mỗi nhánh -> so sánh trên cùng ngân sách.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| S15+V7 >= S7 | Bất đối xứng THẮNG mốc tầm thường. Khuyến nghị hiện tại ĐỨNG VỮNG. |
| S15+V7 < S7 rõ rệt (ngoài nhiễu) | **PHẢI HẠ CẤP KHUYẾN NGHỊ ĐẦU README.** Cấu hình này bị THỐNG TRỊ bởi "chỉ dùng model lớn". Kết quả +14.0 vẫn đúng nhưng VÔ DỤNG THỰC TIỄN. |
| S15+V7 < S7 nhưng dùng ÍT TOKEN 7B hơn rõ rệt | Có giá trị dưới dạng ĐÁNH ĐỔI CHI PHÍ. Phải phát biểu kèm số token, không được nói "tốt hơn". |
| S7+V7 > S7 | Soát vẫn có ích ngay cả khi solver đã là 7B -> giá trị nằm ở VAI SOÁT, không ở chênh lệch năng lực. Phải sửa lại diễn giải của H15. |

## Chỉ số chính
acc từng nhánh trên CÙNG fold; `tokens_7B` sinh ra ở mỗi nhánh; acc trên mỗi 1000 token 7B.

## Ghi chú trung thực
Tôi đã ĐƯA cấu hình này lên tiêu đề README ở vòng #20 mà CHƯA hề so với mốc "chỉ dùng 7B".
Đó là thiếu sót nghiêm trọng: một kết quả "+14 điểm" vô nghĩa nếu phương án đơn giản hơn còn tốt hơn.
Nếu rơi hàng 2, README phải sửa NGAY.

---

# Đăng ký trước #18 — H19: SO ĐẦU-ĐỐI-ĐẦU TRÊN GSM8K (khớp với bs_m của MATH)
**Viết TRƯỚC khi chạy.**

## Lý do
Vòng #23 tính được: pipeline 1.5B 4 vai (.724) THẤP HƠN 7B-solo (.884) tới 16 điểm trên GSM8K.
Nhưng đó là SO CHÉO KERNEL, hai tập con khác nhau. Cần đo trên CÙNG bài, CÙNG fold.
bs_m đang làm việc này cho MATH; H19 làm cho GSM8K.

## H19
5 fold x 100 bài GSM8K. Bốn nhánh trên CÙNG bài:
  S15 (1.5B giải) | PIPE15 (P->S->V->A toàn 1.5B) | S7 (7B giải) | S7+V7 (7B giải + 7B soát)
Kèm đếm token sinh ra để so trên cùng ngân sách.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| PIPE15 < S7 rõ rệt (ngoài nhiễu) | XÁC NHẬN kết luận vòng #23: đa tác tử model nhỏ BỊ THỐNG TRỊ bởi model lớn. Đây là kết luận chính của báo cáo. |
| PIPE15 >= S7 | Kết luận vòng #23 SAI (do so chéo kernel). Phải rút lại NGAY và sửa README. |
| PIPE15 < S7 nhưng dùng ÍT token hơn NHIỀU | Đa tác tử có chỗ đứng ở chế độ TIẾT KIỆM. Phải phát biểu kèm số token. |
| S7+V7 > S7 rõ rệt | Vai SOÁT vẫn có giá trị ngay cả với model lớn -> khuyến nghị: dùng model lớn VÀ vẫn soát. |

## Chỉ số chính
acc từng nhánh trên CÙNG fold; tổng token sinh ra mỗi nhánh; acc trên mỗi 1000 token.

## Ghi chú trung thực
Nếu rơi hàng 2, kết luận vừa ghi ở vòng #23 phải bị RÚT LẠI. Đó là rủi ro thật vì so chéo
kernel đã từng lừa tôi một lần (con số +9.0 trên MATH hoá ra là nhiễu).

---

# Đăng ký trước #19 — H20: SỬA LỖI ĐỊNH DẠNG CÓ CỨU ĐƯỢC AGGREGATOR KHÔNG?
**Viết TRƯỚC khi chạy.** Rút thẳng từ phân tích trace ở vòng #25.

## Xuất phát (ĐO ĐƯỢC)
"Aggregator gây hại trên MATH −6.4đ" (5/5 fold) — nhưng đọc 20 ca PHÁ thì:
  85% KHÔNG phát ra \boxed | 50% tự giải lại | 40% output thoái hoá | **chỉ 5% chọn nhầm thật**
18% toàn bộ output Aggregator trên MATH không trích được đáp án.
=> Giả thuyết: đây là LỖI KỸ THUẬT, sửa được — không phải giới hạn phán đoán.

## H20 — hai bản sửa RẤT RẺ
  A_base   : như hiện tại (mốc)
  A_fallback: nếu output KHÔNG có \boxed -> LẤY ĐÁP ÁN CỦA VERIFIER (không gọi lại model)
  A_forced : prompt ép "Reply with ONLY \boxed{...}, no explanation" (giới hạn 64 token)
  A_both   : ép định dạng + fallback
Chạy 5 fold x 100 bài MATH, 1.5B.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| A_fallback hoặc A_forced ĐƯA A_gain về ≥ 0 | H20 XÁC NHẬN. "Aggregator gây hại" là LỖI KỸ THUẬT, sửa bằng 1 dòng code. Phải sửa lại diễn giải trong RESULTS.md/README. |
| Có cải thiện nhưng A_gain VẪN âm | Lỗi định dạng chỉ là MỘT PHẦN. Phải báo cả hai thành phần, không quy hết cho định dạng. |
| Không cải thiện | Diễn giải "lỗi định dạng" SAI. Vấn đề nằm sâu hơn. Rút lại kết luận vòng #25. |
| A_forced LÀM TỆ HƠN | Ép định dạng làm mất khả năng suy luận (khớp kết quả struct/showwork trước đây). Ghi rõ. |

## Chỉ số chính
`A_gain` (= acc_A − acc_V) từng nhánh, 5 fold, kèm khoảng; và `boxed_rate` từng nhánh
(kiểm tra can thiệp CÓ hiệu lực).

## Ghi chú trung thực
Nếu H20 xác nhận, thì một trong những "phát hiện" chắc chắn nhất của dự án (Aggregator gây hại,
5/5 fold) hoá ra chỉ là lỗi parsing — và điều đó phải được ghi rõ ở đầu RESULTS.md.

---

# Đăng ký trước #20 — H21: VERIFIER "VÁ LỖI" vs VERIFIER "GIẢI LẠI"; và PLANNER CÓ ĐANG GIẤU ĐÁP ÁN?
**Viết TRƯỚC khi chạy.** Cả hai câu hỏi do người dùng đặt ra; số đo hiện có ủng hộ mạnh.

## Bằng chứng xuất phát (ĐO ĐƯỢC từ 600 trace)
(a) Tỉ lệ Verifier TÁI SỬ DỤNG số của Solver, theo hành vi:
      GSM8K: đồng ý .20 | SỬA **0.00** | PHÁ **0.00**      MATH: đồng ý 1.00 | SỬA .33 | PHÁ .29
    => Mỗi khi CAN THIỆP, Verifier VỨT BỎ toàn bộ chuỗi của Solver và GIẢI LẠI TỪ ĐẦU.
    => Giải thích được vì sao độ chính xác can thiệp chỉ ~56% ≈ ĐỘ CHÍNH XÁC TỰ GIẢI của model
       (1.5B giải GSM8K ~.63), chứ không phải độ chính xác của việc KIỂM (lẽ ra phải dễ hơn).
(b) Planner sinh 6 SỐ MỚI ở 100% số lượt (0% lượt không tính toán), nhưng chỉ 3.3% có \boxed.
    => Giả thuyết: chỉ dẫn "Do NOT compute the final answer" KHÔNG ngăn nó tính,
       chỉ khiến nó GIẤU đáp án.

## H21a — ÉP VÁ LỖI THAY VÌ GIẢI LẠI
Verifier chỉ được phép: chỉ ra BƯỚC SAI ĐẦU TIÊN và viết tiếp TỪ ĐÓ. Phần trước GIỮ NGUYÊN
bằng CODE (ghép chuỗi), không phụ thuộc việc model có nghe lời hay không.
  V_std  : verifier như hiện tại (mốc)
  V_patch: ghép [tiền tố Solver tới bước sai] + [phần viết tiếp của Verifier]
  V_none : chỉ đáp án (đối chứng)

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| V_patch > V_std rõ rệt, và tỉ lệ tái sử dụng TĂNG | H21a XÁC NHẬN. "Verifier là solver thứ hai" là lỗi THIẾT KẾ, sửa được bằng cách ép vá lỗi. |
| V_patch ~ V_std | Ép vá lỗi không giúp. Vấn đề không nằm ở việc giải lại. Ghi rõ đã bác. |
| V_patch < V_std | Tiền tố của Solver là GÁNH NẶNG, không phải tài sản — giải lại từ đầu TỐT HƠN. Đảo ngược trực giác, phải ghi rõ. |
| tỉ lệ tái sử dụng KHÔNG tăng | CAN THIỆP VÔ HIỆU (ghép chuỗi không có tác dụng). Không kết luận về H21a. |

## H21b — PLANNER CÓ ĐANG GIẤU ĐÁP ÁN KHÔNG?
  P_hide : prompt hiện tại ("Do NOT compute the final answer")
  P_free : BỎ chỉ dẫn đó, cho phép tính thoải mái
  P_ask  : YÊU CẦU tính luôn đáp án
Đo: độ chính xác của ĐÁP ÁN NGẦM trong kế hoạch (trích 3 cách), và acc của Solver phía sau.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| acc đáp án ngầm của P_hide ≈ P_free ≈ P_ask | XÁC NHẬN: chỉ dẫn chỉ GIẤU, không ngăn tính. "Planner" thực chất là một Solver bị bịt miệng. |
| P_hide THẤP HƠN rõ rệt | Chỉ dẫn THỰC SỰ ngăn nó tính. Bác giả thuyết. |
| P_free/P_ask làm Solver phía sau TỐT HƠN | Giấu đáp án đang GÂY HẠI -> nên bỏ chỉ dẫn đó. Khuyến nghị trực tiếp. |
| P_free/P_ask làm Solver phía sau TỆ HƠN | Giấu đáp án CÓ tác dụng (tránh mỏ neo). Giữ nguyên thiết kế. |

## Ghi chú trung thực
H21a có thể thất bại: tôi đã từng thử ép định dạng cho Verifier (struct/V_ST) và nó LÀM TỆ ĐI.
Lần này khác ở chỗ việc GIỮ TIỀN TỐ do CODE làm, không nhờ model tuân lệnh.

---

# Đăng ký trước #21 — H22: BỎ CHỈ DẪN "ĐỪNG TÍNH/ĐỪNG VIẾT CODE" CÓ CÒN ĐÚNG TRÊN CODE KHÔNG?
**Viết TRƯỚC khi chạy.**
ĐO ĐƯỢC (H21b): bỏ "Do NOT compute the final answer" khỏi Planner làm Solver TỐT HƠN
  MATH +3.75 (5/5 fold), GSM8K +3.25 (4/5) -> gộp 9/10 fold, p~.02.
Câu hỏi: có chuyển sang MIỀN CODE không? (HumanEval, chấm bằng CHẠY TEST -> chân lý chính xác)
Nhánh (5 fold x 32 bài, 1.5B): NoP (không planner) | P_hide ("đừng viết code")
  | P_free (không cấm) | P_ask (yêu cầu viết luôn code)

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| P_free/P_ask > P_hide ở đa số fold | XÁC NHẬN, hiệu ứng TỔNG QUÁT qua 3 miền -> khuyến nghị chung: bỏ chỉ dẫn cấm. |
| P_free ~ P_hide | KHÔNG tổng quát sang code. Kết luận H21b chỉ giới hạn ở toán. Ghi rõ. |
| P_free < P_hide | ĐẢO DẤU trên code. Thêm một bằng chứng "hiệu ứng không bền theo miền". |
| NoP >= mọi nhánh có planner | Trên code, Planner VÔ DỤNG hoặc CÓ HẠI bất kể prompt. Kết luận kiến trúc. |

Chỉ số chính: pass@1 (chạy test) từng nhánh, 5 fold, kèm khoảng + số fold cùng dấu.
Ghi chú: HumanEval n=164 nên fold nhỏ (32 bài) -> nhiễu lớn hơn; chỉ kết luận khi ĐA SỐ fold cùng dấu.

---

# Đăng ký trước #22 — H23: GRPO TRÊN VERIFIER (tối ưu ĐỘ CHÍNH XÁC CAN THIỆP)
**Viết TRƯỚC khi chạy.** Chạy trên RTX 5090, sau khi pat15/pat7 xong.

## Mục tiêu — đúng khiếm khuyết ĐÃ ĐO
Verifier 1.5B can thiệp với độ chính xác chỉ **56%** (≈ độ chính xác TỰ GIẢI của nó), vì nó
GIẢI LẠI thay vì KIỂM (tái sử dụng 0% số của Solver khi can thiệp).
=> Phần thưởng RL ĐẶT ĐÚNG vào đó: +1 nếu SỬA ĐÚNG (Solver sai -> Verifier đúng),
   −1 nếu PHÁ (Solver đúng -> Verifier sai), 0 nếu không đổi kết quả.
   Đây CHÍNH LÀ đại lượng mà mọi thí nghiệm trước đo được là hỏng.

## Thiết lập
GRPO + LoRA trên Qwen2.5-1.5B (không cần value model; policy tham chiếu = tắt adapter).
Dữ liệu: GSM8K **main_train** (tách hoàn toàn khỏi test). Mỗi bài: Solver sinh 1 lời giải (đóng băng),
Verifier sinh k=4 phản hồi -> tính reward -> advantage = r − mean(r) trong nhóm.
Đánh giá: GSM8K test, 5 fold, so `V_gain` và ĐỘ CHÍNH XÁC CAN THIỆP trước/sau.

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Độ chính xác can thiệp TĂNG rõ (>65%) VÀ V_gain tăng | H23 XÁC NHẬN. RL sửa được khiếm khuyết mà prompting không sửa nổi. |
| Độ chính xác can thiệp tăng nhưng V_gain KHÔNG tăng | Nó học cách CAN THIỆP ÍT ĐI chứ không CHÍNH XÁC HƠN. Phải báo kèm SỐ LẦN can thiệp. |
| Không đổi | RL không giúp ở quy mô này. Ghi rõ đã bác. Củng cố khuyến nghị "dùng model lớn hơn". |
| Sụp đổ / reward hacking (vd luôn đồng ý) | Ghi rõ. Phần thưởng thưa (chỉ ~15-20% bài có can thiệp) là rủi ro đã biết. |

## Chỉ số BẮT BUỘC báo
`V_gain`, ĐỘ CHÍNH XÁC CAN THIỆP, **SỐ LẦN CAN THIỆP** (để phát hiện "học cách im lặng"),
và so với mốc **7B verifier không huấn luyện** (98%) — nếu RL không vượt được mốc đó thì
khuyến nghị vẫn là "dùng model lớn hơn".

## Prior TRUNG THỰC (ghi trước)
Tôi đã lập luận RL là công cụ SAI ở đây vì đã có nhãn trực tiếp (grader) -> học có giám sát
dùng tín hiệu đó tốt hơn. Reward rất THƯA. Tôi cho rằng khả năng cao rơi vào hàng 2 hoặc 3.
Vẫn chạy vì người dùng yêu cầu và vì nó nhắm ĐÚNG khiếm khuyết đã đo.
