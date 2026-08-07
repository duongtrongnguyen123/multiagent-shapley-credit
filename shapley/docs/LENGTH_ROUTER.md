# Route verify theo độ dài lời giải — GIẢ THUYẾT BỊ BÁC

Tính offline trên `results_rescue/gsm8k/traces.json` (150 câu, 5 fold) bằng
`analysis/length_router.py`. Không tốn GPU.

## Giả thuyết

`VERIFIER_RESCUE.md` ghi nhận: trong các ca Solver sai, lời giải **ngắn** được Verifier cứu
**50%**, lời giải **dài** chỉ **24%**. Và Verifier ròng bằng 0 (cứu 17 / phá 18).

Suy ra: nếu **chỉ verify khi lời giải ngắn**, ta giữ được phần cứu và bỏ phần phá.

Điều khiến hướng này đáng thử hơn các routing đã thất bại (H3 gated verification, fidelity
routing): **độ dài quan sát được TRƯỚC khi verify** — không cần biết trước câu nào sai.

## Phép đo

Mọi câu trong trace đều đã có **cả** nhánh S lẫn nhánh V, nên chính sách *"verify nếu
len(S) < T"* tính được **chính xác** bằng cách chọn nhánh tương ứng cho từng câu. Đây là
counterfactual thật, không phải mô phỏng.

## Kết quả

| chính sách | acc | Δ vs chỉ-S | fold cùng dấu | % câu được verify |
|---|---|---|---|---|
| không bao giờ verify (chỉ S) | **0.7000** | — | — | 0% |
| luôn verify (cấu hình hiện tại) | 0.6933 | −0.007 | 2/5 | 100% |
| verify nếu len < 100 | 0.6667 | −0.033 | 2/5 | 63% |
| verify nếu len < 150 | 0.6733 | −0.027 | 2/5 | 66% |
| verify nếu len < 200 | 0.6733 | −0.027 | 3/5 | 69% |
| verify nếu len < 300 | 0.6733 | −0.027 | 3/5 | 74% |
| verify nếu len < 600 | 0.6667 | −0.033 | 2/5 | 83% |
| *[trần oracle, không khả thi]* | *0.8133* | *+0.113* | | |

**Không ngưỡng nào thắng.** Mọi chính sách route đều **kém hơn cả việc không verify gì cả**, và
kém hơn cả "luôn verify". Ngưỡng tốt nhất (T=150) chỉ đạt 2/5 fold cùng dấu.

## Vì sao giả thuyết sai

Bảng cơ chế cho câu trả lời — nó có **bốn** ô, còn giả thuyết chỉ nhìn hai:

| nhóm | n | S sai | **V cứu** | S đúng | **V phá** |
|---|---|---|---|---|---|
| ngắn (<200) | 103 | 24 | **12 (50%)** | 79 | **16 (20%)** |
| dài (≥200) | 47 | 21 | 5 (24%) | 26 | 2 (8%) |

Lời giải ngắn đúng là **được cứu nhiều hơn** (50% vs 24%) — phần đó của phát hiện cũ vẫn đúng.
Nhưng chúng cũng **bị phá nhiều hơn** (20% vs 8%). Tính theo số câu tuyệt đối:

- nhóm ngắn: cứu **12**, phá **16** → **ròng −4**
- nhóm dài: cứu 5, phá 2 → ròng **+3**

**Nhóm ngắn là nhóm Verifier gây hại nhất, không phải nhóm nó giúp nhiều nhất.** Route *về phía*
lời giải ngắn tức là route thẳng vào vùng lỗ.

Lỗi suy luận của tôi: tôi lấy tỉ lệ cứu **có điều kiện trên các ca S sai** (50% vs 24%) rồi suy
ra lợi ích ròng, mà bỏ qua rằng nhóm ngắn có **79 câu S vốn đã đúng** để Verifier phá — nhiều
gấp ba nhóm dài (26 câu). Tỉ lệ cao trên một nhóm nhỏ không thắng nổi thiệt hại trên một nhóm
lớn.

## Điều còn lại

**Trần oracle +11.3 điểm** (0.700 → 0.813): nếu biết trước câu nào nên verify thì có 11 điểm để
lấy. Verifier **có** thông tin thật, chỉ là ta chưa có tín hiệu nào tách được ca cứu khỏi ca phá.
Độ dài không phải tín hiệu đó.

Đây là lần thứ **ba** một tín hiệu quan sát-trước-khi-verify thất bại trong dự án này — sau H3
(gated verification: cổng kêu 0/250 lần) và fidelity routing (không được ủng hộ, underpowered).
Ba lần thất bại theo ba cách khác nhau, cùng chỉ về một chỗ: **quyết định "có nên verify không"
khó ngang việc verify.**

## Giới hạn

- n = 150, GSM8K, 1.5B. Bản MATH chưa có (`rescue-fullpipe-math` đang chạy) — script tự chạy
  luôn phần MATH khi trace về.
- Ngưỡng T được chọn **trên chính dữ liệu này** nên có overfit; nhưng điều đó chỉ làm kết quả
  **tốt hơn** thực tế, mà nó vẫn thua — nên kết luận bác bỏ càng chắc.
- Sàn nhiễu ~5 điểm vẫn áp dụng: các Δ ở đây (−2.7 đến −3.3 điểm) nhỏ hơn ngưỡng đó, nên phát
  biểu chặt chẽ là *"không có bằng chứng route theo độ dài giúp ích"*, chứ không phải *"chắc
  chắn có hại"*.
