"""Evaluate pre-registered Agent A10 RR-Abstain rule (strictly committed AFTER final/PREREG_A10.md)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from revision.es10 import es10
from revision.eval_run import (
    THRESH_GRID,
    compute_decision_features,
    find_val_matched_threshold,
    pick_episode,
    settle_candidates,
    summarize_chosen,
    tune_threshold_on_val,
)
from revision.stats_utils import two_way_cluster_bootstrap_all_metrics
from src.evaluation.bootstrap import holm_bonferroni

ROOT = Path(__file__).resolve().parents[1]
KAPPAS = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]


def rr_abstain_score(df: pd.DataFrame, kappa: float) -> np.ndarray:
    """Strictly <= t-1 continuous reliability-weighted expected-value score."""
    p_rep = 0.5 * df["dest_exact_rep_28d"].to_numpy(dtype=np.float64) + 0.5 * df["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64)
    p_rep = np.clip(p_rep, 0.0, 1.0)
    p_dest = df["dest_lag_price"].to_numpy(dtype=np.float64)
    p_orig = df["origin_lag_price"].to_numpy(dtype=np.float64)
    sp0 = df["spoil_ref_0"].to_numpy(dtype=np.float64)
    fee_r = df["fee_rate"].to_numpy(dtype=np.float64)
    f_road = df["freight_road"].to_numpy(dtype=np.float64)

    delta_open = p_dest * (1.0 - sp0) * (1.0 - fee_r) - p_orig - f_road
    delta_miss = -float(kappa) * f_road - p_orig * sp0
    return p_rep * delta_open + (1.0 - p_rep) * delta_miss


def run() -> None:
    out_dir = ROOT / "revision" / "results"
    summary_base = json.loads((out_dir / "summary.json").read_text())
    th_base = summary_base["tuned_thresholds_on_val"]
    target_val_disp = float(summary_base["val_summaries"]["B2_age_matched"]["dispatch_rate"])

    df = pd.read_parquet(out_dir / "lagged_candidates.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df["split"] = np.where(df["date"] <= pd.Timestamp("2025-05-31"), "val", "test")
    df["y"] = settle_candidates(df, how="sequential", weather="none", div=1.5, disc=0.10)

    val = df[df["split"] == "val"].copy().reset_index(drop=True)
    test = df[df["split"] == "test"].copy().reset_index(drop=True)
    vf = compute_decision_features(val)
    tf = compute_decision_features(test)

    age_val_gate = (vf["age"] >= 1) & (vf["age"] <= 3)
    age_test_gate = (tf["age"] >= 1) & (tf["age"] <= 3)

    # Validation selection per PREREG_A10.md Section 2 ONLY on val
    val_b2_chosen = pick_episode(val, vf["net_road_fee"], age_val_gate & (vf["net_road_fee"] > th_base["B2_age_matched"]))
    val_b2_rec = summarize_chosen("B2_age_matched", val_b2_chosen)
    mean_floor = float(val_b2_rec["mean"]) - 10.0

    best_matched_feasible = None
    best_matched_fallback = None
    val_sweep_rows = []
    for k in KAPPAS:
        sc_val = rr_abstain_score(val, k)
        m_match = find_val_matched_threshold(val, sc_val, age_val_gate, target_val_disp)
        ch_v = pick_episode(val, sc_val, age_val_gate & (sc_val > m_match))
        rec_v = summarize_chosen(f"RR_k{k}", ch_v)
        val_sweep_rows.append({"kappa": k, "m_match_val": round(m_match, 2), **rec_v})

        key = float(rec_v["es10"])
        loss_tie = -float(rec_v["ep_loss_rate"])
        if best_matched_fallback is None or (key, loss_tie) > best_matched_fallback[0]:
            best_matched_fallback = ((key, loss_tie), k, m_match, rec_v)
        if rec_v["mean"] >= mean_floor:
            if best_matched_feasible is None or (key, loss_tie) > best_matched_feasible[0]:
                best_matched_feasible = ((key, loss_tie), k, m_match, rec_v)

    chosen_matched_cfg = best_matched_feasible if best_matched_feasible is not None else best_matched_fallback
    kappa_star = float(chosen_matched_cfg[1])
    m_star_matched = float(chosen_matched_cfg[2])

    # Unconstrained grid over (kappa, m in THRESH_GRID)
    best_unc = None
    for k in KAPPAS:
        sc_v = rr_abstain_score(val, k)
        vf_tmp = {"s_rr": sc_v, "age": vf["age"]}
        m_k, rec_u = tune_threshold_on_val(val, vf_tmp, "s_rr", lambda f: (f["age"] >= 1) & (f["age"] <= 3))
        if rec_u["dispatch_rate"] is None or rec_u["dispatch_rate"] < 0.25:
            continue
        key_u = (rec_u["cond_loss_rate"], -rec_u["mean"])
        if best_unc is None or key_u < best_unc[0]:
            best_unc = (key_u, k, m_k, rec_u)
    kappa_dag = float(best_unc[1])
    m_dag = float(best_unc[2])

    # Comparators on identical test frame (reusing exact frozen thresholds / val-matched cutoffs)
    m_mg_match = find_val_matched_threshold(
        val, vf["net_road_fee_spoil"], age_val_gate & (vf["rep14"] >= 0.50) & (vf["dow8"] >= 0.35), target_val_disp
    )
    m_act_match = find_val_matched_threshold(
        val, vf["net_road_fee"], age_val_gate & (vf["rep14"] >= 0.50), target_val_disp
    )

    sc_test_star = rr_abstain_score(test, kappa_star)
    sc_test_dag = rr_abstain_score(test, kappa_dag)

    policies_test = {
        "B1_lagged_screen": pick_episode(test, tf["lag_spread"], np.ones(len(test), dtype=bool)),
        "B2_age_matched": pick_episode(test, tf["net_road_fee"], age_test_gate & (tf["net_road_fee"] > th_base["B2_age_matched"])),
        "B_simple_activity_matched": pick_episode(test, tf["net_road_fee"], age_test_gate & (tf["rep14"] >= 0.50) & (tf["net_road_fee"] > m_act_match)),
        "MG_matched": pick_episode(test, tf["net_road_fee_spoil"], age_test_gate & (tf["rep14"] >= 0.50) & (tf["dow8"] >= 0.35) & (tf["net_road_fee_spoil"] > m_mg_match)),
        "RR_Abstain_matched": pick_episode(test, sc_test_star, age_test_gate & (sc_test_star > m_star_matched)),
        "RR_Abstain_m0": pick_episode(test, sc_test_star, age_test_gate & (sc_test_star > 0.0)),
        "RR_Abstain_m100": pick_episode(test, sc_test_star, age_test_gate & (sc_test_star > 100.0)),
        "RR_Abstain_val": pick_episode(test, sc_test_dag, age_test_gate & (sc_test_dag > m_dag)),
    }

    res_rows = []
    for pname, ch in policies_test.items():
        rec = summarize_chosen(pname, ch)
        res_rows.append(rec)
    pd.DataFrame(res_rows).to_csv(out_dir / "a10_results.csv", index=False)

    # Bootstrap H_A10_1..4 + secondary comparisons across ALL THREE clustering schemes (State|dest fixed!)
    bdf = policies_test["RR_Abstain_matched"][["episode_id", "date", "origin_market_key", "State", "Commodity"]].copy()
    for pname, ch in policies_test.items():
        bdf[pname] = ch["y"].to_numpy(dtype=np.float64)
        bdf[f"{pname}_disp"] = ch["eligible"].to_numpy(dtype=bool)
        bdf[f"{pname}_dest"] = ch["dest_market"].to_numpy()
    bdf["dest_or_origin_key"] = np.where(
        bdf["B2_age_matched_disp"],
        bdf["State"].astype(str) + "|" + bdf["B2_age_matched_dest"].astype(str),
        bdf["origin_market_key"],
    )
    bdf["rr_dest_or_origin_key"] = np.where(
        bdf["RR_Abstain_matched_disp"],
        bdf["State"].astype(str) + "|" + bdf["RR_Abstain_matched_dest"].astype(str),
        bdf["origin_market_key"],
    )

    # Pre-registered H_A10_1..4 plus full metric table for matched comparisons
    test_pairs = [
        ("H_A10_vs_B2_age_matched", "RR_Abstain_matched", "B2_age_matched"),
        ("H_A10_vs_B_simple_activity_matched", "RR_Abstain_matched", "B_simple_activity_matched"),
        ("H_A10_vs_MG_matched", "RR_Abstain_matched", "MG_matched"),
        ("H_A10_vs_B1", "RR_Abstain_matched", "B1_lagged_screen"),
    ]
    prereg_family = {
        ("H_A10_vs_B2_age_matched", "es10"): "H_A10_1",
        ("H_A10_vs_B2_age_matched", "ep_loss_rate"): "H_A10_2",
        ("H_A10_vs_B2_age_matched", "mean"): "H_A10_3",
        ("H_A10_vs_MG_matched", "es10"): "H_A10_4",
    }

    boot_rows = []
    cluster_schemes = (
        ("origin_x_2week", "origin_market_key"),
        ("b2dest_or_origin_x_2week", "dest_or_origin_key"),
        ("rrdest_or_origin_x_2week", "rr_dest_or_origin_key"),
    )
    for cname, ca, cb in test_pairs:
        for sch, mcol in cluster_schemes:
            res = two_way_cluster_bootstrap_all_metrics(bdf, ca, cb, mandi_col=mcol, reps=2000, seed=20261117)
            for metric, md in res.items():
                p_dir = md["p_value_less"] if metric == "ep_loss_rate" else md["p_value_greater"]
                hid = prereg_family.get((cname, metric), "")
                boot_rows.append(
                    {
                        "hypothesis_id": hid,
                        "contrast": cname,
                        "cluster": sch,
                        "metric": metric,
                        "estimate": round(md["estimate"], 4),
                        "ci95_low": round(md["ci95_low"], 4),
                        "ci95_high": round(md["ci95_high"], 4),
                        "p_value": p_dir,
                        "p_value_two_sided": md["p_value_two_sided"],
                        "n": md["n"],
                        "n_clusters": md["n_clusters"],
                        "n_blocks": md["n_blocks"],
                    }
                )
    boot_df = pd.DataFrame(boot_rows)
    boot_df["p_holm_1s"] = np.nan
    boot_df["p_holm_2s"] = np.nan
    for sch, _ in cluster_schemes:
        mask = (boot_df["cluster"] == sch) & (boot_df["hypothesis_id"] != "")
        boot_df.loc[mask, "p_holm_1s"] = holm_bonferroni(boot_df.loc[mask, "p_value"].tolist())
        boot_df.loc[mask, "p_holm_2s"] = holm_bonferroni(boot_df.loc[mask, "p_value_two_sided"].tolist())
    boot_df["p_holm"] = boot_df["p_holm_2s"]
    boot_df.to_csv(out_dir / "a10_bootstrap.csv", index=False)

    # Crop splits (especially Non-Apple!)
    crop_rows = []
    for cname_sl, mask_sl in (
        ("Apple", bdf["Commodity"] == "Apple"),
        ("NonApple", bdf["Commodity"] != "Apple"),
        ("Onion", bdf["Commodity"] == "Onion"),
        ("Potato", bdf["Commodity"] == "Potato"),
        ("Tomato", bdf["Commodity"] == "Tomato"),
    ):
        g = bdf.loc[mask_sl].reset_index(drop=True)
        r_b2 = two_way_cluster_bootstrap_all_metrics(g, "RR_Abstain_matched", "B2_age_matched", reps=1000, seed=20261117)
        for pname in ("B2_age_matched", "MG_matched", "RR_Abstain_matched"):
            vals = g[pname].to_numpy()
            crop_rows.append(
                {
                    "crop_slice": cname_sl,
                    "n": int(len(g)),
                    "policy": pname,
                    "dispatch_rate": round(float(g[f"{pname}_disp"].mean()), 4),
                    "mean": round(float(vals.mean()), 2),
                    "ep_loss_rate": round(float((vals < 0).mean()), 4),
                    "es10": round(float(es10(vals)), 2),
                    "diff_vs_B2_mean_ci95": f"[{r_b2['mean']['ci95_low']:.2f}, {r_b2['mean']['ci95_high']:.2f}]" if pname == "RR_Abstain_matched" else "",
                    "diff_vs_B2_es10_ci95": f"[{r_b2['es10']['ci95_low']:.2f}, {r_b2['es10']['ci95_high']:.2f}]" if pname == "RR_Abstain_matched" else "",
                }
            )
    pd.DataFrame(crop_rows).to_csv(out_dir / "a10_crop_splits.csv", index=False)

    # Missing-price stability across div in [0..2.0] and heterogeneous missingness
    miss_rows = []
    y_zero = settle_candidates(test, div=0.0, disc=0.0)
    y_mild = settle_candidates(test, div=0.5, disc=0.05)
    y_harsh = settle_candidates(test, div=2.0, disc=0.20)
    rep14 = test["dest_exact_rep_14d"].to_numpy()
    comm = test["Commodity"].to_numpy()

    for label, y_arr in (
        ("div_0.0_disc_0.00", y_zero),
        ("div_0.5_disc_0.10", settle_candidates(test, div=0.5, disc=0.10)),
        ("div_1.0_disc_0.10", settle_candidates(test, div=1.0, disc=0.10)),
        ("div_1.5_disc_0.10_base", test["y"].to_numpy(dtype=np.float64)),
        ("div_2.0_disc_0.10", settle_candidates(test, div=2.0, disc=0.10)),
        ("het_crop_perishability", np.where(comm == "Tomato", y_harsh, np.where(comm == "Potato", y_mild, test["y"].to_numpy(dtype=np.float64)))),
        ("het_selective_missing_lowrep_harsh", np.where(rep14 < 0.50, y_harsh, y_mild)),
    ):
        for pname in ("B1_lagged_screen", "B2_age_matched", "B_simple_activity_matched", "MG_matched", "RR_Abstain_matched"):
            ch = policies_test[pname]
            rec = summarize_chosen(pname, ch, y_override=y_arr[ch["_i"].to_numpy()])
            rec["missing_scenario"] = label
            miss_rows.append(rec)
    pd.DataFrame(miss_rows).to_csv(out_dir / "a10_missing_stability.csv", index=False)

    # Zero-retuning test on Lagged HP Graded Apples (N = 2,802)
    hp = pd.read_parquet(out_dir / "lagged_hp_apple_candidates.parquet")
    hp["date"] = pd.to_datetime(hp["date"])
    hp["y"] = settle_candidates(hp, how="sequential", weather="none", div=1.5, disc=0.10)
    hp_rows = []
    for w_lbl, sub_hp in (("ALL_2025_2026", hp), ("POST_JUNE_2026", hp[hp["date"] >= pd.Timestamp("2026-06-01")].reset_index(drop=True))):
        hf = compute_decision_features(sub_hp)
        age_hp = (hf["age"] >= 1) & (hf["age"] <= 3)
        sc_hp = rr_abstain_score(sub_hp, kappa_star)
        sc_hp_dag = rr_abstain_score(sub_hp, kappa_dag)
        hp_pols = {
            "B2_age_matched": pick_episode(sub_hp, hf["net_road_fee"], age_hp & (hf["net_road_fee"] > th_base["B2_age_matched"])),
            "MG_matched": pick_episode(sub_hp, hf["net_road_fee_spoil"], age_hp & (hf["rep14"] >= 0.50) & (hf["dow8"] >= 0.35) & (hf["net_road_fee_spoil"] > m_mg_match)),
            "RR_Abstain_matched": pick_episode(sub_hp, sc_hp, age_hp & (sc_hp > m_star_matched)),
            "RR_Abstain_val": pick_episode(sub_hp, sc_hp_dag, age_hp & (sc_hp_dag > m_dag)),
        }
        for pname, ch_hp in hp_pols.items():
            rec = summarize_chosen(pname, ch_hp)
            rec["window"] = w_lbl
            hp_rows.append(rec)
    pd.DataFrame(hp_rows).to_csv(out_dir / "a10_hp_apple.csv", index=False)

    # Extended kappa profile [0..20] diagnostic exposing ceiling artifact at kappa=5 vs physical kappa=1.5
    kappa_prof = []
    for kv in [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0]:
        sc_v = rr_abstain_score(val, kv)
        sc_t = rr_abstain_score(test, kv)
        mm_val = find_val_matched_threshold(val, sc_v, age_val_gate, target_val_disp)
        r_val_m = summarize_chosen(f"RR_val_k{kv}", pick_episode(val, sc_v, age_val_gate & (sc_v > mm_val)))
        r_test_m = summarize_chosen(f"RR_test_matched_k{kv}", pick_episode(test, sc_t, age_test_gate & (sc_t > mm_val)))
        r_test_0 = summarize_chosen(f"RR_test_m0_k{kv}", pick_episode(test, sc_t, age_test_gate & (sc_t > 0.0)))
        kappa_prof.append({
            "kappa": kv,
            "m_match_val": round(mm_val, 2),
            "val_matched_mean": r_val_m["mean"],
            "val_matched_es10": r_val_m["es10"],
            "test_matched_disp": r_test_m["dispatch_rate"],
            "test_matched_mean": r_test_m["mean"],
            "test_matched_ep_loss": r_test_m["ep_loss_rate"],
            "test_matched_es10": r_test_m["es10"],
            "test_m0_disp": r_test_0["dispatch_rate"],
            "test_m0_mean": r_test_0["mean"],
            "test_m0_es10": r_test_0["es10"],
        })

    meta = {
        "kappa_star_matched": kappa_star,
        "m_star_matched": round(m_star_matched, 4),
        "kappa_dag_unconstrained": kappa_dag,
        "m_dag_unconstrained": round(m_dag, 4),
        "target_b2_val_dispatch": target_val_disp,
        "val_sweep_matched": val_sweep_rows,
        "kappa_profile_0_to_20": kappa_prof,
        "prereg_commit": "87a0b62dda1b5fcf99ce6c93581c3006437eca09",
        "exploratory": True,
    }
    (out_dir / "a10_summary.json").write_text(json.dumps(meta, indent=2, default=float))

    print(f"Chosen on val: kappa_star={kappa_star}, m_star_matched={m_star_matched:.2f}; unconstrained: kappa_dag={kappa_dag}, m_dag={m_dag:.2f}")
    print("\n=== A10 RESULTS TABLE ===")
    print(pd.DataFrame(res_rows)[["policy", "dispatch_rate", "mean", "ep_loss_rate", "cond_loss_rate", "es10"]].to_string(index=False))
    print("\n=== PRE-REGISTERED H_A10_1..4 HOLM SUMMARY (origin_x_2week) ===")
    print(boot_df[(boot_df["cluster"] == "origin_x_2week") & (boot_df["hypothesis_id"] != "")][["hypothesis_id", "metric", "estimate", "ci95_low", "ci95_high", "p_value", "p_holm"]].to_string(index=False))
    print("\n=== PRE-REGISTERED H_A10_1..4 HOLM SUMMARY (b2dest_or_origin_x_2week) ===")
    print(boot_df[(boot_df["cluster"] == "b2dest_or_origin_x_2week") & (boot_df["hypothesis_id"] != "")][["hypothesis_id", "metric", "estimate", "ci95_low", "ci95_high", "p_value", "p_holm"]].to_string(index=False))
    print("\n=== A10 VS MG_matched (ALL METRICS) ===")
    print(boot_df[boot_df["contrast"] == "H_A10_vs_MG_matched"][["cluster", "metric", "estimate", "ci95_low", "ci95_high", "p_value_two_sided"]].to_string(index=False))
    print("\n=== A10 CROP SPLITS ===")
    print(pd.DataFrame(crop_rows).to_string(index=False))
    print("\n=== A10 HP APPLE LAGGED ===")
    print(pd.DataFrame(hp_rows).to_string(index=False))


if __name__ == "__main__":
    run()
