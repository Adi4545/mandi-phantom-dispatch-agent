# Project State — MandiGuard Revision v4 (`finalization`, PR #1)

**Current Verdict:** **CONDITIONAL PASS (8.4 / 10)** — [`final/AUDIT_V4.md`](final/AUDIT_V4.md) & [`final/READINESS.md`](final/READINESS.md).  
**Environment:** Python `3.11.5`, `numpy 1.24.3`, `pandas 2.0.3`, `scikit-learn 1.3.0`, `scipy 1.11.1`, `pyarrow 11.0.0`, `pytest 7.4.0`.

## Synchronized Inventory & Status
1. **Tracked Primary Datasets:**
   - `data/raw/agmarknet_6state_top_apple_2024_2026.parquet`: `260,043` raw rows -> `759` out-of-range invalid dropped -> `259,284` valid -> `256,997` raw-key unique -> `248,302` canonical variety-day rows -> `95,074` Top-5 lagged episodes (`36,398` val, `58,676` test). Zero dependency on gitignored `candidates_6state.parquet`.
   - `data/raw/hp_apple_daily_2025_2026.csv`: `4,427` rows (`42` HP markets) -> `2,802` Top-5 lagged episodes.
   - `data/processed/osrm_corridor_matrix.parquet`: `8,147` corridors (`15.19–499.43 km`), `100%` join (`178/178` core, `42/42` HP).
   - `data/processed/mandi_weather_2024_2026.parquet`: audited `66,222 / 67,135` (`98.64%`) rain identity in `2025–2026`; strictly `< 2025-01-01` 2024 climatology used only as a sensitivity check (`−₹0.05` vs `none_20C_reference`).
2. **Core Revision Pipeline (`revision/`):** `build_variant.py`, `build_hp_apple_lagged.py`, `eval_run.py`, `sensitivity_a8.py`, `eval_a10.py` (pre-registered at `87a0b62`), `make_figures.py`, `es10.py`, `stats_utils.py`, `build_run.py`.
3. **Verification Gates Passed:**
   - `make reproduce` in fresh clean clone: **`CLEAN_CLONE_MAX_ABS_DIFF = 0.0`**.
   - `scripts/a16_independent_audit.py`: independent cleanroom re-derivation matches all headline metrics to **`₹0.00`**.
   - `scripts/verify_traceability.py`: **`0` untraceable empirical numbers** across `paper/manuscript.md`, `final/VIVA_QA.md`, and `viva/00..03*.md`.
   - `pytest -v`: **`32 passed`**, including counterfactual future-perturbation `R3` property tests and all edge-case settlement/fee tests.
4. **Open External Boundary (Gate J):** Shipped windows (`2025-06..2026-04` and HP Apple) were exposed in earlier commits (`exploratory: true`). Prospective holdout & field receipts await a live FPO pilot.
