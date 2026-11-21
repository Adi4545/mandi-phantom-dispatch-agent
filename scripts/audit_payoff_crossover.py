"""Exact B1 versus B2 payoff sensitivity on two historical simulator cohorts.

Run from any directory with the rebuilt six-state candidates in data/processed.
The uniform increment applies only to the payoff of a selected route lacking
a finite positive exact-key price on arrival day and the following two days.
All policy actions and the episode denominator are fixed.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.baselines.dispatch_baselines import eval_b1_naive_screen_greedy, eval_b2_fresh_road_greedy


def selected_payoffs(table, policy, hurdle):
    decisions = policy(table, hurdle_inr=hurdle).set_index("episode_id", verify_integrity=True).sort_index()
    keys = ["episode_id", "dest_market"]
    prices = table[["dest_modal_d0", "dest_modal_d1", "dest_modal_d2"]].to_numpy()
    missing = ~(np.isfinite(prices) & (prices > 0)).any(axis=1)
    if not np.array_equal(missing, table.real_no_exact_variety_3d):
        raise ValueError("Stored missing-quote flags disagree with the three daily destination prices")
    candidates = table.assign(missing=missing).set_index(keys, verify_integrity=True)
    dispatched = decisions[decisions.is_dispatch]
    chosen_keys = pd.MultiIndex.from_arrays([dispatched.index, dispatched.chosen_dest], names=keys)
    selected = candidates.loc[chosen_keys]
    np.testing.assert_allclose(selected.real_delta_net_inr, dispatched.delta_net_inr, rtol=0, atol=0)
    decisions["unmatched_dispatch"] = False
    decisions.loc[dispatched.index, "unmatched_dispatch"] = selected.missing.to_numpy()
    return decisions


def compare(name, table, hurdle):
    first = selected_payoffs(table, eval_b1_naive_screen_greedy, hurdle)
    second = selected_payoffs(table, eval_b2_fresh_road_greedy, hurdle)
    if not first.index.equals(second.index):
        raise ValueError(f"{name} episode sets differ")
    diff = first.delta_net_inr - second.delta_net_inr
    n = len(diff)
    m1, m2 = first.unmatched_dispatch, second.unmatched_dispatch
    delta_m = m1.astype(int) - m2.astype(int)
    intercept, slope = diff.mean(), delta_m.mean()
    total_unmatched_routes = int(m1.sum() + m2.sum())
    same_unmatched_choice = int((m1 & m2 & first.chosen_dest.eq(second.chosen_dest)).sum())
    # For independent bounded corrections to each episode-destination,
    # common choices cancel; each remaining selected missing route has |weight|=1/N.
    worst_case_slope = (total_unmatched_routes - 2 * same_unmatched_choice) / n
    crossing = -intercept / slope if slope != 0 else np.nan
    if np.isfinite(crossing):
        first_at_crossing = first.delta_net_inr + crossing * m1
        second_at_crossing = second.delta_net_inr + crossing * m2
        np.testing.assert_allclose((first_at_crossing - second_at_crossing).mean(), 0, atol=1e-9)
    return {
        "panel": name, "shortlisted_episodes": n,
        "B1_dispatches":int(first.is_dispatch.sum()), "B2_dispatches":int(second.is_dispatch.sum()),
        "B1_unmatched3d_dispatches":int(m1.sum()), "B2_unmatched3d_dispatches":int(m2.sum()),
        "shared_unmatched3d_route_choices":same_unmatched_choice,
        "B1_initial_mean":first.delta_net_inr.mean(), "B2_initial_mean":second.delta_net_inr.mean(),
        "B1_minus_B2_initial_inr_qtl":intercept, "B1_minus_B2_uniform_slope":slope,
        "uniform_offset_to_tie_inr_qtl":crossing,
        "B1_minus_B2_minus500_offset":float((diff - 500*delta_m).mean()),
        "B1_minus_B2_plus500_offset":float((diff + 500*delta_m).mean()),
        "route_specific_bound_slope":worst_case_slope,
        "smallest_route_specific_symmetric_bound_allowing_tie":abs(intercept)/worst_case_slope if worst_case_slope else np.nan,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT/"data/processed")
    parser.add_argument("--output", type=Path, default=ROOT/"final/payoff-crossover.csv")
    args = parser.parse_args()
    with (ROOT/"configs/config.json").open() as file:
        cfg=json.load(file)
    split = cfg["temporal_splits"]
    specs = [
        ("six_state", "candidates_6state.parquet", split["test_start"], split["test_end"], split["test_end"]),
        ("hp_apple", "candidates_hp_apple_grade.parquet", split["apple_test_start"], "2026-08-27", split["apple_test_end"]),
    ]
    columns = ["State","Commodity","episode_id","dest_market","same_district","euclid_km","road_km","local_price",
               "screen_dest_price","screen_spread","dest_age_days","dest_ref_price","real_delta_net_inr",
               "real_open_d0_delta_net_inr","real_closed_or_no_variety_trap","real_arrival_price_dropped",
               "dest_modal_d0","dest_modal_d1","dest_modal_d2","real_no_exact_variety_3d"]
    rows = []
    for name, path, first, last, arrival_end in specs:
        filters = [("date", ">=", pd.Timestamp(first)), ("date", "<=", pd.Timestamp(last)),
                   ("arrival_date", "<=", pd.Timestamp(arrival_end))]
        table = pd.read_parquet(args.data_dir/path, columns=columns, filters=filters)
        rows.append(compare(name, table, cfg["agent_defaults"]["screen_hurdle_inr_qtl"]))
    result=pd.DataFrame(rows)
    args.output.parent.mkdir(exist_ok=True,parents=True)
    result.to_csv(args.output,index=False)
    print(result.to_string(index=False))


if __name__=="__main__":
    main()
