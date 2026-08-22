# Kịch bản thuyết trình — Nhóm 13, INT3406

25 slide · 20 phút trình bày (slide 1–20) · slide 21–24 là dự phòng cho phần hỏi đáp.
Chia bốn người, mỗi người 5 slide. Chữ in nghiêng là ghi chú thao tác, không đọc lên.

| Người | Slide | Thời lượng |
|---|---|---|
| Người 1 | 1–5 | ~4 phút |
| Người 2 | 6–10 | ~5 phút |
| Người 3 | 11–15 | ~6 phút |
| Người 4 | 16–20 | ~5 phút |

---

# NGƯỜI 1

## Slide 1 — Bìa · 20 giây

Chào thầy và các bạn. Nhóm 13 xin trình bày khảo sát về hệ suy luận đa tác tử. Câu hỏi của
nhóm là: khi ta ghép nhiều model lại thành một hệ có phân vai, phần lợi ích đo được thực sự
đến từ đâu.

*Sang slide 2 ngay, đừng đọc tên từng thành viên.*

## Slide 2 — Ví dụ · 90 giây

Em bắt đầu bằng một trường hợp cụ thể.

Đề bài bên trái: tìm số nguyên dương nhỏ nhất chia 7 dư 3 và chia 5 dư 4. Model 7B giải một
mình. Nó đặt n bằng 7k cộng 3, thay vào điều kiện thứ hai, ra k đồng dư 3 theo modulo 5, được
n bằng 24. Nó kiểm lại cả hai điều kiện. Đáp án đúng.

Bên phải là **cùng model 7B đó, cùng đề đó**. Khác đúng một chỗ: trong ngữ cảnh có thêm lời
giải của model 1,5B. Model nhỏ giải sai — nó liệt kê đúng dãy 3, 10, 17, 24 nhưng rồi chọn
"số nhỏ nhất lẻ là 17" một cách vô căn cứ.

*Chỉ vào cột phải.*

Model 7B nhận lời giải đó làm điểm khởi đầu. Nó kiểm lại điều kiện thứ nhất, bỏ qua điều kiện
thứ hai, và giữ nguyên con số 17. Sai.

Đây là điều bọn em muốn nhấn: model mạnh **không hề yếu đi**. Nó chỉ nhìn thấy một lời giải
sai, và thế là đủ. Và đây không phải một ca cá biệt — trên nhóm bài mà model yếu giải sai,
hiệu ứng trung bình là âm 27,2 điểm.

## Slide 3 — Pipeline · 45 giây

Trước khi đi tiếp, đây là kiến trúc bọn em kiểm suốt báo cáo.

Bốn vai nối tiếp: planner lập kế hoạch, solver giải, verifier kiểm và được phép sửa,
aggregator chọn đáp án cuối. Mỗi vai là một lần gọi model.

Kỳ vọng đặt vào kiến trúc này có ba: chia nhỏ độ khó nên mỗi lần gọi chỉ làm một việc; có một
bước kiểm độc lập với bước giải; và tổng hợp được nhiều ứng viên thay vì tin vào một lời giải
duy nhất.

Ba kỳ vọng đó nghe hợp lý. Phần còn lại của bài là kiểm xem chúng có đúng không.

## Slide 4 — Câu hỏi · 30 giây

Câu hỏi trung tâm của bọn em, viết gọn lại là thế này.

*Dừng một nhịp, để người nghe đọc.*

Lợi ích đo được đến từ **cơ chế phối hợp**, hay chỉ từ việc **gọi model nhiều lần hơn**?

Hai thứ này rất dễ lẫn, vì hệ đa tác tử luôn gọi model nhiều lần hơn model đơn lẻ. Muốn tách
được chúng ra thì phải kiểm soát ba thứ mà các nghiên cứu thường bỏ qua.

## Slide 5 — Ba điều kiện đánh giá · 75 giây

Thứ nhất là **ngân sách tính toán**. Nếu đem một hệ gọi model bốn lần so với một model chỉ
chạy một lượt, thì hệ thắng cũng không nói lên điều gì. Bỏ qua điều kiện này thì lợi ích bị
phóng đại.

Thứ hai là **mốc đối chứng**. Phần lớn nghiên cứu đo mức cải thiện so với chính model bị sửa,
tức model yếu. Nhưng trong thực tế người ta phân vân giữa việc chạy cả một hệ phức tạp hay chỉ
dùng một model mạnh. Đo trên mốc yếu cũng làm lợi ích bị phóng đại.

Thứ ba là **phạm vi tác động**. Trong một bộ đề luôn có những bài mà không cơ chế chọn nào đổi
được kết quả — quá khó thì mọi ứng viên đều sai, quá dễ thì mọi ứng viên đều đúng. Tính trung
bình trên cả tập sẽ làm loãng lợi ích thật.

*Chỉ vào dòng kết luận.*

Điểm quan trọng là hai loại sai lệch này **đi ngược chiều nhau**. Hai cái đầu thổi phồng, cái
thứ ba làm teo lại. Nên không thể áp một cái rồi bỏ hai cái kia — phải áp đồng thời cả ba.

*Chuyển người.*

---

# NGƯỜI 2

## Slide 6 — Thiết lập · 60 giây

Em nói qua phạm vi thực nghiệm.

Bốn benchmark: GSM8K và MATH cho suy luận toán, MBPP và HumanEval cho lập trình. Model từ 0,5
đến 32 tỉ tham số, dùng cho cả vai trò lẫn mốc đối chứng.

Một điểm về phương pháp: bọn em dùng giải mã tất định, `do_sample` bằng False. Nghĩa là chênh
lệch giữa các fold hoàn toàn do khác tập bài, không có nhiễu do lấy mẫu ngẫu nhiên.

Bên phải là cách đọc số trong các slide sau. Mỗi mức thay đổi là trung bình trên năm fold.
Ngưỡng hiệu dụng khoảng 3,3 điểm — dưới ngưỡng thì bọn em ghi rõ là chưa vượt ngưỡng chứ không
coi là kết quả. Và thiết kế cùng tiêu chí đánh giá đều được chốt trước khi chạy.

## Slide 7 — Mức dao động nền · 50 giây

Con số 3,3 điểm đó ở đâu ra, em giải thích nhanh.

Bọn em chạy **cùng một cấu hình** trên năm tập bài khác nhau. Không đổi gì cả, chỉ đổi bài.
Mức cải thiện của verifier dao động từ cộng 1,0 đến cộng 8,0 điểm, độ lệch chuẩn là 2,65 điểm.

*Chỉ vào trục.*

Từ đó suy ra ngưỡng hiệu dụng khoảng 3,3 điểm. Đây là lý do mọi con số trong các slide sau đều
là trung bình năm fold, chứ không phải một phép đo đơn lẻ.

## Slide 8 — Pipeline có lợi hay có hại · 70 giây

Đây là phép đo đầu tiên, chưa áp điều kiện nào cả.

Trên GSM8K, pipeline bốn vai đạt 0,744 so với 0,632 của một lần sinh — hơn 11,2 điểm. Nghe rất
tốt.

*Chỉ sang dòng MATH.*

Nhưng trên MATH thì ngược: 0,345 so với 0,405, tức **kém 6 điểm**. Cùng một kiến trúc, cùng
một model, chỉ đổi task, và dấu của hiệu ứng đảo ngược.

Cột cuối là chi phí. GSM8K tốn gấp 2,9 lần token, MATH tốn gấp 6,63 lần. Nghĩa là kể cả ở task
mà pipeline có lợi, nó vẫn đắt gấp gần ba lần. Còn ở task nó có hại thì đắt gấp gần bảy lần.

Vậy lợi ích không phổ quát, mà chi phí thì luôn có.

## Slide 9 — Giá trị nằm ở đâu · 75 giây

Câu hỏi tiếp theo: cái 11,2 điểm trên GSM8K đến từ đâu — từ việc verifier phê bình, hay chỉ vì
model được sinh thêm một lượt nữa?

Bọn em làm một đối chứng đơn giản. Cho model giải lại **có đọc** phê bình của verifier: kết quả
0,453. Cho model giải lại **không đọc gì cả**, chỉ giải lại, cùng ngân sách: cũng 0,453.

*Dừng một nhịp.*

Hai con số bằng nhau tới chữ số thứ ba, trong khi mức dao động nền là 2,65 điểm. Tức là nội
dung phê bình **không đóng góp gì**. Cái tạo ra giá trị chỉ là có thêm một lần sinh.

Hai kết quả bên phải củng cố điều đó. Với cùng ngân sách tám lần sinh, để model tự đọc rồi tổng
hợp thì kém bỏ phiếu đa số từ 19 đến 26 điểm — cơ chế thông minh hơn lại tệ hơn cách đếm phiếu.
Và biến thể vòng lặp giải-rồi-chấm, rẻ hơn pipeline đủ bốn vai, còn hơn nó 4 điểm trên MATH.

## Slide 10 — Shapley · 70 giây

Nếu giá trị nằm ở số lần sinh, thì từng vai đóng góp bao nhiêu?

Bọn em chạy đủ mười sáu tổ hợp bật tắt bốn vai, rồi tính giá trị Shapley. Đóng góp của một vai
là mức thay đổi trung bình khi thêm vai đó vào mọi tổ hợp con.

*Chỉ vào biểu đồ.*

Solver và aggregator đóng góp dương. Planner là vai duy nhất nằm bên trái vạch không.

Ví dụ cụ thể: thêm planner vào tổ hợp solver-aggregator làm giảm 12 điểm, từ 0,682 xuống 0,562.

Một lưu ý về cách đọc: giá trị của verifier trong bảng là **suy ra bằng đối xứng với solver,
không phải số đo**, nên bọn em không xếp hạng nó cùng ba vai kia.

Và điều đáng nói nhất: khi nâng riêng planner lên 7B, đóng góp của nó đảo dấu. Nghĩa là đóng
góp của một vai không phải thuộc tính cố định — nó là hàm của năng lực model.

*Chuyển người.*

---

# NGƯỜI 3

## Slide 11 — Vai được gán khác vai thực thi · 75 giây

Shapley cho biết đóng góp gắn với **nhãn** vai trò. Nhưng cái nhãn đó có phản ánh hành vi thật
không? Bọn em đọc trace để kiểm.

Planner bị cấm tính đáp án. Nhưng trên MATH, 34,7% số lần kế hoạch của nó **đã chứa sẵn đáp án
đúng**. Trên GSM8K là 14%.

Solver lẽ ra phải sinh lời giải. Nhưng 62% số lần trên MATH, nó không sinh ra một con số mới
nào — chỉ chép lại.

Aggregator lẽ ra phải chọn giữa các ứng viên. Trên hai nghìn lượt, nó chỉ **ba lần** đưa ra một
đáp án vừa mới vừa đúng.

*Chỉ vào dòng kết luận.*

Ba vai này đang làm các phiên bản của cùng một việc. Chỉ số tương tác Shapley xác nhận: solver,
verifier và aggregator thay thế nhau chứ không bổ sung nhau.

Có một điều kiện quan trọng: ở model 7B các hiện tượng này gần như biến mất, planner chỉ còn rò
đáp án 4% trên MATH. Kết luận này chỉ áp cho model nhỏ.

## Slide 12 — Verifier · 70 giây

Riêng verifier bọn em đo kỹ hơn, vì nó là vai được kỳ vọng nhiều nhất.

Khi verifier 1,5B kiểm solver 1,5B — tức cùng cỡ — độ chính xác can thiệp chỉ 56 đến 59%. Gần
mức đoán mò. Bọn em thử tiêm lỗi vào một chữ số trong đáp án, nó không phát hiện được.

*Chỉ sang cột phải.*

Khi verifier là 7B kiểm solver 1,5B, độ chính xác lên 98%, tỷ lệ sửa trên phá là 43 trên 1,
hiệu ứng cộng 14 điểm.

Phần chênh do cỡ model lớn hơn là 11 điểm. Nói cách khác, gần như **toàn bộ** giá trị của bước
kiểm đến từ việc dùng model mạnh hơn, chứ không từ việc thêm một vai vào pipeline.

## Slide 13 — Mốc so sánh · 80 giây

Đây là đóng góp phương pháp luận mà nhóm em muốn nhấn nhất.

Trục ngang là khoảng cách năng lực giữa model yếu và model mạnh. Trục dọc là hiệu ứng của hệ đa
tác tử.

*Chỉ đường trên.*

Đường này là hiệu ứng đo **so với model yếu**. Càng chênh lệch nhiều, hiệu ứng càng tăng. Nhìn
đường này thì kết luận là: càng chênh năng lực càng tốt.

*Chỉ đường dưới.*

Đường này là **cùng thí nghiệm đó**, nhưng đo so với model mạnh chạy một mình. Càng chênh lệch
nhiều, hệ càng thua model mạnh đơn lẻ.

Hai đường cắt nhau. Nghĩa là tồn tại một vùng mà hai mốc cho hai kết luận **trái ngược nhau**
trên cùng một dữ liệu. Điểm duy nhất hệ đa tác tử thắng model mạnh đơn lẻ là khi khoảng cách
bằng không, được cộng 7,7 điểm.

Nên khi đọc bất kỳ báo cáo nào về generate-and-refine, câu hỏi đầu tiên phải là: họ đo trên mốc
nào.

## Slide 14 — Mẫu số · 65 giây

Điều kiện thứ ba: phạm vi tác động.

Bọn em phân tầng toàn bộ tập theo trạng thái của pool ứng viên. 32% số bài là quá khó — cả năm
lần sinh đều sai, không cơ chế chọn nào cứu được. 25% là quá dễ — cả năm lần đều đúng, chọn kiểu
gì cũng đúng.

*Chỉ hai đoạn xám.*

Cộng lại là 57% số bài nằm ngoài tầm can thiệp.

Trên 43% còn lại, hiệu ứng thật là cộng 26,7 đến cộng 41,7 điểm tuỳ tầng. Nhưng nếu tính trung
bình trên cả tập, con số đó bị pha loãng từ 2,3 đến 3,3 lần — đủ để một can thiệp có giá trị bị
kết luận nhầm là vô dụng.

## Slide 15 — Thí nghiệm trung tâm · 90 giây

Đây là thí nghiệm chính của cả khảo sát, và cũng là chỗ giải thích cho ví dụ ở đầu buổi.

Thiết kế rất chặt. Một đề bài, 500 bài MATH, chia hai nhánh. Nhánh I: model mạnh giải độc lập,
ngữ cảnh chỉ có đề bài. Nhánh E: cùng model mạnh đó, cùng lệnh giải, cùng ngân sách sinh, chỉ
khác một chỗ — trong ngữ cảnh có thêm lời giải của model yếu.

*Nhấn.*

Khác **duy nhất** một chỗ: nội dung ngữ cảnh.

Rồi bọn em phân tầng theo nội dung của lời giải đó. Khi lời giải của model yếu **đúng**, model
mạnh được lợi 3,8 điểm. Khi lời giải đó **sai**, model mạnh mất 27,2 điểm.

Hai tầng hoàn toàn không đối xứng: cái hại lớn gấp bảy lần cái lợi.

Kết luận là: không phải việc nhìn thấy lời giải gây hại, mà là **nội dung** của lời giải đó.
Cùng một cơ chế, nội dung đúng thì giúp, nội dung sai thì phá.

*Chuyển người.*

---

# NGƯỜI 4

## Slide 16 — Cơ chế · 80 giây

Slide trước cho biết cái gì xảy ra. Slide này giải thích tại sao.

Bọn em phân tầng 500 bài theo trạng thái của cả hai model: model yếu W đúng hay sai, và model
mạnh I khi giải độc lập đúng hay sai.

*Chỉ ô dưới trái.*

Ô này là vùng rủi ro: model mạnh vốn đúng, model yếu sai. Hệ phá hỏng 77 trên 121 bài, tức
63,6%. Gần hai phần ba.

*Chỉ ô dưới phải.*

Ô này là vùng cơ hội: cả hai cùng sai, hệ có cơ hội tạo ra lời giải mới. Nó chỉ làm được 6 trên
140 bài, tức 4,3%.

*Chỉ ô trên phải.*

Còn ô này, khi model yếu đúng mà model mạnh sai, hệ truyền lại đáp án đúng: 10 trên 11 bài.

Ghép ba ô lại thì hành vi rất rõ: hệ **truyền** đáp án rất tốt, nhưng **tạo** ra đáp án mới thì
gần như không. Đó là hành vi của một kênh truyền, không phải của một cơ chế sửa lỗi.

## Slide 17 — Tín hiệu kiểm chứng · 70 giây

Vậy có cách nào để bước kiểm thực sự hoạt động không? Bọn em so hai loại tín hiệu.

Bên trái là tín hiệu chắc chắn: trên bài lập trình, chạy test. Kết quả là **không phá hỏng bài
nào trong cả hai mươi fold**, và lấy được gần trọn trần lý thuyết.

*Chỉ sang phải.*

Bên phải là tín hiệu học được: bọn em huấn luyện một bộ phân loại lỗi, đạt AUC 0,893. Chất
lượng phát hiện rất cao. Nhưng khi đem đi chọn ứng viên, nó chỉ đổi được 2,4 điểm — dưới ngưỡng
3,3 — và chỉ 2 trên 5 fold dương.

Bài học ở đây: chất lượng phát hiện lỗi cao **không tự động đổi thành điểm số**. Trần bị chặn
bởi pool — nếu không ứng viên nào đúng thì không bộ chọn nào cứu được.

## Slide 18 — Huấn luyện · 80 giây

Câu hỏi cuối: nếu các vai không làm đúng chức năng, ta huấn luyện chúng làm đúng được không?

Nhóm em thử bảy phương pháp. Đây là bốn dòng tiêu biểu.

GRPO thưởng theo can thiệp: precision đạt tuyệt đối trên cả năm fold. Nhưng lối tắt là **im
lặng** — số lần can thiệp giảm từ 20,2 xuống 8,4. Nó đạt precision hoàn hảo bằng cách nói ít
đi một nửa.

Bọn em vá lỗ đó, chuyển sang thưởng theo đáp án cuối. Được 1,8 điểm, dưới ngưỡng. Lối tắt mới
là **nhại solver** — độ dài đầu ra rút từ 480 xuống 19 ký tự.

Credit-RL dùng chính đóng góp Shapley làm tín hiệu thưởng: không vai nào trong bốn vai cải
thiện. Planner sập hẳn về kế hoạch rỗng ở 200 trên 200 bài.

Đồng huấn luyện ba vai: 0,690 thành 0,690. Không đổi gì.

*Chỉ dòng kết luận.*

Mỗi lần bọn em chặn một kiểu lách, phương pháp lại tìm ra kiểu khác. Vấn đề không nằm ở thuật
toán, mà ở chỗ hàm mục tiêu cho phép đạt điểm mà không buộc vai trò làm đúng việc.

## Slide 19 — Khi nào nên dùng · 70 giây

Tổng hợp lại thành một hướng dẫn dùng được.

Câu hỏi thứ nhất: có tín hiệu kiểm chứng khách quan không — chạy được test, đối chiếu được
không? Nếu không, dùng model mạnh đơn lẻ.

Thứ hai: model nền còn tiềm năng cải thiện, hay đã bão hoà trên task này? Nếu đã bão hoà, thêm
cơ chế chỉ tăng chi phí.

Thứ ba: người kiểm có mạnh hơn người bị kiểm không? Nếu cùng cỡ, bước kiểm gần như vô nghĩa.

Đủ cả ba thì phối hợp đa tác tử mới có khả năng mang lại lợi ích.

*Chỉ dòng bên phải.*

Và ngay cả khi đủ ba điều kiện, đừng đưa lời giải chưa được kiểm của model yếu vào ngữ cảnh của
model mạnh. Đó là kết quả rõ nhất của cả báo cáo.

## Slide 20 — Chốt · 45 giây

Ba điều nhóm em muốn để lại.

Lợi ích đo được phần lớn đến từ việc sinh nhiều lần, không từ cơ chế phối hợp.

Đổi mốc so sánh làm đảo dấu kết luận — nên phải báo cáo cả hai mốc.

Và lời giải sai của model yếu gây hại nhiều hơn lời giải đúng mang lợi.

Phối hợp đa tác tử không mặc định tạo ra lợi ích. Nó phụ thuộc vào năng lực model, cách tổ chức
thông tin, và cơ chế kiểm chứng.

Phần trình bày của nhóm em đến đây là hết. Nhóm em xin nghe câu hỏi của thầy và các bạn.

---

# SLIDE DỰ PHÒNG — chỉ mở khi được hỏi

## Slide 21 (D1) — Bảng huấn luyện

*Mở khi được hỏi "còn ba phương pháp kia thì sao".*

Đây là bảng đầy đủ hơn. Ngoài bốn dòng đã trình bày còn có ORPO cho aggregator, credit-RL giai
đoạn hai, và một biến thể GRPO với bất đối xứng thông tin. Biến thể cuối đáng chú ý nhất: nó đo
đồng thời hai mốc trên cùng một lần chạy — so với model yếu được cộng 17 điểm, nhưng so với
chính model kiểm khi tự giải thì âm 10,4 điểm. Cùng một mô hình, hai mốc, hai dấu.

## Slide 22 (D2) — Bảng Shapley đầy đủ

*Mở khi được hỏi về con số Shapley cụ thể.*

Đây là giá trị Shapley trên cả hai task, kèm khoảng tin cậy. Ba điểm cần lưu ý.

Thứ nhất, hàng verifier không có khoảng tin cậy vì nó là giá trị suy ra bằng đối xứng với
solver, không phải số đo.

Thứ hai, khoảng tin cậy của planner **cắt qua không** ở cả hai task. Nên chính xác thì phải nói
đóng góp của planner không phân biệt được với không, chứ chưa đủ để gọi là âm. Cái chắc chắn là
mức chênh khi nâng lên 7B.

Thứ ba, trên MATH mọi chênh lệch giữa các vai đều dưới mức dao động nền, nên thứ hạng ở cột đó
không có ý nghĩa.

## Slide 23 (D3) — Quy đổi chi phí

*Mở khi được hỏi "hệ đa tác tử có rẻ hơn không".*

Nếu đếm theo lượt gọi thì pipeline rẻ hơn 12%, vì các vai dùng model nhỏ hơn. Nhưng đó là chi
phí danh nghĩa. Token sinh của pipeline là 2,9 lần trên GSM8K và 6,63 lần trên MATH. Nhân số
token với chi phí mỗi token theo cỡ model, tức quy về FLOP, thì phần rẻ hơn biến mất.

## Slide 24 (D4) — Kiểm chuyển miền

*Mở khi được hỏi "quy luật có tổng quát không".*

Bọn em khớp quy luật trên MBPP rồi đem dự báo sang miền toán mà không khớp lại. Hai trên ba cặp
nằm trong khoảng tin cậy, nên quy luật không bị bác bỏ.

Nhưng có hai hạn chế phải nói rõ. Khoảng tin cậy khá rộng nên phép kiểm có độ phân giải thấp.
Và thứ tự ba điểm không đơn điệu — cặp chênh 0,244 cho hiệu ứng âm sâu hơn cặp chênh 0,288. Nên
tính đơn điệu của quy luật chưa được xác nhận trên miền toán.

---

# CÂU HỎI DỰ ĐOÁN

**"Kết quả toàn âm thì đóng góp của nhóm là gì?"**
Đóng góp là khung đo. Ba điều kiện đánh giá và thí nghiệm hai nhánh có thể dùng lại cho bất kỳ
hệ đa tác tử nào. Và kết quả âm có điều kiện rõ ràng: bọn em chỉ ra chính xác khi nào cơ chế
hoạt động — có tín hiệu khách quan, model chưa bão hoà, người kiểm mạnh hơn.

**"Sao không thử model lớn hơn?"**
Phạm vi là 0,5 đến 32 tỉ tham số, chạy trên GPU miễn phí. Bọn em ghi rõ trong phần hạn chế rằng
kết luận chưa suy rộng được cho model siêu lớn. Nhưng xu hướng theo năng lực đã quan sát được
trong dải này, và nó đi theo hướng các hiện tượng giảm dần khi model mạnh lên.

**"Mức dao động nền 2,65 điểm có làm mọi kết quả thành vô nghĩa không?"**
Không, vì đó chính là lý do bọn em chia năm fold. Sai số chuẩn là 2,65 chia căn năm, và các kết
quả chính đều vượt ngưỡng với kiểm định t. Những kết quả không vượt thì bọn em ghi rõ là chưa
vượt ngưỡng.

**"Thí nghiệm artifact có phải chỉ là prompt injection không?"**
Khác ở chỗ không có ý đồ tấn công. Lời giải của model yếu là đầu ra bình thường của chính
pipeline đó, không ai cố tình chèn gì. Đây là chế độ hỏng nội tại của kiến trúc sinh-rồi-sửa,
không phải kịch bản đối kháng.
