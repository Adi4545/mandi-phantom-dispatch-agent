"""Independent checks on the archived HP panel and weather grids. Run from any directory."""
import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized

DATA = ROOT / "data"
PANEL = DATA / "processed/candidates_hp_apple_grade.parquet"
MODEL = DATA / "interim/forecaster_2024.pkl"
ERA = DATA / "interim/weather_cache_era5.parquet"
FC = DATA / "interim/weather_cache_fc.parquet"
COORDS = DATA / "processed/mandi_coordinates.parquet"
ARCHIVE = DATA / "raw/agmarknet_6state_top_apple_2024_2026_all.parquet"


def weather_pairs():
    keys = ["grid_lat", "grid_lon", "date"]
    pair = pd.read_parquet(ERA).merge(pd.read_parquet(FC), on=keys, validate="one_to_one")
    return {
        "paired_cell_days": len(pair),
        "cells": int(pair[keys[:2]].drop_duplicates().shape[0]),
        "wet_paired_cell_days": int((pair.era5_rain_mm > 0).sum()),
        "rain_identical": int(pair.era5_rain_mm.eq(pair.fc_rain_mm).sum()),
        "humidity_identical": int(pair.era5_rh_mean.eq(pair.fc_rh_mean).sum()),
        "max_temperature_identical": int(pair.era5_tmax.eq(pair.fc_tmax).sum()),
    }


def market_selection():
    keys = ["State", "Market"]
    days = pd.read_parquet(ARCHIVE, columns=keys + ["Arrival_Date"]).drop_duplicates()
    train_days = days[days.Arrival_Date < "2025-01-01"].groupby(keys).size().rename("train_days")
    stats = train_days.to_frame().join(days.groupby(keys).size().rename("all_days")).reset_index()
    stats = stats.sort_values(["State", "train_days", "Market"], ascending=[True, False, True])
    eligible = stats[stats.train_days >= 20]

    def select(rows):
        return set(rows.groupby("State").head(30)[keys].itertuples(index=False, name=None))

    archive = select(eligible[eligible.all_days >= 80])
    train20 = select(eligible)
    train80 = select(eligible[eligible.train_days >= 80])
    return {
        "historical_market_count": len(archive),
        "training_20_days_only_count": len(train20),
        "training_80_days_only_count": len(train80),
        "added_if_exclude_future_days_20_day_cutoff": sorted(train20 - archive),
        "removed_if_exclude_future_days_20_day_cutoff": sorted(archive - train20),
    }


def recompute_apple_payoff(df):
    # HP apple tariff, prescribed discount, wait costs and weather law at audited HEAD.
    freight = 35 + 0.45 * 1.45 * df.road_km + (~df.same_district) * 0.01 * df.local_price
    prices = df[["dest_modal_d0", "dest_modal_d1", "dest_modal_d2"]].to_numpy()
    lows = df[["dest_min_d0", "dest_min_d1", "dest_min_d2"]].to_numpy()
    available = np.isfinite(prices) & (prices > 0)
    wait = available.argmax(axis=1)
    row = np.arange(len(df))
    price, low = prices[row, wait], lows[row, wait]
    low = np.where(np.isfinite(low) & (low > 0), low, price)
    heavy = df.route_era5_rain >= 35
    sale = np.where(heavy, (price + low) / 2, price)
    heat = 2 ** ((df.route_era5_tmax.clip(5, 48) - 20) / 10)
    humidity = 1 + 0.25 * ((df.route_era5_rh.clip(20, 100) - 70) / 30).clip(lower=0)
    hours = (df.truck_hours + 24 * wait).clip(lower=1)
    spoil = (0.0164 * hours / 24 * heat * humidity + 0.02 * heavy).clip(0, 0.55)
    fallback_sale = 0.9 * df.dest_any_var_min_d0
    fallback = np.where(fallback_sale > 0, fallback_sale * (1 - spoil) - freight - df.local_price,
                        -1.5 * freight - df.local_price * spoil)
    return np.where(available.any(axis=1), sale * (1 - spoil) - freight - 25 * wait - df.local_price,
                    fallback)


def metrics(out):
    net = np.sort(out.delta_net_inr.to_numpy())
    tail_mass = 0.1 * len(net)
    k = int(tail_mass)
    exact_tail = (net[:k].sum() + (tail_mass - k) * net[k]) / tail_mass
    dispatch = out.is_dispatch
    return {
        "episodes": len(net), "dispatches": int(dispatch.sum()),
        "negative_episodes": int((net < 0).sum()), "mean_inr_per_episode": float(net.mean()),
        "loss_pct_per_dispatch": float(100 * (net < 0).sum() / dispatch.sum()),
        "historical_mean_at_or_below_q10": float(net[net <= np.quantile(net, 0.1)].mean()),
        "exact_10_percent_mass_tail_mean": float(exact_tail),
    }


def baseline(df, kind):
    if kind == "B1":
        rows = df.assign(score=df.screen_spread - 35 - 0.45 * 1.45 * 1.2 * df.euclid_km)
    else:
        shortlist = df.sort_values(["episode_id", "screen_spread", "dest_market"],
                                   ascending=[True, False, True]).groupby("episode_id").head(5)
        freight = 35 + 0.45 * 1.45 * shortlist.road_km + (~shortlist.same_district) * 0.01 * shortlist.local_price
        score = (shortlist.dest_ref_price - shortlist.local_price - freight).where(shortlist.dest_age_days == 0)
        rows = shortlist.assign(score=score)
    ranked = rows.sort_values(["episode_id", "score", "dest_market"], ascending=[True, False, True])
    chosen = ranked.drop_duplicates("episode_id").set_index("episode_id")
    dispatch = chosen.score > 100
    filled = ranked.groupby("episode_id").first()
    incorrectly_filled = dispatch & chosen.real_open_d0_delta_net_inr.isna() & filled.real_open_d0_delta_net_inr.notna()
    out = pd.DataFrame({"is_dispatch": dispatch, "delta_net_inr": chosen.audit_payoff.where(dispatch, 0)})
    return dict(metrics(out), open_day0_fields_borrowed_by_historical_groupby_first=int(incorrectly_filled.sum()))


def lag_weather(df):
    # Pessimistic timing sensitivity: plug in t-7 calendar day weather at both route endpoints.
    # Final reanalysis is a retrospective proxy even here; no as-issued forecasts are inferred.
    coords = pd.read_parquet(COORDS)
    coords = coords[coords.State.eq("Himachal Pradesh")].drop_duplicates("Market").set_index("Market")
    era = pd.read_parquet(ERA).set_index(["grid_lat", "grid_lon", "date"])
    cols = ["era5_tmax", "era5_rh_mean", "era5_rain_mm"]
    series = []
    for endpoint in ["origin_market", "dest_market"]:
        key = pd.MultiIndex.from_arrays([df[endpoint].map(coords.lat).round(1),
                                         df[endpoint].map(coords.lon).round(1),
                                         pd.to_datetime(df.date) - pd.Timedelta(days=7)])
        series.append(era.loc[:, cols].reindex(key).to_numpy())
    lagged = np.maximum(*series)
    if not np.isfinite(lagged).all():
        raise ValueError("Incomplete seven-day weather join")
    df = df.copy()
    df[["route_fc_tmax", "route_fc_rh", "route_fc_rain"]] = lagged
    return df


def main():
    cand = pd.read_parquet(PANEL)
    with MODEL.open("rb") as fh:
        model = pickle.load(fh)
    cand["pred_ret"], cand["lcb_ret"] = model.predict_point_and_causal_lcb(cand)
    hold = cand[cand.date.between("2026-06-01", "2026-08-27") & (cand.arrival_date <= "2026-09-01")].copy()
    hold["audit_payoff"] = recompute_apple_payoff(hold)
    max_error = float(np.max(np.abs(hold.audit_payoff - hold.real_delta_net_inr)))
    if max_error > 1e-7:
        raise ValueError(f"HP payoff mismatch {max_error}")
    cfg = AgentConfig(safety_margin_inr=50.0)
    original, _ = evaluate_mandiguard_vectorized(hold, cfg)
    changed, _ = evaluate_mandiguard_vectorized(lag_weather(hold), cfg)
    aligned = original.merge(changed, on="episode_id", suffixes=("_original", "_lag"), validate="one_to_one")
    report = {
        "input_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in (PANEL, MODEL, ERA, FC, COORDS, ARCHIVE)},
        "scope": "HP exact-grade 2026 screened episodes; per-quintal simulator, same model/outcome parameters.",
        "weather_cache": weather_pairs(), "market_selection": market_selection(),
        "hp_candidate_rows": len(hold), "max_abs_payoff_difference": max_error,
        "B1_independent": baseline(hold, "B1"), "B2_independent": baseline(hold, "B2"),
        "v1_archived_weather": metrics(original), "v1_seven_day_lag_decision_weather": metrics(changed),
        "changed_action_or_destination": int(aligned.chosen_dest_original.ne(aligned.chosen_dest_lag).sum()),
    }
    destination = ROOT / "final/weather-and-apple-checks.json"
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
