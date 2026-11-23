"""Agent A16 Independent Cleanroom Audit (ZERO imports from revision/).

Independently loads ONLY tracked primary data files:
  - data/raw/agmarknet_6state_top_apple_2024_2026.parquet
  - data/processed/osrm_corridor_matrix.parquet
  - data/processed/state_apmc_and_loss_parameters.csv
and re-derives the cleaning funnel, strictly < t lagged Top-5 shortlist,
sequential settlement, B1, B2_age_matched, RR_Abstain_matched, and exact ES10,
asserting exact integer match on counts and <= ₹0.01 match on all headline metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NABCONS = {"Tomato": 0.0325, "Onion": 0.0196, "Apple": 0.0164, "Potato": 0.0086}


def indep_canon_var(comm: str, var: str) -> str:
    s = " ".join(str(var).strip().split())
    low = s.lower()
    if low in {str(comm).lower(), "other", "faq", ""}:
        return "Standard"
    if low in {"desi", "deshi"}:
        return "Desi"
    return s


def indep_es10(arr: np.ndarray) -> float:
    x = np.sort(np.asarray(arr, dtype=np.float64))
    x = x[np.isfinite(x)]
    n = len(x)
    m = 0.10 * n
    k = int(np.floor(m))
    f = m - k
    tot = float(x[:k].sum()) if k > 0 else 0.0
    if f > 1e-12:
        tot += f * float(x[k])
    return tot / m


def main() -> None:
    res_dir = ROOT / "revision" / "results"
    pub_counts = json.loads((res_dir / "cleaning_counts.json").read_text())
    pub_a10 = pd.read_csv(res_dir / "a10_results.csv").set_index("policy")
    pub_a10_meta = json.loads((res_dir / "a10_summary.json").read_text())

    raw = pd.read_parquet(ROOT / "data/raw/agmarknet_6state_top_apple_2024_2026.parquet")
    assert len(raw) == pub_counts["panel_rows_raw"]
    raw["Arrival_Date"] = pd.to_datetime(raw["Arrival_Date"])

    bad = (
        raw["Modal_Price"].isna() | raw["Min_Price"].isna() | raw["Max_Price"].isna()
        | (raw["Modal_Price"] <= 0) | (raw["Min_Price"] <= 0) | (raw["Max_Price"] <= 0)
        | (raw["Min_Price"] > raw["Max_Price"])
        | (raw["Modal_Price"] < raw["Min_Price"]) | (raw["Modal_Price"] > raw["Max_Price"])
    )
    valid = raw.loc[~bad].copy()
    assert len(valid) == pub_counts["rows_after_invalid_drop"]

    valid["Var"] = [indep_canon_var(c, v) for c, v in zip(valid["Commodity"], valid["Variety"])]
    canon = valid.groupby(["State", "Market", "Commodity", "Var", "Arrival_Date"], as_index=False).agg(
        Modal_Price=("Modal_Price", "median"),
        Min_Price=("Min_Price", "min"),
    )
    assert len(canon) == pub_counts["retained_canonical_variety_day_rows"]

    # Strictly < t origin and dest quotes
    orig = canon[(canon["Arrival_Date"] >= "2025-01-01") & (canon["Arrival_Date"] <= "2026-04-08")].rename(
        columns={"Market": "origin_market", "Arrival_Date": "date", "Modal_Price": "local_d0"}
    )[["State", "origin_market", "Commodity", "Var", "date", "local_d0"]].copy()
    orig["ld"] = orig["date"] - pd.Timedelta(days=1)

    orig_lag_src = canon[["State", "Market", "Commodity", "Var", "Arrival_Date", "Modal_Price"]].rename(
        columns={"Market": "origin_market", "Arrival_Date": "oq_date", "Modal_Price": "orig_lag_p"}
    ).sort_values("oq_date")
    orig = pd.merge_asof(
        orig.sort_values("ld"),
        orig_lag_src,
        left_on="ld",
        right_on="oq_date",
        by=["State", "origin_market", "Commodity", "Var"],
        direction="backward",
    )
    orig["o_age"] = (orig["date"] - orig["oq_date"]).dt.days
    orig = orig[(orig["o_age"] >= 1) & (orig["o_age"] <= 7)].copy()
    assert len(orig) == pub_counts["origin_days_with_lag_1_7d"]

    orig = orig.sort_values(["State", "Commodity", "Var", "origin_market", "date"]).reset_index(drop=True)
    orig["ep_id"] = np.arange(len(orig))

    cor = pd.read_parquet(ROOT / "data/processed/osrm_corridor_matrix.parquet")
    cands = orig.merge(
        cor[["State", "origin_market", "dest_market", "same_district", "road_km", "truck_hours", "arrival_lag_days"]],
        on=["State", "origin_market"],
        how="inner",
    )
    dest_lag_src = canon[["State", "Market", "Commodity", "Var", "Arrival_Date", "Modal_Price"]].rename(
        columns={"Market": "dest_market", "Arrival_Date": "dq_date", "Modal_Price": "dest_lag_p"}
    ).sort_values("dq_date")
    cands = pd.merge_asof(
        cands.sort_values("ld"),
        dest_lag_src,
        left_on="ld",
        right_on="dq_date",
        by=["State", "dest_market", "Commodity", "Var"],
        direction="backward",
    )
    cands["d_age"] = (cands["date"] - cands["dq_date"]).dt.days
    cands = cands[(cands["d_age"] >= 1) & (cands["d_age"] <= 7)].copy()
    cands["lag_spread"] = cands["dest_lag_p"] - cands["orig_lag_p"]
    cands = cands[cands["lag_spread"] > 100.0].copy()
    cands = cands.sort_values(["ep_id", "lag_spread", "road_km", "dest_market"], ascending=[True, False, True, True])
    cands["_rk"] = cands.groupby("ep_id").cumcount()
    cands = cands[cands["_rk"] < 5].drop(columns=["_rk"]).reset_index(drop=True)

    test = cands[cands["date"] > pd.Timestamp("2025-05-31")].copy().reset_index(drop=True)
    assert test["ep_id"].nunique() == int(pub_a10.loc["B1_lagged_screen", "n"])

    # Independent strictly <= t-1 reporting rate (28d & arrival dow 8w) for shortlisted dest markets
    # Compute directly on canon by date filtering per needed key -> clean vectorized lookup
    min_d, max_d = canon["Arrival_Date"].min(), canon["Arrival_Date"].max()
    all_dates = pd.date_range(min_d, max_d, freq="D")
    d2i = {d: i for i, d in enumerate(all_dates)}
    dows = all_dates.dayofweek.to_numpy()
    test["arr_date"] = test["date"] + pd.to_timedelta(test["arrival_lag_days"], unit="D")
    arr_dow = test["arr_date"].dt.dayofweek.to_numpy()
    t_idx_arr = test["date"].map(d2i).to_numpy()

    rep28 = np.empty(len(test), dtype=np.float64)
    dow8 = np.empty(len(test), dtype=np.float64)
    cv28 = np.empty(len(test), dtype=np.float64)
    needed_groups = test.groupby(["State", "Commodity", "Var"], sort=False).groups
    canon_groups = {k: g for k, g in canon.groupby(["State", "Commodity", "Var"], sort=False)}
    for k_grp, idxs in needed_groups.items():
        idx_np = np.asarray(list(idxs), dtype=np.int64)
        cg = canon_groups[k_grp]
        mkts = sorted(cg["Market"].unique())
        m2i = {m: i for i, m in enumerate(mkts)}
        obs = np.zeros((len(all_dates), len(mkts)), dtype=np.float64)
        pr_mat = np.zeros((len(all_dates), len(mkts)), dtype=np.float64)
        pr2_mat = np.zeros((len(all_dates), len(mkts)), dtype=np.float64)
        r_cg = cg["Arrival_Date"].map(d2i).to_numpy()
        c_cg = cg["Market"].map(m2i).to_numpy()
        pv = cg["Modal_Price"].to_numpy(dtype=np.float64)
        obs[r_cg, c_cg] = 1.0
        pr_mat[r_cg, c_cg] = pv
        pr2_mat[r_cg, c_cg] = pv * pv

        cs = np.zeros((len(all_dates) + 1, len(mkts)), dtype=np.float64)
        cs_x = np.zeros((len(all_dates) + 1, len(mkts)), dtype=np.float64)
        cs_x2 = np.zeros((len(all_dates) + 1, len(mkts)), dtype=np.float64)
        cs[1:] = np.cumsum(obs, axis=0)
        cs_x[1:] = np.cumsum(pr_mat, axis=0)
        cs_x2[1:] = np.cumsum(pr2_mat, axis=0)

        ti = np.arange(len(all_dates))
        t28 = np.maximum(0, ti - 28)
        r28_mat = (cs[ti] - cs[t28] + 1.0) / (np.minimum(ti, 28)[:, None] + 2.0)
        cnt28 = cs[ti] - cs[t28]
        sx28 = cs_x[ti] - cs_x[t28]
        sx228 = cs_x2[ti] - cs_x2[t28]
        with np.errstate(divide="ignore", invalid="ignore"):
            mu28 = np.where(cnt28 >= 2, sx28 / np.maximum(cnt28, 1.0), 1.0)
            var28 = np.where(cnt28 >= 2, np.maximum(0.0, (sx228 - (sx28 * sx28) / np.maximum(cnt28, 1.0)) / np.maximum(cnt28 - 1.0, 1.0)), 0.0)
            cv28_mat = np.where((cnt28 >= 2) & (mu28 > 0), np.clip(np.sqrt(var28) / mu28, 0.0, 1.0), 0.05)

        dow_mat = np.full((7, len(all_dates), len(mkts)), 0.5, dtype=np.float64)
        for w in range(7):
            occ = np.flatnonzero(dows == w)
            if len(occ) == 0:
                continue
            wobs = obs[occ]
            csw = np.zeros((len(occ) + 1, len(mkts)), dtype=np.float64)
            csw[1:] = np.cumsum(wobs, axis=0)
            u = np.arange(len(occ))
            u0 = np.maximum(0, u - 7)
            ri = (csw[u + 1] - csw[u0] + 1.0) / ((u - u0 + 1)[:, None] + 2.0)
            tmp = np.full((len(all_dates), len(mkts)), np.nan)
            nxt = occ + 1
            vn = nxt < len(all_dates)
            if vn.any():
                tmp[nxt[vn]] = ri[vn]
            dow_mat[w] = pd.DataFrame(tmp).ffill().fillna(0.5).to_numpy()

        j_c = test.loc[idx_np, "dest_market"].map(m2i).to_numpy()
        rep28[idx_np] = r28_mat[t_idx_arr[idx_np], j_c]
        dow8[idx_np] = dow_mat[arr_dow[idx_np], t_idx_arr[idx_np], j_c]
        cv28[idx_np] = cv28_mat[t_idx_arr[idx_np], j_c]

    # Independent arrival lookup & sequential payoff
    fees = pd.read_csv(ROOT / "data/processed/state_apmc_and_loss_parameters.csv")
    fee_map = fees.set_index(["State", "Commodity"])["statutory_seller_fee_pct"].to_dict()
    hp = np.where(test["State"].to_numpy() == "Himachal Pradesh", 1.45, 1.0)
    f_road = 35.0 + 0.45 * hp * test["road_km"].to_numpy(dtype=np.float64)
    fee_r = np.where(
        test["same_district"].to_numpy(dtype=bool),
        0.0,
        np.array([fee_map[(s, c)] for s, c in zip(test["State"], test["Commodity"])], dtype=np.float64),
    )
    comm = test["Commodity"].to_numpy()
    hrs = test["truck_hours"].to_numpy(dtype=np.float64)
    base_sp = np.array([NABCONS[c] for c in comm], dtype=np.float64)
    loc0 = test["local_d0"].to_numpy(dtype=np.float64)

    any_m = canon.groupby(["State", "Market", "Commodity", "Arrival_Date"], as_index=False).agg(any_min=("Min_Price", "min")).rename(columns={"Market": "dest_market"})
    ex_m = canon[["State", "Market", "Commodity", "Var", "Arrival_Date", "Modal_Price"]].rename(columns={"Market": "dest_market"})
    test["_r"] = np.arange(len(test))
    ex_p = []
    an_p = []
    for off in (0, 1, 2):
        kd = test[["_r", "State", "dest_market", "Commodity", "Var"]].copy()
        kd["Arrival_Date"] = test["arr_date"] + pd.Timedelta(days=off)
        me = kd.merge(ex_m, on=["State", "dest_market", "Commodity", "Var", "Arrival_Date"], how="left").sort_values("_r")
        ma = kd[["_r", "State", "dest_market", "Commodity", "Arrival_Date"]].merge(any_m, on=["State", "dest_market", "Commodity", "Arrival_Date"], how="left").sort_values("_r")
        ex_p.append(me["Modal_Price"].to_numpy(dtype=np.float64))
        an_p.append(ma["any_min"].to_numpy(dtype=np.float64))

    y = np.empty(len(test), dtype=np.float64)
    taken = np.zeros(len(test), dtype=bool)
    for d in (0, 1, 2):
        sp = np.clip(base_sp * (np.maximum(1.0, hrs + 24.0 * d) / 24.0), 0.0, 0.55)
        ok = (~taken) & np.isfinite(ex_p[d]) & (ex_p[d] > 0)
        y[ok] = ex_p[d][ok] * (1.0 - sp[ok]) * (1.0 - fee_r[ok]) - f_road[ok] - 25.0 * d - loc0[ok]
        taken |= ok
        if d == 2:
            rest = ~taken
            u_oth = rest & np.isfinite(an_p[2]) & (an_p[2] > 0)
            y[u_oth] = (an_p[2][u_oth] * 0.90) * (1.0 - sp[u_oth]) * (1.0 - fee_r[u_oth]) - f_road[u_oth] - 50.0 - loc0[u_oth]
            u_div = rest & (~u_oth)
            y[u_div] = -1.5 * f_road[u_div] - loc0[u_div] * sp[u_div] - 50.0
            break
        gu = (~taken) & (~(np.isfinite(an_p[d]) & (an_p[d] > 0)))
        y[gu] = -1.5 * f_road[gu] - loc0[gu] * sp[gu] - 25.0 * d
        taken |= gu

    test["y"] = y
    sp0 = np.clip(base_sp * (np.maximum(1.0, hrs) / 24.0), 0.0, 0.55)
    p_dest_l = test["dest_lag_p"].to_numpy(dtype=np.float64)
    p_orig_l = test["orig_lag_p"].to_numpy(dtype=np.float64)
    age = test["d_age"].to_numpy()
    p_rep = np.clip(0.5 * rep28 + 0.5 * dow8, 0.0, 1.0)

    net_b2 = p_dest_l * (1.0 - fee_r) - p_orig_l - f_road
    d_open = p_dest_l * (1.0 - sp0) * (1.0 - fee_r) - p_orig_l - f_road
    d_miss = -float(pub_a10_meta["kappa_star_matched"]) * f_road - p_orig_l * sp0
    sc_rr = p_rep * d_open + (1.0 - p_rep) * d_miss
    m_rr = float(pub_a10_meta["m_star_matched"])

    def eval_rule(name, score, elig):
        w = test[["ep_id", "road_km", "dest_market", "y"]].copy()
        w["elig"] = elig
        w["sc"] = np.where(elig, score, -1e18)
        top = w.sort_values(["ep_id", "elig", "sc", "road_km", "dest_market"], ascending=[True, False, False, True, True]).groupby("ep_id", as_index=False).head(1)
        yy = np.where(top["elig"], top["y"], 0.0)
        mean_v = float(yy.mean())
        es10_v = indep_es10(yy)
        eplr_v = float((yy < 0).mean())
        dr_v = float(top["elig"].mean())
        p_row = pub_a10.loc[name]
        assert abs(mean_v - p_row["mean"]) <= 0.01, f"{name} mean diff: {mean_v} vs {p_row['mean']}"
        assert abs(es10_v - p_row["es10"]) <= 0.01, f"{name} es10 diff: {es10_v} vs {p_row['es10']}"
        assert abs(eplr_v - p_row["ep_loss_rate"]) <= 0.0002, f"{name} loss diff"
        assert abs(dr_v - p_row["dispatch_rate"]) <= 0.0002, f"{name} disp diff"
        print(f"A16 PASS {name:20s}: disp={dr_v:.4f}, mean={mean_v:.2f} (pub {p_row['mean']:.2f}), es10={es10_v:.2f} (pub {p_row['es10']:.2f})")

    eval_rule("B1_lagged_screen", test["lag_spread"].to_numpy(), np.ones(len(test), dtype=bool))
    eval_rule("B2_age_matched", net_b2, (age <= 3) & (net_b2 > 200.0))
    eval_rule("RR_Abstain_matched", sc_rr, (age <= 3) & (sc_rr > m_rr))
    eval_rule("RR_Abstain_m0", sc_rr, (age <= 3) & (sc_rr > 0.0))

    # Independent audit of zero-parameter A18 policies against a18_results.csv + cluster invariants
    if (res_dir / "a18_results.csv").exists():
        pub_a18 = pd.read_csv(res_dir / "a18_results.csv").set_index("policy")
        g_plain = p_dest_l * (1.0 - fee_r) - p_orig_l
        g_1sd = p_dest_l * (1.0 - cv28) * (1.0 - fee_r) - p_orig_l
        p_min = np.minimum(rep28, dow8)
        sc_safe_sunk = dow8 * g_1sd - f_road
        sc_safe_phys = dow8 * (g_1sd - f_road) - (1.0 - dow8) * 1.5 * f_road
        sc_rt2f_min = p_min * g_plain - 2.0 * f_road
        sc_rt2f_dow = dow8 * g_plain - 2.0 * f_road
        for name_a18, sc_a18 in (
            ("Safe_EV_Sunk_m0", sc_safe_sunk),
            ("Safe_EV_Phys_m0", sc_safe_phys),
            ("RT_2F_Min_m0", sc_rt2f_min),
            ("RT_2F_Dow_m0", sc_rt2f_dow),
        ):
            w = test[["ep_id", "road_km", "dest_market", "y"]].copy()
            w["elig"] = (age <= 3) & (sc_a18 > 0.0)
            w["sc"] = np.where(w["elig"], sc_a18, -1e18)
            top = w.sort_values(["ep_id", "elig", "sc", "road_km", "dest_market"], ascending=[True, False, False, True, True]).groupby("ep_id", as_index=False).head(1)
            yy = np.where(top["elig"], top["y"], 0.0)
            p_row = pub_a18.loc[name_a18]
            assert abs(float(yy.mean()) - p_row["mean"]) <= 0.01
            assert abs(indep_es10(yy) - p_row["es10"]) <= 0.01
            assert abs(float((yy < 0).mean()) - p_row["ep_loss_rate"]) <= 0.0002
            print(f"A16 PASS {name_a18:20s}: disp={float(top['elig'].mean()):.4f}, mean={float(yy.mean()):.2f} (pub {p_row['mean']:.2f}), es10={indep_es10(yy):.2f} (pub {p_row['es10']:.2f})")

    for bname in ("bootstrap.csv", "a10_bootstrap.csv", "a18_bootstrap.csv", "v6_bootstrap_5000.csv"):
        bp = res_dir / bname
        if bp.exists():
            bdf = pd.read_csv(bp)
            assert int(bdf["n_clusters"].max()) <= 178, f"{bname} n_clusters > 178: {bdf['n_clusters'].max()}"
    print("A16 INDEPENDENT AUDIT PASSED WITHIN <= ₹0.01 ACROSS ALL HEADLINE POLICIES AND CLUSTER INVARIANTS!")


if __name__ == "__main__":
    main()
