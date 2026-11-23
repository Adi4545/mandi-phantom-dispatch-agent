"""Statistical inference helpers for Revision v4 (A7):
- Exact ES10 point & weighted cluster-bootstrap estimator
- Paired two-way cluster bootstrap for Mean, Episode Loss Rate, and ES10
- Finite-sample Phipson & Smyth (2010) p-values and Holm-Bonferroni FWER control
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd

from revision.es10 import es10
from src.evaluation.bootstrap import holm_bonferroni, phipson_smyth_p


def weighted_es10(values: np.ndarray, weights: np.ndarray) -> float:
    """Exact weighted lower-10% Expected Shortfall matching revision/es10.py for unit weights."""
    v = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    mask = np.isfinite(v) & (w > 0)
    if not mask.any():
        return float("nan")
    v = v[mask]
    w = w[mask]
    order = np.argsort(v, kind="mergesort")
    vs = v[order]
    ws = w[order]
    total_w = float(ws.sum())
    target = 0.1 * total_w
    cw = np.cumsum(ws)
    idx = int(np.searchsorted(cw, target, side="left"))
    if idx >= len(vs):
        idx = len(vs) - 1
    prev_w = float(cw[idx - 1]) if idx > 0 else 0.0
    need_w = max(0.0, target - prev_w)
    head_sum = float(np.dot(ws[:idx], vs[:idx])) if idx > 0 else 0.0
    return float((head_sum + need_w * float(vs[idx])) / target)


def _batch_weighted_es10_presorted(vs: np.ndarray, ws: np.ndarray) -> np.ndarray:
    """Vectorized exact weighted ES10 when vs is ALREADY sorted ascending and ws aligns with vs."""
    b_n = ws.shape[0]
    out = np.empty(b_n, dtype=np.float64)
    cw = np.cumsum(ws, axis=1)
    totals = cw[:, -1]
    targets = 0.1 * totals
    n_len = len(vs)
    for b in range(b_n):
        tot = totals[b]
        if tot <= 0:
            out[b] = float("nan")
            continue
        tgt = targets[b]
        idx = int(np.searchsorted(cw[b], tgt, side="left"))
        if idx >= n_len:
            idx = n_len - 1
        prev_w = float(cw[b, idx - 1]) if idx > 0 else 0.0
        need_w = max(0.0, tgt - prev_w)
        head_sum = float(np.dot(ws[b, :idx], vs[:idx])) if idx > 0 else 0.0
        out[b] = (head_sum + need_w * float(vs[idx])) / tgt
    return out


def _batch_weighted_es10(vals: np.ndarray, w_mat: np.ndarray) -> np.ndarray:
    """Vectorized weighted ES10 over draws (B, N) where vals is (N,) unsorted or pre-sorted."""
    order = np.argsort(vals, kind="mergesort")
    return _batch_weighted_es10_presorted(vals[order], w_mat[:, order])


def two_way_cluster_bootstrap_all_metrics(
    df: pd.DataFrame,
    col_a: str,
    col_b: str,
    mandi_col: str = "origin_market_key",
    date_col: str = "date",
    week_block_len: int = 2,
    reps: int = 2000,
    seed: int = 20261117,
) -> Dict[str, Dict[str, float]]:
    """Paired two-way cluster bootstrap for Mean(A-B), EpLossRate(A-B), and ES10(A-B).

    Returns a dict keyed by metric name ('mean', 'ep_loss_rate', 'es10'), each with:
      estimate, ci95_low, ci95_high, p_value_greater, p_value_less, p_value_two_sided, n, n_clusters, n_blocks
    Note: larger mean and larger (less negative) ES10 are better ('greater'); smaller ep_loss_rate is better ('less').
    """
    va = df[col_a].to_numpy(dtype=np.float64)
    vb = df[col_b].to_numpy(dtype=np.float64)
    valid = np.isfinite(va) & np.isfinite(vb)
    va = va[valid]
    vb = vb[valid]
    n = int(len(va))

    m_codes, _ = pd.factorize(df.loc[valid, mandi_col], sort=True)
    dates = pd.to_datetime(df.loc[valid, date_col])
    week_idx = ((dates - dates.min()).dt.days // (7 * week_block_len)).to_numpy(dtype=np.int32)
    b_codes, _ = pd.factorize(week_idx, sort=True)
    n_m = int(m_codes.max()) + 1
    n_b = int(b_codes.max()) + 1

    # Fast matrices for Mean and Episode Loss Rate
    diff_mean = va - vb
    la = (va < 0).astype(np.float64)
    lb = (vb < 0).astype(np.float64)
    diff_loss = la - lb

    sum_mean = np.zeros((n_m, n_b), dtype=np.float64)
    sum_loss = np.zeros((n_m, n_b), dtype=np.float64)
    cnt_mb = np.zeros((n_m, n_b), dtype=np.float64)
    np.add.at(sum_mean, (m_codes, b_codes), diff_mean)
    np.add.at(sum_loss, (m_codes, b_codes), diff_loss)
    np.add.at(cnt_mb, (m_codes, b_codes), 1.0)

    est_mean = float(diff_mean.mean())
    est_loss = float(diff_loss.mean())
    est_es10 = float(es10(va) - es10(vb))

    rng = np.random.default_rng(seed)
    boot_mean = np.empty(reps, dtype=np.float64)
    boot_loss = np.empty(reps, dtype=np.float64)
    boot_es10 = np.empty(reps, dtype=np.float64)

    # Compress and pre-sort separately for va and vb (exact weighted ES10, zero per-chunk sorting)
    ga = pd.DataFrame({"m": m_codes, "b": b_codes, "v": va}).groupby(["m", "b", "v"], sort=False, as_index=False).size()
    oa = np.argsort(ga["v"].to_numpy(dtype=np.float64), kind="mergesort")
    gma = ga["m"].to_numpy(dtype=np.int32)[oa]
    gba = ga["b"].to_numpy(dtype=np.int32)[oa]
    gva_s = ga["v"].to_numpy(dtype=np.float64)[oa]
    gca = ga["size"].to_numpy(dtype=np.float64)[oa]

    gb_df = pd.DataFrame({"m": m_codes, "b": b_codes, "v": vb}).groupby(["m", "b", "v"], sort=False, as_index=False).size()
    ob = np.argsort(gb_df["v"].to_numpy(dtype=np.float64), kind="mergesort")
    gmb = gb_df["m"].to_numpy(dtype=np.int32)[ob]
    gbb = gb_df["b"].to_numpy(dtype=np.int32)[ob]
    gvb_s = gb_df["v"].to_numpy(dtype=np.float64)[ob]
    gcb = gb_df["size"].to_numpy(dtype=np.float64)[ob]

    chunk = 100
    for r0 in range(0, reps, chunk):
        rc = min(chunk, reps - r0)
        m_idx = rng.integers(0, n_m, size=(rc, n_m))
        b_idx = rng.integers(0, n_b, size=(rc, n_b))
        m_w = np.zeros((rc, n_m), dtype=np.float64)
        b_w = np.zeros((rc, n_b), dtype=np.float64)
        for ci in range(rc):
            m_w[ci] = np.bincount(m_idx[ci], minlength=n_m)
            b_w[ci] = np.bincount(b_idx[ci], minlength=n_b)

        den = np.einsum("rm,mb,rb->r", m_w, cnt_mb, b_w)
        num_m = np.einsum("rm,mb,rb->r", m_w, sum_mean, b_w)
        num_l = np.einsum("rm,mb,rb->r", m_w, sum_loss, b_w)
        with np.errstate(divide="ignore", invalid="ignore"):
            boot_mean[r0 : r0 + rc] = np.where(den > 0, num_m / den, est_mean)
            boot_loss[r0 : r0 + rc] = np.where(den > 0, num_l / den, est_loss)

        ws_a = m_w[:, gma] * b_w[:, gba] * gca[None, :]
        ws_b = m_w[:, gmb] * b_w[:, gbb] * gcb[None, :]
        es_a = _batch_weighted_es10_presorted(gva_s, ws_a)
        es_b = _batch_weighted_es10_presorted(gvb_s, ws_b)
        es_diff = es_a - es_b
        boot_es10[r0 : r0 + rc] = np.where(np.isfinite(es_diff), es_diff, est_es10)

    def _summarize(est: float, draws: np.ndarray) -> Dict[str, float]:
        lo, hi = np.quantile(draws, [0.025, 0.975])
        p_gr = phipson_smyth_p(int(np.sum(draws <= 0.0)), reps)
        p_ls = phipson_smyth_p(int(np.sum(draws >= 0.0)), reps)
        p_two = min(1.0, 2.0 * min(p_gr, p_ls))
        return {
            "estimate": float(est),
            "ci95_low": float(lo),
            "ci95_high": float(hi),
            "p_value_greater": float(p_gr),
            "p_value_less": float(p_ls),
            "p_value_two_sided": float(p_two),
            "n": n,
            "n_clusters": n_m,
            "n_blocks": n_b,
        }

    return {
        "mean": _summarize(est_mean, boot_mean),
        "ep_loss_rate": _summarize(est_loss, boot_loss),
        "es10": _summarize(est_es10, boot_es10),
    }


def ci95_single_metric(
    df: pd.DataFrame,
    col: str,
    mandi_col: str = "origin_market_key",
    date_col: str = "date",
    week_block_len: int = 2,
    reps: int = 1000,
    seed: int = 20261117,
) -> Dict[str, Tuple[float, float]]:
    """Cluster-bootstrap 95% CIs for a single policy's mean, ep_loss_rate, and ES10."""
    v = df[col].to_numpy(dtype=np.float64)
    m_codes, _ = pd.factorize(df[mandi_col], sort=True)
    dates = pd.to_datetime(df[date_col])
    week_idx = ((dates - dates.min()).dt.days // (7 * week_block_len)).to_numpy(dtype=np.int32)
    b_codes, _ = pd.factorize(week_idx, sort=True)
    n_m = int(m_codes.max()) + 1
    n_b = int(b_codes.max()) + 1

    loss = (v < 0).astype(np.float64)
    sum_m = np.zeros((n_m, n_b), dtype=np.float64)
    sum_l = np.zeros((n_m, n_b), dtype=np.float64)
    cnt = np.zeros((n_m, n_b), dtype=np.float64)
    np.add.at(sum_m, (m_codes, b_codes), v)
    np.add.at(sum_l, (m_codes, b_codes), loss)
    np.add.at(cnt, (m_codes, b_codes), 1.0)

    grp_es = pd.DataFrame({"m": m_codes, "b": b_codes, "v": v}).groupby(["m", "b", "v"], sort=False, as_index=False).size()
    gm = grp_es["m"].to_numpy(dtype=np.int32)
    gb = grp_es["b"].to_numpy(dtype=np.int32)
    gv = grp_es["v"].to_numpy(dtype=np.float64)
    gc = grp_es["size"].to_numpy(dtype=np.float64)

    rng = np.random.default_rng(seed)
    bm = np.empty(reps, dtype=np.float64)
    bl = np.empty(reps, dtype=np.float64)
    be = np.empty(reps, dtype=np.float64)
    est_m = float(v.mean())
    est_l = float(loss.mean())
    est_e = float(es10(v))

    chunk = 100
    for r0 in range(0, reps, chunk):
        rc = min(chunk, reps - r0)
        m_idx = rng.integers(0, n_m, size=(rc, n_m))
        b_idx = rng.integers(0, n_b, size=(rc, n_b))
        m_w = np.zeros((rc, n_m), dtype=np.float64)
        b_w = np.zeros((rc, n_b), dtype=np.float64)
        for ci in range(rc):
            m_w[ci] = np.bincount(m_idx[ci], minlength=n_m)
            b_w[ci] = np.bincount(b_idx[ci], minlength=n_b)
        den = np.einsum("rm,mb,rb->r", m_w, cnt, b_w)
        with np.errstate(divide="ignore", invalid="ignore"):
            bm[r0 : r0 + rc] = np.where(den > 0, np.einsum("rm,mb,rb->r", m_w, sum_m, b_w) / den, est_m)
            bl[r0 : r0 + rc] = np.where(den > 0, np.einsum("rm,mb,rb->r", m_w, sum_l, b_w) / den, est_l)
        w_rep = m_w[:, gm] * b_w[:, gb] * gc[None, :]
        es_d = _batch_weighted_es10(gv, w_rep)
        be[r0 : r0 + rc] = np.where(np.isfinite(es_d), es_d, est_e)

    return {
        "mean": tuple(float(x) for x in np.quantile(bm, [0.025, 0.975])),
        "ep_loss_rate": tuple(float(x) for x in np.quantile(bl, [0.025, 0.975])),
        "es10": tuple(float(x) for x in np.quantile(be, [0.025, 0.975])),
    }
