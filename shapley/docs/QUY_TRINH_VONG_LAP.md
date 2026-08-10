# Quy trình vòng lặp nghiên cứu tự động

Tài liệu này mô tả cách chạy vòng lặp, và **vì sao nó từng dừng** — kèm quy tắc để không dừng nữa.
Viết sau khi Nguyên chỉ ra: vòng lặp chỉ chạy tiếp mỗi khi anh gõ gì đó.

---

## 1. Vòng lặp

```
kết quả về  →  ĐỌC theo bảng khoá  →  GHI vào IDEAS.md  →  commit+push
            →  THIẾT KẾ phép thử kế  →  ĐĂNG KÝ TRƯỚC + commit  →  CHẠY
            →  gắn monitor  →  (quay lại đầu)
```

**Toàn bộ chuỗi trên phải nằm TRONG MỘT LƯỢT.** Không tách "ghi kết quả" và "chạy phép thử kế"
thành hai lượt khác nhau.

---

## 2. Vì sao vòng lặp từng dừng — nguyên nhân thật

**Tôi kết thúc lượt sau khi báo cáo kết quả.** Chỉ vậy thôi.

Khi một job xong, thông báo đánh thức tôi **đúng một lượt**. Nếu tôi đọc kết quả, ghi chép, commit,
rồi kết thúc lượt — quyền điều khiển trả về cho người dùng và **không gì khởi động lại tôi**
cho đến khi Nguyên gõ tiếp. Vòng lặp không chết vì thiếu thông báo; nó chết vì **tôi tự dừng giữa chu kỳ**.

**Thông báo KHÔNG hỏng.** Trong phiên ngày 2026-08-09/10, mọi monitor đều bắn đúng: 20 lượt shard xong,
lỗi OOM, cảnh báo GPU rỗi. Cái hỏng là **phản ứng của tôi**: coi thông báo là "đến lúc báo cáo"
thay vì "đến lúc chạy bước kế".

**Bằng chứng trong phiên:**
- H40 gộp xong → ghi chép → **dừng**
- H42 gộp xong → ghi chép → viết *"đang soạn, rồi sẽ chạy"* → **dừng**

Câu "đang soạn, rồi sẽ chạy" là trả quyền điều khiển được nguỵ trang thành kế hoạch.
Việc đó mất ~4 phút, không có lý do gì để không nằm trong cùng lượt.

**Thói quen thứ hai làm nặng thêm:** coi một ràng buộc là chướng ngại thay vì đi vòng.
Nguyên nói "đừng chạy trên 5090" → tôi treo H41 và nói *"cứ bảo là tôi chạy"*,
trong khi cách hiển nhiên là **chuyển H41 sang bộ khung shard Kaggle đang chạy tốt**.

**Lỗ hổng cấu trúc:** một thông báo chỉ mua được một lượt. Muốn vòng lặp sống sót qua việc
tôi kết thúc lượt thì cần **tự đặt lịch đánh thức**. Chưa từng đặt → mỗi chu kỳ đều phụ thuộc
vào việc Nguyên có mặt.

---

## 3. Quy tắc bắt buộc

1. **Không bao giờ kết thúc lượt bằng "tôi sẽ làm X".** Làm X, rồi báo cáo X **đã xong**.
2. **Mỗi thông báo hoàn thành ⇒ chạy trọn chu kỳ trong cùng lượt:**
   đọc → ghi → đăng ký trước → CHẠY → gắn monitor → rồi mới báo cáo.
3. **Ràng buộc không phải chướng ngại.** Phần cứng này bị cấm thì chuyển phép thử sang phần cứng khác.
   Chỉ hỏi khi mọi phương án đều bị chặn.
4. **Chỉ thị đứng (standing directive) không cần xin phép lại.** "ok run automatic" là đủ cho mọi vòng sau.
5. **Đặt lịch tự đánh thức** để vòng lặp chạy cả khi không có thông báo và không có người.

---

## 4. Kỷ luật khoa học (không được bỏ)

- **Đăng ký trước KHI CHƯA có số**, commit **trước** khi chạy. Dấu thời gian git là bằng chứng thứ tự.
- Bảng diễn giải phải có **một hàng cho trường hợp giả thuyết CHẾT**.
- Ghi **prior trung thực** trước khi chạy. (Tính đến vòng #81, prior của tôi **sai 4 lần liên tiếp** —
  #78, #79, #80, #81. Đó chính là lý do bảng khoá tồn tại.)
- Ngưỡng hiệu lực khoá trước: `pct_escalated` ∈ .15–.85, tỉ lệ biên dịch ≥ .50, n ≥ 40 mỗi tầng,
  `adapter_leak` ≤ .05, lệch đẳng thức phân rã ≤ .01.
- **Quan sát hậu nghiệm ≠ kết quả.** Nhánh dựng ra sau khi nhìn số phải được đăng ký trước
  và kiểm trên **dữ liệu chưa từng đụng tới** (ví dụ: #49 kiểm trên MBPP 511–974).
- Nhãn rõ **ĐO ĐƯỢC** vs **GIẢ THUYẾT**. Không diễn giải lại sau khi có số.

---

## 5. Bài học vận hành (mỗi cái đều từng gây hỏng thật)

**Trước khi phóng cả loạt kernel — LUÔN chạy thử tại chỗ**
Tải bộ dữ liệu về, chạy **chính các hàm của kernel** trên đó. Hai vòng × 20 phiên GPU đã cháy
vì cột CSV Kaggle là `Question`/`Answer` (viết hoa) còn tôi tra bằng chữ thường.
Chạy thử mất 1 phút và bắt được cả hai lỗi ngay lần đầu.

**Có mã đang chạy tốt thì CHÉP, đừng viết lại**
`kernels_as_m` đã đọc đúng file CSV đó từ lâu. Tôi viết mới → hỏng.

**Cột dữ liệu có thể không phải thứ mình tưởng**
Cột `Answer` của MBPP/MATH-500 bản Kaggle là **cả lời giải**, không phải đáp án cuối (0/500 khớp).
Chấm theo nó thì mọi nhánh ≈ 0 và trông như "kết quả". Lấy đáp án chuẩn từ HF qua **mã băm đề bài**.

**`pkill -f` khớp CHÍNH shell đang gọi nó** — đã tự giết phiên 4 lần. Kill theo PID.

**Tính lại batch mỗi khi đổi phần cứng/model** — không chép lại.
Thủ phạm hay bị quên: logits tiền xử lý `[B, T, 151936]` — ở B=32 nó đòi **4.25 GiB** một lần cấp phát.
Nên có **lùi lô khi OOM** (chia đôi đến khi vừa) để một đề dài không giết cả shard.

**GPU thuê là tài nguyên khan hiếm** — kiểm bằng `nvidia-smi --query-compute-apps` + watt,
không bao giờ chỉ bằng `pgrep`. Và **kiểm tra có job của người khác** trước khi coi GPU là của mình.

**Trên máy remote: mỗi lúc một job.** Supervisor phải có `flock`, sổ ghi việc đã xong
(job xong thì KHÔNG BAO GIỜ chạy lại), pop hàng đợi có kiểm chứng, và tên tag lấy từ trường
`TAG|lệnh` — không đoán bằng `$(NF-1)` (đã sinh ra thông báo vô nghĩa "END 96 OK").

**Đợi GPU trống LIÊN TỤC 3 lần kiểm** trước khi khởi động, để không chen vào khe hở
giữa hai giai đoạn của job người khác.

**Kernel Kaggle không có internet thì `pip install` chết.** Ảnh Kaggle **không** có sẵn
`bitsandbytes` → muốn nf4 phải bật `enable_internet`. Nếu không, im lặng lùi về fp16.

**Tên file đầu ra của shard PHẢI là duy nhất trên toàn bộ loạt chạy**
H45 chạy 4 ô × 5 shard, nhưng kernel đặt tên `res_H45s{0..4}.json` theo chỉ số shard TRONG ô
-> **cả 4 ô sinh ra CÙNG 5 tên file**, tải về đè lên nhau. 15 shard xong nhưng chỉ còn 5 file.
Nếu không để ý thì đã gộp 1/4 dữ liệu mà vẫn tưởng là đủ. Cách chữa: tải mỗi kernel vào
**thư mục riêng**, và script gộp dùng `glob(..., recursive=True)` + **đếm số ô, thiếu thì TỪ CHỐI kết luận**.
Dấu hiệu bắt được: *số shard báo xong* ≠ *số file trên đĩa*. Luôn so hai con số này.

**Kiểm cú pháp KHÔNG đủ khi cắt/ghép kernel**
Dựng H48 bằng cách cắt một đoạn của kernel cũ: `ast.parse` PASS, nhưng đoạn cắt đã xoá mất
`mktok`, `probe_src`, `gen`, `task_prompt` — những hàm mà phần còn lại vẫn gọi. 12 kernel sẽ
chết vì `NameError`. Cách bắt: sau khi dựng, **liệt kê hàm đã định nghĩa bằng AST và đối chiếu
với danh sách hàm cần có**, rồi kiểm mọi tên toàn cục đã được gán (`symtable`).
Cú pháp đúng ≠ tên tồn tại.

**Bí mật:** token `KGAT_...` không bao giờ được commit. `accounts.txt`, `manifest*.json`,
`kernels_*/`, `monitor.sh` đều nằm trong `.gitignore`. Tên tài khoản không xuất hiện trong tài liệu chung.

---

## 6. Việc kiểm tra trước mỗi lần phóng loạt

- [ ] Đăng ký trước đã commit **trước** khi chạy, có hàng "giả thuyết chết"
- [ ] Đã tải dữ liệu thật và chạy thử **hàm của chính kernel** trên đó
- [ ] Đáp án chuẩn lấy từ nguồn đáng tin, không phải cột mơ hồ
- [ ] Batch tính từ VRAM, có lùi lô khi OOM
- [ ] Không có token trong thứ sắp commit
- [ ] Monitor bám **mọi trạng thái kết thúc**, không chỉ trạng thái thành công
- [ ] Script gộp **từ chối kết luận** khi thiếu shard **hoặc thiếu ô**
- [ ] Tên file đầu ra **duy nhất toàn loạt** (không chỉ duy nhất trong một ô)
- [ ] Sau khi tải: **số file trên đĩa == số shard báo xong**
- [ ] Kernel dựng bằng cắt/ghép: **đối chiếu danh sách hàm bằng AST**, không chỉ `ast.parse`
