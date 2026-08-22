"""Shared fixtures cho test suite.

Tạo dữ liệu giả lập 16 tổ hợp (2^4 = {P,S,V,A}) với vector đúng/sai theo từng câu,
giữ đúng format mà router.py kỳ vọng khi đọc từ results_<ROUND>/<mask>/preds.json
và summary.json.
"""
import json
import pytest
from pathlib import Path
from itertools import combinations


ROLES = ["P", "S", "V", "A"]


def mask_to_dirname(mask: dict) -> str:
    """Chuyển mask dict → tên thư mục 4-bit (vd PSVA = '1111', chỉ S = '0100')."""
    return "".join("1" if mask[r] else "0" for r in ROLES)


def make_preds(n: int, correct_vec: list[int]) -> list[dict]:
    """Tạo preds.json content: list of {gold, pred, correct}."""
    preds = []
    for i in range(n):
        ok = correct_vec[i]
        preds.append({
            "gold": f"ans_{i}",
            "pred": f"ans_{i}" if ok else f"wrong_{i}",
            "correct": bool(ok),
        })
    return preds


def make_summary(mask: dict, accuracy: float) -> dict:
    """Tạo summary.json content với mask và accuracy."""
    return {
        "mask": mask,
        "accuracy": accuracy,
        "n": 0,  # sẽ được điền sau
    }


@pytest.fixture
def sample_n():
    """Số câu hỏi dùng trong mọi fixture."""
    return 20


@pytest.fixture
def synthetic_results(tmp_path, sample_n):
    """Tạo thư mục results_test/ với 16 tổ hợp, mỗi tổ hợp có preds.json + summary.json.

    Dữ liệu được thiết kế để:
    - Solver (S) một mình đúng ~60% (12/20)
    - Verifier (V) sửa được 3 câu sai → S+V đúng 15/20
    - Aggregator (A) chọn đúng thêm 1 → S+V+A đúng 16/20
    - Planner (P) gần như vô dụng (chỉ giúp 1 câu trong vài tổ hợp)
    - Oracle có thể đạt 18/20 bằng cách chọn tổ hợp tốt nhất cho từng câu
    """
    n = sample_n
    results_dir = tmp_path / "results_test"
    results_dir.mkdir()

    # Tạo vector đúng/sai cho từng câu, cho từng tổ hợp.
    # Quy ước: correct_vec[coalition][question_idx] = 0 hoặc 1
    # Bắt đầu với S một mình: đúng 12/20 câu (0-11 đúng, 12-19 sai)
    s_correct = [1] * 12 + [0] * 8

    # V sửa được câu 12, 13, 14 (S sai → V đúng), nhưng phá câu 0 (S đúng → V sai)
    # S+V: 0 sai, 1-11 đúng, 12-14 đúng, 15-19 sai = 15/20
    sv_correct = [0] + [1] * 11 + [1, 1, 1] + [0] * 5

    # A chọn đúng thêm câu 15 (khi có S+V+A), nhưng phá câu 1
    # S+V+A: 0 sai, 1 sai, 2-11 đúng, 12-14 đúng, 15 đúng, 16-19 sai = 15/20
    # Nhưng S+A (không V): A không đủ context → chỉ đúng = S
    sva_correct = [0, 0] + [1] * 10 + [1, 1, 1] + [1] + [0] * 4

    # P giúp câu 16 trong một số tổ hợp (hiếm)
    p_help = [0] * 16 + [1, 0, 0, 0]

    # Tạo tất cả 16 tổ hợp
    for size in range(5):
        for combo in combinations(ROLES, size):
            mask = {r: (r in combo) for r in ROLES}
            dirname = mask_to_dirname(mask)
            d = results_dir / dirname
            d.mkdir()

            # Tính vector đúng/sai cho tổ hợp này
            if size == 0:
                # Empty coalition: luôn sai
                vec = [0] * n
            else:
                # Bắt đầu với 0
                vec = [0] * n
                # Nếu có S, dùng s_correct làm nền
                if "S" in combo:
                    vec = list(s_correct)
                # Nếu có V và S, dùng sv_correct
                if "S" in combo and "V" in combo:
                    vec = list(sv_correct)
                # Nếu có S, V, A, dùng sva_correct
                if "S" in combo and "V" in combo and "A" in combo:
                    vec = list(sva_correct)
                # Nếu có A nhưng không có V: A chỉ copy S (không thêm gì)
                # Nếu có P: giúp 1 câu
                if "P" in combo and size > 0:
                    for i in range(n):
                        if p_help[i]:
                            vec[i] = 1
                # Nếu chỉ có P hoặc V hoặc A một mình (không S): giải lại, yếu hơn
                if "S" not in combo and size > 0:
                    # Chỉ đúng 5/20 câu (idx 0-4)
                    vec = [1] * 5 + [0] * 15
                    if "P" in combo:
                        for i in range(n):
                            if p_help[i]:
                                vec[i] = 1

            accuracy = sum(vec) / n
            preds = make_preds(n, vec)
            summary = make_summary(mask, accuracy)
            summary["n"] = n

            (d / "preds.json").write_text(json.dumps(preds))
            (d / "summary.json").write_text(json.dumps(summary))

    return results_dir


@pytest.fixture
def trace_data(tmp_path, sample_n):
    """Tạo trace data giả lập (format giống traces_full.json).

    Mỗi item có: i, q, gold, sol, ver, agg, sa, va, aa, s_ok, v_ok, a_ok, len_sol, len_ver, len_agg
    """
    n = sample_n
    traces = []
    for i in range(n):
        s_ok = i < 12  # 12/20 đúng
        v_ok = i < 15 if i > 0 else False  # V phá câu 0, sửa 12-14
        a_ok = i < 16 if i > 1 else False  # A phá câu 1, sửa 15

        traces.append({
            "i": i,
            "q": f"Question {i}",
            "gold": f"ans_{i}",
            "sol": f"Solution {i}" * 10,
            "ver": f"Verification {i}" * 10,
            "agg": f"Aggregation {i}",
            "sa": f"ans_{i}" if s_ok else f"wrong_{i}",
            "va": f"ans_{i}" if v_ok else f"wrong_{i}",
            "aa": f"ans_{i}" if a_ok else f"wrong_{i}",
            "s_ok": s_ok,
            "v_ok": v_ok,
            "a_ok": a_ok,
            "len_sol": 500 + i * 50,
            "len_ver": 600 + i * 30,
            "len_agg": 200 + i * 10,
        })

    trace_dir = tmp_path / "res_ft_test"
    trace_dir.mkdir()
    (trace_dir / "traces_full.json").write_text(json.dumps(traces))
    (trace_dir / "summary.json").write_text(json.dumps({
        "task": "math",
        "n": n,
        "acc_S": 12 / n,
        "acc_V": sum(1 for t in traces if t["v_ok"]) / n,
        "acc_A": sum(1 for t in traces if t["a_ok"]) / n,
    }))
    return trace_dir
