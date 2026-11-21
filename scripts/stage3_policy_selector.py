"""Exploratory Stage III. Train one shallow abstention tree for B2-proposed routes."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.tree import DecisionTreeRegressor, export_text
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.baselines.dispatch_baselines import eval_b2_fresh_road_greedy
from src.evaluation.payoff_model import compute_freight_inr, PayoffParams

# Only these columns are admitted to destination selection. The tree sees a
# smaller fixed subset from the single candidate already proposed by B2.
BOARD = [
    "episode_id",
    "State",
    "Commodity",
    "origin_market_key",
    "date",
    "arrival_date",
    "dest_market",
    "screen_spread",
    "local_price",
    "road_km",
    "same_district",
    "dest_ref_price",
    "dest_age_days",
    "dest_open_prob_14d",
    "dest_dow_open_rate",
    "dest_vol_14d",
    "dest_intra_spread_14d",
]
FEATURES = [
    "fresh_net_margin_inr",
    "local_price",
    "road_km",
    "dest_open_prob_14d",
    "dest_dow_open_rate",
    "dest_vol_14d",
    "dest_intra_spread_14d",
]
SCORING = [
    "real_delta_net_inr",
    "real_open_d0_delta_net_inr",
    "real_closed_or_no_variety_trap",
    "real_arrival_price_dropped",
]
HURDLE = 100.0
SEED = 20261117
REPS = 5000


def propose_from_board(board):
    ranked = board.sort_values(
        ["episode_id", "screen_spread", "dest_market"], ascending=[True, False, True]
    )
    short = ranked.groupby("episode_id", sort=False).head(5).copy()
    params = PayoffParams()
    freight = np.fromiter(
        (
            compute_freight_inr(state, km, district, price, params, commodity=crop)
            for state, km, district, price, crop in zip(
                short.State,
                short.road_km,
                short.same_district,
                short.local_price,
                short.Commodity,
            )
        ),
        float,
    )
    short["fresh_net_margin_inr"] = (
        short.dest_ref_price - short.local_price - freight
    ).where(short.dest_age_days == 0, -np.inf)
    ordered = short.sort_values(
        ["episode_id", "fresh_net_margin_inr", "dest_market"],
        ascending=[True, False, True],
    )
    proposed = ordered.drop_duplicates("episode_id").set_index("episode_id").copy()
    proposed["b2_dispatch"] = proposed.fresh_net_margin_inr > HURDLE
    return proposed


def apply_saved_tree(board, card):
    """Return policy choices from the board only. No price/outcome labels are loaded."""
    proposals = propose_from_board(board[BOARD])
    active = proposals.b2_dispatch
    proposals["predicted_increment_inr_qtl"] = np.nan
    x = (
        proposals.loc[active, card["features"]]
        .fillna(card["feature_medians_training_only"])
        .to_numpy(dtype=np.float32)
    )
    tree = card["tree"]
    estimates = []
    for row in x:
        node = 0
        while tree["children_left"][node] >= 0:
            feature = tree["feature_index"][node]
            go_left = row[feature] <= tree["threshold"][node]
            node = (
                tree["children_left"][node] if go_left else tree["children_right"][node]
            )
        estimates.append(tree["estimated_payoff"][node])
    proposals.loc[active, "predicted_increment_inr_qtl"] = estimates
    proposals["b2_destination"] = proposals.dest_market.where(active, "LOCAL")
    proposals["chosen_destination"] = proposals.dest_market.where(
        active & (proposals.predicted_increment_inr_qtl > 0), "LOCAL"
    )
    return proposals[
        ["b2_destination", "chosen_destination", "predicted_increment_inr_qtl"]
    ].reset_index()


def joined_panel(path, first, last):
    date_filter = [
        ("date", ">=", pd.Timestamp(first)),
        ("date", "<=", pd.Timestamp(last)),
    ]
    original = pd.read_parquet(path, columns=BOARD + SCORING, filters=date_filter)
    chosen = propose_from_board(original[BOARD])
    historical = (
        eval_b2_fresh_road_greedy(original, hurdle_inr=HURDLE)
        .set_index("episode_id")
        .reindex(chosen.index)
    )
    np.testing.assert_array_equal(
        chosen.dest_market.where(chosen.b2_dispatch, "LOCAL"), historical.chosen_dest
    )
    # Only now attach historical candidate outcomes for training or scoring.
    labels = original.set_index(["episode_id", "dest_market"], verify_integrity=True)[
        "real_delta_net_inr"
    ]
    keys = pd.MultiIndex.from_arrays(
        [chosen.index, chosen.dest_market], names=labels.index.names
    )
    chosen["payoff"] = labels.reindex(keys).to_numpy()
    if chosen.payoff.isna().any():
        raise ValueError("Selected candidate lacks a simulator payoff")
    np.testing.assert_array_equal(
        chosen.payoff.where(chosen.b2_dispatch, 0), historical.delta_net_inr
    )
    return chosen


def crossed_interval(episodes, diff):
    # A crossed ('pigeonhole') cluster bootstrap: resample origin-market labels
    # and Monday-Sunday calendar weeks independently, then multiply their counts.
    market_codes, markets = pd.factorize(episodes.origin_market_key, sort=True)
    week_codes, weeks = pd.factorize(episodes.date.dt.to_period("W-SUN"), sort=True)
    n_market, n_week = len(markets), len(weeks)
    ids = market_codes * n_week + week_codes
    shape = (n_market, n_week)
    sums = np.bincount(ids, weights=diff, minlength=n_market * n_week).reshape(shape)
    counts = np.bincount(ids, minlength=n_market * n_week).reshape(shape)
    rng = np.random.default_rng(SEED)
    estimates = []
    for offset in range(0, REPS, 250):
        size = min(REPS - offset, 250)
        mw = rng.multinomial(n_market, np.full(n_market, 1 / n_market), size=size)
        ww = rng.multinomial(n_week, np.full(n_week, 1 / n_week), size=size)
        weights = (mw @ counts * ww).sum(axis=1)
        numerator = (mw @ sums * ww).sum(axis=1)
        estimates.extend(numerator[weights > 0] / weights[weights > 0])
    lo, hi = np.quantile(estimates, [0.025, 0.975])
    return {
        "paired_cluster_ci_low": float(lo),
        "paired_cluster_ci_high": float(hi),
        "origin_market_clusters": n_market,
        "calendar_week_clusters": n_week,
        "valid_boot_reps": len(estimates),
    }


def evaluate(name, cohort, model, medians):
    active = cohort.b2_dispatch
    values = model.predict(cohort.loc[active, FEATURES].fillna(medians))
    accepted = active.copy()
    accepted.loc[active] = values > 0
    b2_return = cohort.payoff.where(active, 0.0)
    predicted_return = cohort.payoff.where(accepted, 0.0)
    diff = predicted_return - b2_return
    return {
        "panel": name,
        "episodes": len(cohort),
        "B2_dispatches": int(active.sum()),
        "selector_dispatches": int(accepted.sum()),
        "extra_abstentions": int((active & ~accepted).sum()),
        "B2_negative_dispatches": int((b2_return < 0).sum()),
        "selector_negative_dispatches": int((predicted_return < 0).sum()),
        "B2_mean_inr_qtl": float(b2_return.mean()),
        "selector_mean_inr_qtl": float(predicted_return.mean()),
        "paired_mean_selector_minus_B2": float(diff.mean()),
        **crossed_interval(cohort, diff),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "final")
    parser.add_argument(
        "--score-board",
        type=Path,
        help="Make decisions from a candidate-board Parquet without fitting or loading outcomes",
    )
    parser.add_argument(
        "--model", type=Path, default=ROOT / "final/stage3-selector-model.json"
    )
    parser.add_argument("--decisions-out", type=Path)
    args = parser.parse_args()
    if args.score_board is not None:
        if args.decisions_out is None:
            parser.error("--score-board requires --decisions-out")
        board = pd.read_parquet(args.score_board, columns=BOARD)
        card = json.loads(args.model.read_text())
        apply_saved_tree(board, card).to_csv(args.decisions_out, index=False)
        return
    cfg = json.loads((ROOT / "configs/config.json").read_text())
    split = cfg["temporal_splits"]
    if cfg["agent_defaults"]["screen_hurdle_inr_qtl"] != HURDLE:
        raise ValueError("This control uses B2's published 100 INR/qtl hurdle")
    main_file = args.data_dir / "candidates_6state.parquet"
    apple_file = args.data_dir / "candidates_hp_apple_grade.parquet"
    training = joined_panel(main_file, split["train_start"], split["train_end"])
    settled = training.arrival_date + pd.Timedelta(days=2) <= pd.Timestamp(
        split["train_end"]
    )
    train = training[training.b2_dispatch & settled].copy()
    medians = train[FEATURES].median()
    model = DecisionTreeRegressor(max_depth=3, min_samples_leaf=250, random_state=SEED)
    model.fit(train[FEATURES].fillna(medians), train.payoff)
    print(f"Fitted on {len(train)} paired, settled B2 dispatches", flush=True)
    panels = [
        (
            "six_state",
            main_file,
            split["test_start"],
            split["test_end"],
            split["test_end"],
        ),
        (
            "hp_apple",
            apple_file,
            split["apple_test_start"],
            "2026-08-27",
            split["apple_test_end"],
        ),
    ]
    rows = []
    for name, path, first, last, last_arrival in panels:
        cohort = joined_panel(path, first, last)
        if (
            cohort.arrival_date + pd.Timedelta(days=2) > pd.Timestamp(last_arrival)
        ).any():
            raise ValueError("Outcome window extends beyond archived prices")
        rows.append(evaluate(name, cohort, model, medians))
    meta = {
        "features": FEATURES,
        "feature_medians_training_only": medians.to_dict(),
        "fit_rows": len(train),
        "training_shortlisted_episodes": len(training),
        "last_training_settlement": str(
            (train.arrival_date + pd.Timedelta(days=2)).max().date()
        ),
        "tree_depth": int(model.get_depth()),
        "leaves": int(model.get_n_leaves()),
        "minimum_leaf_size": 250,
        "training_seed": SEED,
        "bootstrap_reps": REPS,
        "scikit_learn": sklearn.__version__,
        "tree_rules_display": export_text(model, feature_names=FEATURES, decimals=4),
        "tree": {
            "feature_index": model.tree_.feature.tolist(),
            "threshold": model.tree_.threshold.tolist(),
            "children_left": model.tree_.children_left.tolist(),
            "children_right": model.tree_.children_right.tolist(),
            "estimated_payoff": model.tree_.value.ravel().tolist(),
            "n_training": model.tree_.n_node_samples.tolist(),
        },
        "sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (main_file, apple_file)
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "stage3-selector-model.json").write_text(
        json.dumps(meta, indent=2, allow_nan=False) + "\n"
    )
    result = pd.DataFrame(rows)
    result.to_csv(args.output_dir / "stage3-selector.csv", index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
