# Nâng chất lượng Judge — khảo sát vote & few-shot

Bối cảnh (`SOLVEJUDGE_MATH.md`): Judge 1.5B binary là điểm nghẽn — MATH prec .52 (39 false-pos),
GSM8K prec .33 (chê sai 70/84 câu đúng). Khảo sát hai biện pháp trên cùng lời giải S1 greedy:

1. **Judge-vote** (`judgevote`): K=3 Judge độc lập (temp 1.0/0.7/0.4) → ngưỡng vote 1/2/3.
2. **Few-shot** (`judgefewshot`): thêm 1 ví dụ lời giải ĐÚNG (→1) + 1 SAI (→0) vào prompt Judge.

n=150 mỗi task. Basline = Judge greedy không vote, không few-shot (chính là Judge trong solvejudge).

## Kết quả

### MATH (S1 acc .407)
| vị trí | prec | rec | tp | fp | fn |
|---|---|---|---|---|---|
| **judge1 (baseline)** | .496 | .984 | 60 | 61 | 1 |
| vote2of3 | .500 | .967 | 59 | 59 | 2 |
| vote3of3 | .509 | .967 | 59 | 57 | 2 |
| few-shot | .518 | .967 | 59 | 55 | 2 |

### GSM8K (S1 acc .64)
| vị trí | prec | rec | tp | fp | fn |
|---|---|---|---|---|---|
| **judge1 (baseline)** | .664 | .927 | 89 | 45 | 7 |
| vote2of3 | .669 | .927 | 89 | 44 | 7 |
| vote3of3 | .669 | .906 | 87 | 43 | 9 |
| few-shot | .648 | .958 | 92 | 50 | 4 |

## Insight

**1. Cả vote lẫn few-shot đều gần như BẤT LỰC — Δ prec ≤ .025 trên cả hai task.**

| | MATH Δprec | GSM8K Δprec | MATH Δrec | GSM8K Δrec |
|---|---|---|---|---|
| vote3of3 | +.013 | +.005 | −.017 | −.021 |
| few-shot | +.022 | −.016 | +.000 | +.031 |

Judge-vote làm sạch **rất ít**: vote3of3 giảm fp (61→57 MATH, 45→43 GSM8K) nhưng cũng giảm rec
(đánh đổi, vì đòi 3/3 đồng thuận thì bỏ lỡ vài câu đúng). Few-shot trên GSM8K chỉ **dịch chuyển
false-type**: bớt 3 fp → thêm 4 fn, rec tăng nhưng prec giảm.

**2. Judge 1.5B không "nhầm lẫn do thiếu calib" — nó CHẠM TRẦN năng lực riêng của nó.**
Vote loại bỏ nhiễu sampling (agreement 0.97 cả hai task — các Judge hầu như đồng thuận rồi),
few-shot không dạy nó phân biệt hơn. Vậy lỗi là **hệ thống**: Judge 1.5B đọc lời giải mà không
kiểm được bước sai (nó chỉ nhìn format/độ dài). Thêm Judge hay vài ví dụ không thêm năng lực.

**3. Không tương tác như kỳ vọng giữa hai biện pháp.**
Giả thuyết "vote sạch nhiễu + few-shot nâng năng lực, cộng lại khả dụng" — nhưng khi mỗi cái chỉ
cho +.01~.02 và nằm dưới sàn nhiễu, tổ hợp cũng không đủ.

## Đối chiếu với hướng đã đo mạnh hơn

Project có **hai hướng cho hiệu quả Judge/verify rõ rệt** mà khảo sát này không chạm tới:
- **Nâng model Judge lên 7B** (RESULTS.md): "Solver 1.5B + Verifier 7B" **+14.0đ trên MATH** — vì
  Judge 7B thực sự giải lại được các bước.
- **Exec-based verification** (H33–H35): `exec3` = oracle@4 chính xác trên code — nhưng rào cản H8
  (exec_success .42 ở 1.5B) chặn trên toán văn bản.

→ **Δprec ≤ .025 từ vote/few-shot cho thấy: không đáng để thêm call vào Judge 1.5B.** Muốn Judge
tốt hơn, hoặc đổi model (7B), hoặc đổi cơ chế (exec).

## Kết luận

Judge-vote và few-shot là **null result**: cả hai nâng prec nhiều nhất +.02 (MATH vote3 / few-shot),
dưới sàn nhiễu ~5 điểm, không đáng thêm call. Điểm rút ra:
- Judge 1.5B **chạm trần năng lực lời giải** — lỗi hệ thống, không phải thiếu calib.
- Nếu muốn Judge tốt hơn thật: **7B hoặc exec**, không phải vote hay few-shot.
- Loop solve-judge vẫn giữ giá trị ở MATH (Judge đủ tốt để dừng sớm) nhưng **không thể vỗ béo Judge
  1.5B bằng vote/few-shot**.

## Giới hạn

- n=150, một lần chạy. Δ đều trong nhiễu nên kết luận đúng là "không phân biệt được", không phải
  "chắc chắn vô dụng" — nhưng đủ để ưu tiên hướng khác.
- Vote K=3 Judge tốn 2 call thêm mỗi vòng; few-shot không tốn thêm call nhưng không giúp.
- Chưa thử vote K lớn hơn (5) hay few-shot nhiều mẫu hơn — nhưng cơ chế (trần năng lực) cho thấy
  không đủ chỗ để cải thiện.