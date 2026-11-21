"""Tests for Stage-II Mechanistic Autopsy (Exp 16) and Uncensored CRC Forecaster (Exp 17)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.models.uncensored_crc_forecaster import (
    CRCConfig,
    UncensoredCRCForecaster,
    evaluate_mandiguard_crc,
    t1_pass_mask,
)
from tests.test_agent_and_leakage import _make_toy_cands


def test_uncensored_crc_settlement_firewall_zero_future_leakage() -> None:
    """Verify training rows whose arrival_date+2 exceeds max training date never enter fit()."""
    rng = np.random.default_rng(123)
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    n = len(dates)
    from src.models.arrival_forecaster import FEATURE_COLS

    df = pd.DataFrame({c: rng.normal(0.0, 0.05, size=n) for c in FEATURE_COLS})
    df["tau_days"] = 2
    df["dest_age_days"] = 0
    df["dest_open_prob_14d"] = 0.85
    df["dest_dow_open_rate"] = 0.80
    df["arrival_dow"] = dates.dayofweek
    df["commodity_code"] = 0
    df["state_code"] = 0
    df["State"] = "Maharashtra"
    df["Commodity"] = "Onion"
    df["road_km"] = 120.0
    df["euclid_km"] = 95.0
    df["truck_hours"] = 4.0
    df["same_district"] = False
    df["local_price"] = 1200.0
    df["dest_ref_price"] = 1800.0
    df["route_fc_tmax"] = 30.0
    df["route_fc_rh"] = 60.0
    df["route_fc_rain"] = 0.0
    df["dest_intra_spread_14d"] = 0.10
    df["date"] = dates.strftime("%Y-%m-%d")
    df["arrival_date"] = (dates + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    df["real_delta_net_inr"] = rng.normal(200.0, 80.0, size=n)

    # Perturb rows whose arrival_date+2 > max_train_date (2024-04-09): predictions must match identically!
    df_pert = df.copy()
    tail_mask = (pd.to_datetime(df_pert["arrival_date"]) + pd.Timedelta(days=2)) > pd.Timestamp(df_pert["date"].max())
    assert tail_mask.sum() >= 2
    df_pert.loc[tail_mask, "real_delta_net_inr"] = -99999.0

    fc1 = UncensoredCRCForecaster(seed=123).fit(df)
    fc2 = UncensoredCRCForecaster(seed=123).fit(df_pert)

    mu1, pl1, _, _, _ = fc1.predict_components(df)
    mu2, pl2, _, _, _ = fc2.predict_components(df)
    assert np.allclose(mu1, mu2, atol=1e-12)
    assert np.allclose(pl1, pl2, atol=1e-12)


def test_crc_zero_dispatch_is_not_zero_risk() -> None:
    """Total abstention must not satisfy the empirical risk gate."""
    cands = _make_toy_cands().copy()
    cands["real_delta_net_inr"] = -50.0
    fc = UncensoredCRCForecaster(seed=0)
    # Bypass fitting: calibration only needs predict_components.
    fc.is_fitted = True
    fc.predict_components = lambda df: (  # type: ignore[method-assign]
        np.full(len(df), -10.0),
        np.full(len(df), 0.9),
        np.full(len(df), -10.0),
        np.full(len(df), 40.0),
        np.full(len(df), 40.0),
    )
    cfg = CRCConfig(safety_margin_inr=10_000.0, beta_target=0.095, thin_grade_aware_t1=True)
    out = fc.calibrate_crc_lambda(cands, cfg=cfg, lambda_grid=np.array([0.0, 0.15, 1.2]))
    assert out["val_crc_risk"] == 1.0
    assert out["lambda_star"] == 1.2


def test_thin_grade_aware_t1_and_crc_calibration_bound() -> None:
    cands = _make_toy_cands()
    # Add dest_open_prob_14d=0.30, age=0 row and verify thin-grade-aware accepts while strict rejects
    thin_row = cands.iloc[[0]].copy()
    thin_row["episode_id"] = "EP_THIN"
    thin_row["dest_age_days"] = 0.0
    thin_row["dest_open_prob_14d"] = 0.30
    thin_row["dest_dow_open_rate"] = 0.30
    strict_ok = t1_pass_mask(thin_row, CRCConfig(thin_grade_aware_t1=False))
    thin_ok = t1_pass_mask(thin_row, CRCConfig(thin_grade_aware_t1=True))
    assert not bool(strict_ok[0])
    assert bool(thin_ok[0])


def test_exp16_and_exp17_outputs_and_figure9_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    res = root / "results"
    exp16 = pd.read_csv(res / "exp16_censored_bias_and_coverage_illusion.csv")
    exp17 = pd.read_csv(res / "exp17_uncensored_crc_validation.csv")
    exp17_b = pd.read_csv(res / "exp17_crc_bootstrap_comparisons.csv")

    assert len(exp16) == 18
    assert not exp16.isna().any().any()
    assert len(exp17) >= 28
    assert not exp17.isna().any().any()
    assert len(exp17_b) == 4
    assert (exp17["val_calibrated_lambda_star"] == 0.15).all()

    # Verify Figure 9 present and non-empty
    f9 = root / "figures/fig9_mechanistic_autopsy_and_uncensored_crc.png"
    assert f9.exists() and f9.stat().st_size > 20000

    # Verify Dual-Tier Exp 14 manifest updated
    man14 = json.loads((root / "data/manifests/official_datagov_parity_manifest.json").read_text())
    assert "tier2_agmarknet2_summary" in man14
    assert man14["tier2_agmarknet2_summary"]["modal_price_exact_parity_pct"] == 100.0
