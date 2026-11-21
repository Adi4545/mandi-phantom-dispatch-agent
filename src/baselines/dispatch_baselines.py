"""Matched baselines B0-B6 for evaluating MandiGuard against simpler and upfront comparators."""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.evaluation.payoff_model import PayoffParams, compute_freight_inr, compute_spoilage_fraction


def eval_b1_naive_screen_greedy(
    cand_df: pd.DataFrame,
    hurdle_inr: float = 100.0,
    payoff_params: PayoffParams = PayoffParams(),
) -> pd.DataFrame:
    """B1: Models standard farmer price boards — picks max headline modal(<=7d) - simple Euclid freight > 0."""
    df = cand_df.copy()
    # Naive freight estimate uses 1.2 * Euclidean distance (no OSRM, no vitality/variety/weather/forecast)
    hp_mult = np.where(df["State"] == "Himachal Pradesh", payoff_params.hp_km_mult, 1.0)
    naive_freight = (payoff_params.freight_base + payoff_params.freight_per_km * hp_mult * 1.20 * df["euclid_km"]) * payoff_params.freight_mult
    naive_net = df["screen_dest_price"] - df["local_price"] - naive_freight
    df["naive_est_net"] = naive_net
    df = df.sort_values(["episode_id", "naive_est_net", "dest_market"], ascending=[True, False, True])
    # Select one complete destination row, including missing arrival-day outcomes.
    top = df.drop_duplicates("episode_id", ignore_index=True)

    dispatch_mask = (top["naive_est_net"] > hurdle_inr) & np.isfinite(top["real_delta_net_inr"])
    out = pd.DataFrame(
        {
            "episode_id": top["episode_id"],
            "action": np.where(dispatch_mask, "DISPATCH", "SELL_LOCAL"),
            "chosen_dest": np.where(dispatch_mask, top["dest_market"], "LOCAL"),
            "delta_net_inr": np.where(dispatch_mask, top["real_delta_net_inr"], 0.0),
            "open_d0_delta_net_inr": np.where(dispatch_mask, top["real_open_d0_delta_net_inr"], 0.0),
            "is_dispatch": dispatch_mask,
            "is_phantom_loss": np.where(dispatch_mask, top["real_delta_net_inr"] < 0.0, False),
            "is_closed_trap": np.where(dispatch_mask, top["real_closed_or_no_variety_trap"], False),
            "is_arrival_drop": np.where(dispatch_mask, top["real_arrival_price_dropped"], False),
            "tool_calls_total": 0,
        }
    )
    return out


def eval_b2_fresh_road_greedy(
    cand_df: pd.DataFrame,
    hurdle_inr: float = 100.0,
    payoff_params: PayoffParams = PayoffParams(),
) -> pd.DataFrame:
    """B2: Requires today's exact-variety price (age==0) + OSRM road freight > hurdle; no T1 DOW/vitality, T3, or T4."""
    df = cand_df.copy()
    df = df.sort_values(["episode_id", "screen_spread", "dest_market"], ascending=[True, False, True])
    df["_rk"] = df.groupby("episode_id").cumcount()
    df = df[df["_rk"] < 5].copy()

    freight = np.array(
        [
            compute_freight_inr(str(s), float(d), bool(sd), float(lp), payoff_params, commodity=str(c))
            for s, d, sd, lp, c in zip(df["State"], df["road_km"], df["same_district"], df["local_price"], df["Commodity"])
        ]
    )
    est_net = np.where(df["dest_age_days"] == 0, df["dest_ref_price"] - df["local_price"] - freight, -1e12)
    df["b2_est"] = est_net
    # Uses 1 fresh-check + 1 road lookup on up to 5 candidates = 2 calls per active candidate evaluated
    ranked = df.sort_values(["episode_id", "b2_est", "dest_market"], ascending=[True, False, True])
    top = ranked.drop_duplicates("episode_id", ignore_index=True)
    n_cands = df.groupby("episode_id").size().reindex(top["episode_id"]).to_numpy()
    dispatch_mask = top["b2_est"] > hurdle_inr
    return pd.DataFrame(
        {
            "episode_id": top["episode_id"],
            "action": np.where(dispatch_mask, "DISPATCH", "SELL_LOCAL"),
            "chosen_dest": np.where(dispatch_mask, top["dest_market"], "LOCAL"),
            "delta_net_inr": np.where(dispatch_mask, top["real_delta_net_inr"], 0.0),
            "open_d0_delta_net_inr": np.where(dispatch_mask, top["real_open_d0_delta_net_inr"], 0.0),
            "is_dispatch": dispatch_mask,
            "is_phantom_loss": np.where(dispatch_mask, top["real_delta_net_inr"] < 0.0, False),
            "is_closed_trap": np.where(dispatch_mask, top["real_closed_or_no_variety_trap"], False),
            "is_arrival_drop": np.where(dispatch_mask, top["real_arrival_price_dropped"], False),
            "tool_calls_total": n_cands * 2,
        }
    )


def eval_b3_ml_point_dispatch(
    cand_df: pd.DataFrame,
    safety_margin_inr: float = 150.0,
    payoff_params: PayoffParams = PayoffParams(),
) -> pd.DataFrame:
    """B3: Uses OSRM freight + ML point forecast P50, WITHOUT T1 vitality/weekday guard, T3 weather, or T4 LCB."""
    df = cand_df.copy()
    df = df.sort_values(["episode_id", "screen_spread", "dest_market"], ascending=[True, False, True])
    df["_rk"] = df.groupby("episode_id").cumcount()
    df = df[df["_rk"] < 5].copy()

    freight = np.array(
        [
            compute_freight_inr(str(s), float(d), bool(sd), float(lp), payoff_params, commodity=str(c))
            for s, d, sd, lp, c in zip(df["State"], df["road_km"], df["same_district"], df["local_price"], df["Commodity"])
        ]
    )
    p_base = np.where(np.isfinite(df["dest_ref_price"]) & (df["dest_ref_price"] > 0), df["dest_ref_price"], df["screen_dest_price"])
    p_arr_p50 = p_base * (1.0 + df["pred_ret"])
    est_net = p_arr_p50 - freight - df["local_price"]
    df["b3_est"] = est_net
    ranked = df.sort_values(["episode_id", "b3_est", "dest_market"], ascending=[True, False, True])
    top = ranked.drop_duplicates("episode_id", ignore_index=True)
    n_cands = df.groupby("episode_id").size().reindex(top["episode_id"]).to_numpy()
    dispatch_mask = top["b3_est"] > safety_margin_inr
    return pd.DataFrame(
        {
            "episode_id": top["episode_id"],
            "action": np.where(dispatch_mask, "DISPATCH", "SELL_LOCAL"),
            "chosen_dest": np.where(dispatch_mask, top["dest_market"], "LOCAL"),
            "delta_net_inr": np.where(dispatch_mask, top["real_delta_net_inr"], 0.0),
            "open_d0_delta_net_inr": np.where(dispatch_mask, top["real_open_d0_delta_net_inr"], 0.0),
            "is_dispatch": dispatch_mask,
            "is_phantom_loss": np.where(dispatch_mask, top["real_delta_net_inr"] < 0.0, False),
            "is_closed_trap": np.where(dispatch_mask, top["real_closed_or_no_variety_trap"], False),
            "is_arrival_drop": np.where(dispatch_mask, top["real_arrival_price_dropped"], False),
            "tool_calls_total": n_cands * 2,
        }
    )


def eval_b4_upfront_all_tools(
    cand_df: pd.DataFrame,
    cfg: AgentConfig,
    payoff_params: PayoffParams = PayoffParams(),
) -> pd.DataFrame:
    """B4: Runs ALL 4 tools upfront on every shortlisted candidate (zero pruning), up to budget cap."""
    budget = cfg.max_tool_calls_per_episode
    if budget is None:
        out, _ = evaluate_mandiguard_vectorized(cand_df, cfg, payoff_params)
        cands_per_ep = cand_df.groupby("episode_id").size().clip(upper=cfg.k_max)
        out["tool_calls_total"] = cands_per_ep.reindex(out["episode_id"]).to_numpy() * 4
        return out

    # Under budget B, an upfront polling loop can fully finish at most k_budget = floor(B / 4) candidates
    k_budget = int(budget // 4)
    ep_ids_all = sorted(cand_df["episode_id"].unique())
    cands_per_ep = cand_df.groupby("episode_id").size().clip(upper=cfg.k_max)
    if k_budget <= 0:
        return pd.DataFrame(
            {
                "episode_id": ep_ids_all,
                "action": "REFUSE_PHANTOM_SPREAD",
                "chosen_dest": "LOCAL",
                "delta_net_inr": 0.0,
                "open_d0_delta_net_inr": 0.0,
                "is_dispatch": False,
                "is_phantom_loss": False,
                "is_closed_trap": False,
                "is_arrival_drop": False,
                "tool_calls_total": np.minimum(int(budget), cands_per_ep.reindex(ep_ids_all).to_numpy() * 4),
            }
        )

    sub_cfg = AgentConfig(
        screen_hurdle_inr=cfg.screen_hurdle_inr,
        k_max=min(cfg.k_max, k_budget),
        t1_max_age_days=cfg.t1_max_age_days,
        t1_min_open_prob_14d=cfg.t1_min_open_prob_14d,
        t1_min_dow_open_rate=cfg.t1_min_dow_open_rate,
        safety_margin_inr=cfg.safety_margin_inr,
        max_tool_calls_per_episode=None,
    )
    out, _ = evaluate_mandiguard_vectorized(cand_df, sub_cfg, payoff_params)
    out["tool_calls_total"] = np.minimum(int(budget), cands_per_ep.reindex(out["episode_id"]).to_numpy() * 4)
    return out


def eval_b5_multi_agent_coordinator(
    cand_df: pd.DataFrame,
    safety_margin_inr: float = 150.0,
    k_max: int = 5,
    max_tool_calls: int | None = None,
    payoff_params: PayoffParams = PayoffParams(),
) -> pd.DataFrame:
    """B5: 3-agent role coordinator (ScoutAgent -> LogisticsWeatherAgent -> RiskGateAgent) over discretized 4-bin bus."""
    df = cand_df.sort_values(["episode_id", "screen_spread", "dest_market"], ascending=[True, False, True]).copy()
    df["_rk"] = df.groupby("episode_id").cumcount()
    df = df[df["_rk"] < k_max].copy().reset_index(drop=True)

    ep_ids = df["episode_id"].to_numpy()
    dest_ref = df["dest_ref_price"].to_numpy(dtype=np.float64)
    age_days = df["dest_age_days"].to_numpy(dtype=np.float64)
    open_prob = df["dest_open_prob_14d"].to_numpy(dtype=np.float64)
    dow_open = df["dest_dow_open_rate"].to_numpy(dtype=np.float64)
    states = df["State"].to_numpy()
    comms = df["Commodity"].to_numpy()
    road_km = df["road_km"].to_numpy(dtype=np.float64)
    same_dist = df["same_district"].to_numpy(dtype=bool)
    local_p = df["local_price"].to_numpy(dtype=np.float64)
    truck_hrs = df["truck_hours"].to_numpy(dtype=np.float64)
    fc_tmax = df["route_fc_tmax"].to_numpy(dtype=np.float64)
    fc_rh = df["route_fc_rh"].to_numpy(dtype=np.float64)
    fc_rain = df["route_fc_rain"].to_numpy(dtype=np.float64)
    lcb_ret = df["lcb_ret"].to_numpy(dtype=np.float64)
    dest_mkts = df["dest_market"].to_numpy()
    real_dnet = df["real_delta_net_inr"].to_numpy(dtype=np.float64)
    real_od0 = df["real_open_d0_delta_net_inr"].to_numpy(dtype=np.float64)
    real_trap = df["real_closed_or_no_variety_trap"].to_numpy(dtype=bool)
    real_drop = df["real_arrival_price_dropped"].to_numpy(dtype=bool)

    split_idx = np.flatnonzero(ep_ids[1:] != ep_ids[:-1]) + 1
    starts = np.concatenate(([0], split_idx))
    ends = np.concatenate((split_idx, [len(df)]))

    rows = []
    for s_i, e_i in zip(starts, ends):
        calls = 0
        best_r = -1
        best_bucket_score = -1.0
        for r in range(s_i, e_i):
            if max_tool_calls is not None and calls >= max_tool_calls:
                break
            calls += 1
            p_fresh = dest_ref[r]
            if not (np.isfinite(p_fresh) and age_days[r] <= 3 and open_prob[r] >= 0.50 and dow_open[r] >= 0.35):
                continue
            if max_tool_calls is not None and calls >= max_tool_calls:
                break
            calls += 1
            freight = compute_freight_inr(str(states[r]), float(road_km[r]), bool(same_dist[r]), float(local_p[r]), payoff_params, commodity=str(comms[r]))
            if p_fresh - local_p[r] - freight <= 0:
                continue
            if max_tool_calls is not None and calls >= max_tool_calls:
                break
            calls += 1
            spoil = compute_spoilage_fraction(str(comms[r]), float(truck_hrs[r]), float(fc_tmax[r]), float(fc_rh[r]), float(fc_rain[r]), 0, payoff_params)
            net_after_w = p_fresh * (1.0 - spoil) - freight - local_p[r]
            if net_after_w <= 0:
                continue
            if max_tool_calls is not None and calls >= max_tool_calls:
                break
            calls += 1
            lcb_est = p_fresh * (1.0 + lcb_ret[r]) * (1.0 - spoil) - freight - local_p[r]
            quant_lcb = np.floor(lcb_est / 150.0) * 150.0
            if quant_lcb >= safety_margin_inr and quant_lcb > best_bucket_score:
                best_bucket_score = quant_lcb
                best_r = r

        if best_r >= 0:
            d_net = float(real_dnet[best_r])
            od0 = float(real_od0[best_r]) if np.isfinite(real_od0[best_r]) else np.nan
            rows.append(
                {
                    "episode_id": ep_ids[s_i],
                    "action": "DISPATCH",
                    "chosen_dest": str(dest_mkts[best_r]),
                    "delta_net_inr": d_net,
                    "open_d0_delta_net_inr": od0,
                    "is_dispatch": True,
                    "is_phantom_loss": d_net < 0.0,
                    "is_closed_trap": bool(real_trap[best_r]),
                    "is_arrival_drop": bool(real_drop[best_r]),
                    "tool_calls_total": calls,
                }
            )
        else:
            rows.append(
                {
                    "episode_id": ep_ids[s_i],
                    "action": "REFUSE_PHANTOM_SPREAD",
                    "chosen_dest": "LOCAL",
                    "delta_net_inr": 0.0,
                    "open_d0_delta_net_inr": 0.0,
                    "is_dispatch": False,
                    "is_phantom_loss": False,
                    "is_closed_trap": False,
                    "is_arrival_drop": False,
                    "tool_calls_total": calls,
                }
            )
    return pd.DataFrame(rows)


def eval_b6_heuristic_bucket_router(
    cand_df: pd.DataFrame,
    k_max: int = 5,
    payoff_params: PayoffParams = PayoffParams(),
) -> pd.DataFrame:
    """B6: Coarse verbal/rule bucket heuristic (no ML forecast, no conformal LCB, rough 25% haircut on >200km/hot days)."""
    df = cand_df.sort_values(["episode_id", "screen_spread", "dest_market"], ascending=[True, False, True]).copy()
    df["_rk"] = df.groupby("episode_id").cumcount()
    df = df[df["_rk"] < k_max].copy()

    # Verbal buckets: Reject if age > 1 or open_prob < 0.6; rough cost = 50 + 0.5*road_km; haircut 12% if T>=35 or rain>=25
    freight_rough = (50.0 + 0.55 * df["road_km"]) * payoff_params.freight_mult
    haircut = np.where((df["route_fc_tmax"] >= 35.0) | (df["route_fc_rain"] >= 25.0), 0.12, 0.04) * payoff_params.spoilage_mult
    score = np.where(
        (df["dest_age_days"] <= 1) & (df["dest_open_prob_14d"] >= 0.60),
        df["dest_ref_price"] * (1.0 - haircut) - freight_rough - df["local_price"],
        -1e12,
    )
    df["b6_score"] = score
    ranked = df.sort_values(["episode_id", "b6_score", "dest_market"], ascending=[True, False, True])
    top = ranked.drop_duplicates("episode_id", ignore_index=True)
    n_cands = df.groupby("episode_id").size().reindex(top["episode_id"]).to_numpy()
    dispatch_mask = top["b6_score"] > 200.0
    return pd.DataFrame(
        {
            "episode_id": top["episode_id"],
            "action": np.where(dispatch_mask, "DISPATCH", "SELL_LOCAL"),
            "chosen_dest": np.where(dispatch_mask, top["dest_market"], "LOCAL"),
            "delta_net_inr": np.where(dispatch_mask, top["real_delta_net_inr"], 0.0),
            "open_d0_delta_net_inr": np.where(dispatch_mask, top["real_open_d0_delta_net_inr"], 0.0),
            "is_dispatch": dispatch_mask,
            "is_phantom_loss": np.where(dispatch_mask, top["real_delta_net_inr"] < 0.0, False),
            "is_closed_trap": np.where(dispatch_mask, top["real_closed_or_no_variety_trap"], False),
            "is_arrival_drop": np.where(dispatch_mask, top["real_arrival_price_dropped"], False),
            "tool_calls_total": n_cands * 3,
        }
    )
