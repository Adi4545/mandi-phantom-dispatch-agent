"""Evaluate locked exploratory zero-hyperparameter rules (PREREG_A18.md) & full A17 audits.

STRICT R5 ORDER: This file was created and executed strictly AFTER committing `final/PREREG_A18.md` (commit 4cbb02d).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

from revision.build_variant import SimParams, build_lagged_candidates_from_frames, spoil_frac_ref
from revision.es10 import es10
from revision.eval_a10 import rr_abstain_score
from revision.eval_run import (
    ci95_single_metric,
    compute_decision_features,
    find_val_matched_threshold,
    pick_episode,
    settle_candidates,
    summarize_chosen,
)
from revision.stats_utils import two_way_cluster_bootstrap_all_metrics
from src.evaluation.bootstrap import holm_bonferroni

ROOT = Path(__file__).resolve().parents[1]


# Zero-hyperparameter A18 scorers (strictly <= t-1 features, age 1..3 gate applied at selection)
def score_safe_ev_sunk(df: pd.DataFrame) -> np.ndarray:
    """Method 1 (0 tuned params): p_dow * G_1sd - F > 0."""
    p_dow = df["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64)
    p_dest_safe = df["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - df["dest_price_cv_28d"].to_numpy(dtype=np.float64))
    g_safe = p_dest_safe * (1.0 - df["fee_rate"].to_numpy(dtype=np.float64)) - df["origin_lag_price"].to_numpy(dtype=np.float64)
    return p_dow * g_safe - df["freight_road"].to_numpy(dtype=np.float64)


def score_safe_ev_phys(df: pd.DataFrame) -> np.ndarray:
    """Method 3 (0 tuned params, exact physical div=1.5): p_dow*(G_1sd - F) - (1-p_dow)*1.5*F > 0."""
    p_dow = df["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64)
    f = df["freight_road"].to_numpy(dtype=np.float64)
    p_dest_safe = df["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - df["dest_price_cv_28d"].to_numpy(dtype=np.float64))
    g_safe = p_dest_safe * (1.0 - df["fee_rate"].to_numpy(dtype=np.float64)) - df["origin_lag_price"].to_numpy(dtype=np.float64)
    return p_dow * (g_safe - f) - (1.0 - p_dow) * 1.5 * f


def score_rt2f_dow(df: pd.DataFrame) -> np.ndarray:
    """Method 2a (Class-8 phone calculator, NO cv28, NO spoil): p_dow * G - 2*F > 0."""
    p_dow = df["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64)
    g = df["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - df["fee_rate"].to_numpy(dtype=np.float64)) - df["origin_lag_price"].to_numpy(dtype=np.float64)
    return p_dow * g - 2.0 * df["freight_road"].to_numpy(dtype=np.float64)


def score_rt2f_min(df: pd.DataFrame) -> np.ndarray:
    """Method 2b (Class-8 keypad calculator, NO cv28, NO spoil): min(rep28, dow8) * G - 2*F > 0."""
    p_min = np.minimum(
        df["dest_exact_rep_28d"].to_numpy(dtype=np.float64),
        df["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64),
    )
    g = df["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - df["fee_rate"].to_numpy(dtype=np.float64)) - df["origin_lag_price"].to_numpy(dtype=np.float64)
    return p_min * g - 2.0 * df["freight_road"].to_numpy(dtype=np.float64)


def score_ev_rt_min(df: pd.DataFrame) -> np.ndarray:
    """Method 4 (Exact 2-state round-trip EV, NO cv28): p_min * G - (2 - p_min)*F > 0."""
    p_min = np.minimum(
        df["dest_exact_rep_28d"].to_numpy(dtype=np.float64),
        df["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64),
    )
    g = df["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - df["fee_rate"].to_numpy(dtype=np.float64)) - df["origin_lag_price"].to_numpy(dtype=np.float64)
    return p_min * g - (2.0 - p_min) * df["freight_road"].to_numpy(dtype=np.float64)


def _extended_metrics(name: str, ch: pd.DataFrame, otypes_all: np.ndarray, y_override: np.ndarray | None = None) -> dict:
    rec = summarize_chosen(name, ch, y_override=y_override)
    elig = ch["eligible"].to_numpy(dtype=bool)
    km_arr = ch["road_km"].to_numpy(dtype=np.float64)[elig]
    rec["mean_road_km"] = round(float(km_arr.mean()), 2) if len(km_arr) else 0.0
    if int(elig.sum()) > 0:
        ots = otypes_all[ch["_i"].to_numpy()[elig]].astype(str)
        rec["divert_rate_among_disp"] = round(float(np.char.startswith(ots, "no_comm_divert").mean()), 4)
    else:
        rec["divert_rate_among_disp"] = 0.0
    return rec


def _score_frame_for_policy(df: pd.DataFrame, age: np.ndarray, th_b2: float, m_mg_match: float, kappa_star: float, m_rr_match: float, m_safe_match: float, m_phys_match: float, m_rt_match: float, feats: dict | None = None) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    f = compute_decision_features(df) if feats is None else feats
    age13 = (age >= 1) & (age <= 3)
    sc_rr = rr_abstain_score(df, kappa_star)
    sc_rr15 = rr_abstain_score(df, 1.5)
    sc_safe = score_safe_ev_sunk(df)
    sc_phys = score_safe_ev_phys(df)
    sc_rtmin = score_rt2f_min(df)
    sc_rtdow = score_rt2f_dow(df)
    sc_evrt = score_ev_rt_min(df)
    return {
        "B1_lagged_screen": (f["lag_spread"], np.ones(len(df), dtype=bool)),
        "B2_age_matched": (f["net_road_fee"], age13 & (f["net_road_fee"] > th_b2)),
        "MG_matched": (f["net_road_fee_spoil"], age13 & (f["rep14"] >= 0.50) & (f["dow8"] >= 0.35) & (f["net_road_fee_spoil"] > m_mg_match)),
        "RR_Abstain_matched": (sc_rr, age13 & (sc_rr > m_rr_match)),
        "RR_Abstain_m0": (sc_rr, age13 & (sc_rr > 0.0)),
        "RR_Abstain_phys15_m0": (sc_rr15, age13 & (sc_rr15 > 0.0)),
        "Safe_EV_Sunk_m0": (sc_safe, age13 & (sc_safe > 0.0)),
        "Safe_EV_Sunk_matched": (sc_safe, age13 & (sc_safe > m_safe_match)),
        "Safe_EV_Phys_m0": (sc_phys, age13 & (sc_phys > 0.0)),
        "Safe_EV_Phys_matched": (sc_phys, age13 & (sc_phys > m_phys_match)),
        "RT_2F_Min_m0": (sc_rtmin, age13 & (sc_rtmin > 0.0)),
        "RT_2F_Min_matched": (sc_rtmin, age13 & (sc_rtmin > m_rt_match)),
        "RT_2F_Dow_m0": (sc_rtdow, age13 & (sc_rtdow > 0.0)),
        "EV_RT_Min_m0": (sc_evrt, age13 & (sc_evrt > 0.0)),
    }


def _recompute_scenario_decision_df(df: pd.DataFrame, kw: dict) -> pd.DataFrame:
    """Adjust decision-time freight, effective fee, and reference spoilage for re-scored tornado checks."""
    out = df.copy()
    fb = float(kw.get("freight_base", 35.0))
    fpk = float(kw.get("freight_per_km", 0.45))
    hpm = float(kw.get("hp_km_mult", 1.45))
    fee_mult = float(kw.get("fee_mult", 1.0))
    arhtiya = float(kw.get("arhtiya_rate", 0.0))
    sp_mult = float(kw.get("spoil_mult", 1.0))

    hp = np.where(out["State"].to_numpy() == "Himachal Pradesh", hpm, 1.0)
    out["freight_road"] = fb + fpk * hp * out["road_km"].to_numpy(dtype=np.float64)
    same = out["same_district"].to_numpy(dtype=bool)
    stat_r = np.where(same, 0.0, fee_mult * out["fee_rate"].to_numpy(dtype=np.float64))
    out["fee_rate"] = np.clip(stat_r + arhtiya, 0.0, 0.30)
    out["spoil_ref_0"] = np.clip(sp_mult * out["spoil_ref_0"].to_numpy(dtype=np.float64), 0.0, 0.55)
    return out


def _unconditional_origin_panel(root: Path, cor: pd.DataFrame, fees: pd.DataFrame, clim: pd.DataFrame | None) -> Tuple[pd.DataFrame, dict]:
    raw = pd.read_parquet(root / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet")
    # Build ONLY on test window with history starting 2024-01-01
    return build_lagged_candidates_from_frames(
        raw_df=raw,
        corridors_df=cor,
        fee_params_df=fees,
        clim_df=clim,
        grade_explicit=False,
        min_origin_date="2025-06-01",
        max_origin_date="2026-04-08",
        include_unreported_origin_days=True,
    )


def run() -> None:
    out_dir = ROOT / "revision" / "results"
    summary_base = json.loads((out_dir / "summary.json").read_text())
    summary_a10 = json.loads((out_dir / "a10_summary.json").read_text())
    th_base = summary_base["tuned_thresholds_on_val"]
    target_val_disp = float(summary_base["val_summaries"]["B2_age_matched"]["dispatch_rate"])
    kappa_star = float(summary_a10["kappa_star_matched"])
    m_rr_match = float(summary_a10["m_star_matched"])

    df = pd.read_parquet(out_dir / "lagged_candidates.parquet")
    df["date"] = pd.to_datetime(df["date"])
    y_seq, ot_seq = settle_candidates(df, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    df["y"] = y_seq
    df["_ot"] = ot_seq

    val = df[df["date"] <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    test = df[df["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    test_ot = test["_ot"].to_numpy()
    vf = compute_decision_features(val)
    tf = compute_decision_features(test)
    age_val = vf["age"]
    age_val13 = (age_val >= 1) & (age_val <= 3)
    age_test = tf["age"]
    age_test13 = (age_test >= 1) & (age_test <= 3)

    # Calibrate val-matched cutoffs for comparative 70.71%-matched benchmarks
    m_act_match = find_val_matched_threshold(val, vf["net_road_fee"], age_val13 & (vf["rep14"] >= 0.50), target_val_disp)
    m_mg_match = find_val_matched_threshold(val, vf["net_road_fee_spoil"], age_val13 & (vf["rep14"] >= 0.50) & (vf["dow8"] >= 0.35), target_val_disp)
    m_rr15_match = find_val_matched_threshold(val, rr_abstain_score(val, 1.5), age_val13, target_val_disp)
    m_safe_match = find_val_matched_threshold(val, score_safe_ev_sunk(val), age_val13, target_val_disp)
    m_phys_match = find_val_matched_threshold(val, score_safe_ev_phys(val), age_val13, target_val_disp)
    m_rtmin_match = find_val_matched_threshold(val, score_rt2f_min(val), age_val13, target_val_disp)

    # 1. Head-to-head a18_results.csv on test (N = 58,676)
    sc_map = _score_frame_for_policy(
        test, age_test, float(th_base["B2_age_matched"]), m_mg_match, kappa_star, m_rr_match,
        m_safe_match, m_phys_match, m_rtmin_match, feats=tf,
    )
    sc_map["B_simple_activity_matched"] = (tf["net_road_fee"], age_test13 & (tf["rep14"] >= 0.50) & (tf["net_road_fee"] > m_act_match))
    sc_map["RR_Abstain_phys15_matched"] = (rr_abstain_score(test, 1.5), age_test13 & (rr_abstain_score(test, 1.5) > m_rr15_match))

    meta_tags = {
        "B1_lagged_screen": (1, 100.0),
        "B2_age_matched": (1, float(th_base["B2_age_matched"])),
        "B_simple_activity_matched": (2, round(m_act_match, 2)),
        "MG_matched": (4, round(m_mg_match, 2)),
        "RR_Abstain_matched": (2, round(m_rr_match, 2)),
        "RR_Abstain_m0": (1, 0.0),
        "RR_Abstain_phys15_m0": (0, 0.0),
        "RR_Abstain_phys15_matched": (1, round(m_rr15_match, 2)),
        "Safe_EV_Sunk_m0": (0, 0.0),
        "Safe_EV_Sunk_matched": (1, round(m_safe_match, 2)),
        "Safe_EV_Phys_m0": (0, 0.0),
        "Safe_EV_Phys_matched": (1, round(m_phys_match, 2)),
        "RT_2F_Min_m0": (0, 0.0),
        "RT_2F_Min_matched": (1, round(m_rtmin_match, 2)),
        "RT_2F_Dow_m0": (0, 0.0),
        "EV_RT_Min_m0": (0, 0.0),
    }

    chosen_pols: Dict[str, pd.DataFrame] = {}
    res_rows = []
    for pname in meta_tags:
        sc_a, el_a = sc_map[pname]
        ch = pick_episode(test, sc_a, el_a)
        chosen_pols[pname] = ch
        rec = _extended_metrics(pname, ch, test_ot)
        rec["free_params"] = meta_tags[pname][0]
        rec["calibrated_threshold"] = meta_tags[pname][1]
        res_rows.append(rec)
    pd.DataFrame(res_rows).to_csv(out_dir / "a18_results.csv", index=False)

    # 2. Cluster bootstrap across ALL 3 schemes with two-sided Holm (H_A18_1..4 + secondaries)
    bdf = chosen_pols["B1_lagged_screen"][["episode_id", "date", "origin_market_key", "State", "Commodity"]].copy()
    for pname, ch in chosen_pols.items():
        bdf[pname] = ch["y"].to_numpy(dtype=np.float64)
        bdf[f"{pname}_disp"] = ch["eligible"].to_numpy(dtype=bool)
        bdf[f"{pname}_dest"] = ch["dest_market"].to_numpy()
    bdf["b2_dest_key"] = np.where(
        bdf["B2_age_matched_disp"],
        bdf["State"].astype(str) + "|" + bdf["B2_age_matched_dest"].astype(str),
        bdf["origin_market_key"],
    )
    bdf["safe_dest_key"] = np.where(
        bdf["Safe_EV_Sunk_m0_disp"],
        bdf["State"].astype(str) + "|" + bdf["Safe_EV_Sunk_m0_dest"].astype(str),
        bdf["origin_market_key"],
    )
    bdf["safe_m_dest_key"] = np.where(
        bdf["Safe_EV_Sunk_matched_disp"],
        bdf["State"].astype(str) + "|" + bdf["Safe_EV_Sunk_matched_dest"].astype(str),
        bdf["origin_market_key"],
    )
    bdf["rt_dest_key"] = np.where(
        bdf["RT_2F_Min_m0_disp"],
        bdf["State"].astype(str) + "|" + bdf["RT_2F_Min_m0_dest"].astype(str),
        bdf["origin_market_key"],
    )

    contrast_specs = [
        ("Safe_EV_Sunk_m0_vs_B2", "Safe_EV_Sunk_m0", "B2_age_matched", "safe_dest_key"),
        ("Safe_EV_Sunk_matched_vs_RR", "Safe_EV_Sunk_matched", "RR_Abstain_matched", "safe_m_dest_key"),
        ("RT_2F_Min_m0_vs_B2", "RT_2F_Min_m0", "B2_age_matched", "rt_dest_key"),
        ("Safe_EV_Sunk_m0_vs_MG_matched", "Safe_EV_Sunk_m0", "MG_matched", "safe_dest_key"),
        ("Safe_EV_Sunk_m0_vs_RR", "Safe_EV_Sunk_m0", "RR_Abstain_matched", "safe_dest_key"),
        ("Safe_EV_Phys_matched_vs_RR", "Safe_EV_Phys_matched", "RR_Abstain_matched", "safe_m_dest_key"),
        ("RT_2F_Min_m0_vs_RR", "RT_2F_Min_m0", "RR_Abstain_matched", "rt_dest_key"),
        ("RT_2F_Dow_m0_vs_B2", "RT_2F_Dow_m0", "B2_age_matched", "rt_dest_key"),
        ("Safe_EV_Sunk_matched_vs_B2", "Safe_EV_Sunk_matched", "B2_age_matched", "safe_m_dest_key"),
    ]
    prereg_h = {
        ("Safe_EV_Sunk_m0_vs_B2", "es10"): "H_A18_1",
        ("Safe_EV_Sunk_matched_vs_RR", "es10"): "H_A18_2",
        ("Safe_EV_Sunk_m0_vs_B2", "ep_loss_rate"): "H_A18_3",
        ("RT_2F_Min_m0_vs_B2", "mean"): "H_A18_4",
    }

    boot_rows = []
    for cname, ca, cb, pol_mcol in contrast_specs:
        for sch_lbl, mcol in (
            ("origin_x_2week", "origin_market_key"),
            ("b2dest_or_origin_x_2week", "b2_dest_key"),
            ("policy_dest_or_origin_x_2week", pol_mcol),
        ):
            res = two_way_cluster_bootstrap_all_metrics(bdf, ca, cb, mandi_col=mcol, reps=2000, seed=20261117)
            for metric, md in res.items():
                p_dir = md["p_value_less"] if metric == "ep_loss_rate" else md["p_value_greater"]
                boot_rows.append({
                    "hypothesis_id": prereg_h.get((cname, metric), ""),
                    "contrast": cname,
                    "cluster": sch_lbl,
                    "metric": metric,
                    "estimate": round(md["estimate"], 4),
                    "ci95_low": round(md["ci95_low"], 4),
                    "ci95_high": round(md["ci95_high"], 4),
                    "p_value": p_dir,
                    "p_value_two_sided": md["p_value_two_sided"],
                    "n": md["n"],
                    "n_clusters": md["n_clusters"],
                    "n_blocks": md["n_blocks"],
                })
    boot_df = pd.DataFrame(boot_rows)
    boot_df["p_holm_1s"] = np.nan
    boot_df["p_holm_2s"] = np.nan
    for sch_lbl in ("origin_x_2week", "b2dest_or_origin_x_2week", "policy_dest_or_origin_x_2week"):
        m = (boot_df["cluster"] == sch_lbl) & (boot_df["hypothesis_id"] != "")
        boot_df.loc[m, "p_holm_1s"] = holm_bonferroni(boot_df.loc[m, "p_value"].tolist())
        boot_df.loc[m, "p_holm_2s"] = holm_bonferroni(boot_df.loc[m, "p_value_two_sided"].tolist())
    boot_df["p_holm"] = boot_df["p_holm_2s"]
    boot_df.to_csv(out_dir / "a18_bootstrap.csv", index=False)

    # 3. Fair feature, tuning-budget & test-matched ablations (A17 #6)
    # 3a) val-ES10-tuned hard-gate MG
    best_mg_es10 = None
    for rcut in (0.30, 0.40, 0.50, 0.60, 0.70, 0.75):
        for dcut in (0.20, 0.35, 0.50):
            gv = age_val13 & (vf["rep28"] >= rcut) & (vf["dow8"] >= dcut)
            if gv.mean() < 0.25:
                continue
            thm = find_val_matched_threshold(val, vf["net_road_fee_spoil"], gv, target_val_disp)
            rec_v = summarize_chosen("mg_grid", pick_episode(val, vf["net_road_fee_spoil"], gv & (vf["net_road_fee_spoil"] > thm)))
            key = (rec_v["es10"], rec_v["mean"])
            if best_mg_es10 is None or key > best_mg_es10[0]:
                best_mg_es10 = (key, rcut, dcut, thm)
    _, rcut_b, dcut_b, th_mg_es10 = best_mg_es10
    ch_mg_es10 = pick_episode(test, tf["net_road_fee_spoil"], age_test13 & (tf["rep28"] >= rcut_b) & (tf["dow8"] >= dcut_b) & (tf["net_road_fee_spoil"] > th_mg_es10))

    # 3b) RR using rep14 only
    def _rr_rep14(dframe: pd.DataFrame, k: float) -> np.ndarray:
        p = np.clip(dframe["dest_exact_rep_14d"].to_numpy(dtype=np.float64), 0.0, 1.0)
        d_op = dframe["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - dframe["spoil_ref_0"].to_numpy(dtype=np.float64)) * (1.0 - dframe["fee_rate"].to_numpy(dtype=np.float64)) - dframe["origin_lag_price"].to_numpy(dtype=np.float64) - dframe["freight_road"].to_numpy(dtype=np.float64)
        d_ms = -float(k) * dframe["freight_road"].to_numpy(dtype=np.float64) - dframe["origin_lag_price"].to_numpy(dtype=np.float64) * dframe["spoil_ref_0"].to_numpy(dtype=np.float64)
        return p * d_op + (1.0 - p) * d_ms

    th_rr14 = find_val_matched_threshold(val, _rr_rep14(val, kappa_star), age_val13, target_val_disp)
    ch_rr14 = pick_episode(test, _rr_rep14(test, kappa_star), age_test13 & (_rr_rep14(test, kappa_star) > th_rr14))

    # 3c) Pure distance-penalty without p_rep (d_open - 3*F_road), matched on val
    sc_dist_v = vf["net_road_fee_spoil"] - 3.0 * val["freight_road"].to_numpy(dtype=np.float64)
    th_dist = find_val_matched_threshold(val, sc_dist_v, age_val13, target_val_disp)
    sc_dist_t = tf["net_road_fee_spoil"] - 3.0 * test["freight_road"].to_numpy(dtype=np.float64)
    ch_dist = pick_episode(test, sc_dist_t, age_test13 & (sc_dist_t > th_dist))

    # 3d) Safe_EV fixed 10% haircut vs adaptive (1 - cv28)
    def _safe_fixed(dframe: pd.DataFrame, drop_pct: float = 0.10) -> np.ndarray:
        p = dframe["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64)
        g_s = dframe["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - drop_pct) * (1.0 - dframe["fee_rate"].to_numpy(dtype=np.float64)) - dframe["origin_lag_price"].to_numpy(dtype=np.float64)
        return p * g_s - dframe["freight_road"].to_numpy(dtype=np.float64)

    ch_fix10_m0 = pick_episode(test, _safe_fixed(test), age_test13 & (_safe_fixed(test) > 0.0))
    th_fix10_m = find_val_matched_threshold(val, _safe_fixed(val), age_val13, target_val_disp)
    ch_fix10_mat = pick_episode(test, _safe_fixed(test), age_test13 & (_safe_fixed(test) > th_fix10_m))

    # 3e) Euclid*1.20 and 2024 clim sensitivity on Safe_EV_Sunk_m0 & RR_Abstain_matched
    df_euc = test.copy()
    df_euc["freight_road"] = df_euc["freight_euclid"]
    ch_safe_euc = pick_episode(df_euc, score_safe_ev_sunk(df_euc), age_test13 & (score_safe_ev_sunk(df_euc) > 0.0))
    ch_rr_euc = pick_episode(df_euc, rr_abstain_score(df_euc, kappa_star), age_test13 & (rr_abstain_score(df_euc, kappa_star) > m_rr_match))

    # 3f) Safe_EV with 2024 climatology spoilage subtracted in G_1sd
    sp_cl = spoil_frac_ref(
        test["Commodity"].to_numpy(),
        test["truck_hours"].to_numpy(dtype=np.float64),
        np.zeros(len(test)),
        test["clim_tmax_2024"].to_numpy(dtype=np.float64),
        test["clim_rh_2024"].to_numpy(dtype=np.float64),
        test["clim_rain_2024"].to_numpy(dtype=np.float64),
    )
    sc_safe_cl = (
        test["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64)
        * (
            test["dest_lag_price"].to_numpy(dtype=np.float64)
            * (1.0 - test["dest_price_cv_28d"].to_numpy(dtype=np.float64))
            * (1.0 - sp_cl)
            * (1.0 - test["fee_rate"].to_numpy(dtype=np.float64))
            - test["origin_lag_price"].to_numpy(dtype=np.float64)
        )
        - test["freight_road"].to_numpy(dtype=np.float64)
    )
    ch_safe_cl = pick_episode(test, sc_safe_cl, age_test13 & (sc_safe_cl > 0.0))

    # 3g) Test-set exact dispatch-matched B2 comparisons (eliminating dispatch drift confounder A17 #6)
    rr_disp_rate = float(chosen_pols["RR_Abstain_matched"]["eligible"].mean())
    safe_m0_disp_rate = float(chosen_pols["Safe_EV_Sunk_m0"]["eligible"].mean())
    th_b2_test_rr = find_val_matched_threshold(test, tf["net_road_fee"], age_test13, rr_disp_rate)
    th_b2_test_safe = find_val_matched_threshold(test, tf["net_road_fee"], age_test13, safe_m0_disp_rate)
    ch_b2_test_rr = pick_episode(test, tf["net_road_fee"], age_test13 & (tf["net_road_fee"] > th_b2_test_rr))
    ch_b2_test_safe = pick_episode(test, tf["net_road_fee"], age_test13 & (tf["net_road_fee"] > th_b2_test_safe))

    abl_rows = []
    for lbl, ch_a, note in (
        ("MG_val_es10_tuned_matched", ch_mg_es10, f"rep28>={rcut_b}, dow8>={dcut_b}, th={th_mg_es10:.2f}"),
        ("RR_rep14_only_matched", ch_rr14, f"equal 14d info to B_simple, th={th_rr14:.2f}"),
        ("B2_dist_penalty_3F_matched", ch_dist, f"no p_rep, pure distance penalty, th={th_dist:.2f}"),
        ("Safe_EV_fixed10pct_m0", ch_fix10_m0, "fixed 10% haircut, m=0"),
        ("Safe_EV_fixed10pct_matched", ch_fix10_mat, f"fixed 10% haircut, th={th_fix10_m:.2f}"),
        ("Safe_EV_euclid120_m0", ch_safe_euc, "1.20 * euclid_km freight"),
        ("RR_Abstain_euclid120", ch_rr_euc, "1.20 * euclid_km freight"),
        ("Safe_EV_clim2024_m0", ch_safe_cl, "with 2024 ERA5 state-mo clim spoil"),
        ("B2_test_matched_to_RR_69pct", ch_b2_test_rr, f"exact test-matched B2 th={th_b2_test_rr:.2f}"),
        ("B2_test_matched_to_SafeM0", ch_b2_test_safe, f"exact test-matched B2 th={th_b2_test_safe:.2f}"),
    ):
        r = _extended_metrics(lbl, ch_a, test_ot)
        r["note"] = note
        abl_rows.append(r)
    pd.DataFrame(abl_rows).to_csv(out_dir / "a18_fair_ablations.csv", index=False)

    # 4. Missing-Quote & Manski Regimes (A17 #2)
    div_mask = np.char.startswith(test_ot.astype(str), "no_comm_divert")
    exact_d0_cand = test_ot == "exact_d0"
    sp0_test = test["spoil_ref_0"].to_numpy(dtype=np.float64)
    fee_t = test["fee_rate"].to_numpy(dtype=np.float64)
    froad_t = test["freight_road"].to_numpy(dtype=np.float64)
    local_t = test["settle_local_price_d0"].to_numpy(dtype=np.float64)
    pdest_l = test["dest_lag_price"].to_numpy(dtype=np.float64)

    y_zero_sp = settle_candidates(test, div=0.0, disc=0.0)
    y_mild = settle_candidates(test, div=0.5, disc=0.05)
    y_harsh = settle_candidates(test, div=2.0, disc=0.20)
    # Exact zero divert loss (literally payoff = 0.0 when blank/diverted!)
    y_exact_zero_div = np.where(div_mask, 0.0, test["y"].to_numpy(dtype=np.float64))
    # Open-yard MAR counterfactual: portal omitted row -> transaction actually cleared at dest_lag_price!
    y_mar_open = pd.Series(test["y"].to_numpy(dtype=np.float64)).to_numpy()
    y_mar_cand = pdest_l * (1.0 - sp0_test) * (1.0 - fee_t) - froad_t - local_t
    y_mar_open = np.where(div_mask, y_mar_cand, test["y"].to_numpy(dtype=np.float64))

    rep14_t = test["dest_exact_rep_14d"].to_numpy(dtype=np.float64)
    comm_t = test["Commodity"].to_numpy()

    miss_scenarios = [
        ("div_2.0_disc_0.10", settle_candidates(test, div=2.0, disc=0.10)),
        ("div_1.5_disc_0.10_base", test["y"].to_numpy(dtype=np.float64)),
        ("div_1.0_disc_0.10", settle_candidates(test, div=1.0, disc=0.10)),
        ("div_0.5_disc_0.10", settle_candidates(test, div=0.5, disc=0.10)),
        ("div_0.0_spoil_only", y_zero_sp),
        ("exact_zero_divert_payoff_0", y_exact_zero_div),
        ("open_yard_MAR_lagged_price", y_mar_open),
        ("het_crop_perishability", np.where(comm_t == "Tomato", y_harsh, np.where(comm_t == "Potato", y_mild, test["y"].to_numpy(dtype=np.float64)))),
        ("het_selective_missing_lowrep_harsh", np.where(rep14_t < 0.50, y_harsh, y_mild)),
        ("het_adversarial_lowrep_ok_highrep_harsh", np.where(rep14_t >= 0.50, y_harsh, y_zero_sp)),
    ]
    miss_pols = ("B1_lagged_screen", "B2_age_matched", "B_simple_activity_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Sunk_matched", "RT_2F_Min_m0")
    miss_rows = []
    for s_lbl, y_s in miss_scenarios:
        for pname in miss_pols:
            ch = chosen_pols[pname]
            r = _extended_metrics(pname, ch, test_ot, y_override=y_s[ch["_i"].to_numpy()])
            r["missing_scenario"] = s_lbl
            miss_rows.append(r)

    # Realized exact_d0-only counterfactual (pure open-market price risk without ANY arrival missingness)
    for pname in miss_pols:
        ch = chosen_pols[pname]
        disp = ch["eligible"].to_numpy(dtype=bool)
        idx_c = ch["_i"].to_numpy()
        is_ex0 = disp & (test_ot[idx_c] == "exact_d0")
        sub_ch = ch.loc[is_ex0].reset_index(drop=True)
        r = _extended_metrics(pname, sub_ch, test_ot)
        r["missing_scenario"] = "realized_exact_d0_dispatched_only"
        miss_rows.append(r)
    pd.DataFrame(miss_rows).to_csv(out_dir / "a18_missing_regimes.csv", index=False)

    # Bootstrap at div=0.0_spoil_only and exact_zero_divert_payoff_0 for RR and Safe_EV_Sunk vs B2
    miss_boot = {}
    for m_lbl, y_s in (("div_0.0_spoil_only", y_zero_sp), ("exact_zero_divert_payoff_0", y_exact_zero_div), ("open_yard_MAR_lagged_price", y_mar_open)):
        mb = bdf[["episode_id", "date", "origin_market_key"]].copy()
        for pname in ("B2_age_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0"):
            ch = chosen_pols[pname]
            el = ch["eligible"].to_numpy(dtype=bool)
            mb[pname] = np.where(el, y_s[ch["_i"].to_numpy()], 0.0)
        for ca in ("RR_Abstain_matched", "Safe_EV_Sunk_m0"):
            res = two_way_cluster_bootstrap_all_metrics(mb, ca, "B2_age_matched", mandi_col="origin_market_key", reps=1000, seed=20261117)
            miss_boot[f"{m_lbl}__{ca}_vs_B2"] = {
                m: {k: round(float(v), 4) for k, v in md.items()} for m, md in res.items()
            }

    # 5. Full 18-scenario Tornado under BOTH frozen and re-scored decisions (A17 #5)
    scenarios: Dict[str, dict] = {
        "base": dict(),
        "freight_niti_floor_0.258": dict(freight_per_km=0.258, freight_base=20.0),
        "freight_lcv_0.75": dict(freight_per_km=0.75),
        "freight_steep_1.20": dict(freight_per_km=1.20),
        "hp_mult_1.00": dict(hp_km_mult=1.00),
        "hp_mult_1.75": dict(hp_km_mult=1.75),
        "arhtiya_2pct": dict(arhtiya_rate=0.02),
        "arhtiya_4pct": dict(arhtiya_rate=0.04),
        "arhtiya_6pct": dict(arhtiya_rate=0.06),
        "fee_buyer_paid_0pct": dict(fee_mult=0.0),
        "spoil_0.5x": dict(spoil_mult=0.5),
        "spoil_1.5x": dict(spoil_mult=1.5),
        "spoil_2.0x": dict(spoil_mult=2.0),
        "detention_0": dict(detention_per_day=0.0),
        "detention_100": dict(detention_per_day=100.0),
        "joint_optimistic_niti": dict(freight_per_km=0.258, freight_base=20.0, spoil_mult=0.5, div=0.5),
        "joint_realistic_harsh_lcv_arhtiya4": dict(freight_per_km=0.75, arhtiya_rate=0.04, spoil_mult=1.5),
        "outside_option_origin_lag": dict(outside_option="lag"),
    }
    torn_pols = ("B1_lagged_screen", "B2_age_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0")
    torn_rows = []
    for sname, kw in scenarios.items():
        y_sc, ot_sc = settle_candidates(test, how="sequential", weather="none", return_outcomes=True, **kw)
        # Frozen base decisions
        for pname in torn_pols:
            ch = chosen_pols[pname]
            r = _extended_metrics(pname, ch, ot_sc, y_override=y_sc[ch["_i"].to_numpy()])
            r["scenario"] = sname
            r["decision_mode"] = "frozen"
            torn_rows.append(r)
        # Re-scored decisions under altered cost parameters
        test_r = _recompute_scenario_decision_df(test, kw)
        test_r["y"] = y_sc
        sc_r = _score_frame_for_policy(test_r, age_test, float(th_base["B2_age_matched"]), m_mg_match, kappa_star, m_rr_match, m_safe_match, m_phys_match, m_rtmin_match)
        for pname in torn_pols:
            s_arr, el_arr = sc_r[pname]
            ch_r = pick_episode(test_r, s_arr, el_arr)
            rr = _extended_metrics(pname, ch_r, ot_sc)
            rr["scenario"] = sname
            rr["decision_mode"] = "rescored"
            torn_rows.append(rr)
    pd.DataFrame(torn_rows).to_csv(out_dir / "a18_tornado.csv", index=False)

    # 6. Settlement, Exact-Geocode, Non-Conflicting-Dup, Origin-Lag 1..3 & Unconditional Origin Panel (A17 #4, #5, #8)
    sr_rows = []
    y_hind, ot_hind = settle_candidates(test, how="hindsight", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    y_olag, ot_olag = settle_candidates(test, how="sequential", weather="none", div=1.5, disc=0.10, outside_option="lag", return_outcomes=True)
    for m_lbl, y_m, ot_m in (
        ("sequential_base", y_seq[df["date"] > "2025-05-31"], test_ot),
        ("hindsight_3d", y_hind, ot_hind),
        ("outside_origin_lag", y_olag, ot_olag),
    ):
        for pname in torn_pols:
            ch = chosen_pols[pname]
            r = _extended_metrics(pname, ch, ot_m, y_override=y_m[ch["_i"].to_numpy()])
            r["robustness_slice"] = m_lbl
            sr_rows.append(r)

    # Sub-slices: exact geocode, non-conflicting dups, origin_lag_age 1..3
    mc = pd.read_parquet(ROOT / "data/processed/mandi_coordinates.parquet", columns=["State", "Market", "geocode_precision"]).drop_duplicates(["State", "Market"])
    exact_set = set(zip(mc.loc[mc["geocode_precision"] == "market_exact", "State"], mc.loc[mc["geocode_precision"] == "market_exact", "Market"]))
    test_exact_geo = np.array([((s, om) in exact_set) and ((s, dm) in exact_set) for s, om, dm in zip(test["State"], test["origin_market"], test["dest_market"])], dtype=bool)
    ep_exact_geo = test.groupby("episode_id")["origin_market"].transform(lambda s: True).to_numpy()
    ep_no_conf = ~test.groupby("episode_id")["touches_conflicting_dup"].transform("any").to_numpy()
    ep_olag13 = test["origin_lag_age"].to_numpy() <= 3

    for sl_lbl, cand_mask in (
        ("exact_geocode_corridors_only", test_exact_geo),
        ("non_conflicting_dup_episodes_only", ep_no_conf),
        ("origin_lag_age_1_3_only", ep_olag13),
    ):
        sub_df = test.loc[cand_mask].copy().reset_index(drop=True)
        sub_ot = sub_df["_ot"].to_numpy()
        sf = compute_decision_features(sub_df)
        sc_sub = _score_frame_for_policy(sub_df, sf["age"], float(th_base["B2_age_matched"]), m_mg_match, kappa_star, m_rr_match, m_safe_match, m_phys_match, m_rtmin_match, feats=sf)
        for pname in torn_pols:
            ch_s = pick_episode(sub_df, *sc_sub[pname])
            r = _extended_metrics(pname, ch_s, sub_ot)
            r["robustness_slice"] = sl_lbl
            sr_rows.append(r)

    # Unconditional Origin Panel (A17 #4: keep active origin days that did NOT report exact variety on day t!)
    cor = pd.read_parquet(ROOT / "data/processed/osrm_corridor_matrix.parquet")
    fees = pd.read_csv(ROOT / "data/processed/state_apmc_and_loss_parameters.csv")
    unc_test, unc_counts = _unconditional_origin_panel(ROOT, cor, fees, None)
    unc_y_d0lag, unc_ot = settle_candidates(unc_test, how="sequential", weather="none", div=1.5, disc=0.10, outside_option="d0_or_lag", return_outcomes=True)
    unc_y_lag = settle_candidates(unc_test, how="sequential", weather="none", div=1.5, disc=0.10, outside_option="lag")
    unc_test["y"] = unc_y_d0lag
    uf = compute_decision_features(unc_test)
    sc_unc = _score_frame_for_policy(unc_test, uf["age"], float(th_base["B2_age_matched"]), m_mg_match, kappa_star, m_rr_match, m_safe_match, m_phys_match, m_rtmin_match, feats=uf)
    for m_lbl, y_u in (("unconditional_orig_panel_d0_or_lag", unc_y_d0lag), ("unconditional_orig_panel_lag_outside", unc_y_lag)):
        for pname in torn_pols:
            ch_u = pick_episode(unc_test, *sc_unc[pname])
            r = _extended_metrics(pname, ch_u, unc_ot, y_override=y_u[ch_u["_i"].to_numpy()])
            r["robustness_slice"] = m_lbl
            sr_rows.append(r)
    pd.DataFrame(sr_rows).to_csv(out_dir / "a18_settlement_and_robustness.csv", index=False)

    # 7. Crop & 6-State Splits with Paired Cluster CIs (A17 #5)
    cs_rows = []
    cs_policies = ("B2_age_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Sunk_matched", "RT_2F_Min_m0")
    slices_iter = [
        ("Commodity", c, bdf["Commodity"] == c) for c in ("Apple", "Potato", "Onion", "Tomato")
    ] + [("Commodity", "NonApple", bdf["Commodity"] != "Apple")] + [
        ("State", s, bdf["State"] == s) for s in sorted(bdf["State"].unique())
    ]
    for stype, sname, smask in slices_iter:
        g = bdf.loc[smask].reset_index(drop=True)
        r_safe = two_way_cluster_bootstrap_all_metrics(g, "Safe_EV_Sunk_m0", "B2_age_matched", reps=1000, seed=20261117)
        r_rr = two_way_cluster_bootstrap_all_metrics(g, "RR_Abstain_matched", "B2_age_matched", reps=1000, seed=20261117)
        for pname in cs_policies:
            vals = g[pname].to_numpy(dtype=np.float64)
            ci_m = ""
            ci_e = ""
            if pname == "Safe_EV_Sunk_m0":
                ci_m = f"[{r_safe['mean']['ci95_low']:.2f}, {r_safe['mean']['ci95_high']:.2f}]"
                ci_e = f"[{r_safe['es10']['ci95_low']:.2f}, {r_safe['es10']['ci95_high']:.2f}]"
            elif pname == "RR_Abstain_matched":
                ci_m = f"[{r_rr['mean']['ci95_low']:.2f}, {r_rr['mean']['ci95_high']:.2f}]"
                ci_e = f"[{r_rr['es10']['ci95_low']:.2f}, {r_rr['es10']['ci95_high']:.2f}]"
            cs_rows.append({
                "slice_type": stype,
                "slice": sname,
                "n": int(len(g)),
                "policy": pname,
                "dispatch_rate": round(float(g[f"{pname}_disp"].mean()), 4),
                "mean": round(float(vals.mean()), 2),
                "ep_loss_rate": round(float((vals < 0).mean()), 4),
                "es10": round(float(es10(vals)), 2),
                "diff_vs_B2_mean_ci95": ci_m,
                "diff_vs_B2_es10_ci95": ci_e,
            })
    pd.DataFrame(cs_rows).to_csv(out_dir / "a18_crop_and_state_splits.csv", index=False)

    # 8. Outcome mix across headline policies
    om_rows = []
    for pname in torn_pols:
        ch = chosen_pols[pname]
        tot = len(ch)
        disp = ch[ch["eligible"]]
        ots = test_ot[disp["_i"].to_numpy()]
        for otype in pd.unique(ots):
            cnt = int((ots == otype).sum())
            om_rows.append({
                "policy": pname,
                "outcome_type": str(otype),
                "count": cnt,
                "pct_episodes": round(100.0 * cnt / tot, 2),
                "pct_dispatched": round(100.0 * cnt / max(1, len(disp)), 2),
            })
        abstain = int((~ch["eligible"]).sum())
        om_rows.append({"policy": pname, "outcome_type": "ABSTAIN_HOME", "count": abstain, "pct_episodes": round(100.0 * abstain / tot, 2), "pct_dispatched": 0.0})
    pd.DataFrame(om_rows).to_csv(out_dir / "a18_outcome_mix.csv", index=False)

    # 9. Full risk-coverage curves with 95% cluster CIs (including RR_Abstain & Safe_EV_Sunk & RT_2F_Min)
    rc_rows = []
    rc_specs = [
        ("B2_age_matched", tf["net_road_fee"], age_test13, list(range(0, 601, 50))),
        ("MG_T1_T2_T3_T4", tf["net_road_fee_spoil"], age_test13 & (tf["rep14"] >= 0.50) & (tf["dow8"] >= 0.35), list(range(0, 601, 50))),
        ("RR_Abstain", rr_abstain_score(test, kappa_star), age_test13, [-200, -100, 0, 50, 100, 150, 200, 300, 400, 500]),
        ("Safe_EV_Sunk", score_safe_ev_sunk(test), age_test13, [-200, -100, -50, 0, 50, 100, 150, 200, 300, 400]),
        ("RT_2F_Min", score_rt2f_min(test), age_test13, [-200, -100, 0, 50, 100, 150, 200, 300, 400]),
    ]
    for fam, s_arr, g_arr, knobs in rc_specs:
        for kn in knobs:
            ch = pick_episode(test, s_arr, g_arr & (s_arr > float(kn)))
            rec = summarize_chosen(fam, ch)
            cis = ci95_single_metric(ch, "y", reps=400, seed=20261117 + abs(int(kn)))
            rec["knob"] = kn
            rec["family"] = fam
            rec["ep_loss_ci95_low"] = round(cis["ep_loss_rate"][0], 4)
            rec["ep_loss_ci95_high"] = round(cis["ep_loss_rate"][1], 4)
            rec["es10_ci95_low"] = round(cis["es10"][0], 2)
            rec["es10_ci95_high"] = round(cis["es10"][1], 2)
            rc_rows.append(rec)
    pd.DataFrame(rc_rows).to_csv(out_dir / "a18_risk_coverage.csv", index=False)

    # 10. Zero-retuning test on Lagged HP Graded Apples (N = 2,802)
    hp = pd.read_parquet(out_dir / "lagged_hp_apple_candidates.parquet")
    hp["date"] = pd.to_datetime(hp["date"])
    hp_y, hp_ot = settle_candidates(hp, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    hp["y"] = hp_y
    hp_rows = []
    for w_lbl, sub_hp in (("ALL_2025_2026", hp), ("POST_JUNE_2026", hp[hp["date"] >= pd.Timestamp("2026-06-01")].reset_index(drop=True))):
        hf = compute_decision_features(sub_hp)
        sc_hp = _score_frame_for_policy(sub_hp, hf["age"], float(th_base["B2_age_matched"]), m_mg_match, kappa_star, m_rr_match, m_safe_match, m_phys_match, m_rtmin_match, feats=hf)
        sub_ot = hp_ot[sub_hp.index] if w_lbl == "ALL_2025_2026" else hp_ot[hp["date"] >= pd.Timestamp("2026-06-01")]
        for pname in ("B1_lagged_screen", "B2_age_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "Safe_EV_Sunk_matched", "RT_2F_Min_m0"):
            ch_hp = pick_episode(sub_hp, *sc_hp[pname])
            rec = _extended_metrics(pname, ch_hp, sub_ot)
            rec["window"] = w_lbl
            hp_rows.append(rec)
    pd.DataFrame(hp_rows).to_csv(out_dir / "a18_hp_apple.csv", index=False)

    # Origin lag age distribution & day-t origin conditioning stats on test
    orig_eps = test.groupby("episode_id").first()
    olag_4_7 = int((orig_eps["origin_lag_age"] > 3).sum())
    exact_geo_row_frac = float(test_exact_geo.mean())
    exact_geo_ep_frac = float(test.groupby("episode_id").apply(lambda g: bool(((g["State"].iloc[0], g["origin_market"].iloc[0]) in exact_set) and all((s, d) in exact_set for s, d in zip(g["State"], g["dest_market"])))).mean())

    unc_test_only = unc_test[unc_test["date"] > pd.Timestamp("2025-05-31")]
    unc_eps_n = int(unc_test_only["episode_id"].nunique())
    unc_unrep_d0 = int(unc_test_only.groupby("episode_id")["settle_local_price_d0"].first().isna().sum())

    meta = {
        "prereg_a18_commit": "4cbb02d",
        "exploratory": True,
        "target_val_disp": target_val_disp,
        "val_matched_thresholds": {
            "B_simple_activity": round(m_act_match, 4),
            "MG_matched": round(m_mg_match, 4),
            "RR_Abstain_matched": round(m_rr_match, 4),
            "RR_Abstain_phys15_matched": round(m_rr15_match, 4),
            "Safe_EV_Sunk_matched": round(m_safe_match, 4),
            "Safe_EV_Phys_matched": round(m_phys_match, 4),
            "RT_2F_Min_matched": round(m_rtmin_match, 4),
            "MG_val_es10_grid_best": {"rep28": rcut_b, "dow8": dcut_b, "th": round(th_mg_es10, 4)},
        },
        "a17_forensic_counts": {
            "test_exact_geocode_row_pct": round(100.0 * exact_geo_row_frac, 2),
            "test_centroid_approx_row_pct": round(100.0 * (1.0 - exact_geo_row_frac), 2),
            "test_origin_lag_4_7_episodes": olag_4_7,
            "unconditional_origin_test_episodes": unc_eps_n,
            "unconditional_origin_missing_d0_episodes": unc_unrep_d0,
            "unconditional_counts": unc_counts,
        },
        "missing_regime_bootstraps": miss_boot,
    }
    (out_dir / "a18_summary.json").write_text(json.dumps(meta, indent=2, default=float))

    print("=== A18 HEAD-TO-HEAD RESULTS (test N = 58,676) ===")
    print(pd.DataFrame(res_rows)[["policy", "free_params", "dispatch_rate", "mean", "ep_loss_rate", "cond_loss_rate", "es10", "loss_given_loss", "mean_road_km"]].to_string(index=False))
    print("\n=== A18 HOLM-BONFERRONI (TWO-SIDED PRIMARY, ALL 3 CLUSTERINGS) ===")
    print(boot_df[boot_df["hypothesis_id"] != ""][["hypothesis_id", "cluster", "metric", "estimate", "ci95_low", "ci95_high", "p_value_two_sided", "p_holm_2s", "n_clusters"]].to_string(index=False))
    print("\n=== A18 STATE SPLITS (Safe_EV_Sunk_m0 vs RR_Abstain_matched vs B2) ===")
    st_sub = pd.DataFrame(cs_rows)
    print(st_sub[(st_sub["slice_type"] == "State") & (st_sub["policy"].isin(["B2_age_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0"]))][["slice", "n", "policy", "dispatch_rate", "mean", "es10", "diff_vs_B2_es10_ci95"]].to_string(index=False))
    print("\n=== A18 HP GRADED APPLE (ALL_2025_2026) ===")
    hp_df_r = pd.DataFrame(hp_rows)
    print(hp_df_r[hp_df_r["window"] == "ALL_2025_2026"][["policy", "dispatch_rate", "mean", "ep_loss_rate", "cond_loss_rate", "es10"]].to_string(index=False))


if __name__ == "__main__":
    run()
