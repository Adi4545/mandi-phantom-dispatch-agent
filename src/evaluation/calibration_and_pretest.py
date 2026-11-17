"""Step 3: Strictly pre-holdout training (2024) and validation calibration (2025-01..05).

Never touches holdout dates (>= 2025-06-01). Audits 2024/Val_2025H1 market price structure,
fits CausalArrivalForecaster on 2024, saves the frozen forecaster, and freezes safety_margin_inr.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.baselines.dispatch_baselines import eval_b1_naive_screen_greedy, eval_b2_fresh_road_greedy
from src.models.arrival_forecaster import CausalArrivalForecaster
from src.utils.leakage import assert_no_future_leakage_dates, load_config


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root)
    splits = cfg["temporal_splits"]

    cands = pd.read_parquet(root / "data/processed/candidates_6state.parquet")
    cands["date_dt"] = pd.to_datetime(cands["date"])
    cands["arr_dt"] = pd.to_datetime(cands["arrival_date"])

    train_df = cands[(cands["date_dt"] <= splits["train_end"]) & (cands["arr_dt"] <= splits["train_end"])].copy()
    val_df = cands[
        (cands["date_dt"] >= splits["val_start"])
        & (cands["date_dt"] <= splits["val_end"])
        & (cands["arr_dt"] <= splits["val_end"])
    ].copy()
    assert_no_future_leakage_dates(train_df, val_df, cfg)

    print(f"[Step 3] Train_2024 candidates: {len(train_df):,} ({train_df['episode_id'].nunique():,} eps)")
    print(f"[Step 3] Val_2025H1 candidates: {len(val_df):,} ({val_df['episode_id'].nunique():,} eps)")

    # Diagnostic check on 2024/2025-01..05: verify wholesale spread sanity (no extreme persistent retail outliers)
    b1_val = eval_b1_naive_screen_greedy(val_df, hurdle_inr=cfg["agent_defaults"]["screen_hurdle_inr_qtl"])
    b2_val = eval_b2_fresh_road_greedy(val_df, hurdle_inr=cfg["agent_defaults"]["screen_hurdle_inr_qtl"])
    print(
        f"  [Val B1 Naive] dispatch={(b1_val['is_dispatch'].mean()*100):.1f}% | "
        f"Mean dNet=Rs {b1_val['delta_net_inr'].mean():.1f}/qtl | "
        f"PLR={(b1_val.loc[b1_val['is_dispatch'], 'is_phantom_loss'].mean()*100):.1f}% | "
        f"Trap={(b1_val.loc[b1_val['is_dispatch'], 'is_closed_trap'].mean()*100):.1f}%"
    )
    print(
        f"  [Val B2 FreshRoad] dispatch={(b2_val['is_dispatch'].mean()*100):.1f}% | "
        f"Mean dNet=Rs {b2_val['delta_net_inr'].mean():.1f}/qtl | "
        f"PLR={(b2_val.loc[b2_val['is_dispatch'], 'is_phantom_loss'].mean()*100):.1f}% | "
        f"Trap={(b2_val.loc[b2_val['is_dispatch'], 'is_closed_trap'].mean()*100):.1f}%"
    )

    # Fit CausalArrivalForecaster strictly on Train_2024
    forecaster = CausalArrivalForecaster(
        seed=cfg["master_seed"], alpha_target=cfg["agent_defaults"]["lcb_alpha_target"]
    ).fit(train_df)
    pred_val, lcb_val = forecaster.predict_point_and_causal_lcb(val_df)
    val_df["pred_ret"] = pred_val
    val_df["lcb_ret"] = lcb_val

    # Check empirical 80% LCB coverage on matured Val_2025H1 exact arrivals
    obs_val = val_df["target_ret"].notna()
    emp_cov = float((val_df.loc[obs_val, "target_ret"] >= val_df.loc[obs_val, "lcb_ret"]).mean())
    print(f"  [Val Causal Conformal LCB] Empirical coverage (target >=80%): {emp_cov*100:.2f}%")

    # Sweep safety_margin_inr strictly on Val_2025H1 to freeze hyperparameter before touching holdout
    sweep_rows = []
    for margin in [50.0, 100.0, 150.0, 200.0, 250.0]:
        acfg = AgentConfig(safety_margin_inr=margin)
        mg_val, _ = evaluate_mandiguard_vectorized(val_df, acfg)
        disp = mg_val["is_dispatch"]
        plr = float(mg_val.loc[disp, "is_phantom_loss"].mean() * 100) if disp.any() else 0.0
        sweep_rows.append(
            {
                "safety_margin_inr": margin,
                "dispatch_pct": round(float(disp.mean() * 100), 2),
                "mean_delta_net_inr": round(float(mg_val["delta_net_inr"].mean()), 2),
                "phantom_loss_rate_pct": round(plr, 2),
                "avg_tool_calls": round(float(mg_val["tool_calls_total"].mean()), 2),
            }
        )
    sweep_df = pd.DataFrame(sweep_rows)
    print("  [Val Safety Margin Sweep]")
    print(sweep_df.to_string(index=False))

    # Select margin maximizing Val mean_delta_net_inr among policies with PLR <= 15% (or highest mean_delta_net_inr)
    ok = sweep_df[sweep_df["phantom_loss_rate_pct"] <= 15.0]
    best_row = (ok if len(ok) > 0 else sweep_df).sort_values("mean_delta_net_inr", ascending=False).iloc[0]
    frozen_margin = float(best_row["safety_margin_inr"])

    out_dir = root / "data/interim"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "forecaster_2024.pkl", "wb") as f:
        pickle.dump(forecaster, f)

    cal_summary = {
        "train_rows": int(len(train_df)),
        "val_rows": int(len(val_df)),
        "val_conformal_lcb_empirical_coverage_pct": round(emp_cov * 100, 2),
        "val_b1_mean_dnet": round(float(b1_val["delta_net_inr"].mean()), 2),
        "val_b1_plr_pct": round(float(b1_val.loc[b1_val["is_dispatch"], "is_phantom_loss"].mean() * 100), 2),
        "val_b2_mean_dnet": round(float(b2_val["delta_net_inr"].mean()), 2),
        "val_b2_plr_pct": round(float(b2_val.loc[b2_val["is_dispatch"], "is_phantom_loss"].mean() * 100), 2),
        "safety_margin_sweep": sweep_rows,
        "frozen_safety_margin_inr": frozen_margin,
    }
    (root / "configs/frozen_calibration.json").write_text(json.dumps(cal_summary, indent=2))
    print(f"=== FROZEN SAFETY MARGIN ON VAL_2025H1: Rs {frozen_margin:.0f}/qtl ===")


if __name__ == "__main__":
    main()
