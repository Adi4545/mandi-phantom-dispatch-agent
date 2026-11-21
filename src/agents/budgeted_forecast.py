"""Review a daily batch of fresh-road proposals using a frozen arrival-price tool."""
import numpy as np
import pandas as pd

from src.models.arrival_forecaster import FEATURE_COLS


def review_proposals(
    proposals, predict, *, hurdle=100.0, mode="margin", seed=20261117, rank_loss=None
):
    """Return call and veto decisions on B2 dispatch proposals. Inputs are pre-dispatch fields."""
    if not proposals.episode_id.is_unique:
        raise ValueError("One B2 proposal per episode is required")
    if mode not in {
        "margin",
        "random",
        "all",
        "none",
        "veto_without_forecast",
        "learned",
    }:
        raise ValueError(f"Unknown review mode {mode}")
    rows = proposals.sort_values("episode_id").copy()
    if rows.date.isna().any() or not np.isfinite(rows.b2_margin).all():
        raise ValueError("Every proposal requires a decision date and finite margin")
    if not np.isfinite(rows.dest_ref_price).all() or (rows.dest_ref_price <= 0).any():
        raise ValueError("Positive reference prices are required")
    rows["priority"] = (rows.b2_margin - hurdle) / rows.dest_ref_price
    if mode == "learned":
        if rank_loss is None:
            raise ValueError("Learned routing requires a frozen loss-priority scorer")
        scores = np.asarray(rank_loss(rows), dtype=float)
        if scores.shape != (len(rows),) or not np.isfinite(scores).all():
            raise ValueError(
                "The routing scorer must return one finite priority per proposal"
            )
        rows["priority"] = -scores  # highest expected avoidable loss first
    if mode == "random":
        rows["priority"] = np.random.default_rng(seed).random(len(rows))
    rows = rows.sort_values(["date", "priority", "episode_id"])
    daily = rows.groupby("date")
    review = daily.cumcount() < daily.episode_id.transform("size") // 10
    if mode == "all":
        review[:] = True
    if mode == "none":
        review[:] = False
    calls = review & (mode != "veto_without_forecast")
    veto = review.copy()
    if calls.any():
        chosen = rows.loc[calls]
        returns = np.asarray(predict(chosen[FEATURE_COLS].to_numpy(dtype=float)))
        if returns.shape != (len(chosen),) or not np.isfinite(returns).all():
            raise ValueError(
                "The forecast tool must return one finite prediction per proposal"
            )
        veto.loc[calls] = chosen.b2_margin + chosen.dest_ref_price * returns <= hurdle
    return pd.DataFrame(
        {"episode_id": rows.episode_id, "forecast_call": calls, "veto": veto}
    ).set_index("episode_id")
