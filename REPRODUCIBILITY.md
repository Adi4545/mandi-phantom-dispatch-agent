# Reproducibility & Verification Guide — `MandiGuard`

## 1. Environment Requirements
* **OS / Tested Hardware:** macOS (`arm64`), 8 GB RAM (`Python 3.11.5`), also portable cleanly to Linux / Google Colab.
* **Packages (`environment/requirements.txt`):** `numpy`, `pandas`, `pyarrow`, `scikit-learn`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `requests`, `beautifulsoup4`, `pypdf`, `pytest`, `jupyter`, `nbconvert`.

## 2. Deterministic Execution Order (End-to-End Pipeline)
1. **Official Market & Geospatial Data (`src/data/`):**
   * `extract_agmarknet_multistate.py`: Streams official 2024–2026 daily AGMARKNET CSV archives (`14,443,770` raw rows -> `260,043` causally `2024`-ranked panel rows across `178` mandis + SHA-256 manifest).
   * `live_agmarknet_api.py`: Executes 22 open unauthenticated Nov-2026 live API queries against `api.agmarknet.gov.in`.
   * `build_road_network.py`: District-validated geocoding (`220` mandis) + OSRM public highway routing (`8,147` intra-state corridors `15–500 km`).
   * `fetch_climate_data.py`: Combines `145/145` ECMWF ERA5 `0.1°` daily grids with `102/145` Open-Meteo Historical NWP grids + causal $\le t$ `2024`-trained Ridge nowcaster on the remaining `43` cells.
   * `build_official_govt_survey_table.py`: Downloads & hashes 8 official open GoI PIB HTML/PDF documents + verified GoHP Economic Survey 2025-26 PDF -> `data/processed/state_apmc_and_loss_parameters.csv`.
   * `build_dispatch_episodes.py`: Builds zero-leakage episode and candidate tables (`episodes_6state.parquet`, `candidates_6state.parquet`, `episodes_hp_apple.parquet`, `candidates_hp_apple_grade.parquet`).
   * `extract_decade_2017_2023.py`: Streams historical 2017–2023 official AGMARKNET archives (`42,722,187` cumulative raw rows `2017–2026` -> `883,406` rows in the fixed 178-mandi panel) alongside `291,384` daily official NASA POWER agroclimatology rows (`114` `0.5°` grids, `0.0%` missing).
2. **Pre-Holdout Training & Calibration (`src/evaluation/calibration_and_pretest.py`):**
   * Trains `CausalArrivalForecaster` strictly on `Train_2024` (`arrival_date <= 2024-12-31`).
   * Freezes `safety_margin_inr = 50.0` solely on `Val_2025H1` (`2025-01-01`..`2025-05-31`).
3. **Holdout, Decade, Edge-AI & FPO Experiments & Figures:**
   * `src/evaluation/run_all_experiments.py`: Evaluates all policies (`B0`–`B6`, `MandiGuard`, ablations `T1`–`T4`, budget frontier, $3\times 3$ sensitivity + fee ablation, live check) + `R=5,000` Two-Way Origin-Mandi $\times$ 2-Week-Block Bootstrap (`seed=20261117`, Holm $m=4$).
   * `src/evaluation/run_creative_decade_and_modern_experiments.py`: Evaluates `Exp 10` (6 macro regimes `2017H2–2026`, `661,192` eps), `Exp 10b` (`1-Yr / 3-Yr / 8-Yr` scaling), `Exp 11` (Modern AI & NeurIPS'21 `ACI`), `Exp 12` (`ZeroCloud` & Val-calibrated satisficing edge agent), and `Exp 13/13b` (`FPO 90-qtl` pooling, `Split Top-2` portfolio, Biological Spoilage Clock & `160`-char SMS cards).
   * `src/visualization/make_figures.py`: Generates 8 300-DPI PNG figures (`fig1`–`fig8`) in `figures/`.
4. **Tests & Notebooks:**
   * `PYTHONPATH=. python3 -m pytest -v tests`: Runs all `18` automated anti-leakage, manifest SHA-256, survey parameter, ZeroCloud/ACI, and result integrity tests (`100%` self-contained in a fresh clone!).
   * `src/utils/build_notebooks.py` + `jupyter nbconvert --execute`: Builds & executes sequential notebooks `00`–`09` plus standalone Google Colab bundle (`notebooks/colab_standalone_reproduction.ipynb` + `data/processed/colab_data_pack.tar.gz`, `4.82 MB < 10 MB`, `<3 min`).
   * **Reading & Viva Guides:** Start with [paper/12th_class_easy_reading_edition.md](paper/12th_class_easy_reading_edition.md), the full thesis manuscript [paper/manuscript.md](paper/manuscript.md), and the exam-room defense sheet [viva/00_career_defense_master_sheet.md](viva/00_career_defense_master_sheet.md).
