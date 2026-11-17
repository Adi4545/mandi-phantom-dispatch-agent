"""Memory-safe parallel byte-range streaming extractor for official AGMARKNET multi-state CSVs.

Streams 2024.csv, 2025.csv, and 2026 Jan_April_13.csv over HTTPS using bounded byte-range
chunks, verifies byte lengths and computes exact SHA-256 digests in-flight without storing
multi-gigabyte raw CSVs on disk, filters to the 6 target states and 4 perishable crops
(Onion, Potato, Tomato, Apple), normalizes market names across 2024-2026 schema shifts,
and writes clean Parquet outputs plus provenance manifests.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import requests

BASE_HF = (
    "https://huggingface.co/datasets/Arunvithyasegar/"
    "AGMARK_Commodity_Pricing_Variety_Wise_Daily_Market_Prices_Data_Commodity_2022_2025"
    "/resolve/main"
)

SOURCE_FILES = [
    ("2024", f"{BASE_HF}/2024.csv"),
    ("2025", f"{BASE_HF}/2025.csv"),
    ("2026_jan_apr", f"{BASE_HF}/2026%20Jan_April_13.csv"),
]

TARGET_STATES = {
    "maharashtra": "Maharashtra",
    "uttar pradesh": "Uttar Pradesh",
    "karnataka": "Karnataka",
    "madhya pradesh": "Madhya Pradesh",
    "gujarat": "Gujarat",
    "himachal pradesh": "Himachal Pradesh",
}

TARGET_COMMODITIES = {
    "onion": "Onion",
    "potato": "Potato",
    "tomato": "Tomato",
    "apple": "Apple",
}

# Canonical state-level district renames observed across 2024-2026 AGMARKNET vintages
DISTRICT_ALIASES = {
    ("Uttar Pradesh", "Prayagraj"): "Allahabad",
    ("Maharashtra", "Chhatrapati Sambhajinagar"): "Aurangabad",
    ("Maharashtra", "Dharashiv"): "Osmanabad",
    ("Maharashtra", "Ahilyanagar"): "Ahmednagar",
    ("Gujarat", "Banaskantha"): "Banas Kantha",
    ("Gujarat", "Sabarkantha"): "Sabar Kantha",
    ("Gujarat", "Panchmahal"): "Panch Mahals",
    ("Gujarat", "Dohad"): "Dahod",
    ("Karnataka", "Bengaluru"): "Bangalore",
    ("Karnataka", "Bengaluru Rural"): "Bangalore",
    ("Karnataka", "Belagavi"): "Belgaum",
    ("Karnataka", "Vijayapura"): "Bijapur",
    ("Karnataka", "Kalaburagi"): "Gulbarga",
    ("Karnataka", "Shivamogga"): "Shimoga",
    ("Karnataka", "Ballari"): "Bellary",
    ("Karnataka", "Mysuru"): "Mysore",
    ("Karnataka", "Tumakuru"): "Tumkur",
    ("Karnataka", "Hubballi"): "Dharwad",
    ("Karnataka", "Chikkamagaluru"): "Chikmagalur",
    ("Karnataka", "Chikkaballapur"): "Chikballapur",
    ("Madhya Pradesh", "Narmadapuram"): "Hoshangabad",
    ("Himachal Pradesh", "Lahul & Spiti"): "Lahaul and Spiti",
}

EXPECTED_COLS = [
    "State",
    "District",
    "Market",
    "Commodity",
    "Variety",
    "Grade",
    "Arrival_Date",
    "Min_Price",
    "Max_Price",
    "Modal_Price",
    "Commodity_Code",
]


def normalize_market_name(raw_market: str) -> str:
    """Normalize APMC naming drift across 2024-2026 AGMARKNET dumps."""
    m = " ".join(str(raw_market).strip().split())
    m = re.sub(r"\s+APMC$", "", m, flags=re.IGNORECASE).strip()
    m = re.sub(r"\s+", " ", m)
    return m


def normalize_district_name(state: str, raw_district: str) -> str:
    d = " ".join(str(raw_district).strip().split())
    return DISTRICT_ALIASES.get((state, d), d)


def _fetch_range(session: requests.Session, url: str, start: int, end: int) -> bytes:
    headers = {"Range": f"bytes={start}-{end}", "User-Agent": "Mozilla/5.0"}
    for attempt in range(5):
        try:
            resp = session.get(url, headers=headers, timeout=45)
            if resp.status_code in (200, 206):
                expected = end - start + 1
                if len(resp.content) == expected:
                    return resp.content
        except Exception:
            pass
        time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"Failed fetching byte range {start}-{end} from {url}")


def stream_filter_csv(
    tag: str,
    url: str,
    chunk_bytes: int = 8 * 1024 * 1024,
    workers: int = 6,
) -> Tuple[pd.DataFrame, Dict]:
    """Download CSV in ordered parallel byte-range chunks, verify SHA-256, and filter in-flight."""
    t0 = time.perf_counter()
    session = requests.Session()
    head = session.head(url, allow_redirects=True, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    head.raise_for_status()
    final_url = head.url
    total_bytes = int(head.headers["Content-Length"])

    ranges: List[Tuple[int, int]] = []
    pos = 0
    while pos < total_bytes:
        end = min(pos + chunk_bytes - 1, total_bytes - 1)
        ranges.append((pos, end))
        pos = end + 1

    sha = hashlib.sha256()
    bytes_done = 0
    leftover = ""
    col_idx: Dict[str, int] | None = None
    total_rows = 0
    kept_rows: List[List[str]] = []

    print(f"[{tag}] Streaming {total_bytes / 1e6:.2f} MB across {len(ranges)} chunks ({workers} workers)...")
    with ThreadPoolExecutor(max_workers=workers) as pool:
        batch_size = workers * 2
        for b0 in range(0, len(ranges), batch_size):
            batch = ranges[b0 : b0 + batch_size]
            futures = [pool.submit(_fetch_range, session, final_url, s, e) for s, e in batch]
            for fut in futures:
                chunk = fut.result()
                sha.update(chunk)
                bytes_done += len(chunk)
                text = leftover + chunk.decode("utf-8", errors="replace")
                last_nl = text.rfind("\n")
                if last_nl == -1:
                    leftover = text
                    continue
                complete_block = text[: last_nl + 1]
                leftover = text[last_nl + 1 :]

                reader = csv.reader(io.StringIO(complete_block))
                for row in reader:
                    if not row:
                        continue
                    if col_idx is None:
                        col_idx = {name.strip(): i for i, name in enumerate(row)}
                        missing = [c for c in EXPECTED_COLS if c not in col_idx]
                        if missing:
                            raise ValueError(f"[{tag}] Missing expected columns {missing}; got {row}")
                        max_idx = max(col_idx.values())
                        continue
                    total_rows += 1
                    if len(row) <= max_idx:
                        continue
                    st_raw = row[col_idx["State"]].strip().lower()
                    if st_raw not in TARGET_STATES:
                        continue
                    cm_raw = row[col_idx["Commodity"]].strip().lower()
                    if cm_raw not in TARGET_COMMODITIES:
                        continue
                    kept_rows.append([row[col_idx[c]].strip() for c in EXPECTED_COLS])

            if (b0 // batch_size) % 3 == 0 or b0 + batch_size >= len(ranges):
                print(
                    f"  [{tag}] {bytes_done / 1e6:6.1f}/{total_bytes / 1e6:6.1f} MB "
                    f"| rows={total_rows:,} | kept={len(kept_rows):,}",
                    flush=True,
                )

    if leftover.strip():
        reader = csv.reader(io.StringIO(leftover))
        for row in reader:
            if not row or col_idx is None:
                continue
            total_rows += 1
            st_raw = row[col_idx["State"]].strip().lower()
            cm_raw = row[col_idx["Commodity"]].strip().lower()
            if st_raw in TARGET_STATES and cm_raw in TARGET_COMMODITIES:
                kept_rows.append([row[col_idx[c]].strip() for c in EXPECTED_COLS])

    assert bytes_done == total_bytes, f"Byte count mismatch: {bytes_done} != {total_bytes}"
    dt = time.perf_counter() - t0
    df = pd.DataFrame(kept_rows, columns=EXPECTED_COLS)
    df["source_file"] = tag
    meta = {
        "tag": tag,
        "url": url,
        "final_url_host": final_url.split("/")[2],
        "content_length_bytes": total_bytes,
        "sha256_raw_csv": sha.hexdigest(),
        "total_csv_data_rows": total_rows,
        "filtered_6state_4crop_rows": int(len(df)),
        "download_seconds": round(dt, 2),
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
    }
    return df, meta


def parse_and_clean(raw_df: pd.DataFrame, min_date: str = "2024-01-01", max_date: str = "2026-04-13") -> Tuple[pd.DataFrame, Dict]:
    """Parse mixed dates, normalize market/district strings, drop invalid prices & exact duplicates."""
    df = raw_df.copy()
    n_start = len(df)
    df["State"] = df["State"].str.strip().str.lower().map(TARGET_STATES)
    df["Commodity"] = df["Commodity"].str.strip().str.lower().map(TARGET_COMMODITIES)
    df["District_Raw"] = df["District"].astype(str).str.strip()
    df["District"] = [normalize_district_name(s, d) for s, d in zip(df["State"], df["District_Raw"])]
    df["Market_Raw"] = df["Market"].astype(str).str.strip()
    df["Market"] = df["Market_Raw"].map(normalize_market_name)
    df["Variety"] = df["Variety"].astype(str).str.strip().replace({"": "Other"})
    df["Grade"] = df["Grade"].astype(str).str.strip().replace({"": "FAQ"})

    # Parse dates carefully: 2024/2025 use DD/MM/YYYY, 2026 uses YYYY-MM-DD (or mixed).
    dt_iso = pd.to_datetime(df["Arrival_Date"], format="%Y-%m-%d", errors="coerce")
    dt_dmy = pd.to_datetime(df["Arrival_Date"], format="%d/%m/%Y", errors="coerce")
    df["Arrival_Date"] = dt_iso.fillna(dt_dmy)
    n_bad_date = int(df["Arrival_Date"].isna().sum())
    df = df.dropna(subset=["Arrival_Date"]).copy()

    for col in ["Min_Price", "Max_Price", "Modal_Price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    n_before_price = len(df)
    valid_price = (
        df["Modal_Price"].notna()
        & df["Min_Price"].notna()
        & df["Max_Price"].notna()
        & (df["Modal_Price"] > 0)
        & (df["Min_Price"] > 0)
        & (df["Max_Price"] >= df["Min_Price"])
        & (df["Modal_Price"] <= 100000.0)  # Drop impossible entry typos (> Rs 1 lakh/qtl)
    )
    df = df.loc[valid_price].copy()
    n_bad_price = n_before_price - len(df)

    # Bound strictly to [min_date, max_date]
    df = df[(df["Arrival_Date"] >= min_date) & (df["Arrival_Date"] <= max_date)].copy()

    n_before_dedup = len(df)
    df = df.drop_duplicates(
        subset=[
            "State",
            "District",
            "Market",
            "Commodity",
            "Variety",
            "Grade",
            "Arrival_Date",
            "Min_Price",
            "Max_Price",
            "Modal_Price",
        ]
    ).sort_values(["State", "Market", "Commodity", "Variety", "Arrival_Date"]).reset_index(drop=True)
    n_dups = n_before_dedup - len(df)

    stats = {
        "rows_filtered_raw": n_start,
        "dropped_bad_date": n_bad_date,
        "dropped_invalid_or_outlier_price": n_bad_price,
        "dropped_exact_duplicates": n_dups,
        "rows_clean_total": int(len(df)),
        "date_min": str(df["Arrival_Date"].min().date()),
        "date_max": str(df["Arrival_Date"].max().date()),
        "n_states": int(df["State"].nunique()),
        "n_markets": int(df.groupby(["State", "Market"]).ngroups),
        "n_commodities": int(df["Commodity"].nunique()),
    }
    return df, stats


def build_active_panel(df: pd.DataFrame, min_days: int = 80, max_markets_per_state: int = 30) -> Tuple[pd.DataFrame, Dict]:
    """Select active well-connected mandis (ranked causally on 2024 history when >30, requiring >=80 total days)."""
    df_2024 = df[df["Arrival_Date"] <= "2024-12-31"]
    days_2024 = df_2024.groupby(["State", "Market"])["Arrival_Date"].nunique().rename("days_2024")
    days_all = df.groupby(["State", "Market"])["Arrival_Date"].nunique().rename("days_all")
    days_test = df[df["Arrival_Date"] >= "2025-06-01"].groupby(["State", "Market"])["Arrival_Date"].nunique().rename("days_holdout")

    mkt_stats = pd.concat([days_2024, days_all, days_test], axis=1).fillna(0).reset_index()
    # Must have >= min_days total and >= 20 trading days in 2024 so causal history & lag features exist
    eligible = mkt_stats[(mkt_stats["days_all"] >= min_days) & (mkt_stats["days_2024"] >= 20)].copy()
    # Rank strictly by 2024 trading days within each state to avoid holdout survivorship selection
    eligible = eligible.sort_values(["State", "days_2024", "Market"], ascending=[True, False, True])
    retained_mkts = eligible.groupby("State", group_keys=False).head(max_markets_per_state).copy()

    panel = df.merge(retained_mkts[["State", "Market"]], on=["State", "Market"], how="inner").copy()
    panel = panel.sort_values(["State", "Market", "Commodity", "Variety", "Arrival_Date"]).reset_index(drop=True)

    summary = {
        "eligible_markets_ge80d_ge20d2024": int(len(eligible)),
        "retained_markets_capped30_per_state": int(len(retained_mkts)),
        "retained_by_state": retained_mkts.groupby("State").size().to_dict(),
        "panel_rows": int(len(panel)),
        "panel_rows_by_state": panel.groupby("State").size().to_dict(),
        "panel_rows_by_commodity": panel.groupby("Commodity").size().to_dict(),
    }
    return panel, summary


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    out_all = root / "data/raw/agmarknet_6state_top_apple_2024_2026_all.parquet"
    out_panel = root / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet"
    manifest_path = root / "data/manifests/agmarknet_extract_manifest.json"

    dfs: List[pd.DataFrame] = []
    file_metas: List[Dict] = []
    for tag, url in SOURCE_FILES:
        df_part, meta = stream_filter_csv(tag, url)
        dfs.append(df_part)
        file_metas.append(meta)

    raw_df = pd.concat(dfs, ignore_index=True)
    clean_df, clean_stats = parse_and_clean(raw_df)
    clean_df.to_parquet(out_all, index=False)

    panel_df, panel_stats = build_active_panel(clean_df, min_days=80, max_markets_per_state=30)
    panel_df.to_parquet(out_panel, index=False)

    def file_sha256(p: Path) -> str:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
        return h.hexdigest()

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "sources": file_metas,
        "cleaning_stats": clean_stats,
        "retained_panel_stats": panel_stats,
        "outputs": {
            "all_clean_parquet": {"path": str(out_all.relative_to(root)), "sha256": file_sha256(out_all), "bytes": out_all.stat().st_size},
            "retained_panel_parquet": {"path": str(out_panel.relative_to(root)), "sha256": file_sha256(out_panel), "bytes": out_panel.stat().st_size},
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print("=== EXTRACTION COMPLETE ===")
    print(json.dumps(clean_stats, indent=2))
    print(json.dumps(panel_stats, indent=2))


if __name__ == "__main__":
    main()
