# Bảng master — Shapley theo vai trò × cấu hình

| Vai trò | GSM8K·1.5B | MATH·1.5B | MATH·7B* |
|---|---|---|---|
| **Planner** | -0.014 | +0.017 | — |
| **Solver** | +0.252 | +0.144 | — |
| **Verifier** | +0.252 | +0.144 | — |
| **Aggregator** | +0.190 | +0.150 | — |

*(GSM8K·1.5B từ N=1319; MATH·1.5B từ N=500, chấm sympy. Cột 7B điền khi mA/mV/mP xong.)*

**Đọc nhanh (RQ2 — thứ hạng đảo theo độ khó):** Verifier ngang Solver và dẫn đầu trên
GSM8K, nhưng trên MATH thì **Aggregator vươn lên #1**, Verifier tụt ngang Solver; Planner
từ đóng-góp-âm (GSM8K) sang ~trung tính (MATH).
