"""Strict R3 decision-time firewall, cleaning funnel, fee-base, and edge-case tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from revision.build_variant import (
    SimParams,
    build_lagged_candidates_from_frames,
    compute_cleaning_funnel,
    spoil_frac_ref,
)

ROOT = Path(__file__).resolve().parents[1]


def test_cleaning_funnel_drops_invalid_and_reconciles() -> None:
    df = pd.DataFrame(
        [
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-01", "Min_Price": 1000.0, "Modal_Price": 1500.0, "Max_Price": 1800.0},
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-01", "Min_Price": 1000.0, "Modal_Price": 1600.0, "Max_Price": 1800.0},  # conflicting dup
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Other", "Grade": "FAQ", "Arrival_Date": "2025-01-02", "Min_Price": 1100.0, "Modal_Price": 1400.0, "Max_Price": 1700.0},
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-03", "Min_Price": 1000.0, "Modal_Price": 400.0, "Max_Price": 1500.0},  # invalid modal < min
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-04", "Min_Price": 1200.0, "Modal_Price": 1600.0, "Max_Price": 1100.0},  # invalid min > max
            {"State": "Maharashtra", "District": "Nashik", "Market": "Lasalgaon", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": "2025-01-05", "Min_Price": -5.0, "Modal_Price": 1200.0, "Max_Price": 1500.0},   # nonpositive
        ]
    )
    canon_df, bad_df, counts = compute_cleaning_funnel(df)
    assert counts["panel_rows_raw"] == 6
    assert counts["invalid_nonpositive_or_na_rows"] == 1
    assert counts["invalid_minmax_swapped_rows"] == 1
    assert counts["invalid_modal_outside_minmax_rows"] == 1
    assert counts["invalid_rows_dropped_total"] == 3
    assert counts["rows_after_invalid_drop"] == 3
    assert counts["raw_key_conflicting_modal_groups"] == 1
    assert counts["retained_raw_key_rows"] == 2
    assert counts["retained_canonical_variety_day_rows"] == 2
    assert len(bad_df) == 1
    # Conflicting dup median of [1500, 1600] == 1550
    row0 = canon_df[canon_df["Arrival_Date"] == pd.Timestamp("2025-01-01")].iloc[0]
    assert row0["Modal_Price"] == 1550.0


def test_real_lagged_candidates_and_cleaning_counts_invariants() -> None:
    counts = json.loads((ROOT / "revision/results/cleaning_counts.json").read_text())
    assert counts["panel_rows_raw"] == 260043
    assert counts["invalid_modal_outside_minmax_rows"] == 759
    assert counts["panel_rows_raw"] - counts["invalid_rows_dropped_total"] == counts["rows_after_invalid_drop"]
    assert counts["rows_after_invalid_drop"] - counts["raw_key_duplicate_excess_dropped"] == counts["retained_raw_key_rows"]
    assert counts["retained_raw_key_rows"] - counts["canonical_variety_merge_excess"] == counts["retained_canonical_variety_day_rows"]
    # Weather leak audit counts present and honest (2025-01-01..2026-04-08 window)
    assert counts["weather_rows_2025_2026"] == 67135
    assert counts["weather_rain_fc_equals_era5"] == 66222
    assert counts["weather_rain_fc_equals_era5"] > 0.95 * counts["weather_rows_2025_2026"]

    df = pd.read_parquet(ROOT / "revision/results/lagged_candidates.parquet")
    assert len(df) > 100000
    d = pd.to_datetime(df["date"])
    dq = pd.to_datetime(df["dest_quote_date"])
    oq = pd.to_datetime(df["origin_quote_date"])
    arr = pd.to_datetime(df["arrival_date"])

    # R3: strict inequality < t on EVERY quote and arrival > date
    assert (dq < d).all()
    assert (oq < d).all()
    assert ((d - dq).dt.days == df["dest_lag_age"]).all()
    assert ((d - oq).dt.days == df["origin_lag_age"]).all()
    assert (df["dest_lag_age"].between(1, 7)).all()
    assert (df["origin_lag_age"].between(1, 7)).all()
    assert (arr > d).all()
    assert (df["lag_spread"] == df["dest_lag_price"] - df["origin_lag_price"]).all()
    assert (df["lag_spread"] > 100.0).all()
    assert "route_fc_rain" not in df.columns
    assert "route_era5_rain" not in df.columns
    # Max per episode == 5
    assert (df.groupby("episode_id").size() <= 5).all()
    # Fee rate is 0 on same_district
    assert (df.loc[df["same_district"], "fee_rate"] == 0.0).all()


def test_counterfactual_future_perturbation_zero_leakage_r3() -> None:
    """R3 property test: corrupting ALL prices on dates >= t* leaves day-t* shortlist and decisions bit-for-bit identical."""
    dates = pd.date_range("2025-07-01", "2025-07-20", freq="D")
    rows = []
    for d in dates:
        # Origin O1
        rows.append({"State": "Maharashtra", "District": "D1", "Market": "O1", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": d, "Min_Price": 900.0, "Modal_Price": 1000.0, "Max_Price": 1100.0})
        # Destination M1 (high yesterday spread, sporadic)
        if d.day % 2 == 1:
            rows.append({"State": "Maharashtra", "District": "D2", "Market": "M1", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": d, "Min_Price": 1400.0, "Modal_Price": 1600.0, "Max_Price": 1700.0})
        # Destination M2 (steady lower spread)
        rows.append({"State": "Maharashtra", "District": "D3", "Market": "M2", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": d, "Min_Price": 1200.0, "Modal_Price": 1400.0, "Max_Price": 1500.0})
        # Destination M3 (not profitable before t*: price = 950)
        rows.append({"State": "Maharashtra", "District": "D4", "Market": "M3", "Commodity": "Onion", "Variety": "Red", "Grade": "FAQ", "Arrival_Date": d, "Min_Price": 900.0, "Modal_Price": 950.0, "Max_Price": 1000.0})

    cor = pd.DataFrame([
        {"State": "Maharashtra", "origin_market": "O1", "dest_market": "M1", "same_district": False, "euclid_km": 80.0, "road_km": 100.0, "truck_hours": 3.0, "arrival_lag_days": 1},
        {"State": "Maharashtra", "origin_market": "O1", "dest_market": "M2", "same_district": False, "euclid_km": 70.0, "road_km": 90.0, "truck_hours": 3.0, "arrival_lag_days": 1},
        {"State": "Maharashtra", "origin_market": "O1", "dest_market": "M3", "same_district": False, "euclid_km": 60.0, "road_km": 80.0, "truck_hours": 2.5, "arrival_lag_days": 1},
    ])
    fees = pd.DataFrame([{"State": "Maharashtra", "Commodity": "Onion", "statutory_seller_fee_pct": 0.01}])

    t_star = pd.Timestamp("2025-07-12")
    raw_base = pd.DataFrame(rows)

    # Adversarially corrupt ALL prices on d >= t* (keep origin O1 row present at t* with a crazy modal price!)
    raw_adv = raw_base.copy()
    mask_ge = raw_adv["Arrival_Date"] >= t_star
    raw_adv.loc[mask_ge & (raw_adv["Market"] == "M3"), "Modal_Price"] = 99999.0
    raw_adv.loc[mask_ge & (raw_adv["Market"] == "M3"), "Max_Price"] = 99999.0
    raw_adv.loc[mask_ge & (raw_adv["Market"] == "O1"), "Modal_Price"] = 500.0
    raw_adv.loc[mask_ge & (raw_adv["Market"] == "O1"), "Min_Price"] = 400.0
    # Drop M1 and M2 completely on d > t* and on d == t*!
    raw_adv = raw_adv[~(mask_ge & raw_adv["Market"].isin(["M1", "M2"]))].copy()

    c_base, _ = build_lagged_candidates_from_frames(raw_base, cor, fees, min_origin_date="2025-07-03", max_origin_date="2025-07-16")
    c_adv, _ = build_lagged_candidates_from_frames(raw_adv, cor, fees, min_origin_date="2025-07-03", max_origin_date="2025-07-16")

    dec_cols = [
        "origin_market", "dest_market", "origin_lag_price", "origin_quote_date", "origin_lag_age",
        "dest_lag_price", "dest_quote_date", "dest_lag_age", "lag_spread",
        "dest_exact_rep_14d", "dest_exact_rep_28d", "dest_any_rep_14d", "dest_any_rep_28d",
        "dest_price_cv_28d", "dest_obs_cnt_28d", "dest_dow_exact_rep_8w",
        "freight_road", "fee_rate", "spoil_ref_0",
    ]
    sub_b = c_base[c_base["date"] <= t_star].sort_values(["date", "dest_market"]).reset_index(drop=True)
    sub_a = c_adv[c_adv["date"] <= t_star].sort_values(["date", "dest_market"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(sub_b[dec_cols], sub_a[dec_cols], check_exact=False, rtol=0, atol=1e-12)
    # Meanwhile settlement column changed at t* for O1!
    assert (sub_b.loc[sub_b["date"] == t_star, "settle_local_price_d0"] == 1000.0).all()
    assert (sub_a.loc[sub_a["date"] == t_star, "settle_local_price_d0"] == 500.0).all()


def test_hp_apple_lagged_invariants_and_gitignored_independence() -> None:
    hp_path = ROOT / "revision/results/lagged_hp_apple_candidates.parquet"
    assert hp_path.exists()
    hp = pd.read_parquet(hp_path)
    d = pd.to_datetime(hp["date"])
    dq = pd.to_datetime(hp["dest_quote_date"])
    oq = pd.to_datetime(hp["origin_quote_date"])
    assert (dq < d).all()
    assert (oq < d).all()
    assert (hp["dest_lag_age"].between(1, 7)).all()
    assert (hp["origin_lag_age"].between(1, 7)).all()
    assert (hp["lag_spread"] > 100.0).all()
    assert (hp["freight_road"] == 35.0 + 0.45 * 1.45 * hp["road_km"]).all()
    assert (hp.loc[hp["same_district"], "fee_rate"] == 0.0).all()
    assert (hp.loc[~hp["same_district"], "fee_rate"] == 0.010).all()

    bv_text = (ROOT / "revision/build_variant.py").read_text()
    assert "candidates_6state.parquet" not in bv_text.split("Enforces" if "Enforces" in bv_text else "ROOT = Path")[1]


def test_sequential_settlement_fee_base_and_edge_cases() -> None:
    from revision.es10 import es10
    from revision.eval_a10 import rr_abstain_score
    from revision.eval_run import settle_candidates, summarize_chosen
    from revision.stats_utils import weighted_es10

    # Base synthetic frame verifying all settlement branches + M9 fee-base fix
    # freight_road = 35 + 0.45 * 100 = 80.0; Tomato 4h at 20C = 0.0325 * (4/24) = 0.0054166667
    sp4 = 0.0325 * (4.0 / 24.0)
    sp28 = 0.0325 * (28.0 / 24.0)
    sp52 = 0.0325 * (52.0 / 24.0)

    def _row(same_dist, dm0, dm1, dm2, am0, am1, am2):
        return {
            "State": "Maharashtra", "Commodity": "Tomato", "road_km": 100.0, "truck_hours": 4.0,
            "same_district": same_dist, "fee_rate": 0.0 if same_dist else 0.01,
            "settle_local_price_d0": 1000.0, "origin_lag_price": 1000.0, "dest_lag_price": 1500.0,
            "freight_road": 80.0, "spoil_ref_0": sp4,
            "dest_exact_rep_28d": 0.5, "dest_dow_exact_rep_8w": 0.5,
            "settle_dest_modal_d0": dm0, "settle_dest_modal_d1": dm1, "settle_dest_modal_d2": dm2,
            "settle_any_min_d0": am0, "settle_any_min_d1": am1, "settle_any_min_d2": am2,
        }

    test_df = pd.DataFrame([
        _row(False, 1600.0, np.nan, np.nan, 1200.0, np.nan, np.nan),  # 0: d0 exact sell w/ 1% dest post-spoil fee
        _row(True, 1600.0, np.nan, np.nan, 1200.0, np.nan, np.nan),   # 1: same_district zero fee
        _row(False, np.nan, 1600.0, np.nan, np.nan, 1600.0, np.nan),  # 2: d0 no commodity -> MUST divert d0 (NO wait lookahead!)
        _row(False, np.nan, 1600.0, np.nan, 1200.0, 1600.0, np.nan),  # 3: d0 other var active -> wait 1d (+25 detention) -> d1 sell
        _row(False, np.nan, np.nan, np.nan, 1200.0, 1200.0, 1100.0),  # 4: d2 fallback to other_var_min * (1 - 0.10) + 50 detention
        _row(False, np.nan, np.nan, np.nan, 1200.0, 1200.0, np.nan),  # 5: d2 no commodity -> divert d2 + 50 detention + zero fee
    ])

    y, ot = settle_candidates(test_df, how="sequential", weather="none", div=1.5, disc=0.10, return_outcomes=True)
    # 0: fee on dest post-spoil sale: 1600*(1-sp4)*(1-0.01) - 80 - 1000
    exp0 = 1600.0 * (1.0 - sp4) * 0.99 - 80.0 - 1000.0
    assert abs(y[0] - exp0) < 1e-9 and ot[0] == "exact_d0"
    # 1: same_district fee == 0 -> exact difference equals 1% of dest gross sale (1600*(1-sp4)*0.01), independent of local_price!
    assert abs((y[1] - y[0]) - 1600.0 * (1.0 - sp4) * 0.01) < 1e-9
    # 2: sequential NO lookahead! Even though dm1 == 1600, am0 is NaN so trader returns at d0 with zero fee!
    exp2 = -1.5 * 80.0 - 1000.0 * sp4
    assert abs(y[2] - exp2) < 1e-9 and ot[2] == "no_comm_divert_d0"
    # Verify hindsight differs on row 2
    yh = settle_candidates(test_df, how="hindsight", weather="none", div=1.5, disc=0.10)
    assert yh[2] > 400.0 and ot[2] == "no_comm_divert_d0"
    # 3: wait 1d -> 1600*(1-sp28)*0.99 - 80 - 25 - 1000
    exp3 = 1600.0 * (1.0 - sp28) * 0.99 - 80.0 - 25.0 - 1000.0
    assert abs(y[3] - exp3) < 1e-9 and ot[3] == "exact_wait_d1"
    # 4: d2 distress -> 1100*0.9*(1-sp52)*0.99 - 80 - 50 - 1000
    exp4 = (1100.0 * 0.90) * (1.0 - sp52) * 0.99 - 80.0 - 50.0 - 1000.0
    assert abs(y[4] - exp4) < 1e-9 and ot[4] == "other_var_distress_d2"
    # 5: d2 divert -> -1.5*80 - 1000*sp52 - 50 (zero fee!)
    exp5 = -1.5 * 80.0 - 1000.0 * sp52 - 50.0
    assert abs(y[5] - exp5) < 1e-9 and ot[5] == "no_comm_divert_d2"

    # Weighted ES10 exact identity with es10 for unit weights
    arr = np.array([-300.0, -50.0, 0.0, 0.0, 10.0, 20.0, 40.0, 80.0, 120.0, 200.0, 350.0])
    assert abs(weighted_es10(arr, np.ones_like(arr)) - es10(arr)) < 1e-10

    # Zero-dispatch summarize_chosen edge case
    zero_df = pd.DataFrame({"eligible": [False, False], "y_raw": [100.0, -50.0]})
    zs = summarize_chosen("zero", zero_df)
    assert zs["n_dispatch"] == 0 and zs["mean"] == 0.0 and zs["cond_loss_rate"] is None

    # RR-Abstain boundary check (p_rep = 0 -> delta_miss; p_rep = 1 -> delta_open)
    b_df = pd.DataFrame([
        {**_row(False, 1600, np.nan, np.nan, 1200, np.nan, np.nan), "dest_exact_rep_28d": 1.0, "dest_dow_exact_rep_8w": 1.0},
        {**_row(False, 1600, np.nan, np.nan, 1200, np.nan, np.nan), "dest_exact_rep_28d": 0.0, "dest_dow_exact_rep_8w": 0.0},
    ])
    sc = rr_abstain_score(b_df, kappa=1.5)
    assert abs(sc[0] - (1500.0 * (1.0 - sp4) * 0.99 - 1000.0 - 80.0)) < 1e-9
    assert abs(sc[1] - (-1.5 * 80.0 - 1000.0 * sp4)) < 1e-9


def test_manuscript_and_viva_zero_untraceable_numbers() -> None:
    from scripts.verify_traceability import verify_docs

    fails = verify_docs(ROOT)
    assert fails == [], f"Untraceable numbers found: {fails}"


def test_repo_portability_citations_and_prereg_order() -> None:
    import re
    import subprocess

    # 1. Zero hardcoded local /Users/ paths across active Revision v4 documentation, code, and configs
    active_rel_dirs_and_files = [
        "paper/manuscript.md",
        "paper/12th_class_easy_reading_edition.md",
        "NOVELTY_AUDIT.md",
        "RESEARCH_DECISIONS.md",
        "README.md",
        "FINDINGS.md",
        "PROJECT_STATE.md",
        "REPRODUCIBILITY.md",
        "Makefile",
        ".github/workflows/ci.yml",
    ]
    for folder in ("final", "viva", "revision", "scripts"):
        for p in (ROOT / folder).rglob("*"):
            if p.is_file() and p.suffix in (".md", ".py"):
                active_rel_dirs_and_files.append(str(p.relative_to(ROOT)))

    bad_user_paths = []
    home_path_re = re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/")
    for rel in sorted(set(active_rel_dirs_and_files)):
        p = ROOT / rel
        if p.exists() and home_path_re.search(p.read_text(errors="ignore")):
            bad_user_paths.append(rel)
    assert bad_user_paths == [], f"Hardcoded local user directory path in active files: {bad_user_paths}"

    # 2. All relative figure links in paper/manuscript.md resolve to existing PNGs
    ms = (ROOT / "paper/manuscript.md").read_text()
    img_links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", ms)
    assert len(img_links) == 4
    for link in img_links:
        assert not link.startswith("file://"), f"Expected relative link, got {link}"
        target = ((ROOT / "paper") / link).resolve()
        assert target.exists() and target.stat().st_size > 1000, f"Missing figure target: {target}"

    # 3. Every [key] citation in paper/manuscript.md exists in paper/references.bib
    bib = (ROOT / "paper/references.bib").read_text()
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib))
    ms_body = re.split(r"^##\s+References\b", ms, maxsplit=1, flags=re.M)[0]
    cited = set()
    for grp in re.findall(r"\[([^\[\]]+)\](?!\()", ms_body):
        for tok in re.split(r"[;,]\s*", grp.strip()):
            tok = tok.strip()
            if re.match(r"^[a-z][a-z0-9_]*\d{2,}[a-z0-9_]*$", tok):
                cited.add(tok)
    missing_bib = sorted(cited - bib_keys)
    assert missing_bib == [], f"Manuscript citations missing from references.bib: {missing_bib}"

    # 4. Pre-registration commit order (R5): PREREG_A10.md committed strictly BEFORE revision/eval_a10.py
    if (ROOT / ".git").exists():
        c_prereg = subprocess.run(
            ["git", "log", "--reverse", "--format=%H", "--", "final/PREREG_A10.md"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout.strip().splitlines()
        c_eval = subprocess.run(
            ["git", "log", "--reverse", "--format=%H", "--", "revision/eval_a10.py"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout.strip().splitlines()
        if c_prereg and c_eval:
            assert c_prereg[0] != c_eval[0], "PREREG_A10.md and eval_a10.py must not share initial commit"
            is_anc = subprocess.run(
                ["git", "merge-base", "--is-ancestor", c_prereg[0], c_eval[0]],
                cwd=ROOT, check=False,
            )
            assert is_anc.returncode == 0, f"PREREG_A10 ({c_prereg[0]}) is not an ancestor of eval_a10 ({c_eval[0]})"

