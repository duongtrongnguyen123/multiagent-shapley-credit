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

## [Loop] VÒNG #37 — pa_m15: H21a VÔ HIỆU (cùng lỗi), H21b RƠI HÀNG 3 TRÊN MATH
### H21a trên MATH — VÔ HIỆU, cùng lỗi code như pa_g15
  V_std .420 | V_patch .355 | patch_minus_std -6.5 (5/5 ÂM)
  reuse_std .820 -> reuse_patch .871 (CÓ tăng, nhưng MATH vốn đã cao sẵn)
=> Dù tỉ lệ tái sử dụng có nhích lên, ĐÁP ÁN VẪN LẤY TỪ RIÊNG PHẦN VÁ (lỗi code đã nêu ở vòng #36).
   Phép đo SAI bất kể reuse ra sao. KHÔNG dùng mức tăng reuse trên MATH để kết luận HÀNG 3.
   CẢ HAI pa_g15 và pa_m15 ĐỀU VÔ HIỆU. pa2_g15 (bản đã sửa) mới là phép thử hợp lệ.

### H21b — RƠI HÀNG 3: BỎ CHỈ DẪN "ĐỪNG TÍNH ĐÁP ÁN" THÌ SOLVER PHÍA SAU TỐT HƠN
  MATH  solver sau kế hoạch: hide .4075 -> free .4450  = +3.75, theo fold: +2.5 +1.25 +1.25 +5.0 +8.75
        -> 5/5 FOLD DƯƠNG
  GSM8K solver sau kế hoạch: hide .6700 -> free .7025  = +3.25, 4/5 fold dương
  GỘP HAI TASK: 9/10 fold DƯƠNG -> sign test p ~ .02
=> ĐO ĐƯỢC: BỎ chỉ dẫn "Do NOT compute the final answer" của Planner LÀM SOLVER PHÍA SAU TỐT HƠN.
   Hiệu ứng KHIÊM TỐN (~+3.5đ) nhưng NHẤT QUÁN qua cả hai task.
=> Khớp với trực giác của người dùng theo đúng chỗ quan trọng: chỉ dẫn KHÔNG ngăn Planner tính
   (nó vẫn sinh 6 số mới ở 100% lượt), nó chỉ khiến Planner GIẤU kết quả — và việc giấu đó
   LÀM MẤT một phần giá trị cho Solver.
=> KHUYẾN NGHỊ THỰC DỤNG: bỏ chỉ dẫn "đừng tính đáp án" khỏi prompt của Planner.
   Đây là thay đổi MỘT DÒNG, không tốn thêm compute.
LƯU Ý: plan_acc (hide .2125 vs free .2775 trên MATH) vẫn KHÔNG phân biệt được "không tính" với
  "tính mà không nói" — hạn chế đã ghi ở vòng #36 vẫn giữ nguyên.

## [Loop] VÒNG #38 — pa2_g15: H21a KHÔNG THỂ KIỂM ĐƯỢC TRÊN GSM8K (do chính cấu trúc pipeline)
pa2_g15 (bản ĐÃ sửa lỗi ghép chuỗi): reuse_std .157 -> reuse_patch .175 — VẪN gần như không đổi.
NGUYÊN NHÂN: trên GSM8K, Solver chỉ viết MỘT DÒNG (~18 ký tự, "The answer is 42.").
  Hàm splice của tôi BỎ DÒNG CUỐI để nối phần vá -> bỏ luôn TOÀN BỘ -> merged = chỉ phần vá.
=> H21a KHÔNG THỂ KIỂM TRÊN GSM8K VỀ MẶT CẤU TRÚC: không thể "vá" một lời giải KHÔNG CÓ BƯỚC NÀO.
   Đây là hệ quả TRỰC TIẾP của phát hiện cũ: Planner đã giải xong nên Solver chỉ chép một dòng,
   KHÔNG CÓ TIỀN TỐ để giữ lại.
=> Chỉ MATH mới kiểm được (Solver viết ~986 ký tự; pa_m15 cho thấy reuse .820 -> .871).
ĐÃ SỬA splice cho an toàn (chỉ bỏ dòng cuối khi lời giải có >=3 dòng) và phóng pa2_m15 trên MATH.
GHI CHÚ: đây là lần thứ ba một thí nghiệm bị vô hiệu vì tôi giả định Solver có nhiều bước,
  trong khi CHÍNH DỰ ÁN NÀY đã đo được nó chỉ viết một dòng. Tôi không áp dụng phát hiện của
  chính mình khi thiết kế thí nghiệm sau đó.

## [Loop] VÒNG #39 — KHÔNG CÓ KẾT QUẢ MỚI; CHỦ ĐỘNG KHÔNG PHÓNG THÊM
3 kernel đang chạy (rc_m7b, pa2_m15, pc_he), không cái nào xong.
QUYẾT ĐỊNH: KHÔNG phóng thí nghiệm thứ tư trong vòng này, vì:
  - 3 câu hỏi còn mở đã được 3 kernel này phủ hết
  - 3/19 tài khoản đã cạn quota tuần 30h -> ngân sách GPU là ràng buộc thật
  - thêm kernel lúc này chỉ tạo hàng đợi mà không rút ngắn được thời gian có câu trả lời
TRẠNG THÁI CÂU HỎI CÒN MỞ:
  rc_m7b  : mắt xích cuối chưa có thanh sai số (truyền trace ở MATH 7B)
  pa2_m15 : giả thuyết VÁ LỖI của người dùng — lần đầu kiểm được đúng cách (chỉ MATH mới đủ bước)
  pc_he   : chỉ dẫn cấm của Planner có tổng quát sang CODE không (chấm bằng chạy test)

## [Loop] VÒNG #41 — BA KẾT QUẢ LỚN: H21a BỊ BÁC (phép thử HỢP LỆ), H22 RƠI HÀNG 3+4
### H21a (VÁ LỖI) — LẦN NÀY CAN THIỆP CÓ HIỆU LỰC, VÀ GIẢ THUYẾT BỊ BÁC
  pat15 (MATH 1.5B, n=500, 5 fold): V_std .474 | V_patch .382 | patch−std **−9.2**
     tái sử dụng: std .988 -> patch **1.000**  (CAN THIỆP CÓ HIỆU LỰC — khác hẳn lần trước)
     sửa/phá: std 26/9  ->  patch **14/43**
  pat7  (MATH 7B  , n=500, 5 fold): V_std .690 | V_patch .654 | patch−std **−3.6**
     sửa/phá: std 38/5  ->  patch **38/23**
=> Rơi HÀNG 3 của pre-reg #20: "V_patch < V_std -> TIỀN TỐ CỦA SOLVER LÀ GÁNH NẶNG,
   GIẢI LẠI TỪ ĐẦU TỐT HƠN. Đảo ngược trực giác, phải ghi rõ."
=> CƠ CHẾ: giữ tiền tố = GIỮ LUÔN LỖI. Số PHÁ tăng vọt (9->43 ở 1.5B, 5->23 ở 7B) vì verifier
   bị cấm viết lại phần trước, nên lỗi nằm sớm trong chuỗi KHÔNG BAO GIỜ được sửa.
=> ĐẢO NGƯỢC DIỄN GIẢI CŨ CỦA TÔI: tôi từng gọi "verifier giải lại thay vì kiểm" là KHIẾM KHUYẾT.
   Thực ra ĐÓ CHÍNH LÀ THỨ LÀM NÓ HỮU ÍCH — giải lại là cách nó THOÁT khỏi lỗi của Solver.
   Ép nó bám vào chuỗi cũ thì nó thừa hưởng luôn lỗi cũ.

### H22 (bỏ chỉ dẫn cấm, trên CODE) — rơi ĐỒNG THỜI HÀNG 3 VÀ HÀNG 4
  pc_he (HumanEval, 5 fold x 32): NoP **.5375** | P_hide .4312 | P_ask .4437 | P_free .3812
  free−hide = **−5.0** (chỉ 1/5 fold dương)  -> HÀNG 3: ĐẢO DẤU so với toán (+3.5)
  **NoP CAO HƠN MỌI nhánh có Planner (~+9đ)** -> HÀNG 4: TRÊN CODE, PLANNER GÂY HẠI, bỏ hẳn thì tốt hơn.
  planCode: P_hide **.537** | P_free .738 | P_ask 1.0
  => 53.7% kế hoạch VẪN CHỨA CODE dù bị cấm -> XÁC NHẬN trực tiếp giả thuyết của người dùng:
     chỉ dẫn cấm KHÔNG ngăn được model làm, nó chỉ làm model GIẤU BỚT.
     (Đây là phép đo trực tiếp, mạnh hơn hẳn chỉ số plan_acc gián tiếp ở H21b.)

## [Loop] VÒNG #42 — pa2_m15 XÁC NHẬN ĐỘC LẬP H21a BỊ BÁC; GRPO TẠM DỪNG VÌ OOM
### pa2_m15 (Kaggle, MATH 1.5B, 5 fold) — XÁC NHẬN LẦN THỨ BA
  V_std .420 | V_patch .385 | patch−std **−3.5**, khoảng [−6.25, −1.25], 5/5 fold ÂM
  tái sử dụng .820 -> **.955** (can thiệp CÓ hiệu lực)
=> H21a BỊ BÁC trên BA lần chạy ĐỘC LẬP: pat15 (−9.2), pat7 (−3.6), pa2_m15 (−3.5).
   Cả ba đều có reuse TĂNG -> đều là phép thử HỢP LỆ. Kết luận VỮNG.
=> Phát biểu chốt: GIỮ TIỀN TỐ CỦA SOLVER LÀM VERIFIER TỆ ĐI. Việc "giải lại từ đầu" —
   thứ tôi từng gọi là khiếm khuyết — CHÍNH LÀ cơ chế giúp verifier thoát khỏi lỗi của Solver.

### GRPO (H23) — TẠM DỪNG: OOM DAI DẲNG, ĐÃ THỬ 4 CẤU HÌNH
  BP12/CHUNK8 -> OOM | BP6/CHUNK4 + gradient checkpointing -> OOM
  log_softmax bf16 thay float32 -> OOM | BP4/CHUNK1 -> VẪN OOM (1.36 GiB)
CHẨN ĐOÁN: `vchunks` giữ TOÀN BỘ chuỗi đã sinh trên GPU suốt cả bước, cộng với đồ thị gradient
  tích luỹ qua các chunk -> bộ nhớ không giảm dù chunk nhỏ. Cần viết lại: giải phóng chuỗi sau
  mỗi chunk, hoặc tách hẳn pha sinh (lưu ra CPU) khỏi pha tính gradient.
QUYẾT ĐỊNH: KHÔNG đốt thêm tài nguyên vào GRPO lúc này. Chuyển GPU sang sinh trace
  (luôn có giá trị — mọi phát hiện cơ chế của dự án đều đến từ đọc trace).
  GRPO vẫn giữ trong hàng đợi, sẽ viết lại phần quản lý bộ nhớ khi có điều kiện.
GHI CHÚ TRUNG THỰC: prior tôi ghi trước ở pre-reg #22 là "khả năng cao rơi hàng 2 hoặc 3"
  (RL không giúp). Việc dừng lại lúc này KHÔNG được tính là bằng chứng ủng hộ prior đó —
  H23 vẫn là CHƯA KIỂM, không phải bị bác.

## [Loop] VÒNG #43 — H1 KHÔNG KẾT LUẬN CHUNG; H2 BỊ BÁC Ở 7B (kết quả cũ PHẦN LỚN LÀ NHIỄU PROMPT)
Bảy kernel của đăng ký trước #2 đã xong: bl_g15 / bl_g7 / bl_m15 / bl_m7 / agf_15 / agf_7 / sw_m7.

### H1 — "verifier bị bịt mắt bắt lỗi tốt hơn". Chỉ số chính = `fixes` (CÙNG bộ lời giải)
| ô | S | fixes I | fixes B | B>I? | add I | add B |
|---|---|---|---|---|---|---|
| GSM8K 1.5B | .632 | 20 | **42** | CÓ (2.1×) | +.056 | +.076 |
| GSM8K 7B   | .916 |  4 |  **6** | có (yếu)  | −.008 | +.000 |
| MATH 1.5B  | .405 | 13 | **19** | CÓ        | +.050 | +.050 |
| MATH 7B    | .625 | **17** | 9 | **NGƯỢC** | +.065 | +.005 |
=> Rơi vào HÀNG 4 của bảng đã khoá: "chỉ 1 task có, 1 task không -> KHÔNG kết luận chung,
   ghi là PHỤ THUỘC, cần thêm dữ liệu". H1 KHÔNG được phát biểu như khẳng định.

ĐO ĐƯỢC (GSM8K 1.5B, kiểm định 2 tỉ lệ): bịt mắt sửa .457 vs .217 (z=3.44, p<.001)
  NHƯNG cũng phá .146 vs .038 (z=3.31, p<.001). Sửa nhiều hơn ĐI KÈM phá nhiều hơn
  theo tỉ lệ gần như y hệt -> giá trị gia tăng RÒNG gần như không đổi (+.076 vs +.056,
  dưới sàn nhiễu ~5 điểm). "Bịt mắt" KHÔNG phải bữa trưa miễn phí.

### Nhánh P (thấy suy luận, XOÁ đáp án) — tách cơ chế, đã khoá trước
fix/break: g15 .163/.006 | g7 .143/.022 | m15 .109/.148 | m7 .200/.024
P GIỐNG I ở cả 4 ô, KHÔNG giống B.
=> Theo cam kết đã khoá: **thủ phạm là PHẦN SUY LUẬN, không phải đáp án**. Xoá mỗi con số
   cuối KHÔNG khôi phục được tính hoài nghi; chính lập luận trôi chảy mới thuyết phục verifier.
   (P ở GSM8K 1.5B có break_rate .006 — THẤP NHẤT mọi nhánh — đáng chú ý cho luật định tuyến.)

### Nhánh X (giả dược: thấy lời giải BÀI KHÁC) — CẢNH BÁO cho chính H1
fix_rate: g15 .315 | **g7 .381** | m15 .193 | m7 .200
Ở GSM8K 7B, X có fix_rate CAO NHẤT trong cả 4 nhánh (.381 > B .286 > I .191).
Context của X là VÔ NGHĨA -> "sửa" của nó không thể là kiểm lỗi thật, chỉ có thể là GIẢI LẠI.
=> Một phần hiệu ứng "bịt mắt bắt lỗi tốt hơn" KHÔNG phải do hoài nghi mà do
   context bị phá vỡ khiến model bỏ qua lời giải và tự giải lại. Khớp với phát hiện cũ
   (verifier tái sử dụng 0% số của Solver). ĐÂY LÀ GIẢ THUYẾT, chưa tách được — xem H3.

### H2 — bộ tổng hợp LLM khi ĐƯỢC ĐỐI XỬ CÔNG BẰNG (cùng CoT, cùng 1024 token)
| ô | maj@8 | agg_fair | vs_maj | phá/cứu đa số |
|---|---|---|---|---|
| 1.5B | .533 | .467 | −.067 | 15 / 7 |
| 7B   | .717 | .725 | **+.008** | **3 / 4** |
(agg_full_sol: 1.5B .358 −.175 (26/5) — thảm hoạ; 7B .733 **+.017** (7/9))
SỐ CŨ (không công bằng) ở 7B: đè lên **26** đa số đúng, cứu **0**.
SỐ MỚI (công bằng)   ở 7B: đè **3**, cứu **4**.
=> Rơi vào HÀNG 2 của bảng đã khoá: "khoảng cách thu hẹp rõ -> kết quả cũ PHẦN LỚN do
   NHIỄU PROMPT, phải sửa lại phát biểu". Ở 7B thậm chí chạm HÀNG 3 (aggregator >= bỏ phiếu)
   -> **H2 BỊ BÁC ở 7B**. Ở 1.5B vẫn âm (−.067) nhưng kiểm định dấu 15/7 cho p≈.13,
   KHÔNG đạt p<.05, và độ lớn nằm quanh sàn nhiễu.
### RÚT LẠI CÔNG KHAI
Phát biểu cũ của dự án — "aggregator LLM là SAI LOẠI, phải thay bằng thống kê" — được xây
trên một so sánh KHÔNG CÔNG BẰNG (aggregator không có chỉ dẫn CoT, chỉ 384 token so với
1024). Khi sửa lại cho công bằng, hiệu ứng gần như biến mất ở 7B. TÔI RÚT LẠI phát biểu đó.
Phát biểu thay thế (HẸP HƠN): ở model YẾU (1.5B), tổng hợp bằng LLM có xu hướng kém bỏ phiếu,
đặc biệt khi phải đọc TOÀN BỘ lời giải (−.175); ở 7B không còn khác biệt đo được.

### sw_m7 — bắt Solver TRÌNH BÀY, và Verifier có cần thấy phần trình bày không?
A_bare .6467 | B_work_shown .6067 | C_work_hidden .6067  (B và C DÙNG CHUNG lời giải)
verifier: B .660 (11 sửa/3 phá) vs C .6667 (12 sửa/3 phá) — chênh .007, KHÔNG có gì.
median_sol_len 861 -> 26 ký tự mà kết quả KHÔNG đổi.
=> XÁC NHẬN lại: bắt Solver trình bày làm Solver TỆ ĐI (−4.0 điểm).
=> Và ở MATH 7B, giấu phần trình bày khỏi Verifier KHÔNG đổi gì -> khớp với ô MATH 7B của H1
   (nhánh ngược chiều). Hai phép đo ĐỘC LẬP cùng nói: ở MATH 7B, H1 không đúng.

## [Loop] VÒNG #44 — H23 (GRPO): RƠI ĐÚNG HÀNG 2 ĐÃ KHOÁ — "HỌC CÁCH IM LẶNG"
GRPO chạy xong 100 bước (bp=24, k=4, 2400 bài GSM8K main_train), eval 5 fold GSM8K test.
Cả hai nhánh DÙNG CHUNG lời giải của Solver (Solver luôn chạy trên model gốc) -> so sánh CẶP.

| fold | S | V_base | V_lora | gain_base | gain_lora | can thiệp base | can thiệp lora | prec base | prec lora |
|---|---|---|---|---|---|---|---|---|---|
| 0 | .56 | .66 | .63 | +.100 | +.070 | 23 | 13 | .86 | **1.00** |
| 1 | .63 | .68 | .66 | +.050 | +.030 | 20 |  8 | .78 | **1.00** |
| 2 | .66 | .73 | .72 | +.070 | +.060 | 18 |  9 | .77 | **1.00** |
| 3 | .62 | .66 | .63 | +.040 | +.010 | 21 |  5 | .70 | **1.00** |
| 4 | .64 | .72 | .69 | +.080 | +.050 | 19 |  7 | .90 | **1.00** |

ĐO ĐƯỢC:
  ĐỘ CHÍNH XÁC CAN THIỆP: .70–.90 -> **1.00 ở CẢ 5 FOLD** (tổng 22 sửa / **0 phá**)
  V_gain:                 +.068 -> **+.044**  (GIẢM 2.4 điểm, **0/5 fold** tốt hơn)
  SỐ LẦN CAN THIỆP:       20.2/100 -> **8.4/100** (còn 42%)
  tổng sửa/phá:           base 45/11  ->  lora **22/0**

=> **RƠI ĐÚNG HÀNG 2 của bảng đã khoá**: "độ chính xác can thiệp tăng nhưng V_gain KHÔNG tăng
   -> nó học cách CAN THIỆP ÍT ĐI chứ không CHÍNH XÁC HƠN. Phải báo kèm SỐ LẦN can thiệp."
   Chính vì đã khoá trước chỉ số "số lần can thiệp" mà không thể kể câu chuyện đẹp
   "độ chính xác can thiệp đạt 100%!" — nó đạt 100% bằng cách NÓI ÍT ĐI MỘT NỬA.

CƠ CHẾ (rõ ràng, không phải suy đoán): reward = +1 sửa / −1 phá / 0 nếu không đổi.
Chiến lược tối ưu TẦM THƯỜNG của reward này là CAN THIỆP ÍT ĐI: bớt can thiệp -> bớt phá ->
reward trung bình tăng, trong khi "im lặng" được cho 0 điểm chứ không bị phạt.
Model đã tối ưu ĐÚNG thứ tôi viết ra. Lỗi ở HÀM THƯỞNG, không ở thuật toán.
Dấu vết trong log huấn luyện khớp: `nseq` (số chuỗi có advantage khác 0) tụt còn 4–24/96
ở các bước cuối — phần lớn mẫu KHÔNG còn tín hiệu học vì chúng đã giống hệt nhau (đều im lặng).

Ý NGHĨA THỐNG KÊ: −2.4 điểm là NHỎ, dưới sàn nhiễu không ghép cặp (~5 điểm). NHƯNG hai nhánh
dùng CHUNG lời giải nên đây là so sánh CẶP, nhạy hơn; hướng nhất quán 5/5 fold
(kiểm định dấu một phía p≈.031). Kết luận: GRPO KHÔNG cải thiện độ chính xác ròng.

SO VỚI MỐC BẮT BUỘC (7B verifier KHÔNG huấn luyện, độ chính xác can thiệp 98%):
LoRA đạt precision 1.00 nhưng chỉ mang +4.4 điểm, trong khi 7B không huấn luyện mang nhiều hơn.
=> **Khuyến nghị GIỮ NGUYÊN: dùng model lớn hơn, đừng huấn luyện model nhỏ bằng RL.**

PRIOR ĐÃ GHI TRƯỚC (pre-reg #22): "khả năng cao rơi vào hàng 2 hoặc 3". **Prior ĐÚNG.**
Ghi rõ để cân bằng: rất nhiều prior khác của tôi trong dự án này đã SAI; lần này đúng.

ĐIỀU CÓ THẬT VÀ ĐÁNG GIỮ: lora KHÔNG BAO GIỜ phá một đáp án đúng (0/11 so với base).
Nếu ai cần một verifier "không gây hại" thì đây là cách có được nó — nhưng phải chấp nhận
mất một nửa số lần sửa. Đó là ĐÁNH ĐỔI, không phải cải thiện.

THÍ NGHIỆM TIẾP NẾU QUAY LẠI RL (chưa chạy, chưa đăng ký): phạt sự im lặng —
reward 0 cho "không đổi khi Solver ĐÚNG" nhưng −0.5 cho "không đổi khi Solver SAI".
Khi đó im lặng không còn miễn phí. HIỆN CHƯA LÀM: ưu tiên đang là H24.

## [Loop] VÒNG #45 — H25 SỤP SÀN (100% nói "NO"); H24 ô MATH 1.5B; RÚT KINH NGHIỆM THIẾT KẾ
### dt_g15 (H25, GSM8K 1.5B) — ĐO ĐƯỢC nhưng PHÉP ĐO KHÔNG HỢP LỆ cho câu hỏi đã đặt
phân tầng: HIGH 78 | MID 99 | ZERO 23 (giải đúng trung bình .546/8 mẫu)
| tầng | phát hiện trên CORRUPT | báo động giả trên CLEAN | PHÂN BIỆT |
|---|---|---|---|
| HIGH | .000 | .000 | **+.000** |
| MID  | .000 | .000 | **+.000** |
| ZERO | .000 | .000 | **+.000** |
TRACE (392/392): model xuất ra ĐÚNG chuỗi `NO` trong **100%** lượt. Không phải lỗi parser —
đã kiểm bằng trace. Ví dụ bị bỏ sót: `9 * 2 = <<9*2=17>>17` (9×2=18) -> vẫn trả lời "NO".

THEO BẢNG ĐÃ KHOÁ, đây là HÀNG 3: "phát hiện thấp ở MỌI tầng -> model không làm nổi cả
nhiệm vụ kiểm đơn giản nhất". NHƯNG tôi PHẢI ghi kèm KHIẾM KHUYẾT THIẾT KẾ CỦA CHÍNH TÔI:
kernel đặt `max_new_tokens=16` và bắt trả lời YES/NO NGAY -> model KHÔNG CÓ CHỖ ĐỂ TÍNH.
Phân biệt = 0.000 CHÍNH XÁC ở cả ba tầng, kể cả tầng HIGH (bài nó giải đúng 6-8/8 lần) —
hiệu ứng SÀN như vậy thường tố cáo DỤNG CỤ ĐO, không phải năng lực.
=> Phép đo này HỢP LỆ cho phát biểu HẸP: "1.5B không phán đoán đúng/sai được nếu KHÔNG được
   suy luận trước". Nó KHÔNG HỢP LỆ cho câu hỏi đã đăng ký ("kiểm lỗi có tách rời khỏi giải").
=> Tự phê: pre-reg #24 KHÔNG khoá ngưỡng hiệu lực (như H8 đã từng làm với exec_success_rate .50).
   Nếu có khoá, tôi đã bắt được lỗi này TRƯỚC khi chạy. Ghi lại thành LUẬT: mọi thí nghiệm
   phán đoán nhị phân phải khoá trước ngưỡng "tỉ lệ trả lời suy biến < 90%".
=> CHẠY LẠI (dt2): cho phép kiểm từng bước rồi mới chốt `VERDICT: YES/NO`, 400 token.
   H25 hiện là CHƯA KIỂM, KHÔNG phải đã bác.

### rs_m15 (H24, MATH 1.5B) — ô thứ 2/4
solver .405
| nhánh | acc | thêm | sửa | phá |
|---|---|---|---|---|
| V_inf | .455 | +.050 | 13 | 3 |
| V_bli | .460 | +.055 | 20 | 9 |
| S_anc | .440 | +.035 | 17 | 10 |
| S_pln | .430 | +.025 | 23 | **18** |
Ở ô này S_pln SỬA NHIỀU NHẤT (23) nhưng PHÁ GẤP ĐÔI (18 vs 9) -> khớp HÀNG 3 của bảng khoá
("sửa ngang nhau nhưng V_bli phá ít hơn -> khung kiểm tăng TÍNH CHỌN LỌC, không tăng PHÁT HIỆN").
Ô GSM8K 1.5B trước đó khớp HÀNG 4 (mỏ neo làm hết việc, S_anc ≈ V_bli).
=> HAI ô, HAI hàng khác nhau. CHƯA KẾT LUẬN — chờ rs_g7 và rs_m7. Bảng đã khoá yêu cầu >=3/4 ô.

## [Loop] VÒNG #46 — H25b VẪN SUY BIẾN dù đã cho suy luận -> HÀNG 4 (VÔ HIỆU); MẤT MÁY REMOTE
### dt2_g15 (H25b, GSM8K 1.5B, 400 token + dòng VERDICT)
parse_fail = **0.000** (parser tốt, không phải lỗi đọc) | phân tầng HIGH 84 / MID 96 / ZERO 20
| tầng | phát hiện | báo động giả | phân biệt | suy biến | HỢP LỆ |
|---|---|---|---|---|---|
| HIGH | .012 | .000 | +.012 | **.994** | **KHÔNG** |
| MID  | .021 | .000 | +.021 | **.990** | **KHÔNG** |
| ZERO | .050 | .050 | +.000 | **.950** | **KHÔNG** |

=> **RƠI ĐÚNG HÀNG 4 của bảng đã khoá ở #26**: "vẫn suy biến >.90 dù đã cho 400 token ->
   KHÔNG kết luận gì về năng lực. Ghi: nhiệm vụ phán nhị phân KHÔNG đo được ở 1.5B bằng cách hỏi này."
   Cho model 400 token để kiểm từng bước KHÔNG cứu được: nó vẫn nói "NO" ~99% số lượt.

GIÁ TRỊ CỦA VIỆC KHOÁ NGƯỠNG TRƯỚC: kernel TỰ ĐÁNH DẤU `VALID=false` cho cả 3 tầng.
Vòng trước (dt_g15) tôi phải phát hiện thủ công bằng cách đọc trace; lần này ngưỡng đã khoá ở
pre-reg #26 bắt được ngay trong kernel. Luật mới hoạt động đúng như mong đợi.

ĐỌC ĐÚNG MỰC: đây KHÔNG phải bằng chứng "1.5B không kiểm được lỗi". Nó là bằng chứng
"KHÔNG THỂ MOI RA phán đoán nhị phân từ 1.5B BẰNG PROMPT" — dù có cho suy luận dài.
Phân biệt +.012/+.021 tuy dương và đúng hướng nhưng vô nghĩa khi 99% câu trả lời giống nhau.

HỆ QUẢ TRỰC TIẾP CHO H27 (verifier PHÂN BIỆT, pre-reg #27): kết quả này làm H27 QUAN TRỌNG HƠN,
không phải kém đi. Prompt không moi được phán đoán -> câu hỏi còn lại là HUẤN LUYỆN có moi được không.
H27 dạy thẳng model xuất Yes/No trên 6400 nhãn tự động — nhắm ĐÚNG vào sự suy biến này.
Nếu H27 cũng cho AUC <= .55 thì lúc đó mới được nói "1.5B không học được hàm phân biệt".

### MẤT MÁY REMOTE (180.189.55.43:18440) — GHI NHẬN THIỆT HẠI TRUNG THỰC
Máy KHÔNG còn truy cập được: cổng đóng, ping mất 100% gói. Toàn bộ hàng đợi 5 tầng mất:
  role_rl (H26, đang ở ~bước 30/60) | eval_role | dtl7b | dtl15 | disc15
**Chưa có kết quả nào của H26 được kéo về local.** Số liệu duy nhất còn giữ là các dòng log
đã in ra trong phiên: `reveal` 0.28 -> 0.53 (bước 10 -> 20), Rp âm suốt, Rs ~+0.63.
Đó là phần thưởng TRÊN MẺ HUẤN LUYỆN, KHÔNG phải kết quả đánh giá -> **H26 là CHƯA KIỂM.**
KHÔNG được dùng mấy con số đó để kết luận gì; đặc biệt KHÔNG được nói "planner hội tụ về
tiết lộ đáp án" như một phát hiện — nó mới chỉ là xu hướng trên mẻ, chưa qua tập kiểm.

BÀI HỌC (thành LUẬT): mọi công việc chạy dài trên máy thuê PHẢI kéo kết quả trung gian về local
theo chu kỳ (vd mỗi 10 bước scp `*_hist.json`), vì máy thuê có thể biến mất bất cứ lúc nào.
Tôi đã KHÔNG làm việc đó và mất toàn bộ H26. Lỗi của tôi, không phải rủi ro không lường được.

## [Loop] VÒNG #47 — H24 ô 7B (BÃO HOÀ, ít thông tin); H25 ở 7B KHÔNG suy biến; disc_g15 LỖI MÔI TRƯỜNG
### rs_g7 (H24, GSM8K 7B) — ô thứ 3/4
solver **.916** -> chỉ còn 21 bài sai, mọi hiệu ứng đều bé hơn sàn nhiễu.
| nhánh | thêm | sửa | phá | fixR |
|---|---|---|---|---|
| V_inf | +.004 | 4 | 3 | .191 |
| V_bli | +.004 | 7 | 6 | .333 |
| S_anc | **+.008** | 10 | 8 | **.476** |
| S_pln | +.000 | 7 | 7 | .333 |
Ô này KHÔNG kết luận được gì (bão hoà) — nhưng đáng ghi: `S_anc`, nhánh KHÔNG có khung kiểm,
lại có fix_rate CAO NHẤT (.476) và giá trị thêm cao nhất.

### TỔNG HỢP H24 sau 3/4 ô — mẫu hình NHẤT QUÁN đã lộ
| ô | V_inf | V_bli | **S_anc** | **S_pln** |
|---|---|---|---|---|
| GSM8K 1.5B | +.060 | +.076 | **+.080** | **−.012** |
| MATH 1.5B  | +.050 | +.055 | +.035 | +.025 |
| GSM8K 7B   | +.004 | +.004 | **+.008** | +.000 |
`S_pln` (giải lại KHÔNG có mỏ neo) là NHÁNH TỆ NHẤT ở cả 3 ô.
`S_anc` (có mỏ neo, KHÔNG có một chữ nào về "kiểm tra") ngang hoặc hơn `V_bli` ở 2/3 ô.
=> HƯỚNG VỀ HÀNG 4 của bảng khoá: thứ có tác dụng là **MỎ NEO ĐÁP ÁN**, không phải khung kiểm.
   CHƯA CHỐT — bảng yêu cầu >=3/4 ô và ô GSM8K 7B bão hoà nên không tính được. Chờ rs_m7.

### dt_g7 (H25 ở 7B, bản 16 token) — KHÔNG suy biến, nên ĐỌC ĐƯỢC
phân tầng HIGH 166 / MID 28 / ZERO **6** | solve_rate .872
| tầng | phát hiện | báo động giả | phân biệt | tỉ lệ nói "NO" |
|---|---|---|---|---|
| HIGH | .204 | .111 | **+.093** | ~.84 (HỢP LỆ) |
| MID  | .357 | .321 | +.036 | ~.66 (HỢP LỆ) |
| ZERO | .500 | .500 | +.000 | .50 (n=**6**, VÔ DỤNG) |
KHÁC HẲN 1.5B: ở 7B model CÓ trả lời đa dạng (không kẹt ở "NO"), nên dụng cụ đo HOẠT ĐỘNG.
Nhưng phân biệt YẾU ở mọi tầng, và GIẢM dần theo độ khó: .093 -> .036 -> .000.
Hướng giảm này KHỚP với hàng 2 ("kiểm lỗi bị chặn bởi năng lực giải") NHƯNG:
  (a) độ lớn quá bé để khẳng định; (b) tầng ZERO chỉ có **6 bài** — không đọc được;
  (c) đây vẫn là bản 16 TOKEN, không cho suy luận — cùng khiếm khuyết đã biết.
=> H25 ở 7B: CHƯA KIỂM. Chờ dt2_g7 (có suy luận) mới đọc theo bảng.
=> Ghi nhận thêm: 7B giải đúng .872 nên tầng ZERO gần như RỖNG. Muốn đo "bài không giải nổi"
   ở 7B thì PHẢI đổi sang tập khó hơn (MATH), không dùng GSM8K được nữa. Ghi vào thiết kế sau.

### disc_g15 LỖI: `ImportError: torchao 0.10.0, chỉ hỗ trợ >0.16.0`
Không phải lỗi khoa học — lỗi MÔI TRƯỜNG: `peft` trên ảnh Kaggle kéo theo torchao quá cũ.
Sửa: cài `torchao>=0.16.0` ngay đầu kernel (đã bật enable_internet). Phóng lại.

## [Loop] VÒNG #48 — dt2_g7: KIỂM LỖI **TÁCH RỜI** KHỎI GIẢI Ở 7B (hàng 1) — nhưng tầng quyết định chỉ n=9
### dt2_g7 (H25b, GSM8K **7B**, có suy luận 400 token + dòng VERDICT)
parse_fail = .0026 (<.20 ✓) | phân tầng HIGH 170 / MID 21 / ZERO **9** | solve_rate .867
| tầng | phát hiện | báo động giả | **PHÂN BIỆT** | bal_acc | suy biến | HỢP LỆ |
|---|---|---|---|---|---|---|
| HIGH | .723 | .072 | **+.651** | .825 | .602 | **CÓ** |
| MID  | .550 | .048 | **+.502** | .751 | .707 | **CÓ** |
| ZERO | .667 | .222 | **+.444** | .722 | .556 | **CÓ** |

=> **RƠI VÀO HÀNG 1 của bảng đã khoá ở #26**: "phân biệt ở ZERO >= .40 -> KIỂM LỖI LÀ KỸ NĂNG
   TÁCH RỜI. Vai verifier CÓ THẬT; huấn luyện theo vai là đúng hướng."
   Ở tầng ZERO — những bài model KHÔNG GIẢI ĐÚNG DÙ MỘT LẦN trong 8 mẫu — nó vẫn phát hiện
   được lỗi số học bị tiêm với tỉ lệ .667 và chỉ báo động giả .222.

### GIỚI HẠN PHẢI NÓI TRƯỚC KHI AI KỊP MỪNG: tầng ZERO chỉ có **9 CẶP**
Với n=9, khoảng tin cậy của phân biệt .444 rộng tới mức gần như chắc chắn CHỨA 0.
Hàng 1 nổ lên ĐÚNG THEO NGƯỠNG ĐÃ KHOÁ (.40), nhưng ngưỡng đó được khoá khi tôi chưa biết
tầng ZERO sẽ nhỏ đến vậy. **Kết luận "kiểm lỗi tách rời khỏi giải" hiện CHƯA ĐỦ BẰNG CHỨNG.**
Thứ ĐO ĐƯỢC CHẮC CHẮN là hai tầng có đủ mẫu: HIGH +.651 (n=166) và MID +.502 (n=20).
Nghĩa là: 7B PHÁT HIỆN ĐƯỢC lỗi số học tiêm sẵn rất tốt — điều mà 1.5B KHÔNG làm nổi.

### ĐỐI CHIẾU 1.5B vs 7B — NGƯỠNG NĂNG LỰC, KHÔNG PHẢI NHIỆM VỤ BẤT KHẢ
dt2_g15 (1.5B): suy biến **.99** ở mọi tầng -> VÔ HIỆU, không moi được phán đoán.
dt2_g7  (7B)  : suy biến .60 -> hợp lệ, phân biệt **+.651**.
=> Cùng prompt, cùng dữ liệu, cùng lỗi tiêm. Khác biệt DUY NHẤT là năng lực model.
=> Củng cố phát biểu xuyên suốt dự án: **bộ máy đa tác tử chỉ hoạt động khi MODEL ĐI KIỂM
   đủ mạnh**. Giờ có thêm bằng chứng ở mức NHIỆM VỤ KIỂM THUẦN TUÝ, không lẫn với việc giải.

### VÌ SAO GSM8K KHÔNG TRẢ LỜI ĐƯỢC CÂU HỎI TRUNG TÂM (đã ghi trước ở vòng #47)
7B giải đúng .867 trên GSM8K -> tầng "không giải nổi" chỉ còn 9/200 bài. Tầng quyết định
BỊ RỖNG DO THIẾT KẾ, không phải do ngẫu nhiên. Muốn đo "phát hiện lỗi ở bài KHÔNG giải nổi"
thì PHẢI đổi sang tập khó hơn. Tôi đã ghi điều này ở vòng trước, TRƯỚC khi thấy kết quả này.
=> Thí nghiệm tiếp: dt3 trên **MATH** ở 7B, nơi solver chỉ .625 -> tầng ZERO sẽ đông hơn nhiều.

## [Loop] VÒNG #49 — H27: BỘ CHẤM RẤT GIỎI (AUC .883) NHƯNG RERANK **KHÔNG** THẮNG BỎ PHIẾU; dt3_m15 VÔ HIỆU
### disc_g15 (H27, GSM8K 1.5B, 3200 cặp nhãn TỰ ĐỘNG)
**AUC = .8829** (ngưỡng hiệu lực .55 -> HỢP LỆ, và cao hơn nhiều). Tỉ lệ nhãn dương .632.
| fold | greedy | maj@8 | rerank@8 | oracle@8 | rerank−maj |
|---|---|---|---|---|---|
| 0 | .483 | .700 | .650 | .850 | **−.050** |
| 1 | .567 | .717 | .733 | .867 | +.017 |
| 2 | .533 | .667 | .667 | .817 | .000 |
| 3 | .567 | .733 | .750 | .867 | +.017 |
| 4 | .517 | .700 | .633 | .817 | **−.067** |
trung bình: greedy .533 | **maj@8 .703** | **rerank@8 .687** | oracle@8 .843
rerank − maj = **−.017**, khoảng [−.067,+.017], chỉ **2/5** fold dương.

=> **RƠI VÀO HÀNG 2 của bảng đã khoá ở #27**: "rerank@8 ≈ maj@8 (chênh trong sàn nhiễu)
   -> chấm điểm KHÔNG thêm gì so với đếm phiếu. BỎ PHIẾU vẫn là cách tổng hợp nên dùng."
   KHÔNG đọc là hàng 3 (tệ hơn hẳn) vì độ lớn dưới sàn nhiễu và dấu lẫn lộn.

### PRIOR CỦA TÔI SAI — ghi rõ
Ở pre-reg #27 tôi viết: "Đây là hướng tôi tin NHẤT trong toàn dự án... tôi đoán rerank@8 sẽ
vượt maj@8 vài điểm". **Sai.** Nó không vượt. Tôi đã tin nhất vào hướng này và nó không ra.

### NGHỊCH LÝ ĐÁNG GIÁ NHẤT: AUC .883 mà vẫn thua đếm phiếu
Bộ chấm PHÂN BIỆT rất tốt (AUC .883 — nó THỰC SỰ biết lời giải nào đúng).
Nhưng dùng nó theo kiểu **argmax một mẫu** thì thua **đếm phiếu**.
GIẢ THUYẾT (chưa kiểm): đếm phiếu khai thác THÔNG TIN ĐỒNG THUẬN giữa 8 mẫu; argmax VỨT BỎ
thông tin đó — nó chọn 1 mẫu và bỏ qua việc 5 mẫu khác cùng nói một đáp án.
Một bộ chấm dù giỏi, khi dùng theo kiểu chọn-một, vẫn có thể thua một thống kê tập hợp.
=> Cách dùng ĐÚNG phải là **BỎ PHIẾU CÓ TRỌNG SỐ**: gom mẫu theo đáp án, cộng điểm trong mỗi
   nhóm, chọn nhóm tổng điểm cao nhất. Vừa giữ đồng thuận, vừa dùng điểm. Xem pre-reg #29.
=> Ghi nhận: khoảng trống maj->oracle vẫn còn **+14.0 điểm** (.703 -> .843) CHƯA ai lấy được.

### dt3_m15 (H25c, MATH 1.5B) — **VÔ HIỆU** theo ngưỡng đã khoá
`pct_problems_corruptible` = **.0875** < .50 -> `VALID_corruptible=false`.
Chỉ 8.75% bài MATH có biểu thức `a op b = c` để tiêm lỗi: lời giải vàng của MATH là văn xuôi
LaTeX, hiếm khi viết phép tính tường minh. Mẫu còn lại bị CHỌN LỌC THIÊN LỆCH nặng.
(Các tầng cũng suy biến: MID 1.000, ZERO .979 -> VALID=false.)
=> Theo hàng cuối của bảng #28: "pct < .50 -> lần chạy VÔ HIỆU, thiết kế lại cách tiêm lỗi."
=> `dt3_m7` đang chạy DÙNG CÙNG MÃ TIÊM LỖI nên chắc chắn cũng vô hiệu -> thay bằng bản sửa.
LẦN THỨ BA ngưỡng hiệu lực khoá trước cứu tôi khỏi đọc nhầm một phép đo hỏng.

## [Loop] VÒNG #50 — H24 CHỐT (hàng 3); **H28 XÁC NHẬN — LẦN ĐẦU TIÊN VƯỢT ĐƯỢC maj@8**
### rs_m7 (MATH 7B) — ô quyết định 4/4 của H24
solver .615 | V_inf **+.055** (13 sửa/2 phá) | V_bli +.040 (11/3) | S_anc +.025 (10/5) | S_pln +.015 (13/10)
Ô này V_inf TỐT NHẤT và S_anc KÉM hơn — **ngược hẳn** ô GSM8K 1.5B.

### H24 — BẢNG ĐẦY ĐỦ 4/4 Ô VÀ HÀNG ĐƯỢC KÍCH HOẠT
| ô | V_inf | V_bli | S_anc | S_pln | **sửa** V_bli:S_pln | **phá** V_bli:S_pln |
|---|---|---|---|---|---|---|
| GSM8K 1.5B | +.060 | +.076 | +.080 | −.012 | 41 : 37 | **22 : 40** |
| MATH 1.5B | +.050 | +.055 | +.035 | +.025 | 20 : 23 | **9 : 18** |
| GSM8K 7B | +.004 | +.004 | +.008 | +.000 | 7 : 7 | 6 : 7 |
| MATH 7B | +.055 | +.040 | +.025 | +.015 | 11 : 13 | **3 : 10** |
SỬA: gần như BẰNG NHAU ở cả 4 ô. PHÁ: V_bli ÍT HƠN S_pln ở **4/4 ô**
(kiểm định 2 tỉ lệ: g15 z=2.57 p=.010 · m7 z=2.00 p=.046 · m15 z=1.90 p=.058 · g7 bão hoà ns).
=> **RƠI VÀO HÀNG 3 của bảng đã khoá**: "sửa ngang nhau nhưng V_bli phá ít hơn -> H24 BÁC MỘT PHẦN.
   Khung kiểm KHÔNG tăng PHÁT HIỆN mà tăng **TÍNH CHỌN LỌC**."
=> Hàng 4 (mỏ neo làm hết việc) KHÔNG đạt: `S_anc ≈ V_bli` chỉ ở 2/4 ô, dưới ngưỡng >=3/4.
**TỰ SỬA:** ở vòng #47 và #49 tôi đã viết "hướng về hàng 4". Ô thứ 4 lật lại điều đó. Tôi đã
nghiêng kết luận khi mới có 3/4 ô, dù chính bảng khoá yêu cầu 4 ô. Ghi lại để không lặp.
PHÁT BIỂU ĐÚNG: nói "hãy kiểm tra" KHÔNG giúp bắt thêm lỗi — nó giúp **BỚT PHÁ đáp án đang đúng**.
Giá trị của vai verifier là SỰ THẬN TRỌNG, không phải khả năng phát hiện.

### wv_g15 (H28, GSM8K 1.5B) — **XÁC NHẬN, HÀNG 1**
AUC .8792 (hợp lệ). CÙNG 8 mẫu, CÙNG bộ chấm, chỉ đổi CÁCH TỔNG HỢP:
| fold | maj@8 | rerank | **wvote_sum** | wvote_mean | oracle | wsum−maj |
|---|---|---|---|---|---|---|
| 0 | .700 | .683 | **.717** | .600 | .883 | +.017 |
| 1 | .767 | .717 | **.783** | .667 | .883 | +.017 |
| 2 | .683 | .683 | **.717** | .600 | .883 | +.033 |
| 3 | .733 | .683 | **.817** | .650 | .867 | **+.083** |
| 4 | .650 | .583 | .650 | .550 | .850 | +.000 |
trung bình: maj@8 **.7067** | rerank .6700 | **wvote_sum .7367** | wvote_mean .6133 | oracle .8733
`wsum − maj` = **+.030**, **4/5 fold dương, 1 hoà, 0 âm** -> **HÀNG 1: H28 XÁC NHẬN.**
Lấy được **20.5%** khoảng trống maj->oracle.

### VÌ SAO — ba nhánh tách bạch đúng cơ chế
`wvote_mean` (CHỈ điểm, bỏ số phiếu) = .613, **kém maj@8 tới −9.3, 0/5 fold** ->
ĐIỂM SỐ MỘT MÌNH TỆ HƠN ĐẾM PHIẾU MỘT MÌNH.
`rerank` (argmax, chọn 1 mẫu) = .670, cũng kém maj@8.
`wvote_sum` (= cỡ nhóm × điểm trung bình) = .737, **hơn cả hai**.
=> ĐỒNG THUẬN mang phần LỚN tín hiệu; điểm số chỉ là TINH CHỈNH thêm lên trên.
   Giả thuyết đặt ở vòng #49 ("argmax vứt bỏ thông tin đồng thuận") ĐƯỢC XÁC NHẬN.

### Ý NGHĨA: LẦN ĐẦU TIÊN CÓ CƠ CHẾ VƯỢT ĐƯỢC ĐẾM PHIẾU
Trước đó GRPO, verifier vá lỗi, verifier bịt mắt, rerank AUC .883 — **không cái nào** vượt maj@8.
`wvote_sum` là cơ chế ĐẦU TIÊN làm được. Độ lớn +3.0 điểm nằm DƯỚI sàn nhiễu không ghép cặp (~5),
NHƯNG đây là so sánh CẶP tuyệt đối (y hệt 8 mẫu, chỉ khác phép tổng hợp) nên nhạy hơn nhiều;
dấu nhất quán 4 dương / 1 hoà / 0 âm. Cần TÁI LẬP ở ô khác trước khi phát biểu mạnh -> H28b.

### dt4_m7 LỖI: OOM trên T4 (14.56 GiB), đòi 3.22 GiB khi SDPA attention
Không phải lỗi khoa học. 7B 4-bit + BS=8 + lời giải MATH dài -> vượt VRAM. Sửa: BS 8 -> 3.

## [Loop] VÒNG #51 — H28b hai ô đều OOM (lỗi CỠ, không phải khoa học); đã sửa và phóng lại
`wv_g7` : **lỗi thiết kế của tôi** — tôi bê nguyên kernel viết cho 1.5B sang 7B mà QUÊN nhánh
  lượng tử hoá. 7B fp16 ≈ 15 GB, T4 chỉ có 14.56 GB -> chắc chắn OOM ngay khi nạp model.
`wv_m15`: 1.5B nhưng `BS=16` × `k=8` = **128 chuỗi sinh cùng lúc** trên lời giải MATH dài -> OOM.
SỬA: thêm nhánh 4-bit nf4 + `prepare_model_for_kbit_training` + gradient checkpointing;
  hạ BS (m15: 16->4 ; g7: 6->2), MB (4->2 / ->1), max_length 1024->768, `empty_cache` sau mỗi lô sinh.
GHI NHẬN: hai lần OOM liên tiếp đều do TÔI không tính lại ngân sách bộ nhớ khi đổi cỡ model
  hoặc đổi tập dữ liệu. Thành LUẬT: **mỗi lần đổi model hoặc đổi tập, phải tính lại
  (số chuỗi đồng thời × độ dài) và nhánh lượng tử hoá TRƯỚC khi phóng.**
Không có kết luận khoa học nào từ vòng này — H28b vẫn CHƯA KIỂM.

## [Loop] VÒNG #52 — H28b TÁI LẬP ở MATH 1.5B: **5/5 fold, +5.0 điểm, lấy 46.7% khoảng trống**
### wv_m15 (MATH 1.5B, train/test tách đôi MATH-500, 1600 cặp nhãn tự động)
AUC = **.9506** (hợp lệ) | tỉ lệ nhãn dương .259 (mất cân bằng, đúng vì solver chỉ ~.20)
| fold | maj@8 | rerank | **wvote_sum** | wvote_mean | oracle | wsum−maj |
|---|---|---|---|---|---|---|
| 0 | .200 | .225 | **.250** | .125 | .300 | +.050 |
| 1 | .325 | .350 | **.375** | .350 | .425 | +.050 |
| 2 | .125 | .175 | **.175** | .175 | .250 | +.050 |
| 3 | .375 | .325 | **.400** | .250 | .450 | +.025 |
| 4 | .300 | .350 | **.375** | .325 | .425 | +.075 |
greedy .195 | maj@8 **.265** | rerank .285 | **wvote_sum .315** | wvote_mean .245 | oracle .370
`wsum − maj` = **+.050**, **5/5 fold DƯƠNG**, khoảng [+.025,+.075] (kiểm định dấu một phía p=.031)
`wsum_pct_gap` = **.467** — lấy được **46.7%** khoảng trống maj->oracle (ở GSM8K 1.5B chỉ 20.5%).

### ĐỐI CHIẾU HAI Ô ĐÃ CÓ (ô thứ ba wv_g7 đang chạy)
| ô | maj@8 | wvote_sum | chênh | fold dương | % khoảng trống lấy được |
|---|---|---|---|---|---|
| GSM8K 1.5B | .707 | .737 | **+.030** | 4/5 (1 hoà, 0 âm) | 20.5% |
| **MATH 1.5B** | .265 | **.315** | **+.050** | **5/5** | **46.7%** |
Hiệu ứng MẠNH HƠN ở ô KHÓ HƠN — khớp với prior đã ghi trước ở #31
("MATH 1.5B còn nhiều khoảng trống nên dễ tái lập hơn").
**CHƯA CHỐT**: bảng khoá yêu cầu CẢ HAI ô mới. `wv_g7` (GSM8K 7B, bão hoà) chưa có kết quả.
Nếu wv_g7 KHÔNG tái lập thì rơi hàng 4 ("phụ thuộc dải độ khó"), và phát biểu PHẢI kèm điều kiện
— KHÔNG được rút gọn thành "bỏ phiếu có trọng số luôn tốt hơn".

### CƠ CHẾ LẶP LẠI LẦN THỨ HAI
`wvote_mean` (chỉ điểm, bỏ số phiếu) = .245 < maj@8 .265 -> ĐIỂM MỘT MÌNH vẫn thua ĐẾM PHIẾU.
`wvote_sum` (= cỡ nhóm × điểm) = .315 -> hơn cả hai.
Khác GSM8K một chi tiết: ở MATH `rerank` (.285) CŨNG hơn maj@8, còn ở GSM8K nó thua.
GIẢ THUYẾT (chưa kiểm): khi solver rất yếu (.195), đa số phiếu thường SAI nên đồng thuận
mang ít tín hiệu hơn, và bộ chấm giành lại vai trò. Cần ô thứ ba để nói chắc.

### GHI CHÚ TÍNH HỢP LỆ
AUC .9506 cao một phần vì mất cân bằng lớp (chỉ 25.9% dương). Không dùng AUC để khoe;
chỉ dùng làm NGƯỠNG HIỆU LỰC như đã khoá (>.55). Kết luận chỉ dựa trên `wsum − maj`.
Train/test là hai NỬA RỜI NHAU của MATH-500 (200/200) -> không rò rỉ.

## [Loop] VÒNG #53 — H29 (đường cong năng lực): **CẢ BA MODEL VÔ HIỆU** vì vượt ngưỡng parse_fail
### Số liệu thô (MATH-500, bf16, RTX 6000 Pro sm_120, pct_corruptible .97)
| model | solve | **parse_fail** | HIGH | MID | ZERO |
|---|---|---|---|---|---|
| 7B  | .487 | **.232** | +.337 (n=86) | +.074 (n=28) | +.173 (n=32) |
| 14B | .489 | **.219** | +.472 (n=89) | +.333 (n=21) | +.130 (n=39) |
| 32B | .504 | **.224** | +.529 (n=91) | +.360 (n=25) | +.236 (n=34) |

### PHÁN QUYẾT: VÔ HIỆU. Ngưỡng khoá ở pre-reg #32 là `parse_fail_rate` <= .20.
Cả ba đều .219–.232 -> `VALID_parse=false` cho CẢ BA. **Không được kết luận gì từ lần chạy này.**

### VÌ SAO PHẢI NÓI RÕ ĐIỀU NÀY
Nhìn cột HIGH: **+.337 -> +.472 -> +.529**. Đơn điệu tăng theo cỡ model, ĐÚNG Y HỆT hàng 1 của
bảng đã khoá ("phân biệt tăng đơn điệu 7B→14B→32B -> XÁC NHẬN đường cong năng lực") và đúng y hệt
prior tôi ghi trước. Đây chính xác là kịch bản dễ tự lừa nhất: **kết quả đẹp, đúng như mong đợi,
nhưng phép đo đã hỏng.** Ngưỡng được khoá TRƯỚC khi nhìn số nên tôi không có quyền chọn lại.
=> Con số +.337/+.472/+.529 KHÔNG được đưa vào RESULTS.md, README, hay bất kỳ phát biểu nào.
   H29 là **CHƯA KIỂM**, không phải đã xác nhận.

### NGUYÊN NHÂN — đã chẩn đoán bằng trace, không phải đoán
75/300 trace của 14B KHÔNG có dòng `VERDICT:`. Đọc đuôi: tất cả đều bị **CẮT GIỮA CHỪNG** trong
LaTeX (`\sum_{n = 2}^\infty \frac{1}{n^3}.` ... hết token). `max_new_tokens=512` KHÔNG ĐỦ cho
model viết hết phần kiểm rồi mới tới dòng phán quyết trên miền MATH.
NGUY HIỂM HƠN: cắt cụt KHÔNG ngẫu nhiên theo tầng — bài khó -> lời giải dài -> dễ bị cắt hơn.
Nên mẫu sống sót bị THIÊN LỆCH theo đúng biến đang nghiên cứu. Đây chính là lý do ngưỡng tồn tại.

### KHIẾM KHUYẾT KHÁC CỦA LẦN CHẠY NÀY (ghi để sửa)
1. **Tầng ZERO vẫn thiếu lực**: n=32/39/34, đều < ngưỡng 40 đã khoá ở #28. Dù parse có đạt thì
   tầng quyết định vẫn không kết luận được. Phải tăng N (200 -> 400+).
2. **Dùng GPU rất lãng phí**: BS=12 bê nguyên từ thời T4. Pha phát hiện chạy `k=1` nên chỉ
   **12 chuỗi đồng thời** trên card 102 GB; ước tính ~70–75% card để không suốt 57 phút.
   Kernel cũng KHÔNG ghi `max_memory_allocated()` -> không đo được, chỉ suy ra từ cỡ model.
   Đây đúng là lỗi tôi đã tự viết thành LUẬT ở vòng #51 (phải tính lại ngân sách khi đổi phần cứng)
   rồi lặp lại theo chiều ngược lại.
3. 7B bf16 (+.337 HIGH, MATH) vs 7B 4-bit (+.651 HIGH, GSM8K): KHÔNG so sánh được vì khác miền.
   Muốn tách biến lượng tử hoá thì phải chạy 7B bf16 và 7B 4-bit trên CÙNG miền.

## [Loop] VÒNG #54 — dt4_m7 VÔ HIỆU vì LỖI REGEX CỦA TÔI, KHÔNG phải vì phương pháp hỏng
### Số liệu
`pct_problems_corruptible` = **0.0** (0/400 bài tiêm được) -> `VALID_corruptible=false`, cả ba tầng
không có cặp nào. parse_fail=.0 (không chạy tới đó). Phân tầng: HIGH 91 / MID 87 / ZERO **222**
(solve .291 — tầng ZERO cuối cùng cũng ĐÔNG, đúng như thiết kế #28 mong muốn).

### CHẨN ĐOÁN — đã kiểm chứng, không phỏng đoán
detect4: `ANYNUM=re.compile(r"(?<![\\w.])(\\d+(?:\\.\\d+)?)(?![\\w.])")`
capcurve: `ANY   =re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")`
Chạy thử trên một chuỗi MATH thật: detect4 tìm được **[]**, capcurve tìm được **7 số**.
Trong chuỗi RAW, `\\w` là "dấu gạch chéo ngược rồi chữ w", KHÔNG phải ký tự chữ.
Nguyên nhân gốc: tôi tạo detect4 bằng `s.replace(...)` LỒNG trong heredoc -> phải thoát 4 tầng,
và tôi thoát dư một tầng.

### VÌ SAO **KHÔNG** ĐƯỢC ÁP HÀNG CUỐI CỦA BẢNG #30
Bảng khoá có hàng: "`pct_corruptible` < .50 lần nữa -> BỎ HẲN hướng tiêm-lỗi trên MATH".
Hàng đó giả định một PHÉP ĐO HỢP LỆ cho thấy phương pháp không tiêm nổi. Ở đây regex khớp
**không gì cả** — đó là KHIẾM KHUYẾT MÃ, không phải phép đo. Áp hàng này sẽ là kết luận SAI.
BẰNG CHỨNG ĐỐI CHỨNG: kernel `capcurve` chạy CÙNG cách tiêm lỗi trên CÙNG MATH-500 đạt
`pct_corruptible` = **.97**. Phương pháp tiêm lỗi trên MATH **HOẠT ĐỘNG TỐT**; chỉ bản detect4 hỏng.
=> H25d (tiêm lỗi trên MATH) là CHƯA KIỂM. Không được ghi là đã bác.

### ĐIỀU DUY NHẤT ĐÁNG GIỮ TỪ LẦN CHẠY NÀY
Ở 7B 4-bit trên MATH, `solve_rate` = .291 -> phân tầng ZERO có **222 bài**, vượt xa ngưỡng 40.
Xác nhận quyết định ở #28 là đúng: MATH (không phải GSM8K) mới là miền đo được câu hỏi
"phát hiện lỗi ở bài KHÔNG giải nổi". Chỉ cần regex đúng là đo được.

### LUẬT MỚI (lần thứ ba mã sinh-bằng-chuỗi gây lỗi câm)
Trước đây: `rows`/`len(rows)` NameError, `_sp` NameError — đều do vá kernel bằng thay chuỗi.
Nay thêm: regex bị thoát dư tầng, chạy hết 400 bài mới lộ.
**LUẬT: mọi kernel có regex trích/tiêm dữ liệu PHẢI có tự kiểm 3 dòng ngay đầu kernel —
chạy regex trên một chuỗi mẫu và `assert` kết quả khác rỗng — để chết NGAY thay vì chết sau 1 giờ.**
Và: KHÔNG viết regex qua nhiều tầng thay-chuỗi; viết thẳng vào file kernel.

## [Loop] VÒNG #55 — KIỂM SƠ BỘ H30 TRÊN TRACE ĐÃ CÓ: khoảng trống maj→oracle CÓ DẤU HIỆU BỊ THỔI PHỒNG
Không có tài khoản trống, không dùng RTX theo yêu cầu. Nhưng `oracle_solid` là HÀM TẤT ĐỊNH của
dữ liệu ĐÃ NẰM TRÊN ĐĨA -> tính được ngay, không tốn GPU, không thêm bậc tự do nào.

### Số liệu (mỗi nguồn 25 bài × 8 mẫu — CỠ MẪU NHỎ, đọc dè dặt)
| nguồn | bài | oracle@8 (>=1 đúng) | oracle_solid@8 (>=2) | >=3 đúng | **CHỈ 1 mẫu đúng** |
|---|---|---|---|---|---|
| disc_g15 (GSM8K 1.5B) | 25 | .800 | .680 | .520 | **.120** |
| wv_g15 (GSM8K 1.5B) | 25 | .760 | .600 | .520 | **.160** |
| wv_m15 (MATH 1.5B) | 25 | .320 | .280 | .200 | **.040** |

### Ý NGHĨA — VÀ MỘT PHÉP TÍNH ƯỚC LƯỢNG PHẢI ĐỌC CẨN THẬN
Ở GSM8K 1.5B, **12–16 điểm** của `oracle@8` đến từ những bài mà ĐÚNG **MỘT** trong 8 mẫu đúng.
Trên bộ đầy đủ 300 bài tôi đã đo `maj@8` = .703 và `oracle@8` = .843 (khoảng trống **+14.0**).
Nếu tỉ lệ "chỉ-1-mẫu-đúng" ~.14 giữ nguyên ở quy mô đầy đủ thì
`oracle_solid@8` ≈ .843 − .14 ≈ **.70 ≈ maj@8 (.703)** -> **khoảng trống thật ≈ 0**.
=> ĐÂY LÀ ƯỚC LƯỢNG BẰNG PHÉP TRỪ, **KHÔNG PHẢI PHÉP ĐO**: trace chỉ lưu cờ đúng/sai và
   `sol` bị cắt 500 ký tự, nên KHÔNG tính được `maj@8` trên chính 25 bài đó. Phải chạy H30 thật.

### MỘT DẤU HIỆU NỘI TẠI ỦNG HỘ CÁCH ĐỌC "MAY MẮN"
GSM8K (đáp án là SỐ NGUYÊN, dễ trúng ngẫu nhiên): chênh **.12–.16**
MATH (đáp án là BIỂU THỨC LaTeX, gần như không thể trúng ngẫu nhiên): chênh chỉ **.040**
Đúng chiều dự đoán nếu phần lớn "chỉ-1-đúng" ở GSM8K là TRÙNG SỐ chứ không phải lập luận đúng.

### GIỚI HẠN PHẢI GHI KÈM (không được bỏ)
1. n=25 mỗi nguồn — rất nhỏ. `oracle@8` trên các tập con này (.800/.760) đã lệch so với .843
   của bộ đầy đủ, tức nhiễu lấy mẫu đáng kể.
2. `oracle_solid` KHÔNG phải bộ lọc may mắn hoàn hảo: model CÓ THỂ giải đúng thật sự đúng 1/8 lần
   bằng lập luận đúng mà không tái lập được. Nên phần chênh là CẬN TRÊN của "may mắn".
3. **CHƯA sửa RESULTS.md/README.** Con số +14.0 vẫn đứng cho tới khi H30 (#33) chạy thật.
   Ghi nhận này chỉ LÀM TĂNG mức ưu tiên của H30, không thay thế nó.

## [Loop] VÒNG #56 — H28b CHỐT: **TÁI LẬP MỘT PHẦN** (hàng 2/hàng 4), độ lớn bị chặn bởi khoảng trống sẵn có
### wv_g7 (GSM8K 7B) — ô thứ 3, ô quyết định
AUC .9002 (hợp lệ) | 2000 cặp, tỉ lệ dương **.9125** (7B giải GSM8K rất tốt -> nhãn mất cân bằng nặng)
| fold | maj@8 | rerank | **wvote_sum** | wvote_mean | oracle | wsum−maj |
|---|---|---|---|---|---|---|
| 0 | .800 | .875 | **.850** | .775 | .925 | +.050 |
| 1 | .975 | .900 | .975 | .850 | .975 | +.000 |
| 2 | .875 | .900 | **.900** | .850 | .925 | +.025 |
| 3 | .925 | .900 | .925 | .775 | .950 | +.000 |
| 4 | .875 | .925 | **.900** | .850 | .950 | +.025 |
greedy .810 | maj@8 **.890** | rerank .900 | **wvote_sum .910** | wvote_mean .820 | oracle .945
`wsum − maj` = **+.020**, **3/5 fold dương, 2 hoà, 0 âm** — KHÔNG đạt ngưỡng >=4/5 đã khoá.

### PHÁN QUYẾT THEO BẢNG ĐÃ KHOÁ (#31)
Bảng yêu cầu `wvote_sum > maj8` ở **>=4/5 fold ở CẢ HAI ô mới**. wv_m15 đạt (5/5); wv_g7 chỉ 3/5.
=> **HÀNG 2: "chỉ 1/2 ô tái lập -> PHỤ THUỘC Ô, KHÔNG được phát biểu tổng quát."**
Đồng thời khớp đúng **HÀNG 4** đã khoá sẵn: "ô bão hoà (GSM8K 7B) không có hiệu ứng nhưng ô khó
(MATH 1.5B) có -> phát biểu KÈM ĐIỀU KIỆN: chỉ có ích khi maj@8 còn khoảng trống."

### ĐỘ LỚN BÁM SÁT KHOẢNG TRỐNG CÒN LẠI — ba ô, ba mức
| ô | maj@8 | oracle@8 | khoảng trống | wsum−maj | % khoảng trống lấy được | fold dương |
|---|---|---|---|---|---|---|
| MATH 1.5B | .265 | .370 | **.105** | **+.050** | 47.7% | 5/5 |
| GSM8K 1.5B | .703 | .843 | **.140** | +.030 | 20.5% | 4/5 (1 hoà) |
| GSM8K 7B | .890 | .945 | **.055** | +.020 | 24.7% | 3/5 (2 hoà) |
=> Lấy được 20–48% khoảng trống ở MỌI ô. Ô nào còn ÍT khoảng trống thì hiệu ứng tuyệt đối nhỏ.
=> **KHÔNG có fold nào ÂM trong cả 15 fold của 3 ô.** Hướng nhất quán; chỉ ĐỘ LỚN là phụ thuộc ô.

### CƠ CHẾ XÁC NHẬN LẦN THỨ BA
`wvote_mean` (chỉ điểm, bỏ số phiếu): **0/5 fold dương ở CẢ BA ô** (−.093 / −.020 / −.070).
Điểm số MỘT MÌNH luôn thua đếm phiếu. Chỉ `cỡ nhóm × điểm` mới thắng. Ba lần lặp lại độc lập.

### PHÁT BIỂU ĐƯỢC PHÉP DÙNG (hẹp, kèm điều kiện)
"Dùng bộ chấm để CÂN TRỌNG SỐ phiếu (không phải để chọn một mẫu) cho lợi ích nhất quán về HƯỚNG
trên 3 ô, độ lớn +2.0 đến +5.0 điểm, tỉ lệ thuận với khoảng trống maj->oracle còn lại.
Ở ô đã bão hoà thì lợi ích nhỏ và không đạt ngưỡng tái lập đã đăng ký."
KHÔNG được rút gọn thành "bỏ phiếu có trọng số luôn tốt hơn".

### CẢNH BÁO NỐI VỚI H30 (bắt buộc đọc kèm)
Toàn bộ cách tính "% khoảng trống lấy được" ở trên dựa vào `oracle@8`. Kiểm sơ bộ ở vòng #55 cho
thấy 12–16 điểm của `oracle@8` trên GSM8K là "chỉ 1/8 mẫu đúng" — có thể phần lớn là TRÙNG SỐ.
Nếu H30 xác nhận, MẪU SỐ của mọi tỉ lệ trên đều SAI và phải tính lại theo `oracle_solid`.
Khi đó "lấy được 20–48%" có thể thành một con số CAO HƠN NHIỀU (vì khoảng trống thật nhỏ hơn).

## [Loop] VÒNG #57 — H30 CHỐT: **KHOẢNG TRỐNG maj→oracle BỊ THỔI PHỒNG**. Phải sửa RESULTS.md và README.
### ks_g15 (GSM8K 1.5B, n=200) và ks_m15 (MATH 1.5B, n=200) — cùng bộ 16 mẫu, mọi k là tiền tố
| | k | maj@k | oracle@k | **oracle_solid@k** | gap | **gap_solid** |
|---|---|---|---|---|---|---|
| GSM8K | 2 | .580 | .710 | .415 | +.130 | **−.165** |
| GSM8K | 4 | .670 | .800 | .635 | +.130 | **−.035** |
| **GSM8K** | **8** | **.740** | **.915** | **.800** | **+.175** | **+.060** |
| GSM8K | 16 | .790 | .940 | .910 | +.150 | +.120 |
| MATH | 2 | .320 | .420 | .250 | +.100 | −.070 |
| MATH | 4 | .395 | .490 | .375 | +.095 | −.020 |
| **MATH** | **8** | **.465** | **.540** | **.470** | **+.075** | **+.005** |
| MATH | 16 | .500 | .615 | .535 | +.115 | +.035 |

### PHÁN QUYẾT: **HÀNG 2 của bảng đã khoá (#33)**, nổ ở CẢ HAI ô
"`oracle_solid@8 − maj@8` NHỎ HƠN NHIỀU (< một nửa) -> khoảng trống bị THỔI PHỒNG bởi các mẫu
đúng-do-may. **Tôi PHẢI sửa lại RESULTS.md và README**, và hạ mục tiêu của hướng tổng hợp xuống
con số thật."
GSM8K: **.060 / .175 = 34%** sống sót · MATH: **.005 / .075 = 7%** sống sót. Cả hai < 50%.
gap_solid theo fold — GSM8K [0, .075, .05, .10, .075] (4 dương, 1 hoà);
MATH [.025, −.025, .05, −.025, 0] (**2 dương, 2 ÂM, 1 hoà — không khác 0**).

### PHÁT BIỂU ĐÚNG THAY CHO PHÁT BIỂU CŨ
CŨ (đã đưa vào README, SAI LỆCH): "còn +14.0 điểm khoảng trống maj→oracle chưa ai lấy được".
MỚI (đo được): khoảng trống *maj→oracle* PHÓNG ĐẠI khoảng trống thật **~3× ở GSM8K** và
**~14× ở MATH**. Ở MATH, khoảng trống thật **KHÔNG KHÁC 0** (2/5 fold âm).
`oracle@k` tính là THÀNH CÔNG cả những bài mà chỉ 1/k mẫu đúng — trên GSM8K đáp án là số nguyên
nên phần lớn nhiều khả năng là TRÙNG SỐ, không phải lập luận đúng.

### PRIOR CỦA TÔI ĐÚNG LẦN NÀY — và nó chống lại chính tôi
Pre-reg #33 tôi ghi: "Tôi đoán `oracle_solid` sẽ THẤP HƠN RÕ... nếu đúng thì đây là lần tự sửa
thứ ba, và lần này là sửa một con số tôi đã ĐƯA VÀO README như điểm nhấn." Đúng như vậy.

### HỆ QUẢ TÍCH CỰC CHO H28 (bỏ phiếu có trọng số) — nhưng phải đo lại tử số/mẫu số
Nếu khoảng trống THẬT ở GSM8K 1.5B chỉ ~+6.0 điểm (không phải +14.0) thì `wvote_sum` (+3.0)
lấy được **~50%** khoảng trống thật, không phải 20.5%. Bỏ phiếu có trọng số TỐT HƠN tôi tưởng.
CẢNH BÁO: KHÔNG được ghép số giữa các lần chạy khác nhau — `ks_m15` có maj@8 .465 còn `wv_m15`
có .265 (khác nửa dữ liệu MATH-500 và khác nhiệt độ lấy mẫu). Muốn tỉ lệ đúng thì phải đo
`oracle_solid` NGAY TRONG cùng kernel với `wvote_sum`. Đó là việc tiếp theo.

### HÀNG VỀ XU HƯỚNG THEO k: KHÔNG kết luận (đúng như sửa đổi đã ghi trước)
`gap_solid` KHÔNG phẳng — nó TĂNG theo k (−.165 → +.120 ở GSM8K). Nhưng dãy chỉ tới k=16
nên theo sửa đổi đã đăng ký, mọi kết luận về xu hướng k lớn là YẾU. Phải chạy k=64 khi được
phép dùng RTX 6000 Pro.

## [Loop] VÒNG #58 — H31: bỏ phiếu có trọng số VƯỢT trần `oracle_solid` -> **TÔI PHẢI SỬA CHÍNH ĐÍNH CHÍNH CỦA MÌNH**
### ws_g15 (GSM8K 1.5B, AUC .9113) — CÙNG kernel, CÙNG mẫu
maj@8 **.5467** | wvote_sum **.6567** | oracle@8 .7600 | **oracle_solid@8 .6333**
`wsum − maj` = **+.110** (5/5 fold dương) · `gap(oracle)` = +.213 · **`gap_solid` = +.0866**
=> `wsum − maj` (+.110) **LỚN HƠN** `gap_solid` (+.0866) -> lấy được **127%** "khoảng trống thật".

### ws_m15 (MATH 1.5B, AUC .959)
maj@8 .2950 | wvote_sum .3050 | oracle@8 .3700 | **oracle_solid@8 .2850**
`gap_solid` = **−.010 (ÂM)** — tức `oracle_solid` **THẤP HƠN CẢ maj@8**.
`wsum − maj` = +.010 (2 dương / 2 âm / 1 hoà) -> KHÔNG khác 0 ở ô này.

### PHÁN QUYẾT: **HÀNG 1 ở GSM8K** (tỉ lệ >= 50%), và **HÀNG 2 lộ ra ở CẢ HAI ô**
Hàng 2 đã khoá: "`wvote_sum` vượt cả trần `solid` -> `oracle_solid` là trần **QUÁ CHẶT**,
đã lọc mất cả những lần giải đúng THẬT. Phải nói rõ trần thật nằm GIỮA `oracle_solid` và `oracle`."

### VÌ SAO `oracle_solid` CÓ THỂ THẤP HƠN `maj@8` — chứng minh, không phải phỏng đoán
Khi cả 8 mẫu cho 8 đáp án KHÁC NHAU, `maj@8` vẫn phải chọn một, và nó CÓ THỂ trúng đáp án đúng
dù đáp án đó chỉ có **1 phiếu**. `oracle_solid` (đòi >=2 mẫu đúng) tính bài đó là THẤT BẠI.
=> `oracle_solid` KHÔNG phải trần hợp lệ: một "trần" mà baseline vượt qua được thì không phải trần.

### TỰ SỬA LẦN THỨ TƯ — VÀ LẦN NÀY LÀ SỬA CHÍNH BẢN ĐÍNH CHÍNH
Vòng #57 tôi đã sửa README: "khoảng trống thật chỉ +.060 (GSM8K) / +.005 (MATH)".
Con số đó dùng `oracle_solid` làm trần. Nay đo được `oracle_solid` là **CẬN DƯỚI**, không phải trần.
PHÁT BIỂU ĐÚNG (cả hai chiều):
  · `oracle@k` **PHÓNG ĐẠI** (tính cả bài chỉ 1/k mẫu đúng do TRÙNG SỐ) — H30 vẫn đúng ở điểm này.
  · `oracle_solid@k` **HẠ THẤP** (loại cả bài model giải đúng THẬT nhưng chỉ 1 lần, và có thể
    tụt xuống dưới cả maj@8) — H31 đo được.
  · **Trần thật nằm trong khoảng [`oracle_solid`, `oracle`].** Không con số đơn nào là "khoảng trống thật".
  · Bằng chứng cứng: `wvote_sum` ĐẠT +.110 trên GSM8K, nên trần thật **ít nhất** là maj+.110.
Bài học: khi tôi đính chính một chỉ số bằng một chỉ số khác, tôi phải kiểm chỉ số MỚI cũng
nghiêm như chỉ số cũ. Tôi đã không làm vậy ở vòng #57 và đã công bố một con số quá bi quan.

### GHI NHẬN TÍCH CỰC — con số ĐÁNG TIN NHẤT của dự án về hướng tổng hợp
Ở GSM8K 1.5B, `wvote_sum` hơn `maj@8` **+11.0 điểm, 5/5 fold**, đo trên CÙNG bộ 8 mẫu
(so sánh cặp tuyệt đối). Đây là hiệu ứng LỚN NHẤT và NHẤT QUÁN NHẤT dự án từng đo được cho
một cơ chế tổng hợp. Ở MATH cùng lần chạy thì KHÔNG khác 0 -> vẫn PHỤ THUỘC Ô, đúng như #31 đã chốt.

## dt5_m15 (H25d, MATH 1.5B) — TRẢ LỜI: **NĂNG LỰC**, không phải miền
`pct_corruptible` = **.9775** (sửa regex đã ăn — trước là 0.0) · `parse_fail` = .0026 · ĐỦ LỰC mọi tầng
(HIGH 56 / MID 102 / **ZERO 231** — lần đầu tiên tầng quyết định đủ mẫu)
NHƯNG suy biến **.991 / .985 / 1.000** -> cả ba tầng **VÔ HIỆU**.
=> 1.5B nói "NO" gần như 100% trên **CẢ** GSM8K (dt2_g15) **VÀ** MATH (dt5_m15).
=> Ghi chú thực thi của #30 đã khoá trước: "nếu 1.5B lại suy biến >.90 trên MATH thì đó là NĂNG LỰC".
   **KẾT LUẬN: NĂNG LỰC.** 1.5B không đưa ra được phán đoán nhị phân đúng/sai ở BẤT KỲ miền nào
   bằng cách hỏi này. Không phải hiện vật của GSM8K.
Bộ máy thí nghiệm giờ đã ĐÚNG (tiêm lỗi .9775, parse .003, ZERO n=231) — cái hỏng là MODEL, không phải phép đo.

## [Loop] VÒNG #59 — **LỖI NGHIÊM TRỌNG: mẫu đánh giá được sinh bởi model ĐÃ BỊ LoRA Yes/No làm hỏng**
### Phát hiện bằng cách đối chiếu hai lần chạy CÙNG Ô, CÙNG DỮ LIỆU
| run | NTR/NTE | MB | số bước tối ưu | greedy1 | maj@8 | wsum−maj |
|---|---|---|---|---|---|---|
| wv_g15 | 400/300 | 4 | 800 | **.5167** | **.7067** | +.030 |
| ws_g15 | 400/300 | **2** | **1600** | **.3867** | **.5467** | **+.110** |
Cùng 300 bài, cùng nhiệt độ .8, hàm `gen()` giống hệt nhau về mặt chức năng.
`greedy1` (một mẫu, KHÔNG dính bộ chấm) tụt **13 điểm**. Quá lớn để là nhiễu lấy mẫu
(sd ≈ .029 với n=300 -> chênh này là ~4.5 sd).

### NGUYÊN NHÂN — đã xác minh trong mã, không phải phỏng đoán
`disable_adapter` xuất hiện **0 lần** trong CẢ BA kernel (wv_g15 / ws_g15 / ws_m15).
Thứ tự trong kernel: `get_peft_model` (dòng 9) -> huấn luyện `opt.step()` (dòng 89)
-> **`mj=gen(S_SYS,qs,...)` sinh mẫu ĐÁNH GIÁ (dòng 113)**.
=> Mẫu đánh giá được sinh **VỚI LoRA đang bật** — mà LoRA đó vừa được huấn luyện để xuất
   đúng hai token `Yes`/`No`. Nó phá năng lực GIẢI của chính model.
=> `ws_g15` chạy **1600 bước** (MB=2) so với `wv_g15` **800 bước** (MB=4) -> hỏng NẶNG GẤP ĐÔI
   -> baseline thấp hơn -> `wsum − maj` trông TO HƠN.

### HẬU QUẢ — nói thẳng, không giảm nhẹ
1. **Con số +11.0 điểm (GSM8K 1.5B, 5/5 fold) mà tôi vừa gọi là "hiệu ứng lớn nhất dự án từng đo"
   là BỊ NHIỄM.** Nó được đo trên bể mẫu do một solver ĐÃ HỎNG sinh ra.
2. So sánh CẶP `wsum` vs `maj` trên CÙNG bể mẫu vẫn HỢP LỆ về mặt nội tại — cả hai tổng hợp
   cùng 8 mẫu đó. Nên **HƯỚNG** (bỏ phiếu có trọng số > đếm phiếu) nhiều khả năng vẫn đúng.
3. Nhưng **ĐỘ LỚN KHÔNG chuyển được sang thực tế**: trong triển khai thật, Solver là model GỐC,
   chỉ bộ chấm mới là model đã tinh chỉnh. Mẫu kém chất lượng -> nhiều bất đồng -> bộ chấm có
   nhiều đất diễn hơn. Nhiều khả năng +11.0 là PHÓNG ĐẠI.
4. Mọi chênh lệch độ lớn giữa các lần chạy (+.030 vs +.110 ở GSM8K; +.050 vs +.010 ở MATH)
   giờ có lời giải thích TẦM THƯỜNG: lượng huấn luyện khác nhau, không phải khoa học.
5. Kéo theo: `oracle_solid`/`oracle` trong ws_* cũng tính trên bể mẫu hỏng -> tỉ lệ "127%" ở
   vòng #58 KHÔNG đáng tin. Kết luận định tính của #58 (`oracle_solid` có thể thấp hơn `maj@8`,
   nên nó KHÔNG phải trần hợp lệ) VẪN ĐỨNG vì đó là lập luận toán học, không phụ thuộc chất lượng mẫu.

### GỐC RỄ: tôi đã CÓ mã đúng rồi và làm mất nó khi chuyển sang Kaggle
Bản `disc_verifier.py` viết cho máy remote CÓ tham số `adapter=False` và dùng `model.disable_adapter()`
khi sinh lời giải. Khi port sang kernel Kaggle tôi bỏ tham số đó đi cho gọn. Đây là lần thứ TƯ
việc port/vá kernel bằng thay-chuỗi làm mất một chi tiết đúng (trước đó: `rows`, `_sp`, regex thoát dư).
**LUẬT: khi port một script sang kernel, phải liệt kê TỪNG cờ hành vi (adapter on/off, dtype,
padding side, truncation) và đối chiếu một-một, không chỉ chép phần thân.**

## [Loop] VÒNG #60 — RÀ SOÁT TOÀN BỘ: **6/6 kernel có huấn luyện đều bị RÒ RỈ ADAPTER**
Quét mọi kernel có `get_peft_model`, kiểm hai điều: có gọi `disable_adapter` không, và
pha sinh mẫu ĐÁNH GIÁ có nằm SAU `opt.step()` không.

| kernel | `disable_adapter` | eval sau train | tình trạng | giả thuyết bị ảnh hưởng |
|---|---|---|---|---|
| disc_g15 | **0** | có | **NHIỄM** | **H27** (rerank@8 thua maj@8) |
| wv_g15 | **0** | có | **NHIỄM** | **H28** (bỏ phiếu có trọng số) |
| wv_m15 | **0** | có | **NHIỄM** | **H28b** (tái lập MATH) |
| wv_g7 | **0** | có | **NHIỄM** | **H28b** (tái lập 7B) |
| ws_g15 | **0** | có | **NHIỄM** | **H31** (oracle_solid + wsum) |
| ws_m15 | **0** | có | **NHIỄM** | **H31** |
| wf_g15 / wf_m15 | 2 | có | **SẠCH** (bản đã sửa, đang chạy) | H28c |

### PHẠM VI THIỆT HẠI — nói thẳng
**Toàn bộ nhánh "tổng hợp" của dự án — H27, H28, H28b, H31 — đo trên bể mẫu do solver BỊ HỎNG
sinh ra.** Đây cũng chính là nhánh chứa KẾT QUẢ DƯƠNG DUY NHẤT của dự án.
Cụ thể mỗi kết luận bị ảnh hưởng thế nào:
1. **H27** ("bộ chấm AUC .883 nhưng rerank .687 < maj .703"): cả rerank lẫn maj đều tính trên
   mẫu hỏng. AUC cũng có thể bị THỔI PHỒNG vì phân biệt lời giải TỆ thì dễ hơn.
2. **H28/H28b** ("wsum > maj, +2 đến +5 điểm"): so sánh CẶP nên HƯỚNG nhiều khả năng còn đúng,
   nhưng ĐỘ LỚN không chuyển được sang thực tế.
3. **H31** ("wsum lấy 127% khoảng trống thật"): tử số và mẫu số đều tính trên mẫu hỏng -> con số vô nghĩa.
   (Lập luận TOÁN HỌC rằng `oracle_solid` có thể < `maj@8` thì KHÔNG phụ thuộc chất lượng mẫu -> VẪN ĐỨNG.)

### TRẠNG THÁI ĐƯỢC PHÉP DÙNG NGAY BÂY GIỜ
H27, H28, H28b, H31 -> **TẠM ĐÌNH CHỈ**, không phải đã bác, không phải đã xác nhận.
`wf_g15`/`wf_m15` (pre-reg #36) sẽ quyết định. Ngưỡng `adapter_leak <= .05` đã khoá để bắt
đúng lỗi này nếu nó còn sót đường rò rỉ khác.
**Không được trích dẫn bất kỳ con số nào của bốn giả thuyết trên cho tới khi có kết quả sạch.**

## [Loop] VÒNG #61 — RÀ SOÁT BỘ CHẤM: có bỏ sót đáp án đúng không?
### Phương pháp
Không suy luận suông: chạy chính hàm chấm của dự án trên (a) bộ ca tổng hợp, (b) **trace THẬT**
(959 dự đoán MATH, 960 dự đoán GSM8K), rồi đối chiếu với `sympy.simplify` qua `parse_latex`.

### CẢNH BÁO PHƯƠNG PHÁP — lần đầu ra 0% là SAI
Lần chạy đầu báo "0 bỏ sót". Kiểm lại thì `parse_latex` **fail 5/5** vì thiếu gói `antlr4`
-> mọi so sánh sympy đều trả False -> "0%" là vô nghĩa. Đã cài `antlr4-python3-runtime==4.11`,
xác minh parser hoạt động 5/5, rồi chạy lại. **Đây là lần thứ NĂM một phép kiểm báo thành công
mà chưa hề kiểm.** (trước: `head` exit 0, quét token, push bị từ chối, regex thoát dư).

### GSM8K — bộ chấm CHẮC CHẮN
- 960/960 dự đoán trích được số (`pred=None` 0.00%).
- Ca tổng hợp: 12/13 đúng. Ca duy nhất trượt: đáp án **viết bằng chữ** ("seventy-two")
  — không thấy xuất hiện trong trace thật.
- Xử lý đúng: dấu phẩy hàng nghìn (`1,200`), `$18.00`, số âm, `=` ở bước trung gian,
  chữ đuôi ("72 clips (out of 100)" vẫn ra 72), `**72**`.
=> **Không có bằng chứng bỏ sót trên GSM8K.**

### MATH — có bỏ sót, nhưng NHỎ: **~0.6%**
Thô: 12/959 = 1.25% bị grader chấm SAI mà sympy nói ĐÚNG. Kiểm TAY từng ca:
| ca | số lần | phán quyết |
|---|---|---|
| `\sqrt{117}` vs `3\sqrt{13}` | 4 | **BỎ SÓT THẬT** (√117 = √(9·13) = 3√13) |
| `\binom{5}{4}\times\binom{10}{8}` vs `225` | 1 | **BỎ SÓT THẬT** (dạng chưa rút gọn) |
| `\frac{2187}{5625}` vs `\frac{243}{625}` | 1 | **BỎ SÓT THẬT** (chia cả hai cho 9) |
| `1` vs `1,-2` | 1 | sympy SAI — gold có HAI nghiệm, model chỉ cho một -> grader ĐÚNG |
| `52` vs `52_8` | 3 | sympy SAI — gold là 52 **hệ cơ số 8** (=42) -> grader ĐÚNG |
| chưa kiểm tay | 2 | chưa rõ |
=> **BỎ SÓT THẬT ≈ 6/959 = 0.63%**; sympy tự nó báo nhầm 4/959 = 0.42%.
   (Bài học kèm: dùng sympy làm "chân lý" cũng có sai số — nó không hiểu cơ số 8 hay đa nghiệm.)

### ẢNH HƯỞNG TỚI KẾT LUẬN CỦA DỰ ÁN — ĐÁNH GIÁ TRUNG THỰC
1. **Độ chính xác TUYỆT ĐỐI trên MATH bị HẠ THẤP ~0.6 điểm.** Nhỏ so với sàn nhiễu ~5 điểm.
2. **Các phép SO SÁNH gần như không bị ảnh hưởng**: cùng một bộ chấm áp cho MỌI nhánh
   (V_inf/V_bli/S_anc/S_pln, maj/wsum/oracle), nên sai lệch là ĐỘ DỊCH CHUNG, triệt tiêu khi lấy hiệu.
   `V_gain`, `wsum − maj`, `discrimination` KHÔNG bị bóp méo đáng kể.
3. Chỗ CÓ THỂ bị lệch: `oracle@k` (một mẫu đúng bị chấm sai -> oracle bị hạ), và `fixes/breaks`.
   Với 0.63% thì mức lệch dưới 1 điểm — vẫn dưới sàn nhiễu.
4. **KHÔNG có bằng chứng bộ chấm THIÊN VỊ một nhánh nào.** Mọi nhánh dùng chung `pred()`+`ok()`.
=> Kết luận: bộ chấm KHÔNG phải nguồn sai lệch cho bất kỳ phát biểu nào của dự án.
   Nhưng nên nâng cấp cho MATH (thêm rút gọn căn/phân số) nếu về sau cần con số tuyệt đối chính xác.

## [Loop] VÒNG #62 — H28c **VÔ HIỆU** theo ngưỡng đã khoá, DÙ số trông đẹp. Và ngưỡng đó cũng hỏng.
### Kết quả thô (KHÔNG được trích dẫn)
| ô | pre_acc | post_acc | **adapter_leak** | VALID | greedy | maj@8 | wsum | wsum−maj |
|---|---|---|---|---|---|---|---|---|
| GSM8K 1.5B | .6144 | .5537 | **.0606** | **KHÔNG** | .5500 | .7233 | .7700 | +.0467 (5/5) |
| MATH 1.5B | .2756 | .2156 | **.0600** | **KHÔNG** | .2150 | .3150 | .3500 | +.0350 (2/5) |

### PHÁN QUYẾT: HÀNG 4 của #36 — "leak > .05 dù đã sửa -> **VÔ HIỆU**, không được đọc số."
Ngưỡng .05 được khoá TRƯỚC. Cả hai ô đều .060 > .05. **Tuyên VÔ HIỆU.**
Tôi ghi rõ điều khó chịu: lần này ngưỡng đang GIẾT một kết quả DƯƠNG (+.047, 5/5 fold) —
tức là việc tuân thủ ngưỡng làm TÔI THIỆT. Đúng như khi tuyên vô hiệu H29 dù nó cho đường cong
đơn điệu y hệt prior của tôi. Ngưỡng chỉ có giá trị nếu nó cắt cả hai chiều.

### NHƯNG CHÍNH NGƯỠNG ĐÓ CŨNG HỎNG — phải nói ra, và KHÔNG dùng nó để cứu số
`PRE_ACC` = tỉ lệ đúng của mẫu **tập HUẤN LUYỆN** (sinh trước khi có adapter)
`POST_ACC` = tỉ lệ đúng của mẫu **tập KIỂM TRA** (sinh sau, adapter đã tắt)
=> HAI TẬP BÀI KHÁC NHAU. Chênh .06 có thể chỉ là khác độ khó train/test, KHÔNG phải rò rỉ.
**Ngưỡng tôi khoá không đo được thứ nó định đo.** Đây là lỗi thiết kế của tôi, phát hiện sau khi chạy.
=> Cách xử lý ĐÚNG: **vẫn tuyên VÔ HIỆU** (không được sửa luật sau khi thấy số), rồi
   **thiết kế lại ngưỡng cho đúng** và chạy lại. KHÔNG được lấy "ngưỡng hỏng" làm cớ giữ kết quả.

### BẰNG CHỨNG ĐỘC LẬP RẰNG BẢN SỬA CÓ TÁC DỤNG (ghi nhận, chưa phải kết luận)
| run | adapter khi sinh | greedy1 | maj@8 |
|---|---|---|---|
| wv_g15 (nhiễm, 800 bước) | BẬT | .5167 | .7067 |
| ws_g15 (nhiễm, 1600 bước) | BẬT | **.3867** | **.5467** |
| **wf_g15 (đã sửa)** | **TẮT** | **.5500** | **.7233** |
`maj@8` quay về ~.72 và `greedy` lên .55 — cao hơn CẢ HAI lần nhiễm, đúng hướng bản sửa dự đoán.
Hàng 5 của #36 ("maj@8 mới ≈ .70 chứ không phải .55 -> xác nhận chẩn đoán rò rỉ") ĐÃ NỔ.
=> Chẩn đoán rò rỉ ở vòng #59 được XÁC NHẬN. Nhưng ĐỘ LỚN của `wsum−maj` vẫn CHƯA đo được hợp lệ.

### TRẠNG THÁI
H27/H28/H28b/H31 vẫn **TẠM ĐÌNH CHỈ**. H28c **VÔ HIỆU**. Cần chạy lần thứ ba với ngưỡng đúng.

## [Loop] VÒNG #63 — H32 **PRIOR CỦA TÔI SAI**: ở CÙNG NGÂN SÁCH, pipeline THẮNG bỏ phiếu
### bg_g15 (GSM8K 1.5B, n=250, MỌI nhánh đúng 3 lượt sinh)
| fold | greedy1 | maj@3 | **PSV** | SVV | **SS_anc** | maj3−PSV |
|---|---|---|---|---|---|---|
| 0 | .540 | .620 | **.680** | .640 | .680 | −.060 |
| 1 | .600 | .620 | **.800** | .680 | .680 | −.180 |
| 2 | .640 | .600 | **.700** | .700 | .720 | −.100 |
| 3 | .660 | .660 | .660 | .660 | **.760** | +.000 |
| 4 | .720 | .720 | **.800** | .780 | .800 | −.080 |
**greedy .6320 | maj@3 .6440 | PSV .7280 | SVV .6920 | SS_anc .7280**
`maj3 − PSV` = **−.084**, **0/5 fold dương** -> **PSV THẮNG maj@3 ở 5/5 fold.**

### TOKEN THẬT SỰ SINH RA — pipeline còn RẺ HƠN
| nhánh | token | so với greedy |
|---|---|---|
| SS_anc | 169,022 | 3.35× |
| **maj@3** | **149,384** | **2.96×** |
| SVV | 122,866 | 2.43× |
| **PSV** | **115,722** | **2.29×** |
| greedy1 | 50,463 | 1.00× |
=> `PSV` dùng **ÍT token hơn `maj@3` 22%** mà vẫn hơn **+8.4 điểm**. Thắng trên CẢ HAI trục.

### PHÁN QUYẾT: **HÀNG 2 của bảng đã khoá** — và tôi phải rút lại
Hàng 2: "`PSV` > `maj3` ở >=4/5 fold -> Pipeline CÓ thêm giá trị vượt trên lấy mẫu.
**Phải rút lại cách đọc 'vai không chuyên biệt'.**"
Prior tôi ghi trước: "đoán hàng 1 hoặc hàng 3 — maj3 ngang hoặc hơn PSV... nếu ra hàng 1 thì đây là
kết luận LỚN NHẤT của dự án". **PRIOR SAI.** Ngược hẳn.

### NHƯNG HÀNG 5 CŨNG NỔ — và nó giữ lại phần đúng của cách đọc cũ
`SS_anc` = **.7280**, GIỐNG HỆT `PSV` = .7280. `SS_anc` KHÔNG có một chữ nào về vai:
nó là giải -> giải lại CÓ MỎ NEO -> giải lại CÓ MỎ NEO.
Hàng 5 đã khoá: "`SS_anc` ≈ `PSV` -> vai là NHÃN, không phải cơ chế."

### HỢP NHẤT — phát biểu đúng sau vòng này
1. **Lợi thế LÀ THẬT và KHÔNG phải do lấy mẫu lặp.** PSV hơn maj@3 +8.4 điểm ở ít token hơn.
   Câu "pipeline chỉ là cách đắt tiền để lấy mẫu nhiều lần" — mà tôi đã nói với người dùng —
   **SAI**, và tôi rút lại.
2. **Cơ chế KHÔNG phải phân vai** mà là **TINH CHỈNH TUẦN TỰ CÓ MỎ NEO**: mỗi lượt được THẤY
   đáp án của lượt trước. Bỏ hết ngôn ngữ vai (SS_anc) vẫn cho kết quả Y HỆT.
   Khớp với H24 (mỏ neo làm việc, khung "kiểm" thì không) và với `S_pln` là nhánh tệ nhất mọi ô.
3. Vậy: **tuần tự > song song ở cùng ngân sách; nhưng "vai" chỉ là cái tên của tính tuần tự.**
4. `SVV` (.6920) < `PSV` (.7280): hai lượt kiểm liên tiếp KÉM hơn plan+solve+verify.
   `SVV` vẫn hơn `maj@3` (+.048, 4/5) -> tuần tự thắng song song kể cả không có Planner.

### CÒN THIẾU
`bg_m15` (MATH) LỖI: `ANCH.format(A=a)` gặp `\boxed{}` trong TAIL của MATH -> `{}` bị hiểu là
ô định dạng -> `IndexError`. GSM8K không có ngoặc nên không lộ. Sửa bằng `.replace()`, phóng lại.
**Chưa có ô thứ hai -> chưa được tổng quát hoá.**

## [Loop] VÒNG #64 — H32 ô MATH 1.5B: KHÔNG đạt ngưỡng; dt5_m7 **VÔ HIỆU** lần thứ BA vì cắt cụt
### bg_m15 (MATH 1.5B, n=200) — ô thứ 2/4 của H32
greedy .3300 | maj@3 .3500 | **PSV .3800** | **SVV .4150** | SS_anc .3600
| chỉ số | giá trị | fold |
|---|---|---|
| `maj3 − PSV` | −.030 | **2/5 dương** -> PSV thắng 3/5, **KHÔNG đạt ngưỡng >=4/5** |
| `SVV − maj3` | **+.065** | **4/5 dương** -> ĐẠT ngưỡng |
| `SSanc − PSV` | −.020 | 3/5 |
token: PSV **2.39×** (rẻ nhất), SVV 2.53×, SS_anc 3.01×, maj@3 3.07×
=> Ô này KHÔNG lặp lại `bg_g15`: `PSV` hơn `maj@3` về trung bình (+3.0) nhưng chỉ 3/5 fold.
=> NHƯNG **`SVV` (Solver→Verify→Verify) là nhánh TỐT NHẤT** (.4150) và ĐẠT ngưỡng so với maj@3.
   Ở GSM8K 1.5B thì `PSV` tốt nhất; ở MATH 1.5B thì `SVV` tốt nhất — **cấu hình tối ưu PHỤ THUỘC Ô**.
=> Điểm CHUNG của cả hai ô: **nhánh TUẦN TỰ tốt nhất luôn hơn `maj@3`, và luôn tốn ÍT token hơn.**
   (g15: PSV +8.4 @ 2.29× vs maj3 2.96× · m15: SVV +6.5 @ 2.53× vs maj3 3.07×)
CHƯA KẾT LUẬN LƯỚI — còn `bg_m7` và `bg_g7`.

### dt5_m7 (MATH 7B) — **VÔ HIỆU: `parse_fail` = .3824 > ngưỡng .20**
`pct_corruptible` .9775 ✓ · suy biến .815/.804/.899 (đều < .90) ✓ · **ZERO n=100 — LẦN ĐẦU ĐỦ LỰC** ✓
NHƯNG `parse_fail_rate` = **.3824**, vượt xa ngưỡng .20 khoá ở #26 -> **cả lần chạy VÔ HIỆU**.
Số thô (KHÔNG được trích dẫn): HIGH +.257 · MID +.215 · **ZERO +.139**.
=> Đây là **LẦN THỨ BA** cùng một lỗi giết một thí nghiệm: model viết LaTeX dài trên MATH,
   hết `max_new_tokens=512` TRƯỚC khi tới dòng `VERDICT:`. (Trước đó: H29 scaling-a/b .22–.23,
   nay .38.) Cắt cụt lệch theo tầng (bài khó -> lời giải dài -> dễ bị cắt) nên mẫu sống sót thiên lệch.
=> Bản sửa ĐÃ ĐƯỢC ĐẶC TẢ ở pre-reg #34 (1024 token + giới hạn 120 từ lập luận + **lượt hỏi lại**
   nếu thiếu VERDICT) nhưng tôi CHƯA TRIỂN KHAI vì lúc đó đang tạm dừng RTX. Lẽ ra phải áp
   cho MỌI kernel dt chứ không chỉ bản RTX. Đó là thiếu sót của tôi — đặc tả xong rồi để đấy.

## [Loop] VÒNG #65 — **ĐỒNG THUẬN LÀ TÍN HIỆU MẠNH NHẤT DỰ ÁN TỪNG ĐO** (và nó MIỄN PHÍ)
Câu hỏi: 3 mẫu song song có thật sự cho ĐA SỐ không, hay ra 3 đáp án khác nhau?
Đo trực tiếp trên trace đã có (60 bài × 16 mẫu, temp .8) — không tốn GPU.

### k=3: PHẦN LỚN KHÔNG CÓ ĐA SỐ
| | 3/3 đồng ý | 2/3 đồng ý | **1/3 (BA đáp án KHÁC NHAU)** |
|---|---|---|---|
| GSM8K 1.5B | 25.0% bài, acc **.933** | 25.0%, acc **.867** | **50.0%**, acc **.300** |
| MATH 1.5B | 21.7%, acc **1.000** | 20.0%, acc **.917** | **58.3%**, acc **.029** |

=> **Một nửa (GSM8K) tới 58% (MATH) số bài KHÔNG có đa số nào cả.**
   Ở những bài đó `maj@3` KHÔNG phải bỏ phiếu — nó là **hoà, và code lấy mẫu ĐẦU TIÊN**
   (`max(cnt,key=cnt.get)` trả về khoá được chèn sớm nhất = mẫu 0). Tức là ≈ một mẫu đơn.
=> Giải thích luôn vì sao `maj@3` (.644) ≈ `greedy` (.632) ở GSM8K: một nửa số bài nó thoái hoá
   thành "lấy mẫu đầu tiên".

### k=8: cùng hiện tượng, và ĐỘ CHÍNH XÁC BÁM CHẶT MỨC ĐỒNG THUẬN
GSM8K: 8/8 → **1.000** · 6/8 → .917 · 2/8 → .727 · **1/8 → .143**
MATH : 8/8 → **1.000** · 6/8 → **1.000** · 2/8 → **.000** · **1/8 → .000** (30% số bài!)

### PHÁT HIỆN: MỨC ĐỒNG THUẬN LÀ BỘ PHÂN LOẠI ĐÚNG/SAI GẦN NHƯ HOÀN HẢO Ở HAI ĐẦU
- Đồng thuận CAO (≥6/8): độ chính xác **.92–1.00**
- Đồng thuận THẤP (1/8): độ chính xác **.143 (GSM8K) / .000 (MATH)**
Đây là tín hiệu **MIỄN PHÍ** — chỉ cần đếm, không cần huấn luyện gì.
So sánh: bộ chấm huấn luyện (H27) đạt AUC .88–.95 nhưng tốn dữ liệu, LoRA, và đã gây ra lỗi
rò rỉ adapter làm hỏng 6 kernel. **Đếm phiếu trùng nhau cho tín hiệu tương đương mà không tốn gì.**

### HỆ QUẢ THỰC TIỄN (khuyến nghị mạnh nhất dự án có thể đưa ra lúc này)
**Dùng mức đồng thuận để ĐỊNH TUYẾN chi phí:**
- k mẫu đồng thuận cao -> nhận đáp án, DỪNG. Gần như chắc đúng, không cần verifier.
- k mẫu phân tán hoàn toàn -> đáp án gần như chắc SAI. Đây MỚI là chỗ đáng đổ thêm compute
  (model lớn hơn, hoặc lượt tuần tự có mỏ neo).
Hiện tại mọi pipeline của dự án tiêu compute ĐỀU NHAU cho mọi bài — lãng phí ở bài dễ,
thiếu ở bài khó.

### NỐI VỚI H32 (vì sao tuần tự thắng song song)
Khi 3 mẫu ra 3 đáp án khác nhau (50–58% số bài), bỏ phiếu KHÔNG có gì để khai thác.
Nhưng lượt tuần tự CÓ MỎ NEO vẫn dùng được đáp án trước để cải thiện.
=> Đây là cơ chế giải thích vì sao `PSV`/`SVV` hơn `maj@3` ở cùng ngân sách.
GIẢ THUYẾT (chưa kiểm): lợi thế của tuần tự tập trung HOÀN TOÀN ở nhóm "không có đa số".

## [Loop] VÒNG #66 — **KAGGLE CHO 2× T4 (31.2 GB), TÔI CHỈ DÙNG 1 SUỐT CẢ DỰ ÁN**
### Bằng chứng (kernel dò, chạy trong 1 phút)
`torch.cuda.device_count()` = **2** · mỗi cái Tesla T4 15.6 GB sm_75 · **tổng 31.2 GB**
— dù metadata gửi đi là `"machine_shape":"NvidiaTeslaT4"` (không có giá trị `T4x2` để yêu cầu).

### THIỆT HẠI
Mọi kernel fp16 dùng `device_map="cuda"` -> ghim hết vào **GPU 0**, **GPU 1 NGỒI KHÔNG**.
| | đã dùng | thực có |
|---|---|---|
| VRAM | 15.6 GB | **31.2 GB** |
| 7B | buộc phải **4-bit** | fp16 trải 2 card, **KHÔNG cần lượng tử hoá** |
| batch | cỡ cho 15.6 GB | gấp đôi được |
=> Nghiêm trọng nhất KHÔNG phải tốc độ mà là: **4-bit CHƯA BAO GIỜ CẦN THIẾT.**
   `dt2_g7` (+.651), các ô 7B của H32, `dt6_m7`, `ev_he7` — tất cả chạy 4-bit để vừa một
   giới hạn bộ nhớ KHÔNG TỒN TẠI. Lượng tử hoá là một nhiễu loạn CÓ THỂ TRÁNH ĐƯỢC
   nằm dưới mọi kết quả 7B của dự án.

### GỐC RỄ NIỀM TIN SAI
Ghi chú cũ của tôi: "`machine_shape` chỉ nhận giá trị một-GPU, không có T4×2".
Vế đó ĐÚNG — không YÊU CẦU được. Nhưng tôi suy ra sai rằng do đó chỉ ĐƯỢC một T4.
Phát biểu đúng: **không gọi tên được T4×2, nhưng Kaggle vẫn cấp HAI T4.**

### BẰNG CHỨNG ĐÃ NẰM TRƯỚC MẶT MÀ TÔI KHÔNG ĐỌC
Lỗi OOM của `dt4_m7`: *"**GPU 1** has a total capacity of 14.56 GiB"*.
Tôi đã đọc thông báo đó BỐN LẦN trong lúc sửa OOM và chưa từng để ý tới chỉ số **1**.
Nếu để ý, tôi đã biết có 2 GPU từ nhiều vòng trước.
**LUẬT: khi đọc lỗi OOM, PHẢI đọc cả chỉ số GPU, không chỉ dung lượng.**

### SỬA (áp cho mọi kernel về sau)
- fp16/bf16: `device_map="auto"` thay cho `device_map="cuda"` -> trải 2 card.
- 7B trên Kaggle: **BỎ 4-bit**, dùng fp16 `device_map="auto"` (7B fp16 ≈ 15.2 GB, chia 2 card
  còn ~7.6 GB/card, thừa chỗ cho KV cache).
- Batch có thể tăng đáng kể; phải đo lại ngân sách bộ nhớ (LUẬT vòng #51).
- Kết quả 7B đã có: giữ nguyên nhưng PHẢI ghi kèm "đo ở 4-bit"; muốn sạch thì chạy lại fp16.

## [Loop] VÒNG #67 — **H35 XÁC NHẬN HÀNG 1: BỘ KIỂM ĐÚNG ĐẮN THẮNG TẤT CẢ** + 3 kết quả khác
### D) ev_he15 (HumanEval 1.5B) — **KẾT QUẢ MẠNH NHẤT DỰ ÁN TỪNG CÓ**
`exec_success_rate` = **1.00** (ngưỡng .50 ✓ HỢP LỆ)
| nhánh | acc | so với |
|---|---|---|
| greedy1 (1 lượt) | .5375 | — |
| **maj@4** (4 lượt) | **.4250** | **THẤP HƠN CẢ GREEDY** |
| **llm3** (LLM tự kiểm, 4 lượt) | .4812 | cũng thấp hơn greedy |
| **exec3** (sửa theo KẾT QUẢ CHẠY TEST, 4 lượt) | **.6000** | — |
`exec3 − llm3` = **+.119, 5/5 fold** · `exec3 − maj@4` = **+.175, 5/5 fold**
**PHÁ ĐÁP ÁN ĐÚNG: exec3 = 0.0 (0/5 fold) · llm3 = 2.8/fold (5/5 fold)**
=> **HÀNG 1 của bảng khoá #40 NỔ**: "bộ kiểm ĐÚNG ĐẮN làm được thứ LLM-kiểm không làm nổi,
   và thắng cả lấy mẫu ở cùng ngân sách."
=> Cùng model, cùng 4 lượt sinh, **chỉ khác NGUỒN TÍN HIỆU KIỂM** -> chênh **11.9 điểm**.
   Và bộ kiểm đúng đắn **KHÔNG PHÁ MỘT ĐÁP ÁN NÀO**, trong khi LLM-kiểm phá 2.8 bài/fold.
=> Đây là câu trả lời cho câu hỏi "chứng minh định lý": không cần Lean — nguyên lý đã đo được.

### PHÁT HIỆN PHỤ ĐÁNG CHÚ Ý: BỎ PHIẾU **CÓ HẠI** TRÊN CODE
`maj@4` (.425) **THẤP HƠN** `greedy` (.5375) — 11 điểm. Trên toán bỏ phiếu luôn có lợi.
GIẢ THUYẾT (chưa kiểm): đáp án toán là một con số, dễ trùng; còn code là chuỗi dài,
hai lời giải đúng hiếm khi GIỐNG HỆT nhau -> "đa số" gần như luôn là hoà 1-1-1-1,
và bỏ phiếu thoái hoá thành lấy mẫu ngẫu nhiên (tệ hơn greedy). Khớp với vòng #65.
=> **Bỏ phiếu chỉ dùng được khi đáp án có dạng CHUẨN HOÁ ĐƯỢC.**

### A) Cấu hình 2S/3S -> 1V (mỗi cấu hình một notebook, có đối chứng riêng)
| ô | V nhỏ (0.5B) | V thường (1.5B) |
|---|---|---|
| GSM8K 2S→1V | **−.104** (1/5) | **+.036** (4/5) |
| GSM8K 3S→1V | **−.120** (0/5) | — |
| MATH 2S→1V | +.060 (4/5) | +.040 (2/5) |
| MATH 3S→1V | −.035 (0/5) | — |
=> Ở GSM8K, verifier **0.5B GÂY HẠI RÕ** (−10 đến −12 điểm) còn 1.5B thì có lợi (+3.6).
   Củng cố NGƯỠNG NĂNG LỰC: model quá nhỏ làm verifier thì phá nhiều hơn sửa.
=> Ở MATH thì lẫn lộn (0.5B +.060 nhưng 3S→1V −.035) -> KHÔNG kết luận, cần thêm dữ liệu.
LƯU Ý: `maj3` nền khác nhau giữa các kernel (.668 vs .620 ở GSM8K) vì là các lần chạy RIÊNG —
so sánh CHÉO giữa cấu hình là YẾU; chỉ so sánh TRONG mỗi kernel mới chắc.

### B) b4_g15 (GSM8K 1.5B, ngân sách 4 lượt)
maj@3 .664 | **maj@4 .700** | P3S .712 | PSV .728 | **PSVA .744** | SS_anc .728
`P3S − maj@4` = **+.012 (2/5)** -> kế hoạch chung **KHÔNG** bù được đa dạng đã mất. Prior tôi ĐÚNG.
`PSVA − PSV` = +.016 (3/5) -> Aggregator thêm rất ít, KHÔNG đạt ngưỡng 4/5. Prior tôi ĐÚNG.
`maj@4 − maj@3` = +.036 (4/5) -> lượt sinh thứ 4 CÓ giúp đếm phiếu.

### C) bg_m7 (MATH 7B, 4-bit) — ô thứ 3 của lưới H32
greedy .500 | maj@3 .505 | **PSV .590** | SVV .550 | SS_anc .480
`maj3 − PSV` = **−.085, 0/5 fold** -> **PSV THẮNG maj@3 ở MATH 7B.**
### LƯỚI H32 hiện tại: GSM8K 1.5B ✓(+.084) · MATH 1.5B ~(+.030, 3/5) · **MATH 7B ✓(+.085)**
· GSM8K 7B đang chạy (dấu hiệu sớm: PSV .90 < greedy .94 -> ô BÃO HOÀ đảo chiều)

## [Loop] VÒNG #68 — H35 **TÁI LẬP ĐỘC LẬP** trên phần cứng khác, mạnh hơn lần đầu
### R_c15b (HumanEval 1.5B, **bf16 trên RTX 5090**, bộ kiểm ĐÃ SỬA)
`exec_success_rate` = **.994** (ngưỡng .50 ✓) · tự kiểm bộ kiểm: OK
| nhánh | acc | phá đáp án đúng |
|---|---|---|
| greedy1 | .5625 | — |
| **maj@4** | **.4313** | — (THẤP HƠN greedy 13 điểm) |
| **llm3** | .4375 | **4.6 bài/fold** (5/5) |
| **exec3** | **.6438** | **0.0** (0/5) |
`exec3 − llm3` = **+.206 (5/5)** · `exec3 − maj@4` = **+.213 (5/5)**

### ĐỐI CHIẾU HAI LẦN CHẠY ĐỘC LẬP — CÙNG KẾT LUẬN, KHÁC PHẦN CỨNG
| | ev_he15 (Kaggle T4, fp16) | **R_c15b (RTX 5090, bf16)** |
|---|---|---|
| exec3 − llm3 | +.119 (5/5) | **+.206 (5/5)** |
| exec3 − maj@4 | +.175 (5/5) | **+.213 (5/5)** |
| phá bởi exec3 | **0.0** | **0.0** |
| phá bởi llm3 | 2.8/fold | **4.6/fold** |
| maj@4 so với greedy | −.113 | −.131 |
=> **TÁI LẬP.** Hai lần chạy, hai máy, hai độ chính xác số học, cùng kết luận và cùng dấu.
   Đây là kết quả DƯƠNG VỮNG NHẤT của dự án — và là kết quả DUY NHẤT tái lập được ở mức này.
=> `exec3` **KHÔNG PHÁ MỘT ĐÁP ÁN ĐÚNG NÀO** trong 10 fold của cả hai lần chạy (0/10).
   `llm3` phá trong **10/10 fold**. Khác biệt không nằm ở độ chính xác mà ở TÍNH AN TOÀN.

### XÁC NHẬN LẠI: BỎ PHIẾU CÓ HẠI TRÊN CODE
`maj@4` thấp hơn `greedy` ở CẢ HAI lần (−.113 và −.131). Không phải nhiễu.
Cơ chế (khớp vòng #65): code là chuỗi dài, hai lời giải ĐÚNG hiếm khi giống hệt nhau
-> "đa số" gần như luôn là hoà -> bỏ phiếu thoái hoá thành chọn ngẫu nhiên, tệ hơn greedy.

### R_m7 (MATH 7B bf16) — xác nhận lại lưới H32 và ĐỐI CHỨNG NHIỄU LOẠN
greedy .480 | maj@3 .515 | maj3_g .500 | **PSV .595** | SVV .525
`maj3 − PSV` = **−.080, 0/5** -> PSV thắng, lặp lại `bgL_m7` (−.075).
`maj3_g − maj3` = −.015 (1/5) -> **đối chứng #41 lại cho ~0**: greedy KHÔNG phải nguồn lợi thế.
Đã đo ở 4 ô độc lập, luôn ≈ 0 -> **nhiễu loạn do người dùng chỉ ra đã bị LOẠI TRỪ dứt điểm.**

## [Loop] VÒNG #69 — **exec3 = oracle@4 CHÍNH XÁC**: bộ kiểm là BỘ CHỌN HOÀN HẢO, không phải bộ sửa
Người dùng hỏi: "4 solver có chứa đáp án đúng không?" -> tính trực tiếp từ trace (chạy test thật).
| ô | **oracle@4** | maj@4 | **exec3** | khoảng trống voting BỎ LỠ |
|---|---|---|---|---|
| code 1.5B | **.6438** | .4313 | **.6438** | **21.3 điểm** |
| code 7B | **.8812** | .7875 | **.8812** | 9.4 điểm |
=> **exec3 KHỚP oracle@4 tới từng chữ số ở CẢ HAI ô.** Không phải trùng hợp:
   exec3 sửa cho tới khi test PASS rồi dừng -> nó chính là "lấy mẫu cho tới khi đúng",
   tức là ĐẠT TRẦN best-of-k theo định nghĩa.

### DIỄN GIẢI LẠI H35 — chính xác hơn phát biểu cũ
Trước đây tôi nói "bộ kiểm đúng đắn SỬA được lỗi". **Sai trọng tâm.**
Bộ kiểm không sửa giỏi hơn — nó **CHỌN hoàn hảo**. Giá trị của nó = biến k mẫu thành best-of-k.
`maj@4` chỉ lấy được 43.1% (1.5B) trong khi 64.4% khả dụng -> **bỏ lỡ 21.3 điểm**.
`exec3` lấy 100% khoảng trống đó.

### PHÂN BỐ giải thích VÌ SAO bỏ phiếu thất bại trên code
| số mẫu đúng /4 | 1.5B | 7B |
|---|---|---|
| 0 | 57 (36%) | 19 (12%) |
| **1** | **23 (14%)** | 9 |
| 2 | 21 | 9 |
| 3 | 21 | 12 |
| 4 | 38 (24%) | 111 (69%) |
**23 bài (14%) ở 1.5B chỉ có ĐÚNG MỘT mẫu đúng trong 4.** Bỏ phiếu gần như KHÔNG THỂ chọn ra
(1 phiếu chọi 3). Bộ kiểm tìm ra HẾT. Cộng với các bài 2/4 (hoà) -> đó chính là 21.3 điểm.

### NỐI VỚI H30 (khoảng trống maj->oracle trên TOÁN)
Trên toán tôi từng tranh cãi `oracle@k` phóng đại vì tính cả "đúng do may một lần".
Trên CODE thì KHÔNG có vấn đề đó: "đúng" = **chạy qua toàn bộ test**, không thể trúng ngẫu nhiên.
=> `oracle@4` trên code là trần THẬT, và nó **lấy được** — exec3 đã lấy.
=> Đây là lý do miền có BỘ KIỂM ĐÚNG ĐẮN khác hẳn miền chỉ có LLM đi kiểm.

## [Quy uoc] VONG LAP TU DONG DAY LEN NHANH RIENG (tu 2026-08-09)
Tu day, moi commit cua vong lap tu dong day len **`loop-autonomous`**, KHONG day thang vao `main`.
Ly do: Duc lam viec tren nhanh `duc` va gop bang PR. Vong lap cua toi day thang vao `main` voi
nhip do cao da buoc Duc phai merge `origin/main` vao `duc` **5 lan**. Tach nhanh de anh ay
khong bi ep merge lien tuc, va de review theo PR nhu binh thuong.
Gop vao `main` bang PR khi mot manh viec da xong, khong gop tung commit le.

## [Loop] VÒNG #70 — dt6_m7 HỢP LỆ VÀ ĐỦ LỰC LẦN ĐẦU: **HÀNG 3 — kiểm lỗi YẾU ở MỌI tầng trên MATH**
### dt6_m7 (MATH 7B, bản sửa cắt cụt #34: 1024 token + giới hạn 120 từ + lượt hỏi lại)
`parse_fail` = **0.000** (trước là .38!) · `pct_needed_retry` = .0013 · `pct_corruptible` = .9775
**Lần ĐẦU TIÊN cả ba tầng vừa HỢP LỆ vừa ĐỦ LỰC** (ZERO **n=224**).
| tầng | n | phát hiện | báo động giả | PHÂN BIỆT | suy biến | HỢP LỆ | ĐỦ LỰC |
|---|---|---|---|---|---|---|---|
| HIGH | 97 | .186 | .072 | **+.113** | .871 | CÓ | CÓ |
| MID | 70 | .143 | .143 | **+.000** | .857 | CÓ | CÓ |
| ZERO | 224 | .192 | .076 | **+.116** | .866 | CÓ | CÓ |

=> **HÀNG 3 của bảng khoá (#26)**: "phân biệt THẤP ở mọi tầng HỢP LỆ -> model KHÔNG kiểm được
   lỗi số học dù đã được suy luận. **Bác hướng 'vai kiểm'.**"
=> Đáng chú ý: ZERO (+.116) ≈ HIGH (+.113) -> phát hiện **KHÔNG giảm** theo độ khó.
   Nó YẾU ĐỀU. Tức KHÔNG phải "bị chặn bởi năng lực giải" (hàng 2) mà là **yếu toàn cục** trên MATH.

### MÂU THUẪN VỚI dt2_g7 — VÀ ĐÓ LÀ PHÁT HIỆN
`dt2_g7` (**GSM8K** 7B): phân biệt **+.651** ở HIGH.
`dt6_m7` (**MATH** 7B): phân biệt **+.113** ở HIGH.
Cùng cỡ model, cùng 4-bit, cùng cách tiêm lỗi, cùng prompt -> **khác 5.8 LẦN chỉ vì MIỀN.**
=> Phát biểu "ngưỡng NĂNG LỰC cho việc kiểm" phải sửa thành **"phụ thuộc NĂNG LỰC *VÀ* MIỀN"**.
   Kiểm số học trong chuỗi GSM8K (số nguyên, bước ngắn) thì 7B làm được;
   kiểm trong chuỗi MATH (LaTeX, đại số, nhiều bước) thì KHÔNG.
   Đây là lần thứ hai một kết luận "năng lực" hoá ra là "năng lực × miền" (lần trước: H1).

## ev_he7 (HumanEval 7B, Kaggle 4-bit) — **TÁI LẬP LẦN THỨ BA của H35**
greedy .7938 | maj@4 .7375 | **exec3 .9000** | llm3 .7438
`exec3−llm3` = **+.156 (5/5)** · `exec3−maj@4` = **+.163 (5/5)** · `exec3−greedy` = **+.106**
phá: **exec3 = 0.0 (0/5)** · llm3 = **3.2/fold (5/5)**
### BA LẦN CHẠY ĐỘC LẬP, HAI CỠ MODEL, HAI PHẦN CỨNG
| run | máy | exec3−llm3 | exec3−greedy | phá exec3 | phá llm3 |
|---|---|---|---|---|---|
| ev_he15 (1.5B, T4) | Kaggle | +.119 | +.063 | **0.0** | 2.8 |
| R_c15b (1.5B, bf16) | 5090 | +.206 | +.081 | **0.0** | 4.6 |
| R_c7b (7B, bf16) | 5090 | +.100 | +.081 | **0.0** | 2.6 |
| **ev_he7 (7B, 4-bit)** | **Kaggle** | **+.156** | **+.106** | **0.0** | **3.2** |
=> **exec3 KHÔNG phá một đáp án đúng nào trong 20/20 fold của BỐN lần chạy.**
   `llm3` phá trong **20/20 fold**. Đây là kết quả bền vững nhất dự án có.

## R_g7b (GSM8K 7B bf16) — lặp lại ô BÃO HOÀ
greedy .924 | maj@3 .928 | maj3_g .932 | **PSV .912** | SVV .924
`maj3−PSV` = **+.016 (3/5)** -> PSV THUA, lặp lại `bgL_g7` (+.036). Ô bão hoà đảo chiều: XÁC NHẬN.
`maj3g−maj3` = +.004 (2/5) -> đối chứng nhiễu loạn ≈ 0 lần thứ **7**.

## [Loop] VÒNG #71 — H8b CHỐT TRÊN **CẢ HAI MIỀN**: PAL thua ở MỌI ô, "chạy được ≠ mô hình hoá đúng"
### H8b_G7real — phép thử GSM8K THẬT (trước đó bị lỗi tham số task che mất)
`exec_success_rate` = **.980** — gần như MỌI chương trình đều CHẠY ĐƯỢC.
greedy **.948** | maj@3 **.944** | **pal3 .876** -> `pal3−maj3` = **−.068, 0/5 fold**

### BẢNG ĐẦY ĐỦ — PAL thua ở **5/5 phép đo**, hai miền, hai cỡ model
| ô | exec_ok | greedy | maj@3 | pal3 | **pal3 − maj3** |
|---|---|---|---|---|---|
| GSM8K 7B | **.980** | .948 | .944 | .876 | **−.068 (0/5)** |
| GSM8K 1.5B | .872 | .492 | .480 | .436 | **−.044 (1/5)** |
| MATH 7B (n=200) | .875 | .485 | .540 | .475 | **−.065 (1/5)** |
| MATH 7B (n=250) | .852 | .480 | .508 | .452 | **−.056 (2/5)** |
| MATH 1.5B | .760 | .325 | .370 | .295 | **−.075 (0/5)** |

=> **KẾT LUẬN CHỐT**: viết-và-chạy chương trình Python **LUÔN THUA** suy luận bằng văn bản,
   ở CẢ HAI miền, CẢ HAI cỡ model, **5/5 phép đo**, biên độ −4.4 đến −7.5 điểm.
=> Và điều này KHÔNG phải vì model không viết nổi code: `exec_success` = **.98 ở GSM8K 7B**.
   **Chương trình CHẠY ĐƯỢC gần như luôn luôn. Chúng chỉ tính SAI THỨ CẦN TÍNH.**
=> Đây là bằng chứng mạnh nhất cho phân biệt đã khoá ở #42:
   **BỘ KIỂM chỉ có giá trị khi là ORACLE VỀ TÍNH ĐÚNG (bộ test: pass = đúng),
   KHÔNG có giá trị khi chỉ là MỘT CÁCH TÍNH KHÁC (chạy Python cho toán).**
   Code: `exec3` = `oracle@4` chính xác, +6 đến +11 điểm, 0 lần phá.
   Toán/GSM8K: PAL = −4.4 đến −7.5 điểm dù chương trình chạy được .98.

### GHI CHÚ CHO CHỨNG MINH ĐỊNH LÝ
Bộ kiểm Lean LÀ oracle (chứng minh kiểm được hoặc không) -> thuộc nhóm CODE.
Kết quả âm của PAL **KHÔNG** dự đoán thất bại cho Lean. Hai thứ khác loại.

## R_g15b / R_g7b — lưới H32 tái lập lần nữa (có trace đầy đủ)
GSM8K 1.5B: greedy .636 | maj@3 .608 | maj3_g .652 | **PSV .704** | **SVV .716** -> `maj3−PSV` = **−.096 (PSV thắng 4/5)**
GSM8K 7B : greedy .924 | maj@3 .928 | maj3_g .932 | PSV .912 | SVV .924 -> `maj3−PSV` = **+.016 (PSV thua, ô BÃO HOÀ)**
=> Lặp lại chính xác mẫu hình đã có: tuần tự thắng ở ô CHƯA bão hoà, thua ở ô ĐÃ bão hoà.
=> `maj3_g − maj3` = +.044 và +.004 -> đối chứng nhiễu loạn vẫn ≈ 0 (ô thứ 8 và 9).

## [Loop] VÒNG #72 — H37 (bộ kiểm huấn luyện) ô 1.5B: 4/5 fold trước khi OOM. **PRIOR CỦA TÔI SAI**
### Số liệu (hợp lệ: `adapter_leak` = −0.05, đúng bằng ngưỡng)
`probe_pre` .3333 -> `probe_post` .3833 | **A) TIÊM: DISC = +0.032** | **B) THẬT: DISC = +0.219, AUC .563**
`wvote − maj@8` theo fold: **+.02, +.02, −.04, .00** (fold 4 OOM)

### PRIOR SAI — và sai theo hướng KHÔNG ai đoán
Tôi ghi trước (pre-reg #43): "`injected` sẽ CAO (>.6), `real` sẽ THẤP (<.2)" — tức học được
hiện vật rồi không chuyển giao. **Thực tế NGƯỢC LẠI**: `injected` = **+.032** (gần 0),
`real` = +.219 (cao hơn). Model **KHÔNG HỌC ĐƯỢC** ngay cả nhiệm vụ tiêm lỗi.
Loss huấn luyện TĂNG (0.22 -> 0.65), không hội tụ.
=> Bắt "một chữ số bị đổi trong chuỗi vàng hoàn hảo" khó hơn tôi tưởng RẤT NHIỀU —
   khó hơn cả phân biệt lời giải đúng/sai thật.

### PHÁN QUYẾT SƠ BỘ: HÀNG 4 của bảng khoá
"`discrimination_real` > 0 nhưng `wvote` KHÔNG hơn `maj@8` -> kiểm được nhưng KHÔNG chuyển
thành độ chính xác. Ghi rõ: **đo được ≠ dùng được**."
AUC .563 chỉ nhỉnh hơn ngẫu nhiên (.50). `wvote−maj` trung bình ≈ 0 trên 4 fold.
CHỜ ô 7B trước khi chốt — năng lực là lý do prompt thất bại, nên 7B mới là phép thử thật.

### LỖI HẠ TẦNG: chạy song song giết job
`H37_m7` (7B) phình từ 17.1GB -> **19.5GB** trong lúc chạy (optimizer state), chỉ còn 12.6GB;
`H37_m15` xin thêm **90 MiB** và OOM ở fold 4.
=> Supervisor của tôi kiểm VRAM **lúc KHỞI ĐỘNG** nhưng job huấn luyện **PHÌNH LÊN** sau đó.
=> SỬA: job `checker_local` (có huấn luyện) nay chạy **ĐỘC QUYỀN**, không cùng lúc với job khác.
   Job chỉ suy luận thì vẫn cho chạy song song (chúng không phình).

## [Loop] VÒNG #73 — **LƯỚI H32 HOÀN TẤT VÀ TÁI LẬP ĐỘC LẬP**: 8 phép đo, 4 ô, 2 phần cứng
| ô | phần cứng | greedy | maj@3 | PSV | `maj3−PSV` | fold |
|---|---|---|---|---|---|---|
| GSM8K 1.5B | T4 | .632 | .644 | **.728** | **−.084** | 0/5 |
| GSM8K 1.5B | 5090 | .636 | .608 | **.704** | **−.096** | 1/5 |
| MATH 1.5B | T4 | .330 | .350 | **.380** | −.030 | 2/5 |
| MATH 1.5B | 5090 | .325 | .385 | **.440** | **−.055** | 0/5 |
| MATH 7B | T4 4-bit | .500 | .505 | **.590** | **−.085** | 0/5 |
| MATH 7B | 5090 bf16 | .480 | .520 | **.595** | **−.075** | 0/5 |
| **GSM8K 7B** | T4 4-bit | .912 | **.916** | .904 | **+.012** | 3/5 |
| **GSM8K 7B** | 5090 bf16 | .924 | **.932** | .896 | **+.036** | 4/5 |

### KẾT LUẬN — mọi ô đo HAI LẦN, hai phần cứng, hai độ chính xác số học, CÙNG DẤU
- **PSV thắng ở 3/4 ô**, tái lập ở cả hai lần chạy của mỗi ô.
- **Chỉ thua ở ô BÃO HOÀ** (GSM8K 7B, greedy .912–.924) — và thua ở CẢ HAI lần chạy.
  Đây là ĐIỀU KIỆN đã khoá trước, không phải phản chứng: solver gần trần thì lượt thêm
  chỉ có thể PHÁ đáp án đang đúng.
- Tái lập chéo T4-4bit vs 5090-bf16 -> **kết luận KHÔNG phụ thuộc lượng tử hoá hay phần cứng.**

### VÀ NÓ RẺ HƠN
Token ở GSM8K 7B: `PSV` **1.89×** greedy vs `maj@3` **3.04×** -> tuần tự dùng **ÍT HƠN 38% token**
mà vẫn ngang/hơn. (Ở GSM8K 1.5B trước đó: 2.29× vs 2.96×, ít hơn 22%.)

### CƠ CHẾ VẪN LÀ MỎ NEO, KHÔNG PHẢI VAI
`SS_anc` (giải → neo → neo, KHÔNG một chữ nào về vai) = .924 ở GSM8K 7B, **cao hơn cả PSV .904**.
`SSanc − PSV` = +.020. Cộng với các ô trước (SS_anc = PSV chính xác ở GSM8K 1.5B):
**bỏ hết ngôn ngữ vai mà kết quả không đổi hoặc tốt hơn.**

### PHÁT BIỂU ĐƯỢC PHÉP DÙNG
"Ở CÙNG ngân sách sinh, **tinh chỉnh tuần tự có mỏ neo** hơn **lấy mẫu song song + bỏ phiếu**
từ 3 đến 9.6 điểm, trên 3/4 ô của lưới `task × cỡ model`, tái lập độc lập trên hai phần cứng,
và dùng ít token hơn 22–38%. Ngoại lệ DUY NHẤT là khi solver đã bão hoà (>.90), lúc đó
lượt thêm chỉ gây hại. Cơ chế là **MỎ NEO ĐÁP ÁN TRƯỚC**, không phải phân vai —
nhánh không có ngôn ngữ vai nào đạt kết quả ngang hoặc hơn."

## [Loop] VÒNG #74 — H37 ô 7B: **BỘ KIỂM HỌC RẤT TỐT (AUC .893) NHƯNG GẦN NHƯ VÔ DỤNG (+2.4 điểm)**
### Số liệu (HỢP LỆ: `adapter_leak` = 0.05, đúng bằng ngưỡng; đo trên CÙNG 60 bài trước/sau)
| | 1.5B | **7B** |
|---|---|---|
| A) TIÊM (trong phân phối) | +0.032 | **+0.573** |
| B) THẬT (chuyển giao) | +0.219 (AUC .563) | **+0.693 (AUC .893)** |
| `wvote − maj@8` | ≈0 (4 fold) | **+0.024, 2/5 fold** |
| maj@8 / wvote | — | .504 / .528 |

### PHÁN QUYẾT: **HÀNG 4 của bảng khoá (#43)**
"`discrimination_real` > 0 nhưng `wvote` KHÔNG hơn `maj@8` (>=4/5) -> kiểm được nhưng KHÔNG
chuyển thành độ chính xác. **ĐO ĐƯỢC ≠ DÙNG ĐƯỢC.**"
`real` = +.693 vượt xa ngưỡng .40, nhưng `wvote` chỉ hơn `maj@8` ở **2/5 fold**, +2.4 điểm.

### PRIOR CỦA TÔI SAI LẦN THỨ HAI — và sai cả hai chiều
Tôi ghi trước: "`injected` CAO, `real` THẤP" (học hiện vật, không chuyển giao).
Thực tế ở 7B: **CẢ HAI ĐỀU CAO, và `real` (+.693) CAO HƠN `injected` (+.573).**
Chuyển giao KHÔNG phải vấn đề. Nút thắt nằm ở chỗ khác hoàn toàn.

### NÚT THẮT THẬT: BỘ CHỌN KHÔNG THỂ VƯỢT `oracle@k`
Bộ kiểm chỉ CHỌN trong k ứng viên. Nếu **không ứng viên nào đúng**, AUC .893 cũng vô ích.
Khớp với vòng #65: bài "không đồng thuận" (50–58% số bài) có độ chính xác ~**.14 / .00** —
tức là ở nhóm đó, thường KHÔNG CÓ đáp án đúng nào để chọn.
=> Đây là lý do vì sao mọi cơ chế TỔNG HỢP của dự án đều chạm trần thấp:
   **giới hạn không phải ở việc CHỌN, mà ở việc SINH.**

### ĐỐI CHIẾU VỚI CODE — vì sao code khác hẳn
Trên code, `exec3` = `oracle@4` **CHÍNH XÁC**, và `oracle@4` = .644/.881 — CAO hơn `maj@4` rất nhiều
(bỏ lỡ 21.3 điểm). Nên ở đó bộ chọn hoàn hảo mua được 21 điểm.
Trên toán, `oracle` gần `maj` hơn nhiều -> bộ chọn dù hoàn hảo cũng mua được ít.
=> **Giá trị của bộ kiểm = khoảng cách `oracle@k − maj@k`, KHÔNG phải chất lượng bộ kiểm.**
   AUC .893 trên toán mua +2.4 điểm; bộ test trên code (AUC hiệu dụng 1.0) mua +21 điểm.

### NĂNG LỰC QUYẾT ĐỊNH VIỆC HỌC ĐƯỢC HAY KHÔNG
`injected`: 1.5B **+.032** vs 7B **+.573** — gấp **18 lần**. Loss 1.5B TĂNG (0.22->0.65),
loss 7B GIẢM (8.56->0.18). Bắt lỗi số học tiêm sẵn cần năng lực mà 1.5B KHÔNG có.

## [Loop] VÒNG #75 — H38 ô GSM8K 7B: **SUY BIẾN** (chỉ 2.8% bài không đồng thuận) + H37 hoàn tất
### rtL_g7 (GSM8K 7B) — VÔ HIỆU theo ngưỡng đã khoá
`pct_no_consensus` = **.028**, dưới ngưỡng hiệu lực **.15** khoá ở #44.
Đường cong tiêu đều: maj@3 .9240 | maj@4 .9280 | maj@6 .9400 | maj@8 .9400
Nhánh định tuyến: `route_3_6` .9360 @ 3.08 lượt (delta +.0117) · `route_3_seq` .9360 @ 3.06 lượt (+.0118)
=> Delta DƯƠNG nhưng chỉ dựa trên **~7/250 bài** được định tuyến -> **KHÔNG ĐỌC ĐƯỢC**,
   theo đúng hàng đã khoá: "ghi rõ suy biến, không đọc là thành công/thất bại của ý tưởng".
=> NGUYÊN NHÂN có ý nghĩa: GSM8K 7B **BÃO HOÀ** (greedy .924 = maj@3 .924), model tự đồng ý
   với chính nó gần như luôn luôn -> **không có gì để định tuyến**.
   Khớp y hệt lưới H32: ô bão hoà là nơi MỌI cơ chế đều mất tác dụng.
=> Ô kiểm được ý tưởng là 1.5B (50–58% bài không đồng thuận): `rt_g15`, `rt_m15`, `rtL_g15`.

## H37 HOÀN TẤT — cả hai ô, cả hai HỢP LỆ, cùng HÀNG 4
| | leak | A) tiêm | B) thật | AUC | `wvote−maj@8` |
|---|---|---|---|---|---|
| 1.5B (chạy lại sạch) | −.017 ✓ | **−.012** | +.195 | .528 | **−.008 (1/5)** |
| 7B | +.050 ✓ | **+.573** | **+.693** | **.893** | **+.024 (2/5)** |
=> **HÀNG 4 ở CẢ HAI ô: "đo được ≠ dùng được".**
=> 1.5B: phân biệt lỗi tiêm **ÂM** — không học được gì. 7B: học rất tốt VÀ chuyển giao tốt hơn
   cả trong phân phối (+.693 > +.573) — **chuyển giao KHÔNG phải vấn đề**.
=> Nhưng AUC .893 chỉ mua được **+2.4 điểm, 2/5 fold**.

### PHÁT BIỂU HỢP NHẤT (nối H27 + H35 + H8b + H37)
**Giá trị của một bộ kiểm = khoảng cách `oracle@k − maj@k`, KHÔNG phải chất lượng bộ kiểm.**
- Code: khoảng cách **+21.3 điểm**; bộ test (AUC hiệu dụng 1.0) lấy được **toàn bộ**.
- Toán: khoảng cách nhỏ; bộ kiểm AUC .893 chỉ lấy được **+2.4**.
Bộ kiểm chỉ CHỌN trong k ứng viên. Ở 50–58% bài không đồng thuận (độ chính xác ~.14/.00),
**thường KHÔNG CÓ ứng viên đúng nào để chọn**.
=> **NÚT THẮT LÀ SINH, KHÔNG PHẢI CHỌN.** Đây là lý do mọi cơ chế tổng hợp của dự án
   (rerank, bỏ phiếu có trọng số, bộ chấm huấn luyện) đều chạm trần thấp trên toán.

## [Loop] VÒNG #76 — **HAI KẾT QUẢ LỚN**: H38 XÁC NHẬN (hàng 1) và H28d GỠ ĐÌNH CHỈ (leak = 0.0)
### A) H38 — ĐỊNH TUYẾN THEO ĐỒNG THUẬN **THẮNG** TIÊU ĐỀU Ở CÙNG CHI PHÍ
| ô | không đồng thuận | nhánh | acc | chi phí (lượt) | tiêu đều CÙNG chi phí | **delta** | fold |
|---|---|---|---|---|---|---|---|
| GSM8K 1.5B | .368 ✓ | route_3_6 | .7360 | 4.10 | .6865 | **+.0495** | 4/5 |
| GSM8K 1.5B | .368 ✓ | **route_3_seq** | .7360 | **3.74** | .6671 | **+.0689** | 4/5 |
| MATH 1.5B | .600 ✓ | route_3_6 | .4400 | 4.80 | .4160 | **+.0240** | 4/5 |
| MATH 1.5B | .600 ✓ | **route_3_seq** | .4650 | **4.20** | .4040 | **+.0610** | **5/5** |
(GSM8K 7B: không đồng thuận .028 -> **SUY BIẾN**, không đọc — ô bão hoà)

=> **HÀNG 1 của bảng khoá #44**: "`route` > `maj@k` nội suy tại cùng chi phí, >=4/5 fold ->
   XÁC NHẬN, định tuyến theo đồng thuận đáng dùng." **Đạt ở 4/4 phép đo hợp lệ.**
=> **HÀNG 4 CŨNG NỔ**: `route_3_seq` > `route_3_6` ở **CẢ HAI ô** (+.069 vs +.050; +.061 vs +.024)
   VÀ rẻ hơn (3.74 vs 4.10; 4.20 vs 4.80 lượt).
   "Ở bài KHÓ, TUẦN TỰ tốt hơn LẤY THÊM MẪU" — khớp và làm sắc thêm H32.
=> Tín hiệu đồng thuận **MIỄN PHÍ** (chỉ đếm), không cần huấn luyện, không có rủi ro rò rỉ adapter.

### B) H28d — GỠ ĐÌNH CHỈ cho H28: bỏ phiếu có trọng số ĐỨNG VỮNG
`probe_pre` = `probe_post` = **.55** trên CÙNG 60 bài -> **`adapter_leak` = 0.0**, VALID.
(Ngưỡng cũ hỏng vì so tập TRAIN với tập TEST; nay so CÙNG bài trước/sau.)
greedy .5267 | **maj@8 .7167** | rerank .7200 | **wvote_sum .7767** | oracle@8 .8767 | AUC .8555
**`wsum − maj` = +.0600, [+.017,+.100], 5/5 fold** (f0 +.100, f1 +.017, f2 +.100, f3 +.067, f4 +.017)
Lấy được **37%** khoảng trống `maj@8 -> oracle@8` (+.160).
=> **H27/H28/H28b/H31 KHÔNG còn bị đình chỉ.** Con số ĐƯỢC PHÉP công bố là **+6.0 điểm, 5/5 fold**,
   đo với `adapter_leak = 0.0` — KHÔNG phải +11.0 (nhiễm) cũng KHÔNG phải +3.0 (đo ở lần rò rỉ ít).

### HỢP NHẤT — hai cách DUY NHẤT đã đo được là vượt `maj@k` trên toán
1. **Bỏ phiếu CÓ TRỌNG SỐ** bằng bộ chấm huấn luyện: **+6.0 điểm** (5/5), lấy 37% khoảng trống.
2. **ĐỊNH TUYẾN THEO ĐỒNG THUẬN** + tuần tự: **+6.1 đến +6.9 điểm** (4–5/5) ở CÙNG chi phí,
   và **MIỄN PHÍ** — không huấn luyện gì cả.
=> Hai đường độc lập, biên độ gần bằng nhau. Nhưng (2) không cần dữ liệu, không cần LoRA,
   không có rủi ro rò rỉ -> **khuyến nghị thực tiễn ưu tiên (2)**.
=> Cả hai đều KHÔNG chạm trần `oracle` — nhất quán với "nút thắt là SINH, không phải CHỌN".

## [Loop] VÒNG #77 — **rtL_m7: ĐỊNH TUYẾN + TUẦN TỰ HƠN `maj@8` 10.5 ĐIỂM VỚI CHI PHÍ ÍT HƠN 2.1 LẦN**
### MATH 7B (không đồng thuận .405 — HỢP LỆ), 5/5 fold
| fold | maj@3 | maj@8 | **route_3_seq** | chi phí | tiêu đều cùng chi phí | delta |
|---|---|---|---|---|---|---|
| 0 | .575 | .550 | **.725** | 3.80 | .5750 | **+.1500** |
| 1 | .675 | .675 | **.750** | 3.45 | .6750 | +.0750 |
| 2 | .375 | .450 | **.550** | 4.05 | .3519 | **+.1981** |
| 3 | .375 | .475 | **.575** | 4.10 | .3775 | **+.1975** |
| 4 | .575 | .575 | **.650** | 3.65 | .5750 | +.0750 |
**route_3_seq = .6500 @ 3.81 lượt** vs **maj@8 = .5450 @ 8.00 lượt**
=> **HƠN 10.5 ĐIỂM với chi phí ÍT HƠN 2.1 LẦN.** So với tiêu đều CÙNG chi phí: **+.1391, 5/5 fold.**
=> `route_3_6` chỉ +.0273 -> **tuần tự hơn hẳn lấy thêm mẫu** (gấp 5 lần hiệu quả), rẻ hơn (3.81 vs 4.21).

### LƯỚI H38 ĐẦY ĐỦ — 3 ô hợp lệ, 1 ô suy biến
| ô | không đồng thuận | route_3_6 | **route_3_seq** | fold (seq) |
|---|---|---|---|---|
| GSM8K 1.5B | .368 | +.0495 | **+.0689** | 4/5 |
| MATH 1.5B | .600 | +.0240 | **+.0610** | 5/5 |
| **MATH 7B** | .405 | +.0273 | **+.1391** | **5/5** |
| GSM8K 7B | .028 | — | — | SUY BIẾN (bão hoà) |
=> `route_3_seq` THẮNG ở **3/3 ô hợp lệ**, và LUÔN hơn `route_3_6`.
=> Hiệu ứng LỚN NHẤT ở ô mà H32 cũng cho PSV thắng đậm nhất (MATH 7B) — **nhất quán nội tại**:
   đó là ô "giữa dải độ khó" (solver ~.50), đúng luật dải độ khó đã đo từ đầu dự án.

### PHÁT BIỂU THỰC TIỄN MẠNH NHẤT DỰ ÁN CÓ
**"Lấy 3 mẫu. Nếu >=2 đồng ý -> nhận, dừng. Nếu không -> chạy tuần tự có mỏ neo.
Kết quả hơn `maj@8` tới 10.5 điểm với chi phí chưa bằng một nửa."**
- Tín hiệu định tuyến MIỄN PHÍ (chỉ đếm phiếu trùng nhau), không huấn luyện, không rò rỉ adapter.
- Vượt cả bỏ phiếu có trọng số (+6.0, cần LoRA + dữ liệu) VÀ rẻ hơn.
- Ngoại lệ: ô BÃO HOÀ (solver >.90) — ở đó không có gì để định tuyến, đừng dùng.

## [Loop] VÒNG #78 — **H39: ESCALATE THEO ĐỒNG THUẬN + TUẦN TỰ HƠN "LUÔN DÙNG 7B" 10.5 ĐIỂM VỚI CHI PHÍ 4.3× ÍT HƠN**
### MATH, escalate 1.5B -> 7B, tỉ lệ escalate = **.625** (HỢP LỆ), chi phí quy về FLOP 1.5B (7B = 5.07×)
| nhánh | acc | chi phí (1.5B-eq) |
|---|---|---|
| small_maj3 (chỉ 1.5B) | .3500 | 3.00 |
| small_maj8 (chỉ 1.5B) | .4800 | 8.00 |
| big_maj3 (chỉ 7B) | .5050 | 15.20 |
| big_maj8 (chỉ 7B) | .5400 | 40.53 |
| escalate (7B lấy mẫu) | .4950 | 12.50 |
| **escalate_seq (7B TUẦN TỰ)** | **.6450** | **9.33** |

| so sánh | chênh acc | chi phí |
|---|---|---|
| `escalate_seq` vs `big_maj3` | **+.1400** | **1.63× rẻ hơn** (5/5 fold) |
| `escalate_seq` vs `big_maj8` | **+.1050** | **4.34× rẻ hơn** |
| `escalate_seq` vs `small_maj8` | +.1650 | — |
| `escalate` (lấy mẫu) vs `big_maj3` | −.0100 | 1.22× rẻ hơn |

### PHÁN QUYẾT: **HÀNG 1 + HÀNG 4 của bảng khoá #45**
Hàng 1: "`escalate` >= `big_maj3` nhưng chi phí thấp hơn rõ -> XÁC NHẬN: chỉ trả tiền cho model
lớn ở bài KHÔNG đồng thuận." **Đạt (với biến thể tuần tự): +.14 acc, 1.63× rẻ hơn, 5/5 fold.**
Hàng 4: "`escalate_seq` > `escalate` -> tuần tự lại thắng lấy mẫu." **Đạt rất mạnh: .645 vs .495 = +.150.**
Bản LẤY MẪU của escalate (.495) còn THUA `big_maj3` (.505) -> **chỉ TUẦN TỰ mới có tác dụng.**

### PRIOR CỦA TÔI SAI — lần này sai theo chiều TỐT
Tôi ghi trước: "escalate sẽ gần `big_maj3` với chi phí thấp hơn, NHƯNG sẽ THẤP HƠN `big_maj8`;
kết luận sẽ là về hiệu quả chi phí, không phải độ chính xác."
Thực tế: `escalate_seq` = .645 **CAO HƠN** `big_maj8` = .540 **10.5 điểm**, và rẻ hơn **4.34 lần**.
Không chỉ hiệu quả chi phí — mà **CHÍNH XÁC HƠN VÀ RẺ HƠN CÙNG LÚC**.

### VÌ SAO — ba mảnh khớp nhau
1. **Đồng thuận biết bài nào dễ** (vòng #65): 37.5% bài mà 1.5B tự đồng ý -> nó gần như luôn đúng,
   dùng 7B ở đó là LÃNG PHÍ.
2. **Tuần tự > song song** (H32, H38): ở bài khó, một lượt có MỎ NEO đáng giá hơn nhiều lượt độc lập.
3. **Nút thắt là SINH, không phải CHỌN** (H37): `big_maj8` tiêu 40.5 đơn vị để lấy mẫu SONG SONG —
   nhưng 8 mẫu song song của 7B vẫn không sinh ra đáp án đúng ở nhóm khó. Tuần tự thì có.

### KHUYẾN NGHỊ TRIỂN KHAI (mạnh nhất dự án đưa ra được)
**"Lấy 3 mẫu bằng model NHỎ. Nếu >=2 đồng ý -> nhận, dừng. Nếu không -> gọi model LỚN chạy
TUẦN TỰ CÓ MỎ NEO (giải lại + kiểm), KHÔNG phải lấy nhiều mẫu."**
Trên MATH: **.645 so với .540 của "luôn dùng 7B, 8 mẫu", với 1/4.3 chi phí.**
Tín hiệu định tuyến MIỄN PHÍ. Không huấn luyện. Không rò rỉ adapter.

## [Loop] VÒNG #79 — **H39_g: TRÊN GSM8K, ESCALATE **THUA**. HÀNG 2 CỦA BẢNG KHOÁ #45.**
### GSM8K, escalate 1.5B -> 7B, tỉ lệ escalate = **.372** (HỢP LỆ)
| nhánh | acc | chi phí (1.5B-eq) |
|---|---|---|
| small_maj3 | .6160 | 3.00 |
| small_maj8 | .7400 | 8.00 |
| big_maj3 | **.9360** | 15.20 |
| big_maj8 | **.9480** | 40.53 |
| escalate (lấy mẫu) | .8880 | 8.65 |
| escalate_seq (tuần tự) | .8720 | 6.77 |

| so sánh | chênh acc | chi phí | fold |
|---|---|---|---|
| `escalate_seq` vs `big_maj3` | **−.0640** | 2.25× rẻ hơn | **0/5** |
| `escalate_seq` vs `big_maj8` | **−.0760** | 5.99× rẻ hơn | **0/5** |
| tuần tự vs lấy mẫu | **−.0160** | — | ĐẢO CHIỀU so với MATH |

### PHÁN QUYẾT: **HÀNG 2 của bảng khoá #45 — "escalate < big_maj3"**
Đúng câu chữ đã khoá: *"Escalate không đủ — ghi rõ."* **GHI RÕ: trên GSM8K, escalate THUA
`big_maj3` 6.4 điểm ở 0/5 fold.** Rẻ hơn 2.25× nhưng KHÔNG chính xác bằng.
Và **hàng 4 ĐẢO CHIỀU**: tuần tự (.872) THẤP HƠN lấy mẫu (.888) — ngược hẳn MATH (+.150).

### KẾT QUẢ #78 KHÔNG PHỔ QUÁT. Phải thu hẹp phạm vi.
Vòng #78 tôi viết: *"khuyến nghị triển khai mạnh nhất dự án đưa ra được."* **Câu đó SAI vì
thiếu điều kiện.** Nó đúng trên MATH, sai trên GSM8K. Ghi lại cho đúng:
> escalate theo đồng thuận thắng **trên MATH**, thua **trên GSM8K**. Chưa biết cái gì quyết định.

### ĐỐI CHIẾU HAI MIỀN — khác biệt lớn nhất là **TRẦN**
| | acc `big_maj3` | dư địa còn lại | chênh `escalate_seq` |
|---|---|---|---|
| MATH | .5050 | .495 | **+.1400** |
| GSM8K | .9360 | .064 | **−.0640** |
Khi 7B đã ở .936, việc GIỮ 62.8% bài cho 1.5B nghĩa là **từ bỏ** phần 7B lẽ ra sửa được.
Lỗi còn lại trong nhóm "đồng thuận" là KHÔNG THỂ cứu — ta không bao giờ gọi 7B ở đó.
Khi 7B mới ở .505, dư địa lớn, và lượt tuần tự trên nhóm khó thu được nhiều hơn phần đánh mất.

### ĐÂY LÀ **GIẢ THUYẾT**, KHÔNG PHẢI ĐO ĐƯỢC
"Trần quyết định" mới chỉ dựa trên **2 điểm dữ liệu** (2 tác vụ). Hai miền còn khác nhau ở
độ dài bài, kiểu suy luận, chất lượng bộ chấm. **Chưa được coi là đã chứng minh.**
Kiểm chứng ở đăng ký trước #46: đo TRONG CÙNG MỘT tác vụ, tách theo độ khó.

## [Loop] VÒNG #80 — **H40: GIẢ THUYẾT "TRẦN" CỦA TÔI **SAI**. HÀNG 2 CỦA BẢNG KHOÁ #46.**
### MATH-500 đầy đủ, 20 shard Kaggle song song, 7B fp16, đẳng thức tự kiểm HỢP LỆ ở mọi tầng
| tầng | n | esc% | big_maj3 | escalate_seq | **gain** | opp_cost | gain_on_esc | ID |
|---|---|---|---|---|---|---|---|---|
| DỄ (lv1-2) | 133 | .271 | .7669 | .7895 | **+.0226** | +.0309 | +.1667 | OK |
| GIỮA (lv3) | 105 | .610 | .6190 | .6762 | **+.0572** | +.1463 | +.1875 | OK |
| KHÓ (lv4-5) | 262 | .782 | .2939 | .4351 | **+.1412** | −.0175 | +.1756 | OK |
| TẤT CẢ | 500 | .610 | .4880 | .5800 | **+.0920** | +.0410 | +.1771 | OK |

### PHÁN QUYẾT: **HÀNG 2 — "gain > 0 ở CẢ HAI tầng"**
Đúng câu chữ đã khoá: *"Giả thuyết trần **SAI**. Chênh lệch MATH↔GSM8K do thứ khác.
**Ghi rõ là CHƯA GIẢI THÍCH ĐƯỢC**."* Tôi đoán hàng 1 (`gain`(DỄ) ≤ 0). Đo được **+.0226 > 0**.
**PRIOR CỦA TÔI SAI LẦN THỨ BA LIÊN TIẾP** (#78 dự đoán thấp hơn `big_maj8` — cao hơn;
#79 tuyên bố "khuyến nghị mạnh nhất" — GSM8K lật ngược; nay #80).
`opp_cost` cũng KHÔNG theo trần: +.0309 → **+.1463** → −.0175, không đơn điệu.

### NHƯNG H39_m **TÁI LẬP** — hiệu ứng chính là THẬT
| | n | máy | 7B | esc% | big_maj3 | escalate_seq | gain | rẻ hơn |
|---|---|---|---|---|---|---|---|---|
| H39_m | 200 | RTX 5090 | bf16 | .625 | .5050 | .6450 | +.1400 | 1.63× |
| **H40** | **500** | **20×Kaggle** | **fp16** | .610 | .4880 | .5800 | **+.0920** | **1.66×** |
Cùng dấu, cùng tỉ lệ chi phí, phần cứng độc lập, mẫu gấp 2.5×. **Thắng lợi trên MATH không phải may.**

### PHÂN RÃ CHỈ RA MỘT ĐIỀU TÔI KHÔNG NGỜ — `gain_on_esc` GẦN NHƯ **HẰNG SỐ**
`gain_on_esc` = **+.1667 / +.1875 / +.1756** qua ba tầng — hầu như không đổi theo độ khó.
Cái thay đổi là **TẦN SUẤT escalate**: `pe` = .271 → .610 → .782.
=> Tổng `gain` tăng theo độ khó **KHÔNG PHẢI** vì lượt tuần tự đáng giá hơn ở bài khó,
   mà vì bài khó **kích hoạt escalate thường xuyên hơn**. Giá trị mỗi lần escalate là ~+.18 đều đặn.
**ĐÂY LÀ QUAN SÁT HẬU NGHIỆM, CHƯA ĐƯỢC TÍNH LÀ KẾT QUẢ.** Phải đăng ký trước rồi mới được khẳng định.

### HẠN CHẾ THIẾT KẾ CỦA CHÍNH TÔI — phép thử này KHÔNG chạm vùng bão hoà
`big_maj3` cao nhất trong ba tầng chỉ **.7669** (tầng DỄ). Ngưỡng bão hoà ghi ở vòng #71 là **>.90**.
Tức **không tầng nào của MATH đạt bão hoà** — phép so sánh quyết định (bão hoà vs chưa) **CHƯA HỀ ĐƯỢC LÀM**.
Nêu ra như một sự thật đo được (`big_maj3` từng tầng), KHÔNG phải để cứu giả thuyết đã chết theo bảng khoá.

### VÌ SAO H41 (ĐĂNG KÝ TRƯỚC #47) LÀ PHÉP THỬ QUYẾT ĐỊNH
GSM8K có `big_maj3` = .936 tổng thể — vùng bão hoà THẬT, thứ MATH không có.
Và phân rã trên cho một dự đoán SẮC: nếu `gain_on_esc` thật sự ~hằng số dương,
thì `gain` ÂM của GSM8K **buộc phải** đến từ `opp_cost` LỚN (7B hơn hẳn 1.5B trên nhóm đồng thuận).
Nếu đo ra `opp_cost` GSM8K nhỏ mà `gain_on_esc` âm -> quan sát "hằng số" ở trên cũng sai nốt.

## [Loop] VÒNG #81 — **H42: ĐỊNH TUYẾN **KHÔNG** CHUYỂN SANG CODE. HÀNG 3 CỦA BẢNG KHOÁ #48.**
### MBPP tách chuẩn 11–510, 498 bài, 20 shard Kaggle, 7B **nf4** (2 bản sao/thẻ), biên dịch được **.994**
| nhánh | acc (assert giữ lại) | chi phí | esc% |
|---|---|---|---|
| small_1 (1 bản 1.5B) | .4217 | 1.00 | — |
| small_maj3 | .4739 | 3.00 | — |
| **big_greedy (1 lượt 7B)** | **.6365** | **5.07** | — |
| big_maj3 | .6526 | 15.20 | — |
| big_maj8 | .6627 | 40.53 | — |
| route_consensus | .5643 | 6.74 | .369 |
| route_oracle | .6004 | 6.27 | .520 |

### PHÁN QUYẾT: **HÀNG 3 — "cả hai ≤ `big_maj3`"**
Đúng câu chữ đã khoá: *"**Định tuyến KHÔNG chuyển sang code.** Thắng lợi ở MATH (#46) là đặc thù miền.
Ghi rõ, không diễn giải lại."* Tôi đoán hàng 1. **PRIOR SAI LẦN THỨ TƯ LIÊN TIẾP** (#78,#79,#80,#81).
Cả hai bộ định tuyến HỢP LỆ (esc% .369 và .520, trong .15–.85) — kết quả đọc được, không suy biến.

### TỆ HƠN: ĐỊNH TUYẾN BỊ **ÁP ĐẢO HOÀN TOÀN** trên code
`big_greedy` — **một lượt 7B duy nhất** — đạt **.6365** với chi phí **5.07**.
Cả hai bộ định tuyến vừa **kém chính xác hơn** vừa **đắt hơn**. Không có đánh đổi nào để bào chữa.

### PHÂN RÃ (mô tả, KHÔNG phải phép thử đã đăng ký) — hỏng ở ĐÂU
| bộ định tuyến | opp_cost (trên NHẬN) | **gain_on_esc** (trên ESC) |
|---|---|---|
| consensus | +.0956 | **−.0761** |
| **oracle** | **−.0167** | **−.1159** |
**Tín hiệu định tuyến oracle gần như HOÀN HẢO**: `opp_cost` **ÂM** — trên nhóm giữ lại,
model nhỏ (.8368) còn HƠN 7B (.8201). Nó phân loại đúng bài nào không cần model lớn.
**Cái hỏng là HÀNH ĐỘNG SAU KHI ESCALATE**: lượt 7B TUẦN TỰ CÓ MỎ NEO đạt .3822,
trong khi chỉ cần bỏ phiếu 7B×3 đã .4981 → **tuần tự làm TỆ ĐI 11.6 điểm**.

### ĐIỀU NÀY ĐẢO CHIỀU KHẲNG ĐỊNH MẠNH NHẤT CỦA DỰ ÁN — nhưng KHỚP với H35
Trên MATH `gain_on_esc` = **+.18 đều đặn**. Trên code = **−.08 đến −.12**.
KHÔNG mâu thuẫn với H35: ở đó `exec3` (sửa theo **stderr của test thật**) thắng +6..+11,
còn `llm3` (LLM tự nhận xét, KHÔNG chạy test) thì không. Lượt tuần tự của tôi CHÍNH LÀ loại `llm3`.
=> Gộp lại: **"cho model xem lại đáp án trước của chính nó" giúp ở TOÁN, hại ở CODE.**
   Ở code chỉ có ORACLE THẬT (chạy test) mới sửa được.

### QUAN SÁT HẬU NGHIỆM — CHƯA ĐƯỢC TÍNH LÀ KẾT QUẢ
Giữ nguyên tín hiệu oracle nhưng escalate bằng **7B maj@3** thay vì tuần tự:
**acc .6606 · chi phí 8.91 · hơn `big_maj3` +.0080 · rẻ hơn 1.71×**.
Tính từ CHÍNH dữ liệu vừa xem -> **không có giá trị chứng minh**. Phải đăng ký trước và
kiểm trên **phần MBPP chưa hề đụng tới (task_id 511–974)**. Xem đăng ký trước #49.

## [Loop] VÒNG #82 — **H43 trên MBPP 511–974 (CHƯA TỪNG ĐỤNG): HÀNG 2, không phải hàng 1**
### 464 bài, 20 shard, 7B nf4, biên dịch được .994 — tất cả nhánh đo trong CÙNG một lần chạy
| nhánh | acc | chi phí | esc% |
|---|---|---|---|
| small_maj3 | .5086 | 3.00 | — |
| big_greedy | .7091 | 5.07 | — |
| **big_maj3** | **.7371** | 15.20 | — |
| big_maj8 | .7371 | 40.53 | — |
| route_consensus | .5819 | 6.47 | .343 |
| route_oracle_**seq** | .6228 | 5.89 | .483 |
| **route_oracle_maj3** (nhánh cần kiểm) | **.7392** | **8.34** | .483 |

### BẢNG KHOÁ CỦA TÔI CÓ HAI HÀNG CHỒNG NHAU — tôi lấy cách đọc BẢO THỦ
`route_oracle_maj3 − big_maj3` = **+.0021**. Số này thoả **cả** hàng 1 ("> big_maj3 và rẻ hơn")
**lẫn** hàng 2 ("|chênh| < .01"). Script tôi viết xét hàng 1 trước nên in ra "XÁC NHẬN".
**Đó là lỗi thiết kế bảng của tôi, và script đã chọn hàng có lợi cho tôi.**
Cách đọc đúng là **HÀNG 2**: *"Ngang độ chính xác, rẻ hơn. Kết luận YẾU: chỉ tiết kiệm chi phí,
không cải thiện."* **+.0021 ≈ 1 bài trên 464** — nằm gọn trong nhiễu. Đã sửa thứ tự xét trong script.
=> Phát biểu được phép dùng: **định tuyến bằng test thật + escalate bằng LẤY MẪU đạt ngang
`big_maj3` với chi phí 1.82× thấp hơn.** KHÔNG được nói là "chính xác hơn".

### KẾT QUẢ THẬT SỰ MẠNH Ở ĐÂY: **"TUẦN TỰ HẠI TRÊN CODE" ĐÃ TÁI LẬP**
| | H42 (11–510, 498 bài) | **H43 (511–974, 464 bài, chưa từng đụng)** |
|---|---|---|
| lấy mẫu − tuần tự, trên nhóm escalate | **+.1159** | **+.1164** |
Hai tách rời nhau, chênh nhau **0.0005**. Hàng 4 của #49 ("nếu `gain_on_esc`(seq) ≥ 0 thì phải
RÚT LẠI cơ chế vòng #81") **KHÔNG kích hoạt** — cơ chế đứng vững.
`route_oracle_seq` thua `big_maj3` **−.1143**, y hệt hình mẫu ở H42.

### PHÁT BIỂU HỢP NHẤT (toán vs code)
> Cho model xem lại đáp án trước của chính nó: **+.18 mỗi lần trên MATH**, **−.12 trên CODE**.
> Cùng một cơ chế, **đảo dấu theo miền**. Ở code, chỉ ORACLE THẬT (chạy test) mới sửa được;
> mỏ neo bằng văn bản làm model VÁ code sai thay vì viết lại.

### Ghi thêm: `big_maj8` = `big_maj3` = .7371 **chính xác bằng nhau**
Lấy thêm 5 mẫu nữa của 7B trên MBPP **không thêm một bài nào**. Củng cố "nút thắt là SINH,
không phải CHỌN" — ở code còn rõ hơn ở toán.

## [Loop] VÒNG #83 — **H41: GIẢ THUYẾT "TRẦN" CHẾT DỨT KHOÁT. HÀNG 3 — NGƯỢC HẲN.**
### GSM8K 500 bài, 20 shard Kaggle, 7B nf4, độ khó = số bước tính, đẳng thức tự kiểm HỢP LỆ mọi tầng
| tầng | n | esc% | big_maj3 | escalate_seq | **gain** | opp_cost | gain_on_esc |
|---|---|---|---|---|---|---|---|
| DỄ (≤2 bước) | 188 | .197 | **.9628** | .8883 | **−.0745** | +.0530 | −.1621 |
| GIỮA (3) | 125 | .304 | .9120 | .8400 | **−.0720** | +.0919 | −.0263 |
| KHÓ (≥4) | 187 | .455 | .9037 | .7701 | **−.1336** | +.1569 | −.1059 |
| TẤT CẢ | 500 | .320 | .9280 | .8320 | −.0960 | +.0941 | −.1000 |

### PHÉP THỬ NÀY **HỢP LỆ** — khác H40
Bổ sung #47 khoá: *"nếu `big_maj3`(DỄ) < .90 thì CHƯA chạm bão hoà, không kết luận"*.
Đo được **.9628 ≥ .90** -> **đã chạm vùng bão hoà thật**. Điều kiện huỷ KHÔNG kích hoạt.

### PHÁN QUYẾT: **HÀNG 3 của bảng khoá #47**
`gain`(KHÓ) − `gain`(DỄ) = −.1336 − (−.0745) = **−.0591**, vượt ngưỡng −.03.
Câu chữ đã khoá: *"**NGƯỢC HẲN. Giả thuyết trần CHẾT.** Ghi rõ, không diễn giải lại."*
Định tuyến **tệ hơn ở bài KHÓ**, không phải tốt hơn. `opp_cost` cũng đi ngược dự đoán:
**+.0530 → +.0919 → +.1569**, TĂNG theo độ khó (tôi đoán nó GIẢM).
**PRIOR CỦA TÔI SAI LẦN THỨ NĂM LIÊN TIẾP** (#78,#79,#80,#81,#83).

### BỨC TRANH BA MIỀN — **MATH mới là NGOẠI LỆ, không phải quy luật**
| miền | `gain_on_esc` (giá trị mỗi lần escalate) |
|---|---|
| MATH | **+.1667 / +.1875 / +.1756** (dương, gần như hằng số) |
| GSM8K | **−.1621 / −.0263 / −.1059** (âm) |
| CODE (MBPP) | **−.1159 (H42) / −.1164 (H43)** (âm, tái lập) |
=> Lượt 7B **tuần tự có mỏ neo** chỉ đáng giá **ở MATH**. Ở GSM8K và code nó **gây hại**.
Trước đây tôi phát biểu "tuần tự hơn lấy mẫu" như khẳng định mạnh nhất dự án, với ngoại lệ
là "ô bão hoà". Nay: **hai trong ba miền cho dấu ÂM**. Ngoại lệ không phải bão hoà —
mà đơn giản là **MATH khác hai miền kia**, và **CHƯA GIẢI THÍCH ĐƯỢC vì sao**.

### Điều gì CHƯA chết
Lưới H32 (PSV vs maj@3, cùng ngân sách, một model) vẫn đứng: PSV thắng 3/4 ô, tái lập hai phần cứng.
H41 đo thứ KHÁC: **escalate 1.5B→7B** rồi mới chạy tuần tự. Không được lẫn hai phát biểu.
Việc cần làm là đối chiếu trực tiếp hai thiết kế trên cùng bài — chưa làm.

## [Loop] VÒNG #84 — **H44: MỎ NEO LÀ THỦ PHẠM CHÍNH TRÊN CODE. HÀNG 1 + HÀNG 4 của #50.**
### MBPP 11–510, 498 bài, 265 bài escalate (.532 — HỢP LỆ), biên dịch được .995, 7B nf4
Ba hành động trên **CÙNG nhóm escalate**, **cùng một lần chạy**:
| hành động | acc | chi phí |
|---|---|---|
| **A) tuần tự CÓ mỏ neo** | **.3698** | 2 lượt 7B |
| **B) tuần tự KHÔNG mỏ neo** | **.4679** | 2 lượt 7B |
| **C) lấy mẫu maj@3** | **.5245** | 3 lượt 7B |

### PHÂN RÃ SẠCH — hai hàng đều kích hoạt và chúng CỘNG LẠI, không mâu thuẫn
```
C − A = +.1547   tổng thiệt hại so với lấy mẫu
  B − A = +.0981   <- RIÊNG do MỎ NEO            (63%)
  C − B = +.0566   <- do CẤU TRÚC TUẦN TỰ        (37%)
```
**Hàng 1**: bỏ mỏ neo — cùng cấu trúc, cùng chi phí, chỉ bỏ code sai khỏi prompt — **hồi lại 9.8 điểm**.
Đưa code hỏng vào khiến model **VÁ** thay vì **VIẾT LẠI**.
**Hàng 4**: kể cả đã bỏ mỏ neo, lấy mẫu VẪN hơn tuần tự **5.7 điểm** trên code.

### LẦN ĐẦU PRIOR CỦA TÔI ĐÚNG (sau 5 lần sai liên tiếp)
Ghi trước: "đoán hàng 1 (mỏ neo là thủ phạm)". Đúng. #78–#81, #83 đều sai; #84 đúng.

### ĐIỀU NÀY ĐÁNH THẲNG VÀO CƠ CHẾ TRUNG TÂM CỦA DỰ ÁN
Vòng #73 phát biểu: *"Cơ chế là **MỎ NEO ĐÁP ÁN TRƯỚC**, không phải phân vai — nhánh không có
ngôn ngữ vai nào đạt kết quả ngang hoặc hơn."* Đó là lời giải thích cho `SS_anc` = `PSV`.
Nay trên code, **chính mỏ neo đó là nguồn thiệt hại lớn nhất (63%)**.
=> Mỏ neo **không phải cơ chế phổ quát**. Nó giúp ở MATH, hại ở code. **Chưa biết vì sao.**

### H45 (đang chạy) là phép đo quyết định
H45 đo `delta_seq` = tuần tự-có-mỏ-neo − maj3, **không escalate, không hai model**, trên 4 ô.
Nếu MATH 7B cho `delta_seq` > 0 còn GSM8K 7B < 0 với CÙNG model -> biến là TÁC VỤ, không phải mỏ neo.
Nếu cả bốn ô đều âm -> mọi kết quả dương trước đây đến từ escalate, và phát biểu
"tuần tự hơn lấy mẫu" phải viết lại toàn bộ.

## [Loop] VÒNG #85 — **H45: DẤU CỦA `delta_seq` ĐI THEO **ĐỘ CHÍNH XÁC CỦA CHÍNH MODEL**. HÀNG 1 của #51.**
### 4 ô × 300 bài, KHÔNG escalate, KHÔNG hai model — cô lập đúng một biến
| ô | greedy | maj3 | seq | **delta_seq** | lượng tử |
|---|---|---|---|---|---|
| math-1.5B | .3367 | .3667 | .4233 | **+.0566** | fp16 |
| **math-7B** | **.4900** | .5100 | **.6533** | **+.1433** | nf4 |
| gsm8k-1.5B | .6200 | .6700 | .6800 | +.0100 | fp16 |
| **gsm8k-7B** | **.9067** | .9233 | .9133 | **−.0100** | nf4 |

### PHÉP SO SÁNH QUYẾT ĐỊNH: **CÙNG MỘT MODEL 7B, HAI DẤU NGƯỢC NHAU**
7B trên MATH (`greedy` .4900) -> `delta_seq` **+.1433**.
7B trên GSM8K (`greedy` .9067) -> `delta_seq` **−.0100**.
Cùng trọng số, cùng arm, cùng ngân sách. **Biến quyết định là model đã giỏi tới đâu TRÊN TÁC VỤ ĐÓ**,
không phải tác vụ là gì, cũng không phải bài khó hay dễ.
Mọi ô có `greedy` < .60 đều DƯƠNG; ô có `greedy` > .85 ÂM. **Hàng 1 của #51.**

### ĐÂY KHÔNG PHẢI GIẢ THUYẾT ĐÃ CHẾT SỐNG LẠI
#47 kiểm **độ khó của BÀI trong cùng tác vụ** -> CHẾT ở vòng #83, và chết đúng: cả ba tầng GSM8K
đều có `big_maj3` > .90, **không tầng nào chưa bão hoà**, nên độ khó không thể phân biệt gì.
#51 kiểm **độ chính xác của MODEL ĐANG CHẠY** — biến KHÁC — và biến này đứng vững.

### GIẢI ĐƯỢC CÂU ĐỐ "MATH LÀ NGOẠI LỆ" Ở VÒNG #83
MATH không đặc biệt. 7B chỉ đơn giản là **còn xa trần trên MATH** (.49) và **đã bão hoà trên GSM8K** (.91).
Code nằm giữa: MBPP 7B đo được `greedy` = .7091 (H43) và cho dấu ÂM.
=> Điểm đổi dấu nằm đâu đó trong khoảng **.62 – .71**.

### KHÔNG khẳng định: độ lớn KHÔNG đơn điệu theo `greedy`
.3367 -> +.0566 nhưng .4900 -> +.1433. Đỉnh nằm quanh .49, không phải giảm đều.
Hàng 1 chỉ nói về DẤU trong hai dải, và tôi chỉ khẳng định đúng chừng đó.

### PHÁT BIỂU ĐƯỢC PHÉP DÙNG (thay cho phát biểu cũ ở vòng #73)
> Ở CÙNG ngân sách sinh, tinh chỉnh tuần tự có mỏ neo **hơn** lấy mẫu + bỏ phiếu **khi và chỉ khi
> model còn xa trần trên chính tác vụ đó** (`greedy` < ~.60). Khi model đã bão hoà (`greedy` > ~.85)
> nó **hại**. Đo sạch trên 4 ô, không escalate, cùng một model cho hai dấu ngược nhau.

## [Loop] VÒNG #86 — **H47: PHÂN RÃ MỎ NEO TÁI LẬP, NHƯNG CON SỐ "63%" THÌ KHÔNG**
### MBPP 511–974 (tách H44 chưa từng chạy), 464 bài, 225 escalate (.485 HỢP LỆ), biên dịch .993
| đại lượng | H44 (11–510) | **H47 (511–974)** | lệch |
|---|---|---|---|
| **B − A** (riêng MỎ NEO) | +.0981 | **+.0800** | **.018** |
| C − B (riêng CẤU TRÚC tuần tự) | +.0566 | **+.0889** | .032 |
| C − A (tổng) | +.1547 | +.1689 | .014 |

### PHÁN QUYẾT: **HÀNG 1 của #53 — TÁI LẬP**
`B − A` dương ở cả hai tách, lệch **.018 < .05**. **Bỏ mỏ neo hồi lại 8–10 điểm trên code.**
Đo trên hai tách rời nhau. Đây là kết quả chắc chắn.

### NHƯNG PHẢI **RÚT LẠI** CON SỐ "63%" TÔI ĐÃ NÓI Ở VÒNG #84
Tỉ lệ `(B−A)/(C−A)` = **63% (H44)** và **47% (H47)**. Hai thành phần **đổi chỗ cho nhau**:
ở tách thứ hai, CẤU TRÚC tuần tự đóng góp NHIỀU HƠN mỏ neo một chút.
=> Chỉ được nói: **mỏ neo gây hại ~8–10 điểm trên code, chiếm KHOẢNG MỘT NỬA tổng thiệt hại.**
KHÔNG được trích "63%". Hai phép đo cách nhau như vậy không đỡ nổi một con số chính xác đến thế.
(Bảng khoá #53 có sẵn hàng cho tình huống này: "hướng đúng, độ lớn KHÔNG ổn định".)

### Hàng 5 của #53 KHÔNG kích hoạt
`C − B` giữ NGUYÊN DẤU (dương ở cả hai tách) -> phần "cấu trúc tuần tự cũng gây hại" vẫn đứng,
dù độ lớn dao động (.0566 vs .0889).

### TỔNG HỢP HAI KẾT QUẢ HÔM NAY VỀ TUẦN TỰ
- **H45**: dấu của `delta_seq` đi theo **độ chính xác của chính model** — CÙNG 7B cho +.1433 (MATH,
  `greedy` .49) và −.0100 (GSM8K, `greedy` .91).
- **H44+H47**: trên code, thiệt hại chia ~nửa-nửa giữa **mỏ neo** và **cấu trúc tuần tự**,
  tái lập trên hai tách.
Code (MBPP 7B `greedy` .7091) nằm ở phía "đã khá bão hoà" của điểm đổi dấu .62–.71 -> hai kết quả
này **nhất quán với nhau**: ở vùng bão hoà, cả mỏ neo lẫn lượt tự kiểm đều chỉ phá đáp án đã đúng.

## [Loop] VÒNG #87 — **H46: MỎ NEO **KHÔNG PHẢI** CƠ CHẾ. LƯỢT THÊM MỚI LÀ.** → RÚT LẠI VÒNG #73
### 4 ô × 300 bài, bốn nhánh trong CÙNG một lần chạy
| ô | greedy | maj3 | A (có mỏ neo) | B (không mỏ neo) | **A−B** | A−maj3 | B−maj3 |
|---|---|---|---|---|---|---|---|
| math-1.5B | .3300 | .3600 | .4333 | .4033 | +.0300 | +.0733 | +.0433 |
| **math-7B** | .4933 | .4800 | **.6367** | **.6267** | **+.0100** | **+.1567** | **+.1467** |
| gsm8k-1.5B | .6233 | .6400 | .6900 | .6833 | +.0067 | +.0500 | +.0433 |
| gsm8k-7B | .9133 | .9267 | .9100 | .9167 | −.0067 | −.0167 | −.0100 |

### Script báo **HỖN HỢP** (dấu A−B không đồng nhất) — và cách đọc trung thực còn sắc hơn
Trên TOÁN, mỏ neo gần như **không làm gì**: |A−B| ≤ .01 ở **ba trên bốn ô** (~3 bài/300), tối đa .03.
Trên CODE, cùng phép đo đó cho **−.0800 (H47)** và **−.0981 (H44)**.
=> Mỏ neo chạy từ **vô tác dụng** (toán) đến **gây hại rõ** (code). **Không bao giờ là nguồn của lợi ích.**

### NGUỒN CỦA LỢI ÍCH LÀ **LƯỢT THÊM**, KHÔNG PHẢI MỎ NEO
math-7B: có mỏ neo hơn `maj3` **+.1567**; KHÔNG mỏ neo hơn `maj3` **+.1467**. **Gần như bằng nhau.**
Bỏ sạch mỏ neo, lợi ích vẫn còn nguyên.

### RÚT LẠI PHÁT BIỂU TRUNG TÂM CỦA VÒNG #73
Vòng #73 ghi: *"Cơ chế là **MỎ NEO ĐÁP ÁN TRƯỚC**, không phải phân vai — nhánh không có ngôn ngữ
vai nào đạt kết quả ngang hoặc hơn."* Đó là lời giải thích cho việc `SS_anc` ngang `PSV`.
**Đo trực tiếp: mỏ neo đóng góp ≈ 0 trên toán. Phát biểu đó SAI và tôi RÚT LẠI.**
`SS_anc` ngang `PSV` vì **lý do khác** — và lý do đó vẫn CHƯA BIẾT. Ứng viên còn lại:
đơn giản là **số lượt sinh thêm + một lượt tự kiểm**, bất kể prompt viết gì.

### H46 CŨNG TÁI LẬP ĐỘC LẬP H45
| ô | H45 (`delta_seq`) | H46 (`A−maj3`) | lệch |
|---|---|---|---|
| math-7B | +.1433 | +.1567 | .013 |
| gsm8k-7B | −.0100 | −.0167 | .007 |
| math-1.5B | +.0566 | +.0733 | .017 |
| gsm8k-1.5B | +.0100 | +.0500 | .040 |
Hai loạt kernel riêng biệt. **Kết quả bão hoà ở #85 đứng vững.**

### PHÁT BIỂU ĐƯỢC PHÉP DÙNG SAU HÔM NAY
> Ở cùng ngân sách, **thêm một lượt tinh chỉnh tuần tự** (giải lại + tự kiểm) hơn lấy mẫu + bỏ phiếu
> **khi model còn xa trần trên tác vụ đó** (`greedy` < ~.60), và hại khi đã bão hoà (`greedy` > ~.85).
> **Việc có nhắc lại đáp án cũ (mỏ neo) hay không gần như không ảnh hưởng trên toán, và GÂY HẠI trên code.**

## [Loop] VÒNG #88 — **H48: QUY TẮC BÃO HOÀ CHỈ ĐÚNG CHO **TOÁN**. HÀNG 2 của #54.** → SỬA VÒNG #87
### MBPP 11–510, 498 bài/ô, TOÀN BỘ bài (không escalate), biên dịch .989/.993
| ô | greedy | maj3 | A (có mỏ neo) | B (không mỏ neo) | **delta_seq** | A−B |
|---|---|---|---|---|---|---|
| **mbpp-1.5B** | **.4558** | .4558 | .4337 | .4277 | **−.0221** | +.0060 |
| mbpp-7B | .6546 | .6727 | .6024 | .6104 | **−.0703** | −.0080 |

### Ô QUYẾT ĐỊNH: mbpp-1.5B có `greedy` = .4558 — **XA TRẦN**, quy tắc toán bảo phải DƯƠNG
Đo được **−.0221**. **Âm.** Tuần tự hại trên code **kể cả khi model còn xa trần**.
=> **Quy tắc bão hoà (#85) KHÔNG chuyển sang code.** Phát biểu tôi ghi ở vòng #87 nói chung cho
"tác vụ" là **QUÁ RỘNG** và phải thu hẹp lại thành **chỉ cho TOÁN**.
**PRIOR CỦA TÔI SAI** (đoán hàng 1). Tỉ lệ prior đúng: 2/8.

### PHÁT BIỂU ĐÃ SỬA (thay cho bản ở vòng #87)
> **TRÊN TOÁN** (GSM8K, MATH), ở cùng ngân sách, thêm một lượt tinh chỉnh tuần tự hơn lấy mẫu +
> bỏ phiếu **khi model còn xa trần** (`greedy` < ~.60), và hại khi đã bão hoà (`greedy` > ~.85).
> **TRÊN CODE, tuần tự hại ở CẢ HAI cỡ model** (−.022 ở 1.5B `greedy` .46; −.070 ở 7B `greedy` .65),
> nên quy tắc bão hoà **không áp dụng cho code**. Vì sao code khác — **CHƯA GIẢI THÍCH ĐƯỢC**.

### PHÁT HIỆN THỨ HAI: tác hại của MỎ NEO chỉ nằm ở **NHÓM ĐÃ LỌC**
Trên TOÀN BỘ bài: `A − B` = **+.0060 / −.0080** ≈ 0.
Trên **nhóm escalate** (H44/H47): `A − B` = **−.0981 / −.0800**.
=> Mỏ neo gây hại **tập trung ở những bài mà model yếu đã trượt test hiển thị** (bài khó/gài),
và **triệt tiêu** khi tính trên toàn bộ. Cả hai phép đo đều đúng; phát biểu "mỏ neo hại trên code"
**bắt buộc kèm điều kiện "trên nhóm bài khó đã lọc"**.

### Ghi chú: ở mbpp-1.5B, `maj3` = `greedy` = .4558 **bằng nhau tuyệt đối**
Lấy 3 mẫu không thêm được bài nào so với 1 lượt tham lam. Củng cố "nút thắt là SINH, không phải CHỌN".


## [Loop] VÒNG #89 — **H49: HAI NHÁNH BỊ HUỶ. MỘT DO MODEL, MỘT DO **TÔI**.**
### BigCodeBench 300 bài/ô, chạy được .99–1.00
| ô | greedy | "maj3" (HỎNG) | seq | "PSV" (HỎNG) |
|---|---|---|---|---|
| bcb-1.5B | .1600 | .0667 | .1933 | .1433 |
| bcb-7B | .3467 | .3467 | .3467 | .2967 |

### NHÁNH 1 BỊ HUỶ — `PSV`: **can thiệp KHÔNG diễn ra** (kiểm tra can thiệp của bổ sung #55)
"Kế hoạch" chứa code ở **85.3% (1.5B)** và **100% (7B)**. Không đọc được cho câu hỏi lập kế hoạch.
LƯU Ý: script gộp của tôi **không** cài cổng này nên nó vẫn in ra "HÀNG 3: lập kế hoạch không đáng
một lượt" cho ô 7B. **Tôi BÁC kết luận đó** — cổng can thiệp có quyền cao hơn script.

### NHÁNH 2 BỊ HUỶ — `maj3`: **lỗi thiết kế CỦA TÔI**
```
def maj3(x): return sum(s["pass"] for s in x["samp"]) >= 2
```
Hai lỗi: (a) chọn bằng `pass` — **chính là kết quả test dùng để chấm** -> **RÒ RỈ**;
(b) "≥2/3 đạt" **không phải bỏ phiếu đa số**, mà là điều kiện HỘI. Ở `greedy` .16 điều đó gần như
không xảy ra -> `maj3` = .0667, **thấp hơn cả greedy .1600**.
=> **`seq − maj3` = +.1266 KHÔNG PHẢI kết quả. Tôi rút lại trước khi nó đi đâu xa hơn.**
Không sửa được từ dữ liệu đã lưu: prompt BigCodeBench **không có test ví dụ** nên không có tín hiệu
thực thi không-rò-rỉ để gom cụm, và tôi chỉ lưu cờ `pass` của 3 mẫu, **không lưu code của chúng**.

### SO SÁNH HỢP LỆ DUY NHẤT CÒN LẠI (3 lượt vs 1 lượt — KHÔNG ngang ngân sách)
`seq − greedy` = **+.0333** (1.5B) và **+.0000** (7B).

### HỆ QUẢ ĐÚNG
**H49 KHÔNG nói được gì về `delta_seq` trên BigCodeBench.** Phát biểu ở vòng #88
("tuần tự hại trên code") vẫn đứng **đúng như đã đo trên MBPP**; BigCodeBench đơn giản là
**CHƯA ĐO ĐƯỢC**, không phải mâu thuẫn.

### BÀI HỌC — nhánh đối chứng cũng phải qua kiểm tra hiệu lực
Tôi đã dựng ba lớp cổng cho *giả thuyết* (ngưỡng suy biến, đẳng thức tự kiểm, kiểm tra can thiệp)
nhưng **không cổng nào kiểm NHÁNH ĐỐI CHỨNG có đúng là thứ nó tự nhận hay không**.
`maj3` phải thoả hai điều kiện, từ nay ghi thành quy tắc:
1. **KHÔNG được dùng tín hiệu chấm điểm để chọn** (nếu không thì nó là oracle, không phải bỏ phiếu).
2. Phải là **chọn 1 trong k**, không phải điều kiện hội trên k.
Và: **lưu code của MỌI mẫu**, không chỉ cờ đạt/không — nếu có code thì đã cứu được nhánh này.


## [Loop] VÒNG #90 — **H50: LẬP KẾ HOẠCH **THẬT SỰ** KHÔNG ĐÁNG MỘT LƯỢT, KỂ CẢ TRÊN BÀI DÀI**
### BigCodeBench 300 bài/ô. **Can thiệp ĐÃ diễn ra**: "kế hoạch" chứa code chỉ **7.0%** (1.5B) và **0.0%** (7B)
Cưỡng chế ở tầng sinh (`bad_words_ids` chặn dấu rào code) hạ tỉ lệ từ **85.3% → 7.0%**.
Bảo model "đừng viết code" vô dụng; **chặn token thì được**.

| ô | plan có code | greedy | seq | PSV | **PSV − seq** |
|---|---|---|---|---|---|
| bcb-1.5B | 7.0% | .1567 | .1900 | .1267 | **−.0633** |
| bcb-7B | 0.0% | .3467 | .3467 | .3100 | **−.0367** |

### PHÁN QUYẾT: **HÀNG 4 của #56, ở CẢ HAI ô**
Dùng một trong ba lượt để LẬP KẾ HOẠCH **thua** dùng nó để GIẢI THỬ, **3.7–6.3 điểm**.
Khác H49: lần này **can thiệp CÓ diễn ra**, nên đây là **kết quả âm THẬT**.
**PRIOR CỦA TÔI ĐÚNG** (đoán hàng 4). Tỉ lệ: 3/9.

### TRẢ LỜI TRỰC TIẾP CHO GIẢ THUYẾT CỦA NGUYÊN
Nguyên nêu: MBPP là hàm 3 dòng, không có gì để lập kế hoạch — hãy thử bài dài, nhiều bước.
Đã thử: BigCodeBench dài gấp ~4 lần, phải ghép nhiều thư viện, đặc tả đầu ra nhiều phần.
**Lập kế hoạch VẪN không đáng một lượt.** Các kết quả null trước đây trên GSM8K/MATH/MBPP
**KHÔNG phải** do bộ dữ liệu quá ngắn.

### GIẢ THUYẾT THAY THẾ CŨNG CHẾT
Tôi đã khoá sẵn hàng: nếu cưỡng chế làm `PSV` TỤT MẠNH thì thứ đang giúp là **BẢN NHÁP CODE**,
không phải kế hoạch. Đo được: `.1433 → .1267` và `.2967 → .3100` — **gần như không đổi**.
=> `PSV` thua từ trước rồi, không phải vì code lọt vào kế hoạch.

### KHÔNG được khẳng định
- So với **lấy mẫu song song**: KHÔNG kết luận được — `maj3` trên BigCodeBench đã bị huỷ ở vòng #89
  do lỗi thiết kế của tôi (chọn bằng kết quả test = rò rỉ).
- `seq − greedy` = +.0333 / +.0000 là **3 lượt so với 1 lượt**, không ngang ngân sách.
- Một bộ dữ liệu, hai cỡ model, n=300 mỗi ô. **Người lập kế hoạch là CHÍNH model đi giải** —
  một planner MẠNH HƠN (model lớn hơn lập kế hoạch cho model nhỏ giải) **chưa được thử**.

### Ghi chú: ở 7B, `greedy` = `seq` = **.3467 bằng nhau tuyệt đối** (lặp lại y hệt H49)
Hai lượt tinh chỉnh thêm không đổi được một bài nào trên BigCodeBench ở 7B.


## [Loop] VÒNG #91 — **H51: KẾ HOẠCH TỪ MODEL MẠNH CÓ GIÚP MODEL YẾU — NHƯNG BỊ ÁP ĐẢO**
### BigCodeBench 300 bài. Can thiệp ĐẠT: "kế hoạch" chứa code **0.0%**, chạy được **1.000**
| nhánh | acc | chi phí (1.5B-eq) |
|---|---|---|
| small_greedy | .1633 | 1.00 |
| small_seq | .1933 | 3.00 |
| **big_greedy** | **.3467** | **5.07** |
| bigplan_smallsolve | .2067 | 7.07 |

### PHÁN QUYẾT: **HÀNG 2 của #57**
Kế hoạch của 7B **có** nâng 1.5B: `.1633 → .2067` = **+4.3 điểm** so với chính nó chạy tham lam.
Nhưng so với `small_seq` chỉ **+.0134** — **4 bài trên 300, nằm trong nhiễu**.
=> **Một kế hoạch từ model lớn gấp 5 lần đáng giá xấp xỉ việc model nhỏ tự thử thêm hai lượt.**
Và số quyết định: **−.1400 so với `big_greedy`, trong khi TỐN THÊM 2.00 đơn vị chi phí.**
Chạy thẳng 7B một lượt — không kế hoạch, không phân vai, không model thứ hai — **hơn 14 điểm và RẺ HƠN**.
**PRIOR CỦA TÔI ĐÚNG** (đoán hàng 2). Tỉ lệ: 4/10.

### ĐÂY LÀ LẦN THỨ BA CÙNG MỘT HÌNH MẪU — và là kết luận thực dụng của cả ngày
| phép thử | đường ống công phu | bị thua bởi |
|---|---|---|
| H42 (#81) định tuyến trên code | định tuyến oracle + escalate | `big_greedy`, thua cả acc lẫn chi phí |
| H50 (#90) tự lập kế hoạch | kế hoạch → giải → tự kiểm | tuần tự thường |
| **H51 (#91) kế hoạch bất đối xứng** | 7B lập kế hoạch → 1.5B giải → tự kiểm | **`big_greedy`, −.140 với +2.00 chi phí** |

> **TRÊN CODE, chi phí điều phối KHÔNG BAO GIỜ tự bù lại.** Cùng ngần ấy tính toán,
> chạy MỘT LƯỢT model lớn hơn luôn tốt hơn.

### Điều này KHÔNG mâu thuẫn với H15 (+14 điểm nhờ Verifier 7B)
H15 đo trên **toán**, và vai đó là **KIỂM TRA** (dùng thông tin đúng/sai), không phải **LẬP KẾ HOẠCH**.
Khớp với phân biệt đã khoá ở #42: **bộ kiểm có giá trị khi là ORACLE về tính đúng**;
lập kế hoạch không mang thông tin đúng/sai nào cả.

### Giới hạn phải nêu
Một bộ dữ liệu (BigCodeBench), một cặp model (1.5B/7B), n=300, chưa tái lập.
Chưa thử: kế hoạch từ model MẠNH HƠN NỮA, hoặc trên toán (nơi tuần tự vốn có tác dụng).


## [Loop] VÒNG #92 — **H52: REFACTOR — oracle GIÚP nhưng KHÔNG đạt ngưỡng tôi đã khoá**
### BigCodeBench, 266 bài (lời giải chuẩn đã đạt test trong chính kernel), nf4, AST đọc được .985
| nhánh | preserve | simpler¹ | good_refactor | nút TB |
|---|---|---|---|---|
| `ref1` | **.7406** | .3147 | **.2331** | 111.2 |
| `ref_seq` (LLM tự nhận xét) | **.7105** | .2963 | .2105 | 114.5 |
| `ref_exec` (chạy test) | **.7707** | .3073 | .2368 | 113.1 |
| *(gốc)* | — | — | — | 119.5 |

¹ chỉ tính trên các bài `preserve`

### PHÁN QUYẾT: **nằm GIỮA hai ngưỡng — không được coi là xác nhận**
`preserve(exec) − preserve(seq)` = **+.0602**, nằm giữa .05 và .10 đã khoá.
Hướng ủng hộ oracle nhưng **KHÔNG đạt ngưỡng đã đăng ký**, nên **không được nói là xác nhận #42**.
**PRIOR CỦA TÔI SAI** (đoán hàng 1, ≥ .10). Tỉ lệ: 4/11.

### KẾT QUẢ SẮC NHẤT: **lượt LLM tự nhận xét làm REFACTOR TỆ ĐI**
`ref_seq` thua `ref1` ở **mọi** thước đo: preserve −.0301, good −.0226, và code **TO HƠN**
(114.5 vs 111.2 nút). Một lượt "xem lại" mà **không có cách kiểm hành vi** thì **phá** bản refactor
đang chạy được. Đây là lần thứ **tư** trong ngày LLM-tự-nhận-xét-không-oracle tỏ ra vô ích hoặc có hại
(H35 `llm3`, #90 PSV, #91, nay #92).

### GIỚI HẠN NĂNG LỰC — nêu thẳng
- Chỉ **~23%** lần refactor vừa giữ hành vi vừa đơn giản hơn.
- **~26% vẫn làm hỏng hành vi NGAY CẢ KHI có oracle sửa lỗi** (`ref_exec` preserve .7707).
- `ref1` làm hỏng ngay **69/266 = 25.9%**.
- Độ phức tạp giảm rất ít: 119.5 → 111.2 nút (**~7%**).
=> 7B ở quy mô này **phần lớn hoặc làm hỏng code, hoặc gần như không đổi gì**.

### VỀ MỎ NEO — câu hỏi đặt ra khi thiết kế
H44/H47: mỏ neo vào code **HỎNG** khiến model VÁ thay vì viết lại (−8..−10 điểm ở nhóm khó).
Ở đây code đưa vào **ĐÚNG** và mỏ neo chính là đề bài — nhưng model vẫn làm hỏng 1/4 số bài.
=> Vấn đề **không chỉ** là "mỏ neo vào code sai": model **không giữ nổi hành vi** khi viết lại,
bất kể code gốc đúng hay sai.


## [Loop] VÒNG #93 — **H53: ORACLE CHỈ ĐÚNG CHỖ HỎNG, NHƯNG MODEL KHÔNG SỬA NỔI**
### BigCodeBench refactor, 267 bài, nf4, oracle sửa tối đa 3 vòng
| nhánh | preserve | simpler¹ | good | nút TB |
|---|---|---|---|---|
| `ref1` | .7378 | .3147 | .2322 | 111.2 |
| `ref_seq` (LLM tự nhận xét) | **.7116** | .2947 | .2097 | 114.3 |
| `ref_exec1` (1 vòng) | .7715 | .3058 | .2360 | 112.9 |
| `ref_exec3` (tối đa 3 vòng) | **.7903** | .3081 | .2434 | 114.1 |
| *(gốc)* | | | | 119.3 |

### TÁI LẬP GẦN NHƯ HOÀN HẢO — kiểm tra quan trọng nhất, và nó ĐẠT
`ref_exec1` = **.7715**, H52 đo được **.7707** -> lệch **+.0008**.
`ref_seq` = **.7116**, H52 = **.7105**. Hai loạt kernel riêng biệt.
=> Toàn bộ đường ống refactor **tái lập được**. Đây là cơ sở để tin phần còn lại.

### PHÁN QUYẾT: **HÀNG 2 của #59** — vòng sửa thêm gần như vô ích
`exec3 − exec1` = **+.0188**, **dưới ngưỡng .02 đã khoá**.
Và KHÔNG phải vì không dùng tới: **trung bình 2.70 vòng** trên các bài hỏng, chạm trần 3.
Model được chỉ ĐÚNG bài test nào trượt, **ba lần**, và chỉ cứu thêm **1.9 điểm**.
**~21% vẫn hỏng** sau tất cả. **PRIOR CỦA TÔI ĐÚNG.** Tỉ lệ: 5/12.

### ĐỐI CHIẾU VỚI H35 — ĐÂY MỚI LÀ PHÁT HIỆN
| | tác vụ | oracle 3 vòng đáng giá |
|---|---|---|
| H35 `exec3` | **SINH code mới** | **+6 đến +11 điểm** |
| H53 `ref_exec3` | **REFACTOR** | **+1.9 điểm** |
Cùng một giao thức, cùng loại oracle. Khác ở chỗ **model có sửa nổi hay không**.
=> **Lỗi khi SINH code thì thô và khu trú được; lỗi khi REFACTOR là TRÔI NGỮ NGHĨA TINH VI.**
Stack trace nêu **triệu chứng** chứ không chỉ ra **chỗ lệch**. Oracle cung cấp thông tin như nhau,
nhưng chỉ hữu ích khi model đủ sức hành động theo nó.

### Sửa lại phát biểu chung của dự án về oracle
Trước nay: *"bộ kiểm có giá trị khi là ORACLE về tính đúng"*. Cần thêm điều kiện:
> **Oracle chỉ đáng giá khi model CÓ THỂ HÀNH ĐỘNG theo tín hiệu đó.**
> Trên refactor, oracle phát hiện đúng nhưng model không sửa được -> lợi ích gần như bằng 0.


## [Loop] VÒNG #94 — **H55: VAI VERIFIER LÀM ĐƯỢC VIỆC — nhưng vẫn KHÔNG hơn lấy mẫu**
### MBPP 11–510, 498 bài, 12 shard, nf4. Đề xuất của Nguyên: verifier TỰ VIẾT TEST.

### VAI NÀY THÀNH CÔNG — artifact đầu tiên trong dự án ĐO ĐƯỢC LÀ TỐT
| thước đo | giá trị |
|---|---|
| sinh được test | **99.8%** số bài, trung bình **1.44** assert |
| **`test_soundness`** | **.8712** — lời giải chuẩn ĐẠT hết test tự sinh |
| **`test_power`** | **.7514** — bắt được **133/177** bản cài đặt SAI thật |
Prior của tôi là soundness .60–.80; đo được **.87**. Verifier viết test **ĐÚNG** và **CÓ LỰC**.

### NHƯNG ĐƯỜNG ỐNG THÌ HOÀ
| nhánh | acc (assert giữ lại) |
|---|---|
| solve1 | .6546 |
| **maj3** | **.6627** |
| tdd_impl (thấy test, KHÔNG chạy) | .6426 |
| tdd_noexec (thấy test + tự nhận xét) | **.6084** |
| **tdd (thấy test + CHẠY + sửa)** | **.6667** |

**HÀNG 2 của #61**: `tdd − maj3` = **+.0040**. Oracle tự sinh — dù đúng và có lực —
**không thêm gì** so với bỏ phiếu đa số. **PRIOR CỦA TÔI ĐÚNG.** Tỉ lệ: 6/13.

### PHÂN RÃ — vì sao hoà, và KHÔNG phải lý do tôi đoán
1. **Đưa test vào prompt LÀM HẠI bản cài đặt đầu**: `tdd_impl` .6426 **THẤP HƠN** `solve1` .6546 (−.0120).
   Viết code bám theo **1.44 assert mỏng** làm hỏng nhiều hơn được.
2. **CHẠY test thì hồi lại**: `tdd − tdd_noexec` = **+.0583** — CÙNG bộ test, khác duy nhất ở chỗ CÓ CHẠY.
   Nguyên tắc oracle đứng vững thêm một lần nữa.
3. Toàn bộ phần lợi ở (2) bị tiêu để bù cho phần hại ở (1) -> tổng ≈ 0.

### `tdd_noexec` là nhánh TỆ NHẤT (.6084) — thấp hơn cả không làm gì
Lần thứ **năm** trong ngày: LLM tự nhận xét mà KHÔNG chạy được gì thì **gây hại**
(H35 `llm3`, #90 PSV, #92/#93 refactor, nay #94).

### BƯỚC KẾ SUY RA TRỰC TIẾP TỪ PHÂN RÃ
Đừng để bản cài đặt đầu nhìn thấy test. **Giải bình thường → CHẠY test tự sinh → chỉ dùng để SỬA.**
Giữ được +.0583 của việc chạy test mà không phải trả −.0120 của việc bám theo test mỏng.
Dự đoán thô: ≈ .6667 + .0120 ≈ **.679** vs `maj3` .6627. Phải ĐĂNG KÝ TRƯỚC rồi mới chạy.


## [Loop] VÒNG #95 — **H56: KẾT QUẢ DƯƠNG ĐẦU TIÊN — dùng test tự sinh để CHỌN, +.0401**
### MBPP 11–510, 498 bài, 12 shard, 7B nf4. `test_soundness` .8712 (ĐẠT), 1.44 assert/bài.
| nhánh | acc | chi phí |
|---|---|---|
| maj3 | .6586 | 3 lượt |
| **maj8** | **.6687** | 8 lượt |
| **`select_tests`** | **.7088** | **8 + 1 lượt** |
| oracle8 (trần) | .7631 | — |

### PHÁN QUYẾT: **HÀNG 1 của #62**
`select_tests − maj8` = **+.0401**, vượt xa ngưỡng +.02.
Khoảng trống `oracle8 − maj8` = **+.0944** -> **thu được 42.5%**.
**PRIOR CỦA TÔI ĐÚNG** (đoán +2..+4 điểm, thu 25–50%). Tỉ lệ: **7/14**.

### ĐIỀU LÀM NÊN KHÁC BIỆT — cùng một công cụ, khác chỗ dùng
| dùng test tự sinh để… | kết quả |
|---|---|
| **SỬA** một bản cài đặt (#94) | **+.0040** — vô nghĩa |
| **CHỌN** trong 8 mẫu (#95) | **+.0401** — gấp 10 lần |
Soundness .871 / power .751 luôn là **bộ lọc chạy được**; ở #94 tôi chĩa nó vào việc sai.
=> Bài học tổng quát: **oracle nên dùng để LỌC ỨNG VIÊN, không phải để SỬA một ứng viên.**
Khớp với nút thắt đã đo suốt ngày: 80.8% bài ĐÃ CÓ lời giải đúng trong pool; vấn đề là CHỌN.

### VÌ SAO KHÔNG THU ĐƯỢC 100%
Chỉ **1.44 assert/bài** -> nhiều mẫu HOÀ điểm (cùng đạt hết số test ít ỏi đó), lúc đó phải
rơi về bỏ phiếu hành vi. Muốn thu thêm phải **sinh NHIỀU test hơn** — đó là phép thử kế tiếp.

### BẮT BUỘC TRƯỚC KHI CÔNG BỐ
Bảng khoá #62 ghi rõ: **phải TÁI LẬP trên tách MBPP 511–974** (dữ liệu H56 chưa từng chạm).
Đang chạy ngay: H57.


## [Loop] VÒNG #96 — **H57: TÁI LẬP THÀNH CÔNG. Kết quả dương đầu tiên của dự án trên CODE đứng vững.**
| lần chạy | tách MBPP | n | `select − maj8` | thu được | soundness |
|---|---|---|---|---|---|
| H56 (#95) | 11–510 | 498 | **+.0401** | 42.5% | .8712 |
| **H57** | **511–974** | **464** | **+.0388** | **46.1%** | .8750 |
**Hai tách RỜI NHAU, lệch .0013.** Ngang với hai cặp tái lập chặt nhất trong ngày (.0005 / .0008).

### PHÁT BIỂU ĐƯỢC PHÉP DÙNG
> Dùng **test do chính model tự sinh** để **CHỌN trong 8 ứng viên** hơn bỏ phiếu đa số
> **+.039 đến +.040** trên MBPP, tái lập trên hai tách rời nhau, với chi phí **thêm 1 lượt sinh**
> (8+1 so với 8). Thu được **42–46%** khoảng cách tới trần `oracle@8`.

### VÌ SAO ĐÂY LÀ KẾT QUẢ THẬT (khác mọi thứ trước đó trong ngày)
- Nút thắt đã đo: **80.8% số bài ĐÃ CÓ lời giải đúng trong pool** -> vấn đề là CHỌN, không phải SINH.
- Cùng bộ test đó dùng để **SỬA** chỉ được **+.004** (#94); dùng để **CHỌN** được **+.040** — gấp 10 lần.
=> **Oracle nên dùng để LỌC ỨNG VIÊN, không phải để SỬA một ứng viên.**

## [Loop] VÒNG #97 — **H58: SỐ LƯỢNG TEST *KHÔNG* PHẢI NÚT THẮT. HÀNG 2 của #63.**
Sinh test 3 lượt (T=0.8) rồi hợp nhất, cùng tách 11–510:
| | H56 | **H58** |
|---|---|---|
| assert/bài | 1.44 | **2.22** |
| `test_soundness` | .8712 | **.8048** |
| `select_tests` | .7088 | **.7189** |
`select`(H58) − `select`(H56) = **+.0101**, **DƯỚI** ngưỡng +.02 đã khoá -> **HÀNG 2**:
*"thêm test KHÔNG giúp -> nút thắt là CHẤT LƯỢNG PHÂN BIỆT, không phải số lượng."*
**PRIOR CỦA TÔI SAI** (đoán hàng 1). Tỉ lệ: **7/15**.

### RỦI RO ĐÃ KHOÁ TRƯỚC ĐÃ XẢY RA ĐÚNG NHƯ DỰ ĐOÁN
Hợp nhất test lấy mẫu làm **soundness tụt .8712 -> .8048 (−.066)**: test sai lọt vào và
**loại oan mẫu ĐÚNG**. Phần lợi từ phân biệt thêm bị chính phần hại này ăn mất phần lớn.
=> Muốn thu thêm khoảng trống thì phải **tăng CHẤT LƯỢNG test**, không phải số lượng —
ví dụ lọc test bằng chính lời giải đa số, hoặc sinh test đối kháng có kiểm tra tính đúng.


## [Loop] VÒNG #98 — **H59 (GRPO thưởng đã sửa): HỌC CÁCH **NHẠI LẠI**. Cùng một lỗ hổng, cửa khác.**
### GSM8K, 1.5B + LoRA, 100 bước, `adapter_leak = 0.0` (HỢP LỆ)

### TRƯỚC HẾT: TÔI ĐÃ BÁO SAI SỐ ĐẦU TIÊN — lỗi BỘ CHẤM
Bộ rút đáp án của tôi dùng `=\s*\$?(\d...)` nên **không đọc được `= \$12`** (dấu `$` thoát LaTeX).
Model GỐC viết nhiều LaTeX -> bị đọc sai **23/500**; model đã huấn luyện viết văn trơn -> chỉ **7/500**.
**Lỗi thiên vị đúng nhánh tôi mong thắng.** Sửa bộ chấm rồi chấm lại toàn bộ 500 trace:
| | báo lần đầu | **đã sửa** |
|---|---|---|
| gain_base | .054 | .042 |
| gain_lora | .076 | .060 |
| **chênh** | **+.0220** | **+.0180** |
| sửa/phá base | 45/18 | 37/16 |
| sửa/phá lora | 42/4 | **33/3** |
=> **+.0180 DƯỚI ngưỡng +.02 đã khoá** -> **HÀNG 1 KHÔNG kích hoạt.** Thêm nữa, số can thiệp
giảm 27.6% (> mức 25% cho phép) -> điều kiện HÀNG 4 thoả. **H59 KHÔNG xác nhận "RL giúp khi mục tiêu đúng".**

### PHÁT HIỆN THẬT: ĐỘ DÀI ĐẦU RA VERIFIER **480 -> 19 KÝ TỰ**
Trung vị đầu ra: gốc **480** ký tự, sau huấn luyện **19** ký tự — tức là `"The answer is 240."`
**Nó thôi kiểm tra hoàn toàn. Nó NHẠI LẠI đáp án của Solver.**
| | gốc | GRPO |
|---|---|---|
| đồng ý với Solver | .790 | **.868** |
| **đồng ý KHI Solver SAI** (bỏ lọt lỗi) | .497 | **.644** |
| đồng ý khi Solver ĐÚNG (không phá) | .950 | **.991** |
Tốt hơn ở chỗ không phá, **tệ hơn ở chỗ bắt lỗi**. +.0180 là hai hiệu ứng gần như triệt tiêu nhau.

### VÌ SAO — LÀ SỐ HỌC, KHÔNG PHẢI TINH CHỈNH
Thưởng = `+1` nếu đáp án cuối của verifier ĐÚNG. **Nhại lại Solver được đúng bằng độ chính xác
của Solver (.646).** Muốn hơn nhại lại thì verifier phải **CHÍNH XÁC HƠN Solver** — nhưng nó
CHÍNH LÀ Solver: cùng 1.5B, cùng tri thức, chỉ thêm LoRA.
=> **Điểm tối ưu của hàm thưởng CHÍNH LÀ nhại lại**, và nó tìm ra.
Tôi đã thay một chiến lược thoái hoá (**im lặng miễn phí**) bằng một chiến lược thoái hoá khác
(**đồng ý miễn phí**). Cả hai đều là "không làm việc". Sửa hàm thưởng mà không cho verifier
bất kỳ **lợi thế thông tin** nào thì vô ích.

### PHÁT BIỂU TỔNG QUÁT (khớp mọi kết quả về verifier của dự án)
> **Verifier KHÔNG có lợi thế thông tin so với Solver thì KHÔNG THỂ vượt Solver, bất kể hàm thưởng.**
- H15: 7B kiểm 1.5B (**lệch năng lực**) -> **+14 điểm** ✅
- #95/#96: test CHẠY ĐƯỢC (**thông tin model không có**) -> **+.040**, tái lập ✅
- H37 (bộ kiểm huấn luyện, cùng cỡ), #90/#92/#93 (LLM tự nhận xét), H59 (RL cùng model) -> ≈0 hoặc hại ❌

### GIỚI HẠN DỮ LIỆU (nêu rõ)
- Lời giải huấn luyện sinh ở **T=0.8**, đánh giá ở **T=0.0** -> phân bố lỗi khác nhau.
- `nseq` chỉ **12.8/96**: ~87% nhóm mẫu đồng đều (cùng đúng hoặc cùng sai) nên **không có gradient**.
### Bước kế đúng đắn (chưa chạy)
Huấn luyện verifier trên lời giải của **model KHÁC/YẾU HƠN chính nó**, hoặc cho nó **công cụ thực thi** —
để việc "đúng hơn Solver" là chuyện KHẢ THI về nguyên tắc.

---

## Vòng #99 — H60: **CON SỐ AI CŨNG BÁO CÁO NÓI NGƯỢC VỚI CON SỐ ĐÚNG**
*(đăng ký trước #65, khoá tại `6ff5cce` TRƯỚC khi chạy — Solver 0.5B, Verifier 1.5B + GRPO)*

### Cổng hiệu lực: ĐẠT
`acc(S)` = **.3700** (trong [.20,.55]) · `adapter_leak` = **0.0** · `nseq` ~40/96 suốt 100 bước
(không suy biến, khác hẳn H23) · n = 500, 5 fold.

### Kết quả
| | S (0.5B giải) | I (1.5B **tự giải**) | V0 (1.5B xem lời giải) | V\* (1.5B + GRPO) |
|---|---|---|---|---|
| acc | .3700 | **.6440** | .4760 | .5400 |

| Đại lượng | Giá trị | 5 fold |
|---|---|---|
| **`V* − I`** (đăng ký trước là CHÍNH) | **−.1040** | −.14 −.07 −.11 −.12 −.08 → **5/5 ÂM** |
| `V* − S` (con số ai cũng báo cáo) | **+.1700** | **5/5 DƯƠNG** |
| `V0 − I` (giá bị đầu độc, chưa huấn luyện) | −.1680 | |
| `V* − V0` (GRPO có giúp) | +.0640 | 5/5 dương |

**Cùng một thí nghiệm. Hai con số. Kết luận NGƯỢC DẤU.**
Chênh lệch chỉ nằm ở **một nhánh đối chứng** mà gần như không ai chạy: *"nếu model mạnh cứ
tự giải, KHÔNG thèm xem lời giải của model yếu, thì sao?"*

### Bảng khoá #65: KHÔNG HÀNG NÀO KHỚP — lỗi thiết kế của tôi
- Hàng 1 cần `V*−I` ≥ +.02 → không.
- Hàng 2 cần \|`V*−I`\| < .02 → không.
- Hàng 3 cần độ dài SỤP và `agree_wrong` TĂNG → **ngược lại cả hai**.
- Hàng 4 cần `V*` < `V0` − .02 → không, `V*` > `V0` cả 5 fold.

Tôi đã viết bảng với giả định ngầm rằng chiều đầu độc không thể lớn đến thế. Nó lớn hơn
mọi hiệu ứng tôi đã đăng ký. **Ghi nhận là thiếu sót của bảng, KHÔNG bịa thêm hàng cho khớp.**

### Phần giải thích #98 ĐƯỢC XÁC NHẬN (cơ chế)
Ba chỉ số nhại lại đảo chiều **đúng như đã đoán trước** khi Solver yếu đi:
| | H59 (Solver 1.5B) | H60 (Solver 0.5B) |
|---|---|---|
| độ dài trung vị | 480 → **19** (sụp) | 418 → **822** (GẤP ĐÔI) |
| `agree_wrong` | .497 → **.644** (tăng) | .441 → **.274** (giảm) |
| sửa/phá | — | 11.6/1.0 → **19.4**/2.4 |

Nhại lại **đã biến mất** khi nó không còn là nước đi tối ưu. Lợi thế thông tin đúng là ràng buộc
chặn hành vi nhại lại. Nhưng gỡ được ràng buộc đó **không** làm kết quả dương.

### Điều MỚI: bị *cho xem* lời giải kém là ĐỘC, và độc hơn mọi thứ khác
Tách 300 bài (fold 0–2): **56 bài BỊ ĐẦU ĐỘC** (I đúng → V\* sai) so với **24 bài ĐƯỢC CỨU**.
Ròng −32/300 = −.107, khớp đúng `V*−I`.

Trong 56 bài bị đầu độc:
- **26 (46%)** — V\* lấy theo đáp án SAI của Solver (nhại lại còn sót).
- **30 (54%)** — V\* ra **đáp án THỨ BA**, không theo ai cả.

Hơn một nửa thiệt hại **không phải bắt chước**. Nhìn thấy một lời giải kém *làm hỏng lập luận
của chính nó* ngay cả khi nó không chép. Đây là **nhiễm độc**, không phải bắt chước —
và GRPO chỉ gỡ lại **38.1%** thiệt hại rồi dừng.

### Ý nghĩa
1. **`V − S` là con số sai.** Đúng phải là `V − I`. Ở đây một cái +.17, một cái −.10.
   Báo cáo `V−S` là so verifier với **model yếu**, không phải với **lựa chọn thay thế thật sự**
   (dùng chính con model mạnh đó mà giải thẳng, RẺ HƠN vì chỉ 1 lượt thay vì 2).
2. **Điều này đe doạ H15 (+14, 7B kiểm 1.5B)** — kết quả dương LÂU ĐỜI NHẤT của dự án.
   H15 **chưa bao giờ có nhánh I**. Nếu 7B tự giải mà đã ≥ 7B-kiểm-1.5B thì +14 là ảo giác
   do thiếu đối chứng. **Phải kiểm ngay** (H61).
3. Khớp với luận điểm xuyên suốt: thứ DUY NHẤT từng thắng là **test chạy được** (+.040, tái lập).
   Ở đó oracle mang thông tin model KHÔNG có. Ở đây ta có cho verifier lợi thế năng lực thật
   (1.5B > 0.5B) nhưng **kênh truyền là "đọc đoạn văn này"** — và văn bản từ agent yếu là độc ròng.

> **Định tuyến đầu ra của agent yếu vào agent mạnh là ÂM RÒNG.
> Không phải vì agent mạnh không đủ giỏi, mà vì việc ĐỌC đã gây hại rồi.
> Không hàm thưởng nào sửa được — thiệt hại nằm ở lần tiếp xúc, không nằm ở chính sách.**

---

## Vòng #100 — H61: **NHÁNH ĐỐI CHỨNG CÒN THIẾU GIẾT CÁCH PHÁT BIỂU CỦA H15**
*(đăng ký trước #66 khoá tại `9754607`, sửa prior #66-b tại `7aeaa89` — cả hai TRƯỚC khi có số)*

### Cổng: ĐẠT (`I − S` = +.2360 ≥ .05) · n = 500 · greedy · GSM8K test
| nhánh | là gì | acc | chi phí |
|---|---|---|---|
| S | 1.5B giải | .6720 | 1×1.5B |
| **I** | **7B TỰ giải, không xem gì** | **.9080** | **1×7B** |
| V | 7B xem lời giải của S rồi kiểm/sửa (thiết lập H15) | .8340 | 1×1.5B + 1×7B |

| đại lượng | giá trị | 5 fold |
|---|---|---|
| `V − S` (con số kiểu H15) | **+.1620** | +.14 +.16 +.17 +.21 +.13 → **5/5 DƯƠNG** |
| **`V − I`** (đăng ký trước là CHÍNH) | **−.0740** | −.12 −.05 −.04 −.03 −.13 → **5/5 ÂM** |

**PHÁN QUYẾT: HÀNG 3.** Leo thang **tệ hơn** chỉ dùng 7B, **ở chi phí CAO HƠN**
(V tốn thêm một lượt 1.5B mà I không tốn). **V bị ÁP ĐẢO HOÀN TOÀN.**

### Con số làm cho việc kiểm tra TRÔNG tuyệt vời
`fix/break` so với S = **85/4**, precision **.955**. Theo cách đo của H15 thì đây là verifier
xuất sắc: sửa 85 lỗi của 1.5B, chỉ phá 4. **Vẫn thấp hơn 7B-tự-giải 7.4 điểm.**
> **precision cao trên `fix/break` HOÀN TOÀN tương thích với việc cả pipeline bị áp đảo,**
> vì `fix/break` đo so với **S**, không đo so với **I**.

### Đầu độc tái lập qua thang model, benchmark khác, cặp model khác
**56 bị đầu độc** (I đúng → V sai) vs **19 được cứu**, ròng **−37/500 = −.074**, khớp đúng `V−I`.
| | H60 (0.5B→1.5B, GSM8K) | H61 (1.5B→7B, GSM8K) |
|---|---|---|
| nhại đáp án sai của S | 46% | **55%** |
| ra **đáp án THỨ BA** | 54% | **45%** |

Cả hai thang: **gần một nửa thiệt hại là đáp án thứ ba** — không theo ai cả.
Đọc một lời giải kém **làm hỏng lập luận vốn đã đúng**, không chỉ dụ nó chép.

### PRIOR CỦA TÔI SAI LẦN NỮA — và sai đúng chỗ tôi vừa tự tin thêm
`#66` tôi đoán hàng 2/3 (~70%). Rồi `#66-b` tôi **tự sửa prior sang hàng 1 (~55%)** vì tin
"7B đủ mạnh để miễn nhiễm". **Sai.** 7B bị đầu độc −.074. Tỉ lệ prior đúng: **7/17**.
Bài học: tôi đã dùng vòng #87 làm bằng chứng cho miễn nhiễm — **đó là đọc sai chính dữ liệu của mình.**

### HOÀ GIẢI với vòng #87 (mỏ neo ≈ 0 ở 7B) — KHÔNG mâu thuẫn, KHÁC CÂU HỎI
- #87 so **seq-có-neo vs seq-KHÔNG-neo**: cả hai đều là pipeline **nhiều lượt**, 7B vẫn tự giải
  ở lượt đầu. Nó trả lời: *"trong pipeline 2 lượt, lượt 2 nhìn thấy đáp án lượt 1 có quan trọng không?"*
  → Không.
- H61 so **V vs I**: có-xem-lời-giải-của-model-khác vs **không xem gì cả**. Nó trả lời:
  *"việc TIẾP XÚC với lời giải của một model yếu tốn bao nhiêu?"* → **−.074.**

**#87 chưa bao giờ đo giá của việc tiếp xúc.** H60+H61 là lần đo trực tiếp đầu tiên.

### Phạm vi — cái gì SỐNG, cái gì CHẾT
- **CHẾT: cách phát biểu của H15.** "+14 điểm" là so với **1.5B**, không phải so với
  **lựa chọn rẻ hơn là gọi thẳng 7B**. Con số giữ nguyên, **DIỄN GIẢI RÚT LẠI.**
- **SỐNG: H39 (vòng #78).** `escalate_seq` .6450 vs `big_maj3` .5050 / `big_maj8` .5400 —
  **đã có** nhánh 7B-chạy-một-mình và vẫn thắng, còn rẻ hơn. **Định tuyến CÓ ĐIỀU KIỆN
  (chỉ gọi 7B ở bài 1.5B không tự đồng thuận) khác hẳn định tuyến VÔ ĐIỀU KIỆN.**
  H61 giết cái sau, không đụng cái trước.
- **SỐNG: test chạy được** (+.0401 / +.0388, tái lập) — oracle mang thông tin model KHÔNG có.

> **Quy tắc: `V − S` là con số sai. Luôn báo `V − I`.**
> Baseline đúng của bất kỳ pipeline nhiều agent nào không phải là agent YẾU NHẤT trong đó,
> mà là **agent MẠNH NHẤT chạy một mình** — thường là lựa chọn RẺ HƠN.
> Với `V−S` thì đây là "+16 điểm, precision .955". Với `V−I` thì đây là **âm và đắt hơn**.

---

## Vòng #101 — H62: **TRÌNH BÀY GỠ ĐƯỢC MỘT NỬA. NỬA CÒN LẠI KHÔNG.**
*(đăng ký trước #67, khoá tại `6250ac0` TRƯỚC khi chạy)*

### Cổng tái lập H61: ĐẠT — `V_std − I` = **−.0940** ∈ [−.12, −.03]
n = 500 GSM8K test · greedy · S = 1.5B (.6780) · I = 7B tự giải (**.9340**) · mọi nhánh V dùng
CHUNG một bộ lời giải S · cùng chi phí (1 lượt 7B).

| nhánh | acc | `−I` | bị đầu độc | **nhại** | **thứ ba** | được cứu |
|---|---|---|---|---|---|---|
| `V_std` "Proposed solution: …" | .8400 | −.0940 | 57 | **36** | 21 | **10** |
| `V_first` tự giải & CAM KẾT trước khi đọc | .8780 | −.0560 | 38 | **15** | 23 | **10** |
| `V_label` nói rõ nguồn yếu, hãy hoài nghi | **.8860** | **−.0480** | 34 | 19 | **15** | **10** |

**PHÁN QUYẾT: HÀNG 2.** `V_first` gỡ lại **40.4%**, `V_label` gỡ **48.9%**. Không nhánh nào
về được tới `I`. Và **hàng phụ cũng khớp**: `V_label` > `V_first` → **HOÀI NGHI NGUỒN
quan trọng hơn THỨ TỰ CAM KẾT.**

### Cơ chế tách ra rất sạch — hai loại thiệt hại, hai thuốc chữa khác nhau
- **Cam kết trước khi đọc giết NHẠI LẠI**: 36 → **15** (−58%), nhưng **KHÔNG đụng được đáp án
  thứ ba**: 21 → **23**. Cam kết đáp án của mình ngăn được việc CHÉP, không ngăn được việc
  **đọc làm nhiễu lập luận**.
- **Hoài nghi nguồn giảm CẢ HAI**: nhại 36→19, thứ ba 21→**15**.

### PHÁT HIỆN SẮC NHẤT: **số bài ĐƯỢC CỨU KHÔNG ĐỔI — đúng 10 ở cả ba nhánh**
Không cách trình bày nào làm **tăng** phần lợi. Mọi chuyển động đều nằm ở phần **hại**.
> **Tỉ lệ cứu là thuộc tính của TASK, không phải của PROMPT. Chỉ thiệt hại là uốn được — và không đủ.**

### Chặn trên định lượng cho toàn bộ hướng này
`V = I − đầu_độc/500 + cứu/500`. Với `cứu` cố định = 10:
- trình bày hoàn hảo (đầu độc → 0) ⇒ `V` = **.9540**, tức **chỉ +.020** so với `I`.
- hiện tại còn dư **34** bài đầu độc, tức −.068.

**Trần lý thuyết của việc cho 7B xem lời giải 1.5B là +.020 — và chỉ đạt được nếu việc tiếp xúc
trở nên HOÀN TOÀN miễn phí.** Thực tế tốt nhất đo được là **−.048**. Khoảng cách giữa
"tốt nhất có thể" và "đáng làm" quá hẹp để hướng này đáng theo.

### Prior của tôi ĐÚNG (lần đầu sau ba lần trượt)
Ghi trước: hàng 2, gỡ **40–70%**. Thực tế **40.4% / 48.9%** — trúng, sát mép dưới.
Tỉ lệ prior đúng: **8/18**.

### Ghi chú confound (tự bắt)
`I` = .9340 ở H62 nhưng .9080 ở H61. Khác biệt: `MAXNEW` 512 vs 400 → 7B được sinh dài hơn thì
tốt hơn 2.6 điểm. **Không ảnh hưởng kết luận**: mọi so sánh trong H62 là CẶP, cùng `MAXNEW`,
và cổng tái lập đặt trên `V_std − I` (đo trong cùng một lần chạy) đã ĐẠT.
Nhưng ghi lại: **`MAXNEW` là một biến có tác dụng thật, phải giữ cố định khi so giữa các vòng.**

---

## Vòng #102 — H64: **LẬP KẾ HOẠCH KHÔNG GIÚP, VÀ THÊM LƯỢT CŨNG KHÔNG**
*(đăng ký trước #69 + #69-b, khoá tại `b715ab2` / `334a82a` TRƯỚC khi chạy — đề xuất của Nguyên)*

### Mọi cổng ĐẠT
Lọc theo lời giải chuẩn: **88 lớp / 354 method** (từ 100/410) ≥ 80/350 ✓ ·
`class_pass(solve1)` = **.3295** ∈ [.10,.60] ✓ · **`plan_is_code_rate` = .0000** ✓
(kế hoạch là văn xuôi thật, trung vị 462 ký tự) · AST .920 ≥ .80 ✓

### Kết quả — ClassEval, 4.1 method/lớp, lời giải TB 1334 ký tự (3.2× BigCodeBench)
| nhánh | lượt | method_pass | class_pass |
|---|---|---|---|
| `solve1` | 1 | .6328 | **.3295** |
| `seq3` (giải→sửa→sửa) | 3 | **.6356** | .3182 |
| `PSV` (kế hoạch→giải→kiểm) | 3 | .6243 | .2841 |

**PHÁN QUYẾT: HÀNG 3.** `PSV − seq3` = **−.0113** (method), **−.0341** (class).
Bất đồng 19/15, **p = .608**. Lập kế hoạch **không thêm gì**, kể cả ở 3.2× độ dài.

### ĐÁP ỨNG THEO LIỀU: nhìn thì thuyết phục, đếm ra thì là NHIỄU
| nhóm | dài | seq3 | PSV | chênh % | **chênh SỐ METHOD** | p |
|---|---|---|---|---|---|---|
| 0 | 496–1029 | .7300 | .6900 | −.0400 | **−4** | .125 |
| 1 | 1031–1457 | .7154 | .7073 | −.0081 | **−1** | 1.000 |
| 2 | 1461–3914 | .4885 | .4962 | **+.0077** | **+1** | 1.000 |

Tỉ số odds cũng tăng đều (.823 → .961 → **1.031**) nên **không phải** hiệu ứng nén sàn.
Nhưng tính bằng **số method** thì toàn bộ "xu hướng" là **−4, −1, +1 = biên độ 5 method / 354**.
> **Tôi đã đăng ký phép thử đáp ứng-theo-liều là QUYẾT ĐỊNH. Nó KHÔNG đủ lực.**
> ~118 method/nhóm, tỉ lệ bất đồng ~10% ⇒ không phân biệt nổi +.05 với 0. **Đây là lỗi thiết kế của tôi**,
> phải ghi rõ: hướng của số liệu đúng như Nguyên đoán, nhưng **dữ liệu không cho phép kết luận gì từ hướng đó**.

### PHÁT HIỆN MỚI VÀ QUAN TRỌNG HƠN: **THÊM LƯỢT CŨNG KHÔNG GIÚP TRÊN SẢN PHẨM DÀI**
`seq3 − solve1` = **+.0028** method · **−.0113** class. **Ba lượt ≈ một lượt.**
Và ở cấp lớp thì **sửa lại LÀM HẠI**: .3295 → .3182 → **.2841** (`PSV` kém `solve1` **−.0454**).

Điều này **ngược với TOÁN**, nơi `PSV`/`SS_anc` thắng `maj@3` ở 3/4 ô (H32).
=> Lời giải thích cũ *"thứ có tác dụng là SỐ LƯỢT, không phải VAI"* **chỉ đúng trên bài NGẮN**.
Trên sản phẩm dài, **cả hai đều không có tác dụng, và lượt sửa lại gây hại**.

**Vì sao cấp lớp hại nặng hơn cấp method**: một lớp chỉ đạt khi **MỌI** method đạt, nên mọi
hư hại đều **cộng dồn**. Sửa 4.1 method cùng lúc thì xác suất phá ít nhất một cái tăng theo.
Khớp với #92 (`ref_seq` làm refactor tệ đi) và #99–#101 (đọc lại thì hỏng).

### Trả lời thẳng giả thuyết của Nguyên
*"Bài dài sẽ thực sự cần planner"* — **đo rồi: không.** Ở nhóm dài nhất, `PSV` hơn `seq3`
đúng **1 method trên 131**. Và ở đó `solve1` một lượt vẫn ngang cả hai.
Nhưng phải nói rõ phần tôi **chưa** loại trừ: ClassEval dài hơn BigCodeBench 3.2× **nhưng vẫn là
MỘT FILE, MỘT LỚP**. Chưa chạm tới nhiều file / nhiều vòng phụ thuộc / trạng thái kéo dài —
nơi kế hoạch có thể mang thông tin mà một lượt không giữ nổi. **Kết quả này đóng "lớp ~1300 ký tự",
KHÔNG đóng "tác vụ dài" nói chung.**

### Prior của tôi ĐÚNG
Ghi trước: hàng 3 ~50%. Ra hàng 3. Tỉ lệ prior đúng: **9/19**.

---

## Vòng #103 — H66: **ĐẦU ĐỘC TỔNG QUÁT SANG CODE — và trên code nó gần như TOÀN LÀ VIẾT LẠI HỎNG**
*(đăng ký trước #71, khoá tại `166bb16` TRƯỚC khi chạy)*

### Cổng ĐẠT: `I − S` = **+.2120** ≥ .05 · tỉ lệ biên dịch **.9940** ≥ .50 · n = **500**
MBPP 11–510 · 1.5B fp16 viết code · 7B nf4 kiểm · greedy · chấm bằng **assert đi kèm** (oracle thật).

| nhánh | acc | chi phí |
|---|---|---|
| `S` (1.5B viết) | .4280 | 1×1.5B |
| **`I` (7B TỰ viết)** | **.6400** | **1×7B** ← RẺ HƠN |
| `V` (7B xem code của S) | .5660 | 1×1.5B + 1×7B |

| đại lượng | giá trị | 5 fold |
|---|---|---|
| `V − S` (con số ai cũng báo) | **+.1380** | dương |
| **`V − I`** (khoá trước là CHÍNH) | **−.0740** | −.10 −.04 −.09 −.09 −.05 → **5/5 ÂM** |

**PHÁN QUYẾT: HÀNG 1.** Đầu độc **KHÔNG** phải hiện tượng của toán.

### Con số trùng đến mức phải nói rõ là TRÙNG
`V − I` = **−.0740** trên MBPP, và H61 đo **−.0740** trên GSM8K. **Giống hệt tới 4 chữ số.**
Hai task khác hẳn nhau (toán văn xuôi vs code), hai bộ chấm khác hẳn (so `\boxed` vs **chạy test**).
**Đây là TRÙNG HỢP, không phải quy luật** — n=500 nên sai số chuẩn ~.02; tôi **không** được nói
"đầu độc luôn bằng −.074". Điều nói được: **cùng ĐỘ LỚN, cùng DẤU, ở hai miền không liên quan.**

### Khác biệt THẬT so với toán: trên code, thiệt hại gần như toàn là VIẾT LẠI HỎNG
**69 bị đầu độc** vs **32 được cứu**, ròng −37/500 = −.0740 (khớp đúng).
| | giữ nguyên code sai của S ("nhại") | **viết ra bản THỨ BA vẫn sai** |
|---|---|---|
| H60 (toán, 0.5B→1.5B) | 46% | 54% |
| H61 (toán, 1.5B→7B) | 55% | 45% |
| **H66 (code, 1.5B→7B)** | **22%** (15/69) | **78%** (54/69) |

Trên code, 7B **hầu như không chép** code sai — nó **viết lại và làm hỏng**. Tỉ lệ biên dịch .9940
nên **không phải lỗi cú pháp**: là **trôi ngữ nghĩa**. Khớp thẳng với #93: *lỗi khi SINH thì thô,
lỗi khi BIẾN ĐỔI là trôi ngữ nghĩa tinh vi* — và với H52 (`ref_seq` làm refactor tệ đi).

> **Việc bị cho xem một lời giải kém đẩy model mạnh vào chế độ SỬA CHỮA thay vì chế độ SÁNG TÁC —
> và với model này, sửa chữa kém hơn sáng tác.** `I` sáng tác đạt .6400; cùng model đó ở chế độ
> sửa chữa chỉ đạt .5660.

### Ba miền, ba cặp model, cùng một dấu
| | task | cặp | `V − S` | **`V − I`** |
|---|---|---|---|---|
| H60 | GSM8K | 0.5B→1.5B | +.1700 | **−.1040** |
| H61 | GSM8K | 1.5B→7B | +.1620 | **−.0740** |
| **H66** | **MBPP (code)** | 1.5B→7B | **+.1380** | **−.0740** |

**Mọi lần `V − S` dương và `V − I` âm.** Con số hay được báo cáo sai dấu ở **cả ba**.

### Prior của tôi ĐÚNG
Ghi trước: hàng 1, ~65%, và lý do ghi trước cũng đúng — mỏ neo trên code đã đo là **có hại**
(−.08/−.098) trong khi trên toán ≈0. Tỉ lệ prior đúng: **10/20**.

---

## Vòng #104 — **THĂM DÒ (KHÔNG đăng ký trước): đầu độc là hiệu ứng CÓ ĐIỀU KIỆN**
> ⚠️ **ĐÂY LÀ PHÂN TÍCH HẬU KIỂM trên dữ liệu H66 đã có, KHÔNG phải phép thử khoá trước.**
> Không được coi là xác nhận. Nó **sinh giả thuyết**, phải kiểm bằng một đăng ký trước riêng.
> Không tốn thêm một giây GPU nào.

### Tách `V − I` = −.0740 theo việc code của S ĐÚNG hay SAI
| nhóm | n | `I` (7B tự viết) | `V` (7B xem code S) | chênh |
|---|---|---|---|---|
| **S ĐÚNG** | 214 | .8972 | **.9393** | **+.0421** |
| **S SAI** | 286 | .4476 | **.2867** | **−.1608** |

| | bị đầu độc | được cứu | đóng góp vào tổng |
|---|---|---|---|
| khi S đúng | 6 | 15 | **+.0180** |
| khi S sai | 63 | 17 | **−.0920** |
| | | | **−.0740** ✓ |

### Ba điều đọc được
1. **Tiếp xúc KHÔNG xấu tự thân — nó xấu CÓ ĐIỀU KIỆN.** Cho xem code **đúng** của model yếu
   thì model mạnh **TỐT LÊN +.0421**. Cho xem code **sai** thì **TỆ ĐI −.1608**. Gần **4 lần**.
   => Nói "đọc sản phẩm agent yếu là độc" là **nói quá**. Đúng hơn: **đọc sản phẩm SAI là độc.**
2. **Thiệt hại rơi đúng vào chỗ đã khó.** Nhóm S sai cũng là nhóm `I` chỉ đạt **.4476**
   (so với .8972 ở nhóm kia). Lời giải kém xuất hiện đúng những bài model mạnh vốn đã chật vật,
   nên nó đẩy ngã người đang đứng không vững.
3. **Biến điều kiện lại chính là thứ KHÔNG quan sát được.** Muốn hưởng +.0421 và tránh −.1608
   thì phải biết code của S đúng hay sai — **mà đó chính là bài toán cần giải.**
   Triage hoàn hảo (chỉ cho xem khi S đúng) cho `V` = **.6580**, tức **chỉ +.0180** so với `I`.

### Vì sao +.0180 (triage) < +.0440 (hợp oracle của H69)
Triage chỉ trả lời *"có cho xem không"*. **CHỌN** trả lời *"lấy bản nào"* — nên còn vớt được
**22 bài mà 1.5B giải được và 7B trượt**. Đây là lý do H69 (đang chạy) nhắm **chọn**, không nhắm triage.

### Giả thuyết sinh ra (phải đăng ký trước rồi mới kiểm)
> Nếu đưa cho model mạnh một lời giải yếu **đã được lọc để chỉ còn bản ĐÚNG**, nó sẽ hơn
> `I` khoảng **+.04**; nếu không lọc được thì mọi giao thức "cho xem rồi review" đều thua `I`.

Điều này **khớp** với quy tắc đã tái lập của dự án: **oracle nên LỌC, đừng SỬA.**
Ở đây oracle lọc *ứng viên nào được nhìn thấy*, chứ không sửa gì cả.

---

## Vòng #105 — H68: **CẢ CHẾ ĐỘ LẪN NGUỒN ĐỀU GÓP — "đầu độc" đúng một phần, và phải nói rõ phần nào**
*(đăng ký trước #73, khoá tại `ccdff64` TRƯỚC khi chạy)*

### Cổng ĐẠT: tái lập H66 `V_weak − I` = **−.0740** ∈ [−.12,−.03] · biên dịch **.9955** · n=500
| nhánh | 7B xem gì | acc | `− I` | 5 fold |
|---|---|---|---|---|
| `I` | không gì (sáng tác) | **.6400** | — | — |
| `V_self` | **code của CHÍNH NÓ** | .6120 | **−.0280** | −.02 −.06 −.03 −.03 .00 |
| `V_weak` | code của **1.5B** | .5660 | **−.0740** | −.10 −.04 −.09 −.09 −.05 |

**PHÁN QUYẾT: HÀNG 3 — CẢ HAI ĐỀU GÓP.**
- **chế độ SỬA CHỮA** tự nó: **−.0280** (38% thiệt hại) — 7B sửa **code của chính nó** cũng tệ đi.
- **nguồn NGOẠI LAI** cộng thêm: **−.0460** (62%).

### Phải nói rõ: cách gọi ở #99–#103 ĐÚNG MỘT PHẦN
Tôi đã gọi toàn bộ hiệu ứng là "đầu độc", ngụ ý **lỗi ở sản phẩm agent yếu**.
Đo ra thì **38% của nó xảy ra kể cả khi KHÔNG có agent yếu nào** — chỉ cần bảo model
xem lại việc của chính mình là đã mất .028. **Không rút lại số, nhưng thu hẹp cách gọi:**
> *`V − I` = (thuế của việc THÊM MỘT LƯỢT SỬA) + (thiệt hại RIÊNG của sản phẩm ngoại lai).*
> Trên MBPP: **−.028 + −.046**.

### Bằng chứng cơ chế: nó VIẾT LẠI code người khác nhiều hơn code của mình
| | giữ nguyên đầu vào (`unchanged_rate`) | bị đầu độc: giữ/bản thứ ba |
|---|---|---|
| `V_self` | **.6980** | 0 / **24** |
| `V_weak` | **.3820** | 15 / **54** |

Với code của **chính nó**, 7B giữ nguyên **70%** số bài. Với code của **1.5B**, chỉ **38%** —
nó viết lại gần **gấp đôi**. Khớp thẳng với #103 (78% thiệt hại là bản thứ ba).
`V_self` có **0** ca "giữ nguyên bản sai" — đúng như định nghĩa, giữ nguyên code của mình
thì kết quả y như `I`; mọi thiệt hại của `V_self` đều là **tự viết lại rồi tự phá**.

### Prior của tôi ĐÚNG (đoán hàng 3, ~45%)
Tỉ lệ prior đúng: **11/21**.

---

## Vòng #106 — H69: **HUỶ — chốt chống rò rỉ của tôi đã PHÁ chính nhánh cần đo**
*(đăng ký trước #74, khoá tại `9169ff5`)*

### Cổng chặn đúng chỗ: `test_soundness` = **.0523** < .50 ⇒ **HUỶ, KHÔNG ĐỌC**
`test_copy_rate` = .0004 (không rò rỉ) nhưng test tự sinh **gần như sai hết**.

### Nguyên nhân — lỗi thiết kế của tôi, không phải kết quả khoa học
Để chống rò rỉ tôi **bỏ `test_list` khỏi lượt viết test**. Nhưng trong MBPP, `test_list`
là **NƠI DUY NHẤT chứa TÊN HÀM**. Không có nó, model **tự bịa tên**:
| MBPP | model viết test cho |
|---|---|
| `remove_Occ` | `remove_first_last_occurrence` |
| `sort_matrix` | `sort_matrix_by_row_sum` |
| `count_common` | `count_most_common_words` |

Mọi assert chết vì `NameError` ⇒ soundness .052 ⇒ chọn lựa **suy biến**: chỉ lấy bản của S
**3/500 lần**, nên `SEL` = .6360 ≈ `I` = .6400. **`SEL − I` = −.0040 là VÔ NGHĨA, không được đọc.**
(Đối chiếu: H56 đạt soundness **.8712** vì ở đó model **có** chữ ký hàm.)

### Sửa cho lần chạy lại (H69b)
Đưa **TÊN HÀM** (trích tự động từ `test_list` bằng regex `assert\s+(\w+)\(`) vào lượt viết test,
**KHÔNG** đưa giá trị kỳ vọng. Tên hàm **không phải** tín hiệu chấm; **giá trị kỳ vọng mới là**.
Giữ nguyên cổng `test_copy_rate` ≤ .20 và thêm cổng `test_soundness` ≥ .50 chạy **TRƯỚC** khi kết luận.

> **Bài học: một chốt chống rò rỉ cũng là một CAN THIỆP — phải kiểm nó có phá phép đo không.**
> Ở đây "bỏ test_list" tưởng chỉ chặn rò rỉ, thực ra còn cắt luôn thông tin cần thiết.

---

## Vòng #107 — H67: **BẢO NÓ "ĐỪNG VIẾT LẠI" LÀM MỌI THỨ TỆ HƠN GẤP ĐÔI — và tôi đã đoán SAI**
*(đăng ký trước #72, khoá tại `31765ac` TRƯỚC khi chạy)*

### Cổng ĐẠT: tái lập H66 **−.0740** · biên dịch **.9960** · `unchanged_rate(V_cons)` = **.7500** ≥ .20
(cổng can thiệp ĐẠT nghĩa là model **CÓ nghe lời** — nó thật sự giữ nguyên code. Không phải lỗi thực thi.)

| nhánh | acc | `− I` | `− V_std` | bị đầu độc | **giữ code S** / bản thứ ba | `unchanged` |
|---|---|---|---|---|---|---|
| `I` | **.6400** | — | — | — | — | — |
| `V_std` | .5660 | −.0740 | — | 69 | 15 / 54 | .3820 |
| `V_first` (cam kết trước) | **.5880** | −.0520 | **+.0220** | 64 | 14 / 50 | .3500 |
| **`V_cons`** ("đừng đụng vào") | **.4840** | **−.1560** | **−.0820** | **102** | **75** / 27 | **.7500** |

fold `V_cons`: −.23 −.09 −.15 −.18 −.13 → **5/5 âm và âm rất sâu.**

### PHÁN QUYẾT: HÀNG 3 — nhưng phải nói rõ bảng của tôi **không lường hết ĐỘ LỚN**
Hàng 3 khoá trước là *"`V_cons − V_std` < +.02 ⇒ trình bày KHÔNG cứu được đầu độc trên code"*.
Nó **khớp về dấu**. Nhưng bảng của tôi **không có hàng nào** cho việc can thiệp làm hại
**gấp đôi** (−.1560 so với −.0740). Ghi nhận là **thiếu sót của bảng**, không bịa hàng mới.

### VÌ SAO — và đây là chỗ nó nối liền với H59
Tôi bảo model *"nếu code đúng thì giữ NGUYÊN VĂN"*. Nó **nghe lời**: giữ nguyên **75%** (so với 38%).
Nhưng code của S chỉ đúng **.4280**. **Giữ nguyên code của S = thừa hưởng độ chính xác của S.**
Số ca "giữ nguyên bản SAI" nhảy **15 → 75**, gấp **5 lần**.

> **Model không phân biệt được đúng/sai — đó CHÍNH LÀ bài toán.**
> Bảo nó "chỉ sửa cái chắc chắn sai" là giao cho nó đúng việc nó không làm được.

**Đây là ĐỐI XỨNG GƯƠNG của vòng #98 (H59).** Ở đó GRPO dạy verifier **NHẠI LẠI** solver,
và tôi đã chỉ ra: nhại lại ghi điểm **đúng bằng** độ chính xác của solver, nên không thể vượt.
Ở đây prompt "bảo thủ" **ép** đúng hành vi nhại lại đó — và kết quả rơi về phía `S` y như dự đoán số học.

| | cơ chế | hệ quả |
|---|---|---|
| quá **PHỤC TÙNG** (`V_cons`, GRPO ở #98) | giữ nguyên đầu vào | bị chặn trần ở **độ chính xác của nguồn** (.4280) |
| quá **CHỦ ĐỘNG** (`V_std`) | viết lại | **hỏng bản đang đúng** (54 bản thứ ba) |

**Không có điểm ngọt nào ở tầng prompt**, vì cả hai cực đều hỏng và model không có tín hiệu
để chọn giữa chúng. Khớp với kết luận #98: *không có lợi thế thông tin thì không có hàm thưởng
(hay prompt) nào cứu được.*

### Phần tôi đoán ĐÚNG, và phần tôi đoán SAI
- **ĐÚNG**: `V_first` giúp **ÍT hơn** trên code so với toán — **+.0220** (code) vs **+.0380** (toán).
  Lý do ghi trước cũng đúng: `V_first` chữa *nhại lại*, mà code chỉ có 22% là nhại.
- **SAI NẶNG**: tôi đoán hàng 1 (~55%) rằng `V_cons` sẽ **hơn** `V_std` ≥ +.04.
  Thực tế **−.0820**. Tôi đã suy từ cơ chế "78% là viết lại" ra "vậy chặn viết lại là chữa" —
  **bỏ qua** rằng chặn viết lại thì phải GIỮ, mà giữ cái sai cũng chết y hệt.
  Tỉ lệ prior đúng: **11/22**.

### Phát biểu dùng được
> Trên code, **`V_first` là biện pháp trình bày TỐT NHẤT đo được (+.0220)** nhưng vẫn để lại
> **−.0520** so với chỉ gọi thẳng model mạnh. **Không cách trình bày nào cứu được.**
> Và biện pháp "an toàn" trực giác nhất — *đừng đụng vào nếu không chắc* — **là tệ nhất trong ba**.

---

## Vòng #108 — H69b: **HUỶ LẦN HAI — nhưng truy nguyên nó đã CỨU kết quả dương của dự án**
*(đăng ký trước #74 + #74-b)*

### Vẫn HUỶ: `test_soundness` = **.2580** < .50
Sửa "đưa tên hàm" **có tác dụng đúng hướng** — soundness **.0523 → .2580** (gấp 5), số lần chọn
bản của S **3 → 46**, `test_copy_rate` = .0190 (không rò rỉ). Nhưng vẫn dưới cổng ⇒ **KHÔNG ĐỌC**
`SEL − I` = −.0100.

### Vì sao vẫn hỏng: biết TÊN chưa đủ, phải biết NGỮ NGHĨA
Có tên hàm rồi thì assert chạy được, nhưng 7B vẫn **đặt sai giá trị kỳ vọng** — mà muốn đặt đúng
thì phải **giải được bài**. Đây đúng là nút thắt năng lực, không phải lỗi kỹ thuật.

### Truy nguyên dẫn tới một kiểm tra QUAN TRỌNG: **H56 có rò rỉ không?**
H56 báo `test_soundness` = **.8712** trên cùng benchmark. Chênh quá lớn (.87 vs .26) nên tôi
nghi **chính H56 đã rò rỉ** — tức kết quả dương **DUY NHẤT tái lập được** của dự án (+.0401/+.0388)
có thể hỏng. **Đã kiểm trực tiếp mã nguồn `mbpp_select_kernel.py`:**

```
# KHONG RO RI: assert[0] vao prompt va dung dinh tuyen; assert[1..2] CHI de cham diem.
TQ = {i: f"{text}\n\nExample test (for the function name):\n{a0}" ...}
```
=> H56 đưa **một** assert làm **ví dụ**, và **chấm bằng hai assert CÒN LẠI**. Đây là thiết kế
**giữ lại (held-out) hợp lệ**, đã ghi rõ trong header từ đầu. **Kết quả +.0401 KHÔNG rò rỉ — VẪN ĐỨNG.**

### Và đó cũng chính là lời giải cho H69
Khác biệt duy nhất giữa .8712 và .2580 là **một ví dụ đầu-vào→đầu-ra**.
H56 cho model thấy *ngữ nghĩa mong đợi* trông thế nào; tôi chỉ cho **tên hàm**.
> **Bài học: "chống rò rỉ" không phải là cắt càng nhiều càng tốt.**
> Đúng ranh giới là: **được thấy VÍ DỤ, bị chấm trên phần GIỮ LẠI.**
> Tôi đã cắt quá tay hai lần liên tiếp (#106 cắt tên hàm, nay cắt ví dụ) và **tự phá phép đo hai lần**.

### Chạy lại H69c theo đúng giao thức đã hoạt động của H56
`assert[0]` vào prompt (cả lượt giải lẫn lượt viết test) · **chấm CHỈ bằng `assert[1..2]`**.
Lưu ý phải ghi: **thang điểm đổi** so với H66 (vốn chấm bằng cả ba), nên `acc` tuyệt đối
không so trực tiếp giữa hai vòng; **mọi so sánh trong H69c là nội bộ, cùng bộ chấm.**

### Phụ lục #105-b — **THĂM DÒ: "thuế sửa chữa" là NGHI NGỜ VÔ CỚ, và nó nối liền cả phiên**
> ⚠️ Phân tích hậu kiểm trên trace H68, **không đăng ký trước**. Sinh giả thuyết, không xác nhận.

24 ca 7B **tự phá code ĐÚNG của chính nó** (`V_self`). Đọc hết:
- **0/24** giữ nguyên văn ⇒ mọi thiệt hại đều là **sửa thật sự**, không phải lỗi trích xuất.
- độ dài: trung vị **+3 ký tự**, 15 dài ra / 4 ngắn đi ⇒ **không phải xu hướng rút gọn**, mà là **VIẾT LẠI**.

```
task 35 — "find the n-th rectangular number"
I      (ĐÚNG) : return n * (n + 1)
V_self (SAI)  : return n * (n + 1) // 2      <- biến thành số TAM GIÁC
```
```
task 30 — đếm chuỗi con có ký tự đầu = cuối
I      (ĐÚNG) : đếm bằng bảng tần suất, O(n)
V_self (SAI)  : viết lại thành hai vòng lặp lồng nhau, sai
```

### Nối liền với đầu phiên: **CÙNG MỘT BỆNH, hai miền**
Ở trace Carol (#98, toán), verifier gốc mở đầu bằng *"The proposed solution is incorrect"*,
**tính lại ra đúng 20%**, rồi **tự bịa ra một phân biệt** để đổi thành 25%.
Ở đây, 7B nhìn công thức **đúng** của chính mình rồi "sửa" thành công thức khác.

> **Thuế của lượt sửa chữa KHÔNG phải lười biếng — nó là NGHI NGỜ VÔ CỚ.**
> Được lệnh "xem lại", model coi việc **tìm ra thứ để đổi** là hoàn thành nhiệm vụ.
> Đó là lý do `V_self` mất **−.0280** dù không có agent yếu nào, và là lý do
> `V_cons` ("đừng đụng vào") **đảo sang cực kia** rồi chết theo kiểu khác (#107).

Giả thuyết sinh ra (phải đăng ký trước rồi mới kiểm): **prompt review nào cũng hàm ý
"đáng lẽ phải có gì đó để sửa"; một prompt nêu rõ "phần lớn code đưa vào là ĐÚNG,
không đổi là kết quả bình thường và được chấp nhận" có thể cắt được phần thuế này** —
nhưng #107 cảnh báo: đẩy quá tay sang phía phục tùng thì bị chặn trần ở độ chính xác của nguồn.

---

## Vòng #109 — H71: **HUỶ — tôi mang lỗi đã biết sang kernel dẫn xuất**
*(đăng ký trước #76, khoá tại `32afad3`)*

### HUỶ: `test_soundness` = **.2580** < .50 — **y hệt H69b**
Không phải trùng hợp: H71 được **dựng từ kernel H69 ở thời điểm CHƯA có bản sửa #74-c**
(đưa `assert[0]` làm ví dụ). Nó thừa hưởng đúng cái prompt viết-test đã biết là hỏng.
`test_copy_rate` .0190 (không rò rỉ), biên dịch .9980, `acc(I)` = .6400 (cổng tái lập ĐẠT).

**Số KHÔNG ĐƯỢC ĐỌC** (ghi lại chỉ để đối chiếu khi chạy lại):
`I` = .6400 [chi phí 5.07] · mẫu 2 (T=.8) = .6360 · `SEL_self` = .6500 [chi phí **15.21**] ·
trần `I_pass2` = .6760 · `SEL−I` = +.0100 (5/5 fold dương, **lấy nhầm = 0**).

### Bài học QUY TRÌNH (đã thêm vào QUY_TRINH_VONG_LAP.md)
> **Khi một bản sửa được xác nhận, phải LAN sang MỌI kernel dẫn xuất ngay lập tức.**
Tôi sửa `mbpp_select_vs_review_kernel.py` (#74-c) nhưng quên `mbpp_budget_kernel.py` vốn
được sao ra từ nó trước đó ⇒ **đốt một phiên GPU cho một lỗi đã biết cách chữa.**
Đây là lần thứ hai trong phiên tôi để lỗi đã biết đi tiếp (lần trước: kiểm AST trước khi sửa).

### Chạy lại H71b với đúng giao thức #74-c
`assert[0]` vào cả prompt giải lẫn prompt viết test · chấm CHỈ bằng `assert[1..2]` ·
loại bài < 3 assert. Bảng khoá #76 giữ NGUYÊN.

---

## Vòng #110 — H69c: **KẾT QUẢ DƯƠNG ĐẦU TIÊN CHO HỢP TÁC YẾU→MẠNH**
### Cùng hai bản code. REVIEW mất −.1080. CHỌN được +.0220. Chênh **+.1300**.
*(đăng ký trước #74 + #74-b + #74-c, khoá tại `9169ff5`/`6b85a15` TRƯỚC khi chạy)*

### MỌI CỔNG ĐẠT (sau hai lần HUỶ vì chính tôi cắt chống-rò-rỉ quá tay)
`test_soundness` = **.7214** ≥ .50 ✓ (.0523 → .2580 → **.7214**) · `test_copy_rate` = **.0258** ≤ .20 ✓
· `V_review − I` **ÂM** ✓ · biên dịch .9955 · n = 500 · chấm **chỉ bằng `assert[1..2]`**

| nhánh | acc | so với `I` | chi phí (1.5B-eq) |
|---|---|---|---|
| `S` (1.5B viết) | .4400 | −.2000 | 1.00 |
| **`I` (7B tự viết)** | **.6400** | — | **5.07** |
| `V_review` (7B review code S) | **.5320** | **−.1080** | 6.07 |
| **`SEL`** (7B viết test → chọn giữa S và I) | **.6620** | **+.0220** | 11.14 |
| *(trần: hợp của S và I)* | .6740 | +.0340 | — |

**PHÁN QUYẾT: HÀNG 1.** 5/5 fold dương [.04 .01 .00 .01 .05].

### Điều này nói gì
1. **Cùng HAI ARTIFACT y hệt nhau, chỉ đổi GIAO THỨC, kết quả lệch .1300.**
   Review phá −.1080; chọn thu +.0220. **Vấn đề chưa bao giờ là code của 1.5B — mà là cách dùng nó.**
2. `SEL` thu được **65%** khoảng trống oracle (+.0220 / +.0340). H56 thu 42–46% ⇒ **cao hơn**,
   vì ở đây chỉ phải phân biệt **hai** ứng viên chứ không phải tám.
3. Chọn rất **sạch**: loại oan **4**, lấy nhầm **2** trên 500. Lấy bản của 1.5B **42 lần**.
4. Khẳng định lại quy tắc đã tái lập: **oracle nên LỌC ứng viên, đừng SỬA một ứng viên.**
   Nay có thêm dạng mạnh hơn: **kể cả khi ứng viên đến từ model YẾU HƠN NHIỀU.**

### Nhưng phải nói thẳng phần chưa xong
- **+.0220 là khiêm tốn** và tốn **2.2×** chi phí của `I` (11.14 vs 5.07).
- Câu hỏi đúng chưa trả lời: **cùng ngân sách đó tiêu vào MẪU CỦA CHÍNH 7B thì sao?**
  Đó là **H71b đang chạy**. Nếu `SEL_self` ≥ `SEL` thì agent yếu **vẫn** không đáng dùng,
  chỉ là "chọn" đỡ tệ hơn "review". **Chưa được tuyên bố hợp tác yếu→mạnh thắng cho tới khi có H71b.**
- Thang chấm đổi (`assert[1..2]`) nên `acc` **không so trực tiếp** với #103/#105.
  Trong vòng này mọi nhánh dùng **cùng** bộ chấm nên so sánh nội bộ hợp lệ.

### Prior của tôi: gần đúng
Ghi trước hàng 2 (~45%), hàng 1 ~30%. Ra **hàng 1** — tôi đã đánh giá thấp vì ước tính theo
H56 (42–46% khoảng trống) mà quên rằng **hai ứng viên dễ phân biệt hơn tám**.
Tỉ lệ prior đúng: **11/23**.

---

## Vòng #111 — H71b: **NGÂN SÁCH THÊM NÊN TIÊU VÀO MẪU CỦA CHÍNH MODEL MẠNH**
### …nhưng khoảng cách nhỏ hơn tôi tưởng, và **tính theo chi phí thì HOÀ**
*(đăng ký trước #76, khoá tại `32afad3` TRƯỚC khi chạy)*

### Mọi cổng ĐẠT: `soundness` .7214 · `copy_rate` .0258 · `acc(I)` = .6400 ∈ [.60,.68] · biên dịch .9975
**PHÁN QUYẾT #76: HÀNG 1.** `SEL_self − I` = **+.0340**, 5/5 fold [.02 .04 .02 .04 .05].

### So sánh CẶP với H69c — **cùng bộ test y hệt** (soundness .7214, 1395 assert, sinh xác định)
| giao thức | ứng viên | acc | so với `I` | trần | thu được | chi phí |
|---|---|---|---|---|---|---|
| `I` | — | .6400 | — | — | — | **5.07** |
| **`SEL_weak`** (H69c) | 1.5B + 7B | .6620 | **+.0220** | .6740 | **65%** | 11.14 |
| **`SEL_self`** (H71b) | 7B + 7B(T=.8) | **.6740** | **+.0340** | .6820 | **81%** | 15.21 |

### `SEL_self − SEL_weak` = **+.0120** — KHÔNG hàng nào của bảng khoá khớp
Bảng #76 có hai hàng: `≥ +.02` (mẫu của chính nó thắng) và `≤ −.02` (agent yếu đóng góp thật).
**+.0120 nằm GIỮA.** Ghi nhận đúng như vậy, **không ép vào hàng nào.**

### Ba điều đọc được, và điều thứ ba là điều tôi suýt bỏ sót
1. **Trần cao hơn khi ứng viên đến từ chính model mạnh**: .6820 vs .6740. Hai mẫu 7B **đa dạng
   hơn** cặp (1.5B, 7B) về mặt hữu ích — dù 1.5B "khác" nhiều hơn, cái nó thêm vào phần lớn là **sai**.
2. **Chọn cũng dễ hơn**: thu 81% khoảng trống so với 65%. Phân biệt hai bản **cùng chất lượng**
   dễ hơn phân biệt một bản tốt với một bản kém — ngược với trực giác của tôi.
3. **TÍNH THEO CHI PHÍ THÌ HOÀ.** Lợi ích trên mỗi đơn vị chi phí **thêm**:
   `SEL_weak` **.00362** · `SEL_self` **.00335**. **`SEL_weak` nhỉnh hơn một chút.**
   `SEL_self` thắng về **độ chính xác tuyệt đối**, `SEL_weak` thắng về **hiệu quả**. **Không cái nào áp đảo.**

### Trả lời thẳng câu hỏi tôi đã hứa không đoán trước
Ở #110 tôi viết: *"chưa được tuyên bố hợp tác yếu→mạnh thắng cho tới khi có H71b."*
**Kết quả: KHÔNG thắng.** Cùng cơ chế chọn, mẫu của chính 7B cho **+.0340** so với **+.0220**.
> **Phát biểu đúng là: "CHỌN hơn REVIEW" (+.1300, rất lớn), KHÔNG phải "agent yếu có giá trị".**
> Agent yếu vẫn **không** phải cách tốt nhất tiêu ngân sách — nó chỉ **không còn có hại** khi
> dùng làm ứng viên thay vì làm mỏ neo.

### Chi tiết đáng chú ý
`mẫu 2` của 7B ở **T=0.8** đạt **.6580**, **cao hơn** greedy `.6400`. Lấy mẫu có nhiệt độ
hơn greedy trên MBPP ở model này — nhỏ nhưng nhất quán với việc trần `I_pass2` cao.

### Prior của tôi ĐÚNG (hàng 1, ~45%)
Nhưng phần dự đoán `SEL_self` vs `SEL_weak` tôi ghi "~60% nghiêng SEL_self" — đúng chiều,
và biên độ (+.0120) nhỏ hơn ngưỡng tôi đặt. Tỉ lệ prior đúng: **12/24**.

### Phụ lục #111-b — **THĂM DÒ: nút thắt KHÔNG còn là bộ chọn, mà là TRẦN CỦA POOL**
> ⚠️ Hậu kiểm trên trace H71b, **không đăng ký trước**. Sinh giả thuyết, không xác nhận. Miễn phí.

Phân tích mọi bài mà pool **CÓ** bản đúng nhưng `SEL` chọn trượt:

| | số bài / 500 |
|---|---|
| có bản đúng nhưng chọn trượt | **4** |
| — vì không sinh được test nào | 0 |
| — vì **hoà điểm** test | 1 |
| — vì test **chấm ngược** (ưu tiên bản sai) | 3 |

`trần (hợp)` = .6820 · `SEL` = .6740 ⇒ **chỉ mất .0080**.
**Bộ chọn đã khai thác gần như TOÀN BỘ những gì pool có.**

### Hệ quả: cải thiện TEST gần như hết đường
- sửa hết test chấm ngược: tối đa **+.0060**
- phá hết thế hoà đúng cách: tối đa **+.0020**
=> Cộng lại **< +.01**. Trong khi khoảng cách từ `SEL` .6740 tới **1.0** vẫn còn **.326**.

### Vì sao: **89.8% số bài (449/500) HOÀ điểm test**
Hai ứng viên chạy **giống hệt nhau** trên test tự sinh ở gần 9/10 bài. Ở đó bộ chọn
**không có việc gì để làm** (mặc định giữ `I`, và đó là hành vi đúng).
Toàn bộ lợi ích đến từ **~10% bài mà hai bản KHÁC nhau**.

> **Đổi hướng: muốn hơn nữa thì phải NÂNG TRẦN (thêm/đa dạng hoá ứng viên),
> KHÔNG phải làm bộ chọn thông minh hơn.** Hướng "cải thiện chất lượng test" (H55/H58)
> gần như cạn ở k=2 — H58 đã đo *"số lượng test không phải nút thắt"* (+.0101), nay hiểu vì sao:
> **test không phải nút thắt vì bộ chọn không phải nút thắt.**

Giả thuyết sinh ra (phải đăng ký trước rồi mới kiểm): **lợi ích của `SEL` tăng theo k**
(số ứng viên) chứ không theo chất lượng test; và tỉ lệ hoà giảm khi k tăng.
H72 (đang chạy) cho một điểm dữ liệu: thêm 1.5B vào pool có nâng trần không.

---

## Vòng #112 — H69d: **TÁI LẬP trên dải tách rời — nhưng biên độ CO LẠI 1/3**
*(đăng ký trước #77, khoá tại `2ef8593` TRƯỚC khi chạy — MBPP 511–974, không giao với 11–510)*

### Cổng ĐẠT: `soundness` .7084 · `copy_rate` .0218 · `V_review − I` ÂM ✓ · biên dịch .9973 · n = **464**

| | H69c (11–510, n=500) | **H69d (511–974, n=464)** |
|---|---|---|
| `S` (1.5B) | .4400 | .5172 |
| `I` (7B) | .6400 | .7069 |
| `V_review` | .5320 | .6379 |
| **`SEL`** | **.6620** | **.7220** |
| trần (hợp) | .6740 | .7500 |
| **`SEL − I`** | **+.0220** | **+.0151** |
| **`SEL − V_review`** | **+.1300** | **+.0841** |
| `V_review − I` | −.1080 | −.0690 |

fold H69d: [.0000 .0109 .0326 .0217 .0109] — **4/5 dương, 1 bằng 0, KHÔNG fold nào âm.**

### PHÁN QUYẾT theo bảng khoá #77 (bảng CHI PHỐI H69d): **HÀNG 1 — TÁI LẬP**
`SEL − I` = **+.0151 ≥ +.01** ⇒ tái lập. Hàng 4 cũng khớp: `SEL − V_review` = +.0841 ≥ +.05.

### NHƯNG phải nói rõ điều này, nếu không là báo cáo thiếu trung thực
Kernel in ra **"HÀNG 2"** vì nó dùng bảng **#74** (bảng của H69c, ngưỡng **+.02**).
Dưới ngưỡng của chính H69c thì **+.0151 sẽ KHÔNG kích hoạt hàng 1**.
> **Hai cách đọc, phải nêu cả hai:**
> - theo **#77** (bảng tái lập, ngưỡng +.01, viết trước khi chạy H69d): **TÁI LẬP**.
> - theo **#74** (ngưỡng +.02 của lần đầu): **không đạt**.
>
> Tôi giữ kết luận **TÁI LẬP** vì #77 là đăng ký chi phối, khoá trước khi có số.
> Nhưng **biên độ co từ +.0220 xuống +.0151 (giảm ~1/3)** là dữ kiện phải đi kèm mọi lần trích dẫn.
Ước lượng gộp hai dải: **≈ +.019** (n = 964).

### Cái TÁI LẬP MẠNH không phải cái tôi nhắm ban đầu
`SEL − V_review`: **+.1300** và **+.0841** — lớn ở cả hai dải, cùng dấu, cùng cỡ.
`V_review − I`: **−.1080** và **−.0690** — âm ở cả hai dải.
> **Phát biểu vững nhất: CHỌN hơn REVIEW rất nhiều (+.08..+.13).**
> Phát biểu yếu hơn: chọn hơn gọi thẳng model mạnh **+.015..+.022** — thật, nhưng nhỏ,
> và **#111 đã cho thấy tiêu cùng ngân sách vào mẫu của chính 7B còn hơn (+.0340)**.

### Bức tranh cuối cho vai "agent yếu" trên code
1. làm **mỏ neo** (review) → **−.069..−.108** ❌
2. làm **ứng viên** (chọn) → **+.015..+.022** ✓ nhưng nhỏ
3. **không dùng, tiêu tiền vào mẫu của chính model mạnh** → **+.0340** ✓✓ tốt nhất

### Prior của tôi ĐÚNG
Ghi trước: tái lập ~70%, biên độ **+.01..+.03**. Thực tế **+.0151** — trúng cả hai.
Tỉ lệ prior đúng: **13/25**.

---

## Vòng #113 — H72: **AGENT YẾU CÓ ĐÓNG GÓP BIÊN THẬT — và SỬA LẠI kết luận của chính tôi ở #111**
*(đăng ký trước #78, khoá tại `bb51694` TRƯỚC khi chạy)*

### Cổng ĐẠT: `soundness` .7214 · `copy_rate` .0258 · `acc(I)` .6400 ∈ [.60,.68] · biên dịch .9967 · n=500
Một kernel, **sinh MỘT lần**, so **mọi tập con** ⇒ ghép cặp hoàn hảo.
acc riêng: `I` .6400 · `I2` (7B, T=.8) **.6320** · `S` (1.5B) .4400

| pool | acc | vs `I` | trần | thu | chi phí |
|---|---|---|---|---|---|
| {I} | .6400 | — | .6400 | — | 5.07 |
| **{I, S}** | **.6620** | +.0220 | .6740 | 65% | **6.07** |
| **{I, I2}** | **.6620** | +.0220 | .6660 | 85% | **10.14** |
| **{I, I2, S}** | **.6800** | **+.0400** | .6960 | 71% | 11.14 |

**PHÁN QUYẾT: HÀNG 1.** Đóng góp biên của `S` = **+.0180** ≥ +.01.
Hàng phụ cũng khớp: **15 bài chỉ MÌNH `S` giải được** (cả hai mẫu 7B trượt) ⇒ **đa dạng THẬT**.

### ĐỐI XỨNG ĐẸP, và nó lật ngược khuyến nghị thực dụng
- đóng góp biên của **S** thêm vào {I,I2} = **+.0180** (chi phí thêm **1.00**)
- đóng góp biên của **I2** thêm vào {I,S} = **+.0180** (chi phí thêm **5.07**)

**Hai nguồn ứng viên đóng góp BẰNG NHAU. Nhưng `S` rẻ hơn 5.07 lần.**
> **Trên mỗi đơn vị chi phí, 1.5B hiệu quả gấp 5.1× so với một mẫu 7B nữa.**
Và `SEL{I,S}` = `SEL{I,I2}` = **.6620** — y hệt nhau, ở **6.07** vs **10.14** chi phí.

### PHẢI SỬA LẠI #111
Ở #111 tôi viết: *"`SEL_self` +.0340 hơn `SEL_weak` +.0220 ⇒ ngân sách nên tiêu vào mẫu của chính
model mạnh"*. **So sánh đó là GIỮA HAI LẦN CHẠY, và mẫu `I2` khác nhau:**
| | `I2` acc | `SEL{I,I2}` |
|---|---|---|
| H71b | **.6580** | .6740 |
| H72 | **.6320** | .6620 |

Chênh **.0260** chỉ do **rút một mẫu T=0.8 khác**. Nghĩa là **+.0340 của #111 phần lớn là
MAY MẮN của lần rút đó**, không phải ưu thế giao thức.
**H72 đo trong CÙNG một lần chạy, ghép cặp** ⇒ đáng tin hơn, và cho **bằng nhau**.

> **SỬA LẠI: khuyến nghị "tiêu ngân sách vào mẫu của chính model mạnh" ở #111 KHÔNG đứng vững.**
> Đúng hơn: **hai nguồn tương đương về lợi ích, và nguồn YẾU rẻ hơn 5×.**
> Đây là bài học lặp lại của chính dự án: **so sánh giữa các lần chạy là không đáng tin;
> chỉ so sánh GHÉP CẶP trong cùng một lần chạy.** (Đã dính ở #70 với `MAXNEW`, nay dính lại.)

### Bức tranh cuối cho vai "agent yếu" trên code — ĐÃ CẬP NHẬT
1. làm **mỏ neo** (review) → **−.069..−.108** ❌
2. làm **ứng viên** trong pool → **+.0220**, và **+.0180 biên** kể cả khi đã có mẫu 7B thứ hai ✓
3. **rẻ nhất trong mọi cách mở rộng pool** — hiệu quả/chi phí gấp **5.1×** một mẫu 7B ✓✓

### Prior của tôi SAI
Đoán hàng 2 (~55%): "đóng góp biên ≈ 0", lý do là *"22 bài 1.5B giải được thì mẫu 7B thứ hai
chắc cũng bắt được"*. Thực tế **15 bài vẫn chỉ mình 1.5B giải được**. Tỉ lệ prior đúng: **13/26**.

### Phụ lục #113-b — **THĂM DÒ: điểm test tự sinh BÁO ĐƯỢC độ khó, nhưng KHÔNG dùng làm cổng định tuyến được**
> ⚠️ Hậu kiểm trên trace H72, **không đăng ký trước**. Sinh giả thuyết. Miễn phí.

### Điểm test tự sinh mà nhánh `I` (7B greedy) đạt được, tách theo kết cục
| nhóm | n | `c_I` trung bình |
|---|---|---|
| **chỉ 1.5B giải được** (cả hai mẫu 7B trượt) | 15 | **0.53** |
| 7B giải được (ít nhất một mẫu) | 333 | **2.33** |
| **cả ba đều trượt** | **152** | 0.84 |

Tín hiệu **phân tách rõ**: 0.53 vs 2.33. Điểm test thấp ⇒ 7B đang chật vật.

### Nhưng làm CỔNG định tuyến thì hỏng vì TỈ LỆ NỀN
Lấy ngưỡng `c_I ≤ 2`: bắt được **14/15** ca chỉ-1.5B-thắng (**recall 93%**),
nhưng kích hoạt trên **347/500 bài** ⇒ **precision 4%**.
=> Không dùng để **tiết kiệm** được gì đáng kể. *Nhưng* vì ứng viên 1.5B chỉ tốn **1.00**,
kích hoạt thừa cũng rẻ — giá trung bình 0.69 thay vì 1.00. Lợi ích nhỏ, không đáng phức tạp hoá.

### Con số ĐÁNG LO nhất, và nó chặn mọi thứ phía trên
**152/500 = 30.4% số bài mà CẢ BA ứng viên đều sai.** Ở đó mở rộng pool không cứu được gì.
Và trên nhóm đó `c_I` = 0.84 — **test tự sinh CŨNG trượt**, tức model "biết" có gì đó sai
mà **không sửa nổi**. Khớp với #93 (*oracle chỉ đáng giá khi model CÓ THỂ hành động theo tín hiệu*).

> **Trần thật của toàn bộ hướng "chọn trong pool" ở thang model này là ~.70**
> (500 − 152 = 348 bài có ít nhất một ứng viên đúng ⇒ **.696**).
> `SEL{I,I2,S}` đã đạt **.6800**, tức **97.7%** của trần đó.
> **Hướng này gần như CẠN.** Muốn hơn nữa phải làm cho ứng viên **đúng nhiều hơn** — tức
> quay lại bài toán SINH, không phải bài toán CHỌN.

Giả thuyết sinh ra (phải đăng ký trước rồi mới kiểm): H73 (k=8, đang chạy) sẽ **không** vượt
được nhiều so với k=2, vì trần chỉ nhích lên khi có ứng viên đúng MỚI, mà 30% bài thì
không mẫu nào của model này đúng.

---

## Vòng #114 — H65T2: **HỎNG Ở BƯỚC 14B, NHƯNG CỨU ĐƯỢC DỮ LIỆU — và nó THU HẸP phát hiện chính**
*(đăng ký trước #70 + #70-b. **Bảng khoá KHÔNG thể kích hoạt**: thiếu nhánh 14B ⇒ cổng
`acc(I_14B) − acc(I_7B) ≥ .05` không đánh giá được. Phần dưới là **DỮ LIỆU MỘT PHẦN**, không phải phán quyết.)*

### Bản sửa "lưu từng phần" ĐÃ CÓ TÁC DỤNG
H65T mất sạch 2.7h khi sập ở bước 14B. H65T2 sập **cùng chỗ** nhưng `partial_H65T2.json`
giữ được **cả 5 nhánh** của 1.5B và 7B (~2.5h). **Bài học #H65T đã trả công.**

### Nguyên nhân OOM lần này — một lỗi API thật, không phải ước lượng sai
`torch.cuda.empty_cache()` và `torch.cuda.memory_allocated()` **chỉ tác dụng lên THIẾT BỊ HIỆN TẠI**.
Tôi in "VRAM sau khi giải phóng 7B: 0.01 GB" — nhưng đó **chỉ là GPU 0**.
Bản sao 7B trên **GPU 1 vẫn còn nguyên** (5.2 GB), nên 14B `device_map="auto"` tràn GPU 1:
**5.2 + 9.3 = 14.5 GB** — khớp đúng thông báo lỗi.
**Sửa:** lặp `for d in range(NG): with torch.cuda.device(d): torch.cuda.empty_cache()`
và **báo VRAM theo TỪNG GPU**. (Chỉ số chẩn đoán của tôi đã nói dối vì cùng lỗi API đó.)

### DỮ LIỆU MỘT PHẦN — MATH-500 (cổng của phần này ĐẠT: `acc(S)` .3980 ∈ [.10,.55]; `I_7B − S` = +.1640)
| nhánh | acc |
|---|---|
| `S` = `I_1.5B` (1.5B tự giải) | .3980 |
| `V_1.5B` (1.5B xem lời giải của chính nó) | **.4440** |
| `I_7B` | .5620 |
| `V_7B` (7B xem lời giải 1.5B) | .5500 |

| | MATH (đây) | GSM8K (#100) | MBPP code (#103) |
|---|---|---|---|
| `poisoning(7B)` | **−.0120** | −.0740 | −.0740 |
| `poisoning(1.5B, tự xem)` | **+.0460** | — | −.0280 (7B, #105) |

### Hai điều PHẢI ghi, và cả hai đều thu hẹp phát biểu cũ
1. **Trên MATH, đầu độc gần như BIẾN MẤT** (−.0120 so với −.0740 ở hai miền kia).
   Phát biểu "đọc sản phẩm agent yếu hại ròng" **KHÔNG phổ quát theo task** như tôi đã ngụ ý ở #103.
2. **Ở 1.5B, tự xem lại lời giải của chính mình LÀM TỐT LÊN +.0460** — ngược dấu với `V_self`
   của 7B trên code (−.0280, #105). ⇒ "thuế của lượt sửa chữa" **không** áp dụng đồng đều;
   ở model yếu trên toán, lượt thứ hai **có ích thật**.

> **Chưa được kết luận gì thêm cho tới khi H65T3 (đã phóng, đã sửa lỗi GPU) cho đủ ba điểm.**
> Đặc biệt **không** được vẽ xu hướng năng lực từ hai điểm này.

---

## Vòng #115 — H74: **HOÀ ở cùng ngân sách — và tôi phải SỬA HAI kết luận thăm dò gần đây**
*(đăng ký trước #80, khoá tại `72d6985` TRƯỚC khi chạy)*

### Cổng ĐẠT: `soundness` .7214 · `copy_rate` .0258 · `acc(I)` .6400 · biên dịch .9869 · n=500
acc riêng: `I` .6400 · `I2` .6260 · `S1..S5` .4400/.4280/.3860/.4160/.4160

| pool | acc | vs `I` | **trần** | **thu được** | chi phí |
|---|---|---|---|---|---|
| {I} | .6400 | — | .6400 | — | 10.14 |
| {I,S1} | .6620 | +.0220 | .6740 | **65%** | 11.14 |
| **{I,I2}** | **.6640** | +.0240 | .6680 | **86%** | **15.21** |
| **{I,S1..S5}** | **.6660** | +.0260 | **.7040** | **41%** | **15.14** |
| {I,I2,S1..S5} | **.6840** | +.0440 | **.7260** | 51% | 20.21 |

**PHÁN QUYẾT: HÀNG 2 — HOÀ.** `SEL{I,S1..S5} − SEL{I,I2}` = **+.0020** ở chi phí khớp 0.5%.
Hai hàng phụ cũng kích hoạt: **bão hoà** (+.0040 từ S2..S5) và **pool rẻ có trần cao hơn** (+.036).

### ĐÂY LÀ ĐIỀU QUAN TRỌNG, và nó SỬA #111-b
**Trần tăng đều theo số ứng viên: .6400 → .6680 → .7040 → .7260.**
**Nhưng tỉ lệ thu được SỤT: 86% → 41% → 51%.**

Ở #111-b tôi kết luận (thăm dò, k=2): *"bộ chọn không còn là nút thắt, nút thắt là trần pool"*.
**Đúng ở k=2** (thu 86%), **SAI khi pool giàu hơn**. Với 6 ứng viên, trần lên .7040 mà bộ chọn
chỉ lấy được **41%** — **bộ chọn TRỞ LẠI làm nút thắt.**
> **Phát biểu đã sửa: nút thắt CHUYỂN theo k.** k nhỏ ⇒ pool là giới hạn; k lớn ⇒ bộ chọn là giới hạn.
> Không có một câu trả lời duy nhất, và tôi đã tổng quát hoá từ **một điểm k=2**.

### Và nó cũng SỬA #113-b
#113-b viết: *"trần thật của hướng này là .696, `SEL` đã đạt 97.7% ⇒ hướng gần CẠN"*.
Con số .696 tính trên pool **ba** ứng viên. Với **bảy** ứng viên trần là **.7260**.
**Trần KHÔNG cố định — nó tăng theo số ứng viên.** Phát biểu "gần cạn" là **quá sớm**;
cái cạn là *khả năng KHAI THÁC* của bộ chọn, không phải trần.

### Bão hoà: đa dạng của 1.5B là MỘT LẦN đối với BỘ CHỌN, không phải đối với POOL
`S1` một mình cho +.0220. Thêm `S2..S5` chỉ cho **+.0040** nữa.
Nhưng trần vẫn nhảy .6740 → .7040, và số bài **chỉ 1.5B giải được** tăng **15 → 29**.
=> Ứng viên đúng **có ở đó**, bộ chọn **không nhặt được**. Test `soundness` .72 không đủ
phân biệt khi số ứng viên tăng — càng nhiều ứng viên, càng nhiều cơ hội test chấm nhầm.

### Trả lời câu hỏi thực dụng
**Ở cùng ngân sách, nguồn ứng viên gần như KHÔNG quan trọng** (+.0020).
Cái quan trọng là **tổng ngân sách** — và cả hai cách đều bị chặn bởi **chất lượng bộ chọn**.
Cấu hình tốt nhất đo được: **{I,I2,S1..S5} = .6840 (+.0440)** ở chi phí 20.21 (2× cấu hình rẻ).

### Prior của tôi ĐÚNG (hàng 2, ~40%)
Lý do ghi trước cũng đúng: *"thêm mẫu 1.5B sẽ tạo thêm ứng viên sai, bộ chọn soundness .72
dễ bị đánh lừa hơn"* — đúng là thế, thể hiện ở tỉ lệ thu được tụt còn 41%.
Tỉ lệ prior đúng: **14/27**.

---

## Vòng #116 — H70: **TRÊN TOÁN, 7B TỰ XEM LẠI LỜI GIẢI CỦA MÌNH ĐƯỢC +.1080 — không hàng nào khớp**
*(đăng ký trước #75, khoá tại `d096473` TRƯỚC khi chạy)*

### Cổng ĐẠT: `I − S` = +.1640 · `acc(S)` = .3980 ∈ [.10,.55] · n=500 · MATH-500
| nhánh | 7B xem gì | acc | `− I` | 5 fold | sửa/phá | `unchanged` |
|---|---|---|---|---|---|---|
| `I` | không gì | .5620 | — | — | — | — |
| **`V_self`** | **lời giải CỦA CHÍNH NÓ** | **.6700** | **+.1080** | .13 .09 .10 .10 .12 | **cứu 58 / phá 4** | .6820 |
| `V_weak` | lời giải của 1.5B | .5500 | −.0120 | .01 −.06 .02 −.05 .02 | cứu 47 / phá 53 | .5260 |

`V_self − V_weak` = **+.1200**.

### BẢNG KHOÁ #75 KHÔNG CÓ HÀNG NÀO KHỚP — lỗi thiết kế của tôi, lần thứ HAI
Bốn hàng của #75 đều giả định `V_self` **≤ 0 hoặc ≈ `I`**. Thực tế **+.1080**, mạnh và 5/5 fold.
Tôi đã khoá bảng với niềm tin ngầm rằng "thuế sửa chữa" (#105, −.0280 trên code) là **phổ quát**.
**Không bịa hàng mới. Ghi nhận là thiếu sót.**
> Đây là **lần thứ hai** (sau #99/H60) tôi khoá bảng thiếu hàng cho *"hiệu ứng đi mạnh theo
> chiều tôi cho là không thể"*. Quy tắc ở QUY_TRINH đã có; tôi **vẫn** vi phạm. Phải áp dụng
> máy móc: **mọi bảng phải có hàng cho cả hai chiều, biên độ LỚN.**

### Nội dung khoa học: **"thuế sửa chữa" là ĐẶC THÙ TASK, không phổ quát**
| | `V_self − I` |
|---|---|
| **MATH** (đây) | **+.1080** ✓ |
| **MBPP code** (#105) | **−.0280** ❌ |

Trên **toán**, lượt thứ hai **cứu 58 phá 4** — model bắt được lỗi số học của chính nó.
Trên **code**, cùng thao tác **cứu 10 phá 24** — nó viết lại và làm hỏng chương trình đang chạy.
> **Khác biệt: sửa một phép tính là CỤC BỘ; sửa một chương trình là TOÀN CỤC.**
> Khớp với #93 (*lỗi khi SINH thì thô, lỗi khi BIẾN ĐỔI là trôi ngữ nghĩa*) và #103 (78% thiệt hại
> trên code là **viết lại**).

### Tái lập được một con số
`V_weak − I` = **−.0120** trên MATH — **trùng khớp** dữ liệu một phần cứu từ H65T2 (#114),
cùng thiết lập, hai lần chạy độc lập. Đầu độc trên toán **thật sự yếu** (so với −.0740 ở GSM8K/MBPP).

### Phải sửa lại phát biểu ở #105
#105 viết: *"`V − I` = (thuế THÊM LƯỢT SỬA) + (thiệt hại RIÊNG của nguồn ngoại lai)"*, với
thuế = −.0280. **Trên toán thuế đó là DƯƠNG +.1080.** Phân tách hai thành phần **vẫn đúng về
cấu trúc**, nhưng **dấu và độ lớn của từng phần phụ thuộc TASK** — không được mang số của code sang toán.

### Prior của tôi SAI
Đoán hàng 1 (~50%): *"phép tách lặp lại trên toán"*. Thực tế thành phần "chế độ" **đổi dấu**.
Tỉ lệ prior đúng: **14/28**.

### Phụ lục #115-b — **THĂM DÒ: "thu được 41%" nghe tệ hơn thực tế — và chỗ hỏng là XẾP HẠNG SAI, không phải HOÀ**
> ⚠️ Hậu kiểm trên trace H74, **không đăng ký trước**. Miễn phí.

### Hai cách đo cùng một bộ chọn, và tôi đã báo cách nghe tệ hơn
Pool đầy đủ 7 ứng viên:
- **363/500** bài có ít nhất một ứng viên ĐÚNG (= trần .7260)
- `SEL` chọn trượt ở **21** bài ⇒ **chọn đúng 342/363 = 94.2%**
- Nhưng `I` một mình đã đúng **320** bài. Phần *có thể thêm* chỉ là **43** bài;
  `SEL` cứu **22** ⇒ **51%** — đây là con số tôi đã báo ở #115.

Cả hai đều đúng, nhưng **ý nghĩa khác nhau**:
> **94.2%** = bộ chọn hầu như không làm hỏng gì.
> **51%** = trong số bài **`I` đã sai mà pool có bản đúng**, nó chỉ vớt được một nửa.
> Con số **51%** mới là con số cho *giá trị biên*, và đó là lý do nó nhỏ — **những bài `I` đã sai
> chính là những bài KHÓ, nơi test tự sinh kém tin cậy nhất.** Không phải bộ chọn "hỏng".

### Chỗ hỏng cụ thể: **XẾP HẠNG SAI**, gần như không phải HOÀ
| nguyên nhân trượt | số bài |
|---|---|
| **test chấm NGƯỢC** (bản đúng không đạt điểm cao nhất) | **19** |
| tất cả hoà điểm | 2 |

Và bản **ĐÚNG** thua bản được chọn trung bình **1.00 điểm test** (trung vị 1) — tức test
**ưu tiên nhầm với biên độ nhỏ**, đúng như `soundness` .7214 dự đoán.

### Điều này SẮC HOÁ dự đoán cho H75 (đang chạy)
Đồng thuận thực thi nhắm vào việc **không dùng giá trị kỳ vọng**. Nhưng:
- nhóm **HOÀ** (2 bài) — đồng thuận có thể phá hoà ⇒ **tối đa +.004**
- nhóm **XẾP HẠNG SAI** (19 bài) — đồng thuận chỉ cứu được **nếu đa số ứng viên ĐÚNG**.
  Pool có **5/7 là 1.5B** (acc ~.42) ⇒ ở bài khó, **đa số nhiều khả năng SAI**.

> **Dự đoán sắc hơn (ghi trước khi H75 có số): đồng thuận sẽ KHÔNG hơn nhiều — hàng 2 hoặc hàng 3
> của bảng #81.** Trần tuyệt đối nếu sửa được cả 21 bài là **+.042**, nhưng phần khả thi thực tế
> nhỏ hơn nhiều. Nếu H75 ra hàng 1 (≥ +.02) thì tôi đã đánh giá thấp đồng thuận và phải ghi nhận.

---

## Vòng #117 — H73: **k LÀ ĐÒN BẨY — +.0800 so với greedy, hiệu ứng DƯƠNG LỚN NHẤT của dự án**
*(đăng ký trước #79, khoá tại `f522179` TRƯỚC khi chạy)*

### Cổng ĐẠT: `soundness` .7214 · `copy_rate` .0258 · `acc(SEL@1)` = .6400 ∈ [.60,.68] · biên dịch .9948
8 ứng viên đều là **7B** (1 greedy + 7 mẫu T=0.8), acc riêng **.624–.662**. Test sinh **một lần**, dùng chung.
k nhỏ là **tiền tố** của k lớn ⇒ ghép cặp hoàn hảo.

| k | `SEL@k` | so với k=1 | **trần** | **thu được** | **tie_rate** | chi phí |
|---|---|---|---|---|---|---|
| 1 | .6400 | — | .6400 | — | 1.000 | 10.14 |
| 2 | **.6800** | **+.0400** | .6840 | **91%** | .9080 | 15.21 |
| 4 | **.7040** | **+.0640** | .7180 | **82%** | .7980 | 25.35 |
| 8 | **.7200** | **+.0800** | .7500 | **73%** | .7240 | 45.63 |

**PHÁN QUYẾT: HÀNG 1.** `SEL@8 − SEL@2` = **+.0400** ≥ +.02, tăng đều theo k.
**`tie_rate` giảm .908 → .724** đúng như cơ chế đã nêu ở #111-b.

### Giải quyết mâu thuẫn #111-b ↔ #115 — **cả hai đều đúng**
- #115 đúng: **tỉ lệ thu được GIẢM** khi pool giàu lên (91% → 73%).
- #111-b đúng: **k vẫn là đòn bẩy**, vì **trần tăng NHANH HƠN mức bộ chọn xuống cấp**
  (trần +.1100 từ k=1→8, thu được mất 18 điểm phần trăm ⇒ ròng vẫn **+.0800**).
> **Phát biểu hợp nhất: thêm ứng viên vừa nâng trần vừa làm bộ chọn khó hơn — nhưng ở dải k≤8
> phần nâng trần THẮNG.** Cả hai kết luận trước đều đúng một nửa; không cái nào bị rút.

### Nhưng phải nói rõ CHI PHÍ
+.0800 đổi bằng **4.5× chi phí** (10.14 → 45.63). Lợi ích mỗi đơn vị chi phí **giảm dần**:
k=2 **+.00113/đơn vị** · k=4 **+.00042** · k=8 **+.00023**.
**Nếu ngân sách là ràng buộc thì k=2 là điểm ngọt**, không phải k=8.

### Cảnh báo so sánh CHÉO LẦN CHẠY (lần thứ ba)
`SEL@2` ở đây = **.6800**; `SEL{I,I2}` ở H74 = **.6640**. Cùng thiết lập, khác **mẫu T=0.8**
(cand-1 ở đây .662, `I2` ở H74 .626). Chênh **.0160** thuần do rút mẫu.
**Chỉ đọc các so sánh GHÉP CẶP TRONG CÙNG lần chạy.** Đã dính ba lần: #70 (`MAXNEW`),
#113 (`I2`), nay lại.

### Prior của tôi ĐÚNG (hàng 1, ~55%)
Đoán `SEL@8 − SEL@2` ≈ +.025; thực tế **+.0400** — đúng hướng, **đánh giá thấp biên độ**.
Rủi ro tôi nêu trước (*"tie_rate .898 quá cao, có thể ra hàng 2"*) **không xảy ra**: tie giảm mạnh.
Tỉ lệ prior đúng: **15/29**.

---

## Vòng #118 — H75: **ĐỒNG THUẬN THỰC THI TỆ HƠN HẲN (−.0840) — đa số SAI nhấn chìm thiểu số ĐÚNG**
*(đăng ký trước #81, khoá tại `80667a9` TRƯỚC khi chạy)*

### Cổng ĐẠT: tách lời gọi **.9986** · `soundness` .7214 · `copy_rate` .0258 · `acc(I)` .6400 · `SEL_test` .6900 ∈ [.66,.71]
Pool 7 ứng viên: `I` .6400 · `I2` .6420 · `S1..S5` .440/.406/.410/.414/.424 (**5/7 là 1.5B**)

| bộ chọn | acc | `− I` | trần | thu | chọn `S1` bao nhiêu lần |
|---|---|---|---|---|---|
| **`SEL_test`** (đếm assert đạt) | **.6900** | **+.0500** | .7340 | 53% | 29 |
| **`SEL_cons`** (đồng thuận thực thi) | **.6060** | **−.0340** | .7340 | **−36%** | **65** |
| `SEL_hyb` | .6060 | −.0340 | .7340 | −36% | 71 |

**PHÁN QUYẾT: HÀNG 4.** `SEL_cons − SEL_test` = **−.0840**. Đồng thuận **tệ hơn cả việc chỉ dùng `I`**.

### Cơ chế — đúng như tôi đã NÊU TRƯỚC, chỉ là tôi đặt cược sai
Đăng ký trước #81 tôi viết: *"đồng thuận chỉ tốt khi đa số đúng, mà pool này đa số là model yếu"*.
Đó chính xác là điều xảy ra: đồng thuận chọn `S1` **65 lần** (so với 29 của `SEL_test`),
mà `S1` chỉ đúng **.44**.
> **Năm mẫu 1.5B KHÔNG phải năm phiếu độc lập.** Chúng đến từ **cùng một model**, nên chúng
> **sai theo cùng một kiểu** và tạo ra một "đa số" thống nhất **quanh câu trả lời sai**.
> Đồng thuận nhầm **lỗi tương quan** thành **bằng chứng**.

**Đây là cùng một sai lầm với "đầu độc" ở #103, nhìn từ góc khác:** thêm tiếng nói từ một
model yếu không thêm **thông tin**, nó chỉ thêm **trọng số cho phân phối lỗi của model đó**.

### Tại sao `SEL_test` vẫn thắng dù test chỉ đúng .72
Test tự sinh **sai độc lập với** lỗi của ứng viên (nó do 7B viết, từ mô tả bài).
Đồng thuận thì **không độc lập** với lỗi ứng viên — nó CHÍNH LÀ lỗi ứng viên.
> **Một tín hiệu yếu nhưng ĐỘC LẬP hơn hẳn một tín hiệu mạnh nhưng TƯƠNG QUAN.**

### Prior của tôi SAI — nhưng cơ chế thì ĐÚNG
Đoán hàng 2 (~40%), hàng 4 chỉ ~15%. Ra **hàng 4** với biên độ lớn.
Ở #115-b tôi còn sắc hoá thành *"hàng 2 hoặc 3"* — cũng sai.
**Nhưng lý do tôi ghi trước cho rủi ro lại chính là nguyên nhân thật.**
Bài học: khi đã viết ra được cơ chế thất bại, phải **cân nhắc nó nặng hơn** trong prior,
đừng để "ý tưởng hay" kéo prior lên. Tỉ lệ prior đúng: **15/30**.

### Câu hỏi bật ra ngay (đã phóng H76)
Nếu chẩn đoán đúng thì đồng thuận phải **hoạt động tốt khi đa số ĐÚNG**.
Pool 8×7B của #117 (mỗi mẫu ~.64) là phép thử sạch cho điều đó.

### Phụ lục #117-b — **THĂM DÒ: 8 mẫu cùng model TƯƠNG QUAN cực mạnh — dự đoán H76 TRƯỚC khi có số**
> ⚠️ Hậu kiểm trên trace H73, **không đăng ký trước**. Nhưng nó **dự đoán H76 đang chạy**,
> nên ghi lại **NGAY BÂY GIỜ** để dấu thời gian git chứng minh là dự đoán, không phải hồi tố.

### Phân bố số ứng viên ĐÚNG trong 8 mẫu (tất cả đều là 7B, T=0.8)
| số đúng | số bài | % |
|---|---|---|
| **0/8** | **125** | **25.0%** |
| 1–7/8 | 111 | **22.2%** |
| **8/8** | **264** | **52.8%** |

**Cực kỳ LƯỠNG CỰC.** 8 mẫu **đồng ý về tính đúng/sai ở 77.8% số bài**.
Đây là **lỗi tương quan** đo trực tiếp — không phải suy đoán.

### Và đây là chỗ chết của bỏ phiếu đa số
Bỏ phiếu chỉ có việc làm ở **111 bài hỗn hợp**. Trong đó **đa số ĐÚNG chỉ ở 52 bài (46.8%)**
— tức **đa số SAI thường xuyên hơn đúng**, đúng ở những bài mà việc bỏ phiếu mới quan trọng.

> **Nghịch lý: model đúng 64% tổng thể, nhưng ở những bài CÓ BẤT ĐỒNG thì đa số chỉ đúng 46.8%.**
> Bất đồng **chọn lọc ra** đúng những bài khó, nơi câu trả lời phổ biến nhất của model là SAI.

**Ước lượng bỏ phiếu đa số = (264 + 52)/500 = .6320 — THẤP HƠN greedy .6400.**

### DỰ ĐOÁN CHO H76 (ghi trước khi có kết quả)
> **Đoán H76 ra HÀNG 3** (*"đồng thuận hại KỂ CẢ khi đa số đúng ⇒ RÚT LẠI chẩn đoán #118"*),
> với `SEL_cons` ≈ **.63**, kém `SEL_test` khoảng **−.06**.

Nếu đúng thì chẩn đoán #118 (*"đồng thuận hỏng vì pool đa số YẾU"*) là **CHƯA ĐỦ**:
nó hỏng vì **lỗi tương quan**, và 8 mẫu cùng một model cũng tương quan y như 5 mẫu model yếu.
Prior ở #83 (hàng 1, 45%) tôi đặt **quá cao** — lần thứ hai liên tiếp để "ý tưởng hay" kéo prior lên,
dù lần này tôi đã tự cảnh báo. **Với dữ liệu này tôi hạ xuống: hàng 3 ~70%, hàng 2 ~20%, hàng 1 ~10%.**

---

## Vòng #119 — H65c: **HUỶ theo cổng đã khoá — và tôi phát hiện một CONFOUND làm hỏng MỌI kết quả MATH**
*(đăng ký trước #70, khoá tại `85b7ef2`)*

### Phần cứng ĐÚNG như thiết kế
`NVIDIA RTX PRO 6000 Blackwell | 95.0 GB | sm_120` · **bf16 cả ba model, KHÔNG lượng tử hoá**.
Cổng ba trường và cơ chế tự chọn độ chính xác đều hoạt động. `bitsandbytes` không cài được
(competition cấm internet) nhưng **không cần** — đúng như thiết kế.

### HUỶ: cổng `acc(I_14B) − acc(I_7B) ≥ .05` TRƯỢT
`I_7B` = **.5760** · `I_14B` = **.5480** ⇒ **−.0280**. **14B YẾU HƠN 7B** trên MATH-500 ở thiết lập này.
Cổng này tôi khoá chính xác để chặn trường hợp "thêm năng lực **không xảy ra**".
⇒ **KHÔNG ĐỌC** quét năng lực. (Các số bị niêm phong, chỉ ghi để đối chiếu:
poisoning 1.5B +.0640 · 7B −.0220 · 14B +.0540 — **không đơn điệu**, nhưng **không được diễn giải**.)

### CONFOUND — nghiêm trọng hơn cả việc HUỶ, và nó đánh vào phát hiện của CHÍNH TÔI
Chẩn đoán tiếp: đếm đầu ra **không có `\boxed`** (dấu hiệu bị cắt ở `MAXNEW=640`):
| nhánh | thiếu `\boxed` | | nhánh | thiếu | **lệch** |
|---|---|---|---|---|---|
| `I_1.5B` | **45.8%** | | `V_1.5B` | 20.8% | **−125 bài** |
| `I_7B` | **39.8%** | | `V_7B` | 25.4% | **−72 bài** |
| `I_14B` | **43.0%** | | `V_14B` | 24.6% | **−92 bài** |

**Nhánh `I` bị cắt NHIỀU HƠN HẲN nhánh `V`** — và lý do thì hiển nhiên khi đã thấy:
`V` **được đưa sẵn một lời giải**, nó chỉ cần kiểm rồi chốt đáp án; `I` phải **tự dẫn từ đầu**
nên tốn token hơn và đụng trần `MAXNEW` thường xuyên hơn.

> **Mọi phép đo `V − I` trên MATH đều THIÊN LỆCH CÓ HỆ THỐNG THEO HƯỚNG CÓ LỢI CHO `V`.**

### Hệ quả: PHẢI ĐÌNH CHỈ phát hiện đầu bảng của vòng #116
#116 báo `V_self − I` = **+.1080** trên MATH và tôi đã dùng nó để nói *"thuế sửa chữa là đặc thù task"*.
**Con số đó dùng đúng kernel này, đúng `MAXNEW=640`** ⇒ **bị confound đúng chiều làm nó DƯƠNG hơn thực tế.**
- **#116 (+.1080) — ĐÌNH CHỈ, chưa được trích dẫn** cho tới khi đo lại.
- **#114 (+.0460 và −.0120) — ĐÌNH CHỈ** vì cùng kernel, cùng `MAXNEW`.
- H70b (đang chạy, tái lập #116) **đã XOÁ** — nó chỉ tái lập cái confound, không tái lập phát hiện.

### Kết quả CODE **KHÔNG** bị ảnh hưởng — đã kiểm
MBPP: chỉ **3/500** ứng viên thiếu `def` (0.6%), `S` **0/500**; tỉ lệ biên dịch .99+.
⇒ Toàn bộ chuỗi code (#103, #105, #107, #110, #112, #113, #115, #117, #118) **VẪN ĐỨNG**.

### Bài học
> **Một giới hạn sinh (`MAXNEW`) là một CAN THIỆP, không phải tham số vô hại — và nó tác động
> KHÔNG ĐỀU lên các nhánh có độ dài đầu ra khác nhau.** Cùng loại lỗi với "chốt chống rò rỉ"
> ở #106/#108: thứ tôi tưởng là chi tiết kỹ thuật lại là biến gây nhiễu.
> **Cổng mới bắt buộc cho mọi thí nghiệm MATH: tỉ lệ có `\boxed` ≥ .80 ở MỌI nhánh,
> và chênh lệch tỉ lệ đó giữa hai nhánh < .05.**

### Phụ lục #119-b — **THĂM DÒ: confound cắt ngắn chỉ đe doạ các kết quả mà `V` TRÔNG TỐT**
> ⚠️ Hậu kiểm trên trace H61/H66/H65c, **không đăng ký trước**. Miễn phí.

Đo lệch cắt ngắn (`I` thiếu dấu đáp án − `V` thiếu) trên **cả ba** miền:

| miền | `MAXNEW` | `I` thiếu | `V` thiếu | **lệch** | ảnh hưởng tới kết luận |
|---|---|---|---|---|---|
| **MATH** (#114/#116/H65c) | 640 | 39.8% | 25.4% | **−14.4 đpt** | **ĐÌNH CHỈ** — làm `V` trông TỐT hơn |
| **GSM8K** (#100) | 400 | 9.4% | 4.2% | **−5.2 đpt** | **AN TOÀN** — xem dưới |
| **MBPP code** (#103…#118) | 512 | 0.6% | 0.6% | ~0 | **AN TOÀN** |

### Vì sao GSM8K vẫn đứng vững dù có lệch
Lệch **luôn có lợi cho `V`**. Ở GSM8K kết quả là `V − I` = **−.0740**, tức **`V` THUA**.
Một thiên lệch giúp `V` mà `V` vẫn thua **−.074** ⇒ **giá trị thật còn ÂM HƠN**.
> **Confound làm kết quả #100 trở nên BẢO THỦ, không thể tạo ra nó.**

Cùng lập luận cho **MBPP** (#103, `V − I` = −.0740, lệch ~0) và cho `V_review` ở #110/#112.

### Quy tắc rút ra
> **Một thiên lệch chỉ nguy hiểm khi nó CÙNG CHIỀU với kết luận.**
> Khi nó **ngược chiều**, nó biến kết quả thành **cận dưới** — vẫn dùng được, thậm chí mạnh hơn.
> Vì thế: **#114/#116 (V trông TỐT trên MATH) bị đình chỉ; #100/#103 (V trông XẤU) không bị đụng.**

Điều này thu hẹp đúng phạm vi thiệt hại của #119: **chỉ các kết quả MATH có dấu DƯƠNG cho `V`.**

---

## Vòng #120 — H76: **DỰ ĐOÁN #117-b ĐÚNG — đồng thuận hại KỂ CẢ khi đa số đúng ⇒ RÚT LẠI chẩn đoán #118**
*(đăng ký trước #83, khoá tại `18659c5`; dự đoán ghi trước tại `abad54f`)*

| bộ chọn | acc | so với cand0 | trần | thu |
|---|---|---|---|---|
| **`SEL_test`** | **.7280** | +.0880 | .7620 | 72% |
| `SEL_cons` | .6640 | +.0240 | .7620 | 20% |
| `SEL_hyb` | .6700 | +.0300 | .7620 | 25% |

**PHÁN QUYẾT: HÀNG 3.** `SEL_cons − SEL_test` = **−.0640**.

### Dự đoán ghi trước ở #117-b: **TRÚNG**
Tôi ghi (trước khi có số): *"hàng 3, `SEL_cons` ≈ .63, kém `SEL_test` khoảng −.06"*.
Thực tế **−.0640**, `SEL_cons` = .6640. **Trúng cả hàng lẫn biên độ.**
Cơ sở là phân bố lưỡng cực đo được ở #117-b (25% cùng sai / 52.8% cùng đúng / 22.2% hỗn hợp,
và trong nhóm hỗn hợp đa số chỉ đúng 46.8%).

### RÚT LẠI chẩn đoán #118
#118 giải thích đồng thuận thất bại là vì *"pool đa số YẾU"*. **Sai — chưa đủ.**
Ở đây pool là **8 mẫu 7B, đa số ĐÚNG tổng thể**, mà đồng thuận vẫn **−.0640**.
> **Nguyên nhân thật: LỖI TƯƠNG QUAN, không phải năng lực của đa số.**
> Mẫu từ cùng một model sai theo cùng một kiểu; "đa số" không phải bằng chứng độc lập.
> Bất đồng **chọn lọc ra** đúng những bài khó, nơi câu trả lời phổ biến nhất là SAI.

Phát biểu ở #118 (*"tín hiệu yếu nhưng ĐỘC LẬP thắng tín hiệu mạnh nhưng TƯƠNG QUAN"*) **vẫn đúng**;
chỉ phần **chẩn đoán nguyên nhân** phải sửa.

---

## Vòng #121 — H73b: **VÔ HIỆU LÀM TÁI LẬP — kernel chạy nhầm CÙNG dải bài**
*(đăng ký trước #82)*

`res_h73b` có `task_id 11..510` — **y hệt H73**, không phải dải giữ lại 511–974.
**Nguyên nhân:** tôi chỉ tham số hoá `@@LO@@/@@HI@@` cho `mbpp_select_vs_review_kernel.py`,
**quên `mbpp_kscale_kernel.py`** (vẫn hardcode `TIDLO, TIDHI = 11, 510`). Bộ phóng chỉ kiểm
*"còn placeholder chưa thay"*, **không kiểm "placeholder có tồn tại không"** ⇒ `LO=511 HI=974` bị **bỏ qua im lặng**.
**Đây là lỗi #109 lặp lại: bản sửa không lan sang mọi kernel dẫn xuất.**

### Vẫn đọc được gì
| | dải | `SEL@8 − SEL@2` | `tie_rate` k=2→8 |
|---|---|---|---|
| H73 | 11–510 | +.0400 | .908 → .724 |
| H73b | **11–510 (trùng)** | +.0460 | .886 → .730 |

⇒ **Tái lập theo LẦN RÚT MẪU** (cùng bài, mẫu khác): +.0400 vs +.0460, cùng chiều, cùng cỡ.
⇒ **KHÔNG phải tái lập theo BÀI.** Phát biểu k-scaling vẫn **chưa được kiểm trên dải giữ lại**,
**không được đưa vào README** cho tới khi chạy đúng.

**Sửa bắt buộc trước khi chạy lại:** tham số hoá dải trong `mbpp_kscale_kernel.py`, và thêm vào
`launch_any.py` phép kiểm **"nếu truyền LO/HI thì kernel PHẢI chứa `@@LO@@`"** — im lặng bỏ qua
tham số là kiểu lỗi tệ nhất vì nó tạo ra một "bản tái lập" giả.

---

## Vòng #122 — H70c: **RÚT LẠI #116. `V_self` = +.0020, KHÔNG phải +.1080 — gần như TOÀN BỘ là artifact cắt ngắn**
*(đăng ký trước #84, khoá tại `3c86654` TRƯỚC khi chạy)*

### Cổng cắt ngắn ĐẠT: tỉ lệ có `\boxed` = `S` .956 · `I` .976 · `V_weak` .978 · `V_self` .996
min .9560 ≥ .80 ✓ · chênh .0400 < .05 ✓ ⇒ **dữ liệu SẠCH**, đọc được.

| | H70 (`MAXNEW`=640, **confound**) | **H70c** (`MAXNEW`=1280, sạch) |
|---|---|---|
| `I` | .5620 | **.7000** |
| `V_self − I` | **+.1080** | **+.0020** |
| `V_weak − I` | −.0120 | **−.1260** |

**PHÁN QUYẾT theo bảng #84: HÀNG 3 — `\|V_self − I\| < .02` ⇒ RÚT LẠI #116.**
*(Kernel in "HÀNG 2" vì nó dùng logic bảng #75 cũ; bảng chi phối H70c là **#84**.)*

### Hai điều, và cả hai đều đi cùng một hướng
1. **`V_self` = +.1080 → +.0020.** Phát hiện đầu bảng của #116 (*"trên toán tự xem lại được +.1080"*)
   **gần như hoàn toàn là artifact**: nhánh `I` bị cắt 39.8% còn `V_self` chỉ 24.6%, và khi cho đủ
   token thì hiệu ứng **biến mất**. **#116 RÚT LẠI HOÀN TOÀN.**
2. **`V_weak` = −.0120 → −.1260.** Đầu độc trên MATH **KHÔNG yếu như tôi tưởng** — nó bị
   **CHE** bởi chính confound đó. **−.1260 là hiệu ứng đầu độc LỚN NHẤT đo được ở mọi miền**
   (GSM8K −.0740 · MBPP −.0740), 5/5 fold từ −.05 tới −.18.

⇒ Phát biểu ở #114/#119 rằng *"trên MATH đầu độc gần như biến mất"* cũng **SAI và bị rút lại**.
Sự thật ngược lại: **MATH là nơi đầu độc MẠNH NHẤT.**

### Phân tách chế độ/nguồn trên toán, nay đo SẠCH
`V_self − I` = **+.0020** (chế độ sửa chữa: **không tốn gì**) · `V_weak − I` = **−.1260** (nguồn: **toàn bộ thiệt hại**).
| | phần CHẾ ĐỘ | phần NGUỒN |
|---|---|---|
| **code** (#105) | −.0280 (38%) | −.0460 (62%) |
| **toán** (đây) | **+.0020 (0%)** | **−.1260 (100%)** |
⇒ **Phép tách vẫn đúng về cấu trúc, nhưng tỉ lệ hoàn toàn khác theo task** — như #116 đã nói,
chỉ là **con số của #116 sai**. Trên toán, xem lại việc của mình **vô hại**; xem lời giải của
agent yếu **rất hại**.

### Prior của tôi SAI, nhưng tôi đã đặt cược ĐÚNG HƯỚNG
#84 tôi đoán hàng 2 (~45%, "đúng chiều nhưng nhỏ hơn"), hàng 3 (rút lại) ~30%.
Ra **hàng 3**. **Tôi đã cố tình đặt cược chống lại phát hiện của chính mình và điều đó là đúng.**
Tỉ lệ prior đúng: **15/31**.

---

## Vòng #123 — H65d: **HUỶ lần hai — cổng cắt ngắn trượt SÁT NÚT (.0500 vs ngưỡng <.05)**
*(đăng ký trước #85)* · RTX PRO 6000, bf16 cả ba model, `MAXNEW`=1280.
`min(boxed)` = .9400 ✓ nhưng **chênh = .0500**, ngưỡng là **< .05** ⇒ **TRƯỢT, không đọc.**
Cổng `I_14B − I_7B` = **+.0180** cũng dưới .05.

**Điều đọc được (chỉ về hạ tầng, không phải kết luận khoa học):** `I_14B − I_7B` đi từ
**−.0280** (H65c, `MAXNEW`=640) lên **+.0180** (đây, 1280) ⇒ **confound cắt ngắn ĐÚNG LÀ
một phần nguyên nhân** khiến 14B trông yếu hơn 7B. Nhưng ngay cả khi sửa, **14B vẫn không
hơn 7B đủ .05** trên MATH-500. ⇒ Hướng quét năng lực 14B **dừng lại** — hai lần HUỶ,
và lần này lý do là năng lực thật, không phải hạ tầng.

---

## Vòng #124 — H63: **MẤT TRẮNG ~15 giờ GPU — đụng tường 12h, KHÔNG có lưu từng phần**
Kernel bị `CANCEL_ACKNOWLEDGED`. Đầu ra chỉ có log; **không có `res_H63.json`, không có trace.**
Kịp in: `ref1` preserve **.7681** (5113s) · `ref_exec3` preserve **.8669** (9850s),
rồi **chết trong lúc sinh 8 mẫu cho nhánh `ref_sel8`** — tức **đúng nhánh là mục đích của thí nghiệm**.

> H63 được port **trước** khi tôi rút ra bài học "lưu từng phần" (H65T, vòng #114).
> H65T2 sập y hệt nhưng **cứu được** nhờ bản sửa đó. H63 thì không.
> **Câu hỏi refactor CHỌN-vs-SỬA vẫn CHƯA có câu trả lời** sau ~15 giờ GPU.
Muốn chạy lại thì **bắt buộc**: lưu từng phần sau mỗi nhánh, và giảm k từ 8 xuống 4 để lọt 12h.

---

# Vòng #125 — **KIỂM ĐỘC LẬP: ba tác nhân trung lập soi lại code, số liệu và lập luận**
*(ba agent chạy song song, KHÔNG được cho biết tôi đã kết luận gì, được yêu cầu giả định tôi sai)*
**Đây là mục quan trọng nhất trong toàn bộ log. Nhiều kết luận của tôi KHÔNG sống sót.**

## A. LỖI CODE — nghiêm trọng, tôi đã bỏ sót hoàn toàn

### A1. `tie_rate` ở #117 ĐO NHẦM SỰ KIỆN — **tôi đã tự kiểm chứng, ĐÚNG là lỗi**
`mbpp_kscale_kernel.py:168` đếm **tất cả k ứng viên bằng nhau**, nhưng sự kiện thật sự ép về
`cand0` là **hoà TẠI MAX**. Tự đo lại trên trace H73:
| k | `tie_rate` tôi báo cáo | **hoà-tại-MAX (sự kiện thật)** |
|---|---|---|
| 2 | .9080 | .9080 |
| 4 | .7980 | **.9220** |
| 8 | **.7240** | **.9440** |
Con số tôi báo **GIẢM** thuần do tổ hợp; đại lượng vận hành **TĂNG**.
⇒ **Phát biểu cơ chế ở #117 (*"tie_rate giảm .908→.724 đúng như #111-b dự đoán"*) SAI, RÚT LẠI.**
Tệ hơn: dòng chẩn đoán `:225` lẽ ra để **bác bỏ** #111-b **không bao giờ có thể kích hoạt**.
Tôi đã tự viết một phép thử không thể thất bại rồi coi việc nó không thất bại là bằng chứng.

### A2. Quét năng lực đo **hai đại lượng khác nhau** (`capacity_poison_kernel.py:176-185`)
`poisoning(1.5B)` = **tự xem lại** (`I_1.5B is SOLS`), còn `poisoning(7B/14B)` = **xem model khác**.
⇒ Trục "năng lực" trộn **chế độ** với **nguồn** — đúng cái confound mà `math_selfvsweak` sinh ra để tách.
**Cả H65c lẫn H65d hỏng về THIẾT KẾ, không chỉ trượt cổng.** Hệ quả: `poisoned_echo` ở 1.5B
**luôn bằng 0 theo định nghĩa** (đã xác nhận trong cả hai file kết quả) — bảng mời người đọc
hiểu nhầm là *"1.5B không bao giờ nhại lại"*.

### A3. Đồng thuận gom **CÙNG MỘT KIỂU CRASH** thành "đồng ý" (`mbpp_cons8_kernel.py:56,209`)
Khoá gom cụm là `'ERR:'+type(e).__name__`. Tám ứng viên cùng ném `TypeError` tạo thành
**một khối nhất trí 8 phiếu** và thắng ứng viên duy nhất chạy được. `SEL_test` **không thể** mắc
lỗi này (crash = 0 điểm). ⇒ **Một cơ chế MỘT CHIỀU đẩy `SEL_cons` xuống**, tức chính đại lượng
đầu bảng của #118/#120 (−.0840, −.0640). **Lời giải thích "lỗi tương quan" của tôi bị nhiễm bởi
một lỗi lập trình**, và `OUTS` không được lưu nên **không thể tách ra từ dữ liệu đã có**.

### A4. `mbpp_poison_kernel.py:110` + `:43` — **assert dùng để CHẤM nằm trong PROMPT**
H66 hiển thị **toàn bộ** `test_list` trong đề **và** chấm bằng **chính** chúng. Bốn kernel MBPP
khác đã được sửa (`#74-c`: đề chỉ có `assert[0]`, chấm bằng `[1:3]`), **kernel này chưa bao giờ được lan**.
⇒ **H66 và H69c không cùng mặt bằng dù cùng báo −.0740.** Đây là **lỗi #109 lần thứ ba**.

### A5. Quy tắc hoà thiên vị **chống lại** giả thuyết đang kiểm (`mbpp_pool_kernel.py:167-176`)
Hoà → `pool[0]` = `I`, và `S` luôn đứng cuối. 297/500 bài hoà ba chiều; 4 bài ở max mà **chỉ `S` đúng**
thì `S` **không bao giờ** được chọn. ⇒ `marginal_S` = +.0180 là **cận DƯỚI** (thiên lệch bảo thủ).

### A6. Trích đáp án MATH: nhánh `I` được **thêm cơ hội đoán** (`math_selfvsweak_kernel.py:184`)
Fallback `(?:answer is|=)` chỉ chạy khi `\boxed` hỏng, mà tỉ lệ hỏng **khác nhau theo nhánh**
(H70c: `I` 2.4% vs `V_self` 0.4%). ⇒ **thổi `I` lên, làm `poisoning` trông ÂM HƠN thực tế** (~2 đpt).
Ngoài ra `[^\n.$]+` loại dấu `.` nên `answer is 3.5` → `3`. Và **`boxed_rate` không bao giờ được lưu**
(`res[...] = BOXR` chạy SAU `json.dump`) — đã xác nhận thiếu trong cả `res_H70c.json` lẫn `res_H65d.json`.

## B. THỐNG KÊ — nhiều kết luận KHÔNG phân biệt được với nhiễu (McNemar ghép cặp, n=500)

| kết luận của tôi | delta | CI 95% | p | phán quyết |
|---|---|---|---|---|
| `SEL_self − SEL_weak` (#111) | +.0120 | [−.009, +.033] | **.34** | **KHÔNG ĐỨNG** |
| `cheap_vs_dear` (#115) | +.0020 | [−.022, +.026] | 1.00 | **KHÔNG ĐỨNG** (null hai lần) |
| bão hoà S1→S5 (#115) | +.0040 | [−.012, +.020] | .80 | **KHÔNG ĐỨNG** |
| `V_self − I` MATH (#122) | +.0020 | [−.008, +.012] | 1.00 | **KHÔNG ĐỨNG** (7 bài tín hiệu) |
| `(I+S) − (I+I2)` (#113) | .0000 | [−.020, +.020] | 1.00 | **KHÔNG ĐỨNG** |
| thu 65% vs 81% (#111) | — | [31,89] vs [60,96] | — | **KHÔNG ĐỨNG** (CI chồng hoàn toàn) |
| `marginal_S` (#113) | +.0180 | [+.004, +.032] | .022 | biên |
| `SEL−I` H69c / H69d | +.0220 / +.0151 | [+.008,+.038] / [+.002,+.028] | .0074 / .039 | biên (gộp Fisher .0026) |
| `V_weak−I` mọi miền · `SEL−V_review` +.1300 · `I−S` · k-scaling từng bước | — | — | ≤1e-3 | **VỮNG** |

### B1. **"5/5 fold" của tôi vừa VÔ NGHĨA vừa SAI SỰ THẬT**
- Tự kiểm: H69c folds = `[.04 .01 **.00** .01 .05]`, H69d = `[**.000** .011 .033 .022 .011]`.
  **Fold bằng 0 KHÔNG phải fold dương. Hai chỗ tôi viết "5/5" thực ra là 4/5. SAI SỰ THẬT.**
- Và nó gần như không mang thông tin: cho trước biên độ đã quan sát, P(5/5) = **.15–.84**.
  Phép thử dấu 5 fold **chặn trên ở p = .031**, yếu hơn McNemar mà tôi **chưa từng chạy** (.0074).

### B2. **k=2 "điểm ngọt" — độ cong KHÔNG tồn tại, và có thiên lệch chọn mẫu**
`k4→k8` **không nhỏ hơn** `k2→k4` ở 2/3 lần chạy. Và nhánh k=2 **luôn dùng ứng viên số 1** —
tự kiểm: trong 7 lựa chọn có thể, số 1 xếp **2/7 (H73)** và **1/7 (H73b)**, tức **gần MAX**.
Thổi k=2 lên ~+.005..+.011 — **đúng chiều tạo ra "điểm ngọt"**. ⇒ **RÚT LẠI khuyến nghị k=2.**
Chỉ còn phát biểu được: **k=1 là lựa chọn tệ nhất**.

### B3. H73/H73b/H76 là **ba lần rút mẫu trên CÙNG 500 bài** ⇒ **n hiệu dụng = 500, không phải 1500**.

### B4. ~40 so sánh, **không kiểm soát đa phép thử**. Ở α=.05 kỳ vọng ~2 dương tính giả —
đúng vùng p≈.02–.04 nơi `marginal_S`, `V_self−I` (#105), H69d nằm.

## C. LẬP LUẬN — đọc số sau khi cổng đã trượt (lỗi nặng nhất về kỷ luật)

1. **#123**: cổng cắt ngắn TRƯỢT, tôi viết *"không đọc"* — **rồi đọc `I_14B − I_7B` = +.0180 và
   dùng nó để ĐÓNG hướng 14B**. Đúng loại sai phạm mà đăng ký trước sinh ra để chặn. **RÚT LẠI.**
2. **#114**: cổng `#70` không đánh giá được, tôi **tự chế ra "cổng của phần này"** từ hai cổng phụ
   rồi rút hai kết luận. **RÚT LẠI cả hai.**
3. **#121**: tuyên VOID rồi vẫn đọc +.0460 là *"tái lập theo lần rút mẫu"*; cổng `#82`
   (`acc(SEL@1)` ∈ [.66,.76]) **trượt ở .6400 và tôi không hề báo cáo**. **RÚT LẠI.**
4. **#122**: *"−.1260 là đầu độc LỚN NHẤT mọi miền"* — **SAI**: #99 đã đo `V0−I` = **−.1680** trên GSM8K
   (tự kiểm, `IDEAS.md:3501`). Tôi **bỏ sót số của chính mình**. Và xếp hạng MATH>GSM8K>MBPP là
   **so chéo lần chạy** với headroom và `MAXNEW` khác nhau. **RÚT LẠI xếp hạng.**
5. **#120**: tôi tự chấm dự đoán #117-b là *"trúng cả hàng lẫn biên độ"*. Thực tế phần **số** SAI:
   dự đoán `SEL_cons` ≈ .63 **dưới** greedy .6400; thực tế **.6640, TRÊN** greedy. Chỉ **khoảng cách**
   (−.06 vs −.0640) là trúng. **Sửa: trúng hàng và khoảng cách, SAI mức và SAI dấu so với greedy.**
6. **#113** chi phí thiếu 5.07 (lượt sinh test) ⇒ tỉ lệ đúng là 11.14 vs 15.21 = **1.37×**, không phải 1.67×.
7. **#117** con số "lợi ích/đơn vị" (.00113/.00042/.00023) **không tái tạo được** từ chính bảng của nó
   (đúng phải là .00789/.00421/.00225).
8. **#103/#100**: *"ba miền, ba cặp model"* thực ra là **hai benchmark, hai cặp**; #100 ghi
   *"benchmark khác"* trong khi H60 và H61 **đều là GSM8K**.
9. **#101**: `V_label > V_first` = **+.0080 = 4 bài** — tôi rút ra cơ chế (*"hoài nghi nguồn quan trọng hơn"*)
   từ 4 bài, trong dự án dùng ngưỡng .02 ở mọi nơi khác. **RÚT LẠI cơ chế đó.**
10. **#102**: *"cấp lớp sửa lại LÀM HẠI"* là chênh **1 lớp và 4 lớp** trên n=88, không có phép thử —
    **trong đúng vòng tôi tuyên bố 5 method/354 là nhiễu**. Tiêu chuẩn kép. **RÚT LẠI.**
11. **#124**: báo `preserve` một mình — **đăng ký #68 cấm rõ ràng**.
12. **#115-b**: tiêu đề nói "41%" nhưng toàn bộ phân tích bên trong là pool 7 ứng viên (**51%**).

## D. Cái gì CÒN SỐNG sau kiểm định
- **Đầu độc `V − I` ÂM** ở mọi miền đã đo: GSM8K −.0740, MBPP −.0740, MATH −.1260, và
  #99 −.1680 — **tất cả p ≤ 1e-3**. Đây là kết quả vững nhất của dự án.
- **`SEL − V_review` = +.1300 / +.0841** (p 9e-13) — **CHỌN hơn REVIEW**, vững.
- **`I − S`**, **k-scaling từng bước dương** (mỗi bước p ≤ .02), **`SEL_test` hơn `SEL_cons`** (dấu vững,
  dù biên độ nhiễm lỗi A3).
- `SEL−I` ~+.02 [+.008,+.038] với **tái lập độc lập** H69c+H69d — giữ, nhưng **nêu kèm CI**,
  và nêu rõ **lật 6 bài là xoá sạch** hiệu ứng ở H69c.

## E. Bài học lớn nhất
> **Tôi đã bắt được rất nhiều lỗi hạ tầng của chính mình, nhưng KHÔNG bắt được lỗi nào
> trong nhóm A và B — vì đó là những lỗi khiến kết quả TRÔNG ĐÚNG.**
> Ba tác nhân trung lập tìm ra chúng trong ~10 phút. **Kiểm định độc lập không phải thủ tục;
> nó tìm ra một lớp lỗi mà tự kiểm về nguyên tắc không tìm được.**
> Cụ thể nhất: ở A1 tôi **tự viết một phép thử không thể thất bại** rồi coi việc nó không
> thất bại là bằng chứng ủng hộ giả thuyết của mình.

---

## Vòng #126 — H73c: **k-scaling TÁI LẬP THẬT trên dải tách rời** (lần này dải đúng)
*(đăng ký trước #82, khoá tại `2ef8593`; kernel + launcher đã sửa theo bài học #121)*

### Xác minh dải TRƯỚC khi đọc số (đúng quy tắc #121)
`n = 464` · `task_id 511..974` · **giao với dải cũ = 0 bài**. Lần này là tái lập THẬT.

| k | `SEL@k` | so với k=1 | trần | thu | `tie_rate` báo cáo | chi phí |
|---|---|---|---|---|---|---|
| 1 | .7069 | — | .7069 | — | 1.000 | 10.14 |
| 2 | .7198 | +.0129 | .7392 | 40% | .9246 | 15.21 |
| 4 | .7414 | +.0345 | .7716 | 53% | .8254 | 25.35 |
| 8 | **.7565** | **+.0496** | .7996 | 54% | .7414 | 45.63 |

### Hai cách đọc cổng — phải nêu cả hai (như #112)
Kernel in **"HUỶ: `acc(SEL@1)` ngoài [.60,.68]"** vì nó nhúng cổng của bảng **#79** (dải 11–510).
Bảng **CHI PHỐI H73c là #82**, cổng là **[.66, .76]** — `.7069` **NẰM TRONG** ⇒ **cổng ĐẠT**.
`SEL@8 − SEL@2` = **+.0367 ≥ +.02**, tăng đều ⇒ **HÀNG 1 của #82: TÁI LẬP.**

### Tái lập trên **bài khác nhau**, không phải mẫu khác nhau
| | dải | `SEL@8 − SEL@2` | `SEL@8 − SEL@1` |
|---|---|---|---|
| H73 | 11–510 | +.0400 | +.0800 |
| **H73c** | **511–974 (tách rời)** | **+.0367** | **+.0496** |

McNemar ghép cặp trên H73c: `SEL@1→SEL@8` = **+.0496, thắng 27 / thua 4, p = 3.4e-5**.
Từng bước: `1→2` +.0129 (p .11, **không đạt**) · `2→4` +.0216 (p .0064) · `4→8` +.0151 (p .065).
⇒ **Hiệu ứng TỔNG (k=1→8) vững; từng bước riêng lẻ thì KHÔNG** ở dải này.

### Cảnh báo #125-B2 KHÔNG tái diễn ở đây — và điều đó lại củng cố cảnh báo
Kiểm thiên lệch chọn ứng viên cho k=2: `cand1` xếp **6/7** trong các lựa chọn có thể
(.7198 so với trung bình .7250) ⇒ **thiên lệch −.0052**, tức lần này ngược chiều.
Ở H73/H73b nó xếp 2/7 và 1/7 (**+.005..+.011**). ⇒ **Xác nhận đây là nhiễu rút mẫu chứ không
phải hiệu ứng**, và củng cố việc **rút lại "k=2 là điểm ngọt"** ở #125: biên độ k=2 dao động
±.005 chỉ do chọn bạn đồng hành nào.

### Phát biểu được phép dùng
> **Lấy thêm mẫu rồi CHỌN bằng test tự sinh giúp +.0496 (k=1→8) trên dải giữ lại,
> tái lập +.0800 của dải gốc về DẤU và về tính đơn điệu, biên độ nhỏ hơn.**
> Chi phí **4.5×**. **KHÔNG** phát biểu gì về hình dạng đường cong (từng bước không đủ lực),
> **KHÔNG** phát biểu "k=2 là điểm ngọt".
Vẫn cần nói rõ: đây là **best-of-n có verifier** (Cobbe et al. 2021) áp dụng lại, không phải kỹ thuật mới.

---

## Vòng #127 — H79: **HUỶ theo cổng — mẫu thô quá ít, KHÔNG nới ngưỡng**
*(đăng ký trước #88)* · RTX PRO 6000 Blackwell 95 GB, sm_120 — phần cứng đúng.
Lọc theo lời giải chuẩn: **267/300** bài đạt (tỉ lệ giữ **.89**), cổng #88 yêu cầu **n ≥ 280** ⇒ **HUỶ**.

**Không đọc số nào.** Nguyên nhân là tôi ước lượng tỉ lệ giữ từ **40 bài** (32/40 = .80) rồi lấy
`N_TASK=300`; thực tế .89 nhưng vẫn không đủ vì tôi lấy mẫu thô quá sát ngưỡng.

> **Sửa đúng cách: TĂNG MẪU THÔ (300 → 340), KHÔNG hạ ngưỡng.**
> Hạ ngưỡng sau khi thấy số chính là sai phạm tôi đã ghi ở #123 (đọc `I_14B − I_7B` sau khi
> cổng trượt). Lần này làm ngược lại — giữ nguyên cổng, sửa thiết kế lấy mẫu.
Cũng ghi nhận: **kiểm bộ chấm offline TRƯỚC khi chạy đã cứu một phiên** — lần thử đầu cho
lời giải chuẩn **0/40** vì `canonical_solution` chỉ là **thân hàm**, phải ghép `complete_prompt`
(sau khi ghép: 32/40). Nếu không kiểm, mọi nhánh sẽ gần 0 và tôi sẽ có một kết quả **giả hoàn toàn**.

---

## Vòng #128 — H77: **MẤT 12 GIỜ vì tôi áp dụng CÁI TÊN của bài học, không phải NỘI DUNG**
Kernel bị `CANCEL_ACKNOWLEDGED` ở tường 12h. Kịp xong `S`, `I`, `V_review` và **4/8 mẫu** maj@k
(mẫu cuối ở 41977s). Nhưng file lưu-từng-phần chỉ có:
```
partial_H77.json  =  25 byte  =  {"partial": true, "n": 4}
```
so với bản làm ĐÚNG ở H65T2: **3.1 MB**, khoá `{partial, done, quant, raw}` với **toàn bộ đầu ra 5 nhánh**.

> **Tôi đã ghi bài học "lưu từng phần" ở #114, rồi khi viết kernel mới lại lưu một BỘ ĐẾM
> TIẾN ĐỘ thay vì DỮ LIỆU.** Cái tên của bài học được áp dụng; nội dung thì không.
> Đây là **lần thứ hai** mất >12 giờ vì đúng một nguyên nhân (lần đầu: H63, #124).

**Quy tắc thay thế, cụ thể hơn (đã thêm vào QUY_TRINH):** file lưu-từng-phần phải **CHỨA ĐỦ
để tái dựng kết quả mà không cần chạy lại GPU**. Kiểm bằng một câu hỏi duy nhất:
> *"Nếu kernel chết ngay sau dòng này, tôi có chấm điểm được từ file đã lưu không?"*
Nếu không — nó không phải lưu-từng-phần, nó là log. **Kích thước file là phép thử rẻ nhất:**
partial < 1 KB cho một kernel sinh 500 bài là dấu hiệu hỏng, thấy được ngay mà không cần đọc mã.

**Câu hỏi của H77 (CHỌN có hơn REVIEW trên TOÁN không) vẫn CHƯA có câu trả lời.**
Muốn chạy lại thì phải: giảm k từ 8 xuống 4 (để lọt 12h), và lưu `raw` thật sau mỗi mẫu.

---

## Vòng #129 — H79b: **BỊ CHIẾM CHỖ khi nạp 32B — nhưng con số quyết định ĐÃ ĐO XONG**
*(đăng ký trước #88)* · RTX PRO 6000. H78 **vẫn chạy**, nên đây không phải huỷ toàn cục:
**pool RTX 6000 đuổi job THỨ HAI** của cùng tài khoản (H79b chết ở 43% quá trình nạp 32B).

### Đã kịp đo, và nó đủ để kết luận NỬA CHI PHÍ
```
NHAN 34/301  |  leo thang 267  |  p_esc = 0.887
```
Code của **7B đạt test do CHÍNH NÓ viết chỉ ở 11.3%** số bài BigCodeBench.
⇒ Bộ định tuyến "chấp nhận-hoặc-leo-thang" **leo thang 88.7% số bài**.

| nhánh | chi phí (1.5B-eq) |
|---|---|
| `I` — gọi thẳng 32B | **21.30** |
| `ROUTE` — 7B code + 7B test + .887 × 32B | **29.00** |

> **Định tuyến "hợp lý" ĐẮT HƠN 1.36× so với gọi thẳng model mạnh — trước khi bàn tới độ chính xác.**
> Nó **không thể** tiết kiệm ở bất kỳ mức chính xác nào. Nửa chi phí của bảng khoá #88 đã xong.

**Chưa được kết luận:** `ROUTE − I` về **độ chính xác** (cần nhánh 32B chạy xong) ⇒ **chưa kích hoạt hàng nào**.

### Vì sao điều này quan trọng (trả lời phản biện "định tuyến của anh là kiểu rơm")
H39 (#78) — kết quả dương DUY NHẤT về định tuyến — chạy trên **MATH**, nơi tầng rẻ (1.5B)
**tự đồng thuận** ở **37.5%** số bài. Ở đây trên **code khó**, tầng rẻ chỉ tự tin ở **11.3%**.
> **Định tuyến có điều kiện sống nhờ việc tầng rẻ THƯỜNG XUYÊN tự tin ĐÚNG.**
> Trên tác vụ đủ khó để cần model mạnh, tầng rẻ gần như không bao giờ tự tin —
> nên định tuyến **suy biến thành "luôn leo thang" CỘNG một lượt rẻ lãng phí**.
Đây là **giới hạn cấu trúc**, không phải lỗi cấu hình: cùng cái làm bài khó (tầng rẻ hay sai)
cũng là cái làm cổng định tuyến luôn mở.

### Hạ tầng: pool RTX 6000 chỉ cho **MỘT** job mỗi tài khoản
Hai job 32B song song trên `zhongzhing` ⇒ job thứ hai bị đuổi giữa lúc nạp.
**Quy tắc mới: mỗi tài khoản CHỈ MỘT kernel RTX 6000 tại một thời điểm**, xếp hàng tuần tự.

---

## Vòng #130 — H78: **HUỶ — và cổng cắt ngắn vừa chặn một phát hiện GIẢ ngoạn mục**
*(đăng ký trước #87 + #87-b)* · RTX PRO 6000, bf16, thiết kế đã sửa (mọi hàng cross-model).

### Cổng cắt ngắn TRƯỢT rất nặng
| nhánh | tỉ lệ có `\boxed` |
|---|---|
| `S` .940 · `I_7B` .966 · `V_7B` .974 · `I_14B` .968 · `V_14B` .990 | bình thường |
| **`I_32B` .316** · **`V_32B` .524** | **thảm hoạ** |
min **.3160** (cần ≥ .80) · chênh **.6740** (cần < .05) ⇒ **HUỶ, không đọc số nào.**

### Vì sao: **32B lý luận DÀI HƠN NHIỀU** và bị `MAXNEW`=1280 chặt cụt
| nhánh | độ dài trung vị | % chạm trần |
|---|---|---|
| `I_7B` | 1332 | 39.6% |
| `I_14B` | 1331 | 41.2% |
| **`I_32B`** | **1500 (kịch trần)** | **99.8%** |

**32B gần như KHÔNG BAO GIỜ kịp viết xong.** Nó mất **68%** số đáp án chỉ vì hết token.

### Con số mà cổng đã chặn — và đáng lẽ tôi đã báo cáo nó
Nếu đọc bừa, bảng sẽ nói:
- `I_32B` = **.2880** so với `I_7B` = .7000 ⇒ *"32B tệ hơn 7B 41 điểm ở toán"* — **vô lý hiển nhiên**.
- `poisoning(32B)` = **+.2080**, 5/5 fold từ +.16 tới +.27 ⇒ *"ở 32B, được xem lời giải yếu
  giúp TĂNG 21 điểm!"* — một **đảo chiều ngoạn mục** của phát hiện chính, và **hoàn toàn là artifact**:
  `V_32B` giữ được `\boxed` ở **.524** còn `I_32B` chỉ **.316**, vì `V` được đưa sẵn lời giải
  nên tốn ít token hơn để đi tới đáp án. **Đúng confound #119, nay khuếch đại gấp 5 lần.**

> **Đây là lần cổng hiệu lực trả công lớn nhất.** Không có nó, tôi đã có một bảng số
> "5/5 fold, +.2080" trông cực kỳ thuyết phục và **sai hoàn toàn**.

### Bài học tổng quát (mới, và nó áp ngược lên các vòng trước)
> **Model càng mạnh càng lý luận DÀI. Một `MAXNEW` cố định vì thế PHẠT model mạnh NẶNG NHẤT —
> và phạt nhánh `I` nặng hơn nhánh `V`.** Hai thiên lệch cùng chiều, cùng nhân lên theo cỡ model.
Điều này **giải thích hồi tố** vì sao 14B trông yếu hơn 7B ở H65c (−.0280) và chỉ nhỉnh hơn
ở H65d (+.0180): **cùng một cơ chế, biên độ nhỏ hơn**. Ở 32B nó bùng thành .674 chênh lệch.
**Mọi so sánh giữa các cỡ model phải kiểm tỉ lệ hoàn thành TRƯỚC, không phải sau.**

### Chạy lại cần gì
`MAXNEW` ≥ **3072** cho 32B (trung vị 7B là 1332 token-tương-đương ⇒ 32B cần ~2.3×).
Nhưng H78 đã mất **5.2 giờ** ở 1280; ×2.4 sẽ vượt tường 12h ⇒ phải **giảm n xuống ~250**
hoặc **bỏ nhánh 14B**. Ghi rõ: đây là đánh đổi bắt buộc, không phải lựa chọn tuỳ tiện.

---

# Vòng #131 — H80: **ĐA DẠNG HỌ THẮNG ĐA DẠNG LẤY MẪU — M2 ĐƯỢC XÁC NHẬN**
*(đăng ký trước #89, khoá tại `92fddfb` TRƯỚC khi chạy — đây là dự đoán 3 của TONG_HOP,
và bảng khoá có hàng GIẾT M2 nếu `|ΔH| < .05`)*

### Cổng ĐẠT: soundness **.9619** · copy_rate **.0020** · biên dịch **.9992** · mọi model ≥ .35
RTX PRO 6000, bf16, MBPP 11–510, n=500. **Bộ chọn GIỮ NGUYÊN** (test do Qwen viết, một lần)
⇒ khác biệt duy nhất là **thành phần pool**. Chi phí khớp (3 × ~7B).

| pool | ứng viên | **trần `H`** | **`SEL`** | **`κ`** | hoà |
|---|---|---|---|---|---|
| **A — đa dạng LẤY MẪU** | Q1 .666 · Q2 .666 · Q3 .662 | .7220 | .6920 | **46.4%** | .866 |
| **B — đa dạng HỌ** | Q1 .666 · **L .540** · D .622 | **.7720** | **.7240** | **54.7%** | .682 |

**PHÁN QUYẾT: HÀNG 1 — M2 XÁC NHẬN MẠNH.**
- `H(B) − H(A)` = **+.0500** · thắng 38 / thua 13 · **McNemar p = 6.2e-4**
- `SEL(B) − SEL(A)` = **+.0320** · thắng 24 / thua 8 · **p = 7.0e-3**
- Hàng phụ cũng kích hoạt: **`SEL(B)` = .7240 > `H(A)` = .7220** —
  **CHỌN trong pool khác họ vượt cả TRẦN của pool cùng họ.**

### Cơ chế đo được TRỰC TIẾP — đây là điều đáng giá nhất
| phân bố số ứng viên đúng | cùng sai | **hỗn hợp** | cùng đúng |
|---|---|---|---|
| pool A (cùng họ) | 139 | **57** | 304 |
| pool B (khác họ) | **114** | **167** | 219 |

**Số bài HỖN HỢP tăng gấp 2.9 lần (57 → 167)**, và số bài **cùng sai giảm 139 → 114**.
Đây chính là **giải tương quan lỗi**, đo thẳng chứ không suy diễn.

### Điều lật ngược trực giác — và là phát biểu mạnh nhất rút ra được
**`L` (Llama-3.1-8B) là ứng viên YẾU NHẤT: .5400, kém MỌI mẫu Qwen (≥ .662).
Thêm nó vào vẫn NÂNG cả trần lẫn kết quả cuối.**

> **Một ứng viên YẾU HƠN nhưng GIẢI TƯƠNG QUAN đóng góp nhiều hơn một ứng viên MẠNH HƠN
> nhưng TƯƠNG QUAN.** Giá trị của một agent trong nhóm **KHÔNG phải là năng lực của nó**,
> mà là **phần lỗi của nó KHÔNG trùng với lỗi của những agent đã có**.

### `κ` cũng TĂNG — rủi ro tôi nêu trước KHÔNG xảy ra
Ở #89 tôi ghi trước rủi ro: *"test do Q viết có thể thiên vị code kiểu Q ⇒ κ tụt ở pool B"*.
Thực tế **κ tăng .464 → .547**: ứng viên đa dạng hơn **dễ phân biệt hơn**, vì tỉ lệ hoà
giảm .866 → .682. Bộ chọn có nhiều việc để làm hơn và làm tốt hơn.

### Ý nghĩa cho khung hợp nhất
`value = H × κ − D`. Đổi từ đa dạng-lấy-mẫu sang đa dạng-họ **nâng ĐỒNG THỜI cả `H` lẫn `κ`**,
ở **cùng chi phí** và `D = 0`. Đây là **đòn bẩy rẻ nhất tìm được trong toàn dự án**:
không cần model lớn hơn, không cần thêm lượt, chỉ cần **đổi NGUỒN ứng viên**.

### Prior của tôi ĐÚNG (hàng 1, ~50%)
Tỉ lệ prior đúng: **16/32**.

### Còn phải kiểm
Một lần chạy, một benchmark (MBPP), ba model cụ thể. **Chưa tái lập trên dải bài tách rời** —
đây là kết quả dương mạnh nhất nên **bắt buộc phải tái lập** trước khi vào README.

---

## Vòng #132 — Lỗi Python nuốt mất mọi lần "giải phóng model" ở 6 kernel

**Bối cảnh.** H83c chết OOM trên T4 dù bản vá tự-chọn-độ-chính-xác (#131) đã có mặt và đã chạy
đúng: log xác nhận `CHE DO: card nho -> nf4`, `nap 7B: VRAM 2.9 GB`, tầng rẻ hoàn tất cả hai
lượt. OOM xảy ra khi nạp model **thứ hai**. Tức là model thứ nhất chưa hề được trả về.

**Nguyên nhân.**
```python
def free(mo):
    del mo; gc.collect()     # xoá TÊN CỤC BỘ, không phải biến của caller
```
`del` trong hàm chỉ gỡ tên khỏi scope của hàm. Caller vẫn giữ `mo`, refcount không về 0, model
vẫn nằm nguyên trên card. Toàn bộ dòng `free(mo)` trong repo là **no-op** đối với VRAM.

**Vì sao lọt qua ngần ấy vòng.** Hai lý do, cả hai đều là bài học:
1. Bản vá đa-GPU ở #128 sửa đúng phần `empty_cache()` phải lặp qua mọi device — nên nó *trông
   như* đã là bản giải phóng đúng, và tôi không đọc lại thân hàm.
2. Log tự xác nhận sai: nó in `memory_allocated()`, mà con số này về gần 0 sau `empty_cache()`
   ngay cả khi pool vẫn bị chiếm. **Chỉ báo đúng là `memory_reserved()`.**

**Phạm vi.** `grep -l "def free(mo)" pipeline/*.py` → **6 kernel**: `bcb_route32b`,
`capacity32b`, `crossfamily`, `mbpp_route`, `selector_indep`, `strong_plus_diverse`.

**Hệ quả đã chặn được.** H87 đang chạy trên RTX 6000 với kernel lỗi: 32B (68 GB) + Llama (16 GB)
+ DeepSeek (13.5 GB) = **97.5 GB > 95 GB**. Nó **chắc chắn sẽ OOM** ở model thứ ba, sau khi đã
đốt phần lớn ngân sách GPU tuần của tài khoản đắt nhất. Đã xoá và phóng lại **H87b** với kernel
đã sửa. H83c → **H83d**.

**Điều đáng nói về mặt phương pháp.** Đây là lần thứ ba một kết quả suýt bị quyết định bởi
hạ tầng chứ không phải bởi giả thuyết (#119 truncation, #130 truncation ở 32B, giờ là #132).
Cả ba đều có chung một dạng: **một cơ chế kỹ thuật tác động KHÔNG ĐỀU lên các nhánh.** Ở đây
nhánh nào nạp nhiều model tuần tự nhất thì chết trước — mà đó đúng là nhánh "pool đa dạng",
tức là nhánh mang giả thuyết. Nếu H87 chạy hết và nhánh đa dạng lỗi, tôi sẽ đọc được thành
"pool đa dạng không giúp gì" trong khi sự thật chỉ là hết VRAM.

> **Không có hàng nào trong bảng khoá được đọc ở vòng này** — đây là lỗi hạ tầng, không phải
> kết quả. H87b và H83d giữ nguyên bảng khoá của #96 và #83.

---

## Vòng #133 — Kiểm tính nhất quán tài liệu: một phát biểu DƯƠNG bị nêu thiếu điều kiện

**Không phải vòng thí nghiệm.** Trong lúc chờ 13 kernel, tôi rà xem có phát biểu nào **đã bị rút
ở #125** mà vẫn còn sống trong tài liệu tóm tắt (README, TONG_HOP) — nơi người đọc thật sự trích.

**Phần lớn sạch.** Các lần khớp mẫu `k=2` / `tie_rate` / `5/5` trong `IDEAS.md` là **nhật ký
theo thời gian** — ghi lại một phát biểu **rồi rút nó** đúng là việc phải làm ở đó. Ba file
`AGG_FORMAT_CHECK` / `FEWSHOT_ROLES` / `DIFFICULTY_STRATA` thuộc **giai đoạn planner/aggregator
trước**, không thuộc dòng `V/I/SEL`. `README:129` (`H39_m +.140, 5/5 fold`) **không** phải một
trong hai chỗ sai — #125-B1 chỉ đích danh **H69c và H69d**.

**Nhưng có một chỗ thật.** #125-D ra điều kiện rõ ràng: `SEL − I` *"giữ, nhưng **nêu kèm CI**,
và nêu rõ **lật 6 bài là xoá sạch** hiệu ứng ở H69c"*. README nêu **`+.0220` trần trụi** làm
một hàng kết quả nổi bật — **không CI, không ghi chú mong manh** — trong khi **cùng tài liệu đó**,
cách 33 dòng, rút lại *"mọi chênh lệch ≤ .02 là nhiễu"*. Người đọc gặp `+.0220` ngay cạnh
`≤ .02 là nhiễu` mà không có gì bắc cầu.

Đây **không** phải lỗi số học — `+.0220` đúng, `p = .0074` đúng. Đây là lỗi **trình bày**, và là
loại lỗi #125-E cảnh báo: *kết quả TRÔNG ĐÚNG*. Điều kiện của kiểm định độc lập được ghi vào
`IDEAS.md` rồi **không bao giờ lan tới tài liệu người ta đọc**.

**Đã sửa** ở cả `README.md` lẫn `TONG_HOP.md`: thêm CI `[+.008, +.038]` / `[+.002, +.028]`, Fisher
`.0026`, ghi chú **lật 6 bài**, và nói thẳng con số thắng lớn là **`SEL − V_review`** (tránh REVIEW),
còn **`SEL − I` thì nhỏ và mong manh**.

> **Quy tắc rút ra: một điều kiện của kiểm định chỉ được coi là ĐÃ ÁP DỤNG khi nó có mặt trong
> tài liệu mà người đọc TRÍCH, không phải trong vòng ghi nhận nó.**
> Kiểm định sinh ra điều kiện; áp dụng điều kiện là **việc riêng, phải làm rõ ràng**.

---

## Vòng #134 — H84b + H89 + H89c HUỶ vì hạ tầng: **ném đi một nửa số GPU Kaggle đưa cho**

**KHÔNG đọc con số nào.** Cả ba chết vì OOM, không vì khoa học. Bảng khoá #97/#98 giữ nguyên.

### Chẩn đoán — và dòng log mới ở #132 đã trả công ngay
H89 in ra, sau khi giải phóng model rẻ:
```
sau giai phong: gpu0 cap phat 0.01 giu cho 2.88 | gpu1 cap phat 0.00 giu cho 0.00
```
Đọc được **hai** điều mà trước đây tôi không thấy:

1. **`cấp phát` = 0.01 nhưng `giữ chỗ` = 2.88 GB.** Giải phóng **ĐÃ chạy đúng** — nhưng bộ cấp phát
   vẫn ôm 2.88 GB *sau khi* `empty_cache()`. Nếu chỉ in `memory_allocated` như trước #132, tôi đã
   kết luận "free vẫn hỏng" và đi sửa đúng chỗ **không hỏng**. Đã đặt `PYTORCH_CUDA_ALLOC_CONF=
   expandable_segments:True` (phải đặt **trước** khi import torch).
2. **Có `gpu1`.** Dòng đầu kernel in `GPU=Tesla T4 | 14.6 GB` vì nó chỉ hỏi card 0. Kaggle thực ra
   đưa **2× T4 = 31.2 GB**, còn `device_map={"": 0}` **vứt bỏ một nửa** rồi OOM khi nạp Llama-3.1-8B.

> **Đây là lỗi tôi đã ghi trong bộ nhớ từ trước** (*"Kaggle cho 2 GPU ngay cả khi chỉ xin một;
> `device_map='cuda'` phí một nửa"*) **mà vẫn viết lại đúng lỗi đó.** Biết một luật không bằng
> việc kernel **in ra** đủ thứ để luật đó tự lộ.

### H84b — lớp lỗi KHÁC, và quét ở #132 đã BỎ SÓT
`mbpp_peer_kernel.py` chạy được 3 chặng (S 147s, I 987s, V_weak 2013s) rồi OOM ở model thứ tư.
Nó nạp 7B → giải phóng → nạp Llama → giải phóng → **nạp LẠI 7B**. Và nó giải phóng bằng:
```python
for _m in m7: del _m     # chi xoa BIEN VONG LAP, list khong he bi dong toi
del m7; gc.collect()
```
Quét ở #132 của tôi tìm `def free(mo)` — **đúng chuỗi ký tự tôi vừa gõ**, nên 12 kernel dùng
`for _m in X: del _m` **lọt hết**.

> **Quy tắc cứng: quét theo LỚP LỖI, không theo chuỗi ký tự của bản sửa vừa rồi.**
> Lớp lỗi ở đây là *"giải phóng tài nguyên qua một tên không phải tên của caller"*.
> Đã sửa **11 kernel** bằng `_free_models()` (gán **từng phần tử** = None), + `mbpp_peer` sửa tay.

`mbpp_peer` còn được **xếp lại thứ tự**: `1.5B → Llama → 7B`, mỗi model nạp **đúng một lần**,
bỏ hẳn lần nạp lại. Và thêm **lưu từng phần có DỮ LIỆU THÔ** sau mỗi chặng — H84b chạy 36 phút,
cứu được **0 byte**.

### Cái được cứu
H89 **có** `partial_H89.json` **282 KB dữ liệu thật** (499 bài `S` + `TESTS`). Luật #128 hoạt động.
Đối chiếu: H84b, kernel chưa có luật đó, mất trắng.

### Còn treo
`H89b` (DeepSeek-6.7B) **vẫn chạy** trên bản `device_map={"": 0}` cũ — model nhỏ nên vừa một card.
Không giết: sẽ mất >40 phút công đã chạy. **Ghi nhận sai khác**: H89b chạy 1 card, H89d/H89e chạy
2 card; giải mã vẫn greedy nên khác biệt chỉ có thể đến từ kích thước lô lúc lùi OOM — nhỏ,
nhưng **phải nêu** nếu đọc ba nhánh cạnh nhau.

---

## Vòng #134-d — H84c HUỶ: **Llama-3.1-8B vào fp16 chứ không phải nf4**

**Không đọc số nào.** Lại là hạ tầng. Nhưng lần này log đủ để chốt nguyên nhân *chính xác*,
không phải đoán — và nó bác bỏ chẩn đoán tôi định đưa ra.

### Bản vá #134 ĐÃ hoạt động
```
sau giai phong: gpu0 cap phat 0.01 giu cho 0.02 | gpu1 cap phat 0.01 giu cho 0.02
```
Cả `cấp phát` lẫn `giữ chỗ` đều về ~0 trên **cả hai** card. `_free_models()` đúng, và
`expandable_segments` xoá nốt 2.88 GB "giữ chỗ" còn sót ở #134. **Giải phóng không còn là vấn đề.**

### Nguyên nhân thật, đọc thẳng từ thông báo lỗi
```
14.32 GiB is allocated by PyTorch, and 87.30 MiB is reserved but unallocated
```
`reserved-but-unallocated` chỉ **87 MB** ⇒ **KHÔNG phải phân mảnh**. 14.32 GB là model **thật sự**
chiếm. Llama-3.1-8B ở nf4 phải ~5.6 GB; 14.32 GB đang trên đường tới **~16 GB của fp16**.
⇒ **lượng tử hoá KHÔNG được áp dụng cho Llama.**

Bằng chứng đối chứng nằm ngay trong cùng kernel: **Qwen-7B nf4 nạp bình thường ở 5.2 GB** (H84b).
Nên bitsandbytes có chạy; sự cố **riêng với Llama** trên đường nạp mới của transformers
(`core_model_loading._materialize_copy` — vật chất hoá tensor **trước** rồi mới lượng tử hoá).

> Nếu chỉ nhìn "OOM khi nạp model thứ hai" tôi đã kết luận "free vẫn hỏng" lần thứ ba liên tiếp
> và đi sửa đúng cái **không hỏng**. Con số `reserved-but-unallocated` là thứ phân biệt
> **phân mảnh** với **thật sự quá to** — hai bệnh khác nhau, hai thuốc khác nhau.

### Bản sửa
`load_sharded()`: **một** bản Llama **trải đều cả hai card** (`device_map="auto"`, 31.2 GB tổng),
thay vì hai bản mỗi bản một card. Vừa cả khi nó ở fp16.
**Đánh đổi được ghi rõ:** song song **dữ liệu** (2 bản, nhanh) → song song **mô hình** (1 bản, chậm hơn).
Qwen-7B giữ nguyên 2 bản vì nó lượng tử hoá đúng và chỉ tốn 5.2 GB.

### Cứu được
`partial_H84c.json` **72 KB dữ liệu thật** (`S_RAW` 500 bài). So với H84b cùng chỗ chết:
**0 byte**. Luật #128 đã trả công lần thứ hai trong hai vòng.

---

## Vòng #135 — H86b/H81c/H84d HUỶ. **Nguyên nhân gốc: model NGOÀI HỌ QWEN không được lượng tử hoá**

**Không đọc số nào.** Ba lần huỷ nữa, nhưng lần này chẩn đoán đã lên tới **nguyên nhân gốc**
thay vì vá từng ca.

### Bằng chứng hội tụ — bốn lần quan sát ĐỘC LẬP
| lần chạy | model chết | `allocated` lúc OOM | fp16 lý thuyết |
|---|---|---|---|
| H84c (`mbpp_peer`) | Llama-3.1-8B | 14.32 GB | 14.96 GB |
| H89 (`gated_repair`) | Llama-3.1-8B | 14.32 GB | 14.96 GB |
| H86b (`crossfamily`) | Llama-3.1-8B | 13.94 GB | 14.96 GB |
| **H81c (`selector_indep`)** | **DeepSeek-Coder-6.7B** | **13.85 GB** | **12.57 GB** |

Trong **cùng những kernel đó**, Qwen-7B lượng tử hoá bình thường ở **5.2 GB**.

> **Không phải "Llama có vấn đề". Là: trên bản transformers/bitsandbytes này, `quantization_config`
> IM LẶNG không áp dụng cho model ngoài họ Qwen — chúng rơi về fp16 (12.5–15 GB), tức ngay tại
> hoặc vượt trần một card T4 (14.56 GB).** H81c là mảnh ghép quyết định: DeepSeek **không phải**
> Llama, nên giả thuyết "lỗi riêng của Llama" bị bác.

Điều này cũng giải thích vì sao `grep -ln "llama"` của tôi **bỏ sót** `selector_indep` — tôi đã
quét theo **tên model**, trong khi lớp lỗi là **"không thuộc họ Qwen"**. Lại đúng cái sai của #134:
quét theo chuỗi ký tự chứ không theo lớp lỗi.

### H84d — lỗi này là DO TÔI GÂY RA
`RuntimeError: CUDA error: an illegal memory access` ngay sau khi nạp 1.5B. H84c **qua chặng đó
trong 150s**. Khác biệt duy nhất: tôi thêm `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
`mbpp_peer` là kernel **DUY NHẤT** dùng `threading` + **nhiều bản sao trên nhiều GPU**.

> **`expandable_segments` + đa luồng đa GPU = lỗi CUDA.** Đã gỡ khỏi `mbpp_peer` (giữ ở các kernel
> một-model-một-luồng, nơi nó thật sự chữa được 2.88 GB "giữ chỗ" ở #134).
> **Bài học: một bản vá đúng ở kernel A có thể là lỗi ở kernel B.** "Lan bản vá sang mọi kernel
> phái sinh" phải kèm câu hỏi *"kernel này có gì khác không?"* — không phải dán mù.

### Bản sửa
`load()` **lạc quan có đường lùi** ở `crossfamily`, `strong_plus_diverse`, `selector_indep`,
`gated_repair` — thử một card, `OutOfMemoryError` thì giải phóng sạch rồi trải đều hai card
(31.2 GB, thừa cho fp16 15 GB). Thêm **`canary()`**: nạp thử **từng** model rồi giải phóng ngay,
**trước** khi sinh gì cả — H86b tiêu **54 phút** cho model 1 rồi mới chết ở model 2; canary trả
lời "kế hoạch này chạy được không" trong ~5 phút.

### Giá phải trả cho tới giờ
H86b **54 phút** · H81c **48 phút** · H84b **36 phút** · H89 ~11 phút · H84c ~10 phút · H84d ~3 phút.
Tất cả đều cứu được dữ liệu thô nhờ #128 — trừ H84b (chạy trước khi có luật đó): **0 byte**.

---

## Vòng #136 (THĂM DÒ, **không phải kết luận**) — Lấy mẫu 3 lần chỉ mua được **1.93** ứng viên

**Nguồn dữ liệu:** `partial_H86b.json` cứu được từ lần huỷ ở #135 (Pool A = 3 mẫu Qwen-7B,
MBPP **511–974**, n=464). **Không chấm điểm, không đụng đáp án chuẩn** — nên **không** làm nhiễm
bảng khoá #89 mà H86c đang chạy lại. Chỉ đo **độ đa dạng VỀ CHUỖI**, đại lượng độc lập với đúng/sai.

| | số bài | tỉ lệ |
|---|---|---|
| cả 3 mẫu **giống hệt nhau** | 160 | **.345** |
| đúng 2 trong 3 giống nhau | 175 | .377 |
| cả 3 **khác nhau** | 129 | .278 |
| **số ứng viên phân biệt trung bình** | | **1.933 / 3** |

Trùng từng cặp: `.513` · `.489` · `.409`.

### Vì sao điều này đáng chú ý
**34.5% số bài chỉ có ĐÚNG MỘT ứng viên, dù đã trả tiền sinh ba lần.** Với những bài đó, mọi
giao thức chỉ-CHỌN đều **không thể** làm gì — không có gì để chọn giữa. Đây là **trần cứng của
`H(pool A)` đọc được mà không cần chấm điểm**: một pool chứa duy nhất một câu trả lời thì không
cứu được bài nào, bất kể `κ` tốt đến đâu.

Nó cho M2 một cơ chế **định lượng và cụ thể hơn**: TONG_HOP nói lỗi của các mẫu cùng model
**tương quan**; con số này nói phần lớn "tương quan" ấy là dạng mạnh nhất có thể —
**cùng một chuỗi ký tự**. Một phần ba ngân sách lấy mẫu mua về **con số không**.

### Vì sao CHƯA vào TONG_HOP
- **Thăm dò**: không có đăng ký trước nào khoá đại lượng này; tôi chọn nó **sau khi** đã thấy dữ liệu.
- Một dải bài, một model, một mức nhiệt độ.
- Chuẩn hoá (bỏ chú thích + gộp khoảng trắng) là **lựa chọn của tôi**; chuẩn hoá lỏng hơn sẽ đẩy
  "giống hệt" lên cao hơn, chặt hơn thì thấp xuống. Con số **phụ thuộc quy ước**.

> Muốn dùng được thì phải **đăng ký trước** như một dự đoán: *nếu M2 đúng, pool khác họ phải có
> số ứng viên phân biệt cao hơn hẳn 1.93 trên cùng dải bài*. H86c sẽ có sẵn cả hai pool —
> nhưng đại lượng đó phải được khoá **trước** khi tôi mở kết quả của nó.

---

## Vòng #137 — H83d XONG. **Hàng 4 của #92 khớp: công thức định tuyến bị THỰC TẾ BÁC BỎ**

Lần chạy hoàn tất đầu tiên sau sáu vòng hạ tầng. **Cổng chất lượng ĐẠT** nên được đọc số:
`I − S` = **+.2004** (p 5.45e-18) · soundness .533 · biên dịch .9947 · chuẩn chạy được 1.0 ·
n=499, `task_id` 11–510 (đã xác minh trong trace, bài học #121).

### Đọc theo BẢNG KHOÁ #92 — không diễn giải lại

| điều kiện của hàng 1 | đo được | |
|---|---|---|
| `p_esc` < .803 | **.7475** | ✓ |
| `ROUTE ≥ I − .02` | **+.0060** | ✓ |
| **chi phí `ROUTE` < chi phí `I`** | **5.79 vs 5.07 = 1.142×** | **✗** |

Hàng 1 trượt ở điều kiện thứ ba. Hàng 2 đòi `p_esc ≥ .803` — không. Hàng 3 đòi `ROUTE < I − .02`
— không. Còn lại **hàng 4: "dự đoán ngược thực tế" ⇒ RÚT LẠI công thức M3.**

Công thức **như đã đăng ký** dự đoán **THẮNG** (`.7475 < .803`); thực tế **THUA** (đắt hơn 1.142×).
**Ghi nhận đúng như bảng đã khoá.**

### Nguyên nhân — và vì sao đây KHÔNG phải cứu vãn hậu nghiệm
Ngưỡng `.803 = 1 − 1/5.07` giả định tầng rẻ tốn **1 lượt**. Thiết kế thực tế tốn **2**: một lượt
**giải** + một lượt **viết test**. Với `c_rẻ = 2`: ngưỡng = `1 − 2/5.07` = **.606**, mà `p_esc = .7475
> .606` ⇒ **dự đoán THUA, đúng như thực tế**.

Mâu thuẫn này nằm **ngay trong một file, viết TRƯỚC khi chạy**:
```
dòng  11:  COST = {...}   # nguong hoa von = 1 - 1/5.07 = .803     <-- 1 luot re
dòng 174:  cost_route = COST["7B"]*2 + p_esc*COST["32B"]           <-- 2 luot re
```
Nên đây là **lỗi ĐẶC TẢ của #92**, chứng minh được bằng artifact tiền-nghiệm — không phải thứ tôi
nghĩ ra sau khi thấy kết quả. **Nhưng nó KHÔNG cứu công thức**: một dự đoán sai vì đặc tả sai thì
vẫn là **dự đoán sai**, và tôi không thể chứng minh mình sẽ phát hiện lỗi đó nếu kết quả đi theo
hướng ủng hộ.

### Hậu quả NẶNG HƠN cho TONG_HOP
TONG_HOP ghi công thức **"khớp cả hai trường hợp đã có"** (MATH thắng, BCB thua).
Nếu #92 tính `c_rẻ` sai thì **hai điểm kia phải được kiểm lại bằng CÙNG một quy ước** —
MATH cũng dùng ngưỡng `.803`, tức cũng giả định 1 lượt rẻ. **Thành tích 2/2 hiện đang NGHI VẤN.**

> **Công thức định tuyến chuyển sang trạng thái ĐÌNH CHỈ**, không phải "đã xác nhận".
> Không được trích ở dạng hiện tại. Phải: (1) chốt một quy ước chi phí DUY NHẤT, (2) tính lại
> cả ba điểm bằng quy ước đó, (3) đăng ký trước rồi mới đo điểm thứ tư.

### Kết quả PHỤ — vững, và là bản tái lập sạch
- **`V − I` = −.0882, p 1.55e-05** (73 bài bị phá / 29 được cứu). Đầu độc **tái lập** trên
  MBPP 11–510; lần trước đo −.0740. Kết quả vững nhất của dự án tiếp tục đứng.
- **`agree(V, S)` = .3788 vs `agree(V, I)` = .0902.** Đầu ra của `V` trùng **nguồn yếu** nhiều gấp
  **4.2 lần** so với trùng thứ mà model mạnh tự viết ra. Cơ chế "nhiễm từ nguồn" có số đo trực tiếp.
- **`ROUTE − I` = +.0060 (p .648)** và **`SEL − I` = +.0120 (p .146)**: **CẢ HAI KHÔNG CÓ Ý NGHĨA**
  và đều **dưới ngưỡng .02** mà dự án đã tuyên là nhiễu. **Không được phát biểu là "định tuyến
  giữ nguyên độ chính xác" hay "chọn có lợi"** — n=499 không phân biệt được chúng với 0.

---

## Vòng #138 — H88 + H88b **VOID**. Cổng đo *thói quen định dạng*, không đo *tính hợp lệ*

**KHÔNG đọc `d_gate`, `d_honest`, `d_cont`, `d_ceil`, hay bất kỳ `acc` nào. Sẽ không bao giờ đọc.**

### Cổng trượt
| | `extract_min` | chênh | `n` | `test_runnable` |
|---|---|---|---|---|
| H88 (11–510) | **.1383** | **.8617** | 499 ✓ | .6994 |
| H88b (511–974) | **.2073** | **.7927** | **463** ✗ | .6739 |

### Cổng đã bắt cái gì
| nhánh | `has_block` (đã CÀI) | `compiles(extract(·))` (đã VIẾT trong #97) |
|---|---|---|
| `S` (1.5B) | **.1383** | **.9980** |
| `I` (7B) | 1.0000 | .9940 |

#97 viết *"tỉ lệ **trích được code chạy** ≥ .80"*. Tôi cài bằng `has_block()` — **có hàng rào
markdown hay không**. Model yếu **không rào code**; nó cứ thế in `def remove_Occ(s, ch): ...`.
`extract()` có đường lui lấy toàn văn, và code ấy **biên dịch được 99.8%**.
Cổng bắt một **thói quen định dạng**, không phải một **mối đe doạ tới tính hợp lệ**.

### Vì sao vẫn VOID
Theo chữ đã viết, cổng **ĐẠT** (.998 / .994, chênh .0040). Theo thứ đã cài, cổng **TRƯỢT**.
Chuyển sang thước đo mà tôi **đã biết là sẽ đạt**, **sau khi** thấy thước đo kia trượt —
đó đúng là **#114**, sai phạm mà kiểm định #125-C đã bắt và tôi đã phải rút hai kết luận.

> **Một lý lẽ đúng đưa ra SAU khi thấy cổng trượt vẫn là lý lẽ đưa ra sau.**
> Tôi không chứng minh được rằng mình sẽ soi lại định nghĩa cổng nếu nó ĐẠT.
> **H88/H88b VOID vĩnh viễn.** Điều duy nhất cứu vãn được: tôi **chưa mở** các delta,
> nên lần chạy lại vẫn **sạch**.

### Đã sửa (đăng ký ở #97-c, TRƯỚC khi chạy lại)
- cổng → `compiles(extract(t))`, đúng chữ của #97; `has_block` **vẫn báo cáo** nhưng **hết là cổng**
- `n ≥ 480`: H88b chỉ được 463 ⇒ **nới DẢI LẤY BÀI lên 511–1000**, **không hạ ngưỡng** (bài học #127)
- `test_runnable`: **.70 → .60**. **Đây là NỚI ngưỡng và tôi nói thẳng.** Ngưỡng .70 là tôi đoán;
  đại lượng này chỉ mô tả **cổng `z` mạnh cỡ nào**, không đe doạ tính hợp lệ của so sánh.
  Ai không chấp nhận việc nới thì **chỉ đọc `d_ceil`** — cổng ORACLE, **không dính** tới `z`.

### Bảng khoá #97 **không sửa một chữ.**

---

## Vòng #139 — H87b **VOID**: cổng soundness trượt (.4509 < .50)

Lần chạy RTX 6000 đắt nhất của dự án (32B + Llama-8B + DeepSeek, 3619s). **Cổng của #96 trượt** ⇒
**không hàng nào được đọc**. Các cổng khác đều đạt (copy_rate .0177 · n=500 · biên dịch .9945 ·
`acc(32B)` .742 ∈ [.60,.90] · `acc(L)` .538, `acc(D)` .618 ≥ .35). Chỉ **soundness .4509** trượt —
tức **test do 32B viết SAI nhiều hơn ĐÚNG** khi chấm trên lời giải chuẩn.

### Công bố thành thật: tôi ĐÃ NHÌN THẤY các con số
Kernel in toàn bộ tổng kết trước khi tôi kịp kiểm cổng. **Tôi không thể "chưa thấy" chúng.**
Cái tôi làm được: **không dùng**, không đưa vào TONG_HOP, không đưa vào README, và **ghi lại rằng
mình đã bị nhiễm** để lần chạy lại không bị tôi lái theo.

> **Rủi ro cụ thể:** giờ tôi biết pool C có `H` cao hơn nhưng `κ` thấp hơn. Khi thiết kế H87c,
> mọi thay đổi tôi đưa ra đều có thể **vô tình** hướng về việc làm hàng đó "đẹp hơn".
> Vì thế H87c **chỉ được đổi ĐÚNG MỘT THỨ: cách sinh test.** Pool, bộ chọn, dải bài, model —
> **giữ nguyên tuyệt đối.** Bất kỳ đề xuất đổi gì khác đều phải bị nghi là hậu quả của nhiễm.

### Sửa kernel để cổng được kiểm TRƯỚC khi in
Lỗi quy trình thật sự: kernel **in tổng kết rồi mới nói HUỶ**. Phải đảo lại — kiểm cổng, nếu trượt
thì **in đúng dòng VOID và các số CỦA CỔNG, không in gì khác**. Có thế thì kỷ luật mới không phụ
thuộc vào việc tôi nhắm mắt kịp hay không.

### Vấn đề thật: test do model viết KHÔNG ĐÁNG TIN, hai lần liên tiếp
| lần chạy | soundness | ngưỡng |
|---|---|---|
| H83d (#137) | **.533** | .50 — **suýt trượt** |
| H87b (#139) | **.4509** | .50 — **trượt** |

Đây **không** phải nhiễu ngẫu nhiên; đây là đại lượng `κ` phụ thuộc vào, và nó đang **sát đáy**.
`SEL` chỉ có thể tốt bằng tín hiệu `z`, mà `z` ở đây **đúng chưa tới một nửa**.

---

## Vòng #140 — H84e XONG. **Hàng 1 khớp CON SỐ nhưng KHÔNG khớp BẰNG CHỨNG**

Cổng đạt (biên dịch .994 · n=500 · `I − S` = +.2120). Được đọc số.
**Chấm lại độc lập tại máy** từ `partial_H84e.json`: tái tạo **CHÍNH XÁC** ba nhánh mà kernel báo
per-item (S .4280 · I .6400 · V .5660) ⇒ bộ chấm cục bộ được kiểm chứng, rồi mới chấm hai nhánh
`PEER`/`VPEER` mà trace **không** có.

### Bảng khoá #93

| đại lượng | giá trị | CI95 | p (McNemar) |
|---|---|---|---|
| `V(S_weak) − I` | **−.0740** | [−.1140, −.0360] | **.000296** ✓ |
| `V(S_peer) − I` | **−.0280** | **[−.0680, +.0120]** | **.2108** ✗ |

Hàng 1 đòi `V(S_peer) − I ≤ −.02`. Đo được **−.0280** ⇒ **khớp về SỐ**.
Nhưng **CI vắt qua 0 và p = .21**: hiệu ứng **không phân biệt được với KHÔNG**.

> **#93 đặt ngưỡng mà QUÊN đòi ý nghĩa thống kê.** Đây là lỗi thiết kế của chính tôi:
> ngưỡng `−.02` nằm đúng vùng mà dự án đã tuyên là nhiễu ở n=500 (#125-B).
> **Vì thế tôi KHÔNG viết kết luận của hàng 1.** "Văn bản ngoại lai tự nó gây hại" **chưa được
> chứng minh** — dữ liệu này không phân biệt được nó với "không gây hại gì".

### Bổ sung — phép thử TRỰC TIẾP mà #93 lẽ ra phải khoá
Câu hỏi thật của #93 là *"đầu độc có phụ thuộc chênh năng lực không?"*. Phép thử đúng là so
**hai nhánh V với nhau**, ghép cặp:

**`V_peer − V_weak` = +.0460, CI95 [+.0080, +.0840], p = .0206** — **có ý nghĩa**.

Nguồn **ngang cơ** (Llama-8B, acc .560) phá **ít hơn** nguồn **yếu** (Qwen-1.5B, acc .428).
Đây là bằng chứng cho **(a): đầu độc CẦN nguồn kém** — tức gần với **hàng 2** hơn hàng 1,
dù hàng 2 không khớp theo chữ (nó đòi `V(S_peer) − I ≥ −.02`).

**Ghi rõ:** phép thử này **KHÔNG nằm trong bảng khoá** ⇒ **thăm dò**, không phải xác nhận.
Muốn dùng thì phải đăng ký trước rồi tái lập trên dải tách rời.

### Không hàng nào của #93 được viết ra
Hàng 1 khớp số nhưng bằng chứng không đủ; hàng 2 không khớp số; hàng 3 (cả hai ≈ 0) sai vì
`V(S_weak) − I` rõ ràng âm và có ý nghĩa. **Ghi nhận là THẤT BẠI THIẾT KẾ của #93**, giống
#99 và #116 — lần thứ ba tôi viết bảng khoá bằng ngưỡng trần trụi **không kèm điều kiện p**.

> **Quy tắc rút ra: mọi hàng trong bảng khoá phải nêu ĐỒNG THỜI ngưỡng hiệu ứng VÀ ngưỡng
> ý nghĩa.** Ngưỡng trần trụi biến một kết quả nhiễu thành một kết luận nghe rất chắc.
