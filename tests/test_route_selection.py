import numpy as np
import pandas as pd
import pytest

from src.baselines.dispatch_baselines import (
    eval_b1_naive_screen_greedy,
    eval_b2_fresh_road_greedy,
    eval_b3_ml_point_dispatch,
    eval_b6_heuristic_bucket_router,
)


@pytest.mark.parametrize("evaluate", [
    eval_b1_naive_screen_greedy, eval_b2_fresh_road_greedy,
    eval_b3_ml_point_dispatch, eval_b6_heuristic_bucket_router,
])
def test_winning_destination_retains_its_own_missing_arrival(evaluate):
    # An equally ranked second market has an arrival quote. Ties go to market A.
    common = dict(episode_id=1, State="Punjab", Commodity="Potato", euclid_km=3,
                  local_price=400, road_km=5, same_district=True, dest_age_days=0,
                  screen_dest_price=1400, screen_spread=1000, dest_ref_price=1400,
                  pred_ret=0, route_fc_tmax=24, route_fc_rain=0, dest_open_prob_14d=1)
    candidates = pd.DataFrame([
        dict(common, dest_market="B", real_delta_net_inr=850,
             real_closed_or_no_variety_trap=False, real_arrival_price_dropped=False,
             real_open_d0_delta_net_inr=850),
        dict(common, dest_market="A", real_delta_net_inr=-100,
             real_closed_or_no_variety_trap=True, real_arrival_price_dropped=True,
             real_open_d0_delta_net_inr=np.nan),
    ], index=[17, 32])
    result = evaluate(candidates).iloc[0]
    assert result.is_dispatch
    assert result.chosen_dest == "A"
    assert result.delta_net_inr == -100
    assert result.is_closed_trap and result.is_phantom_loss and result.is_arrival_drop
    assert pd.isna(result.open_d0_delta_net_inr)


def test_missing_day0_for_every_selected_route_yields_undefined_mean():
    from src.evaluation.run_all_experiments import _summarize_policy

    decisions = pd.DataFrame([dict(is_dispatch=True, delta_net_inr=-80.0,
                                   open_d0_delta_net_inr=np.nan, is_phantom_loss=True,
                                   is_closed_trap=True, tool_calls_total=0)])
    assert pd.isna(_summarize_policy("B1", decisions)["open_d0_mean_delta_net_inr"])
