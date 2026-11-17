"""Exploratory diagnostics: Leave-One-State-Out (LOSO) transfer & exact Arrival Price Drop %."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.baselines.dispatch_baselines import eval_b1_naive_screen_greedy, eval_b2_fresh_road_greedy, eval_b3_ml_point_dispatch
from src.models.arrival_forecaster import CausalArrivalForecaster
from src.utils.leakage import load_config


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root)
    splits = cfg["temporal_splits"]
    seed = int(cfg["master_seed"])
    hurdle = float(cfg["agent_defaults"]["screen_hurdle_inr_qtl"])
    frozen_margin = float(json.loads((root / "configs/frozen_calibration.json").read_text())["frozen_safety_margin_inr"])

    cand = pd.read_parquet(root / "data/processed/candidates_6state.parquet")
    cand["date_dt"] = pd.to_datetime(cand["date"])
    cand["arr_dt"] = pd.to_datetime(cand["arrival_date"])

    train_24 = cand[(cand["date_dt"] <= splits["train_end"]) & (cand["arr_dt"] <= splits["train_end"])].copy()
    hold = cand[(cand["date_dt"] >= splits["test_start"]) & (cand["arr_dt"] <= splits["test_end"])].copy()

    rows = []
    for held_state in cfg["states"]:
        tr_sub = train_24[train_24["State"] != held_state].copy()
        fc_loso = CausalArrivalForecaster(seed=seed, alpha_target=cfg["agent_defaults"]["lcb_alpha_target"]).fit(tr_sub)

        # Warm conformal residuals strictly within held_state starting Val_2025H1 -> score Holdout
        st_2526 = cand[(cand["State"] == held_state) & (cand["date_dt"] >= splits["val_start"]) & (cand["arr_dt"] <= splits["test_end"])].copy()
        p_ret, l_ret = fc_loso.predict_point_and_causal_lcb(st_2526)
        st_2526["pred_ret"], st_2526["lcb_ret"] = p_ret, l_ret
        st_hold = st_2526[st_2526["date_dt"] >= splits["test_start"]].copy()

        b1 = eval_b1_naive_screen_greedy(st_hold, hurdle_inr=hurdle)
        b2 = eval_b2_fresh_road_greedy(st_hold, hurdle_inr=hurdle)
        b3 = eval_b3_ml_point_dispatch(st_hold, safety_margin_inr=frozen_margin)
        mg, _ = evaluate_mandiguard_vectorized(st_hold, AgentConfig(screen_hurdle_inr=hurdle, safety_margin_inr=frozen_margin))

        for pname, d in [("B1_NaiveScreenGreedy", b1), ("B2_FreshRoadGreedy", b2), ("B3_MLPointDispatch", b3), ("MandiGuard_LOSO", mg)]:
            disp = d["is_dispatch"]
            rows.append(
                {
                    "held_out_state": held_state,
                    "policy": pname,
                    "n_episodes": len(d),
                    "dispatch_rate_pct": round(float(disp.mean() * 100.0), 2),
                    "mean_delta_net_inr": round(float(d["delta_net_inr"].mean()), 2),
                    "cond_phantom_loss_rate_pct": round(float(d.loc[disp, "is_phantom_loss"].mean() * 100.0), 2) if disp.any() else 0.0,
                    "cond_arrival_drop_rate_pct": round(float(d.loc[disp, "is_arrival_drop"].mean() * 100.0), 2) if disp.any() else 0.0,
                    "cond_closed_trap_rate_pct": round(float(d.loc[disp, "is_closed_trap"].mean() * 100.0), 2) if disp.any() else 0.0,
                }
            )
        print(f"  [LOSO {held_state}] MG_LOSO Mean dNet=Rs {rows[-1]['mean_delta_net_inr']:.1f}/qtl, PLR={rows[-1]['cond_phantom_loss_rate_pct']:.1f}%, ArrDrop={rows[-1]['cond_arrival_drop_rate_pct']:.1f}%")

    out_df = pd.DataFrame(rows)
    out_df.to_csv(root / "results/exp9_loso_transfer_and_arrival_drop.csv", index=False)
    print("=== LOSO & ARRIVAL DROP DIAGNOSTIC SAVED ===")


if __name__ == "__main__":
    main()
