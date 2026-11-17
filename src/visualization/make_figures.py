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
    axes[0].legend(frameon=False, fontsize=8.5, loc="upper left")

    # Panel B: Trap & Phantom Loss rates across States
    y = np.arange(len(states))
    h = 0.36
    axes[1].barh(y + h / 2, states["closed_or_variety_trap_pct"], height=h, label="Closed / No-Variety Trap (%)", color="#8172B3")
    axes[1].barh(y - h / 2, states["phantom_loss_rate_pct"], height=h, label="Net Loss Dispatch Rate (%)", color="#C44E52")
    axes[1].set_yticks(y)
    axes[1].set_yticklabels(states["slice_value"])
    axes[1].set_xlabel("Percentage of Naive Screen Dispatches (%)")
    axes[1].set_title("(B) Physical Trap & Phantom Loss Rates Across States")
    axes[1].legend(frameon=False, fontsize=8.5, loc="lower right")
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
    axes[0].set_ylabel("Mean Net Gain (INR/qtl)")
    axes[0].set_title("(A) Leave-One-Tool-Out Ablation on Realized Profit")
    axes[0].legend(frameon=False, fontsize=8.5)

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
        for _, row in sub.iterrows():
            if int(row["budget_cap"]) in (2, 4, 8, 20):
                ax.annotate(
                    f"B={int(row['budget_cap'])}",
                    (row["avg_tool_calls"], row["mean_delta_net_inr"]),
                    textcoords="offset points",
                    xytext=(4, 5),
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
    axes[0].set_ylabel("Mean Net Gain (INR/qtl)", color="#2B8CBE")
    ax2.set_ylabel("Dispatched Trap Rate (%)", color="#C44E52")
    axes[0].set_title("(A) 2026 HP Apple Grade-Explicit Holdout (Overall)")

    xg = np.arange(len(top_grades))
    wg = 0.35
    b1_g = sub_g[sub_g["policy"] == "B1_NaiveScreenGreedy"].set_index("Grade").loc[top_grades]
    mg_g = sub_g[sub_g["policy"] == "MandiGuard"].set_index("Grade").loc[top_grades]
    axes[1].bar(xg - wg / 2, b1_g["cond_closed_or_trap_rate_pct"], width=wg, label="B1 Naive Trap %", color="#C44E52")
    axes[1].bar(xg + wg / 2, mg_g["cond_closed_or_trap_rate_pct"], width=wg, label="MandiGuard Trap %", color="#1B7837")
    axes[1].set_xticks(xg)
    axes[1].set_xticklabels(top_grades, fontsize=8.5)
    axes[1].set_ylabel("Closed / Grade-Mismatch Trap Rate (%)")
    axes[1].set_title("(B) Grade-Wise Execution Trap Elimination")
    axes[1].legend(frameon=False, fontsize=8.5)

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
                ax.text(j, i, f"+Rs {vals[i, j]:.1f}", ha="center", va="center", color="black", fontweight="bold", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.tight_layout()
    fig.savefig(fig_dir / "fig6_sensitivity_and_govt_fees.png", dpi=300, bbox_inches="tight")
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
    print("=== ALL 6 PUBLICATION FIGURES GENERATED ===")


if __name__ == "__main__":
    main()
