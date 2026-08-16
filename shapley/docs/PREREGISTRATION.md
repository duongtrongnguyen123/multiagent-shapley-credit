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

---

# Đăng ký trước #37 — H28d: NGƯỠNG RÒ RỈ ĐO ĐÚNG CÁCH
**Viết TRƯỚC khi chạy.** #36 vô hiệu vì ngưỡng của chính nó so hai TẬP BÀI KHÁC NHAU.

## Sửa ngưỡng
Đo rò rỉ trên **CÙNG MỘT tập bài**: giữ lại 60 bài kiểm tra làm "mẫu dò".
- `probe_pre`  : sinh 1 mẫu cho 60 bài đó **TRƯỚC** khi huấn luyện (model gốc)
- `probe_post` : sinh 1 mẫu cho **ĐÚNG 60 bài đó** **SAU** khi huấn luyện, adapter TẮT
- `adapter_leak` = `probe_pre − probe_post` (cùng bài, cùng nhiệt độ, cùng seed)
Chênh còn lại chỉ có thể là nhiễu lấy mẫu hoặc rò rỉ thật, KHÔNG còn lẫn khác biệt train/test.
Ngưỡng: **|leak| <= .05** -> hợp lệ. Báo kèm `probe_n=60` để biết sai số (~±.065 ở n=60, nên
ngưỡng .05 là CHẶT; nếu |leak| <= .05 thì gần như chắc chắn không rò rỉ).

## Cam kết diễn giải (khoá TRƯỚC khi có số) — giữ nguyên bảng #36, chỉ đổi cách đo leak
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| leak <= .05 VÀ `wsum − maj` > 0 ở >=4/5 fold | H28 ĐỨNG VỮNG sau sửa lỗi. Con số MỚI là con số duy nhất được công bố; +11.0 và +3.0 cũ bị RÚT. |
| leak <= .05 VÀ `wsum − maj` ≈ 0 | **RÚT LẠI H28/H28b/H31.** Dự án KHÔNG có cơ chế nào vượt `maj@8`. Phải nói thẳng. |
| leak > .05 lần nữa | Còn đường rò rỉ thứ ba chưa tìm ra. VÔ HIỆU; phải tìm bằng cách so từng bước, KHÔNG được đọc số. |

## Prior TRUNG THỰC (ghi trước)
Số thô của #36 (vô hiệu) là +.047 (GSM8K, 5/5) và +.035 (MATH, 2/5). Tôi đoán lần này ra
tương tự: **dương nhỏ ở GSM8K (~+3 đến +5 điểm), không khác 0 ở MATH.**
Nếu đúng thì phát biểu cuối của dự án là: bỏ phiếu có trọng số giúp VÀI ĐIỂM ở GSM8K 1.5B,
KHÔNG tổng quát sang MATH — khiêm tốn hơn nhiều so với "+11.0 điểm" tôi từng viết.

---

# Đăng ký trước #38 — H32: PIPELINE VAI TRÒ vs LẤY MẪU LẶP **Ở CÙNG NGÂN SÁCH**
**Viết TRƯỚC khi chạy.** Đây là phép thử mà toàn bộ dự án đã THIẾU.

## Lỗ hổng trong chính bằng chứng của tôi
Mọi so sánh "pipeline > solver đơn" của dự án đều cho pipeline **NHIỀU LƯỢT SINH HƠN**:
`P→S→V` dùng 3 lượt, `Solver` dùng 1 lượt. Nên "+5.6 điểm" có thể HOÀN TOÀN là do
"sinh 3 lần thì tốt hơn sinh 1 lần", KHÔNG phải do phân vai.
Bằng chứng gián tiếp đã có (Planner giải rồi giấu; Verifier tái sử dụng 0%; `S_anc` không có
chữ "kiểm" nào vẫn ngang verifier; giả dược `X_cross` sửa nhiều nhất) đều nói vai KHÔNG chuyên biệt.
Nhưng **chưa ai đo trực tiếp**: ở CÙNG số lượt sinh, pipeline có hơn bỏ phiếu không?

## Thiết kế — MỌI nhánh đúng 3 LƯỢT SINH, cùng bài, cùng model, 5 fold
- `greedy1` : 1 lượt (mốc dưới, để quy chiếu)
- **`maj3`** : 3 mẫu độc lập (temp .8) -> đếm phiếu
- **`PSV`**  : Planner -> Solver -> Verifier (đúng pipeline của dự án)
- **`SVV`**  : Solver -> Verifier -> Verifier (2 lượt kiểm, không có Planner)
- `SS_anc`  : Solver -> giải lại CÓ mỏ neo -> giải lại CÓ mỏ neo (không có chữ "kiểm" nào)
**BẮT BUỘC đếm SỐ TOKEN SINH RA của từng nhánh** — ngân sách công bằng phải tính theo TOKEN,
không chỉ theo số lượt. Báo `tokens_per_arm`.

## Chỉ số chính
`maj3 − PSV` theo từng fold. Phụ: `SVV − maj3`, `SS_anc − PSV`, và token của mỗi nhánh.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `maj3` >= `PSV` ở >=4/5 fold | **PIPELINE VAI TRÒ KHÔNG MANG LỢI ÍCH GÌ ngoài việc sinh nhiều lần.** Phải phát biểu thẳng trong README: lợi ích đã báo cáo của pipeline là lợi ích của LẤY MẪU LẶP. Kiến trúc phân vai KHÔNG đáng dùng ở quy mô này. |
| `PSV` > `maj3` ở >=4/5 fold | Pipeline CÓ thêm giá trị vượt trên lấy mẫu. Vai có ý nghĩa. Phải rút lại cách đọc "vai không chuyên biệt". |
| Bằng nhau trong sàn nhiễu | Lợi ích là của LẤY MẪU, vai chỉ là cách LẤY MẪU ĐA DẠNG tốn kém hơn. Khuyến nghị: dùng bỏ phiếu, rẻ và đơn giản hơn. |
| `PSV` ngang `maj3` NHƯNG tốn NHIỀU TOKEN HƠN | Pipeline **TỆ HƠN** ở cùng chất lượng. Phải nói rõ là tệ hơn, không phải "ngang". |
| `SS_anc` ≈ `PSV` | Xác nhận thêm: bỏ hết ngôn ngữ vai mà kết quả không đổi -> vai là NHÃN, không phải cơ chế. |
| `SVV` > `PSV` | Planner có hại; nên bỏ Planner, dồn ngân sách cho lượt kiểm. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán **hàng 1 hoặc hàng 3** — tức `maj3` ngang hoặc hơn `PSV`. Lý do: mọi bằng chứng cơ chế
đã đo đều nói vai không chuyên biệt, và đếm phiếu chưa từng bị đánh bại một cách hợp lệ.
Nếu ra hàng 1 thì đây là kết luận LỚN NHẤT và KHIÊM TỐN NHẤT của dự án: **kiến trúc đa tác tử
phân vai, ở quy mô này, chỉ là một cách đắt tiền để lấy mẫu nhiều lần.**
Tôi ghi trước rằng kết luận đó sẽ phủ định phần lớn công sức 60 vòng lặp của chính tôi.

## MỞ RỘNG #38 (H32) SANG ĐỦ LƯỚI 2×2 — ghi TRƯỚC khi có số
`bg_g15` (GSM8K 1.5B) đã xong và cho HÀNG 2 (PSV > maj@3, 5/5 fold, ít token hơn).
Nay chạy đủ ba ô còn lại: `bg_m15` (MATH 1.5B), `bg_m7` (MATH 7B), `bg_g7` (GSM8K 7B).
Bảng diễn giải của #38 GIỮ NGUYÊN, áp cho TỪNG ô. Thêm quy tắc tổng hợp lưới:

| Kết quả trên lưới | Kết luận BẮT BUỘC |
|---|---|
| `PSV > maj@3` ở **>=3/4 ô** | Tuần tự-có-mỏ-neo THẮNG song song ở cùng ngân sách — phát biểu được như KHUYẾN NGHỊ CHUNG. |
| Chỉ 1–2/4 ô | PHỤ THUỘC Ô. `bg_g15` là ngoại lệ chứ không phải quy luật; KHÔNG được tổng quát. |
| Không ô nào (ngoài g15) | Kết quả `bg_g15` là ngẫu nhiên của một ô. Phải rút lại vòng #63. |
| `SS_anc ≈ PSV` ở >=3/4 ô | Xác nhận: vai là NHÃN, cơ chế là MỎ NEO. Đây là phát biểu cơ chế của dự án. |
| Ô bão hoà (GSM8K 7B, solver .916) không có hiệu ứng | Khớp luật dải độ khó; KHÔNG tính là phản chứng, ghi kèm điều kiện. |

**Prior TRUNG THỰC (ghi trước):** prior lần trước của tôi SAI (đoán maj@3 thắng, thực tế thua 5/5).
Lần này tôi đoán: MATH 1.5B **CÓ** hiệu ứng (solver .405, còn nhiều chỗ để sửa),
MATH 7B **CÓ** (dải .60-.67 là nơi verify sinh lợi), GSM8K 7B **KHÔNG** (bão hoà .916).
Tức là 3/4 ô -> hàng 1. Nhưng tôi vừa sai một lần nên đặt ít trọng số vào prior này.

---

# Đăng ký trước #39 — H33: `P→3S` và `P→S→V→A` Ở NGÂN SÁCH 4 LƯỢT
**Viết TRƯỚC khi chạy.** Mở rộng H32 sang ngân sách 4 lượt, có ĐỐI CHỨNG CÙNG NGÂN SÁCH.

## Hai cấu hình cần kiểm (người dùng đề xuất)
- **`P3S`** : Planner 1 lượt -> **3 Solver CÙNG đọc kế hoạch đó** -> đếm phiếu giữa 3 lời giải. (4 lượt)
- **`PSVA`**: Planner -> Solver -> Verifier -> Aggregator (đủ 4 vai). (4 lượt)
**ĐỐI CHỨNG BẮT BUỘC: `maj@4`** (4 mẫu độc lập, đếm phiếu) — cùng 4 lượt sinh.
Kèm lại `maj@3` và `PSV` (3 lượt) để biết lượt thứ 4 có mua được gì không.
Đếm TOKEN mọi nhánh.

## Câu hỏi cơ chế mà thiết kế này tách được
`P3S` cho cả 3 mẫu ĐỌC CHUNG một kế hoạch -> **giảm ĐA DẠNG** giữa các mẫu.
Nếu đếm phiếu hoạt động nhờ đa dạng, `P3S` sẽ **KÉM `maj@4`** dù có thêm thông tin kế hoạch.
Đây là phép thử trực tiếp: **thông tin chung có bù được cho đa dạng bị mất không?**

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `P3S` > `maj@4` ở >=4/5 fold | Kế hoạch chung BÙ ĐƯỢC đa dạng đã mất. Điều kiện hoá tập trung có giá trị. |
| `P3S` < `maj@4` ở >=4/5 fold | **Đa dạng quan trọng hơn thông tin chung.** Không nên ép nhiều solver theo cùng một kế hoạch. |
| `PSVA` > `PSV` | Aggregator CÓ giá trị ở 1.5B — mâu thuẫn với đo cũ (agg_fair 1.5B −.067, agg_full_sol −.175); phải đối chiếu và giải thích. |
| `PSVA` <= `PSV` | Lượt thứ 4 dành cho Aggregator là LÃNG PHÍ. Khuyến nghị: dừng ở Verifier. |
| `maj@4` ≈ `maj@3` | Lượt sinh thứ 4 gần như vô ích cho đếm phiếu -> lợi ích cận biên của lấy mẫu bão hoà sớm. |
| Nhánh tuần tự tốt nhất (4 lượt) <= nhánh tuần tự tốt nhất (3 lượt) | Thêm lượt KHÔNG mua thêm gì; ngân sách 3 lượt là đủ. Phát biểu được như khuyến nghị thực tiễn. |

## Prior TRUNG THỰC (ghi trước)
- `P3S` **KÉM** `maj@4`: kế hoạch chung làm 3 mẫu giống nhau, đếm phiếu mất tác dụng.
- `PSVA` **≈ hoặc kém** `PSV`: Aggregator đã đo là trung tính (7B) tới có hại (1.5B).
- Tức là tôi đoán **cả hai cấu hình mới đều KHÔNG hơn** cấu hình 3 lượt tốt nhất.
Ghi rõ: prior gần nhất của tôi về H32 đã SAI (đoán maj@3 thắng, thực tế thua 5/5),
nên đặt ít trọng số vào prior này.

---

# Đăng ký trước #40 — H35: KIỂM BẰNG **BỘ KIỂM ĐÚNG ĐẮN** vs KIỂM BẰNG LLM, Ở CÙNG NGÂN SÁCH
**Viết TRƯỚC khi chạy.** Đây là phát biểu tổng quát mà "chứng minh định lý" chỉ là một trường hợp.

## Vì sao đây mới là thí nghiệm đáng chạy (thay vì Lean)
Phát hiện âm trung tâm của dự án: "verifier" bằng LLM **không kiểm** — nó GIẢI LẠI
(tái sử dụng 0% số của Solver; độ chính xác can thiệp = độ chính xác TỰ GIẢI).
Đối chứng gần nhất đã đo: **verify bằng CHẠY TEST** trên HumanEval —
.787 -> **.835** ở 7B, **0 phá** suốt 3 vòng; trong khi verify bằng LLM PHÁ đáp án đúng ở CẢ 4 ô.
=> Giả thuyết tổng quát: **vai verifier chỉ hoạt động khi việc kiểm là ĐÚNG ĐẮN VỀ MẶT CƠ HỌC,
   không phải khi nó là một lượt LLM nữa.** Chứng minh định lý hình thức là một hiện thân
   (bộ kiểm Lean), thực thi test là một hiện thân khác — và cái thứ hai CHẠY ĐƯỢC ở quy mô này.

## Khiếm khuyết của số cũ, phải sửa
`.787→.835` đo **MỘT LẦN**, +4.8 điểm — **DƯỚI sàn nhiễu 5 điểm**, và **KHÔNG có đối chứng
cùng ngân sách** (3 vòng sửa = 4 lượt sinh, so với 1 lượt của baseline). Đúng loại so sánh
mà chính tôi đã bị chỉ ra là sai ở H32.

## Thiết kế — HumanEval, 5 fold, MỌI nhánh 4 LƯỢT SINH
- `greedy1` (1 lượt, quy chiếu)
- **`maj@4`** — 4 mẫu, bỏ phiếu theo chuỗi code chuẩn hoá (đối chứng cùng ngân sách)
- **`exec3`** — sinh 1 lần rồi **3 vòng sửa dựa trên KẾT QUẢ CHẠY TEST** (bộ kiểm đúng đắn)
- **`llm3`**  — sinh 1 lần rồi **3 vòng sửa dựa trên NHẬN XÉT CỦA LLM** (không chạy test)
`exec3` vs `llm3` là phép so sánh CHÍNH: **cùng số lượt, cùng model, chỉ khác NGUỒN TÍN HIỆU KIỂM.**
Đếm token mọi nhánh. Báo `n_breaks` (bài đang đúng bị làm hỏng) cho từng nhánh.

## NGƯỠNG HIỆU LỰC (khoá trước)
`exec_success_rate` (tỉ lệ code chạy được, không lỗi cú pháp) phải **>= .50** — cùng ngưỡng đã
dùng để tuyên H8 VÔ HIỆU. Nếu thấp hơn thì model không viết nổi code chạy được -> VÔ HIỆU.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `exec3` > `llm3` VÀ `exec3` > `maj@4`, >=4/5 fold | **XÁC NHẬN: bộ kiểm ĐÚNG ĐẮN làm được thứ LLM-kiểm không làm nổi**, và nó thắng cả lấy mẫu ở cùng ngân sách. Đây là phát biểu THỰC TIỄN mạnh nhất dự án: chỉ thêm verifier khi có bộ kiểm thật. |
| `exec3` > `llm3` nhưng KHÔNG hơn `maj@4` | Bộ kiểm hơn LLM-kiểm, nhưng vẫn không đáng so với chỉ lấy mẫu thêm. Khuyến nghị: bỏ phiếu. |
| `exec3` ≈ `llm3` | Nguồn tín hiệu kiểm KHÔNG quan trọng -> bác giả thuyết trung tâm của vòng này. Phải nói thẳng. |
| `llm3` phá nhiều hơn `exec3` (n_breaks) | Củng cố cơ chế: LLM-kiểm gây hại, bộ kiểm thì không. Ngay cả khi độ chính xác ngang nhau. |
| `exec_success_rate` < .50 | VÔ HIỆU (như H8). Không được đọc là "bộ kiểm thất bại". |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán `exec3` > `llm3` rõ rệt và `exec3` >= `maj@4` — tức hàng 1. Đây là hướng tôi tin nhất
còn lại của dự án, vì nó là cơ chế DUY NHẤT đã đo được **0 phá** trong khi mọi LLM-verifier đều phá.
Ghi kèm: prior H32 của tôi đã sai, nên đặt trọng số vừa phải.

## VỀ CHỨNG MINH ĐỊNH LÝ (trả lời trực tiếp)
Không chạy Lean lúc này vì: (a) **không có bộ dữ liệu miniF2F trên Kaggle** (đã tìm, không có);
(b) không có toolchain Lean khi `enable_internet=false`; (c) Qwen2.5-1.5B/7B-Instruct gần như
không sinh nổi Lean hợp lệ -> mọi tầng sẽ rỗng, đúng lỗi đã giết `dt2_g7` (tầng quyết định n=9).
Nếu về sau có model chuyên (DeepSeek-Prover/Llemma) và bộ kiểm, H35 chính là khuôn mẫu để lặp lại.

---

# Đăng ký trước #41 — H36: TÁCH "TUẦN TỰ vs SONG SONG" KHỎI "GREEDY vs LẤY MẪU"
**Viết TRƯỚC khi chạy.** Người dùng chỉ ra một NHIỄU LOẠN trong H32 mà tôi đã bỏ sót.

## Nhiễu loạn đã bỏ sót
Trong H32, prompt HỆ THỐNG của Solver là **GIỐNG HỆT** ở cả hai nhánh (`SOLVE`), phần user chỉ
khác ở chỗ nhánh chuỗi được nối thêm kế hoạch. NHƯNG **NHIỆT ĐỘ KHÁC NHAU**:
- `maj@3`: 3 mẫu ở **temp 0.8** (bắt buộc, nếu temp 0 thì 3 mẫu giống hệt nhau, không bỏ phiếu được)
- `PSV`  : plan/solve/verify đều ở **temp 0.0 (greedy)**
`greedy1` (temp 0) = **.632** còn `maj@3` (3 mẫu temp .8) = **.644** -> mỗi mẫu ngẫu nhiên
YẾU HƠN HẲN một lần giải greedy. Nên `PSV` xuất phát từ một bước giải TỐT HƠN.
=> **+8.4 điểm của `PSV` so với `maj@3` có thể một phần là "greedy hơn lấy mẫu",
   KHÔNG phải "tuần tự hơn song song".**

## Thiết kế đối chứng
`maj3_g` = **1 mẫu greedy (temp 0) + 2 mẫu temp .8** -> bỏ phiếu, hoà thì lấy mẫu greedy.
Cùng 3 lượt sinh, nhưng nhánh song song NAY CŨNG được hưởng một lần giải tất định.
Chạy CÙNG kernel với `greedy1`, `maj@3` (thuần ngẫu nhiên), `PSV`, `SS_anc` -> so sánh CẶP.
Ô: GSM8K 1.5B và MATH 1.5B.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `maj3_g` ≈ `PSV` (chênh trong sàn nhiễu) | **Lợi thế của H32 là do GIẢI MÃ GREEDY, không phải cấu trúc tuần tự.** Phải RÚT LẠI cách đọc ở vòng #63 và sửa README. |
| `maj3_g` > `maj@3` nhưng vẫn KÉM `PSV` >=4/5 fold | Cả hai yếu tố cùng đóng góp. Phải báo phần do greedy (`maj3_g − maj@3`) TÁCH RIÊNG khỏi phần do tuần tự (`PSV − maj3_g`). |
| `maj3_g` ≈ `maj@3` | Greedy KHÔNG phải nguồn lợi thế; kết luận tuần tự-thắng-song song của H32 ĐỨNG VỮNG. |
| `maj3_g` > `PSV` | Đối chứng đúng còn THẮNG cả pipeline -> H32 bị bác hoàn toàn, phải rút lại. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán hàng 2: cả hai cùng đóng góp, phần do greedy chiếm khoảng **một phần ba đến một nửa**
của +8.4. Tức là kết luận "tuần tự thắng song song" sẽ SỐNG SÓT nhưng **NHỎ ĐI ĐÁNG KỂ**.
Ghi rõ: đây là nhiễu loạn do NGƯỜI DÙNG phát hiện, không phải tôi. Tôi đã công bố +8.4
ở vòng #63 mà chưa kiểm nó.

---

# Đăng ký trước #42 — H8b: CHẠY LẠI H8 (verify bằng THỰC THI trên TOÁN) VỚI 7B
**Viết TRƯỚC khi chạy.** H8 bị tuyên VÔ HIỆU ở 1.5B vì `exec_success_rate` = .42 < ngưỡng .50.

## Vì sao chạy lại bây giờ
7B viết code chạy được ở mức `exec_success_rate` = **1.000** trên HumanEval (đo ở R_c7b).
H8 chạy ở 1.5B và chết vì model không viết nổi code chạy được. Câu hỏi mở: **7B có vượt .50
trên MIỀN TOÁN không?** Nếu có, toán lần đầu có một BỘ KIỂM CHẠY ĐƯỢC.

## PHÂN BIỆT THEN CHỐT — ghi trước để không đọc nhầm kết quả
Trên CODE, bộ test là **ORACLE VỀ TÍNH ĐÚNG**: pass = đúng, không thể lừa.
Trên TOÁN, chạy Python chỉ cho biết **CHƯƠNG TRÌNH CHẠY ĐƯỢC**, KHÔNG cho biết chương trình
MÔ HÌNH HOÁ ĐÚNG bài toán. Một chương trình chạy trơn tru vẫn có thể tính sai thứ cần tính.
=> Vì vậy `exec3` trên toán chỉ sửa được **LỖI SẬP**, không sửa được **LỖI MÔ HÌNH HOÁ**.
=> DỰ ĐOÁN: lợi ích trên toán sẽ NHỎ HƠN NHIỀU so với +8.1 điểm đo được trên code.
   Đây là điều làm cho code và toán KHÁC LOẠI, không chỉ khác độ khó.

## Thiết kế (MATH-500, 7B bf16, 5 fold, đếm token)
- `greedy1` — suy luận bằng văn bản (1 lượt)
- `maj3` — 3 mẫu văn bản, bỏ phiếu (3 lượt)
- **`pal1`** — viết CHƯƠNG TRÌNH PYTHON, chạy, lấy kết quả in ra (1 lượt)
- **`pal3`** — `pal1` × 3, bỏ phiếu trên KẾT QUẢ ĐÃ CHẠY (3 lượt)
- **`exec3`** — viết Python; nếu SẬP thì sửa theo stderr, tối đa 3 vòng (<=4 lượt)
BẮT BUỘC báo: `exec_success_rate` (tỉ lệ code chạy không lỗi), `pct_no_output` (chạy nhưng
không in ra số), và `n_breaks` cho từng nhánh.

## NGƯỠNG HIỆU LỰC (giữ nguyên ngưỡng đã khoá của H8)
`exec_success_rate` < **.50** -> **VÔ HIỆU** như H8. Không được đọc là "thực thi thất bại trên toán";
chỉ được đọc là "7B vẫn chưa viết nổi code chạy được cho toán".

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `exec_success_rate` >= .50 VÀ `pal3` > `maj3` >=4/5 fold | **Toán CÓ THỂ có bộ kiểm chạy được ở 7B.** H8 trước đây thất bại vì NĂNG LỰC MODEL, không phải vì miền. Mở lại hướng thực thi cho toán. |
| `exec_success_rate` >= .50 nhưng `pal3` <= `maj3` | Code chạy được KHÔNG đủ — chạy được ≠ mô hình hoá đúng. Xác nhận phân biệt then chốt ở trên. Toán vẫn KHÔNG có bộ kiểm thật. |
| `exec3` > `pal1` nhưng vẫn <= `maj3` | Sửa lỗi SẬP có tác dụng, nhưng không bù được lỗi MÔ HÌNH HOÁ. Ghi rõ hai loại lỗi này khác nhau. |
| `exec_success_rate` < .50 | **VÔ HIỆU lần hai.** 7B cũng không viết nổi code cho toán -> ghi là giới hạn NĂNG LỰC ở quy mô này, và DỪNG hướng này. |
| `exec3` ≈ `oracle@k` (như trên code) | Bộ kiểm lại là BỘ CHỌN hoàn hảo -> nhưng phải kiểm xem "chạy được" có thật sự lọc đúng/sai không (nghi ngờ mạnh). |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán **`exec_success_rate` sẽ VƯỢT .50 ở 7B** (có lẽ .75–.95) nhưng **`pal3` KHÔNG hơn `maj3`**,
vì chạy được không đảm bảo mô hình hoá đúng. Tức là rơi HÀNG 2.
Nếu đúng thì kết luận là: **bộ kiểm chỉ có giá trị khi nó là ORACLE VỀ TÍNH ĐÚNG (như bộ test),
không phải khi nó chỉ là MỘT CÁCH TÍNH KHÁC (như chạy Python cho toán).**
Đó sẽ là phát biểu tổng quát và chặt chẽ hơn nhiều so với "code có bộ kiểm, toán thì không".

---

# Đăng ký trước #43 — H37: HUẤN LUYỆN BỘ KIỂM LỖI, VÀ NÓ CÓ CHUYỂN GIAO KHÔNG?
**Viết TRƯỚC khi chạy.** Trả lời: "có nên align/finetune/reinforce cho việc KIỂM không?"

## Vì sao đáng thử (bằng chứng đã có)
Cùng model 1.5B, cùng nhiệm vụ phán đoán đúng/sai:
- **PROMPT**: suy biến .99 (luôn nói "NO") -> VÔ HIỆU ở cả GSM8K lẫn MATH
- **HUẤN LUYỆN** (H27, nhãn tự động từ grader): **AUC .88–.95**
=> Năng lực phán đoán CÓ TỒN TẠI trong model, chỉ là **KHÔNG MOI RA ĐƯỢC BẰNG PROMPT**.
Nhãn cho việc kiểm lỗi tiêm sẵn là MIỄN PHÍ và VÔ HẠN (chuỗi vàng = sạch; đổi 1 số = bẩn).

## RỦI RO CHÍNH — phải thiết kế để đo, không được bỏ qua
Lỗi TIÊM SẴN = đổi MỘT con số trong chuỗi hoàn hảo.
Lỗi THẬT của model = sai cách tiếp cận, sai công thức, thiếu trường hợp.
**Hai loại khác hẳn nhau.** Một bộ kiểm huấn luyện trên lỗi tiêm có thể giỏi bắt "số bị đổi"
mà VÔ DỤNG với lỗi thật. Vì vậy thiết kế BẮT BUỘC là **huấn luyện trên TIÊM, đánh giá trên THẬT**.

## Thiết kế
- **Huấn luyện**: LoRA phân loại nhị phân trên MATH *train-half*, nhãn tiêm sẵn
  (clean vs corrupt, cân bằng). ~3000 cặp. Solver KHÔNG dính adapter (bài học rò rỉ #59).
- **Đánh giá A (trong phân phối)**: lỗi TIÊM trên test-half -> `discrimination_injected`
- **Đánh giá B (CHUYỂN GIAO — chỉ số CHÍNH)**: lời giải THẬT do model sinh, nhãn đúng/sai
  từ grader -> `discrimination_real`
- **Đánh giá C (giá trị thực tiễn)**: dùng bộ kiểm để CÂN TRỌNG SỐ phiếu trên k=8 -> so `maj@8`
- Mốc: bộ chấm H27 (huấn luyện trên lời giải THẬT) trên CÙNG tập test.

## NGƯỠNG HIỆU LỰC (khoá trước)
`adapter_leak` <= .05 (đo trên CÙNG 60 bài trước/sau, theo #37) · AUC > .55 mới đọc được ·
`degenerate_rate` <= .90.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `discrimination_real` >= .40 VÀ wvote > maj@8 >=4/5 fold | **HUẤN LUYỆN BỘ KIỂM LÀ ĐÚNG HƯỚNG.** Toán có thể có bộ kiểm học được, xấp xỉ vai trò mà bộ test đóng cho code. Kết quả lớn. |
| `discrimination_injected` cao NHƯNG `discrimination_real` ≈ 0 | **HỌC ĐƯỢC HIỆN VẬT, KHÔNG CHUYỂN GIAO.** Bộ kiểm chỉ bắt "số bị đổi". Phải nói thẳng và KHÔNG được báo cáo con số in-distribution như thành công. |
| Cả hai đều ≈ 0 | Huấn luyện không moi được năng lực kiểm cho lỗi số học. Cộng với H23 (GRPO im lặng) -> **DỪNG hướng huấn luyện vai kiểm**. |
| `discrimination_real` > 0 nhưng wvote KHÔNG hơn maj@8 | Kiểm được nhưng KHÔNG chuyển thành độ chính xác. Ghi rõ: đo được ≠ dùng được. |
| Thua bộ chấm H27 (huấn luyện trên lời giải thật) | Nhãn TIÊM kém hơn nhãn THẬT. Khuyến nghị: dùng grader trên lời giải thật, đừng tiêm. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán **hàng 2**: `discrimination_injected` sẽ CAO (>.6, vì nhiệm vụ dễ và nhãn sạch) nhưng
`discrimination_real` sẽ THẤP (<.2). Lý do: lỗi tiêm là bài toán "tìm số không khớp",
lỗi thật là bài toán "hiểu bài". Hai thứ này không cùng một kỹ năng.
Nếu đúng hàng 2 thì kết luận là: **nhãn rẻ không thay thế được nhãn đúng loại** — và cách duy
nhất còn lại cho toán vẫn là bộ kiểm CƠ HỌC, thứ mà toán KHÔNG CÓ (đã đo ở H8b).

---

# Đăng ký trước #44 — H38: ĐỊNH TUYẾN THEO ĐỒNG THUẬN vs TIÊU ĐỀU, Ở CÙNG CHI PHÍ TRUNG BÌNH
**Viết TRƯỚC khi chạy.** Rút thẳng từ số đã đo ở vòng #65.

## Sự việc đã đo
| đồng thuận (k=8) | GSM8K | MATH |
|---|---|---|
| 8/8 | **1.000** | **1.000** |
| 1/8 (không có đa số) | **.143** | **.000** |
Ở k=3, **50–58% số bài KHÔNG có đa số nào** -> `maj@3` thoái hoá thành "lấy mẫu đầu tiên".
Mọi pipeline của dự án hiện TIÊU CHI PHÍ ĐỀU NHAU cho mọi bài: lãng phí ở bài đã đồng thuận
(gần chắc đúng), thiếu ở bài phân tán (gần chắc sai).

## Thiết kế — so trên ĐƯỜNG CONG chi phí, không so một điểm
Đường cong TIÊU ĐỀU: `maj@3`, `maj@4`, `maj@6`, `maj@8` (mỗi bài dùng đúng k lượt).
Nhánh ĐỊNH TUYẾN (chi phí THAY ĐỔI theo bài):
- **`route_3_6`**: sinh 3; nếu **>=2 mẫu đồng ý** -> NHẬN, dừng. Nếu không -> sinh thêm 3, bỏ phiếu trên 6.
- **`route_3_seq`**: sinh 3; nếu đồng thuận -> nhận; nếu không -> chạy **tuần tự có mỏ neo** 3 lượt.
**BẮT BUỘC báo `mean_gens` và `mean_tokens` THỰC TẾ của từng nhánh** — định tuyến có chi phí
biến thiên nên chỉ so được khi biết chi phí thật.

## Chỉ số chính
Nhánh định tuyến có nằm **TRÊN** đường cong tiêu đều tại ĐÚNG chi phí của nó không?
Cụ thể: nội suy `maj@k` tại `k = mean_gens(route)` rồi so.

## NGƯỠNG HIỆU LỰC (khoá trước)
Nếu tỉ lệ bài "không đồng thuận" < .15 hoặc > .85 thì định tuyến gần như không phân biệt được
gì -> ghi rõ "định tuyến suy biến", không đọc là thành công/thất bại của ý tưởng.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `route` > `maj@k` nội suy tại cùng chi phí, >=4/5 fold | **XÁC NHẬN: định tuyến theo đồng thuận đáng dùng.** Khuyến nghị thực tiễn: đừng tiêu đều — đo đồng thuận trước, chỉ đổ thêm compute vào bài phân tán. Tín hiệu MIỄN PHÍ. |
| `route` ≈ đường cong tiêu đều | Đồng thuận KHÔNG giúp phân bổ compute tốt hơn. Ghi rõ đã bác; tiêu đều là đủ. |
| `route` < đường cong | Định tuyến GÂY HẠI — có thể vì bài "đồng thuận" cũng cần kiểm. Phải nói thẳng. |
| `route_3_seq` > `route_3_6` | Ở bài KHÓ, tuần tự tốt hơn lấy thêm mẫu — khớp H32 và làm sắc thêm nó. |
| `route_3_6` > `route_3_seq` | Ở bài khó, thêm mẫu tốt hơn tuần tự — MÂU THUẪN với H32, phải điều tra. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán **hàng 1 nhưng biên độ NHỎ** (1–3 điểm tại cùng chi phí). Lý do: tín hiệu đồng thuận
rất mạnh ở hai đầu (1.000 vs .143) nhưng nhóm "không đồng thuận" cũng chính là nhóm mà MỌI
cơ chế đều yếu — đổ thêm compute vào bài model không giải nổi có thể không cứu được.
Nếu ra hàng 2 thì kết luận thực tiễn của dự án gọn lại còn: **"lấy k mẫu, đếm phiếu, dừng"**.

---

# Đăng ký trước #45 — H39: DÙNG ĐỒNG THUẬN ĐỂ QUYẾT ĐỊNH **KHI NÀO TRẢ TIỀN CHO MODEL LỚN**
**Viết TRƯỚC khi chạy.** Kết hợp hai phát hiện đã đo của dự án.

## Hai mảnh ghép đã có
1. **Đồng thuận là tín hiệu đúng/sai gần như hoàn hảo và MIỄN PHÍ** (vòng #65):
   8/8 đồng ý -> acc 1.000; 1/8 -> .143/.000.
2. **Solver 1.5B + Verifier 7B** cho +14.0 điểm (H15) — nhưng ta CHƯA BAO GIỜ hỏi:
   *có cần gọi 7B cho MỌI bài không, hay chỉ cho bài mà 1.5B tự mâu thuẫn?*
=> Giả thuyết: **1.5B đủ cho phần lớn bài; chỉ escalate lên 7B khi 3 mẫu 1.5B KHÔNG đồng thuận.**

## Thiết kế — chi phí tính bằng FLOP, không phải "số lượt"
Quy đổi: 1 lượt 7B ≈ **4.67×** chi phí 1 lượt 1.5B (tỉ lệ tham số). Báo `cost_15B_equiv`.
- `small_maj3` / `small_maj8` : chỉ 1.5B (đường cong rẻ)
- `big_maj3` / `big_maj8`     : chỉ 7B (đường cong đắt)
- **`escalate`**: 3 mẫu 1.5B -> nếu >=2 đồng ý thì NHẬN; nếu không -> 3 mẫu **7B** + bỏ phiếu
- **`escalate_seq`**: như trên nhưng bài phân tán chạy **7B tuần tự có mỏ neo** (rẻ hơn 3 mẫu)
BẮT BUỘC báo `pct_escalated` và `cost_15B_equiv` của từng nhánh.

## NGƯỠNG HIỆU LỰC (khoá trước)
`pct_escalated` ngoài khoảng .15–.85 -> SUY BIẾN, không đọc (như rtL_g7 đã bị).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `escalate` >= `big_maj3` NHƯNG `cost_15B_equiv` THẤP HƠN rõ | **XÁC NHẬN: chỉ cần trả tiền cho model lớn ở bài KHÔNG đồng thuận.** Đây là khuyến nghị triển khai trực tiếp, tiết kiệm thật. |
| `escalate` < `big_maj3` ở cùng chi phí | Escalate không đủ — bài khó cần model lớn TỪ ĐẦU, không chỉ ở lượt sau. Ghi rõ. |
| `escalate` ≈ `small_maj8` | Model lớn không thêm gì ở nhóm phân tán -> nhóm đó KHÓ với cả hai model. Củng cố "nút thắt là SINH". |
| `escalate_seq` > `escalate` | Tuần tự lại thắng lấy mẫu, lần thứ hai ở bối cảnh khác. Củng cố H38. |
| `pct_escalated` ngoài .15–.85 | SUY BIẾN, không kết luận. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán **hàng 1**: escalate đạt gần `big_maj3` với chi phí thấp hơn nhiều, vì ~60% bài
1.5B đã đồng thuận và ở nhóm đó nó gần như luôn đúng (acc ~1.0 khi 8/8).
NHƯNG tôi cũng đoán biên độ so với `big_maj8` sẽ ÂM — model lớn dùng toàn phần vẫn tốt hơn,
chỉ là đắt hơn nhiều. Kết luận thực tiễn sẽ là về **hiệu quả chi phí**, không phải độ chính xác tuyệt đối.

# Đăng ký trước #46 — H40: **"TRẦN" CÓ THỰC SỰ QUYẾT ĐỊNH KHI NÀO ESCALATE THẮNG KHÔNG?**
**Viết TRƯỚC khi chạy.** Kiểm chứng lời giải thích hậu nghiệm sinh ra ở vòng #79.

## Vì sao phải chạy cái này
Vòng #78: escalate theo đồng thuận **thắng** trên MATH (+.140 so `big_maj3`).
Vòng #79: cùng giao thức, **thua** trên GSM8K (−.064, 0/5 fold).
Tôi đã đề xuất lời giải thích: *"escalate thắng khi model lớn còn XA TRẦN"* — dựa trên
**2 điểm dữ liệu**, và hai tác vụ còn khác nhau ở độ dài, kiểu suy luận, bộ chấm.
**Đó là GIẢ THUYẾT hậu nghiệm. Chưa được tính là kết quả.** Đây là bài kiểm nó.

## Thiết kế — tách độ khó TRONG CÙNG MỘT tác vụ
MATH-500 có trường `level` 1–5. Chạy nguyên 500 bài, cùng giao thức H39, tách theo:
- **DỄ** = level 1–2 (n=133) — nơi 7B gần trần
- GIỮA = level 3 (n=105)
- **KHÓ** = level 4–5 (n=262) — nơi 7B xa trần
Cùng model, cùng prompt, cùng bộ chấm, cùng ngày. Chỉ độ khó thay đổi.
Điều này loại trừ mọi khác biệt giữa-tác-vụ mà so sánh MATH-vs-GSM8K không loại được.

## PHÂN RÃ CƠ CHẾ (phần chính) — không chỉ đo hướng, mà đo VÌ SAO
Với mỗi tầng, tách tập bài thành NHẬN (đồng thuận, giữ cho 1.5B) và ESC (escalate):
- `acc_small_on_kept` — ta DÙNG cái này trên tập NHẬN
- `acc_big3_on_kept`  — 7B lẽ ra đạt được gì ở đó = **CÁI TA TỪ BỎ**
- `opp_cost` = `acc_big3_on_kept` − `acc_small_on_kept`  (giá phải trả để tiết kiệm)
- `gain_on_esc` = `acc_seq_on_esc` − `acc_big3_on_esc`   (cái ta THU được ở nhóm khó)
- **Đẳng thức phải nghiệm đúng:**
  `escalate_seq − big_maj3` ≈ `p_kept`·(−`opp_cost`) + `p_esc`·`gain_on_esc`
  Sai số > .01 ⇒ **CÓ BUG, không đọc kết quả.** Đây là tự kiểm tra mã, khoá trước.

## NGƯỠNG HIỆU LỰC (khoá trước)
- `pct_escalated` của một tầng ngoài .15–.85 ⇒ tầng đó SUY BIẾN, không đọc.
- n mỗi tầng ≥ 40 (đã thoả: 133/105/262).
- Đẳng thức phân rã lệch > .01 ⇒ huỷ toàn bộ, sửa mã, chạy lại.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `gain`(KHÓ) > 0 **và** `gain`(DỄ) ≤ 0, **và** `opp_cost`(DỄ) > `opp_cost`(KHÓ) | **XÁC NHẬN giả thuyết TRẦN.** Escalate là công cụ cho vùng model lớn CÒN SAI NHIỀU. Quy tắc triển khai có điều kiện đo được. |
| `gain` > 0 ở **CẢ HAI** tầng | Giả thuyết trần **SAI**. Chênh lệch MATH↔GSM8K do thứ khác (độ dài? kiểu suy luận? bộ chấm?). Ghi rõ là CHƯA GIẢI THÍCH ĐƯỢC. |
| `gain` ≤ 0 ở **CẢ HAI** tầng | **H39_m CHẾT** — thắng lợi +.140 trên MATH ở vòng #78 là giả tạo, không tái lập khi chạy đủ 500 bài. Phải rút lại vòng #78. |
| `gain`(DỄ) > 0 và `gain`(KHÓ) ≤ 0 | Ngược hoàn toàn dự đoán. Escalate hợp cho bài DỄ. Ghi rõ, không xoay lời. |
| hướng đúng nhưng `opp_cost` KHÔNG theo trần | Hướng đúng, **cơ chế sai**. Trần không phải nguyên nhân; phải tìm biến khác. |
| đẳng thức lệch > .01 | BUG. Không kết luận. |

## Prior TRUNG THỰC (ghi trước)
Tôi đoán hàng 1. **Nhưng prior của tôi vừa sai hai lần liên tiếp trong đúng chuỗi này**:
(a) tôi đoán `escalate_seq` sẽ THẤP HƠN `big_maj8` trên MATH — nó CAO HƠN 10.5 điểm;
(b) tôi tuyên bố kết quả #78 là "khuyến nghị mạnh nhất dự án" — GSM8K lật ngược ngay vòng sau.
Vì vậy prior này đáng được coi trọng **thấp**. Bảng trên mới là thứ quyết định.

# Đăng ký trước #47 — H41: KIỂM GIẢ THUYẾT "TRẦN" NGAY TRONG MIỀN MÀ ESCALATE ĐÃ **THUA**
**Viết TRƯỚC khi chạy.** Bài kiểm khắt khe hơn #46.

## Vì sao đây là bài kiểm mạnh hơn
#46 tách độ khó trên MATH — miền escalate đã THẮNG (+.140). Dễ ra kết quả thuận.
#47 làm đúng thế trên **GSM8K**, miền escalate đã **THUA** (−.064, 0/5 fold, vòng #79).
Nếu "trần" là nguyên nhân thật, thì NGAY TRONG GSM8K, nhóm bài nhiều bước (7B xa trần hơn)
phải cho `gain` cao hơn nhóm ít bước. Đây là dự đoán có thể sai rõ ràng.

## Độ khó cho GSM8K — GSM8K KHÔNG có trường `level`
Dùng **số bước tính** = số chú thích `<<...>>` trong lời giải chuẩn. Khách quan, có sẵn, không do tôi gán.
Phân bố đo được ở N=500: **DỄ (≤2 bước) 188 · GIỮA (3) 125 · KHÓ (≥4) 187** — đều ≥ 40.

## Thiết kế
Giao thức H39 y nguyên (3 mẫu 1.5B -> đồng thuận thì nhận, không thì 7B tuần tự có mỏ neo),
chạy trên 500 bài GSM8K, **bf16** trên RTX 5090, tách theo 3 tầng trên.
Phân rã cơ chế và **đẳng thức tự kiểm** giống hệt #46:
  `escalate_seq − big_maj3` ≈ `p_kept`·(−`opp_cost`) + `p_esc`·`gain_on_esc`  (lệch > .01 ⇒ BUG)

## NGƯỠNG HIỆU LỰC (khoá trước)
`pct_escalated` của tầng ngoài .15–.85 ⇒ tầng đó SUY BIẾN. n mỗi tầng ≥ 40. Lệch đẳng thức > .01 ⇒ huỷ.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `gain`(KHÓ) > `gain`(DỄ) ít nhất .03 **và** `opp_cost`(DỄ) > `opp_cost`(KHÓ) | **XÁC NHẬN MẠNH giả thuyết trần** — đúng cả trong miền escalate thua tổng thể. Trần là biến điều tiết, không phải khác biệt giữa hai tác vụ. |
| \|`gain`(KHÓ) − `gain`(DỄ)\| < .03 | Trần **KHÔNG giải thích được trong nội bộ GSM8K**. Khác biệt MATH↔GSM8K là ở cấp TÁC VỤ, không phải cấp độ khó. Giả thuyết trần YẾU ĐI rõ. |
| `gain`(KHÓ) < `gain`(DỄ) − .03 | **NGƯỢC HẲN. Giả thuyết trần CHẾT.** Ghi rõ, không diễn giải lại. |
| `gain`(KHÓ) > 0 | Có quy tắc dùng được: escalate CHỈ cho bài ≥4 bước, bỏ qua bài ngắn. |
| `opp_cost` không giảm theo độ khó | Hướng có thể đúng nhưng **cơ chế sai** — phải tìm biến khác. |

## Prior TRUNG THỰC (ghi trước)
Đoán hàng 1, nhưng biên độ nhỏ: `gain`(KHÓ) ≈ −.02, `gain`(DỄ) ≈ −.10.
Tức escalate vẫn THUA ở mọi tầng của GSM8K, chỉ bớt thua ở nhóm nhiều bước.
Prior của tôi đã sai 2 lần liên tiếp trong chuỗi này (vòng #78, #79) — bảng khoá mới là thứ quyết định.

# Đăng ký trước #48 — H42: ĐỊNH TUYẾN TRÊN **CODE** — TÍN HIỆU MIỄN PHÍ (ĐỒNG THUẬN) vs ORACLE THẬT (CHẠY TEST)
**Viết TRƯỚC khi chạy.** Đưa kết quả định tuyến (#46) sang miền code, và kiểm phân biệt trung tâm của dự án.

## Vì sao code là phép thử đúng
Vòng #71 khoá một phân biệt: **bộ kiểm chỉ có giá trị khi là ORACLE VỀ TÍNH ĐÚNG**
(test: pass = đúng, +6 đến +11 điểm), **không** có giá trị khi chỉ là một cách tính khác (PAL: −4.4 đến −7.5).
Code là miền DUY NHẤT có oracle thật. Vậy: **tín hiệu đồng thuận MIỄN PHÍ có sánh được với oracle không?**

## Dữ liệu — MBPP, tách rõ ràng KHÔNG rò rỉ
974 bài, mỗi bài **đúng 3 assert**. Dùng tách chuẩn `task_id` 11–510 = **500 bài**.
- `assert[0]`: **đưa vào prompt** (cần để biết tên hàm) và **dùng làm tín hiệu định tuyến**
- `assert[1]`, `assert[2]`: **CHỈ dùng để chấm điểm**, không nhánh nào được nhìn thấy
Đã kiểm: 498/500 tách được `lời_gọi == kỳ_vọng` bằng phân tích cú pháp AST.
LƯU Ý PHƯƠNG PHÁP: `exec3` cũ (H35) sửa code dựa trên CHÍNH bộ test dùng để chấm.
Hợp lệ theo cách nó được phát biểu (oracle công khai), nhưng **không so sánh được** với định tuyến
triển khai được. Ở đây mọi nhánh chỉ thấy `assert[0]`.

## Hai bộ định tuyến — khác nhau ĐÚNG một điều: có nhìn ĐÁP ÁN kỳ vọng hay không
- **`route_consensus`**: sinh 3 bản 1.5B, chạy cả 3 trên **LỜI GỌI** của `assert[0]`, so sánh
  đầu ra VỚI NHAU. Nhận nếu ≥2 bản cho **cùng một đầu ra KHÔNG PHẢI LỖI**. Không hề biết kỳ vọng.
  **KHOÁ TRƯỚC: ba bản cùng CRASH thì KHÔNG tính là đồng thuận** (phải escalate).
- **`route_oracle`**: sinh **1** bản 1.5B, chạy `assert[0]` ĐẦY ĐỦ (có kỳ vọng). Đạt thì nhận.
  Rẻ hơn: 1 lượt sinh thay vì 3.
Cả hai khi escalate đều gọi **7B tuần tự có mỏ neo** (giải lại + kiểm), giống H39/H40.

## Chi phí (quy về FLOP 1.5B, 1 lượt 7B = 5.07)
`route_consensus` = 3 + 2·5.07·pe_c · | `route_oracle` = 1 + 2·5.07·pe_o · | `big_maj3` = 15.20
Nhánh đối chứng: `small_maj3`, `big_maj3`, `big_maj8`.

## NGƯỠNG HIỆU LỰC (khoá trước)
- `pct_escalated` của MỖI bộ định tuyến ngoài .15–.85 ⇒ bộ đó SUY BIẾN, không đọc.
- Tỉ lệ code **biên dịch được** < .50 ⇒ huỷ toàn bộ (như ngưỡng H8).
- n mỗi fold ≥ 40 (5 fold × 100 = đạt).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `route_oracle` > `route_consensus` > `big_maj3` | Định tuyến CHUYỂN sang code, và **oracle thật hơn tín hiệu miễn phí**. Củng cố phân biệt #42: tín hiệu có thông tin ĐÚNG/SAI đáng giá hơn tín hiệu chỉ có ĐỒNG Ý/KHÔNG. |
| \|`route_consensus` − `route_oracle`\| < .03 | **Tín hiệu MIỄN PHÍ ngang oracle.** Không cần chạy test để định tuyến — kết quả có giá trị triển khai cao, và làm YẾU phân biệt oracle-vs-đồng thuận. |
| cả hai ≤ `big_maj3` | **Định tuyến KHÔNG chuyển sang code.** Thắng lợi ở MATH (#46) là đặc thù miền. Ghi rõ, không diễn giải lại. |
| `route_oracle` > `big_maj3` nhưng `route_consensus` ≤ `big_maj3` | Định tuyến trên code **cần tín hiệu ĐÚNG/SAI thật**; các bản mẫu đồng ý với nhau là KHÔNG đủ. |
| `pct_escalated` ngoài .15–.85 | SUY BIẾN, không kết luận về bộ đó. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1**, biên độ nhỏ giữa hai bộ định tuyến. Lý do: đầu ra trùng nhau trên MỘT input
là bằng chứng yếu hơn hẳn so với biết đáp án đúng — nhưng 3 chương trình sai mà trùng đầu ra
thì hiếm (đã loại trường hợp cùng crash).
**Prior của tôi đã sai 3 lần liên tiếp (#78, #79, #80).** Bảng khoá mới là thứ quyết định.

# Đăng ký trước #49 — H43: KIỂM NHÁNH HẬU NGHIỆM CỦA #81 TRÊN PHẦN MBPP **CHƯA HỀ ĐỤNG TỚI**
**Viết TRƯỚC khi chạy.** Vòng #81 quan sát hậu nghiệm; đây là phép thử độc lập của nó.

## Vì sao
#81 (H42) đo trên MBPP `task_id` 11–510: định tuyến oracle có `opp_cost` ÂM (phân loại gần hoàn hảo)
nhưng thua vì **hành động sau escalate** — lượt 7B TUẦN TỰ kém bỏ phiếu 7B×3 tới **11.6 điểm**.
Từ CHÍNH dữ liệu đó tôi tính ra: giữ tín hiệu oracle, escalate bằng `maj@3` -> **.6606 / chi phí 8.91**,
hơn `big_maj3` +.0080 và rẻ hơn 1.71×. **Biên độ chỉ +.008 = ~4 bài trên 498.** Rất có thể là nhiễu.

## Dữ liệu — KHÔNG dùng lại một bài nào
MBPP `task_id` **511–974** (~464 bài). Dự án CHƯA từng chạy phần này. Cùng giao thức, cùng model,
cùng bộ chấm: `assert[0]` để định tuyến, `assert[1..2]` CHỈ để chấm.

## Nhánh (khoá trước)
`small_1`, `small_maj3`, `big_greedy`, `big_maj3`, `big_maj8`,
`route_oracle_seq` (như #81), **`route_oracle_maj3`** (nhánh cần kiểm: escalate -> 7B maj@3).
Chi phí: `route_oracle_maj3` = 1 + 3·5.07·pe · | `route_oracle_seq` = 1 + 2·5.07·pe · | `big_maj3` = 15.20

## NGƯỠNG HIỆU LỰC (khoá trước)
`pct_escalated` ngoài .15–.85 ⇒ SUY BIẾN. Tỉ lệ biên dịch được < .50 ⇒ huỷ. n ≥ 400.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `route_oracle_maj3` > `big_maj3` **và** rẻ hơn | **XÁC NHẬN.** Quy tắc dùng được cho code: định tuyến bằng TÍN HIỆU THẬT (chạy 1 test), rồi escalate bằng **LẤY MẪU**, KHÔNG phải tuần tự. |
| \|chênh\| < .01 nhưng rẻ hơn rõ | Ngang độ chính xác, rẻ hơn. Kết luận YẾU: chỉ tiết kiệm chi phí, không cải thiện. |
| `route_oracle_maj3` < `big_maj3` | **Nhánh hậu nghiệm KHÔNG tái lập.** +.0080 ở #81 là nhiễu do nhìn dữ liệu rồi mới dựng nhánh. **Định tuyến trên code CHẾT hoàn toàn.** Ghi rõ. |
| `gain_on_esc`(seq) ≥ 0 ở tách này | Phát hiện "tuần tự hại trên code" (#81) KHÔNG tái lập -> phải **RÚT LẠI** cơ chế đã ghi ở vòng #81. |
| `pct_escalated` ngoài .15–.85 | SUY BIẾN, không kết luận. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 hoặc 3**, KHÔNG phải hàng 1: biên độ +.008 quá nhỏ so với nhiễu giữa các lần chạy
(đã thấy `maj@3` lệch 3.2 điểm giữa hai lần chạy ở H40). Prior của tôi đã sai **4 lần liên tiếp**
(#78,#79,#80,#81) nên trọng số của nó thấp; bảng khoá mới là thứ quyết định.

## BỔ SUNG cho đăng ký trước #47 (H41) — ghi ngày 2026-08-10, TRƯỚC khi chạy
**Thay đổi phần cứng và độ chính xác số học.** Bản gốc #47 ghi "bf16 trên RTX 5090".
Nguyên yêu cầu không dùng 5090 nữa, nên H41 chạy trên **Kaggle, 20 shard, 7B nf4 (4-bit)**.
- Bảng diễn giải đã khoá **GIỮ NGUYÊN, không sửa một chữ**. Nó chỉ nói về **DẤU** của `gain`
  giữa tầng DỄ và KHÓ; lượng tử hoá không được kỳ vọng làm đảo dấu.
- Rủi ro phải nêu trước: nf4 kéo `big_maj3` xuống, tức **kéo GSM8K RA XA vùng bão hoà** —
  đúng cái mà #47 muốn đo. Nếu `big_maj3` đo được **< .90**, thì tầng đó KHÔNG còn bão hoà nữa
  và **phép thử mất hiệu lực cho câu hỏi bão hoà** — phải ghi rõ, không được đọc như đã kiểm được.
- **Ngưỡng bổ sung khoá tại đây:** nếu `big_maj3` của tầng DỄ **< .90**, kết luận bắt buộc là
  *"chưa chạm vùng bão hoà, y như H40 — câu hỏi vẫn CHƯA được trả lời"*, chứ không phải
  ủng hộ hay bác bỏ giả thuyết trần.

# Đăng ký trước #50 — H44: TRÊN CODE, THỦ PHẠM LÀ **MỎ NEO** HAY LÀ **CẤU TRÚC TUẦN TỰ**?
**Viết TRƯỚC khi chạy.** Tách đôi cơ chế đã tái lập ở #81/#82.

## Điều đã ĐO ĐƯỢC (hai tách rời nhau, chênh 0.0005)
Trên nhóm escalate của code, **lấy mẫu hơn tuần tự +.1159 (H42) và +.1164 (H43)**.
Nhưng "tuần tự có mỏ neo" gộp HAI thứ: (a) **cho xem code sai trước đó**, (b) **thêm lượt tự kiểm**.
Chưa biết cái nào gây hại. Trên MATH cùng cấu trúc đó lại **+.18**.

## Thiết kế — ba HÀNH ĐỘNG trên CÙNG nhóm escalate, CÙNG một lần chạy
Nhóm escalate xác định bằng bộ định tuyến oracle (chạy `assert[0]`), như #82.
- **A) tuần tự CÓ mỏ neo**: giải-kèm-code-cũ → tự kiểm   (2 lượt 7B)  ← y hệt #81/#82
- **B) tuần tự KHÔNG mỏ neo**: giải MỚI hoàn toàn → tự kiểm (2 lượt 7B)  ← chỉ bỏ mỏ neo
- **C) lấy mẫu maj@3**                                  (3 lượt 7B)
A vs B **cô lập đúng MỎ NEO**: cùng cấu trúc, cùng chi phí, khác duy nhất ở chỗ có đưa code cũ vào hay không.
B vs C so tuần tự với lấy mẫu ở chi phí gần bằng nhau (2 vs 3 lượt).
Dữ liệu: MBPP `task_id` 11–510. Chấm CHỈ bằng `assert[1..2]`.

## NGƯỠNG HIỆU LỰC (khoá trước)
`pct_escalated` ngoài .15–.85 ⇒ SUY BIẾN. Biên dịch được < .50 ⇒ huỷ. n_escalate ≥ 100.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| B − A ≥ +.05 | **MỎ NEO là thủ phạm.** Đưa code sai vào khiến model VÁ thay vì viết lại. Cấu trúc tuần tự tự nó không sai. |
| \|B − A\| < .05 | **Mỏ neo KHÔNG phải nguyên nhân.** Bản thân LƯỢT TỰ KIỂM trên code mới là thứ gây hại (khớp H35: `llm3` vô dụng). |
| A − B ≥ +.05 | Mỏ neo **giúp**; thiếu hụt ở #81/#82 đến từ chỗ khác. **Phải RÚT LẠI** phát biểu cơ chế ở vòng #82. |
| C > B ≥ +.05 | Kể cả bỏ mỏ neo, lấy mẫu vẫn hơn tuần tự trên code -> kết luận là về **LẤY MẪU vs TUẦN TỰ**, không phải về mỏ neo. |
| `pct_escalated` ngoài .15–.85 | SUY BIẾN, không kết luận. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1** (mỏ neo là thủ phạm). Nhưng prior của tôi **sai 4 lần liên tiếp** (#78–#81)
và ở #82 bảng của tôi còn tự mâu thuẫn. Trọng số prior: rất thấp.

# Đăng ký trước #51 — H45: DẤU CỦA "TUẦN TỰ − LẤY MẪU" CÓ ĐI THEO **ĐỘ BÃO HOÀ CỦA CHÍNH MODEL ĐANG CHẠY** KHÔNG?
**Viết TRƯỚC khi chạy.** Thay thế giả thuyết "trần theo độ khó" đã chết ở vòng #83.

## Điều đã ĐO ĐƯỢC và điều CHƯA giải thích được
`gain_on_esc` (giá trị mỗi lần escalate, lượt 7B tuần tự có mỏ neo):
**MATH +.18 · GSM8K −.10 · CODE −.12**. MATH là ngoại lệ, chưa rõ vì sao.
Ở H41 mọi tầng GSM8K đều có `big_maj3` **> .90** (.9628/.9120/.9037) -> **không tầng nào chưa bão hoà**,
nên độ khó KHÔNG thể phân biệt được điều gì. Biến ứng viên còn lại: **độ chính xác của CHÍNH model
đang thực hiện lượt tuần tự** — không phải độ khó của bài.

## Thiết kế — đo `delta_seq` trên lưới tác vụ × cỡ model, CÙNG một bộ arm
Với mỗi ô (tác vụ ∈ {gsm8k, math} × model ∈ {1.5B, 7B}), trên CÙNG 300 bài, CÙNG một lần chạy:
- `greedy` (1 lượt) — **đây là thước đo độ bão hoà của ô**
- `maj3` (3 mẫu, T=0.8)
- `seq` (giải → giải lại có MỎ NEO → tự kiểm; 3 lượt) — **đúng arm dùng trong H39–H43**
- **`delta_seq` = `seq` − `maj3`** (cùng 3 lượt sinh, so sánh ngang ngân sách)
4 ô × 5 shard = 20 kernel. KHÔNG có escalate, KHÔNG có hai model — cô lập đúng một biến.

## NGƯỠNG HIỆU LỰC (khoá trước)
n mỗi ô ≥ 300. Tỉ lệ phân tích được đáp án ≥ .80. Ô nào `maj3` = 0 hoặc 1 tuyệt đối ⇒ bỏ.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `delta_seq` > 0 ở MỌI ô có `greedy` < .60 **và** < 0 ở MỌI ô có `greedy` > .85 | **XÁC NHẬN: dấu đi theo ĐỘ BÃO HOÀ CỦA MODEL.** Quy tắc dùng được: chỉ chạy tuần tự khi model còn xa trần TRÊN CHÍNH TÁC VỤ ĐÓ. |
| dấu KHÔNG theo `greedy` (ví dụ MATH 7B `greedy`≈.50 mà `delta_seq` < 0, hoặc GSM8K 1.5B `greedy`≈.50 mà < 0) | **Bão hoà cũng KHÔNG phải lời giải thích.** Khác biệt là ở TÁC VỤ (MATH vs phần còn lại), chưa rõ cơ chế. Ghi rõ CHƯA GIẢI THÍCH ĐƯỢC. |
| `delta_seq` < 0 ở CẢ BỐN ô | Arm "mỏ neo + tự kiểm" của tôi **không bao giờ có lợi** khi đo sạch -> mọi kết quả dương trước đây đến từ **escalate**, không từ tuần tự. Phải xem lại toàn bộ phát biểu "tuần tự hơn lấy mẫu". |
| `delta_seq` > 0 ở CẢ BỐN ô | Ngược lại: tuần tự luôn có lợi khi KHÔNG escalate -> cái hại ở H41/H42 là do **escalate**, không do tuần tự. |
| tỉ lệ phân tích được < .80 ở ô nào | Ô đó SUY BIẾN, không đọc. |

## Prior TRUNG THỰC (ghi trước)
Đoán hàng 1. **Nhưng prior của tôi sai 5 lần liên tiếp (#78,#79,#80,#81,#83)** — trọng số rất thấp.
Đáng chú ý: hàng 3 và hàng 4 đều buộc tôi rút lại những phát biểu đã ghi, và tôi để nguyên như vậy.

# Đăng ký trước #52 — H46: TÁCH RIÊNG TÁC DỤNG CỦA **MỎ NEO** TRÊN TOÁN (đối xứng với H44 trên code)
**Viết TRƯỚC khi chạy.**

## Vì sao
H44 (#84) đo trên code: bỏ mỏ neo **hồi lại +.0981**. Tức mỏ neo GÂY HẠI trên code.
Nhưng vòng #73 khẳng định mỏ neo CHÍNH LÀ cơ chế làm tuần tự thắng trên toán
(`SS_anc` ngang `PSV` dù không có ngôn ngữ vai nào). **Chưa ai đo tách riêng mỏ neo trên toán.**
H45 đang chạy chỉ có nhánh CÓ mỏ neo, nên không trả lời được câu này.

## Thiết kế — bốn nhánh trong CÙNG một lần chạy, trên CÙNG bài
Lưới: tác vụ ∈ {gsm8k, math} × model ∈ {1.5B, 7B}, 300 bài mỗi ô, 4 ô × 3 shard = 12 kernel.
- `greedy` (1 lượt) — thước đo bão hoà của ô
- `maj3` (3 mẫu)
- **A) `seq_anchor`**: giải → giải lại CÓ MỎ NEO → tự kiểm (3 lượt)
- **B) `seq_noanchor`**: giải → giải lại MỚI (không nhắc đáp án cũ) → tự kiểm (3 lượt)
**A vs B cô lập đúng MỎ NEO** — cùng cấu trúc, cùng số lượt, khác duy nhất ở việc có đưa đáp án
trước đó vào prompt hay không. Đây là bản đối xứng của H44 nhưng KHÔNG escalate, KHÔNG hai model.

## NGƯỠNG HIỆU LỰC (khoá trước)
n mỗi ô ≥ 300. Tỉ lệ phân tích được đáp án ≥ .80. Ô không đạt ⇒ không đọc ô đó.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| A − B > 0 ở các ô TOÁN **và** < 0 ở code (H44 đã đo −.0981) | **Mỏ neo đảo dấu theo miền.** Cơ chế có thật nhưng CÓ ĐIỀU KIỆN. Phải viết lại phát biểu vòng #73 kèm điều kiện miền. |
| \|A − B\| < .02 ở mọi ô toán | **Mỏ neo KHÔNG làm gì trên toán.** Phát biểu "cơ chế là mỏ neo" ở vòng #73 **SAI** — `SS_anc` ngang `PSV` vì lý do khác. Phải RÚT LẠI. |
| A − B < 0 ở ô toán (giống code) | **Mỏ neo hại ở MỌI miền.** Mọi thắng lợi của tuần tự đến từ LƯỢT THÊM, không từ mỏ neo. Rút lại vòng #73. |
| B > `maj3` nhưng A < `maj3` | Tuần tự KHÔNG mỏ neo mới là thứ đáng dùng; bản có mỏ neo đã luôn tự làm hỏng mình. |
| parse < .80 ở ô nào | Ô đó SUY BIẾN, không đọc. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1** (mỏ neo giúp ở toán, hại ở code). Prior của tôi sai 5/6 lần gần đây
(#84 đúng, #78–#81 và #83 sai). Hàng 2 và hàng 3 đều buộc RÚT LẠI một phát biểu trung tâm
của dự án, và tôi để nguyên khả năng đó trong bảng.

# Đăng ký trước #53 — H47: TÁI LẬP PHÂN RÃ MỎ NEO CỦA H44 TRÊN TÁCH MBPP CÒN LẠI
**Viết TRƯỚC khi chạy.**

## Vì sao
H44 (#84) đo trên MBPP 11–510: trên nhóm escalate, `B − A` = **+.0981** (bỏ mỏ neo hồi lại 9.8 điểm),
`C − B` = **+.0566**. Đó là **MỘT tách duy nhất**. Phát hiện "tuần tự hại trên code" chỉ trở nên
chắc chắn khi H43 tái lập nó trên tách khác (+.1159 vs +.1164, lệch .0005). Phân rã mỏ neo
xứng đáng được đối xử y như vậy.

## Thiết kế
Y HỆT H44 (cùng kernel, cùng arm A/B/C, cùng bộ định tuyến oracle), chỉ đổi dữ liệu sang
MBPP `task_id` **511–974** (464 bài) — tách mà H44 CHƯA từng chạy. 12 shard.

## NGƯỠNG HIỆU LỰC (khoá trước)
`pct_escalated` ngoài .15–.85 ⇒ SUY BIẾN. Biên dịch được < .50 ⇒ huỷ. n_escalate ≥ 100.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `B − A` > 0 và lệch với H44 (+.0981) dưới .05 | **TÁI LẬP.** Phân rã mỏ neo là thật: mỏ neo chiếm phần lớn thiệt hại trên code. |
| `B − A` > 0 nhưng lệch ≥ .05 | Hướng đúng, **độ lớn KHÔNG ổn định**. Chỉ được nói về DẤU, không được trích con số 63%. |
| \|`B − A`\| < .02 | **KHÔNG tái lập.** +.0981 ở H44 là nhiễu một tách. Phải rút lại phát biểu "mỏ neo là thủ phạm chính". |
| `B − A` < 0 | Đảo dấu -> phân rã ở #84 **SAI**. Rút lại toàn bộ vòng #84. |
| `C − B` đổi dấu so với H44 | Phần "cấu trúc tuần tự" của phân rã không ổn định; chỉ giữ phần mỏ neo. |

## Prior TRUNG THỰC (ghi trước)
Đoán hàng 1 (tái lập, lệch < .05), vì hai lần đo trước trên code (`C − A`) lệch nhau chỉ .0005.
Prior gần đây: đúng 1/6.

# Đăng ký trước #54 — H48: QUY TẮC BÃO HOÀ (#51) CÓ ĐÚNG TRÊN **CODE** KHÔNG?
**Viết TRƯỚC khi chạy.** Giải quyết mâu thuẫn giữa vòng #85 và vòng #84/#86.

## Mâu thuẫn cần giải
- #85 (H45): `delta_seq` DƯƠNG ở mọi ô có `greedy` < .60, ÂM ở ô `greedy` > .85. **Lưới đó chỉ có
  toán — KHÔNG có ô code nào.**
- #84/#86 (H44/H47): trên nhóm escalate của MBPP, 7B đạt `maj@3` = .5245 / .5867 — **nằm trong dải
  "đáng lẽ phải giúp"** — nhưng tuần tự **THUA** lấy mẫu 5.7 / 8.9 điểm.
=> Hoặc quy tắc bão hoà KHÔNG áp dụng cho code, hoặc code hỏng vì lý do khác. Chưa phân biệt được.

## Thiết kế — thêm ĐÚNG hai ô code vào lưới #51/#52, cùng bộ arm
MBPP `task_id` 11–510, **TOÀN BỘ bài** (không escalate, không hai model), 2 ô × 6 shard = 12 kernel:
- ô `mbpp-1.5B` (dự kiến `greedy` ≈ .42 — **XA TRẦN**) và ô `mbpp-7B` (dự kiến `greedy` ≈ .71)
- nhánh: `greedy` (thước đo bão hoà), `maj3` (bỏ phiếu theo HÀNH VI), **A** (giải → giải lại có mỏ neo
  → tự kiểm), **B** (giải → giải lại mới → tự kiểm). Chấm CHỈ bằng `assert[1..2]`.
Giống hệt lưới toán, chỉ đổi tác vụ -> so sánh trực tiếp được với 4 ô đã có.

## NGƯỠNG HIỆU LỰC (khoá trước)
n mỗi ô ≥ 400. Tỉ lệ biên dịch được ≥ .50. Ô không đạt ⇒ không đọc.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `delta_seq`(mbpp-1.5B) > 0 (ô có `greedy` < .60) | **Quy tắc bão hoà ĐÚNG cả trên code.** Thất bại ở H44/H47 là do đo trên NHÓM ESCALATE (bài đã lọc), không phải do miền code. |
| `delta_seq`(mbpp-1.5B) < 0 dù `greedy` < .60 | **Quy tắc bão hoà KHÔNG áp dụng cho code.** Code khác về bản chất. Phải ghi rõ #85 chỉ đúng cho TOÁN, và sửa phát biểu đã ghi ở vòng #87. |
| cả hai ô code đều ≈ 0 (\|delta\| < .02) | Tuần tự **trung tính** trên code; thiệt hại ở H44/H47 đến từ việc chỉ chạy trên nhóm escalate. |
| `delta_seq`(mbpp-7B) > 0 dù `greedy` > .60 | Điểm đổi dấu ước lượng .62–.71 ở #85 **SAI**; phải bỏ con số đó. |
| A − B < −.05 ở ô code | Mỏ neo hại trên code kể cả khi KHÔNG escalate -> củng cố #84/#86 ngoài phạm vi nhóm escalate. |

## Prior TRUNG THỰC (ghi trước)
Đoán hàng 1 (quy tắc đúng cả trên code; thất bại trước đó là do lọc theo nhóm escalate).
Prior gần đây: đúng 2/7 (#84, #86 đúng; #78–#81, #83 sai).

# Đăng ký trước #55 — H49: **LẬP KẾ HOẠCH CÓ ĐÁNG MỘT LƯỢT KHÔNG, KHI BÀI ĐỦ DÀI?**
**Viết TRƯỚC khi chạy.** Nguyên chỉ ra: MBPP là hàm 3 dòng — **không có gì để lập kế hoạch**.

## Vì sao phép thử cũ có thể đã hỏi sai chỗ
Dự án đã đo Planner nhiều lần và đều ~vô dụng: Shapley cho planner ÂM ở 1.5B, `P3S − maj@4` = +.012 (2/5),
`PSVA − PSV` = +.016 (3/5). **Nhưng tất cả đều đo trên GSM8K/MATH/MBPP — bài một bước hoặc một hàm ngắn.**
Không thể đo giá trị của phân rã trên tác vụ **không có cấu trúc để phân rã**.

## Dữ liệu — BigCodeBench (đã chạy thử: 28/30 lời giải chuẩn ĐẠT qua bộ đo của tôi)
1140 bài, mỗi bài yêu cầu **ghép nhiều thư viện, nhiều bước**. So với MBPP:
prompt trung vị **607** ký tự (MBPP: một câu), lời giải chuẩn trung vị **414** ký tự (MBPP: ~3 dòng).
Chấm bằng `unittest` đi kèm. Dùng 300 bài đầu mỗi ô. 2 ô (7B, 1.5B) × 6 shard = 12 kernel.

## Nhánh — CÙNG NGÂN SÁCH 3 LƯỢT
- `greedy` (1 lượt) — thước đo bão hoà của ô
- `maj3` — 3 mẫu song song + bỏ phiếu theo HÀNH VI
- `seq` — giải → giải lại → tự kiểm (3 lượt)  ← nhánh đã nghiên cứu ở #85/#87
- **`PSV`** — **lập kế hoạch (không viết code) → giải theo kế hoạch → tự kiểm** (3 lượt)
`PSV` vs `seq` là phép so sạch: **cùng 3 lượt**, chỉ khác lượt đầu dùng để LẬP KẾ HOẠCH hay để GIẢI.

## NGƯỠNG HIỆU LỰC (khoá trước)
`maj3` của một ô ngoài khoảng .05–.95 ⇒ ô đó SUY BIẾN (sàn/trần), không đọc.
n mỗi ô ≥ 250. Tỉ lệ chạy được (không lỗi cú pháp) ≥ .50.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `PSV` > `maj3` **và** `PSV` > `seq`, cả hai ≥ .02 | **LẬP KẾ HOẠCH CÓ GIÁ TRỊ khi bài đủ dài.** Các kết quả null trước đây là do BỘ DỮ LIỆU quá ngắn, không phải do Planner vô dụng. Kết quả lớn — phải tái lập trước khi công bố. |
| \|`PSV` − `seq`\| < .02, cả hai > `maj3` | **Lượt thêm mới quan trọng, KHÔNG phải nội dung lượt đó.** Khớp #87 (mỏ neo ≈ 0): thứ có giá trị là THÊM MỘT LƯỢT, viết gì trong đó gần như không đổi. |
| `PSV` ≤ `maj3` | **Lập kế hoạch KHÔNG đáng một lượt kể cả trên bài dài nhiều bước.** Tiền đề phân rã theo vai thất bại ngay trên bộ dữ liệu chọn để ưu ái nó. Ghi rõ. |
| `seq` > `maj3` nhưng `PSV` < `maj3` | Tinh chỉnh tuần tự giúp; **riêng LẬP KẾ HOẠCH gây hại** — nó tiêu một lượt mà không sinh ra code nào. |
| `maj3` ngoài .05–.95 | Ô SUY BIẾN, không kết luận. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2** (lượt thêm quan trọng, nội dung không) vì #87 vừa cho thấy mỏ neo ≈ 0 trên toán.
Nhưng trực giác của Nguyên (hàng 1) hợp lý và **chưa từng được kiểm trên bài dài** — đó chính là
lý do chạy phép thử này. Prior gần đây: đúng 2/7.

## BỔ SUNG cho #55 (H49) — **KIỂM TRA CAN THIỆP**, ghi 2026-08-10, SAU khi thấy dữ liệu 1.5B
**Ghi rõ: bổ sung này là HẬU NGHIỆM.** #55 gốc khoá ngưỡng độ chính xác và ngưỡng suy biến
nhưng **QUÊN kiểm tra xem can thiệp có thật sự xảy ra hay không**. Đó là thiếu sót của tôi.

### Điều đã đo được
Ô 1.5B: **215/250 = 86%** "kế hoạch" **chứa code** (khối ```; có `def`/`import`),
dù prompt ghi rõ "Do NOT write any code".
=> Nhánh `PSV` của ô đó **không hề kiểm lập kế hoạch**. Nó là "viết code → viết lại từ code đó →
tự kiểm", tức `seq` với chữ khác. Đọc `PSV` 8/50 vs `seq` 15/50 thành "lập kế hoạch gây hại"
là **kết luận về một can thiệp CHƯA TỪNG DIỄN RA**.

### NGƯỠNG BỔ SUNG (áp dụng cho mọi ô của #55, và cho mọi phép thử có vai "Planner" về sau)
- Tính `plan_is_code_rate` = tỉ lệ "kế hoạch" chứa khối ``` hoặc dòng bắt đầu bằng `def `/`import `/`from `.
- **`plan_is_code_rate` > .20 ⇒ ô đó KHÔNG ĐỌC ĐƯỢC cho câu hỏi lập kế hoạch.** Ghi là
  "can thiệp thất bại", KHÔNG phải "lập kế hoạch vô dụng".
- Ô nào đạt ngưỡng (< .20) thì đọc bình thường theo bảng khoá #55 gốc.

### Hệ quả
Ô 1.5B (86%) **KHÔNG ĐỌC ĐƯỢC**. Ô 7B chờ đo — 7B tuân lệnh định dạng tốt hơn nên có thể đạt.
Nếu ô 7B cũng trượt, phải chạy lại với prompt ép chặt hơn (cấm dấu ```, bắt buộc văn xuôi đánh số)
trước khi được phát biểu bất cứ điều gì về giá trị của lập kế hoạch.


# Đăng ký trước #56 — H50: LẬP KẾ HOẠCH, **CƯỠNG CHẾ Ở TẦNG SINH** (H49 thất bại can thiệp)
**Viết TRƯỚC khi chạy.**

## Vì sao phải chạy lại
H49 (#55) hỏng ở khâu can thiệp: "kế hoạch" chứa code ở **85.3% (1.5B)** và **100% (7B)**.
Bảo model "Do NOT write any code" **không có tác dụng** — cả hai cỡ đều viết thẳng lời giải.
Không thể kết luận gì về lập kế hoạch từ dữ liệu đó (đã ghi ở bổ sung #55).

## Thay đổi DUY NHẤT so với H49: cưỡng chế, không phải nhờ vả
1. **Chặn ở tầng sinh**: truyền `bad_words_ids` cho chuỗi ``` (dấu rào code). Model **không thể**
   sinh khối code trong lượt lập kế hoạch.
2. Prompt chặt: "Trả lời bằng 3–6 bước đánh số, mỗi bước MỘT CÂU văn xuôi. Không có code."
3. **Cắt an toàn**: trước khi đưa kế hoạch sang lượt giải, xoá mọi khối ``` còn sót và mọi dòng
   khớp `def \w+\(`. Lượt giải chỉ nhận VĂN XUÔI.

## Định nghĩa lại thước đo can thiệp (nêu rõ vì đã đổi so với #55)
`plan_is_code` = có ``` **hoặc** khớp `\bdef\s+\w+\s*\(`.
(#55 tính cả dòng bắt đầu bằng `import`/`from`; kế hoạch nhắc tên thư viện là HỢP LỆ,
nên thước đo cũ quá nghiêm. Ghi rõ thay đổi này TRƯỚC khi chạy.)
**Ngưỡng giữ nguyên: `plan_is_code_rate` > .20 ⇒ ô KHÔNG ĐỌC ĐƯỢC.**

## Thiết kế
BigCodeBench, 300 bài, 2 ô (1.5B, 7B) × 6 shard. Nhánh: `greedy` | `maj3` | `seq` | `PSV`
(kế hoạch cưỡng chế → giải theo kế hoạch → tự kiểm). Cùng 3 lượt như #55.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `plan_is_code_rate` > .20 dù đã cưỡng chế | Can thiệp lại thất bại. **KHÔNG kết luận gì về lập kế hoạch**; ghi là giới hạn phương pháp. |
| Đạt ngưỡng **và** `PSV` > `maj3` **và** `PSV` > `seq`, cả hai ≥ .02 | **LẬP KẾ HOẠCH CÓ GIÁ TRỊ trên bài dài.** Các null trước đây là do bộ dữ liệu ngắn. |
| Đạt ngưỡng **và** \|`PSV` − `seq`\| < .02 | **Lượt thêm quan trọng, nội dung KHÔNG.** Khớp #87 (mỏ neo ≈ 0). |
| Đạt ngưỡng **và** `PSV` < `maj3` | **Lập kế hoạch KHÔNG đáng một lượt, kể cả trên bài dài** — và lần này can thiệp CÓ diễn ra. Kết luận âm THẬT. |
| `PSV` thấp hơn H49 rõ rệt | Cưỡng chế đã lấy mất "kế hoạch = code nháp" vốn đang giúp -> ghi rõ: cái giúp là BẢN NHÁP, không phải KẾ HOẠCH. |

## Prior TRUNG THỰC (ghi trước)
Đoán hàng 4 (`PSV` < `maj3`): khi bị cấm viết code, kế hoạch văn xuôi của model 1.5B/7B nhiều khả
năng mơ hồ và lượt giải phải bắt đầu từ đầu — mất một lượt. Prior gần đây: đúng 2/8.


# Đăng ký trước #57 — H51: **NGƯỜI LẬP KẾ HOẠCH MẠNH HƠN NGƯỜI GIẢI** — dạng bất đối xứng chưa từng thử
**Viết TRƯỚC khi chạy.**

## Vì sao đúng phép thử này
H50 (#90) đã chốt: lập kế hoạch không đáng một lượt **khi model tự lập kế hoạch cho chính mình**.
Nhưng **kết quả DƯƠNG mạnh nhất của dự án là BẤT ĐỐI XỨNG**: Solver 1.5B + Verifier 7B = **+14 điểm** (H15),
và Shapley cho planner ÂM ở 1.5B nhưng **DƯƠNG ở 7B** — gợi ý ngưỡng NĂNG LỰC, không phải vai vô dụng.
Dạng tương ứng cho lập kế hoạch **chưa bao giờ chạy**: **7B lập kế hoạch, 1.5B thực thi.**

## Thiết kế — BigCodeBench 300 bài, người GIẢI luôn là 1.5B
Chi phí quy về FLOP 1.5B (1 lượt 7B = 5.07):
- `small_greedy` — 1.5B, 1 lượt — **chi phí 1.00**
- `small_seq` — 1.5B: giải → giải lại → tự kiểm — **chi phí 3.00**
- **`bigplan_smallsolve`** — **7B lập kế hoạch** (cưỡng chế như #56) → 1.5B giải theo kế hoạch →
  1.5B tự kiểm — **chi phí 5.07 + 2 = 7.07**
- `big_greedy` — 7B, 1 lượt — **chi phí 5.07** ← mốc quan trọng nhất
Nạp model TUẦN TỰ (7B lập kế hoạch cho toàn bộ, giải phóng, rồi nạp 1.5B) để vừa VRAM T4.
6 shard. Chấm bằng unittest đi kèm.

## NGƯỠNG HIỆU LỰC (khoá trước)
- `plan_is_code_rate` > .20 ⇒ KHÔNG đọc (như #56; thước đo: có ``` hoặc khớp `\bdef\s+\w+\s*\(`).
- n ≥ 250. Tỉ lệ chạy được ≥ .50.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `bigplan_smallsolve` > `small_seq` **và** > `big_greedy` | **PHÂN RÃ VAI BẤT ĐỐI XỨNG CÓ GIÁ TRỊ.** Kế hoạch từ model mạnh nâng được model yếu vượt cả việc chạy thẳng model mạnh. Kết quả lớn — phải tái lập. |
| > `small_seq` nhưng ≤ `big_greedy` | Kế hoạch mạnh **có giúp** model yếu, **nhưng bị ÁP ĐẢO**: rẻ hơn và tốt hơn nếu chỉ chạy thẳng 7B. Y hệt hình mẫu định tuyến ở #81. |
| ≤ `small_seq` | **Kế hoạch từ model MẠNH HƠN cũng không giúp nổi model yếu.** Đây là dạng phủ định MẠNH NHẤT: lập kế hoạch thất bại kể cả khi người lập kế hoạch giỏi hơn hẳn người giải. |
| `plan_is_code_rate` > .20 | Can thiệp thất bại, không kết luận. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2** (giúp model nhỏ nhưng bị `big_greedy` áp đảo) — theo đúng hình mẫu H42:
tín hiệu/kế hoạch tốt, nhưng cấu hình tổng thể vẫn thua việc dùng thẳng model lớn.
Tỉ lệ prior đúng gần đây: 3/9.


# Đăng ký trước #58 — H52: **REFACTOR** — giữ nguyên hành vi có cần ORACLE THẬT không?
**Viết TRƯỚC khi chạy.** Nguyên đề xuất thử tác vụ refactor.

## Vì sao refactor là phép thử đúng cho phân biệt trung tâm
Phân biệt đã khoá ở #42 và củng cố ở H35: **bộ kiểm chỉ có giá trị khi là ORACLE VỀ TÍNH ĐÚNG**
(`exec3` +6..+11), **không** khi chỉ là LLM tự nhận xét (`llm3` ≈ 0).
Refactor là nơi phân biệt đó sắc nhất: **"hành vi có đổi không" được bộ test trả lời CHÍNH XÁC**.
Ngoài ra refactor còn là **mỏ neo ở dạng thuần tuý**: model được đưa code và bảo cải thiện.
Ở H44/H47, mỏ neo vào code HỎNG khiến model VÁ thay vì viết lại (−8..−10 điểm).
Ở đây code được đưa là **ĐÚNG** — mỏ neo chính là đề bài.

## Dữ liệu
BigCodeBench 300 bài. Đầu vào refactor = `complete_prompt + canonical_solution` (lời giải chuẩn,
**đã chạy qua test trong chính kernel** để lọc; bài nào lời giải chuẩn không đạt thì LOẠI).
Trung vị: 114 nút AST, 35 dòng.

## Nhánh (7B)
- `ref1` — refactor 1 lượt
- `ref_seq` — refactor → **LLM tự nhận xét** (2 lượt) — **KHÔNG có oracle**
- `ref_exec` — refactor → **CHẠY TEST** → nếu trượt thì sửa theo stderr (2 lượt) — **CÓ oracle**
Nêu rõ: `ref_exec` **dùng chính bộ test dùng để chấm**. Đó KHÔNG phải so sánh ngang thông tin;
đúng là điều kiện "có oracle" mà #42 định nghĩa. Câu hỏi là **oracle đáng giá bao nhiêu**.

## Thước đo (khoá trước)
1. **`preserve`** = code sau refactor VẪN đạt bộ test. Đây là thước đo chính.
2. **`simpler`** = giảm số nút AST so với bản gốc, **CHỈ tính trên các bài `preserve`**
   (nếu không thì xoá sạch code cũng "giảm phức tạp").
3. **`good_refactor`** = `preserve` **và** `simpler`. Đây mới là refactor thành công.

## NGƯỠNG HIỆU LỰC (khoá trước)
n ≥ 250 sau khi lọc. Tỉ lệ phân tích được AST của bản refactor ≥ .80.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `preserve`(exec) − `preserve`(seq) ≥ .10 | **ORACLE LÀ THIẾT YẾU để refactor an toàn.** Xác nhận #42 ở miền thứ ba. LLM tự nhận xét không phát hiện được đổi hành vi. |
| \|`preserve`(exec) − `preserve`(seq)\| < .05 | LLM tự nhận xét **đủ** cho refactor -> **LÀM YẾU** phân biệt #42. Phải ghi rõ. |
| `preserve` của MỌI nhánh < .50 | Model **không refactor an toàn được** ở quy mô này. Giới hạn NĂNG LỰC, không phải về vai. |
| `simpler` cao nhưng `preserve` thấp | "Cải thiện" thực chất là **phá**. Ghi rõ, và chỉ được báo `good_refactor`. |
| `ref1` ≈ `ref_seq` ở `good_refactor` | Lượt thêm không mang lại gì khi KHÔNG có oracle (khớp #90/#91). |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1** (oracle hơn hẳn), theo #42 và H35. Tỉ lệ prior đúng gần đây: 4/10.


# Đăng ký trước #59 — H53: ORACLE ĐƯỢC SỬA **BA VÒNG** THAY VÌ MỘT, TRÊN REFACTOR
**Viết TRƯỚC khi chạy.**

## Vì sao
H52 (#92) cho `preserve(exec) − preserve(seq)` = **+.0602**, **giữa** hai ngưỡng đã khoá (.05–.10),
nên không được coi là xác nhận #42. **Nhưng thiết kế của tôi chỉ cho oracle SỬA MỘT VÒNG.**
H35 — nơi oracle thắng +6..+11 — dùng **BA VÒNG** (`exec3`). Vậy +.0602 có thể là hệ quả của
lựa chọn ngân sách của tôi, không phải giá trị thật của oracle.
Và 26% bài **vẫn hỏng hành vi dù đã có oracle** — cần biết một vòng nữa có cứu được không.

## Thiết kế — y hệt H52, chỉ đổi số vòng sửa
BigCodeBench, cùng bộ lọc (lời giải chuẩn phải đạt test trong kernel), 7B nf4, 6 shard.
- `ref1` — refactor 1 lượt (mốc)
- `ref_exec1` — refactor → chạy test → sửa **1 vòng**  (bằng H52, để đối chiếu tái lập)
- **`ref_exec3`** — refactor → chạy test → sửa, lặp tối đa **3 vòng**, dừng sớm khi đạt
Ghi thêm: `rounds_used` (số vòng thực dùng) và `preserve` sau mỗi vòng.

## NGƯỠNG HIỆU LỰC (khoá trước)
n ≥ 250. AST đọc được ≥ .80. Mọi shard cùng `quant` (script gộp DỪNG nếu khác).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `preserve`(exec3) − `preserve`(seq) ≥ .10 | **XÁC NHẬN #42 trên refactor.** +.0602 ở H52 là do tôi chỉ cho sửa MỘT vòng, không phải giới hạn của oracle. |
| `preserve`(exec3) − `preserve`(exec1) < .02 | **Vòng sửa thêm KHÔNG cứu được gì.** 26% hỏng là lỗi model không giữ nổi hành vi, oracle chỉ ra lỗi nhưng model không sửa nổi. Kết luận NĂNG LỰC. |
| `preserve`(exec3) ≥ .90 | Oracle + lặp làm refactor **an toàn thực dụng**. Khuyến nghị triển khai: KHÔNG BAO GIỜ refactor mà không chạy test sau mỗi vòng. |
| `preserve`(exec1) lệch H52 (.7707) hơn .05 | H52 **không tái lập** — phải xem lại cả vòng #92. |

## Prior TRUNG THỰC (ghi trước)
Đoán hàng 2 (vòng thêm cứu được rất ít): lỗi refactor thường là **đổi ngữ nghĩa tinh vi**,
stderr chỉ ra triệu chứng chứ không chỉ ra chỗ lệch. Khác với sinh code mới, nơi lỗi thường thô hơn.
Tỉ lệ prior đúng gần đây: 4/11.


# Đăng ký trước #60 — H54: **THẮNG LỢI DUY NHẤT CỦA DỰ ÁN CÓ SỐNG SÓT KHI LÊN 14B KHÔNG?**
**Viết TRƯỚC khi chạy.** Nguyên yêu cầu chạy ở 14B.

## Vì sao đúng phép thử này
Sau cả ngày, **kết quả DƯƠNG thực dụng duy nhất** còn đứng là **định tuyến theo đồng thuận trên MATH**:
- H39_m (n=200, bf16, RTX 5090): **+.140** so `big_maj3`, rẻ hơn 1.63×
- H40 (n=500, fp16, 20 kernel Kaggle): **+.092** so `big_maj3`, rẻ hơn 1.66×
Cùng chiều, phần cứng độc lập, mẫu gấp 2.5×. **Nhưng cả hai đều ở cỡ 7B.**
Câu hỏi quyết định: đây là **quy tắc triển khai được** hay chỉ là **hiện tượng của model nhỏ**?
Nếu model lớn đủ giỏi thì nhóm "1.5B đồng thuận" mà ta GIỮ LẠI sẽ ngày càng đắt về cơ hội.

## Thiết kế — y hệt H40, chỉ đổi model LỚN: 7B -> **14B**
MATH-500, 500 bài, 20 shard. Nhỏ = Qwen2.5-1.5B-Instruct (fp16).
Lớn = **Qwen2.5-14B-Instruct-AWQ** (đã kiểm: `Qwen2ForCausalLM`, có `lm_head`, có chat template,
AWQ 4-bit gemm chạy được trên sm_75 của T4).
Quy đổi chi phí: **1 lượt 14B = 9.80 lượt 1.5B** (14.7/1.5), thay cho 5.07 của 7B.
Nhánh: `small_maj3`, `small_maj8`, `big_maj3`, `big_maj8`, `escalate`, `escalate_seq` — như H40.
Phân tầng theo `level` của MATH-500 qua mã băm đề bài, như #46.

## NGƯỠNG HIỆU LỰC (khoá trước)
- `pct_escalated` ngoài .15–.85 ⇒ SUY BIẾN.
- Đẳng thức phân rã lệch > .01 ⇒ BUG, không đọc.
- Mọi shard cùng `quant` (script gộp DỪNG nếu khác).
- `big_maj3`(14B) phải **> `big_maj3`(7B) = .488** đo ở H40; nếu KHÔNG thì model lớn không thực sự
  mạnh hơn trong thiết lập này ⇒ phép thử **mất hiệu lực**, ghi rõ, không kết luận về quy mô.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `escalate_seq` > `big_maj3` **và** rẻ hơn, như ở 7B | **QUY TẮC SỐNG SÓT QUA MỘT BƯỚC QUY MÔ.** Đây là kết quả triển khai được mạnh nhất dự án có. |
| chênh acc dương nhưng **NHỎ HƠN** ở 7B (+.092) rõ rệt | Lợi ích **TEO DẦN theo quy mô**. Ngoại suy lên model lớn hơn là KHÔNG có cơ sở. Ghi rõ xu hướng. |
| `escalate_seq` ≤ `big_maj3` | **Thắng lợi ở 7B là HIỆN TƯỢNG CỦA MODEL NHỎ.** Kết quả dương thực dụng duy nhất của dự án **chết ở 14B**. Phải ghi thẳng, không giảm nhẹ. |
| `big_maj3`(14B) ≤ .488 | Phép thử mất hiệu lực (model "lớn" không mạnh hơn). Không kết luận. |
| `pct_escalated` ngoài .15–.85 | SUY BIẾN. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2** (còn dương nhưng teo lại): 14B trên MATH mạnh hơn 7B rõ, nên chi phí cơ hội của
việc giữ bài cho 1.5B tăng lên — chính là cơ chế đã giết định tuyến trên GSM8K (`opp_cost` tăng).
Tỉ lệ prior đúng gần đây: **5/12**.


# Đăng ký trước #61 — H55: **VERIFIER TỰ VIẾT TEST** (đề xuất của Nguyên) — vai trò có ARTIFACT KHÁC NHAU
**Viết TRƯỚC khi chạy.**

## Vì sao thiết kế này khác mọi thứ đã đo
Mọi "vai" tôi đã đo đều sinh ra **CÙNG một artifact**: một lời giải. "Kế hoạch" hoá ra là code ở
**85.3%–100%** (#89); lượt "kiểm" chỉ là giải lại. **Không có gì để phân rã.**
Ở đây mỗi vai sinh ra **loại đối tượng KHÁC NHAU**: kế hoạch (văn xuôi) · **test (chạy được)** · code.
Model không thể gộp "viết test" thành "viết hàm" — kiểu đầu ra không cho phép.

Quan trọng hơn: **verifier không NHẬN XÉT, nó TẠO RA ORACLE.** Phát hiện bền nhất của dự án là
bộ kiểm chỉ đáng giá khi là oracle về tính đúng (test thật: +6..+11; LLM nhận xét: 0 hoặc hại,
**4 lần độc lập** trong ngày). Thiết kế này tự sinh ra đúng thứ đó.

## Dữ liệu — MBPP 11–510 (498 bài), model 7B
Chọn MBPP vì đã có sẵn mốc trên **cùng 498 bài** (#88): `greedy` .6546 · `maj3` .6727 ·
định tuyến oracle .7392. `assert[0]` cho tên hàm; **`assert[1..2]` CHỈ để chấm**, không nhánh nào thấy.

## Nhánh — cùng 3 lượt sinh
- `solve1` — 1 lượt (mốc)
- `maj3` — 3 mẫu, bỏ phiếu theo HÀNH VI trên lời gọi `assert[0]` (giống #88, KHÔNG dùng kết quả chấm)
- **`TDD`** — verifier **viết test** → solver cài đặt → **CHẠY test tự sinh** → hỏng thì sửa (3 lượt)
- **`TDD_noexec`** — verifier viết test → solver cài đặt **CÓ NHÌN test** → tự nhận xét (3 lượt)
  ← đối chứng tách **"chạy test"** khỏi **"prompt giàu thông tin hơn"**

## Thước đo (khoá trước)
- **`test_soundness`** = tỉ lệ test tự sinh mà **LỜI GIẢI CHUẨN VẪN ĐẠT**. Test bác bỏ lời giải
  tham chiếu là **sai theo định nghĩa**.
- **`test_power`** = tỉ lệ mẫu solver ĐÃ BIẾT LÀ SAI (trượt `assert[1..2]`) mà test tự sinh **bắt được**.
  (Chống test đúng-nhưng-rỗng kiểu `assert f(x) == f(x)`: soundness hoàn hảo, power = 0.)
- Độ chính xác cuối cùng chấm **CHỈ bằng `assert[1..2]`**.

## NGƯỠNG HIỆU LỰC (khoá trước)
- **`test_soundness` < .50 ⇒ ô KHÔNG ĐỌC ĐƯỢC** cho câu hỏi TDD (test sai nhiều hơn đúng).
  Ghi là "vai verifier thất bại ở khâu tạo oracle", KHÔNG phải "phân rã vai vô dụng".
- Tỉ lệ biên dịch ≥ .50. n ≥ 400.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `TDD` − `maj3` ≥ +.02 **và** `test_soundness` ≥ .70 | **PHÂN RÃ VAI CÓ GIÁ TRỊ khi các vai sinh ra ARTIFACT KHÁC NHAU.** Verifier tự tạo oracle là vai đầu tiên trong dự án trả được tiền. Phải tái lập trên tách 511–974 trước khi công bố. |
| \|`TDD` − `maj3`\| < .02 | Oracle tự sinh **không thêm gì** so với lấy mẫu. Ghi rõ. |
| `TDD` < `maj3` − .02 | **Test tự sinh ĐÁNH LẠC HƯỚNG**: solver tối ưu theo đặc tả SAI. Kết quả âm có cơ chế rõ. |
| \|`TDD` − `TDD_noexec`\| < .02 | Lợi ích (nếu có) đến từ **prompt giàu hơn**, KHÔNG phải từ việc CHẠY test. Làm yếu cách đọc "oracle". |
| `test_soundness` ≥ .70 nhưng `test_power` < .20 | Test **đúng nhưng rỗng** — không bắt được lỗi nào. Vai verifier hình thức, vô dụng. |
| `test_soundness` < .50 | Ô SUY BIẾN cho câu hỏi TDD. |

## Prior TRUNG THỰC (ghi trước)
Đoán `test_soundness` khoảng **.60–.80**, và kết quả rơi vào **hàng 2 hoặc 3**: một test sai một cách
tự tin còn tệ hơn không có test. Nhưng đây là thiết kế vai **đầu tiên** có cơ chế mà tôi tin là
có thể chạy được nếu test đủ đúng. Tỉ lệ prior đúng gần đây: **5/12**.


# Đăng ký trước #62 — H56: DÙNG TEST TỰ SINH ĐỂ **CHỌN** TRONG k MẪU (không phải để SỬA)
**Viết TRƯỚC khi chạy.**

## Khoảng trống ĐO ĐƯỢC — đây là chỗ duy nhất còn tiền trên bàn
MBPP 7B, n=464 (dữ liệu H47 đã có):
| | |
|---|---|
| `maj@8` | **.7306** |
| `oracle@8` (có ít nhất 1 mẫu đúng) | **.8082** |
| **khoảng trống** | **+.0776** |
**375/464 = 80.8% số bài ĐÃ CÓ lời giải đúng trong 8 mẫu**; bỏ phiếu chọn sai ở **36** bài.
Suốt cả ngày không đường ống nào thu được quá +.01. Ở đây có **7.8 điểm** đang bỏ không.

## Vì sao lần này khác các phép thử CHỌN đã thất bại
- H37: bộ kiểm huấn luyện, AUC **.893** -> chỉ **+2.4** điểm. Nhưng đó là **điểm số học được**.
- #94 (H55): test tự sinh có **soundness .871**, **power .751** — tức **BỘ LỌC CHẠY ĐƯỢC**,
  đúng loại tín hiệu mà cả dự án cho thấy là có giá trị. **Nhưng tôi dùng nó để SỬA, không phải để CHỌN.**
=> Phép thử này chĩa đúng công cụ vào đúng việc.

## Thiết kế — MBPP 11–510, 7B, 12 shard
- `maj3`, `maj8` — bỏ phiếu theo HÀNH VI (mốc, giống #88)
- **`select_tests`** — sinh 8 mẫu + 1 lượt viết test; **chấm mỗi mẫu bằng SỐ TEST TỰ SINH nó đạt**;
  chọn mẫu đạt nhiều nhất (hoà -> bỏ phiếu hành vi trong nhóm hoà). Chi phí: 8 lượt + **1 lượt** viết test.
- `oracle8` — trần lý thuyết (có mẫu nào đúng không), **chỉ để báo cáo tỉ lệ khoảng trống thu được**
Chấm CHỈ bằng `assert[1..2]`. Ghi thêm `test_soundness`, `test_power` như #61.

## NGƯỠNG HIỆU LỰC (khoá trước)
`test_soundness` < .50 ⇒ không đọc. n ≥ 400. Mọi shard cùng `quant`.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `select_tests` − `maj8` ≥ +.02 | **CHỌN BẰNG ORACLE TỰ SINH CÓ TÁC DỤNG.** Kết quả DƯƠNG đầu tiên vượt mốc trong ngày. Báo **tỉ lệ khoảng trống thu được** = (select−maj8)/(oracle8−maj8). Phải tái lập trên 511–974. |
| \|`select_tests` − `maj8`\| < .02 | Test tự sinh **không chọn tốt hơn bỏ phiếu**. Cùng với #94 -> oracle tự sinh vô dụng cho CẢ sửa lẫn chọn. Kết luận âm MẠNH. |
| `select_tests` < `maj8` − .02 | Test tự sinh **làm hỏng việc chọn** (đẩy về mẫu sai). |
| thu được < 25% khoảng trống dù ≥ +.02 | Có tác dụng nhưng **phần lớn 7.8 điểm vẫn bỏ không** -> nút thắt là CHỌN, và ta chưa chọn nổi. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 với biên độ nhỏ**: soundness .871 và power .751 là bộ lọc thật, nhưng chỉ **1.44 assert/bài**
nên nhiều mẫu sẽ HOÀ nhau -> thu được có lẽ **25–50%** khoảng trống, tức **+2 đến +4 điểm**.
Nếu đúng, đây là thứ đầu tiên trong ngày HƠN được mốc. Tỉ lệ prior đúng: **6/13**.


# Đăng ký trước #63 — H58: **SINH NHIỀU TEST HƠN** — số lượng test có phải nút thắt của việc CHỌN?
**Viết TRƯỚC khi chạy.**

## Đo được ở #95, và nó chỉ thẳng vào việc kế tiếp
`select_tests` thắng +.0401 với **chỉ 1.44 assert/bài**. Nhưng phân tích thêm:
| | |
|---|---|
| bài có HOÀ ở điểm cao nhất | **96.4%** |
| bài mà **CẢ 8** mẫu hoà nhau | **371/498 = 74.5%** |
| phá hoà HOÀN HẢO chỉ thêm | **+.0301** (→ .7390) |
=> Trên 3/4 số bài, test **không phân biệt được gì** -> nhánh tụt về bỏ phiếu thường.
Toàn bộ +.0401 kiếm được từ **~25% số bài** mà test có phân biệt. Tín hiệu mỏng mà hiệu quả cao
=> **số lượng test là nút thắt**, không phải chất lượng.

## Thiết kế — y hệt H56, chỉ đổi cách sinh test
MBPP 11–510, 7B, 12 shard.
- H56: **1 lượt** viết test, T=0.0 -> 1.44 assert
- **H58: 3 lượt** viết test ở T=0.8, **hợp nhất + khử trùng lặp** -> kỳ vọng 3–5 assert
Chấm mỗi mẫu bằng số test đạt; chọn mẫu cao điểm nhất; hoà -> bỏ phiếu hành vi. Như #62.
Chi phí: 8 lượt sinh + **3 lượt** viết test (H56: 8 + 1).

## RỦI RO PHẢI ĐO — hợp nhất nhiều test thì dễ dính test SAI
Một test sai sẽ **loại oan mẫu đúng**. Vì vậy bắt buộc báo:
- `test_soundness` của **tập hợp nhất** (lời giải chuẩn đạt HẾT các test hợp nhất)
- `avg_tests`, và **tỉ lệ bài còn hoà 8 mẫu**

## NGƯỠNG HIỆU LỰC (khoá trước)
`test_soundness` < .50 ⇒ không đọc. n ≥ 400. Mọi shard cùng `quant`.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `select`(H58) − `select`(H56 = .7088) ≥ +.02 | **SỐ LƯỢNG TEST LÀ NÚT THẮT.** Sinh thêm test là đòn bẩy rẻ và trực tiếp. Báo tỉ lệ khoảng trống thu được so với `oracle8`. |
| \|chênh\| < .02 | Thêm test **không giúp** -> nút thắt là **chất lượng phân biệt**, không phải số lượng. |
| `select`(H58) < `select`(H56) − .02 | **Hợp nhất test làm HẠI**: test sai loại oan mẫu đúng. Kiểm bằng `test_soundness` giảm. |
| `test_soundness` giảm > .10 so với .8712 | Ghi rõ: đánh đổi số lượng lấy độ đúng. Nếu acc vẫn tăng thì chấp nhận được; nếu giảm thì đây là nguyên nhân. |
| tỉ lệ hoà-8-mẫu vẫn > .50 | Ngay cả 3 lượt viết test vẫn không đủ phân biệt -> cần cách khác (test sinh theo mẫu, hoặc test đối kháng). |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 nhưng biên độ vừa phải (+.02 đến +.04)**: nhiều test hơn sẽ phá được phần lớn
hoà-8-mẫu, nhưng trần phá-hoà-hoàn-hảo chỉ là +.0301 nên phần lớn lợi ích phải đến từ việc
test mới phân biệt được ở những bài trước đây cả 8 mẫu cùng đạt. Tỉ lệ prior đúng: **7/14**.


# Đăng ký trước #64 — H59: GRPO **VỚI HÀM THƯỞNG ĐÃ SỬA** — RL có giúp verifier khi mục tiêu không bị lách được?
**Viết TRƯỚC khi chạy.**

## Vì sao chạy lại
Vòng #44 (H23): GRPO đạt **precision 1.00** (5/5 fold) nhưng **V_gain giảm** +.068 -> +.044,
số lần can thiệp **20.2 -> 8.4 / 100 bài**, sửa/phá **45/11 -> 22/0**.
Cơ chế đã rõ và **lỗi là ở tôi, không ở thuật toán**: thưởng = `+1 sửa / −1 phá / **0 nếu im lặng**`.
**Im lặng là MIỄN PHÍ** -> chiến lược tối ưu tầm thường là NÓI ÍT ĐI. Log khớp: `nseq` (chuỗi có
advantage ≠ 0) tụt còn 4–24/96 ở các bước cuối vì mọi mẫu đều đã im lặng như nhau.
=> H23 **không kiểm được** câu hỏi "RL có giúp verifier không". Nó chỉ chứng minh hàm thưởng của tôi hỏng.

## Thay đổi DUY NHẤT: hàm thưởng
- **CŨ**: `+1` sửa đúng · `−1` phá · `0` không đổi
- **MỚI**: thưởng theo **ĐÚNG/SAI CUỐI CÙNG của đầu ra verifier**: `+1` nếu đáp án verifier ĐÚNG,
  `−1` nếu SAI. **Im lặng trên lời giải SAI bị phạt y như phá một lời giải đúng.**
  Không còn nước đi miễn phí.
Mọi thứ khác giữ nguyên: 1.5B + LoRA, GSM8K `main_train`, bp=24, k=4, 100 bước, eval 5 fold test,
Solver LUÔN chạy trên model gốc (so sánh CẶP, hai nhánh dùng chung lời giải).

## PHẢI LƯU (thiếu ở H23)
Toàn văn đầu ra verifier của **cả hai** nhánh trên tập eval -> để đọc trace, không chỉ đếm số.

## NGƯỠNG HIỆU LỰC (khoá trước)
- **`adapter_leak`**: đo `probe_pre` và `probe_post` trên **CÙNG 60 bài**, adapter **TẮT**.
  Lệch > .05 ⇒ HUỶ (6/6 kernel huấn luyện từng dính lỗi này, vòng #60).
- `nseq` trung bình 20 bước cuối < 10/96 ⇒ tín hiệu học đã tắt, ghi rõ là **suy biến**.
- Số lần can thiệp phải báo KÈM precision — không được báo precision một mình.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `V_gain`(lora) − `V_gain`(base) ≥ +.02 **và** số can thiệp KHÔNG giảm quá 25% | **RL CÓ GIÚP khi mục tiêu đúng.** Kết quả dương thật; phải tái lập. |
| `V_gain` không tăng nhưng số can thiệp **TĂNG** | Sửa thưởng đã chặn được "học im lặng", nhưng RL vẫn không làm verifier chính xác hơn. |
| `V_gain` giảm và số can thiệp **TĂNG** | Thưởng mới đẩy sang thái cực ngược: can thiệp bừa. Ghi rõ. |
| số can thiệp vẫn giảm > 25% | Model VẪN học im lặng dù bị phạt -> vấn đề sâu hơn hàm thưởng. |
| `adapter_leak` > .05 | HUỶ, không đọc. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2**: chặn được nước đi "im lặng" nhưng `V_gain` không tăng — vì suốt cả ngày,
mọi cách làm verifier "thông minh hơn" đều không chuyển thành độ chính xác (H37: AUC .893 -> +2.4;
#94: oracle tự sinh dùng để SỬA -> +.004). Nút thắt là **SINH**, không phải **PHÁN ĐOÁN**.
Tỉ lệ prior đúng gần đây: **7/14**.


# Đăng ký trước #65 — H60: **BẤT ĐỐI XỨNG THÔNG TIN** — nhại lại có biến mất khi Solver YẾU HƠN thật không?
**Viết TRƯỚC khi chạy.** Đây là bài kiểm để **GIẾT lời giải thích của chính tôi ở vòng #98.**

## Lời giải thích cần kiểm
H59: GRPO làm verifier co từ **480 -> 19 ký tự**; nó học cách **NHẠI LẠI** Solver.
Tôi đã giải thích bằng số học: nhại lại ghi điểm **đúng bằng** độ chính xác của Solver (.646),
và verifier **cùng model, cùng tri thức** thì không có cách nào làm hơn -> tối ưu của hàm thưởng
CHÍNH LÀ nhại lại. Kết luận tôi đã ghi: *"Verifier KHÔNG có lợi thế thông tin so với Solver
thì KHÔNG THỂ vượt Solver, bất kể hàm thưởng."*

**Đó mới là một lời giải thích, chưa phải bằng chứng.** Nếu đúng, thì khi Solver YẾU HƠN HẲN,
nhại lại bị chặn trần ở độ chính xác thấp của Solver, tối ưu phải dịch ra khỏi nhại lại,
và độ dài đầu ra **không được** sụp.

## Thiết kế
Thay đổi **DUY NHẤT** so với H59: **Solver = Qwen2.5-0.5B-Instruct** (`/root/m05`),
Verifier vẫn là 1.5B (`/root/m15`) + LoRA + **đúng hàm thưởng H59** (+1 đúng / −1 sai).
Mọi thứ khác giữ nguyên: GSM8K train 2400 / test 500, bp=24, k=4, 100 bước, eval 5 fold, seed 0.

## BỐN nhánh, cùng 500 bài test
| Nhánh | Là gì | Vai trò |
|---|---|---|
| **S** | 0.5B giải, greedy | sàn |
| **I** | 1.5B **tự giải, KHÔNG được xem lời giải** | trần-tầm-thường ("cứ lờ Solver đi") |
| **V0** | 1.5B gốc, ĐƯỢC xem lời giải của S | verifier chưa huấn luyện |
| **V\*** | 1.5B + GRPO, ĐƯỢC xem lời giải của S | verifier đã huấn luyện |

**Đại lượng chính là `V* − I`, KHÔNG phải `V* − S`.**
`V* − S` dương là tầm thường (1.5B > 0.5B) và **không** chứng minh gì về việc kiểm tra.
Chỉ `V* − I` mới tách được câu hỏi *"nó có HỌC CÁCH DÙNG lời giải không"*.

## NGƯỠNG HIỆU LỰC (khoá trước)
- `acc(S)` ∈ **[.20, .55]**. Nếu ≥ .55 thì bất đối xứng quá yếu, phép kiểm vô nghĩa ⇒ HUỶ.
- `adapter_leak` ≤ .05 (đo `probe_pre`/`probe_post`, adapter TẮT, cùng 60 bài).
- `nseq` TB 20 bước cuối ≥ 10/96, nếu không: suy biến, ghi rõ.
- n = 500 test, tách rời tập train.
- **Bắt buộc lưu toàn văn** trace cả 4 nhánh.

## Chỉ số CHẨN ĐOÁN NHẠI LẠI (khoá trước, so thẳng với H59)
- `len_med`: độ dài trung vị đầu ra verifier. H59: base 480 -> lora **19**.
- `agree_wrong`: tỉ lệ verifier ra ĐÚNG đáp án của Solver **khi Solver SAI**. H59: .497 -> **.644**.
- `agree_right`: như trên nhưng khi Solver ĐÚNG.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `V* − I` ≥ **+.02** VÀ `agree_wrong` GIẢM VÀ `len_med` không sụp (≥ 50% của base) | **Verifier ĐÃ HỌC DÙNG lời giải một cách CÓ ĐIỀU KIỆN.** Lời giải thích #98 **ĐƯỢC XÁC NHẬN**: lợi thế thông tin đúng là ràng buộc chặn. Vai trò "verifier" có thật khi có bất đối xứng. |
| \|`V* − I`\| < .02 và `V*` >> `S` | Nó học cách **LỜ ĐI** Solver, không phải kiểm tra nó. Giải thích #98 đúng NỬA (hết nhại lại) nhưng **vai trò verifier vẫn không hình thành** — nó chỉ thành một Solver thứ hai. Phải ghi: vai trò không tồn tại, chỉ có năng lực model. |
| `len_med` VẪN sụp (< 50% base) VÀ `agree_wrong` VẪN tăng, dù Solver yếu | **GIẢI THÍCH #98 SAI — RÚT LẠI.** Sụp đổ do thứ khác (độ dài chuỗi / entropy / advantage thưa), không phải do thiếu lợi thế thông tin. |
| `V*` < `V0` − .02 | GRPO có hại kể cả khi bất đối xứng. Ghi rõ, RL bỏ khỏi hướng này. |
| `acc(S)` ≥ .55 | HUỶ, không đọc (bất đối xứng không thành). |
| `adapter_leak` > .05 | HUỶ, không đọc. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2** (~55%). Một verifier 1.5B nhìn lời giải kém của 0.5B có rất ít lý do để
*điều kiện hoá* lên lời giải đó; nước đi dễ nhất là **tự giải lấy**. Nếu vậy thì đây là một
kết quả ÂM quan trọng: "verifier" chưa bao giờ là một VAI TRÒ, nó chỉ là năng lực model
được dán nhãn khác. Hàng 1 ~25%. Hàng 3 (tôi sai) ~15% — và tôi phải ghi nhận nghiêm túc
khả năng này vì hôm nay tôi đã sai công khai 2 lần (GPU "bị chia sẻ", `seq − maj3` rò rỉ).
Tỉ lệ prior đúng gần đây: **7/15**.


# Đăng ký trước #66 — H61: **NHÁNH ĐỐI CHỨNG CÒN THIẾU** — H15 (+14) có phải ảo giác không?
**Viết TRƯỚC khi chạy.** Đây là bài kiểm có thể **GIẾT kết quả dương LÂU ĐỜI NHẤT của dự án.**

## Vì sao
H60 (vòng #99): cùng một thí nghiệm cho `V−S` = **+.17** và `V−I` = **−.104**, ngược dấu.
Khác biệt duy nhất là nhánh **I** = *"cứ để model MẠNH tự giải, không cho xem lời giải của model yếu"*.
**H15 chưa bao giờ có nhánh I.** Nó báo cáo 7B-kiểm-1.5B hơn 1.5B **+14 điểm** và tôi đã
diễn giải đó là "kiểm tra có giá trị". Nhưng +14 so với **1.5B** không trả lời được câu hỏi
thật: *có hơn việc gọi thẳng 7B không* — mà gọi thẳng 7B lại còn **RẺ HƠN** (1 lượt thay vì 2).

## Thiết kế — thuần đánh giá, không huấn luyện
GSM8K test 500 bài, greedy, 5 fold × 100. Solver 1.5B (`/root/m15`), Verifier/Solver-mạnh 7B (`/root/m7`), bf16.
| Nhánh | Là gì | Chi phí |
|---|---|---|
| **S** | 1.5B giải | 1×1.5B |
| **V** | 7B ĐƯỢC XEM lời giải của S rồi kiểm/sửa (đúng thiết lập H15) | 1×1.5B + 1×7B |
| **I** | 7B **tự giải, KHÔNG xem gì cả** | **1×7B** ← RẺ HƠN V |

**I rẻ hơn V.** Nên nếu `I ≥ V` thì V bị **áp đảo hoàn toàn** (vừa tệ hơn vừa đắt hơn).

## NGƯỠNG HIỆU LỰC (khoá trước)
- `acc(I) − acc(S)` ≥ **.05**, nếu không thì bất đối xứng không thành ⇒ HUỶ.
- n = 500. Cùng bộ lời giải S cho V (so sánh CẶP).
- Lưu toàn văn cả 3 nhánh.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `V − I` ≥ **+.02** | **Leo thang CÓ giá trị thật.** Đọc lời giải yếu vẫn thêm thông tin ròng dù tốn thêm 1 lượt. H15 ĐỨNG VỮNG. Năng lực đủ lớn thì MIỄN NHIỄM với đầu độc — ghi là biên giới của H60. |
| \|`V − I`\| < .02 | **+14 của H15 là ẢO GIÁC do thiếu đối chứng.** Leo thang không mua được gì so với gọi thẳng 7B, mà lại đắt hơn. Con số +14 giữ nguyên, **DIỄN GIẢI bị RÚT LẠI**. |
| `V − I` ≤ **−.02** | **Leo thang TỆ HƠN việc chỉ dùng 7B, ở chi phí CAO HƠN.** H60 tổng quát qua thang model. Kết quả âm mạnh: định tuyến agent-yếu→agent-mạnh bị áp đảo. |
| `acc(I) − acc(S)` < .05 | HUỶ, không đọc. |

Bắt buộc báo KÈM (bất kể hàng nào): số bài **BỊ ĐẦU ĐỘC** (I đúng→V sai) so với **ĐƯỢC CỨU**
(I sai→V đúng), và trong số bị đầu độc, bao nhiêu là **nhại theo đáp án sai của S** so với
bao nhiêu ra **đáp án THỨ BA** (H60: 46% / 54%).

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 hoặc 3 (~70% gộp)**, vì H60 rất sạch và 5/5 fold. Nhưng để ngỏ **hàng 1 (~30%)**:
7B mạnh hơn 1.5B nhiều, có thể **đủ tự tin để bỏ qua** lời giải kém — trong khi 1.5B thì không.
Nếu vậy thì "đầu độc" là hiện tượng của model YẾU, và đó là một biên giới đáng giá, không phải
kết quả âm. Tỉ lệ prior đúng gần đây: **7/16** (H60 tôi đoán hàng 2, thực tế không hàng nào khớp — tính là SAI).

## BỔ SUNG #66-b — sửa prior TRƯỚC KHI CÓ SỐ H61 (viết trong lúc H61 đang chạy, chưa có kết quả nào)
Đang chờ H61 thì tôi rà lại IDEAS.md và tìm được **bằng chứng có sẵn mà tôi đã quên**, nó
**chống lại** dự đoán tôi vừa ghi ở #66. Ghi lại NGAY, trước khi số về, để không thành hồi tố:

1. **H39 (vòng #78) ĐÃ CÓ nhánh model-mạnh-tự-chạy.** `big_maj3` = .5050 và `big_maj8` = .5400
   là 7B chạy MỘT MÌNH. `escalate_seq` = .6450 hơn cả hai (+.1400 / +.1050) và còn rẻ hơn.
   => **Kết quả leo thang của dự án KHÔNG dính lỗi thiếu đối chứng.** Nó đã được kiểm đúng.
   H61 chỉ nhắm vào cách phát biểu của **H15**, không nhắm vào H39.
2. **Vòng #87/#94 đo THẲNG tác dụng của mỏ neo ở 7B trên TOÁN: ≈ 0** (có neo +.1567 vs
   không neo +.1467, lệch .01; ba trên bốn ô có |A−B| ≤ .01).
   => Ở **7B**, việc bị cho xem lời giải yếu **không** gây hại. Đầu độc −.168 của H60 đo ở **1.5B**.

**Sửa prior:** hàng 1 (leo thang có giá trị thật, 7B miễn nhiễm đầu độc) lên **~55%**,
hàng 2 ~30%, hàng 3 (đầu độc lan sang 7B) xuống **~15%**. Nếu hàng 1 đúng thì kết luận đúng
KHÔNG phải "đầu độc là phổ quát" mà là **"đầu độc là hiện tượng của model YẾU; năng lực đủ lớn
thì miễn nhiễm"** — và ranh giới đó là phát hiện có giá trị hơn một kết quả âm.
Bảng khoá #66 giữ NGUYÊN, không sửa một chữ.


# Đăng ký trước #67 — H62: **ĐẦU ĐỘC CÓ SỬA ĐƯỢC BẰNG CÁCH TRÌNH BÀY KHÔNG?**
**Viết TRƯỚC khi chạy.**

## Câu hỏi
#99/#100 cho thấy *đọc* lời giải yếu tốn **−.074** (7B) / **−.104** (1.5B), và **~50%** thiệt hại
là **đáp án THỨ BA** — tức lập luận bị hỏng, không phải bắt chước. Câu hỏi tiếp theo là câu
**hữu dụng**: thiệt hại đó nằm ở **việc tiếp xúc** (không sửa được) hay ở **cách trình bày**
(sửa được bằng một dòng prompt)?

Nếu bắt model **tự giải XONG rồi mới đọc** lời giải kia, nó đã **cam kết** vào đáp án của mình
trước khi bị neo. Nếu cách đó gỡ được phần lớn −.074 thì đây là một **kết quả DƯƠNG, rẻ, dùng ngay được**.

## Thiết kế — thuần đánh giá, GSM8K test 500, greedy, 7B (`/root/m7`), solver 1.5B (`/root/m15`)
Cùng một bộ lời giải S cho cả ba nhánh V (so sánh CẶP).
| nhánh | prompt | chi phí |
|---|---|---|
| **I** | 7B tự giải, không xem gì | 1×7B |
| **V_std** | "Proposed solution: …" + kiểm/sửa (đúng H61) | 1×1.5B + 1×7B |
| **V_first** | **"Giải bài này một mình TRƯỚC. Viết đáp án của bạn ra. RỒI mới đọc lời giải đề xuất và chốt."** | 1×1.5B + 1×7B |
| **V_label** | như V_std nhưng NÓI RÕ nguồn là model yếu hơn nhiều, chỉ đúng ~2/3, hãy hoài nghi | 1×1.5B + 1×7B |

`V_first` và `V_label` vẫn là **một lượt 7B** → chi phí ngang `V_std`.

## NGƯỠNG HIỆU LỰC (khoá trước)
- Phải tái lập được H61: `V_std − I` ∈ **[−.12, −.03]**. Nếu không, thiết lập đã trôi ⇒ HUỶ, không đọc.
- n = 500, 5 fold, cùng bộ S.
- Báo `poisoned`/`rescued` cho **cả ba** nhánh V.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `V_first − I` ≥ **−.02** VÀ `V_first − V_std` ≥ **+.04** | **ĐẦU ĐỘC SỬA ĐƯỢC BẰNG TRÌNH BÀY.** Bắt reviewer cam kết đáp án của mình TRƯỚC khi đọc là biện pháp một dòng, không tốn thêm lượt. Kết quả DƯƠNG dùng được ngay. |
| `V_first − V_std` ≥ +.02 nhưng `V_first` vẫn < `I` − .02 | Giảm nhẹ được, **không** khử được. Giá tiếp xúc là thật nhưng co lại được. Báo % gỡ lại. |
| \|`V_first − V_std`\| < .02 | **THIỆT HẠI LÀ NỘI TẠI CỦA VIỆC TIẾP XÚC.** Prompt không cứu được. Đây là bản mạnh nhất của #99/#100. |
| `V_label` > `V_first` | Điều quan trọng là **HOÀI NGHI NGUỒN**, không phải **thứ tự cam kết**. Ghi rõ, đảo lại lời giải thích. |
| `V_label` < `V_std` − .02 | Nói "nguồn này yếu" khiến nó **can thiệp bừa** → phá cả bài đúng. |
| `V_std − I` ngoài [−.12,−.03] | HUỶ, không đọc. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 (~50%)**: gỡ được một phần (tôi đoán 40–70% của khoảng cách) nhưng không hết,
vì **~45–54% thiệt hại là "đáp án thứ ba"** — nghĩa là ngay cả khi không bị dụ chép, việc đọc
vẫn làm nhiễu. Hàng 1 ~25%, hàng 3 ~25%.
**Lưu ý về chính tôi:** hai lần gần nhất tôi đoán sai, và lần #66-b tôi còn tự tin sửa prior
theo hướng sai. Tỉ lệ prior đúng: **7/17**. Đừng tin prior này quá.


# Đăng ký trước #68 — H63: **REFACTOR bằng CHỌN LỌC, không phải SỬA CHỮA**
**Viết TRƯỚC khi chạy.** Nguyên hỏi lại về refactor.

## Vì sao đúng là phép thử còn thiếu
Quy tắc dương DUY NHẤT tái lập được của dự án (#95/#96/#97): **oracle nên LỌC ứng viên,
đừng SỬA một ứng viên** — trên MBPP, dùng test để **CHỌN** trong 8 mẫu = **+.0401** (tái lập +.0388),
còn dùng oracle để **SỬA** = **+.004**. Gấp **10 lần**.
Trên refactor, H53 đã thử **SỬA** (`ref_exec3`, tối đa 3 vòng, dùng TB 2.70 vòng): chỉ **+1.9 điểm**.
**CHỌN LỌC thì CHƯA AI THỬ trên refactor.**

Refactor hợp với chọn lọc hơn cả sinh code, vì có **HAI** tín hiệu tự động, không cần LLM phán xét:
1. `preserve` — bộ test trả lời CHÍNH XÁC (oracle hành vi),
2. `simpler` — **đếm nút AST**, khách quan hoàn toàn.
=> chọn lọc **hoàn toàn tự động**: lọc theo (1), xếp hạng theo (2).

Refactor cũng là tác vụ **DUY NHẤT** mà phê phán ở #100 không áp dụng: **không thể refactor mà
không đọc code** — tiếp xúc là ĐỊNH NGHĨA của tác vụ, nên không tồn tại nhánh `I`.

## Dữ liệu & nhánh (BigCodeBench, 7B bf16 trên 5090, lọc như H52: chỉ giữ bài mà lời giải chuẩn ĐẠT test)
| nhánh | mô tả | chi phí |
|---|---|---|
| `ref1` | refactor 1 lượt, greedy (tái lập H52/H53) | 1 |
| `ref_exec3` | refactor → chạy test → sửa theo stderr, tối đa 3 vòng (tái lập H53) | ≤4 |
| **`ref_sel8`** | **sinh 8 bản refactor (T=0.8) → chạy test cả 8 → trong số ĐẠT, chọn bản ÍT NÚT AST NHẤT** | 8 |
| `ref_sel8_first` | như trên nhưng chọn bản ĐẠT **ĐẦU TIÊN** (đối chứng: lợi ích đến từ LỌC hay từ XẾP HẠNG?) | 8 |
| *(gốc)* | không refactor: `preserve` = 1.000, `simpler` = 0 | 0 |

`ref_sel8_first` là đối chứng quan trọng: tách **"có ứng viên nào sống sót"** khỏi
**"chọn được ứng viên tốt nhất"**.

## Thước đo — GIỮ NGUYÊN định nghĩa #58, không đổi một chữ
`preserve` (đạt test) · `simpler` (giảm nút AST, **chỉ tính trên bài preserve**) ·
**`good_refactor` = preserve ∧ simpler** ← thước đo CHÍNH.

## NGƯỠNG HIỆU LỰC (khoá trước)
- n ≥ 250 sau lọc · tỉ lệ đọc được AST ≥ .80.
- **Cổng tái lập**: `preserve(ref1)` ∈ [.70, .79] (H52 .7406, H53 .7378). Ngoài khoảng ⇒ HUỶ.
- Báo `preserve` KÈM `good_refactor` — **không được báo `preserve` một mình**, vì
  "không refactor gì cả" đạt `preserve` = 1.000. `preserve` cao mà `simpler` thấp là VÔ GIÁ TRỊ.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `good(sel8) − good(ref_exec3)` ≥ **+.08** | **CHỌN LỌC THẮNG SỬA CHỮA TRÊN REFACTOR.** Quy tắc "lọc, đừng sửa" tổng quát từ SINH sang BIẾN ĐỔI code. Kết quả dương thứ hai của dự án trên code. Phải nêu chi phí 8× và so với `ref1`×8 công bằng. |
| +.02 ≤ chênh < +.08 | Chọn lọc hơn sửa chữa nhưng **khiêm tốn**; nêu rõ chi phí 8 lượt so với ≤4 lượt của `exec3`. |
| \|chênh\| < .02 | **Chọn lọc KHÔNG tổng quát sang refactor.** Quy tắc #95 bị thu hẹp: chỉ đúng cho SINH code. Nút thắt refactor là **năng lực giữ ngữ nghĩa**, không phải chọn ứng viên. |
| `good(sel8) < good(ref_exec3)` − .02 | Chọn lọc TỆ HƠN sửa chữa. Ghi rõ, rút hướng này. |
| `good(sel8) − good(sel8_first)` < .02 | Lợi ích đến từ **LỌC** (có bản nào sống sót), không từ **XẾP HẠNG** theo độ đơn giản. Quan trọng: nghĩa là chỉ cần test, không cần thước đo "tốt hơn". |
| `preserve(sel8)` < .90 | Đáng ngạc nhiên: 8 mẫu mà vẫn không bản nào giữ được hành vi ở >10% số bài ⇒ giới hạn NĂNG LỰC, không phải giới hạn tìm kiếm. Ghi thẳng. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 (~50%)**. Lý do số học: `ref1` giữ được hành vi .74; nếu 8 mẫu độc lập gần như
độc lập thì `preserve(sel8)` phải rất cao (~.95+), và trong số đó chọn bản đơn giản nhất trong
nhiều bản làm `simpler` tăng mạnh. `good` có thể từ .2434 lên **.45–.60**.
**Rủi ro tôi thấy trước**: các mẫu có thể **tương quan cao** — model hỏng cùng một kiểu ở cùng
những bài, nên 8 mẫu không cho 8 cơ hội thật. Nếu vậy ra hàng 3, và đó cũng là phát hiện tốt.
Hàng 2 ~25%, hàng 3 ~20%. Tỉ lệ prior đúng: **8/18**.


# Đăng ký trước #69 — H64: **LẬP KẾ HOẠCH CÓ ĐÁNG KHÔNG KHI SẢN PHẨM ĐỦ DÀI?**
**Viết TRƯỚC khi chạy.** Nguyên: *"what about a long coding task? it will really need planner, other role."*

## Vì sao đây là ô còn trống — và vì sao bằng chứng cũ KHÔNG kết luận được
| bằng chứng | nói gì |
|---|---|
| H32 (lưới 4 ô) | `PSV` **thắng** `maj@3` ở **3/4 ô**, tái lập trên hai phần cứng |
| cùng H32 | `SS_anc` (**cùng số lượt, KHÔNG có chữ nào về vai**) − `PSV` = **+.020** ⇒ **hoà** |
| vòng #87 | mỏ neo đóng góp **≈ 0** trên toán ⇒ không phải mỏ neo giải thích |

=> Trên bài NGẮN, "lập kế hoạch" **không phân biệt được với việc chỉ thêm một lượt**.
GSM8K = một câu · MBPP = ~3 dòng · BigCodeBench = lời giải chuẩn **414 ký tự**.
**Chưa bao giờ có tác vụ đủ dài để một kế hoạch có việc mà làm.**

## Dữ liệu: ClassEval (`FudanSELab/ClassEval`)
100 lớp · **4.1 method/lớp**, phụ thuộc lẫn nhau · lời giải TB **1334 ký tự**
(**3.2× BigCodeBench**) · có test chạy được ở **cả cấp method lẫn cấp lớp**.
=> **410 method** làm đơn vị đo ⇒ độ phân giải cao hơn con số n=100 gợi ý.

## Nhánh — KHOÁ CỨNG NGÂN SÁCH 3 LƯỢT cho hai nhánh chính
| nhánh | lượt | có ngôn ngữ VAI? |
|---|---|---|
| `solve1` | 1 | không (mốc tham chiếu) |
| **`seq3`** | 3: giải → sửa lại → sửa lại | **KHÔNG** |
| **`PSV`** | 3: **lập kế hoạch** → giải theo kế hoạch → tự kiểm | **CÓ** |

**Đại lượng CHÍNH = `PSV − seq3`.** Cùng model, cùng số lượt, cùng ngân sách token.
Khác **đúng một điều**: lượt đầu dùng để **LẬP KẾ HOẠCH** hay để **GIẢI**.
(Đây là contrast đã dùng ở H49; điều mới là **ĐỘ DÀI SẢN PHẨM**.)

## PHÉP THỬ QUYẾT ĐỊNH: **ĐÁP ỨNG THEO LIỀU** (dose-response)
Chia 100 lớp thành **3 nhóm ba** theo độ dài lời giải chuẩn. Tính `PSV − seq3` **trong từng nhóm**.
> Nếu lập kế hoạch có giá trị THẬT vì sản phẩm dài, lợi ích **PHẢI TĂNG** theo nhóm.
> **Đường phẳng thì giả thuyết "bài quá ngắn" CHẾT**, dù trung bình có dương hay không.

## Thước đo (khoá trước)
1. **`method_pass`** = tỉ lệ method qua test (410 đơn vị) ← **CHÍNH**
2. `class_pass` = cả lớp qua toàn bộ test ← phụ
3. `plan_is_code_rate` ≤ .20 (kế hoạch phải là văn xuôi; nếu là code thì "lập kế hoạch" chỉ là giải sớm) ⇒ >.20 thì HUỶ nhánh PSV

## NGƯỠNG HIỆU LỰC (khoá trước)
- `class_pass(solve1)` ∈ **[.10, .60]** — ngoài khoảng là sàn/bão hoà ⇒ HUỶ, không đọc.
- tỉ lệ đọc được AST ≥ .80 · n = 100 lớp / 410 method.
- Báo `method_pass` KÈM `class_pass` — không được báo một mình.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `PSV − seq3` ≥ **+.05** VÀ tăng đều theo 3 nhóm dài | **LẬP KẾ HOẠCH ĐÁNG GIÁ KHI SẢN PHẨM ĐỦ DÀI.** Giả thuyết của Nguyên ĐÚNG: các vòng trước đo trên bài quá ngắn nên không thấy. Vai Planner CÓ THẬT, có điều kiện kích hoạt là **độ dài**. |
| `PSV − seq3` ≥ +.05 nhưng **PHẲNG** theo nhóm | Lập kế hoạch giúp, nhưng **KHÔNG PHẢI vì độ dài**. Phải tìm cơ chế khác; không được nói "vì bài dài". |
| \|`PSV − seq3`\| < .05 | **LẬP KẾ HOẠCH VẪN KHÔNG THÊM GÌ, kể cả ở 3.2× độ dài.** Vai Planner không phải một vai — thứ có tác dụng là **SỐ LƯỢT**. Bản mạnh nhất của kết quả âm; khép lại hướng phân vai bằng prompt. |
| `PSV < seq3 − .05` | Lập kế hoạch **có hại** trên bài dài (kế hoạch sai khoá chặt lời giải). Ghi rõ. |
| `class_pass(solve1)` ngoài [.10,.60] | HUỶ, không đọc. |
| `plan_is_code_rate` > .20 | Nhánh PSV không hợp lệ: "kế hoạch" thực chất là code. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 3 (~50%)**: mọi vai không-oracle đều đã thất bại (H35 `llm3`, #90 PSV, #91, #92 `ref_seq`,
H59/H60 verifier). Nhưng hàng 1 **~30%** là thật, cao hơn tôi từng cho bất kỳ vai nào — vì đây là
lần ĐẦU TIÊN sản phẩm đủ dài để một kế hoạch có nội dung để mang, và vì **H60/H61 cho thấy
đọc văn xuôi của agent khác là ĐỘC** — kế hoạch là văn xuôi của CHÍNH nó, nên có thể thoát.
Hàng 2 ~10%, hàng 4 ~10%. Tỉ lệ prior đúng: **8/18**.

## BỔ SUNG #69-b — LỌC THEO LỜI GIẢI CHUẨN (viết TRƯỚC khi chạy, chưa có số nào của H64)
Chạy thử bộ chấm tại chỗ trên 30 lớp đầu: **lời giải CHUẨN chỉ đạt 109/118 = .9237**.
Chín method trượt là do **môi trường**, không do bộ chấm: `BookManagementDB` (cần file sqlite),
`CookiesUtil` (đọc/ghi file), `CalendarUtil.get_upcoming_events` (phụ thuộc `datetime.now`).

Để nguyên thì **trần của MỌI nhánh bị hạ xuống ~.92** và các lớp phụ thuộc môi trường sẽ
làm nhiễu phép so sánh — đúng loại lỗi đã ghi ở #58/H52.

**Áp dụng đúng bộ lọc của H52:** chạy `solution_code` qua bộ chấm **NGAY TRONG KERNEL**,
và **chỉ tính điểm trên những method mà lời giải chuẩn ĐẠT**. Trần trở lại 1.0 cho mọi nhánh.
- Bộ lọc **giống hệt nhau cho cả ba nhánh** ⇒ không ưu ái nhánh nào.
- `n` được xác định trong kernel và **phải báo cáo**.
- **Ngưỡng mới thay cho "410 method"**: `n_method` sau lọc **≥ 350** và `n_class` **≥ 80**,
  nếu không ⇒ HUỶ. Nhóm ba theo độ dài chia trên tập ĐÃ LỌC.

Mọi phần còn lại của #69 giữ NGUYÊN, không sửa một chữ.


# Đăng ký trước #70 — H65: **ĐẦU ĐỘC CÓ TAN BIẾN THEO NĂNG LỰC KHÔNG?** (14B)
**Viết TRƯỚC khi chạy.** Nguyên đề nghị lên 14B; chạy trên Kaggle RTX 6000 Pro (102 GB).

## Câu hỏi — điểm thứ BA của một đường đã có hai điểm
| verifier ← solver | tỉ lệ năng lực | `V − I` | nguồn |
|---|---|---|---|
| 1.5B ← 0.5B | 3× | **−.1040** | H60 (#99) |
| 7B ← 1.5B | 4.7× | **−.0740** | H61 (#100) |
| **14B ← 1.5B** | **9.3×** | **?** | H65 |

Hai điểm đã có đều **n=500, hiệu ứng .07–.10**, 5/5 fold — **KHÔNG** phải loại nhiễu như
đáp ứng-theo-liều hỏng ở #102 (5 method/354). Điểm thứ ba phân định hai thế giới rất khác nhau:
**đầu độc là hiện tượng của model YẾU và tan dần theo năng lực**, hay **nội tại của việc đọc
văn xuôi model khác và chững lại quanh −.07**.

## VÌ SAO ĐỔI SANG MATH-500, KHÔNG DÙNG GSM8K
7B **một mình** đã đạt **.908–.934** trên GSM8K (H61/H62). 14B sẽ ~.95 ⇒ **mọi nhánh bị nén vào trần**,
đo được là TRẦN chứ không phải hiệu ứng. MATH-500: 7B ≈ .49 (H45) ⇒ còn dư địa thật.
**Hệ quả phải chấp nhận:** điểm 7B sẽ được đo LẠI trên MATH nên **không so trực tiếp** với −.0740
của GSM8K. Trong H65, cả ba điểm nằm trên **CÙNG một benchmark** ⇒ so sánh nội bộ là hợp lệ.
Điểm 7B trên MATH cũng là **tái lập trên benchmark khác** của chính hiện tượng.

## Thiết kế — Solver CỐ ĐỊNH, chỉ đổi năng lực Verifier
Ba model cùng nạp bf16 trên một card 102 GB (1.5B 3 GB + 7B 15 GB + 14B 29 GB = 47 GB).
**Không lượng tử hoá** ⇒ tránh đúng chuỗi lỗi gói đã giết H54 (`autoawq`/`gptqmodel`/numpy ABI).

- `S` = **1.5B** giải, greedy — dùng CHUNG cho mọi nhánh V (so sánh CẶP)
- với mỗi M ∈ {1.5B, 7B, 14B}: `I_M` = M **tự giải** · `V_M` = M **xem lời giải của S** rồi kiểm/sửa
- `poisoning(M)` = `acc(V_M) − acc(I_M)`
- `I_1.5B` ≡ `S` (cùng model, cùng prompt, cùng greedy) — **dùng lại, không sinh hai lần**

Chấm: lấy `\boxed{}`. **Gold lấy từ `\boxed{}` trong cột `Answer` của CSV Kaggle — đã kiểm tại chỗ:
500/500 bài có `\boxed`, gold trung vị 3 ký tự, 0 rỗng.** (Lỗi cũ ở vòng trước là so cả chuỗi
lời giải với đáp án ⇒ 0/500; nay so `\boxed` với `\boxed`.)

## NGƯỠNG HIỆU LỰC (khoá trước)
- `acc(S)` ∈ **[.10, .55]**.
- **`acc(I_14B) − acc(I_7B)` ≥ .05** — 14B phải THẬT SỰ mạnh hơn trên benchmark này, nếu không
  thì "thêm năng lực" không xảy ra ⇒ **HUỶ, không đọc**.
- `acc(I_7B) − acc(S)` ≥ .05.
- n = 500 · báo 5 fold · lưu toàn văn cả ba nhánh.

## Bắt buộc báo KÈM (bất kể hàng nào) — cho TỪNG mức năng lực
số **bị đầu độc** (I đúng→V sai) vs **được cứu**; trong số bị đầu độc, bao nhiêu **nhại đáp án
sai của S** vs bao nhiêu ra **đáp án THỨ BA** (H60: 46/54 · H61: 55/45).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `poisoning(14B)` ≥ **−.02** VÀ \|đầu độc\| giảm đều theo 1.5B→7B→14B | **ĐẦU ĐỘC TAN THEO NĂNG LỰC.** Là hiện tượng của model yếu. Thực tiễn: định tuyến lên model đủ mạnh là AN TOÀN. Nêu rõ 14B vẫn là model nhỏ, không suy ra được cho model biên. |
| `poisoning(14B)` ∈ [−.05, −.02) VÀ giảm đều | Co lại theo năng lực nhưng **CHƯA hết**. Ngoại suy tuyến tính cho ra mức năng lực hoà vốn; ghi rõ đó là ngoại suy, không phải đo. |
| \|`poisoning(14B)`\| ≥ **.05** HOẶC không giảm đều | **ĐẦU ĐỘC LÀ NỘI TẠI, không rửa được bằng năng lực.** Bản mạnh nhất của #99–#101: đọc văn xuôi của agent yếu hại ròng ở mọi thang đã đo. |
| `poisoning(14B)` > **+.02** | Đảo dấu: ở 14B việc đọc lời giải yếu **có ích**. Ghi rõ và tìm ngưỡng năng lực đảo dấu. |
| `acc(I_14B) − acc(I_7B)` < .05 | HUỶ, không đọc. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 (~45%)**: co lại còn khoảng −.03..−.04, chưa về 0 — vì hai điểm đã có
(−.104 → −.074) giảm **chậm** so với mức tăng năng lực (3×→4.7×), và vì **54%/45% thiệt hại là
"đáp án thứ ba"**, tức nhiễu lập luận chứ không phải bắt chước, thứ mà năng lực khó xoá hẳn.
Hàng 1 ~20%, hàng 3 ~30%, hàng 4 ~5%.
**Cảnh báo về chính tôi:** ở #102 tôi đã khoá một phép thử đáp ứng-theo-liều **thiếu lực**.
Lần này hiệu ứng lớn gấp ~15 lần và n=500/điểm, nhưng vẫn chỉ có **BA điểm** — không được
vẽ đường xu hướng rồi ngoại suy như thể đó là phép đo. Tỉ lệ prior đúng: **9/19**.

## BỔ SUNG #70-b — RTX 6000 Pro KHÔNG CÒN; chuyển 2×T4 + nf4 (viết TRƯỚC khi chạy lại, chưa có số nào)
Lần chạy đầu **HỎNG VÌ HẠ TẦNG, không phải vì khoa học**: kernel nhận **Tesla P100 sm_60**
-> `no kernel image available` (torch hỗ trợ sm_70+).

**Nguyên nhân — KHÔNG phải metadata của tôi.** Kaggle ghi nhận đủ cả ba trường
(`machine_shape` / `enable_gpu` / `competition_sources`), và `zhongzhing` **đã tham gia** competition.
Nhưng **competition `nvidia-nemotron-model-reasoning-challenge` đã ĐÓNG hạn 2026-06-15**, tức
**hai tháng trước**. Suất tính toán RTX 6000 Pro đi kèm competition đó **đã hết hiệu lực**:
Kaggle vẫn nhận liên kết nhưng **âm thầm cấp P100**. Cổng ba trường trong `KAGGLE_RTX6000.md`
đúng khi competition còn mở; **nay KHÔNG còn đúng**. Không có competition đang mở nào cấp lại.

## Thay đổi: 1.5B fp16 · 7B nf4 · 14B nf4, hai bản sao trên 2×T4 (data parallel)
**Vì sao lượng tử hoá KHÔNG phá phép đo chính:** `poisoning(M) = acc(V_M) − acc(I_M)` là đại lượng
**GHÉP CẶP TRONG CÙNG MỘT MODEL** — hai nhánh dùng **y hệt** bộ trọng số. nf4 hạ **mức tuyệt đối**
của cả `I_M` lẫn `V_M` như nhau nên **triệt tiêu trong hiệu**. Đây khác hẳn việc so giữa các model.

**Hạn chế PHẢI ghi rõ (bất lợi cho chính giả thuyết của tôi):** nf4-14B có năng lực hữu hiệu
thấp hơn bf16-14B (ước lượng thô: ~bf16-13B). Trục năng lực vì thế bị **NÉN NHẸ**, nên nếu
kết quả ra "đầu độc chưa tan" thì một phần có thể do 14B-nf4 chưa đủ mạnh. **Không được kết luận
"năng lực không cứu được" một cách tuyệt đối từ dữ liệu này** — chỉ được nói tới mức năng lực ĐÃ ĐO.
Ngược lại nếu ra hàng 1 (đầu độc tan) thì kết luận **mạnh hơn**, vì đạt được dù model bị nén.

Cổng `acc(I_14B) − acc(I_7B)` ≥ .05 **giữ nguyên** và chính là cái bắt lỗi này: nếu nf4 nén 14B
tới mức không hơn 7B đủ .05 thì **HUỶ**, không đọc. Mọi phần còn lại của #70 giữ NGUYÊN.


# Đăng ký trước #71 — H66: **ĐẦU ĐỘC CÓ XẢY RA TRÊN CODE KHÔNG?**
**Viết TRƯỚC khi chạy.**

## Vì sao
#99–#101 đo đầu độc **chỉ trên TOÁN** (GSM8K). Chưa biết nó có phải hiện tượng riêng của toán
hay của **giao tiếp bằng ngôn ngữ** nói chung. Code là phép thử tốt nhất vì **có oracle thật**
(chạy test) nên không phụ thuộc bộ chấm.

Manh mối cũ, **KHÁC câu hỏi**: H44/H47 đo *mỏ neo-có vs mỏ neo-không* trên code = **−.0800 / −.0981**
— nhưng cả hai nhánh đều là pipeline nhiều lượt của **cùng** model. **Chưa ai đo `V − I` trên code.**

## Thiết kế — y hệt H61, đổi task
MBPP 11–510 (498 bài, có test). 7B nf4, greedy.
| nhánh | là gì | chi phí |
|---|---|---|
| `S` | **1.5B** viết code | 1×1.5B |
| **`I`** | **7B tự viết, KHÔNG xem gì** | **1×7B** ← RẺ HƠN V |
| `V` | 7B xem code của S rồi kiểm/sửa | 1×1.5B + 1×7B |

Chấm: `pass` = qua toàn bộ assert đi kèm. **`I` rẻ hơn `V`** ⇒ `I ≥ V` là **áp đảo hoàn toàn**.

## NGƯỠNG HIỆU LỰC (khoá trước)
`acc(I) − acc(S)` ≥ .05 · tỉ lệ biên dịch được ≥ .50 · n ≥ 400.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `V − I` ≤ **−.02** | **ĐẦU ĐỘC TỔNG QUÁT SANG CODE.** Không phải hiện tượng của toán mà của **việc đọc sản phẩm agent yếu**. Cùng với #99/#100 thành ba task, ba cặp model. |
| \|`V − I`\| < .02 | **Đầu độc KHÔNG tổng quát sang code.** Phải thu hẹp #99–#101 về "trên toán". Tìm cái gì khác nhau: code có oracle nội tại (chạy được), văn xuôi toán thì không. |
| `V − I` ≥ **+.02** | Trên code, đọc code yếu **CÓ ÍCH** — ngược dấu với toán. Kết quả mạnh, phải nêu vì sao code khác. |
| `acc(I) − acc(S)` < .05 | HUỶ. |

Báo KÈM: `poisoned`/`rescued`, và trong số bị đầu độc bao nhiêu **giữ nguyên code sai của S**
(tương đương "nhại") vs bao nhiêu **viết ra bản thứ ba vẫn sai**.

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 (~65%)** — mạnh hơn mọi prior gần đây, vì mỏ neo trên code đã đo là **có hại**
(−.08/−.098) trong khi trên toán là ≈0, nên `V−I` trên code có lẽ **ÂM HƠN** toán, không nhẹ hơn.
Hàng 2 ~25%, hàng 3 ~10%. Tỉ lệ prior đúng: **9/19**.


# Đăng ký trước #72 — H67: **TRÊN CODE, THUỐC CHỮA PHẢI KHÁC** — vì bệnh khác
**Viết TRƯỚC khi chạy.** Suy ra thẳng từ cơ chế đo được ở #103.

## Lập luận (ghi trước, để có thể SAI công khai)
H62 trên **toán**: `V_first` (tự giải & cam kết TRƯỚC khi đọc) gỡ **40.4%** thiệt hại —
nhưng phân tích cơ chế cho thấy nó **giết NHẠI LẠI** (36→15) mà **không đụng** được "đáp án thứ ba" (21→23).
H66 trên **code**: thiệt hại **78% là bản THỨ BA**, chỉ **22%** là giữ code sai.
=> **`V_first` phải KÉM hiệu quả trên code**, vì nó chữa đúng cái phần code hầu như không có.

Thứ code cần là chặn **VIẾT LẠI**: model mạnh bị đẩy vào *chế độ sửa chữa* và sửa kém hơn tự viết
(`I` .6400 vs `V` .5660). Nên thuốc phải là **"đừng đụng vào nếu không chắc chắn sai"**.

## Nhánh — MBPP 11–510, 1.5B viết, 7B nf4 kiểm, greedy, cùng một bộ code của S
| nhánh | prompt | chi phí |
|---|---|---|
| `I` | 7B tự viết, không xem gì | 1×7B |
| `V_std` | "Proposed code: …" + kiểm/sửa (tái lập H66) | 1×1.5B+1×7B |
| `V_first` | tự viết lời giải của mình TRƯỚC, rồi mới đọc code kia và chốt | 1×1.5B+1×7B |
| **`V_cons`** | **"Chạy thử code trong đầu với các test đã cho. Nếu nó ĐÚNG, trả về NGUYÊN VĂN không đổi một ký tự. CHỈ sửa phần chứng minh được là sai."** | 1×1.5B+1×7B |

## NGƯỠNG HIỆU LỰC (khoá trước)
Tái lập H66: `V_std − I` ∈ **[−.12, −.03]**, ngoài khoảng ⇒ HUỶ. Biên dịch ≥ .50. n = 500.
Báo KÈM cho mỗi nhánh: `poisoned`/`rescued`, **tỉ lệ trả về NGUYÊN VĂN code của S** (`unchanged_rate`),
và tách nhại/bản-thứ-ba.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `V_cons − V_std` ≥ **+.04** VÀ `V_cons − V_first` ≥ **+.02** | **CƠ CHẾ ĐƯỢC XÁC NHẬN: bệnh khác thì thuốc khác.** Trên toán chữa bằng *cam kết trước khi đọc*; trên code chữa bằng *đừng viết lại*. Suy luận từ #103 đúng. |
| cả hai nhánh gỡ ≥ +.04, chênh nhau < .02 | Hai can thiệp **không phân biệt được**; thiệt hại không đặc thù "viết lại". Lập luận của tôi SAI ở phần cơ chế dù kết quả vẫn dương. |
| `V_cons − V_std` < +.02 | **Trình bày KHÔNG cứu được đầu độc trên code** (trái với toán, gỡ 40–49%). Code nặng hơn: phải bỏ hẳn kiểu định tuyến này trên code. |
| `V_cons` ≥ `I` − .02 | Chữa được **gần hết**: bảo model đừng đụng vào là đủ. Nêu rõ khi đó `V` chỉ còn *bằng* `I` mà vẫn **đắt hơn** ⇒ vẫn nên gọi thẳng model mạnh. |
| `unchanged_rate(V_cons)` < .20 | Can thiệp **KHÔNG xảy ra** (model vẫn viết lại dù bị bảo đừng) ⇒ nhánh không hợp lệ, không đọc như bằng chứng về cơ chế. |
| `V_std − I` ngoài [−.12,−.03] | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 (~55%)**. Lý do: cơ chế ở #103 rất rõ (78% là viết lại) và can thiệp nhắm đúng nó.
Rủi ro thấy trước: model có thể **không nghe lời** — bảo "đừng đổi" nhưng vẫn đổi (nên có cổng
`unchanged_rate`). Hàng 2 ~15%, hàng 3 ~25%, hàng 4 ~5%. Tỉ lệ prior đúng: **10/20**.


# Đăng ký trước #73 — H68: **ĐỘC VÌ LÀ CỦA AGENT YẾU, HAY ĐỘC VÌ Ở CHẾ ĐỘ SỬA CHỮA?**
**Viết TRƯỚC khi chạy.** Đây là **ĐỐI CHỨNG CÒN THIẾU của chính câu chuyện đầu độc.**

## Lỗ hổng trong lập luận của tôi
#99–#103 đều so `V` (model mạnh **xem sản phẩm của agent YẾU**) với `I` (model mạnh **tự làm**).
Tôi đã diễn giải hiệu số âm là *"đọc văn xuôi của agent yếu gây hại"*.
**Nhưng hai nhánh khác NHAU HAI THỨ cùng lúc:**
1. có/không **được xem sản phẩm của MODEL KHÁC**, và
2. ở **chế độ SỬA CHỮA** vs chế độ **SÁNG TÁC**.

Ở #103 tôi còn tự viết: *"bị cho xem lời giải kém đẩy model vào chế độ sửa chữa, và nó sửa kém hơn
sáng tác"*. **Nếu điều đó đúng thì thủ phạm là CHẾ ĐỘ, không phải NGUỒN** — và toàn bộ cách gọi
"đầu độc" (ngụ ý lỗi ở agent yếu) là **SAI TÊN**. Phải tách ra.

## Thiết kế — MBPP 11–510, 7B nf4, greedy, tách ĐÚNG một biến
| nhánh | 7B được xem gì | chế độ | lượt |
|---|---|---|---|
| `I` | không xem gì | sáng tác | 1×7B |
| **`V_self`** | **code của CHÍNH NÓ** (sinh ở lượt 1) | **sửa chữa** | 2×7B |
| `V_weak` | code của **1.5B** (tái lập H66) | sửa chữa | 1×1.5B + 1×7B |

`V_self` và `V_weak` **cùng chế độ sửa chữa, cùng prompt REVIEW**, khác **đúng một điều**:
code đem vào là **của chính nó** hay **của model yếu**.

## NGƯỠNG HIỆU LỰC (khoá trước)
Tái lập H66: `V_weak − I` ∈ **[−.12, −.03]** ⇒ ngoài khoảng thì HUỶ. Biên dịch ≥ .50. n = 500.
Báo KÈM: `poisoned`/`rescued` và `unchanged_rate` cho **cả hai** nhánh V.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `V_self − I` ≤ −.03 VÀ \|`V_self − V_weak`\| < .03 | **THỦ PHẠM LÀ CHẾ ĐỘ SỬA CHỮA, KHÔNG PHẢI NGUỒN.** Tên gọi "đầu độc" SAI và phải **RÚT LẠI cách diễn giải** ở #99–#103 (số giữ nguyên). Phát biểu đúng: *bất kỳ lượt sửa chữa nào cũng hại, dù sửa code của chính mình.* Hệ quả thực tiễn còn MẠNH HƠN: đừng thêm lượt review, chấm hết. |
| `V_self` ≈ `I` (\|Δ\| < .02) VÀ `V_weak − I` ≤ −.03 | **NGUỒN mới là thủ phạm.** Sửa code của chính mình thì vô hại; sửa code model yếu thì hại. Câu chuyện đầu độc ở #99–#103 **ĐỨNG VỮNG** và nay có đối chứng chặt. |
| cả hai âm nhưng `V_weak` âm hơn `V_self` ≥ .03 | **CẢ HAI đều góp**: chế độ sửa chữa hại một phần, nguồn ngoại lai hại thêm. Báo tách phần đóng góp của từng cái. |
| `V_self − I` ≥ +.02 | Tự review CÓ ÍCH trên code (trái #92 `ref_seq`). Kết quả bất ngờ, phải tái lập trước khi tin. |
| `V_weak − I` ngoài [−.12,−.03] | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 3 (~45%)**: cả hai đều âm, `V_weak` âm hơn. Vì (a) #92 đã đo `ref_seq` (tự nhận xét)
**làm refactor tệ đi**, và H35 `llm3` ≈ 0 — nên chế độ sửa chữa tự nó đã hại; nhưng (b) H66 cho
thấy 78% thiệt hại là **viết lại**, mà code của chính mình thì ít lý do viết lại hơn.
Hàng 1 ~25%, hàng 2 ~25%, hàng 4 ~5%.
**Tôi sẽ phải rút lại cách diễn giải của bốn vòng nếu ra hàng 1 — và đó là lý do PHẢI chạy.**
Tỉ lệ prior đúng: **10/20**.


# Đăng ký trước #74 — H69: **CÙNG HAI BẢN CODE — CHỌN thay vì REVIEW**
**Viết TRƯỚC khi chạy.** Đây là phép thử **tổng hợp** hai kết quả lớn của dự án.

## Vì sao — đã tính sẵn TRẦN từ trace H66 (miễn phí, trước khi chạy)
Trên đúng 500 bài của H66:
| | số bài |
|---|---|
| chỉ `I` (7B) đúng | 128 |
| **chỉ `S` (1.5B) đúng — 7B TRƯỢT** | **22** |
| cả hai đúng | 192 |
| cả hai sai | 158 |

`acc(I)` = .6400 · `acc(S)` = .4280 · **HỢP = .6840** · `acc(V_review)` = .5660.
=> Code của agent yếu **CÓ giá trị thật**: nó giải được **22 bài** mà 7B trượt.
**Trần của việc CHỌN = +.0440 so với `I`, và +.1180 so với REVIEW.**
Giao thức review đang **phá** đúng cái nó lẽ ra phải thu.

## Thiết kế — MBPP 11–510, cùng bộ `S`/`I`, 7B nf4
| nhánh | là gì | chi phí |
|---|---|---|
| `I` | 7B tự viết | 1×7B |
| `V_review` | 7B review code của S (tái lập H66) | 1×1.5B+1×7B |
| **`SEL`** | 7B **tự viết test**, chạy test lên **CẢ HAI** bản (`I` và `S`), **CHỌN** bản qua nhiều test hơn (hoà → giữ `I`) | 1×1.5B+2×7B |
| `ORACLE2` | chọn đúng bằng test chính thức (chỉ để báo TRẦN, **không** phải nhánh cạnh tranh) | — |

## CHỐNG RÒ RỈ — bắt buộc, đây là chỗ tôi đã sai một lần và phải rút lại
MBPP đưa `test_list` **ngay trong đề**, và `test_list` **chính là bộ chấm**. Dùng nó để chọn là
**RÒ RỈ** (đúng lỗi `maj3` trên BigCodeBench đã phải rút lại ở vòng trước).
- Lượt **viết test** chỉ nhận `text` (mô tả), **KHÔNG** nhận `test_list`.
- Chấm **luôn luôn** bằng `test_list` chính thức.
- **Cổng `test_copy_rate`** = tỉ lệ assert tự sinh trùng **nguyên văn** (sau chuẩn hoá khoảng trắng)
  với `test_list`. **> .20 ⇒ HUỶ nhánh SEL**, coi như rò rỉ, không đọc.
- Báo `test_soundness` = tỉ lệ test tự sinh mà **lời giải chuẩn** MBPP vượt qua.

## NGƯỠNG HIỆU LỰC (khoá trước)
Tái lập H66: `V_review − I` ∈ [−.12,−.03] ⇒ ngoài thì HUỶ. Biên dịch ≥ .50. n = 500.
`test_soundness` ≥ .50 (test quá sai thì chọn vô nghĩa).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL − I` ≥ **+.02** | **CHỌN thu được giá trị mà REVIEW phá.** Cùng hai bản code, cùng chi phí một lượt thêm: chọn hơn review ~.10. Đây là **giao thức thay thế dùng được ngay** cho định tuyến yếu→mạnh. |
| `SEL − V_review` ≥ **+.05** nhưng `SEL − I` < +.02 | Chọn **hơn hẳn** review nhưng **không hơn** việc chỉ gọi model mạnh. Kết luận: sản phẩm agent yếu vẫn không đáng lấy — nhưng nếu buộc phải dùng thì CHỌN, đừng REVIEW. |
| \|`SEL − V_review`\| < .05 | Chọn **không** hơn review ⇒ vấn đề không nằm ở giao thức mà ở **chất lượng phân biệt** của test tự sinh. Đối chiếu `test_soundness`. |
| `SEL` < `I` − .02 | Chọn bằng test tự sinh **có hại**: test sai loại oan bản đúng. Báo kèm số bài bị loại oan. |
| `test_copy_rate` > .20 | **HUỶ nhánh SEL** — rò rỉ, không đọc như kết quả. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 (~45%)**: chọn sẽ hơn review rõ rệt (vì review đang −.074 và trần chọn là +.044,
khoảng cách .118 quá lớn để không thấy gì), **nhưng** khó vượt `I` đủ +.02, vì H56 chỉ thu được
**42–46%** khoảng trống oracle bằng test tự sinh — áp vào đây là ~+.019, **ngay dưới ngưỡng**.
Hàng 1 ~30%. Hàng 3 ~15%, hàng 4 ~10%. Tỉ lệ prior đúng: **10/20**.

## BỔ SUNG #74-b — chạy lại H69 sau khi HUỶ (viết TRƯỚC khi chạy lại, chưa có số nào của H69b)
H69 **HUỶ** vì `test_soundness` = **.0523**. Nguyên nhân: chốt chống rò rỉ bỏ `test_list`,
mà đó là **nơi duy nhất chứa TÊN HÀM** ⇒ model bịa tên ⇒ mọi assert `NameError`.

**Sửa duy nhất:** đưa **TÊN HÀM** vào lượt viết test, trích tự động bằng
`re.search(r"assert\s+\(?\s*([A-Za-z_]\w*)\s*\(", a)` — **đã kiểm offline: 500/500 bài trích đúng**
(`remove_Occ`, `sort_matrix`, `count_common`, …). **KHÔNG** đưa giá trị kỳ vọng.

**Vì sao đây KHÔNG phải nới lỏng chống rò rỉ:** bộ chấm là *cặp (đầu vào → đầu ra kỳ vọng)*.
Tên hàm chỉ là **giao diện gọi**, model phải tự nghĩ ra ca kiểm thử và kết quả đúng.
Cổng `test_copy_rate` ≤ .20 **giữ nguyên** và sẽ bắt được nếu model chép nguyên assert.
Thêm: **phải kiểm `test_soundness` ≥ .50 TRƯỚC khi đọc bất kỳ con số nào.**

Bảng khoá #74 giữ **NGUYÊN**, không sửa một chữ. Prior giữ nguyên (hàng 2, ~45%).


# Đăng ký trước #75 — H70: **TÁCH CHẾ ĐỘ / NGUỒN có lặp lại trên TOÁN không?**
**Viết TRƯỚC khi chạy.**

## Vì sao
#105 (H68) tách được `V − I` trên **code** thành **hai** phần:
**chế độ sửa chữa −.0280 (38%)** + **nguồn ngoại lai −.0460 (62%)**.
Đó là **phép tách MỚI, chưa tái lập**, và tôi đã dùng nó để **thu hẹp cách gọi "đầu độc"** ở
#99–#103. Một kết luận đã sửa lại lời văn của bốn vòng thì **phải được kiểm trên task thứ hai**.

## Thiết kế — MATH-500, y hệt H68, đổi task
1.5B fp16 giải (`S`) · 7B nf4 · greedy · chấm `\boxed` bằng bộ chuẩn hoá đã kiểm offline ở #70
(500/500 gold tự khớp, 10/10 biến thể, 0 dương tính giả).
| nhánh | 7B xem gì | chế độ |
|---|---|---|
| `I` | không gì | sáng tác |
| `V_self` | **lời giải của CHÍNH NÓ** | sửa chữa |
| `V_weak` | lời giải của **1.5B** | sửa chữa |

## NGƯỠNG HIỆU LỰC (khoá trước)
`acc(I) − acc(S)` ≥ .05 · n ≥ 450 · `acc(S)` ∈ [.10,.55] (MATH không bão hoà).
**KHÔNG** đặt cổng tái lập theo giá trị `V_weak − I` của code (−.074) — đây là **task khác**,
ép cổng đó sẽ là áp đặt hậu kiểm.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `V_self − I` ≤ −.02 **và** `V_weak` thấp hơn `V_self` ≥ .02 | **PHÉP TÁCH LẶP LẠI trên toán.** "Thuế một lượt sửa" + "thiệt hại riêng của nguồn ngoại lai" là cấu trúc chung, không phải đặc thù code. Báo tỉ lệ % của hai phần và so với 38/62 của code. |
| `V_self ≈ I` (\|Δ\| < .02) **và** `V_weak − I` ≤ −.02 | Trên **toán**, chế độ sửa chữa **KHÔNG** tốn gì; toàn bộ thiệt hại là do **nguồn**. ⇒ phép tách 38/62 **đặc thù CODE**, phải nói rõ phạm vi ở #105. |
| cả hai ≈ `I` (\|Δ\| < .02) | Không có thiệt hại nào trên toán ở cặp 1.5B→7B này ⇒ mâu thuẫn H61 (−.0740 trên GSM8K). Phải kiểm khác biệt GSM8K vs MATH trước khi kết luận gì. |
| `V_self` thấp hơn `V_weak` ≥ .02 | Đảo ngược: sửa lời giải **của chính mình** hại **hơn** sửa của model yếu. Bất ngờ, phải tái lập trước khi tin. |
| `acc(I) − acc(S)` < .05 | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 (~50%)** nhưng với **tỉ lệ khác**: trên toán, mỏ neo đo ở #87 là **≈ 0**, còn trên
code là **−.08/−.098**. Nên phần "nguồn" trên toán có thể **nhỏ hơn** 62%, và phần "chế độ"
chiếm tỉ trọng lớn hơn. Hàng 2 ~25%, hàng 3 ~15%, hàng 4 ~10%. Tỉ lệ prior đúng: **11/21**.


# Đăng ký trước #76 — H71: **CÙNG NGÂN SÁCH — tiêu vào AGENT YẾU hay vào THÊM MẪU CỦA CHÍNH MODEL MẠNH?**
**Viết TRƯỚC khi chạy.**

## Vì sao — đây là câu hỏi THỰC DỤNG còn lại
#103/#105/#107: mọi giao thức "cho 7B xem sản phẩm 1.5B" đều **thua** việc gọi thẳng 7B
(−.0520 tốt nhất, −.1560 tệ nhất). Nhưng các nhánh đó **tốn thêm một lượt 1.5B**.
Câu hỏi đúng của người dùng không phải *"review có hại không"* mà:
> **Có thêm ngân sách X — tiêu vào chạy một model YẾU rồi hợp tác, hay vào LẤY THÊM MẪU của model MẠNH?**

## Thiết kế — MBPP 11–510, 7B nf4, chấm bằng assert đi kèm
| nhánh | gồm | chi phí (quy 1.5B-eq, 7B = 5.07×) |
|---|---|---|
| `I` | 1 mẫu 7B greedy | **5.07** |
| `V_weak` | 1.5B viết + 7B review *(đã đo: .5660)* | 6.07 |
| `SEL_weak` | 1.5B viết + 7B viết + 7B viết test → chọn *(H69b đang chạy)* | 11.14 |
| **`SEL_self`** | **7B greedy + 7B mẫu T=0.8 + 7B viết test → chọn giữa HAI mẫu của CHÍNH NÓ** | **15.21** |
| `I_pass2` | *(báo kèm)* có ít nhất một trong hai mẫu 7B đúng = trần của `SEL_self` | — |

**Không nhánh nào khớp chi phí chính xác** — vì thế **BẮT BUỘC báo cả acc lẫn chi phí**,
và kết luận phải nói rõ *"hơn/kém bao nhiêu, ở chi phí bao nhiêu"*, không được nói suông "tốt hơn".

Dùng lại đúng bộ sinh test và cổng chống rò rỉ của #74-b (tên hàm CÓ, giá trị kỳ vọng KHÔNG).

## NGƯỠNG HIỆU LỰC (khoá trước)
`test_copy_rate` ≤ .20 · `test_soundness` ≥ .50 · biên dịch ≥ .50 · n = 500 ·
`acc(I)` phải nằm trong **[.60, .68]** (tái lập .6400 của H66/H68/H69), ngoài khoảng ⇒ HUỶ.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL_self − I` ≥ **+.02** | **Ngân sách thêm nên tiêu vào MẪU CỦA CHÍNH MODEL MẠNH.** Kết hợp với #103–#107: agent yếu không những vô ích mà còn là **lựa chọn tệ hơn** cho cùng số tiền. Phát biểu thực dụng rõ ràng. |
| \|`SEL_self − I`\| < .02 | Lấy thêm mẫu của chính nó **cũng không** giúp ⇒ nút thắt là **SINH**, không phải chọn hay hợp tác. Khi đó **không có** cách tiêu ngân sách nào ăn thua ở thang này — kết quả âm rộng, phải nói thẳng. |
| `SEL_self` < `I` − .02 | Chọn bằng test tự sinh **có hại** ngay cả trên hai mẫu của chính nó ⇒ vấn đề nằm ở **chất lượng test**, không ở nguồn. Đối chiếu `test_soundness`. |
| `SEL_self − SEL_weak` ≥ +.02 *(khi H69b có số)* | Với **cùng cơ chế chọn**, mẫu của chính model mạnh **hơn** mẫu của agent yếu ⇒ agent yếu không đóng góp ứng viên có giá trị. |
| `SEL_weak − SEL_self` ≥ +.02 *(khi H69b có số)* | **Agent yếu CÓ đóng góp đa dạng thật** — nó giải được bài model mạnh trượt (22 bài ở #104), và chọn khai thác được. Đây sẽ là lần đầu hợp tác yếu→mạnh THẮNG. |
| `acc(I)` ngoài [.60,.68] | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 (~45%)**: `SEL_self` hơn `I` khoảng +.02..+.04, vì `I_pass2` (trần) chắc chắn
cao hơn `I` đáng kể và H56 thu được 42–46% khoảng trống oracle bằng test tự sinh.
Hàng 2 ~25%, hàng 3 ~20%. Về cặp `SEL_self` vs `SEL_weak`: đoán `SEL_self` hơn (~60%),
nhưng #104 cho thấy 1.5B giải được **22 bài** 7B trượt — đa dạng là thật, nên không chắc.
Tỉ lệ prior đúng: **11/22**.

## BỔ SUNG #74-c — H69c: dùng ĐÚNG giao thức giữ-lại của H56 (viết TRƯỚC khi chạy lại)
Hai lần HUỶ đều do tôi **cắt chống-rò-rỉ quá tay**: #106 cắt mất TÊN HÀM (soundness .0523),
#108 vẫn thiếu VÍ DỤ NGỮ NGHĨA (soundness .2580). H56 đạt **.8712** vì nó dùng ranh giới đúng:

- `assert[0]` **ĐƯỢC** đưa vào prompt (cả lượt giải lẫn lượt viết test) làm **ví dụ**.
- **Chấm CHỈ bằng `assert[1..2]`** — phần model chưa từng thấy.
Đây là **giữ-lại (held-out)** hợp lệ, không phải rò rỉ, và đã dùng ở kết quả +.0401/+.0388.

**Thay đổi cho H69c:**
1. prompt giải + prompt viết test: thêm `assert[0]`.
2. **bộ chấm đổi sang `test_list[1:3]`** cho **MỌI** nhánh.
3. Loại bài có < 3 assert (như H56 đã làm).
4. Giữ cổng `test_copy_rate` ≤ .20 (nay tính trên `assert[1..2]`, tức phần chấm) và
   `test_soundness` ≥ .50.

**HỆ QUẢ PHẢI GHI RÕ:** thang điểm khác H66/H68 (vốn chấm cả ba assert) ⇒ **`acc` tuyệt đối
KHÔNG so trực tiếp giữa các vòng**. Vì thế **BỎ cổng tái lập theo giá trị `V_review − I` ∈ [−.12,−.03]**
và thay bằng: **`V_review − I` phải ÂM** (cùng dấu với H66), nếu dương ⇒ ghi rõ là bất nhất và
kiểm lại trước khi đọc gì thêm. Mọi so sánh khác là **nội bộ, cùng bộ chấm** nên hợp lệ.

Bảng khoá #74 giữ NGUYÊN. Prior giữ nguyên (hàng 2, ~45%).


# Đăng ký trước #77 — H69d: **TÁI LẬP H69c trên dải bài TÁCH RỜI**
**Viết TRƯỚC khi chạy.**

## Vì sao
H69c là **kết quả dương đầu tiên cho hợp tác yếu→mạnh** (`SEL − I` = +.0220, 5/5 fold).
Quy tắc của dự án: **phát biểu mạnh nhất là phát biểu TÁI LẬP ĐƯỢC** (H56 +.0401 → H57 +.0388,
lệch .0013). Một kết quả dương chưa tái lập thì chưa được đưa vào README.

Thêm lý do phải cẩn thận: H69c là **lần thử THỨ BA** (hai lần trước HUỶ). Càng nhiều lần chạy
trên cùng ý tưởng thì càng dễ vô tình chọn cấu hình hợp với nhiễu. **Dải bài tách rời là cách kiểm.**

## Thiết kế — Y HỆT H69c, đổi DUY NHẤT dải task_id
MBPP **511–974** (H69c dùng 11–510, **không giao nhau**). Mọi thứ khác giữ nguyên tuyệt đối:
`assert[0]` vào prompt, chấm bằng `assert[1..2]`, loại bài < 3 assert, 1.5B fp16 + 7B nf4, greedy.

## NGƯỠNG HIỆU LỰC (khoá trước)
`test_soundness` ≥ .50 · `test_copy_rate` ≤ .20 · biên dịch ≥ .50 · n ≥ 400 ·
`V_review − I` phải ÂM (cùng dấu H69c).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL − I` ≥ **+.01** | **TÁI LẬP.** Hợp tác yếu→mạnh qua CHỌN LỌC là kết quả thật. Được đưa vào README kèm cả hai con số và chi phí 2.2×. Vẫn phải đối chiếu H71b trước khi khuyến nghị dùng. |
| \|`SEL − I`\| < .01 | **KHÔNG tái lập.** +.0220 của H69c phải bị **hạ cấp** xuống "chưa xác lập"; ghi rõ đó là lần thử thứ ba nên rủi ro nhiễu cao. |
| `SEL − I` ≤ **−.01** | **ĐẢO DẤU ⇒ RÚT LẠI H69c.** Chọn lọc không đáng tin trên dải khác. |
| `SEL − V_review` ≥ +.05 (bất kể ô trên) | Phần **"chọn hơn review"** tái lập kể cả khi biên độ so với `I` không tái lập. Đây là phát biểu yếu hơn nhưng vẫn dùng được. |
| cổng nào trượt | HUỶ, không đọc. |

## Prior TRUNG THỰC (ghi trước)
Đoán **tái lập (~70%)**: cơ chế rõ ràng (loại oan 4, lấy nhầm 2 — rất sạch, không giống nhiễu),
và `SEL − V_review` = +.1300 quá lớn để là ngẫu nhiên. Nhưng biên độ `+.0220` thì **nhỏ**
so với trần `+.0340`, nên con số cụ thể có thể dao động đáng kể. Đoán khoảng **+.01..+.03**.
Tỉ lệ prior đúng: **11/23**.


# Đăng ký trước #78 — H72: **ĐÓNG GÓP BIÊN của agent yếu khi pool ĐÃ đa dạng**
**Viết TRƯỚC khi chạy.** Đây là câu hỏi Shapley nguyên thuỷ của dự án, đặt đúng chỗ cuối cùng.

## Vì sao
#110/#111: chọn giữa {1.5B, 7B} cho **+.0220**; chọn giữa {7B, 7B'} cho **+.0340**.
Nhưng hai cái đó là **pool KHÁC NHAU**, chưa trả lời được câu hỏi biên:
> **Thêm 1.5B vào một pool ĐÃ CÓ hai mẫu 7B thì được thêm bao nhiêu?**

Đây chính là **giá trị Shapley của vai "agent yếu"** trong liên minh — mục tiêu ban đầu của dự án,
nhưng nay đo bằng **độ chính xác cuối cùng dưới oracle chọn**, không bằng bảng 2⁴ tổ hợp.

## Thiết kế — MỘT kernel, sinh MỘT lần, so MỌI tập con (ghép cặp hoàn hảo)
MBPP 11–510, giao thức #74-c (`assert[0]` vào prompt, chấm `assert[1..2]`).
Sinh: `I` = 7B greedy · `I2` = 7B T=0.8 · `S` = 1.5B greedy · `TESTS` = 7B viết test.
Rồi tính CHỌN trên các pool: **{I}** · **{I,S}** · **{I,I2}** · **{I,I2,S}**.
Mọi pool dùng **cùng bộ test, cùng bộ code** ⇒ khác biệt duy nhất là **thành phần pool**.

Báo kèm **trần hợp** của từng pool, và `n_picked` từng nguồn.

## NGƯỠNG HIỆU LỰC (khoá trước)
`test_soundness` ≥ .50 · `test_copy_rate` ≤ .20 · n = 500 · `acc(I)` ∈ [.60,.68] ·
tái lập: `SEL{I,S} − I` và `SEL{I,I2} − I` phải **dương** (H69c/H71b đã cho +.0220/+.0340).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL{I,I2,S} − SEL{I,I2}` ≥ **+.01** | **Agent yếu CÓ đóng góp biên thật** kể cả khi pool đã đa dạng. Vai "model yếu như nguồn ứng viên" được xác lập — nêu kèm chi phí (+1.00 đơn vị, rẻ nhất trong mọi cách mở rộng pool). |
| \|chênh\| < **.01** | **Đóng góp biên ≈ 0.** 1.5B không thêm gì mà hai mẫu 7B chưa có. Kết luận cuối cho vai agent yếu: **không có giá trị biên**, kể cả ở dạng dùng tốt nhất (ứng viên + chọn). |
| chênh ≤ **−.01** | Thêm 1.5B **làm hại** pool: bộ chọn bị đánh lừa bởi ứng viên kém. Báo số lần chọn nhầm sang S. |
| `SEL{I,I2,S}` ≥ trần của `{I,I2}` | 1.5B giải được bài mà **cả hai** mẫu 7B trượt ⇒ đa dạng thật, dù bộ chọn có bắt được hay không. Báo riêng con số này. |
| cổng trượt | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 (~55%)**: đóng góp biên ≈ 0. Lý do: ở #104, 1.5B giải được **22/500** bài mà 7B
trượt — nhưng phần lớn trong số đó là bài **dễ-với-1.5B** mà mẫu 7B thứ hai (T=0.8) nhiều khả năng
cũng bắt được. Hàng 1 ~25%, hàng 3 ~20% (bộ chọn có `soundness` .72, tức **28% test sai**,
nên thêm một ứng viên kém là thêm cơ hội bị đánh lừa). Tỉ lệ prior đúng: **12/24**.


# Đăng ký trước #79 — H73: **LỢI ÍCH CỦA CHỌN CÓ TĂNG THEO SỐ ỨNG VIÊN k KHÔNG?**
**Viết TRƯỚC khi chạy.** Suy thẳng từ phụ lục thăm dò #111-b.

## Vì sao
#111-b (hậu kiểm H71b): trên 500 bài, **chỉ 4 bài** có bản đúng trong pool mà bộ chọn bỏ lỡ
(mất .0080). **89.8% số bài HOÀ điểm test** ⇒ bộ chọn **không còn là nút thắt**;
cải thiện test tối đa còn **< +.01**. Nút thắt đã chuyển sang **TRẦN CỦA POOL**.
Nếu đúng thì **thêm ứng viên** phải là đòn bẩy, và **tỉ lệ hoà phải giảm khi k tăng**.
Đây cũng là lời giải thích hậu kiểm cho H58 (*"số lượng test không phải nút thắt"*, +.0101) —
nay phải kiểm bằng một phép thử khoá trước.

## Thiết kế — MỘT kernel, sinh MỘT lần, cắt theo k (ghép cặp hoàn hảo)
MBPP 11–510, 7B nf4, giao thức #74-c (`assert[0]` vào prompt, chấm `assert[1..2]`).
Sinh **8 ứng viên**: 1 greedy + 7 mẫu T=0.8. Sinh test **một lần** (7B, greedy).
Tính `SEL@k` cho **k = 1, 2, 4, 8** trên **đúng cùng** bộ ứng viên và **cùng** bộ test
(k nhỏ = tiền tố của k lớn) ⇒ khác biệt duy nhất là **số ứng viên**.

Báo cho mỗi k: `SEL@k` · `trần@k` (hợp) · **`tie_rate@k`** (tỉ lệ bài mà mọi ứng viên hoà điểm test)
· % khoảng trống thu được · chi phí (1.5B-eq, 7B = 5.07×; k ứng viên + 1 lượt test).

## NGƯỠNG HIỆU LỰC (khoá trước)
`test_soundness` ≥ .50 · `test_copy_rate` ≤ .20 · n = 500 · `acc(SEL@1)` = `acc(I)` ∈ [.60,.68].

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL@8 − SEL@2` ≥ **+.02** VÀ `SEL@k` tăng đều theo k | **k LÀ ĐÒN BẨY.** #111-b được xác nhận: nút thắt là trần pool. Khuyến nghị thực dụng: tiêu ngân sách vào **thêm mẫu**, không vào test tốt hơn. Nêu kèm chi phí tăng tuyến tính theo k. |
| \|`SEL@8 − SEL@2`\| < **.02** | **k KHÔNG phải đòn bẩy.** Cả bộ chọn lẫn pool đều bão hoà ⇒ nút thắt nằm ở **bản thân việc SINH** (8 mẫu không đa dạng hơn 2 một cách hữu ích). Kết quả âm rộng: không cách tiêu ngân sách nào ăn thua ở thang model này. |
| `trần@8 − trần@2` ≥ +.04 **nhưng** `SEL@8 − SEL@2` < +.02 | **ĐẢO LẠI #111-b: ở k lớn, BỘ CHỌN mới là nút thắt.** Pool có nhiều bản đúng hơn nhưng test tự sinh không phân biệt nổi. Khi đó quay lại hướng cải thiện test — và tôi phải **rút lại** kết luận của #111-b. |
| `tie_rate@8` KHÔNG giảm rõ so với `tie_rate@2` | Cơ chế tôi nêu ở #111-b SAI: thêm ứng viên không tạo thêm khác biệt quan sát được qua test. Ghi rõ. |
| cổng trượt | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 (~55%)** nhưng với **lợi ích giảm dần**: `SEL@2` +.034 (đã đo ở H71b),
đoán `SEL@4` ≈ +.05, `SEL@8` ≈ +.06 ⇒ `SEL@8 − SEL@2` ≈ **+.025**, vừa qua ngưỡng.
Rủi ro thấy trước: `tie_rate` **.898 ở k=2 là rất cao**; nếu 8 mẫu greedy-ish của cùng model
vẫn hoà ở ~80% thì ra hàng 2. Hàng 2 ~25%, hàng 3 ~15%, hàng 4 ~5%.
Tỉ lệ prior đúng: **13/25**.


# Đăng ký trước #80 — H74: **CÙNG CHI PHÍ — NHIỀU ứng viên RẺ hay ÍT ứng viên ĐẮT?**
**Viết TRƯỚC khi chạy.** Suy thẳng từ #113.

## Vì sao
#113 (ghép cặp, cùng lần chạy): đóng góp biên của **một mẫu 1.5B** = **+.0180**, **BẰNG** đóng góp
của **một mẫu 7B nữa** (+.0180) — nhưng rẻ hơn **5.07 lần**. Nếu quan hệ đó còn giữ khi thêm mẫu,
thì với **cùng ngân sách**, một pool gồm **nhiều mẫu 1.5B** phải **thắng** pool ít mẫu 7B.
Đây là dạng thực dụng nhất của toàn bộ chuỗi #99–#113.

## Thiết kế — MỘT kernel, sinh MỘT lần, so mọi pool (ghép cặp hoàn hảo)
MBPP 11–510, giao thức #74-c. Sinh: `I` = 7B greedy · `I2` = 7B T=0.8 ·
`S1..S5` = 5 mẫu 1.5B (1 greedy + 4 T=0.8) · `TESTS` = 7B viết test (một lần, dùng chung).

| pool | chi phí sinh (1.5B-eq) | +test | TỔNG |
|---|---|---|---|
| {I} | 5.07 | 5.07 | 10.14 |
| {I, S1} | 6.07 | 5.07 | 11.14 |
| **{I, I2}** | **10.14** | 5.07 | **15.21** |
| **{I, S1..S5}** | **10.07** | 5.07 | **15.14** |
| {I, I2, S1..S5} | 15.14 | 5.07 | 20.21 |

**{I, I2} và {I, S1..S5} khớp chi phí tới 0.5%** ⇒ đây là **so sánh cùng ngân sách thật sự**.

## NGƯỠNG HIỆU LỰC (khoá trước)
`test_soundness` ≥ .50 · `test_copy_rate` ≤ .20 · n = 500 · `acc(I)` ∈ [.60,.68] ·
tái lập #113: `SEL{I,S1}` và `SEL{I,I2}` đều phải **dương** so với `I`.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL{I,S1..S5} − SEL{I,I2}` ≥ **+.02** | **NHIỀU ỨNG VIÊN RẺ THẮNG.** Ở cùng ngân sách, năm mẫu 1.5B hơn một mẫu 7B. Khuyến nghị thực dụng rõ ràng và **đảo ngược trực giác "dùng model tốt nhất có thể"**. |
| \|chênh\| < **.02** | **HOÀ ở cùng ngân sách.** Nguồn ứng viên không quan trọng bằng **tổng ngân sách**; chọn nguồn nào là tuỳ tiện. Vẫn là phát biểu dùng được. |
| chênh ≤ **−.02** | **ÍT ứng viên ĐẮT thắng.** Chất lượng ứng viên quan trọng hơn số lượng; #113 không ngoại suy được lên nhiều mẫu. |
| `SEL{I,S1..S5} − SEL{I,S1}` < **+.01** | **Bão hoà ngay sau mẫu 1.5B ĐẦU TIÊN.** Đa dạng của 1.5B là *một lần*, không cộng dồn — hạn chế quan trọng của #113. |
| trần{I,S1..S5} ≥ trần{I,I2} + .03 | Pool rẻ có **trần cao hơn** ngay cả khi bộ chọn không khai thác hết ⇒ đa dạng thật, nút thắt quay lại bộ chọn. |
| cổng trượt | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 (~40%)** — hoà. Lý do: #111-b cho thấy **89.8% bài HOÀ điểm test** ở k=2;
thêm mẫu 1.5B (chất lượng .44) sẽ tạo thêm ứng viên **sai**, mà bộ chọn có `soundness` .72
nên dễ bị đánh lừa hơn. Hàng 1 ~30% (nếu đa dạng thắng nhiễu), hàng 3 ~15%, hàng 4 ~15%.
**Tôi vừa sai ở #113 khi đoán "đóng góp biên ≈ 0"**, nên lần này không tự tin về phía âm.
Tỉ lệ prior đúng: **13/26**.


# Đăng ký trước #81 — H75: **SỬA BỘ CHỌN — đồng thuận THỰC THI thay vì đếm test ĐẠT**
**Viết TRƯỚC khi chạy.** Suy thẳng từ #115.

## Vì sao
#115: trần tăng đều theo số ứng viên (.6400 → .7260) nhưng **tỉ lệ thu được sụt 86% → 41%**.
Ứng viên đúng **có ở đó**; bộ chọn **không nhặt được**. Nguyên nhân đã biết: `test_soundness` = .7214,
tức **28% bộ test có GIÁ TRỊ KỲ VỌNG SAI** — càng nhiều ứng viên, càng nhiều cơ hội chấm nhầm.

**Điểm mấu chốt: cái SAI là giá trị kỳ vọng, KHÔNG phải đầu vào.**
Lời gọi hàm trong assert tự sinh vẫn hợp lệ. Vậy thì đừng dùng kỳ vọng — **chạy MỌI ứng viên
trên CÙNG đầu vào và so đầu ra VỚI NHAU**. Cụm lớn nhất thắng. Không cần biết đáp án đúng.
(Dự án đã có nguyên hàm này ở H56: `route_consensus`, và `split_assert` tách được **498/500**.)

## Thiết kế — MỘT kernel, pool 7 ứng viên như #115, ba BỘ CHỌN trên CÙNG dữ liệu
MBPP 11–510, giao thức #74-c. Sinh: `I`, `I2` (7B), `S1..S5` (1.5B), `TESTS` (7B).
Tách **đầu vào** khỏi assert bằng AST (`split_assert`), bỏ vế kỳ vọng.
| bộ chọn | tín hiệu |
|---|---|
| `SEL_test` | đếm assert tự sinh ĐẠT (như #115 — mốc so sánh) |
| **`SEL_cons`** | chạy mọi ứng viên trên **đầu vào**, gom cụm theo **đầu ra**, chọn cụm LỚN NHẤT |
| `SEL_hyb` | `SEL_cons`, hoà thì phân giải bằng `SEL_test` |

Hoà tuyệt đối ⇒ giữ `I`. Chấm bằng `assert[1..2]`. Báo `captured_pct` của cả ba trên **cùng trần**.

## NGƯỠNG HIỆU LỰC (khoá trước)
`split_assert` tách được ≥ **.80** số assert · `test_soundness` ≥ .50 · `copy_rate` ≤ .20 ·
n = 500 · `acc(I)` ∈ [.60,.68] · tái lập #115: `SEL_test` trên pool 7 phải ∈ [.66, .71].

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL_cons − SEL_test` ≥ **+.02** | **ĐỒNG THUẬN THỰC THI HƠN HẲN.** Bỏ được phụ thuộc vào giá trị kỳ vọng ⇒ bộ chọn hết là nút thắt. Đây là bản sửa trực tiếp cho #115 và là giao thức nên dùng khi k lớn. |
| +.005 ≤ chênh < +.02 | Hơn nhưng **khiêm tốn**; nút thắt vẫn còn. Báo `captured_pct` để định lượng phần còn thiếu. |
| \|chênh\| < .005 | **Đồng thuận KHÔNG hơn đếm test.** Nghĩa là các ứng viên **sai theo cùng một kiểu** (lỗi tương quan), nên cụm lớn nhất cũng sai. Kết quả âm quan trọng: đa dạng ở #115 là đa dạng *bề mặt*. |
| chênh ≤ **−.02** | Đồng thuận **tệ hơn**: đa số sai nhấn chìm thiểu số đúng. Ghi rõ, giữ `SEL_test`. |
| `SEL_hyb` > cả hai + .005 | Hai tín hiệu **bổ sung** nhau; nêu kèm. |
| `split_assert` < .80 hoặc cổng khác trượt | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 (~40%)**: hơn một chút. Lý do đối nghịch nhau: đồng thuận **thoát** được lỗi
giá trị kỳ vọng (điểm mạnh thật), **nhưng** 5/7 ứng viên là 1.5B với acc ~.42, nên **đa số
có thể SAI** ở nhiều bài — cụm lớn nhất khi đó là cụm sai. Hàng 1 ~20%, hàng 3 ~25%, hàng 4 ~15%.
**Đây chính là rủi ro tôi phải nêu trước:** đồng thuận chỉ tốt khi đa số đúng, mà pool này
đa số là model yếu. Tỉ lệ prior đúng: **14/27**.


# Đăng ký trước #82 — H73b: **TÁI LẬP k-scaling trên dải TÁCH RỜI**
**Viết TRƯỚC khi chạy.**

## Vì sao
#117 là **hiệu ứng dương LỚN NHẤT** của dự án (`SEL@8` = .7200, **+.0800** so với greedy).
Quy tắc dự án: phát biểu mạnh nhất là phát biểu **TÁI LẬP ĐƯỢC**. Chưa tái lập thì chưa vào README.
Thêm nữa, #117 vừa cho thấy **chênh .0160 chỉ do rút mẫu khác** giữa H73 và H74 — biên độ nhiễu
của một lần rút là **đáng kể**, nên một dải bài khác là phép kiểm cần thiết.

## Thiết kế — Y HỆT H73, đổi DUY NHẤT dải task_id
MBPP **511–974** (H73 dùng 11–510). 8 ứng viên 7B, test sinh một lần, k = 1/2/4/8, tiền tố.

## NGƯỠNG HIỆU LỰC (khoá trước)
`test_soundness` ≥ .50 · `copy_rate` ≤ .20 · n ≥ 400 · `acc(SEL@1)` phải nằm trong
**[.66, .76]** (H69d đo `I` = .7069 trên dải này; cho biên rộng vì mẫu khác).

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL@8 − SEL@2` ≥ **+.02** VÀ tăng đều theo k | **TÁI LẬP.** k-scaling là kết quả thật, đưa vào README kèm **cả chi phí 4.5×** và kèm ghi chú lợi ích/đơn vị giảm dần. |
| +.01 ≤ chênh < +.02 | Tái lập **yếu**; hiệu ứng thật nhưng biên độ nhỏ hơn #117 rõ rệt. Báo cả hai số, không lấy số lớn hơn làm đại diện. |
| \|chênh\| < .01 | **KHÔNG tái lập** ⇒ hạ cấp #117 xuống "chưa xác lập". |
| chênh ≤ −.01 | **ĐẢO DẤU ⇒ RÚT LẠI #117.** |
| `tie_rate` KHÔNG giảm theo k | Cơ chế nêu ở #111-b/#117 sai trên dải này; ghi rõ dù biên độ acc có tái lập. |
| **`SEL@8` ≥ `SEL@4` + .04** (tăng TĂNG TỐC thay vì giảm dần) | Ngược hẳn dự đoán "lợi ích giảm dần" của tôi ⇒ phải kiểm k > 8 trước khi khuyến nghị k=2 làm điểm ngọt. |
| cổng trượt | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **tái lập (~75%)** với biên độ **+.025..+.045**: cơ chế (tie_rate giảm) rất rõ và đơn điệu
qua bốn mức k, khó là nhiễu. Nhưng dải 511–974 có `I` cao hơn (.7069 vs .6400) ⇒ **ít dư địa hơn**,
nên biên độ có thể **nhỏ hơn** #117. Tỉ lệ prior đúng: **15/29**.


# Đăng ký trước #83 — H76: **ĐỒNG THUẬN CÓ HOẠT ĐỘNG KHI ĐA SỐ ĐÚNG KHÔNG?**
**Viết TRƯỚC khi chạy.** Kiểm thẳng chẩn đoán của #118.

## Vì sao
#118: đồng thuận thực thi **−.0840** trên pool **5/7 là 1.5B** (acc ~.42).
Chẩn đoán tôi đưa ra: *"đa số SAI nhấn chìm thiểu số ĐÚNG; năm mẫu cùng một model là lỗi
TƯƠNG QUAN, không phải năm phiếu độc lập."*
**Nếu chẩn đoán đó đúng thì trên pool mà đa số ĐÚNG, đồng thuận phải hoạt động tốt.**
Pool 8 mẫu 7B của #117 (mỗi mẫu **.624–.662**) là phép thử sạch: đa số đúng ở phần lớn bài.

## Thiết kế — pool 8×7B của H73, ba bộ chọn trên CÙNG dữ liệu (ghép cặp hoàn hảo)
MBPP 11–510, giao thức #74-c. Sinh 8 ứng viên 7B (1 greedy + 7 T=0.8) + test (7B, một lần).
`SEL_test` (đếm assert đạt) · `SEL_cons` (gom cụm đầu ra) · `SEL_hyb` (cons, hoà thì dùng test).

## NGƯỠNG HIỆU LỰC (khoá trước)
tách lời gọi ≥ .80 · `soundness` ≥ .50 · `copy_rate` ≤ .20 · n=500 ·
tái lập #117: `SEL_test` trên 8 ứng viên phải ∈ **[.69, .75]**.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL_cons − SEL_test` ≥ **+.02** | **CHẨN ĐOÁN #118 ĐƯỢC XÁC NHẬN.** Đồng thuận tốt khi đa số đúng, hại khi đa số sai. Quy tắc dùng được: **chỉ bỏ phiếu giữa các ứng viên CÙNG mức năng lực cao**; đừng trộn model yếu vào phiếu bầu. |
| \|chênh\| < .02 | Đồng thuận **không hơn** ngay cả khi đa số đúng ⇒ chẩn đoán #118 **chưa đủ**: vấn đề không chỉ là "đa số sai" mà là **lỗi tương quan nói chung** (8 mẫu cùng model cũng tương quan). Phát biểu mạnh hơn và bi quan hơn. |
| `SEL_cons` < `SEL_test` − .02 | **Đồng thuận hại kể cả khi đa số đúng** ⇒ **RÚT LẠI chẩn đoán #118**; nguyên nhân thật nằm ở chỗ khác (ví dụ: gom cụm theo `repr` quá nhạy với khác biệt vô hại). |
| `SEL_hyb` > cả hai + .005 | Hai tín hiệu bổ sung nhau; đây là bộ chọn nên dùng. |
| `SEL_cons` ≥ trần − .01 | Đồng thuận gần như khai thác hết pool ⇒ nút thắt chuyển hẳn về SINH. |
| cổng trượt | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 (~45%)** — nhưng **thận trọng hơn lần trước**, vì bài học #118 là tôi đã để
"ý tưởng hay" kéo prior lên. Lý do nghi ngờ, ghi rõ: **8 mẫu từ CÙNG một model 7B vẫn tương quan
mạnh** (chúng chia sẻ cùng thiên lệch), nên "đa số đúng" có thể vẫn không phải phiếu độc lập.
Hàng 2 ~35% (đó là kịch bản bi quan và tôi thấy nó rất khả dĩ), hàng 3 ~15%.
Tỉ lệ prior đúng: **15/30**.


# Đăng ký trước #84 — H70c: **ĐO LẠI `V_self` trên MATH sau khi SỬA CONFOUND CẮT NGẮN**
**Viết TRƯỚC khi chạy.**

## Vì sao
#119: nhánh `I` bị cắt ở `MAXNEW=640` **nhiều hơn hẳn** nhánh `V` (thiếu `\boxed`:
`I_7B` 39.8% vs `V_7B` 25.4%), vì `V` được đưa sẵn lời giải nên tốn ít token hơn.
⇒ Mọi `V − I` trên MATH **thiên lệch có lợi cho `V`**. Phát hiện đầu bảng #116
(`V_self − I` = **+.1080**) đã bị **ĐÌNH CHỈ**.

## Thay đổi so với H70
1. **`MAXNEW` 640 → 1280** (gấp đôi).
2. **Cổng cắt ngắn MỚI (khoá trước):** tỉ lệ đầu ra có `\boxed` ≥ **.80** ở **MỌI** nhánh,
   **VÀ** chênh lệch tỉ lệ đó giữa hai nhánh bất kỳ < **.05**. Trượt ⇒ **HUỶ, không đọc**.
3. Báo tỉ lệ `\boxed` của từng nhánh trong tổng kết.
Mọi thứ khác giữ nguyên: MATH-500, 1.5B fp16 giải, 7B nf4, greedy, `I`/`V_self`/`V_weak`.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `V_self − I` ≥ **+.05** (cổng cắt ngắn ĐẠT) | **#116 SỐNG SÓT.** Tự xem lại trên toán thật sự có ích lớn; confound chỉ phóng đại chứ không tạo ra hiệu ứng. Ghi lại cả hai số (+.1080 cũ, số mới) và dùng **số MỚI**. |
| +.02 ≤ `V_self − I` < +.05 | **#116 ĐÚNG CHIỀU nhưng PHÓNG ĐẠI ĐÁNG KỂ.** Phải thay số cũ bằng số mới ở mọi chỗ trích dẫn. |
| \|`V_self − I`\| < .02 | **#116 PHẦN LỚN LÀ ARTIFACT CẮT NGẮN ⇒ RÚT LẠI.** "Thuế sửa chữa đặc thù task" không được xác lập trên toán. |
| `V_self − I` ≤ −.02 | **ĐẢO DẤU:** tự xem lại HẠI trên toán, giống code. Rút lại #116 hoàn toàn và ghi rõ hướng ngược. |
| `V_weak − I` khác đáng kể −.0120 (cũ) | Ghi rõ: số cũ cũng bị confound; dùng số mới. |
| cổng cắt ngắn TRƯỢT lần nữa | HUỶ; tăng `MAXNEW` tiếp và ghi rõ rằng MATH-500 cần ngân sách token lớn hơn tôi tưởng. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 (~45%)**: đúng chiều nhưng nhỏ hơn nhiều — vì lệch cắt ngắn (−72 bài trên 500
= **14.4 điểm phần trăm**) đủ lớn để giải thích **phần lớn** +.1080, nhưng `V_self` cứu 58 phá 4
(#116) là một cấu trúc khó tạo ra hoàn toàn bằng artifact. Hàng 1 ~15%, hàng 3 ~30%, hàng 4 ~10%.
**Tôi đang đặt cược chống lại phát hiện của chính mình, và đó là điều đúng phải làm.**
Tỉ lệ prior đúng: **15/30**.


# Đăng ký trước #85 — H65d: **QUÉT NĂNG LỰC LÀM LẠI trên RTX 6000, `MAXNEW`=1280**
**Viết TRƯỚC khi chạy.** Cần card lớn thật sự: ba model bf16 + sinh dài.

## Vì sao chạy lại
H65c **HUỶ** vì cổng `acc(I_14B) − acc(I_7B) ≥ .05` trượt (**−.0280**, 14B YẾU HƠN 7B).
Nhưng #119 phát hiện **`MAXNEW`=640 cắt nhánh `I` rất nặng** (39.8–45.8% mất `\boxed`),
và **14B bị cắt nhiều hơn 7B** (43.0% vs 39.8%).
> **Giả thuyết: chính cổng đó trượt VÌ confound.** Model lớn viết dài hơn ⇒ bị cắt nhiều hơn ⇒
> **đo ra yếu hơn**. Với `MAXNEW`=1280, 14B có thể vượt 7B và quét năng lực trở nên đọc được.

**Đây là lý do phải dùng zhongzhing/RTX 6000:** ba model **bf16** (3+15+29 = 47 GB) **cộng**
sinh 1280 token cho lô lớn — T4 không chứa nổi, và nf4 sẽ thêm một confound khác.

## Thiết kế
Y hệt #70, đổi **hai** thứ: `MAXNEW` 640 → **1280**, và thêm **cổng cắt ngắn**.

## NGƯỠNG HIỆU LỰC (khoá trước)
- **cổng cắt ngắn MỚI:** tỉ lệ có `\boxed` ≥ **.80** ở MỌI nhánh **VÀ** chênh giữa hai nhánh bất kỳ < **.05**.
- `acc(I_14B) − acc(I_7B)` ≥ **.05** · `acc(I_7B) − acc(S)` ≥ .05 · `acc(S)` ∈ [.10,.55] · n=500.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| cổng cắt ngắn ĐẠT **và** `I_14B − I_7B` ≥ .05 | **Cổng ở H65c trượt VÌ CONFOUND, không phải vì 14B kém.** Đọc quét năng lực theo bảng #70. Ghi rõ: một tham số sinh đã suýt tạo ra kết luận sai về năng lực model. |
| cổng cắt ngắn ĐẠT nhưng `I_14B − I_7B` < .05 | **14B THẬT SỰ không mạnh hơn 7B trên MATH-500 ở thiết lập này** (không phải artifact). HUỶ quét năng lực **lần cuối**; ngừng theo đuổi hướng 14B trên benchmark này và ghi rõ lý do. |
| cổng cắt ngắn TRƯỢT lần nữa | HUỶ; MATH-500 cần ngân sách token lớn hơn 1280 — báo tỉ lệ để chọn mức tiếp theo. |
| `I_14B − I_7B` ≥ .05 nhưng **poisoning KHÔNG đơn điệu** theo năng lực | Ghi đúng như đo được; **không** vẽ xu hướng từ ba điểm. |
| poisoning(14B) ≥ **+.02** (V TỐT HƠN I ở 14B) | Hàng cho chiều tôi cho là khó: ở năng lực cao, **được xem lời giải yếu lại CÓ ÍCH**. Nếu ra thế này phải kiểm ngay xem cổng cắt ngắn có thật sự cân bằng không trước khi tin. |

## Prior TRUNG THỰC (ghi trước)
Đoán **50/50** giữa hai hàng đầu. Lệch cắt ngắn 14B−7B chỉ **3.2 đpt**, khó lấp hết khoảng
**−.0280**, nên nghiêng nhẹ về *"14B thật sự không hơn"*. Nhưng `MAXNEW` dài hơn cũng nâng
**tất cả** các nhánh và có thể đổi thứ hạng. Tỉ lệ prior đúng: **15/30**.


# Đăng ký trước #86 — H77: **"CHỌN hơn REVIEW" có đúng trên TOÁN không?**
**Viết TRƯỚC khi chạy.**

## Vì sao
Phát biểu vững nhất của chuỗi #99–#118 là **"CHỌN hơn REVIEW"** (+.0841..+.1300 trên MBPP),
nhưng **toàn bộ bằng chứng đến từ CODE**, nơi có oracle chạy được. Trên toán không có test,
nhưng có **bỏ phiếu đa số đáp án** (`maj@k`) — cũng là **chọn**, chỉ khác tín hiệu.
Nếu nguyên tắc đúng thì `maj@k` phải hơn `V_review` trên MATH.

**Và nó kiểm luôn lời giải thích ở #118.** Ở đó đồng thuận **thất bại trên code** vì lỗi tương quan
(8 mẫu 7B: 25% cùng sai, 52.8% cùng đúng). Trên **toán**, đáp án là **một con số ngắn**,
lỗi đa dạng hơn nhiều ⇒ đồng thuận **phải** hoạt động. Đây là phép thử phân biệt sạch.

## Thiết kế — MATH-500, `MAXNEW`=1280, 7B nf4, cùng một bộ sinh
`S` = 1.5B giải · `I` = 7B greedy · `C1..C8` = 8 mẫu 7B (T=0.8) · `V_review` = 7B xem lời giải của `S`.
Nhánh: `I` · `V_review` · **`maj@2/4/8`** (bỏ phiếu đáp án đã chuẩn hoá, hoà → giữ `I`).

## NGƯỠNG HIỆU LỰC (khoá trước)
**Cổng cắt ngắn (#84):** tỉ lệ có `\boxed` ≥ .80 mọi nhánh, chênh giữa hai nhánh < .05 ⇒ nếu không, HUỶ.
`acc(I) − acc(S)` ≥ .05 · n = 500.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `maj@8 − V_review` ≥ **+.05** | **"CHỌN hơn REVIEW" TỔNG QUÁT SANG TOÁN.** Nguyên tắc không phụ thuộc oracle chạy được; nó đúng với bất kỳ tín hiệu chọn nào. Phát biểu trung tâm của dự án mạnh lên rõ rệt. |
| +.02 ≤ chênh < +.05 | Đúng chiều nhưng **yếu hơn code** rõ rệt; nêu cả hai biên độ, không gộp. |
| \|chênh\| < .02 | **KHÔNG tổng quát.** "Chọn hơn review" là phát biểu **về CODE**, không phải về hợp tác nói chung. Thu hẹp mọi chỗ đã viết. |
| `maj@8` < `V_review` − .02 | **ĐẢO DẤU trên toán** — review hơn chọn. Bất ngờ lớn, phải kiểm cổng cắt ngắn kỹ trước khi tin. |
| `maj@8 − I` ≥ +.05 **và** `maj@8` tăng đều theo k | k-scaling (#117) tổng quát sang toán bằng tín hiệu KHÁC (đáp án thay vì test). |
| `maj@8 − I` < +.02 | Bỏ phiếu đa số **không giúp** trên toán ⇒ lỗi tương quan là hiện tượng **chung**, không đặc thù code ⇒ củng cố #117-b và làm yếu lời giải thích ở #118. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 (~60%)**: `maj@k` trên toán là kỹ thuật đã biết là mạnh, và `V_review` trên MATH
chỉ ≈ −.012, nên khoảng cách dễ vượt +.05. Về `maj@8 − I`: đoán **+.05..+.09**.
Rủi ro ghi trước: nếu 8 mẫu toán cũng lưỡng cực như code (#117-b) thì ra hàng 6 và **lời giải thích
#118 phải đổi từ "đặc thù code" sang "chung"**. Tỉ lệ prior đúng: **15/30**.


# Đăng ký trước #87 — H78: **32B — ĐẦU ĐỘC CÓ TAN THEO NĂNG LỰC KHÔNG?** (thiết kế ĐÃ SỬA)
**Viết TRƯỚC khi chạy.** Cần RTX 6000 Pro thật sự: Qwen2.5-32B **bf16 = 68 GB**.

## Vì sao chạy, và vì sao THIẾT KẾ CŨ PHẢI BỎ
Phát hiện chính của dự án (`V − I` ÂM ở mọi miền: −.074 / −.074 / −.126 / −.168) có **một phản
biện hiển nhiên**: *"chỉ đúng vì model của anh đều nhỏ"*. 32B là phép thử rẻ nhất cho phản biện đó.

**Nhưng thiết kế cũ (#70/#85) HỎNG** — kiểm định độc lập #125-A2 chỉ ra:
`poisoning(1.5B)` là **TỰ xem lại** (`I_1.5B is SOLS`) trong khi `poisoning(7B/14B)` là **xem model KHÁC**.
Trục "năng lực" trộn **chế độ** với **nguồn**. Thêm 32B vào bảng đó = thêm một hàng vô nghĩa.

**Sửa: BỎ hàng 1.5B.** Solver **cố định = 1.5B**; chỉ đổi **năng lực VERIFIER** qua **7B / 14B / 32B**.
Mọi hàng đều là **cross-model review trên CÙNG một bộ lời giải của 1.5B** ⇒ so sánh thuần một biến.

## Thiết kế
MATH-500 · **bf16 toàn bộ, KHÔNG lượng tử hoá** · `MAXNEW`=1280 · greedy ·
nạp **tuần tự** (15+29+68 = 112 GB > 95 GB nên không thể giữ cùng lúc) · **lưu từng phần sau mỗi model**.
Với mỗi M ∈ {7B, 14B, 32B}: `I_M` = M tự giải · `V_M` = M xem lời giải của 1.5B rồi kiểm/sửa.
`poisoning(M)` = `acc(V_M) − acc(I_M)`.

## NGƯỠNG HIỆU LỰC (khoá trước)
- **Cổng cắt ngắn (#84):** tỉ lệ có `\boxed` ≥ **.80** ở MỌI nhánh **VÀ** chênh giữa hai nhánh bất kỳ < **.05**.
  *(H65d trượt đúng cổng này ở .0500 — không được nới.)*
- **Cổng năng lực:** `acc(I_32B) − acc(I_7B)` ≥ **.05**. Nếu 32B không thật sự mạnh hơn 7B thì
  "thêm năng lực" **không xảy ra** ⇒ HUỶ. *(14B chỉ hơn 7B .0180 nên cổng này rất có thể trượt lần nữa —
  tôi chấp nhận rủi ro đó thay vì nới ngưỡng.)*
- `acc(S)` ∈ [.10,.55] · n = 500 · lưu toàn văn.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `poisoning(32B)` ≥ **−.02** VÀ \|poisoning\| giảm đều 7B→14B→32B | **ĐẦU ĐỘC TAN THEO NĂNG LỰC.** Phản biện "model quá nhỏ" ĐÚNG; phát hiện chính phải thu hẹp về "model nhỏ". Nêu rõ 32B vẫn chưa phải model biên. |
| `poisoning(32B)` ∈ [−.05, −.02) VÀ giảm đều | Co lại theo năng lực nhưng **chưa hết** ở 32B. Ngoại suy điểm hoà vốn, ghi rõ là ngoại suy. |
| \|`poisoning(32B)`\| ≥ **.05** HOẶC không giảm đều | **ĐẦU ĐỘC KHÔNG RỬA ĐƯỢC BẰNG NĂNG LỰC** trong dải 7B–32B (hơn **4.5×** tham số). Đây là bản mạnh nhất của phát hiện chính và là câu trả lời trực tiếp cho phản biện. |
| `poisoning(32B)` > **+.02** | **ĐẢO DẤU ở năng lực cao:** 32B được xem lời giải yếu lại TỐT LÊN. Nếu vậy phải kiểm cổng cắt ngắn cực kỹ trước khi tin, và kiểm xem 32B có đang bỏ qua hoàn toàn lời giải kia không (`unchanged_rate`). |
| `acc(I_32B) − acc(I_7B)` < .05 | **HUỶ**, không đọc. Kết luận: MATH-500 ở greedy **không phân giải được** năng lực trong dải này — và đó là lý do phải dừng hướng quét năng lực, không phải vì đầu độc. |
| cổng cắt ngắn trượt | HUỶ; báo tỉ lệ để chọn `MAXNEW` tiếp theo. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 3 (~45%)**: đầu độc còn ≥ .05 ở 32B. Lý do: cơ chế đo được không phải "thiếu năng lực"
mà là **được đưa một lời giải sai thì bị kéo vào chế độ sửa chữa**, và #122 cho thấy trên toán
**100% thiệt hại đến từ NGUỒN** chứ không phải chế độ — năng lực không rõ chữa được cái đó.
Hàng 2 ~30% · hàng 1 ~15% · hàng 4 ~5% · HUỶ vì cổng năng lực ~**thực tế cao**, có thể 30–40%
(14B chỉ hơn 7B .0180).
**Tôi đang chạy một phép thử mà kết cục khả dĩ nhất là HUỶ** — nhưng đây là phản biện mạnh nhất
với kết quả chính, nên đáng chạy. Tỉ lệ prior đúng: **15/31**.

## BỔ SUNG #87-b — TÁCH "chữa được" khỏi "LỜ ĐI" (viết TRƯỚC khi H78 có số; H78 đang chạy)
**Phản biện của Nguyên:** *nếu khoảng cách năng lực quá lớn thì model mạnh chỉ tự làm hết,
nên `V → I` — và đó KHÔNG phải "năng lực chữa được đầu độc".*

**Đúng, và bảng #87 KHÔNG tách được hai cơ chế đó.** Hàng 1 (`poisoning(32B)` ≥ −.02) sẽ kích hoạt
trong CẢ HAI trường hợp:
- **(a) CHỮA ĐƯỢC** — model đọc lời giải yếu, không bị lừa, vẫn dùng được phần tốt.
- **(b) LỜ ĐI** — model bỏ qua đầu vào và tự giải lại, nên `V` trùng `I` theo mặc định.

**Chỉ số phân biệt (thêm vào, KHÔNG đổi ngưỡng nào):** tỉ lệ `V` trùng đáp án của **`I`**
so với trùng đáp án của **`S`**, tính theo từng bài.
Đã đo trên dữ liệu CÓ SẴN (H70c, MATH, verifier 7B): **trùng `I` 60.2% · trùng `S` 69.6% ·
đáp án thứ ba 18.6%** (nền: `I` và `S` tự trùng nhau 49.8%).
⇒ **Ở 7B model KHÔNG lờ đi — nó bám vào lời giải yếu NHIỀU HƠN bám vào đáp án của chính nó.**
Đó chính là lý do đầu độc tồn tại.

**Quy tắc đọc BỔ SUNG cho H78 (khoá trước):**
| nếu hàng 1 kích hoạt (`poisoning(32B)` ≥ −.02) VÀ… | kết luận |
|---|---|
| `agree(V,I)` tăng rõ theo năng lực **và** `agree(V,S)` giảm xuống gần nền | **(b) LỜ ĐI** — không phải "chữa được". Phát biểu đúng: *ở khoảng cách đủ lớn, model mạnh bỏ qua đầu vào, nên hợp tác trở nên VÔ NGHĨA chứ không phải có lợi.* |
| `agree(V,S)` vẫn cao (≥ nền + .10) mà `poisoning` vẫn ≈ 0 | **(a) CHỮA ĐƯỢC** — model vẫn đọc, vẫn bám, nhưng không còn bị kéo sai. Đây mới là "năng lực chữa được". |
| cả hai chỉ số đi ngang | không kết luận được cơ chế; chỉ báo số. |

**Hệ quả thực dụng nếu ra (b):** khuyến nghị không đổi — vẫn **gọi thẳng model mạnh**, vì
`V ≈ I` mà `V` **đắt hơn** (tốn thêm lượt 1.5B). "Hết hại" không có nghĩa là "có ích".
Ngưỡng và bảng #87 giữ NGUYÊN, đây chỉ là chỉ số chẩn đoán thêm.


# Đăng ký trước #88 — H79: **CẤU HÌNH ĐỊNH TUYẾN HỢP LÝ, trên tác vụ ĐỦ KHÓ cho 32B**
**Viết TRƯỚC khi chạy.** Hai phản biện của Nguyên, gộp thành một phép thử.

## Vì sao
1. **MATH-500 quá dễ cho 32B.** 7B đã đạt `.700` (#122) ⇒ cổng năng lực của H78 rất có thể trượt
   vì **trần**, không phải vì 32B kém. Cần tác vụ khó hơn: **BigCodeBench** (7B greedy ~.35 ở các
   vòng trước, lời giải chuẩn 466 ký tự, prompt 663 — khó hơn MBPP nhiều).
2. **Định tuyến của tôi tới giờ đều là kiểu rơm.** Mọi nhánh `V` là *"luôn luôn đưa cho model mạnh xem"* —
   không ai triển khai như thế. Cấu hình **thật** là **CHẤP NHẬN-hoặc-LEO THANG có điều kiện**,
   và đó cũng là kết quả dương DUY NHẤT về định tuyến của dự án (H39, vòng #78).

## Thiết kế — BigCodeBench (300 bài đầu), cheap = **7B**, strong = **32B**, bf16, RTX 6000
*(1.5B vô dụng trên BCB nên tầng rẻ phải là 7B — định tuyến chỉ hợp lý khi tầng rẻ dùng được)*

| nhánh | giao thức | chi phí (1.5B-eq; 7B=5.07, 32B=21.3) |
|---|---|---|
| `S` | 7B viết code | 5.07 |
| `I` | **32B viết code** (mốc đắt) | 21.3 |
| `V` | 32B **xem code 7B** rồi sửa (giao thức đã biết là hại) | 26.4 |
| **`ROUTE`** | 7B viết code **+ 7B tự viết test**; **ĐẠT test của chính nó → NHẬN**; **trượt → leo thang 32B** | 10.14 + `p_esc`×21.3 |
| `SEL` | 7B và 32B cùng viết; chọn bằng test tự sinh của 7B | 31.4 |

**Đại lượng CHÍNH: `ROUTE` so với `I`, KÈM chi phí.** Định tuyến chỉ có nghĩa nếu
**gần bằng `I` mà RẺ HƠN**. Báo `p_esc` (tỉ lệ leo thang) — nếu `p_esc` → 1 thì định tuyến
**suy biến thành "luôn gọi 32B"** và không tiết kiệm gì.

## NGƯỠNG HIỆU LỰC (khoá trước)
- **Cổng năng lực: `acc(I) − acc(S)` ≥ .05.** Nếu 32B không hơn 7B trên BCB thì tác vụ vẫn
  không phân giải được năng lực ⇒ HUỶ (và khi đó phản biện "MATH quá dễ" là **chưa đủ** —
  vấn đề nằm ở chỗ khác).
- `test_soundness` (lời giải chuẩn vượt test tự sinh của 7B) ≥ .50 · tỉ lệ biên dịch ≥ .50 · n ≥ 280.
- **Chống rò rỉ:** lượt viết test **KHÔNG** thấy `test` chính thức; chấm **chỉ** bằng `test` chính thức.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `ROUTE ≥ I − .02` **và** chi phí `ROUTE` < **0.80×** chi phí `I` | **ĐỊNH TUYẾN CÓ ĐIỀU KIỆN HOẠT ĐỘNG trên code khó.** H39 tổng quát từ toán sang code và lên tới 32B. Đây sẽ là kết quả **thực dụng** mạnh nhất của dự án. |
| `ROUTE ≥ I − .02` nhưng chi phí ≥ 0.80× `I` | **SUY BIẾN**: gần như luôn leo thang. Định tuyến "đúng" nhưng **không tiết kiệm** — trên tác vụ khó, tầng rẻ hiếm khi tự tin đúng. Báo `p_esc`. |
| `ROUTE < I − .02` | Định tuyến **mất chính xác**: test tự sinh của 7B **nhận nhầm** code sai. Báo số bài nhận nhầm. |
| `V − I` ≤ −.02 (lặp lại phát hiện chính ở 32B trên code khó) | Đầu độc **không rửa được bằng năng lực** ngay cả ở 32B trên tác vụ khó — bản mạnh nhất của kết quả chính. |
| `V − I` ≥ −.02 | Ở 32B trên code khó, đầu độc **biến mất** ⇒ kiểm ngay `agree(V,I)` vs `agree(V,S)` theo #87-b để tách **chữa được** khỏi **lờ đi**. |
| `SEL > I + .02` | Chọn vẫn thắng ở thang 32B. |
| cổng năng lực trượt | HUỶ, không đọc. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 2 (~45%)**: `ROUTE` ≈ `I` nhưng `p_esc` cao (≈.6–.75) nên **không tiết kiệm**.
Lý do: BCB khó, 7B chỉ ~.35, nên code của nó **trượt test của chính nó** ở phần lớn bài ⇒ leo thang gần như luôn.
Hàng 1 ~20% · hàng 3 ~20% · HUỶ vì cổng năng lực ~15%.
**Dự đoán phụ:** `V − I` vẫn ÂM ở 32B (~70%), vì cơ chế là *bị kéo vào chế độ sửa chữa*,
không phải thiếu năng lực. Tỉ lệ prior đúng: **15/31**.


# Đăng ký trước #89 — H80: **ĐA DẠNG HỌ MODEL vs ĐA DẠNG LẤY MẪU** (dự đoán 3 của TONG_HOP)
**Viết TRƯỚC khi chạy.** Đây là phép thử trực tiếp cho mệnh đề M2, và nó có thể **PHÁ** khung hợp nhất.

## Vì sao — và vì sao nó "ra ngoài hộp" so với mọi vòng trước
Toàn bộ dự án dùng **một họ model duy nhất (Qwen2.5)**. M2 nói giá trị của bộ chọn bị chặn bởi
**độ ĐỘC LẬP của lỗi**, và #117-b đo được 8 mẫu cùng model **đồng ý về đúng/sai ở 77.8%** số bài.
Nếu M2 đúng thì **ứng viên từ HỌ KHÁC phải nâng trần `H` nhiều hơn hẳn** cùng số ứng viên từ một họ.
Nếu KHÔNG — nếu đa dạng họ cũng chỉ ngang đa dạng lấy mẫu — thì **"lỗi tương quan" không phải
ràng buộc chặn**, và mệnh đề M2 (cùng lời giải thích cho #118/#120) phải **RÚT LẠI**.

## Thiết kế — MỘT kernel, ghép cặp hoàn hảo, CHI PHÍ KHỚP
MBPP 11–510, giao thức #74-c (`assert[0]` vào prompt, chấm `assert[1..2]`), bf16 trên RTX 6000.
Ba model **cùng cỡ (~7B), ba HỌ khác nhau**: `Q`=Qwen2.5-7B · `L`=Llama-3.1-8B · `D`=DeepSeek-Coder-6.7B.

| pool | ứng viên | chi phí |
|---|---|---|
| **A — đa dạng LẤY MẪU** | `Q₁` greedy, `Q₂` T=.8, `Q₃` T=.8 | 3 × ~7B |
| **B — đa dạng HỌ** | `Q₁` greedy, `L` greedy, `D` greedy | 3 × ~7B |

**Bộ chọn GIỮ NGUYÊN cho cả hai** (test tự sinh do **Q** viết, một lần) ⇒ khác biệt duy nhất
là **thành phần pool**. Báo cho mỗi pool: `acc` từng ứng viên · **trần `H`** (hợp) ·
`SEL` · **`κ` = tỉ lệ khai thác** · **phân bố số ứng viên đúng** (đo tương quan trực tiếp).

## NGƯỠNG HIỆU LỰC (khoá trước)
`test_soundness` ≥ .50 · `copy_rate` ≤ .20 · n = 500 · biên dịch ≥ .50 ·
**mỗi model phải đạt `acc` ∈ [.35, .80]** — nếu `L` hoặc `D` sụp dưới .35 thì pool B không phải
"đa dạng" mà là "một model hỏng" ⇒ HUỶ.

## Cam kết diễn giải (khoá TRƯỚC khi có số)
| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `H(B) − H(A)` ≥ **+.05** VÀ `SEL(B) − SEL(A)` ≥ **+.02** | **M2 ĐƯỢC XÁC NHẬN MẠNH.** Lỗi tương quan đúng là ràng buộc chặn; đa dạng HỌ là đòn bẩy rẻ hơn nhiều so với thêm mẫu. Khuyến nghị thực dụng thay đổi hẳn: **trộn họ model, đừng lấy thêm mẫu**. |
| `H(B) − H(A)` ≥ +.05 nhưng `SEL(B) − SEL(A)` < +.02 | Trần lên nhưng **bộ chọn không khai thác được** ⇒ `κ` giảm khi ứng viên đa dạng hơn. M2 đúng về `H`, sai về `κ`. Nút thắt quay về bộ chọn. |
| \|`H(B) − H(A)`\| < .05 | **M2 SAI hoặc yếu hơn tôi nghĩ ⇒ RÚT LẠI** lời giải thích "lỗi tương quan" ở #118/#120/TONG_HOP-M2. Lỗi của các model KHÁC HỌ cũng tương quan như mẫu cùng model — nghĩa là ràng buộc nằm ở **độ khó của BÀI**, không ở model. |
| `H(B) < H(A)` − .02 | Đảo ngược: trộn họ **hại** trần. Bất ngờ lớn, phải kiểm `acc` từng model trước khi tin. |
| `SEL(B) > H(A)` | Pool đa dạng vượt cả **trần** của pool cùng họ ⇒ kết quả rất mạnh, ghi rõ. |
| model nào `acc` < .35 | HUỶ. |

## Prior TRUNG THỰC (ghi trước)
Đoán **hàng 1 (~50%)**. Lý do: `D` là model **chuyên code**, kiến trúc và dữ liệu huấn luyện
khác hẳn Qwen ⇒ lỗi khó tương quan. Đoán `H(A)` ≈ .69 (từ #117: 8 mẫu Qwen cho trần .750,
3 mẫu sẽ thấp hơn), `H(B)` ≈ .76–.80.
Rủi ro ghi trước: **`κ` có thể tụt mạnh** ở pool B vì test do **Q** viết có thể thiên vị code kiểu Q
— nếu vậy ra hàng 2, và đó cũng là phát hiện đáng giá (bộ chọn cũng phải độc lập với **họ**).
Hàng 2 ~25% · hàng 3 ~20% · hàng 4 ~5%. Tỉ lệ prior đúng: **15/31**.


# Đăng ký trước #90 — H81: **BỘ CHỌN có cần ĐỘC LẬP VỀ HỌ không?** (dự đoán 1 của TONG_HOP)
M2 nói `κ` bị chặn bởi độ độc lập của tín hiệu. Test tự sinh hiện do **chính Qwen** viết —
lỗi của nó có thể tương quan với lỗi code của Qwen. Nếu M2 đúng, **test do HỌ KHÁC viết phải chọn TỐT HƠN**.
**Thiết kế:** MBPP 11–510, ứng viên **cố định** = {Q1 greedy, Q2 T=.8}; đổi **duy nhất** người viết test:
`T_self` (Qwen) vs **`T_other` (DeepSeek-Coder)**. Cùng ứng viên, cùng bài ⇒ ghép cặp hoàn hảo.
**Cổng:** soundness ≥ .50 cả hai · copy_rate ≤ .20 · n=500.
| Kết quả | Kết luận |
|---|---|
| `SEL(T_other) − SEL(T_self)` ≥ **+.02** | **M2 XÁC NHẬN ở phía bộ chọn.** Tín hiệu phải độc lập về HỌ, không chỉ về mẫu. |
| \|chênh\| < .02 | Độc lập về họ **không** cải thiện `κ` ⇒ M2 chỉ đúng cho pool, không cho tín hiệu. Thu hẹp. |
| chênh ≤ −.02 | Test của họ khác **tệ hơn** ⇒ `κ` phụ thuộc **khớp phong cách**, ngược M2. Rút lại phần κ. |
| `soundness(T_other)` < .50 | HUỶ nhánh đó (DeepSeek có thể viết test kém). |
**Prior:** hàng 1 ~40%, hàng 2 ~35%, hàng 3 ~25%. Rủi ro: DeepSeek-Coder viết test **kém hơn** về
soundness, làm nhiễu phép so. **Tỉ lệ prior đúng: 15/31.**

# Đăng ký trước #91 — H82: **"CHỌN hơn REVIEW" trên TOÁN** (chạy lại H77, đã chết ở tường 12h)
H77 mất 12h vì `k=8` + lưu-từng-phần rỗng. **Sửa: `k=4`, lưu `raw` thật sau MỖI mẫu.**
MATH-500, `MAXNEW`=1280 + cổng cắt ngắn #84. `I` · `V_review` · `maj@2/4`.
| Kết quả | Kết luận |
|---|---|
| `maj@4 − V_review` ≥ **+.05** | **"CHỌN hơn REVIEW" TỔNG QUÁT sang toán** — không phụ thuộc oracle chạy được. |
| +.02 ≤ chênh < +.05 | đúng chiều, yếu hơn code (+.084…+.130); nêu cả hai. |
| \|chênh\| < .02 | **KHÔNG tổng quát** ⇒ phát biểu trung tâm chỉ về CODE. Thu hẹp TONG_HOP-M1. |
| `maj@4 − I` < .02 | bỏ phiếu đa số không giúp trên toán ⇒ củng cố lỗi tương quan là hiện tượng chung. |
| cổng cắt ngắn trượt | HUỶ. |
**Prior:** hàng 1 ~55% (`V_review` trên MATH = −.1260 nên khoảng cách dễ vượt). **15/31.**

# Đăng ký trước #92 — H83: **ĐIỂM THỨ BA cho công thức định tuyến** (dự đoán 4)
Công thức: hoà vốn khi `p_esc < 1 − chi_phí_rẻ/chi_phí_đắt`. Đã khớp 2/2
(MATH 1.5B→7B: ngưỡng .803, thực .625 → thắng · BCB 7B→32B: ngưỡng .762, thực .887 → thua).
**Điểm thứ ba: MBPP, 1.5B→7B** ⇒ ngưỡng `1 − 1/5.07` = **.803**.
| Kết quả | Kết luận |
|---|---|
| `p_esc` < .803 **và** `ROUTE ≥ I − .02` **và** chi phí < `I` | **CÔNG THỨC ĐÚNG 3/3** — dùng được để dự đoán trước khi chạy. |
| `p_esc` ≥ .803 **và** `ROUTE` đắt hơn `I` | cũng khớp công thức (dự đoán thua, thua thật). |
| `p_esc` < .803 nhưng `ROUTE < I − .02` | công thức đúng về CHI PHÍ, sai về ĐỘ CHÍNH XÁC ⇒ cần thêm số hạng. |
| dự đoán ngược thực tế | **RÚT LẠI công thức M3.** |
**Prior:** `p_esc` ≈ .55–.70 (MBPP dễ hơn BCB), tức **thắng** — hàng 1 ~55%. **15/31.**

# Đăng ký trước #93 — H84: **ĐẦU ĐỘC là do CHÊNH NĂNG LỰC hay do VĂN BẢN NGOẠI LAI?**
Mọi phép đo đầu độc đều dùng nguồn **yếu hơn**. Chưa tách được hai giả thuyết:
(a) hại vì lời giải **SAI nhiều**, (b) hại vì nó **của model KHÁC**.
**Thiết kế:** MBPP, verifier = Qwen2.5-7B. Nguồn: `S_weak` = 1.5B (**yếu hơn**) vs
**`S_peer` = Llama-3.1-8B (CÙNG CỠ, khác họ)**. Cùng verifier, cùng bài.
| Kết quả | Kết luận |
|---|---|
| `V(S_peer) − I` ≤ **−.02** | **ĐẦU ĐỘC KHÔNG CẦN CHÊNH NĂNG LỰC** — văn bản ngoại lai tự nó gây hại. Phát biểu mạnh hơn nhiều. |
| `V(S_peer) − I` ≥ −.02 mà `V(S_weak) − I` ≤ −.05 | Đầu độc **cần** nguồn yếu ⇒ (a) đúng, thu hẹp phát biểu về "nguồn KÉM", không phải "nguồn NGOẠI LAI". |
| cả hai ≈ 0 | không tái lập được đầu độc trong lần chạy này ⇒ HUỶ, kiểm lại thiết lập. |
**Prior:** hàng 1 ~45%. Lý do: #104 cho thấy cho xem lời giải **ĐÚNG** vẫn giúp (+.042), nên
"sai" là yếu tố lớn — nhưng 78% thiệt hại là **viết lại**, mà viết lại không cần nguồn sai. **15/31.**

# Đăng ký trước #94 — H85: **REFACTOR: CHỌN vs SỬA** (chạy lại H63, đã mất ~15h)
H63 chết ở tường 12h **không lưu gì**. **Sửa: k=8→4, lưu `raw` sau mỗi nhánh, n=267 (đã lọc).**
BigCodeBench (dataset đã stage), 7B nf4. `ref1` · `ref_exec3` (sửa) · **`ref_sel4`** (chọn bản
ít nút AST nhất trong 4 bản GIỮ ĐƯỢC hành vi).
**Thước đo (khoá #58):** `good_refactor` = preserve ∧ simpler. **Báo `preserve` KÈM `good`.**
| Kết quả | Kết luận |
|---|---|
| `good(sel4) − good(exec3)` ≥ **+.08** | **CHỌN thắng SỬA trên refactor** — quy tắc tổng quát từ SINH sang BIẾN ĐỔI. |
| +.02 ≤ chênh < +.08 | hơn nhưng khiêm tốn; nêu chi phí 4 lượt vs ≤4 lượt. |
| \|chênh\| < .02 | **CHỌN không tổng quát sang refactor** ⇒ nút thắt là **giữ ngữ nghĩa**, không phải chọn ứng viên. |
| `preserve(ref1)` ngoài [.70,.85] | HUỶ (không tái lập được H52/H53). |
**Prior:** hàng 1 ~45% (H53 cho SỬA chỉ +1.9 điểm, còn CHỌN chưa ai thử). **15/31.**


# Đăng ký trước #95 — H86: **TÁI LẬP H80 trên dải bài TÁCH RỜI**
**Viết TRƯỚC khi chạy.** H80 là kết quả dương **mạnh nhất** của dự án
(`H` +.0500 p=6.2e-4 · `SEL` +.0320 p=7.0e-3). Quy tắc dự án: **chưa tái lập thì chưa vào README**,
và H73b đã cho thấy một "bản tái lập" chạy nhầm dải trông y như thật.

**Thiết kế:** Y HỆT H80, đổi DUY NHẤT dải task_id → **MBPP 511–974** (không giao với 11–510).
**Bắt buộc xác minh `task_id` min/max trong trace TRƯỚC khi đọc số** (bài học #121).

**Cổng:** soundness ≥ .50 · copy_rate ≤ .20 · n ≥ 400 · mọi model `acc` ∈ [.35,.85].

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `H(B) − H(A)` ≥ **+.03** VÀ `SEL(B) − SEL(A)` ≥ **+.015** | **TÁI LẬP.** Đa dạng họ là đòn bẩy thật; đưa vào README kèm cả hai lần đo và cả hai p. |
| `H(B) − H(A)` ≥ +.03 nhưng `SEL` không tái lập | Trần tái lập, khai thác thì không ⇒ `κ` không ổn định. Báo cả hai. |
| \|`H(B) − H(A)`\| < .03 | **KHÔNG tái lập ⇒ HẠ CẤP H80** xuống "chưa xác lập". M2 mất chỗ dựa thực nghiệm mạnh nhất. |
| `H(B) < H(A)` | **ĐẢO DẤU ⇒ RÚT LẠI H80.** |
| số bài **hỗn hợp** ở pool B KHÔNG cao hơn pool A rõ rệt | Cơ chế "giải tương quan" không tái lập ⇒ ghi rõ dù biên độ acc có tái lập. |
| `task_id` không nằm trong 511–974 | **HUỶ** — chạy nhầm dải (lỗi #121). |

**Prior:** tái lập ~75%. Cơ chế (hỗn hợp 57→167) quá mạnh và quá cơ học để là nhiễu;
nhưng biên độ có thể nhỏ hơn vì dải 511–974 có `acc` nền cao hơn (H69d: `I` = .7069)
⇒ ít dư địa. Đoán `H` +.03..+.05. **Tỉ lệ prior đúng: 16/32.**


# Đăng ký trước #96 — H87: **MODEL YẾU-KHÁC-HỌ có còn đóng góp khi đã có model MẠNH?**
**Viết TRƯỚC khi chạy.** Mở rộng H80 (#131) sang trường hợp **lệch năng lực lớn** — câu hỏi thực dụng nhất.

H80: thêm Llama-8B (.540, **yếu nhất**) vào pool Qwen-7B vẫn nâng `H` +.0500, `SEL` +.0320.
Nhưng cả ba **ngang cơ**. Câu hỏi của người triển khai:
> *"Đã có 32B. Thêm vài model 7B rẻ khác họ có còn được gì, hay chênh năng lực nuốt hết đa dạng?"*

## Thiết kế — RTX 6000, MBPP 11–510, bộ chọn GIỮ NGUYÊN (test do 32B viết một lần)
| pool | ứng viên | chi phí (1.5B-eq) |
|---|---|---|
| **A** | 32B greedy | 21.3 |
| **B** | 32B + 32B(T=.8) | 42.6 |
| **C** | **32B + Llama-8B + DeepSeek-6.7B** | **31.2** ← rẻ hơn B, thêm HAI ứng viên |

## NGƯỠNG (khoá trước)
soundness ≥ .50 · copy_rate ≤ .20 · n=500 · `acc(32B)` ∈ [.60,.90] · `acc(L)`,`acc(D)` ≥ .35 ·
tỉ lệ có ```python block ≥ .90 mọi nhánh (bài học #130).

| Kết quả | Kết luận BẮT BUỘC |
|---|---|
| `SEL(C) − SEL(A)` ≥ **+.02** VÀ `SEL(C) ≥ SEL(B) − .01` | **M2 DẠNG MẠNH ĐÚNG.** Model yếu-khác-họ vẫn đóng góp bên cạnh model mạnh, **rẻ hơn** thêm mẫu. Khuyến nghị triển khai rõ ràng. |
| `SEL(C) − SEL(A)` ≥ +.02 nhưng `< SEL(B) − .01` | Có đóng góp nhưng thua thêm mẫu ⇒ đa dạng họ chỉ thắng **giữa model NGANG CƠ**. Thu hẹp H80. |
| \|`SEL(C) − SEL(A)`\| < .02 | **Chênh năng lực NUỐT đa dạng** ⇒ M2 chỉ đúng giữa model ngang cơ. Thu hẹp mạnh ở TONG_HOP. |
| `SEL(C) < SEL(A)` − .02 | Thêm model yếu **HẠI** khi đã có model mạnh; đối chiếu #118. |
| `H(C) > H(B)` mà `SEL(C) < SEL(B)` | `κ` tụt khi pool lệch năng lực ⇒ nút thắt là bộ chọn. |

**Prior:** hàng 1 ~40%, **kém tự tin hơn H80**: 32B mạnh hơn Llama-8B nhiều (đoán .78 vs .54)
nên số bài Llama đúng mà 32B sai sẽ ít hơn hẳn 38 bài của H80.
Hàng 2 ~25% · hàng 3 ~25% · hàng 4 ~10%. **Tỉ lệ prior đúng: 16/32.**

---

## #97 — H88: SỬA CÓ CỔNG — `D` có biến mất khi cổng bằng tín hiệu độc lập không?

**Đăng ký lúc:** trước khi phóng H88/H88b/H88c. **Chưa nhìn bất kỳ số nào.**

### Câu hỏi
M1 nói `D > 0` vì `M` **ghi đè lên artifact vốn đã đúng**. Nếu vậy thì chặn nó ghi đè ở đúng
những bài đó phải khử được `D`. Chưa ai kiểm điều này — mọi vòng trước chỉ so **sửa vô điều kiện**
với **chọn**, chưa bao giờ thử **sửa CÓ ĐIỀU KIỆN**.

### Thiết kế
MBPP, `S` = Qwen2.5-1.5B, `M` = Qwen2.5-7B. Sinh **một lần** rồi ghép nhánh **offline** —
nên các nhánh dùng **cùng** artifact, không có nhiễu lấy mẫu giữa nhánh.

| nhánh | định nghĩa | chi phí |
|---|---|---|
| `S` | 1.5B tự giải | 1 |
| `I` | 7B tự giải, **không thấy gì** | `c` |
| `V` | 7B **xem** lời giải của `S` rồi sửa (vô điều kiện) | 1+`c` |
| `z` | test do `S` tự viết, **chạy thật** trên lời giải của `S` | ~0 |
| `G_V` | `z` đạt → **giữ `S`**; `z` trượt → lấy `V` | 1+`c`·`p_esc` |
| `G_I` | `z` đạt → **giữ `S`**; `z` trượt → lấy `I` (không cho thấy artifact) | 1+`c`·`p_esc` |
| `G*_V` | **cổng ORACLE**: `S` đúng thật → giữ `S`; sai → lấy `V` | (không khả thi) |

`G*_V` không phải một hệ thống — nó là **CHẶN TRÊN**. Nó tách bạch "tín hiệu của ta kém"
khỏi "chẳng có gì để khai thác".

### Đại lượng
- `Δ_gate  = acc(G_V) − acc(V)`   — cổng có cứu được sửa khỏi chính nó?
- `Δ_honest= acc(G_V) − acc(I)`   — cứu rồi thì có **thắng mốc thật** không?
- `Δ_cont  = acc(G_I) − acc(G_V)` — dưới cổng, **cho thấy artifact** còn hại nữa không?
- `Δ_ceil  = acc(G*_V) − acc(I)`  — chặn trên của cả dòng sửa-có-cổng

### BẢNG KHOÁ (đọc theo thứ tự; hàng đầu tiên khớp là kết luận)

| # | điều kiện | KẾT LUẬN ĐƯỢC PHÉP VIẾT |
|---|---|---|
| 0 | **CỔNG CHẤT LƯỢNG** trượt (xem dưới) | **VOID** — không đọc số nào |
| 1 | `Δ_ceil ≤ 0` (McNemar p<.05 hoặc CI chứa 0 với \|Δ\|<.02) | **GIẾT CẢ DÒNG SỬA.** Ngay cả cổng ORACLE cũng không vượt `I` ⇒ không có gì để khai thác; mọi nỗ lực cải thiện tín hiệu cổng là vô ích. Ghi vào TONG_HOP như **kết quả chặn trên**. |
| 2 | `Δ_ceil > 0` và `Δ_gate ≥ +.04` (p<.05) và `Δ_honest ≥ +.02` (p<.05) | **M1 CHO RA ĐƠN THUỐC DÙNG ĐƯỢC**: sửa an toàn khi và chỉ khi có cổng độc lập. Kết quả dương đầu tiên của dòng sửa. |
| 3 | `Δ_ceil > 0` và `Δ_gate ≥ +.04` (p<.05) nhưng `Δ_honest ≤ 0` | Cổng **khử được `D`** nhưng `κ = 0`: cứu `V` khỏi chính nó mà vẫn không bằng chỉ gọi `M` một lượt. **M1 đúng về cơ chế, sai về giá trị.** |
| 4 | `Δ_ceil > 0` nhưng `Δ_gate < +.04` | **M1 SAI NHƯ ĐANG PHÁT BIỂU.** Có chỗ để khai thác (`Δ_ceil>0`) nhưng chặn ghi đè ở tập cổng-đạt **không** cứu được ⇒ phá hoại **không** nằm ở những bài `S` làm đúng. Phải viết lại M1. |
| 5 | bất kỳ hàng nào trên **và** `Δ_cont < −.02` (p<.05) | **cộng thêm**: ngay cả dưới cổng, **cho `M` thấy artifact vẫn nhiễm độc** ⇒ củng cố #119. |

### CỔNG CHẤT LƯỢNG (kiểm TRƯỚC khi đọc bảng)
1. tỉ lệ trích được code chạy `≥ .80` ở **mọi** nhánh, chênh giữa nhánh cao nhất/thấp nhất `< .05`
2. `n ≥ 480` bài qua lọc
3. `p_esc` (tỉ lệ `z` trượt) nằm trong `[.15, .90]` — ngoài dải này cổng suy biến, nhánh `G` bằng `S` hoặc bằng `V`
4. tỉ lệ test tự sinh **chạy được** `≥ .70`

### TIÊN NGHIỆM THÀNH THẬT
Hàng 3 **~50%** · hàng 1 **~20%** · hàng 4 **~20%** · hàng 2 **~10%**.
Tôi cho rằng cổng sẽ khử phần lớn `D` (cơ chế M1 đúng) nhưng `G_V` vẫn **không** vượt `I`,
vì mọi vòng trước cho thấy `κ` của giao thức sửa bằng 0 — sửa không **chọn** gì cả.
Hàng 1 đáng kể vì `acc(I)` đã cao hơn `acc(S)` tới +.2120: tập bài `S` đúng mà `I` sai có thể quá nhỏ.

### Tái lập dựng sẵn
`H88` = MBPP 11–510 · `H88b` = MBPP 511–974 (**dải tách rời**) · `H88c` = MATH-500 (khác miền).
Kết luận chỉ vào TONG_HOP nếu **H88 và H88b khớp hàng**.

---

## #98 — H89: PHÁ HOẠI CÓ PHỤ THUỘC HỌ MODEL KHÔNG?

**Đăng ký lúc:** trước khi phóng H89/H89b/H89c. **Chưa nhìn số nào.**

### Câu hỏi
TONG_HOP mục 1 kết luận thiệt hại **100% đến từ NGUỒN NGOẠI LAI** (trên MATH: `V_self` = +.0020
vô hại, `V_weak` = −.1260). Nhưng "ngoại lai" ở đó chỉ có nghĩa **model khác kích cỡ, CÙNG họ
Qwen2.5**. Nếu cơ chế thật sự là "nguồn lạ" thì đổi sang **model khác HỌ** — nguồn lạ tối đa —
phải làm `D` **lớn hơn**. Đây là dự đoán **có hướng**, nên nó **có thể sai**.

Đồng thời vá được điểm yếu tự thú ở TONG_HOP mục 4: *"mọi thứ ở một họ model (Qwen2.5)"*.

### Thiết kế
Giữ **nguyên** `S` = Qwen2.5-1.5B, **nguyên** giao thức, **nguyên** dải bài, **nguyên** MBPP.
Chỉ đổi **một biến**: họ của model đắt `M`.

| chạy | `M` | họ | dải |
|---|---|---|---|
| (đã có, H88) | Qwen2.5-7B | **cùng họ** | 11–510 |
| `H89` | Llama-3.1-8B | khác họ | 11–510 |
| `H89b` | DeepSeek-Coder-6.7B | khác họ, **chuyên code** | 11–510 |
| `H89c` | Llama-3.1-8B | khác họ | 511–974 (tái lập) |

Mốc đã khoá để so: `V − I` nội họ Qwen trên MBPP = **−.0740**.

### CỔNG CHẤT LƯỢNG (kiểm TRƯỚC khi đọc) — thêm vào 5 cổng của #97
6. **`I − S ≥ .05`** — nếu `M` khác họ không thật sự mạnh hơn `S`, `V − I` vô nghĩa. VOID.

### BẢNG KHOÁ (hàng đầu tiên khớp là kết luận)

| # | điều kiện | KẾT LUẬN ĐƯỢC PHÉP VIẾT |
|---|---|---|
| 0 | cổng chất lượng trượt | **VOID** — không đọc số nào |
| A | `V−I ≤ −.104` (tức âm hơn mốc ≥ .03) và p<.05 | **Cơ chế "nguồn lạ" ĐƯỢC CỦNG CỐ**: nguồn càng lạ, phá càng mạnh. `D` là hàm tăng theo khoảng cách phân phối giữa nguồn và người sửa. |
| B | `\|V−I −(−.0740)\| < .03` và `V−I < −.02` | **Phá hoại KHÔNG phụ thuộc họ.** "Nguồn lạ" không phải chuyện HỌ MODEL mà là chuyện artifact **của người khác**. Phải phát biểu lại cơ chế trong TONG_HOP. |
| C | `V−I ≥ −.02` | **Đầu độc BIẾN MẤT khi đổi họ** ⇒ kết quả trung tâm của cả dự án **chỉ đúng trong họ Qwen**. Phải thu hẹp phạm vi mọi phát biểu. **Đây là hàng giết giả thuyết.** |
| D | còn lại (âm nhưng yếu hơn rõ rệt) | phá hoại **giảm** khi đổi họ — ngược dự đoán A, ghi nhận nhưng chưa đủ mạnh để kết luận C. |

### TIÊN NGHIỆM THÀNH THẬT
Hàng B **~45%** · hàng A **~25%** · hàng D **~20%** · hàng C **~10%**.
Tôi nghiêng về B: cơ chế đọc từ trace ở #119 là `M` **viết lại** khi được lệnh "review" — hành vi
đó do **prompt** gây ra, không do nguồn thuộc họ nào. Hàng A đòi hỏi `M` phải "khó chịu" với code
lạ theo mức độ định lượng được, điều chưa có bằng chứng nào.
**Rủi ro đã biết:** DeepSeek-Coder chuyên code nên `I − S` có thể rất lớn, đẩy `V − I` theo hướng
khác vì lý do năng lực chứ không vì họ — nên H89b đọc **kèm** `I − S`, không đọc rời.

### Tái lập
Kết luận chỉ vào TONG_HOP nếu **H89 và H89c khớp hàng** (cùng `M`, hai dải tách rời).

---

## #97-b — SỬA ĐỔI cho H88c (MATH): định nghĩa `z` mà #97 còn thiếu

**Đăng ký lúc:** trước khi phóng H88c. Đây là **sửa đổi công khai**, không phải diễn giải lại.

### Vì sao phải sửa đổi
#97 định nghĩa cổng `z` = *"test do `S` tự viết, **chạy thật**"*. Trên MATH **không có gì để chạy**.
Nên dòng "H88c = MATH-500" trong #97 **thiếu định nghĩa** — nếu tôi cứ chọn một `z` nào đó sau khi
đã thấy dữ liệu thì đó đúng là post hoc. Khoá lại ngay bây giờ.

### `z` cho MATH
`z` = **tự nhất quán k=2**: `S` giải lần 1 (greedy) và lần 2 (nhiệt độ 0.8, hạt cố định);
`z` ĐẠT ⟺ hai đáp án chuẩn hoá **trùng nhau**.

### Hệ quả PHẢI thừa nhận trước
`z` này **TƯƠNG QUAN** với lỗi của `S` — cùng một model, M2 đã đo: 8 mẫu cùng model có 25.0%
**cùng SAI**. Vậy M2 **dự đoán trước** rằng cổng này sẽ bắt kém. Nếu H88c ra `κ` thấp thì
**KHÔNG được đọc thành "cổng không hoạt động trên toán"** — nó chỉ tái xác nhận M2.

### Vì thế H88c đổi thứ tự đọc

| | đại lượng | vì sao đọc được |
|---|---|---|
| **CHÍNH** | `Δ_ceil = acc(G*_V) − acc(I)` | cổng **ORACLE** — **không phụ thuộc** chất lượng `z`. Trả lời: trên MATH **có gì để khai thác không**? |
| phụ (thăm dò) | `Δ_gate`, `Δ_honest` với `z` tự nhất quán | chỉ đọc **kèm** cảnh báo tương quan ở trên |

**Chỉ hàng 0 và hàng 1 của bảng khoá #97 được áp cho H88c.** Hàng 2/3/4 nói về cổng khả thi
nên **không** áp cho một `z` đã biết trước là tương quan.

### CỔNG CHẤT LƯỢNG (thay cổng code của #97)
1. tỉ lệ có `\boxed` `≥ .80` ở **mọi** nhánh, chênh `< .05` (cổng cắt cụt #84 — bài học #119/#130)
2. `MAXNEW = 1280`
3. `n ≥ 450` · 4. `.15 ≤ p_esc ≤ .90`

### TIÊN NGHIỆM
`Δ_ceil > 0` rõ rệt trên MATH: **~70%** (vì `I − S` trên MATH lớn, còn tập "S đúng mà I sai" thì
nhỏ — nhưng `acc(S)` thấp nên vẫn còn chỗ). Cổng khả thi cho `κ` gần 0: **~75%**.

---

## #99 — ĐỘ ĐA DẠNG VỀ CHUỖI: cơ chế của M2 ở tầng DƯỚI kết quả

**Đăng ký lúc:** H86c **đang chạy**, tôi **chưa có** bất kỳ số nào của nó. Vòng #136 đo đại lượng
này trên Pool A của H86b (thăm dò, hậu nghiệm). Đăng ký này khoá nó lại **trước** khi mở H86c,
để nó trở thành **xác nhận** thay vì kể chuyện.

### Vì sao đáng đăng ký riêng
M2 nói bộ chọn bị chặn bởi **độ độc lập** của tín hiệu, và lỗi các mẫu cùng model thì **tương quan**.
#136 (thăm dò) cho thấy phần lớn "tương quan" ấy có thể là dạng cực đoan nhất: **cùng một chuỗi**
— 3 mẫu Qwen chỉ cho **1.933/3** ứng viên phân biệt, **34.5%** số bài chỉ có **một**.
Nếu đúng, M2 có một cơ chế **đo được mà không cần chấm điểm** — mạnh hơn nhiều so với chỉ nói
"lỗi tương quan".

### Đại lượng (đo trên CÙNG bộ bài, CÙNG lần chạy H86c)
`distinct(P)` = số ứng viên **phân biệt về chuỗi** trung bình trong pool `P`, sau chuẩn hoá
**đã cố định ở #136**: bỏ chú thích `#...`, gộp mọi khoảng trắng, so khớp chính xác.
- `dA` = pool **lấy mẫu** (Q1, Q2, Q3 — cùng Qwen-7B)
- `dB` = pool **khác họ** (Qwen, Llama, DeepSeek)
- `Δd = dB − dA` · `soloA`, `soloB` = tỉ lệ bài chỉ có **MỘT** ứng viên phân biệt

### BẢNG KHOÁ

| # | điều kiện | KẾT LUẬN ĐƯỢC PHÉP VIẾT |
|---|---|---|
| 0 | H86c VOID theo cổng của #89 | **VOID** — không đọc |
| 1 | `Δd ≥ +0.50` **và** `soloB ≤ soloA − .15` | **M2 có cơ chế ở tầng chuỗi.** Pool cùng model tương quan tới mức **trùng nguyên văn**; pool khác họ mua được ứng viên thật. Ghi vào TONG_HOP như cơ chế của `κ`. |
| 2 | `+0.20 ≤ Δd < +0.50` | đa dạng khác họ **cao hơn nhưng khiêm tốn**; trùng-nguyên-văn **không** phải lời giải thích chính. Nêu kèm, không nâng thành cơ chế. |
| 3 | `\|Δd\| < 0.20` | **GIẾT giả thuyết này.** Pool khác họ **không** đa dạng hơn về chuỗi ⇒ nếu H86c vẫn cho `H(B) > H(A)` thì lợi ích đến từ **chất lượng/bổ trợ**, KHÔNG phải từ đa dạng bề mặt. #136 chỉ là chuyện bên lề. |
| 4 | `Δd ≤ −0.20` | ngược hẳn dự đoán — pool khác họ **kém** đa dạng hơn. Phải điều tra lại chính cách đo. |

### TIÊN NGHIỆM THÀNH THẬT
Hàng 1 **~55%** · hàng 2 **~30%** · hàng 3 **~13%** · hàng 4 **~2%**.
Ba model khác nhau gần như chắc chắn không sinh ra **cùng một chuỗi**, nên `dB` sát 3.0 là hợp lý
(⇒ `Δd ≈ +1.0`). **Rủi ro thật nằm ở chỗ khác**: `Δd` lớn có thể **tầm thường** — model khác nhau
thì code khác nhau, điều đó **không** tự động nghĩa là chúng đúng/sai độc lập. Vì thế hàng 1 chỉ
được viết khi **kèm** `soloB` giảm rõ; và mọi phát biểu về **`κ`** vẫn phải dựa trên `H` và `SEL`
của #89, **không** dựa vào riêng `Δd`.

---

## #97-c — SỬA ĐỔI: cổng trích xuất của #97 đo SAI thứ nó viết ra

**Đăng ký lúc:** sau khi H88/H88b **VOID**, **TRƯỚC** khi chạy lại. **Tôi CHƯA đọc `d_gate`,
`d_honest`, `d_cont`, `d_ceil` hay bất kỳ `acc` nào của H88/H88b** — và sẽ không đọc.

### Chuyện đã xảy ra
#97 viết cổng là: *"tỉ lệ **trích được code chạy** ≥ .80 ở mọi nhánh, chênh < .05"*.
Kernel lại cài đặt bằng `has_block()` — **có hàng rào ```python hay không**. Hai thứ khác nhau.

| nhánh | `has_block` (đã cài) | `compiles(extract(·))` (đã VIẾT) |
|---|---|---|
| `S` (1.5B) | **.1383** | **.9980** |
| `I` (7B) | 1.0000 | .9940 |

Model yếu **không rào code bằng markdown**; nhưng `extract()` có đường lui lấy toàn văn, và
code đó **biên dịch được 99.8%**. Cổng đã bắt một **thói quen định dạng**, không phải một
**mối đe doạ tới tính hợp lệ**.

### Vì sao vẫn VOID mà KHÔNG đọc số
Cổng **đã cài** trượt. Đổi sang thước đo mà tôi **biết là sẽ đạt**, **sau khi** thấy thước đo kia
trượt, chính là sai phạm ở **#114** mà kiểm định #125-C đã bắt. Lý lẽ hay không làm nó bớt sai.
**H88 và H88b VOID vĩnh viễn. Số của chúng không bao giờ được trích.**

### Cổng cho lần chạy lại (H88d / H88e) — khoá lại tại đây
1. **`compiles(extract(t)) ≥ .80` ở MỌI nhánh** và **chênh < .05** ← đúng chữ của #97
2. `n ≥ 480` (H88b được 463 ⇒ **nới dải lấy bài, KHÔNG hạ ngưỡng** — bài học #127: dùng
   MBPP 511–**1000** để bù phần bị lọc)
3. `.15 ≤ p_esc ≤ .90`
4. **`test_runnable ≥ .60`** (đo được .6994/.6739; ngưỡng .70 cũ là tôi đoán, không có cơ sở)
   — **đây là NỚI ngưỡng, phải nói thẳng.** Lý do: đại lượng này chỉ mô tả **cổng `z` mạnh cỡ nào**,
   nó **không** đe doạ tính hợp lệ của so sánh; và `d_ceil` (cổng ORACLE) **không phụ thuộc** vào `z`.
   Nếu ai không đồng ý với việc nới này thì **chỉ đọc `d_ceil`**, đại lượng không dính tới `z`.
5. **`has_block` vẫn được BÁO CÁO** như số mô tả — không còn là cổng.

### Bảng khoá: **GIỮ NGUYÊN #97**, không sửa một chữ.

---

## #101 — H91: SỬA CÓ CỔNG **ở 32B** (điểm 32B đầu tiên của dự án)

**Đăng ký lúc:** trước khi phóng. TONG_HOP mục 4 tự thú: *"không có điểm nào ở 32B trở lên —
hai lần HUỶ vì hạ tầng (#123, #130), chưa vì khoa học"*. #139 vừa HUỶ lần thứ ba (soundness).

### Vì sao thiết kế NÀY cho khe RTX, chứ không phải chạy lại H87
`H87` phụ thuộc **soundness của test do model viết** — đại lượng đã trượt (.4509) và suýt trượt
(.533) hai lần liên tiếp. Chạy lại nó mà chưa sửa được soundness là **đánh cược tài nguyên khan
hiếm nhất vào đúng thứ vừa hỏng hai lần**.

Thiết kế `gated_repair` có **đại lượng CHÍNH `Δ_ceil` = `acc(G*_V) − acc(I)`** dùng **cổng ORACLE**
(giữ `S` khi `S` ĐÚNG THẬT). Nó **không phụ thuộc chút nào** vào chất lượng test. Nên khe RTX
sinh ra kết quả đọc được **bất kể** soundness ra sao.

### Thiết kế
Y hệt #97 (H88), đổi **duy nhất** cặp model: `S` = **Qwen2.5-7B** · `M` = **Qwen2.5-32B** (bf16,
95 GB đủ). MBPP 11–510. `MAXNEW` = 768 (mã ngắn hơn văn xuôi toán; #130 là bài học của MATH).

### CỔNG (mỗi hàng nêu CẢ hiệu ứng LẪN ý nghĩa — luật mới #140)
1. `compiles(extract(t)) ≥ .80` mọi nhánh, chênh **< .05** (đúng chữ #97, đã sửa ở #97-c)
2. `n ≥ 480` · 3. `.15 ≤ p_esc ≤ .90`
4. **`I − S ≥ .05` VÀ p < .05** ← #141: Llama-8B trượt đúng cổng này; đừng giả định model to là mạnh

### BẢNG KHOÁ (đọc theo thứ tự)

| # | điều kiện | KẾT LUẬN |
|---|---|---|
| 0 | cổng trượt | **VOID** |
| 1 | `Δ_ceil ≤ 0` **hoặc** (p ≥ .05 và \|Δ_ceil\| < .02) | **GIẾT DÒNG SỬA Ở MỌI QUY MÔ.** Ngay ở 32B, cổng ORACLE cũng không vượt `I` ⇒ không có gì để khai thác từ artifact của model yếu hơn. Kết quả 32B đầu tiên, và là kết quả **mạnh**. |
| 2 | `Δ_ceil ≥ +.02` và p < .05 và `Δ_honest ≥ +.02` và p < .05 | sửa **CÓ CỔNG** thắng mốc thật ở 32B ⇒ quy mô **cứu** được dòng sửa. Trái ngược tiên nghiệm. |
| 3 | `Δ_ceil ≥ +.02` và p < .05 nhưng `Δ_honest` không đạt | có chỗ khai thác nhưng **cổng khả thi không lấy được** ⇒ nút thắt là `κ`, đúng M2, **ở quy mô 32B**. |
| 4 | `Δ_ceil` đạt nhưng `Δ_gate < 0` và p < .05 | cổng làm **hỏng** so với sửa vô điều kiện — phải viết lại M1. |

### TIÊN NGHIỆM THÀNH THẬT
Hàng 3 **~45%** · hàng 1 **~30%** · hàng 2 **~15%** · hàng 4 **~10%**.
Ở 7B, `I − S` = +.20 và `V − I` = −.074..−.088 rất ổn định. Ở 32B khoảng cách `M`−`S` **hẹp lại**
(7B đã khá), nên tập "S đúng mà I sai" nhỏ đi ⇒ `Δ_ceil` nhỏ đi. **Rủi ro lớn nhất: cổng `I − S`
trượt** vì Qwen-7B vốn đã mạnh trên MBPP — chính là cách H89e chết. Tôi cho **~25%** khả năng VOID.

---

## #97-d — SỬA ĐỔI: cổng `n ≥ 480` là BẤT KHẢ THI trên dải tách rời

**Đăng ký lúc:** H88e đã xong và **VOID** vì `n`=463. **Tôi CHƯA đọc `d_gate`/`d_honest`/
`d_cont`/`d_ceil` của H88e** — sửa đổi này được ghi và commit **TRƯỚC** khi đọc.

### Sự thật thuộc về DỮ LIỆU, không thuộc về kết quả
```
MBPP full: task_id 11..974, tong 964 bai
  dai  11-510 : 500 bai tho -> 499 sau loc
  dai 511-974 : 464 bai tho -> 463 sau loc
  dai 511-1000: 464 bai tho   <-- y HET, vi MBPP het o 974
```
Ở #97-c tôi "sửa" bằng cách nới dải lên **511–1000**. **Sửa đó VÔ NGHĨA** — không có bài nào
trên 974. Tôi đã áp bài học #127 (*"nới dải, đừng hạ ngưỡng"*) **mà không kiểm dải có nới được không**.

Hệ quả: **`n ≥ 480` KHÔNG BAO GIỜ đạt được trên dải tách rời.** Đặt nguyên ngưỡng đó nghĩa là
**cấm vĩnh viễn** việc tái lập trên benchmark này — không phải kỷ luật, mà là hỏng thiết kế.

### Sửa
**Dải tách rời (511–974): cổng `n ≥ 460`.** Dải chính (11–510): giữ **`n ≥ 480`**.

**Vì sao được phép hạ ở đây mà #127 thì không:** căn cứ là **số đếm của bộ dữ liệu** (464 bài tồn
tại), **kiểm chứng độc lập được**, và **không phụ thuộc mảy may vào đầu ra của model nào**.
Ở #127 tôi định hạ ngưỡng vì **kết quả** không đạt — hoàn toàn khác. Chênh 463 vs 480 là **3.5%**
cỡ mẫu, ảnh hưởng không đáng kể tới lực thống kê.

**Công bố thứ tự:** sửa đổi này commit **trước** khi tôi mở bất kỳ delta nào của H88e.
Ai kiểm tra được bằng dấu thời gian git.

### Không đổi gì khác. Bảng khoá #97 giữ nguyên từng chữ.

---

## #102 — H92: **LIỀU–ĐÁP ỨNG của việc NHÌN THẤY** (kiểm M1 đã phát biểu lại ở #142)

**Đăng ký lúc:** trước khi phóng. #142 vừa phát biểu lại M1: *"vấn đề không phải `M` được phép
GHI ĐÈ, mà là `M` NHÌN THẤY"*. Đó là một **cơ chế**, và cơ chế thì phải có **liều–đáp ứng**.
Nếu không có, phát biểu lại của tôi chỉ là kể chuyện cho vừa số liệu.

### Thiết kế — cùng bài, cùng ngân sách, chỉ đổi LƯỢNG được nhìn
`S` = Qwen2.5-1.5B, `M` = Qwen2.5-7B, MBPP. Sinh `S` **một lần**, dùng chung cho mọi nhánh.

| nhánh | `M` được cho xem gì | ghi chú |
|---|---|---|
| `E0` = `I` | **không gì cả** | mốc thật |
| `E1` | *"Một model nhỏ hơn đã thử bài này."* — **không nội dung** | chỉ có sự tồn tại |
| `E2` | **chỉ chữ ký hàm + số dòng** của `S` (không thân hàm) | cấu trúc, không logic |
| `E3` | **toàn bộ code** của `S` (= `V`) | phơi nhiễm tối đa |

Mọi nhánh dùng **cùng một lệnh**: *"Write the complete self-contained Python function."*
`E1`–`E3` chỉ **thêm** phần ngữ cảnh. **Không nhánh nào được bảo "sửa"** — nhờ vậy tách được
**NHÌN THẤY** khỏi **ĐƯỢC LỆNH GHI ĐÈ** (thứ mà `V` truyền thống trộn chung).

### CỔNG (nêu CẢ hiệu ứng LẪN ý nghĩa — luật #140)
1. `compiles(extract(t)) ≥ .80` mọi nhánh, chênh **< .05**
2. `n ≥ 480` (dải 11–510) · 3. `I − S ≥ .05` **và** p < .05

### BẢNG KHOÁ

| # | điều kiện | KẾT LUẬN |
|---|---|---|
| 0 | cổng trượt | **VOID** |
| 1 | `E0 > E1 > E2 > E3` đơn điệu, và `E0 − E3 ≥ .05` với p < .05, và `E0 − E2 ≥ .02` với p < .05 | **LIỀU–ĐÁP ỨNG CÓ THẬT.** "Nhìn thấy" là biến gây hại, càng nhìn nhiều càng hại. M1 phát biểu lại ở #142 **đứng vững**. |
| 2 | `E3` thấp hơn `E0` (p<.05) nhưng `E1 ≈ E2 ≈ E0` (đều \|Δ\|<.02) | **NGƯỠNG, không phải liều.** Chỉ **nội dung logic đầy đủ** mới hại; biết-có-tồn-tại và cấu trúc thì vô hại. Phát biểu lại M1 lần nữa: hại đến từ **logic cụ thể**, không từ "nhìn thấy" nói chung. |
| 3 | `E1 < E0` với p < .05 (chỉ cần **biết có người thử** đã hại) | **KINH NGẠC.** Thiệt hại xảy ra **không cần nội dung nào** ⇒ là hiệu ứng **lệnh/khung**, không phải nhiễm nội dung. Sẽ phải xét lại toàn bộ diễn giải "nguồn ngoại lai". |
| 4 | mọi \|`Ei` − `E0`\| < .02 hoặc p ≥ .05 | **GIẾT phát biểu lại của #142.** Không tái lập được thiệt hại khi BỎ lệnh "review" ⇒ thủ phạm là **LỆNH GHI ĐÈ**, không phải việc nhìn thấy. M1 quay về bản gốc. |

### TIÊN NGHIỆM THÀNH THẬT
Hàng 2 **~40%** · hàng 1 **~25%** · hàng 4 **~25%** · hàng 3 **~10%**.
Tôi nghiêng về **ngưỡng** hơn **liều**: #119 đọc từ trace thấy `M` **viết lại** khi thấy code —
hành vi ấy cần **code thật** để bám vào, chứ chữ ký hàm thì khó neo.
**Hàng 4 đáng kể (~25%)** vì mọi phép đo đầu độc từ trước tới nay **đều kèm lệnh "review"**;
rất có thể lệnh mới là thủ phạm, và #142 của tôi đã quy sai cho "nhìn thấy".
**Nếu hàng 4 xảy ra, tôi phải sửa TONG_HOP lần nữa và nói rõ #142 đã suy diễn quá tay.**

---

## #101-b — SỬA ĐỔI: `MAXNEW` quá nhỏ cho nhánh `V` ở 32B

**Đăng ký lúc:** H91b đã VOID (`extract_spread` .0982 > .05). **Tôi CHƯA đọc `d_ceil`/`d_gate`/
`d_honest`/`d_cont` của H91b và sẽ không đọc** — nó VOID vĩnh viễn.

### Chẩn đoán (chỉ dùng đại lượng CỔNG + độ dài, không dùng kết quả)
| nhánh | độ dài TB | p95 | **block ```` ``` ```` CHƯA ĐÓNG** |
|---|---|---|---|
| `S` | 219 | 533 | **0.0%** |
| `I` | 302 | 733 | 0.4% |
| **`V`** | **1359** | **3374** | **17.2%** |

`V` dài gấp **4.5×** `I` và **17.2%** bị cắt giữa chừng ở `MAXNEW`=768 ⇒ không trích được code.
**Đây đúng là confound cắt cụt của #119/#130 — nhưng ĐỔI CHIỀU:** ở #130 cái cap phạt `I` nặng hơn,
ở đây nó phạt `V` nặng hơn. Lý do: 32B khi **được cho xem code** thì viết dài (giải thích + code),
còn khi **giải từ đầu** thì viết gọn.

> **Bài học tổng quát hơn #130: `MAXNEW` cố định phạt nhánh nào VIẾT DÀI NHẤT, và nhánh đó
> thay đổi theo thiết kế lẫn theo cỡ model.** Không thể chọn `MAXNEW` một lần rồi dùng mãi.

### Sửa cho H91c
1. **`MAXNEW`: 768 → 1536.** Căn cứ: p95 của `V` ≈ 3374 ký tự ≈ 850–900 token; 1536 để dư gấp ~1.7×.
   Chi phí: `V` mất ~36 phút ở 768 ⇒ ước ~72 phút; tổng ~100 phút, thừa sức trong tường 12h.
2. **Thêm CỔNG CẮT CỤT tường minh:** tỉ lệ output có block ```` ``` ```` **chưa đóng** phải **< .05
   ở MỌI nhánh**. Cổng `extract_spread` chỉ bắt được hậu quả; cổng này bắt **nguyên nhân**, và
   bắt sớm hơn.

### Bảng khoá #101 **giữ nguyên từng chữ.** Không đổi gì khác.
