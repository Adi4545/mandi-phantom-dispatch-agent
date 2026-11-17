"""Vectorized zero-leakage episode and candidate-corridor builder for MandiGuard.

Builds:
  - data/processed/episodes_6state.parquet (all active origin lots across 2024-01-01..2026-04-08)
  - data/processed/candidates_6state.parquet (all reachable corridors with screen_spread > hurdle)
  - data/processed/episodes_hp_apple.parquet & candidates_hp_apple.parquet (grade-explicit 2025-2026)
  - data/manifests/data_provenance_manifest.json (complete SHA-256 provenance)

Enforces strict causal <= t feature & forecast weather indexing (zero future price or ERA5 leakage).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from src.evaluation.payoff_model import PayoffParams, compute_realized_dispatch_outcome
from src.models.arrival_forecaster import COMMODITY_TO_ID, STATE_TO_ID
from src.utils.leakage import load_config


def canonicalize_variety(commodity: str, variety: str) -> str:
    v0 = " ".join(str(variety).strip().split())
    vl = v0.lower()
    if vl in {commodity.lower(), "other", "faq", ""}:
        return "Standard"
    if vl in {"desi", "deshi"}:
        return "Desi"
    return v0


def _causal_trailing_mean(arr: np.ndarray, valid_mask: np.ndarray, win: int) -> np.ndarray:
    """Strictly causal rolling mean over [t - win + 1, t] along axis 0."""
    df_v = pd.DataFrame(np.where(valid_mask, arr, np.nan))
    return df_v.rolling(win, min_periods=1).mean().to_numpy(dtype=np.float64)


def _causal_dow_open_rate(obs_bool: np.ndarray, dates_idx: pd.DatetimeIndex, lag_days: int) -> np.ndarray:
    """For decision day t and corridor lag tau, historical open rate on weekday (t + tau) <= t."""
    n_days, n_mkts = obs_bool.shape
    out = np.full((n_days, n_mkts), 0.5, dtype=np.float64)
    dows = dates_idx.dayofweek.to_numpy()
    # Precompute for each weekday w in 0..6 the trailing 12-occurrence smoothed open rate <= t
    dow_rates = np.full((7, n_days, n_mkts), 0.5, dtype=np.float64)
    for w in range(7):
        w_mask = dows == w
        w_rows = obs_bool[w_mask].astype(np.float64)
        # On weekday w itself, causal up to & including today t (since on day t we know today's report status at end-of-day or before? Wait:
        # At decision time t, destination's weekday rate for arrival day t+tau (which is != t since tau in {1,2,3}) only uses days <= t!)
        if len(w_rows) > 0:
            roll_sum = pd.DataFrame(w_rows).rolling(12, min_periods=1).sum().to_numpy()
            roll_cnt = np.minimum(np.arange(1, len(w_rows) + 1)[:, None], 12.0)
            # Laplace smoothing (k + 1) / (n + 2)
            smoothed = (roll_sum + 1.0) / (roll_cnt + 2.0)
            # Forward-fill this weekday's latest rate across non-w days strictly forward
            tmp = np.full((n_days, n_mkts), np.nan, dtype=np.float64)
            tmp[w_mask] = smoothed
            dow_rates[w] = pd.DataFrame(tmp).ffill().fillna(0.5).to_numpy(dtype=np.float64)
    arr_dows = (dows + lag_days) % 7
    for t in range(n_days):
        out[t] = dow_rates[arr_dows[t], t]
    return out


def build_panel_tables(
    raw_df: pd.DataFrame,
    coords_df: pd.DataFrame,
    corridors_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    min_date: str,
    max_eval_origin_date: str,
    max_data_date: str,
    grade_explicit: bool = False,
    hurdle_inr: float = 100.0,
    max_cands_keep: int = 12,
    payoff_params: PayoffParams = PayoffParams(),
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Construct episode metadata and enriched candidate-corridor records."""
    df = raw_df.copy()
    df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"])
    df = df[(df["Arrival_Date"] >= min_date) & (df["Arrival_Date"] <= max_data_date)].copy()
    df["Var_Canon"] = [canonicalize_variety(c, v) for c, v in zip(df["Commodity"], df["Variety"])]
    if grade_explicit:
        df["Variety_Key"] = df["Var_Canon"] + " | " + df["Grade"].astype(str).str.strip()
    else:
        df["Variety_Key"] = df["Var_Canon"]

    # Map markets -> weather grid
    m_coord = coords_df[["State", "Market", "lat", "lon"]].drop_duplicates(["State", "Market"]).copy()
    m_coord["grid_lat"] = m_coord["lat"].round(1)
    m_coord["grid_lon"] = m_coord["lon"].round(1)

    all_dates = pd.date_range(min_date, max_data_date, freq="D")
    n_days = len(all_dates)
    date_to_idx = {d: i for i, d in enumerate(all_dates)}
    max_origin_idx = date_to_idx[pd.Timestamp(max_eval_origin_date)]

    # Index weather grids cleanly by (grid_lat, grid_lon) -> (n_days, 8)
    w_sub = weather_df[(weather_df["date"] >= min_date) & (weather_df["date"] <= max_data_date)].copy()
    w_cols = ["era5_tmax", "era5_tmin", "era5_rain_mm", "era5_rh_mean", "fc_tmax", "fc_tmin", "fc_rain_mm", "fc_rh_mean"]
    grid_weather: Dict[Tuple[float, float], np.ndarray] = {}
    for (glat, glon), grp in w_sub.groupby(["grid_lat", "grid_lon"]):
        g2 = grp.set_index("date").reindex(all_dates)[w_cols].ffill().bfill()
        grid_weather[(float(glat), float(glon))] = g2.to_numpy(dtype=np.float64)

    ep_chunks: List[pd.DataFrame] = []
    cand_chunks: List[pd.DataFrame] = []
    ep_counter = 0

    for state, st_df in df.groupby("State", sort=True):
        st_mkts = sorted(set(st_df["Market"].unique()) & set(m_coord[m_coord["State"] == state]["Market"].unique()))
        if len(st_mkts) < 2:
            continue
        mkt_to_idx = {m: i for i, m in enumerate(st_mkts)}
        n_mkts = len(st_mkts)

        # Build weather tensor for this state's markets: (n_days, n_mkts, 8)
        st_mcoord = m_coord[m_coord["State"] == state].set_index("Market")
        w_tensor = np.zeros((n_days, n_mkts, 8), dtype=np.float64)
        for m_name, m_i in mkt_to_idx.items():
            glat = float(st_mcoord.at[m_name, "grid_lat"])
            glon = float(st_mcoord.at[m_name, "grid_lon"])
            w_tensor[:, m_i, :] = grid_weather[(glat, glon)]

        # Pre-compute any-commodity yard-open matrix (n_days, n_mkts)
        st_any = st_df[["Arrival_Date", "Market"]].drop_duplicates()
        any_open_mat = np.zeros((n_days, n_mkts), dtype=bool)
        r_idx = st_any["Arrival_Date"].map(date_to_idx).to_numpy()
        c_idx = st_any["Market"].map(mkt_to_idx).dropna().astype(int).to_numpy()
        valid_mask_idx = st_any["Market"].isin(mkt_to_idx).to_numpy()
        any_open_mat[r_idx[valid_mask_idx], c_idx] = True

        # Corridor lookup for this state
        st_cor = corridors_df[
            (corridors_df["State"] == state)
            & corridors_df["origin_market"].isin(mkt_to_idx)
            & corridors_df["dest_market"].isin(mkt_to_idx)
        ].copy()
        if len(st_cor) == 0:
            continue
        cor_orig_i = st_cor["origin_market"].map(mkt_to_idx).to_numpy()
        cor_dest_j = st_cor["dest_market"].map(mkt_to_idx).to_numpy()
        cor_lag = st_cor["arrival_lag_days"].to_numpy(dtype=np.int32)
        cor_rkm = st_cor["road_km"].to_numpy(dtype=np.float64)
        cor_ekm = st_cor["euclid_km"].to_numpy(dtype=np.float64)
        cor_thrs = st_cor["truck_hours"].to_numpy(dtype=np.float64)
        cor_sdist = st_cor["same_district"].to_numpy(dtype=bool)
        n_cor = len(st_cor)

        # Map each origin market to indices of its outgoing corridors
        out_cors_by_orig: List[np.ndarray] = [np.flatnonzero(cor_orig_i == m_i) for m_i in range(n_mkts)]

        for comm, cm_df in st_df.groupby("Commodity", sort=True):
            # Headline screen board price per (date, market): daily median modal across all varieties of comm, causal ffill(7)
            cm_daily = cm_df.groupby(["Arrival_Date", "Market"], as_index=False).agg(
                modal=("Modal_Price", "median"),
                min_p=("Min_Price", "min"),
            )
            cm_modal_piv = cm_daily.pivot(index="Arrival_Date", columns="Market", values="modal").reindex(index=all_dates, columns=st_mkts)
            cm_min_piv = cm_daily.pivot(index="Arrival_Date", columns="Market", values="min_p").reindex(index=all_dates, columns=st_mkts)
            screen_board_mat = cm_modal_piv.ffill(limit=7).to_numpy(dtype=np.float64)
            any_var_min_mat = cm_min_piv.to_numpy(dtype=np.float64)

            # Causal state hub 7d return (median across markets trading comm <= t)
            hub_med_series = cm_modal_piv.median(axis=1).ffill(limit=7)
            hub_ret_7d = ((hub_med_series - hub_med_series.shift(7)) / hub_med_series.shift(7)).fillna(0.0).clip(-0.5, 0.5).to_numpy()

            for vkey, v_df in cm_df.groupby("Variety_Key", sort=True):
                if v_df["Market"].nunique() < 2:
                    continue
                agg_dict = {"Modal_Price": ("Modal_Price", "median"), "Min_Price": ("Min_Price", "median")}
                if "arrival_tonnes" in v_df.columns:
                    agg_dict["arrival_tonnes"] = ("arrival_tonnes", "sum")
                vd = v_df.groupby(["Arrival_Date", "Market"], as_index=False).agg(**agg_dict)

                mod_piv = vd.pivot(index="Arrival_Date", columns="Market", values="Modal_Price").reindex(index=all_dates, columns=st_mkts)
                min_piv = vd.pivot(index="Arrival_Date", columns="Market", values="Min_Price").reindex(index=all_dates, columns=st_mkts)
                ton_mat = (
                    vd.pivot(index="Arrival_Date", columns="Market", values="arrival_tonnes")
                    .reindex(index=all_dates, columns=st_mkts)
                    .to_numpy(dtype=np.float64)
                    if "arrival_tonnes" in vd.columns
                    else np.full((n_days, n_mkts), np.nan)
                )

                mod_mat = mod_piv.to_numpy(dtype=np.float64)
                min_mat = min_piv.to_numpy(dtype=np.float64)
                obs_mask = np.isfinite(mod_mat) & (mod_mat > 0)

                # Causal <= t destination features across (n_days, n_mkts)
                ff14_df = mod_piv.ffill(limit=14)
                last_p_mat = ff14_df.to_numpy(dtype=np.float64)

                # Age in days since last exact-variety observation <= t
                obs_idx_mat = np.where(obs_mask, np.arange(n_days)[:, None], np.nan)
                last_obs_idx = pd.DataFrame(obs_idx_mat).ffill().to_numpy(dtype=np.float64)
                age_mat = np.where(np.isfinite(last_obs_idx), np.arange(n_days)[:, None] - last_obs_idx, 99.0)
                age_mat = np.where(age_mat <= 14.0, age_mat, 99.0)

                # Causal returns & volatility <= t
                ret_1d = ((ff14_df - ff14_df.shift(1)) / ff14_df.shift(1)).fillna(0.0).clip(-0.5, 0.5).to_numpy()
                ret_3d = ((ff14_df - ff14_df.shift(3)) / ff14_df.shift(3)).fillna(0.0).clip(-0.5, 0.5).to_numpy()
                ret_7d = ((ff14_df - ff14_df.shift(7)) / ff14_df.shift(7)).fillna(0.0).clip(-0.5, 0.5).to_numpy()
                ret_14d = ((ff14_df - ff14_df.shift(14)) / ff14_df.shift(14)).fillna(0.0).clip(-0.5, 0.5).to_numpy()
                vol_14d = pd.DataFrame(ret_1d).rolling(14, min_periods=2).std().fillna(0.04).clip(0.0, 0.4).to_numpy()
                med_30d = ff14_df.rolling(30, min_periods=3).median().to_numpy()
                lvl_ratio_30d = np.where(np.isfinite(med_30d) & (med_30d > 0), np.clip(last_p_mat / med_30d, 0.4, 2.5), 1.0)

                open_prob_14d = pd.DataFrame(obs_mask.astype(np.float64)).rolling(14, min_periods=1).mean().to_numpy()
                intra_raw = np.where(obs_mask, np.clip((mod_mat - min_mat) / mod_mat, 0.0, 0.7), np.nan)
                intra_14d = pd.DataFrame(intra_raw).ffill(limit=14).rolling(14, min_periods=1).mean().fillna(0.10).to_numpy()

                # Precompute weekday open rate for lag 1, 2, 3
                dow_by_lag = {lag: _causal_dow_open_rate(obs_mask, all_dates, lag) for lag in (1, 2, 3)}

                # Iterate over days t where at least 1 origin market traded exact (comm, vkey) and needs >= 20 days warmup
                active_days = np.flatnonzero(obs_mask[: max_origin_idx + 1].any(axis=1))
                active_days = active_days[active_days >= 14]  # min 14d causal history

                ep_rows_local = []
                cand_rows_local = []

                for t in active_days:
                    dt_t = all_dates[t]
                    month_angle = 2.0 * np.pi * (dt_t.dayofyear / 365.25)
                    m_sin = float(np.sin(month_angle))
                    m_cos = float(np.cos(month_angle))

                    orig_mkts = np.flatnonzero(obs_mask[t])
                    for m_i in orig_mkts:
                        ep_counter += 1
                        ep_id = f"{state[:2].upper()}_{comm[:3].upper()}_{ep_counter:07d}"
                        p_loc = float(mod_mat[t, m_i])
                        c_idxs = out_cors_by_orig[m_i]

                        has_shortlist = False
                        if len(c_idxs) > 0:
                            dest_js = cor_dest_j[c_idxs]
                            scr_ps = screen_board_mat[t, dest_js]
                            scr_spreads = scr_ps - p_loc
                            valid_scr = np.isfinite(scr_spreads) & (scr_spreads > hurdle_inr)
                            if valid_scr.any():
                                cand_c_idxs = c_idxs[valid_scr]
                                cand_spreads = scr_spreads[valid_scr]
                                # Sort descending by screen_spread and keep top max_cands_keep
                                order = np.argsort(-cand_spreads)[:max_cands_keep]
                                cand_c_idxs = cand_c_idxs[order]
                                has_shortlist = True

                                for c_idx_cor in cand_c_idxs:
                                    j = int(cor_dest_j[c_idx_cor])
                                    lag = int(cor_lag[c_idx_cor])
                                    t_arr = t + lag
                                    dt_arr = all_dates[t_arr]

                                    scr_p = float(screen_board_mat[t, j])
                                    d_ref = float(last_p_mat[t, j]) if np.isfinite(last_p_mat[t, j]) else np.nan
                                    d_age = float(age_mat[t, j])
                                    d_op = float(open_prob_14d[t, j])
                                    d_dow = float(dow_by_lag[lag][t, j])
                                    d_intra = float(intra_14d[t, j])

                                    # Causal day-t weather forecast along corridor (origin & dest at date t ONLY)
                                    fc_tmax_r = float(max(w_tensor[t, m_i, 4], w_tensor[t, j, 4]))
                                    fc_rh_r = float(max(w_tensor[t, m_i, 7], w_tensor[t, j, 7]))
                                    fc_rain_r = float(max(w_tensor[t, m_i, 6], w_tensor[t, j, 6]))

                                    # Ground-truth ERA5 realized weather over transit [t, t + lag]
                                    era_slice = w_tensor[t : t_arr + 1, :, :4]
                                    era_tmax_r = float(max(era_slice[:, m_i, 0].max(), era_slice[:, j, 0].max()))
                                    era_rh_r = float(max(era_slice[:, m_i, 3].max(), era_slice[:, j, 3].max()))
                                    era_rain_r = float(max(era_slice[:, m_i, 2].max(), era_slice[:, j, 2].max()))

                                    # Ground-truth destination auction lookup at [t_arr, t_arr+1, t_arr+2]
                                    pm0, pmn0 = float(mod_mat[t_arr, j]), float(min_mat[t_arr, j])
                                    pm1 = float(mod_mat[t_arr + 1, j]) if t_arr + 1 < n_days else np.nan
                                    pmn1 = float(min_mat[t_arr + 1, j]) if t_arr + 1 < n_days else np.nan
                                    pm2 = float(mod_mat[t_arr + 2, j]) if t_arr + 2 < n_days else np.nan
                                    pmn2 = float(min_mat[t_arr + 2, j]) if t_arr + 2 < n_days else np.nan
                                    any_min0 = float(any_var_min_mat[t_arr, j])
                                    any_open0 = bool(any_open_mat[t_arr, j])

                                    out_phys = compute_realized_dispatch_outcome(
                                        state=state,
                                        commodity=comm,
                                        local_price=p_loc,
                                        road_km=float(cor_rkm[c_idx_cor]),
                                        truck_hours=float(cor_thrs[c_idx_cor]),
                                        same_district=bool(cor_sdist[c_idx_cor]),
                                        arrival_lag_days=lag,
                                        dest_exact_prices=(pm0, pmn0, pm1, pmn1, pm2, pmn2),
                                        dest_any_var_min_d0=any_min0,
                                        dest_any_open_d0=any_open0,
                                        route_tmax=era_tmax_r,
                                        route_rh=era_rh_r,
                                        route_rain=era_rain_r,
                                        params=payoff_params,
                                    )

                                    tgt_ret = ((pm0 - d_ref) / d_ref) if (np.isfinite(pm0) and np.isfinite(d_ref) and d_ref > 0) else np.nan

                                    cand_rows_local.append(
                                        {
                                            "episode_id": ep_id,
                                            "State": state,
                                            "Commodity": comm,
                                            "Variety_Key": vkey,
                                            "date": dt_t,
                                            "arrival_date": dt_arr,
                                            "origin_market": st_mkts[m_i],
                                            "origin_market_key": f"{state}|{st_mkts[m_i]}",
                                            "dest_market": st_mkts[j],
                                            "local_price": p_loc,
                                            "screen_dest_price": scr_p,
                                            "screen_spread": scr_p - p_loc,
                                            "dest_ref_price": d_ref,
                                            "tau_days": lag,
                                            "road_km": float(cor_rkm[c_idx_cor]),
                                            "euclid_km": float(cor_ekm[c_idx_cor]),
                                            "truck_hours": float(cor_thrs[c_idx_cor]),
                                            "same_district": bool(cor_sdist[c_idx_cor]),
                                            "dest_age_days": d_age,
                                            "dest_ret_1d": float(ret_1d[t, j]),
                                            "dest_ret_3d": float(ret_3d[t, j]),
                                            "dest_ret_7d": float(ret_7d[t, j]),
                                            "dest_ret_14d": float(ret_14d[t, j]),
                                            "dest_vol_14d": float(vol_14d[t, j]),
                                            "dest_intra_spread_14d": d_intra,
                                            "dest_open_prob_14d": d_op,
                                            "dest_dow_open_rate": d_dow,
                                            "state_hub_ret_7d": float(hub_ret_7d[t]),
                                            "dest_level_ratio_30d": float(lvl_ratio_30d[t, j]),
                                            "arrival_dow": int(dt_arr.dayofweek),
                                            "month_sin": m_sin,
                                            "month_cos": m_cos,
                                            "commodity_code": COMMODITY_TO_ID[comm],
                                            "state_code": STATE_TO_ID[state],
                                            "route_fc_tmax": fc_tmax_r,
                                            "route_fc_rh": fc_rh_r,
                                            "route_fc_rain": fc_rain_r,
                                            "route_era5_tmax": era_tmax_r,
                                            "route_era5_rh": era_rh_r,
                                            "route_era5_rain": era_rain_r,
                                            "target_ret": tgt_ret,
                                            "dest_modal_d0": pm0,
                                            "dest_min_d0": pmn0,
                                            "dest_modal_d1": pm1,
                                            "dest_min_d1": pmn1,
                                            "dest_modal_d2": pm2,
                                            "dest_min_d2": pmn2,
                                            "dest_any_var_min_d0": any_min0,
                                            "dest_any_open_d0": any_open0,
                                            "real_delta_net_inr": out_phys["delta_net_inr"],
                                            "real_open_d0_delta_net_inr": out_phys["open_d0_delta_net_inr"],
                                            "real_freight_inr": out_phys["freight_inr"],
                                            "real_spoil_frac": out_phys["spoil_frac"],
                                            "real_wait_days": out_phys["wait_days"],
                                            "real_closed_or_no_variety_trap": out_phys["closed_or_no_variety_trap"],
                                            "real_no_exact_variety_3d": out_phys["no_exact_variety_3d"],
                                            "real_arrival_price_dropped": out_phys["arrival_price_dropped"],
                                            "real_outcome_type": out_phys["outcome_type"],
                                        }
                                    )

                        ep_rows_local.append(
                            {
                                "episode_id": ep_id,
                                "State": state,
                                "Commodity": comm,
                                "Variety_Key": vkey,
                                "date": dt_t,
                                "origin_market": st_mkts[m_i],
                                "origin_market_key": f"{state}|{st_mkts[m_i]}",
                                "local_price": p_loc,
                                "arrival_tonnes": float(ton_mat[t, m_i]) if np.isfinite(ton_mat[t, m_i]) else np.nan,
                                "has_screen_shortlist": has_shortlist,
                                "origin_era5_tmax": float(w_tensor[t, m_i, 0]),
                                "origin_era5_rain": float(w_tensor[t, m_i, 2]),
                            }
                        )

                if ep_rows_local:
                    ep_chunks.append(pd.DataFrame(ep_rows_local))
                if cand_rows_local:
                    cand_chunks.append(pd.DataFrame(cand_rows_local))

    episodes_df = pd.concat(ep_chunks, ignore_index=True) if ep_chunks else pd.DataFrame()
    cands_df = pd.concat(cand_chunks, ignore_index=True) if cand_chunks else pd.DataFrame()
    return episodes_df, cands_df


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root)

    panel_raw = pd.read_parquet(root / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet")
    coords_df = pd.read_parquet(root / "data/processed/mandi_coordinates.parquet")
    corridors_df = pd.read_parquet(root / "data/processed/osrm_corridor_matrix.parquet")
    weather_df = pd.read_parquet(root / "data/processed/mandi_weather_2024_2026.parquet")

    print("[Builder] Building 6-state TOP+Apple episodes & candidates (2024-01-01..2026-04-08)...")
    ep_6, cand_6 = build_panel_tables(
        raw_df=panel_raw,
        coords_df=coords_df,
        corridors_df=corridors_df,
        weather_df=weather_df,
        min_date="2024-01-01",
        max_eval_origin_date="2026-04-08",
        max_data_date="2026-04-13",
        grade_explicit=False,
        hurdle_inr=cfg["agent_defaults"]["screen_hurdle_inr_qtl"],
        max_cands_keep=12,
    )
    ep_6.to_parquet(root / "data/processed/episodes_6state.parquet", index=False)
    cand_6.to_parquet(root / "data/processed/candidates_6state.parquet", index=False)
    print(f"  6-State: {len(ep_6):,} episodes ({ep_6['has_screen_shortlist'].sum():,} active shortlist) | {len(cand_6):,} candidate pairs")

    print("[Builder] Building Grade-Explicit HP Apple panel (2025-11-07..2026-08-27)...")
    apple_raw = pd.read_csv(root / "data/raw/hp_apple_daily_2025_2026.csv").rename(
        columns={
            "state": "State",
            "district": "District",
            "market": "Market",
            "commodity": "Commodity",
            "variety": "Variety",
            "grade": "Grade",
            "arrival_date": "Arrival_Date",
            "min_price": "Min_Price",
            "max_price": "Max_Price",
            "modal_price": "Modal_Price",
        }
    )
    ep_ap, cand_ap = build_panel_tables(
        raw_df=apple_raw,
        coords_df=coords_df,
        corridors_df=corridors_df,
        weather_df=weather_df,
        min_date="2025-11-07",
        max_eval_origin_date="2026-08-27",
        max_data_date="2026-09-01",
        grade_explicit=True,
        hurdle_inr=cfg["agent_defaults"]["screen_hurdle_inr_qtl"],
        max_cands_keep=12,
    )
    ep_ap.to_parquet(root / "data/processed/episodes_hp_apple.parquet", index=False)
    cand_ap.to_parquet(root / "data/processed/candidates_hp_apple_grade.parquet", index=False)
    print(f"  HP Apple Grade: {len(ep_ap):,} episodes ({ep_ap['has_screen_shortlist'].sum():,} active shortlist) | {len(cand_ap):,} candidate pairs")

    def sha256(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    prov = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "6state_episodes": int(len(ep_6)),
        "6state_shortlisted_episodes": int(ep_6["has_screen_shortlist"].sum()),
        "6state_candidate_rows": int(len(cand_6)),
        "hp_apple_episodes": int(len(ep_ap)),
        "hp_apple_shortlisted_episodes": int(ep_ap["has_screen_shortlist"].sum()),
        "hp_apple_candidate_rows": int(len(cand_ap)),
        "sha256": {
            "episodes_6state": sha256(root / "data/processed/episodes_6state.parquet"),
            "candidates_6state": sha256(root / "data/processed/candidates_6state.parquet"),
            "episodes_hp_apple": sha256(root / "data/processed/episodes_hp_apple.parquet"),
            "candidates_hp_apple_grade": sha256(root / "data/processed/candidates_hp_apple_grade.parquet"),
        },
    }
    (root / "data/manifests/data_provenance_manifest.json").write_text(json.dumps(prov, indent=2))
    print("=== DATA PROVENANCE MANIFEST SAVED ===")
    print(json.dumps(prov, indent=2))


if __name__ == "__main__":
    main()
