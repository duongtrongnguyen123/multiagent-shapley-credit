# Phân tầng độ khó: 57% số câu KHÔNG THỂ có hiệu ứng — và đó là lý do mọi thứ chìm dưới sàn nhiễu

Tính offline trên trace đã có (`analysis/difficulty_strata.py`), không tốn GPU.

## Vì sao làm

`ROLE_SPECIALIZATION.md` và main đều kết luận *"verification chỉ có tác dụng ở giữa dải độ khó"*
— nhưng đó là so sánh **giữa 4 ô**, tức 4 điểm dữ liệu. Nếu cơ chế là thật thì nó phải xuất hiện
cả **bên trong một lần chạy**: các câu khó/dễ khác nhau trong cùng một ô cũng phải cho hiệu ứng
khác nhau theo cùng hình dạng.

Thước đo độ khó: **số lời giải đúng trong K mẫu độc lập của Solver**. Đây là độ khó *đối với
chính model này*, tốt hơn nhãn Level do người gán (mà MATH-500 trên Kaggle cũng không có).

## Kết quả then chốt — MATH 1.5B, K=5 (n=150)

| số mẫu đúng /5 | n | Solver | vote5 | Δ |
|---|---|---|---|---|
| **0/5** — quá sức | **48 (32%)** | .000 | .000 | **+0.000** |
| 1/5 | 20 | .000 | .000 | +0.000 |
| 2/5 | 15 | .333 | .600 | **+0.267** |
| 3/5 | 12 | .583 | 1.000 | **+0.417** |
| 4/5 | 18 | .722 | 1.000 | **+0.278** |
| **5/5** — quá dễ | **37 (25%)** | 1.000 | 1.000 | **+0.000** |

**Gộp tầng giữa (1–4/5): n=65 (43%), .385 → .600 = +21.5 điểm.**

## Phát hiện chính

**57% số câu KHÔNG THỂ có hiệu ứng — vì lý do toán học, không phải vì method kém.**

- **32% câu (0/5)**: không mẫu nào đúng → không có gì để chọn. Mọi cơ chế chọn lọc đều bất lực.
- **25% câu (5/5)**: mọi mẫu đều đúng → không có gì để phá, cũng không có gì để cải thiện.

Chỉ **43% số câu** là nơi việc chọn lọc có ý nghĩa. Và ở đó hiệu ứng là **+21.5 điểm** — gấp
**4 lần sàn nhiễu**.

Nhưng khi tính trung bình trên toàn bộ 150 câu, +21.5 điểm bị pha loãng bởi 57% câu bất động
thành **+9.3 điểm** (đúng con số `vote5` vs `S` đã đo ở `EXTRA_PASS_FINDING.md`).

## Điều này giải thích cả dự án

Suốt dự án, mọi can thiệp đều cho hiệu ứng 0–5 điểm và chìm dưới sàn nhiễu. Lý do bây giờ rõ:

> **Hiệu ứng thật bị pha loãng ~2.3 lần vì hơn một nửa số câu nằm ngoài tầm với của bất kỳ cơ
> chế phối hợp nào.**

Đây không phải "multi-agent vô dụng" mà là **đo sai mẫu số**. Một can thiệp mạnh +21 điểm trên
tập nó có thể tác động sẽ hiện ra thành +9 điểm trên tập đầy đủ — và một can thiệp trung bình
+10 điểm sẽ thành +4, tức chìm dưới sàn nhiễu và bị kết luận là "không có tác dụng".

## Verifier theo tầng — mẫu hình khác, yếu hơn

Dùng nhánh Solver-một-mình làm proxy độ khó:

| ô | câu DỄ (S-một-mình đúng) | câu KHÓ (S-một-mình sai) |
|---|---|---|
| GSM8K 1.5B | n=96, +0.000 (cứu 10/phá 10) | n=54, **−0.019** (cứu 7/phá 8) |
| MATH 1.5B | n=62, **+0.048** (cứu 8/phá 5) | n=88, **−0.045** (cứu 5/phá 9) |
| GSM8K 7B | n=91, −0.011 (0/1) | n=9, +0.000 (0/0) |
| MATH 7B | n=72, +0.000 (0/0) | n=28, **+0.036** (2/1) |

**Verifier hành xử ngược mong đợi ở 1.5B:** nó *giúp* trên câu dễ (+0.048 MATH) và *hại* trên
câu khó (−0.045). Với câu khó, Solver sai và Verifier — cùng năng lực — cũng sai, nhưng còn thêm
cơ hội phá những gì tình cờ đúng.

Ở 7B thì đảo lại: giúp nhẹ trên câu khó (+0.036), trung tính trên câu dễ. Khớp với việc Verifier
7B chỉ can thiệp 14% số lượt.

⇒ **Không có "dải độ khó vàng" cho Verifier bên trong một ô.** Kết luận "chỉ giúp ở giữa dải"
đúng khi so **giữa các ô** (theo accuracy tổng của Solver) nhưng **không tái lập bên trong một
ô**. Hai hiện tượng khác nhau, không nên gộp.

## So sánh vote5 vs agg5 theo tầng — thêm một bằng chứng

| tầng | vote5 Δ | agg5 Δ |
|---|---|---|
| 1/5 | +0.000 | +0.100 |
| 2/5 | +0.267 | +0.267 |
| 3/5 | +0.417 | **−0.167** |
| 4/5 | +0.278 | +0.167 |
| **gộp giữa** | **+0.215** | +0.108 |

Ở tầng 3/5 — nơi **đa số mẫu đã đúng** — Aggregator LLM làm **hỏng** (−0.167) trong khi bỏ phiếu
đạt 100%. Đây là bằng chứng trực tiếp nhất cho kết luận ở `AGGREGATOR_EXPLAINED.md`: nó không
đếm phiếu, nó chép, nên nó phá được cả những ca mà đa số đã đúng sẵn.

## Hệ quả thực dụng

1. **Báo cáo hiệu ứng nên kèm mẫu số.** "+9.3 điểm trên toàn tập" và "+21.5 điểm trên 43% câu
   có thể tác động" là cùng một dữ liệu, nhưng câu thứ hai mới nói đúng cơ chế.
2. **Sàn nhiễu nên tính trên tầng giữa**, không phải toàn tập — hiện tại ta đang đòi một can
   thiệp phải vượt 5 điểm trên mẫu số bị pha loãng 2.3 lần.
3. **Định tuyến theo `số mẫu đúng` là bất khả thi** (cần biết đáp án), nhưng **độ đồng thuận
   giữa K mẫu thì quan sát được**. Câu 0/5 và 5/5 đều có đồng thuận cao (tất cả sai giống nhau,
   hoặc tất cả đúng) — đây có thể là tín hiệu định tuyến khả thi, khác với các tín hiệu đã thất
   bại (H3 gate, fidelity, độ dài).

## Giới hạn

- n=150, MATH 1.5B, một lần chạy. Các tầng chỉ có 12–48 câu nên Δ từng tầng rất nhiễu; con số
  đáng tin là **tỉ lệ tầng biên 57%** (đếm trực tiếp) và **Δ gộp tầng giữa +21.5**.
- Phần Verifier dùng proxy độ khó thô (đúng/sai nhị phân) vì rescue trace chỉ có 1 mẫu Solver.
- Chưa kiểm ở 7B với K mẫu — chỉ có aggk ở 1.5B.
