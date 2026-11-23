"""Unified Revision v6 verification & upgrades module (Step 12).

Adds four strict methodological & robustness checks directly on tracked repo files
without altering any frozen A10 / A18 outputs (`R5`, `R8`, `R9`):
  1. Strict 2024-only 171-market panel rebuilt end-to-end from raw records (>= 80 days in 2024, <= 30/state —
     zero future market-selection OR Top-5 shortlist lookahead, with validation comparators re-calibrated on val_171).
  2. Realized ERA5 destination arrival-day weather settlement ONLY (zero weather in decisions; Q10 + RH +
     rain >= 35mm price/rot penalty), under both closed-yard sequential and open-yard MAR settlement.
  3. Exact algebraic break-even silent-market thresholds (INR/qtl extra shift, flat constant-payoff counterfactual,
     and homogeneous Open-MAR share theta*) across ALL four closed-yard panels, verified numerically to < 1e-6.
  4. R = 5,000 paired two-way cluster bootstrap across all 3 corrected State| clusterings + 1-week & 4-week calendar
     block-length checks + rebuilt 171-market & realized-ERA5 settlement panels (strict two-sided Holm p_holm_2s).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from revision.build_variant import build_lagged_candidates_from_frames, spoil_frac_ref
from revision.es10 import es10
from revision.eval_a10 import rr_abstain_score
from revision.eval_a18 import (
    _extended_metrics,
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
from revision.stats_utils import two_way_cluster_bootstrap_all_metrics
from src.evaluation.bootstrap import holm_bonferroni

ROOT = Path(__file__).resolve().parents[1]


def get_2024_only_markets(raw_df: pd.DataFrame, min_days: int = 80, max_per_state: int = 30) -> pd.DataFrame:
    """Select eligible markets strictly from 2024 data (zero future market-selection lookahead)."""
    dates = pd.to_datetime(raw_df["Arrival_Date"])
    r24 = raw_df.loc[dates.dt.year == 2024, ["State", "Market"]].copy()
    r24["date"] = dates.loc[dates.dt.year == 2024]
    days = r24.groupby(["State", "Market"])["date"].nunique().reset_index(name="n_days_2024")
    elig = days[days["n_days_2024"] >= min_days].sort_values(
        ["State", "n_days_2024", "Market"], ascending=[True, False, True]
    )
    return elig.groupby("State", group_keys=False).head(max_per_state).reset_index(drop=True)


def attach_realized_era5_settlement_weather(
    df: pd.DataFrame,
    coords_df: pd.DataFrame,
    wx_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, dict]:
    """Attach realized ERA5 arrival-day d=0,1,2 weather strictly for settlement (NEVER used in decisions)."""
    out = df.copy()
    c_map = coords_df[["State", "Market", "lat", "lon"]].drop_duplicates(["State", "Market"]).copy()
    c_map["grid_lat"] = c_map["lat"].round(1)
    c_map["grid_lon"] = c_map["lon"].round(1)
    c_map = c_map.rename(columns={"Market": "dest_market"})[["State", "dest_market", "grid_lat", "grid_lon"]]
    out = out.merge(c_map, on=["State", "dest_market"], how="left")

    wx = wx_df[["grid_lat", "grid_lon", "date", "era5_tmax", "era5_rh_mean", "era5_rain_mm"]].copy()
    wx["date"] = pd.to_datetime(wx["date"])
    wx = wx.drop_duplicates(["grid_lat", "grid_lon", "date"])

    arr_base = pd.to_datetime(out["arrival_date"])
    matched_rates = {}
    for d in (0, 1, 2):
        out[f"_arr_d{d}"] = arr_base + pd.Timedelta(days=d)
        sub_wx = wx.rename(
            columns={
                "date": f"_arr_d{d}",
                "era5_tmax": f"settle_era5_tmax_d{d}",
                "era5_rh_mean": f"settle_era5_rh_d{d}",
                "era5_rain_mm": f"settle_era5_rain_d{d}",
            }
        )
        out = out.merge(sub_wx, on=["grid_lat", "grid_lon", f"_arr_d{d}"], how="left")
        matched_rates[f"d{d}_era5_coverage_pct"] = round(float(out[f"settle_era5_tmax_d{d}"].notna().mean() * 100.0), 2)
        out[f"settle_era5_tmax_d{d}"] = out[f"settle_era5_tmax_d{d}"].fillna(20.0)
        out[f"settle_era5_rh_d{d}"] = out[f"settle_era5_rh_d{d}"].fillna(65.0)
        out[f"settle_era5_rain_d{d}"] = out[f"settle_era5_rain_d{d}"].fillna(0.0)
        out.drop(columns=[f"_arr_d{d}"], inplace=True)
    out.drop(columns=["grid_lat", "grid_lon"], inplace=True)
    return out, matched_rates


def settle_realized_era5_sequential(
    df: pd.DataFrame,
    div: float = 1.5,
    disc: float = 0.10,
    detention_per_day: float = 25.0,
    open_yard_mar: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    """Non-anticipative sequential settlement using realized arrival-day ERA5 weather (T, RH, rain >= 35mm).

    Heavy rain (>= 35 mm) moves realized exact-variety sale price halfway toward reported Min_Price
    (when Min_Price > 0) and adds +0.02 spoilage fraction inside `spoil_frac_ref`.
    """
    n = len(df)
    comm = df["Commodity"].to_numpy()
    hours = df["truck_hours"].to_numpy(dtype=np.float64)
    f_road = df["freight_road"].to_numpy(dtype=np.float64)
    same = df["same_district"].to_numpy(dtype=bool)
    sale_fee_rate = np.where(same, 0.0, df["fee_rate"].to_numpy(dtype=np.float64))
    local = df["settle_local_price_d0"].to_numpy(dtype=np.float64)

    p_ex = [df[f"settle_dest_modal_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    p_min = [df[f"settle_dest_min_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    p_an = [df[f"settle_any_min_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    tmax = [df[f"settle_era5_tmax_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    rh = [df[f"settle_era5_rh_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    rain = [df[f"settle_era5_rain_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]

    def _sp(idx: np.ndarray, d: int) -> np.ndarray:
        return spoil_frac_ref(
            comm[idx],
            hours[idx],
            np.full(int(idx.sum()), d, dtype=np.float64),
            tmax[d][idx],
            rh[d][idx],
            rain[d][idx],
        )

    def _sell_exact(idx: np.ndarray, d: int) -> np.ndarray:
        sp = _sp(idx, d)
        mod = p_ex[d][idx]
        mn = p_min[d][idx]
        heavy = (rain[d][idx] >= 35.0) & np.isfinite(mn) & (mn > 0)
        sale_p = np.where(heavy, 0.5 * (mod + mn), mod)
        return sale_p * (1.0 - sp) * (1.0 - sale_fee_rate[idx]) - f_road[idx] - detention_per_day * d - local[idx]

    def _sell_price(idx: np.ndarray, sale_p: np.ndarray, d: int) -> np.ndarray:
        sp = _sp(idx, d)
        return sale_p * (1.0 - sp) * (1.0 - sale_fee_rate[idx]) - f_road[idx] - detention_per_day * d - local[idx]

    def _divert(idx: np.ndarray, d: int) -> np.ndarray:
        sp = _sp(idx, d)
        return -div * f_road[idx] - local[idx] * sp - detention_per_day * d

    out = np.empty(n, dtype=np.float64)
    otypes = np.empty(n, dtype=object)

    taken = np.zeros(n, dtype=bool)
    for d in (0, 1, 2):
        exact = (~taken) & np.isfinite(p_ex[d]) & (p_ex[d] > 0)
        if exact.any():
            out[exact] = _sell_exact(exact, d)
            otypes[exact] = "exact_d0" if d == 0 else f"exact_wait_d{d}"
            taken |= exact
        if d == 2:
            rest = ~taken
            if rest.any():
                amin2 = p_an[2]
                use_other = rest & np.isfinite(amin2) & (amin2 > 0)
                no_other = rest & ~use_other
                if use_other.any():
                    out[use_other] = _sell_price(use_other, amin2[use_other] * (1.0 - disc), 2)
                    otypes[use_other] = "other_var_distress_d2"
                if no_other.any():
                    out[no_other] = _divert(no_other, 2)
                    otypes[no_other] = "no_comm_divert_d2"
            break
        active_any = np.isfinite(p_an[d]) & (p_an[d] > 0)
        give_up = (~taken) & (~active_any)
        if give_up.any():
            out[give_up] = _divert(give_up, d)
            otypes[give_up] = f"no_comm_divert_d{d}"
            taken |= give_up

    if open_yard_mar:
        # Replace ONLY unobserved silent-yard (`no_comm_divert`) trips with open-yard MAR clearance at dest_lag_price
        div_mask = np.char.startswith(otypes.astype(str), "no_comm_divert")
        if div_mask.any():
            lag_p = df["dest_lag_price"].to_numpy(dtype=np.float64)[div_mask]
            out[div_mask] = _sell_price(div_mask, lag_p, 0)
            otypes[div_mask] = "open_yard_mar_silent"
    return out, otypes


def _evaluate_panel(
    panel_name: str,
    df_test: pd.DataFrame,
    y_arr: np.ndarray,
    ot_arr: np.ndarray,
    th_b2: float,
    m_mg_match: float,
    kappa_star: float,
    m_rr_match: float,
    m_safe_match: float,
) -> Tuple[List[dict], Dict[str, pd.DataFrame]]:
    """Score the core comparison policies on df_test with strictly weather-free <= t-1 features."""
    df_t = df_test.copy().reset_index(drop=True)
    df_t["_i"] = np.arange(len(df_t))
    df_t["y"] = y_arr
    age = df_t["dest_lag_age"].to_numpy(dtype=np.float64)
    age13 = (age >= 1) & (age <= 3)
    f = compute_decision_features(df_t)
    sc_rr = rr_abstain_score(df_t, kappa_star)
    sc_safe = score_safe_ev_sunk(df_t)
    sc_phys = score_safe_ev_phys(df_t)
    sc_rtmin = score_rt2f_min(df_t)

    specs = {
        "B1_lagged_screen": (f["lag_spread"], np.ones(len(df_t), dtype=bool)),
        "B2_age_matched": (f["net_road_fee"], age13 & (f["net_road_fee"] > th_b2)),
        "MG_matched": (f["net_road_fee_spoil"], age13 & (f["rep14"] >= 0.50) & (f["dow8"] >= 0.35) & (f["net_road_fee_spoil"] > m_mg_match)),
        "RR_Abstain_matched": (sc_rr, age13 & (sc_rr > m_rr_match)),
        "Safe_EV_Sunk_m0": (sc_safe, age13 & (sc_safe > 0.0)),
        "Safe_EV_Sunk_matched": (sc_safe, age13 & (sc_safe > m_safe_match)),
        "Safe_EV_Phys_m0": (sc_phys, age13 & (sc_phys > 0.0)),
        "RT_2F_Min_m0": (sc_rtmin, age13 & (sc_rtmin > 0.0)),
    }
    rows = []
    chosen_map: Dict[str, pd.DataFrame] = {}
    for pname, (sc, mask) in specs.items():
        ch = pick_episode(df_t, sc, mask, "y")
        rec = _extended_metrics(pname, ch, ot_arr)
        rec["panel"] = panel_name
        rows.append(rec)
        chosen_map[pname] = ch
    return rows, chosen_map


def _compute_breakeven_rows(
    panel_name: str,
    chosen_closed: Dict[str, pd.DataFrame],
    ot_closed: np.ndarray,
    chosen_open: Dict[str, pd.DataFrame],
) -> List[dict]:
    """Compute exact break-even silent-market thresholds where Mean(A - B) == 0.

    Reports three algebraically exact, numerically verified (< 1e-6) thresholds:
      1. `breakeven_silent_extra_inr`: extra INR/qtl above closed-yard turn-back on silent trips.
      2. `breakeven_silent_abs_payoff_inr`: constant realized net payoff (INR/qtl vs local) on silent trips.
      3. `breakeven_open_mar_share_pct`: exact mixture share theta* (0..100%) between closed-yard and open-MAR.
    """
    pairs = [
        ("Safe_EV_Sunk_m0", "B2_age_matched"),
        ("Safe_EV_Phys_m0", "B2_age_matched"),
        ("RT_2F_Min_m0", "B2_age_matched"),
        ("Safe_EV_Sunk_m0", "B1_lagged_screen"),
    ]
    out = []
    for pa, pb in pairs:
        ca, cb = chosen_closed[pa], chosen_closed[pb]
        ya = ca["y"].to_numpy(dtype=np.float64)
        yb = cb["y"].to_numpy(dtype=np.float64)
        ya_open = chosen_open[pa]["y"].to_numpy(dtype=np.float64)
        yb_open = chosen_open[pb]["y"].to_numpy(dtype=np.float64)
        elig_a = ca["eligible"].to_numpy(dtype=bool)
        elig_b = cb["eligible"].to_numpy(dtype=bool)
        ot_a = np.where(elig_a, ot_closed[ca["_i"].to_numpy()].astype(str), "abstain")
        ot_b = np.where(elig_b, ot_closed[cb["_i"].to_numpy()].astype(str), "abstain")
        div_a = np.char.startswith(ot_a, "no_comm_divert").astype(np.float64)
        div_b = np.char.startswith(ot_b, "no_comm_divert").astype(np.float64)

        mean_diff_closed = float((ya - yb).mean())
        mean_diff_open = float((ya_open - yb_open).mean())
        p_div_a = float(div_a.mean())
        p_div_b = float(div_b.mean())
        gap_div = p_div_b - p_div_a
        if gap_div > 1e-9:
            delta_be = mean_diff_closed / gap_div
            resid_extra = float(((ya + div_a * delta_be) - (yb + div_b * delta_be)).mean())
            assert abs(resid_extra) < 1e-6, f"Break-even extra residual check failed: {resid_extra}"

            # Constant absolute net payoff c (INR/qtl) replacing y_div on silent trips
            c_be = float((ya * (1.0 - div_a) - yb * (1.0 - div_b)).mean()) / gap_div
            resid_abs = float((np.where(div_a > 0.5, c_be, ya) - np.where(div_b > 0.5, c_be, yb)).mean())
            assert abs(resid_abs) < 1e-6, f"Break-even abs residual check failed: {resid_abs}"
            resid = max(abs(resid_extra), abs(resid_abs))
        else:
            delta_be = float("nan")
            c_be = float("nan")
            resid = float("nan")

        if (mean_diff_closed - mean_diff_open) > 1e-9:
            theta_be = mean_diff_closed / (mean_diff_closed - mean_diff_open)
            resid_theta = float((((1.0 - theta_be) * ya + theta_be * ya_open) - ((1.0 - theta_be) * yb + theta_be * yb_open)).mean())
            assert abs(resid_theta) < 1e-6, f"Break-even theta residual check failed: {resid_theta}"
            theta_pct = round(theta_be * 100.0, 2)
            resid = max(resid, abs(resid_theta)) if np.isfinite(resid) else abs(resid_theta)
        else:
            theta_pct = float("nan")

        out.append({
            "panel": panel_name,
            "policy_a": pa,
            "policy_b": pb,
            "mean_diff_closed": round(mean_diff_closed, 2),
            "mean_diff_open_mar": round(mean_diff_open, 2),
            "divert_share_a_pct": round(p_div_a * 100.0, 2),
            "divert_share_b_pct": round(p_div_b * 100.0, 2),
            "breakeven_silent_extra_inr": round(delta_be, 2),
            "breakeven_silent_abs_payoff_inr": round(c_be, 2),
            "breakeven_open_mar_share_pct": theta_pct,
            "verification_resid": round(abs(resid), 9),
        })
    return out


def _dest_or_origin_key(ch: pd.DataFrame) -> np.ndarray:
    st = ch["State"].astype(str).to_numpy()
    elig = ch["eligible"].to_numpy(dtype=bool)
    dm = ch["dest_market"].astype(str).to_numpy()
    orig = ch["origin_market_key"].astype(str).to_numpy()
    return np.where(elig, st + "|" + dm, orig)


def run() -> None:
    out_dir = ROOT / "revision" / "results"
    summary_base = json.loads((out_dir / "summary.json").read_text())
    summary_a10 = json.loads((out_dir / "a10_summary.json").read_text())
    summary_a18 = json.loads((out_dir / "a18_summary.json").read_text())

    th_b2 = float(summary_base["tuned_thresholds_on_val"]["B2_age_matched"])
    m_mg_match = float(summary_a18["val_matched_thresholds"]["MG_matched"])
    kappa_star = float(summary_a10["kappa_star_matched"])
    m_rr_match = float(summary_a10["m_star_matched"])
    m_safe_match = float(summary_a18["val_matched_thresholds"]["Safe_EV_Sunk_matched"])

    raw = pd.read_parquet(ROOT / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet")
    mkts_2024 = get_2024_only_markets(raw, min_days=80, max_per_state=30)
    assert len(mkts_2024) == 171, f"Expected 171 markets from 2024-only filter, got {len(mkts_2024)}"
    mkt_set_2024 = set(zip(mkts_2024["State"].astype(str), mkts_2024["Market"].astype(str)))

    coords = pd.read_parquet(ROOT / "data/processed/mandi_coordinates.parquet")
    wx = pd.read_parquet(ROOT / "data/processed/mandi_weather_2024_2026.parquet")

    df = pd.read_parquet(out_dir / "lagged_candidates.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df_test = df[df["date"] >= pd.Timestamp("2025-06-01")].copy().reset_index(drop=True)

    # Attach realized ERA5 weather strictly for settlement (zero weather in decisions)
    df_test_wx, wx_cov = attach_realized_era5_settlement_weather(df_test, coords, wx)

    # 1. Full 178-market panel (N = 58,676): 20C ref (closed & open-MAR), Realized ERA5 (closed & open-MAR)
    y_20c, ot_20c = settle_candidates(df_test, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    div_20c = np.char.startswith(ot_20c.astype(str), "no_comm_divert")
    same_20c = df_test["same_district"].to_numpy(dtype=bool)
    sale_fee_20c = np.where(same_20c, 0.0, df_test["fee_rate"].to_numpy(dtype=np.float64))
    y_mar_20c_cand = (
        df_test["dest_lag_price"].to_numpy(dtype=np.float64)
        * (1.0 - df_test["spoil_ref_0"].to_numpy(dtype=np.float64))
        * (1.0 - sale_fee_20c)
        - df_test["freight_road"].to_numpy(dtype=np.float64)
        - df_test["settle_local_price_d0"].to_numpy(dtype=np.float64)
    )
    y_20c_open = np.where(div_20c, y_mar_20c_cand, y_20c)
    ot_20c_open = np.where(div_20c, "open_yard_mar_silent", ot_20c.astype(str))
    y_era5, ot_era5 = settle_realized_era5_sequential(df_test_wx, div=1.5, disc=0.10, open_yard_mar=False)
    y_era5_open, ot_era5_open = settle_realized_era5_sequential(df_test_wx, div=1.5, disc=0.10, open_yard_mar=True)

    all_rows: List[dict] = []
    r_178_20c, ch_178_20c = _evaluate_panel("full_178_20C_closed", df_test, y_20c, ot_20c, th_b2, m_mg_match, kappa_star, m_rr_match, m_safe_match)
    _, ch_178_20c_open = _evaluate_panel("full_178_20C_open_MAR", df_test, y_20c_open, ot_20c_open, th_b2, m_mg_match, kappa_star, m_rr_match, m_safe_match)
    r_178_era5, ch_178_era5 = _evaluate_panel("full_178_ERA5_closed", df_test_wx, y_era5, ot_era5, th_b2, m_mg_match, kappa_star, m_rr_match, m_safe_match)
    r_178_open, ch_178_open = _evaluate_panel("full_178_ERA5_open_MAR", df_test_wx, y_era5_open, ot_era5_open, th_b2, m_mg_match, kappa_star, m_rr_match, m_safe_match)
    all_rows.extend(r_178_20c + r_178_era5 + r_178_open)

    # 2. Strict 2024-only 171-market zero-lookahead panel REBUILT FROM SCRATCH on raw_171 (zero post-2024 shortlist truncation!)
    cor = pd.read_parquet(ROOT / "data/processed/osrm_corridor_matrix.parquet")
    fees = pd.read_csv(ROOT / "data/processed/state_apmc_and_loss_parameters.csv")
    raw_171_mask = [
        (st, mk) in mkt_set_2024
        for st, mk in zip(raw["State"].astype(str), raw["Market"].astype(str))
    ]
    raw_171 = raw.loc[raw_171_mask].copy().reset_index(drop=True)
    df_171_all, counts_171 = build_lagged_candidates_from_frames(
        raw_df=raw_171,
        corridors_df=cor,
        fee_params_df=fees,
        clim_df=None,
        grade_explicit=False,
    )
    df_171_all["date"] = pd.to_datetime(df_171_all["date"])
    df_val_171 = df_171_all[df_171_all["date"] <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    df_171 = df_171_all[df_171_all["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)

    # Re-calibrate B2 and matched comparators strictly on val_171 using the exact eval_run.py protocol
    df_val_171["y"] = settle_candidates(df_val_171, how="sequential", weather="none", div=1.5, disc=0.10)
    fv171 = compute_decision_features(df_val_171)
    age_v171 = (fv171["age"] >= 1) & (fv171["age"] <= 3)
    th_b2_171, val171_b2_summ = tune_threshold_on_val(
        df_val_171,
        fv171,
        "net_road_fee",
        lambda ft: (ft["age"] >= 1) & (ft["age"] <= 3),
    )
    target_disp_171 = float(val171_b2_summ["dispatch_rate"])
    m_mg_171 = find_val_matched_threshold(
        df_val_171,
        fv171["net_road_fee_spoil"],
        age_v171 & (fv171["rep14"] >= 0.50) & (fv171["dow8"] >= 0.35),
        target_disp_171,
    )
    m_rr_171 = find_val_matched_threshold(df_val_171, rr_abstain_score(df_val_171, kappa_star), age_v171, target_disp_171)
    m_safe_171 = find_val_matched_threshold(df_val_171, score_safe_ev_sunk(df_val_171), age_v171, target_disp_171)

    df_171_wx, wx_cov_171 = attach_realized_era5_settlement_weather(df_171, coords, wx)
    y_171_20c, ot_171_20c = settle_candidates(df_171, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    div_171_20c = np.char.startswith(ot_171_20c.astype(str), "no_comm_divert")
    same_171 = df_171["same_district"].to_numpy(dtype=bool)
    sale_fee_171 = np.where(same_171, 0.0, df_171["fee_rate"].to_numpy(dtype=np.float64))
    y_171_20c_mar_cand = (
        df_171["dest_lag_price"].to_numpy(dtype=np.float64)
        * (1.0 - df_171["spoil_ref_0"].to_numpy(dtype=np.float64))
        * (1.0 - sale_fee_171)
        - df_171["freight_road"].to_numpy(dtype=np.float64)
        - df_171["settle_local_price_d0"].to_numpy(dtype=np.float64)
    )
    y_171_20c_open = np.where(div_171_20c, y_171_20c_mar_cand, y_171_20c)
    ot_171_20c_open = np.where(div_171_20c, "open_yard_mar_silent", ot_171_20c.astype(str))
    y_171_era5, ot_171_era5 = settle_realized_era5_sequential(df_171_wx, div=1.5, disc=0.10, open_yard_mar=False)
    y_171_open, ot_171_open = settle_realized_era5_sequential(df_171_wx, div=1.5, disc=0.10, open_yard_mar=True)

    r_171_20c, ch_171_20c = _evaluate_panel("strict2024_171_20C_closed", df_171, y_171_20c, ot_171_20c, th_b2_171, m_mg_171, kappa_star, m_rr_171, m_safe_171)
    _, ch_171_20c_open = _evaluate_panel("strict2024_171_20C_open_MAR", df_171, y_171_20c_open, ot_171_20c_open, th_b2_171, m_mg_171, kappa_star, m_rr_171, m_safe_171)
    r_171_era5, ch_171_era5 = _evaluate_panel("strict2024_171_ERA5_closed", df_171_wx, y_171_era5, ot_171_era5, th_b2_171, m_mg_171, kappa_star, m_rr_171, m_safe_171)
    r_171_open, ch_171_open = _evaluate_panel("strict2024_171_ERA5_open_MAR", df_171_wx, y_171_open, ot_171_open, th_b2_171, m_mg_171, kappa_star, m_rr_171, m_safe_171)
    all_rows.extend(r_171_20c + r_171_era5 + r_171_open)

    upgrades_df = pd.DataFrame(all_rows)
    upgrades_df.to_csv(out_dir / "v6_upgrades.csv", index=False)

    # 3. Exact Break-Even Silent-Market Values across ALL FOUR closed-yard panels (16 rows)
    be_rows = (
        _compute_breakeven_rows("full_178_20C_closed", ch_178_20c, ot_20c, ch_178_20c_open)
        + _compute_breakeven_rows("full_178_ERA5_closed", ch_178_era5, ot_era5, ch_178_open)
        + _compute_breakeven_rows("strict2024_171_20C_closed", ch_171_20c, ot_171_20c, ch_171_20c_open)
        + _compute_breakeven_rows("strict2024_171_ERA5_closed", ch_171_era5, ot_171_era5, ch_171_open)
    )
    be_df = pd.DataFrame(be_rows)
    be_df.to_csv(out_dir / "v6_breakeven.csv", index=False)

    # 4. R = 5,000 paired cluster bootstraps across all 3 clusterings + 1w/4w block sensitivity + 171-mkt + ERA5
    boot_rows: List[dict] = []

    def _run_boot_family(
        family_label: str,
        ch_map: Dict[str, pd.DataFrame],
        schemes: List[Tuple[str, str, int]],
        contrasts: List[Tuple[str, str, str, str]],
        reps: int = 5000,
    ) -> None:
        base_ch = ch_map["B2_age_matched"]
        panel_df = pd.DataFrame({
            "episode_id": base_ch["episode_id"].to_numpy(),
            "date": base_ch["date"].to_numpy(),
            "origin_market_key": base_ch["origin_market_key"].to_numpy(),
            "b2dest_or_origin_key": _dest_or_origin_key(base_ch),
        })
        for pname, ch in ch_map.items():
            panel_df[pname] = ch["y"].to_numpy(dtype=np.float64)
            panel_df[f"{pname}_dest_key"] = _dest_or_origin_key(ch)

        for scheme_name, mcol_kind, wk_len in schemes:
            fam_raw: List[dict] = []
            pair_cache: Dict[Tuple[str, str, str, int], dict] = {}
            for hid, pa, pb, metric in contrasts:
                mcol = f"{pa}_dest_key" if mcol_kind == "policy_dest" else mcol_kind
                ckey = (pa, pb, mcol, wk_len)
                if ckey not in pair_cache:
                    pair_cache[ckey] = two_way_cluster_bootstrap_all_metrics(
                        panel_df, pa, pb, mandi_col=mcol, date_col="date", week_block_len=wk_len, reps=reps, seed=20261117
                    )
                res = pair_cache[ckey]
                r_m = res[metric]
                fam_raw.append({
                    "family": family_label,
                    "scheme": scheme_name,
                    "week_block_len": wk_len,
                    "reps": reps,
                    "hypothesis_id": hid,
                    "policy_a": pa,
                    "policy_b": pb,
                    "metric": metric,
                    "estimate": round(r_m["estimate"], 4),
                    "ci95_low": round(r_m["ci95_low"], 4),
                    "ci95_high": round(r_m["ci95_high"], 4),
                    "p_value_two_sided": round(r_m["p_value_two_sided"], 6),
                    "n": int(r_m["n"]),
                    "n_clusters": int(r_m["n_clusters"]),
                    "n_blocks": int(r_m["n_blocks"]),
                })
            # Two-sided Holm across the family
            p_adj = holm_bonferroni([r["p_value_two_sided"] for r in fam_raw])
            for rec, pa_val in zip(fam_raw, p_adj):
                rec["p_holm_2s"] = round(float(pa_val), 6)
                boot_rows.append(rec)

    primary_contrasts = [
        ("H_V6_1", "Safe_EV_Sunk_m0", "B2_age_matched", "es10"),
        ("H_V6_2", "Safe_EV_Phys_m0", "B2_age_matched", "es10"),
        ("H_V6_3", "Safe_EV_Sunk_m0", "B2_age_matched", "ep_loss_rate"),
        ("H_V6_4", "Safe_EV_Sunk_matched", "RR_Abstain_matched", "es10"),
        ("H_V6_5", "RT_2F_Min_m0", "B2_age_matched", "mean"),
        ("H_V6_6", "Safe_EV_Sunk_m0", "B2_age_matched", "mean"),
    ]
    _run_boot_family(
        "full_178_20C_closed",
        ch_178_20c,
        [
            ("origin_x_2week", "origin_market_key", 2),
            ("b2dest_or_origin_x_2week", "b2dest_or_origin_key", 2),
            ("policy_dest_or_origin_x_2week", "policy_dest", 2),
            ("origin_x_1week", "origin_market_key", 1),
            ("origin_x_4week", "origin_market_key", 4),
        ],
        primary_contrasts,
        reps=5000,
    )
    _run_boot_family(
        "full_178_ERA5_closed",
        ch_178_era5,
        [
            ("origin_x_2week", "origin_market_key", 2),
            ("b2dest_or_origin_x_2week", "b2dest_or_origin_key", 2),
        ],
        primary_contrasts,
        reps=5000,
    )
    _run_boot_family(
        "strict2024_171_ERA5_closed",
        ch_171_era5,
        [
            ("origin_x_2week", "origin_market_key", 2),
            ("b2dest_or_origin_x_2week", "b2dest_or_origin_key", 2),
        ],
        primary_contrasts,
        reps=5000,
    )
    _run_boot_family(
        "strict2024_171_20C_closed",
        ch_171_20c,
        [
            ("origin_x_2week", "origin_market_key", 2),
            ("b2dest_or_origin_x_2week", "b2dest_or_origin_key", 2),
        ],
        primary_contrasts,
        reps=5000,
    )

    boot_df = pd.DataFrame(boot_rows)
    boot_df.to_csv(out_dir / "v6_bootstrap_5000.csv", index=False)

    summary_v6 = {
        "exploratory": True,
        "strict_2024_markets_count": int(len(mkts_2024)),
        "strict_2024_markets_by_state": {str(k): int(v) for k, v in mkts_2024.groupby("State").size().items()},
        "strict_2024_fresh_rebuild": True,
        "strict_2024_shortlist_test_rows": int(len(df_171)),
        "n_test_full_178": int(ch_178_20c["B2_age_matched"].shape[0]),
        "n_test_strict2024_171": int(ch_171_20c["B2_age_matched"].shape[0]),
        "val_171_b2_threshold": float(th_b2_171),
        "val_171_b2_dispatch_rate": round(target_disp_171, 4),
        "val_171_matched_thresholds": {
            "MG_matched": round(float(m_mg_171), 4),
            "RR_Abstain_matched": round(float(m_rr_171), 4),
            "Safe_EV_Sunk_matched": round(float(m_safe_171), 4),
        },
        "era5_settlement_coverage": wx_cov,
        "era5_settlement_coverage_171": wx_cov_171,
        "bootstrap_reps": 5000,
        "p_min_two_sided_5000": round(2.0 / 5001.0, 6),
        "p_holm_min_6tests_5000": round(6.0 * (2.0 / 5001.0), 6),
    }
    (out_dir / "v6_summary.json").write_text(json.dumps(summary_v6, indent=2))
    print("=== V6 SUMMARY ===")
    print(json.dumps(summary_v6, indent=2))
    print("\n=== V6 UPGRADES (Selected Panels) ===")
    print(upgrades_df[["panel", "policy", "n", "dispatch_rate", "mean", "ep_loss_rate", "es10"]].to_string(index=False))
    print("\n=== V6 BREAK-EVEN SILENT MARKET VALUES ===")
    print(be_df.to_string(index=False))


if __name__ == "__main__":
    run()
