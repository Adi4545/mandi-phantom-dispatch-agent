# Project State — MandiGuard Revision v6 (`finalization`, PR #1)

**Current Status:** **CONDITIONAL PASS — Unified Publication-Grade `Revision v6` Freeze (`0` untraceable numbers across `23/23` active docs; `49/49` verified bibliography citations; `₹0.00` `A16` audit match across 8 policies; `36/36` tests passing; `R = 5,000` paired cluster bootstrap across 1-, 2-, 4-week blocks; strict `2024`-only `171`-market panel & realized ERA5 arrival-weather settlement verified; `Gate J = BLOCKED` honestly disclosed).**  
**Environment:** Python `3.11.5`, `numpy 1.24.3`, `pandas 2.0.3`, `scikit-learn 1.3.0`, `scipy 1.11.1`, `pyarrow 11.0.0`, `pytest 7.4.0`.

## Synchronized Inventory & Status
1. **Tracked Primary Datasets:**
   - `data/raw/agmarknet_6state_top_apple_2024_2026.parquet`: `260,043` raw rows -> `759` out-of-range invalid dropped -> `259,284` -> `256,997` -> `248,302` canonical rows -> `95,074` Top-5 episodes (`36,398` val, `58,676` test) + strict `2024`-only `171`-market zero-lookahead test panel (`N = 57,634`) + `N = 88,014` unconditional origin robustness (`29,338` missing-d0 eps).
   - `data/raw/hp_apple_daily_2025_2026.csv`: `4,427` rows (`42` HP markets) -> `2,802` Top-5 lagged episodes.
   - `data/processed/osrm_corridor_matrix.parquet`: `8,147` corridors (`15.19–499.43 km`), `58.29%` exact-geocoded test rows (`40,690` episodes retaining exact-geocoded corridors; `18,189` all-5 exact).
   - `data/processed/mandi_weather_2024_2026.parquet`: excluded completely from all decisions; used strictly inside settlement for `Revision v6` realized ERA5 robustness (`100.0%` arrival coverage across `d0..d2`).
2. **Core Revision Pipeline (`revision/`):** `build_variant.py`, `build_hp_apple_lagged.py`, `eval_run.py`, `sensitivity_a8.py`, `eval_a10.py` (`87a0b62`), `eval_a18.py` (`4cbb02d`), **`eval_v6.py`**, `make_figures.py`, `es10.py`, `stats_utils.py`, `build_run.py`.
3. **Automated Gates Passing (`Revision v6`):**
   - `scripts/a16_independent_audit.py`: exact **`₹0.00`** discrepancy across `B1`, `B2_age_matched`, `RR_Abstain_matched`, `RR_Abstain_m0`, `Safe_EV_Sunk_m0`, `Safe_EV_Phys_m0`, `RT_2F_Min_m0`, `RT_2F_Dow_m0`, plus `n_clusters <= 178`.
   - `scripts/verify_traceability.py`: **`0` untraceable numbers across ALL `23/23` active docs**.
   - `pytest -v`: **`36 passed`**, including portability, `49/49` BibTeX citation sync, `R5` commit ancestry for `PREREG_A10` & `PREREG_A18`, `v6` `171`-market / realized-ERA5 / break-even (`resid < 1e-6`) / `R = 5,000` assertions, and compiled PDF/DOCX/LaTeX/Slides/Notebooks integrity checks.
4. **Open External Boundary (Gate J):** Bulk AGMARKNET stops `2026-04-13` (`exploratory: true`); live FPO pilot required for future holdout and field receipts.
