"""Unit tests for payoff physics, bootstrap inference, Holm correction, and leakage guards."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.evaluation.bootstrap import holm_bonferroni, phipson_smyth_p, two_way_mandi_week_bootstrap
from src.evaluation.payoff_model import (
    PayoffParams,
    compute_freight_inr,
    compute_realized_dispatch_outcome,
    compute_spoilage_fraction,
)
from src.utils.leakage import assert_no_future_leakage_dates, load_config


def test_freight_and_spoilage_monotone() -> None:
    p = PayoffParams()
    f_mh = compute_freight_inr("Maharashtra", 200.0, False, 2000.0, p)
    f_hp = compute_freight_inr("Himachal Pradesh", 200.0, False, 2000.0, p)
    assert f_hp > f_mh  # Mountain road surcharge

    s_cool = compute_spoilage_fraction("Tomato", 12.0, 20.0, 60.0, 0.0, 0, p)
    s_hot_rain = compute_spoilage_fraction("Tomato", 12.0, 38.0, 85.0, 45.0, 0, p)
    assert s_hot_rain > s_cool > 0.0
    assert s_hot_rain <= 0.55


def test_realized_outcome_open_vs_closed_trap() -> None:
    p = PayoffParams()
    open_out = compute_realized_dispatch_outcome(
        state="Maharashtra",
        commodity="Onion",
        local_price=1500.0,
        road_km=120.0,
        truck_hours=4.0,
        same_district=False,
        arrival_lag_days=1,
        dest_exact_prices=(2200.0, 2000.0, np.nan, np.nan, np.nan, np.nan),
        dest_any_var_min_d0=1800.0,
        dest_any_open_d0=True,
        route_tmax=28.0,
        route_rh=60.0,
        route_rain=0.0,
        params=p,
    )
    assert not open_out["closed_or_no_variety_trap"]
    assert open_out["delta_net_inr"] > 400.0
    assert np.isfinite(open_out["open_d0_delta_net_inr"])

    closed_out = compute_realized_dispatch_outcome(
        state="Maharashtra",
        commodity="Onion",
        local_price=1500.0,
        road_km=120.0,
        truck_hours=4.0,
        same_district=False,
        arrival_lag_days=1,
        dest_exact_prices=(np.nan, np.nan, np.nan, np.nan, np.nan, np.nan),
        dest_any_var_min_d0=np.nan,
        dest_any_open_d0=False,
        route_tmax=28.0,
        route_rh=60.0,
        route_rain=0.0,
        params=p,
    )
    assert closed_out["closed_or_no_variety_trap"]
    assert closed_out["no_exact_variety_3d"] is True
    assert closed_out["outcome_type"] == "closed_yard_divert"
    assert closed_out["delta_net_inr"] < 0.0
    assert np.isnan(closed_out["open_d0_delta_net_inr"])

    # A later exact-variety quote is a realized sale, not a three-day absence.
    # The trap flag is still True because wait_days > 0. Callers must not
    # describe that flag as an observed market closure.
    waited = compute_realized_dispatch_outcome(
        state="Maharashtra",
        commodity="Onion",
        local_price=1500.0,
        road_km=120.0,
        truck_hours=4.0,
        same_district=False,
        arrival_lag_days=1,
        dest_exact_prices=(np.nan, np.nan, 2100.0, 1900.0, np.nan, np.nan),
        dest_any_var_min_d0=1800.0,
        dest_any_open_d0=True,
        route_tmax=28.0,
        route_rh=60.0,
        route_rain=0.0,
        params=p,
    )
    assert waited["wait_days"] == 1
    assert waited["outcome_type"] == "exact_wait_d1"
    assert waited["closed_or_no_variety_trap"] is True
    assert waited["no_exact_variety_3d"] is False
    assert np.isfinite(waited["delta_net_inr"])


def test_bootstrap_and_holm() -> None:
    adj = holm_bonferroni([0.001, 0.04, 0.03, 0.20])
    assert abs(adj[0] - 0.004) < 1e-12
    assert abs(adj[2] - 0.09) < 1e-12
    assert phipson_smyth_p(0, 5000) == 1.0 / 5001.0

    rows = []
    dates = pd.date_range("2025-06-01", periods=28, freq="D")
    for m in range(10):
        for d in dates:
            rows.append({"origin_market_key": f"M{m}", "date": d, "a": 120.0 + m, "b": 20.0})
    df = pd.DataFrame(rows)
    res = two_way_mandi_week_bootstrap(df, "a", "b", reps=500, seed=20261117, direction="greater")
    assert abs(res["estimate"] - 104.5) < 1e-9
    assert res["ci95_low"] > 90.0
    assert res["p_value"] < 0.01
    assert res["p_value_basic"] < 0.05
    assert res["p_value_percentile"] == res["p_value"]


def test_temporal_firewall_guard() -> None:
    cfg = load_config()
    tr = pd.DataFrame({"date": ["2024-01-10", "2024-12-25"], "arrival_date": ["2024-01-11", "2024-12-27"]})
    va = pd.DataFrame({"date": ["2025-01-05", "2025-05-20"], "arrival_date": ["2025-01-06", "2025-05-22"]})
    assert_no_future_leakage_dates(tr, va, cfg)
