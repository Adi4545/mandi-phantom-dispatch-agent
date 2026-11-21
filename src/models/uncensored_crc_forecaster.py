"""Uncensored Execution Forecaster & Validation-Calibrated Conformal Risk Control (Stage II).

Addresses two verified pathologies of standard mandi price models (`Exp 16`):
  1. Censored-Arrival Survivorship Bias: Drops no missing-d0 rows during training; fits on
     uncensored execution return `r_exec = (real_delta_net_inr - static_net) / dest_ref_price`
     strictly after settlement (`arrival_date + 2d <= train_cutoff`), jointly estimating both
     expected return `mu_hat` and episode-loss probability `p_loss`.
  2. Heteroscedastic Coverage Illusion: Replaces a single additive cushion with an
     empirically calibrated price-scaled risk gate. The ratio is inspired by
     conformal risk control (Angelopoulos et al., 2024) but does not satisfy
     Theorem 1: prices are not exchangeable, and the dispatch denominator depends on lambda.
         Score = mu_hat(x) - lambda_star * local_price * p_loss(x),
     with `lambda_star` calibrated strictly on `Val_2025H1` to satisfy `(n_loss + 1)/(n_disp + 1) <= beta`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

from src.evaluation.payoff_model import BASE_SPOIL_24H, PayoffParams
from src.models.arrival_forecaster import FEATURE_COLS

EXT_FEATURE_COLS = list(FEATURE_COLS) + ["static_margin_ratio"]


@dataclass
class CRCConfig:
    screen_hurdle_inr: float = 100.0
    k_max: int = 5
    safety_margin_inr: float = 50.0
    beta_target: float = 0.095
    use_euclid_step0_sort: bool = True
    thin_grade_aware_t1: bool = True
    t1_max_age_days: int = 3
    t1_min_open_prob_14d: float = 0.50
    t1_min_dow_open_rate: float = 0.35
    fresh0_min_open_prob_14d: float = 0.20
    fresh0_min_dow_open_rate: float = 0.25


def compute_vectorized_static_payoff(
    df: pd.DataFrame,
    params: PayoffParams = PayoffParams(),
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute (f_hat, spoil_hat, rain_pen, static_net, euclid_freight_approx) cleanly in vectorized NumPy."""
    states = df["State"].astype(str)
    comms = df["Commodity"].astype(str)
    road_km = df["road_km"].to_numpy(dtype=np.float64)
    euclid_km = df["euclid_km"].to_numpy(dtype=np.float64)
    truck_hrs = df["truck_hours"].to_numpy(dtype=np.float64)
    same_dist = df["same_district"].to_numpy(dtype=bool)
    local_p = df["local_price"].to_numpy(dtype=np.float64)
    ref_p = df["dest_ref_price"].to_numpy(dtype=np.float64)
    tmax = df["route_fc_tmax"].to_numpy(dtype=np.float64)
    rh = df["route_fc_rh"].to_numpy(dtype=np.float64)
    rain = df["route_fc_rain"].to_numpy(dtype=np.float64)
    intra = df["dest_intra_spread_14d"].fillna(0.10).to_numpy(dtype=np.float64)

    hp_m = np.where(states == "Himachal Pradesh", params.hp_km_mult, 1.0)
    if params.use_state_statutory_fees:
        is_hp_app = (states == "Himachal Pradesh") & (comms == "Apple")
        fee_r = np.select(
            [states.isin(["Karnataka", "Gujarat"]), is_hp_app, states == "Himachal Pradesh", states == "Maharashtra"],
            [0.005, 0.010, 0.005, 0.010],
            default=params.out_of_district_fee,
        )
    else:
        fee_r = np.full(len(df), params.out_of_district_fee, dtype=np.float64)

    base_f = (params.freight_base + params.freight_per_km * hp_m * road_km) * params.freight_mult
    f_hat = base_f + np.where(same_dist, 0.0, fee_r * np.maximum(0.0, local_p))
    euclid_f = (params.freight_base + params.freight_per_km * hp_m * 1.20 * euclid_km) * params.freight_mult

    s0 = np.array([BASE_SPOIL_24H.get(c, 0.02) for c in comms], dtype=np.float64)
    t_eff = np.clip(np.where(np.isfinite(tmax), tmax, 25.0), 5.0, 48.0)
    rh_eff = np.clip(np.where(np.isfinite(rh), rh, 65.0), 20.0, 100.0)
    rain_eff = np.where(np.isfinite(rain), rain, 0.0)
    q10 = 2.0 ** ((t_eff - 20.0) / 10.0)
    rh_factor = 1.0 + 0.25 * np.maximum(0.0, (rh_eff - 70.0) / 30.0)
    bio_loss = s0 * (np.maximum(1.0, truck_hrs) / 24.0) * q10 * rh_factor + np.where(
        rain_eff >= params.heavy_rain_mm, params.heavy_rain_extra_spoil, 0.0
    )
    spoil_hat = np.clip(bio_loss * params.spoilage_mult, 0.0, 0.55)
    rain_pen = np.where(rain_eff >= params.heavy_rain_mm, 0.50 * ref_p * intra, 0.0)
    static_net = ref_p * (1.0 - spoil_hat) - rain_pen - f_hat - local_p
    return f_hat, spoil_hat, rain_pen, static_net, euclid_f


def t1_pass_mask(df: pd.DataFrame, cfg: CRCConfig) -> np.ndarray:
    """Apply either thin-grade-aware (age==0 adaptive) or strict T1 vitality gate."""
    ref_ok = np.isfinite(df["dest_ref_price"].to_numpy(dtype=np.float64)) & (df["dest_ref_price"].to_numpy(dtype=np.float64) > 0)
    age = df["dest_age_days"].to_numpy(dtype=np.float64)
    op = df["dest_open_prob_14d"].to_numpy(dtype=np.float64)
    dow = df["dest_dow_open_rate"].to_numpy(dtype=np.float64)

    strict = (age <= cfg.t1_max_age_days) & (op >= cfg.t1_min_open_prob_14d) & (dow >= cfg.t1_min_dow_open_rate)
    if not cfg.thin_grade_aware_t1:
        return ref_ok & strict
    fresh0 = (age == 0.0) & (op >= cfg.fresh0_min_open_prob_14d) & (dow >= cfg.fresh0_min_dow_open_rate)
    return ref_ok & (fresh0 | strict)


class UncensoredCRCForecaster:
    """Jointly estimates uncensored execution return & loss probability with CRC calibration."""

    def __init__(self, seed: int = 20261117, params: PayoffParams = PayoffParams()) -> None:
        self.seed = seed
        self.params = params
        self.reg_exec = HistGradientBoostingRegressor(
            loss="squared_error",
            max_depth=5,
            max_iter=180,
            min_samples_leaf=80,
            learning_rate=0.05,
            l2_regularization=1.0,
            categorical_features=[15, 16],
            random_state=seed,
        )
        self.clf_loss = HistGradientBoostingClassifier(
            max_depth=5,
            max_iter=180,
            min_samples_leaf=80,
            learning_rate=0.05,
            l2_regularization=1.0,
            categorical_features=[15, 16],
            random_state=seed,
        )
        self.lambda_star: float = 0.0
        self.train_cutoff_date: Optional[pd.Timestamp] = None
        self.val_crc_risk: float = 1.0
        self.is_fitted: bool = False

    def _build_features(self, df: pd.DataFrame, static_net: np.ndarray) -> np.ndarray:
        local_p = np.maximum(100.0, df["local_price"].to_numpy(dtype=np.float64))
        smr = np.clip(static_net / local_p, -0.5, 2.0)
        x_base = df[FEATURE_COLS].to_numpy(dtype=np.float64)
        return np.column_stack([x_base, smr])

    def fit(self, train_df: pd.DataFrame, cfg: CRCConfig = CRCConfig()) -> "UncensoredCRCForecaster":
        """Fit uncensored return & loss models strictly on corridors settled by max training date."""
        df = train_df.copy()
        df["_dt"] = pd.to_datetime(df["date"])
        df["_settle_dt"] = pd.to_datetime(df["arrival_date"]) + pd.Timedelta(days=2)
        max_dt = df["_dt"].max()
        self.train_cutoff_date = max_dt

        _, _, _, static_net, _ = compute_vectorized_static_payoff(df, self.params)
        t1_ok = t1_pass_mask(df, cfg)
        mask = (df["_settle_dt"] <= max_dt) & t1_ok & (static_net > 0.0) & np.isfinite(df["real_delta_net_inr"].to_numpy(dtype=np.float64))
        sub = df.loc[mask].copy()
        snet_sub = static_net[mask]

        x_tr = self._build_features(sub, snet_sub)
        r_exec = np.clip((sub["real_delta_net_inr"].to_numpy(dtype=np.float64) - snet_sub) / sub["dest_ref_price"].to_numpy(dtype=np.float64), -1.0, 0.8)
        y_loss = (sub["real_delta_net_inr"].to_numpy(dtype=np.float64) < 0.0).astype(np.int32)

        self.reg_exec.fit(x_tr, r_exec)
        self.clf_loss.fit(x_tr, y_loss)
        self.is_fitted = True
        return self

    def predict_components(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return (mu_hat, p_loss, static_net, f_hat, euclid_f) for each candidate row."""
        assert self.is_fitted, "UncensoredCRCForecaster must be fitted first."
        f_hat, _, _, static_net, euclid_f = compute_vectorized_static_payoff(df, self.params)
        x_ev = self._build_features(df, static_net)
        r_hat = self.reg_exec.predict(x_ev)
        p_loss = self.clf_loss.predict_proba(x_ev)[:, 1]
        mu_hat = static_net + df["dest_ref_price"].to_numpy(dtype=np.float64) * r_hat
        return mu_hat, p_loss, static_net, f_hat, euclid_f

    def calibrate_crc_lambda(
        self,
        val_df: pd.DataFrame,
        cfg: CRCConfig = CRCConfig(),
        lambda_grid: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Select smallest price-scaled risk multiplier lambda* ensuring Val CRC loss bound <= beta_target."""
        if lambda_grid is None:
            lambda_grid = np.round(np.linspace(0.0, 1.20, 25), 4)
        mu_hat, p_loss, static_net, f_hat, euclid_f = self.predict_components(val_df)
        chosen_lam = float(lambda_grid[-1])
        chosen_risk = 1.0
        chosen_mean = -1e9
        for lam in lambda_grid:
            res = evaluate_mandiguard_crc(
                val_df,
                cfg=cfg,
                lambda_risk=float(lam),
                precomputed=(mu_hat, p_loss, static_net, f_hat, euclid_f),
                params=self.params,
            )
            disp = res["is_dispatch"].to_numpy(dtype=bool)
            n_d = int(disp.sum())
            n_l = int(res.loc[disp, "is_phantom_loss"].sum()) if n_d > 0 else 0
            # A rule that never dispatches has no conditional loss rate.
            # (n_l+1)/(n_d+1) is 1 when n_d=0; treating that as risk 0 would
            # accept total abstention as perfect risk control.
            crc_risk = float((n_l + 1) / (n_d + 1)) if n_d > 0 else 1.0
            if crc_risk <= cfg.beta_target:
                chosen_lam = float(lam)
                chosen_risk = crc_risk
                chosen_mean = float(res["delta_net_inr"].mean())
                break
        self.lambda_star = chosen_lam
        self.val_crc_risk = chosen_risk
        return {
            "lambda_star": chosen_lam,
            "val_crc_risk": round(chosen_risk, 5),
            "val_mean_dnet": round(chosen_mean, 2),
        }


def evaluate_mandiguard_crc(
    cand_df: pd.DataFrame,
    cfg: CRCConfig = CRCConfig(),
    lambda_risk: float = 0.0,
    precomputed: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = None,
    params: PayoffParams = PayoffParams(),
) -> pd.DataFrame:
    """Evaluate vectorized sequential T1->T2->T3->T4 CRC dispatch cascade with real tool-call accounting."""
    df = cand_df.copy()
    if precomputed is None:
        raise ValueError("Pass precomputed (mu_hat, p_loss, static_net, f_hat, euclid_f) from UncensoredCRCForecaster.")
    mu_hat, p_loss, static_net, f_hat, euclid_f = precomputed
    df["_mu_hat"] = mu_hat
    df["_p_loss"] = p_loss
    df["_static_net"] = static_net
    df["_f_hat"] = f_hat
    df["_euclid_f"] = euclid_f
    df["_t1_ok"] = t1_pass_mask(df, cfg)
    df["_sort_key"] = (df["screen_spread"] - df["_euclid_f"]) if cfg.use_euclid_step0_sort else df["screen_spread"]

    df = df.sort_values(["episode_id", "_sort_key", "dest_market"], ascending=[True, False, True]).reset_index(drop=True)
    df["_rk"] = df.groupby("episode_id").cumcount()
    df = df[df["_rk"] < cfg.k_max].copy().reset_index(drop=True)

    ep_ids = df["episode_id"].to_numpy()
    n_rows = len(df)
    split_idx = np.flatnonzero(ep_ids[1:] != ep_ids[:-1]) + 1
    starts = np.concatenate(([0], split_idx))
    ends = np.concatenate((split_idx, [n_rows]))

    t1_ok = df["_t1_ok"].to_numpy(dtype=bool)
    ref_p = df["dest_ref_price"].to_numpy(dtype=np.float64)
    loc_p = df["local_price"].to_numpy(dtype=np.float64)
    f_arr = df["_f_hat"].to_numpy(dtype=np.float64)
    snet_arr = df["_static_net"].to_numpy(dtype=np.float64)
    mu_arr = df["_mu_hat"].to_numpy(dtype=np.float64)
    ploss_arr = df["_p_loss"].to_numpy(dtype=np.float64)
    real_dnet = df["real_delta_net_inr"].to_numpy(dtype=np.float64)
    real_od0 = df["real_open_d0_delta_net_inr"].to_numpy(dtype=np.float64)
    real_trap = df["real_closed_or_no_variety_trap"].to_numpy(dtype=bool)
    real_drop = df["real_arrival_price_dropped"].to_numpy(dtype=bool)
    dest_mkts = df["dest_market"].to_numpy()

    scores = mu_arr - lambda_risk * loc_p * ploss_arr

    records = []
    for s_i, e_i in zip(starts, ends):
        calls = 0
        best_r = -1
        best_sc = -1e18
        for r in range(s_i, e_i):
            calls += 1  # T1
            if not t1_ok[r]:
                continue
            calls += 1  # T2
            if ref_p[r] - loc_p[r] - f_arr[r] <= 0.0:
                continue
            calls += 1  # T3
            if snet_arr[r] <= 0.0:
                continue
            calls += 1  # T4 (Uncensored CRC)
            if mu_arr[r] > cfg.safety_margin_inr and scores[r] > best_sc:
                best_sc = float(scores[r])
                best_r = r

        if best_r >= 0 and best_sc > cfg.safety_margin_inr:
            dn = float(real_dnet[best_r])
            od0 = float(real_od0[best_r]) if np.isfinite(real_od0[best_r]) else np.nan
            records.append(
                {
                    "episode_id": ep_ids[s_i],
                    "action": "DISPATCH",
                    "chosen_dest": str(dest_mkts[best_r]),
                    "delta_net_inr": dn,
                    "open_d0_delta_net_inr": od0,
                    "is_dispatch": True,
                    "is_phantom_loss": bool(dn < 0.0),
                    "is_closed_trap": bool(real_trap[best_r]),
                    "is_arrival_drop": bool(real_drop[best_r]),
                    "tool_calls_total": calls,
                }
            )
        else:
            records.append(
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
    return pd.DataFrame(records)
