# Khi nào phối hợp đa tác tử LLM tạo ra giá trị? Một khảo sát thực nghiệm dưới ba phép kiểm soát

**BẢN THẢO v0.1** — các chương §2, §4 đang chờ người phụ trách; xem khối TODO.

Nhóm thực hiện: Nguyên · Đức · Tùng Dương *(TODO: thống nhất thứ tự tên và việc ghi nhận Quân)*

> **Luận điểm:** Chênh lệch năng lực giữa hai model tạo ra cơ hội cải thiện; giao thức phối hợp
> quyết định cơ hội đó được khai thác hay bị phá huỷ.

*Quy ước: số thập phân dùng dấu phẩy; công thức trong khối mã giữ ký hiệu gốc. Thuật ngữ và ký
hiệu định nghĩa ở Phụ lục A (rút từ `THUAT_NGU.md`). Mức tin cậy của từng số liệu theo
`HUONG_DAN_CONG_TAC.md`: **mức A** = tiền đăng ký + điều kiện hợp lệ, hoặc 5 fold qua t-test;
**mức B** = thăm dò/hậu nghiệm, ghi rõ tại chỗ.*

---

## Tóm tắt

Các hệ đa tác tử LLM (planner–solver–verifier–aggregator, debate, sinh-rồi-sửa) thường được báo
cáo là cải thiện so với một model đơn lẻ. Khảo sát này đo lại nhận định đó trên GSM8K, MATH-500,
MBPP và HumanEval với các model Qwen2.5 (1.5B–32B), Llama-3.1-8B và DeepSeek-Coder-6.7B, dưới
**ba phép kiểm soát** mà phần lớn báo cáo trong lĩnh vực bỏ qua: (1) **cùng ngân sách token** —
pipeline bốn vai tốn 3–6,6 lần chi phí của một lượt giải; (2) **đúng mốc so sánh** — người triển
khai đã có model mạnh trong tay, nên đại lượng đúng là chênh lệch với *model mạnh chạy một mình*
(`V − I`), không phải với model yếu (`V − S`); (3) **đúng mẫu số** — 57% số câu không thể có hiệu
ứng vì mọi mẫu đều đúng hoặc đều sai, làm hiệu ứng thật bị pha loãng 3,3 lần.

Sau ba kiểm soát, bức tranh đảo ngược có hệ thống: hiệu ứng dương lớn nhất (+14,0 điểm) chỉ tồn
tại khi so với model yếu; so cùng token với model mạnh đơn lẻ thì hoà hoặc kém. Nguyên nhân được
tách bằng một đẳng thức đại số `Δ_ceil = A − B + C` và một thí nghiệm tiền đăng ký tái lập trên
hai miền: thiệt hại đến từ việc model mạnh **tiếp xúc với nội dung sai** (trên MATH: −27,2 điểm
trên tầng artifact sai; độ chính xác rơi từ 46,4% xuống 19,2%). Cùng một biến chênh lệch năng lực
làm giao thức **tuyển chọn** thắng lớn nhưng giao thức **sửa chữa** thua — nghịch lý được giải vì
tuyển chọn có `B ≈ 0` theo cấu trúc còn sửa chữa phải trả `B`, và `B` tăng theo chênh lệch.

Khuyến nghị thực tiễn: *dùng model nhỏ để giải, model lớn để soát; không cho model lớn xem bài làm
của model nhỏ với mục đích sửa; ở miền có bộ kiểm đúng đắn (code chạy được test) thì phối hợp đạt
đúng trần oracle, ở miền không có thì tín hiệu học được dù AUC 0,893 cũng gần như vô dụng.*

---

## §1. Mở đầu

Việc ghép nhiều vai LLM thành một hệ — planner vạch kế hoạch, solver giải, verifier kiểm,
aggregator tổng hợp — có tạo thêm giá trị so với một model đơn lẻ không? Và nếu có, giá trị đến
từ đâu: từ **cấu trúc phối hợp**, hay từ thứ khác?

Câu hỏi này khó trả lời hơn vẻ ngoài, vì ba lý do đo lường:

1. **Ngân sách.** Pipeline bốn vai tốn 2,9 lần ký tự trên GSM8K và 6,63 lần trên MATH so với một
   lượt giải. So sánh hệ 3× với hệ 1× rồi kết luận "phối hợp có giá trị" là so sánh không công bằng.
2. **Mốc so sánh.** Gần như mọi công trình sinh-rồi-sửa đo cải thiện so với model *bị sửa* — tức
   model yếu. Nhưng lựa chọn thật của người triển khai, vốn đã có model mạnh trong pipeline, là:
   chạy pipeline hay **gọi thẳng model mạnh**. Khi đổi mốc, dấu của hiệu ứng đảo ngược.
3. **Mẫu số.** Trên hơn một nửa số câu, không cơ chế phối hợp nào có thể tác động (mọi mẫu đều
   đúng hoặc đều sai). Hiệu ứng trung bình trên toàn tập vì thế đánh giá thấp hiệu ứng thật.

Khảo sát này áp cả ba kiểm soát cùng lúc, trên ba nhánh nghiên cứu độc lập của nhóm — phân rã
đóng góp theo vai bằng giá trị Shapley, phân tích chi phí–lợi ích của cơ chế định tuyến, và phân
tích luồng thông tin của giao thức sửa chữa — rồi hợp nhất chúng trong một khung duy nhất.

**Đóng góp:**

1. Khung phân rã giá trị `value = H(pool) × κ(z) − D(protocol)` thống nhất ba nhánh (§3).
2. Bằng chứng nhất quán trên hai thiết kế độc lập rằng **chênh lệch năng lực**, không phải số
   lượng vai hay họ model, là biến quyết định (§5.4, §5.7).
3. Một **đẳng thức đại số** `Δ_ceil = A − B + C` tách cơ hội khỏi thiệt hại, khớp tuyệt đối trên
   19/19 cặp đo (§5.7).
4. Bằng chứng tiền đăng ký, tái lập trên hai miền: thiệt hại của giao thức sửa chữa đến từ việc
   **tiếp xúc với nội dung sai**, không phải từ việc tiếp xúc (§5.8).
5. Giải nghịch lý "cùng biến, hai dấu": tuyển chọn thắng và sửa chữa thua đều do cùng cơ chế (§6).
6. Một bộ quy trình chống tự đánh lừa (tiền đăng ký, điều kiện hợp lệ, niêm phong hash, sàn nhiễu,
   t-test theo fold) mà 50% số lần chạy không vượt qua — bản thân con số đó là một kết quả (§7).

*(Chương này viết sau cùng theo đường găng; rà lại sau khi §6 chốt.)*

---

## §2. Công trình liên quan

> **TODO — ĐỨC.** Nguồn đã có: `../docs/RELATED_BASELINES.md` (102 dòng) và
> `../docs/RELATED_PIPELINE.md` (77 dòng). Khung chương:
>
> 1. **Debate và self-consistency:** số liệu công bố cho thấy debate kém self-consistency ở đa số
>    ô so sánh và sụp 16 điểm với Llama-3.1-8B trên GSM8K — trùng hướng với kết quả của nhóm,
>    nguồn độc lập. ⚠️ Kiểm lại phát biểu "3/4 ô": bảng gốc trong tài liệu có thể chỉ đỡ được 2/4.
> 2. **Pipeline vai nối tiếp:** định vị so với MAS_RPSV (bốn vai, cùng cỡ model, cùng benchmark)
>    và SHARP (cùng dùng Shapley; báo cáo chỉ 12,96% lượt gọi subagent hữu ích — song song với
>    §5.4 của ta).
> 3. **PHẦN CÒN THIẾU, quan trọng nhất:** dòng sinh-rồi-sửa — Self-Refine, Reflexion, CRITIC —
>    và với TỪNG công trình phải ghi rõ: model sửa và model bị sửa có cùng cỡ không, và bài báo
>    đo so với baseline nào (`V − S` hay `V − I`). Đây là chỗ luận điểm §1 đứng hoặc đổ
>    (câu hỏi B1 trong `CAU_HOI_THAO_LUAN.md` — trả lời xong mới chốt được §1).

---

## §3. Khung lý thuyết

### 3.1 Phân rã giá trị

```
value = H(pool) × κ(z) − D(protocol)
```

- **`H` — dư địa:** pool ứng viên có chứa lời giải mà model mạnh đơn lẻ không tạo ra được không?
  Đo bằng `oracle@k`.
- **`κ` — chất lượng bộ chọn:** một tín hiệu *khả thi* (không phải oracle) có lấy được lời giải đó
  ra khỏi pool không?
- **`D` — thiệt hại:** bản thân giao thức phá hỏng bao nhiêu?

Ba nhánh nghiên cứu của nhóm tương ứng ba thành phần: phân tích Shapley theo vai đo `H`; phân
tích router đo `κ`; phân tích luồng thông tin đo `D`. Ba nhánh không phải ba chủ đề rời — chúng
là ba thừa số của cùng một biểu thức.

### 3.2 Đẳng thức phân rã

Với `S` là model yếu giải bài, `I` là model mạnh giải bài *không nhìn thấy gì của `S`*, `V` là
**cùng model mạnh đó** nhưng ngữ cảnh có kèm bài làm của `S` (xem Phụ lục A về điểm dễ nhầm này),
và trần lý tưởng `CEIL` = đúng nếu `S` đúng **hoặc** `V` đúng (tức `oracle@2` trên cặp {S, V}):

```
Δ_ceil = acc(CEIL) − acc(I) = A − B + C

A = P(S đúng ∧ I sai)          cơ hội có sẵn — tính chất của CẶP MODEL
B = P(S sai ∧ I đúng ∧ V sai)  giao thức làm hỏng bài mà I vốn giải đúng — tính chất của GIAO THỨC
C = P(S sai ∧ I sai ∧ V đúng)  giao thức cứu được bài cả hai đều sai
```

Đây là đẳng thức đại số, không phải mô hình xấp xỉ: khớp tuyệt đối trên 4/4 cặp có lưu vết và
15/15 cặp của thí nghiệm quy mô lớn (§5.7). Giao thức **chỉ chọn** có `B ≈ 0` vì không thể tạo ra
lời giải sai mới; giao thức **sửa** luôn phải trả `B`. Đẳng thức này là công cụ giải nghịch lý §6.

Hai đại lượng đọc kèm: `Δ_ceil` là **chặn trên** (cần oracle, không triển khai được — giá trị của
nó là sàng lọc: `Δ_ceil < 0` thì đóng hướng ngay, không cổng nào cứu nổi); `Δ_honest = acc(V) −
acc(I)` mới là con số triển khai.

### 3.3 Ba mệnh đề

- **M1.** Thiệt hại `D` là hàm của việc tiếp xúc với **nội dung sai**, không phải của việc tiếp
  xúc. (Phát biểu hoàn chỉnh và bằng chứng tiền đăng ký ở §5.8.)
- **M2.** `κ` phụ thuộc vào việc tín hiệu chọn là **đúng đắn** hay **học được**, không phụ thuộc
  nó mạnh hay độc lập. (Phát biểu này đã qua hai lần thu hẹp từ bản gốc "độc lập thắng tương
  quan"; §5.10.)
- **M3.** Cơ chế định tuyến tiết kiệm ở đúng nơi ít cần tiết kiệm nhất. (§5.6.)

---

## §4. Thiết lập thí nghiệm

> **TODO — TÙNG DƯƠNG.** Khung chương: model (Qwen2.5 1.5B/7B/14B/32B, Llama-3.1-8B,
> DeepSeek-Coder-6.7B — ghi rõ lượng tử hoá đo được từng model: DeepSeek 3,61 GB nf4, Llama và
> Qwen-14B không lượng tử hoá được); benchmark (GSM8K, MATH-500, MBPP 11–510 và phần giữ lại
> 511–974 chỉ 464 bài, HumanEval); vai `P/S/V/A`; đại lượng (`Δ_ceil`, `Δ_honest`, `V_gain`,
> `A_gain`, chi phí theo lượt gọi VÀ theo token — nêu rõ verifier tốn ~5 lần aggregator); kiểm
> định (McNemar ghép cặp, bootstrap theo bài, t-test theo fold); giải mã greedy tất định — hệ quả:
> hai tài khoản, hai ngày, cùng phần cứng cho kết quả giống nhau trên 499/499 bài, nên chạy lại
> cùng cấu hình không phải bằng chứng độc lập. Nguồn: `../pipeline/*.py`, `THUAT_NGU.md` mục 8–9.

---

## §5. Kết quả

*Chương này viết theo mạch dẫn dắt: mỗi thí nghiệm mở bằng câu hỏi kế thừa từ thí nghiệm trước.
Bản đầy đủ của mạch (16 bước) ở `MACH_DAN_DAT.md`; các con số đều mức A trừ khi ghi khác.*

### 5.1 Điểm xuất phát: pipeline có giúp không — và sàn nhiễu

Pipeline đầy đủ so với solver đơn lẻ (Qwen-1.5B):

| Task | Solver | Pipeline đầy đủ | Chênh | Chi phí ký tự |
|---|---|---|---|---|
| GSM8K | 0,632 | 0,744 | **+0,112** | 2,9× |
| MATH | 0,405 | 0,345 | **−0,060** | **6,63×** |

Trên GSM8K có lợi; trên MATH tốn 6,63 lần ký tự để **kém hơn 6 điểm**. Phép đo 5 fold cho
`PSVA − PS` = +5,6 điểm (KTC 95% [+3,3; +7,9]; t = 6,89).

Một phép đo hiệu chuẩn định hình mọi kết luận sau đó: chạy *cùng một cấu hình* trên 5 fold rời
nhau cho `V_gain` dao động từ +1,0 đến +8,0 điểm. Toàn bộ dao động này đến từ việc **các fold là
những bộ bài khác nhau** (giải mã greedy tất định — không có nhiễu lấy mẫu khi sinh). Hệ quả: mọi
hiệu ứng được báo cáo kèm khoảng tin cậy tính từ độ lệch giữa fold; chuẩn chấp nhận trình bày ở §7.

**Câu hỏi để lại:** phần lợi trên GSM8K có phải do phối hợp không, hay chỉ do được sinh nhiều lượt?

### 5.2 Kiểm soát ngân sách: giá trị nằm ở lượt sinh, không ở vai tổng hợp

Cố định đúng 8 lượt sinh trên MATH, chỉ đổi cách tổng hợp:

| Cách tổng hợp | MATH 1.5B | MATH 7B |
|---|---|---|
| greedy (1 lượt) | 0,50 | 0,72 |
| `maj@8` — bỏ phiếu cơ học | **0,60** | **0,73** |
| `llm_agg@8` — LLM đọc cả 8 rồi tổng hợp | 0,41 | **0,47** |
| `oracle@8` — trần | 0,73 | 0,85 |

Cùng chi phí, thành phần LLM tổng hợp **kém bỏ phiếu 19–26 điểm**; ở 7B nó kém cả greedy một
lượt. Nó phá vỡ đa số đúng 21 và 26 lần, sửa được đa số sai 2 và 0 lần. Kết quả này **phụ thuộc
task**: đo trực tiếp `vote5 − llm_agg` cho +0,075 trên MATH nhưng −0,056 trên GSM8K — phát biểu
đúng là *thành phần tổng hợp LLM không mang lại giá trị ổn định; ở miền khó nó gây hại đáng kể*.

Hai đối chứng tách nốt phần còn lại:

- **Giải lại không cần phản hồi.** `loop` (giải lại sau khi đọc phê bình của verifier) = `rerun`
  (giải lại vô điều kiện, không thấy phê bình) = 0,453, bằng nhau chính xác. Lợi ích đến từ
  **lượt sinh thêm**, không từ nội dung phản hồi. (Con số +20 điểm của `loop` từng báo cáo ở một
  phép đo đơn lẻ không tái lập: 5 fold còn +4,0.)
- **Aggregator không chọn — nó chép.** Với 5 ứng viên, nó chép nguyên ứng viên *cuối cùng* ở 65%
  số câu; đọc 600 trace: 100% lượt không sinh số mới. **Nhưng phần "gây hại" phải đính chính:**
  85% số ca phá trên MATH là **không phát ra `\boxed{}`** — lỗi định dạng, chỉ 5% chọn nhầm thật.
  Thêm fallback miễn phí (không có `\boxed` → lấy đáp án verifier): `A_gain` từ −6,4 thành **+1,0**
  (KTC [0; +2]). Phát biểu đúng: *bộ tổng hợp LLM trung tính một khi đã xử lý định dạng đầu ra* —
  nó không cộng giá trị so với bỏ phiếu, nhưng "phá hoại" phần lớn là hiện vật đo lường.
  ⚠️ *Một mâu thuẫn chưa giải giữa hai lần chạy 5 fold của chính đại lượng này (−6,4 so với +8,0,
  mỗi bên đều nhất quán nội bộ) được ghi ở §8.*

**Câu hỏi để lại:** nếu mọi can thiệp chỉ cho 0–5 điểm, có phải đo sai mẫu số?

### 5.3 Kiểm soát mẫu số: 57% số câu không thể có hiệu ứng

Phân tầng theo độ khó *đối với chính model* (số mẫu đúng trong 5 lượt, MATH 1.5B, n = 150):

| Số mẫu đúng /5 | n | Solver | vote5 | Δ |
|---|---|---|---|---|
| 0/5 (quá sức) | 48 (32%) | 0,000 | 0,000 | 0,000 |
| 1/5 | 20 | 0,000 | 0,000 | 0,000 |
| 2/5 | 15 | 0,333 | 0,600 | +0,267 |
| 3/5 | 12 | 0,583 | 1,000 | +0,417 |
| 4/5 | 18 | 0,722 | 1,000 | +0,278 |
| 5/5 (quá dễ) | 37 (25%) | 1,000 | 1,000 | 0,000 |

32% số câu không mẫu nào đúng (không có gì để chọn), 25% mọi mẫu đều đúng (không có gì để cải
thiện hay phá) — **57% bất động vì lý do toán học**. Trên tầng có thể tác động, hiệu ứng là +21,5
điểm (nhóm 1–4/5, cách nhóm của tài liệu nguồn) hoặc +31,1 điểm (nhóm 2–4/5, loại tầng có hiệu
ứng bằng 0); trung bình toàn tập bị pha loãng còn +9,3. Một can thiệp trung bình +10 điểm sẽ hiện
ra thành +3 — chìm dưới nhiễu và bị kết luận nhầm là vô dụng.

Ba kiểm soát tác động **ngược chiều nhau**: thiếu kiểm soát mẫu số thì đánh giá *thấp*; thiếu
kiểm soát ngân sách và mốc so sánh thì đánh giá *cao*. Chúng phải đi cùng nhau.

**Câu hỏi để lại:** trong phần có thể tác động, vai nào thực sự đóng góp?

### 5.4 Vai trò: chuyên biệt hoá sụp đổ ở model yếu; biến quyết định là năng lực

Đọc chỉ số **hành vi** từ trace (không phải accuracy): ở 1.5B, planner — được yêu cầu *không*
tính đáp án — chứa sẵn đáp án ở 34,7% số câu MATH (45,3% có `\boxed`); solver không sinh số mới ở
60,7–62% số lượt, lời giải dài **19 ký tự** khi có plan so với 664 khi không có. *Nó không giải,
nó chép.* Ở 7B hai vai hồi phục đúng chức năng — nhưng ở mức đó pipeline lại thua solver đơn lẻ.
Đối chứng nhân quả mạnh nhất: **hoán vị prompt giữa các vị trí** (`normal`/`swap`/`solo`) cho
accuracy không phân biệt được (0,660 = 0,660; `solo` 0,673; chênh `swap − normal` trên MATH +5,3
không đạt ý nghĩa: t = 1,84, KTC [−2,7; +13,4]). Danh tính vai không phải biến.

Biến thật là **năng lực của model được đặt vào lượt kiểm**. Trên cùng 300 bài MATH (5 fold × 60):

| Verifier | Hiệu ứng | KTC 95% | Sửa : Phá |
|---|---|---|---|
| **V7B** (lớn hơn solver 1.5B) | **+14,0** | [+7,4; +20,6] | **43 : 1** |
| V1.5B (cùng cỡ) | +3,0* | khoảng chạm 0 | 15 : 6 |
| Riêng phần do lớn hơn (V7 − V15) | **+11,0** | [+3,9; +18,1] | — |

Cơ chế, đọc từ trace: khi can thiệp, verifier **tái sử dụng 0%** số liệu của solver — nó không
kiểm từng bước, nó **giải lại từ đầu**. *Verifier là một solver thứ hai đội lốt bộ kiểm; mua
verifier 7B tức là mua một solver tốt hơn cho lượt thứ hai.* Ở chiều ngược, phục hồi từ dữ liệu
fold cho thấy `V_gain` có ý nghĩa ở cả MATH 7B (+4,4; KTC [+1,5; +7,3]) — giá trị của verifier
xuất hiện *cùng với* năng lực.

**Câu hỏi để lại:** +14,0 là so với model yếu. So với model mạnh đơn lẻ thì sao?

### 5.5 Kiểm soát mốc so sánh: cấu hình bất đối xứng chỉ là phương án tiết kiệm

Đo token thật, 5 fold:

| Cấu hình | GSM8K | MATH | Token GSM8K | Token MATH |
|---|---|---|---|---|
| S1.5B + V7B | 0,810 | 0,563 | 105k | 119k |
| **S7B một mình** | **0,910** | **0,593** | 120k | 152k |
| S7B + V7B | 0,900 | **0,670** | 205k | 261k |

So với S7B đơn lẻ — vốn *rẻ hơn* cấu hình này tưởng chừng đắt: bất đối xứng **kém 10 điểm** trên
GSM8K; trên MATH kém 3 điểm với chênh theo fold chứa 0 (hoà thống kê), rẻ hơn 22% token. Phân
tích Pareto: solver đơn lẻ **nằm trên đường Pareto ở cả hai task**; pipeline đầy đủ **không** nằm
trên đường Pareto ở MATH (0,4133 so với 0,373 mà đắt gấp ba). Phát biểu đúng: *bất đối xứng năng
lực là một phương án tiết kiệm chi phí ở giữa dải độ khó, không phải một cải thiện độ chính xác.*
Riêng thêm V7B vào chính S7B trên MATH cho +7,7 điểm thật (KTC qua t-test p = 0,0075) — với giá
1,7 lần token.

Đây là dạng tổng quát của vấn đề mốc so sánh: `V − S` dương trong khi `V − I` âm, **cùng một hệ,
hai mốc, hai kết luận ngược nhau** — và nó lặp lại ở mọi nhánh của khảo sát.

**Câu hỏi để lại:** giá trị mất đi đâu? (Từ đây dùng công cụ §3.2.)

### 5.6 Chi phí và định tuyến: tiết kiệm được ở nơi ít cần nhất

Consensus router (chạy S và V; chỉ khi bất đồng mới gọi A):

| Chiến lược | GSM8K | Chi phí | MATH | Chi phí |
|---|---|---|---|---|
| Solver đơn lẻ | 0,6733 | 1 | 0,4133 | 1 |
| Pipeline đầy đủ | 0,7233 | 3 | 0,3733 | 3 |
| **Router** | **0,7200** | **2,32** | 0,4133 | 2,40 |

GSM8K: giữ 94% phần lợi với 77% chi phí. MATH: đúng bằng solver đơn lẻ — vô dụng. Cơ chế: khi
S–V bất đồng, aggregator cứu được 45,4% trường hợp trên GSM8K nhưng chỉ 25,0% trên MATH (mức B —
đo một lần). Đây là mệnh đề M3: định tuyến chỉ trả tiền ở nơi đã sẵn đồng thuận — nơi ít cần nó.

### 5.7 Số hạng `A`: chênh lệch năng lực, không phải họ model

Quan sát ban đầu trên 7 cặp gộp nhiều lần chạy: cặp *khác họ* có dư địa `A` gần gấp đôi cặp cùng
họ (0,0597 so với 0,0481). Nhưng các cặp khác họ trong mẫu đó cũng có chênh lệch năng lực nhỏ hơn
(0,130 so với 0,167) — hai biến trộn nhau hoàn toàn. Thiết kế tách: **6 model, 15 cặp có hướng,
cùng 499 bài MBPP, một lần chạy** (tiền đăng ký #106), bổ sung đúng các ô còn thiếu:

```
A = β₀ + β₁·(chênh lệch) + β₂·(khác họ)
β₁ = −0,1922  (p ≈ 0)          β₂ = +0,0045,  KTC 95% [−0,0051; +0,0140],  p = 0,31
R² chỉ với chênh lệch = 0,824
```

KTC của `β₂` nằm **trọn dưới** ngưỡng +0,02 đã khoá trước — một **null có thông tin**, không phải
thiếu lực. "Khác họ" là tương quan giả; biến thật là chênh lệch năng lực. (Kết quả đa dạng ứng
viên — pool 3 model cho 2,70/3 ứng viên phân biệt so với 1,91/3 khi lấy mẫu cùng model — được ghi
là "khác **model**", vì đối chứng khác-model-cùng-họ chưa chạy.)

Thí nghiệm mở rộng thêm nhánh sửa cho cả 15 cặp (tiền đăng ký #107) cho quy luật:

```
Δ_ceil = +0,0218 − 0,2392 × (chênh lệch)      R² = 0,60   p = 1e-05   điểm đổi dấu g* = 0,0913
```

Đẳng thức `A − B + C` khớp tuyệt đối 15/15. Nhưng phải đọc kèm: **0/15 cặp có `Δ_ceil` dương với
ý nghĩa**, 3/15 âm với ý nghĩa — nên chỉ phát biểu được **chiều phủ định**: *chênh lệch vượt ~0,09
thì đừng dùng giao thức sửa.* Chiều khẳng định cần lượng dữ liệu gấp ~8 lần toàn bộ MBPP — không
khả thi trên benchmark này. Phần phương sai của `B` chỉ được chênh lệch giải thích 35% (so với
82% của `A`) — `A` do cặp model định đoạt, `B` thì không hoàn toàn.

**Câu hỏi để lại:** `B` — thứ giao thức kiểm soát được — do đâu mà có?

### 5.8 Số hạng `B`: hình phạt của việc tiếp xúc với nội dung sai (kết quả trung tâm)

Thiết kế tách sạch nhất (tiền đăng ký #104, chạy trên MATH-500 để đổi miền so với quan sát thăm
dò gốc trên MBPP): hai nhánh dùng **cùng một lệnh giải**, khác duy nhất việc ngữ cảnh có kèm bài
làm của model yếu hay không, rồi phân tầng theo **nội dung** của bài làm đó:

| | MBPP 11–510 *(mức B)* | MBPP 511–974 *(mức B)* | **MATH-500 (mức A, tiền đăng ký)** |
|---|---|---|---|
| Artifact **sai** | −0,1900 | −0,1927 | **−0,2720** (p ≈ 0; n = 261) |
| Artifact **đúng** | +0,0636 | +0,0245 | **+0,0377** (p = 0,012; n = 239) |

Trên tầng artifact sai, model mạnh rơi từ **46,4% xuống 19,2%** — trên chính những bài nó vốn
giải được gần một nửa. Khi artifact đúng, nó *khá lên*. Tổng hợp hai tầng theo trọng số tái tạo
chính xác `V − I` = −0,1240. **`D` không phải hình phạt của việc nhìn thấy; nó là hình phạt của
việc nhìn thấy nội dung sai** — và vì không có lệnh sửa nào trong thiết kế này, *riêng việc nhìn
thấy đã đủ gây hại*. Đây cũng là lời giải cho câu hỏi bỏ ngỏ ở §5.6: aggregator vô dụng trên MATH
vì ở đó model yếu sai nhiều hơn, nên nó tiếp xúc với nhiều nội dung sai hơn (45,4% so với 25,0%
khớp hướng; mức B, chưa kiểm định lượng).

### 5.9 Tính chuyển miền của quy luật chênh lệch

Dùng đường hồi quy khớp **trên MBPP** để dự báo `Δ_ceil` **trên MATH** (tiền đăng ký #112, ba cặp
Qwen, mọi điều kiện hợp lệ đạt):

| Cặp | Chênh | Đo được | KTC 95% | MBPP dự báo | |
|---|---|---|---|---|---|
| 7B→14B | 0,044 | −0,0140 | [−0,046; +0,018] | +0,0108 | trong khoảng |
| 1.5B→7B | 0,244 | **−0,1660** | [−0,208; −0,124] | −0,0361 | **ngoài** |
| 1.5B→14B | 0,288 | −0,0680 | [−0,102; −0,034] | −0,0471 | trong khoảng |

2/3 dự báo nằm trong khoảng tin cậy ⇒ quy luật **không bị bác bỏ** trên miền toán (không viết
"đã xác nhận": các khoảng rộng 0,064–0,084 nên phép kiểm có độ phân giải thấp). Cặp lệch, lệch
**hệ thống**: `B` = 0,208 — gấp mười lần `A` — và tái lập một phép đo độc lập trước đó trên cùng
cặp (−0,1380 so với −0,1660). Quy luật mô tả xu hướng; ngoại lệ nằm ở nơi model yếu quá yếu so
với bài.

### 5.10 `κ`: tín hiệu đúng đắn đạt trần oracle; tín hiệu học được thì "đo được ≠ dùng được"

**Tín hiệu đúng đắn** (chạy test thật) — HumanEval, cùng model, cùng 4 lượt sinh, chỉ khác nguồn
tín hiệu kiểm; kết quả tái lập trên 4 cấu hình × 2 hệ phần cứng:

| Ô | greedy | **exec3** | llm3 | exec3 phá | llm3 phá |
|---|---|---|---|---|---|
| HE 1.5B (Kaggle) | 0,5375 | **0,6000** | 0,4812 | **0,0** | 2,8 |
| HE 1.5B (5090) | 0,5625 | **0,6438** | 0,4375 | **0,0** | 4,6 |
| HE 7B (5090) | 0,8000 | **0,8812** | 0,7812 | **0,0** | 2,6 |
| HE 7B (Kaggle) | 0,7938 | **0,9000** | 0,7438 | **0,0** | 3,2 |

`exec3` phá **0 bài trong 20/20 fold** và đạt đúng `oracle@4` ở hai ô có ghi số; `llm3` phá bài ở
cả 20 fold. Mốc trung thực là greedy (bỏ phiếu **có hại** trên code: −0,113/−0,131 vì lời giải
dài hiếm khi trùng): `exec3 − greedy` = +0,063 đến +0,106. Giới hạn: khi model nền bão hoà
(GSM8K 7B, solver 0,916), ngay cả bộ kiểm thực thi chính xác 0,837 vẫn **lỗ ròng** (26 phá / 6
sửa) — không còn gì để sửa mà vẫn còn thứ để phá.

**Tín hiệu học được** (bộ phân loại huấn luyện trên lỗi tiêm — đổi một chữ số trong lời giải
đúng; cả hai ô hợp lệ):

| Model | Lỗi tiêm | Lỗi thật | AUC | Đổi thành độ chính xác |
|---|---|---|---|---|
| 1.5B | −0,012 | +0,195 | 0,528 | −0,008 (1/5 fold) |
| **7B** | **+0,573** | **+0,693** | **0,893** | **+0,024 (2/5 fold)** |

Ở 7B nó học **rất tốt** và chuyển giao còn tốt hơn trong phân phối — nhưng AUC 0,893 chỉ mua được
+2,4 điểm, 2/5 fold. **Đo được ≠ dùng được.** Phát biểu hợp nhất (nối bốn thí nghiệm):

> **Giá trị của một bộ kiểm bằng khoảng cách `oracle@k − maj@k`, không bằng chất lượng bộ kiểm.**
> Code: khoảng cách +21,3 điểm — bộ test lấy toàn bộ. Toán: khoảng cách nhỏ — AUC 0,893 lấy được
> +2,4. **Nút thắt nằm ở khâu SINH, không phải khâu CHỌN** (ở 50–58% bài không đồng thuận, pool
> gần như không chứa ứng viên đúng nào).

Trần của cơ chế định tuyến theo mức tiếp xúc, tính trên dữ liệu §5.8: cổng **lý tưởng** (chỉ cho
xem khi artifact đúng) đạt 0,7160 so với `I` = 0,6980 — **chỉ +0,018** trên nền thiệt hại −0,124;
bộ phân loại thật cần ~89% độ chính xác mới hoà vốn. Kết luận không phải "làm cổng tốt hơn" mà là
**mặc định đừng cho xem**.

---

## §6. Tổng hợp: giải nghịch lý

**Nghịch lý.** §5.4: chênh lệch năng lực lớn cho +14,0 điểm. §5.7: chênh lệch năng lực lớn làm
`Δ_ceil` âm. Cùng một biến, hai dấu ngược nhau.

**Cách giải** — bằng đẳng thức §3.2. Hai kết quả dùng hai giao thức khác nhau:

```
Tuyển chọn (verifier 43:1):   value ≈ A × κ − 0        → chênh lệch tăng thì giá trị TĂNG
Sửa chữa   (V phải trả B):    value = A − B + C        → B tăng nhanh hơn A  → giá trị GIẢM
```

Chênh lệch năng lực làm tăng **cả** `A` **lẫn** `B`. Ai thắng do giao thức quyết định. Sáu mảnh
bằng chứng độc lập hội tụ:

1. **Đại số** — giao thức chỉ-chọn có `B ≈ 0` theo cấu trúc (verifier: 43 sửa / 1 phá).
2. **Độ lớn** — trên MATH ở chênh lệch lớn, `B` = 0,176–0,208, gấp ~11 lần `A`.
3. **Cơ chế** — `B` là thiệt hại do tiếp xúc nội dung sai, đo tiền đăng ký, hai miền (§5.8).
4. **Trần** — cổng lọc hoàn hảo cũng chỉ thu về +0,018 trên nền −0,124 (§5.10).
5. **Ngoại chứng** — số liệu công bố: debate thua self-consistency ở đa số ô, sụp 16 điểm ở model
   nhỏ *(chờ §2 chốt trích dẫn)*.
6. **Liên miền** — quy luật khớp trên MBPP dự báo được trên MATH ở 2/3 cặp (§5.9).

Bức tranh cuối là một **cây quyết định** chứ không phải một khẩu hiệu:

- Miền có **bộ kiểm đúng đắn** (code chạy test được): phối hợp đạt đúng trần oracle, 0 phá —
  dùng, và dùng dạng chỉ-chọn.
- Miền không có: bỏ phiếu cơ học lấy phần lớn giá trị của việc sinh nhiều lượt; thành phần LLM
  tổng hợp trung tính-đến-hại; tín hiệu học được "đo được nhưng không dùng được".
- Mọi miền: **đừng cho model mạnh xem bài làm của model yếu với mục đích sửa** — nhất là khi
  chênh lệch năng lực vượt ~0,09; muốn dùng model mạnh thì gọi thẳng nó.

> **Khuyến nghị một câu:** dùng model nhỏ để giải, model lớn để soát; sinh độc lập rồi chọn,
> đừng đưa cho nhau sửa.

---

## §7. Phương pháp luận

Nhóm dùng **hai chuẩn kiểm chứng bổ sung nhau** — nêu cả hai, không giấu chuẩn nào:

| Chuẩn | Áp dụng | Cơ chế chống tự đánh lừa |
|---|---|---|
| Thanh sai số theo fold | khối nhóm | 5 fold rời nhau; sàn nhiễu hiệu chuẩn (V_gain +1,0…+8,0); t-test trên fold, KTC 95%, phép thử dấu |
| Tiền đăng ký + điều kiện hợp lệ + niêm phong | khối luồng thông tin | bảng diễn giải khoá **trước** khi chạy, có dòng bác bỏ giả thuyết; hash artifact trước khi đọc; VOID thì không đọc số |

Các con số tự nói:

- **16 trên 32** lần chạy có tệp kết quả mang trạng thái VOID (50%) — điều kiện hợp lệ đang làm
  đúng việc; 18 lần có niêm phong hash (công cụ ra đời giữa dự án).
- Sổ dự đoán trước công khai: **21 đúng / 43** — kể cả người đặt ra giả thuyết cũng đoán sai một
  nửa, đó là lý do phải khoá diễn giải trước.
- Greedy tất định: hai tài khoản, hai ngày, cùng phần cứng → **giống nhau 499/499 bài**. Hệ quả
  phương pháp: chạy lại cùng cấu hình không phải bằng chứng độc lập; so sánh chéo lần chạy chỉ
  hợp lệ khi trùng cả (máy + độ chính xác số) lẫn bộ bài (đo được nf4 so với bf16 lệch tới 0,03).
- Chuẩn thống kê đã được **rà lại giữa kỳ** (đề xuất nhóm E, `CAU_HOI_THAO_LUAN.md`): ngưỡng
  "5 điểm" gốc suy cho phép đo đơn lẻ; với 5 fold, chuẩn đúng là t-test (ngưỡng hiệu dụng ~3,3
  điểm) kèm KTC. Rà lại 131 đại lượng: **bốn kết quả chủ lực đều đứng vững** (t = 3,3–6,9); 6 kết
  quả được phục hồi *sau khi đối chiếu cờ hợp lệ* (thống kê không cứu được lần chạy vô hiệu);
  1 kết quả mất ý nghĩa (k = 3 fold); 2 ca treo được phán dứt khoát bằng cách tải dữ liệu fold
  còn trên Kaggle — không cần chạy lại. 131 phép thử ⇒ kỳ vọng ~6,6 dương tính giả; mọi ca
  p ∈ [0,02; 0,05] cần đọc với dè dặt tương ứng.

Phần lớn "cải thiện" ghi nhận ban đầu không sống sót qua kiểm chứng. Đó là một kết quả, không
phải một thất bại.

---

## §8. Hạn chế

1. **`Δ_honest` chưa có kết luận.** Đại lượng triển khai được thật (giao thức khả thi có thắng
   model mạnh đơn lẻ không) đã qua năm lần chạy đều hỏng vì giới hạn 14,6 GB của GPU miễn phí.
   Phần lớn kết luận định lượng của khảo sát dựa trên **chặn trên** `Δ_ceil`, và mọi chặn trên
   của dòng sửa chữa đều âm hoặc không dương có ý nghĩa.
2. **Một mâu thuẫn chưa giải:** hai lần chạy 5 fold của `A_gain` trên MATH 1.5B cho dấu ngược
   nhau (−0,064 và +0,080, mỗi bên nhất quán nội bộ; khác cỡ fold 100/40 và có thể khác xử lý
   `\boxed`). Con số −6,4 chỉ được trích kèm chú thích này cho tới khi giải xong.
3. Hai khối dùng hai chuẩn kiểm chứng, chưa kiểm chéo lẫn nhau; đề xuất hợp nhất chuẩn (nhóm E)
   chưa được cả nhóm phê duyệt.
4. Tính chuyển miền của quy luật chênh lệch dựa trên 3 cặp với khoảng tin cậy rộng, có 1/3 lệch
   hệ thống; vùng dương của quy luật **không thể** xác lập trên MBPP (thiếu lực ~8 lần).
5. `κ` chưa giải được ở miền không có bộ kiểm đúng đắn: ba tín hiệu định tuyến đã thử (tự đánh
   giá độ khó, độ dài, đồng thuận có trọng số) đều thất bại hoặc trần quá thấp.
6. Chỉ greedy decoding ở khối luồng thông tin — mỗi cấu hình là một điểm, không có phương sai lấy
   mẫu; khối nhóm có fold bù lại một phần.
7. Tập model bị giới hạn bởi VRAM tầng miễn phí (Llama-8B và Qwen-14B không lượng tử hoá được);
   phạm vi khẳng định là **model nhỏ-đến-trung trên bài toán suy luận**, chưa nói được gì về
   model rất lớn *(quyết định phạm vi cuối: câu B4)*.
8. Kết quả `+14,0` và toàn bộ khối vai trò đo trên n = 300 với fold 60 câu — khoảng tin cậy rộng
   tương ứng; và §5.6 (router) là phép đo một lần, chưa có thanh sai số.

---

## §9. Kết luận

Câu hỏi "đa tác tử có giúp không" không có câu trả lời đơn — nhưng có một câu trả lời **có cấu
trúc**. Dưới ba phép kiểm soát (ngân sách, mốc so sánh, mẫu số), giá trị của phối hợp phân rã
thành ba thừa số đo được: dư địa `H` do chênh lệch năng lực quyết định; bộ chọn `κ` do tính đúng
đắn của tín hiệu quyết định; thiệt hại `D` do việc tiếp xúc nội dung sai quyết định. Cùng một
chênh lệch năng lực nuôi cả cơ hội lẫn thiệt hại — giao thức tuyển chọn gặt cơ hội, giao thức
sửa chữa gánh thiệt hại. Nơi có bộ kiểm đúng đắn, phối hợp chạm trần oracle mà không phá một bài
nào; nơi không có, cách khôn ngoan nhất là sinh độc lập, bỏ phiếu, và đừng để các model đọc bài
của nhau.

---

## Phụ lục

- **A. Thuật ngữ và ký hiệu** — rút từ `THUAT_NGU.md` *(TODO: chép mục 1–4 vào đây khi dựng bản in)*
- **B. Trích các bản tiền đăng ký** (#104, #106, #107, #112) — từ `../docs/PREREGISTRATION.md`
- **C. Bảng niêm phong hash** — `../docs/RESULT_SEALS.md`
- **D. 16 lần chạy VOID (trên 32) và lý do** — tổng hợp từ `res_*.json`
- **E. Sổ dự đoán trước (21/43)** — từ `../docs/PREREGISTRATION.md` mục #167
- **F. 37 quy tắc quy trình** — `../docs/QUY_TRINH_VONG_LAP.md`
- **G. Bảng kết quả đầy đủ khối nhóm** — `../docs/RESULTS.md`
- **H. Phân tích Shapley theo vai** — 29 tài liệu trong `../docs/`

## Hình *(TODO — theo bảng phân công trong `BAO_CAO_CAU_TRUC.md`)*

1. Sơ đồ khung `H × κ − D` + ánh xạ ba nhánh — Nguyên
2. **Nghịch lý hai đường ngược chiều** (quan trọng nhất) — Nguyên
3. `Δ_ceil` theo chênh lệch, 15 điểm + `g*` — Tùng Dương
4. Phân tầng tiếp xúc 2×2 — Tùng Dương
5. Accuracy–chi phí, có điểm router — Tùng Dương
6. Bất đối xứng verifier, có thanh sai số — Đức
7. Trần định tuyến theo độ chính xác bộ phân loại — Tùng Dương

---

*Việc còn chờ trước khi chốt: (a) §2 — Đức; (b) §4 — Tùng Dương; (c) Bước 0: cả nhóm duyệt câu
luận điểm + ba câu C3/B3/B4 + đề xuất chuẩn thống kê nhóm E; (d) giải mâu thuẫn D1 (§8.2);
(e) quyết định có gộp nhánh `nguoi3-router` (chứa `EFFICIENCY.md`) vào `main` không; (f) H100e
nếu muốn đóng `Δ_honest` — cần ~40 phút GPU với đường nạp lại đã có.*
