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
