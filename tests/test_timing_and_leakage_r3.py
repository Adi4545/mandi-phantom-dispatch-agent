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

        c_a18_prereg = subprocess.run(
            ["git", "log", "--reverse", "--format=%H", "--", "final/PREREG_A18.md"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout.strip().splitlines()
        c_a18_eval = subprocess.run(
            ["git", "log", "--reverse", "--format=%H", "--", "revision/eval_a18.py"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout.strip().splitlines()
        if c_a18_prereg and c_a18_eval:
            assert c_a18_prereg[0] != c_a18_eval[0], "PREREG_A18.md and eval_a18.py must not share initial commit"
            is_anc2 = subprocess.run(
                ["git", "merge-base", "--is-ancestor", c_a18_prereg[0], c_a18_eval[0]],
                cwd=ROOT, check=False,
            )
            assert is_anc2.returncode == 0, f"PREREG_A18 ({c_a18_prereg[0]}) is not an ancestor of eval_a18 ({c_a18_eval[0]})"


def test_a18_zero_param_scorers_and_cluster_bounds() -> None:
    from revision.eval_a18 import score_rt2f_min, score_safe_ev_sunk

    row = pd.DataFrame([{
        "dest_lag_price": 2000.0,
        "origin_lag_price": 1500.0,
        "dest_price_cv_28d": 0.10,
        "fee_rate": 0.015,
        "freight_road": 125.0,
        "dest_dow_exact_rep_8w": 0.80,
        "dest_exact_rep_28d": 0.70,
    }])
    # Safe_EV_Sunk: 0.80 * (2000*0.90*0.985 - 1500) - 125 = 0.80 * 273.0 - 125 = 93.40
    assert abs(float(score_safe_ev_sunk(row)[0]) - 93.40) < 1e-9
    # RT_2F_Min: 0.70 * (2000*0.985 - 1500) - 2*125 = 0.70 * 470 - 250 = 79.00
    assert abs(float(score_rt2f_min(row)[0]) - 79.00) < 1e-9

    # Ensure zero phantom cluster keys > 178 across all bootstrap result tables
    res_dir = ROOT / "revision" / "results"
    for bname in ("bootstrap.csv", "a10_bootstrap.csv", "a18_bootstrap.csv"):
        bp = res_dir / bname
        assert bp.exists(), f"Missing {bname}"
        bdf = pd.read_csv(bp)
        assert int(bdf["n_clusters"].max()) <= 178
        assert "p_holm_2s" in bdf.columns


def test_compiled_deliverables_revision_v5_integrity() -> None:
    import json
    import re
    from docx import Document
    from pypdf import PdfReader

    pdf_targets = [
        ROOT / "paper" / "MandiGuard_Research_Paper.pdf",
        ROOT / "paper" / "MandiGuard_Easy_Reading_Edition.pdf",
        ROOT / "viva" / "MandiGuard_Viva_Defense_Slides.pdf",
        ROOT / "docs" / "MandiGuard_First_Principles_and_Thesis_Defense_Handbook.pdf",
        ROOT / "docs" / "MandiGuard_Master_Study_Guide.pdf",
        ROOT / "docs" / "MandiGuard_Student_Study_Guide.pdf",
        ROOT / "docs" / "MandiGuard_Ultra_Simplified_Concept_and_Key_Papers_Guide.pdf",
    ]
    forbidden = (
        "B3_MLPoint",
        "cvar_10",
        "fig1_phantom_arbitrage",
        "fig2_main_policy_comparison",
        "[jensen2007digital]",
        "[baulch1997transfer]",
        "exploratory: true",
        "make reproduce",
        "Brinjal",
        "Cabbage",
        "ICPAR",
        "4.2/qtl",
        r"\frac",
        r"\text{",
        r"\Longleftrightarrow",
        r"\Delta\text{Net}",
        r"\big(",
        r"\big)",
        r"\Big(",
        r"\Big)",
        "≤ ft(",
        r"\%",
        "@@TOK",
        "<br",
        "**",
        "`",
        "$S_",
        "/" + "Users/",
        "TO CONFIRM",
        "Crushes",
        "slashes",
        "slashing",
    )
    splits_df = pd.read_csv(ROOT / "revision" / "results" / "v7_splits_171.csv")
    for pdf_path in pdf_targets:
        assert pdf_path.exists() and pdf_path.stat().st_size > 10_000, f"Missing or tiny PDF: {pdf_path}"
        reader = PdfReader(str(pdf_path))
        if pdf_path.name == "MandiGuard_Research_Paper.pdf":
            assert len(reader.pages) <= 15, f"Paper PDF too long: {len(reader.pages)} pages (> 15)"
        if pdf_path.name == "MandiGuard_Viva_Defense_Slides.pdf":
            assert len(reader.pages) == 12, f"Expected 12 slides, got {len(reader.pages)}"
            slide9_txt = reader.pages[8].extract_text() or ""
            for st_name in ("Gujarat", "Himachal Pradesh", "Karnataka", "Madhya Pradesh", "Maharashtra", "Uttar Pradesh"):
                sub = splits_df[(splits_df["slice_type"] == "State") & (splits_df["slice"] == st_name)]
                b2_es10 = float(sub[sub["policy"] == "B2_age_matched"]["es10"].iloc[0])
                safe_row = sub[sub["policy"] == "Safe_EV_Sunk_m0"].iloc[0]
                rt_row = sub[sub["policy"] == "RT_2F_Min_m0"].iloc[0]
                assert f"{float(safe_row['mean']):,.2f}" in slide9_txt, f"Slide 9 Safe_EV Mean mismatch for {st_name}"
                assert f"{float(rt_row['mean']):,.2f}" in slide9_txt, f"Slide 9 RT_2F Mean mismatch for {st_name}"
                assert f"{float(safe_row['es10']) - b2_es10:,.2f}" in slide9_txt, f"Slide 9 ES10 gain mismatch for {st_name}"
        txt = "\n".join((pg.extract_text() or "") for pg in reader.pages)
        for req in ("Safe_EV_Sunk_m0", "RT_2F_Min_m0", "57,634", "345.53", "383,952"):
            assert req in txt, f"Missing `{req}` in {pdf_path.name}"
        for bad in forbidden:
            assert bad not in txt, f"Forbidden token `{bad}` leaked into {pdf_path.name}"
        raw_macros = sorted(set(re.findall(r"\\[a-zA-Z]{2,}", txt)))
        assert raw_macros == [], f"Unrendered LaTeX macros leaked into {pdf_path.name}: {raw_macros}"

    docx_path = ROOT / "paper" / "MandiGuard_Research_Paper.docx"
    assert docx_path.exists() and docx_path.stat().st_size > 50_000, "Missing Research Paper DOCX"
    doc = Document(str(docx_path))
    docx_chunks = [p.text for p in doc.paragraphs] + [c.text for t in doc.tables for row in t.rows for c in row.cells]
    docx_txt = "\n".join(docx_chunks)
    for bad_docx in ("`", "**", "$", "B3_MLPoint", "cvar_10", "[jensen2007digital]", "exploratory: true", "make reproduce"):
        assert bad_docx not in docx_txt, f"Forbidden token `{bad_docx}` leaked into {docx_path.name}"

    tex_path = ROOT / "paper" / "manuscript.tex"
    assert tex_path.exists() and tex_path.stat().st_size > 5_000, "Missing LaTeX manuscript.tex"
    tex_txt = tex_path.read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", (ROOT / "paper" / "references.bib").read_text()))
    for grp in re.findall(r"\\citep?\{([^}]+)\}", tex_txt):
        for k in [p.strip() for p in grp.split(",")]:
            assert k in bib_keys, f"LaTeX citation `{k}` missing from references.bib"
    for rel_fig in re.findall(r"\\includegraphics\[[^\]]+\]\{([^}]+)\}", tex_txt):
        assert ((ROOT / "paper") / rel_fig).resolve().exists(), f"Missing LaTeX graphic: {rel_fig}"

    for nb_name in ("10_finalization_reproduction.ipynb", "colab_standalone_reproduction.ipynb"):
        nb_raw = (ROOT / "notebooks" / nb_name).read_text(encoding="utf-8")
        nb_obj = json.loads(nb_raw)
        assert len(nb_obj.get("cells", [])) >= 4
        assert "Safe_EV_Sunk_m0" in nb_raw
        assert "B3_MLPoint" not in nb_raw and "colab_data_pack.tar.gz" not in nb_raw


def test_v6_zero_lookahead_era5_and_breakeven() -> None:
    import json
    import re

    res = ROOT / "revision" / "results"
    s6 = json.loads((res / "v6_summary.json").read_text())
    assert s6["exploratory"] is True
    assert s6["strict_2024_markets_count"] == 171
    assert s6["strict_2024_fresh_rebuild"] is True
    assert s6["val_171_b2_threshold"] == 200.0
    assert s6["n_test_full_178"] == 58676
    assert s6["n_test_strict2024_171"] == 57634
    assert s6["bootstrap_reps"] == 5000
    for d in ("d0", "d1", "d2"):
        assert s6["era5_settlement_coverage"][f"{d}_era5_coverage_pct"] == 100.0
        assert s6["era5_settlement_coverage_171"][f"{d}_era5_coverage_pct"] == 100.0

    up = pd.read_csv(res / "v6_upgrades.csv")
    assert set(up["panel"].unique()) == {
        "full_178_20C_closed",
        "full_178_ERA5_closed",
        "full_178_ERA5_open_MAR",
        "strict2024_171_20C_closed",
        "strict2024_171_ERA5_closed",
        "strict2024_171_ERA5_open_MAR",
    }

    be = pd.read_csv(res / "v6_breakeven.csv")
    assert len(be) == 16
    assert float(be["verification_resid"].max()) < 1e-6

    b5 = pd.read_csv(res / "v6_bootstrap_5000.csv")
    assert len(b5) == 66
    assert int(b5["reps"].min()) == 5000
    assert int(b5["n_clusters"].max()) <= 178
    assert set(b5["week_block_len"].unique()) == {1, 2, 4}
    assert float(b5["p_holm_2s"].max()) < 0.05

    # Verify 100% 1-to-1 citation parity, calm prose, zero TO CONFIRM, and <= 260w abstract in manuscript.md
    ms = (ROOT / "paper" / "manuscript.md").read_text(encoding="utf-8")
    for banned in ("TO CONFIRM", "Crushes", "slashes"):
        assert banned not in ms, f"Banned phrase `{banned}` found in manuscript.md"
    body, refs = ms.split("## References", 1)
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", (ROOT / "paper" / "references.bib").read_text()))
    ref_list = set(re.findall(r"\[([a-z0-9_]+)\]", refs))
    body_cites = set()
    for grp in re.findall(r"\[([a-z0-9_,\s]+)\]", body):
        parts = [p.strip() for p in grp.split(",") if p.strip()]
        if parts and all(p in bib_keys for p in parts):
            body_cites.update(parts)
    assert body_cites == ref_list, f"Citation mismatch body vs References: {body_cites ^ ref_list}"
    assert ref_list.issubset(bib_keys), f"Missing bib keys: {ref_list - bib_keys}"
    assert len(ref_list) >= 45
    abs_words = len(ms.split("## Abstract", 1)[1].split("---", 1)[0].strip().split())
    assert abs_words <= 245, f"Abstract too long ({abs_words} words)"


def test_v7_primary_171_and_decade_2018_2023() -> None:
    import json
    import re
    from scripts.verify_traceability import DEFAULT_DOC_REL_PATHS

    res = ROOT / "revision" / "results"
    s7 = json.loads((res / "v7_summary.json").read_text())
    assert s7["strict_2024_markets_count"] == 171
    assert s7["counts_171"]["shortlist_test_episodes"] == 57634
    dec = s7["decade_2018_2023"]
    assert dec["clean_166_markets_count"] == 166
    assert dec["counts_166clean"]["episodes_with_lag_spread_gt_100"] == 383952
    assert dec["n_episodes_166clean"] == 383952
    assert dec["markets_2017_clean_ge50d"] == 115
    assert dec["counts_115clean2017"]["episodes_with_lag_spread_gt_100"] == 325993
    assert dec["n_episodes_115clean2017"] == 325993

    b2k = pd.read_csv(res / "v7_bootstrap_prereg_2000.csv")
    reg = b2k[b2k["registered_prereg_a18"] == True]
    assert len(reg) == 12
    assert set(reg["hypothesis_id"].unique()) == {"H_A18_1", "H_A18_2", "H_A18_3", "H_A18_4"}
    assert (reg["reps"] == 2000).all()
    assert float(reg["p_holm_2s_prereg4"].max()) <= 0.0041
    assert int(b2k["n_clusters"].max()) <= 171

    by = pd.read_csv(res / "v7_decade_by_year.csv")
    for yr in range(2018, 2024):
        sub = by[by["year"] == yr].set_index("policy")
        assert float(sub.loc["Safe_EV_Sunk_m0", "mean"]) > float(sub.loc["B2_age_matched", "mean"])
        assert float(sub.loc["Safe_EV_Sunk_m0", "ep_loss_rate"]) < float(sub.loc["B2_age_matched", "ep_loss_rate"])
        assert float(sub.loc["Safe_EV_Sunk_m0", "es10"]) > float(sub.loc["B2_age_matched", "es10"])
        assert float(sub.loc["Safe_EV_Sunk_m0", "cond_es10"]) > float(sub.loc["B2_age_matched", "cond_es10"])

    by_boot = pd.read_csv(res / "v7_decade_by_year_boot_2000.csv")
    for yr in (2020, 2023):
        p_mean = float(by_boot[(by_boot["year"] == yr) & (by_boot["policy_a"] == "Safe_EV_Sunk_m0") & (by_boot["policy_b"] == "B2_age_matched") & (by_boot["metric"] == "mean")]["p_value_two_sided"].iloc[0])
        assert p_mean > 0.05

    rec = pd.read_csv(res / "v7_era5_and_reconcile.csv").set_index("policy")
    b1 = rec.loc["B1_lagged_screen"]
    assert abs(float(b1["shift_market_178_to_171_20C"]) - (-13.26)) < 1e-6
    assert abs(float(b1["shift_weather_20C_to_ERA5_171"]) - (-17.90)) < 1e-6
    assert abs(float(b1["shift_total_178_20C_to_171_ERA5"]) - (-31.16)) < 1e-6

    # Phase 6 stress summary & CSV invariants + 59-citation bijection + zero /Users/ paths
    exp_sum = json.loads((res / "v7_exp_summary.json").read_text())
    assert exp_sum["exp1_latency_t2"]["t2_leakage_test_passed"] is True
    exp1 = pd.read_csv(res / "v7_exp1_latency_t2.csv")
    t2_safe = exp1[(exp1["window"] == "t2_age_2_3") & (exp1["policy"] == "Safe_EV_Sunk_m0")].iloc[0]
    assert float(t2_safe["diff_B2_es10_p2s"]) <= 0.002 and float(t2_safe["diff_B2_cond_es10_p2s"]) <= 0.002
    exp2 = pd.read_csv(res / "v7_exp2_bio_s6_condmar.csv")
    s6_cm = exp2[(exp2["experiment"] == "S6_Smallholder_4pctArh_USDA_ERA5_Frozen") & (exp2["missing_regime"] == "Stoch_CondMAR_p1.00")].set_index("policy")
    assert float(s6_cm.loc["Safe_EV_Sunk_m0", "cond_es10"]) - float(s6_cm.loc["B2_age_matched", "cond_es10"]) > 300.0
    exp3 = pd.read_csv(res / "v7_exp3_manski_and_open.csv")
    assert len(exp3) >= 9
    exp4 = pd.read_csv(res / "v7_exp4_ml_pareto_and_formula.csv")
    pareto = exp4[exp4["group"] == "ml_or_pareto"].set_index("policy")
    assert float(pareto.loc["ZeroParam_Safe_EV_Sunk_m0", "cond_es10"]) > float(pareto.loc["OR_Vargas_MeanVar_g0002", "cond_es10"])
    exp5 = pd.read_csv(res / "v7_exp5_hygiene_sutva_inference.csv")
    assert len(exp5[exp5["slice_check"] == "PureAll5_ExactGeocode_N19362"]) == 4

    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", (ROOT / "paper" / "references.bib").read_text()))
    assert len(bib_keys) == 59
    for rel in DEFAULT_DOC_REL_PATHS:
        assert ("/" + "Users/") not in (ROOT / rel).read_text(encoding="utf-8"), f"/Users/ found in {rel}"


def test_harsh_examiner_invariants_v7() -> None:
    """Hostile critical-examiner checks for TeX ASCII purity, Table 1-5 parity, Pareto honesty, and compact traceability."""
    import re

    tex_path = ROOT / "paper" / "manuscript.tex"
    tex_txt = tex_path.read_text(encoding="utf-8")
    non_ascii = [(idx, ch, hex(ord(ch))) for idx, ch in enumerate(tex_txt) if ord(ch) > 127]
    assert non_ascii == [], f"Non-ASCII characters in manuscript.tex: {non_ascii[:10]}"

    caps = re.findall(r"\\caption\{([^}]+)\}", tex_txt)
    tbl_blocks = re.findall(r"\\begin\{table\}", tex_txt)
    assert len(tbl_blocks) == 5, f"Expected 5 LaTeX tables, got {len(tbl_blocks)}"
    # Figures also use \caption, so filter table captions strictly via table environments
    tbl_caps = re.findall(r"\\begin\{table\}[\s\S]*?\\caption\{([^}]+)\}", tex_txt)
    assert len(tbl_caps) == 5
    expected_kw = ("Epistemic", "171-market", "PREREG", "ML/OR", "166-market")
    for idx_t, (cap, kw) in enumerate(zip(tbl_caps, expected_kw), 1):
        assert kw in cap, f"Table {idx_t} caption missing `{kw}`: {cap}"

    ms_txt = (ROOT / "paper" / "manuscript.md").read_text(encoding="utf-8")
    ms_title = ms_txt.splitlines()[0].lstrip("# ").strip()
    assert "ML_HGBR_Q20_m0" in ms_txt
    assert "dominates every learned" not in ms_txt
    assert "Tables 3–5" not in ms_txt and "Tables 3-5" not in ms_txt
    assert "Table 3 compares all rules" not in ms_txt
    assert "(`R = 2,000`, Table 4)" not in ms_txt
    assert "Table 2 compares all rules" in ms_txt
    assert "Tables 2–4" in ms_txt
    assert "(`R = 2,000`, Table 3)" in ms_txt
    assert "Table 5 summarizes" in ms_txt

    readme_txt = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "expected-value rules" not in readme_txt

    audit_txt = (ROOT / "audit" / "16_AGENT_SCIENTIFIC_AUDIT_AND_VERDICT.md").read_text(encoding="utf-8")
    assert ms_title in audit_txt

    vn_size = (ROOT / "revision" / "results" / "verified_numbers.json").stat().st_size
    assert vn_size < 6_500_000, f"verified_numbers.json too large ({vn_size} bytes); check cross-scenario diff bloat"

    exp4_raw = pd.read_csv(ROOT / "revision" / "results" / "v7_exp4_ml_pareto_and_formula.csv")
    exp4 = exp4_raw[exp4_raw["group"] == "ml_or_pareto"].set_index("policy")
    assert abs(float(exp4.loc["MG_T1_T2_T3_T4_Intact_matched", "cond_es10"]) - (-414.44)) <= 0.05


def test_omega_v8_invariants() -> None:
    """Revision v8 regression checks: sub-yard geocoding, return-leg biology, heteroscedastic CQR, coupled Manski cond_ES10, 2x2 ortho, 17m ML, CGM G*, and prose hygiene."""
    from src.data.build_road_network import clean_market_query
    from revision.eval_v7_stress_experiments import _spoil_return_leg, _spoil_vector
    from scripts.verify_traceability import DEFAULT_DOC_REL_PATHS

    # (a) Sub-yard-first clean_market_query
    q_cands = clean_market_query("Dindori(Vani)")
    assert q_cands[0] == "Vani" and "Dindori" in q_cands

    # (b) Repaired _spoil_return_leg >= _spoil_vector on 100% of rows under identical ERA5 inputs
    sample_df = pd.DataFrame({
        "Commodity": ["Tomato", "Onion", "Potato", "Apple"],
        "tau_days": [1.0, 2.0, 1.0, 2.0],
        "truck_hours": [6.0, 12.0, 8.0, 18.0],
    })
    tmax = np.array([38.0, 42.0, 28.0, 18.0])
    tmin = np.array([26.0, 30.0, 18.0, 8.0])
    rh = np.array([50.0, 80.0, 75.0, 60.0])
    rain = np.array([0.0, 40.0, 10.0, 0.0])
    for mode in ("usda_sched7", "nabcons_24tau", "nabcons_truck"):
        for wait_d in (0, 1, 2):
            s_sell = _spoil_vector(sample_df, wait_d, mode, True, tmax, tmin, rh, rain)
            s_ret = _spoil_return_leg(sample_df, wait_d, mode, True, tmax, tmin, rh, rain)
            assert np.all(s_ret >= s_sell - 1e-12), f"Return spoilage < sell spoilage for {mode}, w={wait_d}"

    res = ROOT / "revision" / "results"
    exp_sum = json.loads((res / "v7_exp_summary.json").read_text())

    # (c) Heteroscedastic Split-CQR produces substantial destination re-ranking switches
    assert int(exp_sum["exp4_ml_pareto_and_formula"]["cqr5m_dest_switches_vs_raw"]) == 8848
    assert int(exp_sum["exp4_ml_pareto_and_formula"]["cqr17m_dest_switches_vs_raw"]) == 8115

    # (d) Coupled Manski cond_ES10 remains strictly positive on Supp1 and Supp2
    exp3 = pd.read_csv(res / "v7_exp3_manski_and_open.csv").set_index("analysis")
    assert float(exp3.loc["Manski_Supp1_div15_openlag", "coupled_dcond_es10_wc"]) > 0.0
    assert float(exp3.loc["Manski_Supp2_div20_q95", "coupled_dcond_es10_wc"]) > 0.0

    # (e) Exp 6.4 17m ML/OR & 2x2 orthogonal rows exist cleanly
    exp4 = pd.read_csv(res / "v7_exp4_ml_pareto_and_formula.csv")
    pols4 = set(exp4["policy"].astype(str))
    for req_pol in ("ML_17m_MeanQ10_Hybrid_valmatch", "ML_17m_MeanQ10_NoSafeEV_eq63", "Ortho_Pure_cv28_only", "ScaleInv_Safe_EV_24tau"):
        assert req_pol in pols4, f"Missing v8 Exp 6.4 policy {req_pol}"

    # (f) Exp 6.5 non-collided geocode, common intersection, call priority, outsider & HP Apple rows exist
    exp5 = pd.read_csv(res / "v7_exp5_hygiene_sutva_inference.csv")
    slices5 = set(exp5["slice_check"].astype(str))
    for req_sl in ("PureAll5_NonCollided_Exact_N6605", "CommonIntersection_DS_cap_DB", "PhoneCall_TopK_Open", "Outsider_Mid_LCV_4pctArh", "HP_Apple_ScaleNonInv"):
        assert req_sl in slices5, f"Missing v8 Exp 6.5 slice {req_sl}"

    # (g) CGM G* finite-sample metadata & 1-way Webb6 relabeling
    cgm_tbl = exp_sum["exp5_hygiene_sutva_inference"]["cgm_inference_table"]
    assert len(cgm_tbl) >= 11
    for rec in cgm_tbl:
        assert "p_wild_webb6_1w_block_only" in rec
        assert "g_star_block_warning" in rec
        assert "atom_at_q10" in rec
        assert "p_wild_webb6_block_2s" not in rec

    # (h) Forbidden claims / hallucinated phrases absent across all 23 active docs
    for rel in DEFAULT_DOC_REL_PATHS:
        txt_l = (ROOT / rel).read_text(encoding="utf-8").lower()
        for bad in ("propensity", "indian mandi procurement", "dfl procurement", "locked confirmatory inference"):
            assert bad not in txt_l, f"Forbidden phrase `{bad}` found in {rel}"

    # (i) Pure 7-bit ASCII LaTeX manuscript
    tex_txt = (ROOT / "paper" / "manuscript.tex").read_text(encoding="utf-8")
    assert all(ord(c) < 128 for c in tex_txt), "manuscript.tex contains non-ASCII character"





