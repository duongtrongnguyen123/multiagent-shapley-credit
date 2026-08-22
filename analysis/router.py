#!/usr/bin/env python3
"""analysis/router.py — Router chọn tổ hợp vai trò theo câu để tối ưu accuracy/compute.

RQ4: Tận dụng biến thiên theo câu để chạy rẻ hơn được không?

Ba chiến lược được đánh giá:
  1. Oracle (trần trên)   — mỗi câu chọn tổ hợp rẻ nhất giải đúng; không quan sát được
                            trong thực tế nhưng cho biết khoảng trống tối đa.
  2. Consensus router     — chạy S+V; nếu đồng thuận → dừng; nếu bất đồng → chạy A.
                            Cost trung bình: 2–3 calls/question (so với 4 cho full pipeline).
  3. Static pipeline      — luôn chạy cùng một tổ hợp (vd P→S→V→A = 4 calls).

Pareto: vẽ accuracy vs #model-calls cho cả 16 tổ hợp + router + oracle.

Yêu cầu dữ liệu:
  - results_<ROUND>/<mask>/preds.json   — list of {gold, pred, correct}
  - results_<ROUND>/<mask>/summary.json — {mask: {P:bool,...}, accuracy: float, n: int}
  <mask> là 4-bit PSVA (vd 1111 = đầy đủ, 0100 = chỉ Solver).

Fallback: nếu không có 16 tổ hợp, dùng trace data (res_ft_*/traces_full.json)
  với s_ok, v_ok, a_ok để tính router trên pipeline đầy đủ.

Chạy:
  ROUND=m1 python analysis/router.py                    # dùng results_m1/
  TRACE=res_ft_m15 python analysis/router.py            # dùng trace fallback
  python analysis/router.py                              # demo với dữ liệu có sẵn

Output:
  - In bảng so sánh: Solver / Full pipeline / Router / Oracle
  - Ghi results_summary/router_results.json
"""
from __future__ import annotations

import json
import os
import sys
import io
import math
import statistics
from pathlib import Path
from itertools import combinations
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# HẰNG SỐ & CẤU HÌNH
# ─────────────────────────────────────────────────────────────────────────────

#: 4 vai trò trong pipeline
ROLES = ["P", "S", "V", "A"]

#: Tên hiển thị
NAMES = {"P": "Planner", "S": "Solver", "V": "Verifier", "A": "Aggregator"}

#: Cost model: mỗi vai = 1 lần gọi model. Cost của tổ hợp = số vai hoạt động.
#: frozenset → int
ROLE_COST: dict[frozenset, int] = {}

for _size in range(len(ROLES) + 1):
    for _combo in combinations(ROLES, _size):
        _fs = frozenset(_combo)
        ROLE_COST[_fs] = len(_fs)

#: Thứ tự vai để in
ROLE_ORDER = {r: i for i, r in enumerate(ROLES)}


def _coalition_label(fs: frozenset) -> str:
    """Chuyển frozenset thành chuỗi dễ đọc (vd {S,V} → 'SV')."""
    return "".join(sorted(fs, key=lambda r: ROLE_ORDER[r])) or "∅"


# ─────────────────────────────────────────────────────────────────────────────
# 1. COALITION DATA — Tải dữ liệu 16 tổ hợp
# ─────────────────────────────────────────────────────────────────────────────

class CoalitionData:
    """Tải và quản lý vector đúng/sai per-question cho 16 tổ hợp.

    Mỗi tổ hợp (coalition) là một tập con của {P,S,V,A}. Với mỗi tổ hợp,
    ta có một vector [0/1, 0/1, ...] cho biết câu thứ i có được giải đúng
    hay không khi chỉ bật các vai trong tổ hợp đó.

    Attributes:
        results_dir     — đường dẫn thư mục results_<ROUND>/
        correctness     — dict {frozenset → list[int]}, mỗi list dài n_questions
        accuracy        — dict {frozenset → float}, accuracy = mean(correctness)
        n_questions     — số câu hỏi (phải đồng nhất giữa mọi tổ hợp)
    """

    def __init__(self, results_dir: Path | str):
        """Khởi tạo từ thư mục results.

        Args:
            results_dir: thư mục chứa các sub-dir <mask>/ với preds.json + summary.json
        """
        self.results_dir = Path(results_dir)
        self.correctness: dict[frozenset, list[int]] = {}
        self.accuracy: dict[frozenset, float] = {}
        self.n_questions: int = 0

        self._load()

    def _load(self):
        """Quét thư mục results_dir, tải preds.json + summary.json cho mỗi tổ hợp."""
        if not self.results_dir.exists():
            return

        for d in sorted(self.results_dir.iterdir()):
            if not d.is_dir():
                continue

            preds_path = d / "preds.json"
            summary_path = d / "summary.json"
            if not preds_path.exists() or not summary_path.exists():
                continue

            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                preds = json.loads(preds_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                continue

            # Trích mask từ summary → frozenset key
            mask = summary.get("mask", {})
            if not isinstance(mask, dict):
                continue
            key = frozenset(r for r in ROLES if mask.get(r, False))

            # Trích vector đúng/sai từ preds
            vec = [1 if p.get("correct", False) else 0 for p in preds]
            self.correctness[key] = vec
            self.accuracy[key] = sum(vec) / len(vec) if vec else 0.0

        # Kiểm tra tính nhất quán về số câu hỏi
        lengths = {len(v) for v in self.correctness.values()}
        if len(lengths) > 1:
            raise ValueError(
                f"Inconsistent question counts across coalitions: {lengths}. "
                f"All coalitions must have the same number of questions."
            )
        if lengths:
            self.n_questions = lengths.pop()

    def __len__(self) -> int:
        """Số tổ hợp đã tải."""
        return len(self.correctness)

    def __repr__(self) -> str:
        return f"CoalitionData({len(self)} coalitions, n={self.n_questions})"


# ─────────────────────────────────────────────────────────────────────────────
# 2. ORACLE — Trần trên: chọn tổ hợp tốt nhất cho từng câu
# ─────────────────────────────────────────────────────────────────────────────

class Oracle:
    """Tính oracle accuracy — trần trên khi biết trước câu nào đúng với tổ hợp nào.

    Cho mỗi câu, chọn tổ hợp RẺ NHẤT (ít vai nhất) giải đúng câu đó.
    Nếu không tổ hợp nào đúng → chọn tổ hợp rẻ nhất (empty, cost=0).

    Đây là trần trên không đạt được trong thực tế (cần biết đáp án trước),
    nhưng cho biết khoảng trống tối đa mà router có thể khai thác.

    Attributes:
        data        — CoalitionData
        accuracy    — oracle accuracy (0–1)
        choices     — list[frozenset], tổ hợp được chọn cho từng câu
        avg_cost    — cost trung bình per-question
    """

    def __init__(self, data: CoalitionData):
        self.data = data
        self.choices: list[frozenset] = []
        self.accuracy: float = 0.0
        self.avg_cost: float = 0.0

        if data.n_questions == 0 or len(data) == 0:
            return

        self._compute()

    def _compute(self):
        """Tính oracle choices, accuracy, và avg_cost."""
        n = self.data.n_questions
        total_correct = 0
        total_cost = 0

        for i in range(n):
            # Tìm tất cả tổ hợp đúng câu i, sắp xếp theo cost tăng dần
            correct_coalitions = [
                key for key, vec in self.data.correctness.items()
                if vec[i] == 1
            ]

            if correct_coalitions:
                # Chọn tổ hợp rẻ nhất (ít vai nhất) trong các tổ hợp đúng
                best = min(correct_coalitions, key=lambda k: ROLE_COST[k])
                total_correct += 1
            else:
                # Không tổ hợp nào đúng → chọn empty (cost=0, sai)
                best = frozenset()

            self.choices.append(best)
            total_cost += ROLE_COST[best]

        self.accuracy = total_correct / n
        self.avg_cost = total_cost / n

    def summary(self) -> dict:
        """Trả về tóm tắt oracle."""
        return {
            "accuracy": round(self.accuracy, 4),
            "avg_cost": round(self.avg_cost, 2),
            "n_questions": self.data.n_questions,
            "strategy": "oracle",
        }

    def __repr__(self) -> str:
        return f"Oracle(acc={self.accuracy:.4f}, cost={self.avg_cost:.2f})"


# ─────────────────────────────────────────────────────────────────────────────
# 3. CONSENSUS ROUTER — Router heuristic dựa trên độ đồng thuận
# ─────────────────────────────────────────────────────────────────────────────

class ConsensusRouter:
    """Router heuristic: dùng tín hiệu đồng thuận giữa S và V để quyết định có chạy A.

    Chiến lược 2-stage:
      Stage 1: Luôn chạy Solver (S) + Verifier (V) → cost = 2
      Stage 2: Nếu S và V ĐỒNG THUẬN (cùng đáp án) → dùng đáp án S, không chạy A
               Nếu S và V BẤT ĐỒNG → chạy Aggregator (A) → cost = 3

    Trong offline analysis (có 16 tổ hợp), ta mô phỏng:
      - "S và V đồng thuận" = S và V cùng đúng HOẶC cùng sai
        (trong thực tế, ta so sánh đáp án, không biết đúng/sai)
      - Khi đồng thuận: dùng tổ hợp {S} (cost=1, nhưng đã chạy V nên cost=2)
      - Khi bất đồng: dùng tổ hợp {S,V,A} (cost=3)

    Lưu ý về cost: Ta đã chạy S+V (cost=2) để quan sát đồng thuận.
      Nếu đồng thuận → cost=2 (S+V đã chạy, không cần A)
      Nếu bất đồng → cost=3 (S+V+A)
    Cost trung bình = 2 + P(bất đồng)

    Attributes:
        data        — CoalitionData
        accuracy    — router accuracy (0–1)
        choices     — list[frozenset], tổ hợp được chọn cho từng câu
        avg_cost    — cost trung bình per-question
    """

    def __init__(self, data: CoalitionData):
        self.data = data
        self.choices: list[frozenset] = []
        self.accuracy: float = 0.0
        self.avg_cost: float = 0.0
        self.n_agree: int = 0   # số câu S,V đồng thuận
        self.n_disagree: int = 0  # số câu S,V bất đồng

        if data.n_questions == 0 or len(data) == 0:
            return

        self._compute()

    def _compute(self):
        """Tính router choices, accuracy, và avg_cost."""
        n = self.data.n_questions

        # Cần có tổ hợp {S}, {S,V}, {S,V,A} để mô phỏng
        s_key = frozenset({"S"})
        sv_key = frozenset({"S", "V"})
        sva_key = frozenset({"S", "V", "A"})

        s_vec = self.data.correctness.get(s_key)
        sv_vec = self.data.correctness.get(sv_key)
        sva_vec = self.data.correctness.get(sva_key)

        if s_vec is None or sv_vec is None or sva_vec is None:
            # Fallback: nếu thiếu tổ hợp cần thiết, dùng những gì có
            self._compute_fallback()
            return

        total_correct = 0
        total_cost = 0

        for i in range(n):
            s_ok = s_vec[i]      # S đúng câu i?
            v_ok = sv_vec[i]     # S+V đúng câu i? (proxy cho V đồng ý + đúng)

            # Đồng thuận = S và V cùng đúng hoặc cùng sai
            # Trong thực tế: so sánh đáp án S vs V (không biết đúng/sai)
            # Offline: dùng (s_ok == (sv_vec[i])) làm proxy
            # Nhưng chính xác hơn: S đúng và S+V đúng → V đồng ý (vì S+V = S được V sửa)
            # Nếu S đúng và S+V đúng → V không sửa (hoặc sửa rồi giữ) → đồng thuận
            # Nếu S sai và S+V sai → V không sửa được → "đồng thuận sai"
            # Nếu S sai và S+V đúng → V sửa → bất đồng (V thấy S sai)
            # Nếu S đúng và S+V sai → V phá → bất đồng (V thấy S "sai")

            # Proxy đồng thuận: S và S+V cùng đúng hoặc cùng sai
            agree = (s_ok == 1 and sv_vec[i] == 1) or (s_ok == 0 and sv_vec[i] == 0)

            if agree:
                # Đồng thuận → dùng S, không cần A
                # Cost = 2 (đã chạy S+V để quan sát)
                self.choices.append(s_key)
                total_cost += 2
                total_correct += s_ok
                self.n_agree += 1
            else:
                # Bất đồng → chạy thêm A
                # Cost = 3 (S+V+A)
                self.choices.append(sva_key)
                total_cost += 3
                total_correct += sva_vec[i]
                self.n_disagree += 1

        self.accuracy = total_correct / n
        self.avg_cost = total_cost / n

    def _compute_fallback(self):
        """Fallback khi thiếu tổ hợp {S} hoặc {S,V} hoặc {S,V,A}.

        Dùng tổ hợp đầy đủ (PSVA) và tổ hợp không có A (PSV) nếu có.
        """
        n = self.data.n_questions
        full_key = frozenset(ROLES)
        no_a_key = frozenset({"P", "S", "V"})
        s_key = frozenset({"S"})

        full_vec = self.data.correctness.get(full_key, [0] * n)
        no_a_vec = self.data.correctness.get(no_a_key, [0] * n)
        s_vec = self.data.correctness.get(s_key, [0] * n)

        total_correct = 0
        total_cost = 0

        for i in range(n):
            # Proxy: nếu S đúng → đồng thuận (dùng S, cost=2)
            # Nếu S sai → bất đồng (dùng full, cost=4)
            if s_vec[i] == 1:
                self.choices.append(s_key)
                total_cost += 2
                total_correct += 1
                self.n_agree += 1
            else:
                self.choices.append(full_key)
                total_cost += 4
                total_correct += full_vec[i]
                self.n_disagree += 1

        self.accuracy = total_correct / n
        self.avg_cost = total_cost / n

    def summary(self) -> dict:
        """Trả về tóm tắt router."""
        n = self.data.n_questions
        return {
            "accuracy": round(self.accuracy, 4),
            "avg_cost": round(self.avg_cost, 2),
            "total_calls": int(self.avg_cost * n),
            "n_questions": n,
            "n_agree": self.n_agree,
            "n_disagree": self.n_disagree,
            "agree_rate": round(self.n_agree / n, 4) if n > 0 else 0,
            "strategy": "consensus_sv",
        }

    def __repr__(self) -> str:
        return f"ConsensusRouter(acc={self.accuracy:.4f}, cost={self.avg_cost:.2f})"


# ─────────────────────────────────────────────────────────────────────────────
# 4. PARETO ANALYZER — Bảng accuracy vs compute cho 16 tổ hợp
# ─────────────────────────────────────────────────────────────────────────────

class ParetoAnalyzer:
    """Tính bảng Pareto: accuracy vs #model-calls cho 16 tổ hợp + router + oracle.

    Mỗi tổ hợp là một điểm (cost, accuracy) trên đồ thị Pareto.
    Một điểm là Pareto-optimal nếu không có điểm nào khác có accuracy >= mà cost <=
    (với ít nhất một inequality strict).

    Attributes:
        data          — CoalitionData
        points        — list of dict, mỗi dict = {coalition, accuracy, cost, label, is_pareto_optimal}
        router_point  — điểm của router (nếu có)
        oracle_point  — điểm của oracle (nếu có)
    """

    def __init__(
        self,
        data: CoalitionData,
        oracle: Optional[Oracle] = None,
        router: Optional[ConsensusRouter] = None,
    ):
        self.data = data
        self.oracle = oracle
        self.router = router
        self.points: list[dict] = []
        self.router_point: Optional[dict] = None
        self.oracle_point: Optional[dict] = None

        self._compute()

    def _compute(self):
        """Tính tất cả điểm Pareto + frontier."""
        # Tạo điểm cho mỗi tổ hợp
        for key, acc in self.data.accuracy.items():
            self.points.append({
                "coalition": _coalition_label(key),
                "coalition_set": key,
                "accuracy": round(acc, 4),
                "cost": ROLE_COST[key],
                "label": _coalition_label(key),
                "is_pareto_optimal": False,  # sẽ tính sau
            })

        # Xác định Pareto frontier
        for i, p1 in enumerate(self.points):
            dominated = False
            for j, p2 in enumerate(self.points):
                if i == j:
                    continue
                # p2 dominates p1 nếu: p2.acc >= p1.acc AND p2.cost <= p1.cost
                # và ít nhất một strict
                if (p2["accuracy"] >= p1["accuracy"] and
                    p2["cost"] <= p1["cost"] and
                    (p2["accuracy"] > p1["accuracy"] or p2["cost"] < p1["cost"])):
                    dominated = True
                    break
            p1["is_pareto_optimal"] = not dominated

        # Điểm router
        if self.router is not None and self.router.accuracy > 0:
            self.router_point = {
                "coalition": "Router",
                "accuracy": round(self.router.accuracy, 4),
                "cost": round(self.router.avg_cost, 2),
                "label": "Router (consensus)",
                "is_pareto_optimal": False,
            }
            # Kiểm tra router có Pareto-optimal không
            dominated = False
            for p in self.points:
                if (p["accuracy"] >= self.router_point["accuracy"] and
                    p["cost"] <= self.router_point["cost"] and
                    (p["accuracy"] > self.router_point["accuracy"] or
                     p["cost"] < self.router_point["cost"])):
                    dominated = True
                    break
            self.router_point["is_pareto_optimal"] = not dominated

        # Điểm oracle
        if self.oracle is not None and self.oracle.accuracy > 0:
            self.oracle_point = {
                "coalition": "Oracle",
                "accuracy": round(self.oracle.accuracy, 4),
                "cost": round(self.oracle.avg_cost, 2),
                "label": "Oracle (upper bound)",
                "is_pareto_optimal": False,
            }

    def to_dict(self) -> dict:
        """Serialize ra dict để ghi JSON."""
        # Mốc baseline: chỉ Solver và full pipeline
        s_key = frozenset({"S"})
        full_key = frozenset(ROLES)

        baseline_s = None
        baseline_full = None

        for p in self.points:
            if p["coalition_set"] == s_key:
                baseline_s = {"accuracy": p["accuracy"], "cost": p["cost"], "label": "Solver only"}
            if p["coalition_set"] == full_key:
                baseline_full = {"accuracy": p["accuracy"], "cost": p["cost"], "label": "Full pipeline (PSVA)"}

        return {
            "coalitions": [
                {k: v for k, v in p.items() if k != "coalition_set"}
                for p in self.points
            ],
            "router": self.router_point,
            "oracle": self.oracle_point,
            "baseline_s": baseline_s,
            "baseline_full": baseline_full,
            "n_questions": self.data.n_questions,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. TRACE DATA FALLBACK — Dùng traces_full.json khi không có 16 tổ hợp
# ─────────────────────────────────────────────────────────────────────────────

def load_coalition_data(results_dir: Path | str) -> CoalitionData:
    """Hàm tiện ích: tạo CoalitionData từ thư mục results_<ROUND>/.

    Args:
        results_dir: thư mục chứa các sub-dir <mask>/ với preds.json + summary.json

    Returns:
        CoalitionData đã tải xong 16 tổ hợp
    """
    return CoalitionData(results_dir=results_dir)


def load_trace_data(trace_dir: Path | str) -> list[dict]:
    """Tải trace data từ res_ft_*/traces_full.json.

    Mỗi item có: i, q, gold, sol, ver, agg, sa, va, aa, s_ok, v_ok, a_ok, len_*

    Args:
        trace_dir: thư mục chứa traces_full.json (vd res_ft_m15/ tren nhanh archive)

    Returns:
        list of dict, mỗi dict = một câu hỏi với trace đầy đủ
    """
    trace_path = Path(trace_dir) / "traces_full.json"
    if not trace_path.exists():
        return []
    return json.loads(trace_path.read_text(encoding="utf-8"))


def trace_oracle(traces: list[dict]) -> dict:
    """Tính oracle accuracy từ trace data.

    Oracle: mỗi câu, nếu ít nhất một trong S/V/A đúng → oracle đúng.
    Cost: chọn vai rẻ nhất đúng (S=1, V=2 vì phải chạy S trước, A=3).
    """
    n = len(traces)
    if n == 0:
        return {"accuracy": 0.0, "avg_cost": 0.0, "n_questions": 0, "strategy": "trace_oracle"}

    total_correct = 0
    total_cost = 0

    for t in traces:
        s_ok = t.get("s_ok", False)
        v_ok = t.get("v_ok", False)
        a_ok = t.get("a_ok", False)

        # Ưu tiên S (rẻ nhất) → V (cost 2) → A (cost 3)
        if s_ok:
            total_correct += 1
            total_cost += 1  # Chỉ cần S
        elif v_ok:
            total_correct += 1
            total_cost += 2  # S + V
        elif a_ok:
            total_correct += 1
            total_cost += 3  # S + V + A
        else:
            # Không ai đúng → cost 1 (chạy S)
            total_cost += 1

    return {
        "accuracy": round(total_correct / n, 4),
        "avg_cost": round(total_cost / n, 2),
        "total_calls": total_cost,
        "n_questions": n,
        "strategy": "trace_oracle",
    }


def trace_consensus_router(traces: list[dict]) -> dict:
    """Tính consensus router accuracy từ trace data.

    Chiến lược: chạy S+V (cost=2). Nếu S và V đồng thuận (cùng đáp án) → dùng S.
    Nếu bất đồng → chạy A (cost=3).
    """
    n = len(traces)
    if n == 0:
        return {"accuracy": 0.0, "avg_cost": 0.0, "n_questions": 0, "strategy": "trace_router"}

    total_correct = 0
    total_cost = 0
    n_agree = 0
    n_disagree = 0

    for t in traces:
        sa = t.get("sa", "")
        va = t.get("va", "")
        s_ok = t.get("s_ok", False)
        a_ok = t.get("a_ok", False)

        # Luôn chạy S + V → cost = 2
        total_cost += 2

        if sa == va:
            # Đồng thuận → dùng đáp án S
            n_agree += 1
            total_correct += 1 if s_ok else 0
        else:
            # Bất đồng → chạy A → cost + 1
            n_disagree += 1
            total_cost += 1
            total_correct += 1 if a_ok else 0

    return {
        "accuracy": round(total_correct / n, 4),
        "avg_cost": round(total_cost / n, 2),
        "total_calls": total_cost,
        "n_questions": n,
        "n_agree": n_agree,
        "n_disagree": n_disagree,
        "agree_rate": round(n_agree / n, 4),
        "strategy": "trace_consensus_sv",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. MAIN — Chạy phân tích và in kết quả
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Chạy phân tích router và in kết quả.

    Tự động phát hiện nguồn dữ liệu:
      1. results_<ROUND>/ (nếu có) → phân tích đầy đủ 16 tổ hợp
      2. res_ft_*/traces_full.json (nếu có) → fallback trace
      3. results_summary/shapley_results.json → chỉ in tóm tắt
    """
    # UTF-8 stdout (tránh lỗi Unicode trên Windows)
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    ROOT = Path(__file__).resolve().parents[1]
    ROUND = os.environ.get("ROUND", "")
    TRACE = os.environ.get("TRACE", "")

    print("=" * 78)
    print("ROUTER ANALYSIS — RQ4: Tận dụng biến thiên theo câu để chạy rẻ hơn?")
    print("=" * 78)

    # ── Thử nguồn 1: results_<ROUND>/ ──
    if ROUND:
        results_dir = ROOT / f"results_{ROUND}"
    else:
        # Thử tìm thư mục results_* nào đó
        candidates = sorted(ROOT.glob("results_*"))
        candidates = [c for c in candidates if c.is_dir() and (c / "preds.json").parent.exists()]
        # Thử results/ (mặc định cho GSM8K r1)
        if (ROOT / "results").exists():
            results_dir = ROOT / "results"
        else:
            results_dir = candidates[0] if candidates else None

    if results_dir and results_dir.exists():
        print(f"\n📊 Nguồn dữ liệu: {results_dir}/")
        cd = CoalitionData(results_dir)

        if len(cd) == 0:
            print("⚠️  Không tìm thấy dữ liệu tổ hợp. Thử trace fallback...")
        elif len(cd) < 16:
            print(f"⚠️  Chỉ tải {len(cd)}/16 tổ hợp. Kết quả có thể không đầy đủ.")
            _run_full_analysis(cd)
        else:
            _run_full_analysis(cd)
            return

    # ── Thử nguồn 2: trace data ──
    trace_dir = None
    if TRACE:
        trace_dir = ROOT / TRACE
    else:
        # Tự động tìm res_ft_*/
        for candidate in sorted(ROOT.glob("res_ft_*")):
            if (candidate / "traces_full.json").exists():
                trace_dir = candidate
                break

    if trace_dir and trace_dir.exists():
        print(f"\n📊 Nguồn dữ liệu (fallback): {trace_dir}/traces_full.json")
        traces = load_trace_data(trace_dir)
        if traces:
            _run_trace_analysis(traces)
            return

    # ── Nguồn 3: chỉ có summary ──
    print("\n📊 Không tìm thấy per-question data. Dùng summary data từ shapley_results.json")
    summary_path = ROOT / "results_summary" / "shapley_results.json"
    if summary_path.exists():
        _run_summary_only(summary_path)
    else:
        print("❌ Không tìm thấy dữ liệu nào. Hãy chạy với ROUND=m1 hoặc đặt dữ liệu trong results_/")
        print("   Xem nhánh archive của repo để biết format dữ liệu.")


def _run_full_analysis(cd: CoalitionData):
    """Chạy phân tích đầy đủ với 16 tổ hợp."""
    n = cd.n_questions
    print(f"   Đã tải {len(cd)}/16 tổ hợp, n={n} câu hỏi\n")

    # Tính oracle, router
    oracle = Oracle(cd)
    router = ConsensusRouter(cd)

    # Baselines
    s_key = frozenset({"S"})
    full_key = frozenset(ROLES)
    s_acc = cd.accuracy.get(s_key, 0.0)
    full_acc = cd.accuracy.get(full_key, 0.0)

    # In bảng so sánh
    print("─" * 78)
    print(f"{'Chiến lược':<30s} {'Accuracy':>10s} {'Cost/Q':>8s} {'Total calls':>12s}")
    print("─" * 78)
    print(f"{'Solver only (S)':<30s} {s_acc:>10.4f} {1:>8d} {n:>12d}")
    print(f"{'Full pipeline (PSVA)':<30s} {full_acc:>10.4f} {4:>8d} {4*n:>12d}")
    print(f"{'Consensus Router (S+V→A?)':<30s} {router.accuracy:>10.4f} {router.avg_cost:>8.2f} {int(router.avg_cost*n):>12d}")
    print(f"{'Oracle (upper bound)':<30s} {oracle.accuracy:>10.4f} {oracle.avg_cost:>8.2f} {int(oracle.avg_cost*n):>12d}")
    print("─" * 78)

    # Gap analysis
    gap_oracle = oracle.accuracy - full_acc
    gap_router = router.accuracy - full_acc
    gap_router_vs_oracle = oracle.accuracy - router.accuracy

    print(f"\n📈 GAP ANALYSIS:")
    print(f"   Router  − Full pipeline = {gap_router:+.4f} ({gap_router*100:+.1f}đ)")
    print(f"   Oracle  − Full pipeline = {gap_oracle:+.4f} ({gap_oracle*100:+.1f}đ)")
    print(f"   Oracle  − Router        = {gap_router_vs_oracle:+.4f} ({gap_router_vs_oracle*100:+.1f}đ)")
    print(f"   Router lấy lại {gap_router/gap_oracle*100:.1f}% khoảng trống oracle" if gap_oracle > 0 else "")

    # Router details
    rs = router.summary()
    print(f"\n🔧 ROUTER DETAILS:")
    print(f"   Đồng thuận (skip A): {rs['n_agree']}/{n} ({rs['agree_rate']:.1%})")
    print(f"   Bất đồng (run A):   {rs['n_disagree']}/{n} ({1-rs['agree_rate']:.1%})")
    print(f"   Cost trung bình:     {rs['avg_cost']:.2f} calls/Q (so với 4 cho full)")

    # Pareto
    pa = ParetoAnalyzer(cd, oracle=oracle, router=router)
    print(f"\n📊 PARETO FRONTIER (accuracy vs #model-calls):")
    print(f"   {'Tổ hợp':<12s} {'Accuracy':>10s} {'Cost':>6s} {'Pareto?':>8s}")
    for p in sorted(pa.points, key=lambda x: (x["cost"], -x["accuracy"])):
        flag = "✅" if p["is_pareto_optimal"] else ""
        print(f"   {p['label']:<12s} {p['accuracy']:>10.4f} {p['cost']:>6d} {flag:>8s}")
    if pa.router_point:
        print(f"   {'Router':<12s} {pa.router_point['accuracy']:>10.4f} {pa.router_point['cost']:>6.2f} {'⭐':>8s}")
    if pa.oracle_point:
        print(f"   {'Oracle':<12s} {pa.oracle_point['accuracy']:>10.4f} {pa.oracle_point['cost']:>6.2f} {'🌟':>8s}")

    # Lưu kết quả
    output = {
        "n_questions": n,
        "n_coalitions": len(cd),
        "baselines": {
            "solver_only": {"accuracy": s_acc, "cost": 1},
            "full_pipeline": {"accuracy": full_acc, "cost": 4},
        },
        "router": router.summary(),
        "oracle": oracle.summary(),
        "pareto": pa.to_dict(),
    }
    out_path = Path(__file__).resolve().parents[1] / "results_summary" / "router_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    print(f"\n💾 Đã ghi: {out_path}")


def _run_trace_analysis(traces: list[dict]):
    """Chạy phân tích với trace data (fallback)."""
    n = len(traces)
    print(f"   Đã tải {n} traces\n")

    oracle = trace_oracle(traces)
    router = trace_consensus_router(traces)

    # Baselines từ trace
    s_correct = sum(1 for t in traces if t.get("s_ok", False))
    v_correct = sum(1 for t in traces if t.get("v_ok", False))
    a_correct = sum(1 for t in traces if t.get("a_ok", False))

    print("─" * 78)
    print(f"{'Chiến lược':<30s} {'Accuracy':>10s} {'Cost/Q':>8s} {'Total calls':>12s}")
    print("─" * 78)
    print(f"{'Solver only (S)':<30s} {s_correct/n:>10.4f} {1:>8d} {n:>12d}")
    print(f"{'S+V (always)':<30s} {v_correct/n:>10.4f} {2:>8d} {2*n:>12d}")
    print(f"{'S+V+A (always)':<30s} {a_correct/n:>10.4f} {3:>8d} {3*n:>12d}")
    print(f"{'Consensus Router':<30s} {router['accuracy']:>10.4f} {router['avg_cost']:>8.2f} {router['total_calls']:>12d}")
    print(f"{'Oracle (upper bound)':<30s} {oracle['accuracy']:>10.4f} {oracle['avg_cost']:>8.2f} {oracle['total_calls']:>12d}")
    print("─" * 78)

    gap_oracle = oracle["accuracy"] - s_correct / n
    gap_router = router["accuracy"] - s_correct / n
    print(f"\n📈 GAP ANALYSIS (so với Solver):")
    print(f"   Router  − Solver = {gap_router:+.4f} ({gap_router*100:+.1f}đ)")
    print(f"   Oracle  − Solver = {gap_oracle:+.4f} ({gap_oracle*100:+.1f}đ)")

    print(f"\n🔧 ROUTER DETAILS:")
    print(f"   Đồng thuận (skip A): {router['n_agree']}/{n} ({router['agree_rate']:.1%})")
    print(f"   Bất đồng (run A):   {router['n_disagree']}/{n} ({1-router['agree_rate']:.1%})")

    # Lưu
    output = {
        "n_questions": n,
        "source": "trace",
        "baselines": {
            "solver_only": {"accuracy": s_correct / n, "cost": 1},
            "sv_always": {"accuracy": v_correct / n, "cost": 2},
            "sva_always": {"accuracy": a_correct / n, "cost": 3},
        },
        "router": router,
        "oracle": oracle,
    }
    out_path = Path(__file__).resolve().parents[1] / "results_summary" / "router_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n💾 Đã ghi: {out_path}")


def _run_summary_only(summary_path: Path):
    """In tóm tắt khi chỉ có summary data (không có per-question)."""
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    coalitions = data.get("coalitions", {})
    shapley = data.get("shapley", {})

    print(f"\n📋 Summary data từ {summary_path.name}")
    print(f"   v(full) = {data.get('v_full', '?')}")
    print(f"   v(empty) = {data.get('v_empty', '?')}")
    print(f"\n   Shapley values:")
    for role in ROLES:
        phi = shapley.get(role, 0)
        print(f"     {NAMES[role]:11s} φ = {phi:+.4f}")

    print(f"\n   Coalition accuracies (sorted):")
    sorted_coals = sorted(coalitions.items(), key=lambda x: -x[1])
    for name, acc in sorted_coals:
        print(f"     {name:<12s} = {acc:.4f}")

    print(f"\n⚠️  Không có per-question data → không tính router/oracle.")
    print(f"    Cần thư mục results_<ROUND>/ với preds.json để chạy phân tích đầy đủ.")


if __name__ == "__main__":
    main()
