"""Exploratory sensitivity of modeled dispatch payoffs to one missing arrival-day report.

Run from the repository root: python -m scripts.audit_one_day_gap

Freeze B1/B2 decisions first. For a dispatched route with positive, finite exact-variety
quotes on both arrival day and the next calendar day, mask the arrival-day quote and
recompute its payoff. Each focal destination/variety/date is a separate one-day
interruption, with its following report retained. This is not a simultaneous deletion
of consecutive dates. Untreated episodes stay in the all-episode denominator.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.baselines.dispatch_baselines import eval_b1_naive_screen_greedy, eval_b2_fresh_road_greedy
from src.evaluation.payoff_model import PayoffParams, compute_realized_dispatch_outcome
from src.utils.leakage import load_config

ROOT = Path(__file__).resolve().parents[1]
ROUTE = ["episode_id", "dest_market"]
QUOTE = ["State", "Commodity", "Variety_Key", "dest_market", "arrival_date"]
PARAMS = PayoffParams(use_state_statutory_fees=True)


def compare_payoffs(row):
    common = dict(
        state=row.State, commodity=row.Commodity, local_price=row.local_price,
        road_km=row.road_km, truck_hours=row.truck_hours, same_district=row.same_district,
        arrival_lag_days=row.tau_days, dest_any_var_min_d0=np.nan, dest_any_open_d0=False,
        route_tmax=row.route_era5_tmax, route_rh=row.route_era5_rh, route_rain=row.route_era5_rain,
        params=PARAMS,
    )
    # The positive day-1 exact quote guarantees that fallback market-level fields
    # cannot enter either score. All paths share the same route and transit weather.
    def score(day0, day1, wait):
        result = compute_realized_dispatch_outcome(
            **common, dest_exact_prices=(*day0, *day1, np.nan, np.nan))
        if result["wait_days"] != wait:
            raise ValueError("Scorer did not take the specified exact-quote path.")
        return result["delta_net_inr"]

    day0 = (row.dest_modal_d0, row.dest_min_d0)
    day1 = (row.dest_modal_d1, row.dest_min_d1)
    absent = (np.nan, np.nan)
    original = score(day0, day1, 0)
    delayed_same_quote = score(absent, day0, 1)
    delayed_next_quote = score(absent, day1, 1)
    return original, delayed_same_quote, delayed_next_quote


def evaluate_panel(panel, filename, start, end, last_decision, hurdle):
    candidates = pd.read_parquet(ROOT / "data/processed" / filename)
    keep = candidates.date.between(start, last_decision) & candidates.arrival_date.le(end)
    candidates = candidates.loc[keep].copy()
    choices = {}
    for name, policy in [("B1", eval_b1_naive_screen_greedy), ("B2", eval_b2_fresh_road_greedy)]:
        choices[name] = policy(candidates, hurdle_inr=hurdle, payoff_params=PARAMS).set_index("episode_id")
    if not choices["B1"].index.equals(choices["B2"].index):
        raise ValueError("Policies have different episode sets.")

    selected_keys = pd.concat([
        decisions.loc[decisions.is_dispatch, ["chosen_dest"]].reset_index().rename(columns={"chosen_dest": "dest_market"})
        for decisions in choices.values()
    ]).drop_duplicates()
    selected = selected_keys.merge(candidates, on=ROUTE, how="left", validate="one_to_one", indicator=True)
    if not selected["_merge"].eq("both").all():
        raise ValueError("Selected destination unavailable in the candidate table.")
    prices = selected[["dest_modal_d0", "dest_modal_d1"]]
    eligible = selected.loc[(np.isfinite(prices) & prices.gt(0)).all(axis=1)].copy()
    scores = [compare_payoffs(row) for row in eligible.itertuples(index=False)]
    eligible[["original", "delay_same_price", "masked"]] = np.asarray(scores)
    np.testing.assert_allclose(eligible.original, eligible.real_delta_net_inr, rtol=1e-6, atol=0.02)
    # The same portal quote can serve multiple origins and both policies. Report
    # that shared support separately from the count of scored dispatch episodes.
    if (eligible.groupby(QUOTE)[["dest_modal_d0", "dest_min_d0", "dest_modal_d1", "dest_min_d1"]]
            .nunique(dropna=False).to_numpy() > 1).any():
        raise ValueError("Multiple quote values for the same panel key.")
    eligible = eligible.set_index(ROUTE, verify_integrity=True)
    rows = []
    all_payoffs = {}
    for name, decisions in choices.items():
        dispatch = decisions.loc[decisions.is_dispatch]
        keys = pd.MultiIndex.from_arrays([dispatch.index, dispatch.chosen_dest], names=ROUTE)
        acted = eligible.reindex(keys).dropna(subset=["original"]).reset_index()
        shift = acted.masked - acted.original
        baseline = decisions.delta_net_inr.copy()
        revised = baseline.copy()
        revised.loc[acted.episode_id] += shift.to_numpy()
        all_payoffs[name] = (baseline, revised)
        rows.append(dict(
            panel=panel, policy=name, episodes=len(decisions), dispatches=len(dispatch),
            consecutive_report_dispatches=len(acted), distinct_focal_quote_keys=len(acted[QUOTE].drop_duplicates()),
            original_mean_all_episodes=baseline.mean(), masked_mean_all_episodes=revised.mean(),
            change_mean_all_episodes=(revised - baseline).mean(),
            original_mean_affected=acted.original.mean(), masked_mean_affected=acted.masked.mean(),
            mean_change_affected=shift.mean(), mean_absolute_change_affected=shift.abs().mean(),
            mean_delay_spoilage_cost_change_at_fixed_quote=(acted.delay_same_price - acted.original).mean(),
            mean_change_due_to_next_report_price=(acted.masked - acted.delay_same_price).mean(),
            nonloss_to_loss=int((acted.original.ge(0) & acted.masked.lt(0)).sum()),
            loss_to_nonloss=int((acted.original.lt(0) & acted.masked.ge(0)).sum()),
        ))
    b1, m1 = all_payoffs["B1"]
    b2, m2 = all_payoffs["B2"]
    rows.append(dict(panel=panel, policy="B2_minus_B1", episodes=len(b2),
                     original_mean_all_episodes=(b2 - b1).mean(), masked_mean_all_episodes=(m2 - m1).mean(),
                     change_mean_all_episodes=((m2 - m1) - (b2 - b1)).mean()))
    return rows


def main():
    config = load_config(ROOT)
    splits = config["temporal_splits"]
    hurdle = config["agent_defaults"]["screen_hurdle_inr_qtl"]
    rows = evaluate_panel("six_state_holdout", "candidates_6state.parquet", splits["test_start"],
                          splits["test_end"], splits["test_end"], hurdle)
    rows.extend(evaluate_panel("HP_graded_apple", "candidates_hp_apple_grade.parquet", splits["apple_test_start"],
                               splits["apple_test_end"], "2026-08-27", hurdle))
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "final/one-day-gap.csv", index=False, float_format="%.6f")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
