"""Build strictly lagged, leak-free HP Grade-Explicit Apple candidates (Step 2 / A2-A3, R6).

Reads tracked `data/raw/hp_apple_daily_2025_2026.csv` + `data/processed/osrm_corridor_matrix.parquet`
and reuses the exact leak-free `build_lagged_candidates_from_frames(..., grade_explicit=True)`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from revision.build_variant import build_2024_climatology, build_lagged_candidates_from_frames

ROOT = Path(__file__).resolve().parents[1]


def build_hp_apple(root: Path = ROOT) -> pd.DataFrame:
    hp = pd.read_csv(root / "data/raw/hp_apple_daily_2025_2026.csv")
    raw = pd.DataFrame(
        {
            "State": hp["state"],
            "District": hp["district"],
            "Market": hp["market"],
            "Commodity": hp["commodity"],
            "Variety": hp["variety"],
            "Grade": hp["grade"],
            "Arrival_Date": pd.to_datetime(hp["arrival_date"]),
            "Min_Price": pd.to_numeric(hp["min_price"], errors="coerce"),
            "Max_Price": pd.to_numeric(hp["max_price"], errors="coerce"),
            "Modal_Price": pd.to_numeric(hp["modal_price"], errors="coerce"),
        }
    )
    cor = pd.read_parquet(root / "data/processed/osrm_corridor_matrix.parquet")
    fees = pd.read_csv(root / "data/processed/state_apmc_and_loss_parameters.csv")
    clim_df, _ = build_2024_climatology(root)

    # Origin window 2025-11-21..2026-08-27 ensures full [t+tau, t+tau+2] observability inside 2026-09-01
    cands, counts = build_lagged_candidates_from_frames(
        raw_df=raw,
        corridors_df=cor,
        fee_params_df=fees,
        clim_df=clim_df,
        grade_explicit=True,
        min_origin_date="2025-11-21",
        max_origin_date="2026-08-27",
    )
    out_dir = root / "revision" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "hp_apple_cleaning_counts.json").write_text(json.dumps(counts, indent=2))
    cands.to_parquet(out_dir / "lagged_hp_apple_candidates.parquet", index=False)
    print(json.dumps(counts, indent=2))
    print("wrote lagged_hp_apple_candidates.parquet:", len(cands), "rows,", cands["episode_id"].nunique(), "episodes")
    return cands


if __name__ == "__main__":
    build_hp_apple()
