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


def es_alpha(arr: np.ndarray, alpha: float = 0.10) -> float:
    """Exact fractional lower-alpha Expected Shortfall matching es10 when alpha=0.10."""
    x = np.sort(np.asarray(arr, dtype=np.float64))
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return float("nan")
    m = float(alpha) * n
    k = int(np.floor(m))
    f = m - k
    tot = float(x[:k].sum()) if k > 0 else 0.0
    if f > 1e-12 and k < n:
        tot += f * float(x[k])
    return float(tot / m)


def _batch_weighted_es_alpha_presorted(vs: np.ndarray, ws: np.ndarray, alpha: float = 0.10) -> np.ndarray:
    """Vectorized exact weighted ES_alpha when vs is ALREADY sorted ascending and ws aligns with vs."""
    b_n = ws.shape[0]
    out = np.empty(b_n, dtype=np.float64)
    cw = np.cumsum(ws, axis=1)
    totals = cw[:, -1]
    targets = float(alpha) * totals
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


def two_way_cluster_bootstrap_extended(
    df: pd.DataFrame,
    col_a: str,
    col_b: str,
    disp_col_a: str | None = None,
    disp_col_b: str | None = None,
    mandi_col: str = "origin_market_key",
    date_col: str = "date",
    week_block_len: int = 2,
    reps: int = 2000,
    seed: int = 20261117,
) -> Dict[str, Dict[str, float]]:
    """Two-way cluster bootstrap returning mean, ep_loss_rate, ep_es10, cond_es10, cond_es05 + null-centered basic CI/p."""
    va = df[col_a].to_numpy(dtype=np.float64)
    vb = df[col_b].to_numpy(dtype=np.float64)
    valid = np.isfinite(va) & np.isfinite(vb)
    va = va[valid]
    vb = vb[valid]
    n = int(len(va))

    da = df.loc[valid, disp_col_a].to_numpy(dtype=bool) if disp_col_a is not None else np.ones(n, dtype=bool)
    db = df.loc[valid, disp_col_b].to_numpy(dtype=bool) if disp_col_b is not None else np.ones(n, dtype=bool)

    m_codes, _ = pd.factorize(df.loc[valid, mandi_col], sort=True)
    dates = pd.to_datetime(df.loc[valid, date_col])
    week_idx = ((dates - dates.min()).dt.days // (7 * week_block_len)).to_numpy(dtype=np.int32)
    b_codes, _ = pd.factorize(week_idx, sort=True)
    n_m = int(m_codes.max()) + 1
    n_b = int(b_codes.max()) + 1

    diff_mean = va - vb
    diff_loss = (va < 0).astype(np.float64) - (vb < 0).astype(np.float64)
    sum_mean = np.zeros((n_m, n_b), dtype=np.float64)
    sum_loss = np.zeros((n_m, n_b), dtype=np.float64)
    cnt_mb = np.zeros((n_m, n_b), dtype=np.float64)
    np.add.at(sum_mean, (m_codes, b_codes), diff_mean)
    np.add.at(sum_loss, (m_codes, b_codes), diff_loss)
    np.add.at(cnt_mb, (m_codes, b_codes), 1.0)

    est_mean = float(diff_mean.mean())
    est_loss = float(diff_loss.mean())
    est_es10 = float(es10(va) - es10(vb))
    est_cond_es10 = float(es_alpha(va[da], 0.10) - es_alpha(vb[db], 0.10)) if (da.any() and db.any()) else float("nan")
    est_cond_es05 = float(es_alpha(va[da], 0.05) - es_alpha(vb[db], 0.05)) if (da.any() and db.any()) else float("nan")

    def _prep_sorted(vals_sub: np.ndarray, m_sub: np.ndarray, b_sub: np.ndarray):
        gdf = pd.DataFrame({"m": m_sub, "b": b_sub, "v": vals_sub}).groupby(["m", "b", "v"], sort=False, as_index=False).size()
        ord_i = np.argsort(gdf["v"].to_numpy(dtype=np.float64), kind="mergesort")
        return (
            gdf["m"].to_numpy(dtype=np.int32)[ord_i],
            gdf["b"].to_numpy(dtype=np.int32)[ord_i],
            gdf["v"].to_numpy(dtype=np.float64)[ord_i],
            gdf["size"].to_numpy(dtype=np.float64)[ord_i],
        )

    gma, gba, gva_s, gca = _prep_sorted(va, m_codes, b_codes)
    gmb, gbb, gvb_s, gcb = _prep_sorted(vb, m_codes, b_codes)
    cma, cba, cva_s, cca = _prep_sorted(va[da], m_codes[da], b_codes[da])
    cmb, cbb, cvb_s, ccb = _prep_sorted(vb[db], m_codes[db], b_codes[db])

    rng = np.random.default_rng(seed)
    boot_m = np.empty(reps, dtype=np.float64)
    boot_l = np.empty(reps, dtype=np.float64)
    boot_e10 = np.empty(reps, dtype=np.float64)
    boot_ce10 = np.empty(reps, dtype=np.float64)
    boot_ce05 = np.empty(reps, dtype=np.float64)

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
        if np.any(den <= 0.0):
            raise RuntimeError(f"Zero total weight draw encountered in cluster bootstrap ({col_a} vs {col_b})")
        boot_m[r0 : r0 + rc] = np.einsum("rm,mb,rb->r", m_w, sum_mean, b_w) / den
        boot_l[r0 : r0 + rc] = np.einsum("rm,mb,rb->r", m_w, sum_loss, b_w) / den

        ws_a = m_w[:, gma] * b_w[:, gba] * gca[None, :]
        ws_b = m_w[:, gmb] * b_w[:, gbb] * gcb[None, :]
        boot_e10[r0 : r0 + rc] = _batch_weighted_es_alpha_presorted(gva_s, ws_a, 0.10) - _batch_weighted_es_alpha_presorted(gvb_s, ws_b, 0.10)

        wsc_a = m_w[:, cma] * b_w[:, cba] * cca[None, :]
        wsc_b = m_w[:, cmb] * b_w[:, cbb] * ccb[None, :]
        ce10 = _batch_weighted_es_alpha_presorted(cva_s, wsc_a, 0.10) - _batch_weighted_es_alpha_presorted(cvb_s, wsc_b, 0.10)
        ce05 = _batch_weighted_es_alpha_presorted(cva_s, wsc_a, 0.05) - _batch_weighted_es_alpha_presorted(cvb_s, wsc_b, 0.05)
        boot_ce10[r0 : r0 + rc] = ce10
        boot_ce05[r0 : r0 + rc] = ce05

    def _summarize_ext(est: float, draws: np.ndarray) -> Dict[str, float]:
        fin = np.isfinite(draws)
        d = draws[fin]
        r_eff = int(len(d))
        if r_eff == 0:
            raise RuntimeError("No finite bootstrap draws")
        lo, hi = np.quantile(d, [0.025, 0.975])
        blo, bhi = 2.0 * est - hi, 2.0 * est - lo
        p_gr = phipson_smyth_p(int(np.sum(d <= 0.0)), r_eff)
        p_ls = phipson_smyth_p(int(np.sum(d >= 0.0)), r_eff)
        p_two = min(1.0, 2.0 * min(p_gr, p_ls))
        centered = d - est
        p_null = phipson_smyth_p(int(np.sum(np.abs(centered) >= abs(est))), r_eff)
        return {
            "estimate": float(est),
            "boot_se": float(np.std(d, ddof=1)),
            "ci95_low": float(lo),
            "ci95_high": float(hi),
            "basic_ci95_low": float(blo),
            "basic_ci95_high": float(bhi),
            "p_value_greater": float(p_gr),
            "p_value_less": float(p_ls),
            "p_value_two_sided": float(p_two),
            "p_value_null_cent_2s": float(p_null),
            "n": n,
            "n_clusters": n_m,
            "n_blocks": n_b,
        }

    return {
        "mean": _summarize_ext(est_mean, boot_m),
        "ep_loss_rate": _summarize_ext(est_loss, boot_l),
        "es10": _summarize_ext(est_es10, boot_e10),
        "cond_es10": _summarize_ext(est_cond_es10, boot_ce10),
        "cond_es05": _summarize_ext(est_cond_es05, boot_ce05),
    }


def _es10_influence(x: np.ndarray, alpha: float = 0.10) -> Tuple[float, np.ndarray]:
    """Exact empirical value and centered influence function psi_i for ES_alpha."""
    val = es_alpha(x, alpha=alpha)
    q = float(np.quantile(x, alpha))
    # Influence of E[X | X <= q_alpha]: (1/alpha) * (q + min(0, x - q)) - ES_alpha
    psi = (q + np.minimum(0.0, x - q)) / float(alpha) - val
    psi = psi - float(psi.mean())
    return val, psi


def two_way_cgm_and_studentized_test(
    df: pd.DataFrame,
    col_a: str,
    col_b: str,
    metric: str = "mean",
    mandi_col: str = "origin_market_key",
    date_col: str = "date",
    week_block_len: int = 2,
    reps: int = 2000,
    seed: int = 20261117,
) -> Dict[str, float]:
    """Analytic two-way CGM variance, CSS G* effective blocks, null-centered studentized bootstrap-t, and Webb-6 wild block test."""
    from scipy import stats as scipy_stats

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

    atom_at_q10 = False
    if metric == "mean":
        est = float((va - vb).mean())
        psi = (va - vb) - est
    elif metric == "ep_loss_rate":
        la = (va < 0).astype(np.float64)
        lb = (vb < 0).astype(np.float64)
        est = float((la - lb).mean())
        psi = (la - lb) - est
    elif metric == "es10":
        ea, pa = _es10_influence(va, 0.10)
        eb, pb = _es10_influence(vb, 0.10)
        est = float(ea - eb)
        psi = pa - pb
        qa = float(np.quantile(va, 0.10))
        qb = float(np.quantile(vb, 0.10))
        atom_at_q10 = bool((abs(qa) < 1e-9 and float(np.mean(va == 0.0)) > 0.05) or (abs(qb) < 1e-9 and float(np.mean(vb == 0.0)) > 0.05))
    else:
        raise ValueError(f"Unsupported metric for CGM/studentized test: {metric}")

    # Exact cell score sums & counts for analytic CGM and fast studentized bootstrap-t
    cell_psi = np.zeros((n_m, n_b), dtype=np.float64)
    cell_cnt = np.zeros((n_m, n_b), dtype=np.float64)
    np.add.at(cell_psi, (m_codes, b_codes), psi)
    np.add.at(cell_cnt, (m_codes, b_codes), 1.0)

    s_m = cell_psi.sum(axis=1)
    s_b = cell_psi.sum(axis=0)
    # Finite-sample Cameron-Gelbach-Miller (2011) G/(G-1) two-way variance: V_M + V_B - V_MB
    v_m = (float(np.sum(s_m ** 2)) / (n * n)) * (float(n_m) / max(1.0, float(n_m - 1)))
    v_b = (float(np.sum(s_b ** 2)) / (n * n)) * (float(n_b) / max(1.0, float(n_b - 1)))
    n_cells = int(np.sum(cell_cnt > 0))
    v_mb = (float(np.sum(cell_psi ** 2)) / (n * n)) * (float(n_cells) / max(1.0, float(n_cells - 1)))
    v_cgm_raw = v_m + v_b - v_mb
    v_cgm = max(v_cgm_raw, 1e-12)
    se_cgm = float(np.sqrt(v_cgm))

    # Carter-Schnepel-Steigerwald (2017) effective cluster count across blocks & markets
    sb2 = s_b ** 2
    g_star_b = float((sb2.sum() ** 2) / max(1e-24, float(np.sum(sb2 ** 2))))
    sm2 = s_m ** 2
    g_star_m = float((sm2.sum() ** 2) / max(1e-24, float(np.sum(sm2 ** 2))))

    t_obs = float(est / se_cgm)
    p_cgm_norm = float(2.0 * scipy_stats.norm.sf(abs(t_obs)))
    df_b = max(1.0, float(n_b - 1))
    df_gstar = max(1.0, float(g_star_b - 1.0))
    p_cgm_tb = float(2.0 * scipy_stats.t.sf(abs(t_obs), df=df_b))
    p_cgm_gstar = float(2.0 * scipy_stats.t.sf(abs(t_obs), df=df_gstar))

    # Null-centered studentized bootstrap-t (using replicated cluster influence variance SE* per draw)
    if metric == "es10":
        ga = pd.DataFrame({"m": m_codes, "b": b_codes, "v": va}).groupby(["m", "b", "v"], sort=False, as_index=False).size()
        oa = np.argsort(ga["v"].to_numpy(dtype=np.float64), kind="mergesort")
        gma, gba, gva_s, gca = ga["m"].to_numpy(dtype=np.int32)[oa], ga["b"].to_numpy(dtype=np.int32)[oa], ga["v"].to_numpy(dtype=np.float64)[oa], ga["size"].to_numpy(dtype=np.float64)[oa]
        gb_d = pd.DataFrame({"m": m_codes, "b": b_codes, "v": vb}).groupby(["m", "b", "v"], sort=False, as_index=False).size()
        ob = np.argsort(gb_d["v"].to_numpy(dtype=np.float64), kind="mergesort")
        gmb, gbb, gvb_s, gcb = gb_d["m"].to_numpy(dtype=np.int32)[ob], gb_d["b"].to_numpy(dtype=np.int32)[ob], gb_d["v"].to_numpy(dtype=np.float64)[ob], gb_d["size"].to_numpy(dtype=np.float64)[ob]

    rng = np.random.default_rng(seed)
    t_stars = np.empty(reps, dtype=np.float64)
    boot_vals = np.empty(reps, dtype=np.float64)

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
        den = np.einsum("rm,mb,rb->r", m_w, cell_cnt, b_w)
        if np.any(den <= 0.0):
            raise RuntimeError(f"Zero total weight draw in CGM bootstrap ({col_a} vs {col_b})")

        psi_diff = np.einsum("rm,mb,rb->r", m_w, cell_psi, b_w) / den
        if metric == "es10":
            ws_a = m_w[:, gma] * b_w[:, gba] * gca[None, :]
            ws_b = m_w[:, gmb] * b_w[:, gbb] * gcb[None, :]
            est_star = _batch_weighted_es_alpha_presorted(gva_s, ws_a, 0.10) - _batch_weighted_es_alpha_presorted(gvb_s, ws_b, 0.10)
        else:
            est_star = est + psi_diff

        # Weighted CGM influence variance inside bootstrap replicate (exact same finite-sample G/(G-1) scaling as se_cgm!)
        m_scale = float(n_m) / max(1.0, float(n_m - 1))
        b_scale = float(n_b) / max(1.0, float(n_b - 1))
        mb_scale = float(n_cells) / max(1.0, float(n_cells - 1))
        bw_psi = cell_psi @ b_w.T  # (M, rc)
        bw_cnt = cell_cnt @ b_w.T  # (M, rc)
        s_m_star = bw_psi.T - psi_diff[:, None] * bw_cnt.T  # (rc, M)
        v_m_star = (np.sum(m_w * (s_m_star ** 2), axis=1) / (den ** 2)) * m_scale

        mw_psi = (m_w @ cell_psi)  # (rc, B)
        mw_cnt = (m_w @ cell_cnt)  # (rc, B)
        s_b_star = mw_psi - psi_diff[:, None] * mw_cnt
        v_b_star = (np.sum(b_w * (s_b_star ** 2), axis=1) / (den ** 2)) * b_scale

        c_adj = cell_psi[None, :, :] - psi_diff[:, None, None] * cell_cnt[None, :, :]
        w_mb = m_w[:, :, None] * b_w[:, None, :]
        v_mb_star = (np.sum(w_mb * (c_adj ** 2), axis=(1, 2)) / (den ** 2)) * mb_scale

        v_cgm_star = v_m_star + v_b_star - v_mb_star
        v_cgm_star = np.where(v_cgm_star > 1e-12, v_cgm_star, np.maximum(v_m_star, v_b_star))
        se_star = np.sqrt(np.maximum(v_cgm_star, 1e-12))
        boot_vals[r0 : r0 + rc] = est_star
        t_stars[r0 : r0 + rc] = (est_star - est) / se_star

    p_stud_2s = phipson_smyth_p(int(np.sum(np.abs(t_stars) >= abs(t_obs))), reps)
    tq_lo, tq_hi = np.quantile(t_stars, [0.025, 0.975])
    stud_ci_low = float(est - tq_hi * se_cgm)
    stud_ci_high = float(est - tq_lo * se_cgm)

    # One-way block Webb (2023) 6-point wild cluster bootstrap over time blocks on null-centered psi.
    # NOTE: Explicitly 1-way block-only (omits market clustering and breaks down when CSS G*_b < 3,
    # e.g., HP G*_b = 1.54); never treat as a replacement for two-way CGM G* or studentized-t.
    webb_pts = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)], dtype=np.float64)
    rng_w = np.random.default_rng(seed + 777)
    se_1w_b = float(np.sqrt(max(v_b, 1e-12)))
    t_obs_1w = float(est / se_1w_b)
    t_wild = np.empty(reps, dtype=np.float64)
    n_b_arr = cell_cnt.sum(axis=0)
    b_scale = float(n_b) / max(1.0, float(n_b - 1))
    for r0 in range(0, reps, chunk):
        rc = min(chunk, reps - r0)
        w_b = webb_pts[rng_w.integers(0, 6, size=(rc, n_b))]
        w_sum = np.sum(w_b * s_b[None, :], axis=1)
        est_w = w_sum / n
        s_w = w_b * s_b[None, :] - est_w[:, None] * n_b_arr[None, :]
        se_w = np.sqrt(np.maximum((np.sum(s_w ** 2, axis=1) / (n * n)) * b_scale, 1e-12))
        t_wild[r0 : r0 + rc] = est_w / se_w
    p_wild_webb6_1w = phipson_smyth_p(int(np.sum(np.abs(t_wild) >= abs(t_obs_1w))), reps)

    return {
        "estimate": est,
        "se_cgm": se_cgm,
        "se_market": float(np.sqrt(v_m)),
        "se_block": float(np.sqrt(v_b)),
        "v_cgm_floored": float(v_cgm_raw <= 1e-12),
        "g_star_block": g_star_b,
        "g_star_market": g_star_m,
        "g_star_block_warning": bool(g_star_b < 3.0),
        "atom_at_q10": atom_at_q10,
        "t_obs_cgm": t_obs,
        "p_cgm_norm": p_cgm_norm,
        "p_cgm_tb": p_cgm_tb,
        "p_cgm_gstar": p_cgm_gstar,
        "p_stud_2s": p_stud_2s,
        "stud_ci95_low": stud_ci_low,
        "stud_ci95_high": stud_ci_high,
        "p_wild_webb6_1w_block_only": p_wild_webb6_1w,
        "n": n,
        "n_clusters": n_m,
        "n_blocks": n_b,
    }
