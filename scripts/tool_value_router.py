"""Exploratory allocation of a fixed number of frozen arrival-price forecasts."""
import argparse
import hashlib
import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.tree import DecisionTreeRegressor, export_text
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.stage3_policy_selector import HURDLE, joined_panel
from src.evaluation.bootstrap import two_way_mandi_week_bootstrap
from src.models.arrival_forecaster import FEATURE_COLS

SEED = 20261117
CHEAP = [
    "relative_hurdle_margin",
    "fresh_net_margin_inr",
    "local_price",
    "road_km",
    "dest_open_prob_14d",
    "dest_dow_open_rate",
    "dest_vol_14d",
    "dest_intra_spread_14d",
]


def read_panel(path, start, end):
    episodes = joined_panel(path, start, end)
    trips = episodes[episodes.b2_dispatch].reset_index()
    needed = [c for c in FEATURE_COLS if c not in trips]
    extra = pd.read_parquet(
        path,
        columns=["episode_id", "dest_market", *needed],
        filters=[
            ("date", ">=", pd.Timestamp(start)),
            ("date", "<=", pd.Timestamp(end)),
        ],
    )
    trips = trips.merge(
        extra, on=["episode_id", "dest_market"], validate="one_to_one", how="left"
    )
    trips["relative_hurdle_margin"] = (
        trips.fresh_net_margin_inr - HURDLE
    ) / trips.dest_ref_price
    return episodes, trips.set_index("episode_id", verify_integrity=True).sort_index()


def scheduled(context, priority):
    # Both methods spend exactly floor(N_date/10). An episode ID breaks tied priorities.
    ranked = (
        context[["date"]]
        .assign(priority=priority)
        .reset_index()
        .sort_values(["date", "priority", "episode_id"], ascending=[True, False, True])
    )
    daily = ranked.groupby("date")
    return pd.Index(
        ranked.loc[
            daily.cumcount() < daily.episode_id.transform("size") // 10, "episode_id"
        ]
    )


def query_veto(context, selected, tool):
    if not len(selected):
        return pd.Series(dtype=bool, index=selected)
    rows = context.loc[selected]
    output = np.asarray(tool.predict(rows[FEATURE_COLS].to_numpy(dtype=float)))
    if output.shape != (len(selected),) or not np.isfinite(output).all():
        raise ValueError("Each requested forecast must be finite")
    veto = (rows.fresh_net_margin_inr + rows.dest_ref_price * output) <= HURDLE
    return veto


def exact_random(context, tool):
    # For a date with n proposals and k slots, use prefix-length k in cyclic rotations
    # whose starts advance by k. In the n/gcd(n,k) allocations each proposal occurs
    # k/gcd(n,k) times. Memoize the deterministic answers only after a route is selected.
    # Once all eligible routes have been selected, the other rotations reuse those answers.
    groups = [pd.Index(g.index) for _, g in context.groupby("date") if len(g) >= 10]
    probability = pd.Series(0.0, index=context.index)
    for ids in groups:
        probability.loc[ids] = (len(ids) // 10) / len(ids)
    answers = pd.Series(False, index=context.index)
    known = set()
    batches = max((math.ceil(len(ids) / (len(ids) // 10)) for ids in groups), default=0)
    for iteration in range(batches):
        need = []
        for ids in groups:
            k = len(ids) // 10
            selected = ids.take((iteration * k + np.arange(k)) % len(ids))
            need.extend(x for x in selected if x not in known)
        fresh = pd.Index(need)
        if len(fresh):
            answers.loc[fresh] = query_veto(context, fresh, tool)
            known.update(fresh.tolist())
    if known != set(probability.index[probability > 0]):
        raise AssertionError("Uncovered positive-probability benchmark routes")
    return probability * answers.astype(float), len(known)


def evaluate(name, episodes, trips, router, fill, price_tool):
    # Router input is strictly decision context. Score labels are read later for evaluation.
    context = trips[
        list(
            dict.fromkeys(
                [
                    "date",
                    "fresh_net_margin_inr",
                    "dest_ref_price",
                    *CHEAP,
                    *FEATURE_COLS,
                ]
            )
        )
    ]
    priorities = router.predict(context[CHEAP].fillna(fill))
    learned = scheduled(context, priorities)
    margin = scheduled(context, -context.relative_hurdle_margin)
    if len(learned) != len(margin):
        raise AssertionError("Mismatched budgets")
    vetos = {}
    for mode, chosen in [("learned_tool_value", learned), ("low_margin", margin)]:
        mask = pd.Series(0.0, index=context.index)
        mask.loc[chosen] = query_veto(context, chosen, price_tool).astype(float)
        vetos[mode] = mask
    random_veto, random_unique = exact_random(context, price_tool)
    vetos["expected_uniform_random"] = random_veto
    vetos["B2_no_calls"] = pd.Series(0.0, index=context.index)
    base = episodes.payoff.where(episodes.b2_dispatch, 0)
    payoff = {
        name: base.add(-prob * trips.payoff, fill_value=0).reindex(episodes.index)
        for name, prob in vetos.items()
    }
    rows = []
    for mode, veto in vetos.items():
        calls = 0 if mode == "B2_no_calls" else len(learned)
        row = {
            "panel": name,
            "policy": mode,
            "episodes": len(episodes),
            "B2_proposals": len(trips),
            "forecast_rows_per_policy_run": calls,
            "expected_vetoes": float(veto.sum()),
            "mean_inr_qtl": float(payoff[mode].mean()),
            "mean_vs_B2": float((payoff[mode] - base).mean()),
            "mean_vs_margin": float((payoff[mode] - payoff["low_margin"]).mean()),
            "mean_vs_expected_random": float(
                (payoff[mode] - payoff["expected_uniform_random"]).mean()
            ),
        }
        rows.append(row)
    contrasts = []
    for comparator in ["B2_no_calls", "low_margin", "expected_uniform_random"]:
        changes = episodes[["origin_market_key", "date"]].assign(
            change=payoff["learned_tool_value"] - payoff[comparator]
        )
        boot = two_way_mandi_week_bootstrap(
            changes, "change", week_block_len=2, reps=5000, seed=SEED
        )
        contrasts.append(
            {
                "panel": name,
                "comparator": comparator,
                "learned_minus_comparator": boot["estimate"],
                "paired_95_lower": boot["ci95_low"],
                "paired_95_upper": boot["ci95_high"],
            }
        )
    return rows, contrasts, random_unique


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "final")
    args = parser.parse_args()
    main_path = args.data_dir / "candidates_6state.parquet"
    apple_path = args.data_dir / "candidates_hp_apple_grade.parquet"
    model_path = ROOT / "data/interim/forecaster_2024.pkl"
    with model_path.open("rb") as file:
        price_tool = pickle.load(file).point_model
    cfg = json.loads((ROOT / "configs/config.json").read_text())
    split = cfg["temporal_splits"]
    _, cal = read_panel(main_path, split["val_start"], split["val_end"])
    cal = cal[
        cal.arrival_date + pd.Timedelta(days=2) <= pd.Timestamp(split["val_end"])
    ].copy()
    would_veto = query_veto(cal, cal.index, price_tool)
    target = (-cal.payoff).where(would_veto, 0.0)
    fill = cal[CHEAP].median()
    router = DecisionTreeRegressor(max_depth=3, min_samples_leaf=250, random_state=SEED)
    router.fit(cal[CHEAP].fillna(fill), target)
    # This is the sole fit, with parameters fixed before any evaluation replay.
    meta = {
        "seed": SEED,
        "price_model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "candidate_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [main_path, apple_path]
        },
        "calibration_proposals_with_labels": len(cal),
        "would_veto": int(would_veto.sum()),
        "target_negative": int((target < 0).sum()),
        "target_positive": int((target > 0).sum()),
        "last_training_settlement": str(
            (cal.arrival_date + pd.Timedelta(days=2)).max().date()
        ),
        "target_mean": float(target.mean()),
        "features": CHEAP,
        "median_imputation": fill.to_dict(),
        "max_depth": 3,
        "min_samples_leaf": 250,
        "sklearn": sklearn.__version__,
        "daily_budget": "floor(n_B2/10)",
        "veto_threshold": HURDLE,
        "tree": export_text(router, feature_names=CHEAP, decimals=6),
        "random_benchmark_unique_forecasts_across_cyclic_allocations": {},
    }
    rows, intervals = [], []
    for name, path, start, end in [
        ("six_state", main_path, split["test_start"], split["test_end"]),
        ("hp_apple", apple_path, split["apple_test_start"], "2026-08-27"),
    ]:
        episodes, trips = read_panel(path, start, end)
        values, comparisons, count = evaluate(
            name, episodes, trips, router, fill, price_tool
        )
        rows.extend(values)
        intervals.extend(comparisons)
        meta["random_benchmark_unique_forecasts_across_cyclic_allocations"][
            name
        ] = count
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output_dir / "tool-value-router.csv", index=False)
    pd.DataFrame(intervals).to_csv(
        args.output_dir / "tool-value-router-contrasts.csv", index=False
    )
    (args.output_dir / "tool-value-router-metadata.json").write_text(
        json.dumps(meta, indent=2, allow_nan=False) + "\n"
    )
    print(pd.DataFrame(intervals).to_string(index=False))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
