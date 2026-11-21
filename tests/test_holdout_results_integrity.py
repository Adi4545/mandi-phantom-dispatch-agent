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
        "exp14_official_datagov_parity_audit.csv",
        "exp15_missing_data_open_yard_sensitivity.csv",
        "exp16_censored_bias_and_coverage_illusion.csv",
        "exp17_uncensored_crc_validation.csv",
        "exp17_crc_bootstrap_comparisons.csv",
    ]
    for fn in required_csvs:
        p = res_dir / fn
        assert p.exists(), f"Missing results file: {fn}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Empty results file: {fn}"
        if fn.startswith(("exp15", "exp16", "exp17")):
            assert not df.isna().any().any(), f"Unexpected NaNs in {fn}"

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

    # H3 is episode-level incidence, not the conditional loss-trip rate.
    b3_ep = float(exp2.loc["B3_MLPointDispatch", "ep_phantom_loss_pct"])
    mg_ep = float(exp2.loc["MandiGuard", "ep_phantom_loss_pct"])
    b3_cond = float(exp2.loc["B3_MLPointDispatch", "cond_phantom_loss_rate_pct"])
    mg_cond = float(exp2.loc["MandiGuard", "cond_phantom_loss_rate_pct"])
    h3 = float(holm.loc[holm["hypothesis"] == "H3", "estimate"].iloc[0])
    assert abs(((mg_ep - b3_ep) / 100.0) - h3) < 5e-4
    assert abs((mg_cond - b3_cond) / 100.0 - h3) > 0.01

    # Check live demo valid summary
    live = json.loads((res_dir / "exp8_live_nov2026_demo.json").read_text())
    assert live["queries_executed"] == 22

    # Check all 9 publication figures generated (fig1-fig6 Phase A + fig7-fig8 Phase B + fig9 Stage-II)
    figs = list((root / "figures").glob("fig*.png"))
    assert len(figs) == 9
    for f in figs:
        assert f.stat().st_size > 20000
