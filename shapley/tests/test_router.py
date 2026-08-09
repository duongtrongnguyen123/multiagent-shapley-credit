"""Test cases cho analysis/router.py — viết trước theo TDD.

Mỗi test mô tả một yêu cầu (requirement) của router:
- Tải đúng 16 tổ hợp từ results_<ROUND>/
- Tính oracle accuracy (trần trên)
- Tính consensus router accuracy + cost
- Tính Pareto data (accuracy vs #model-calls cho 16 tổ hợp)
- Xử lý thiếu dữ liệu (coalition thiếu, file hỏng)
- Fallback khi chỉ có trace data (không có 16 tổ hợp)

Chạy: pytest shapley/tests/test_router.py -v
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import sẽ hoạt động sau khi router.py được tạo
from analysis.router import (
    CoalitionData,
    Oracle,
    ConsensusRouter,
    ParetoAnalyzer,
    ROLE_COST,
    ROLES,
    load_coalition_data,
    load_trace_data,
)


# ─────────────────────────────────────────────────────────────
# 1. COALITION DATA LOADING
# ─────────────────────────────────────────────────────────────

class TestCoalitionData:
    """Test tải dữ liệu 16 tổ hợp từ thư mục results_<ROUND>/."""

    def test_load_all_16_coalitions(self, synthetic_results):
        """Tải đủ 16/16 tổ hợp từ thư mục results."""
        cd = CoalitionData(results_dir=synthetic_results)
        assert len(cd) == 16, f"Expected 16 coalitions, got {len(cd)}"

    def test_correctness_vectors_length(self, synthetic_results, sample_n):
        """Mỗi tổ hợp có vector đúng/sai dài đúng = số câu."""
        cd = CoalitionData(results_dir=synthetic_results)
        for key, vec in cd.correctness.items():
            assert len(vec) == sample_n, (
                f"Coalition {key}: expected {sample_n} questions, got {len(vec)}"
            )

    def test_values_are_binary(self, synthetic_results):
        """Mỗi phần tử trong correctness vector phải là 0 hoặc 1."""
        cd = CoalitionData(results_dir=synthetic_results)
        for key, vec in cd.correctness.items():
            for v in vec:
                assert v in (0, 1), f"Coalition {key}: found non-binary value {v}"

    def test_coalition_keys_are_frozensets(self, synthetic_results):
        """Keys của correctness phải là frozenset của role names."""
        cd = CoalitionData(results_dir=synthetic_results)
        for key in cd.correctness:
            assert isinstance(key, frozenset)
            for role in key:
                assert role in ROLES

    def test_empty_coalition_exists(self, synthetic_results):
        """Tổ hợp rỗng (không vai nào) phải tồn tại."""
        cd = CoalitionData(results_dir=synthetic_results)
        assert frozenset() in cd.correctness

    def test_full_coalition_exists(self, synthetic_results):
        """Tổ hợp đầy đủ PSVA phải tồn tại."""
        cd = CoalitionData(results_dir=synthetic_results)
        assert frozenset(ROLES) in cd.correctness

    def test_solver_alone_accuracy(self, synthetic_results):
        """Solver một mình đúng 12/20 = 0.6."""
        cd = CoalitionData(results_dir=synthetic_results)
        s_key = frozenset({"S"})
        acc = sum(cd.correctness[s_key]) / len(cd.correctness[s_key])
        assert acc == pytest.approx(0.6, abs=0.001)

    def test_accuracy_from_summary(self, synthetic_results):
        """Accuracy trong summary.json phải khớp với mean của correctness vector."""
        cd = CoalitionData(results_dir=synthetic_results)
        for key, vec in cd.correctness.items():
            expected_acc = sum(vec) / len(vec)
            assert cd.accuracy[key] == pytest.approx(expected_acc, abs=0.001)

    def test_missing_coalition_handled(self, tmp_path, sample_n):
        """Thiếu một tổ hợp → vẫn load được nhưng báo warning."""
        # Tạo chỉ 15 tổ hợp (thiếu 1)
        results_dir = tmp_path / "results_partial"
        results_dir.mkdir()
        from itertools import combinations
        from tests.conftest import mask_to_dirname, make_preds, make_summary

        count = 0
        for size in range(5):
            for combo in combinations(ROLES, size):
                if count == 5:  # Bỏ qua tổ hợp thứ 6
                    count += 1
                    continue
                mask = {r: (r in combo) for r in ROLES}
                d = results_dir / mask_to_dirname(mask)
                d.mkdir()
                vec = [1] * (sample_n // 2) + [0] * (sample_n - sample_n // 2)
                (d / "preds.json").write_text(json.dumps(make_preds(sample_n, vec)))
                (d / "summary.json").write_text(json.dumps(make_summary(mask, sum(vec) / sample_n)))
                count += 1

        cd = CoalitionData(results_dir=results_dir)
        assert len(cd) == 15  # Chỉ 15 tổ hợp

    def test_n_questions_consistent(self, synthetic_results, sample_n):
        """Tất cả tổ hợp phải có cùng số câu hỏi."""
        cd = CoalitionData(results_dir=synthetic_results)
        lengths = {len(v) for v in cd.correctness.values()}
        assert len(lengths) == 1, f"Inconsistent question counts: {lengths}"
        assert lengths.pop() == sample_n


# ─────────────────────────────────────────────────────────────
# 2. ORACLE
# ─────────────────────────────────────────────────────────────

class TestOracle:
    """Test tính oracle accuracy — trần trên khi chọn tổ hợp tốt nhất cho từng câu."""

    def test_oracle_ge_full_pipeline(self, synthetic_results):
        """Oracle accuracy phải >= accuracy của bất kỳ tổ hợp đơn lẻ nào."""
        cd = CoalitionData(results_dir=synthetic_results)
        oracle = Oracle(cd)
        oracle_acc = oracle.accuracy
        for key, acc in cd.accuracy.items():
            assert oracle_acc >= acc - 1e-9, (
                f"Oracle {oracle_acc} < coalition {key} accuracy {acc}"
            )

    def test_oracle_max_1(self, synthetic_results):
        """Oracle accuracy không vượt 1.0."""
        cd = CoalitionData(results_dir=synthetic_results)
        oracle = Oracle(cd)
        assert oracle.accuracy <= 1.0 + 1e-9

    def test_oracle_per_question_choice(self, synthetic_results, sample_n):
        """Mỗi câu phải được gán cho ít nhất một tổ hợp."""
        cd = CoalitionData(results_dir=synthetic_results)
        oracle = Oracle(cd)
        choices = oracle.choices  # list of frozenset, len = n_questions
        assert len(choices) == sample_n
        for ch in choices:
            assert isinstance(ch, frozenset)

    def test_oracle_picks_cheapest_correct(self, synthetic_results):
        """Khi nhiều tổ hợp đều đúng, oracle chọn tổ hợp rẻ nhất (ít vai nhất).

        Nếu không tổ hợp nào đúng câu đó, oracle chọn empty (cost=0) — đó là fallback.
        Chỉ kiểm tra các câu có ít nhất 1 tổ hợp đúng.
        """
        cd = CoalitionData(results_dir=synthetic_results)
        oracle = Oracle(cd)
        for i, choice in enumerate(oracle.choices):
            # Nếu tổ hợp được chọn là empty và không đúng → không có tổ hợp nào đúng
            if choice == frozenset() and cd.correctness[choice][i] == 0:
                # Kiểm tra: không tổ hợp nào đúng câu i
                for key, vec in cd.correctness.items():
                    assert vec[i] == 0, (
                        f"Oracle chose empty for question {i} but {key} is correct"
                    )
                continue

            # Kiểm tra: tổ hợp được chọn thực sự đúng câu i
            assert cd.correctness[choice][i] == 1, (
                f"Oracle picked incorrect coalition {choice} for question {i}"
            )
            # Kiểm tra: không có tổ hợp rẻ hơn cũng đúng câu i
            choice_cost = ROLE_COST[choice]
            for key, vec in cd.correctness.items():
                if vec[i] == 1 and key != choice:
                    assert ROLE_COST[key] >= choice_cost, (
                        f"Cheaper correct coalition {key} (cost {ROLE_COST[key]}) "
                        f"exists but oracle picked {choice} (cost {choice_cost})"
                    )

    def test_oracle_avg_cost(self, synthetic_results):
        """Oracle phải trả về cost trung bình per-question."""
        cd = CoalitionData(results_dir=synthetic_results)
        oracle = Oracle(cd)
        assert oracle.avg_cost > 0
        assert oracle.avg_cost <= 4.0  # Tối đa 4 vai

    def test_oracle_gain_over_best_single(self, synthetic_results):
        """Oracle phải tốt hơn tổ hợp đơn lẻ tốt nhất."""
        cd = CoalitionData(results_dir=synthetic_results)
        oracle = Oracle(cd)
        best_single = max(cd.accuracy.values())
        assert oracle.accuracy >= best_single


# ─────────────────────────────────────────────────────────────
# 3. CONSENSUS ROUTER
# ─────────────────────────────────────────────────────────────

class TestConsensusRouter:
    """Test router heuristic dựa trên độ đồng thuận giữa các vai."""

    def test_router_accuracy(self, synthetic_results):
        """Router phải đạt accuracy > Solver đơn độc."""
        cd = CoalitionData(results_dir=synthetic_results)
        router = ConsensusRouter(cd)
        s_acc = cd.accuracy[frozenset({"S"})]
        assert router.accuracy >= s_acc, (
            f"Router {router.accuracy} < Solver alone {s_acc}"
        )

    def test_router_cost_le_full(self, synthetic_results):
        """Router cost trung bình phải <= full pipeline (4 calls)."""
        cd = CoalitionData(results_dir=synthetic_results)
        router = ConsensusRouter(cd)
        assert router.avg_cost <= 4.0

    def test_router_choices_valid(self, synthetic_results, sample_n):
        """Mỗi choice của router phải là một frozenset hợp lệ."""
        cd = CoalitionData(results_dir=synthetic_results)
        router = ConsensusRouter(cd)
        assert len(router.choices) == sample_n
        for ch in router.choices:
            assert isinstance(ch, frozenset)
            for role in ch:
                assert role in ROLES

    def test_router_always_includes_solver(self, synthetic_results):
        """Router luôn include ít nhất Solver (không bao giờ trả về empty)."""
        cd = CoalitionData(results_dir=synthetic_results)
        router = ConsensusRouter(cd)
        for ch in router.choices:
            assert "S" in ch, f"Router chose coalition without Solver: {ch}"

    def test_router_sv_agree_skip_agg(self, synthetic_results):
        """Khi S và V đồng thuận (cùng đúng hoặc cùng sai), không cần A.

        Logic: nếu S và V cùng đúng → dùng S (rẻ hơn).
        Nếu S và V cùng sai → A cũng khó cứu → dùng S (rẻ hơn, không lãng phí).
        """
        cd = CoalitionData(results_dir=synthetic_results)
        router = ConsensusRouter(cd)
        # Ít nhất một câu phải được route mà không cần A (tiết kiệm cost)
        no_agg_count = sum(1 for ch in router.choices if "A" not in ch)
        assert no_agg_count > 0, "Router never skips Aggregator — no cost savings"

    def test_router_disagreement_triggers_agg(self, synthetic_results):
        """Khi S và V không đồng thuận → router nên dùng A."""
        cd = CoalitionData(results_dir=synthetic_results)
        router = ConsensusRouter(cd)
        with_agg_count = sum(1 for ch in router.choices if "A" in ch)
        assert with_agg_count > 0, "Router never uses Aggregator"

    def test_router_summary(self, synthetic_results):
        """Router phải trả về summary dict với các trường cần thiết."""
        cd = CoalitionData(results_dir=synthetic_results)
        router = ConsensusRouter(cd)
        summary = router.summary()
        assert "accuracy" in summary
        assert "avg_cost" in summary
        assert "total_calls" in summary
        assert "n_questions" in summary
        assert "strategy" in summary


# ─────────────────────────────────────────────────────────────
# 4. PARETO ANALYZER
# ─────────────────────────────────────────────────────────────

class TestParetoAnalyzer:
    """Test tính bảng Pareto: accuracy vs #model-calls cho 16 tổ hợp."""

    def test_pareto_has_all_coalitions(self, synthetic_results):
        """Bảng Pareto phải có đủ 16 tổ hợp."""
        cd = CoalitionData(results_dir=synthetic_results)
        pa = ParetoAnalyzer(cd)
        assert len(pa.points) == 16

    def test_pareto_points_format(self, synthetic_results):
        """Mỗi point phải có: coalition, accuracy, cost, is_pareto_optimal."""
        cd = CoalitionData(results_dir=synthetic_results)
        pa = ParetoAnalyzer(cd)
        for p in pa.points:
            assert "coalition" in p
            assert "accuracy" in p
            assert "cost" in p
            assert "is_pareto_optimal" in p
            assert "label" in p

    def test_pareto_cost_matches_role_count(self, synthetic_results):
        """Cost = số vai trong tổ hợp (mỗi vai = 1 model call)."""
        cd = CoalitionData(results_dir=synthetic_results)
        pa = ParetoAnalyzer(cd)
        for p in pa.points:
            expected_cost = len(p["coalition_set"])
            assert p["cost"] == expected_cost, (
                f"{p['coalition']}: cost {p['cost']} != {expected_cost} roles"
            )

    def test_pareto_frontier(self, synthetic_results):
        """Các điểm Pareto-optimal: không bị dominated (cao hơn mà rẻ hơn)."""
        cd = CoalitionData(results_dir=synthetic_results)
        pa = ParetoAnalyzer(cd)
        frontier = [p for p in pa.points if p["is_pareto_optimal"]]
        assert len(frontier) >= 1, "Pareto frontier must not be empty"

        # Kiểm tra: không điểm nào trên frontier bị dominated bởi điểm khác
        for i, p1 in enumerate(frontier):
            for p2 in pa.points:
                if p2 is p1:
                    continue
                # p2 dominates p1 nếu p2 có accuracy >= và cost <= (ít nhất 1 strict)
                if (p2["accuracy"] >= p1["accuracy"] and
                    p2["cost"] <= p1["cost"] and
                    (p2["accuracy"] > p1["accuracy"] or p2["cost"] < p1["cost"])):
                    pytest.fail(
                        f"Pareto point {p1['coalition']} is dominated by {p2['coalition']}"
                    )

    def test_pareto_includes_router_and_oracle(self, synthetic_results):
        """Bảng Pareto phải include điểm của router và oracle."""
        cd = CoalitionData(results_dir=synthetic_results)
        oracle = Oracle(cd)
        router = ConsensusRouter(cd)
        pa = ParetoAnalyzer(cd, oracle=oracle, router=router)
        assert pa.router_point is not None
        assert pa.oracle_point is not None
        assert pa.router_point["accuracy"] == router.accuracy
        assert pa.oracle_point["accuracy"] == oracle.accuracy

    def test_pareto_to_dict(self, synthetic_results):
        """ParetoAnalyzer phải serialize được ra dict/JSON."""
        cd = CoalitionData(results_dir=synthetic_results)
        oracle = Oracle(cd)
        router = ConsensusRouter(cd)
        pa = ParetoAnalyzer(cd, oracle=oracle, router=router)
        d = pa.to_dict()
        assert "coalitions" in d
        assert "router" in d
        assert "oracle" in d
        assert "baseline_s" in d  # Mốc "chỉ Solver"
        assert "baseline_full" in d  # Mốc "luôn chạy full"
        assert len(d["coalitions"]) == 16


# ─────────────────────────────────────────────────────────────
# 5. TRACE DATA FALLBACK
# ─────────────────────────────────────────────────────────────

class TestTraceDataFallback:
    """Test fallback khi chỉ có trace data (không có 16 tổ hợp)."""

    def test_load_trace_data(self, trace_data):
        """Tải trace data từ res_ft_test/traces_full.json."""
        traces = load_trace_data(trace_data)
        assert len(traces) == 20
        assert "s_ok" in traces[0]
        assert "v_ok" in traces[0]
        assert "a_ok" in traces[0]

    def test_trace_oracle(self, trace_data):
        """Oracle từ trace: chọn S/V/A đúng nhất cho từng câu."""
        traces = load_trace_data(trace_data)
        # Oracle: mỗi câu, nếu S đúng → dùng S (cost 1), nếu V đúng → dùng V (cost 1), etc.
        # Oracle accuracy = fraction of questions where at least one of S/V/A is correct
        n = len(traces)
        oracle_correct = sum(
            1 for t in traces if t["s_ok"] or t["v_ok"] or t["a_ok"]
        )
        oracle_acc = oracle_correct / n
        assert oracle_acc > 0
        assert oracle_acc <= 1.0

    def test_trace_consensus_router(self, trace_data):
        """Consensus router từ trace: S+V, nếu đồng ý → stop, nếu khác → A."""
        traces = load_trace_data(trace_data)
        n = len(traces)
        correct = 0
        total_cost = 0
        for t in traces:
            # Luôn chạy S + V (cost = 2)
            total_cost += 2
            if t["sa"] == t["va"]:  # S và V đồng thuận
                # Dùng đáp án S
                correct += 1 if t["s_ok"] else 0
            else:
                # Chạy thêm A (cost + 1)
                total_cost += 1
                # Dùng đáp án A
                correct += 1 if t["a_ok"] else 0
        router_acc = correct / n
        assert router_acc > 0
        assert total_cost <= 3 * n  # Tối đa 3 calls/question


# ─────────────────────────────────────────────────────────────
# 6. EDGE CASES
# ─────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Test các trường hợp biên."""

    def test_empty_results_dir(self, tmp_path):
        """Thư mục results rỗng → CoalitionData raise error hoặc trả empty."""
        empty_dir = tmp_path / "results_empty"
        empty_dir.mkdir()
        cd = CoalitionData(results_dir=empty_dir)
        assert len(cd) == 0

    def test_all_wrong_solver(self, tmp_path, sample_n):
        """Solver sai hết → oracle = 0 (nếu tất cả tổ hợp đều sai hết)."""
        results_dir = tmp_path / "results_all_wrong"
        results_dir.mkdir()
        from tests.conftest import mask_to_dirname, make_preds, make_summary
        from itertools import combinations

        for size in range(5):
            for combo in combinations(ROLES, size):
                mask = {r: (r in combo) for r in ROLES}
                d = results_dir / mask_to_dirname(mask)
                d.mkdir()
                vec = [0] * sample_n
                (d / "preds.json").write_text(json.dumps(make_preds(sample_n, vec)))
                (d / "summary.json").write_text(json.dumps(make_summary(mask, 0.0)))

        cd = CoalitionData(results_dir=results_dir)
        oracle = Oracle(cd)
        assert oracle.accuracy == 0.0

    def test_all_correct_full(self, tmp_path, sample_n):
        """Tất cả tổ hợp đều đúng hết → oracle = 1.0, cost = 0 (empty coalition đúng)."""
        results_dir = tmp_path / "results_all_right"
        results_dir.mkdir()
        from tests.conftest import mask_to_dirname, make_preds, make_summary
        from itertools import combinations

        for size in range(5):
            for combo in combinations(ROLES, size):
                mask = {r: (r in combo) for r in ROLES}
                d = results_dir / mask_to_dirname(mask)
                d.mkdir()
                vec = [1] * sample_n
                (d / "preds.json").write_text(json.dumps(make_preds(sample_n, vec)))
                (d / "summary.json").write_text(json.dumps(make_summary(mask, 1.0)))

        cd = CoalitionData(results_dir=results_dir)
        oracle = Oracle(cd)
        assert oracle.accuracy == 1.0
        # Empty coalition (cost=0) đúng hết → oracle chọn empty, avg_cost = 0
        assert oracle.avg_cost == 0.0

    def test_role_cost(self):
        """ROLE_COST: empty=0, S=1, SV=2, SVA=3, PSVA=4."""
        assert ROLE_COST[frozenset()] == 0
        assert ROLE_COST[frozenset({"S"})] == 1
        assert ROLE_COST[frozenset({"S", "V"})] == 2
        assert ROLE_COST[frozenset({"S", "V", "A"})] == 3
        assert ROLE_COST[frozenset({"P", "S", "V", "A"})] == 4

    def test_n_questions_mismatch(self, tmp_path):
        """Hai tổ hợp có số câu khác nhau → raise error."""
        results_dir = tmp_path / "results_mismatch"
        results_dir.mkdir()
        from tests.conftest import mask_to_dirname, make_preds, make_summary
        from itertools import combinations

        dirs_created = 0
        for size in range(5):
            for combo in combinations(ROLES, size):
                mask = {r: (r in combo) for r in ROLES}
                d = results_dir / mask_to_dirname(mask)
                d.mkdir()
                n = 20 if dirs_created < 8 else 15  # Nửa 20, nửa 15
                vec = [1] * (n // 2) + [0] * (n - n // 2)
                (d / "preds.json").write_text(json.dumps(make_preds(n, vec)))
                (d / "summary.json").write_text(json.dumps(make_summary(mask, sum(vec) / n)))
                dirs_created += 1

        with pytest.raises(ValueError, match="[Ii]nconsistent"):
            CoalitionData(results_dir=results_dir)
