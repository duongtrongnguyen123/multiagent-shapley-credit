# QUY TRÌNH VIẾT BÁO CÁO — làm theo thứ tự này

> Ba tệp, ba việc khác nhau — **đừng lẫn**:
> - **`BAO_CAO_CAU_TRUC.md`** — *viết CÁI GÌ*: luận điểm, khung, 9 mục, 7 hình
> - **`HUONG_DAN_CONG_TAC.md`** — *được phép viết CON SỐ NÀO*: ba tầng bằng chứng, bảng số chốt
> - **`QUY_TRINH_VIET_BAO_CAO.md`** (tệp này) — *làm THEO THỨ TỰ NÀO*
>
> Nếu chỉ đọc được một tệp trước khi bắt đầu: đọc **§0 của `BAO_CAO_CAU_TRUC.md`**.

---

## Bước 0 — Trước khi ai viết dòng nào *(cả nhóm, ~30 phút)*

- [ ] Cả ba người đọc **§0 `BAO_CAO_CAU_TRUC.md`** (luận điểm hợp nhất). Một trang.
- [ ] Cả ba người đọc **§1 + §2 + §3 `HUONG_DAN_CONG_TAC.md`** (tầng bằng chứng · số chốt · điều cấm).
- [ ] **Thống nhất một câu luận điểm** và ghi nó vào đầu file bản thảo. Mọi mục sau phải phục vụ câu đó.
- [ ] Chốt: nộp **tiếng Việt**. (Nếu phải tiếng Anh → dịch **sau khi** đóng băng nội dung, đừng dịch song song.)

> **Đừng bỏ qua bước này.** Ba mảng công việc dùng từ vựng khác nhau ("verifier gain" / "Δ_ceil" /
> "cost per query"). Không thống nhất trước thì báo cáo sẽ đọc như ba bài dán lại.

---

## Bước 1 — Dựng khung rỗng *(Nguyên, ~1 giờ)*

- [ ] Tạo `docs/BAO_CAO.md` với **đủ 9 tiêu đề mục + phụ lục**, mỗi mục để `TODO` và **số trang dự kiến**
- [ ] Dán **§0 luận điểm hợp nhất** vào ngay dưới tiêu đề, dạng khối trích dẫn
- [ ] Dán bảng số chốt (`HUONG_DAN_CONG_TAC.md` §2) vào **phụ lục** trước — để lúc viết chỉ việc trỏ tới

**Xong khi:** mở file ra thấy được toàn bộ hình dạng bài, dù chưa có chữ nào.

---

## Bước 2 — Viết SONG SONG, không tuần tự *(cả nhóm, ~3–4 ngày)*

Ba người viết **cùng lúc**, mỗi người phần không đụng nhau:

| người | mục | phụ thuộc gì |
|---|---|---|
| **Đức** | **§2 Công trình liên quan** | không phụ thuộc ai — bắt đầu ngay |
| **Tùng Dương** | **§4 Thiết lập** + **Hình 5** | không phụ thuộc ai — bắt đầu ngay |
| **Nguyên** | **§3 Khung** → **§5.4/5.5/5.6** → **§6** | §6 phải viết **sau cùng** |

**Thứ tự bắt buộc bên trong phần của Nguyên:** §3 (khung) → §5 (kết quả) → §6 (tổng hợp).
Viết §6 trước sẽ ra một bài luận không có số đỡ.

### Quy tắc khi viết một mục kết quả
Mỗi mục §5 viết theo đúng 4 nhịp này:
1. **Câu hỏi** — mục này trả lời gì? (một câu)
2. **Thiết kế** — đo thế nào, cổng nào? (2–3 câu)
3. **Số** — bảng, kèm p hoặc khoảng tin cậy
4. **Đọc số** — nghĩa là gì, **và giới hạn của nó là gì**

> Nhịp 4 là chỗ báo cáo này khác một bài báo tầm thường. **Đừng cắt nó cho ngắn.**

---

## Bước 3 — Vẽ hình *(song song với bước 2)*

Theo bảng ở cuối `BAO_CAO_CAU_TRUC.md`. Ưu tiên nếu thiếu thời gian: **Hình 2 → 4 → 6**.

- [ ] Mọi hình dùng **cùng một bộ màu** và **cùng cỡ chữ**
- [ ] Trục luôn có **đơn vị**; hiệu ứng luôn có **thanh sai số hoặc khoảng tin cậy**
- [ ] Chú thích hình phải **tự đứng được** — người đọc lướt chỉ xem hình vẫn hiểu

**Hình 2 là hình quan trọng nhất** (nghịch lý hai đường ngược chiều). Nếu chỉ vẽ đẹp được một hình, vẽ nó.

---

## Bước 4 — Kiểm số *(bắt buộc, trước khi ghép)*

- [ ] Mỗi con số trong bản thảo phải **truy được về** `results_X/res_X.json` + tên khoá
- [ ] Chạy lại script đối chiếu (Nguyên có sẵn) — **mọi số phải khớp tuyệt đối**
- [ ] Rà bảng **"đừng viết X / hãy viết Y"** (`HUONG_DAN_CONG_TAC.md` §3), tìm bằng Ctrl-F:
      `khác họ` · `thắng` · `tái lập` · `cổng định tuyến`
- [ ] Rà: không con số nào đến từ **16 lần chạy VOID**

**Xong khi:** người ngoài cầm bản thảo, chọn bừa 5 con số, cả 5 đều tra ngược được về artifact.

---

## Bước 5 — Ghép và làm phẳng giọng văn *(Nguyên, ~nửa ngày)*

- [ ] Ghép ba phần vào `BAO_CAO.md`
- [ ] Thống nhất **thuật ngữ**: dùng đúng một tên cho mỗi khái niệm xuyên suốt
      *(ví dụ: luôn "chênh năng lực", đừng lúc "capability gap" lúc "chênh lệch")*
- [ ] Thống nhất **ký hiệu**: `S` `I` `V` `A` `B` `C` `H` `κ` `D` — định nghĩa **một lần** ở §3, dùng lại
- [ ] Đọc to §1 và §6. Nếu §6 không trả lời được câu hỏi ở §1 thì một trong hai mục sai.

---

## Bước 6 — Nối kết quả còn đang chạy

**H99b** và **H100e** chưa xong. Khi có kết quả, làm **đúng thứ tự này** — không tắt bước:

1. Tải kết quả → **niêm phong hash ngay** (`python deploy/seal_results.py results_X`) → **commit**
2. **Đọc bảng khoá trước** (`PREREGISTRATION.md` #112 cho H99b, #111 cho H100e)
3. **Đọc cổng trước.** Cổng trượt ⇒ **VOID**, chỉ vào phụ lục C, **không đọc số**
4. Cổng đạt ⇒ đọc số, đối chiếu **đúng hàng** của bảng khoá
5. Chỉ khi đó mới sửa bản thảo

### Ảnh hưởng tới bản thảo nếu chúng ra kết quả
| lần chạy | nếu kết quả là… | phải sửa gì |
|---|---|---|
| **H99b** | luật chênh **không** chuyển sang toán (hàng 1 hoặc 4) | **§5.5 và §6 phải thu hẹp luật thành "trên code"** — đây là sửa **bắt buộc**, không phải tuỳ chọn |
| **H99b** | luật **chuyển được** (hàng 2) | §5.5 mạnh lên; §6 thêm một dòng bằng chứng |
| **H100e** | `Δ_honest` **dương** ở ≥ 2/3 cặp | **Kết quả dương dùng được ĐẦU TIÊN** của dự án ⇒ thêm mục §5.8 và sửa §6 |
| **H100e** | không dương | §8 Hạn chế: ghi rõ giao thức độc-lập-trước **không** vượt được model mạnh |

> **Đừng viết trước §5.5 và §6 phần phụ thuộc H99b.** Viết rồi phải xoá thì tốn hơn là chờ.

---

## Bước 7 — Rà cuối *(cả nhóm, ~1 giờ)*

- [ ] Tóm tắt/abstract nêu **khuyến nghị thực dụng**: *"model nhỏ GIẢI, model lớn SOÁT; đừng cho
      model lớn xem bài làm của model nhỏ để SỬA"*
- [ ] §8 Hạn chế **không được làm đẹp** — 6 mục trong `BAO_CAO_CAU_TRUC.md` §8 giữ nguyên tinh thần
- [ ] Đóng góp của **cả ba người** đều xuất hiện trong thân bài, không bị đẩy hết xuống phụ lục
- [ ] §7 nêu **cả hai chuẩn kiểm chứng** (fold vs đăng ký trước) — đừng giấu một cái
- [ ] Tỉ lệ VOID **52%** và sổ tiên nghiệm **21/42** có mặt — đó là điểm mạnh, không phải điểm yếu

---

## Sai lầm hay gặp — tránh sẵn

| sai lầm | vì sao chết | cách tránh |
|---|---|---|
| Ba mảng viết như ba bài rời | Mất luận điểm, mất điểm cao nhất | Bước 0 chốt một câu; §6 phải khâu ba mảng lại |
| Trích số từ lần chạy VOID | Đã xảy ra thật ở #114/#121/#123 | Bước 4, và `HUONG_DAN_CONG_TAC.md` §1 |
| Viết "chênh nhỏ thì sửa THẮNG" | Chiều khẳng định **chưa xác lập** | Chỉ viết chiều phủ định |
| Gộp số của hai mảng vào một bảng | Hai chuẩn kiểm chứng khác nhau | Ghi rõ chuẩn ở mỗi bảng, hoặc tách bảng |
| Để §8 Hạn chế thành ba dòng chiếu lệ | Người chấm nhìn ra ngay | Giữ đủ 6 mục |
| Đợi H99b/H100e rồi mới viết | Hết thời gian | Viết §1–§4, §5.1–§5.4, §7 **ngay bây giờ** — chúng không phụ thuộc |

---

## Đường găng — làm gì trước nếu gấp

```
Bước 0  →  §3 Khung  →  §5.1–§5.4  →  §6 Tổng hợp  →  §1 Mở đầu  →  phần còn lại
```
**§1 viết SAU §6.** Chỉ khi biết chắc mình kết luận gì thì mới viết được mở đầu cho gọn.
