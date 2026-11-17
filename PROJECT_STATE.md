# Project State — `MandiGuard`

**Last Updated:** 2026-11-17 (Pre-Holdout Registration & Calibration Lock Checkpoint)  
**Active Project Directory:** `/Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent`  
**Status:** Steps 1–3 complete (`Train_2024` + `Val_2025H1` calibration frozen; `Holdout_2025_2026` & `HP Apple 2026` untouched).

---

## Completed Datasets & Provenance
1. **Official AGMARKNET 6-State Panel (`2024-01-01`..`2026-04-13`):**
   - Streamed `14,443,770` raw daily rows (`2024`, `2025`, `2026 Jan–Apr 13`) from OGD Resource `35985678` mirror -> `673,971` clean rows across `699` markets -> causally `2024`-ranked top-30 panel of **`260,043` rows across `178` active mandis** in `6` states (`Gujarat: 30`, `Himachal Pradesh: 28`, `Karnataka: 30`, `Madhya Pradesh: 30`, `Maharashtra: 30`, `Uttar Pradesh: 30`) and `4` crops (`Onion`, `Potato`, `Tomato`, `Apple`).
   - Plus **`4,427` grade-explicit Himachal Pradesh Apple rows** across `42` mandis (`2025-11-07`..`2026-09-01`) and **`22` live unauthenticated Nov-2026 AGMARKNET API queries**.
2. **OSRM Real Highway Matrix (`data/processed/osrm_corridor_matrix.parquet`):**
   - `220` district-validated geocoded markets (`150` exact market matches within `<= 110 km` of District HQ, `70` district-centroid fallbacks).
   - **`8,147` intra-state highway corridors (`15–500 km`)** queried from public OSRM with realistic APMC auction arrival lags (`1 day: 3,810`, `2 days: 3,942`, `3 days: 395`).
3. **Climate Dataset (`data/processed/mandi_weather_2024_2026.parquet`):**
   - `141,955` daily rows across `145` deduplicated `0.1°` grid cells (`2024-01-01`..`2026-09-05`, `0.0%` missing after causal backfill): `145/145` ECMWF ERA5 realized ground truth + `102/145` native Open-Meteo Historical NWP forecasts + strictly causal `<= t` 2024-fitted Ridge nowcasting for `43` northern grid cells (`Val_2025H1` MAE: `1.047°C` tmax, `0.001 mm` rain, `0.284%` RH).
4. **Verified GoI Central & State Surveys (`data/processed/state_apmc_and_loss_parameters.csv`):**
   - Archived `8` open `.gov.in` PIB HTML/PDF documents plus `GoHP Economic Survey 2025-26` PDF (`88.86%` smallholders, `65.01 lakh qtl` APMC arrivals, `91.59%` single-lane hill roads).
   - Anchored physical & statutory model to MoFPI NABCONS (2022) market-level loss rates (`Tomato 3.25%`, `Onion 1.96%`, `Apple 1.64%`, `Potato 0.86%`), GoI `PIB relid=154554` APMC F&V fee rules, MoSPI NSO NSS 77th Round Report No. 587 (`30 qtl` smallholder lot benchmark, `Rs 3,798/mo` net crop income), MoFPI Nov-2023 state cold-storage capacity, and Oct-2024 e-NAM mandi counts.
5. **Zero-Leakage Episode Tables (`data/processed/`):**
   - **6-State Panel:** `239,809` episodes (`209,450` active shortlist episodes, `1,457,515` candidate rows).
   - **HP Apple Grade Panel:** `4,129` episodes (`3,923` active shortlist episodes, `33,090` candidate rows).

---

## Pre-Holdout Calibration Lock (`Val_2025H1` `2025-01-01`..`2025-05-31`)
* **2024 Forecaster Training Rows:** `701,932` (`<= 2024-12-31`, `arrival_date <= 2024-12-31`).
* **Validation Rows / Shortlisted Episodes:** `280,697` / `42,794` (`arrival_date <= 2025-05-31`).
* **Validation Empirical 80% Conformal LCB Coverage:** `78.85%`.
* **Validation Frozen Margin (`configs/frozen_calibration.json`):** **`Rs 50.0/qtl`** (`Val` `MandiGuard` Mean $\Delta\text{Net}$ = `Rs 351.36/qtl`, Dispatched Phantom Loss = `9.68%`, `9.10` avg tool calls vs `15.59` for Upfront `B4` [`41.6%` reduction]).
* **Unit Tests Verified Before Pre-Registration Commit:** `12/12` passed (`pytest`).
