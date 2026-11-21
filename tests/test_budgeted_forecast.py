import numpy as np
import pandas as pd
from src.agents.budgeted_forecast import review_proposals
from src.models.arrival_forecaster import FEATURE_COLS


def test_budget_and_tool_response_on_two_days():
    rows = pd.DataFrame(0.0, index=range(29), columns=FEATURE_COLS)
    rows["episode_id"] = np.arange(len(rows))
    rows["date"] = [1] * 20 + [2] * 9
    rows["dest_ref_price"] = 1000.0
    rows["b2_margin"] = 101 + np.arange(len(rows))
    sizes = []

    def forecast(features):
        sizes.append(len(features))
        return np.array([-0.1, 0.1])

    out = review_proposals(rows.sample(frac=1, random_state=3), forecast)
    assert sizes == [2]
    assert set(out.index[out.forecast_call]) == {0, 1}
    assert list(out.index[out.veto]) == [0]
    abstain = review_proposals(rows, None, mode="veto_without_forecast")
    assert not abstain.forecast_call.any()
    assert set(abstain.index[abstain.veto]) == {0, 1}


def test_learned_priority_calls_tool_only_on_budgeted_rows():
    # The largest learned scores tie on IDs 17-19. The first two IDs win.
    rows = pd.DataFrame(0.0, index=range(20), columns=FEATURE_COLS)
    rows["episode_id"] = np.arange(len(rows))
    rows["date"] = pd.Timestamp("2026-04-03")
    rows["b2_margin"] = 150.0
    rows["dest_ref_price"] = 1000.0
    rows["month_sin"] = rows.episode_id / 20.0
    seen = []

    def forecast(features):
        seen.extend(features[:, FEATURE_COLS.index("month_sin")])
        return np.array([-0.1, 0.2])

    def priority(batch):
        return np.minimum(batch.episode_id, 17)

    result = review_proposals(
        rows.sample(frac=1, random_state=55),
        forecast,
        mode="learned",
        rank_loss=priority,
    )
    assert set(result.index[result.forecast_call]) == {17, 18}
    assert set(result.index[result.veto]) == {17}
    assert seen == [17 / 20, 18 / 20]
