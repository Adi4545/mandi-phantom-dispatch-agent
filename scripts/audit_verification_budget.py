"""Daily verification allocation among B1 trips, using a perfect-veto ceiling."""
from pathlib import Path
import json

import numpy as np
import pandas as pd

from src.baselines.dispatch_baselines import eval_b1_naive_screen_greedy
from src.evaluation.payoff_model import PayoffParams

ROOT = Path(__file__).resolve().parents[1]


def evaluate(panel, frame, hurdle):
    costs = PayoffParams()
    assert np.isfinite(frame.real_delta_net_inr).all()
    policy = eval_b1_naive_screen_greedy(frame, hurdle_inr=hurdle, payoff_params=costs)
    trips = policy[policy.is_dispatch].merge(
        frame, left_on=["episode_id", "chosen_dest"], right_on=["episode_id", "dest_market"],
        how="left", validate="one_to_one")
    np.testing.assert_array_equal(trips.delta_net_inr, trips.real_delta_net_inr)
    multiplier = np.where(trips.State.eq("Himachal Pradesh"), costs.hp_km_mult, 1)
    trips["margin"] = trips.screen_dest_price - trips.local_price - costs.freight_base - (
        costs.freight_per_km * multiplier * 1.2 * trips.euclid_km)
    trips["loss_avoided"] = (-trips.delta_net_inr).clip(lower=0)
    pool = trips.groupby("date").episode_id.transform("size")
    trips["quota"] = pool // 10
    rows = []
    for label, col, ascending in [
        ("uniform_random_expected", None, True), ("oldest_variety_quote", "dest_age_days", False),
        ("smallest_screen_margin", "margin", True), ("perfect_priority_ceiling", "loss_avoided", False)
    ]:
        if col is None:
            weights = trips.quota / pool
            total = (weights * trips.loss_avoided).sum()
            calls = int(trips.groupby("date").quota.first().sum())
        else:
            # Average over uniform tie breaks at the daily cutoff, exactly.
            assert trips[col].notna().all()
            ranks = trips.groupby("date")[col]
            first = ranks.rank(method="min", ascending=ascending)
            last = ranks.rank(method="max", ascending=ascending)
            weights = ((trips.quota - first + 1) / (last - first + 1)).clip(0, 1)
            total = (weights * trips.loss_avoided).sum()
            calls = int(trips.groupby("date").quota.first().sum())
            np.testing.assert_allclose(weights.groupby(trips.date).sum(), trips.groupby("date").quota.first())
        rows.append(dict(panel=panel, priority=label, episodes=len(policy), proposed_trips=len(trips),
                         call_slots=calls, ceiling_gain_per_episode_inr_qtl=total/len(policy),
                         ceiling_gain_per_call_inr_qtl=total/calls))
    assert len({row["call_slots"] for row in rows}) == 1
    assert rows[-1]["ceiling_gain_per_episode_inr_qtl"] >= max(r["ceiling_gain_per_episode_inr_qtl"] for r in rows[:-1])
    return rows


def main():
    cfg = json.loads((ROOT / "configs/config.json").read_text())
    splits = cfg["temporal_splits"]
    rows = []
    cols = ["episode_id","date","arrival_date","dest_market","State","dest_age_days","euclid_km","screen_dest_price",
            "local_price","real_delta_net_inr","real_open_d0_delta_net_inr","real_closed_or_no_variety_trap","real_arrival_price_dropped"]
    for label, file, prefix in [("six_state","candidates_6state",""),("hp_apple","candidates_hp_apple_grade","apple_")]:
        frame = pd.read_parquet(ROOT / "data/processed" / (file + ".parquet"), columns=cols)
        mask = (pd.to_datetime(frame.date) >= splits[prefix+"test_start"]) & (pd.to_datetime(frame.arrival_date) <= splits[prefix+"test_end"])
        rows.extend(evaluate(label, frame[mask], cfg["agent_defaults"]["screen_hurdle_inr_qtl"]))
    pd.DataFrame(rows).to_csv(ROOT / "final/verification-budget.csv", index=False)


if __name__ == "__main__":
    main()
