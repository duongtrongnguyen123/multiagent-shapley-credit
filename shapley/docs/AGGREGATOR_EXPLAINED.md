# Aggregator làm gì? — prompt, input, và output thật

Đọc từ trace thật của `rescue-fullpipe-gsm8k` (150 câu, `results_rescue/gsm8k/traces.json`).

## 1. Prompt

```python
AGG_SYS = ("You are given a math problem and one or more candidate solutions. "
           "Decide the correct final answer by re-checking and majority. "
           "End with 'The answer is <number>'.")
```
Bản MATH giống hệt, chỉ đổi phần đuôi thành `Put the final answer in \boxed{}`.

## 2. Nó nhận gì

```python
agg = gen(AGG_SYS, f"{q}\n\nCandidate 1:\n{sol}\n\nCandidate 2:\n{ver}")
```

Aggregator nhận **đề bài + hai lời giải ứng viên**:
- Candidate 1 = lời giải của **Solver**
- Candidate 2 = lời giải của **Verifier**

Nó **không** nhận kế hoạch, không biết ứng viên nào đến từ vai nào, và không được cho biết
Candidate 2 là bản đã soát lại của Candidate 1. Với nó, đây chỉ là hai lời giải ngang hàng.

Nhiệm vụ trên giấy: *"quyết định đáp án đúng bằng cách kiểm lại và lấy đa số"*. Nhưng với đúng
**hai** ứng viên thì "đa số" là vô nghĩa — hai phiếu không bao giờ tạo ra đa số. Đây là một khiếm
khuyết thiết kế đáng ghi nhận: prompt yêu cầu một thứ mà cấu hình không cung cấp được.

## 3. Thực tế nó làm gì (150 câu GSM8K)

| hành vi | số câu |
|---|---|
| đáp án **trùng Verifier** | 141/150 (**94%**) |
| đáp án trùng Solver | 104/150 (69%) |
| đáp án **khác cả hai** | 3/150 (2%) |

Khi hai ứng viên **bất đồng** (50/150 câu):

| A chọn ai | số câu |
|---|---|
| chọn **Verifier** | **43** |
| chọn Solver | 6 |
| tự đưa đáp án khác | 1 |

**Aggregator gần như luôn theo Candidate 2 (Verifier) — 43/50 lần khi có bất đồng.**

Nó không thực sự "kiểm lại rồi quyết định"; nó **lấy ứng viên cuối cùng**. Hành vi này khớp với
xu hướng recency bias của model nhỏ: cái đọc sau cùng có trọng số lớn nhất.

Hệ quả: `A_gain` +0.007 (xem `VERIFIER_RESCUE.md`) — Aggregator gần như là **lớp đi qua**
(pass-through). Điều này khớp với `fc6f02c` của dự án: *"only 2 of 4 agents actually compute:
planner and verifier generate, solver and aggregator pass through."*

Chuyển tiếp trên 150 câu: cứu **4** · phá **3** · giữ nguyên đúng 101 · bỏ lỡ 42.

## 4. Ca nó CỨU (câu 3, gold 540)

Đề: *"James runs 3 sprints 3 times a week, 60 meters each. Total meters per week?"*

```
Candidate 1 (Solver)  ->  "The answer is 540."                    ĐÚNG
Candidate 2 (Verifier) ->  60 × 3 = 180 meters/week
                           "Therefore, the answer is 180."        SAI
Aggregator             ->  "The answer is 540."                   ĐÚNG
```

Verifier bỏ sót một phép nhân (3 sprint × 3 lần/tuần × 60m), Aggregator quay lại chọn Candidate 1.
Đây đúng là việc ta mong nó làm — **và nó chỉ làm được 4 lần trên 150 câu**.

## 5. Ca nó PHÁ (câu 4, gold 20)

Đề: bài về Wendi cho gà ăn.

```
Candidate 1 (Solver)  ->  "The answer is 20."                     ĐÚNG
Candidate 2 (Verifier) ->  "...we cannot determine the exact amount needed
                            for the final meal.
                            Final Answer: The answer is not provided based
                            on the available information."         KHÔNG có đáp án
Aggregator             ->  "The answer is not provided based on the
                            available information."                SAI
```

**Cả hai ứng viên đều không sai về mặt số học** — Solver ra 20 (đúng), Verifier thì từ chối trả
lời. Aggregator lẽ ra chỉ cần lấy ứng viên **có** đáp án. Nhưng nó chép nguyên câu từ chối của
Candidate 2, biến một lời giải đúng thành **không có đáp án nào**.

Đây là dạng hỏng đáng chú ý nhất: Aggregator không cần *tính* gì để tránh nó — chỉ cần nhận ra
một ứng viên trống. Nó vẫn hỏng vì hành vi thật của nó là **chép cái đọc sau cùng**, không phải
so sánh.

## 6. Tóm tắt

| | |
|---|---|
| **Trên giấy** | kiểm lại các ứng viên, lấy đa số, chốt đáp án đúng |
| **Thực tế** | chép Candidate 2 trong 94% số câu; khi bất đồng thì theo Verifier 43/50 lần |
| **Đóng góp** | cứu 4, phá 3 trên 150 câu → `A_gain` +0.007, không phân biệt được với 0 |
| **Khiếm khuyết thiết kế** | prompt bảo "lấy đa số" nhưng chỉ có 2 ứng viên — không bao giờ có đa số |

Điều này giải thích vì sao trong bảng Shapley gốc, Aggregator đứng #1 trên MATH (+0.148): ở đó
nó nhận **nhiều** ứng viên hơn nên "chọn lọc" có ý nghĩa. Còn trong pipeline nối tiếp chỉ có
S và V, nó thoái hoá thành một lớp sao chép.

**Phép thử tự nhiên tiếp theo**: cho Aggregator ≥3 ứng viên độc lập (self-consistency) rồi đo
lại. Dự án đã có kết quả liên quan — `maj@8` được +10 điểm trên MATH 1.5B — cho thấy khi có đủ
ứng viên để bỏ phiếu thật thì cơ chế này mới hoạt động.
