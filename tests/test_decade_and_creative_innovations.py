"""Tests for 10-year 2017-2026 manifests, ZeroCloud edge/satisficing mode, ACI bounds, and vectorized freight."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.evaluation.payoff_model import PayoffParams, compute_realized_dispatch_outcome
from src.evaluation.run_creative_decade_and_modern_experiments import _exact_vectorized_freight_shift
from src.models.arrival_forecaster import CausalArrivalForecaster, FEATURE_COLS
from tests.test_agent_and_leakage import _make_toy_cands


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def test_decade_and_nasa_power_manifests_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    nasa_man = json.loads((root / "data/manifests/nasa_power_manifest.json").read_text())
    dec_man = json.loads((root / "data/manifests/decade_agmarknet_manifest.json").read_text())

    assert nasa_man["n_grid_cells"] == 114
    assert nasa_man["n_rows"] >= 290000
    assert _sha256_file(root / "data/processed/nasa_power_climate_2017_2023.parquet") == nasa_man["sha256"]

    assert dec_man["total_raw_csv_rows_streamed_2017_2026"] > 35_000_000
    assert dec_man["decade_panel_rows"] > 600_000
    assert _sha256_file(root / dec_man["output_parquet"]["path"]) == dec_man["output_parquet"]["sha256"]


def test_zerocloud_live_api_call_savings_and_early_exit() -> None:
    cands = _make_toy_cands()
    # EP_001: Dest_A pruned at T1 (1 live call); Dest_B passes T1 (1 live call), T2 cached (0 live), T3 (1 live), T4 edge CPU (0 live) -> 3 calls total vs 5 full sequential!
    cfg_zc = AgentConfig(safety_margin_inr=100.0, zerocloud_mode=True)
    res_zc, _ = evaluate_mandiguard_vectorized(cands, cfg_zc)
    assert res_zc.loc[res_zc["episode_id"] == "EP_001", "chosen_dest"].iloc[0] == "Dest_B"
    assert res_zc.loc[res_zc["episode_id"] == "EP_001", "tool_calls_total"].iloc[0] == 3

    # Satisficing early-exit stops immediately when a candidate exceeds threshold
    cfg_sat = AgentConfig(safety_margin_inr=100.0, zerocloud_mode=True, early_exit_satisficing_inr=200.0)
    res_sat, _ = evaluate_mandiguard_vectorized(cands, cfg_sat)
    assert res_sat.loc[res_sat["episode_id"] == "EP_001", "chosen_dest"].iloc[0] == "Dest_B"


def test_aci_bounds_and_exact_freight_shift() -> None:
    rng = np.random.default_rng(7)
    dates = pd.date_range("2024-01-01", periods=120, freq="D")
    n = len(dates)
    df = pd.DataFrame({c: rng.normal(0.0, 0.1, size=n) for c in FEATURE_COLS})
    df["tau_days"] = 2
    df["dest_age_days"] = 0
    df["arrival_dow"] = dates.dayofweek
    df["commodity_code"] = 0
    df["state_code"] = 0
    df["Commodity"] = "Onion"
    df["date"] = dates
    df["arrival_date"] = dates + pd.Timedelta(days=2)
    df["target_ret"] = rng.normal(0.0, 0.05, size=n)

    fc = CausalArrivalForecaster(seed=7).fit(df)
    _, _ = fc.predict_point_and_causal_lcb(df, adaptive_gamma=0.005)
    for alpha_v in fc.last_aci_alpha_by_comm.values():
        assert 0.02 <= alpha_v <= 0.45

    # Verify exact algebraic match between _exact_vectorized_freight_shift and compute_realized_dispatch_outcome
    row_base = {
        "State": "Maharashtra",
        "Commodity": "Onion",
        "local_price": 1500.0,
        "road_km": 180.0,
        "truck_hours": 5.5,
        "same_district": False,
        "arrival_lag_days": 2,
        "dest_modal_d0": 2100.0,
        "dest_min_d0": 1900.0,
        "dest_modal_d1": np.nan,
        "dest_min_d1": np.nan,
        "dest_modal_d2": np.nan,
        "dest_min_d2": np.nan,
        "dest_any_var_min_d0": np.nan,
        "dest_any_open_d0": True,
        "route_era5_tmax": 32.0,
        "route_era5_rh": 65.0,
        "route_era5_rain": 0.0,
    }
    o1 = compute_realized_dispatch_outcome(
        row_base["State"],
        row_base["Commodity"],
        row_base["local_price"],
        row_base["road_km"],
        row_base["truck_hours"],
        row_base["same_district"],
        row_base["arrival_lag_days"],
        (row_base["dest_modal_d0"], row_base["dest_min_d0"], np.nan, np.nan, np.nan, np.nan),
        np.nan,
        True,
        32.0,
        65.0,
        0.0,
        params=PayoffParams(freight_mult=1.0),
    )
    o_fpo = compute_realized_dispatch_outcome(
        row_base["State"],
        row_base["Commodity"],
        row_base["local_price"],
        row_base["road_km"],
        row_base["truck_hours"],
        row_base["same_district"],
        row_base["arrival_lag_days"],
        (row_base["dest_modal_d0"], row_base["dest_min_d0"], np.nan, np.nan, np.nan, np.nan),
        np.nan,
        True,
        32.0,
        65.0,
        0.0,
        params=PayoffParams(freight_mult=0.70),
    )
    df_test = pd.DataFrame([{**row_base, "real_delta_net_inr": o1["delta_net_inr"]}])
    shifted = _exact_vectorized_freight_shift(df_test, 0.70)["real_delta_net_inr"].iloc[0]
    assert abs(shifted - o_fpo["delta_net_inr"]) < 1e-9


def test_creative_decade_results_files_non_empty() -> None:
    root = Path(__file__).resolve().parents[1]
    res_dir = root / "results"
    for fn in [
        "exp10_decade_regime_evolution_2017_2026.csv",
        "exp10b_multiyear_training_scaling.csv",
        "exp11_modern_ai_and_aci_showdown.csv",
        "exp12_zerocloud_money_efficient_agent.csv",
        "exp13_outofbox_fpo_pooling_and_spoilage_clock.csv",
        "exp13b_biological_spoilage_clock.csv",
    ]:
        p = res_dir / fn
        assert p.exists(), f"Missing {fn}"
        df = pd.read_csv(p)
        assert len(df) > 0
        if fn in ("exp13_outofbox_fpo_pooling_and_spoilage_clock.csv", "exp13b_biological_spoilage_clock.csv"):
            assert not df.isna().any().any()

    assert (res_dir / "sample_farmer_sms_cards.txt").exists()
    sms_lines = (res_dir / "sample_farmer_sms_cards.txt").read_text().strip().splitlines()
    assert len(sms_lines) == 4
    assert all(len(s) <= 160 for s in sms_lines)

    for fn in ["fig7_decade_2017_2026_evolution.png", "fig8_zerocloud_fpo_and_modern_ai.png"]:
        fp = root / "figures" / fn
        assert fp.exists() and fp.stat().st_size > 20000

    # Ensure Exp 11-13b are typed strictly as Appendix_Illustration and placed after Conclusion
    reg = pd.read_csv(root / "EXPERIMENT_REGISTRY.csv")
    app_rows = reg[reg["experiment_id"].astype(str).str.startswith(("Exp11", "Exp12", "Exp13"))]
    assert len(app_rows) == 7
    assert (app_rows["type"] == "Appendix_Illustration").all()

    ms_text = (root / "paper/manuscript.md").read_text()
    idx_conc = ms_text.index("## 9. Conclusion")
    idx_app = ms_text.index("## Appendix:")
    assert idx_app > idx_conc

    idx_contrib = ms_text.index("### Summary of Contributions")
    idx_rel = ms_text.index("## 2. Related Work")
    contrib_sec = ms_text[idx_contrib:idx_rel]
    assert "Appendix illustrations, not main contributions" in contrib_sec
    assert "90-qtl" not in contrib_sec
    contrib_claims_only = contrib_sec.split("*(Exploratory")[0]
    assert "ZeroCloud" not in contrib_claims_only


def test_official_datagov_parity_and_open_yard_sensitivity() -> None:
    root = Path(__file__).resolve().parents[1]
    man = json.loads((root / "data/manifests/official_datagov_parity_manifest.json").read_text())
    xml_p = root / man["xml_file"]["path"]
    assert xml_p.exists()
    assert _sha256_file(xml_p) == man["xml_file"]["sha256"]

    exp14 = pd.read_csv(root / "results/exp14_official_datagov_parity_audit.csv")
    assert len(exp14) == 1
    assert exp14["min_price_exact_parity_pct"].iloc[0] == 100.0
    assert exp14["max_price_exact_parity_pct"].iloc[0] == 100.0
    assert exp14["modal_price_exact_parity_pct"].iloc[0] >= 99.0

    exp15 = pd.read_csv(root / "results/exp15_missing_data_open_yard_sensitivity.csv")
    assert len(exp15) == 20
    assert not exp15.isna().any().any()
    mg_rows = exp15[exp15["policy"] == "MandiGuard"]
    assert (mg_rows["mg_minus_b1_inr_qtl"] > 70.0).all()

