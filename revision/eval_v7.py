"""Revision v7 Primary Zero-Lookahead (171-Market) & Historical Out-of-Period (2018-2023) Pipeline.

Directly addresses all external-review structural critiques without modifying any frozen Stage I,
A10, A18, or v6 outputs (`R5`, `R8`, `R9`):
  1. Promotes the strict 2024-only 171-market panel (`N = 57,634` test, `N_val = 35,870` val, rebuilt
     end-to-end from raw records with zero post-2024 market-selection or shortlist lookahead) to the
     PRIMARY main analysis across ALL tables (main benchmark, fair ablations, missing-quote bounds,
     6-state & 5-crop splits, 36-cell tornado, structural/unconditional checks, ERA5 settlement, and
     exact silent-market break-even).
  2. Preserves the exact locked `PREREG_A18.md` 4-hypothesis family (`H_A18_1..4`) at exact locked
     `R = 2,000` replicates (`p_holm_2s` floor `0.0040`) as primary registered inference, strictly
     separated from unregistered post-hoc `R = 5,000` Monte Carlo precision & `1w/2w/4w` block checks.
  3. Explicitly computes & reports all negative/reversal Mean results (`div = 0.0_spoil_only` and
     `exact_zero_divert_payoff_0` non-significant Mean diffs, `hindsight_3d` higher Mean for `B2`,
     Open-MAR Mean reversal, state/crop Mean CIs crossing zero, and Potato `ES10` vs `RR`).
  4. Adds an untouched historical out-of-period generalization test across six full years (`2018-2023`,
     with `2017` causal burn-in, `N = 389,357` episodes + `2017`-active `120`-market subset) evaluating
     frozen zero-parameter rules verbatim with zero retuning (including year-by-year 2018..2023 and
     2020 COVID shock, closed & Open-MAR bounds, exact break-even, and R=2,000 cluster bootstrap).
  5. Quantifies exact price-level decomposition between the 178-mkt 20C legacy panel, the 171-mkt 20C
     primary panel, and 171-mkt realized ERA5 arrival-day weather settlement.
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
    _recompute_scenario_decision_df,
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
    summarize_chosen,
    tune_threshold_on_val,
)
from revision.eval_v6 import (
    _compute_breakeven_rows,
    _dest_or_origin_key,
    attach_realized_era5_settlement_weather,
    get_2024_only_markets,
    settle_realized_era5_sequential,
)
from revision.stats_utils import (
    ci95_single_metric,
    es_alpha,
    two_way_cgm_and_studentized_test,
    two_way_cluster_bootstrap_all_metrics,
    two_way_cluster_bootstrap_extended,
)
from src.evaluation.bootstrap import holm_bonferroni

ROOT = Path(__file__).resolve().parents[1]


def _extended_metrics_v7(
    name: str,
    ch: pd.DataFrame,
    otypes_all: np.ndarray,
    y_override: np.ndarray | None = None,
) -> dict:
    rec = _extended_metrics(name, ch, otypes_all, y_override=y_override)
    elig = ch["eligible"].to_numpy(dtype=bool)
    y_raw = ch["y_raw"].to_numpy(dtype=np.float64) if y_override is None else y_override
    if int(elig.sum()) > 0:
        disp_y = y_raw[elig]
        rec["cond_es10"] = round(float(es_alpha(disp_y, 0.10)), 2)
        rec["cond_es05"] = round(float(es_alpha(disp_y, 0.05)), 2)
    else:
        rec["cond_es10"] = None
        rec["cond_es05"] = None
    return rec


def _score_all_14(
    df: pd.DataFrame,
    th_b2: float,
    m_act: float,
    m_mg: float,
    kappa_star: float,
    m_rr: float,
    m_rr15: float,
    m_safe: float,
    m_phys: float,
    m_rtmin: float,
    feats: dict | None = None,
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    f = compute_decision_features(df) if feats is None else feats
    age13 = (f["age"] >= 1) & (f["age"] <= 3)
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
        "B_simple_activity_matched": (f["net_road_fee"], age13 & (f["rep14"] >= 0.50) & (f["net_road_fee"] > m_act)),
        "MG_matched": (
            f["net_road_fee_spoil"],
            age13 & (f["rep14"] >= 0.50) & (f["dow8"] >= 0.35) & (f["net_road_fee_spoil"] > m_mg),
        ),
        "RR_Abstain_matched": (sc_rr, age13 & (sc_rr > m_rr)),
        "RR_Abstain_m0": (sc_rr, age13 & (sc_rr > 0.0)),
        "RR_Abstain_phys15_matched": (sc_rr15, age13 & (sc_rr15 > m_rr15)),
        "Safe_EV_Sunk_m0": (sc_safe, age13 & (sc_safe > 0.0)),
        "Safe_EV_Sunk_matched": (sc_safe, age13 & (sc_safe > m_safe)),
        "Safe_EV_Phys_m0": (sc_phys, age13 & (sc_phys > 0.0)),
        "Safe_EV_Phys_matched": (sc_phys, age13 & (sc_phys > m_phys)),
        "RT_2F_Min_m0": (sc_rtmin, age13 & (sc_rtmin > 0.0)),
        "RT_2F_Dow_m0": (sc_rtdow, age13 & (sc_rtdow > 0.0)),
        "EV_RT_Min_m0": (sc_evrt, age13 & (sc_evrt > 0.0)),
    }


def _open_mar_20c(df: pd.DataFrame, y_closed: np.ndarray, ot_closed: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    div_mask = np.char.startswith(ot_closed.astype(str), "no_comm_divert")
    same = df["same_district"].to_numpy(dtype=bool)
    sale_fee = np.where(same, 0.0, df["fee_rate"].to_numpy(dtype=np.float64))
    y_mar_cand = (
        df["dest_lag_price"].to_numpy(dtype=np.float64)
        * (1.0 - df["spoil_ref_0"].to_numpy(dtype=np.float64))
        * (1.0 - sale_fee)
        - df["freight_road"].to_numpy(dtype=np.float64)
        - df["settle_local_price_d0"].to_numpy(dtype=np.float64)
    )
    y_open = np.where(div_mask, y_mar_cand, y_closed)
    ot_open = np.where(div_mask, "open_yard_mar_silent", ot_closed.astype(str))
    return y_open, ot_open


def run() -> None:
    out_dir = ROOT / "revision" / "results"
    summary_a10 = json.loads((out_dir / "a10_summary.json").read_text())
    kappa_star = float(summary_a10["kappa_star_matched"])

    raw = pd.read_parquet(ROOT / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet")
    cor = pd.read_parquet(ROOT / "data/processed/osrm_corridor_matrix.parquet")
    fees = pd.read_csv(ROOT / "data/processed/state_apmc_and_loss_parameters.csv")
    coords = pd.read_parquet(ROOT / "data/processed/mandi_coordinates.parquet")
    wx = pd.read_parquet(ROOT / "data/processed/mandi_weather_2024_2026.parquet")

    # =========================================================================
    # PART A: PRIMARY ZERO-LOOKAHEAD 2024-ONLY 171-MARKET PANEL (N = 57,634)
    # =========================================================================
    mkts_2024 = get_2024_only_markets(raw, min_days=80, max_per_state=30)
    assert len(mkts_2024) == 171, f"Expected 171 markets from 2024-only filter, got {len(mkts_2024)}"
    mkt_set_2024 = set(zip(mkts_2024["State"].astype(str), mkts_2024["Market"].astype(str)))

    raw_171_mask = [(st, mk) in mkt_set_2024 for st, mk in zip(raw["State"].astype(str), raw["Market"].astype(str))]
    raw_171 = raw.loc[raw_171_mask].copy().reset_index(drop=True)
    df_171_all, counts_171 = build_lagged_candidates_from_frames(
        raw_df=raw_171,
        corridors_df=cor,
        fee_params_df=fees,
        clim_df=None,
        grade_explicit=False,
    )
    df_171_all["date"] = pd.to_datetime(df_171_all["date"])
    y_all, ot_all = settle_candidates(df_171_all, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    df_171_all["y"] = y_all
    df_171_all["_ot"] = ot_all

    val = df_171_all[df_171_all["date"] <= pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    test = df_171_all[df_171_all["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    test_ot = test["_ot"].to_numpy()
    vf = compute_decision_features(val)
    tf = compute_decision_features(test)
    age_val13 = (vf["age"] >= 1) & (vf["age"] <= 3)
    age_test13 = (tf["age"] >= 1) & (tf["age"] <= 3)

    # Calibrate B2 and matched comparators strictly on val_171
    th_b2, val_b2_summ = tune_threshold_on_val(val, vf, "net_road_fee", lambda ft: (ft["age"] >= 1) & (ft["age"] <= 3))
    target_val_disp = float(val_b2_summ["dispatch_rate"])
    m_act = find_val_matched_threshold(val, vf["net_road_fee"], age_val13 & (vf["rep14"] >= 0.50), target_val_disp)
    m_mg = find_val_matched_threshold(
        val, vf["net_road_fee_spoil"], age_val13 & (vf["rep14"] >= 0.50) & (vf["dow8"] >= 0.35), target_val_disp
    )
    m_rr = find_val_matched_threshold(val, rr_abstain_score(val, kappa_star), age_val13, target_val_disp)
    m_rr15 = find_val_matched_threshold(val, rr_abstain_score(val, 1.5), age_val13, target_val_disp)
    m_safe = find_val_matched_threshold(val, score_safe_ev_sunk(val), age_val13, target_val_disp)
    m_phys = find_val_matched_threshold(val, score_safe_ev_phys(val), age_val13, target_val_disp)
    m_rtmin = find_val_matched_threshold(val, score_rt2f_min(val), age_val13, target_val_disp)

    # 1. Primary Main Table (v7_main_171.csv) & Outcome Mix (v7_outcome_mix_171.csv)
    sc_map = _score_all_14(test, th_b2, m_act, m_mg, kappa_star, m_rr, m_rr15, m_safe, m_phys, m_rtmin, feats=tf)
    meta_tags = {
        "B1_lagged_screen": (1, 100.0),
        "B2_age_matched": (1, round(th_b2, 2)),
        "B_simple_activity_matched": (2, round(m_act, 2)),
        "MG_matched": (4, round(m_mg, 2)),
        "RR_Abstain_matched": (2, round(m_rr, 2)),
        "RR_Abstain_m0": (1, 0.0),
        "RR_Abstain_phys15_matched": (1, round(m_rr15, 2)),
        "Safe_EV_Sunk_m0": (0, 0.0),
        "Safe_EV_Sunk_matched": (1, round(m_safe, 2)),
        "Safe_EV_Phys_m0": (0, 0.0),
        "Safe_EV_Phys_matched": (1, round(m_phys, 2)),
        "RT_2F_Min_m0": (0, 0.0),
        "RT_2F_Dow_m0": (0, 0.0),
        "EV_RT_Min_m0": (0, 0.0),
    }
    chosen: Dict[str, pd.DataFrame] = {}
    main_rows = []
    for pname, (fp, cal_th) in meta_tags.items():
        ch = pick_episode(test, *sc_map[pname])
        chosen[pname] = ch
        rec = _extended_metrics_v7(pname, ch, test_ot)
        rec["free_params"] = fp
        rec["calibrated_threshold"] = cal_th
        main_rows.append(rec)
    pd.DataFrame(main_rows).to_csv(out_dir / "v7_main_171.csv", index=False)

    om_rows = []
    core6 = ("B1_lagged_screen", "B2_age_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0")
    for pname in core6:
        ch = chosen[pname]
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
        om_rows.append({
            "policy": pname,
            "outcome_type": "ABSTAIN_HOME",
            "count": abstain,
            "pct_episodes": round(100.0 * abstain / tot, 2),
            "pct_dispatched": 0.0,
        })
    pd.DataFrame(om_rows).to_csv(out_dir / "v7_outcome_mix_171.csv", index=False)

    # 2. Primary Registered Inference: EXACT PREREG_A18 4-hypothesis family at R = 2,000 (v7_bootstrap_prereg_2000.csv)
    bdf = chosen["B1_lagged_screen"][["episode_id", "date", "origin_market_key", "State", "Commodity"]].copy()
    for pname, ch in chosen.items():
        bdf[pname] = ch["y"].to_numpy(dtype=np.float64)
        bdf[f"{pname}_disp"] = ch["eligible"].to_numpy(dtype=bool)
        bdf[f"{pname}_dest_key"] = _dest_or_origin_key(ch)

    prereg_contrasts = [
        ("H_A18_1", True, "Safe_EV_Sunk_m0", "B2_age_matched", "es10"),
        ("H_A18_2", True, "Safe_EV_Sunk_matched", "RR_Abstain_matched", "es10"),
        ("H_A18_3", True, "Safe_EV_Sunk_m0", "B2_age_matched", "ep_loss_rate"),
        ("H_A18_4", True, "RT_2F_Min_m0", "B2_age_matched", "mean"),
        ("SEC_1", False, "Safe_EV_Sunk_m0", "B2_age_matched", "mean"),
        ("SEC_2", False, "Safe_EV_Phys_m0", "B2_age_matched", "es10"),
        ("SEC_3", False, "MG_matched", "B2_age_matched", "es10"),
        ("SEC_4", False, "RR_Abstain_matched", "B2_age_matched", "es10"),
        ("SEC_5", False, "Safe_EV_Sunk_m0", "RR_Abstain_matched", "es10"),
    ]
    boot2k_rows: List[dict] = []
    for sch_lbl, mkind in (
        ("origin_x_2week", "origin"),
        ("b2dest_or_origin_x_2week", "b2dest"),
        ("policy_dest_or_origin_x_2week", "poldest"),
    ):
        cache: Dict[Tuple[str, str, str], dict] = {}
        fam_rows: List[dict] = []
        for hid, is_reg, pa, pb, metric in prereg_contrasts:
            mcol = "origin_market_key" if mkind == "origin" else ("B2_age_matched_dest_key" if mkind == "b2dest" else f"{pa}_dest_key")
            ck = (pa, pb, mcol)
            if ck not in cache:
                cache[ck] = two_way_cluster_bootstrap_all_metrics(bdf, pa, pb, mandi_col=mcol, week_block_len=2, reps=2000, seed=20261117)
            md = cache[ck][metric]
            fam_rows.append({
                "hypothesis_id": hid,
                "registered_prereg_a18": is_reg,
                "cluster": sch_lbl,
                "policy_a": pa,
                "policy_b": pb,
                "metric": metric,
                "estimate": round(md["estimate"], 4),
                "ci95_low": round(md["ci95_low"], 4),
                "ci95_high": round(md["ci95_high"], 4),
                "p_value_two_sided": round(md["p_value_two_sided"], 6),
                "_raw_p": float(md["p_value_two_sided"]),
                "p_holm_2s_prereg4": np.nan,
                "n": int(md["n"]),
                "n_clusters": int(md["n_clusters"]),
                "n_blocks": int(md["n_blocks"]),
                "reps": 2000,
            })
        reg_idx = [i for i, r in enumerate(fam_rows) if r["registered_prereg_a18"]]
        ph4 = holm_bonferroni([fam_rows[i]["_raw_p"] for i in reg_idx])
        for i, phv in zip(reg_idx, ph4):
            fam_rows[i]["p_holm_2s_prereg4"] = round(float(phv), 6)
        for r in fam_rows:
            r.pop("_raw_p", None)
        boot2k_rows.extend(fam_rows)
    pd.DataFrame(boot2k_rows).to_csv(out_dir / "v7_bootstrap_prereg_2000.csv", index=False)

    # 3. Fair Control Ablations on 171 Markets (v7_ablations_171.csv)
    best_mg = None
    for rcut in (0.30, 0.40, 0.50, 0.60, 0.70, 0.75):
        for dcut in (0.20, 0.35, 0.50):
            gv = age_val13 & (vf["rep28"] >= rcut) & (vf["dow8"] >= dcut)
            if gv.mean() < 0.25:
                continue
            thm = find_val_matched_threshold(val, vf["net_road_fee_spoil"], gv, target_val_disp)
            rec_v = summarize_chosen("mg_grid", pick_episode(val, vf["net_road_fee_spoil"], gv & (vf["net_road_fee_spoil"] > thm)))
            key = (rec_v["es10"], rec_v["mean"])
            if best_mg is None or key > best_mg[0]:
                best_mg = (key, rcut, dcut, thm)
    _, rcut_b, dcut_b, th_mg_es10 = best_mg
    ch_mg_es10 = pick_episode(test, tf["net_road_fee_spoil"], age_test13 & (tf["rep28"] >= rcut_b) & (tf["dow8"] >= dcut_b) & (tf["net_road_fee_spoil"] > th_mg_es10))

    def _rr_rep14(dframe: pd.DataFrame, k: float) -> np.ndarray:
        p = np.clip(dframe["dest_exact_rep_14d"].to_numpy(dtype=np.float64), 0.0, 1.0)
        d_op = dframe["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - dframe["spoil_ref_0"].to_numpy(dtype=np.float64)) * (1.0 - dframe["fee_rate"].to_numpy(dtype=np.float64)) - dframe["origin_lag_price"].to_numpy(dtype=np.float64) - dframe["freight_road"].to_numpy(dtype=np.float64)
        d_ms = -float(k) * dframe["freight_road"].to_numpy(dtype=np.float64) - dframe["origin_lag_price"].to_numpy(dtype=np.float64) * dframe["spoil_ref_0"].to_numpy(dtype=np.float64)
        return p * d_op + (1.0 - p) * d_ms

    th_rr14 = find_val_matched_threshold(val, _rr_rep14(val, kappa_star), age_val13, target_val_disp)
    ch_rr14 = pick_episode(test, _rr_rep14(test, kappa_star), age_test13 & (_rr_rep14(test, kappa_star) > th_rr14))

    sc_dist_v = vf["net_road_fee_spoil"] - 3.0 * val["freight_road"].to_numpy(dtype=np.float64)
    th_dist = find_val_matched_threshold(val, sc_dist_v, age_val13, target_val_disp)
    sc_dist_t = tf["net_road_fee_spoil"] - 3.0 * test["freight_road"].to_numpy(dtype=np.float64)
    ch_dist = pick_episode(test, sc_dist_t, age_test13 & (sc_dist_t > th_dist))

    def _safe_fixed(dframe: pd.DataFrame, drop_pct: float = 0.10) -> np.ndarray:
        p = dframe["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64)
        g_s = dframe["dest_lag_price"].to_numpy(dtype=np.float64) * (1.0 - drop_pct) * (1.0 - dframe["fee_rate"].to_numpy(dtype=np.float64)) - dframe["origin_lag_price"].to_numpy(dtype=np.float64)
        return p * g_s - dframe["freight_road"].to_numpy(dtype=np.float64)

    ch_fix10_m0 = pick_episode(test, _safe_fixed(test), age_test13 & (_safe_fixed(test) > 0.0))
    df_euc = test.copy()
    df_euc["freight_road"] = df_euc["freight_euclid"]
    ch_safe_euc = pick_episode(df_euc, score_safe_ev_sunk(df_euc), age_test13 & (score_safe_ev_sunk(df_euc) > 0.0))
    safe_m0_disp_rate = float(chosen["Safe_EV_Sunk_m0"]["eligible"].mean())
    th_b2_test_safe = find_val_matched_threshold(test, tf["net_road_fee"], age_test13, safe_m0_disp_rate)
    ch_b2_test_safe = pick_episode(test, tf["net_road_fee"], age_test13 & (tf["net_road_fee"] > th_b2_test_safe))

    abl_rows = []
    for lbl, ch_a, note in (
        ("B2_test_matched_to_SafeM0", ch_b2_test_safe, f"exact test-matched B2 th={th_b2_test_safe:.2f}"),
        ("B2_dist_penalty_3F_matched", ch_dist, f"no p_rep, pure distance penalty, th={th_dist:.2f}"),
        ("MG_val_es10_tuned_matched", ch_mg_es10, f"rep28>={rcut_b}, dow8>={dcut_b}, th={th_mg_es10:.2f}"),
        ("RR_rep14_only_matched", ch_rr14, f"equal 14d info, th={th_rr14:.2f}"),
        ("Safe_EV_fixed10pct_m0", ch_fix10_m0, "fixed 10% haircut, m=0"),
        ("Safe_EV_euclid120_m0", ch_safe_euc, "1.20 * euclid_km freight"),
    ):
        r = _extended_metrics_v7(lbl, ch_a, test_ot)
        r["note"] = note
        abl_rows.append(r)
    pd.DataFrame(abl_rows).to_csv(out_dir / "v7_ablations_171.csv", index=False)

    # 4. Missing-Quote Regimes & Paired Cluster Tests (Mean + EpLoss + ES10) on 171 Markets
    y_test = test["y"].to_numpy(dtype=np.float64)
    div_mask = np.char.startswith(test_ot.astype(str), "no_comm_divert")
    y_zero_sp = settle_candidates(test, div=0.0, disc=0.0)
    y_mild = settle_candidates(test, div=0.5, disc=0.05)
    y_harsh = settle_candidates(test, div=2.0, disc=0.20)
    y_exact_zero_div = np.where(div_mask, 0.0, y_test)
    y_mar_open, _ = _open_mar_20c(test, y_test, test_ot)
    rep14_t = test["dest_exact_rep_14d"].to_numpy(dtype=np.float64)
    comm_t = test["Commodity"].to_numpy()

    miss_scenarios = [
        ("div_2.0_disc_0.10", settle_candidates(test, div=2.0, disc=0.10)),
        ("div_1.5_disc_0.10_base", y_test),
        ("div_1.0_disc_0.10", settle_candidates(test, div=1.0, disc=0.10)),
        ("div_0.5_disc_0.10", settle_candidates(test, div=0.5, disc=0.10)),
        ("div_0.0_spoil_only", y_zero_sp),
        ("exact_zero_divert_payoff_0", y_exact_zero_div),
        ("open_yard_MAR_lagged_price", y_mar_open),
        ("het_crop_perishability", np.where(comm_t == "Tomato", y_harsh, np.where(comm_t == "Potato", y_mild, y_test))),
        ("het_selective_missing_lowrep_harsh", np.where(rep14_t < 0.50, y_harsh, y_mild)),
        ("het_adversarial_lowrep_ok_highrep_harsh", np.where(rep14_t >= 0.50, y_harsh, y_zero_sp)),
    ]
    miss_pols = ("B1_lagged_screen", "B2_age_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "RT_2F_Min_m0")
    miss_rows = []
    for s_lbl, y_s in miss_scenarios:
        for pname in miss_pols:
            ch = chosen[pname]
            r = _extended_metrics_v7(pname, ch, test_ot, y_override=y_s[ch["_i"].to_numpy()])
            r["missing_scenario"] = s_lbl
            miss_rows.append(r)
    for pname in miss_pols:
        ch = chosen[pname]
        disp = ch["eligible"].to_numpy(dtype=bool)
        is_ex0 = disp & (test_ot[ch["_i"].to_numpy()] == "exact_d0")
        sub_ch = ch.loc[is_ex0].reset_index(drop=True)
        r = _extended_metrics_v7(pname, sub_ch, test_ot)
        r["missing_scenario"] = "realized_exact_d0_dispatched_only"
        miss_rows.append(r)
    pd.DataFrame(miss_rows).to_csv(out_dir / "v7_missing_regimes_171.csv", index=False)

    miss_test_rows = []
    for m_lbl, y_s in (
        ("div_0.0_spoil_only", y_zero_sp),
        ("exact_zero_divert_payoff_0", y_exact_zero_div),
        ("open_yard_MAR_lagged_price", y_mar_open),
    ):
        mb = bdf[["episode_id", "date", "origin_market_key"]].copy()
        for pname in ("B2_age_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
            ch = chosen[pname]
            el = ch["eligible"].to_numpy(dtype=bool)
            mb[pname] = np.where(el, y_s[ch["_i"].to_numpy()], 0.0)
        sc_tests = []
        for ca in ("Safe_EV_Sunk_m0", "RR_Abstain_matched", "RT_2F_Min_m0"):
            res = two_way_cluster_bootstrap_all_metrics(mb, ca, "B2_age_matched", mandi_col="origin_market_key", reps=2000, seed=20261117)
            for metric, md in res.items():
                raw_p = float(md["p_value_two_sided"])
                sc_tests.append({
                    "missing_scenario": m_lbl,
                    "policy_a": ca,
                    "policy_b": "B2_age_matched",
                    "metric": metric,
                    "estimate": round(md["estimate"], 4),
                    "ci95_low": round(md["ci95_low"], 4),
                    "ci95_high": round(md["ci95_high"], 4),
                    "p_value_two_sided": round(raw_p, 6),
                    "_raw_p": raw_p,
                    "n": int(md["n"]),
                    "n_clusters": int(md["n_clusters"]),
                    "reps": 2000,
                })
        ph_sc = holm_bonferroni([r["_raw_p"] for r in sc_tests])
        for r, phv in zip(sc_tests, ph_sc):
            r["p_holm_2s_scen9"] = round(float(phv), 6)
            r.pop("_raw_p", None)
        miss_test_rows.extend(sc_tests)
    pd.DataFrame(miss_test_rows).to_csv(out_dir / "v7_missing_tests_171.csv", index=False)

    # 5. All 6 States & 5 Crop Slices on 171 Markets (R = 2,000 CIs for Mean, ep_ES10, cond_ES10, null-cent, stud & Holm11)
    cs_rows = []
    cs_pols = ("B2_age_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Sunk_matched", "RT_2F_Min_m0")
    slices_iter = [
        ("Commodity", c, bdf["Commodity"] == c) for c in ("Apple", "Potato", "Onion", "Tomato")
    ] + [("Commodity", "NonApple", bdf["Commodity"] != "Apple")] + [
        ("State", s, bdf["State"] == s) for s in sorted(bdf["State"].unique())
    ]
    for stype, sname, smask in slices_iter:
        g = bdf.loc[smask].reset_index(drop=True)
        r_safe = two_way_cluster_bootstrap_extended(
            g, "Safe_EV_Sunk_m0", "B2_age_matched",
            disp_col_a="Safe_EV_Sunk_m0_disp", disp_col_b="B2_age_matched_disp",
            reps=2000, seed=20261117,
        )
        r_rr = two_way_cluster_bootstrap_extended(
            g, "RR_Abstain_matched", "B2_age_matched",
            disp_col_a="RR_Abstain_matched_disp", disp_col_b="B2_age_matched_disp",
            reps=2000, seed=20261117,
        )
        r_rt = two_way_cluster_bootstrap_extended(
            g, "RT_2F_Min_m0", "B2_age_matched",
            disp_col_a="RT_2F_Min_m0_disp", disp_col_b="B2_age_matched_disp",
            reps=2000, seed=20261117,
        )
        cgm_safe_e = two_way_cgm_and_studentized_test(g, "Safe_EV_Sunk_m0", "B2_age_matched", metric="es10", reps=2000, seed=20261117)
        cgm_rr_e = two_way_cgm_and_studentized_test(g, "RR_Abstain_matched", "B2_age_matched", metric="es10", reps=2000, seed=20261117)
        cgm_rt_e = two_way_cgm_and_studentized_test(g, "RT_2F_Min_m0", "B2_age_matched", metric="es10", reps=2000, seed=20261117)
        for pname in cs_pols:
            vals = g[pname].to_numpy(dtype=np.float64)
            disp_m = g[f"{pname}_disp"].to_numpy(dtype=bool)
            cond_v = vals[disp_m]
            ci_m, ci_e, ci_ce, ci_eb = "", "", "", ""
            p_m, p_e, p_ce, p_e_nc, p_e_stud = np.nan, np.nan, np.nan, np.nan, np.nan
            est_ce = np.nan
            raw_pm, raw_pe = np.nan, np.nan
            ref = r_safe if pname == "Safe_EV_Sunk_m0" else (r_rr if pname == "RR_Abstain_matched" else (r_rt if pname == "RT_2F_Min_m0" else None))
            cgm_ref = cgm_safe_e if pname == "Safe_EV_Sunk_m0" else (cgm_rr_e if pname == "RR_Abstain_matched" else (cgm_rt_e if pname == "RT_2F_Min_m0" else None))
            if ref is not None:
                ci_m = f"[{ref['mean']['ci95_low']:.2f}, {ref['mean']['ci95_high']:.2f}]"
                ci_e = f"[{ref['es10']['ci95_low']:.2f}, {ref['es10']['ci95_high']:.2f}]"
                ci_eb = f"[{ref['es10']['basic_ci95_low']:.2f}, {ref['es10']['basic_ci95_high']:.2f}]"
                ci_ce = f"[{ref['cond_es10']['ci95_low']:.2f}, {ref['cond_es10']['ci95_high']:.2f}]"
                raw_pm = float(ref["mean"]["p_value_two_sided"])
                raw_pe = float(ref["es10"]["p_value_two_sided"])
                p_m = round(raw_pm, 6)
                p_e = round(raw_pe, 6)
                p_ce = round(float(ref["cond_es10"]["p_value_two_sided"]), 6)
                est_ce = round(float(ref["cond_es10"]["estimate"]), 2)
                p_e_nc = round(float(ref["es10"]["p_value_null_cent_2s"]), 6)
                p_e_stud = round(float(cgm_ref["p_stud_2s"]), 6)
            cs_rows.append({
                "slice_type": stype,
                "slice": sname,
                "n": int(len(g)),
                "n_clusters": int(r_safe["mean"]["n_clusters"]),
                "n_blocks": int(r_safe["mean"]["n_blocks"]),
                "policy": pname,
                "dispatch_rate": round(float(disp_m.mean()), 4),
                "mean": round(float(vals.mean()), 2),
                "ep_loss_rate": round(float((vals < 0).mean()), 4),
                "cond_loss_rate": round(float((cond_v < 0).mean()), 4) if len(cond_v) else np.nan,
                "es10": round(float(es10(vals)), 2),
                "cond_es10": round(float(es_alpha(cond_v, 0.10)), 2) if len(cond_v) else np.nan,
                "cond_es05": round(float(es_alpha(cond_v, 0.05)), 2) if len(cond_v) else np.nan,
                "diff_vs_B2_mean_ci95": ci_m,
                "diff_vs_B2_mean_p2s": p_m,
                "diff_vs_B2_mean_holm11": np.nan,
                "diff_vs_B2_es10_ci95": ci_e,
                "diff_vs_B2_es10_basic_ci95": ci_eb,
                "diff_vs_B2_es10_p2s": p_e,
                "diff_vs_B2_es10_holm11": np.nan,
                "diff_vs_B2_es10_p_null_cent": p_e_nc,
                "diff_vs_B2_es10_p_stud": p_e_stud,
                "diff_vs_B2_cond_es10": est_ce,
                "diff_vs_B2_cond_es10_ci95": ci_ce,
                "diff_vs_B2_cond_es10_p2s": p_ce,
                "_raw_pm": raw_pm,
                "_raw_pe": raw_pe,
            })
    for pname in ("Safe_EV_Sunk_m0", "RR_Abstain_matched", "RT_2F_Min_m0"):
        idxs = [i for i, r in enumerate(cs_rows) if r["policy"] == pname]
        phm = holm_bonferroni([cs_rows[i]["_raw_pm"] for i in idxs])
        phe = holm_bonferroni([cs_rows[i]["_raw_pe"] for i in idxs])
        for i, vm, ve in zip(idxs, phm, phe):
            cs_rows[i]["diff_vs_B2_mean_holm11"] = round(float(vm), 6)
            cs_rows[i]["diff_vs_B2_es10_holm11"] = round(float(ve), 6)
    for r in cs_rows:
        r.pop("_raw_pm", None)
        r.pop("_raw_pe", None)
    pd.DataFrame(cs_rows).to_csv(out_dir / "v7_splits_171.csv", index=False)

    # 6. Full 18-Scenario Tornado (36 cells: frozen + rescored) on 171 Markets
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
    torn_rows = []
    for sname, kw in scenarios.items():
        y_sc, ot_sc = settle_candidates(test, how="sequential", weather="none", return_outcomes=True, **kw)
        for pname in core6:
            ch = chosen[pname]
            r = _extended_metrics_v7(pname, ch, ot_sc, y_override=y_sc[ch["_i"].to_numpy()])
            r["scenario"] = sname
            r["decision_mode"] = "frozen"
            torn_rows.append(r)
        val_r = _recompute_scenario_decision_df(val, kw)
        y_val_sc = settle_candidates(val_r, how="sequential", weather="none", return_outcomes=False, **kw)
        val_r["y"] = y_val_sc
        vf_r = compute_decision_features(val_r)
        age_vr = (vf_r["age"] >= 1) & (vf_r["age"] <= 3)
        th_b2_r, b2_vs_r = tune_threshold_on_val(val_r, vf_r, "net_road_fee", lambda ft: (ft["age"] >= 1) & (ft["age"] <= 3))
        tgt_r = float(b2_vs_r["dispatch_rate"])
        m_act_r = find_val_matched_threshold(val_r, vf_r["net_road_fee"], age_vr & (vf_r["rep14"] >= 0.50), tgt_r)
        m_mg_r = find_val_matched_threshold(val_r, vf_r["net_road_fee_spoil"], age_vr & (vf_r["rep14"] >= 0.50) & (vf_r["dow8"] >= 0.35), tgt_r)
        m_rr_r = find_val_matched_threshold(val_r, rr_abstain_score(val_r, kappa_star), age_vr, tgt_r)
        m_rr15_r = find_val_matched_threshold(val_r, rr_abstain_score(val_r, 1.5), age_vr, tgt_r)
        m_safe_r = find_val_matched_threshold(val_r, score_safe_ev_sunk(val_r), age_vr, tgt_r)
        m_phys_r = find_val_matched_threshold(val_r, score_safe_ev_phys(val_r), age_vr, tgt_r)
        m_rtmin_r = find_val_matched_threshold(val_r, score_rt2f_min(val_r), age_vr, tgt_r)

        test_r = _recompute_scenario_decision_df(test, kw)
        test_r["y"] = y_sc
        sc_r = _score_all_14(test_r, th_b2_r, m_act_r, m_mg_r, kappa_star, m_rr_r, m_rr15_r, m_safe_r, m_phys_r, m_rtmin_r)
        for pname in core6:
            ch_r = pick_episode(test_r, *sc_r[pname])
            rr = _extended_metrics_v7(pname, ch_r, ot_sc)
            rr["scenario"] = sname
            rr["decision_mode"] = "rescored"
            torn_rows.append(rr)
    pd.DataFrame(torn_rows).to_csv(out_dir / "v7_tornado_171.csv", index=False)

    # 7. Settlement & Structural Robustness on 171 Markets (incl. hindsight_3d Mean disclosure & unconditional_171!)
    sr_rows = []
    y_hind, ot_hind = settle_candidates(test, how="hindsight", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    y_olag, ot_olag = settle_candidates(test, how="sequential", weather="none", div=1.5, disc=0.10, outside_option="lag", return_outcomes=True)
    for m_lbl, y_m, ot_m in (("sequential_base", y_test, test_ot), ("hindsight_3d", y_hind, ot_hind), ("outside_origin_lag", y_olag, ot_olag)):
        for pname in core6:
            ch = chosen[pname]
            r = _extended_metrics_v7(pname, ch, ot_m, y_override=y_m[ch["_i"].to_numpy()])
            r["robustness_slice"] = m_lbl
            sr_rows.append(r)

    # Paired bootstrap on hindsight_3d to verify B2's higher Mean transparently
    hb = bdf[["episode_id", "date", "origin_market_key"]].copy()
    for pname in ("B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
        ch = chosen[pname]
        hb[pname] = np.where(ch["eligible"].to_numpy(dtype=bool), y_hind[ch["_i"].to_numpy()], 0.0)
    hind_boot_safe = two_way_cluster_bootstrap_all_metrics(hb, "Safe_EV_Sunk_m0", "B2_age_matched", reps=2000, seed=20261117)
    hind_boot_rt = two_way_cluster_bootstrap_all_metrics(hb, "RT_2F_Min_m0", "B2_age_matched", reps=2000, seed=20261117)

    mc = coords[["State", "Market", "geocode_precision"]].drop_duplicates(["State", "Market"])
    exact_set = set(zip(mc.loc[mc["geocode_precision"] == "market_exact", "State"], mc.loc[mc["geocode_precision"] == "market_exact", "Market"]))
    test_exact_geo = np.array([((s, om) in exact_set) and ((s, dm) in exact_set) for s, om, dm in zip(test["State"], test["origin_market"], test["dest_market"])], dtype=bool)
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
        sc_sub = _score_all_14(sub_df, th_b2, m_act, m_mg, kappa_star, m_rr, m_rr15, m_safe, m_phys, m_rtmin, feats=sf)
        for pname in core6:
            ch_s = pick_episode(sub_df, *sc_sub[pname])
            r = _extended_metrics_v7(pname, ch_s, sub_ot)
            r["robustness_slice"] = sl_lbl
            sr_rows.append(r)

    # Unconditional origin panel on strict 2024-only 171 markets
    unc_171, unc_171_counts = build_lagged_candidates_from_frames(
        raw_df=raw_171,
        corridors_df=cor,
        fee_params_df=fees,
        clim_df=None,
        grade_explicit=False,
        min_origin_date="2025-06-01",
        max_origin_date="2026-04-08",
        include_unreported_origin_days=True,
    )
    unc_y_d0lag, unc_ot = settle_candidates(unc_171, how="sequential", weather="none", div=1.5, disc=0.10, outside_option="d0_or_lag", return_outcomes=True)
    unc_y_lag = settle_candidates(unc_171, how="sequential", weather="none", div=1.5, disc=0.10, outside_option="lag")
    unc_171["y"] = unc_y_d0lag
    uf = compute_decision_features(unc_171)
    sc_unc = _score_all_14(unc_171, th_b2, m_act, m_mg, kappa_star, m_rr, m_rr15, m_safe, m_phys, m_rtmin, feats=uf)
    for m_lbl, y_u in (("unconditional_orig_171_d0_or_lag", unc_y_d0lag), ("unconditional_orig_171_lag_outside", unc_y_lag)):
        for pname in core6:
            ch_u = pick_episode(unc_171, *sc_unc[pname])
            r = _extended_metrics_v7(pname, ch_u, unc_ot, y_override=y_u[ch_u["_i"].to_numpy()])
            r["robustness_slice"] = m_lbl
            sr_rows.append(r)
    pd.DataFrame(sr_rows).to_csv(out_dir / "v7_robustness_171.csv", index=False)

    # 8. Realized ERA5 Settlement on 171 Markets + Exact Break-Even + 171-Mkt Risk-Coverage & HP Apple + Precision R=5,000
    test_wx, wx_cov_171 = attach_realized_era5_settlement_weather(test, coords, wx)
    y_era5, ot_era5 = settle_realized_era5_sequential(test_wx, div=1.5, disc=0.10, open_yard_mar=False)
    y_era5_open, ot_era5_open = settle_realized_era5_sequential(test_wx, div=1.5, disc=0.10, open_yard_mar=True)

    chosen_20c_open: Dict[str, pd.DataFrame] = {}
    chosen_era5: Dict[str, pd.DataFrame] = {}
    chosen_era5_open: Dict[str, pd.DataFrame] = {}
    for pname in ("B1_lagged_screen", "B2_age_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Sunk_matched", "Safe_EV_Phys_m0", "RT_2F_Min_m0"):
        ch = chosen[pname]
        el = ch["eligible"].to_numpy(dtype=bool)
        idx_c = ch["_i"].to_numpy()
        c_open = ch.copy(); c_open["y"] = np.where(el, y_mar_open[idx_c], 0.0); chosen_20c_open[pname] = c_open
        c_e = ch.copy(); c_e["y"] = np.where(el, y_era5[idx_c], 0.0); chosen_era5[pname] = c_e
        c_eo = ch.copy(); c_eo["y"] = np.where(el, y_era5_open[idx_c], 0.0); chosen_era5_open[pname] = c_eo

    be_171 = (
        _compute_breakeven_rows("strict2024_171_20C_closed", chosen, test_ot, chosen_20c_open)
        + _compute_breakeven_rows("strict2024_171_ERA5_closed", chosen_era5, ot_era5, chosen_era5_open)
    )

    # Pure 171-market risk-coverage curves with R=1,000 CIs (for Fig 1 without 178-market mixing!)
    rc_rows = []
    rc_specs = [
        ("B2_age_matched", tf["net_road_fee"], age_test13, list(range(0, 601, 50))),
        ("MG_T1_T2_ML_stripped", tf["net_road_fee_spoil"], age_test13 & (tf["rep14"] >= 0.50) & (tf["dow8"] >= 0.35), list(range(0, 601, 50))),
        ("RR_Abstain", rr_abstain_score(test, kappa_star), age_test13, [-200, -100, 0, 50, 100, 150, 200, 300, 400, 500]),
        ("Safe_EV_Sunk", score_safe_ev_sunk(test), age_test13, [-200, -100, -50, 0, 50, 100, 150, 200, 300, 400]),
        ("RT_2F_Min", score_rt2f_min(test), age_test13, [-200, -100, 0, 50, 100, 150, 200, 300, 400]),
    ]
    for fam, s_arr, g_arr, knobs in rc_specs:
        for kn in knobs:
            ch_rc = pick_episode(test, s_arr, g_arr & (s_arr > float(kn)))
            rec_rc = _extended_metrics_v7(fam, ch_rc, test_ot)
            cis = ci95_single_metric(ch_rc, "y", reps=1000, seed=20261117 + abs(int(kn)))
            rec_rc["knob"] = kn
            rec_rc["family"] = fam
            rec_rc["ep_loss_ci95_low"] = round(cis["ep_loss_rate"][0], 4)
            rec_rc["ep_loss_ci95_high"] = round(cis["ep_loss_rate"][1], 4)
            rec_rc["es10_ci95_low"] = round(cis["es10"][0], 2)
            rec_rc["es10_ci95_high"] = round(cis["es10"][1], 2)
            rc_rows.append(rec_rc)
    pd.DataFrame(rc_rows).to_csv(out_dir / "v7_risk_coverage_171.csv", index=False)

    # Pure 171-calibrated HP Graded Apple benchmark (fixing val_178 threshold contamination in Fig 4)
    hp = pd.read_parquet(out_dir / "lagged_hp_apple_candidates.parquet")
    hp["date"] = pd.to_datetime(hp["date"])
    hp_y, hp_ot = settle_candidates(hp, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    hp["y"] = hp_y
    hp_rows = []
    hp_chosen_all: Dict[str, pd.DataFrame] = {}
    for w_lbl, sub_hp in (("ALL_2025_2026", hp), ("POST_JUNE_2026", hp[hp["date"] >= pd.Timestamp("2026-06-01")].reset_index(drop=True))):
        hf = compute_decision_features(sub_hp)
        sc_hp = _score_all_14(sub_hp, th_b2, m_act, m_mg, kappa_star, m_rr, m_rr15, m_safe, m_phys, m_rtmin, feats=hf)
        sub_ot = hp_ot[sub_hp.index] if w_lbl == "ALL_2025_2026" else hp_ot[hp["date"] >= pd.Timestamp("2026-06-01")]
        for pname in ("B1_lagged_screen", "B2_age_matched", "MG_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "Safe_EV_Sunk_matched", "RT_2F_Min_m0"):
            ch_hp = pick_episode(sub_hp, *sc_hp[pname])
            if w_lbl == "ALL_2025_2026":
                hp_chosen_all[pname] = ch_hp
            rec = _extended_metrics_v7(pname, ch_hp, sub_ot)
            rec["window"] = w_lbl
            hp_rows.append(rec)
    pd.DataFrame(hp_rows).to_csv(out_dir / "v7_hp_apple_171.csv", index=False)
    hp_bdf = hp_chosen_all["B2_age_matched"][["episode_id", "date", "origin_market_key"]].copy()
    for p in ("B2_age_matched", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"):
        hp_bdf[p] = hp_chosen_all[p]["y"].to_numpy(dtype=np.float64)
        hp_bdf[f"{p}_disp"] = hp_chosen_all[p]["eligible"].to_numpy(dtype=bool)
    hp_boot = two_way_cluster_bootstrap_extended(
        hp_bdf, "Safe_EV_Sunk_m0", "B2_age_matched",
        disp_col_a="Safe_EV_Sunk_m0_disp", disp_col_b="B2_age_matched_disp",
        reps=2000, seed=20261117,
    )

    # Price-level decomposition: 178-mkt 20C vs 171-mkt 20C vs 171-mkt ERA5 (computing 171 directly, reading/computing 178)
    main_idx_map = {r["policy"]: r["mean"] for r in main_rows}
    if (out_dir / "v6_upgrades.csv").exists():
        v6_up = pd.read_csv(out_dir / "v6_upgrades.csv")
    else:
        v6_up = None
    decomp_rows = []
    for pname in ("B1_lagged_screen", "B2_age_matched", "Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "RT_2F_Min_m0"):
        m171_20 = float(main_idx_map[pname])
        m171_er = round(float(chosen_era5[pname]["y"].mean()), 2)
        if v6_up is not None:
            m178_20 = float(v6_up[(v6_up["panel"] == "full_178_20C_closed") & (v6_up["policy"] == pname)]["mean"].iloc[0])
            m178_er = float(v6_up[(v6_up["panel"] == "full_178_ERA5_closed") & (v6_up["policy"] == pname)]["mean"].iloc[0])
        else:
            m178_20, m178_er = np.nan, np.nan
        decomp_rows.append({
            "policy": pname,
            "mean_178_20C": m178_20,
            "mean_171_20C": m171_20,
            "mean_178_ERA5": m178_er,
            "mean_171_ERA5": m171_er,
            "shift_market_178_to_171_20C": round(m171_20 - m178_20, 2) if np.isfinite(m178_20) else np.nan,
            "shift_weather_20C_to_ERA5_178": round(m178_er - m178_20, 2) if np.isfinite(m178_er) else np.nan,
            "shift_weather_20C_to_ERA5_171": round(m171_er - m171_20, 2),
            "shift_total_178_20C_to_171_ERA5": round(m171_er - m178_20, 2) if np.isfinite(m178_20) else np.nan,
        })
    pd.DataFrame(decomp_rows).to_csv(out_dir / "v7_era5_and_reconcile.csv", index=False)

    # Post-hoc Monte Carlo precision & temporal block-length check (R = 5,000, strictly separated from PREREG_A18 R=2,000)
    prec_rows: List[dict] = []
    prec_contrasts = [
        ("H_A18_1", "Safe_EV_Sunk_m0", "B2_age_matched", "es10"),
        ("H_A18_2", "Safe_EV_Sunk_matched", "RR_Abstain_matched", "es10"),
        ("H_A18_3", "Safe_EV_Sunk_m0", "B2_age_matched", "ep_loss_rate"),
        ("H_A18_4", "RT_2F_Min_m0", "B2_age_matched", "mean"),
        ("POSTHOC_1", "Safe_EV_Phys_m0", "B2_age_matched", "es10"),
        ("POSTHOC_2", "Safe_EV_Sunk_m0", "B2_age_matched", "mean"),
    ]
    for sch_lbl, wk_len, ch_src in (
        ("171_20C_origin_x_1week", 1, chosen),
        ("171_20C_origin_x_2week", 2, chosen),
        ("171_20C_origin_x_4week", 4, chosen),
        ("171_ERA5_origin_x_2week", 2, chosen_era5),
    ):
        pdf = pd.DataFrame({
            "date": ch_src["B2_age_matched"]["date"].to_numpy(),
            "origin_market_key": ch_src["B2_age_matched"]["origin_market_key"].to_numpy(),
        })
        for p in ("B2_age_matched", "RR_Abstain_matched", "Safe_EV_Sunk_m0", "Safe_EV_Sunk_matched", "Safe_EV_Phys_m0", "RT_2F_Min_m0"):
            pdf[p] = ch_src[p]["y"].to_numpy(dtype=np.float64)
        cache_p: Dict[Tuple[str, str], dict] = {}
        fam_p: List[dict] = []
        for hid, pa, pb, metric in prec_contrasts:
            if (pa, pb) not in cache_p:
                cache_p[(pa, pb)] = two_way_cluster_bootstrap_all_metrics(pdf, pa, pb, mandi_col="origin_market_key", week_block_len=wk_len, reps=5000, seed=20261123)
            md = cache_p[(pa, pb)][metric]
            raw_p = float(md["p_value_two_sided"])
            fam_p.append({
                "scheme": sch_lbl,
                "week_block_len": wk_len,
                "hypothesis_id": hid,
                "policy_a": pa,
                "policy_b": pb,
                "metric": metric,
                "estimate": round(md["estimate"], 4),
                "ci95_low": round(md["ci95_low"], 4),
                "ci95_high": round(md["ci95_high"], 4),
                "p_value_two_sided": round(raw_p, 6),
                "_raw_p": raw_p,
                "n": int(md["n"]),
                "n_clusters": int(md["n_clusters"]),
                "n_blocks": int(md["n_blocks"]),
                "reps": 5000,
            })
        ph_all = holm_bonferroni([r["_raw_p"] for r in fam_p])
        for r, phv in zip(fam_p, ph_all):
            r["p_holm_2s_6tests"] = round(float(phv), 6)
            r.pop("_raw_p", None)
        prec_rows.extend(fam_p)
    pd.DataFrame(prec_rows).to_csv(out_dir / "v7_bootstrap_precision_5000.csv", index=False)

    # =========================================================================
    # PART B: CLEAN 166-MKT 2018-2023 OUT-OF-PERIOD HISTORICAL BACKTEST (Zero Lookahead)
    # =========================================================================
    dec_raw = pd.read_parquet(ROOT / "data/raw/agmarknet_6state_decade_2017_2026.parquet")
    dec_raw["Arrival_Date"] = pd.to_datetime(dec_raw["Arrival_Date"])
    dec_17_23 = dec_raw[dec_raw["Arrival_Date"] <= pd.Timestamp("2023-12-31")].copy().reset_index(drop=True)

    # Strict non-lookahead intersection 171 (2024-only) ∩ 173 (decade geocoded) = 166 markets
    raw_166_mask = [(st, mk) in mkt_set_2024 for st, mk in zip(dec_17_23["State"].astype(str), dec_17_23["Market"].astype(str))]
    dec_17_23_166 = dec_17_23.loc[raw_166_mask].copy().reset_index(drop=True)
    n_markets_166 = int(dec_17_23_166[["State", "Market"]].drop_duplicates().shape[0])

    # 2017-active markets (>= 50 days in 2017): legacy (120) vs clean non-lookahead intersection with 171 (115)
    r17 = dec_17_23[dec_17_23["Arrival_Date"].dt.year == 2017]
    d17 = r17.groupby(["State", "Market"])["Arrival_Date"].nunique().reset_index(name="n17")
    mkts_2017_all = set(zip(d17.loc[d17["n17"] >= 50, "State"].astype(str), d17.loc[d17["n17"] >= 50, "Market"].astype(str)))
    mkts_2017_clean = mkts_2017_all & mkt_set_2024

    # Primary CLEAN 166-market 2018-2023 lagged candidates (2017 strictly burn-in)
    dec_df, dec_counts = build_lagged_candidates_from_frames(
        raw_df=dec_17_23_166,
        corridors_df=cor,
        fee_params_df=fees,
        clim_df=None,
        grade_explicit=False,
        min_origin_date="2018-01-01",
        max_origin_date="2023-12-26",
    )
    dec_df["date"] = pd.to_datetime(dec_df["date"])
    dec_y, dec_ot = settle_candidates(dec_df, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    dec_y_open, dec_ot_open = _open_mar_20c(dec_df, dec_y, dec_ot)
    dec_df["y"] = dec_y
    dec_df["_ot"] = dec_ot
    df_f = compute_decision_features(dec_df)
    dec_age13 = (df_f["age"] >= 1) & (df_f["age"] <= 3)

    # Clean 115-market 2017-active subset (zero 2024-2026 lookahead)
    raw_115_mask = [(st, mk) in mkts_2017_clean for st, mk in zip(dec_17_23_166["State"].astype(str), dec_17_23_166["Market"].astype(str))]
    dec_115_df, dec_115_counts = build_lagged_candidates_from_frames(
        raw_df=dec_17_23_166.loc[raw_115_mask].copy().reset_index(drop=True),
        corridors_df=cor,
        fee_params_df=fees,
        clim_df=None,
        grade_explicit=False,
        min_origin_date="2018-01-01",
        max_origin_date="2023-12-26",
    )
    dec_115_df["date"] = pd.to_datetime(dec_115_df["date"])
    dec_115_y, dec_115_ot = settle_candidates(dec_115_df, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    dec_115_df["y"] = dec_115_y

    # Legacy 173-market superset (solely to quantify the 7-market post-2024 lookahead contamination)
    dec_173_df, dec_173_counts = build_lagged_candidates_from_frames(
        raw_df=dec_17_23,
        corridors_df=cor,
        fee_params_df=fees,
        clim_df=None,
        grade_explicit=False,
        min_origin_date="2018-01-01",
        max_origin_date="2023-12-26",
    )
    dec_173_df["date"] = pd.to_datetime(dec_173_df["date"])
    dec_173_y, dec_173_ot = settle_candidates(dec_173_df, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    dec_173_y_open, dec_173_ot_open = _open_mar_20c(dec_173_df, dec_173_y, dec_173_ot)
    dec_173_df["y"] = dec_173_y
    f173 = compute_decision_features(dec_173_df)
    a173 = (f173["age"] >= 1) & (f173["age"] <= 3)

    # Frozen zero-parameter rules + B2 fixed at val_171 threshold (200.0) + equal-dispatch B2_eq_SafeM0
    sc_dec_safe = score_safe_ev_sunk(dec_df)
    ch_dec_safe_tmp = pick_episode(dec_df, sc_dec_safe, dec_age13 & (sc_dec_safe > 0.0))
    dec_safe_disp = float(ch_dec_safe_tmp["eligible"].mean())
    th_dec_b2_eq = find_val_matched_threshold(dec_df, df_f["net_road_fee"], dec_age13, dec_safe_disp)

    dec_specs = {
        "B1_lagged_screen": (df_f["lag_spread"], np.ones(len(dec_df), dtype=bool)),
        "B2_age_matched": (df_f["net_road_fee"], dec_age13 & (df_f["net_road_fee"] > th_b2)),
        "B2_eq_SafeM0": (df_f["net_road_fee"], dec_age13 & (df_f["net_road_fee"] > th_dec_b2_eq)),
        "Safe_EV_Sunk_m0": (sc_dec_safe, dec_age13 & (sc_dec_safe > 0.0)),
        "Safe_EV_Phys_m0": (score_safe_ev_phys(dec_df), dec_age13 & (score_safe_ev_phys(dec_df) > 0.0)),
        "RT_2F_Min_m0": (score_rt2f_min(dec_df), dec_age13 & (score_rt2f_min(dec_df) > 0.0)),
        "RT_2F_Dow_m0": (score_rt2f_dow(dec_df), dec_age13 & (score_rt2f_dow(dec_df) > 0.0)),
    }
    dec_chosen: Dict[str, pd.DataFrame] = {}
    dec_chosen_open: Dict[str, pd.DataFrame] = {}
    dec_rows = []
    for pname, (sc, el) in dec_specs.items():
        ch = pick_episode(dec_df, sc, el)
        dec_chosen[pname] = ch
        r_cl = _extended_metrics_v7(pname, ch, dec_ot)
        r_cl["panel"] = "decade_2018_2023_166clean_closed"
        dec_rows.append(r_cl)

        c_op = ch.copy()
        c_op["y"] = np.where(ch["eligible"].to_numpy(dtype=bool), dec_y_open[ch["_i"].to_numpy()], 0.0)
        dec_chosen_open[pname] = c_op
        r_op = _extended_metrics_v7(pname, ch, dec_ot_open, y_override=dec_y_open[ch["_i"].to_numpy()])
        r_op["panel"] = "decade_2018_2023_166clean_open_lag"
        dec_rows.append(r_op)

    # Clean 115-market 2017-active closed
    f115 = compute_decision_features(dec_115_df)
    a115 = (f115["age"] >= 1) & (f115["age"] <= 3)
    for pname, (sc, el) in {
        "B1_lagged_screen": (f115["lag_spread"], np.ones(len(dec_115_df), dtype=bool)),
        "B2_age_matched": (f115["net_road_fee"], a115 & (f115["net_road_fee"] > th_b2)),
        "Safe_EV_Sunk_m0": (score_safe_ev_sunk(dec_115_df), a115 & (score_safe_ev_sunk(dec_115_df) > 0.0)),
        "Safe_EV_Phys_m0": (score_safe_ev_phys(dec_115_df), a115 & (score_safe_ev_phys(dec_115_df) > 0.0)),
        "RT_2F_Min_m0": (score_rt2f_min(dec_115_df), a115 & (score_rt2f_min(dec_115_df) > 0.0)),
    }.items():
        ch115 = pick_episode(dec_115_df, sc, el)
        r115 = _extended_metrics_v7(pname, ch115, dec_115_ot)
        r115["panel"] = "decade_2018_2023_115clean2017_closed"
        dec_rows.append(r115)

    # Legacy 173-market reconciliation rows
    dec_173_chosen: Dict[str, pd.DataFrame] = {}
    dec_173_open: Dict[str, pd.DataFrame] = {}
    for pname, (sc, el) in {
        "B1_lagged_screen": (f173["lag_spread"], np.ones(len(dec_173_df), dtype=bool)),
        "B2_age_matched": (f173["net_road_fee"], a173 & (f173["net_road_fee"] > th_b2)),
        "Safe_EV_Sunk_m0": (score_safe_ev_sunk(dec_173_df), a173 & (score_safe_ev_sunk(dec_173_df) > 0.0)),
        "Safe_EV_Phys_m0": (score_safe_ev_phys(dec_173_df), a173 & (score_safe_ev_phys(dec_173_df) > 0.0)),
        "RT_2F_Min_m0": (score_rt2f_min(dec_173_df), a173 & (score_rt2f_min(dec_173_df) > 0.0)),
    }.items():
        ch173 = pick_episode(dec_173_df, sc, el)
        dec_173_chosen[pname] = ch173
        cop173 = ch173.copy()
        cop173["y"] = np.where(ch173["eligible"].to_numpy(dtype=bool), dec_173_y_open[ch173["_i"].to_numpy()], 0.0)
        dec_173_open[pname] = cop173
        r173 = _extended_metrics_v7(pname, ch173, dec_173_ot)
        r173["panel"] = "decade_2018_2023_173legacy_closed"
        dec_rows.append(r173)
    pd.DataFrame(dec_rows).to_csv(out_dir / "v7_decade_2018_2023.csv", index=False)

    # Exact silent-market break-even on 171 + clean 166-mkt decade (plus 173 legacy reconcile)
    be_dec_166 = _compute_breakeven_rows("decade_2018_2023_166clean_closed", dec_chosen, dec_ot, dec_chosen_open)
    be_dec_173 = _compute_breakeven_rows("decade_2018_2023_173legacy_closed", dec_173_chosen, dec_173_ot, dec_173_open)
    pd.DataFrame(be_171 + be_dec_166 + be_dec_173).to_csv(out_dir / "v7_breakeven_171.csv", index=False)

    # Clean 166-mkt Year-by-Year 2018..2023 metrics + R=2,000 paired bootstrap (documenting 2020 & 2023 NS Mean!)
    yr_rows = []
    yr_boot_rows = []
    base_dates = pd.to_datetime(dec_chosen["B2_age_matched"]["date"])
    for yr in (2018, 2019, 2020, 2021, 2022, 2023):
        ymask = (base_dates.dt.year == yr).to_numpy()
        yr_bdf = dec_chosen["B2_age_matched"].loc[ymask, ["episode_id", "date", "origin_market_key"]].copy().reset_index(drop=True)
        for pname in ("B1_lagged_screen", "B2_age_matched", "B2_eq_SafeM0", "Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "RT_2F_Min_m0"):
            ch_y = dec_chosen[pname].loc[ymask].reset_index(drop=True)
            ry = _extended_metrics_v7(pname, ch_y, dec_ot)
            ry["year"] = yr
            yr_rows.append(ry)
            if pname in ("B2_age_matched", "B2_eq_SafeM0", "Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "RT_2F_Min_m0"):
                yr_bdf[pname] = ch_y["y"].to_numpy(dtype=np.float64)
                yr_bdf[f"{pname}_disp"] = ch_y["eligible"].to_numpy(dtype=bool)
        for pa, pb in (("Safe_EV_Sunk_m0", "B2_age_matched"), ("Safe_EV_Sunk_m0", "B2_eq_SafeM0"), ("RT_2F_Min_m0", "B2_age_matched")):
            yres = two_way_cluster_bootstrap_extended(
                yr_bdf, pa, pb,
                disp_col_a=f"{pa}_disp", disp_col_b=f"{pb}_disp",
                mandi_col="origin_market_key", week_block_len=2, reps=2000, seed=20261117,
            )
            for met in ("mean", "ep_loss_rate", "es10", "cond_es10"):
                md = yres[met]
                yr_boot_rows.append({
                    "year": yr,
                    "policy_a": pa,
                    "policy_b": pb,
                    "metric": met,
                    "estimate": round(md["estimate"], 4),
                    "ci95_low": round(md["ci95_low"], 4),
                    "ci95_high": round(md["ci95_high"], 4),
                    "basic_ci95_low": round(md["basic_ci95_low"], 4),
                    "basic_ci95_high": round(md["basic_ci95_high"], 4),
                    "p_value_two_sided": round(md["p_value_two_sided"], 6),
                    "p_value_null_cent_2s": round(md["p_value_null_cent_2s"], 6),
                    "n": int(md["n"]),
                    "n_clusters": int(md["n_clusters"]),
                    "n_blocks": int(md["n_blocks"]),
                    "reps": 2000,
                })
    pd.DataFrame(yr_rows).to_csv(out_dir / "v7_decade_by_year.csv", index=False)
    pd.DataFrame(yr_boot_rows).to_csv(out_dir / "v7_decade_by_year_boot_2000.csv", index=False)

    # R = 2,000 paired two-way cluster bootstrap on pooled CLEAN 166-mkt 2018-2023 (origin_x_2week & b2dest_or_origin_x_2week)
    dec_bdf = dec_chosen["B2_age_matched"][["episode_id", "date", "origin_market_key"]].copy()
    dec_bdf["b2dest_key"] = _dest_or_origin_key(dec_chosen["B2_age_matched"])
    for pname in ("B2_age_matched", "B2_eq_SafeM0", "Safe_EV_Sunk_m0", "Safe_EV_Phys_m0", "RT_2F_Min_m0"):
        dec_bdf[pname] = dec_chosen[pname]["y"].to_numpy(dtype=np.float64)
        dec_bdf[f"{pname}_disp"] = dec_chosen[pname]["eligible"].to_numpy(dtype=bool)
    dec_boot_rows = []
    for sch_lbl, mcol in (("decade_origin_x_2week", "origin_market_key"), ("decade_b2dest_or_origin_x_2week", "b2dest_key")):
        for pa, pb in (
            ("Safe_EV_Sunk_m0", "B2_age_matched"),
            ("Safe_EV_Sunk_m0", "B2_eq_SafeM0"),
            ("Safe_EV_Phys_m0", "B2_age_matched"),
            ("RT_2F_Min_m0", "B2_age_matched"),
        ):
            res = two_way_cluster_bootstrap_extended(
                dec_bdf, pa, pb,
                disp_col_a=f"{pa}_disp", disp_col_b=f"{pb}_disp",
                mandi_col=mcol, week_block_len=2, reps=2000, seed=20261117,
            )
            for metric in ("mean", "ep_loss_rate", "es10", "cond_es10"):
                md = res[metric]
                dec_boot_rows.append({
                    "cluster": sch_lbl,
                    "policy_a": pa,
                    "policy_b": pb,
                    "metric": metric,
                    "estimate": round(md["estimate"], 4),
                    "ci95_low": round(md["ci95_low"], 4),
                    "ci95_high": round(md["ci95_high"], 4),
                    "p_value_two_sided": round(md["p_value_two_sided"], 6),
                    "n": int(md["n"]),
                    "n_clusters": int(md["n_clusters"]),
                    "n_blocks": int(md["n_blocks"]),
                    "reps": 2000,
                })
    pd.DataFrame(dec_boot_rows).to_csv(out_dir / "v7_decade_boot_2000.csv", index=False)

    # Forensic counts on primary 171-market panel
    orig_eps_171 = test.groupby("episode_id").first()
    unc_eps_171 = int(unc_171["episode_id"].nunique())
    unc_unrep_171 = int(unc_171.groupby("episode_id")["settle_local_price_d0"].first().isna().sum())
    ch_s171 = chosen["Safe_EV_Sunk_m0"]
    s171_disp_idx = ch_s171.loc[ch_s171["eligible"], "_i"].to_numpy()
    s171_cnt28_fb = int((test.loc[s171_disp_idx, "dest_obs_cnt_28d"] < 2).sum())
    exact_all5_171 = int(pd.Series(test_exact_geo).groupby(test["episode_id"]).all().sum())

    v7_meta = {
        "primary_panel": "strict2024_171_markets",
        "exploratory_2025_2026": True,
        "out_of_period_2018_2023_zero_retuning": True,
        "strict_2024_markets_count": 171,
        "strict_2024_markets_by_state": mkts_2024.groupby("State").size().to_dict(),
        "counts_171": counts_171,
        "val_171_b2_threshold": round(float(th_b2), 4),
        "val_171_b2_dispatch_rate": round(target_val_disp, 4),
        "val_171_matched_thresholds": {
            "B_simple_activity_matched": round(float(m_act), 4),
            "MG_matched": round(float(m_mg), 4),
            "RR_Abstain_matched": round(float(m_rr), 4),
            "RR_Abstain_phys15_matched": round(float(m_rr15), 4),
            "Safe_EV_Sunk_matched": round(float(m_safe), 4),
            "Safe_EV_Phys_matched": round(float(m_phys), 4),
            "RT_2F_Min_matched": round(float(m_rtmin), 4),
            "MG_val_es10_grid_best": {"rep28": rcut_b, "dow8": dcut_b, "th": round(float(th_mg_es10), 4)},
        },
        "forensic_counts_171": {
            "test_episodes": int(test["episode_id"].nunique()),
            "val_episodes": int(val["episode_id"].nunique()),
            "test_exact_geocode_row_pct": round(100.0 * float(test_exact_geo.mean()), 2),
            "test_centroid_approx_row_pct": round(100.0 * float(1.0 - test_exact_geo.mean()), 2),
            "test_all5_exact_geocode_episodes": exact_all5_171,
            "test_conflicting_dup_episodes": int(test["episode_id"].nunique() - test.loc[ep_no_conf, "episode_id"].nunique()),
            "test_origin_lag_4_7_episodes": int((orig_eps_171["origin_lag_age"] > 3).sum()),
            "safe_ev_sunk_m0_cnt28_fallback_dispatched": s171_cnt28_fb,
            "safe_ev_sunk_m0_cnt28_fallback_pct": round(100.0 * s171_cnt28_fb / max(1, len(s171_disp_idx)), 2),
            "unconditional_orig_171_test_episodes": unc_eps_171,
            "unconditional_orig_171_missing_d0_episodes": unc_unrep_171,
            "era5_settlement_coverage_171": wx_cov_171,
        },
        "hindsight_3d_boot_171": {
            "Safe_EV_Sunk_m0_vs_B2": {m: {k: round(float(v), 4) for k, v in md.items()} for m, md in hind_boot_safe.items()},
            "RT_2F_Min_m0_vs_B2": {m: {k: round(float(v), 4) for k, v in md.items()} for m, md in hind_boot_rt.items()},
        },
        "hp_apple_171_boot": {
            m: {k: round(float(v), 4) for k, v in md.items()} for m, md in hp_boot.items()
        },
        "decade_2018_2023": {
            "clean_166_markets_count": n_markets_166,
            "counts_166clean": dec_counts,
            "markets_2017_clean_ge50d": len(mkts_2017_clean),
            "counts_115clean2017": dec_115_counts,
            "n_episodes_166clean": int(dec_df["episode_id"].nunique()),
            "n_episodes_115clean2017": int(dec_115_df["episode_id"].nunique()),
            "b2_eq_SafeM0_threshold_166": round(float(th_dec_b2_eq), 4),
            "legacy_173_counts": dec_173_counts,
            "legacy_173_n_episodes": int(dec_173_df["episode_id"].nunique()),
            "legacy_markets_2017_ge50d": len(mkts_2017_all),
        },
    }
    (out_dir / "v7_summary.json").write_text(json.dumps(v7_meta, indent=2, default=float))

    print("=== V7 PRIMARY 171-MARKET MAIN TABLE (N = 57,634) ===")
    print(pd.DataFrame(main_rows)[["policy", "free_params", "dispatch_rate", "mean", "ep_loss_rate", "es10", "cond_es10", "loss_given_loss"]].to_string(index=False))
    print("\n=== V7 LOCKED PREREG_A18 4-TEST FAMILY AT R = 2,000 (171 MARKETS) ===")
    b2k = pd.DataFrame(boot2k_rows)
    print(b2k[b2k["registered_prereg_a18"]][["hypothesis_id", "cluster", "metric", "estimate", "ci95_low", "ci95_high", "p_value_two_sided", "p_holm_2s_prereg4", "n_clusters"]].to_string(index=False))
    print("\n=== V7 MISSING REGIME TESTS (171 MARKETS, R = 2,000) ===")
    mt = pd.DataFrame(miss_test_rows)
    print(mt[mt["policy_a"] == "Safe_EV_Sunk_m0"][["missing_scenario", "metric", "estimate", "ci95_low", "ci95_high", "p_value_two_sided", "p_holm_2s_scen9"]].to_string(index=False))
    print("\n=== V7 CLEAN 166-MKT 2018-2023 HISTORICAL OUT-OF-PERIOD BACKTEST ===")
    print(pd.DataFrame(dec_rows)[["panel", "policy", "n", "dispatch_rate", "mean", "ep_loss_rate", "es10", "cond_es10"]].to_string(index=False))
    print("\n=== V7 CLEAN 166-MKT 2018-2023 YEAR-BY-YEAR (Safe_EV_Sunk_m0 vs B2 & B2_eq & RT_2F) ===")
    yd = pd.DataFrame(yr_rows)
    print(yd[yd["policy"].isin(["B2_age_matched", "B2_eq_SafeM0", "Safe_EV_Sunk_m0", "RT_2F_Min_m0"])][["year", "policy", "n", "dispatch_rate", "mean", "ep_loss_rate", "es10", "cond_es10"]].to_string(index=False))
    print("\n=== V7 2018-2023 YEARLY BOOTSTRAP MEAN P-VALUES (Safe_EV_Sunk_m0 vs B2_age_matched) ===")
    yb = pd.DataFrame(yr_boot_rows)
    print(yb[(yb["policy_a"] == "Safe_EV_Sunk_m0") & (yb["policy_b"] == "B2_age_matched") & (yb["metric"].isin(["mean", "es10", "cond_es10"]))][["year", "metric", "estimate", "ci95_low", "ci95_high", "p_value_two_sided", "n_clusters", "n_blocks"]].to_string(index=False))
    print("\n=== V7 PRICE-LEVEL DECOMPOSITION (178->171 vs 20C->ERA5) ===")
    print(pd.DataFrame(decomp_rows).to_string(index=False))


if __name__ == "__main__":
    run()
