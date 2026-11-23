"""Economic parameter audit, tornado sensitivity, and heterogeneous missing-price bounds (Step 4 / A8)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from revision.eval_run import (
    compute_decision_features,
    pick_episode,
    settle_candidates,
    summarize_chosen,
)

ROOT = Path(__file__).resolve().parents[1]


def build_epistemic_table() -> pd.DataFrame:
    rows = [
        ("Daily wholesale prices (Min, Modal, Max), Variety, Grade", "Observed", "AGMARKNET / HF clean extract (260,043 rows -> 259,284 valid)", "data/manifests/agmarknet_extract_manifest.json; NDSAP Open Govt"),
        ("HP Grade-Explicit Apple prices (2025-11..2026-09)", "Observed", "AGMARKNET official daily records (4,427 rows, 42 markets)", "data/raw/hp_apple_daily_2025_2026.csv"),
        ("Corridor road distance & truck duration", "Derived", "OSRM routing on OSM (150 exact geocodes + 70 district centroids), 1.35x truck speed, 1.25x HP speed (no flat +4h buffer in stored matrix)", "data/manifests/road_network_manifest.json; OSM ODbL"),
        ("Stylized 24h decay from NABCONS cumulative loss", "Assumed_Stylized", "Tomato 3.25%, Onion 1.96%, Apple 1.64%, Potato 0.86% cumulative market-stage loss shares adapted as stylized 24h daily decay benchmark", "MoFPI / NABCONS (2022) Annexure-II Table-2 (PIB PRID=2151371)"),
        ("Biological Q10 & RH transit spoilage scaling", "Derived_Assumed", "Q10=2.0 per 10C from 20C ref + 0.25 excess above 70% RH, clipped [0, 0.55]", "Kader (2002) / Gross et al. (2016) USDA-66 Q10 standard"),
        ("Stylized APMC seller-fee tier", "Assumed_Stylized", "KA/GJ/HP-veg 0.5%, MH/HP-apple 1.0%, MP/UP 1.5% on destination gross sale; statutory APMC fees are generally buyer-paid and PIB 154554 omits UP", "Qualitative state APMC background GoI PIB relid=154554; data/processed/state_apmc_and_loss_parameters.csv"),
        ("Freight cost per quintal-km & fixed base", "Assumed_Bracketed", "Base: Rs 35/qtl + Rs 0.45/qtl-km; swept [0.258 NITI heavy truck, 0.45, 0.75 LCV, 1.20]", "NITI Aayog & RMI (2021) Rs 2.58/tonne-km = Rs 0.258/qtl-km road average"),
        ("HP hill-road freight multiplier (1.45x)", "Assumed_Motivated", "1.45x on HP road km; swept [1.00, 1.25, 1.45, 1.75]", "GoHP Economic Survey 2025-26 Table 28 (91.59% single-lane motorable roads)"),
        ("Commission agent (arhtiya) & secondary slippage", "Assumed_Stressed", "0% incremental in base (or buyer-paid); swept +2%, +4%, +6% of dest sale", "RBI Bulletin TOP Study (33-37% farmer share, APMC commission context)"),
        ("Smallholder truckload benchmark (30 qtl)", "Assumed_Benchmark", "Stylized scaling anchor for per-truck narrative only; all model metrics in Rs/qtl; NSS 77th Round covers holdings/income, not truckload size", "MoSPI NSS 77th Round Report 587 (PIB PRID=1753856)"),
        ("Detention on wait & no-quote return/distress penalty", "Assumed_Scenario", "Wait detention Rs 25/qtl-day; other-var min*(1-0.10); no-commodity divert -1.5x freight - local*spoil", "Swept homogeneously & heterogeneously in missing_sensitivity_heterogeneous.csv"),
    ]
    return pd.DataFrame(rows, columns=["parameter", "epistemic_class", "specification_and_range", "primary_source"])


def run() -> None:
    out_dir = ROOT / "revision" / "results"
    build_epistemic_table().to_csv(out_dir / "epistemic_parameters.csv", index=False)

    summary = json.loads((out_dir / "summary.json").read_text())
    th = summary["tuned_thresholds_on_val"]

    df = pd.read_parquet(out_dir / "lagged_candidates.parquet")
    df["date"] = pd.to_datetime(df["date"])
    test = df[df["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    tf = compute_decision_features(test)

    # Pre-select fixed frozen test decisions using identical eval_run definitions
    test["y"] = 0.0
    specs = {
        "B1_lagged_screen": pick_episode(test, tf["lag_spread"], np.ones(len(test), dtype=bool)),
        "B2_fresh_val": pick_episode(test, tf["net_road_fee"], (tf["age"] <= 1) & (tf["net_road_fee"] > th["B2_fresh_val"])),
        "B2_age_matched": pick_episode(test, tf["net_road_fee"], (tf["age"] >= 1) & (tf["age"] <= 3) & (tf["net_road_fee"] > th["B2_age_matched"])),
        "B_simple_activity": pick_episode(test, tf["net_road_fee"], (tf["age"] >= 1) & (tf["age"] <= 3) & (tf["rep14"] >= 0.50) & (tf["net_road_fee"] > th["B_simple_activity"])),
        "MG_T1_T2_T3_T4": pick_episode(test, tf["net_road_fee_spoil"], (tf["age"] >= 1) & (tf["age"] <= 3) & (tf["rep14"] >= 0.50) & (tf["dow8"] >= 0.35) & (tf["net_road_fee_spoil"] > th["MG_T1_T2_T3_T4"])),
    }

    # 1) Tornado sensitivity across primary-source physical & market friction parameters
    scenarios: Dict[str, dict] = {
        "base": dict(),
        "freight_niti_floor_0.258": dict(freight_per_km=0.258, freight_base=20.0),
        "freight_lcv_0.75": dict(freight_per_km=0.75),
        "freight_steep_1.20": dict(freight_per_km=1.20),
        "hp_mult_1.00": dict(hp_km_mult=1.00),
        "hp_mult_1.75": dict(hp_km_mult=1.75),
        "arhtiya_2pct": dict(arhtiya_rate=0.02),
        "arhtiya_4pct": dict(arhtiya_rate=0.04),
        "arhtiya_6pct": dict(arhtiya_rate=0.06),
        "fee_buyer_paid_0pct": dict(fee_mult=0.0),
        "spoil_0.5x": dict(spoil_mult=0.5),
        "spoil_1.5x": dict(spoil_mult=1.5),
        "spoil_2.0x": dict(spoil_mult=2.0),
        "detention_0": dict(detention_per_day=0.0),
        "detention_100": dict(detention_per_day=100.0),
        "joint_optimistic_niti": dict(freight_per_km=0.258, freight_base=20.0, spoil_mult=0.5, div=0.5),
        "joint_realistic_harsh_lcv_arhtiya4": dict(freight_per_km=0.75, arhtiya_rate=0.04, spoil_mult=1.5),
        "outside_option_origin_lag": dict(outside_option="lag"),
    }

    torn_rows = []
    for sname, kw in scenarios.items():
        y_sc = settle_candidates(test, how="sequential", weather="none", **kw)
        for pname, ch in specs.items():
            idx = ch["_i"].to_numpy()
            rec = summarize_chosen(pname, ch, y_override=y_sc[idx])
            rec["scenario"] = sname
            torn_rows.append(rec)
    torn_df = pd.DataFrame(torn_rows)
    torn_df.to_csv(out_dir / "tornado_sensitivity.csv", index=False)

    # 2) Homogeneous AND Heterogeneous Missing-Price Sensitivity Grid (ALL + Crops)
    miss_rows = []
    for div in (0.0, 0.5, 1.0, 1.5, 2.0):
        for disc in (0.0, 0.05, 0.10, 0.20):
            y_sc = settle_candidates(test, how="sequential", weather="none", div=div, disc=disc)
            for sl_name, sl_mask in (
                ("ALL", np.ones(len(specs["B1_lagged_screen"]), dtype=bool)),
                ("Apple", specs["B1_lagged_screen"]["Commodity"].to_numpy() == "Apple"),
                ("NonApple", specs["B1_lagged_screen"]["Commodity"].to_numpy() != "Apple"),
            ):
                for pname, ch in specs.items():
                    sub_ch = ch.loc[sl_mask].reset_index(drop=True)
                    idx = ch.loc[sl_mask, "_i"].to_numpy()
                    rec = summarize_chosen(pname, sub_ch, y_override=y_sc[idx])
                    rec["div"] = div
                    rec["disc"] = disc
                    rec["regime"] = "homogeneous_grid"
                    rec["slice"] = sl_name
                    miss_rows.append(rec)

    # Heterogeneous Crop-Scaled Perishability & Selective-Missingness Scenarios
    y_zero = settle_candidates(test, div=0.0, disc=0.0)
    y_mild = settle_candidates(test, div=0.5, disc=0.05)
    y_base = settle_candidates(test, div=1.5, disc=0.10)
    y_harsh = settle_candidates(test, div=2.0, disc=0.20)

    comm = test["Commodity"].to_numpy()
    rep14 = test["dest_exact_rep_14d"].to_numpy()

    het_specs = {
        "het_crop_perishability": np.where(comm == "Tomato", y_harsh, np.where(comm == "Potato", y_mild, y_base)),
        "het_selective_missing_lowrep_harsh": np.where(rep14 < 0.50, y_harsh, y_mild),
        "het_adversarial_lowrep_ok_highrep_harsh": np.where(rep14 >= 0.50, y_harsh, y_zero),
    }
    for hname, y_h in het_specs.items():
        for pname, ch in specs.items():
            idx = ch["_i"].to_numpy()
            rec = summarize_chosen(pname, ch, y_override=y_h[idx])
            rec["div"] = np.nan
            rec["disc"] = np.nan
            rec["regime"] = hname
            rec["slice"] = "ALL"
            miss_rows.append(rec)

    miss_df = pd.DataFrame(miss_rows)
    miss_df.to_csv(out_dir / "missing_sensitivity_heterogeneous.csv", index=False)

    print("=== TORNADO HIGHLIGHTS (MG_T1_T2_T3_T4 vs B2_age_matched vs B1) ===")
    piv = torn_df.pivot(index="scenario", columns="policy", values="mean")[["B1_lagged_screen", "B2_age_matched", "MG_T1_T2_T3_T4"]]
    piv["MG_minus_B2"] = (piv["MG_T1_T2_T3_T4"] - piv["B2_age_matched"]).round(2)
    piv["MG_minus_B1"] = (piv["MG_T1_T2_T3_T4"] - piv["B1_lagged_screen"]).round(2)
    print(piv.to_string())

    print("\n=== MISSING SENSITIVITY ALL (div=0, 0.5, 1.5, 2.0 at disc=0.10 & het) ===")
    m_all = miss_df[(miss_df["slice"] == "ALL") & ((miss_df["disc"] == 0.10) | (miss_df["regime"] != "homogeneous_grid"))]
    print(m_all[["regime", "div", "policy", "mean", "ep_loss_rate", "es10"]].to_string(index=False))


if __name__ == "__main__":
    run()
