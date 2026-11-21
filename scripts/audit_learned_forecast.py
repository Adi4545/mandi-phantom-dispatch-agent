"""Route an actual archived forecast tool with the fixed contextual ranking, using its original veto.

The training target and hyperparameters are identical to audit_contextual_verification.
The scorer sees settlement labels in 2024 only. Both test-period decision functions
receive an explicit list of pre-decision fields. Retrospective evaluation never
supplies a perfect verification signal. Run: python -m scripts.audit_learned_forecast
"""
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from scripts.audit_contextual_verification import (
    APPLE,
    FEATURES,
    MAIN,
    BudgetedVerificationRouter,
    block_interval,
    proposals,
)
from src.agents.budgeted_forecast import review_proposals
from src.evaluation.bootstrap import two_way_mandi_week_bootstrap
from src.evaluation.tail_risk import lower_decile_mean
from src.models.arrival_forecaster import FEATURE_COLS
from src.utils.leakage import load_config

ROOT = Path(__file__).resolve().parents[1]
DECISION_FIELDS = list(dict.fromkeys(["date", "episode_id", *FEATURES, *FEATURE_COLS]))


def evaluate(panel, episodes, trips, model, router, hurdle, seed, reps):
    decisions = trips[DECISION_FIELDS].copy()
    decisions["b2_margin"] = decisions.margin
    scores = {}
    base = trips.set_index("episode_id").delta_net_inr.reindex(
        episodes.episode_id, fill_value=0.0
    )
    episode_meta = episodes.set_index("episode_id")
    episode_dates = episode_meta.date
    counts = episodes.groupby("date").size()

    def run_policy(mode):
        forecast_rows = []

        def predict(features):
            forecast_rows.append(len(features))
            return model.predict(features)

        review = review_proposals(
            decisions,
            predict,
            mode=mode,
            hurdle=hurdle,
            rank_loss=router.predict_priority,
        )
        calls = review.forecast_call
        if sum(forecast_rows) != calls.sum() or (review.veto & ~calls).any():
            raise ValueError("Executed forecast rows disagree with call/veto log")
        net = base.copy()
        net.loc[review.index[review.veto]] = 0.0
        return review, net

    for mode in ["none", "margin", "learned"]:
        scores[mode] = run_policy(mode)
    margin_review, margin_net = scores["margin"]
    learned_review, learned_net = scores["learned"]
    learned_calls = learned_review.forecast_call.sort_index()
    margin_calls = margin_review.forecast_call.sort_index()
    day_slots = decisions.groupby("date").size() // 10
    for calls in [learned_calls, margin_calls]:
        used = calls.groupby(episode_dates.reindex(calls.index)).sum()
        np.testing.assert_array_equal(used.reindex(day_slots.index), day_slots)
    overlap = int((learned_calls & margin_calls).sum())

    # A policy's choice depends only on the dispatch-time allow-list. Reordering
    # proposal rows and changing all held-out payoff labels must preserve it.
    permuted = trips.sample(frac=1, random_state=seed).copy()
    permuted["real_delta_net_inr"] = -permuted.real_delta_net_inr + 791.0
    permuted["delta_net_inr"] = 0.0
    probe = permuted[DECISION_FIELDS].copy()
    probe["b2_margin"] = probe.margin
    check = review_proposals(
        probe,
        model.predict,
        mode="learned",
        hurdle=hurdle,
        rank_loss=router.predict_priority,
    )
    pd.testing.assert_frame_equal(check.sort_index(), learned_review.sort_index())

    rows = []
    for mode, (review, net) in scores.items():
        vetoed = base.loc[review.index[review.veto]]
        change = net - base
        daily = change.groupby(episode_dates).sum()
        blocks, ci = block_interval(counts, daily, reps, seed)
        margin_difference = net - margin_net
        _, ci_margin = block_interval(
            counts, margin_difference.groupby(episode_dates).sum(), reps, seed
        )
        clustered = episode_meta.assign(
            change_b2=change, change_margin=margin_difference
        )
        multi_b2 = two_way_mandi_week_bootstrap(
            clustered, "change_b2", reps=reps, seed=seed
        )
        multi_margin = two_way_mandi_week_bootstrap(
            clustered, "change_margin", reps=reps, seed=seed
        )
        rows.append(
            {
                "panel": panel,
                "routing": mode,
                "episodes": len(base),
                "b2_proposals": len(trips),
                "priority_model_rows": len(trips) if mode == "learned" else 0,
                "forecast_rows": int(review.forecast_call.sum()),
                "forecast_vetoes": len(vetoed),
                "losing_trips_vetoed": int((vetoed < 0).sum()),
                "profitable_trips_vetoed": int((vetoed > 0).sum()),
                "dispatches_after_review": len(trips) - len(vetoed),
                "loss_pct_among_dispatches": 100
                * (net < 0).sum()
                / (len(trips) - len(vetoed)),
                "mean_modeled_inr_qtl_per_episode": net.mean(),
                "mean_change_vs_b2": change.mean(),
                "ci95_low_vs_b2": ci[0],
                "ci95_high_vs_b2": ci[1],
                "mean_change_vs_normalized_margin": margin_difference.mean(),
                "ci95_low_vs_margin": ci_margin[0],
                "ci95_high_vs_margin": ci_margin[1],
                "origin_x_14d_low_vs_b2": multi_b2["ci95_low"],
                "origin_x_14d_high_vs_b2": multi_b2["ci95_high"],
                "origin_x_14d_low_vs_margin": multi_margin["ci95_low"],
                "origin_x_14d_high_vs_margin": multi_margin["ci95_high"],
                "origin_clusters": multi_b2["n_mandis"],
                "exact_lower_decile_mean": lower_decile_mean(net.to_numpy()),
                "blocks_14d": blocks,
                "learned_and_margin_overlap_checks": overlap,
            }
        )
    return rows


def main():
    config = load_config(ROOT)
    splits = config["temporal_splits"]
    hurdle = config["agent_defaults"]["screen_hurdle_inr_qtl"]
    seed = config["master_seed"]
    model_path = ROOT / "data/interim/forecaster_2024.pkl"
    with model_path.open("rb") as model_file:
        point = pickle.load(model_file).point_model
    _, train = proposals(
        MAIN,
        splits["train_start"],
        splits["train_end"],
        hurdle,
        settled_by=splits["train_end"],
    )
    if (train.arrival_date + pd.Timedelta(days=2)).max() > pd.Timestamp(
        splits["train_end"]
    ):
        raise ValueError("A training target uses settlement beyond the training cutoff")
    router = BudgetedVerificationRouter(seed).fit(train)
    rows = []
    for name, path, start, end in [
        ("six_state", MAIN, splits["test_start"], "2026-04-08"),
        ("hp_graded_apple", APPLE, splits["apple_test_start"], "2026-08-27"),
    ]:
        episodes, trips = proposals(path, start, end, hurdle)
        rows.extend(
            evaluate(
                name,
                episodes,
                trips,
                point,
                router,
                hurdle,
                seed,
                config["evaluation"]["bootstrap_reps"],
            )
        )
    table = pd.DataFrame(rows)
    table.to_csv(ROOT / "final/learned-forecast.csv", index=False, float_format="%.6f")
    evidence = {
        "routing_fit": "Same fixed settled-2024 B2 target, features and hyperparameters as contextual-verification-metadata.json",
        "training_b2_trips": len(train),
        "through_settlement": str(
            (train.arrival_date.max() + pd.Timedelta(days=2)).date()
        ),
        "forecast_model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "permutation_and_test_label_mutation_invariance": "Verified on both evaluation panels",
        "threshold_inr_qtl": hurdle,
        "veto_rule": "b2_margin + dest_ref_price * frozen_point_return <= threshold",
        "uncertainty": "5000 paired resamples of nonoverlapping 14-day blocks; additional crossed origin-market x 14-day bootstrap; both weight all eligible episodes",
        "cost_unit": "Forecast rows are distinct B2 proposals passed to the released predictor; one priority prediction per B2 proposal for learned routing. Batch invocation, prices, settlement and actual latency are separate.",
        "input_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (MAIN, APPLE)
        },
    }
    (ROOT / "final/learned-forecast-metadata.json").write_text(
        json.dumps(evidence, indent=2) + "\n"
    )
    print(table.to_string(index=False))


if __name__ == "__main__":
    with threadpool_limits(1):
        main()
