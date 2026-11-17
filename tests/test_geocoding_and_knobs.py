"""Unit tests verifying geocoding district distance guards, OSRM lags, and tool-budget caps."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from tests.test_agent_and_leakage import _make_toy_cands


def test_saved_coordinates_and_corridors_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    coords = pd.read_parquet(root / "data/processed/mandi_coordinates.parquet")
    cor = pd.read_parquet(root / "data/processed/osrm_corridor_matrix.parquet")

    assert len(coords) >= 178
    assert coords["lat"].notna().all() and coords["lon"].notna().all()
    assert (coords["dist_to_district_km"] <= 110.0).all()
    # Verify our Gonda & Ahmednagar & Neemuch fixes landed in the right geographic range
    ahm = coords[(coords["State"] == "Maharashtra") & (coords["District"] == "Ahmednagar")].iloc[0]
    assert 18.0 <= ahm["district_lat"] <= 20.0 and 73.5 <= ahm["district_lon"] <= 75.6
    gnd = coords[(coords["State"] == "Uttar Pradesh") & (coords["District"] == "Gonda")].iloc[0]
    assert 26.5 <= gnd["district_lat"] <= 27.6 and 81.2 <= gnd["district_lon"] <= 82.6
    nmh = coords[(coords["State"] == "Madhya Pradesh") & (coords["District"] == "Neemuch")].iloc[0]
    assert 24.0 <= nmh["district_lat"] <= 25.0 and 74.3 <= nmh["district_lon"] <= 75.5

    assert set(cor["arrival_lag_days"].unique()) == {1, 2, 3}
    assert (cor["road_km"] >= 15.0).all() and (cor["road_km"] <= 500.0).all()
    assert (cor["road_km"] >= cor["euclid_km"] * 0.95).all()


def test_tool_budget_hard_cap_and_ablation_flags() -> None:
    cands = _make_toy_cands()
    # Cap budget at 2 tool calls per episode -> EP_001 uses 1 call for Dest_A (prune), 1 call for Dest_B T1, hits cap before T2!
    cfg_b2 = AgentConfig(max_tool_calls_per_episode=2)
    res, _ = evaluate_mandiguard_vectorized(cands, cfg_b2)
    assert (res["tool_calls_total"] <= 2).all()
    assert res.loc[res["episode_id"] == "EP_001", "action"].iloc[0] == "REFUSE_PHANTOM_SPREAD"

    # Disable T1 -> naive screen trap Dest_A is no longer pruned by T1 and gets dispatched!
    cfg_no_t1 = AgentConfig(use_t1=False, use_t3_weather=False, use_t4_lcb=False, safety_margin_inr=100.0)
    res_no_t1, _ = evaluate_mandiguard_vectorized(cands, cfg_no_t1)
    assert res_no_t1.loc[res_no_t1["episode_id"] == "EP_001", "chosen_dest"].iloc[0] == "Dest_A"
