"""Causal arrival-day return forecaster and streaming conformal lower confidence bound (LCB).

Trained strictly on 2024 (with arrival_date <= 2024-12-31). Conformal downside quantile
q_0.80 is updated causally as historical arrival dates mature (arrival_date <= decision_date t).
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

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


class CausalArrivalForecaster:
    """Predicts arrival-day relative return (P_arrival - P_ref) / P_ref + causal 80% LCB."""

    def __init__(self, seed: int = 20261117, window_size: int = 400, alpha_target: float = 0.20) -> None:
        self.seed = seed
        self.window_size = window_size
        self.alpha_target = alpha_target
        self.point_model = HistGradientBoostingRegressor(
            loss="squared_error",
            max_depth=5,
            max_iter=180,
            min_samples_leaf=80,
            learning_rate=0.05,
            l2_regularization=1.0,
            categorical_features=[15, 16],
            random_state=seed,
        )
        self.seed_residuals_by_comm: Dict[str, List[float]] = defaultdict(list)
        self.seed_residuals_global: List[float] = []
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame) -> "CausalArrivalForecaster":
        """Fit on strictly 2024 training rows (arrival_date <= 2024-12-31) and seed causal residuals."""
        df = train_df.dropna(subset=["target_ret"]).copy()
        df = df.sort_values("date").reset_index(drop=True)
        # Temporal split inside 2024: Jan-Sep fit, Oct-Dec out-of-sample seed residuals (no overfit!)
        cutoff_internal = pd.Timestamp("2024-10-01")
        fit_sub = df[pd.to_datetime(df["arrival_date"]) < cutoff_internal]
        seed_sub = df[pd.to_datetime(df["date"]) >= cutoff_internal]

        X_fit = fit_sub[FEATURE_COLS].to_numpy(dtype=np.float64)
        y_fit = np.clip(fit_sub["target_ret"].to_numpy(dtype=np.float64), -0.60, 0.80)
        temp_model = HistGradientBoostingRegressor(
            loss="squared_error",
            max_depth=5,
            max_iter=180,
            min_samples_leaf=80,
            learning_rate=0.05,
            l2_regularization=1.0,
            categorical_features=[15, 16],
            random_state=self.seed,
        )
        temp_model.fit(X_fit, y_fit)

        if len(seed_sub) > 0:
            preds_seed = temp_model.predict(seed_sub[FEATURE_COLS].to_numpy(dtype=np.float64))
            # Downside shortfall residual: pred - actual (larger = actual fell below prediction)
            res = preds_seed - seed_sub["target_ret"].to_numpy(dtype=np.float64)
            self.seed_residuals_global = res[-self.window_size :].tolist()
            for comm, grp in seed_sub.assign(_r=res).groupby("Commodity"):
                self.seed_residuals_by_comm[str(comm)] = grp["_r"].to_numpy()[-self.window_size :].tolist()

        # Refit final model on full 2024 (still strictly arrival_date <= 2024-12-31)
        X_all = df[FEATURE_COLS].to_numpy(dtype=np.float64)
        y_all = np.clip(df["target_ret"].to_numpy(dtype=np.float64), -0.60, 0.80)
        self.point_model.fit(X_all, y_all)
        self.is_fitted = True
        return self

    def predict_point_and_causal_lcb(self, eval_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Predict point return and strictly causal conformal LCB return row-by-row over sorted dates.

        At decision date t, ONLY residuals whose arrival_date <= t are added to the conformal buffer.
        """
        assert self.is_fitted, "Model must be fitted on 2024 before predicting."
        df = eval_df.copy()
        df["_orig_idx"] = np.arange(len(df))
        df["date_dt"] = pd.to_datetime(df["date"])
        df["arr_dt"] = pd.to_datetime(df["arrival_date"])
        df = df.sort_values("date_dt").reset_index(drop=True)

        X = df[FEATURE_COLS].to_numpy(dtype=np.float64)
        pred_ret = self.point_model.predict(X)
        lcb_ret = np.empty(len(df), dtype=np.float64)

        # Initialize causal residual buffers from 2024 seed
        buf_global: deque = deque(self.seed_residuals_global[-self.window_size :], maxlen=self.window_size)
        buf_comm: Dict[str, deque] = {
            c: deque(vals[-self.window_size :], maxlen=self.window_size)
            for c, vals in self.seed_residuals_by_comm.items()
        }
        # Pending observations keyed by arrival_date so nothing leaks before arrival_date <= t
        pending: Dict[pd.Timestamp, List[Tuple[str, float]]] = defaultdict(list)
        matured_dates_heap: List[pd.Timestamp] = []

        # Group by date_dt to guarantee zero same-day peeking and crisp causal maturation
        q_level = 1.0 - self.alpha_target  # 0.80 quantile of downside shortfall (pred - actual)
        import heapq

        for date_t, grp in df.groupby("date_dt", sort=True):
            # 1. Mature all past dispatches whose arrival_date <= date_t
            while matured_dates_heap and matured_dates_heap[0] <= date_t:
                arr_d = heapq.heappop(matured_dates_heap)
                for comm_k, res_val in pending.pop(arr_d, []):
                    buf_global.append(res_val)
                    if comm_k not in buf_comm:
                        buf_comm[comm_k] = deque(maxlen=self.window_size)
                    buf_comm[comm_k].append(res_val)

            # 2. Compute current causal quantile per commodity on date_t
            q_by_comm: Dict[str, float] = {}
            q_glob = float(np.quantile(buf_global, q_level)) if len(buf_global) >= 20 else 0.12
            for comm_k in COMMODITY_TO_ID:
                cbuf = buf_comm.get(comm_k)
                if cbuf is not None and len(cbuf) >= 40:
                    q_by_comm[comm_k] = float(np.quantile(cbuf, q_level))
                else:
                    q_by_comm[comm_k] = q_glob

            # 3. Emit LCB for all rows on date_t and enqueue matured residuals if target_ret is observed
            idxs = grp.index.to_numpy()
            comms = grp["Commodity"].to_numpy()
            arr_dts = grp["arr_dt"].to_numpy()
            has_tgt = "target_ret" in grp.columns
            tgt_vals = grp["target_ret"].to_numpy() if has_tgt else None

            for local_pos, row_idx in enumerate(idxs):
                cm = str(comms[local_pos])
                q_val = q_by_comm.get(cm, q_glob)
                lcb_ret[row_idx] = pred_ret[row_idx] - max(0.0, q_val)
                if has_tgt:
                    tv = tgt_vals[local_pos]
                    if np.isfinite(tv):
                        ad = pd.Timestamp(arr_dts[local_pos])
                        if ad not in pending:
                            heapq.heappush(matured_dates_heap, ad)
                        pending[ad].append((cm, float(pred_ret[row_idx] - tv)))

        # Restore original row order
        order = np.argsort(df["_orig_idx"].to_numpy())
        return pred_ret[order], lcb_ret[order]
