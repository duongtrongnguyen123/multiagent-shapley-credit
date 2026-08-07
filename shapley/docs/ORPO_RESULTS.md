# ORPO cho Aggregator — kết quả: thắng in-domain nhưng không đạt chuẩn, không chuyển sang task khác

Giai đoạn 2 của vòng ORPO. Tiêu chí đã khoá trước trong `ORPO_AGGREGATOR.md`.

Adapter LoRA (r=16) train trên **428 cặp preference từ MATH train**, eval 5 fold × 30 trên
MATH-500 test (**in-domain**) và GSM8K test (**cross-task** — adapter chưa từng thấy GSM8K).

## MATH — in-domain

| nhánh | acc | Δ vs base | fold cùng dấu |
|---|---|---|---|
| S (Solver một mình) | .4133 | −0.053 | 5/5 |
| agg3_base | .4667 | — | — |
| **agg3_orpo** | **.4933** | **+0.027** | 3/5 |
| **agg3_orpo + fallback** | **.5000** | **+0.033** | 4/5 |
| vote3 | .4733 | +0.007 | 2/5 |
| *oracle (3 ứng viên)* | *.6200* | | |

**Mốc `vote5` = .507.**

## GSM8K — cross-task

| nhánh | acc | Δ vs base | fold |
|---|---|---|---|
| S | .6533 | −0.073 | 4/5 |
| agg3_base | .7267 | — | — |
| **agg3_orpo** | **.7267** | **±0.000** | 0/5 |
| agg3_orpo + fallback | .7333 | +0.007 | 1/5 |
| vote3 | .7000 | −0.027 | 3/5 |
| *oracle* | *.8067* | | |

## Đọc theo tiêu chí đã khoá

| kết quả | kết luận bắt buộc (khoá trước) |
|---|---|
| > vote5 (.507) **và** 5/5 fold | kết quả dương thật |
| > vote3 nhưng ≤ .507 | **thắng cùng ngân sách, thua bỏ phiếu 5 mẫu → kết quả một phần** |
| .467 < x ≤ vote3 | thất bại thực dụng |
| ≤ .467 | không dịch chuyển được hành vi |

**MATH rơi vào hàng 2.** `agg3_orpo_fb` = .5000, vượt `vote3` (.4733) và vượt `agg3_base`
(.4667), nhưng **không đạt** mốc `vote5` = .507, và chỉ 4/5 fold cùng dấu.

Phát biểu trung thực: **ORPO cải thiện Aggregator ở cùng ngân sách 3 mẫu, nhưng vẫn không bằng
việc chỉ cần lấy 5 mẫu rồi bỏ phiếu — vốn miễn phí và không cần train gì.**

Hiệu ứng +3.3 điểm cũng **dưới sàn nhiễu ~5 điểm**, nên chặt chẽ mà nói đây là *"chưa đo được
cải thiện đáng tin"*, không phải *"có cải thiện nhỏ"*.

**GSM8K rơi vào hàng 4** — accuracy y hệt base (.7267 = .7267, 0/5 fold).

## Chỉ số khoá trước: `copies_last`

Đây là lý do phải khoá chỉ số trước khi chạy (bài học H23, xem `ORPO_VS_H23.md`).

| | base | ORPO |
|---|---|---|
| **MATH** `copies_last` | .627 | **.567** ↓ |
| **MATH** `novel` (đáp án ngoài đầu vào) | — | **.307** |
| **GSM8K** `copies_last` | .793 | **.833** ↑ |
| **GSM8K** `novel` | — | .033 |

Trên MATH, recency bias **giảm** (.627 → .567) — đúng hướng mong muốn. Nhưng `novel` tăng vọt
lên **.307**: gần một phần ba số câu, Aggregator xuất ra đáp án **không có trong bất kỳ ứng viên
nào**.

Đối chiếu với đo đạc trước (`ROLE_SPECIALIZATION.md`): Aggregator gốc sinh đáp án ngoài đầu vào
ở 12% số câu MATH và **0 ca nào đúng**. Nếu tỉ lệ đúng vẫn gần 0 thì phần lớn +3.3 điểm **không**
đến từ việc chọn tốt hơn.

## Adapter có thật sự hoạt động không? — có, và rất khác nhau giữa hai task

| | output giống hệt từng ký tự | đáp án trùng nhau |
|---|---|---|
| **MATH** | **3/150 (2%)** | 78/150 (52%) |
| **GSM8K** | **127/150 (85%)** | 139/150 (93%) |

**Trên MATH adapter đổi gần như toàn bộ output** (98% khác). **Trên GSM8K nó gần như không làm
gì** (85% giống hệt từng ký tự).

Ví dụ trên MATH cho thấy nó đổi *kiểu hành vi*, không chỉ đổi lựa chọn:

```
base: "The correct final answer is \(\boxed{(3, \frac{\pi}{2})}\)."
orpo: "To convert the point \((0,3)\) from rectangular to polar coordinates, we use..."
```

Base **chọn** một ứng viên; ORPO **tự giải lại**. Điều này giải thích `novel` = .307 — adapter
học được cách "tự tính" chứ không phải "chọn khéo hơn". Đây là **lối tắt tầm thường** kiểu H23:
mục tiêu là *chọn giữa các ứng viên*, nhưng cách tối ưu hàm mất mát lại là *bỏ qua ứng viên và
giải lại*.

## Kết luận

1. **ORPO không đạt mốc đã khoá.** Trên MATH nó thắng cùng ngân sách (+3.3 điểm so với base)
   nhưng thua `vote5`, và hiệu ứng dưới sàn nhiễu.
2. **Không chuyển sang task khác.** GSM8K: 0/5 fold, output 85% giống hệt base. Adapter train
   trên MATH chỉ tác động trên MATH.
3. **Cơ chế không phải cái ta muốn dạy.** Nó không học chọn đúng hơn — nó học **tự giải lại**
   (`novel` .307, output đổi 98%). Đó là lối tắt của hàm mất mát, không phải giải pháp cho bài
   toán selection.
4. **Bỏ phiếu cơ học vẫn thắng.** `vote5` = .507 > `agg3_orpo_fb` = .500, và không cần train,
   không cần dữ liệu, không cần GPU.

Khớp với kết luận lớn hơn của dự án: mọi can thiệp đều thua một baseline đơn giản hơn hoặc một
model to hơn.

## Vì sao có thể như vậy — và giới hạn

- **428 cặp là ít.** Đã ghi rủi ro này trước khi train. Nhưng thất bại **không phải** kiểu "không
  học được gì" — nó học rất mạnh (output đổi 98%), chỉ là học sai thứ.
- **Trần vốn đã thấp.** Trong 172 ca base chọn sai ở tập train, chỉ **76%** là chọn nhầm ứng viên
  có sẵn; 24% là tự bịa đáp án — ORPO không nhắm được phần đó.
- **Oracle chỉ .620** trên eval này (3 ứng viên), thấp hơn .673 của vòng aggk (5 ứng viên). Với
  3 mẫu thì trần vốn đã hẹp.
- n=150 mỗi task, sàn nhiễu ~5 điểm. Mọi Δ ở đây đều nhỏ hơn thế trừ khoảng cách S↔base.

## Điều đáng làm tiếp nếu quay lại hướng này

Phạt trực tiếp hành vi "tự giải lại": thêm ràng buộc để `chosen` phải là **một trong các ứng
viên** thay vì văn bản tự do. Cách hiện tại vô tình cho phép model thoát khỏi bài toán selection.
