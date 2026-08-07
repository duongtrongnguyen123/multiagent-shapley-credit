# Ý tưởng & hướng breakthrough (loop tự cập nhật)

Loop tự chủ ghi vào đây sau mỗi kết quả: ý tưởng mới + đánh giá novelty trung thực
(lĩnh vực đông → đừng overclaim) + thí nghiệm nhỏ để kiểm.

## Trạng thái lưới (cập nhật liên tục)
- GSM8K·1.5B: S=V +0.252, A +0.190, P −0.014
- MATH·1.5B: A +0.150, S=V +0.144, P +0.017
- MATH·7B: A +0.319, V +0.318 (P=mP, S=mS đang chạy)

## Ý tưởng ứng viên (loop bổ sung)
1. **Substitution giữa V–A**: 7B-V làm φ_A giảm, 7B-A làm φ_V giảm → cặp thay thế. Đo interaction index để định lượng.
2. **Content-level vs role-level credit**: critic (NLP) có khớp Shapley không? Nếu KHÁC → phát hiện đáng giá.
3. **Plan-and-Solve gộp** vs Planner tách rời → chữa được vai Planner âm?
4. (loop thêm...)

## [Loop] Kết quả credit critic (200 trace GSM8K) — 2 cách đo credit KHÁC nhau
- Content-level critic (TF-IDF, AUC=0.61 yếu): Aggregator +0.003, Solver ~0, Verifier −0.004, **Planner −0.007 (tệ nhất)**.
- Role-level Shapley (GSM8K): S=V +0.252, A +0.190, **Planner −0.014 (tệ nhất)**.
- **KHỚP:** cả hai đồng ý Planner là vai tệ nhất → cross-method confirmation (đáng viết).
- **KHÁC:** critic bảo *text* Verifier không giúp đoán đúng/sai; Shapley bảo Verifier rất giá trị.
  → 2 KHÁI NIỆM credit khác nhau: Shapley = "thêm role có đổi kết quả không"; critic = "text role có
  *dự đoán* được kết quả không". Verifier đóng góp bằng ĐỔI đáp án, không bằng text tiên đoán → critic bỏ sót.
  **Đây là điểm phương pháp thật:** content-predictiveness ≠ causal-contribution.
- **Hạn chế:** critic bag-of-words quá yếu (AUC 0.61). Cần critic mạnh hơn (transformer / model re-check).
  Ý tưởng-thí-nghiệm: thay TF-IDF bằng embedding-of-transcript + LogReg, hoặc dùng LLM-judge làm critic.

## [Loop] Interaction index — cấu trúc thay thế/bổ trợ (finding mạnh)
- Solver×Verifier×Aggregator: SUBSTITUTE mạnh (I ≈ −0.21..−0.27, cả GSM8K & MATH) → 3 vai "sản
  xuất" đáp án THỪA nhau. Giải thích: (a) φ chúng gần bằng nhau; (b) nâng 1 lên 7B làm giảm φ hai
  vai kia (substitution đã thấy ở mA/mV). Đây là điểm interaction mà Shapley-biên đơn thuần không thấy.
- Planner ~độc lập với cả ba (I≈0) — không chồng chéo, nhưng cũng gần như không synergy.
- Ý tưởng-thí nghiệm: nếu S/V/A thừa nhau, một pipeline TỐI GIẢN (bỏ bớt 1 vai sản xuất) nên gần
  bằng full mà rẻ hơn → kiểm bằng oracle/router (đã có +19 điểm oracle 16 tổ hợp).
- Lưới MATH·7B đầy đủ: P+0.062 S+0.305 V+0.318 A+0.319 → S/V/A đều nhạy 7B mạnh (~+0.17) & thay thế;
  Planner nhạy yếu nhất (+0.04). "Đầu tư năng lực vào 1 trong 3 vai sản xuất là đủ, không cần cả ba."

## [Loop] Critic embedding không hơn TF-IDF (AUC 0.607 ≈ 0.61)
Encoder mạnh hơn KHÔNG giúp → nút thắt không phải biểu diễn text mà là "đặc trưng bề mặt của
transcript đoán yếu đúng/sai toán". ΔP: Planner −0.009 (tệ nhất, nhất quán), Solver +0.005, Verifier
−0.002, Aggregator +0.002. ⇒ critic nông (linear) không đủ; cần **LLM-judge critic** (model tự
re-check transcript) — đây mới là "học từ nội dung" đúng nghĩa. Củng cố: content-pred ≠ causal-contrib.

## [Loop] GSM8K 7B-Aggregator +0.048 (khiêm tốn) — capacity-sensitivity BÁM thứ hạng
- GSM8K: 7B-Verifier +0.462 (nhạy MẠNH), 7B-Aggregator chỉ +0.048 (yếu). MATH: 7B-Aggregator +0.319 &
  7B-Verifier +0.318 (cả hai mạnh). ⇒ **vai NHẠY năng lực = vai DẪN ĐẦU ở độ khó đó**: GSM8K→Verifier,
  MATH→Aggregator. Quy tắc thực dụng: "đầu tư 7B vào vai đang dẫn ở mức khó của bài".
- Ý tưởng: dự đoán *trước* vai nào đáng nâng dựa trên độ khó dataset (proxy: accuracy 1 solver) → quy tắc phân bổ năng lực.

## [Loop] LƯỚI GSM8K·7B ĐẦY ĐỦ (đường chéo)
7B-Planner +0.055 (r3) · 7B-Solver [gS] · 7B-Verifier +0.462 (r4) · 7B-Aggregator +0.244 (gA).
Chốt: trên GSM8K, Verifier là vai nhạy năng lực áp đảo (+0.46) — khớp "capacity vào vai dẫn đầu".
LOOP KẾT THÚC: core + bonus hoàn tất. Deliverables: master 4×3, GSM8K·7B & MATH·7B đường chéo,
interaction (S/V/A substitute), signed Shapley, critic NLP 3 lớp (novelty/NLI/learned), IDEAS.md.

## [Loop] 5 hướng CẢI TIẾN (base/showwork/loop/tool/struct) × {1.5B,7B} GSM8K — KẾT QUẢ TRUNG THỰC
1.5B(N=150): base 0.767, showwork 0.753, loop 0.760, tool 0.567, struct 0.707.
7B(N=80): base 0.900, loop 0.887, tool 0.850, struct 0.900 (showwork chờ).
→ KHÔNG method nào thắng base ở cả 2 size. 1.5B: tool/struct HẠI (model nhỏ không theo format/viết code lỗi).
  7B: base đã 0.90 (GSM8K gần bão hoà) → hết headroom, method ~ngang/kém.
KẾT LUẬN: cải tiến bằng phương pháp (format/tool/loop) KHÔNG phải đòn bẩy — bài dễ bão hoà, model yếu phản
tác dụng. Đòn bẩy thật = năng lực model. (Negative result có ích, chống hype "thêm cấu trúc/tool là tốt".)
Lưu ý: kiểm lại trên MATH (khó, chưa bão hoà) mới công bằng — GSM8K 7B quá dễ để thấy cải tiến.

## [Loop] BẢNG 5×2 ĐẦY ĐỦ (showwork-7B=0.925)
1.5B: base .767 showwork .753 loop .760 tool .567 struct .707
7B  : base .900 showwork .925 loop .887 tool .850 struct .900
CHỐT: KHÔNG method nào cải thiện ĐÁNG KỂ trên base. 1.5B: tricks hại. 7B: showwork nhỉnh (+.025, N=80 → nhiễu),
còn lại ~ngang/kém; GSM8K-7B bão hoà .90. => phương pháp KHÔNG phải đòn bẩy trên GSM8K; năng lực mới là.
NEXT (công bằng): lặp 5 hướng trên MATH (chưa bão hoà) để test thật.

## [Loop] TEST CÔNG BẰNG trên MATH-500 (khó, CHƯA bão hoà) — 5 method × {1.5B,7B}
1.5B(N=100): base .40  showwork .39  loop .60  tool .42  struct .27
7B (N=100): base .69  showwork .66  loop .69  tool .51  struct .65   (7B chạy 4-bit nf4 trên 1×T4)
PHÁT HIỆN CHÍNH — tương tác METHOD × CAPACITY:
- loop (Solver giải LẠI sau phê bình Verifier) là cải tiến THẬT nhưng CHỈ ở model yếu:
  1.5B +0.20 tuyệt đối (+50% tương đối, .40->.60); 7B loop = base (.69=.69) → hết lợi.
  Diễn giải: feedback-rerun CỨU model yếu (lần 1 sai, đọc phê bình sửa được); model khoẻ làm 1 lần đã đúng.
- MỌI method khác <= base ở CẢ 2 size:
  tool(PoT) HẠI mạnh 7B (.51 vs .69, -.18): đáp án MATH hay ở dạng ký hiệu/phân số, ép python+print làm mất
    thế mạnh CoT tự nhiên + lỗi code; struct HẠI 1.5B (.27 vs .40): model nhỏ bị gò format thì sụp.
KẾT LUẬN GỘP (GSM8K + MATH):
  Trên GSM8K (dễ/bão hoà) KHÔNG method nào thắng base. Trên MATH (khó) DUY NHẤT loop thắng, và chỉ cho 1.5B.
  => "Feedback-rerun là đòn bẩy có điều kiện: chỉ đáng khi (bài đủ khó) VÀ (model đủ yếu để lần 1 hay sai)."
  Đây là đóng góp positive + ranh giới áp dụng rõ ràng — hợp làm finding chính của đồ án (không hype, có số).

## [Loop] ITERATIVE (K vòng Solver<->Verifier) + STRUCTURED-COMM trên MATH-500 — KHÉP KÍN CÂU CHUYỆN
STRUCTURED-COMM (agent trao JSON field, Verifier chỉ đích step sai):
  1.5B acc .25 (base .40 -> HẠI); valid-JSON solver CHỈ .12 (model yếu không tuân format); fix/break = 1/34.
  7B  acc .48 (base .69 -> HẠI); valid-JSON solver .82; fix/break = 13/20.
  => Ép cấu trúc HẠI cả hai. Càng ép model càng sập; Verifier phá >> sửa. valid-JSON-rate = bằng chứng NLP đẹp.
ITERATIVE (acc theo vòng; vòng0 = solve, chưa verify):
  1.5B: [.52, .54, .54, .53]  fix/round [0,4,1,0]  break/round [0,2,1,1]  converged [_,68,17,5]
  7B  : [.66, .68, .68, .68]  fix/round [0,2,0,0]  break/round [0,0,0,0]  converged [_,87,8,2]
  => Feedback ăn MỘT lần (vòng 1, net +2), rồi BÃO HOÀ. Model yếu: vòng 3 bắt đầu HẠI (0 sửa/1 phá).
     Model khoẻ: không bao giờ phá (break=0) nhưng cũng chỉ +2 rồi hết (87% đồng thuận ngay vòng 1).
CƠ CHẾ TRUNG TÂM (gộp mọi thí nghiệm): Verifier là con dao 2 lưỡi — sửa vài lỗi NHƯNG phá đáp án đúng
  (negative transfer/sycophancy). Cán cân nghiêng về HẠI khi: (model càng yếu) HOẶC (càng ép format) HOẶC
  (càng lặp nhiều vòng). loop 1-vòng ở bài khó là điểm ngọt duy nhất. Đây là finding chính, nhất quán, có số,
  nối thẳng vào nhánh trace-analysis (đã đo break>>fix). Không hype, phù hợp đồ án NLP.
NOTE: số tuyệt đối giữa các kernel lệch nhẹ (loop-mode có Planner+Aggregator; iter-kernel chỉ S<->V) nên so
  HƯỚNG chứ không so thẳng con số; mọi harness đều cho cùng kết luận định tính.

## [Loop] STEP-INTERLEAVED vs POST-HOC + BẤT ĐỐI XỨNG NĂNG LỰC (MATH-500, N=50, solver=1.5B)
Hai kernel độc lập ra SỐ TRÙNG KHÍT (greedy, deterministic) -> tái lập được.
  A không verify            : .46
  B verify TỪNG BƯỚC (1.5B) : .22   fix 2  / break 14   step_err_rate .724
  C verify TỪNG BƯỚC (7B)   : .34   fix 5  / break 11   step_err_rate .426
  D verify POST-HOC (7B)    : .64   fix 9  / break  0   <-- TỐT NHẤT toàn dự án
  E 7B chia bước nguyên tử + 1.5B thi hành : .26  fix 5 / break 15  (avg 4.36 bước/bài)
GIẢ THUYẾT BAN ĐẦU SAI: tưởng interleave sẽ GIẢM break (vì verifier chỉ phán 1 bước nhỏ,
  không đụng đáp án cuối). Thực tế interleave là cấu hình TỆ NHẤT.
CƠ CHẾ (đo được, không suy diễn): tỉ lệ BÁO ĐỘNG GIẢ.
  Verifier 1.5B kêu "sai" ở 72.4% số bước; 7B vẫn kêu 42.6%. Mỗi báo động giả nhét một
  "sửa chữa" bịa vào context -> phá quỹ đạo vốn đang đúng. Nói càng nhiều, false-positive
  càng nhân lên. Nói MỘT lần thì không.
=> ĐỊNH LUẬT GỘP: giá trị của Verifier SỤP theo TẦN SUẤT can thiệp, ở cùng một mức năng lực.
   (7B mỗi bước .34  vs  7B một lần .64). Khớp luôn với kết quả iterative trước đó
   (vòng 2-3 vô ích, vòng 3 bắt đầu phá). Một định luật giải thích cả hai thí nghiệm.
KẾT QUẢ DƯƠNG (D): 1.5B giải + 7B soát MỘT lần = .46 -> .64 (+.18), 9 sửa / 0 phá.
   Sign test p ~ .004. Ý tưởng "bất đối xứng năng lực" ĐÚNG, nhưng cần MỘT can thiệp
   đặt đúng chỗ, không phải giám sát liên tục. Rẻ: 7B chỉ chạy 1 lần/bài.
   (Tham chiếu: 7B làm TẤT CẢ = .69 ở N=100 -> bất đối xứng gần bằng, tốn ít hơn nhiều.
    Khác N nên chỉ là so sánh gần đúng, cần xác nhận cùng N.)
THỐNG KÊ: B hại có ý nghĩa (2 vs 14, p~.004); E hại có ý nghĩa (5 vs 15, p~.04);
   C (5 vs 11, p~.21) chỉ là xu hướng, CHƯA đủ ý nghĩa với N=50.

## [Loop] CODE (HumanEval, n=164) — KIỂM CHỨNG ĐỊNH LUẬT BẰNG VERIFIER CHÍNH XÁC TUYỆT ĐỐI
              1.5B      7B
  A không verify        .531      .787
  B LLM tự soát         .543      .768(!)   <- tự soát KHÔNG giúp; 7B còn giảm
  C chạy test, sửa 1v   .561      .823
  D chạy test, sửa 3v   .567      .835      <- tốt nhất
D theo vòng: 1.5B .531->.561->.567->.567 | 7B .787->.823->.835->.835
  fix/vòng: [5,1,0] và [6,2,0];  break/vòng: [0,0,0] và [0,0,0]  <- KHÔNG PHÁ LẦN NÀO
KẾT LUẬN 1 — ĐỊNH LUẬT ĐƯỢC CHỨNG MINH (không còn là suy diễn):
  Ở MATH, lặp tới vòng 3 BẮT ĐẦU PHÁ. Ở CODE với verifier chính xác (chạy test), lặp
  KHÔNG BAO GIỜ phá — chỉ bão hoà. Cùng vòng lặp, cùng số vòng, CHỈ ĐỔI độ tin cậy tín hiệu.
  => Tác hại KHÔNG đến từ "lặp nhiều", mà từ "lặp trên tín hiệu KHÔNG ĐÁNG TIN".
  (1.5B 6 fix/0 break p~.03; 7B 8 fix/0 break p~.008)
KẾT LUẬN 2 — BẤT NGỜ: verifier LLM ĐỔI KIỂU HỎNG theo miền, ngược hẳn dự đoán của tôi.
  MATH: BÁO ĐỘNG THỪA (kêu sai 42-72% số bước) -> phá lời giải đúng.
  CODE: BỎ SÓT (chỉ kêu 15/164 và 12/164; recall trên bug thật chỉ .156 và .171
        -> bỏ lọt 65/77 và 29/35 chương trình HỎNG). Code "trông hợp lý" là nó cho qua.
  => Bất biến THẬT không phải "hay báo động giả", mà là "PHÁN ĐOÁN LLM KHÔNG ĐÁNG TIN";
     hướng lệch phụ thuộc miền. (Phải sửa lại cách phát biểu định luật cho đúng.)
KẾT LUẬN 3 — THANG BẬC VERIFIER (gộp cả MATH lẫn CODE):
  verify CHÍNH XÁC (chạy test)      > verify bằng MODEL MẠNH HƠN   > TỰ soát
  code D +.036/+.049, 0 phá           math D +.18, 0 phá             code B ~0 hoặc âm
  Tự soát (verifier = solver) gần như vô dụng: 1.5B +.012, 7B -.018 (n nhỏ, chưa ý nghĩa).
HỆ QUẢ CHO RLAIF/GRPO: dùng verifier LLM làm REWARD là hỏng — trên code nó chỉ bắt được
  15-17% lỗi thật. Reward phải là EXECUTION (code) hoặc CONSENSUS (math), không phải phán đoán LLM.

## [Loop] CHẤM TAY 6 CA "VERIFIER PHÁ" (GSM8K traces, n=200) — TÌM RA NGUYÊN NHÂN GỐC
Chấm thủ công 6/11 ca Verifier phá đáp án đúng: CẢ 6 đều là BÁO ĐỘNG SAI, phản đối vô căn cứ:
  case10 áp mức giảm 30% nhầm tháng rồi đếm trùng | case17 sai số học (20*35*50 ghi thành 3500)
  case19 trả lời THỜI GIAN trong khi đề hỏi VẬN TỐC | case44 đọc "20 nến" thành "20 pound"
  case46 bịa thêm biến y,z vô nghĩa | case54 hiểu "gấp 3 số mèo NHẬN NUÔI" thành gấp 3 của Trixie
=> Đây KHÔNG phải lỗi KIỂM TRA, mà là lỗi GIẢI LẠI.
PHÁT HIỆN GỐC: 5/6 ca đó Solver KHÔNG TRÌNH BÀY GÌ, chỉ ghi "The answer is X."
  Verifier không có gì để kiểm -> buộc phải TỰ GIẢI LẠI TỪ ĐẦU -> lỗi riêng của nó thành đáp án cuối.
SỐ LIỆU ĐỊNH LƯỢNG (chia theo độ dài lời giải Solver):
  KHÔNG trình bày (<200 ký tự): n=150, S đúng=103, V PHÁ=11  -> tỉ lệ phá 10.7%
  CÓ trình bày   (>=200 ký tự): n= 50, S đúng= 28, V PHÁ= 0  -> tỉ lệ phá  0.0%
  Median độ dài lời giải Solver = 20 KÝ TỰ (!) -> 1.5B hầu như không bao giờ trình bày.
  (p ~ .04 một phía; n=28 ở nhóm có trình bày -> GỢI Ý MẠNH, chưa kết luận chắc.)
DIỄN GIẢI LẠI TOÀN BỘ: Verifier không "kém kiểm tra" — nó CHƯA BAO GIỜ ĐƯỢC ĐƯA GÌ ĐỂ KIỂM.
  Kiểm tra thì dễ, giải mới khó; mình vô tình bắt nó làm việc khó.
CẢNH BÁO PHƯƠNG PHÁP: đây là quan sát QUAN SÁT (observational), không phải can thiệp —
  lời giải có trình bày có thể khác hệ thống (bài khó hơn / model ít tự tin hơn). Cần thí nghiệm
  CAN THIỆP: ép Solver luôn trình bày rồi đo lại tỉ lệ phá.
  Lưu ý: mode showwork trước đây KHÔNG cải thiện ACCURACY (.753 vs .767 GSM8K) — không mâu thuẫn,
  vì giảm phá có thể bị bù trừ chỗ khác; nhưng nghĩa là chỉ được kết luận "giảm phá", chưa được
  kết luận "tốt hơn".
GHI CHÚ: nhãn do LLM mạnh (Claude) chấm -> BẢN THÂN cũng là LLM judge. Phải để người chấm mù
  ~40 mục và báo độ đồng thuận (kappa) thì mới dùng được như gold proxy.

## [Loop] KẾT QUẢ CAN THIỆP "ép trình bày" — GIẢ THUYẾT CỦA TÔI BỊ BÁC BỎ (theo đúng pre-registration)
Kiểm tra can thiệp: GSM8K median độ dài lời giải 18 -> 542 ký tự. CAN THIỆP CÓ HIỆU LỰC (không vô hiệu).
GSM8K (n=250; nhánh mạnh về thống kê, 155 bài Solver đúng) — break_rate:
  A trơ            14/171 = .082
  B thấy trình bày 12/155 = .077
  C GIẤU trình bày 13/155 = .084     (C dùng CÙNG lời giải với B)
  => B ~ C ~ A. Rơi vào HÀNG 3 của PREREGISTRATION.md: GIẢ THUYẾT SAI.
     Tương quan quan sát trước đó (0/28 vs 11/103) là do NHIỄU, không sống sót qua can thiệp.
MATH (n=150) đi hướng ngược (.062 vs .154) NHƯNG chỉ 65 bài đúng, 4 vs 10 -> KHÔNG có ý nghĩa
  thống kê. KHÔNG được kết luận.
LƯU Ý QUAN TRỌNG: quan sát gốc (median 20 ký tự) là của GSM8K. Trên MATH Solver VỐN ĐÃ trình bày
  (median 894 ký tự) -> tôi đã suy rộng một hiện tượng riêng của GSM8K sang MATH. Sai phương pháp.

## [Loop] PHÁT HIỆN NGOÀI DỰ KIẾN (HẬU NGHIỆM — chưa pre-register, cần xác nhận độc lập)
Nhìn vào FIXES (không phải chỉ số chính đã đăng ký):
                    Verifier THẤY lời giải     Verifier BỊ BỊT MẮT
  GSM8K             10 sửa / 12 phá = net -2   40 sửa / 13 phá = net +27
  MATH               6 sửa /  4 phá = net +2   20 sửa / 10 phá = net +10
  verifier accuracy  .612 / .447                .728 / .500
=> VERIFIER BỊ BỊT MẮT BẮT LỖI GẤP ~4 LẦN, trên CẢ HAI task, với CÙNG bộ lời giải.
   Cho xem phần trình bày KHÔNG giúp nó kiểm — nó làm cho nó ĐỒNG TÌNH (anchoring/sycophancy).
   ĐẢO NGƯỢC câu chuyện cũ: verifier "tự giải lại" KHÔNG phải lỗi, mà chính là thứ làm nó hữu ích.
   (HẬU NGHIỆM: sinh ra từ chính bộ số này -> phải kiểm chứng độc lập trước khi dựa vào.)

## [Loop] SELF-CONSISTENCY k=8 (1.5B, MATH, n=100) — KẾT QUẢ DƯƠNG RÕ NHẤT
  greedy .50 | maj@4 .58 | maj@8 .60 | oracle@8 .73 | LLM-aggregator trên CÙNG 8 ứng viên .41
  llm_breaks_majority = 21   llm_fixes_majority = 2   (sign test p < .001)
=> (1) Bỏ phiếu thắng greedy +.10. Phương pháp KHÔNG-huấn-luyện đầu tiên thắng rõ.
   (2) Trên CÙNG bộ ứng viên, bộ tổng hợp LLM THẤP HƠN bỏ phiếu 19 ĐIỂM, và nó đè lên phe đa số
       ĐÚNG 21 lần trong khi chỉ cứu được 2 lần.
   => Khẳng định "SAI LOẠI BỘ TỔNG HỢP" giờ là ĐO ĐỐI ĐẦU, không còn là lập luận.
   (3) oracle@8 - maj@8 = .13 -> còn dư địa thật cho một bộ chọn (reranker) được huấn luyện.

## [Loop] SELF-CONSISTENCY 7B (MATH, n=100) — LỜI GIẢI CHO CÂU HỎI "CÓ PHẢI DO MODEL NHỎ KHÔNG?"
                     1.5B        7B
  greedy             .50         .72
  maj@8              .60 (+.10)  .73 (+.01)
  oracle@8           .73         .85
  LLM-aggregator     .41         .47
  đè lên đa số ĐÚNG  21          26
  cứu được đa số SAI  2           0   (!!)
  mức đồng thuận TB  4.6/8       6.4/8
(1) LỢI ÍCH CỦA BỎ PHIẾU GIẢM THEO NĂNG LỰC: +.10 ở 1.5B nhưng chỉ +.01 ở 7B.
    CƠ CHẾ nhìn thấy được: mức đồng thuận 4.6 -> 6.4. Model mạnh thì các mẫu GIỐNG NHAU hơn
    -> bỏ phiếu không còn gì để khai thác. Bỏ phiếu biến ĐA DẠNG thành độ chính xác;
    model mạnh cung cấp ít đa dạng hơn. (Cùng dạng với kết quả `loop` trước: giúp 1.5B, không giúp 7B.)
(2) SỰ SỤP ĐỔ CỦA BỘ TỔNG HỢP LLM NẶNG HƠN Ở 7B, không nhẹ đi: 26 lần đè lên phe đa số ĐÚNG,
    và 0 lần cứu được phe đa số SAI. => KHÔNG phải hiện tượng riêng của model nhỏ.
(3) oracle - maj: .13 (1.5B) và .12 (7B) -> dư địa cho reranker gần như NHƯ NHAU ở cả hai cỡ.

### CẢNH BÁO NHIỄU (phải sửa trước khi dùng kết luận (2) ở mức mạnh)
Nhánh aggregator KHÔNG công bằng theo thiết kế hiện tại:
  prompt SOLVE: có "step by step" + 1024 token | prompt AGG: KHÔNG có CoT + chỉ 384 token
=> .47 vs .72 lẫn lộn giữa "tổng hợp có hại" và "prompt yếu hơn, ít chỗ suy nghĩ hơn".
   Bất đối xứng 26/0 khó giải thích bằng prompt yếu (prompt yếu lẽ ra vẫn cứu được vài ca),
   nhưng KHÔNG tách bạch được bằng thiết kế này.
ĐƯỢC PHÉP KẾT LUẬN: bộ tổng hợp LLM *như đã cấu hình* kém xa bỏ phiếu trên cùng bộ ứng viên.
CHƯA ĐƯỢC KẾT LUẬN: tổng hợp bằng LLM về bản chất kém hơn bỏ phiếu.
CÁCH SỬA (rẻ): chạy lại nhánh aggregator với CÙNG chỉ dẫn CoT và CÙNG 1024 token.

## [Loop] GSM8K 7B — HIỆU ỨNG "VERIFIER BỊ BỊT MẮT" LẶP LẠI Ở CỠ LỚN HƠN
  B (thấy lời giải):  ver .840  breaks 8  fixes  9   medlen 407
  C (BỊ BỊT MẮT, CÙNG lời giải): ver .916  breaks 6  fixes 26   medlen 17
GIÁ TRỊ GIA TĂNG CỦA KHÂU VERIFY (verifier_acc - solver_acc), CẢ 3 THIẾT LẬP:
                 THẤY lời giải     BỊ BỊT MẮT      fixes
  GSM8K 1.5B      -0.8 điểm        +10.8 điểm      10 -> 40
  GSM8K 7B        +0.4 điểm        + 8.0 điểm       9 -> 26
  MATH  1.5B      +1.3 điểm        + 6.7 điểm       6 -> 20
=> VERIFY CÓ ĐỌC LỜI GIẢI: giá trị ~ 0.  VERIFY BỊT MẮT: +7 đến +11 điểm.
   Cùng lời giải, cùng verifier, cùng prompt — chỉ khác CÓ ĐƯỢC ĐỌC PHẦN TRÌNH BÀY HAY KHÔNG.
ĐIỂM SẮC NHẤT: số PHÁ gần như KHÔNG đổi (8 vs 6; 12 vs 13). Cho xem lời giải KHÔNG làm giảm
   thiệt hại — nó BÓP NGHẸT KHẢ NĂNG BẮT LỖI. Nhìn thấy lời giải làm verifier bị thuyết phục
   mà thôi phản đối (anchoring / sycophancy).
HỆ QUẢ THỰC DỤNG (ngược trực giác): đa số framework đa tác tử mặc định truyền TOÀN BỘ trace
   giữa các agent. Kết quả này nói: ĐỪNG đưa lời giải của Solver cho Verifier — chỉ đưa ĐÁP ÁN
   và bắt nó tự kiểm độc lập. RẺ HƠN (17 vs 407 ký tự context) mà TỐT HƠN NHIỀU.
PHÁT HIỆN PHỤ (nhất quán): ÉP ĐỊNH DẠNG "trình bày từng bước" LÀM SOLVER KÉM ĐI ở mọi thiết lập:
   .684->.620 (GSM8K 1.5B), .896->.836 (GSM8K 7B), .440->.433 (MATH 1.5B).
   Khớp với các kết quả format trước đây (struct/showwork đều hại).
CẢNH BÁO: vẫn là HẬU NGHIỆM. Cả 3 thiết lập đến từ CÙNG một mẻ thí nghiệm phóng cùng lúc ->
   là lặp lại nhất quán qua các điều kiện, KHÔNG phải kiểm chứng độc lập có đăng ký trước.
   Cần 1 lần chạy xác nhận có pre-registration trước khi coi là KHẲNG ĐỊNH.

## [Loop] XÁC NHẬN H1 (có pre-register) — ỦNG HỘ MỘT PHẦN; BẢN "MẠNH" CỦA TÔI LÀ SAI
bl_g15 — GSM8K 1.5B, n=250, solver .632 (158 đúng). MỘT bộ lời giải, cho Verifier xem 4 KIỂU:
  arm            ver_acc  value_added  fixes  breaks  đổi đáp án  ctx_chars
  I informed      .688      +5.6         20      6       46         854
  B blind         .708      +7.6         42     23      108         260
  P giấu đáp án   .688      +5.6         15      1       27         871
  X bài khác      .596      -3.6         29     38      122         852
ĐO ĐƯỢC: blind SỬA nhiều hơn (42 vs 20) NHƯNG cũng PHÁ gần 4 lần nhiều hơn (23 vs 6).
  Chênh lệch giá trị gia tăng chỉ +2 điểm (+7.6 vs +5.6), KHÔNG phải +8..+11 như tôi báo trước.
DIỄN GIẢI ĐÚNG: blind KHÔNG "thông minh hơn", nó CAN THIỆP NHIỀU HƠN (đổi 108 vs 46 đáp án).
  fixes tăng 2.1x, breaks tăng 3.8x -> ĐỘ CHÍNH XÁC của blind THẤP HƠN chút
  (39% số lần đổi là sửa đúng, so với 43% của informed).
TỰ SỬA SAI: con số +8..+11 trước đây đến từ thiết lập CÓ Planner + lời giải BỊ ÉP TRÌNH BÀY.
  Trong lần chạy sạch (không planner, prompt thường) khoảng cách co lại còn +2. TÔI ĐÃ NÓI QUÁ.
ARM X (GIẢ DƯỢC) — KẾT QUẢ GIÁ TRỊ NHẤT: cùng độ dài context (852 vs 854) nhưng nội dung là
  của BÀI KHÁC -> value_added -3.6, PHÁ 38 đáp án đúng.
  => Thứ quyết định là ĐỘ LIÊN QUAN của context, KHÔNG phải ĐỘ DÀI. Loại bỏ được cách giải
     thích cạnh tranh "context dài thì làm nó phân tâm".
ARM P (thấy suy luận, GIẤU đáp án cuối): CỰC KỲ THẬN TRỌNG — chỉ 1 PHÁ / 158 bài đúng
  (break_rate .006), chỉ đổi 27 đáp án. Cấu hình AN TOÀN NHẤT đo được trong cả dự án, nhưng
  sản lượng thấp (15 sửa). => Chính ĐÁP ÁN mới là cái neo verifier lại, không phải phần suy luận.
sw_m7 — MATH 7B: KHÔNG có hiệu ứng blind. fixes 11 vs 12, breaks 3 vs 3. Hiệu ứng BIẾN MẤT.
GIẢ THUYẾT (chưa kiểm chứng, quan sát chéo thí nghiệm): PLANNER LÀM SOLVER NGỪNG TRÌNH BÀY.
  Cùng prompt SOLVE: có Planner -> median 18 ký tự (sw_g15); không Planner -> 600 ký tự (bl_g15).
  Khớp với việc Planner có giá trị Shapley thấp/âm. CẦN thí nghiệm có kiểm soát mới kết luận.

## [Loop] VÒNG #3 — 6 KẾT QUẢ. HAI GIẢ THUYẾT BỊ BÁC, MỘT TỰ RÚT LẠI KHUYẾN NGHỊ

### H3 (verify có cổng lọc) — BỊ BÁC, rơi vào HÀNG 4 của pre-registration
  G gated GSM8K: 0 sửa / 0 phá / +0.0 điểm | cổng kêu YES 0/250 lần
  G gated MATH : 1 sửa / 0 phá / +0.5 điểm | cổng kêu YES 2/200 lần (recall .017)
=> CỔNG KHÔNG BAO GIỜ KÊU. G kém cả I (+5.6) lẫn B (+7.6) -> H3 BỊ BÁC, ghi rõ, không diễn giải lại.
ĐO ĐƯỢC (phần có giá trị): câu hỏi NHỊ PHÂN "có lỗi không? YES/NO" là THOÁI HOÁ với model nhỏ —
  nó gần như luôn trả lời NO. CÙNG model đó, khi được bảo LÀM RA lời giải sửa, nó đổi 27-108 đáp án;
  khi chỉ được bảo PHÁN, nó đổi 0. => Phải bắt model nhỏ LÀM VIỆC, đừng bắt nó CHẤM ĐIỂM.
  Khớp với kết quả code trước đó (verifier LLM bỏ sót, recall .156).
TỰ RÚT LẠI: vòng trước tôi gọi P (giấu đáp án) là "cấu hình an toàn nhất" và đề xuất áp dụng.
  Trên MATH, P phá 12 so với informed chỉ phá 3 -> P TỆ HƠN, không an toàn hơn.
  Mức an toàn ở GSM8K (1 phá) là ĐẶC THÙ TASK + do nó THỤ ĐỘNG. KHUYẾN NGHỊ ĐÓ ĐÃ SAI.

### H4 (Planner bóp nghẹt Solver) — BÓP NGHẸT: ĐÚNG. GÂY HẠI: BỊ BÁC.
GSM8K:  không planner acc .632 median 600 ký tự (2.8% dưới 200)
        CÓ planner   acc .684 median  18 ký tự (88.4% dưới 200)
        planner + nhắc "vẫn phải trình bày": acc .672, median VẪN 18 -> KHÔNG cứu được bằng prompt
MATH :  .405/1319  ->  .425/899  (cùng hướng)
=> Planner làm Solver ngừng viết ra lời giải (600 -> 18) NHƯNG ĐỘ CHÍNH XÁC TĂNG (.632 -> .684).
   Giả thuyết "gây hại" của tôi BỊ BÁC. Việc bóp nghẹt trình bày KHÔNG làm giảm chất lượng.
GIẢ THUYẾT MỚI (chưa kiểm chứng): BẢN KẾ HOẠCH CHÍNH LÀ PHẦN SUY LUẬN. Solver suy luận ngay ở
   bước lập kế hoạch rồi chỉ phát ra đáp án -> PIPELINE VỨT BỎ PHẦN SUY LUẬN TRƯỚC KHI VERIFIER
   NHÌN THẤY. Giải thích được các trace "đáp án trơ" mà không cần giả thuyết "solver lười".

### H2 (bộ tổng hợp công bằng) — HÀNG 2: KHOẢNG CÁCH CŨ PHẦN LỚN DO NHIỄU PROMPT CỦA TÔI
  cũ (prompt thiệt thòi): .41  vs maj .60  = -19.0 điểm | 21 phá / 2 cứu
  agg_fair (CoT + 1024):  .467 vs maj .533 = - 6.7 điểm | 15 phá / 7 cứu
  agg_with_counts:        .500              = - 3.3 điểm | 11 phá / 7 cứu
  agg_full_sol:           .358              = -17.5 điểm | 26 phá / 5 cứu
=> Khoảng cách co từ -19 xuống -6.7 khi đối xử công bằng. KHẲNG ĐỊNH "kém 19 điểm" CỦA TÔI ĐÃ
   BỊ THỔI PHỒNG bởi nhiễu prompt, đúng như đã tự cảnh báo. Phát biểu CÒN SỐNG (yếu hơn):
   tổng hợp bằng LLM vẫn thua bỏ phiếu (-6.7) và vẫn phá gấp ~2 lần số cứu.
   Cho biết SỐ PHIẾU giúp thu hẹp (-3.3) nhưng VẪN không bằng bỏ phiếu thuần.

### H1 trên MATH (bl_m15) — chỉ ỦNG HỘ YẾU
  I informed: +5.0 điểm, 13 sửa /  3 phá | B blind: +5.0 điểm, 19 sửa /  9 phá
  P giấu đáp: +0.5 điểm, 13 sửa / 12 phá | X bài khác: -3.5 điểm, 23 sửa / 30 phá
=> fixes(blind) > fixes(informed) đúng ở CẢ HAI task (42>20 và 19>13) NHƯNG giá trị gia tăng
   trên MATH BẰNG NHAU (+5.0 = +5.0). Lợi ích thực tế của blind = 0 trên MATH.

### PHÁT HIỆN LẶP LẠI ỔN ĐỊNH NHẤT: ĐỘ LIÊN QUAN CỦA CONTEXT
  X_cross: GSM8K -3.6 (38 phá) | MATH -3.5 (30 phá)  -> LẶP LẠI 2/2 task
  agg_full_sol (cho aggregator xem TOÀN VĂN lời giải): -17.5, tệ nhất trong các nhánh aggregator
=> HAI VAI khác nhau, HAI task khác nhau, CÙNG một hướng: đưa thêm context làm HỎNG phán đoán
   của LLM; thứ quyết định là ĐỘ LIÊN QUAN chứ không phải ĐỘ DÀI.

## [Loop] VÒNG #4 — H5 BỊ BÁC (rơi HÀNG 3). LẦN THỨ 5 giả thuyết của tôi chết.
pp_g15 — GSM8K 1.5B, n=250, Planner BẬT (solver 18 ký tự, plan 435 ký tự), solver_acc .684:
  V_sol  (chỉ lời giải)      +4.8 điểm | 26 sửa / 14 phá | ctx 275
  V_plan (kế hoạch + đáp án) -2.8 điểm |  6 sửa / 13 phá | ctx 704
  V_both (kế hoạch + lời giải)-2.0 điểm |  3 sửa /  8 phá | ctx 757
  V_none (chỉ đáp án)        +4.0 điểm | 27 sửa / 17 phá | ctx 260
=> Đưa KẾ HOẠCH cho Verifier KHÔNG khôi phục khả năng kiểm tra — nó PHÁ HUỶ khả năng đó.
   Giá trị tụt ~7 điểm, số SỬA sụp từ 26 xuống 3. H5 BỊ BÁC, rơi đúng HÀNG 3 đã khoá trước:
   "kế hoạch chỉ là context gây nhiễu, KHÔNG phải suy luận hữu ích".
GHI CHÚ: V_none ~ V_sol vì khi Planner bật, "lời giải" vốn đã trơ (18 ký tự) — hai nhánh gần
   như cùng một thứ. Đối chiếu thực sự ở đây là CÓ vs KHÔNG có context kế hoạch.

### LẦN THỨ 4 LẶP LẠI CÙNG MỘT HIỆU ỨNG (đây mới là thứ bền)
  ĐO ĐƯỢC — thêm context cho Verifier làm GIẢM giá trị của nó, ở MỌI dạng đã thử:
    không thêm gì (chỉ đáp án)        +4.0
    kế hoạch của Solver               -2.8
    kế hoạch + lời giải               -2.0
    suy luận của BÀI KHÁC             -3.6 / -3.5  (2 task)
    toàn văn lời giải (vai aggregator)-17.5
### TỰ SỬA SAI: phải LÀM YẾU khẳng định vòng trước
  Vòng trước tôi nói "ĐỘ LIÊN QUAN mới quan trọng, không phải ĐỘ DÀI".
  Kế hoạch LÀ context LIÊN QUAN (đúng bài đó, và nó còn LÀM TĂNG acc của Solver .632->.684)
  — VẬY MÀ VẪN HẠI Verifier. => Chỉ "liên quan" thôi KHÔNG cứu được context. RÚT LẠI dạng mạnh.
GIẢ THUYẾT MỚI (chưa kiểm chứng): thứ quyết định là context có chứa PHÉP TÍNH KIỂM CHỨNG ĐƯỢC
  hay không. Kế hoạch nêu Ý ĐỊNH ("tìm tổng rồi trừ đi"); lời giải nêu KẾT QUẢ ("14 x 3 = 42").
  Số học thì KIỂM ĐƯỢC; ý định thì KHÔNG.

## [Loop] VÒNG #5 — H5 BỊ BÁC LẦN 2 (MATH); H6 BỊ BÁC VÀ THỨ TỰ NGƯỢC HẲN DỰ ĐOÁN
### pp_m15 (H5 trên MATH, 1.5B, n=200, solver .425)
  V_none (chỉ đáp án) +4.0 | 23 sửa / 15 phá | ctx  204
  V_sol               +2.0 | 11 sửa /  7 phá | ctx 1066
  V_both              +2.0 | 11 sửa /  7 phá | ctx 1762
  V_plan              +1.0 | 11 sửa /  9 phá | ctx  988
=> Rơi HÀNG 4 đã khoá: "V_none tốt nhất -> mọi context đều hại". H5 bị bác trên CẢ HAI task.

### cp_g15 (H6 trên GSM8K, 1.5B, n=250, Planner TẮT, solver .632, lời giải THẬT 600 ký tự)
  W_prose (ẨN HẾT SỐ, giữ lời văn) +8.4 | 33 sửa / 12 phá | ctx 916
  W_none  (chỉ đáp án)             +7.6 | 42 sửa / 23 phá | ctx 260
  W_calc  (CHỈ dòng phép tính)     +6.4 | 25 sửa /  9 phá | ctx 605
  W_full  (nguyên văn)             +5.6 | 20 sửa /  6 phá | ctx 854
=> H6 BỊ BÁC, rơi HÀNG 2: "không phải phép tính; là thứ khác".
   Tôi dự đoán PHÉP TÍNH là thành phần hoạt tính. THỰC TẾ NGƯỢC LẠI: XOÁ SỐ ĐI thì TỐT HƠN,
   và chỉ-đưa-phép-tính còn TỆ HƠN không đưa gì.

### QUY LUẬT MỚI (ĐO ĐƯỢC, đơn điệu theo LƯỢNG SỐ LIỆU được nhìn thấy)
  không có số nào (prose, ẩn giá trị)  +8.4 | 33 sửa
  chỉ đáp án cuối                      +7.6 | 42 sửa
  mọi giá trị trong phép tính          +6.4 | 25 sửa
  toàn bộ                              +5.6 | 20 sửa
=> Càng cho Verifier thấy NHIỀU GIÁ TRỊ TRUNG GIAN, giá trị của nó càng GIẢM.
GIẢ THUYẾT (chưa kiểm chứng, KHÔNG nằm trong pre-registration): chính các GIÁ TRỊ TRUNG GIAN
  của Solver là thứ NEO Verifier lại. Thấy một con số thì nó CHẤP NHẬN con số đó thay vì tính lại.
  Che số đi thì nó buộc phải TỰ TÍNH -> bắt được nhiều lỗi hơn.
ĐÂY LÀ NHÁNH ĐẦU TIÊN VƯỢT ĐƯỢC "chỉ-đáp-án": cho thấy CẤU TRÚC suy luận nhưng CHE GIÁ TRỊ
  (+8.4) tốt hơn cả hai thái cực. Là khuyến nghị TÍCH CỰC (làm gì) chứ không chỉ "đừng làm gì".
  NHƯNG: 1 task, 1 model, KHÔNG pre-register -> vẫn chỉ là GIẢ THUYẾT. cp_m15 và cp_g7 đang chạy
  sẽ kiểm chứng đúng điều này.

## [Loop] VÒNG #6 — RÚT LẠI KẾT QUẢ VÒNG TRƯỚC: CHE GIÁ TRỊ KHÔNG LẶP LẠI, NÓ ĐẢO NGƯỢC
### cp_m15 (H6 trên MATH, 1.5B, n=200, solver .405)
  W_calc  (chỉ phép tính)  +5.5 | 15 sửa /  4 phá
  W_full  (nguyên văn)     +5.0 | 13 sửa /  3 phá
  W_none  (chỉ đáp án)     +5.0 | 19 sửa /  9 phá
  W_prose (ẨN HẾT SỐ)      -2.0 | 21 sửa / 25 phá   <-- TỆ NHẤT
ĐỐI CHIẾU VỚI GSM8K vòng trước: W_prose là TỐT NHẤT (+8.4). Trên MATH nó TỆ NHẤT (-2.0). ĐẢO NGƯỢC.
TỰ RÚT LẠI: vòng trước tôi gọi "che giá trị trung gian" là "kết quả TÍCH CỰC, TRIỂN KHAI ĐƯỢC
  đầu tiên của cả dự án". NÓ KHÔNG LẶP LẠI. Tôi đã ghi rõ đó là GIẢ THUYẾT cần kiểm chứng;
  kiểm chứng cho kết quả ÂM -> RÚT LẠI HOÀN TOÀN.
GIẢ THUYẾT giải thích (chưa kiểm chứng): lời văn GSM8K vẫn giữ được logic khi xoá số
  ("tìm tổng rồi trừ đi"); còn lời giải MATH bị xoá ký hiệu thì VÔ NGHĨA — phân số, căn, biểu thức
  CHÍNH LÀ nội dung. Che số = phá huỷ nội dung toán.

### bl_g7 (H1 trên GSM8K 7B, n=250, solver ĐÃ .916 — gần bão hoà)
  B blind    0.0 | 6 sửa / 6 phá     I informed -0.8 | 4 sửa / 6 phá
  P partial -0.8 | 3 sửa / 5 phá     X cross    -1.6 | 8 sửa /12 phá
=> MỌI nhánh verify đều BẰNG 0 hoặc ÂM. Tiêu chí fixes của H1 (6 vs 4) là vụn vặt, không ý nghĩa.
ĐO ĐƯỢC: KHI SOLVER ĐÃ MẠNH (gần bão hoà), KHÔNG cấu hình verify nào còn giá trị.

### THỨ DUY NHẤT CHƯA BAO GIỜ THẤT BẠI
  X_cross (context KHÔNG liên quan) ÂM 3/3 thiết lập: -3.6 (GSM8K 1.5B), -3.5 (MATH 1.5B),
  -1.6 (GSM8K 7B). Cả 2 task, cả 2 cỡ model.
  Cùng với verify BẰNG THỰC THI (code: 0 phá qua 3 vòng) — đây là hai thứ chưa từng hỏng.

### TỔNG KẾT TRUNG THỰC: 7 GIẢ THUYẾT CỦA TÔI ĐÃ CHẾT
  interleaving giúp | math vốn khó verify | H3 cổng lọc | H4 planner gây hại | H5 truyền kế hoạch
  | H6 phép tính là thành phần hoạt tính | che-giá-trị triển khai được
META-PHÁT HIỆN (ĐO ĐƯỢC, từ chính chuỗi thất bại này): PHẦN LỚN "mẹo" cải tiến đa tác tử tạo ra
  hiệu ứng KHÔNG CHUYỂN ĐƯỢC qua task khác hoặc cỡ model khác. W_prose: +8.4 (GSM8K) -> -2.0 (MATH).
  Blind: +2 (GSM8K 1.5B) -> 0 (MATH 1.5B) -> 0 (GSM8K 7B).
  => Đây TỰ NÓ là kết quả có giá trị và bảo vệ được: cảnh báo về tính KHÔNG BỀN của các mẹo
     prompting đa tác tử, có 7 lần bác bỏ + 1 lần đảo ngược làm bằng chứng.

## [Loop] VÒNG #7 — H8 VÔ HIỆU (không phải bị bác), H7 BỊ BÁC, và ĐIỂM DỮ LIỆU SẮC NHẤT DỰ ÁN

### H8 (verify bằng THỰC THI trên math) — RƠI HÀNG 4: THÍ NGHIỆM VÔ HIỆU
  ex_g15 (GSM8K): L_llm +5.6 | E_take -12.0 (4 sửa/34 phá) | E_flag +1.6
  ex_m15 (MATH) : L_llm +5.0 | E_take  -5.0 (11 sửa/21 phá) | E_flag +2.0
  KIỂM TRA HIỆU LỰC: exec_success_rate .416 và .435 -> CẢ HAI DƯỚI 50%
                     exec_acc .414 và .391 -> Python chạy được thì cũng SAI 60%
=> Đúng như đã KHOÁ TRƯỚC: dưới 50% thì THÍ NGHIỆM VÔ HIỆU về mặt cơ chế. Đây là HẠN CHẾ NĂNG LỰC
   của model 1.5B (không viết nổi chương trình tính lại), KHÔNG PHẢI bằng chứng bác bỏ H8.
   E_take sụp (-12.0) chỉ vì nó nhận đáp án từ code SAI 60% — không nói lên điều gì về cơ chế.
   KHÔNG ĐƯỢC kết luận "verify bằng thực thi thất bại trên math". H8 vẫn CHƯA ĐƯỢC KIỂM CHỨNG.
ĐỐI CHIẾU: cùng model này đạt .53 pass@1 trên HumanEval — nơi ĐỀ BÀI ĐÃ CHO SẴN chữ ký hàm và
   docstring. Viết chương trình tính lại TỪ ĐẦU khó hơn nhiều. Cần model mạnh hơn để kiểm H8.

### H7 (che giá trị cho vai AGGREGATOR) — BỊ BÁC, rơi HÀNG 2
  am_15 (MATH 1.5B, n=120, maj@8 .55, oracle@8 .70):
    A_answers (chỉ danh sách đáp án)   .533  vs_maj -1.7   |  7 phá /  5 cứu | ctx  251
    A_full    (toàn văn lời giải)      .300  vs_maj -25.0  | 33 phá /  3 cứu | ctx 2876
    A_masked  (toàn văn, CHE GIÁ TRỊ)  .325  vs_maj -22.5  | 30 phá /  3 cứu | ctx 3261
=> Che số cứu được gần như KHÔNG GÌ (.325 vs .300). Hiệu ứng che số CHỈ RIÊNG vai Verifier,
   KHÔNG tổng quát sang vai Aggregator. H7 BỊ BÁC.
   Đồng thời rơi luôn HÀNG 4: MỌI nhánh LLM đều thua bỏ phiếu -> củng cố "vai tổng hợp dùng THỐNG KÊ".

### ĐIỂM DỮ LIỆU SẮC NHẤT CỦA CẢ DỰ ÁN (từ chính am_15)
  CÙNG bài, CÙNG bộ ứng viên, CHỈ khác cái được nhìn:
    chỉ đưa DANH SÁCH ĐÁP ÁN  -> .533  (gần bằng bỏ phiếu .55)
    đưa thêm TOÀN VĂN lời giải -> .300  (SỤP 23 ĐIỂM)
=> Thêm context làm MẤT 23 ĐIỂM ở cùng một nhiệm vụ. Đây là minh chứng rõ nhất cho
   "CONTEXT PHÁ HUỶ PHÁN ĐOÁN CỦA LLM", và nó ở vai THỨ HAI (không phải Verifier).

## [Loop] VÒNG #8 — H5 BỊ BÁC LẦN 3 (GSM8K 7B), rơi HÀNG 4
pp_g7 (GSM8K 7B 4-bit, n=250, solver ĐÃ .896):
  V_none (chỉ đáp án) +2.4 | 12 sửa / 6 phá | ctx  260   <-- TỐT NHẤT
  V_plan              +1.6 |  7 sửa / 3 phá | ctx  620
  V_sol               +0.8 |  8 sửa / 6 phá | ctx  707
  V_both              +0.8 |  3 sửa / 1 phá | ctx 1062
=> "V_none tốt nhất" -> HÀNG 4. H5 bị bác ở CẢ BA thiết lập (GSM8K 1.5B, MATH 1.5B, GSM8K 7B).
=> Đồng thời khớp bl_g7: khi Solver đã mạnh (.896), MỌI hiệu ứng verify đều nhỏ (+0.8..+2.4).

### TỔNG HỢP "V_none (chỉ đáp án)" QUA 3 THIẾT LẬP
  GSM8K 1.5B: +4.0 (V_sol +4.8 nhỉnh hơn chút, nhưng V_plan -2.8 / V_both -2.0 TỆ HƠN NHIỀU)
  MATH  1.5B: +4.0  <-- tốt nhất
  GSM8K 7B  : +2.4  <-- tốt nhất
=> Truyền THÊM suy luận cho Verifier KHÔNG BAO GIỜ giúp rõ rệt; truyền KẾ HOẠCH thì hại.
   Chỉ truyền ĐÁP ÁN luôn nằm ở hoặc gần vị trí tốt nhất, VÀ rẻ hơn 3-4 lần về context.

## [Loop] VÒNG #9 — MẺ 6 KẾT QUẢ LÀM LUNG LAY TOÀN BỘ CÂU CHUYỆN "CONTEXT GÂY HẠI"

### bl_m7 (H1 tại MATH 7B, solver .625) — ĐẢO NGƯỢC
  I informed +6.5 | 17 sửa / 4 phá     P partial +6.0 | 15 sửa / 3 phá
  X cross    +5.5 | 15 sửa / 4 phá     B blind   +0.5 |  9 sửa / 8 phá
=> Informed TỐT HƠN blind gấp 13 lần — NGƯỢC HẲN giả thuyết verifier-bịt-mắt.
=> X_cross (context KHÔNG liên quan) LẦN ĐẦU DƯƠNG (+5.5), sau khi ÂM ở 3/3 thiết lập trước
   (-3.6, -3.5, -1.6). "Phát hiện bền nhất" của tôi ĐÃ GÃY.

### agf_7 (H2 tại MATH 7B) — H2 BỊ BÁC, rơi HÀNG 3
  maj@8 .7167 | agg_fair .725 (+0.8) | agg_with_counts .7167 (0.0) | agg_full_sol .7333 (+1.7)
=> Bộ tổng hợp LLM giờ NGANG hoặc HƠN bỏ phiếu, và nhánh CHO XEM TOÀN VĂN LỜI GIẢI LÀ TỐT NHẤT.
=> Con số "-19 điểm, 26 phá / 0 cứu" trước đây LÀ NHIỄU PROMPT HOÀN TOÀN, đúng như đã tự cảnh báo.

### cp_g7 (H6 tại GSM8K 7B, solver .916 bão hoà)
  W_none 0.0 | W_full -0.8 | W_calc -0.8 | W_prose -1.6  -> mọi thứ ~0, không kết luận được gì.

### mf_g15 / mf_m15 (H9 — thí nghiệm hợp nhất)
              solver đơn  FULL   MIN   tỉ lệ context
  GSM8K         .632      .744   .640      2.9x
  MATH          .405      .345   .405      6.6x
=> GSM8K: FULL HƠN MIN 10.4 điểm và hơn solver đơn 11.2 điểm -> H9 BỊ BÁC, rơi HÀNG 2
   ("mâu thuẫn quan trọng phải giải thích", đã khoá trước).
=> MATH: MIN >= FULL (+6.0) và FULL còn TỆ HƠN solver đơn (-6.0).
### TỰ THÚ LỖI THIẾT KẾ (không phải bào chữa hậu nghiệm)
  Nhánh MIN của tôi bỏ ĐỒNG THỜI hai thứ: (a) truyền trace cho Verifier/Aggregator, và
  (b) đường Planner -> Solver. Nhưng plan_g15 ĐÃ ĐO ĐƯỢC (b) LÀM TĂNG acc (.632 -> .684).
  => MIN bị chấp ~5 điểm ngay từ đầu. PHÉP SO SÁNH KHÔNG SẠCH. Cần bản sửa lỗi.

### KẾT LUẬN TRUNG THỰC PHẢI GHI LẠI
ĐO ĐƯỢC: quy luật "thêm context làm hỏng phán đoán" ĐÚNG ở 1.5B nhưng ĐẢO NGƯỢC ở 7B trên MATH.
  Toàn bộ câu chuyện tôi dựng lên phần lớn là HIỆN TƯỢNG CỦA MODEL YẾU, cộng thêm nhiễu prompt
  ở các nhánh aggregator. KHÔNG được phát biểu nó như một quy luật chung.
META-PHÁT HIỆN (giờ đã rất vững, có 9 lần bác bỏ + nhiều lần ĐỔI DẤU làm bằng chứng):
  Hiệu ứng của các "mẹo" đa tác tử KHÔNG BỀN — chúng đổi dấu theo task và theo cỡ model.
  Muốn kết luận bất cứ điều gì, PHẢI đo trên lưới task x cỡ model, không được suy rộng từ một ô.

## [Loop] VÒNG #10 — H10 (BẢN ĐÃ SỬA LỖI) trên GSM8K 1.5B: RƠI HÀNG 2, PHẢI RÚT LẠI KHUYẾN NGHỊ
tr_g15 — mọi nhánh GIỮ NGUYÊN Planner->Solver; FULL và TRIM dùng CÙNG BỘ LỜI GIẢI (sT=sF),
chỉ khác thứ V và A được nhìn thấy:
  FULL (P->S->V->A, toàn văn)      .744   ctx 577k
  NOVA (chỉ P->S, bỏ V và A)       .684   (-6.0 so với FULL)
  TRIM (P->S->V->A, chỉ đáp án)    .668   (-7.6 so với FULL)  ctx 139k (rẻ 4.2 lần)
  solver đơn                       .632   (-11.2)
=> ĐO ĐƯỢC: truyền trace đáng giá +7.6 điểm ở mức ĐẦU-CUỐI. Rơi HÀNG 2 đã khoá trước:
   PHẢI RÚT LẠI khuyến nghị "đừng truyền trace" (chờ 3 ô còn lại của lưới để chốt).

### THỨ TỰ CÒN SẮC HƠN MỘT PHÉP ĐẢO NGƯỢC ĐƠN THUẦN
  TRIM (.668) THẤP HƠN NOVA (.684): thêm Verifier + Aggregator mà chỉ cho chúng ĐÁP ÁN thì
  CÒN TỆ HƠN LÀ KHÔNG CÓ CHÚNG. Nhưng CÙNG hai vai đó với toàn văn thì ĐÁNG +6.0.
=> V và A không tự thân có hại hay có lợi: GIÁ TRỊ CỦA CHÚNG PHỤ THUỘC HOÀN TOÀN vào việc
   có được nhận phần suy luận hay không. Bỏ đói context thì chúng thành ÂM.

### BÀI HỌC PHƯƠNG PHÁP (quan trọng cho chính khung Shapley của dự án)
Các thí nghiệm TỪNG VAI của tôi đo Verifier RIÊNG LẺ và thấy nó tốt hơn khi bị bịt mắt.
Điều đó KHÔNG dự đoán được hiệu ứng ở mức pipeline, vì Aggregator phía sau CẦN trace để phân xử
giữa Solver và Verifier.
=> ĐO MỘT VAI RIÊNG LẺ LÀ CHỈ DẤU TỒI cho hành vi đầu-cuối. Đây là cảnh báo trực tiếp đối với
   chính khung "Shapley theo từng vai" mà dự án khởi đầu — giá trị của một vai không tách rời
   được khỏi thứ mà các vai khác nhận được.

## [Loop] VÒNG #11 — H11 (phân bổ vai) và H10 trên MATH: ĐỔI DẤU ĐƯỢC XÁC NHẬN SẠCH
### ra_g15 (H11, GSM8K 1.5B, n=250) — rơi HÀNG 1
  P->S        .684
  P->S->V     .732   (+4.8)   <-- Verifier mang gần như TOÀN BỘ giá trị
  P->S->V->A  .744   (+6.0)   (Aggregator thêm +1.2 khi ĐỨNG SAU Verifier)
  P->S->A     .428   (-25.6)  <-- Aggregator ĐỨNG MỘT MÌNH thì sụp
LƯU Ý TRUNG THỰC: nhánh P->S->A là CẤU HÌNH THOÁI HOÁ — bộ tổng hợp chỉ nhận MỘT ứng viên thì
  không có gì để tổng hợp, nó đi giải lại và hỏng. -25.6 phản ánh điều đó, KHÔNG phải
  "Aggregator vô dụng". Chỉ số synergy +.268 cũng bị thổi phồng bởi chính sự sụp đổ này.

### tr_m15 (H10 bản đã sửa lỗi, MATH 1.5B, n=200)
  TRIM (chỉ đáp án) .435 | NOVA (bỏ V,A) .425 | solver đơn .405 | FULL (toàn văn) .345
  trim_minus_full = +.09   full_minus_solo = -.06
=> Trên MATH: truyền trace LÀM HẠI (-9.0 so với cắt trace; -6.0 so với solver đơn).
=> Trên GSM8K (tr_g15): truyền trace CÓ LỢI (+7.6).
=> ĐỔI DẤU 16.6 ĐIỂM giữa hai task, với CÙNG mã nguồn và thiết kế ĐÃ KHỬ NHIỄU
   (mọi nhánh giữ Planner->Solver; FULL và TRIM dùng CÙNG bộ lời giải).
   Rơi HÀNG 3 của pre-registration #9: "kết quả đổi dấu giữa các ô -> META-PHÁT HIỆN LÀ KẾT LUẬN".

### CHỐT HƯỚNG CHÍNH CỦA DỰ ÁN
Đây là bằng chứng SẠCH NHẤT cho meta-phát hiện, vì H10 là thiết kế đã khử nhiễu (khác với các
lần đảo dấu trước còn lẫn biến). Hướng chính của repo được cập nhật trong README:
  "Hiệu ứng của cơ chế phối hợp đa tác tử KHÔNG BỀN — đổi dấu theo task và cỡ model."
Đã thêm docs/RESULTS.md tổng hợp toàn bộ số liệu.

## [Loop] KIỂM TRA TRỰC TIẾP OUTPUT CỦA PLANNER — PHÁT HIỆN KIẾN TRÚC QUAN TRỌNG NHẤT
Prompt của Planner: "Give a concise numbered plan. Do NOT compute the final answer."
ĐỌC TRỰC TIẾP trace (results_trace/traces.json, GSM8K 1.5B, n=200): NÓ KHÔNG TUÂN.
  case 1 : kế hoạch tính luôn "2 + 1 = 3 bolts" -> Solver ghi "The answer is 3." (16 ký tự)
  case 10: kế hoạch tính luôn tới "= 366"       -> Solver ghi "The answer is 366." (18 ký tự)
ĐO ĐƯỢC:
  Kế hoạch ĐÃ CHỨA đáp án đúng            : 91/200 = 45.5%
  Đáp án Solver TRÙNG số cuối của kế hoạch: 125/200 = 62.5%
  Lời giải Solver < 60 ký tự              : 138/200 = 69.0%
  CHÉP LẠI (ngắn VÀ trùng kế hoạch)       : 122/200 = 61.0%
  Khi kế hoạch ĐÚNG (n=91) -> Solver đúng 98.9%
  Khi kế hoạch SAI  (n=109) -> Solver đúng 37.6%
  Median: kế hoạch 501 ký tự / lời giải Solver 20 ký tự.
=> SOLVER KHÔNG GIẢI — NÓ CHÉP LẠI. Độ chính xác của nó gần như HOÀN TOÀN do Planner quyết định.

### GIẢI THÍCH ĐƯỢC 4 CÂU ĐỐ TRƯỚC ĐÓ, CÙNG MỘT LÚC
  1. Vì sao lời giải Solver chỉ 20 ký tự -> vì suy luận đã xảy ra ở bước LẬP KẾ HOẠCH.
  2. Vì sao Planner "làm tăng" acc (.632 -> .684) -> vì CHÍNH NÓ mới là người giải.
  3. Vì sao Verifier không có gì để kiểm -> suy luận nằm trong kế hoạch, pipeline KHÔNG chuyển tiếp.
  4. Vì sao H5 (truyền kế hoạch cho Verifier) VẪN thất bại -> truyền kế hoạch là truyền luôn LỖI
     của Planner, mà kế hoạch SAI tới 54.5%.

### HỆ QUẢ NGHIÊM TÚC CHO CHÍNH KHUNG SHAPLEY CỦA DỰ ÁN
BỐN VAI KHÔNG LÀM ĐÚNG VIỆC MÀ TÊN GỌI CỦA CHÚNG NÓI. Giá trị Shapley tính trên nhãn
"Planner/Solver/Verifier/Aggregator" là đang đo NHÃN, không phải đo CHỨC NĂNG.
Planner có đóng góp đo được thấp CHÍNH VÌ phần đóng góp của nó đã bị âm thầm tính sang cho Solver.
=> Bài học: trong hệ đa tác tử, PHẢI KIỂM TRA agent thực sự LÀM GÌ, đừng tin vào tên vai và prompt.
LƯU Ý: hiện tượng này ĐẶC THÙ GSM8K. Trên MATH, Solver vẫn viết 899 ký tự (median) và KHÔNG
  suy thoái thành chép lại — thêm một trường hợp của chủ đề "hiệu ứng không bền theo task".

## [Loop] VÒNG #12 — H8 CÓ PHÉP THỬ HỢP LỆ VÀ BỊ BÁC; H11 trên MATH ĐẢO DẤU
### ex_m7 (H8 chạy lại ở 7B) — NGƯỠNG HIỆU LỰC ĐẠT, rơi HÀNG 3
  exec_success_rate = .735  (>= .50 đã khoá trước -> LẦN NÀY LÀ PHÉP THỬ HỢP LỆ)
  exec_acc = .4286          (code CHẠY ĐƯỢC nhưng chỉ ĐÚNG 42.9%)
  L_llm  +6.5 | 17 sửa /  4 phá
  E_flag +2.5 |  9 sửa /  4 phá
  E_take -18.0|  7 sửa / 43 phá
=> H8 BỊ BÁC: verify bằng thực thi KHÔNG tổng quát sang math. Cả hai nhánh E đều THUA L_llm.
CƠ CHẾ ĐO ĐƯỢC: model viết được code CHẠY (73.5%) nhưng code chỉ TÍNH ĐÚNG 42.9% —
  còn THẤP HƠN cả việc nó giải trực tiếp (.625). Dịch đề toán bằng lời sang code ĐÚNG khó
  ngang với giải bài. Trên HumanEval thì ĐẶC TẢ ĐÃ Ở DẠNG HÌNH THỨC SẴN; trên MATH thì không.
=> KẾT LUẬN: verify cơ học chỉ dùng được KHI BÀI TOÁN VỐN ĐÃ LÀ CODE.

### ra_m15 (H11 trên MATH 1.5B) — PIPELINE ĐẦY ĐỦ LÀ ÂM
                    GSM8K 1.5B        MATH 1.5B
  P->S              .684              .425
  P->S->V           .732  (+4.8)      .445  (+2.0)
  P->S->V->A        .744  (+6.0)      .385  (-4.0)   <-- THẤP HƠN cả P->S
  P->S->A           .428  (-25.6)     .390  (-3.5)
=> Aggregator GIÚP trên GSM8K (+1.2 khi thêm vào sau V) nhưng PHÁ 6 điểm trên MATH
   (từ .445 xuống .385). THÊM MỘT LẦN ĐẢO DẤU.

### pp_m7 (H5 tại MATH 7B) — H5 BỊ BÁC Ở Ô THỨ TƯ
  V_none +4.0 (tốt nhất) | V_sol +3.5 | V_both +3.0 | V_plan -1.0
=> Truyền KẾ HOẠCH cho Verifier KHÔNG BAO GIỜ giúp, ở CẢ 4 Ô của lưới.

### HAI THỨ DUY NHẤT KHÔNG ĐẢO DẤU TRÊN TOÀN LƯỚI
  (1) Truyền kế hoạch cho Verifier: vô ích hoặc có hại — 4/4 ô.
  (2) Verifier có đóng góp DƯƠNG: GSM8K +4.8, MATH +2.0 — 2/2 task.
  Ngược lại, AGGREGATOR đảo dấu (+1.2 GSM8K / -6.0 MATH) -> đây là vai đáng ngờ nhất.

## [Loop] ĐỘ TRUNG THÀNH THỰC THI (execution fidelity) — BIẾN GIẢI THÍCH MẠNH NHẤT TÌM ĐƯỢC
Xuất phát từ đề xuất "đo entailment giữa các lượt agent". Kiểm chứng NGAY trên dữ liệu có sẵn
(GSM8K, n=200, 1.5B), với "trung thành" = đáp án Solver TRÙNG số cuối của kế hoạch:
                                 n     Solver đúng
  kế hoạch ĐÚNG  -> ĐI THEO      90    100.0%
  kế hoạch SAI   -> ĐI THEO      35      0.0%
  kế hoạch SAI   -> LỆCH         74     55.4%
  kế hoạch ĐÚNG  -> LỆCH          1      0.0%
  Median độ dài lời giải: trung thành 19 ký tự | lệch 358 ký tự
=> ĐỘ TRUNG THÀNH × CHẤT LƯỢNG KẾ HOẠCH GIẢI THÍCH GẦN NHƯ TOÀN BỘ độ chính xác của Solver.
   Không biến prompting nào chúng tôi đã thử tiệm cận được sức giải thích này.
=> GIẢ THUYẾT "LỆCH SÁNG TẠO" ĐƯỢC XÁC NHẬN: khi kế hoạch SAI, LỆCH là con đường DUY NHẤT
   dẫn tới đáp án đúng (55.4% so với ĐÚNG BẰNG 0%).

### BA ĐIỂM PHẢI SỬA TRONG ĐỀ XUẤT (đánh giá kỹ thuật)
1. "Giá trị Shapley của độ trung thành" KHÔNG HỢP LỆ VỀ MẶT HÌNH THỨC. Shapley phân bổ công
   giữa các NGƯỜI CHƠI trong liên minh; độ trung thành là BIẾN ĐỒNG HÀNH (covariate), không phải
   người chơi, không có liên minh để tham gia. Cách đúng: PHÂN TẦNG đóng góp của vai theo mức
   trung thành, hoặc thêm số hạng TƯƠNG TÁC. Cùng câu hỏi khoa học, nhưng công cụ đúng.
2. NLI LÀ CÔNG CỤ SAI — ĐÃ ĐO (analysis/trace_nli.py, 40 trace): bắt tốt "đồng ý" (15/24 kéo theo)
   và "sửa" (3/5 mâu thuẫn) nhưng BỎ SÓT HOÀN TOÀN "phá" (0/3) — mà "phá" mới là ca đáng quan tâm.
   NLI off-the-shelf không so nổi hai lời giải toán dài nhiều bước.
3. TRÊN GSM8K KHÔNG CÓ TRACE ĐỂ CHẠY NLI: khi Solver trung thành thì output chỉ 19 KÝ TỰ
   ("The answer is 366."). Tính entailment giữa kế hoạch 501 ký tự và chuỗi đó là vô nghĩa.
   Answer-agreement thì CHÍNH XÁC, MIỄN PHÍ, và chính nó tạo ra bảng số ở trên.

### PHIÊN BẢN NÊN CHẠY
Giữ KHUNG TƯ DUY của đề xuất (đo ĐỘ TRUNG THÀNH THỰC THI thay vì chỉ đo đáp án cuối), bỏ phần NLI:
  - tín hiệu cứng : answer-agreement (chính xác, chi phí 0)
  - tín hiệu mềm  : LLM-judge, CHỈ trên MATH (nơi Solver viết 899 ký tự, có trace thật)
  - phân tích     : PHÂN TẦNG — giá trị biên của Verifier có khác nhau giữa nhóm Solver
                    TRUNG THÀNH và nhóm LỆCH hay không?

## [Loop] AGENT NÀO THỰC SỰ TÍNH TOÁN? — CHỈ 2/4 (GSM8K, n=200, 1.5B)
Đo "số MỚI" = giá trị số xuất hiện trong output mà KHÔNG có trong input của agent đó
(proxy cho "có thực sự tính toán gì không").
  Agent        median ký tự   số MỚI/lượt   % lượt KHÔNG có số mới   đáp án = agent trước
  Planner            501            6              0.0%                    —
  Solver              20            0             69.0%                  62.5%
  Verifier           592            4             20.5%                  69.0%
  Aggregator          18            0            100.0%                  96.0%
=> PLANNER và VERIFIER thực sự TÍNH. SOLVER và AGGREGATOR chỉ CHUYỂN TIẾP.
   Aggregator KHÔNG SINH RA SỐ MỚI Ở 100% SỐ LƯỢT và lặp lại đáp án Verifier ở 96% —
   nó gần như là một no-op có kèm một lần gọi model.
=> "Pipeline 4 tác tử" thực chất là PIPELINE 2 TÁC TỬ (Planner + Verifier) cộng 2 trạm chuyển tiếp.

### GIẢI THÍCH ĐỒNG THỜI NHIỀU KẾT QUẢ TRƯỚC ĐÓ
  - Vì sao Aggregator đóng góp ~0 (+1.2 GSM8K, -6.0 MATH): nó KHÔNG BAO GIỜ tính gì.
    Hành động duy nhất của nó là CHỌN giữa hai đáp án có sẵn -> chỉ có thể mất, khó mà được.
  - Vì sao Shapley của Solver trông khá: nó được ghi công cho phép tính CỦA PLANNER.
  - Vì sao P->S->V là cấu hình tốt nhất: đó ĐÚNG BẰNG hai agent thực sự làm việc.
  - Vì sao P->S->A sụp còn .428: aggregator chỉ có MỘT ứng viên thì không có gì để chọn,
    nó phải tự bịa, mà nó lại không tính toán được.
LƯU Ý: đây là GSM8K 1.5B. Trên MATH, Solver viết 899 ký tự (median) nên nhiều khả năng NÓ CÓ TÍNH.
  Nếu đúng thì PHÂN CÔNG LAO ĐỘNG GIỮA CÁC VAI THAY ĐỔI THEO TASK — khớp với toàn bộ chủ đề
  "hiệu ứng không bền" của dự án. Kernel pt_m15/pt_m7 đang chạy sẽ trả lời.

## [Loop] GIẢ THUYẾT ĐỊNH TUYẾN THEO ĐỘ TRUNG THÀNH — KHÔNG ĐƯỢC ỦNG HỘ (và THIẾU LỰC THỐNG KÊ)
Giả thuyết đề xuất: Verifier chỉ hữu ích khi Solver SAI LỆCH khỏi kế hoạch; gọi nó trên ca
TRUNG THÀNH là tốn kém và có thể gây sycophancy.
ĐO TRÊN GSM8K traces (n=200, 1.5B). LƯU Ý: phân tích HẬU NGHIỆM, KHÔNG pre-register.
  Tầng                       n    Solver   Verifier   sửa  phá   giá trị biên   sign test
  TRUNG THÀNH (theo plan)  125     72.0%     75.2%     15   11      +3.2%        p=.56
  SAI LỆCH   (khác plan)    75     54.7%     60.0%      4    0      +5.3%        p=.13
=> Verifier DƯƠNG Ở CẢ HAI TẦNG. Giả thuyết dự đoán tầng TRUNG THÀNH sẽ ~0 hoặc ÂM — thực tế +3.2.
   HƯỚNG của trực giác thì đúng (tầng lệch có biên lớn hơn và 0 phá), nhưng khoảng cách nhỏ
   và KHÔNG tầng nào đạt ý nghĩa thống kê (26 và 4 cặp bất đồng).
=> KẾT LUẬN TRUNG THỰC: với n=200, DỮ LIỆU KHÔNG ĐỦ SỨC PHÂN GIẢI câu hỏi này. Không được
   kết luận theo hướng nào. Cần n lớn hơn nhiều (ước lượng >=600 để tách +3.2 khỏi +5.3).

### MÔ PHỎNG BỘ ĐỊNH TUYẾN (n=200)
  không bao giờ gọi Verifier : 65.5%   (0% lần gọi)
  LUÔN gọi Verifier          : 69.5%   (100% lần gọi)
  ĐỊNH TUYẾN (chỉ khi lệch)  : 67.5%   (38% lần gọi)
=> Bộ định tuyến MẤT 2.0 điểm chính xác để TIẾT KIỆM 62% lần gọi Verifier.
   Đây là một ĐIỂM HỢP LỆ trên đường cong chi phí–chất lượng, KHÔNG PHẢI "thắng miễn phí"
   như giả thuyết ngụ ý. Bỏ Verifier ở ca trung thành làm MẤT độ chính xác thật (15 ca được sửa).

### PHẦN CÒN ĐÚNG CỦA Ý TƯỞNG
Tín hiệu đáng chú ý là 0 PHÁ ở tầng SAI LỆCH: khi Solver đã đi lệch kế hoạch, Verifier dường như
CHỈ CÓ THỂ GIÚP. Nếu điều này còn đúng ở n lớn, chính sách nên là PHÂN CẤP chứ không nhị phân:
"luôn verify ca lệch; verify ca trung thành nếu còn ngân sách."

## [Loop] VÒNG #13 — DỰ ĐOÁN ĐÚNG (hiếm), THÊM MỘT ĐẢO DẤU, VÀ MỘT MÂU THUẪN PHẢI CÔNG BỐ

### pt_m15 — HIỆU ỨNG "PLANNER GIẢI HỘ" LÀ ĐẶC THÙ GSM8K (dự đoán TRƯỚC khi chạy: ĐÚNG)
Tôi đã tuyên bố trước: "hiệu ứng chép lại sẽ YẾU HƠN NHIỀU trên MATH". XÁC NHẬN:
                                  GSM8K     MATH
  copycat_rate                     61%      6.5%
  Solver < 60 ký tự                69%     11.5%
  đáp án Solver = số cuối plan    62.5%      28%
  plan chứa đáp án đúng           45.5%     18.5%
  median lời giải Solver           20      910 ký tự
=> Trên MATH, Solver THỰC SỰ LÀM VIỆC, không chép.
NHƯNG PHÂN TÁCH ĐỘ CHÍNH XÁC VẪN CÒN: plan ĐÚNG -> 97.3% | plan SAI -> 31.9%
   (GSM8K: 98.9% / 37.6%) — gần như y hệt, dù việc chép lại đã biến mất.
CẢNH BÁO NHIỄU (bắt buộc ghi): trên MATH chỉ 18.5% kế hoạch đúng -> "plan đúng" nhiều khả năng
   TRÙNG với "bài dễ". Phân tách này có thể là NHIỄU ĐỘ KHÓ, không phải kế hoạch gây ra kết quả.
   Trên GSM8K việc chép làm quan hệ gần nhân quả; trên MATH thì CHƯA CHỨNG MINH ĐƯỢC.

### H12 (bỏ phiếu thay Aggregator-LLM) — rơi HÀNG 5: LẠI ĐẢO DẤU
                    GSM8K     MATH
  PS                 .684      .425
  PSV                .732      .445
  PSVA (LLM agg)     .744      .385
  PSV_vote5          .688      .460
  bỏ phiếu vs LLM   -5.6      +7.5
=> Bỏ phiếu THUA trên GSM8K, THẮNG trên MATH. Đây là can thiệp THỨ SÁU đảo dấu giữa hai task.
=> Trên GSM8K cấu hình tốt nhất là PSVA; trên MATH là PSV_vote5, còn PSVA là TỆ NHẤT.

### am_7 (H7 ở 7B) — VÀ MỘT MÂU THUẪN GIỮA HAI THÍ NGHIỆM CỦA CHÍNH CHÚNG TÔI
  maj@8 .7583 | A_answers .7167 (-4.2) | A_masked .675 (-8.3) | A_full .6417 (-11.7)
  => Mọi nhánh LLM đều THUA bỏ phiếu -> rơi HÀNG 4. Che số giúp +3.3 nhưng không cứu được.
MÂU THUẪN PHẢI CÔNG BỐ: agf_7 (cùng 7B, cùng MATH, n=120) cho agg_full_sol .7333 vs maj .7167,
  tức aggregator THẮNG bỏ phiếu (+1.7). am_7 cho A_full .6417 vs maj .7583, tức THUA (-11.7).
  Hai thí nghiệm gần như cùng thiết lập, KẾT LUẬN NGƯỢC NHAU. Ngay cả mốc maj@8 cũng khác
  (.7167 vs .7583) -> bể mẫu khác nhau. TÔI KHÔNG GIẢI THÍCH ĐƯỢC. Ghi lại cả hai.
  Đây là bằng chứng thêm cho chính chủ đề của dự án: các hiệu ứng này KHÔNG BỀN, và
  KHÔNG ĐỦ ỔN ĐỊNH để rút kết luận từ MỘT lần chạy.

## [Loop] VÒNG #14 — SỬA LỖI KERNEL SÀN NHIỄU, CHƯA CÓ KẾT QUẢ MỚI
nf_m15 và nf_g15 (thí nghiệm SÀN NHIỄU) đều ERROR ngay từ đầu:
  `NameError: name 'rows' is not defined` (dòng 23)
NGUYÊN NHÂN: khi sinh kernel từ roleablate_kernel.py, tôi thay dòng `rows=list(...)` bằng
  `ALL=...; NF=5; FOLD=...` nhưng dòng print NGAY SAU vẫn tham chiếu `len(rows)`.
ĐÃ SỬA + kiểm tra bằng `ast.parse` và kiểm tra không còn tham chiếu `rows` trước vòng lặp fold,
  rồi đẩy lại version 2.
BÀI HỌC QUY TRÌNH: các kernel sinh ra bằng cách thay chuỗi phải được PARSE THỬ TẠI MÁY trước khi
  đẩy lên Kaggle. Hai lần chạy GPU đã bị lãng phí cho một lỗi 1 dòng mà `ast.parse` bắt được ngay.
  Từ nay: luôn `ast.parse` bản đã thay placeholder trước khi push.
4 kernel còn lại (tr_g7, tr_m7, ra_m7, pt_m7 — đều là nhánh 7B 4-bit) vẫn đang chạy, chưa có số.

## [Loop] VÒNG #15 — SÀN NHIỄU (H13): RƠI HÀNG 2. PHẢI HẠ CẤP CÁC KHẲNG ĐỊNH NHỎ.
nf_g15 — GSM8K 1.5B, CÙNG cấu hình chạy trên 5 FOLD RỜI NHAU (mỗi fold 100 bài):
  fold 0: PS .68 PSV .76 PSVA .75 | V_gain +8.0 | A_gain -1.0
  fold 1: PS .67 PSV .68 PSVA .71 | V_gain +1.0 | A_gain +3.0
  fold 2: PS .69 PSV .72 PSVA .73 | V_gain +3.0 | A_gain +1.0
  fold 3: PS .66 PSV .69 PSVA .71 | V_gain +3.0 | A_gain +2.0
  fold 4: PS .64 PSV .71 PSVA .72 | V_gain +7.0 | A_gain +1.0
  V_gain: mean +4.4, range 7.0 (từ +1.0 tới +8.0), std 2.65
  A_gain: mean +1.2, range 4.0 (từ -1.0 tới +3.0), std 1.33
=> CÙNG MỘT THÍ NGHIỆM, CHẠY 5 LẦN, CHO GIÁ TRỊ VERIFIER TỪ +1.0 ĐẾN +8.0.
=> Rơi HÀNG 2 đã khoá trước: PHẢI HẠ CẤP mọi khẳng định dựa trên MỘT lần chạy ở n<=250.

### CÁI GÌ BỊ HẠ CẤP (bắt buộc)
  Khoảng của A_gain (-1.0 .. +3.0) CHỨA SỐ 0 và có phần ÂM.
  => Khẳng định "Aggregator đóng góp +1.2 trên GSM8K" (từ ra_g15) KHÔNG PHÂN BIỆT ĐƯỢC VỚI NHIỄU.
     HẠ CẤP khẳng định này.
  Quy đổi std sang n=250: ~1.7 điểm. HIỆU CỦA HAI phép đo có std ~2.4 -> NGƯỠNG 2 sigma ~ 5 ĐIỂM.
  => MỌI hiệu ứng NHỎ HƠN ~5 ĐIỂM, đo MỘT LẦN ở n<=250, KHÔNG PHẢI LÀ BẰNG CHỨNG.

### CÁI GÌ SỐNG SÓT
  Các lần ĐẢO DẤU đều vượt ngưỡng 5 điểm:
    truyền trace (H10) 16.6 | bỏ phiếu vs LLM-agg (H12) 13.1 | che giá trị (H6) 10.4
    X_cross 9.1 | verifier bịt mắt (H1) 8.0 | vai Aggregator 7.2 (sát ngưỡng)
  => PHÁT HIỆN CHÍNH CỦA DỰ ÁN (hiệu ứng đảo dấu theo task/cỡ model) VẪN ĐỨNG.
     Nhưng NHIỀU CHI TIẾT PHỤ trong đó thì KHÔNG.

### HAI KẾT QUẢ KHÁC
pt_m7 (MATH 7B): copycat_rate 0.0% | Solver <60 ký tự 0.0% | plan chứa đáp án đúng chỉ 7%
  => Hiệu ứng "Planner giải hộ" giờ đã được xác nhận là ĐẶC THÙ GSM8K-1.5B qua BA thiết lập.
tr_g7 (GSM8K 7B, solver .916): FULL .904 | TRIM .912 | NOVA .896 | solo .916
  => truyền trace đáng +0.8 (so với +7.6 ở 1.5B) — NẰM TRONG NHIỄU. Khi đã bão hoà, không gì
     còn quan trọng nữa.

### GHI CHÚ TỰ PHÊ BÌNH
Đây là phép đo lẽ ra phải chạy ĐẦU TIÊN, trước khi diễn giải bất kỳ hiệu ứng nào. Việc chạy nó
muộn khiến nhiều vòng trước đã dành công sức diễn giải các chênh lệch 1-3 điểm vốn không có ý nghĩa.

## [Loop] VÒNG #16 — CÓ THANH SAI SỐ CHO CẢ HAI TASK: MỘT SỐ KẾT LUẬN ĐỔI HẲN
### nf_m15 — SÀN NHIỄU trên MATH (5 fold x 100 bài)
  fold: V_gain +4,-1,+1,+4,-1 | A_gain -6,-7,-6,-9,-4
  V_gain: mean +1.4, range [-1.0, +4.0], std 2.24   <-- CHỨA SỐ 0
  A_gain: mean -6.4, range [-9.0, -4.0], std 1.62   <-- TOÀN ÂM
  PS: mean .402 nhưng range .14 (từ .34 tới .48) — MATH các fold LỆCH ĐỘ KHÓ RẤT NHIỀU,
      đây là lý do hiệu ứng trên MATH nhiễu hơn GSM8K nhiều.

### BẢNG ĐỐI CHIẾU CÓ THANH SAI SỐ (thay cho các con số đo MỘT LẦN trước đây)
              GSM8K 1.5B                        MATH 1.5B
  V_gain      +4.4  [+1.0, +8.0]  TOÀN DƯƠNG    +1.4  [-1.0, +4.0]  CHỨA 0
  A_gain      +1.2  [-1.0, +3.0]  CHỨA 0        -6.4  [-9.0, -4.0]  TOÀN ÂM
=> PHẢI SỬA LẠI BA KHẲNG ĐỊNH:
  1. "Verifier mang gần như toàn bộ giá trị" -> ĐÚNG trên GSM8K; TRÊN MATH CHƯA XÁC LẬP (chứa 0).
  2. "Aggregator có hại trên MATH" -> XÁC NHẬN, cả 5 fold đều âm, khoảng [-9, -4].
  3. "Aggregator +1.2 trên GSM8K" -> VẪN BỊ HẠ CẤP (khoảng chứa 0).
=> ĐẢO DẤU CỦA VAI AGGREGATOR LÀ THẬT khi có thanh sai số:
   GSM8K [-1,+3] và MATH [-9,-4] KHÔNG CHỒNG LẤN.

### rc_g15 — H14 (nửa GSM8K)
  trim_minus_full theo fold: -8, -7, -2, -8, -10
  mean -7.0, range [-10.0, -2.0], std 2.68  -> CẢ 5 FOLD ĐỀU ÂM
=> Trên GSM8K, cắt trace LÀM HẠI một cách ổn định (~7 điểm). Chờ rc_m15 để xét chồng lấn
   và chốt kết luận cho H14 (phát hiện chủ đạo của dự án).

## [Loop] VÒNG #17 — ra_m7 rơi HÀNG 4; LƯỚI 4 Ô GIỜ ĐÃ ĐẦY ĐỦ VÀ RẤT TỈNH TÁO
### ra_m7 (H11 tại MATH 7B, n=200, solver .640)
  P->S .640 | P->S->V .675 (+3.5) | P->S->V->A .670 (+3.0) | P->S->A .650 (+1.0)
=> MỌI hiệu ứng đều DƯỚI ngưỡng nhiễu 5 điểm. Theo đúng quy tắc tôi đã tự khoá:
   KHÔNG cái nào tính là bằng chứng. Rơi HÀNG 4: "không vai nào đóng góp gì".

### LƯỚI GIÁ TRỊ CỦA VERIFIER — CẢ 4 Ô, ĐỌC CÙNG MỘT NGƯỠNG
                 GSM8K                              MATH
  1.5B    +4.4  [+1, +8]  5/5 fold  XÁC LẬP    +1.4  [-1, +4]  chứa 0  CHƯA XÁC LẬP
  7B      ~0    (solver đã bão hoà .916)       +3.5  1 lần đo, dưới ngưỡng  CHƯA XÁC LẬP
=> LỢI ÍCH CỦA ĐA TÁC TỬ CHỈ ĐƯỢC XÁC LẬP Ở ĐÚNG 1/4 Ô CỦA LƯỚI.
=> PHÁT BIỂU ĐÚNG KHÔNG PHẢI "đa tác tử có ích", MÀ LÀ:
   "đa tác tử có ích với MODEL YẾU trên BÀI DỄ, và không ở đâu khác mà chúng tôi đo được."
Đây là phát biểu tỉnh táo hơn nhiều so với mọi thứ dự án từng viết ra trước đó, và nó chỉ
xuất hiện được SAU KHI đo sàn nhiễu.

## [Loop] TỰ KIỂM: TÔI KHÔNG ĐỌC OUTPUT THÔ — VÀ ĐÓ LÀ LỖ HỔNG NGHIÊM TRỌNG
Kiểm kê: **3/26 kernel** có lưu trace thô (trace_kernel, plantrace_math_kernel, gendata_kernel).
23 kernel còn lại VỨT BỎ toàn bộ văn bản mô hình sinh ra, chỉ giữ số tổng hợp.
Trong suốt dự án tôi chỉ ĐỌC văn bản thô ĐÚNG HAI LẦN — và cả hai lần đều ra phát hiện
giải thích được nhiều nhất trong vòng đó:
  (1) đọc output Planner -> phát hiện Planner giải hộ, Solver chép lại (giải thích 4 câu đố)
  (2) chấm tay 6 ca "phá" -> phát hiện Verifier không hỏng ở khâu KIỂM, mà bị ép GIẢI LẠI.

### ĐỌC TRACE MATH (chưa từng mở) -> PHÁT HIỆN NGAY MỘT LỖI ĐO
case 3 (pt_m15): Planner tính đủ `(2+1)(2+1) = 3 x 3 = 9`, tức ĐÃ GIẢI XONG.
Nhưng `plan_tail` của tôi trích ra `"9\)."` — dính dấu đóng LaTeX -> so với gold `"9"` -> BÁO TRƯỢT.
NGUYÊN NHÂN: hàm norm() bỏ `\left`/`\right` nhưng KHÔNG bỏ `\(` `\)` `\[` `\]`.
### SỐ LIỆU SAU KHI SỬA
                                  kernel báo   ->   tính lại
  MATH 1.5B plan chứa đáp án đúng    .185           .225
  MATH 1.5B Solver = plan            .280           .350
  MATH 7B   plan chứa đáp án đúng    .070           .155   <-- SAI HƠN 2 LẦN
  MATH 7B   Solver = plan            .095           .200
  MATH 1.5B: plan ĐÚNG (n=45) -> Solver đúng 100.0% | plan SAI (n=155) -> 27.7%
  MATH 7B  : plan ĐÚNG (n=31) -> Solver đúng  96.8% | plan SAI (n=169) -> 55.6%
=> KẾT LUẬN ĐỊNH TÍNH VẪN ĐÚNG (GSM8K 45.5% vs MATH 22.5%, vẫn gấp ~2 lần) NHƯNG
   ĐỘ LỚN TÔI ĐÃ BÁO CÁO SAI TỚI 2 LẦN, nặng nhất đúng ở ô 7B nơi tôi kết luận "gần bằng 0".

### BÀI HỌC QUY TRÌNH (nghiêm trọng hơn bản thân lỗi này)
23/26 kernel không lưu output -> KHÔNG THỂ kiểm tra hồi tố phần lớn kết quả của dự án.
Mọi lỗi trích xuất/chấm điểm tương tự trong các kernel đó sẽ KHÔNG BAO GIỜ bị phát hiện.
QUY TẮC TỪ NAY: mọi kernel PHẢI lưu ít nhất một mẫu output thô (vd 50 trace) cùng summary.
Số tổng hợp chỉ đáng tin khi còn cách kiểm lại được văn bản sinh ra nó.

## [Loop] VÒNG #18 — H14 RƠI HÀNG 2: PHÁT HIỆN CHỦ ĐẠO CỦA DỰ ÁN BỊ HẠ CẤP
rc_m15 (MATH, 5 fold) — trim_minus_full theo fold: -6, +4, +4, +3, -3
  mean **+0.4**, range **[-6, +4]**, std 4.13  -> CHỨA SỐ 0, hai dấu lẫn lộn
rc_g15 (GSM8K, 5 fold): mean -7.0, range [-10, -2], 5/5 ÂM
KIỂM TRA CHỒNG LẤN: GSM8K [-10,-2] và MATH [-6,+4] -> GIAO NHAU tại [-6,-2]. CÓ CHỒNG LẤN.
=> Rơi HÀNG 2 đã khoá trước: "PHÁT HIỆN CHỦ ĐẠO BỊ HẠ CẤP — phải sửa README và RESULTS.md".
=> Con số +9.0 trên MATH (tr_m15, đo 1 lần) LÀ NHIỄU. Chạy 5 fold cho +0.4.
=> "Đảo dấu 16.6 điểm" KHÔNG SỐNG SÓT khi có thanh sai số.
PHÁT BIỂU ĐÚNG (đã cập nhật README): truyền trace CÓ ÍCH trên GSM8K (-7.0 khi cắt, 5/5 fold),
  và KHÔNG ĐO ĐƯỢC tác dụng trên MATH ([-6,+4]). Đó là PHỤ THUỘC ĐỘ LỚN theo task,
  KHÔNG PHẢI đảo dấu.
ĐÃ THỰC HIỆN: viết lại tiêu đề + phần "Hướng chính" của README, thêm mục "Phát biểu đã bị RÚT LẠI".

### ft_g15 — trace đầy đủ đầu tiên (GSM8K, n=300) và BA cách trích khác nhau
  acc S .6733 | V .7067 | A .7233 | V_fix 32 / V_break 22
  median độ dài: plan 418 | sol 18 | ver 577 | agg 18
  plan_boxed_rate .033 | plan_has_ans_boxed .013 | plan_has_ans_tail .320
=> BA cách trích "đáp án ngầm của kế hoạch" cho kết quả RẤT KHÁC NHAU (1.3% vs 32%).
   Đây chính là lý do phải lưu trace: con số "Planner đã giải hộ 45.5%" phụ thuộc MẠNH vào
   lựa chọn trích xuất, và trước đây chỉ có MỘT cách được lưu lại.

### LỖI KERNEL (thứ hai liên tiếp do sinh code bằng thay chuỗi)
nf_g7/nf_m7 lỗi `NameError: _sp is not defined`: bản vá 7B chèn `import subprocess as _sp` vào
  NHÁNH else (fp16) trong khi lệnh dùng nó nằm ở mức module. Thực ra noisefloor_kernel ĐÃ tự xử lý
  QUANT nên BẢN VÁ LÀ THỪA. Đã bỏ vá, đẩy lại version 2.
  `ast.parse` KHÔNG bắt được lỗi này (cú pháp vẫn hợp lệ) -> cần thêm kiểm tra ngữ nghĩa,
  hoặc tốt hơn: ĐỪNG sinh kernel bằng thay chuỗi khi template đã có sẵn tham số.

## [Loop] VÒNG #19 — HỢP NHẤT (theo đúng cam kết ở pre-registration #15: DỪNG mở giả thuyết mới)
Không có kernel nào xong trong vòng này (5 kernel vẫn chạy). Chuyển sang RÀ SOÁT các khẳng định
cũ mâu thuẫn với sàn nhiễu.

### 1. HẠ CẤP TOÀN BỘ BẢNG "ĐẢO DẤU" trong RESULTS.md
Bảng này từng là PHÁT HIỆN CHỦ ĐẠO với 5 dòng. Sự thật:
  - CHỈ 1/5 dòng từng được kiểm bằng 5 fold (truyền trace, H14) -> VÀ NÓ ĐÃ SỤP.
  - 4 dòng còn lại vẫn là đo MỘT LẦN mỗi ô, CHƯA TỪNG có thanh sai số.
=> Đã đánh dấu 4 dòng đó là "⚠️ CHƯA KIỂM CHỨNG" và ghi rõ:
   "Không có lý do gì để tin bốn dòng còn lại vững hơn dòng đã sụp."
   Đây là suy luận bắt buộc: cùng một quy trình đo, cùng cỡ mẫu, cùng loại hiệu ứng.

### 2. THÊM CẢNH BÁO VÀO BẢNG SHAPLEY GỐC (README mục 2)
Bảng φ ban đầu (Solver +0.252, Verifier +0.252, Aggregator +0.190, Planner -0.014) được tính
TRƯỚC khi có sàn nhiễu. Đối chiếu ngưỡng ~5 điểm:
  - Solver vs Verifier: chênh 0 -> vô nghĩa để xếp hạng
  - Aggregator so với hai vai kia: chênh ~6 điểm, SÁT ngưỡng
  - Bảng MATH (φ .017 -> .148): MỌI chênh lệch DƯỚI ngưỡng -> KHÔNG xếp hạng được
=> Đã thêm cảnh báo đọc ngay trên bảng, dẫn sang RESULTS.md mục 0-1 cho các kết luận đã kiểm.

### GHI CHÚ TỰ ĐÁNH GIÁ
Hai vòng gần nhất không tạo ra kết quả mới nào — chỉ đi HẠ CẤP kết quả cũ của chính mình.
Đó là công việc đúng đắn ở giai đoạn này, nhưng cũng cho thấy: nếu đo sàn nhiễu TỪ ĐẦU,
phần lớn 19 vòng vừa qua đã có thể tránh được.

## [Loop] VÒNG #20 — H15 RƠI HÀNG 1: XÁC NHẬN. KẾT QUẢ MẠNH NHẤT CỦA DỰ ÁN SỐNG SÓT.
as_m — MATH, 5 fold x 60 (n=300), Solver 1.5B + Verifier {1.5B | 7B}, cả 2 model cùng trên GPU:
  V7_gain      mean +14.0  range [+8.3, +20.0]  5/5 fold DƯƠNG   <-- không chứa 0
  V7_minus_V15 mean +11.0  range [+3.3, +16.7]  5/5 fold DƯƠNG   <-- không chứa 0
  V15_gain     mean  +3.0  range [ 0.0,  +6.7]  CHỨA 0           <-- CHƯA XÁC LẬP
  Tổng 300 bài: verifier 7B = 43 SỬA / 1 PHÁ | verifier 1.5B = 15 SỬA / 6 PHÁ
=> Rơi HÀNG 1 của pre-registration #14: XÁC NHẬN. Đây là kết quả dương DUY NHẤT của dự án
   vượt qua kiểm chứng bằng thanh sai số.

### BA ĐIỀU ĐƯỢC XÁC LẬP MÀ TRƯỚC ĐÂY CHƯA CÓ
1. Con số "+18 điểm ở n=50" LÀ THẬT — nó nằm TRONG khoảng [+8.3, +20.0] đo ở n=300.
   Tôi từng cảnh báo "9 sửa / 0 phá có thể do may mắn"; ở n=300 tỉ lệ là 43 SỬA / 1 PHÁ.
2. Lợi ích đến từ việc VERIFIER MẠNH HƠN, KHÔNG phải từ việc CÓ verifier.
   V7 - V15 dương ở 5/5 fold. Verifier CÙNG CỠ chỉ cho +3.0 với khoảng chạm 0 -> vô giá trị.
   Đây là phân tách mà thí nghiệm n=50 ban đầu KHÔNG hề tách được.
3. Kết quả này ở trên MATH — đúng cái task mà Verifier, Aggregator, truyền trace và che giá trị
   ĐỀU THẤT BẠI. Bất đối xứng năng lực hoạt động ĐÚNG Ở NƠI mọi thứ khác không hoạt động.

### HỢP NHẤT VỚI CÂU ĐỐ MATH TRƯỚC ĐÓ
nf_m15: verifier 1.5B trên MATH = +1.4 [-1, +4] -> CHƯA XÁC LẬP.
as_m  : verifier 7B  trên MATH = +14.0 [+8.3, +20.0] -> XÁC LẬP.
=> Giá trị của vai Verifier trên MATH KHÔNG nằm ở VAI TRÒ, mà nằm HOÀN TOÀN ở NĂNG LỰC model.
   Một verifier yếu ngang solver thì vô dụng; một verifier mạnh hơn thì đáng +14 điểm.
   Phát biểu này giải thích được vì sao mọi thí nghiệm verifier đồng cỡ trên MATH đều ra ~0.

## [Loop] VÒNG #21 — BA KẾT QUẢ HỘI TỤ VỀ MỘT LỜI GIẢI THÍCH: TẤT CẢ LÀ NĂNG LỰC
### nf_g7 (H16, GSM8K 7B, 5 fold) — solver .884 (gần bão hoà)
  V_gain mean +1.0 range [-3, +5] CHỨA 0 | A_gain mean +0.4 range [-1, +1] CHỨA 0
=> Khi solver đã mạnh, KHÔNG vai nào có giá trị đo được. Khớp HÀNG 1 của pre-reg #15 (chờ nf_m7).

### tr_m7 (H10 tại MATH 7B, n=200) — truyền trace ĐÁNG +17.5 ĐIỂM
  solo .625 | FULL .680 | TRIM .505 | NOVA .640
  trim_minus_full = -17.5   full_minus_solo = +5.5
  ĐỐI CHIẾU MATH 1.5B (rc_m15, 5 fold): trim_minus_full = +0.4, khoảng [-6, +4] -> KHÔNG có gì.
=> Cắt trace mất 17.5 điểm ở 7B nhưng KHÔNG mất gì ở 1.5B. Vượt xa ngưỡng nhiễu 5 điểm,
   NHƯNG là đo MỘT LẦN -> cần kiểm bằng 5 fold trước khi khẳng định.

### ft_m15 (trace đầy đủ MATH 1.5B, n=300)
  acc_S .4133 | acc_V .4267 | acc_A .3733 (Aggregator LÀM MẤT 9 điểm — khớp nf_m15 A_gain -6.4)
  median: plan 873 | sol 986 | ver 1087 | agg 142
  plan_boxed .157 | plan_has_ans_boxed .070 | plan_has_ans_tail .173
  (GSM8K tương ứng: .033 / .013 / .320) -> "Planner giải hộ" vẫn là hiện tượng của GSM8K.

### HỢP NHẤT: MỌI THỨ QUY VỀ NĂNG LỰC CỦA MODEL ĐI KIỂM
  Trên MATH:            1.5B                          7B
  giá trị Verifier      +1.4  [-1, +4]  KHÔNG          +14.0 [+8.3, +20.0]  CÓ (5/5 fold)
  giá trị truyền trace  +0.4  [-6, +4]  KHÔNG          +17.5 (1 lần đo)     CÓ
  Aggregator            -6.4  [-9, -4]  HẠI            ~0
=> PHÁT BIỂU HỢP NHẤT: BỘ MÁY ĐA TÁC TỬ CHỈ HOẠT ĐỘNG KHI MODEL ĐI KIỂM ĐỦ MẠNH ĐỂ
   DÙNG ĐƯỢC THỨ NÓ ĐƯỢC ĐƯA. Ở 1.5B, verifier không khai thác nổi trace -> truyền trace vô ích
   và MỌI can thiệp đều thất bại. Ở 7B, cả verifier lẫn trace đều bắt đầu sinh lợi.
   Một câu này giải thích được: H15 (xác nhận), tr_m7, và gần như toàn bộ thất bại ở 1.5B
   suốt 20 vòng vừa qua.

## [Loop] VÒNG #22 — HỢP NHẤT TIẾP (không mở thí nghiệm mới, theo cam kết pre-reg #16)
Hai kernel cuối (nf_m7, rc_m7) vẫn chạy. Không có số mới. Tiếp tục RÀ SOÁT tài liệu.

### Đã sửa trong RESULTS.md
1. §3 (phân bổ đóng góp): con số "Aggregator thêm +1.2" nay ghi rõ DƯỚI ngưỡng nhiễu và
   khoảng [-1,+3] chứa 0 -> KHÔNG phải bằng chứng. Phần Verifier +4.8 nay dẫn kèm bản đã
   kiểm 5 fold (+4.4, [+1,+8]).
2. §4 (giá trị V,A phụ thuộc context): chênh lệch -1.6 (TRIM vs NOVA) DƯỚI ngưỡng -> không
   kết luận. Phần còn đứng: FULL vs TRIM = -7.0 [-10,-2] 5/5 fold trên GSM8K; trên MATH 1.5B
   thì KHÔNG ([-6,+4]).
3. Thêm §4b: PHÁT BIỂU HỢP NHẤT, kèm cảnh báo rõ rằng NỬA SAU (phần về trace) mới chỉ có
   MỘT phép đo và đang được kiểm bởi rc_m7.

### TRẠNG THÁI TÀI LIỆU
Mọi con số trong RESULTS.md giờ đều được gắn một trong ba nhãn:
  ✅ đã kiểm 5 fold, mọi fold cùng dấu
  ⚠️ chưa kiểm / đang kiểm / dưới ngưỡng nhiễu
  ❌ đã bị hạ cấp hoặc rút lại
Đây là điều lẽ ra phải làm từ vòng đầu, nhưng chỉ khả thi sau khi có sàn nhiễu.

## [Loop] VÒNG #23 — KẾT LUẬN CUỐI CÙNG (VÀ KHẮC NGHIỆT NHẤT) CỦA DỰ ÁN
Tính từ dữ liệu ĐÃ CÓ, không cần kernel mới:
                              1.5B solo   cấu hình đa tác tử TỐT NHẤT   7B SOLO      chênh
  GSM8K                        .6680       .7240  (+5.6đ)               **.8840**   -16.0đ
  MATH                         .4233       .5633  (+14.0đ)              **.6250**   - 6.2đ
CHI PHÍ THÔ: pipeline 1.5B 4 vai = 4 lượt x 1.5B = 6.0B-params-lượt (còn sinh NHIỀU token hơn)
             7B solo            = 1 lượt x 7B   = 7.0B-params-lượt
=> XẤP XỈ NHAU VỀ COMPUTE. Nhưng 7B-solo CHÍNH XÁC HƠN Ở CẢ HAI TASK.

### => MỌI "CẢI THIỆN" MÀ DỰ ÁN XÁC NHẬN ĐỀU BỊ THỐNG TRỊ BỞI "CHỈ DÙNG MODEL LỚN HƠN"
  Cả hai kết quả đã kiểm bằng 5 fold (+5.6đ pipeline GSM8K; +14.0đ bất đối xứng MATH)
  đều là cải thiện SO VỚI MỐC YẾU. Khi so với phương án đơn giản nhất — bỏ hẳn kiến trúc
  đa tác tử và dùng model lớn hơn — cả hai đều THUA, ở mức compute tương đương.
  Khoảng cách 16.0đ và 6.2đ đều VƯỢT XA ngưỡng nhiễu 5 điểm -> hướng kết luận là chắc chắn.

### VÌ SAO ĐIỀU NÀY QUAN TRỌNG
Các nghiên cứu đa tác tử thường so với mốc "cùng model, một lượt gọi" — mốc đó DỄ THẮNG.
Rất hiếm khi so với "dùng model lớn hơn ở compute tương đương". Dự án này đã đo cả hai,
và kết quả đảo ngược hoàn toàn kết luận.

### CẢNH BÁO TRUNG THỰC
1. Đây là so sánh CHÉO KERNEL trên các tập con KHÁC NHAU. Kernel bs_m đang chạy sẽ cho
   so sánh đầu-đối-đầu SẠCH trên MATH; cần một kernel tương tự cho GSM8K.
2. Hạch toán compute là THÔ (số lượt x số tham số), chưa tính chính xác token sinh ra.
3. Chỉ 2 task, 2 cỡ model. Không suy rộng ra mọi kiến trúc đa tác tử.
NHƯNG: với biên độ 16 và 6.2 điểm so với ngưỡng nhiễu 5 điểm, HƯỚNG của kết luận khó đảo.

## [Loop] VÒNG #24 — ĐƯA KẾT LUẬN CHÍNH LÊN ĐẦU README (không có kernel nào xong)
4 kernel vẫn chạy. Công việc vòng này: sửa README, vì nó vẫn đang KHUYẾN NGHỊ một cấu hình
mà chính dữ liệu của mình cho thấy là BỊ THỐNG TRỊ.
- Vòng #20 tôi đã đưa "dùng model nhỏ GIẢI, model lớn SOÁT" lên tiêu đề README.
- Vòng #23 phát hiện cấu hình đó THẤP HƠN 7B-solo 6.2 điểm (MATH) và pipeline 1.5B thấp hơn
  7B-solo 16.0 điểm (GSM8K), ở compute tương đương.
=> Đã thay phần đầu README bằng KẾT LUẬN CHÍNH có cảnh báo ⚠️, giữ nguyên bảng các kết quả
   đã kiểm 5 fold (chúng vẫn ĐÚNG — chỉ là cải thiện so với mốc yếu), và ghi rõ rằng
   bs_m/bs_g đang chạy để kiểm chéo; nếu chúng lật kết quả thì mục này sẽ bị rút lại.
GHI CHÚ: đây là lần thứ HAI trong dự án tôi phải hạ cấp chính thứ mình vừa đưa lên tiêu đề
   (lần trước: bảng "đảo dấu"). Bài học: KHÔNG đưa kết quả lên tiêu đề khi chưa so với
   MỌI mốc tầm thường có liên quan — đặc biệt mốc "chỉ dùng model lớn hơn".

## [Loop] VÒNG #25 — ĐỌC TRACE: "AGGREGATOR GÂY HẠI" PHẦN LỚN LÀ LỖI ĐỊNH DẠNG, KHÔNG PHẢI LỖI PHÁN ĐOÁN
Không kernel nào xong (4 kernel 7B 4-bit vẫn chạy — chúng nặng thật). Chuyển sang ĐỌC 600 trace
đầy đủ từ ft_g15/ft_m15 (đây là lần thứ TƯ đọc output thô, và lại ra phát hiện).

### ĐỐI CHIẾU CƠ BẢN
  MATH  (ft_m15, n=300): Aggregator PHÁ 20 / SỬA 4   -> net -16/300 = -5.3đ (khớp nf_m15 A_gain -6.4)
  GSM8K (ft_g15, n=300): Aggregator PHÁ  0 / SỬA 5   -> net +5/300
  median độ dài output Aggregator: GSM8K 18 ký tự | MATH 142 ký tự

### PHÂN LOẠI 20 CA PHÁ TRÊN MATH (một ca có thể thuộc nhiều nhóm)
  KHÔNG có \boxed trong output          17  (85%)
  TỰ GIẢI LẠI (đáp án khác CẢ HAI ứng viên) 10  (50%)
  output THOÁI HOÁ (<200 ký tự)          8  (40%)
  **CHỌN NHẦM ứng viên (đúng việc của nó)  1  ( 5%)**
  Tỉ lệ có \boxed trên toàn bộ 300 output Aggregator: 82% -> 18% KHÔNG trích được đáp án.

### BA KIỂU HỎNG ĐỌC ĐƯỢC BẰNG MẮT
  1. TỰ GIẢI LẠI: viết 1096 ký tự suy luận riêng, sai, rồi phát ra đáp án của chính nó,
     BỎ QUA cả hai ứng viên. (Cùng kiểu "giải lại thay vì kiểm" đã thấy ở Verifier.)
  2. KHÔNG CHỐT ĐÁP ÁN: bàn xem ứng viên nào trình bày hay hơn ("Candidate 1 offers more
     insight") rồi KHÔNG phát ra \boxed -> bộ trích lấy nhầm số.
  3. THOÁI HOÁ HOÀN TOÀN: phát ra "You are an AI assistant that helps people find information..."
     — tức nhả lại một đoạn giống system prompt.

### KẾT LUẬN PHẢI GHI
ĐO ĐƯỢC: kết quả "-6.4đ Aggregator gây hại trên MATH" (đã kiểm 5/5 fold) PHẦN LỚN LÀ
  LỖI ĐỊNH DẠNG/TRÍCH XUẤT, KHÔNG PHẢI lỗi phán đoán. Chỉ 1/20 ca là thực sự "chọn nhầm".
=> Con số vẫn ĐÚNG như một phép đo hệ thống đầu-cuối, NHƯNG DIỄN GIẢI "LLM tổng hợp phán đoán kém"
   LÀ SAI. Diễn giải đúng: ở bài khó, Aggregator không tuân được định dạng đầu ra, nên hệ thống
   mất điểm — một vấn đề KỸ THUẬT có thể sửa (ép định dạng, fallback về ứng viên khi thiếu \boxed),
   chứ không phải giới hạn về năng lực suy luận.
=> ĐÂY LÀ LẦN THỨ TƯ đọc trace thô lật lại một diễn giải. Tỉ lệ 4/4.

## [Loop] VÒNG #26 — ĐỌC TRACE (lần 5): VERIFIER HỎNG KHÁC HẲN AGGREGATOR, VÀ CƠ CHẾ CỦA +14 LỘ RA
### PHÂN LOẠI CA "PHÁ" CỦA VERIFIER (từ ft_m15 / ft_g15, mỗi bộ n=300)
  MATH : SỬA 18 / PHÁ 14 | 13/14 (93%) là ĐỔI SANG ĐÁP ÁN KHÁC, chỉ 1 ca lỗi trích xuất
  GSM8K: SỬA 32 / PHÁ 22 | 22/22 (100%) là ĐỔI SANG ĐÁP ÁN KHÁC, 0 ca lỗi trích xuất
=> TRÁI NGƯỢC HẲN với Aggregator (85% là lỗi ĐỊNH DẠNG). Ca "phá" của Verifier là
   LỖI PHÁN ĐOÁN THẬT: nó đọc một lời giải ĐÚNG rồi chủ động sửa thành SAI.
   Không thể chữa bằng cách ép định dạng.
=> HAI VAI HỎNG THEO HAI CÁCH KHÁC NHAU:
     Aggregator: lỗi KỸ THUẬT (không phát ra \boxed) -> SỬA ĐƯỢC (H20 đang kiểm)
     Verifier  : lỗi PHÁN ĐOÁN (sửa nhầm lời giải đúng) -> KHÔNG sửa được bằng định dạng

### ĐỘ CHÍNH XÁC CỦA CAN THIỆP — CƠ CHẾ CỦA KẾT QUẢ +14.0
  Verifier          số SỬA  số PHÁ   ĐỘ CHÍNH XÁC KHI CAN THIỆP
  1.5B (MATH ft)      18      14            56%
  1.5B (GSM8K ft)     32      22            59%
  1.5B (MATH as_m)    15       6            71%
  **7B  (MATH as_m)   43       1            98%**
=> VERIFIER 1.5B CHỈ NHỈNH HƠN TUNG ĐỒNG XU về việc KHI NÀO nên can thiệp (56-59%).
   Nó làm việc thật theo cả hai chiều và chỉ hoà vốn nhẹ -> ĐÚNG LÝ DO vì sao giá trị đo được
   của nó nhỏ và khoảng tin cậy chứa 0.
=> VERIFIER 7B không chỉ can thiệp NHIỀU HƠN (44 vs 21) mà còn CHÍNH XÁC HƠN HẲN (98% vs 71%).
   ĐÂY LÀ CƠ CHẾ ĐỊNH LƯỢNG CỦA KẾT QUẢ +14.0 — thứ mà H15 xác nhận nhưng không giải thích được.
=> PHÁT BIỂU GỌN: giá trị của một verifier KHÔNG nằm ở việc nó bắt được bao nhiêu lỗi,
   mà ở ĐỘ CHÍNH XÁC CỦA QUYẾT ĐỊNH CAN THIỆP. Dưới ~60% thì nó gần như vô dụng;
   ở 98% thì nó đáng +14 điểm.

## [Loop] VÒNG #27 — nf_m7 HOÀN TẤT LƯỚI: RƠI HÀNG 2, LÀ 2/4 Ô CHỨ KHÔNG PHẢI 1/4
nf_m7 (MATH 7B, 5 fold x 100): V_gain theo fold +2, +5, +4, +8, +3
  V_gain mean +4.4  range [+2, +8]  5/5 fold DƯƠNG -> XÁC LẬP
  A_gain mean +0.6  range [-1, +3]  chứa 0 -> chưa xác lập
=> Rơi HÀNG 2 của pre-reg #15: "MATH 7B TOÀN DƯƠNG -> thành 2/4 ô, phải sửa phát biểu."
   Khẳng định "chỉ 1/4 ô xác lập" ở vòng #17 ĐÃ SAI. Phải sửa thành 2/4.

### LƯỚI ĐẦY ĐỦ (cả 4 ô cùng chuẩn 5-fold) — VÀ NÓ LÀ ĐƯỜNG CHÉO
  V_gain      GSM8K                      MATH
  1.5B        +4.4 [+1,+8]  5/5  ✅      +1.4 [-1,+4]  ❌
  7B          +1.0 [-3,+5]  ❌           +4.4 [+2,+8]  5/5  ✅

### CƠ CHẾ: XẾP THEO ĐỘ CHÍNH XÁC CỦA SOLVER THÌ MỌI THỨ SÁNG RA
  ô            acc Solver   verifier
  MATH 1.5B      .402       ❌ (model bị NGỢP)
  GSM8K 1.5B     .668       ✅ +4.4
  MATH 7B        .598       ✅ +4.4
  GSM8K 7B       .884       ❌ (đã BÃO HOÀ)
=> ĐO ĐƯỢC: VERIFY CHỈ SINH LỢI Ở GIỮA DẢI ĐỘ KHÓ (~.60-.67 độ chính xác của Solver).
   Quá khó -> verifier không phân biệt nổi đúng/sai (độ chính xác can thiệp chỉ 56%, vòng #26).
   Quá dễ -> không còn gì để sửa.
=> Phát biểu này THAY THẾ "đa tác tử giúp model yếu ở bài dễ" (vòng #17) — cái đó chỉ là
   NGẪU NHIÊN của hai ô tôi đã đo. Phát biểu mới DỰ ĐOÁN ĐƯỢC cả hai ô thành công LẪN hai ô
   thất bại, và khớp trực tiếp với số liệu độ chính xác can thiệp ở vòng #26.
### GHI CHÚ
Đây là lần thứ hai một khẳng định "chỉ 1/4 ô" bị sửa vì đo thêm dữ liệu. Bài học lặp lại:
KHÔNG phát biểu tổng quát khi lưới còn ô trống.

## [Loop] VÒNG #28 — H20 RƠI HÀNG 1: "AGGREGATOR GÂY HẠI" LÀ LỖI PARSING, SỬA BẰNG 1 DÒNG
af_m (MATH 1.5B, 5 fold x 100):
  A_gain base      mean -6.4  range [-9, -4]   5/5 ÂM      (khớp chính xác nf_m15)
  A_gain FALLBACK  mean +1.0  range [ 0, +2]   5/5 >= 0    <-- HẾT HẠI
  A_gain forced    mean -2.4  range [-4, -1]   vẫn âm
  A_gain both      mean +0.6  range [-1, +1]
  boxed_rate: base .768 -> forced .874 (ép định dạng CÓ hiệu lực nhưng KHÔNG đủ)
=> Rơi HÀNG 1 đã khoá trước: XÁC NHẬN. "Aggregator gây hại" là LỖI KỸ THUẬT.
FALLBACK LÀ MIỄN PHÍ: khi output không có \boxed thì LẤY ĐÁP ÁN CỦA VERIFIER —
  KHÔNG gọi thêm model, không tốn token. Chỉ vậy mà -6.4 thành +1.0.
ÉP ĐỊNH DẠNG KÉM HƠN FALLBACK (-2.4 so với +1.0): khớp với các kết quả struct/showwork trước đây —
  ép định dạng làm giảm chất lượng suy luận.

### PHẢI SỬA LẠI MỘT KHẲNG ĐỊNH ĐÃ TỪNG ĐƯỢC COI LÀ CHẮC CHẮN
Trước: "Aggregator GÂY HẠI trên MATH −6.4đ, đã kiểm 5/5 fold" — nằm trong danh sách
  kết quả ĐÃ XÁC NHẬN của RESULTS.md và README.
Nay:  phép ĐO vẫn đúng (với cấu hình chuẩn, aggregator làm mất 6.4đ), NHƯNG NGUYÊN NHÂN là
  KHÔNG TRÍCH ĐƯỢC ĐÁP ÁN, không phải phán đoán kém. Sau khi xử lý định dạng, aggregator
  TRUNG TÍNH (+1.0, khoảng [0,+2]).
PHÁT BIỂU ĐÚNG: "Bộ tổng hợp LLM KHÔNG giúp cũng KHÔNG hại, một khi đã xử lý định dạng đầu ra.
  Tác hại quan sát được trước đây là hiện vật của khâu trích xuất."

### CHU TRÌNH ĐẦY ĐỦ ĐÃ HOẠT ĐỘNG
đọc trace (vòng #25) -> 85% ca phá không có \boxed -> giả thuyết "lỗi định dạng, không phải
phán đoán" -> ĐĂNG KÝ TRƯỚC (#19) -> chạy -> XÁC NHẬN.
Đây là LẦN ĐẦU trong dự án một giả thuyết sinh ra từ việc ĐỌC OUTPUT THÔ sống sót qua
kiểm chứng có đăng ký trước.

## [Loop] VÒNG #29 — bs_g: H18 RƠI HÀNG 2. BẤT ĐỐI XỨNG BỊ THỐNG TRỊ, CÓ THANH SAI SỐ.
bs_g (GSM8K, 5 fold x 100, so ĐẦU-ĐỐI-ĐẦU trên CÙNG bài):
  S15 (1.5B đơn)            .628
  S15_V7 (1.5B + soát 7B)   .810   (+18.2 so với S15 — THẬT, nhưng...)
  **S7 (7B đơn)             .910**
  S7_V7 (7B + soát 7B)      .900
  asym_minus_S7  mean -10.0  range [-13, -6]  5/5 fold ÂM  -> NGOÀI NHIỄU
  S7V7_minus_S7  mean  -1.0  range [ -4, +3]  chứa 0
=> Rơi HÀNG 2 của pre-reg #17: PHẢI HẠ CẤP KHUYẾN NGHỊ Ở ĐẦU README.
   Lợi ích +18.2 so với mốc 1.5B là THẬT nhưng VÔ NGHĨA THỰC TIỄN: chỉ cần dùng 7B là hơn 10 điểm.

### HẠCH TOÁN TOKEN — LẬP LUẬN "RẺ HƠN" CŨNG SỤP
  token do 7B sinh ra: bất đối xứng 105,172  |  7B đơn 120,145
  => chỉ TIẾT KIỆM 12.5% token 7B, để ĐÁNH ĐỔI 10 ĐIỂM chính xác.
  Tính accuracy trên mỗi token 7B: .810/105k vs .910/120k -> chênh nhau <2%, coi như BẰNG NHAU.
  VÀ điều đó CHƯA TÍNH lượt giải 1.5B mà bất đối xứng vẫn phải trả.
  => KỂ CẢ VỀ CHI PHÍ, bất đối xứng KHÔNG THẮNG. Nó thua ở CẢ HAI TRỤC.

### XÁC NHẬN LẠI: SOÁT VÔ NGHĨA KHI SOLVER ĐÃ MẠNH
  S7_V7 - S7 = -1.0, khoảng [-4, +3] chứa 0. Khớp nf_g7 (GSM8K 7B bão hoà .884).
  Ở mức .910 thì không còn gì để sửa — đúng như "dải độ khó" ở vòng #27.

### TRẠNG THÁI KHUYẾN NGHỊ CỦA DỰ ÁN
Vòng #20 tôi đưa "model nhỏ GIẢI + model lớn SOÁT" lên tiêu đề README.
Vòng #23 nghi ngờ (so chéo kernel). Vòng #29 XÁC NHẬN bằng 5 fold đầu-đối-đầu: BỊ THỐNG TRỊ.
=> Khuyến nghị đó ĐÃ CHẾT trên GSM8K. Chờ bs_m để chốt trên MATH.

## [Loop] VÒNG #30 — NỬA CÒN LẠI CỦA KẾT LUẬN: ĐA TÁC TỬ CÓ ÍCH, NHƯNG ÁP LÊN MODEL TỐT NHẤT
Tôi đã phát biểu "kiến trúc đa tác tử bị thống trị" — CHỈ ĐÚNG với phiên bản DÙNG MODEL NHỎ.
Kiểm lại phiên bản áp lên MODEL TỐT NHẤT:
  GSM8K 7B: S7 .910 (BÃO HOÀ) -> S7+V7 .900 = -1.0đ, khoảng [-4,+3] CHỨA 0 -> vô ích
  MATH  7B: PS .598 (GIỮA DẢI) -> PSV .642 = +4.4đ, khoảng [+2,+8] 5/5 DƯƠNG -> CÓ ÍCH
=> ĐA TÁC TỬ THỰC SỰ CÓ GIÁ TRỊ khi áp LÊN TRÊN model mạnh nhất — với điều kiện model đó
   nằm GIỮA DẢI ĐỘ KHÓ của task.

### QUY TẮC QUYẾT ĐỊNH HOÀN CHỈNH (mọi số đều đã kiểm 5 fold)
  1. LUÔN dùng model mạnh nhất có thể. ĐỪNG thay bằng "model nhỏ + verifier" (-10.0đ, 5/5 âm).
  2. CHỈ thêm verifier nếu model đó đạt ~.60-.67 trên task.
     Bão hoà (.91) -> không còn gì để sửa. Quá khó (.40) -> verifier chỉ đúng 56% khi can thiệp.
  3. Bộ tổng hợp LLM TRUNG TÍNH nếu xử lý định dạng (fallback miễn phí: -6.4 -> +1.0).

### GHI CHÚ TỰ PHÊ BÌNH
Ba vòng liền tôi phát biểu kết luận theo hướng CÀNG LÚC CÀNG TIÊU CỰC ("bị thống trị"),
trong khi dữ liệu ĐÃ CÓ SẴN cho thấy nửa tích cực (nf_m7, đo từ vòng #27).
Tôi đã không ghép hai mảnh lại vì đang tập trung vào việc hạ cấp khẳng định cũ.
BÀI HỌC: khi đang sửa sai, vẫn phải rà xem dữ liệu có phần KHẲNG ĐỊNH nào bị bỏ sót không —
thiên lệch theo hướng tiêu cực cũng là thiên lệch.

## [Loop] VÒNG #31 — bs_m: MATH KHÁC HẲN GSM8K, RƠI ĐỒNG THỜI HÀNG 3 VÀ HÀNG 4
bs_m (MATH, 5 fold x 60, đầu-đối-đầu cùng bài):
  S15 (1.5B đơn)          .4233
  S15_V7 (bất đối xứng)   .5633   asym_minus_S7 mean -3.0  range [-8.3, +3.3] CHỨA 0
  S7 (7B đơn)             .5933
  **S7_V7 (7B + soát 7B)  .6700   S7V7_minus_S7 mean +7.7 range [+1.7,+11.7] 5/5 DƯƠNG**
  token 7B: asym 118,969 | S7 151,700 | S7_V7 260,595
  verifier 7B: 43 SỬA / 1 PHÁ (khớp CHÍNH XÁC as_m)

### HÀNG 3 — ĐÁNH ĐỔI CHI PHÍ HỢP LỆ (chỉ trên MATH)
  Bất đối xứng NGANG 7B-đơn về mặt thống kê (khoảng chứa 0) mà dùng ÍT HƠN 21.6% token 7B.
  => Trên MATH đây là LỰA CHỌN CHI PHÍ HỢP LỆ.
  KHÁC HẲN GSM8K (bs_g): ở đó bất đối xứng -10.0đ, 5/5 fold ÂM -> BỊ THỐNG TRỊ.
  CƠ CHẾ: GSM8K solver 7B đã .910 -> hạ xuống 1.5B mất rất nhiều. MATH solver 7B chỉ .593
  -> khoảng cách đủ nhỏ để verifier bù lại. Khớp "dải độ khó" ở vòng #27.

### HÀNG 4 — XÁC NHẬN ĐẦU-ĐỐI-ĐẦU: THÊM VERIFIER LÊN MODEL TỐT NHẤT CÓ ÍCH
  S7_V7 hơn S7 +7.7đ, 5/5 fold DƯƠNG, khoảng [+1.7, +11.7].
  .6700 LÀ CẤU HÌNH TỐT NHẤT ĐO ĐƯỢC TRONG TOÀN DỰ ÁN.
  => Quy tắc 2 (thêm verifier khi model ở giữa dải độ khó) ĐƯỢC XÁC NHẬN bằng so sánh trực tiếp,
     không chỉ suy ra từ lưới.

### QUY TẮC 1 PHẢI ĐƯỢC ĐIỀU CHỈNH
Trước: "ĐỪNG thay model mạnh bằng model yếu + verifier" (dựa trên GSM8K -10.0).
Nay:  đúng khi model mạnh ĐÃ BÃO HOÀ trên task (GSM8K .910 -> mất 10 điểm).
      Khi model mạnh chỉ ở GIỮA DẢI (MATH .593) thì bất đối xứng NGANG BẰNG mà rẻ hơn 21.6%.
=> Phát biểu đúng: giá trị của bất đối xứng phụ thuộc vào việc model MẠNH đang ở đâu trên
   dải độ khó — y hệt quy luật đã tìm ra cho verifier.

## [Loop] VÒNG #32 — HAI CÂU HỎI CỦA NGƯỜI DÙNG, CẢ HAI ĐỀU ĐÚNG THEO SỐ ĐO
### (1) "Verifier có làm đúng việc không? Lẽ ra nó chỉ cần SỬA và ĐI TIẾP từ đường của Solver"
ĐO TỈ LỆ VERIFIER TÁI SỬ DỤNG SỐ CỦA SOLVER (bỏ các số vốn có trong đề):
              toàn bộ   khi ĐỒNG Ý   khi SỬA   khi PHÁ
  GSM8K        .17         .20        **0.00**  **0.00**
  MATH         .83        1.00          .33       .29
=> MỖI KHI CAN THIỆP, VERIFIER VỨT BỎ TOÀN BỘ CHUỖI CỦA SOLVER VÀ GIẢI LẠI TỪ ĐẦU.
   Nó chỉ tái sử dụng khi ĐỒNG Ý (tức là đang đọc lướt và gật đầu).
=> GIẢI THÍCH TRỌN VẸN con số 56%: nếu can thiệp = tự giải lại, thì độ chính xác can thiệp
   phải xấp xỉ ĐỘ CHÍNH XÁC TỰ GIẢI của model (1.5B giải GSM8K ~.63), CHỨ KHÔNG PHẢI độ chính xác
   của việc KIỂM (đáng lẽ dễ hơn nhiều).
=> "VERIFIER KHÔNG PHẢI LÀ BỘ KIỂM TRA TỒI — NÓ LÀ MỘT SOLVER THỨ HAI ĐỘI LỐT BỘ KIỂM TRA."
   Cũng giải thích luôn vì sao verifier 7B giúp nhiều (98%): thực chất ta đang mua một
   SOLVER TỐT HƠN cho lượt thứ hai, không phải một bộ kiểm tra tốt hơn.

### (2) "Planner có làm việc thật không, hay nó GIẢI XONG RỒI? Prompt 'đừng tính đáp án' chỉ ép nó GIẤU"
ĐO ĐƯỢC: Planner sinh 6 SỐ MỚI ở 100% số lượt (0% lượt không tính toán) nhưng chỉ 3.3% có \boxed;
  đáp án ngầm vẫn trích được ở 32-45% số kế hoạch.
=> Ủng hộ mạnh giả thuyết: chỉ dẫn KHÔNG ngăn nó tính, chỉ khiến nó KHÔNG NÓI RA.

### ĐÃ ĐĂNG KÝ TRƯỚC + PHÓNG (pre-reg #20)
  H21a: verifier VÁ LỖI — GIỮ TIỀN TỐ CỦA SOLVER BẰNG CODE (ghép chuỗi), model chỉ viết phần TIẾP.
        Khác lần trước (struct/V_ST) ở chỗ không phụ thuộc model có tuân lệnh hay không.
  H21b: 3 kiểu Planner (giấu / tự do / yêu cầu tính) -> đo acc đáp án NGẦM và acc Solver phía sau.
  Kernel: pa_g15, pa_m15 (5 fold x 80).

## [Loop] VÒNG #33 — HỢP NHẤT CÁC CƠ CHẾ VÀO RESULTS.md (không kernel nào xong)
3 kernel vẫn chạy. rc_m7 đã chạy ~12h — CHẠM TRẦN của Kaggle; nếu vòng sau vẫn RUN hoặc ERROR
thì sẽ phóng lại bản NHẸ HƠN (3 fold x 60 thay vì 5 fold x 100).
Công việc vòng này: gom TOÀN BỘ phát hiện về CƠ CHẾ (vốn nằm rải rác trong IDEAS.md) vào
RESULTS.md thành mục 4c, vì đó mới là phần giải thích được "vì sao", còn các bảng số chỉ nói "cái gì".
Bốn cơ chế đã đưa vào:
  (1) chỉ 2/4 vai thực sự tính toán (Planner, Verifier); Solver và Aggregator là trạm chuyển tiếp
  (2) Planner GIẢI rồi GIẤU đáp án — chỉ dẫn "đừng tính" không ngăn được việc tính
  (3) Verifier GIẢI LẠI chứ không KIỂM (tái sử dụng 0% khi can thiệp) -> độ chính xác can thiệp
      ≈ độ chính xác tự giải, không phải độ chính xác kiểm
  (4) Aggregator hỏng vì ĐỊNH DẠNG (85% không có \boxed), chỉ 5% là chọn nhầm thật
GHI CHÚ: cả bốn đều đến từ ĐỌC OUTPUT THÔ, không từ số tổng hợp. Năm lần đọc trace, năm lần
  lật lại một diễn giải. Đây là lập luận mạnh nhất cho quy tắc "mọi kernel PHẢI lưu trace".

## [Loop] VÒNG #35 — rc_m7 CHẠM TRẦN 12H CỦA KAGGLE; PHÓNG LẠI BẢN NHẸ
rc_m7 đã ở trạng thái RUNNING hơn 13 giờ — vượt trần 12h của Kaggle, coi như CHẾT.
NGUYÊN NHÂN: tôi đặt 5 fold x 100 bài trên 7B 4-bit với 5 lượt sinh mỗi bài
  (~2500 lượt sinh 7B 4-bit) — QUÁ NẶNG cho một session.
ĐÃ PHÓNG LẠI: rc_m7b = 3 fold x 60 bài (180 bài, nhẹ hơn ~2.8 lần) trên tuananhtran37.
  (zhongzhing đã hết quota tuần 30h — tài khoản thứ ba chạm quota trong dự án.)

### BÀI HỌC VỀ QUY MÔ THÍ NGHIỆM
Các kernel 7B 4-bit tốn gấp nhiều lần dự tính. Quy tắc rút ra cho phần còn lại:
  - 1.5B fp16: 5 fold x 100 là AN TOÀN
  - 7B  4-bit: TỐI ĐA 3 fold x 60, và chỉ khi số nhánh <= 3
Ba tài khoản đã cạn quota tuần (truongdinhduc06, tuetrandoanminh, zhongzhing) -> phải
tính ngân sách GPU như một ràng buộc thật, không phải tài nguyên vô hạn.

## [Loop] VÒNG #36 — H21a VÔ HIỆU VÌ LỖI CODE CỦA TÔI; H21b ĐO SAI THỨ CẦN ĐO
### H21a (verifier VÁ LỖI) — rơi HÀNG 4: THÍ NGHIỆM VÔ HIỆU
  V_std .705 | V_patch .5875 | patch_minus_std -11.75 (5/5 fold ÂM)
  reuse_std .157 -> reuse_patch .169  ==> TỈ LỆ TÁI SỬ DỤNG GẦN NHƯ KHÔNG ĐỔI
=> Đúng HÀNG 4 đã khoá trước: "tỉ lệ tái sử dụng KHÔNG tăng -> CAN THIỆP VÔ HIỆU,
   KHÔNG kết luận về H21a."
NGUYÊN NHÂN LÀ LỖI CODE CỦA TÔI, không phải model không nghe lời:
    merged=[f"{sols[i]}\n[correction]\n{v_pat[i]}" ...]   # có tính
    a_pat=[pred(v_pat[i]) ...]                            # NHƯNG KHÔNG DÙNG
  Tôi dựng chuỗi ghép rồi VỨT ĐI, và lấy đáp án CHỈ TỪ phần vá.
  => Thí nghiệm thực chất đo "verifier bị bắt viết ngắn hơn" (494 vs 551 ký tự), chứ KHÔNG
     đo "verifier giữ tiền tố của Solver". Con số -11.75 KHÔNG bác bỏ giả thuyết của người dùng.
=> GIẢ THUYẾT VẪN CHƯA ĐƯỢC KIỂM. Phóng lại bản đã sửa.

### H21b (Planner có giấu đáp án không?) — HÀNG 2 theo chữ nghĩa, NHƯNG CHỈ SỐ KHÔNG ĐỦ SỨC PHÂN GIẢI
  plan_acc: hide .333 | free .485 | ask .463
  solver sau đó: hide .670 | free .703  (chênh +3.25, khoảng [-3.75, +10.0] CHỨA 0, dưới ngưỡng 5đ)
=> Theo chữ nghĩa: rơi HÀNG 2 ("chỉ dẫn THỰC SỰ làm giảm").
=> NHƯNG PHẢI GHI RÕ HẠN CHẾ: chỉ số `plan_acc` chỉ đo ĐÁP ÁN TRÍCH XUẤT ĐƯỢC.
   Tỉ lệ thấp hơn khi "hide" NHẤT QUÁN VỚI CẢ HAI cách giải thích: (a) nó không tính,
   (b) nó có tính nhưng KHÔNG NÓI RA. Chỉ số này KHÔNG phân biệt được hai điều đó.
   => Tôi đã thiết kế một phép đo không trả lời được câu hỏi mình đặt ra.
BẰNG CHỨNG MẠNH HƠN VẪN LÀ CÁI CŨ: Planner sinh 6 SỐ MỚI ở 100% số lượt kể cả khi bị bảo
   "đừng tính" (0% lượt không có số mới). Tức là NÓ VẪN TÍNH. Giả thuyết của người dùng
   vẫn được ủng hộ bởi phép đếm số, không phải bởi phép đo này.
### TỰ PHÊ BÌNH
Hai vòng liên tiếp có lỗi do TÔI: rc_m7 quá nặng (chạm trần 12h), pa_* ghép chuỗi không dùng.
Cả hai đều LÃNG PHÍ GPU và làm chậm câu trả lời cho câu hỏi của người dùng.
