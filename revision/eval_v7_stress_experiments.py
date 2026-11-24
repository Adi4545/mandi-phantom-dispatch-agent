"""Phase 6 Audit-Driven Stress & Verification Experiments for MandiGuard (Revision v7+).

Produces six deterministic verification tables under `revision/results/`:
  - v7_exp1_latency_t2.csv            : Strict <= t - 2 upload-latency rebuild (ages 2..3 & 2..4) + R=2,000 CIs
  - v7_exp2_bio_s6_condmar.csv        : Schedule #7 biological clock x Smallholder S6 x Stochastic Cond-MAR x blind_wait
  - v7_exp3_manski_and_open.csv       : Coupled/decoupled Manski [WC, BC] bounds, cross-crop MNAR, 2D thin/thick, origin symmetry, pre-choice all-open
  - v7_exp4_ml_pareto_and_formula.csv : Spillover-purged val_171, clean <=t-1 ML/OR/T1..T4 Pareto, cv28==0 fix, ratio-argmax, top_k=None
  - v7_exp5_hygiene_sutva_inference.csv : 369-outlier clean, grade-explicit, exact-all5, SUTVA crowding, 166-mkt NASA/CPI decade, CGM+stud+Webb6+joint-val-test
  - v7_exp_summary.json               : Key invariant assertions & scalar audit counts
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge

from revision.build_variant import BASE_SPOIL_24H, build_lagged_candidates_from_frames, compute_cleaning_funnel
from revision.es10 import es10
from revision.eval_a10 import rr_abstain_score
from revision.eval_a18 import (
    score_ev_rt_min,
    score_rt2f_dow,
    score_rt2f_min,
    score_safe_ev_phys,
    score_safe_ev_sunk,
)
from revision.eval_run import (
    compute_decision_features,
    find_val_matched_threshold,
    pick_episode,
    settle_candidates,
    tune_threshold_on_val,
)
from revision.eval_v6 import get_2024_only_markets
from revision.eval_v7 import _extended_metrics_v7
from revision.stats_utils import (
    es_alpha,
    two_way_cgm_and_studentized_test,
    two_way_cluster_bootstrap_extended,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "revision" / "results"


# ---------------------------------------------------------------------------
# Shared Helpers
# ---------------------------------------------------------------------------
def _eval_policies_dict(
    df: pd.DataFrame,
    scores: Dict[str, Tuple[np.ndarray, np.ndarray]],
    ot: np.ndarray,
    y_override: np.ndarray | None = None,
) -> Dict[str, pd.DataFrame]:
    out = {}
    for pname, (sc, el) in scores.items():
        ch = pick_episode(df, sc, el)
        if y_override is not None:
            ch = ch.copy()
            ch["y_raw"] = y_override[ch["_i"].to_numpy()]
            ch["y"] = np.where(ch["eligible"].to_numpy(dtype=bool), ch["y_raw"], 0.0)
        out[pname] = ch
    return out


def _standard_val_calibrate(val: pd.DataFrame, kappa_star: float) -> dict:
    vf = compute_decision_features(val)
    age_v = (vf["age"] >= 1) & (vf["age"] <= 3)
    th_b2, vs_b2 = tune_threshold_on_val(val, vf, "net_road_fee", lambda ft: (ft["age"] >= 1) & (ft["age"] <= 3))
    tgt = float(vs_b2["dispatch_rate"])
    return {
        "th_b2": th_b2,
        "tgt": tgt,
        "m_act": find_val_matched_threshold(val, vf["net_road_fee"], age_v & (vf["rep14"] >= 0.50), tgt),
        "m_mg": find_val_matched_threshold(val, vf["net_road_fee_spoil"], age_v & (vf["rep14"] >= 0.50) & (vf["dow8"] >= 0.35), tgt),
        "m_rr": find_val_matched_threshold(val, rr_abstain_score(val, kappa_star), age_v, tgt),
        "m_safe": find_val_matched_threshold(val, score_safe_ev_sunk(val), age_v, tgt),
    }


def _score_core_subset(df: pd.DataFrame, th_b2: float, m_mg: float, kappa_star: float, m_rr: float, m_safe: float, min_age: int = 1, max_age: int = 3) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    f = compute_decision_features(df)
    age_g = (f["age"] >= min_age) & (f["age"] <= max_age)
    sc_rr = rr_abstain_score(df, kappa_star)
    sc_safe = score_safe_ev_sunk(df)
    sc_phys = score_safe_ev_phys(df)
    sc_rtmin = score_rt2f_min(df)
    sc_rtdow = score_rt2f_dow(df)
    return {
        "B1_lagged_screen": (f["lag_spread"], np.ones(len(df), dtype=bool)),
        "B2_age_matched": (f["net_road_fee"], age_g & (f["net_road_fee"] > th_b2)),
        "MG_matched": (f["net_road_fee_spoil"], age_g & (f["rep14"] >= 0.50) & (f["dow8"] >= 0.35) & (f["net_road_fee_spoil"] > m_mg)),
        "RR_Abstain_matched": (sc_rr, age_g & (sc_rr > m_rr)),
        "Safe_EV_Sunk_m0": (sc_safe, age_g & (sc_safe > 0.0)),
        "Safe_EV_Sunk_matched": (sc_safe, age_g & (sc_safe > m_safe)),
        "Safe_EV_Phys_m0": (sc_phys, age_g & (sc_phys > 0.0)),
        "RT_2F_Min_m0": (sc_rtmin, age_g & (sc_rtmin > 0.0)),
        "RT_2F_Dow_m0": (sc_rtdow, age_g & (sc_rtdow > 0.0)),
    }


def _attach_full_era5(df: pd.DataFrame, coords: pd.DataFrame, wx_df: pd.DataFrame, grid_step: float = 0.1) -> pd.DataFrame:
    out = df.copy()
    c_map = coords[["State", "Market", "lat", "lon"]].drop_duplicates(["State", "Market"]).copy()
    inv = round(1.0 / grid_step)
    c_map["grid_lat"] = (c_map["lat"] * inv).round() / inv
    c_map["grid_lon"] = (c_map["lon"] * inv).round() / inv
    c_map = c_map.rename(columns={"Market": "dest_market"})[["State", "dest_market", "grid_lat", "grid_lon"]]
    out = out.merge(c_map, on=["State", "dest_market"], how="left")
    wx = wx_df[["grid_lat", "grid_lon", "date", "era5_tmax", "era5_tmin", "era5_rh_mean", "era5_rain_mm"]].copy()
    wx["date"] = pd.to_datetime(wx["date"])
    wx = wx.drop_duplicates(["grid_lat", "grid_lon", "date"])
    arr_base = pd.to_datetime(out["arrival_date"])
    for d in (0, 1, 2):
        out[f"_arr_d{d}"] = arr_base + pd.Timedelta(days=d)
        sub_wx = wx.rename(
            columns={
                "date": f"_arr_d{d}",
                "era5_tmax": f"settle_era5_tmax_d{d}",
                "era5_tmin": f"settle_era5_tmin_d{d}",
                "era5_rh_mean": f"settle_era5_rh_d{d}",
                "era5_rain_mm": f"settle_era5_rain_d{d}",
            }
        )
        out = out.merge(sub_wx, on=["grid_lat", "grid_lon", f"_arr_d{d}"], how="left")
        if d == 0:
            cov = float(out["settle_era5_tmax_d0"].notna().mean() * 100.0)
            assert cov >= 95.0, f"Low weather coverage ({cov:.2f}%) at grid_step={grid_step}"
        out[f"settle_era5_tmax_d{d}"] = out[f"settle_era5_tmax_d{d}"].fillna(24.0)
        out[f"settle_era5_tmin_d{d}"] = out[f"settle_era5_tmin_d{d}"].fillna(16.0)
        out[f"settle_era5_rh_d{d}"] = out[f"settle_era5_rh_d{d}"].fillna(65.0)
        out[f"settle_era5_rain_d{d}"] = out[f"settle_era5_rain_d{d}"].fillna(0.0)
        out.drop(columns=[f"_arr_d{d}"], inplace=True)
    out.drop(columns=["grid_lat", "grid_lon"], inplace=True)
    return out


# ---------------------------------------------------------------------------
# Exp 6.1: Strict <= t - 2 Portal Latency Firewall
# ---------------------------------------------------------------------------
def run_exp1_latency_t2(raw_171: pd.DataFrame, cor: pd.DataFrame, fees: pd.DataFrame, kappa_star: float) -> Tuple[pd.DataFrame, dict]:
    # Counterfactual t-2 invariance assertion on synthetic slice
    sub_dates = raw_171[pd.to_datetime(raw_171["Arrival_Date"]).between("2025-05-01", "2025-07-25")].copy().reset_index(drop=True)
    t_star = pd.Timestamp("2025-07-15")
    base_s, _ = build_lagged_candidates_from_frames(
        sub_dates, cor, fees, clim_df=None, grade_explicit=False,
        min_origin_date="2025-06-15", max_origin_date="2025-07-20", lag_offset_days=2,
    )
    corrupt = sub_dates.copy()
    m_fut = pd.to_datetime(corrupt["Arrival_Date"]) >= (t_star - pd.Timedelta(days=1))
    corrupt.loc[m_fut, "Modal_Price"] = corrupt.loc[m_fut, "Modal_Price"] * 1.9 + 5000.0
    corrupt.loc[m_fut, "Max_Price"] = corrupt.loc[m_fut, "Max_Price"] * 2.0 + 6000.0
    corr_s, _ = build_lagged_candidates_from_frames(
        corrupt, cor, fees, clim_df=None, grade_explicit=False,
        min_origin_date="2025-06-15", max_origin_date="2025-07-20", lag_offset_days=2,
    )
    b_le = base_s[pd.to_datetime(base_s["date"]) <= t_star].reset_index(drop=True)
    c_le = corr_s[pd.to_datetime(corr_s["date"]) <= t_star].reset_index(drop=True)
    dec_cols = ["episode_id", "dest_market", "dest_lag_price", "origin_lag_price", "lag_spread", "dest_exact_rep_14d", "dest_exact_rep_28d", "dest_dow_exact_rep_8w", "dest_price_cv_28d"]
    pd.testing.assert_frame_equal(b_le[dec_cols], c_le[dec_cols])

    df_t2, cnt_t2 = build_lagged_candidates_from_frames(raw_171, cor, fees, clim_df=None, grade_explicit=False, lag_offset_days=2)
    df_t2["date"] = pd.to_datetime(df_t2["date"])
    y_t2, ot_t2 = settle_candidates(df_t2, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    df_t2["y"] = y_t2
    df_t2["_ot"] = ot_t2

    val_t2 = df_t2[df_t2["date"] <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    test_t2 = df_t2[df_t2["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    ot_test = test_t2["_ot"].to_numpy()
    vf = compute_decision_features(val_t2)
    tf = compute_decision_features(test_t2)

    rows = []
    boot_summary = {}
    for max_age_lbl, max_a in (("t2_age_2_3", 3), ("t2_age_2_4", 4)):
        age_v = (vf["age"] >= 2) & (vf["age"] <= max_a)
        age_t = (tf["age"] >= 2) & (tf["age"] <= max_a)
        th_b2, vs_b2 = tune_threshold_on_val(val_t2, vf, "net_road_fee", lambda ft, ma=max_a: (ft["age"] >= 2) & (ft["age"] <= ma))
        tgt = float(vs_b2["dispatch_rate"])
        m_mg = find_val_matched_threshold(val_t2, vf["net_road_fee_spoil"], age_v & (vf["rep14"] >= 0.50) & (vf["dow8"] >= 0.35), tgt)
        m_rr = find_val_matched_threshold(val_t2, rr_abstain_score(val_t2, kappa_star), age_v, tgt)
        m_safe = find_val_matched_threshold(val_t2, score_safe_ev_sunk(val_t2), age_v, tgt)

        sc_map = _score_core_subset(test_t2, th_b2, m_mg, kappa_star, m_rr, m_safe, min_age=2, max_age=max_a)
        chosen = _eval_policies_dict(test_t2, sc_map, ot_test)
        safe_disp = float(chosen["Safe_EV_Sunk_m0"]["eligible"].mean())
        th_b2_eq = find_val_matched_threshold(test_t2, tf["net_road_fee"], age_t, safe_disp)
        chosen["B2_eq_SafeM0"] = pick_episode(test_t2, tf["net_road_fee"], age_t & (tf["net_road_fee"] > th_b2_eq))

        bdf = chosen["B2_age_matched"][["episode_id", "date", "origin_market_key"]].copy()
        for p, ch in chosen.items():
            bdf[p] = ch["y"].to_numpy(dtype=np.float64)
            bdf[f"{p}_disp"] = ch["eligible"].to_numpy(dtype=bool)

        boots = {
            pa: two_way_cluster_bootstrap_extended(
                bdf, pa, "B2_age_matched", disp_col_a=f"{pa}_disp", disp_col_b="B2_age_matched_disp",
                mandi_col="origin_market_key", reps=2000, seed=20261117,
            )
            for pa in ("Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "RT_2F_Min_m0")
        }
        boots["Safe_vs_B2eq"] = two_way_cluster_bootstrap_extended(
            bdf, "Safe_EV_Sunk_m0", "B2_eq_SafeM0", disp_col_a="Safe_EV_Sunk_m0_disp", disp_col_b="B2_eq_SafeM0_disp",
            mandi_col="origin_market_key", reps=2000, seed=20261117,
        )
        boot_summary[max_age_lbl] = {
            k: {m: {kk: round(float(vv), 4) for kk, vv in md.items()} for m, md in d.items()} for k, d in boots.items()
        }

        for pname, ch in chosen.items():
            rec = _extended_metrics_v7(pname, ch, ot_test)
            rec["window"] = max_age_lbl
            rec["th_b2"] = round(float(th_b2), 2)
            for m_k, col_out in (("mean", "diff_B2_mean_p2s"), ("es10", "diff_B2_es10_p2s"), ("cond_es10", "diff_B2_cond_es10_p2s")):
                rec[col_out] = round(boots[pname][m_k]["p_value_two_sided"], 6) if pname in boots else np.nan
            if pname in boots:
                rec["diff_B2_es10_ci95"] = f"[{boots[pname]['es10']['ci95_low']:.2f}, {boots[pname]['es10']['ci95_high']:.2f}]"
                rec["diff_B2_cond_es10_ci95"] = f"[{boots[pname]['cond_es10']['ci95_low']:.2f}, {boots[pname]['cond_es10']['ci95_high']:.2f}]"
            else:
                rec["diff_B2_es10_ci95"] = ""
                rec["diff_B2_cond_es10_ci95"] = ""
            rows.append(rec)
    return pd.DataFrame(rows), {"counts_t2": cnt_t2, "t2_leakage_test_passed": True, "boots": boot_summary}


# ---------------------------------------------------------------------------
# Exp 6.2: Schedule #7 Bio Clock x Smallholder S6 x Stochastic Cond-MAR x blind_wait
# ---------------------------------------------------------------------------
def _spoil_vector(df: pd.DataFrame, wait_d: int, mode: str, use_era5: bool, tmax_arr: np.ndarray, tmin_arr: np.ndarray, rh_arr: np.ndarray, rain_arr: np.ndarray) -> np.ndarray:
    n = len(df)
    if mode == "zero":
        return np.zeros(n, dtype=np.float64)
    comm = df["Commodity"].to_numpy()
    tau_d = df["tau_days"].to_numpy(dtype=np.float64)
    hrs = df["truck_hours"].to_numpy(dtype=np.float64)
    if mode == "nabcons_24tau":
        base = np.array([BASE_SPOIL_24H.get(str(c), 0.02) for c in comm], dtype=np.float64)
        clock_h = 24.0 * tau_d + 24.0 * wait_d
    elif mode == "nabcons_truck":
        base = np.array([BASE_SPOIL_24H.get(str(c), 0.02) for c in comm], dtype=np.float64)
        clock_h = np.maximum(1.0, hrs + 24.0 * wait_d)
    elif mode == "usda_sched7":
        usda = {"Tomato": 0.020, "Apple": 0.0035, "Onion": 0.0025, "Potato": 0.0015}
        base = np.array([usda.get(str(c), 0.01) for c in comm], dtype=np.float64)
        clock_h = 24.0 * tau_d + 24.0 * wait_d
    else:
        raise ValueError(mode)
    if use_era5:
        tmean = 0.5 * (tmax_arr + tmin_arr)
        t_eff = np.clip(tmean, 5.0, 48.0)
        rh_eff = np.clip(rh_arr, 20.0, 100.0)
        q10 = 2.0 ** ((t_eff - 20.0) / 10.0)
        # VPD-correct moisture stress for bulbs/tubers vs wilting low RH
        rh_f = np.where(np.isin(comm, ["Tomato", "Apple"]), 1.0 + 0.25 * np.maximum(0.0, (70.0 - rh_eff) / 40.0), 1.0 + 0.25 * np.maximum(0.0, (rh_eff - 70.0) / 30.0))
        chill = np.where(comm == "Tomato", 0.015 * np.maximum(0.0, (12.0 - t_eff) / 5.0), 0.0)
        rain_f = np.where(rain_arr >= 35.0, 0.02, 0.0)
    else:
        q10 = 1.0
        rh_f = 1.0
        chill = 0.0
        rain_f = 0.0
    return np.clip(base * (clock_h / 24.0) * q10 * rh_f + chill + rain_f, 0.0, 0.55)


def _spoil_return_leg(df: pd.DataFrame, wait_d: int, mode: str, use_era5: bool, tmax_arr: np.ndarray, tmin_arr: np.ndarray, rh_arr: np.ndarray, rain_arr: np.ndarray) -> np.ndarray:
    """Return-leg physical clock: outbound arrival clock + wait + return drive (>= sell clock on 100% of rows)."""
    n = len(df)
    if mode == "zero":
        return np.zeros(n, dtype=np.float64)
    comm = df["Commodity"].to_numpy()
    tau_d = df["tau_days"].to_numpy(dtype=np.float64)
    hrs = df["truck_hours"].to_numpy(dtype=np.float64)
    usda = {"Tomato": 0.020, "Apple": 0.0035, "Onion": 0.0025, "Potato": 0.0015}
    base = np.array([usda.get(str(c), 0.01) for c in comm], dtype=np.float64) if mode == "usda_sched7" else np.array([BASE_SPOIL_24H.get(str(c), 0.02) for c in comm], dtype=np.float64)
    if mode == "nabcons_truck":
        clock_h = np.maximum(1.0, 2.0 * hrs + 24.0 * wait_d)
    else:
        clock_h = 24.0 * tau_d + hrs + 24.0 * wait_d
    if use_era5:
        tmean = 0.5 * (tmax_arr + tmin_arr)
        t_eff = np.clip(tmean, 5.0, 48.0)
        rh_eff = np.clip(rh_arr, 20.0, 100.0)
        q10 = 2.0 ** ((t_eff - 20.0) / 10.0)
        rh_f = np.where(np.isin(comm, ["Tomato", "Apple"]), 1.0 + 0.25 * np.maximum(0.0, (70.0 - rh_eff) / 40.0), 1.0 + 0.25 * np.maximum(0.0, (rh_eff - 70.0) / 30.0))
        chill = np.where(comm == "Tomato", 0.015 * np.maximum(0.0, (12.0 - t_eff) / 5.0), 0.0)
        rain_f = np.where(rain_arr >= 35.0, 0.02, 0.0)
    else:
        q10, rh_f, chill, rain_f = 1.0, 1.0, 0.0, 0.0
    return np.clip(base * (clock_h / 24.0) * q10 * rh_f + chill + rain_f, 0.0, 0.55)


def _settle_custom(
    df: pd.DataFrame,
    bio_mode: str,
    use_era5: bool,
    freight_base: float,
    freight_per_km: float,
    fee_mult: float,
    arhtiya: float,
    div: float = 1.5,
    disc: float = 0.10,
    blind_wait: int = 0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Unified settlement returning (y_arr, ot_arr, wait_days_arr)."""
    n = len(df)
    hp = np.where(df["State"].to_numpy() == "Himachal Pradesh", 1.45, 1.0)
    f_road = freight_base + freight_per_km * hp * df["road_km"].to_numpy(dtype=np.float64)
    same = df["same_district"].to_numpy(dtype=bool)
    fee_r = np.clip(np.where(same, 0.0, fee_mult * df["fee_rate"].to_numpy(dtype=np.float64)) + arhtiya, 0.0, 0.30)
    loc = df["settle_local_price_d0"].to_numpy(dtype=np.float64)

    p_ex = [df[f"settle_dest_modal_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    p_min = [df[f"settle_dest_min_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    p_an = [df[f"settle_any_min_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    if use_era5:
        tm = [df[f"settle_era5_tmax_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
        tn = [df[f"settle_era5_tmin_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
        rh = [df[f"settle_era5_rh_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
        rn = [df[f"settle_era5_rain_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    else:
        tm = [np.full(n, 20.0)] * 3
        tn = [np.full(n, 20.0)] * 3
        rh = [np.full(n, 65.0)] * 3
        rn = [np.zeros(n)] * 3

    sp_sell = [_spoil_vector(df, d, bio_mode, use_era5, tm[d], tn[d], rh[d], rn[d]) for d in (0, 1, 2)]
    sp_ret = [_spoil_return_leg(df, d, bio_mode, use_era5, tm[d], tn[d], rh[d], rn[d]) for d in (0, 1, 2)]

    out = np.empty(n, dtype=np.float64)
    otypes = np.empty(n, dtype=object)
    waits = np.zeros(n, dtype=np.int32)
    taken = np.zeros(n, dtype=bool)

    for d in (0, 1, 2):
        sale_p = p_ex[d].copy()
        if use_era5:
            heavy = (rn[d] >= 35.0) & np.isfinite(p_min[d]) & (p_min[d] > 0)
            sale_p = np.where(heavy, 0.5 * (sale_p + p_min[d]), sale_p)
        ok = (~taken) & np.isfinite(sale_p) & (sale_p > 0)
        out[ok] = sale_p[ok] * (1.0 - sp_sell[d][ok]) * (1.0 - fee_r[ok]) - f_road[ok] - 25.0 * d - loc[ok]
        otypes[ok] = "exact_d0" if d == 0 else f"exact_wait_d{d}"
        waits[ok] = d
        taken |= ok

        if d < blind_wait:
            # Causal blind wait: truck stays anchored at destination even if today's portal is completely blank
            continue

        if d == 2 or blind_wait == d:
            rest = ~taken
            u_oth = rest & np.isfinite(p_an[d]) & (p_an[d] > 0)
            out[u_oth] = (p_an[d][u_oth] * (1.0 - disc)) * (1.0 - sp_sell[d][u_oth]) * (1.0 - fee_r[u_oth]) - f_road[u_oth] - 25.0 * d - loc[u_oth]
            otypes[u_oth] = f"other_var_distress_d{d}"
            waits[u_oth] = d
            u_div = rest & (~u_oth)
            out[u_div] = -div * f_road[u_div] - loc[u_div] * sp_ret[d][u_div] - 25.0 * d
            otypes[u_div] = f"no_comm_divert_d{d}"
            waits[u_div] = d
            taken |= rest
            break

        # Non-clairvoyant sequential without blind_wait: divert immediately only if zero commodity on portal
        act_any = np.isfinite(p_an[d]) & (p_an[d] > 0)
        give = (~taken) & (~act_any)
        out[give] = -div * f_road[give] - loc[give] * sp_ret[d][give] - 25.0 * d
        otypes[give] = f"no_comm_divert_d{d}"
        waits[give] = d
        taken |= give

    return out, otypes, waits


def run_exp2_bio_s6_condmar(val: pd.DataFrame, test: pd.DataFrame, coords: pd.DataFrame, wx: pd.DataFrame, kappa_star: float, th_base: dict) -> Tuple[pd.DataFrame, dict]:
    val_wx = _attach_full_era5(val, coords, wx)
    test_wx = _attach_full_era5(test, coords, wx)

    # Pre-fit empirical P_obs / P_lag ratios on observed exact_d0 test rows by (Commodity, age<=3, cv28 quartile)
    y_b_init, ot_b_init = settle_candidates(test, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    obs_ex0 = (ot_b_init == "exact_d0") & np.isfinite(test["settle_dest_modal_d0"]) & (test["dest_lag_price"] > 0)
    ratios_all = (test.loc[obs_ex0, "settle_dest_modal_d0"] / test.loc[obs_ex0, "dest_lag_price"]).to_numpy(dtype=np.float64)
    comms_all = test.loc[obs_ex0, "Commodity"].to_numpy()
    cv_q_all = pd.qcut(test["dest_price_cv_28d"], q=4, labels=False, duplicates="drop").fillna(0).to_numpy(dtype=int)
    stratum_pools: Dict[Tuple[str, int], np.ndarray] = {}
    for c_val in np.unique(test["Commodity"]):
        for q_val in np.unique(cv_q_all):
            m = obs_ex0 & (test["Commodity"].to_numpy() == c_val) & (cv_q_all == q_val)
            pool = (test.loc[m, "settle_dest_modal_d0"] / test.loc[m, "dest_lag_price"]).to_numpy(dtype=np.float64)
            stratum_pools[(str(c_val), int(q_val))] = pool if len(pool) >= 20 else ratios_all

    rows = []
    specs = [
        # (label, bio_mode, use_era5, fb, fpk, fee_mult, arhtiya, blind_wait, retune_on_val)
        ("S0_Sched7_USDA_20C", "usda_sched7", False, 35.0, 0.45, 1.0, 0.00, 0, True),
        ("S1_Sched7_USDA_ERA5", "usda_sched7", True, 35.0, 0.45, 1.0, 0.00, 0, True),
        ("S2_Bio_Zero_20C", "zero", False, 35.0, 0.45, 1.0, 0.00, 0, True),
        ("S3_NABCONS_24tau_ERA5_Upper", "nabcons_24tau", True, 35.0, 0.45, 1.0, 0.00, 0, True),
        ("S6_Smallholder_4pctArh_USDA_ERA5_Retuned", "usda_sched7", True, 60.0, 0.75, 0.0, 0.04, 0, True),
        ("S6_Smallholder_6pctArh_USDA_ERA5_Retuned", "usda_sched7", True, 60.0, 0.75, 0.0, 0.06, 0, True),
        ("S6_Smallholder_2pctArh_ZeroBio_Retuned", "zero", False, 60.0, 0.75, 0.0, 0.02, 0, True),
        ("S6_Smallholder_4pctArh_USDA_ERA5_Frozen", "usda_sched7", True, 60.0, 0.75, 0.0, 0.04, 0, False),
        ("Causal_BlindWait_1d_ExactV7_20C", "nabcons_truck", False, 35.0, 0.45, 1.0, 0.00, 1, False),
        ("Causal_BlindWait_2d_ExactV7_20C", "nabcons_truck", False, 35.0, 0.45, 1.0, 0.00, 2, False),
        ("Causal_BlindWait_1d_Sched7ERA5", "usda_sched7", True, 35.0, 0.45, 1.0, 0.00, 1, False),
        ("Causal_BlindWait_2d_Sched7ERA5", "usda_sched7", True, 35.0, 0.45, 1.0, 0.00, 2, False),
    ]

    for lbl, bmode, u_era5, fb, fpk, fmult, arh, bwait, do_retune in specs:
        y_cl, ot_cl, w_cl = _settle_custom(test_wx, bmode, u_era5, fb, fpk, fmult, arh, div=1.5, disc=0.10, blind_wait=bwait)
        y_div1, _, _ = _settle_custom(test_wx, bmode, u_era5, fb, fpk, fmult, arh, div=1.0, disc=0.10, blind_wait=bwait)

        if do_retune:
            kw = {"freight_base": fb, "freight_per_km": fpk, "fee_mult": fmult, "arhtiya_rate": arh}
            from revision.eval_a18 import _recompute_scenario_decision_df
            val_r = _recompute_scenario_decision_df(val_wx, kw)
            if bmode == "zero":
                val_r["spoil_ref_0"] = 0.0
            y_val_r, _, _ = _settle_custom(val_r, bmode, u_era5, fb, fpk, fmult, arh, div=1.5, disc=0.10, blind_wait=bwait)
            val_r["y"] = y_val_r
            cal = _standard_val_calibrate(val_r, kappa_star)
            test_r = _recompute_scenario_decision_df(test_wx, kw)
            if bmode == "zero":
                test_r["spoil_ref_0"] = 0.0
        else:
            cal = {"th_b2": th_base["th_b2"], "m_mg": th_base["m_mg"], "m_rr": th_base["m_rr"], "m_safe": th_base["m_safe"]}
            test_r = test_wx

        test_r["y"] = y_cl
        sc_map = _score_core_subset(test_r, cal["th_b2"], cal["m_mg"], kappa_star, cal["m_rr"], cal["m_safe"])
        core_pols = ("B1_lagged_screen", "B2_age_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "RT_2F_Min_m0")
        sc_sub = {p: sc_map[p] for p in core_pols}

        # Closed div=1.5 + free return div=1.0
        for reg_name, y_use in (("closed_div1.5", y_cl), ("free_return_div1.0", y_div1)):
            if reg_name == "free_return_div1.0" and bwait > 0:
                continue
            ch_dict = _eval_policies_dict(test_r, sc_sub, ot_cl, y_override=y_use)
            for pname, ch in ch_dict.items():
                r = _extended_metrics_v7(pname, ch, ot_cl, y_override=y_use[ch["_i"].to_numpy()])
                r["experiment"] = lbl
                r["missing_regime"] = reg_name
                r["th_b2_used"] = round(float(cal["th_b2"]), 2)
                rows.append(r)

        # Skip multi-p_open MAR sweeps for pure blind_wait comparisons to keep matrix focused
        if bwait > 0:
            continue

        # Stochastic Conditional-MAR draws preserving wait_d & fee structure
        div_mask = np.char.startswith(ot_cl.astype(str), "no_comm_divert")
        idx_div = np.flatnonzero(div_mask)
        hp_t = np.where(test_r["State"].to_numpy() == "Himachal Pradesh", 1.45, 1.0)
        f_road_t = fb + fpk * hp_t * test_r["road_km"].to_numpy(dtype=np.float64)
        same_t = test_r["same_district"].to_numpy(dtype=bool)
        fee_r_t = np.clip(np.where(same_t, 0.0, fmult * test_r["fee_rate"].to_numpy(dtype=np.float64)) + arh, 0.0, 0.30)
        loc_t = test_r["settle_local_price_d0"].to_numpy(dtype=np.float64)
        p_lag_t = test_r["dest_lag_price"].to_numpy(dtype=np.float64)

        sp_div = np.empty(len(idx_div), dtype=np.float64)
        for d in (0, 1, 2):
            wd_m = waits_d = (w_cl[idx_div] == d)
            if wd_m.any():
                sub_d = test_wx.iloc[idx_div[wd_m]]
                tm_d = sub_d[f"settle_era5_tmax_d{d}"].to_numpy(dtype=np.float64) if u_era5 else np.full(len(sub_d), 20.0)
                tn_d = sub_d[f"settle_era5_tmin_d{d}"].to_numpy(dtype=np.float64) if u_era5 else np.full(len(sub_d), 20.0)
                rh_d = sub_d[f"settle_era5_rh_d{d}"].to_numpy(dtype=np.float64) if u_era5 else np.full(len(sub_d), 65.0)
                rn_d = sub_d[f"settle_era5_rain_d{d}"].to_numpy(dtype=np.float64) if u_era5 else np.zeros(len(sub_d))
                sp_div[wd_m] = _spoil_vector(sub_d, d, bmode, u_era5, tm_d, tn_d, rh_d, rn_d)

        # Deterministic S=10 seed average of empirical Cond-MAR draws
        rng = np.random.default_rng(20261117)
        comm_div = test_r["Commodity"].to_numpy()[idx_div]
        cvq_div = cv_q_all[idx_div]
        y_open_draws = []
        for _ in range(10):
            drawn_r = np.empty(len(idx_div), dtype=np.float64)
            for (c_val, q_val), pool in stratum_pools.items():
                mm = (comm_div == c_val) & (cvq_div == q_val)
                if mm.any():
                    drawn_r[mm] = pool[rng.integers(0, len(pool), size=int(mm.sum()))]
            p_sim = p_lag_t[idx_div] * drawn_r
            y_sim = p_sim * (1.0 - sp_div) * (1.0 - fee_r_t[idx_div]) - f_road_t[idx_div] - 25.0 * w_cl[idx_div] - loc_t[idx_div]
            y_full_open = y_cl.copy()
            y_full_open[idx_div] = y_sim
            y_open_draws.append(y_full_open)

        for p_open in (0.25, 0.50, 0.75, 1.00):
            # Average metrics across 10 Cond-MAR Bernoulli realizations at p_open
            acc: Dict[str, List[dict]] = {p: [] for p in core_pols}
            for s_i, y_op in enumerate(y_open_draws):
                if p_open < 1.0:
                    coin = rng.random(len(idx_div)) < p_open
                    y_mix = y_cl.copy()
                    y_mix[idx_div] = np.where(coin, y_op[idx_div], y_cl[idx_div])
                else:
                    y_mix = y_op
                ch_dict = _eval_policies_dict(test_r, sc_sub, ot_cl, y_override=y_mix)
                for pname, ch in ch_dict.items():
                    acc[pname].append(_extended_metrics_v7(pname, ch, ot_cl, y_override=y_mix[ch["_i"].to_numpy()]))
            for pname in core_pols:
                recs = acc[pname]
                avg_r = {k: recs[0][k] for k in recs[0]}
                for num_k in ("mean", "cond_mean", "ep_loss_rate", "cond_loss_rate", "es10", "cond_es10", "cond_es05", "loss_given_loss"):
                    vals = [rr[num_k] for rr in recs if rr[num_k] is not None]
                    avg_r[num_k] = round(float(np.mean(vals)), 4 if "rate" in num_k else 2) if vals else None
                avg_r["experiment"] = lbl
                avg_r["missing_regime"] = f"Stoch_CondMAR_p{p_open:.2f}"
                avg_r["th_b2_used"] = round(float(cal["th_b2"]), 2)
                rows.append(avg_r)

    return pd.DataFrame(rows), {"n_stratum_pools": len(stratum_pools), "n_obs_exact_d0_ref": int(obs_ex0.sum())}


# ---------------------------------------------------------------------------
# Exp 6.3: Nonparametric Manski Bounds, Cross-Crop MNAR, Thin/Thick, Origin & Pre-Choice
# ---------------------------------------------------------------------------
def run_exp3_manski_and_open(
    raw_171: pd.DataFrame,
    cor: pd.DataFrame,
    fees: pd.DataFrame,
    test: pd.DataFrame,
    test_ot: np.ndarray,
    chosen: Dict[str, pd.DataFrame],
) -> Tuple[pd.DataFrame, dict]:
    rows = []
    y_base = test["y"].to_numpy(dtype=np.float64)
    div_mask = np.char.startswith(test_ot.astype(str), "no_comm_divert")
    same = test["same_district"].to_numpy(dtype=bool)
    fee_r = np.where(same, 0.0, test["fee_rate"].to_numpy(dtype=np.float64))
    p_lag = test["dest_lag_price"].to_numpy(dtype=np.float64)
    sp0 = test["spoil_ref_0"].to_numpy(dtype=np.float64)
    f_road = test["freight_road"].to_numpy(dtype=np.float64)
    loc0 = test["settle_local_price_d0"].to_numpy(dtype=np.float64)

    # Observed exact_d0 quantiles for upper Manski support endpoints
    obs_ex0 = (test_ot == "exact_d0") & (p_lag > 0)
    r_ex0 = (test.loc[obs_ex0, "settle_dest_modal_d0"] / test.loc[obs_ex0, "dest_lag_price"]).to_numpy(dtype=np.float64)
    q95_r = float(np.quantile(r_ex0, 0.95))
    q99_r = float(np.quantile(r_ex0, 0.99))

    y_open_lag = np.where(div_mask, p_lag * (1.0 - sp0) * (1.0 - fee_r) - f_road - loc0, y_base)
    y_open_q95 = np.where(div_mask, (p_lag * q95_r) * (1.0 - sp0) * (1.0 - fee_r) - f_road - loc0, y_base)
    y_open_q99 = np.where(div_mask, (p_lag * q99_r) * (1.0 - sp0) * (1.0 - fee_r) - f_road - loc0, y_base)
    y_div20 = np.where(div_mask, -2.0 * f_road - loc0 * sp0, y_base)
    y_totloss = np.where(div_mask, -2.0 * f_road - 0.55 * loc0, y_base)

    ch_s = chosen["Safe_EV_Sunk_m0"]
    ch_b = chosen["B2_age_matched"]
    idx_s = ch_s["_i"].to_numpy()
    idx_b = ch_b["_i"].to_numpy()
    el_s = ch_s["eligible"].to_numpy(dtype=bool)
    el_b = ch_b["eligible"].to_numpy(dtype=bool)
    div_s = el_s & div_mask[idx_s]
    div_b = el_b & div_mask[idx_b]
    same_dest_silent = div_s & div_b & (ch_s["dest_market"].to_numpy() == ch_b["dest_market"].to_numpy())

    def _solve_coupled_tail(
        ys_unsh: np.ndarray,
        yb_unsh: np.ndarray,
        sh_mask: np.ndarray,
        y_lo_sh: np.ndarray,
        y_hi_sh: np.ndarray,
        sub_a: np.ndarray | None = None,
        sub_b: np.ndarray | None = None,
        minimize: bool = True,
    ) -> float:
        def eval_z(z_hi: np.ndarray) -> float:
            ys = ys_unsh.copy()
            yb = yb_unsh.copy()
            v_sh = np.where(z_hi, y_hi_sh, y_lo_sh)
            ys[sh_mask] = v_sh
            yb[sh_mask] = v_sh
            va = ys[sub_a] if sub_a is not None else ys
            vb = yb[sub_b] if sub_b is not None else yb
            return float(es10(va) - es10(vb))

        n_sh = int(sh_mask.sum())
        if n_sh == 0:
            return eval_z(np.zeros(0, dtype=bool))
        best_z = np.zeros(n_sh, dtype=bool)
        best_val = eval_z(best_z)
        cands = [np.ones(n_sh, dtype=bool)]
        for thr in np.unique(np.quantile(y_lo_sh, np.linspace(0.0, 1.0, 25))):
            cands.append(y_lo_sh > thr)
            cands.append(y_lo_sh <= thr)
        for zc in cands:
            v = eval_z(zc)
            if (minimize and v < best_val) or ((not minimize) and v > best_val):
                best_val, best_z = v, zc.copy()
        na_eff = int(sub_a.sum()) if sub_a is not None else len(ys_unsh)
        nb_eff = int(sub_b.sum()) if sub_b is not None else len(yb_unsh)
        for _ in range(8):
            ys = ys_unsh.copy()
            yb = yb_unsh.copy()
            v_sh = np.where(best_z, y_hi_sh, y_lo_sh)
            ys[sh_mask] = v_sh
            yb[sh_mask] = v_sh
            qa = float(np.quantile(ys[sub_a] if sub_a is not None else ys, 0.10))
            qb = float(np.quantile(yb[sub_b] if sub_b is not None else yb, 0.10))
            d_a = (np.maximum(0.0, qa - y_lo_sh) - np.maximum(0.0, qa - y_hi_sh)) / max(1.0, 0.10 * na_eff)
            d_b = (np.maximum(0.0, qb - y_lo_sh) - np.maximum(0.0, qb - y_hi_sh)) / max(1.0, 0.10 * nb_eff)
            delta = d_a - d_b
            z_next = (delta < 0.0) if minimize else (delta > 0.0)
            if np.array_equal(z_next, best_z):
                break
            v_next = eval_z(z_next)
            if (minimize and v_next < best_val - 1e-9) or ((not minimize) and v_next > best_val + 1e-9):
                best_val, best_z = v_next, z_next
            else:
                break
        return best_val

    # Coupled & decoupled Manski bounds across Supp1, Supp2, Supp3 (both ES10 and cond_ES10!)
    for s_name, y_lo_all, y_hi_all in (
        ("Manski_Supp1_div15_openlag", y_base, y_open_lag),
        ("Manski_Supp2_div20_q95", y_div20, y_open_q95),
        ("Manski_Supp3_totloss_q99", y_totloss, y_open_q99),
    ):
        ys_lo = np.where(el_s, y_lo_all[idx_s], 0.0)
        ys_hi = np.where(el_s, y_hi_all[idx_s], 0.0)
        yb_lo = np.where(el_b, y_lo_all[idx_b], 0.0)
        yb_hi = np.where(el_b, y_hi_all[idx_b], 0.0)

        # Decoupled WC/BC contrast bounds: WC = (S_lo - B_hi), BC = (S_hi - B_lo)
        dec_dmean_lo = float((ys_lo - yb_hi).mean())
        dec_dmean_hi = float((ys_hi - yb_lo).mean())
        dec_des10_lo = float(es10(ys_lo) - es10(yb_hi))
        dec_des10_hi = float(es10(ys_hi) - es10(yb_lo))
        dec_dcond_lo = float(es10(ys_lo[el_s]) - es10(yb_hi[el_b]))
        dec_dcond_hi = float(es10(ys_hi[el_s]) - es10(yb_lo[el_b]))

        # Coupled Mean is linear -> invariant on same_dest_silent
        unsh_s = div_s & (~same_dest_silent)
        unsh_b = div_b & (~same_dest_silent)
        ys_wc_base = np.where(unsh_s, ys_lo, ys_lo)
        yb_wc_base = np.where(unsh_b, yb_hi, yb_lo)
        ys_bc_base = np.where(unsh_s, ys_hi, ys_lo)
        yb_bc_base = np.where(unsh_b, yb_lo, yb_lo)
        y_lo_sh = ys_lo[same_dest_silent]
        y_hi_sh = ys_hi[same_dest_silent]

        best_wc_mean = float((ys_wc_base - yb_wc_base).mean())
        best_bc_mean = float((ys_bc_base - yb_bc_base).mean())
        best_wc_es10 = _solve_coupled_tail(ys_wc_base, yb_wc_base, same_dest_silent, y_lo_sh, y_hi_sh, None, None, minimize=True)
        best_bc_es10 = _solve_coupled_tail(ys_bc_base, yb_bc_base, same_dest_silent, y_lo_sh, y_hi_sh, None, None, minimize=False)
        best_wc_cond = _solve_coupled_tail(ys_wc_base, yb_wc_base, same_dest_silent, y_lo_sh, y_hi_sh, el_s, el_b, minimize=True)
        best_bc_cond = _solve_coupled_tail(ys_bc_base, yb_bc_base, same_dest_silent, y_lo_sh, y_hi_sh, el_s, el_b, minimize=False)

        rows.append({
            "analysis": s_name, "subgroup": "Safe_EV_vs_B2",
            "n": len(ch_s), "safe_silent_n": int(div_s.sum()), "b2_silent_n": int(div_b.sum()),
            "shared_silent_n": int(same_dest_silent.sum()),
            "coupled_dmean_wc": round(best_wc_mean, 2), "coupled_dmean_bc": round(best_bc_mean, 2),
            "coupled_des10_wc": round(best_wc_es10, 2), "coupled_des10_bc": round(best_bc_es10, 2),
            "coupled_dcond_es10_wc": round(best_wc_cond, 2), "coupled_dcond_es10_bc": round(best_bc_cond, 2),
            "decoupled_dmean_wc": round(dec_dmean_lo, 2), "decoupled_dmean_bc": round(dec_dmean_hi, 2),
            "decoupled_des10_wc": round(dec_des10_lo, 2), "decoupled_des10_bc": round(dec_des10_hi, 2),
            "decoupled_dcond_es10_wc": round(dec_dcond_lo, 2), "decoupled_dcond_es10_bc": round(dec_dcond_hi, 2),
        })

    # Cross-crop activity (any_open_mat) + Two-tier MNAR + Thin/Thick heterogeneity
    canon_171, _, _ = compute_cleaning_funnel(raw_171)
    all_open_keys = set(zip(canon_171["State"].astype(str), canon_171["Market"].astype(str), pd.to_datetime(canon_171["Arrival_Date"]).dt.strftime("%Y-%m-%d")))
    arr_str = pd.to_datetime(test["arrival_date"]).dt.strftime("%Y-%m-%d")
    any_crop_open_d0 = np.array([(s, dm, d) in all_open_keys for s, dm, d in zip(test["State"].astype(str), test["dest_market"].astype(str), arr_str)], dtype=bool)
    blackout_d0 = div_mask & (~any_crop_open_d0)
    other_crop_d0 = div_mask & any_crop_open_d0

    thick = (test["dest_exact_rep_14d"].to_numpy() >= 0.50) & (test["dest_dow_exact_rep_8w"].to_numpy() >= 0.35)
    for g_name, y_custom in (
        ("CrossCrop_BlackoutClosed_OtherOpenLag", np.where(other_crop_d0, y_open_lag, y_base)),
        ("CrossCrop_BlackoutClosed_OtherOpen80pctLag", np.where(other_crop_d0, 0.80 * p_lag * (1.0 - sp0) * (1.0 - fee_r) - f_road - loc0, y_base)),
        ("Het_ThickOpenLag_ThinClosed", np.where(div_mask & thick, y_open_lag, y_base)),
        ("Het_ThickClosed_ThinOpenLag", np.where(div_mask & (~thick), y_open_lag, y_base)),
    ):
        ys = np.where(el_s, y_custom[idx_s], 0.0)
        yb = np.where(el_b, y_custom[idx_b], 0.0)
        rows.append({
            "analysis": g_name, "subgroup": f"b2_blackout={int((div_b & blackout_d0[idx_b]).sum())},other={int((div_b & other_crop_d0[idx_b]).sum())}",
            "n": len(ch_s), "safe_silent_n": int(div_s.sum()), "b2_silent_n": int(div_b.sum()),
            "shared_silent_n": int(same_dest_silent.sum()),
            "coupled_dmean_wc": round(float((ys - yb).mean()), 2), "coupled_dmean_bc": round(float((ys - yb).mean()), 2),
            "coupled_des10_wc": round(float(es10(ys) - es10(yb)), 2), "coupled_des10_bc": round(float(es10(ys[el_s]) - es10(yb[el_b])), 2),
            "coupled_dcond_es10_wc": round(float(es10(ys[el_s]) - es10(yb[el_b])), 2), "coupled_dcond_es10_bc": round(float(es10(ys[el_s]) - es10(yb[el_b])), 2),
            "decoupled_dmean_wc": round(float(ys.mean()), 2), "decoupled_dmean_bc": round(float(yb.mean()), 2),
            "decoupled_des10_wc": round(float(es10(ys)), 2), "decoupled_des10_bc": round(float(es10(yb)), 2),
            "decoupled_dcond_es10_wc": round(float(es10(ys[el_s])), 2), "decoupled_dcond_es10_bc": round(float(es10(yb[el_b])), 2),
        })

    # Pre-choice all-open candidates vs paired both-open vs realized_exact_d0 post-treatment
    ep_all_open = test.groupby("episode_id")["settle_dest_modal_d0"].transform(lambda s: s.notna().all()).to_numpy()
    sub_all_open = test.loc[ep_all_open].copy().reset_index(drop=True)
    ch_s_ao = pick_episode(sub_all_open, score_safe_ev_sunk(sub_all_open), (sub_all_open["dest_lag_age"].between(1, 3)) & (score_safe_ev_sunk(sub_all_open) > 0.0))
    f_ao = compute_decision_features(sub_all_open)
    th_b2_base = 200.0
    a_ao = (f_ao["age"] >= 1) & (f_ao["age"] <= 3)
    ch_b_ao = pick_episode(sub_all_open, f_ao["net_road_fee"], a_ao & (f_ao["net_road_fee"] > th_b2_base))
    ys_ao = ch_s_ao["y"].to_numpy()
    yb_ao = ch_b_ao["y"].to_numpy()
    rows.append({
        "analysis": "PreChoice_AllCandidates_ExactD0", "subgroup": "Safe_vs_B2",
        "n": int(len(ys_ao)), "safe_silent_n": 0, "b2_silent_n": 0, "shared_silent_n": 0,
        "coupled_dmean_wc": round(float((ys_ao - yb_ao).mean()), 2), "coupled_dmean_bc": round(float(ys_ao.mean() - yb_ao.mean()), 2),
        "coupled_des10_wc": round(float(es10(ys_ao) - es10(yb_ao)), 2), "coupled_des10_bc": round(float(es10(ys_ao[ch_s_ao['eligible']]) - es10(yb_ao[ch_b_ao['eligible']])), 2),
        "coupled_dcond_es10_wc": round(float(es10(ys_ao[ch_s_ao['eligible']]) - es10(yb_ao[ch_b_ao['eligible']])), 2), "coupled_dcond_es10_bc": round(float(es10(ys_ao[ch_s_ao['eligible']]) - es10(yb_ao[ch_b_ao['eligible']])), 2),
        "decoupled_dmean_wc": round(float(ys_ao.mean()), 2), "decoupled_dmean_bc": round(float(yb_ao.mean()), 2),
        "decoupled_des10_wc": round(float(es10(ys_ao)), 2), "decoupled_des10_bc": round(float(es10(yb_ao)), 2),
        "decoupled_dcond_es10_wc": round(float(es10(ys_ao[ch_s_ao['eligible']])), 2), "decoupled_dcond_es10_bc": round(float(es10(yb_ao[ch_b_ao['eligible']])), 2),
    })

    # Symmetric origin-missingness check on N=86,054 unconditional origins
    unc_171, _ = build_lagged_candidates_from_frames(
        raw_df=raw_171, corridors_df=cor, fee_params_df=fees, clim_df=None,
        grade_explicit=False, min_origin_date="2025-06-01", max_origin_date="2026-04-08", include_unreported_origin_days=True,
    )
    unc_y_d0lag, unc_ot = settle_candidates(unc_171, how="sequential", weather="none", div=1.5, disc=0.10, outside_option="d0_or_lag", return_outcomes=True)
    unc_171["y"] = unc_y_d0lag
    uf = compute_decision_features(unc_171)
    a_u = (uf["age"] >= 1) & (uf["age"] <= 3)
    ch_u_s = pick_episode(unc_171, score_safe_ev_sunk(unc_171), a_u & (score_safe_ev_sunk(unc_171) > 0.0))
    ch_u_b = pick_episode(unc_171, uf["net_road_fee"], a_u & (uf["net_road_fee"] > th_b2_base))
    ep_orig_d0_missing = ch_u_s["episode_id"].map(unc_171.groupby("episode_id")["settle_local_price_d0"].first().isna()).to_numpy()
    orig_open_keys = set(zip(canon_171["State"].astype(str) + "|" + canon_171["Market"].astype(str), pd.to_datetime(canon_171["Arrival_Date"]).dt.strftime("%Y-%m-%d")))
    u_dstr = pd.to_datetime(ch_u_s["date"]).dt.strftime("%Y-%m-%d")
    u_orig_any = np.array([(omk, d) in orig_open_keys for omk, d in zip(ch_u_s["origin_market_key"].astype(str), u_dstr)], dtype=bool)
    orig_blackout = ep_orig_d0_missing & (~u_orig_any)
    ep_olag_p = ch_u_s["episode_id"].map(unc_171.groupby("episode_id")["origin_lag_price"].first()).to_numpy(dtype=np.float64)
    ep_comm = ch_u_s["Commodity"].to_numpy()
    orig_sp24 = np.array([BASE_SPOIL_24H.get(str(c), 0.02) for c in ep_comm], dtype=np.float64)
    orig_pen = np.where(orig_blackout, -(ep_olag_p * orig_sp24 + 25.0), 0.0)
    ys_sym = np.where(ch_u_s["eligible"], ch_u_s["y"].to_numpy(), orig_pen)
    yb_sym = np.where(ch_u_b["eligible"], ch_u_b["y"].to_numpy(), orig_pen)
    rows.append({
        "analysis": "Unconditional_86054_SymClosedOrigin", "subgroup": f"orig_miss={int(ep_orig_d0_missing.sum())},orig_blackout={int(orig_blackout.sum())}",
        "n": len(ys_sym), "safe_silent_n": int((~ch_u_s["eligible"]).sum()), "b2_silent_n": int((~ch_u_b["eligible"]).sum()), "shared_silent_n": 0,
        "coupled_dmean_wc": round(float((ys_sym - yb_sym).mean()), 2), "coupled_dmean_bc": round(float(ys_sym.mean() - yb_sym.mean()), 2),
        "coupled_des10_wc": round(float(es10(ys_sym) - es10(yb_sym)), 2), "coupled_des10_bc": round(float(es10(ys_sym[ch_u_s['eligible']]) - es10(yb_sym[ch_u_b['eligible']])), 2),
        "coupled_dcond_es10_wc": round(float(es10(ys_sym[ch_u_s['eligible']]) - es10(yb_sym[ch_u_b['eligible']])), 2), "coupled_dcond_es10_bc": round(float(es10(ys_sym[ch_u_s['eligible']]) - es10(yb_sym[ch_u_b['eligible']])), 2),
        "decoupled_dmean_wc": round(float(ys_sym.mean()), 2), "decoupled_dmean_bc": round(float(yb_sym.mean()), 2),
        "decoupled_des10_wc": round(float(es10(ys_sym)), 2), "decoupled_des10_bc": round(float(es10(yb_sym)), 2),
        "decoupled_dcond_es10_wc": round(float(es10(ys_sym[ch_u_s['eligible']])), 2), "decoupled_dcond_es10_bc": round(float(es10(yb_sym[ch_u_b['eligible']])), 2),
    })

    # Thin/Thick theta break-even numbers
    s_m = np.where(el_s, (y_open_lag - y_base)[idx_s], 0.0)
    b_m = np.where(el_b, (y_open_lag - y_base)[idx_b], 0.0)
    d_closed = float((ch_s["y"] - ch_b["y"]).mean())
    gain_s_thick = float(np.where(thick[idx_s], s_m, 0.0).mean())
    gain_b_thick = float(np.where(thick[idx_b], b_m, 0.0).mean())
    gain_s_thin = float(np.where(~thick[idx_s], s_m, 0.0).mean())
    gain_b_thin = float(np.where(~thick[idx_b], b_m, 0.0).mean())
    theta_thin_t0 = d_closed / max(1e-9, (gain_b_thin - gain_s_thin))
    theta_thin_t1 = (d_closed - (gain_b_thick - gain_s_thick)) / max(1e-9, (gain_b_thin - gain_s_thin))
    meta = {
        "q95_ratio_ex0": round(q95_r, 4), "q99_ratio_ex0": round(q99_r, 4),
        "b2_silent_total": int(div_b.sum()),
        "b2_silent_thick": int((div_b & thick[idx_b]).sum()),
        "b2_silent_thin": int((div_b & (~thick[idx_b])).sum()),
        "safe_silent_thick": int((div_s & thick[idx_s]).sum()),
        "safe_silent_thin": int((div_s & (~thick[idx_s])).sum()),
        "theta_thin_be_when_thick0": round(theta_thin_t0 * 100.0, 2),
        "theta_thin_be_when_thick1": round(theta_thin_t1 * 100.0, 2),
    }
    return pd.DataFrame(rows), meta


# ---------------------------------------------------------------------------
# Exp 6.4: Purged Val, Clean <= t-1 ML / OR / Intact T1..T4 Pareto, Formula Audits
# ---------------------------------------------------------------------------
def _ml_design_matrix(
    df: pd.DataFrame,
    dummy_cols: List[str] | None = None,
    include_safe_ev: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    f = compute_decision_features(df)
    dt = pd.to_datetime(df["date"])
    month = dt.dt.month.to_numpy(dtype=np.float64)
    dow = dt.dt.dayofweek.to_numpy(dtype=np.float64)
    p_orig = np.maximum(df["origin_lag_price"].to_numpy(dtype=np.float64), 1.0)
    f_road = np.maximum(df["freight_road"].to_numpy(dtype=np.float64), 1.0)
    p_dest = df["dest_lag_price"].to_numpy(dtype=np.float64)
    cv = df["dest_price_cv_28d"].fillna(0.05).to_numpy(dtype=np.float64)
    same = df["same_district"].to_numpy(dtype=bool)
    fee_eff = np.where(same, 0.0, df["fee_rate"].to_numpy(dtype=np.float64))
    g1sd = p_dest * (1.0 - cv) * (1.0 - fee_eff) - df["origin_lag_price"].to_numpy(dtype=np.float64)

    cols = {
        "lag_spread": df["lag_spread"].to_numpy(dtype=np.float64),
        "rel_spread": df["lag_spread"].to_numpy(dtype=np.float64) / p_orig,
        "log1p_spread": np.log1p(np.maximum(0.0, df["lag_spread"].to_numpy(dtype=np.float64))),
        "net_road_fee": f["net_road_fee"],
        "net_road_fee_spoil": f["net_road_fee_spoil"],
        "g1sd_over_f": g1sd / f_road,
        "dest_lag_price": p_dest,
        "origin_lag_price": df["origin_lag_price"].to_numpy(dtype=np.float64),
        "freight_road": df["freight_road"].to_numpy(dtype=np.float64),
        "fee_rate": df["fee_rate"].to_numpy(dtype=np.float64),
        "spoil_ref_0": df["spoil_ref_0"].to_numpy(dtype=np.float64),
        "road_km": df["road_km"].to_numpy(dtype=np.float64),
        "tau_days": df["tau_days"].to_numpy(dtype=np.float64),
        "same_district": df["same_district"].to_numpy(dtype=np.float64),
        "dest_lag_age": df["dest_lag_age"].to_numpy(dtype=np.float64),
        "origin_lag_age": df["origin_lag_age"].to_numpy(dtype=np.float64),
        "rep14": df["dest_exact_rep_14d"].to_numpy(dtype=np.float64),
        "rep28": df["dest_exact_rep_28d"].to_numpy(dtype=np.float64),
        "any14": df["dest_any_rep_14d"].to_numpy(dtype=np.float64),
        "any28": df["dest_any_rep_28d"].to_numpy(dtype=np.float64),
        "dow8": df["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64),
        "cv28": df["dest_price_cv_28d"].to_numpy(dtype=np.float64),
        "cnt28": df["dest_obs_cnt_28d"].to_numpy(dtype=np.float64),
        "month_sin": np.sin(2.0 * np.pi * month / 12.0),
        "month_cos": np.cos(2.0 * np.pi * month / 12.0),
        "dow_sin": np.sin(2.0 * np.pi * dow / 7.0),
        "dow_cos": np.cos(2.0 * np.pi * dow / 7.0),
    }
    if include_safe_ev:
        cols["safe_ev_feat"] = score_safe_ev_sunk(df)
    X = pd.DataFrame(cols)
    dummies = pd.get_dummies(df[["State", "Commodity"]], drop_first=False, dtype=np.float64)
    if dummy_cols is not None:
        dummies = dummies.reindex(columns=dummy_cols, fill_value=0.0)
    cols_out = list(dummies.columns)
    return pd.concat([X.reset_index(drop=True), dummies.reset_index(drop=True)], axis=1), cols_out


def run_exp4_ml_pareto_and_formula(raw_171: pd.DataFrame, cor: pd.DataFrame, fees: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, test_ot: np.ndarray, kappa_star: float) -> Tuple[pd.DataFrame, dict]:
    rows = []
    tf = compute_decision_features(test)
    age_t13 = (tf["age"] >= 1) & (tf["age"] <= 3)

    # 1) Compare full val vs purged val (arrival_date + 2d <= 2025-05-31 removing 939 spillover episodes)
    ep_max_settle = val.groupby("episode_id")["arrival_date"].transform(lambda s: (pd.to_datetime(s) + pd.Timedelta(days=2)).max())
    val_purged = val[ep_max_settle <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    n_spilled = int(val["episode_id"].nunique() - val_purged["episode_id"].nunique())
    cal_full = _standard_val_calibrate(val, kappa_star)
    cal_purged = _standard_val_calibrate(val_purged, kappa_star)

    for tag, cal_c in (("B2_val_full", cal_full), ("B2_val_purged939", cal_purged)):
        ch_b = pick_episode(test, tf["net_road_fee"], age_t13 & (tf["net_road_fee"] > cal_c["th_b2"]))
        r = _extended_metrics_v7(tag, ch_b, test_ot)
        r["group"] = "val_purge_check"
        r["note"] = f"th={cal_c['th_b2']:.2f}, m_rr={cal_c['m_rr']:.2f}, m_mg={cal_c['m_mg']:.2f}"
        rows.append(r)

    # Safe_EV val dispatch target (~62.4% on val_purged) for fair out-of-sample matched-coverage ML comparisons
    vf_p = compute_decision_features(val_purged)
    age_vp13 = (vf_p["age"] >= 1) & (vf_p["age"] <= 3)
    ch_safe_vp = pick_episode(val_purged, score_safe_ev_sunk(val_purged), age_vp13 & (score_safe_ev_sunk(val_purged) > 0.0))
    safe_val_disp_tgt = float(ch_safe_vp["eligible"].mean())

    # 2A) 5-Month Off-Season (2025 Jan-May) ML/OR/CQR Models trained strictly on val_purged
    X_val, dcols = _ml_design_matrix(val_purged, include_safe_ev=True)
    X_test, _ = _ml_design_matrix(test, dummy_cols=dcols, include_safe_ev=True)
    yv = val_purged["y"].to_numpy(dtype=np.float64)

    vdates = pd.to_datetime(val_purged["date"])
    v_fit = (vdates <= pd.Timestamp("2025-04-15")).to_numpy()
    v_cal = ~v_fit
    y_vfit = yv[v_fit]
    y_vcal = yv[v_cal]

    mu_x = X_val.mean(axis=0).to_numpy()
    sd_x = np.maximum(X_val.std(axis=0).to_numpy(), 1e-6)
    Xv_s = (X_val.to_numpy() - mu_x) / sd_x
    Xt_s = (X_test.to_numpy() - mu_x) / sd_x

    ridge = Ridge(alpha=10.0).fit(Xv_s, yv)
    pred_ridge_test = ridge.predict(Xt_s)

    clf_pos = LogisticRegression(C=0.5, max_iter=500).fit(Xv_s, (yv > 0).astype(int))
    reg_pos = Ridge(alpha=10.0).fit(Xv_s[yv > 0], yv[yv > 0])
    reg_neg = Ridge(alpha=10.0).fit(Xv_s[yv <= 0], yv[yv <= 0])
    p_tp_t = clf_pos.predict_proba(Xt_s)[:, 1]
    sc_tp_t = p_tp_t * reg_pos.predict(Xt_s) + (1.0 - p_tp_t) * reg_neg.predict(Xt_s)

    hgbr_ev = HistGradientBoostingRegressor(max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_val.to_numpy(), yv)
    ev_t = hgbr_ev.predict(X_test.to_numpy())

    hgbr_loss = HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=150, min_samples_leaf=50, random_state=42).fit(X_val.to_numpy(), (yv < 0).astype(int))
    ploss_t = hgbr_loss.predict_proba(X_test.to_numpy())[:, 1]

    hgbr_q20 = HistGradientBoostingRegressor(loss="quantile", quantile=0.20, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_val.to_numpy(), yv)
    q20_v = hgbr_q20.predict(X_val.to_numpy())
    q20_t = hgbr_q20.predict(X_test.to_numpy())
    th_q20_5m_safematch = find_val_matched_threshold(val_purged, q20_v, age_vp13, safe_val_disp_tgt)

    hgbr_q30 = HistGradientBoostingRegressor(loss="quantile", quantile=0.30, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_val.to_numpy(), yv)
    q30_t = hgbr_q30.predict(X_test.to_numpy())
    hgbr_q35 = HistGradientBoostingRegressor(loss="quantile", quantile=0.35, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_val.to_numpy(), yv)
    q35_t = hgbr_q35.predict(X_test.to_numpy())

    # Legacy 43d Mean-Var retained for backward comparability + flagged as strawman
    hgbr_ev_in = HistGradientBoostingRegressor(max_depth=5, learning_rate=0.05, max_iter=150, min_samples_leaf=50, random_state=42).fit(X_val.to_numpy()[v_fit], y_vfit)
    ev_in_cal = hgbr_ev_in.predict(X_val.to_numpy()[v_cal])
    ev_in_t = hgbr_ev_in.predict(X_test.to_numpy())
    sq_res_cal = np.square(y_vcal - ev_in_cal)
    hgbr_var = HistGradientBoostingRegressor(max_depth=4, learning_rate=0.05, max_iter=120, min_samples_leaf=80, random_state=42).fit(X_val.to_numpy()[v_cal], sq_res_cal)
    var_t = np.maximum(1.0, hgbr_var.predict(X_test.to_numpy()))

    # TRUE Heteroscedastic Split Conformalized Quantile Regression (MG_T1..T4_Intact):
    # Scale one-sided residual (EV - y) by conditional IQR (q80 - q20) so conformal width adapts per corridor and re-ranks candidates!
    hgbr_q20_in = HistGradientBoostingRegressor(loss="quantile", quantile=0.20, max_depth=5, learning_rate=0.05, max_iter=150, min_samples_leaf=50, random_state=42).fit(X_val.to_numpy()[v_fit], y_vfit)
    hgbr_q80_in = HistGradientBoostingRegressor(loss="quantile", quantile=0.80, max_depth=5, learning_rate=0.05, max_iter=150, min_samples_leaf=50, random_state=42).fit(X_val.to_numpy()[v_fit], y_vfit)
    sig_in_cal = np.maximum(50.0, hgbr_q80_in.predict(X_val.to_numpy()[v_cal]) - hgbr_q20_in.predict(X_val.to_numpy()[v_cal]))
    sig_in_t = np.maximum(50.0, hgbr_q80_in.predict(X_test.to_numpy()) - hgbr_q20_in.predict(X_test.to_numpy()))
    scaled_res_cal = (ev_in_cal - y_vcal) / sig_in_cal
    q_conf80 = float(np.quantile(scaled_res_cal, min(0.999, 0.80 * (1.0 + 1.0 / max(1, len(scaled_res_cal))))))
    lcb_conf_cal = ev_in_cal - q_conf80 * sig_in_cal
    lcb_conf_t = ev_in_t - q_conf80 * sig_in_t

    val_cal_df = val_purged.loc[v_cal].reset_index(drop=True)
    t13_v_all = (val_purged["dest_lag_age"].between(1, 3)) & (val_purged["dest_exact_rep_14d"] >= 0.50) & (val_purged["dest_dow_exact_rep_8w"] >= 0.35) & (compute_decision_features(val_purged)["net_road_fee_spoil"] > 0.0)
    t13_v_cal = t13_v_all.to_numpy()[v_cal]
    t13_t = age_t13 & (tf["rep14"] >= 0.50) & (tf["dow8"] >= 0.35) & (tf["net_road_fee_spoil"] > 0.0)
    th_t4_match = find_val_matched_threshold(val_cal_df, lcb_conf_cal, t13_v_cal, cal_purged["tgt"])
    ch_raw_in_5m = pick_episode(test, ev_in_t, t13_t & (ev_in_t > find_val_matched_threshold(val_cal_df, ev_in_cal, t13_v_cal, cal_purged["tgt"])))
    ch_cqr_5m = pick_episode(test, lcb_conf_t, t13_t & (lcb_conf_t > th_t4_match))
    cqr5m_dest_switches = int((ch_cqr_5m["eligible"] & (ch_cqr_5m["dest_market"] != ch_raw_in_5m["dest_market"])).sum())

    # 2B) Full-Season 17-Month Leak-Free Training (2024-02-01..2025-05-28, arrival_date + 2d <= 2025-05-31)
    df_17m_raw, _ = build_lagged_candidates_from_frames(
        raw_171, cor, fees, clim_df=None, grade_explicit=False, min_origin_date="2024-02-01", max_origin_date="2025-05-31"
    )
    df_17m_raw["date"] = pd.to_datetime(df_17m_raw["date"])
    df_17m_raw["y"] = settle_candidates(df_17m_raw, how="sequential", weather="none", div=1.5, disc=0.10)
    ep17_max = df_17m_raw.groupby("episode_id")["arrival_date"].transform(lambda s: (pd.to_datetime(s) + pd.Timedelta(days=2)).max())
    train_17m = df_17m_raw[ep17_max <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    n_ep_17m = int(train_17m["episode_id"].nunique())

    f17 = compute_decision_features(train_17m)
    age17_13 = (f17["age"] >= 1) & (f17["age"] <= 3)
    ch17_safe = pick_episode(train_17m, score_safe_ev_sunk(train_17m), age17_13 & (score_safe_ev_sunk(train_17m) > 0.0))
    safe_17m_disp_tgt = float(ch17_safe["eligible"].mean())

    X_17m, dcols_17m = _ml_design_matrix(train_17m, include_safe_ev=True)
    X_t_17m, _ = _ml_design_matrix(test, dummy_cols=dcols_17m, include_safe_ev=True)
    y_17m = train_17m["y"].to_numpy(dtype=np.float64)
    y_rel_17m = y_17m / np.maximum(train_17m["origin_lag_price"].to_numpy(dtype=np.float64), 100.0)
    p_orig_t = np.maximum(test["origin_lag_price"].to_numpy(dtype=np.float64), 100.0)

    ev_17m_m = HistGradientBoostingRegressor(max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m.to_numpy(), y_17m)
    q10_17m_m = HistGradientBoostingRegressor(loss="quantile", quantile=0.10, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m.to_numpy(), y_17m)
    q20_17m_m = HistGradientBoostingRegressor(loss="quantile", quantile=0.20, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m.to_numpy(), y_17m)
    q35_17m_m = HistGradientBoostingRegressor(loss="quantile", quantile=0.35, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m.to_numpy(), y_17m)
    q80_17m_m = HistGradientBoostingRegressor(loss="quantile", quantile=0.80, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m.to_numpy(), y_17m)
    relq20_17m_m = HistGradientBoostingRegressor(loss="quantile", quantile=0.20, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m.to_numpy(), y_rel_17m)

    ev17_v, ev17_t = ev_17m_m.predict(X_17m.to_numpy()), ev_17m_m.predict(X_t_17m.to_numpy())
    q10_17_v, q10_17_t = q10_17m_m.predict(X_17m.to_numpy()), q10_17m_m.predict(X_t_17m.to_numpy())
    q20_17_v, q20_17_t = q20_17m_m.predict(X_17m.to_numpy()), q20_17m_m.predict(X_t_17m.to_numpy())
    q35_17_t = q35_17m_m.predict(X_t_17m.to_numpy())
    q80_17_v, q80_17_t = q80_17m_m.predict(X_17m.to_numpy()), q80_17m_m.predict(X_t_17m.to_numpy())
    relq20_v = relq20_17m_m.predict(X_17m.to_numpy()) * np.maximum(train_17m["origin_lag_price"].to_numpy(dtype=np.float64), 100.0)
    relq20_t = relq20_17m_m.predict(X_t_17m.to_numpy()) * p_orig_t

    hyb_17_v = 0.4 * ev17_v + 0.6 * q10_17_v
    hyb_17_t = 0.4 * ev17_t + 0.6 * q10_17_t
    th_q20_17_vm = find_val_matched_threshold(train_17m, q20_17_v, age17_13, safe_17m_disp_tgt)
    th_relq20_17_vm = find_val_matched_threshold(train_17m, relq20_v, age17_13, safe_17m_disp_tgt)
    th_hyb_17_vm = find_val_matched_threshold(train_17m, hyb_17_v, age17_13, safe_17m_disp_tgt)
    # Also compute exact 63.23% test-rate match strictly from ranking (for equal-coverage slope comparison)
    safe_test_disp = float(pick_episode(test, score_safe_ev_sunk(test), age_t13 & (score_safe_ev_sunk(test) > 0.0))["eligible"].mean())
    th_hyb_17_eq63 = find_val_matched_threshold(test, hyb_17_t, age_t13, safe_test_disp)

    # Stylized Mean-SD (scale-invariant IQR spread proxy, replacing 43d variance strawman)
    iqr17_v = np.maximum(50.0, q80_17_v - q20_17_v)
    iqr17_t = np.maximum(50.0, q80_17_t - q20_17_t)
    meansd_v = ev17_v - 0.35 * iqr17_v
    meansd_t = ev17_t - 0.35 * iqr17_t
    th_meansd_vm = find_val_matched_threshold(train_17m, meansd_v, age17_13, safe_17m_disp_tgt)

    # Physics-informed ablation: IDENTICAL 17-month Mean-Q10 MINUS safe_ev_feat
    X_17m_ns, dcols_ns = _ml_design_matrix(train_17m, include_safe_ev=False)
    X_t_17m_ns, _ = _ml_design_matrix(test, dummy_cols=dcols_ns, include_safe_ev=False)
    ev17_ns = HistGradientBoostingRegressor(max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m_ns.to_numpy(), y_17m)
    q10_17_ns = HistGradientBoostingRegressor(loss="quantile", quantile=0.10, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m_ns.to_numpy(), y_17m)
    hyb_ns_v = 0.4 * ev17_ns.predict(X_17m_ns.to_numpy()) + 0.6 * q10_17_ns.predict(X_17m_ns.to_numpy())
    hyb_ns_t = 0.4 * ev17_ns.predict(X_t_17m_ns.to_numpy()) + 0.6 * q10_17_ns.predict(X_t_17m_ns.to_numpy())
    th_hyb_ns_vm = find_val_matched_threshold(train_17m, hyb_ns_v, age17_13, safe_17m_disp_tgt)
    th_hyb_ns_eq63 = find_val_matched_threshold(test, hyb_ns_t, age_t13, safe_test_disp)

    # True 17-month Heteroscedastic CQR (fit <= 2025-03-31, cal = 2025-04-01..2025-05-28)
    d17 = pd.to_datetime(train_17m["date"])
    f17_in = (d17 <= pd.Timestamp("2025-03-31")).to_numpy()
    c17_in = ~f17_in
    ev_17_in = HistGradientBoostingRegressor(max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m.to_numpy()[f17_in], y_17m[f17_in])
    q20_17_in = HistGradientBoostingRegressor(loss="quantile", quantile=0.20, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m.to_numpy()[f17_in], y_17m[f17_in])
    q80_17_in = HistGradientBoostingRegressor(loss="quantile", quantile=0.80, max_depth=5, learning_rate=0.05, max_iter=180, min_samples_leaf=50, random_state=42).fit(X_17m.to_numpy()[f17_in], y_17m[f17_in])
    pred_17_cal = ev_17_in.predict(X_17m.to_numpy()[c17_in])
    sig_17_cal = np.maximum(50.0, q80_17_in.predict(X_17m.to_numpy()[c17_in]) - q20_17_in.predict(X_17m.to_numpy()[c17_in]))
    s_17_cal = (pred_17_cal - y_17m[c17_in]) / sig_17_cal
    q_cqr17 = float(np.quantile(s_17_cal, min(0.999, 0.80 * (1.0 + 1.0 / max(1, len(s_17_cal))))))
    cqr_17_cal = pred_17_cal - q_cqr17 * sig_17_cal
    sig_17_t = np.maximum(50.0, q80_17_in.predict(X_t_17m.to_numpy()) - q20_17_in.predict(X_t_17m.to_numpy()))
    raw_17_in_t = ev_17_in.predict(X_t_17m.to_numpy())
    cqr_17_t = raw_17_in_t - q_cqr17 * sig_17_t
    t17_cal_df = train_17m.loc[c17_in].reset_index(drop=True)
    a17_cal = age17_13[c17_in]
    th_cqr17_vm = find_val_matched_threshold(t17_cal_df, cqr_17_cal, a17_cal, safe_17m_disp_tgt)
    ch_raw17_tmp = pick_episode(test, raw_17_in_t, age_t13 & (raw_17_in_t > find_val_matched_threshold(t17_cal_df, pred_17_cal, a17_cal, safe_17m_disp_tgt)))
    ch_cqr17_tmp = pick_episode(test, cqr_17_t, age_t13 & (cqr_17_t > th_cqr17_vm))
    cqr17m_dest_switches = int((ch_cqr17_tmp["eligible"] & (ch_cqr17_tmp["dest_market"] != ch_raw17_tmp["dest_market"])).sum())

    ml_candidates = [
        ("ML_Ridge_EV_m0", pred_ridge_test, pred_ridge_test > 0.0, "5m Ridge > 0"),
        ("ML_TwoPart_LogitRidge_m0", sc_tp_t, sc_tp_t > 0.0, "5m Logit*Pos + (1-p)*Neg > 0"),
        ("ML_HGBR_EV_TV_m0", ev_t, ev_t > 0.0, "5m Unconstrained <=t-1 HGBR > 0"),
        ("ML_HGBR_EV_TV_age13_m0", ev_t, age_t13 & (ev_t > 0.0), "5m age 1..3 HGBR EV > 0"),
        ("ML_HGBR_RiskAverse_L250", ev_t - 250.0 * ploss_t, age_t13 & ((ev_t - 250.0 * ploss_t) > 0.0), "5m HGBR EV - 250*P(loss) > 0"),
        ("ML_HGBR_RiskAverse_L500", ev_t - 500.0 * ploss_t, age_t13 & ((ev_t - 500.0 * ploss_t) > 0.0), "5m HGBR EV - 500*P(loss) > 0"),
        ("ML_HGBR_Q20_m0", q20_t, age_t13 & (q20_t > 0.0), "5m 20th percentile regressor > 0"),
        ("ML_5m_HGBR_Q20_matched63", q20_t, age_t13 & (q20_t > th_q20_5m_safematch), f"5m Q20 val-matched to Safe_EV disp (th={th_q20_5m_safematch:.1f})"),
        ("ML_5m_HGBR_Q30_m0", q30_t, age_t13 & (q30_t > 0.0), "5m 30th percentile regressor > 0"),
        ("ML_5m_HGBR_Q35_m0", q35_t, age_t13 & (q35_t > 0.0), "5m 35th percentile regressor > 0"),
        ("OR_Vargas_MeanVar_g0002", ev_t - 0.0002 * var_t, age_t13 & ((ev_t - 0.0002 * var_t) > 0.0), "Legacy 43d Mean - 0.0002*Var > 0"),
        ("OR_Vargas_MeanVar_g0005", ev_t - 0.0005 * var_t, age_t13 & ((ev_t - 0.0005 * var_t) > 0.0), "Legacy 43d Mean - 0.0005*Var > 0"),
        ("MG_T1_T2_T3_T4_Intact_m0", lcb_conf_t, t13_t & (lcb_conf_t > 0.0), f"5m Heteroscedastic CQR LCB (s80={q_conf80:.2f}) > 0"),
        ("MG_T1_T2_T3_T4_Intact_matched", lcb_conf_t, t13_t & (lcb_conf_t > th_t4_match), f"5m Heteroscedastic CQR val-matched th={th_t4_match:.1f}, switches={cqr5m_dest_switches}"),
        ("ML_17m_HGBR_EV_m0", ev17_t, age_t13 & (ev17_t > 0.0), f"Full-season 17m (n={n_ep_17m}) HGBR EV > 0"),
        ("ML_17m_HGBR_Q20_valmatch", q20_17_t, age_t13 & (q20_17_t > th_q20_17_vm), f"17m HGBR Q20 val-matched th={th_q20_17_vm:.1f}"),
        ("ML_17m_HGBR_Q35_m0", q35_17_t, age_t13 & (q35_17_t > 0.0), "17m HGBR Q35 > 0"),
        ("ML_17m_RelQ20_valmatch", relq20_t, age_t13 & (relq20_t > th_relq20_17_vm), f"17m Scale-normalized y/P_orig Q20 valmatch th={th_relq20_17_vm:.1f}"),
        ("ML_17m_MeanQ10_Hybrid_valmatch", hyb_17_t, age_t13 & (hyb_17_t > th_hyb_17_vm), f"17m 0.4*EV+0.6*Q10 (with safe_ev_feat) valmatch th={th_hyb_17_vm:.1f}"),
        ("ML_17m_MeanQ10_Hybrid_eq63", hyb_17_t, age_t13 & (hyb_17_t > th_hyb_17_eq63), f"17m 0.4*EV+0.6*Q10 (with safe_ev_feat) eq 63.23% th={th_hyb_17_eq63:.1f}"),
        ("ML_17m_MeanQ10_NoSafeEV_valmatch", hyb_ns_t, age_t13 & (hyb_ns_t > th_hyb_ns_vm), f"17m 0.4*EV+0.6*Q10 WITHOUT safe_ev_feat valmatch th={th_hyb_ns_vm:.1f}"),
        ("ML_17m_MeanQ10_NoSafeEV_eq63", hyb_ns_t, age_t13 & (hyb_ns_t > th_hyb_ns_eq63), f"17m 0.4*EV+0.6*Q10 WITHOUT safe_ev_feat eq 63.23% th={th_hyb_ns_eq63:.1f}"),
        ("ML_17m_CQR80_m0", cqr_17_t, age_t13 & (cqr_17_t > 0.0), f"17m Heteroscedastic Split-CQR (s80={q_cqr17:.2f}) > 0"),
        ("ML_17m_CQR80_valmatch", cqr_17_t, age_t13 & (cqr_17_t > th_cqr17_vm), f"17m Heteroscedastic CQR valmatch th={th_cqr17_vm:.1f}, switches={cqr17m_dest_switches}"),
        ("OR_Stylized_MeanSD_17m_m0", meansd_t, age_t13 & (meansd_t > 0.0), "17m Scale-invariant EV - 0.35*IQR > 0"),
        ("OR_Stylized_MeanSD_17m_valmatch", meansd_t, age_t13 & (meansd_t > th_meansd_vm), f"17m EV - 0.35*IQR valmatch th={th_meansd_vm:.1f}"),
        ("ZeroParam_Safe_EV_Sunk_m0", score_safe_ev_sunk(test), age_t13 & (score_safe_ev_sunk(test) > 0.0), "Reference 0-tuned-param"),
        ("ZeroParam_RT_2F_Min_m0", score_rt2f_min(test), age_t13 & (score_rt2f_min(test) > 0.0), "Reference calculator 0-tuned-param"),
    ]
    for pname, sc_t, el_t, note in ml_candidates:
        ch = pick_episode(test, sc_t, el_t)
        r = _extended_metrics_v7(pname, ch, test_ot)
        r["group"] = "ml_or_pareto"
        r["note"] = note
        rows.append(r)

    # 3) Formula, cv28==0 bug, ratio-argmax, 2x2 Orthogonal Decomposition, Scale-Invariance, & unrestricted top_k=None checks
    cv28_raw = test["dest_price_cv_28d"].to_numpy(dtype=np.float64)
    cnt28_raw = test["dest_obs_cnt_28d"].to_numpy(dtype=np.float64)
    cv28_fixed = np.where((cnt28_raw < 5) | (cv28_raw <= 0.0), 0.05, cv28_raw)
    test_cvfix = test.copy()
    test_cvfix["dest_price_cv_28d"] = cv28_fixed
    sc_safe_cvfix = score_safe_ev_sunk(test_cvfix)
    n_cv0_affected = int(((cv28_raw == 0.0) & (cnt28_raw >= 2)).sum())

    p_dow = test["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64)
    p_d = test["dest_lag_price"].to_numpy(dtype=np.float64)
    p_o = test["origin_lag_price"].to_numpy(dtype=np.float64)
    same_t = test["same_district"].to_numpy(dtype=bool)
    fee_r = np.where(same_t, 0.0, test["fee_rate"].to_numpy(dtype=np.float64))
    f_rd = test["freight_road"].to_numpy(dtype=np.float64)
    sp0_t = test["spoil_ref_0"].to_numpy(dtype=np.float64)
    tau_t = test["tau_days"].to_numpy(dtype=np.float64)
    hrs_t = test["truck_hours"].to_numpy(dtype=np.float64)
    sp_24tau_t = np.minimum(0.55, np.array([BASE_SPOIL_24H.get(str(c), 0.02) for c in test["Commodity"]]) * (24.0 * tau_t + hrs_t) / 24.0)

    sc_safe_spoil = p_dow * (p_d * (1.0 - cv28_raw) * (1.0 - sp0_t) * (1.0 - fee_r) - p_o) - f_rd
    sc_safe_z05 = p_dow * (p_d * (1.0 - 0.5 * cv28_raw) * (1.0 - fee_r) - p_o) - f_rd
    sc_safe_z15 = p_dow * (p_d * np.maximum(0.0, 1.0 - 1.5 * cv28_raw) * (1.0 - fee_r) - p_o) - f_rd
    p_dow_jef = np.clip((p_dow * 10.0 - 0.5) / 9.0, 0.05, 0.95)
    sc_safe_jef = p_dow_jef * (p_d * (1.0 - cv28_raw) * (1.0 - fee_r) - p_o) - f_rd

    # Ratio argmax vs product argmax
    g_1sd = p_d * (1.0 - cv28_raw) * (1.0 - fee_r) - p_o
    sc_ratio_safe = (g_1sd / np.maximum(f_rd, 1e-6)) - (1.0 / np.maximum(p_dow, 1e-6))
    ch_safe_prod = pick_episode(test, score_safe_ev_sunk(test), age_t13 & (score_safe_ev_sunk(test) > 0.0))
    ch_safe_ratio = pick_episode(test, sc_ratio_safe, age_t13 & (sc_ratio_safe > 0.0))
    n_ratio_switches = int((ch_safe_prod["eligible"] & (ch_safe_prod["dest_market"] != ch_safe_ratio["dest_market"])).sum())

    g_plain = p_d * (1.0 - fee_r) - p_o
    p_min = np.minimum(test["dest_exact_rep_28d"].to_numpy(dtype=np.float64), p_dow)
    sc_ratio_rt = (g_plain / np.maximum(2.0 * f_rd, 1e-6)) - (1.0 / np.maximum(p_min, 1e-6))
    ch_rt_prod = pick_episode(test, score_rt2f_min(test), age_t13 & (score_rt2f_min(test) > 0.0))
    ch_rt_ratio = pick_episode(test, sc_ratio_rt, age_t13 & (sc_ratio_rt > 0.0))
    n_rt_ratio_switches = int((ch_rt_prod["eligible"] & (ch_rt_prod["dest_market"] != ch_rt_ratio["dest_market"])).sum())

    for fname, ch_f, note in (
        ("Formula_Safe_EV_cv28_zero_fixed", pick_episode(test_cvfix, sc_safe_cvfix, age_t13 & (sc_safe_cvfix > 0.0)), f"floor 0.05 if cnt28<5 or cv28==0 ({n_cv0_affected} cand rows)"),
        ("Formula_Safe_EV_spoil_aware", pick_episode(test, sc_safe_spoil, age_t13 & (sc_safe_spoil > 0.0)), "Includes spoil_ref_0 inside G_1SD"),
        ("Formula_Safe_EV_z05", pick_episode(test, sc_safe_z05, age_t13 & (sc_safe_z05 > 0.0)), "z=0.5 SD multiplier"),
        ("Formula_Safe_EV_z15", pick_episode(test, sc_safe_z15, age_t13 & (sc_safe_z15 > 0.0)), "z=1.5 SD multiplier"),
        ("Formula_Safe_EV_Jeffreys_p", pick_episode(test, sc_safe_jef, age_t13 & (sc_safe_jef > 0.0)), "Beta(0.5,0.5) prior proxy"),
        ("Argmax_Ratio_Safe_EV", ch_safe_ratio, f"argmax (G_1SD/F - 1/p_dow); {n_ratio_switches} dest switches vs product"),
        ("Argmax_Ratio_RT_2F", ch_rt_ratio, f"argmax (G/2F - 1/p_min); {n_rt_ratio_switches} dest switches vs product"),
    ):
        r = _extended_metrics_v7(fname, ch_f, test_ot)
        r["group"] = "formula_audit"
        r["note"] = note
        rows.append(r)

    # 2x2 Orthogonal Decomposition (p_dow vs cv28) under both Closed-Yard and Open-MAR + Scale-Invariant EV
    g1_fix = p_d * (1.0 - cv28_fixed) * (1.0 - fee_r) - p_o
    sc_pure_cv28 = g1sd_s = g_1sd - f_rd
    sc_pure_pdow = p_dow * g_plain - f_rd
    sc_scale_24tau = p_dow * (g1_fix - f_rd - p_d * sp_24tau_t) - (1.0 - p_dow) * (1.5 * f_rd + p_o * sp_24tau_t)
    div_mask_t = np.char.startswith(test_ot.astype(str), "no_comm_divert")
    y_open_t = np.where(div_mask_t, p_d * (1.0 - sp0_t) * (1.0 - fee_r) - f_rd - test["settle_local_price_d0"].to_numpy(dtype=np.float64), test["y"].to_numpy(dtype=np.float64))
    ot_open_t = np.where(div_mask_t, "open_yard_mar_silent", test_ot.astype(str))
    ortho_specs = [
        ("B2_age_matched", tf["net_road_fee"], age_t13 & (tf["net_road_fee"] > 200.0), "B2 reference (th=200)"),
        ("Safe_EV_Sunk_m0", score_safe_ev_sunk(test), age_t13 & (score_safe_ev_sunk(test) > 0.0), "Combined p_dow + cv28"),
        ("Ortho_Pure_cv28_only", sc_pure_cv28, age_t13 & (sc_pure_cv28 > 0.0), "p_dow=1.0 (G_1SD - F > 0): isolates volatility haircut"),
        ("Ortho_Pure_pdow_only", sc_pure_pdow, age_t13 & (sc_pure_pdow > 0.0), "cv28=0.0 (p_dow*G - F > 0): isolates clerk-blank screen"),
        ("ScaleInv_Safe_EV_24tau", sc_scale_24tau, age_t13 & (sc_scale_24tau > 0.0), "Full 24*tau return/sell spoilage + 1.5F + cv28_fix"),
        ("ScaleInv_Safe_EV_pFloor50", score_safe_ev_sunk(test), age_t13 & (score_safe_ev_sunk(test) > 0.0) & (p_dow >= 0.50), "Safe_EV + hard p_dow >= 0.50 reliability floor"),
    ]
    for settle_lbl, y_eval, ot_eval in (("closed_yard_ortho", test["y"].to_numpy(dtype=np.float64), test_ot), ("open_mar_ortho", y_open_t, ot_open_t)):
        test_tmp = test.copy()
        test_tmp["y"] = y_eval
        for pname, sc_o, el_o, note in ortho_specs:
            ch_o = pick_episode(test_tmp, sc_o, el_o)
            r = _extended_metrics_v7(pname, ch_o, ot_eval)
            r["group"] = settle_lbl
            r["note"] = note
            rows.append(r)

    # Unrestricted menus (top_k=None, min_lag_spread=100 vs min_lag_spread=0)
    for sp_lbl, min_sp in (("Unrestricted_topK_None_sp100", 100.0), ("Unrestricted_topK_None_sp0", 0.0)):
        df_un, _ = build_lagged_candidates_from_frames(raw_171, cor, fees, clim_df=None, grade_explicit=False, min_lag_spread=min_sp, top_k=None)
        df_un["date"] = pd.to_datetime(df_un["date"])
        df_un["y"] = settle_candidates(df_un, how="sequential", weather="none", div=1.5, disc=0.10)
        val_u = df_un[df_un["date"] <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
        test_u = df_un[df_un["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
        _, ot_u = settle_candidates(test_u, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
        tf_u = compute_decision_features(test_u)
        vf_u = compute_decision_features(val_u)
        th_b2_u, _ = tune_threshold_on_val(val_u, vf_u, "net_road_fee", lambda ft: (ft["age"] >= 1) & (ft["age"] <= 3))
        a_tu = (tf_u["age"] >= 1) & (tf_u["age"] <= 3)
        for pname, sc_u, el_u in (
            ("B1_lagged_screen", tf_u["lag_spread"], np.ones(len(test_u), dtype=bool)),
            ("B2_age_matched", tf_u["net_road_fee"], a_tu & (tf_u["net_road_fee"] > th_b2_u)),
            ("Safe_EV_Sunk_m0", score_safe_ev_sunk(test_u), a_tu & (score_safe_ev_sunk(test_u) > 0.0)),
            ("RT_2F_Min_m0", score_rt2f_min(test_u), a_tu & (score_rt2f_min(test_u) > 0.0)),
        ):
            r = _extended_metrics_v7(pname, pick_episode(test_u, sc_u, el_u), ot_u)
            r["group"] = sp_lbl
            r["note"] = f"test_rows={len(test_u)}, th_b2={th_b2_u:.1f}"
            rows.append(r)

    meta = {
        "val_purged_episodes_dropped": n_spilled,
        "cal_full": cal_full,
        "cal_purged": cal_purged,
        "intact_t4_q_conf80": round(q_conf80, 4),
        "cqr5m_dest_switches_vs_raw": cqr5m_dest_switches,
        "cqr17m_q_scale80": round(q_cqr17, 4),
        "cqr17m_dest_switches_vs_raw": cqr17m_dest_switches,
        "train_17m_episodes": n_ep_17m,
        "safe_ev_ratio_dest_switches": n_ratio_switches,
        "rt2f_ratio_dest_switches": n_rt_ratio_switches,
        "cv28_zero_bug_candidate_rows": n_cv0_affected,
    }
    return pd.DataFrame(rows), meta


# ---------------------------------------------------------------------------
# Exp 6.5: Outlier Cleaning, Grade-Explicit, Exact-All5, SUTVA Crowding, NASA Decade & Inference
# ---------------------------------------------------------------------------
def _rebuild_decade_clean166(raw_decade: pd.DataFrame, mkt_set_171: set, cor: pd.DataFrame, fees: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    dec_17_23 = raw_decade[pd.to_datetime(raw_decade["Arrival_Date"]) <= pd.Timestamp("2023-12-31")].copy().reset_index(drop=True)
    m166 = [(s, m) in mkt_set_171 for s, m in zip(dec_17_23["State"].astype(str), dec_17_23["Market"].astype(str))]
    dec_df, _ = build_lagged_candidates_from_frames(
        raw_df=dec_17_23.loc[m166].copy().reset_index(drop=True),
        corridors_df=cor, fee_params_df=fees, clim_df=None, grade_explicit=False,
        min_origin_date="2018-01-01", max_origin_date="2023-12-26",
    )
    dec_17_only, _ = build_lagged_candidates_from_frames(
        raw_df=dec_17_23.loc[m166].copy().reset_index(drop=True),
        corridors_df=cor, fee_params_df=fees, clim_df=None, grade_explicit=False,
        min_origin_date="2017-01-01", max_origin_date="2017-12-26",
    )
    return dec_df, dec_17_only


def run_exp5_hygiene_sutva_inference(
    raw_171: pd.DataFrame,
    raw_decade: pd.DataFrame,
    cor: pd.DataFrame,
    fees: pd.DataFrame,
    coords: pd.DataFrame,
    wx_decade: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    test_ot: np.ndarray,
    chosen: Dict[str, pd.DataFrame],
    kappa_star: float,
    mkt_set_171: set,
) -> Tuple[pd.DataFrame, dict]:
    rows = []

    # 1) 369-row extreme price-outlier filter rebuild
    bad_ext = (
        (raw_171["Min_Price"] < 100.0) | (raw_171["Modal_Price"] < 100.0) | (raw_171["Max_Price"] < 100.0)
        | ((raw_171["Commodity"] != "Apple") & ((raw_171["Modal_Price"] > 15000.0) | (raw_171["Max_Price"] > 15000.0)))
    )
    n_ext_dropped = int(bad_ext.sum())
    df_clean, _ = build_lagged_candidates_from_frames(raw_171.loc[~bad_ext].copy().reset_index(drop=True), cor, fees, clim_df=None, grade_explicit=False)
    df_clean["date"] = pd.to_datetime(df_clean["date"])
    df_clean["y"], ot_clean = settle_candidates(df_clean, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    df_clean["_ot"] = ot_clean
    val_cl = df_clean[df_clean["date"] <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    test_cl = df_clean[df_clean["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    cal_cl = _standard_val_calibrate(val_cl, kappa_star)
    sc_cl = _score_core_subset(test_cl, cal_cl["th_b2"], cal_cl["m_mg"], kappa_star, cal_cl["m_rr"], cal_cl["m_safe"])
    ch_cl = _eval_policies_dict(test_cl, sc_cl, test_cl["_ot"].to_numpy())
    bdf_cl = ch_cl["B2_age_matched"][["episode_id", "date", "origin_market_key"]].copy()
    for p in ("B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
        bdf_cl[p] = ch_cl[p]["y"].to_numpy()
        bdf_cl[f"{p}_disp"] = ch_cl[p]["eligible"].to_numpy()
    boot_cl = two_way_cluster_bootstrap_extended(bdf_cl, "Safe_EV_Sunk_m0", "B2_age_matched", "Safe_EV_Sunk_m0_disp", "B2_age_matched_disp", reps=2000, seed=20261117)
    for p in ("B1_lagged_screen", "B2_age_matched", "Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "RT_2F_Min_m0"):
        r = _extended_metrics_v7(p, ch_cl[p], test_cl["_ot"].to_numpy())
        r["slice_check"] = f"OutlierClean369_N{test_cl['episode_id'].nunique()}"
        r["p_vs_B2_es10"] = round(boot_cl["es10"]["p_value_two_sided"], 6) if p == "Safe_EV_Sunk_m0" else np.nan
        r["p_vs_B2_cond_es10"] = round(boot_cl["cond_es10"]["p_value_two_sided"], 6) if p == "Safe_EV_Sunk_m0" else np.nan
        rows.append(r)

    # 2) Grade-explicit=True rebuild across all 6 states
    df_ge, _ = build_lagged_candidates_from_frames(raw_171, cor, fees, clim_df=None, grade_explicit=True)
    df_ge["date"] = pd.to_datetime(df_ge["date"])
    df_ge["y"], ot_ge = settle_candidates(df_ge, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    df_ge["_ot"] = ot_ge
    val_ge = df_ge[df_ge["date"] <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    test_ge = df_ge[df_ge["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    cal_ge = _standard_val_calibrate(val_ge, kappa_star)
    sc_ge = _score_core_subset(test_ge, cal_ge["th_b2"], cal_ge["m_mg"], kappa_star, cal_ge["m_rr"], cal_ge["m_safe"])
    ch_ge = _eval_policies_dict(test_ge, sc_ge, test_ge["_ot"].to_numpy())
    for p in ("B1_lagged_screen", "B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
        r = _extended_metrics_v7(p, ch_ge[p], test_ge["_ot"].to_numpy())
        r["slice_check"] = "GradeExplicit_6State"
        rows.append(r)

    # 3) Pure all-5 exact-geocode subset (N = 19,362) + Non-Collided Exact-Geocode audit (excluding clean_market_query parent collisions)
    mc = coords[["State", "Market", "geocode_precision", "lat", "lon"]].drop_duplicates(["State", "Market"]).copy()
    exact_set = set(zip(mc.loc[mc["geocode_precision"] == "market_exact", "State"], mc.loc[mc["geocode_precision"] == "market_exact", "Market"]))
    t_exact = np.array([((s, om) in exact_set) and ((s, dm) in exact_set) for s, om, dm in zip(test["State"], test["origin_market"], test["dest_market"])], dtype=bool)
    ep_all5 = pd.Series(t_exact).groupby(test["episode_id"]).transform("all").to_numpy()
    sub_all5 = test.loc[ep_all5].copy().reset_index(drop=True)
    bdf_a5 = chosen["B2_age_matched"][["episode_id", "date", "origin_market_key"]].copy()
    ep_set_a5 = set(sub_all5["episode_id"].unique())
    m_a5 = bdf_a5["episode_id"].isin(ep_set_a5).to_numpy()
    bdf_a5 = bdf_a5.loc[m_a5].reset_index(drop=True)
    for p in ("B1_lagged_screen", "B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
        bdf_a5[p] = chosen[p].loc[m_a5, "y"].to_numpy()
        bdf_a5[f"{p}_disp"] = chosen[p].loc[m_a5, "eligible"].to_numpy()
    boot_a5 = two_way_cluster_bootstrap_extended(bdf_a5, "Safe_EV_Sunk_m0", "B2_age_matched", "Safe_EV_Sunk_m0_disp", "B2_age_matched_disp", reps=2000, seed=20261117)
    for p in ("B1_lagged_screen", "B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
        vals_a5 = bdf_a5[p].to_numpy()
        disp_a5 = bdf_a5[f"{p}_disp"].to_numpy()
        rows.append({
            "policy": p, "n": len(vals_a5), "dispatch_rate": round(float(disp_a5.mean()), 4),
            "mean": round(float(vals_a5.mean()), 2), "ep_loss_rate": round(float((vals_a5 < 0).mean()), 4),
            "es10": round(float(es10(vals_a5)), 2),
            "cond_es10": round(float(es_alpha(vals_a5[disp_a5], 0.10)), 2),
            "slice_check": f"PureAll5_ExactGeocode_N{len(vals_a5)}",
            "p_vs_B2_es10": round(boot_a5["es10"]["p_value_two_sided"], 6) if p == "Safe_EV_Sunk_m0" else np.nan,
            "p_vs_B2_cond_es10": round(boot_a5["cond_es10"]["p_value_two_sided"], 6) if p == "Safe_EV_Sunk_m0" else np.nan,
        })

    # Coordinate-uniqueness audit across the 171 primary markets (exposing parent-town collisions in legacy geocoding)
    mc171 = mc[[(str(s), str(m)) in mkt_set_171 for s, m in zip(mc["State"], mc["Market"])]].copy()
    mc171["coord_mult"] = mc171.groupby(["State", "lat", "lon"])["Market"].transform("count")
    collided_171 = int((mc171["coord_mult"] > 1).sum())
    falsely_exact_171 = int(((mc171["coord_mult"] > 1) & (mc171["geocode_precision"] == "market_exact")).sum())
    nc_exact_set = set(zip(
        mc171.loc[(mc171["geocode_precision"] == "market_exact") & (mc171["coord_mult"] == 1), "State"],
        mc171.loc[(mc171["geocode_precision"] == "market_exact") & (mc171["coord_mult"] == 1), "Market"],
    ))
    t_exact_nc = np.array([((s, om) in nc_exact_set) and ((s, dm) in nc_exact_set) for s, om, dm in zip(test["State"], test["origin_market"], test["dest_market"])], dtype=bool)
    non_collided_exact_row_pct = round(float(t_exact_nc.mean() * 100.0), 2)
    ep_all5_nc = pd.Series(t_exact_nc).groupby(test["episode_id"]).transform("all").to_numpy()
    ep_set_nc = set(test.loc[ep_all5_nc, "episode_id"].unique())
    m_nc = chosen["B2_age_matched"]["episode_id"].isin(ep_set_nc).to_numpy()
    bdf_nc = chosen["B2_age_matched"].loc[m_nc, ["episode_id", "date", "origin_market_key"]].copy().reset_index(drop=True)
    for p in ("B1_lagged_screen", "B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
        bdf_nc[p] = chosen[p].loc[m_nc, "y"].to_numpy()
        bdf_nc[f"{p}_disp"] = chosen[p].loc[m_nc, "eligible"].to_numpy()
    boot_nc = two_way_cluster_bootstrap_extended(bdf_nc, "Safe_EV_Sunk_m0", "B2_age_matched", "Safe_EV_Sunk_m0_disp", "B2_age_matched_disp", reps=2000, seed=20261117)
    for p in ("B1_lagged_screen", "B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
        vals_nc = bdf_nc[p].to_numpy()
        disp_nc = bdf_nc[f"{p}_disp"].to_numpy()
        rows.append({
            "policy": p, "n": len(vals_nc), "dispatch_rate": round(float(disp_nc.mean()), 4),
            "mean": round(float(vals_nc.mean()), 2), "ep_loss_rate": round(float((vals_nc < 0).mean()), 4),
            "es10": round(float(es10(vals_nc)), 2),
            "cond_es10": round(float(es_alpha(vals_nc[disp_nc], 0.10)), 2),
            "slice_check": f"PureAll5_NonCollided_Exact_N{len(vals_nc)}",
            "p_vs_B2_es10": round(boot_nc["es10"]["p_value_two_sided"], 6) if p == "Safe_EV_Sunk_m0" else np.nan,
            "p_vs_B2_cond_es10": round(boot_nc["cond_es10"]["p_value_two_sided"], 6) if p == "Safe_EV_Sunk_m0" else np.nan,
        })

    # 3B) Compositional vs Routing Decomposition on Common Dispatched Intersection (D_S ∩ D_B),
    # 6 a.m. Phone-Call Counterfactual, Outsider Min_Price + LCV + Arhtiya Stress, & HP Apple Scale Non-Invariance
    el_s_e = chosen["Safe_EV_Sunk_m0"]["eligible"].to_numpy(dtype=bool)
    el_b_e = chosen["B2_age_matched"]["eligible"].to_numpy(dtype=bool)
    y_s_raw = chosen["Safe_EV_Sunk_m0"]["y_raw"].to_numpy(dtype=np.float64)
    y_b_raw = chosen["B2_age_matched"]["y_raw"].to_numpy(dtype=np.float64)
    both_el = el_s_e & el_b_e
    b_only_el = el_b_e & (~el_s_e)
    s_only_el = el_s_e & (~el_b_e)
    common_decomp = {
        "n_common_intersection": int(both_el.sum()),
        "safe_common_mean": round(float(y_s_raw[both_el].mean()), 2),
        "b2_common_mean": round(float(y_b_raw[both_el].mean()), 2),
        "common_mean_diff": round(float(y_s_raw[both_el].mean() - y_b_raw[both_el].mean()), 2),
        "safe_common_es10": round(float(es_alpha(y_s_raw[both_el], 0.10)), 2),
        "b2_common_es10": round(float(es_alpha(y_b_raw[both_el], 0.10)), 2),
        "common_es10_diff": round(float(es_alpha(y_s_raw[both_el], 0.10) - es_alpha(y_b_raw[both_el], 0.10)), 2),
        "pruned_b2_only_n": int(b_only_el.sum()),
        "pruned_b2_only_mean": round(float(y_b_raw[b_only_el].mean()), 2),
        "pruned_b2_only_loss_rate": round(float((y_b_raw[b_only_el] < 0).mean()), 4),
        "pruned_b2_only_es10": round(float(es_alpha(y_b_raw[b_only_el], 0.10)), 2),
        "added_safe_only_n": int(s_only_el.sum()),
        "added_safe_only_mean": round(float(y_s_raw[s_only_el].mean()), 2),
        "added_safe_only_es10": round(float(es_alpha(y_s_raw[s_only_el], 0.10)), 2),
    }
    rows.append({
        "policy": "Safe_EV_Sunk_m0", "n": int(both_el.sum()), "dispatch_rate": 1.0,
        "mean": common_decomp["safe_common_mean"], "ep_loss_rate": round(float((y_s_raw[both_el] < 0).mean()), 4),
        "es10": common_decomp["safe_common_es10"], "cond_es10": common_decomp["safe_common_es10"],
        "slice_check": "CommonIntersection_DS_cap_DB",
    })
    rows.append({
        "policy": "B2_age_matched", "n": int(both_el.sum()), "dispatch_rate": 1.0,
        "mean": common_decomp["b2_common_mean"], "ep_loss_rate": round(float((y_b_raw[both_el] < 0).mean()), 4),
        "es10": common_decomp["b2_common_es10"], "cond_es10": common_decomp["b2_common_es10"],
        "slice_check": "CommonIntersection_DS_cap_DB",
    })

    # PhoneCall_TopK_Open counterfactual: skip no_comm_divert candidates via 6 a.m. arhtiya confirmation call
    tf_ph = compute_decision_features(test)
    age_ph = (tf_ph["age"] >= 1) & (tf_ph["age"] <= 3)
    not_div = ~np.char.startswith(test_ot.astype(str), "no_comm_divert")
    fee_ph = np.where(test["same_district"].to_numpy(dtype=bool), 0.0, test["fee_rate"].to_numpy(dtype=np.float64))
    g1_ph = test["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - test["dest_price_cv_28d"].fillna(0.05).to_numpy(dtype=np.float64)) * (1.0 - fee_ph) - test["origin_lag_price"].to_numpy(dtype=np.float64)
    sc_pure_cv_ph = g1_ph - test["freight_road"].to_numpy(dtype=np.float64)
    for ph_name, ph_sc, ph_el in (
        ("B2_age_matched", tf_ph["net_road_fee"], age_ph & (tf_ph["net_road_fee"] > 200.0) & not_div),
        ("Pure_cv28_only", sc_pure_cv_ph, age_ph & (sc_pure_cv_ph > 0.0) & not_div),
        ("Safe_EV_Sunk_m0", score_safe_ev_sunk(test), age_ph & (score_safe_ev_sunk(test) > 0.0) & not_div),
    ):
        ch_ph = pick_episode(test, ph_sc, ph_el)
        r_ph = _extended_metrics_v7(ph_name, ch_ph, test_ot)
        r_ph["slice_check"] = "PhoneCall_TopK_Open"
        rows.append(r_ph)

    # Outsider Min_Price / Mid(Modal,Min) discrimination + LCV freight (₹60 + ₹0.75/km) + 4% arhtiya commission
    for out_lbl, mix_w in (("Outsider_Mid_LCV_4pctArh", 0.50), ("Outsider_MinPrice_LCV_4pctArh", 0.00)):
        test_out = test.copy()
        same_o = test_out["same_district"].to_numpy(dtype=bool)
        for d_i in (0, 1, 2):
            m_col, mn_col = f"settle_dest_modal_d{d_i}", f"settle_dest_min_d{d_i}"
            mod_v = test_out[m_col].to_numpy(dtype=np.float64)
            min_v = np.where(np.isfinite(test_out[mn_col].to_numpy(dtype=np.float64)), test_out[mn_col].to_numpy(dtype=np.float64), mod_v)
            adj_v = np.where(same_o, mod_v, mix_w * mod_v + (1.0 - mix_w) * min_v)
            test_out[m_col] = np.where(np.isfinite(mod_v), adj_v, np.nan)
        y_out, ot_out = settle_candidates(test_out, how="sequential", weather="none", div=1.5, disc=0.10, freight_base=60.0, freight_per_km=0.75, arhtiya_rate=0.04, return_outcomes=True)
        test_out["y"] = y_out
        sc_o = _score_core_subset(test_out, cal_base_th := 200.0, 0.0, kappa_star, 0.0, 0.0)
        for p in ("B1_lagged_screen", "B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
            sc_v, el_v = sc_o[p]
            r_o = _extended_metrics_v7(p, pick_episode(test_out, sc_v, el_v), ot_out)
            r_o["slice_check"] = out_lbl
            rows.append(r_o)

    # Winner's Curse, cv28 small-n diagnostic, & HP Apple Scale Non-Invariance
    ex0_b1 = chosen["B1_lagged_screen"]["_i"].to_numpy()[test_ot[chosen["B1_lagged_screen"]["_i"].to_numpy()] == "exact_d0"]
    wc_orig = float((test["settle_local_price_d0"].to_numpy(dtype=np.float64) - test["origin_lag_price"].to_numpy(dtype=np.float64)).mean())
    wc_dest = float((test["settle_dest_modal_d0"].to_numpy(dtype=np.float64)[ex0_b1] - test["dest_lag_price"].to_numpy(dtype=np.float64)[ex0_b1]).mean())
    cnt28_s = test["dest_obs_cnt_28d"].to_numpy(dtype=np.float64)[chosen["Safe_EV_Sunk_m0"]["_i"].to_numpy()][el_s_e]
    ys_d_s = y_s_raw[el_s_e]
    m_le4 = cnt28_s <= 4.0

    # HP Graded Apple scale non-invariance audit
    hp_df = pd.read_parquet(OUT_DIR / "lagged_hp_apple_candidates.parquet").reset_index(drop=True)
    y_hp, ot_hp = settle_candidates(hp_df, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    hp_df["y"] = y_hp
    f_hp = compute_decision_features(hp_df)
    a_hp = (f_hp["age"] >= 1) & (f_hp["age"] <= 3)
    p_dow_hp = hp_df["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64)
    fee_hp = np.where(hp_df["same_district"].to_numpy(dtype=bool), 0.0, hp_df["fee_rate"].to_numpy(dtype=np.float64))
    cv_hp = hp_df["dest_price_cv_28d"].fillna(0.05).to_numpy(dtype=np.float64)
    cnt_hp = hp_df["dest_obs_cnt_28d"].fillna(0.0).to_numpy(dtype=np.float64)
    cv_hp_fix = np.where((cnt_hp < 5.0) | (cv_hp <= 0.0), 0.05, cv_hp)
    p_d_hp = hp_df["dest_lag_price"].to_numpy(dtype=np.float64)
    p_o_hp = hp_df["origin_lag_price"].to_numpy(dtype=np.float64)
    fr_hp = hp_df["freight_road"].to_numpy(dtype=np.float64)
    g1_hp = p_d_hp * (1.0 - cv_hp) * (1.0 - fee_hp) - p_o_hp
    g1_hp_fix = p_d_hp * (1.0 - cv_hp_fix) * (1.0 - fee_hp) - p_o_hp
    sp_24_hp = np.minimum(0.55, 0.0164 * (24.0 * hp_df["tau_days"].to_numpy(dtype=np.float64) + hp_df["truck_hours"].to_numpy(dtype=np.float64)) / 24.0)
    sc_hp_scale = p_dow_hp * (g1_hp_fix - fr_hp - p_d_hp * sp_24_hp) - (1.0 - p_dow_hp) * (1.5 * fr_hp + p_o_hp * sp_24_hp)
    ch_hp_safe = pick_episode(hp_df, score_safe_ev_sunk(hp_df), a_hp & (score_safe_ev_sunk(hp_df) > 0.0))
    idx_hp_s = ch_hp_safe["_i"].to_numpy()[ch_hp_safe["eligible"].to_numpy(dtype=bool)]
    hp_frac_lt_010 = round(float((fr_hp[idx_hp_s] / np.maximum(g1_hp[idx_hp_s], 1e-6) < 0.10).mean() * 100.0), 2)
    for hp_lbl, hp_sc, hp_el in (
        ("B2_age_matched", f_hp["net_road_fee"], a_hp & (f_hp["net_road_fee"] > 200.0)),
        ("Safe_EV_Sunk_m0", score_safe_ev_sunk(hp_df), a_hp & (score_safe_ev_sunk(hp_df) > 0.0)),
        ("Pure_cv28_only", g1_hp - fr_hp, a_hp & ((g1_hp - fr_hp) > 0.0)),
        ("Safe_EV_Sunk_pFloor50", score_safe_ev_sunk(hp_df), a_hp & (score_safe_ev_sunk(hp_df) > 0.0) & (p_dow_hp >= 0.50)),
        ("ScaleInv_Safe_EV_24tau", sc_hp_scale, a_hp & (sc_hp_scale > 0.0)),
    ):
        r_hp = _extended_metrics_v7(hp_lbl, pick_episode(hp_df, hp_sc, hp_el), ot_hp)
        r_hp["slice_check"] = "HP_Apple_ScaleNonInv"
        rows.append(r_hp)

    # 4) SUTVA Crowding & Price-Impact Elasticity Stress on primary chosen policies
    arr_dates = pd.to_datetime(test["arrival_date"])
    vkeys = test["Variety_Key"]
    for p in ("B1_lagged_screen", "B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
        ch = chosen[p].copy()
        idx = ch["_i"].to_numpy()
        el = ch["eligible"].to_numpy(dtype=bool)
        ch["arr_date"] = arr_dates.iloc[idx].to_numpy()
        ch["vk"] = vkeys.iloc[idx].to_numpy()
        # Count simultaneous dispatches targeting identical (arr_date, State, Commodity, vk, dest_market)
        herd_cnt = np.ones(len(ch), dtype=np.int32)
        if el.any():
            sub_e = ch.loc[el]
            grp_c = sub_e.groupby(["arr_date", "State", "Commodity", "vk", "dest_market"]).transform("size").to_numpy(dtype=np.int32)
            herd_cnt[el] = grp_c
        ex_open = el & (test_ot[idx] == "exact_d0")
        p_d0 = test["settle_dest_modal_d0"].to_numpy(dtype=np.float64)[idx]
        for impact_rate, lbl_s in ((0.05, "SUTVA_Impact_5pctPerExtraTruck"), (0.10, "SUTVA_Impact_10pctPerExtraTruck")):
            pen = np.where(ex_open & (herd_cnt > 1), p_d0 * np.minimum(0.35, impact_rate * (herd_cnt - 1)), 0.0)
            y_imp = np.where(el, ch["y_raw"].to_numpy() - pen, 0.0)
            rows.append({
                "policy": p, "n": len(ch), "dispatch_rate": round(float(el.mean()), 4),
                "mean": round(float(y_imp.mean()), 2), "ep_loss_rate": round(float((y_imp < 0).mean()), 4),
                "es10": round(float(es10(y_imp)), 2), "cond_es10": round(float(es_alpha(y_imp[el], 0.10)), 2),
                "slice_check": lbl_s,
            })
        # Cap simultaneous herd at k <= 2 (surplus earliest tie-breakers abstain home -> 0)
        order_rk = np.zeros(len(ch), dtype=np.int32)
        if el.any():
            sub_e = ch.loc[el].sort_values(["arr_date", "State", "Commodity", "vk", "dest_market", "origin_market_key"])
            rks = sub_e.groupby(["arr_date", "State", "Commodity", "vk", "dest_market"]).cumcount().to_numpy() + 1
            order_rk[sub_e.index.to_numpy()] = rks
        keep_k2 = el & (order_rk <= 2)
        y_k2 = np.where(keep_k2, ch["y_raw"].to_numpy(), 0.0)
        rows.append({
            "policy": p, "n": len(ch), "dispatch_rate": round(float(keep_k2.mean()), 4),
            "mean": round(float(y_k2.mean()), 2), "ep_loss_rate": round(float((y_k2 < 0).mean()), 4),
            "es10": round(float(es10(y_k2)), 2), "cond_es10": round(float(es_alpha(y_k2[keep_k2], 0.10)), 2) if keep_k2.any() else np.nan,
            "slice_check": "SUTVA_CapacityCap_k2",
        })

    # 5) Clean 166-mkt Decade: 2017-tuned B2, CPI-deflated threshold, & realized NASA POWER 2018-2023 weather
    dec_166, dec_17 = _rebuild_decade_clean166(raw_decade, mkt_set_171, cor, fees)
    dec_17["y"] = settle_candidates(dec_17, how="sequential", weather="none", div=1.5, disc=0.10)
    th_2017_b2, _ = tune_threshold_on_val(dec_17, compute_decision_features(dec_17), "net_road_fee", lambda ft: (ft["age"] >= 1) & (ft["age"] <= 3))
    dec_wx_df = _attach_full_era5(dec_166, coords, wx_decade, grid_step=0.5)
    # Use settle_realized_era5_sequential formula via _settle_custom with NABCONS or USDA Schedule 7
    y_dec_nasa, ot_dec_nasa, _ = _settle_custom(dec_wx_df, "nabcons_24tau", True, 35.0, 0.45, 1.0, 0.0)
    y_dec_usda_nasa, ot_dec_usda_nasa, _ = _settle_custom(dec_wx_df, "usda_sched7", True, 35.0, 0.45, 1.0, 0.0)
    y_dec_20c, ot_dec_20c = settle_candidates(dec_166, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    df_166 = compute_decision_features(dec_166)
    a166 = (df_166["age"] >= 1) & (df_166["age"] <= 3)

    # Year-median CPI scaling factor relative to 2025 validation median origin_lag_price
    med_2025 = float(val["origin_lag_price"].median())
    yr_dec = pd.to_datetime(dec_166["date"]).dt.year
    yr_meds = dec_166.groupby(yr_dec)["origin_lag_price"].transform("median").to_numpy(dtype=np.float64)
    th_cpi = 200.0 * (yr_meds / med_2025)

    for lbl_d, y_d, ot_d, b2_cut in (
        (f"Decade166_20C_2017TunedB2_th{th_2017_b2:.0f}", y_dec_20c, ot_dec_20c, th_2017_b2),
        ("Decade166_20C_CPIAdjustedB2", y_dec_20c, ot_dec_20c, th_cpi),
        ("Decade166_NASA_POWER_NABCONS", y_dec_nasa, ot_dec_nasa, 200.0),
        ("Decade166_NASA_POWER_USDA_Sched7", y_dec_usda_nasa, ot_dec_usda_nasa, 200.0),
    ):
        dec_166["y"] = y_d
        sc_d = {
            "B1_lagged_screen": (df_166["lag_spread"], np.ones(len(dec_166), dtype=bool)),
            "B2_age_matched": (df_166["net_road_fee"], a166 & (df_166["net_road_fee"] > b2_cut)),
            "Safe_EV_Sunk_m0": (score_safe_ev_sunk(dec_166), a166 & (score_safe_ev_sunk(dec_166) > 0.0)),
            "RT_2F_Min_m0": (score_rt2f_min(dec_166), a166 & (score_rt2f_min(dec_166) > 0.0)),
        }
        for p, (scv, elv) in sc_d.items():
            r = _extended_metrics_v7(p, pick_episode(dec_166, scv, elv), ot_d)
            r["slice_check"] = lbl_d
            rows.append(r)

    # 6) Complete Small-Cluster & Skewness Inference Audit (CGM + CSS G* + Studentized t + Webb6 + Joint val+test H_A18_2)
    inf_records = []
    bdf_all = chosen["B2_age_matched"][["episode_id", "date", "origin_market_key", "State", "Commodity"]].copy()
    for p in ("B2_age_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Sunk_matched", "RT_2F_Min_m0"):
        bdf_all[p] = chosen[p]["y"].to_numpy()
        bdf_all[f"{p}_dest_key"] = np.where(
            chosen[p]["eligible"].to_numpy(dtype=bool),
            chosen[p]["State"].astype(str) + "|" + chosen[p]["dest_market"].astype(str),
            chosen[p]["origin_market_key"].astype(str),
        )
    tests_cgm = [
        ("H_A18_1_origin_2w", bdf_all, "Safe_EV_Sunk_m0", "B2_age_matched", "es10", "origin_market_key", 2),
        ("H_A18_1_b2dest_2w", bdf_all, "Safe_EV_Sunk_m0", "B2_age_matched", "es10", "B2_age_matched_dest_key", 2),
        ("H_A18_2_origin_2w", bdf_all, "Safe_EV_Sunk_matched", "RR_Abstain_matched", "es10", "origin_market_key", 2),
        ("H_A18_2_b2dest_2w", bdf_all, "Safe_EV_Sunk_matched", "RR_Abstain_matched", "es10", "B2_age_matched_dest_key", 2),
        ("H_A18_3_origin_2w", bdf_all, "Safe_EV_Sunk_m0", "B2_age_matched", "ep_loss_rate", "origin_market_key", 2),
        ("H_A18_4_origin_2w", bdf_all, "RT_2F_Min_m0", "B2_age_matched", "mean", "origin_market_key", 2),
        ("4w_B12_Safe_Mean", bdf_all, "Safe_EV_Sunk_m0", "B2_age_matched", "mean", "origin_market_key", 4),
        ("4w_B12_Safe_ES10", bdf_all, "Safe_EV_Sunk_m0", "B2_age_matched", "es10", "origin_market_key", 4),
        ("4w_B12_RT_Mean", bdf_all, "RT_2F_Min_m0", "B2_age_matched", "mean", "origin_market_key", 4),
        ("HP_2w_B12_ES10", bdf_all[bdf_all["State"] == "Himachal Pradesh"].reset_index(drop=True), "Safe_EV_Sunk_m0", "B2_age_matched", "es10", "origin_market_key", 2),
        ("Apple_2w_ES10", bdf_all[bdf_all["Commodity"] == "Apple"].reset_index(drop=True), "Safe_EV_Sunk_m0", "B2_age_matched", "es10", "origin_market_key", 2),
    ]
    for tid, gdf, pa, pb, met, mcol, wlen in tests_cgm:
        cg = two_way_cgm_and_studentized_test(gdf, pa, pb, metric=met, mandi_col=mcol, week_block_len=wlen, reps=2000, seed=20261117)
        cg["test_id"] = tid
        cg["metric"] = met
        inf_records.append(cg)

    # Joint (val + test) block bootstrap for H_A18_2 (R=1,000, propagating validation threshold variance)
    vf_all = compute_decision_features(val)
    tf_all = compute_decision_features(test)
    val_age13 = (vf_all["age"] >= 1) & (vf_all["age"] <= 3)
    test_age13 = (tf_all["age"] >= 1) & (tf_all["age"] <= 3)
    # Pre-group val max score per episode for fast weighted quantile calculation
    v_ep_df = pd.DataFrame({
        "episode_id": val.groupby("episode_id", sort=False)["episode_id"].first().to_numpy(),
        "date": pd.to_datetime(val.groupby("episode_id", sort=False)["date"].first().to_numpy()),
        "origin_market_key": val.groupby("episode_id", sort=False)["origin_market_key"].first().to_numpy(),
        "sc_safe": pd.Series(np.where(val_age13, score_safe_ev_sunk(val), -1e18)).groupby(val["episode_id"], sort=False).max().to_numpy(),
        "sc_rr": pd.Series(np.where(val_age13, rr_abstain_score(val, kappa_star), -1e18)).groupby(val["episode_id"], sort=False).max().to_numpy(),
        "sc_b2": pd.Series(np.where(val_age13, vf_all["net_road_fee"], -1e18)).groupby(val["episode_id"], sort=False).max().to_numpy(),
    })
    # Fix target dispatch rate to full-sample val B2 target (~0.7043) or re-estimate B2 threshold? Keep target disp at th_b2=200 (grid argmin) weighted disp rate!
    b2_val_disp_vec = (v_ep_df["sc_b2"].to_numpy() > 200.0).astype(np.float64)
    # Map test episode-max candidate payoffs & scores for fast re-thresholding on weighted draw
    # Candidate scores sorted within episode for fast pickup would be slow; threshold changes only on matched cutoffs:
    # Approximate cleanly using episode top candidate above threshold grid or exact sorted cand mask per test episode!
    # Build fast episode arrays: sorted top score -> y_top (since age13 & score > m picks highest score among age13!)
    t_safe_df = test.loc[test_age13, ["episode_id", "date", "origin_market_key", "road_km", "dest_market", "y"]].copy()
    t_safe_df["sc"] = score_safe_ev_sunk(test)[test_age13]
    t_safe_top = t_safe_df.sort_values(["episode_id", "sc", "road_km", "dest_market"], ascending=[True, False, True, True]).groupby("episode_id", as_index=False).first()
    t_rr_df = test.loc[test_age13, ["episode_id", "date", "origin_market_key", "road_km", "dest_market", "y"]].copy()
    t_rr_df["sc"] = rr_abstain_score(test, kappa_star)[test_age13]
    t_rr_top = t_rr_df.sort_values(["episode_id", "sc", "road_km", "dest_market"], ascending=[True, False, True, True]).groupby("episode_id", as_index=False).first()
    # Align onto full test episode order
    base_eps = chosen["B2_age_matched"][["episode_id", "date", "origin_market_key"]].copy()
    base_eps = base_eps.merge(t_safe_top[["episode_id", "sc", "y"]].rename(columns={"sc": "s_sc", "y": "s_y"}), on="episode_id", how="left").fillna({"s_sc": -1e18, "s_y": 0.0})
    base_eps = base_eps.merge(t_rr_top[["episode_id", "sc", "y"]].rename(columns={"sc": "r_sc", "y": "r_y"}), on="episode_id", how="left").fillna({"r_sc": -1e18, "r_y": 0.0})

    # Pre-index val & test market codes + disjoint fortnight blocks
    all_mkts = sorted(set(v_ep_df["origin_market_key"].unique()) | set(base_eps["origin_market_key"].unique()))
    m2i_j = {m: i for i, m in enumerate(all_mkts)}
    vm = v_ep_df["origin_market_key"].map(m2i_j).to_numpy()
    tm_idx = base_eps["origin_market_key"].map(m2i_j).to_numpy()
    vb_c, _ = pd.factorize(((v_ep_df["date"] - v_ep_df["date"].min()).dt.days // 14).to_numpy())
    tb_c, _ = pd.factorize(((pd.to_datetime(base_eps["date"]) - pd.to_datetime(base_eps["date"]).min()).dt.days // 14).to_numpy())
    n_vm_b = int(vb_c.max()) + 1
    n_tm_b = int(tb_c.max()) + 1
    n_jm = len(all_mkts)

    ord_vs = np.argsort(v_ep_df["sc_safe"].to_numpy())
    v_sc_s_sorted = v_ep_df["sc_safe"].to_numpy()[ord_vs]
    ord_vr = np.argsort(v_ep_df["sc_rr"].to_numpy())
    v_sc_r_sorted = v_ep_df["sc_rr"].to_numpy()[ord_vr]

    rng_j = np.random.default_rng(20261117)
    j_diffs = np.empty(1000, dtype=np.float64)
    from revision.stats_utils import weighted_es10
    s_sc_t = base_eps["s_sc"].to_numpy()
    s_y_t = base_eps["s_y"].to_numpy()
    r_sc_t = base_eps["r_sc"].to_numpy()
    r_y_t = base_eps["r_y"].to_numpy()
    for r_i in range(1000):
        mw = np.bincount(rng_j.integers(0, n_jm, size=n_jm), minlength=n_jm).astype(np.float64)
        vbw = np.bincount(rng_j.integers(0, n_vm_b, size=n_vm_b), minlength=n_vm_b).astype(np.float64)
        tbw = np.bincount(rng_j.integers(0, n_tm_b, size=n_tm_b), minlength=n_tm_b).astype(np.float64)
        vw = mw[vm] * vbw[vb_c]
        tgt_r = float(np.sum(vw * b2_val_disp_vec) / max(1.0, float(vw.sum())))
        q_val = 1.0 - tgt_r
        # Weighted quantile for Safe & RR on val draw
        ws_v = vw[ord_vs]
        ms_idx = min(len(v_sc_s_sorted) - 1, int(np.searchsorted(np.cumsum(ws_v), q_val * ws_v.sum())))
        m_safe_star = float(v_sc_s_sorted[ms_idx])
        wr_v = vw[ord_vr]
        mr_idx = min(len(v_sc_r_sorted) - 1, int(np.searchsorted(np.cumsum(wr_v), q_val * wr_v.sum())))
        m_rr_star = float(v_sc_r_sorted[mr_idx])

        tw = mw[tm_idx] * tbw[tb_c]
        ys_star = np.where(s_sc_t > m_safe_star, s_y_t, 0.0)
        yr_star = np.where(r_sc_t > m_rr_star, r_y_t, 0.0)
        j_diffs[r_i] = weighted_es10(ys_star, tw) - weighted_es10(yr_star, tw)

    est_ha18_2 = float(es10(chosen["Safe_EV_Sunk_matched"]["y"].to_numpy()) - es10(chosen["RR_Abstain_matched"]["y"].to_numpy()))
    j_lo, j_hi = np.quantile(j_diffs, [0.025, 0.975])
    j_p_null = float((1 + np.sum(np.abs(j_diffs - est_ha18_2) >= abs(est_ha18_2))) / 1001.0)
    j_p_perc = float(min(1.0, 2.0 * (1 + np.sum(j_diffs <= 0.0)) / 1001.0))

    meta = {
        "outliers_dropped_raw": n_ext_dropped,
        "clean_test_episodes": int(test_cl["episode_id"].nunique()),
        "all5_exact_geocode_episodes": len(bdf_a5),
        "collided_markets_171": collided_171,
        "falsely_exact_markets_171": falsely_exact_171,
        "non_collided_exact_row_pct": non_collided_exact_row_pct,
        "non_collided_all5_exact_episodes": len(bdf_nc),
        "common_intersection_decomp": common_decomp,
        "winners_curse_lagspread100": {
            "origin_rebound_mean": round(wc_orig, 2),
            "b1_exact_d0_dest_reversion_mean": round(wc_dest, 2),
            "total_winners_curse_gap": round(wc_orig - wc_dest, 2),
        },
        "cv28_cnt_le_4_safe_dispatches": {
            "n": int(m_le4.sum()),
            "cond_loss_rate": round(float((ys_d_s[m_le4] < 0).mean()), 4) if m_le4.any() else 0.0,
            "cond_es10": round(float(es_alpha(ys_d_s[m_le4], 0.10)), 2) if m_le4.any() else 0.0,
        },
        "hp_apple_frac_f_over_g1sd_lt_010_pct": hp_frac_lt_010,
        "decade_166_2017_tuned_b2_threshold": float(th_2017_b2),
        "joint_val_test_H_A18_2": {
            "estimate": round(est_ha18_2, 2),
            "ci95_low": round(float(j_lo), 2),
            "ci95_high": round(float(j_hi), 2),
            "boot_se": round(float(np.std(j_diffs, ddof=1)), 2),
            "p_perc_2s": round(j_p_perc, 6),
            "p_null_cent_2s": round(j_p_null, 6),
        },
        "cgm_inference_table": [{k: (round(float(v), 5) if isinstance(v, float) else v) for k, v in rec.items()} for rec in inf_records],
    }
    return pd.DataFrame(rows), meta


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_a10 = json.loads((OUT_DIR / "a10_summary.json").read_text())
    kappa_star = float(summary_a10["kappa_star_matched"])

    raw = pd.read_parquet(ROOT / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet")
    raw_dec = pd.read_parquet(ROOT / "data/raw/agmarknet_6state_decade_2017_2026.parquet")
    cor = pd.read_parquet(ROOT / "data/processed/osrm_corridor_matrix.parquet")
    fees = pd.read_csv(ROOT / "data/processed/state_apmc_and_loss_parameters.csv")
    coords = pd.read_parquet(ROOT / "data/processed/mandi_coordinates.parquet")
    wx = pd.read_parquet(ROOT / "data/processed/mandi_weather_2024_2026.parquet")
    wx_dec = pd.read_parquet(ROOT / "data/processed/nasa_power_climate_2017_2023.parquet")

    mkts_2024 = get_2024_only_markets(raw, min_days=80, max_per_state=30)
    mkt_set_171 = set(zip(mkts_2024["State"].astype(str), mkts_2024["Market"].astype(str)))
    raw_171 = raw.loc[[(s, m) in mkt_set_171 for s, m in zip(raw["State"].astype(str), raw["Market"].astype(str))]].copy().reset_index(drop=True)

    df_171, _ = build_lagged_candidates_from_frames(raw_171, cor, fees, clim_df=None, grade_explicit=False)
    df_171["date"] = pd.to_datetime(df_171["date"])
    y_all, ot_all = settle_candidates(df_171, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    df_171["y"] = y_all
    df_171["_ot"] = ot_all
    val = df_171[df_171["date"] <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    test = df_171[df_171["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    test_ot = test["_ot"].to_numpy()
    cal_base = _standard_val_calibrate(val, kappa_star)
    sc_base = _score_core_subset(test, cal_base["th_b2"], cal_base["m_mg"], kappa_star, cal_base["m_rr"], cal_base["m_safe"])
    chosen = _eval_policies_dict(test, sc_base, test_ot)

    print("[Phase 6] Running Exp 6.1 (<= t - 2 portal latency)...", flush=True)
    e1_df, e1_meta = run_exp1_latency_t2(raw_171, cor, fees, kappa_star)
    e1_df.to_csv(OUT_DIR / "v7_exp1_latency_t2.csv", index=False)

    print("[Phase 6] Running Exp 6.2 (Schedule #7 x S6 x Stoch Cond-MAR x blind_wait)...", flush=True)
    e2_df, e2_meta = run_exp2_bio_s6_condmar(val, test, coords, wx, kappa_star, cal_base)
    e2_df.to_csv(OUT_DIR / "v7_exp2_bio_s6_condmar.csv", index=False)

    print("[Phase 6] Running Exp 6.3 (Manski bounds, Cross-Crop MNAR, Origin Sym, All-Open)...", flush=True)
    e3_df, e3_meta = run_exp3_manski_and_open(raw_171, cor, fees, test, test_ot, chosen)
    e3_df.to_csv(OUT_DIR / "v7_exp3_manski_and_open.csv", index=False)

    print("[Phase 6] Running Exp 6.4 (Purged Val, Clean ML/OR Pareto, Formula Audits)...", flush=True)
    e4_df, e4_meta = run_exp4_ml_pareto_and_formula(raw_171, cor, fees, val, test, test_ot, kappa_star)
    e4_df.to_csv(OUT_DIR / "v7_exp4_ml_pareto_and_formula.csv", index=False)

    print("[Phase 6] Running Exp 6.5 (Outliers, Grade, Exact-5, SUTVA, Decade NASA, CGM/Wild)...", flush=True)
    e5_df, e5_meta = run_exp5_hygiene_sutva_inference(raw_171, raw_dec, cor, fees, coords, wx_dec, val, test, test_ot, chosen, kappa_star, mkt_set_171)
    e5_df.to_csv(OUT_DIR / "v7_exp5_hygiene_sutva_inference.csv", index=False)

    summary_out = {
        "exp1_latency_t2": e1_meta,
        "exp2_bio_s6_condmar": e2_meta,
        "exp3_manski_and_open": e3_meta,
        "exp4_ml_pareto_and_formula": e4_meta,
        "exp5_hygiene_sutva_inference": e5_meta,
    }
    (OUT_DIR / "v7_exp_summary.json").write_text(json.dumps(summary_out, indent=2, default=float))
    print("=== PHASE 6 EXPERIMENTS COMPLETE ===", flush=True)


if __name__ == "__main__":
    run()
