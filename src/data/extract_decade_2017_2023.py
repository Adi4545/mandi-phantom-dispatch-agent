"""Expand AGMARKNET + Official Climate to nearly 10 full years (2017-01-01 .. 2026-04-13).

1. Streams 2017.csv .. 2023.csv over HTTPS via `stream_filter_csv` with full-stream SHA-256 verification,
   reuses `parse_and_clean` (`src.data.extract_agmarknet_multistate`), restricts to the fixed 178-mandi panel,
   and merges with 2024-2026 into `data/raw/agmarknet_6state_decade_2017_2026.parquet`.
2. Fetches official US Govt NASA POWER daily agroclimatology (2017-01-01..2023-12-31) across all 114
   deduplicated 0.5-deg grid cells (`mandi_coordinates.parquet`) and applies the causal <=t 2024-fitted
   Ridge nowcaster for causal day-t decision forecasts.
"""

from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import requests

from src.data.extract_agmarknet_multistate import BASE_HF, parse_and_clean, stream_filter_csv
from src.data.fetch_climate_data import fit_causal_era5_nowcaster, predict_causal_nowcast

DECADE_FILES_2017_2023 = [
    ("2017", f"{BASE_HF}/2017.csv"),
    ("2018", f"{BASE_HF}/2018.csv"),
    ("2019", f"{BASE_HF}/2019.csv"),
    ("2020", f"{BASE_HF}/2020.csv"),
    ("2021", f"{BASE_HF}/2021.csv"),
    ("2022", f"{BASE_HF}/2022.csv"),
    ("2023", f"{BASE_HF}/2023.csv"),
]

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _fetch_nasa_cell(glat: float, glon: float, start: str = "20170101", end: str = "20231231") -> pd.DataFrame:
    params = {
        "parameters": "T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M",
        "community": "AG",
        "longitude": f"{glon:.2f}",
        "latitude": f"{glat:.2f}",
        "start": start,
        "end": end,
        "format": "JSON",
    }
    for attempt in range(5):
        try:
            resp = requests.get(NASA_POWER_URL, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=35)
            if resp.status_code == 200:
                prm = resp.json()["properties"]["parameter"]
                dates = sorted(prm["T2M_MAX"].keys())
                df = pd.DataFrame(
                    {
                        "grid_lat": glat,
                        "grid_lon": glon,
                        "date": pd.to_datetime(dates, format="%Y%m%d"),
                        "era5_tmax": [prm["T2M_MAX"][d] for d in dates],
                        "era5_tmin": [prm["T2M_MIN"][d] for d in dates],
                        "era5_rain_mm": [prm["PRECTOTCORR"][d] for d in dates],
                        "era5_rh_mean": [prm["RH2M"][d] for d in dates],
                    }
                )
                for c in ["era5_tmax", "era5_tmin", "era5_rain_mm", "era5_rh_mean"]:
                    df[c] = pd.to_numeric(df[c], errors="coerce").replace(-999.0, np.nan)
                return df
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"NASA POWER failed after retries for ({glat}, {glon})")


def fetch_nasa_power_2017_2023(root: Path, coords_df: pd.DataFrame) -> None:
    cache_path = root / "data/interim/nasa_power_2017_2023_cache.parquet"
    out_path = root / "data/processed/nasa_power_climate_2017_2023.parquet"
    manifest_path = root / "data/manifests/nasa_power_manifest.json"

    g05 = (
        coords_df.assign(grid_lat=(coords_df["lat"] * 2.0).round() / 2.0, grid_lon=(coords_df["lon"] * 2.0).round() / 2.0)[
            ["grid_lat", "grid_lon"]
        ]
        .drop_duplicates()
        .sort_values(["grid_lat", "grid_lon"])
        .reset_index(drop=True)
    )

    existing = pd.read_parquet(cache_path) if cache_path.exists() else pd.DataFrame()
    done_keys = set(zip(existing["grid_lat"], existing["grid_lon"])) if len(existing) else set()
    todo = [((float(r.grid_lat), float(r.grid_lon))) for _, r in g05.iterrows() if (r.grid_lat, r.grid_lon) not in done_keys]
    print(f"[NASA POWER] 0.5-deg grids={len(g05)}, cached={len(done_keys)}, remaining={len(todo)}", flush=True)

    frames = [existing] if len(existing) else []
    if todo:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futs = {pool.submit(_fetch_nasa_cell, lat, lon): (lat, lon) for lat, lon in todo}
            completed = 0
            for fut in as_completed(futs):
                frames.append(fut.result())
                completed += 1
                if completed % 20 == 0 or completed == len(todo):
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    pd.concat(frames, ignore_index=True).to_parquet(cache_path, index=False)
                    print(f"  [NASA POWER] Saved {completed}/{len(todo)} cells", flush=True)

    nasa_df = pd.concat(frames, ignore_index=True).drop_duplicates(["grid_lat", "grid_lon", "date"]).sort_values(
        ["grid_lat", "grid_lon", "date"]
    )
    val_cols = ["era5_tmax", "era5_tmin", "era5_rain_mm", "era5_rh_mean"]
    raw_nulls = {c: float(nasa_df[c].isna().mean()) for c in val_cols}
    nasa_df[val_cols] = nasa_df.groupby(["grid_lat", "grid_lon"])[val_cols].ffill().bfill()
    assert all(nasa_df[c].isna().mean() == 0.0 for c in val_cols)

    # Fit causal <=t nowcaster ONLY on 2024 overlapping ERA5+NWP data cleanly, then score 2017-2023 <=t
    era5_24 = pd.read_parquet(root / "data/interim/weather_cache_era5.parquet").drop_duplicates(["grid_lat", "grid_lon", "date"])
    fc_24 = pd.read_parquet(root / "data/interim/weather_cache_fc.parquet").drop_duplicates(["grid_lat", "grid_lon", "date"])
    nowcaster, _ = fit_causal_era5_nowcaster(era5_24, fc_24, train_end="2024-12-31")

    fc_1723 = predict_causal_nowcast(nasa_df, nowcaster)
    merged = nasa_df.merge(fc_1723.drop(columns=["fc_source"]), on=["grid_lat", "grid_lon", "date"], how="inner")
    merged["fc_source"] = "nasa_power_plus_causal_2024_nowcast_le_t"
    merged.to_parquet(out_path, index=False, compression="zstd")

    man = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "url": NASA_POWER_URL,
        "community": "AG",
        "grid_resolution_deg": 0.5,
        "n_grid_cells": int(merged.groupby(["grid_lat", "grid_lon"]).ngroups),
        "n_rows": int(len(merged)),
        "date_min": str(merged["date"].min().date()),
        "date_max": str(merged["date"].max().date()),
        "raw_null_rates": raw_nulls,
        "sha256": _sha256_file(out_path),
    }
    manifest_path.write_text(json.dumps(man, indent=2))
    print(f"=== NASA POWER 2017-2023 SAVED: {len(merged):,} rows across {man['n_grid_cells']} grid cells ===", flush=True)


def extract_agmarknet_2017_2026(root: Path) -> None:
    panel_2426 = pd.read_parquet(root / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet")
    fixed_mkts = panel_2426[["State", "Market"]].drop_duplicates().copy()
    print(f"[AGMARKNET Decade] Fixed 2024-ranked core markets: {len(fixed_mkts)}", flush=True)

    dfs: List[pd.DataFrame] = []
    file_metas: List[Dict] = []
    for tag, url in DECADE_FILES_2017_2023:
        df_part, meta = stream_filter_csv(tag, url, workers=6)
        dfs.append(df_part)
        file_metas.append(meta)

    raw_1723 = pd.concat(dfs, ignore_index=True)
    clean_1723, clean_stats = parse_and_clean(raw_1723, min_date="2017-01-01", max_date="2023-12-31")
    panel_1723 = clean_1723.merge(fixed_mkts, on=["State", "Market"], how="inner")

    # Harmonize column subset cleanly and concatenate with 2024-2026
    keep_cols = [c for c in panel_2426.columns if c in panel_1723.columns]
    decade_panel = (
        pd.concat([panel_1723[keep_cols], panel_2426[keep_cols]], ignore_index=True)
        .drop_duplicates(subset=["State", "District", "Market", "Commodity", "Variety", "Grade", "Arrival_Date", "Min_Price", "Max_Price", "Modal_Price"])
        .sort_values(["State", "Market", "Commodity", "Variety", "Arrival_Date"])
        .reset_index(drop=True)
    )
    out_decade = root / "data/raw/agmarknet_6state_decade_2017_2026.parquet"
    decade_panel.to_parquet(out_decade, index=False, compression="zstd")

    man_2426 = json.loads((root / "data/manifests/agmarknet_extract_manifest.json").read_text())
    raw_rows_2017_2023 = sum(m["total_csv_data_rows"] for m in file_metas)
    raw_rows_2024_2026 = sum(m["total_csv_data_rows"] for m in man_2426["sources"])

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "sources_2017_2023": file_metas,
        "sources_2024_2026_ref": man_2426["sources"],
        "total_raw_csv_rows_streamed_2017_2026": int(raw_rows_2017_2023 + raw_rows_2024_2026),
        "clean_2017_2023_stats": clean_stats,
        "panel_178mkts_2017_2023_rows": int(len(panel_1723)),
        "panel_178mkts_2024_2026_rows": int(len(panel_2426)),
        "decade_panel_rows": int(len(decade_panel)),
        "decade_date_min": str(pd.to_datetime(decade_panel["Arrival_Date"]).min().date()),
        "decade_date_max": str(pd.to_datetime(decade_panel["Arrival_Date"]).max().date()),
        "decade_rows_by_year": pd.to_datetime(decade_panel["Arrival_Date"]).dt.year.value_counts().sort_index().to_dict(),
        "output_parquet": {
            "path": str(out_decade.relative_to(root)),
            "sha256": _sha256_file(out_decade),
            "bytes": out_decade.stat().st_size,
        },
    }
    (root / "data/manifests/decade_agmarknet_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(
        f"=== 10-YEAR AGMARKNET COMPLETE: {manifest['total_raw_csv_rows_streamed_2017_2026']:,} total raw rows streamed "
        f"-> {len(decade_panel):,} clean decade panel rows ({manifest['decade_date_min']}..{manifest['decade_date_max']}) ===",
        flush=True,
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    coords_df = pd.read_parquet(root / "data/processed/mandi_coordinates.parquet")
    fetch_nasa_power_2017_2023(root, coords_df)
    extract_agmarknet_2017_2026(root)


if __name__ == "__main__":
    main()
