"""Step 2 Upgrade: Decade-Scale (2017-2026), Modern AI & ACI Showdown, ZeroCloud, FPO & Spoilage Clock.

Produces:
  - results/exp10_decade_regime_evolution_2017_2026.csv
  - results/exp10b_multiyear_training_scaling.csv
  - results/exp11_modern_ai_and_aci_showdown.csv
  - results/exp12_zerocloud_money_efficient_agent.csv
  - results/exp13_outofbox_fpo_pooling_and_spoilage_clock.csv
  - results/sample_farmer_sms_cards.txt
"""

from __future__ import annotations

import gc
import heapq
import json
import pickle
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.agents.mandiguard_agent import AgentConfig, evaluate_mandiguard_vectorized
from src.baselines.dispatch_baselines import (
    eval_b1_naive_screen_greedy,
    eval_b2_fresh_road_greedy,
    eval_b3_ml_point_dispatch,
    eval_b4_upfront_all_tools,
    eval_b5_multi_agent_coordinator,
)
from src.data.build_dispatch_episodes import build_panel_tables
from src.evaluation.payoff_model import BASE_SPOIL_24H, PayoffParams, compute_freight_inr, compute_spoilage_fraction
from src.evaluation.tail_risk import lower_decile_mean
from src.models.arrival_forecaster import COMMODITY_TO_ID, CausalArrivalForecaster
from src.utils.leakage import load_config


def _minimal_metrics(name: str, pol_df: pd.DataFrame, extra: Dict[str, object] | None = None) -> Dict[str, object]:
    disp = pol_df["is_dispatch"].to_numpy(dtype=bool)
    dnet = pol_df["delta_net_inr"].to_numpy(dtype=np.float64)
    ep_pl = pol_df["is_phantom_loss"].to_numpy(dtype=bool)
    trap = pol_df["is_closed_trap"].to_numpy(dtype=bool)
    calls = pol_df["tool_calls_total"].to_numpy(dtype=np.float64)
    row: Dict[str, object] = {
        "policy": name,
        "n_episodes": int(len(pol_df)),
        "dispatch_rate_pct": round(float(disp.mean() * 100.0), 2),
        "mean_net_gain_inr_qtl": round(float(dnet.mean()), 2),
        "lot_30qtl_gain_inr": round(float(dnet.mean() * 30.0), 1),
        "loss_trip_rate_pct": round(float(ep_pl[disp].mean() * 100.0), 2) if disp.any() else 0.0,
        "closed_trap_rate_pct": round(float(trap[disp].mean() * 100.0), 2) if disp.any() else 0.0,
        "worst_10pct_loss_inr_qtl": round(lower_decile_mean(dnet), 2),
        "live_api_calls_per_query": round(float(calls.mean()), 2),
    }
    if extra:
        row.update(extra)
    return row


def _build_or_load_decade_2017_2023_candidates(root: Path, cfg: Dict) -> pd.DataFrame:
    cache_path = root / "data/interim/candidates_2017_2023.parquet"
    if cache_path.exists():
        print(f"[Cache] Loading {cache_path.name}...", flush=True)
        return pd.read_parquet(cache_path)

    print("[Decade Builder] Constructing causal 2017-2023 corridors with NASA POWER weather...", flush=True)
    panel_dec = pd.read_parquet(root / "data/raw/agmarknet_6state_decade_2017_2026.parquet")
    panel_dec["Arrival_Date"] = pd.to_datetime(panel_dec["Arrival_Date"])
    coords_df = pd.read_parquet(root / "data/processed/mandi_coordinates.parquet")
    corridors_df = pd.read_parquet(root / "data/processed/osrm_corridor_matrix.parquet")
    nasa_raw = pd.read_parquet(root / "data/processed/nasa_power_climate_2017_2023.parquet")

    # Map every distinct 0.1-deg cell from coords_df -> corresponding 0.5-deg NASA POWER cell cleanly
    c01 = coords_df.assign(
        lat01=coords_df["lat"].round(1),
        lon01=coords_df["lon"].round(1),
        lat05=(coords_df["lat"] * 2.0).round() / 2.0,
        lon05=(coords_df["lon"] * 2.0).round() / 2.0,
    )[["lat01", "lon01", "lat05", "lon05"]].drop_duplicates(["lat01", "lon01"])

    nasa_01 = (
        c01.merge(nasa_raw, left_on=["lat05", "lon05"], right_on=["grid_lat", "grid_lon"], how="inner")
        .drop(columns=["grid_lat", "grid_lon", "lat05", "lon05"])
        .rename(columns={"lat01": "grid_lat", "lon01": "grid_lon"})
    )

    hurdle = float(cfg["agent_defaults"]["screen_hurdle_inr_qtl"])
    # Process in 2 chunks to bound peak RAM cleanly (< 2 GB)
    p17 = panel_dec[(panel_dec["Arrival_Date"] >= "2017-01-01") & (panel_dec["Arrival_Date"] <= "2020-01-05")].copy()
    _, c1719 = build_panel_tables(
        raw_df=p17,
        coords_df=coords_df,
        corridors_df=corridors_df,
        weather_df=nasa_01,
        min_date="2017-01-01",
        max_eval_origin_date="2019-12-31",
        max_data_date="2020-01-05",
        grade_explicit=False,
        hurdle_inr=hurdle,
        max_cands_keep=8,
    )
    c1719["episode_id"] = "D1719_" + c1719["episode_id"].astype(str)
    del p17
    gc.collect()

    p20 = panel_dec[(panel_dec["Arrival_Date"] >= "2019-11-15") & (panel_dec["Arrival_Date"] <= "2023-12-31")].copy()
    _, c2023 = build_panel_tables(
        raw_df=p20,
        coords_df=coords_df,
        corridors_df=corridors_df,
        weather_df=nasa_01,
        min_date="2019-11-15",
        max_eval_origin_date="2023-12-26",
        max_data_date="2023-12-31",
        grade_explicit=False,
        hurdle_inr=hurdle,
        max_cands_keep=8,
    )
    c2023 = c2023[pd.to_datetime(c2023["date"]) >= "2020-01-01"].copy()
    c2023["episode_id"] = "D2023_" + c2023["episode_id"].astype(str)
    del p20, panel_dec, nasa_01
    gc.collect()

    c_1723 = pd.concat([c1719, c2023], ignore_index=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    c_1723.to_parquet(cache_path, index=False, compression="zstd")
    print(f"  [Decade Builder] Saved {len(c_1723):,} candidate rows across 2017-2023 ({c_1723['episode_id'].nunique():,} eps).", flush=True)
    return c_1723


def _predict_contextual_ucb_bandit(train_df: pd.DataFrame, eval_df: pd.DataFrame, window_size: int = 400) -> Tuple[np.ndarray, np.ndarray]:
    """Pure online sliding causal UCB/LCB bandit per (Commodity, tau_days) matured <= date t (no ML tree)."""
    seed_stats: Dict[Tuple[str, int], deque] = defaultdict(lambda: deque(maxlen=window_size))
    tr = train_df.dropna(subset=["target_ret"]).sort_values("date")
    for cm, tau, tv in zip(tr["Commodity"], tr["tau_days"], tr["target_ret"]):
        seed_stats[(str(cm), int(tau))].append(float(tv))

    df = eval_df.copy()
    df["_orig_idx"] = np.arange(len(df))
    df["date_dt"] = pd.to_datetime(df["date"])
    df["arr_dt"] = pd.to_datetime(df["arrival_date"])
    df = df.sort_values("date_dt").reset_index(drop=True)

    pred_ret = np.zeros(len(df), dtype=np.float64)
    lcb_ret = np.zeros(len(df), dtype=np.float64)
    pending: Dict[pd.Timestamp, List[Tuple[str, int, float]]] = defaultdict(list)
    heap: List[pd.Timestamp] = []

    for date_t, grp in df.groupby("date_dt", sort=True):
        while heap and heap[0] <= date_t:
            ad = heapq.heappop(heap)
            for cm_k, tau_k, val in pending.pop(ad, []):
                seed_stats[(cm_k, tau_k)].append(val)

        cur_est: Dict[Tuple[str, int], Tuple[float, float]] = {}
        for k, buf in seed_stats.items():
            arr = np.asarray(buf, dtype=np.float64)
            if len(arr) >= 20:
                mu = float(arr.mean())
                sd = float(arr.std())
                cur_est[k] = (mu, mu - 0.8416 * sd)
            else:
                cur_est[k] = (0.0, -0.10)

        idxs = grp.index.to_numpy()
        comms = grp["Commodity"].to_numpy()
        taus = grp["tau_days"].to_numpy()
        arr_dts = grp["arr_dt"].to_numpy()
        tgts = grp["target_ret"].to_numpy()

        for lp, ridx in enumerate(idxs):
            key = (str(comms[lp]), int(taus[lp]))
            mu, lb = cur_est.get(key, (0.0, -0.10))
            pred_ret[ridx] = mu
            lcb_ret[ridx] = lb
            tv = tgts[lp]
            if np.isfinite(tv):
                ad = pd.Timestamp(arr_dts[lp])
                if ad not in pending:
                    heapq.heappush(heap, ad)
                pending[ad].append((key[0], key[1], float(tv)))

    order = np.argsort(df["_orig_idx"].to_numpy())
    return pred_ret[order], lcb_ret[order]


def _eval_split_top2_portfolio(
    cand_df: pd.DataFrame, safety_margin_inr: float, k_max: int = 5, payoff_params: PayoffParams = PayoffParams()
) -> pd.DataFrame:
    """Out-of-the-Box Top-2 Split-Lot Portfolio: splits truck 50/50 across top-2 LCB-cleared mandis."""
    df = cand_df.sort_values(["episode_id", "screen_spread", "dest_market"], ascending=[True, False, True]).copy()
    df["_rk"] = df.groupby("episode_id").cumcount()
    df = df[df["_rk"] < k_max].copy().reset_index(drop=True)

    ep_ids = df["episode_id"].to_numpy()
    local_p = df["local_price"].to_numpy(dtype=np.float64)
    dest_ref = df["dest_ref_price"].to_numpy(dtype=np.float64)
    age_days = df["dest_age_days"].to_numpy(dtype=np.float64)
    open_prob = df["dest_open_prob_14d"].to_numpy(dtype=np.float64)
    dow_open = df["dest_dow_open_rate"].to_numpy(dtype=np.float64)
    intra = df["dest_intra_spread_14d"].to_numpy(dtype=np.float64)
    states = df["State"].to_numpy()
    comms = df["Commodity"].to_numpy()
    road_km = df["road_km"].to_numpy(dtype=np.float64)
    same_dist = df["same_district"].to_numpy(dtype=bool)
    truck_hrs = df["truck_hours"].to_numpy(dtype=np.float64)
    fc_tmax = df["route_fc_tmax"].to_numpy(dtype=np.float64)
    fc_rh = df["route_fc_rh"].to_numpy(dtype=np.float64)
    fc_rain = df["route_fc_rain"].to_numpy(dtype=np.float64)
    lcb_ret = df["lcb_ret"].to_numpy(dtype=np.float64)
    real_dnet = df["real_delta_net_inr"].to_numpy(dtype=np.float64)
    real_trap = df["real_closed_or_no_variety_trap"].to_numpy(dtype=bool)

    split_idx = np.flatnonzero(ep_ids[1:] != ep_ids[:-1]) + 1
    starts = np.concatenate(([0], split_idx))
    ends = np.concatenate((split_idx, [len(df)]))

    rows = []
    for s_i, e_i in zip(starts, ends):
        calls = 0
        passed: List[Tuple[float, int]] = []
        for r in range(s_i, e_i):
            calls += 1
            pf = dest_ref[r]
            if not (np.isfinite(pf) and pf > 0 and age_days[r] <= 3 and open_prob[r] >= 0.50 and dow_open[r] >= 0.35):
                continue
            calls += 1
            fr = compute_freight_inr(str(states[r]), float(road_km[r]), bool(same_dist[r]), float(local_p[r]), payoff_params, commodity=str(comms[r]))
            if pf - local_p[r] - fr <= 0:
                continue
            calls += 1
            sp = compute_spoilage_fraction(str(comms[r]), float(truck_hrs[r]), float(fc_tmax[r]), float(fc_rh[r]), float(fc_rain[r]), 0, payoff_params)
            rpen = (0.50 * pf * float(np.nan_to_num(intra[r], nan=0.10))) if fc_rain[r] >= payoff_params.heavy_rain_mm else 0.0
            if pf * (1.0 - sp) - rpen - fr - local_p[r] <= 0:
                continue
            calls += 1
            est_lcb = pf * (1.0 + lcb_ret[r]) * (1.0 - sp) - rpen - fr - local_p[r]
            if est_lcb > safety_margin_inr:
                passed.append((float(est_lcb), r))

        if len(passed) >= 2:
            passed.sort(reverse=True)
            r1, r2 = passed[0][1], passed[1][1]
            dn = 0.5 * float(real_dnet[r1]) + 0.5 * float(real_dnet[r2])
            trp = bool(real_trap[r1] and real_trap[r2])
            rows.append(
                {
                    "episode_id": ep_ids[s_i],
                    "is_dispatch": True,
                    "delta_net_inr": dn,
                    "is_phantom_loss": dn < 0.0,
                    "is_closed_trap": trp,
                    "tool_calls_total": calls,
                }
            )
        elif len(passed) == 1:
            r1 = passed[0][1]
            dn = float(real_dnet[r1])
            rows.append(
                {
                    "episode_id": ep_ids[s_i],
                    "is_dispatch": True,
                    "delta_net_inr": dn,
                    "is_phantom_loss": dn < 0.0,
                    "is_closed_trap": bool(real_trap[r1]),
                    "tool_calls_total": calls,
                }
            )
        else:
            rows.append(
                {
                    "episode_id": ep_ids[s_i],
                    "is_dispatch": False,
                    "delta_net_inr": 0.0,
                    "is_phantom_loss": False,
                    "is_closed_trap": False,
                    "tool_calls_total": calls,
                }
            )
    return pd.DataFrame(rows)


def _exact_vectorized_freight_shift(cand_df: pd.DataFrame, freight_mult: float) -> pd.DataFrame:
    """Exact O(N) vectorized update of real_delta_net_inr for any freight_mult (verified vs compute_realized_dispatch_outcome)."""
    df = cand_df.copy()
    hp_m = np.where(df["State"].to_numpy() == "Himachal Pradesh", 1.45, 1.0)
    base_road_f = 35.0 + 0.45 * hp_m * df["road_km"].to_numpy(dtype=np.float64)
    divert_mask = (
        (~np.isfinite(df["dest_modal_d0"]))
        & (~np.isfinite(df["dest_modal_d1"]))
        & (~np.isfinite(df["dest_modal_d2"]))
        & (~(np.isfinite(df["dest_any_var_min_d0"]) & (df["dest_any_var_min_d0"] > 0)))
    )
    mult = np.where(divert_mask, 1.5, 1.0)
    df["real_delta_net_inr"] = df["real_delta_net_inr"].to_numpy(dtype=np.float64) - mult * (freight_mult - 1.0) * base_road_f
    return df


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root)
    splits = cfg["temporal_splits"]
    seed = int(cfg["master_seed"])
    hurdle = float(cfg["agent_defaults"]["screen_hurdle_inr_qtl"])
    k_max = int(cfg["agent_defaults"]["k_max_candidates"])
    res_dir = root / "results"
    res_dir.mkdir(parents=True, exist_ok=True)

    cal_info = json.loads((root / "configs/frozen_calibration.json").read_text())
    frozen_margin = float(cal_info["frozen_safety_margin_inr"])

    # Load 2024-2026 candidates cleanly
    cand_2426 = pd.read_parquet(root / "data/processed/candidates_6state.parquet")
    cand_2426["date_dt"] = pd.to_datetime(cand_2426["date"])
    cand_2426["arr_dt"] = pd.to_datetime(cand_2426["arrival_date"])
    train_24 = cand_2426[(cand_2426["date_dt"] <= splits["train_end"]) & (cand_2426["arr_dt"] <= splits["train_end"])].copy()
    val_df = cand_2426[(cand_2426["date_dt"] >= splits["val_start"]) & (cand_2426["date_dt"] <= splits["val_end"]) & (cand_2426["arr_dt"] <= splits["val_end"])].copy()
    cand_2526 = cand_2426[cand_2426["date_dt"] >= splits["val_start"]].copy()

    # Load frozen 2024 forecaster
    with open(root / "data/interim/forecaster_2024.pkl", "rb") as f:
        fc_2024 = pickle.load(f)
    p2526, l2526 = fc_2024.predict_point_and_causal_lcb(cand_2526)
    cand_2526["pred_ret"] = p2526
    cand_2526["lcb_ret"] = l2526
    hold_cands = cand_2526[(cand_2526["date_dt"] >= splits["test_start"]) & (cand_2526["arr_dt"] <= splits["test_end"])].copy()
    val_scored = cand_2526[(cand_2526["date_dt"] >= splits["val_start"]) & (cand_2526["date_dt"] <= splits["val_end"]) & (cand_2526["arr_dt"] <= splits["val_end"])].copy()

    # -------------------- BUILD 2017-2023 CANDIDATES --------------------
    cand_1723 = _build_or_load_decade_2017_2023_candidates(root, cfg)
    cand_1723["date_dt"] = pd.to_datetime(cand_1723["date"])
    cand_1723["arr_dt"] = pd.to_datetime(cand_1723["arrival_date"])

    # -------------------- EXP 10: 10-YEAR DECADE REGIMES (2017-2026) --------------------
    print("[Exp 10] Evaluating 6 Macro-Economic & Climate Regimes across 2017-2026...", flush=True)
    regimes = [
        ("2017H2_GST_Transition", "2017-07-01", "2017-12-31", ("2017-01-01", "2017-06-30"), "2017H1"),
        ("2018-2019_PreCOVID", "2018-01-01", "2019-12-31", ("2017-01-01", "2017-12-31"), "2017"),
        ("2020-2021_COVID_Shock", "2020-01-01", "2021-12-31", ("2017-01-01", "2019-12-31"), "2017-2019"),
        ("2022-2023_Inflation_ExportCurb", "2022-01-01", "2023-12-26", ("2017-01-01", "2021-12-31"), "2017-2021"),
        ("2024_ElNino_Heatwave", "2024-01-01", "2024-12-31", ("2017-01-01", "2023-12-26"), "2017-2023"),
        ("2025-2026_Holdout_Benchmark", "2025-06-01", "2026-04-08", None, "2024"),
    ]
    exp10_rows = []
    for reg_name, d0, d1, train_win, tr_label in regimes:
        if int(d0[:4]) <= 2023:
            eval_sub = cand_1723[(cand_1723["date_dt"] >= d0) & (cand_1723["date_dt"] <= d1) & (cand_1723["arr_dt"] <= d1)].copy()
        elif d0.startswith("2024"):
            eval_sub = train_24.copy()
        else:
            eval_sub = hold_cands.copy()

        b1_r = eval_b1_naive_screen_greedy(eval_sub, hurdle_inr=hurdle)
        b2_r = eval_b2_fresh_road_greedy(eval_sub, hurdle_inr=hurdle)

        if train_win is not None:
            tw0, tw1 = train_win
            tr_hist = cand_1723[(cand_1723["date_dt"] >= tw0) & (cand_1723["arr_dt"] <= tw1)].copy()
            fc_exp = CausalArrivalForecaster(seed=seed).fit(tr_hist)
            pr, lr = fc_exp.predict_point_and_causal_lcb(eval_sub)
            eval_sub["pred_ret"], eval_sub["lcb_ret"] = pr, lr
        mg_r, _ = evaluate_mandiguard_vectorized(eval_sub, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin))

        spread_mean = round(float(eval_sub.groupby("episode_id")["screen_spread"].max().mean()), 1)
        for pname, pdf in [("B1_NaiveScreen", b1_r), ("B2_FreshRoad", b2_r), ("MandiGuard_Expanding", mg_r)]:
            exp10_rows.append(
                _minimal_metrics(
                    pname,
                    pdf,
                    {
                        "regime": reg_name,
                        "train_window": tr_label if pname == "MandiGuard_Expanding" else "Rule",
                        "mean_screen_spread_inr": spread_mean,
                    },
                )
            )
    exp10_df = pd.DataFrame(exp10_rows)
    exp10_df.to_csv(res_dir / "exp10_decade_regime_evolution_2017_2026.csv", index=False)
    print(exp10_df.to_string(index=False))

    # -------------------- EXP 10b: 1-YR vs 3-YR vs 8-YR TRAINING HORIZON --------------------
    print("[Exp 10b] Testing 1-Year vs 3-Year vs 8-Year Training Horizon on Holdout_2025_2026...", flush=True)
    tr_2224 = pd.concat([cand_1723[cand_1723["date_dt"] >= "2022-01-01"], train_24], ignore_index=True)
    tr_1724 = pd.concat([cand_1723, train_24], ignore_index=True)
    exp10b_rows = []
    for label, tr_set, fc_obj in [
        ("MandiGuard_1Yr (2024 only)", train_24, fc_2024),
        ("MandiGuard_3Yr (2022-2024)", tr_2224, None),
        ("MandiGuard_8Yr (2017-2024)", tr_1724, None),
    ]:
        if fc_obj is None:
            fc_obj = CausalArrivalForecaster(seed=seed).fit(tr_set)
            p_m, l_m = fc_obj.predict_point_and_causal_lcb(cand_2526)
            sub_h = hold_cands.copy()
            # Map predictions via index alignment cleanly
            pred_map = pd.DataFrame({"episode_id": cand_2526["episode_id"], "dest_market": cand_2526["dest_market"], "pred_ret": p_m, "lcb_ret": l_m})
            sub_h = sub_h.drop(columns=["pred_ret", "lcb_ret"]).merge(pred_map, on=["episode_id", "dest_market"], how="left")
        else:
            sub_h = hold_cands
        mg_m, _ = evaluate_mandiguard_vectorized(sub_h, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin))
        exp10b_rows.append(_minimal_metrics(label, mg_m, {"train_rows": int(len(tr_set))}))
    del tr_2224, tr_1724, cand_1723
    gc.collect()
    exp10b_df = pd.DataFrame(exp10b_rows)
    exp10b_df.to_csv(res_dir / "exp10b_multiyear_training_scaling.csv", index=False)
    print(exp10b_df.to_string(index=False))

    # -------------------- EXP 11: MODERN AI & ACI SHOWDOWN --------------------
    print("[Exp 11] Running Modern AI Showdown (Quantile GBDT, Deep MLP, ExtraTrees, UCB Bandit, ACI)...", flush=True)
    cand_ap = pd.read_parquet(root / "data/processed/candidates_hp_apple_grade.parquet")
    cand_ap["date_dt"] = pd.to_datetime(cand_ap["date"])
    cand_ap["arr_dt"] = pd.to_datetime(cand_ap["arrival_date"])
    ap_mask = (cand_ap["date_dt"] >= splits["apple_test_start"]) & (cand_ap["date_dt"] <= "2026-08-27") & (cand_ap["arr_dt"] <= splits["apple_test_end"])

    exp11_rows = []
    # Reference Standard MandiGuard + ACI on both 6-State Holdout and HP Apple 2026
    aci_alphas_check = {}
    for bench_name, full_stream, eval_mask in [
        ("Holdout_6State_2025_2026", cand_2526, (cand_2526["date_dt"] >= splits["test_start"]) & (cand_2526["arr_dt"] <= splits["test_end"])),
        ("HP_Apple_Grade_2026", cand_ap, ap_mask),
    ]:
        # Standard HGBR Static Conformal
        p_st, l_st = fc_2024.predict_point_and_causal_lcb(full_stream, adaptive_gamma=None)
        ev_df = full_stream.loc[eval_mask].copy()
        ev_df["pred_ret"] = p_st[eval_mask]
        ev_df["lcb_ret"] = l_st[eval_mask]
        mg_st, _ = evaluate_mandiguard_vectorized(ev_df, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin))
        exp11_rows.append(_minimal_metrics("MandiGuard_Standard", mg_st, {"benchmark": bench_name}))

        # MandiGuard_ACI (Gibbs & Candes 2021)
        p_aci, l_aci = fc_2024.predict_point_and_causal_lcb(full_stream, adaptive_gamma=0.005)
        aci_alphas_check[bench_name] = dict(fc_2024.last_aci_alpha_by_comm)
        ev_df["pred_ret"] = p_aci[eval_mask]
        ev_df["lcb_ret"] = l_aci[eval_mask]
        mg_aci, _ = evaluate_mandiguard_vectorized(ev_df, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin))
        exp11_rows.append(_minimal_metrics("MandiGuard_ACI_NeurIPS21", mg_aci, {"benchmark": bench_name}))

        # Pure Online Contextual UCB Bandit
        p_ucb, l_ucb = _predict_contextual_ucb_bandit(train_24, full_stream)
        ev_df["pred_ret"] = p_ucb[eval_mask]
        ev_df["lcb_ret"] = l_ucb[eval_mask]
        mg_ucb, _ = evaluate_mandiguard_vectorized(ev_df, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin))
        exp11_rows.append(_minimal_metrics("Contextual_UCB_Bandit", mg_ucb, {"benchmark": bench_name}))

    # Modern neural / tree / direct-quantile models fit strictly on Train_2024
    for m_label, m_kind in [
        ("Direct_Quantile_GBDT_Q20", "quantile_q20"),
        ("Deep_MLP_Conformal", "mlp"),
        ("ExtraTrees_Conformal", "extratrees"),
    ]:
        print(f"  Fitting {m_label} strictly on Train_2024...", flush=True)
        fc_mod = CausalArrivalForecaster(seed=seed, model_kind=m_kind).fit(train_24)
        for bench_name, full_stream, eval_mask in [
            ("Holdout_6State_2025_2026", cand_2526, (cand_2526["date_dt"] >= splits["test_start"]) & (cand_2526["arr_dt"] <= splits["test_end"])),
            ("HP_Apple_Grade_2026", cand_ap, ap_mask),
        ]:
            pm, lm = fc_mod.predict_point_and_causal_lcb(full_stream)
            ev_df = full_stream.loc[eval_mask].copy()
            ev_df["pred_ret"] = pm[eval_mask]
            ev_df["lcb_ret"] = lm[eval_mask]
            mg_mod, _ = evaluate_mandiguard_vectorized(ev_df, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin))
            exp11_rows.append(_minimal_metrics(m_label, mg_mod, {"benchmark": bench_name}))

    # Persist ACI final alphas so tests verify [0.02, 0.45] bounds cleanly
    (res_dir / "aci_diagnostics.json").write_text(json.dumps(aci_alphas_check, indent=2))
    exp11_df = pd.DataFrame(exp11_rows)
    exp11_df.to_csv(res_dir / "exp11_modern_ai_and_aci_showdown.csv", index=False)
    print(exp11_df.to_string(index=False))

    # -------------------- EXP 12: ZEROCLOUD & SATISFICING MONEY-EFFICIENT AGENT --------------------
    print("[Exp 12] Calibrating Satisficing Threshold on Val_2025H1 & Testing MandiGuard-ZeroCloud...", flush=True)
    # Calibrate satisficing hurdle strictly on Val_2025H1 (pick smallest threshold retaining >=98% of full ZeroCloud Mean dNet)
    val_zc_full, _ = evaluate_mandiguard_vectorized(val_scored, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin, zerocloud_mode=True))
    target_val_dnet = float(val_zc_full["delta_net_inr"].mean())
    chosen_sat = 250.0
    for sat_cand in [150.0, 200.0, 250.0, 300.0, 400.0]:
        v_df, _ = evaluate_mandiguard_vectorized(
            val_scored,
            AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin, zerocloud_mode=True, early_exit_satisficing_inr=sat_cand),
        )
        if float(v_df["delta_net_inr"].mean()) >= 0.985 * target_val_dnet:
            chosen_sat = sat_cand
            break
    print(f"  Val_2025H1 frozen ZeroCloud satisficing hurdle = Rs {chosen_sat:.0f}/qtl (target Val dNet >= {0.985*target_val_dnet:.1f})", flush=True)

    exp12_rows = []
    # Measure latency + API call rupee cost (at Rs 0.05/call standard cloud map/weather/inference query vs ZeroCloud)
    t_b4 = time.perf_counter()
    b4_h = eval_b4_upfront_all_tools(hold_cands, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin))
    dt_b4 = (time.perf_counter() - t_b4) * 1000.0 / len(b4_h)

    t_b5 = time.perf_counter()
    b5_h = eval_b5_multi_agent_coordinator(hold_cands, safety_margin_inr=frozen_margin, k_max=k_max)
    dt_b5 = (time.perf_counter() - t_b5) * 1000.0 / len(b5_h)

    t_mg = time.perf_counter()
    mg_h, _ = evaluate_mandiguard_vectorized(hold_cands, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin))
    dt_mg = (time.perf_counter() - t_mg) * 1000.0 / len(mg_h)

    t_zcf = time.perf_counter()
    zcf_h, _ = evaluate_mandiguard_vectorized(hold_cands, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin, zerocloud_mode=True))
    dt_zcf = (time.perf_counter() - t_zcf) * 1000.0 / len(zcf_h)

    t_zcs = time.perf_counter()
    zcs_h, _ = evaluate_mandiguard_vectorized(
        hold_cands,
        AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin, zerocloud_mode=True, early_exit_satisficing_inr=chosen_sat),
    )
    dt_zcs = (time.perf_counter() - t_zcs) * 1000.0 / len(zcs_h)

    for lbl, pdf, ms_q, note in [
        ("B4_UpfrontAllTools", b4_h, dt_b4, "All external APIs upfront"),
        ("B5_MultiAgentCoordinator", b5_h, dt_b5, "3 LLM/Agent roles over quantized bus"),
        ("MandiGuard_Standard", mg_h, dt_mg, "Full sequential cascade (live T1..T4)"),
        ("MandiGuard_ZeroCloud_Full", zcf_h, dt_zcf, "Cached T2 OSRM + Edge CPU T4 (only live T1+T3)"),
        ("MandiGuard_ZeroCloud_Satisficing", zcs_h, dt_zcs, f"Cached T2 + Edge T4 + Val early-exit >= Rs {chosen_sat:.0f}"),
    ]:
        calls_m = float(pdf["tool_calls_total"].mean())
        cost_10k_inr = calls_m * 0.05 * 10000.0  # Rs 0.05 per external API call across 10,000 farmer advisories
        exp12_rows.append(
            _minimal_metrics(
                lbl,
                pdf,
                {
                    "cpu_ms_per_query": round(ms_q, 3),
                    "api_cost_per_10k_queries_inr": round(cost_10k_inr, 0),
                    "val_sat_hurdle_inr": chosen_sat if "Satisficing" in lbl else np.nan,
                    "architecture_note": note,
                },
            )
        )
    exp12_df = pd.DataFrame(exp12_rows)
    exp12_df.to_csv(res_dir / "exp12_zerocloud_money_efficient_agent.csv", index=False)
    print(exp12_df.to_string(index=False))

    # -------------------- EXP 13: OUT-OF-THE-BOX FPO POOLING, SPLIT-LOT & SPOILAGE CLOCK --------------------
    print("[Exp 13] Computing FPO Shared-Truck Pooling, Top-2 Split Portfolio & Biological Spoilage Clock...", flush=True)
    exp13_rows = []
    for scale_lbl, fm in [
        ("Marginal_Solo_10qtl_1.60xFreight", 1.60),
        ("Standard_MiniTruck_30qtl_1.00xFreight", 1.00),
        ("Cooperative_FPO_90qtl_0.70xFreight", 0.70),
    ]:
        pp = PayoffParams(freight_mult=fm, use_state_statutory_fees=True)
        hc_sc = hold_cands if fm == 1.00 else _exact_vectorized_freight_shift(hold_cands, fm)
        b1_sc = eval_b1_naive_screen_greedy(hc_sc, hurdle_inr=hurdle, payoff_params=pp)
        mg_sc, _ = evaluate_mandiguard_vectorized(hc_sc, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin), payoff_params=pp)
        exp13_rows.append(_minimal_metrics(f"B1_{scale_lbl}", b1_sc, {"experiment": "Truck_Pooling_Scale"}))
        exp13_rows.append(_minimal_metrics(f"MandiGuard_{scale_lbl}", mg_sc, {"experiment": "Truck_Pooling_Scale"}))

    # Top-2 Split-Lot Portfolio Diversification
    split_df = _eval_split_top2_portfolio(hold_cands, safety_margin_inr=frozen_margin, k_max=k_max)
    exp13_rows.append(_minimal_metrics("Split_Top2_Portfolio_StandardFreight", split_df, {"experiment": "Split_Lot_Diversification"}))
    pd.DataFrame(exp13_rows).to_csv(res_dir / "exp13_outofbox_fpo_pooling_and_spoilage_clock.csv", index=False)

    # Biological Spoilage Clock (dedicated zero-NaN table: max safe hours before Q10 decay hits 15% loss)
    clock_rows = []
    target_frac = 0.15  # Rs 300/qtl on Rs 2,000/qtl benchmark lot
    for comm, b_24h in BASE_SPOIL_24H.items():
        for temp_c, season in [(20.0, "20C_Winter"), (32.0, "32C_SpringMonsoon"), (42.0, "42C_PeakSummer")]:
            q10_rate = 2.0 ** ((temp_c - 20.0) / 10.0)
            loss_per_hour = (b_24h / 24.0) * q10_rate
            safe_hrs = target_frac / loss_per_hour
            clock_rows.append(
                {
                    "commodity": comm,
                    "scenario": season,
                    "temp_c": temp_c,
                    "nabcons_base_24h_20c_pct": round(b_24h * 100.0, 2),
                    "daily_decay_rate_pct": round(loss_per_hour * 24.0 * 100.0, 2),
                    "safe_transit_hours_to_15pct_loss": round(safe_hrs, 1),
                }
            )
    pd.DataFrame(clock_rows).to_csv(res_dir / "exp13b_biological_spoilage_clock.csv", index=False)
    _write_farmer_sms_cards(res_dir, hold_cands, mg_h, exp13_rows)
    print("=== ALL CREATIVE DECADE, MODERN AI, ZEROCLOUD, FPO & SPOILAGE CLOCK EXPERIMENTS COMPLETE ===", flush=True)


def _clean_sms_mkt(name: object, max_len: int = 12) -> str:
    txt = str(name).split("(")[0].strip()
    return txt[:max_len].strip()


def _write_farmer_sms_cards(res_dir: Path, hold_cands: pd.DataFrame, mg_h: pd.DataFrame, exp13_rows: List[Dict]) -> None:
    st_abbr = {
        "Maharashtra": "MH",
        "Madhya Pradesh": "MP",
        "Uttar Pradesh": "UP",
        "Karnataka": "KA",
        "Gujarat": "GJ",
        "Himachal Pradesh": "HP",
    }
    mg_joined = mg_h.merge(
        hold_cands[["episode_id", "State", "Commodity", "origin_market", "dest_market", "road_km", "truck_hours", "local_price", "screen_spread", "route_fc_tmax", "route_fc_rain"]].drop_duplicates(["episode_id", "dest_market"]),
        left_on=["episode_id", "chosen_dest"],
        right_on=["episode_id", "dest_market"],
        how="left",
    )
    ok_pool = mg_joined[(mg_joined["action"] == "DISPATCH") & (mg_joined["State"] == "Maharashtra") & (mg_joined["Commodity"] == "Onion") & (mg_joined["delta_net_inr"] > 200)]
    if len(ok_pool) == 0:
        ok_pool = mg_joined[(mg_joined["action"] == "DISPATCH") & (mg_joined["delta_net_inr"] > 100)]
    ok_ex = ok_pool.iloc[0]

    rain_pool = hold_cands[(hold_cands["State"] == "Karnataka") & (hold_cands["Commodity"] == "Tomato") & (hold_cands["route_fc_rain"] >= 35.0)].merge(
        mg_h[mg_h["action"] != "DISPATCH"][["episode_id", "reason"]], on="episode_id", how="inner"
    )
    if len(rain_pool) == 0:
        rain_pool = hold_cands[hold_cands["route_fc_rain"] >= 35.0].merge(
            mg_h[mg_h["action"] != "DISPATCH"][["episode_id", "reason"]], on="episode_id", how="inner"
        )
    rain_cand = rain_pool.iloc[0]

    stale_pool = hold_cands[(hold_cands["State"] == "Madhya Pradesh") & (hold_cands["dest_age_days"] > 3) & (hold_cands["screen_spread"] > 400)].merge(
        mg_h[mg_h["action"] != "DISPATCH"][["episode_id", "reason"]], on="episode_id", how="inner"
    )
    if len(stale_pool) == 0:
        stale_pool = hold_cands[(hold_cands["dest_age_days"] > 3) & (hold_cands["screen_spread"] > 300)].merge(
            mg_h[mg_h["action"] != "DISPATCH"][["episode_id", "reason"]], on="episode_id", how="inner"
        )
    stale_cand = stale_pool.iloc[0]

    fpo_row = [r for r in exp13_rows if r["policy"] == "MandiGuard_Cooperative_FPO_90qtl_0.70xFreight"][0]
    std_row = [r for r in exp13_rows if r["policy"] == "MandiGuard_Standard_MiniTruck_30qtl_1.00xFreight"][0]
    fpo_gain = fpo_row["mean_net_gain_inr_qtl"] - std_row["mean_net_gain_inr_qtl"]

    sms_lines = [
        f"[MandiGuard DISPATCH] {st_abbr[ok_ex['State']]} {ok_ex['Commodity']}: {_clean_sms_mkt(ok_ex['origin_market'])}->{_clean_sms_mkt(ok_ex['chosen_dest'])} ({ok_ex['road_km']:.0f}km/{ok_ex['truck_hours']:.1f}h). LCB +Rs{ok_ex['best_est_lcb']:.0f}, Real +Rs{ok_ex['delta_net_inr']:.0f}/qtl!",
        f"[MandiGuard STOP] {st_abbr[stale_cand['State']]} {stale_cand['Commodity']} at {_clean_sms_mkt(stale_cand['origin_market'])}: SKIP {_clean_sms_mkt(stale_cand['dest_market'])} (+Rs{stale_cand['screen_spread']:.0f} screen). {stale_cand['reason']}. Sell local!",
        f"[MandiGuard RAIN STOP] {st_abbr[rain_cand['State']]} {rain_cand['Commodity']} at {_clean_sms_mkt(rain_cand['origin_market'])}: SKIP {_clean_sms_mkt(rain_cand['dest_market'])}. Rain {rain_cand['route_fc_rain']:.0f}mm -> spoil risk. Sell local!",
        f"[MandiGuard FPO POOL] 90qtl shared FPO truck (0.70x freight) raises mean net gain +Rs{fpo_gain:.1f}/qtl over 30qtl solo (Rs{fpo_row['mean_net_gain_inr_qtl']:.1f}/qtl vs Rs{std_row['mean_net_gain_inr_qtl']:.1f})!",
    ]
    sms_lines = [ln[:160] for ln in sms_lines]
    (res_dir / "sample_farmer_sms_cards.txt").write_text("\n".join(sms_lines) + "\n")


def regenerate_sms_only(root: Path) -> None:
    cfg = load_config(root)
    splits = cfg["temporal_splits"]
    hurdle = float(cfg["agent_defaults"]["screen_hurdle_inr_qtl"])
    k_max = int(cfg["agent_defaults"]["k_max_candidates"])
    frozen_margin = float(json.loads((root / "configs/frozen_calibration.json").read_text())["frozen_safety_margin_inr"])
    res_dir = root / "results"
    cand_2426 = pd.read_parquet(root / "data/processed/candidates_6state.parquet")
    cand_2426["date_dt"] = pd.to_datetime(cand_2426["date"])
    cand_2426["arr_dt"] = pd.to_datetime(cand_2426["arrival_date"])
    cand_2526 = cand_2426[cand_2426["date_dt"] >= splits["val_start"]].copy()
    with open(root / "data/interim/forecaster_2024.pkl", "rb") as f:
        fc_2024 = pickle.load(f)
    p2526, l2526 = fc_2024.predict_point_and_causal_lcb(cand_2526)
    cand_2526["pred_ret"], cand_2526["lcb_ret"] = p2526, l2526
    hold_cands = cand_2526[(cand_2526["date_dt"] >= splits["test_start"]) & (cand_2526["arr_dt"] <= splits["test_end"])].copy()
    mg_h, _ = evaluate_mandiguard_vectorized(hold_cands, AgentConfig(screen_hurdle_inr=hurdle, k_max=k_max, safety_margin_inr=frozen_margin))
    exp13_rows = pd.read_csv(res_dir / "exp13_outofbox_fpo_pooling_and_spoilage_clock.csv").to_dict("records")
    _write_farmer_sms_cards(res_dir, hold_cands, mg_h, exp13_rows)


if __name__ == "__main__":
    import sys

    if "--only-sms" in sys.argv:
        regenerate_sms_only(Path(__file__).resolve().parents[2])
    else:
        main()

