"""Causal arrival-day return forecasters and streaming conformal / ACI lower bounds.

Supports:
  - Frozen HGBR point model (`model_kind="hgbr"`, default)
  - Direct quantile GBDT (`model_kind="quantile_q20"`)
  - Neural MLPRegressor (`model_kind="mlp"`)
  - ExtraTreesRegressor (`model_kind="extratrees"`)
  - Static causal conformal LCB (`adaptive_gamma=None`) or Gibbs & Candes (2021)
    Adaptive Conformal Inference (`adaptive_gamma=0.005`, alpha clipped in [0.02, 0.45])

Strictly zero-leakage: residuals are buffered ONLY after `arrival_date <= decision_date t`.
"""

from __future__ import annotations

import heapq
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

FEATURE_COLS = [
    "tau_days",
    "dest_age_days",
    "dest_ret_1d",
    "dest_ret_3d",
    "dest_ret_7d",
    "dest_ret_14d",
    "dest_vol_14d",
    "dest_intra_spread_14d",
    "dest_open_prob_14d",
    "dest_dow_open_rate",
    "state_hub_ret_7d",
    "dest_level_ratio_30d",
    "arrival_dow",
    "month_sin",
    "month_cos",
    "commodity_code",
    "state_code",
]

COMMODITY_TO_ID = {"Onion": 0, "Potato": 1, "Tomato": 2, "Apple": 3}
STATE_TO_ID = {
    "Maharashtra": 0,
    "Uttar Pradesh": 1,
    "Karnataka": 2,
    "Madhya Pradesh": 3,
    "Gujarat": 4,
    "Himachal Pradesh": 5,
}


def _make_base_estimator(model_kind: str, seed: int):
    if model_kind == "hgbr":
        return HistGradientBoostingRegressor(
            loss="squared_error",
            max_depth=5,
            max_iter=180,
            min_samples_leaf=80,
            learning_rate=0.05,
            l2_regularization=1.0,
            categorical_features=[15, 16],
            random_state=seed,
        )
    if model_kind == "quantile_q20":
        return HistGradientBoostingRegressor(
            loss="quantile",
            quantile=0.20,
            max_depth=5,
            max_iter=180,
            min_samples_leaf=80,
            learning_rate=0.05,
            l2_regularization=1.0,
            categorical_features=[15, 16],
            random_state=seed,
        )
    if model_kind == "extratrees":
        return Pipeline(
            [
                ("imp", SimpleImputer(strategy="median")),
                (
                    "et",
                    ExtraTreesRegressor(
                        n_estimators=80,
                        max_depth=14,
                        min_samples_leaf=60,
                        max_samples=0.40,
                        bootstrap=True,
                        n_jobs=-1,
                        random_state=seed,
                    ),
                ),
            ]
        )
    if model_kind == "mlp":
        num_idx = list(range(15))
        cat_idx = [15, 16]
        prep = ColumnTransformer(
            [
                ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num_idx),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_idx),
            ]
        )
        return Pipeline(
            [
                ("prep", prep),
                (
                    "mlp",
                    MLPRegressor(
                        hidden_layer_sizes=(128, 64),
                        activation="relu",
                        alpha=1e-2,
                        batch_size=1024,
                        max_iter=40,
                        early_stopping=True,
                        n_iter_no_change=5,
                        random_state=seed,
                    ),
                ),
            ]
        )
    raise ValueError(f"Unknown model_kind: {model_kind}")


class CausalArrivalForecaster:
    """Predicts arrival-day relative return (P_arrival - P_ref) / P_ref + causal 80% LCB or ACI."""

    def __init__(
        self,
        seed: int = 20261117,
        window_size: int = 400,
        alpha_target: float = 0.20,
        model_kind: str = "hgbr",
    ) -> None:
        self.seed = seed
        self.window_size = window_size
        self.alpha_target = alpha_target
        self.model_kind = model_kind
        self.point_model = _make_base_estimator(model_kind, seed)
        self.seed_residuals_by_comm: Dict[str, List[float]] = defaultdict(list)
        self.seed_residuals_global: List[float] = []
        self.last_aci_alpha_by_comm: Dict[str, float] = {}
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame) -> "CausalArrivalForecaster":
        """Fit strictly on historical training rows and seed out-of-sample conformal residuals."""
        df = train_df.dropna(subset=["target_ret"]).copy()
        df["date_dt"] = pd.to_datetime(df["date"])
        df["arr_dt"] = pd.to_datetime(df["arrival_date"])
        df = df.sort_values("date_dt").reset_index(drop=True)

        max_arr = df["arr_dt"].max()
        min_d = df["date_dt"].min()
        if max_arr >= pd.Timestamp("2024-11-01") and min_d <= pd.Timestamp("2024-09-01"):
            cutoff_internal = pd.Timestamp("2024-10-01")
        else:
            cutoff_internal = pd.Timestamp(df["date_dt"].quantile(0.75))

        fit_sub = df[df["arr_dt"] < cutoff_internal]
        seed_sub = df[df["date_dt"] >= cutoff_internal]

        X_fit = fit_sub[FEATURE_COLS].to_numpy(dtype=np.float64)
        y_fit = np.clip(fit_sub["target_ret"].to_numpy(dtype=np.float64), -0.60, 0.80)
        temp_model = _make_base_estimator(getattr(self, "model_kind", "hgbr"), self.seed)
        temp_model.fit(X_fit, y_fit)

        if len(seed_sub) > 0:
            preds_seed = temp_model.predict(seed_sub[FEATURE_COLS].to_numpy(dtype=np.float64))
            res = preds_seed - seed_sub["target_ret"].to_numpy(dtype=np.float64)
            self.seed_residuals_global = res[-self.window_size :].tolist()
            for comm, grp in seed_sub.assign(_r=res).groupby("Commodity"):
                self.seed_residuals_by_comm[str(comm)] = grp["_r"].to_numpy()[-self.window_size :].tolist()

        X_all = df[FEATURE_COLS].to_numpy(dtype=np.float64)
        y_all = np.clip(df["target_ret"].to_numpy(dtype=np.float64), -0.60, 0.80)
        self.point_model.fit(X_all, y_all)
        self.is_fitted = True
        return self

    def predict_point_and_causal_lcb(
        self, eval_df: pd.DataFrame, adaptive_gamma: Optional[float] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Predict point return and strictly causal conformal LCB (static or Gibbs-Candes ACI).

        At decision date t, ONLY residuals whose arrival_date <= t mature into the buffer.
        """
        assert self.is_fitted, "Model must be fitted before predicting."
        df = eval_df.copy()
        df["_orig_idx"] = np.arange(len(df))
        df["date_dt"] = pd.to_datetime(df["date"])
        df["arr_dt"] = pd.to_datetime(df["arrival_date"])
        df = df.sort_values("date_dt").reset_index(drop=True)

        X = df[FEATURE_COLS].to_numpy(dtype=np.float64)
        pred_ret = self.point_model.predict(X)
        lcb_ret = np.empty(len(df), dtype=np.float64)

        buf_global: deque = deque(self.seed_residuals_global[-self.window_size :], maxlen=self.window_size)
        buf_comm: Dict[str, deque] = {
            c: deque(vals[-self.window_size :], maxlen=self.window_size)
            for c, vals in self.seed_residuals_by_comm.items()
        }
        alpha_comm: Dict[str, float] = {c: self.alpha_target for c in COMMODITY_TO_ID}
        pending: Dict[pd.Timestamp, List[Tuple[str, float, float]]] = defaultdict(list)
        matured_dates_heap: List[pd.Timestamp] = []

        for date_t, grp in df.groupby("date_dt", sort=True):
            while matured_dates_heap and matured_dates_heap[0] <= date_t:
                arr_d = heapq.heappop(matured_dates_heap)
                for comm_k, res_val, issued_q in pending.pop(arr_d, []):
                    buf_global.append(res_val)
                    if comm_k not in buf_comm:
                        buf_comm[comm_k] = deque(maxlen=self.window_size)
                    buf_comm[comm_k].append(res_val)
                    if adaptive_gamma is not None:
                        err_t = 1.0 if res_val > max(0.0, issued_q) else 0.0
                        cur_a = alpha_comm.get(comm_k, self.alpha_target)
                        alpha_comm[comm_k] = float(
                            np.clip(cur_a + adaptive_gamma * (self.alpha_target - err_t), 0.02, 0.45)
                        )

            q_by_comm: Dict[str, float] = {}
            q_level_glob = float(np.clip(1.0 - self.alpha_target, 0.05, 0.98))
            q_glob = float(np.quantile(buf_global, q_level_glob)) if len(buf_global) >= 20 else 0.12
            for comm_k in COMMODITY_TO_ID:
                cbuf = buf_comm.get(comm_k)
                a_use = alpha_comm.get(comm_k, self.alpha_target) if adaptive_gamma is not None else self.alpha_target
                q_lv = float(np.clip(1.0 - a_use, 0.55, 0.98))
                if cbuf is not None and len(cbuf) >= 40:
                    q_by_comm[comm_k] = float(np.quantile(cbuf, q_lv))
                else:
                    q_by_comm[comm_k] = q_glob

            idxs = grp.index.to_numpy()
            comms = grp["Commodity"].to_numpy()
            arr_dts = grp["arr_dt"].to_numpy()
            has_tgt = "target_ret" in grp.columns
            tgt_vals = grp["target_ret"].to_numpy() if has_tgt else None

            for local_pos, row_idx in enumerate(idxs):
                cm = str(comms[local_pos])
                q_val = q_by_comm.get(cm, q_glob)
                if getattr(self, "model_kind", "hgbr") == "quantile_q20":
                    lcb_ret[row_idx] = pred_ret[row_idx]
                else:
                    lcb_ret[row_idx] = pred_ret[row_idx] - max(0.0, q_val)
                if has_tgt:
                    tv = tgt_vals[local_pos]
                    if np.isfinite(tv):
                        ad = pd.Timestamp(arr_dts[local_pos])
                        if ad not in pending:
                            heapq.heappush(matured_dates_heap, ad)
                        pending[ad].append((cm, float(pred_ret[row_idx] - tv), float(q_val)))

        if adaptive_gamma is not None:
            self.last_aci_alpha_by_comm = dict(alpha_comm)
        order = np.argsort(df["_orig_idx"].to_numpy())
        return pred_ret[order], lcb_ret[order]
