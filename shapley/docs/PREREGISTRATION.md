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

---

# Đăng ký trước #23 — H24: "SỬA LỖI" CỦA VERIFIER CHỈ LÀ GIẢI LẠI, KHÔNG PHẢI KIỂM LỖI
**Viết TRƯỚC khi chạy.** Rút ra từ vòng #43.

## Vì sao hỏi câu này
Nhánh giả dược X (verifier thấy lời giải của BÀI KHÁC) có fix_rate CAO NHẤT ở GSM8K 7B
(.381 > blind .286 > informed .191). Context của X vô nghĩa nên "sửa" của nó KHÔNG THỂ là
kiểm lỗi. Cộng với phát hiện cũ (verifier tái sử dụng 0% con số của Solver) và với H21a
(ép giữ tiền tố của Solver làm verifier TỆ ĐI, 3 lần chạy độc lập), giả thuyết hợp lý là:
**vai "verifier" không kiểm gì cả — nó chỉ là một LẦN LẤY MẪU THỨ HAI được đặt tên khác.**
Nếu đúng, toàn bộ khung "verification" của dự án phải phát biểu lại, và khuyến nghị thực tế
là thay verifier bằng lấy mẫu nhiều lần + bỏ phiếu (rẻ hơn, đã biết là mạnh).

## Thiết kế — CÙNG MỘT bộ lời giải của Solver, 4 nhánh, mỗi nhánh ĐÚNG 1 lần sinh thêm
- **V_inf**  : "Check the proposed solution..." + TOÀN BỘ lời giải   (đối chứng trên)
- **V_bli**  : "Check the proposed solution..." + CHỈ đáp án          (nhánh mạnh nhất ở #2)
- **S_anc**  : "Solve step by step. A previous attempt answered <A>." — CÓ mỏ neo, KHÔNG có khung kiểm
- **S_pln**  : "Solve step by step."  (temp 0.7, hạt giống khác)      — KHÔNG neo, KHÔNG khung kiểm
Chi phí bằng nhau (1 lần sinh). So sánh trên CÙNG phân hoạch đúng/sai của Solver.

## Chỉ số chính
`fixes` (Solver sai -> nhánh đúng) và `breaks` (Solver đúng -> nhánh sai), theo từng nhánh.
Phụ: `changed_answer`, và tỉ lệ nhánh nhắc lại con số của Solver (đo mỏ neo có hiệu lực).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| S_pln ≈ V_bli ở CẢ fixes VÀ breaks (chênh trong sàn nhiễu) ở >=3/4 ô | **H24 XÁC NHẬN.** Khung "kiểm lỗi" không đóng góp gì ngoài một mẫu thứ hai. Phải phát biểu lại toàn bộ ngôn ngữ "verifier" của dự án và khuyến nghị bỏ phiếu thay vì verify. |
| V_bli sửa NHIỀU HƠN S_pln, p<.05, >=3/4 ô | **H24 BỊ BÁC.** Khung kiểm lỗi làm việc thật. Giữ nguyên ngôn ngữ verifier. |
| fixes bằng nhau NHƯNG V_bli phá ÍT HƠN S_pln, p<.05 | H24 BÁC MỘT PHẦN. Khung kiểm không tăng PHÁT HIỆN mà tăng TÍNH CHỌN LỌC. Phải phát biểu hẹp đúng như vậy. |
| S_anc ≈ V_bli nhưng cả hai khác S_pln | Thứ có tác dụng là MỎ NEO ĐÁP ÁN, không phải khung kiểm. Ngôn ngữ "verify" vẫn phải bỏ. |
| Kết quả trái chiều giữa các ô | KHÔNG kết luận chung. Ghi "phụ thuộc ô", không được chọn ô đẹp để kể. |

## Prior TRUNG THỰC (ghi trước)
Tôi cho rằng H24 nhiều khả năng XÁC NHẬN (hàng 1) hoặc rơi hàng 4. Ba mảnh bằng chứng độc lập
đã chỉ cùng hướng: reuse 0%, H21a bị bác 3 lần, X-giả dược sửa nhiều nhất. Nếu đúng thì đây là
phát hiện LỚN NHẤT của dự án và đồng thời là lời tự bác bỏ mạnh nhất — phần lớn công sức trước
đây được tiêu vào việc tinh chỉnh một vai mà có thể chưa bao giờ làm đúng việc nó được đặt tên.
Tôi ghi rõ điều này TRƯỚC khi có số để không thể diễn giải lại sau.

## Bắt buộc
Lưu >=50 trace thô mỗi nhánh (`traces.json`) — mọi phát hiện cơ chế của dự án đều đến từ đọc trace.

---

# Đăng ký trước #24 — H25: KIỂM LỖI CÓ PHẢI KỸ NĂNG TÁCH RỜI KHỎI GIẢI KHÔNG?
**Viết TRƯỚC khi chạy.** Trả lời đề xuất "fine-tune / thưởng theo bước để củng cố đúng vai".

## Vì sao phải hỏi câu này TRƯỚC khi huấn luyện
Đề xuất: SFT trên đáp án ĐÚNG, hoặc thưởng theo BƯỚC đúng, để củng cố từng vai.
VẤN ĐỀ LOGIC: nếu SFT verifier trên "câu kiểm đúng", các câu đó chỉ có thể sinh ra từ việc
model GIẢI ĐÚNG. Vậy SFT-trên-đáp-án-đúng = huấn luyện một SOLVER TỐT HƠN rồi gọi nó là verifier.
Nó sẽ LÀM SÂU THÊM sự sụp đổ vai mà vòng #43-#44 đã đo, chứ không sửa được.
Vai chỉ có ý nghĩa nếu verifier làm được thứ solver KHÔNG làm được.
=> Phải đo TRƯỚC: **model có phát hiện được lỗi trong bài mà chính nó KHÔNG giải nổi không?**
Nếu KHÔNG -> kiểm lỗi bị chặn bởi năng lực giải, không có vai nào để củng cố, mọi kế hoạch
huấn luyện vai đều vô nghĩa. Nếu CÓ -> vai kiểm lỗi CÓ THẬT và đáng huấn luyện.

## Thiết kế — TRÁNH nhiễu văn phong (đã tính trước)
Không dùng "lời giải model" làm nhánh sai và "lời giải vàng" làm nhánh đúng — văn phong sẽ
LỘ NHÃN. Thay vào đó CẢ HAI nhánh đều là chuỗi vàng của GSM8K:
- **CLEAN** : chuỗi vàng nguyên vẹn
- **CORRUPT**: chuỗi vàng bị đổi kết quả của ĐÚNG MỘT bước `<<a op b = c>>` thành c' != c
  (chỉ một bước sai số học; mọi thứ khác giữ nguyên) — phát hiện nó KHÔNG cần giải lại từ đầu
Câu hỏi cho model: "Does this solution contain a computational error? YES/NO."

## Phân tầng theo NĂNG LỰC GIẢI (đo bằng chính model, k=8 mẫu, temp .8)
- `HIGH` : giải đúng >= 6/8   | `MID` : 1–5/8   | `ZERO`: **0/8 — model KHÔNG giải nổi**
Chỉ số chính: **độ chính xác phát hiện trong tầng ZERO**, cùng độ lệch phản hồi
(tỉ lệ nói "YES" trên CLEAN vs CORRUPT — đo phân biệt, miễn nhiễm với thiên lệch trả lời).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Phát hiện ở ZERO cao rõ (>=70%) và gần bằng HIGH | **Kiểm lỗi LÀ kỹ năng tách rời.** Vai verifier CÓ THẬT. Đề xuất huấn luyện theo vai là ĐÚNG HƯỚNG -> chuyển sang SFT phân biệt / thưởng theo bước. |
| Phát hiện ở ZERO ≈ ngẫu nhiên (45–55%) trong khi HIGH cao | **Kiểm lỗi BỊ CHẶN bởi năng lực giải.** Không có vai để củng cố. Phải nói thẳng: mọi kế hoạch huấn luyện vai trên model này là vô nghĩa; khuyến nghị vẫn là dùng model lớn hơn. |
| Phát hiện thấp ở MỌI tầng | Model không làm nổi cả nhiệm vụ kiểm đơn giản nhất. Ghi rõ. Bác bỏ toàn bộ hướng "vai". |
| Phát hiện cao ở MỌI tầng kể cả ZERO, nhưng cũng nói "có lỗi" trên CLEAN | Không phải phát hiện — chỉ là thiên lệch luôn-nói-sai. Phải báo tỉ lệ YES trên CLEAN. |
| 1.5B và 7B trái chiều | Ghi "phụ thuộc năng lực", không kết luận chung. |

## Prior TRUNG THỰC (ghi trước)
Ba bằng chứng độc lập (tái sử dụng 0%, H21a bác 3 lần, giả dược X sửa nhiều nhất) đều nói
verifier chỉ đang giải lại. Nhưng CẢ BA đều đo nhiệm vụ SỬA, chưa bao giờ đo nhiệm vụ PHÁT HIỆN
tách riêng. Tôi cho rằng phát hiện lỗi số học ĐƯỢC TIÊM SẴN sẽ dễ hơn hẳn, nên tôi nghiêng về
hàng 1 ở tầng HIGH/MID, và THẬT SỰ KHÔNG BIẾT ở tầng ZERO — đó chính là lý do phải chạy.
Nếu ra hàng 2 thì đề xuất huấn luyện vai bị bác, và tôi phải nói thẳng điều đó.

## Bắt buộc
Lưu >=50 trace mỗi tầng × mỗi nhánh. Báo tỉ lệ nói YES trên CLEAN (thiên lệch) cùng độ chính xác.

---

# Đăng ký trước #25 — H26: MỖI VAI MỘT ADAPTER RIÊNG, THƯỞNG BẰNG ĐÓNG GÓP BIÊN
**Viết TRƯỚC khi chạy.** Theo đề xuất: "củng cố TỪNG MODEL vào ĐÚNG VAI của nó."

## Khác gì H23 (đã thất bại)
H23: MỘT model, MỘT adapter, đội mũ prompt khác nhau -> vẫn là một model. Đã đo: sụp đổ vai.
H26: **BA adapter LoRA RIÊNG BIỆT** trên cùng base 1.5B (A_plan / A_solve / A_verify),
mỗi adapter có HÀM THƯỞNG RIÊNG. Đây mới đúng là "mỗi model một vai".

## Phần thưởng = ĐÓNG GÓP BIÊN (leave-one-out) — chính đại lượng dự án này đo bằng Shapley
Mỗi bài chạy 4 biến thể: {S}, {P,S}, {S,V}, {P,S,V}. Từ đó:
  r_solve  = 1[{S} đúng]
  r_plan   = 1[{P,S} đúng] − 1[{S} đúng]
  r_verify = 1[{S,V} đúng] − 1[{S} đúng]  **CỘNG phạt im lặng: −0.3 nếu {S} SAI mà V không đổi gì**
Phạt im lặng là bản vá TRỰC TIẾP cho lỗi đã đo ở H23: reward cũ cho "không đổi" = 0 nên
IM LẶNG LÀ MIỄN PHÍ và policy đã chọn đúng lối đó. Giờ im lặng khi Solver sai PHẢI trả giá.

## Chỉ số BẮT BUỘC báo (mỗi vai)
- V_gain, SỐ LẦN CAN THIỆP (bẫy im lặng — H23 đã dính)
- **`plan_reveals_answer`**: tỉ lệ kế hoạch chứa đáp án cuối. Đã đo ở vòng trước: Planner
  vốn GIẢI RỒI GIẤU. Nếu thưởng theo đóng góp biên, lối tối ưu TẦM THƯỜNG là kế hoạch
  NÓI THẲNG đáp án. KHÔNG cấm — để nó tự tìm, và ĐO xem có tìm ra không.
- Độ tương đồng giữa 3 adapter (chuẩn LoRA delta) — vai có THỰC SỰ tách ra không?

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Cả 3 vai đều tăng đóng góp biên, pipeline {P,S,V} > baseline, và 3 adapter KHÁC nhau rõ | **H26 XÁC NHẬN. Chuyên biệt hoá theo vai LÀ HỌC ĐƯỢC.** Đề xuất của người dùng đúng; hướng đi mới của dự án. |
| Chỉ A_solve tăng, A_plan/A_verify ≈ 0 | Chỉ có vai GIẢI là học được. Vai phụ không có tín hiệu để học. Ghi rõ: phân rã vai không phải trừu tượng đúng ở quy mô này. |
| A_plan hội tụ về NÓI THẲNG ĐÁP ÁN (`plan_reveals_answer` tăng mạnh) | Chuyên biệt hoá "thành công" bằng cách BIẾN PLANNER THÀNH SOLVER. Phải báo đúng như vậy, KHÔNG được kể là chuyên biệt hoá vai. |
| A_verify lại im lặng dù đã phạt | Phạt chưa đủ / reward vẫn thưa. H23+H26 cùng bác -> DỪNG hướng RL cho verifier. |
| 3 adapter hội tụ về gần như GIỐNG NHAU (delta tương đồng cao) | Vai KHÔNG tách được kể cả khi cho tham số riêng. Đây là bằng chứng MẠNH NHẤT cho sự sụp đổ vai. |
| Pipeline sau huấn luyện < maj@8 chưa huấn luyện | Toàn bộ hướng đa tác tử thua lấy mẫu song song. Phải nói thẳng. |

## Phụ thuộc
Nhánh A_verify chỉ có ý nghĩa nếu **H25 (đăng ký #24)** cho thấy phát hiện lỗi TÁCH RỜI khỏi giải.
Nếu H25 ra hàng 2 (phát hiện bị chặn bởi năng lực giải) thì A_verify KHÔNG có gì để học,
và điều đó phải được ghi là ĐÃ BIẾT TRƯỚC, không phải phát hiện sau.

## Prior TRUNG THỰC (ghi trước)
Tôi nghiêng về hàng 2 hoặc hàng 3. Lý do: H24 ô đầu vừa đo được `S_anc` (KHÔNG có khung kiểm)
ngang `V_bli` -> khung vai không mang thông tin; và Planner đã được đo là "giải rồi giấu",
nên thưởng theo đóng góp biên nhiều khả năng đẩy nó tới chỗ NÓI THẲNG đáp án.
Tôi ghi trước để nếu ra hàng 3 thì KHÔNG được kể thành công.
Vẫn chạy vì: (a) chưa ai cho mỗi vai THAM SỐ RIÊNG — mọi kết luận sụp đổ vai trước đây đều ở
điều kiện dùng CHUNG tham số, nên chưa phải phép thử công bằng; (b) đó là phép thử SẠCH nhất
cho câu hỏi trung tâm của dự án.

---

# Đăng ký trước #26 — H25b: CHẠY LẠI H25, CHO PHÉP SUY LUẬN TRƯỚC KHI PHÁN
**Viết TRƯỚC khi chạy.** Sửa khiếm khuyết thiết kế của chính tôi ở #24.

## Vì sao chạy lại
dt_g15 cho phân biệt = **.000 CHÍNH XÁC ở cả 3 tầng**, trace cho thấy model xuất `NO` ở
**392/392** lượt. Kernel chỉ cho `max_new_tokens=16` và ép phán ngay -> model không có chỗ tính.
Hiệu ứng sàn hoàn hảo tố cáo DỤNG CỤ, không phải năng lực. H25 do đó là CHƯA KIỂM.

## Sửa gì
- Cho kiểm TỪNG BƯỚC rồi mới chốt dòng cuối `VERDICT: YES` / `VERDICT: NO`, **400 token**.
- Vẫn giữ nguyên: hai nhánh đều là chuỗi vàng (CLEAN vs CORRUPT một bước) -> không lộ nhãn qua văn phong.
- Vẫn phân tầng theo năng lực giải của chính model (k=8).

## NGƯỠNG HIỆU LỰC — khoá TRƯỚC (đây chính là thứ #24 THIẾU)
- `degenerate_rate` = tỉ lệ của câu trả lời phổ biến nhất. Nếu **> .90** ở một tầng ->
  tầng đó **VÔ HIỆU**, KHÔNG được đọc là "không phát hiện được".
- `parse_fail_rate` > .20 -> toàn bộ lần chạy VÔ HIỆU.
Hai ngưỡng này áp dụng cho MỌI thí nghiệm phán đoán nhị phân về sau. Đây là LUẬT mới của dự án.

## Cam kết diễn giải (khoá TRƯỚC khi có số) — chỉ đọc các tầng HỢP LỆ
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Phân biệt ở ZERO >= .40 và gần HIGH | **Kiểm lỗi LÀ kỹ năng tách rời.** Vai verifier có thật -> huấn luyện theo vai là đúng hướng. |
| Phân biệt HIGH cao nhưng ZERO ≈ 0 | **Kiểm lỗi BỊ CHẶN bởi năng lực giải.** Không có vai để củng cố. Nhánh A_verify của H26 vô nghĩa. |
| Phân biệt thấp ở mọi tầng HỢP LỆ | Model không kiểm được lỗi số học dù được suy luận. Bác hướng "vai kiểm". |
| Vẫn suy biến >.90 dù đã cho 400 token | Không kết luận gì về năng lực. Ghi: nhiệm vụ phán nhị phân KHÔNG đo được ở 1.5B; phải đổi cách hỏi. |
| 1.5B và 7B trái chiều | "Phụ thuộc năng lực", không kết luận chung. |

## Prior TRUNG THỰC (ghi trước)
Tôi cho rằng khi được suy luận, model sẽ hết suy biến và phân biệt sẽ DƯƠNG RÕ ở tầng HIGH.
Ở tầng ZERO tôi vẫn THẬT SỰ KHÔNG BIẾT — đó vẫn là câu hỏi trung tâm.
Lưu ý trung thực: lỗi được TIÊM vào là lỗi SỐ HỌC MỘT BƯỚC, dễ hơn lỗi suy luận thật.
Nếu ngay cả lỗi này cũng không phát hiện nổi thì kết luận rất mạnh; nhưng nếu phát hiện được,
KHÔNG được suy rộng thành "biết kiểm lỗi nói chung".

---

# Đăng ký trước #27 — H27: VERIFIER PHÂN BIỆT (chấm điểm) THAY VÌ VERIFIER SINH VĂN BẢN
**Viết TRƯỚC khi chạy.** Trả lời đề xuất "lấy output rồi gán nhãn để có dữ liệu fine-tune".

## Ba điều dữ liệu ĐÃ ĐO nói trước khi thiết kế
1. **Nhãn KHÔNG cần gán tay.** Grader (đáp án vàng) đã cho nhãn đúng/sai MIỄN PHÍ ở quy mô
   không giới hạn. Gán tay chỉ đáng cho nhãn TỪNG BƯỚC — mà thứ đó cũng lấy tự động được
   (tung nhiều lần từ mỗi tiền tố, hoặc TIÊM lỗi vào chuỗi vàng như kernel dt đang làm).
2. **Mọi thứ đã thất bại đều là verifier SINH VĂN BẢN** (H21a bác 3 lần, H23 im lặng,
   H24 ô g15 cho thấy `S_anc` không có khung kiểm vẫn ngang `V_bli`). Chưa BAO GIỜ thử
   verifier PHÂN BIỆT (xuất một điểm số, không viết lại lời giải).
3. **Khoảng trống ĐÃ ĐO**: maj@8 -> oracle@8 = **+17.5 điểm (1.5B)**, **+11.7 điểm (7B)**.
   Câu trả lời ĐÚNG đã nằm sẵn trong 8 mẫu; bỏ phiếu chỉ không chọn được nó.
   Đây là chỗ DUY NHẤT trong dự án có headroom lớn đã đo, không phải phỏng đoán.

## Thiết kế
- **Dữ liệu (nhãn tự động)**: 800 bài GSM8K *train*, mỗi bài 8 mẫu (temp .8) -> ~6400 cặp
  (lời giải, đúng/sai) do grader chấm. KHÔNG có nhãn tay.
- **Huấn luyện**: LoRA, dạy model xuất token `Yes`/`No` cho câu "Is this solution correct?".
  Điểm số khi suy luận = logprob của token `Yes`. Không thêm đầu phân loại -> giữ đơn giản.
- **Dùng**: sinh k=8 trên test, CHẤM cả 8, chọn điểm cao nhất (**rerank@8**).
- **So với**: greedy, maj@8, oracle@8 (trần), và maj@8 CỦA CÙNG 8 MẪU ĐÓ (so sánh cặp).

## NGƯỠNG HIỆU LỰC — khoá TRƯỚC (theo luật mới lập ở #26)
- **AUC** của bộ chấm trên tập test phải **> .55**. Nếu AUC ≈ .50 -> bộ chấm KHÔNG học được gì,
  kết quả rerank là NGẪU NHIÊN và KHÔNG được đọc là "phân biệt thất bại vì nhiệm vụ khó".
- `degenerate_rate` của Yes/No > .90 -> VÔ HIỆU.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| rerank@8 > maj@8, >=4/5 fold, và AUC > .55 | **H27 XÁC NHẬN.** Verifier PHÂN BIỆT làm được thứ verifier SINH VĂN BẢN không làm nổi. Đây là hướng đúng để dùng nhãn tự động; khuyến nghị của dự án phải đổi. |
| rerank@8 ≈ maj@8 (chênh trong sàn nhiễu) | Chấm điểm không thêm gì so với đếm phiếu. Bỏ phiếu vẫn là cách tổng hợp nên dùng. |
| rerank@8 < maj@8 | Bộ chấm TỆ HƠN đếm phiếu. Ghi rõ đã bác. Không được đổ cho "thiếu dữ liệu" nếu AUC > .55. |
| AUC <= .55 | VÔ HIỆU cho câu hỏi rerank. Kết luận HẸP: 1.5B không học được hàm phân biệt đúng/sai từ 6400 mẫu. Phải nói rõ đây là giới hạn NĂNG LỰC/DỮ LIỆU, chưa bác được hướng phân biệt. |
| rerank@8 chạm gần oracle@8 (>= 80% khoảng trống) | Kết quả MẠNH NHẤT dự án từng có. Phải kiểm lại rò rỉ dữ liệu train/test trước khi báo. |

## Prior TRUNG THỰC (ghi trước)
Đây là hướng tôi tin NHẤT trong toàn dự án, vì: (a) nhãn miễn phí và nhiều; (b) phân biệt là
nhiệm vụ DỄ HƠN sinh; (c) headroom đã ĐO chứ không suy đoán. Tôi đoán rerank@8 sẽ vượt maj@8
vài điểm nhưng KHÔNG chạm oracle.
CẢNH BÁO tự đặt: nếu H25b cho thấy 1.5B không phân biệt nổi chuỗi vàng SẠCH và chuỗi BỊ TIÊM LỖI,
thì AUC ở đây nhiều khả năng thấp -> phải đọc theo hàng 4, KHÔNG được kể thành "cần thêm dữ liệu".

---

# Đăng ký trước #28 — H25c: LÀM ĐÔNG TẦNG "KHÔNG GIẢI NỔI" BẰNG MATH
**Viết TRƯỚC khi chạy.** dt2_g7 cho hàng 1 nhưng tầng quyết định chỉ có **9 cặp**.

## Vấn đề CHÍNH XÁC cần sửa
7B giải GSM8K .867 -> tầng ZERO rỗng do THIẾT KẾ. Phân biệt .444 ở n=9 có khoảng tin cậy
gần như chắc chắn chứa 0. Không được kết luận từ đó.
=> Chạy lại trên **MATH-500** ở 7B (solver đã đo .625) và **MATH ở 1.5B** (solver .405),
   nơi tầng ZERO sẽ đông hơn nhiều lần.
=> Cỡ mẫu MỤC TIÊU: >= 40 cặp ở tầng ZERO. Nếu không đạt, ghi rõ là KHÔNG ĐỦ LỰC.

## Khác biệt kỹ thuật với dt2
MATH không có chú thích `<<a op b=c>>` như GSM8K -> phải tiêm lỗi bằng cách khác:
lấy chuỗi lời giải VÀNG của MATH, tìm biểu thức số học `a op b = c` bằng regex thường,
đổi `c` thành `c'`. Nếu không tìm được biểu thức nào thì BỎ bài đó (ghi số bài bị bỏ).
**Kiểm tra hiệu lực BẮT BUỘC**: báo `pct_problems_corruptible`. Nếu < .50 thì phép đo
VÔ HIỆU vì mẫu còn lại đã bị chọn lọc thiên lệch (chỉ giữ bài nhiều số học).

## NGƯỠNG HIỆU LỰC (giữ nguyên từ #26, thêm một điều kiện)
- `degenerate_rate` > .90 ở một tầng -> tầng đó VÔ HIỆU
- `parse_fail_rate` > .20 -> cả lần chạy VÔ HIỆU
- **n_pairs < 40 ở tầng ZERO -> tầng ZERO KHÔNG ĐƯỢC DÙNG ĐỂ KẾT LUẬN** (chỉ báo cáo, ghi "thiếu lực")

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| ZERO n>=40 và phân biệt >= .40 ở 7B | **XÁC NHẬN: kiểm lỗi TÁCH RỜI khỏi giải ở 7B.** Đây là phát hiện dương mạnh nhất của dự án. Vai verifier có thật; huấn luyện phân biệt là hướng đúng. |
| ZERO n>=40 và phân biệt ≈ 0 ở 7B, trong khi HIGH cao | **BÁC: kiểm lỗi BỊ CHẶN bởi năng lực giải.** dt2_g7 chỉ là ảo ảnh của n=9. Phải rút lại cách đọc lạc quan ở vòng #48. |
| 7B phân biệt tốt mọi tầng, 1.5B vẫn suy biến | "Phụ thuộc NĂNG LỰC" — có ngưỡng năng lực cho việc kiểm. Không được suy rộng xuống model nhỏ. |
| Cả hai model suy biến trên MATH | Nhiệm vụ tiêm-lỗi không đo được trên MATH. Kết quả GSM8K đứng một mình, phải nói rõ chỉ có 1 miền. |
| `pct_problems_corruptible` < .50 | Lần chạy VÔ HIỆU. Thiết kế lại cách tiêm lỗi. |

## Prior TRUNG THỰC (ghi trước)
Sau dt2_g7 tôi NGHIÊNG về hàng 1 (phân biệt sống sót ở tầng ZERO đông hơn). Nhưng tôi đã sai
nhiều lần trong dự án này khi ngoại suy từ mẫu nhỏ, và n=9 chính là mẫu nhỏ.
Tôi ghi rõ: nếu ra hàng 2, tôi PHẢI rút lại cách đọc ở vòng #48 và nói thẳng là đã mừng sớm.

---

# Đăng ký trước #29 — H28: BỎ PHIẾU CÓ TRỌNG SỐ (giữ đồng thuận + dùng điểm)
**Viết TRƯỚC khi chạy.** Rút thẳng từ nghịch lý của H27.

## Sự việc đã đo
Bộ chấm phân biệt rất tốt (**AUC .883**) nhưng dùng theo kiểu **argmax một mẫu** cho
rerank@8 = .687 < maj@8 = .703. Khoảng trống maj->oracle còn **+14.0 điểm** chưa lấy được.
GIẢ THUYẾT: argmax vứt bỏ thông tin ĐỒNG THUẬN mà đếm phiếu đang khai thác.

## Thiết kế — CÙNG bộ 8 mẫu, CÙNG bộ chấm đã huấn luyện, chỉ đổi CÁCH TỔNG HỢP
- `maj8`      : đếm phiếu thường (mốc)
- `rerank8`   : argmax điểm (đã đo, để đối chiếu)
- **`wvote_sum`** : gom mẫu theo đáp án; điểm nhóm = TỔNG prob(Yes); chọn nhóm cao nhất
- **`wvote_mean`**: điểm nhóm = TRUNG BÌNH prob(Yes) (tách ảnh hưởng của cỡ nhóm)
- `oracle8`   : trần
Chỉ số chính: `wvote_sum − maj8` theo từng fold (5 fold, so sánh CẶP trên cùng mẫu).

## NGƯỠNG HIỆU LỰC (khoá trước)
- AUC của bộ chấm phải > .55 (đã đạt .883 ở lần huấn luyện này; huấn luyện lại phải báo lại).
- Nếu `maj8` lần này lệch quá 5 điểm so với .703 đã đo -> nghi vấn tái lập, phải báo.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `wvote_sum` > `maj8` >= 4/5 fold | **H28 XÁC NHẬN.** Bộ chấm CÓ giá trị nhưng phải dùng kèm đồng thuận, không dùng argmax. Đây là cách dùng đúng của nhãn tự động. |
| `wvote_sum` ≈ `maj8` (trong sàn nhiễu) | Bộ chấm không thêm gì DÙ dùng đúng cách. Kết luận mạnh: ở 1.5B, đếm phiếu đã VẮT KIỆT tín hiệu; AUC cao KHÔNG chuyển thành độ chính xác. Phải nói thẳng. |
| `wvote_sum` < `maj8` | Trọng số làm HỎNG đếm phiếu. Bác. Khuyến nghị: chỉ dùng đếm phiếu trần. |
| `wvote_mean` >> `wvote_sum` | Ảnh hưởng đến từ cỡ nhóm chứ không phải điểm -> tức là vẫn chỉ là đếm phiếu trá hình. Phải nói rõ. |
| Lấy được >= 50% khoảng trống maj->oracle | Kết quả mạnh nhất dự án. Phải kiểm rò rỉ train/test trước khi báo. |

## Prior TRUNG THỰC (ghi trước)
Prior trước của tôi (H27 sẽ thắng) đã SAI. Lần này tôi hạ kỳ vọng: tôi đoán `wvote_sum` hơn
`maj8` khoảng 1–3 điểm, tức là VẪN nằm quanh sàn nhiễu và có thể rơi hàng 2.
Lý do vẫn chạy: đây là phép sửa TỐI THIỂU và ĐÚNG LÝ cho nghịch lý vừa đo, chi phí thấp
(dùng lại LoRA đã lưu ở `disc_lora`), và nó tách bạch "bộ chấm vô dụng" khỏi "cách dùng sai".

---

# Đăng ký trước #30 — H25d: SỬA CÁCH TIÊM LỖI CHO MATH
**Viết TRƯỚC khi chạy.** dt3 vô hiệu vì chỉ .0875 bài MATH tiêm được.

## Sửa gì
Bỏ yêu cầu tìm biểu thức `a op b = c`. Thay bằng: chọn NGẪU NHIÊN một token số trong THÂN
lời giải vàng (loại trừ đáp án `\boxed` cuối) và đổi giá trị -> tạo MÂU THUẪN NỘI TẠI giữa
thân bài và kết luận. Phát hiện nó cần ĐỐI CHIẾU, không cần giải lại từ đầu.
Kỳ vọng `pct_problems_corruptible` ~ 1.0.

## HẠN CHẾ TỰ NHẬN (ghi trước)
Đổi một số ngẫu nhiên có thể trúng số KHÔNG ẢNH HƯỞNG kết quả -> lỗi "vô hại", khó phát hiện
một cách chính đáng. Điều này làm nhiệm vụ KHÓ HƠN, nên kết quả DƯƠNG là kết luận BẢO THỦ
(an toàn); kết quả ÂM thì KHÔNG được đọc mạnh, vì có thể do lỗi vô hại.
Bắt buộc báo `pct_corrupt_changes_final_answer` để ước lượng phần lỗi thực sự có hại.

## Cam kết diễn giải (khoá TRƯỚC khi có số) — giữ mọi ngưỡng của #28
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| ZERO n>=40, phân biệt >= .40 ở 7B | **XÁC NHẬN kiểm lỗi tách rời khỏi giải** trên MIỀN THỨ HAI (MATH). Cùng với dt2_g7 thành hai miền -> phát biểu được. |
| ZERO n>=40, phân biệt ≈ 0 ở 7B | **BÁC.** dt2_g7 chỉ là ảo ảnh n=9. Tôi PHẢI rút lại cách đọc lạc quan ở vòng #48 và nói rõ đã mừng sớm. |
| ZERO vẫn n<40 | Ghi "thiếu lực", KHÔNG kết luận. |
| Suy biến >.90 | Tầng đó VÔ HIỆU. |
| pct_corruptible < .50 lần nữa | Bỏ hẳn hướng tiêm-lỗi trên MATH; ghi là KHÔNG ĐO ĐƯỢC bằng phương pháp này. |

---

# Đăng ký trước #31 — H28b: TÁI LẬP BỎ PHIẾU CÓ TRỌNG SỐ Ở Ô KHÁC
**Viết TRƯỚC khi chạy.** H28 xác nhận ở GSM8K 1.5B (+3.0, 4/5 fold). Một ô KHÔNG đủ để phát biểu.

## Vì sao phải tái lập trước khi công bố
`wvote_sum` là cơ chế ĐẦU TIÊN của dự án vượt được `maj@8`. Chính vì thế nó là kết quả DỄ BỊ
tự huyễn hoặc nhất. Độ lớn +3.0 dưới sàn nhiễu không ghép cặp; chỉ có tính chất CẶP và dấu
nhất quán (4 dương/1 hoà/0 âm) đang chống đỡ. Dự án này đã có 11 giả thuyết bị bác — phần lớn
là những kết quả "đẹp" ở MỘT ô rồi tan khi mở rộng lưới.

## Thiết kế — y hệt H28, đổi ô
- `wv_m15`: **MATH 1.5B** (solver ~.405 — dải khó hơn hẳn)
- `wv_g7` : **GSM8K 7B** (solver ~.916 — gần bão hoà, maj@8 chỉ +.01)
Mỗi ô: huấn luyện lại bộ chấm trên chính ô đó (nhãn tự động), rồi so
`maj8` / `rerank8` / `wvote_sum` / `wvote_mean` / `oracle8` trên CÙNG bộ 8 mẫu, 5 fold.

## NGƯỠNG HIỆU LỰC (giữ nguyên)
AUC > .55 mới đọc được kết quả tổng hợp. Báo AUC từng ô.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `wvote_sum` > `maj8` ở CẢ HAI ô mới, >=4/5 fold mỗi ô | **H28 TÁI LẬP.** Được phát biểu như KHUYẾN NGHỊ THỰC TIỄN: dùng bộ chấm để CÂN TRỌNG SỐ phiếu, không dùng để chọn một mẫu. Đây thành kết quả chính của dự án. |
| Chỉ 1/2 ô tái lập | "Phụ thuộc ô". KHÔNG được phát biểu tổng quát. Phải nói rõ ô nào có, ô nào không, và ngờ rằng hiệu ứng phụ thuộc dải độ khó. |
| Không ô nào tái lập | **H28 chỉ là ngẫu nhiên của một ô.** Phải RÚT LẠI cách đọc lạc quan ở vòng #50 và ghi rõ đã mừng sớm. |
| Ở ô bão hoà (GSM8K 7B) không có hiệu ứng nhưng ô khó (MATH 1.5B) có | Khớp với luật dải độ khó đã đo. Phát biểu kèm điều kiện: chỉ có ích khi maj@8 còn khoảng trống. |
| `wvote_mean` lại kém `wvote_sum` ở cả hai ô | Củng cố cơ chế: đồng thuận mang phần lớn tín hiệu. Ghi nhận như bằng chứng lặp lại. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán MATH 1.5B TÁI LẬP (còn nhiều khoảng trống: maj@8 .533 vs oracle .708) và
GSM8K 7B KHÔNG (đã bão hoà, maj@8 chỉ hơn greedy +.01, gần như không còn gì để cân).
Nếu đúng vậy thì rơi hàng 4, và phát biểu phải KÈM ĐIỀU KIỆN về dải độ khó — KHÔNG được
nói gọn thành "bỏ phiếu có trọng số luôn tốt hơn".

---

# Đăng ký trước #32 — H29: ĐƯỜNG CONG NĂNG LỰC CỦA VIỆC KIỂM LỖI (1.5B → 32B)
**Viết TRƯỚC khi chạy.** Chạy trên RTX 6000 Pro (102 GB) — T4 KHÔNG chạy nổi 32B bf16 (59 GB).

## Vì sao đây là thí nghiệm đáng chạy nhất trên GPU lớn
Phát biểu trung tâm, lặp lại nhiều lần nhất của dự án là "bộ máy chỉ hoạt động khi MODEL ĐI KIỂM
đủ mạnh". Hiện nó dựa trên ĐÚNG HAI ĐIỂM: 1.5B (suy biến .99, VÔ HIỆU) và 7B (phân biệt +.651).
Hai điểm thì vẽ được đường qua bất cứ đâu. Thêm 14B và 32B biến nó thành ĐƯỜNG CONG THẬT.
Đồng thời điểm 7B cũ đo ở **4-bit** — bản thân lượng tử hoá là một biến gây nhiễu CHƯA loại trừ
cho hiện tượng suy biến. Lần này chạy **bf16 toàn bộ**, cùng dữ liệu, cùng prompt.

## Thiết kế
Nhiệm vụ: PHÁT HIỆN LỖI SỐ HỌC TIÊM SẴN (như dt2/dt4), trên **MATH-500** (GSM8K bão hoà ở >=7B
nên tầng ZERO rỗng — đã ghi nhận ở vòng #47/#48).
Model: **7B bf16** (mốc sạch, loại bỏ 4-bit) · **14B bf16** · **32B bf16** — cùng kernel, tuần tự.
Phân tầng theo năng lực giải của CHÍNH model đó (k=8). Chỉ số: phân biệt = phát hiện − báo động giả.

## NGƯỠNG HIỆU LỰC (giữ nguyên luật đã lập ở #26/#28/#30)
`degenerate_rate` > .90 -> tầng VÔ HIỆU · `parse_fail_rate` > .20 -> cả model VÔ HIỆU
· `pct_problems_corruptible` < .50 -> cả lần chạy VÔ HIỆU
· `n_pairs` < 40 ở tầng ZERO -> tầng đó chỉ báo cáo, KHÔNG kết luận
· **BẮT BUỘC** báo GPU thật (`sm_120` hay không) để chắc chắn không tụt về P100.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Phân biệt TĂNG đơn điệu 7B → 14B → 32B | **XÁC NHẬN đường cong năng lực.** Phát biểu trung tâm của dự án có cơ sở định lượng, không còn là suy diễn từ 2 điểm. |
| Phân biệt BÃO HOÀ từ 14B (14B ≈ 32B) | Có NGƯỠNG, không phải thang liên tục. Khuyến nghị thực tiễn đổi hẳn: "đủ 14B là đủ", không cần model lớn hơn. |
| 7B bf16 KHÁC RÕ 7B 4-bit (đã đo +.651) | **Lượng tử hoá là biến gây nhiễu.** Mọi kết luận 4-bit trước đây của dự án phải gắn cảnh báo, kể cả dt2_g7. |
| Phân biệt KHÔNG tăng theo cỡ (phẳng hoặc lộn xộn) | **BÁC đường cong năng lực.** Kích thước model KHÔNG phải biến giải thích; phải tìm biến khác (dữ liệu huấn luyện, RLHF, họ model). Đây sẽ là đòn mạnh vào phát biểu trung tâm — phải nói thẳng. |
| Tầng ZERO đủ n>=40 và phân biệt >= .40 ở 14B/32B | Kiểm lỗi TÁCH RỜI khỏi giải, xác nhận ở năng lực cao + miền thứ hai. Cộng dt2_g7 thành bằng chứng hai miền. |
| Model lớn cũng suy biến (>.90) | Suy biến KHÔNG phải vấn đề năng lực mà là vấn đề ĐỊNH DẠNG CÂU HỎI. Phải thiết kế lại cách hỏi, không đổ cho model nhỏ. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán phân biệt TĂNG từ 7B lên 14B rồi BÃO HOÀ ở 32B (hàng 2). Tôi cũng đoán 7B bf16 ≈ 7B 4-bit
(tức lượng tử hoá KHÔNG phải thủ phạm) — nhưng đây là điều tôi ÍT CHẮC NHẤT và chính là lý do
phải có mốc 7B bf16 trong cùng lần chạy.
Ghi rõ: prior gần nhất của tôi (H27 rerank sẽ thắng) đã SAI, nên không nên tin prior này quá.

---

# Đăng ký trước #33 — H30: KHOẢNG TRỐNG maj→oracle CÓ THẬT KHÔNG, HAY CHỈ LÀ HIỆN VẬT CỦA k=8?
**Viết TRƯỚC khi chạy.** Chuẩn bị sẵn cho khe GPU tiếp theo trên RTX 6000 Pro.

## Sự việc đã đo và ĐIỀU CHƯA AI KIỂM
`oracle@8 − maj@8` = **+14.0 điểm** (GSM8K 1.5B) và **+10.5** (MATH 1.5B).
Đây là khoảng trống LỚN NHẤT và DUY NHẤT đã đo được của dự án, và toàn bộ hướng "tổng hợp"
(H27 rerank, H28 bỏ phiếu có trọng số) đang nhắm vào nó.
NHƯNG `oracle@k` là một mốc **LẠC QUAN CÓ HỆ THỐNG**: nó tính là ĐÚNG khi CHỈ CẦN 1 trong k mẫu
đúng — kể cả khi mẫu đó đúng do MAY MẮN (đoán trúng số) chứ không do lập luận đúng.
Khi k tăng, `oracle@k` tăng đơn điệu theo định nghĩa, còn `maj@k` thì bão hoà.
=> **Khoảng trống có thể PHÌNH RA thuần tuý vì k, mà không hề có thêm tín hiệu nào để khai thác.**
Nếu vậy thì "còn 14 điểm chưa lấy được" là một phát biểu SAI LỆCH mà chính tôi đã viết vào
RESULTS.md và README. Phải kiểm.

## Thiết kế — k = 2, 4, 8, 16, 32, 64 trên CÙNG bộ mẫu
Sinh 64 mẫu/bài (temp .8), rồi tính TẤT CẢ chỉ số trên TIỀN TỐ k đầu tiên (k=2..64) -> so sánh
hoàn toàn ghép cặp, không cần sinh lại. (T4 không làm nổi 64 chuỗi đồng thời; RTX 6000 Pro thì được.)
Mỗi k báo: `greedy1` · `maj@k` · `oracle@k` · `wvote_sum@k` · **`oracle_solid@k`**
**`oracle_solid@k`** = chỉ tính đúng nếu **>=2 trong k mẫu** cùng cho đáp án đúng
  -> loại phần lớn các cú "đúng do may mắn một lần". Đây là mốc trần TRUNG THỰC HƠN.

## Chỉ số chính
`oracle@k − maj@k` theo k, và `oracle_solid@k − maj@k` theo k.
Phụ: `wvote_sum@k − maj@k` có tăng theo k không (bộ chấm có tận dụng được nhiều mẫu hơn không).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `oracle_solid@8 − maj@8` gần bằng `oracle@8 − maj@8` | Khoảng trống LÀ THẬT, không phải may mắn. Phát biểu "+14 điểm chưa lấy được" ĐỨNG VỮNG. |
| `oracle_solid@8 − maj@8` NHỎ HƠN NHIỀU (vd < một nửa) | **Khoảng trống bị THỔI PHỒNG bởi các mẫu đúng-do-may.** Tôi PHẢI sửa lại RESULTS.md và README, và hạ mục tiêu của hướng tổng hợp xuống con số thật. |
| `oracle@k − maj@k` phình đều theo k trong khi `oracle_solid` phẳng | Khẳng định mạnh: `oracle@k` là mốc RÁC ở k lớn. Dự án phải bỏ hẳn `oracle@k`, dùng `oracle_solid@k`. |
| `wvote_sum@k − maj@k` TĂNG theo k | Bỏ phiếu có trọng số càng nhiều mẫu càng lợi -> khuyến nghị thực tiễn: tăng k. |
| `wvote_sum@k − maj@k` phẳng hoặc giảm theo k | Lợi thế của bỏ phiếu có trọng số KHÔNG mở rộng được; chỉ hữu ích ở k nhỏ. Phải nói rõ. |
| `maj@k` bão hoà sớm (k>=16 không tăng) | Ghi nhận: k=8 đã gần hết giá trị của đếm phiếu; tăng k không phải hướng đi. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán `oracle_solid` sẽ THẤP HƠN RÕ so với `oracle`, tức khoảng trống thật NHỎ HƠN con số
+14.0 tôi đã công bố. Nếu đúng thì đây là lần tự sửa thứ ba của dự án, và lần này là sửa một
con số tôi đã ĐƯA VÀO README như điểm nhấn. Tôi ghi trước để không thể lờ đi.

---

# Đăng ký trước #34 — H29b: CHẠY LẠI ĐƯỜNG CONG NĂNG LỰC, SỬA CẮT CỤT + THIẾU LỰC + LÃNG PHÍ GPU
**Viết TRƯỚC khi chạy.** H29 vô hiệu vì `parse_fail` .22–.23 > ngưỡng .20 đã khoá.
**CHƯA PHÓNG** — đang chờ người dùng cho phép dùng lại RTX 6000 Pro.

## Ba khiếm khuyết phải sửa (đã chẩn đoán, không phải phỏng đoán)
1. **CẮT CỤT** — 75/300 trace hết token giữa LaTeX trước khi tới dòng `VERDICT:`.
   Sửa: `max_new_tokens` 512 -> **1024**, VÀ ép ngắn phần lập luận
   ("Work through it in at most 120 words, then the final line must be exactly VERDICT: YES/NO"),
   VÀ thêm **lượt hỏi lại**: nếu lượt 1 không có `VERDICT:`, hỏi lượt 2 CHỈ để lấy phán quyết
   (đưa lại phần lập luận đã sinh). Báo `pct_needed_retry`.
2. **THIẾU LỰC ở tầng ZERO** — n=32/39/34 < 40. Sửa: N 200 -> **400** (dùng cả MATH-500).
3. **LÃNG PHÍ GPU** — BS=12 là di sản T4. Sửa: BS theo cỡ model
   (7B: 96 · 14B: 64 · 32B: 32) và **tách batch pha phát hiện khỏi pha lấy mẫu** (pha phát hiện k=1
   nên phải dùng batch LỚN). Kernel BẮT BUỘC in `torch.cuda.max_memory_allocated()` sau mỗi pha.

## Ngưỡng hiệu lực — GIỮ NGUYÊN, không nới
`parse_fail` <= .20 (SAU khi đã hỏi lại) · `degenerate_rate` <= .90 · `pct_corruptible` >= .50
· tầng ZERO cần n >= 40 mới được dùng để kết luận · `assert sm_120`.
**KHÔNG được nới ngưỡng để cứu kết quả.** Nếu vẫn > .20 thì nhiệm vụ này KHÔNG đo được trên MATH
bằng cách hỏi hiện tại, và phải đổi thiết kế chứ không đổi ngưỡng.

## Cam kết diễn giải (khoá TRƯỚC khi có số) — giữ nguyên bảng của #32
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| Phân biệt tăng đơn điệu 7B→14B→32B, tất cả HỢP LỆ | XÁC NHẬN đường cong năng lực. |
| Bão hoà từ 14B | Có NGƯỠNG, không phải thang liên tục -> "đủ 14B là đủ". |
| Không tăng theo cỡ | BÁC đường cong năng lực; cỡ model không phải biến giải thích. |
| Tầng ZERO n>=40 và phân biệt >= .40 | Kiểm lỗi TÁCH RỜI khỏi giải ở năng lực cao. |
| Tầng ZERO n>=40 nhưng phân biệt ≈ 0 trong khi HIGH cao | Kiểm lỗi BỊ CHẶN bởi năng lực giải. Phải rút lại cách đọc lạc quan ở vòng #48. |
| `parse_fail` vẫn > .20 | VÔ HIỆU lần hai -> BỎ thiết kế hỏi-phán-quyết trên MATH, chuyển sang cách đo khác. |

## GHI CHÚ TRUNG THỰC (bắt buộc đọc kèm)
Lần chạy trước cho HIGH = **+.337 / +.472 / +.529** — đơn điệu tăng, đúng hàng 1, đúng prior của tôi.
Tôi đã TUYÊN VÔ HIỆU nó. Nếu lần này ra kết quả TƯƠNG TỰ, đó **KHÔNG phải** sự xác nhận của lần trước
— lần trước không tồn tại về mặt bằng chứng. Ghi ở đây để không ai (kể cả tôi) kể lại thành
"đã thấy trước rồi, giờ chỉ xác nhận".

## SỬA ĐỔI cho Đăng ký trước #33 (H30) — ghi TRƯỚC khi có số, sau khi đã phóng
`ks_g15` (GSM8K 1.5B) và `ks_m15` (MATH 1.5B) đã phóng trên **T4**, KHÔNG phải RTX 6000 Pro
(người dùng yêu cầu tạm dừng dùng RTX). Vì T4 không sinh nổi 64 chuỗi đồng thời:
**k tối đa 64 -> 16**, dãy quét `KS = [2,4,8,16]` thay vì `[2,4,8,16,32,64]`.

**Câu hỏi CHÍNH của #33 KHÔNG đổi và vẫn trả lời được đầy đủ**: ba hàng đầu của bảng đã khoá
đều so sánh tại **k=8** (`oracle_solid@8 − maj@8` với `oracle@8 − maj@8`). k=8 vẫn nằm trong dãy.
Thứ MẤT ĐI là hai hàng nói về xu hướng theo k lớn:
  - "`oracle@k − maj@k` phình đều theo k trong khi `oracle_solid` phẳng"
  - "`maj@k` bão hoà sớm (k>=16 không tăng)"
Hai hàng đó chỉ đọc được trên dãy tới k=16 -> **kết luận về chúng phải ghi là YẾU/CHƯA ĐỦ**,
và phải chạy lại tới k=64 khi được phép dùng RTX 6000 Pro.

Ghi rõ: đây là THU HẸP PHẠM VI do ràng buộc phần cứng, **không phải nới ngưỡng, không phải đổi
tiêu chí phán quyết**. Bảng diễn giải của #33 giữ NGUYÊN VẸN cho mọi hàng tại k=8.

---

# Đăng ký trước #35 — H31: ĐO `oracle_solid` VÀ `wvote_sum` TRONG **CÙNG MỘT** KERNEL
**Viết TRƯỚC khi chạy.** Rút thẳng từ H30.

## Vì sao cần
H30 cho thấy khoảng trống thật (`oracle_solid − maj`) nhỏ hơn nhiều con số đã công bố.
Nhưng H30 và H28 chạy ở HAI kernel KHÁC NHAU, khác nửa dữ liệu và khác nhiệt độ:
`ks_m15` có maj@8 = .465 còn `wv_m15` có maj@8 = .265. **Không được ghép số giữa hai lần chạy.**
Muốn biết bỏ phiếu có trọng số lấy được BAO NHIÊU PHẦN của khoảng trống THẬT thì phải đo
CẢ HAI trên CÙNG bộ mẫu, CÙNG kernel.

## Thiết kế
Kernel `wvote` hiện có, THÊM `oracle_solid@8` (>=2/8 mẫu đúng) vào cùng vòng lặp fold.
Báo thêm: `wsum_pct_gap_solid` = (`wvote_sum` − `maj8`) / (`oracle_solid` − `maj8`).
Ô: GSM8K 1.5B và MATH 1.5B (hai ô đã có `wvote_sum` dương).

## NGƯỠNG HIỆU LỰC (giữ nguyên)
AUC > .55 · nếu `oracle_solid − maj8` <= 0 ở một ô thì **KHÔNG được tính tỉ lệ phần trăm** cho ô đó
(chia cho số âm/không là vô nghĩa) — phải báo "khoảng trống thật không khác 0".

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `wvote_sum − maj8` > 0 VÀ `oracle_solid − maj8` > 0, tỉ lệ >= 50% | **Bỏ phiếu có trọng số lấy được PHẦN LỚN khoảng trống thật.** Đây là phát biểu mạnh nhất mà dự án được phép đưa ra về hướng tổng hợp. |
| `wvote_sum − maj8` > 0 nhưng `oracle_solid − maj8` ≈ 0 | Bỏ phiếu có trọng số **vượt cả trần "solid"** -> tức `oracle_solid` là trần QUÁ CHẶT (đã lọc mất cả những lần giải đúng thật). Phải nói rõ trần thật nằm giữa `oracle_solid` và `oracle`. |
| Tỉ lệ < 20% | Còn nhiều khoảng trống thật chưa lấy được -> hướng tổng hợp vẫn đáng đầu tư. |
| `wvote_sum − maj8` ≈ 0 ở lần chạy này | Không tái lập được H28 trong điều kiện mới -> phải hạ cấp H28 xuống "phụ thuộc lần chạy". |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán rơi vào hàng 1 hoặc hàng 2 — tức bỏ phiếu có trọng số đã lấy gần hết khoảng trống THẬT,
và phần còn lại để giành là RẤT NHỎ. Nếu vậy, kết luận thực tiễn của dự án là:
**"lấy 8 mẫu, đếm phiếu có trọng số, và DỪNG LẠI — phần còn lại không đáng theo đuổi ở quy mô này."**
Đó sẽ là một kết luận KHIÊM TỐN nhưng là kết luận VỮNG NHẤT mà dữ liệu cho phép.

## GHI CHÚ THỰC THI cho #30 (H25d) — `dt5_m7` / `dt5_m15`, viết TRƯỚC khi có số
Chạy lại thí nghiệm tiêm-lỗi trên MATH sau khi sửa **lỗi regex thoát dư tầng** (vòng #54)
đã khiến `dt4_m7` cho `pct_corruptible = 0.0` và bị tuyên VÔ HIỆU.
Kernel nay có **tự kiểm regex ngay đầu** (`assert` số khớp >= 4 trên chuỗi mẫu) -> chết trong
vài giây nếu regex hỏng, thay vì sau 1 giờ.
Hai ô: **7B 4-bit** (`dt5_m7`) và **1.5B fp16** (`dt5_m15`), N=400, CÙNG dữ liệu, CÙNG cách tiêm.
Bảng diễn giải của #30 và mọi ngưỡng hiệu lực (#26/#28) GIỮ NGUYÊN, không sửa một chữ.

Lý do thêm ô 1.5B: `dt2_g15` cho 1.5B suy biến .99 trên GSM8K (VÔ HIỆU). Chạy 1.5B trên MATH
cùng lần này để biết suy biến là do NĂNG LỰC hay do MIỀN — hai khả năng chưa tách được.
Nếu 1.5B lại suy biến >.90 trên MATH thì đó là NĂNG LỰC; nếu không thì trước đây là do miền.

---

# Đăng ký trước #36 — H28c: ĐO LẠI BỎ PHIẾU CÓ TRỌNG SỐ SAU KHI SỬA LỖI RÒ RỈ ADAPTER
**Viết TRƯỚC khi chạy.** Mọi kết quả bỏ phiếu có trọng số trước đây đều BỊ NHIỄM (vòng #59).

## Lỗi đã sửa
Mẫu ĐÁNH GIÁ được sinh khi LoRA Yes/No vẫn BẬT -> solver bị chính bộ chấm làm hỏng.
Bằng chứng: cùng ô, cùng dữ liệu, chỉ khác lượng huấn luyện (800 vs 1600 bước) ->
`greedy1` .5167 vs .3867, `maj@8` .7067 vs .5467, và `wsum−maj` +.030 vs +.110.
Sửa: `gen(..., adapter=False)` mặc định -> mọi lời giải sinh bằng **MODEL GỐC**;
adapter CHỈ bật khi CHẤM ĐIỂM.

## NGƯỠNG HIỆU LỰC MỚI (khoá trước) — bắt lại đúng lỗi này
`adapter_leak` = `pre_acc` − `post_acc` (độ chính xác mẫu TRƯỚC vs SAU huấn luyện).
Nếu **|leak| > .05** -> lần chạy **VÔ HIỆU**: adapter vẫn rò rỉ vào pha giải.
Giữ nguyên: AUC > .55.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `wsum − maj` > 0, >=4/5 fold, leak <= .05 | Bỏ phiếu có trọng số ĐỨNG VỮNG sau khi sửa lỗi. Độ lớn MỚI là con số được phép công bố; con số +11.0 cũ phải bị RÚT. |
| `wsum − maj` ≈ 0 sau khi sửa | **Hiệu ứng trước đây PHẦN LỚN là hiện vật của solver bị hỏng.** Phải RÚT LẠI H28/H28b/H31 và ghi rõ dự án KHÔNG có cơ chế nào vượt `maj@8`. |
| `wsum − maj` > 0 nhưng NHỎ HƠN NHIỀU con số cũ | Hiệu ứng THẬT nhưng đã bị lỗi thổi phồng. Công bố con số mới, ghi rõ mức thổi phồng. |
| leak > .05 dù đã sửa | VÔ HIỆU; còn đường rò rỉ khác chưa tìm ra. Phải tìm tiếp, KHÔNG được đọc số. |
| `maj@8` mới ≈ .70 (khớp wv_g15) chứ không phải .55 | Xác nhận chẩn đoán: baseline thấp trước đây đúng là do adapter rò rỉ. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán hiệu ứng VẪN DƯƠNG nhưng NHỎ HƠN NHIỀU +11.0 — có lẽ quanh +2 đến +4 điểm, tức gần
với `wv_g15` (+.030) hơn là `ws_g15` (+.110), vì `wv_g15` huấn luyện ít hơn nên rò rỉ ít hơn.
Nếu ra hàng 2 (≈0) thì dự án MẤT kết quả dương duy nhất của mình, và tôi phải nói thẳng điều đó.
