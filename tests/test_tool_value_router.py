import numpy as np
import pandas as pd

from scripts.tool_value_router import exact_random, scheduled
from src.models.arrival_forecaster import FEATURE_COLS


def test_random_expectation_spends_only_each_days_budget():
    dates = pd.to_datetime(["2026-01-01"] * 21 + ["2026-01-02"] * 8)
    context = pd.DataFrame(
        0.0, index=pd.Index(range(29), name="episode_id"), columns=FEATURE_COLS
    )
    context["date"] = dates
    context["fresh_net_margin_inr"] = 111.0
    context["dest_ref_price"] = 1000.0
    negative = np.arange(len(context)) % 2 == 0
    context[FEATURE_COLS[0]] = np.where(negative, -0.1, 0.1)

    class Forecast:
        def predict(self, x):
            assert len(x) <= 2
            return x[:, 0]

    expected, unique_queries = exact_random(context, Forecast())
    np.testing.assert_allclose(
        expected, np.where((np.arange(29) < 21) & negative, 2 / 21, 0)
    )
    assert unique_queries == 21
    chosen = scheduled(context, np.arange(len(context)))
    assert set(chosen) == {19, 20}
