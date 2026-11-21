"""Evaluate conditional forecast calls against B2 on the two previously inspected panels."""
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.agents.budgeted_forecast import review_proposals
from src.baselines.dispatch_baselines import eval_b2_fresh_road_greedy
from src.evaluation.bootstrap import two_way_mandi_week_bootstrap
from src.evaluation.payoff_model import PayoffParams, compute_freight_inr
from src.evaluation.tail_risk import lower_decile_mean
from src.models.arrival_forecaster import FEATURE_COLS
from src.utils.leakage import load_config

ROOT = Path(__file__).resolve().parents[1]


def evaluate(name, frame, predict, hurdle):
    decisions = eval_b2_fresh_road_greedy(frame, hurdle_inr=hurdle)
    base = decisions.set_index("episode_id").delta_net_inr
    trips = decisions.loc[decisions.is_dispatch, ["episode_id", "chosen_dest"]].merge(
        frame,
        left_on=["episode_id", "chosen_dest"],
        right_on=["episode_id", "dest_market"],
        validate="one_to_one",
    )
    params = PayoffParams()
    trips["b2_margin"] = (
        trips.dest_ref_price
        - trips.local_price
        - np.array(
            [
                compute_freight_inr(
                    r.State,
                    r.road_km,
                    r.same_district,
                    r.local_price,
                    params,
                    commodity=r.Commodity,
                )
                for r in trips.itertuples()
            ]
        )
    )
    assert (trips.b2_margin > hurdle).all()
    meta = (
        frame.drop_duplicates("episode_id")
        .set_index("episode_id")[["origin_market_key", "date"]]
        .reindex(base.index)
    )
    proposals = trips[
        ["episode_id", "date", "b2_margin", "dest_ref_price", *FEATURE_COLS]
    ]
    rows, breakdown, sensitivities, gains = [], [], [], {}
    unmatched = trips.set_index("episode_id").real_no_exact_variety_3d
    groups = frame.drop_duplicates("episode_id").set_index("episode_id")[
        ["State", "Commodity"]
    ]
    for mode in ["none", "margin", "random", "all", "veto_without_forecast"]:
        review = review_proposals(proposals, predict, hurdle=hurdle, mode=mode)
        net = base.copy()
        net.loc[review.index[review.veto]] = 0
        contrast = two_way_mandi_week_bootstrap(
            meta.assign(change=net - base), "change"
        )
        dispatched = len(trips) - int(review.veto.sum())
        delta = net - base
        gains[mode] = delta
        missing_vetoes = int(unmatched.loc[review.index[review.veto]].sum())
        if mode in {"margin", "all"}:
            for column in groups:
                for value, group in delta.groupby(groups[column]):
                    breakdown.append(
                        dict(
                            panel=name,
                            mode=mode,
                            group=column,
                            value=value,
                            episodes=len(group),
                            mean_vs_b2=group.mean(),
                        )
                    )
            for block in (1, 2, 4):
                result = two_way_mandi_week_bootstrap(
                    meta.assign(change=delta), "change", week_block_len=block
                )
                sensitivities.append(
                    dict(
                        panel=name,
                        mode=mode,
                        weeks=block,
                        low=result["ci95_low"],
                        high=result["ci95_high"],
                    )
                )
        rows.append(
            dict(
                panel=name,
                mode=mode,
                episodes=len(base),
                forecast_rows=int(review.forecast_call.sum()),
                vetoes=int(review.veto.sum()),
                unquoted_3d_vetoes=missing_vetoes,
                uniform_missing_offset_to_tie=delta.sum() / missing_vetoes
                if missing_vetoes
                else np.nan,
                dispatches=dispatched,
                mean=float(net.mean()),
                mean_vs_b2=contrast["estimate"],
                paired_low=contrast["ci95_low"],
                paired_high=contrast["ci95_high"],
                loss_pct=100 * (net < 0).sum() / dispatched,
                worst_decile=lower_decile_mean(net.to_numpy()),
            )
        )
    # A random queue of k out of m proposals includes each proposal with probability k/m.
    # Conditioning on the observed batch removes Monte Carlo error from the comparison.
    daily_size = trips.groupby("date").episode_id.transform("size")
    inclusion = pd.Series(
        ((daily_size // 10) / daily_size).to_numpy(), index=trips.episode_id
    )
    random_gain = gains["all"] * inclusion.reindex(base.index, fill_value=0)
    contrasts = []
    for label, comparator in [
        ("expected_uniform", random_gain),
        ("blind_veto", gains["veto_without_forecast"]),
    ]:
        result = two_way_mandi_week_bootstrap(
            meta.assign(change=gains["margin"] - comparator), "change"
        )
        contrasts.append(
            dict(
                panel=name,
                comparator=label,
                comparator_gain_vs_b2=comparator.mean(),
                margin_minus_comparator=result["estimate"],
                low=result["ci95_low"],
                high=result["ci95_high"],
            )
        )
    return rows, breakdown, sensitivities, contrasts


def main():
    cfg = load_config(ROOT)
    splits = cfg["temporal_splits"]
    with (ROOT / "data/interim/forecaster_2024.pkl").open("rb") as f:
        model = pickle.load(f).point_model
    rows, groups, blocks, comparisons = [], [], [], []
    for panel, file, prefix in [
        ("six_state", "candidates_6state", ""),
        ("hp_apple", "candidates_hp_apple_grade", "apple_"),
    ]:
        df = pd.read_parquet(
            ROOT / "data/processed" / (file + ".parquet"),
            filters=[
                ("date", ">=", pd.Timestamp(splits[prefix + "test_start"])),
                ("arrival_date", "<=", pd.Timestamp(splits[prefix + "test_end"])),
            ],
        )
        results, subgroup, intervals, contrasts = evaluate(
            panel, df, model.predict, cfg["agent_defaults"]["screen_hurdle_inr_qtl"]
        )
        rows.extend(results)
        groups.extend(subgroup)
        blocks.extend(intervals)
        comparisons.extend(contrasts)
    pd.DataFrame(comparisons).to_csv(
        ROOT / "final/forecast-direct-contrasts.csv", index=False
    )
    pd.DataFrame(groups).to_csv(ROOT / "final/forecast-subgroups.csv", index=False)
    pd.DataFrame(blocks).to_csv(
        ROOT / "final/forecast-block-sensitivity.csv", index=False
    )
    pd.DataFrame(rows).to_csv(ROOT / "final/budgeted-forecast.csv", index=False)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
