"""Unit tests verifying 100%-authentic Govt survey manifests, state APMC rules, NABCONS spoilage, and weather causality."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.fetch_climate_data import build_causal_nowcast_features
from src.evaluation.payoff_model import (
    BASE_SPOIL_24H,
    PayoffParams,
    compute_freight_inr,
    get_statutory_fee_rate,
)


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_govt_survey_and_climate_manifests_integrity() -> None:
    root = Path(__file__).resolve().parents[1]
    govt_man = json.loads((root / "data/manifests/govt_survey_manifest.json").read_text())
    clim_man = json.loads((root / "data/manifests/climate_manifest.json").read_text())

    # Check CSV & JSON outputs against logged SHA-256 digests
    for item in govt_man["outputs"].values():
        p = root / item["path"]
        assert p.exists()
        assert _sha256_file(p) == item["sha256"]

    csv_df = pd.read_csv(root / "data/processed/state_apmc_and_loss_parameters.csv")
    assert len(csv_df) == 24  # 6 states x 4 commodities
    assert set(csv_df["State"].unique()) == {
        "Maharashtra",
        "Uttar Pradesh",
        "Karnataka",
        "Madhya Pradesh",
        "Gujarat",
        "Himachal Pradesh",
    }

    assert clim_man["n_grid_cells"] == 145
    assert clim_man["n_era5_realized_cells"] == 145
    assert all(v == 0.0 for v in clim_man["null_rates_after_causal_ffill"].values())
    assert _sha256_file(root / "data/processed/mandi_weather_2024_2026.parquet") == clim_man["sha256"]


def test_statutory_fees_and_nabcons_rates() -> None:
    params_stat = PayoffParams(use_state_statutory_fees=True)
    params_unif = PayoffParams(use_state_statutory_fees=False)

    # NABCONS (2022) Annexure-II Table-2 market-level rates
    assert abs(BASE_SPOIL_24H["Tomato"] - 0.0325) < 1e-12
    assert abs(BASE_SPOIL_24H["Onion"] - 0.0196) < 1e-12
    assert abs(BASE_SPOIL_24H["Apple"] - 0.0164) < 1e-12
    assert abs(BASE_SPOIL_24H["Potato"] - 0.0086) < 1e-12

    # Statutory state fees (PIB relid=154554: HP exempt except Apple; KA/GJ 0.5% user charge; UP/MP 1.5%)
    assert abs(get_statutory_fee_rate("Karnataka", "Tomato", params_stat) - 0.005) < 1e-12
    assert abs(get_statutory_fee_rate("Himachal Pradesh", "Tomato", params_stat) - 0.005) < 1e-12
    assert abs(get_statutory_fee_rate("Himachal Pradesh", "Apple", params_stat) - 0.010) < 1e-12
    assert abs(get_statutory_fee_rate("Uttar Pradesh", "Potato", params_stat) - 0.015) < 1e-12
    assert abs(get_statutory_fee_rate("Karnataka", "Tomato", params_unif) - 0.015) < 1e-12

    f_ka_tom = compute_freight_inr("Karnataka", 100.0, False, 2000.0, params_stat, commodity="Tomato")
    f_up_tom = compute_freight_inr("Uttar Pradesh", 100.0, False, 2000.0, params_stat, commodity="Tomato")
    assert abs((f_up_tom - f_ka_tom) - 20.0) < 1e-9  # 1.5% - 0.5% = 1.0% of 2000 = Rs 20


def test_causal_weather_nowcast_features_zero_future_leakage() -> None:
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    df1 = pd.DataFrame(
        {
            "grid_lat": [31.1] * 10,
            "grid_lon": [77.2] * 10,
            "date": dates,
            "era5_tmax": np.linspace(15.0, 24.0, 10),
            "era5_tmin": np.linspace(5.0, 12.0, 10),
            "era5_rain_mm": [0.0, 2.0, 0.0, 5.0, 0.0, 1.0, 0.0, 0.0, 10.0, 0.0],
            "era5_rh_mean": [60.0] * 10,
        }
    )
    df2 = df1.copy()
    # Perturb ONLY future days >= index 5
    df2.loc[5:, "era5_tmax"] = 45.0
    df2.loc[5:, "era5_rain_mm"] = 120.0

    f1 = build_causal_nowcast_features(df1)
    f2 = build_causal_nowcast_features(df2)
    cols = ["era5_tmax", "era5_tmax_lag1", "era5_tmax_3d_mean", "era5_rain_mm", "era5_rain_lag1"]
    assert np.allclose(f1.loc[:4, cols].to_numpy(), f2.loc[:4, cols].to_numpy(), atol=1e-15)
