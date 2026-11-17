"""Gentle unauthenticated client for live AGMARKNET v1 public endpoints (Nov 2026 demo).

Uses ONLY verified open JSON endpoints:
  - GET /v1/dashboard-filters/?dashboard_name=cumm_faq
  - GET /v1/prices-and-arrivals/commodity-price/lastweek?marketId=...&stateId=...&commodityId=...
Never accesses any CAPTCHA-gated endpoint.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests

FILTERS_URL = "https://api.agmarknet.gov.in/v1/dashboard-filters/?dashboard_name=cumm_faq"
LASTWEEK_URL = "https://api.agmarknet.gov.in/v1/prices-and-arrivals/commodity-price/lastweek"

TARGET_STATE_NAMES = [
    "Maharashtra",
    "Uttar Pradesh",
    "Karnataka",
    "Madhya Pradesh",
    "Gujarat",
    "Himachal Pradesh",
]
TARGET_COMMODITY_NAMES = ["Onion", "Potato", "Tomato", "Apple"]


def fetch_live_snapshot(max_queries: int = 24, sleep_s: float = 0.35) -> Dict:
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}

    r_filters = session.get(FILTERS_URL, headers=headers, timeout=20)
    r_filters.raise_for_status()
    fdata = r_filters.json()["data"]

    states_map = {s["state_name"].strip(): int(s["state_id"]) for s in fdata["state_data"]}
    comm_map = {c["cmdt_name"].strip(): int(c["cmdt_id"]) for c in fdata["cmdt_data"]}
    markets = fdata["market_data"]

    target_state_ids = {states_map[s]: s for s in TARGET_STATE_NAMES if s in states_map}
    target_comm_ids = {comm_map[c]: c for c in TARGET_COMMODITY_NAMES if c in comm_map}

    # Select well-known hub and regional markets across the 6 target states (~3-4 per state)
    preferred_keywords = [
        ("Maharashtra", "Onion", ["Lasalgaon", "Pimpalgaon", "Pune", "Solapur", "Mumbai"]),
        ("Uttar Pradesh", "Potato", ["Agra", "Kanpur", "Lucknow", "Azadpur", "Farrukhabad", "Prayagraj", "Allahabad"]),
        ("Karnataka", "Tomato", ["Kolar", "Bengaluru", "Chikkaballapur", "Mysuru", "Ramanagara"]),
        ("Madhya Pradesh", "Onion", ["Indore", "Ujjain", "Ratlam", "Shajapur"]),
        ("Gujarat", "Onion", ["Mahuva", "Rajkot", "Gondal", "Bhavnagar", "Ahmedabad"]),
        ("Himachal Pradesh", "Apple", ["Shimla", "Solan", "Kullu", "Mandi", "Kangra", "Parwanoo"]),
    ]

    queries: List[Dict] = []
    seen_pairs = set()
    for st_name, cm_name, kw_list in preferred_keywords:
        st_id = states_map.get(st_name)
        cm_id = comm_map.get(cm_name)
        if not st_id or not cm_id:
            continue
        st_mkts = [m for m in markets if int(m.get("state_id") or -1) == st_id]
        for kw in kw_list:
            matches = [m for m in st_mkts if kw.lower() in m.get("mkt_name", "").lower()]
            if matches:
                m = matches[0]
                mkt_id = int(m["id"])
                key = (st_id, mkt_id, cm_id)
                if key not in seen_pairs:
                    seen_pairs.add(key)
                    queries.append(
                        {
                            "state": st_name,
                            "state_id": st_id,
                            "market": m["mkt_name"].strip(),
                            "market_id": mkt_id,
                            "commodity": cm_name,
                            "commodity_id": cm_id,
                        }
                    )
            if len(queries) >= max_queries:
                break
        if len(queries) >= max_queries:
            break

    records = []
    for q in queries:
        try:
            resp = session.get(
                LASTWEEK_URL,
                params={
                    "marketId": q["market_id"],
                    "stateId": q["state_id"],
                    "commodityId": q["commodity_id"],
                },
                headers=headers,
                timeout=15,
            )
            payload = resp.json() if resp.status_code == 200 else {"success": False, "status_code": resp.status_code}
            records.append(
                {
                    **q,
                    "http_status": resp.status_code,
                    "success": bool(payload.get("success", False)),
                    "title": payload.get("title", ""),
                    "columns": payload.get("columns", []),
                    "data": payload.get("data", []),
                }
            )
        except Exception as exc:
            records.append({**q, "http_status": -1, "success": False, "error": str(exc)})
        time.sleep(sleep_s)

    return {
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "filters_url": FILTERS_URL,
        "lastweek_url": LASTWEEK_URL,
        "n_states_catalog": len(fdata.get("state_data", [])),
        "n_markets_catalog": len(fdata.get("market_data", [])),
        "n_commodities_catalog": len(fdata.get("cmdt_data", [])),
        "target_state_ids": target_state_ids,
        "target_commodity_ids": target_comm_ids,
        "queries_executed": len(records),
        "records": records,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    out_path = root / "data/raw/live_nov2026_agmarknet_snapshot.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    snap = fetch_live_snapshot(max_queries=22, sleep_s=0.35)
    raw_bytes = json.dumps(snap, indent=2).encode("utf-8")
    out_path.write_bytes(raw_bytes)
    sha = hashlib.sha256(raw_bytes).hexdigest()
    non_empty = sum(
        1
        for rec in snap["records"]
        if any(
            str(v) not in ("NR", "Unknown", "", "None")
            for row in rec.get("data", [])
            for k, v in row.items()
            if k not in ("variety", "unitOfPrice")
        )
    )
    print(f"Saved live snapshot: {out_path} ({len(raw_bytes)} B, sha256={sha[:12]}...)")
    print(f"Executed {snap['queries_executed']} live queries; {non_empty} had active Nov 2026 quotes.")


if __name__ == "__main__":
    main()
