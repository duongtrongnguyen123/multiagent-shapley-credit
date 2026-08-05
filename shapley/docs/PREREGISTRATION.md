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
