"""Anti-leakage, provenance, and configuration helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict

import pandas as pd


def load_config(root: Path | None = None) -> Dict:
    if root is None:
        root = Path(__file__).resolve().parents[2]
    return json.loads((root / "configs/config.json").read_text())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_no_future_leakage_dates(train_df: pd.DataFrame, val_df: pd.DataFrame, cfg: Dict) -> None:
    """Verify strict temporal separation between training, validation, and holdout test windows."""
    splits = cfg["temporal_splits"]
    tr_max = pd.to_datetime(train_df["date"]).max()
    va_min = pd.to_datetime(val_df["date"]).min()
    va_max = pd.to_datetime(val_df["date"]).max()
    assert tr_max <= pd.to_datetime(splits["train_end"]), f"Train leakage past {splits['train_end']}: {tr_max}"
    assert va_min >= pd.to_datetime(splits["val_start"]), f"Val overlaps train: {va_min}"
    assert va_max <= pd.to_datetime(splits["val_end"]), f"Val leakage past {splits['val_end']}: {va_max}"
    if "arrival_date" in train_df.columns:
        assert pd.to_datetime(train_df["arrival_date"]).max() <= pd.to_datetime(splits["train_end"]), (
            "Training arrival_date extends into validation window"
        )
    if "arrival_date" in val_df.columns:
        assert pd.to_datetime(val_df["arrival_date"]).max() <= pd.to_datetime(splits["val_end"]), (
            "Validation arrival_date extends into holdout window"
        )
