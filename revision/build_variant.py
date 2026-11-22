"""Build the lagged decision table.

Decision quotes are exact-variety modals dated on or before the day before the
origin date. Same-day destination prices are not used. Settlement prices on the
arrival day and the next two days are outcomes, not decision inputs.

The revision files named by the external review were not in any branch. This
module is the replacement.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.build_dispatch_episodes import canonicalize_variety

ROOT = Path(__file__).resolve().parents[1]


def _fee_rate(state: pd.Series, commodity: pd.Series) -> np.ndarray:
    is_hp_app = (state == "Himachal Pradesh") & (commodity == "Apple")
    return np.select(
        [
            state.isin(["Karnataka", "Gujarat"]),
            is_hp_app,
            state == "Himachal Pradesh",
            state == "Maharashtra",
        ],
        [0.005, 0.010, 0.005, 0.010],
        default=0.015,
    )


def cleaning_counts(panel: pd.DataFrame) -> dict:
    key = ["State", "District", "Market", "Commodity", "Variety", "Grade", "Arrival_Date"]
    n = int(len(panel))
    modal = panel["Modal_Price"]
    invalid = (modal.isna()) | (modal <= 0) | (panel["Min_Price"] <= 0) | (panel["Max_Price"] <= 0)
    outside = (modal < panel["Min_Price"]) | (modal > panel["Max_Price"])
    dup_mask = panel.duplicated(key, keep=False)
    n_dup_rows = int(dup_mask.sum())
    n_dup_keys = int(panel.loc[dup_mask].groupby(key).ngroups) if n_dup_rows else 0
    conflict = 0
    if n_dup_rows:
        conflict = int((panel.loc[dup_mask].groupby(key)["Modal_Price"].nunique() > 1).sum())
    # Retained: drop nonpositive prices, then one median row per key.
    kept = panel.loc[~invalid].copy()
    before = len(kept)
    kept = (
        kept.groupby(key, as_index=False)
        .agg(Modal_Price=("Modal_Price", "median"), Min_Price=("Min_Price", "min"), Max_Price=("Max_Price", "max"))
    )
    return {
        "panel_rows": n,
        "invalid_nonpositive_price_rows": int(invalid.sum()),
        "modal_outside_minmax_rows": int(outside.sum()),
        "duplicate_key_rows": n_dup_rows,
        "duplicate_keys": n_dup_keys,
        "duplicate_keys_conflicting_modal": conflict,
        "rows_after_drop_invalid": int(before),
        "retained_key_rows_after_median": int(len(kept)),
    }


def build(root: Path = ROOT) -> pd.DataFrame:
    panel = pd.read_parquet(root / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet")
    panel["Arrival_Date"] = pd.to_datetime(panel["Arrival_Date"])
    panel["Var"] = [canonicalize_variety(c, v) for c, v in zip(panel["Commodity"], panel["Variety"])]
    counts = cleaning_counts(panel)
    exact = (
        panel.groupby(["State", "Market", "Commodity", "Var", "Arrival_Date"], as_index=False)
        .agg(lag_price=("Modal_Price", "median"))
    )
    anyc = (
        panel.groupby(["State", "Market", "Commodity", "Arrival_Date"], as_index=False)
        .agg(any_min=("Min_Price", "min"))
    )
    # 2024 route climatology by state and month, from stored realized weather on candidates.
    clim_src = pd.read_parquet(
        root / "data/processed/candidates_6state.parquet",
        columns=["date", "State", "route_era5_tmax", "route_era5_rh", "route_era5_rain"],
    )
    clim_src["date"] = pd.to_datetime(clim_src["date"])
    clim_src = clim_src[clim_src["date"] < "2025-01-01"]
    clim_src["month"] = clim_src["date"].dt.month
    clim = (
        clim_src.groupby(["State", "month"], as_index=False)
        .agg(clim_tmax=("route_era5_tmax", "mean"), clim_rh=("route_era5_rh", "mean"), clim_rain=("route_era5_rain", "mean"))
    )

    use_cols = [
        "episode_id", "State", "Commodity", "Variety_Key", "date", "arrival_date",
        "origin_market", "origin_market_key", "dest_market", "local_price",
        "road_km", "euclid_km", "truck_hours", "same_district", "tau_days",
        "dest_modal_d0", "dest_min_d0", "dest_modal_d1", "dest_min_d1", "dest_modal_d2", "dest_min_d2",
        "dest_any_var_min_d0", "screen_dest_price", "dest_age_days", "dest_ref_price",
        "route_fc_rain", "route_era5_rain", "route_fc_rh", "route_era5_rh", "route_fc_tmax", "route_era5_tmax",
    ]
    cand = pd.read_parquet(root / "data/processed/candidates_6state.parquet", columns=use_cols)
    cand["date"] = pd.to_datetime(cand["date"])
    cand["arrival_date"] = pd.to_datetime(cand["arrival_date"])
    cand = cand[(cand["date"] >= "2025-01-01") & (cand["date"] <= "2026-04-08")].copy()
    cand["lag_deadline"] = cand["date"] - pd.Timedelta(days=1)
    exact = exact.rename(columns={"Market": "dest_market", "Var": "Variety_Key", "Arrival_Date": "quote_date"})
    exact = exact.sort_values("quote_date")
    left = cand.sort_values("lag_deadline")
    merged = pd.merge_asof(
        left,
        exact,
        left_on="lag_deadline",
        right_on="quote_date",
        by=["State", "dest_market", "Commodity", "Variety_Key"],
        direction="backward",
    )
    merged["lag_age"] = (merged["date"] - merged["quote_date"]).dt.days
    merged.loc[merged["lag_age"] > 7, "lag_price"] = np.nan
    merged["lag_spread"] = merged["lag_price"] - merged["local_price"]

    # Any-variety minimum on arrival+1 and arrival+2 (d0 is already on the row).
    anyc = anyc.rename(columns={"Market": "dest_market"})
    for offset, col in [(1, "any_min_d1"), (2, "any_min_d2")]:
        key = merged[["State", "dest_market", "Commodity"]].copy()
        key["Arrival_Date"] = merged["arrival_date"] + pd.Timedelta(days=offset)
        key["_row"] = np.arange(len(key))
        hit = key.merge(anyc, on=["State", "dest_market", "Commodity", "Arrival_Date"], how="left")
        hit = hit.sort_values("_row")
        merged[col] = hit["any_min"].to_numpy()
    merged["any_min_d0"] = merged["dest_any_var_min_d0"]

    fee_r = _fee_rate(merged["State"], merged["Commodity"])
    hp = np.where(merged["State"].to_numpy() == "Himachal Pradesh", 1.45, 1.0)
    road = merged["road_km"].to_numpy(dtype=np.float64)
    euc = merged["euclid_km"].to_numpy(dtype=np.float64)
    local = merged["local_price"].to_numpy(dtype=np.float64)
    same = merged["same_district"].to_numpy(dtype=bool)
    base_road = 35.0 + 0.45 * hp * road
    base_euc = 35.0 + 0.45 * hp * 1.20 * euc
    fee = np.where(same, 0.0, fee_r * np.maximum(local, 0.0))
    merged["freight_road"] = base_road + fee
    merged["freight_euclid"] = base_euc + fee
    merged["month"] = merged["date"].dt.month
    merged = merged.merge(clim, on=["State", "month"], how="left")
    # Forecast vs realized identity, for the audit note.
    rain_eq = np.isclose(merged["route_fc_rain"], merged["route_era5_rain"], equal_nan=False)
    rh_eq = np.isclose(merged["route_fc_rh"], merged["route_era5_rh"], equal_nan=False)
    counts["decision_rows_2025_2026"] = int(len(merged))
    counts["rain_fc_equals_era5"] = int(rain_eq.sum())
    counts["rh_fc_equals_era5"] = int(rh_eq.sum())
    counts["rain_pairs"] = int(len(merged))
    # Episodes touching a conflicting duplicate key on the origin date or dest quote date.
    conflict_keys = set()
    key = ["State", "District", "Market", "Commodity", "Variety", "Grade", "Arrival_Date"]
    dups = panel[panel.duplicated(key, keep=False)]
    if len(dups):
        nunq = dups.groupby(key)["Modal_Price"].nunique()
        bad = nunq[nunq > 1].reset_index()
        conflict_keys = set(zip(bad["State"], bad["Market"], bad["Commodity"], bad["Arrival_Date"].astype(str)))
    # Affected episodes: origin market/date or destination quote in that set. Variety omitted because of canonical names.
    odate = merged["date"].dt.strftime("%Y-%m-%d")
    qdate = merged["quote_date"].dt.strftime("%Y-%m-%d")
    origin_hit = [
        (s, m, c, d) in conflict_keys
        for s, m, c, d in zip(merged["State"], merged["origin_market"], merged["Commodity"], odate)
    ]
    dest_hit = [
        (s, m, c, d) in conflict_keys
        for s, m, c, d in zip(merged["State"], merged["dest_market"], merged["Commodity"], qdate.fillna(""))
    ]
    hit = np.array(origin_hit) | np.array(dest_hit)
    counts["candidate_rows_touching_conflicting_duplicate"] = int(hit.sum())
    counts["episodes_touching_conflicting_duplicate"] = int(merged.loc[hit, "episode_id"].nunique())
    out_dir = root / "revision" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cleaning_counts.json").write_text(json.dumps(counts, indent=2))
    keep = [
        "episode_id", "State", "Commodity", "Variety_Key", "date", "arrival_date", "origin_market",
        "origin_market_key", "dest_market", "local_price", "lag_price", "lag_age", "lag_spread",
        "quote_date", "tau_days", "road_km", "euclid_km", "truck_hours", "same_district",
        "freight_road", "freight_euclid", "dest_modal_d0", "dest_min_d0", "dest_modal_d1", "dest_min_d1",
        "dest_modal_d2", "dest_min_d2", "any_min_d0", "any_min_d1", "any_min_d2",
        "clim_tmax", "clim_rh", "clim_rain", "screen_dest_price", "dest_age_days", "dest_ref_price",
    ]
    slim = merged[keep].copy()
    slim.to_parquet(out_dir / "lagged_candidates.parquet", index=False)
    print(json.dumps(counts, indent=2))
    print("wrote", len(slim), "rows")
    return slim


if __name__ == "__main__":
    build()
