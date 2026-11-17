# Independent Post-Fix Thesis Examiner Review (`MandiGuard`)

**Examiner Role:** Independent Statistical & Red-Team Reviewer (`statistical_and_redteam_reviewer`)  
**Repository:** `/Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent`  
**Audit Date:** 2026-11-17 (Post-Fix Verification against uncommitted cleanup on top of `4fa3948`)  
**Verdict:** **`NEEDS_POLISH`** *(All core Checklist 1–3 statistical, numerical, BibTeX, figure, pytest, file-size, and secret checks **PASS 100%** across the 11 primary documents; verdict is `NEEDS_POLISH` solely due to 1 stale `Exp 15` line in top-level `REPRODUCIBILITY.md:22` plus 3 minor wording/numbering nits noted in Section 5.)*

---

## Executive Summary & Pass/Fail Checklist

| Audit Item | Target Scope | Result | Key Verified Metrics / Evidence |
|:---|:---|:---|:---|
| **1a. Numerical Reconciliation** | `paper/manuscript.md`, `paper/12th_class_easy_reading_edition.md`, `FINDINGS.md`, `README.md`, `PROJECT_STATE.md`, `NOVELTY_AUDIT.md`, `EXPERIMENT_REGISTRY.csv`, `viva/00..03` | **PASS** | `0` numerical discrepancies against `confirmatory_holm_summary.csv`, `exp1`–`exp15`, `configs/frozen_calibration.json`, and `official_datagov_parity_manifest.json`. |
| **1b. `Exp 11`–`Exp 13b` Framing** | Manuscript, Easy-Reading Edition, Guides, `EXPERIMENT_REGISTRY.csv`, `viva/*.md` | **PASS** | Segregated strictly as exploratory Appendix illustrations (not main contributions); `7/7` rows typed `Appendix_Illustration` in `EXPERIMENT_REGISTRY.csv`. |
| **1c. `Exp 15` Dual-View Integrity** | View 1 (`N = 69,526` crossover) + View 2 (`N = 10,162` & `N = 16,849` matched cohorts) | **PASS** | Both views match `exp15_missing_data_open_yard_sensitivity.csv` (`28` rows) identically; zero post-outcome selection bias in `src/evaluation/run_official_parity_and_open_yard_sensitivity.py`. |
| **2a. Stale `d0` Slice Scan** | `EXPERIMENT_REGISTRY.csv`, `FINDINGS.md`, `README.md`, `PROJECT_STATE.md`, `NOVELTY_AUDIT.md`, `paper/*.md`, `viva/*.md` | **PASS** | **`0` hits** for `1035.32`, `1,035.32`, `28359`, `28,359`, `178.46`, `201.59`, `50pct_Clerk`, `100pct_Clerk`. |
| **2b. Hype Phrase Scan** | Same 11 core documents | **PASS** | **`0` hits** for `crushed`, `knockouts`, `knockout`, `undeniable`, `provably superior`, `massive`, `shockingly`, `catastrophic`, `blazing`, `jackpot`, `100% verified`, `100% authentic`, `82.6x`, `82x`. |
| **3a. BibTeX Citation Integrity** | `paper/references.bib` vs `paper/manuscript.md` | **PASS** | **`31/31` BibTeX keys cited** (`Missing: set()`, `Extra: set()`). |
| **3b. Figure Link & Disk Integrity** | `paper/manuscript.md` & `paper/12th_class_easy_reading_edition.md` | **PASS** | **`8/8` `../figures/fig*.png` links** present and valid on disk in both documents. |
| **3c. Automated Test Suite** | `PYTHONPATH=. /Users/adityasharma/anaconda3/bin/python3 -m pytest -v tests` | **PASS** | **`19 passed, 0 failed in 10.03s`**. |
| **3d. File-Size Cap & Secrets** | `git ls-files --cached --others --exclude-standard` (`132` trackable files) | **PASS** | **`0` files `> 10 MB`** (largest: `data/processed/colab_data_pack.tar.gz`, `4.82 MiB`); **`0` secret token hits** (`DATA_GOV_IN_API_KEY` or GitHub PAT prefixes). |
| **4. Temporal Firewall & Inference** | `src/data/build_dispatch_episodes.py`, `src/models/arrival_forecaster.py`, `src/evaluation/bootstrap.py` | **PASS** | Strict `<= t` features/forecasts, `Train 2024` / `Val 2025-01..05` / `Holdout 2025-06..2026-04` + `HP Apple Summer 2026`, causal `arrival_date <= decision_date` LCB maturation, `R=5,000` (`seed=20261117`) Two-Way Bootstrap, Holm `m=4`. |
| **5. Repo-Wide Companion Docs** | `REPRODUCIBILITY.md`, `RESEARCH_DECISIONS.md`, `viva/02`, `paper/manuscript.md` formatting | **NEEDS_POLISH** | Stale `Exp 15` wording at `REPRODUCIBILITY.md:22`; typo at `viva/02:40`; unnumbered table at `paper/manuscript.md:123`; stale `Exp 2c` label at `RESEARCH_DECISIONS.md:14`. |

---

## 1. Statistical & Causal Firewall Audit (`Train` / `Val` / `Holdout`)

1. **Chronological Split Firewall (`configs/config.json`, `src/utils/leakage.py`, `src/evaluation/calibration_and_pretest.py`, `src/evaluation/run_all_experiments.py`):**
   - `Train_2024` (`2024-01-01`..`2024-12-31`, `701,932` rows) trains `CausalArrivalForecaster` (`HistGradientBoostingRegressor`), with `configs/frozen_calibration.json` locking `safety_margin_inr = 50.0` solely on `Val_2025H1` (`2025-01-01`..`2025-05-31`, `280,697` rows / `42,794` episodes, `78.85%` empirical LCB coverage).
   - `Holdout_2025_2026` (`2025-06-01`..`2026-04-08`, `81,048` total / `69,526` shortlisted episodes, `468,816` candidate rows) and `HP Apple Summer 2026` (`2026-06-01`..`2026-08-27`, `1,537` shortlisted episodes) were evaluated strictly post-`e421d15` pre-registration.
   - In `src/models/arrival_forecaster.py:214-260`, conformal residuals enter the rolling `400`-trip buffer via a min-heap strictly when `arrival_date <= date_t`, and quantiles are computed before predicting day `t`.
   - In `src/data/build_dispatch_episodes.py:44-68, 197-220, 269-278`, arrival-weekday openness (`_causal_dow_open_rate` with `tau in {1,2,3}`), price lags/volatilities, and day-`t` NWP/Ridge weather covariates use strictly `<= t` data, while evaluation uses realized ERA5 `[t, t+tau]`.

2. **Two-Way Cluster Bootstrap & Holm–Bonferroni Verification (`src/evaluation/bootstrap.py`, `results/confirmatory_holm_summary.csv`):**
   - Verified `two_way_mandi_week_bootstrap(..., week_block_len=2, reps=5000, seed=20261117)` resamples `174` origin mandis and `23` 2-week blocks jointly via multinomial multiplicity weights, applies Phipson–Smyth `(1 + n_ge) / (reps + 1)` $p$-values, and runs step-down Holm–Bonferroni across `m = 4`:
     - **`H1` (`MG - B1 Mean dNet`):** `+102.7823` INR/qtl, 95% CI `[48.6649, 153.4512]`, `p_raw = 0.0006`, **`p_holm = 0.0012`**, **`SUPPORTED`**.
     - **`H2` (`MG - B2 Mean dNet`):** `+6.1303` INR/qtl, 95% CI `[-17.0161, 25.0171]`, `p_raw = 0.269946`, **`p_holm = 0.269946`**, **`NOT_SUPPORTED`** (candidly disclosed everywhere; `MandiGuard` trades dispatch volume `48.66%` vs `62.11%` for halved LTR `9.97%` vs `18.11%` and reduced `CVaR_10%` `-37.89` vs `-436.67` INR/qtl).
     - **`H3` (`MG - B3 Ep Phantom Incidence`):** `-0.3729` (`4.85%` vs `42.14%`), 95% CI `[-0.4019, -0.3424]`, `p_raw = 0.0002`, **`p_holm = 0.0008`**, **`SUPPORTED`**.
     - **`H4` (`MG Calls - 0.75 * B4 Calls`):** `-3.0548` (`8.75` vs `15.74` = `44.4%` fewer calls), 95% CI `[-3.4408, -2.6906]`, `p_raw = 0.0002`, **`p_holm = 0.0008`**, **`SUPPORTED`** (candidly framed as an expected design consequence of cheap-first ordering whose practical value shows under tight caps like `B = 6`: `+₹104.54/qtl`).

3. **Robustness, Sensitivity & `Exp 14`/`Exp 15` Audit:**
   - **Model-free / `Exp 1` & `Exp 9`:** `B1` (`63,040` dispatches) loses money `40.46%` of the time with `58.94%` closed/variety traps (`46.69%` missing exact variety across 3 days); `Exp 9` LOSO beats `B1` in `6/6` unseen states (`+₹11.50` GJ to `+₹424.19/qtl` HP), holding arrival drops to `3.34%–9.72%` vs `45.29%–55.66%` (`B1`).
   - **`Exp 4` & `Exp 6`:** `3x3` freight (`0.75x..1.25x`) $\times$ spoilage (`0.5x..1.5x`) grid beats `B1` in `9/9` cells (`+₹82.62` to `+₹121.42/qtl`) and `B2` at `1.0x`/`1.5x` spoilage (`+₹5.27` to `+₹14.50/qtl`, trailing `-₹0.02` to `-₹1.52/qtl` only at `0.5x` spoilage); GoI state statutory fees add `+₹7.12/qtl` over uniform `1.5%`.
   - **`Exp 14` (`official_datagov_parity_manifest.json` & `exp14_official_datagov_parity_audit.csv`):** Single-day `2023-10-18` official `data.gov.in` XML spot-check (`6,434` all-India rows, `532` 6-state/4-crop, `181` core-panel, `172` matched keys, `171` exact 10-col matches): `100.00%` `Min_Price`/`Max_Price` and `99.42%` `Modal_Price` parity, accurately disclosed as a single-day spot-check.
   - **`Exp 15` (`exp15_missing_data_open_yard_sensitivity.csv`, `28` rows):**
     - **View 1 (Crossover Curve, `N = 69,526`):** `MandiGuard` leads `B1` and `B3` at `1.5x/10%` (`+₹102.78` / `+₹121.94`), `1.0x/10%` (`+₹91.66` / `+₹109.39`), `0.5x/5%` (`+₹42.43` / `+₹46.12`), and `5_ZeroTrap_BreakEven0_Missing3d` (`+₹82.26` / `+₹73.61`), crossing below `B1`/`B3` on mean only at `4_ZeroDiv_Div0.0x_Disc0pct` (`B1 ₹468.17`, `B3 ₹479.09`, `MG ₹458.17` $\to$ `-₹10.00` vs `B1`, `-₹20.93` vs `B3`, `+₹2.08` vs `B2 ₹456.09`) while still cutting loss trips roughly three-fold (`6.09%` vs `18.52%` `B1`, `20.40%` `B3`) and bounding `CVaR_10%` (`-₹28.70` vs `-₹877.41` / `-₹851.02`).
     - **View 2 (Fair Matched Complete-Observation Cohorts, Identical Episodes Across All 4 Policies):** On `6_Fair_Matched_AllTopK_Observed_d0` (`N = 10,162`), `MandiGuard` (`₹510.89/qtl`, `47.31%` disp, `6.82%` LTR, `-₹36.07` `CVaR_10%`) beats `B1` (`₹472.51`, `+₹38.38`) and `B2` (`₹469.99`, `+₹40.91`), while point-ML `B3` earns `₹553.22` (`+₹42.33` higher mean) at `2.2x` higher LTR (`14.77%`) and `10x` deeper `CVaR_10%` (`-₹362.40`). On `7_Fair_Matched_AllTopK_Observed_3d` (`N = 16,849`), `MandiGuard` (`₹592.53`, `7.74%` LTR, `-₹48.25` `CVaR_10%`) beats `B1` (`₹581.06`, `+₹11.47`) and `B2` (`₹572.09`, `+₹20.44`), while `B3` earns `₹670.38` (`15.02%` LTR, `-₹464.35` `CVaR_10%`).

---

## 2. Numerical Reconciliation & Appendix Segregation Across Audited Documents

Programmatic cross-checking across all **11 target documents** (`paper/manuscript.md`, `paper/12th_class_easy_reading_edition.md`, `FINDINGS.md`, `README.md`, `PROJECT_STATE.md`, `NOVELTY_AUDIT.md`, `EXPERIMENT_REGISTRY.csv`, and `viva/00`–`viva/03`) against `results/*.csv`, `results/*.json`, `configs/*.json`, `data/manifests/*.json`, and source parquets (`2,735,166` rows / `516,428` episodes in `candidates_2017_2023.parquet`; `81,048` total / `69,526` shortlisted holdout episodes; `4,427` HP Apple raw rows) confirms **`0` numeric mismatches**.

- **`Exp 11`–`Exp 13b` Segregation:** Verified across `paper/manuscript.md` (`L35`, `L291–L318`), `paper/12th_class_easy_reading_edition.md` (`L116–L122`), `FINDINGS.md` (`L89–L100`), `README.md` (`L28`), `PROJECT_STATE.md` (`L29`), `EXPERIMENT_REGISTRY.csv` (`7/7` rows tagged `Appendix_Illustration`), and `viva/00`–`viva/03` (`L29`, `L114–L120`, `L120–L135`, `L25`/`L37`) that `Exp 11`–`Exp 13b` are explicitly framed as exploratory post-hoc Appendix illustrations rather than main thesis contributions.
- **`Exp 15` Two-View Consistency:** Verified View 1 (`N = 69,526` crossover) and View 2 (`N = 10,162` & `N = 16,849`) appear accurately and consistently across `paper/manuscript.md` (`L9`, `L33`, `L209–L224`, `L280`, `L287`), `paper/12th_class_easy_reading_edition.md` (`L70–L78`), `FINDINGS.md` (`L22–L51`), `README.md` (`L21–L23`), `PROJECT_STATE.md` (`L25–L27`), and `viva/00`–`viva/03` (`00:L21–L27, L100–L110`; `01:L83–L97`; `02:L147–L153`; `03:L25, L37`). *(Note: `EXPERIMENT_REGISTRY.csv` logs `Exp15a_TrapPenalty_Crossover` and `Exp15b_Fair_Matched_Observed_d0`, and `NOVELTY_AUDIT.md` summarizes `N=10,162` and `0.0x/0%`, all matching CSV values.)*

---

## 3. Stale `d0`, Hype, BibTeX, Figure, Pytest, Size & Secret Audit

1. **Stale `d0` Token Scan (11 target files):** **`0` hits** (`1035.32`, `1,035.32`, `28359`, `28,359`, `178.46`, `201.59`, `50pct_Clerk`, `100pct_Clerk`).
2. **Hype Phrase Scan (11 target files):** **`0` hits** (`crushed`, `knockouts`, `knockout`, `undeniable`, `provably superior`, `massive`, `shockingly`, `catastrophic`, `blazing`, `jackpot`, `100% verified`, `100% authentic`, `82.6x`, `82x`). *(Code-only note: `src/agents/mandiguard_agent.py:80` contains the comment `# Pre-extract arrays for blazing speed...`, outside documentation prose.)*
3. **BibTeX Citations:** **`31/31` keys** in `paper/references.bib` cited in `paper/manuscript.md` (`Missing: set()`, `Extra: set()`).
4. **Figures:** **`8/8` `../figures/fig*.png` links** valid and present on disk in both `paper/manuscript.md` and `paper/12th_class_easy_reading_edition.md`.
5. **Pytest Suite:** Executed `PYTHONPATH=. /Users/adityasharma/anaconda3/bin/python3 -m pytest -v tests` $\to$ **`19 passed in 10.03s` (`0` failed, `0` skipped)**.
6. **File Size & Secret Scan (`git ls-files --cached --others --exclude-standard`):**
   - `132` trackable files; **`0` files `> 10 MB`** (largest: `data/processed/colab_data_pack.tar.gz`, `5,049,010` bytes = `4.82 MiB`).
   - **`0` leaked secret tokens** (`DATA_GOV_IN_API_KEY` or GitHub PAT prefixes).

---

## 4. Flagged Lines & Minor Polish Items (`NEEDS_POLISH` Scope)

Every item below is non-statistical and requires `< 5` minutes of text cleanup before final commit/freeze:

1. **`REPRODUCIBILITY.md:22` *(Stale Pre-Fix `Exp 15` Description — Highest Priority Polish)*:**
   - Currently reads: `...and Exp 15 (4 clerk-upload-lag sensitivity regimes + 100%-observed d0 slice).`
   - Update to match the post-fix script/CSV: `...and Exp 15 (5-step trap-penalty crossover curve across N=69,526 episodes + 2 fair matched complete-observation cohorts at N=10,162 and N=16,849).`
2. **`viva/02_35_viva_questions_and_answers.md:40` *(Typo)* & Filename Count:**
   - Line 40 reads `"peaks into the future"` $\to$ fix to **`"peeks into the future"`**.
   - Minor note: the file contains `44` Q&As (`Q1–Q44`) while keeping filename `02_35_viva_questions_and_answers.md` (leave filename unchanged unless updating all cross-links).
3. **`paper/manuscript.md:123, 243, 278` *(Minor Editorial Nits)*:**
   - `L123`: The 3-row outcome-rules table in Section 4.2 sits unnumbered between `Table 2` (`L80`) and `Tables 3 and 4` (`L182`); consider adding explicit bold captions (`Table 1`–`Table 7`, `Table A1`, and labeling or integrating the Section 4.2 summary).
   - `L243`: `"dominates upfront checking"` $\to$ `"Pareto-dominates upfront checking"` for tighter precision.
   - `L278`: Mentions `"Our 19/19 passing unit tests verify..."` (candidly scoped, though `RESEARCH_DECISIONS.md` Decision 5 originally discouraged test counts in manuscript prose).
4. **`RESEARCH_DECISIONS.md:14` *(Stale Subgroup Tag)*:**
   - References `(Exp 2c)` for the 4-state native-NWP check; update to **`(Exp 2b)`** to match `results/exp2b_by_state_commodity.csv` and `paper/manuscript.md`.

---

## 5. Honest Post-Fix Examiner Scoring & Irreducible External Limitation

| Evaluation Dimension | Post-Fix Score | Examiner Rationale |
|:---|---:|:---|
| **M.Tech Thesis Quality** | **8.9 / 10** | Rigorous multi-modal data engineering (`42.72M` raw records $\to$ `883,406` panel rows, OSRM, ERA5/NWP/NASA POWER, 8 GoI anchors), leak-free chronological split + `e421d15` pre-registration, properly clustered `174 x 23` bootstrap with Holm FWER control, and exemplary scientific candor (`H2` failure, HP Apple `Grade A` under-dispatch, `Exp 15` open-yard `B3` tradeoff, Appendix segregation). |
| **Applied Publication Readiness** *(e.g., ACM COMPASS / ICTD)* | **8.2 / 10** | Strong empirical measurement of *Phantom Spatial Arbitrage* and transparent counterfactual sensitivity (`Exp 15`) that directly addresses missing-row selection concerns; capped below `9+` strictly by the absence of prospective field-pilot evidence. |
| **Methodological & Systems Novelty** | **7.6 / 10** | Honest applied/systems novelty: no claims of new conformal theorems, physical rot laws, or LLM/RL policies; genuine contribution lies in problem reframing (`REFUSE_PHANTOM_SPREAD`), multi-state phantom erosion decomposition, and deterministic cheap-first cascade (`T1 -> T2 -> T3 -> T4`) on a clean reproducible benchmark. |

### Remaining Irreducible External Limitation
No software, bootstrap, or sensitivity fix can manufacture primary physical-world evidence: **the study still lacks live farmer interviews, prospective field dispatch pilots, actual truck freight invoices, and destination weighment/spoilage receipts**. Trucking tariffs (`₹35 + ₹0.45/km`), $Q_{10}$ spoilage anchored to MoFPI/NABCONS (2022), and closed-yard diversion costs remain structural economic models validated only via sensitivity bounds (`Exp 6`, `Exp 15`), while the `data.gov.in` XML verification (`Exp 14`) covers a single snapshot day (`2023-10-18`, `172` matched keys) and the `19/19` passing `pytest` suite verifies deterministic code execution, schema/checksum integrity, and temporal split hygiene—not real-world farm-gate economic truth.
