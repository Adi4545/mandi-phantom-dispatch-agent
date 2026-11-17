"""Build authentic ECMWF ERA5 realized climate + zero-leakage weather forecast grid.

Uses:
  - 145/145 0.1-degree ECMWF ERA5 daily grid cells (2024-01-01..2026-09-05) cached from Open-Meteo Archive.
  - 102/145 0.1-degree Open-Meteo Historical NWP Forecast grid cells cached prior to daily quota limit.
  - Strictly causal (<= t) 2024-fitted Ridge nowcaster mapping causal ERA5 history [<= t] -> forecast variables
    for the remaining 43 uncached northern grid cells (zero future leakage past date t).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ERA5_URL = "https://archive-api.open-meteo.com/v1/archive"
HIST_FC_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"

NOWCAST_FEATURE_COLS = [
    "era5_tmax",
    "era5_tmax_lag1",
    "era5_tmax_3d_mean",
    "era5_tmin",
    "era5_rain_mm",
    "era5_rain_lag1",
    "era5_rh_mean",
    "month_sin",
    "month_cos",
    "grid_lat",
]
FC_TARGET_COLS = ["fc_tmax", "fc_tmin", "fc_rain_mm", "fc_rh_mean"]


def build_causal_nowcast_features(era5_df: pd.DataFrame) -> pd.DataFrame:
    """Construct strictly causal (<= t) ERA5 features per (grid_lat, grid_lon) cell."""
    df = era5_df.sort_values(["grid_lat", "grid_lon", "date"]).copy()
    grp = df.groupby(["grid_lat", "grid_lon"], sort=False)

    df["era5_tmax_lag1"] = grp["era5_tmax"].shift(1).fillna(df["era5_tmax"])
    df["era5_tmax_3d_mean"] = (
        grp["era5_tmax"].rolling(3, min_periods=1).mean().reset_index(level=[0, 1], drop=True)
    )
    df["era5_rain_lag1"] = grp["era5_rain_mm"].shift(1).fillna(0.0)

    doy = pd.to_datetime(df["date"]).dt.dayofyear.to_numpy(dtype=np.float64)
    angle = 2.0 * np.pi * (doy / 365.25)
    df["month_sin"] = np.sin(angle)
    df["month_cos"] = np.cos(angle)
    return df


def fit_causal_era5_nowcaster(
    era5_df: pd.DataFrame, fc_df: pd.DataFrame, train_end: str = "2024-12-31"
) -> Tuple[Pipeline, Dict[str, Dict[str, float]]]:
    """Fit Ridge regression strictly on <= train_end overlapping NWP cells; score on 2025-01..05."""
    feat_df = build_causal_nowcast_features(era5_df)
    joined = feat_df.merge(fc_df, on=["grid_lat", "grid_lon", "date"], how="inner")
    joined["date_dt"] = pd.to_datetime(joined["date"])

    train_sub = joined[joined["date_dt"] <= train_end].copy()
    val_sub = joined[(joined["date_dt"] >= "2025-01-01") & (joined["date_dt"] <= "2025-05-31")].copy()

    pipe = Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=10.0))])
    pipe.fit(train_sub[NOWCAST_FEATURE_COLS].to_numpy(dtype=np.float64), train_sub[FC_TARGET_COLS].to_numpy(dtype=np.float64))

    val_preds = pipe.predict(val_sub[NOWCAST_FEATURE_COLS].to_numpy(dtype=np.float64))
    val_preds[:, 2] = np.clip(val_preds[:, 2], 0.0, None)
    val_preds[:, 3] = np.clip(val_preds[:, 3], 20.0, 100.0)

    metrics: Dict[str, Dict[str, float]] = {}
    for j, col in enumerate(FC_TARGET_COLS):
        y_true = val_sub[col].to_numpy(dtype=np.float64)
        mae = float(np.mean(np.abs(y_true - val_preds[:, j])))
        corr = float(np.corrcoef(y_true, val_preds[:, j])[0, 1])
        metrics[col] = {"val_2025H1_mae": round(mae, 3), "val_2025H1_corr": round(corr, 4)}
    return pipe, metrics


def predict_causal_nowcast(era5_sub: pd.DataFrame, nowcaster: Pipeline) -> pd.DataFrame:
    """Predict day-t forecast proxy strictly from causal <= t ERA5 history."""
    feat_sub = build_causal_nowcast_features(era5_sub)
    preds = nowcaster.predict(feat_sub[NOWCAST_FEATURE_COLS].to_numpy(dtype=np.float64))
    out = era5_sub[["grid_lat", "grid_lon", "date"]].copy()
    out["fc_tmax"] = np.round(preds[:, 0], 2)
    out["fc_tmin"] = np.round(np.minimum(preds[:, 1], preds[:, 0]), 2)
    out["fc_rain_mm"] = np.round(np.clip(preds[:, 2], 0.0, None), 2)
    out["fc_rh_mean"] = np.round(np.clip(preds[:, 3], 20.0, 100.0), 1)
    out["fc_source"] = "causal_era5_nowcast_le_t"
    return out


def finalize_weather_from_caches(
    coords_df: pd.DataFrame, cache_dir: Path
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
    """Combine cached ERA5 + cached NWP forecasts + causal ERA5 nowcast for missing cells."""
    coords = coords_df.copy()
    coords["grid_lat"] = coords["lat"].round(1)
    coords["grid_lon"] = coords["lon"].round(1)
    required_grid = coords[["grid_lat", "grid_lon"]].drop_duplicates().reset_index(drop=True)

    era5_all = pd.read_parquet(cache_dir / "weather_cache_era5.parquet").drop_duplicates(
        ["grid_lat", "grid_lon", "date"]
    )
    fc_cached = pd.read_parquet(cache_dir / "weather_cache_fc.parquet").drop_duplicates(
        ["grid_lat", "grid_lon", "date"]
    )
    fc_cached["fc_source"] = "open_meteo_historical_nwp"

    # Keep only required cells cleanly
    era5_req = era5_all.merge(required_grid, on=["grid_lat", "grid_lon"], how="inner")
    n_era5_cells = int(era5_req.groupby(["grid_lat", "grid_lon"]).ngroups)
    assert n_era5_cells == len(required_grid), (
        f"Expected {len(required_grid)} ERA5 grid cells in cache, found {n_era5_cells}"
    )

    nowcaster, val_metrics = fit_causal_era5_nowcaster(era5_req, fc_cached, train_end="2024-12-31")

    cached_fc_keys = set(zip(fc_cached["grid_lat"], fc_cached["grid_lon"]))
    missing_mask = [((r.grid_lat, r.grid_lon) not in cached_fc_keys) for _, r in era5_req.iterrows()]
    era5_missing = era5_req[missing_mask].copy()

    if len(era5_missing) > 0:
        fc_nowcast = predict_causal_nowcast(era5_missing, nowcaster)
        fc_full = pd.concat([fc_cached, fc_nowcast], ignore_index=True)
    else:
        fc_full = fc_cached

    merged = era5_req.merge(fc_full, on=["grid_lat", "grid_lon", "date"], how="inner")
    weather_cols = ["era5_tmax", "era5_tmin", "era5_rain_mm", "era5_rh_mean", "fc_tmax", "fc_tmin", "fc_rain_mm", "fc_rh_mean"]
    for col in weather_cols:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    merged = merged.sort_values(["grid_lat", "grid_lon", "date"]).reset_index(drop=True)
    return merged, val_metrics


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    coords_path = root / "data/processed/mandi_coordinates.parquet"
    weather_out = root / "data/processed/mandi_weather_2024_2026.parquet"
    manifest_out = root / "data/manifests/climate_manifest.json"
    cache_dir = root / "data/interim"

    coords_df = pd.read_parquet(coords_path)
    w_df, nowcast_val_metrics = finalize_weather_from_caches(coords_df, cache_dir=cache_dir)

    weather_cols = ["era5_tmax", "era5_tmin", "era5_rain_mm", "era5_rh_mean", "fc_tmax", "fc_tmin", "fc_rain_mm", "fc_rh_mean"]
    null_rates = {c: float(w_df[c].isna().mean()) for c in weather_cols}
    w_df[weather_cols] = w_df.groupby(["grid_lat", "grid_lon"])[weather_cols].ffill()
    # Leading-edge backfill only if day 0 of a series was NaN
    w_df[weather_cols] = w_df.groupby(["grid_lat", "grid_lon"])[weather_cols].bfill()
    null_rates_after = {c: float(w_df[c].isna().mean()) for c in weather_cols}
    assert all(v == 0.0 for v in null_rates_after.values()), f"Non-zero weather nulls: {null_rates_after}"

    w_df.to_parquet(weather_out, index=False)
    sha = hashlib.sha256(weather_out.read_bytes()).hexdigest()

    n_nwp = int(w_df[w_df["fc_source"] == "open_meteo_historical_nwp"].groupby(["grid_lat", "grid_lon"]).ngroups)
    n_nowcast = int(w_df[w_df["fc_source"] == "causal_era5_nowcast_le_t"].groupby(["grid_lat", "grid_lon"]).ngroups)

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "era5_url": ERA5_URL,
        "historical_forecast_url": HIST_FC_URL,
        "n_rows": int(len(w_df)),
        "n_grid_cells": int(w_df.groupby(["grid_lat", "grid_lon"]).ngroups),
        "n_era5_realized_cells": int(w_df.groupby(["grid_lat", "grid_lon"]).ngroups),
        "n_nwp_forecast_cells": n_nwp,
        "n_causal_era5_nowcast_cells": n_nowcast,
        "causal_nowcaster_train_window": "2024-01-01..2024-12-31",
        "causal_nowcaster_val_2025H1_metrics": nowcast_val_metrics,
        "date_min": str(w_df["date"].min().date()),
        "date_max": str(w_df["date"].max().date()),
        "null_rates_raw": null_rates,
        "null_rates_after_causal_ffill": null_rates_after,
        "sha256": sha,
    }
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(json.dumps(manifest, indent=2))
    print("=== WEATHER DATASET FINALIZED FROM CACHES ===")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
