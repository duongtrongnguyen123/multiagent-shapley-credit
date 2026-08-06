# Debate-planner: nhiều planner 1.5B thay cho một planner 7B — DỪNG vì chi phí

Giả thuyết: bottleneck của vai Planner là **năng lực model** (φ_P: −0.014 GSM8K · +0.017
MATH·1.5B · +0.062 MATH·7B). Thay vì mua năng lực bằng 7B (đắt), thử mua bằng **phối hợp** —
để nhiều planner 1.5B tranh luận rồi chốt một kế hoạch.

Kernel: `pipeline/template_debate_math.py`. Kết quả: `results_pdeb/`.

## Thiết kế

Ba chế độ planner, pipeline PSVA đầy đủ, MATH N=300, để **tách hiệu ứng debate khỏi hiệu ứng
sampling** — nếu bỏ qua bước này thì mọi cải thiện đều có thể chỉ do được sample nhiều lần:

| chế độ | planner | số lượt gọi model/câu |
|---|---|---|
| `single` | 1 kế hoạch greedy (baseline, khớp `template_math.py`) | 1 |
| `sampling` | 3 kế hoạch sample (temp 0.7, seed cố định) → judge gộp, **không** phản biện | 4 |
| `debate` | 3 kế hoạch sample → phản biện chéo → mỗi planner tự sửa kế hoạch của mình → judge chốt | **10** |

Cơ chế chống anchoring của nhánh `debate`: planner j **không được nhìn kế hoạch của chính
mình** khi phản biện, và chỉ tự sửa bản của mình dựa trên phản biện từ hai peer — thay vì cả
nhóm cùng hùa theo một kế hoạch tự tin nhưng sai (sycophancy).

## Kết quả

| chế độ | accuracy | thời gian chạy (T4) |
|---|---|---|
| `single` | **0.4467** | 2.5 h |
| `sampling` | **0.4433** | 6.4 h |
| `debate` | **không hoàn thành** | > 11 h, chưa xong |

**`sampling` không hơn `single`** (−0.34 điểm). Chênh lệch này tương đương **1 câu trên 300** và
nằm **sâu dưới sàn nhiễu ~5 điểm** của H13 — kết luận trung thực duy nhất là *"không đo được
khác biệt"*, không phải *"sampling vô ích"*.

Nhánh `debate` **không cho ra dữ liệu nào**: lần chạy đầu bị hủy, lần thứ hai vượt 11 giờ mà
chưa xong. Kernel chỉ ghi file ở dòng cuối cùng nên khi bị cắt thì mất trắng — không có
checkpoint, log cũng không chứa nội dung sinh ra.

## Vì sao dừng

**Chi phí compute không tương xứng với kỳ vọng.** Nhánh `debate` cần **10 lượt gọi model mỗi
câu** — gấp 10 lần baseline và 2.5 lần nhánh `sampling` vốn đã mất 6.4 giờ. Ước tính 10–14 giờ
cho N=300, tức **chạm trần 12 h/kernel của Kaggle**, trên một tài khoản chỉ có 2 slot GPU.

Ba lý do khiến việc chi thêm compute đó khó biện minh:

1. **Bậc thang trung gian đã không cho tín hiệu.** `sampling` là bước rẻ hơn nằm giữa `single` và
   `debate`, và nó không nhích được gì. Nếu ba kế hoạch đa dạng cộng một judge không giúp, thì
   khó kỳ vọng ba vòng phản biện — vẫn cùng một model 1.5B — sẽ giúp.

2. **Sàn nhiễu nuốt mất thứ cần đo.** Ở N=300 với sàn nhiễu ~5 điểm, `debate` phải thắng
   baseline **hơn 5 điểm** thì mới nói được gì. Muốn phát hiện hiệu ứng nhỏ hơn thì phải chạy
   nhiều fold — tức nhân chi phí vốn đã cao nhất lên 5 lần nữa.

3. **Vòng Planner cho thấy đây không phải nút thắt.** Xem
   [`PLANNER_ROUND_RESULTS.md`](PLANNER_ROUND_RESULTS.md): kế hoạch dù chứa sẵn đáp án vẫn giúp
   +6 điểm so với không có kế hoạch, và khi nó dắt Solver đi sai thì Verifier gỡ được 71% số ca.
   Cải thiện *chất lượng kế hoạch* nhắm vào một chỗ mà pipeline vốn đã tự vá phần lớn.

## Giữ lại được gì

- `single` 0.4467 (N=300, MATH) là mốc baseline hữu ích, khớp với v(PSVA) ≈ 0.456 của `results_m1`.
- `sampling` 0.4433: **một kết quả âm sạch** — đa dạng hoá kế hoạch bằng sampling, với model yếu
  trên bài khó, không mua được accuracy. Đứng cạnh kết quả của IDEAS.md rằng không method nào
  thắng base trên GSM8K.
- Mã nguồn ba chế độ vẫn nằm trong repo, chạy lại được nếu sau này có nhiều GPU hơn hoặc muốn
  thử ở 7B.

## Bài học kỹ thuật (đã áp dụng cho các kernel sau)

Kernel dài **phải ghi kết quả từng phần**. `template_debate_math.py` chỉ `json.dump` ở dòng cuối,
nên hơn 11 giờ tính toán bốc hơi khi bị cắt. Các kernel viết sau vòng này
(`fullpipe_rescue_kernel.py`, `fewshot_folds_kernel.py`) đã lưu trace đầy đủ theo từng câu —
nhưng vẫn ghi ở cuối, nên bài học đầy đủ là: **ghi theo checkpoint, không chỉ theo từng câu.**

## Nếu quay lại hướng này

Chạy ở **N nhỏ (100–150)** trước để xem có tín hiệu không, thay vì N=300 ngay. Và ghi kết quả
sau mỗi fold để một lần bị cắt không xoá sạch mọi thứ.
