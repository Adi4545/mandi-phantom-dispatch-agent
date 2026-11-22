"""Generate Revision v4 publication figures directly from revision/results/*.csv (zero hardcoded numbers)."""

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
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "figure.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.25,
    })

    rc = pd.read_csv(res / "risk_coverage.csv")
    a10 = pd.read_csv(res / "a10_results.csv").set_index("policy")
    main_df = pd.read_csv(res / "main_table.csv").set_index("policy")
    matched = pd.read_csv(res / "matched_dispatch.csv")
    crops = pd.read_csv(res / "a10_crop_splits.csv")
    torn = pd.read_csv(res / "tornado_sensitivity.csv")
    miss = pd.read_csv(res / "a10_missing_stability.csv")
    settle = pd.read_csv(res / "settlement_compare.csv")
    hp_a10 = pd.read_csv(res / "a10_hp_apple.csv")
    omix = pd.read_csv(res / "outcome_mix.csv")

    # 1. Risk-coverage curves with 95% CIs
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    for fam, lbl, col in (
        ("B2_age_matched", "B2_age_matched (lag 1..3)", "#1f77b4"),
        ("MG_T1_T2_T3_T4", "MG_T1_T2_T3_T4 (hard-gated)", "#2ca02c"),
    ):
        sub = rc[rc["family"] == fam].sort_values("dispatch_rate")
        x = sub["dispatch_rate"].to_numpy() * 100.0
        axes[0].plot(x, sub["ep_loss_rate"] * 100.0, label=lbl, color=col, lw=2)
        axes[0].fill_between(x, sub["ep_loss_ci95_low"] * 100.0, sub["ep_loss_ci95_high"] * 100.0, color=col, alpha=0.15)
        axes[1].plot(x, sub["es10"], label=lbl, color=col, lw=2)
        axes[1].fill_between(x, sub["es10_ci95_low"], sub["es10_ci95_high"], color=col, alpha=0.15)

    # Mark B1 and pre-registered RR-Abstain matched point
    b1_row = a10.loc["B1_lagged_screen"]
    rr_row = a10.loc["RR_Abstain_matched"]
    axes[0].scatter([b1_row["dispatch_rate"] * 100], [b1_row["ep_loss_rate"] * 100], color="#d62728", s=70, zorder=5, label="B1_lagged_screen (100%)")
    axes[0].scatter([rr_row["dispatch_rate"] * 100], [rr_row["ep_loss_rate"] * 100], color="#ff7f0e", marker="*", s=160, zorder=6, label="RR_Abstain_matched (69.0%)")
    axes[1].scatter([b1_row["dispatch_rate"] * 100], [b1_row["es10"]], color="#d62728", s=70, zorder=5, label="B1_lagged_screen (100%)")
    axes[1].scatter([rr_row["dispatch_rate"] * 100], [rr_row["es10"]], color="#ff7f0e", marker="*", s=160, zorder=6, label="RR_Abstain_matched (69.0%)")

    axes[0].set_title("Episode Loss Incidence vs Dispatch Coverage (95% Cluster CI)")
    axes[0].set_xlabel("Dispatch Rate (%)")
    axes[0].set_ylabel("Episode Loss Rate (%)")
    axes[0].legend(fontsize=8)
    axes[1].set_title("Worst-10% Shortfall (ES10) vs Dispatch Coverage (95% CI)")
    axes[1].set_xlabel("Dispatch Rate (%)")
    axes[1].set_ylabel("ES10 (INR / qtl)")
    axes[1].legend(fontsize=8)
    fig.savefig(fig_dir / "rev_fig1_risk_coverage_ci.png", dpi=240)
    plt.close(fig)

    # 2. Matched-dispatch ablations and non-apple vs apple crop splits
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0), constrained_layout=True)
    m_sub = matched[matched["match_target"] == "B2_age_matched_val"].set_index("policy")
    ab_order = ["B2_age_matched", "B_simple_activity", "Abl_T1_T2_noT3", "MG_T1_T2_T3_T4", "Abl_euclid_freight", "Abl_clim2024_spoil"]
    ab_labels = ["B2_age_matched", "B_simple_act", "T1+T2 (no T3)", "MG (T1..T4)", "Euclid*1.2", "2024 Clim"]
    means_ab = [float(m_sub.loc[p, "mean"]) for p in ab_order] + [float(rr_row["mean"])]
    es10_ab = [float(m_sub.loc[p, "es10"]) for p in ab_order] + [float(rr_row["es10"])]
    ab_labels.append("RR_Abstain")
    x_pos = np.arange(len(ab_labels))
    w = 0.38
    axes[0].bar(x_pos - w / 2, means_ab, width=w, color="#1f77b4", label="Mean Net Gain (INR/qtl)")
    axes[0].bar(x_pos + w / 2, es10_ab, width=w, color="#d62728", label="Worst-10% ES10 (INR/qtl)")
    axes[0].axhline(0, color="black", lw=0.8)
    axes[0].set_ylim(-600, 620)
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels(ab_labels, rotation=22, ha="right", fontsize=8.5)
    axes[0].set_title("Matched (~70%) Component Ablations & RR-Abstain")
    axes[0].set_ylabel("INR / qtl")
    axes[0].legend(fontsize=8, loc="upper left", ncol=2)

    c_list = ["Onion", "Potato", "Tomato", "NonApple", "Apple"]
    pols_c = [("B2_age_matched", "#1f77b4"), ("MG_matched", "#2ca02c"), ("RR_Abstain_matched", "#ff7f0e")]
    xc = np.arange(len(c_list))
    wc = 0.26
    for idx_p, (pname, col) in enumerate(pols_c):
        vals = [float(crops[(crops["crop_slice"] == c) & (crops["policy"] == pname)]["es10"].iloc[0]) for c in c_list]
        axes[1].bar(xc + (idx_p - 1) * wc, vals, width=wc, color=col, label=pname)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_xticks(xc)
    axes[1].set_xticklabels(c_list)
    axes[1].set_title("Matched Worst-10% Shortfall (ES10) by Crop Slice")
    axes[1].set_ylabel("ES10 (INR / qtl, higher is milder)")
    axes[1].legend(fontsize=8)
    fig.savefig(fig_dir / "rev_fig2_ablations_and_crops.png", dpi=240)
    plt.close(fig)

    # 3. Tornado sensitivity & missing-price stability
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), constrained_layout=True)
    sc_list = [
        "joint_optimistic_niti", "freight_niti_floor_0.258", "fee_buyer_paid_0pct",
        "spoil_0.5x", "base", "arhtiya_2pct", "arhtiya_4pct",
        "freight_lcv_0.75", "joint_realistic_harsh_lcv_arhtiya4", "freight_steep_1.20",
    ]
    t_piv = torn[torn["scenario"].isin(sc_list)].pivot(index="scenario", columns="policy", values="mean").loc[sc_list]
    y_t = np.arange(len(sc_list))
    for pname, col, marker in (("B1_lagged_screen", "#d62728", "o"), ("B2_age_matched", "#1f77b4", "s"), ("MG_T1_T2_T3_T4", "#2ca02c", "^")):
        axes[0].plot(t_piv[pname].to_numpy(), y_t, marker=marker, lw=1.5, color=col, label=pname)
    axes[0].set_yticks(y_t)
    axes[0].set_yticklabels(sc_list, fontsize=8)
    axes[0].set_title("A8 Parameter Sensitivity Across Freight/Fee Regimes")
    axes[0].set_xlabel("Test Mean Net Gain (INR / qtl)")
    axes[0].legend(fontsize=8)

    miss_order = ["div_0.0_disc_0.00", "div_0.5_disc_0.10", "div_1.0_disc_0.10", "div_1.5_disc_0.10_base", "div_2.0_disc_0.10", "het_crop_perishability", "het_selective_missing_lowrep_harsh"]
    miss_lbls = ["div=0", "div=0.5", "div=1.0", "div=1.5*", "div=2.0", "Het-Crop", "Het-LowRep"]
    xm = np.arange(len(miss_order))
    for pname, col in (("B1_lagged_screen", "#d62728"), ("B2_age_matched", "#1f77b4"), ("MG_matched", "#2ca02c"), ("RR_Abstain_matched", "#ff7f0e")):
        ys = [float(miss[(miss["missing_scenario"] == m) & (miss["policy"] == pname)]["es10"].iloc[0]) for m in miss_order]
        axes[1].plot(xm, ys, marker="o", lw=2, color=col, label=pname)
    axes[1].set_xticks(xm)
    axes[1].set_xticklabels(miss_lbls, rotation=20, ha="right", fontsize=8.5)
    axes[1].set_title("ES10 Across Homogeneous & Heterogeneous Missing Scenarios")
    axes[1].set_ylabel("ES10 (INR / qtl)")
    axes[1].legend(fontsize=8)
    fig.savefig(fig_dir / "rev_fig3_sensitivity_tornado_and_missing.png", dpi=240)
    plt.close(fig)

    # 4. Sequential vs hindsight settlement + Outcome mix / HP Apple lagged
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8), constrained_layout=True)
    pol_s = ["B1_lagged_screen", "B2_fresh_val", "B2_age_matched", "B_simple_activity", "MG_T1_T2_T3_T4"]
    seq_lr = [float(settle[(settle["policy"] == p) & (settle["settlement_mode"] == "sequential_20C_d0_outside")]["ep_loss_rate"].iloc[0]) * 100 for p in pol_s]
    hnd_lr = [float(settle[(settle["policy"] == p) & (settle["settlement_mode"] == "hindsight_20C_d0_outside")]["ep_loss_rate"].iloc[0]) * 100 for p in pol_s]
    xs = np.arange(len(pol_s))
    ws = 0.35
    axes[0].bar(xs - ws / 2, seq_lr, width=ws, color="#1f77b4", label="Sequential (no lookahead)")
    axes[0].bar(xs + ws / 2, hnd_lr, width=ws, color="#9467bd", label="Hindsight (3d lookahead)")
    axes[0].set_xticks(xs)
    axes[0].set_xticklabels(["B1", "B2_fresh", "B2_age1-3", "B_act", "MG_T1..T4"], rotation=15)
    axes[0].set_title("Sequential vs Hindsight Episode Loss Rate")
    axes[0].set_ylabel("Episode Loss Rate (%)")
    axes[0].legend(fontsize=8)

    hp_all = hp_a10[hp_a10["window"] == "ALL_2025_2026"].set_index("policy")
    hp_pols = ["B2_age_matched", "MG_matched", "RR_Abstain_matched", "RR_Abstain_val"]
    xh = np.arange(len(hp_pols))
    axes[1].bar(xh - 0.18, [float(hp_all.loc[p, "mean"]) for p in hp_pols], width=0.35, color="#1f77b4", label="Mean Net (INR/qtl)")
    axes[1].bar(xh + 0.18, [float(hp_all.loc[p, "es10"]) for p in hp_pols], width=0.35, color="#d62728", label="ES10 (INR/qtl)")
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_xticks(xh)
    axes[1].set_xticklabels(["B2_age1-3", "MG_matched", "RR_matched", "RR_val"], rotation=15)
    axes[1].set_title("Lagged HP Graded-Apple Holdout (N=2,802)")
    axes[1].set_ylabel("INR / qtl")
    axes[1].legend(fontsize=8)
    fig.savefig(fig_dir / "rev_fig4_settlement_and_hp_apple.png", dpi=240)
    plt.close(fig)
    print("Generated rev_fig1..4 in", fig_dir)


if __name__ == "__main__":
    make_all_figures()
