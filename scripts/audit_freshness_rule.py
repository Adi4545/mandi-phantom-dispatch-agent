"""Exploratory matched replay on two previously inspected cohorts; no model refit.

B1 chooses a destination in the usual way. A single new rule vetoes that
dispatch when its pooled commodity headline is more than one calendar day old.
Vetoed episodes sell locally at zero incremental modeled payoff. The runner-up
is never substituted. All summaries retain the original eligible episodes.
Same-date portal reports are assumed available when taking a decision. The
source has no publication time to support a dispatch-morning interpretation.

Run from the repository root: python -m scripts.audit_freshness_rule
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.baselines.dispatch_baselines import eval_b1_naive_screen_greedy, eval_b2_fresh_road_greedy
from src.evaluation.bootstrap import two_way_mandi_week_bootstrap
from src.evaluation.tail_risk import lower_decile_mean
from src.utils.leakage import load_config

ROOT = Path(__file__).resolve().parents[1]
AGE_LIMIT_DAYS = 1
KEYS = ["State", "Commodity", "dest_market"]
PRICE_COLUMNS = ["State", "Commodity", "Market", "Arrival_Date", "Modal_Price"]


def latest_b1_quote(candidates, outcomes, prices):
    """Match each B1 dispatch to the latest historical commodity quote at its chosen destination."""
    daily = (prices.rename(columns={"Market": "dest_market", "Arrival_Date": "report_date"})
             .groupby(KEYS + ["report_date"], as_index=False).Modal_Price.median()
             .dropna(subset=["Modal_Price"]))
    daily["report_date"] = pd.to_datetime(daily.report_date)
    dispatch = outcomes.loc[outcomes.is_dispatch, ["chosen_dest"]].reset_index()
    chosen = dispatch.merge(candidates[["episode_id", *KEYS, "date", "screen_dest_price"]],
                            left_on=["episode_id", "chosen_dest"], right_on=["episode_id", "dest_market"],
                            validate="one_to_one", how="left")
    matched = pd.merge_asof(chosen.sort_values("date"), daily.sort_values("report_date"), by=KEYS,
                            left_on="date", right_on="report_date", direction="backward",
                            tolerance=pd.Timedelta(days=7))
    if matched.report_date.isna().any():
        raise ValueError("An original B1 dispatch has no historical headline within seven days")
    np.testing.assert_allclose(matched.Modal_Price, matched.screen_dest_price, atol=1e-8, rtol=0)
    matched = matched.set_index("episode_id", verify_integrity=True)
    return (matched.date - matched.report_date).dt.days


def cohort_results(scope, candidates, prices, cfg):
    hurdle = cfg["agent_defaults"]["screen_hurdle_inr_qtl"]
    if not np.isfinite(candidates.real_delta_net_inr).all():
        raise ValueError("A candidate has no scored scenario payoff")
    b1 = eval_b1_naive_screen_greedy(candidates, hurdle_inr=hurdle).set_index("episode_id", verify_integrity=True)
    b2 = eval_b2_fresh_road_greedy(candidates, hurdle_inr=hurdle).set_index("episode_id", verify_integrity=True)
    if not b1.index.equals(b2.index):
        raise ValueError("Baseline episode sets differ")
    ages = latest_b1_quote(candidates, b1, prices)
    keep = b1.is_dispatch & ages.reindex(b1.index).le(AGE_LIMIT_DAYS)
    rule_net = b1.delta_net_inr.where(keep, 0.0)
    rows = []
    design = candidates[["episode_id", "origin_market_key", "date"]].drop_duplicates().set_index("episode_id")
    design = design.loc[b1.index]
    design["delta_vs_b1"] = rule_net - b1.delta_net_inr
    design["delta_vs_b2"] = rule_net - b2.delta_net_inr
    intervals = {
        label: two_way_mandi_week_bootstrap(design, "delta_vs_" + label, reps=cfg["evaluation"]["bootstrap_reps"],
                                            seed=cfg["master_seed"])
        for label in ["b1", "b2"]
    }
    for label, dispatched, net in [
        ("B1_original", b1.is_dispatch, b1.delta_net_inr),
        ("B1_headline_max_age_1d", keep, rule_net),
        ("B2_fresh_exact_road", b2.is_dispatch, b2.delta_net_inr),
    ]:
        losses = net < 0
        row = dict(cohort=scope, evaluation="exploratory_reused_holdout", policy=label,
                   n_episodes=len(net), dispatches=int(dispatched.sum()), negative_episodes=int(losses.sum()),
                   dispatch_pct=100 * dispatched.mean(), loss_pct_among_dispatches=100 * losses[dispatched].mean(),
                   loss_pct_per_episode=100 * losses.mean(), mean_gain_inr_per_qtl_episode=net.mean(),
                   worst_decile_inr_per_qtl_episode=lower_decile_mean(net.to_numpy()))
        if label == "B1_headline_max_age_1d":
            veto = b1.is_dispatch & ~keep
            row.update(verified_original_dispatch_quotes=len(ages), vetoed_b1_dispatches=int(veto.sum()),
                       vetoed_losing_dispatches=int((veto & (b1.delta_net_inr < 0)).sum()),
                       vetoed_profitable_dispatches=int((veto & (b1.delta_net_inr > 0)).sum()))
            for key, result in intervals.items():
                row["mean_diff_vs_" + key] = result["estimate"]
                row["ci95_low_vs_" + key] = result["ci95_low"]
                row["ci95_high_vs_" + key] = result["ci95_high"]
            row["n_origin_mandis"] = intervals["b1"]["n_mandis"]
            row["n_2week_blocks"] = intervals["b1"]["n_blocks"]
        rows.append(row)
    return rows


def main():
    cfg = load_config(ROOT)
    data = ROOT / "data"
    ranges = cfg["temporal_splits"]
    main_quotes = pd.read_parquet(data / "raw/agmarknet_6state_top_apple_2024_2026.parquet", columns=PRICE_COLUMNS)
    apple_quotes = pd.read_csv(data / "raw/hp_apple_daily_2025_2026.csv",
                               usecols=["state", "commodity", "market", "arrival_date", "modal_price"])
    apple_quotes.columns = [name.title() for name in apple_quotes.columns]
    rows = []
    for scope, filename, quotes, start, end_day, last_arrival in [
        ("six_state", "candidates_6state.parquet", main_quotes, ranges["test_start"], "2026-04-08", ranges["test_end"]),
        ("HP_graded_apple", "candidates_hp_apple_grade.parquet", apple_quotes, ranges["apple_test_start"],
         "2026-08-27", ranges["apple_test_end"]),
    ]:
        frame = pd.read_parquet(data / "processed" / filename,
                                filters=[("date", ">=", pd.Timestamp(start)), ("date", "<=", pd.Timestamp(end_day)),
                                         ("arrival_date", "<=", pd.Timestamp(last_arrival))])
        rows.extend(cohort_results(scope, frame, quotes, cfg))
    output = pd.DataFrame(rows)
    output.to_csv(ROOT / "final/freshness-rule.csv", index=False, float_format="%.6f")
    print(output.to_string(index=False))


if __name__ == "__main__":
    main()
