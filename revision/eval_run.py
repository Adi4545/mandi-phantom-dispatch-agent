"""Evaluate lagged dispatch rules.

Primary settlement is sequential: on each arrival day the rule sells if an
exact-variety price is recorded, waits one day if any variety of the commodity
is recorded, and otherwise returns. It does not look ahead. The hindsight
settlement, which uses the first exact price within three days, is reported
only as a comparison.

Weather in the primary score and payoff is the NABCONS 20C reference (no live
forecast and no ERA5). A 2024 state-month climatology is a sensitivity.
Live ERA5 is not treated as known at decision time.

Thresholds are chosen on 2025-01-01..2025-05-31 and then frozen.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from revision.es10 import es10
from src.evaluation.bootstrap import two_way_mandi_week_bootstrap

ROOT = Path(__file__).resolve().parents[1]
BASE = {"Tomato": 0.0325, "Onion": 0.0196, "Apple": 0.0164, "Potato": 0.0086}
THETAS = [100, 150, 200, 250, 300, 400, 500]
MARGINS = [0, 50, 100, 150, 200, 250, 300, 400]


def spoil_frac(commodity: np.ndarray, hours: np.ndarray, wait: np.ndarray, tmax, rh, rain) -> np.ndarray:
    base = np.array([BASE.get(c, 0.02) for c in commodity], dtype=np.float64)
    t_eff = np.clip(tmax, 5.0, 48.0)
    rh_eff = np.clip(rh, 20.0, 100.0)
    q10 = 2.0 ** ((t_eff - 20.0) / 10.0)
    rh_f = 1.0 + 0.25 * np.maximum(0.0, (rh_eff - 70.0) / 30.0)
    total_h = np.maximum(1.0, hours + 24.0 * np.maximum(wait, 0))
    bio = base * (total_h / 24.0) * q10 * rh_f
    bio = bio + np.where(rain >= 35.0, 0.02, 0.0)
    return np.clip(bio, 0.0, 0.55)


def _wx(df: pd.DataFrame, mode: str):
    n = len(df)
    if mode == "none":
        return np.full(n, 20.0), np.full(n, 65.0), np.zeros(n)
    if mode == "clim":
        return (
            df["clim_tmax"].fillna(20.0).to_numpy(dtype=np.float64),
            df["clim_rh"].fillna(65.0).to_numpy(dtype=np.float64),
            df["clim_rain"].fillna(0.0).to_numpy(dtype=np.float64),
        )
    raise ValueError(mode)


def settle(df: pd.DataFrame, how: str, weather: str, div: float, disc: float) -> np.ndarray:
    """Return modeled net gain versus selling locally, INR/qtl, one value per row."""
    n = len(df)
    comm = df["Commodity"].to_numpy()
    hours = df["truck_hours"].to_numpy(dtype=np.float64)
    freight = df["freight_road"].to_numpy(dtype=np.float64)
    local = df["local_price"].to_numpy(dtype=np.float64)
    tmax, rh, rain = _wx(df, weather)
    p = [df[c].to_numpy(dtype=np.float64) for c in ("dest_modal_d0", "dest_modal_d1", "dest_modal_d2")]
    pmin = [df[c].to_numpy(dtype=np.float64) for c in ("dest_min_d0", "dest_min_d1", "dest_min_d2")]
    any_min = [df[c].to_numpy(dtype=np.float64) for c in ("any_min_d0", "any_min_d1", "any_min_d2")]
    out = np.empty(n, dtype=np.float64)

    def exact_delta(i, wait):
        sp = spoil_frac(comm[i], hours[i], np.full(i.sum(), wait), tmax[i], rh[i], rain[i])
        sale = p[wait][i]
        # No live rain blend in none/clim modes (rain is 0 or a climatology, not that day's ERA5).
        return sale * (1.0 - sp) - freight[i] - 25.0 * wait - local[i]

    def missing_delta(i, wait, day):
        sp = spoil_frac(comm[i], hours[i], np.full(i.sum(), wait), tmax[i], rh[i], rain[i])
        amin = any_min[day][i]
        use_other = np.isfinite(amin) & (amin > 0)
        delta = np.empty(i.sum(), dtype=np.float64)
        sale = amin * (1.0 - disc)
        delta[use_other] = sale[use_other] * (1.0 - sp[use_other]) - freight[i][use_other] - 25.0 * wait - local[i][use_other]
        delta[~use_other] = -div * freight[i][~use_other] - local[i][~use_other] * sp[~use_other] - 25.0 * wait
        return delta

    if how == "hindsight":
        taken = np.zeros(n, dtype=bool)
        for w in range(3):
            ok = (~taken) & np.isfinite(p[w]) & (p[w] > 0)
            out[ok] = exact_delta(ok, w)
            taken |= ok
        rest = ~taken
        # Original hindsight missing branch does not add detention.
        sp = spoil_frac(comm[rest], hours[rest], np.zeros(rest.sum()), tmax[rest], rh[rest], rain[rest])
        amin = any_min[0][rest]
        use_other = np.isfinite(amin) & (amin > 0)
        delta = np.empty(rest.sum(), dtype=np.float64)
        sale = amin * (1.0 - disc)
        delta[use_other] = sale[use_other] * (1.0 - sp[use_other]) - freight[rest][use_other] - local[rest][use_other]
        delta[~use_other] = -div * freight[rest][~use_other] - local[rest][~use_other] * sp[~use_other]
        out[rest] = delta
        return out

    if how != "sequential":
        raise ValueError(how)
    # Day by day. Wait only if some variety of this commodity is recorded that day.
    taken = np.zeros(n, dtype=bool)
    for day in range(3):
        exact = (~taken) & np.isfinite(p[day]) & (p[day] > 0)
        out[exact] = exact_delta(exact, day)
        taken |= exact
        if day == 2:
            rest = ~taken
            out[rest] = missing_delta(rest, 2, 2)
            break
        active = np.isfinite(any_min[day]) & (any_min[day] > 0)
        give_up = (~taken) & (~active)
        out[give_up] = missing_delta(give_up, day, day)
        taken |= give_up
    return out


def _pick(df: pd.DataFrame, score: np.ndarray, eligible: np.ndarray) -> pd.DataFrame:
    """One row per episode. Ineligible rows stay in the table so the episode is counted as a refusal."""
    work = df[["episode_id", "date", "origin_market_key", "State", "Commodity", "dest_market"]].copy()
    work["score"] = np.where(eligible, score, -1e18)
    work["eligible"] = eligible
    work["_i"] = np.arange(len(df))
    work = work.sort_values(["episode_id", "score"], ascending=[True, False])
    top = work.groupby("episode_id", as_index=False).head(1)
    y = df["y"].to_numpy(dtype=np.float64)
    top["y"] = y[top["_i"].to_numpy()]
    return top


def summarize(name: str, chosen: pd.DataFrame, dnet: np.ndarray) -> dict:
    loss = dnet < 0
    dispatched = chosen["eligible"].to_numpy()
    # Abstain -> 0. The chosen row still carries a destination score; replace with 0.
    y = np.where(dispatched, dnet, 0.0)
    n_d = int(dispatched.sum())
    return {
        "policy": name,
        "n": int(len(y)),
        "dispatch_rate": round(float(dispatched.mean()), 4) if len(y) else None,
        "n_dispatch": n_d,
        "mean": round(float(y.mean()), 2) if len(y) else None,
        "loss_rate": round(float(loss[dispatched].mean()), 4) if n_d else None,
        "es10": round(es10(y), 2),
        "loss_given_loss": round(float(y[dispatched & loss].mean()), 2) if np.any(dispatched & loss) else None,
    }


def attach_payoffs(df: pd.DataFrame, how: str, weather: str, div: float, disc: float) -> pd.DataFrame:
    out = df.copy()
    out["y"] = settle(out, how, weather, div, disc)
    return out


def run() -> None:
    root = ROOT
    path = root / "revision" / "results" / "lagged_candidates.parquet"
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    # Top 5 by lagged spread among quotes that are actually lagged.
    df = df[df["lag_price"].notna() & (df["lag_spread"] > 100)].copy()
    df = df.sort_values(["episode_id", "lag_spread"], ascending=[True, False])
    df["_rk"] = df.groupby("episode_id").cumcount()
    df = df[df["_rk"] < 5].copy()
    df["split"] = np.where(df["date"] <= "2025-05-31", "val", "test")
    df = attach_payoffs(df, "sequential", "none", 1.5, 0.10)

    def eval_split(sub: pd.DataFrame, b2_theta: float, margin: float, score_col: str) -> dict:
        # Map row payoff. score_col is the decision score already on the frame.
        b1 = _pick(sub, sub["lag_spread"].to_numpy(), np.ones(len(sub), dtype=bool))
        y_b1 = b1
        age = sub["lag_age"].to_numpy()
        net = (sub["lag_price"] - sub["local_price"] - sub["freight_road"]).to_numpy()
        b2_ok = (age <= 1) & (net > b2_theta)
        b2 = _pick(sub, net, b2_ok)
        y_b2 = b2
        if score_col == "net_road":
            sc = net
            ok = (age >= 1) & (age <= 3) & (sc > margin)
        elif score_col == "net_euclid":
            sc = (sub["lag_price"] - sub["local_price"] - sub["freight_euclid"]).to_numpy()
            ok = (age >= 1) & (age <= 3) & (sc > margin)
        elif score_col == "net_clim":
            # Expected spoil cost at 2024 climatology, zero wait, subtracted from the lagged net.
            sp = spoil_frac(
                sub["Commodity"].to_numpy(),
                sub["truck_hours"].to_numpy(dtype=np.float64),
                np.zeros(len(sub)),
                sub["clim_tmax"].fillna(20).to_numpy(dtype=np.float64),
                sub["clim_rh"].fillna(65).to_numpy(dtype=np.float64),
                sub["clim_rain"].fillna(0).to_numpy(dtype=np.float64),
            )
            sc = net - sub["lag_price"].to_numpy(dtype=np.float64) * sp
            ok = (age >= 1) & (age <= 3) & (sc > margin)
        else:
            raise ValueError(score_col)
        mg = _pick(sub, sc, ok)
        y_mg = mg
        # Align to the episode list of this split (episodes that have a lagged shortlist).
        return {
            "B1": summarize("B1", y_b1, y_b1["y"].to_numpy()),
            "B2": summarize("B2", y_b2, y_b2["y"].fillna(0).to_numpy()),
            "MG": summarize("MG", y_mg, y_mg["y"].fillna(0).to_numpy()),
            "frames": {"B1": y_b1, "B2": y_b2, "MG": y_mg},
        }

    val = df[df["split"] == "val"]
    # Tune conservative B2 and the cautious margin on validation only.
    best_b2 = None
    for th in THETAS:
        rec = eval_split(val, th, 100.0, "net_road")["B2"]
        key = (rec["loss_rate"] if rec["loss_rate"] is not None else 1.0, -(rec["mean"] or -1e9))
        if best_b2 is None or key < best_b2[0]:
            best_b2 = (key, th, rec)
    b2_theta = best_b2[1]
    best_m = None
    for m in MARGINS:
        rec = eval_split(val, b2_theta, m, "net_road")["MG"]
        if rec["dispatch_rate"] is None or rec["dispatch_rate"] < 0.25:
            continue
        key = (rec["loss_rate"], -(rec["mean"]))
        if best_m is None or key < best_m[0]:
            best_m = (key, m, rec)
    if best_m is None:
        # Fall back to the margin with the lowest loss rate, ignoring the dispatch floor.
        for m in MARGINS:
            rec = eval_split(val, b2_theta, m, "net_road")["MG"]
            key = (rec["loss_rate"] if rec["loss_rate"] is not None else 1.0, -(rec["mean"] or -1e9))
            if best_m is None or key < best_m[0]:
                best_m = (key, m, rec)
    margin = best_m[1]

    test = df[df["split"] == "test"]
    primary = eval_split(test, b2_theta, margin, "net_road")
    # Also the pre-registered-style B2 at theta 100, not the tuned one.
    b2_100 = eval_split(test, 100.0, margin, "net_road")
    euclid = eval_split(test, b2_theta, margin, "net_euclid")
    clim = eval_split(test, b2_theta, margin, "net_clim")

    # Hindsight settlement on the same chosen trips (positional index into `test`).
    hind = attach_payoffs(test, "hindsight", "none", 1.5, 0.10)
    hind_y = hind["y"].to_numpy(dtype=np.float64)

    def rescore(frame: pd.DataFrame) -> dict:
        yy = hind_y[frame["_i"].to_numpy()]
        return summarize("x", frame, yy)

    settlement_rows = []
    for label, frame in primary["frames"].items():
        a = summarize(label, frame, frame["y"].fillna(0).to_numpy())
        a["settlement"] = "sequential"
        b = rescore(frame)
        b["policy"] = label
        b["settlement"] = "hindsight"
        settlement_rows.extend([a, b])

    # Risk-coverage for the cautious rule and for B2.
    curve = []
    for m in list(range(0, 801, 25)):
        rec = eval_split(test, 100.0, float(m), "net_road")["MG"]
        rec["knob"] = m
        rec["family"] = "MG_margin"
        curve.append(rec)
    for th in list(range(0, 801, 25)):
        rec = eval_split(test, float(th), margin, "net_road")["B2"]
        rec["knob"] = th
        rec["family"] = "B2_theta"
        curve.append(rec)

    # Missing-price grid on the frozen choices, by crop and overall.
    sens = []
    for div in (0.0, 0.5, 1.0, 1.5):
        for disc in (0.0, 0.05, 0.10):
            alt = attach_payoffs(test, "sequential", "none", div, disc)
            # evaluate using alt y
            backed = test.copy()
            backed["y"] = alt["y"]
            # monkeypatch by replacing test y
            saved = test["y"].copy()
            test["y"] = alt["y"].to_numpy()
            rec = eval_split(test, b2_theta, margin, "net_road")
            for pol in ("B1", "B2", "MG"):
                row = dict(rec[pol])
                row["div"] = div
                row["disc"] = disc
                row["slice"] = "ALL"
                sens.append(row)
            for crop, g in test.groupby("Commodity"):
                rg = eval_split(g, b2_theta, margin, "net_road")
                for pol in ("B1", "B2", "MG"):
                    row = dict(rg[pol])
                    row["div"] = div
                    row["disc"] = disc
                    row["slice"] = str(crop)
                    sens.append(row)
            for state, g in test.groupby("State"):
                rg = eval_split(g, b2_theta, margin, "net_road")
                row = dict(rg["MG"])
                row["div"] = div
                row["disc"] = disc
                row["slice"] = "state:" + str(state)
                sens.append(row)
            test["y"] = saved

    # Crop and state at the primary penalty, with bootstrap CIs for MG-B2 and MG-B1.
    frames = primary["frames"]
    base = frames["MG"][["episode_id", "date", "origin_market_key", "State", "Commodity", "eligible", "dest_market"]].copy()
    base["mg"] = np.where(frames["MG"]["eligible"], frames["MG"]["y"], 0.0)
    b2y = frames["B2"][["episode_id", "eligible", "y", "dest_market"]].rename(
        columns={"eligible": "b2_disp", "y": "b2y", "dest_market": "b2_dest"}
    )
    b1y = frames["B1"][["episode_id", "eligible", "y"]].rename(columns={"eligible": "b1_disp", "y": "b1y"})
    paired = base.merge(b2y, on="episode_id").merge(b1y, on="episode_id")
    paired["b2"] = np.where(paired["b2_disp"], paired["b2y"], 0.0)
    paired["b1"] = np.where(paired["b1_disp"], paired["b1y"], 0.0)
    boot = []
    for label, a, b in (("MG_minus_B2", "mg", "b2"), ("MG_minus_B1", "mg", "b1")):
        res = two_way_mandi_week_bootstrap(paired, a, b, reps=2000, seed=20261117, direction="greater")
        boot.append({"contrast": label, "cluster": "origin_x_2week", **{k: res[k] for k in ("estimate", "ci95_low", "ci95_high", "p_value", "p_value_basic", "n")}})
    # Destination x week, using B2's destination when it dispatched, else origin.
    paired["dest_key"] = np.where(paired["b2_disp"], paired["b2_dest"], paired["origin_market_key"])
    for label, a, bcol in (("MG_minus_B2", "mg", "b2"), ("MG_minus_B1", "mg", "b1")):
        res = two_way_mandi_week_bootstrap(
            paired, a, bcol, mandi_col="dest_key", reps=2000, seed=20261117, direction="greater"
        )
        boot.append({"contrast": label, "cluster": "b2dest_or_origin_x_2week", **{k: res[k] for k in ("estimate", "ci95_low", "ci95_high", "p_value", "p_value_basic", "n")}})

    by = []
    for col in ("Commodity", "State"):
        for gval, g in paired.groupby(col):
            by.append(
                {
                    "slice_type": col,
                    "slice": gval,
                    "n": int(len(g)),
                    "mg_mean": round(float(g["mg"].mean()), 2),
                    "b2_mean": round(float(g["b2"].mean()), 2),
                    "b1_mean": round(float(g["b1"].mean()), 2),
                    "mg_minus_b2": round(float((g["mg"] - g["b2"]).mean()), 2),
                    "mg_es10": round(es10(g["mg"].to_numpy()), 2),
                    "b2_es10": round(es10(g["b2"].to_numpy()), 2),
                    "mg_loss_rate": round(float(((g["mg"] < 0)).mean()), 4),
                }
            )

    out = root / "revision" / "results"
    pd.DataFrame([primary["B1"], primary["B2"], primary["MG"], b2_100["B2"]]).assign(note="primary_sequential_noweather").to_csv(
        out / "main_table.csv", index=False
    )
    # Fix B2_100 label
    main = pd.DataFrame(
        [
            {**primary["B1"], "role": "B1_lagged_screen"},
            {**b2_100["B2"], "role": "B2_theta100"},
            {**primary["B2"], "role": "B2_val_conservative"},
            {**primary["MG"], "role": "cautious_T1_T2_T4"},
            {**euclid["MG"], "role": "ablation_euclid_instead_of_road"},
            {**clim["MG"], "role": "ablation_plus_2024_climatology"},
        ]
    )
    main.to_csv(out / "main_table.csv", index=False)
    pd.DataFrame(settlement_rows).to_csv(out / "settlement_compare.csv", index=False)
    pd.DataFrame(curve).to_csv(out / "risk_coverage.csv", index=False)
    pd.DataFrame(sens).to_csv(out / "missing_sensitivity.csv", index=False)
    pd.DataFrame(by).to_csv(out / "by_crop_state.csv", index=False)
    pd.DataFrame(boot).to_csv(out / "bootstrap.csv", index=False)
    meta = {
        "b2_theta_frozen_on_val": b2_theta,
        "margin_frozen_on_val": margin,
        "val_b2": best_b2[2],
        "val_mg": best_m[2],
        "test_n_episodes": int(paired["episode_id"].nunique()),
        "weather_primary": "none_20C_reference",
        "settlement_primary": "sequential",
        "div_primary": 1.5,
        "disc_primary": 0.10,
        "exploratory": False,
        "note": "Thresholds frozen on Jan-May 2025. Jun 2025-Apr 2026 is the test window. No untouched window remains beyond this split. Stage I H2 on the old same-day design stays inconclusive and is not re-opened here.",
    }
    (out / "summary.json").write_text(json.dumps(meta, indent=2, default=float))
    print(main.to_string(index=False))
    print(json.dumps(meta, indent=2, default=float))
    print(pd.DataFrame(boot).to_string(index=False))


if __name__ == "__main__":
    run()
