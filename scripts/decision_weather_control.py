"""Paired, frozen-policy sensitivity to information available about the weather."""
import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.baselines.dispatch_baselines import eval_b2_fresh_road_greedy
from src.models.uncensored_crc_forecaster import CRCConfig, UncensoredCRCForecaster, evaluate_mandiguard_crc


# Characteristic reference conditions in the baseline payoff model. These three
# values are constants and require no forecast vintage or observations.
REFERENCE = {"route_fc_tmax": 20.0, "route_fc_rh": 70.0, "route_fc_rain": 0.0}
FROZEN_LAMBDA = 0.15


def digest(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def evaluate_panel(name, frame, v1, crc, crc_config, margin, hurdle, dates):
    frame["pred_ret"], frame["lcb_ret"] = v1.predict_point_and_causal_lcb(frame)
    start, last_decision, last_arrival = map(pd.Timestamp, dates)
    hold = frame[frame.date.between(start, last_decision) & (frame.arrival_date <= last_arrival)].copy()
    baseline = eval_b2_fresh_road_greedy(hold, hurdle_inr=hurdle).set_index("episode_id").sort_index()
    rows = []
    original = {}
    # Only decision weather changes. Both arms use the same candidate rows,
    # fitted trees, cutoffs, reference prices, adaptive residuals and payoff.
    for arm in ["archived", "fixed_reference"]:
        if arm == "fixed_reference":
            for col, value in REFERENCE.items():
                hold[col] = value
        v1_out, _ = evaluate_mandiguard_vectorized(hold, AgentConfig(safety_margin_inr=margin, screen_hurdle_inr=hurdle))
        crc_out = evaluate_mandiguard_crc(hold, cfg=crc_config, lambda_risk=FROZEN_LAMBDA,
                                          precomputed=crc.predict_components(hold))
        for policy, out in [("B2", baseline.reset_index()), ("v1", v1_out), ("stage_ii", crc_out)]:
            ordered = out.set_index("episode_id").sort_index()
            if not baseline.index.equals(ordered.index):
                raise ValueError("Policies have different episode sets")
            if arm == "archived":
                original[policy] = ordered[["chosen_dest","delta_net_inr"]].copy()
            payoff = ordered.delta_net_inr
            dispatch = ordered.is_dispatch
            n_loss = int((payoff < 0).sum())
            rows.append({"panel": name, "decision_weather": arm, "policy": policy, "episodes": len(payoff),
                         "dispatches": int(dispatch.sum()), "negative_episodes": n_loss,
                         "mean_inr_per_qtl_per_episode": float(payoff.mean()),
                         "loss_pct_per_dispatch": float(100 * n_loss / dispatch.sum()),
                         "mean_minus_B2": float((payoff - baseline.delta_net_inr).mean()),
                         "mean_minus_own_archived_weather": float((payoff-original[policy].delta_net_inr).mean()),
                         "changed_action_or_destination": int(ordered.chosen_dest.ne(original[policy].chosen_dest).sum())})
        print(f"{name} {arm} complete", flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-candidates", type=Path, default=ROOT / "data/processed/candidates_6state.parquet")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "final")
    args = parser.parse_args()
    cfg = json.loads((ROOT / "configs/config.json").read_text())
    splits = cfg["temporal_splits"]
    margin = json.loads((ROOT / "configs/frozen_calibration.json").read_text())["frozen_safety_margin_inr"]
    hurdle = cfg["agent_defaults"]["screen_hurdle_inr_qtl"]
    seed = cfg["master_seed"]
    crc_config = CRCConfig(thin_grade_aware_t1=True, use_euclid_step0_sort=True,
                           safety_margin_inr=margin, screen_hurdle_inr=hurdle)
    model_path = ROOT / "data/interim/forecaster_2024.pkl"
    apple_path = ROOT / "data/processed/candidates_hp_apple_grade.parquet"
    with model_path.open("rb") as file:
        v1 = pickle.load(file)
    # Stage II has no committed binary. Recover its historical training recipe
    # once; evaluate exactly these fitted trees and the published multiplier in both arms.
    training = pd.read_parquet(args.main_candidates, filters=[("date", "<=", pd.Timestamp(splits["train_end"]))])
    crc = UncensoredCRCForecaster(seed=seed).fit(training, crc_config)
    training_rows = len(training)
    del training
    print("Stage II training complete", flush=True)
    post = pd.read_parquet(args.main_candidates, filters=[("date", ">=", pd.Timestamp(splits["val_start"]))])
    rows = evaluate_panel("six_state", post, v1, crc, crc_config, margin, hurdle,
                          (splits["test_start"], splits["test_end"], splits["test_end"]))
    del post
    apple = pd.read_parquet(apple_path)
    rows.extend(evaluate_panel("hp_apple", apple, v1, crc, crc_config, margin, hurdle,
                               (splits["apple_test_start"], "2026-08-27", splits["apple_test_end"])))
    meta = {"reference_weather": REFERENCE, "frozen_lambda": FROZEN_LAMBDA, "frozen_margin": margin,
            "model_seed": seed, "training_candidate_rows_before_stage_ii_filters": training_rows,
            "train_end": splits["train_end"], "decision_clock_qualification": "Only the fixed weather vector is point-in-time by construction.",
            "sha256": {"main_candidates": digest(args.main_candidates), "hp_candidates": digest(apple_path),
                       "stage_i_fitted_model": digest(model_path)}, "python":sys.version.split()[0],
            "numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__}
    args.output_dir.mkdir(exist_ok=True, parents=True)
    pd.DataFrame(rows).to_csv(args.output_dir / "decision-weather-control.csv", index=False)
    (args.output_dir / "decision-weather-control-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
