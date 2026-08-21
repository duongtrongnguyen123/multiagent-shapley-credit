# Quy trình nhờ model sửa văn phong một phần báo cáo (tiết kiệm token)

Dùng khi muốn một model mới (context sạch) đánh bóng văn phong tiếng Việt cho **một phần**
của `BAO_CAO.tex`, mà không tốn token đọc cả bài.

## Nguyên tắc tiết kiệm

**Không cho model đọc kết quả, không cho đọc cả file.** Sửa văn phong không cần biết số liệu.
Cho đọc kết quả vừa tốn token vừa khiến model dễ tự ý "sửa" số. Chỉ cần:

1. **Đoạn văn bản cần sửa**, cắt ra file riêng.
2. **Danh sách thuật ngữ đã thống nhất** (dán thẳng trong prompt, ~20 dòng) để nó không đổi tên.
3. **Luật hard-constraint** để không phá LaTeX.

So sánh với §3+§4: cắt riêng ≈ **3,7k token**; cả `BAO_CAO.tex` ≈ **19,7k token** → tiết kiệm 5,3×.

## Bước 1 — cắt phần cần sửa

```bash
cd report
a=$(grep -n '^\\section{Phương pháp đo lường}' BAO_CAO.tex | cut -d: -f1)
b=$(grep -n '^\\section{Kết quả}' BAO_CAO.tex | cut -d: -f1)
sed -n "${a},$((b-1))p" BAO_CAO.tex > SEC34.tex
```

Đổi hai tên `\section{...}` cho phần khác. Sau khi model trả kết quả, ghép lại:

```bash
head -n $((a-1)) BAO_CAO.tex  > /tmp/new.tex
cat SEC34.tex                >> /tmp/new.tex
tail -n +$b BAO_CAO.tex      >> /tmp/new.tex
mv /tmp/new.tex BAO_CAO.tex
tectonic BAO_CAO.tex    # phải ra 0 lỗi
```

## Bước 2 — prompt (dán nguyên văn, đổi tên file cho đúng phần)

---

Bạn là biên tập viên tiếng Việt cho một báo cáo khoa học về mô hình ngôn ngữ. Nhiệm vụ: **chỉ
sửa văn phong** file `report/SEC34.tex` cho tự nhiên như người Việt viết, **không đổi nội dung**.

Đọc file, viết lại, ghi đè lại chính file đó. Không đọc file nào khác.

### TUYỆT ĐỐI KHÔNG ĐỔI

- Mọi con số, đơn vị, dấu phẩy thập phân (`0{,}244`, `+14{,}0`, `2,9×`).
- Mọi ký hiệu toán và lệnh LaTeX: `$...$`, `\[...\]`, `\begin{...}...\end{...}`,
  `\label{}`, `\ref{}`, `\cite{}`, `\S`, `\emph`, `\textbf`, `\texttt`, `\todoD`, `\todoTD`,
  và các macro riêng `\dceil`, `\dhonest`, `\CEIL`, `\acc`, `\mucB`.
- **Tên thuật ngữ đã thống nhất** (đổi là hỏng tính nhất quán toàn bài):
  - Ba khái niệm khung: **Tiềm năng cải thiện** ($H$) — **Khả năng khai thác** ($\kappa$) —
    **Thiệt hại** ($D$).
  - Ba nhân vật thí nghiệm tiếp xúc: $W$ (model yếu) / $I$ (model mạnh độc lập) /
    $E$ (model mạnh có tiếp xúc); bài làm của $W$ gọi là **artifact**.
  - Ba số hạng: $G$ (cơ hội) / $L$ (thiệt hại) / $R$ (phần cứu được).
  - Bốn vai pipeline: $P$ planner / $S$ solver / $V$ verifier / $A$ aggregator.
  - **chênh** (chênh lệch năng lực), $g^\ast$, **sàn nhiễu**, **fold**, **mức A / mức B**,
    **VOID**, **tiền đăng ký**, **điều kiện hợp lệ**, **niêm phong**.
  - Gọi $H$ là **tiềm năng cải thiện**. **Không dùng "dư địa"** (sắc thái kinh tế) và không
    dùng "khả năng cải thiện" (dễ lẫn với "khả năng khai thác" của $\kappa$).
  - Từ mượn giữ nguyên, đừng dịch cưỡng ép: *model, pool, prompt, token, benchmark, greedy,
    oracle, artifact, adapter, trace, fold, pipeline*.
- Cấu trúc mục: giữ nguyên số lượng và thứ tự `\section` / `\subsection` / `\paragraph`,
  giữ nguyên các `\label`.

### CẦN SỬA — các lỗi văn phong dịch máy

1. **Bỏ "được" thừa.** Tiếng Việt ít bị động hơn tiếng Anh.
   *"các đại lượng được xây dựng và sử dụng nhất quán"* → *"chúng tôi xây dựng và dùng nhất
   quán các đại lượng"*.
2. **Bỏ danh-từ-hoá bằng "việc" / "sự".**
   *"tác động của việc tiếp xúc"* → *"tác động khi model mạnh tiếp xúc"*.
3. **Bỏ mở đầu rỗng kiểu dịch.** *"Điểm quan trọng của thiết kế này là..."*,
   *"Một điều cần lưu ý là..."* → vào thẳng mệnh đề chính.
4. **Cắt câu dài.** Câu quá 40 chữ thì tách. Trong file hiện có ít nhất 4 câu 47–66 chữ.
5. **Bỏ "của" chồng tầng.** *"chất lượng của bộ chọn của cơ chế"* → *"chất lượng bộ chọn"*.
6. **Giảm "Chúng tôi" lặp.** Đang có 3 lần trong §3; giữ tối đa 1–2, còn lại đổi sang câu
   không chủ ngữ hoặc chủ ngữ là đối tượng ("Thiết kế này cô lập...").
7. **Dùng từ thuần Việt khi tương đương.** *sử dụng* → *dùng*; *thực hiện* → *làm/chạy*;
   *tiến hành* → bỏ; *nhằm mục đích* → *để*.
8. **Trật tự tự nhiên.** Tiếng Việt đưa thông tin cũ lên trước, thông tin mới ra sau; đừng
   bê nguyên trật tự câu tiếng Anh.

### GIỮ NGUYÊN GIỌNG

Trung tính, mô tả, không cảm thán. **Không** thêm tính từ đánh giá ("ấn tượng", "mạnh mẽ",
"đáng kể"), **không** thêm câu hỏi tu từ, **không** thêm mệnh lệnh với người đọc.

### ĐẦU RA

1. Ghi đè `report/SEC34.tex` bằng bản đã sửa (giữ nguyên độ dài dòng ~100 ký tự cho dễ diff).
2. Rồi báo lại danh sách ngắn: mỗi sửa đổi đáng kể một dòng, dạng
   `dòng ~N: "trích cũ" → "trích mới" (loại lỗi 1–8)`. Tối đa 25 dòng.
3. Nếu thấy chỗ nào **nội dung** đáng ngờ, **đừng sửa** — liệt kê riêng ở cuối để nhóm quyết.

---

## Bước 3 — kiểm tra sau khi ghép

```bash
tectonic BAO_CAO.tex          # 0 lỗi
git diff --stat               # chỉ SEC34/BAO_CAO thay đổi
git diff BAO_CAO.tex | grep -E '^[-+].*[0-9]{1,3}\{,\}[0-9]'   # soi xem có số nào bị đổi
```

Câu lệnh cuối là chốt chặn quan trọng nhất: nếu nó in ra cặp `-`/`+` nào mà con số khác nhau
thì model đã sửa số — phải hoàn tác.
