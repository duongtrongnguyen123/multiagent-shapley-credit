# BÁO CÁO CUỐI KỲ NLP — bắt đầu từ đây

> **Thư mục này CHỈ chứa hướng dẫn viết báo cáo.**
> **Kết quả thí nghiệm nằm ở `../docs/`** — đừng lẫn hai chỗ.

---

## Bốn tệp, bốn việc

| tệp | trả lời câu hỏi | khi nào đọc |
|---|---|---|
| **`BAO_CAO_CAU_TRUC.md`** | *viết **CÁI GÌ*** — luận điểm hợp nhất, khung `H × κ − D`, 9 mục, 7 hình | **đọc §0 đầu tiên** (1 trang) |
| **`HUONG_DAN_CONG_TAC.md`** | *được phép viết **CON SỐ NÀO*** — ba tầng bằng chứng, bảng số chốt, điều cấm | trước khi gõ con số đầu tiên |
| **`QUY_TRINH_VIET_BAO_CAO.md`** | *làm **THEO THỨ TỰ NÀO*** — 7 bước, phân công song song, đường găng | khi bắt tay vào làm |
| `BAO_CAO.md` | **bản thảo** | chưa có — Bước 1 của quy trình sẽ tạo |

---

## Đọc trong 3 phút

1. **`BAO_CAO_CAU_TRUC.md` §0** — luận điểm một câu của cả báo cáo
2. **`QUY_TRINH_VIET_BAO_CAO.md` Bước 0** — việc cả nhóm phải làm trước khi ai viết gì

Xong hai mục đó là bắt đầu viết được.

---

## Luận điểm một câu *(chép từ `BAO_CAO_CAU_TRUC.md` §0)*

> **Chênh lệch năng lực TẠO RA cơ hội; GIAO THỨC quyết định ta thu hoạch hay phá huỷ nó.**

Bằng chứng hai chiều, **ngược dấu nhau** — và đó chính là điểm hay của báo cáo:
- giao thức **SOÁT/CHỌN**: Solver 1.5B + Verifier 7B = **+14.0đ** MATH, **5/5 fold**
- giao thức **SỬA**: `Δ_ceil = +.0218 − .2392·chênh`, p = **1e-05**, đổi dấu tại `g*` = .091

---

## Ranh giới hai thư mục — **đừng lẫn**

| | `report/` *(đây)* | `../docs/` |
|---|---|---|
| chứa gì | **hướng dẫn viết** | **kết quả thí nghiệm** |
| bao nhiêu tệp | 3 (+ bản thảo) | 38 |
| ai viết | Nguyên | cả ba người |
| có được trích số từ đây không | **không** — số nằm ở `../docs/` và `../results_*/` | có, **theo tầng bằng chứng** |

**Cửa vào của `../docs/`:** `../docs/INDEX.md`

---

## Ba việc đang chờ

1. **Bước 0** của `QUY_TRINH_VIET_BAO_CAO.md` — cả nhóm chốt một câu luận điểm *(chưa làm)*
2. **H99b** và **H100e** đang chạy — xem Bước 6 để biết cách nối vào, và mục nào **bắt buộc** phải sửa
3. **`EFFICIENCY.md`** (Tùng Dương, 210 dòng) — **chỉ có trên nhánh `nguoi3-router`, chưa có trên `main`**.
   Cần cho §5.3. Là nhánh của Tùng Dương nên **chủ nhánh quyết định** có gộp không.
