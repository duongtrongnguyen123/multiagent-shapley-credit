# Báo cáo cuối kỳ NLP — Tài liệu hướng dẫn

Thư mục `report/` chỉ chứa **tài liệu hướng dẫn viết báo cáo**.
Kết quả thí nghiệm nằm ở thư mục `../docs/`. Không nên dùng lẫn hai thư mục này.

---

## Bốn tài liệu

| Tài liệu | Trả lời câu hỏi | Thời điểm cần đọc |
|---|---|---|
| `BAO_CAO_CAU_TRUC.md` | **Viết nội dung gì** — luận điểm chính, khung lý thuyết, bố cục 9 chương, danh sách hình | Đọc mục §0 trước tiên (khoảng một trang) |
| `HUONG_DAN_CONG_TAC.md` | **Được phép trích dẫn số liệu nào** — ba mức độ tin cậy, bảng số liệu đã chốt, các phát biểu cần tránh | Trước khi viết con số đầu tiên |
| `QUY_TRINH_VIET_BAO_CAO.md` | **Thực hiện theo trình tự nào** — bảy bước, phân công song song, đường găng | Khi bắt đầu viết |
| `MACH_DAN_DAT.md` | **Các thí nghiệm dẫn tới nhau như thế nào** — mạch 10 bước, dùng khi viết phần thân theo dạng survey | Trước khi viết §5 |
| `CAU_HOI_THAO_LUAN.md` | **Những gì cả nhóm cần thống nhất** — 11 câu hỏi chia ba nhóm, kèm mức độ ưu tiên | Bước 0 và trong lúc viết |
| **`THUAT_NGU.md`** | **Định nghĩa thuật ngữ và ký hiệu** — `oracle@k`, `maj@k`, `A`/`B`/`C`, `H`/`κ`/`D`, vai trò, độ tin cậy | Tra bất cứ lúc nào; đưa cho người đọc ngoài nhóm |
| **`BAO_CAO.md`** | **BẢN THẢO v0.1** — §1, §3, §5–§9 đã viết; §2 chờ Đức, §4 chờ Tùng Dương | Đọc và sửa trực tiếp |

---

## Cách bắt đầu

1. Đọc mục **§0 của `BAO_CAO_CAU_TRUC.md`** — luận điểm chính của toàn bộ báo cáo.
2. Đọc **`MACH_DAN_DAT.md`** — mạch dẫn dắt giữa các thí nghiệm, tức nội dung chính của phần thân.
3. Đọc **Bước 0 của `QUY_TRINH_VIET_BAO_CAO.md`** — phần việc cả nhóm cần thống nhất trước khi
   bất kỳ ai bắt đầu viết.
4. Xem **`CAU_HOI_THAO_LUAN.md`**, trả lời trước hai câu **A1** và **B1**.

Hoàn thành hai mục trên là có thể bắt đầu.

---

## Luận điểm chính

> **Chênh lệch năng lực giữa hai model tạo ra cơ hội cải thiện; giao thức phối hợp quyết định
> cơ hội đó được khai thác hay bị phá huỷ.**

Luận điểm được chống đỡ bởi hai nhóm bằng chứng **ngược dấu nhau**. Chính sự ngược dấu này là
nội dung đáng chú ý nhất của báo cáo:

- Với giao thức **tuyển chọn** (verifier): Solver 1.5B kết hợp Verifier 7B đạt **+14,0 điểm** trên
  MATH, nhất quán trên **cả 5 fold**.
- Với giao thức **sửa chữa** (repair): `Δ_ceil = +0,0218 − 0,2392 × (chênh lệch năng lực)`,
  p = 1e-05, đổi dấu tại `g*` = 0,091.

---

## Phân biệt hai thư mục

| | `report/` (thư mục này) | `../docs/` |
|---|---|---|
| Nội dung | Hướng dẫn viết báo cáo | Tài liệu kết quả thí nghiệm |
| Số lượng tệp | 7 (kể cả bản thảo) | 39 |
| Người biên soạn | Nguyên | Cả nhóm |
| Trích số liệu từ đây | Không. Số liệu nằm ở `../docs/` và `../results_*/` | Có, theo đúng mức độ tin cậy tương ứng |

Điểm vào của thư mục kết quả: `../docs/INDEX.md`

**Người đọc chưa quen thuật ngữ nên bắt đầu ở `THUAT_NGU.md`** — đặc biệt mục 1 (`greedy`,
`maj@k`, `oracle@k`) vì ba khái niệm đó chi phối cách đọc gần như mọi bảng trong báo cáo.

---

## Các việc còn tồn đọng

1. **Bước 0** trong `QUY_TRINH_VIET_BAO_CAO.md`: cả nhóm thống nhất một câu luận điểm. Chưa thực hiện.
2. **Chuẩn thống kê đang được đề xuất sửa** — xem `CAU_HOI_THAO_LUAN.md` nhóm **E**: ngưỡng sàn
   nhiễu 5 điểm được suy ra cho phép đo đơn lẻ nhưng đang áp cho kết quả 5 fold; ngưỡng đúng
   khoảng 3,3 điểm. Cần cả nhóm quyết.
3. Thí nghiệm **H100e** chưa hoàn tất (thiếu 2 trên 6 ô đo). Xem Bước 6 để biết cách bổ sung kết quả
   và những mục bắt buộc phải sửa lại.
4. Tệp `EFFICIENCY.md` (Tùng Dương, 210 dòng) hiện chỉ có trên nhánh `nguoi3-router`, chưa có trên
   `main`. Tài liệu này cần cho mục §5.3. Việc hợp nhất nhánh thuộc quyền quyết định của tác giả nhánh.

---

## Quy ước thuật ngữ

Báo cáo viết bằng tiếng Việt. Các thuật ngữ sau **giữ nguyên tiếng Anh**, vì chưa có bản dịch thống
nhất trong tài liệu tiếng Việt hoặc vì việc dịch làm giảm tính chính xác:

`prompt` · `pipeline` · `baseline` · `benchmark` · `fold` · `bootstrap` · `greedy decoding` ·
`solver` · `verifier` · `planner` · `aggregator` · `router` · `artifact` · `self-consistency` ·
`debate` · `Shapley` · `McNemar` · `VOID`

Các thuật ngữ sau **dịch sang tiếng Việt** và dùng nhất quán trong toàn bộ báo cáo:

| Tiếng Anh | Tiếng Việt |
|---|---|
| pre-registration | tiền đăng ký |
| locked interpretation table | bảng diễn giải đã khoá |
| quality gate | điều kiện hợp lệ |
| headroom | dư địa |
| capability gap | chênh lệch năng lực |
| repair protocol | giao thức sửa chữa |
| select protocol | giao thức tuyển chọn |
| exposure | mức tiếp xúc với artifact |
| noise floor | sàn nhiễu |
| hash seal | niêm phong bằng hash |
| oracle gate | cổng lý tưởng |
| capability asymmetry | bất đối xứng năng lực |
