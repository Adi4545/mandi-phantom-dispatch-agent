"""District-validated mandi geocoding and OSRM real highway distance/duration matrix.

Guard against Indian town homonyms (e.g., Pimpalgaon in Nashik vs Yavatmal):
  1. Geocode each unique (District, State) centroid within India & matching admin1 state.
  2. Geocode cleaned Market town name; accept ONLY if matching country='IN', matching
     admin1 state, AND Haversine distance to its (District, State) centroid <= 110 km.
     Otherwise fall back cleanly to the verified District centroid.
  3. Compute real driving road distance & duration within each state via OpenStreetMap OSRM.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
OSRM_TABLE_URL = "http://router.project-osrm.org/table/v1/driving"

STATE_ADMIN1_ALIASES = {
    "Maharashtra": {"maharashtra"},
    "Uttar Pradesh": {"uttar pradesh"},
    "Karnataka": {"karnataka"},
    "Madhya Pradesh": {"madhya pradesh"},
    "Gujarat": {"gujarat"},
    "Himachal Pradesh": {"himachal pradesh"},
}

# Explicit manual fallback only for historical district renames/spellings if Open-Meteo returns no hit
DISTRICT_SEARCH_OVERRIDES = {
    ("Gujarat", "Banaskanth"): "Palanpur",
    ("Gujarat", "Banas Kantha"): "Palanpur",
    ("Gujarat", "Sabar Kantha"): "Himmatnagar",
    ("Gujarat", "Panch Mahals"): "Godhra",
    ("Gujarat", "Kachchh"): "Bhuj",
    ("Gujarat", "Gir Somnath"): "Veraval",
    ("Gujarat", "Vadodara(Baroda)"): "Vadodara",
    ("Gujarat", "Dahod"): "Dohad",
    ("Gujarat", "Morbi"): "Morvi",
    ("Himachal Pradesh", "Sirmore"): "Nahan",
    ("Himachal Pradesh", "Sirmaur"): "Nahan",
    ("Himachal Pradesh", "Lahaul and Spiti"): "Keylong",
    ("Himachal Pradesh", "Kangra"): "Kangra",
    ("Himachal Pradesh", "Kullu"): "Kulu",
    ("Himachal Pradesh", "Kinnaur"): "Reckong Peo",
    ("Karnataka", "Bangalore"): "Bengaluru",
    ("Karnataka", "Shimoga"): "Shivamogga",
    ("Karnataka", "Chamrajnagar"): "Chamarajanagar",
    ("Karnataka", "Kalburgi"): "Kalaburagi",
    ("Maharashtra", "Ahmednagar"): "Ahilyanagar",
    ("Maharashtra", "Amarawati"): "Amravati",
    ("Maharashtra", "Chattrapati Sambhajinagar"): "Aurangabad",
    ("Maharashtra", "Sholapur"): "Solapur",
    ("Maharashtra", "Raigad"): "Alibag",
    ("Uttar Pradesh", "Allahabad"): "Prayagraj",
    ("Uttar Pradesh", "Bulandshahar"): "Bulandshahr",
    ("Uttar Pradesh", "Chitrakut"): "Chitrakoot",
    ("Uttar Pradesh", "Farukhabad"): "Farrukhabad",
    ("Uttar Pradesh", "Pillibhit"): "Pilibhit",
    ("Uttar Pradesh", "Raebarelli"): "Raebareli",
    ("Uttar Pradesh", "Kushinagar"): "Padrauna",
    ("Uttar Pradesh", "Ambedkar Nagar"): "Akbarpur",
    ("Uttar Pradesh", "Gautam Buddha Nagar"): "Noida",
    ("Uttar Pradesh", "Sant Kabir Nagar"): "Khalilabad",
    ("Uttar Pradesh", "Siddharth Nagar"): "Naugarh",
    ("Uttar Pradesh", "Shravasti"): "Bhinga",
}

# Verified Indian district HQ overrides for 2 Open-Meteo index mislabels:
# (1) Neemuch, MP is mislabeled admin1='Rajasthan' in Open-Meteo; (2) Gonda District HQ vs Aligarh's Gonda village
EXACT_DISTRICT_COORDS = {
    ("Madhya Pradesh", "Neemuch"): (24.47639, 74.86241, "Neemuch"),
    ("Uttar Pradesh", "Gonda"): (27.13390, 81.96190, "Gonda"),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def clean_market_query(market: str) -> List[str]:
    m = market.strip()
    cands = []
    # Check inside parentheses if e.g. "Kangra(Jassour)" -> try Jassour and Kangra
    paren = re.findall(r"\(([^)]+)\)", m)
    base = re.sub(r"\([^)]*\)", "", m).strip()
    for prefix in ("PMY ", "SMY ", "F&V ", "F & V ", "APMC "):
        if base.upper().startswith(prefix):
            base = base[len(prefix) :].strip()
    base = re.sub(r"\s+(APMC|Mandi|Yard|Sub Yard|Market|Sabzi Mandi|Uzhavar Sandhai)$", "", base, flags=re.I).strip()
    if base:
        cands.append(base)
    for p in paren:
        p_clean = re.sub(r"\s+(APMC|Mandi|Yard|Sub Yard)$", "", p.strip(), flags=re.I).strip()
        if p_clean and p_clean.lower() not in {"f&v", "veg", "fruit", "grain", "new", "old"}:
            cands.append(p_clean)
    return cands


def geocode_in_state(
    session: requests.Session, query: str, state: str, cache: Dict[str, List[Dict]], district_hint: str = ""
) -> Optional[Tuple[float, float, str]]:
    key = query.lower().strip()
    if key not in cache:
        for attempt in range(3):
            try:
                resp = session.get(
                    GEOCODE_URL,
                    params={"name": query, "count": 10, "language": "en", "format": "json"},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=12,
                )
                if resp.status_code == 200:
                    cache[key] = resp.json().get("results", []) or []
                    break
            except Exception:
                pass
            time.sleep(0.4 * (attempt + 1))
        else:
            cache[key] = []
        time.sleep(0.06)

    allowed = STATE_ADMIN1_ALIASES[state]
    matches = [
        r
        for r in cache[key]
        if r.get("country_code") == "IN" and str(r.get("admin1", "")).strip().lower() in allowed
    ]
    if not matches:
        return None
    dh = district_hint.lower().strip()
    matches.sort(
        key=lambda r: (
            1 if (dh and dh[:5] in str(r.get("admin2", "")).lower()) else 0,
            1 if str(r.get("feature_code", "")) in ("PPLA", "PPLA2") else 0,
            float(r.get("population") or 0.0),
        ),
        reverse=True,
    )
    top = matches[0]
    return float(top["latitude"]), float(top["longitude"]), str(top.get("name", query))


def geocode_markets(markets_df: pd.DataFrame) -> pd.DataFrame:
    """Geocode unique (State, District, Market) pairs with <= 110 km district validation."""
    session = requests.Session()
    cache: Dict[str, List[Dict]] = {}

    # 1. Geocode every unique (State, District) centroid first
    dist_coords: Dict[Tuple[str, str], Tuple[float, float, str]] = {}
    unique_districts = markets_df[["State", "District"]].drop_duplicates().sort_values(["State", "District"])
    for _, row in unique_districts.iterrows():
        st, dist = row["State"], row["District"]
        if (st, dist) in EXACT_DISTRICT_COORDS:
            dist_coords[(st, dist)] = EXACT_DISTRICT_COORDS[(st, dist)]
            continue
        q_dist = DISTRICT_SEARCH_OVERRIDES.get((st, dist), dist)
        hit = geocode_in_state(session, q_dist, st, cache, district_hint=dist)
        if hit is None and " " in q_dist:
            hit = geocode_in_state(session, q_dist.split()[0], st, cache, district_hint=dist)
        if hit is None:
            raise RuntimeError(f"Could not geocode verified Indian district: ({st}, {dist}) via '{q_dist}'")
        dist_coords[(st, dist)] = hit

    # 2. Geocode each Market and validate distance <= 110 km from its District centroid
    records = []
    for _, row in markets_df.sort_values(["State", "Market"]).iterrows():
        st, dist, mkt = row["State"], row["District"], row["Market"]
        d_lat, d_lon, d_name = dist_coords[(st, dist)]
        best_hit = None
        for cand_q in clean_market_query(mkt):
            hit = geocode_in_state(session, cand_q, st, cache, district_hint=dist)
            if hit is not None:
                dist_km = haversine_km(d_lat, d_lon, hit[0], hit[1])
                if dist_km <= 110.0:
                    best_hit = (hit[0], hit[1], "market_exact", round(dist_km, 2), hit[2])
                    break
        if best_hit is None:
            best_hit = (d_lat, d_lon, "district_centroid", 0.0, d_name)
        records.append(
            {
                "State": st,
                "District": dist,
                "Market": mkt,
                "lat": best_hit[0],
                "lon": best_hit[1],
                "geocode_precision": best_hit[2],
                "dist_to_district_km": best_hit[3],
                "matched_place_name": best_hit[4],
                "district_lat": d_lat,
                "district_lon": d_lon,
            }
        )
    out = pd.DataFrame(records)
    assert out["lat"].notna().all() and out["lon"].notna().all()
    assert (out["dist_to_district_km"] <= 110.0).all()
    return out


def fetch_osrm_state_corridors(coords_df: pd.DataFrame) -> pd.DataFrame:
    """Query OSRM driving table API within each state (batching >50 coords if needed)."""
    session = requests.Session()
    corridor_rows: List[Dict] = []

    for state, grp in coords_df.groupby("State", sort=True):
        grp = grp.reset_index(drop=True)
        n = len(grp)
        if n < 2:
            continue
        coord_str = ";".join(f"{r.lon:.6f},{r.lat:.6f}" for _, r in grp.iterrows())
        dists = [[None] * n for _ in range(n)]
        durs = [[None] * n for _ in range(n)]
        src_batch = 40
        for s0 in range(0, n, src_batch):
            s_idx = list(range(s0, min(s0 + src_batch, n)))
            url = f"{OSRM_TABLE_URL}/{coord_str}"
            params = {
                "annotations": "distance,duration",
                "sources": ";".join(map(str, s_idx)),
                "destinations": ";".join(map(str, range(n))),
            }
            data = None
            for attempt in range(4):
                try:
                    resp = session.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=35)
                    if resp.status_code == 200:
                        j = resp.json()
                        if j.get("code") == "Ok":
                            data = j
                            break
                except Exception:
                    pass
                time.sleep(0.8 * (attempt + 1))
            if data is None:
                raise RuntimeError(f"OSRM table query failed for state={state} ({n} markets)")
            for local_i, global_i in enumerate(s_idx):
                dists[global_i] = data["distances"][local_i]
                durs[global_i] = data["durations"][local_i]
            time.sleep(0.25)

        truck_factor = 1.35 * (1.25 if state == "Himachal Pradesh" else 1.0)
        road_cost_mult = 1.45 if state == "Himachal Pradesh" else 1.0

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                d_m = dists[i][j]
                t_s = durs[i][j]
                if d_m is None or t_s is None:
                    continue
                road_km = float(d_m) / 1000.0
                if not (15.0 <= road_km <= 500.0):
                    # Handle identical centroid fallback (0 km) or >500 km intrastate pairs
                    # Allow Haversine floor if two markets fell back to same centroid? Wait:
                    # Plan specifies 15 km <= d_ij <= 500 km! Keep strict 15..500 km corridors.
                    continue
                car_hours = float(t_s) / 3600.0
                truck_hours = car_hours * truck_factor
                # Realistic Indian APMC morning-auction cutoff arrival lag in {1, 2, 3} days
                if truck_hours <= 4.5:
                    arrival_lag_days = 1
                elif truck_hours <= 8.5:
                    arrival_lag_days = 2
                else:
                    arrival_lag_days = 3
                freight_inr_qtl = 35.0 + 0.45 * road_cost_mult * road_km
                euclid_km = haversine_km(grp.loc[i, "lat"], grp.loc[i, "lon"], grp.loc[j, "lat"], grp.loc[j, "lon"])
                corridor_rows.append(
                    {
                        "State": state,
                        "origin_market": grp.loc[i, "Market"],
                        "origin_district": grp.loc[i, "District"],
                        "dest_market": grp.loc[j, "Market"],
                        "dest_district": grp.loc[j, "District"],
                        "same_district": bool(grp.loc[i, "District"] == grp.loc[j, "District"]),
                        "euclid_km": round(euclid_km, 2),
                        "road_km": round(road_km, 2),
                        "car_hours": round(car_hours, 2),
                        "truck_hours": round(truck_hours, 2),
                        "arrival_lag_days": arrival_lag_days,
                        "freight_inr_qtl": round(freight_inr_qtl, 2),
                    }
                )
        print(f"[OSRM] {state}: {n} markets -> {sum(1 for r in corridor_rows if r['State']==state)} corridors (15-500 km)")
        time.sleep(0.3)

    return pd.DataFrame(corridor_rows)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    panel_path = root / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet"
    apple_path = root / "data/raw/hp_apple_daily_2025_2026.csv"
    coords_out = root / "data/processed/mandi_coordinates.parquet"
    corridors_out = root / "data/processed/osrm_corridor_matrix.parquet"
    manifest_out = root / "data/manifests/road_network_manifest.json"

    panel = pd.read_parquet(panel_path, columns=["State", "District", "Market"])
    # Pick modal District per (State, Market) in case of rare boundary drift
    m_panel = (
        panel.groupby(["State", "Market", "District"])
        .size()
        .reset_index(name="n")
        .sort_values(["State", "Market", "n"], ascending=[True, True, False])
        .drop_duplicates(["State", "Market"])[["State", "District", "Market"]]
    )

    # Also include any additional HP Apple markets from hp_apple_daily_2025_2026.csv
    ap = pd.read_csv(apple_path, usecols=["state", "district", "market"]).rename(
        columns={"state": "State", "district": "District", "market": "Market"}
    )
    ap["Market"] = ap["Market"].astype(str).str.strip()
    m_ap = ap.drop_duplicates(["State", "Market"])
    all_mkts = pd.concat([m_panel, m_ap], ignore_index=True).drop_duplicates(["State", "Market"])

    coords_df = geocode_markets(all_mkts)
    coords_out.parent.mkdir(parents=True, exist_ok=True)
    coords_df.to_parquet(coords_out, index=False)

    corridors_df = fetch_osrm_state_corridors(coords_df)
    corridors_df.to_parquet(corridors_out, index=False)

    def sha256(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n_markets_geocoded": int(len(coords_df)),
        "precision_counts": coords_df["geocode_precision"].value_counts().to_dict(),
        "n_corridors_15_500km": int(len(corridors_df)),
        "corridors_by_state": corridors_df.groupby("State").size().to_dict(),
        "lag_days_distribution": corridors_df["arrival_lag_days"].value_counts().sort_index().to_dict(),
        "outputs": {
            "mandi_coordinates": {"path": str(coords_out.relative_to(root)), "sha256": sha256(coords_out)},
            "osrm_corridor_matrix": {"path": str(corridors_out.relative_to(root)), "sha256": sha256(corridors_out)},
        },
    }
    manifest_out.write_text(json.dumps(manifest, indent=2))
    print("=== GEOCODING & OSRM COMPLETE ===")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
