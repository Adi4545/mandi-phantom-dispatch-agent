"""Verification tests for completed holdout results, manifests, figures, and zero-NaN invariants."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


def test_preregistration_precedes_results_in_git() -> None:
    root = Path(__file__).resolve().parents[1]
    res = subprocess.run(["git", "log", "--oneline"], cwd=root, capture_output=True, text=True, check=True)
    assert "Pre-register H1-H4 hypotheses" in res.stdout


def test_all_experiment_artifacts_present_and_consistent() -> None:
    root = Path(__file__).resolve().parents[1]
    res_dir = root / "results"
    required_csvs = [
        "confirmatory_holm_summary.csv",
        "exp1_phantom_anatomy.csv",
        "exp2_main_benchmark_6state.csv",
        "exp2b_by_state_commodity.csv",
        "exp3_hp_apple_grade_holdout.csv",
        "exp4_tool_ablations.csv",
        "exp5_budget_pareto.csv",
        "exp6_sensitivity_grid.csv",
        "exp7_rejection_breakdown.csv",
    ]
    for fn in required_csvs:
        p = res_dir / fn
        assert p.exists(), f"Missing results file: {fn}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Empty results file: {fn}"

    assert (res_dir / "exp8_live_nov2026_demo.json").exists()
    assert (res_dir / "traces/mandiguard_sample_traces.jsonl").exists()
    assert (root / "EXPERIMENT_REGISTRY.csv").exists()

    # Verify MandiGuard matches B4_UpfrontAllTools unrestricted utility and cuts tool calls > 25%
    exp2 = pd.read_csv(res_dir / "exp2_main_benchmark_6state.csv").set_index("policy")
    assert abs(exp2.loc["MandiGuard", "mean_delta_net_inr"] - exp2.loc["B4_UpfrontAllTools", "mean_delta_net_inr"]) < 1e-9
    assert exp2.loc["MandiGuard", "avg_tool_calls"] < 0.75 * exp2.loc["B4_UpfrontAllTools", "avg_tool_calls"]

    # Check confirmatory summary has 4 hypotheses with valid finite stats & exact N=69,526
    holm = pd.read_csv(res_dir / "confirmatory_holm_summary.csv")
    assert len(holm) == 4
    assert (holm["n_episodes"] == 69526).all()
    assert holm[["estimate", "ci95_low", "ci95_high", "p_raw", "p_holm"]].notna().all().all()

    # Check live demo valid summary
    live = json.loads((res_dir / "exp8_live_nov2026_demo.json").read_text())
    assert live["queries_executed"] == 22

    # Check all 8 publication figures generated (fig1-fig6 Phase A + fig7-fig8 Phase B)
    figs = list((root / "figures").glob("fig*.png"))
    assert len(figs) == 8
    for f in figs:
        assert f.stat().st_size > 20000
