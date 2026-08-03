# Phân tích trace bằng NLP — vượt khỏi "chỉ prompting"

Repo đo đóng góp vai trò bằng **bật/tắt role + Shapley** — text sinh ra chỉ là input/output,
*không được model NLP phân tích*. Lớp này thêm phần NLP thật: **đọc và học từ NỘI DUNG ngôn
ngữ của trace** để quy đóng góp cho từng *câu/lượt* dựa trên quan hệ ngữ nghĩa và hành vi hội
thoại. Shapley trở thành *cơ chế tổng hợp*, không phải toàn bộ method.

## Ba lớp (đã có script + pilot)

| Lớp | Script | Ý tưởng |
|---|---|---|
| Novelty (embedding) | `analysis/trace_novelty.py` | turn 'mới' hay chỉ paraphrase (1 − cosine) |
| NLI (quan hệ) | `analysis/trace_nli.py` | Solver↔Verifier: mâu thuẫn / kéo theo / trung tính |
| **Learned credit critic** | `analysis/credit_critic.py` | model đọc transcript → dự đoán đúng/sai; MASK từng message → ΔP = credit |

## Kết quả pilot (40 trace GSM8K, Qwen2.5-1.5B)

**1. Novelty thô — thất bại có ích:** `corr(novelty, đổi-đáp-án) = −0.16` (SAI hướng). Verifier
*luôn* giải lại nên luôn "novel"; novelty bị **confound bởi độ dài**. ⇒ embedding thô không đủ.

**2. NLI — đúng hướng nhưng yếu ở ca khó:**

| Nhóm Verifier | n | mâu thuẫn | kéo theo | trung tính |
|---|---|---|---|---|
| GIỮ (đồng ý) | 24 | 2 | **15** | 7 |
| SỬA (fix) | 5 | **3** | 2 | 0 |
| PHÁ (break) | 3 | **0** | 1 | 2 |

NLI bắt tốt "đồng ý" (kéo-theo ↔ GIỮ) và "sửa" (mâu-thuẫn), nhưng **hỏng ở "phá" (0/3)** —
NLI off-the-shelf không giỏi so hai lời giải toán DÀI nhiều bước.

## Kết luận thiết kế (motivation cho contribution chính)
Công cụ NLP *có sẵn* (embedding, NLI) **không đủ** cho trace agent-toán:
- embedding thô → confound bởi verbosity;
- NLI tổng quát → bỏ sót "phá" tinh vi.

⇒ **Đóng góp chính = train một *credit critic* trên chính trace mình sinh** (có nhãn đúng/sai
từ gold), rồi mask-message đo Δ. Đây là phần "học từ nội dung ngôn ngữ" — có động lực thực
nghiệm, không phải thêm cho có.

## Việc cần: scale trace generation
Pilot chỉ 40 trace (3 phá, 5 sửa) → noisy. Cần **≥150–300 trace** (Kaggle: `trace_kernel`,
GSM8K nhanh + MATH) để critic đáng tin. Sinh trace = GPU (Kaggle); phân tích = CPU (local).
