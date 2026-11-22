# Progress Log — MandiGuard Finalization (`finalization`, PR #1)

## Step 1: Recon + Baseline Snapshot (`A1` PI)
- **Date:** 2026-11-22
- **Branch / Base SHA:** `finalization` tracking `origin/finalization` at `b3bb46f8fee131218d6154898f4d0659b3018fa4` (branched from `main` `d20a0cb`). Other local sibling branches untouched (`main`, `omega-research-lab`, `omega-x-scientific-audit`).
- **Environment:** `/Users/adityasharma/anaconda3/bin/python3` — Python `3.11.5`, `numpy 1.24.3`, `pandas 2.0.3`, `scikit-learn 1.3.0`, `scipy 1.11.1`, `pyarrow 11.0.0`, `pytest 7.4.0`.
- **Legacy Pickle Check:** `data/interim/forecaster_2024.pkl` loaded cleanly under Python 3.11.5 + `scikit-learn 1.3.0` as `CausalArrivalForecaster`, though the revised primary dispatch rules do not rely on the pickled tree.
- **Baseline `pytest -v`:** **25 passed, 1 failed** in 2.52s (`M7`):
  - Failing test: `tests/test_decade_and_creative_innovations.py::test_creative_decade_results_files_non_empty` (`ValueError: substring not found` on `ms_text.index("## 9. Conclusion")`, because prior `finalization` commits simplified `paper/manuscript.md` to 6 sections without updating that test).
  - No `R3` strictly-`< t` counterfactual future-perturbation timing property test existed on the revision pipeline.
- **Baseline Audit Findings Confirmed on `b3bb46f`:**
  1. `C1` & `M5/M6`: `revision/build_variant.py` loaded gitignored `data/processed/candidates_6state.parquet`, inheriting a shortlist constructed with day-$t$ destination & origin prices (`build_dispatch_episodes.py` used `screen_board_mat[t, dest_js]` and `mod_mat[t, m_i]`).
  2. `M9`: `revision/build_variant.py` used same-day `local_price` (day-$t$ origin modal price) in `lag_spread` and `net`, computed statutory fees on `local_price` rather than destination gross sale realization, included fees in the diversion freight base, and lacked a primary-source citation/provenance ledger for `hp=1.45` and freight slopes.
  3. `M4`: `B2` (`lag_age <= 1`) and `MG` (`1 <= lag_age <= 3`) operated on unequal quote-age windows; `T1`–`T4` were not cleanly ablated at matched dispatch.
  4. `M3`: In prior `revision/results/main_table.csv`, `MG` (`₹490.52`, `73.73%` dispatch) vs `B2_val_conservative` (`₹424.23`, `60.13%` dispatch) yielded `+₹66.29` across mismatched dispatch rates, while matched `B2_theta100` (`73.95%` dispatch) had lower loss rate (`30.82%` vs `33.41%`) and milder `ES10` (`-₹419.36` vs `-₹444.37`); segment gains were heavily concentrated in `Apple` (`+₹366.67` vs `+₹11.25..+₹52.27`).
  5. `M8`: `cleaning_counts.json` recorded `759` `modal_outside_minmax_rows` but did not drop them (`rows_after_drop_invalid` stayed `260,043`), while `final/ISSUE_REGISTER.md` logged `799` and `paper/manuscript.md` mixed raw-key deduplication with modeling-key aggregation.
  6. `R5` Exposure Log: Both the 6-state holdout (`2025-06-01..2026-04-08`) and HP grade-explicit apple extract (`data/raw/hp_apple_daily_2025_2026.csv`, `2025-11-07..2026-09-01`, `results/exp3_hp_apple_grade_holdout.csv`) have been inspected in prior commits. No untouched post-April-2026 multi-state bulk panel exists in official archives (`HuggingFace` mirror ends `2026-04-13`; `api.agmarknet.gov.in/v1` `/lastweek` returns only a 7-day snapshot). All post-Stage-I results on shipped windows must be labeled `exploratory: true`, Gate J marked `BLOCKED (disclosed)`, and any `A10` extension pre-registered in git prior to code execution.
  7. Weather Audit Confirmed: In `data/processed/mandi_weather_2024_2026.parquet`, `fc_rain_mm == era5_rain_mm` on `87,538 / 88,885` (`98.48%`) of 2025–2026 rows; live/reanalysis weather remains excluded from all primary decision rules.

## Agent Roster & Dependency DAG (`A1`–`A16`)
```
Step 1 [A1 PI Snapshot]
   └──> Step 2 [A2 Data Forensics + A3 Timing Firewall & Leak-Free Builder + Property Tests (fixes C1, M5/M6, M7, M8, M9)]
           ├──> Step 3 [A4 Sequential Settlement + A5 Equal-Menu Baselines + A6 Matched Ablations + A7 Two-Clustering Holm Inference (fixes M3, M4, M9)]
           │       └──> Step 4 [A8 Primary-Source Tornado & Heterogeneous Missing-Price Sensitivity]
           └──> Step 5 [A9 Literature Bib + A10 Pre-Registered RR-Abstain (Commit PREREG_A10 before eval_a10) + A11/A12 Adversarial Attack]
                   └──> Step 6 [A13 Code Figures + Makefile + Pinned Env + Colab + Clean-Clone Reproduction <= ₹0.01]
                           └──> Step 7 [A14 10-12p Manuscript + A15 Difficulty & Verified Viva (fixes C2) + Scripted Traceability Audit]
                                   └──> Step 8 [A16 Independent Re-Derivation + final/* Reconciliation (fixes M8) + Final Clean-Clone Check + Push PR #1]
```

- **Step 1 Acceptance Test:** Branch `finalization` checked out at `b3bb46f`, Python 3.11.5 + `sklearn 1.3.0` verified, `forecaster_2024.pkl` checked, baseline `pytest` (`25 passed, 1 failed`) recorded cleanly. **PASSED.**
