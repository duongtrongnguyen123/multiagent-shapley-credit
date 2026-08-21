# Prompt dựng slide báo cáo — Nhóm 13, INT3406

> Dán toàn bộ file này cho Claude Design. Kèm theo file `BAO_CAO_NHOM13.pdf` để nó đối chiếu
> số liệu, và bốn file hình trong `figs/`.

---

# PHẦN 0 — BỐI CẢNH VÀ YÊU CẦU

Bạn đang dựng bộ slide trình bày cho một báo cáo bài tập lớn môn Xử lý ngôn ngữ tự nhiên
(INT3406, UET-VNU). Báo cáo dài 22 trang, đính kèm ở dạng PDF. Buổi trình bày kéo dài
**20 phút**, sau đó là hỏi đáp.

Đây là báo cáo về một **khảo sát thực nghiệm**, không phải giới thiệu sản phẩm. Phần lớn kết
quả là **kết quả âm hoặc null** — nhóm đo và thấy các lợi ích được kỳ vọng của hệ đa tác tử
biến mất khi áp đủ điều kiện so sánh công bằng. Toàn bộ slide phải phản ánh đúng tinh thần đó:
trình bày bằng chứng, không quảng cáo.

**Đầu ra mong muốn:** một bộ slide 16:9, khoảng 20 slide chính + 6 slide dự phòng, dùng cho
trình chiếu trong giảng đường (người ngồi cuối phòng phải đọc được).

---

# PHẦN 1 — RÀNG BUỘC TUYỆT ĐỐI (đọc kỹ trước khi làm)

Bộ slide này **không được có mùi AI**. Dưới đây là các đặc điểm khiến slide bị nhận ra ngay là
do AI sinh. Tránh tuyệt đối:

### 1.1. Về tiêu đề slide

**Cấm** các tiêu đề nhãn chung chung: "Giới thiệu", "Tổng quan", "Phương pháp", "Kết quả",
"Những phát hiện chính", "Kết luận", "Cảm ơn", "Q&A".

**Thay bằng** tiêu đề là chính mệnh đề cần nói — người đọc chỉ nhìn tiêu đề đã nắm được luận
điểm. Đây là nguyên tắc *assertion–evidence*: tiêu đề là khẳng định, thân slide là bằng chứng.

| Đừng viết | Hãy viết |
|---|---|
| "Kết quả Shapley" | "Planner đóng góp âm ở model nhỏ, nhưng dương khi nâng năng lực" |
| "Thí nghiệm tiếp xúc" | "Nội dung artifact quyết định dấu của hiệu ứng, không phải việc nhìn thấy nó" |
| "Hạn chế" | "Bốn chỗ kết luận của chúng tôi có thể sai" |

### 1.2. Về ngôn ngữ

- **Cấm** các từ: "đáng kể", "vượt trội", "ấn tượng", "mạnh mẽ", "tối ưu", "đột phá",
  "cách mạng", "thay đổi cuộc chơi", "sức mạnh của", "khai phá", "tận dụng tối đa".
- **Cấm** câu hỏi tu từ làm tiêu đề ("Liệu đa tác tử có thực sự hiệu quả?").
- **Cấm** các cụm chuyển tiếp rỗng: "Hãy cùng tìm hiểu", "Điều thú vị là", "Đáng chú ý là",
  "Không thể phủ nhận rằng".
- **Cấm** slide cuối kiểu "Cảm ơn đã lắng nghe!" kèm hình minh hoạ.
- **Mọi khẳng định phải kèm số.** Không viết "hiệu quả giảm" mà viết "hiệu quả giảm từ 43%
  xuống 8%". Nếu một ý không có số đi kèm thì hoặc tìm số trong báo cáo, hoặc bỏ ý đó.
- Viết câu hoàn chỉnh khi cần, không ép mọi thứ thành gạch đầu dòng cụt.

### 1.3. Về bố cục

- **Cấm** quy tắc "ba gạch đầu dòng mỗi slide". Số lượng ý phải do nội dung quyết định: có
  slide chỉ một con số lớn, có slide là một bảng sáu dòng.
- **Cấm** dùng cùng một layout cho mọi slide. Bộ slide phải có ít nhất 5 kiểu bố cục khác nhau
  (xem Phần 3).
- **Cấm** icon trang trí cạnh mỗi gạch đầu dòng. **Cấm** emoji hoàn toàn.
- **Cấm** nền gradient, hiệu ứng đổ bóng, khung bo tròn lớn, hình nền trừu tượng.
- **Cấm** ảnh stock, hình vẽ robot, hình bộ não, hình mạng nơ-ron trang trí.
- Mỗi slide chỉ mang **một thông điệp**. Nếu slide có hai ý ngang hàng, tách thành hai slide.

### 1.4. Về màu

- Bảng màu tối đa **ba màu** cộng đen/trắng/xám. Màu chỉ dùng để **mã hoá dữ liệu**
  (dương/âm/trung tính), không dùng để trang trí.
- Không tô màu chữ tiêu đề. Không highlight nhiều hơn một cụm mỗi slide.

### 1.5. Kiểm tra cuối

Trước khi giao, tự soát: *nếu xoá hết tiêu đề slide và chỉ đọc phần thân, người xem có nắm
được mạch không?* Nếu không thì tiêu đề đang làm việc thay cho nội dung — viết lại nội dung.

---

# PHẦN 2 — VĂN PHONG PHẢI KHỚP BÁO CÁO

Báo cáo dùng một hệ thuật ngữ đã thống nhất. Slide **phải dùng đúng**, không tự dịch lại.

### 2.1. Từ vựng bắt buộc

| Dùng | Không dùng |
|---|---|
| model | mô hình *(trừ khi nói "mô hình hoá" theo nghĩa lý thuyết)* |
| trace | vết, dấu vết |
| task | tác vụ, nhiệm vụ |
| pool | tập ứng viên |
| tác tử | tác nhân, agent |
| vai trò | vai |
| lần sinh | lượt sinh |
| mức dao động nền | sàn nhiễu, mức nhiễu |
| tiềm năng cải thiện | dư địa |
| khả năng khai thác | bộ chọn khả thi |
| chốt trước | tiền đăng ký, đăng ký trước |
| thí nghiệm tác động artifact | thí nghiệm tiếp xúc, phơi nhiễm |
| ngữ cảnh | context |

### 2.2. Ký hiệu

- $W$ = model yếu · $I$ = model mạnh chạy độc lập · $E$ = model mạnh có tiếp xúc artifact
- $P$ / $S$ / $V$ / $A$ = planner / solver / verifier / aggregator
- $G$ = cơ hội cải thiện · $L$ = thiệt hại · $R$ = phần cứu được
- $\Delta_{\text{real}}$ = hiệu số triển khai được · $\Delta_{\text{ceil}}$ = trần lý thuyết
- $\varphi_i$ = giá trị Shapley của vai trò $i$ · $\kappa$ = khả năng khai thác

**Slide nào dùng ký hiệu thì phải định nghĩa ký hiệu đó ngay trên slide đó** hoặc ở slide liền
trước. Không được dùng ký hiệu chưa giới thiệu.

### 2.3. Định dạng số

- Dấu thập phân là **dấu phẩy**: `0,744` không phải `0.744`.
- Độ chính xác ở thang 0–1 (`0,632`), hiệu ứng ở đơn vị **điểm** (`+11,2 điểm`).
- Luôn ghi dấu cho hiệu ứng: `+11,2` / `−6,0` (dùng dấu trừ thật `−`, không phải gạch nối).
- Tỷ số chi phí kèm dấu nhân: `2,9×`.
- Khoảng tin cậy viết `[+7,4; +20,6]`.

### 2.4. Giọng

Trung tính, mô tả. Nhóm báo cáo cái đã đo, kể cả khi kết quả ngược kỳ vọng. Khi một kết quả
yếu hoặc dưới ngưỡng, **nói thẳng là dưới ngưỡng** thay vì lờ đi. Đây là điểm mạnh của báo
cáo, không phải điểm yếu — giữ nguyên tinh thần đó trên slide.

---

# PHẦN 3 — TEMPLATE

### 3.1. Khổ và lưới

- Tỷ lệ **16:9**, kích thước gốc 1920×1080.
- Lề an toàn: trái/phải 96 px, trên 72 px, dưới 88 px.
- Lưới 12 cột, máng 24 px. Các bố cục hai cột dùng 7+5 hoặc 6+6.

### 3.2. Chữ

Dùng một bộ chữ không chân cho tiêu đề và một bộ có chân cho số liệu lớn, hoặc dùng chung một
bộ không chân nếu cần đơn giản. **Bắt buộc hỗ trợ đầy đủ dấu tiếng Việt** — thử ngay các chữ
`ượ ầ ế ộ ữ ỹ ằ` trước khi chốt bộ chữ.

| Thành phần | Cỡ | Đậm nhạt |
|---|---|---|
| Tiêu đề slide | 40–44 px | 600 |
| Tiêu đề phụ / dòng dẫn | 26 px | 400, màu xám đậm |
| Thân | 24–28 px | 400 |
| Số liệu nổi bật | 96–140 px | 600 |
| Chú thích bảng/hình | 18–20 px | 400, màu xám |
| Nhãn nguồn (góc dưới) | 16 px | 400, xám nhạt |

Chiều cao dòng thân 1,45. Không viết hoa toàn bộ. Không chữ nghiêng quá một cụm mỗi slide.

### 3.3. Màu

| Vai trò | Mã | Dùng cho |
|---|---|---|
| Nền | `#FFFFFF` | toàn bộ |
| Chữ chính | `#1A1A1A` | tiêu đề, thân |
| Chữ phụ | `#6B6B6B` | chú thích, nhãn trục |
| Nhấn / dương | `#1F6FB2` (xanh) | giá trị dương, đường chính |
| Cảnh báo / âm | `#B5442E` (đỏ gạch) | giá trị âm, thiệt hại |
| Trung tính | `#C9C9C9` | lưới, đường phụ, cột nền |

Chỉ hai slide trong cả bộ được dùng nền tối (slide 1 và slide 20), để tạo điểm ngắt.

### 3.4. Năm kiểu bố cục

Đánh số để phần 4 gọi lại:

- **L1 — Toàn màn hình một câu.** Chỉ một mệnh đề cỡ 60–72 px, căn trái, chiếm 8 cột. Dùng cho
  các slide bản lề.
- **L2 — Số lớn + diễn giải.** Một con số cỡ 120 px bên trái (4 cột), 2–3 câu giải thích bên
  phải (7 cột). Dùng khi cả slide xoay quanh một phép đo.
- **L3 — Hình chiếm ưu thế.** Hình/biểu đồ chiếm 8 cột trái, chú giải và 2–3 ý bên phải 4 cột.
- **L4 — Bảng.** Bảng chiếm 10 cột giữa, một dòng kết luận in đậm ngay dưới bảng.
- **L5 — Hai cột đối chiếu.** 6+6, dùng khi so hai điều kiện (trước/sau, mốc yếu/mốc mạnh).

### 3.5. Quy ước biểu đồ

- Không viền khung. Chỉ giữ trục cần thiết. Không lưới dọc.
- Ghi giá trị trực tiếp lên đầu cột/điểm, bỏ trục tung nếu đã ghi số.
- Không dùng biểu đồ tròn. Không 3D. Không đổ bóng.
- Đường tham chiếu (mốc 0, ngưỡng hiệu dụng 3,3 điểm) vẽ nét đứt màu xám, có nhãn.
- Mỗi biểu đồ có **một câu chú thích** dưới đáy nói biểu đồ chứng minh điều gì.

### 3.6. Chân slide

Góc dưới trái: `Nhóm 13 · INT3406`. Góc dưới phải: số slide. Cỡ 16 px, màu xám nhạt.
Slide 1 và slide bản lề không có chân slide.

---

# PHẦN 4 — ĐẶC TẢ TỪNG SLIDE

Với mỗi slide dưới đây: **Tiêu đề** là chữ phải hiện đúng nguyên văn. **Thông điệp** là điều
người xem phải nhớ. **Nội dung** là chữ và số phải có. **Hình** là thứ cần vẽ. **Ghi chú** là
lời người nói, đặt vào phần speaker notes.

---

## Slide 1 — Bìa

**Bố cục:** L1, nền tối `#1A1A1A`, chữ trắng.

**Nội dung:**
- Dòng nhỏ trên cùng: `Xử lý ngôn ngữ tự nhiên · INT3406`
- Tiêu đề chính (48 px): tên đề tài lấy đúng từ trang bìa báo cáo
- Dòng dưới: `Nhóm 13`
- Bốn tên xếp hai hàng hai cột: Dương Trọng Nguyên · Trương Đình Đức · Trần Tùng Dương ·
  Lê Hoàng Quân
- Logo UET góc dưới phải, chiều cao 72 px, phiên bản đơn sắc trắng

**Không có:** hình nền, hiệu ứng, ngày tháng.

---

## Slide 2 — Bài toán, kể bằng một ví dụ

**Tiêu đề:** `Model 7B tự giải đúng bài này. Sau khi đọc lời giải của model 1,5B, nó giải sai.`

**Thông điệp:** Vấn đề là có thật và cụ thể, không trừu tượng.

**Bố cục:** L5.

**Nội dung:** Cột trái — một bài toán MATH ngắn (lấy ví dụ có thật trong báo cáo hoặc dựng lại
tương đương), lời giải độc lập của model mạnh, đáp án đúng. Cột phải — cùng bài đó, kèm lời
giải sai của model yếu đưa vào ngữ cảnh, và đáp án sai mà model mạnh đưa ra. Dùng màu xanh cho
nhánh đúng, đỏ gạch cho nhánh sai. Bên dưới, một dòng: `Đây không phải ngoại lệ — trên tầng
artifact sai, hiệu ứng là −27,2 điểm.`

**Ghi chú:** Mở đầu bằng hiện tượng, chưa nói tên gọi hay ký hiệu gì.

---

## Slide 3 — Kỳ vọng đặt vào hệ đa tác tử

**Tiêu đề:** `Chia việc cho nhiều vai trò được kỳ vọng tốt hơn một model đơn lẻ`

**Thông điệp:** Nêu giả định mà cả lĩnh vực đang dùng, để các slide sau kiểm nó.

**Bố cục:** L3.

**Hình A — sơ đồ pipeline bốn vai.** Bốn khối xếp ngang: Planner → Solver → Verifier →
Aggregator, mũi tên nối, đầu vào là đề bài, đầu ra là đáp án. Mỗi khối ghi một dòng chức năng
được giao: lập kế hoạch / giải / kiểm tra và sửa / chọn đáp án cuối. Vẽ đơn sắc, không tô màu.

**Nội dung bên phải:** ba dòng ngắn nêu lý do kỳ vọng — chia nhỏ độ khó, có bước kiểm độc lập,
tổng hợp nhiều ứng viên.

---

## Slide 4 — Câu hỏi của báo cáo

**Tiêu đề:** `Lợi ích đo được đến từ cơ chế phối hợp, hay từ việc gọi model nhiều lần hơn?`

**Thông điệp:** Đây là câu hỏi trung tâm.

**Bố cục:** L1.

**Nội dung:** Chỉ mệnh đề trên, cộng một dòng nhỏ phía dưới: `Để trả lời, phải kiểm soát ba
thứ thường bị bỏ qua.` Dòng này dẫn thẳng sang slide 5.

---

## Slide 5 — Ba phép kiểm soát

**Tiêu đề:** `Ba sai lệch trong cách đo, và chúng không cùng chiều nhau`

**Thông điệp:** Thiếu kiểm soát thì kết luận sai — theo cả hai hướng.

**Bố cục:** L4 (bảng ba dòng).

| Kiểm soát | Nếu thiếu | Hệ quả |
|---|---|---|
| Chi phí tính toán | So hệ nhiều lượt gọi với model chạy một lượt | Đánh giá **cao** |
| Mốc so sánh | Chỉ so với model yếu bị sửa, không so với model mạnh đơn lẻ | Đánh giá **cao** |
| Mẫu số | Tính trung bình trên cả những bài không cơ chế nào đổi được | Đánh giá **thấp** |

**Dòng kết luận dưới bảng:** `Vì hai chiều ngược nhau, ba phép kiểm soát phải áp đồng thời —
không cái nào thay được cái nào.`

---

## Slide 6 — Thiết lập

**Tiêu đề:** `Bốn benchmark, model từ 0,5B đến 32B, mọi phép đo chia năm fold`

**Thông điệp:** Nền tảng thực nghiệm đủ rộng để tin được.

**Bố cục:** L5.

**Cột trái — cái đã chạy:** benchmark GSM8K, MATH, MBPP, HumanEval; dải model 0,5B–32B; giải
mã tất định (`sample = false`), nên chênh lệch giữa các fold hoàn toàn do khác bài chứ không do
ngẫu nhiên lấy mẫu.

**Cột phải — cách đọc số:** mọi hiệu ứng chia 5 fold; ngưỡng hiệu dụng ≈ 3,3 điểm; hiệu ứng
dưới ngưỡng được ghi là dưới ngưỡng chứ không được coi là có thật; thiết kế và tiêu chí đánh
giá được **chốt trước** khi chạy.

---

## Slide 7 — Mức dao động nền

**Tiêu đề:** `Chạy cùng một cấu hình trên năm fold cho kết quả lệch nhau tới 7 điểm`

**Thông điệp:** Không có mốc nhiễu thì không đọc được kết quả nào.

**Bố cục:** L2.

**Số lớn:** `2,65 điểm` — kèm nhãn nhỏ `độ lệch chuẩn giữa các fold`.

**Diễn giải bên phải:** cùng cấu hình, chỉ khác bài, `V_gain` dao động từ +1,0 đến +8,0 điểm.
Suy ra ngưỡng hiệu dụng ≈ 3,3 điểm. Một phép đo đơn lẻ trên 100 bài gần như không mang thông
tin; mọi con số trong các slide sau đều là trung bình năm fold.

**Hình B — dot plot:** năm chấm trên một trục ngang từ 0 đến +10 điểm, tại các giá trị đo được;
đường nét đứt xám tại 3,3 ghi `ngưỡng hiệu dụng`.

---

## Slide 8 — Pipeline có lợi trên một task, có hại trên task kia

**Tiêu đề:** `Pipeline bốn vai hơn 11,2 điểm trên GSM8K nhưng kém 6,0 điểm trên MATH`

**Thông điệp:** Lợi ích không phổ quát, và chi phí thì luôn có.

**Bố cục:** L4.

| Task | Một lần sinh | Pipeline bốn vai | Chênh lệch | Token sinh |
|---|---|---|---|---|
| GSM8K | 0,632 | **0,744** | +11,2 | 2,9× |
| MATH | **0,405** | 0,345 | −6,0 | 6,63× |

Tô xanh ô 0,744, tô đỏ gạch ô 0,345. Cột token in xám để nhấn rằng chi phí luôn tăng bất kể
kết quả.

**Dòng kết luận:** `Cùng một kiến trúc, hai task, hai dấu ngược nhau — và cả hai đều tốn thêm
gấp 3 đến 6 lần token.`

---

## Slide 9 — Giá trị nằm ở đâu

**Tiêu đề:** `Bỏ phản hồi của verifier đi, kết quả không đổi: 0,453 so với 0,453`

**Thông điệp:** Lợi ích đến từ việc sinh thêm lần, không từ nội dung phối hợp.

**Bố cục:** L5.

**Cột trái — đối chứng:** cho model giải lại **có** đọc phê bình của verifier → 0,453. Cho giải
lại **không** đọc gì → 0,453. Hai số bằng nhau.

**Cột phải — hệ quả:** với cùng ngân sách 8 lần sinh, để model tự tổng hợp kém bỏ phiếu đa số
19–26 điểm. Biến thể vòng lặp giải-rồi-chấm, rẻ hơn pipeline đủ vai, còn hơn nó 4,0 điểm trên
MATH.

**Dòng dưới cùng:** `Cái tạo ra giá trị là nhiều lần sinh độc lập. Cơ chế phối hợp không thêm
gì, và bộ tổng hợp bằng model còn làm hỏng.`

---

## Slide 10 — Phân rã theo vai trò

**Tiêu đề:** `Planner đóng góp âm ở model 1,5B, và dương khi nâng lên 7B`

**Thông điệp:** Đóng góp của một vai là hàm của năng lực, không phải thuộc tính cố định.

**Bố cục:** L3.

**Hình C — biểu đồ cột ngang.** Bốn vai trò, giá trị $\varphi$ trên GSM8K. Cột dương màu xanh,
cột âm màu đỏ gạch, đường 0 rõ. Ghi giá trị lên đầu mỗi cột. Planner là cột âm duy nhất.

**Bên phải:** giải thích cách đo — chạy đủ $2^4 = 16$ tổ hợp bật/tắt bốn vai, $\varphi_i$ là
mức thay đổi trung bình khi thêm vai $i$ vào mọi tổ hợp con. Ví dụ cụ thể: thêm planner vào tổ
hợp $SA$ làm giảm 12 điểm (0,682 → 0,562). Khi nâng riêng planner lên 7B, $\varphi_P$ đảo dấu.

**Cảnh báo cho người dựng:** giá trị của Verifier trong báo cáo là giá trị **áp đặt bằng đối
xứng**, không phải giá trị đo. Đừng đưa nó lên biểu đồ như một phép đo. Nếu cần, vẽ cột đó
bằng nét đứt và ghi chú `suy ra bằng đối xứng`.

---

## Slide 11 — Vai trò được gán khác vai trò thực thi

**Tiêu đề:** `Trên MATH, planner giải sẵn đáp án trong 34,7% số câu thay vì lập kế hoạch`

**Thông điệp:** Shapley gán công cho *nhãn* vai trò, còn *hành vi* thì đã lệch khỏi chức năng.

**Bố cục:** L4.

Bảng ba dòng, mỗi dòng một vai và một hành vi lệch đo được từ trace. **Mọi số ở cột phải đều
là model 1,5B** — ghi rõ điều này ở chú thích dưới bảng.

| Vai trò | Hành vi được giao | Hành vi đo được (1,5B) |
|---|---|---|
| Planner | Lập dàn ý, bị cấm tính đáp án | Vẫn chứa đáp án đúng: 34,7% trên MATH, 14,0% trên GSM8K |
| Solver | Sinh lời giải | Không sinh số mới: 62,0% trên MATH, 60,7% trên GSM8K |
| Aggregator | Chọn giữa các ứng viên | 3 trên 2.000 lượt cho ra đáp án mới và đúng |

**Dòng kết luận:** `Ba vai đang làm các phiên bản của cùng một việc. Chỉ số tương tác Shapley
xác nhận: solver, verifier và aggregator thay thế nhau chứ không bổ sung nhau.`

**Lưu ý bắt buộc:** ở model 7B các hiện tượng này gần như biến mất (planner rò 4,0% trên MATH,
1,0% trên GSM8K). Phải nói câu này trên slide, vì nếu bỏ đi thì slide thành lời buộc tội chung
cho mọi model, trong khi báo cáo chỉ kết luận cho model nhỏ.

---

## Slide 12 — Verifier

**Tiêu đề:** `Verifier cùng cỡ với solver gần như không phát hiện được lỗi`

**Thông điệp:** Bước kiểm chỉ có giá trị khi người kiểm mạnh hơn người bị kiểm.

**Bố cục:** L5.

**Cột trái:** verifier 1,5B kiểm solver 1,5B — độ chính xác can thiệp 56–59%, tức gần mức đoán
mò; mù hoàn toàn với lỗi chữ số được tiêm vào.

**Cột phải:** verifier 7B kiểm solver 1,5B — độ chính xác can thiệp 98%, tỷ lệ sửa trên phá là
43:1, hiệu ứng +14,0 điểm với khoảng tin cậy [+7,4; +20,6].

**Dòng dưới:** `Phần chênh do cỡ model lớn hơn là +11,0 điểm. Nói cách khác, gần như toàn bộ
giá trị của bước kiểm đến từ việc dùng model mạnh hơn, không từ việc có thêm một vai.`

---

## Slide 13 — Mốc so sánh

**Tiêu đề:** `Đổi mốc so sánh làm đảo dấu kết luận`

**Thông điệp:** Đây là đóng góp phương pháp luận trung tâm của báo cáo.

**Bố cục:** L3.

**Hình D — biểu đồ hai đường.** Trục hoành là khoảng cách năng lực giữa hai model (từ 0 tăng
dần). Đường xanh: hiệu ứng đo **so với model yếu** — tăng dần theo khoảng cách. Đường đỏ gạch:
hiệu ứng đo **so với model mạnh chạy độc lập** — giảm dần và xuống dưới 0. Hai đường cắt nhau.
Đánh dấu điểm tại khoảng cách bằng 0, ghi `+7,7 điểm — trường hợp duy nhất hệ đa tác tử hơn
model mạnh đơn lẻ`.

**Bên phải:** cùng một thí nghiệm, hai mốc, hai kết luận ngược nhau. Nhóm nào chỉ báo cáo mốc
yếu sẽ kết luận "càng chênh càng tốt"; đo trên mốc mạnh thì thấy điều ngược lại.

---

## Slide 14 — Mẫu số

**Tiêu đề:** `57% số bài nằm ngoài tầm can thiệp của mọi cơ chế chọn ứng viên`

**Thông điệp:** Trung bình trên toàn tập làm loãng tín hiệu tới ba lần.

**Bố cục:** L3.

**Hình E — cột chồng ngang một dải.** Một thanh ngang chia ba đoạn theo tỷ lệ: `32% quá khó —
mọi ứng viên đều sai` (xám), `25% quá dễ — mọi ứng viên đều đúng` (xám), `43% còn lại — vùng
có thể tác động` (xanh). Ghi phần trăm trực tiếp trên từng đoạn.

**Bên phải:** trên 43% còn lại, hiệu ứng thật là +26,7 đến +41,7 điểm tuỳ tầng. Tính trung bình
trên cả tập, con số đó bị pha loãng 2,3 đến 3,3 lần — đủ để một can thiệp có giá trị bị kết
luận nhầm là vô dụng.

---

## Slide 15 — Thí nghiệm trung tâm

**Tiêu đề:** `Cùng một lệnh giải, chỉ khác nội dung artifact đưa vào — dấu hiệu ứng đảo ngược`

**Thông điệp:** Đây là thí nghiệm chính; thiết kế chặt và kết quả mạnh nhất báo cáo.

**Bố cục:** L3, dùng lại **Hình 1 của báo cáo** (`figs/` — sơ đồ hai nhánh) nếu chất lượng đủ,
hoặc vẽ lại theo đúng cấu trúc đó.

**Cấu trúc hình:** một đề bài → hai nhánh. Nhánh $I$: model mạnh giải độc lập. Nhánh $E$: model
mạnh giải với artifact của model yếu trong ngữ cảnh. Cùng lệnh, cùng ngân sách, chỉ khác chỗ đó.

**Bảng nhỏ dưới hình:**

| Tầng | Hiệu ứng $\text{acc}(E) - \text{acc}(I)$ |
|---|---|
| Artifact đúng | +3,8 điểm |
| Artifact sai | **−27,2 điểm** |

**Dòng kết luận:** `Không phải việc nhìn thấy lời giải gây hại, mà là nội dung của lời giải đó.`

---

## Slide 16 — Cơ chế

**Tiêu đề:** `Giao thức sinh-rồi-sửa hoạt động như ống dẫn, không phải bộ sửa lỗi`

**Thông điệp:** Giải thích *tại sao* kết quả slide 15 xảy ra.

**Bố cục:** L4, bảng $2\times2$.

Phân tầng 500 bài MATH theo trạng thái của $W$ và $I$:

| | $I$ đúng | $I$ sai |
|---|---|---|
| **$W$ đúng** | không đổi | truyền lại đáp án đúng của $W$: 10/11 bài |
| **$W$ sai** | **phá hỏng: 77/121 bài (63,6%)** | tạo lời giải mới: 6/140 bài (4,3%) |

**Dòng kết luận:** `Khi cả hai cùng sai, hệ gần như không tạo được gì mới. Khi model mạnh đúng
mà model yếu sai, hệ phá hỏng gần hai phần ba. Đó là hành vi của một kênh truyền, không phải
của một cơ chế sửa lỗi.`

---

## Slide 17 — Tín hiệu kiểm chứng

**Tiêu đề:** `Chạy test không phá bài nào trong cả 20 fold; để model tự chấm thì phá ở cả 20`

**Thông điệp:** Tín hiệu khách quan và tín hiệu do model tự sinh khác nhau về bản chất.

**Bố cục:** L5.

**Cột trái — tín hiệu chắc chắn (chạy test trên code):** 0 bài bị phá trong 20/20 fold; lấy gần
trọn trần lý thuyết `oracle@k − maj@k`.

**Cột phải — tín hiệu học được:** bộ phân loại lỗi đạt AUC 0,893 — chất lượng phát hiện cao —
nhưng khi đem đi chọn ứng viên chỉ đổi được +2,4 điểm, và chỉ 2 trên 5 fold dương.

**Dòng dưới:** `Chất lượng phát hiện lỗi cao không tự động đổi thành điểm số. Trần bị chặn bởi
pool: nếu không ứng viên nào đúng thì không bộ chọn nào cứu được.`

---

## Slide 18 — Huấn luyện

**Tiêu đề:** `Bảy phương pháp huấn luyện, bảy lối tắt khác nhau, không cái nào cải thiện thật`

**Thông điệp:** Không thể huấn luyện để vá vấn đề, vì hàm mục tiêu luôn bị lách.

**Bố cục:** L4.

Bảng bốn dòng chọn lọc (không liệt kê cả bảy, sẽ quá dày — bảy cái đầy đủ để ở slide dự phòng):

| Phương pháp | Đạt được | Lối tắt tìm ra |
|---|---|---|
| GRPO thưởng theo can thiệp | Precision lên 1,00 ở cả 5 fold | Im lặng — số lần can thiệp rơi từ 20,2 xuống 8,4 |
| GRPO thưởng theo đáp án cuối | +1,8 điểm, dưới ngưỡng | Nhại solver — độ dài đầu ra rút từ 480 xuống 19 ký tự |
| Credit-RL theo đóng góp Shapley | 0 trên 4 vai cải thiện | Planner sập về kế hoạch rỗng ở 200/200 bài |
| Đồng huấn luyện ba vai | 0,690 → 0,690 | Aggregator nghẽn suốt quá trình |

**Dòng kết luận:** `Mỗi lần bịt một lối tắt, phương pháp tìm ra lối khác. Vấn đề không nằm ở
thuật toán huấn luyện mà ở chỗ hàm mục tiêu không buộc được vai trò làm đúng chức năng.`

**Hình F (tuỳ chọn, nếu còn chỗ):** dùng lại hình ví dụ GRPO trong báo cáo — solver giải đúng,
verifier "sửa" thành sai.

---

## Slide 19 — Khi nào nên dùng đa tác tử

**Tiêu đề:** `Ba điều kiện, và nếu thiếu một thì model mạnh đơn lẻ là lựa chọn tốt hơn`

**Thông điệp:** Kết luận có tính hành động, không phải phủ định toàn bộ.

**Bố cục:** L3, hình là cây quyết định.

**Hình G — cây quyết định** ba nút, mỗi nút một câu hỏi, nhánh "không" đều dẫn về cùng một ô
kết luận `dùng model mạnh đơn lẻ`:

1. Có tín hiệu kiểm chứng khách quan không (chạy được test, đối chiếu được)?
2. Model nền còn tiềm năng cải thiện, hay đã bão hoà trên task này?
3. Người kiểm có mạnh hơn người bị kiểm không?

Nhánh "có" cả ba dẫn tới ô `phối hợp đa tác tử có khả năng mang lại lợi ích`.

**Bên phải:** một dòng nhấn — `Và ngay cả khi đủ ba điều kiện, đừng đưa lời giải chưa được kiểm
của model yếu vào ngữ cảnh của model mạnh.`

---

## Slide 20 — Chốt

**Tiêu đề:** `Phối hợp đa tác tử không mặc định tạo ra lợi ích`

**Bố cục:** L1, nền tối, giống slide 1 để đóng khung bộ slide.

**Nội dung:** mệnh đề trên, cỡ lớn. Dưới đó ba dòng ngắn, mỗi dòng một câu, không gạch đầu dòng:

- Lợi ích đo được phần lớn đến từ việc sinh nhiều lần, không từ cơ chế phối hợp.
- Đổi mốc so sánh làm đảo dấu kết luận, nên phải báo cáo cả hai mốc.
- Lời giải sai của model yếu gây hại nhiều hơn lời giải đúng mang lợi.

Dòng cuối cùng, cỡ nhỏ, màu xám: địa chỉ repo mã nguồn và dữ liệu.

**Không có** slide "Cảm ơn" hay "Q&A" sau slide này.

---

## SLIDE DỰ PHÒNG (đặt sau slide 20, không trình bày trừ khi được hỏi)

- **D1 — Bảy phương pháp huấn luyện, bảng đầy đủ.** Cả bảy dòng với lối tắt tương ứng.
- **D2 — Bảng giá trị Shapley đầy đủ**, cả hai task, kèm khoảng tin cậy, kèm ghi chú rõ giá trị
  nào là đo và giá trị nào là suy ra bằng đối xứng.
- **D3 — Quy đổi chi phí về FLOP.** Cho thấy con số "rẻ hơn 12%" biến mất khi quy đổi.
- **D4 — Kiểm chuyển miền.** Ba cặp model, dự báo so với đo được, 2 trên 3 nằm trong khoảng.
- **D5 — Phân tầng năm lần sinh đầy đủ.** Sáu tầng từ 0/5 đến 5/5 với $n$ và $\Delta$ từng tầng.
- **D6 — Bốn hạn chế của khảo sát.** Nêu thẳng: phạm vi model 0,5–32B nên chưa suy rộng được
  cho model rất lớn; một nhánh của $\Delta_{\text{real}}$ chưa chạy xong; giải mã tất định nên
  mỗi cấu hình chỉ có một ước lượng; một số đối chứng còn thiếu.

---

# PHẦN 5 — HÌNH CẦN VẼ, TỔNG HỢP

| Mã | Slide | Loại | Ghi chú |
|---|---|---|---|
| A | 3 | Sơ đồ khối | Bốn vai nối tiếp, đơn sắc |
| B | 7 | Dot plot | Năm điểm + đường ngưỡng nét đứt |
| C | 10 | Cột ngang | Bốn vai, có cột âm, đường 0 rõ |
| D | 13 | Hai đường | Hai mốc, cắt nhau, đánh dấu điểm giao |
| E | 14 | Thanh chia đoạn | Ba đoạn 32/25/43 |
| F | 18 | Ảnh chụp ví dụ | Dùng lại từ báo cáo |
| G | 19 | Cây quyết định | Ba nút, hai kết cục |

Hình 1 của báo cáo (sơ đồ hai nhánh $I$/$E$) dùng lại cho slide 15.

Tất cả hình vẽ bằng vector trong chính slide, không nhúng ảnh bitmap trừ F và Hình 1.

---

# PHẦN 6 — SỐ LIỆU ĐANG ĐƯỢC RÀ LẠI, ĐỪNG ĐƯA LÊN SLIDE

Bốn con số dưới đây trong báo cáo đang được nhóm đối chiếu lại. **Không đưa lên slide** cho
đến khi có xác nhận:

1. Tỷ số giữa thiệt hại $L$ và cơ hội $G$ (báo cáo ghi khoảng 11 lần).
2. Tỷ lệ bài mà bỏ phiếu đa số sai và pool không chứa ứng viên đúng.
3. Giá trị $\varphi$ của verifier — là giá trị suy ra bằng đối xứng, không phải đo.
4. Khoảng cách trần trên miền code (báo cáo ghi +21,3 điểm) — chưa dẫn được từ bảng nào.

Nếu một slide cần một trong bốn số này, hãy để trống chỗ đó và ghi chú lại để nhóm điền sau.

---

# PHẦN 7 — SOÁT TRƯỚC KHI GIAO

- [ ] Không slide nào có tiêu đề dạng nhãn ("Kết quả", "Phương pháp"...).
- [ ] Mọi khẳng định đều có số kèm theo.
- [ ] Không emoji, không icon trang trí, không ảnh stock, không gradient.
- [ ] Dấu thập phân là dấu phẩy ở mọi con số.
- [ ] Dấu âm là `−`, không phải `-`.
- [ ] Thuật ngữ khớp bảng ở Phần 2.1, đã soát từng slide.
- [ ] Mọi ký hiệu đều được định nghĩa trước hoặc ngay tại chỗ dùng.
- [ ] Có ít nhất năm kiểu bố cục khác nhau trong bộ.
- [ ] Chữ tiếng Việt hiển thị đủ dấu, kể cả `ượ ầ ế ộ ữ ỹ ằ`.
- [ ] Cỡ chữ nhỏ nhất trong phần thân không dưới 24 px.
- [ ] Không có slide "Cảm ơn" hoặc "Q&A".
- [ ] Không dùng bốn con số ở Phần 6.
- [ ] Đọc lướt chỉ riêng phần thân các slide vẫn nắm được mạch lập luận.
