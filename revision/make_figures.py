"""Generate Revision v5 publication figures directly from revision/results/*.csv (zero hardcoded numbers)."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def make_all_figures(root: Path = ROOT) -> None:
    res = root / "revision" / "results"
    fig_dir = root / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9.5,
        "figure.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.25,
    })

    rc18 = pd.read_csv(res / "a18_risk_coverage.csv")
    a18 = pd.read_csv(res / "a18_results.csv").set_index("policy")
    fair_ab = pd.read_csv(res / "a18_fair_ablations.csv").set_index("policy")
    crops = pd.read_csv(res / "a18_crop_and_state_splits.csv")
    torn = pd.read_csv(res / "a18_tornado.csv")
    miss = pd.read_csv(res / "a18_missing_regimes.csv")
    sr = pd.read_csv(res / "a18_settlement_and_robustness.csv")
    hp18 = pd.read_csv(res / "a18_hp_apple.csv")

    # 1. Risk-coverage curves with 95% CIs (including B2, MG, RR_Abstain, Safe_EV_Sunk)
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0), constrained_layout=True)
    for fam, lbl, col in (
        ("B2_age_matched", "B2_age_matched (lag 1..3)", "#1f77b4"),
        ("MG_T1_T2_T3_T4", "MG (hard T1..T4)", "#2ca02c"),
        ("RR_Abstain", "RR_Abstain (k=5)", "#ff7f0e"),
        ("Safe_EV_Sunk", "Safe_EV_Sunk (0 params)", "#9467bd"),
    ):
        sub = rc18[rc18["family"] == fam].sort_values("dispatch_rate")
        x = sub["dispatch_rate"].to_numpy() * 100.0
        axes[0].plot(x, sub["ep_loss_rate"] * 100.0, label=lbl, color=col, lw=2)
        axes[0].fill_between(x, sub["ep_loss_ci95_low"] * 100.0, sub["ep_loss_ci95_high"] * 100.0, color=col, alpha=0.12)
        axes[1].plot(x, sub["es10"], label=lbl, color=col, lw=2)
        axes[1].fill_between(x, sub["es10_ci95_low"], sub["es10_ci95_high"], color=col, alpha=0.12)

    for pname, mkr, col, sz, lbl in (
        ("B1_lagged_screen", "o", "#d62728", 65, "B1_lagged_screen (100%)"),
        ("RT_2F_Min_m0", "D", "#8c564b", 65, "RT_2F_Min_m0 (S>0, 0p)"),
        ("Safe_EV_Sunk_m0", "*", "#111111", 160, "Safe_EV_Sunk_m0 (S>0, 0p)"),
    ):
        row = a18.loc[pname]
        axes[0].scatter([row["dispatch_rate"] * 100], [row["ep_loss_rate"] * 100], color=col, marker=mkr, s=sz, zorder=6, label=lbl)
        axes[1].scatter([row["dispatch_rate"] * 100], [row["es10"]], color=col, marker=mkr, s=sz, zorder=6, label=lbl)

    axes[0].set_title("Episode Loss Incidence vs Dispatch Coverage (95% CI)")
    axes[0].set_xlabel("Dispatch Rate (%)")
    axes[0].set_ylabel("Episode Loss Rate (%)")
    axes[0].legend(fontsize=7.5, loc="upper left")
    axes[1].set_title("Worst-10% Shortfall (ES10) vs Dispatch Coverage (95% CI)")
    axes[1].set_xlabel("Dispatch Rate (%)")
    axes[1].set_ylabel("ES10 (INR / qtl)")
    axes[1].legend(fontsize=7.5, loc="lower left")
    fig.savefig(fig_dir / "rev_fig1_risk_coverage_ci.png", dpi=240)
    plt.close(fig)

    # 2. Fair feature/tuning ablations & ES10 across crop slices
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), constrained_layout=True)
    ab_specs = [
        ("B2_age_matched", a18, "B2_age_matched"),
        ("B2_dist_penalty_3F_matched", fair_ab, "B2 - 3F (dist only)"),
        ("MG_matched", a18, "MG_matched"),
        ("MG_val_es10_tuned_matched", fair_ab, "MG (val-ES10 tuned)"),
        ("RR_rep14_only_matched", fair_ab, "RR (rep14 only)"),
        ("RR_Abstain_matched", a18, "RR_Abstain (k*=5)"),
        ("Safe_EV_fixed10pct_m0", fair_ab, "Safe-EV (fix 10%)"),
        ("RT_2F_Min_m0", a18, "RT_2F_Min (0p)"),
        ("Safe_EV_Sunk_m0", a18, "Safe_EV_Sunk (0p)"),
    ]
    ab_labels = [s[2] for s in ab_specs]
    means_ab = [float(s[1].loc[s[0], "mean"]) for s in ab_specs]
    es10_ab = [float(s[1].loc[s[0], "es10"]) for s in ab_specs]
    x_pos = np.arange(len(ab_labels))
    w = 0.38
    axes[0].bar(x_pos - w / 2, means_ab, width=w, color="#1f77b4", label="Mean Net Gain (INR/qtl)")
    axes[0].bar(x_pos + w / 2, es10_ab, width=w, color="#d62728", label="Worst-10% ES10 (INR/qtl)")
    axes[0].axhline(0, color="black", lw=0.8)
    axes[0].set_ylim(-600, 620)
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(ab_labels, rotation=28, ha="right", fontsize=8)
    axes[0].set_title("Fair Ablations vs Zero-Param Safe_EV_Sunk & RT_2F_Min")
    axes[0].set_ylabel("INR / qtl")
    axes[0].legend(fontsize=8, loc="upper left", ncol=2)

    c_list = ["Onion", "Potato", "Tomato", "NonApple", "Apple"]
    pols_c = [
        ("B2_age_matched", "#1f77b4", "B2_age_matched"),
        ("MG_matched", "#2ca02c", "MG_matched"),
        ("RR_Abstain_matched", "#ff7f0e", "RR_Abstain_matched"),
        ("Safe_EV_Sunk_m0", "#9467bd", "Safe_EV_Sunk_m0 (0p)"),
    ]
    xc = np.arange(len(c_list))
    wc = 0.20
    for idx_p, (pname, col, lbl) in enumerate(pols_c):
        vals = [float(crops[(crops["slice_type"] == "Commodity") & (crops["slice"] == c) & (crops["policy"] == pname)]["es10"].iloc[0]) for c in c_list]
        axes[1].bar(xc + (idx_p - 1.5) * wc, vals, width=wc, color=col, label=lbl)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_xticks(xc)
    axes[1].set_xticklabels(c_list)
    axes[1].set_title("Worst-10% Shortfall (ES10) by Crop Slice")
    axes[1].set_ylabel("ES10 (INR / qtl, higher is milder)")
    axes[1].legend(fontsize=8, loc="lower left")
    fig.savefig(fig_dir / "rev_fig2_ablations_and_crops.png", dpi=240)
    plt.close(fig)

    # 3. Re-scored Tornado Sensitivity & Complete Missing-Quote Regimes
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.4), constrained_layout=True)
    sc_list = [
        "joint_optimistic_niti", "freight_niti_floor_0.258", "fee_buyer_paid_0pct",
        "spoil_0.5x", "base", "arhtiya_2pct", "arhtiya_4pct",
        "freight_lcv_0.75", "joint_realistic_harsh_lcv_arhtiya4", "freight_steep_1.20",
    ]
    t_sub = torn[torn["decision_mode"] == "rescored"]
    t_piv = t_sub[t_sub["scenario"].isin(sc_list)].pivot(index="scenario", columns="policy", values="mean").loc[sc_list]
    y_t = np.arange(len(sc_list))
    for pname, col, marker in (
        ("B1_lagged_screen", "#d62728", "o"),
        ("B2_age_matched", "#1f77b4", "s"),
        ("MG_matched", "#2ca02c", "^"),
        ("RR_Abstain_matched", "#ff7f0e", "v"),
        ("RT_2F_Min_m0", "#8c564b", "D"),
        ("Safe_EV_Sunk_m0", "#9467bd", "*"),
    ):
        axes[0].plot(t_piv[pname].to_numpy(), y_t, marker=marker, lw=1.5, color=col, label=pname)
    axes[0].set_yticks(y_t)
    axes[0].set_yticklabels(sc_list, fontsize=7.5)
    axes[0].set_xlim(180, 565)
    axes[0].set_title("Re-Scored Sensitivity Across Freight & Fee Regimes")
    axes[0].set_xlabel("Test Mean Net Gain (INR / qtl)")
    axes[0].legend(fontsize=7.5, loc="lower left")

    miss_order = [
        "open_yard_MAR_lagged_price", "exact_zero_divert_payoff_0", "div_0.0_spoil_only",
        "div_0.5_disc_0.10", "div_1.0_disc_0.10", "div_1.5_disc_0.10_base", "div_2.0_disc_0.10",
        "het_selective_missing_lowrep_harsh", "het_adversarial_lowrep_ok_highrep_harsh",
    ]
    miss_lbls = ["Open MAR", "Exact 0 div", "div=0(sp)", "div=0.5", "div=1.0", "div=1.5*", "div=2.0", "Het-LowRep", "Het-Adv"]
    xm = np.arange(len(miss_order))
    for pname, col in (
        ("B1_lagged_screen", "#d62728"),
        ("B2_age_matched", "#1f77b4"),
        ("MG_matched", "#2ca02c"),
        ("RR_Abstain_matched", "#ff7f0e"),
        ("RT_2F_Min_m0", "#8c564b"),
        ("Safe_EV_Sunk_m0", "#9467bd"),
    ):
        ys = [float(miss[(miss["missing_scenario"] == m) & (miss["policy"] == pname)]["es10"].iloc[0]) for m in miss_order]
        axes[1].plot(xm, ys, marker="o", lw=1.8, color=col, label=pname)
    axes[1].set_xticks(xm)
    axes[1].set_xticklabels(miss_lbls, rotation=24, ha="right", fontsize=8)
    axes[1].set_title("ES10 Across Full Missing-Quote & Open-MAR Bounds")
    axes[1].set_ylabel("ES10 (INR / qtl)")
    axes[1].legend(fontsize=7.5, loc="lower left")
    fig.savefig(fig_dir / "rev_fig3_sensitivity_tornado_and_missing.png", dpi=240)
    plt.close(fig)

    # 4. Structural robustness slices (Sequential, Hindsight, Exact-Geo, Unconditional Origin) + HP Apples
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.0), constrained_layout=True)
    sl_list = [
        ("sequential_base", "Sequential (N=58.7k)"),
        ("hindsight_3d", "3d Hindsight"),
        ("exact_geocode_corridors_only", "Exact Geocode"),
        ("unconditional_orig_panel_d0_or_lag", "Uncond. Orig (N=88.0k)"),
    ]
    pols_sr = [("B2_age_matched", "#1f77b4"), ("MG_matched", "#2ca02c"), ("RR_Abstain_matched", "#ff7f0e"), ("Safe_EV_Sunk_m0", "#9467bd")]
    xs = np.arange(len(sl_list))
    ws = 0.20
    for idx_p, (pname, col) in enumerate(pols_sr):
        es_vals = [float(sr[(sr["robustness_slice"] == sk) & (sr["policy"] == pname)]["es10"].iloc[0]) for sk, _ in sl_list]
        axes[0].bar(xs + (idx_p - 1.5) * ws, es_vals, width=ws, color=col, label=pname)
    axes[0].axhline(0, color="black", lw=0.8)
    axes[0].set_ylim(-640, 120)
    axes[0].set_xticks(xs)
    axes[0].set_xticklabels([l for _, l in sl_list], rotation=18, ha="right", fontsize=8.5)
    axes[0].set_title("ES10 Across Settlement & Structural Robustness Checks")
    axes[0].set_ylabel("ES10 (INR / qtl)")
    axes[0].legend(fontsize=7.5, loc="upper center", ncol=2)

    hp_all = hp18[hp18["window"] == "ALL_2025_2026"].set_index("policy")
    hp_pols = ["B2_age_matched", "MG_matched", "RR_Abstain_matched", "RT_2F_Min_m0", "Safe_EV_Sunk_m0"]
    xh = np.arange(len(hp_pols))
    axes[1].bar(xh - 0.18, [float(hp_all.loc[p, "mean"]) for p in hp_pols], width=0.35, color="#1f77b4", label="Mean Net (INR/qtl)")
    axes[1].bar(xh + 0.18, [float(hp_all.loc[p, "es10"]) for p in hp_pols], width=0.35, color="#d62728", label="ES10 (INR/qtl)")
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_ylim(-2600, 1850)
    axes[1].set_xticks(xh)
    axes[1].set_xticklabels(["B2_age", "MG_matched", "RR_matched", "RT_2F_Min(0p)", "Safe_EV_Sunk(0p)"], rotation=18, ha="right", fontsize=8)
    axes[1].set_title("Lagged HP Graded-Apple Holdout (N=2,802)")
    axes[1].set_ylabel("INR / qtl")
    axes[1].legend(fontsize=8, loc="upper left", ncol=2)
    fig.savefig(fig_dir / "rev_fig4_settlement_and_hp_apple.png", dpi=240)
    plt.close(fig)
    print("Generated rev_fig1..4 in", fig_dir.relative_to(root))


if __name__ == "__main__":
    make_all_figures()
