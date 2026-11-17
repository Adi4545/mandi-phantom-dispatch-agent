"""Clustered bootstrap and Holm-Bonferroni multiple-testing inference for dispatch policies.

Implements Section 3 Step 4:
  - Two-Way Origin-Mandi x Week-Block Bootstrap (R=5,000, seed=20261117)
  - Phipson & Smyth (2010) finite-sample permutation/bootstrap p-values
  - Holm-Bonferroni (1979) step-down FWER adjustment across m confirmatory hypotheses
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd


def phipson_smyth_p(n_ge: int, reps: int) -> float:
    return float((1 + n_ge) / (reps + 1))


def holm_bonferroni(p_values: Sequence[float]) -> List[float]:
    m = len(p_values)
    order = np.argsort(p_values)
    adj = np.empty(m, dtype=float)
    running_max = 0.0
    for rank, idx in enumerate(order):
        val = min(1.0, (m - rank) * float(p_values[idx]))
        running_max = max(running_max, val)
        adj[idx] = running_max
    return adj.tolist()


def two_way_mandi_week_bootstrap(
    df: pd.DataFrame,
    metric_col_a: str,
    metric_col_b: str | None = None,
    mandi_col: str = "origin_market_key",
    date_col: str = "date",
    week_block_len: int = 2,
    reps: int = 5000,
    seed: int = 20261117,
    direction: str = "greater",  # "greater" tests mean(A - B) > 0; "less" tests mean(A - B) < 0
) -> Dict[str, float]:
    """Fast vectorized two-way Origin-Mandi x Week-Block bootstrap on paired episode metrics.

    Each draw resamples Origin Mandis with replacement (multiplicity m_i) AND 2-week calendar
    blocks with replacement (multiplicity w_b), weighting episode (i, t) by m_i * w_{b(t)}.
    """
    vals_a = df[metric_col_a].to_numpy(dtype=np.float64)
    vals_b = df[metric_col_b].to_numpy(dtype=np.float64) if metric_col_b is not None else np.zeros_like(vals_a)
    diff = vals_a - vals_b

    valid = np.isfinite(diff)
    diff = diff[valid]
    if len(diff) == 0:
        return {"estimate": np.nan, "ci95_low": np.nan, "ci95_high": np.nan, "p_value": 1.0, "n": 0}

    mandi_codes, _ = pd.factorize(df.loc[valid, mandi_col], sort=True)
    dates = pd.to_datetime(df.loc[valid, date_col])
    min_d = dates.min()
    week_idx = ((dates - min_d).dt.days // (7 * week_block_len)).to_numpy(dtype=np.int32)
    block_codes, _ = pd.factorize(week_idx, sort=True)

    n_mandis = int(mandi_codes.max()) + 1
    n_blocks = int(block_codes.max()) + 1
    # Aggregate diff into (n_mandis, n_blocks) sum & count matrices so 5,000 draws run in < 0.1s!
    sum_mat = np.zeros((n_mandis, n_blocks), dtype=np.float64)
    cnt_mat = np.zeros((n_mandis, n_blocks), dtype=np.float64)
    np.add.at(sum_mat, (mandi_codes, block_codes), diff)
    np.add.at(cnt_mat, (mandi_codes, block_codes), 1.0)

    point_est = float(diff.mean())
    rng = np.random.default_rng(seed)

    # Sample multinomial / uniform index counts per draw in chunks to bound RAM
    boot_ests = np.empty(reps, dtype=np.float64)
    chunk = 500
    for r0 in range(0, reps, chunk):
        rc = min(chunk, reps - r0)
        m_idx = rng.integers(0, n_mandis, size=(rc, n_mandis))
        b_idx = rng.integers(0, n_blocks, size=(rc, n_blocks))

        m_w = np.zeros((rc, n_mandis), dtype=np.float64)
        b_w = np.zeros((rc, n_blocks), dtype=np.float64)
        for c_i in range(rc):
            m_w[c_i] = np.bincount(m_idx[c_i], minlength=n_mandis)
            b_w[c_i] = np.bincount(b_idx[c_i], minlength=n_blocks)

        num = np.einsum("rm,mb,rb->r", m_w, sum_mat, b_w)
        den = np.einsum("rm,mb,rb->r", m_w, cnt_mat, b_w)
        with np.errstate(divide="ignore", invalid="ignore"):
            vals = np.where(den > 0, num / den, point_est)
        boot_ests[r0 : r0 + rc] = vals

    ci_low, ci_high = np.quantile(boot_ests, [0.025, 0.975])
    # Center bootstrap distribution under H0 to compute one-sided test, or count violation fraction directly
    if direction == "greater":
        # Fraction of bootstrap draws <= 0 (paired bootstrap one-sided p-value)
        n_fail = int(np.sum(boot_ests <= 0.0))
    else:
        n_fail = int(np.sum(boot_ests >= 0.0))
    p_val = phipson_smyth_p(n_fail, reps)
    return {
        "estimate": point_est,
        "ci95_low": float(ci_low),
        "ci95_high": float(ci_high),
        "p_value": p_val,
        "n": int(len(diff)),
        "n_mandis": n_mandis,
        "n_blocks": n_blocks,
    }
