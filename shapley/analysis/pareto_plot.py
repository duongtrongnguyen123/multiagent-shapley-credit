#!/usr/bin/env python3
"""analysis/pareto_plot.py — Vẽ đường Pareto accuracy vs compute.

RQ4: Coordination có đáng compute không, và router lấy lại được bao nhiêu của +19 điểm?

Đồ thị:
  - Trục X: #model-calls per question (1 = chỉ Solver, 4 = full pipeline)
  - Trục Y: Accuracy
  - Chấm: 16 tổ hợp (xanh = Pareto-optimal, xám = bị dominated)
  - Sao: Router
  - Vương miện: Oracle
  - Đường ngang: baseline Solver và Full pipeline

Chạy:
  python analysis/pareto_plot.py                    # dùng router_results.json
  python analysis/pareto_plot.py --output pareto.png
"""
from __future__ import annotations

import json
import sys
import os
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# UTF-8 stdout
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]


def load_results() -> dict | None:
    """Tải router_results.json."""
    path = ROOT / "results_summary" / "router_results.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def plot_pareto(results: dict, output_path: Path | str = None):
    """Vẽ đồ thị Pareto.

    Hỗ trợ 2 chế độ:
      - Full mode: có 16 tổ hợp (từ results_<ROUND>/)
      - Trace mode: chỉ có S, S+V, S+V+A, Router, Oracle (từ traces_full.json)

    Args:
        results: dict từ router_results.json
        output_path: đường dẫn file output (PNG). Nếu None → default path.
    """
    pareto = results.get("pareto", {})
    coalitions = pareto.get("coalitions", [])
    router_pt = pareto.get("router")
    oracle_pt = pareto.get("oracle")
    baseline_s = pareto.get("baseline_s", {})
    baseline_full = pareto.get("baseline_full", {})

    # ── Trace mode fallback: dùng baselines thay cho coalitions ──
    is_trace_mode = results.get("source") == "trace"
    if is_trace_mode and not coalitions:
        baselines = results.get("baselines", {})
        coalitions = []
        for label, data in baselines.items():
            coalitions.append({
                "coalition": data.get("label", label),
                "accuracy": data.get("accuracy", 0),
                "cost": data.get("cost", 0),
                "label": data.get("label", label),
                "is_pareto_optimal": True,  # sẽ tính lại
            })
        # Tính Pareto optimality
        for i, p1 in enumerate(coalitions):
            dominated = False
            for j, p2 in enumerate(coalitions):
                if i == j:
                    continue
                if (p2["accuracy"] >= p1["accuracy"] and
                    p2["cost"] <= p1["cost"] and
                    (p2["accuracy"] > p1["accuracy"] or p2["cost"] < p1["cost"])):
                    dominated = True
                    break
            p1["is_pareto_optimal"] = not dominated
        router_pt = results.get("router")
        oracle_pt = results.get("oracle")
        baseline_s = baselines.get("solver_only", {})
        baseline_full = baselines.get("sva_always", {})

    if not coalitions:
        print("❌ Không có dữ liệu Pareto để vẽ.")
        return

    fig, ax = plt.subplots(figsize=(10, 7))

    # ── Vẽ các điểm tổ hợp ──
    for p in coalitions:
        is_frontier = p.get("is_pareto_optimal", False)
        color = "#2ecc71" if is_frontier else "#bdc3c7"
        marker = "*" if is_frontier else "o"
        size = 150 if is_frontier else 60
        ax.scatter(
            p["cost"], p["accuracy"],
            c=color, s=size, marker=marker, zorder=5,
            edgecolors="#27ae60" if is_frontier else "#95a5a6",
            linewidths=0.8,
        )
        # Label cho frontier points
        if is_frontier:
            ax.annotate(
                p["label"],
                (p["cost"], p["accuracy"]),
                textcoords="offset points",
                xytext=(8, 8),
                fontsize=9,
                fontweight="bold",
                color="#27ae60",
            )

    # ── Nối các điểm Pareto frontier ──
    frontier = sorted(
        [p for p in coalitions if p.get("is_pareto_optimal")],
        key=lambda x: x["cost"],
    )
    if len(frontier) > 1:
        ax.plot(
            [p["cost"] for p in frontier],
            [p["accuracy"] for p in frontier],
            color="#2ecc71", linestyle="--", linewidth=1.5, alpha=0.7, zorder=4,
        )

    # ── Điểm Router ──
    if router_pt:
        r_cost = router_pt.get("cost", router_pt.get("avg_cost", 0))
        r_acc = router_pt.get("accuracy", 0)
        ax.scatter(
            r_cost, r_acc,
            c="#e74c3c", s=200, marker="D", zorder=6,
            edgecolors="#c0392b", linewidths=1.2,
        )
        ax.annotate(
            f"Router\n({r_acc:.3f})",
            (r_cost, r_acc),
            textcoords="offset points",
            xytext=(10, -15),
            fontsize=9,
            fontweight="bold",
            color="#c0392b",
        )

    # ── Điểm Oracle ──
    if oracle_pt:
        o_cost = oracle_pt.get("cost", oracle_pt.get("avg_cost", 0))
        o_acc = oracle_pt.get("accuracy", 0)
        ax.scatter(
            o_cost, o_acc,
            c="#f1c40f", s=250, marker="^", zorder=6,
            edgecolors="#f39c12", linewidths=1.5,
        )
        ax.annotate(
            f"Oracle\n({o_acc:.3f})",
            (o_cost, o_acc),
            textcoords="offset points",
            xytext=(10, 8),
            fontsize=9,
            fontweight="bold",
            color="#f39c12",
        )

    # ── Baseline đường ngang ──
    if baseline_s:
        bs_acc = baseline_s.get("accuracy", 0)
        ax.axhline(
            y=bs_acc,
            color="#3498db", linestyle=":", linewidth=1, alpha=0.6,
        )
        ax.text(
            0.1, bs_acc + 0.005,
            f"Solver only ({bs_acc:.3f})",
            color="#3498db", fontsize=8, alpha=0.8,
        )

    if baseline_full:
        bf_acc = baseline_full.get("accuracy", 0)
        ax.axhline(
            y=bf_acc,
            color="#9b59b6", linestyle=":", linewidth=1, alpha=0.6,
        )
        ax.text(
            0.1, bf_acc + 0.005,
            f"Full pipeline ({bf_acc:.3f})",
            color="#9b59b6", fontsize=8, alpha=0.8,
        )

    # ── Formatting ──
    ax.set_xlabel("Model calls per question (compute cost)", fontsize=12)
    ax.set_ylabel("Accuracy", fontsize=12)
    ax.set_title(
        "Pareto: Accuracy vs Compute — Router có đáng không?",
        fontsize=14, fontweight="bold",
    )

    # Trục X: số nguyên (1-4)
    ax.set_xticks(range(0, 5))
    ax.set_xticklabels(["0 (empty)", "1 (S)", "2 (SV)", "3 (SVA)", "4 (PSVA)"])

    # Grid
    ax.grid(True, alpha=0.3, linestyle="-")

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#2ecc71", edgecolor="#27ae60", label="Pareto-optimal"),
        mpatches.Patch(facecolor="#bdc3c7", edgecolor="#95a5a6", label="Dominated"),
        plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="#e74c3c",
                   markersize=10, label="Router (consensus)"),
        plt.Line2D([0], [0], marker="^", color="w", markerfacecolor="#f1c40f",
                   markersize=10, label="Oracle (upper bound)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)

    # Tight layout
    plt.tight_layout()

    # Save or show
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"💾 Đã lưu đồ thị: {output_path}")
    else:
        output_path = ROOT / "results_summary" / "pareto_plot.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"💾 Đã lưu đồ thị: {output_path}")

    plt.close(fig)


def main():
    """Main entry point."""
    print("=" * 78)
    print("PARETO PLOT — Accuracy vs Compute")
    print("=" * 78)

    results = load_results()
    if results is None:
        print("❌ Không tìm thấy router_results.json.")
        print("   Hãy chạy `python analysis/router.py` trước.")
        return

    n = results.get("n_questions", "?")
    print(f"   N = {n} câu hỏi")

    output = os.environ.get("OUTPUT", "")
    if output:
        plot_pareto(results, output_path=output)
    else:
        plot_pareto(results)

    # In tóm tắt
    router = results.get("router", {})
    oracle = results.get("oracle", {})
    baselines = results.get("baselines", {})

    print(f"\n📊 TÓM TẮT:")
    if baselines.get("solver_only"):
        print(f"   Solver only:      acc={baselines['solver_only']['accuracy']:.4f}, cost=1")
    if baselines.get("full_pipeline"):
        print(f"   Full pipeline:    acc={baselines['full_pipeline']['accuracy']:.4f}, cost=4")
    if router:
        print(f"   Router:           acc={router.get('accuracy', 0):.4f}, cost={router.get('avg_cost', 0):.2f}")
    if oracle:
        print(f"   Oracle:           acc={oracle.get('accuracy', 0):.4f}, cost={oracle.get('avg_cost', 0):.2f}")


if __name__ == "__main__":
    main()
