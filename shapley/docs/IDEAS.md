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
