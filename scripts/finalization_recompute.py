"""Recompute Stage-I holdout metrics from the rebuilt candidate table.

Does not overwrite exp1–exp17 artifacts. Writes:
  results/exp1b_b1_outcome_types.csv
  results/exp18_used_holdout_temporal_slice.csv
  results/finalization_recompute.json

Exp 18 is a partition of the already-used holdout (origin date >= 2026-02-12
versus earlier). It is a stability check, not an untouched test. No threshold
is retuned.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.baselines.dispatch_baselines import (
    eval_b1_naive_screen_greedy,
    eval_b2_fresh_road_greedy,
    eval_b3_ml_point_dispatch,
    eval_b4_upfront_all_tools,
)
from src.evaluation.bootstrap import holm_bonferroni, two_way_mandi_week_bootstrap
from src.evaluation.payoff_model import PayoffParams
from src.evaluation.run_all_experiments import _summarize_policy
from src.evaluation.tail_risk import lower_decile_mean
from src.utils.leakage import load_config

LATE_SLICE_START = "2026-02-12"  # declared before looking at slice estimates


def _slice_summary(name: str, df: pd.DataFrame) -> dict:
    d = _summarize_policy(name, df)
    d["slice"] = name
    return d


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root)
    splits = cfg["temporal_splits"]
    seed = int(cfg["master_seed"])
    reps = int(cfg["evaluation"]["bootstrap_reps"])
    cal = json.loads((root / "configs/frozen_calibration.json").read_text())
    margin = float(cal["frozen_safety_margin_inr"])
    hurdle = float(cfg["agent_defaults"]["screen_hurdle_inr_qtl"])
    k_max = int(cfg["agent_defaults"]["k_max_candidates"])

    forecaster = None
    pickle_error = None
    try:
        with open(root / "data/interim/forecaster_2024.pkl", "rb") as f:
            forecaster = pickle.load(f)
    except Exception as exc:  # sklearn 1.3.0 pickle vs newer runtime
        pickle_error = f"{type(exc).__name__}: {exc}"
        print(f"[recompute] forecaster pickle not loaded: {pickle_error}", flush=True)

    ep_all = pd.read_parquet(root / "data/processed/episodes_6state.parquet")
    cand_all = pd.read_parquet(root / "data/processed/candidates_6state.parquet")
    cand_all["date_dt"] = pd.to_datetime(cand_all["date"])
    cand_all["arr_dt"] = pd.to_datetime(cand_all["arrival_date"])
    cand_2526 = cand_all[cand_all["date_dt"] >= splits["val_start"]].copy()
    if forecaster is not None:
        print(f"[recompute] predicting LCB on {len(cand_2526):,} rows", flush=True)
        pred_ret, lcb_ret = forecaster.predict_point_and_causal_lcb(cand_2526)
        cand_2526["pred_ret"] = pred_ret
        cand_2526["lcb_ret"] = lcb_ret
    hold = cand_2526[
        (cand_2526["date_dt"] >= splits["test_start"]) & (cand_2526["arr_dt"] <= splits["test_end"])
    ].copy()
    ep_meta = (
        hold[["episode_id", "State", "Commodity", "date", "origin_market_key", "local_price"]]
        .drop_duplicates("episode_id")
        .reset_index(drop=True)
    )
    cov = None
    if forecaster is not None and "lcb_ret" in hold.columns:
        obs = hold["target_ret"].notna()
        cov = float((hold.loc[obs, "target_ret"] >= hold.loc[obs, "lcb_ret"]).mean() * 100.0)
    print(f"[recompute] holdout episodes={len(ep_meta):,} coverage={cov}", flush=True)

    payoff = PayoffParams(use_state_statutory_fees=True)
    mg_cfg = AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=margin)
    policies = {
        "B1_NaiveScreenGreedy": eval_b1_naive_screen_greedy(hold, hurdle_inr=hurdle, payoff_params=payoff),
        "B2_FreshRoadGreedy": eval_b2_fresh_road_greedy(hold, hurdle_inr=hurdle, payoff_params=payoff),
    }
    if forecaster is not None:
        policies["B3_MLPointDispatch"] = eval_b3_ml_point_dispatch(hold, safety_margin_inr=margin, payoff_params=payoff)
        policies["B4_UpfrontAllTools"] = eval_b4_upfront_all_tools(
            hold, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=margin), payoff
        )
        policies["MandiGuard"] = evaluate_mandiguard_vectorized(hold, mg_cfg, payoff)[0]
    fresh = pd.DataFrame([_summarize_policy(k, v) for k, v in policies.items()]).set_index("policy")
    published = pd.read_csv(root / "results/exp2_main_benchmark_6state.csv").set_index("policy")
    compare_cols = [
        "n_episodes",
        "dispatch_rate_pct",
        "mean_delta_net_inr",
        "ep_phantom_loss_pct",
        "cond_phantom_loss_rate_pct",
        "cond_closed_or_trap_rate_pct",
        "cvar_10_inr",
        "avg_tool_calls",
    ]
    diffs = []
    for pol in fresh.index:
        if pol not in published.index:
            continue
        for col in compare_cols:
            a = float(fresh.loc[pol, col])
            b = float(published.loc[pol, col])
            if abs(a - b) > 0.02:
                diffs.append({"policy": pol, "column": col, "recomputed": a, "published": b})

    paired = ep_meta.copy()
    for pname, pdf in policies.items():
        sub = pdf.set_index("episode_id")
        paired[f"{pname}_dnet"] = paired["episode_id"].map(sub["delta_net_inr"]).to_numpy(dtype=np.float64)
        paired[f"{pname}_phantom"] = paired["episode_id"].map(sub["is_phantom_loss"]).to_numpy(dtype=np.float64)
        paired[f"{pname}_calls"] = paired["episode_id"].map(sub["tool_calls_total"]).to_numpy(dtype=np.float64)
    if "B4_UpfrontAllTools_calls" in paired.columns:
        paired["B4_calls_75pct"] = 0.75 * paired["B4_UpfrontAllTools_calls"]
    specs = [("H_B2_minus_B1", "B2_FreshRoadGreedy_dnet", "B1_NaiveScreenGreedy_dnet", "greater")]
    if "MandiGuard_dnet" in paired.columns and "B3_MLPointDispatch_phantom" in paired.columns:
        specs = [
            ("H1", "MandiGuard_dnet", "B1_NaiveScreenGreedy_dnet", "greater"),
            ("H2", "MandiGuard_dnet", "B2_FreshRoadGreedy_dnet", "greater"),
            ("H3", "MandiGuard_phantom", "B3_MLPointDispatch_phantom", "less"),
            ("H4", "MandiGuard_calls", "B4_calls_75pct", "less"),
        ]
    boot_rows = []
    raw_p = []
    for hid, ca, cb, direction in specs:
        res = two_way_mandi_week_bootstrap(paired, ca, cb, reps=reps, seed=seed, direction=direction)
        raw_p.append(res["p_value"])
        boot_rows.append(
            {
                "hypothesis": hid,
                "estimate": round(res["estimate"], 4),
                "ci95_low": round(res["ci95_low"], 4),
                "ci95_high": round(res["ci95_high"], 4),
                "p_percentile": res["p_value"],
                "p_basic": res["p_value_basic"],
                "n": res["n"],
            }
        )
    holm = holm_bonferroni(raw_p)
    for i, row in enumerate(boot_rows):
        row["p_holm_percentile"] = holm[i]

    # B1 outcome types. The trap flag is true for waits as well as absences.
    b1 = policies["B1_NaiveScreenGreedy"]
    chosen = b1[b1["is_dispatch"]].merge(
        hold,
        left_on=["episode_id", "chosen_dest"],
        right_on=["episode_id", "dest_market"],
        how="inner",
    )
    vc = chosen["real_outcome_type"].value_counts(dropna=False)
    outcome_rows = []
    for k, n in vc.items():
        outcome_rows.append(
            {
                "outcome_type": str(k),
                "n_b1_dispatches": int(n),
                "share_pct": round(100.0 * n / len(chosen), 2),
                "mean_delta_net_inr": round(float(chosen.loc[chosen["real_outcome_type"] == k, "real_delta_net_inr"].mean()), 2),
                "loss_rate_pct": round(float((chosen.loc[chosen["real_outcome_type"] == k, "real_delta_net_inr"] < 0).mean() * 100), 2),
            }
        )
    out_df = pd.DataFrame(outcome_rows)
    out_df.to_csv(root / "results/exp1b_b1_outcome_types.csv", index=False)

    # Extreme quoted prices touching the holdout candidate rows.
    price_cols = [c for c in ["screen_dest_price", "dest_ref_price", "local_price", "dest_modal_d0"] if c in hold.columns]
    extreme = {}
    for c in price_cols:
        s = hold[c]
        extreme[c] = {
            "n_gt_20000": int((s > 20000).sum()),
            "n_lt_5": int((s < 5).sum()),
            "n": int(s.notna().sum()),
        }

    # Exp 18: partition of the used holdout. Not untouched.
    paired["date_dt"] = pd.to_datetime(paired["date"])
    slice_rows = []
    for label, mask in [
        ("early_2025-06-01_to_2026-02-11", paired["date_dt"] < LATE_SLICE_START),
        ("late_2026-02-12_to_2026-04-08", paired["date_dt"] >= LATE_SLICE_START),
        ("full_used_holdout", pd.Series(True, index=paired.index)),
    ]:
        sub = paired.loc[mask]
        slice_rows.append(
            {
                "slice": label,
                "untouched": False,
                "n_episodes": int(len(sub)),
                "B1_mean": round(float(sub["B1_NaiveScreenGreedy_dnet"].mean()), 2),
                "B2_mean": round(float(sub["B2_FreshRoadGreedy_dnet"].mean()), 2),
                "B2_minus_B1": round(float((sub["B2_FreshRoadGreedy_dnet"] - sub["B1_NaiveScreenGreedy_dnet"]).mean()), 2),
                "B1_ep_phantom_pct": round(float(sub["B1_NaiveScreenGreedy_phantom"].mean() * 100), 2),
                "B2_ep_phantom_pct": round(float(sub["B2_FreshRoadGreedy_phantom"].mean() * 100), 2),
                "B1_cvar10": round(lower_decile_mean(sub["B1_NaiveScreenGreedy_dnet"].to_numpy()), 2),
                "B2_cvar10": round(lower_decile_mean(sub["B2_FreshRoadGreedy_dnet"].to_numpy()), 2),
                "MG_recomputed": "MandiGuard_dnet" in sub.columns,
            }
        )
    pd.DataFrame(slice_rows).to_csv(root / "results/exp18_used_holdout_temporal_slice.csv", index=False)

    published_holm = pd.read_csv(root / "results/confirmatory_holm_summary.csv")
    report = {
        "holdout_episodes": int(len(ep_meta)),
        "pickle_error": pickle_error,
        "holdout_conformal_coverage_pct": None if cov is None else round(cov, 2),
        "published_holdout_conformal_coverage_pct": 79.07,
        "metric_mismatches": diffs,
        "tail_definition": "Mean of exactly the lowest 10% of finite episode payoff mass. Historical tables included all ties at the percentile.",
        "bootstrap": boot_rows,
        "published_holm": published_holm.to_dict(orient="records"),
        "b1_dispatches": int(len(chosen)),
        "b1_outcome_types": outcome_rows,
        "b1_trap_flag_pct": round(float(chosen["real_closed_or_no_variety_trap"].mean() * 100), 2),
        "b1_no_exact_3d_pct": round(float(chosen["real_no_exact_variety_3d"].mean() * 100), 2),
        "extreme_prices": extreme,
        "exp18": slice_rows,
        "cvar_hand_check": round(lower_decile_mean(np.array([0.0, 0.0, -10.0, -30.0, 5.0, 8.0, 9.0, 10.0, 11.0, 12.0])), 4),
    }
    (root / "results/finalization_recompute.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"mismatches": diffs, "coverage": report["holdout_conformal_coverage_pct"], "bootstrap": boot_rows, "exp18": slice_rows, "outcomes": outcome_rows}, indent=2))


if __name__ == "__main__":
    main()
