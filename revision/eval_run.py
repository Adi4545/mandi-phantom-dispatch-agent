"""Evaluate strictly lagged dispatch rules under sequential settlement (Step 3 / A4-A7).

Primary settlement is strictly sequential over arrival days d in {0, 1, 2}:
  - Sell if exact-variety Modal_Price is recorded on day d (wait_days = d).
  - Wait 1 day only if exact variety is missing AND some other variety of the same
    commodity traded on day d (adds ₹25/qtl detention and 24h spoilage).
  - Return / divert immediately if no variety of the commodity traded on day d.
Statutory APMC seller fees are charged strictly on destination post-spoilage gross
sale realization (`fee_rate * sale_price * (1 - sp)`), and are 0 on same-district
or no-sale diversion turns (`M9` fix).

Thresholds are tuned ONLY on 2025-01-01..2025-05-31 (`val`). Because 2025-06-01..2026-04-08
(`test`) was previously inspected in repo history, `summary.json` explicitly sets
`exploratory: true` (`R5`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

from revision.build_variant import spoil_frac_ref
from revision.es10 import es10
from revision.stats_utils import ci95_single_metric, two_way_cluster_bootstrap_all_metrics
from src.evaluation.bootstrap import holm_bonferroni

ROOT = Path(__file__).resolve().parents[1]
THRESH_GRID = [0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 500.0]


def _wx(df: pd.DataFrame, mode: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(df)
    if mode == "none":
        return np.full(n, 20.0), np.full(n, 65.0), np.zeros(n)
    if mode == "clim2024":
        return (
            df["clim_tmax_2024"].fillna(20.0).to_numpy(dtype=np.float64),
            df["clim_rh_2024"].fillna(65.0).to_numpy(dtype=np.float64),
            df["clim_rain_2024"].fillna(0.0).to_numpy(dtype=np.float64),
        )
    raise ValueError(mode)


def settle_candidates(
    df: pd.DataFrame,
    how: str = "sequential",
    weather: str = "none",
    div: float = 1.5,
    disc: float = 0.10,
    freight_base: float = 35.0,
    freight_per_km: float = 0.45,
    hp_km_mult: float = 1.45,
    fee_mult: float = 1.0,
    arhtiya_rate: float = 0.0,
    spoil_mult: float = 1.0,
    detention_per_day: float = 25.0,
    outside_option: str = "d0",
    return_outcomes: bool = False,
) -> np.ndarray | Tuple[np.ndarray, np.ndarray]:
    """Return modeled net gain (INR/qtl) vs selling locally under sequential or hindsight settlement."""
    n = len(df)
    comm = df["Commodity"].to_numpy()
    hours = df["truck_hours"].to_numpy(dtype=np.float64)
    hp = np.where(df["State"].to_numpy() == "Himachal Pradesh", hp_km_mult, 1.0)
    f_road = freight_base + freight_per_km * hp * df["road_km"].to_numpy(dtype=np.float64)

    base_fee_rate = df["fee_rate"].to_numpy(dtype=np.float64)
    same = df["same_district"].to_numpy(dtype=bool)
    stat_rate = np.where(same, 0.0, fee_mult * base_fee_rate)
    sale_fee_rate = np.clip(stat_rate + arhtiya_rate, 0.0, 0.30)

    if outside_option == "d0":
        local = df["settle_local_price_d0"].to_numpy(dtype=np.float64)
    elif outside_option == "lag":
        local = df["origin_lag_price"].to_numpy(dtype=np.float64)
    else:
        raise ValueError(outside_option)

    tmax, rh, rain = _wx(df, weather)
    p_ex = [df[f"settle_dest_modal_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]
    p_an = [df[f"settle_any_min_d{d}"].to_numpy(dtype=np.float64) for d in (0, 1, 2)]

    out = np.empty(n, dtype=np.float64)
    otypes = np.empty(n, dtype=object)

    def _sp(idx: np.ndarray, wait: int) -> np.ndarray:
        raw_sp = spoil_frac_ref(
            comm[idx],
            hours[idx],
            np.full(int(idx.sum()), wait, dtype=np.float64),
            tmax[idx],
            rh[idx],
            rain[idx],
        )
        return np.clip(spoil_mult * raw_sp, 0.0, 0.55)

    def _sell_delta(idx: np.ndarray, sale_p: np.ndarray, wait: int) -> np.ndarray:
        sp = _sp(idx, wait)
        gross_sale = sale_p * (1.0 - sp)
        net_after_fee = gross_sale * (1.0 - sale_fee_rate[idx])
        return net_after_fee - f_road[idx] - detention_per_day * wait - local[idx]

    def _divert_delta(idx: np.ndarray, wait: int) -> np.ndarray:
        sp = _sp(idx, wait)
        # Zero yard sale -> zero destination statutory/commission fee (`M9` fixed!)
        return -div * f_road[idx] - local[idx] * sp - detention_per_day * wait

    if how == "hindsight":
        taken = np.zeros(n, dtype=bool)
        for w in (0, 1, 2):
            ok = (~taken) & np.isfinite(p_ex[w]) & (p_ex[w] > 0)
            if ok.any():
                out[ok] = _sell_delta(ok, p_ex[w][ok], w)
                otypes[ok] = f"exact_d{w}"
                taken |= ok
        rest = ~taken
        if rest.any():
            amin0 = p_an[0]
            use_other = rest & np.isfinite(amin0) & (amin0 > 0)
            no_other = rest & ~use_other
            if use_other.any():
                out[use_other] = _sell_delta(use_other, amin0[use_other] * (1.0 - disc), 0)
                otypes[use_other] = "other_var_distress_d0"
            if no_other.any():
                out[no_other] = _divert_delta(no_other, 0)
                otypes[no_other] = "no_comm_divert_d0"
        return (out, otypes) if return_outcomes else out

    if how != "sequential":
        raise ValueError(how)

    taken = np.zeros(n, dtype=bool)
    for d in (0, 1, 2):
        exact = (~taken) & np.isfinite(p_ex[d]) & (p_ex[d] > 0)
        if exact.any():
            out[exact] = _sell_delta(exact, p_ex[d][exact], d)
            otypes[exact] = f"exact_d{d}" if d == 0 else f"exact_wait_d{d}"
            taken |= exact
        if d == 2:
            rest = ~taken
            if rest.any():
                amin2 = p_an[2]
                use_other = rest & np.isfinite(amin2) & (amin2 > 0)
                no_other = rest & ~use_other
                if use_other.any():
                    out[use_other] = _sell_delta(use_other, amin2[use_other] * (1.0 - disc), 2)
                    otypes[use_other] = "other_var_distress_d2"
                if no_other.any():
                    out[no_other] = _divert_delta(no_other, 2)
                    otypes[no_other] = "no_comm_divert_d2"
            break
        active_any = np.isfinite(p_an[d]) & (p_an[d] > 0)
        give_up = (~taken) & (~active_any)
        if give_up.any():
            out[give_up] = _divert_delta(give_up, d)
            otypes[give_up] = f"no_comm_divert_d{d}"
            taken |= give_up

    return (out, otypes) if return_outcomes else out


def compute_decision_features(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """Precompute strictly < t decision score arrays from lagged columns ONLY (zero settle_* access)."""
    p_dest = df["dest_lag_price"].to_numpy(dtype=np.float64)
    p_orig = df["origin_lag_price"].to_numpy(dtype=np.float64)
    f_road = df["freight_road"].to_numpy(dtype=np.float64)
    f_euc = df["freight_euclid"].to_numpy(dtype=np.float64)
    fee_r = df["fee_rate"].to_numpy(dtype=np.float64)
    sp0 = df["spoil_ref_0"].to_numpy(dtype=np.float64)

    sp_clim = spoil_frac_ref(
        df["Commodity"].to_numpy(),
        df["truck_hours"].to_numpy(dtype=np.float64),
        np.zeros(len(df), dtype=np.float64),
        df["clim_tmax_2024"].fillna(20.0).to_numpy(dtype=np.float64),
        df["clim_rh_2024"].fillna(65.0).to_numpy(dtype=np.float64),
        df["clim_rain_2024"].fillna(0.0).to_numpy(dtype=np.float64),
    )

    net_road_fee = p_dest * (1.0 - fee_r) - p_orig - f_road
    net_road_fee_spoil = p_dest * (1.0 - sp0) * (1.0 - fee_r) - p_orig - f_road
    net_euc_fee_spoil = p_dest * (1.0 - sp0) * (1.0 - fee_r) - p_orig - f_euc
    net_clim_fee_spoil = p_dest * (1.0 - sp_clim) * (1.0 - fee_r) - p_orig - f_road

    return {
        "lag_spread": df["lag_spread"].to_numpy(dtype=np.float64),
        "age": df["dest_lag_age"].to_numpy(dtype=np.float64),
        "rep14": df["dest_exact_rep_14d"].to_numpy(dtype=np.float64),
        "rep28": df["dest_exact_rep_28d"].to_numpy(dtype=np.float64),
        "dow8": df["dest_dow_exact_rep_8w"].to_numpy(dtype=np.float64),
        "net_road_fee": net_road_fee,
        "net_road_fee_spoil": net_road_fee_spoil,
        "net_euc_fee_spoil": net_euc_fee_spoil,
        "net_clim_fee_spoil": net_clim_fee_spoil,
    }


def pick_episode(df: pd.DataFrame, score: np.ndarray, eligible: np.ndarray, y_col: str = "y") -> pd.DataFrame:
    """Pick the highest-scoring eligible candidate per episode; retain episode with eligible=False if all pruned."""
    work = pd.DataFrame(
        {
            "episode_id": df["episode_id"].to_numpy(),
            "date": df["date"].to_numpy(),
            "origin_market_key": df["origin_market_key"].to_numpy(),
            "State": df["State"].to_numpy(),
            "Commodity": df["Commodity"].to_numpy(),
            "dest_market": df["dest_market"].to_numpy(),
            "road_km": df["road_km"].to_numpy(dtype=np.float64),
            "eligible": eligible.astype(bool),
            "eff_score": np.where(eligible, score, -1e18),
            "y_raw": df[y_col].to_numpy(dtype=np.float64),
            "_i": np.arange(len(df), dtype=np.int64),
        }
    )
    if "outcome_type" in df.columns:
        work["outcome_type"] = df["outcome_type"].to_numpy()
    work = work.sort_values(
        ["episode_id", "eligible", "eff_score", "road_km", "dest_market"],
        ascending=[True, False, False, True, True],
        kind="mergesort",
    )
    top = work.groupby("episode_id", as_index=False).head(1).reset_index(drop=True)
    top["y"] = np.where(top["eligible"], top["y_raw"], 0.0)
    return top


def summarize_chosen(name: str, chosen: pd.DataFrame, y_override: np.ndarray | None = None) -> dict:
    dispatched = chosen["eligible"].to_numpy(dtype=bool)
    y_raw = chosen["y_raw"].to_numpy(dtype=np.float64) if y_override is None else y_override
    y = np.where(dispatched, y_raw, 0.0)
    n_ep = int(len(y))
    n_d = int(dispatched.sum())
    cond_loss = (y_raw[dispatched] < 0)
    ep_loss = (y < 0)
    return {
        "policy": name,
        "n": n_ep,
        "dispatch_rate": round(float(dispatched.mean()), 4) if n_ep else None,
        "n_dispatch": n_d,
        "mean": round(float(y.mean()), 2) if n_ep else None,
        "cond_mean": round(float(y_raw[dispatched].mean()), 2) if n_d else None,
        "ep_loss_rate": round(float(ep_loss.mean()), 4) if n_ep else None,
        "cond_loss_rate": round(float(cond_loss.mean()), 4) if n_d else None,
        "es10": round(float(es10(y)), 2) if n_ep else None,
        "loss_given_loss": round(float(y[ep_loss].mean()), 2) if ep_loss.any() else None,
    }


def tune_threshold_on_val(
    val_df: pd.DataFrame,
    val_feat: Dict[str, np.ndarray],
    score_key: str,
    gate_fn: Callable[[Dict[str, np.ndarray]], np.ndarray],
    grid: List[float] = THRESH_GRID,
    min_dispatch: float = 0.25,
) -> Tuple[float, dict]:
    """Tune cutoff strictly on val minimizing episode loss rate (tie-break max mean) with min_dispatch floor."""
    gate = gate_fn(val_feat)
    score = val_feat[score_key]
    best = None
    best_fb = None
    for th in grid:
        chosen = pick_episode(val_df, score, gate & (score > th))
        rec = summarize_chosen("tune", chosen)
        fb_key = (rec["cond_loss_rate"] if rec["cond_loss_rate"] is not None else 1.0, -(rec["mean"] if rec["mean"] is not None else -1e9))
        if best_fb is None or fb_key < best_fb[0]:
            best_fb = (fb_key, float(th), rec)
        if rec["dispatch_rate"] is not None and rec["dispatch_rate"] >= min_dispatch:
            key = (rec["cond_loss_rate"], -rec["mean"])
            if best is None or key < best[0]:
                best = (key, float(th), rec)
    picked = best if best is not None else best_fb
    return picked[1], picked[2]


def find_val_matched_threshold(
    val_df: pd.DataFrame,
    score: np.ndarray,
    gate: np.ndarray,
    target_dispatch: float,
) -> float:
    """Compute exact threshold on validation episode-max eligible scores matching target_dispatch on val."""
    work = pd.DataFrame(
        {
            "episode_id": val_df["episode_id"].to_numpy(),
            "eff": np.where(gate, score, -1e18),
        }
    )
    ep_max = work.groupby("episode_id", sort=False)["eff"].max().to_numpy(dtype=np.float64)
    # Probability(ep_max > th) == target_dispatch -> th = quantile at (1 - target_dispatch)
    q = float(np.clip(1.0 - target_dispatch, 0.0, 1.0))
    return float(np.quantile(ep_max, q))


def run() -> None:
    out_dir = ROOT / "revision" / "results"
    df = pd.read_parquet(out_dir / "lagged_candidates.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df["split"] = np.where(df["date"] <= pd.Timestamp("2025-05-31"), "val", "test")

    y_seq, otypes = settle_candidates(df, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    df["y"] = y_seq
    df["outcome_type"] = otypes

    val = df[df["split"] == "val"].copy().reset_index(drop=True)
    test = df[df["split"] == "test"].copy().reset_index(drop=True)
    val_f = compute_decision_features(val)
    test_f = compute_decision_features(test)

    # Fair equal-menu policy family specs: (name, role, score_key, gate_fn, fixed_threshold_or_None)
    policy_specs = [
        ("B1_lagged_screen", "baseline_screen", "lag_spread", lambda f: np.ones(len(f["age"]), dtype=bool), 100.0),
        ("B2_fresh_100", "baseline_fresh_fixed100", "net_road_fee", lambda f: f["age"] <= 1, 100.0),
        ("B2_fresh_val", "baseline_fresh_val_tuned", "net_road_fee", lambda f: f["age"] <= 1, None),
        ("B2_age_matched", "baseline_age1_3_val_tuned", "net_road_fee", lambda f: (f["age"] >= 1) & (f["age"] <= 3), None),
        ("B2_age7_val", "baseline_age1_7_val_tuned", "net_road_fee", lambda f: (f["age"] >= 1) & (f["age"] <= 7), None),
        ("B_simple_activity", "baseline_simple_activity", "net_road_fee", lambda f: (f["age"] >= 1) & (f["age"] <= 3) & (f["rep14"] >= 0.50), None),
        ("Abl_T2_only", "ablation_T2_road_fee", "net_road_fee", lambda f: (f["age"] >= 1) & (f["age"] <= 3), None),
        ("Abl_T2_T3", "ablation_T2_T3_spoil", "net_road_fee_spoil", lambda f: (f["age"] >= 1) & (f["age"] <= 3), None),
        ("Abl_T1_T2_noT3", "ablation_T1_T2_no_spoil", "net_road_fee", lambda f: (f["age"] >= 1) & (f["age"] <= 3) & (f["rep14"] >= 0.50) & (f["dow8"] >= 0.35), None),
        ("MG_T1_T2_T3_T4", "cautious_T1_T2_T3_T4", "net_road_fee_spoil", lambda f: (f["age"] >= 1) & (f["age"] <= 3) & (f["rep14"] >= 0.50) & (f["dow8"] >= 0.35), None),
        ("Abl_euclid_freight", "ablation_euclid_distance", "net_euc_fee_spoil", lambda f: (f["age"] >= 1) & (f["age"] <= 3) & (f["rep14"] >= 0.50) & (f["dow8"] >= 0.35), None),
        ("Abl_clim2024_spoil", "ablation_2024_clim_spoil", "net_clim_fee_spoil", lambda f: (f["age"] >= 1) & (f["age"] <= 3) & (f["rep14"] >= 0.50) & (f["dow8"] >= 0.35), None),
    ]

    main_rows = []
    chosen_test: Dict[str, pd.DataFrame] = {}
    tuned_thresholds: Dict[str, float] = {}
    val_summaries: Dict[str, dict] = {}

    for pname, role, skey, gfn, fixed_th in policy_specs:
        if fixed_th is None:
            th, vrec = tune_threshold_on_val(val, val_f, skey, gfn)
        else:
            th = float(fixed_th)
            vrec = summarize_chosen(pname, pick_episode(val, val_f[skey], gfn(val_f) & (val_f[skey] > th)))
        tuned_thresholds[pname] = th
        val_summaries[pname] = vrec

        t_gate = gfn(test_f)
        t_elig = t_gate & (test_f[skey] > th)
        ch = pick_episode(test, test_f[skey], t_elig)
        chosen_test[pname] = ch
        row = summarize_chosen(pname, ch)
        row["role"] = role
        row["val_threshold"] = th
        row["val_dispatch_rate"] = vrec["dispatch_rate"]
        main_rows.append(row)

    main_df = pd.DataFrame(main_rows)
    main_df.to_csv(out_dir / "main_table.csv", index=False)

    # Outcome mix across B1, B2_age_matched, B_simple_activity, MG_T1_T2_T3_T4
    om_rows = []
    for pname in ("B1_lagged_screen", "B2_fresh_val", "B2_age_matched", "B_simple_activity", "MG_T1_T2_T3_T4"):
        ch = chosen_test[pname]
        disp = ch[ch["eligible"]]
        vc = disp["outcome_type"].value_counts()
        tot = len(ch)
        for otype, cnt in vc.items():
            om_rows.append({"policy": pname, "outcome_type": str(otype), "count": int(cnt), "pct_episodes": round(100.0 * cnt / tot, 2), "pct_dispatched": round(100.0 * cnt / max(1, len(disp)), 2)})
        abstain = int((~ch["eligible"]).sum())
        om_rows.append({"policy": pname, "outcome_type": "ABSTAIN_HOME", "count": abstain, "pct_episodes": round(100.0 * abstain / tot, 2), "pct_dispatched": 0.0})
    pd.DataFrame(om_rows).to_csv(out_dir / "outcome_mix.csv", index=False)

    # Matched-dispatch calibration strictly from validation percentiles (R4 / M3 fix)
    target_b2_val_disp = float(val_summaries["B2_age_matched"]["dispatch_rate"])
    matched_targets = [("B2_age_matched_val", target_b2_val_disp), ("60pct_val", 0.60), ("70pct_val", 0.70), ("75pct_val", 0.75)]
    matched_rows = []
    matched_chosen_b2 = None
    matched_chosen_mg = None
    for tname, tgt in matched_targets:
        for pname, role, skey, gfn, _ in policy_specs:
            if pname == "B1_lagged_screen":
                continue
            th_m = find_val_matched_threshold(val, val_f[skey], gfn(val_f), tgt)
            ch_m = pick_episode(test, test_f[skey], gfn(test_f) & (test_f[skey] > th_m))
            rec = summarize_chosen(pname, ch_m)
            rec["match_target"] = tname
            rec["target_val_dispatch"] = round(tgt, 4)
            rec["calibrated_threshold"] = round(th_m, 2)
            matched_rows.append(rec)
            if tname == "B2_age_matched_val" and pname == "B2_age_matched":
                matched_chosen_b2 = ch_m
            if tname == "B2_age_matched_val" and pname == "MG_T1_T2_T3_T4":
                matched_chosen_mg = ch_m
    pd.DataFrame(matched_rows).to_csv(out_dir / "matched_dispatch.csv", index=False)

    # Paired two-way cluster bootstrap across TWO schemes for Mean, EpLossRate, and exact ES10 + Holm
    boot_rows = []
    base_df = chosen_test["MG_T1_T2_T3_T4"][["episode_id", "date", "origin_market_key", "State", "Commodity"]].copy()
    for pname, ch in chosen_test.items():
        base_df[pname] = ch["y"].to_numpy(dtype=np.float64)
        base_df[f"{pname}_disp"] = ch["eligible"].to_numpy(dtype=bool)
        base_df[f"{pname}_dest"] = ch["dest_market"].to_numpy()
    base_df["MG_matched"] = matched_chosen_mg["y"].to_numpy(dtype=np.float64)
    base_df["B2_matched"] = matched_chosen_b2["y"].to_numpy(dtype=np.float64)

    # Second cluster key: B2_age_matched chosen destination (or origin when B2 abstains)
    base_df["dest_or_origin_key"] = np.where(base_df["B2_age_matched_disp"], base_df["B2_age_matched_dest"], base_df["origin_market_key"])

    contrasts = [
        ("MG_vs_B1", "MG_T1_T2_T3_T4", "B1_lagged_screen", True),
        ("MG_vs_B2_age_matched", "MG_T1_T2_T3_T4", "B2_age_matched", True),
        ("MG_vs_B_simple_activity", "MG_T1_T2_T3_T4", "B_simple_activity", True),
        ("MG_vs_B2_fresh_val", "MG_T1_T2_T3_T4", "B2_fresh_val", False),
        ("MG_matched_vs_B2_age_matched", "MG_matched", "B2_matched", True),
        ("B2_age_matched_vs_B1", "B2_age_matched", "B1_lagged_screen", False),
    ]
    for cname, ca, cb, in_holm in contrasts:
        for sch_name, mcol in (("origin_x_2week", "origin_market_key"), ("b2dest_or_origin_x_2week", "dest_or_origin_key")):
            res = two_way_cluster_bootstrap_all_metrics(base_df, ca, cb, mandi_col=mcol, reps=2000, seed=20261117)
            for metric, mdict in res.items():
                # Directional primary hypothesis: Mean > 0 ('greater'), EpLossRate < 0 ('less'), ES10 > 0 ('greater')
                p_dir = mdict["p_value_less"] if metric == "ep_loss_rate" else mdict["p_value_greater"]
                boot_rows.append(
                    {
                        "contrast": cname,
                        "cluster": sch_name,
                        "metric": metric,
                        "in_holm_family": in_holm,
                        "estimate": round(mdict["estimate"], 4),
                        "ci95_low": round(mdict["ci95_low"], 4),
                        "ci95_high": round(mdict["ci95_high"], 4),
                        "p_value": p_dir,
                        "p_value_two_sided": mdict["p_value_two_sided"],
                        "n": mdict["n"],
                        "n_clusters": mdict["n_clusters"],
                        "n_blocks": mdict["n_blocks"],
                    }
                )
    boot_df = pd.DataFrame(boot_rows)
    # Apply Holm-Bonferroni within each clustering scheme over the declared primary family
    boot_df["p_holm"] = np.nan
    for sch in ("origin_x_2week", "b2dest_or_origin_x_2week"):
        mask = (boot_df["cluster"] == sch) & (boot_df["in_holm_family"])
        boot_df.loc[mask, "p_holm"] = holm_bonferroni(boot_df.loc[mask, "p_value"].tolist())
    boot_df.to_csv(out_dir / "bootstrap.csv", index=False)

    # Risk-coverage curve WITH 95% CIs at key thresholds for B2_age_matched & MG_T1_T2_T3_T4
    rc_rows = []
    for fam, skey, gfn in (
        ("MG_T1_T2_T3_T4", "net_road_fee_spoil", lambda f: (f["age"] >= 1) & (f["age"] <= 3) & (f["rep14"] >= 0.50) & (f["dow8"] >= 0.35)),
        ("B2_age_matched", "net_road_fee", lambda f: (f["age"] >= 1) & (f["age"] <= 3)),
    ):
        g_test = gfn(test_f)
        for kn in range(0, 701, 50):
            ch = pick_episode(test, test_f[skey], g_test & (test_f[skey] > float(kn)))
            rec = summarize_chosen(fam, ch)
            cis = ci95_single_metric(ch, "y", reps=500, seed=20261117 + kn)
            rec["knob"] = kn
            rec["family"] = fam
            rec["mean_ci95_low"] = round(cis["mean"][0], 2)
            rec["mean_ci95_high"] = round(cis["mean"][1], 2)
            rec["ep_loss_ci95_low"] = round(cis["ep_loss_rate"][0], 4)
            rec["ep_loss_ci95_high"] = round(cis["ep_loss_rate"][1], 4)
            rec["es10_ci95_low"] = round(cis["es10"][0], 2)
            rec["es10_ci95_high"] = round(cis["es10"][1], 2)
            rc_rows.append(rec)
    pd.DataFrame(rc_rows).to_csv(out_dir / "risk_coverage.csv", index=False)

    # Crop & State splits with paired bootstrap CIs (MG_T1_T2_T3_T4 vs B2_age_matched)
    by_rows = []
    for stype in ("Commodity", "State"):
        for sval, grp in base_df.groupby(stype, sort=True):
            res = two_way_cluster_bootstrap_all_metrics(grp, "MG_T1_T2_T3_T4", "B2_age_matched", reps=1000, seed=20261117)
            by_rows.append(
                {
                    "slice_type": stype,
                    "slice": str(sval),
                    "n": int(len(grp)),
                    "mg_disp_rate": round(float(grp["MG_T1_T2_T3_T4_disp"].mean()), 4),
                    "b2_disp_rate": round(float(grp["B2_age_matched_disp"].mean()), 4),
                    "mg_mean": round(float(grp["MG_T1_T2_T3_T4"].mean()), 2),
                    "b2_mean": round(float(grp["B2_age_matched"].mean()), 2),
                    "b1_mean": round(float(grp["B1_lagged_screen"].mean()), 2),
                    "mg_minus_b2_mean": round(res["mean"]["estimate"], 2),
                    "mean_diff_ci95_low": round(res["mean"]["ci95_low"], 2),
                    "mean_diff_ci95_high": round(res["mean"]["ci95_high"], 2),
                    "mg_es10": round(es10(grp["MG_T1_T2_T3_T4"].to_numpy()), 2),
                    "b2_es10": round(es10(grp["B2_age_matched"].to_numpy()), 2),
                    "es10_diff_ci95_low": round(res["es10"]["ci95_low"], 2),
                    "es10_diff_ci95_high": round(res["es10"]["ci95_high"], 2),
                    "mg_ep_loss_rate": round(float((grp["MG_T1_T2_T3_T4"] < 0).mean()), 4),
                    "b2_ep_loss_rate": round(float((grp["B2_age_matched"] < 0).mean()), 4),
                }
            )
    pd.DataFrame(by_rows).to_csv(out_dir / "by_crop_state.csv", index=False)

    # Settlement & outside-option comparisons
    y_hind = settle_candidates(test, how="hindsight", weather="none", div=1.5, disc=0.10)
    y_lag_out = settle_candidates(test, how="sequential", weather="none", div=1.5, disc=0.10, outside_option="lag")
    y_clim_out = settle_candidates(test, how="sequential", weather="clim2024", div=1.5, disc=0.10)
    sc_rows = []
    for pname in ("B1_lagged_screen", "B2_fresh_val", "B2_age_matched", "B_simple_activity", "MG_T1_T2_T3_T4"):
        ch = chosen_test[pname]
        idx = ch["_i"].to_numpy()
        for s_label, y_arr in (
            ("sequential_20C_d0_outside", ch["y_raw"].to_numpy(dtype=np.float64)),
            ("hindsight_20C_d0_outside", y_hind[idx]),
            ("sequential_20C_lag_outside", y_lag_out[idx]),
            ("sequential_clim2024_d0_outside", y_clim_out[idx]),
        ):
            r = summarize_chosen(pname, ch, y_override=y_arr)
            r["settlement_mode"] = s_label
            sc_rows.append(r)
    pd.DataFrame(sc_rows).to_csv(out_dir / "settlement_compare.csv", index=False)

    # Lagged HP Grade-Explicit Apple benchmark (zero HP re-tuning -> frozen 6-state thresholds!)
    hp_df = pd.read_parquet(out_dir / "lagged_hp_apple_candidates.parquet")
    hp_df["date"] = pd.to_datetime(hp_df["date"])
    hp_df["y"] = settle_candidates(hp_df, how="sequential", weather="none", div=1.5, disc=0.10)
    hp_rows = []
    for w_label, sub_hp in (("ALL_2025_2026", hp_df), ("POST_JUNE_2026", hp_df[hp_df["date"] >= pd.Timestamp("2026-06-01")].reset_index(drop=True))):
        hf = compute_decision_features(sub_hp)
        for pname, _, skey, gfn, _ in policy_specs:
            if pname not in ("B1_lagged_screen", "B2_fresh_val", "B2_age_matched", "B_simple_activity", "MG_T1_T2_T3_T4"):
                continue
            th = tuned_thresholds[pname]
            ch_hp = pick_episode(sub_hp, hf[skey], gfn(hf) & (hf[skey] > th))
            rec = summarize_chosen(pname, ch_hp)
            rec["window"] = w_label
            rec["threshold_used"] = th
            hp_rows.append(rec)
    pd.DataFrame(hp_rows).to_csv(out_dir / "hp_apple_lagged.csv", index=False)

    summary = {
        "val_window": "2025-01-01..2025-05-31",
        "test_window": "2025-06-01..2026-04-08",
        "val_n_episodes": int(val["episode_id"].nunique()),
        "test_n_episodes": int(test["episode_id"].nunique()),
        "hp_apple_lagged_n_episodes": int(hp_df["episode_id"].nunique()),
        "tuned_thresholds_on_val": tuned_thresholds,
        "val_summaries": val_summaries,
        "weather_primary": "none_20C_reference",
        "settlement_primary": "sequential",
        "fee_base": "destination_post_spoilage_gross_sale_zero_on_divert_or_same_district",
        "div_primary": 1.5,
        "disc_primary": 0.10,
        "exploratory": True,
        "note": "Thresholds frozen on Jan-May 2025. Jun 2025-Apr 2026 was previously exposed in repo history, so test evaluation is explicitly exploratory (R5). Zero dependence on gitignored candidates_6state.parquet.",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print("=== MAIN TABLE (test N =", summary["test_n_episodes"], ") ===")
    print(main_df[["policy", "dispatch_rate", "mean", "ep_loss_rate", "cond_loss_rate", "es10", "val_threshold"]].to_string(index=False))
    print("\n=== MATCHED DISPATCH (target val B2 =", round(target_b2_val_disp, 4), ") ===")
    m_sub = pd.DataFrame(matched_rows)
    print(m_sub[m_sub["match_target"] == "B2_age_matched_val"][["policy", "dispatch_rate", "mean", "ep_loss_rate", "cond_loss_rate", "es10", "calibrated_threshold"]].to_string(index=False))
    print("\n=== BOOTSTRAP HOLM (origin_x_2week) ===")
    print(boot_df[boot_df["cluster"] == "origin_x_2week"][["contrast", "metric", "estimate", "ci95_low", "ci95_high", "p_value", "p_holm"]].to_string(index=False))
    print("\n=== BY CROP (MG vs B2_age_matched) ===")
    print(pd.DataFrame(by_rows)[["slice_type", "slice", "n", "mg_mean", "b2_mean", "mg_minus_b2_mean", "mg_es10", "b2_es10"]].to_string(index=False))
    print("\n=== HP APPLE LAGGED (ALL) ===")
    print(pd.DataFrame(hp_rows)[pd.DataFrame(hp_rows)["window"] == "ALL_2025_2026"][["policy", "n", "dispatch_rate", "mean", "ep_loss_rate", "es10"]].to_string(index=False))


if __name__ == "__main__":
    run()
