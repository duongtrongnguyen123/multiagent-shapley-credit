#!/usr/bin/env python3
"""NIÊM PHONG kết quả: ghi hash của artifact NGAY khi tải về, TRƯỚC khi đọc số.

Vì sao cần (kiểm định độc lập #161 chỉ ra):
  Dự án nhiều lần viết *"sửa đổi commit lúc HH:MM:SS TRƯỚC khi tôi mở delta — dấu thời gian git
  kiểm được"*. **Điều đó KHÔNG kiểm được.** Git chỉ chứng minh sửa đổi có trước lúc VIẾT BÁO CÁO,
  không chứng minh nó có trước lúc ĐỌC. Và `res_*/` bị `.gitignore` chặn nên artifact không hề
  nằm trong lịch sử.

Cách dùng (đúng thứ tự này):
    1. kaggle kernels output ... -p results_H99
    2. python deploy/seal_results.py results_H99      <-- niêm phong + commit NGAY
    3. (nếu cần) commit sửa đổi đăng ký trước
    4. CHỈ SAU ĐÓ mới đọc số

Niêm phong ghi vào docs/RESULT_SEALS.md: đường dẫn, kích thước, sha256, thời điểm.
Ai cũng kiểm lại được bằng `sha256sum`; và thứ tự commit trong git trở thành bằng chứng THẬT
rằng artifact đã tồn tại ở dạng đó trước khi bất kỳ diễn giải nào được viết.

KHÔNG in nội dung file — chỉ hash. Niêm phong không được phép làm lộ số.
"""
import hashlib, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEALS = ROOT / "docs" / "RESULT_SEALS.md"

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv) < 2:
        sys.exit("dung: python deploy/seal_results.py <thu_muc_ket_qua> [thu_muc_khac ...]")
    stamp = time.strftime("%Y-%m-%d %H:%M:%S %z")
    lines = []
    for d in sys.argv[1:]:
        dp = Path(d)
        if not dp.is_dir():
            print(f"  bo qua {d}: khong phai thu muc"); continue
        files = sorted(f for f in dp.iterdir() if f.is_file())
        if not files:
            print(f"  bo qua {d}: rong"); continue
        lines.append(f"\n### `{dp.name}` — niêm phong {stamp}\n")
        lines.append("| tệp | bytes | sha256 |")
        lines.append("|---|---|---|")
        for f in files:
            lines.append(f"| `{f.name}` | {f.stat().st_size} | `{sha256(f)}` |")
            print(f"  niem phong {f}")
    if not lines:
        sys.exit("khong co gi de niem phong")
    hdr = ""
    if not SEALS.exists():
        hdr = ("# Niêm phong kết quả (hash ghi TRƯỚC khi đọc số)\n\n"
               "> Mỗi mục dưới đây được ghi **ngay khi tải artifact về**, **trước** khi bất kỳ con số nào\n"
               "> được đọc hay diễn giải. Kiểm lại bằng `sha256sum <tệp>`.\n"
               "> Lý do tồn tại: xem `deploy/seal_results.py` và kiểm định độc lập #161.\n")
    with open(SEALS, "a", encoding="utf-8") as f:
        f.write(hdr + "\n".join(lines) + "\n")
    print(f"\nda ghi vao {SEALS.relative_to(ROOT)} — HAY COMMIT NGAY, TRUOC KHI DOC SO.")

if __name__ == "__main__":
    main()
