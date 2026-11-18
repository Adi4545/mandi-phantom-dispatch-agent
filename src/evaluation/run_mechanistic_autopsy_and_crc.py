"""Stage-II Mechanistic Autopsy (Exp 16) & Validation-Calibrated Uncensored Conformal Risk Control (Exp 17).

Note on Scientific Separation:
  - Stage I (H1-H4, Exp 1-Exp 15) preserves pre-registered commit e421d15 untouched.
  - Stage II runs Exp 16 (diagnostic root-cause proof of Censored-Arrival Survivorship Bias,
    Heteroscedastic Coverage Illusion, and HP Apple Sub-Grade T1 Sparsity) and Exp 17
    ([POST-DIAGNOSTIC / VALIDATION-CALIBRATED] 4-rung factorial evaluation of MandiGuard-CRC
    with parameters trained solely on Train_2024 and calibrated solely on Val_2025H1).
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.baselines.dispatch_baselines import (
    eval_b1_naive_screen_greedy,
    eval_b2_fresh_road_greedy,
    eval_b3_ml_point_dispatch,
)
from src.evaluation.bootstrap import two_way_mandi_week_bootstrap
from src.evaluation.payoff_model import PayoffParams
from src.models.uncensored_crc_forecaster import (
    CRCConfig,
    UncensoredCRCForecaster,
    compute_vectorized_static_payoff,
    evaluate_mandiguard_crc,
)
from src.utils.leakage import assert_no_future_leakage_dates, load_config

LOT_SIZE_QTL = 30.0


def _cvar10(vals: np.ndarray) -> float:
    arr = vals[np.isfinite(vals)]
    if len(arr) == 0:
        return 0.0
    q10 = np.quantile(arr, 0.10)
    tail = arr[arr <= q10]
    return float(tail.mean()) if len(tail) > 0 else float(q10)


def _summarize(name: str, dfp: pd.DataFrame, scope: str, extra: str = "") -> Dict[str, object]:
    disp = dfp["is_dispatch"].to_numpy(dtype=bool)
    dnet = dfp["delta_net_inr"].to_numpy(dtype=np.float64)
    mean_d = float(dnet.mean())
    ltr = float((dnet[disp] < 0.0).mean() * 100.0) if disp.any() else 0.0
    trap = float(dfp.loc[disp, "is_closed_trap"].mean() * 100.0) if disp.any() else 0.0
    ep_loss = float((dnet < 0.0).mean() * 100.0)
    return {
        "evaluation_scope": scope,
        "subgroup": extra if extra else "ALL",
        "policy": name,
        "n_episodes": int(len(dfp)),
        "dispatch_rate_pct": round(float(disp.mean() * 100.0), 2),
        "mean_delta_net_inr": round(mean_d, 2),
        "lot_30qtl_gain_inr": round(mean_d * LOT_SIZE_QTL, 1),
        "cond_phantom_loss_rate_pct": round(ltr, 2),
        "ep_phantom_loss_pct": round(ep_loss, 2),
        "cond_closed_or_trap_rate_pct": round(trap, 2),
        "cvar_10_inr": round(_cvar10(dnet), 2),
        "avg_tool_calls": round(float(dfp["tool_calls_total"].mean()), 2),
    }


def run_exp16_mechanistic_autopsy(
    root: Path,
    cand_6s: pd.DataFrame,
    cand_ap: pd.DataFrame,
    splits: Dict[str, str],
    hurdle_inr: float,
    margin: float,
    cfg: Dict[str, object],
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    tr = cand_6s[cand_6s["date_dt"] <= splits["train_end"]].copy()
    tr_arr_clean = cand_6s[(cand_6s["date_dt"] <= splits["train_end"]) & (cand_6s["arr_dt"] <= splits["train_end"])].copy()
    va = cand_6s[
        (cand_6s["date_dt"] >= splits["val_start"])
        & (cand_6s["date_dt"] <= splits["val_end"])
        & (cand_6s["arr_dt"] <= splits["val_end"])
    ].copy()
    assert_no_future_leakage_dates(tr_arr_clean, va, cfg)
    ho = cand_6s[(cand_6s["date_dt"] >= splits["test_start"]) & (cand_6s["arr_dt"] <= splits["test_end"])].copy()

    # 1. Censored-Arrival Survivorship Bias across dest_age_days = 0..3
    for split_name, sub_df in [("Train_2024", tr), ("Holdout_2025_2026", ho)]:
        t1_sub = sub_df[
            (sub_df["dest_ref_price"].notna())
            & (sub_df["dest_ref_price"] > 0)
            & (sub_df["dest_age_days"] <= 3)
            & (sub_df["dest_open_prob_14d"] >= 0.50)
            & (sub_df["dest_dow_open_rate"] >= 0.35)
        ].copy()
        _, _, _, snet, _ = compute_vectorized_static_payoff(t1_sub)
        gross = t1_sub["real_delta_net_inr"].to_numpy(dtype=np.float64) + t1_sub["local_price"].to_numpy(dtype=np.float64) + t1_sub["real_freight_inr"].to_numpy(dtype=np.float64)
        t1_sub["uncensored_ret"] = np.clip((gross - t1_sub["dest_ref_price"].to_numpy(dtype=np.float64)) / t1_sub["dest_ref_price"].to_numpy(dtype=np.float64), -1.2, 0.8)
        for age_d, grp in t1_sub.groupby("dest_age_days"):
            cens = grp["target_ret"].dropna()
            unc = grp["uncensored_ret"]
            rows.append(
                {
                    "diagnostic_family": "1_Censored_Arrival_Bias",
                    "split": split_name,
                    "stratum": f"age_{int(age_d)}d",
                    "n_rows": int(len(grp)),
                    "metric_a_name": "censored_d0_q20_pct",
                    "metric_a_val": round(float(np.quantile(cens, 0.20) * 100.0), 2),
                    "metric_b_name": "uncensored_q20_pct",
                    "metric_b_val": round(float(np.quantile(unc, 0.20) * 100.0), 2),
                    "metric_c_name": "exact_d0_open_rate_pct",
                    "metric_c_val": round(float(grp["target_ret"].notna().mean() * 100.0), 2),
                }
            )

    # 2. Heteroscedastic Marginal Coverage Illusion across Volatility Quartiles
    for split_name, sub_df in [("Val_2025H1", va), ("Holdout_2025_2026", ho)]:
        op = sub_df.dropna(subset=["target_ret"]).copy()
        op["covered"] = op["target_ret"] >= op["lcb_ret"]
        op["cushion"] = op["pred_ret"] - op["lcb_ret"]
        op["err"] = op["pred_ret"] - op["target_ret"]
        qbins = pd.qcut(op["dest_vol_14d"], 4, labels=["Q1_Calm", "Q2_Mod", "Q3_Elevated", "Q4_Volatile"])
        for qname, grp in op.groupby(qbins, observed=False):
            rows.append(
                {
                    "diagnostic_family": "2_Heteroscedastic_Coverage_Illusion",
                    "split": split_name,
                    "stratum": str(qname),
                    "n_rows": int(len(grp)),
                    "metric_a_name": "empirical_coverage_pct",
                    "metric_a_val": round(float(grp["covered"].mean() * 100.0), 2),
                    "metric_b_name": "issued_cushion_pct",
                    "metric_b_val": round(float(grp["cushion"].mean() * 100.0), 2),
                    "metric_c_name": "true_err_q80_pct",
                    "metric_c_val": round(float(np.quantile(grp["err"], 0.80) * 100.0), 2),
                }
            )

    # 3. HP Apple Refusal Attribution (Warmup vs Test): T1 Sub-Grade Sparsity vs T4 LCB
    wu_ap = cand_ap[(cand_ap["date_dt"] <= "2026-05-31") & (cand_ap["arr_dt"] <= "2026-05-31")].copy()
    ho_ap = cand_ap[
        (cand_ap["date_dt"] >= splits["apple_test_start"])
        & (cand_ap["date_dt"] <= "2026-08-27")
        & (cand_ap["arr_dt"] <= splits["apple_test_end"])
    ].copy()
    for split_name, ap_sub in [("HP_Warmup_to_2026_05", wu_ap), ("HP_Apple_Holdout_2026", ho_ap)]:
        b2_a = eval_b2_fresh_road_greedy(ap_sub, hurdle_inr=hurdle_inr)
        mg_a, _ = evaluate_mandiguard_vectorized(ap_sub, AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=5, safety_margin_inr=margin))
        m = b2_a.merge(mg_a[["episode_id", "is_dispatch", "reason"]], on="episode_id", suffixes=("_b2", "_mg"))
        sub_ref = m[m["is_dispatch_b2"] & (~m["is_dispatch_mg"])]
        t1_cnt = int(sub_ref["reason"].isin(["VARIETY_OR_STALE", "CLOSED_YARD_RISK"]).sum())
        t4_cnt = int((sub_ref["reason"] == "ARRIVAL_REVERSION_RISK").sum())
        tot_ref = max(1, len(sub_ref))
        rows.append(
            {
                "diagnostic_family": "3_HP_Apple_Refusal_Attribution",
                "split": split_name,
                "stratum": "B2_Disp_MG_Refuse",
                "n_rows": int(len(sub_ref)),
                "metric_a_name": "blocked_by_T1_pct",
                "metric_a_val": round(100.0 * t1_cnt / tot_ref, 2),
                "metric_b_name": "blocked_by_T4_LCB_pct",
                "metric_b_val": round(100.0 * t4_cnt / tot_ref, 2),
                "metric_c_name": "b2_realized_mean_inr_qtl",
                "metric_c_val": round(float(sub_ref["delta_net_inr"].mean()), 2),
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(root / "results/exp16_censored_bias_and_coverage_illusion.csv", index=False)
    print("\n=== EXP 16: MECHANISTIC AUTOPSY ===")
    print(out.to_string(index=False))
    return out


def run_exp17_uncensored_crc(
    root: Path,
    cand_6s: pd.DataFrame,
    cand_ap: pd.DataFrame,
    splits: Dict[str, str],
    hurdle_inr: float,
    margin: float,
    seed: int,
    reps: int,
    cfg: Dict[str, object],
) -> None:
    tr = cand_6s[cand_6s["date_dt"] <= splits["train_end"]].copy()
    tr_arr_clean = cand_6s[(cand_6s["date_dt"] <= splits["train_end"]) & (cand_6s["arr_dt"] <= splits["train_end"])].copy()
    va = cand_6s[
        (cand_6s["date_dt"] >= splits["val_start"])
        & (cand_6s["date_dt"] <= splits["val_end"])
        & (cand_6s["arr_dt"] <= splits["val_end"])
    ].copy()
    assert_no_future_leakage_dates(tr_arr_clean, va, cfg)
    ho = cand_6s[(cand_6s["date_dt"] >= splits["test_start"]) & (cand_6s["arr_dt"] <= splits["test_end"])].copy()

    ho_ap = cand_ap[
        (cand_ap["date_dt"] >= splits["apple_test_start"])
        & (cand_ap["date_dt"] <= "2026-08-27")
        & (cand_ap["arr_dt"] <= splits["apple_test_end"])
    ].copy()
    ho_ap["Grade"] = ho_ap["Variety_Key"].astype(str).str.split("|").str[-1].str.strip()

    # Fair matched open-d0 cohort (identical 10,162 episodes from Exp 15)
    ho_sort = ho.sort_values(["episode_id", "screen_spread", "dest_market"], ascending=[True, False, True])
    top_k = ho_sort[ho_sort["screen_spread"] > hurdle_inr].groupby("episode_id").head(5)
    ep_d0 = top_k.groupby("episode_id")["dest_modal_d0"].apply(lambda s: s.notna().all())
    ho_open_d0 = ho[ho["episode_id"].isin(set(ep_d0[ep_d0].index))].copy()

    # Train Strict-T1 and Thin-Aware UncensoredCRCForecasters solely on Train_2024, calibrate strictly on Val_2025H1!
    cfg_strict = CRCConfig(thin_grade_aware_t1=False, use_euclid_step0_sort=True, safety_margin_inr=margin, beta_target=0.095)
    cfg_full = CRCConfig(thin_grade_aware_t1=True, use_euclid_step0_sort=True, safety_margin_inr=margin, beta_target=0.095)

    fc_strict = UncensoredCRCForecaster(seed=seed).fit(tr, cfg_strict)
    cal_strict = fc_strict.calibrate_crc_lambda(va, cfg_strict)
    fc_full = UncensoredCRCForecaster(seed=seed).fit(tr, cfg_full)
    cal_full = fc_full.calibrate_crc_lambda(va, cfg_full)
    print(f"\n[CRC Calibrated Strictly on Val_2025H1] StrictT1={cal_strict} | MandiGuard-CRC={cal_full}")

    def _run_suite(scope_name: str, sub_df: pd.DataFrame, by_grade: bool = False) -> tuple[List[Dict], Dict[str, pd.DataFrame]]:
        b1 = eval_b1_naive_screen_greedy(sub_df, hurdle_inr=hurdle_inr)
        b2 = eval_b2_fresh_road_greedy(sub_df, hurdle_inr=hurdle_inr)
        b3 = eval_b3_ml_point_dispatch(sub_df, safety_margin_inr=margin)
        mg_v1, _ = evaluate_mandiguard_vectorized(sub_df, AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=5, safety_margin_inr=margin))

        # Rung 1: MG_v1 + free Euclidean Step-0 sort (zero ML/conformal change)
        sub_euc = sub_df.copy()
        hp_m = np.where(sub_euc["State"] == "Himachal Pradesh", 1.45, 1.0)
        sub_euc["screen_spread"] = sub_df["screen_spread"] - (35.0 + 0.45 * hp_m * 1.20 * sub_euc["euclid_km"])
        rung1, _ = evaluate_mandiguard_vectorized(sub_euc, AgentConfig(screen_hurdle_inr=hurdle_inr, k_max=5, safety_margin_inr=margin))

        # Rung 2: Strict T1 + Euclid Step-0 + Uncensored Price-Scaled CRC
        p_str = fc_strict.predict_components(sub_df)
        rung2 = evaluate_mandiguard_crc(sub_df, cfg=cfg_strict, lambda_risk=fc_strict.lambda_star, precomputed=p_str)

        # Rung 3: MandiGuard-CRC (Thin-Grade-Aware T1 + Euclid Step-0 + Uncensored Price-Scaled CRC)
        p_ful = fc_full.predict_components(sub_df)
        rung3 = evaluate_mandiguard_crc(sub_df, cfg=cfg_full, lambda_risk=fc_full.lambda_star, precomputed=p_ful)

        pols = {
            "B1_NaiveScreen": b1,
            "B2_FreshRoad": b2,
            "B3_MLPoint": b3,
            "MG_v1_PreReg": mg_v1,
            "Rung1_EuclidStep0": rung1,
            "Rung2_UncensoredCRC_StrictT1": rung2,
            "Rung3_MandiGuard_CRC": rung3,
        }
        s_rows = [_summarize(pn, pd_df, scope_name) for pn, pd_df in pols.items()]
        if by_grade:
            gmap = sub_df[["episode_id", "Grade"]].drop_duplicates("episode_id").set_index("episode_id")["Grade"]
            for pn, pd_df in pols.items():
                tmp = pd_df.copy()
                tmp["Grade"] = tmp["episode_id"].map(gmap)
                for grd in ["Grade A", "Grade B"]:
                    gdf = tmp[tmp["Grade"] == grd]
                    if len(gdf) > 0:
                        s_rows.append(_summarize(pn, gdf, scope_name, extra=grd))
        return s_rows, pols

    all_rows: List[Dict] = []
    rows_va, _ = _run_suite("Val_2025H1", va)
    all_rows.extend(rows_va)
    rows_ho, pols_ho = _run_suite("Holdout_2025_2026", ho)
    all_rows.extend(rows_ho)
    rows_d0, _ = _run_suite("Matched_AllTopK_Observed_d0", ho_open_d0)
    all_rows.extend(rows_d0)
    rows_ap, _ = _run_suite("HP_Apple_Grade_2026", ho_ap, by_grade=True)
    all_rows.extend(rows_ap)

    exp17_df = pd.DataFrame(all_rows)
    exp17_df["val_calibrated_lambda_star"] = cal_full["lambda_star"]
    lam_map = {
        "Rung2_UncensoredCRC_StrictT1": cal_strict["lambda_star"],
        "Rung3_MandiGuard_CRC": cal_full["lambda_star"],
    }
    exp17_df["policy_lambda_used"] = exp17_df["policy"].map(lam_map).fillna(0.0)
    exp17_df.to_csv(root / "results/exp17_uncensored_crc_validation.csv", index=False)
    print("\n=== EXP 17: VALIDATION-CALIBRATED UNCENSORED CRC FACTORIAL BENCHMARK ===")
    print(exp17_df[exp17_df["subgroup"] == "ALL"].to_string(index=False))

    # Two-Way Origin-Mandi x 2-Week-Block Cluster Bootstrap on Holdout_2025_2026 (R = 5,000)
    ep_meta = ho[["episode_id", "origin_market_key", "date"]].drop_duplicates("episode_id").copy()
    for pn in ["B1_NaiveScreen", "B2_FreshRoad", "B3_MLPoint", "MG_v1_PreReg", "Rung3_MandiGuard_CRC"]:
        pm = pols_ho[pn].set_index("episode_id")
        ep_meta[f"{pn}_dnet"] = ep_meta["episode_id"].map(pm["delta_net_inr"]).to_numpy(dtype=np.float64)
        ep_meta[f"{pn}_phantom"] = ep_meta["episode_id"].map(pm["is_phantom_loss"]).to_numpy(dtype=np.float64)

    boot_specs = [
        ("MandiGuard_CRC vs B1_NaiveScreen Mean dNet", "Rung3_MandiGuard_CRC_dnet", "B1_NaiveScreen_dnet", "greater"),
        ("MandiGuard_CRC vs B2_FreshRoad Mean dNet", "Rung3_MandiGuard_CRC_dnet", "B2_FreshRoad_dnet", "greater"),
        ("MandiGuard_CRC vs MG_v1_PreReg Mean dNet", "Rung3_MandiGuard_CRC_dnet", "MG_v1_PreReg_dnet", "greater"),
        ("MandiGuard_CRC vs B3_MLPoint Ep Phantom Loss", "Rung3_MandiGuard_CRC_phantom", "B3_MLPoint_phantom", "less"),
    ]
    boot_rows = []
    for desc, ca, cb, d in boot_specs:
        br = two_way_mandi_week_bootstrap(ep_meta, ca, cb, reps=reps, seed=seed, direction=d)
        boot_rows.append(
            {
                "comparison": desc,
                "direction": d,
                "estimate": round(br["estimate"], 4),
                "ci95_low": round(br["ci95_low"], 4),
                "ci95_high": round(br["ci95_high"], 4),
                "p_raw_phipson_smyth": round(br["p_value"], 6),
                "n_episodes": br["n"],
                "n_origin_mandis": br["n_mandis"],
                "n_2week_blocks": br["n_blocks"],
            }
        )
    boot_df = pd.DataFrame(boot_rows)
    boot_df.to_csv(root / "results/exp17_crc_bootstrap_comparisons.csv", index=False)
    print("\n=== EXP 17: TWO-WAY BOOTSTRAP (MANDIGUARD-CRC vs COMPARATORS) ===")
    print(boot_df.to_string(index=False))


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root)
    splits = cfg["temporal_splits"]
    seed = int(cfg["master_seed"])
    reps = int(cfg["evaluation"]["bootstrap_reps"])
    cal_info = json.loads((root / "configs/frozen_calibration.json").read_text())
    margin = float(cal_info["frozen_safety_margin_inr"])
    hurdle_inr = float(cfg["agent_defaults"]["screen_hurdle_inr_qtl"])

    with open(root / "data/interim/forecaster_2024.pkl", "rb") as f:
        fc_v1 = pickle.load(f)

    cand_6s = pd.read_parquet(root / "data/processed/candidates_6state.parquet")
    cand_6s["date_dt"] = pd.to_datetime(cand_6s["date"])
    cand_6s["arr_dt"] = pd.to_datetime(cand_6s["arrival_date"])
    c_post = cand_6s[cand_6s["date_dt"] >= splits["val_start"]].copy()
    pr_v1, lr_v1 = fc_v1.predict_point_and_causal_lcb(c_post)
    cand_6s["pred_ret"] = np.nan
    cand_6s["lcb_ret"] = np.nan
    cand_6s.loc[c_post.index, "pred_ret"] = pr_v1
    cand_6s.loc[c_post.index, "lcb_ret"] = lr_v1

    cand_ap = pd.read_parquet(root / "data/processed/candidates_hp_apple_grade.parquet")
    cand_ap["date_dt"] = pd.to_datetime(cand_ap["date"])
    cand_ap["arr_dt"] = pd.to_datetime(cand_ap["arrival_date"])
    ap_pr, ap_lr = fc_v1.predict_point_and_causal_lcb(cand_ap)
    cand_ap["pred_ret"] = ap_pr
    cand_ap["lcb_ret"] = ap_lr

    run_exp16_mechanistic_autopsy(root, cand_6s, cand_ap, splits, hurdle_inr, margin, cfg)
    run_exp17_uncensored_crc(root, cand_6s, cand_ap, splits, hurdle_inr, margin, seed, reps, cfg)


if __name__ == "__main__":
    main()
