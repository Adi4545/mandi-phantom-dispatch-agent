"""Draw the corrected modeled mean/expected-shortfall comparison from the replay tables."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
POLICIES = ["B1_NaiveScreenGreedy", "B2_FreshRoadGreedy", "MandiGuard"]


def main():
    main_table = pd.read_csv(ROOT / "results/exp2_main_benchmark_6state.csv")
    apple_table = pd.read_csv(ROOT / "results/exp3_hp_apple_grade_holdout.csv")
    panels = [
        ("Six-state panel", main_table),
        ("Graded Himachal apples", apple_table[apple_table.Grade == "ALL_GRADES"]),
    ]
    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.2), constrained_layout=True)
    for axis, (title, table) in zip(axes, panels):
        table = table.set_index("policy").loc[POLICIES]
        for index, (_, row) in enumerate(table.iterrows()):
            lower, mean = row.cvar_10_inr, row.mean_delta_net_inr
            axis.plot([lower, mean], [index, index], color="#AEB8BE", lw=2, zorder=1)
            axis.scatter(lower, index, color="#A53925", marker="s", label="Worst 10% mean" if index == 0 else None)
            axis.scatter(mean, index, color="#116558", label="All-episode mean" if index == 0 else None)
        axis.set_title(f"{title}  ({int(table.n_episodes.iloc[0]):,} episodes)", loc="left")
        axis.set_yticks(range(3), ["Stale-price rule", "Fresh-road rule", "MandiGuard v1"])
        axis.set_ylim(2.5, -0.5)
        axis.axvline(0, color="#737D84", lw=0.8, ls="--")
        axis.spines[["top", "right", "left"]].set_visible(False)
    axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, 1.45), ncol=2, frameon=False)
    axes[-1].set_xlabel("Modeled incremental payoff (rupees per quintal)")
    fig.savefig(ROOT / "figures/corrected_benchmark.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    main()
