"""Learn which B2 proposals to verify. Only the retrospective scorer sees trip outcomes.

Run from repository root with `python -m scripts.audit_contextual_verification`.
Within each date's B2 proposals the agent can request floor(N/10) extra checks.
Training uses 2024 choices whose entire episode has settled by December 31.
Both test panels were previously examined. Uniform random is integrated exactly.
Perfect pre-trip loss veto, zero checking cost and a single daily decision batch
define the evaluation scenario; actual confirmations and receipts are unavailable.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from src.baselines.dispatch_baselines import eval_b2_fresh_road_greedy
from src.evaluation.payoff_model import compute_freight_inr
from src.models.arrival_forecaster import FEATURE_COLS
from src.utils.leakage import load_config

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "data/processed/candidates_6state.parquet"
APPLE = ROOT / "data/processed/candidates_hp_apple_grade.parquet"
FEATURES = [
    "margin",
    "local_price",
    "dest_ref_price",
    "road_km",
    "tau_days",
    "dest_open_prob_14d",
    "dest_dow_open_rate",
    "dest_vol_14d",
    "dest_intra_spread_14d",
    "dest_ret_7d",
    "month_sin",
    "month_cos",
    "state_code",
    "commodity_code",
]
META = [
    "episode_id",
    "date",
    "origin_market_key",
    "dest_market",
    "arrival_date",
    "State",
    "Commodity",
    "same_district",
    "screen_spread",
    "dest_age_days",
    "real_delta_net_inr",
    "real_open_d0_delta_net_inr",
    "real_closed_or_no_variety_trap",
    "real_arrival_price_dropped",
]
COLUMNS = list(
    dict.fromkeys(META + [f for f in FEATURES if f != "margin"] + FEATURE_COLS)
)
BUDGET_DIVISOR = 10


def proposals(path, start, end, hurdle, settled_by=None):
    frame = pd.read_parquet(
        path,
        columns=COLUMNS,
        filters=[
            ("date", ">=", pd.Timestamp(start)),
            ("date", "<=", pd.Timestamp(end)),
        ],
    )
    if settled_by is not None:
        # Drop whole episodes to avoid removing competitors before B2 chooses a route.
        latest_arrival = frame.groupby("episode_id").arrival_date.transform("max")
        frame = frame[latest_arrival + pd.Timedelta(days=2) <= pd.Timestamp(settled_by)]
    if not np.isfinite(frame.real_delta_net_inr).all():
        raise ValueError("Incomplete structural payoff for a B2 candidate")
    decisions = eval_b2_fresh_road_greedy(frame, hurdle_inr=hurdle)
    trips = decisions.loc[
        decisions.is_dispatch, ["episode_id", "chosen_dest", "delta_net_inr"]
    ].merge(
        frame,
        left_on=["episode_id", "chosen_dest"],
        right_on=["episode_id", "dest_market"],
        validate="one_to_one",
        how="left",
    )
    np.testing.assert_allclose(trips.delta_net_inr, trips.real_delta_net_inr)
    freight = np.asarray(
        [
            compute_freight_inr(s, km, sd, lp, commodity=c)
            for s, km, sd, lp, c in zip(
                trips.State,
                trips.road_km,
                trips.same_district,
                trips.local_price,
                trips.Commodity,
            )
        ]
    )
    trips["margin"] = trips.dest_ref_price - trips.local_price - freight
    if not (trips.margin.gt(hurdle) & trips.dest_age_days.eq(0)).all():
        raise ValueError("Selected route fails B2's original eligibility condition")
    trips = trips.sort_values(["date", "episode_id"]).reset_index(drop=True)
    episodes = (
        frame[["episode_id", "date", "origin_market_key"]]
        .drop_duplicates()
        .sort_values(["date", "episode_id"])
    )
    if len(episodes) != len(decisions):
        raise ValueError("Distinct episode count does not match B2 decisions")
    return episodes, trips


def allocate(context, priority):
    """Executable budget decision. Higher priorities run first; ties use the episode key."""
    ranked = context[["episode_id", "date"]].assign(priority=priority)
    ranked = ranked.sort_values(
        ["date", "priority", "episode_id"], ascending=[True, False, True]
    )
    groups = ranked.groupby("date")
    selected = groups.cumcount() < (
        groups.episode_id.transform("size") // BUDGET_DIVISOR
    )
    return selected.reindex(context.index)


class BudgetedVerificationRouter:
    """Estimate the magnitude of an avoidable loss, then allocate the day's call slots."""

    def __init__(self, seed):
        self.model = HistGradientBoostingRegressor(
            max_depth=3,
            max_iter=60,
            learning_rate=0.06,
            min_samples_leaf=50,
            categorical_features=[
                FEATURES.index("state_code"),
                FEATURES.index("commodity_code"),
            ],
            loss="squared_error",
            early_stopping=False,
            random_state=seed,
        )

    def fit(self, train):
        target = (-train.delta_net_inr).clip(lower=0)
        self.model.fit(train[FEATURES], target)
        return self

    def predict_priority(self, context):
        return self.model.predict(context[FEATURES]).clip(min=0)

    def route(self, context):
        return allocate(context, self.predict_priority(context))


def block_interval(episode_counts, differences, reps, seed):
    """Paired ratio-of-sums interval across nonoverlapping 14-calendar-day blocks."""
    days = pd.DataFrame(
        {"episodes": episode_counts, "gain_difference": differences}
    ).fillna(0)
    block = (days.index - days.index.min()).days // 14
    sums = days.groupby(block).sum().to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(sums), size=(reps, len(sums)))
    draws = sums[idx].sum(axis=1)
    ci = np.quantile(draws[:, 1] / draws[:, 0], [0.025, 0.975])
    return len(sums), ci


def replay(name, episodes, trips, router, seed, reps):
    context = trips[["episode_id", "date", *FEATURES]]
    daily_n = context.groupby("date").episode_id.transform("size")
    slots = daily_n // BUDGET_DIVISOR
    benefit = (-trips.delta_net_inr).clip(lower=0)
    stages = {
        "learned_expected_loss": router.route(context),
        "uniform_random_expected": slots / daily_n,
        "lowest_b2_margin": allocate(context, -context.margin),
        "lowest_recent_reporting": allocate(context, -context.dest_open_prob_14d),
        "prescient_priority_ceiling": allocate(context, benefit),
    }
    expected_counts = slots.groupby(context.date).first()
    calls = int(expected_counts.sum())
    total_payoff = trips.delta_net_inr.sum()
    counts = episodes.groupby("date").size()
    model_gain = benefit * stages["learned_expected_loss"]
    rows = []
    for label, queried in stages.items():
        np.testing.assert_allclose(queried.groupby(context.date).sum(), expected_counts)
        gain = queried * benefit
        daily_delta = (model_gain - gain).groupby(context.date).sum()
        nblocks, ci = block_interval(counts, daily_delta, reps, seed)
        rows.append(
            {
                "cohort": name,
                "priority": label,
                "episodes": len(episodes),
                "b2_proposals": len(trips),
                "daily_batches_with_proposals": len(expected_counts),
                "batches_with_slots": int(expected_counts.gt(0).sum()),
                "verification_slots": calls,
                "total_b2_negative_trips": int(benefit.gt(0).sum()),
                "expected_vetoed_loss_trips": float((queried * benefit.gt(0)).sum()),
                "baseline_mean_modeled_inr_qtl_per_episode": total_payoff
                / len(episodes),
                "oracle_verification_gain_inr_qtl_per_episode": gain.sum()
                / len(episodes),
                "oracle_verification_gain_inr_qtl_per_check": gain.sum() / calls,
                "oracle_total_modeled_inr_qtl_per_episode": (total_payoff + gain.sum())
                / len(episodes),
                "learned_minus_this_inr_qtl_per_episode": daily_delta.sum()
                / len(episodes),
                "paired_ci95_low": ci[0],
                "paired_ci95_high": ci[1],
                "fortnight_blocks": nblocks,
            }
        )
    ceiling = rows[-1]["oracle_verification_gain_inr_qtl_per_episode"]
    if any(
        r["oracle_verification_gain_inr_qtl_per_episode"] > ceiling + 1e-9 for r in rows
    ):
        raise ValueError("A feasible allocation exceeded the perfect-priority ceiling")
    return rows


def main():
    config = load_config(ROOT)
    seed = config["master_seed"]
    hurdle = config["agent_defaults"]["screen_hurdle_inr_qtl"]
    splits = config["temporal_splits"]
    train_eps, train = proposals(
        MAIN,
        splits["train_start"],
        splits["train_end"],
        hurdle,
        settled_by=splits["train_end"],
    )
    router = BudgetedVerificationRouter(seed).fit(train)
    cohorts = [
        ("six_state", MAIN, splits["test_start"], "2026-04-08"),
        ("hp_graded_apple", APPLE, splits["apple_test_start"], "2026-08-27"),
    ]
    rows = []
    for label, path, start, end in cohorts:
        eps, trips = proposals(path, start, end, hurdle)
        rows.extend(
            replay(
                label, eps, trips, router, seed, config["evaluation"]["bootstrap_reps"]
            )
        )
    output = pd.DataFrame(rows)
    output.to_csv(
        ROOT / "final/contextual-verification.csv", index=False, float_format="%.6f"
    )
    metadata = {
        "train_candidate_episodes_after_full_settlement": len(train_eps),
        "train_b2_proposals": len(train),
        "train_loss_cases": int(train.delta_net_inr.lt(0).sum()),
        "train_max_selected_settlement_date": str(
            (train.arrival_date.max() + pd.Timedelta(days=2)).date()
        ),
        "seed": seed,
        "number_of_bootstrap_draws": config["evaluation"]["bootstrap_reps"],
        "target": "max(0, -modeled_B2_incremental_payoff_inr_per_quintal)",
        "features": FEATURES,
        "daily_slots": "floor(number_of_B2_proposals_on_date/10)",
        "model": router.model.get_params(),
        "evidence": "Exploratory reanalysis of previously inspected cohorts with fixed simulator payoffs. "
        "Perfect, cost-free loss verification before departure is assumed; no verified field outcomes.",
        "inputs_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (MAIN, APPLE)
        },
    }
    (ROOT / "final/contextual-verification-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n"
    )
    print(output.to_string(index=False))


if __name__ == "__main__":
    with threadpool_limits(1):
        main()
