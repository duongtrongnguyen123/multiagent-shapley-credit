#!/usr/bin/env python3
"""Sinh nhãn Execution Fidelity (F) từ plan của Planner.

F = 1 nếu "con số cuối cùng" xuất hiện trong plan của Planner bằng đáp án
(pred) mà Solver đưa ra cho cùng câu hỏi; ngược lại F = 0. Đây là proxy O(1)
dùng cho routing policy: "Solver trung thành với plan -> bỏ qua Verifier".

Cách dùng:
  ROUND=m1 python analysis/extract_fidelity.py

Dữ liệu vào (có thể trỏ bằng env):
  ROUND : round kết quả (mặc định m1)
  PLANS : file JSON plan theo từng câu. Chấp nhận 2 dạng:
            - list chuỗi:  ["plan câu 0", "plan câu 1", ...]
            - list dict:   [{"plan": "...", "pred": "..."}, ...]
            ("pred" tùy chọn; nếu thiếu sẽ lấy từ results_<round>/1111/preds.json,
             tức đáp án Solver của tổ hợp đầy đủ — cùng thứ tự câu)
  OUT   : nơi ghi nhãn (mặc định results_summary/fidelity_<round>.json)

Kết quả ghi: {"round": ..., "n": ..., "labels": [0/1, ...]} — căn theo INDEX
câu hỏi nên dùng chung được cho mọi tổ hợp trong results_<round>/ (các template
hiện tại chạy cùng N câu, cùng thứ tự).

Lưu ý: "con số cuối cùng" được hiểu theo nghĩa đen (số xuất hiện sau cùng
trong văn bản plan). Với MATH, prompt dặn Planner KHÔNG được tính đáp án, nên
nhóm F=1 có thể rất nhỏ — đó là tín hiệu thật của dữ liệu, không phải lỗi.
"""
import os, re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUND = os.environ.get("ROUND", "m1")
PLANS = Path(os.environ.get("PLANS", ROOT / "results_summary" / f"plans_{ROUND}.json"))
OUT = Path(os.environ.get("OUT", ROOT / "results_summary" / f"fidelity_{ROUND}.json"))
RES = ROOT / (f"results_{ROUND}" if ROUND != "r1" else "results")
SOLVER_CID = os.environ.get("SOLVER_CID", "1111")

NUM = re.compile(r"-?\d+(?:\.\d+)?")


def last_number(text):
    """Con số cuối cùng xuất hiện trong text (nghĩa đen, không bóc LaTeX)."""
    if not text:
        return None
    nums = NUM.findall(text)
    return nums[-1] if nums else None


def main():
    if not PLANS.exists():
        raise SystemExit(
            f"không tìm thấy {PLANS}.\n"
            f"  -> Chạy lại kernel {SOLVER_CID} (tổ hợp đầy đủ) có log plan của Planner, "
            f"dump plan theo thứ tự câu vào {PLANS.name} rồi chạy lại script này.")
    data = json.loads(PLANS.read_text())
    recs = [{"plan": x} if isinstance(x, str) else x for x in data]
    n = len(recs)

    preds_1111 = None

    def solver_pred(i, rec):
        p = rec.get("pred")
        if p is not None:
            return p
        nonlocal preds_1111
        if preds_1111 is None:
            pj = RES / SOLVER_CID / "preds.json"
            if not pj.exists():
                raise SystemExit(
                    f"{PLANS.name} không kèm 'pred' và không tìm thấy {pj}.\n"
                    f"  -> Dump cả pred vào {PLANS.name}, hoặc đợi kết quả {SOLVER_CID} về.")
            preds_1111 = [r["pred"] for r in json.loads(pj.read_text())]
            if len(preds_1111) != n:
                raise SystemExit(f"{pj} có {len(preds_1111)} câu != {n} câu trong {PLANS.name}")
        return preds_1111[i]

    labels, n_f1 = [], 0
    for i, rec in enumerate(recs):
        ln = last_number(rec.get("plan"))
        pred = solver_pred(i, rec)
        f = 0
        if ln is not None and pred is not None:
            try:
                f = int(abs(float(ln) - float(pred)) < 1e-6)
            except (ValueError, TypeError):
                f = 0
        labels.append(f)
        n_f1 += f

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"round": ROUND, "n": n, "labels": labels}, indent=2))
    print(f"F=1 (trung thành): {n_f1:4d}/{n}  ({n_f1 / n:.1%})")
    print(f"F=0 (lệch)       : {n - n_f1:4d}/{n}")
    print(f"đã ghi {OUT}")


if __name__ == "__main__":
    main()
