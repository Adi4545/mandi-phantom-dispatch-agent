# Reproducibility & Verification Guide — `MandiGuard`

## 1. Environment Requirements
* **OS / Tested Hardware:** macOS (`arm64`), 8 GB RAM (`Python 3.11.5`), also portable cleanly to Linux / Google Colab.
* **Packages (`environment/requirements.txt`):** `numpy`, `pandas`, `pyarrow`, `scikit-learn`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `requests`, `beautifulsoup4`, `pypdf`, `pytest`, `jupyter`, `nbconvert`.

## 2. Deterministic Execution Order (End-to-End Pipeline)
1. **Official Market & Geospatial Data (`src/data/`):**
   * `extract_agmarknet_multistate.py`: Streams 2024–2026 daily AGMARKNET CSV archives (`14,443,770` raw rows -> `260,043` causally `2024`-ranked panel rows across `178` mandis + SHA-256 manifest).
   * `live_agmarknet_api.py`: Executes 22 open unauthenticated Nov-2026 live API queries against `api.agmarknet.gov.in`.
   * `build_road_network.py`: District-validated geocoding (`220` mandis) + OSRM public highway routing (`8,147` intra-state corridors `15–500 km`).
   * `fetch_climate_data.py`: Combines `145/145` ECMWF ERA5 `0.1°` daily grids with `102/145` Open-Meteo Historical NWP grids + causal $\le t$ `2024`-trained Ridge nowcaster on the remaining `43` cells.
   * `build_official_govt_survey_table.py`: Downloads & hashes 8 official open GoI PIB HTML/PDF documents + GoHP Economic Survey 2025–26 PDF -> `data/processed/state_apmc_and_loss_parameters.csv`.
   * `build_dispatch_episodes.py`: Builds zero-leakage episode and candidate tables (`episodes_6state.parquet`, `candidates_6state.parquet`, `episodes_hp_apple.parquet`, `candidates_hp_apple_grade.parquet`).
   * `extract_decade_2017_2023.py`: Streams historical 2017–2023 AGMARKNET archives (`42,722,187` cumulative raw rows `2017–2026` -> `883,406` rows in fixed 178-mandi panel) alongside `291,384` daily NASA POWER agroclimatology rows (`114` `0.5°` grids, `0.0%` missing).
2. **Stage I Pre-Holdout Training & Calibration (`src/evaluation/calibration_and_pretest.py`):**
   * Trains `CausalArrivalForecaster` strictly on `Train_2024` (`arrival_date <= 2024-12-31`).
   * Freezes `safety_margin_inr = 50.0` solely on `Val_2025H1` (`2025-01-01..2025-05-31`).
3. **Stage I Holdout, Decade, Parity & Sensitivity Experiments (`src/evaluation/`):**
   * `run_all_experiments.py`: Evaluates `B0`–`B6`, `MandiGuard`, ablations `T1`–`T4`, budget frontier, $3\times 3$ sensitivity + fee ablation, live check + `R=5,000` Two-Way Origin-Mandi $\times$ 2-Week-Block Bootstrap (`seed=20261117`, Holm $m=4$).
   * `run_creative_decade_and_modern_experiments.py`: Runs `Exp 10` (6 macro regimes `2017H2–2026`, `661,192` eps) & `Exp 10b` (`1-Yr / 3-Yr / 8-Yr` scaling) plus Appendix illustrations `Exp 11` (`ACI`/plug-in predictors), `Exp 12` (`ZeroCloud`), and `Exp 13/13b` (`FPO` pooling, `Split Top-2`, Spoilage Clock & SMS cards).
   * `run_official_parity_and_open_yard_sensitivity.py`: Runs `Exp 14` Dual-Tier Parity Audit (Tier-1 `data.gov.in` XML `2023-10-18` `172` matched keys: `100.0%` Min/Max, `99.42%` Modal + Tier-2 149-day AGMARKNET 2.0 `hp_apple_daily_2025_2026.csv` `2,042` matched keys: `100.00%` Min/Max/Modal) and `Exp 15` (`5`-step trap-penalty crossover curve across `N = 69,526` + `2` fair matched cohorts at `N = 10,162` and `N = 16,849`).
4. **Stage II Mechanistic Autopsy & Validation-Calibrated `MandiGuard-CRC` (`src/evaluation/run_mechanistic_autopsy_and_crc.py`):**
   * Computes `Exp 16` (`results/exp16_censored_bias_and_coverage_illusion.csv`) proving censored-arrival bias, heteroscedastic coverage illusion, and HP Apple sub-grade `T1` sparsity.
   * Trains `UncensoredCRCForecaster` strictly on settled 2024 outcomes (`arrival_date + 2d <= 2024-12-31`), calibrates $\lambda^* = 0.15$ strictly on `Val_2025H1`, and evaluates `Exp 17` (`results/exp17_uncensored_crc_validation.csv` & `results/exp17_crc_bootstrap_comparisons.csv`).
5. **Figures, First-Principles PDF, Tests & Notebooks:**
   * `src/visualization/make_figures.py`: Generates all 9 300-DPI PNG figures (`fig1`–`fig9`) in `figures/`.
   * `scripts/build_first_principles_defense_pdf.py`: Compiles `docs/MandiGuard_First_Principles_and_Thesis_Defense_Handbook.html` and `.pdf` (via headless Chrome, `< 10 MB`).
   * `PYTHONPATH=. python3 -m pytest -v tests`: Runs all automated anti-leakage, SHA-256 manifest, survey parameter, ZeroCloud/ACI, Dual-Tier official parity, sensitivity, and Stage-II `MandiGuard-CRC` unit tests (`100%` offline reproducible).
   * `src/utils/build_notebooks.py` + `jupyter nbconvert --execute`: Builds & executes notebooks `00`–`09` plus standalone Google Colab bundle (`notebooks/colab_standalone_reproduction.ipynb` + `data/processed/colab_data_pack.tar.gz`, `4.83 MB < 10 MB`).
