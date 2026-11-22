"""Strict R3 decision-time firewall, cleaning funnel, fee-base, and edge-case tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from revision.build_variant import (
    SimParams,
    build_lagged_candidates_from_frames,
    compute_cleaning_funnel,
    spoil_frac_ref,
)

ROOT = Path(__file__).resolve().parents[1]


def test_cleaning_funnel_drops_invalid_and_reconciles() -> None:
    df = pd.DataFrame(
        [
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-01", "Min_Price": 1000.0, "Modal_Price": 1500.0, "Max_Price": 1800.0},
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-01", "Min_Price": 1000.0, "Modal_Price": 1600.0, "Max_Price": 1800.0},  # conflicting dup
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Other", "Grade": "FAQ", "Arrival_Date": "2025-01-02", "Min_Price": 1100.0, "Modal_Price": 1400.0, "Max_Price": 1700.0},
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-03", "Min_Price": 1000.0, "Modal_Price": 400.0, "Max_Price": 1500.0},  # invalid modal < min
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-04", "Min_Price": 1200.0, "Modal_Price": 1600.0, "Max_Price": 1100.0},  # invalid min > max
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-05", "Min_Price": -5.0, "Modal_Price": 1200.0, "Max_Price": 1500.0},   # nonpositive
        ]
    )
    canon_df, bad_df, counts = compute_cleaning_funnel(df)
    assert counts["panel_rows_raw"] == 6
    assert counts["invalid_nonpositive_or_na_rows"] == 1
    assert counts["invalid_minmax_swapped_rows"] == 1
    assert counts["invalid_modal_outside_minmax_rows"] == 1
    assert counts["invalid_rows_dropped_total"] == 3
    assert counts["rows_after_invalid_drop"] == 3
    assert counts["raw_key_conflicting_modal_groups"] == 1
    assert counts["retained_raw_key_rows"] == 2
    assert counts["retained_canonical_variety_day_rows"] == 2
    assert len(bad_df) == 1
    # Conflicting dup median of [1500, 1600] == 1550
    row0 = canon_df[canon_df["Arrival_Date"] == pd.Timestamp("2025-01-01")].iloc[0]
    assert row0["Modal_Price"] == 1550.0


def test_real_lagged_candidates_and_cleaning_counts_invariants() -> None:
    counts = json.loads((ROOT / "revision/results/cleaning_counts.json").read_text())
    assert counts["panel_rows_raw"] == 260043
    assert counts["invalid_modal_outside_minmax_rows"] == 759
    assert counts["panel_rows_raw"] - counts["invalid_rows_dropped_total"] == counts["rows_after_invalid_drop"]
    assert counts["rows_after_invalid_drop"] - counts["raw_key_duplicate_excess_dropped"] == counts["retained_raw_key_rows"]
    assert counts["retained_raw_key_rows"] - counts["canonical_variety_merge_excess"] == counts["retained_canonical_variety_day_rows"]
    # Weather leak audit counts present and honest (2025-01-01..2026-04-08 window)
    assert counts["weather_rows_2025_2026"] == 67135
    assert counts["weather_rain_fc_equals_era5"] == 66222
    assert counts["weather_rain_fc_equals_era5"] > 0.95 * counts["weather_rows_2025_2026"]

    df = pd.read_parquet(ROOT / "revision/results/lagged_candidates.parquet")
    assert len(df) > 100000
    d = pd.to_datetime(df["date"])
    dq = pd.to_datetime(df["dest_quote_date"])
    oq = pd.to_datetime(df["origin_quote_date"])
    arr = pd.to_datetime(df["arrival_date"])

    # R3: strict inequality < t on EVERY quote and arrival > date
    assert (dq < d).all()
    assert (oq < d).all()
    assert ((d - dq).dt.days == df["dest_lag_age"]).all()
    assert ((d - oq).dt.days == df["origin_lag_age"]).all()
    assert (df["dest_lag_age"].between(1, 7)).all()
    assert (df["origin_lag_age"].between(1, 7)).all()
    assert (arr > d).all()
    assert (df["lag_spread"] == df["dest_lag_price"] - df["origin_lag_price"]).all()
    assert (df["lag_spread"] > 100.0).all()
    assert "route_fc_rain" not in df.columns
    assert "route_era5_rain" not in df.columns
    # Max per episode == 5
    assert (df.groupby("episode_id").size() <= 5).all()
    # Fee rate is 0 on same_district
    assert (df.loc[df["same_district"], "fee_rate"] == 0.0).all()


def test_counterfactual_future_perturbation_zero_leakage_r3() -> None:
    """R3 property test: corrupting ALL prices on dates >= t* leaves day-t* shortlist and decisions bit-for-bit identical."""
    dates = pd.date_range("2025-07-01", "2025-07-20", freq="D")
    rows = []
    for d in dates:
        # Origin O1
        rows.append({"State": "Maharashtra", "District": "D1", "Market": "O1", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": d, "Min_Price": 900.0, "Modal_Price": 1000.0, "Max_Price": 1100.0})
        # Destination M1 (high yesterday spread, sporadic)
        if d.day % 2 == 1:
            rows.append({"State": "Maharashtra", "District": "D2", "Market": "M1", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": d, "Min_Price": 1400.0, "Modal_Price": 1600.0, "Max_Price": 1700.0})
        # Destination M2 (steady lower spread)
        rows.append({"State": "Maharashtra", "District": "D3", "Market": "M2", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": d, "Min_Price": 1200.0, "Modal_Price": 1400.0, "Max_Price": 1500.0})
        # Destination M3 (not profitable before t*: price = 950)
        rows.append({"State": "Maharashtra", "District": "D4", "Market": "M3", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": d, "Min_Price": 900.0, "Modal_Price": 950.0, "Max_Price": 1000.0})

    cor = pd.DataFrame([
        {"State": "Maharashtra", "origin_market": "O1", "dest_market": "M1", "same_district": False, "euclid_km": 80.0, "road_km": 100.0, "truck_hours": 3.0, "arrival_lag_days": 1},
        {"State": "Maharashtra", "origin_market": "O1", "dest_market": "M2", "same_district": False, "euclid_km": 70.0, "road_km": 90.0, "truck_hours": 3.0, "arrival_lag_days": 1},
        {"State": "Maharashtra", "origin_market": "O1", "dest_market": "M3", "same_district": False, "euclid_km": 60.0, "road_km": 80.0, "truck_hours": 2.5, "arrival_lag_days": 1},
    ])
    fees = pd.DataFrame([{"State": "Maharashtra", "Commodity": "Onion", "statutory_seller_fee_pct": 0.01}])

    t_star = pd.Timestamp("2025-07-12")
    raw_base = pd.DataFrame(rows)

    # Adversarially corrupt ALL prices on d >= t* (keep origin O1 row present at t* with a crazy modal price!)
    raw_adv = raw_base.copy()
    mask_ge = raw_adv["Arrival_Date"] >= t_star
    raw_adv.loc[mask_ge & (raw_adv["Market"] == "M3"), "Modal_Price"] = 99999.0
    raw_adv.loc[mask_ge & (raw_adv["Market"] == "M3"), "Max_Price"] = 99999.0
    raw_adv.loc[mask_ge & (raw_adv["Market"] == "O1"), "Modal_Price"] = 500.0
    raw_adv.loc[mask_ge & (raw_adv["Market"] == "O1"), "Min_Price"] = 400.0
    # Drop M1 and M2 completely on d > t* and on d == t*!
    raw_adv = raw_adv[~(mask_ge & raw_adv["Market"].isin(["M1", "M2"]))].copy()

    c_base, _ = build_lagged_candidates_from_frames(raw_base, cor, fees, min_origin_date="2025-07-03", max_origin_date="2025-07-16")
    c_adv, _ = build_lagged_candidates_from_frames(raw_adv, cor, fees, min_origin_date="2025-07-03", max_origin_date="2025-07-16")

    dec_cols = [
        "origin_market", "dest_market", "origin_lag_price", "origin_quote_date", "origin_lag_age",
        "dest_lag_price", "dest_quote_date", "dest_lag_age", "lag_spread",
        "dest_exact_rep_14d", "dest_exact_rep_28d", "dest_any_rep_14d", "dest_any_rep_28d",
        "dest_price_cv_28d", "dest_obs_cnt_28d", "dest_dow_exact_rep_8w",
        "freight_road", "fee_rate", "spoil_ref_0",
    ]
    sub_b = c_base[c_base["date"] <= t_star].sort_values(["date", "dest_market"]).reset_index(drop=True)
    sub_a = c_adv[c_adv["date"] <= t_star].sort_values(["date", "dest_market"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(sub_b[dec_cols], sub_a[dec_cols], check_exact=False, rtol=0, atol=1e-12)
    # Meanwhile settlement column changed at t* for O1!
    assert (sub_b.loc[sub_b["date"] == t_star, "settle_local_price_d0"] == 1000.0).all()
    assert (sub_a.loc[sub_a["date"] == t_star, "settle_local_price_d0"] == 500.0).all()


def test_hp_apple_lagged_invariants_and_gitignored_independence() -> None:
    hp_path = ROOT / "revision/results/lagged_hp_apple_candidates.parquet"
    assert hp_path.exists()
    hp = pd.read_parquet(hp_path)
    d = pd.to_datetime(hp["date"])
    dq = pd.to_datetime(hp["dest_quote_date"])
    oq = pd.to_datetime(hp["origin_quote_date"])
    assert (dq < d).all()
    assert (oq < d).all()
    assert (hp["dest_lag_age"].between(1, 7)).all()
    assert (hp["origin_lag_age"].between(1, 7)).all()
    assert (hp["lag_spread"] > 100.0).all()
    assert (hp["freight_road"] == 35.0 + 0.45 * 1.45 * hp["road_km"]).all()
    assert (hp.loc[hp["same_district"], "fee_rate"] == 0.0).all()
    assert (hp.loc[~hp["same_district"], "fee_rate"] == 0.010).all()

    bv_text = (ROOT / "revision/build_variant.py").read_text()
    assert "candidates_6state.parquet" not in bv_text.split("Enforces" if "Enforces" in bv_text else "ROOT = Path")[1]

