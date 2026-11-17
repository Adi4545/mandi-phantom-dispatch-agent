"""Publication-quality 300-DPI figures for the MandiGuard M.Tech thesis & manuscript."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 11.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
    }
)


def make_fig1_phantom_anatomy(res_dir: Path, fig_dir: Path) -> None:
    df = pd.read_csv(res_dir / "exp1_phantom_anatomy.csv")
    comm = df[df["slice_type"] == "Commodity"].set_index("slice_value").loc[["Tomato", "Apple", "Onion", "Potato"]]
    states = df[df["slice_type"] == "State"].sort_values("phantom_loss_rate_pct", ascending=True)

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8))

    # Panel A: Screen spread erosion waterfall-style grouped bars by crop
    x = np.arange(len(comm))
    w = 0.19
    axes[0].bar(x - 1.5 * w, comm["mean_screen_spread_inr"], width=w, label="Headline Screen Spread", color="#4C72B0")
    axes[0].bar(x - 0.5 * w, comm["mean_freight_inr"], width=w, label="Road Freight & APMC Fee", color="#DD8452")
    axes[0].bar(x + 0.5 * w, comm["mean_spoilage_inr"], width=w, label="Weather/Transit Spoilage", color="#C44E52")
    axes[0].bar(x + 1.5 * w, comm["mean_realized_dnet_inr"], width=w, label="Realized Net Gain (DeltaNet)", color="#55A868")
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(comm.index)
    axes[0].set_ylabel("Rupees per Quintal (INR/qtl)")
    axes[0].set_title("(A) Spread Erosion Under Naive Screen Chasing (B1)")
    axes[0].legend(frameon=False, fontsize=8.5, loc="upper right")

    # Panel B: Trap & Phantom Loss rates across States
    y = np.arange(len(states))
    h = 0.36
    axes[1].barh(y + h / 2, states["closed_or_variety_trap_pct"], height=h, label="Closed / No-Variety Trap (%)", color="#8172B3")
    axes[1].barh(y - h / 2, states["phantom_loss_rate_pct"], height=h, label="Net Loss Dispatch Rate (%)", color="#C44E52")
    axes[1].set_yticks(y)
    axes[1].set_yticklabels(states["slice_value"])
    axes[1].set_xlim(0, 72)
    axes[1].set_xlabel("Percentage of Naive Screen Dispatches (%)")
    axes[1].set_title("(B) Physical Trap & Phantom Loss Rates Across States", pad=22)
    axes[1].legend(frameon=False, fontsize=8.5, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    for idx, (_, row) in enumerate(states.iterrows()):
        axes[1].text(row["closed_or_variety_trap_pct"] + 0.8, idx + h / 2, f"{row['closed_or_variety_trap_pct']:.1f}%", va="center", fontsize=8)
        axes[1].text(row["phantom_loss_rate_pct"] + 0.8, idx - h / 2, f"{row['phantom_loss_rate_pct']:.1f}%", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(fig_dir / "fig1_phantom_arbitrage_anatomy.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_fig2_main_policy_comparison(res_dir: Path, fig_dir: Path) -> None:
    df = pd.read_csv(res_dir / "exp2_main_benchmark_6state.csv")
    df = df[df["policy"] != "B0_SellLocal"].copy()
    order = [
        "B1_NaiveScreenGreedy",
        "B2_FreshRoadGreedy",
        "B3_MLPointDispatch",
        "B6_HeuristicBucketRouter",
        "B5_MultiAgentCoordinator",
        "B4_UpfrontAllTools",
        "MandiGuard",
    ]
    labels = [
        "B1: Naive\nScreen",
        "B2: Fresh +\nOSRM",
        "B3: ML\nPoint",
        "B6: Verbal\nRules",
        "B5: 3-Agent\nQuantized",
        "B4: Upfront\nAll-Tools",
        "MandiGuard\n(Ours)",
    ]
    sub = df.set_index("policy").loc[order]
    colors = ["#8C8C8C", "#A6BDD7", "#74A9CF", "#FEB24C", "#FD8D3C", "#2B8CBE", "#1B7837"]

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.8))
    x = np.arange(len(order))

    bars = axes[0].bar(x, sub["mean_delta_net_inr"], color=colors, edgecolor="#222222", linewidth=0.5)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, fontsize=8.5)
    axes[0].set_ylabel("Mean Net Gain over Local Sale (INR/qtl)")
    axes[0].set_title("(A) Holdout Economic Gain Across Shortlisted Episodes")
    for b in bars:
        axes[0].text(b.get_x() + b.get_width() / 2, b.get_height() + 5, f"Rs {b.get_height():.0f}", ha="center", va="bottom", fontsize=8)

    w = 0.36
    axes[1].bar(x - w / 2, sub["cond_phantom_loss_rate_pct"], width=w, label="Dispatched Phantom Loss (%)", color="#C44E52")
    axes[1].bar(x + w / 2, sub["cond_closed_or_trap_rate_pct"], width=w, label="Closed / No-Variety Trap (%)", color="#8172B3")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, fontsize=8.5)
    axes[1].set_ylabel("Risk Rate Among Dispatched Trucks (%)")
    axes[1].set_title("(B) Phantom Loss & Closed-Yard Trap Rates (Lower = Better)")
    axes[1].legend(frameon=False, fontsize=8.5, loc="upper right")

    fig.tight_layout()
    fig.savefig(fig_dir / "fig2_main_policy_comparison.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_fig3_ablation_and_weather(res_dir: Path, fig_dir: Path) -> None:
    df = pd.read_csv(res_dir / "exp4_tool_ablations.csv")
    order = ["Full_MandiGuard", "No_T1_Vitality", "No_T2_OSRM_to_Euclid", "No_T3_Weather", "No_T4_ConformalLCB"]
    labels = ["Full\nMandiGuard", "w/o T1\n(Vitality)", "w/o T2\n(Euclid)", "w/o T3\n(Weather)", "w/o T4\n(Conformal)"]

    all_r = df[df["regime"] == "All_Holdout"].set_index("policy").loc[order]
    ext_r = df[df["regime"] == "Extreme_Heat_or_Rain"].set_index("policy").loc[order]

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.7))
    x = np.arange(len(order))
    w = 0.35

    axes[0].bar(x - w / 2, all_r["mean_delta_net_inr"], width=w, label="All Holdout", color="#2B8CBE")
    axes[0].bar(x + w / 2, ext_r["mean_delta_net_inr"], width=w, label="Extreme Heat (>=35C) or Rain (>=35mm)", color="#D95F0E")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, fontsize=8.5)
    axes[0].set_ylim(0, 560)
    axes[0].set_ylabel("Mean Net Gain (INR/qtl)")
    axes[0].set_title("(A) Leave-One-Tool-Out Ablation on Realized Profit")
    axes[0].legend(frameon=False, fontsize=8.5, loc="upper left")

    axes[1].bar(x - w / 2, all_r["cond_phantom_loss_rate_pct"], width=w, label="All Holdout PLR (%)", color="#4C72B0")
    axes[1].bar(x + w / 2, ext_r["cond_phantom_loss_rate_pct"], width=w, label="Extreme Heat/Rain PLR (%)", color="#C44E52")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, fontsize=8.5)
    axes[1].set_ylabel("Dispatched Phantom Loss Rate (%)")
    axes[1].set_title("(B) Impact of Tool Removal on False-Dispatch Risk")
    axes[1].legend(frameon=False, fontsize=8.5)

    fig.tight_layout()
    fig.savefig(fig_dir / "fig3_tool_ablation_and_monsoon_heat.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_fig4_budget_pareto(res_dir: Path, fig_dir: Path) -> None:
    df = pd.read_csv(res_dir / "exp5_budget_pareto.csv")
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    styles = {
        "MandiGuard": ("#1B7837", "o-", "MandiGuard (Sequential Funnel)"),
        "B4_UpfrontAllTools": ("#2B8CBE", "s--", "B4: Upfront All-Tools"),
        "B5_MultiAgentCoordinator": ("#FD8D3C", "^:", "B5: 3-Agent Quantized Bus"),
    }
    for pname, (col, fmt, lbl) in styles.items():
        sub = df[df["policy"] == pname].sort_values("avg_tool_calls")
        ax.plot(sub["avg_tool_calls"], sub["mean_delta_net_inr"], fmt, color=col, linewidth=2.0, markersize=6, label=lbl)
        if pname == "MandiGuard":
            for _, row in sub.iterrows():
                if int(row["budget_cap"]) in (4, 6, 8, 12, 20):
                    ax.annotate(
                        f"B={int(row['budget_cap'])}",
                        (row["avg_tool_calls"], row["mean_delta_net_inr"]),
                        textcoords="offset points",
                        xytext=(-6, 7),
                        fontsize=7.5,
                        color=col,
                        fontweight="bold",
                    )
        elif pname == "B4_UpfrontAllTools":
            for _, row in sub.iterrows():
                if int(row["budget_cap"]) in (8, 20):
                    ax.annotate(
                        f"B={int(row['budget_cap'])}",
                        (row["avg_tool_calls"], row["mean_delta_net_inr"]),
                        textcoords="offset points",
                        xytext=(5, -10),
                        fontsize=7.5,
                        color=col,
                    )

    ax.set_xlabel("Average External Tool Calls per Episode")
    ax.set_ylabel("Mean Realized Net Gain (INR/qtl)")
    ax.set_title("Tool-Call Cost vs. Realized Dispatch Utility Frontier (Holdout)")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig4_tool_budget_pareto.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_fig5_hp_apple_grades(res_dir: Path, fig_dir: Path) -> None:
    df = pd.read_csv(res_dir / "exp3_hp_apple_grade_holdout.csv")
    all_g = df[df["Grade"] == "ALL_GRADES"].set_index("policy").loc[
        ["B1_NaiveScreenGreedy", "B2_FreshRoadGreedy", "B3_MLPointDispatch", "MandiGuard"]
    ]
    grades = df[df["Grade"] != "ALL_GRADES"]
    top_grades = grades[grades["policy"] == "B1_NaiveScreenGreedy"].sort_values("n_episodes", ascending=False)["Grade"].head(4).tolist()
    sub_g = df[df["Grade"].isin(top_grades)]

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6))
    x = np.arange(len(all_g))
    w = 0.35
    axes[0].bar(x - w / 2, all_g["mean_delta_net_inr"], width=w, label="Mean DeltaNet (INR/qtl)", color="#2B8CBE")
    ax2 = axes[0].twinx()
    ax2.bar(x + w / 2, all_g["cond_closed_or_trap_rate_pct"], width=w, label="Closed/Grade Trap (%)", color="#C44E52")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(["B1 Naive", "B2 Fresh+Road", "B3 ML Point", "MandiGuard"], fontsize=8.5)
    axes[0].set_ylim(0, 1450)
    ax2.set_ylim(0, 122)
    axes[0].set_ylabel("Mean Net Gain (INR/qtl)", color="#2B8CBE")
    ax2.set_ylabel("Dispatched Trap Rate (%)", color="#C44E52")
    axes[0].set_title("(A) 2026 HP Apple Grade-Explicit Holdout (Overall)")
    h1, l1 = axes[0].get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    axes[0].legend(h1 + h2, l1 + l2, frameon=False, fontsize=8.0, loc="upper right", ncol=2)

    xg = np.arange(len(top_grades))
    wg = 0.35
    b1_g = sub_g[sub_g["policy"] == "B1_NaiveScreenGreedy"].set_index("Grade").loc[top_grades]
    mg_g = sub_g[sub_g["policy"] == "MandiGuard"].set_index("Grade").loc[top_grades]
    axes[1].bar(xg - wg / 2, b1_g["cond_closed_or_trap_rate_pct"], width=wg, label="B1 Naive Trap %", color="#C44E52")
    axes[1].bar(xg + wg / 2, mg_g["cond_closed_or_trap_rate_pct"], width=wg, label="MandiGuard Trap %", color="#1B7837")
    axes[1].set_xticks(xg)
    axes[1].set_xticklabels(top_grades, fontsize=8.5)
    axes[1].set_ylim(0, 118)
    axes[1].set_ylabel("Closed / Grade-Mismatch Trap Rate (%)")
    axes[1].set_title("(B) Grade-Wise Execution Trap Elimination")
    axes[1].legend(frameon=False, fontsize=8.5, loc="upper right")

    fig.tight_layout()
    fig.savefig(fig_dir / "fig5_hp_apple_grade_traps.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_fig6_sensitivity(res_dir: Path, fig_dir: Path) -> None:
    df = pd.read_csv(res_dir / "exp6_sensitivity_grid.csv")
    grid = df[df["use_state_statutory_fees"] == True].copy()
    p1 = grid.pivot(index="freight_mult", columns="spoilage_mult", values="MG_minus_B1_inr")
    p2 = grid.pivot(index="freight_mult", columns="spoilage_mult", values="MG_minus_B2_inr")

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4))
    for ax, piv, title in [
        (axes[0], p1, "(A) MandiGuard Gain over Naive Screen B1 (INR/qtl)"),
        (axes[1], p2, "(B) MandiGuard Gain over Fresh+Road B2 (INR/qtl)"),
    ]:
        im = ax.imshow(piv.to_numpy(), cmap="YlGn", aspect="auto")
        ax.set_xticks(np.arange(len(piv.columns)))
        ax.set_xticklabels([f"{c}x" for c in piv.columns])
        ax.set_yticks(np.arange(len(piv.index)))
        ax.set_yticklabels([f"{r}x" for r in piv.index])
        ax.set_xlabel("Weather Spoilage Multiplier")
        ax.set_ylabel("Freight Cost Multiplier")
        ax.set_title(title)
        vals = piv.to_numpy()
        for i in range(vals.shape[0]):
            for j in range(vals.shape[1]):
                ax.text(j, i, f"Rs {vals[i, j]:+.1f}", ha="center", va="center", color="black", fontweight="bold", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.tight_layout()
    fig.savefig(fig_dir / "fig6_sensitivity_and_govt_fees.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_fig7_decade_and_modern_ai(res_dir: Path, fig_dir: Path) -> None:
    d10 = pd.read_csv(res_dir / "exp10_decade_regime_evolution_2017_2026.csv")
    d11 = pd.read_csv(res_dir / "exp11_modern_ai_and_aci_showdown.csv")

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.4))

    # Panel A: 10-Year Macro-Economic & Climate Regime Evolution (Exp 10)
    regimes = [
        ("2017H2_GST_Transition", "2017H2\nGST"),
        ("2018-2019_PreCOVID", "2018-19\nPre-COVID"),
        ("2020-2021_COVID_Shock", "2020-21\nCOVID"),
        ("2022-2023_Inflation_ExportCurb", "2022-23\nInfl./Curb"),
        ("2024_ElNino_Heatwave", "2024\nEl-Nino"),
        ("2025-2026_Holdout_Benchmark", "2025-26\nHoldout"),
    ]
    x = np.arange(len(regimes))
    w = 0.26
    pol_specs = [
        ("B1_NaiveScreen", "B1 Naive Screen", "#C44E52"),
        ("B2_FreshRoad", "B2 Fresh+Road", "#DD8452"),
        ("MandiGuard_Expanding", "MandiGuard (Causal)", "#1B7837"),
    ]
    for k, (pkey, plabel, pcol) in enumerate(pol_specs):
        sub = d10[d10["policy"] == pkey].set_index("regime").loc[[r[0] for r in regimes]]
        pos = x + (k - 1) * w
        axes[0].bar(pos, sub["mean_net_gain_inr_qtl"], width=w, label=plabel, color=pcol)
        for j, (_, row) in enumerate(sub.iterrows()):
            if k in (0, 2):
                axes[0].text(
                    pos[j],
                    row["mean_net_gain_inr_qtl"] + 8,
                    f"{row['loss_trip_rate_pct']:.0f}%\nloss",
                    ha="center",
                    va="bottom",
                    fontsize=7.2,
                    color=pcol,
                    fontweight="bold",
                )

    axes[0].set_xticks(x)
    axes[0].set_xticklabels([r[1] for r in regimes], fontsize=8.8)
    axes[0].set_ylim(0, 560)
    axes[0].set_ylabel("Mean Net Gain (INR/qtl)")
    axes[0].set_title("(A) 10-Year Regime Robustness (2017-2026, Loss-Trip % Annotated)", pad=22)
    axes[0].legend(frameon=False, fontsize=8.5, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)

    # Panel B: Modern AI & ACI Showdown (Holdout 6-State + HP Apple Shift Insight)
    h6 = d11[d11["benchmark"] == "Holdout_6State_2025_2026"].sort_values("mean_net_gain_inr_qtl", ascending=True)
    name_map = {
        "Contextual_UCB_Bandit": "Contextual UCB Bandit",
        "Deep_MLP_Conformal": "Deep MLP + Conformal",
        "MandiGuard_ACI_NeurIPS21": "MandiGuard ACI (NeurIPS'21)",
        "MandiGuard_Standard": "MandiGuard Std (HGBR+Conf)",
        "ExtraTrees_Conformal": "ExtraTrees + Conformal",
        "Direct_Quantile_GBDT_Q20": "Direct Quantile GBDT (Q20)",
    }
    colors_b = [
        "#1B7837" if "MandiGuard_Std" in p else ("#2B8CBE" if "ACI" in p else ("#55A868" if "Quantile" in p else "#7F7F7F"))
        for p in h6["policy"]
    ]
    y = np.arange(len(h6))
    axes[1].barh(y, h6["mean_net_gain_inr_qtl"], color=colors_b, height=0.58)
    axes[1].set_yticks(y)
    axes[1].set_yticklabels([name_map.get(p, p) for p in h6["policy"]], fontsize=8.8)
    axes[1].set_xlim(350, 560)
    axes[1].set_ylim(-1.45, 5.55)
    axes[1].set_xlabel("Mean Net Gain on 6-State Holdout (INR/qtl)")
    axes[1].set_title("(B) Modern Predictors & ACI Tail Safety (Holdout & HP Shift)", pad=12)
    for idx, (_, row) in enumerate(h6.iterrows()):
        axes[1].text(
            row["mean_net_gain_inr_qtl"] + 2.5,
            idx,
            f"Rs {row['mean_net_gain_inr_qtl']:.1f} | LTR {row['loss_trip_rate_pct']:.1f}% | W10 {row['worst_10pct_loss_inr_qtl']:+.0f}",
            va="center",
            fontsize=7.8,
        )
    axes[1].text(
        354,
        -0.92,
        "HP Apple Shift (N=1,537): Deep MLP leads mean (Rs 615.3/qtl);\nACI cuts tail Worst-10% loss by 27.6% (-Rs 102.8 -> -Rs 74.4/qtl)",
        fontsize=8.0,
        va="center",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#F4F6F9", "edgecolor": "#B0BEC5"},
    )

    fig.tight_layout()
    fig.savefig(fig_dir / "fig7_decade_2017_2026_evolution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def make_fig8_zerocloud_fpo_clock(res_dir: Path, fig_dir: Path) -> None:
    d12 = pd.read_csv(res_dir / "exp12_zerocloud_money_efficient_agent.csv")
    d13 = pd.read_csv(res_dir / "exp13_outofbox_fpo_pooling_and_spoilage_clock.csv")
    d13b = pd.read_csv(res_dir / "exp13b_biological_spoilage_clock.csv")

    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.4))

    # Panel A: MandiGuard-ZeroCloud & Satisficing Cost-Value Frontier (Exp 12)
    p_cols = {
        "B4_UpfrontAllTools": ("B4 Upfront All APIs\n(15.74 calls)", "#C44E52", (10, -4), "left", "top"),
        "B5_MultiAgentCoordinator": ("B5 Multi-Agent\n(8.76 calls)", "#8172B3", (0, -10), "center", "top"),
        "MandiGuard_Standard": ("MandiGuard Std\n(8.75 calls)", "#2B8CBE", (0, 10), "center", "bottom"),
        "MandiGuard_ZeroCloud_Full": ("ZeroCloud Full\n(5.53 live calls)", "#1B7837", (10, 0), "left", "center"),
        "MandiGuard_ZeroCloud_Satisficing": ("ZeroCloud Satisficing\n(3.84 live calls)", "#006837", (-12, 0), "right", "center"),
    }
    xs = d12["api_cost_per_10k_queries_inr"].to_numpy()
    ys = d12["mean_net_gain_inr_qtl"].to_numpy()
    axes[0].plot(xs[[0, 2, 3, 4]], ys[[0, 2, 3, 4]], linestyle="--", color="#90A4AE", linewidth=1.2, zorder=1)
    for _, row in d12.iterrows():
        pkey = str(row["policy"])
        lbl, col, offset_xy, ha, va = p_cols[pkey]
        axes[0].scatter(row["api_cost_per_10k_queries_inr"], row["mean_net_gain_inr_qtl"], color=col, s=110, zorder=3)
        axes[0].annotate(
            f"{lbl}\nRs {row['mean_net_gain_inr_qtl']:.1f}/qtl",
            xy=(row["api_cost_per_10k_queries_inr"], row["mean_net_gain_inr_qtl"]),
            xytext=offset_xy,
            textcoords="offset points",
            fontsize=8.0,
            color=col,
            fontweight="bold",
            ha=ha,
            va=va,
        )
    axes[0].set_xlim(8600, 900)
    axes[0].set_ylim(433, 459.5)
    axes[0].set_xlabel("Live API Cost per 10,000 Farmer Advisories (INR, lower is better ->)")
    axes[0].set_ylabel("Mean Net Gain (INR/qtl)")
    axes[0].set_title("(A) ZeroCloud Edge-AI & Satisficing Cost Frontier (Exp 12)", pad=12)

    # Panel B: FPO 90-qtl Shared Truck Pooling + Split-Lot Portfolio + Spoilage Clock (Exp 13/13b)
    order_13 = [
        ("B1_Marginal_Solo_10qtl_1.60xFreight", "B1 Marginal Solo (10-qtl, 1.6x)", "#C44E52"),
        ("B1_Standard_MiniTruck_30qtl_1.00xFreight", "B1 Standard Solo (30-qtl, 1.0x)", "#DD8452"),
        ("Split_Top2_Portfolio_StandardFreight", "Split Top-2 Portfolio (50/50)", "#2B8CBE"),
        ("MandiGuard_Marginal_Solo_10qtl_1.60xFreight", "MandiGuard Marginal (10-qtl, 1.6x)", "#74C476"),
        ("MandiGuard_Standard_MiniTruck_30qtl_1.00xFreight", "MandiGuard Solo (30-qtl, 1.0x)", "#238B45"),
        ("MandiGuard_Cooperative_FPO_90qtl_0.70xFreight", "MandiGuard FPO Pool (90-qtl, 0.7x)", "#005A32"),
    ]
    d13_i = d13.set_index("policy")
    yb = np.arange(len(order_13))
    vals_b = [float(d13_i.at[k, "mean_net_gain_inr_qtl"]) for k, _, _ in order_13]
    ltrs_b = [float(d13_i.at[k, "loss_trip_rate_pct"]) for k, _, _ in order_13]
    trps_b = [float(d13_i.at[k, "closed_trap_rate_pct"]) for k, _, _ in order_13]
    cols_b = [c for _, _, c in order_13]

    axes[1].barh(yb, vals_b, color=cols_b, height=0.58)
    axes[1].set_yticks(yb)
    axes[1].set_yticklabels([lbl for _, lbl, _ in order_13], fontsize=8.5)
    axes[1].set_xlim(0, 660)
    axes[1].set_ylim(-1.45, 5.55)
    axes[1].set_xlabel("Mean Net Gain (INR/qtl)")
    axes[1].set_title("(B) FPO Pooling, Top-2 Split Portfolio & Spoilage Clock (Exp 13)", pad=12)
    for idx in range(len(order_13)):
        axes[1].text(
            vals_b[idx] + 6,
            idx,
            f"Rs {vals_b[idx]:.1f} | LTR {ltrs_b[idx]:.1f}% | Trap {trps_b[idx]:.1f}%",
            va="center",
            fontsize=7.8,
        )

    tom_20 = float(d13b[(d13b["commodity"] == "Tomato") & (d13b["temp_c"] == 20.0)]["safe_transit_hours_to_15pct_loss"].iloc[0])
    tom_42 = float(d13b[(d13b["commodity"] == "Tomato") & (d13b["temp_c"] == 42.0)]["safe_transit_hours_to_15pct_loss"].iloc[0])
    pot_42 = float(d13b[(d13b["commodity"] == "Potato") & (d13b["temp_c"] == 42.0)]["safe_transit_hours_to_15pct_loss"].iloc[0])
    axes[1].text(
        10,
        -0.92,
        f"Biological Spoilage Clock (to 15% loss): Tomato 20C: {tom_20:.1f}h -> 42C: {tom_42:.1f}h | Potato 42C: {pot_42:.1f}h",
        fontsize=7.8,
        va="center",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#FFF8E1", "edgecolor": "#FFB300"},
    )

    fig.tight_layout()
    fig.savefig(fig_dir / "fig8_zerocloud_fpo_and_modern_ai.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    res_dir = root / "results"
    fig_dir = root / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    make_fig1_phantom_anatomy(res_dir, fig_dir)
    make_fig2_main_policy_comparison(res_dir, fig_dir)
    make_fig3_ablation_and_weather(res_dir, fig_dir)
    make_fig4_budget_pareto(res_dir, fig_dir)
    make_fig5_hp_apple_grades(res_dir, fig_dir)
    make_fig6_sensitivity(res_dir, fig_dir)
    make_fig7_decade_and_modern_ai(res_dir, fig_dir)
    make_fig8_zerocloud_fpo_clock(res_dir, fig_dir)
    print("=== ALL 8 PUBLICATION FIGURES GENERATED ===")


if __name__ == "__main__":
    main()
