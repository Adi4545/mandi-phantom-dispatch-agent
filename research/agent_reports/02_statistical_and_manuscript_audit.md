# MandiGuard Independent Statistical, Red-Team & Manuscript Audit (Final Verification Including `Exp 14` & `Exp 15`)

**Auditor Role:** Independent Statistical & Red-Team Reviewer  
**Repository:** `/Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent`  
**Audit Date:** 2026-11-17  
**Overall Verdict:** **PASS** *(`0` numeric discrepancies `> 0.1` across all 8 updated documents; `Exp 14` `.gov.in` XML SHA-256 + price parity verified; `Exp 15` clerk-upload-lag & 100%-observed `d0` open-yard results verified; `0` secrets/API keys; `0` manuscript jargon hits; `31/31` BibTeX citations; `8/8` figures; `0` trackable files `> 10 MB`; `19/19` pytest passing; only non-blocking label note: `README.md:29` text says `exp1–exp13b` while `results/` now spans `exp1`–`exp15`)*

---

## 1. `Exp 14` & `Exp 15` Integrity, SHA-256 Parity & Secrets Audit — PASS

1. **Official `data.gov.in` XML Provenance & Parity (`Exp 14`):**
   - Verified `shasum -a 256 data/raw/official_datagov_datewise_prices.xml` = `0df451235fe6f11c517947daea136254c937a20703425f377ca69310dbc2cb06` (`2,439,430` bytes = `2.3M`), matching `data/manifests/official_datagov_parity_manifest.json:8-9` identically.
   - Inspected `src/evaluation/run_official_parity_and_open_yard_sensitivity.py:45-136` and cross-checked `results/exp14_official_datagov_parity_audit.csv`:
     - Source: `data.gov.in Resource 9ef84268-d588-465a-a308-a864a43d0070 (Date-Wise XML)`, date `2023-10-18`.
     - Counts: **`6,434` all-India rows**, **`532` 6-state/4-crop rows**, **`181` 178-panel core rows**, **`172` matched keys** (`171` exact 10-column matches).
     - Exact rupee parity: **`100.00%` `Min_Price`**, **`100.00%` `Max_Price`**, **`99.42%` `Modal_Price`**, and **`94.48%` exact full-row match rate** across `gov_178_panel_rows`.
2. **Missing-Data / Clerk-Upload-Lag & Open-Only `d0` Sensitivity (`Exp 15`):**
   - Inspected `src/evaluation/run_official_parity_and_open_yard_sensitivity.py:139-257` and confirmed strictly causal pre-holdout usage (`forecaster_2024.pkl` streamed from `val_start` with frozen `safety_margin_inr = 50.0` evaluated on `Holdout_2025_2026`).
   - Cross-checked all 20 rows of `results/exp15_missing_data_open_yard_sensitivity.csv`:
     - Regime 1 (`1_Baseline_Physical_1.5x_Diversion`, `N = 69,526`): `MandiGuard ₹452.79/qtl` (`9.97%` LTR) vs `B1 ₹350.01` (`40.46%`), `B2 ₹446.66`, `B3 ₹330.85` $\to$ **`MG - B1 = +₹102.78/qtl`**.
     - Regime 2 (`2_No_Return_Haul_1.0x_OneWay_Only`, `N = 69,526`): `MandiGuard ₹454.27` vs `B1 ₹362.61` $\to$ **`+₹91.66/qtl`**.
     - Regime 3 (`3_50pct_Clerk_Upload_Lag_OpenAtRef90`, `N = 69,526`): `MandiGuard ₹465.35` (`7.09%` LTR) vs `B1 ₹381.74` (`36.12%` LTR), `B2 ₹465.08` (`14.45%`), `B3 ₹360.60` $\to$ **`+₹83.61/qtl`**.
     - Regime 4 (`4_100pct_Clerk_Upload_Lag_LocalParity`, `N = 69,526`): `MandiGuard ₹456.19` vs `B1 ₹378.85`, `B2 ₹452.78`, `B3 ₹363.12` $\to$ **`+₹77.34/qtl`**.
     - Regime 5 (`5_Observed_Arrival_Day_d0_Only_ZeroMissing`, `Dispatched_With_Observed_d0_Price`): **`MandiGuard` (`N = 28,359`) earns `₹1,035.32/qtl` (`4.98%` LTR)** vs `B1` (`N = 25,882`: `₹856.86/qtl`, `12.32%` LTR), `B2` (`N = 32,679`: `₹833.73/qtl`, `10.32%` LTR), and `B3` (`N = 22,224`: `₹1,009.17/qtl`, `9.00%` LTR), beating `B1` by **`+₹178.46/qtl`** and `B2` by **`+₹201.59/qtl`**.
3. **Secrets & API-Key Audit:**
   - Verified `run_official_parity_and_open_yard_sensitivity.py:60` reads optional `DATA_GOV_IN_API_KEY` solely from environment variables (`os.environ.get`), `0` `.env*` files exist, and repository-wide regex scan confirmed **`0` project/cloud/API secrets** (the only regex matches across the repo are public `BOOMR_API_key="C4E7H-KSCMC-422L4-W3EM5-U36MF"` Akamai Boomerang RUM snippets embedded inside downloaded official `pib.gov.in` HTML releases).

---

## 2. Every-Number Cross-Check & Transparent Disclosures — PASS

1. **Zero `> 0.1` Discrepancies Across All 8 Audited Documents:**
   - Programmatically verified every numeric entry across `paper/manuscript.md`, `paper/12th_class_easy_reading_edition.md`, `viva/00_career_defense_master_sheet.md`, `FINDINGS.md`, `README.md`, `REPRODUCIBILITY.md`, `PROJECT_STATE.md`, and `EXPERIMENT_REGISTRY.csv` against `results/*.csv` (`exp1`–`exp15`, `confirmatory_holm_summary.csv`), `results/*.json`, `configs/*.json`, `data/manifests/*.json`, `data/processed/state_apmc_and_loss_parameters.csv`, `data/raw/official_govt_survey_parameters.json`, and `data/interim/candidates_2017_2023.parquet` (`2,735,166` candidate rows across `516,428` episodes).
   - Also confirmed the prior `82x` rounding at `paper/manuscript.md:228` has been corrected to **`82.6x`** (`8487.24 / 102.76 = 82.59x`). *(Note: `L5` abstract hook range `"₹700 to ₹1,330"` remains an intentional descriptive summary of `Exp 1` Onion `₹704.50` to All-Holdout `₹1,330.49`, with exact decimals reported at `L171, L174`.)*
2. **Transparent Disclosures Verified:**
   - `paper/manuscript.md:62`, `README.md:6`, `viva/00_career_defense_master_sheet.md:82`, `FINDINGS.md:65`: explicitly state bulk 2017–2026 CSVs came from a public AGMARKNET archive mirror and were cross-verified directly against official `data.gov.in` Resource `9ef84268-d588-465a-a308-a864a43d0070`.
   - `paper/manuscript.md:278`, `paper/12th_class_easy_reading_edition.md:72`, `viva/00_career_defense_master_sheet.md:84`: explicitly distinguish observed market prices, yard activity, OSRM road hours, and weather from modeled trucking costs (`₹35 + ₹0.45/km`), $Q_{10}$ spoilage, API billing (`₹0.05/call`), and exploratory scenarios (`Exp 11–13`).
   - Minor non-blocking doc-label note: `README.md:29` text mentions `(exp1–exp13b)` for `results/` rather than `(exp1–exp15)`, although `README.md:20` explicitly reports `Exp 14` and `Exp 15`.

---

## 3. Manuscript Hygiene, GitHub Packaging & Execution Proofs — PASS

1. **Manuscript Formatting & Anti-Jargon (`paper/manuscript.md`):**
   - `0` Git hashes (`e421d15`, `2663e42`, `59bef3f`, or hex strings), `0` SHA-256 strings, `0` `pytest` / unit-test mentions, `0` internal `.py`/`.parquet`/`.csv`/`.json`/`.ipynb`/`.xml` paths in body prose.
   - `paper/references.bib`: **`31/31` BibTeX keys cited (`0` missing, `0` uncited)**.
   - Figures: **`8/8` valid PNG links on disk** in both `paper/manuscript.md` and `paper/12th_class_easy_reading_edition.md`.
2. **File-Size Cap & `.gitignore` (`<= 10 MB`):**
   - Verified `git ls-files -co --exclude-standard`: **`0` trackable files `> 10 MB`**. Largest non-ignored artifact is `data/processed/colab_data_pack.tar.gz` (`4.815 MiB` / `4.82 MB`); `data/raw/official_datagov_datewise_prices.xml` is `2.3M`.
3. **Pytest Suite Verification:**
   - Re-ran `PYTHONPATH=. /Users/adityasharma/anaconda3/bin/python3 -m pytest -v tests` $\to$ **`19 passed in 2.73s`**, matching `results/pytest_execution.log` (`19 passed in 3.69s`), including `test_official_datagov_parity_and_open_yard_sensitivity`.
