"""Build strictly lagged, leak-free dispatch decision tables (Step 2 / A2-A3).

Reads ONLY tracked primary files in the repository (zero dependency on gitignored
`data/processed/candidates_6state.parquet`):
  - data/raw/agmarknet_6state_top_apple_2024_2026.parquet
  - data/processed/osrm_corridor_matrix.parquet
  - data/processed/state_apmc_and_loss_parameters.csv
  - data/processed/mandi_coordinates.parquet
  - data/processed/mandi_weather_2024_2026.parquet (strictly < 2025-01-01 for
    2024 climatology sensitivity only, plus weather-leak audit counts)

All decision-time features and shortlist construction at origin date t strictly
use information dated <= t - 1 (`dest_quote_date < t`, `origin_quote_date < t`,
lag_age in [1, 7]). Same-day origin modal price (`settle_local_price_d0`) and
arrival-window outcomes (`settle_*`) live exclusively in the settlement namespace.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from src.data.build_dispatch_episodes import canonicalize_variety

ROOT = Path(__file__).resolve().parents[1]

BASE_SPOIL_24H: Dict[str, float] = {
    "Tomato": 0.0325,
    "Onion": 0.0196,
    "Apple": 0.0164,
    "Potato": 0.0086,
}


@dataclass(frozen=True)
class SimParams:
    freight_base: float = 35.0
    freight_per_km: float = 0.45
    hp_km_mult: float = 1.45
    euclid_circuity_ref: float = 1.20
    detention_per_day: float = 25.0
    diversion_freight_mult: float = 1.5
    other_var_discount: float = 0.10


def spoil_frac_ref(
    commodity: np.ndarray,
    hours: np.ndarray,
    wait: np.ndarray,
    tmax: np.ndarray | float = 20.0,
    rh: np.ndarray | float = 65.0,
    rain: np.ndarray | float = 0.0,
) -> np.ndarray:
    """NABCONS (2022) 20C reference biological Q10 transit + waiting spoilage."""
    base = np.array([BASE_SPOIL_24H.get(str(c), 0.02) for c in commodity], dtype=np.float64)
    t_eff = np.clip(np.asarray(tmax, dtype=np.float64), 5.0, 48.0)
    rh_eff = np.clip(np.asarray(rh, dtype=np.float64), 20.0, 100.0)
    rain_eff = np.asarray(rain, dtype=np.float64)
    q10 = 2.0 ** ((t_eff - 20.0) / 10.0)
    rh_f = 1.0 + 0.25 * np.maximum(0.0, (rh_eff - 70.0) / 30.0)
    total_h = np.maximum(1.0, np.asarray(hours, dtype=np.float64) + 24.0 * np.maximum(wait, 0.0))
    bio = base * (total_h / 24.0) * q10 * rh_f + np.where(rain_eff >= 35.0, 0.02, 0.0)
    return np.clip(bio, 0.0, 0.55)


def compute_cleaning_funnel(panel: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Audit and drop invalid rows, collapse exact raw keys and canonical variety-day keys.

    Returns:
      - clean_canon_df: deduplicated canonical-variety daily rows
      - conflict_keys_df: unique (State, Market, Commodity, Arrival_Date) with conflicting modals
      - counts: exact reconciled integer funnel dictionary
    """
    raw = panel.copy()
    raw["Arrival_Date"] = pd.to_datetime(raw["Arrival_Date"])
    n_raw = int(len(raw))

    nonpos = (
        raw["Modal_Price"].isna()
        | raw["Min_Price"].isna()
        | raw["Max_Price"].isna()
        | (raw["Modal_Price"] <= 0)
        | (raw["Min_Price"] <= 0)
        | (raw["Max_Price"] <= 0)
    )
    minmax_swapped = raw["Min_Price"] > raw["Max_Price"]
    modal_outside = (~nonpos) & (~minmax_swapped) & (
        (raw["Modal_Price"] < raw["Min_Price"]) | (raw["Modal_Price"] > raw["Max_Price"])
    )
    invalid_any = nonpos | minmax_swapped | modal_outside
    valid = raw.loc[~invalid_any].copy()
    n_valid = int(len(valid))

    # 1) Exact 7-column raw duplicate audit on valid rows
    raw_key = ["State", "District", "Market", "Commodity", "Variety", "Grade", "Arrival_Date"]
    dup_raw_mask = valid.duplicated(raw_key, keep=False)
    n_dup_raw_rows = int(dup_raw_mask.sum())
    n_dup_raw_groups = int(valid.loc[dup_raw_mask].groupby(raw_key).ngroups) if n_dup_raw_rows else 0
    conflict_raw_groups = (
        int((valid.loc[dup_raw_mask].groupby(raw_key)["Modal_Price"].nunique() > 1).sum())
        if n_dup_raw_rows
        else 0
    )
    dedup_raw = valid.groupby(raw_key, as_index=False).agg(
        Modal_Price=("Modal_Price", "median"),
        Min_Price=("Min_Price", "min"),
        Max_Price=("Max_Price", "max"),
    )
    n_raw_key_retained = int(len(dedup_raw))
    raw_key_dup_excess = n_valid - n_raw_key_retained

    # 2) Canonicalize variety names & aggregate to unique (State, Market, Commodity, Variety_Key, Arrival_Date)
    if "Variety_Key" not in valid.columns:
        valid["Var_Canon"] = [canonicalize_variety(c, v) for c, v in zip(valid["Commodity"], valid["Variety"])]
        valid["Variety_Key"] = valid["Var_Canon"]

    canon_key = ["State", "Market", "Commodity", "Variety_Key", "Arrival_Date"]
    canon_df = valid.groupby(canon_key, as_index=False).agg(
        Modal_Price=("Modal_Price", "median"),
        Min_Price=("Min_Price", "min"),
        Max_Price=("Max_Price", "max"),
    )
    n_canon_retained = int(len(canon_df))
    canon_collapse_excess = n_raw_key_retained - n_canon_retained
    total_collapsed_from_valid = n_valid - n_canon_retained

    # Conflict keys for downstream telemetry
    if n_dup_raw_rows:
        g_conf = valid.loc[dup_raw_mask].groupby(raw_key)["Modal_Price"].nunique()
        bad = g_conf[g_conf > 1].reset_index()[["State", "Market", "Commodity", "Arrival_Date"]].drop_duplicates()
    else:
        bad = pd.DataFrame(columns=["State", "Market", "Commodity", "Arrival_Date"])

    counts = {
        "panel_rows_raw": n_raw,
        "invalid_nonpositive_or_na_rows": int(nonpos.sum()),
        "invalid_minmax_swapped_rows": int(minmax_swapped.sum()),
        "invalid_modal_outside_minmax_rows": int(modal_outside.sum()),
        "invalid_rows_dropped_total": int(invalid_any.sum()),
        "rows_after_invalid_drop": n_valid,
        "raw_key_duplicate_rows_involved": n_dup_raw_rows,
        "raw_key_duplicate_groups": n_dup_raw_groups,
        "raw_key_conflicting_modal_groups": conflict_raw_groups,
        "raw_key_duplicate_excess_dropped": int(raw_key_dup_excess),
        "retained_raw_key_rows": n_raw_key_retained,
        "canonical_variety_merge_excess": int(canon_collapse_excess),
        "retained_canonical_variety_day_rows": n_canon_retained,
        "total_dup_and_variant_excess_from_valid": int(total_collapsed_from_valid),
    }
    assert counts["panel_rows_raw"] - counts["invalid_rows_dropped_total"] == counts["rows_after_invalid_drop"]
    assert counts["rows_after_invalid_drop"] - counts["raw_key_duplicate_excess_dropped"] == counts["retained_raw_key_rows"]
    assert counts["retained_raw_key_rows"] - counts["canonical_variety_merge_excess"] == counts["retained_canonical_variety_day_rows"]
    assert counts["rows_after_invalid_drop"] - counts["total_dup_and_variant_excess_from_valid"] == counts["retained_canonical_variety_day_rows"]
    return canon_df, bad, counts


def build_feature_availability_table() -> pd.DataFrame:
    """Document every column's timestamp, R3 decision-time availability, and source."""
    rows = [
        ("episode_id", "t", "key", "Deterministic episode key from (State, Commodity, Variety_Key, origin_market, date)"),
        ("State", "static", "decision_allowed", "Primary AGMARKNET / OSRM state label"),
        ("Commodity", "static", "decision_allowed", "Crop name (Onion, Potato, Tomato, Apple)"),
        ("Variety_Key", "static", "decision_allowed", "Canonicalized variety (or Variety | Grade for HP Apple)"),
        ("date", "t", "decision_allowed", "Morning dispatch decision date t"),
        ("arrival_date", "t + tau", "key", "Expected truck arrival date t + tau_days"),
        ("origin_market", "static", "decision_allowed", "Origin AGMARKNET mandi name"),
        ("origin_market_key", "static", "decision_allowed", "State|origin_market clustering identifier"),
        ("dest_market", "static", "decision_allowed", "Candidate destination AGMARKNET mandi name"),
        ("tau_days", "static", "decision_allowed", "OSRM physical transit days (1..3)"),
        ("road_km", "static", "decision_allowed", "OSRM road distance (km)"),
        ("euclid_km", "static", "decision_allowed", "Great-circle distance (km)"),
        ("truck_hours", "static", "decision_allowed", "OSRM corridor truck hours"),
        ("same_district", "static", "decision_allowed", "True iff origin_district == dest_district"),
        ("fee_rate", "static", "decision_allowed", "Statutory APMC seller rate (0 if same_district, else PIB 154554 state rate)"),
        ("freight_road", "static", "decision_allowed", "Assumed transport freight (35 + 0.45 * hp_mult * road_km)"),
        ("freight_euclid", "static", "decision_allowed", "Euclidean distance freight ablation (35 + 0.45 * hp_mult * 1.2 * euclid_km)"),
        ("spoil_ref_0", "static_20C", "decision_allowed", "NABCONS (2022) 20C reference spoilage fraction at wait=0"),
        ("origin_quote_date", "<= t - 1", "decision_allowed", "Latest exact-variety origin modal quote date strictly before t"),
        ("origin_lag_age", ">= 1", "decision_allowed", "(date - origin_quote_date).days in [1, 7]"),
        ("origin_lag_price", "<= t - 1", "decision_allowed", "Latest exact-variety origin modal price strictly before t"),
        ("dest_quote_date", "<= t - 1", "decision_allowed", "Latest exact-variety destination modal quote date strictly before t"),
        ("dest_lag_age", ">= 1", "decision_allowed", "(date - dest_quote_date).days in [1, 7]"),
        ("dest_lag_price", "<= t - 1", "decision_allowed", "Latest exact-variety destination modal price strictly before t"),
        ("lag_spread", "<= t - 1", "decision_allowed", "dest_lag_price - origin_lag_price (> 100 INR/qtl menu screen)"),
        ("dest_exact_rep_14d", "<= t - 1", "decision_allowed", "Laplace-smoothed exact-variety reporting rate over [t-14, t-1]"),
        ("dest_exact_rep_28d", "<= t - 1", "decision_allowed", "Laplace-smoothed exact-variety reporting rate over [t-28, t-1]"),
        ("dest_any_rep_14d", "<= t - 1", "decision_allowed", "Laplace-smoothed any-variety reporting rate over [t-14, t-1]"),
        ("dest_any_rep_28d", "<= t - 1", "decision_allowed", "Laplace-smoothed any-variety reporting rate over [t-28, t-1]"),
        ("dest_dow_exact_rep_8w", "<= t - 1", "decision_allowed", "Laplace-smoothed exact-variety reporting rate on arrival weekday over last <=8 prior occurrences < t"),
        ("dest_price_cv_28d", "<= t - 1", "decision_allowed", "Sample CV of exact-variety dest modal over [t-28, t-1] (0.05 fallback if < 2 obs)"),
        ("dest_obs_cnt_28d", "<= t - 1", "decision_allowed", "Count of exact-variety destination quotes in [t-28, t-1]"),
        ("clim_tmax_2024", "< 2025-01-01", "decision_allowed_sens", "2024 state-month mean ERA5 Tmax (sensitivity only)"),
        ("clim_rh_2024", "< 2025-01-01", "decision_allowed_sens", "2024 state-month mean ERA5 RH (sensitivity only)"),
        ("clim_rain_2024", "< 2025-01-01", "decision_allowed_sens", "2024 state-month mean ERA5 rain (sensitivity only)"),
        ("settle_local_price_d0", "t", "settlement_only", "Realized day-t origin auction modal outside option (NEVER in decisions)"),
        ("settle_dest_modal_d0", "t + tau", "settlement_only", "Realized exact-variety modal price on arrival day d=0"),
        ("settle_dest_min_d0", "t + tau", "settlement_only", "Realized exact-variety min price on arrival day d=0"),
        ("settle_dest_modal_d1", "t + tau + 1", "settlement_only", "Realized exact-variety modal price on arrival day d=1"),
        ("settle_dest_min_d1", "t + tau + 1", "settlement_only", "Realized exact-variety min price on arrival day d=1"),
        ("settle_dest_modal_d2", "t + tau + 2", "settlement_only", "Realized exact-variety modal price on arrival day d=2"),
        ("settle_dest_min_d2", "t + tau + 2", "settlement_only", "Realized exact-variety min price on arrival day d=2"),
        ("settle_any_min_d0", "t + tau", "settlement_only", "Realized any-variety commodity min price on arrival day d=0"),
        ("settle_any_min_d1", "t + tau + 1", "settlement_only", "Realized any-variety commodity min price on arrival day d=1"),
        ("settle_any_min_d2", "t + tau + 2", "settlement_only", "Realized any-variety commodity min price on arrival day d=2"),
    ]
    return pd.DataFrame(rows, columns=["column", "information_timestamp", "role", "description"])


def _compute_strictly_past_history(
    canon_df: pd.DataFrame,
    min_date: pd.Timestamp,
    max_date: pd.Timestamp,
) -> pd.DataFrame:
    """Compute strictly <= t-1 reporting reliability & volatility features per (State, Market, Commodity, Variety_Key, date)."""
    all_dates = pd.date_range(min_date, max_date, freq="D")
    n_days = len(all_dates)
    dows = all_dates.dayofweek.to_numpy()
    date_to_idx = {d: i for i, d in enumerate(all_dates)}

    # Precompute any-variety daily existence matrix per (State, Commodity)
    any_rates: Dict[Tuple[str, str], Tuple[Dict[str, int], np.ndarray, np.ndarray]] = {}
    for (st, cm), sub_stcm in canon_df.groupby(["State", "Commodity"], sort=True):
        u_mkts = sorted(sub_stcm["Market"].unique())
        m2i = {m: i for i, m in enumerate(u_mkts)}
        obs_any = np.zeros((n_days, len(u_mkts)), dtype=np.float64)
        sub_c = sub_stcm[["Arrival_Date", "Market"]].drop_duplicates()
        sub_c = sub_c[sub_c["Arrival_Date"].isin(date_to_idx)]
        r_idx = sub_c["Arrival_Date"].map(date_to_idx).to_numpy(dtype=np.int64)
        c_idx = sub_c["Market"].map(m2i).to_numpy(dtype=np.int64)
        obs_any[r_idx, c_idx] = 1.0
        cs = np.zeros((n_days + 1, len(u_mkts)), dtype=np.float64)
        cs[1:] = np.cumsum(obs_any, axis=0)
        t_arr = np.arange(n_days)
        t14 = np.maximum(0, t_arr - 14)
        t28 = np.maximum(0, t_arr - 28)
        den14 = np.minimum(t_arr, 14)[:, None] + 2.0
        den28 = np.minimum(t_arr, 28)[:, None] + 2.0
        rep14 = (cs[t_arr] - cs[t14] + 1.0) / den14
        rep28 = (cs[t_arr] - cs[t28] + 1.0) / den28
        any_rates[(st, cm)] = (m2i, rep14, rep28)

    chunks = []
    # Exact variety matrix loop
    for (st, cm, vk), grp in canon_df.groupby(["State", "Commodity", "Variety_Key"], sort=True):
        u_mkts = sorted(grp["Market"].unique())
        m2i = {m: i for i, m in enumerate(u_mkts)}
        n_m = len(u_mkts)
        sub = grp[grp["Arrival_Date"].isin(date_to_idx)]
        r_idx = sub["Arrival_Date"].map(date_to_idx).to_numpy(dtype=np.int64)
        c_idx = sub["Market"].map(m2i).to_numpy(dtype=np.int64)
        obs = np.zeros((n_days, n_m), dtype=np.float64)
        price = np.zeros((n_days, n_m), dtype=np.float64)
        price2 = np.zeros((n_days, n_m), dtype=np.float64)
        pvals = sub["Modal_Price"].to_numpy(dtype=np.float64)
        obs[r_idx, c_idx] = 1.0
        price[r_idx, c_idx] = pvals
        price2[r_idx, c_idx] = pvals * pvals

        cs_n = np.zeros((n_days + 1, n_m), dtype=np.float64)
        cs_x = np.zeros((n_days + 1, n_m), dtype=np.float64)
        cs_x2 = np.zeros((n_days + 1, n_m), dtype=np.float64)
        cs_n[1:] = np.cumsum(obs, axis=0)
        cs_x[1:] = np.cumsum(price, axis=0)
        cs_x2[1:] = np.cumsum(price2, axis=0)

        t_arr = np.arange(n_days)
        t14 = np.maximum(0, t_arr - 14)
        t28 = np.maximum(0, t_arr - 28)
        ex14 = (cs_n[t_arr] - cs_n[t14] + 1.0) / (np.minimum(t_arr, 14)[:, None] + 2.0)
        ex28 = (cs_n[t_arr] - cs_n[t28] + 1.0) / (np.minimum(t_arr, 28)[:, None] + 2.0)

        cnt28 = cs_n[t_arr] - cs_n[t28]
        sx28 = cs_x[t_arr] - cs_x[t28]
        sx228 = cs_x2[t_arr] - cs_x2[t28]
        with np.errstate(divide="ignore", invalid="ignore"):
            mu28 = np.where(cnt28 >= 2, sx28 / np.maximum(cnt28, 1.0), 1.0)
            var28 = np.where(cnt28 >= 2, np.maximum(0.0, (sx228 - (sx28 * sx28) / np.maximum(cnt28, 1.0)) / np.maximum(cnt28 - 1.0, 1.0)), 0.0)
            cv28 = np.where((cnt28 >= 2) & (mu28 > 0), np.clip(np.sqrt(var28) / mu28, 0.0, 1.0), 0.05)

        # Strictly past arrival-weekday rates for arrival_dow w in 0..6:
        # Place rate inclusive of d_occ onto day d_occ + 1 and ffill, so on day t we ONLY ever read <= t - 1!
        dow_rates = np.full((7, n_days, n_m), 0.5, dtype=np.float64)
        for w in range(7):
            occ = np.flatnonzero(dows == w)
            if len(occ) == 0:
                continue
            w_obs = obs[occ]
            cs_w = np.zeros((len(occ) + 1, n_m), dtype=np.float64)
            cs_w[1:] = np.cumsum(w_obs, axis=0)
            u = np.arange(len(occ))
            u0 = np.maximum(0, u - 7)  # up to 8 occurrences: indices [u0..u] inclusive of u
            k_incl = cs_w[u + 1] - cs_w[u0]
            n_incl = (u - u0 + 1)[:, None]
            r_incl = (k_incl + 1.0) / (n_incl + 2.0)
            tmp = np.full((n_days, n_m), np.nan, dtype=np.float64)
            nxt = occ + 1
            valid_nxt = nxt < n_days
            if valid_nxt.any():
                tmp[nxt[valid_nxt]] = r_incl[valid_nxt]
            dow_rates[w] = pd.DataFrame(tmp).ffill().fillna(0.5).to_numpy(dtype=np.float64)

        m2i_any, any14_mat, any28_mat = any_rates[(st, cm)]
        any_cols = np.array([m2i_any[m] for m in u_mkts], dtype=np.int64)
        any14 = any14_mat[:, any_cols]
        any28 = any28_mat[:, any_cols]

        chunks.append((st, cm, vk, u_mkts, ex14, ex28, any14, any28, cv28, cnt28, dow_rates))

    return all_dates, date_to_idx, chunks


def build_lagged_candidates_from_frames(
    raw_df: pd.DataFrame,
    corridors_df: pd.DataFrame,
    fee_params_df: pd.DataFrame,
    clim_df: pd.DataFrame | None = None,
    grade_explicit: bool = False,
    min_origin_date: str = "2025-01-01",
    max_origin_date: str = "2026-04-08",
    max_lag_age: int = 7,
    min_lag_spread: float = 100.0,
    top_k: int = 5,
    params: SimParams = SimParams(),
    include_unreported_origin_days: bool = False,
) -> Tuple[pd.DataFrame, dict]:
    """Pure, leak-free builder turning raw price rows + static corridors into Top-K lagged candidates."""
    panel = raw_df.copy()
    if grade_explicit:
        panel["Var_Canon"] = [canonicalize_variety(c, v) for c, v in zip(panel["Commodity"], panel["Variety"])]
        panel["Variety_Key"] = panel["Var_Canon"] + " | " + panel["Grade"].astype(str).str.strip()

    canon_df, bad_conf_df, counts = compute_cleaning_funnel(panel)

    min_d = canon_df["Arrival_Date"].min()
    max_d = canon_df["Arrival_Date"].max()
    all_dates, date_to_idx, hist_chunks = _compute_strictly_past_history(canon_df, min_d, max_d)

    # Map history lookups for fast vectorized indexing
    hist_lookup = {(st, cm, vk): (mkts, ex14, ex28, any14, any28, cv28, cnt28, dow_r) for (st, cm, vk, mkts, ex14, ex28, any14, any28, cv28, cnt28, dow_r) in hist_chunks}

    # Origin lots strictly within evaluation window (day-t modal kept ONLY as settle_local_price_d0!)
    win_canon = canon_df[
        (canon_df["Arrival_Date"] >= pd.Timestamp(min_origin_date))
        & (canon_df["Arrival_Date"] <= pd.Timestamp(max_origin_date))
    ][["State", "Market", "Commodity", "Variety_Key", "Arrival_Date", "Modal_Price"]].rename(
        columns={"Market": "origin_market", "Arrival_Date": "date", "Modal_Price": "settle_local_price_d0"}
    ).copy()
    if include_unreported_origin_days:
        valid_orig_keys = canon_df[["State", "Market", "Commodity", "Variety_Key"]].drop_duplicates().rename(columns={"Market": "origin_market"})
        orig_in_cor = corridors_df[["State", "origin_market"]].drop_duplicates()
        valid_orig_keys = valid_orig_keys.merge(orig_in_cor, on=["State", "origin_market"], how="inner")
        win_dates = pd.DataFrame({"date": pd.date_range(pd.Timestamp(min_origin_date), pd.Timestamp(max_origin_date), freq="D")})
        grid = valid_orig_keys.assign(_k=1).merge(win_dates.assign(_k=1), on="_k").drop(columns=["_k"])
        orig = grid.merge(win_canon, on=["State", "origin_market", "Commodity", "Variety_Key", "date"], how="left")
    else:
        orig = win_canon
    counts["origin_variety_days_in_window"] = int(len(orig))

    # Origin lagged quote strictly <= t - 1
    orig["lag_deadline"] = orig["date"] - pd.Timedelta(days=1)
    orig_lag_src = canon_df[["State", "Market", "Commodity", "Variety_Key", "Arrival_Date", "Modal_Price"]].rename(
        columns={"Market": "origin_market", "Arrival_Date": "origin_quote_date", "Modal_Price": "origin_lag_price"}
    ).sort_values("origin_quote_date")

    orig = pd.merge_asof(
        orig.sort_values("lag_deadline"),
        orig_lag_src,
        left_on="lag_deadline",
        right_on="origin_quote_date",
        by=["State", "origin_market", "Commodity", "Variety_Key"],
        direction="backward",
    )
    orig["origin_lag_age"] = (orig["date"] - orig["origin_quote_date"]).dt.days
    orig = orig[(orig["origin_lag_age"] >= 1) & (orig["origin_lag_age"] <= max_lag_age)].copy()
    counts["origin_days_with_lag_1_7d"] = int(len(orig))

    # Deterministic episode order
    orig = orig.sort_values(["State", "Commodity", "Variety_Key", "origin_market", "date"]).reset_index(drop=True)
    orig["episode_id"] = [
        f"{st[:2].upper()}_{cm[:3].upper()}_{i+1:07d}"
        for i, (st, cm) in enumerate(zip(orig["State"], orig["Commodity"]))
    ]
    orig["origin_market_key"] = orig["State"] + "|" + orig["origin_market"]

    # Join static OSRM corridors
    cor_cols = ["State", "origin_market", "dest_market", "same_district", "euclid_km", "road_km", "truck_hours", "arrival_lag_days"]
    cands = orig.merge(corridors_df[cor_cols], on=["State", "origin_market"], how="inner")
    cands = cands.rename(columns={"arrival_lag_days": "tau_days"})
    counts["reachable_corridor_pairs"] = int(len(cands))

    # Strictly <= t - 1 destination exact-variety quote via merge_asof
    dest_lag_src = canon_df[["State", "Market", "Commodity", "Variety_Key", "Arrival_Date", "Modal_Price"]].rename(
        columns={"Market": "dest_market", "Arrival_Date": "dest_quote_date", "Modal_Price": "dest_lag_price"}
    ).sort_values("dest_quote_date")

    cands = pd.merge_asof(
        cands.sort_values("lag_deadline"),
        dest_lag_src,
        left_on="lag_deadline",
        right_on="dest_quote_date",
        by=["State", "dest_market", "Commodity", "Variety_Key"],
        direction="backward",
    )
    cands["dest_lag_age"] = (cands["date"] - cands["dest_quote_date"]).dt.days
    cands = cands[(cands["dest_lag_age"] >= 1) & (cands["dest_lag_age"] <= max_lag_age)].copy()
    cands["lag_spread"] = cands["dest_lag_price"] - cands["origin_lag_price"]
    counts["corridor_pairs_with_dest_lag_1_7d"] = int(len(cands))
    counts["episodes_with_dest_lag_1_7d"] = int(cands["episode_id"].nunique())

    # Leak-free Top-K shortlist strictly using lag_spread (> 100), road_km, dest_market
    cands = cands[cands["lag_spread"] > min_lag_spread].copy()
    counts["corridor_pairs_with_lag_spread_gt_100"] = int(len(cands))
    counts["episodes_with_lag_spread_gt_100"] = int(cands["episode_id"].nunique())

    cands = cands.sort_values(
        ["episode_id", "lag_spread", "road_km", "dest_market"],
        ascending=[True, False, True, True],
    )
    cands["_rk"] = cands.groupby("episode_id").cumcount()
    cands = cands[cands["_rk"] < top_k].drop(columns=["_rk"]).reset_index(drop=True)
    counts["shortlist_top5_rows"] = int(len(cands))
    counts["shortlist_val_episodes"] = int(cands.loc[cands["date"] <= "2025-05-31", "episode_id"].nunique())
    counts["shortlist_test_episodes"] = int(cands.loc[cands["date"] > "2025-05-31", "episode_id"].nunique())

    # Attach strictly < t historical reporting reliability & volatility features to shortlisted rows
    n = len(cands)
    ex14_v = np.empty(n, dtype=np.float64)
    ex28_v = np.empty(n, dtype=np.float64)
    any14_v = np.empty(n, dtype=np.float64)
    any28_v = np.empty(n, dtype=np.float64)
    cv28_v = np.empty(n, dtype=np.float64)
    cnt28_v = np.empty(n, dtype=np.float64)
    dow_v = np.empty(n, dtype=np.float64)

    cands["arrival_date"] = cands["date"] + pd.to_timedelta(cands["tau_days"], unit="D")
    arr_dow = cands["arrival_date"].dt.dayofweek.to_numpy()
    d_idx_arr = cands["date"].map(date_to_idx).to_numpy()

    for (st, cm, vk), grp_idx in cands.groupby(["State", "Commodity", "Variety_Key"], sort=False).groups.items():
        idx = np.asarray(list(grp_idx), dtype=np.int64)
        mkts, ex14, ex28, any14, any28, cv28, cnt28, dow_r = hist_lookup[(st, cm, vk)]
        m2i = {m: k for k, m in enumerate(mkts)}
        j_cols = cands.loc[idx, "dest_market"].map(m2i).to_numpy(dtype=np.int64)
        t_rows = d_idx_arr[idx]
        w_arr = arr_dow[idx]
        ex14_v[idx] = ex14[t_rows, j_cols]
        ex28_v[idx] = ex28[t_rows, j_cols]
        any14_v[idx] = any14[t_rows, j_cols]
        any28_v[idx] = any28[t_rows, j_cols]
        cv28_v[idx] = cv28[t_rows, j_cols]
        cnt28_v[idx] = cnt28[t_rows, j_cols]
        dow_v[idx] = dow_r[w_arr, t_rows, j_cols]

    cands["dest_exact_rep_14d"] = ex14_v
    cands["dest_exact_rep_28d"] = ex28_v
    cands["dest_any_rep_14d"] = any14_v
    cands["dest_any_rep_28d"] = any28_v
    cands["dest_price_cv_28d"] = cv28_v
    cands["dest_obs_cnt_28d"] = cnt28_v
    cands["dest_dow_exact_rep_8w"] = dow_v

    # Physical freight (transport only) + statutory fee rate (applied on destination gross sale!)
    hp = np.where(cands["State"].to_numpy() == "Himachal Pradesh", params.hp_km_mult, 1.0)
    road = cands["road_km"].to_numpy(dtype=np.float64)
    euc = cands["euclid_km"].to_numpy(dtype=np.float64)
    cands["freight_road"] = params.freight_base + params.freight_per_km * hp * road
    cands["freight_euclid"] = params.freight_base + params.freight_per_km * hp * params.euclid_circuity_ref * euc

    fee_map = fee_params_df.set_index(["State", "Commodity"])["statutory_seller_fee_pct"].to_dict()
    raw_fee_r = np.array([fee_map.get((st, cm), 0.015) for st, cm in zip(cands["State"], cands["Commodity"])], dtype=np.float64)
    cands["fee_rate"] = np.where(cands["same_district"].to_numpy(dtype=bool), 0.0, raw_fee_r)
    cands["spoil_ref_0"] = spoil_frac_ref(cands["Commodity"].to_numpy(), cands["truck_hours"].to_numpy(dtype=np.float64), np.zeros(n))

    # Climatology (< 2025-01-01 ONLY sensitivity)
    if clim_df is not None and len(clim_df) > 0:
        cands["month"] = cands["date"].dt.month
        cands = cands.merge(clim_df, on=["State", "month"], how="left").drop(columns=["month"])
        cands["clim_tmax_2024"] = cands["clim_tmax_2024"].fillna(20.0)
        cands["clim_rh_2024"] = cands["clim_rh_2024"].fillna(65.0)
        cands["clim_rain_2024"] = cands["clim_rain_2024"].fillna(0.0)
    else:
        cands["clim_tmax_2024"] = 20.0
        cands["clim_rh_2024"] = 65.0
        cands["clim_rain_2024"] = 0.0

    # Attach settlement-only outcomes on arrival_date + {0, 1, 2}
    exact_settle = canon_df[["State", "Market", "Commodity", "Variety_Key", "Arrival_Date", "Modal_Price", "Min_Price"]].rename(
        columns={"Market": "dest_market"}
    )
    any_settle = (
        canon_df.groupby(["State", "Market", "Commodity", "Arrival_Date"], as_index=False)
        .agg(any_min=("Min_Price", "min"))
        .rename(columns={"Market": "dest_market"})
    )

    cands["_row_order"] = np.arange(len(cands))
    for offset in (0, 1, 2):
        key_df = cands[["_row_order", "State", "dest_market", "Commodity", "Variety_Key"]].copy()
        key_df["Arrival_Date"] = cands["arrival_date"] + pd.Timedelta(days=offset)
        m_ex = key_df.merge(
            exact_settle,
            on=["State", "dest_market", "Commodity", "Variety_Key", "Arrival_Date"],
            how="left",
        ).sort_values("_row_order")
        cands[f"settle_dest_modal_d{offset}"] = m_ex["Modal_Price"].to_numpy(dtype=np.float64)
        cands[f"settle_dest_min_d{offset}"] = m_ex["Min_Price"].to_numpy(dtype=np.float64)

        m_an = key_df[["_row_order", "State", "dest_market", "Commodity", "Arrival_Date"]].merge(
            any_settle,
            on=["State", "dest_market", "Commodity", "Arrival_Date"],
            how="left",
        ).sort_values("_row_order")
        cands[f"settle_any_min_d{offset}"] = m_an["any_min"].to_numpy(dtype=np.float64)

    cands = cands.drop(columns=["_row_order", "lag_deadline"])

    # Conflicting duplicate audit on shortlisted rows
    if len(bad_conf_df) > 0:
        conflict_set = set(zip(bad_conf_df["State"], bad_conf_df["Market"], bad_conf_df["Commodity"], bad_conf_df["Arrival_Date"].dt.strftime("%Y-%m-%d")))
        odate = cands["date"].dt.strftime("%Y-%m-%d")
        qdate = cands["dest_quote_date"].dt.strftime("%Y-%m-%d")
        oqdate = cands["origin_quote_date"].dt.strftime("%Y-%m-%d")
        hit = np.array([
            ((s, om, c, od) in conflict_set) or ((s, dm, c, qd) in conflict_set) or ((s, om, c, oqd) in conflict_set)
            for s, om, dm, c, od, qd, oqd in zip(
                cands["State"], cands["origin_market"], cands["dest_market"], cands["Commodity"], odate, qdate, oqdate
            )
        ])
        cands["touches_conflicting_dup"] = hit
        counts["shortlist_rows_touching_conflicting_dup"] = int(hit.sum())
        counts["shortlist_episodes_touching_conflicting_dup"] = int(cands.loc[hit, "episode_id"].nunique())
    else:
        cands["touches_conflicting_dup"] = False
        counts["shortlist_rows_touching_conflicting_dup"] = 0
        counts["shortlist_episodes_touching_conflicting_dup"] = 0

    return cands, counts


def build_2024_climatology(root: Path) -> Tuple[pd.DataFrame, dict]:
    """Compute strictly < 2025-01-01 ERA5 state-month climatology from tracked weather + coordinates."""
    coords = pd.read_parquet(root / "data/processed/mandi_coordinates.parquet", columns=["State", "Market", "lat", "lon"]).drop_duplicates(["State", "Market"]).copy()
    coords["grid_lat"] = coords["lat"].round(1)
    coords["grid_lon"] = coords["lon"].round(1)
    st_grids = coords[["State", "grid_lat", "grid_lon"]].drop_duplicates()

    wx = pd.read_parquet(root / "data/processed/mandi_weather_2024_2026.parquet")
    wx["date"] = pd.to_datetime(wx["date"])
    wx_2024 = wx[wx["date"] < pd.Timestamp("2025-01-01")].copy()
    wx_2024["month"] = wx_2024["date"].dt.month
    m_2024 = st_grids.merge(wx_2024, on=["grid_lat", "grid_lon"], how="inner")
    clim = m_2024.groupby(["State", "month"], as_index=False).agg(
        clim_tmax_2024=("era5_tmax", "mean"),
        clim_rh_2024=("era5_rh_mean", "mean"),
        clim_rain_2024=("era5_rain_mm", "mean"),
    )

    wx_post = wx[(wx["date"] >= "2025-01-01") & (wx["date"] <= "2026-04-08")]
    wx_audit = {
        "weather_rows_2025_2026": int(len(wx_post)),
        "weather_rain_fc_equals_era5": int(np.isclose(wx_post["fc_rain_mm"], wx_post["era5_rain_mm"], equal_nan=False).sum()),
        "weather_rh_fc_equals_era5_1pct": int((np.abs(wx_post["fc_rh_mean"] - wx_post["era5_rh_mean"]) <= 1.0).sum()),
    }
    return clim, wx_audit


def build(root: Path = ROOT) -> pd.DataFrame:
    raw = pd.read_parquet(root / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet")
    cor = pd.read_parquet(root / "data/processed/osrm_corridor_matrix.parquet")
    fees = pd.read_csv(root / "data/processed/state_apmc_and_loss_parameters.csv")
    clim_df, wx_audit = build_2024_climatology(root)

    cands, counts = build_lagged_candidates_from_frames(
        raw_df=raw,
        corridors_df=cor,
        fee_params_df=fees,
        clim_df=clim_df,
        grade_explicit=False,
        min_origin_date="2025-01-01",
        max_origin_date="2026-04-08",
    )
    counts.update(wx_audit)

    out_dir = root / "revision" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cleaning_counts.json").write_text(json.dumps(counts, indent=2))
    build_feature_availability_table().to_csv(out_dir / "feature_availability_table.csv", index=False)
    cands.to_parquet(out_dir / "lagged_candidates.parquet", index=False)
    print(json.dumps(counts, indent=2))
    print("wrote lagged_candidates.parquet:", len(cands), "rows,", cands["episode_id"].nunique(), "episodes")
    return cands


if __name__ == "__main__":
    build()
