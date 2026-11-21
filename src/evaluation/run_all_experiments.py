"""Step 4: Exhaustive Holdout Experiments, Statistical Bootstrap, & Ablations (MandiGuard).

Strict Temporal Protocol:
  - Loads pre-trained 2024 CausalArrivalForecaster (`data/interim/forecaster_2024.pkl`)
    and validation-frozen `safety_margin_inr` (`configs/frozen_calibration.json`).
  - Streams conformal quantile updates strictly causally (arrival_date <= t) across 2025-01-01..2026-04-08,
    and evaluates CONFIRMATORY hypotheses ONLY on untouched Holdout_2025_2026 (`2025-06-01`..`2026-04-08`).
  - Also evaluates Grade-Explicit HP Apple holdout (`2026-06-01`..`2026-08-27`).
  - Writes results/exp1_*.csv..exp8_*.json, confirmatory_holm_summary.csv, EXPERIMENT_REGISTRY.csv,
    sample traces JSONL, and FINDINGS.md.
"""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.baselines.dispatch_baselines import (
    eval_b1_naive_screen_greedy,
    eval_b2_fresh_road_greedy,
    eval_b3_ml_point_dispatch,
    eval_b4_upfront_all_tools,
    eval_b5_multi_agent_coordinator,
    eval_b6_heuristic_bucket_router,
)
from src.evaluation.bootstrap import holm_bonferroni, two_way_mandi_week_bootstrap
from src.evaluation.payoff_model import PayoffParams, compute_realized_dispatch_outcome
from src.evaluation.tail_risk import lower_decile_mean
from src.utils.leakage import load_config

LOT_SIZE_QTL = 30.0  # Grounded in MoSPI NSO NSS 77th Round Report No. 587 (Potato 29.33 qtl, Onion 38.73 qtl)
AVG_MONTHLY_CROP_INCOME_INR = 3798.0  # NSO NSS 77th Round Table 6


def _summarize_policy(name: str, pol_df: pd.DataFrame) -> Dict[str, object]:
    disp = pol_df["is_dispatch"].to_numpy(dtype=bool)
    dnet = pol_df["delta_net_inr"].to_numpy(dtype=np.float64)
    open_d0 = pol_df["open_d0_delta_net_inr"].to_numpy(dtype=np.float64)
    ep_phantom = pol_df["is_phantom_loss"].to_numpy(dtype=bool)
    trap = pol_df["is_closed_trap"].to_numpy(dtype=bool)
    calls = pol_df["tool_calls_total"].to_numpy(dtype=np.float64)

    n_ep = len(pol_df)
    n_disp = int(disp.sum())
    cond_plr = float(ep_phantom[disp].mean() * 100.0) if n_disp > 0 else 0.0
    cond_trap = float(trap[disp].mean() * 100.0) if n_disp > 0 else 0.0
    cond_dnet = float(dnet[disp].mean()) if n_disp > 0 else 0.0
    # Open-Day-0 conditional on open-d0 dispatches (or SELL_LOCAL=0 for abstainers)
    valid_od0 = open_d0[np.isfinite(open_d0)]
    mean_od0 = float(valid_od0.mean()) if len(valid_od0) > 0 else np.nan

    return {
        "policy": name,
        "n_episodes": n_ep,
        "dispatch_rate_pct": round(100.0 * n_disp / max(1, n_ep), 2),
        "mean_delta_net_inr": round(float(dnet.mean()), 2),
        "cond_dispatched_delta_net_inr": round(cond_dnet, 2),
        "open_d0_mean_delta_net_inr": round(mean_od0, 2),
        "ep_phantom_loss_pct": round(float(ep_phantom.mean() * 100.0), 2),
        "cond_phantom_loss_rate_pct": round(cond_plr, 2),
        "cond_closed_or_trap_rate_pct": round(cond_trap, 2),
        "cvar_10_inr": round(lower_decile_mean(dnet), 2),
        "avg_tool_calls": round(float(calls.mean()), 2),
        "lot_30qtl_gain_inr": round(float(dnet.mean()) * LOT_SIZE_QTL, 1),
    }


def _recompute_outcomes_with_params(cand_df: pd.DataFrame, params: PayoffParams) -> pd.DataFrame:
    """Recompute ground-truth realized payoffs across an alternative PayoffParams setting cleanly."""
    df = cand_df.copy()
    n = len(df)
    new_dnet = np.empty(n, dtype=np.float64)
    new_od0 = np.empty(n, dtype=np.float64)
    new_trap = np.empty(n, dtype=bool)
    new_drop = np.empty(n, dtype=bool)

    states = df["State"].to_numpy()
    comms = df["Commodity"].to_numpy()
    lps = df["local_price"].to_numpy(dtype=np.float64)
    rkms = df["road_km"].to_numpy(dtype=np.float64)
    thrs = df["truck_hours"].to_numpy(dtype=np.float64)
    sds = df["same_district"].to_numpy(dtype=bool)
    lags = df["tau_days"].to_numpy(dtype=int)
    pm0 = df["dest_modal_d0"].to_numpy(dtype=np.float64)
    pmn0 = df["dest_min_d0"].to_numpy(dtype=np.float64)
    pm1 = df["dest_modal_d1"].to_numpy(dtype=np.float64)
    pmn1 = df["dest_min_d1"].to_numpy(dtype=np.float64)
    pm2 = df["dest_modal_d2"].to_numpy(dtype=np.float64)
    pmn2 = df["dest_min_d2"].to_numpy(dtype=np.float64)
    amin0 = df["dest_any_var_min_d0"].to_numpy(dtype=np.float64)
    aopen0 = df["dest_any_open_d0"].to_numpy(dtype=bool)
    tmax = df["route_era5_tmax"].to_numpy(dtype=np.float64)
    rh = df["route_era5_rh"].to_numpy(dtype=np.float64)
    rain = df["route_era5_rain"].to_numpy(dtype=np.float64)

    for i in range(n):
        res = compute_realized_dispatch_outcome(
            state=str(states[i]),
            commodity=str(comms[i]),
            local_price=float(lps[i]),
            road_km=float(rkms[i]),
            truck_hours=float(thrs[i]),
            same_district=bool(sds[i]),
            arrival_lag_days=int(lags[i]),
            dest_exact_prices=(pm0[i], pmn0[i], pm1[i], pmn1[i], pm2[i], pmn2[i]),
            dest_any_var_min_d0=float(amin0[i]),
            dest_any_open_d0=bool(aopen0[i]),
            route_tmax=float(tmax[i]),
            route_rh=float(rh[i]),
            route_rain=float(rain[i]),
            params=params,
        )
        new_dnet[i] = res["delta_net_inr"]
        new_od0[i] = res["open_d0_delta_net_inr"]
        new_trap[i] = res["closed_or_no_variety_trap"]
        new_drop[i] = res["arrival_price_dropped"]

    df["real_delta_net_inr"] = new_dnet
    df["real_open_d0_delta_net_inr"] = new_od0
    df["real_closed_or_no_variety_trap"] = new_trap
    df["real_arrival_price_dropped"] = new_drop
    return df


def _audit_live_nov2026(live_json_path: Path) -> Dict[str, object]:
    raw = json.loads(live_json_path.read_text())
    records = raw.get("records", [])
    n_total = len(records)
    active_series = 0
    nr_all_week = 0
    latest_rows = []
    for rec in records:
        rows = rec.get("data", [])
        cols = [c["key"] for c in rec.get("columns", []) if c["key"] not in ("variety", "unitOfPrice")]
        found_num = False
        valid_prices = []
        for row in rows:
            for ck in cols:
                val = row.get(ck)
                if isinstance(val, (int, float)) and np.isfinite(val):
                    found_num = True
                    valid_prices.append(float(val))
        if found_num:
            active_series += 1
            latest_rows.append(
                {
                    "state": rec["state"],
                    "market": rec["market"],
                    "commodity": rec["commodity"],
                    "n_active_days_lastweek": len(valid_prices),
                    "latest_price_inr_qtl": valid_prices[0] if valid_prices else None,
                    "t1_status": "PASS_ACTIVE" if len(valid_prices) >= 3 else "WATCH_SPARSE",
                }
            )
        else:
            nr_all_week += 1
            latest_rows.append(
                {
                    "state": rec["state"],
                    "market": rec["market"],
                    "commodity": rec["commodity"],
                    "n_active_days_lastweek": 0,
                    "latest_price_inr_qtl": None,
                    "t1_status": "PRUNE_NON_REPORTING_7D",
                }
            )
    return {
        "retrieved_utc": raw.get("retrieved_utc"),
        "queries_executed": n_total,
        "active_series_count": active_series,
        "full_week_non_reporting_count": nr_all_week,
        "non_reporting_rate_pct": round(100.0 * nr_all_week / max(1, n_total), 1),
        "market_details": latest_rows,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root)
    splits = cfg["temporal_splits"]
    seed = int(cfg["master_seed"])
    reps = int(cfg["evaluation"]["bootstrap_reps"])

    cal_info = json.loads((root / "configs/frozen_calibration.json").read_text())
    frozen_margin = float(cal_info["frozen_safety_margin_inr"])
    hurdle_inr = float(cfg["agent_defaults"]["screen_hurdle_inr_qtl"])
    k_max = int(cfg["agent_defaults"]["k_max_candidates"])

    with open(root / "data/interim/forecaster_2024.pkl", "rb") as f:
        forecaster = pickle.load(f)

    res_dir = root / "results"
    trace_dir = res_dir / "traces"
    res_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(parents=True, exist_ok=True)

    print("[Step 4] Loading candidates & episodes and running causal prediction stream (>=2025-01-01)...")
    ep_all = pd.read_parquet(root / "data/processed/episodes_6state.parquet")
    cand_all = pd.read_parquet(root / "data/processed/candidates_6state.parquet")
    cand_all["date_dt"] = pd.to_datetime(cand_all["date"])
    cand_all["arr_dt"] = pd.to_datetime(cand_all["arrival_date"])

    # Stream causal point + conformal LCB across >= 2025-01-01 (no model refit; strictly <= t arrival maturation)
    cand_2526 = cand_all[cand_all["date_dt"] >= splits["val_start"]].copy()
    pred_ret, lcb_ret = forecaster.predict_point_and_causal_lcb(cand_2526)
    cand_2526["pred_ret"] = pred_ret
    cand_2526["lcb_ret"] = lcb_ret

    # Isolate UNTOUCHED Holdout_2025_2026 (2025-06-01 .. 2026-04-08)
    hold_cands = cand_2526[
        (cand_2526["date_dt"] >= splits["test_start"])
        & (cand_2526["arr_dt"] <= splits["test_end"])
    ].copy()
    hold_eps_all = ep_all[
        (pd.to_datetime(ep_all["date"]) >= splits["test_start"])
        & (pd.to_datetime(ep_all["date"]) <= "2026-04-08")
    ].copy()

    ep_meta = (
        hold_cands[["episode_id", "State", "Commodity", "Variety_Key", "date", "origin_market", "origin_market_key", "local_price"]]
        .drop_duplicates("episode_id")
        .reset_index(drop=True)
    )
    print(
        f"  Holdout total episodes={len(hold_eps_all):,}, shortlisted active episodes={len(ep_meta):,}, candidate rows={len(hold_cands):,}"
    )

    # Check holdout conformal empirical coverage on exact arrivals
    obs_h = hold_cands["target_ret"].notna()
    hold_conformal_cov = float((hold_cands.loc[obs_h, "target_ret"] >= hold_cands.loc[obs_h, "lcb_ret"]).mean() * 100.0)
    print(f"  Holdout causal conformal 80% LCB empirical coverage: {hold_conformal_cov:.2f}%")

    # ---------------- EXP 2: Main Benchmark Policies ----------------
    print("[Exp 2] Evaluating policies B0..B6 and MandiGuard on Holdout_2025_2026...")
    payoff_std = PayoffParams(use_state_statutory_fees=True)
    mg_cfg = AgentConfig(
        screen_hurdle_inr=hurdle_inr,
        k_max=k_max,
        safety_margin_inr=frozen_margin,
        log_traces=True,
        trace_limit=250,
    )

    mg_df, traces = evaluate_mandiguard_vectorized(hold_cands, mg_cfg, payoff_std)
    b1_df = eval_b1_naive_screen_greedy(hold_cands, hurdle_inr=hurdle_inr, payoff_params=payoff_std)
    b2_df = eval_b2_fresh_road_greedy(hold_cands, hurdle_inr=hurdle_inr, payoff_params=payoff_std)
    b3_df = eval_b3_ml_point_dispatch(hold_cands, safety_margin_inr=frozen_margin, payoff_params=payoff_std)
    b4_df = eval_b4_upfront_all_tools(hold_cands, AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin), payoff_std)
    b5_df = eval_b5_multi_agent_coordinator(hold_cands, safety_margin_inr=frozen_margin, k_max=k_max, payoff_params=payoff_std)
    b6_df = eval_b6_heuristic_bucket_router(hold_cands, k_max=k_max, payoff_params=payoff_std)

    b0_df = ep_meta[["episode_id"]].copy()
    b0_df["action"] = "SELL_LOCAL"
    b0_df["chosen_dest"] = "LOCAL"
    b0_df["delta_net_inr"] = 0.0
    b0_df["open_d0_delta_net_inr"] = 0.0
    b0_df["is_dispatch"] = False
    b0_df["is_phantom_loss"] = False
    b0_df["is_closed_trap"] = False
    b0_df["is_arrival_drop"] = False
    b0_df["tool_calls_total"] = 0

    policies = {
        "B0_SellLocal": b0_df,
        "B1_NaiveScreenGreedy": b1_df,
        "B2_FreshRoadGreedy": b2_df,
        "B3_MLPointDispatch": b3_df,
        "B4_UpfrontAllTools": b4_df,
        "B5_MultiAgentCoordinator": b5_df,
        "B6_HeuristicBucketRouter": b6_df,
        "MandiGuard": mg_df,
    }
    exp2_rows = [_summarize_policy(k, v) for k, v in policies.items()]
    exp2_df = pd.DataFrame(exp2_rows)
    exp2_df.to_csv(res_dir / "exp2_main_benchmark_6state.csv", index=False)
    print(exp2_df.to_string(index=False))

    # Write JSONL traces
    with open(trace_dir / "mandiguard_sample_traces.jsonl", "w") as tf:
        for tr in traces:
            tf.write(json.dumps(tr) + "\n")

    # Align paired table for bootstrap & subgroup splits
    paired = ep_meta.copy()
    for pname, pdf in policies.items():
        if pname == "B0_SellLocal":
            continue
        p_sub = pdf.set_index("episode_id")
        paired[f"{pname}_dnet"] = paired["episode_id"].map(p_sub["delta_net_inr"]).to_numpy(dtype=np.float64)
        paired[f"{pname}_phantom"] = paired["episode_id"].map(p_sub["is_phantom_loss"]).to_numpy(dtype=np.float64)
        paired[f"{pname}_trap"] = paired["episode_id"].map(p_sub["is_closed_trap"]).to_numpy(dtype=np.float64)
        paired[f"{pname}_disp"] = paired["episode_id"].map(p_sub["is_dispatch"]).to_numpy(dtype=np.float64)
        paired[f"{pname}_calls"] = paired["episode_id"].map(p_sub["tool_calls_total"]).to_numpy(dtype=np.float64)
    paired["B4_calls_75pct"] = 0.75 * paired["B4_UpfrontAllTools_calls"]

    # State & Commodity breakdown + 4-state 100% NWP verification (Exp 2b & 2c)
    sub_rows = []
    for grp_type, grp_col in [("State", "State"), ("Commodity", "Commodity")]:
        for gval, gdf in paired.groupby(grp_col, sort=True):
            sub_rows.append(
                {
                    "group_type": grp_type,
                    "group_value": gval,
                    "n_episodes": len(gdf),
                    "B1_dnet": round(float(gdf["B1_NaiveScreenGreedy_dnet"].mean()), 2),
                    "B2_dnet": round(float(gdf["B2_FreshRoadGreedy_dnet"].mean()), 2),
                    "B3_dnet": round(float(gdf["B3_MLPointDispatch_dnet"].mean()), 2),
                    "MG_dnet": round(float(gdf["MandiGuard_dnet"].mean()), 2),
                    "B1_ep_phantom_pct": round(float(gdf["B1_NaiveScreenGreedy_phantom"].mean() * 100), 2),
                    "B3_ep_phantom_pct": round(float(gdf["B3_MLPointDispatch_phantom"].mean() * 100), 2),
                    "MG_ep_phantom_pct": round(float(gdf["MandiGuard_phantom"].mean() * 100), 2),
                    "MG_gain_vs_B1": round(float((gdf["MandiGuard_dnet"] - gdf["B1_NaiveScreenGreedy_dnet"]).mean()), 2),
                    "MG_gain_vs_B2": round(float((gdf["MandiGuard_dnet"] - gdf["B2_FreshRoadGreedy_dnet"]).mean()), 2),
                    "MG_avg_calls": round(float(gdf["MandiGuard_calls"].mean()), 2),
                }
            )
    nwp4 = paired[paired["State"].isin(["Gujarat", "Karnataka", "Madhya Pradesh", "Maharashtra"])]
    sub_rows.append(
        {
            "group_type": "WeatherSubset",
            "group_value": "4States_100pct_Native_NWP",
            "n_episodes": len(nwp4),
            "B1_dnet": round(float(nwp4["B1_NaiveScreenGreedy_dnet"].mean()), 2),
            "B2_dnet": round(float(nwp4["B2_FreshRoadGreedy_dnet"].mean()), 2),
            "B3_dnet": round(float(nwp4["B3_MLPointDispatch_dnet"].mean()), 2),
            "MG_dnet": round(float(nwp4["MandiGuard_dnet"].mean()), 2),
            "B1_ep_phantom_pct": round(float(nwp4["B1_NaiveScreenGreedy_phantom"].mean() * 100), 2),
            "B3_ep_phantom_pct": round(float(nwp4["B3_MLPointDispatch_phantom"].mean() * 100), 2),
            "MG_ep_phantom_pct": round(float(nwp4["MandiGuard_phantom"].mean() * 100), 2),
            "MG_gain_vs_B1": round(float((nwp4["MandiGuard_dnet"] - nwp4["B1_NaiveScreenGreedy_dnet"]).mean()), 2),
            "MG_gain_vs_B2": round(float((nwp4["MandiGuard_dnet"] - nwp4["B2_FreshRoadGreedy_dnet"]).mean()), 2),
            "MG_avg_calls": round(float(nwp4["MandiGuard_calls"].mean()), 2),
        }
    )
    pd.DataFrame(sub_rows).to_csv(res_dir / "exp2b_by_state_commodity.csv", index=False)

    # ---------------- Confirmatory Holm Bootstrap (H1-H4) ----------------
    print("[Confirmatory] Running Two-Way Mandi x 2-Week-Block Bootstrap (R=5,000, m=4 Holm)...")
    h_specs = [
        ("H1", "MG - B1 Mean dNet (INR/qtl)", "MandiGuard_dnet", "B1_NaiveScreenGreedy_dnet", "greater"),
        ("H2", "MG - B2 Mean dNet (INR/qtl)", "MandiGuard_dnet", "B2_FreshRoadGreedy_dnet", "greater"),
        ("H3", "MG - B3 Ep Phantom Incidence (prob)", "MandiGuard_phantom", "B3_MLPointDispatch_phantom", "less"),
        ("H4", "MG Calls - 0.75*B4 Calls", "MandiGuard_calls", "B4_calls_75pct", "less"),
    ]
    h_rows = []
    raw_ps = []
    for hid, desc, ca, cb, direction in h_specs:
        b_res = two_way_mandi_week_bootstrap(paired, ca, cb, reps=reps, seed=seed, direction=direction)
        raw_ps.append(b_res["p_value"])
        h_rows.append(
            {
                "hypothesis": hid,
                "estimand": desc,
                "direction": direction,
                "estimate": round(b_res["estimate"], 4),
                "ci95_low": round(b_res["ci95_low"], 4),
                "ci95_high": round(b_res["ci95_high"], 4),
                "p_raw": b_res["p_value"],
                "n_episodes": b_res["n"],
                "n_origin_mandis": b_res["n_mandis"],
                "n_2week_blocks": b_res["n_blocks"],
            }
        )
    holm_p = holm_bonferroni(raw_ps)
    for i, r in enumerate(h_rows):
        r["p_holm"] = round(float(holm_p[i]), 6)
        r["p_raw"] = round(float(r["p_raw"]), 6)
        ok_dir = (r["estimate"] > 0) if r["direction"] == "greater" else (r["estimate"] < 0)
        r["status"] = "SUPPORTED" if (ok_dir and r["p_holm"] < float(cfg["evaluation"]["alpha_fwer"])) else "NOT_SUPPORTED"
    holm_df = pd.DataFrame(h_rows)
    holm_df.to_csv(res_dir / "confirmatory_holm_summary.csv", index=False)
    print(holm_df.to_string(index=False))

    # ---------------- EXP 1: Phantom Arbitrage Anatomy (B1 Chosen Routes) ----------------
    print("[Exp 1] Quantifying Model-Free Phantom Arbitrage Anatomy under Naive B1...")
    b1_chosen = b1_df[b1_df["is_dispatch"]].merge(
        hold_cands,
        left_on=["episode_id", "chosen_dest"],
        right_on=["episode_id", "dest_market"],
        how="inner",
    )
    b1_chosen["dist_band"] = pd.cut(b1_chosen["road_km"], bins=[0, 100, 250, 1000], labels=["15-100km", "100-250km", "250-500km"]).astype(str)
    # Decomposition of gross screen spread into erosion drivers (computed cleanly across B1 dispatches)
    b1_chosen["spoil_cost_inr"] = b1_chosen["dest_modal_d0"].fillna(b1_chosen["screen_dest_price"]) * b1_chosen["real_spoil_frac"]
    b1_chosen["exec_reversion_loss_inr"] = b1_chosen["screen_spread"] - b1_chosen["real_freight_inr"] - b1_chosen["spoil_cost_inr"] - b1_chosen["real_delta_net_inr"]

    anat_rows = []
    for sl_name, grp_col in [("Overall", None), ("Commodity", "Commodity"), ("State", "State"), ("DistanceBand", "dist_band")]:
        groups = [("All_Holdout", b1_chosen)] if grp_col is None else list(b1_chosen.groupby(grp_col, sort=True))
        for gval, g in groups:
            mean_dnet = float(g["real_delta_net_inr"].mean())
            anat_rows.append(
                {
                    "slice_type": sl_name,
                    "slice_value": str(gval),
                    "n_b1_dispatches": len(g),
                    "mean_screen_spread_inr": round(float(g["screen_spread"].mean()), 2),
                    "mean_freight_inr": round(float(g["real_freight_inr"].mean()), 2),
                    "mean_spoilage_inr": round(float(g["spoil_cost_inr"].mean()), 2),
                    "mean_trap_and_reversion_inr": round(float(g["exec_reversion_loss_inr"].mean()), 2),
                    "mean_realized_dnet_inr": round(mean_dnet, 2),
                    "phantom_loss_rate_pct": round(float((g["real_delta_net_inr"] < 0).mean() * 100.0), 2),
                    "closed_or_variety_trap_pct": round(float(g["real_closed_or_no_variety_trap"].mean() * 100.0), 2),
                    "no_exact_variety_3d_pct": round(float(g["real_no_exact_variety_3d"].mean() * 100.0), 2),
                    "lot_30qtl_dnet_inr": round(mean_dnet * LOT_SIZE_QTL, 1),
                    "pct_monthly_hh_crop_income": round(100.0 * (mean_dnet * LOT_SIZE_QTL) / AVG_MONTHLY_CROP_INCOME_INR, 1),
                }
            )
    pd.DataFrame(anat_rows).to_csv(res_dir / "exp1_phantom_anatomy.csv", index=False)

    # ---------------- EXP 3: Grade-Explicit HP Apple Holdout (2026-06-01..2026-08-27) ----------------
    print("[Exp 3] Evaluating Grade-Explicit HP Apple Holdout (2026-06-01..2026-08-27)...")
    cand_ap = pd.read_parquet(root / "data/processed/candidates_hp_apple_grade.parquet")
    cand_ap["date_dt"] = pd.to_datetime(cand_ap["date"])
    cand_ap["arr_dt"] = pd.to_datetime(cand_ap["arrival_date"])
    # Run causal stream from warmup start (2025-11-07), score strictly 2026-06-01..2026-08-27!
    ap_pred, ap_lcb = forecaster.predict_point_and_causal_lcb(cand_ap)
    cand_ap["pred_ret"] = ap_pred
    cand_ap["lcb_ret"] = ap_lcb
    ap_hold = cand_ap[
        (cand_ap["date_dt"] >= splits["apple_test_start"])
        & (cand_ap["date_dt"] <= "2026-08-27")
        & (cand_ap["arr_dt"] <= splits["apple_test_end"])
    ].copy()
    ap_hold["Grade"] = ap_hold["Variety_Key"].astype(str).str.split("|").str[-1].str.strip()

    ap_pols = {
        "B1_NaiveScreenGreedy": eval_b1_naive_screen_greedy(ap_hold, hurdle_inr=hurdle_inr, payoff_params=payoff_std),
        "B2_FreshRoadGreedy": eval_b2_fresh_road_greedy(ap_hold, hurdle_inr=hurdle_inr, payoff_params=payoff_std),
        "B3_MLPointDispatch": eval_b3_ml_point_dispatch(ap_hold, safety_margin_inr=frozen_margin, payoff_params=payoff_std),
        "MandiGuard": evaluate_mandiguard_vectorized(ap_hold, AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin), payoff_std)[0],
    }
    ep_grade_map = ap_hold[["episode_id", "Grade"]].drop_duplicates("episode_id").set_index("episode_id")["Grade"]
    exp3_rows = []
    for pname, pdf in ap_pols.items():
        row_all = _summarize_policy(pname, pdf)
        row_all["Grade"] = "ALL_GRADES"
        exp3_rows.append(row_all)
        pdf_g = pdf.copy()
        pdf_g["Grade"] = pdf_g["episode_id"].map(ep_grade_map)
        for gname, gdf in pdf_g.groupby("Grade", sort=True):
            rg = _summarize_policy(pname, gdf)
            rg["Grade"] = gname
            exp3_rows.append(rg)
    pd.DataFrame(exp3_rows).to_csv(res_dir / "exp3_hp_apple_grade_holdout.csv", index=False)

    # ---------------- EXP 4: Leave-One-Tool-Out Ablations & Extreme Weather Subgroup ----------------
    print("[Exp 4] Running Leave-One-Tool-Out Ablations + Heat/Rain Stress Subgroup...")
    hot_wet_ep_ids = set(
        hold_cands.loc[
            (hold_cands["route_era5_tmax"] >= 35.0) | (hold_cands["route_era5_rain"] >= 35.0), "episode_id"
        ].unique()
    )
    ablation_cfgs = {
        "Full_MandiGuard": AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin),
        "No_T1_Vitality": AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin, use_t1=False),
        "No_T2_OSRM_to_Euclid": AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin, use_t2_osrm=False),
        "No_T3_Weather": AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin, use_t3_weather=False),
        "No_T4_ConformalLCB": AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin, use_t4_lcb=False),
    }
    exp4_rows = []
    for aname, acfg in ablation_cfgs.items():
        adf, _ = evaluate_mandiguard_vectorized(hold_cands, acfg, payoff_std)
        r_all = _summarize_policy(aname, adf)
        r_all["regime"] = "All_Holdout"
        exp4_rows.append(r_all)

        adf_hw = adf[adf["episode_id"].isin(hot_wet_ep_ids)]
        r_hw = _summarize_policy(aname, adf_hw)
        r_hw["regime"] = "Extreme_Heat_or_Rain"
        exp4_rows.append(r_hw)
    pd.DataFrame(exp4_rows).to_csv(res_dir / "exp4_tool_ablations.csv", index=False)

    # ---------------- EXP 5: Tool Budget Pareto Frontier ----------------
    print("[Exp 5] Computing Tool Budget Pareto Frontier...")
    exp5_rows = []
    for budget in [1, 2, 3, 4, 6, 8, 12, 20]:
        mg_b, _ = evaluate_mandiguard_vectorized(
            hold_cands,
            AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin, max_tool_calls_per_episode=budget),
            payoff_std,
        )
        r_mg = _summarize_policy("MandiGuard", mg_b)
        r_mg["budget_cap"] = budget
        exp5_rows.append(r_mg)

        b4_b = eval_b4_upfront_all_tools(
            hold_cands,
            AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin, max_tool_calls_per_episode=budget),
            payoff_std,
        )
        r_b4 = _summarize_policy("B4_UpfrontAllTools", b4_b)
        r_b4["budget_cap"] = budget
        exp5_rows.append(r_b4)

        b5_b = eval_b5_multi_agent_coordinator(
            hold_cands,
            safety_margin_inr=frozen_margin,
            k_max=k_max,
            max_tool_calls=budget,
            payoff_params=payoff_std,
        )
        r_b5 = _summarize_policy("B5_MultiAgentCoordinator", b5_b)
        r_b5["budget_cap"] = budget
        exp5_rows.append(r_b5)
    pd.DataFrame(exp5_rows).to_csv(res_dir / "exp5_budget_pareto.csv", index=False)

    # ---------------- EXP 6: 3x3 Sensitivity Grid & Uniform vs State Statutory Fee Ablation ----------------
    print("[Exp 6] Running 3x3 Freight x Spoilage Sensitivity Grid + Govt Fee Ablation...")
    sens_cases = [
        (fm, sm, True)
        for fm in (0.75, 1.0, 1.25)
        for sm in (0.5, 1.0, 1.5)
    ] + [(1.0, 1.0, False)]  # Uniform 1.5% out-of-district fee comparison
    exp6_rows = []
    for fm, sm, use_stat in sens_cases:
        pp = PayoffParams(freight_mult=fm, spoilage_mult=sm, use_state_statutory_fees=use_stat)
        hc_sens = hold_cands if (fm == 1.0 and sm == 1.0 and use_stat) else _recompute_outcomes_with_params(hold_cands, pp)
        mg_s, _ = evaluate_mandiguard_vectorized(hc_sens, AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=k_max, safety_margin_inr=frozen_margin), pp)
        b1_s = eval_b1_naive_screen_greedy(hc_sens, hurdle_inr=hurdle_inr, payoff_params=pp)
        b2_s = eval_b2_fresh_road_greedy(hc_sens, hurdle_inr=hurdle_inr, payoff_params=pp)
        exp6_rows.append(
            {
                "freight_mult": fm,
                "spoilage_mult": sm,
                "use_state_statutory_fees": use_stat,
                "B1_mean_dnet_inr": round(float(b1_s["delta_net_inr"].mean()), 2),
                "B2_mean_dnet_inr": round(float(b2_s["delta_net_inr"].mean()), 2),
                "MG_mean_dnet_inr": round(float(mg_s["delta_net_inr"].mean()), 2),
                "MG_minus_B1_inr": round(float(mg_s["delta_net_inr"].mean() - b1_s["delta_net_inr"].mean()), 2),
                "MG_minus_B2_inr": round(float(mg_s["delta_net_inr"].mean() - b2_s["delta_net_inr"].mean()), 2),
                "B1_cond_plr_pct": round(float(b1_s.loc[b1_s["is_dispatch"], "is_phantom_loss"].mean() * 100), 2),
                "MG_cond_plr_pct": round(float(mg_s.loc[mg_s["is_dispatch"], "is_phantom_loss"].mean() * 100), 2),
            }
        )
    pd.DataFrame(exp6_rows).to_csv(res_dir / "exp6_sensitivity_grid.csv", index=False)

    # ---------------- EXP 7: Rejection / Pruning Breakdown ----------------
    print("[Exp 7] Exporting MandiGuard Decision & Rejection Breakdown...")
    mg_joined = mg_df.merge(ep_meta[["episode_id", "State", "Commodity"]], on="episode_id", how="left")
    rej_overall = mg_joined.groupby(["action", "reason"], as_index=False).agg(
        count=("episode_id", "count"),
        mean_calls=("tool_calls_total", "mean"),
    )
    rej_overall["slice"] = "Overall"
    rej_overall["pct"] = (100.0 * rej_overall["count"] / len(mg_joined)).round(2)
    rej_overall["mean_calls"] = rej_overall["mean_calls"].round(2)

    rej_comm = mg_joined.groupby(["Commodity", "action", "reason"], as_index=False).agg(
        count=("episode_id", "count"),
        mean_calls=("tool_calls_total", "mean"),
    )
    rej_comm = rej_comm.rename(columns={"Commodity": "slice"})
    tot_by_comm = mg_joined.groupby("Commodity").size().to_dict()
    rej_comm["pct"] = [round(100.0 * c / tot_by_comm[s], 2) for c, s in zip(rej_comm["count"], rej_comm["slice"])]
    rej_comm["mean_calls"] = rej_comm["mean_calls"].round(2)
    pd.concat([rej_overall, rej_comm], ignore_index=True).to_csv(res_dir / "exp7_rejection_breakdown.csv", index=False)

    # ---------------- EXP 8: Live Nov-2026 AGMARKNET API Yard Check ----------------
    print("[Exp 8] Summarizing Live Nov-2026 Official AGMARKNET Snapshot...")
    live_summary = _audit_live_nov2026(root / "data/raw/live_nov2026_agmarknet_snapshot.json")
    (res_dir / "exp8_live_nov2026_demo.json").write_text(json.dumps(live_summary, indent=2))

    # ---------------- EXPERIMENT REGISTRY ----------------
    reg_rows = []
    for _, hr in holm_df.iterrows():
        reg_rows.append(
            {
                "experiment_id": hr["hypothesis"],
                "type": "Confirmatory",
                "scope": "Holdout_2025_2026_Shortlisted",
                "metric": hr["estimand"],
                "value": hr["estimate"],
                "ci_or_note": f"[{hr['ci95_low']}, {hr['ci95_high']}]",
                "p_holm": hr["p_holm"],
                "outcome": hr["status"],
            }
        )
    reg_rows.append(
        {
            "experiment_id": "Val_Conformal_Cov",
            "type": "Diagnostic",
            "scope": "Val_2025H1",
            "metric": "Empirical 80% LCB Coverage (%)",
            "value": cal_info["val_conformal_lcb_empirical_coverage_pct"],
            "ci_or_note": f"Frozen safety_margin={frozen_margin} INR/qtl",
            "p_holm": np.nan,
            "outcome": "LOGGED",
        }
    )
    reg_rows.append(
        {
            "experiment_id": "Holdout_Conformal_Cov",
            "type": "Diagnostic",
            "scope": "Holdout_2025_2026",
            "metric": "Empirical 80% LCB Coverage (%)",
            "value": round(hold_conformal_cov, 2),
            "ci_or_note": "Strictly causal <=t arrival maturation",
            "p_holm": np.nan,
            "outcome": "LOGGED",
        }
    )
    pd.DataFrame(reg_rows).to_csv(root / "EXPERIMENT_REGISTRY.csv", index=False)
    print("=== ALL HOLDOUT EXPERIMENTS COMPLETE ===")


if __name__ == "__main__":
    main()
