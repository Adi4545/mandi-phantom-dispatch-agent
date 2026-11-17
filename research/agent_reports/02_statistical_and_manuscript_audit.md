# MandiGuard Independent Statistical, Red-Team & Manuscript Audit (Final Phase A + Phase B + Class-12 Rewrite & Packaging)

**Auditor Role:** Independent Statistical & Red-Team Reviewer  
**Repository:** `/Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent`  
**Audit Date:** 2026-11-17  
**Overall Verdict:** **PASS** *(0 factual/statistical discrepancies; all core pillars, causal firewalls, worked arithmetic, `ZeroCloud_Full` mechanism, packaging caps, `18/18` pytest checks, `11/11` notebooks, `31/31` BibTeX citations, and `8/8` figures verified; minor non-blocking prose/draft rounding notes itemized in Section 2.4 for transparency)*

---

## 1. Git Pre-Registration, Temporal Firewall & Zero-Leakage Audit — PASS

1. **Git Pre-Registration Ordering (`e421d15` $\prec$ `2663e42`):**
   - Verified via `git log --oneline`:
     - `e421d15` (*"Pre-register H1-H4 hypotheses and freeze Val_2025H1 calibration before holdout evaluation"*) precedes `2663e42` (*"Expand to 10-year 2017-2026 dataset, add ZeroCloud/ACI/FPO/SpoilageClock experiments, minimal metrics, and pass independent audit"*) as direct parent on `main`.
     - `e421d15` committed `configs/config.json`, `configs/frozen_calibration.json`, `data/processed/state_apmc_and_loss_parameters.csv`, `data/raw/official_govt_survey_parameters.json`, and raw manifests strictly prior to all holdout `results/*.csv`, `paper/manuscript.md`, `EXPERIMENT_REGISTRY.csv`, and `figures/*.png` in `2663e42`.
2. **Causal Splits & Zero Future Leakage:**
   - Verified `src/evaluation/calibration_and_pretest.py:31-37` enforces `date_dt <= "2024-12-31"` & `arr_dt <= "2024-12-31"` for `Train_2024` (`701,932` candidate rows, `96,468` episodes) and `2025-01-01 <= date_dt <= 2025-05-31` & `arr_dt <= 2025-05-31` for `Val_2025H1` (`280,697` candidate rows, `42,794` episodes; full validation episode table including boundary arrivals = `48,631` episodes / `43,103` shortlisted; `Holdout_2025_2026` = `81,048` total / `69,526` shortlisted; `HP_Apple` = `4,129` total / `1,608` holdout / `1,537` shortlisted).
   - Verified `configs/frozen_calibration.json` locks `frozen_safety_margin_inr = 50.0` (`Val` coverage `78.85%`, `Mean dNet = ₹351.36/qtl`, `PLR = 9.68%`) strictly before holdout.
   - Verified `src/models/arrival_forecaster.py:132-265` trains strictly on past lags (`FEATURE_COLS`, 17 causal features), clips `target_ret` during training (`[-0.60, 0.80]`), and uses a min-heap `matured_dates_heap` (`L215-228`) so residuals and Gibbs–Candès `ACI` updates (`adaptive_gamma=0.005`, `alpha` clipped to `[0.02, 0.45]`) enter ONLY after `arrival_date <= decision_date t`.
   - Verified `src/evaluation/run_all_experiments.py:218-240` streams causal predictions from `val_start` (`2025-01-01`) onward and isolates untouched holdout `2025-06-01`..`2026-04-08` (`69,526` shortlisted episodes).
3. **Manifests & Ground-Truth Surveys:**
   - Verified `data/manifests/decade_agmarknet_manifest.json`: `42,722,187` raw streamed CSV rows (`28,278,417` in `2017–2023` + `14,443,770` in `2024–2026`) $\to$ `883,406` balanced 178-mandi rows (`623,363` + `260,043`), all `sha256_raw_csv` and `output_parquet.sha256` present.
   - Verified `data/manifests/nasa_power_manifest.json`: `291,384` daily rows (`2017-01-01..2023-12-31`), `114` `0.5-deg` grid cells, `0.0` missingness across all 4 weather variables, `sha256` present.
   - Verified `data/manifests/climate_manifest.json`: `141,955` rows (`2024-01-01..2026-09-05`), `145` ERA5 cells (`102` NWP + `43` causal ERA5 nowcaster), `0.0` null rates after causal ffill.
   - Verified `data/raw/hp_apple_daily_2025_2026.csv` directly: `4,427` rows across `42` markets (`2025-11-07` to `2026-09-01`), grade counts `Medium: 1,945`, `Grade B: 1,264`, `Grade A: 1,007`, `Local: 78`, `Grade Range-1: 75`, `Grade C: 51`, `Small: 4`, `Large: 3`.
   - Verified `data/manifests/road_network_manifest.json`: `220` geocoded markets (`150` exact, `70` district centroids), `8,147` corridors (`15–500 km`).

---

## 2. Every-Number & Mechanistic Cross-Check — PASS

Audited all numbers across `paper/manuscript.md`, `paper/12th_class_easy_reading_edition.md`, `viva/00_career_defense_master_sheet.md`, `README.md`, `REPRODUCIBILITY.md`, and `research/agent_reports/03_autonomous_agents_12th_grade_and_viva_synthesis.md` against `results/*.csv`, `results/*.json`, `configs/frozen_calibration.json`, `EXPERIMENT_REGISTRY.csv`, `data/processed/state_apmc_and_loss_parameters.csv`, `data/raw/official_govt_survey_parameters.json`, and `data/manifests/*.json`.

### 2.1 Worked 5-Line Example vs `src/evaluation/payoff_model.py` — EXACT (`< 1e-9`)
- Scenario: `Tomato`, `Madhya Pradesh` (`1.5%` fee), `local_price = ₹1,400/qtl`, `screen_dest_price = ₹2,000/qtl`, `road_km = 200`, `truck_hours = 6.0`, `temp = 40°C`, `RH <= 70%`, `rain = 0`, `same_district = False`, `8%` conformal drop cushion:
  - `compute_spoilage_fraction`: `0.0325 * (6/24) * 2^((40-20)/10) = 0.0325 * 0.25 * 4 = 0.0325` (`-₹65.00` on `₹2,000` $\to$ `₹1,935.00/qtl` surviving value).
  - `compute_freight_inr`: `35.0 + 0.45 * 200.0 + 0.015 * 1400.0 = 35.0 + 90.0 + 21.0 = ₹146.00/qtl` (`1,935.00 - 146.00 = ₹1,789.00/qtl`).
  - `8%` safety cushion (`T4`): `0.08 * 1935.00 = -₹154.80/qtl` (`1,789.00 - 154.80 = ₹1,634.20/qtl`).
  - Net gain above local (`₹1,400`): `+₹234.20/qtl` = **`+₹7,026.00` per 30-qtl truck** (`> ₹50/qtl` frozen hurdle $\to$ `DISPATCH`).
- Matches `paper/manuscript.md:95-101`, `paper/12th_class_easy_reading_edition.md:27-40`, `viva/00_career_defense_master_sheet.md:21-27`, and `research/agent_reports/03_autonomous_agents_12th_grade_and_viva_synthesis.md:89-95` identically.

### 2.2 Mechanistic & Scientific Fidelity Checks — VERIFIED
- **`ZeroCloud_Full` Pre-Ranking (`+₹2.54/qtl` lift):** Verified `src/agents/mandiguard_agent.py:56-75` computes `cached_f = compute_freight_inr(...)` and sorts Step-0 candidates by `screen_spread - cached_f` before slicing top-`k_max = 5`, explaining accurately why `MandiGuard_ZeroCloud_Full` outperforms `MandiGuard_Standard` (`₹455.33/qtl` & `9.89%` LTR vs `₹452.79/qtl` & `9.97%` LTR) while reducing live calls to `5.53` (`-64.9%` API spend). Verified in `paper/manuscript.md:268`, `paper/12th_class_easy_reading_edition.md:85`, `viva/00_career_defense_master_sheet.md:67`, and `03_...md:258-262`.
- **Denominator Clarity (`₹386.02` vs `₹350.01`, `9.97%` vs `4.85%`):** Verified explicitly reconciled in `paper/manuscript.md:171,179` (`386.02 * 0.9067 = ₹350.01` unconditional across `69,526` episodes vs `63,040` dispatched; `48.66% * 9.97% = 4.85%` vs `93.05% * 45.28% = 42.14%` $\to$ `-37.29 pp` episode phantom reduction in `H3`), `paper/12th_class_easy_reading_edition.md:49-53,63`, and `viva/00_career_defense_master_sheet.md:40-41,58-59`.
- **Honest Tradeoffs Reported Without Spin:**
  - `H2` `NOT_SUPPORTED` (`+₹6.13/qtl`, `95% CI [-₹17.02, +₹25.02]`, `p_Holm = 0.269946`; safety-vs-lottery tradeoff `9.97%` vs `18.11%` LTR and `-₹37.89` vs `-₹436.67` CVaR10, `+₹31.82/qtl` in 4-state `42,766`-ep native NWP subset).
  - `Exp 3` HP Apple (`1,537` lots): `MandiGuard` mean `₹605.06/qtl` (`18.67%` dispatch) below `B2` (`₹1,150.83/qtl`, `33.64%`) and `B1` (`₹841.58/qtl`) due to `2024` ungraded model over-abstaining on scarce `Grade A` (`5.39%` dispatch), while cutting closed traps `94.14% -> 13.24%`, cutting CVaR10 `-₹8,487.24 -> -₹102.76/qtl`, flipping `Grade B` `-₹427.54 -> +₹833.70/qtl`, and `MandiGuard_ACI` cutting Apple CVaR10 `-27.6%` (`-₹102.76 -> -₹74.42/qtl`, `alpha_Apple = 0.164`).
  - `Exp 4` `No_T3_Weather`: removing `T3` lifts unconditional profit `+₹2.46/qtl` (`₹455.25` vs `₹452.79/qtl`), candidly disclosed alongside its cost in `21,656` extreme heat/rain episodes (higher LTR `11.39%` vs `10.10%` and worse CVaR10 `-₹67.49` vs `-₹57.11/qtl`).

### 2.3 Key Tables & Derived Quantities Cross-Check — ALL EXACT (`<= 0.1` tolerance)
- `results/confirmatory_holm_summary.csv`: `H1` `+102.7823` `[48.6649, 153.4512]` (`p_raw=0.0006`, `p_holm=0.0012`, `SUPPORTED`), `H2` `+6.1303` `[-17.0161, 25.0171]` (`p_raw=0.269946`, `p_holm=0.269946`, `NOT_SUPPORTED`), `H3` `-0.3729` `[-0.4019, -0.3424]` (`p_raw=0.0002`, `p_holm=0.0008`, `SUPPORTED`), `H4` `-3.0548` `[-3.4408, -2.6906]` (`p_raw=0.0002`, `p_holm=0.0008`, `SUPPORTED`), `174` origin mandis $\times$ `23` 2-week blocks, `69,526` episodes.
- Truckload & household scale derivations: `102.7823 * 30 = +₹3,083.5` (`13,583.6 - 10,500.2 = 3,083.4`), `3,083.5 / 3,798 = 81.2%`; `-37.89 * 30 = -₹1,136.7`, `-436.67 * 30 = -₹13,100.1`, `-1,062.66 * 30 = -₹31,879.8`.
- `Exp 9` LOSO (`6/6` states beat `B1`): exact differences verified against `results/exp9_loso_transfer_and_arrival_drop.csv` (`+424.19` HP, `+122.79` MP, `+69.51` KA, `+61.54` UP, `+55.39` MH, `+11.50` GJ; MG arrival drop `3.34%–9.72%` vs `B1` `45.29%–55.66%`).
- `Exp 10` (`661,192` matched episodes across `6` regimes), `Exp 10b` (`701,932` / `1,668,451` / `3,437,098` rows $\to$ `₹452.79` / `₹454.74` / `₹454.94`), `Exp 11` (`Direct_Quantile_GBDT_Q20` `₹459.02`, `Deep_MLP_Conformal` HP Apple `₹615.34`, `aci_diagnostics.json`: Tomato `0.038`, Apple `0.164`), `Exp 12` (`ZeroCloud_Full` `₹455.33` / `5.53` calls / `₹2,764`; `ZeroCloud_Satisficing` `₹440.48` / `3.84` calls / `₹1,922` / `0.075 ms`), `Exp 13` / `13b` (`FPO 90-qtl` `₹477.28` / `₹14,318.5`; `Split_Top2` `9.85%` closed traps = `-39.08%` relative vs `16.17%`, `8.09%` LTR, `-₹26.40/qtl` CVaR10; Spoilage Clock Tomato `110.8h / 48.2h / 24.1h`, Onion `183.7h / 79.9h / 40.0h`, Potato `418.6h / 182.2h / 91.1h`), `results/sample_farmer_sms_cards.txt`, and `README.md` (`<= 4.82 MB` actual max file `colab_data_pack.tar.gz` = `5,049,010 B` = `4.815 MiB`).

### 2.4 Minor Non-Blocking Rounding Notes (Transparency Log)
No table entries, statistical test values, or experimental conclusions contain errors. Two minor prose/draft rounding notes `> 0.1` are recorded transparently:
1. `paper/manuscript.md:228`: writes `"improves worst-10% losses 82x (-₹102.76/qtl)"` — exact ratio `8487.24 / 102.76 = 82.59x` (truncated integer `82x` vs `82.6x`/`83x`; `0.59x` low). Also `L5` opens with the prose hook range `"₹700 to ₹1,330"` (`0.49` below `1,330.49` and `4.50` below Onion `704.50`, with exact values given at `L171, L174`). *(Prose multiplier adjectives `"four-fold"` at `L217`/`12th:L69` vs `4.15x` and `"seven-fold"` at `L228`/`viva:L37` vs `7.11x` are rounded integer multipliers.)*
2. `research/agent_reports/03_autonomous_agents_12th_grade_and_viva_synthesis.md:106,157`: Critic's *pre-rewrite draft suggestions* wrote `"₹1,330/qtl"` (`-0.49` vs `1,330.49`) and `"₹404/qtl to ₹299/qtl"` (`+0.15` vs `403.85`, `-0.31` vs `299.31`). Both were **NOT** propagated into final `paper/manuscript.md:171,223` or `paper/12th_class_easy_reading_edition.md:70`, which kept exact two-decimal figures. (Similarly, `03_...md:211` says `"42.7 million"` / `"nearly 5x"` for `42,722,187` / `4.90x`.)

---

## 3. Class-12 Readability, Anti-Jargon, Bibliography & Figures — PASS

1. **Class-12 Readability Audit:** Verified `paper/manuscript.md`, `paper/12th_class_easy_reading_edition.md`, and `viva/00_career_defense_master_sheet.md` provide plain-English glosses inline for every dense concept (phantom arbitrage, cultivar mismatch, two-way cluster bootstrap, Holm–Bonferroni, 80% conformal LCB cushion, ACI, CVaR10%, Q10 decay, exchangeability, ZeroCloud, FPO), include the 1-line ASCII timeline (`manuscript.md:129`), the 5-line arithmetic walkthrough before formal equations, and the 10-term mini-dictionary (`12th_class_easy_reading_edition.md:94-107`).
2. **Manuscript Anti-Jargon (`paper/manuscript.md`):**
   - `0` Git commit hashes (`e421d15`, `59bef3f`, `2663e42`, or 7+ hex strings).
   - `0` SHA-256 strings.
   - `0` `pytest` / unit-test mentions in prose.
   - `0` internal `.py` / `.parquet` / `.csv` / `.json` / `.ipynb` file paths in body prose.
3. **Bibliography & Figures:**
   - `paper/references.bib` vs `paper/manuscript.md`: **`31/31` BibTeX keys cited (`0` missing, `0` uncited)**.
   - Figures: **`8/8` `../figures/fig1..fig8.png` files exist on disk (`172,886`–`401,299` bytes)** and are referenced cleanly in both `paper/manuscript.md` (`L176, 204, 220, 225, 232, 234, 254, 272`) and `paper/12th_class_easy_reading_edition.md` (`L21, 66, 74, 76, 78, 80, 88, 90`).

---

## 4. GitHub Packaging & Execution Proofs — PASS

1. **`.gitignore` & Repository File Size Cap (`<= 10 MB`):**
   - `.gitignore` excludes `data/processed/candidates_6state.parquet` (`77M`), `data/interim/candidates_2017_2023.parquet` (`126M`), `data/interim/colab_stage/`, `data/interim/nasa_power_2017_2023_cache.parquet`, and `mandiguard_colab_work/`.
   - Verified **`0` tracked files `> 10 MB`** and **`0` non-ignored files `> 10 MB`**; largest non-ignored artifact is `data/processed/colab_data_pack.tar.gz` (`5,049,010` bytes = `4.82 MiB`).
2. **Independent Pytest Verification:**
   - Executed `PYTHONPATH=. /Users/adityasharma/anaconda3/bin/python3 -m pytest -v tests` $\to$ **`18 passed in 5.39s`**, matching `results/pytest_execution.log` (`18 passed in 4.73s`).
3. **Notebooks Verification:**
   - Verified all **`11/11` notebooks** (`notebooks/00_*.ipynb` through `09_*.ipynb` + `colab_standalone_reproduction.ipynb`) executed cleanly with `errors = []` across every cell.
