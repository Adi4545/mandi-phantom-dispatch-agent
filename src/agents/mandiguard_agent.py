"""MandiGuard: Sequential Climate-, Road-, and Freshness-Aware Dispatch Agent.

Performs 4 metered verification steps over candidate corridors before emitting
{SELL_LOCAL, DISPATCH(j*), REFUSE_PHANTOM_SPREAD}, with full JSON-serializable trace logs:
  Step 0 (Screen, 0 calls): Shortlist top-K destinations with headline spread > hurdle.
  Tool T1 (verify_vitality_and_variety): Causal <= t staleness, 14d open prob, arrival DOW rate.
  Tool T2 (compute_osrm_freight): OSRM highway distance, truck lag, freight + APMC fees.
  Tool T3 (assess_weather_spoilage): Archived day-t weather forecast -> Q10 spoilage & rain flag.
  Tool T4 (forecast_arrival_lcb): 2024-trained forecaster + causal matured conformal 80% LCB.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.evaluation.payoff_model import PayoffParams, compute_freight_inr, compute_spoilage_fraction


@dataclass
class AgentConfig:
    screen_hurdle_inr: float = 100.0
    k_max: int = 5
    t1_max_age_days: int = 3
    t1_min_open_prob_14d: float = 0.50
    t1_min_dow_open_rate: float = 0.35
    safety_margin_inr: float = 150.0
    max_tool_calls_per_episode: Optional[int] = None  # None = unlimited within top-K funnel
    use_t1: bool = True
    use_t2_osrm: bool = True
    use_t3_weather: bool = True
    use_t4_lcb: bool = True
    log_traces: bool = False
    trace_limit: int = 400


def evaluate_mandiguard_vectorized(
    cand_df: pd.DataFrame,
    cfg: AgentConfig,
    payoff_params: PayoffParams = PayoffParams(),
) -> Tuple[pd.DataFrame, List[Dict]]:
    """Execute MandiGuard sequentially over pre-joined episode-candidate table.

    Note: Each row in `cand_df` is an (episode_id, dest_market) candidate generated at Step 0
    where `screen_spread = screen_dest_price - local_price > hurdle`. Tool call counters
    strictly mirror row-by-row sequential execution with optional per-episode tool budget.
    """
    df = cand_df.copy()
    # Sort within each episode by preliminary screen_spread descending (deterministic dest_market tie-break)
    df = df.sort_values(
        ["episode_id", "screen_spread", "dest_market"], ascending=[True, False, True]
    ).reset_index(drop=True)

    # Keep top k_max candidates per episode from Step 0 screen
    df["_cand_rank"] = df.groupby("episode_id").cumcount()
    df = df[df["_cand_rank"] < cfg.k_max].copy().reset_index(drop=True)

    ep_ids = df["episode_id"].to_numpy()
    n_rows = len(df)

    # Pre-extract arrays for blazing speed across 100k+ candidate rows
    local_p = df["local_price"].to_numpy(dtype=np.float64)
    screen_p = df["screen_dest_price"].to_numpy(dtype=np.float64)
    dest_ref_p = df["dest_ref_price"].to_numpy(dtype=np.float64)
    age_days = df["dest_age_days"].to_numpy(dtype=np.float64)
    open_prob = df["dest_open_prob_14d"].to_numpy(dtype=np.float64)
    dow_open = df["dest_dow_open_rate"].to_numpy(dtype=np.float64)
    intra_spread = df["dest_intra_spread_14d"].to_numpy(dtype=np.float64)

    states = df["State"].to_numpy()
    comms = df["Commodity"].to_numpy()
    same_dist = df["same_district"].to_numpy(dtype=bool)
    road_km = df["road_km"].to_numpy(dtype=np.float64)
    euclid_km = df["euclid_km"].to_numpy(dtype=np.float64)
    truck_hrs = df["truck_hours"].to_numpy(dtype=np.float64)

    fc_tmax = df["route_fc_tmax"].to_numpy(dtype=np.float64)
    fc_rh = df["route_fc_rh"].to_numpy(dtype=np.float64)
    fc_rain = df["route_fc_rain"].to_numpy(dtype=np.float64)

    pred_ret = df["pred_ret"].to_numpy(dtype=np.float64)
    lcb_ret = df["lcb_ret"].to_numpy(dtype=np.float64)

    real_dnet = df["real_delta_net_inr"].to_numpy(dtype=np.float64)
    real_open_d0 = df["real_open_d0_delta_net_inr"].to_numpy(dtype=np.float64)
    real_trap = df["real_closed_or_no_variety_trap"].to_numpy(dtype=bool)
    real_drop = df["real_arrival_price_dropped"].to_numpy(dtype=bool)

    dest_mkts = df["dest_market"].to_numpy()

    # Iterate cleanly grouped by episode boundaries (since df is sorted by episode_id)
    split_idx = np.flatnonzero(ep_ids[1:] != ep_ids[:-1]) + 1
    starts = np.concatenate(([0], split_idx))
    ends = np.concatenate((split_idx, [n_rows]))

    ep_records = []
    traces: List[Dict] = []

    for s_idx, e_idx in zip(starts, ends):
        ep_id = ep_ids[s_idx]
        budget = cfg.max_tool_calls_per_episode
        calls_used = 0
        t1_calls = t2_calls = t3_calls = t4_calls = 0

        best_j_idx = -1
        best_score = -1e18
        rejection_reasons: List[str] = []
        cand_trace = []

        for r in range(s_idx, e_idx):
            # Tool T1: Vitality & Variety check
            if cfg.use_t1:
                if budget is not None and calls_used >= budget:
                    rejection_reasons.append("BUDGET_EXHAUSTED")
                    break
                calls_used += 1
                t1_calls += 1
                p_fresh = dest_ref_p[r]
                t1_ok = (
                    np.isfinite(p_fresh)
                    and p_fresh > 0
                    and age_days[r] <= cfg.t1_max_age_days
                    and open_prob[r] >= cfg.t1_min_open_prob_14d
                    and dow_open[r] >= cfg.t1_min_dow_open_rate
                )
                if not t1_ok:
                    reason = "VARIETY_OR_STALE" if (not np.isfinite(p_fresh) or age_days[r] > cfg.t1_max_age_days) else "CLOSED_YARD_RISK"
                    rejection_reasons.append(reason)
                    if cfg.log_traces and len(traces) < cfg.trace_limit:
                        cand_trace.append({"dest": str(dest_mkts[r]), "T1": "PRUNE", "reason": reason})
                    continue
            else:
                p_fresh = screen_p[r] if np.isfinite(screen_p[r]) else dest_ref_p[r]
                if not np.isfinite(p_fresh) or p_fresh <= 0:
                    rejection_reasons.append("NO_PRICE")
                    continue

            # Tool T2: OSRM Highway Freight (or Euclidean ablation if use_t2_osrm=False)
            if cfg.use_t2_osrm:
                if budget is not None and calls_used >= budget:
                    rejection_reasons.append("BUDGET_EXHAUSTED")
                    break
                calls_used += 1
                t2_calls += 1
                dist_used = road_km[r]
                hrs_used = truck_hrs[r]
            else:
                dist_used = 1.15 * euclid_km[r]
                hrs_used = dist_used / 35.0
            freight_hat = compute_freight_inr(
                str(states[r]),
                float(dist_used),
                bool(same_dist[r]),
                float(local_p[r]),
                payoff_params,
                commodity=str(comms[r]),
            )
            if p_fresh - local_p[r] - freight_hat <= 0.0:
                rejection_reasons.append("FREIGHT_EXCEEDS_SPREAD")
                if cfg.log_traces and len(traces) < cfg.trace_limit:
                    cand_trace.append({"dest": str(dest_mkts[r]), "T1": "PASS", "T2": "PRUNE", "freight": round(freight_hat, 1)})
                continue

            # Tool T3: Weather-Conditioned Spoilage
            if cfg.use_t3_weather:
                if budget is not None and calls_used >= budget:
                    rejection_reasons.append("BUDGET_EXHAUSTED")
                    break
                calls_used += 1
                t3_calls += 1
                spoil_hat = compute_spoilage_fraction(
                    str(comms[r]), float(hrs_used), float(fc_tmax[r]), float(fc_rh[r]), float(fc_rain[r]), 0, payoff_params
                )
                rain_pen = (0.50 * p_fresh * float(np.nan_to_num(intra_spread[r], nan=0.10))) if fc_rain[r] >= payoff_params.heavy_rain_mm else 0.0
            else:
                spoil_hat = 0.0
                rain_pen = 0.0

            est_after_weather = p_fresh * (1.0 - spoil_hat) - rain_pen - freight_hat - local_p[r]
            if cfg.use_t3_weather and est_after_weather <= 0.0:
                rejection_reasons.append("WEATHER_SPOILAGE_RISK")
                if cfg.log_traces and len(traces) < cfg.trace_limit:
                    cand_trace.append({"dest": str(dest_mkts[r]), "T1": "PASS", "T2": "PASS", "T3": "PRUNE", "spoil_pct": round(spoil_hat * 100, 1)})
                continue

            # Tool T4: Arrival-Day Forecast & Conformal 80% LCB
            if cfg.use_t4_lcb:
                if budget is not None and calls_used >= budget:
                    rejection_reasons.append("BUDGET_EXHAUSTED")
                    break
                calls_used += 1
                t4_calls += 1
                p_arr_lcb = p_fresh * (1.0 + lcb_ret[r])
                est_net_lcb = p_arr_lcb * (1.0 - spoil_hat) - rain_pen - freight_hat - local_p[r]
            else:
                est_net_lcb = est_after_weather

            if cfg.log_traces and len(traces) < cfg.trace_limit:
                cand_trace.append(
                    {
                        "dest": str(dest_mkts[r]),
                        "T1": "PASS",
                        "T2": "PASS",
                        "T3": "PASS" if cfg.use_t3_weather else "SKIP",
                        "T4_lcb_net": round(float(est_net_lcb), 1),
                    }
                )
            if est_net_lcb > best_score:
                best_score = est_net_lcb
                best_j_idx = r

        if best_j_idx >= 0 and best_score > cfg.safety_margin_inr:
            action = "DISPATCH"
            chosen_dest = str(dest_mkts[best_j_idx])
            d_net = float(real_dnet[best_j_idx])
            open_d0_net = float(real_open_d0[best_j_idx]) if np.isfinite(real_open_d0[best_j_idx]) else np.nan
            is_phantom = bool(d_net < 0.0)
            is_trap = bool(real_trap[best_j_idx])
            is_drop = bool(real_drop[best_j_idx])
            reason_final = "DISPATCH_CLEARED_LCB"
        else:
            action = "REFUSE_PHANTOM_SPREAD"
            chosen_dest = "LOCAL"
            d_net = 0.0
            open_d0_net = 0.0
            is_phantom = False
            is_trap = False
            is_drop = False
            if best_j_idx >= 0:
                reason_final = "ARRIVAL_REVERSION_RISK"
            elif rejection_reasons:
                reason_final = rejection_reasons[0]
            else:
                reason_final = "NO_VIABLE_CANDIDATE"

        ep_records.append(
            {
                "episode_id": ep_id,
                "action": action,
                "chosen_dest": chosen_dest,
                "reason": reason_final,
                "delta_net_inr": d_net,
                "open_d0_delta_net_inr": open_d0_net,
                "is_dispatch": bool(action == "DISPATCH"),
                "is_phantom_loss": is_phantom,
                "is_closed_trap": is_trap,
                "is_arrival_drop": is_drop,
                "tool_calls_total": calls_used,
                "t1_calls": t1_calls,
                "t2_calls": t2_calls,
                "t3_calls": t3_calls,
                "t4_calls": t4_calls,
                "best_est_lcb": float(best_score) if best_j_idx >= 0 else np.nan,
            }
        )
        if cfg.log_traces and len(traces) < cfg.trace_limit:
            traces.append(
                {
                    "episode_id": str(ep_id),
                    "n_screen_shortlist": int(e_idx - s_idx),
                    "tool_calls": {"T1": t1_calls, "T2": t2_calls, "T3": t3_calls, "T4": t4_calls, "total": calls_used},
                    "candidates": cand_trace,
                    "decision": action,
                    "chosen_dest": chosen_dest,
                    "reason": reason_final,
                    "estimated_lcb_net_inr": round(float(best_score), 1) if best_j_idx >= 0 else None,
                    "realized_net_inr": round(d_net, 1),
                }
            )

    return pd.DataFrame(ep_records), traces
