"""Official data.gov.in Parity Audit (Exp 14) & Missing-Entry / Open-Yard Sensitivity Proof (Exp 15).

1. Downloads the official data.gov.in Resource `9ef84268-d588-465a-a308-a864a43d0070` daily XML feed
   (`Date-Wise-Prices-all-Commodity.xml`), saves SHA-256 provenance, and cross-verifies exact
   Min_Price, Max_Price, and Modal_Price parity against the multi-year AGMARKNET archive panel.
   (Also probes api.data.gov.in if DATA_GOV_IN_API_KEY env var is set, logging gateway status.)
2. Evaluates MandiGuard vs B1/B2/B3 across five missing-data / clerk-upload-lag assumptions
   on Holdout_2025_2026 (`Exp 15`), including 100%-observed arrival-day dispatches (`d0`).
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import requests

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.baselines.dispatch_baselines import (
    eval_b1_naive_screen_greedy,
    eval_b2_fresh_road_greedy,
    eval_b3_ml_point_dispatch,
)
from src.data.extract_agmarknet_multistate import parse_and_clean
from src.evaluation.payoff_model import PayoffParams, compute_freight_inr, compute_spoilage_fraction
from src.utils.leakage import load_config

OFFICIAL_DATAGOV_XML_URL = (
    "https://www.data.gov.in/files/ogd20/ogdpv2dms/s3fs-public/Date-Wise-Prices-all-Commodity.xml"
)
OFFICIAL_DATAGOV_RESOURCE_URL = (
    "https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi"
)
OFFICIAL_API_GATEWAY_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"


def run_exp14_official_parity(root: Path) -> Dict:
    res_dir = root / "results"
    res_dir.mkdir(parents=True, exist_ok=True)
    xml_out = root / "data/raw/official_datagov_datewise_prices.xml"
    manifest_out = root / "data/manifests/official_datagov_parity_manifest.json"

    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(OFFICIAL_DATAGOV_XML_URL, headers=headers, timeout=25)
    resp.raise_for_status()
    xml_bytes = resp.content
    xml_out.write_bytes(xml_bytes)
    xml_sha = hashlib.sha256(xml_bytes).hexdigest()

    # Optional non-secret gateway health probe if user supplies env var DATA_GOV_IN_API_KEY
    api_probe_status = "skipped_no_env_key"
    env_key = os.environ.get("DATA_GOV_IN_API_KEY", "").strip()
    if env_key:
        try:
            pr = requests.get(
                OFFICIAL_API_GATEWAY_URL,
                params={"api-key": env_key, "format": "json", "limit": 2},
                headers=headers,
                timeout=6,
            )
            api_probe_status = f"http_{pr.status_code}"
        except Exception as exc:
            api_probe_status = f"timeout_or_err:{type(exc).__name__}"

    et_root = ET.fromstring(resp.text)
    rows = [{c.tag.replace("_x0020_", "_"): (c.text or "").strip() for c in t} for t in et_root.findall(".//Table")]
    df_gov = pd.DataFrame(rows)
    clean_gov, _ = parse_and_clean(df_gov, min_date="2017-01-01", max_date="2026-04-13")
    clean_6s4c = clean_gov.dropna(subset=["State", "Commodity"]).copy()

    dec = pd.read_parquet(root / "data/raw/agmarknet_6state_decade_2017_2026.parquet")
    dec["Arrival_Date"] = pd.to_datetime(dec["Arrival_Date"])
    gov_dates = sorted(str(d.date()) for d in pd.to_datetime(clean_6s4c["Arrival_Date"]).dropna().unique())
    dec_sub = dec[dec["Arrival_Date"].isin(pd.to_datetime(gov_dates))].copy()
    core_mkts = set(zip(dec["State"], dec["Market"]))
    gov_in_core = clean_6s4c[
        [True if (s, m) in core_mkts else False for s, m in zip(clean_6s4c["State"], clean_6s4c["Market"])]
    ].copy()

    key_cols = ["State", "District", "Market", "Commodity", "Variety", "Grade", "Arrival_Date"]
    matched = gov_in_core.merge(dec_sub, on=key_cols, suffixes=("_gov", "_archive"))

    min_parity = float((matched["Min_Price_gov"] == matched["Min_Price_archive"]).mean() * 100.0) if len(matched) else 0.0
    max_parity = float((matched["Max_Price_gov"] == matched["Max_Price_archive"]).mean() * 100.0) if len(matched) else 0.0
    mod_parity = float((matched["Modal_Price_gov"] == matched["Modal_Price_archive"]).mean() * 100.0) if len(matched) else 0.0
    exact_10col = int(
        (
            (matched["Min_Price_gov"] == matched["Min_Price_archive"])
            & (matched["Max_Price_gov"] == matched["Max_Price_archive"])
            & (matched["Modal_Price_gov"] == matched["Modal_Price_archive"])
        ).sum()
    )

    audit_df = pd.DataFrame(
        [
            {
                "official_source": "data.gov.in Resource 9ef84268-d588-465a-a308-a864a43d0070 (Date-Wise XML)",
                "gov_dates": ",".join(gov_dates),
                "total_gov_all_india_rows": int(len(df_gov)),
                "gov_6state_4crop_rows": int(len(clean_6s4c)),
                "gov_178_panel_rows": int(len(gov_in_core)),
                "matched_panel_keys": int(len(matched)),
                "exact_10col_matches": exact_10col,
                "min_price_exact_parity_pct": round(min_parity, 2),
                "max_price_exact_parity_pct": round(max_parity, 2),
                "modal_price_exact_parity_pct": round(mod_parity, 2),
                "exact_full_row_rate_pct": round(exact_10col / max(1, len(gov_in_core)) * 100.0, 2),
            }
        ]
    )
    audit_df.to_csv(res_dir / "exp14_official_datagov_parity_audit.csv", index=False)

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "resource_page_url": OFFICIAL_DATAGOV_RESOURCE_URL,
        "datafile_url": OFFICIAL_DATAGOV_XML_URL,
        "api_gateway_probe": api_probe_status,
        "xml_file": {
            "path": str(xml_out.relative_to(root)),
            "bytes": int(len(xml_bytes)),
            "sha256": xml_sha,
        },
        "parity_summary": audit_df.iloc[0].to_dict(),
    }
    manifest_out.write_text(json.dumps(manifest, indent=2))
    print("=== EXP 14: OFFICIAL DATA.GOV.IN PARITY AUDIT ===", flush=True)
    print(audit_df.to_string(index=False), flush=True)
    return manifest


def run_exp15_open_yard_sensitivity(root: Path) -> pd.DataFrame:
    cfg = load_config(root)
    splits = cfg["temporal_splits"]
    cal = json.loads((root / "configs/frozen_calibration.json").read_text())
    margin = float(cal["frozen_safety_margin_inr"])
    hurdle = float(cfg["agent_defaults"]["screen_hurdle_inr_qtl"])
    k_max = int(cfg["agent_defaults"]["k_max_candidates"])

    cand = pd.read_parquet(root / "data/processed/candidates_6state.parquet")
    cand["date_dt"] = pd.to_datetime(cand["date"])
    cand["arr_dt"] = pd.to_datetime(cand["arrival_date"])
    c2526 = cand[cand["date_dt"] >= splits["val_start"]].copy()
    with open(root / "data/interim/forecaster_2024.pkl", "rb") as f:
        fc = pickle.load(f)
    pr, lr = fc.predict_point_and_causal_lcb(c2526)
    c2526["pred_ret"], c2526["lcb_ret"] = pr, lr
    hold = c2526[(c2526["date_dt"] >= splits["test_start"]) & (c2526["arr_dt"] <= splits["test_end"])].copy()

    pp = PayoffParams()
    fr = np.array(
        [
            compute_freight_inr(str(s), float(d), bool(sd), float(lp), pp, commodity=str(c))
            for s, d, sd, lp, c in zip(
                hold["State"], hold["road_km"], hold["same_district"], hold["local_price"], hold["Commodity"]
            )
        ]
    )
    sp = np.array(
        [
            compute_spoilage_fraction(str(c), float(h), float(tm), float(rh), float(rn), 0, pp)
            for c, h, tm, rh, rn in zip(
                hold["Commodity"], hold["truck_hours"], hold["route_era5_tmax"], hold["route_era5_rh"], hold["route_era5_rain"]
            )
        ]
    )
    divert_mask = (
        (~np.isfinite(hold["dest_modal_d0"]))
        & (~np.isfinite(hold["dest_modal_d1"]))
        & (~np.isfinite(hold["dest_modal_d2"]))
        & (~(np.isfinite(hold["dest_any_var_min_d0"]) & (hold["dest_any_var_min_d0"] > 0)))
    ).to_numpy()

    base_dnet = hold["real_delta_net_inr"].to_numpy(dtype=np.float64)
    local_p = hold["local_price"].to_numpy(dtype=np.float64)
    oneway_only_dnet = -1.0 * fr - local_p * sp
    cf_p = np.where(np.isfinite(hold["dest_ref_price"]), hold["dest_ref_price"] * 0.90, local_p)
    open_cf_dnet = cf_p * (1.0 - sp) - fr - local_p
    local_parity_dnet = -0.5 * fr  # 50% one-way freight parity friction if market matched home price net of spoilage

    rows: List[Dict[str, object]] = []
    scenarios = [
        ("1_Baseline_Physical_1.5x_Diversion", base_dnet),
        ("2_No_Return_Haul_1.0x_OneWay_Only", np.where(divert_mask, oneway_only_dnet, base_dnet)),
        ("3_50pct_Clerk_Upload_Lag_OpenAtRef90", np.where(divert_mask, 0.5 * base_dnet + 0.5 * open_cf_dnet, base_dnet)),
        ("4_100pct_Clerk_Upload_Lag_LocalParity", np.where(divert_mask, local_parity_dnet, base_dnet)),
    ]

    b1_base = b2_base = b3_base = mg_base = None
    for idx, (label, new_vals) in enumerate(scenarios):
        h_mod = hold.copy()
        h_mod["real_delta_net_inr"] = new_vals
        b1 = eval_b1_naive_screen_greedy(h_mod, hurdle_inr=hurdle)
        b2 = eval_b2_fresh_road_greedy(h_mod, hurdle_inr=hurdle)
        b3 = eval_b3_ml_point_dispatch(h_mod, safety_margin_inr=margin)
        mg, _ = evaluate_mandiguard_vectorized(
            h_mod, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=margin)
        )
        if idx == 0:
            b1_base, b2_base, b3_base, mg_base = b1, b2, b3, mg

        b1_mean = float(b1["delta_net_inr"].mean())
        for pname, dfp in [("B1_NaiveScreen", b1), ("B2_FreshRoad", b2), ("B3_MLPoint", b3), ("MandiGuard", mg)]:
            disp = dfp["is_dispatch"].to_numpy(dtype=bool)
            dnet = dfp["delta_net_inr"].to_numpy(dtype=np.float64)
            rows.append(
                {
                    "regime": label,
                    "policy": pname,
                    "evaluation_scope": "All_Shortlisted_Episodes",
                    "n_count": int(len(dfp)),
                    "mean_net_gain_inr_qtl": round(float(dnet.mean()), 2),
                    "loss_trip_rate_pct": round(float((dnet[disp] < 0.0).mean() * 100.0), 2) if disp.any() else 0.0,
                    "mg_minus_b1_inr_qtl": round(float(dnet.mean() - b1_mean), 2) if pname == "MandiGuard" else 0.0,
                }
            )

    # Regime 5: Pure 100%-observed arrival-day d0 dispatches (zero missing data, zero closed-yard inference!)
    obs_means = {}
    obs_rows_tmp = {}
    for pname, dfp in [("B1_NaiveScreen", b1_base), ("B2_FreshRoad", b2_base), ("B3_MLPoint", b3_base), ("MandiGuard", mg_base)]:
        m = dfp.merge(
            hold[["episode_id", "dest_market", "dest_modal_d0"]].drop_duplicates(["episode_id", "dest_market"]),
            left_on=["episode_id", "chosen_dest"],
            right_on=["episode_id", "dest_market"],
            how="left",
        )
        obs = m[m["is_dispatch"] & m["dest_modal_d0"].notna()]
        obs_means[pname] = float(obs["delta_net_inr"].mean())
        obs_rows_tmp[pname] = obs

    for pname in ["B1_NaiveScreen", "B2_FreshRoad", "B3_MLPoint", "MandiGuard"]:
        obs = obs_rows_tmp[pname]
        rows.append(
            {
                "regime": "5_Observed_Arrival_Day_d0_Only_ZeroMissing",
                "policy": pname,
                "evaluation_scope": "Dispatched_With_Observed_d0_Price",
                "n_count": int(len(obs)),
                "mean_net_gain_inr_qtl": round(obs_means[pname], 2),
                "loss_trip_rate_pct": round(float((obs["delta_net_inr"] < 0.0).mean() * 100.0), 2),
                "mg_minus_b1_inr_qtl": round(obs_means["MandiGuard"] - obs_means["B1_NaiveScreen"], 2) if pname == "MandiGuard" else 0.0,
            }
        )

    out_df = pd.DataFrame(rows)
    out_df.to_csv(root / "results/exp15_missing_data_open_yard_sensitivity.csv", index=False)
    print("\n=== EXP 15: MISSING-DATA / CLERK-UPLOAD-LAG SENSITIVITY ===", flush=True)
    print(out_df.to_string(index=False), flush=True)
    return out_df


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    run_exp14_official_parity(root)
    run_exp15_open_yard_sensitivity(root)


if __name__ == "__main__":
    main()
