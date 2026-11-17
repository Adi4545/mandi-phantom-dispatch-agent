"""Unit tests for MandiGuard sequential funnel, zero-leakage guarantees, and baselines."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.baselines.dispatch_baselines import (
    eval_b1_naive_screen_greedy,
    eval_b4_upfront_all_tools,
    eval_b5_multi_agent_coordinator,
)
from src.data.build_dispatch_episodes import canonicalize_variety
from src.models.arrival_forecaster import CausalArrivalForecaster, FEATURE_COLS


def _make_toy_cands() -> pd.DataFrame:
    return pd.DataFrame(
        [
            # Episode 1: Dest_A has stale/closed risk (age=6, open_prob=0.2) despite high screen_spread=700 -> T1 prunes!
            # Dest_B is fresh, active, cool, profitable -> T1, T2, T3, T4 pass -> DISPATCH Dest_B!
            {
                "episode_id": "EP_001",
                "State": "Maharashtra",
                "Commodity": "Onion",
                "Variety_Key": "Red",
                "dest_market": "Dest_A",
                "local_price": 1500.0,
                "screen_dest_price": 2200.0,
                "screen_spread": 700.0,
                "dest_ref_price": 2200.0,
                "dest_age_days": 6.0,
                "dest_open_prob_14d": 0.20,
                "dest_dow_open_rate": 0.25,
                "dest_intra_spread_14d": 0.10,
                "same_district": False,
                "road_km": 120.0,
                "euclid_km": 100.0,
                "truck_hours": 3.5,
                "route_fc_tmax": 28.0,
                "route_fc_rh": 60.0,
                "route_fc_rain": 0.0,
                "pred_ret": 0.02,
                "lcb_ret": -0.05,
                "real_delta_net_inr": -350.0,
                "real_open_d0_delta_net_inr": np.nan,
                "real_closed_or_no_variety_trap": True,
                "real_arrival_price_dropped": True,
            },
            {
                "episode_id": "EP_001",
                "State": "Maharashtra",
                "Commodity": "Onion",
                "Variety_Key": "Red",
                "dest_market": "Dest_B",
                "local_price": 1500.0,
                "screen_dest_price": 2050.0,
                "screen_spread": 550.0,
                "dest_ref_price": 2050.0,
                "dest_age_days": 0.0,
                "dest_open_prob_14d": 0.90,
                "dest_dow_open_rate": 0.85,
                "dest_intra_spread_14d": 0.08,
                "same_district": False,
                "road_km": 90.0,
                "euclid_km": 75.0,
                "truck_hours": 2.5,
                "route_fc_tmax": 26.0,
                "route_fc_rh": 55.0,
                "route_fc_rain": 0.0,
                "pred_ret": 0.01,
                "lcb_ret": -0.04,
                "real_delta_net_inr": 380.0,
                "real_open_d0_delta_net_inr": 380.0,
                "real_closed_or_no_variety_trap": False,
                "real_arrival_price_dropped": False,
            },
            # Episode 2: Freight exceeds spread -> T2 prunes -> REFUSE_PHANTOM_SPREAD -> delta_net = 0
            {
                "episode_id": "EP_002",
                "State": "Himachal Pradesh",
                "Commodity": "Apple",
                "Variety_Key": "Delicious",
                "dest_market": "Dest_C",
                "local_price": 5000.0,
                "screen_dest_price": 5180.0,
                "screen_spread": 180.0,
                "dest_ref_price": 5180.0,
                "dest_age_days": 0.0,
                "dest_open_prob_14d": 0.85,
                "dest_dow_open_rate": 0.80,
                "dest_intra_spread_14d": 0.08,
                "same_district": False,
                "road_km": 250.0,
                "euclid_km": 160.0,
                "truck_hours": 7.0,
                "route_fc_tmax": 22.0,
                "route_fc_rh": 65.0,
                "route_fc_rain": 0.0,
                "pred_ret": 0.0,
                "lcb_ret": -0.05,
                "real_delta_net_inr": -120.0,
                "real_open_d0_delta_net_inr": -120.0,
                "real_closed_or_no_variety_trap": False,
                "real_arrival_price_dropped": False,
            },
        ]
    )


def test_variety_canonicalization() -> None:
    assert canonicalize_variety("Onion", "Onion") == "Standard"
    assert canonicalize_variety("Onion", "Other") == "Standard"
    assert canonicalize_variety("Potato", "Deshi") == "Desi"
    assert canonicalize_variety("Apple", "Royal Delicious") == "Royal Delicious"


def test_funnel_pruning_saves_calls_vs_upfront() -> None:
    cands = _make_toy_cands()
    cfg = AgentConfig(safety_margin_inr=100.0, log_traces=True)
    mg_df, traces = evaluate_mandiguard_vectorized(cands, cfg)
    b4_df = eval_b4_upfront_all_tools(cands, cfg)
    b1_df = eval_b1_naive_screen_greedy(cands)
    b5_df = eval_b5_multi_agent_coordinator(cands, safety_margin_inr=100.0)

    # EP_001: Dest_A pruned at T1 (1 call), Dest_B runs T1..T4 (4 calls) => 5 total vs B4 upfront 8 calls!
    assert mg_df.loc[mg_df["episode_id"] == "EP_001", "chosen_dest"].iloc[0] == "Dest_B"
    assert mg_df.loc[mg_df["episode_id"] == "EP_001", "tool_calls_total"].iloc[0] == 5
    assert b4_df.loc[b4_df["episode_id"] == "EP_001", "tool_calls_total"].iloc[0] == 8
    # Matched terminal outcome between sequential MandiGuard and Upfront B4
    assert np.allclose(mg_df["delta_net_inr"], b4_df["delta_net_inr"])

    # Naive B1 falls into Dest_A phantom trap (-350), whereas MandiGuard achieves +380 and 0 on EP_002
    assert b1_df.loc[b1_df["episode_id"] == "EP_001", "delta_net_inr"].iloc[0] == -350.0
    assert mg_df["delta_net_inr"].sum() == 380.0
    assert len(traces) == 2
    assert b5_df["delta_net_inr"].iloc[0] == 380.0


def test_causal_conformal_zero_future_leakage() -> None:
    """Changing future target_ret values at t' > t must NOT alter prediction or LCB at date <= t."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2024-01-01", periods=365, freq="D")
    n = len(dates)
    df_tr = pd.DataFrame({c: rng.normal(0.0, 0.1, size=n) for c in FEATURE_COLS})
    df_tr["tau_days"] = 2
    df_tr["dest_age_days"] = 0
    df_tr["arrival_dow"] = dates.dayofweek
    df_tr["commodity_code"] = 0
    df_tr["state_code"] = 0
    df_tr["Commodity"] = "Onion"
    df_tr["date"] = dates
    df_tr["arrival_date"] = dates + pd.Timedelta(days=2)
    df_tr["target_ret"] = rng.normal(0.0, 0.05, size=n)

    forecaster = CausalArrivalForecaster(seed=123).fit(df_tr)

    eval_dates = pd.date_range("2025-01-01", periods=40, freq="D")
    df_ev1 = pd.DataFrame({c: rng.normal(0.0, 0.1, size=40) for c in FEATURE_COLS})
    df_ev1["tau_days"] = 2
    df_ev1["dest_age_days"] = 0
    df_ev1["arrival_dow"] = eval_dates.dayofweek
    df_ev1["commodity_code"] = 0
    df_ev1["state_code"] = 0
    df_ev1["Commodity"] = "Onion"
    df_ev1["date"] = eval_dates
    df_ev1["arrival_date"] = eval_dates + pd.Timedelta(days=2)
    df_ev1["target_ret"] = 0.02

    # Perturb ONLY future targets from day 15 onward -> days 0..14 must be 100% bit-identical!
    df_ev2 = df_ev1.copy()
    df_ev2.loc[15:, "target_ret"] = -0.50
    _, lcb1 = forecaster.predict_point_and_causal_lcb(df_ev1)
    _, lcb2 = forecaster.predict_point_and_causal_lcb(df_ev2)
    assert np.allclose(lcb1[:15], lcb2[:15], atol=1e-15)
