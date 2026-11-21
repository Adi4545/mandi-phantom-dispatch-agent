"""Replay the four affected baselines and verify their arrival-day diagnostic against selected keys.

Run from the repository root using python -m scripts.audit_selected_routes.
Historical comparison tables are read from the original Git revision.
"""
import io
import json
import pickle
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from src.baselines import dispatch_baselines as baselines
from src.evaluation.run_all_experiments import _summarize_policy
from src.evaluation.payoff_model import PayoffParams
from src.models.arrival_forecaster import FEATURE_COLS
from src.utils.leakage import load_config

ROOT = Path(__file__).resolve().parents[1]
BASE = "d20a0cb25827b73688e4ced19948ac5c01e49f6b"
COLUMN = "open_d0_mean_delta_net_inr"


def audit_cohort(candidates, historical, is_apple, margin, hurdle, k_max):
    params = PayoffParams(use_state_statutory_fees=True)
    policies = {
        "B1_NaiveScreenGreedy": (baselines.eval_b1_naive_screen_greedy, {"hurdle_inr": hurdle}),
        "B2_FreshRoadGreedy": (baselines.eval_b2_fresh_road_greedy, {"hurdle_inr": hurdle}),
        "B3_MLPointDispatch": (baselines.eval_b3_ml_point_dispatch, {"safety_margin_inr": margin}),
    }
    if not is_apple:
        policies["B6_HeuristicBucketRouter"] = (baselines.eval_b6_heuristic_bucket_router, {"k_max": k_max})

    ranked = candidates.sort_values(["episode_id", "screen_spread", "dest_market"], ascending=[True, False, True])
    short = ranked.groupby("episode_id").head(k_max)
    keys = ["episode_id", "dest_market"]
    routes = candidates.set_index(keys, verify_integrity=True)
    grades = candidates.drop_duplicates("episode_id").set_index("episode_id").Variety_Key.str.split("|").str[-1].str.strip()
    evidence = []
    for policy, (evaluate, kwargs) in policies.items():
        decisions = evaluate(candidates, payoff_params=params, **kwargs).set_index("episode_id", verify_integrity=True)
        chosen = decisions[decisions.is_dispatch]
        route_keys = pd.MultiIndex.from_arrays([chosen.index, chosen.chosen_dest], names=keys)
        selected = routes.loc[route_keys]
        if not is_apple and policy == "B1_NaiveScreenGreedy":
            # Match the historical Exp15 episode filter, which still permits
            # B1 to choose beyond the candidates used to define the cohort.
            top = short[short.screen_spread.gt(hurdle)]
            top_keys = pd.MultiIndex.from_frame(top[keys])
            cohort_rows = []
            for window, cols in [("day0", ["dest_modal_d0"]),
                                 ("three_day", ["dest_modal_d0", "dest_modal_d1", "dest_modal_d2"])]:
                has_report = top[cols].notna().any(axis=1)
                complete = has_report.groupby(top.episode_id).all()
                members = complete[complete].index
                matched = selected.loc[selected.index.get_level_values("episode_id").isin(members)]
                missing = ~matched[cols].notna().any(axis=1)
                outside = ~matched.index.isin(top_keys)
                cohort_rows.append(dict(window=window, episodes=len(members), dispatches=len(matched),
                                        outside_screen_top_k=int(outside.sum()),
                                        without_report_in_window=int(missing.sum()),
                                        outside_and_without_report=int((outside & missing).sum())))
            pd.DataFrame(cohort_rows).to_csv(ROOT / "results/exp15_matched_b1_route_audit.csv", index=False)
        np.testing.assert_allclose(chosen.open_d0_delta_net_inr, selected.real_open_d0_delta_net_inr, equal_nan=True)
        np.testing.assert_allclose(chosen.delta_net_inr, selected.real_delta_net_inr, equal_nan=True)
        # GroupBy.first previously filled a missing selected value whenever any
        # candidate retained by this evaluator supplied that field.
        pool = ranked if policy.startswith("B1_") else short
        available = pool.real_open_d0_delta_net_inr.notna().groupby(pool.episode_id).any()
        borrowed = decisions.open_d0_delta_net_inr.isna() & available.reindex(decisions.index)
        groups = {"ALL_GRADES" if is_apple else "ALL": decisions}
        if is_apple:
            groups.update({grade: rows for grade, rows in decisions.groupby(grades.reindex(decisions.index))})
        for grade, group in groups.items():
            row_idx = historical.policy.eq(policy)
            if is_apple:
                row_idx &= historical.Grade.eq(grade)
            old = historical.loc[row_idx].squeeze()
            summary = _summarize_policy(policy, group)

            # The parent finalization also updates expected shortfall. For the
            # row-selection-only comparison, evaluate the historical tail convention.
            net = group.delta_net_inr.to_numpy()
            summary["cvar_10_inr"] = round(float(net[net <= np.quantile(net, 0.10)].mean()), 2)
            for field, value in summary.items():
                if field not in (COLUMN, "policy"):
                    np.testing.assert_allclose(value, old[field], atol=1e-6, rtol=0, err_msg=field)
            evidence.append({
                "cohort": "HP_Apple" if is_apple else "Six_state", "grade": grade, "policy": policy,
                "episodes": len(group), "dispatches": int(group.is_dispatch.sum()),
                "dispatches_with_observed_day0_payoff": int((group.is_dispatch & group.open_d0_delta_net_inr.notna()).sum()),
                "abstentions_scored_zero": int((~group.is_dispatch).sum()),
                "wrongly_filled_day0_payoffs": int(borrowed.loc[group.index].sum()),
                "historical_day0_mean": float(old[COLUMN]), "corrected_day0_mean": summary[COLUMN],
                "other_historical_summary_fields_match": True,
            })
    return evidence


def main():
    cfg = load_config(ROOT)
    splits = cfg["temporal_splits"]
    options = cfg["agent_defaults"]
    cal = json.loads((ROOT / "configs/frozen_calibration.json").read_text())
    evidence = []
    with (ROOT / "data/interim/forecaster_2024.pkl").open("rb") as handle:
        forecaster = pickle.load(handle)
    for path, table, is_apple in [
        ("candidates_6state", "exp2_main_benchmark_6state", False),
        ("candidates_hp_apple_grade", "exp3_hp_apple_grade_holdout", True),
    ]:
        date_start = splits["apple_test_start" if is_apple else "test_start"]
        date_end = splits["apple_test_end" if is_apple else "test_end"]
        data = pd.read_parquet(ROOT / "data/processed" / (path + ".parquet"))
        keep = (pd.to_datetime(data.date) >= date_start) & (pd.to_datetime(data.arrival_date) <= date_end)
        candidates = data.loc[keep].copy()
        del data
        # B3 only consumes the point forecasts. The point estimator is frozen.
        candidates["pred_ret"] = forecaster.point_model.predict(candidates[FEATURE_COLS].to_numpy(dtype=float))
        raw = subprocess.check_output(["git", "show", f"{BASE}:results/{table}.csv"], cwd=ROOT)
        hist = pd.read_csv(io.BytesIO(raw))
        evidence.extend(audit_cohort(candidates, hist, is_apple, cal["frozen_safety_margin_inr"],
                                     options["screen_hurdle_inr_qtl"], options["k_max_candidates"]))
    out = pd.DataFrame(evidence)
    out.to_csv(ROOT / "results/selected_route_integrity.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
