# Bảng master — Shapley theo vai trò × cấu hình

| Vai trò | GSM8K·1.5B | MATH·1.5B | MATH·7B (nâng chính vai đó) |
|---|---|---|---|
| **Planner** | -0.014 | +0.017 | +0.062 |
| **Solver** | +0.252 | +0.144 | +0.305 |
| **Verifier** | +0.252 | +0.144 | +0.318 |
| **Aggregator** | +0.190 | +0.150 | +0.319 |

*(GSM8K·1.5B: N=1319. MATH·1.5B: N=500. MATH·7B: mỗi ô = φ của vai trò đó khi nó dùng
7B (các vòng mA/mV/mP), so trên cùng N=300; ô '—' là vòng chưa chạy xong.)*

**RQ2 (thứ hạng đảo theo độ khó):** Verifier ngang Solver & dẫn đầu ở GSM8K, nhưng ở MATH
**Aggregator lên #1**. **RQ4 (nhạy năng lực):** trên MATH, nâng Aggregator lên 7B làm φ của
nó hơn gấp đôi (+0.152 → +0.319) — Aggregator là vai nhạy năng lực nhất ở bài khó, y như
Verifier ở bài dễ (GSM8K).
